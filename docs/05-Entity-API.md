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

### Customers, Vendors, Contacts

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/entity/{resource}/ping` | Health check |
| `GET` | `/api/entity/{resource}/new` | Get blank template |
| `GET` | `/api/entity/{resource}/{key}` | Get single record |
| `GET` | `/api/entity/{resource}/` | List all records (trailing slash required) |
| `GET` | `/api/entity/{resource}/?$query=...` | Query with filter |
| `POST` | `/api/entity/{resource}` | Create (no key in body) |
| `PUT` | `/api/entity/{resource}/{key}` | Update (key in URL) |

### Addresses (Limited)

Addresses have a **reduced** set of operations — no `/new` template and no update:

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/entity/addresses/ping` | Health check |
| `GET` | `/api/entity/addresses/{addressId}` | Get single address |
| `GET` | `/api/entity/addresses/` | List all addresses |
| `GET` | `/api/entity/addresses/?$query=...` | Query with filter |
| `POST` | `/api/entity/addresses` | Create new address |

> **No `/new` or PUT:** The address resource does not define a template endpoint or an update method in the SDK interface. The `/new` endpoint returns 500 because it doesn't exist (not a bug). To update an address, use the Interactive API or direct SQL.

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

See [Authentication](00-Authentication.md) for token generation. Per the SDK, tokens expire after **24 hours**.

### Consumer Key Behavior

When using Consumer Key authentication with the Entity API:

| Scenario | Behavior |
|----------|----------|
| No username | Uses default P21 user (admin from `Web.config`) |
| With AD username | Include domain (e.g., `emea\user.name`) |
| With SQL username | Use plain username (e.g., `admin`) |

---

## CRUD Operations

### Key Rule: Presence = Update, Absence = Insert

The Entity API determines whether to insert or update based on whether key fields are present:

- **Key absent** (e.g., `CustomerId` is null or omitted) → **Insert** (create new record, system generates ID)
- **Key present** (e.g., `CustomerId: 10`) → **Update** (modify existing record)

This applies to all entities. When creating, omit or null-out the ID field. When updating, include the key both in the URL and body.

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

### Address Limitations

The Address entity has a reduced API surface compared to other entities:

- **No `/new` template** — `GET /api/entity/addresses/new` returns 500 (endpoint not implemented)
- **No PUT (update)** — The SDK interface only defines `CreateAddress`, not `UpdateAddress`
- **Create only** — You can create and read addresses, but not update them via this API

To update an existing address, use the Interactive API (Address Maintenance window) or direct SQL.

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
GET /api/entity/customers/?$query=startswith(CustomerName, 'ABC')
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
| `substringof` | Contains | `substringof('Supply', VendorName)` |

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

## Template Fields (Complete Reference)

Every field for each entity is listed below, sourced directly from the `/new` template endpoints. Extended properties (nested objects) are listed separately from data fields.

### Customer Template (102 fields)

Complete field list from `GET /api/entity/customers/new`:

**Extended Properties (null by default, populate via `extendedproperties` parameter):**

| # | Field | Type | Default |
|---|-------|------|---------|
| 1 | `CustomerAddress` | null | null |
| 2 | `CustomerEDITransactions` | null | null |
| 3 | `CustomerSalesreps` | null | null |
| 4 | `CustomerTerms` | null | null |
| 5 | `CustomerDealerTypes` | null | null |
| 6 | `CustomerRestrictedClasses` | null | null |
| 7 | `CustomerContacts` | null | null |
| 8 | `CustomerShipTos` | null | null |
| 9 | `CustomerPriceLibraries` | null | null |

**Data Fields:**

| # | Field | Type | Default |
|---|-------|------|---------|
| 10 | `CompanyId` | string | `""` |
| 11 | `CustomerId` | null | null |
| 12 | `CustomerName` | string | `""` |
| 13 | `SalesrepId` | string | `""` |
| 14 | `TermsId` | string | `""` |
| 15 | `CodRequiredFlag` | string | `""` |
| 16 | `GenerateFinanceCharges` | string | `""` |
| 17 | `FcCycle` | string | `""` |
| 18 | `MinimumFinanceCharge` | null | null |
| 19 | `FinanceChargeShipToId` | null | null |
| 20 | `FcGraceDays` | null | null |
| 21 | `FcPercentage` | null | null |
| 22 | `LastFcDate` | null | null |
| 23 | `CreditStatus` | string | `""` |
| 24 | `CreditLimit` | null | null |
| 25 | `CreditLimitPerOrder` | null | null |
| 26 | `CreditLimitCheckAtShipment` | string | `""` |
| 27 | `OverrideRevenueByItem` | string | `""` |
| 28 | `OrderAcknowledgments` | string | `""` |
| 29 | `PoNoRequired` | string | `""` |
| 30 | `LimitMaxShipmentsPerOrder` | null | null |
| 31 | `MinimumOrderDollarAmount` | null | null |
| 32 | `PickTicketType` | string | `""` |
| 33 | `DefaultDisposition` | string | `""` |
| 34 | `BillToContactId` | string | `""` |
| 35 | `InvoicePrintQty` | int | `1` |
| 36 | `GenerateCustomerStatements` | string | `""` |
| 37 | `Taxable` | string | `""` |
| 38 | `StatementBalance` | string | `"O"` |
| 39 | `SicCode` | null | null |
| 40 | `Class1id` | string | `""` |
| 41 | `Class2id` | string | `""` |
| 42 | `Class3id` | string | `""` |
| 43 | `Class4id` | string | `""` |
| 44 | `Class5id` | string | `""` |
| 45 | `StateSalesTaxExemptionNo` | string | `""` |
| 46 | `StateExciseTaxExemptionNo` | string | `""` |
| 47 | `FederalExemptionNumber` | string | `""` |
| 48 | `OtherExemptionNumber` | string | `""` |
| 49 | `SecurityInfo` | string | `""` |
| 50 | `InterchgReceiverId` | string | `""` |
| 51 | `InternationalSAN` | string | `""` |
| 52 | `TradingPartnerName` | string | `""` |
| 53 | `PrintPricesOnPackinglist` | string | `""` |
| 54 | `InvoiceBatchNumber` | null | null |
| 55 | `StatementBatchNumber` | null | null |
| 56 | `JobPricing` | string | `"N"` |
| 57 | `DefaultRebateLocationId` | null | null |
| 58 | `CurrencyId` | null | null |
| 59 | `OverrideProfitLimit` | string | `""` |
| 60 | `MinimumOrderLineProfit` | null | null |
| 61 | `MaximumOrderLineProfit` | null | null |
| 62 | `MinimumOrderProfit` | null | null |
| 63 | `MaximumOrderProfit` | null | null |
| 64 | `DateAcctOpened` | null | null |
| 65 | `PrintPackinglistInShipping` | string | `""` |
| 66 | `InclNonAllocOnTixText` | string | `""` |
| 67 | `ExcludeCanceldFromPickTix` | string | `""` |
| 68 | `InclNonAllocOnListText` | string | `""` |
| 69 | `ExcludeCanceldFromPackList` | string | `""` |
| 70 | `AlwaysUseJobPrice` | string | `""` |
| 71 | `AllowNonJobItem` | string | `""` |
| 72 | `PromptForNonJobItem` | string | `""` |
| 73 | `AllowExceedJobQty` | string | `""` |
| 74 | `PrintLotAttribOnInvoice` | string | `""` |
| 75 | `PrintLotAttribOnPacklist` | string | `""` |
| 76 | `OverTolerancePercentage` | null | null |
| 77 | `UnderTolerancePercentage` | null | null |
| 78 | `CustomerType` | string | `""` |
| 79 | `LeadSourceId` | string | `""` |
| 80 | `UseAllContracts` | string | `""` |
| 81 | `JobNumberRequired` | string | `""` |
| 82 | `PromiseDateBuffer` | null | null |
| 83 | `FreightChargeId` | string | `""` |
| 84 | `OrderPriorityId` | string | `""` |
| 85 | `UseSystemUPSHandlingCharge` | string | `""` |
| 86 | `UpsHandlingCharge` | null | null |
| 87 | `DaysOverdueForCreditHold` | null | null |
| 88 | `Delete` | bool | `false` |
| 89 | `SendOutsideUseDocs` | string | `"N"` |
| 90 | `SendOutsideUsePrint` | string | `"N"` |
| 91 | `SendOutsideUseFax` | string | `"N"` |
| 92 | `SendOutsideUseEmail` | string | `"N"` |
| 93 | `LegacyId` | string | `""` |
| 94 | `PricingMethod` | string | `""` |
| 95 | `RequirePaymentUponReleaseOfItems` | bool | `false` |
| 96 | `CreditLimitUsed` | null | null |
| 97 | `CreditLimitAvailable` | null | null |
| 98 | `CorporateCreditLimit` | null | null |
| 99 | `CorporateCreditLimitAvailable` | null | null |
| 100 | `WebEnabledFlag` | string | `"N"` |
| 101 | `UserDefinedFields` | object | `{}` |
| 102 | `ObjectName` | string | `"customer"` |

### Vendor Template (50 fields)

Complete field list from `GET /api/entity/vendors/new`:

**Extended Properties (null by default, populate via `extendedproperties` parameter):**

| # | Field | Type | Default |
|---|-------|------|---------|
| 1 | `VendorSuppliers` | null | null |
| 2 | `VendorAddress` | null | null |
| 3 | `VendorPurchaseAccounts` | null | null |
| 4 | `VendorContract` | null | null |

**Data Fields:**

| # | Field | Type | Default |
|---|-------|------|---------|
| 5 | `CompanyId` | string | `""` |
| 6 | `VendorName` | string | `""` |
| 7 | `CurrencyId` | null | null |
| 8 | `CurrencyDesc` | string | `""` |
| 9 | `ApAccountNo` | string | `""` |
| 10 | `DefaultTermsId` | string | `""` |
| 11 | `DefaultInvoiceDesc` | string | `""` |
| 12 | `AlwaysTakeTerms` | string | `""` |
| 13 | `JobIdRequired` | string | `"N"` |
| 14 | `Class1id` | string | `""` |
| 15 | `Class2id` | string | `""` |
| 16 | `Class3id` | string | `""` |
| 17 | `Class4id` | string | `""` |
| 18 | `Class5id` | string | `""` |
| 19 | `Incorporated` | string | `"N"` |
| 20 | `Default1099Type` | int | `7` |
| 21 | `SecurityInfo` | string | `""` |
| 22 | `InterchgReceiverId` | string | `""` |
| 23 | `IntlSan` | string | `""` |
| 24 | `DefaultPayFreightTo` | string | `"V"` |
| 25 | `GeneralLiabExpirationDate` | null | null |
| 26 | `WorkersCompExpirationDate` | null | null |
| 27 | `TradingPartnerName` | string | `""` |
| 28 | `VendorId` | null | null |
| 29 | `TrackRebates` | string | `""` |
| 30 | `RebateAccountNo` | string | `""` |
| 31 | `RebateAllowanceAccountNo` | string | `""` |
| 32 | `AttorneyFeeFlag` | string | `""` |
| 33 | `Irs1099State1` | string | `""` |
| 34 | `Irs1099State1IdNo` | string | `""` |
| 35 | `Irs1099State2` | string | `""` |
| 36 | `Irs1099State2IdNo` | string | `""` |
| 37 | `CommissionReceivableAcct` | string | `""` |
| 38 | `CommissionRevenueAcct` | string | `""` |
| 39 | `CommissionAllowanceAcct` | string | `""` |
| 40 | `WarrantyReceivableAcct` | string | `""` |
| 41 | `WarrantyRevenueAcct` | string | `""` |
| 42 | `WarrantyAllowanceAcct` | string | `""` |
| 43 | `VendorTypeDesc` | string | `""` |
| 44 | `IntrastatFlag` | string | `""` |
| 45 | `ConsignmentCountry` | string | `""` |
| 46 | `EuMemberFlag` | string | `"N"` |
| 47 | `Delete` | bool | `false` |
| 48 | `LegacyId` | string | `""` |
| 49 | `UserDefinedFields` | object | `{}` |
| 50 | `ObjectName` | string | `"vendor"` |

### Contact Template (40 fields)

Complete field list from `GET /api/entity/contacts/new`:

**Extended Properties (null by default, populate via `extendedproperties` parameter):**

| # | Field | Type | Default |
|---|-------|------|---------|
| 1 | `ContactDocuments` | null | null |
| 2 | `ContactLeadSources` | null | null |
| 3 | `ContactLinks` | null | null |
| 4 | `ContactLists` | null | null |
| 5 | `ContactSalesreps` | null | null |

**Data Fields:**

| # | Field | Type | Default |
|---|-------|------|---------|
| 6 | `Salutation` | string | `""` |
| 7 | `FirstName` | string | `""` |
| 8 | `Mi` | string | `""` |
| 9 | `LastName` | string | `""` |
| 10 | `Title` | string | `""` |
| 11 | `AddressId` | null | null |
| 12 | `Mailstop` | string | `""` |
| 13 | `NoOfCycleDays` | null | null |
| 14 | `Comments` | string | `""` |
| 15 | `DirectPhone` | string | `""` |
| 16 | `PhoneExt` | string | `""` |
| 17 | `DirectFax` | string | `""` |
| 18 | `FaxExt` | string | `""` |
| 19 | `Beeper` | string | `""` |
| 20 | `Cellular` | string | `""` |
| 21 | `Class1id` | string | `""` |
| 22 | `Class2id` | string | `""` |
| 23 | `Class3id` | string | `""` |
| 24 | `Class4id` | string | `""` |
| 25 | `Class5id` | string | `""` |
| 26 | `HomeAddress1` | string | `""` |
| 27 | `HomeAddress2` | string | `""` |
| 28 | `HomePhone` | string | `""` |
| 29 | `HomeFax` | string | `""` |
| 30 | `HomeEmailAddress` | string | `""` |
| 31 | `Birthday` | null | null |
| 32 | `Anniversary` | null | null |
| 33 | `EmailAddress` | string | `""` |
| 34 | `Url` | string | `""` |
| 35 | `CellularExt` | string | `""` |
| 36 | `Id` | string | `""` |
| 37 | `DeleteFlag` | string | `"N"` |
| 38 | `LoginId` | string | `""` |
| 39 | `UserDefinedFields` | object | `{}` |
| 40 | `ObjectName` | string | `"contacts"` |

### Address Fields (27 fields)

> **Note:** The Address resource does not have a `/new` template endpoint (this is by design, not a bug). The field list below is from an existing address record (`GET /api/entity/addresses/10`).

Complete field list:

| # | Field | Type | Description |
|---|-------|------|-------------|
| 1 | `CorpAddressId` | int | Corporate address ID |
| 2 | `MailAddress1` | string | Mailing address line 1 |
| 3 | `MailAddress2` | string | Mailing address line 2 |
| 4 | `MailAddress3` | string | Mailing address line 3 |
| 5 | `MailCity` | string | Mailing city |
| 6 | `MailState` | string | Mailing state |
| 7 | `MailPostalCode` | string | Mailing postal code |
| 8 | `MailCountry` | string | Mailing country |
| 9 | `CentralPhoneNumber` | string | Main phone number |
| 10 | `CentralFaxNumber` | string | Main fax number |
| 11 | `Alternative1099Name` | string | Alternative name for 1099 |
| 12 | `NameControl` | string | Name control |
| 13 | `PhysAddress1` | string | Physical address line 1 |
| 14 | `PhysAddress2` | string | Physical address line 2 |
| 15 | `PhysAddress3` | string | Physical address line 3 |
| 16 | `PhysCity` | string | Physical city |
| 17 | `PhysState` | string | Physical state |
| 18 | `PhysPostalCode` | string | Physical postal code |
| 19 | `PhysCountry` | string | Physical country |
| 20 | `Incorporated` | string | Incorporated flag (Y/N) |
| 21 | `EmailAddress` | string | Email address |
| 22 | `Url` | string | Website URL |
| 23 | `AddressId` | int | Address ID (key) |
| 24 | `Name` | string | Address/company name |
| 25 | `PhysCounty` | string | Physical county |
| 26 | `UserDefinedFields` | object | UDF container |
| 27 | `ObjectName` | string | Always `"address"` |

---

## Additional Endpoints

### SOAP Endpoints

In addition to the REST endpoints documented above, the Entity API also exposes SOAP web services:

| Version | Endpoint Pattern | Example |
|---------|-----------------|---------|
| SOAP v1 | `/api/entity/{Entity}Service` | `/api/entity/CustomerService` |
| SOAP v2 | `/api/entity/v2/{Entity}Service` | `/api/entity/v2/CustomerService` |

Available for: Customer, Vendor, Contact, Address. Use these if your integration platform prefers SOAP over REST.

### Mobile Endpoints

The P21 middleware also exposes mobile-specific entity endpoints with **additional entities** not available via the standard REST API:

| Endpoint | Entity |
|----------|--------|
| `mobile/entity/customers` | Customers |
| `mobile/entity/vendors` | Vendors |
| `mobile/entity/contacts` | Contacts |
| `mobile/entity/suppliers` | Suppliers (not in REST API) |
| `mobile/entity/users` | Users (not in REST API) |
| `mobile/entity/companies` | Companies (not in REST API) |

> **Note:** The mobile endpoints are designed for the P21 mobile application. Their request/response format may differ from the REST API. Use with caution for custom integrations.

### Endpoint Discovery

You can browse all available Entity API endpoints from the P21 middleware home page:

```
https://{hostname}/docs/
```

This lists every registered endpoint including REST, SOAP, and mobile resources.

---

## Error Codes

| Code | Name | Description |
|------|------|-------------|
| 200 | OK | Request processed successfully |
| 202 | Accepted | Async request acknowledged (for async endpoints) |
| 301 | Moved Permanently | Resource moved — check `Location` header |
| 307 | Temporary Redirect | List endpoint without trailing slash — follow redirect |
| 400 | Bad Request | Invalid parameters or data — check server logs |
| 401 | Unauthorized | Invalid token, expired token, or user marked as deleted in P21 |
| 404 | Not Found | Resource doesn't exist, wrong key format, or wrong URL pattern |
| 5xx | Server Error | Server-side error — check `p21soa.log` and `p21api.log` |

### Log File Locations

When troubleshooting 400/500 errors, check the server-side log files:

| Log | Purpose |
|-----|---------|
| `p21soa.log` | P21 SOA Architecture (routing, auth, middleware) |
| `p21api.log` | P21 Core Business Logic (validation, data operations) |

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
