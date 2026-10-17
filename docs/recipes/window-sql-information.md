# Read a Window's SQL (SQL Information)

Read the SQL behind any P21 window through the API, the way **Help > SQL Information** shows it in the client: the datawindow's full `SELECT`, its column → `table.column` map, and, for one field, the database column, its datatype, and the table a save updates. Use it to find the `DatawindowName` and `FieldName` an Interactive or Transaction call needs, or to write an OData or SQL query that matches what a window shows.

**API:** Interactive (`POST /v2/tools`, tool `m_sqlinformation`) + the web client's `ui/full` surface · **Service:** any window with a service name (`Item` here) · **Deep dive:** [04 § P21 SQL Information](../04-Interactive-API.md#5-p21-sql-information) · [04 § The ui/full Surface](../04-Interactive-API.md#the-uifull-surface-the-web-clients-own-rest-api)

## Prerequisites

- P21 credentials — the complete example below authenticates itself; nothing to install but `httpx` (Python) or a bare `net8.0`-or-later console project (C#).
- A user who can open the window. The tool only reads: nothing is saved.
- The window's service name, the tab page that holds the datawindow, and the datawindow name. `GET /v2/window?id={windowId}` lists a window's tabs (`TabPageList`) and datawindows — see [04 § Window Discovery](../04-Interactive-API.md#window-discovery-techniques).

## Call sequence

1. `POST {ui_server}/api/ui/interactive/v2/window` `{"ServiceName": "Item"}`; `PUT /v2/tab` to the tab that holds the datawindow. Some datawindows need a loaded record first — the example's `load=` option changes the key field without saving.
2. Run the tool. `FieldName` is optional; `Row` is 1-based on a grid, `0` on a form:

   ```json
   {"SessionId": "{sessionId}", "WindowId": "{windowId}", "ToolName": "m_sqlinformation",
    "DatawindowName": "document_link", "FieldName": null, "Row": 0, "Text": null}
   ```

   The answer is `Status` 3 with a `windowopened` event; its `windowid` is the SQL Information dialog.
3. Read the dialog on the web client's surface — `{ui_server}/ui/full`, no `/api/` prefix, the same bearer token:
   - **SQL INFO** text: `GET /ui/full/v1/grid/{dialogId}/elements/state?dwName=sqlinfo&activeRows=*`
   - **Column map**: `POST /ui/full/v2/window/page` `{"WindowId": "{dialogId}", "PageName": "SQL INFORMATION REPORT"}`, then the same `elements/state` call with `dwName=showreport`
   - **SELECT**: `POST /ui/full/v2/window/page` `{"WindowId": "{dialogId}", "PageName": "SQL"}` — the SQL is in that answer, at `Result.TabDefinition.TextBoxes[0].Text`
4. `DELETE /v2/window` for the dialog and the window, then end the session.

## Complete example

`SERVICE`, `DATAWINDOW`, `TAB`, `FIELD`, `ROW` and `LOAD` set what the example describes; command-line arguments override them, so one copy reads any window:

```text
python window_sql_info.py Item tp_1_dw_1 tab=TABPAGE_1 field=item_id
python window_sql_info.py Item document_link tab=DOCUMENT_LINK field=link_name row=1 load=TABPAGE_1.tp_1_dw_1.item_id=WIDGET-001
dotnet run -- Item tp_1_dw_1 tab=TABPAGE_1 field=item_id
```

<!-- tabs -->
```python
"""Read a P21 datawindow's SQL through the client's SQL Information tool.

Usage:
    python window_sql_info.py [SERVICE DATAWINDOW] [tab=TAB] [field=FIELD] [row=N]
                              [load=TAB.DATAWINDOW.FIELD=VALUE]

1. Open the window by service name (Interactive API). With load=, retrieve a
   record first by changing its key field -- nothing is saved.
2. Select the tab that holds the datawindow, and run the m_sqlinformation tool
   on it, the way Help > SQL Information does in the client.
3. Read the dialog it opens: the SQL INFO text, the column map
   (label = table.column), and the datawindow's SELECT. The SELECT is a text
   box on the dialog's SQL tab, which only the web client's ui/full surface
   returns.
4. Close the dialog, the window and the session.
"""
import re
import sys

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.example.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
SERVICE = "Item"                          # Interactive service name of the window
DATAWINDOW = "document_link"              # the datawindow to describe
TAB = "DOCUMENT_LINK"                     # tab page that holds it ("" = leave as opened)
FIELD = ""                                # a column to describe ("" = none)
ROW = 0                                   # 1-based row for a grid field (0 = form or none)
LOAD = ""                                 # e.g. "TABPAGE_1.tp_1_dw_1.item_id=WIDGET-001" loads a record
# ---------------------------------------------------------------------------

# Command-line arguments override the constants above.
args = [a for a in sys.argv[1:] if "=" not in a]
options = dict(a.split("=", 1) for a in sys.argv[1:] if "=" in a)
if len(args) >= 2:
    SERVICE, DATAWINDOW = args[0], args[1]
    TAB = FIELD = LOAD = ""
    ROW = 0
TAB = options.get("tab", TAB)
FIELD = options.get("field", FIELD)
ROW = int(options.get("row", ROW))
LOAD = options.get("load", LOAD)


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
    """The answer, refusing HTTP errors and P21's Status 2 (failure)."""
    if r.status_code >= 400:
        raise RuntimeError(f"{what}: HTTP {r.status_code} {r.text[:300]}")
    body = r.json() if r.content else {}
    if isinstance(body, dict) and body.get("Status") == 2:
        raise RuntimeError(f"{what}: P21 refused it: {body.get('Messages')}")
    return body if isinstance(body, dict) else {}


def full_ok(r: httpx.Response, what: str) -> dict:
    """A ui/full answer: success there is Success + State "Normal", not HTTP 200."""
    body = r.json() if r.content else {}
    if r.status_code >= 400 or not (body.get("Success") and body.get("State") == "Normal"):
        raise RuntimeError(f"{what}: HTTP {r.status_code} {r.text[:300]}")
    return body


def opened_window(answer: dict) -> str:
    """The window id a tool opened (its windowopened event), or ""."""
    for event in answer.get("Events") or []:
        if event.get("Name") == "windowopened":
            for pair in event.get("Data") or []:
                if pair.get("Key") == "windowid":
                    return pair.get("Value") or ""
    return ""


with httpx.Client(verify=VERIFY_SSL, timeout=120, follow_redirects=True) as client:
    token = get_token(client)
    ui_server = get_ui_server(client, token)
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json",
               "Content-Type": "application/json"}
    iapi = f"{ui_server}/api/ui/interactive"
    full = f"{ui_server}/ui/full"   # the web client's surface: no /api/ prefix

    session = checked(client.post(f"{iapi}/sessions/",
                                  json={"ResponseWindowHandlingEnabled": True},
                                  headers=headers), "session")
    session_id = session.get("Id") or session.get("SessionId")
    try:
        # 1. Open the window, and load a record if asked to.
        window = checked(client.post(f"{iapi}/v2/window",
                                     json={"SessionId": session_id, "ServiceName": SERVICE},
                                     headers=headers), f"open {SERVICE}")
        window_id = window["WindowId"]

        def tab(name: str) -> None:
            checked(client.put(f"{iapi}/v2/tab",
                               json={"SessionId": session_id, "WindowId": window_id,
                                     "TabName": name, "PageName": name},
                               headers=headers), f"tab {name}")

        try:
            if LOAD:
                target, value = LOAD.split("=", 1)
                load_tab, load_dw, load_field = target.split(".", 2)
                tab(load_tab)
                checked(client.put(f"{iapi}/v2/change",
                                   json={"SessionId": session_id, "WindowId": window_id,
                                         "List": [{"TabName": load_tab, "DatawindowName": load_dw,
                                                   "FieldName": load_field, "Value": value}]},
                                   headers=headers), f"load {LOAD}")

            # 2. The tab that holds the datawindow, then Help > SQL Information.
            if TAB:
                tab(TAB)
            answer = checked(client.post(f"{iapi}/v2/tools",
                                         json={"SessionId": session_id, "WindowId": window_id,
                                               "ToolName": "m_sqlinformation",
                                               "DatawindowName": DATAWINDOW,
                                               "FieldName": FIELD or None,
                                               "Row": ROW, "Text": None},
                                         headers=headers), "m_sqlinformation")
            dialog = opened_window(answer)
            if not dialog:
                raise RuntimeError(f"SQL Information opened no dialog: {answer}")

            # 3. Read the dialog. Its title names the tab and the window.
            try:
                definition = checked(client.get(f"{iapi}/v2/window", params={"id": dialog},
                                                headers=headers), "dialog")["Definition"]
                pages = [page["Name"] for page in definition.get("TabPageList") or []]

                def rows(datawindow: str) -> list[dict]:
                    """A datawindow's rows on the dialog. ui/full's data/data returns an
                    empty grid until the client asks for its rows; elements/state does."""
                    r = client.get(f"{full}/v1/grid/{dialog}/elements/state",
                                   params={"dwName": datawindow, "activeRows": "*"},
                                   headers=headers)
                    return next(iter(full_ok(r, datawindow).get("Data", {}).values()), [])

                def page(name: str) -> dict:
                    """Select a tab page of the dialog; the answer is its controls."""
                    r = client.post(f"{full}/v2/window/page",
                                    json={"WindowId": dialog, "PageName": name},
                                    headers=headers)
                    return full_ok(r, f"page {name}")["Result"]["TabDefinition"]

                info = rows("sqlinfo")
                columns = []
                if "SQL INFORMATION REPORT" in pages:
                    page("SQL INFORMATION REPORT")
                    columns = [r["info"] for r in rows("showreport") if r.get("info")]
                select = None
                if "SQL" in pages:
                    boxes = page("SQL").get("TextBoxes") or []
                    select = next((b["Text"] for b in boxes if b.get("Text")), None)
            finally:
                client.delete(f"{iapi}/v2/window", params={"id": dialog}, headers=headers)
        finally:
            client.delete(f"{iapi}/v2/window", params={"id": window_id}, headers=headers)
    finally:
        client.delete(f"{iapi}/sessions/", headers=headers)

print(definition.get("Title"))
print("\n-- SQL INFO")
print(info[0]["text"] if info else "(none)")
print("\n-- Columns (label = table.column)")
print("\n".join(columns) or "(none)")
print("\n-- SELECT")
# The text arrives whitespace-collapsed; break it where the client left column gaps.
print(re.sub(r" {3,}", "\n    ", select.replace("\r\n", "\n")).strip() if select else "(none)")
```

```csharp
// Read a P21 datawindow's SQL through the client's SQL Information tool.
// Usage: dotnet run -- [SERVICE DATAWINDOW] [tab=TAB] [field=FIELD] [row=N] [load=TAB.DATAWINDOW.FIELD=VALUE]
// 1. Open the window by service name (Interactive API). With load=, retrieve a
//    record first by changing its key field -- nothing is saved.
// 2. Select the tab that holds the datawindow, and run the m_sqlinformation tool
//    on it, the way Help > SQL Information does in the client.
// 3. Read the dialog it opens: the SQL INFO text, the column map
//    (label = table.column), and the datawindow's SELECT. The SELECT is a text
//    box on the dialog's SQL tab, which only the web client's ui/full surface returns.
// 4. Close the dialog, the window and the session.
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.example.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
var service = "Item";                                 // Interactive service name of the window
var datawindow = "document_link";                     // the datawindow to describe
var tab = "DOCUMENT_LINK";                            // tab page that holds it ("" = leave as opened)
var field = "";                                       // a column to describe ("" = none)
var row = 0;                                          // 1-based row for a grid field (0 = form or none)
var load = "";                                        // e.g. "TABPAGE_1.tp_1_dw_1.item_id=WIDGET-001" loads a record
// ---------------------------------------------------------------------------

// Command-line arguments override the values above.
var positional = args.Where(a => !a.Contains('=')).ToArray();
var options = args.Where(a => a.Contains('='))
    .ToDictionary(a => a[..a.IndexOf('=')], a => a[(a.IndexOf('=') + 1)..]);
if (positional.Length >= 2)
{
    (service, datawindow) = (positional[0], positional[1]);
    (tab, field, row, load) = ("", "", 0, "");
}
tab = options.GetValueOrDefault("tab", tab);
field = options.GetValueOrDefault("field", field);
row = int.Parse(options.GetValueOrDefault("row", row.ToString()));
load = options.GetValueOrDefault("load", load);

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
var full = $"{uiServer}/ui/full";   // the web client's surface: no /api/ prefix

string title = "";
string sqlInfo = "(none)";
var columns = new List<string>();
string? select = null;

var session = await SendAsync(HttpMethod.Post, $"{iapi}/sessions/",
    new { ResponseWindowHandlingEnabled = true }, "session");
var sessionId = session.TryGetProperty("Id", out var id) ? id.GetString()
              : session.GetProperty("SessionId").GetString();
try
{
    // 1. Open the window, and load a record if asked to.
    var window = await SendAsync(HttpMethod.Post, $"{iapi}/v2/window",
        new { SessionId = sessionId, ServiceName = service }, $"open {service}");
    var windowId = window.GetProperty("WindowId").GetString()!;
    try
    {
        if (load != "")
        {
            var target = load[..load.IndexOf('=')];
            var value = load[(load.IndexOf('=') + 1)..];
            var parts = target.Split('.', 3);   // TAB.DATAWINDOW.FIELD
            await TabAsync(parts[0]);
            await SendAsync(HttpMethod.Put, $"{iapi}/v2/change",
                new { SessionId = sessionId, WindowId = windowId,
                      List = new[] { new { TabName = parts[0], DatawindowName = parts[1],
                                           FieldName = parts[2], Value = value } } },
                $"load {load}");
        }

        // 2. The tab that holds the datawindow, then Help > SQL Information.
        if (tab != "") await TabAsync(tab);
        var answer = await SendAsync(HttpMethod.Post, $"{iapi}/v2/tools",
            new { SessionId = sessionId, WindowId = windowId, ToolName = "m_sqlinformation",
                  DatawindowName = datawindow, FieldName = field == "" ? null : field,
                  Row = row, Text = (string?)null }, "m_sqlinformation");
        var dialog = OpenedWindow(answer)
            ?? throw new InvalidOperationException($"SQL Information opened no dialog: {answer}");

        // 3. Read the dialog. Its title names the tab and the window.
        try
        {
            using var dialogDoc = JsonDocument.Parse(
                await client.GetStringAsync($"{iapi}/v2/window?id={dialog}"));
            var definition = dialogDoc.RootElement.GetProperty("Definition");
            title = definition.GetProperty("Title").GetString() ?? "";
            var pages = definition.TryGetProperty("TabPageList", out var list) &&
                        list.ValueKind == JsonValueKind.Array
                ? list.EnumerateArray().Select(p => p.GetProperty("Name").GetString()).ToList()
                : new List<string?>();

            var info = await RowsAsync(dialog, "sqlinfo");
            if (info.Count > 0) sqlInfo = info[0].GetProperty("text").GetString() ?? "(none)";
            if (pages.Contains("SQL INFORMATION REPORT"))
            {
                await PageAsync(dialog, "SQL INFORMATION REPORT");
                foreach (var r in await RowsAsync(dialog, "showreport"))
                    if (r.TryGetProperty("info", out var line) && !string.IsNullOrEmpty(line.GetString()))
                        columns.Add(line.GetString()!);
            }
            if (pages.Contains("SQL"))
            {
                var sqlPage = await PageAsync(dialog, "SQL");
                if (sqlPage.TryGetProperty("TextBoxes", out var boxes) &&
                    boxes.ValueKind == JsonValueKind.Array)
                    select = boxes.EnumerateArray()
                        .Select(b => b.TryGetProperty("Text", out var t) ? t.GetString() : null)
                        .FirstOrDefault(t => !string.IsNullOrEmpty(t));
            }
        }
        finally
        {
            await client.DeleteAsync($"{iapi}/v2/window?id={dialog}");
        }
    }
    finally
    {
        await client.DeleteAsync($"{iapi}/v2/window?id={windowId}");
    }

    async Task TabAsync(string name) =>
        await SendAsync(HttpMethod.Put, $"{iapi}/v2/tab",
            new { SessionId = sessionId, WindowId = windowId, TabName = name, PageName = name },
            $"tab {name}");
}
finally
{
    await client.DeleteAsync($"{iapi}/sessions/");
}

Console.WriteLine(title);
Console.WriteLine("\n-- SQL INFO");
Console.WriteLine(sqlInfo);
Console.WriteLine("\n-- Columns (label = table.column)");
Console.WriteLine(columns.Count > 0 ? string.Join("\n", columns) : "(none)");
Console.WriteLine("\n-- SELECT");
// The text arrives whitespace-collapsed; break it where the client left column gaps.
Console.WriteLine(select is null ? "(none)"
    : Regex.Replace(select.Replace("\r\n", "\n"), " {3,}", "\n    ").Trim());

// --- helpers ---------------------------------------------------------------

// A datawindow's rows on the dialog. ui/full's data/data returns an empty grid
// until the client asks for its rows; elements/state does.
async Task<List<JsonElement>> RowsAsync(string window, string dw)
{
    var body = await FullOkAsync(await client.GetAsync(
        $"{full}/v1/grid/{window}/elements/state?dwName={dw}&activeRows=*"), dw);
    if (!body.TryGetProperty("Data", out var data) || data.ValueKind != JsonValueKind.Object)
        return new List<JsonElement>();
    foreach (var entry in data.EnumerateObject())
        return entry.Value.EnumerateArray().Select(e => e.Clone()).ToList();
    return new List<JsonElement>();
}

// Select a tab page of the dialog; the answer is its controls.
async Task<JsonElement> PageAsync(string window, string name)
{
    var body = JsonSerializer.Serialize(new { WindowId = window, PageName = name });
    var response = await client.PostAsync($"{full}/v2/window/page",
        new StringContent(body, Encoding.UTF8, "application/json"));
    return (await FullOkAsync(response, $"page {name}")).GetProperty("Result").GetProperty("TabDefinition");
}

// A ui/full answer: success there is Success + State "Normal", not HTTP 200.
static async Task<JsonElement> FullOkAsync(HttpResponseMessage response, string what)
{
    var text = await response.Content.ReadAsStringAsync();
    var body = text.Length == 0 ? default : JsonDocument.Parse(text).RootElement.Clone();
    if (!response.IsSuccessStatusCode || body.ValueKind != JsonValueKind.Object ||
        !body.TryGetProperty("Success", out var ok) || !ok.GetBoolean() ||
        body.GetProperty("State").GetString() != "Normal")
        throw new InvalidOperationException($"{what}: HTTP {(int)response.StatusCode} {text}");
    return body;
}

// One Interactive call; refuses HTTP errors and P21's Status 2 (failure).
async Task<JsonElement> SendAsync(HttpMethod method, string url, object body, string what)
{
    using var request = new HttpRequestMessage(method, url)
    {
        Content = new StringContent(JsonSerializer.Serialize(body), Encoding.UTF8,
            "application/json"),
    };
    var response = await client.SendAsync(request);
    var text = await response.Content.ReadAsStringAsync();
    if (!response.IsSuccessStatusCode)
        throw new InvalidOperationException($"{what}: HTTP {(int)response.StatusCode} {text}");
    var answer = text.Length == 0 ? default : JsonDocument.Parse(text).RootElement.Clone();
    if (answer.ValueKind == JsonValueKind.Object &&
        answer.TryGetProperty("Status", out var status) && status.GetInt32() == 2)
        throw new InvalidOperationException($"{what}: P21 refused it: {text}");
    return answer;
}

// The window id a tool opened (its windowopened event), or null.
static string? OpenedWindow(JsonElement answer)
{
    if (!answer.TryGetProperty("Events", out var events)) return null;
    foreach (var e in events.EnumerateArray())
        if (e.GetProperty("Name").GetString() == "windowopened")
            foreach (var pair in e.GetProperty("Data").EnumerateArray())
                if (pair.GetProperty("Key").GetString() == "windowid")
                    return pair.GetProperty("Value").GetString();
    return null;
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

    var match = Regex.Match(payload, $"<{field}>([^<]+)</{field}>");
    if (!match.Success)
        throw new InvalidOperationException(
            $"No {field} in response: {payload[..Math.Min(200, payload.Length)]}");
    return match.Groups[1].Value;
}
```
<!-- /tabs -->

**Example output** — `Item tp_1_dw_1 tab=TABPAGE_1 field=item_id`, trimmed (the `SELECT` arrives whitespace-collapsed; the example breaks it at the client's column gaps):

```text
SQL Information for General Tab on Item Maintenance

-- SQL INFO
Database name for 'Item ID' is inv_mast.item_id.
Column datatype is char(40).
The table to be updated is inv_mast.
The field name is item_id
The column usage is: The id used to refer to the item in the application..
DataWindow Name: tp_1_dw_1
Window Name: w_inventory_sheet
URL Handler Menu Name: m_inventorymastermaintenance

-- Columns (label = table.column)
Column 1: Item ID: = inv_mast.item_id
Column 2: Item Desc = inv_mast.item_desc
Column 3: Delete Flag = inv_mast.delete_flag
...

-- SELECT
--General Tab on Item Maintenance
SELECT inv_mast.item_id
    ,inv_mast.item_desc
    ,inv_mast.delete_flag
    ...
    FROM inv_mast  LEFT JOIN discount_group AS discount_group_a ON (...) ...
    WHERE inv_mast.item_id = :item_id
```

With a record loaded (`load=`), the title carries its caption, as in the client: `SQL Information for Document Links Tab on Item Maintenance: WIDGET-001 (...)`.

## Gotchas (verified on play 26.1.5950.0, 2026-10-17)

- **The `SELECT` comes back only from `ui/full`.** The dialog's `SQL` tab is a text box (`mle_text`), not a datawindow. The Interactive API lists and returns datawindows only: `PUT /v2/tab` to `SQL` succeeds, and `GET /v2/data` then returns the previous tab's rows. `POST /ui/full/v2/window/page` returns the tab's controls, and it accepts the dialog the Interactive session opened.
- **Grid rows on `ui/full` are empty until requested.** `GET /ui/full/v2/data/data?id={dialogId}&dw=showreport` returns `[]` with `TotalRows` 8; `GET /ui/full/v1/grid/{dialogId}/elements/state?dwName=showreport&activeRows=*` returns the rows.
- **A `FieldName` that is not a column of the datawindow is ignored** — no error, and the text reads `No column was selected`. On a grid, pass `Row` as well. The column map and the `SELECT` do not change with `FieldName`.
- **The `SELECT` is the design-time SQL.** Retrieval arguments show (`WHERE inv_mast.item_id = :item_id`); the filter P21 adds at run time goes in at `/*MAIN WHERE CLAUSE*/` and is not shown.
- **Some tabs refuse the tool until a record is loaded.** Order Entry's Items tab answers `A valid customer ID must first be entered.` Load an existing record first — `Order items tab=TP_ITEMS field=unit_price row=1 load=TABPAGE_1.order.order_no=1001234` returns `oe_line.unit_price`, `decimal(9)`, updated in `oe_line`. The example never saves.
- **Report windows have no service name on the Interactive API.** Open them on [the `ui/full` surface](../04-Interactive-API.md#the-uifull-surface-the-web-clients-own-rest-api) by menu class and run the tool through `POST /ui/full/v2/window/tools`; that call answers `Success: false`, `State: "Blocked"`, with the dialog in the `windowopened` event's `EventData.windowid`. A report's criteria datawindow has no `SELECT` (`External source data; no SQL select associated with displayed data`). This example covers windows with a service name only.
- **The output is tenant-specific.** Site customizations appear in it — user-defined (`*_ud`) joins and columns in the `SELECT` and the column map — and the dialog title carries the loaded record's caption. Review it before you paste it anywhere public.

## Verify

Compare one line of the output with the client: open the same window, right-click the same field, and select **Help > SQL Information**. The `SQL INFO` text and the **SQL** tab match the example's `-- SQL INFO` and `-- SELECT` sections. Nothing to read back — the tool writes nothing.

> **Credit:** *@mrwuss* — `m_sqlinformation` through the Interactive API and the `SQL` tab through `ui/full/v2/window/page` found and verified on play 26.1.5950.0, 2026-10-17 ([#203](https://github.com/mrwuss/p21-api-documentation/issues/203)).
