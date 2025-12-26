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

### Context Manager Usage

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
| Purchase Order Entry | PurchaseOrder | Purchase orders |
| Inventory Maintenance | InventoryMaster | Inventory items |

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

## Related

- [Authentication](00-Authentication.md)
- [API Selection Guide](01-API-Selection-Guide.md)
- [Transaction API](03-Transaction-API.md)
- [scripts/interactive/](https://github.com/mrwuss/p21-api-documentation/tree/master/scripts/interactive/) - Working examples
