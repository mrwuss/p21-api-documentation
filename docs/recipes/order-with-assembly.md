# Order with an Assembly Line

Enter a sales order interactively when a line is an assembly that must explode into components and/or spawn a production order.

**API:** Interactive · **Service:** `Order` (window) · **Deep dive:** [Sales Order Entry with Assembly Lines](../04-Interactive-API.md#sales-order-entry-with-assembly-lines) · [Response Windows](../04-Interactive-API.md#response-windows) · **Full schema:** [Order.json](../../definitions/Order.json)

## Prerequisites

- Token + UI server URL (shared auth helper — see the [recipes README](README.md)).
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
BASE_URL = "https://play.p21server.com"
USERNAME = "api_user"
PASSWORD = "api_pass"

token, ui_server, headers = p21_auth(BASE_URL, USERNAME, PASSWORD)
iapi = f"{ui_server}/api/ui/interactive"


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


def answer_response_windows(result: dict, button: str | None = None) -> dict:
    """Answer every popup the last action opened, then return the last result.

    Discovers buttons via GET /v2/tools?windowId= (the tools endpoint takes
    ?windowId=, NOT ?id=), then clicks via POST /v2/tools with the POPUP's
    window ID. If `button` is None, picks the first proceed-style button.
    """
    for popup_id in popup_ids(result):
        tools = httpx.get(
            f"{iapi}/v2/tools", params={"windowId": popup_id},
            headers=headers, verify=False,
        )
        tools.raise_for_status()
        available = [t.get("Name") or t.get("ToolName") for t in tools.json()]
        pick = button
        if pick is None:  # prefer common proceed buttons
            pick = next((b for b in ("cb_ok", "cb_1", "cb_yes") if b in available), None)
        if pick is None or pick not in available:
            raise RuntimeError(f"Popup {popup_id}: buttons {available}, wanted {button}")
        click = httpx.post(
            f"{iapi}/v2/tools", headers=headers, verify=False,
            json={"WindowId": popup_id, "ToolName": pick},
        )
        click.raise_for_status()
        result = click.json()
    return result


def change(window_id: str, tab: str, dw: str, field: str, value: str,
           answer: str | None = None) -> dict:
    """Change one field; answer the popup it triggers (if any) with `answer`."""
    resp = httpx.put(
        f"{iapi}/v2/change", headers=headers, verify=False,
        json={"WindowId": window_id, "List": [{
            "TabName": tab, "DatawindowName": dw,  # DatawindowName required on 25.2+
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
httpx.post(
    f"{iapi}/sessions", headers=headers, verify=False,
    json={"ResponseWindowHandlingEnabled": True},
).raise_for_status()

# 2. Open the Order window
win = httpx.post(
    f"{iapi}/v2/window", headers=headers, verify=False,
    json={"ServiceName": "Order"},
)
win.raise_for_status()
window_id = win.json()["WindowId"]

try:
    # 3. Header -- TABPAGE_1 / datawindow "order". quote OFF = real order.
    change(window_id, "TABPAGE_1", "order", "quote", "OFF")
    change(window_id, "TABPAGE_1", "order", "sales_loc_id", "10")
    change(window_id, "TABPAGE_1", "order", "source_loc_id", "10")
    change(window_id, "TABPAGE_1", "order", "customer_id", "100198")
    change(window_id, "TABPAGE_1", "order", "ship_to_id", "200")
    change(window_id, "TABPAGE_1", "order", "contact_id", "300")
    # Dates fire the w_response_common date-cascade prompt even on a NEW order
    change(window_id, "TABPAGE_1", "order", "order_date", "2030-01-05", answer="cb_ok")
    change(window_id, "TABPAGE_1", "order", "requested_date", "2030-01-06", answer="cb_ok")
    change(window_id, "TABPAGE_1", "order", "po_no", "PO-TEST-001")
    change(window_id, "TABPAGE_1", "order", "taker", "JSMITH")  # else = API user

    # 4. Lines tab
    httpx.put(
        f"{iapi}/v2/tab", headers=headers, verify=False,
        json={"WindowId": window_id, "PageName": "TP_ITEMS"},
    ).raise_for_status()

    # 5. Item on the EXISTING items row (no /v2/row add for the first line).
    #    Assembly prompt: cb_1 = Yes (explode / link prod order).
    change(window_id, "TP_ITEMS", "items", "oe_order_item_id", "WIDGET-001", answer="cb_1")
    # 6. Quantity
    change(window_id, "TP_ITEMS", "items", "unit_quantity", "5")

    # 7. Save -- v2 body is the bare window-ID string (an object => 422)
    save = httpx.put(f"{iapi}/v2/data", headers=headers, verify=False, json=window_id)
    save.raise_for_status()
    result = save.json()
    while is_blocked(result):  # follow-on prompts: answer with proceed button
        result = answer_response_windows(result)
    if result.get("Status") in (2, "Failure"):
        raise RuntimeError(f"Save failed: {result.get('Messages')}")

    # 8. Read order_no back. GET /v2/data returns the ACTIVE surface --
    #    switch back to the header tab first.
    httpx.put(
        f"{iapi}/v2/tab", headers=headers, verify=False,
        json={"WindowId": window_id, "PageName": "TABPAGE_1"},
    ).raise_for_status()
    data = httpx.get(
        f"{iapi}/v2/data", params={"id": window_id},
        headers=headers, verify=False,
    )
    data.raise_for_status()
    for dw in data.json():
        if dw.get("Name") == "order":
            row = dw["Data"][dw.get("ActiveRow", 0)]
            order_no = row[dw["Columns"].index("order_no")]
            print(f"Created order_no: {order_no}")
finally:
    # 9. Clean up (window uses ?id=; sessions endpoint takes no parameter)
    httpx.delete(f"{iapi}/v2/window", params={"id": window_id},
                 headers=headers, verify=False)
    httpx.delete(f"{iapi}/sessions", headers=headers, verify=False)
```

```csharp
var session = await P21Session.CreateAsync(
    "https://play.p21server.com", "api_user", "api_pass");
var http = session.Http;
var iapi = $"{session.UiServer}/api/ui/interactive";

bool IsBlocked(JObject r) =>
    r["Status"]?.ToString() is "3" or "Blocked";  // int or string form

List<string> PopupIds(JObject r) =>
    (r["Events"] as JArray ?? new JArray())
        .Where(e => e["Name"]?.ToString() == "windowopened")
        .SelectMany(e => e["Data"] as JArray ?? new JArray())
        .Where(kv => kv["Key"]?.ToString() == "windowid")
        .Select(kv => kv["Value"]!.ToString())
        .ToList();

// Answer every popup the last action opened; button null => first proceed button.
async Task<JObject> AnswerResponseWindowsAsync(JObject result, string? button = null)
{
    foreach (var popupId in PopupIds(result))
    {
        // Tools endpoint takes ?windowId=, NOT ?id=
        var toolsResp = await http.GetAsync($"{iapi}/v2/tools?windowId={popupId}");
        toolsResp.EnsureSuccessStatusCode();
        var available = JArray.Parse(await toolsResp.Content.ReadAsStringAsync())
            .Select(t => (t["Name"] ?? t["ToolName"])?.ToString()).ToList();
        var pick = button
            ?? new[] { "cb_ok", "cb_1", "cb_yes" }.FirstOrDefault(available.Contains)
            ?? throw new InvalidOperationException(
                $"Popup {popupId}: buttons [{string.Join(", ", available)}]");
        var clickBody = new JObject { ["WindowId"] = popupId, ["ToolName"] = pick };
        var clickResp = await http.PostAsync($"{iapi}/v2/tools",
            new StringContent(clickBody.ToString(), Encoding.UTF8, "application/json"));
        clickResp.EnsureSuccessStatusCode();
        result = JObject.Parse(await clickResp.Content.ReadAsStringAsync());
    }
    return result;
}

async Task<JObject> ChangeAsync(string windowId, string tab, string dw,
    string field, string value, string? answer = null)
{
    var body = new JObject
    {
        ["WindowId"] = windowId,
        ["List"] = new JArray { new JObject
        {
            ["TabName"] = tab,
            ["DatawindowName"] = dw,   // required on 25.2+
            ["FieldName"] = field,
            ["Value"] = value,
        }},
    };
    var resp = await http.PutAsync($"{iapi}/v2/change",
        new StringContent(body.ToString(), Encoding.UTF8, "application/json"));
    resp.EnsureSuccessStatusCode();
    var result = JObject.Parse(await resp.Content.ReadAsStringAsync());
    if (result["Status"]?.ToString() is "2" or "Failure")
        throw new InvalidOperationException($"{field}: {result["Messages"]}");
    return IsBlocked(result) ? await AnswerResponseWindowsAsync(result, answer) : result;
}

// 1. Session with response-window handling ON
var sessBody = new JObject { ["ResponseWindowHandlingEnabled"] = true };
(await http.PostAsync($"{iapi}/sessions",
    new StringContent(sessBody.ToString(), Encoding.UTF8, "application/json")))
    .EnsureSuccessStatusCode();

// 2. Open the Order window
var winBody = new JObject { ["ServiceName"] = "Order" };
var winResp = await http.PostAsync($"{iapi}/v2/window",
    new StringContent(winBody.ToString(), Encoding.UTF8, "application/json"));
winResp.EnsureSuccessStatusCode();
var windowId = JObject.Parse(await winResp.Content.ReadAsStringAsync())["WindowId"]!.ToString();

try
{
    // 3. Header -- TABPAGE_1 / datawindow "order". quote OFF = real order.
    await ChangeAsync(windowId, "TABPAGE_1", "order", "quote", "OFF");
    await ChangeAsync(windowId, "TABPAGE_1", "order", "sales_loc_id", "10");
    await ChangeAsync(windowId, "TABPAGE_1", "order", "source_loc_id", "10");
    await ChangeAsync(windowId, "TABPAGE_1", "order", "customer_id", "100198");
    await ChangeAsync(windowId, "TABPAGE_1", "order", "ship_to_id", "200");
    await ChangeAsync(windowId, "TABPAGE_1", "order", "contact_id", "300");
    // Dates fire the w_response_common date-cascade prompt even on a NEW order
    await ChangeAsync(windowId, "TABPAGE_1", "order", "order_date", "2030-01-05", "cb_ok");
    await ChangeAsync(windowId, "TABPAGE_1", "order", "requested_date", "2030-01-06", "cb_ok");
    await ChangeAsync(windowId, "TABPAGE_1", "order", "po_no", "PO-TEST-001");
    await ChangeAsync(windowId, "TABPAGE_1", "order", "taker", "JSMITH"); // else = API user

    // 4. Lines tab
    var tabBody = new JObject { ["WindowId"] = windowId, ["PageName"] = "TP_ITEMS" };
    (await http.PutAsync($"{iapi}/v2/tab",
        new StringContent(tabBody.ToString(), Encoding.UTF8, "application/json")))
        .EnsureSuccessStatusCode();

    // 5. Item on the EXISTING items row; assembly prompt: cb_1 = Yes (explode)
    await ChangeAsync(windowId, "TP_ITEMS", "items", "oe_order_item_id", "WIDGET-001", "cb_1");
    // 6. Quantity
    await ChangeAsync(windowId, "TP_ITEMS", "items", "unit_quantity", "5");

    // 7. Save -- v2 body is the bare window-ID JSON string (an object => 422)
    var saveResp = await http.PutAsync($"{iapi}/v2/data",
        new StringContent(JsonConvert.SerializeObject(windowId), Encoding.UTF8, "application/json"));
    saveResp.EnsureSuccessStatusCode();
    var result = JObject.Parse(await saveResp.Content.ReadAsStringAsync());
    while (IsBlocked(result))  // follow-on prompts: answer with proceed button
        result = await AnswerResponseWindowsAsync(result);
    if (result["Status"]?.ToString() is "2" or "Failure")
        throw new InvalidOperationException($"Save failed: {result["Messages"]}");

    // 8. Read order_no back -- /v2/data returns the ACTIVE surface, so
    //    switch back to the header tab first.
    var backBody = new JObject { ["WindowId"] = windowId, ["PageName"] = "TABPAGE_1" };
    (await http.PutAsync($"{iapi}/v2/tab",
        new StringContent(backBody.ToString(), Encoding.UTF8, "application/json")))
        .EnsureSuccessStatusCode();
    var dataResp = await http.GetAsync($"{iapi}/v2/data?id={windowId}");
    dataResp.EnsureSuccessStatusCode();
    foreach (var dw in JArray.Parse(await dataResp.Content.ReadAsStringAsync()))
    {
        if (dw["Name"]?.ToString() != "order") continue;
        var columns = (dw["Columns"] as JArray)!.Select(c => c.ToString()).ToList();
        var row = (dw["Data"] as JArray)![(int?)dw["ActiveRow"] ?? 0];
        Console.WriteLine($"Created order_no: {row[columns.IndexOf("order_no")]}");
    }
}
finally
{
    // 9. Clean up (window uses ?id=; sessions endpoint takes no parameter)
    await http.DeleteAsync($"{iapi}/v2/window?id={windowId}");
    await http.DeleteAsync($"{iapi}/sessions");
}
```
<!-- /tabs -->

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
