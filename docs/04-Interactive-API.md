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

### Data Operations

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

Response windows (dialogs) can pop up during operations that trigger business logic questions.

### ResponseWindowHandlingEnabled Session Option

When creating a session, you can specify how dialogs are handled:

```json
POST /api/ui/interactive/sessions
{
    "ResponseWindowHandlingEnabled": false
}
```

| Value | Behavior |
|-------|----------|
| `false` (default) | P21 **auto-handles** dialogs with the **default response** (usually "Yes"). You won't see dialogs but **default actions are taken automatically**. |
| `true` | P21 returns dialog events to your code. You must handle them programmatically before proceeding. |

> ⚠️ **Critical Warning**: `ResponseWindowHandlingEnabled: false` does NOT mean "answer No" - it means "auto-answer with the default", which is typically "Yes".

### Dialog Detection (with ResponseWindowHandlingEnabled: true)

When a dialog opens, the API response will have:
- `Status: 3` (numeric, not string "Blocked")
- A `windowopened` event with the dialog's window ID

Example response:
```json
{
    "Status": 3,
    "Events": [
        {
            "Name": "windowopened",
            "Data": [
                {
                    "Key": "windowid",
                    "Value": "8aaa50e6-a2c7-455b-8598-f37c7ee37188"
                }
            ]
        }
    ],
    "Messages": []
}
```

### Getting Dialog Information

You can retrieve information about the dialog window:

```json
GET /api/ui/interactive/v2/window?id={dialog_window_id}
```

Response:
```json
{
    "Definition": {
        "Title": "Epicor Prophet 21 - Startup",
        "Name": "w_message",
        "Datawindows": {},
        "Id": "8aaa50e6-a2c7-455b-8598-f37c7ee37188",
        "TabPageList": []
    },
    "Data": []
}
```

### Responding to Dialogs

**Discovered endpoint (P21 version 25.2.x):** You CAN respond to dialogs using the tools endpoint:

```http
POST /api/ui/interactive/v2/tools
Content-Type: application/json

{
    "WindowId": "{response_window_id}",
    "ToolName": "cb_2"
}
```

**Common button tool names:**
| ToolName | Typical Text | Use |
|----------|--------------|-----|
| `cb_1` | &Yes | Confirm/Accept |
| `cb_2` | &No | Decline/Cancel |
| `cb_3` | (varies) | Third option if present |

### Getting Available Buttons

Query the response window to see available tools:

```http
GET /api/ui/interactive/v2/tools?windowId={response_window_id}
```

Response:
```json
[
    {"WindowId": "...", "ToolName": "cb_1", "Text": "&Yes", ...},
    {"WindowId": "...", "ToolName": "cb_2", "Text": "&No", ...},
    {"WindowId": "...", "ToolName": "cb_print", "Text": "&Print", ...}
]
```

### Complete Dialog Handling Workflow

1. **Detect dialog** - Check for `Status: 3` and `windowopened` event
2. **Get window info** (optional) - `GET /api/ui/interactive/v2/window?id={id}`
3. **Get available buttons** (optional) - `GET /api/ui/interactive/v2/tools?windowId={id}`
4. **Click the desired button** - `POST /api/ui/interactive/v2/tools` with `ToolName`
5. **Continue with main window** - Dialog is dismissed, proceed normally

### What You CANNOT Get

The actual dialog message text (e.g., "Do you want the GL accounts...") is NOT available via API. The window query only returns:
- `Name`: `w_message` (generic)
- `Title`: `Epicor Prophet 21 - Startup` (generic)
- `Data`: `[]` (empty)

The message text only appears in error responses if you try to continue without handling the dialog.

### Endpoints That Do NOT Work

| Endpoint | Result |
|----------|--------|
| `PUT /api/ui/interactive/v2/tool` (singular) | 404 Not Found |
| `PUT /api/ui/interactive/v2/responsewindow` | 404 Not Found |
| `DELETE /api/ui/interactive/v2/window` with button param | 400 Bad Request |
| `PUT /api/ui/interactive/v2/change` on dialog | "Column is disabled" |

### If Dialog Is Not Handled

If you attempt to continue with the main window while a dialog is open:

```json
{
    "ErrorMessage": "Unable to process request on window {main_window_id} since response window {dialog_window_id} blocks it: w_message (Title) - Dialog message here.",
    "ErrorType": "P21.UI.Common.UiServerUserErrorException"
}
```

---

## GL Account Dialog When Changing Product Groups

### The Problem

When changing the `product_group_id` field on an inventory location (`inv_loc`) via the Item window, P21 displays a dialog:

> "Do you want the GL accounts for product group 'XXX' to be set?"

- **Default answer**: "Yes"
- **Consequence**: GL account fields (`gl_account_no`, `revenue_account_no`, `cos_account_no`) are overwritten with the new product group's default values

### The Solution

Use `ResponseWindowHandlingEnabled: true` and click "No" (`cb_2`) when the dialog appears:

```python
# 1. Start session with ResponseWindowHandlingEnabled: true
await client.post(
    f"{ui_url}/api/ui/interactive/sessions/",
    json={"ResponseWindowHandlingEnabled": True}
)

# 2. Change product_group_id
result = await client.put(
    f"{ui_url}/api/ui/interactive/v2/change",
    json={
        "WindowId": window_id,
        "List": [{
            "TabName": "TABPAGE_18",
            "FieldName": "product_group_id",
            "Value": new_product_group_id,
            "DatawindowName": "inv_loc_detail"
        }]
    }
)

# 3. Check for dialog (Status: 3)
if result.json().get("Status") == 3:
    events = result.json().get("Events", [])
    for event in events:
        if event.get("Name") == "windowopened":
            for data_item in event.get("Data", []):
                if data_item.get("Key") == "windowid":
                    response_window_id = data_item.get("Value")

                    # 4. Click "No" to preserve GL accounts
                    await client.post(
                        f"{ui_url}/api/ui/interactive/v2/tools",
                        json={
                            "WindowId": response_window_id,
                            "ToolName": "cb_2"  # "No" button
                        }
                    )

# 5. Save - GL accounts are preserved
await client.put(f"{ui_url}/api/ui/interactive/v2/data", json=window_id)
```

### Key Points

- `ResponseWindowHandlingEnabled: true` - Required to intercept the dialog
- `Status: 3` - Indicates a dialog window opened
- `windowopened` event - Contains the response window ID
- `cb_2` = "No" button - Declines GL account overwrite
- `cb_1` = "Yes" button - Would apply GL account defaults

### What You Cannot Do

- Get the actual dialog message text via API (only visible in error responses)
- Modify GL accounts via the Item window (fields are read-only on TABPAGE_24)
- Update GL accounts via OData or REST API (404 - not supported)

### If You Need to Accept GL Changes

Simply use `ResponseWindowHandlingEnabled: false` (default) - the dialog will be auto-answered "Yes" and GL accounts will be updated to match the product group defaults

---

## Changing Tabs

Before changing fields on a different tab, select the tab first:

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
| Sales Price Page Entry | SalesPricePage | Price pages |
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

## Example: Updating Product Group per Location

This example shows the complete workflow for updating `product_group_id` in `inv_loc` via the Item Maintenance window, including the row selection workaround.

```python
async def update_inv_loc_product_group(
    client: httpx.AsyncClient,
    ui_url: str,
    headers: dict,
    item_id: str,
    location_id: int,
    new_product_group_id: str
) -> bool:
    """Update product_group_id for an item at a specific location.

    Uses Item service window with row selection workaround.
    """
    # Open Item window
    resp = await client.post(
        f"{ui_url}/api/ui/interactive/v2/window",
        headers=headers,
        json={"ServiceName": "Item"}
    )
    window_id = resp.json()["WindowId"]

    try:
        # 1. Retrieve item
        await client.put(
            f"{ui_url}/api/ui/interactive/v2/change",
            headers=headers,
            json={
                "WindowId": window_id,
                "List": [{"TabName": "TABPAGE_1", "FieldName": "item_id", "Value": item_id}]
            }
        )

        # 2. Go to Locations tab
        await client.put(
            f"{ui_url}/api/ui/interactive/v2/tab",
            headers=headers,
            json={"WindowId": window_id, "PageName": "TABPAGE_17"}
        )

        # 3. Find the row index for this location
        resp = await client.get(
            f"{ui_url}/api/ui/interactive/v2/data?id={window_id}",
            headers=headers
        )
        data = resp.json()

        row_idx = None
        for dw in data:
            if "invloclist" in dw.get("Name", "").lower():
                cols = dw.get("Columns", [])
                rows = dw.get("Data", [])
                if "location_id" in cols:
                    loc_col_idx = cols.index("location_id")
                    for i, row in enumerate(rows):
                        if str(row[loc_col_idx]) == str(location_id):
                            row_idx = i
                            break

        if row_idx is None:
            return False

        # 4. Select target row
        await client.put(
            f"{ui_url}/api/ui/interactive/v2/row",
            headers=headers,
            json={"WindowId": window_id, "DatawindowName": "invloclist", "Row": row_idx}
        )

        # 5. WORKAROUND: Select row+1 to push data through
        await client.put(
            f"{ui_url}/api/ui/interactive/v2/row",
            headers=headers,
            json={"WindowId": window_id, "DatawindowName": "invloclist", "Row": row_idx + 1}
        )

        # 6. Go to Location Detail tab
        await client.put(
            f"{ui_url}/api/ui/interactive/v2/tab",
            headers=headers,
            json={"WindowId": window_id, "PageName": "TABPAGE_18"}
        )

        # 7. Verify correct location is showing
        resp = await client.get(
            f"{ui_url}/api/ui/interactive/v2/data?id={window_id}",
            headers=headers
        )
        data = resp.json()
        for dw in data:
            if "inv_loc_detail" in dw.get("Name", "").lower():
                cols = dw.get("Columns", [])
                rows = dw.get("Data", [])
                if rows and "location_id" in cols:
                    current_loc = rows[0][cols.index("location_id")]
                    if str(current_loc) != str(location_id):
                        return False  # Wrong location showing

        # 8. Change product_group_id
        resp = await client.put(
            f"{ui_url}/api/ui/interactive/v2/change",
            headers=headers,
            json={
                "WindowId": window_id,
                "List": [{
                    "TabName": "TABPAGE_18",
                    "FieldName": "product_group_id",
                    "Value": new_product_group_id,
                    "DatawindowName": "inv_loc_detail"
                }]
            }
        )
        if resp.json().get("Status") != 1:
            return False

        # 9. Save
        resp = await client.put(
            f"{ui_url}/api/ui/interactive/v2/data",
            headers=headers,
            json=window_id
        )
        return resp.json().get("Status") == 1

    finally:
        await client.delete(
            f"{ui_url}/api/ui/interactive/v2/window",
            headers=headers,
            params={"windowId": window_id}
        )
```

**Key Points:**
- Window: `Item` service (not `InventoryMaster` or `InventorySheet`)
- Locations list: `TABPAGE_17` / `invloclist`
- Location detail: `TABPAGE_18` / `inv_loc_detail`
- Field: `product_group_id` (char 8)
- Always use the row+1 workaround for reliable row selection

---

## Related

- [Authentication](00-Authentication.md)
- [API Selection Guide](01-API-Selection-Guide.md)
- [Transaction API](03-Transaction-API.md)
- [scripts/interactive/](https://github.com/mrwuss/p21-api-documentation/tree/master/scripts/interactive/) - Working examples
