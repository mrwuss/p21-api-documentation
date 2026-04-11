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
> | GET `/v2/tools` | No (500) | **Yes** |
>
> Using the wrong parameter returns an error — there is no fallback.

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

> **P21 25.2+ Breaking Change:** `DatawindowName` is now effectively **required** for v2 change requests. The 3-parameter form (TabName + FieldName + Value) stopped working after the 25.2 upgrade — you must include `DatawindowName` as the 4th field. This affects multiple windows including Item, PO Receiving Group, Delivery List, and Group Pick Ticket. Window data structures changed in 25.2 so the server can no longer auto-resolve the target datawindow from TabName alone. **Always include `DatawindowName` in change requests.**

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
        except:
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
        catch { /* ignored */ }
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
    def __init__(self, base_url: str, username: str, password: str, verify_ssl: bool = True):
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

## Best Practices

1. **Always end sessions** - Use context managers or try/finally
2. **Handle response windows** - Check for blocked status
3. **Change tabs before fields** - Tab selection required for REST
4. **Find field names in P21** - Use SQL Information dialog
5. **Save before close** - Unsaved changes are lost
6. **Keep sessions short** - Long sessions consume server resources (pool default: 5 instances)
7. **Log window IDs** - Helps debugging
8. **Use SessionType wisely** - `Auto` for background processes, `User` for interactive integrations

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
await client.put(f"{ui_url}/api/ui/interactive/v2/data", headers=headers, json=window_id)
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
            logger.info("add_row returned Status=2 (previous row incomplete), row added")
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
| **Form + button dialog** | `w_inventory_scan_lookup` | `cb_ok`, `cb_cancel` | Fields visible but **not writable** via API | `POST /tools` with button name |
| **Message box** | `w_message` | Default-answered | Cannot be inspected | Auto-answered when `ResponseWindowHandlingEnabled: false` |

**Key limitation (verified April 2026):** Form-type response windows can only be **dismissed** (button click), not **interacted with** (field changes). `GET /data` returns 400 and `PUT /change` returns 500 with *"Tab with name FORM does not exist"*. Workflows that depend on filling response window fields cannot be fully automated.

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
