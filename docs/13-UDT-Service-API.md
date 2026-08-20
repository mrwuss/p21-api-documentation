# User Defined Tables (UDT) Service API

> **Disclaimer:** This is unofficial, community-created documentation for Epicor Prophet 21 APIs. It is not affiliated with, endorsed by, or supported by Epicor Software Corporation. All product names, trademarks, and registered trademarks are property of their respective owners. Use at your own risk.

---

> **Added April 2026** — Discovered and tested by Felipe Maurer. Additional contributions from David Sokoloski (initial P21 help docs reference), Brad Vandenbogaerde (database tables, SaaS hostname fix), John Kennedy (SQL keyword issue, working Python script), and Jon Christie (response format quirk).

---

## Overview

> **Source**: Official P21 Help Documentation (Zendesk) + community working code + actual API testing (April 2026).

P21 provides a **UDT Service API** at `/udtservice/api/udtdata/` for writing to User Defined Tables (UDTs). UDTs are custom tables created through P21's User Defined Table Maintenance window, prefixed with `udt_` in the database (the window also creates a matching `udv_` view).

The UDT Service API handles **write operations** (insert, update, delete). For **reading** UDT data, use the [OData API](02-OData-API.md) — UDT tables are queryable via Data Services like any other P21 table.

On **2026.1 and later** there is a second, differently-shaped endpoint for high-volume loads: the [Bulk Data API](#bulk-data-api-20261) (`/udtservice/api/bulkupload/{table}`), which bulk-inserts from an uploaded CSV file instead of a JSON body.

> **Creating a UDT is a UI-only operation.** There is no API path to define a new UDT — it is not among the Transaction API's services, and no corresponding Interactive API window could be opened. Use P21's **User Defined Table Maintenance** window. A newly created UDT is **not visible to OData until the schema is refreshed** (SOA Admin → *Refresh OData API service*, see [Prerequisites](#prerequisites)); the Bulk Data API, by contrast, sees it immediately.
>
> **Dropping one needs a refresh too — in the other direction.** After a UDT is dropped, OData keeps it in the schema and queries fail with `404 "Invalid object name 'dbo.{udt}'."` (a SQL error surfaced as a 404) until the schema is refreshed again. Note the difference from a table that was never exposed, which 404s with an **empty body** — the `Invalid object name` wording specifically means *"OData still expects this table, but the database no longer has it."*

### Key Characteristics

- **Write-only** — Three endpoints for insert, update, and delete
- **Stateless** — No session management required
- **Column-based payloads** — Data is sent as column name/value pairs
- **Condition-based targeting** — Updates and deletes identify rows via conditions (typically `row_uid`)
- **Shared auth** — Uses the same Bearer token as all other P21 APIs

### When to Use

- Inserting custom data into UDT tables from external systems
- Updating or deleting UDT records programmatically
- B2B integrations that write to custom P21 tables
- Automating data entry for custom workflows built on UDTs

### Limitations

- **Write only** — No read/query endpoints; use OData for reads
- **No endpoint-based schema discovery** — no service endpoint lists tables or columns, but the catalog is readable over OData: `master_udt_definition` (one row per UDT: `udt_table_name`, `udt_view_name`) and `master_udt_definition_column` (per-column name, `datatype_cd`, `length`, `precision`/`scale`, `nullable_flag`, `df_value`). Verified on 2026.1.
- **SQL keyword filtering** — Values containing SQL keywords (e.g., "drop", "insert") may be rejected even in legitimate data
- **UID-based conditions only** — Updates and deletes require a literal **`row_uid` column**, which UDTs created on 2026.1 **do not have** (their PK is `udt_{tablename}_uid`). On such tables update always 400s and delete silently deletes nothing — see the [warning under Update](#update)
- **Bulk upload is insert-only** — the [Bulk Data API](#bulk-data-api-20261) has no update or delete counterpart

---

## Base URL

```http
https://{hostname}/udtservice/api/udtdata/
```

Example: `https://play.p21server.com/udtservice/api/udtdata/`

> **SaaS environments:** The hostname may require `-api` in the FQDN (e.g., `play-api.p21server.com` instead of `play.p21server.com`). Credit: Brad Vandenbogaerde.

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/udtservice/api/udtdata/insertudtdata` | Insert one or more rows |
| `PUT` | `/udtservice/api/udtdata/updateudtdata` | Update rows by condition |
| `DELETE` | `/udtservice/api/udtdata/deleteudtdata` | Delete rows by condition |
| `POST` | `/udtservice/api/bulkupload/{table}` | **2026.1+** — bulk-insert rows from a CSV file ([details](#bulk-data-api-20261)) |

---

## Authentication

The UDT Service API uses the same Bearer token authentication as all other P21 APIs. Both **consumer key** and **user/password** authentication work. API scope does not affect access.

See [Authentication](00-Authentication.md) for token generation.

### Required Headers

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
Content-Type: application/json
```

---

## Payload Structure

All three endpoints use a common JSON structure with `table`, `rows`, `columns`, and `conditions` fields.

### Core Structure

```json
{
  "table": "udt_table_name",
  "rows": [
    {
      "columns": [
        {"name": "column_name", "value": "column_value"},
        {"name": "another_column", "value": "another_value"}
      ],
      "conditions": []
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `table` | string | UDT table name (e.g., `udt_custom_orders`) |
| `rows` | array | Array of row objects to process |
| `rows[].columns` | array | Column name/value pairs for data |
| `rows[].conditions` | array | Column name/value pairs for WHERE clause (update/delete) |

### Insert vs Update vs Delete

| Operation | `columns` | `conditions` |
|-----------|-----------|-------------|
| **Insert** | Required (data to write) | Empty array `[]` |
| **Update** | Required (new values) | Required (identifies target rows, typically `row_uid`) |
| **Delete** | Empty array `[]` | Required (identifies target rows, typically `row_uid`) |

---

## Insert

Insert one or more rows into a UDT table. All non-nullable columns must be included in the payload. Columns not included will be set to NULL.

### Request

```http
POST /udtservice/api/udtdata/insertudtdata
Authorization: Bearer <ACCESS_TOKEN>
Content-Type: application/json
Accept: application/json
```

### Payload

```json
{
  "table": "udt_custom_orders",
  "rows": [
    {
      "columns": [
        {"name": "order_ref", "value": "ORD-2026-001"},
        {"name": "customer_name", "value": "ABC Supply Company"},
        {"name": "order_total", "value": "1250.00"},
        {"name": "status", "value": "pending"}
      ],
      "conditions": []
    }
  ]
}
```

### Multi-Row Insert

Insert multiple rows in a single request by adding objects to the `rows` array:

```json
{
  "table": "udt_custom_orders",
  "rows": [
    {
      "columns": [
        {"name": "order_ref", "value": "ORD-2026-001"},
        {"name": "customer_name", "value": "ABC Supply Company"},
        {"name": "order_total", "value": "1250.00"},
        {"name": "status", "value": "pending"}
      ],
      "conditions": []
    },
    {
      "columns": [
        {"name": "order_ref", "value": "ORD-2026-002"},
        {"name": "customer_name", "value": "XYZ Manufacturing"},
        {"name": "order_total", "value": "875.50"},
        {"name": "status", "value": "pending"}
      ],
      "conditions": []
    }
  ]
}
```

### Example

<!-- tabs -->

**Python:**
```python
"""Insert a row into a UDT table via the UDT Service API."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
TABLE = "udt_custom_orders"               # UDT table name
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

    payload = {
        "table": TABLE,
        "rows": [
            {
                "columns": [
                    {"name": "order_ref", "value": "ORD-2026-001"},
                    {"name": "customer_name", "value": "ABC Supply Company"},
                    {"name": "order_total", "value": "1250.00"},
                    {"name": "status", "value": "pending"},
                ],
                "conditions": [],
            }
        ],
    }

    resp = client.post(
        f"{BASE_URL}/udtservice/api/udtdata/insertudtdata",
        json=payload,
        headers=headers,
    )
    result = resp.json()

    if result["errorNo"] == 0:
        print(f"Insert: {result['errorMessage']}")
    else:
        print(f"Error {result['errorNo']}: {result['errorMessage']}")

    # Read-back — errorNo == 0 does not prove the row landed; confirm via OData.
    check = client.get(
        f"{BASE_URL}/odataservice/odata/table/{TABLE}",
        params={"$filter": "order_ref eq 'ORD-2026-001'"},
        headers=headers,
    )
    check.raise_for_status()
    rows = check.json().get("value", [])
    print(f"Read-back: {len(rows)} row(s) found for order_ref=ORD-2026-001")
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
const string Table = "udt_custom_orders";               // UDT table name
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

// Insert a row
var payload = new
{
    table = Table,
    rows = new object[]
    {
        new
        {
            columns = new object[]
            {
                new { name = "order_ref", value = "ORD-2026-001" },
                new { name = "customer_name", value = "ABC Supply Company" },
                new { name = "order_total", value = "1250.00" },
                new { name = "status", value = "pending" },
            },
            conditions = Array.Empty<object>(),
        },
    },
};

var resp = await client.PostAsync(
    $"{BaseUrl}/udtservice/api/udtdata/insertudtdata",
    new StringContent(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json"));
var result = JsonDocument.Parse(await resp.Content.ReadAsStringAsync()).RootElement;

if (result.GetProperty("errorNo").GetInt32() == 0)
{
    Console.WriteLine($"Insert: {result.GetProperty("errorMessage").GetString()}");
}
else
{
    Console.WriteLine(
        $"Error {result.GetProperty("errorNo").GetInt32()}: {result.GetProperty("errorMessage").GetString()}");
}

// Read-back — errorNo == 0 does not prove the row landed; confirm via OData.
var checkResp = await client.GetAsync(
    $"{BaseUrl}/odataservice/odata/table/{Table}?$filter=order_ref eq 'ORD-2026-001'");
checkResp.EnsureSuccessStatusCode();
var checkResult = JsonDocument.Parse(await checkResp.Content.ReadAsStringAsync()).RootElement;
Console.WriteLine(
    $"Read-back: {checkResult.GetProperty("value").GetArrayLength()} row(s) found for order_ref=ORD-2026-001");

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

## Update

Update existing rows in a UDT table. Use `conditions` to identify which rows to update (typically by `row_uid`) and `columns` to specify the new values.

> ⚠️ **Update and Delete require a literal `row_uid` column — and UDTs created on 2026.1 don't have one.** Both endpoints are hard-wired to a column named exactly `row_uid`. P21's **User Defined Table Maintenance** window on 2026.1 names the primary key **`udt_{tablename}_uid`** (e.g. `udt_custom_orders_uid`) and creates **no** `row_uid`, which makes both endpoints unable to target any row on such a table:
>
> - **Update** returns `400 {"error":["Invalid Row Uid!"]}` for **every** condition — `row_uid`, the real PK name, or any other column; casing and string-vs-int variants all fail identically.
> - **Delete** is worse: it returns **HTTP 200 `{"errorNo": 0, "errorMessage": "[0] rows deleted from [table] table successfully!"}`** and deletes nothing. The word *"successfully"* with `errorNo: 0` reads as a clean delete — **only the `[0]` row count reveals the no-op.**
>
> **The maintenance window's "Row ID" is not the API's `row_uid`.** P21's generated UDT maintenance windows expose a searchable **Row ID** used to recall, edit and delete a row — but it sits over the `udt_{tablename}_uid` primary key, and the service accepts only a column named literally `row_uid`. The identifier exists; the two surfaces disagree on its name. See [Breaking Changes entry 7](14-Breaking-Changes.md#7-udt-service-updatedelete-cannot-target-rows-in-a-udt-created-on-20261). For bulk row entry without the API, those same windows support **mass update**.
>
> **Before relying on update/delete, confirm your UDT actually has a `row_uid` column** (`GET /odataservice/odata/table/{udt}?$select=row_uid` — a 404 saying *"Could not find a property named 'row_uid'"* means it doesn't). If it doesn't, these endpoints cannot reach your data; use P21's maintenance UI or direct SQL. **Always check the row count in `errorMessage`** rather than trusting `errorNo: 0`.
>
> The `row_uid` convention is well-attested by the contributors who documented these endpoints, so tables that predate 2026.1 evidently do have the column. We could not A/B this against a pre-2026.1 tenant — verified July 2026 on one 2026.1-created UDT.

### Request

```http
PUT /udtservice/api/udtdata/updateudtdata
Authorization: Bearer <ACCESS_TOKEN>
Content-Type: application/json
Accept: application/json
```

### Payload

```json
{
  "table": "udt_custom_orders",
  "rows": [
    {
      "columns": [
        {"name": "status", "value": "completed"},
        {"name": "order_total", "value": "1300.00"}
      ],
      "conditions": [
        {"name": "row_uid", "value": "12345"}
      ]
    }
  ]
}
```

### Example

> The `ROW_UID` constant below must be a value from the table's real `row_uid` column — see the note under [Limitations](#limitations): UDTs created on 2026.1 have no such column, and this call always 400s against them.

<!-- tabs -->

**Python:**
```python
"""Update a UDT row identified by row_uid via the UDT Service API."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
TABLE = "udt_custom_orders"               # UDT table name
ROW_UID = "12345"                         # row_uid of the record to update
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

    payload = {
        "table": TABLE,
        "rows": [
            {
                "columns": [
                    {"name": "status", "value": "completed"},
                    {"name": "order_total", "value": "1300.00"},
                ],
                "conditions": [
                    {"name": "row_uid", "value": ROW_UID},
                ],
            }
        ],
    }

    resp = client.put(
        f"{BASE_URL}/udtservice/api/udtdata/updateudtdata",
        json=payload,
        headers=headers,
    )
    result = resp.json()

    if result["errorNo"] == 0:
        print(f"Update: {result['errorMessage']}")
    else:
        print(f"Error {result['errorNo']}: {result['errorMessage']}")

    # Read-back — confirm the new values actually landed via OData.
    check = client.get(
        f"{BASE_URL}/odataservice/odata/table/{TABLE}",
        params={"$filter": f"row_uid eq {ROW_UID}"},
        headers=headers,
    )
    check.raise_for_status()
    rows = check.json().get("value", [])
    if rows:
        print(f"Read-back: status={rows[0].get('status')}, order_total={rows[0].get('order_total')}")
    else:
        print("Read-back: row_uid not found")
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
const string Table = "udt_custom_orders";               // UDT table name
const string RowUid = "12345";                          // row_uid of the record to update
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

var payload = new
{
    table = Table,
    rows = new object[]
    {
        new
        {
            columns = new object[]
            {
                new { name = "status", value = "completed" },
                new { name = "order_total", value = "1300.00" },
            },
            conditions = new object[]
            {
                new { name = "row_uid", value = RowUid },
            },
        },
    },
};

var resp = await client.PutAsync(
    $"{BaseUrl}/udtservice/api/udtdata/updateudtdata",
    new StringContent(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json"));
var result = JsonDocument.Parse(await resp.Content.ReadAsStringAsync()).RootElement;

if (result.GetProperty("errorNo").GetInt32() == 0)
{
    Console.WriteLine($"Update: {result.GetProperty("errorMessage").GetString()}");
}
else
{
    Console.WriteLine(
        $"Error {result.GetProperty("errorNo").GetInt32()}: {result.GetProperty("errorMessage").GetString()}");
}

// Read-back — confirm the new values actually landed via OData.
var checkResp = await client.GetAsync(
    $"{BaseUrl}/odataservice/odata/table/{Table}?$filter=row_uid eq {RowUid}");
checkResp.EnsureSuccessStatusCode();
var checkResult = JsonDocument.Parse(await checkResp.Content.ReadAsStringAsync()).RootElement;
var checkRows = checkResult.GetProperty("value");
if (checkRows.GetArrayLength() > 0)
{
    var row = checkRows[0];
    Console.WriteLine(
        $"Read-back: status={row.GetProperty("status").GetString()}, order_total={row.GetProperty("order_total").GetString()}");
}
else
{
    Console.WriteLine("Read-back: row_uid not found");
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

> **Note:** To get the `row_uid` for existing records, query the UDT table via OData first (see [Reading UDT Data](#reading-udt-data-odata)).

---

## Delete

Delete rows from a UDT table. Use `conditions` to identify which rows to remove (typically by `row_uid`).

> ⚠️ **Delete reports success even when it deletes nothing** — and on a 2026.1-created UDT (no `row_uid` column) it deletes nothing at all. See the [warning under Update](#update); check the `[N]` row count in `errorMessage`, never `errorNo` alone.

> **Payload note — `conditions` placement differs from Update.** Delete reads `conditions` from the **top level** of the payload; nesting it inside `rows[]` (the shape Update uses, and the shape shown below) returns `400 {"error":["Conditions cannot be blank or none!"]}` on 2026.1. Both forms are documented here because the nested form is what the endpoint's original contributors used successfully — if the documented payload below returns that error, move `conditions` up a level:
>
> **Re-verification status (2026-08-11):** this one could **not** be re-tested. The test tenant has no user-defined tables at all, and creating a UDT is UI-only — there is no API path to make one (a UI-only operation — see the note under [Overview](#overview)). Both shapes therefore stand on the original reports rather than a fresh run; if you have a UDT to hand, try the top-level form first and treat the nested form as the fallback.
>
> ```json
> {"table": "udt_custom_orders", "conditions": [{"name": "row_uid", "value": "12345"}]}
> ```

### Request

```http
DELETE /udtservice/api/udtdata/deleteudtdata
Authorization: Bearer <ACCESS_TOKEN>
Content-Type: application/json
Accept: application/json
```

### Payload

```json
{
  "table": "udt_custom_orders",
  "rows": [
    {
      "columns": [],
      "conditions": [
        {"name": "row_uid", "value": "12345"}
      ]
    }
  ]
}
```

### Example

> `conditions` is sent at the **top level** of the payload, not nested inside `rows[]` — see the payload note above. This example intentionally differs from the `### Payload` block for that reason.

<!-- tabs -->

**Python:**
```python
"""Delete a UDT row identified by row_uid via the UDT Service API."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
TABLE = "udt_custom_orders"               # UDT table name
ROW_UID = "12345"                         # row_uid of the record to delete
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

    # conditions is TOP-LEVEL for delete, not nested in rows[] — see warning above.
    payload = {
        "table": TABLE,
        "conditions": [
            {"name": "row_uid", "value": ROW_UID},
        ],
    }

    resp = client.request(
        "DELETE",
        f"{BASE_URL}/udtservice/api/udtdata/deleteudtdata",
        json=payload,
        headers=headers,
    )
    result = resp.json()

    # Check the row count in errorMessage — errorNo == 0 lies when 0 rows were deleted.
    if result["errorNo"] == 0:
        print(f"Delete: {result['errorMessage']}")
    else:
        print(f"Error {result['errorNo']}: {result['errorMessage']}")

    # Read-back — confirm the row is actually gone via OData.
    check = client.get(
        f"{BASE_URL}/odataservice/odata/table/{TABLE}",
        params={"$filter": f"row_uid eq {ROW_UID}"},
        headers=headers,
    )
    check.raise_for_status()
    rows = check.json().get("value", [])
    print(f"Read-back: {len(rows)} row(s) remain with row_uid={ROW_UID}")
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
const string Table = "udt_custom_orders";               // UDT table name
const string RowUid = "12345";                          // row_uid of the record to delete
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

// conditions is TOP-LEVEL for delete, not nested in rows[] — see warning above.
var payload = new
{
    table = Table,
    conditions = new object[]
    {
        new { name = "row_uid", value = RowUid },
    },
};

var request = new HttpRequestMessage(
    HttpMethod.Delete, $"{BaseUrl}/udtservice/api/udtdata/deleteudtdata")
{
    Content = new StringContent(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json"),
};
var resp = await client.SendAsync(request);
var result = JsonDocument.Parse(await resp.Content.ReadAsStringAsync()).RootElement;

// Check the row count in errorMessage — errorNo == 0 lies when 0 rows were deleted.
if (result.GetProperty("errorNo").GetInt32() == 0)
{
    Console.WriteLine($"Delete: {result.GetProperty("errorMessage").GetString()}");
}
else
{
    Console.WriteLine(
        $"Error {result.GetProperty("errorNo").GetInt32()}: {result.GetProperty("errorMessage").GetString()}");
}

// Read-back — confirm the row is actually gone via OData.
var checkResp = await client.GetAsync(
    $"{BaseUrl}/odataservice/odata/table/{Table}?$filter=row_uid eq {RowUid}");
checkResp.EnsureSuccessStatusCode();
var checkResult = JsonDocument.Parse(await checkResp.Content.ReadAsStringAsync()).RootElement;
Console.WriteLine(
    $"Read-back: {checkResult.GetProperty("value").GetArrayLength()} row(s) remain with row_uid={RowUid}");

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

> **Note:** The `DELETE` HTTP method with a JSON body is non-standard. Some HTTP clients require using `request()` or `SendAsync()` with an explicit `HttpRequestMessage` to include a body on DELETE requests.

---

## Bulk Data API (2026.1+)

> **Source**: Live verification against a 2026.1 tenant (July 2026). Epicor's *Prophet 21 Release 2026.1 Release Guide* announces this as a core enhancement — *"Bulk Data API for User-Defined Tables – A new API enables high-volume data uploads into user-defined tables"* — but names no endpoint, and the in-middleware SDK reference (`/docs/p21sdk`) does not document it. Everything below was established by probing the live service and confirming every result with an OData read-back.

`POST /udtservice/api/bulkupload/{table}` bulk-inserts rows into a UDT from an uploaded **CSV file**. It is a different shape from the JSON `udtdata` endpoints above: a `multipart/form-data` file upload, not a JSON body.

```http
POST /udtservice/api/bulkupload/udt_custom_orders HTTP/1.1
Authorization: Bearer <ACCESS_TOKEN>
Accept: application/json
Content-Type: multipart/form-data; boundary=----X

------X
Content-Disposition: form-data; name="file"; filename="orders.csv"
Content-Type: text/csv

order_code,description,qty,order_date
A1,First order,1.5,2026-01-15
------X--
```

Success returns HTTP 200:

```json
{"isSuccessful": true, "message": "Data uploaded successfully to udt_custom_orders."}
```

### Contract

| Aspect | Verified behavior |
|--------|-------------------|
| **Method** | `POST` only — `GET`/`PUT`/`OPTIONS` return 405 with `Allow: POST` |
| **URL segment** | The **table name**, not an action — `/bulkupload/udt_custom_orders` |
| **Body** | `multipart/form-data`. Any other content type returns **415** with an empty body |
| **Form field name** | Must be **`file`** — any other name returns a 400 validation error naming `file` as required |
| **File format** | **Comma-delimited CSV with a header row.** Tab-delimited is rejected |
| **Header names** | Must match the UDT columns **exactly — case-sensitive, no surrounding whitespace** |
| **Column subset** | Allowed — omitted columns are written as `NULL` |
| **Column order** | Irrelevant — mapped by header name |
| **Quoting** | Standard CSV quoting works (embedded commas and quotes round-trip) |
| **Filename / extension / content-type** | Ignored — `.txt`, no extension, and `application/octet-stream` all upload fine |
| **Atomicity** | **All-or-nothing** — one bad row rejects the whole file and inserts nothing |
| **Duplicates** | **Insert-only, no upsert** — uploading the same key twice creates two rows |
| **Volume** | 1,000 rows in a single call verified (no cap established) |
| **Update / delete** | No counterpart — `/bulkupdate` and `/bulkdelete` are 404 |
| **Target table** | Must be a registered UDT. Ordinary P21 tables (`supplier`, `inv_mast`, `po_hdr`) return `"Incompatible table for bulk insert: {table}"` |

### Gotchas

> ⚠️ **A CSV without a header row reports success and inserts nothing.** The service treats the first line as the header, finds no data rows beneath it, and returns HTTP 200 `{"isSuccessful": true}` having written **zero rows**. A migration or nightly job that omits the header logs a clean success for every run while loading nothing. **Always verify the row count with an OData read-back** — the response body cannot tell you how many rows landed (it reports no count at all).

> ⚠️ **Values are silently rounded to the column's scale.** Into a `decimal(2,1)` column, `1.66` stores as `1.7`, `1.64` as `1.6`, and `1.99` as `2.0` — HTTP 200, no warning. Scale overflow is silent; only *precision* overflow errors (`99.9` into `decimal(2,1)` returns 400). Match your file's precision to the column definition rather than relying on the API to flag it.

**`NULL` can only be expressed by omitting the column.** A blank value (`A1,`) and the literal text `NULL` both return 400 (`"The given value '' ... cannot be converted to type decimal"`) — even when the column is nullable. Consequence: **one file cannot mix rows that have a value with rows that don't** for the same column; split them into separate uploads by column-presence.

**Rows are not attributed to the API user.** The auto-generated audit columns default to `suser_sname()` / `GETDATE()`, so `created_by` records the **middleware's SQL login** (e.g. `Admin`), not the authenticated caller. The file *can* set `created_by` explicitly and the supplied value is stored as-is — these columns are writable, so don't treat them as a trustworthy audit trail. The identity PK (`udt_{name}_uid`) is the exception: a value supplied in the file is silently ignored and the server-assigned identity wins.

**Errors identify the offending column, not the row.** Failures return a bare JSON string with the column position and name — e.g. `"The given value 'abc' of type String from the data source cannot be converted to type decimal for Column 3 [qty]."` or `"The given ColumnName 'not_a_column' does not match up with any column in data source."`. There is no row number, so on a large file you get no direct pointer to which record failed.

### Example

<!-- tabs -->

**Python:**
```python
"""Bulk-insert rows into a UDT from an in-memory CSV, then verify with a read-back."""
import csv
import io
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
TABLE = "udt_custom_orders"               # UDT table name
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


def bulk_upload(client: httpx.Client, table: str, rows: list[dict]) -> dict:
    """Bulk-insert rows into a UDT from an in-memory CSV.

    The header row is mandatory — without it the service returns success and
    inserts nothing. Column names are case-sensitive and must match the UDT.
    """
    if not rows:
        raise ValueError("no rows to upload")

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(rows[0]))
    writer.writeheader()          # REQUIRED — omitting it silently inserts 0 rows
    writer.writerows(rows)

    response = client.post(
        f"{BASE_URL}/udtservice/api/bulkupload/{table}",
        files={"file": ("upload.csv", buf.getvalue().encode(), "text/csv")},
        timeout=300,
    )
    response.raise_for_status()
    return response.json()


def row_count(client: httpx.Client, table: str) -> int:
    """Read-back — the upload response carries no row count."""
    response = client.get(
        f"{BASE_URL}/odataservice/odata/table/{table}",
        params={"$count": "true", "$top": "0"},
        timeout=120,
    )
    response.raise_for_status()
    return response.json().get("@odata.count", 0)


with httpx.Client(verify=VERIFY_SSL, timeout=120, follow_redirects=True) as client:
    token = get_token(client)
    client.headers = httpx.Headers(
        {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    )

    # Usage — count before and after, because "isSuccessful" does not mean "inserted"
    before = row_count(client, TABLE)
    result = bulk_upload(client, TABLE, [
        {"order_code": "A1", "description": "First order", "qty": "1.5"},
        {"order_code": "A2", "description": "Second order", "qty": "2.5"},
    ])
    after = row_count(client, TABLE)
    print(f"{result['message']} — rows inserted: {after - before}")
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
const string Table = "udt_custom_orders";               // UDT table name
// ---------------------------------------------------------------------------

var handler = new HttpClientHandler
{
    // Test tenants often present a self-signed cert. Delete this line in production.
    ServerCertificateCustomValidationCallback =
        HttpClientHandler.DangerousAcceptAnyServerCertificateValidator,
};
using var client = new HttpClient(handler) { Timeout = TimeSpan.FromMinutes(5) };
client.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));

var token = await GetTokenAsync(client);
client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);

var rows = new List<Dictionary<string, string>>
{
    new() { ["order_code"] = "A1", ["description"] = "First order", ["qty"] = "1.5" },
    new() { ["order_code"] = "A2", ["description"] = "Second order", ["qty"] = "2.5" },
};

// Usage — count before and after, because "isSuccessful" does not mean "inserted"
var before = await RowCountAsync(client, Table);
var message = await BulkUploadAsync(client, Table, rows);
var after = await RowCountAsync(client, Table);
Console.WriteLine($"{message} — rows inserted: {after - before}");

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

// Bulk-inserts rows into a UDT from an in-memory CSV, built by hand (no CSV package —
// this repo's docs examples run with zero package installs). The header row is
// mandatory — without it the service returns success and inserts nothing. Column
// names are case-sensitive and must match the UDT.
static async Task<string> BulkUploadAsync(
    HttpClient client, string table, IReadOnlyList<Dictionary<string, string>> rows)
{
    if (rows.Count == 0) throw new ArgumentException("no rows to upload", nameof(rows));

    var columns = rows[0].Keys.ToList();
    var csv = new StringBuilder();
    csv.AppendLine(string.Join(",", columns));   // REQUIRED — omitting it silently inserts 0 rows
    foreach (var row in rows)
        csv.AppendLine(string.Join(",", columns.Select(c => row[c])));

    using var content = new MultipartFormDataContent();
    var file = new ByteArrayContent(Encoding.UTF8.GetBytes(csv.ToString()));
    file.Headers.ContentType = new MediaTypeHeaderValue("text/csv");
    // The form field MUST be named "file" — any other name is rejected.
    content.Add(file, "file", "upload.csv");

    var response = await client.PostAsync($"{BaseUrl}/udtservice/api/bulkupload/{table}", content);
    response.EnsureSuccessStatusCode();
    return await response.Content.ReadAsStringAsync();
}

// Read-back — the upload response carries no row count.
static async Task<int> RowCountAsync(HttpClient client, string table)
{
    var response = await client.GetAsync(
        $"{BaseUrl}/odataservice/odata/table/{table}?$count=true&$top=0");
    response.EnsureSuccessStatusCode();
    var json = JsonDocument.Parse(await response.Content.ReadAsStringAsync()).RootElement;
    return json.TryGetProperty("@odata.count", out var count) ? count.GetInt32() : 0;
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

> **Verification scope:** established against one purpose-built UDT (`char`, `decimal`, and `date` columns) on a 2026.1 test tenant, with every claim confirmed by an OData read-back. Behavior against other column types (e.g. `bit`, `text`) and files larger than 1,000 rows is untested. Because 2026.1 is the first release to ship this endpoint and no 25.2 tenant remained available, the "new in 2026.1" attribution rests on Epicor's release guide rather than an A/B test.

---

## Reading UDT Data (OData)

> **Source**: Official P21 Help Documentation + community working code.

The UDT Service API does not provide read endpoints. To query UDT data, use the [OData API](02-OData-API.md) with the `udt_` table prefix via Data Services.

### Prerequisites

UDT tables must be exposed through the Data Services API. If a UDT table is not visible:

1. Open **SOA Admin** (`https://{hostname}/docs/admin.aspx`)
2. Navigate to **Administration > Refresh OData API service**
3. Verify the table appears in the OData metadata

### Querying UDTs via OData

```http
GET /odataservice/odata/table/udt_custom_orders?$filter=status eq 'pending'
Authorization: Bearer <ACCESS_TOKEN>
Accept: application/json
```

<!-- tabs -->

**Python:**
```python
"""Query UDT data via OData — the UDT Service API has no read endpoints of its own."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
TABLE = "udt_custom_orders"               # UDT table name
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
    }

    resp = client.get(
        f"{BASE_URL}/odataservice/odata/table/{TABLE}",
        params={"$filter": "status eq 'pending'"},
        headers=headers,
    )
    resp.raise_for_status()
    data = resp.json()

    for row in data.get("value", []):
        print(f"Order: {row['order_ref']}, Total: {row['order_total']}")
        # row_uid is available for subsequent update/delete operations
        print(f"  row_uid: {row['row_uid']}")
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
const string Table = "udt_custom_orders";               // UDT table name
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

// Query UDT data via OData
var resp = await client.GetAsync(
    $"{BaseUrl}/odataservice/odata/table/{Table}?$filter=status eq 'pending'");
resp.EnsureSuccessStatusCode();
var data = JsonDocument.Parse(await resp.Content.ReadAsStringAsync()).RootElement;

foreach (var row in data.GetProperty("value").EnumerateArray())
{
    Console.WriteLine($"Order: {row.GetProperty("order_ref")}, Total: {row.GetProperty("order_total")}");
    // row_uid is available for subsequent update/delete operations
    Console.WriteLine($"  row_uid: {row.GetProperty("row_uid")}");
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

> **Tip:** The `row_uid` column returned by OData is the primary identifier used in `conditions` for update and delete operations.

---

## Response Format

All three endpoints return the same response structure.

### Success Response

```json
{
  "id": 0,
  "errorNo": 0,
  "errorMessage": "[1] row inserted in [udt_custom_orders] table successfully..!",
  "documentNo": null,
  "sqlErrorNumber": 0,
  "sqlErrorSeverity": 0,
  "sqlErrorState": 0,
  "sqlObjectName": null,
  "sqlErrorLineNo": 0,
  "sqlErrorMessage": null
}
```

### Error Response (Table Not Found)

```json
{
  "id": 0,
  "errorNo": 4001,
  "errorMessage": "Table udt_nonexistent not available!",
  "documentNo": null,
  "sqlErrorNumber": 0,
  "sqlErrorSeverity": 0,
  "sqlErrorState": 0,
  "sqlObjectName": null,
  "sqlErrorLineNo": 0,
  "sqlErrorMessage": null
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Always 0 |
| `errorNo` | int | **0 = success**, non-zero = error |
| `errorMessage` | string | Result message (success AND error messages use this field) |
| `documentNo` | string/null | Document number if applicable |
| `sqlErrorNumber` | int | SQL Server error number (0 if no SQL error) |
| `sqlErrorSeverity` | int | SQL Server error severity |
| `sqlErrorState` | int | SQL Server error state |
| `sqlObjectName` | string/null | SQL object that caused the error |
| `sqlErrorLineNo` | int | SQL line number of error |
| `sqlErrorMessage` | string/null | Raw SQL error message |

### Checking for Success

Always check `errorNo`, not `errorMessage`. Success messages are returned in the `errorMessage` field, which is counterintuitive.

<!-- tabs -->

**Python:**
```python
"""Check errorNo (not errorMessage) to tell a UDT Service API success from a failure."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
TABLE = "udt_custom_orders"               # UDT table name
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

    payload = {
        "table": TABLE,
        "rows": [
            {
                "columns": [
                    {"name": "order_ref", "value": "ORD-2026-002"},
                    {"name": "customer_name", "value": "XYZ Manufacturing"},
                    {"name": "order_total", "value": "875.50"},
                    {"name": "status", "value": "pending"},
                ],
                "conditions": [],
            }
        ],
    }

    resp = client.post(
        f"{BASE_URL}/udtservice/api/udtdata/insertudtdata",
        json=payload,
        headers=headers,
    )
    result = resp.json()

    if result["errorNo"] == 0:
        # Success — errorMessage contains the success description
        print(f"OK: {result['errorMessage']}")
    else:
        # Error — errorNo is non-zero
        print(f"Failed (code {result['errorNo']}): {result['errorMessage']}")
        if result.get("sqlErrorMessage"):
            print(f"SQL Error: {result['sqlErrorMessage']}")
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
const string Table = "udt_custom_orders";               // UDT table name
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

var payload = new
{
    table = Table,
    rows = new object[]
    {
        new
        {
            columns = new object[]
            {
                new { name = "order_ref", value = "ORD-2026-002" },
                new { name = "customer_name", value = "XYZ Manufacturing" },
                new { name = "order_total", value = "875.50" },
                new { name = "status", value = "pending" },
            },
            conditions = Array.Empty<object>(),
        },
    },
};

var resp = await client.PostAsync(
    $"{BaseUrl}/udtservice/api/udtdata/insertudtdata",
    new StringContent(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json"));
var result = JsonDocument.Parse(await resp.Content.ReadAsStringAsync()).RootElement;

if (result.GetProperty("errorNo").GetInt32() == 0)
{
    // Success — errorMessage contains the success description
    Console.WriteLine($"OK: {result.GetProperty("errorMessage").GetString()}");
}
else
{
    // Error — errorNo is non-zero
    Console.WriteLine(
        $"Failed (code {result.GetProperty("errorNo").GetInt32()}): {result.GetProperty("errorMessage").GetString()}");
    if (result.TryGetProperty("sqlErrorMessage", out var sqlErr) && sqlErr.ValueKind == JsonValueKind.String)
    {
        Console.WriteLine($"SQL Error: {sqlErr.GetString()}");
    }
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

---

## Known Issues

> **Source**: Community-reported issues, verified via actual API testing (April 2026). Tested on P21 version 25.2. Applies to all `/udtservice/api/udtdata/` endpoints.

### 1. Success Messages in errorMessage Field

| | |
|---|---|
| **Discovery** | April 2026 (community-reported) |
| **Affected versions** | All known versions with UDT support |
| **Tested endpoints** | `insertudtdata`, `updateudtdata`, `deleteudtdata` |
| **Workaround** | Check `errorNo == 0` for success, not the field name |

The API returns success messages in the `errorMessage` field (e.g., `"[1] row inserted in [udt_custom_orders] table successfully..!"`). Always check `errorNo == 0` for success, not the field name. Credit: Jon Christie.

### 2. SQL Keyword False Positives

| | |
|---|---|
| **Discovery** | April 2026 (community-reported) |
| **Affected versions** | All known versions with UDT support |
| **Tested endpoints** | `insertudtdata`, `updateudtdata` |
| **Workaround** | No known workaround — abbreviate or encode values |

Values containing SQL keywords like `"drop"`, `"insert"`, `"delete"`, `"update"`, or `"select"` may be blocked by the API's SQL injection filter, even when they appear in legitimate data. For example, a product description containing `"drop tube"` or `"insert fitting"` could be rejected. Credit: John Kennedy.

**Quote characters are part of the same filter, and the behavior is version-dependent.** The protection is reported to be a simplistic string replacement rather than real parameterization, which also catches **quote characters** (`'` and `"`) inside otherwise ordinary values. The everyday casualty is dimensional data: `6" hose`, `1/2" fitting`, `3' section` — feet-and-inches notation is exactly the punctuation the filter objects to. A community session in 2026 reported that Epicor has since relaxed this logic to accept more characters, so **which characters your version rejects is not something to take on faith from any document, including this one**: if your UDT values can contain quotes, insert one row carrying the real punctuation on your own version and read it back before building on it. Testing published on the community forum was done on ~25.1 and may not describe current behavior. *(Community session, Felipe Maurer, 2026.)*

### 3. Update/Delete Only Accept UIDs as Conditions

| | |
|---|---|
| **Discovery** | April 2026 (community-reported) |
| **Affected versions** | All known versions with UDT support |
| **Tested endpoints** | `updateudtdata`, `deleteudtdata` |
| **Workaround** | Query via OData first to obtain `row_uid` |

The `conditions` array for update and delete operations only reliably works with `row_uid`. Attempting to use other column values as conditions may produce unexpected results or errors. Always query via OData first to obtain the `row_uid` of the target row.

### 4. All Non-Nullable Columns Required on Insert

| | |
|---|---|
| **Discovery** | April 2026 (from official documentation) |
| **Affected versions** | All known versions with UDT support |
| **Tested endpoints** | `insertudtdata` |
| **Workaround** | Include all non-nullable columns in the payload |

When inserting, every column that is defined as non-nullable in the UDT must be included in the `columns` array. Columns that are omitted from the payload will be set to NULL, which will fail if the column has a NOT NULL constraint.

### 5. Epicor Documentation JSON Typos

| | |
|---|---|
| **Discovery** | April 2026 (community-reported) |
| **Affected versions** | Official documentation as of April 2026 |
| **Workaround** | Validate JSON before sending |

The official Epicor documentation examples for this API contain JSON syntax errors (extra trailing commas, mismatched brackets). If copying from the official docs, validate your JSON before sending. Credit: Felipe Maurer.

### 6. SaaS Hostname Difference

| | |
|---|---|
| **Discovery** | April 2026 (community-reported, Epicor support confirmed) |
| **Affected versions** | SaaS-hosted environments |
| **Tested endpoints** | `insertudtdata` |
| **Workaround** | Add `-api` to the FQDN hostname |

SaaS-hosted P21 environments may require `-api` in the FQDN hostname for the UDT Service endpoint. For example:

- **On-premise:** `https://play.p21server.com/udtservice/api/udtdata/`
- **SaaS:** `https://play-api.p21server.com/udtservice/api/udtdata/`

If you receive connection errors or 404s in a SaaS environment, check whether the `-api` hostname variant is required. Credit: Brad Vandenbogaerde.

---

## Complete Workflow Example

A typical UDT workflow: insert a record, query it via OData, update it, then delete it.

<!-- tabs -->

**Python:**
```python
"""Insert a UDT row, look it up via OData, update it, then delete it."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
TABLE = "udt_custom_orders"               # UDT table name
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

    # 1. INSERT a row
    insert_payload = {
        "table": TABLE,
        "rows": [
            {
                "columns": [
                    {"name": "order_ref", "value": "ORD-2026-100"},
                    {"name": "customer_name", "value": "ABC Supply Company"},
                    {"name": "order_total", "value": "500.00"},
                    {"name": "status", "value": "draft"},
                ],
                "conditions": [],
            }
        ],
    }
    resp = client.post(
        f"{BASE_URL}/udtservice/api/udtdata/insertudtdata",
        json=insert_payload,
        headers=headers,
    )
    result = resp.json()
    print(f"Insert: errorNo={result['errorNo']}, {result['errorMessage']}")

    # 2. READ via OData to get row_uid
    resp = client.get(
        f"{BASE_URL}/odataservice/odata/table/{TABLE}",
        params={"$filter": "order_ref eq 'ORD-2026-100'"},
        headers=headers,
    )
    resp.raise_for_status()
    rows = resp.json().get("value", [])
    if not rows:
        print("Row not found via OData")
    else:
        row_uid = str(rows[0]["row_uid"])
        print(f"Found row_uid: {row_uid}")

        # 3. UPDATE the row
        update_payload = {
            "table": TABLE,
            "rows": [
                {
                    "columns": [
                        {"name": "status", "value": "confirmed"},
                        {"name": "order_total", "value": "525.00"},
                    ],
                    "conditions": [
                        {"name": "row_uid", "value": row_uid},
                    ],
                }
            ],
        }
        resp = client.put(
            f"{BASE_URL}/udtservice/api/udtdata/updateudtdata",
            json=update_payload,
            headers=headers,
        )
        result = resp.json()
        print(f"Update: errorNo={result['errorNo']}, {result['errorMessage']}")

        # 4. DELETE the row — conditions is TOP-LEVEL for delete, not nested in rows[].
        delete_payload = {
            "table": TABLE,
            "conditions": [
                {"name": "row_uid", "value": row_uid},
            ],
        }
        resp = client.request(
            "DELETE",
            f"{BASE_URL}/udtservice/api/udtdata/deleteudtdata",
            json=delete_payload,
            headers=headers,
        )
        result = resp.json()
        print(f"Delete: errorNo={result['errorNo']}, {result['errorMessage']}")
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
const string Table = "udt_custom_orders";               // UDT table name
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

// 1. INSERT a row
var insertPayload = new
{
    table = Table,
    rows = new object[]
    {
        new
        {
            columns = new object[]
            {
                new { name = "order_ref", value = "ORD-2026-100" },
                new { name = "customer_name", value = "ABC Supply Company" },
                new { name = "order_total", value = "500.00" },
                new { name = "status", value = "draft" },
            },
            conditions = Array.Empty<object>(),
        },
    },
};
var resp = await client.PostAsync(
    $"{BaseUrl}/udtservice/api/udtdata/insertudtdata",
    new StringContent(JsonSerializer.Serialize(insertPayload), Encoding.UTF8, "application/json"));
var result = JsonDocument.Parse(await resp.Content.ReadAsStringAsync()).RootElement;
Console.WriteLine(
    $"Insert: errorNo={result.GetProperty("errorNo").GetInt32()}, {result.GetProperty("errorMessage").GetString()}");

// 2. READ via OData to get row_uid
resp = await client.GetAsync(
    $"{BaseUrl}/odataservice/odata/table/{Table}?$filter=order_ref eq 'ORD-2026-100'");
resp.EnsureSuccessStatusCode();
var data = JsonDocument.Parse(await resp.Content.ReadAsStringAsync()).RootElement;
var rows = data.GetProperty("value");

if (rows.GetArrayLength() == 0)
{
    Console.WriteLine("Row not found via OData");
}
else
{
    var rowUid = rows[0].GetProperty("row_uid").ToString();
    Console.WriteLine($"Found row_uid: {rowUid}");

    // 3. UPDATE the row
    var updatePayload = new
    {
        table = Table,
        rows = new object[]
        {
            new
            {
                columns = new object[]
                {
                    new { name = "status", value = "confirmed" },
                    new { name = "order_total", value = "525.00" },
                },
                conditions = new object[]
                {
                    new { name = "row_uid", value = rowUid },
                },
            },
        },
    };
    resp = await client.PutAsync(
        $"{BaseUrl}/udtservice/api/udtdata/updateudtdata",
        new StringContent(JsonSerializer.Serialize(updatePayload), Encoding.UTF8, "application/json"));
    result = JsonDocument.Parse(await resp.Content.ReadAsStringAsync()).RootElement;
    Console.WriteLine(
        $"Update: errorNo={result.GetProperty("errorNo").GetInt32()}, {result.GetProperty("errorMessage").GetString()}");

    // 4. DELETE the row — conditions is TOP-LEVEL for delete, not nested in rows[].
    var deletePayload = new
    {
        table = Table,
        conditions = new object[]
        {
            new { name = "row_uid", value = rowUid },
        },
    };
    var deleteRequest = new HttpRequestMessage(
        HttpMethod.Delete, $"{BaseUrl}/udtservice/api/udtdata/deleteudtdata")
    {
        Content = new StringContent(JsonSerializer.Serialize(deletePayload), Encoding.UTF8, "application/json"),
    };
    resp = await client.SendAsync(deleteRequest);
    result = JsonDocument.Parse(await resp.Content.ReadAsStringAsync()).RootElement;
    Console.WriteLine(
        $"Delete: errorNo={result.GetProperty("errorNo").GetInt32()}, {result.GetProperty("errorMessage").GetString()}");
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

---

## Related

- [Authentication](00-Authentication.md) — Token generation
- [API Selection Guide](01-API-Selection-Guide.md) — Which API to use when
- [OData API](02-OData-API.md) — Read UDT data via Data Services
- [Error Handling](06-Error-Handling.md) — Common P21 error patterns
