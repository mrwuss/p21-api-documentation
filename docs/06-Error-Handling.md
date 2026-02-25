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
| 408 | Request Timeout | Server took too long to respond |
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

### Session Errors

**Session Not Found**
```json
{
    "error": "Session not found or expired"
}
```

**Solution**: Start a new session.

**Session Timeout**
Default timeout is typically 6 minutes of inactivity.

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

**Solution**: See [Interactive API - Query Parameter Inconsistency](04-Interactive-API.md#data-operations-v2---recommended) for the correct parameter per endpoint.

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
```
HTTP 405 Method Not Allowed
```

This is **by design** — the Address entity has a reduced API surface. See [Entity API - Address Limitations](05-Entity-API.md#address-limitations).

### 500 - Address Template Not Available

```
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

## Python Error Handling

### httpx Error Handling

<!-- tabs -->

**Python**

```python
import httpx

try:
    response = httpx.get(url, headers=headers, verify=False)
    response.raise_for_status()
    data = response.json()
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
using System;
using System.Net.Http;
using System.Threading.Tasks;
using Newtonsoft.Json.Linq;

var handler = new HttpClientHandler
{
    ServerCertificateCustomValidationCallback = (msg, cert, chain, errors) => true
};
using var client = new HttpClient(handler);
client.DefaultRequestHeaders.Add("Authorization", $"Bearer {token}");

try
{
    var response = await client.GetAsync(url);
    var body = await response.Content.ReadAsStringAsync();
    response.EnsureSuccessStatusCode();
    var data = JObject.Parse(body);
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
```

<!-- /tabs -->

### Transaction API Error Handling

<!-- tabs -->

**Python**

```python
def check_transaction_result(response_data: dict) -> bool:
    """Check if a Transaction API call succeeded."""
    summary = response_data.get("Summary", {})
    messages = response_data.get("Messages", [])

    if summary.get("Failed", 0) > 0:
        for msg in messages:
            print(f"Error: {msg}")
        return False

    return True

# Usage
response = httpx.post(url, headers=headers, json=payload)
response.raise_for_status()
data = response.json()

if not check_transaction_result(data):
    # Handle failure
    pass
```

**C#**

```csharp
bool CheckTransactionResult(JObject responseData)
{
    var summary = responseData["Summary"] as JObject;
    var messages = responseData["Messages"] as JArray;

    int failed = summary?["Failed"]?.Value<int>() ?? 0;
    if (failed > 0)
    {
        foreach (var msg in messages ?? new JArray())
        {
            Console.WriteLine($"Error: {msg}");
        }
        return false;
    }
    return true;
}

// Usage
var content = new StringContent(
    payload.ToString(), System.Text.Encoding.UTF8, "application/json");
var response = await client.PostAsync(url, content);
var body = await response.Content.ReadAsStringAsync();
response.EnsureSuccessStatusCode();
var data = JObject.Parse(body);

if (!CheckTransactionResult(data))
{
    // Handle failure
}
```

<!-- /tabs -->

### Retry Logic

<!-- tabs -->

**Python**

```python
import time
import random

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
```

**C#**

```csharp
static readonly int[] RetryableStatusCodes = { 500, 502, 503, 504 };
static readonly Random Jitter = new();

async Task<HttpResponseMessage> RetryRequestAsync(
    Func<Task<HttpResponseMessage>> func, int maxRetries = 3, double baseDelay = 1.0)
{
    for (int attempt = 0; attempt < maxRetries; attempt++)
    {
        var response = await func();
        if (RetryableStatusCodes.Contains((int)response.StatusCode))
        {
            if (attempt < maxRetries - 1)
            {
                double delay = baseDelay * Math.Pow(2, attempt) + Jitter.NextDouble();
                await Task.Delay(TimeSpan.FromSeconds(delay));
                continue;
            }
        }
        response.EnsureSuccessStatusCode();
        return response;
    }
    return null;
}
```

<!-- /tabs -->

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

---

## Common Issues Quick Reference

| Issue | API | Solution |
|-------|-----|----------|
| 401 on every request | All | Check token, re-authenticate |
| 307 Redirect | Entity | Add `follow_redirects=True` (list endpoints) |
| Request timeout | All | Increase timeout, check network |
| "Unexpected window" | Transaction | Use async endpoint, add delays |
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
