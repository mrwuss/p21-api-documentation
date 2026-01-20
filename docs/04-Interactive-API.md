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

```
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
| `/api/ui/interactive/v2/window` | GET | Get window state |
| `/api/ui/interactive/v2/window` | DELETE | Close window |

### Data Operations (v2 - Recommended)

> **Important:** Some P21 servers only support v2 endpoints. If you receive 404 errors on v1 endpoints, use v2 instead.

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/ui/interactive/v2/data` | PUT | Save data |
| `/api/ui/interactive/v2/data` | GET | Get active data |
| `/api/ui/interactive/v2/data` | DELETE | Clear data |
| `/api/ui/interactive/v2/change` | PUT | Change field values |
| `/api/ui/interactive/v2/tab` | PUT | Change active tab |
| `/api/ui/interactive/v2/row` | POST | Add a row |
| `/api/ui/interactive/v2/row` | PUT | Change current row |
| `/api/ui/interactive/v2/tools` | GET | Get available tools |
| `/api/ui/interactive/v2/tools` | POST | Run a tool |

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

### 2. Open Window

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
DELETE /api/ui/interactive/v2/window?windowId=w_sales_price_page
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

1. The result will have `Status: "Blocked"`
2. Check the `Events` array for `windowopened`
3. Get the new window ID from the event data
4. Handle the response window
5. Close it to resume the original operation

Example response with blocked status:
```json
{
    "Status": "Blocked",
    "Events": [
        {
            "Name": "windowopened",
            "Data": {
                "WindowId": "w_response_123"
            }
        }
    ]
}
```

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

Get available tools:
```
GET /api/ui/interactive/v1/tools?windowId=w_sales_price_page
```

Run a tool:
```json
POST /api/ui/interactive/v1/tools
{
    "WindowId": "w_sales_price_page",
    "ToolName": "cb_save",
    "ToolText": "Save"
}
```

---

## Python Examples

### Basic Client Class

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
            f"{self.base_url}/api/security/token",
            headers={
                "username": self.username,
                "password": self.password,
                "Content-Type": "application/json"
            },
            content="",
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

### Context Manager Usage (Sync)

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

### Async Context Manager (Recommended)

For production code, use async patterns with proper cleanup:

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
        url = f"{self.base_url}/api/security/token"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "username": self.username,
            "password": self.password
        }
        client = self._get_client()
        response = await client.post(url, headers=headers, content="")
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

**Key points for async usage:**

1. Use `httpx.AsyncClient` instead of sync `httpx`
2. Implement `__aenter__` and `__aexit__` for async context manager
3. Always close the HTTP client in `__aexit__`
4. Ignore cleanup errors - session may have timed out
5. Use `async with` syntax for guaranteed cleanup

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

---

## Example: Linking Price Page to Price Book

This example shows how to use the SalesPriceBook window to link a price page to a price book. This is a common operation after creating a new price page.

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

**Key points:**

1. Open window by `ServiceName`, not title
2. Retrieve the book first - this loads it into the window
3. Switch to LIST tab before adding/modifying rows
4. Use `add_row('list_detail')` to add a new link row
5. Set `price_page_uid` as a string value
6. Always close the window in a `finally` block

---

## Best Practices

1. **Always end sessions** - Use context managers or try/finally
2. **Handle response windows** - Check for blocked status
3. **Change tabs before fields** - Tab selection required for REST
4. **Find field names in P21** - Use SQL Information dialog
5. **Save before close** - Unsaved changes are lost
6. **Keep sessions short** - Long sessions consume server resources
7. **Log window IDs** - Helps debugging

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
```
Row 0 selected → Detail shows row 0 (correct - first selection)
Row 1 selected → Detail shows row 0 (1 behind)
Row 2 selected → Detail shows row 1 (1 behind)
Row 3 selected → Detail shows row 2 (1 behind)
...
Row 5 selected → Detail shows row 4 (1 behind)
```

**Workaround:** Select row N+1 after selecting row N to "push" row N's data through to the detail view.

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

**Affected Windows:**
- Item Maintenance (`Item` service) - Location Detail tab
- Likely other windows with list/detail patterns

**Note:** This issue may be specific to certain P21 versions or configurations. Test thoroughly with your environment.

---

## v1 vs v2 API Differences

> **Important:** Some P21 servers only support v2 endpoints (v1 returns 404). Always try v2 first.

### Summary Table

| Operation | v1 | v2 |
|-----------|----|----|
| **Change** | `ChangeRequests` array | `List` array |
| **Change field ref** | `DataWindowName` (capital W) | `TabName` + optional `DatawindowName` (lowercase w) |
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

### Get Window Data

**v2:** Use query parameter: `GET /api/ui/interactive/v2/data?id={windowId}`

---

## Troubleshooting v2 Issues

| Error | Cause | Solution |
|-------|-------|----------|
| 404 on v1 | Server only supports v2 | Use v2 endpoints |
| 422 "Window ID was not provided" | Save payload wrapped in object | Send just the GUID string for v2 |
| 500 on tab change | Using PagePath wrapper | Use PageName directly for v2 |
| Field change doesn't persist | Missing TabName | Include TabName in change request |

---

## Related

- [Authentication](00-Authentication.md)
- [API Selection Guide](01-API-Selection-Guide.md)
- [Transaction API](03-Transaction-API.md)
- [scripts/interactive/](https://github.com/mrwuss/p21-api-documentation/tree/master/scripts/interactive/) - Working examples
