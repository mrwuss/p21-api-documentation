# Interactive API

> **Disclaimer:** This is unofficial, community-created documentation for Epicor Prophet 21 APIs. It is not affiliated with, endorsed by, or supported by Epicor Software Corporation. All product names, trademarks, and registered trademarks are property of their respective owners. Use at your own risk.

---

## Overview

The Interactive API (IAPI) is a **stateful** RESTful API that simulates user interaction with P21 windows. It maintains session state, allowing you to perform complex multi-step operations with full business logic validation.

### Key Characteristics

- **Stateful** - Maintains session like a real user
- **Full business logic** - All validations applied
- **Window-based** - Works with P21 windows and fields
- **Response window handling** - Can handle dialogs
- **Complex workflows** - Multi-step operations supported

### When to Use

- Complex data entry requiring business logic
- Multi-step workflows with dependencies
- Operations that trigger response windows
- When you need to interact like a real user

---

## Endpoints

All Interactive API endpoints use the UI Server URL. First, obtain it:

```http
GET https://{hostname}/api/ui/router/v1?urlType=external
```

Then use the returned URL as base:

### Session Management

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/ui/interactive/sessions` | POST | Create new session |
| `/api/ui/interactive/sessions` | GET | List open sessions |
| `/api/ui/interactive/sessions` | DELETE | End session |

### Window Operations (v2)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/ui/interactive/v2/window` | POST | Open a window |
| `/api/ui/interactive/v2/window?id={windowId}` | GET | Get window state |
| `/api/ui/interactive/v2/window?id={windowId}` | DELETE | Close window |

### Data Operations (v2 - Recommended)

> **Important:** Some P21 servers only support v2 endpoints. If you receive 404 errors on v1 endpoints, use v2 instead.

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/ui/interactive/v2/data` | PUT | Save data |
| `/api/ui/interactive/v2/data?id={windowId}` | GET | Get active data |
| `/api/ui/interactive/v2/data?id={windowId}` | DELETE | Clear data |
| `/api/ui/interactive/v2/change` | PUT | Change field values |
| `/api/ui/interactive/v2/tab` | PUT | Change active tab |
| `/api/ui/interactive/v2/row` | POST | Add a row |
| `/api/ui/interactive/v2/row` | PUT | Change current row |
| `/api/ui/interactive/v2/rows/limits` | PUT | Set active row limits |
| `/api/ui/interactive/v2/rows/selected` | POST | Select multiple rows |
| `/api/ui/interactive/v2/tools?windowId={windowId}` | GET | Get available tools |
| `/api/ui/interactive/v2/tools` | POST | Run a tool |

> **Query Parameter Inconsistency:** Most v2 endpoints use `?id=` for the window identifier, but the **tools endpoint uses `?windowId=`**. Verified by live testing:
>
> | Endpoint | Accepts `?id=` | Accepts `?windowId=` |
> |----------|:-:|:-:|
> | GET/DELETE `/v2/window` | **Yes** | No (422) |
> | GET/DELETE `/v2/data` | **Yes** | No (400/422) |
> | GET `/v2/tools` | No (400) | **Yes** |
>
> Using the wrong parameter returns an error — there is no fallback. `GET /v2/tools?id=` fails with HTTP 400 and a validation body (`"The windowId field is required."`).

### Data Operations (v1 - Legacy)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/ui/interactive/v1/data` | PUT | Save data |
| `/api/ui/interactive/v1/data` | GET | Get active data |
| `/api/ui/interactive/v1/data` | DELETE | Clear data |
| `/api/ui/interactive/v1/change` | PUT | Change field values |
| `/api/ui/interactive/v1/tab` | PUT | Change active tab |
| `/api/ui/interactive/v1/row` | POST | Add a row |
| `/api/ui/interactive/v1/row` | PUT | Change current row |
| `/api/ui/interactive/v1/tools` | GET | Get available tools |
| `/api/ui/interactive/v1/tools` | POST | Run a tool |

---

## Authentication

Include the Bearer token in the Authorization header:

```http
POST /api/ui/interactive/sessions HTTP/1.1
Host: {ui-server-host}
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json
```

See [Authentication](00-Authentication.md) for token generation.

---

## Session Lifecycle

### 1. Start Session

```json
POST /api/ui/interactive/sessions
{
    "ResponseWindowHandlingEnabled": false
}
```

Response:
```json
{
    "SessionId": "abc123...",
    "Status": "Active"
}
```

#### Session Parameters (UserParameters)

The session creation body accepts these optional parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `SessionType` | string | `"User"` | `User` (real user login), `Auto` (automated process), or `AutoInteractive` (automated without noninteractive API profile). Affects license consumption and behavior |
| `SessionTimeout` | int | Server default (60s) | Inactivity timeout in seconds before the session is cleaned up |
| `ResponseWindowHandlingEnabled` | bool | `true` | When `false`, response windows (dialogs) are auto-answered with the default response (usually "Yes"). Set to `true` if you need to inspect and handle dialogs yourself |
| `ClientPlatformApp` | string | null | Identifier for your application (useful for server-side logging) |
| `WorkstationID` | string | null | User-defined value to identify the PC or device initiating the session |

**Example with multiple parameters:**

```json
POST /api/ui/interactive/sessions
{
    "SessionType": "Auto",
    "SessionTimeout": 120,
    "ResponseWindowHandlingEnabled": false,
    "ClientPlatformApp": "PricePageSync",
    "WorkstationID": "INTEGRATION-01"
}
```

> **Session pool limits:** The server has a finite pool of API instances (default: 5). If all instances are busy, new session requests will wait up to 60 seconds before timing out. See [Session Pool Troubleshooting](07-Session-Pool-Troubleshooting.md) for configuration details and common issues.

### 2. Open Window

There are four ways to identify which window to open:

| Method | Field | Example | When to Use |
|--------|-------|---------|-------------|
| Service name | `ServiceName` | `"SalesPricePage"` | Most reliable for multi-transaction windows (recommended) |
| Menu title | `Title` | `"Sales Price Page Entry"` | Matches the menu label text in P21 |
| Window name | `Name` | `"w_sales_price_page"` | Internal window name (if known) |
| Menu ID | `MenuId` | `12345` | Numeric menu ID from P21 |

```json
POST /api/ui/interactive/v2/window
{
    "ServiceName": "SalesPricePage"
}
```

Or by menu title:
```json
{
    "Title": "Sales Price Page Entry"
}
```

Response:
```json
{
    "WindowId": "w_sales_price_page",
    "Title": "Sales Price Page Entry",
    "DataElements": [...]
}
```

### 3. Change Data

**v2 Format (Recommended):**

```json
PUT /api/ui/interactive/v2/change
{
    "WindowId": "w_sales_price_page",
    "List": [
        {
            "TabName": "FORM",
            "FieldName": "description",
            "Value": "New Description",
            "DatawindowName": "form"
        }
    ]
}
```

> **Note:** v2 uses `List` with `TabName`, while v1 uses `ChangeRequests` with `DataWindowName`. The `DatawindowName` field in v2 uses lowercase 'w'.

> **P21 25.2+ Breaking Change:** `DatawindowName` is now effectively **required** for v2 change requests. The 3-parameter form (TabName + FieldName + Value) stopped working after the 25.2 upgrade — you must include `DatawindowName` as the 4th field. Window data structures changed in 25.2 so the server can no longer auto-resolve the target datawindow from TabName alone. **Always include `DatawindowName` in change requests.**
>
> **Affected windows (confirmed):**
>
> | Window | Affected Field | Reporter |
> |--------|---------------|----------|
> | Item | Various | Community reports |
> | PO Receiving Group | `po_criteria_id` on `Criteria` tab | Jeff Patterson, Josiah Shollenberger |
> | Delivery List | Various | Community reports |
> | Group Pick Ticket | Various | Community reports |
> | ConvertPOToVoucher | `po_no` on `Voucher Information` tab | Jeff Patterson, Josiah Shollenberger |
> | Order Entry | `order_no` on `Order` tab | Neil Timmerman |
> | Clippership Auto Shipping | `pick_ticket_no` | Josh Owen |
> | Doc Links | Various | Jaime Nelson |
>
> The bug persists through at least version **25.2.5776.1**. Epicor has acknowledged this as a development bug.

**Fix example (C# SDK):**

```csharp
// Broken in 25.2+:
porgwindow.ChangeData("Criteria", "po_criteria_id", "20");

// Fixed — include DatawindowName:
porgwindow.ChangeData("Criteria", "tp_1_dw_1", "po_criteria_id", "20");
```

> *Credit: David Sokoloski (first discovered 4-param workaround), Jeff Patterson (confirmed fix)*

#### ValueType

Each change request supports an optional `ValueType` field:

| ValueType | Description |
|-----------|-------------|
| `"Display"` | The value as it appears on screen (default if omitted) |
| `"Data"` | The raw data value (e.g., internal key instead of display text) |

```json
{
    "TabName": "FORM",
    "FieldName": "supplier_id",
    "Value": "10050",
    "ValueType": "Data"
}
```

Most of the time you can omit `ValueType` — the default `Display` works for typical field changes. Use `Data` when you need to set a field by its internal key value rather than its display text.

**v1 Format (Legacy):**

```json
PUT /api/ui/interactive/v1/change
{
    "WindowId": "w_sales_price_page",
    "ChangeRequests": [
        {
            "DataWindowName": "d_form",
            "FieldName": "description",
            "Value": "New Description"
        }
    ]
}
```

### 4. Save Data

**v2 Format (Recommended):**

```json
PUT /api/ui/interactive/v2/data
"w_sales_price_page"
```

> **Critical:** In v2, send just the WindowId GUID string as the JSON body - NOT wrapped in an object. This is a common source of 422 errors.

**v1 Format (Legacy):**

```json
PUT /api/ui/interactive/v1/data
{
    "WindowId": "w_sales_price_page"
}
```

### 5. Close Window

```json
DELETE /api/ui/interactive/v2/window?id=w_sales_price_page
```

### 6. End Session

```json
DELETE /api/ui/interactive/sessions
```

---

## Finding Field Names

To find the correct field and datawindow names:

1. Open P21 in the web client
2. Navigate to the window
3. Right-click on the field
4. Select **Help > SQL Information**
5. Note the datawindow name and column name

---

## Window Discovery Techniques

> **Source**: Community working code + actual API testing (April 2026). Credit: Jon Christie.

Understanding a window's structure is essential before automating it. These techniques help you discover datawindow names, field names, available tools, and current data.

### 1. Get Window State

After opening a window, call `GetState()` (SDK) or `GET /api/ui/interactive/v2/window?id={windowId}` (REST) to retrieve the full window definition. This returns all datawindows, fields, tabs, enabled states, and current data structure.

<!-- tabs -->

#### Python

```python
async def get_window_state(
    client: httpx.AsyncClient,
    ui_url: str,
    headers: dict[str, str],
    window_id: str,
) -> dict:
    """Get full window state including datawindows, fields, and tabs.

    Args:
        client: httpx async client.
        ui_url: UI server base URL.
        headers: Request headers with auth token.
        window_id: The window ID to inspect.

    Returns:
        Parsed window definition dict.
    """
    response = await client.get(
        f"{ui_url}/api/ui/interactive/v2/window",
        headers=headers,
        params={"id": window_id},
    )
    response.raise_for_status()
    state = response.json()

    # Enumerate datawindows and their fields
    for dw in state.get("Datawindows", []):
        dw_name = dw.get("Name")
        parent_tab = dw.get("ParentPage")
        fields = [f.get("Name") for f in dw.get("Fields", [])]
        logger.info(
            "Datawindow %s (tab: %s) — fields: %s",
            dw_name, parent_tab, fields,
        )

    return state
```

#### C\#

```csharp
public async Task<JObject> GetWindowStateAsync(
    HttpClient http,
    string uiUrl,
    string windowId)
{
    // Get full window state including datawindows, fields, and tabs.
    var response = await http.GetAsync(
        $"{uiUrl}/api/ui/interactive/v2/window?id={windowId}");
    response.EnsureSuccessStatusCode();

    var state = JObject.Parse(await response.Content.ReadAsStringAsync());

    // Enumerate datawindows and their fields
    foreach (var dw in state["Datawindows"] ?? new JArray())
    {
        var dwName = dw["Name"]?.ToString();
        var parentTab = dw["ParentPage"]?.ToString();
        var fields = (dw["Fields"] as JArray)?
            .Select(f => f["Name"]?.ToString())
            .ToList() ?? new List<string?>();

        _logger.LogInformation(
            "Datawindow {DwName} (tab: {ParentTab}) — fields: {Fields}",
            dwName, parentTab, string.Join(", ", fields));
    }

    return state;
}
```

<!-- /tabs -->

**Example response** (sanitized, structure varies by window):

```json
{
  "Definition": {
    "Title": "Order Entry",
    "Datawindows": {
      "form": {
        "Fields": {
          "order_no": {"Label": "Order No", "Enabled": true, "DataType": 1},
          "customer_id": {"Label": "Customer ID", "Enabled": true, "DataType": 1}
        }
      }
    },
    "TabPageList": [
      {"Name": "Order", "DisplayText": "Order"},
      {"Name": "Line_Items", "DisplayText": "Line Items"}
    ]
  }
}
```

> **Tip:** Response windows return an empty `TabPageList` — that is how you can distinguish them from normal windows programmatically.

### 2. Get Available Tools

Call `GetTools()` (SDK) or `GET /api/ui/interactive/v2/tools?windowId={windowId}` (REST) to see available buttons. Tools can be queried at window, datawindow, and field levels by adding `dwName`, `fieldName`, and `row` parameters.

**Example response:**

```json
[
  {"ToolName": "cb_ok", "DatawindowName": null, "FieldName": null},
  {"ToolName": "cb_cancel", "DatawindowName": null, "FieldName": null},
  {"ToolName": "m_addlink", "DatawindowName": "Document_Link", "FieldName": null}
]
```

### 3. Get Current Data

Call `GetData()` (SDK) or `GET /api/ui/interactive/v2/data?id={windowId}` (REST) to retrieve the current data in each datawindow on the active tab. Returns column names, row data, active row index, and total row count.

### 4. Check Result Events

Every API response includes an `Events` collection. When a response window opens, look for `Name: "windowopened"` events. When tabs become enabled, look for `Name: "tabpageenabled"` events. When a new record is saved, look for `Name: "keygenerated"` events.

### 5. P21 SQL Information

In the P21 desktop or web client, right-click any field and select **Help > SQL Information**. This dialog shows:
- **Datawindow name** — the name to use in `DatawindowName` for change requests
- **Column name** — the field name to use in `FieldName`
- **Table name** — the underlying database table

This is the most reliable way to determine the exact names the API expects.

### 6. Browser DevTools

When using the P21 Web Client, open your browser's Developer Tools (F12) and watch the **Network** tab. Every action you perform in the UI generates REST calls to the Interactive API. This lets you see the exact payloads, endpoints, and field names the web client uses — which you can replicate in your automation.

### 7. Transaction API Service Definition

For windows that also exist as Transaction API services (Order, PurchaseOrder, Item, etc.), `GET /api/v2/definition/{ServiceName}` returns the full schema: every DataElement with its `DatawindowName`, `Type` (`Form`/`List`), `KeyFields`, and `FieldDefinitions[]` (field `Name`, `DbColumnName`, `DataType`, `Required`). This is the fastest way to enumerate which datawindows exist and which column names a write needs. See [Get Service Definition](03-Transaction-API.md#get-service-definition) in the Transaction API guide.

> **Warning — don't derive `TABPAGE_N` from the visible tab order:** The `TABPAGE_N` names are **not** sequential with the tabs you see in the UI. The PurchaseOrder window, for example, has 37 tab pages — many disabled or hidden, split across the header and detail bands — so the Items grid that *looks* like the second tab is actually `TABPAGE_17` (`tp_17_dw_17`). Counting visible tabs gives you the wrong name. Read the `TabPageList` from the window state (`GET /api/ui/interactive/v2/window?id={windowId}`) or cross-reference on the **datawindow name** (`tp_N_dw_N` / `d_...`). On the servers tested (25.2/26.x), the Interactive window's `TABPAGE_N` names matched the Transaction API definition's 1:1 — the datawindow name remains the safest identifier either way.

---

## Response Windows

Response windows (dialogs) can pop up during operations. When this happens:

1. The result will have `Status: 3` (Blocked)
2. Check the `Events` array for `windowopened`
3. Get the new window ID from the event data
4. Handle the response window (interact with it like any other window)
5. Close/dismiss it to resume the original operation

> **Status codes** match the `ResultStatus` enum in `P21.UI.Service.Model.Interactive.V2.ResultWrapper`:
> `None=0, Success=1, Failure=2, Blocked=3`.
> The API returns Status as an integer. String values (`"Success"`, `"Failure"`, `"Blocked"`) may appear in some contexts — handle both.

Example response with blocked status:
```json
{
    "Status": 3,
    "Events": [
        {
            "Name": "windowopened",
            "Data": [
                { "Key": "windowid", "Value": "w_response_123" }
            ]
        }
    ]
}
```

> **Note:** The `Events[].Data` field uses a key-value list format:
> `[{"Key": "windowid", "Value": "..."}]`

### Response Window Handling (Tabless Windows)

Response windows (popup dialogs) have **no tabs**. When you receive `Status: 3` (Blocked), a response window has appeared and you must interact with it before continuing. The critical difference from normal windows is that change requests on response windows require `TabName = null` because there are no tabs to reference.

**REST API pattern:**

Include `"TabName": null` in the change request payload:

```json
PUT /api/ui/interactive/v2/change
{
    "WindowId": "w_response_123",
    "List": [
        {
            "TabName": null,
            "DatawindowName": "datawindow_name",
            "FieldName": "field_name",
            "Value": "value"
        }
    ]
}
```

**REST examples (Python / C#):**

<!-- tabs -->

#### Python

```python
async def change_response_window_field(
    client: httpx.AsyncClient,
    ui_url: str,
    headers: dict[str, str],
    response_window_id: str,
    datawindow_name: str,
    field_name: str,
    value: str,
) -> dict:
    """Change a field on a tabless response window.

    Args:
        client: httpx async client.
        ui_url: UI server base URL.
        headers: Request headers with auth token.
        response_window_id: The response window ID from the windowopened event.
        datawindow_name: Datawindow name within the response window.
        field_name: Field to change.
        value: New value.

    Returns:
        Parsed response dict.
    """
    response = await client.put(
        f"{ui_url}/api/ui/interactive/v2/change",
        headers=headers,
        json={
            "WindowId": response_window_id,
            "List": [
                {
                    "TabName": None,
                    "DatawindowName": datawindow_name,
                    "FieldName": field_name,
                    "Value": value,
                }
            ],
        },
    )
    response.raise_for_status()
    return response.json()
```

#### C\#

```csharp
public async Task<JObject> ChangeResponseWindowFieldAsync(
    HttpClient http,
    string uiUrl,
    string responseWindowId,
    string datawindowName,
    string fieldName,
    string value)
{
    // Response windows have no tabs — set TabName to null
    var payload = new JObject
    {
        ["WindowId"] = responseWindowId,
        ["List"] = new JArray
        {
            new JObject
            {
                ["TabName"] = null,
                ["DatawindowName"] = datawindowName,
                ["FieldName"] = fieldName,
                ["Value"] = value
            }
        }
    };
    var content = new StringContent(payload.ToString(), Encoding.UTF8, "application/json");
    var response = await http.PutAsync($"{uiUrl}/api/ui/interactive/v2/change", content);
    response.EnsureSuccessStatusCode();

    return JObject.Parse(await response.Content.ReadAsStringAsync());
}
```

<!-- /tabs -->

> **Note:** The `TabName: null` pattern applies to response windows that accept change requests (editable dialogs with Status: 3/Blocked). `w_message` dialogs cannot be edited programmatically. Use `ResponseWindowHandlingEnabled: false` in the session configuration to auto-answer message box dialogs with their default button.

**Common response window buttons:** `cb_ok`, `cb_cancel`, `cb_finish`, `cb_yes`, `cb_no`

Use `GET /api/ui/interactive/v2/tools?windowId={responseWindowId}` to discover which buttons are available, then `POST /api/ui/interactive/v2/tools` to click them. See the [Response Window Types](#response-window-types) section below for dismissal patterns.

*Credit: Jon Christie*

### Worked Example: "Item Issues Detected" (rule callback)

A concrete `w_rule_callback_response` case from the Item window. Items with data problems pop an **"Item Issues Detected"** dialog; the Transaction API cannot get past it (the change is discarded — see [Item Service gotchas](03-Transaction-API.md#item-service-gotchas)). Interactively, it's answerable:

1. Start the session with `ResponseWindowHandlingEnabled: true`.
2. Open the `Item` window and set `item_id` on `TABPAGE_1.tp_1_dw_1`. **Some items pop the dialog at retrieve time** — the moment `item_id` is set — which blocks the location list from loading. Check the result for a `windowopened` event and answer the popup immediately, not just at save.
3. Navigate and make your edits (e.g. select the location row on `TABPAGE_17.invloclist`, edit `TABPAGE_18.inv_loc_detail`).
4. `save()` — if the dialog opens, the result is Status 3 (Blocked) with a `windowopened` event carrying the popup's window ID.
5. Discover the buttons with `GET /v2/tools?windowId={popupId}`: `cb_1` = **"Yes, Proceed Anyway"**, `cb_2` = "No, Cancel". Run `cb_1` via `POST /v2/tools` with the popup's window ID; the save then commits.

Which items trip the rule depends on each item's data state and differs between environments — don't hard-code a fallback list; run the Transaction API first, verify what stuck, and drive the exceptions interactively.

> **Credit:** [Alex Westemeier](https://github.com/AWestemeier).

---

## Changing Tabs

Before changing fields on a different tab, select the tab first:

**v2 Format (Recommended):**

```json
PUT /api/ui/interactive/v2/tab
{
    "WindowId": "w_sales_price_page",
    "PageName": "VALUES"
}
```

> **Note:** In v2, use `PageName` directly. In v1, use `PagePath: { PageName: "..." }`.

**v1 Format (Legacy):**

```json
PUT /api/ui/interactive/v1/tab
{
    "WindowId": "w_sales_price_page",
    "PagePath": {
        "PageName": "VALUES"
    }
}
```

---

## Running Tools (Buttons)

Tools include all buttons and right-click (RMB) options available at any point in a session. They exist at three levels:

1. **Window level** — Ribbon buttons, window-level buttons
2. **Datawindow level** — Grid/form buttons, RMB options on a datawindow
3. **Field level** — Field-specific RMB options

### Get Available Tools

Query tools at different levels by specifying optional parameters:

```http
GET /api/ui/interactive/v2/tools?windowId=w_sales_price_page
GET /api/ui/interactive/v2/tools?windowId=w_sales_price_page&dwName=form
GET /api/ui/interactive/v2/tools?windowId=w_sales_price_page&dwName=form&fieldName=description&row=0
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `windowId` | Yes | Window ID |
| `dwName` | No | Datawindow name — returns datawindow-level tools |
| `fieldName` | No | Field name — returns field-level tools |
| `row` | No | Row number — for grid-specific tools |

### Run a Tool

```json
POST /api/ui/interactive/v2/tools
{
    "WindowId": "w_sales_price_page",
    "ToolName": "cb_save",
    "ToolText": "Save"
}
```

For datawindow or field-level tools, include the optional fields:

```json
{
    "WindowId": "w_sales_price_page",
    "ToolName": "tool_name",
    "ToolText": "Tool Label",
    "DatawindowName": "form",
    "FieldName": "description",
    "Row": 0
}
```

---

## Python and C# Examples

### Basic Client Class

<!-- tabs -->

#### Python

```python
import httpx

class InteractiveClient:
    def __init__(self, base_url, username, password, verify_ssl=False):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.token = None
        self.ui_server_url = None

    def authenticate(self):
        response = httpx.post(
            f"{self.base_url}/api/security/token/v2",
            json={"username": self.username, "password": self.password},
            verify=self.verify_ssl
        )
        response.raise_for_status()
        self.token = response.json()["AccessToken"]

    def get_ui_server(self):
        response = httpx.get(
            f"{self.base_url}/api/ui/router/v1?urlType=external",
            headers={"Authorization": f"Bearer {self.token}"},
            verify=self.verify_ssl
        )
        response.raise_for_status()
        self.ui_server_url = response.json()["Url"].rstrip("/")

    def start_session(self):
        response = httpx.post(
            f"{self.ui_server_url}/api/ui/interactive/sessions/",
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            },
            json={"ResponseWindowHandlingEnabled": False},
            verify=self.verify_ssl
        )
        response.raise_for_status()

    def end_session(self):
        httpx.delete(
            f"{self.ui_server_url}/api/ui/interactive/sessions/",
            headers={"Authorization": f"Bearer {self.token}"},
            verify=self.verify_ssl
        )
```

#### C#

```csharp
using System.Net.Http;
using System.Net.Http.Headers;
using Newtonsoft.Json.Linq;

public class InteractiveClient
{
    private readonly string _baseUrl;
    private readonly string _username;
    private readonly string _password;
    private readonly HttpClient _http;
    private string? _token;
    private string? _uiServerUrl;

    public InteractiveClient(string baseUrl, string username, string password, bool verifySsl = false)
    {
        _baseUrl = baseUrl.TrimEnd('/');
        _username = username;
        _password = password;

        var handler = new HttpClientHandler();
        if (!verifySsl)
            handler.ServerCertificateCustomValidationCallback = (_, _, _, _) => true;

        _http = new HttpClient(handler);
    }

    public async Task AuthenticateAsync()
    {
        var body = new JObject { ["username"] = _username, ["password"] = _password };
        var content = new StringContent(body.ToString(), System.Text.Encoding.UTF8, "application/json");
        var response = await _http.PostAsync($"{_baseUrl}/api/security/token/v2", content);
        response.EnsureSuccessStatusCode();

        var parsed = JObject.Parse(await response.Content.ReadAsStringAsync());
        _token = parsed["AccessToken"]!.ToString();
        _http.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", _token);
    }

    public async Task GetUiServerAsync()
    {
        var response = await _http.GetAsync($"{_baseUrl}/api/ui/router/v1?urlType=external");
        response.EnsureSuccessStatusCode();

        var body = JObject.Parse(await response.Content.ReadAsStringAsync());
        _uiServerUrl = body["Url"]!.ToString().TrimEnd('/');
    }

    public async Task StartSessionAsync()
    {
        var payload = new JObject { ["ResponseWindowHandlingEnabled"] = false };
        var content = new StringContent(payload.ToString(), System.Text.Encoding.UTF8, "application/json");

        var response = await _http.PostAsync($"{_uiServerUrl}/api/ui/interactive/sessions", content);
        response.EnsureSuccessStatusCode();
    }

    public async Task EndSessionAsync()
    {
        await _http.DeleteAsync($"{_uiServerUrl}/api/ui/interactive/sessions");
    }
}
```

<!-- /tabs -->

### Context Manager / Disposable Usage (Sync)

<!-- tabs -->

#### Python

```python
class InteractiveClient:
    # ... methods above ...

    def __enter__(self):
        self.authenticate()
        self.get_ui_server()
        self.start_session()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.end_session()
        except Exception:
            pass
        return False

# Usage
with InteractiveClient(base_url, username, password) as client:
    window = client.open_window("SalesPricePage")
    window.change_data("description", "New Value")
    window.save()
    window.close()
```

#### C#

```csharp
public class InteractiveClient : IDisposable
{
    // ... fields and methods above ...

    public InteractiveClient Connect()
    {
        AuthenticateAsync().GetAwaiter().GetResult();
        GetUiServerAsync().GetAwaiter().GetResult();
        StartSessionAsync().GetAwaiter().GetResult();
        return this;
    }

    public void Dispose()
    {
        try { EndSessionAsync().GetAwaiter().GetResult(); }
        catch (Exception) { /* ignored */ }
        _http.Dispose();
    }
}

// Usage
using var client = new InteractiveClient(baseUrl, username, password).Connect();
var window = client.OpenWindow("SalesPricePage");
window.ChangeData("description", "New Value");
window.Save();
window.Close();
```

<!-- /tabs -->

### Async Context Manager / IAsyncDisposable (Recommended)

For production code, use async patterns with proper cleanup:

<!-- tabs -->

#### Python

```python
import httpx
import logging

logger = logging.getLogger(__name__)

class P21Client:
    def __init__(
        self, base_url: str, username: str,
        password: str, verify_ssl: bool = True,
    ):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.token: dict | None = None
        self.ui_server_url: str | None = None
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                verify=self.verify_ssl,
                timeout=60.0,
                follow_redirects=True
            )
        return self._client

    async def authenticate(self) -> dict:
        url = f"{self.base_url}/api/security/token/v2"
        client = self._get_client()
        response = await client.post(
            url, json={"username": self.username, "password": self.password}
        )
        response.raise_for_status()
        self.token = response.json()
        return self.token

    async def start_session(self) -> None:
        if not self.token:
            await self.authenticate()
        # ... get ui_server_url and start session ...

    async def end_session(self) -> None:
        # ... end session ...
        pass

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self):
        """Async context manager entry - authenticate and start session."""
        await self.authenticate()
        await self.start_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - end session and close client."""
        try:
            await self.end_session()
        except Exception as e:
            logger.debug(f"Session cleanup error (ignored): {e}")
        await self.close()
        return False

# Usage
async with P21Client(base_url, username, password) as client:
    window = await client.open_window(service_name="SalesPricePage")
    await window.change_data("FORM", "description", "New Value", datawindow_name="form")
    await window.save_data()
    await window.close()
```

#### C#

```csharp
using System.Net.Http;
using System.Net.Http.Headers;
using Microsoft.Extensions.Logging;
using Newtonsoft.Json.Linq;

public class P21Client : IAsyncDisposable
{
    private readonly string _baseUrl;
    private readonly string _username;
    private readonly string _password;
    private readonly ILogger<P21Client> _logger;
    private HttpClient? _http;
    private string? _token;
    private string? _uiServerUrl;

    public P21Client(string baseUrl, string username, string password,
                     bool verifySsl = true, ILogger<P21Client>? logger = null)
    {
        _baseUrl = baseUrl.TrimEnd('/');
        _username = username;
        _password = password;
        _logger = logger ?? Microsoft.Extensions.Logging.Abstractions.NullLogger<P21Client>.Instance;

        var handler = new HttpClientHandler();
        if (!verifySsl)
            handler.ServerCertificateCustomValidationCallback = (_, _, _, _) => true;

        _http = new HttpClient(handler) { Timeout = TimeSpan.FromSeconds(60) };
    }

    public async Task<JObject> AuthenticateAsync()
    {
        var body = new JObject { ["username"] = _username, ["password"] = _password };
        var content = new StringContent(body.ToString(), System.Text.Encoding.UTF8, "application/json");
        var response = await _http!.PostAsync($"{_baseUrl}/api/security/token/v2", content);
        response.EnsureSuccessStatusCode();

        var parsed = JObject.Parse(await response.Content.ReadAsStringAsync());
        _token = parsed["AccessToken"]!.ToString();
        _http.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", _token);
        return parsed;
    }

    public async Task StartSessionAsync()
    {
        if (_token == null)
            await AuthenticateAsync();
        // ... get uiServerUrl and start session ...
    }

    public async Task EndSessionAsync()
    {
        // ... end session ...
    }

    public async ValueTask DisposeAsync()
    {
        try
        {
            await EndSessionAsync();
        }
        catch (Exception ex)
        {
            _logger.LogDebug(ex, "Session cleanup error (ignored)");
        }

        _http?.Dispose();
        _http = null;
    }
}

// Usage
await using var client = new P21Client(baseUrl, username, password);
await client.AuthenticateAsync();
await client.StartSessionAsync();
var window = await client.OpenWindowAsync(serviceName: "SalesPricePage");
await window.ChangeDataAsync("FORM", "description", "New Value", datawindowName: "form");
await window.SaveDataAsync();
await window.CloseAsync();
```

<!-- /tabs -->

**Key points for async usage:**

1. Use `httpx.AsyncClient` (Python) or `HttpClient` with `async`/`await` (C#)
2. Implement `__aenter__`/`__aexit__` (Python) or `IAsyncDisposable` (C#)
3. Always close the HTTP client on disposal
4. Ignore cleanup errors - session may have timed out
5. Use `async with` (Python) or `await using` (C#) for guaranteed cleanup

---

## Working Example Scripts

See the `scripts/interactive/` directory:

| Script | Description |
|--------|-------------|
| `01_open_session.py` | Session lifecycle |
| `02_open_window.py` | Open and close windows |
| `03_change_data.py` | Change field values |
| `04_save_and_close.py` | Complete save workflow |
| `05_response_windows.py` | Handle response dialogs |
| `06_complex_workflow.py` | Multi-step example |

---

## Common Windows

| Window Title | Service Name | Purpose |
|--------------|--------------|---------|
| Customer Maintenance | Customer | Customer records |
| Order Entry | Order | Sales orders |
| Invoice Entry | Invoice | Invoices |
| Supplier Maintenance | Supplier | Supplier records |
| Sales Price Page Entry | SalesPricePage | Price pages ([dropdown codes](08-SalesPricePage-Codes.md)) |
| Sales Price Book Entry | SalesPriceBook | Price book maintenance |
| Purchase Order Entry | PurchaseOrder | Purchase orders |
| Inventory Maintenance | InventoryMaster | Inventory items |

### Production & Labor Windows

| Window Title | Service Name | Purpose |
|--------------|--------------|---------|
| Production Order Entry | ProductionOrder | Full production order management |
| Time Entry | TimeEntry | Record labor hours against production orders |
| Time Entry (Service Order) | TimeEntrySO | Record labor hours against service orders |
| Labor Maintenance | Labor | Labor code definitions and rates |
| Labor Process Maintenance | LaborProcess | Labor process templates |
| Job Maintenance | Job | Job CRUD |
| Job Control Maintenance | JobControl | Job sites and contacts |
| Operation Maintenance | Operation | Operation definitions |
| Predefined Routing | PredefinedRouting | Routing templates |
| Assembly Maintenance | Assembly | Assembly definitions |
| Manufacturing Class | ManufacturingClass | Manufacturing classification |
| Shift Maintenance | Shift | Shift definitions |
| Production Order Processing | ProductionOrderProcessing | Process/complete production orders |

See [Production & Labor API](12-Production-Labor-API.md) for detailed field definitions.

---

## Example: Linking Price Page to Price Book

This example shows how to use the SalesPriceBook window to link a price page to a price book. This is a common operation after creating a new price page.

<!-- tabs -->

#### Python

```python
async def link_page_to_book(
    client: P21Client,
    price_page_uid: int,
    price_book_id: str
) -> bool:
    """Link a price page to a price book via SalesPriceBook window.

    Args:
        client: Authenticated P21Client with active session
        price_page_uid: The price page UID to link
        price_book_id: The price book ID (e.g., "P2 IND_OEM_HUGE")

    Returns:
        True if successful
    """
    # Open the SalesPriceBook window
    window = await client.open_window(service_name='SalesPriceBook')

    try:
        # Step 1: Retrieve the book by ID on FORM tab
        result = await window.change_data(
            'FORM', 'price_book_id', price_book_id,
            datawindow_name='form'
        )
        if not result.success:
            logger.error(f"Failed to retrieve book {price_book_id}: {result.messages}")
            return False

        # Step 2: Switch to LIST tab
        await window.select_tab('LIST')

        # Step 3: Add a new row to the list_detail datawindow
        result = await window.add_row('list_detail')
        if not result.success:
            logger.error(f"Failed to add row: {result.messages}")
            return False

        # Step 4: Set the price_page_uid on the new row
        result = await window.change_data(
            'LIST', 'price_page_uid', str(price_page_uid),
            datawindow_name='list_detail'
        )
        if not result.success:
            logger.error(f"Failed to set price_page_uid: {result.messages}")
            return False

        # Step 5: Save the changes
        result = await window.save_data()

        if result.success:
            logger.info(f"Linked page {price_page_uid} to book {price_book_id}")
            return True
        else:
            logger.error(f"Failed to save: {result.messages}")
            return False

    finally:
        await window.close()
```

#### C#

```csharp
public async Task<bool> LinkPageToBookAsync(
    P21Client client,
    int pricePageUid,
    string priceBookId)
{
    // Open the SalesPriceBook window
    var window = await client.OpenWindowAsync(serviceName: "SalesPriceBook");

    try
    {
        // Step 1: Retrieve the book by ID on FORM tab
        var result = await window.ChangeDataAsync(
            "FORM", "price_book_id", priceBookId,
            datawindowName: "form");
        if (!result.Success)
        {
            _logger.LogError("Failed to retrieve book {BookId}: {Messages}",
                priceBookId, result.Messages);
            return false;
        }

        // Step 2: Switch to LIST tab
        await window.SelectTabAsync("LIST");

        // Step 3: Add a new row to the list_detail datawindow
        result = await window.AddRowAsync("list_detail");
        if (!result.Success)
        {
            _logger.LogError("Failed to add row: {Messages}", result.Messages);
            return false;
        }

        // Step 4: Set the price_page_uid on the new row
        result = await window.ChangeDataAsync(
            "LIST", "price_page_uid", pricePageUid.ToString(),
            datawindowName: "list_detail");
        if (!result.Success)
        {
            _logger.LogError("Failed to set price_page_uid: {Messages}", result.Messages);
            return false;
        }

        // Step 5: Save the changes
        result = await window.SaveDataAsync();

        if (result.Success)
        {
            _logger.LogInformation("Linked page {PageUid} to book {BookId}",
                pricePageUid, priceBookId);
            return true;
        }
        else
        {
            _logger.LogError("Failed to save: {Messages}", result.Messages);
            return false;
        }
    }
    finally
    {
        await window.CloseAsync();
    }
}
```

<!-- /tabs -->

**Key points:**

1. Open window by `ServiceName`, not title
2. Retrieve the book first - this loads it into the window
3. Switch to LIST tab before adding/modifying rows
4. Use `add_row('list_detail')` to add a new link row
5. Set `price_page_uid` as a string value
6. Always close the window in a `finally` block

### Price Book Naming and Lookup Strategies

In production P21 environments, price book names are often inconsistent. For example, the same conceptual book might be named differently across environments or suppliers:

- `P2 IND_OEM_LARGE`
- `P2_JOBBER_HUGE`
- `P2_TP_Huge`

**Strategy: Case-Insensitive OData Lookup**

Use `contains()` with case-insensitive matching to find books by partial name:

<!-- tabs -->

#### Python

```python
async def find_price_book(
    odata_client: ODataClient,
    search_terms: list[str],
) -> dict | None:
    """Find a price book by trying multiple naming patterns.

    Args:
        odata_client: OData API client
        search_terms: List of partial names to try (e.g., ["IND_OEM", "JOBBER"])

    Returns:
        Price book record or None
    """
    for term in search_terms:
        filter_expr = (
            f"contains(price_book_id,'{term}') "
            f"and row_status_flag eq 704"
        )
        results = await odata_client.query(
            "price_book",
            filter_expr=filter_expr,
            select="price_book_id,description",
        )
        if results:
            return results[0]
    return None
```

#### C#

```csharp
public async Task<JObject?> FindPriceBookAsync(
    ODataClient odataClient,
    IEnumerable<string> searchTerms)
{
    foreach (var term in searchTerms)
    {
        var filterExpr = $"contains(price_book_id,'{term}') and row_status_flag eq 704";
        var results = await odataClient.QueryAsync(
            "price_book",
            filterExpr: filterExpr,
            select: "price_book_id,description");

        if (results.Count > 0)
            return results[0];
    }
    return null;
}
```

<!-- /tabs -->

**Strategy: Library-to-Book Resolution**

Price books are organized into libraries. Use the `price_book_x_library` junction table to resolve which books belong to a library:

<!-- tabs -->

#### Python

```python
async def get_books_for_library(
    odata_client: ODataClient,
    library_id: str,
) -> list[dict]:
    """Get all price books linked to a library."""
    links = await odata_client.query(
        "price_book_x_library",
        filter_expr=f"price_library_uid eq {library_id}",
        select="price_book_uid",
    )
    book_uids = [link["price_book_uid"] for link in links]

    books = []
    for uid in book_uids:
        result = await odata_client.query(
            "price_book",
            filter_expr=f"price_book_uid eq {uid} and row_status_flag eq 704",
            select="price_book_id,price_book_uid,description",
        )
        if result:
            books.append(result[0])
    return books
```

#### C#

```csharp
public async Task<List<JObject>> GetBooksForLibraryAsync(
    ODataClient odataClient,
    string libraryId)
{
    var links = await odataClient.QueryAsync(
        "price_book_x_library",
        filterExpr: $"price_library_uid eq {libraryId}",
        select: "price_book_uid");

    var bookUids = links.Select(l => l["price_book_uid"]!.ToString()).ToList();
    var books = new List<JObject>();

    foreach (var uid in bookUids)
    {
        var result = await odataClient.QueryAsync(
            "price_book",
            filterExpr: $"price_book_uid eq {uid} and row_status_flag eq 704",
            select: "price_book_id,price_book_uid,description");

        if (result.Count > 0)
            books.Add(result[0]);
    }
    return books;
}
```

<!-- /tabs -->

**Strategy: Cache Library-to-Book Mapping**

For bulk operations that link many pages to books, cache the library-to-book mapping to avoid N+1 queries:

<!-- tabs -->

#### Python

```python
class BookLookupCache:
    """Cache library-to-book mappings for bulk operations."""

    def __init__(self, odata_client: ODataClient):
        self.odata = odata_client
        self._cache: dict[str, list[dict]] = {}

    async def get_books(self, library_id: str) -> list[dict]:
        if library_id not in self._cache:
            self._cache[library_id] = await get_books_for_library(
                self.odata, library_id
            )
        return self._cache[library_id]
```

#### C#

```csharp
public class BookLookupCache
{
    /// <summary>Cache library-to-book mappings for bulk operations.</summary>
    private readonly ODataClient _odata;
    private readonly Dictionary<string, List<JObject>> _cache = new();

    public BookLookupCache(ODataClient odataClient)
    {
        _odata = odataClient;
    }

    public async Task<List<JObject>> GetBooksAsync(string libraryId)
    {
        if (!_cache.TryGetValue(libraryId, out var books))
        {
            books = await GetBooksForLibraryAsync(_odata, libraryId);
            _cache[libraryId] = books;
        }
        return books;
    }
}
```

<!-- /tabs -->

---

## PurchaseOrder Notepad Writes (Header vs Line)

The PurchaseOrder window exposes **two separate notepad surfaces**, and they use **different tabs and different tools**. Conflating them silently writes to the wrong place with no error.

| | Header notes | Line notes |
|---|---|---|
| **Table** | `po_hdr_notepad` | `po_line_notes` |
| **Keyed by** | `po_no` only | `po_no` + line |
| **Tab** | "PO Note" tab | Line-notes tab (select a line first) |
| **Datawindow** | `tp_7_dw_7` (`d_update_po_hdr_notes_po_entry`) | `tp_21_dw_21` (`d_update_po_line_notes_po_entry`) |
| **Add / Edit tools** | `cb_add` / `cb_edit` | `cb_add_line` / `cb_edit_line` |

> **Warning — silent misfile:** Both tools are labelled **"Add Note"**, but they are distinct. Using `cb_add_line` (the line tool) when you intend a header note **files the note against the currently-selected line** (line 1 after a fresh load) — a perfectly valid *line* note. Every call returns HTTP 200 / `Status: 1` including the save (`savesucceeded`), and the row simply never appears in `po_hdr_notepad`. Symptom: "header note write succeeds but the note is never there." Verified against P21 25.2; reproduced end-to-end July 2026 (misfiled note landed in `tp_21_dw_21` / `po_line_notes` bound to line 1).

> **Requirement — `ResponseWindowHandlingEnabled: true`:** Both add tools open the **Notepad Entry** popup (`w_notepad_response_lite`), which is a response window. The session must be created with `"ResponseWindowHandlingEnabled": true`. With `false`, the tool call fails with HTTP 400: `"Unexpected response window: Notepad Entry Window. Window class: w_notepad_response_lite"`.

> **Tip:** Identify the target tab by its **datawindow name** in the window state (`GET /api/ui/interactive/v2/window?id={windowId}`), not by counting tabs in the UI — the window has 37 tab pages, many disabled or hidden (see [tab identification](#7-transaction-api-service-definition)). On the servers tested, the PO Notes tab is `TABPAGE_7` and the PO Line Notes tab is `TABPAGE_21`, matching the Transaction API definition.

### The Notepad Entry Popup

Both recipes go through the same popup. Running the add tool returns `Status: 3` (Blocked) with a `windowopened` event carrying the popup's window ID:

```json
{
    "Status": 3,
    "Events": [
        {"Name": "windowopened", "Data": [{"Key": "windowid", "Value": "{popupWindowId}"}]}
    ]
}
```

The popup (`w_notepad_response_lite`, title "Notepad Entry Window") is tabless and has three datawindows:

| Datawindow | Purpose |
|------------|---------|
| `_dw_hdr` | The note itself — `topic`, `note`, plus prefilled `po_no`, dates, `mandatory`, `delete_flag`. **The line-note variant additionally carries `line_no` and `item_id`** — check for these columns to confirm which surface you opened |
| `_dw_areas` | Available P21 areas the note can appear in (e.g., "Purchase Order Entry", "Purchase Order Receipts") |
| `_dw_select` | Areas currently selected |

Popup tools: `cb_select`, `cb_select_all`, `cb_deselect`, `cb_deselect_all`, `cb_ok`, `cb_cancel`.

Changes to the popup use the **popup's** window ID with `TabName: null` (it is tabless). `cb_ok` closes the popup (a `close` event with `is_response: true`) and stages the new row into the parent grid — the new `note_id` is already assigned and visible in the parent window's data at this point, **before** saving.

### Recipe: Add a Header Note

1. Start the session with `"ResponseWindowHandlingEnabled": true`, open the `PurchaseOrder` window, and load the PO (change `po_no` on `TABPAGE_1`/`tp_1_dw_1`).
2. Switch to the **PO Notes** tab (`tp_7_dw_7`):

   ```json
   PUT /api/ui/interactive/v2/tab
   {"WindowId": "{windowId}", "PageName": "TABPAGE_7"}
   ```

3. Run the **header** add tool — returns `Status: 3` with the popup's window ID in the `windowopened` event:

   ```json
   POST /api/ui/interactive/v2/tools
   {"WindowId": "{windowId}", "ToolName": "cb_add", "ToolText": "Add Note"}
   ```

4. In the popup, set `topic` and `note` on `_dw_hdr` (note `TabName: null` and the **popup's** window ID):

   ```json
   PUT /api/ui/interactive/v2/change
   {
       "WindowId": "{popupWindowId}",
       "List": [
           {"TabName": null, "DatawindowName": "_dw_hdr", "FieldName": "topic", "Value": "MY TOPIC"},
           {"TabName": null, "DatawindowName": "_dw_hdr", "FieldName": "note", "Value": "Note text"}
       ]
   }
   ```

5. Run `cb_select_all` then `cb_ok` on the popup window ID (`POST /api/ui/interactive/v2/tools`). The popup closes and the staged row (with its new `note_id`) appears in `tp_7_dw_7`.
6. Save the window (`PUT /api/ui/interactive/v2/data`) and [verify the write](#verifying-writes-dont-trust-save-status-alone).

### Recipe: Add a Line Note

1. Start the session with `"ResponseWindowHandlingEnabled": true`, open the `PurchaseOrder` window, and load the PO.
2. **Select the target line row** in the line grid (`tp_17_dw_17`):

   ```json
   PUT /api/ui/interactive/v2/row
   {"WindowId": "{windowId}", "DatawindowName": "tp_17_dw_17", "Row": 0}
   ```

3. Switch to the **PO Line Notes** tab (`tp_21_dw_21`, `PageName: "TABPAGE_21"`).
4. Run the **line** add tool:

   ```json
   POST /api/ui/interactive/v2/tools
   {"WindowId": "{windowId}", "ToolName": "cb_add_line", "ToolText": "Add Note"}
   ```

5. Complete the Notepad Entry popup exactly as in the header recipe (`topic`/`note` on `_dw_hdr` with `TabName: null`, then `cb_select_all`, `cb_ok`) — the popup's `_dw_hdr` shows which `line_no`/`item_id` the note will attach to. Save and verify.

---

## Sales Order Entry with Assembly Lines

Use the Interactive API to create a sales order when a line is an **assembly** that should explode into components and/or spawn a **production order**. The Transaction API cannot do this: entering an assembly item fires an *"add as assembly?"* prompt, and the stateless API auto-answers **No**, killing the explode (see [Order Service Gotchas](03-Transaction-API.md#order-service-gotchas)). Verified end-to-end: interactive order entry created a sales order whose assembly line (`oe_line.assembly = 'P'`) auto-linked to a new production order.

The flow (session started with `ResponseWindowHandlingEnabled: true`):

1. **Header** on `TabName: "TABPAGE_1"`, `DatawindowName: "order"` — set `quote` (`OFF` = real order, `ON` = quote), `sales_loc_id`, `source_loc_id`, `customer_id`, `ship_to_id`, `contact_id`, `order_date`, `requested_date`, `po_no`, `taker`.
   - **`taker` defaults to the API user** — override it with the real salesperson or the order is attributed to the service account.
   - **Setting the dates fires a date-cascade prompt** (`w_response_common`, buttons `cb_ok`/`cb_cancel`) *even on a brand-new order*. Answer **`cb_ok`** via the popup's window ID (see [Response Windows](#response-windows)).
2. **Lines**: `change_tab` to `TP_ITEMS`, then set fields on the **existing** `items` row (`DatawindowName: "items"` — do **not** add a row for the first line):
   - Setting `oe_order_item_id` on an assembly item fires the **assembly prompt** (buttons `cb_1` = Yes / `cb_2` = No / `cb_3` = Cancel). Answer **`cb_1`** to explode the assembly / link a production order.
   - Then set `unit_quantity`.
   - **Do NOT use the quickmode datawindow** (`d_dw_quickmode_*`) to enter lines — it **bypasses the assembly prompt entirely**, and the line lands without the explode.
3. **Save**, answering any follow-on prompts with their proceed button. Read the generated `order_no` from the window data (`GET /v2/data`).

Assembly behavior is item-level (`assembly_hdr`): `production_order_processing` `Y` = production-order assembly / `N` = kit; `auto_create_prod_order` `Y` = auto-create and link the production order at save. On the saved order, `oe_line.assembly` codes: `B` = kit parent, `N` = component, `P` = production-order line, `S` = build-to-stock allocation. The production-order link is `prod_order_line_link` (`transaction_uid = oe_line.oe_line_uid`, `trans_type = 'O'`). See the [Production & Labor API guide](12-Production-Labor-API.md) for the full production lifecycle.

> **Credit:** [Alex Westemeier](https://github.com/AWestemeier) — flow and gotchas verified end-to-end on a play environment (June 2026).

---

## Data Structures Reference

### Result Object

Every action returns a `Result` with these properties:

| Property | Type | Description |
|----------|------|-------------|
| `Status` | int | `0` (None), `1` (Success), `2` (Failure), `3` (Blocked) |
| `Messages` | array | List of messages triggered by the action |
| `Events` | array | List of events that occurred (fields enabled/disabled, windows opened, keys generated, etc.) |

**Status values** (from `ResultStatus` enum):

| Status | Value | Meaning | Action |
|--------|-------|---------|--------|
| `None` | `0` | No action needed | Status couldn't be determined |
| `Success` | `1` | Action completed | Continue to next step |
| `Failure` | `2` | Action failed | Check `Messages` for details |
| `Blocked` | `3` | Session blocked by dialog | Check `Events` for `windowopened`, handle the response window |

### Messages

Each message has a `Text` and a `Type`:

| MessageType | Description |
|-------------|-------------|
| `Information` | Informational (no action needed) |
| `Warning` | Warning (may need attention) |
| `Error` | Error (action failed) |

### Events

Events describe every discrete action the application took. Key event names:

| Event Name | Description |
|------------|-------------|
| `windowopened` | A response window was opened — `Data` contains the window ID |
| `keygenerated` | A new key was generated (e.g., new record ID on save) |

> **Tip:** For less granular information, query the full window state with `GET /api/ui/interactive/v2/window?id={windowId}` after an action instead of parsing individual events.

### Window Definition

When you open or GET a window, the response includes structural information:

| Property | Description |
|----------|-------------|
| `Id` | Window GUID |
| `Title` | Window title |
| `TabPageList` | Array of tabs — each with `Name`, `Text`, and `Enabled` |
| `Datawindows` | Map of datawindow definitions |

Each **datawindow definition** contains:

| Property | Description |
|----------|-------------|
| `Name` | Datawindow name (used in change/row requests) |
| `ParentPage` | Tab this datawindow belongs to |
| `Style` | `List` (grid) or `Form` |
| `Fields` | Map of field definitions |

Each **field definition** contains:

| Property | Description |
|----------|-------------|
| `Name` | Field name (used in change requests) |
| `Label` | Display label |
| `Enabled` | Whether the field is editable |
| `DataType` | `Char`, `Long`, `Datetime`, `Decimal`, `Number`, or `Time` |

### Window Data

`GET /api/ui/interactive/v2/data?id={windowId}` returns data for each datawindow on the active surface:

| Property | Description |
|----------|-------------|
| `Name` | Datawindow name |
| `FullName` | Fully qualified name |
| `ActiveRow` | Currently selected row index |
| `TotalRows` | Number of rows |
| `Columns` | Array of column names |
| `Data` | Array of arrays — each inner array is a row of values |

---

## Self-Documenting Help Endpoints

The API server exposes built-in help pages that list all available endpoints and their parameters:

```http
https://{ui-server-host}/api/ui/interactive/sessions/help
https://{ui-server-host}/ui/interactive/v1/help
```

> **Tip:** These are useful for discovering endpoints and verifying parameter names on your specific P21 version.

---

## V1 REST Endpoint Reference (SDK Internal)

The C# SDK (`P21.UI.Service.Client`) calls these V1 REST endpoints internally. They are listed here for reference — the V2 endpoints documented [above](#window-operations-v2) are recommended for direct REST access. Understanding the V1 paths is useful when debugging SDK behavior or reading network traces.

| Method | V1 Endpoint | Purpose |
|--------|-------------|---------|
| POST | `/uiserver0/ui/common/v1/sessions` | Create session |
| DELETE | `/uiserver0/ui/common/v1/sessions` | End session |
| POST | `/uiserver0/ui/interactive/v1/window` | Open window |
| GET | `/uiserver0/ui/interactive/v1/window` | Get state |
| DELETE | `/uiserver0/ui/interactive/v1/window` | Close window |
| PUT | `/uiserver0/ui/interactive/v1/change` | Change data |
| PUT | `/uiserver0/ui/interactive/v1/data` | Save data |
| GET | `/uiserver0/ui/interactive/v1/data` | Get data |
| DELETE | `/uiserver0/ui/interactive/v1/data` | Clear data |
| PUT | `/uiserver0/ui/interactive/v1/tab` | Change tab |
| GET | `/uiserver0/ui/interactive/v1/tools` | Get tools |
| POST | `/uiserver0/ui/interactive/v1/tools` | Run tool |
| POST | `/uiserver0/ui/interactive/v1/row` | Add row |
| PUT | `/uiserver0/ui/interactive/v1/row` | Change row |

> **Note:** The `uiserver0` prefix is the UI server instance name assigned during routing. Your environment may use a different instance name — check `GET /api/ui/router/v1?urlType=external` to obtain the correct base URL.

---

## Verifying Writes (Don't Trust Save Status Alone)

An Interactive save (`PUT /api/ui/interactive/v2/data`) can return `Status: 1` with a `savesucceeded` event for the **primary** datawindow (`tp_1_dw_1`) even when a change staged into a **child grid** on another tab never actually persisted. The overall call looks fully successful.

Why status alone is not a reliable "it persisted" signal:

- `savesucceeded` / `Status` reflect the main-window save, not necessarily every sub-record you touched. Verified live: a save that persisted a `po_hdr_notepad` child row still reported `savesucceeded` only for `tp_1_dw_1` — and a save whose note had silently misfiled to the *wrong* table looked byte-for-byte identical (`Status: 1`, `savesucceeded`).
- Status-code semantics differ across P21 versions (e.g., an empty/not-found record surfaces differently on 25.2 vs 26.1), so status alone is not portable.
- The **save response** does not include the new auto-generated key (e.g., `note_id`) for an inserted child row. For notepad rows the key is visible earlier — it appears in the parent grid's data (`GET /api/ui/interactive/v2/window?id=`) as soon as the popup commits — but only a read-back proves it actually reached the database.

**Recommendation:** for records where correctness matters, **read the record back after writing** and confirm it exists before treating the write as done — e.g., `POST /api/v2/transaction/get` for the target DataElement (see [Transaction API](03-Transaction-API.md)), or an OData/report read where the table is exposed. Verified live: after the header-note recipe, `transaction/get` keyed by `po_no` returned the `TABPAGE_7.tp_7_dw_7` row with its server-generated `note_id`, and after the misfile scenario it proved the note was in `tp_21_dw_21` instead. This is version-proof, unlike trusting the save's status.

---

## Best Practices

1. **Always end sessions** - Use context managers or try/finally
2. **Handle response windows** - Check for blocked status
3. **Change tabs before fields** - Tab selection required for REST
4. **Find field names in P21** - Use SQL Information dialog
5. **Save before close** - Unsaved changes are lost
6. **Keep sessions short** - Long sessions consume server resources (pool default: 5 instances)
7. **Log window IDs** - Helps debugging
8. **Use SessionType wisely** - `Auto` for background processes, `User` for interactive integrations
9. **Read back after writing** - Save status can report success without persisting a sub-record (see [Verifying Writes](#verifying-writes-dont-trust-save-status-alone))

---

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Invalid/expired token | Re-authenticate |
| "Session not found" | Session ended/timed out | Start new session |
| "Blocked" status | Response window opened | Handle the dialog |
| "Field not found" | Wrong field/datawindow name | Check SQL Information |
| "Window not open" | Window was closed | Re-open the window |

---

## Session vs Transaction API

| Feature | Interactive API | Transaction API |
|---------|-----------------|-----------------|
| Stateful | Yes | No |
| Response windows | Handled | Cause failures |
| Business logic | Full validation | Full validation |
| Complexity | Higher | Lower |
| Performance | Slower | Faster |
| Use case | Complex workflows | Bulk operations |

---

## Known Issues and Workarounds

### Row Selection Synchronization Bug (List → Detail)

When working with windows that have a list/detail pattern (e.g., Item Maintenance with `invloclist` and `inv_loc_detail`), there is a synchronization issue where selecting a row in the list does not immediately update the detail view.

**Symptom:** After selecting row N in a list datawindow and navigating to the detail tab, the detail shows the **previous** row's data instead of row N.

**Pattern observed:**
```text
Row 0 selected → Detail shows row 0 (correct - first selection)
Row 1 selected → Detail shows row 0 (1 behind)
Row 2 selected → Detail shows row 1 (1 behind)
Row 3 selected → Detail shows row 2 (1 behind)
...
Row 5 selected → Detail shows row 4 (1 behind)
```

**Workaround:** Select row N+1 after selecting row N to "push" row N's data through to the detail view.

<!-- tabs -->

#### Python

```python
# To edit row 5 (last row in a 6-row list):

# 1. Select target row
await client.put(f"{ui_url}/api/ui/interactive/v2/row", headers=headers,
    json={"WindowId": window_id, "DatawindowName": "invloclist", "Row": 5})

# 2. Select row N+1 to push row N's data through (can be non-existent)
await client.put(f"{ui_url}/api/ui/interactive/v2/row", headers=headers,
    json={"WindowId": window_id, "DatawindowName": "invloclist", "Row": 6})

# 3. Now go to detail tab - it will show row 5's data
await client.put(f"{ui_url}/api/ui/interactive/v2/tab", headers=headers,
    json={"WindowId": window_id, "PageName": "TABPAGE_18"})

# 4. Change the field and save
await client.put(f"{ui_url}/api/ui/interactive/v2/change", headers=headers,
    json={"WindowId": window_id, "List": [
        {"TabName": "TABPAGE_18", "FieldName": "product_group_id", "Value": "NEW_VALUE"}
    ]})
await client.put(
    f"{ui_url}/api/ui/interactive/v2/data",
    headers=headers, json=window_id,
)
```

#### C#

```csharp
// To edit row 5 (last row in a 6-row list):

// 1. Select target row
await http.PutAsJsonAsync($"{uiUrl}/api/ui/interactive/v2/row",
    new { WindowId = windowId, DatawindowName = "invloclist", Row = 5 });

// 2. Select row N+1 to push row N's data through (can be non-existent)
await http.PutAsJsonAsync($"{uiUrl}/api/ui/interactive/v2/row",
    new { WindowId = windowId, DatawindowName = "invloclist", Row = 6 });

// 3. Now go to detail tab - it will show row 5's data
await http.PutAsJsonAsync($"{uiUrl}/api/ui/interactive/v2/tab",
    new { WindowId = windowId, PageName = "TABPAGE_18" });

// 4. Change the field and save
await http.PutAsJsonAsync($"{uiUrl}/api/ui/interactive/v2/change",
    new
    {
        WindowId = windowId,
        List = new[]
        {
            new { TabName = "TABPAGE_18", FieldName = "product_group_id", Value = "NEW_VALUE" }
        }
    });
await http.PutAsync($"{uiUrl}/api/ui/interactive/v2/data",
    new StringContent($"\"{windowId}\"", System.Text.Encoding.UTF8, "application/json"));
```

<!-- /tabs -->

**Affected Windows:**
- Item Maintenance (`Item` service) - Location Detail tab
- Likely other windows with list/detail patterns

**Note:** This issue may be specific to certain P21 versions or configurations. Test thoroughly with your environment.

**Related trap — never `select_row` on the detail form itself.** A single-row detail form (e.g. `inv_loc_detail`) is *bound* to the currently-selected parent list row. Sending `PUT /v2/row` against the **detail** datawindow does not select within the detail — it re-selects the *parent* list (row N on the detail = row N on `invloclist`) and **silently flips which record the detail is bound to**, typically to the list's first row. The edit then lands on the wrong location while every call reports success. Select only the parent list row, edit the detail directly, and assert the detail shows exactly the intended record before and after the change (abort without saving on mismatch). The Transaction API's nested pattern keys by `location_id` and has no such trap. *(Credit: [Alex Westemeier](https://github.com/AWestemeier))*

### Row 0 Auto-Selection Quirk

After switching to a tab that contains a list or grid datawindow, row 0 is **automatically selected** by the API. Explicitly calling `change_row(0)` after switching tabs returns HTTP 422 because the row is already selected.

**Symptom:** `PUT /api/ui/interactive/v2/row` with `Row: 0` returns 422 error.

**Workaround:** Skip the `change_row(0)` call when targeting the first row. Start explicit row selection at row 1.

<!-- tabs -->

#### Python

```python
async def select_row_safe(window: Window, row: int, datawindow_name: str):
    """Select a row, handling the row 0 auto-selection quirk.

    Row 0 is auto-selected when switching to a tab with a grid.
    Calling change_row(0) explicitly returns 422.
    """
    if row == 0:
        # Row 0 is already selected after tab switch - skip
        return
    await window.change_row(row, datawindow_name)
```

#### C#

```csharp
public async Task SelectRowSafeAsync(Window window, int row, string datawindowName)
{
    // Row 0 is auto-selected when switching to a tab with a grid.
    // Calling ChangeRow(0) explicitly returns 422.
    if (row == 0)
    {
        // Row 0 is already selected after tab switch - skip
        return;
    }
    await window.ChangeRowAsync(row, datawindowName);
}
```

<!-- /tabs -->

**Important:** This is different from the [row selection synchronization bug](#row-selection-synchronization-bug-list--detail) documented above. That bug is about list-to-detail data sync being one row behind. This quirk is specifically about row 0 being pre-selected after a tab switch.

### Key Fields Commit the Cursor (Later Fields Silently Ignored)

Sending a grid row's **key field** in a `change` request commits the row cursor — any field in the same `List` (or a later call) that follows the key field is **silently ignored** (the call still returns Status 0/Success). Example: on the JobContractPricing BINS grid, `contract_bin_id` is the key; if it appears before the quantity fields, the quantities never land.

**Guidance:**

- When only *changing* values on an already-selected row, **don't send the key field at all** — select the row, then change the non-key fields.
- When the key field must be sent (identifying a row by value), send it **last**.
- After the save, read the values back — a silently-dropped edit is indistinguishable from success by status code alone (see [Verifying Writes](#verifying-writes-dont-trust-save-status-alone)).

*(Credit: [Alex Westemeier](https://github.com/AWestemeier))*

### Numeric Values: Send Integer Strings for Whole Numbers

When setting numeric fields, send whole numbers as integer strings (`"30"`), not float-formatted strings (`"30.0"`) — some windows reject or mishandle the float form. Format values the way a user would type them.

---

## v1 vs v2 API Differences

> **Important:** Some P21 servers only support v2 endpoints (v1 returns 404). Always try v2 first.

### Summary Table

| Operation | v1 | v2 |
|-----------|----|----|
| **Change** | `ChangeRequests` array | `List` array |
| **Change field ref** | `DataWindowName` (capital W) | `TabName` + `DatawindowName` (lowercase w) — **required in 25.2+** |
| **Save** | `{"WindowId": "..."}` | `"..."` (just GUID string) |
| **Tab change** | `PagePath: {PageName: "..."}` | `PageName: "..."` (direct) |
| **Row change** | `RowNumber` | `Row` |
| **Row datawindow** | `DataWindowName` | `DatawindowName` (lowercase w) |

### Change Request Format

**v1:**
```json
{
    "WindowId": "...",
    "ChangeRequests": [
        {"DataWindowName": "form", "FieldName": "item_id", "Value": "ABC"}
    ]
}
```

**v2:**
```json
{
    "WindowId": "...",
    "List": [
        {"TabName": "FORM", "FieldName": "item_id", "Value": "ABC", "DatawindowName": "form"}
    ]
}
```

### Save Format

**v1:** `{"WindowId": "abc-123..."}`

**v2:** `"abc-123..."` (just the GUID string - this is critical!)

### Tab Change Format

**v1:**
```json
{"WindowId": "...", "PagePath": {"PageName": "TABPAGE_17"}}
```

**v2:**
```json
{"WindowId": "...", "PageName": "TABPAGE_17"}
```

### Row Change Format

**v1:**
```json
{"WindowId": "...", "DataWindowName": "list", "RowNumber": 0}
```

**v2:**
```json
{"WindowId": "...", "DatawindowName": "list", "Row": 0}
```

### Get Window Data / Close Window

**v2:** Use `?id=` query parameter:

```http
GET /api/ui/interactive/v2/data?id={windowId}
DELETE /api/ui/interactive/v2/window?id={windowId}
DELETE /api/ui/interactive/v2/data?id={windowId}
```

---

## Troubleshooting v2 Issues

| Error | Cause | Solution |
|-------|-------|----------|
| 404 on v1 | Server only supports v2 | Use v2 endpoints |
| 422 "Window ID was not provided" | Save payload wrapped in object | Send just the GUID string for v2 |
| 500 on tab change | Using PagePath wrapper | Use PageName directly for v2 |
| Field change doesn't persist | Missing TabName | Include TabName in change request |

---

## Operational Patterns

Patterns discovered through production use of the Interactive API. These cover behaviors that are not documented in the official SDK but are consistent and reproducible.

### Tab Unlock Sequences

Certain windows have tabs that start disabled and unlock progressively as prerequisite fields are populated. The API communicates unlock state via `tabpageenabled` events in responses.

**Example: JobContractPricing**

On window open, 7 tabs are disabled: `CUSTSHIPTOCONSIGN`, `BINS`, `VALUES`, `BIN_ITEMS`, `ITEM_BIN_NOTES`, `SHIPTOCONSIGNCONTROL`, `CONSIGNMENTISSUES`. The unlock sequence is:

1. Set `contract_no` on `FORM` — enables `CUSTOMER_SHIP_TO`
2. Create a customer/ship_to combination on `CUSTOMER_SHIP_TO`, then set `customer_id` and `ship_to_id` on `FORM` — enables `SHIP_TO_ITEM`
3. Set `item_id` on `SHIP_TO_ITEM` and dismiss the scan lookup dialog — enables `VALUES`, `BINS`, `BIN_ITEMS`, `ITEM_BIN_NOTES` simultaneously

> **Important:** P21 rejects setting `customer_id` or `ship_to_id` on the FORM header directly. You must create the combination on `CUSTOMER_SHIP_TO` first. Error: *"Before selecting a Customer ID or Ship To ID, make sure that the combination exists in the Customer/Ship To tab."*

**Example: JobContractPricing — EXISTING contract (BINS editing).** The sequence above is the *creation* flow. For an existing contract, the combination already exists and the recipe differs (verified; credit: [Alex Westemeier](https://github.com/AWestemeier)):

1. Load the contract by setting `job_no`, `customer_id`, and `ship_to_id` on `FORM/d_dw_job_price_hdr` (three separate change calls). **Load by `job_no`, not `contract_no`** — renewals can leave the same `contract_no` on two header rows, while `job_no` is unique.
2. Change to the `CUSTOMER_SHIP_TO` tab and **select the ship-to's grid row** — the BINS tab only unlocks after the ship-to row is selected. Skipping this (or loading by `contract_no` alone) leaves it disabled with *"Tab page is disabled and cannot be selected."*
3. Per line: `JOBPRICELINE` tab → select the line's row → `BINS` tab → the grid is **filtered to the selected ship-to**, so it has exactly one row per line — `select_row("bins", 1)` always targets the right bin. Edit the quantity fields.
4. One `save()` at the end persists every edit in the session (save per ship-to on large runs so a mid-run failure doesn't lose everything).

> For bulk bin-quantity changes, the Transaction API with `IgnoreDisabled: true` is faster — see [Editing Bin Quantities](03-Transaction-API.md#editing-bin-quantities-on-an-existing-contract). Use this interactive recipe when a Transaction-API edge case appears or the contract is expired-adjacent work that needs window logic.

**Detecting tab unlock events:**

<!-- tabs -->

#### Python

```python
def check_tab_unlocks(result: dict) -> list[str]:
    """Extract tab unlock events from an API response.

    Args:
        result: The parsed JSON response from a change/save operation.

    Returns:
        List of tab names that were just enabled.
    """
    unlocked: list[str] = []
    for event in result.get("Events", []):
        if event.get("Name") == "tabpageenabled":
            for kv in event.get("Data", []):
                if kv.get("Key") == "pagename":
                    unlocked.append(kv["Value"])
    return unlocked


# Usage: monitor unlocks as you populate fields
result = await client.put(
    f"{ui_url}/api/ui/interactive/v2/change",
    headers=headers,
    json={
        "WindowId": window_id,
        "List": [{
            "TabName": "FORM",
            "DatawindowName": "form",
            "FieldName": "contract_no",
            "Value": "1001"
        }]
    }
)
response = result.json()
unlocked = check_tab_unlocks(response)
# unlocked == ["CUSTOMER_SHIP_TO"]
```

#### C\#

```csharp
public List<string> CheckTabUnlocks(JObject result)
{
    // Extract tab unlock events from an API response.
    var unlocked = new List<string>();
    var events = result["Events"] as JArray ?? new JArray();

    foreach (var evt in events)
    {
        if (evt["Name"]?.ToString() == "tabpageenabled")
        {
            var data = evt["Data"] as JArray ?? new JArray();
            foreach (var kv in data)
            {
                if (kv["Key"]?.ToString() == "pagename")
                    unlocked.Add(kv["Value"]!.ToString());
            }
        }
    }
    return unlocked;
}

// Usage: monitor unlocks as you populate fields
var payload = new JObject
{
    ["WindowId"] = windowId,
    ["List"] = new JArray
    {
        new JObject
        {
            ["TabName"] = "FORM",
            ["DatawindowName"] = "form",
            ["FieldName"] = "contract_no",
            ["Value"] = "1001"
        }
    }
};
var content = new StringContent(payload.ToString(), Encoding.UTF8, "application/json");
var response = await http.PutAsync($"{uiUrl}/api/ui/interactive/v2/change", content);
var result = JObject.Parse(await response.Content.ReadAsStringAsync());
var unlocked = CheckTabUnlocks(result);
// unlocked == ["CUSTOMER_SHIP_TO"]
```

<!-- /tabs -->

**General guidance:** Always check `tabpageenabled` events when working with multi-tab windows. Do not attempt to switch to a disabled tab — the API will return an error. Query the window definition (`GET /api/ui/interactive/v2/window?id={windowId}`) to see current tab states via `TabPageList[].Enabled`.

### add_row with Status=2 (Failure)

When calling `add_row`, P21 returns `Status: 2` (Failure) if the **previous** row has incomplete or invalid data. Despite the failure status, the new row **is still created** and ready for data entry. This is expected P21 behavior, not a hard error.

**Example:** `add_row("bins")` returns Status=2 with message *"Required value missing for Bin ID on row 1"* — but row 2 is created and editable.

**Guidance:** When adding multiple rows in sequence, expect Status=2 on subsequent `add_row` calls if prior rows are not fully populated. Do not treat Status=2 as a fatal error in this context — check the messages to determine whether the failure is about the previous row's validation or a real problem.

<!-- tabs -->

#### Python

```python
import logging

import httpx

logger = logging.getLogger(__name__)


async def add_row_tolerant(
    window_id: str,
    datawindow_name: str,
    headers: dict[str, str],
    client: httpx.AsyncClient,
    ui_url: str,
) -> dict:
    """Add a row, tolerating Status=2 from incomplete previous rows.

    Args:
        window_id: The active window ID.
        datawindow_name: Target datawindow (e.g., "bins").
        headers: Request headers with auth token.
        client: httpx async client.
        ui_url: UI server base URL.

    Returns:
        Parsed response dict.

    Raises:
        RuntimeError: If the failure is not a previous-row validation issue.
    """
    response = await client.post(
        f"{ui_url}/api/ui/interactive/v2/row",
        headers=headers,
        json={"WindowId": window_id, "DatawindowName": datawindow_name},
    )
    response.raise_for_status()
    result = response.json()

    status = result.get("Status", 0)
    if status == 2:
        messages = [m.get("Text", "") for m in result.get("Messages", [])]
        # Previous-row validation warnings are expected — row was still added
        if any("required value missing" in m.lower() for m in messages):
            logger.info(
                "add_row returned Status=2, row added"
            )
            return result
        # Unexpected failure — raise
        raise RuntimeError(f"add_row failed: {messages}")

    return result
```

#### C\#

```csharp
public async Task<JObject> AddRowTolerantAsync(
    string windowId,
    string datawindowName,
    HttpClient http,
    string uiUrl)
{
    // Add a row, tolerating Status=2 from incomplete previous rows.
    var payload = new JObject
    {
        ["WindowId"] = windowId,
        ["DatawindowName"] = datawindowName
    };
    var content = new StringContent(payload.ToString(), Encoding.UTF8, "application/json");
    var response = await http.PostAsync($"{uiUrl}/api/ui/interactive/v2/row", content);
    response.EnsureSuccessStatusCode();

    var result = JObject.Parse(await response.Content.ReadAsStringAsync());
    var status = result["Status"]?.Value<int>() ?? 0;

    if (status == 2)
    {
        var messages = result["Messages"]?
            .Select(m => m["Text"]?.ToString() ?? "")
            .ToList() ?? new List<string>();

        // Previous-row validation warnings are expected — row was still added
        if (messages.Any(m => m.Contains("required value missing", StringComparison.OrdinalIgnoreCase)))
        {
            _logger.LogInformation("add_row returned Status=2 (previous row incomplete), row added");
            return result;
        }
        // Unexpected failure — raise
        throw new InvalidOperationException($"add_row failed: {string.Join("; ", messages)}");
    }

    return result;
}
```

<!-- /tabs -->

### Response Window Types

Response windows fall into distinct categories based on what interactions they support. Tool-capable dialogs can be dismissed via `POST /tools`, but message boxes (`w_message`) are auto-answered based on `ResponseWindowHandlingEnabled` configuration.

| Type | Example | Buttons | Field Input | Dismiss Method |
|------|---------|---------|-------------|----------------|
| **Button-only dialog** | `w_rule_callback_response` | `cb_1` through `cb_5` | N/A | `POST /tools` with button name |
| **Form + button dialog** | `w_inventory_scan_lookup` | `cb_ok`, `cb_cancel` | See editability note below | `POST /tools` with button name |
| **Editable form dialog** | `w_notepad_response_lite` | `cb_select_all`, `cb_ok` | **Editable with `TabName: null`** | Fill fields, then `POST /tools` |
| **Message box** | `w_message` | Default-answered | Cannot be inspected | Auto-answered when `ResponseWindowHandlingEnabled: false` |

**Editability (reconciled July 2026):** earlier testing (April 2026) concluded form-type response windows could only be dismissed — `GET /data` returned 400 and `PUT /change` returned 500 with *"Tab with name FORM does not exist"*. Those change attempts addressed the popup's fields with `TabName: "FORM"`. Later work showed form-style response windows **are editable** when the change request uses **`TabName: null`** with the popup's window ID — verified end-to-end on `w_notepad_response_lite` (see [PurchaseOrder Notepad Writes](#purchaseorder-notepad-writes-header-vs-line)). If a popup's fields reject edits, retry with `TabName: null` before concluding the window is dismiss-only. `w_message` boxes remain uneditable and are auto-answered.

**Inspecting and dismissing response windows:**

<!-- tabs -->

#### Python

```python
import logging

import httpx

logger = logging.getLogger(__name__)


async def handle_response_window(
    window_id: str,
    response_window_id: str,
    headers: dict[str, str],
    client: httpx.AsyncClient,
    ui_url: str,
    button: str = "cb_cancel",
) -> dict:
    """Inspect a response window and dismiss it via button click.

    Args:
        window_id: The parent window ID.
        response_window_id: The response window ID from the windowopened event.
        headers: Request headers with auth token.
        client: httpx async client.
        ui_url: UI server base URL.
        button: Button name to click (default: cb_cancel).

    Returns:
        Parsed response from the tool click.
    """
    # Step 1: Discover available buttons
    tools_resp = await client.get(
        f"{ui_url}/api/ui/interactive/v2/tools",
        headers=headers,
        params={"windowId": response_window_id},
    )
    tools_resp.raise_for_status()
    tools = tools_resp.json()
    available = [t.get("Name") or t.get("ToolName") for t in tools]
    logger.info("Response window %s has buttons: %s", response_window_id, available)

    # Step 2: Click the desired button
    click_resp = await client.post(
        f"{ui_url}/api/ui/interactive/v2/tools",
        headers=headers,
        json={"WindowId": response_window_id, "ToolName": button},
    )
    click_resp.raise_for_status()
    return click_resp.json()
```

#### C\#

```csharp
public async Task<JObject> HandleResponseWindowAsync(
    string windowId,
    string responseWindowId,
    HttpClient http,
    string uiUrl,
    string button = "cb_cancel")
{
    // Step 1: Discover available buttons
    var toolsResp = await http.GetAsync(
        $"{uiUrl}/api/ui/interactive/v2/tools?windowId={responseWindowId}");
    toolsResp.EnsureSuccessStatusCode();

    var tools = JArray.Parse(await toolsResp.Content.ReadAsStringAsync());
    var available = tools.Select(t => t["Name"]?.ToString() ?? t["ToolName"]?.ToString()).ToList();
    _logger.LogInformation("Response window {WindowId} has buttons: {Buttons}",
        responseWindowId, string.Join(", ", available));

    // Step 2: Click the desired button
    var payload = new JObject
    {
        ["WindowId"] = responseWindowId,
        ["ToolName"] = button
    };
    var content = new StringContent(payload.ToString(), Encoding.UTF8, "application/json");
    var clickResp = await http.PostAsync($"{uiUrl}/api/ui/interactive/v2/tools", content);
    clickResp.EnsureSuccessStatusCode();

    return JObject.Parse(await clickResp.Content.ReadAsStringAsync());
}
```

<!-- /tabs -->

> **Note:** The `GET /tools` endpoint uses `?windowId=` (not `?id=`). See the [query parameter inconsistency note](#data-operations-v2-recommended) in the Endpoints section.

### UOM Auto-Population

When setting `item_id` via the Interactive API, P21 validates the unit of measure against the item's valid UOM list. Setting an invalid `uom` value results in HTTP 422 with *"Invalid uom value"*.

**Best practice:** Do **not** set `uom` explicitly — let P21 auto-populate it from the item master data. The API fills in the item's default selling or purchasing UOM automatically after `item_id` is set. Only override `uom` if you have confirmed the target value exists in the item's UOM list.

### Timeout Recommendations

Recommended HTTP timeouts based on production experience with large payloads:

| Operation | Recommended Timeout | Notes |
|-----------|-------------------|-------|
| `submit_transaction` (Transaction API, 100+ lines) | 300s | Large payloads with many line items |
| `save_data` (Interactive API) | 120s | Business logic validation can be slow |
| `select_row` / `change_fields` | 60s | Individual field operations |
| Default for all operations | 60s minimum | P21 server processing varies by load |

> These are guidelines from production use. Adjust based on data volume and server performance. The default `httpx` timeout of 5 seconds is almost always too low for P21 operations.

---

## Related

- [Authentication](00-Authentication.md)
- [API Selection Guide](01-API-Selection-Guide.md)
- [Transaction API](03-Transaction-API.md)
- [Production & Labor API](12-Production-Labor-API.md) - TimeEntry, ProductionOrder, and labor services
- [Batch Processing Patterns](09-Batch-Processing-Patterns.md) - Production batch processing, async client, error recovery
- [scripts/interactive/](https://github.com/mrwuss/p21-api-documentation/tree/master/scripts/interactive/) - Working examples
