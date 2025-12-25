# Transaction API

## Overview

The Transaction API is a **stateless RESTful** web service for bulk data manipulation in P21. It allows creating and updating records across any P21 window without maintaining session state.

### Key Characteristics

- **Stateless** - No session management required
- **Bulk operations** - Process multiple records in single request
- **Service-based** - Each P21 window maps to a service
- **JSON or XML** - Supports both formats
- **Async support** - Long operations can run asynchronously

### When to Use

- Creating multiple records (orders, invoices, etc.)
- Bulk updates
- Automated data import
- Integration with external systems

---

## Endpoints

All Transaction API endpoints use the UI Server URL. First, obtain the UI Server URL:

```
GET https://{hostname}/api/ui/router/v1?urlType=external
```

Then use the returned URL as base:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v2/services` | GET | List available services |
| `/api/v2/definition/{name}` | GET | Get service schema |
| `/api/v2/defaults/{name}` | GET | Get default values |
| `/api/v2/transaction/get` | POST | Retrieve existing records |
| `/api/v2/transaction` | POST | Create or update records |
| `/api/v2/transaction/async` | POST | Async create/update |
| `/api/v2/transaction/async/callback` | POST | Async with callback |
| `/api/v2/transaction/async?id={id}` | GET | Check async status |

---

## Authentication

Include the Bearer token in the Authorization header:

```http
POST /api/v2/transaction HTTP/1.1
Host: {ui-server-host}
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json
```

See [Authentication](00-Authentication.md) for token generation.

---

## Request Structure

### TransactionSet

The main request body for create/update operations:

```json
{
    "Name": "ServiceName",
    "UseCodeValues": false,
    "Transactions": [
        {
            "Status": "New",
            "DataElements": [
                {
                    "Name": "TABPAGE_1.table_name",
                    "Type": "Form",
                    "Keys": [],
                    "Rows": [
                        {
                            "Edits": [
                                {"Name": "field_name", "Value": "field_value"}
                            ],
                            "RelativeDateEdits": []
                        }
                    ]
                }
            ]
        }
    ]
}
```

### Key Fields

| Field | Description |
|-------|-------------|
| `Name` | Service name (e.g., "Order", "SalesPricePage") |
| `UseCodeValues` | If `true`, use code values; if `false`, use display values |
| `Status` | Must be "New" for create operations |
| `DataElements` | Array of tabs/sections in the window |
| `Type` | "Form" for single record, "List" for multiple |
| `Keys` | Key fields for List-type elements |
| `Edits` | Array of field name/value pairs |

---

## Common Services

| Service | P21 Window | Purpose |
|---------|------------|---------|
| `Order` | Order Entry | Create/edit sales orders |
| `Invoice` | Invoice Entry | Create/edit invoices |
| `Customer` | Customer Maintenance | Customer records |
| `Supplier` | Supplier Maintenance | Supplier records |
| `SalesPricePage` | Sales Price Page | Price page management |
| `PurchaseOrder` | Purchase Order Entry | Create POs |
| `InventoryMaster` | Inventory Maintenance | Item records |
| `Task` | Task Entry | Create tasks/activities |

---

## Response Format

### Success Response

```json
{
    "Messages": ["Transaction 1:: "],
    "Results": {
        "Name": "Order",
        "Transactions": [
            {
                "DataElements": [
                    {
                        "Name": "TABPAGE_1.order",
                        "Rows": [{
                            "Edits": [
                                {"Name": "order_no", "Value": "1013938"}
                            ]
                        }]
                    }
                ],
                "Status": "Passed"
            }
        ]
    },
    "Summary": {
        "Succeeded": 1,
        "Failed": 0,
        "Other": 0
    }
}
```

### Error Response

```json
{
    "Messages": [
        "Transaction 1:: Customer ID is required"
    ],
    "Results": null,
    "Summary": {
        "Succeeded": 0,
        "Failed": 1,
        "Other": 0
    }
}
```

---

## Field Order Matters

For some services, the order of fields in the request is significant. The API processes fields sequentially, and some fields trigger validation or auto-population of other fields.

### Example: SalesPricePage

Fields must be set in this order:
1. `price_page_type_cd` - Triggers type-specific validation
2. `company_id` - Required before product group
3. `product_group_id` or `discount_group_id`
4. `supplier_id`
5. Other fields...

---

## UseCodeValues

This setting controls how dropdown/checkbox values are interpreted:

| UseCodeValues | Pass | Example |
|---------------|------|---------|
| `false` (default) | Display value | `"Cancelled": "ON"` |
| `true` | Code value | `"Cancelled": "Y"` |

**Recommendation**: Use `false` (display values) for better readability.

---

## Async Operations

For long-running operations, use the async endpoint:

### Submit Async Request

```
POST /api/v2/transaction/async
```

Response includes a request ID:

```json
{
    "RequestId": "ad8f6f74-bc27-4324-a812-0ca7d6cc6a7d",
    "Status": "Active"
}
```

### Check Status

```
GET /api/v2/transaction/async?id=ad8f6f74-bc27-4324-a812-0ca7d6cc6a7d
```

Response:

```json
{
    "RequestId": "ad8f6f74-bc27-4324-a812-0ca7d6cc6a7d",
    "Status": "Complete",
    "Messages": "...",
    "CompletedDate": "2025-01-15T16:34:53"
}
```

Status values: `Active`, `Complete`, `Failed`

### With Callback

Use the callback endpoint to receive notification when complete:

```json
{
    "Content": {
        "Name": "Order",
        "Transactions": [...]
    },
    "Callback": {
        "Url": "https://your-server.com/webhook",
        "Method": "POST",
        "ContentType": "application/json",
        "Headers": [
            {"Name": "X-API-Key", "Value": "your-key"}
        ]
    }
}
```

---

## Examples

### Get Service Definition

```python
import httpx

response = httpx.get(
    f"{ui_server_url}/api/v2/definition/Order",
    headers={"Authorization": f"Bearer {token}"},
    verify=False
)

definition = response.json()
# definition["Template"] - blank template for creating records
# definition["TransactionDefinition"] - field definitions with valid values
```

### Create Order

```python
payload = {
    "Name": "Order",
    "UseCodeValues": False,
    "Transactions": [{
        "Status": "New",
        "DataElements": [
            {
                "Name": "TABPAGE_1.order",
                "Type": "Form",
                "Keys": [],
                "Rows": [{
                    "Edits": [
                        {"Name": "customer_id", "Value": "100198"}
                    ],
                    "RelativeDateEdits": []
                }]
            },
            {
                "Name": "TP_ITEMS.items",
                "Type": "List",
                "Keys": [],
                "Rows": [{
                    "Edits": [
                        {"Name": "oe_order_item_id", "Value": "ITEM123"},
                        {"Name": "unit_quantity", "Value": "1"}
                    ],
                    "RelativeDateEdits": []
                }]
            }
        ]
    }]
}

response = httpx.post(
    f"{ui_server_url}/api/v2/transaction",
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    },
    json=payload,
    verify=False
)
```

---

## Python Examples

See the `scripts/transaction/` directory for working examples:

| Script | Description |
|--------|-------------|
| `01_list_services.py` | List all available services |
| `02_get_definition.py` | Get service schema/template |
| `03_create_single.py` | Create a single record |
| `04_create_bulk.py` | Create multiple records |
| `05_update_existing.py` | Update existing records |
| `06_async_operations.py` | Use async endpoints |
| `test_session_pool.py` | Session pool diagnostic |

---

## Known Issues

### Session Pool Contamination

The Transaction API uses a session pool on the server. When a transaction fails mid-process (e.g., due to validation errors), the session may be left in a "dirty" state with dialogs still open. Subsequent requests using that pooled session may fail with errors like:

- "Unexpected response window"
- "Object reference not set"
- Validation errors for fields that weren't changed

**Workarounds:**

1. **Use the async endpoint** - Creates dedicated session per request
2. **Implement retry logic** - Retry failed requests after a delay
3. **Add jitter** - Random delays between rapid requests
4. **Restart middleware** - Clears the session pool (last resort)

See [Session Pool Troubleshooting](07-Session-Pool-Troubleshooting.md) for detailed analysis.

---

## Best Practices

1. **Get definition first** - Fetch the service definition to understand required fields
2. **Use display values** - Set `UseCodeValues: false` for clarity
3. **Check Summary** - Always check `Summary.Succeeded` and `Summary.Failed`
4. **Handle failures gracefully** - Messages array contains error details
5. **Consider async for bulk** - Use async endpoint for large batches
6. **Add delays between requests** - Prevents session pool issues
7. **Validate locally first** - Check required fields before sending

---

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Invalid/expired token | Refresh token |
| 400 Bad Request | Malformed request | Check JSON structure |
| "Required field missing" | Missing required field | Check definition for required fields |
| "Unexpected response window" | Session pool dirty | Retry or use async |
| "Invalid value" | Wrong dropdown value | Use `UseCodeValues: false` with display values |

---

## Related

- [Authentication](00-Authentication.md)
- [API Selection Guide](01-API-Selection-Guide.md)
- [Session Pool Troubleshooting](07-Session-Pool-Troubleshooting.md)
- [scripts/transaction/](https://github.com/mrwuss/p21-api-documentation/tree/master/scripts/transaction/) - Working examples
