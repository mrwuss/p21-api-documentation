# Batch Processing Patterns

> **Disclaimer:** This is unofficial, community-created documentation for Epicor Prophet 21 APIs. It is not affiliated with, endorsed by, or supported by Epicor Software Corporation. All product names, trademarks, and registered trademarks are property of their respective owners. Use at your own risk.

---

## Overview

The existing Interactive API documentation covers single-operation workflows. Real production use often requires processing dozens or hundreds of operations in sequence, which introduces session timeout, error recovery, and batching concerns.

This document covers patterns learned from operating a production system that created **700+ price pages** across 25+ suppliers using the Interactive API (v2).

---

## Session-Per-Batch Pattern

Interactive API sessions are cleaned up after the server's configured `SessionTimeout` (default **60 seconds** per the [session-parameter table](04-Interactive-API.md#session-parameters-userparameters) in the Interactive API guide; approximately 6 minutes was observed on one production configuration). When processing many operations, a single session will time out between operations if any individual operation takes longer than expected or if there are delays between operations.

### Pattern

Start a new session for each batch of ~25 operations. This keeps each session well within the timeout window while minimizing session creation overhead.

<!-- tabs -->

**Python:**

```python
"""Session-per-batch: visit many price pages with a fresh session per batch."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
PRICE_PAGE_UIDS = [100198, 100199, 100200]  # one work item per UID
BATCH_SIZE = 25                           # operations per session (see timing table)
SERVICE_NAME = "SalesPricePage"           # window opened once per batch
# ---------------------------------------------------------------------------


def get_token(client: httpx.Client) -> str:
    """v2 token endpoint — credentials go in the body, never in headers."""
    r = client.post(
        f"{BASE_URL}/api/security/token/v2",
        json={"username": USERNAME, "password": PASSWORD},
        headers={"Accept": "application/json"},
    )
    r.raise_for_status()
    try:
        return r.json()["AccessToken"]
    except (ValueError, KeyError):  # some middleware answers in XML
        match = re.search(r"<AccessToken>([^<]+)</AccessToken>", r.text)
        if not match:
            raise ValueError(f"No AccessToken in response: {r.text[:200]}") from None
        return match.group(1)


def get_ui_server(client: httpx.Client, token: str) -> str:
    """Transaction and Interactive calls go to the UI server, not BASE_URL."""
    r = client.get(
        f"{BASE_URL}/api/ui/router/v1/?urlType=external",  # trailing slash avoids a 307
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )
    r.raise_for_status()
    try:
        return r.json()["Url"].rstrip("/")
    except (ValueError, KeyError):
        match = re.search(r"<Url>([^<]+)</Url>", r.text)
        if not match:
            raise ValueError(f"No Url in router response: {r.text[:200]}") from None
        return match.group(1).rstrip("/")


def status_of(result: dict) -> int:
    """ResultStatus enum: None=0, Success=1, Failure=2, Blocked=3."""
    status = result.get("Status", 0)
    if isinstance(status, str):
        return {"None": 0, "Success": 1, "Failure": 2, "Blocked": 3}.get(status, 0)
    return status


def messages_of(result: dict) -> list[str]:
    """Failure detail lives in the top-level Messages array, not in Events."""
    return [m.get("Text", "") for m in result.get("Messages", [])]


def start_session(client: httpx.Client, headers: dict, ui_server: str) -> str:
    """Start an Interactive session. 2026.1 renamed SessionId -> Id; read both."""
    r = client.post(
        f"{ui_server}/api/ui/interactive/sessions/",
        json={"ResponseWindowHandlingEnabled": False},
        headers=headers,
    )
    r.raise_for_status()
    data = r.json()
    return data.get("Id") or data.get("SessionId", "")


def end_session(client: httpx.Client, headers: dict, ui_server: str) -> None:
    """Always call this — a leaked session 409s the next create."""
    client.delete(f"{ui_server}/api/ui/interactive/sessions/", headers=headers)


def open_window(client: httpx.Client, headers: dict, ui_server: str, service: str) -> str:
    r = client.post(
        f"{ui_server}/api/ui/interactive/v2/window",
        json={"ServiceName": service},
        headers=headers,
    )
    r.raise_for_status()
    data = r.json()
    return data.get("WindowId") or data.get("windowId", "")


def close_window(client: httpx.Client, headers: dict, ui_server: str, window_id: str) -> None:
    client.delete(
        f"{ui_server}/api/ui/interactive/v2/window",
        params={"id": window_id},
        headers=headers,
    )


def change_field(
    client: httpx.Client,
    headers: dict,
    ui_server: str,
    window_id: str,
    tab: str,
    datawindow: str,
    field: str,
    value: str,
) -> dict:
    """Change one field. One field per call — batched /v2/change is non-atomic."""
    payload = {
        "WindowId": window_id,
        "List": [
            {
                "TabName": tab,
                "DatawindowName": datawindow,  # required since 25.2
                "FieldName": field,
                "Value": value,
            }
        ],
    }
    r = client.put(
        f"{ui_server}/api/ui/interactive/v2/change", json=payload, headers=headers
    )
    r.raise_for_status()
    return r.json()


def clear_window(client: httpx.Client, headers: dict, ui_server: str, window_id: str) -> None:
    """Reset the form for the next record in the batch."""
    r = client.delete(
        f"{ui_server}/api/ui/interactive/v2/data",
        params={"id": window_id},
        headers=headers,
    )
    r.raise_for_status()


def process_batch(
    client: httpx.Client, headers: dict, ui_server: str, batch: list[int]
) -> list[dict]:
    """Load every page in the batch through a single reused window."""
    results = []
    window_id = open_window(client, headers, ui_server, SERVICE_NAME)

    try:
        for i, uid in enumerate(batch):
            try:
                result = change_field(
                    client, headers, ui_server, window_id,
                    "FORM", "form", "price_page_uid", str(uid),
                )
            except httpx.HTTPError as exc:
                results.append({"uid": uid, "success": False, "status": -1,
                                "messages": [str(exc)]})
                # Window state may be corrupted — see Error Recovery below
                close_window(client, headers, ui_server, window_id)
                window_id = open_window(client, headers, ui_server, SERVICE_NAME)
                continue

            code = status_of(result)
            results.append({"uid": uid, "success": code == 1, "status": code,
                            "messages": messages_of(result)})

            # Clear the form for the next record (skip on last item)
            if i < len(batch) - 1:
                clear_window(client, headers, ui_server, window_id)
    finally:
        close_window(client, headers, ui_server, window_id)

    return results


def process_in_batches(
    client: httpx.Client,
    headers: dict,
    ui_server: str,
    items: list[int],
    batch_size: int = 25,
) -> list[dict]:
    """Process items in batches with a fresh session per batch.

    Args:
        client: Open httpx.Client
        headers: Authorized request headers (must include Accept: application/json)
        ui_server: UI server base URL from the router
        items: Price page UIDs to process
        batch_size: Number of operations per session (default 25)

    Returns:
        List of per-item result dicts
    """
    results = []
    total_batches = (len(items) + batch_size - 1) // batch_size

    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batch_num = (i // batch_size) + 1

        print(f"Processing batch {batch_num}/{total_batches} ({len(batch)} items)")

        # New session for each batch — released even if the batch raises
        start_session(client, headers, ui_server)
        try:
            results.extend(process_batch(client, headers, ui_server, batch))
        finally:
            end_session(client, headers, ui_server)

    return results


with httpx.Client(verify=VERIFY_SSL, timeout=120, follow_redirects=True) as client:
    token = get_token(client)
    ui_server = get_ui_server(client, token)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",       # without this you get XML, not JSON
        "Content-Type": "application/json",
    }

    outcomes = process_in_batches(
        client, headers, ui_server, PRICE_PAGE_UIDS, BATCH_SIZE
    )

    for outcome in outcomes:
        flag = "OK  " if outcome["success"] else "FAIL"
        print(f"{flag} uid={outcome['uid']} status={outcome['status']} "
              f"{'; '.join(outcome['messages'])}")
    print(f"{sum(1 for o in outcomes if o['success'])}/{len(outcomes)} succeeded")
```

**C#:**

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string ServiceName = "SalesPricePage";           // window opened once per batch
const int BatchSize = 25;                              // operations per session
int[] pricePageUids = { 100198, 100199, 100200 };      // one work item per UID
// ---------------------------------------------------------------------------

var handler = new HttpClientHandler
{
    // Test tenants often present a self-signed cert. Delete this line in production.
    ServerCertificateCustomValidationCallback =
        HttpClientHandler.DangerousAcceptAnyServerCertificateValidator,
};
using var client = new HttpClient(handler) { Timeout = TimeSpan.FromMinutes(2) };
client.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));

var token = await GetTokenAsync(client);
var uiServer = await GetUiServerAsync(client, token);
client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);

var outcomes = await ProcessInBatchesAsync(client, uiServer, pricePageUids, BatchSize);

foreach (var outcome in outcomes)
    Console.WriteLine(
        $"{(outcome.Success ? "OK  " : "FAIL")} uid={outcome.Uid} " +
        $"status={outcome.Status} {string.Join("; ", outcome.Messages)}");
Console.WriteLine($"{outcomes.Count(o => o.Success)}/{outcomes.Count} succeeded");

// --- batch driver ----------------------------------------------------------

// Process items in batches with a fresh session per batch.
static async Task<List<Outcome>> ProcessInBatchesAsync(
    HttpClient client, string uiServer, IReadOnlyList<int> items, int batchSize)
{
    var results = new List<Outcome>();
    int totalBatches = (items.Count + batchSize - 1) / batchSize;

    for (int i = 0; i < items.Count; i += batchSize)
    {
        var batch = items.Skip(i).Take(batchSize).ToList();
        int batchNum = (i / batchSize) + 1;

        Console.WriteLine(
            $"Processing batch {batchNum}/{totalBatches} ({batch.Count} items)");

        // New session for each batch - released even if the batch throws
        await StartSessionAsync(client, uiServer);
        try
        {
            results.AddRange(await ProcessBatchAsync(client, uiServer, batch));
        }
        finally
        {
            await EndSessionAsync(client, uiServer);
        }
    }

    return results;
}

// Load every page in the batch through a single reused window.
static async Task<List<Outcome>> ProcessBatchAsync(
    HttpClient client, string uiServer, List<int> batch)
{
    var results = new List<Outcome>();
    string windowId = await OpenWindowAsync(client, uiServer, ServiceName);

    try
    {
        for (int i = 0; i < batch.Count; i++)
        {
            int uid = batch[i];
            JsonElement result;
            try
            {
                result = await ChangeFieldAsync(
                    client, uiServer, windowId,
                    "FORM", "form", "price_page_uid", uid.ToString());
            }
            catch (HttpRequestException ex)
            {
                results.Add(new Outcome(uid, false, -1, new List<string> { ex.Message }));
                // Window state may be corrupted - see Error Recovery below
                await CloseWindowAsync(client, uiServer, windowId);
                windowId = await OpenWindowAsync(client, uiServer, ServiceName);
                continue;
            }

            int status = StatusOf(result);
            results.Add(new Outcome(uid, status == 1, status, MessagesOf(result)));

            // Clear the form for the next record (skip on last item)
            if (i < batch.Count - 1)
                await ClearWindowAsync(client, uiServer, windowId);
        }
    }
    finally
    {
        await CloseWindowAsync(client, uiServer, windowId);
    }

    return results;
}

// --- Interactive API helpers -----------------------------------------------

// Start an Interactive session. 2026.1 renamed SessionId -> Id; read both.
static async Task<string> StartSessionAsync(HttpClient client, string uiServer)
{
    var resp = await SendAsync(client, HttpMethod.Post,
        $"{uiServer}/api/ui/interactive/sessions/",
        new Dictionary<string, object> { ["ResponseWindowHandlingEnabled"] = false });
    if (resp.ValueKind == JsonValueKind.Object)
    {
        if (resp.TryGetProperty("Id", out var id)) return id.GetString() ?? "";
        if (resp.TryGetProperty("SessionId", out var sid)) return sid.GetString() ?? "";
    }
    return "";
}

// Always call this - a leaked session 409s the next create.
static async Task EndSessionAsync(HttpClient client, string uiServer)
{
    using var request = new HttpRequestMessage(
        HttpMethod.Delete, $"{uiServer}/api/ui/interactive/sessions/");
    await client.SendAsync(request);
}

static async Task<string> OpenWindowAsync(
    HttpClient client, string uiServer, string serviceName)
{
    var resp = await SendAsync(client, HttpMethod.Post,
        $"{uiServer}/api/ui/interactive/v2/window",
        new Dictionary<string, object> { ["ServiceName"] = serviceName });
    if (resp.ValueKind == JsonValueKind.Object)
    {
        if (resp.TryGetProperty("WindowId", out var id)) return id.GetString() ?? "";
        if (resp.TryGetProperty("windowId", out var lower)) return lower.GetString() ?? "";
    }
    return "";
}

static async Task CloseWindowAsync(HttpClient client, string uiServer, string windowId)
{
    using var request = new HttpRequestMessage(
        HttpMethod.Delete, $"{uiServer}/api/ui/interactive/v2/window?id={windowId}");
    await client.SendAsync(request);
}

// Change one field. One field per call - batched /v2/change is non-atomic.
static async Task<JsonElement> ChangeFieldAsync(
    HttpClient client, string uiServer, string windowId,
    string tab, string datawindow, string field, string value)
{
    var payload = new Dictionary<string, object>
    {
        ["WindowId"] = windowId,
        ["List"] = new[]
        {
            new Dictionary<string, object>
            {
                ["TabName"] = tab,
                ["DatawindowName"] = datawindow,   // required since 25.2
                ["FieldName"] = field,
                ["Value"] = value,
            },
        },
    };
    return await SendAsync(client, HttpMethod.Put,
        $"{uiServer}/api/ui/interactive/v2/change", payload);
}

// Reset the form for the next record in the batch.
static async Task ClearWindowAsync(HttpClient client, string uiServer, string windowId)
{
    using var request = new HttpRequestMessage(
        HttpMethod.Delete, $"{uiServer}/api/ui/interactive/v2/data?id={windowId}");
    var response = await client.SendAsync(request);
    response.EnsureSuccessStatusCode();
}

// ResultStatus enum: None=0, Success=1, Failure=2, Blocked=3.
static int StatusOf(JsonElement result)
{
    if (result.ValueKind != JsonValueKind.Object ||
        !result.TryGetProperty("Status", out var status))
        return 0;
    return status.ValueKind switch
    {
        JsonValueKind.Number => status.GetInt32(),
        JsonValueKind.String => status.GetString() switch
        {
            "Success" => 1,
            "Failure" => 2,
            "Blocked" => 3,
            _ => 0,
        },
        _ => 0,
    };
}

// Failure detail lives in the top-level Messages array, not in Events.
static List<string> MessagesOf(JsonElement result)
{
    var messages = new List<string>();
    if (result.ValueKind == JsonValueKind.Object &&
        result.TryGetProperty("Messages", out var arr) &&
        arr.ValueKind == JsonValueKind.Array)
    {
        foreach (var message in arr.EnumerateArray())
            messages.Add(message.TryGetProperty("Text", out var text)
                ? text.GetString() ?? "" : "");
    }
    return messages;
}

static async Task<JsonElement> SendAsync(
    HttpClient client, HttpMethod method, string url, object? body = null)
{
    using var request = new HttpRequestMessage(method, url);
    if (body is not null)
        request.Content = new StringContent(
            JsonSerializer.Serialize(body), Encoding.UTF8, "application/json");
    var response = await client.SendAsync(request);
    response.EnsureSuccessStatusCode();
    var text = await response.Content.ReadAsStringAsync();
    if (string.IsNullOrWhiteSpace(text)) return default;
    using var doc = JsonDocument.Parse(text);
    return doc.RootElement.Clone();
}

// --- auth helpers ----------------------------------------------------------

// v2 token endpoint — credentials go in the body, never in headers.
static async Task<string> GetTokenAsync(HttpClient client)
{
    var payload = JsonSerializer.Serialize(new { username = Username, password = Password });
    var response = await client.PostAsync(
        $"{BaseUrl}/api/security/token/v2",
        new StringContent(payload, Encoding.UTF8, "application/json"));
    response.EnsureSuccessStatusCode();
    return ReadField(await response.Content.ReadAsStringAsync(), "AccessToken");
}

// Transaction and Interactive calls go to the UI server, not BaseUrl.
static async Task<string> GetUiServerAsync(HttpClient client, string token)
{
    using var request = new HttpRequestMessage(
        HttpMethod.Get, $"{BaseUrl}/api/ui/router/v1/?urlType=external");
    request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
    var response = await client.SendAsync(request);
    response.EnsureSuccessStatusCode();
    return ReadField(await response.Content.ReadAsStringAsync(), "Url").TrimEnd('/');
}

// Some middleware answers these two endpoints in XML even when asked for JSON.
static string ReadField(string payload, string field)
{
    try
    {
        var value = JsonDocument.Parse(payload).RootElement.GetProperty(field).GetString();
        if (!string.IsNullOrEmpty(value)) return value;
    }
    catch (Exception ex) when (ex is JsonException or KeyNotFoundException) { }

    var match = System.Text.RegularExpressions.Regex.Match(payload, $"<{field}>([^<]+)</{field}>");
    if (!match.Success)
        throw new InvalidOperationException(
            $"No {field} in response: {payload[..Math.Min(200, payload.Length)]}");
    return match.Groups[1].Value;
}

// --- result record ---------------------------------------------------------

record Outcome(int Uid, bool Success, int Status, List<string> Messages);
```

<!-- /tabs -->

### Verified Timing Data

From production measurements creating price pages with book linking:

| Metric | Value |
|--------|-------|
| Time per page creation (including book linking) | ~2.5s |
| Time for 25-page batch | ~62s |
| Session overhead (start + end) | ~1s |
| Total for 700 pages (28 batches) | ~30 min |

---

## Window Reuse Within a Batch

Opening a P21 window is expensive (~500ms). Within a batch, open the window once and reuse it for multiple operations by clearing the window data (`DELETE /api/ui/interactive/v2/data?id={windowId}` — `clear_window()` below, `clear_data()` on the client class) between records.

### Pattern

<!-- tabs -->

**Python:**

```python
"""Window reuse: process a batch of records through one window, clearing between."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
PRICE_PAGE_UIDS = [100198, 100199, 100200]  # records handled by one window
SERVICE_NAME = "SalesPricePage"           # window opened once for the whole batch
# ---------------------------------------------------------------------------


def get_token(client: httpx.Client) -> str:
    """v2 token endpoint — credentials go in the body, never in headers."""
    r = client.post(
        f"{BASE_URL}/api/security/token/v2",
        json={"username": USERNAME, "password": PASSWORD},
        headers={"Accept": "application/json"},
    )
    r.raise_for_status()
    try:
        return r.json()["AccessToken"]
    except (ValueError, KeyError):  # some middleware answers in XML
        match = re.search(r"<AccessToken>([^<]+)</AccessToken>", r.text)
        if not match:
            raise ValueError(f"No AccessToken in response: {r.text[:200]}") from None
        return match.group(1)


def get_ui_server(client: httpx.Client, token: str) -> str:
    """Transaction and Interactive calls go to the UI server, not BASE_URL."""
    r = client.get(
        f"{BASE_URL}/api/ui/router/v1/?urlType=external",  # trailing slash avoids a 307
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )
    r.raise_for_status()
    try:
        return r.json()["Url"].rstrip("/")
    except (ValueError, KeyError):
        match = re.search(r"<Url>([^<]+)</Url>", r.text)
        if not match:
            raise ValueError(f"No Url in router response: {r.text[:200]}") from None
        return match.group(1).rstrip("/")


def status_of(result: dict) -> int:
    """ResultStatus enum: None=0, Success=1, Failure=2, Blocked=3."""
    status = result.get("Status", 0)
    if isinstance(status, str):
        return {"None": 0, "Success": 1, "Failure": 2, "Blocked": 3}.get(status, 0)
    return status


def messages_of(result: dict) -> list[str]:
    """Failure detail lives in the top-level Messages array, not in Events."""
    return [m.get("Text", "") for m in result.get("Messages", [])]


def start_session(client: httpx.Client, headers: dict, ui_server: str) -> str:
    """Start an Interactive session. 2026.1 renamed SessionId -> Id; read both."""
    r = client.post(
        f"{ui_server}/api/ui/interactive/sessions/",
        json={"ResponseWindowHandlingEnabled": False},
        headers=headers,
    )
    r.raise_for_status()
    data = r.json()
    return data.get("Id") or data.get("SessionId", "")


def end_session(client: httpx.Client, headers: dict, ui_server: str) -> None:
    """Always call this — a leaked session 409s the next create."""
    client.delete(f"{ui_server}/api/ui/interactive/sessions/", headers=headers)


def open_window(client: httpx.Client, headers: dict, ui_server: str, service: str) -> str:
    """Opening a window is the expensive part — do it once per batch."""
    r = client.post(
        f"{ui_server}/api/ui/interactive/v2/window",
        json={"ServiceName": service},
        headers=headers,
    )
    r.raise_for_status()
    data = r.json()
    return data.get("WindowId") or data.get("windowId", "")


def close_window(client: httpx.Client, headers: dict, ui_server: str, window_id: str) -> None:
    client.delete(
        f"{ui_server}/api/ui/interactive/v2/window",
        params={"id": window_id},
        headers=headers,
    )


def change_field(
    client: httpx.Client,
    headers: dict,
    ui_server: str,
    window_id: str,
    tab: str,
    datawindow: str,
    field: str,
    value: str,
) -> dict:
    """Change one field. One field per call — batched /v2/change is non-atomic."""
    payload = {
        "WindowId": window_id,
        "List": [
            {
                "TabName": tab,
                "DatawindowName": datawindow,  # required since 25.2
                "FieldName": field,
                "Value": value,
            }
        ],
    }
    r = client.put(
        f"{ui_server}/api/ui/interactive/v2/change", json=payload, headers=headers
    )
    r.raise_for_status()
    return r.json()


def clear_window(client: httpx.Client, headers: dict, ui_server: str, window_id: str) -> None:
    """Reset the form so the same window can take the next record."""
    r = client.delete(
        f"{ui_server}/api/ui/interactive/v2/data",
        params={"id": window_id},
        headers=headers,
    )
    r.raise_for_status()


def process_batch(
    client: httpx.Client, headers: dict, ui_server: str, items: list[int]
) -> list[dict]:
    """Process a batch of items using a single window.

    Opens the window once, processes all items, then closes.
    Uses clear_window() between records to reset the form.
    """
    results = []

    # Open window once for the entire batch
    window_id = open_window(client, headers, ui_server, SERVICE_NAME)

    try:
        for i, uid in enumerate(items):
            try:
                result = change_field(
                    client, headers, ui_server, window_id,
                    "FORM", "form", "price_page_uid", str(uid),
                )
                code = status_of(result)
                results.append({"item": uid, "success": code == 1, "status": code,
                                "messages": messages_of(result)})

                # Clear the form for the next record (skip on last item)
                if i < len(items) - 1:
                    clear_window(client, headers, ui_server, window_id)

            except httpx.HTTPError as exc:
                print(f"Failed to process item {uid}: {exc}")
                results.append({"item": uid, "success": False, "status": -1,
                                "messages": [str(exc)]})

                # On error, close and reopen the window (see Error Recovery below)
                close_window(client, headers, ui_server, window_id)
                window_id = open_window(client, headers, ui_server, SERVICE_NAME)

    finally:
        close_window(client, headers, ui_server, window_id)

    return results


with httpx.Client(verify=VERIFY_SSL, timeout=120, follow_redirects=True) as client:
    token = get_token(client)
    ui_server = get_ui_server(client, token)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",       # without this you get XML, not JSON
        "Content-Type": "application/json",
    }

    start_session(client, headers, ui_server)
    try:
        outcomes = process_batch(client, headers, ui_server, PRICE_PAGE_UIDS)
    finally:
        end_session(client, headers, ui_server)

    for outcome in outcomes:
        flag = "OK  " if outcome["success"] else "FAIL"
        print(f"{flag} uid={outcome['item']} status={outcome['status']} "
              f"{'; '.join(outcome['messages'])}")
    print(f"{sum(1 for o in outcomes if o['success'])}/{len(outcomes)} succeeded")
```

**C#:**

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string ServiceName = "SalesPricePage";           // opened once for the batch
int[] pricePageUids = { 100198, 100199, 100200 };      // records handled by one window
// ---------------------------------------------------------------------------

var handler = new HttpClientHandler
{
    // Test tenants often present a self-signed cert. Delete this line in production.
    ServerCertificateCustomValidationCallback =
        HttpClientHandler.DangerousAcceptAnyServerCertificateValidator,
};
using var client = new HttpClient(handler) { Timeout = TimeSpan.FromMinutes(2) };
client.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));

var token = await GetTokenAsync(client);
var uiServer = await GetUiServerAsync(client, token);
client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);

List<Outcome> outcomes;
await StartSessionAsync(client, uiServer);
try
{
    outcomes = await ProcessBatchAsync(client, uiServer, pricePageUids);
}
finally
{
    await EndSessionAsync(client, uiServer);
}

foreach (var outcome in outcomes)
    Console.WriteLine(
        $"{(outcome.Success ? "OK  " : "FAIL")} uid={outcome.Uid} " +
        $"status={outcome.Status} {string.Join("; ", outcome.Messages)}");
Console.WriteLine($"{outcomes.Count(o => o.Success)}/{outcomes.Count} succeeded");

// --- batch over one window -------------------------------------------------

// Process a batch of items using a single window.
// Opens the window once, processes all items, then closes.
// Uses ClearWindowAsync() between records to reset the form.
static async Task<List<Outcome>> ProcessBatchAsync(
    HttpClient client, string uiServer, IReadOnlyList<int> items)
{
    var results = new List<Outcome>();

    // Open window once for the entire batch
    string windowId = await OpenWindowAsync(client, uiServer, ServiceName);

    try
    {
        for (int i = 0; i < items.Count; i++)
        {
            int uid = items[i];
            try
            {
                var result = await ChangeFieldAsync(
                    client, uiServer, windowId,
                    "FORM", "form", "price_page_uid", uid.ToString());
                int status = StatusOf(result);
                results.Add(new Outcome(uid, status == 1, status, MessagesOf(result)));

                // Clear the form for the next record (skip on last item)
                if (i < items.Count - 1)
                    await ClearWindowAsync(client, uiServer, windowId);
            }
            catch (HttpRequestException ex)
            {
                Console.WriteLine($"Failed to process item {uid}: {ex.Message}");
                results.Add(new Outcome(uid, false, -1, new List<string> { ex.Message }));

                // On error, close and reopen the window (see Error Recovery below)
                await CloseWindowAsync(client, uiServer, windowId);
                windowId = await OpenWindowAsync(client, uiServer, ServiceName);
            }
        }
    }
    finally
    {
        await CloseWindowAsync(client, uiServer, windowId);
    }

    return results;
}

// --- Interactive API helpers -----------------------------------------------

// Start an Interactive session. 2026.1 renamed SessionId -> Id; read both.
static async Task<string> StartSessionAsync(HttpClient client, string uiServer)
{
    var resp = await SendAsync(client, HttpMethod.Post,
        $"{uiServer}/api/ui/interactive/sessions/",
        new Dictionary<string, object> { ["ResponseWindowHandlingEnabled"] = false });
    if (resp.ValueKind == JsonValueKind.Object)
    {
        if (resp.TryGetProperty("Id", out var id)) return id.GetString() ?? "";
        if (resp.TryGetProperty("SessionId", out var sid)) return sid.GetString() ?? "";
    }
    return "";
}

// Always call this - a leaked session 409s the next create.
static async Task EndSessionAsync(HttpClient client, string uiServer)
{
    using var request = new HttpRequestMessage(
        HttpMethod.Delete, $"{uiServer}/api/ui/interactive/sessions/");
    await client.SendAsync(request);
}

// Opening a window is the expensive part - do it once per batch.
static async Task<string> OpenWindowAsync(
    HttpClient client, string uiServer, string serviceName)
{
    var resp = await SendAsync(client, HttpMethod.Post,
        $"{uiServer}/api/ui/interactive/v2/window",
        new Dictionary<string, object> { ["ServiceName"] = serviceName });
    if (resp.ValueKind == JsonValueKind.Object)
    {
        if (resp.TryGetProperty("WindowId", out var id)) return id.GetString() ?? "";
        if (resp.TryGetProperty("windowId", out var lower)) return lower.GetString() ?? "";
    }
    return "";
}

static async Task CloseWindowAsync(HttpClient client, string uiServer, string windowId)
{
    using var request = new HttpRequestMessage(
        HttpMethod.Delete, $"{uiServer}/api/ui/interactive/v2/window?id={windowId}");
    await client.SendAsync(request);
}

// Change one field. One field per call - batched /v2/change is non-atomic.
static async Task<JsonElement> ChangeFieldAsync(
    HttpClient client, string uiServer, string windowId,
    string tab, string datawindow, string field, string value)
{
    var payload = new Dictionary<string, object>
    {
        ["WindowId"] = windowId,
        ["List"] = new[]
        {
            new Dictionary<string, object>
            {
                ["TabName"] = tab,
                ["DatawindowName"] = datawindow,   // required since 25.2
                ["FieldName"] = field,
                ["Value"] = value,
            },
        },
    };
    return await SendAsync(client, HttpMethod.Put,
        $"{uiServer}/api/ui/interactive/v2/change", payload);
}

// Reset the form so the same window can take the next record.
static async Task ClearWindowAsync(HttpClient client, string uiServer, string windowId)
{
    using var request = new HttpRequestMessage(
        HttpMethod.Delete, $"{uiServer}/api/ui/interactive/v2/data?id={windowId}");
    var response = await client.SendAsync(request);
    response.EnsureSuccessStatusCode();
}

// ResultStatus enum: None=0, Success=1, Failure=2, Blocked=3.
static int StatusOf(JsonElement result)
{
    if (result.ValueKind != JsonValueKind.Object ||
        !result.TryGetProperty("Status", out var status))
        return 0;
    return status.ValueKind switch
    {
        JsonValueKind.Number => status.GetInt32(),
        JsonValueKind.String => status.GetString() switch
        {
            "Success" => 1,
            "Failure" => 2,
            "Blocked" => 3,
            _ => 0,
        },
        _ => 0,
    };
}

// Failure detail lives in the top-level Messages array, not in Events.
static List<string> MessagesOf(JsonElement result)
{
    var messages = new List<string>();
    if (result.ValueKind == JsonValueKind.Object &&
        result.TryGetProperty("Messages", out var arr) &&
        arr.ValueKind == JsonValueKind.Array)
    {
        foreach (var message in arr.EnumerateArray())
            messages.Add(message.TryGetProperty("Text", out var text)
                ? text.GetString() ?? "" : "");
    }
    return messages;
}

static async Task<JsonElement> SendAsync(
    HttpClient client, HttpMethod method, string url, object? body = null)
{
    using var request = new HttpRequestMessage(method, url);
    if (body is not null)
        request.Content = new StringContent(
            JsonSerializer.Serialize(body), Encoding.UTF8, "application/json");
    var response = await client.SendAsync(request);
    response.EnsureSuccessStatusCode();
    var text = await response.Content.ReadAsStringAsync();
    if (string.IsNullOrWhiteSpace(text)) return default;
    using var doc = JsonDocument.Parse(text);
    return doc.RootElement.Clone();
}

// --- auth helpers ----------------------------------------------------------

// v2 token endpoint — credentials go in the body, never in headers.
static async Task<string> GetTokenAsync(HttpClient client)
{
    var payload = JsonSerializer.Serialize(new { username = Username, password = Password });
    var response = await client.PostAsync(
        $"{BaseUrl}/api/security/token/v2",
        new StringContent(payload, Encoding.UTF8, "application/json"));
    response.EnsureSuccessStatusCode();
    return ReadField(await response.Content.ReadAsStringAsync(), "AccessToken");
}

// Transaction and Interactive calls go to the UI server, not BaseUrl.
static async Task<string> GetUiServerAsync(HttpClient client, string token)
{
    using var request = new HttpRequestMessage(
        HttpMethod.Get, $"{BaseUrl}/api/ui/router/v1/?urlType=external");
    request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
    var response = await client.SendAsync(request);
    response.EnsureSuccessStatusCode();
    return ReadField(await response.Content.ReadAsStringAsync(), "Url").TrimEnd('/');
}

// Some middleware answers these two endpoints in XML even when asked for JSON.
static string ReadField(string payload, string field)
{
    try
    {
        var value = JsonDocument.Parse(payload).RootElement.GetProperty(field).GetString();
        if (!string.IsNullOrEmpty(value)) return value;
    }
    catch (Exception ex) when (ex is JsonException or KeyNotFoundException) { }

    var match = System.Text.RegularExpressions.Regex.Match(payload, $"<{field}>([^<]+)</{field}>");
    if (!match.Success)
        throw new InvalidOperationException(
            $"No {field} in response: {payload[..Math.Min(200, payload.Length)]}");
    return match.Groups[1].Value;
}

// --- result record ---------------------------------------------------------

record Outcome(int Uid, bool Success, int Status, List<string> Messages);
```

<!-- /tabs -->

### Key Points

- Clear the window data after saving each record to reset the form
- Do NOT clear after the last record (the window close handles cleanup)
- If an error occurs, close and reopen the window rather than trying to recover in-place

---

## Error Recovery Pattern

When an error occurs during an Interactive API operation, the window state may be corrupted (partial field values, unsaved changes, open dialogs). Attempting to continue using a corrupted window leads to cascading failures.

### Pattern: Close and Reopen on Error

<!-- tabs -->

**Python:**

```python
"""Error recovery: retry a record on a fresh window after a failed operation."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
PRICE_PAGE_UIDS = [100198, 999999999, 100199]  # middle UID is deliberately bad
MAX_RETRIES = 2                           # retry attempts per record
SERVICE_NAME = "SalesPricePage"
# ---------------------------------------------------------------------------


def get_token(client: httpx.Client) -> str:
    """v2 token endpoint — credentials go in the body, never in headers."""
    r = client.post(
        f"{BASE_URL}/api/security/token/v2",
        json={"username": USERNAME, "password": PASSWORD},
        headers={"Accept": "application/json"},
    )
    r.raise_for_status()
    try:
        return r.json()["AccessToken"]
    except (ValueError, KeyError):  # some middleware answers in XML
        match = re.search(r"<AccessToken>([^<]+)</AccessToken>", r.text)
        if not match:
            raise ValueError(f"No AccessToken in response: {r.text[:200]}") from None
        return match.group(1)


def get_ui_server(client: httpx.Client, token: str) -> str:
    """Transaction and Interactive calls go to the UI server, not BASE_URL."""
    r = client.get(
        f"{BASE_URL}/api/ui/router/v1/?urlType=external",  # trailing slash avoids a 307
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )
    r.raise_for_status()
    try:
        return r.json()["Url"].rstrip("/")
    except (ValueError, KeyError):
        match = re.search(r"<Url>([^<]+)</Url>", r.text)
        if not match:
            raise ValueError(f"No Url in router response: {r.text[:200]}") from None
        return match.group(1).rstrip("/")


def status_of(result: dict) -> int:
    """ResultStatus enum: None=0, Success=1, Failure=2, Blocked=3."""
    status = result.get("Status", 0)
    if isinstance(status, str):
        return {"None": 0, "Success": 1, "Failure": 2, "Blocked": 3}.get(status, 0)
    return status


def messages_of(result: dict) -> list[str]:
    """Failure detail lives in the top-level Messages array, not in Events."""
    return [m.get("Text", "") for m in result.get("Messages", [])]


def start_session(client: httpx.Client, headers: dict, ui_server: str) -> str:
    """Start an Interactive session. 2026.1 renamed SessionId -> Id; read both."""
    r = client.post(
        f"{ui_server}/api/ui/interactive/sessions/",
        json={"ResponseWindowHandlingEnabled": False},
        headers=headers,
    )
    r.raise_for_status()
    data = r.json()
    return data.get("Id") or data.get("SessionId", "")


def end_session(client: httpx.Client, headers: dict, ui_server: str) -> None:
    """Always call this — a leaked session 409s the next create."""
    client.delete(f"{ui_server}/api/ui/interactive/sessions/", headers=headers)


def open_window(client: httpx.Client, headers: dict, ui_server: str, service: str) -> str:
    r = client.post(
        f"{ui_server}/api/ui/interactive/v2/window",
        json={"ServiceName": service},
        headers=headers,
    )
    r.raise_for_status()
    data = r.json()
    return data.get("WindowId") or data.get("windowId", "")


def close_window(client: httpx.Client, headers: dict, ui_server: str, window_id: str) -> None:
    client.delete(
        f"{ui_server}/api/ui/interactive/v2/window",
        params={"id": window_id},
        headers=headers,
    )


def change_field(
    client: httpx.Client,
    headers: dict,
    ui_server: str,
    window_id: str,
    tab: str,
    datawindow: str,
    field: str,
    value: str,
) -> dict:
    """Change one field. One field per call — batched /v2/change is non-atomic."""
    payload = {
        "WindowId": window_id,
        "List": [
            {
                "TabName": tab,
                "DatawindowName": datawindow,  # required since 25.2
                "FieldName": field,
                "Value": value,
            }
        ],
    }
    r = client.put(
        f"{ui_server}/api/ui/interactive/v2/change", json=payload, headers=headers
    )
    r.raise_for_status()
    return r.json()


def load_page(
    client: httpx.Client, headers: dict, ui_server: str, window_id: str, uid: int
) -> dict:
    """Load one price page, raising on anything that is not Success.

    On 2026.1 a nonexistent record loads as Status 2 with an empty window and
    Messages [{"Text": "Enter a valid ID or leave ID blank."}].
    """
    result = change_field(
        client, headers, ui_server, window_id,
        "FORM", "form", "price_page_uid", str(uid),
    )
    code = status_of(result)
    if code != 1:
        raise RuntimeError(f"status={code} {'; '.join(messages_of(result))}")
    return result


def load_page_with_recovery(
    client: httpx.Client,
    headers: dict,
    ui_server: str,
    window_id: str,
    uid: int,
    max_retries: int = 2,
) -> tuple[str, dict]:
    """Load a price page with error recovery.

    On failure, closes the corrupted window and opens a fresh one.

    Args:
        client: Open httpx.Client
        headers: Authorized request headers
        ui_server: UI server base URL from the router
        window_id: Current window (may be replaced on error)
        uid: Price page UID to load
        max_retries: Number of retry attempts

    Returns:
        Tuple of (current_window_id, result_dict)
    """
    for attempt in range(max_retries + 1):
        try:
            result = load_page(client, headers, ui_server, window_id, uid)
            return window_id, {"success": True, "result": result}

        except (httpx.HTTPError, RuntimeError) as e:
            print(f"Attempt {attempt + 1} failed for {uid}: {e}")

            # Close the potentially corrupted window
            try:
                close_window(client, headers, ui_server, window_id)
            except httpx.HTTPError:
                pass  # Window may already be in bad state

            if attempt < max_retries:
                # Open a fresh window and retry
                window_id = open_window(client, headers, ui_server, SERVICE_NAME)
            else:
                # All retries exhausted - reopen window for next item
                window_id = open_window(client, headers, ui_server, SERVICE_NAME)
                return window_id, {"success": False, "error": str(e)}

    # Should not reach here, but just in case
    return window_id, {"success": False, "error": "Unexpected retry exhaustion"}


with httpx.Client(verify=VERIFY_SSL, timeout=120, follow_redirects=True) as client:
    token = get_token(client)
    ui_server = get_ui_server(client, token)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",       # without this you get XML, not JSON
        "Content-Type": "application/json",
    }

    start_session(client, headers, ui_server)
    window_id = open_window(client, headers, ui_server, SERVICE_NAME)
    try:
        for uid in PRICE_PAGE_UIDS:
            window_id, outcome = load_page_with_recovery(
                client, headers, ui_server, window_id, uid, MAX_RETRIES
            )
            flag = "OK  " if outcome["success"] else "FAIL"
            print(f"{flag} uid={uid} {outcome.get('error', '')}")
    finally:
        close_window(client, headers, ui_server, window_id)
        end_session(client, headers, ui_server)
```

**C#:**

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string ServiceName = "SalesPricePage";
const int MaxRetries = 2;                              // retry attempts per record
int[] pricePageUids = { 100198, 999999999, 100199 };   // middle UID is deliberately bad
// ---------------------------------------------------------------------------

var handler = new HttpClientHandler
{
    // Test tenants often present a self-signed cert. Delete this line in production.
    ServerCertificateCustomValidationCallback =
        HttpClientHandler.DangerousAcceptAnyServerCertificateValidator,
};
using var client = new HttpClient(handler) { Timeout = TimeSpan.FromMinutes(2) };
client.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));

var token = await GetTokenAsync(client);
var uiServer = await GetUiServerAsync(client, token);
client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);

await StartSessionAsync(client, uiServer);
string windowId = await OpenWindowAsync(client, uiServer, ServiceName);
try
{
    foreach (int uid in pricePageUids)
    {
        var (nextWindowId, outcome) = await LoadPageWithRecoveryAsync(
            client, uiServer, windowId, uid, MaxRetries);
        windowId = nextWindowId;
        Console.WriteLine($"{(outcome.Success ? "OK  " : "FAIL")} uid={uid} {outcome.Error}");
    }
}
finally
{
    await CloseWindowAsync(client, uiServer, windowId);
    await EndSessionAsync(client, uiServer);
}

// --- recovery wrapper ------------------------------------------------------

// Load a price page with error recovery.
// On failure, closes the corrupted window and opens a fresh one.
static async Task<(string WindowId, RecoveryOutcome Outcome)> LoadPageWithRecoveryAsync(
    HttpClient client, string uiServer, string windowId, int uid, int maxRetries)
{
    for (int attempt = 0; attempt <= maxRetries; attempt++)
    {
        try
        {
            await LoadPageAsync(client, uiServer, windowId, uid);
            return (windowId, new RecoveryOutcome(true, ""));
        }
        catch (Exception ex) when (ex is HttpRequestException or InvalidOperationException)
        {
            Console.WriteLine($"Attempt {attempt + 1} failed for {uid}: {ex.Message}");

            // Close the potentially corrupted window
            try { await CloseWindowAsync(client, uiServer, windowId); }
            catch (HttpRequestException) { /* Window may already be in bad state */ }

            if (attempt < maxRetries)
            {
                // Open a fresh window and retry
                windowId = await OpenWindowAsync(client, uiServer, ServiceName);
            }
            else
            {
                // All retries exhausted - reopen window for next item
                windowId = await OpenWindowAsync(client, uiServer, ServiceName);
                return (windowId, new RecoveryOutcome(false, ex.Message));
            }
        }
    }

    // Should not reach here, but just in case
    return (windowId, new RecoveryOutcome(false, "Unexpected retry exhaustion"));
}

// Load one price page, throwing on anything that is not Success.
// On 2026.1 a nonexistent record loads as Status 2 with an empty window and
// Messages [{"Text": "Enter a valid ID or leave ID blank."}].
static async Task<JsonElement> LoadPageAsync(
    HttpClient client, string uiServer, string windowId, int uid)
{
    var result = await ChangeFieldAsync(
        client, uiServer, windowId, "FORM", "form", "price_page_uid", uid.ToString());
    int status = StatusOf(result);
    if (status != 1)
        throw new InvalidOperationException(
            $"status={status} {string.Join("; ", MessagesOf(result))}");
    return result;
}

// --- Interactive API helpers -----------------------------------------------

// Start an Interactive session. 2026.1 renamed SessionId -> Id; read both.
static async Task<string> StartSessionAsync(HttpClient client, string uiServer)
{
    var resp = await SendAsync(client, HttpMethod.Post,
        $"{uiServer}/api/ui/interactive/sessions/",
        new Dictionary<string, object> { ["ResponseWindowHandlingEnabled"] = false });
    if (resp.ValueKind == JsonValueKind.Object)
    {
        if (resp.TryGetProperty("Id", out var id)) return id.GetString() ?? "";
        if (resp.TryGetProperty("SessionId", out var sid)) return sid.GetString() ?? "";
    }
    return "";
}

// Always call this - a leaked session 409s the next create.
static async Task EndSessionAsync(HttpClient client, string uiServer)
{
    using var request = new HttpRequestMessage(
        HttpMethod.Delete, $"{uiServer}/api/ui/interactive/sessions/");
    await client.SendAsync(request);
}

static async Task<string> OpenWindowAsync(
    HttpClient client, string uiServer, string serviceName)
{
    var resp = await SendAsync(client, HttpMethod.Post,
        $"{uiServer}/api/ui/interactive/v2/window",
        new Dictionary<string, object> { ["ServiceName"] = serviceName });
    if (resp.ValueKind == JsonValueKind.Object)
    {
        if (resp.TryGetProperty("WindowId", out var id)) return id.GetString() ?? "";
        if (resp.TryGetProperty("windowId", out var lower)) return lower.GetString() ?? "";
    }
    return "";
}

static async Task CloseWindowAsync(HttpClient client, string uiServer, string windowId)
{
    using var request = new HttpRequestMessage(
        HttpMethod.Delete, $"{uiServer}/api/ui/interactive/v2/window?id={windowId}");
    await client.SendAsync(request);
}

// Change one field. One field per call - batched /v2/change is non-atomic.
static async Task<JsonElement> ChangeFieldAsync(
    HttpClient client, string uiServer, string windowId,
    string tab, string datawindow, string field, string value)
{
    var payload = new Dictionary<string, object>
    {
        ["WindowId"] = windowId,
        ["List"] = new[]
        {
            new Dictionary<string, object>
            {
                ["TabName"] = tab,
                ["DatawindowName"] = datawindow,   // required since 25.2
                ["FieldName"] = field,
                ["Value"] = value,
            },
        },
    };
    return await SendAsync(client, HttpMethod.Put,
        $"{uiServer}/api/ui/interactive/v2/change", payload);
}

// ResultStatus enum: None=0, Success=1, Failure=2, Blocked=3.
static int StatusOf(JsonElement result)
{
    if (result.ValueKind != JsonValueKind.Object ||
        !result.TryGetProperty("Status", out var status))
        return 0;
    return status.ValueKind switch
    {
        JsonValueKind.Number => status.GetInt32(),
        JsonValueKind.String => status.GetString() switch
        {
            "Success" => 1,
            "Failure" => 2,
            "Blocked" => 3,
            _ => 0,
        },
        _ => 0,
    };
}

// Failure detail lives in the top-level Messages array, not in Events.
static List<string> MessagesOf(JsonElement result)
{
    var messages = new List<string>();
    if (result.ValueKind == JsonValueKind.Object &&
        result.TryGetProperty("Messages", out var arr) &&
        arr.ValueKind == JsonValueKind.Array)
    {
        foreach (var message in arr.EnumerateArray())
            messages.Add(message.TryGetProperty("Text", out var text)
                ? text.GetString() ?? "" : "");
    }
    return messages;
}

static async Task<JsonElement> SendAsync(
    HttpClient client, HttpMethod method, string url, object? body = null)
{
    using var request = new HttpRequestMessage(method, url);
    if (body is not null)
        request.Content = new StringContent(
            JsonSerializer.Serialize(body), Encoding.UTF8, "application/json");
    var response = await client.SendAsync(request);
    response.EnsureSuccessStatusCode();
    var text = await response.Content.ReadAsStringAsync();
    if (string.IsNullOrWhiteSpace(text)) return default;
    using var doc = JsonDocument.Parse(text);
    return doc.RootElement.Clone();
}

// --- auth helpers ----------------------------------------------------------

// v2 token endpoint — credentials go in the body, never in headers.
static async Task<string> GetTokenAsync(HttpClient client)
{
    var payload = JsonSerializer.Serialize(new { username = Username, password = Password });
    var response = await client.PostAsync(
        $"{BaseUrl}/api/security/token/v2",
        new StringContent(payload, Encoding.UTF8, "application/json"));
    response.EnsureSuccessStatusCode();
    return ReadField(await response.Content.ReadAsStringAsync(), "AccessToken");
}

// Transaction and Interactive calls go to the UI server, not BaseUrl.
static async Task<string> GetUiServerAsync(HttpClient client, string token)
{
    using var request = new HttpRequestMessage(
        HttpMethod.Get, $"{BaseUrl}/api/ui/router/v1/?urlType=external");
    request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
    var response = await client.SendAsync(request);
    response.EnsureSuccessStatusCode();
    return ReadField(await response.Content.ReadAsStringAsync(), "Url").TrimEnd('/');
}

// Some middleware answers these two endpoints in XML even when asked for JSON.
static string ReadField(string payload, string field)
{
    try
    {
        var value = JsonDocument.Parse(payload).RootElement.GetProperty(field).GetString();
        if (!string.IsNullOrEmpty(value)) return value;
    }
    catch (Exception ex) when (ex is JsonException or KeyNotFoundException) { }

    var match = System.Text.RegularExpressions.Regex.Match(payload, $"<{field}>([^<]+)</{field}>");
    if (!match.Success)
        throw new InvalidOperationException(
            $"No {field} in response: {payload[..Math.Min(200, payload.Length)]}");
    return match.Groups[1].Value;
}

// --- result record ---------------------------------------------------------

record RecoveryOutcome(bool Success, string Error);
```

<!-- /tabs -->

### Why Not Recover In-Place?

| Recovery Strategy | Outcome |
|-------------------|---------|
| Clear data and retry | May fail - unsaved changes can persist |
| Cancel changes and retry | May fail - dialogs may be blocking |
| Close window and reopen | Reliable - guaranteed clean state |

The close-and-reopen strategy costs ~500ms but guarantees a clean state. For bulk operations, this reliability far outweighs the small performance cost.

---

## Page Expiration Workflow

Creating new price pages often requires expiring old ones to prevent pricing conflicts. If both an old and new page are active for the same supplier/product group, P21 may apply either one unpredictably.

### Pattern: Expire Before Replace

<!-- tabs -->

**Python:**

```python
"""Expire one price page by setting its expiration date, then read it back."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
PRICE_PAGE_UID = 100198                   # page to expire
EXPIRATION_DATE = "2030-12-31"            # YYYY-MM-DD
SERVICE_NAME = "SalesPricePage"
# ---------------------------------------------------------------------------


def get_token(client: httpx.Client) -> str:
    """v2 token endpoint — credentials go in the body, never in headers."""
    r = client.post(
        f"{BASE_URL}/api/security/token/v2",
        json={"username": USERNAME, "password": PASSWORD},
        headers={"Accept": "application/json"},
    )
    r.raise_for_status()
    try:
        return r.json()["AccessToken"]
    except (ValueError, KeyError):  # some middleware answers in XML
        match = re.search(r"<AccessToken>([^<]+)</AccessToken>", r.text)
        if not match:
            raise ValueError(f"No AccessToken in response: {r.text[:200]}") from None
        return match.group(1)


def get_ui_server(client: httpx.Client, token: str) -> str:
    """Transaction and Interactive calls go to the UI server, not BASE_URL."""
    r = client.get(
        f"{BASE_URL}/api/ui/router/v1/?urlType=external",  # trailing slash avoids a 307
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )
    r.raise_for_status()
    try:
        return r.json()["Url"].rstrip("/")
    except (ValueError, KeyError):
        match = re.search(r"<Url>([^<]+)</Url>", r.text)
        if not match:
            raise ValueError(f"No Url in router response: {r.text[:200]}") from None
        return match.group(1).rstrip("/")


def status_of(result: dict) -> int:
    """ResultStatus enum: None=0, Success=1, Failure=2, Blocked=3."""
    status = result.get("Status", 0)
    if isinstance(status, str):
        return {"None": 0, "Success": 1, "Failure": 2, "Blocked": 3}.get(status, 0)
    return status


def messages_of(result: dict) -> list[str]:
    """Failure detail lives in the top-level Messages array, not in Events."""
    return [m.get("Text", "") for m in result.get("Messages", [])]


def start_session(client: httpx.Client, headers: dict, ui_server: str) -> str:
    """Start an Interactive session. 2026.1 renamed SessionId -> Id; read both."""
    r = client.post(
        f"{ui_server}/api/ui/interactive/sessions/",
        json={"ResponseWindowHandlingEnabled": False},
        headers=headers,
    )
    r.raise_for_status()
    data = r.json()
    return data.get("Id") or data.get("SessionId", "")


def end_session(client: httpx.Client, headers: dict, ui_server: str) -> None:
    """Always call this — a leaked session 409s the next create."""
    client.delete(f"{ui_server}/api/ui/interactive/sessions/", headers=headers)


def open_window(client: httpx.Client, headers: dict, ui_server: str, service: str) -> str:
    r = client.post(
        f"{ui_server}/api/ui/interactive/v2/window",
        json={"ServiceName": service},
        headers=headers,
    )
    r.raise_for_status()
    data = r.json()
    return data.get("WindowId") or data.get("windowId", "")


def close_window(client: httpx.Client, headers: dict, ui_server: str, window_id: str) -> None:
    client.delete(
        f"{ui_server}/api/ui/interactive/v2/window",
        params={"id": window_id},
        headers=headers,
    )


def change_field(
    client: httpx.Client,
    headers: dict,
    ui_server: str,
    window_id: str,
    tab: str,
    datawindow: str,
    field: str,
    value: str,
) -> dict:
    """Change one field. One field per call — batched /v2/change is non-atomic."""
    payload = {
        "WindowId": window_id,
        "List": [
            {
                "TabName": tab,
                "DatawindowName": datawindow,  # required since 25.2
                "FieldName": field,
                "Value": value,
            }
        ],
    }
    r = client.put(
        f"{ui_server}/api/ui/interactive/v2/change", json=payload, headers=headers
    )
    r.raise_for_status()
    return r.json()


def save_window(client: httpx.Client, headers: dict, ui_server: str, window_id: str) -> dict:
    """Save. The v2 body is the bare window-id GUID as a JSON string."""
    r = client.put(
        f"{ui_server}/api/ui/interactive/v2/data", json=window_id, headers=headers
    )
    r.raise_for_status()
    return r.json()


def read_field(
    client: httpx.Client,
    headers: dict,
    ui_server: str,
    window_id: str,
    datawindow: str,
    field: str,
) -> str | None:
    """Read one field back off the window's ACTIVE surface.

    GET /v2/data returns the datawindows on the active surface only, and on
    2026.1 only a varying subset of them — a missing field proves nothing.
    """
    r = client.get(
        f"{ui_server}/api/ui/interactive/v2/data",
        params={"id": window_id},
        headers=headers,
    )
    r.raise_for_status()
    for dw in r.json():
        columns = dw.get("Columns", [])
        rows = dw.get("Data", [])
        if dw.get("Name") == datawindow and field in columns and rows:
            return rows[dw.get("ActiveRow", 0)][columns.index(field)]
    return None


def expire_price_page(
    client: httpx.Client,
    headers: dict,
    ui_server: str,
    window_id: str,
    price_page_uid: int,
    expiration_date: str,
) -> bool:
    """Expire a price page by setting its expiration date.

    Args:
        client: Open httpx.Client
        headers: Authorized request headers
        ui_server: UI server base URL from the router
        window_id: Open SalesPricePage window
        price_page_uid: UID of the page to expire
        expiration_date: Date to expire the page (YYYY-MM-DD format)

    Returns:
        True if the save succeeded AND the read-back matched
    """
    # Load the page by UID
    result = change_field(
        client, headers, ui_server, window_id,
        "FORM", "form", "price_page_uid", str(price_page_uid),
    )
    if status_of(result) != 1:
        print(f"Failed to load page {price_page_uid}: {messages_of(result)}")
        return False

    # Set the expiration date
    result = change_field(
        client, headers, ui_server, window_id,
        "FORM", "form", "expiration_date", expiration_date,
    )
    if status_of(result) != 1:
        print(f"Failed to set expiration date: {messages_of(result)}")
        return False

    # Save
    result = save_window(client, headers, ui_server, window_id)
    if status_of(result) != 1:
        print(f"Failed to save expiration: {messages_of(result)}")
        return False

    # Read back — a save can report success without persisting the edit
    landed = read_field(client, headers, ui_server, window_id, "form", "expiration_date")
    print(f"Expired page {price_page_uid}: expiration_date reads back as {landed!r}")
    return landed is not None and landed.startswith(expiration_date)


with httpx.Client(verify=VERIFY_SSL, timeout=120, follow_redirects=True) as client:
    token = get_token(client)
    ui_server = get_ui_server(client, token)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",       # without this you get XML, not JSON
        "Content-Type": "application/json",
    }

    start_session(client, headers, ui_server)
    window_id = open_window(client, headers, ui_server, SERVICE_NAME)
    try:
        ok = expire_price_page(
            client, headers, ui_server, window_id, PRICE_PAGE_UID, EXPIRATION_DATE
        )
        print("OK" if ok else "FAILED")
    finally:
        close_window(client, headers, ui_server, window_id)
        end_session(client, headers, ui_server)
```

**C#:**

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string ServiceName = "SalesPricePage";
const int PricePageUid = 100198;                       // page to expire
const string ExpirationDate = "2030-12-31";            // YYYY-MM-DD
// ---------------------------------------------------------------------------

var handler = new HttpClientHandler
{
    // Test tenants often present a self-signed cert. Delete this line in production.
    ServerCertificateCustomValidationCallback =
        HttpClientHandler.DangerousAcceptAnyServerCertificateValidator,
};
using var client = new HttpClient(handler) { Timeout = TimeSpan.FromMinutes(2) };
client.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));

var token = await GetTokenAsync(client);
var uiServer = await GetUiServerAsync(client, token);
client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);

await StartSessionAsync(client, uiServer);
string windowId = await OpenWindowAsync(client, uiServer, ServiceName);
try
{
    bool ok = await ExpirePricePageAsync(
        client, uiServer, windowId, PricePageUid, ExpirationDate);
    Console.WriteLine(ok ? "OK" : "FAILED");
}
finally
{
    await CloseWindowAsync(client, uiServer, windowId);
    await EndSessionAsync(client, uiServer);
}

// --- expiration ------------------------------------------------------------

// Expire a price page by setting its expiration date.
// Returns true only when the save succeeded AND the read-back matched.
static async Task<bool> ExpirePricePageAsync(
    HttpClient client, string uiServer, string windowId,
    int pricePageUid, string expirationDate)
{
    // Load the page by UID
    var result = await ChangeFieldAsync(
        client, uiServer, windowId,
        "FORM", "form", "price_page_uid", pricePageUid.ToString());
    if (StatusOf(result) != 1)
    {
        Console.WriteLine($"Failed to load page {pricePageUid}: " +
            string.Join("; ", MessagesOf(result)));
        return false;
    }

    // Set the expiration date
    result = await ChangeFieldAsync(
        client, uiServer, windowId, "FORM", "form", "expiration_date", expirationDate);
    if (StatusOf(result) != 1)
    {
        Console.WriteLine("Failed to set expiration date: " +
            string.Join("; ", MessagesOf(result)));
        return false;
    }

    // Save
    result = await SaveWindowAsync(client, uiServer, windowId);
    if (StatusOf(result) != 1)
    {
        Console.WriteLine("Failed to save expiration: " +
            string.Join("; ", MessagesOf(result)));
        return false;
    }

    // Read back - a save can report success without persisting the edit
    string? landed = await ReadFieldAsync(
        client, uiServer, windowId, "form", "expiration_date");
    Console.WriteLine(
        $"Expired page {pricePageUid}: expiration_date reads back as {landed ?? "(null)"}");
    return landed is not null && landed.StartsWith(expirationDate);
}

// --- Interactive API helpers -----------------------------------------------

// Start an Interactive session. 2026.1 renamed SessionId -> Id; read both.
static async Task<string> StartSessionAsync(HttpClient client, string uiServer)
{
    var resp = await SendAsync(client, HttpMethod.Post,
        $"{uiServer}/api/ui/interactive/sessions/",
        new Dictionary<string, object> { ["ResponseWindowHandlingEnabled"] = false });
    if (resp.ValueKind == JsonValueKind.Object)
    {
        if (resp.TryGetProperty("Id", out var id)) return id.GetString() ?? "";
        if (resp.TryGetProperty("SessionId", out var sid)) return sid.GetString() ?? "";
    }
    return "";
}

// Always call this - a leaked session 409s the next create.
static async Task EndSessionAsync(HttpClient client, string uiServer)
{
    using var request = new HttpRequestMessage(
        HttpMethod.Delete, $"{uiServer}/api/ui/interactive/sessions/");
    await client.SendAsync(request);
}

static async Task<string> OpenWindowAsync(
    HttpClient client, string uiServer, string serviceName)
{
    var resp = await SendAsync(client, HttpMethod.Post,
        $"{uiServer}/api/ui/interactive/v2/window",
        new Dictionary<string, object> { ["ServiceName"] = serviceName });
    if (resp.ValueKind == JsonValueKind.Object)
    {
        if (resp.TryGetProperty("WindowId", out var id)) return id.GetString() ?? "";
        if (resp.TryGetProperty("windowId", out var lower)) return lower.GetString() ?? "";
    }
    return "";
}

static async Task CloseWindowAsync(HttpClient client, string uiServer, string windowId)
{
    using var request = new HttpRequestMessage(
        HttpMethod.Delete, $"{uiServer}/api/ui/interactive/v2/window?id={windowId}");
    await client.SendAsync(request);
}

// Change one field. One field per call - batched /v2/change is non-atomic.
static async Task<JsonElement> ChangeFieldAsync(
    HttpClient client, string uiServer, string windowId,
    string tab, string datawindow, string field, string value)
{
    var payload = new Dictionary<string, object>
    {
        ["WindowId"] = windowId,
        ["List"] = new[]
        {
            new Dictionary<string, object>
            {
                ["TabName"] = tab,
                ["DatawindowName"] = datawindow,   // required since 25.2
                ["FieldName"] = field,
                ["Value"] = value,
            },
        },
    };
    return await SendAsync(client, HttpMethod.Put,
        $"{uiServer}/api/ui/interactive/v2/change", payload);
}

// Save. The v2 body is the bare window-id GUID as a JSON string.
static async Task<JsonElement> SaveWindowAsync(
    HttpClient client, string uiServer, string windowId)
{
    return await SendAsync(client, HttpMethod.Put,
        $"{uiServer}/api/ui/interactive/v2/data", windowId);
}

// Read one field back off the window's ACTIVE surface.
// GET /v2/data returns the datawindows on the active surface only, and on
// 2026.1 only a varying subset of them - a missing field proves nothing.
static async Task<string?> ReadFieldAsync(
    HttpClient client, string uiServer, string windowId,
    string datawindow, string field)
{
    var resp = await SendAsync(client, HttpMethod.Get,
        $"{uiServer}/api/ui/interactive/v2/data?id={windowId}");
    if (resp.ValueKind != JsonValueKind.Array) return null;

    foreach (var dw in resp.EnumerateArray())
    {
        if (!dw.TryGetProperty("Name", out var name) || name.GetString() != datawindow)
            continue;
        if (!dw.TryGetProperty("Columns", out var columns) ||
            !dw.TryGetProperty("Data", out var rows) ||
            rows.GetArrayLength() == 0)
            continue;

        int index = -1, i = 0;
        foreach (var column in columns.EnumerateArray())
        {
            if (column.GetString() == field) { index = i; break; }
            i++;
        }
        if (index < 0) continue;

        int activeRow = dw.TryGetProperty("ActiveRow", out var ar) ? ar.GetInt32() : 0;
        return rows[activeRow][index].ToString();
    }
    return null;
}

// ResultStatus enum: None=0, Success=1, Failure=2, Blocked=3.
static int StatusOf(JsonElement result)
{
    if (result.ValueKind != JsonValueKind.Object ||
        !result.TryGetProperty("Status", out var status))
        return 0;
    return status.ValueKind switch
    {
        JsonValueKind.Number => status.GetInt32(),
        JsonValueKind.String => status.GetString() switch
        {
            "Success" => 1,
            "Failure" => 2,
            "Blocked" => 3,
            _ => 0,
        },
        _ => 0,
    };
}

// Failure detail lives in the top-level Messages array, not in Events.
static List<string> MessagesOf(JsonElement result)
{
    var messages = new List<string>();
    if (result.ValueKind == JsonValueKind.Object &&
        result.TryGetProperty("Messages", out var arr) &&
        arr.ValueKind == JsonValueKind.Array)
    {
        foreach (var message in arr.EnumerateArray())
            messages.Add(message.TryGetProperty("Text", out var text)
                ? text.GetString() ?? "" : "");
    }
    return messages;
}

static async Task<JsonElement> SendAsync(
    HttpClient client, HttpMethod method, string url, object? body = null)
{
    using var request = new HttpRequestMessage(method, url);
    if (body is not null)
        request.Content = new StringContent(
            JsonSerializer.Serialize(body), Encoding.UTF8, "application/json");
    var response = await client.SendAsync(request);
    response.EnsureSuccessStatusCode();
    var text = await response.Content.ReadAsStringAsync();
    if (string.IsNullOrWhiteSpace(text)) return default;
    using var doc = JsonDocument.Parse(text);
    return doc.RootElement.Clone();
}

// --- auth helpers ----------------------------------------------------------

// v2 token endpoint — credentials go in the body, never in headers.
static async Task<string> GetTokenAsync(HttpClient client)
{
    var payload = JsonSerializer.Serialize(new { username = Username, password = Password });
    var response = await client.PostAsync(
        $"{BaseUrl}/api/security/token/v2",
        new StringContent(payload, Encoding.UTF8, "application/json"));
    response.EnsureSuccessStatusCode();
    return ReadField(await response.Content.ReadAsStringAsync(), "AccessToken");
}

// Transaction and Interactive calls go to the UI server, not BaseUrl.
static async Task<string> GetUiServerAsync(HttpClient client, string token)
{
    using var request = new HttpRequestMessage(
        HttpMethod.Get, $"{BaseUrl}/api/ui/router/v1/?urlType=external");
    request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
    var response = await client.SendAsync(request);
    response.EnsureSuccessStatusCode();
    return ReadField(await response.Content.ReadAsStringAsync(), "Url").TrimEnd('/');
}

// Some middleware answers these two endpoints in XML even when asked for JSON.
static string ReadField(string payload, string field)
{
    try
    {
        var value = JsonDocument.Parse(payload).RootElement.GetProperty(field).GetString();
        if (!string.IsNullOrEmpty(value)) return value;
    }
    catch (Exception ex) when (ex is JsonException or KeyNotFoundException) { }

    var match = System.Text.RegularExpressions.Regex.Match(payload, $"<{field}>([^<]+)</{field}>");
    if (!match.Success)
        throw new InvalidOperationException(
            $"No {field} in response: {payload[..Math.Min(200, payload.Length)]}");
    return match.Groups[1].Value;
}
```

<!-- /tabs -->

> **Verify after save:** A save can report success without persisting your edits (silently-dropped changes look identical by status code). After every save, read the record back and compare — see [Verifying Writes](04-Interactive-API.md#verifying-writes-dont-trust-save-status-alone).

### Bulk Expiration

Expiration follows the same batch patterns as creation. Process in batches with session-per-batch:

<!-- tabs -->

**Python:**

```python
"""Bulk expire price pages: session per batch, one window per batch, read-back each."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
PAGE_UIDS = [100198, 100199, 100200]      # pages to expire
EXPIRATION_DATE = "2030-12-31"            # YYYY-MM-DD
BATCH_SIZE = 25                           # pages per session batch
SERVICE_NAME = "SalesPricePage"
# ---------------------------------------------------------------------------


def get_token(client: httpx.Client) -> str:
    """v2 token endpoint — credentials go in the body, never in headers."""
    r = client.post(
        f"{BASE_URL}/api/security/token/v2",
        json={"username": USERNAME, "password": PASSWORD},
        headers={"Accept": "application/json"},
    )
    r.raise_for_status()
    try:
        return r.json()["AccessToken"]
    except (ValueError, KeyError):  # some middleware answers in XML
        match = re.search(r"<AccessToken>([^<]+)</AccessToken>", r.text)
        if not match:
            raise ValueError(f"No AccessToken in response: {r.text[:200]}") from None
        return match.group(1)


def get_ui_server(client: httpx.Client, token: str) -> str:
    """Transaction and Interactive calls go to the UI server, not BASE_URL."""
    r = client.get(
        f"{BASE_URL}/api/ui/router/v1/?urlType=external",  # trailing slash avoids a 307
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )
    r.raise_for_status()
    try:
        return r.json()["Url"].rstrip("/")
    except (ValueError, KeyError):
        match = re.search(r"<Url>([^<]+)</Url>", r.text)
        if not match:
            raise ValueError(f"No Url in router response: {r.text[:200]}") from None
        return match.group(1).rstrip("/")


def status_of(result: dict) -> int:
    """ResultStatus enum: None=0, Success=1, Failure=2, Blocked=3."""
    status = result.get("Status", 0)
    if isinstance(status, str):
        return {"None": 0, "Success": 1, "Failure": 2, "Blocked": 3}.get(status, 0)
    return status


def messages_of(result: dict) -> list[str]:
    """Failure detail lives in the top-level Messages array, not in Events."""
    return [m.get("Text", "") for m in result.get("Messages", [])]


def start_session(client: httpx.Client, headers: dict, ui_server: str) -> str:
    """Start an Interactive session. 2026.1 renamed SessionId -> Id; read both."""
    r = client.post(
        f"{ui_server}/api/ui/interactive/sessions/",
        json={"ResponseWindowHandlingEnabled": False},
        headers=headers,
    )
    r.raise_for_status()
    data = r.json()
    return data.get("Id") or data.get("SessionId", "")


def end_session(client: httpx.Client, headers: dict, ui_server: str) -> None:
    """Always call this — a leaked session 409s the next create."""
    client.delete(f"{ui_server}/api/ui/interactive/sessions/", headers=headers)


def open_window(client: httpx.Client, headers: dict, ui_server: str, service: str) -> str:
    r = client.post(
        f"{ui_server}/api/ui/interactive/v2/window",
        json={"ServiceName": service},
        headers=headers,
    )
    r.raise_for_status()
    data = r.json()
    return data.get("WindowId") or data.get("windowId", "")


def close_window(client: httpx.Client, headers: dict, ui_server: str, window_id: str) -> None:
    client.delete(
        f"{ui_server}/api/ui/interactive/v2/window",
        params={"id": window_id},
        headers=headers,
    )


def clear_window(client: httpx.Client, headers: dict, ui_server: str, window_id: str) -> None:
    """Reset the form for the next record in the batch."""
    r = client.delete(
        f"{ui_server}/api/ui/interactive/v2/data",
        params={"id": window_id},
        headers=headers,
    )
    r.raise_for_status()


def change_field(
    client: httpx.Client,
    headers: dict,
    ui_server: str,
    window_id: str,
    tab: str,
    datawindow: str,
    field: str,
    value: str,
) -> dict:
    """Change one field. One field per call — batched /v2/change is non-atomic."""
    payload = {
        "WindowId": window_id,
        "List": [
            {
                "TabName": tab,
                "DatawindowName": datawindow,  # required since 25.2
                "FieldName": field,
                "Value": value,
            }
        ],
    }
    r = client.put(
        f"{ui_server}/api/ui/interactive/v2/change", json=payload, headers=headers
    )
    r.raise_for_status()
    return r.json()


def save_window(client: httpx.Client, headers: dict, ui_server: str, window_id: str) -> dict:
    """Save. The v2 body is the bare window-id GUID as a JSON string."""
    r = client.put(
        f"{ui_server}/api/ui/interactive/v2/data", json=window_id, headers=headers
    )
    r.raise_for_status()
    return r.json()


def read_field(
    client: httpx.Client,
    headers: dict,
    ui_server: str,
    window_id: str,
    datawindow: str,
    field: str,
) -> str | None:
    """Read one field back off the window's ACTIVE surface."""
    r = client.get(
        f"{ui_server}/api/ui/interactive/v2/data",
        params={"id": window_id},
        headers=headers,
    )
    r.raise_for_status()
    for dw in r.json():
        columns = dw.get("Columns", [])
        rows = dw.get("Data", [])
        if dw.get("Name") == datawindow and field in columns and rows:
            return rows[dw.get("ActiveRow", 0)][columns.index(field)]
    return None


def expire_price_page(
    client: httpx.Client,
    headers: dict,
    ui_server: str,
    window_id: str,
    price_page_uid: int,
    expiration_date: str,
) -> bool:
    """Expire one page and confirm the new date read back off the window."""
    result = change_field(
        client, headers, ui_server, window_id,
        "FORM", "form", "price_page_uid", str(price_page_uid),
    )
    if status_of(result) != 1:
        print(f"Failed to load page {price_page_uid}: {messages_of(result)}")
        return False

    result = change_field(
        client, headers, ui_server, window_id,
        "FORM", "form", "expiration_date", expiration_date,
    )
    if status_of(result) != 1:
        print(f"Failed to set expiration date: {messages_of(result)}")
        return False

    result = save_window(client, headers, ui_server, window_id)
    if status_of(result) != 1:
        print(f"Failed to save expiration: {messages_of(result)}")
        return False

    landed = read_field(client, headers, ui_server, window_id, "form", "expiration_date")
    print(f"  {price_page_uid}: expiration_date reads back as {landed!r}")
    return landed is not None and landed.startswith(expiration_date)


def expire_old_pages(
    client: httpx.Client,
    headers: dict,
    ui_server: str,
    page_uids: list[int],
    expiration_date: str,
    batch_size: int = 25,
) -> dict:
    """Bulk expire price pages.

    Args:
        client: Open httpx.Client
        headers: Authorized request headers
        ui_server: UI server base URL from the router
        page_uids: List of price page UIDs to expire
        expiration_date: Expiration date (YYYY-MM-DD)
        batch_size: Pages per session batch

    Returns:
        Summary with success/failure counts
    """
    succeeded = 0
    failed = 0

    for i in range(0, len(page_uids), batch_size):
        batch = page_uids[i:i + batch_size]

        start_session(client, headers, ui_server)
        try:
            window_id = open_window(client, headers, ui_server, SERVICE_NAME)

            try:
                for uid in batch:
                    success = expire_price_page(
                        client, headers, ui_server, window_id, uid, expiration_date
                    )
                    if success:
                        succeeded += 1
                        clear_window(client, headers, ui_server, window_id)
                    else:
                        failed += 1
                        # Reopen window on failure
                        close_window(client, headers, ui_server, window_id)
                        window_id = open_window(
                            client, headers, ui_server, SERVICE_NAME
                        )
            finally:
                close_window(client, headers, ui_server, window_id)
        finally:
            end_session(client, headers, ui_server)

    return {"succeeded": succeeded, "failed": failed, "total": len(page_uids)}


with httpx.Client(verify=VERIFY_SSL, timeout=120, follow_redirects=True) as client:
    token = get_token(client)
    ui_server = get_ui_server(client, token)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",       # without this you get XML, not JSON
        "Content-Type": "application/json",
    }

    summary = expire_old_pages(
        client, headers, ui_server, PAGE_UIDS, EXPIRATION_DATE, BATCH_SIZE
    )
    print(f"succeeded={summary['succeeded']} failed={summary['failed']} "
          f"total={summary['total']}")
```

**C#:**

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string ServiceName = "SalesPricePage";
const string ExpirationDate = "2030-12-31";            // YYYY-MM-DD
const int BatchSize = 25;                              // pages per session batch
int[] pageUids = { 100198, 100199, 100200 };           // pages to expire
// ---------------------------------------------------------------------------

var handler = new HttpClientHandler
{
    // Test tenants often present a self-signed cert. Delete this line in production.
    ServerCertificateCustomValidationCallback =
        HttpClientHandler.DangerousAcceptAnyServerCertificateValidator,
};
using var client = new HttpClient(handler) { Timeout = TimeSpan.FromMinutes(2) };
client.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));

var token = await GetTokenAsync(client);
var uiServer = await GetUiServerAsync(client, token);
client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);

var summary = await ExpireOldPagesAsync(
    client, uiServer, pageUids, ExpirationDate, BatchSize);
Console.WriteLine(
    $"succeeded={summary["succeeded"]} failed={summary["failed"]} " +
    $"total={summary["total"]}");

// --- bulk expiration -------------------------------------------------------

// Bulk expire price pages: one session and one window per batch.
static async Task<Dictionary<string, int>> ExpireOldPagesAsync(
    HttpClient client, string uiServer, IReadOnlyList<int> pageUids,
    string expirationDate, int batchSize)
{
    int succeeded = 0;
    int failed = 0;

    for (int i = 0; i < pageUids.Count; i += batchSize)
    {
        var batch = pageUids.Skip(i).Take(batchSize).ToList();

        await StartSessionAsync(client, uiServer);
        try
        {
            string windowId = await OpenWindowAsync(client, uiServer, ServiceName);

            try
            {
                foreach (int uid in batch)
                {
                    bool success = await ExpirePricePageAsync(
                        client, uiServer, windowId, uid, expirationDate);
                    if (success)
                    {
                        succeeded++;
                        await ClearWindowAsync(client, uiServer, windowId);
                    }
                    else
                    {
                        failed++;
                        // Reopen window on failure
                        await CloseWindowAsync(client, uiServer, windowId);
                        windowId = await OpenWindowAsync(client, uiServer, ServiceName);
                    }
                }
            }
            finally
            {
                await CloseWindowAsync(client, uiServer, windowId);
            }
        }
        finally
        {
            await EndSessionAsync(client, uiServer);
        }
    }

    return new Dictionary<string, int>
    {
        ["succeeded"] = succeeded,
        ["failed"] = failed,
        ["total"] = pageUids.Count,
    };
}

// Expire one page and confirm the new date read back off the window.
static async Task<bool> ExpirePricePageAsync(
    HttpClient client, string uiServer, string windowId,
    int pricePageUid, string expirationDate)
{
    var result = await ChangeFieldAsync(
        client, uiServer, windowId,
        "FORM", "form", "price_page_uid", pricePageUid.ToString());
    if (StatusOf(result) != 1)
    {
        Console.WriteLine($"Failed to load page {pricePageUid}: " +
            string.Join("; ", MessagesOf(result)));
        return false;
    }

    result = await ChangeFieldAsync(
        client, uiServer, windowId, "FORM", "form", "expiration_date", expirationDate);
    if (StatusOf(result) != 1)
    {
        Console.WriteLine("Failed to set expiration date: " +
            string.Join("; ", MessagesOf(result)));
        return false;
    }

    result = await SaveWindowAsync(client, uiServer, windowId);
    if (StatusOf(result) != 1)
    {
        Console.WriteLine("Failed to save expiration: " +
            string.Join("; ", MessagesOf(result)));
        return false;
    }

    string? landed = await ReadFieldAsync(
        client, uiServer, windowId, "form", "expiration_date");
    Console.WriteLine(
        $"  {pricePageUid}: expiration_date reads back as {landed ?? "(null)"}");
    return landed is not null && landed.StartsWith(expirationDate);
}

// --- Interactive API helpers -----------------------------------------------

// Start an Interactive session. 2026.1 renamed SessionId -> Id; read both.
static async Task<string> StartSessionAsync(HttpClient client, string uiServer)
{
    var resp = await SendAsync(client, HttpMethod.Post,
        $"{uiServer}/api/ui/interactive/sessions/",
        new Dictionary<string, object> { ["ResponseWindowHandlingEnabled"] = false });
    if (resp.ValueKind == JsonValueKind.Object)
    {
        if (resp.TryGetProperty("Id", out var id)) return id.GetString() ?? "";
        if (resp.TryGetProperty("SessionId", out var sid)) return sid.GetString() ?? "";
    }
    return "";
}

// Always call this - a leaked session 409s the next create.
static async Task EndSessionAsync(HttpClient client, string uiServer)
{
    using var request = new HttpRequestMessage(
        HttpMethod.Delete, $"{uiServer}/api/ui/interactive/sessions/");
    await client.SendAsync(request);
}

static async Task<string> OpenWindowAsync(
    HttpClient client, string uiServer, string serviceName)
{
    var resp = await SendAsync(client, HttpMethod.Post,
        $"{uiServer}/api/ui/interactive/v2/window",
        new Dictionary<string, object> { ["ServiceName"] = serviceName });
    if (resp.ValueKind == JsonValueKind.Object)
    {
        if (resp.TryGetProperty("WindowId", out var id)) return id.GetString() ?? "";
        if (resp.TryGetProperty("windowId", out var lower)) return lower.GetString() ?? "";
    }
    return "";
}

static async Task CloseWindowAsync(HttpClient client, string uiServer, string windowId)
{
    using var request = new HttpRequestMessage(
        HttpMethod.Delete, $"{uiServer}/api/ui/interactive/v2/window?id={windowId}");
    await client.SendAsync(request);
}

// Reset the form for the next record in the batch.
static async Task ClearWindowAsync(HttpClient client, string uiServer, string windowId)
{
    using var request = new HttpRequestMessage(
        HttpMethod.Delete, $"{uiServer}/api/ui/interactive/v2/data?id={windowId}");
    var response = await client.SendAsync(request);
    response.EnsureSuccessStatusCode();
}

// Change one field. One field per call - batched /v2/change is non-atomic.
static async Task<JsonElement> ChangeFieldAsync(
    HttpClient client, string uiServer, string windowId,
    string tab, string datawindow, string field, string value)
{
    var payload = new Dictionary<string, object>
    {
        ["WindowId"] = windowId,
        ["List"] = new[]
        {
            new Dictionary<string, object>
            {
                ["TabName"] = tab,
                ["DatawindowName"] = datawindow,   // required since 25.2
                ["FieldName"] = field,
                ["Value"] = value,
            },
        },
    };
    return await SendAsync(client, HttpMethod.Put,
        $"{uiServer}/api/ui/interactive/v2/change", payload);
}

// Save. The v2 body is the bare window-id GUID as a JSON string.
static async Task<JsonElement> SaveWindowAsync(
    HttpClient client, string uiServer, string windowId)
{
    return await SendAsync(client, HttpMethod.Put,
        $"{uiServer}/api/ui/interactive/v2/data", windowId);
}

// Read one field back off the window's ACTIVE surface.
static async Task<string?> ReadFieldAsync(
    HttpClient client, string uiServer, string windowId,
    string datawindow, string field)
{
    var resp = await SendAsync(client, HttpMethod.Get,
        $"{uiServer}/api/ui/interactive/v2/data?id={windowId}");
    if (resp.ValueKind != JsonValueKind.Array) return null;

    foreach (var dw in resp.EnumerateArray())
    {
        if (!dw.TryGetProperty("Name", out var name) || name.GetString() != datawindow)
            continue;
        if (!dw.TryGetProperty("Columns", out var columns) ||
            !dw.TryGetProperty("Data", out var rows) ||
            rows.GetArrayLength() == 0)
            continue;

        int index = -1, i = 0;
        foreach (var column in columns.EnumerateArray())
        {
            if (column.GetString() == field) { index = i; break; }
            i++;
        }
        if (index < 0) continue;

        int activeRow = dw.TryGetProperty("ActiveRow", out var ar) ? ar.GetInt32() : 0;
        return rows[activeRow][index].ToString();
    }
    return null;
}

// ResultStatus enum: None=0, Success=1, Failure=2, Blocked=3.
static int StatusOf(JsonElement result)
{
    if (result.ValueKind != JsonValueKind.Object ||
        !result.TryGetProperty("Status", out var status))
        return 0;
    return status.ValueKind switch
    {
        JsonValueKind.Number => status.GetInt32(),
        JsonValueKind.String => status.GetString() switch
        {
            "Success" => 1,
            "Failure" => 2,
            "Blocked" => 3,
            _ => 0,
        },
        _ => 0,
    };
}

// Failure detail lives in the top-level Messages array, not in Events.
static List<string> MessagesOf(JsonElement result)
{
    var messages = new List<string>();
    if (result.ValueKind == JsonValueKind.Object &&
        result.TryGetProperty("Messages", out var arr) &&
        arr.ValueKind == JsonValueKind.Array)
    {
        foreach (var message in arr.EnumerateArray())
            messages.Add(message.TryGetProperty("Text", out var text)
                ? text.GetString() ?? "" : "");
    }
    return messages;
}

static async Task<JsonElement> SendAsync(
    HttpClient client, HttpMethod method, string url, object? body = null)
{
    using var request = new HttpRequestMessage(method, url);
    if (body is not null)
        request.Content = new StringContent(
            JsonSerializer.Serialize(body), Encoding.UTF8, "application/json");
    var response = await client.SendAsync(request);
    response.EnsureSuccessStatusCode();
    var text = await response.Content.ReadAsStringAsync();
    if (string.IsNullOrWhiteSpace(text)) return default;
    using var doc = JsonDocument.Parse(text);
    return doc.RootElement.Clone();
}

// --- auth helpers ----------------------------------------------------------

// v2 token endpoint — credentials go in the body, never in headers.
static async Task<string> GetTokenAsync(HttpClient client)
{
    var payload = JsonSerializer.Serialize(new { username = Username, password = Password });
    var response = await client.PostAsync(
        $"{BaseUrl}/api/security/token/v2",
        new StringContent(payload, Encoding.UTF8, "application/json"));
    response.EnsureSuccessStatusCode();
    return ReadField(await response.Content.ReadAsStringAsync(), "AccessToken");
}

// Transaction and Interactive calls go to the UI server, not BaseUrl.
static async Task<string> GetUiServerAsync(HttpClient client, string token)
{
    using var request = new HttpRequestMessage(
        HttpMethod.Get, $"{BaseUrl}/api/ui/router/v1/?urlType=external");
    request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
    var response = await client.SendAsync(request);
    response.EnsureSuccessStatusCode();
    return ReadField(await response.Content.ReadAsStringAsync(), "Url").TrimEnd('/');
}

// Some middleware answers these two endpoints in XML even when asked for JSON.
static string ReadField(string payload, string field)
{
    try
    {
        var value = JsonDocument.Parse(payload).RootElement.GetProperty(field).GetString();
        if (!string.IsNullOrEmpty(value)) return value;
    }
    catch (Exception ex) when (ex is JsonException or KeyNotFoundException) { }

    var match = System.Text.RegularExpressions.Regex.Match(payload, $"<{field}>([^<]+)</{field}>");
    if (!match.Success)
        throw new InvalidOperationException(
            $"No {field} in response: {payload[..Math.Min(200, payload.Length)]}");
    return match.Groups[1].Value;
}
```

<!-- /tabs -->

---

## Production-Grade Async Client

The example scripts in this project use synchronous `httpx`. For production batch processing, a full async client is recommended. Below is a complete, production-tested client architecture.

### Result Class

Parse Interactive API responses into a structured result. This class and the three
that follow are components of one client — they are shown separately here for
readability.

> Full runnable version: [Complete P21Client Class](#complete-p21client-class)

<!-- tabs -->

**Python:**

```python
from dataclasses import dataclass, field


@dataclass
class Result:
    """Parsed result from an Interactive API response."""

    status_code: int  # 0=None, 1=Success, 2=Failure, 3=Blocked
    success: bool
    messages: list[str] = field(default_factory=list)
    events: list[dict] = field(default_factory=list)
    raw: dict = field(default_factory=dict)

    @classmethod
    def from_response(cls, response_data: dict) -> "Result":
        """Parse an API response dict into a Result.

        Status codes match the official ResultStatus enum from
        P21.UI.Service.Model.Interactive.V2.ResultWrapper:
            None=0, Success=1, Failure=2, Blocked=3

        The API may return Status as an integer (1, 2, 3) or a string
        ("Success", "Failure", "Blocked") depending on context.
        """
        status = response_data.get("Status", 0)

        # Official ResultStatus enum: None=0, Success=1, Failure=2, Blocked=3
        status_code = {
            "None": 0,
            "Success": 1,
            "Failure": 2,
            "Blocked": 3,
        }.get(status, 0) if isinstance(status, str) else status

        # Failure details live in the response's top-level Messages array
        # (each message has Text and Type), not in Events.
        messages = [
            m.get("Text", "") for m in response_data.get("Messages", [])
        ]

        return cls(
            status_code=status_code,
            success=status_code == 1,
            messages=messages,
            events=response_data.get("Events", []),
            raw=response_data,
        )

    def get_event(self, event_name: str) -> list[dict] | None:
        """Get the Data of the first event matching the given name.

        Event Data is a key/value list: [{"Key": ..., "Value": ...}].
        """
        for event in self.events:
            if event.get("Name") == event_name:
                return event.get("Data", [])
        return None
```

**C#:**

```csharp
using System.Text.Json;

/// <summary>
/// Parsed result from an Interactive API response.
/// Status codes match P21.UI.Service.Model.Interactive.V2.ResultWrapper:
///   None=0, Success=1, Failure=2, Blocked=3
/// </summary>
public class Result
{
    public int StatusCode { get; init; }  // 0=None, 1=Success, 2=Failure, 3=Blocked
    public bool Success { get; init; }
    public List<string> Messages { get; init; } = new();
    public List<JsonElement> Events { get; init; } = new();
    public JsonElement Raw { get; init; }

    private static readonly Dictionary<string, int> StatusMap = new()
    {
        ["None"] = 0, ["Success"] = 1, ["Failure"] = 2, ["Blocked"] = 3
    };

    /// <summary>
    /// Parse an API response into a Result.
    /// The API may return Status as an integer or string depending on context.
    /// </summary>
    public static Result FromResponse(JsonElement responseData)
    {
        int statusCode = 0;
        bool isObject = responseData.ValueKind == JsonValueKind.Object;

        if (isObject && responseData.TryGetProperty("Status", out var status))
        {
            if (status.ValueKind == JsonValueKind.String)
                StatusMap.TryGetValue(status.GetString() ?? "", out statusCode);
            else if (status.ValueKind == JsonValueKind.Number)
                statusCode = status.GetInt32();
        }

        // Failure details live in the response's top-level Messages array
        // (each message has Text and Type), not in Events.
        var messages = new List<string>();
        if (isObject && responseData.TryGetProperty("Messages", out var messageArray) &&
            messageArray.ValueKind == JsonValueKind.Array)
        {
            foreach (var message in messageArray.EnumerateArray())
                messages.Add(message.TryGetProperty("Text", out var text)
                    ? text.GetString() ?? "" : "");
        }

        var events = new List<JsonElement>();
        if (isObject && responseData.TryGetProperty("Events", out var eventArray) &&
            eventArray.ValueKind == JsonValueKind.Array)
        {
            foreach (var evt in eventArray.EnumerateArray())
                events.Add(evt);
        }

        return new Result
        {
            StatusCode = statusCode,
            Success = statusCode == 1,
            Messages = messages,
            Events = events,
            Raw = responseData
        };
    }

    /// <summary>
    /// Get the Data of the first event matching the given name.
    /// Event Data is a key/value list: [{"Key": ..., "Value": ...}].
    /// </summary>
    public JsonElement? GetEvent(string eventName)
    {
        foreach (var evt in Events)
        {
            if (evt.TryGetProperty("Name", out var name) &&
                name.GetString() == eventName)
                return evt.TryGetProperty("Data", out var data) ? data : null;
        }
        return null;
    }
}
```

<!-- /tabs -->

### Event Parsing Helpers

Common events you need to extract from API responses. Both take a `Result` from the
class above:

> Full runnable version: [Complete P21Client Class](#complete-p21client-class)

<!-- tabs -->

**Python:**

```python
def get_generated_key(result: Result) -> int | None:
    """Extract auto-generated key (e.g., price_page_uid) from result events.

    After saving a new record, P21 fires a 'keygenerated' event
    containing the new UID. Event Data is a key/value list:
    [{"Key": ..., "Value": ...}].
    """
    for kv in result.get_event("keygenerated") or []:
        try:
            return int(kv.get("Value", ""))
        except (ValueError, TypeError):
            continue
    return None


def get_opened_window_id(result: Result) -> str | None:
    """Extract window ID from a 'windowopened' event.

    When a response window/dialog opens, the API returns this event
    with Data [{"Key": "windowid", "Value": "<new-window-id>"}].
    """
    for kv in result.get_event("windowopened") or []:
        if kv.get("Key") == "windowid":
            return kv.get("Value")
    return None
```

**C#:**

```csharp
using System.Text.Json;

public static class EventHelpers
{
    /// <summary>
    /// Extract auto-generated key (e.g., price_page_uid) from result events.
    /// After saving a new record, P21 fires a 'keygenerated' event
    /// containing the new UID. Event Data is a key/value list:
    /// [{"Key": ..., "Value": ...}].
    /// </summary>
    public static int? GetGeneratedKey(Result result)
    {
        var eventData = result.GetEvent("keygenerated");
        if (eventData is not { ValueKind: JsonValueKind.Array })
            return null;

        foreach (var kv in eventData.Value.EnumerateArray())
        {
            if (kv.TryGetProperty("Value", out var value) &&
                int.TryParse(value.GetString(), out int key))
                return key;
        }
        return null;
    }

    /// <summary>
    /// Extract window ID from a 'windowopened' event.
    /// When a response window/dialog opens, the API returns this event
    /// with Data [{"Key": "windowid", "Value": "&lt;new-window-id&gt;"}].
    /// </summary>
    public static string? GetOpenedWindowId(Result result)
    {
        var eventData = result.GetEvent("windowopened");
        if (eventData is not { ValueKind: JsonValueKind.Array })
            return null;

        foreach (var kv in eventData.Value.EnumerateArray())
        {
            if (kv.TryGetProperty("Key", out var key) && key.GetString() == "windowid")
                return kv.TryGetProperty("Value", out var value) ? value.GetString() : null;
        }
        return null;
    }
}
```

<!-- /tabs -->

### Complete Window Class

Every window operation the batch patterns above use, wrapped as methods on a window handle:

> Full runnable version: [Complete P21Client Class](#complete-p21client-class)

<!-- tabs -->

**Python:**

```python
class Window:
    """Represents an open P21 Interactive API window."""

    def __init__(self, client: "P21Client", window_id: str):
        self.client = client
        self.window_id = window_id

    async def change_data(
        self,
        tab_name: str,
        datawindow_name: str,
        field_name: str,
        value: str,
    ) -> Result:
        """Change a single field value.

        Note: datawindow_name is required in P21 25.2+. Window data
        structures changed so the server can no longer auto-resolve
        the target datawindow from TabName alone.
        """
        payload = {
            "WindowId": self.window_id,
            "List": [
                {
                    "TabName": tab_name,
                    "DatawindowName": datawindow_name,
                    "FieldName": field_name,
                    "Value": value,
                }
            ],
        }
        resp = await self.client._put("/api/ui/interactive/v2/change", json=payload)
        return Result.from_response(resp)

    async def change_data_batch(
        self,
        changes: list[dict],
    ) -> Result:
        """Change multiple field values in a single request.

        Args:
            changes: List of dicts with keys: tab_name, datawindow_name,
                     field_name, value
        """
        payload = {
            "WindowId": self.window_id,
            "List": [
                {
                    "TabName": c["tab_name"],
                    "DatawindowName": c["datawindow_name"],
                    "FieldName": c["field_name"],
                    "Value": c["value"],
                }
                for c in changes
            ],
        }
        resp = await self.client._put("/api/ui/interactive/v2/change", json=payload)
        return Result.from_response(resp)

    async def select_tab(self, page_name: str) -> Result:
        """Switch to a different tab."""
        payload = {"WindowId": self.window_id, "PageName": page_name}
        resp = await self.client._put("/api/ui/interactive/v2/tab", json=payload)
        return Result.from_response(resp)

    async def change_row(self, row: int, datawindow_name: str) -> Result:
        """Select a specific row in a datawindow."""
        payload = {
            "WindowId": self.window_id,
            "DatawindowName": datawindow_name,
            "Row": row,
        }
        resp = await self.client._put("/api/ui/interactive/v2/row", json=payload)
        return Result.from_response(resp)

    async def add_row(self, datawindow_name: str) -> Result:
        """Add a new row to a datawindow."""
        payload = {
            "WindowId": self.window_id,
            "DatawindowName": datawindow_name,
        }
        resp = await self.client._post("/api/ui/interactive/v2/row", json=payload)
        return Result.from_response(resp)

    async def save_data(self) -> Result:
        """Save the current window data."""
        # v2 sends just the window ID string as the body
        resp = await self.client._put(
            "/api/ui/interactive/v2/data", content=f'"{self.window_id}"'
        )
        return Result.from_response(resp)

    async def clear_data(self) -> Result:
        """Clear the current window data (reset form for next record)."""
        resp = await self.client._delete(
            f"/api/ui/interactive/v2/data?id={self.window_id}"
        )
        return Result.from_response(resp)

    async def get_data(self) -> dict:
        """Get the current window data."""
        resp = await self.client._get(
            f"/api/ui/interactive/v2/data?id={self.window_id}"
        )
        return resp

    async def get_state(self) -> dict:
        """Get the current window state."""
        resp = await self.client._get(
            f"/api/ui/interactive/v2/window?id={self.window_id}"
        )
        return resp

    async def get_tools(self) -> list[dict]:
        """Get available tools (buttons) for the window.

        Note: GET /v2/tools returns a bare JSON array (not an object),
        and it is the one v2 endpoint that takes ?windowId= instead of ?id=.
        """
        resp = await self.client._get(
            f"/api/ui/interactive/v2/tools?windowId={self.window_id}"
        )
        return resp

    async def run_tool(self, tool_name: str, tool_text: str = "") -> Result:
        """Run a tool (click a button) in the window."""
        payload = {
            "WindowId": self.window_id,
            "ToolName": tool_name,
            "ToolText": tool_text,
        }
        resp = await self.client._post("/api/ui/interactive/v2/tools", json=payload)
        return Result.from_response(resp)

    async def close(self) -> None:
        """Close this window."""
        await self.client._delete(
            f"/api/ui/interactive/v2/window?id={self.window_id}"
        )
```

**C#:**

```csharp
using System.Text.Json;

/// <summary>Represents an open P21 Interactive API window.</summary>
public class Window : IAsyncDisposable
{
    private readonly P21Client _client;
    public string WindowId { get; }

    public Window(P21Client client, string windowId)
    {
        _client = client;
        WindowId = windowId;
    }

    /// <summary>
    /// Change a single field value.
    /// DatawindowName is required in P21 25.2+. Window data structures
    /// changed so the server can no longer auto-resolve the target
    /// datawindow from TabName alone.
    /// </summary>
    public async Task<Result> ChangeDataAsync(
        string tabName, string datawindowName,
        string fieldName, string value)
    {
        var payload = new Dictionary<string, object>
        {
            ["WindowId"] = WindowId,
            ["List"] = new[]
            {
                new Dictionary<string, object>
                {
                    ["TabName"] = tabName,
                    ["DatawindowName"] = datawindowName,
                    ["FieldName"] = fieldName,
                    ["Value"] = value,
                },
            },
        };
        var resp = await _client.PutAsync("/api/ui/interactive/v2/change", payload);
        return Result.FromResponse(resp);
    }

    /// <summary>Change multiple field values in a single request.</summary>
    public async Task<Result> ChangeDataBatchAsync(
        List<ChangeField> changes)
    {
        var list = changes.Select(c => new Dictionary<string, object>
        {
            ["TabName"] = c.TabName,
            ["DatawindowName"] = c.DatawindowName,
            ["FieldName"] = c.FieldName,
            ["Value"] = c.Value,
        }).ToList();

        var payload = new Dictionary<string, object>
        {
            ["WindowId"] = WindowId,
            ["List"] = list,
        };
        var resp = await _client.PutAsync("/api/ui/interactive/v2/change", payload);
        return Result.FromResponse(resp);
    }

    /// <summary>Switch to a different tab.</summary>
    public async Task<Result> SelectTabAsync(string pageName)
    {
        var payload = new Dictionary<string, object>
        {
            ["WindowId"] = WindowId, ["PageName"] = pageName,
        };
        var resp = await _client.PutAsync("/api/ui/interactive/v2/tab", payload);
        return Result.FromResponse(resp);
    }

    /// <summary>Select a specific row in a datawindow.</summary>
    public async Task<Result> ChangeRowAsync(int row, string datawindowName)
    {
        var payload = new Dictionary<string, object>
        {
            ["WindowId"] = WindowId,
            ["DatawindowName"] = datawindowName,
            ["Row"] = row,
        };
        var resp = await _client.PutAsync("/api/ui/interactive/v2/row", payload);
        return Result.FromResponse(resp);
    }

    /// <summary>Add a new row to a datawindow.</summary>
    public async Task<Result> AddRowAsync(string datawindowName)
    {
        var payload = new Dictionary<string, object>
        {
            ["WindowId"] = WindowId,
            ["DatawindowName"] = datawindowName,
        };
        var resp = await _client.PostAsync("/api/ui/interactive/v2/row", payload);
        return Result.FromResponse(resp);
    }

    /// <summary>Save the current window data.</summary>
    public async Task<Result> SaveDataAsync()
    {
        // v2 sends just the window ID string as the body (bare JSON string)
        var resp = await _client.PutRawAsync(
            "/api/ui/interactive/v2/data",
            JsonSerializer.Serialize(WindowId));
        return Result.FromResponse(resp);
    }

    /// <summary>Clear the current window data (reset form for next record).</summary>
    public async Task<Result> ClearDataAsync()
    {
        var resp = await _client.DeleteAsync(
            $"/api/ui/interactive/v2/data?id={WindowId}");
        return Result.FromResponse(resp);
    }

    /// <summary>
    /// Get the current window data. Returns the datawindows on the active
    /// surface — on 2026.1 only a varying subset of them, so a missing
    /// datawindow is not proof it does not exist.
    /// </summary>
    public async Task<JsonElement> GetDataAsync()
    {
        return await _client.GetAsync(
            $"/api/ui/interactive/v2/data?id={WindowId}");
    }

    /// <summary>Get the current window state.</summary>
    public async Task<JsonElement> GetStateAsync()
    {
        return await _client.GetAsync(
            $"/api/ui/interactive/v2/window?id={WindowId}");
    }

    /// <summary>
    /// Get available tools (buttons) for the window.
    /// GET /v2/tools returns a bare JSON array (not an object), and it is
    /// the one v2 endpoint that takes ?windowId= instead of ?id=.
    /// </summary>
    public async Task<JsonElement> GetToolsAsync()
    {
        return await _client.GetAsync(
            $"/api/ui/interactive/v2/tools?windowId={WindowId}");
    }

    /// <summary>Run a tool (click a button) in the window.</summary>
    public async Task<Result> RunToolAsync(string toolName, string toolText = "")
    {
        var payload = new Dictionary<string, object>
        {
            ["WindowId"] = WindowId,
            ["ToolName"] = toolName,
            ["ToolText"] = toolText,
        };
        var resp = await _client.PostAsync("/api/ui/interactive/v2/tools", payload);
        return Result.FromResponse(resp);
    }

    /// <summary>Close this window.</summary>
    public async Task CloseAsync()
    {
        await _client.DeleteAsync(
            $"/api/ui/interactive/v2/window?id={WindowId}");
    }

    public async ValueTask DisposeAsync()
    {
        try { await CloseAsync(); }
        catch (HttpRequestException) { /* Window may already be closed */ }
    }
}

/// <summary>Field change descriptor for batch operations.</summary>
public record ChangeField(
    string TabName, string DatawindowName,
    string FieldName, string Value);
```

<!-- /tabs -->

### Complete P21Client Class

<!-- tabs -->

**Python:**

```python
"""Production async client for the P21 Interactive API, plus a demo run."""
import asyncio
import re
from dataclasses import dataclass, field

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
SERVICE_NAME = "SalesPricePage"           # window the demo run opens
PRICE_PAGE_UID = 100198                   # record the demo run loads
# ---------------------------------------------------------------------------


@dataclass
class Result:
    """Parsed result from an Interactive API response."""

    status_code: int  # 0=None, 1=Success, 2=Failure, 3=Blocked
    success: bool
    messages: list[str] = field(default_factory=list)
    events: list[dict] = field(default_factory=list)
    raw: dict = field(default_factory=dict)

    @classmethod
    def from_response(cls, response_data: dict) -> "Result":
        """Parse an API response dict into a Result.

        Status codes match the official ResultStatus enum from
        P21.UI.Service.Model.Interactive.V2.ResultWrapper:
            None=0, Success=1, Failure=2, Blocked=3
        """
        status = response_data.get("Status", 0)

        status_code = {
            "None": 0,
            "Success": 1,
            "Failure": 2,
            "Blocked": 3,
        }.get(status, 0) if isinstance(status, str) else status

        messages = [m.get("Text", "") for m in response_data.get("Messages", [])]

        return cls(
            status_code=status_code,
            success=status_code == 1,
            messages=messages,
            events=response_data.get("Events", []),
            raw=response_data,
        )

    def get_event(self, event_name: str) -> list[dict] | None:
        """Get the Data of the first event matching the given name."""
        for event in self.events:
            if event.get("Name") == event_name:
                return event.get("Data", [])
        return None


def get_generated_key(result: Result) -> int | None:
    """Extract an auto-generated key (e.g. price_page_uid) from result events."""
    for kv in result.get_event("keygenerated") or []:
        try:
            return int(kv.get("Value", ""))
        except (ValueError, TypeError):
            continue
    return None


def get_opened_window_id(result: Result) -> str | None:
    """Extract the window ID from a 'windowopened' event."""
    for kv in result.get_event("windowopened") or []:
        if kv.get("Key") == "windowid":
            return kv.get("Value")
    return None


class Window:
    """Represents an open P21 Interactive API window."""

    def __init__(self, client: "P21Client", window_id: str):
        self.client = client
        self.window_id = window_id

    async def change_data(
        self,
        tab_name: str,
        datawindow_name: str,
        field_name: str,
        value: str,
    ) -> Result:
        """Change a single field value.

        Note: datawindow_name is required in P21 25.2+.
        """
        payload = {
            "WindowId": self.window_id,
            "List": [
                {
                    "TabName": tab_name,
                    "DatawindowName": datawindow_name,
                    "FieldName": field_name,
                    "Value": value,
                }
            ],
        }
        resp = await self.client._put("/api/ui/interactive/v2/change", json=payload)
        return Result.from_response(resp)

    async def change_data_batch(self, changes: list[dict]) -> Result:
        """Change multiple field values in a single request."""
        payload = {
            "WindowId": self.window_id,
            "List": [
                {
                    "TabName": c["tab_name"],
                    "DatawindowName": c["datawindow_name"],
                    "FieldName": c["field_name"],
                    "Value": c["value"],
                }
                for c in changes
            ],
        }
        resp = await self.client._put("/api/ui/interactive/v2/change", json=payload)
        return Result.from_response(resp)

    async def select_tab(self, page_name: str) -> Result:
        """Switch to a different tab."""
        payload = {"WindowId": self.window_id, "PageName": page_name}
        resp = await self.client._put("/api/ui/interactive/v2/tab", json=payload)
        return Result.from_response(resp)

    async def change_row(self, row: int, datawindow_name: str) -> Result:
        """Select a specific row in a datawindow."""
        payload = {
            "WindowId": self.window_id,
            "DatawindowName": datawindow_name,
            "Row": row,
        }
        resp = await self.client._put("/api/ui/interactive/v2/row", json=payload)
        return Result.from_response(resp)

    async def add_row(self, datawindow_name: str) -> Result:
        """Add a new row to a datawindow."""
        payload = {
            "WindowId": self.window_id,
            "DatawindowName": datawindow_name,
        }
        resp = await self.client._post("/api/ui/interactive/v2/row", json=payload)
        return Result.from_response(resp)

    async def save_data(self) -> Result:
        """Save the current window data."""
        # v2 sends just the window ID string as the body
        resp = await self.client._put(
            "/api/ui/interactive/v2/data", content=f'"{self.window_id}"'
        )
        return Result.from_response(resp)

    async def clear_data(self) -> Result:
        """Clear the current window data (reset form for next record)."""
        resp = await self.client._delete(
            f"/api/ui/interactive/v2/data?id={self.window_id}"
        )
        return Result.from_response(resp)

    async def get_data(self) -> list[dict]:
        """Get the datawindows on the window's ACTIVE surface.

        On 2026.1 this returns only a varying subset of them — a missing
        datawindow is not proof it does not exist.
        """
        return await self.client._get(
            f"/api/ui/interactive/v2/data?id={self.window_id}"
        )

    async def get_state(self) -> dict:
        """Get the current window state."""
        return await self.client._get(
            f"/api/ui/interactive/v2/window?id={self.window_id}"
        )

    async def get_tools(self) -> list[dict]:
        """Get available tools (buttons) for the window.

        Note: GET /v2/tools returns a bare JSON array (not an object),
        and it is the one v2 endpoint that takes ?windowId= instead of ?id=.
        """
        return await self.client._get(
            f"/api/ui/interactive/v2/tools?windowId={self.window_id}"
        )

    async def run_tool(self, tool_name: str, tool_text: str = "") -> Result:
        """Run a tool (click a button) in the window."""
        payload = {
            "WindowId": self.window_id,
            "ToolName": tool_name,
            "ToolText": tool_text,
        }
        resp = await self.client._post("/api/ui/interactive/v2/tools", json=payload)
        return Result.from_response(resp)

    async def close(self) -> None:
        """Close this window."""
        await self.client._delete(
            f"/api/ui/interactive/v2/window?id={self.window_id}"
        )


class P21Client:
    """Production async client for P21 Interactive API.

    Handles authentication, session management, and window operations.
    Tested against 700+ operations in production.

    Usage:
        async with P21Client(base_url, username, password) as client:
            window = await client.open_window(service_name="SalesPricePage")
            result = await window.change_data("FORM", "form", "description", "Test")
            await window.save_data()
            await window.close()
    """

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        verify_ssl: bool = True,
        timeout: float = 60.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.token: str | None = None
        self.ui_server_url: str | None = None
        self.session_id: str | None = None
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                verify=self.verify_ssl,
                timeout=self.timeout,
                follow_redirects=True,
            )
        return self._client

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            # without this the Interactive API returns XML, not JSON
            "Accept": "application/json",
        }

    async def authenticate(self) -> None:
        """Obtain a bearer token from P21."""
        client = self._get_client()
        response = await client.post(
            f"{self.base_url}/api/security/token/v2",
            json={"username": self.username, "password": self.password},
            headers={"Accept": "application/json"},
        )
        response.raise_for_status()
        try:
            self.token = response.json()["AccessToken"]
        except (ValueError, KeyError):  # some middleware answers in XML
            match = re.search(r"<AccessToken>([^<]+)</AccessToken>", response.text)
            if not match:
                raise ValueError(
                    f"No AccessToken in response: {response.text[:200]}"
                ) from None
            self.token = match.group(1)

    async def get_ui_server(self) -> None:
        """Discover the UI server URL."""
        client = self._get_client()
        response = await client.get(
            # trailing slash avoids a 307
            f"{self.base_url}/api/ui/router/v1/?urlType=external",
            headers=self._headers,
        )
        response.raise_for_status()
        try:
            self.ui_server_url = response.json()["Url"].rstrip("/")
        except (ValueError, KeyError):
            match = re.search(r"<Url>([^<]+)</Url>", response.text)
            if not match:
                raise ValueError(
                    f"No Url in router response: {response.text[:200]}"
                ) from None
            self.ui_server_url = match.group(1).rstrip("/")

    async def start_session(self) -> None:
        """Start an Interactive API session.

        2026.1 renamed the identifier SessionId -> Id; read both so one
        client works across versions.
        """
        resp = await self._post(
            "/api/ui/interactive/sessions/",
            json={"ResponseWindowHandlingEnabled": False},
        )
        self.session_id = resp.get("Id") or resp.get("SessionId")

    async def end_session(self) -> None:
        """End the current Interactive API session.

        Never skip this — a leaked session 409s ("Session already exists")
        on the next create.
        """
        try:
            await self._delete("/api/ui/interactive/sessions/")
        except httpx.HTTPError as e:
            print(f"Session cleanup error (ignored): {e}")

    async def open_window(self, service_name: str) -> Window:
        """Open a P21 window by service name."""
        resp = await self._post(
            "/api/ui/interactive/v2/window",
            json={"ServiceName": service_name},
        )
        window_id = resp.get("WindowId", resp.get("windowId", ""))
        return Window(self, window_id)

    # --- HTTP helpers ---

    async def _get(self, path: str, **kwargs) -> dict | list:
        # Most endpoints return a JSON object; GET /v2/data and GET /v2/tools
        # return bare JSON arrays.
        client = self._get_client()
        resp = await client.get(
            f"{self.ui_server_url}{path}", headers=self._headers, **kwargs
        )
        resp.raise_for_status()
        return resp.json()

    async def _post(self, path: str, **kwargs) -> dict:
        client = self._get_client()
        resp = await client.post(
            f"{self.ui_server_url}{path}", headers=self._headers, **kwargs
        )
        resp.raise_for_status()
        return resp.json()

    async def _put(self, path: str, **kwargs) -> dict:
        client = self._get_client()
        resp = await client.put(
            f"{self.ui_server_url}{path}", headers=self._headers, **kwargs
        )
        resp.raise_for_status()
        return resp.json()

    async def _delete(self, path: str, **kwargs) -> dict:
        client = self._get_client()
        resp = await client.delete(
            f"{self.ui_server_url}{path}", headers=self._headers, **kwargs
        )
        resp.raise_for_status()
        return resp.json() if resp.content else {}

    # --- Context manager ---

    async def __aenter__(self) -> "P21Client":
        await self.authenticate()
        await self.get_ui_server()
        await self.start_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        await self.end_session()
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
        return False


async def main() -> None:
    """Open a window, load one record, and print what came back."""
    async with P21Client(BASE_URL, USERNAME, PASSWORD, verify_ssl=VERIFY_SSL) as client:
        print(f"session {client.session_id} on {client.ui_server_url}")

        window = await client.open_window(service_name=SERVICE_NAME)
        try:
            result = await window.change_data(
                "FORM", "form", "price_page_uid", str(PRICE_PAGE_UID)
            )
            print(f"load status={result.status_code} success={result.success}")
            for text in result.messages:
                print(f"  message: {text}")

            # Read back off the window's active surface
            for dw in await window.get_data():
                if dw.get("Name") != "form" or not dw.get("Data"):
                    continue
                columns = dw["Columns"]
                row = dw["Data"][dw.get("ActiveRow", 0)]
                for column in ("price_page_uid", "description", "expiration_date"):
                    if column in columns:
                        print(f"  {column} = {row[columns.index(column)]!r}")
        finally:
            await window.close()


asyncio.run(main())
```

**C#:**

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const bool VerifySsl = false;                          // true once you trust the cert chain
const string ServiceName = "SalesPricePage";           // window the demo run opens
const int PricePageUid = 100198;                       // record the demo run loads
// ---------------------------------------------------------------------------

await using var client = new P21Client(BaseUrl, Username, Password, verifySsl: VerifySsl);
await client.InitializeAsync();
Console.WriteLine($"session {client.SessionId} on {client.UiServerUrl}");

var window = await client.OpenWindowAsync(ServiceName);
try
{
    var result = await window.ChangeDataAsync(
        "FORM", "form", "price_page_uid", PricePageUid.ToString());
    Console.WriteLine($"load status={result.StatusCode} success={result.Success}");
    foreach (var text in result.Messages)
        Console.WriteLine($"  message: {text}");

    // Read back off the window's active surface
    var data = await window.GetDataAsync();
    if (data.ValueKind == JsonValueKind.Array)
    {
        foreach (var dw in data.EnumerateArray())
        {
            if (!dw.TryGetProperty("Name", out var name) || name.GetString() != "form")
                continue;
            if (!dw.TryGetProperty("Columns", out var columns) ||
                !dw.TryGetProperty("Data", out var rows) || rows.GetArrayLength() == 0)
                continue;

            int activeRow = dw.TryGetProperty("ActiveRow", out var ar) ? ar.GetInt32() : 0;
            var columnNames = columns.EnumerateArray()
                .Select(c => c.GetString() ?? "").ToList();

            foreach (var column in new[]
                     { "price_page_uid", "description", "expiration_date" })
            {
                int index = columnNames.IndexOf(column);
                if (index >= 0)
                    Console.WriteLine($"  {column} = {rows[activeRow][index]}");
            }
        }
    }
}
finally
{
    await window.CloseAsync();
}

/// <summary>
/// Parsed result from an Interactive API response.
/// Status codes match P21.UI.Service.Model.Interactive.V2.ResultWrapper:
///   None=0, Success=1, Failure=2, Blocked=3
/// </summary>
public class Result
{
    public int StatusCode { get; init; }  // 0=None, 1=Success, 2=Failure, 3=Blocked
    public bool Success { get; init; }
    public List<string> Messages { get; init; } = new();
    public List<JsonElement> Events { get; init; } = new();
    public JsonElement Raw { get; init; }

    private static readonly Dictionary<string, int> StatusMap = new()
    {
        ["None"] = 0, ["Success"] = 1, ["Failure"] = 2, ["Blocked"] = 3
    };

    public static Result FromResponse(JsonElement responseData)
    {
        int statusCode = 0;
        bool isObject = responseData.ValueKind == JsonValueKind.Object;

        if (isObject && responseData.TryGetProperty("Status", out var status))
        {
            if (status.ValueKind == JsonValueKind.String)
                StatusMap.TryGetValue(status.GetString() ?? "", out statusCode);
            else if (status.ValueKind == JsonValueKind.Number)
                statusCode = status.GetInt32();
        }

        // Failure details live in the response's top-level Messages array
        // (each message has Text and Type), not in Events.
        var messages = new List<string>();
        if (isObject && responseData.TryGetProperty("Messages", out var messageArray) &&
            messageArray.ValueKind == JsonValueKind.Array)
        {
            foreach (var message in messageArray.EnumerateArray())
                messages.Add(message.TryGetProperty("Text", out var text)
                    ? text.GetString() ?? "" : "");
        }

        var events = new List<JsonElement>();
        if (isObject && responseData.TryGetProperty("Events", out var eventArray) &&
            eventArray.ValueKind == JsonValueKind.Array)
        {
            foreach (var evt in eventArray.EnumerateArray())
                events.Add(evt);
        }

        return new Result
        {
            StatusCode = statusCode,
            Success = statusCode == 1,
            Messages = messages,
            Events = events,
            Raw = responseData
        };
    }

    /// <summary>
    /// Get the Data of the first event matching the given name.
    /// Event Data is a key/value list: [{"Key": ..., "Value": ...}].
    /// </summary>
    public JsonElement? GetEvent(string eventName)
    {
        foreach (var evt in Events)
        {
            if (evt.TryGetProperty("Name", out var name) &&
                name.GetString() == eventName)
                return evt.TryGetProperty("Data", out var data) ? data : null;
        }
        return null;
    }
}

public static class EventHelpers
{
    /// <summary>Extract an auto-generated key from a 'keygenerated' event.</summary>
    public static int? GetGeneratedKey(Result result)
    {
        var eventData = result.GetEvent("keygenerated");
        if (eventData is not { ValueKind: JsonValueKind.Array })
            return null;

        foreach (var kv in eventData.Value.EnumerateArray())
        {
            if (kv.TryGetProperty("Value", out var value) &&
                int.TryParse(value.GetString(), out int key))
                return key;
        }
        return null;
    }

    /// <summary>Extract the window ID from a 'windowopened' event.</summary>
    public static string? GetOpenedWindowId(Result result)
    {
        var eventData = result.GetEvent("windowopened");
        if (eventData is not { ValueKind: JsonValueKind.Array })
            return null;

        foreach (var kv in eventData.Value.EnumerateArray())
        {
            if (kv.TryGetProperty("Key", out var key) && key.GetString() == "windowid")
                return kv.TryGetProperty("Value", out var value) ? value.GetString() : null;
        }
        return null;
    }
}

/// <summary>Represents an open P21 Interactive API window.</summary>
public class Window : IAsyncDisposable
{
    private readonly P21Client _client;
    public string WindowId { get; }

    public Window(P21Client client, string windowId)
    {
        _client = client;
        WindowId = windowId;
    }

    /// <summary>
    /// Change a single field value.
    /// DatawindowName is required in P21 25.2+.
    /// </summary>
    public async Task<Result> ChangeDataAsync(
        string tabName, string datawindowName,
        string fieldName, string value)
    {
        var payload = new Dictionary<string, object>
        {
            ["WindowId"] = WindowId,
            ["List"] = new[]
            {
                new Dictionary<string, object>
                {
                    ["TabName"] = tabName,
                    ["DatawindowName"] = datawindowName,
                    ["FieldName"] = fieldName,
                    ["Value"] = value,
                },
            },
        };
        var resp = await _client.PutAsync("/api/ui/interactive/v2/change", payload);
        return Result.FromResponse(resp);
    }

    /// <summary>Change multiple field values in a single request.</summary>
    public async Task<Result> ChangeDataBatchAsync(List<ChangeField> changes)
    {
        var list = changes.Select(c => new Dictionary<string, object>
        {
            ["TabName"] = c.TabName,
            ["DatawindowName"] = c.DatawindowName,
            ["FieldName"] = c.FieldName,
            ["Value"] = c.Value,
        }).ToList();

        var payload = new Dictionary<string, object>
        {
            ["WindowId"] = WindowId,
            ["List"] = list,
        };
        var resp = await _client.PutAsync("/api/ui/interactive/v2/change", payload);
        return Result.FromResponse(resp);
    }

    /// <summary>Switch to a different tab.</summary>
    public async Task<Result> SelectTabAsync(string pageName)
    {
        var payload = new Dictionary<string, object>
        {
            ["WindowId"] = WindowId, ["PageName"] = pageName,
        };
        var resp = await _client.PutAsync("/api/ui/interactive/v2/tab", payload);
        return Result.FromResponse(resp);
    }

    /// <summary>Select a specific row in a datawindow.</summary>
    public async Task<Result> ChangeRowAsync(int row, string datawindowName)
    {
        var payload = new Dictionary<string, object>
        {
            ["WindowId"] = WindowId,
            ["DatawindowName"] = datawindowName,
            ["Row"] = row,
        };
        var resp = await _client.PutAsync("/api/ui/interactive/v2/row", payload);
        return Result.FromResponse(resp);
    }

    /// <summary>Add a new row to a datawindow.</summary>
    public async Task<Result> AddRowAsync(string datawindowName)
    {
        var payload = new Dictionary<string, object>
        {
            ["WindowId"] = WindowId,
            ["DatawindowName"] = datawindowName,
        };
        var resp = await _client.PostAsync("/api/ui/interactive/v2/row", payload);
        return Result.FromResponse(resp);
    }

    /// <summary>Save the current window data.</summary>
    public async Task<Result> SaveDataAsync()
    {
        // v2 sends just the window ID string as the body (bare JSON string)
        var resp = await _client.PutRawAsync(
            "/api/ui/interactive/v2/data",
            JsonSerializer.Serialize(WindowId));
        return Result.FromResponse(resp);
    }

    /// <summary>Clear the current window data (reset form for next record).</summary>
    public async Task<Result> ClearDataAsync()
    {
        var resp = await _client.DeleteAsync(
            $"/api/ui/interactive/v2/data?id={WindowId}");
        return Result.FromResponse(resp);
    }

    /// <summary>
    /// Get the datawindows on the window's ACTIVE surface. On 2026.1 this
    /// returns only a varying subset of them.
    /// </summary>
    public async Task<JsonElement> GetDataAsync()
    {
        return await _client.GetAsync(
            $"/api/ui/interactive/v2/data?id={WindowId}");
    }

    /// <summary>Get the current window state.</summary>
    public async Task<JsonElement> GetStateAsync()
    {
        return await _client.GetAsync(
            $"/api/ui/interactive/v2/window?id={WindowId}");
    }

    /// <summary>
    /// Get available tools (buttons) for the window.
    /// GET /v2/tools returns a bare JSON array (not an object), and it is
    /// the one v2 endpoint that takes ?windowId= instead of ?id=.
    /// </summary>
    public async Task<JsonElement> GetToolsAsync()
    {
        return await _client.GetAsync(
            $"/api/ui/interactive/v2/tools?windowId={WindowId}");
    }

    /// <summary>Run a tool (click a button) in the window.</summary>
    public async Task<Result> RunToolAsync(string toolName, string toolText = "")
    {
        var payload = new Dictionary<string, object>
        {
            ["WindowId"] = WindowId,
            ["ToolName"] = toolName,
            ["ToolText"] = toolText,
        };
        var resp = await _client.PostAsync("/api/ui/interactive/v2/tools", payload);
        return Result.FromResponse(resp);
    }

    /// <summary>Close this window.</summary>
    public async Task CloseAsync()
    {
        await _client.DeleteAsync(
            $"/api/ui/interactive/v2/window?id={WindowId}");
    }

    public async ValueTask DisposeAsync()
    {
        try { await CloseAsync(); }
        catch (HttpRequestException) { /* Window may already be closed */ }
    }
}

/// <summary>Field change descriptor for batch operations.</summary>
public record ChangeField(
    string TabName, string DatawindowName,
    string FieldName, string Value);

/// <summary>
/// Production async client for P21 Interactive API.
/// Handles authentication, session management, and window operations.
/// Tested against 700+ operations in production.
///
/// Usage:
///   await using var client = new P21Client(baseUrl, username, password);
///   await client.InitializeAsync();
///   var window = await client.OpenWindowAsync("SalesPricePage");
///   var result = await window.ChangeDataAsync("FORM", "form", "description", "Test");
///   await window.SaveDataAsync();
///   await window.CloseAsync();
/// </summary>
public class P21Client : IAsyncDisposable
{
    private readonly string _baseUrl;
    private readonly string _username;
    private readonly string _password;
    private readonly HttpClient _httpClient;

    private string? _token;

    public string? UiServerUrl { get; private set; }
    public string? SessionId { get; private set; }

    public P21Client(
        string baseUrl,
        string username,
        string password,
        bool verifySsl = true,
        TimeSpan? timeout = null)
    {
        _baseUrl = baseUrl.TrimEnd('/');
        _username = username;
        _password = password;

        var handler = new HttpClientHandler();
        if (!verifySsl)
            handler.ServerCertificateCustomValidationCallback =
                HttpClientHandler.DangerousAcceptAnyServerCertificateValidator;

        _httpClient = new HttpClient(handler)
        {
            Timeout = timeout ?? TimeSpan.FromSeconds(60)
        };
    }

    private void SetAuthHeaders()
    {
        _httpClient.DefaultRequestHeaders.Authorization =
            new AuthenticationHeaderValue("Bearer", _token);
        _httpClient.DefaultRequestHeaders.Accept.Clear();
        // without this the Interactive API returns XML, not JSON
        _httpClient.DefaultRequestHeaders.Accept
            .Add(new MediaTypeWithQualityHeaderValue("application/json"));
    }

    /// <summary>Obtain a bearer token from P21.</summary>
    public async Task AuthenticateAsync()
    {
        var body = JsonSerializer.Serialize(
            new { username = _username, password = _password });
        var content = new StringContent(body, Encoding.UTF8, "application/json");
        var response = await _httpClient.PostAsync(
            $"{_baseUrl}/api/security/token/v2", content);
        response.EnsureSuccessStatusCode();

        _token = ReadField(await response.Content.ReadAsStringAsync(), "AccessToken");
        SetAuthHeaders();
    }

    /// <summary>Discover the UI server URL.</summary>
    public async Task DiscoverUiServerAsync()
    {
        // trailing slash avoids a 307
        var response = await _httpClient.GetAsync(
            $"{_baseUrl}/api/ui/router/v1/?urlType=external");
        response.EnsureSuccessStatusCode();
        UiServerUrl = ReadField(
            await response.Content.ReadAsStringAsync(), "Url").TrimEnd('/');
    }

    /// <summary>
    /// Start an Interactive API session. 2026.1 renamed the identifier
    /// SessionId -> Id; read both so one client works across versions.
    /// </summary>
    public async Task StartSessionAsync()
    {
        var resp = await PostAsync("/api/ui/interactive/sessions/",
            new Dictionary<string, object> { ["ResponseWindowHandlingEnabled"] = false });
        if (resp.ValueKind == JsonValueKind.Object)
        {
            if (resp.TryGetProperty("Id", out var id))
                SessionId = id.GetString();
            else if (resp.TryGetProperty("SessionId", out var sid))
                SessionId = sid.GetString();
        }
    }

    /// <summary>
    /// End the current Interactive API session. Never skip this - a leaked
    /// session 409s ("Session already exists") on the next create.
    /// </summary>
    public async Task EndSessionAsync()
    {
        try { await DeleteAsync("/api/ui/interactive/sessions/"); }
        catch (HttpRequestException ex)
        {
            Console.WriteLine($"Session cleanup error (ignored): {ex.Message}");
        }
    }

    /// <summary>
    /// Initialize the client: authenticate, discover UI server, start session.
    /// </summary>
    public async Task InitializeAsync()
    {
        await AuthenticateAsync();
        await DiscoverUiServerAsync();
        await StartSessionAsync();
    }

    /// <summary>
    /// Create a scoped session that auto-disposes (start + end).
    /// Use with "await using" for session-per-batch pattern.
    /// </summary>
    public async Task<P21Session> CreateSessionAsync()
    {
        var session = new P21Session(this);
        await session.StartAsync();
        return session;
    }

    /// <summary>Open a P21 window by service name.</summary>
    public async Task<Window> OpenWindowAsync(string serviceName)
    {
        var resp = await PostAsync("/api/ui/interactive/v2/window",
            new Dictionary<string, object> { ["ServiceName"] = serviceName });

        string windowId = "";
        if (resp.ValueKind == JsonValueKind.Object)
        {
            if (resp.TryGetProperty("WindowId", out var id))
                windowId = id.GetString() ?? "";
            else if (resp.TryGetProperty("windowId", out var lower))
                windowId = lower.GetString() ?? "";
        }
        return new Window(this, windowId);
    }

    // --- HTTP helpers ---

    public async Task<JsonElement> GetAsync(string path)
        => await SendAsync(HttpMethod.Get, path, null);

    public async Task<JsonElement> PostAsync(string path, object payload)
        => await SendAsync(HttpMethod.Post, path, JsonSerializer.Serialize(payload));

    public async Task<JsonElement> PutAsync(string path, object payload)
        => await SendAsync(HttpMethod.Put, path, JsonSerializer.Serialize(payload));

    /// <summary>PUT with a raw string body (used for SaveDataAsync).</summary>
    public async Task<JsonElement> PutRawAsync(string path, string rawBody)
        => await SendAsync(HttpMethod.Put, path, rawBody);

    public async Task<JsonElement> DeleteAsync(string path)
        => await SendAsync(HttpMethod.Delete, path, null);

    private async Task<JsonElement> SendAsync(HttpMethod method, string path, string? body)
    {
        using var request = new HttpRequestMessage(method, $"{UiServerUrl}{path}");
        if (body is not null)
            request.Content = new StringContent(body, Encoding.UTF8, "application/json");
        var response = await _httpClient.SendAsync(request);
        response.EnsureSuccessStatusCode();

        var text = await response.Content.ReadAsStringAsync();
        if (string.IsNullOrWhiteSpace(text)) return default;
        using var doc = JsonDocument.Parse(text);
        return doc.RootElement.Clone();
    }

    // Some middleware answers the token and router endpoints in XML.
    private static string ReadField(string payload, string field)
    {
        try
        {
            var value = JsonDocument.Parse(payload)
                .RootElement.GetProperty(field).GetString();
            if (!string.IsNullOrEmpty(value)) return value;
        }
        catch (Exception ex) when (ex is JsonException or KeyNotFoundException) { }

        var match = System.Text.RegularExpressions.Regex.Match(
            payload, $"<{field}>([^<]+)</{field}>");
        if (!match.Success)
            throw new InvalidOperationException(
                $"No {field} in response: {payload[..Math.Min(200, payload.Length)]}");
        return match.Groups[1].Value;
    }

    public async ValueTask DisposeAsync()
    {
        await EndSessionAsync();
        _httpClient.Dispose();
    }
}

/// <summary>
/// Scoped session for session-per-batch pattern. Use with "await using".
/// </summary>
public class P21Session : IAsyncDisposable
{
    private readonly P21Client _client;

    public P21Session(P21Client client) => _client = client;

    public async Task StartAsync() => await _client.StartSessionAsync();

    public async Task<Window> OpenWindowAsync(string serviceName)
        => await _client.OpenWindowAsync(serviceName);

    public async ValueTask DisposeAsync() => await _client.EndSessionAsync();
}
```

<!-- /tabs -->

---

## Complete Batch Workflow Example

Putting it all together: expire old pages, create new ones, and link to books.

<!-- tabs -->

**Python:**

```python
"""Replace supplier price pages: expire old, create new, link new pages to books."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain

SUPPLIER_ID = "100198"                    # supplier the pages belong to
COMPANY_ID = "ACME"
OLD_PAGE_UIDS = [100199, 100200]          # existing pages to expire
OLD_EXPIRATION_DATE = "2026-12-31"        # date stamped on the OLD pages
NEW_PAGES = [                             # pages to create
    {"product_group_id": "HVAC", "description": "ACME-HVAC-WHOLESALE",
     "calculation_value1": "0.85"},
]
BOOK_IDS = ["ACME_BOOK_A"]                # price books to link the new pages to
BATCH_SIZE = 25                           # operations per session batch

# Dropdown display values and dates for the new pages — see doc 08
PAGE_TYPE = "Supplier / Product Group"
PRICING_METHOD = "Source"
SOURCE_PRICE = "Supplier List Price"
CALCULATION_METHOD = "Multiplier"
NEW_EFFECTIVE_DATE = "2027-01-01"
NEW_EXPIRATION_DATE = "2030-12-31"
# ---------------------------------------------------------------------------


def get_token(client: httpx.Client) -> str:
    """v2 token endpoint — credentials go in the body, never in headers."""
    r = client.post(
        f"{BASE_URL}/api/security/token/v2",
        json={"username": USERNAME, "password": PASSWORD},
        headers={"Accept": "application/json"},
    )
    r.raise_for_status()
    try:
        return r.json()["AccessToken"]
    except (ValueError, KeyError):  # some middleware answers in XML
        match = re.search(r"<AccessToken>([^<]+)</AccessToken>", r.text)
        if not match:
            raise ValueError(f"No AccessToken in response: {r.text[:200]}") from None
        return match.group(1)


def get_ui_server(client: httpx.Client, token: str) -> str:
    """Transaction and Interactive calls go to the UI server, not BASE_URL."""
    r = client.get(
        f"{BASE_URL}/api/ui/router/v1/?urlType=external",  # trailing slash avoids a 307
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )
    r.raise_for_status()
    try:
        return r.json()["Url"].rstrip("/")
    except (ValueError, KeyError):
        match = re.search(r"<Url>([^<]+)</Url>", r.text)
        if not match:
            raise ValueError(f"No Url in router response: {r.text[:200]}") from None
        return match.group(1).rstrip("/")


def status_of(result: dict) -> int:
    """ResultStatus enum: None=0, Success=1, Failure=2, Blocked=3."""
    status = result.get("Status", 0)
    if isinstance(status, str):
        return {"None": 0, "Success": 1, "Failure": 2, "Blocked": 3}.get(status, 0)
    return status


def messages_of(result: dict) -> list[str]:
    """Failure detail lives in the top-level Messages array, not in Events."""
    return [m.get("Text", "") for m in result.get("Messages", [])]


def generated_key(result: dict) -> int | None:
    """After an insert, P21 fires a 'keygenerated' event carrying the new UID.

    Event Data is a key/value list: [{"Key": ..., "Value": ...}].
    """
    for event in result.get("Events", []):
        if event.get("Name") != "keygenerated":
            continue
        for kv in event.get("Data", []):
            try:
                return int(kv.get("Value", ""))
            except (ValueError, TypeError):
                continue
    return None


def start_session(client: httpx.Client, headers: dict, ui_server: str) -> str:
    """Start an Interactive session. 2026.1 renamed SessionId -> Id; read both."""
    r = client.post(
        f"{ui_server}/api/ui/interactive/sessions/",
        json={"ResponseWindowHandlingEnabled": False},
        headers=headers,
    )
    r.raise_for_status()
    data = r.json()
    return data.get("Id") or data.get("SessionId", "")


def end_session(client: httpx.Client, headers: dict, ui_server: str) -> None:
    """Always call this — a leaked session 409s the next create."""
    client.delete(f"{ui_server}/api/ui/interactive/sessions/", headers=headers)


def open_window(client: httpx.Client, headers: dict, ui_server: str, service: str) -> str:
    r = client.post(
        f"{ui_server}/api/ui/interactive/v2/window",
        json={"ServiceName": service},
        headers=headers,
    )
    r.raise_for_status()
    data = r.json()
    return data.get("WindowId") or data.get("windowId", "")


def close_window(client: httpx.Client, headers: dict, ui_server: str, window_id: str) -> None:
    client.delete(
        f"{ui_server}/api/ui/interactive/v2/window",
        params={"id": window_id},
        headers=headers,
    )


def clear_window(client: httpx.Client, headers: dict, ui_server: str, window_id: str) -> None:
    r = client.delete(
        f"{ui_server}/api/ui/interactive/v2/data",
        params={"id": window_id},
        headers=headers,
    )
    r.raise_for_status()


def change_field(
    client: httpx.Client,
    headers: dict,
    ui_server: str,
    window_id: str,
    tab: str,
    datawindow: str,
    field: str,
    value: str,
) -> dict:
    """Change one field. One field per call — batched /v2/change is non-atomic."""
    payload = {
        "WindowId": window_id,
        "List": [
            {
                "TabName": tab,
                "DatawindowName": datawindow,  # required since 25.2
                "FieldName": field,
                "Value": value,
            }
        ],
    }
    r = client.put(
        f"{ui_server}/api/ui/interactive/v2/change", json=payload, headers=headers
    )
    r.raise_for_status()
    return r.json()


def select_tab(
    client: httpx.Client, headers: dict, ui_server: str, window_id: str, page_name: str
) -> dict:
    """Switch tabs. 2026.1 binds PageName only — TabName returns 400."""
    r = client.put(
        f"{ui_server}/api/ui/interactive/v2/tab",
        json={"WindowId": window_id, "PageName": page_name},
        headers=headers,
    )
    r.raise_for_status()
    return r.json()


def add_row(
    client: httpx.Client, headers: dict, ui_server: str, window_id: str, datawindow: str
) -> dict:
    """Add a new row to a datawindow."""
    r = client.post(
        f"{ui_server}/api/ui/interactive/v2/row",
        json={"WindowId": window_id, "DatawindowName": datawindow},
        headers=headers,
    )
    r.raise_for_status()
    return r.json()


def save_window(client: httpx.Client, headers: dict, ui_server: str, window_id: str) -> dict:
    """Save. The v2 body is the bare window-id GUID as a JSON string."""
    r = client.put(
        f"{ui_server}/api/ui/interactive/v2/data", json=window_id, headers=headers
    )
    r.raise_for_status()
    return r.json()


def read_field_anywhere(
    client: httpx.Client, headers: dict, ui_server: str, window_id: str, field: str
) -> str | None:
    """Find a field in whichever datawindow GET /v2/data returns it in.

    GET /v2/data returns the active surface only, and on 2026.1 only a
    varying subset of it — a missing field proves nothing.
    """
    r = client.get(
        f"{ui_server}/api/ui/interactive/v2/data",
        params={"id": window_id},
        headers=headers,
    )
    r.raise_for_status()
    for dw in r.json():
        columns = dw.get("Columns", [])
        rows = dw.get("Data", [])
        if field in columns and rows:
            return rows[dw.get("ActiveRow", 0)][columns.index(field)]
    return None


def expire_price_page(
    client: httpx.Client,
    headers: dict,
    ui_server: str,
    window_id: str,
    price_page_uid: int,
    expiration_date: str,
) -> bool:
    """Expire one page, then confirm the new date reads back."""
    for field_name, value in (
        ("price_page_uid", str(price_page_uid)),
        ("expiration_date", expiration_date),
    ):
        result = change_field(
            client, headers, ui_server, window_id, "FORM", "form", field_name, value
        )
        if status_of(result) != 1:
            print(f"  expire {price_page_uid}: {field_name} -> {messages_of(result)}")
            return False

    result = save_window(client, headers, ui_server, window_id)
    if status_of(result) != 1:
        print(f"  expire {price_page_uid}: save -> {messages_of(result)}")
        return False

    landed = read_field_anywhere(
        client, headers, ui_server, window_id, "expiration_date"
    )
    print(f"  expired {price_page_uid}: expiration_date reads back as {landed!r}")
    return True


def create_single_page(
    client: httpx.Client,
    headers: dict,
    ui_server: str,
    window_id: str,
    page_def: dict,
) -> int | None:
    """Create one price page and return its generated price_page_uid.

    Field order matters — page type first, company before product group.
    See the SalesPricePage field-order rules in doc 08.
    """
    header_fields = [
        ("price_page_type_cd", PAGE_TYPE),
        ("company_id", COMPANY_ID),
        ("product_group_id", page_def["product_group_id"]),
        ("supplier_id", SUPPLIER_ID),
        ("description", page_def["description"]),
        ("pricing_method_cd", PRICING_METHOD),
        ("source_price_cd", SOURCE_PRICE),
        ("effective_date", NEW_EFFECTIVE_DATE),
        ("expiration_date", NEW_EXPIRATION_DATE),
    ]
    for field_name, value in header_fields:
        result = change_field(
            client, headers, ui_server, window_id, "FORM", "form", field_name, value
        )
        if status_of(result) != 1:
            raise RuntimeError(f"{field_name}: {'; '.join(messages_of(result))}")

    # Switch to the VALUES tab before setting the calculation
    select_tab(client, headers, ui_server, window_id, "VALUES")

    for field_name, value in (
        ("calculation_method_cd", CALCULATION_METHOD),
        ("calculation_value1", page_def["calculation_value1"]),
    ):
        result = change_field(
            client, headers, ui_server, window_id,
            "VALUES", "values", field_name, value,
        )
        if status_of(result) != 1:
            raise RuntimeError(f"{field_name}: {'; '.join(messages_of(result))}")

    result = save_window(client, headers, ui_server, window_id)
    if status_of(result) != 1:
        raise RuntimeError(f"save: {'; '.join(messages_of(result))}")

    new_uid = generated_key(result)
    landed = read_field_anywhere(client, headers, ui_server, window_id, "description")
    print(f"  created price_page_uid={new_uid}, description reads back as {landed!r}")
    return new_uid


def link_page_to_book(
    client: httpx.Client,
    headers: dict,
    ui_server: str,
    price_page_uid: int,
    price_book_id: str,
) -> bool:
    """Link a price page to a price book via the SalesPriceBook window."""
    window_id = open_window(client, headers, ui_server, "SalesPriceBook")
    try:
        # Retrieve the book by ID — this loads it into the window
        result = change_field(
            client, headers, ui_server, window_id,
            "FORM", "form", "price_book_id", price_book_id,
        )
        if status_of(result) != 1:
            raise RuntimeError(f"retrieve book: {'; '.join(messages_of(result))}")

        # Switch to the LIST tab before adding rows
        select_tab(client, headers, ui_server, window_id, "LIST")

        result = add_row(client, headers, ui_server, window_id, "list_detail")
        if status_of(result) != 1:
            raise RuntimeError(f"add row: {'; '.join(messages_of(result))}")

        result = change_field(
            client, headers, ui_server, window_id,
            "LIST", "list_detail", "price_page_uid", str(price_page_uid),
        )
        if status_of(result) != 1:
            raise RuntimeError(f"set price_page_uid: {'; '.join(messages_of(result))}")

        result = save_window(client, headers, ui_server, window_id)
        if status_of(result) != 1:
            raise RuntimeError(f"save link: {'; '.join(messages_of(result))}")

        landed = read_field_anywhere(
            client, headers, ui_server, window_id, "price_page_uid"
        )
        print(f"  linked {price_page_uid} -> {price_book_id} "
              f"(list row reads back as {landed!r})")
        return True
    finally:
        close_window(client, headers, ui_server, window_id)


def replace_supplier_pages(
    client: httpx.Client,
    headers: dict,
    ui_server: str,
    old_page_uids: list[int],
    new_pages: list[dict],
    book_ids: list[str],
    expiration_date: str,
    batch_size: int = 25,
) -> dict:
    """Replace supplier price pages: expire old, create new, link to books.

    Args:
        client: Open httpx.Client
        headers: Authorized request headers
        ui_server: UI server base URL from the router
        old_page_uids: UIDs of pages to expire
        new_pages: List of page definitions to create
        book_ids: Price book IDs to link new pages to
        expiration_date: Date to set on old pages
        batch_size: Operations per session batch

    Returns:
        Summary dict with counts
    """
    summary = {"expired": 0, "created": 0, "linked": 0, "errors": []}

    # Phase 1: Expire old pages
    if old_page_uids:
        print(f"Expiring {len(old_page_uids)} old pages...")
        for i in range(0, len(old_page_uids), batch_size):
            batch = old_page_uids[i:i + batch_size]

            start_session(client, headers, ui_server)
            window_id = open_window(client, headers, ui_server, "SalesPricePage")
            try:
                for uid in batch:
                    if expire_price_page(
                        client, headers, ui_server, window_id, uid, expiration_date
                    ):
                        summary["expired"] += 1
                        clear_window(client, headers, ui_server, window_id)
                    else:
                        summary["errors"].append(f"Expire {uid}")
                        close_window(client, headers, ui_server, window_id)
                        window_id = open_window(
                            client, headers, ui_server, "SalesPricePage"
                        )
            finally:
                close_window(client, headers, ui_server, window_id)
                end_session(client, headers, ui_server)

    # Phase 2: Create new pages
    created_uids: list[int] = []
    print(f"Creating {len(new_pages)} new pages...")
    for i in range(0, len(new_pages), batch_size):
        batch = new_pages[i:i + batch_size]

        start_session(client, headers, ui_server)
        window_id = open_window(client, headers, ui_server, "SalesPricePage")
        try:
            for page_def in batch:
                try:
                    uid = create_single_page(
                        client, headers, ui_server, window_id, page_def
                    )
                    if uid is not None:
                        created_uids.append(uid)
                    summary["created"] += 1
                    clear_window(client, headers, ui_server, window_id)
                except (httpx.HTTPError, RuntimeError) as e:
                    summary["errors"].append(str(e))
                    close_window(client, headers, ui_server, window_id)
                    window_id = open_window(
                        client, headers, ui_server, "SalesPricePage"
                    )
        finally:
            close_window(client, headers, ui_server, window_id)
            end_session(client, headers, ui_server)

    # Phase 3: Link new pages to books
    print(f"Linking {len(created_uids)} pages to {len(book_ids)} books...")
    for i in range(0, len(created_uids), batch_size):
        batch = created_uids[i:i + batch_size]

        start_session(client, headers, ui_server)
        try:
            for uid in batch:
                for book_id in book_ids:
                    try:
                        link_page_to_book(client, headers, ui_server, uid, book_id)
                        summary["linked"] += 1
                    except (httpx.HTTPError, RuntimeError) as e:
                        summary["errors"].append(f"Link {uid}->{book_id}: {e}")
        finally:
            end_session(client, headers, ui_server)

    print(
        f"Complete: {summary['expired']} expired, "
        f"{summary['created']} created, "
        f"{summary['linked']} linked, "
        f"{len(summary['errors'])} errors"
    )
    return summary


with httpx.Client(verify=VERIFY_SSL, timeout=120, follow_redirects=True) as client:
    token = get_token(client)
    ui_server = get_ui_server(client, token)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",       # without this you get XML, not JSON
        "Content-Type": "application/json",
    }

    outcome = replace_supplier_pages(
        client, headers, ui_server,
        OLD_PAGE_UIDS, NEW_PAGES, BOOK_IDS, OLD_EXPIRATION_DATE, BATCH_SIZE,
    )
    for error in outcome["errors"]:
        print(f"ERROR {error}")
```

**C#:**

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";

const string SupplierId = "100198";                    // supplier the pages belong to
const string CompanyId = "ACME";
const string OldExpirationDate = "2026-12-31";         // date stamped on the OLD pages
const int BatchSize = 25;                              // operations per session batch

int[] oldPageUids = { 100199, 100200 };                // existing pages to expire
var newPages = new List<PageDef>                       // pages to create
{
    new("HVAC", "ACME-HVAC-WHOLESALE", "0.85"),
};
string[] bookIds = { "ACME_BOOK_A" };                  // books to link the new pages to

// Dropdown display values and dates for the new pages - see doc 08
const string PageType = "Supplier / Product Group";
const string PricingMethod = "Source";
const string SourcePrice = "Supplier List Price";
const string CalculationMethod = "Multiplier";
const string NewEffectiveDate = "2027-01-01";
const string NewExpirationDate = "2030-12-31";
// ---------------------------------------------------------------------------

var handler = new HttpClientHandler
{
    // Test tenants often present a self-signed cert. Delete this line in production.
    ServerCertificateCustomValidationCallback =
        HttpClientHandler.DangerousAcceptAnyServerCertificateValidator,
};
using var client = new HttpClient(handler) { Timeout = TimeSpan.FromMinutes(2) };
client.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));

var token = await GetTokenAsync(client);
var uiServer = await GetUiServerAsync(client, token);
client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);

var outcome = await ReplaceSupplierPagesAsync(
    client, uiServer, oldPageUids, newPages, bookIds, OldExpirationDate, BatchSize);
foreach (var error in outcome.Errors)
    Console.WriteLine($"ERROR {error}");

// --- the three-phase workflow ----------------------------------------------

// Replace supplier price pages: expire old, create new, link to books.
static async Task<BatchSummary> ReplaceSupplierPagesAsync(
    HttpClient client,
    string uiServer,
    IReadOnlyList<int> oldPageUids,
    IReadOnlyList<PageDef> newPages,
    IReadOnlyList<string> bookIds,
    string expirationDate,
    int batchSize)
{
    var summary = new BatchSummary();

    // Phase 1: Expire old pages
    if (oldPageUids.Count > 0)
    {
        Console.WriteLine($"Expiring {oldPageUids.Count} old pages...");
        for (int i = 0; i < oldPageUids.Count; i += batchSize)
        {
            var batch = oldPageUids.Skip(i).Take(batchSize).ToList();

            await StartSessionAsync(client, uiServer);
            string windowId = await OpenWindowAsync(client, uiServer, "SalesPricePage");
            try
            {
                foreach (int uid in batch)
                {
                    if (await ExpirePricePageAsync(
                            client, uiServer, windowId, uid, expirationDate))
                    {
                        summary.Expired++;
                        await ClearWindowAsync(client, uiServer, windowId);
                    }
                    else
                    {
                        summary.Errors.Add($"Expire {uid}");
                        await CloseWindowAsync(client, uiServer, windowId);
                        windowId = await OpenWindowAsync(client, uiServer, "SalesPricePage");
                    }
                }
            }
            finally
            {
                await CloseWindowAsync(client, uiServer, windowId);
                await EndSessionAsync(client, uiServer);
            }
        }
    }

    // Phase 2: Create new pages
    var createdUids = new List<int>();
    Console.WriteLine($"Creating {newPages.Count} new pages...");
    for (int i = 0; i < newPages.Count; i += batchSize)
    {
        var batch = newPages.Skip(i).Take(batchSize).ToList();

        await StartSessionAsync(client, uiServer);
        string windowId = await OpenWindowAsync(client, uiServer, "SalesPricePage");
        try
        {
            foreach (var pageDef in batch)
            {
                try
                {
                    int? uid = await CreateSinglePageAsync(
                        client, uiServer, windowId, pageDef);
                    if (uid is not null) createdUids.Add(uid.Value);
                    summary.Created++;
                    await ClearWindowAsync(client, uiServer, windowId);
                }
                catch (Exception ex)
                    when (ex is HttpRequestException or InvalidOperationException)
                {
                    summary.Errors.Add(ex.Message);
                    await CloseWindowAsync(client, uiServer, windowId);
                    windowId = await OpenWindowAsync(client, uiServer, "SalesPricePage");
                }
            }
        }
        finally
        {
            await CloseWindowAsync(client, uiServer, windowId);
            await EndSessionAsync(client, uiServer);
        }
    }

    // Phase 3: Link new pages to books
    Console.WriteLine($"Linking {createdUids.Count} pages to {bookIds.Count} books...");
    for (int i = 0; i < createdUids.Count; i += batchSize)
    {
        var batch = createdUids.Skip(i).Take(batchSize).ToList();

        await StartSessionAsync(client, uiServer);
        try
        {
            foreach (int uid in batch)
            {
                foreach (string bookId in bookIds)
                {
                    try
                    {
                        await LinkPageToBookAsync(client, uiServer, uid, bookId);
                        summary.Linked++;
                    }
                    catch (Exception ex)
                        when (ex is HttpRequestException or InvalidOperationException)
                    {
                        summary.Errors.Add($"Link {uid}->{bookId}: {ex.Message}");
                    }
                }
            }
        }
        finally
        {
            await EndSessionAsync(client, uiServer);
        }
    }

    Console.WriteLine(
        $"Complete: {summary.Expired} expired, {summary.Created} created, " +
        $"{summary.Linked} linked, {summary.Errors.Count} errors");
    return summary;
}

// Expire one page, then confirm the new date reads back.
static async Task<bool> ExpirePricePageAsync(
    HttpClient client, string uiServer, string windowId,
    int pricePageUid, string expirationDate)
{
    foreach (var (fieldName, value) in new[]
             {
                 ("price_page_uid", pricePageUid.ToString()),
                 ("expiration_date", expirationDate),
             })
    {
        var changed = await ChangeFieldAsync(
            client, uiServer, windowId, "FORM", "form", fieldName, value);
        if (StatusOf(changed) != 1)
        {
            Console.WriteLine($"  expire {pricePageUid}: {fieldName} -> " +
                string.Join("; ", MessagesOf(changed)));
            return false;
        }
    }

    var saved = await SaveWindowAsync(client, uiServer, windowId);
    if (StatusOf(saved) != 1)
    {
        Console.WriteLine($"  expire {pricePageUid}: save -> " +
            string.Join("; ", MessagesOf(saved)));
        return false;
    }

    string? landed = await ReadFieldAnywhereAsync(
        client, uiServer, windowId, "expiration_date");
    Console.WriteLine(
        $"  expired {pricePageUid}: expiration_date reads back as {landed ?? "(null)"}");
    return true;
}

// Create one price page and return its generated price_page_uid.
// Field order matters - page type first, company before product group.
// See the SalesPricePage field-order rules in doc 08.
static async Task<int?> CreateSinglePageAsync(
    HttpClient client, string uiServer, string windowId, PageDef pageDef)
{
    var headerFields = new[]
    {
        ("price_page_type_cd", PageType),
        ("company_id", CompanyId),
        ("product_group_id", pageDef.ProductGroupId),
        ("supplier_id", SupplierId),
        ("description", pageDef.Description),
        ("pricing_method_cd", PricingMethod),
        ("source_price_cd", SourcePrice),
        ("effective_date", NewEffectiveDate),
        ("expiration_date", NewExpirationDate),
    };
    foreach (var (fieldName, value) in headerFields)
    {
        var changed = await ChangeFieldAsync(
            client, uiServer, windowId, "FORM", "form", fieldName, value);
        if (StatusOf(changed) != 1)
            throw new InvalidOperationException(
                $"{fieldName}: {string.Join("; ", MessagesOf(changed))}");
    }

    // Switch to the VALUES tab before setting the calculation
    await SelectTabAsync(client, uiServer, windowId, "VALUES");

    foreach (var (fieldName, value) in new[]
             {
                 ("calculation_method_cd", CalculationMethod),
                 ("calculation_value1", pageDef.CalculationValue1),
             })
    {
        var changed = await ChangeFieldAsync(
            client, uiServer, windowId, "VALUES", "values", fieldName, value);
        if (StatusOf(changed) != 1)
            throw new InvalidOperationException(
                $"{fieldName}: {string.Join("; ", MessagesOf(changed))}");
    }

    var saved = await SaveWindowAsync(client, uiServer, windowId);
    if (StatusOf(saved) != 1)
        throw new InvalidOperationException(
            $"save: {string.Join("; ", MessagesOf(saved))}");

    int? newUid = GeneratedKey(saved);
    string? landed = await ReadFieldAnywhereAsync(
        client, uiServer, windowId, "description");
    Console.WriteLine(
        $"  created price_page_uid={newUid}, description reads back as {landed ?? "(null)"}");
    return newUid;
}

// Link a price page to a price book via the SalesPriceBook window.
static async Task<bool> LinkPageToBookAsync(
    HttpClient client, string uiServer, int pricePageUid, string priceBookId)
{
    string windowId = await OpenWindowAsync(client, uiServer, "SalesPriceBook");
    try
    {
        // Retrieve the book by ID - this loads it into the window
        var result = await ChangeFieldAsync(
            client, uiServer, windowId, "FORM", "form", "price_book_id", priceBookId);
        if (StatusOf(result) != 1)
            throw new InvalidOperationException(
                $"retrieve book: {string.Join("; ", MessagesOf(result))}");

        // Switch to the LIST tab before adding rows
        await SelectTabAsync(client, uiServer, windowId, "LIST");

        result = await AddRowAsync(client, uiServer, windowId, "list_detail");
        if (StatusOf(result) != 1)
            throw new InvalidOperationException(
                $"add row: {string.Join("; ", MessagesOf(result))}");

        result = await ChangeFieldAsync(
            client, uiServer, windowId,
            "LIST", "list_detail", "price_page_uid", pricePageUid.ToString());
        if (StatusOf(result) != 1)
            throw new InvalidOperationException(
                $"set price_page_uid: {string.Join("; ", MessagesOf(result))}");

        result = await SaveWindowAsync(client, uiServer, windowId);
        if (StatusOf(result) != 1)
            throw new InvalidOperationException(
                $"save link: {string.Join("; ", MessagesOf(result))}");

        string? landed = await ReadFieldAnywhereAsync(
            client, uiServer, windowId, "price_page_uid");
        Console.WriteLine($"  linked {pricePageUid} -> {priceBookId} " +
            $"(list row reads back as {landed ?? "(null)"})");
        return true;
    }
    finally
    {
        await CloseWindowAsync(client, uiServer, windowId);
    }
}

// --- Interactive API helpers -----------------------------------------------

// Start an Interactive session. 2026.1 renamed SessionId -> Id; read both.
static async Task<string> StartSessionAsync(HttpClient client, string uiServer)
{
    var resp = await SendAsync(client, HttpMethod.Post,
        $"{uiServer}/api/ui/interactive/sessions/",
        new Dictionary<string, object> { ["ResponseWindowHandlingEnabled"] = false });
    if (resp.ValueKind == JsonValueKind.Object)
    {
        if (resp.TryGetProperty("Id", out var id)) return id.GetString() ?? "";
        if (resp.TryGetProperty("SessionId", out var sid)) return sid.GetString() ?? "";
    }
    return "";
}

// Always call this - a leaked session 409s the next create.
static async Task EndSessionAsync(HttpClient client, string uiServer)
{
    using var request = new HttpRequestMessage(
        HttpMethod.Delete, $"{uiServer}/api/ui/interactive/sessions/");
    await client.SendAsync(request);
}

static async Task<string> OpenWindowAsync(
    HttpClient client, string uiServer, string serviceName)
{
    var resp = await SendAsync(client, HttpMethod.Post,
        $"{uiServer}/api/ui/interactive/v2/window",
        new Dictionary<string, object> { ["ServiceName"] = serviceName });
    if (resp.ValueKind == JsonValueKind.Object)
    {
        if (resp.TryGetProperty("WindowId", out var id)) return id.GetString() ?? "";
        if (resp.TryGetProperty("windowId", out var lower)) return lower.GetString() ?? "";
    }
    return "";
}

static async Task CloseWindowAsync(HttpClient client, string uiServer, string windowId)
{
    using var request = new HttpRequestMessage(
        HttpMethod.Delete, $"{uiServer}/api/ui/interactive/v2/window?id={windowId}");
    await client.SendAsync(request);
}

static async Task ClearWindowAsync(HttpClient client, string uiServer, string windowId)
{
    using var request = new HttpRequestMessage(
        HttpMethod.Delete, $"{uiServer}/api/ui/interactive/v2/data?id={windowId}");
    var response = await client.SendAsync(request);
    response.EnsureSuccessStatusCode();
}

// Change one field. One field per call - batched /v2/change is non-atomic.
static async Task<JsonElement> ChangeFieldAsync(
    HttpClient client, string uiServer, string windowId,
    string tab, string datawindow, string field, string value)
{
    var payload = new Dictionary<string, object>
    {
        ["WindowId"] = windowId,
        ["List"] = new[]
        {
            new Dictionary<string, object>
            {
                ["TabName"] = tab,
                ["DatawindowName"] = datawindow,   // required since 25.2
                ["FieldName"] = field,
                ["Value"] = value,
            },
        },
    };
    return await SendAsync(client, HttpMethod.Put,
        $"{uiServer}/api/ui/interactive/v2/change", payload);
}

// Switch tabs. 2026.1 binds PageName only - TabName returns 400.
static async Task<JsonElement> SelectTabAsync(
    HttpClient client, string uiServer, string windowId, string pageName)
{
    return await SendAsync(client, HttpMethod.Put,
        $"{uiServer}/api/ui/interactive/v2/tab",
        new Dictionary<string, object>
        {
            ["WindowId"] = windowId,
            ["PageName"] = pageName,
        });
}

// Add a new row to a datawindow.
static async Task<JsonElement> AddRowAsync(
    HttpClient client, string uiServer, string windowId, string datawindow)
{
    return await SendAsync(client, HttpMethod.Post,
        $"{uiServer}/api/ui/interactive/v2/row",
        new Dictionary<string, object>
        {
            ["WindowId"] = windowId,
            ["DatawindowName"] = datawindow,
        });
}

// Save. The v2 body is the bare window-id GUID as a JSON string.
static async Task<JsonElement> SaveWindowAsync(
    HttpClient client, string uiServer, string windowId)
{
    return await SendAsync(client, HttpMethod.Put,
        $"{uiServer}/api/ui/interactive/v2/data", windowId);
}

// Find a field in whichever datawindow GET /v2/data returns it in.
// GET /v2/data returns the active surface only, and on 2026.1 only a
// varying subset of it - a missing field proves nothing.
static async Task<string?> ReadFieldAnywhereAsync(
    HttpClient client, string uiServer, string windowId, string field)
{
    var resp = await SendAsync(client, HttpMethod.Get,
        $"{uiServer}/api/ui/interactive/v2/data?id={windowId}");
    if (resp.ValueKind != JsonValueKind.Array) return null;

    foreach (var dw in resp.EnumerateArray())
    {
        if (!dw.TryGetProperty("Columns", out var columns) ||
            !dw.TryGetProperty("Data", out var rows) ||
            rows.GetArrayLength() == 0)
            continue;

        int index = -1, i = 0;
        foreach (var column in columns.EnumerateArray())
        {
            if (column.GetString() == field) { index = i; break; }
            i++;
        }
        if (index < 0) continue;

        int activeRow = dw.TryGetProperty("ActiveRow", out var ar) ? ar.GetInt32() : 0;
        return rows[activeRow][index].ToString();
    }
    return null;
}

// After an insert, P21 fires a 'keygenerated' event carrying the new UID.
// Event Data is a key/value list: [{"Key": ..., "Value": ...}].
static int? GeneratedKey(JsonElement result)
{
    if (result.ValueKind != JsonValueKind.Object ||
        !result.TryGetProperty("Events", out var events) ||
        events.ValueKind != JsonValueKind.Array)
        return null;

    foreach (var evt in events.EnumerateArray())
    {
        if (!evt.TryGetProperty("Name", out var name) ||
            name.GetString() != "keygenerated")
            continue;
        if (!evt.TryGetProperty("Data", out var data) ||
            data.ValueKind != JsonValueKind.Array)
            continue;

        foreach (var kv in data.EnumerateArray())
        {
            if (kv.TryGetProperty("Value", out var value) &&
                int.TryParse(value.GetString(), out int key))
                return key;
        }
    }
    return null;
}

// ResultStatus enum: None=0, Success=1, Failure=2, Blocked=3.
static int StatusOf(JsonElement result)
{
    if (result.ValueKind != JsonValueKind.Object ||
        !result.TryGetProperty("Status", out var status))
        return 0;
    return status.ValueKind switch
    {
        JsonValueKind.Number => status.GetInt32(),
        JsonValueKind.String => status.GetString() switch
        {
            "Success" => 1,
            "Failure" => 2,
            "Blocked" => 3,
            _ => 0,
        },
        _ => 0,
    };
}

// Failure detail lives in the top-level Messages array, not in Events.
static List<string> MessagesOf(JsonElement result)
{
    var messages = new List<string>();
    if (result.ValueKind == JsonValueKind.Object &&
        result.TryGetProperty("Messages", out var arr) &&
        arr.ValueKind == JsonValueKind.Array)
    {
        foreach (var message in arr.EnumerateArray())
            messages.Add(message.TryGetProperty("Text", out var text)
                ? text.GetString() ?? "" : "");
    }
    return messages;
}

static async Task<JsonElement> SendAsync(
    HttpClient client, HttpMethod method, string url, object? body = null)
{
    using var request = new HttpRequestMessage(method, url);
    if (body is not null)
        request.Content = new StringContent(
            JsonSerializer.Serialize(body), Encoding.UTF8, "application/json");
    var response = await client.SendAsync(request);
    response.EnsureSuccessStatusCode();
    var text = await response.Content.ReadAsStringAsync();
    if (string.IsNullOrWhiteSpace(text)) return default;
    using var doc = JsonDocument.Parse(text);
    return doc.RootElement.Clone();
}

// --- auth helpers ----------------------------------------------------------

// v2 token endpoint — credentials go in the body, never in headers.
static async Task<string> GetTokenAsync(HttpClient client)
{
    var payload = JsonSerializer.Serialize(new { username = Username, password = Password });
    var response = await client.PostAsync(
        $"{BaseUrl}/api/security/token/v2",
        new StringContent(payload, Encoding.UTF8, "application/json"));
    response.EnsureSuccessStatusCode();
    return ReadField(await response.Content.ReadAsStringAsync(), "AccessToken");
}

// Transaction and Interactive calls go to the UI server, not BaseUrl.
static async Task<string> GetUiServerAsync(HttpClient client, string token)
{
    using var request = new HttpRequestMessage(
        HttpMethod.Get, $"{BaseUrl}/api/ui/router/v1/?urlType=external");
    request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
    var response = await client.SendAsync(request);
    response.EnsureSuccessStatusCode();
    return ReadField(await response.Content.ReadAsStringAsync(), "Url").TrimEnd('/');
}

// Some middleware answers these two endpoints in XML even when asked for JSON.
static string ReadField(string payload, string field)
{
    try
    {
        var value = JsonDocument.Parse(payload).RootElement.GetProperty(field).GetString();
        if (!string.IsNullOrEmpty(value)) return value;
    }
    catch (Exception ex) when (ex is JsonException or KeyNotFoundException) { }

    var match = System.Text.RegularExpressions.Regex.Match(payload, $"<{field}>([^<]+)</{field}>");
    if (!match.Success)
        throw new InvalidOperationException(
            $"No {field} in response: {payload[..Math.Min(200, payload.Length)]}");
    return match.Groups[1].Value;
}

// --- records ---------------------------------------------------------------

public record PageDef(
    string ProductGroupId, string Description, string CalculationValue1);

public class BatchSummary
{
    public int Expired { get; set; }
    public int Created { get; set; }
    public int Linked { get; set; }
    public List<string> Errors { get; set; } = new();
}
```

<!-- /tabs -->

---

## Performance Summary

Measured from production use creating and managing 700+ price pages:

| Operation | Time | Notes |
|-----------|------|-------|
| Authenticate | ~200ms | One-time per client |
| Start session | ~300ms | Once per batch |
| Open window | ~500ms | Once per batch |
| Change field | ~100ms | Per field |
| Save record | ~400ms | Per record |
| Clear data | ~200ms | Between records |
| Close window | ~200ms | Once per batch |
| End session | ~100ms | Once per batch |
| **Full page creation** | **~2.5s** | Including all fields + save |
| **25-page batch** | **~62s** | Including session overhead |

---

## Related

- [Interactive API](04-Interactive-API.md) - Core Interactive API documentation
- [SalesPricePage Codes](08-SalesPricePage-Codes.md) - Dropdown codes and field order
- [Error Handling](06-Error-Handling.md) - Error handling patterns
- [Session Pool Troubleshooting](07-Session-Pool-Troubleshooting.md) - Session pool issues
