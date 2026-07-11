# User Defined Tables (UDT) Service API

> **Disclaimer:** This is unofficial, community-created documentation for Epicor Prophet 21 APIs. It is not affiliated with, endorsed by, or supported by Epicor Software Corporation. All product names, trademarks, and registered trademarks are property of their respective owners. Use at your own risk.

---

> **Added April 2026** — Discovered and tested by Felipe Maurer. Additional contributions from David Sokoloski (initial P21 help docs reference), Brad Vandenbogaerde (database tables, SaaS hostname fix), John Kennedy (SQL keyword issue, working Python script), and Jon Christie (response format quirk).

---

## Overview

> **Source**: Official P21 Help Documentation (Zendesk) + community working code + actual API testing (April 2026).

P21 provides a **UDT Service API** at `/udtservice/api/udtdata/` for writing to User Defined Tables (UDTs). UDTs are custom tables created through P21's User Defined Table Maintenance window, prefixed with `udt_` in the database.

The UDT Service API handles **write operations** (insert, update, delete). For **reading** UDT data, use the [OData API](02-OData-API.md) — UDT tables are queryable via Data Services like any other P21 table.

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
- **No schema discovery** — No endpoint to list available tables or columns
- **SQL keyword filtering** — Values containing SQL keywords (e.g., "drop", "insert") may be rejected even in legitimate data
- **UID-based conditions only** — Updates and deletes require `row_uid` to identify target rows

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
import httpx

base_url = "https://play.p21server.com"

# Get token (see Authentication docs)
token_resp = httpx.post(
    f"{base_url}/api/security/token/v2",
    json={"username": "api_user", "password": "password"},
    headers={"Accept": "application/json"},
    # verify=False,  # Only for dev environments with self-signed certs
)
token = token_resp.json()["AccessToken"]

client = httpx.Client(
    headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    },
    # verify=False,  # Only for dev environments with self-signed certs
)

payload = {
    "table": "udt_custom_orders",
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
    f"{base_url}/udtservice/api/udtdata/insertudtdata",
    json=payload,
)
result = resp.json()

if result["errorNo"] == 0:
    print(f"Success: {result['errorMessage']}")
else:
    print(f"Error {result['errorNo']}: {result['errorMessage']}")
```

**C#:**
```csharp
using System;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

var baseUrl = "https://play.p21server.com";

// Get token (see Authentication docs)
var handler = new HttpClientHandler
{
    // ServerCertificateCustomValidationCallback = (_, _, _, _) => true  // Only for dev with self-signed certs
};
var client = new HttpClient(handler) { BaseAddress = new Uri(baseUrl) };
client.DefaultRequestHeaders.Add("Accept", "application/json");

var tokenPayload = JsonConvert.SerializeObject(new
{
    username = "api_user",
    password = "password"
});
var tokenResp = await client.PostAsync(
    "/api/security/token/v2",
    new StringContent(tokenPayload, Encoding.UTF8, "application/json")
);
tokenResp.EnsureSuccessStatusCode();
var tokenJson = JObject.Parse(await tokenResp.Content.ReadAsStringAsync());
var token = tokenJson["AccessToken"]!.ToString();

client.DefaultRequestHeaders.Add("Authorization", $"Bearer {token}");

// Insert a row
var payload = new JObject
{
    ["table"] = "udt_custom_orders",
    ["rows"] = new JArray
    {
        new JObject
        {
            ["columns"] = new JArray
            {
                new JObject { ["name"] = "order_ref", ["value"] = "ORD-2026-001" },
                new JObject { ["name"] = "customer_name", ["value"] = "ABC Supply Company" },
                new JObject { ["name"] = "order_total", ["value"] = "1250.00" },
                new JObject { ["name"] = "status", ["value"] = "pending" }
            },
            ["conditions"] = new JArray()
        }
    }
};

var resp = await client.PostAsync(
    "/udtservice/api/udtdata/insertudtdata",
    new StringContent(payload.ToString(), Encoding.UTF8, "application/json")
);
var result = JObject.Parse(await resp.Content.ReadAsStringAsync());

if ((int)result["errorNo"] == 0)
{
    Console.WriteLine($"Success: {result["errorMessage"]}");
}
else
{
    Console.WriteLine($"Error {result["errorNo"]}: {result["errorMessage"]}");
}
```

<!-- /tabs -->

---

## Update

Update existing rows in a UDT table. Use `conditions` to identify which rows to update (typically by `row_uid`) and `columns` to specify the new values.

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

<!-- tabs -->

**Python:**
```python
payload = {
    "table": "udt_custom_orders",
    "rows": [
        {
            "columns": [
                {"name": "status", "value": "completed"},
                {"name": "order_total", "value": "1300.00"},
            ],
            "conditions": [
                {"name": "row_uid", "value": "12345"},
            ],
        }
    ],
}

resp = client.put(
    f"{base_url}/udtservice/api/udtdata/updateudtdata",
    json=payload,
)
result = resp.json()

if result["errorNo"] == 0:
    print(f"Success: {result['errorMessage']}")
else:
    print(f"Error {result['errorNo']}: {result['errorMessage']}")
```

**C#:**
```csharp
var payload = new JObject
{
    ["table"] = "udt_custom_orders",
    ["rows"] = new JArray
    {
        new JObject
        {
            ["columns"] = new JArray
            {
                new JObject { ["name"] = "status", ["value"] = "completed" },
                new JObject { ["name"] = "order_total", ["value"] = "1300.00" }
            },
            ["conditions"] = new JArray
            {
                new JObject { ["name"] = "row_uid", ["value"] = "12345" }
            }
        }
    }
};

var resp = await client.PutAsync(
    "/udtservice/api/udtdata/updateudtdata",
    new StringContent(payload.ToString(), Encoding.UTF8, "application/json")
);
var result = JObject.Parse(await resp.Content.ReadAsStringAsync());

if ((int)result["errorNo"] == 0)
{
    Console.WriteLine($"Success: {result["errorMessage"]}");
}
else
{
    Console.WriteLine($"Error {result["errorNo"]}: {result["errorMessage"]}");
}
```

<!-- /tabs -->

> **Note:** To get the `row_uid` for existing records, query the UDT table via OData first (see [Reading UDT Data](#reading-udt-data-odata)).

---

## Delete

Delete rows from a UDT table. Use `conditions` to identify which rows to remove (typically by `row_uid`).

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

<!-- tabs -->

**Python:**
```python
payload = {
    "table": "udt_custom_orders",
    "rows": [
        {
            "columns": [],
            "conditions": [
                {"name": "row_uid", "value": "12345"},
            ],
        }
    ],
}

resp = client.request(
    "DELETE",
    f"{base_url}/udtservice/api/udtdata/deleteudtdata",
    json=payload,
)
result = resp.json()

if result["errorNo"] == 0:
    print(f"Success: {result['errorMessage']}")
else:
    print(f"Error {result['errorNo']}: {result['errorMessage']}")
```

**C#:**
```csharp
var payload = new JObject
{
    ["table"] = "udt_custom_orders",
    ["rows"] = new JArray
    {
        new JObject
        {
            ["columns"] = new JArray(),
            ["conditions"] = new JArray
            {
                new JObject { ["name"] = "row_uid", ["value"] = "12345" }
            }
        }
    }
};

var request = new HttpRequestMessage(HttpMethod.Delete, "/udtservice/api/udtdata/deleteudtdata")
{
    Content = new StringContent(payload.ToString(), Encoding.UTF8, "application/json")
};
var resp = await client.SendAsync(request);
var result = JObject.Parse(await resp.Content.ReadAsStringAsync());

if ((int)result["errorNo"] == 0)
{
    Console.WriteLine($"Success: {result["errorMessage"]}");
}
else
{
    Console.WriteLine($"Error {result["errorNo"]}: {result["errorMessage"]}");
}
```

<!-- /tabs -->

> **Note:** The `DELETE` HTTP method with a JSON body is non-standard. Some HTTP clients require using `request()` or `SendAsync()` with an explicit `HttpRequestMessage` to include a body on DELETE requests.

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
# Query UDT data via OData
resp = client.get(
    f"{base_url}/odataservice/odata/table/udt_custom_orders",
    params={"$filter": "status eq 'pending'"},
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
// Query UDT data via OData
var resp = await client.GetAsync(
    "/odataservice/odata/table/udt_custom_orders?$filter=status eq 'pending'"
);
resp.EnsureSuccessStatusCode();
var data = JObject.Parse(await resp.Content.ReadAsStringAsync());

foreach (var row in data["value"]!)
{
    Console.WriteLine($"Order: {row["order_ref"]}, Total: {row["order_total"]}");
    // row_uid is available for subsequent update/delete operations
    Console.WriteLine($"  row_uid: {row["row_uid"]}");
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
var result = JObject.Parse(await resp.Content.ReadAsStringAsync());

if ((int)result["errorNo"] == 0)
{
    // Success — errorMessage contains the success description
    Console.WriteLine($"OK: {result["errorMessage"]}");
}
else
{
    // Error — errorNo is non-zero
    Console.WriteLine($"Failed (code {result["errorNo"]}): {result["errorMessage"]}");
    if (result["sqlErrorMessage"]?.ToString() is { Length: > 0 } sqlErr)
    {
        Console.WriteLine($"SQL Error: {sqlErr}");
    }
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
import httpx

base_url = "https://play.p21server.com"

# Authenticate (see Authentication docs for TokenManager pattern)
token_resp = httpx.post(
    f"{base_url}/api/security/token/v2",
    json={"username": "api_user", "password": "password"},
    headers={"Accept": "application/json"},
    # verify=False,  # Only for dev environments with self-signed certs
)
token = token_resp.json()["AccessToken"]

client = httpx.Client(
    headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    },
    # verify=False,  # Only for dev environments with self-signed certs
    follow_redirects=True,
)

TABLE = "udt_custom_orders"

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
    f"{base_url}/udtservice/api/udtdata/insertudtdata",
    json=insert_payload,
)
result = resp.json()
print(f"Insert: errorNo={result['errorNo']}, {result['errorMessage']}")

# 2. READ via OData to get row_uid
resp = client.get(
    f"{base_url}/odataservice/odata/table/{TABLE}",
    params={"$filter": "order_ref eq 'ORD-2026-100'"},
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
        f"{base_url}/udtservice/api/udtdata/updateudtdata",
        json=update_payload,
    )
    result = resp.json()
    print(f"Update: errorNo={result['errorNo']}, {result['errorMessage']}")

    # 4. DELETE the row
    delete_payload = {
        "table": TABLE,
        "rows": [
            {
                "columns": [],
                "conditions": [
                    {"name": "row_uid", "value": row_uid},
                ],
            }
        ],
    }
    resp = client.request(
        "DELETE",
        f"{base_url}/udtservice/api/udtdata/deleteudtdata",
        json=delete_payload,
    )
    result = resp.json()
    print(f"Delete: errorNo={result['errorNo']}, {result['errorMessage']}")
```

**C#:**
```csharp
using System;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

var baseUrl = "https://play.p21server.com";
var table = "udt_custom_orders";

// Authenticate (see Authentication docs for TokenManager pattern)
var handler = new HttpClientHandler
{
    AllowAutoRedirect = true,
    // ServerCertificateCustomValidationCallback = (_, _, _, _) => true  // Only for dev with self-signed certs
};
var client = new HttpClient(handler) { BaseAddress = new Uri(baseUrl) };
client.DefaultRequestHeaders.Add("Accept", "application/json");

var tokenPayload = JsonConvert.SerializeObject(new
{
    username = "api_user",
    password = "password"
});
var tokenResp = await client.PostAsync(
    "/api/security/token/v2",
    new StringContent(tokenPayload, Encoding.UTF8, "application/json")
);
tokenResp.EnsureSuccessStatusCode();
var tokenJson = JObject.Parse(await tokenResp.Content.ReadAsStringAsync());
var token = tokenJson["AccessToken"]!.ToString();
client.DefaultRequestHeaders.Add("Authorization", $"Bearer {token}");

// 1. INSERT a row
var insertPayload = new JObject
{
    ["table"] = table,
    ["rows"] = new JArray
    {
        new JObject
        {
            ["columns"] = new JArray
            {
                new JObject { ["name"] = "order_ref", ["value"] = "ORD-2026-100" },
                new JObject { ["name"] = "customer_name", ["value"] = "ABC Supply Company" },
                new JObject { ["name"] = "order_total", ["value"] = "500.00" },
                new JObject { ["name"] = "status", ["value"] = "draft" }
            },
            ["conditions"] = new JArray()
        }
    }
};
var resp = await client.PostAsync(
    "/udtservice/api/udtdata/insertudtdata",
    new StringContent(insertPayload.ToString(), Encoding.UTF8, "application/json")
);
var result = JObject.Parse(await resp.Content.ReadAsStringAsync());
Console.WriteLine($"Insert: errorNo={result["errorNo"]}, {result["errorMessage"]}");

// 2. READ via OData to get row_uid
resp = await client.GetAsync(
    $"/odataservice/odata/table/{table}?$filter=order_ref eq 'ORD-2026-100'"
);
resp.EnsureSuccessStatusCode();
var data = JObject.Parse(await resp.Content.ReadAsStringAsync());
var rows = data["value"] as JArray;

if (rows == null || rows.Count == 0)
{
    Console.WriteLine("Row not found via OData");
}
else
{
    var rowUid = rows[0]["row_uid"]!.ToString();
    Console.WriteLine($"Found row_uid: {rowUid}");

    // 3. UPDATE the row
    var updatePayload = new JObject
    {
        ["table"] = table,
        ["rows"] = new JArray
        {
            new JObject
            {
                ["columns"] = new JArray
                {
                    new JObject { ["name"] = "status", ["value"] = "confirmed" },
                    new JObject { ["name"] = "order_total", ["value"] = "525.00" }
                },
                ["conditions"] = new JArray
                {
                    new JObject { ["name"] = "row_uid", ["value"] = rowUid }
                }
            }
        }
    };
    resp = await client.PutAsync(
        "/udtservice/api/udtdata/updateudtdata",
        new StringContent(updatePayload.ToString(), Encoding.UTF8, "application/json")
    );
    result = JObject.Parse(await resp.Content.ReadAsStringAsync());
    Console.WriteLine($"Update: errorNo={result["errorNo"]}, {result["errorMessage"]}");

    // 4. DELETE the row
    var deletePayload = new JObject
    {
        ["table"] = table,
        ["rows"] = new JArray
        {
            new JObject
            {
                ["columns"] = new JArray(),
                ["conditions"] = new JArray
                {
                    new JObject { ["name"] = "row_uid", ["value"] = rowUid }
                }
            }
        }
    };
    var deleteRequest = new HttpRequestMessage(
        HttpMethod.Delete, "/udtservice/api/udtdata/deleteudtdata")
    {
        Content = new StringContent(
            deletePayload.ToString(), Encoding.UTF8, "application/json")
    };
    resp = await client.SendAsync(deleteRequest);
    result = JObject.Parse(await resp.Content.ReadAsStringAsync());
    Console.WriteLine($"Delete: errorNo={result["errorNo"]}, {result["errorMessage"]}");
}
```

<!-- /tabs -->

---

## Related

- [Authentication](00-Authentication.md) — Token generation
- [API Selection Guide](01-API-Selection-Guide.md) — Which API to use when
- [OData API](02-OData-API.md) — Read UDT data via Data Services
- [Error Handling](06-Error-Handling.md) — Common P21 error patterns
