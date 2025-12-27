# OData API

> **Disclaimer:** This is unofficial, community-created documentation for Epicor Prophet 21 APIs. It is not affiliated with, endorsed by, or supported by Epicor Software Corporation. All product names, trademarks, and registered trademarks are property of their respective owners. Use at your own risk.

---

## Overview

The OData API provides **read-only** access to P21 data using the standard OData v4 protocol. It's the fastest way to query P21 tables and views.

### Key Characteristics

- **Read-only** - Cannot create, update, or delete data
- **Standard protocol** - OData v4 compatible
- **Direct access** - Query any P21 table or view
- **Efficient** - Supports filtering, pagination, field selection
- **No session** - Simple request/response model

---

## Endpoints

| Endpoint | Purpose |
|----------|---------|
| `/odataservice/odata/table/{tablename}` | Query a database table |
| `/odataservice/odata/view/{viewname}` | Query a database view |

### Base URL Example

```
https://play.p21server.com/odataservice/odata/table/supplier
```

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

---

## Query Parameters

All OData query parameters are prefixed with `$`.

### $select - Choose Fields

Return only specific fields:

```
/odata/table/supplier?$select=supplier_id,supplier_name
```

### $filter - Filter Results

Filter records based on conditions:

```
/odata/table/supplier?$filter=supplier_id eq 21274
```

### $orderby - Sort Results

Sort by one or more fields:

```
/odata/table/supplier?$orderby=supplier_name asc
```

### $top - Limit Results

Return only N records:

```
/odata/table/supplier?$top=10
```

### $skip - Pagination

Skip N records (combine with $top for paging):

```
/odata/table/supplier?$skip=20&$top=10
```

### $count - Get Count

Include total count in response:

```
/odata/table/supplier?$count=true
```

---

## Filter Expressions

### Comparison Operators

| Operator | Meaning | Example |
|----------|---------|---------|
| `eq` | Equal | `$filter=supplier_id eq 21274` |
| `ne` | Not equal | `$filter=status ne 'Inactive'` |
| `gt` | Greater than | `$filter=amount gt 100` |
| `ge` | Greater or equal | `$filter=date ge 2025-01-01` |
| `lt` | Less than | `$filter=quantity lt 50` |
| `le` | Less or equal | `$filter=price le 99.99` |

### Logical Operators

| Operator | Example |
|----------|---------|
| `and` | `$filter=supplier_id eq 21274 and row_status_flag eq 704` |
| `or` | `$filter=status eq 'A' or status eq 'B'` |
| `not` | `$filter=not endswith(name,'Inc')` |

### String Functions

| Function | Example |
|----------|---------|
| `startswith` | `$filter=startswith(supplier_name,'ABC')` |
| `endswith` | `$filter=endswith(supplier_name,'Inc')` |
| `contains` | `$filter=contains(description,'filter')` |

### Null Checks

```
$filter=expiration_date eq null
$filter=notes ne null
```

---

## Common Patterns

### Active Record Filter

P21 uses `row_status_flag` to track record status. Active records have `row_status_flag = 704`:

```
$filter=row_status_flag eq 704
```

Always include this filter when querying for active data:

```
$filter=supplier_id eq 21274 and row_status_flag eq 704
```

### Non-Expired Records

To filter out expired records, compare `expiration_date` against a date value:

```
$filter=expiration_date ge 2025-01-01
```

**Warning:** The `now()` function is not supported in P21 OData. Using it will return a 404 error:

```
# DOES NOT WORK - returns 404
$filter=expiration_date ge now()

# CORRECT - use explicit date
$filter=expiration_date ge 2025-12-28
```

For date-relative queries, calculate the date in your application code:

```python
from datetime import date, timedelta

tomorrow = (date.today() + timedelta(days=1)).isoformat()
filter_expr = f"expiration_date ge {tomorrow}"
```

---

## Data Type Formatting

| Type | Format | Example |
|------|--------|---------|
| String | Single quotes | `'Active'` |
| Number | No quotes | `21274` |
| Decimal | No quotes | `99.99` |
| Date | ISO format | `2025-01-01` |
| DateTime | ISO format | `2025-01-01T00:00:00.000Z` |
| Boolean | No quotes | `true` or `false` |
| GUID | No quotes | `5BC2E4CE-0C0A-4394-A066-29B5835424DA` |

### String Escaping

Single quotes in values must be escaped by doubling:

```
$filter=supplier_name eq 'O''Brien Supply'
```

---

## Response Format

### Success Response

```json
{
    "@odata.context": "https://play.p21server.com/odataservice/odata/$metadata#supplier",
    "value": [
        {
            "supplier_id": 21274,
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

## Examples

### Basic Query

Get all suppliers:

```
GET /odataservice/odata/table/supplier
```

### Filtered Query

Get active price pages for a supplier:

```
GET /odataservice/odata/table/price_page
    ?$filter=supplier_id eq 21274 and row_status_flag eq 704
    &$select=price_page_uid,description,effective_date,expiration_date
    &$orderby=description
```

### Pagination

Get page 3 (10 records per page):

```
GET /odataservice/odata/table/supplier
    ?$skip=20
    &$top=10
    &$count=true
```

### Complex Filter

Products starting with 'FILTER' and price over $10:

```
GET /odataservice/odata/table/inv_mast
    ?$filter=startswith(item_id,'FILTER') and list_price gt 10
    &$select=item_id,item_desc,list_price
```

---

## Python Examples

### Basic Query

```python
import httpx
from scripts.common.auth import get_token, get_auth_headers
from scripts.common.config import load_config

config = load_config()
token_data = get_token(config)
headers = get_auth_headers(token_data["AccessToken"])

# Query suppliers
response = httpx.get(
    f"{config.odata_url}/table/supplier",
    params={"$top": 10, "$select": "supplier_id,supplier_name"},
    headers=headers,
    verify=False
)

data = response.json()
for supplier in data["value"]:
    print(f"{supplier['supplier_id']}: {supplier['supplier_name']}")
```

### Filtered Query

```python
# Get price pages for supplier
params = {
    "$filter": "supplier_id eq 21274 and row_status_flag eq 704",
    "$select": "price_page_uid,description,calculation_value1",
    "$orderby": "description"
}

response = httpx.get(
    f"{config.odata_url}/table/price_page",
    params=params,
    headers=headers,
    verify=False
)
```

### Pagination Helper

```python
def get_all_records(base_url, table, filter_expr=None, page_size=100):
    """Fetch all records with pagination."""
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
        data = response.json()

        records.extend(data["value"])
        total = data.get("@odata.count", len(records))

        if len(records) >= total:
            break
        skip += page_size

    return records
```

---

## Best Practices

1. **Always use $select** - Only request fields you need
2. **Add $filter early** - Filter server-side, not client-side
3. **Use $top for previews** - Don't fetch all data unnecessarily
4. **Paginate large results** - Use $skip/$top for big datasets
5. **Escape strings properly** - Double single quotes in values
6. **Handle null values** - Check for null in filters and responses

---

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| 400 Bad Request | Invalid filter syntax | Check filter expression |
| 401 Unauthorized | Invalid/expired token | Refresh token |
| 404 Not Found | Table doesn't exist, or unsupported function | Verify table name; avoid `now()` |
| 500 Server Error | Query too complex | Simplify query |

### now() Function Not Supported

The standard OData `now()` function returns 404 in P21. Use explicit date values instead:

```python
# Calculate date in code
from datetime import date, timedelta
tomorrow = (date.today() + timedelta(days=1)).isoformat()

# Use in filter
params = {"$filter": f"expiration_date ge {tomorrow}"}
```

---

## Performance Tips

- OData queries are fast (~100ms for simple queries)
- Complex filters may be slower
- Use views for pre-joined data
- Limit fields with $select
- Paginate large result sets

### Measured Performance

| Query Type | Records | Time |
|------------|---------|------|
| Simple table | 10 | ~100ms |
| Filtered query | 160 | ~115ms |
| Full table scan | 1000+ | ~500ms |

### Avoiding N+1 Query Patterns

When working with related entities (e.g., pages → books → libraries), avoid fetching related data in a loop:

```python
# BAD: N+1 queries - one query per page
for page in pages:
    book = await odata.get_book_for_page(page['uid'])  # N queries!
    library = await odata.get_library_for_book(book['uid'])  # N more!
```

**Solution 1: Batch queries**

Fetch all related data upfront with IN clauses or multiple conditions:

```python
# Get all pages first
pages = await odata.query("price_page", filter_expr="supplier_id eq 21274")
page_uids = [p['price_page_uid'] for p in pages]

# Get all links in fewer queries
for page_uid in page_uids:
    links = await odata.query("price_page_x_book",
                               filter_expr=f"price_page_uid eq {page_uid}")
```

**Solution 2: Cache lookups**

For repeated lookups (like library-to-book mapping), cache results:

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

---

## Related

- [Authentication](00-Authentication.md)
- [API Selection Guide](01-API-Selection-Guide.md)
- [Error Handling](06-Error-Handling.md)
- [scripts/odata/](https://github.com/mrwuss/p21-api-documentation/tree/master/scripts/odata/) - Working examples
