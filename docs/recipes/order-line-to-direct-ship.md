# Change a Saved Order Line to Direct Ship

Turn a line on an order that is already saved into a direct-ship line (`disposition = D`), and optionally create its direct-ship purchase order in the same save.

**API:** Interactive (`Order` window, Create PO wizard) + OData read-back; the Transaction API changes the disposition but cannot create the PO · **Service:** `Order` · **Deep dive:** [04 § Changing a saved line to direct ship](../04-Interactive-API.md#changing-a-saved-line-to-direct-ship) · **Full schema:** [Order.json](../../definitions/Order.json)

## Prerequisites

- P21 credentials — the complete example below authenticates itself; nothing to install but `httpx` (Python) or a bare `net8.0`-or-later console project (C#).
- A saved order whose line is not yet on a pick ticket.
- To create the PO (`--create-po`): a P21 user **with a Buyer ID**. A user without one is refused on `c_create_po` with *"To create a PO, you must have a valid Buyer ID."*

## The rule: allocation is the gate

`disposition` on a saved line is not locked because the line is saved, or because of the user. It is locked while the line **holds allocated stock**.

| Line state | Result |
|---|---|
| Saved, nothing allocated (`disposition = 'B'`) | `disposition = D` saves |
| Saved, allocated (`qty_allocated > 0`, `disposition` blank) | `Column is disabled: disposition`, for every user |
| Saved, allocated, `TP_EXTDINFO.extd_info.allocated_qty` set to `0` first | `disposition = D` saves, and `qty_allocated` is `0` |

- **Send the code value `D`.** The display text `Direct Ship` is refused with `Invalid disposition value: Direct Ship`.
- **Releasing the allocation resets `disposition` to `B`** and enables the column in the same response, so edit in this order: allocation, `disposition`, `po_cost`.
- **Set `po_cost`** when you want the PO line priced. A line with no cost raises *"The order line does not have a PO Cost specified. Proceed?"*; the example answers it Yes (`cb_1`).

## Call sequence

The full step table, with the bodies, is in [04 § Changing a saved line to direct ship](../04-Interactive-API.md#changing-a-saved-line-to-direct-ship). In short: open the `Order` window, set `quote` = `OFF`, load the order, select the line in the `items` grid by `user_line_no` (the grid has no `line_no` column), release the allocation if there is one, change `disposition` to `D`, optionally set `po_cost` and `c_create_po`, and save. With `c_create_po` on, the save opens the **Create RFQ/Purchase Orders** wizard: `cb_next` **commits the PO**, `cb_finish` closes the wizard.

## Complete example

Convert one line. The order and line number are arguments (`python order_line_to_direct_ship.py 1001234 1 --execute --create-po --po-cost 8`). Without `--execute` the program makes the changes in the window and stops without saving. After a save it reads the line, the `oe_line_po` link and the `po_hdr` back from OData.

<!-- tabs -->
```python
"""Change a SAVED sales-order line to Direct Ship (disposition D), optionally creating its PO.

Re-open the order in the Order window, make the line the active row of the `items`
grid and change `disposition` to the CODE value "D" ("Direct Ship" is refused).
`disposition` is disabled while the line holds allocated stock ("Column is disabled:
disposition"), so an allocated line is released first with
TP_EXTDINFO.extd_info.allocated_qty = 0.

    python order_line_to_direct_ship.py [ORDER_NO LINE_NO] [--execute] [--create-po] [--po-cost 8]

Without --execute it makes the changes in the window and stops (dry run). --create-po
also ticks the header's c_create_po, so the save opens the "Create RFQ/Purchase Orders"
wizard; the program drives it (cb_next commits the PO, cb_finish closes it). That step
needs a P21 user with a Buyer ID.
"""
import re
import sys

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.example.com"   # your P21 server
USERNAME = "apiuser"                      # for --create-po: a P21 user with a Buyer ID
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
ORDER_NO = "1001234"                      # the saved order
LINE_NO = "1"                             # the line to convert (the window's line number)
EXECUTE = False                           # True saves; False is a dry run
CREATE_PO = False                         # True also creates the direct-ship PO in the same save
PO_COST = ""                              # e.g. "8" -- the line's PO cost (flows to the PO line price)
# ---------------------------------------------------------------------------

BLOCKED = 3  # ResultStatus: a prompt or wizard is waiting for an answer
ORDER_COLUMNS = "order_no,line_no,disposition,po_cost,qty_ordered,qty_allocated,qty_on_pick_tickets"


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


class Session:
    """The few Interactive v2 calls this task needs."""

    def __init__(self, client: httpx.Client, ui_server: str) -> None:
        self.http = client
        self.base = f"{ui_server}/api/ui/interactive"

    def call(self, method: str, path: str, what: str, **kwargs) -> dict | list:
        """One call; refuses HTTP errors and Status 2 (failure). Status 3 is returned."""
        r = self.http.request(method, f"{self.base}{path}", **kwargs)
        if r.status_code >= 400:
            raise RuntimeError(f"{what}: HTTP {r.status_code} {r.text[:300]}")
        body = r.json() if r.content else {}
        if isinstance(body, dict) and body.get("Status") == 2:
            raise RuntimeError(f"{what}: refused: {body.get('Messages')}")
        return body

    def change(self, window: str, tab: str, dw: str, field: str, value: str) -> dict:
        """Change one field on the active row of a datawindow."""
        return self.call("PUT", "/v2/change", f"change {field}", json={
            "WindowId": window,
            "List": [{"TabName": tab, "DatawindowName": dw, "FieldName": field, "Value": value}]})

    def tab(self, window: str, page: str) -> dict:
        return self.call("PUT", "/v2/tab", f"tab {page}", json={"WindowId": window, "PageName": page})

    def row(self, window: str, dw: str, number: int) -> dict:
        """Make a row (1-based) the active row; changes land on it."""
        return self.call("PUT", "/v2/row", f"row {number}",
                         json={"WindowId": window, "DatawindowName": dw, "Row": number})

    def datawindows(self, window: str) -> list[dict]:
        return self.call("GET", "/v2/data", "data", params={"id": window})  # type: ignore[return-value]

    def rows(self, window: str, dw: str) -> list[dict]:
        """All rows of one datawindow as column -> value dicts."""
        for found in self.datawindows(window):
            if found.get("Name") == dw:
                return [dict(zip(found["Columns"], row)) for row in found.get("Data") or []]
        return []

    def active_row(self, window: str, dw: str) -> dict:
        """The active row of one datawindow (ActiveRow is 1-based)."""
        for found in self.datawindows(window):
            if found.get("Name") == dw and found.get("Data"):
                return dict(zip(found["Columns"], found["Data"][max((found.get("ActiveRow") or 1) - 1, 0)]))
        return {}

    def tools(self, window: str) -> list[str]:
        found = self.call("GET", "/v2/tools", "tools", params={"windowId": window})
        return [t.get("ToolName") for t in found]  # type: ignore[union-attr]

    def press(self, window: str, tool: str) -> dict:
        return self.call("POST", "/v2/tools", f"tool {tool}", json={"WindowId": window, "ToolName": tool})

    def window_class(self, window: str) -> str:
        found = self.call("GET", "/v2/window", "window", params={"id": window})
        return ((found or {}).get("Definition") or {}).get("Name") or ""  # type: ignore[union-attr]

    def popups(self, result: dict) -> list[str]:
        """Window ids of the response windows the last call opened (windowopened events)."""
        return [kv["Value"] for event in result.get("Events") or []
                if event.get("Name") == "windowopened"
                for kv in event.get("Data") or [] if kv.get("Key") == "windowid"]


def answer(session: Session, result: dict) -> str | None:
    """Answer whatever a change or save opened; return the PO number if the wizard ran.

    A "no PO Cost" or profit prompt (w_message) is answered Yes (cb_1). The Create PO
    wizard is recognised by its cb_finish button: cb_next COMMITS the PO, cb_finish closes it.
    """
    po_no = None
    while result.get("Status") == BLOCKED:
        popup = session.popups(result)[0]
        tools = session.tools(popup)  # includes the parent's ribbon -- look for names
        if "cb_finish" in tools:
            for row in session.rows(popup, "items"):
                print(f"  wizard: item={row.get('item_id')} supplier={row.get('supplier_id')} "
                      f"qty={row.get('qty_to_purchase')}")
            session.press(popup, "cb_next")  # the PO is committed here
            po_no = session.active_row(popup, "po_print").get("po_no")
            print(f"  wizard page 2: po_no={po_no}")
            result = session.press(popup, "cb_finish")
        elif session.window_class(popup) == "w_message" and "cb_1" in tools:
            print("  prompt answered Yes (cb_1)")
            result = session.press(popup, "cb_1")
        else:
            raise RuntimeError(f"Unexpected response window: {tools}")
    return po_no


def odata(client: httpx.Client, table: str, where: str, select: str = "") -> list[dict]:
    """One OData table read."""
    params = {"$filter": where}
    if select:
        params["$select"] = select
    r = client.get(f"{BASE_URL}/odataservice/odata/table/{table}", params=params)
    r.raise_for_status()
    return r.json()["value"]


def read_back(client: httpx.Client, order_no: str, line_no: str) -> dict:
    """Print the line and any PO linked to it; return the line."""
    line = odata(client, "oe_line", f"order_no eq '{order_no}' and line_no eq {line_no}", ORDER_COLUMNS)[0]
    print("  oe_line:", line)
    for link in odata(client, "oe_line_po", f"order_number eq '{order_no}' and line_number eq {line_no}"):
        po = odata(client, "po_hdr", f"po_no eq {int(link['po_no'])}", "po_no,po_type,supplier_id,approved")[0]
        print(f"  oe_line_po: po_no={int(link['po_no'])} connection_type={link['connection_type']} -> po_hdr {po}")
    return line


def main() -> None:
    """Convert the line, optionally create its PO, and read the result back."""
    args, po_cost = [], PO_COST
    rest = iter(sys.argv[1:])
    for arg in rest:
        if arg == "--po-cost":
            po_cost = next(rest, "")
            if not po_cost:
                sys.exit("--po-cost needs a value")
        elif not arg.startswith("--"):
            args.append(arg)
    if args and len(args) != 2:
        sys.exit("Pass both the order number and the line number, or neither to use the constants")
    order_no, line_no = args if args else (ORDER_NO, LINE_NO)
    execute = EXECUTE or "--execute" in sys.argv
    create_po = CREATE_PO or "--create-po" in sys.argv
    if not (order_no.isdigit() and line_no.isdigit()):  # these go into an OData filter
        sys.exit("The order and line numbers must be digits")

    with httpx.Client(verify=VERIFY_SSL, timeout=180, follow_redirects=True) as client:
        token = get_token(client)
        ui_server = get_ui_server(client, token)
        client.headers.update({"Authorization": f"Bearer {token}", "Accept": "application/json",
                               "Content-Type": "application/json"})
        print("Before:")
        before = read_back(client, order_no, line_no)
        if float(before.get("qty_on_pick_tickets") or 0) > 0:
            sys.exit("The line is on a pick ticket -- reverse the pick ticket first")

        session = Session(client, ui_server)
        session.call("POST", "/sessions/", "start session", json={"ResponseWindowHandlingEnabled": True})
        window, po_no = "", None
        try:
            window = session.call("POST", "/v2/window", "open Order", json={"ServiceName": "Order"})["WindowId"]
            session.change(window, "TABPAGE_1", "order", "quote", "OFF")
            session.change(window, "TABPAGE_1", "order", "order_no", order_no)
            session.tab(window, "TP_ITEMS")
            # The grid has no line_no column; the window's line number is user_line_no.
            grid = session.rows(window, "items")
            found = [i for i, r in enumerate(grid) if int(float(r.get("user_line_no") or 0)) == int(line_no)]
            if not found:
                sys.exit(f"Line {line_no} is not in the items grid")
            session.row(window, "items", found[0] + 1)
            if float(before.get("qty_allocated") or 0) > 0:
                # Allocated stock locks `disposition`; releasing it resets disposition to B and
                # enables the column.
                session.tab(window, "TP_EXTDINFO")
                answer(session, session.change(window, "TP_EXTDINFO", "extd_info", "allocated_qty", "0"))
                print("  released allocation:", session.active_row(window, "extd_info").get("allocated_qty"))
                session.tab(window, "TP_ITEMS")
            answer(session, session.change(window, "TP_ITEMS", "items", "disposition", "D"))
            if po_cost:
                answer(session, session.change(window, "TP_ITEMS", "items", "po_cost", po_cost))
            line = session.rows(window, "items")[found[0]]
            print(f"  in window: disposition={line.get('disposition')} po_cost={line.get('po_cost')}")
            if create_po:
                session.tab(window, "TABPAGE_1")
                answer(session, session.change(window, "TABPAGE_1", "order", "c_create_po", "ON"))
            if not execute:
                print("Dry run: not saved (set EXECUTE = True or pass --execute)")
                return
            po_no = answer(session, session.call("PUT", "/v2/data", "save", json=window))
            print("  saved")
        finally:
            if window:
                client.delete(f"{session.base}/v2/window", params={"id": window})
            client.delete(f"{session.base}/sessions/")

        print("After:")
        after = read_back(client, order_no, line_no)
        if after["disposition"] != "D":
            sys.exit("disposition did not stick")
        if create_po and not po_no:
            sys.exit("The wizard did not run -- no PO (does the user have a Buyer ID?)")
        print("OK")


if __name__ == "__main__":
    main()
```

```csharp
// Change a SAVED sales-order line to Direct Ship (disposition D), optionally creating its PO.
// Re-open the order in the Order window, make the line the active row of the `items` grid and
// change `disposition` to the CODE value "D" ("Direct Ship" is refused). `disposition` is
// disabled while the line holds allocated stock ("Column is disabled: disposition"), so an
// allocated line is released first with TP_EXTDINFO.extd_info.allocated_qty = 0.
//
//   dotnet run -- [ORDER_NO LINE_NO] [--execute] [--create-po] [--po-cost 8]
//
// Without --execute it makes the changes in the window and stops (dry run). --create-po also
// ticks the header's c_create_po, so the save opens the "Create RFQ/Purchase Orders" wizard;
// the program drives it (cb_next commits the PO, cb_finish closes it). That step needs a P21
// user with a Buyer ID.
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.example.com";   // your P21 server
const string Username = "apiuser";                   // for --create-po: a P21 user with a Buyer ID
const string Password = "your-password";
string orderNo = "1001234";                          // the saved order
string lineNo = "1";                                 // the line to convert (the window's line number)
bool execute = false;                                // true saves; false is a dry run
bool createPo = false;                               // true also creates the direct-ship PO in the same save
string poCost = "";                                  // e.g. "8" -- the line's PO cost (flows to the PO line price)
// ---------------------------------------------------------------------------

const int Blocked = 3;                               // ResultStatus: a prompt or wizard is waiting
const string OrderColumns = "order_no,line_no,disposition,po_cost,qty_ordered,qty_allocated,qty_on_pick_tickets";

var rest = new List<string>();
for (var i = 0; i < args.Length; i++)
{
    if (args[i] == "--execute") execute = true;
    else if (args[i] == "--create-po") createPo = true;
    else if (args[i] == "--po-cost" && i + 1 < args.Length) poCost = args[++i];
    else rest.Add(args[i]);
}
if (rest.Count is not (0 or 2)) { Console.WriteLine("Pass both the order number and the line number, or neither to use the constants"); return; }
if (rest.Count == 2) { orderNo = rest[0]; lineNo = rest[1]; }
if (orderNo.Length == 0 || lineNo.Length == 0 || !orderNo.All(char.IsAsciiDigit) || !lineNo.All(char.IsAsciiDigit))
{ Console.WriteLine("The order and line numbers must be digits"); return; }   // they go into an OData filter

var handler = new HttpClientHandler
{
    // Test tenants often present a self-signed cert. Delete this line in production.
    ServerCertificateCustomValidationCallback =
        HttpClientHandler.DangerousAcceptAnyServerCertificateValidator,
};
using var client = new HttpClient(handler) { Timeout = TimeSpan.FromMinutes(3) };
client.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));

var token = await GetTokenAsync(client);
var uiServer = await GetUiServerAsync(client, token);
client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);
var iapi = $"{uiServer}/api/ui/interactive";

Console.WriteLine("Before:");
var before = await ReadBackAsync();
if (Num(before, "qty_on_pick_tickets") > 0) { Console.WriteLine("The line is on a pick ticket -- reverse the pick ticket first"); return; }

await CallAsync(HttpMethod.Post, "/sessions/", "start session", new { ResponseWindowHandlingEnabled = true });
var window = "";
string? poNo = null;
try
{
    window = (await CallAsync(HttpMethod.Post, "/v2/window", "open Order", new { ServiceName = "Order" })).GetProperty("WindowId").GetString()!;
    await ChangeAsync(window, "TABPAGE_1", "order", "quote", "OFF");
    await ChangeAsync(window, "TABPAGE_1", "order", "order_no", orderNo);
    await TabAsync(window, "TP_ITEMS");

    // The grid has no line_no column; the window's line number is user_line_no.
    var grid = await RowsAsync(window, "items");
    var found = grid.FindIndex(r => int.TryParse(Cell(r, "user_line_no").Split('.')[0], out var n) && n == int.Parse(lineNo));
    if (found < 0) { Console.WriteLine($"Line {lineNo} is not in the items grid"); return; }
    await CallAsync(HttpMethod.Put, "/v2/row", "select row", new { WindowId = window, DatawindowName = "items", Row = found + 1 });

    if (Num(before, "qty_allocated") > 0)
    {
        // Allocated stock locks `disposition`; releasing it resets disposition to B and enables the column.
        await TabAsync(window, "TP_EXTDINFO");
        await AnswerAsync(await ChangeAsync(window, "TP_EXTDINFO", "extd_info", "allocated_qty", "0"));
        Console.WriteLine($"  released allocation: {Cell((await ActiveRowAsync(window, "extd_info")), "allocated_qty")}");
        await TabAsync(window, "TP_ITEMS");
    }
    await AnswerAsync(await ChangeAsync(window, "TP_ITEMS", "items", "disposition", "D"));
    if (poCost.Length > 0) await AnswerAsync(await ChangeAsync(window, "TP_ITEMS", "items", "po_cost", poCost));
    var line = (await RowsAsync(window, "items"))[found];
    Console.WriteLine($"  in window: disposition={Cell(line, "disposition")} po_cost={Cell(line, "po_cost")}");
    if (createPo)
    {
        await TabAsync(window, "TABPAGE_1");
        await AnswerAsync(await ChangeAsync(window, "TABPAGE_1", "order", "c_create_po", "ON"));
    }
    if (!execute) { Console.WriteLine("Dry run: not saved (set execute = true or pass --execute)"); return; }
    poNo = await AnswerAsync(await CallAsync(HttpMethod.Put, "/v2/data", "save", window));
    Console.WriteLine("  saved");
}
finally
{
    if (window.Length > 0) await client.DeleteAsync($"{iapi}/v2/window?id={window}");
    await client.DeleteAsync($"{iapi}/sessions/");
}

Console.WriteLine("After:");
var after = await ReadBackAsync();
if (Cell(after, "disposition") != "D") { Console.WriteLine("disposition did not stick"); return; }
if (createPo && poNo is null) { Console.WriteLine("The wizard did not run -- no PO (does the user have a Buyer ID?)"); return; }
Console.WriteLine("OK");

// --- helpers ---------------------------------------------------------------

// One Interactive call; refuses HTTP errors and Status 2 (failure). Status 3 is returned.
async Task<JsonElement> CallAsync(HttpMethod method, string path, string what, object? body = null)
{
    using var request = new HttpRequestMessage(method, $"{iapi}{path}");
    if (body is not null)
        request.Content = new StringContent(JsonSerializer.Serialize(body), Encoding.UTF8, "application/json");
    var response = await client.SendAsync(request);
    var text = await response.Content.ReadAsStringAsync();
    if ((int)response.StatusCode >= 400)
        throw new InvalidOperationException($"{what}: HTTP {(int)response.StatusCode} {text[..Math.Min(300, text.Length)]}");
    var answer = text.Length == 0 ? JsonDocument.Parse("{}").RootElement : JsonDocument.Parse(text).RootElement.Clone();
    if (answer.ValueKind == JsonValueKind.Object && answer.TryGetProperty("Status", out var s)
        && s.ValueKind == JsonValueKind.Number && s.GetInt32() == 2)
        throw new InvalidOperationException($"{what}: refused: {answer.GetProperty("Messages")}");
    return answer;
}

Task<JsonElement> ChangeAsync(string win, string tab, string dw, string field, string value) =>
    CallAsync(HttpMethod.Put, "/v2/change", $"change {field}", new
    {
        WindowId = win,
        List = new[] { new { TabName = tab, DatawindowName = dw, FieldName = field, Value = value } },
    });

Task<JsonElement> TabAsync(string win, string page) =>
    CallAsync(HttpMethod.Put, "/v2/tab", $"tab {page}", new { WindowId = win, PageName = page });

// Datawindows on the window's active surface, as column -> value maps per row.
async Task<List<Dictionary<string, string>>> RowsAsync(string win, string dwName)
{
    var data = await CallAsync(HttpMethod.Get, $"/v2/data?id={win}", "data");
    var rows = new List<Dictionary<string, string>>();
    foreach (var dw in data.EnumerateArray())
    {
        if (dw.GetProperty("Name").GetString() != dwName) continue;
        var columns = dw.GetProperty("Columns").EnumerateArray().Select(c => c.GetString()!).ToList();
        if (!dw.TryGetProperty("Data", out var rowData) || rowData.ValueKind != JsonValueKind.Array) continue;
        foreach (var row in rowData.EnumerateArray())
        {
            var cells = row.EnumerateArray().ToList();
            var map = new Dictionary<string, string>();
            for (var i = 0; i < columns.Count && i < cells.Count; i++)
                map[columns[i]] = cells[i].ValueKind == JsonValueKind.Null ? "" : cells[i].ToString();
            rows.Add(map);
        }
    }
    return rows;
}

// The active row of one datawindow (ActiveRow is 1-based).
async Task<Dictionary<string, string>> ActiveRowAsync(string win, string dwName)
{
    var data = await CallAsync(HttpMethod.Get, $"/v2/data?id={win}", "data");
    foreach (var dw in data.EnumerateArray())
    {
        if (dw.GetProperty("Name").GetString() != dwName) continue;
        var active = dw.TryGetProperty("ActiveRow", out var a) && a.ValueKind == JsonValueKind.Number ? Math.Max(a.GetInt32() - 1, 0) : 0;
        var rows = await RowsAsync(win, dwName);
        if (active < rows.Count) return rows[active];
    }
    return new Dictionary<string, string>();
}

// Answer whatever a change or save opened; return the PO number if the wizard ran.
// A "no PO Cost" or profit prompt (w_message) is answered Yes (cb_1). The Create PO wizard is
// recognised by its cb_finish button: cb_next COMMITS the PO, cb_finish closes it.
async Task<string?> AnswerAsync(JsonElement result)
{
    string? po = null;
    while (result.ValueKind == JsonValueKind.Object && result.TryGetProperty("Status", out var s)
           && s.ValueKind == JsonValueKind.Number && s.GetInt32() == Blocked)
    {
        var popup = result.GetProperty("Events").EnumerateArray()
            .Where(e => e.GetProperty("Name").GetString() == "windowopened")
            .SelectMany(e => e.GetProperty("Data").EnumerateArray())
            .First(kv => kv.GetProperty("Key").GetString() == "windowid").GetProperty("Value").GetString()!;
        var tools = (await CallAsync(HttpMethod.Get, $"/v2/tools?windowId={popup}", "tools"))
            .EnumerateArray().Select(t => t.GetProperty("ToolName").GetString()).ToList();   // includes the parent's ribbon
        var cls = (await CallAsync(HttpMethod.Get, $"/v2/window?id={popup}", "window")).GetProperty("Definition").GetProperty("Name").GetString();
        if (tools.Contains("cb_finish"))
        {
            foreach (var row in await RowsAsync(popup, "items"))
                Console.WriteLine($"  wizard: item={Cell(row, "item_id")} supplier={Cell(row, "supplier_id")} qty={Cell(row, "qty_to_purchase")}");
            await CallAsync(HttpMethod.Post, "/v2/tools", "tool cb_next", new { WindowId = popup, ToolName = "cb_next" });   // the PO is committed here
            po = Cell(await ActiveRowAsync(popup, "po_print"), "po_no");
            Console.WriteLine($"  wizard page 2: po_no={po}");
            result = await CallAsync(HttpMethod.Post, "/v2/tools", "tool cb_finish", new { WindowId = popup, ToolName = "cb_finish" });
        }
        else if (cls == "w_message" && tools.Contains("cb_1"))
        {
            Console.WriteLine("  prompt answered Yes (cb_1)");
            result = await CallAsync(HttpMethod.Post, "/v2/tools", "tool cb_1", new { WindowId = popup, ToolName = "cb_1" });
        }
        else throw new InvalidOperationException($"Unexpected response window: {string.Join(", ", tools)}");
    }
    return po;
}

// Print the line and any PO linked to it; return the line.
async Task<Dictionary<string, string>> ReadBackAsync()
{
    var lines = await ODataAsync("oe_line", $"order_no eq '{orderNo}' and line_no eq {lineNo}", OrderColumns);
    var line = lines[0].EnumerateObject().ToDictionary(p => p.Name, p => p.Value.ValueKind == JsonValueKind.Null ? "" : p.Value.ToString());
    Console.WriteLine("  oe_line: " + string.Join(", ", line.Select(p => $"{p.Key}={p.Value}")));
    foreach (var link in await ODataAsync("oe_line_po", $"order_number eq '{orderNo}' and line_number eq {lineNo}", ""))
    {
        var number = (int)link.GetProperty("po_no").GetDecimal();
        var po = (await ODataAsync("po_hdr", $"po_no eq {number}", "po_no,po_type,supplier_id,approved"))[0];
        Console.WriteLine($"  oe_line_po: po_no={number} connection_type={link.GetProperty("connection_type")} -> po_hdr type={po.GetProperty("po_type")} approved={po.GetProperty("approved")}");
    }
    return line;
}

// One OData table read.
async Task<List<JsonElement>> ODataAsync(string table, string filter, string select)
{
    var url = $"{BaseUrl}/odataservice/odata/table/{table}?$filter={Uri.EscapeDataString(filter)}";
    if (select.Length > 0) url += $"&$select={select}";
    var response = await client.GetAsync(url);
    response.EnsureSuccessStatusCode();
    return JsonDocument.Parse(await response.Content.ReadAsStringAsync())
        .RootElement.GetProperty("value").EnumerateArray().Select(e => e.Clone()).ToList();
}

static string Cell(Dictionary<string, string> row, string column) => row.TryGetValue(column, out var v) ? v : "";
static double Num(Dictionary<string, string> row, string column) => double.TryParse(Cell(row, column), out var n) ? n : 0;

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

## The Transaction API alternative

To convert lines in bulk without a window, `POST /api/v2/transaction` changes the disposition; it cannot create the PO, because `c_create_po` opens a wizard. The payload, including the allocation release and the required `po_cost`, is in [04 § Transaction API](../04-Interactive-API.md#transaction-api).

## Gotchas (verified on play 26.1.5950.0, 2026-10-17)

- **A line on a pick ticket is refused.** The program stops if `qty_on_pick_tickets` is above zero; reverse the pick ticket first. What P21 itself does with such a line was not tested.
- **`/transaction` without `po_cost` writes nothing.** The no-cost prompt is answered No, the result is `Failed: 1`, and the line is unchanged. `IgnoreDisabled: true` does not change this.
- **A wizard that does not open is not an error.** If the item's primary supplier at the location is the company's own intercompany supplier, the save can succeed with no wizard and no PO ([04 § Set quote to OFF first](../04-Interactive-API.md#set-quote-to-off-first-the-window-can-open-in-quote-mode)). The program exits with "The wizard did not run".
- **The PO is committed at `cb_next`.** A session that dies mid-wizard still leaves a real, linked PO behind; look for it before you retry.

## Verify

```text
GET /odataservice/odata/table/oe_line?$filter=order_no eq '1001234' and line_no eq 1
GET /odataservice/odata/table/oe_line_po?$filter=order_number eq '1001234' and line_number eq 1
```

Expect `disposition = 'D'` and `qty_allocated = 0` on the line, and one `oe_line_po` row with `connection_type = 'P'` whose `po_hdr` has `po_type = 'D'`. The example prints all three and exits with an error if the disposition did not stick.
