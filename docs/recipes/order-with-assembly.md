# Order with an Assembly Line

Enter a sales order interactively when a line is an assembly that must explode into components and/or spawn a production order.

**API:** Interactive · **Service:** `Order` (window) · **Deep dive:** [Sales Order Entry with Assembly Lines](../04-Interactive-API.md#sales-order-entry-with-assembly-lines) · [Response Windows](../04-Interactive-API.md#response-windows) · **Full schema:** [Order.json](../../definitions/Order.json)

## Prerequisites

- P21 credentials — the complete example below authenticates itself; nothing to install but `httpx` (Python) or a bare `net9.0` console project (C#).
- The item is configured as an assembly (`assembly_hdr`): `production_order_processing` `Y` = production-order assembly / `N` = kit; `auto_create_prod_order` `Y` = auto-create and link the production order at save.
- **Why not the Transaction API?** Entering an assembly item there fires an *"add as assembly?"* prompt which the stateless API auto-answers **No**, killing the explode ([Order Service Gotchas](../03-Transaction-API.md#order-service-gotchas)). The Interactive API lets you answer it. For plain (non-assembly) orders, use the simpler [create-sales-order](create-sales-order.md) recipe instead.
- The session must be started with **`ResponseWindowHandlingEnabled: true`** so you can inspect and answer the prompts yourself.

## Flow

1. **Start a session** with response-window handling enabled:

   ```json
   POST /api/ui/interactive/sessions
   { "ResponseWindowHandlingEnabled": true }
   ```

2. **Open the Order window**:

   ```json
   POST /api/ui/interactive/v2/window
   { "ServiceName": "Order" }
   ```

3. **Set header fields** on `TabName: "TABPAGE_1"`, `DatawindowName: "order"` — `quote` (`OFF` = real order, `ON` = quote), `sales_loc_id`, `source_loc_id`, `customer_id`, `ship_to_id`, `contact_id`, `order_date`, `requested_date`, `po_no`, `taker`:

   ```json
   PUT /api/ui/interactive/v2/change
   {
       "WindowId": "{windowId}",
       "List": [{
           "TabName": "TABPAGE_1",
           "DatawindowName": "order",
           "FieldName": "customer_id",
           "Value": "100198"
       }]
   }
   ```

   **Setting the dates fires a date-cascade prompt** (`w_response_common`, buttons `cb_ok`/`cb_cancel`) *even on a brand-new order*: the change result comes back `Status: 3` (Blocked) with a `windowopened` event carrying the popup's window ID. Answer **`cb_ok`** against the **popup's** window ID:

   ```json
   POST /api/ui/interactive/v2/tools
   { "WindowId": "{popupWindowId}", "ToolName": "cb_ok" }
   ```

4. **Switch to the lines tab**:

   ```json
   PUT /api/ui/interactive/v2/tab
   { "WindowId": "{windowId}", "PageName": "TP_ITEMS" }
   ```

5. **Set `oe_order_item_id` on the *existing* `items` row** (`TabName: "TP_ITEMS"`, `DatawindowName: "items"` — do **not** add a row for the first line). On an assembly item this fires the **assembly prompt** (buttons `cb_1` = Yes / `cb_2` = No / `cb_3` = Cancel) — answer **`cb_1`** to explode the assembly / link a production order.

6. **Set `unit_quantity`** on the same row.

7. **Save** — in v2 the body is the bare window-ID string, *not* an object:

   ```json
   PUT /api/ui/interactive/v2/data
   "{windowId}"
   ```

   Answer any follow-on prompts with their proceed button.

8. **Read the generated `order_no`** from the window data: `GET /api/ui/interactive/v2/data?id={windowId}` (returns the datawindows on the active surface — switch back to `TABPAGE_1` first so the `order` datawindow is active).

9. **Clean up**: `DELETE /api/ui/interactive/v2/window?id={windowId}`, then `DELETE /api/ui/interactive/sessions`.

## Complete example

Includes an `answer_response_windows` helper grounded in the [Response Windows](../04-Interactive-API.md#response-windows) pattern: loop over `windowopened` events, discover the popup's buttons with `GET /v2/tools?windowId={popupId}`, click one with `POST /v2/tools`.

<!-- tabs -->
```python
"""Enter a sales order with an assembly line via the Interactive API, then verify."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
CUSTOMER_ID = "100198"
SALES_LOC_ID = "10"
SOURCE_LOC_ID = "10"
SHIP_TO_ID = "200"
CONTACT_ID = "300"
ORDER_DATE = "2030-01-05"
REQUESTED_DATE = "2030-01-06"
PO_NO = "PO-TEST-001"
TAKER = "JSMITH"                          # else the order is taken by the API user
ASSEMBLY_ITEM_ID = "WIDGET-001"           # the assembly item to explode
UNIT_QUANTITY = "5"
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


def is_blocked(result: dict) -> bool:
    # Status is an integer (ResultStatus enum: 0 None, 1 Success, 2 Failure,
    # 3 Blocked) but may appear as a string in some contexts -- handle both.
    return result.get("Status") in (3, "Blocked")


def popup_ids(result: dict) -> list[str]:
    """Window IDs of popups opened by the last action.

    Events[].Data is a key-value list: [{"Key": "windowid", "Value": "..."}].
    """
    ids = []
    for event in result.get("Events", []):
        if event.get("Name") == "windowopened":
            for kv in event.get("Data", []):
                if kv.get("Key") == "windowid":
                    ids.append(kv["Value"])
    return ids


with httpx.Client(verify=VERIFY_SSL, timeout=120, follow_redirects=True) as client:
    token = get_token(client)
    ui_server = get_ui_server(client, token)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",       # 2026.1 returns an empty 500 without this
        "Content-Type": "application/json",
    }
    iapi = f"{ui_server}/api/ui/interactive"

    def answer_response_windows(result: dict, button: str | None = None) -> dict:
        """Answer every popup the last action opened, then return the last result.

        Discovers buttons via GET /v2/tools?windowId= (the tools endpoint takes
        ?windowId=, NOT ?id=), then clicks via POST /v2/tools with the POPUP's
        window ID. If `button` is None, picks the first proceed-style button.
        """
        for popup_id in popup_ids(result):
            tools = client.get(f"{iapi}/v2/tools", params={"windowId": popup_id},
                               headers=headers)
            tools.raise_for_status()
            available = [t.get("Name") or t.get("ToolName") for t in tools.json()]
            pick = button
            if pick is None:  # prefer common proceed buttons
                pick = next((b for b in ("cb_ok", "cb_1", "cb_yes")
                             if b in available), None)
            if pick is None or pick not in available:
                raise RuntimeError(
                    f"Popup {popup_id}: buttons {available}, wanted {button}")
            click = client.post(
                f"{iapi}/v2/tools", headers=headers,
                json={"WindowId": popup_id, "ToolName": pick},
            )
            click.raise_for_status()
            result = click.json()
        return result

    def change(window_id: str, tab: str, dw: str, field: str, value: str,
               answer: str | None = None) -> dict:
        """Change one field; answer the popup it triggers (if any) with `answer`."""
        resp = client.put(
            f"{iapi}/v2/change", headers=headers,
            json={"WindowId": window_id, "List": [{
                "TabName": tab, "DatawindowName": dw,  # required on 25.2+
                "FieldName": field, "Value": value,
            }]},
        )
        resp.raise_for_status()
        result = resp.json()
        if result.get("Status") in (2, "Failure"):
            raise RuntimeError(f"{field}: {result.get('Messages')}")
        if is_blocked(result):
            result = answer_response_windows(result, answer)
        return result

    # 1. Session with response-window handling ON
    client.post(
        f"{iapi}/sessions", headers=headers,
        json={"ResponseWindowHandlingEnabled": True},
    ).raise_for_status()

    # 2. Open the Order window
    win = client.post(f"{iapi}/v2/window", headers=headers,
                      json={"ServiceName": "Order"})
    win.raise_for_status()
    window_id = win.json()["WindowId"]

    order_no = None
    try:
        # 3. Header -- TABPAGE_1 / datawindow "order". quote OFF = real order.
        change(window_id, "TABPAGE_1", "order", "quote", "OFF")
        change(window_id, "TABPAGE_1", "order", "sales_loc_id", SALES_LOC_ID)
        change(window_id, "TABPAGE_1", "order", "source_loc_id", SOURCE_LOC_ID)
        change(window_id, "TABPAGE_1", "order", "customer_id", CUSTOMER_ID)
        change(window_id, "TABPAGE_1", "order", "ship_to_id", SHIP_TO_ID)
        change(window_id, "TABPAGE_1", "order", "contact_id", CONTACT_ID)
        # Dates fire the w_response_common date-cascade prompt even on a NEW order
        change(window_id, "TABPAGE_1", "order", "order_date", ORDER_DATE, answer="cb_ok")
        change(window_id, "TABPAGE_1", "order", "requested_date", REQUESTED_DATE,
               answer="cb_ok")
        change(window_id, "TABPAGE_1", "order", "po_no", PO_NO)
        change(window_id, "TABPAGE_1", "order", "taker", TAKER)

        # 4. Lines tab
        client.put(
            f"{iapi}/v2/tab", headers=headers,
            json={"WindowId": window_id, "PageName": "TP_ITEMS"},
        ).raise_for_status()

        # 5. Item on the EXISTING items row (no /v2/row add for the first line).
        #    Assembly prompt: cb_1 = Yes (explode / link prod order).
        change(window_id, "TP_ITEMS", "items", "oe_order_item_id",
               ASSEMBLY_ITEM_ID, answer="cb_1")
        # 6. Quantity
        change(window_id, "TP_ITEMS", "items", "unit_quantity", UNIT_QUANTITY)

        # 7. Save -- v2 body is the bare window-ID string (an object => 422)
        save = client.put(f"{iapi}/v2/data", headers=headers, json=window_id)
        save.raise_for_status()
        result = save.json()
        while is_blocked(result):  # follow-on prompts: answer with proceed button
            result = answer_response_windows(result)
        if result.get("Status") in (2, "Failure"):
            raise RuntimeError(f"Save failed: {result.get('Messages')}")

        # 8. Read order_no back. GET /v2/data returns the ACTIVE surface --
        #    switch back to the header tab first.
        client.put(
            f"{iapi}/v2/tab", headers=headers,
            json={"WindowId": window_id, "PageName": "TABPAGE_1"},
        ).raise_for_status()
        data = client.get(f"{iapi}/v2/data", params={"id": window_id},
                          headers=headers)
        data.raise_for_status()
        for dw in data.json():
            if dw.get("Name") == "order":
                row = dw["Data"][dw.get("ActiveRow", 0)]
                order_no = row[dw["Columns"].index("order_no")]
                print(f"Created order_no: {order_no}")
    finally:
        # 9. Clean up (window uses ?id=; sessions endpoint takes no parameter)
        client.delete(f"{iapi}/v2/window", params={"id": window_id}, headers=headers)
        client.delete(f"{iapi}/sessions", headers=headers)

    # 10. Verify via OData (mirrors the Verify section): assembly codes on the
    #     lines, and the production-order link for the assembly line.
    lines = client.get(
        f"{BASE_URL}/odataservice/odata/table/oe_line",
        params={"$filter": f"order_no eq '{order_no}'"},
        headers=headers,
    )
    lines.raise_for_status()
    for line in lines.json()["value"]:
        # assembly: B = kit parent, N = component, P = production-order line,
        # S = build-to-stock allocation
        print(f"Line {line['line_no']}: assembly={line['assembly']}")
        if line["assembly"] == "P":
            link = client.get(
                f"{BASE_URL}/odataservice/odata/table/prod_order_line_link",
                params={"$filter": f"transaction_uid eq {line['oe_line_uid']} "
                                   "and trans_type eq 'O'"},
                headers=headers,
            )
            link.raise_for_status()
            linked = bool(link.json()["value"])
            print(f"  prod_order_line_link: {'present' if linked else 'MISSING'}")
```

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string CustomerId = "100198";
const string SalesLocId = "10";
const string SourceLocId = "10";
const string ShipToId = "200";
const string ContactId = "300";
const string OrderDate = "2030-01-05";
const string RequestedDate = "2030-01-06";
const string PoNo = "PO-TEST-001";
const string Taker = "JSMITH";              // else the order is taken by the API user
const string AssemblyItemId = "WIDGET-001"; // the assembly item to explode
const string UnitQuantity = "5";
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
var iapi = $"{uiServer}/api/ui/interactive";

// Status is an integer (ResultStatus enum: 0 None, 1 Success, 2 Failure,
// 3 Blocked) but may appear as a string in some contexts -- handle both.
static bool IsBlocked(JsonElement r) =>
    r.TryGetProperty("Status", out var s) && StatusText(s) is "3" or "Blocked";

static string? StatusText(JsonElement s) =>
    s.ValueKind == JsonValueKind.String ? s.GetString() : s.ToString();

// Window IDs of popups opened by the last action.
// Events[].Data is a key-value list: [{"Key": "windowid", "Value": "..."}].
static List<string> PopupIds(JsonElement r)
{
    var ids = new List<string>();
    if (!r.TryGetProperty("Events", out var events)) return ids;
    foreach (var e in events.EnumerateArray())
    {
        if (e.GetProperty("Name").GetString() != "windowopened") continue;
        foreach (var kv in e.GetProperty("Data").EnumerateArray())
        {
            if (kv.GetProperty("Key").GetString() == "windowid")
            {
                ids.Add(kv.GetProperty("Value").GetString()!);
            }
        }
    }
    return ids;
}

// Answer every popup the last action opened; button null => first proceed button.
async Task<JsonElement> AnswerResponseWindowsAsync(JsonElement result, string? button = null)
{
    foreach (var popupId in PopupIds(result))
    {
        // Tools endpoint takes ?windowId=, NOT ?id=
        using var toolsResp = await client.GetAsync($"{iapi}/v2/tools?windowId={popupId}");
        toolsResp.EnsureSuccessStatusCode();
        using var tools = JsonDocument.Parse(await toolsResp.Content.ReadAsStringAsync());
        var available = tools.RootElement.EnumerateArray()
            .Select(t => t.TryGetProperty("Name", out var n)
                ? n.GetString()
                : t.GetProperty("ToolName").GetString())
            .ToList();
        var pick = button
            ?? new[] { "cb_ok", "cb_1", "cb_yes" }.FirstOrDefault(available.Contains)
            ?? throw new InvalidOperationException(
                $"Popup {popupId}: buttons [{string.Join(", ", available)}]");
        var clickBody = JsonSerializer.Serialize(new { WindowId = popupId, ToolName = pick });
        using var clickResp = await client.PostAsync($"{iapi}/v2/tools",
            new StringContent(clickBody, Encoding.UTF8, "application/json"));
        clickResp.EnsureSuccessStatusCode();
        using var clicked = JsonDocument.Parse(await clickResp.Content.ReadAsStringAsync());
        result = clicked.RootElement.Clone();
    }
    return result;
}

// Change one field; answer the popup it triggers (if any) with `answer`.
async Task<JsonElement> ChangeAsync(string windowId, string tab, string dw,
    string field, string value, string? answer = null)
{
    var body = JsonSerializer.Serialize(new
    {
        WindowId = windowId,
        List = new[]
        {
            new
            {
                TabName = tab,
                DatawindowName = dw,   // required on 25.2+
                FieldName = field,
                Value = value,
            },
        },
    });
    using var resp = await client.PutAsync($"{iapi}/v2/change",
        new StringContent(body, Encoding.UTF8, "application/json"));
    resp.EnsureSuccessStatusCode();
    using var parsed = JsonDocument.Parse(await resp.Content.ReadAsStringAsync());
    var result = parsed.RootElement.Clone();
    if (result.TryGetProperty("Status", out var status) &&
        StatusText(status) is "2" or "Failure")
    {
        throw new InvalidOperationException($"{field}: {result.GetProperty("Messages")}");
    }
    return IsBlocked(result) ? await AnswerResponseWindowsAsync(result, answer) : result;
}

// 1. Session with response-window handling ON
using (var sessResp = await client.PostAsync($"{iapi}/sessions",
    new StringContent(
        JsonSerializer.Serialize(new { ResponseWindowHandlingEnabled = true }),
        Encoding.UTF8, "application/json")))
{
    sessResp.EnsureSuccessStatusCode();
}

// 2. Open the Order window
string windowId;
using (var winResp = await client.PostAsync($"{iapi}/v2/window",
    new StringContent(JsonSerializer.Serialize(new { ServiceName = "Order" }),
        Encoding.UTF8, "application/json")))
{
    winResp.EnsureSuccessStatusCode();
    using var win = JsonDocument.Parse(await winResp.Content.ReadAsStringAsync());
    windowId = win.RootElement.GetProperty("WindowId").GetString()!;
}

string? orderNo = null;
try
{
    // 3. Header -- TABPAGE_1 / datawindow "order". quote OFF = real order.
    await ChangeAsync(windowId, "TABPAGE_1", "order", "quote", "OFF");
    await ChangeAsync(windowId, "TABPAGE_1", "order", "sales_loc_id", SalesLocId);
    await ChangeAsync(windowId, "TABPAGE_1", "order", "source_loc_id", SourceLocId);
    await ChangeAsync(windowId, "TABPAGE_1", "order", "customer_id", CustomerId);
    await ChangeAsync(windowId, "TABPAGE_1", "order", "ship_to_id", ShipToId);
    await ChangeAsync(windowId, "TABPAGE_1", "order", "contact_id", ContactId);
    // Dates fire the w_response_common date-cascade prompt even on a NEW order
    await ChangeAsync(windowId, "TABPAGE_1", "order", "order_date", OrderDate, "cb_ok");
    await ChangeAsync(windowId, "TABPAGE_1", "order", "requested_date", RequestedDate, "cb_ok");
    await ChangeAsync(windowId, "TABPAGE_1", "order", "po_no", PoNo);
    await ChangeAsync(windowId, "TABPAGE_1", "order", "taker", Taker);

    // 4. Lines tab
    await SwitchTabAsync(client, iapi, windowId, "TP_ITEMS");

    // 5. Item on the EXISTING items row; assembly prompt: cb_1 = Yes (explode)
    await ChangeAsync(windowId, "TP_ITEMS", "items", "oe_order_item_id",
        AssemblyItemId, "cb_1");
    // 6. Quantity
    await ChangeAsync(windowId, "TP_ITEMS", "items", "unit_quantity", UnitQuantity);

    // 7. Save -- v2 body is the bare window-ID JSON string (an object => 422)
    JsonElement result;
    using (var saveResp = await client.PutAsync($"{iapi}/v2/data",
        new StringContent($"\"{windowId}\"", Encoding.UTF8, "application/json")))
    {
        saveResp.EnsureSuccessStatusCode();
        using var saved = JsonDocument.Parse(await saveResp.Content.ReadAsStringAsync());
        result = saved.RootElement.Clone();
    }
    while (IsBlocked(result))  // follow-on prompts: answer with proceed button
    {
        result = await AnswerResponseWindowsAsync(result);
    }
    if (result.TryGetProperty("Status", out var saveStatus) &&
        StatusText(saveStatus) is "2" or "Failure")
    {
        throw new InvalidOperationException($"Save failed: {result.GetProperty("Messages")}");
    }

    // 8. Read order_no back -- /v2/data returns the ACTIVE surface, so
    //    switch back to the header tab first.
    await SwitchTabAsync(client, iapi, windowId, "TABPAGE_1");
    using var dataResp = await client.GetAsync($"{iapi}/v2/data?id={windowId}");
    dataResp.EnsureSuccessStatusCode();
    using var data = JsonDocument.Parse(await dataResp.Content.ReadAsStringAsync());
    foreach (var dw in data.RootElement.EnumerateArray())
    {
        if (dw.GetProperty("Name").GetString() != "order") continue;
        var columns = dw.GetProperty("Columns").EnumerateArray()
            .Select(c => c.GetString()).ToList();
        var activeRow = dw.TryGetProperty("ActiveRow", out var a) ? a.GetInt32() : 0;
        var row = dw.GetProperty("Data")[activeRow];
        orderNo = row[columns.IndexOf("order_no")].ToString();
        Console.WriteLine($"Created order_no: {orderNo}");
    }
}
finally
{
    // 9. Clean up (window uses ?id=; sessions endpoint takes no parameter)
    await client.DeleteAsync($"{iapi}/v2/window?id={windowId}");
    await client.DeleteAsync($"{iapi}/sessions");
}

// 10. Verify via OData (mirrors the Verify section): assembly codes on the
//     lines, and the production-order link for the assembly line.
foreach (var line in await ODataAsync(client, "oe_line", $"order_no eq '{orderNo}'"))
{
    // assembly: B = kit parent, N = component, P = production-order line,
    // S = build-to-stock allocation
    var assembly = line.GetProperty("assembly").GetString();
    Console.WriteLine($"Line {line.GetProperty("line_no")}: assembly={assembly}");
    if (assembly != "P") continue;
    var links = await ODataAsync(client, "prod_order_line_link",
        $"transaction_uid eq {line.GetProperty("oe_line_uid")} and trans_type eq 'O'");
    Console.WriteLine($"  prod_order_line_link: {(links.Count > 0 ? "present" : "MISSING")}");
}

// --- helpers ---------------------------------------------------------------

static async Task SwitchTabAsync(HttpClient client, string iapi, string windowId, string page)
{
    var body = JsonSerializer.Serialize(new { WindowId = windowId, PageName = page });
    using var resp = await client.PutAsync($"{iapi}/v2/tab",
        new StringContent(body, Encoding.UTF8, "application/json"));
    resp.EnsureSuccessStatusCode();
}

static async Task<List<JsonElement>> ODataAsync(HttpClient client, string table, string filter)
{
    using var response = await client.GetAsync(
        $"{BaseUrl}/odataservice/odata/table/{table}?$filter=" + Uri.EscapeDataString(filter));
    response.EnsureSuccessStatusCode();
    using var doc = JsonDocument.Parse(await response.Content.ReadAsStringAsync());
    return doc.RootElement.GetProperty("value").EnumerateArray()
        .Select(x => x.Clone()).ToList();
}

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

> **End-to-end files** (runnable from the repo with a `.env`, dry-run by default): [`examples/python/recipes/order_with_assembly.py`](../../examples/python/recipes/order_with_assembly.py) · [`examples/csharp/Recipes/OrderWithAssembly.cs`](../../examples/csharp/Recipes/OrderWithAssembly.cs). The snippet above is self-contained; the files use the repo's shared `common` / `P21Examples.Common` helpers like every other example.

## Gotchas

All verified end-to-end — details in [Sales Order Entry with Assembly Lines](../04-Interactive-API.md#sales-order-entry-with-assembly-lines) and [Response Windows](../04-Interactive-API.md#response-windows):

- **Do NOT use the quickmode datawindow** (`d_dw_quickmode_*`) to enter lines — it **bypasses the assembly prompt entirely**, and the line lands without the explode.
- **`taker` defaults to the API user** — override it with the real salesperson or the order is attributed to the service account.
- **The date-cascade prompt fires even on a brand-new order** (`w_response_common`, `cb_ok`/`cb_cancel`). Answer `cb_ok` via the **popup's** window ID, not the Order window's.
- **Set the first line on the existing `items` row** — do not `POST /v2/row` a new row for it.
- **Assembly prompt buttons are `cb_1` = Yes / `cb_2` = No / `cb_3` = Cancel** — `cb_1` explodes the assembly / links the production order. This is exactly the prompt the Transaction API auto-answers No, which is why that API can't do this job.
- **Save body shape**: `PUT /v2/data` takes the bare window-ID string as the JSON body — wrapping it in an object is a common source of 422 errors.
- **`?id=` vs `?windowId=`**: `/v2/window` and `/v2/data` take `?id=`, but `/v2/tools` takes `?windowId=` — the wrong one errors, there is no fallback.
- **Status may be an integer or a string** (`3` or `"Blocked"`, from the `ResultStatus` enum `None=0, Success=1, Failure=2, Blocked=3`) — handle both.
- **`DatawindowName` is required in v2 change requests on P21 25.2+** — the 3-parameter form (TabName + FieldName + Value) no longer works.

## Verify

On the saved order, `oe_line.assembly` codes: `B` = kit parent, `N` = component, `P` = production-order line, `S` = build-to-stock allocation. The production-order link is `prod_order_line_link` (`transaction_uid = oe_line.oe_line_uid`, `trans_type = 'O'`):

```http
GET {base_url}/odataservice/odata/table/oe_line?$filter=order_no eq '1013938'
GET {base_url}/odataservice/odata/table/prod_order_line_link?$filter=trans_type eq 'O'
```

Confirm the assembly line shows the expected `assembly` code (e.g. `P`) and — for `auto_create_prod_order = 'Y'` items — that a `prod_order_line_link` row points at the line's `oe_line_uid`. See the [Production & Labor API guide](../12-Production-Labor-API.md) for the full production lifecycle.

> **Credit:** [Alex Westemeier](https://github.com/AWestemeier)
