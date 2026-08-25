# OData API

> **Disclaimer:** This is unofficial, community-created documentation for Epicor Prophet 21 APIs. It is not affiliated with, endorsed by, or supported by Epicor Software Corporation. All product names, trademarks, and registered trademarks are property of their respective owners. Use at your own risk.

---

## Overview

The OData API provides **read-only** access to P21 data using the OData **v4** protocol. It's the fastest way to query P21 tables and views.

### Key Characteristics

- **Read-only** - Cannot create, update, or delete data
- **Standard protocol** - OData **v4** (see [Protocol version](#protocol-version) — earlier versions of this doc said v3)
- **Direct access** - Query any P21 table or view
- **Efficient** - Supports filtering, field selection (**no server-driven paging** — see [What the service supports](#what-the-service-supports))
- **No session** - Simple request/response model

> **There are two OData surfaces on a P21 server.** This document covers `/odataservice/odata/` — the current one, which reaches every exposed table and view. A second, older surface at `/data/erp/views/v1` exposes a curated set of ~118 views with single-row key addressing. See [The other OData surface](#the-other-odata-surface-dataerpviewsv1).

### Protocol version

Verified against a 26.1 tenant (August 2026) — the service answers as OData **4.0**:

```http
GET {base}/odataservice/odata/table/
    OData-Version: 4.0
    Content-Type: application/json; odata.metadata=minimal; odata.streaming=true

{"@odata.context": "{base}/odataservice/odata/table/$metadata", "value": [...]}
```

```http
GET {base}/odataservice/odata/table/$metadata
    {"$Version": "4.0", "$EntityContainer": "ns.container", ...}
```

`@odata.context` and a JSON CSDL `$metadata` are v4 constructs; v3 used `odata.metadata` at the document root and an XML metadata document. Epicor's own SDK reference guide agrees: *"The Data Services API is based on the OData v4 standard."*

This matters in practice because v4 removed `substringof` (use `contains`) and changed the metadata format — a v3 client library will not talk to this service correctly.

### What the service supports

Epicor publishes an explicit capability list for this implementation. The negatives are the useful part:

| Feature | Supported |
|---|---|
| `$filter` — `eq` `ne` `gt` `ge` `lt` `le` | Yes |
| `$filter` — `and` `or` `not` | Yes |
| `$filter` — `startswith` `endswith` `contains` | Yes |
| `$select` `$orderby` `$top` `$skip` `$count` | Yes |
| **Server-driven paging** | **No** — page yourself with `$top` + `$skip` (see [Page Size Guidance](#page-size-guidance)) |
| `substringof` | No — removed in OData 4.0; use `contains` |
| `$expand` (navigation properties) | Not exposed — there are no relationships to expand; join client-side |

*(Source: Prophet 21 SDK, Data Services reference guide, served from your own middleware at `{middleware}/docs/p21sdk/index.html#/data/reference-guide`.)*

---

## Endpoints

| Endpoint | Purpose |
|----------|---------|
| `/odataservice/odata/table/{tablename}` | Query a database table |
| `/odataservice/odata/view/{viewname}` | Query a database view |
| `/odataservice/odata/table/$metadata` | Schema document — every exposed table and column |
| `/odataservice/odata/view/$metadata` | Schema document for views |

### Base URL Example

```http
https://play.p21server.com/odataservice/odata/table/supplier
```

> **Base host, not ui_server:** OData runs on the P21 **base host** — unlike the Transaction and Interactive APIs, it does **not** use the UI server URL returned by the router endpoint. Don't prefix OData paths with the ui_server.

### Discovering What's Exposed (`$metadata`)

`$metadata` hangs off the **collection path**, not the service root: `/odataservice/odata/table/$metadata` works, while `/odataservice/odata/$metadata` returns **404**. (The correct path is the one echoed in every response's `@odata.context`.)

The document is **JSON CSDL**, not the XML EDMX you may expect, and it is large — roughly 4 MB and ~3,400 tables on a stock tenant. Exposed tables are the keys of `ns.container`:

```python
"""Check what tables are exposed via OData $metadata."""
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
        "Accept": "application/json",       # 2026.1 returns an empty 500 without this
        "Content-Type": "application/json",
    }

    response = client.get(
        f"{BASE_URL}/odataservice/odata/table/$metadata",
        headers=headers,
        timeout=300,  # ~4 MB payload; the shared client's 120s default is tight
    )
    response.raise_for_status()
    metadata = response.json()
    tables = [name for name in metadata["ns"]["container"] if not name.startswith("$")]
    print(f"{len(tables)} tables exposed")           # e.g. 3394
    print("po_hdr exposed?", "po_hdr" in tables)
```

This is the quickest way to answer "is this table actually exposed to Data Services?" before debugging a 404 — and to find the real name of a table you're guessing at.

> **Newly created tables need a manual refresh.** A table added after the service started (e.g. a new UDT) is absent from `$metadata` and 404s on query until **SOA Admin → Refresh OData API service** is run. See [Schema Refresh](#odata-schema-refresh).

---

## Authentication

Include the Bearer token in the Authorization header:

```http
GET /odataservice/odata/table/supplier HTTP/1.1
Host: play.p21server.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

See [Authentication](00-Authentication.md) for token generation.

### Prerequisites (User Credential Auth Only)

If you authenticate with **User Credentials** (username/password), a valid token alone is **not enough**. The P21 user must also have two permissions configured in the P21 Desktop Client:

1. **User Maintenance** → Application Security → **"Allow OData API Service"** = Yes
2. **Role Maintenance** → Dataservice Permission → **Allow** the specific tables/views being queried

Without these, you'll get a `"You are not authorized to access API"` error even with a valid token.

> **Consumer Key** authentication skips these requirements - access is controlled by the key's API scope instead. See [Authentication - P21 Permissions](00-Authentication.md#p21-permissions-user-credential-auth) for full setup details and screenshots.

---

## Query Parameters

All OData query parameters are prefixed with `$`.

### $select - Choose Fields

Return only specific fields:

```http
/odata/table/supplier?$select=supplier_id,supplier_name
```

> ⚠️ **An unknown `$select` column returns 404, not 400.** Naming a column that doesn't exist fails the whole request with an empty-bodied **404** — indistinguishable at a glance from "table not exposed" or "no permission". If a table you know exists suddenly 404s, drop the `$select` and retry before chasing Data Service permissions; a misremembered column name (e.g. `supplier_id` on `po_hdr`, which actually has `vendor_id`) is the more common cause. Verified on 2026.1.

### $filter - Filter Results

Filter records based on conditions:

```http
/odata/table/supplier?$filter=supplier_id eq 10050
```

### $orderby - Sort Results

Sort by one or more fields:

```http
/odata/table/supplier?$orderby=supplier_name asc
```

### $top - Limit Results

Return only N records:

```http
/odata/table/supplier?$top=10
```

### $skip - Pagination

Skip N records (combine with $top for paging):

```http
/odata/table/supplier?$skip=20&$top=10
```

> **No `@odata.nextLink`:** P21's OData responses do **not** include a continuation link. Paging is entirely client-driven with `$skip`/`$top` — loop until a page comes back with fewer rows than `$top` (or track `@odata.count`). See the [Pagination Helper](#pagination-helper).

### $count - Get Count

Include total count in response:

```http
/odata/table/supplier?$count=true
```

---

## Filter Expressions

### Comparison Operators

| Operator | Meaning | Example |
|----------|---------|---------|
| `eq` | Equal | `$filter=supplier_id eq 10050` |
| `ne` | Not equal | `$filter=status ne 'Inactive'` |
| `gt` | Greater than | `$filter=amount gt 100` |
| `ge` | Greater or equal | `$filter=date ge 2025-01-01` |
| `lt` | Less than | `$filter=quantity lt 50` |
| `le` | Less or equal | `$filter=price le 99.99` |

### Logical Operators

| Operator | Example |
|----------|---------|
| `and` | `$filter=supplier_id eq 10050 and row_status_flag eq 704` |
| `or` | `$filter=status eq 'A' or status eq 'B'` |

> ⚠️ **`in` is accepted and silently ignored.** `$filter=id in (2,3,4)` returns HTTP 200 with **every row in the table** — the filter is discarded without a warning, unlike a genuine syntax error, which 404s. Match multiple values with an `or` chain instead. Verified on 26.1.5910.3 — see [Avoiding N+1 Query Patterns](#avoiding-n1-query-patterns).
| `not` | `$filter=not endswith(name,'Inc')` |

### String Functions

| Function | Example |
|----------|---------|
| `startswith` | `$filter=startswith(supplier_name,'ABC')` |
| `endswith` | `$filter=endswith(supplier_name,'Inc')` |
| `contains` | `$filter=contains(description,'filter')` |

### Null Checks

```http
$filter=expiration_date eq null
$filter=notes ne null
```

---

## Common Patterns

### Active Record Filter

P21 tracks record status two different ways, and **using the wrong one 404s the whole request**. Check which column the table actually has before filtering.

**Tables with `row_status_flag`** (e.g. `price_page`, `customer_salesrep`). The values are `code_p21` codes — confirmed against those tables on 26.1:

| `row_status_flag` | Meaning |
|---|---|
| `704` | Active |
| `705` | Inactive |
| `700` | Delete (soft-deleted) |

```http
$filter=row_status_flag eq 704
```

This filter matters more than it looks: soft-deleted rows are not removed, so they accumulate. On the tenants tested, **297 of 300 sampled `price_page` rows were `700` (deleted)**, and `customer_salesrep` held **12,060 rows at `700` against 20,201 at `704`** — an unfiltered query returns dead data, in the `price_page` case overwhelmingly so.

A deleted row also keeps its old values (`customer_salesrep` rows at `700` still carry their last `commission_percentage`), so an unfiltered read isn't merely noisy — it reports retired records with live-looking data. The write side of the same flag is in [03 § Removing a Salesrep Grid Row](03-Transaction-API.md#customer-service-removing-a-salesrep-grid-row): the Transaction API sets it with the **label** (`Delete`), not the code.

**Tables with `delete_flag`** — `customer`, `supplier`, `inv_mast` and many others have **no `row_status_flag` at all**. They use a `'Y'`/`'N'` char column:

```http
$filter=delete_flag eq 'N'
```

> ⚠️ **Filtering on the wrong column fails loudly — and misleadingly.** `supplier?$filter=row_status_flag eq 704` returns **404** with `Could not find a property named 'row_status_flag' on type 'dbo.supplier'`. A bare 404 from this API is easy to misread as "table not exposed" or "no permission", so check the column first: `GET /odataservice/odata/table/{name}?$top=1` and look at the keys.
>
> **Quoting a numeric key fails the same way.** `customer_salesrep?$filter=customer_id eq '100198'` also returns **404** — `A binary operator with incompatible types was detected. Found operand types 'Edm.Decimal' and 'Edm.String'`. Many `*_id` columns (`customer_salesrep.customer_id`, `ship_to_salesrep.ship_to_id`) are `Edm.Decimal` even though the value looks like an identifier string, so send it bare: `customer_id eq 100198`. The same `$top=1` probe answers this too — a quoted value in the response means a string column. Note the asymmetry with the Transaction API, where every `Value` you write is a string regardless of column type.

### Company Scoping — `company_id` vs `company_no`

The company code is the same value everywhere (`"ACME"`), but **the column that holds it has two different names**, and a third group of tables doesn't carry it at all. Verified on 26.1.5910.3:

| Column | Tables (verified) |
|---|---|
| `company_id` | `oe_hdr`, `customer`, `inv_loc`, `contacts` |
| **`company_no`** | `po_hdr`, `po_line`, `invoice_hdr` |
| *(neither)* | `supplier`, `inv_mast`, `address` — these records are not company-scoped |

Purchasing and invoicing use `company_no`; order entry, customers and inventory locations use `company_id`. There is no way to infer which from the table's subject matter, and guessing wrong produces the **404** described above rather than an empty result — `po_hdr?$select=po_no,company_id` fails outright.

> **The API's field names are not the column names.** The `m_reprintpurchaseorders` report takes its criteria field as **`company_id`**, even though the underlying `po_hdr` column is `company_no`. Window/service field names and database column names are separate namespaces throughout P21 — take criteria names from `GET /api/v2/definition/{service}` and column names from the table itself, and don't translate between them.

### Non-Expired Records

To filter out expired records, compare `expiration_date` against a date value:

```http
$filter=expiration_date ge 2025-01-01
```

**Warning:** The `now()` function is not supported in P21 OData. Using it will return a 404 error:

```http
# DOES NOT WORK - returns 404
$filter=expiration_date ge now()

# CORRECT - use explicit date
$filter=expiration_date ge 2025-12-28
```

For date-relative queries, calculate the date in your application code:

> Full runnable version: [Code Examples](#code-examples) — the same `params`/`filter` pattern shown below is used in a complete, authenticated query in the Filtered Query example.

<!-- tabs -->

**Python**

```python
from datetime import date, timedelta

tomorrow = (date.today() + timedelta(days=1)).isoformat()
filter_expr = f"expiration_date ge {tomorrow}"
```

**C#**

```csharp
var tomorrow = DateTime.Today.AddDays(1).ToString("yyyy-MM-dd");
var filterExpr = $"expiration_date ge {tomorrow}";
```

<!-- /tabs -->

### No Joins — Chain Queries by UID

P21 OData has **no joins**: each request hits a single table or view. To traverse relationships, chain queries on the `_uid` key columns — every child table carries its parent's uid. Example, walking a job contract down to its bins and item IDs:

```text
job_price_hdr    $filter=contract_no eq 'JOB-1001'          → job_price_hdr_uid
job_price_line   $filter=job_price_hdr_uid eq {uid}        → job_price_line_uid, inv_mast_uid
job_price_bin    $filter=job_price_line_uid eq {line_uid}  → min_qty / max_qty / reorder_qty ...
inv_mast         $filter=inv_mast_uid eq {im_uid}          → item_id
```

Two ways to avoid long chains:

- **Check for a pre-joined view first.** Many `p21_view_*` views already join the common paths (e.g. `p21_view_bin`) — query `/odataservice/odata/view/{viewname}` instead of chaining tables.
- **Batch the lookups** — collect the uids from one query and fetch the next level with an `or`-combined filter rather than one call per row (see [Avoiding N+1 Query Patterns](#avoiding-n1-query-patterns)).

---

## Data Type Formatting

| Type | Format | Example |
|------|--------|---------|
| String | Single quotes | `'Active'` |
| Number | No quotes | `10050` |
| Decimal | No quotes | `99.99` |
| Date | ISO format | `2025-01-01` |
| DateTime | ISO format | `2025-01-01T00:00:00.000Z` |
| Boolean | No quotes | `true` or `false` |
| GUID | No quotes | `5BC2E4CE-0C0A-4394-A066-29B5835424DA` |

### String Escaping

Single quotes in values must be escaped by doubling:

```http
$filter=supplier_name eq 'O''Brien Supply'
```

### Item IDs with Special Characters

P21 item IDs commonly contain characters that need URL encoding in OData filters: `/`, `+`, `#`, `&`, and spaces. The single-quote doubling rule still applies within the OData filter expression, but these special characters also need URL encoding in the query string.

**Python pattern for safe OData filter construction:**

<!-- tabs -->

**Python**

```python
"""Build an OData filter for an item ID with special characters, then query it."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
ITEM_ID = "1/2-FITTING"                   # item ID containing characters that need escaping
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


def safe_item_filter(item_id: str) -> str:
    """Build a safe OData filter for item IDs with special characters.

    Handles:
    - Single quotes (doubled within OData expression)
    - URL-unsafe characters (/, +, #, &, spaces) via percent-encoding

    Args:
        item_id: Raw item ID (e.g., "1/2-FITTING", "ITEM+SIZE#3")

    Returns:
        URL-encoded filter expression
    """
    # First, escape single quotes for OData
    escaped = item_id.replace("'", "''")

    # Build the filter expression
    filter_expr = f"item_id eq '{escaped}'"

    return filter_expr


# Examples of item IDs that need escaping:
# "1/2-FITTING"     -> item_id eq '1/2-FITTING'     (/ needs URL encoding)
# "ITEM+SIZE"       -> item_id eq 'ITEM+SIZE'       (+ needs URL encoding)
# "PART #3"         -> item_id eq 'PART #3'          (# and space need URL encoding)
# "O'RING-204"      -> item_id eq 'O''RING-204'     (quote doubled)


with httpx.Client(verify=VERIFY_SSL, timeout=120, follow_redirects=True) as client:
    token = get_token(client)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",       # 2026.1 returns an empty 500 without this
        "Content-Type": "application/json",
    }

    # httpx encodes the filter value in the query string automatically
    params = {"$filter": safe_item_filter(ITEM_ID)}
    response = client.get(
        f"{BASE_URL}/odataservice/odata/table/inv_mast",
        params=params,
        headers=headers,
    )
    response.raise_for_status()

    data = response.json()
    print(f"{len(data['value'])} matching rows for {ITEM_ID!r}")
    for row in data["value"]:
        print(row.get("item_id"), row.get("item_desc"))
```

**C#**

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string ItemId = "1/2-FITTING";                    // item ID containing characters that need escaping
// ---------------------------------------------------------------------------

var handler = new HttpClientHandler
{
    // Test tenants often present a self-signed cert. Delete this line in production.
    ServerCertificateCustomValidationCallback =
        HttpClientHandler.DangerousAcceptAnyServerCertificateValidator,
};
using var client = new HttpClient(handler) { Timeout = TimeSpan.FromMinutes(2) };
client.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));

var token = await GetTokenAsync(client);
client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);

// Examples of item IDs that need escaping:
// "1/2-FITTING"     -> item_id eq '1/2-FITTING'     (/ needs URL encoding)
// "ITEM+SIZE"       -> item_id eq 'ITEM+SIZE'       (+ needs URL encoding)
// "PART #3"         -> item_id eq 'PART #3'          (# and space need URL encoding)
// "O'RING-204"      -> item_id eq 'O''RING-204'     (quote doubled)

// Using with HttpClient (URL encoding via Uri.EscapeDataString):
var filter = Uri.EscapeDataString(SafeItemFilter(ItemId));
var url = $"{BaseUrl}/odataservice/odata/table/inv_mast?$filter={filter}";
var response = await client.GetAsync(url);
response.EnsureSuccessStatusCode();
// HttpClient sends the properly encoded query string

var json = await response.Content.ReadAsStringAsync();
var data = JsonDocument.Parse(json).RootElement;
var rows = data.GetProperty("value");
Console.WriteLine($"{rows.GetArrayLength()} matching rows for '{ItemId}'");
foreach (var row in rows.EnumerateArray())
{
    var itemId = row.TryGetProperty("item_id", out var idProp) ? idProp.ToString() : "";
    var itemDesc = row.TryGetProperty("item_desc", out var descProp) ? descProp.ToString() : "";
    Console.WriteLine($"{itemId} {itemDesc}");
}

// --- helpers ---------------------------------------------------------------

/// <summary>
/// Build a safe OData filter for item IDs with special characters.
/// Doubles single quotes for OData; URL encoding is handled by HttpClient.
/// </summary>
static string SafeItemFilter(string itemId)
{
    // Escape single quotes for OData
    var escaped = itemId.Replace("'", "''");

    // Build the filter expression
    return $"item_id eq '{escaped}'";
}

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

> **Tip:** When using `httpx` (Python) with the `params` dict or `Uri.EscapeDataString` (C#), URL encoding is handled automatically. The main concern is correctly doubling single quotes within the OData filter expression itself.

---

## Response Format

### Success Response

```json
{
    "@odata.context": "https://play.p21server.com/odataservice/odata/$metadata#supplier",
    "value": [
        {
            "supplier_id": 10050,
            "supplier_name": "ABC Supply Company",
            "row_status_flag": 704,
            ...
        },
        ...
    ]
}
```

### With Count

```json
{
    "@odata.context": "...",
    "@odata.count": 1547,
    "value": [...]
}
```

### Error Response

```json
{
    "error": {
        "code": "400",
        "message": "Invalid filter expression"
    }
}
```

---

## Common Tables

| Table | Description |
|-------|-------------|
| `supplier` | Supplier master data |
| `customer` | Customer records |
| `inv_mast` | Inventory master |
| `price_page` | Price page definitions |
| `price_book` | Price book records |
| `price_library` | Price library definitions |
| `product_group` | Product groups |

---

## Undeployed / Unlicensed Windows: Readable Tables, No API Surface

OData exposes the **schema**, not the deployment state. A table can be fully readable over OData while the feature that populates it is **undeployed or unlicensed** — its maintenance window is classic-desktop-only and it has no Transaction/Interactive API surface. The rows you read are then **dead storage**: nothing writes them and no business logic consults them.

The clearest verified example (26.1.5894.1, play, July 2026) is the **native zip → salesrep/territory** family. The schema is present and OData-readable, but on an install where the module is undeployed the tables are empty and inert:

| Table | Contents | OData |
|-------|----------|-------|
| `postal_code_group_hdr` | zip-group id/desc per company, `primary_salesrep_id`, `territory_uid`, `default_sales_location_id`, source-location ids | readable |
| `postal_code_group_detail` | `from_postal_code`/`to_postal_code` ranges per group | readable |
| `postal_code_group_location_priority` | ranked location list per group | readable |
| `salesrep_postalcode` | `salesrep_id` + `start_postal_code`/`end_postal_code` (simpler, likely older) | readable |
| `ideal_locations_by_zip` | location-sourcing-by-zip (paired with the "Import Ideal Locations" menu item) | readable |

**Why there's no write path:**

- **Window:** "Postal Code Group Maintenance" (`w_postal_code_group_maint`), AR › Maintenance — **classic desktop only** (`frame_menu`: `new_ui_enabled='N'`, `angular_enabled='N'`, `service_name` **NULL**). A NULL `service_name` is the tell that there is no API surface (see [Window→Service Discovery](04-Interactive-API.md#8-window-to-service-discovery-frame_menu)).
- **Transaction API:** no service — absent from `/api/v2/services`; plausible hidden names all 500 on `/definition`.
- **Interactive API:** by-Name open returns 400 *"not available or user does not have permission"* — the [undeployed-window signal](03-Transaction-API.md#endpoints), not a grantable permission.

**Behavioral consequence — verified:** seeding matching rows in **both** `salesrep_postalcode` and `postal_code_group_hdr`+`detail` (a zip mapped to a deliberately wrong-region rep) and then creating a customer with that zip in the mailing and physical address **does not** default `salesrep_id`. The create fails *"Salesrep ID is required for a new ship to."* until the rep is supplied explicitly — [Customer create](recipes/create-customer.md) never consults these tables when the module is undeployed. So: **readable ≠ live.** Treat OData-visibility of a feature table as evidence the schema exists, not that the feature is active on your install.

---

## Examples

### Basic Query

Get all suppliers:

```http
GET /odataservice/odata/table/supplier
```

### Filtered Query

Get active price pages for a supplier:

```http
GET /odataservice/odata/table/price_page
    ?$filter=supplier_id eq 10050 and row_status_flag eq 704
    &$select=price_page_uid,description,effective_date,expiration_date
    &$orderby=description
```

### Pagination

Get page 3 (10 records per page):

```http
GET /odataservice/odata/table/supplier
    ?$skip=20
    &$top=10
    &$count=true
```

### Complex Filter

Products starting with 'FILTER' and price over $10:

```http
GET /odataservice/odata/table/inv_mast
    ?$filter=startswith(item_id,'FILTER') and list_price gt 10
    &$select=item_id,item_desc,list_price
```

---

## Code Examples

### Basic Query

<!-- tabs -->

**Python**

```python
"""Query suppliers with $top and $select."""
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
        "Accept": "application/json",       # 2026.1 returns an empty 500 without this
        "Content-Type": "application/json",
    }

    # Query suppliers
    response = client.get(
        f"{BASE_URL}/odataservice/odata/table/supplier",
        params={"$top": 10, "$select": "supplier_id,supplier_name"},
        headers=headers,
    )
    response.raise_for_status()

    data = response.json()
    for supplier in data["value"]:
        print(f"{supplier['supplier_id']}: {supplier['supplier_name']}")
```

**C#**

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
};
using var client = new HttpClient(handler) { Timeout = TimeSpan.FromMinutes(2) };
client.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));

var token = await GetTokenAsync(client);
client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);

// Query suppliers
var select = Uri.EscapeDataString("supplier_id,supplier_name");
var url = $"{BaseUrl}/odataservice/odata/table/supplier?$top=10&$select={select}";
var response = await client.GetAsync(url);
response.EnsureSuccessStatusCode();

var json = await response.Content.ReadAsStringAsync();
var data = JsonDocument.Parse(json).RootElement;
foreach (var supplier in data.GetProperty("value").EnumerateArray())
{
    var supplierId = supplier.GetProperty("supplier_id");
    var supplierName = supplier.GetProperty("supplier_name");
    Console.WriteLine($"{supplierId}: {supplierName}");
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

### Filtered Query

<!-- tabs -->

**Python**

```python
"""Query active price pages for a supplier."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
SUPPLIER_ID = 10050                       # supplier to look up price pages for
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
        "Accept": "application/json",       # 2026.1 returns an empty 500 without this
        "Content-Type": "application/json",
    }

    # Get price pages for supplier
    params = {
        "$filter": f"supplier_id eq {SUPPLIER_ID} and row_status_flag eq 704",
        "$select": "price_page_uid,description,calculation_value1",
        "$orderby": "description",
    }

    response = client.get(
        f"{BASE_URL}/odataservice/odata/table/price_page",
        params=params,
        headers=headers,
    )
    response.raise_for_status()

    data = response.json()
    for page in data["value"]:
        print(page["price_page_uid"], page["description"], page["calculation_value1"])
```

**C#**

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const int SupplierId = 10050;                            // supplier to look up price pages for
// ---------------------------------------------------------------------------

var handler = new HttpClientHandler
{
    // Test tenants often present a self-signed cert. Delete this line in production.
    ServerCertificateCustomValidationCallback =
        HttpClientHandler.DangerousAcceptAnyServerCertificateValidator,
};
using var client = new HttpClient(handler) { Timeout = TimeSpan.FromMinutes(2) };
client.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));

var token = await GetTokenAsync(client);
client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);

// Get price pages for supplier
var filter = Uri.EscapeDataString($"supplier_id eq {SupplierId} and row_status_flag eq 704");
var select = Uri.EscapeDataString("price_page_uid,description,calculation_value1");
var orderby = Uri.EscapeDataString("description");

var url = $"{BaseUrl}/odataservice/odata/table/price_page?$filter={filter}&$select={select}&$orderby={orderby}";
var response = await client.GetAsync(url);
response.EnsureSuccessStatusCode();

var json = await response.Content.ReadAsStringAsync();
var data = JsonDocument.Parse(json).RootElement;
foreach (var page in data.GetProperty("value").EnumerateArray())
{
    var uid = page.GetProperty("price_page_uid");
    var description = page.GetProperty("description");
    var calcValue = page.GetProperty("calculation_value1");
    Console.WriteLine($"{uid} {description} {calcValue}");
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

### Pagination Helper

<!-- tabs -->

**Python**

```python
"""Fetch all records from a table via $skip/$top pagination."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
TABLE = "supplier"                        # table to page through
FILTER_EXPR = "row_status_flag eq 704"    # optional; set to None for no filter
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


def get_all_records(client, headers, base_url, table, filter_expr=None, page_size=5000):
    """Fetch all records with automatic pagination.

    Args:
        client: An authenticated httpx.Client.
        headers: Request headers, including the Authorization bearer token.
        base_url: OData service base URL.
        table: Table name to query.
        filter_expr: Optional OData $filter expression.
        page_size: Records per request. Larger values mean fewer HTTP
            round-trips, which is usually the biggest performance factor.
            Use 5,000-25,000 for bulk/preload scenarios. Use 50-200
            when paginating for a UI. There is no documented server-side
            maximum -- 25,000 has been verified in production.
    """
    records = []
    skip = 0

    while True:
        params = {"$top": page_size, "$skip": skip, "$count": "true"}
        if filter_expr:
            params["$filter"] = filter_expr

        response = client.get(
            f"{base_url}/table/{table}",
            params=params,
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()

        records.extend(data["value"])
        total = data.get("@odata.count", len(records))

        if len(records) >= total:
            break
        skip += page_size

    return records


with httpx.Client(verify=VERIFY_SSL, timeout=120, follow_redirects=True) as client:
    token = get_token(client)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",       # 2026.1 returns an empty 500 without this
        "Content-Type": "application/json",
    }

    all_records = get_all_records(
        client,
        headers,
        f"{BASE_URL}/odataservice/odata",
        TABLE,
        filter_expr=FILTER_EXPR,
        page_size=200,
    )
    print(f"{len(all_records)} records fetched from {TABLE}")
```

**C#**

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string Table = "supplier";                        // table to page through
const string FilterExpr = "row_status_flag eq 704";     // optional; pass null for no filter
// ---------------------------------------------------------------------------

var handler = new HttpClientHandler
{
    // Test tenants often present a self-signed cert. Delete this line in production.
    ServerCertificateCustomValidationCallback =
        HttpClientHandler.DangerousAcceptAnyServerCertificateValidator,
};
using var client = new HttpClient(handler) { Timeout = TimeSpan.FromMinutes(2) };
client.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));

var token = await GetTokenAsync(client);
client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);

var records = await GetAllRecordsAsync(
    client, $"{BaseUrl}/odataservice/odata", Table, FilterExpr, pageSize: 200);
Console.WriteLine($"{records.Count} records fetched from {Table}");

// --- helpers ---------------------------------------------------------------

/// <summary>
/// Fetch all records with automatic pagination.
/// </summary>
/// <param name="client">An authenticated HttpClient.</param>
/// <param name="baseUrl">OData service base URL.</param>
/// <param name="table">Table name to query.</param>
/// <param name="filterExpr">Optional OData $filter expression.</param>
/// <param name="pageSize">
/// Records per request. Larger values mean fewer HTTP round-trips,
/// which is usually the biggest performance factor.
/// Use 5,000-25,000 for bulk/preload scenarios. Use 50-200
/// when paginating for a UI. There is no documented server-side
/// maximum -- 25,000 has been verified in production.
/// </param>
static async Task<List<JsonElement>> GetAllRecordsAsync(
    HttpClient client, string baseUrl, string table,
    string? filterExpr = null, int pageSize = 5000)
{
    var records = new List<JsonElement>();
    var skip = 0;

    while (true)
    {
        var query = $"$top={pageSize}&$skip={skip}&$count=true";
        if (filterExpr != null)
            query += $"&$filter={Uri.EscapeDataString(filterExpr)}";

        var url = $"{baseUrl}/table/{table}?{query}";
        var response = await client.GetAsync(url);
        response.EnsureSuccessStatusCode();

        var json = await response.Content.ReadAsStringAsync();
        var data = JsonDocument.Parse(json).RootElement;

        foreach (var item in data.GetProperty("value").EnumerateArray())
            records.Add(item.Clone());

        var total = data.TryGetProperty("@odata.count", out var countProp)
            ? countProp.GetInt32()
            : records.Count;

        if (records.Count >= total)
            break;
        skip += pageSize;
    }

    return records;
}

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

## Best Practices

1. **Always use $select** - Only request fields you need
2. **Add $filter early** - Filter server-side, not client-side
3. **Use $top for previews** - Don't fetch all data unnecessarily
4. **Right-size your page size** - Use large `$top` (5,000-25,000) for bulk/preload fetches; use small `$top` (50-200) for UI pagination. Round-trip overhead dwarfs payload size — see [Page Size Guidance](#page-size-guidance)
5. **Escape strings properly** - Double single quotes in values
6. **Handle null values** - Check for null in filters and responses

---

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| 400 Bad Request | Invalid filter syntax | Check filter expression |
| 401 Unauthorized | Invalid/expired token | Refresh token |
| 401/403 "Not authorized" | Valid token but missing P21 permissions | Enable "Allow OData API Service" in User Maintenance and grant table access in Role Maintenance → Dataservice Permission. See [Prerequisites](#prerequisites-user-credential-auth-only) |
| 404 Not Found | Table doesn't exist, or unsupported function | Verify table name; avoid `now()` |
| 500 Server Error | Query too complex | Simplify query |

### now() Function Not Supported

The standard OData `now()` function returns 404 in P21. Use explicit date values instead:

> Full runnable version: [Code Examples](#code-examples) — the Filtered Query example is a complete, authenticated program using the same `params` pattern.

<!-- tabs -->

**Python**

```python
# Calculate date in code
from datetime import date, timedelta
tomorrow = (date.today() + timedelta(days=1)).isoformat()

# Use in filter
params = {"$filter": f"expiration_date ge {tomorrow}"}
```

**C#**

```csharp
// Calculate date in code
var tomorrow = DateTime.Today.AddDays(1).ToString("yyyy-MM-dd");

// Use in filter
var filter = Uri.EscapeDataString($"expiration_date ge {tomorrow}");
var url = $"{odataUrl}/table/price_page?$filter={filter}";
```

<!-- /tabs -->

---

## Page Size Guidance

Each HTTP request carries overhead: TCP connection, authentication, query planning, and serialization. For large result sets, **the number of round-trips is usually the biggest performance factor**, not the response payload size.

### Choosing a Page Size

| Scenario | Recommended `$top` | Why |
|----------|---------------------|-----|
| Preloading / caching / bulk export | 5,000 - 25,000 | Minimize HTTP round-trips; 1 request beats 22 |
| UI pagination (browsable tables) | 50 - 200 | Match what the user actually sees |
| Unbounded queries (unknown size) | 1,000 - 5,000 | Balance round-trips vs memory |

> **No documented server-side cap.** The P21 SDK does not specify a maximum page size. The Web.config allows up to 100 MB responses. A `$top=25000` request has been verified working in production. Test with your dataset, but don't assume 100 is the right default.

### Real-World Impact

Fetching ~2,500 records with `$select` on a few columns:

| Page Size | Requests | Wall Time |
|-----------|----------|-----------|
| 100 | 25 | ~16s |
| 5,000 | 1 | ~1.7s |

The 10x improvement comes entirely from eliminating round-trip overhead.

---

## Performance Tips

- **Minimize HTTP round-trips** - This is the #1 factor. Use a large `$top` when you need all the data instead of looping with small pages
- **Always use $select** - Only request fields you need; smaller payloads transfer faster
- **Filter server-side** - Use `$filter` instead of fetching everything and filtering in code
- Use views for pre-joined data when available
- For UI-driven pagination, match page size to display needs (50-200 rows)

### Measured Performance

| Query Type | Records | Time |
|------------|---------|------|
| Simple table | 10 | ~100ms |
| Filtered query | 160 | ~115ms |
| Full table scan | 1000+ | ~500ms |
| Bulk fetch ($top=5000) | 2,500 | ~1.7s |

### Avoiding N+1 Query Patterns

When working with related entities (e.g., pages → books → libraries), avoid fetching related data in a loop:

> Full runnable version: [Pagination Helper](#pagination-helper) — fetch each related set with a single paged query instead of one call per row.

<!-- tabs -->

**Python**

```python
# BAD: N+1 queries - one query per page
for page in pages:
    book = await odata.get_book_for_page(page['uid'])  # N queries!
    library = await odata.get_library_for_book(book['uid'])  # N more!
```

**C#**

```csharp
// BAD: N+1 queries - one query per page
foreach (var page in pages)
{
    var book = await odata.GetBookForPageAsync(page["uid"]!.ToString());    // N queries!
    var library = await odata.GetLibraryForBookAsync(book["uid"]!.ToString()); // N more!
}
```

<!-- /tabs -->

**Solution 1: Batch queries**

Collapse the N follow-up queries into one by joining the ids with `or`. This is the real fix for the N+1 above — the loop below is what it replaces.

> ### The `in` operator is silently ignored — do not use it
>
> The obvious way to batch is `$filter=price_page_uid in (2,3,4)`. **It returns HTTP 200 and the entire table.** Verified on 26.1.5910.3 (2026-08-11) against a view holding 50,077 rows:
>
> | Filter | Result |
> |---|---|
> | *(none)* | 200 — **50,077 rows** |
> | `price_page_uid in (2,3,4)` | 200 — **50,077 rows** (filter dropped) |
> | `price_page_uid eq 2 or price_page_uid eq 3` | 200 — **2 rows** (correct) |
> | `price_page_uid zz 2` (deliberate garbage) | 404 — `Syntax error at position 17` |
>
> The service *does* validate filter syntax — garbage is rejected loudly. `in` parses and is then discarded, so you get a successful-looking response, no warning, and every row in the table. On a large view that is a silent full-table scan feeding whatever you do next. **Use an `or` chain.**
>
> Keep the chain to a sane length — URLs have limits. Batch ids in groups of ~50 and issue one request per group; that is still an enormous improvement over one request per id.

<!-- tabs -->

**Python**

```python
# Get all pages first -- one query
pages = await odata.query("price_page", filter_expr="supplier_id eq 10050")
page_uids = [p["price_page_uid"] for p in pages]

# Then ONE query per batch of ids instead of one per id.
# `in` is silently ignored on this service -- join with `or`.
BATCH = 50
links = []
for i in range(0, len(page_uids), BATCH):
    chunk = page_uids[i:i + BATCH]
    or_chain = " or ".join(f"price_page_uid eq {uid}" for uid in chunk)
    links += await odata.query("price_page_x_book", filter_expr=or_chain)
```

**C#**

```csharp
// Get all pages first -- one query
var pages = await odata.QueryAsync("price_page", filterExpr: "supplier_id eq 10050");
var pageUids = pages.Select(p => p["price_page_uid"]!.ToString()).ToList();

// Then ONE query per batch of ids instead of one per id.
// `in` is silently ignored on this service -- join with `or`.
const int Batch = 50;
var links = new List<JsonElement>();
for (var i = 0; i < pageUids.Count; i += Batch)
{
    var chunk = pageUids.Skip(i).Take(Batch);
    var orChain = string.Join(" or ", chunk.Select(uid => $"price_page_uid eq {uid}"));
    links.AddRange(await odata.QueryAsync("price_page_x_book", filterExpr: orChain));
}
```

<!-- /tabs -->

**Solution 2: Cache lookups**

For repeated lookups (like library-to-book mapping), cache results:

> Full runnable version: [Code Examples](#code-examples) — no full program in this doc wraps caching directly; combine the cache pattern below with the authenticated request/response handling shown in Basic Query.

<!-- tabs -->

**Python**

```python
class P21OData:
    def __init__(self):
        self._library_book_cache: dict[str, dict | None] = {}

    async def get_book_for_library(self, library_id: str) -> dict | None:
        # Return cached result if available
        if library_id in self._library_book_cache:
            return self._library_book_cache[library_id]

        # Fetch and cache
        result = await self._fetch_book_for_library(library_id)
        self._library_book_cache[library_id] = result
        return result
```

**C#**

```csharp
public class P21OData
{
    private readonly Dictionary<string, JObject?> _libraryBookCache = new();

    public async Task<JObject?> GetBookForLibraryAsync(string libraryId)
    {
        // Return cached result if available
        if (_libraryBookCache.TryGetValue(libraryId, out var cached))
            return cached;

        // Fetch and cache
        var result = await FetchBookForLibraryAsync(libraryId);
        _libraryBookCache[libraryId] = result;
        return result;
    }
}
```

<!-- /tabs -->

---

## The other OData surface: `/data/erp/views/v1`

A P21 server exposes **two** OData endpoints. Everything above describes `/odataservice/odata/`. The middleware's API Reference page also lists a **Data Services** family at `/data/erp/views/v1` — an older, narrower surface that is genuinely useful for one thing the current one does awkwardly: **fetching a single record by key**.

Verified on a 26.1 tenant, August 2026.

### Which one you want

| | `/odataservice/odata/{table,view}` | `/data/erp/views/v1` |
|---|---|---|
| **Protocol** | OData **v4** (`@odata.context`) | OData **v3** (`odata.metadata`) |
| **Coverage** | Every exposed table and view (thousands) | **118 curated views**, all `p21_view_*` |
| **Single row by key** | Filter and take the first result | **Native** — `view('key')` |
| **User Defined Fields** | Queryable | **Not queryable** (documented limitation) |
| **Writes / joins** | Neither | Neither |

Both are read-only, both need the same token, and neither can join — you assemble related data client-side.

> The SDK page for this endpoint claims v4, which appears to be copied from its sibling page. The wire format says v3 (`odata.metadata` at the document root, `#p21_view_oe_hdr/@Element` for a single entity). Trust the wire.

### Listing what's exposed

```http
GET {base}/data/erp/views/v1
```

Returns the 118 available views. The set is inventory- and order-centric — `p21_view_oe_hdr`, `p21_view_oe_line`, `p21_view_invoice_hdr`, `p21_view_po_hdr`, `p21_view_inv_mast`, `p21_view_inv_loc`, `p21_view_lot`, `p21_view_prod_order_hdr`, `p21_view_job_price_hdr`, the allocation-finder views, and so on. If your view is on the list, this endpoint is often the shorter path; if not, use `/odataservice/`.

### Fetching one record by key

This is the reason to know the endpoint exists:

```http
GET {base}/data/erp/views/v1/p21_view_oe_hdr('1013938')
```

```json
{"odata.metadata": "{base}/data/erp/views/v1/$metadata#p21_view_oe_hdr/@Element",
 "order_no": "1013938", "customer_id": "13162", "order_date": "..."}
```

For a view with a **compound key**, name each part — and mind the OData type suffixes, which is where this bites:

```http
GET {base}/data/erp/views/v1/p21_view_customer(company_id = '1', customer_id = 100915M)
```

The trailing **`M` marks an `Edm.Decimal`**. Omitting it, or quoting a numeric key, produces the same `incompatible types` family of errors documented under [Data Type Formatting](#data-type-formatting) — the rules there apply to both surfaces.

### Documented limitations

- **Read-only** — no create, update or delete.
- **No joins** — retrieve each set and join locally.
- **Curated views only** — the list above is all of it.
- **User Defined Fields cannot be queried.** *(Stated by Epicor for this surface. Not re-tested against `/odataservice/`, which does expose UDF columns on the tables that carry them.)*

*(Source: middleware API Reference (`{middleware}/docs/apiref.aspx`) and the SDK Data Services v1 reference guide; view count and key addressing verified live.)*

---

## OData Schema Refresh

The OData service automatically picks up changes to existing table/view schemas (e.g., column type changes). However, when **new tables or views** are added to the database, the OData service must be manually refreshed:

1. Log in to the **SOA Middleware** home page (`https://{hostname}/api/admin`) — this requires the P21 user's **Access to SOA Admin Page** application-security setting to be **Yes**; see [Authentication § Application Security settings that affect API access](00-Authentication.md#application-security-settings-that-affect-api-access)
2. Go to **Administration** from the menu
3. Find the **"Refresh OData API service"** section
4. Click **"Refresh OData API service"**

![SOA Admin - Refresh OData API service](img/administration.jpg)

> **Note:** Schema changes from P21 application upgrades are handled automatically. Manual refresh is only needed for ad-hoc database changes between upgrades.

---

## Related

- [Authentication](00-Authentication.md)
- [API Selection Guide](01-API-Selection-Guide.md)
- [Error Handling](06-Error-Handling.md)
- [Batch Processing Patterns](09-Batch-Processing-Patterns.md) - Caching and N+1 query patterns
- [examples/python/odata/](https://github.com/mrwuss/p21-api-documentation/tree/master/examples/python/odata/) - Working examples
