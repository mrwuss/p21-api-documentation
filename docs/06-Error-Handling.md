# Error Handling

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

### Token Troubleshooting

| Issue | Solution |
|-------|----------|
| Invalid credentials | Verify username/password in P21 |
| Token expired | Refresh token or re-authenticate |
| Consumer key invalid | Check API Console for correct key |
| Missing scope | Add required API scope to consumer key |

---

## OData API Errors

### 400 - Invalid Filter Expression

```json
{
    "error": {
        "code": "400",
        "message": "Invalid filter expression: 'supplier eq 21274'"
    }
}
```

**Solution**: Check filter syntax. Common issues:
- Missing `_id` suffix on numeric fields: `supplier_id eq 21274`
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
    "Status": "Blocked",
    "Events": [
        {"Name": "windowopened", "Data": {"WindowId": "..."}}
    ]
}
```

**Solution**: Handle the response window before continuing.

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

### Transaction API Error Handling

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

### Retry Logic

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

---

## Debugging Tips

### Enable Verbose Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)
httpx_logger = logging.getLogger("httpx")
httpx_logger.setLevel(logging.DEBUG)
```

### Log Request/Response

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

### Check Token Expiration

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

---

## Common Issues Quick Reference

| Issue | API | Solution |
|-------|-----|----------|
| 401 on every request | All | Check token, re-authenticate |
| 307 Redirect | All | Add `follow_redirects=True` |
| Request timeout | All | Increase timeout, check network |
| "Unexpected window" | Transaction | Use async endpoint, add delays |
| Session expired | Interactive | Start new session |
| "Blocked" status | Interactive | Handle response window |
| 404 on table | OData | Verify table name |
| 404 on entity | Entity | Check if Entity API enabled |
| Validation errors | All | Check required fields |

---

## Related

- [Authentication](00-Authentication.md)
- [Session Pool Troubleshooting](07-Session-Pool-Troubleshooting.md)
- API-specific documentation for detailed error handling
