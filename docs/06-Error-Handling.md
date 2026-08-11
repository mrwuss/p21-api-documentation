# Error Handling

> **Disclaimer:** This is unofficial, community-created documentation for Epicor Prophet 21 APIs. It is not affiliated with, endorsed by, or supported by Epicor Software Corporation. All product names, trademarks, and registered trademarks are property of their respective owners. Use at your own risk.

---

## Overview

This guide covers error handling across all P21 APIs, including HTTP status codes, API-specific error responses, and troubleshooting strategies.

---

## HTTP Status Codes

### Success Codes

| Code | Meaning | When Used |
|------|---------|-----------|
| 200 | OK | Request succeeded |
| 201 | Created | Resource created (POST) |
| 204 | No Content | Request succeeded, no body (DELETE) |

### Client Error Codes

| Code | Meaning | Common Cause |
|------|---------|--------------|
| 400 | Bad Request | Invalid JSON, missing fields, invalid values |
| 401 | Unauthorized | Invalid/expired token, missing auth header |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Invalid endpoint, resource doesn't exist |
| 405 | Method Not Allowed | Wrong HTTP method for endpoint |
| 408 | Request Timeout | Client took too long to send the request |
| 409 | Conflict | Resource conflict (concurrent updates) |
| 422 | Unprocessable Entity | Validation failed |

### Server Error Codes

| Code | Meaning | Common Cause |
|------|---------|--------------|
| 500 | Internal Server Error | Server-side error, bug |
| 502 | Bad Gateway | Middleware proxy issue |
| 503 | Service Unavailable | Server overloaded, maintenance |
| 504 | Gateway Timeout | Backend service timeout |

---

## Authentication Errors

### Token Endpoint Errors

**401 - Invalid Credentials**
```json
{
    "error": "invalid_grant",
    "error_description": "The user name or password is incorrect."
}
```

**401 - Invalid Consumer Key**
```json
{
    "error": "invalid_client",
    "error_description": "Client authentication failed."
}
```

**403 - API Scope Not Granted**
```json
{
    "error": "insufficient_scope",
    "error_description": "Consumer key does not have access to this API."
}
```

**XML Response Instead of JSON**

Some middleware instances return XML instead of JSON for token endpoints. If your JSON parsing fails, check if the response body is XML:
```xml
<TokenResponse><AccessToken>eyJ...</AccessToken><ExpiresIn>86400</ExpiresIn></TokenResponse>
```

**Solution**: Use a dual-format parser that tries JSON first, then falls back to XML regex parsing. See [Authentication - XML Token Responses](00-Authentication.md#xml-token-responses).

### Token Troubleshooting

| Issue | Solution |
|-------|----------|
| Invalid credentials | Verify username/password in P21 |
| Token expired | Refresh token or re-authenticate |
| Consumer key invalid | Check API Console for correct key |
| Missing scope | Add required API scope to consumer key |
| JSON parse fails on token response | Middleware may return XML — use dual-format parser |

---

## OData API Errors

### 400 - Invalid Filter Expression

```json
{
    "error": {
        "code": "400",
        "message": "Invalid filter expression: 'supplier eq 10050'"
    }
}
```

**Solution**: Check filter syntax. Common issues:
- Missing `_id` suffix on numeric fields: `supplier_id eq 10050`
- Wrong operator: Use `eq`, not `=`
- Unquoted strings: Use `'value'` for strings

### 404 - Table Not Found

```json
{
    "error": {
        "code": "404",
        "message": "Resource not found: table/invalid_table"
    }
}
```

**Solution**: Verify table name exists in P21 database.

### Query Too Complex

Long filter expressions or many joined conditions may fail:
```json
{
    "error": {
        "code": "400",
        "message": "Query is too complex"
    }
}
```

**Solution**: Break into multiple smaller queries.

---

## Transaction API Errors

### Summary Object

The Transaction API returns a `Summary` object with success/failure counts:

```json
{
    "Messages": ["Transaction 1:: Customer ID is required"],
    "Results": null,
    "Summary": {
        "Succeeded": 0,
        "Failed": 1,
        "Other": 0
    }
}
```

Always check `Summary.Failed` even on HTTP 200 responses.

### Common Transaction Errors

**Required Field Missing**
```json
{
    "Messages": ["Transaction 1:: customer_id is required"]
}
```

**Invalid Field Value**
```json
{
    "Messages": ["Transaction 1:: Invalid value for price_page_type_cd: 'InvalidType'"]
}
```

**Field Order Issue**
```json
{
    "Messages": ["Transaction 1:: company_id must be set before product_group_id"]
}
```

**Solution**: Check the service definition for required fields and order.

**HTTP 500 on `Status: "Existing"`**

`POST /api/v2/transaction` with `Status: "Existing"` returns HTTP 500 `NullReferenceException` (at `ToInternalBeSpecification`) — a platform-wide bug, not a payload problem, confirmed across multiple services.

**Solution**: Use `Status: "New"` with key fields identifying the existing record — keyed `"New"` rows act as an upsert (update on key match, insert when absent). See [Transaction API - Updating an Existing Contract](03-Transaction-API.md#updating-an-existing-contract).

**Report Services Look Broken (But Aren't)**

Two traps when working with report (`m_*`) services:

- `GET /api/v2/services?type=report` returns an **empty list** (and other `type` values return 400) — report services are hidden from discovery but still callable.
- `POST /api/v2/transaction` **accepts** `m_*` payloads and returns `Succeeded` while emitting **nothing**. Reports must run via `POST /api/v2/process/pdfreport`.

See [Transaction API - PDF Report Generation](03-Transaction-API.md#pdf-report-generation).

**Service Fails on `/transaction` Endpoint**

Some services silently fail or return errors when sent to `/api/v2/transaction`. These services must use `/api/v2/commands` instead. See [Transaction API - Commands Endpoint](03-Transaction-API.md#commands-endpoint) for the full list of affected services.

### Session Pool Contamination

```json
{
    "error": {
        "message": "Unexpected response window encountered"
    }
}
```

Or validation errors on unrelated fields.

**Cause**: A previous failed request left a dialog open in the session pool.

**Solutions**:
1. Use the async endpoint
2. Implement retry logic with delay
3. Restart the middleware (last resort)

See [Session Pool Troubleshooting](07-Session-Pool-Troubleshooting.md) for details.

---

## Interactive API Errors

### Empty HTTP 500 on Every Interactive Call (2026.1)

On P21 **2026.1**, any interactive request whose `Accept` header does not include `application/json` returns an **empty-body HTTP 500** — including `Accept: */*`, the default of httpx and .NET HttpClient. The same request with `application/json` present succeeds; 2025.2 is unaffected.

The rule is *"`application/json` must be present"*, not *"`*/*` is rejected"* — `Accept: application/json, */*` works. `application/xml` and `text/html` both fail, even though the `/api/v2` Transaction endpoints negotiate XML fine.

**Solution**: send `Accept: application/json` on every request. Details: [Breaking Changes § 2026.1](14-Breaking-Changes.md#p21-20261).

### Alternating 500 / 409 "Session already exists" (2026.1)

The failed session create above still **half-creates the session** server-side, so retries hit **409 `{"ErrorMessage":"Session already exists."}`**. If you see this pattern on 2026.1, check the `Accept` header first — it is not a session-pool problem.

**Clear the ghost with `DELETE {uiserver}/api/ui/interactive/sessions`** — it returns 200 and a clean create succeeds immediately after. Waiting out `SessionCleanupExpiration` (~6 min) also works but is unnecessary.

> **The ghost masks the diagnosis.** Once a call has poisoned the session, *every* subsequent create returns 409 no matter what headers it sends — so the header experiment you would run to confirm the cause reports the wrong answer. `DELETE` the session before each attempt when testing this. Details: [Breaking Changes § 2026.1](14-Breaking-Changes.md#p21-20261).

### Batched `/v2/change` Partially Applied After a 400 (2026.1)

A `PUT /v2/change` carrying multiple fields is **not atomic**. If one field is rejected, the response is an HTTP 400 error envelope with **no `Status` field** — but the other fields in the same batch **have already been applied** to the window buffer. Treating the 400 as "nothing happened" and retrying or saving commits a partially-applied edit.

**Solution**: one field per `/change` call, check every call's status, and read back out-of-band. Details: [Breaking Changes § 2026.1](14-Breaking-Changes.md#p21-20261).

### Session Errors

**Session Not Found**
```json
{
    "error": "Session not found or expired"
}
```

**Solution**: Start a new session.

**Session Timeout**
Sessions expire after the configured `SessionTimeout` of inactivity (server default 60 seconds; longer on some configurations). See [Interactive API - Session Parameters](04-Interactive-API.md#session-parameters-userparameters).

**Solution**: Keep sessions short, end when done.

### Window Errors

**Window Not Open**
```json
{
    "error": "Window not found"
}
```

**Solution**: Re-open the window.

**Blocked Status**

When a response window opens, the API returns:
```json
{
    "Status": 3,
    "Events": [
        {"Name": "windowopened", "Data": [{"Key": "windowid", "Value": "..."}]}
    ]
}
```

**Solution**: Handle the response window before continuing.

### 422 / 400 - Wrong Query Parameter

```json
{
    "ErrorMessage": "Window ID was not provided"
}
```

**Cause**: Using `?windowId=` on an endpoint that expects `?id=`, or vice versa. The v2 API is inconsistent — most endpoints use `?id=` but the tools endpoint uses `?windowId=`.

**Solution**: See [Interactive API - Query Parameter Inconsistency](04-Interactive-API.md#data-operations-v2-recommended) for the correct parameter per endpoint.

### Field Not Found

```json
{
    "error": "Field 'invalid_field' not found in datawindow 'd_form'"
}
```

**Solution**: Right-click field in P21, select Help > SQL Information to get correct names.

---

## Entity API Errors

### 404 - Endpoint Not Found

```json
{
    "error": "Not Found"
}
```

**Possible Causes**:
- Entity API not enabled
- Wrong endpoint path
- Entity requires specific licensing

**Solution**: Check middleware home page for available endpoints.

### 405 - Method Not Allowed (Address Updates)

Addresses do not support PUT/update operations. Attempting to update an address returns:
```text
HTTP 405 Method Not Allowed
```

This is **by design** — the Address entity has a reduced API surface. See [Entity API - Address Limitations](05-Entity-API.md#address-limitations).

### 500 - Address Template Not Available

```http
GET /api/entity/addresses/new → 500 Internal Server Error
```

The Address entity does not have a `/new` template endpoint. This is by design — use the Customer or Vendor template endpoints to see address fields within their extended properties.

### Validation Errors

```json
{
    "Message": "The request is invalid.",
    "Errors": [
        "CustomerName is required",
        "State must be a valid 2-letter code"
    ]
}
```

**Solution**: Check the `Errors` array for specific issues.

---

## UDT Service Errors

### `"Invalid Row Uid!"` on Every Update (2026.1)

```json
400 {"error": ["Invalid Row Uid!"]}
```

The update and delete endpoints identify rows by a column named **exactly `row_uid`**. A UDT created by 2026.1's User Defined Table Maintenance has its primary key named `udt_{tablename}_uid` and **no `row_uid`** — so this error comes back for *every* condition you try, including the real PK name.

**Check whether the column exists at all**:

```http
GET /odataservice/odata/table/{udt}?$select=row_uid
→ 404 "Could not find a property named 'row_uid' on type 'dbo.{udt}'."
```

**Solution**: if there's no `row_uid`, these endpoints cannot reach your data — use P21's maintenance UI or direct SQL. Details: [UDT Service API § Update](13-UDT-Service-API.md#update) · [Breaking Changes § 2026.1](14-Breaking-Changes.md#p21-20261).

### `"[0] rows deleted ... successfully!"` — a Delete That Deletes Nothing (2026.1)

```json
200 {"id": 0, "errorNo": 0,
     "errorMessage": "[0] rows deleted from [udt_example] table successfully!"}
```

> ⚠️ **This is a success response that did nothing.** `errorNo: 0` and the word *"successfully"* pass every ordinary status check — only the `[0]` row count betrays it. On a UDT without `row_uid` (see above), **every** delete returns this. A purge or retention job built on it reports success forever while the table grows without bound.

**Solution**: parse the `[N]` count out of `errorMessage` and treat `[0]` as a failure — never trust `errorNo: 0` alone. Confirm with a row-count read-back over OData.

### `"Conditions cannot be blank or none!"` on Delete (2026.1)

```json
400 {"error": ["Conditions cannot be blank or none!"]}
```

The delete endpoint reads `conditions` from the payload's **top level**, unlike update which reads them from inside `rows[]`. Sending the nested form produces this error even though `conditions` is clearly populated.

**Solution**: move `conditions` up a level — `{"table": "...", "conditions": [...]}`. Details: [UDT Service API § Delete](13-UDT-Service-API.md#delete).

### `"Invalid UDT table"` / `"Incompatible table for bulk insert"`

```json
400 {"errorNo": 4001, "errorMessage": "Invalid UDT table", ...}   // udtdata endpoints
400 "Incompatible table for bulk insert: supplier"                 // bulkupload endpoint
```

Both mean the target isn't a registered UDT. Pass the **`udt_`-prefixed name** (`udt_custom_orders`) — the bare name from the maintenance window (`custom_orders`) and the `udv_` view name are both rejected. Ordinary P21 tables are rejected too, by design.

**Solution**: confirm the exact name in `master_udt_definition.udt_table_name` over OData.

---

## Python Error Handling

### httpx Error Handling

<!-- tabs -->

**Python**

```python
"""Catch HTTP-level failures calling P21 -- distinct from the API's own Status field."""
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

    # Swap in a bad key (e.g. a nonexistent customer) to see the except branch fire.
    url = f"{BASE_URL}/api/entity/customers/ping"
    try:
        response = client.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        print(data)
    except httpx.HTTPStatusError as e:
        print(f"HTTP Error: {e.response.status_code}")
        print(f"Response: {e.response.text}")
    except httpx.RequestError as e:
        print(f"Request Error: {e}")
    except Exception as e:
        print(f"Unexpected Error: {e}")
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

// Swap in a bad key (e.g. a nonexistent customer) to see the catch branch fire.
var url = $"{BaseUrl}/api/entity/customers/ping";
try
{
    var response = await client.GetAsync(url);
    var body = await response.Content.ReadAsStringAsync();
    response.EnsureSuccessStatusCode();
    Console.WriteLine(body);
}
catch (HttpRequestException ex) when (ex.StatusCode != null)
{
    Console.WriteLine($"HTTP Error: {(int)ex.StatusCode}");
    Console.WriteLine($"Message: {ex.Message}");
}
catch (HttpRequestException ex)
{
    Console.WriteLine($"Request Error: {ex.Message}");
}
catch (Exception ex)
{
    Console.WriteLine($"Unexpected Error: {ex.Message}");
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

### Transaction API Error Handling

<!-- tabs -->

**Python**

```python
"""Check a Transaction API response's Summary -- HTTP 200 does not mean success."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
CUSTOMER_ID = "100198"
ITEM_ID = "WIDGET-001"
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


def get_ui_server(client: httpx.Client, token: str) -> str:
    """Transaction and Interactive calls go to the UI server, not BASE_URL."""
    r = client.get(
        f"{BASE_URL}/api/ui/router/v1/?urlType=external",  # trailing slash avoids a 307
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )
    r.raise_for_status()
    try:
        return r.json()["Url"].rstrip("/")
    except (ValueError, KeyError):
        match = re.search(r"<Url>([^<]+)</Url>", r.text)
        if not match:
            raise ValueError(f"No Url in router response: {r.text[:200]}") from None
        return match.group(1).rstrip("/")


def check_transaction_result(response_data: dict) -> bool:
    """Check if a Transaction API call succeeded."""
    summary = response_data.get("Summary", {})
    messages = response_data.get("Messages", [])

    if summary.get("Failed", 0) > 0:
        for msg in messages:
            print(f"Error: {msg}")
        return False

    return True


with httpx.Client(verify=VERIFY_SSL, timeout=120, follow_redirects=True) as client:
    token = get_token(client)
    ui_server = get_ui_server(client, token)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",       # 2026.1 returns an empty 500 without this
        "Content-Type": "application/json",
    }

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
                        "Edits": [{"Name": "customer_id", "Value": CUSTOMER_ID}],
                        "RelativeDateEdits": [],
                    }],
                },
                {
                    "Name": "TP_ITEMS.items",
                    "Type": "List",
                    "Keys": [],
                    "Rows": [{
                        "Edits": [
                            {"Name": "oe_order_item_id", "Value": ITEM_ID},
                            {"Name": "unit_quantity", "Value": "1"},
                        ],
                        "RelativeDateEdits": [],
                    }],
                },
            ],
        }],
    }

    response = client.post(f"{ui_server}/api/v2/transaction", headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()

    if not check_transaction_result(data):
        print("Transaction failed -- see messages above.")
    else:
        print("Transaction succeeded.")
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
const string CustomerId = "100198";
const string ItemId = "WIDGET-001";
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
var uiServer = await GetUiServerAsync(client, token);
client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);

var payload = JsonSerializer.Serialize(new
{
    Name = "Order",
    UseCodeValues = false,
    Transactions = new object[]
    {
        new
        {
            Status = "New",
            DataElements = new object[]
            {
                new
                {
                    Name = "TABPAGE_1.order",
                    Type = "Form",
                    Keys = Array.Empty<string>(),
                    Rows = new object[]
                    {
                        new
                        {
                            Edits = new object[] { new { Name = "customer_id", Value = CustomerId } },
                            RelativeDateEdits = Array.Empty<object>(),
                        },
                    },
                },
                new
                {
                    Name = "TP_ITEMS.items",
                    Type = "List",
                    Keys = Array.Empty<string>(),
                    Rows = new object[]
                    {
                        new
                        {
                            Edits = new object[]
                            {
                                new { Name = "oe_order_item_id", Value = ItemId },
                                new { Name = "unit_quantity", Value = "1" },
                            },
                            RelativeDateEdits = Array.Empty<object>(),
                        },
                    },
                },
            },
        },
    },
});

var response = await client.PostAsync(
    $"{uiServer}/api/v2/transaction",
    new StringContent(payload, Encoding.UTF8, "application/json"));
response.EnsureSuccessStatusCode();
using var data = JsonDocument.Parse(await response.Content.ReadAsStringAsync());

if (!CheckTransactionResult(data.RootElement))
    Console.WriteLine("Transaction failed -- see messages above.");
else
    Console.WriteLine("Transaction succeeded.");

// --- helpers ---------------------------------------------------------------

// Check if a Transaction API call succeeded.
static bool CheckTransactionResult(JsonElement responseData)
{
    var failed = 0;
    if (responseData.TryGetProperty("Summary", out var summary) &&
        summary.TryGetProperty("Failed", out var failedElement))
    {
        failed = failedElement.GetInt32();
    }

    if (failed > 0)
    {
        if (responseData.TryGetProperty("Messages", out var messages))
        {
            foreach (var msg in messages.EnumerateArray())
                Console.WriteLine($"Error: {msg}");
        }
        return false;
    }
    return true;
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

// Transaction and Interactive calls go to the UI server, not BaseUrl.
static async Task<string> GetUiServerAsync(HttpClient client, string token)
{
    using var request = new HttpRequestMessage(
        HttpMethod.Get, $"{BaseUrl}/api/ui/router/v1/?urlType=external");
    request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
    var response = await client.SendAsync(request);
    response.EnsureSuccessStatusCode();
    return ReadField(await response.Content.ReadAsStringAsync(), "Url").TrimEnd('/');
}

// Some middleware answers these two endpoints in XML even when asked for JSON.
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

### Retry Logic

<!-- tabs -->

**Python**

```python
"""Retry a P21 call with exponential backoff on transient 5xx errors."""
import random
import re
import time

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


def retry_request(func, max_retries=3, base_delay=1.0):
    """Retry a request with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return func()
        except httpx.HTTPStatusError as e:
            if e.response.status_code in [500, 502, 503, 504]:
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    time.sleep(delay)
                    continue
            raise
    return None


with httpx.Client(verify=VERIFY_SSL, timeout=120, follow_redirects=True) as client:
    token = get_token(client)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",       # 2026.1 returns an empty 500 without this
        "Content-Type": "application/json",
    }

    def call():
        r = client.get(f"{BASE_URL}/api/entity/customers/ping", headers=headers)
        r.raise_for_status()
        return r

    response = retry_request(call)
    print(response.json() if response is not None else "All retries exhausted")
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

var response = await RetryRequestAsync(
    () => client.GetAsync($"{BaseUrl}/api/entity/customers/ping"));
Console.WriteLine(response is not null
    ? await response.Content.ReadAsStringAsync()
    : "All retries exhausted");

// --- helpers ---------------------------------------------------------------

static async Task<HttpResponseMessage?> RetryRequestAsync(
    Func<Task<HttpResponseMessage>> func, int maxRetries = 3, double baseDelay = 1.0)
{
    var retryableStatusCodes = new[] { 500, 502, 503, 504 };
    var jitter = new Random();

    for (int attempt = 0; attempt < maxRetries; attempt++)
    {
        var response = await func();
        if (retryableStatusCodes.Contains((int)response.StatusCode))
        {
            if (attempt < maxRetries - 1)
            {
                double delay = baseDelay * Math.Pow(2, attempt) + jitter.NextDouble();
                await Task.Delay(TimeSpan.FromSeconds(delay));
                continue;
            }
        }
        response.EnsureSuccessStatusCode();
        return response;
    }
    return null;
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

> **Not all 500s are transient.** Some HTTP 500s are deterministic and will fail on every retry — notably Transaction API `Status: "Existing"` (`NullReferenceException`) and XML payloads with wrong DataContract element order. Fix the payload instead of retrying those.

---

## Debugging Tips

### Enable Verbose Logging

<!-- tabs -->

**Python**

```python
import logging

logging.basicConfig(level=logging.DEBUG)
httpx_logger = logging.getLogger("httpx")
httpx_logger.setLevel(logging.DEBUG)
```

**C#**

```csharp
// Use ILogger (Microsoft.Extensions.Logging) or enable HttpClient tracing
using var loggerFactory = LoggerFactory.Create(builder =>
{
    builder.AddConsole().SetMinimumLevel(LogLevel.Debug);
});
var logger = loggerFactory.CreateLogger("HttpClient");

// Or enable System.Net tracing via environment variable:
// set DOTNET_SYSTEM_NET_HTTP_SOCKETSHTTPHANDLER_LOGGING=true
```

<!-- /tabs -->

> Full runnable version: [Retry Logic](#retry-logic) — drop these lines in before the `with httpx.Client(...)` block (Python) or before building `client` (C#) to see debug output on a real call.

### Log Request/Response

<!-- tabs -->

**Python**

```python
def log_request(request):
    print(f"Request: {request.method} {request.url}")
    print(f"Headers: {dict(request.headers)}")
    if request.content:
        print(f"Body: {request.content[:500]}")

def log_response(response):
    print(f"Response: {response.status_code}")
    print(f"Body: {response.text[:500]}")
```

**C#**

```csharp
void LogRequest(HttpRequestMessage request)
{
    Console.WriteLine($"Request: {request.Method} {request.RequestUri}");
    foreach (var header in request.Headers)
    {
        Console.WriteLine($"  {header.Key}: {string.Join(", ", header.Value)}");
    }
    if (request.Content != null)
    {
        var body = request.Content.ReadAsStringAsync().Result;
        Console.WriteLine($"Body: {body[..Math.Min(body.Length, 500)]}");
    }
}

void LogResponse(HttpResponseMessage response)
{
    Console.WriteLine($"Response: {(int)response.StatusCode}");
    var body = response.Content.ReadAsStringAsync().Result;
    Console.WriteLine($"Body: {body[..Math.Min(body.Length, 500)]}");
}
```

<!-- /tabs -->

> Full runnable version: [httpx Error Handling](#httpx-error-handling) — call `log_request`/`log_response` (or `LogRequest`/`LogResponse`) on the `response` object it builds.

### Check Token Expiration

<!-- tabs -->

**Python**

```python
import jwt
from datetime import datetime

def check_token_expiry(token: str):
    """Check if token is expired."""
    try:
        # Decode without verification (just to read claims)
        payload = jwt.decode(token, options={"verify_signature": False})
        exp = payload.get("exp")
        if exp:
            exp_time = datetime.fromtimestamp(exp)
            print(f"Token expires: {exp_time}")
            if exp_time < datetime.now():
                print("Token is EXPIRED")
            else:
                remaining = exp_time - datetime.now()
                print(f"Token valid for: {remaining}")
    except Exception as e:
        print(f"Could not decode token: {e}")
```

**C#**

```csharp
void CheckTokenExpiry(string token)
{
    try
    {
        // Decode the payload without signature verification
        var parts = token.Split('.');
        if (parts.Length < 2)
        {
            Console.WriteLine("Invalid token format");
            return;
        }
        // Pad Base64 string if needed
        var payload = parts[1];
        payload = payload.PadRight(payload.Length + (4 - payload.Length % 4) % 4, '=');
        var json = System.Text.Encoding.UTF8.GetString(Convert.FromBase64String(payload));
        var claims = JObject.Parse(json);

        var exp = claims["exp"]?.Value<long>();
        if (exp.HasValue)
        {
            var expTime = DateTimeOffset.FromUnixTimeSeconds(exp.Value).LocalDateTime;
            Console.WriteLine($"Token expires: {expTime}");
            if (expTime < DateTime.Now)
            {
                Console.WriteLine("Token is EXPIRED");
            }
            else
            {
                var remaining = expTime - DateTime.Now;
                Console.WriteLine($"Token valid for: {remaining}");
            }
        }
    }
    catch (Exception ex)
    {
        Console.WriteLine($"Could not decode token: {ex.Message}");
    }
}
```

<!-- /tabs -->

> Full runnable version: [httpx Error Handling](#httpx-error-handling) — call `check_token_expiry(token)` (or `CheckTokenExpiry(token)`) right after `get_token`/`GetTokenAsync` returns.

---

## Common Issues Quick Reference

| Issue | API | Solution |
|-------|-----|----------|
| 401 on every request | All | Check token, re-authenticate |
| 307 Redirect | Entity | Add `follow_redirects=True` (list endpoints) |
| Request timeout | All | Increase timeout, check network |
| "Unexpected window" | Transaction | Use async endpoint, add delays |
| 500 NullReferenceException on `Status: "Existing"` | Transaction | Use `Status: "New"` + key fields (upsert) — [details](03-Transaction-API.md#updating-an-existing-contract) |
| `services?type=report` empty (other `type` values 400) | Transaction | Expected — report services are hidden; run via `/api/v2/process/pdfreport` |
| m_* report returns Succeeded, no output | Transaction | Use `POST /api/v2/process/pdfreport`, not `/transaction` — [details](03-Transaction-API.md#pdf-report-generation) |
| Session expired | Interactive | Start new session |
| "Blocked" status | Interactive | Handle response window |
| 422 "Window ID not provided" | Interactive | Use `?id=` not `?windowId=` (except tools) |
| 404 on table | OData | Verify table name |
| 404 on entity | Entity | Check if Entity API enabled |
| 405 on address update | Entity | Address has no PUT — by design |
| 500 on address `/new` | Entity | Address has no template — by design |
| XML instead of JSON (token) | Auth | Use dual-format parser |
| Validation errors | All | Check required fields |

---

## Related

- [Authentication](00-Authentication.md)
- [Session Pool Troubleshooting](07-Session-Pool-Troubleshooting.md)
- API-specific documentation for detailed error handling
