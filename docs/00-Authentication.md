# P21 API Authentication

> **Disclaimer:** This is unofficial, community-created documentation for Epicor Prophet 21 APIs. It is not affiliated with, endorsed by, or supported by Epicor Software Corporation. All product names, trademarks, and registered trademarks are property of their respective owners. Use at your own risk.

---

## Overview

All P21 APIs require authentication via Bearer tokens. This guide covers the two authentication methods:

1. **User Credentials** - Username and password authentication
2. **Consumer Key** - Pre-authenticated application key

## Token Endpoints

### V2 Endpoint (Recommended)

```http
POST https://{hostname}/api/security/token/v2
```

The V2 endpoint accepts credentials in the request body.

### V1 Endpoint (Deprecated)

```http
POST https://{hostname}/api/security/token
```

The V1 endpoint accepts credentials as headers. While still functional, Epicor recommends migrating to V2.

---

## Method 1: User Credentials

Use when you have a P21 username and password. The user must be:
- A valid, non-deleted Prophet 21 user
- Associated with a Windows user, AAD user, or SQL user

### V2 Request (Recommended)

**Request:**
```http
POST /api/security/token/v2 HTTP/1.1
Host: play.p21server.com
Content-Type: application/json
Accept: application/json

{
    "username": "api_user",
    "password": "your_password"
}
```

**Response:**
```json
{
    "AccessToken": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "RefreshToken": "dGhpcyBpcyBhIHNhbXBsZSByZWZyZXNoIHRva2Vu...",
    "ExpiresInSeconds": 86400,
    "TokenType": "Bearer"
}
```

### V1 Request (Legacy)

**Request:**
```http
POST /api/security/token HTTP/1.1
Host: play.p21server.com
username: api_user
password: your_password
Content-Type: application/json
Accept: application/json
```

**Response:** Same as V2.

### Code Examples

<!-- tabs -->

**Python:**

```python
import httpx

def get_token_v2(base_url: str, username: str, password: str) -> dict:
    """Get token using V2 endpoint (recommended)."""
    response = httpx.post(
        f"{base_url}/api/security/token/v2",
        json={"username": username, "password": password},
        headers={"Accept": "application/json"}
    )
    response.raise_for_status()
    return response.json()

def get_token_v1(base_url: str, username: str, password: str) -> dict:
    """Get token using V1 endpoint (legacy)."""
    response = httpx.post(
        f"{base_url}/api/security/token",
        headers={
            "username": username,
            "password": password,
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        content=""
    )
    response.raise_for_status()
    return response.json()
```

**C#:**

```csharp
using System;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

public static class P21Auth
{
    /// <summary>Get token using V2 endpoint (recommended).</summary>
    public static async Task<JObject> GetTokenV2Async(
        string baseUrl, string username, string password)
    {
        using var client = new HttpClient();
        var body = new { username, password };
        var content = new StringContent(
            JsonConvert.SerializeObject(body),
            Encoding.UTF8, "application/json");
        client.DefaultRequestHeaders.Add("Accept", "application/json");

        var response = await client.PostAsync(
            $"{baseUrl}/api/security/token/v2", content);
        response.EnsureSuccessStatusCode();

        var json = await response.Content.ReadAsStringAsync();
        return JObject.Parse(json);
    }

    /// <summary>Get token using V1 endpoint (legacy).</summary>
    public static async Task<JObject> GetTokenV1Async(
        string baseUrl, string username, string password)
    {
        using var client = new HttpClient();
        client.DefaultRequestHeaders.Add("username", username);
        client.DefaultRequestHeaders.Add("password", password);
        client.DefaultRequestHeaders.Add("Accept", "application/json");

        var content = new StringContent(
            "", Encoding.UTF8, "application/json");
        var response = await client.PostAsync(
            $"{baseUrl}/api/security/token", content);
        response.EnsureSuccessStatusCode();

        var json = await response.Content.ReadAsStringAsync();
        return JObject.Parse(json);
    }
}
```

<!-- /tabs -->

---

## Method 2: Consumer Key

Use for service accounts and automated integrations. Consumer keys bypass P21 user permission checks (Application Security and Dataservice Permissions) — access is controlled by the consumer key's API scope instead.

### Creating a Consumer Key

1. Log in to SOA Admin Page (`https://{hostname}/api/admin`)
2. Open the **API Console** tab
3. Click **Register Consumer Key**
4. Configure:

| Field | Description | Recommended |
|-------|-------------|-------------|
| **Consumer** | Descriptive name (e.g., `CORE_API_CC`) | Use a name that identifies the integration |
| **Consumer Type** | `Desktop`, `Mobile`, `Web`, or `Service` | `Service` for API integrations |
| **SDK Access** | Enable for P21 SDK access | Enable if using `/p21sdk` scope |
| **Token Expire** | Key validity duration | `Never Expire` for service accounts |
| **API Scope** | Semicolon-delimited paths (see [Scopes](#api-scopes)) | `/api` for full access |

### Basic Request (No Username)

Returns a token tied to the consumer key with no P21 user context. Sufficient for read-only operations (OData, Entity API, Inventory REST API).

```http
POST /api/security/token/v2 HTTP/1.1
Host: play.p21server.com
Content-Type: application/json
Accept: application/json

{
    "ClientSecret": "62ccc18a-25e2-440c-bf6d-749c117fa9db",
    "GrantType": "client_credentials"
}
```

**Response:**
```json
{
    "AccessToken": "eyJhbGciOiJIUzI1NiIs...",
    "TokenType": "Bearer",
    "UserName": "",
    "ExpiresIn": 630720000,
    "RefreshToken": "",
    "Scope": "/api;/p21sdk",
    "SessionId": "a1b2c3d4-...",
    "ConsumerUid": "8",
    "AppKey": null
}
```

### Request with Username (Required for Interactive API)

Adding `username` to the request associates the token with a P21 user identity. This is **required** for Interactive API sessions and provides audit trail attribution for write operations.

> **Important:** The `username` must be a **real P21 user account** — not the consumer name. For example, if your consumer is named `CORE_API_CC`, you still need a P21 user like `coreapi` or `api_user` in the username field. The token endpoint accepts any string, but session creation will fail with `Error retrieving/validating user` if the user doesn't exist in P21.

```http
POST /api/security/token/v2 HTTP/1.1
Host: play.p21server.com
Content-Type: application/json
Accept: application/json

{
    "ClientSecret": "62ccc18a-25e2-440c-bf6d-749c117fa9db",
    "GrantType": "client_credentials",
    "username": "api_user"
}
```

**Response:**
```json
{
    "AccessToken": "eyJhbGciOiJIUzI1NiIs...",
    "TokenType": "Bearer",
    "UserName": "api_user",
    "ExpiresIn": 630720000,
    "RefreshToken": "",
    "Scope": "/api;/p21sdk",
    "SessionId": "e1f2a3b4-...",
    "ConsumerUid": "8",
    "AppKey": null
}
```

### JWT Token Claims

Consumer key tokens contain these claims:

| Claim | Description | Example |
|-------|-------------|---------|
| `sub` | P21 username (if provided) or empty | `"api_user"` |
| `aud` | Scope from consumer config (not the request) | `"/api;/p21sdk"` |
| `P21.ConsumerUid` | Consumer key identifier | `"8"` |
| `P21.SessionId` | Middleware session ID | `"a1b2c3d4-..."` |
| `iss` | Token issuer | `"P21.Soa"` |
| `exp` | Expiration timestamp | `2147483647` (Never Expire) |

> **Note:** The `Scope` in the token response (and the `aud` JWT claim) is determined by the consumer key's configuration in SOA Admin — not by any `Scope` field in the request. Requesting a different scope is silently ignored.

### API-Specific Behavior (Verified)

| API | Without Username | With Username |
|-----|------------------|---------------|
| **OData** | Works — uses consumer key scope | Works — username ignored for data access |
| **Entity** | Works — returns data | Works — uses specified user |
| **Inventory REST** | Works — returns data | Works — uses specified user |
| **Transaction** | Works — uses P21 install user | Works — uses specified user for audit |
| **Interactive** | **Fails** — `Error retrieving/validating user` | **Works** — user must be a real P21 account |

### Important Caveats

1. **Token endpoint creates a middleware session** — each call to `/api/security/token/v2` creates a new middleware session, which may invalidate tokens from previous calls. Get one token and reuse it.
2. **No password required** — the consumer key replaces password authentication entirely. The username is only for P21 user context, not authentication.
3. **Scope is locked** — the `Scope` field in the request is ignored. The consumer key's configured scope in SOA Admin determines access.
4. **`/api` scope is sufficient** — the `/ui` scope is not required for Interactive API. The `/api` scope covers all endpoints including UI server operations.

### Code Examples

<!-- tabs -->

**Python:**

```python
import httpx

async def get_consumer_token(
    base_url: str,
    consumer_key: str,
    username: str = "",
) -> dict:
    """Get token using consumer key authentication.

    Args:
        base_url: P21 server URL (e.g., "https://play.p21server.com")
        consumer_key: Consumer key GUID from SOA Admin
        username: Optional P21 username (required for Interactive API)

    Returns:
        Token response dict with AccessToken, Scope, etc.
    """
    payload = {
        "GrantType": "client_credentials",
        "ClientSecret": consumer_key,
    }
    if username:
        payload["username"] = username

    async with httpx.AsyncClient(verify=False) as client:
        response = await client.post(
            f"{base_url}/api/security/token/v2",
            json=payload,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )
        response.raise_for_status()
        return response.json()
```

**C#:**

```csharp
/// <summary>Get token using consumer key authentication.</summary>
/// <param name="baseUrl">P21 server URL</param>
/// <param name="consumerKey">Consumer key GUID from SOA Admin</param>
/// <param name="username">Optional P21 username (required for Interactive API)</param>
public static async Task<JObject> GetConsumerTokenAsync(
    string baseUrl, string consumerKey, string username = "")
{
    using var client = new HttpClient();
    var payload = new Dictionary<string, string>
    {
        ["GrantType"] = "client_credentials",
        ["ClientSecret"] = consumerKey
    };
    if (!string.IsNullOrEmpty(username))
        payload["username"] = username;

    var content = new StringContent(
        JsonConvert.SerializeObject(payload),
        Encoding.UTF8, "application/json");
    client.DefaultRequestHeaders.Add("Accept", "application/json");

    var response = await client.PostAsync(
        $"{baseUrl}/api/security/token/v2", content);
    response.EnsureSuccessStatusCode();

    var json = await response.Content.ReadAsStringAsync();
    return JObject.Parse(json);
}
```

<!-- /tabs -->

---

## API Scopes

Consumer keys restrict access to specific endpoints. Scopes are configured in SOA Admin as semicolon-delimited paths with a leading slash.

### URL Scopes

| Scope | Access |
|-------|--------|
| `/api` | All API endpoints (recommended for full access) |
| `/api;/p21sdk` | API + SDK access (auto-added when SDK Access is enabled) |
| `/api;/ui` | API + UI sessions |
| `/uiserver0` | Interactive and Transaction APIs only |
| `/odata` | OData endpoints (must specify tables) |
| `/api/.configuration` | Configuration endpoints only |

> **Note:** When SDK Access is enabled in SOA Admin, `/p21sdk` is automatically appended to the scope. The `/api` scope alone is sufficient for all API operations including Interactive API sessions — the `/ui` scope is not required.

### OData Table Scopes

For OData access, specify allowed tables/views:

```http
/odata:price_page,supplier,product_group
```

This restricts the token to only those tables.

---

## P21 Permissions (User Credential Auth)

When authenticating with **User Credentials** (Method 1), generating a valid token is **not sufficient** for API access. The P21 user account must also have specific permissions enabled in the P21 Desktop Client. Without these, you'll receive a generic `"You are not authorized to access API"` error even with a valid token.

> **Note:** Consumer Key authentication (Method 2) bypasses these requirements entirely. Access is controlled by the consumer key's API scope instead.

### Step 1: Application Security

Each user must be explicitly granted API access in **User Maintenance**.

1. Open **User Maintenance** in the P21 Desktop Client
2. Pull up the user's details
3. Go to the **Application Security** tab
4. Find **"Allow OData API Service"** and set it to **Yes** (default is No)

![User Maintenance - Application Security tab showing "Allow OData API Service" set to Yes](img/authorization1.jpg)

### Step 2: Role-Level Dataservice Permissions

After enabling Application Security, the user's **role** must grant access to specific tables and views.

1. Open **Role Maintenance** in the P21 Desktop Client
2. Pull up the role assigned to the user
3. Go to the **Dataservice Permission** tab
4. Set each required table/view to **Allow**

![Role Maintenance - Dataservice Permission tab showing table/view Allow/Deny settings](img/authorization2.jpg)

Key details about the Dataservice Permission screen:

- **Schema Type** dropdown filters between Tables, Views, or Both
- **Allow All** / **Allow All Views** / **Allow All Tables** checkboxes grant blanket access
- Each table/view can be individually set to **Allow** or **Deny**
- The list includes all 6000+ tables and views in the P21 database

### Permission Requirements by Auth Method

| Auth Method | Application Security | Dataservice Permission | Notes |
|-------------|---------------------|----------------------|-------|
| **User Credentials** | Required | Required | Both must be configured |
| **Consumer Key** (no username) | Not needed | Not needed | Access controlled by API scope; sufficient for OData, Entity, Inventory REST |
| **Consumer Key** (with username) | Not needed | Not needed | User must exist in P21 but doesn't need OData/Dataservice permissions; required for Interactive API |

### Troubleshooting

If you receive a `401` or `403` "not authorized" error with a valid token:

1. Verify **Allow OData API Service** = Yes in User Maintenance → Application Security
2. Verify the target table/view is set to **Allow** in Role Maintenance → Dataservice Permission
3. Ensure you're checking the correct **role** (the one actually assigned to the user)

---

## Using the Token

Include the token in the `Authorization` header for all API requests:

```http
GET /odataservice/odata/table/supplier HTTP/1.1
Host: play.p21server.com
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

<!-- tabs -->

**Python:**

```python
def get_auth_headers(token: str) -> dict:
    """Build authorization headers for API requests."""
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

# Usage
token_data = get_token_v2(base_url, username, password)
headers = get_auth_headers(token_data["AccessToken"])

response = httpx.get(
    f"{base_url}/odataservice/odata/table/supplier",
    headers=headers
)
response.raise_for_status()
```

**C#:**

```csharp
public static HttpClient CreateAuthorizedClient(string token)
{
    var client = new HttpClient();
    client.DefaultRequestHeaders.Add("Authorization", $"Bearer {token}");
    client.DefaultRequestHeaders.Add("Accept", "application/json");
    return client;
}

// Usage
var tokenData = await P21Auth.GetTokenV2Async(baseUrl, username, password);
var token = tokenData["AccessToken"]!.ToString();

using var client = CreateAuthorizedClient(token);
var response = await client.GetAsync(
    $"{baseUrl}/odataservice/odata/table/supplier");
var body = await response.Content.ReadAsStringAsync();
```

<!-- /tabs -->

---

## Token Expiration

| Property | Value |
|----------|-------|
| Default lifetime | 24 hours (86400 seconds) |
| Returned in | `ExpiresInSeconds` field |
| Refresh token | Provided for token renewal |

### Handling Expiration

<!-- tabs -->

**Python:**

```python
import time

class TokenManager:
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.token_data = None
        self.token_time = 0

    def get_token(self) -> str:
        """Get valid token, refreshing if needed."""
        now = time.time()
        expires = self.token_data.get("ExpiresInSeconds", 0) if self.token_data else 0

        # Refresh if expired or expiring in 5 minutes
        if not self.token_data or (now - self.token_time) > (expires - 300):
            self.token_data = get_token_v2(
                self.base_url, self.username, self.password
            )
            self.token_time = now

        return self.token_data["AccessToken"]
```

**C#:**

```csharp
public class TokenManager
{
    private readonly string _baseUrl;
    private readonly string _username;
    private readonly string _password;
    private JObject? _tokenData;
    private DateTime _tokenTime = DateTime.MinValue;

    public TokenManager(string baseUrl, string username, string password)
    {
        _baseUrl = baseUrl;
        _username = username;
        _password = password;
    }

    /// <summary>Get valid token, refreshing if needed.</summary>
    public async Task<string> GetTokenAsync()
    {
        var expires = _tokenData?["ExpiresInSeconds"]?.Value<int>() ?? 0;
        var elapsed = (DateTime.UtcNow - _tokenTime).TotalSeconds;

        // Refresh if expired or expiring in 5 minutes
        if (_tokenData == null || elapsed > expires - 300)
        {
            _tokenData = await P21Auth.GetTokenV2Async(
                _baseUrl, _username, _password);
            _tokenTime = DateTime.UtcNow;
        }

        return _tokenData["AccessToken"]!.ToString();
    }
}
```

<!-- /tabs -->

---

## UI Server URL

The Interactive and Transaction APIs require the UI server URL, which is obtained after authentication:

```http
GET /api/ui/router/v1?urlType=external HTTP/1.1
Host: play.p21server.com
Authorization: Bearer {token}
Accept: application/json
```

**Response:**
```json
{
    "Url": "https://play.p21server.com/uiserver0"
}
```

<!-- tabs -->

**Python:**

```python
def get_ui_server_url(base_url: str, token: str) -> str:
    """Get UI server URL for Interactive/Transaction APIs."""
    response = httpx.get(
        f"{base_url}/api/ui/router/v1?urlType=external",
        headers=get_auth_headers(token)
    )
    response.raise_for_status()
    return response.json()["Url"].rstrip("/")
```

**C#:**

```csharp
public static async Task<string> GetUiServerUrlAsync(
    string baseUrl, string token)
{
    using var client = CreateAuthorizedClient(token);
    var response = await client.GetAsync(
        $"{baseUrl}/api/ui/router/v1?urlType=external");
    response.EnsureSuccessStatusCode();

    var json = await response.Content.ReadAsStringAsync();
    var data = JObject.Parse(json);
    return data["Url"]!.ToString().TrimEnd('/');
}
```

<!-- /tabs -->

---

## XML Token Responses

Some P21 middleware instances return **XML instead of JSON** for token endpoints, even when `Accept: application/json` is set. This typically occurs with certain middleware versions or configurations.

### Example XML Response

```xml
<?xml version="1.0" encoding="utf-8"?>
<TokenResponse>
    <AccessToken>eyJhbGciOiJSUzI1NiIs...</AccessToken>
    <TokenType>Bearer</TokenType>
    <ExpiresIn>86400</ExpiresIn>
    <RefreshToken>dGhpcyBpcyBhIHNhbXBsZQ...</RefreshToken>
</TokenResponse>
```

> **Note:** The XML response uses `ExpiresIn` while the JSON response uses `ExpiresInSeconds`. Both represent the token lifetime in seconds.

### Handling Both Formats

<!-- tabs -->

**Python:**

```python
import re

def parse_token_response(response: httpx.Response) -> dict:
    """Parse token response, handling both JSON and XML formats."""
    # Try JSON first
    try:
        data = response.json()
        if isinstance(data, dict) and "AccessToken" in data:
            return data
    except (ValueError, KeyError):
        pass

    # Fall back to XML regex parsing
    text = response.text
    result = {}
    for field in ("AccessToken", "TokenType", "ExpiresIn",
                  "ExpiresInSeconds", "RefreshToken"):
        match = re.search(rf"<{field}>([^<]*)</{field}>", text)
        if match and match.group(1):
            result[field] = match.group(1)

    if "AccessToken" not in result:
        raise ValueError(f"Could not parse token from response: {text[:500]}")

    return result
```

**C#:**

```csharp
public static JObject ParseTokenResponse(HttpResponseMessage response)
{
    var text = response.Content.ReadAsStringAsync().Result;

    // Try JSON first
    try
    {
        var data = JObject.Parse(text);
        if (data["AccessToken"] != null)
            return data;
    }
    catch (JsonReaderException) { }

    // Fall back to XML regex parsing
    var result = new JObject();
    var fields = new[]
    {
        "AccessToken", "TokenType", "ExpiresIn",
        "ExpiresInSeconds", "RefreshToken"
    };

    foreach (var field in fields)
    {
        var match = System.Text.RegularExpressions.Regex.Match(
            text, $@"<{field}>([^<]*)</{field}>");
        if (match.Success && !string.IsNullOrEmpty(match.Groups[1].Value))
            result[field] = match.Groups[1].Value;
    }

    if (result["AccessToken"] == null)
        throw new InvalidOperationException(
            $"Could not parse token from response: {text[..Math.Min(text.Length, 500)]}");

    return result;
}
```

<!-- /tabs -->

---

## Common Errors

| HTTP Code | Cause | Solution |
|-----------|-------|----------|
| 401 | Invalid credentials | Check username/password |
| 401 | Expired token | Request new token |
| 401 | Invalid consumer key | Verify key in SOA Admin |
| 403 | Scope restriction | Check consumer key scope |
| 404 | Wrong endpoint | Use `/api/security/token` or `/api/security/token/v2` |
| 200 (XML body) | Middleware returning XML instead of JSON | Use dual-format parser (see [XML Token Responses](#xml-token-responses)) |

---

## Best Practices

1. **Use V2 endpoint** for new integrations
2. **Store credentials securely** — use environment variables, not code
3. **Handle token expiration** — refresh 5 minutes before expiry to avoid failed requests
4. **Use consumer keys** for service accounts — no password rotation needed
5. **Include username** when using consumer keys with Interactive or Transaction APIs — this provides audit trail attribution and is required for session creation
6. **Reuse tokens** — each call to the token endpoint creates a new middleware session; get one token and reuse it rather than requesting new tokens per-request
7. **Restrict scopes** to minimum required access
8. **Disable SSL verification** only in development (`verify=False`)
9. **Handle both JSON and XML** token responses for maximum middleware compatibility

---

## Related

- [API Selection Guide](01-API-Selection-Guide.md)
- [Error Handling](06-Error-Handling.md)
- [scripts/common/auth.py](https://github.com/mrwuss/p21-api-documentation/tree/master/scripts/common/auth.py) - Authentication module
- [scripts/common/client.py](https://github.com/mrwuss/p21-api-documentation/tree/master/scripts/common/client.py) - Reusable P21 API client with auto token refresh
