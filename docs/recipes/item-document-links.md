# Attach a Document to an Item, Assembly or Kit (Document Links)

Upload a file and add it to an item's **Document Links** tab through the API, the way the P21 client does it — including on assemblies and kits, and on the display area that puts a document on the sales-order pick ticket.

**API:** File handler REST (`/api/filehandler`) + Interactive (`Item` window) + OData read-back · **Service:** `Item` · **Deep dive:** [04 § Adding a Document Link in the Item Window](../04-Interactive-API.md#adding-a-document-link-in-the-item-window) · [15 § filehandler](../15-Other-REST-Families.md#filehandler) · **Full schema:** [Item.json](../../definitions/Item.json) · [Assembly.json](../../definitions/Assembly.json)

## Prerequisites

- P21 credentials — the complete example below authenticates itself; nothing to install but `httpx` (Python) or a bare `net8.0`-or-later console project (C#).
- A user whose role can save the `Item` window.
- The file to attach, on the machine that runs the example.

> **The Transaction API cannot add a link.** Both the `Item` and the `Assembly` services list a `DOCUMENT_LINK.document_link` datawindow in their definitions, but a POST that sets `link_name` fails with `Column is disabled: link_name` on both. The grid is the display list (`d_dw_document_link_display`); links are added through the **Add Link** dialog, which only the Interactive API reaches.

## Where an assembly's document lives

An assembly or kit has no document links of its own. It is an item, and its links are **item links**:

| `document_link` column | Value for an item link |
|---|---|
| `source_area_cd` | `1314` (Item Maintenance) |
| `key1_cd` / `key1_value` | `inv_mast_uid` / the item's `inv_mast_uid` as a string |
| `row_status_flag` | `704` active |

Each link has one `document_link_area` row per **display area** — the windows and printed forms where it shows. Assembly Maintenance only *views* links: its Document Links tab offers `m_viewlink` and no `m_addlink`.

- The **header** Document Links tab of Assembly Maintenance lists the assembly item's links that carry display area `1302` (Assembly Maintenance). A link on the same item without `1302` does not appear there.
- The **component** Document Links tab lists each component item's own links the same way.

Display areas that matter for assemblies and kits (code values, the same on every tenant):

| `display_area_cd` | Area |
|---|---|
| `1314` | Item Maintenance (always selected — the window the link was made in) |
| `1445` | Item Master Inquiry |
| `1302` | Assembly Maintenance |
| `3453` | Sales Order Pick Ticket |
| `1319` | Order Entry/RMA |
| `1332` | Shipping |
| `999` | Packing List |
| `998` | Order Acknowledgement |
| `1325` | Production Order Entry/Processing |
| `2750` | Production Order Form |

The Add Link dialog lists the rest in its **Available Area** list (26 areas on 26.1.5950.0). A document reaches a printed form only through that form's area — for the sales-order pick ticket, `3453`.

## Call sequence

1. **Upload** the file into the folder the client's own Add Link dialog uses — the `item_maintenance_doc_link_upload_folder_path` system setting: `POST /api/filehandler/file/path?fileName={name}&path={folder}` with the raw bytes as the body.
2. **Open** the `Item` window, change `item_id` on `TABPAGE_1`, select the `DOCUMENT_LINK` tab.
3. **Add Link:** `POST /v2/tools` with `ToolName: "m_addlink"` **and** `DatawindowName: "document_link"`. It opens the tabless **Document Link** dialog (`w_inventory_sheet`).
4. **Fill the dialog's `_dw_link`:** `link_path`, `link_name`, `outside_use_flag`, `mandatory_flag`.
5. **Display areas:** the dialog starts with Item Maintenance and Item Master Inquiry selected. `cb_selectall` moves every available area to Selected Areas.
6. **`cb_ok`** closes the dialog. Nothing is written yet.
7. **Save** the `Item` window (`PUT /v2/data`, body = the bare window id). Only the save writes the `document_link` row and its `document_link_area` rows. A business rule can answer the save with a prompt (Status 3) — see [Gotchas](#gotchas-verified-on-play-26159500-2026-10-17).
8. **Read back** `document_link` and `document_link_area` over OData.

```json
POST {ui_server}/api/ui/interactive/v2/tools
{ "WindowId": "<item window id>", "ToolName": "m_addlink", "DatawindowName": "document_link" }

PUT {ui_server}/api/ui/interactive/v2/change
{ "WindowId": "<dialog id>", "List": [
  { "TabName": null, "DatawindowName": "_dw_link", "FieldName": "link_path",
    "Value": "\\\\fileserver\\share\\P21\\Files\\ItemMaint\\WIDGET-001 drawing.pdf" } ] }

POST {ui_server}/api/ui/interactive/v2/tools
{ "WindowId": "<dialog id>", "ToolName": "cb_selectall" }
```

## Complete example

Attach a local file to an item — an assembly or kit works the same way. Set `ALL_AREAS` / `AllAreas` to show the document everywhere, Assembly Maintenance and Sales Order Pick Ticket included. A second run finds the existing link and adds nothing.

<!-- tabs -->
```python
"""Attach a file to an item's Document Links tab, the way the P21 client does it.

An assembly or kit is an item: its Assembly Maintenance Document Links tab and
its pick tickets use the same link, through the link's display areas.

1. Upload the file into Item Maintenance's document upload folder (file handler).
2. Add the link in the Item window's "Add Item Maintenance Link" dialog (Interactive),
   on the dialog's default display areas or, with ALL_AREAS, on every area.
3. Save the Item window -- the dialog's OK alone writes nothing.
4. Read the link and its display areas back over OData.
"""
import re
import sys
from pathlib import Path

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.example.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
ITEM_ID = "WIDGET-001"                    # the item to attach to
FILE_PATH = "WIDGET-001 drawing.pdf"      # the local file to attach
OUTSIDE_USE = "N"                         # "Y" lets the document leave the company
ALL_AREAS = False                         # True: show it everywhere, pick tickets included
SAVE_PROMPT_ANSWER = ""                   # e.g. "cb_1" -- the button for a prompt the save raises
# ---------------------------------------------------------------------------

ITEM_MAINTENANCE_AREA = 1314              # document_link.source_area_cd for an item
UPLOAD_FOLDER_SETTING = "item_maintenance_doc_link_upload_folder_path"


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


def odata(client: httpx.Client, headers: dict, table: str, select: str, where: str) -> list[dict]:
    """One OData table read."""
    r = client.get(
        f"{BASE_URL}/odataservice/odata/table/{table}",
        params={"$select": select, "$filter": where},
        headers=headers,
    )
    r.raise_for_status()
    return r.json()["value"]


def opened_window(answer: dict) -> str:
    """The window id a tool opened (its windowopened event), or ""."""
    for event in answer.get("Events") or []:
        if event.get("Name") == "windowopened":
            for pair in event.get("Data") or []:
                if pair.get("Key") == "windowid":
                    return pair.get("Value") or ""
    return ""


def checked(r: httpx.Response, what: str) -> dict:
    """The answer, refusing HTTP errors and P21's Status 2 (failure)."""
    if r.status_code >= 400:
        raise RuntimeError(f"{what}: HTTP {r.status_code} {r.text[:300]}")
    body = r.json() if r.content else {}
    if isinstance(body, dict) and body.get("Status") == 2:
        raise RuntimeError(f"{what}: P21 refused it: {body.get('Messages')}")
    return body if isinstance(body, dict) else {}


source = Path(FILE_PATH)
content = source.read_bytes()

with httpx.Client(verify=VERIFY_SSL, timeout=120, follow_redirects=True) as client:
    token = get_token(client)
    ui_server = get_ui_server(client, token)
    auth = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    headers = {**auth, "Content-Type": "application/json"}

    # The folder P21's own Add Link dialog uploads into, and the item's uid.
    folder = odata(client, auth, "system_setting", "value",
                   f"name eq '{UPLOAD_FOLDER_SETTING}'")[0]["value"].rstrip("\\")
    items = odata(client, auth, "inv_mast", "inv_mast_uid", f"item_id eq '{ITEM_ID}'")
    if not items:
        sys.exit(f"{ITEM_ID} is not in P21")
    uid = str(int(items[0]["inv_mast_uid"]))
    link_path = f"{folder}\\{source.name}"

    # A second run must not add a second link.
    links_on_item = (
        f"source_area_cd eq {ITEM_MAINTENANCE_AREA} and key1_cd eq 'inv_mast_uid' "
        f"and key1_value eq '{uid}' and row_status_flag eq 704"
    )
    existing = odata(client, auth, "document_link", "document_link_uid,link_path", links_on_item)
    if any(row["link_path"].lower() == link_path.lower() for row in existing):
        sys.exit(f"{ITEM_ID} already links {link_path}")

    # 1. Upload. The body is the raw file; path names the upload folder.
    r = client.post(
        f"{BASE_URL}/api/filehandler/file/path",
        params={"fileName": source.name, "path": folder},
        headers=auth,
        content=content,
    )
    r.raise_for_status()
    uploaded = r.json()
    if uploaded.get("SizeInBytes") != len(content):
        sys.exit(f"Upload landed {uploaded.get('SizeInBytes')} bytes of {len(content)}")
    print(f"Uploaded {uploaded['FullPath']}")

    # 2. The Item window, the item, its Document Links tab, Add Link.
    session = checked(client.post(f"{ui_server}/api/ui/interactive/sessions/",
                                  json={"ResponseWindowHandlingEnabled": True},
                                  headers=headers), "session")
    session_id = session.get("Id") or session.get("SessionId")
    try:
        window = checked(client.post(f"{ui_server}/api/ui/interactive/v2/window",
                                     json={"SessionId": session_id, "ServiceName": "Item"},
                                     headers=headers), "open Item")
        window_id = window["WindowId"]

        def tab(name: str) -> None:
            checked(client.put(f"{ui_server}/api/ui/interactive/v2/tab",
                               json={"SessionId": session_id, "WindowId": window_id,
                                     "TabName": name, "PageName": name},
                               headers=headers), f"tab {name}")

        def change(target: str, field: str, value: str, *, tab_name=None, datawindow=None):
            item = {"TabName": tab_name, "FieldName": field, "Value": value}
            if datawindow:
                item["DatawindowName"] = datawindow
            return checked(client.put(f"{ui_server}/api/ui/interactive/v2/change",
                                      json={"SessionId": session_id, "WindowId": target,
                                            "List": [item]},
                                      headers=headers), f"change {field}")

        tab("TABPAGE_1")
        change(window_id, "item_id", ITEM_ID, tab_name="TABPAGE_1")
        tab("DOCUMENT_LINK")
        answer = checked(client.post(f"{ui_server}/api/ui/interactive/v2/tools",
                                     json={"SessionId": session_id, "WindowId": window_id,
                                           "ToolName": "m_addlink",
                                           "DatawindowName": "document_link"},
                                     headers=headers), "Add Link")
        dialog = opened_window(answer)
        if not dialog:
            raise RuntimeError(f"Add Link opened no dialog: {answer}")

        # The dialog's own datawindow is _dw_link; it has no tabs.
        for field, value in (("link_path", link_path), ("link_name", source.name),
                             ("outside_use_flag", OUTSIDE_USE), ("mandatory_flag", "N")):
            change(dialog, field, value, datawindow="_dw_link")
        if ALL_AREAS:
            # Select All moves every Available Area to Selected Areas, Assembly
            # Maintenance and Sales Order Pick Ticket among them.
            checked(client.post(f"{ui_server}/api/ui/interactive/v2/tools",
                                json={"SessionId": session_id, "WindowId": dialog,
                                      "ToolName": "cb_selectall"},
                                headers=headers), "Select All")
        checked(client.post(f"{ui_server}/api/ui/interactive/v2/tools",
                            json={"SessionId": session_id, "WindowId": dialog,
                                  "ToolName": "cb_ok"},
                            headers=headers), "OK")

        # 3. Save the Item window: the body is the bare window id.
        saved = checked(client.put(f"{ui_server}/api/ui/interactive/v2/data",
                                   json=window_id, headers=headers), "save")
        # A business rule on the Item window can stop the save with a prompt
        # (Status 3). Name it and its buttons, and answer only when told to.
        while saved.get("Status") == 3 and opened_window(saved):
            prompt = opened_window(saved)
            title = checked(client.get(f"{ui_server}/api/ui/interactive/v2/window",
                                       params={"id": prompt}, headers=headers),
                            "prompt")["Definition"]["Title"]
            buttons = {t["ToolName"]: t.get("Text") for t in client.get(
                f"{ui_server}/api/ui/interactive/v2/tools", params={"windowId": prompt},
                headers=headers).json() if t["ToolName"].startswith("cb_") and t.get("Text")}
            if SAVE_PROMPT_ANSWER not in buttons:
                raise RuntimeError(f"The save opened '{title}' with buttons {buttons}; "
                                   "set SAVE_PROMPT_ANSWER to one of them")
            print(f"Answered '{title}' with {buttons[SAVE_PROMPT_ANSWER]}")
            saved = checked(client.post(f"{ui_server}/api/ui/interactive/v2/tools",
                                        json={"SessionId": session_id, "WindowId": prompt,
                                              "ToolName": SAVE_PROMPT_ANSWER},
                                        headers=headers), "answer")
        if saved.get("Status") != 1:
            raise RuntimeError(f"The save did not finish (Status {saved.get('Status')}): "
                               f"{saved.get('Messages')}")
        client.delete(f"{ui_server}/api/ui/interactive/v2/window",
                      params={"id": window_id}, headers=headers)
    finally:
        client.delete(f"{ui_server}/api/ui/interactive/sessions/", headers=headers)

    # 4. Read it back: the link, and where P21 shows it.
    link = next(row for row in odata(client, auth, "document_link",
                                     "document_link_uid,link_name,link_path,outside_use_flag",
                                     links_on_item)
                if row["link_path"].lower() == link_path.lower())
    areas = odata(client, auth, "document_link_area", "display_area_cd",
                  f"document_link_uid eq {int(link['document_link_uid'])} and row_status_flag eq 704")
    print(f"Linked {link['link_name']} to {ITEM_ID} as document_link_uid "
          f"{int(link['document_link_uid'])}, outside use {link['outside_use_flag']}, "
          f"shown in areas {sorted(int(a['display_area_cd']) for a in areas)}")
```

```csharp
// Attach a file to an item's Document Links tab, the way the P21 client does it.
// An assembly or kit is an item: its Assembly Maintenance Document Links tab and
// its pick tickets use the same link, through the link's display areas.
// 1. Upload the file into Item Maintenance's document upload folder (file handler).
// 2. Add the link in the Item window's "Add Item Maintenance Link" dialog (Interactive),
//    on the dialog's default display areas or, with AllAreas, on every area.
// 3. Save the Item window -- the dialog's OK alone writes nothing.
// 4. Read the link and its display areas back over OData.
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.example.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string ItemId = "WIDGET-001";                   // the item to attach to
const string FilePath = "WIDGET-001 drawing.pdf";     // the local file to attach
const string OutsideUse = "N";                        // "Y" lets the document leave the company
bool AllAreas = false;                                // true: show it everywhere, pick tickets included
const string SavePromptAnswer = "";                   // e.g. "cb_1" -- the button for a prompt the save raises
// ---------------------------------------------------------------------------

const int ItemMaintenanceArea = 1314;                 // document_link.source_area_cd for an item
const string UploadFolderSetting = "item_maintenance_doc_link_upload_folder_path";

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

var fileName = Path.GetFileName(FilePath);
var content = await File.ReadAllBytesAsync(FilePath);

// The folder P21's own Add Link dialog uploads into, and the item's uid.
var folder = (await ODataAsync("system_setting", "value", $"name eq '{UploadFolderSetting}'"))[0]
    .GetProperty("value").GetString()!.TrimEnd('\\');
var items = await ODataAsync("inv_mast", "inv_mast_uid", $"item_id eq '{ItemId}'");
if (items.Count == 0) { Console.WriteLine($"{ItemId} is not in P21"); return; }
var uid = items[0].GetProperty("inv_mast_uid").GetDecimal().ToString("0");
var linkPath = $"{folder}\\{fileName}";

// A second run must not add a second link.
var linksOnItem = $"source_area_cd eq {ItemMaintenanceArea} and key1_cd eq 'inv_mast_uid' " +
                  $"and key1_value eq '{uid}' and row_status_flag eq 704";
var existing = await ODataAsync("document_link", "document_link_uid,link_path", linksOnItem);
if (existing.Any(r => string.Equals(r.GetProperty("link_path").GetString(), linkPath,
        StringComparison.OrdinalIgnoreCase)))
{
    Console.WriteLine($"{ItemId} already links {linkPath}");
    return;
}

// 1. Upload. The body is the raw file; path names the upload folder.
var uploadUrl = $"{BaseUrl}/api/filehandler/file/path?fileName={Uri.EscapeDataString(fileName)}" +
                $"&path={Uri.EscapeDataString(folder)}";
var upload = await client.PostAsync(uploadUrl, new ByteArrayContent(content));
upload.EnsureSuccessStatusCode();
using (var uploaded = JsonDocument.Parse(await upload.Content.ReadAsStringAsync()))
{
    var size = uploaded.RootElement.GetProperty("SizeInBytes").GetInt64();
    if (size != content.Length)
        throw new InvalidOperationException($"Upload landed {size} bytes of {content.Length}");
    Console.WriteLine($"Uploaded {uploaded.RootElement.GetProperty("FullPath").GetString()}");
}

// 2. The Item window, the item, its Document Links tab, Add Link.
var session = await SendAsync(HttpMethod.Post, $"{uiServer}/api/ui/interactive/sessions/",
    new { ResponseWindowHandlingEnabled = true }, "session");
var sessionId = session.TryGetProperty("Id", out var id) ? id.GetString()
              : session.GetProperty("SessionId").GetString();
try
{
    var window = await SendAsync(HttpMethod.Post, $"{uiServer}/api/ui/interactive/v2/window",
        new { SessionId = sessionId, ServiceName = "Item" }, "open Item");
    var windowId = window.GetProperty("WindowId").GetString()!;

    await TabAsync("TABPAGE_1");
    await ChangeAsync(windowId, "item_id", ItemId, tabName: "TABPAGE_1");
    await TabAsync("DOCUMENT_LINK");
    var answer = await SendAsync(HttpMethod.Post, $"{uiServer}/api/ui/interactive/v2/tools",
        new { SessionId = sessionId, WindowId = windowId, ToolName = "m_addlink",
              DatawindowName = "document_link" }, "Add Link");
    var dialog = OpenedWindow(answer)
        ?? throw new InvalidOperationException($"Add Link opened no dialog: {answer}");

    // The dialog's own datawindow is _dw_link; it has no tabs.
    foreach (var (field, value) in new[] {
                 ("link_path", linkPath), ("link_name", fileName),
                 ("outside_use_flag", OutsideUse), ("mandatory_flag", "N") })
        await ChangeAsync(dialog, field, value, datawindow: "_dw_link");
    if (AllAreas)
        // Select All moves every Available Area to Selected Areas, Assembly
        // Maintenance and Sales Order Pick Ticket among them.
        await SendAsync(HttpMethod.Post, $"{uiServer}/api/ui/interactive/v2/tools",
            new { SessionId = sessionId, WindowId = dialog, ToolName = "cb_selectall" }, "Select All");
    await SendAsync(HttpMethod.Post, $"{uiServer}/api/ui/interactive/v2/tools",
        new { SessionId = sessionId, WindowId = dialog, ToolName = "cb_ok" }, "OK");

    // 3. Save the Item window: the body is the bare window id.
    var saved = await SendAsync(HttpMethod.Put, $"{uiServer}/api/ui/interactive/v2/data",
        windowId, "save");
    // A business rule on the Item window can stop the save with a prompt
    // (Status 3). Name it and its buttons, and answer only when told to.
    while (saved.GetProperty("Status").GetInt32() == 3 && OpenedWindow(saved) is string prompt)
    {
        using var promptWindow = JsonDocument.Parse(await client.GetStringAsync(
            $"{uiServer}/api/ui/interactive/v2/window?id={prompt}"));
        var title = promptWindow.RootElement.GetProperty("Definition").GetProperty("Title").GetString();
        using var tools = JsonDocument.Parse(await client.GetStringAsync(
            $"{uiServer}/api/ui/interactive/v2/tools?windowId={prompt}"));
        var buttons = tools.RootElement.EnumerateArray()
            .Where(t => t.GetProperty("ToolName").GetString()!.StartsWith("cb_") &&
                        !string.IsNullOrEmpty(t.GetProperty("Text").GetString()))
            .ToDictionary(t => t.GetProperty("ToolName").GetString()!,
                          t => t.GetProperty("Text").GetString()!);
        if (!buttons.ContainsKey(SavePromptAnswer))
            throw new InvalidOperationException($"The save opened '{title}' with buttons " +
                string.Join(", ", buttons.Select(b => $"{b.Key} = {b.Value}")) +
                "; set SavePromptAnswer to one of them");
        Console.WriteLine($"Answered '{title}' with {buttons[SavePromptAnswer]}");
        saved = await SendAsync(HttpMethod.Post, $"{uiServer}/api/ui/interactive/v2/tools",
            new { SessionId = sessionId, WindowId = prompt, ToolName = SavePromptAnswer }, "answer");
    }
    if (saved.GetProperty("Status").GetInt32() != 1)
        throw new InvalidOperationException($"The save did not finish: {saved}");
    await client.DeleteAsync($"{uiServer}/api/ui/interactive/v2/window?id={windowId}");

    async Task TabAsync(string name) =>
        await SendAsync(HttpMethod.Put, $"{uiServer}/api/ui/interactive/v2/tab",
            new { SessionId = sessionId, WindowId = windowId, TabName = name, PageName = name },
            $"tab {name}");
}
finally
{
    await client.DeleteAsync($"{uiServer}/api/ui/interactive/sessions/");
}

// 4. Read it back: the link, and where P21 shows it.
var link = (await ODataAsync("document_link",
        "document_link_uid,link_name,link_path,outside_use_flag", linksOnItem))
    .First(r => string.Equals(r.GetProperty("link_path").GetString(), linkPath,
        StringComparison.OrdinalIgnoreCase));
var linkUid = link.GetProperty("document_link_uid").GetDecimal().ToString("0");
var areas = (await ODataAsync("document_link_area", "display_area_cd",
        $"document_link_uid eq {linkUid} and row_status_flag eq 704"))
    .Select(a => (int)a.GetProperty("display_area_cd").GetDecimal()).Order();
Console.WriteLine($"Linked {link.GetProperty("link_name").GetString()} to {ItemId} as " +
                  $"document_link_uid {linkUid}, outside use " +
                  $"{link.GetProperty("outside_use_flag").GetString()}, shown in areas " +
                  $"[{string.Join(", ", areas)}]");

// --- helpers ---------------------------------------------------------------

// One OData table read.
async Task<List<JsonElement>> ODataAsync(string table, string select, string where)
{
    var url = $"{BaseUrl}/odataservice/odata/table/{table}?$select={select}" +
              $"&$filter={Uri.EscapeDataString(where)}";
    var response = await client.GetAsync(url);
    response.EnsureSuccessStatusCode();
    using var doc = JsonDocument.Parse(await response.Content.ReadAsStringAsync());
    return doc.RootElement.GetProperty("value").EnumerateArray().Select(e => e.Clone()).ToList();
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

// One field change, on a tab of the window or on a tabless dialog's datawindow.
async Task ChangeAsync(string target, string field, string value,
    string? tabName = null, string? datawindow = null)
{
    var item = new Dictionary<string, string?> { ["TabName"] = tabName, ["FieldName"] = field,
                                                 ["Value"] = value };
    if (datawindow is not null) item["DatawindowName"] = datawindow;
    await SendAsync(HttpMethod.Put, $"{uiServer}/api/ui/interactive/v2/change",
        new { SessionId = sessionId, WindowId = target, List = new[] { item } },
        $"change {field}");
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

    var match = System.Text.RegularExpressions.Regex.Match(payload, $"<{field}>([^<]+)</{field}>");
    if (!match.Success)
        throw new InvalidOperationException(
            $"No {field} in response: {payload[..Math.Min(200, payload.Length)]}");
    return match.Groups[1].Value;
}
```
<!-- /tabs -->

## Gotchas (verified on play 26.1.5950.0, 2026-10-17)

- **Only the window save writes.** `cb_ok` closes the dialog and adds a grid row; closing the window without saving writes nothing.
- **Areas: all, or the defaults.** `cb_selectall` works. Moving a single area needs a *selected* row in the dialog's `source` list, and setting the current row with `PUT /v2/row` does not select it: `cb_select` then fails with `Button cb_select is not enabled`. `PUT /v2/rows/selected` takes a `RowsSpecification` object whose row field this page has not identified — every shape tried returned an empty HTTP 500. Until it is captured (the web client's DevTools Network tab shows it), add the link with all areas or the defaults, and narrow the list in the client's Edit Link dialog.
- **A business rule can stop the save.** On a tenant with an Item rule, the save returns Status 3 and opens a rule-callback window — on play, *Item Issues Detected* with `cb_1` = *Yes, Proceed Anyway* and `cb_2` = *No, Cancel*. The example names the prompt and its buttons and stops; set `SAVE_PROMPT_ANSWER` / `SavePromptAnswer` to answer it. Read the rule's message before you choose: [04 § Worked Example: Item Issues Detected](../04-Interactive-API.md#worked-example-item-issues-detected-rule-callback).
- **The link path must be a real UNC path.** A path that reaches the server with one leading backslash (`\fileserver\share\...`, typically an escaping slip) is refused on the `link_path` change: *The path '…' is not valid - this path needs to point to a valid FileHandler location.* With link-in-place allowed, a well-formed UNC path outside the upload folder is accepted as well — the upload is only needed when the file is not already on a share the server reads.
- **The upload does not overwrite.** `POST /api/filehandler/file/path` to a file name that already exists in the folder returns an HTTP 500. The example checks for an existing link first; a file left by a run that failed after the upload has to be removed or renamed before the next run.
- **Pick tickets returned by the API do not carry the document.** A sales-order pick ticket printed through the API comes back as one PDF of the ticket alone — from the `Order` service's `print_tix` and from `m_reprintpicktickets` with `process_doclinks` (*Transmit Document Links*) `ON` or `OFF` alike, for a kit whose links include area `3453`: same page count, same size. *Transmit Document Links* is a print-time option of the client's pick-ticket windows (`process_doclinks`, default `OFF` on play); whether the client then prints the linked file alongside the ticket was not tested here.

## Verify

```sql
SELECT dl.document_link_uid, dl.link_name, dl.link_path, dl.outside_use_flag, a.display_area_cd
FROM document_link dl
JOIN document_link_area a ON a.document_link_uid = dl.document_link_uid AND a.row_status_flag = 704
WHERE dl.source_area_cd = 1314 AND dl.key1_cd = 'inv_mast_uid'
  AND dl.key1_value = '<inv_mast_uid>' AND dl.row_status_flag = 704
ORDER BY dl.document_link_uid, a.display_area_cd
```

Over OData the example reads the same two tables (`document_link`, then `document_link_area` by `document_link_uid`). Expected after a run with all areas: one link and 26 area rows, `1302` and `3453` among them; with the defaults, two rows (`1314`, `1445`). Then open the assembly in Assembly Maintenance: the link is on the header Document Links tab only when `1302` is among its areas.

> **Credit:** *@mrwuss* — Item-window flow and file-handler upload found and verified on play 26.1 ([#200](https://github.com/mrwuss/p21-api-documentation/issues/200)); display areas, assemblies and kits, and the pick-ticket check verified on play 26.1.5950.0, 2026-10-17.
