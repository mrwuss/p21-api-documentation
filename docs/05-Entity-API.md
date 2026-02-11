# Entity API

> **Disclaimer:** This is unofficial, community-created documentation for Epicor Prophet 21 APIs. It is not affiliated with, endorsed by, or supported by Epicor Software Corporation. All product names, trademarks, and registered trademarks are property of their respective owners. Use at your own risk.

---

> **Status Update (February 2026):** The Entity API is **functional**. Previous reports of it being non-functional were due to incorrect endpoint URLs. The correct base path is `/api/entity/`, not `/api/sales/` or `/api/inventory/`.

---

## Overview

The Entity API is a **stateless REST** API for CRUD (Create, Read, Update, Delete) operations on P21 business objects. It uses domain object models and supports only **four entities**: Customer, Vendor, Contact, and Address.

### Key Characteristics

- **Stateless** - No session management required
- **Entity-based** - Works with domain objects (not raw table rows)
- **CRUD operations** - Get, Create, Update via REST
- **Query support** - Filter with `$query` parameter
- **Extended properties** - Include related/nested data in responses
- **User Defined Fields** - UDF support when enabled in admin
- **Dual format** - Supports both JSON and XML (`Accept` header)

### When to Use

- Customer, vendor, contact, or address lookups
- Basic CRUD on the 4 supported entities
- B2B integrations needing domain object models
- When you want cleaner data shapes than raw OData table rows

### Limitations

- **Only 4 entities** - No orders, items, invoices, POs, or other business objects
- **No inventory/sales entities** - Use Transaction or Interactive API for those
- **Limited coverage** - For broad data access, use OData (read) or Transaction API (write)

---

## Base URL

```
https://{hostname}/api/entity/{resource}
```

Examples:
- `https://play.p21server.com/api/entity/customers`
- `https://play.p21server.com/api/entity/vendors`
- `https://play.p21server.com/api/entity/contacts`
- `https://play.p21server.com/api/entity/addresses`

> **Warning:** Older documentation (including Epicor SDK reference guides) may show category-based URLs like `/api/sales/customers` or `/api/inventory/parts`. These **do not work** as Entity API endpoints. Always use `/api/entity/`.

---

## Available Entities

Only four entities are available via the Entity API:

| Entity | Endpoint | Key Format | Fields |
|--------|----------|------------|--------|
| **Customers** | `/api/entity/customers` | `{CompanyId}_{CustomerId}` | 102 |
| **Vendors** | `/api/entity/vendors` | `{CompanyId}_{VendorId}` | 50 |
| **Contacts** | `/api/entity/contacts` | `{Id}` (simple numeric) | 40 |
| **Addresses** | `/api/entity/addresses` | `{AddressId}` (simple numeric) | 27 |

### Composite Keys

Customers and Vendors require a **composite key** combining `CompanyId` and the entity ID, separated by an underscore:

```
/api/entity/customers/ACME_10          # CompanyId=ACME, CustomerId=10
/api/entity/vendors/ACME_28485        # CompanyId=ACME, VendorId=28485
```

- `CompanyId` is a **string** (e.g., `"ACME"`), not numeric
- Using just the numeric ID (e.g., `/customers/10`) returns 404
- The underscore can be URL-encoded (`%5F`) if needed

Contacts and Addresses use **simple numeric IDs**:

```
/api/entity/contacts/1
/api/entity/addresses/10
```

### Vendor ID vs Supplier ID

The Entity API `VendorId` is **not the same** as the OData `supplier_id`. These come from different database tables. To find the correct `VendorId`, query vendors through the Entity API or check the `vendor` table via OData.

---

## Endpoints Per Entity

Each entity supports the same set of endpoints:

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/entity/{resource}/ping` | Health check |
| `GET` | `/api/entity/{resource}/new` | Get blank template |
| `GET` | `/api/entity/{resource}/{key}` | Get single record |
| `GET` | `/api/entity/{resource}/` | List all records (trailing slash required) |
| `GET` | `/api/entity/{resource}/?$query=...` | Query with filter |
| `POST` | `/api/entity/{resource}` | Create (no key in body) |
| `PUT` | `/api/entity/{resource}/{key}` | Update (key in URL) |

### Trailing Slash on List Endpoints

List endpoints (`GET /api/entity/customers`) return a **307 redirect** to the same URL with a trailing slash (`/api/entity/customers/`). Configure your HTTP client to follow redirects:

```python
client = httpx.Client(follow_redirects=True, ...)
```

> **Note:** Be cautious with unfiltered list queries. The customers endpoint returned 19,896 records, contacts returned 58,639. Always use `$query` to filter when possible.

---

## Authentication

Include the Bearer token in the Authorization header:

```http
GET /api/entity/customers/ACME_10 HTTP/1.1
Host: play.p21server.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

See [Authentication](00-Authentication.md) for token generation.

### Consumer Key Behavior

When using Consumer Key authentication with the Entity API:

| Scenario | Behavior |
|----------|----------|
| No username | Uses default P21 user (admin from `Web.config`) |
| With AD username | Include domain (e.g., `emea\user.name`) |
| With SQL username | Use plain username (e.g., `admin`) |

---

## CRUD Operations

### Read (GET)

**Single record by key:**
```http
GET /api/entity/customers/ACME_10
Accept: application/json
```

**Response:**
```json
{
    "CompanyId": "ACME",
    "CustomerId": 10,
    "CustomerName": "ABC Supply Company",
    "SalesrepId": "1100",
    "TermsId": "1",
    "CreditStatus": "GOOD",
    "CreditLimit": 1.0,
    "Taxable": "Y",
    "CurrencyId": 1,
    "CustomerType": "COM",
    "CustomerAddress": null,
    "CustomerContacts": null,
    "CustomerShipTos": null,
    "UserDefinedFields": {},
    "ObjectName": "customer"
}
```

> **Note:** Nested objects (CustomerAddress, CustomerContacts, etc.) are `null` by default. Use `extendedproperties` to populate them.

### Create (POST)

1. Get a template: `GET /api/entity/customers/new`
2. Fill in required fields
3. POST without key fields (absence of key = insert)

```http
POST /api/entity/customers
Content-Type: application/json

{
    "CompanyId": "ACME",
    "CustomerName": "New Customer Inc.",
    "SalesrepId": "1100",
    "TermsId": "1",
    "CodRequiredFlag": "N",
    "Taxable": "Y"
}
```

### Update (PUT)

Include the composite key in the URL:

```http
PUT /api/entity/customers/ACME_10
Content-Type: application/json

{
    "CompanyId": "ACME",
    "CustomerId": 10,
    "CustomerName": "Updated Name"
}
```

### Delete

Per the SDK, set the `Delete` field to `true` on an update:

```http
PUT /api/entity/customers/ACME_10
Content-Type: application/json

{
    "CompanyId": "ACME",
    "CustomerId": 10,
    "Delete": true
}
```

> **Note:** Dedicated DELETE HTTP method is not documented in the SDK for any entity.

---

## Health Check (Ping)

Each entity has a `/ping` endpoint for verifying the service is running:

```http
GET /api/entity/customers/ping
```

**Response:**
```json
{
    "ResponseMessage": "success"
}
```

---

## Query Syntax

Filter results using the `$query` parameter on list endpoints:

```
GET /api/entity/customers/?$query=startswith(CustomerName, 'Parker')
```

> **Remember:** List endpoints redirect (307), so use a trailing slash or enable redirect following.

### Comparison Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `eq` | Equal | `CompanyId eq 'ACME'` |
| `ne` | Not equal | `LastName ne null` |
| `gt` | Greater than | `CreditLimit gt 1000` |
| `ge` | Greater than or equal | `CreditLimit ge 1000` |
| `lt` | Less than | `CreditLimit lt 1000` |
| `le` | Less than or equal | `CreditLimit le 1000` |

### Logical Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `and` | Logical AND | `CreditLimit ge 1000 and CreditStatus eq 'GOOD'` |
| `or` | Logical OR | `CreditStatus eq 'GOOD' or CreditStatus eq 'HOLD'` |
| `not` | Logical NOT | `not (CustomerId eq 0)` |

### String Functions

| Function | Description | Example |
|----------|-------------|---------|
| `startswith` | Starts with | `startswith(CustomerName, 'ABC')` |
| `endswith` | Ends with | `endswith(CustomerName, 'Inc.')` |
| `substringof` | Contains | `substringof('Parker', VendorName)` |

### Verified Query Examples

```
# Find customers by name prefix (returned 7 results)
GET /api/entity/customers/?$query=startswith(CustomerName, 'ABC')

# Find vendors by name prefix (returned 6 results)
GET /api/entity/vendors/?$query=startswith(VendorName, 'ABC')

# Filter by company
GET /api/entity/customers/?$query=CompanyId eq 'ACME'
```

---

## Extended Properties

Include related/nested data using the `extendedproperties` parameter:

**All nested objects:**
```
GET /api/entity/customers/ACME_10?extendedproperties=*
```

**Specific nested object:**
```
GET /api/entity/customers/ACME_10?extendedproperties=CustomerAddress
```

### Available Extended Properties by Entity

**Customer:**
- `CustomerAddress` - Mailing and physical address
- `CustomerEDITransactions` - EDI configuration
- `CustomerSalesreps` - Assigned sales reps
- `CustomerTerms` - Payment terms
- `CustomerDealerTypes` - Dealer type assignments
- `CustomerRestrictedClasses` - Restricted product classes
- `CustomerContacts` - Associated contacts
- `CustomerShipTos` - Ship-to addresses
- `CustomerPriceLibraries` - Price library assignments

**Vendor:**
- `VendorSuppliers` - Associated supplier records
- `VendorAddress` - Mailing and physical address
- `VendorPurchaseAccounts` - Purchase account configuration
- `VendorContract` - Contract information

**Contact:**
- `ContactDocuments` - Associated documents
- `ContactLeadSources` - Lead source tracking
- `ContactLinks` - Related entity links
- `ContactLists` - Mailing list membership
- `ContactSalesreps` - Assigned sales reps

### Example: Customer with Address

```http
GET /api/entity/customers/ACME_10?extendedproperties=CustomerAddress
```

```json
{
    "CompanyId": "ACME",
    "CustomerId": 10,
    "CustomerName": "ABC Supply Company",
    "CustomerAddress": {
        "CorpAddressId": 10,
        "MailAddress1": "123 Industrial Parkway",
        "MailCity": "Springfield",
        "MailState": "IL",
        "MailPostalCode": "62701",
        "MailCountry": "USA",
        "CentralPhoneNumber": "555-555-1234",
        "PhysAddress1": "123 Industrial Parkway",
        "PhysCity": "Springfield",
        "PhysState": "IL"
    }
}
```

---

## User Defined Fields

Entity API supports User Defined Fields (UDFs) when enabled in the P21 middleware.

### Enabling UDFs

1. Go to the Administration page: `https://{hostname}/docs/admin.aspx`
2. Toggle **"User Defined Field Enabled Setting"** to Enabled
3. Click **"Regenerate User Defined Fields"** if fields are not appearing

### UDF Behavior

- UDFs appear in the response under the `UserDefinedFields` property
- UDFs are subordinate to the parent entity (cannot be modified independently)
- When creating/updating, include UDF values in the `UserDefinedFields` object

---

## Response Format

### Single Record

```json
{
    "CompanyId": "ACME",
    "CustomerId": 10,
    "CustomerName": "ABC Supply Company",
    "SalesrepId": "1100",
    "CreditStatus": "GOOD",
    "UserDefinedFields": {},
    "ObjectName": "customer"
}
```

### Collection (List/Query)

```json
[
    {
        "CompanyId": "ACME",
        "CustomerId": 10,
        "CustomerName": "ABC Supply Company"
    },
    {
        "CompanyId": "ACME",
        "CustomerId": 20,
        "CustomerName": "ABC Supply Company"
    }
]
```

### Error Response

```json
{
    "DateTimeStamp": "2026-02-11T15:30:00",
    "ErrorMessage": "Your query did not yield any results. No resources found for query string \"GetById 100198\".",
    "ErrorType": "ResourceNotFoundException",
    "HostName": "P21SERVER",
    "InnerException": null,
    "LogId": "...",
    "StackTrace": "...",
    "UserId": "api_user"
}
```

### Content Types

Both JSON and XML are supported. Set via the `Accept` header:

```http
Accept: application/json
Accept: application/xml
```

XML response example (ping):
```xml
<?xml version="1.0"?>
<PingResponse>
    <ResponseMessage>success</ResponseMessage>
</PingResponse>
```

---

## Python Examples

### Setup

```python
import httpx

base_url = "https://play.p21server.com"

# Get token
token_resp = httpx.post(
    f"{base_url}/api/security/token/v2",
    json={"username": "api_user", "password": "password"},
    headers={"Accept": "application/json"},
    verify=False,
)
token = token_resp.json()["AccessToken"]

# Create client (must follow redirects for list endpoints)
client = httpx.Client(
    headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    },
    verify=False,
    follow_redirects=True,
)
```

### Health Check

```python
resp = client.get(f"{base_url}/api/entity/customers/ping")
print(resp.json())  # {"ResponseMessage": "success"}
```

### Get Single Customer

```python
resp = client.get(f"{base_url}/api/entity/customers/ACME_10")
customer = resp.json()
print(f"{customer['CustomerId']}: {customer['CustomerName']}")
# 10: ABC Supply Company
```

### Get Customer with Extended Properties

```python
resp = client.get(
    f"{base_url}/api/entity/customers/ACME_10",
    params={"extendedproperties": "CustomerAddress"},
)
customer = resp.json()
addr = customer["CustomerAddress"]
print(f"{addr['MailCity']}, {addr['MailState']} {addr['MailPostalCode']}")
# Springfield, IL 62701
```

### Query Customers

```python
resp = client.get(
    f"{base_url}/api/entity/customers/",
    params={"$query": "startswith(CustomerName, 'ABC')"},
)
customers = resp.json()
print(f"Found {len(customers)} customers")
for c in customers:
    print(f"  {c['CompanyId']}_{c['CustomerId']}: {c['CustomerName']}")
```

### Get Contact

```python
resp = client.get(f"{base_url}/api/entity/contacts/1")
contact = resp.json()
print(f"{contact['FirstName']} {contact['LastName']}")
# John Smith
```

### Create Customer

```python
# Get template first
template = client.get(f"{base_url}/api/entity/customers/new").json()

# Fill required fields
template["CompanyId"] = "ACME"
template["CustomerName"] = "New Customer Inc."
template["SalesrepId"] = "1100"
template["TermsId"] = "1"

# Create (POST without CustomerId = insert)
resp = client.post(
    f"{base_url}/api/entity/customers",
    json=template,
)
```

### Update Customer

```python
resp = client.put(
    f"{base_url}/api/entity/customers/ACME_10",
    json={
        "CompanyId": "ACME",
        "CustomerId": 10,
        "CustomerName": "Updated Customer Name",
    },
)
```

---

## Template Fields

Use the `/new` endpoint to discover all available fields for each entity.

### Customer Template (102 fields)

Key fields and their types from `GET /api/entity/customers/new`:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `CompanyId` | string | `""` | Company identifier (e.g., "ACME") |
| `CustomerId` | null | `null` | Auto-assigned on create |
| `CustomerName` | string | `""` | Customer name |
| `SalesrepId` | string | `""` | Default sales rep |
| `TermsId` | string | `""` | Payment terms |
| `CreditStatus` | string | `""` | Credit status (GOOD, HOLD, etc.) |
| `CreditLimit` | null | `null` | Credit limit amount |
| `Taxable` | string | `""` | Y/N taxable flag |
| `CurrencyId` | null | `null` | Currency |
| `CustomerType` | string | `""` | Customer type code |
| `Delete` | bool | `false` | Delete flag |
| `WebEnabledFlag` | string | `"N"` | Web access flag |
| `UserDefinedFields` | object | `{}` | UDF container |
| `ObjectName` | string | `"customer"` | Entity type |

### Vendor Template (50 fields)

Key fields from `GET /api/entity/vendors/new`:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `CompanyId` | string | `""` | Company identifier |
| `VendorId` | null | `null` | Auto-assigned on create |
| `VendorName` | string | `""` | Vendor name |
| `DefaultTermsId` | string | `""` | Payment terms |
| `ApAccountNo` | string | `""` | AP account number |
| `Incorporated` | string | `"N"` | Incorporated flag |
| `Default1099Type` | int | `7` | 1099 type |
| `TrackRebates` | string | `""` | Rebate tracking |
| `Delete` | bool | `false` | Delete flag |

### Contact Template (40 fields)

Key fields from `GET /api/entity/contacts/new`:

| Field | Type | Description |
|-------|------|-------------|
| `Salutation` | string | Salutation |
| `FirstName` | string | First name |
| `LastName` | string | Last name |
| `Title` | string | Job title |
| `AddressId` | null | Associated address ID |
| `DirectPhone` | string | Direct phone number |
| `EmailAddress` | string | Email address |
| `Id` | null | Auto-assigned on create |

### Address Template

> **Known Issue:** `GET /api/entity/addresses/new` returns a **500 error**. Use an existing address as a reference instead.

Key fields from address records:

| Field | Type | Description |
|-------|------|-------------|
| `CorpAddressId` | int | Corporate address ID |
| `AddressId` | int | Address ID |
| `Name` | string | Address name |
| `MailAddress1` | string | Mailing address line 1 |
| `MailCity` | string | Mailing city |
| `MailState` | string | Mailing state |
| `MailPostalCode` | string | Mailing postal code |
| `MailCountry` | string | Mailing country |
| `PhysAddress1` | string | Physical address line 1 |
| `CentralPhoneNumber` | string | Main phone |

---

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| 307 Redirect | List endpoint without trailing slash | Add trailing slash or enable `follow_redirects` |
| 401 Unauthorized | Invalid/expired token | Refresh token |
| 404 "No resources found" | Wrong key format or record doesn't exist | Use composite key (`ACME_10`) for customers/vendors |
| 404 HTML page | Endpoint doesn't exist | Verify you're using `/api/entity/` base path |
| 500 Server Error | Internal error (e.g., addresses `/new`) | Try a different approach or entity |

### Common Mistakes

1. **Wrong URL pattern** - Use `/api/entity/customers`, NOT `/api/sales/customers`
2. **Simple ID for customers** - Use `ACME_10`, NOT just `10`
3. **Missing redirect handling** - List endpoints return 307, must follow redirect
4. **Confusing VendorId with supplier_id** - These are different database tables
5. **Expecting orders/items/parts** - Only 4 entities exist (customers, vendors, contacts, addresses)

---

## Entity API vs Other APIs

| Feature | Entity API | OData | Transaction | Interactive |
|---------|------------|-------|-------------|-------------|
| Operations | CRUD | Read-only | Bulk CRUD | Stateful CRUD |
| Entities | 4 only | Any table/view | Many services | Any P21 window |
| Format | Domain objects | Table rows | XML payloads | Window fields |
| Session | Stateless | Stateless | Stateless | Stateful |
| Queries | `$query` | `$filter` (OData) | N/A | N/A |
| Extended data | `extendedproperties` | N/A | N/A | Tab navigation |
| Best for | Customer/vendor CRUD | Reporting, lookups | Bulk operations | Complex workflows |

---

## Related

- [Authentication](00-Authentication.md)
- [API Selection Guide](01-API-Selection-Guide.md)
- [OData API](02-OData-API.md) - For read-only queries on any table
- [Transaction API](03-Transaction-API.md) - For bulk data operations
- [Interactive API](04-Interactive-API.md) - For stateful CRUD with business logic
- [scripts/entity/](https://github.com/mrwuss/p21-api-documentation/tree/master/scripts/entity/) - Test scripts
