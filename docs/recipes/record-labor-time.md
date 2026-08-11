# Record Labor Time on a Production Order

Post a technician's labor hours to a production order with the `TimeEntry` service.

**API:** Transaction · **Service:** `TimeEntry` · **Deep dive:** [Recording Labor Hours](../12-Production-Labor-API.md#recording-labor-hours-timeentry-service), [Quick Time Entry mechanics](../12-Production-Labor-API.md#time-entry-against-a-production-order-quick-time-entry), [Labor timing](../12-Production-Labor-API.md#labor-timing-log-labor-before-printing) · **Full schema:** [definitions/TimeEntry.json](../../definitions/TimeEntry.json)

## Prerequisites

- A production order exists (here `1000123`) with an assembly line (item `ASSY-100`) carrying a labor component (here `LABOR-SHOP`).
- `technician_id` is a **contact ID** (here `300`) — not a P21 user ID.
- The **accounting period for `entry_date` must be open**, or the save fails.
- If the order will be completed later: **log labor before printing the pick ticket** (or reprint after) — labor must land on a pick ticket to be consumed at completion. See [the runbook](production-order-runbook.md).
- For labor against **service orders**, use the separate `TimeEntrySO` service instead.

## Payload

`POST {ui_server}/api/v2/transaction`, `Status: "New"`, `UseCodeValues: false`. Two DataElements:

**Header — `TP_TECHNICIAN.tp_technician` (Form)**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `company_id` | Char | Yes | Company ID |
| `technician_id` | Char | Yes | **A contact ID**, not a user ID |
| `entry_date` | Datetime | Yes | Accounting period for this date must be open |

**Labor lines — `TP_LABORRECORDING.prod_order_line_comp_labor` (List, key `prod_order_number`)**

Enter the fields **in this order** — out of order, the downstream fields stay disabled:

| # | Field | Type | Notes |
|---|-------|------|-------|
| 1 | `prod_order_number` | Decimal | Key. The production order |
| 2 | `item_id` | Char | The assembly **line's** item (not the component) |
| 3 | `component_labor_id` | Char | The labor component on that line |
| 4 | `start_time` | Datetime | |
| 5 | `end_time` | Datetime | |

Other fields from the definition: `service_labor_id` (labor ID from the `Labor` service — the alternate lookup used in the [manual's reference example](../12-Production-Labor-API.md#recording-labor-hours-timeentry-service)), `time_worked` (Char, `HH:MM`), `labor_type_cd` (Long, **required** — valid values `Rate`, `OT Rate`, `Prem Rate`), `operation_cd`, `cc_completeprodorder`.

Time is stored per line at minute granularity and **accumulates across entries**; cost = minutes × the labor code's rate.

## Complete example

Posts 4 hours against the labor component, then reads the labor grid back.

<!-- tabs -->
```python
"""Post labor hours to a production order, then read the labor grid back."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
COMPANY_ID = "ACME"
TECHNICIAN_ID = "300"                     # a CONTACT id, not a P21 user id
ENTRY_DATE = "2030-01-05"                 # its accounting period must be OPEN
PROD_ORDER = "1000123"
ASSEMBLY_ITEM_ID = "ASSY-100"             # the assembly LINE's item
COMPONENT_LABOR_ID = "LABOR-SHOP"         # the labor component on that line
START_TIME = "2030-01-05T08:00:00"
END_TIME = "2030-01-05T12:00:00"
LABOR_TYPE_CD = "Rate"                    # Rate | OT Rate | Prem Rate
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


with httpx.Client(verify=VERIFY_SSL, timeout=120, follow_redirects=True) as client:
    token = get_token(client)
    ui_server = get_ui_server(client, token)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",       # 2026.1 returns an empty 500 without this
        "Content-Type": "application/json",
    }

    payload = {
        "Name": "TimeEntry",
        "UseCodeValues": False,
        "Transactions": [{
            "Status": "New",
            "DataElements": [
                {
                    "Name": "TP_TECHNICIAN.tp_technician",
                    "Type": "Form",
                    "Keys": [],
                    "Rows": [{
                        "Edits": [
                            {"Name": "company_id", "Value": COMPANY_ID},
                            {"Name": "technician_id", "Value": TECHNICIAN_ID},
                            {"Name": "entry_date", "Value": ENTRY_DATE},
                        ],
                        "RelativeDateEdits": [],
                    }],
                },
                {
                    "Name": "TP_LABORRECORDING.prod_order_line_comp_labor",
                    "Type": "List",
                    "Keys": ["prod_order_number"],
                    "Rows": [{
                        # Strict order: prod_order_number -> item_id ->
                        # component_labor_id -> start_time -> end_time
                        "Edits": [
                            {"Name": "prod_order_number", "Value": PROD_ORDER},
                            {"Name": "item_id", "Value": ASSEMBLY_ITEM_ID},
                            {"Name": "component_labor_id", "Value": COMPONENT_LABOR_ID},
                            {"Name": "start_time", "Value": START_TIME},
                            {"Name": "end_time", "Value": END_TIME},
                            {"Name": "labor_type_cd", "Value": LABOR_TYPE_CD},
                        ],
                        "RelativeDateEdits": [],
                    }],
                },
            ],
        }],
    }

    resp = client.post(f"{ui_server}/api/v2/transaction",
                       headers=headers, json=payload)
    resp.raise_for_status()  # HTTP 200 even on failure -- check the Summary
    result = resp.json()

    summary = result["Summary"]
    print(f"Succeeded: {summary['Succeeded']}, Failed: {summary['Failed']}")
    if summary["Failed"] > 0:
        for msg in result.get("Messages", []):
            print(f"  {msg}")
        raise SystemExit("Time entry failed")

    # --- Read back the labor grid for the order ---
    # time_worked is the ACCUMULATED total, not just this entry.
    get_payload = {
        "ServiceName": "TimeEntry",
        "TransactionStates": [{
            "DataElementName": "TP_LABORRECORDING.prod_order_line_comp_labor",
            "Keys": [{"Name": "prod_order_number", "Value": PROD_ORDER}],
        }],
    }
    resp = client.post(f"{ui_server}/api/v2/transaction/get",
                       headers=headers, json=get_payload)
    resp.raise_for_status()
    for txn in resp.json().get("Transactions", []):
        for de in txn.get("DataElements", []):
            for row in de.get("Rows", []):
                fields = {e["Name"]: e["Value"] for e in row.get("Edits", [])}
                if fields.get("prod_order_number"):
                    labor_id = (fields.get("component_labor_id")
                                or fields.get("service_labor_id"))
                    print(f"  {labor_id}: time_worked={fields.get('time_worked')}")
```

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string CompanyId = "ACME";
const string TechnicianId = "300";       // a CONTACT id, not a P21 user id
const string EntryDate = "2030-01-05";   // its accounting period must be OPEN
const string ProdOrder = "1000123";
const string AssemblyItemId = "ASSY-100";        // the assembly LINE's item
const string ComponentLaborId = "LABOR-SHOP";    // the labor component on that line
const string StartTime = "2030-01-05T08:00:00";
const string EndTime = "2030-01-05T12:00:00";
const string LaborTypeCd = "Rate";       // Rate | OT Rate | Prem Rate
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

var payload = new
{
    Name = "TimeEntry",
    UseCodeValues = false,
    Transactions = new[]
    {
        new
        {
            Status = "New",
            DataElements = new object[]
            {
                new
                {
                    Name = "TP_TECHNICIAN.tp_technician",
                    Type = "Form",
                    Keys = Array.Empty<string>(),
                    Rows = new[]
                    {
                        new
                        {
                            Edits = new[]
                            {
                                new { Name = "company_id", Value = CompanyId },
                                new { Name = "technician_id", Value = TechnicianId },
                                new { Name = "entry_date", Value = EntryDate },
                            },
                            RelativeDateEdits = Array.Empty<object>(),
                        },
                    },
                },
                new
                {
                    Name = "TP_LABORRECORDING.prod_order_line_comp_labor",
                    Type = "List",
                    Keys = new[] { "prod_order_number" },
                    Rows = new[]
                    {
                        new
                        {
                            // Strict order: prod_order_number -> item_id ->
                            // component_labor_id -> start_time -> end_time
                            Edits = new[]
                            {
                                new { Name = "prod_order_number", Value = ProdOrder },
                                new { Name = "item_id", Value = AssemblyItemId },
                                new { Name = "component_labor_id", Value = ComponentLaborId },
                                new { Name = "start_time", Value = StartTime },
                                new { Name = "end_time", Value = EndTime },
                                new { Name = "labor_type_cd", Value = LaborTypeCd },
                            },
                            RelativeDateEdits = Array.Empty<object>(),
                        },
                    },
                },
            },
        },
    },
};

using var resp = await client.PostAsync(
    $"{uiServer}/api/v2/transaction",
    new StringContent(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json"));
resp.EnsureSuccessStatusCode();  // HTTP 200 even on failure -- check the Summary
using var result = JsonDocument.Parse(await resp.Content.ReadAsStringAsync());

var summary = result.RootElement.GetProperty("Summary");
Console.WriteLine($"Succeeded: {summary.GetProperty("Succeeded")}, " +
                  $"Failed: {summary.GetProperty("Failed")}");
if (summary.GetProperty("Failed").GetInt32() > 0)
{
    if (result.RootElement.TryGetProperty("Messages", out var messages))
    {
        Console.Error.WriteLine($"  {messages}");
    }
    throw new InvalidOperationException("Time entry failed");
}

// --- Read back the labor grid for the order ---
// time_worked is the ACCUMULATED total, not just this entry.
var getPayload = new
{
    ServiceName = "TimeEntry",
    TransactionStates = new[]
    {
        new
        {
            DataElementName = "TP_LABORRECORDING.prod_order_line_comp_labor",
            Keys = new[] { new { Name = "prod_order_number", Value = ProdOrder } },
        },
    },
};
using var getResp = await client.PostAsync(
    $"{uiServer}/api/v2/transaction/get",
    new StringContent(JsonSerializer.Serialize(getPayload), Encoding.UTF8, "application/json"));
getResp.EnsureSuccessStatusCode();
using var getResult = JsonDocument.Parse(await getResp.Content.ReadAsStringAsync());

foreach (var txn in getResult.RootElement.GetProperty("Transactions").EnumerateArray())
{
    foreach (var de in txn.GetProperty("DataElements").EnumerateArray())
    {
        foreach (var row in de.GetProperty("Rows").EnumerateArray())
        {
            var fields = new Dictionary<string, string?>();
            foreach (var edit in row.GetProperty("Edits").EnumerateArray())
            {
                fields[edit.GetProperty("Name").GetString()!] =
                    edit.GetProperty("Value").GetString();
            }
            if (string.IsNullOrEmpty(fields.GetValueOrDefault("prod_order_number"))) continue;
            var laborId = fields.GetValueOrDefault("component_labor_id")
                          ?? fields.GetValueOrDefault("service_labor_id");
            Console.WriteLine($"  {laborId}: " +
                              $"time_worked={fields.GetValueOrDefault("time_worked")}");
        }
    }
}

// --- helpers ---------------------------------------------------------------

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

> **Payload files:** [JSON](../../examples/payloads/json/record-labor-time.json) · [XML](../../examples/payloads/xml/record-labor-time.xml) — validator-verified, see [payloads README](../../examples/payloads/README.md).
>
> **End-to-end files** (runnable from the repo with a `.env`, dry-run by default): [`examples/python/recipes/record_labor_time.py`](../../examples/python/recipes/record_labor_time.py) · [`examples/csharp/Recipes/RecordLaborTime.cs`](../../examples/csharp/Recipes/RecordLaborTime.cs). The snippet above is self-contained; the files use the repo's shared `common` / `P21Examples.Common` helpers like every other example.

## Gotchas

- **Strict field order** on the labor grid: `prod_order_number` → `item_id` → `component_labor_id` → `start_time` → `end_time`. Out of order, the downstream fields stay disabled and the values don't land.
- **`technician_id` is a contact ID**, not a P21 user ID.
- **The accounting period for `entry_date` must be open** — a closed period fails the save.
- **Time accumulates.** Each entry adds to the line's stored hours/minutes; re-posting the same entry doubles the labor (and its cost = minutes × the labor code's rate).
- **Log labor before printing the pick ticket** (or reprint after adding it). Labor on no ticket has `qty_on_pick_tickets = 0` and order completion fails with *"components have a quantity used of 0."*
- **Cost timing:** labor posted before completion lands in the `PROP` receipt cost; labor posted after completion misses it; labor posted after invoicing generates a separate *"Post Freight/Labor Prod. Order: NNNN"* invoice ($0 price, ± COGS). See [the cost model](../12-Production-Labor-API.md#cost-model-know-this-before-trusting-cogs).
- **`labor_type_cd` is required** — valid values `Rate`, `OT Rate`, `Prem Rate` (with `UseCodeValues: false`).
- **HTTP 200 is not success** — check `Summary.Succeeded` / `Summary.Failed` and print `Messages`.

## Verify

Read the labor grid back (second half of the example): `POST /api/v2/transaction/get` on `TimeEntry`, element `TP_LABORRECORDING.prod_order_line_comp_labor`, keyed by `prod_order_number` — the line's `time_worked` should reflect the **accumulated** total, not just this entry. A successful post also returns `Status: "Passed"` on the transaction with `Summary.Succeeded: 1`.

> **Credit:** [Alex Westemeier](https://github.com/AWestemeier)
