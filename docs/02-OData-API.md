# OData API

> **Disclaimer:** This is unofficial, community-created documentation for Epicor Prophet 21 APIs. It is not affiliated with, endorsed by, or supported by Epicor Software Corporation. All product names, trademarks, and registered trademarks are property of their respective owners. Use at your own risk.

---

## Overview

The OData API provides **read-only** access to P21 data using the OData v3 protocol. It's the fastest way to query P21 tables and views.

### Key Characteristics

- **Read-only** - Cannot create, update, or delete data
- **Standard protocol** - OData v3
- **Direct access** - Query any P21 table or view
- **Efficient** - Supports filtering, pagination, field selection
- **No session** - Simple request/response model

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
import httpx

response = httpx.get(
    f"{base_url}/odataservice/odata/table/$metadata",
    headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    timeout=300,
)
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

P21 uses `row_status_flag` to track record status. Active records have `row_status_flag = 704`:

```http
$filter=row_status_flag eq 704
```

Always include this filter when querying for active data:

```http
$filter=supplier_id eq 10050 and row_status_flag eq 704
```

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
job_price_hdr    $filter=contract_no eq 'A120-12'          → job_price_hdr_uid
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
from urllib.parse import quote

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

# Using with httpx (handles URL encoding automatically):
headers = {"Authorization": "Bearer <token>", "Content-Type": "application/json", "Accept": "application/json"}
params = {"$filter": safe_item_filter("1/2-FITTING")}
response = httpx.get(f"{base_url}/table/inv_mast", params=params, headers=headers)
response.raise_for_status()
# httpx encodes the filter value in the query string automatically
```

**C#**

```csharp
using System.Net.Http;

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

// Examples of item IDs that need escaping:
// "1/2-FITTING"     -> item_id eq '1/2-FITTING'     (/ needs URL encoding)
// "ITEM+SIZE"       -> item_id eq 'ITEM+SIZE'       (+ needs URL encoding)
// "PART #3"         -> item_id eq 'PART #3'          (# and space need URL encoding)
// "O'RING-204"      -> item_id eq 'O''RING-204'     (quote doubled)

// Using with HttpClient (URL encoding via Uri.EscapeDataString):
var filter = Uri.EscapeDataString(SafeItemFilter("1/2-FITTING"));
var url = $"{baseUrl}/table/inv_mast?$filter={filter}";
var response = await client.GetAsync(url);
// HttpClient sends the properly encoded query string
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
import httpx

# Helper modules live at examples/python/common — run from examples/python/
# or add that directory to sys.path (see examples/python/odata/01_basic_query.py)
from common.auth import get_token, get_auth_headers
from common.config import load_config

config = load_config()
token_data = get_token(config)
headers = get_auth_headers(token_data["AccessToken"])

# Query suppliers
response = httpx.get(
    f"{config.odata_url}/table/supplier",
    params={"$top": 10, "$select": "supplier_id,supplier_name"},
    headers=headers,
    verify=False  # dev/test only -- verify certificates in production
)
response.raise_for_status()

data = response.json()
for supplier in data["value"]:
    print(f"{supplier['supplier_id']}: {supplier['supplier_name']}")
```

**C#**

```csharp
using System.Net.Http;
using System.Net.Http.Headers;
using Newtonsoft.Json.Linq;

// Assumes token and baseUrl are already configured (see Authentication docs)
var client = new HttpClient();
client.DefaultRequestHeaders.Authorization =
    new AuthenticationHeaderValue("Bearer", accessToken);

// Query suppliers
var select = Uri.EscapeDataString("supplier_id,supplier_name");
var url = $"{odataUrl}/table/supplier?$top=10&$select={select}";
var response = await client.GetAsync(url);
response.EnsureSuccessStatusCode();

var json = await response.Content.ReadAsStringAsync();
var data = JObject.Parse(json);
foreach (var supplier in data["value"]!)
{
    Console.WriteLine($"{supplier["supplier_id"]}: {supplier["supplier_name"]}");
}
```

<!-- /tabs -->

### Filtered Query

<!-- tabs -->

**Python**

```python
# Get price pages for supplier
params = {
    "$filter": "supplier_id eq 10050 and row_status_flag eq 704",
    "$select": "price_page_uid,description,calculation_value1",
    "$orderby": "description"
}

response = httpx.get(
    f"{config.odata_url}/table/price_page",
    params=params,
    headers=headers,
    verify=False
)
response.raise_for_status()
```

**C#**

```csharp
// Get price pages for supplier
var filter = Uri.EscapeDataString("supplier_id eq 10050 and row_status_flag eq 704");
var select = Uri.EscapeDataString("price_page_uid,description,calculation_value1");
var orderby = Uri.EscapeDataString("description");

var url = $"{odataUrl}/table/price_page?$filter={filter}&$select={select}&$orderby={orderby}";
var response = await client.GetAsync(url);
response.EnsureSuccessStatusCode();
```

<!-- /tabs -->

### Pagination Helper

<!-- tabs -->

**Python**

```python
def get_all_records(base_url, table, filter_expr=None, page_size=5000):
    """Fetch all records with automatic pagination.

    Args:
        base_url: OData service base URL.
        table: Table name to query.
        filter_expr: Optional OData $filter expression.
        page_size: Records per request. Larger values mean fewer HTTP
            round-trips, which is usually the biggest performance factor.
            Use 5,000-25,000 for bulk/preload scenarios. Use 50-200
            when paginating for a UI. There is no documented server-side
            maximum -- 25,000 has been verified in production.
    """
    headers = {"Authorization": "Bearer <token>", "Content-Type": "application/json", "Accept": "application/json"}
    records = []
    skip = 0

    while True:
        params = {"$top": page_size, "$skip": skip, "$count": "true"}
        if filter_expr:
            params["$filter"] = filter_expr

        response = httpx.get(
            f"{base_url}/table/{table}",
            params=params,
            headers=headers,
            verify=False
        )
        response.raise_for_status()
        data = response.json()

        records.extend(data["value"])
        total = data.get("@odata.count", len(records))

        if len(records) >= total:
            break
        skip += page_size

    return records
```

**C#**

```csharp
/// <summary>
/// Fetch all records with automatic pagination.
/// </summary>
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
async Task<List<JObject>> GetAllRecordsAsync(
    HttpClient client, string baseUrl, string table,
    string? filterExpr = null, int pageSize = 5000)
{
    var records = new List<JObject>();
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
        var data = JObject.Parse(json);

        foreach (var item in data["value"]!)
            records.Add((JObject)item);

        var total = data["@odata.count"]?.Value<int>() ?? records.Count;

        if (records.Count >= total)
            break;
        skip += pageSize;
    }

    return records;
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

Fetch all related data upfront with IN clauses or multiple conditions:

<!-- tabs -->

**Python**

```python
# Get all pages first
pages = await odata.query("price_page", filter_expr="supplier_id eq 10050")
page_uids = [p['price_page_uid'] for p in pages]

# Get all links in fewer queries
for page_uid in page_uids:
    links = await odata.query("price_page_x_book",
                               filter_expr=f"price_page_uid eq {page_uid}")
```

**C#**

```csharp
// Get all pages first
var pages = await odata.QueryAsync("price_page", filterExpr: "supplier_id eq 10050");
var pageUids = pages.Select(p => p["price_page_uid"]!.ToString()).ToList();

// Get all links in fewer queries
foreach (var pageUid in pageUids)
{
    var links = await odata.QueryAsync("price_page_x_book",
                                        filterExpr: $"price_page_uid eq {pageUid}");
}
```

<!-- /tabs -->

**Solution 2: Cache lookups**

For repeated lookups (like library-to-book mapping), cache results:

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

## OData Schema Refresh

The OData service automatically picks up changes to existing table/view schemas (e.g., column type changes). However, when **new tables or views** are added to the database, the OData service must be manually refreshed:

1. Log in to the **SOA Middleware** home page (`https://{hostname}/api/admin`)
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
