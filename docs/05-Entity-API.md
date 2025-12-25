# Entity API

## Overview

The Entity API is a **stateless REST** API for simple CRUD (Create, Read, Update, Delete) operations on P21 business objects. It uses domain object models for straightforward data manipulation.

### Key Characteristics

- **Stateless** - No session management required
- **Entity-based** - Works with domain objects (Customer, Order, etc.)
- **Simple CRUD** - Get, Create, Update, Delete operations
- **Query support** - Filter results with query syntax
- **Extended properties** - Include related data in responses

### When to Use

- Simple lookups and queries
- Basic CRUD operations
- B2B integrations
- When you need cleaner domain object models

---

## Base URL

The Entity API uses the main P21 API base URL:

```
https://{hostname}/api/{category}/{entity}
```

Examples:
- `https://play.ifpusa.com/api/sales/customers`
- `https://play.ifpusa.com/api/sales/orders`
- `https://play.ifpusa.com/api/inventory/parts`

---

## Common Endpoints

### Sales

| Endpoint | Description |
|----------|-------------|
| `/api/sales/customers` | Customer records |
| `/api/sales/customers/{id}` | Single customer |
| `/api/sales/orders` | Sales orders |
| `/api/sales/orders/{id}` | Single order |
| `/api/sales/invoices` | Invoices |
| `/api/sales/quotes` | Quotes |

### Inventory

| Endpoint | Description |
|----------|-------------|
| `/api/inventory/parts` | Inventory items |
| `/api/inventory/parts/{id}` | Single item |
| `/api/inventory/warehouses` | Warehouses |
| `/api/inventory/locations` | Locations |

### Purchasing

| Endpoint | Description |
|----------|-------------|
| `/api/purchasing/suppliers` | Suppliers |
| `/api/purchasing/purchaseorders` | Purchase orders |

### Other

| Endpoint | Description |
|----------|-------------|
| `/api/contacts` | Contacts |
| `/api/addresses` | Addresses |

---

## Authentication

Include the Bearer token in the Authorization header:

```http
GET /api/sales/customers HTTP/1.1
Host: play.ifpusa.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

See [Authentication](00-Authentication.md) for token generation.

---

## CRUD Operations

### Create (POST)

To create a new record:

1. Get a template: `GET /api/sales/customers/new`
2. Fill in the required fields
3. POST the object: `POST /api/sales/customers`

**Key Point**: The absence of key fields indicates a new record.

```http
POST /api/sales/customers
Content-Type: application/json

{
    "CustomerName": "New Customer",
    "Address1": "123 Main St",
    "City": "Cedar Rapids",
    "State": "IA"
}
```

### Read (GET)

Get all records:
```
GET /api/sales/customers
```

Get single record by ID:
```
GET /api/sales/customers/100198
```

### Update (POST)

To update an existing record:

1. Include the key field(s) in the object
2. POST the object

**Key Point**: The presence of key fields indicates an update.

```http
POST /api/sales/customers

{
    "CustomerCode": 100198,
    "CustomerName": "Updated Name"
}
```

### Delete (DELETE)

```
DELETE /api/sales/customers/100198
```

---

## Query Syntax

Filter results using the `$query` parameter:

```
GET /api/sales/customers?$query=State eq 'IA'
```

### Comparison Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `eq` | Equal | `LastName eq 'Brown'` |
| `ne` | Not equal | `LastName ne null` |
| `gt` | Greater than | `CreditLimit gt 1000` |
| `ge` | Greater than or equal | `CreditLimit ge 1000` |
| `lt` | Less than | `CreditLimit lt 1000` |
| `le` | Less than or equal | `CreditLimit le 1000` |

### Logical Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `and` | Logical AND | `CreditLimit ge 1000 and State eq 'CO'` |
| `or` | Logical OR | `State eq 'CO' or State eq 'PA'` |
| `not` | Logical NOT | `not (CustomerCode eq 1)` |

### String Functions

| Function | Description | Example |
|----------|-------------|---------|
| `startswith` | Starts with | `startswith(CustomerName, 'ABC')` |
| `endswith` | Ends with | `endswith(CustomerName, 'Inc')` |
| `substringof` | Contains | `substringof('copper', ItemDesc)` |

---

## Extended Properties

Include related data using the `extendedproperties` parameter:

Get order with all related data:
```
GET /api/sales/orders/100999?extendedproperties=*
```

Get order with just line items:
```
GET /api/sales/orders/100999?extendedproperties=Lines
```

---

## Async Operations

For long-running operations (orders, POs), use async endpoints:

### Submit Async

```http
POST /api/sales/orders/async
Content-Type: application/json

{
    "CustomerCode": 100198,
    "Lines": [...]
}
```

Response:
```json
{
    "RequestId": "ad8f6f74-bc27-4324-a812-0ca7d6cc6a7d",
    "Status": "Active"
}
```

### Check Status

```
GET /api/sales/orders/async?id=ad8f6f74-bc27-4324-a812-0ca7d6cc6a7d
```

### With Callback

```json
{
    "Content": {
        "CustomerCode": 100198,
        "Lines": [...]
    },
    "Callback": {
        "Url": "https://your-server.com/webhook",
        "Method": "POST",
        "ContentType": "application/json"
    }
}
```

---

## Response Format

### Success Response

Single record:
```json
{
    "CustomerCode": 100198,
    "CustomerName": "ABC Company",
    "Address1": "123 Main St",
    "City": "Cedar Rapids",
    "State": "IA"
}
```

Collection:
```json
[
    {"CustomerCode": 100198, "CustomerName": "ABC Company"},
    {"CustomerCode": 100199, "CustomerName": "XYZ Corp"}
]
```

### Error Response

```json
{
    "Message": "The request is invalid.",
    "Errors": [
        "CustomerName is required"
    ]
}
```

---

## Python Examples

### Basic Query

```python
import httpx

response = httpx.get(
    f"{base_url}/api/sales/customers",
    params={"$query": "State eq 'IA'"},
    headers={"Authorization": f"Bearer {token}"},
    verify=False
)

customers = response.json()
for customer in customers:
    print(f"{customer['CustomerCode']}: {customer['CustomerName']}")
```

### Get with Extended Properties

```python
response = httpx.get(
    f"{base_url}/api/sales/orders/100999",
    params={"extendedproperties": "*"},
    headers={"Authorization": f"Bearer {token}"},
    verify=False
)

order = response.json()
print(f"Order: {order['OrderNumber']}")
for line in order.get("Lines", []):
    print(f"  - {line['ItemId']}: {line['Quantity']}")
```

### Create Record

```python
# Get template
template = httpx.get(
    f"{base_url}/api/sales/customers/new",
    headers={"Authorization": f"Bearer {token}"},
    verify=False
).json()

# Fill required fields
template["CustomerName"] = "New Customer"
template["Address1"] = "123 Main St"
template["City"] = "Cedar Rapids"
template["State"] = "IA"

# Create
response = httpx.post(
    f"{base_url}/api/sales/customers",
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    },
    json=template,
    verify=False
)
```

---

## Working Example Scripts

See the `scripts/entity/` directory:

| Script | Description |
|--------|-------------|
| `01_list_entities.py` | Discover available entities |
| `02_query_entity.py` | Query with filters |
| `03_create_entity.py` | Create a record |
| `04_update_entity.py` | Update existing record |

---

## Best Practices

1. **Use templates** - Get `/new` before creating to see available fields
2. **Query efficiently** - Use `$query` to filter server-side
3. **Extended properties sparingly** - Only request related data when needed
4. **Check for key fields** - Include keys for updates, omit for creates
5. **Handle async for orders** - Large orders should use async endpoint

---

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Invalid/expired token | Refresh token |
| 404 Not Found | Entity/endpoint doesn't exist | Check endpoint path, verify Entity API is enabled |
| 400 Bad Request | Invalid data | Check required fields |
| "Field is required" | Missing required field | Check template for requirements |

**Note**: Entity API availability depends on P21 server configuration. Some endpoints may require specific licensing or middleware setup. Check your middleware documentation page for available endpoints.

---

## Entity API vs OData

| Feature | Entity API | OData |
|---------|------------|-------|
| Operations | Full CRUD | Read-only |
| Format | Domain objects | Table rows |
| Queries | `$query` parameter | OData `$filter` |
| Extended data | `extendedproperties` | Not available |
| Use case | Business objects | Raw data access |

---

## Related

- [Authentication](00-Authentication.md)
- [API Selection Guide](01-API-Selection-Guide.md)
- [OData API](02-OData-API.md)
- [scripts/entity/](../scripts/entity/) - Working examples
