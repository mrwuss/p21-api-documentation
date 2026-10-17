# Link an Existing Production Order to a Sales-Order Line

Attach a production order that already exists (built to stock, or entered before the sale) to an open sales-order line for the same assembly, through the Production Order window's **Transactions To Assign** tab.

**API:** Interactive (`ProductionOrder` window) + OData read-back · **Service:** `ProductionOrder` · **Deep dive:** [12 § Production Order Gotchas](../12-Production-Labor-API.md#production-order-gotchas-field-verified) · **Full schema:** [ProductionOrder.json](../../definitions/ProductionOrder.json)

## Prerequisites

- P21 credentials — the complete example below authenticates itself; nothing to install but `httpx` (Python) or a bare `net8.0`-or-later console project (C#).
- A user whose role can open and save the `ProductionOrder` window.
- An **open production order** for the assembly, with quantity left to assign.
- A **sales-order line for the same assembly that is already a production-order assembly line**: `oe_line.assembly = 'P'` and `disposition = 'P'`. Entering the assembly item in the Interactive `Order` window and answering the "add as assembly?" prompt with `cb_1` produces this ([order-with-assembly](order-with-assembly.md)). On the verified tenant the save did not create a production order by itself, so the line stayed unlinked.

> **The Transaction API cannot do this, and the obvious control is a decoy.** The tab's `retrieve_open_transactions` column is a constant (`'Y'`) in the tab's `SELECT` and is disabled for every role, so no write to it fills the grid. A Transaction row keyed `trans_number` + `customer_id` fails *"Object reference not set"*. The real control is the grid's **right-click tool**, `m_retrieveotheropentransactions` ("Retrieve Other Open Transactions").

## Call sequence

| Step | Call | Body |
|---|---|---|
| 1 | `POST {ui}/api/ui/interactive/sessions` | `{"ResponseWindowHandlingEnabled": true}` |
| 2 | `POST {ui}/api/ui/interactive/v2/window` | `{"ServiceName": "ProductionOrder"}` |
| 3 | `PUT {ui}/api/ui/interactive/v2/change` | `prod_order_number` on `TABPAGE_1` / `tp_1_dw_1` |
| 4 | `PUT {ui}/api/ui/interactive/v2/tab` | `{"WindowId": "{windowId}", "PageName": "TABPAGE_TRANSACTIONS_TO_ASSIGN"}` |
| 5 | `POST {ui}/api/ui/interactive/v2/tools` | `m_retrieveotheropentransactions` (below) |
| 6 | `GET {ui}/api/ui/interactive/v2/data?id={windowId}` | find the row: `cf_transaction_type` `Sales Order`, `trans_number`, `line_number` |
| 7 | `PUT {ui}/api/ui/interactive/v2/row` | `{"WindowId": "{windowId}", "DatawindowName": "tabpage_transactions_to_assign", "Row": n}` (1-based) |
| 8 | `PUT {ui}/api/ui/interactive/v2/change` | `assigned` = `ON` on `TABPAGE_TRANSACTIONS_TO_ASSIGN` / `tabpage_transactions_to_assign` |
| 9 | `PUT {ui}/api/ui/interactive/v2/data` | `"{windowId}"` (save — the body is the bare window id) |
| 10 | `DELETE` the window and the session | — |

The retrieve tool (step 5):

```http
POST {ui}/api/ui/interactive/v2/tools
{"WindowId": "{windowId}", "ToolName": "m_retrieveotheropentransactions",
 "DatawindowName": "tabpage_transactions_to_assign", "FieldName": null, "Row": 0, "Text": null}
```

It returns `Status: 1` with one `dwcontentchanged` event and no popup. The grid then holds one row per open, unassigned demand line for the item:

```jsonc
{"assigned": "N", "cf_transaction_type": "Sales Order", "trans_number": "1001234",
 "line_number": "1", "customer_id": "100198", "qty_remaining": "1.000000000", "qty_to_assign": "0"}
```

Ticking `assigned` (step 8) fills `qty_to_assign` with the line's remaining quantity. The save raised no prompt and returned a `savesucceeded` event carrying `__prod_order_number`.

**Finding the tool.** It is not in the window-level list. Ask for the datawindow's own tools: `GET {ui}/api/ui/interactive/v2/tools?windowId={windowId}&dwName=tabpage_transactions_to_assign` lists `m_retrieveotheropentransactions` and `m_reset` among the right-click options. The tab's `SELECT` (from `m_sqlinformation`, see [window-sql-information](window-sql-information.md)) reads only existing `prod_order_line_link` rows, which is why switching to the tab alone shows nothing to assign.

## What the save writes

One `prod_order_line_link` row. Nothing on `oe_line` changes — `assembly` and `disposition` stay `P`.

| Column | Value |
|---|---|
| `prod_order_number`, `prod_order_line_number` | the production order and its assembly line |
| `trans_type` | `O` (sales order) |
| `transaction_uid` | the sales line's `oe_line.oe_line_uid` |
| `quantity` | the assigned quantity |
| `row_status_flag` | `O` |

## Complete example

Link a production order to a sales-order line. The three record numbers are arguments (`python link_production_order.py 1000123 1001234 1`); without `--save` the program retrieves the open transactions and ticks the row but writes nothing. After a save it reads the link back from OData and compares its `transaction_uid` with the sales line's `oe_line_uid`.

<!-- tabs -->
```python
"""Link an existing production order to an open sales-order line (Interactive API).

The Production Order window's Transactions To Assign tab fills through the
datawindow's right-click tool m_retrieveotheropentransactions. Tick `assigned`
on the sales-order row and save: P21 writes one prod_order_line_link row.

    python link_production_order.py [PROD_ORDER ORDER_NO LINE_NO] [--save]

Without --save it retrieves the open transactions and ticks the row, then stops
without saving (dry run).
"""
import re
import sys

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.example.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
PROD_ORDER = "1000123"                    # the existing, open production order
ORDER_NO = "1001234"                      # the sales order to link it to
LINE_NO = "1"                             # that order's production-order assembly line
SAVE = False                              # True writes the link; False is a dry run
# ---------------------------------------------------------------------------

TAB = "TABPAGE_TRANSACTIONS_TO_ASSIGN"
DW = "tabpage_transactions_to_assign"
SHOW = ("assigned", "cf_transaction_type", "trans_number", "line_number", "customer_id",
        "qty_remaining", "qty_to_assign")


def get_token(client: httpx.Client) -> str:
    """v2 token endpoint -- credentials go in the body, never in headers."""
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


def checked(r: httpx.Response, what: str) -> dict:
    """The answer, refusing HTTP errors, Status 2 (failure) and Status 3 (a prompt)."""
    if r.status_code >= 400:
        raise RuntimeError(f"{what}: HTTP {r.status_code} {r.text[:300]}")
    body = r.json() if r.content else {}
    if isinstance(body, dict) and body.get("Status") in (2, 3):
        raise RuntimeError(f"{what}: Status {body['Status']}: {body.get('Messages')}")
    return body if isinstance(body, dict) else {}


def rows_of(client: httpx.Client, iapi: str, window_id: str, dw_name: str) -> list[dict]:
    """The rows of one datawindow on the window's active surface, as column -> value dicts."""
    r = client.get(f"{iapi}/v2/data", params={"id": window_id})
    r.raise_for_status()
    for dw in r.json():
        if dw.get("Name") == dw_name:
            return [dict(zip(dw["Columns"], row)) for row in dw.get("Data") or []]
    return []


def number(value: object) -> str:
    """Normalize a decimal string such as '1001234.0' to '1001234'."""
    return str(value).split(".")[0]


def odata(client: httpx.Client, table: str, where: str) -> list[dict]:
    """One OData table read."""
    r = client.get(f"{BASE_URL}/odataservice/odata/table/{table}", params={"$filter": where})
    r.raise_for_status()
    return r.json()["value"]


def main() -> None:
    """Retrieve the open transactions, tick the sales-order row, optionally save."""
    args = [a for a in sys.argv[1:] if a != "--save"]
    if args and len(args) != 3:
        sys.exit("Pass all three record numbers, or none to use the constants")
    prod_order, order_no, line_no = args if args else (PROD_ORDER, ORDER_NO, LINE_NO)
    save = SAVE or "--save" in sys.argv
    for value in (prod_order, order_no, line_no):
        if not value.isdigit():  # these go into an OData filter
            sys.exit(f"Not a number: {value}")

    with httpx.Client(verify=VERIFY_SSL, timeout=120, follow_redirects=True) as client:
        token = get_token(client)
        ui_server = get_ui_server(client, token)
        client.headers.update({"Authorization": f"Bearer {token}",
                               "Accept": "application/json",
                               "Content-Type": "application/json"})
        iapi = f"{ui_server}/api/ui/interactive"

        checked(client.post(f"{iapi}/sessions", json={"ResponseWindowHandlingEnabled": True}),
                "open session")
        window_id = ""
        try:
            opened = checked(client.post(f"{iapi}/v2/window", json={"ServiceName": "ProductionOrder"}),
                             "open ProductionOrder")
            window_id = opened["WindowId"]

            # 1. Load the production order, 2. switch to the Transactions To Assign tab.
            checked(client.put(f"{iapi}/v2/change", json={"WindowId": window_id, "List": [{
                "TabName": "TABPAGE_1", "DatawindowName": "tp_1_dw_1",
                "FieldName": "prod_order_number", "Value": prod_order}]}), "load production order")
            checked(client.put(f"{iapi}/v2/tab", json={"WindowId": window_id, "PageName": TAB}),
                    "select tab")

            # 3. The grid's right-click tool fills it with open, unassigned demand. The
            #    window-level tool list does not show it; ask for the datawindow's tools:
            #    GET /v2/tools?windowId=...&dwName=tabpage_transactions_to_assign
            checked(client.post(f"{iapi}/v2/tools", json={
                "WindowId": window_id, "ToolName": "m_retrieveotheropentransactions",
                "DatawindowName": DW, "FieldName": None, "Row": 0, "Text": None}), "retrieve")
            grid = rows_of(client, iapi, window_id, DW)
            for row in grid:
                print("  open:", {k: row.get(k) for k in SHOW})
            match = [i for i, row in enumerate(grid)
                     if row.get("cf_transaction_type") == "Sales Order"
                     and number(row.get("trans_number")) == order_no
                     and number(row.get("line_number")) == line_no]
            if not match:
                sys.exit("That sales-order line is not among the open transactions")

            # 4. Make it the current row (1-based), 5. tick `assigned`; P21 fills qty_to_assign.
            checked(client.put(f"{iapi}/v2/row", json={
                "WindowId": window_id, "DatawindowName": DW, "Row": match[0] + 1}), "select row")
            checked(client.put(f"{iapi}/v2/change", json={"WindowId": window_id, "List": [{
                "TabName": TAB, "DatawindowName": DW,
                "FieldName": "assigned", "Value": "ON"}]}), "tick assigned")
            ticked = rows_of(client, iapi, window_id, DW)[match[0]]
            print("  ticked:", {k: ticked.get(k) for k in SHOW})
            if not save:
                print("Dry run: not saved (set SAVE = True or pass --save)")
                return

            # 6. Save -- the body is the bare window id.
            checked(client.put(f"{iapi}/v2/data", json=window_id), "save")
            print("  saved")
        finally:
            if window_id:
                client.delete(f"{iapi}/v2/window", params={"id": window_id})
            client.delete(f"{iapi}/sessions")

        # Read back: one prod_order_line_link row whose transaction_uid is the sales line's uid.
        line = odata(client, "oe_line", f"order_no eq '{order_no}' and line_no eq {line_no}")[0]
        links = odata(client, "prod_order_line_link", f"prod_order_number eq {prod_order}")
        print("  oe_line:", {k: line.get(k) for k in ("oe_line_uid", "assembly", "disposition")})
        for link in links:
            print("  link:", {k: link.get(k) for k in (
                "prod_order_number", "prod_order_line_number", "trans_type", "quantity",
                "row_status_flag", "transaction_uid")})
        if not any(link.get("transaction_uid") == line["oe_line_uid"] for link in links):
            sys.exit("No prod_order_line_link row for that sales-order line")
        print("Linked.")


if __name__ == "__main__":
    main()
```

```csharp
// Link an existing production order to an open sales-order line (Interactive API).
// The Production Order window's Transactions To Assign tab fills through the datawindow's
// right-click tool m_retrieveotheropentransactions. Tick `assigned` on the sales-order
// row and save: P21 writes one prod_order_line_link row.
//
//   dotnet run -- [PROD_ORDER ORDER_NO LINE_NO] [--save]
//
// Without --save it retrieves the open transactions and ticks the row, then stops (dry run).
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.example.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
string prodOrder = "1000123";                        // the existing, open production order
string orderNo = "1001234";                          // the sales order to link it to
string lineNo = "1";                                 // that order's production-order assembly line
bool save = false;                                   // true writes the link; false is a dry run
// ---------------------------------------------------------------------------

const string Tab = "TABPAGE_TRANSACTIONS_TO_ASSIGN";
const string Dw = "tabpage_transactions_to_assign";

var positional = args.Where(a => a != "--save").ToArray();
if (positional.Length is not (0 or 3)) { Console.WriteLine("Pass all three record numbers, or none to use the constants"); return; }
if (positional.Length == 3) { prodOrder = positional[0]; orderNo = positional[1]; lineNo = positional[2]; }
if (args.Contains("--save")) save = true;
foreach (var value in new[] { prodOrder, orderNo, lineNo })
    if (value.Length == 0 || !value.All(char.IsAsciiDigit))   // these go into an OData filter
    { Console.WriteLine($"Not a number: {value}"); return; }

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

await SendAsync(HttpMethod.Post, $"{iapi}/sessions", new { ResponseWindowHandlingEnabled = true }, "open session");
var windowId = "";
try
{
    var opened = await SendAsync(HttpMethod.Post, $"{iapi}/v2/window", new { ServiceName = "ProductionOrder" }, "open ProductionOrder");
    windowId = opened.GetProperty("WindowId").GetString()!;

    // 1. Load the production order, 2. switch to the Transactions To Assign tab.
    await ChangeAsync(windowId, "TABPAGE_1", "tp_1_dw_1", "prod_order_number", prodOrder);
    await SendAsync(HttpMethod.Put, $"{iapi}/v2/tab", new { WindowId = windowId, PageName = Tab }, "select tab");

    // 3. The grid's right-click tool fills it with open, unassigned demand. The window-level
    //    tool list does not show it; ask for the datawindow's tools:
    //    GET /v2/tools?windowId=...&dwName=tabpage_transactions_to_assign
    await SendAsync(HttpMethod.Post, $"{iapi}/v2/tools", new
    {
        WindowId = windowId, ToolName = "m_retrieveotheropentransactions",
        DatawindowName = Dw, FieldName = (string?)null, Row = 0, Text = (string?)null,
    }, "retrieve");
    var grid = await RowsAsync(windowId, Dw);
    var match = -1;
    for (var i = 0; i < grid.Count; i++)
    {
        var row = grid[i];
        Console.WriteLine($"  open: {Cell(row, "cf_transaction_type")} {Cell(row, "trans_number")}" +
            $" line {Cell(row, "line_number")} assigned={Cell(row, "assigned")} remaining={Cell(row, "qty_remaining")}");
        if (Cell(row, "cf_transaction_type") == "Sales Order"
            && Number(Cell(row, "trans_number")) == orderNo
            && Number(Cell(row, "line_number")) == lineNo)
            match = i;
    }
    if (match < 0) { Console.WriteLine("That sales-order line is not among the open transactions"); return; }

    // 4. Make it the current row (1-based), 5. tick `assigned`; P21 fills qty_to_assign.
    await SendAsync(HttpMethod.Put, $"{iapi}/v2/row", new { WindowId = windowId, DatawindowName = Dw, Row = match + 1 }, "select row");
    await ChangeAsync(windowId, Tab, Dw, "assigned", "ON");
    var ticked = (await RowsAsync(windowId, Dw))[match];
    Console.WriteLine($"  ticked: assigned={Cell(ticked, "assigned")} qty_to_assign={Cell(ticked, "qty_to_assign")}");
    if (!save) { Console.WriteLine("Dry run: not saved (set save = true or pass --save)"); return; }

    // 6. Save -- the body is the bare window id.
    await SendAsync(HttpMethod.Put, $"{iapi}/v2/data", windowId, "save");
    Console.WriteLine("  saved");
}
finally
{
    if (windowId.Length > 0) await client.DeleteAsync($"{iapi}/v2/window?id={windowId}");
    await client.DeleteAsync($"{iapi}/sessions");
}

// Read back: one prod_order_line_link row whose transaction_uid is the sales line's uid.
var lines = await ODataAsync("oe_line", $"order_no eq '{orderNo}' and line_no eq {lineNo}");
var links = await ODataAsync("prod_order_line_link", $"prod_order_number eq {prodOrder}");
var lineUid = lines[0].GetProperty("oe_line_uid").GetDecimal();
Console.WriteLine($"  oe_line: uid {lineUid:0} assembly={lines[0].GetProperty("assembly")} disposition={lines[0].GetProperty("disposition")}");
foreach (var link in links)
    Console.WriteLine($"  link: order {link.GetProperty("prod_order_number")} line {link.GetProperty("prod_order_line_number")}" +
        $" trans_type={link.GetProperty("trans_type")} quantity={link.GetProperty("quantity")}" +
        $" row_status_flag={link.GetProperty("row_status_flag")} transaction_uid={link.GetProperty("transaction_uid")}");
if (!links.Any(l => l.GetProperty("transaction_uid").GetDecimal() == lineUid))
{ Console.WriteLine("No prod_order_line_link row for that sales-order line"); return; }
Console.WriteLine("Linked.");

// --- helpers ---------------------------------------------------------------

// One Interactive call; refuses HTTP errors, Status 2 (failure) and Status 3 (a prompt).
async Task<JsonElement> SendAsync(HttpMethod method, string url, object body, string what)
{
    using var request = new HttpRequestMessage(method, url)
    {
        Content = new StringContent(JsonSerializer.Serialize(body), Encoding.UTF8, "application/json"),
    };
    var response = await client.SendAsync(request);
    var text = await response.Content.ReadAsStringAsync();
    if ((int)response.StatusCode >= 400)
        throw new InvalidOperationException($"{what}: HTTP {(int)response.StatusCode} {text[..Math.Min(300, text.Length)]}");
    var answer = text.Length == 0 ? JsonDocument.Parse("{}").RootElement : JsonDocument.Parse(text).RootElement.Clone();
    if (answer.ValueKind == JsonValueKind.Object && answer.TryGetProperty("Status", out var status)
        && status.ValueKind == JsonValueKind.Number && status.GetInt32() is 2 or 3)
        throw new InvalidOperationException($"{what}: Status {status}: {answer.GetProperty("Messages")}");
    return answer;
}

Task<JsonElement> ChangeAsync(string window, string tab, string dw, string field, string value) =>
    SendAsync(HttpMethod.Put, $"{iapi}/v2/change", new
    {
        WindowId = window,
        List = new[] { new { TabName = tab, DatawindowName = dw, FieldName = field, Value = value } },
    }, $"change {field}");

// The rows of one datawindow on the active surface, as column -> value maps.
async Task<List<Dictionary<string, string>>> RowsAsync(string window, string dwName)
{
    var json = await client.GetStringAsync($"{iapi}/v2/data?id={window}");
    var rows = new List<Dictionary<string, string>>();
    foreach (var dw in JsonDocument.Parse(json).RootElement.EnumerateArray())
    {
        if (dw.GetProperty("Name").GetString() != dwName) continue;
        var columns = dw.GetProperty("Columns").EnumerateArray().Select(c => c.GetString()!).ToList();
        if (!dw.TryGetProperty("Data", out var data) || data.ValueKind != JsonValueKind.Array) continue;
        foreach (var row in data.EnumerateArray())
        {
            var map = new Dictionary<string, string>();
            var cells = row.EnumerateArray().ToList();
            for (var i = 0; i < columns.Count && i < cells.Count; i++)
                map[columns[i]] = cells[i].ValueKind == JsonValueKind.Null ? "" : cells[i].ToString();
            rows.Add(map);
        }
    }
    return rows;
}

static string Cell(Dictionary<string, string> row, string column) => row.TryGetValue(column, out var v) ? v : "";

// Normalize a decimal string such as "1001234.0" to "1001234".
static string Number(string value) => value.Split('.')[0];

// One OData table read.
async Task<List<JsonElement>> ODataAsync(string table, string filter)
{
    var url = $"{BaseUrl}/odataservice/odata/table/{table}?$filter={Uri.EscapeDataString(filter)}";
    var response = await client.GetAsync(url);
    response.EnsureSuccessStatusCode();
    return JsonDocument.Parse(await response.Content.ReadAsStringAsync())
        .RootElement.GetProperty("value").EnumerateArray().Select(e => e.Clone()).ToList();
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

## Gotchas (verified on play 26.1.5950.0, 2026-10-17)

- **Only open demand for the order's item appears.** The retrieve fills the grid with the open demand lines for the production order's item; a line already linked to this order shows `assigned = Y`, so a second run finds the row already ticked. A line that is not in the grid cannot be ticked; the program stops with "not among the open transactions" and writes nothing.
- **A plain sales line cannot be switched afterwards.** A line entered with `assembly = 'N'` cannot be changed to disposition `P` later. Enter it as a production-order assembly line first.
- **A user-defined field can block a production-order save.** On the verified tenant a header UD field was required when *creating* the production order (the save is refused until it is set). Loading an existing order and linking it saved without touching that field. If your tenant refuses the save, set the required field on the header first ([production-order-runbook](production-order-runbook.md)).
- **Save, not tick, writes.** Closing the window after ticking `assigned` writes nothing.
- **The window row index is 1-based.** `PUT /v2/row` takes the position in the grid as listed; the program adds one to its 0-based list index.

## Verify

```text
GET /odataservice/odata/table/prod_order_line_link?$filter=prod_order_number eq 1000123
```

Expect one row with `trans_type` `O`, `row_status_flag` `O`, and `transaction_uid` equal to the sales line's `oe_line_uid`. The example prints it and exits with an error if the link is missing.
