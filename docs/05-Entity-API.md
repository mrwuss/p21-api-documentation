# Entity API

> **Disclaimer:** This is unofficial, community-created documentation for Epicor Prophet 21 APIs. It is not affiliated with, endorsed by, or supported by Epicor Software Corporation. All product names, trademarks, and registered trademarks are property of their respective owners. Use at your own risk.

---

> **Status Update (February 2026):** The Entity API is **functional**. Previous reports of it being non-functional were due to incorrect endpoint URLs. The customer/vendor/contact/address entities live under `/api/entity/`.

---

## Terminology — Epicor's Naming (July 2026)

Epicor's own use of **"Entity API"** is broader than this document. In Epicor's naming (per the SOA middleware admin site):

- **"Entity API"** is an **umbrella term** covering two APIs:
  - the **REST API** — which includes the `/api/entity/`, `/api/inventory/`, and `/api/sales/` endpoint families, and
  - the **eCommerce API** (also called the Entity SOAP API).
- **URL segments are arbitrary** — the word "entity" in a URL has no relationship to the "Entity API" term. Don't infer API boundaries from URL paths.
- This document covers the **`/api/entity/` endpoint family** of the REST API. The [Inventory REST API](11-Inventory-REST-API.md) (`/api/inventory/parts`) is **part of the same REST API**, not a separate API — the two docs are split for readability only.
- Epicor briefly subdivided the REST API into "V1 API" / "V2 API" — short-lived naming you may still hear; it has **no relation** to `/v2/` segments in eCommerce SOAP URLs.

**Corroborated by the in-middleware SDK reference** (`/docs/p21sdk` on a 2026.1 tenant), which is Epicor's own first-party catalog and lists exactly **four** APIs — no more:

| SDK name | Epicor's description |
|----------|----------------------|
| **Transaction API** | *"...previously known as the v2 API — a stateless REST API that works with most of our system using a metadata model."* |
| **Entity API** | *"...a very specific set of stateless, fit for purpose REST endpoints using strongly typed business object models."* |
| **Interactive API** | *"...allowing developers to interact with a stateful Prophet 21 session."* |
| **Data Services API** | *"...secure reads from your Prophet 21 database using OData protocol."* |

Two things worth noting: Epicor confirms in its own words that the **Transaction API is the artist formerly known as the "v2 API"**, and the SDK's four-way split is by *capability*, not by URL prefix — reinforcing that URL segments don't define API boundaries. The UDT Service and its 2026.1 [Bulk Data API](13-UDT-Service-API.md#bulk-data-api-20261) appear in **none** of the four, despite being documented, supported endpoints — so the SDK catalog is not exhaustive either.

*Credit: Felipe Maurer ([P21WWUG profile](https://forums.p21ww.org/UserInfo10045.aspx)) — taxonomy correction and 25.1 middleware evidence in [this forum topic](https://forums.p21ww.org/Topic245514-3.aspx); endpoint behavior re-verified live July 2026, SDK catalog cross-checked on 2026.1.*

---

## Overview

This document covers the **stateless REST** endpoints at `/api/entity/` for CRUD (Create, Read, Update, Delete) operations on P21 business objects. They use domain object models and support **four entities**: Customer, Vendor, Contact, and Address.

The same REST API also provides `/api/inventory/parts` — see [Inventory REST API](11-Inventory-REST-API.md) — and an `/api/sales/orders` endpoint family (see [Other REST Endpoint Families](#other-rest-endpoint-families) below).

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

- **Only 4 entities** at `/api/entity/` - Orders live at `/api/sales/orders` (see [Other REST Endpoint Families](#other-rest-endpoint-families)); no invoices, POs, or other business objects found
- **Inventory documented separately** - Lives at `/api/inventory/parts`, part of the same REST API (see [Inventory REST API](11-Inventory-REST-API.md))
- **Limited coverage** - For broad data access, use OData (read) or Transaction API (write)

---

## Base URL

```http
https://{hostname}/api/entity/{resource}
```

Examples:
- `https://play.p21server.com/api/entity/customers`
- `https://play.p21server.com/api/entity/vendors`
- `https://play.p21server.com/api/entity/contacts`
- `https://play.p21server.com/api/entity/addresses`

> **Warning:** Customer/vendor/contact/address records are served **only** from `/api/entity/` — category-style URLs for those records (e.g., `/api/sales/customers`) return 404. But do **not** generalize that to "category URLs don't work": `/api/sales/orders` **exists and responds** (verified July 2026 — see [Other REST Endpoint Families](#other-rest-endpoint-families)), and `/api/inventory/parts` is fully functional ([Inventory REST API](11-Inventory-REST-API.md)). All of these are endpoint families of the same REST API.

---

## Available Entities

Only four entities are available via the Entity API:

| Entity | Endpoint | Key Format | Fields |
|--------|----------|------------|--------|
| **Customers** | `/api/entity/customers` | `{CompanyId}_{CustomerId}` | 102 |
| **Vendors** | `/api/entity/vendors` | `{CompanyId}_{VendorId}` | 50 |
| **Contacts** | `/api/entity/contacts` | `{Id}` (simple numeric) | 40 |
| **Addresses** | `/api/entity/addresses` | `{AddressId}` (simple numeric) | 27 |

Additionally, the same REST API provides inventory items at `/api/inventory/parts` (**[Inventory REST API](11-Inventory-REST-API.md)**) and sales orders at `/api/sales/orders` ([below](#other-rest-endpoint-families)).

### Composite Keys

Customers and Vendors require a **composite key** combining `CompanyId` and the entity ID, separated by an underscore:

```http
/api/entity/customers/ACME_10          # CompanyId=ACME, CustomerId=10
/api/entity/vendors/ACME_28485        # CompanyId=ACME, VendorId=28485
```

- `CompanyId` is a **string** (e.g., `"ACME"`), not numeric
- Using just the numeric ID (e.g., `/customers/10`) returns 404
- The underscore can be URL-encoded (`%5F`) if needed

Contacts and Addresses use **simple numeric IDs**:

```http
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

<!-- tabs -->

**Python:**
```python
client = httpx.Client(follow_redirects=True, verify=VERIFY_SSL, timeout=120)
```

**C#:**
```csharp
var handler = new HttpClientHandler { AllowAutoRedirect = true };
var client = new HttpClient(handler);
```

<!-- /tabs -->

> Full runnable version: [Query Customers](#query-customers) — its client is built with `follow_redirects=True` / `AllowAutoRedirect = true` and calls a list endpoint.

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

See [Authentication](00-Authentication.md) for token generation. Per the SDK, **user-credential tokens** expire after **24 hours**; consumer-key tokens last far longer (years).

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
    "SalesrepId": "200",
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
    "SalesrepId": "200",
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

To update an existing address, use the Interactive API (Address Maintenance window) or direct SQL. See [Error Handling - Entity API](06-Error-Handling.md#entity-api-errors) for the specific error codes these limitations produce.

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

```http
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

```http
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
```http
GET /api/entity/customers/ACME_10?extendedproperties=*
```

**Specific nested object:**
```http
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

**Inventory:** see the [Inventory REST API extended properties reference](11-Inventory-REST-API.md#extended-properties-reference) for the full list for `/api/inventory/parts`.

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
    "SalesrepId": "200",
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

## Code Examples

### Setup

Every example below is a complete, standalone program — paste it into a file, edit the
`EDIT THESE` constants, run it. Entity API calls go straight to `BASE_URL`; there is no
UI-server redirect to resolve (that only applies to Transaction and Interactive).

<!-- tabs -->

**Python:**
```python
"""Authenticate against P21 and build a client for Entity API calls."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
# ---------------------------------------------------------------------------


def get_token(client: httpx.Client) -> str:
    """v2 token endpoint — credentials go in the body, never in headers."""
    r = client.post(
        f"{BASE_URL}/api/security/token/v2",
        json={"username": USERNAME, "password": PASSWORD},
        headers={"Accept": "application/json"},
    )
    r.raise_for_status()
    try:
        return r.json()["AccessToken"]
    except (ValueError, KeyError):  # some middleware answers in XML
        match = re.search(r"<AccessToken>([^<]+)</AccessToken>", r.text)
        if not match:
            raise ValueError(f"No AccessToken in response: {r.text[:200]}") from None
        return match.group(1)


with httpx.Client(verify=VERIFY_SSL, timeout=120, follow_redirects=True) as client:
    token = get_token(client)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",       # without this you get XML, not JSON
        "Content-Type": "application/json",
    }

    # Every other example on this page repeats this same setup block, then adds
    # its own call to /api/entity/... using `client` and `headers`.
    print("Authenticated — token acquired.")
```

**C#:**
```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
// ---------------------------------------------------------------------------

var handler = new HttpClientHandler
{
    // Test tenants often present a self-signed cert. Delete this line in production.
    ServerCertificateCustomValidationCallback =
        HttpClientHandler.DangerousAcceptAnyServerCertificateValidator,
    AllowAutoRedirect = true,                           // list endpoints 307 without a slash
};
using var client = new HttpClient(handler) { Timeout = TimeSpan.FromMinutes(2) };
client.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));

var token = await GetTokenAsync(client);
client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);

// Every other example on this page repeats this same setup block, then adds
// its own call to /api/entity/... using `client`.
Console.WriteLine("Authenticated — token acquired.");

// --- helpers ---------------------------------------------------------------

// v2 token endpoint — credentials go in the body, never in headers.
static async Task<string> GetTokenAsync(HttpClient client)
{
    var payload = JsonSerializer.Serialize(new { username = Username, password = Password });
    var response = await client.PostAsync(
        $"{BaseUrl}/api/security/token/v2",
        new StringContent(payload, Encoding.UTF8, "application/json"));
    response.EnsureSuccessStatusCode();
    return ReadField(await response.Content.ReadAsStringAsync(), "AccessToken");
}

// Some middleware answers this endpoint in XML even when asked for JSON.
static string ReadField(string payload, string field)
{
    try
    {
        var value = JsonDocument.Parse(payload).RootElement.GetProperty(field).GetString();
        if (!string.IsNullOrEmpty(value)) return value;
    }
    catch (Exception ex) when (ex is JsonException or KeyNotFoundException) { }

    var match = System.Text.RegularExpressions.Regex.Match(payload, $"<{field}>([^<]+)</{field}>");
    if (!match.Success)
        throw new InvalidOperationException(
            $"No {field} in response: {payload[..Math.Min(200, payload.Length)]}");
    return match.Groups[1].Value;
}
```

<!-- /tabs -->

### Health Check

<!-- tabs -->

**Python:**
```python
"""Ping the customers entity to confirm the Entity API is reachable."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
# ---------------------------------------------------------------------------


def get_token(client: httpx.Client) -> str:
    """v2 token endpoint — credentials go in the body, never in headers."""
    r = client.post(
        f"{BASE_URL}/api/security/token/v2",
        json={"username": USERNAME, "password": PASSWORD},
        headers={"Accept": "application/json"},
    )
    r.raise_for_status()
    try:
        return r.json()["AccessToken"]
    except (ValueError, KeyError):  # some middleware answers in XML
        match = re.search(r"<AccessToken>([^<]+)</AccessToken>", r.text)
        if not match:
            raise ValueError(f"No AccessToken in response: {r.text[:200]}") from None
        return match.group(1)


with httpx.Client(verify=VERIFY_SSL, timeout=120, follow_redirects=True) as client:
    token = get_token(client)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",       # without this you get XML, not JSON
        "Content-Type": "application/json",
    }

    resp = client.get(f"{BASE_URL}/api/entity/customers/ping", headers=headers)
    resp.raise_for_status()
    print(resp.json())  # {"ResponseMessage": "success"}
```

**C#:**
```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
// ---------------------------------------------------------------------------

var handler = new HttpClientHandler
{
    // Test tenants often present a self-signed cert. Delete this line in production.
    ServerCertificateCustomValidationCallback =
        HttpClientHandler.DangerousAcceptAnyServerCertificateValidator,
    AllowAutoRedirect = true,
};
using var client = new HttpClient(handler) { Timeout = TimeSpan.FromMinutes(2) };
client.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));

var token = await GetTokenAsync(client);
client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);

var resp = await client.GetAsync($"{BaseUrl}/api/entity/customers/ping");
resp.EnsureSuccessStatusCode();
Console.WriteLine(await resp.Content.ReadAsStringAsync());  // {"ResponseMessage": "success"}

// --- helpers ---------------------------------------------------------------

// v2 token endpoint — credentials go in the body, never in headers.
static async Task<string> GetTokenAsync(HttpClient client)
{
    var payload = JsonSerializer.Serialize(new { username = Username, password = Password });
    var response = await client.PostAsync(
        $"{BaseUrl}/api/security/token/v2",
        new StringContent(payload, Encoding.UTF8, "application/json"));
    response.EnsureSuccessStatusCode();
    return ReadField(await response.Content.ReadAsStringAsync(), "AccessToken");
}

// Some middleware answers this endpoint in XML even when asked for JSON.
static string ReadField(string payload, string field)
{
    try
    {
        var value = JsonDocument.Parse(payload).RootElement.GetProperty(field).GetString();
        if (!string.IsNullOrEmpty(value)) return value;
    }
    catch (Exception ex) when (ex is JsonException or KeyNotFoundException) { }

    var match = System.Text.RegularExpressions.Regex.Match(payload, $"<{field}>([^<]+)</{field}>");
    if (!match.Success)
        throw new InvalidOperationException(
            $"No {field} in response: {payload[..Math.Min(200, payload.Length)]}");
    return match.Groups[1].Value;
}
```

<!-- /tabs -->

### Get Single Customer

<!-- tabs -->

**Python:**
```python
"""Fetch a single customer by its composite key."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
CUSTOMER_KEY = "ACME_10"                  # {CompanyId}_{CustomerId}
# ---------------------------------------------------------------------------


def get_token(client: httpx.Client) -> str:
    """v2 token endpoint — credentials go in the body, never in headers."""
    r = client.post(
        f"{BASE_URL}/api/security/token/v2",
        json={"username": USERNAME, "password": PASSWORD},
        headers={"Accept": "application/json"},
    )
    r.raise_for_status()
    try:
        return r.json()["AccessToken"]
    except (ValueError, KeyError):  # some middleware answers in XML
        match = re.search(r"<AccessToken>([^<]+)</AccessToken>", r.text)
        if not match:
            raise ValueError(f"No AccessToken in response: {r.text[:200]}") from None
        return match.group(1)


with httpx.Client(verify=VERIFY_SSL, timeout=120, follow_redirects=True) as client:
    token = get_token(client)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",       # without this you get XML, not JSON
        "Content-Type": "application/json",
    }

    resp = client.get(f"{BASE_URL}/api/entity/customers/{CUSTOMER_KEY}", headers=headers)
    resp.raise_for_status()
    customer = resp.json()
    print(f"{customer['CustomerId']}: {customer['CustomerName']}")
    # 10: ABC Supply Company
```

**C#:**
```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string CustomerKey = "ACME_10";                   // {CompanyId}_{CustomerId}
// ---------------------------------------------------------------------------

var handler = new HttpClientHandler
{
    // Test tenants often present a self-signed cert. Delete this line in production.
    ServerCertificateCustomValidationCallback =
        HttpClientHandler.DangerousAcceptAnyServerCertificateValidator,
    AllowAutoRedirect = true,
};
using var client = new HttpClient(handler) { Timeout = TimeSpan.FromMinutes(2) };
client.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));

var token = await GetTokenAsync(client);
client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);

var resp = await client.GetAsync($"{BaseUrl}/api/entity/customers/{CustomerKey}");
resp.EnsureSuccessStatusCode();
using var customer = JsonDocument.Parse(await resp.Content.ReadAsStringAsync());
var root = customer.RootElement;
Console.WriteLine($"{root.GetProperty("CustomerId")}: {root.GetProperty("CustomerName")}");
// 10: ABC Supply Company

// --- helpers ---------------------------------------------------------------

// v2 token endpoint — credentials go in the body, never in headers.
static async Task<string> GetTokenAsync(HttpClient client)
{
    var payload = JsonSerializer.Serialize(new { username = Username, password = Password });
    var response = await client.PostAsync(
        $"{BaseUrl}/api/security/token/v2",
        new StringContent(payload, Encoding.UTF8, "application/json"));
    response.EnsureSuccessStatusCode();
    return ReadField(await response.Content.ReadAsStringAsync(), "AccessToken");
}

// Some middleware answers this endpoint in XML even when asked for JSON.
static string ReadField(string payload, string field)
{
    try
    {
        var value = JsonDocument.Parse(payload).RootElement.GetProperty(field).GetString();
        if (!string.IsNullOrEmpty(value)) return value;
    }
    catch (Exception ex) when (ex is JsonException or KeyNotFoundException) { }

    var match = System.Text.RegularExpressions.Regex.Match(payload, $"<{field}>([^<]+)</{field}>");
    if (!match.Success)
        throw new InvalidOperationException(
            $"No {field} in response: {payload[..Math.Min(200, payload.Length)]}");
    return match.Groups[1].Value;
}
```

<!-- /tabs -->

### Get Customer with Extended Properties

<!-- tabs -->

**Python:**
```python
"""Fetch a customer with its nested CustomerAddress populated."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
CUSTOMER_KEY = "ACME_10"                  # {CompanyId}_{CustomerId}
# ---------------------------------------------------------------------------


def get_token(client: httpx.Client) -> str:
    """v2 token endpoint — credentials go in the body, never in headers."""
    r = client.post(
        f"{BASE_URL}/api/security/token/v2",
        json={"username": USERNAME, "password": PASSWORD},
        headers={"Accept": "application/json"},
    )
    r.raise_for_status()
    try:
        return r.json()["AccessToken"]
    except (ValueError, KeyError):  # some middleware answers in XML
        match = re.search(r"<AccessToken>([^<]+)</AccessToken>", r.text)
        if not match:
            raise ValueError(f"No AccessToken in response: {r.text[:200]}") from None
        return match.group(1)


with httpx.Client(verify=VERIFY_SSL, timeout=120, follow_redirects=True) as client:
    token = get_token(client)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",       # without this you get XML, not JSON
        "Content-Type": "application/json",
    }

    resp = client.get(
        f"{BASE_URL}/api/entity/customers/{CUSTOMER_KEY}",
        headers=headers,
        params={"extendedproperties": "CustomerAddress"},
    )
    resp.raise_for_status()
    customer = resp.json()
    addr = customer["CustomerAddress"]
    print(f"{addr['MailCity']}, {addr['MailState']} {addr['MailPostalCode']}")
    # Springfield, IL 62701
```

**C#:**
```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string CustomerKey = "ACME_10";                   // {CompanyId}_{CustomerId}
// ---------------------------------------------------------------------------

var handler = new HttpClientHandler
{
    // Test tenants often present a self-signed cert. Delete this line in production.
    ServerCertificateCustomValidationCallback =
        HttpClientHandler.DangerousAcceptAnyServerCertificateValidator,
    AllowAutoRedirect = true,
};
using var client = new HttpClient(handler) { Timeout = TimeSpan.FromMinutes(2) };
client.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));

var token = await GetTokenAsync(client);
client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);

var resp = await client.GetAsync(
    $"{BaseUrl}/api/entity/customers/{CustomerKey}?extendedproperties=CustomerAddress");
resp.EnsureSuccessStatusCode();
using var customer = JsonDocument.Parse(await resp.Content.ReadAsStringAsync());
var addr = customer.RootElement.GetProperty("CustomerAddress");
Console.WriteLine(
    $"{addr.GetProperty("MailCity")}, {addr.GetProperty("MailState")} {addr.GetProperty("MailPostalCode")}");
// Springfield, IL 62701

// --- helpers ---------------------------------------------------------------

// v2 token endpoint — credentials go in the body, never in headers.
static async Task<string> GetTokenAsync(HttpClient client)
{
    var payload = JsonSerializer.Serialize(new { username = Username, password = Password });
    var response = await client.PostAsync(
        $"{BaseUrl}/api/security/token/v2",
        new StringContent(payload, Encoding.UTF8, "application/json"));
    response.EnsureSuccessStatusCode();
    return ReadField(await response.Content.ReadAsStringAsync(), "AccessToken");
}

// Some middleware answers this endpoint in XML even when asked for JSON.
static string ReadField(string payload, string field)
{
    try
    {
        var value = JsonDocument.Parse(payload).RootElement.GetProperty(field).GetString();
        if (!string.IsNullOrEmpty(value)) return value;
    }
    catch (Exception ex) when (ex is JsonException or KeyNotFoundException) { }

    var match = System.Text.RegularExpressions.Regex.Match(payload, $"<{field}>([^<]+)</{field}>");
    if (!match.Success)
        throw new InvalidOperationException(
            $"No {field} in response: {payload[..Math.Min(200, payload.Length)]}");
    return match.Groups[1].Value;
}
```

<!-- /tabs -->

### Query Customers

<!-- tabs -->

**Python:**
```python
"""List endpoint with a $query filter -- note the trailing slash and follow_redirects."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
NAME_PREFIX = "ABC"                       # customers whose name starts with this
# ---------------------------------------------------------------------------


def get_token(client: httpx.Client) -> str:
    """v2 token endpoint — credentials go in the body, never in headers."""
    r = client.post(
        f"{BASE_URL}/api/security/token/v2",
        json={"username": USERNAME, "password": PASSWORD},
        headers={"Accept": "application/json"},
    )
    r.raise_for_status()
    try:
        return r.json()["AccessToken"]
    except (ValueError, KeyError):  # some middleware answers in XML
        match = re.search(r"<AccessToken>([^<]+)</AccessToken>", r.text)
        if not match:
            raise ValueError(f"No AccessToken in response: {r.text[:200]}") from None
        return match.group(1)


with httpx.Client(verify=VERIFY_SSL, timeout=120, follow_redirects=True) as client:
    token = get_token(client)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",       # without this you get XML, not JSON
        "Content-Type": "application/json",
    }

    resp = client.get(
        f"{BASE_URL}/api/entity/customers/",
        headers=headers,
        params={"$query": f"startswith(CustomerName, '{NAME_PREFIX}')"},
    )
    resp.raise_for_status()
    customers = resp.json()
    print(f"Found {len(customers)} customers")
    for c in customers:
        print(f"  {c['CompanyId']}_{c['CustomerId']}: {c['CustomerName']}")
```

**C#:**
```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string NamePrefix = "ABC";                        // customers whose name starts with this
// ---------------------------------------------------------------------------

var handler = new HttpClientHandler
{
    // Test tenants often present a self-signed cert. Delete this line in production.
    ServerCertificateCustomValidationCallback =
        HttpClientHandler.DangerousAcceptAnyServerCertificateValidator,
    AllowAutoRedirect = true,                           // list endpoints 307 without a slash
};
using var client = new HttpClient(handler) { Timeout = TimeSpan.FromMinutes(2) };
client.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));

var token = await GetTokenAsync(client);
client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);

var resp = await client.GetAsync(
    $"{BaseUrl}/api/entity/customers/?$query=startswith(CustomerName, '{NamePrefix}')");
resp.EnsureSuccessStatusCode();
using var customers = JsonDocument.Parse(await resp.Content.ReadAsStringAsync());
var rows = customers.RootElement;
Console.WriteLine($"Found {rows.GetArrayLength()} customers");
foreach (var c in rows.EnumerateArray())
{
    Console.WriteLine($"  {c.GetProperty("CompanyId")}_{c.GetProperty("CustomerId")}: {c.GetProperty("CustomerName")}");
}

// --- helpers ---------------------------------------------------------------

// v2 token endpoint — credentials go in the body, never in headers.
static async Task<string> GetTokenAsync(HttpClient client)
{
    var payload = JsonSerializer.Serialize(new { username = Username, password = Password });
    var response = await client.PostAsync(
        $"{BaseUrl}/api/security/token/v2",
        new StringContent(payload, Encoding.UTF8, "application/json"));
    response.EnsureSuccessStatusCode();
    return ReadField(await response.Content.ReadAsStringAsync(), "AccessToken");
}

// Some middleware answers this endpoint in XML even when asked for JSON.
static string ReadField(string payload, string field)
{
    try
    {
        var value = JsonDocument.Parse(payload).RootElement.GetProperty(field).GetString();
        if (!string.IsNullOrEmpty(value)) return value;
    }
    catch (Exception ex) when (ex is JsonException or KeyNotFoundException) { }

    var match = System.Text.RegularExpressions.Regex.Match(payload, $"<{field}>([^<]+)</{field}>");
    if (!match.Success)
        throw new InvalidOperationException(
            $"No {field} in response: {payload[..Math.Min(200, payload.Length)]}");
    return match.Groups[1].Value;
}
```

<!-- /tabs -->

### Get Contact

<!-- tabs -->

**Python:**
```python
"""Fetch a single contact by its simple numeric ID."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
CONTACT_ID = "1"
# ---------------------------------------------------------------------------


def get_token(client: httpx.Client) -> str:
    """v2 token endpoint — credentials go in the body, never in headers."""
    r = client.post(
        f"{BASE_URL}/api/security/token/v2",
        json={"username": USERNAME, "password": PASSWORD},
        headers={"Accept": "application/json"},
    )
    r.raise_for_status()
    try:
        return r.json()["AccessToken"]
    except (ValueError, KeyError):  # some middleware answers in XML
        match = re.search(r"<AccessToken>([^<]+)</AccessToken>", r.text)
        if not match:
            raise ValueError(f"No AccessToken in response: {r.text[:200]}") from None
        return match.group(1)


with httpx.Client(verify=VERIFY_SSL, timeout=120, follow_redirects=True) as client:
    token = get_token(client)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",       # without this you get XML, not JSON
        "Content-Type": "application/json",
    }

    resp = client.get(f"{BASE_URL}/api/entity/contacts/{CONTACT_ID}", headers=headers)
    resp.raise_for_status()
    contact = resp.json()
    print(f"{contact['FirstName']} {contact['LastName']}")
    # John Smith
```

**C#:**
```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string ContactId = "1";
// ---------------------------------------------------------------------------

var handler = new HttpClientHandler
{
    // Test tenants often present a self-signed cert. Delete this line in production.
    ServerCertificateCustomValidationCallback =
        HttpClientHandler.DangerousAcceptAnyServerCertificateValidator,
    AllowAutoRedirect = true,
};
using var client = new HttpClient(handler) { Timeout = TimeSpan.FromMinutes(2) };
client.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));

var token = await GetTokenAsync(client);
client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);

var resp = await client.GetAsync($"{BaseUrl}/api/entity/contacts/{ContactId}");
resp.EnsureSuccessStatusCode();
using var contact = JsonDocument.Parse(await resp.Content.ReadAsStringAsync());
var root = contact.RootElement;
Console.WriteLine($"{root.GetProperty("FirstName")} {root.GetProperty("LastName")}");
// John Smith

// --- helpers ---------------------------------------------------------------

// v2 token endpoint — credentials go in the body, never in headers.
static async Task<string> GetTokenAsync(HttpClient client)
{
    var payload = JsonSerializer.Serialize(new { username = Username, password = Password });
    var response = await client.PostAsync(
        $"{BaseUrl}/api/security/token/v2",
        new StringContent(payload, Encoding.UTF8, "application/json"));
    response.EnsureSuccessStatusCode();
    return ReadField(await response.Content.ReadAsStringAsync(), "AccessToken");
}

// Some middleware answers this endpoint in XML even when asked for JSON.
static string ReadField(string payload, string field)
{
    try
    {
        var value = JsonDocument.Parse(payload).RootElement.GetProperty(field).GetString();
        if (!string.IsNullOrEmpty(value)) return value;
    }
    catch (Exception ex) when (ex is JsonException or KeyNotFoundException) { }

    var match = System.Text.RegularExpressions.Regex.Match(payload, $"<{field}>([^<]+)</{field}>");
    if (!match.Success)
        throw new InvalidOperationException(
            $"No {field} in response: {payload[..Math.Min(200, payload.Length)]}");
    return match.Groups[1].Value;
}
```

<!-- /tabs -->

### Create Customer

<!-- tabs -->

**Python:**
```python
"""Create a customer from the /new template, then read it back to confirm."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
COMPANY_ID = "ACME"
CUSTOMER_NAME = "New Customer Inc."
SALESREP_ID = "200"
TERMS_ID = "1"
# ---------------------------------------------------------------------------


def get_token(client: httpx.Client) -> str:
    """v2 token endpoint — credentials go in the body, never in headers."""
    r = client.post(
        f"{BASE_URL}/api/security/token/v2",
        json={"username": USERNAME, "password": PASSWORD},
        headers={"Accept": "application/json"},
    )
    r.raise_for_status()
    try:
        return r.json()["AccessToken"]
    except (ValueError, KeyError):  # some middleware answers in XML
        match = re.search(r"<AccessToken>([^<]+)</AccessToken>", r.text)
        if not match:
            raise ValueError(f"No AccessToken in response: {r.text[:200]}") from None
        return match.group(1)


with httpx.Client(verify=VERIFY_SSL, timeout=120, follow_redirects=True) as client:
    token = get_token(client)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",       # without this you get XML, not JSON
        "Content-Type": "application/json",
    }

    # Get template first
    resp = client.get(f"{BASE_URL}/api/entity/customers/new", headers=headers)
    resp.raise_for_status()
    template = resp.json()

    # Fill required fields
    template["CompanyId"] = COMPANY_ID
    template["CustomerName"] = CUSTOMER_NAME
    template["SalesrepId"] = SALESREP_ID
    template["TermsId"] = TERMS_ID

    # Create (POST without CustomerId = insert)
    resp = client.post(f"{BASE_URL}/api/entity/customers", headers=headers, json=template)
    resp.raise_for_status()

    # Read back -- HTTP 200 on the POST doesn't confirm what landed or the generated ID.
    resp = client.get(
        f"{BASE_URL}/api/entity/customers/",
        headers=headers,
        params={"$query": f"CompanyId eq '{COMPANY_ID}' and CustomerName eq '{CUSTOMER_NAME}'"},
    )
    resp.raise_for_status()
    created = resp.json()
    print(f"Found {len(created)} matching customer(s) after create:")
    for c in created:
        print(f"  {c['CompanyId']}_{c['CustomerId']}: {c['CustomerName']}")
```

**C#:**
```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string CompanyId = "ACME";
const string CustomerName = "New Customer Inc.";
const string SalesrepId = "200";
const string TermsId = "1";
// ---------------------------------------------------------------------------

var handler = new HttpClientHandler
{
    // Test tenants often present a self-signed cert. Delete this line in production.
    ServerCertificateCustomValidationCallback =
        HttpClientHandler.DangerousAcceptAnyServerCertificateValidator,
    AllowAutoRedirect = true,                           // list endpoints 307 without a slash
};
using var client = new HttpClient(handler) { Timeout = TimeSpan.FromMinutes(2) };
client.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));

var token = await GetTokenAsync(client);
client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);

// Get template first
var resp = await client.GetAsync($"{BaseUrl}/api/entity/customers/new");
resp.EnsureSuccessStatusCode();
using var templateDoc = JsonDocument.Parse(await resp.Content.ReadAsStringAsync());

// Fill required fields (System.Text.Json documents are read-only, so build a fresh object)
var template = new Dictionary<string, object?>();
foreach (var property in templateDoc.RootElement.EnumerateObject())
    template[property.Name] = property.Value;
template["CompanyId"] = CompanyId;
template["CustomerName"] = CustomerName;
template["SalesrepId"] = SalesrepId;
template["TermsId"] = TermsId;

// Create (POST without CustomerId = insert)
resp = await client.PostAsync(
    $"{BaseUrl}/api/entity/customers",
    new StringContent(JsonSerializer.Serialize(template), Encoding.UTF8, "application/json"));
resp.EnsureSuccessStatusCode();

// Read back -- HTTP 200 on the POST doesn't confirm what landed or the generated ID.
resp = await client.GetAsync(
    $"{BaseUrl}/api/entity/customers/?$query=CompanyId eq '{CompanyId}' and CustomerName eq '{CustomerName}'");
resp.EnsureSuccessStatusCode();
using var created = JsonDocument.Parse(await resp.Content.ReadAsStringAsync());
var rows = created.RootElement;
Console.WriteLine($"Found {rows.GetArrayLength()} matching customer(s) after create:");
foreach (var c in rows.EnumerateArray())
{
    Console.WriteLine($"  {c.GetProperty("CompanyId")}_{c.GetProperty("CustomerId")}: {c.GetProperty("CustomerName")}");
}

// --- helpers ---------------------------------------------------------------

// v2 token endpoint — credentials go in the body, never in headers.
static async Task<string> GetTokenAsync(HttpClient client)
{
    var payload = JsonSerializer.Serialize(new { username = Username, password = Password });
    var response = await client.PostAsync(
        $"{BaseUrl}/api/security/token/v2",
        new StringContent(payload, Encoding.UTF8, "application/json"));
    response.EnsureSuccessStatusCode();
    return ReadField(await response.Content.ReadAsStringAsync(), "AccessToken");
}

// Some middleware answers this endpoint in XML even when asked for JSON.
static string ReadField(string payload, string field)
{
    try
    {
        var value = JsonDocument.Parse(payload).RootElement.GetProperty(field).GetString();
        if (!string.IsNullOrEmpty(value)) return value;
    }
    catch (Exception ex) when (ex is JsonException or KeyNotFoundException) { }

    var match = System.Text.RegularExpressions.Regex.Match(payload, $"<{field}>([^<]+)</{field}>");
    if (!match.Success)
        throw new InvalidOperationException(
            $"No {field} in response: {payload[..Math.Min(200, payload.Length)]}");
    return match.Groups[1].Value;
}
```

<!-- /tabs -->

### Update Customer

<!-- tabs -->

**Python:**
```python
"""Update a customer's name, then read it back to confirm what landed."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
COMPANY_ID = "ACME"
CUSTOMER_ID = 10
NEW_NAME = "Updated Customer Name"
# ---------------------------------------------------------------------------


def get_token(client: httpx.Client) -> str:
    """v2 token endpoint — credentials go in the body, never in headers."""
    r = client.post(
        f"{BASE_URL}/api/security/token/v2",
        json={"username": USERNAME, "password": PASSWORD},
        headers={"Accept": "application/json"},
    )
    r.raise_for_status()
    try:
        return r.json()["AccessToken"]
    except (ValueError, KeyError):  # some middleware answers in XML
        match = re.search(r"<AccessToken>([^<]+)</AccessToken>", r.text)
        if not match:
            raise ValueError(f"No AccessToken in response: {r.text[:200]}") from None
        return match.group(1)


with httpx.Client(verify=VERIFY_SSL, timeout=120, follow_redirects=True) as client:
    token = get_token(client)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",       # without this you get XML, not JSON
        "Content-Type": "application/json",
    }

    customer_key = f"{COMPANY_ID}_{CUSTOMER_ID}"
    resp = client.put(
        f"{BASE_URL}/api/entity/customers/{customer_key}",
        headers=headers,
        json={
            "CompanyId": COMPANY_ID,
            "CustomerId": CUSTOMER_ID,
            "CustomerName": NEW_NAME,
        },
    )
    resp.raise_for_status()

    # Read back -- HTTP 200 on the PUT doesn't confirm what landed.
    resp = client.get(f"{BASE_URL}/api/entity/customers/{customer_key}", headers=headers)
    resp.raise_for_status()
    customer = resp.json()
    print(f"{customer['CustomerId']}: {customer['CustomerName']}")
```

**C#:**
```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string CompanyId = "ACME";
const int CustomerId = 10;
const string NewName = "Updated Customer Name";
// ---------------------------------------------------------------------------

var handler = new HttpClientHandler
{
    // Test tenants often present a self-signed cert. Delete this line in production.
    ServerCertificateCustomValidationCallback =
        HttpClientHandler.DangerousAcceptAnyServerCertificateValidator,
    AllowAutoRedirect = true,
};
using var client = new HttpClient(handler) { Timeout = TimeSpan.FromMinutes(2) };
client.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));

var token = await GetTokenAsync(client);
client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);

var customerKey = $"{CompanyId}_{CustomerId}";
var payload = JsonSerializer.Serialize(new
{
    CompanyId = CompanyId,
    CustomerId = CustomerId,
    CustomerName = NewName,
});
var resp = await client.PutAsync(
    $"{BaseUrl}/api/entity/customers/{customerKey}",
    new StringContent(payload, Encoding.UTF8, "application/json"));
resp.EnsureSuccessStatusCode();

// Read back -- HTTP 200 on the PUT doesn't confirm what landed.
resp = await client.GetAsync($"{BaseUrl}/api/entity/customers/{customerKey}");
resp.EnsureSuccessStatusCode();
using var customer = JsonDocument.Parse(await resp.Content.ReadAsStringAsync());
var root = customer.RootElement;
Console.WriteLine($"{root.GetProperty("CustomerId")}: {root.GetProperty("CustomerName")}");

// --- helpers ---------------------------------------------------------------

// v2 token endpoint — credentials go in the body, never in headers.
static async Task<string> GetTokenAsync(HttpClient client)
{
    var payload = JsonSerializer.Serialize(new { username = Username, password = Password });
    var response = await client.PostAsync(
        $"{BaseUrl}/api/security/token/v2",
        new StringContent(payload, Encoding.UTF8, "application/json"));
    response.EnsureSuccessStatusCode();
    return ReadField(await response.Content.ReadAsStringAsync(), "AccessToken");
}

// Some middleware answers this endpoint in XML even when asked for JSON.
static string ReadField(string payload, string field)
{
    try
    {
        var value = JsonDocument.Parse(payload).RootElement.GetProperty(field).GetString();
        if (!string.IsNullOrEmpty(value)) return value;
    }
    catch (Exception ex) when (ex is JsonException or KeyNotFoundException) { }

    var match = System.Text.RegularExpressions.Regex.Match(payload, $"<{field}>([^<]+)</{field}>");
    if (!match.Success)
        throw new InvalidOperationException(
            $"No {field} in response: {payload[..Math.Min(200, payload.Length)]}");
    return match.Groups[1].Value;
}
```

<!-- /tabs -->

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

```http
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

## Other REST Endpoint Families

The REST API exposes more than `/api/entity/` and `/api/inventory/parts`. Verified against a 25.2 tenant (July 2026):

### `/api/sales/orders` — exists and responds

| Call | Result |
|------|--------|
| `GET /api/sales/orders/ping` | 200 |
| `GET /api/sales/orders/new` | 200 — full order template (Lines, Notes, Salesreps, BuilderSelectionSheets, Samples, …) |
| `GET /api/sales/orders/{order_no}` | 200 — ~70 top-level fields |
| `GET /api/sales/orders/{order_no}/approve` | 405 — route exists; the middleware documents PUT for this action (PUT untested) |
| `GET /api/sales/orders/?$query=...` | 500 with an unrecognized field name — list query syntax not yet discovered |
| `POST /api/sales/orders/` | Creates an order — **trailing slash required**, lines nest under `Lines.list`. See [Creating an Order](#creating-an-order-post-apisalesorders) (community-verified on 25.2) |

The approve action and every other write on this family remain **untested**; order creation is the one write with a reported working payload, below.

### Creating an Order (`POST /api/sales/orders/`)

`/api/sales/orders/` is not read-only: the same URL accepts a **POST** whose body is a single order — header fields at the top level, lines nested inside. `GET /api/sales/orders/new` shows you the object's shape but says nothing about how to submit one, which is why this went undocumented for so long.

> **Contributed and tested on P21 25.2 by [Rob Landham](https://github.com/roblandham) ([issue #108](https://github.com/mrwuss/p21-api-documentation/issues/108))** — the payload shape and both rules below are their findings, reproduced here as reported. They have **not** been re-verified on this repo's tenant, and the [open questions](#what-is-not-pinned-down-yet) at the end of this section list exactly what nobody has pinned down yet. Treat the field list as an example header, not a required-field spec: which fields your environment demands depends on its configuration.

Two shape rules decide whether the call works at all.

**1. The trailing slash is required.** `POST /api/sales/orders/` routes correctly; drop the slash and the request is not routed to the API. This is the write-side face of the [307 on list endpoints](#trailing-slash-on-list-endpoints) — except that on a POST you cannot paper over it with a redirect-following client and call it handled, because whether the body and method survive the hop is up to the client. Send the slash.

**2. `Lines` is an object, not an array.** The lines go in an array under `Lines.list`. A top-level `Lines` array **fails** — this is the mistake the `/new` template does not protect you from, since it shows the container without explaining the nesting.

#### Header fields

| Field | Type | Notes |
|-------|------|-------|
| `CustomerId` | string | P21 customer ID the order is placed against |
| `CompanyId` | string | Company/branch code |
| `LocationId` | string | Fulfilling location ID |
| `Taker` | string | User/service account identifier that "took" the order |
| `PromiseDate` | string (`YYYY-MM-DD`) | Promised ship/delivery date |
| `TermsId` | string | Payment terms code (e.g. `NET30`) |
| `ShipToId` | string | Ship-to record ID |
| `ShipToName`, `ShipToAddress1`, `ShipToAddress2`, `ShipToCity`, `ShipToState`, `ZipCode`, `ShipToCountry` | string | Ship-to address fields — sent inline when `ShipToId` alone doesn't resolve the full address |
| `ShipToEmail`, `ShipToPhone` | string | Ship-to contact details |
| `SourceLocId` | string | Source location for the order |
| `PoNo` | string | Customer PO number reference |
| `Quote` | string (`"Y"`/`"N"`) | Whether this is a quote rather than a firm order |
| `DeletedFlag` | string (`"Y"`/`"N"`) | Soft-delete flag — `"N"` for new orders |
| `Lines` | object | Container wrapping the lines — **not** an array |
| `Lines.list` | array | The line objects |

#### Line fields (`Lines.list[]`)

| Field | Type | Notes |
|-------|------|-------|
| `ItemId` | string | Item being ordered |
| `UnitQuantity` | number | Quantity in `UnitOfMeasure` |
| `UnitOfMeasure` | string | e.g. `EA` |
| `UnitPrice` | number | Price per unit |
| `TaxItem` | string (`"Y"`/`"N"`) | Whether the line is taxable |
| `Delete` | string (`"Y"`/`"N"`) | `"N"` on a new line |

Note the type split: quantities and prices are **JSON numbers** here, while the flags are `"Y"`/`"N"` **strings** — unlike the Transaction API, where every `Value` is a string.

#### Example request body

```json
POST {base_url}/api/sales/orders/

{
    "CustomerId": "100198",
    "CompanyId": "ACME",
    "LocationId": "10",
    "Taker": "JSMITH",
    "PromiseDate": "2030-01-06",
    "TermsId": "NET30",
    "ShipToId": "200",
    "ShipToName": "Acme Fulfillment Co",
    "ShipToAddress1": "123 Example Street",
    "ShipToAddress2": "Ste 100",
    "ShipToCity": "Atlanta",
    "ShipToState": "GA",
    "ZipCode": "30000",
    "ShipToCountry": "US",
    "ShipToEmail": "orders@example.com",
    "ShipToPhone": "000-000-0000",
    "SourceLocId": "10",
    "PoNo": "PO-TEST-001",
    "Quote": "N",
    "DeletedFlag": "N",
    "Lines": {
        "list": [
            {
                "ItemId": "WIDGET-001",
                "UnitQuantity": 1,
                "UnitOfMeasure": "EA",
                "UnitPrice": 0.99,
                "TaxItem": "N",
                "Delete": "N"
            }
        ]
    }
}
```

#### Complete example

The create response shape is unconfirmed (see [below](#what-is-not-pinned-down-yet)), so this program **prints the raw body** before trying to find an order number in it, and reads the order back when it finds one. Run it against a play tenant first — it writes a real order.

<!-- tabs -->

**Python:**
```python
"""Create a sales order through the REST API, then read it back."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
CUSTOMER_ID = "100198"
COMPANY_ID = "ACME"
LOCATION_ID = "10"
TAKER = "JSMITH"
PROMISE_DATE = "2030-01-06"
TERMS_ID = "NET30"
SHIP_TO_ID = "200"
ITEM_ID = "WIDGET-001"
QUANTITY = 1
UNIT_PRICE = 0.99
# ---------------------------------------------------------------------------

ORDER = {
    "CustomerId": CUSTOMER_ID,
    "CompanyId": COMPANY_ID,
    "LocationId": LOCATION_ID,
    "Taker": TAKER,
    "PromiseDate": PROMISE_DATE,
    "TermsId": TERMS_ID,
    "ShipToId": SHIP_TO_ID,
    "SourceLocId": LOCATION_ID,
    "PoNo": "PO-TEST-001",
    "Quote": "N",                          # "Y" makes it a quote, not an order
    "DeletedFlag": "N",
    # Lines is an OBJECT wrapping a list -- a top-level array fails.
    "Lines": {
        "list": [
            {
                "ItemId": ITEM_ID,
                "UnitQuantity": QUANTITY,
                "UnitOfMeasure": "EA",
                "UnitPrice": UNIT_PRICE,
                "TaxItem": "N",
                "Delete": "N",
            }
        ]
    },
}


def get_token(client: httpx.Client) -> str:
    """v2 token endpoint — credentials go in the body, never in headers."""
    r = client.post(
        f"{BASE_URL}/api/security/token/v2",
        json={"username": USERNAME, "password": PASSWORD},
        headers={"Accept": "application/json"},
    )
    r.raise_for_status()
    try:
        return r.json()["AccessToken"]
    except (ValueError, KeyError):  # some middleware answers in XML
        match = re.search(r"<AccessToken>([^<]+)</AccessToken>", r.text)
        if not match:
            raise ValueError(f"No AccessToken in response: {r.text[:200]}") from None
        return match.group(1)


with httpx.Client(verify=VERIFY_SSL, timeout=120, follow_redirects=True) as client:
    token = get_token(client)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",       # without this you get XML, not JSON
        "Content-Type": "application/json",
    }

    # The trailing slash is required -- without it the request isn't routed here.
    resp = client.post(f"{BASE_URL}/api/sales/orders/", headers=headers, json=ORDER)
    print(f"HTTP {resp.status_code}")
    print(resp.text[:1000] or "(empty body)")   # success shape is unconfirmed -- read it raw
    resp.raise_for_status()

    # Find the new order number. The response key is not confirmed, so try the
    # plausible spellings rather than assuming one.
    body = resp.json() if resp.text.strip().startswith("{") else {}
    order_no = next(
        (str(body[key]) for key in ("OrderNo", "OrderNumber", "Id", "OrderId") if body.get(key)),
        None,
    )
    if not order_no:
        raise SystemExit("No order number in the create response -- see the body printed above")

    # Read back -- HTTP 200 on the POST doesn't confirm what actually landed.
    resp = client.get(f"{BASE_URL}/api/sales/orders/{order_no}", headers=headers)
    resp.raise_for_status()
    order = resp.json()
    lines = (order.get("Lines") or {}).get("list") or []
    print(f"Order {order_no}: customer {order.get('CustomerId')}, {len(lines)} line(s)")
```

**C#:**
```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string CustomerId = "100198";
const string CompanyId = "ACME";
const string LocationId = "10";
const string Taker = "JSMITH";
const string PromiseDate = "2030-01-06";
const string TermsId = "NET30";
const string ShipToId = "200";
const string ItemId = "WIDGET-001";
const decimal Quantity = 1m;
const decimal UnitPrice = 0.99m;
// ---------------------------------------------------------------------------

var order = new Dictionary<string, object?>
{
    ["CustomerId"] = CustomerId,
    ["CompanyId"] = CompanyId,
    ["LocationId"] = LocationId,
    ["Taker"] = Taker,
    ["PromiseDate"] = PromiseDate,
    ["TermsId"] = TermsId,
    ["ShipToId"] = ShipToId,
    ["SourceLocId"] = LocationId,
    ["PoNo"] = "PO-TEST-001",
    ["Quote"] = "N",                                    // "Y" makes it a quote, not an order
    ["DeletedFlag"] = "N",
    // Lines is an OBJECT wrapping a list -- a top-level array fails.
    ["Lines"] = new Dictionary<string, object?>
    {
        ["list"] = new[]
        {
            new Dictionary<string, object?>
            {
                ["ItemId"] = ItemId,
                ["UnitQuantity"] = Quantity,
                ["UnitOfMeasure"] = "EA",
                ["UnitPrice"] = UnitPrice,
                ["TaxItem"] = "N",
                ["Delete"] = "N",
            },
        },
    },
};

var handler = new HttpClientHandler
{
    // Test tenants often present a self-signed cert. Delete this line in production.
    ServerCertificateCustomValidationCallback =
        HttpClientHandler.DangerousAcceptAnyServerCertificateValidator,
    AllowAutoRedirect = true,
};
using var client = new HttpClient(handler) { Timeout = TimeSpan.FromMinutes(2) };
client.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));

var token = await GetTokenAsync(client);
client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);

// The trailing slash is required -- without it the request isn't routed here.
var resp = await client.PostAsync(
    $"{BaseUrl}/api/sales/orders/",
    new StringContent(JsonSerializer.Serialize(order), Encoding.UTF8, "application/json"));
var responseBody = await resp.Content.ReadAsStringAsync();
Console.WriteLine($"HTTP {(int)resp.StatusCode}");
Console.WriteLine(responseBody.Length > 0
    ? responseBody[..Math.Min(1000, responseBody.Length)]   // success shape is unconfirmed
    : "(empty body)");
resp.EnsureSuccessStatusCode();

// Find the new order number. The response key is not confirmed, so try the
// plausible spellings rather than assuming one.
string? orderNo = null;
if (responseBody.TrimStart().StartsWith("{"))
{
    using var created = JsonDocument.Parse(responseBody);
    foreach (var key in new[] { "OrderNo", "OrderNumber", "Id", "OrderId" })
    {
        if (created.RootElement.TryGetProperty(key, out var value) &&
            value.ValueKind is not (JsonValueKind.Null or JsonValueKind.Undefined))
        {
            orderNo = value.ToString();
            if (!string.IsNullOrWhiteSpace(orderNo)) break;
        }
    }
}

if (string.IsNullOrWhiteSpace(orderNo))
{
    Console.WriteLine("No order number in the create response -- see the body printed above");
    return;
}

// Read back -- HTTP 200 on the POST doesn't confirm what actually landed.
resp = await client.GetAsync($"{BaseUrl}/api/sales/orders/{orderNo}");
resp.EnsureSuccessStatusCode();
using var readBack = JsonDocument.Parse(await resp.Content.ReadAsStringAsync());
var lineCount = readBack.RootElement.TryGetProperty("Lines", out var lines) &&
                lines.TryGetProperty("list", out var list) &&
                list.ValueKind == JsonValueKind.Array
    ? list.GetArrayLength()
    : 0;
var customer = readBack.RootElement.TryGetProperty("CustomerId", out var c) ? c.ToString() : "?";
Console.WriteLine($"Order {orderNo}: customer {customer}, {lineCount} line(s)");

// --- helpers ---------------------------------------------------------------

// v2 token endpoint — credentials go in the body, never in headers.
static async Task<string> GetTokenAsync(HttpClient client)
{
    var payload = JsonSerializer.Serialize(new { username = Username, password = Password });
    var response = await client.PostAsync(
        $"{BaseUrl}/api/security/token/v2",
        new StringContent(payload, Encoding.UTF8, "application/json"));
    response.EnsureSuccessStatusCode();
    return ReadField(await response.Content.ReadAsStringAsync(), "AccessToken");
}

// Some middleware answers this endpoint in XML even when asked for JSON.
static string ReadField(string payload, string field)
{
    try
    {
        var value = JsonDocument.Parse(payload).RootElement.GetProperty(field).GetString();
        if (!string.IsNullOrEmpty(value)) return value;
    }
    catch (Exception ex) when (ex is JsonException or KeyNotFoundException) { }

    var match = System.Text.RegularExpressions.Regex.Match(payload, $"<{field}>([^<]+)</{field}>");
    if (!match.Success)
        throw new InvalidOperationException(
            $"No {field} in response: {payload[..Math.Min(200, payload.Length)]}");
    return match.Groups[1].Value;
}
```

<!-- /tabs -->

#### What is not pinned down yet

Stated as unknowns rather than guessed at — if you settle one against your tenant, [open an issue](https://github.com/mrwuss/p21-api-documentation/issues/new/choose) and it gets documented:

- **The success response shape**, including where the generated order number comes back. The example above prints the raw body and probes four plausible key spellings for exactly this reason.
- **Which fields are strictly required** versus optional. The header above is one working example from one 25.2 tenant, not a minimum payload — configuration (taxes, terms, ship-to defaults) decides what your server insists on.
- **Whether the inline ship-to fields are required alongside `ShipToId`** or only act as a fallback when the ship-to record doesn't resolve a full address.
- **HTTP status codes and body for validation failures** — the write-side error vocabulary of this family is undocumented.
- **The other collections in the `/new` template** (`Notes`, `Salesreps`, `BuilderSelectionSheets`, `Samples`) — presumably the same `{"list": [...]}` nesting as `Lines`, but untested.

#### REST vs the Transaction API for order creation

Both create orders. Pick by what you need:

| | `POST /api/sales/orders/` | Transaction API `Order` service |
|---|---|---|
| Payload | Plain domain JSON, lines under `Lines.list` | `DataElements` / `Rows` / `Edits`, every value a string |
| Verified by | Contributor, 25.2 ([issue #108](https://github.com/mrwuss/p21-api-documentation/issues/108)) | This repo, against a live tenant |
| Error reporting | Undocumented (see above) | `Summary.Succeeded` / `Failed` envelope, [documented traps](06-Error-Handling.md) |
| Bulk | One order per call | Many orders per call |
| Assembly lines | Untested | Auto-answers the explode prompt **No** — use the [order-with-assembly](recipes/order-with-assembly.md) recipe instead |

For a walk-through of the Transaction path, see the [create-sales-order recipe](recipes/create-sales-order.md).

### Discovering what your tenant actually exposes

**Don't guess family names — read them off the middleware.** Your own server publishes the authoritative list at:

```
https://{middleware}/docs/apiref.aspx
```

It enumerates every REST and SOAP family the server hosts, per tenant and per version, and links each one to a **`/help` page** (`{base}/{family}/help`) describing its operations. Reaching that page requires the **Access to SOA Admin Page** application-security setting; see [Authentication](00-Authentication.md#application-security-settings-that-affect-api-access).

This matters because family names are not guessable. An earlier version of this document reported that `purchasing/*` 404s — it doesn't; the family is named **`purchasing/purchaseorders`** and it answers fine. The wildcard was a guess written up as a finding.

#### Verified family sweep

`GET {base}/{family}/ping` against a 26.1 tenant, August 2026. This is one tenant at one version — treat it as a worked example of the method, not a universal list:

| Answering (200) | Not on this tenant |
|---|---|
| `accounting/customerformtemplates` · `accounting/exchangerates` · `accounting/gl` · `entity/addresses` · `entity/contacts` · `entity/customers` · `entity/vendors` · `epayments` · `extensibility/userdefinedfields` · `filehandler` · `inventory/externalcounts` · `inventory/inventoryadjustments` · `inventory/parts` · `inventory/partscan` · `inventory/serialnumberextdinfo` · `inventory/v2/parts` · `purchasing/purchaseorders` · `sales/consignmentusageorders` · `sales/opportunities` · `sales/orders` · `sales/tasks` · `service/serviceorders` | `.configuration` · `chat` · `ecommerce` · `eh` · `environment/systems` · `help` · `integrationProcedures` · `inventory/inventorymovement` · `inventory/rental` · `localization` · `pathguide` · `printing` · **`sales/invoices`** (404) · `cardstorage` (**405** — route exists, `GET /ping` not allowed) · `document`, `logistics/roadnet` (500) |

Notable among the ones that answer and aren't documented here yet: **`accounting/gl`**, **`extensibility/userdefinedfields`** (UDF access over REST), **`inventory/inventoryadjustments`**, **`sales/tasks`**, and **`purchasing/purchaseorders`**. A `405` rather than a `404` — as on `cardstorage` — means the family is real and only the probe verb is wrong; worth a `/help` read rather than writing it off.

> **`inventory/v2/parts` is not a different API.** It pings 200 and a single-item GET returns a **byte-identical** response to `inventory/parts` (1,396 bytes for the same item on the tested tenant). Treat it as an alias unless you find a divergence on a write path; [11 Inventory REST API](11-Inventory-REST-API.md) documents the v1 path and applies to both.

*Credit: Felipe Maurer ([P21WWUG profile](https://forums.p21ww.org/UserInfo10045.aspx)) — surfaced `/api/sales/orders` and the middleware endpoint listing in [this forum topic](https://forums.p21ww.org/Topic245514-3.aspx).*

*Credit: [Rob Landham](https://github.com/roblandham) — documented `POST /api/sales/orders/`, the required trailing slash and the `Lines.list` nesting, tested on 25.2 ([issue #108](https://github.com/mrwuss/p21-api-documentation/issues/108)).*

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

1. **Wrong URL pattern for the 4 entities** - Use `/api/entity/customers`, NOT `/api/sales/customers`
2. **Simple ID for customers** - Use `ACME_10`, NOT just `10`
3. **Missing redirect handling** - List endpoints return 307, must follow redirect
4. **Confusing VendorId with supplier_id** - These are different database tables
5. **Expecting orders/items at `/api/entity/`** - Only 4 entities exist there (customers, vendors, contacts, addresses). Inventory uses `/api/inventory/parts` ([Inventory REST API](11-Inventory-REST-API.md)); orders use `/api/sales/orders` ([Other REST Endpoint Families](#other-rest-endpoint-families))

---

## Entity API vs Other APIs

| Feature | Entity API | OData | Transaction | Interactive |
|---------|------------|-------|-------------|-------------|
| Operations | CRUD | Read-only | Bulk CRUD | Stateful CRUD |
| Entities | 4 (see also [Inventory REST API](11-Inventory-REST-API.md)) | Any table/view | Many services | Any P21 window |
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
- [Inventory REST API](11-Inventory-REST-API.md) - Inventory CRUD at `/api/inventory/parts`
- [examples/python/entity/](https://github.com/mrwuss/p21-api-documentation/tree/master/examples/python/entity/) - Test scripts
