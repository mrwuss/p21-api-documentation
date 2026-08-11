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

### V1 Endpoint (Deprecated-Security Risk)

```http
POST https://{hostname}/api/security/token
```

> **Security Warning:** The V1 endpoint transmits credentials in HTTP **headers**. Headers are routinely logged by reverse proxies, load balancers, WAFs, and middleware — meaning usernames and passwords can end up in access logs, error logs, and monitoring dashboards. **Always use V2** for new integrations. V1 is documented here only for reference with legacy systems.

> **On 2026.1, don't let a session failure talk you back onto V1.** Interactive session-create returns an **empty HTTP 500 when the request lacks `Accept: application/json`**, which reads convincingly as "our V2 tokens stopped working on 26.1". It isn't a token problem: a V2 token opens sessions normally once the header is present (verified on 26.1.5910.3). A production integration misdiagnosed this and fell back to V1 before a controlled same-token test found the header.
>
> Downgrading costs you twice — credentials in headers, **and** per-operator attribution, since the V1 endpoint has no consumer key and every write lands against the service account. Two requests tell them apart: same token to session-create, once with `Accept` and once without. See [Breaking Changes § 2026.1 entry 1](14-Breaking-Changes.md#1-interactive-api-returns-an-empty-http-500-without-an-explicit-accept-applicationjson-header).

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

### V1 Request (Legacy — Not Recommended)

> **Do not use this pattern.** Credentials are in headers — see [security warning above](#v1-endpoint-deprecated-security-risk). The raw request below is shown for reference only (e.g., to recognize it in legacy code), deliberately without helper code. New integrations must use the V2 endpoint.

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
"""Get a P21 token via the V2 endpoint and print what came back."""
import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
# ---------------------------------------------------------------------------


def get_token_v2(base_url: str, username: str, password: str) -> dict:
    """Get token using V2 endpoint (recommended)."""
    response = httpx.post(
        f"{base_url}/api/security/token/v2",
        json={"username": username, "password": password},
        headers={"Accept": "application/json"},
        verify=VERIFY_SSL,
    )
    response.raise_for_status()
    return response.json()


# No V1 helper is provided — the V1 endpoint puts credentials in
# HTTP headers, which get logged by proxies and middleware.

if __name__ == "__main__":
    token_data = get_token_v2(BASE_URL, USERNAME, PASSWORD)
    print("TokenType:", token_data.get("TokenType"))
    print("ExpiresInSeconds:", token_data.get("ExpiresInSeconds"))
    print("AccessToken (truncated):", token_data["AccessToken"][:20] + "...")
```

**C#:**

```csharp
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
// ---------------------------------------------------------------------------

using var client = new HttpClient();
var tokenData = await GetTokenV2Async(client, BaseUrl, Username, Password);
Console.WriteLine($"TokenType: {tokenData.GetProperty("TokenType").GetString()}");
Console.WriteLine($"ExpiresInSeconds: {tokenData.GetProperty("ExpiresInSeconds").GetInt64()}");
var accessToken = tokenData.GetProperty("AccessToken").GetString() ?? "";
Console.WriteLine($"AccessToken (truncated): {accessToken[..Math.Min(20, accessToken.Length)]}...");

// No V1 helper is provided — the V1 endpoint puts credentials in
// HTTP headers, which get logged by proxies and middleware.

// --- helpers ---------------------------------------------------------------

/// <summary>Get token using V2 endpoint (recommended).</summary>
static async Task<JsonElement> GetTokenV2Async(
    HttpClient client, string baseUrl, string username, string password)
{
    var body = new { username, password };
    var content = new StringContent(
        JsonSerializer.Serialize(body),
        Encoding.UTF8, "application/json");
    client.DefaultRequestHeaders.Add("Accept", "application/json");

    var response = await client.PostAsync(
        $"{baseUrl}/api/security/token/v2", content);
    response.EnsureSuccessStatusCode();

    var json = await response.Content.ReadAsStringAsync();
    using var doc = JsonDocument.Parse(json);
    return doc.RootElement.Clone();
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
| **Consumer** | Descriptive name (e.g., `MY_SERVICE_APP`) | Use a name that identifies the integration |
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
    "ClientSecret": "00000000-1111-2222-3333-444444444444",
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

> **Important:** The `username` must be a **real P21 user account** — not the consumer name. For example, if your consumer is named `MY_SERVICE_APP`, you still need a P21 user like `svc_api` or `api_user` in the username field. The token endpoint accepts any string, but session creation will fail with `Error retrieving/validating user` if the user doesn't exist in P21.

```http
POST /api/security/token/v2 HTTP/1.1
Host: play.p21server.com
Content-Type: application/json
Accept: application/json

{
    "ClientSecret": "00000000-1111-2222-3333-444444444444",
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
"""Get a P21 token via consumer key authentication and print what came back."""
import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"                       # your P21 server
CONSUMER_KEY = "00000000-1111-2222-3333-444444444444"          # from SOA Admin
USERNAME = "apiuser"                                           # "" to omit (required for Interactive API)
VERIFY_SSL = False                                              # True once you trust the cert chain
# ---------------------------------------------------------------------------


def get_consumer_token(
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

    response = httpx.post(
        f"{base_url}/api/security/token/v2",
        json=payload,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        verify=VERIFY_SSL,
    )
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    token_data = get_consumer_token(BASE_URL, CONSUMER_KEY, USERNAME)
    print("TokenType:", token_data.get("TokenType"))
    print("ExpiresIn:", token_data.get("ExpiresIn"))
    print("UserName:", token_data.get("UserName"))
    print("AccessToken (truncated):", token_data["AccessToken"][:20] + "...")
```

**C#:**

```csharp
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";                // your P21 server
const string ConsumerKey = "00000000-1111-2222-3333-444444444444";  // from SOA Admin
const string Username = "apiuser";                                   // "" to omit (required for Interactive API)
// ---------------------------------------------------------------------------

using var client = new HttpClient();
var tokenData = await GetConsumerTokenAsync(client, BaseUrl, ConsumerKey, Username);
Console.WriteLine($"TokenType: {tokenData.GetProperty("TokenType").GetString()}");
Console.WriteLine($"ExpiresIn: {tokenData.GetProperty("ExpiresIn").GetInt64()}");
Console.WriteLine($"UserName: {tokenData.GetProperty("UserName").GetString()}");
var accessToken = tokenData.GetProperty("AccessToken").GetString() ?? "";
Console.WriteLine($"AccessToken (truncated): {accessToken[..Math.Min(20, accessToken.Length)]}...");

// --- helpers ---------------------------------------------------------------

/// <summary>Get token using consumer key authentication.</summary>
/// <param name="client">HttpClient to use for the request</param>
/// <param name="baseUrl">P21 server URL</param>
/// <param name="consumerKey">Consumer key GUID from SOA Admin</param>
/// <param name="username">Optional P21 username (required for Interactive API)</param>
static async Task<JsonElement> GetConsumerTokenAsync(
    HttpClient client, string baseUrl, string consumerKey, string username = "")
{
    var payload = new Dictionary<string, string>
    {
        ["GrantType"] = "client_credentials",
        ["ClientSecret"] = consumerKey
    };
    if (!string.IsNullOrEmpty(username))
        payload["username"] = username;

    var content = new StringContent(
        JsonSerializer.Serialize(payload),
        Encoding.UTF8, "application/json");
    client.DefaultRequestHeaders.Add("Accept", "application/json");

    var response = await client.PostAsync(
        $"{baseUrl}/api/security/token/v2", content);
    response.EnsureSuccessStatusCode();

    var json = await response.Content.ReadAsStringAsync();
    using var doc = JsonDocument.Parse(json);
    return doc.RootElement.Clone();
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

> **`Accept: application/json` is not optional on 2026.1.** Every example in this documentation sends it; on P21 **2026.1** the Interactive API returns an **empty HTTP 500** for any request whose `Accept` header doesn't include `application/json` — including the `Accept: */*` default of httpx and .NET HttpClient — and the failed session create leaves a ghost session behind. Set it in one shared header builder rather than per call site. See [Breaking Changes § 2026.1](14-Breaking-Changes.md#p21-20261).



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
"""Build authorization headers from a token and use them to call OData."""
import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
# ---------------------------------------------------------------------------


def get_token_v2(base_url: str, username: str, password: str) -> dict:
    """Get token using V2 endpoint (recommended)."""
    response = httpx.post(
        f"{base_url}/api/security/token/v2",
        json={"username": username, "password": password},
        headers={"Accept": "application/json"},
        verify=VERIFY_SSL,
    )
    response.raise_for_status()
    return response.json()


def get_auth_headers(token: str) -> dict:
    """Build authorization headers for API requests."""
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }


if __name__ == "__main__":
    token_data = get_token_v2(BASE_URL, USERNAME, PASSWORD)
    headers = get_auth_headers(token_data["AccessToken"])

    response = httpx.get(
        f"{BASE_URL}/odataservice/odata/table/supplier",
        headers=headers,
        verify=VERIFY_SSL,
    )
    response.raise_for_status()
    print(response.json())
```

**C#:**

```csharp
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
// ---------------------------------------------------------------------------

using var authClient = new HttpClient();
var tokenData = await GetTokenV2Async(authClient, BaseUrl, Username, Password);
var token = tokenData.GetProperty("AccessToken").GetString() ?? "";

using var client = CreateAuthorizedClient(token);
var response = await client.GetAsync(
    $"{BaseUrl}/odataservice/odata/table/supplier");
response.EnsureSuccessStatusCode();
var body = await response.Content.ReadAsStringAsync();
Console.WriteLine(body);

// --- helpers ---------------------------------------------------------------

static HttpClient CreateAuthorizedClient(string token)
{
    var client = new HttpClient();
    client.DefaultRequestHeaders.Add("Authorization", $"Bearer {token}");
    client.DefaultRequestHeaders.Add("Accept", "application/json");
    return client;
}

/// <summary>Get token using V2 endpoint (recommended).</summary>
static async Task<JsonElement> GetTokenV2Async(
    HttpClient client, string baseUrl, string username, string password)
{
    var body = new { username, password };
    var content = new StringContent(
        JsonSerializer.Serialize(body),
        Encoding.UTF8, "application/json");
    client.DefaultRequestHeaders.Add("Accept", "application/json");

    var response = await client.PostAsync(
        $"{baseUrl}/api/security/token/v2", content);
    response.EnsureSuccessStatusCode();

    var json = await response.Content.ReadAsStringAsync();
    using var doc = JsonDocument.Parse(json);
    return doc.RootElement.Clone();
}
```

<!-- /tabs -->

---

## Token Lifetime and Reuse

### Token TTL

The token response includes an expiry field indicating how long the token remains valid, in seconds. The field name varies by auth flow and middleware format: user credential JSON responses use `ExpiresInSeconds`, consumer key JSON responses use `ExpiresIn`, and XML responses also use `ExpiresIn`. Always check for both field names when parsing (see the `TokenManager` examples below).

| Auth Method | Typical TTL | Notes |
|-------------|-------------|-------|
| **User Credentials** | 86,400 seconds (24 hours) | Configurable per server |
| **Consumer Key** | 630,720,000 seconds (20 years) | When set to "Never Expire" in SOA Admin |

> **Important:** Always read the expiry field (`ExpiresInSeconds` or `ExpiresIn`) from the response rather than hardcoding a TTL value. The default varies by server configuration and P21 version.

### Why Reuse Tokens

Authenticate **once** at the start of your application or script and reuse that token for all subsequent API calls.

- **Middleware sessions** — each call to `/api/security/token/v2` creates a new middleware session. Excessive token requests waste server resources and may invalidate previous sessions.
- **Rate limiting** — frequent authentication requests may trigger server-side throttling.
- **Performance** — token acquisition involves a network round-trip and credential validation. Reusing a cached token avoids this overhead on every API call.

### Multi-API Reuse

A single token works across **all** P21 APIs. You do not need separate tokens per API.

| API | Same Token? |
|-----|-------------|
| OData | Yes |
| Transaction | Yes |
| Interactive | Yes (requires username in token request) |
| Entity | Yes |
| Inventory REST | Yes |

### Token Refresh

When a token expires or is about to expire, re-authenticate to get a new one. The token response may include a `RefreshToken` field, but most P21 integrations simply re-authenticate with credentials since the token endpoint is lightweight.

**Recommended approach:** Check the token's remaining lifetime before each request and re-authenticate when the token is within 5 minutes of expiry. This avoids mid-request failures from an expired token.

### Token Manager Pattern

The following pattern caches the token, checks expiry with a 5-minute buffer before each request, and automatically re-authenticates when needed.

<!-- tabs -->

**Python:**

```python
"""Cache a P21 token, auto-refresh before it expires, and reuse it across calls."""
import time

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
# ---------------------------------------------------------------------------

# Buffer in seconds — re-authenticate this far before actual expiry
TOKEN_REFRESH_BUFFER = 300  # 5 minutes


class TokenManager:
    """Manages P21 token lifecycle with automatic refresh.

    Caches the token and re-authenticates when the token is
    within TOKEN_REFRESH_BUFFER seconds of expiry.
    """

    def __init__(self, base_url: str, username: str, password: str) -> None:
        self.base_url = base_url
        self.username = username
        self.password = password
        self._token_data: dict | None = None
        self._token_acquired_at: float = 0.0

    def _is_token_valid(self) -> bool:
        """Check if the cached token is still valid (with buffer)."""
        if self._token_data is None:
            return False
        expires_raw = self._token_data.get(
            "ExpiresInSeconds",
            self._token_data.get("ExpiresIn", 0),
        )
        try:
            expires_in = int(expires_raw)
        except (TypeError, ValueError):
            expires_in = 3600
        elapsed = time.time() - self._token_acquired_at
        return elapsed < (expires_in - TOKEN_REFRESH_BUFFER)

    def _authenticate(self) -> None:
        """Request a new token from the P21 token endpoint."""
        response = httpx.post(
            f"{self.base_url}/api/security/token/v2",
            json={"username": self.username, "password": self.password},
            headers={"Accept": "application/json"},
        )
        response.raise_for_status()
        self._token_data = response.json()
        self._token_acquired_at = time.time()

    def get_token(self) -> str:
        """Get a valid access token, refreshing if needed."""
        if not self._is_token_valid():
            self._authenticate()
        return self._token_data["AccessToken"]

    def get_headers(self) -> dict[str, str]:
        """Get authorization headers with a valid token."""
        return {
            "Authorization": f"Bearer {self.get_token()}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }


if __name__ == "__main__":
    # Usage — authenticate once, reuse for all API calls
    manager = TokenManager(
        base_url=BASE_URL,
        username=USERNAME,
        password=PASSWORD,
    )

    # OData query
    odata_resp = httpx.get(
        f"{BASE_URL}/odataservice/odata/table/supplier",
        headers=manager.get_headers(),
    )
    odata_resp.raise_for_status()
    print("OData status:", odata_resp.status_code)

    # Entity API query — same token, no re-authentication
    entity_resp = httpx.get(
        f"{BASE_URL}/api/entity/customers/",
        headers=manager.get_headers(),
    )
    entity_resp.raise_for_status()
    print("Entity API status:", entity_resp.status_code)
```

**C#:**

```csharp
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
// ---------------------------------------------------------------------------

// Usage — one long-lived HttpClient, per-request auth (always fresh token)
var manager = new TokenManager(BaseUrl, Username, Password);
using var client = new HttpClient();

// OData query
var odataReq = new HttpRequestMessage(
    HttpMethod.Get, $"{BaseUrl}/odataservice/odata/table/supplier");
await manager.ApplyAuthAsync(odataReq);
var odataResp = await client.SendAsync(odataReq);
odataResp.EnsureSuccessStatusCode();
Console.WriteLine($"OData status: {(int)odataResp.StatusCode}");

// Entity API query — same token, no re-authentication
var entityReq = new HttpRequestMessage(
    HttpMethod.Get, $"{BaseUrl}/api/entity/customers/");
await manager.ApplyAuthAsync(entityReq);
var entityResp = await client.SendAsync(entityReq);
entityResp.EnsureSuccessStatusCode();
Console.WriteLine($"Entity API status: {(int)entityResp.StatusCode}");

// --- helpers ---------------------------------------------------------------

/// <summary>
/// Manages P21 token lifecycle with automatic refresh.
/// Caches the token and re-authenticates when the token is
/// within RefreshBufferSeconds of expiry.
/// </summary>
class TokenManager
{
    // Re-authenticate this far before actual expiry
    private const int RefreshBufferSeconds = 300; // 5 minutes

    private readonly string _baseUrl;
    private readonly string _username;
    private readonly string _password;
    private JsonElement? _tokenData;
    private DateTime _tokenAcquiredAt = DateTime.MinValue;

    public TokenManager(string baseUrl, string username, string password)
    {
        _baseUrl = baseUrl;
        _username = username;
        _password = password;
    }

    private bool IsTokenValid()
    {
        if (_tokenData == null) return false;
        var data = _tokenData.Value;
        var expiresIn = data.TryGetProperty("ExpiresInSeconds", out var expSeconds) ? expSeconds.GetInt64()
                       : data.TryGetProperty("ExpiresIn", out var expires) ? expires.GetInt64()
                       : 0;
        var elapsed = (DateTime.UtcNow - _tokenAcquiredAt).TotalSeconds;
        return elapsed < (expiresIn - RefreshBufferSeconds);
    }

    private async Task AuthenticateAsync()
    {
        // Short-lived HttpClient is acceptable here — token refresh is infrequent
        // (once per TTL, typically 24h+ for user credentials, 20y for consumer keys).
        using var client = new HttpClient();
        var body = new { username = _username, password = _password };
        var content = new StringContent(
            JsonSerializer.Serialize(body),
            Encoding.UTF8, "application/json");
        client.DefaultRequestHeaders.Add("Accept", "application/json");

        var response = await client.PostAsync(
            $"{_baseUrl}/api/security/token/v2", content);
        response.EnsureSuccessStatusCode();

        var json = await response.Content.ReadAsStringAsync();
        using var doc = JsonDocument.Parse(json);
        _tokenData = doc.RootElement.Clone();
        _tokenAcquiredAt = DateTime.UtcNow;
    }

    /// <summary>Get a valid access token, refreshing if needed.</summary>
    public async Task<string> GetTokenAsync()
    {
        if (!IsTokenValid())
            await AuthenticateAsync();
        return _tokenData!.Value.GetProperty("AccessToken").GetString()!;
    }

    /// <summary>Apply auth to a request, refreshing the token if needed.</summary>
    public async Task ApplyAuthAsync(HttpRequestMessage request)
    {
        var token = await GetTokenAsync();
        request.Headers.Authorization =
            new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", token);
        if (!request.Headers.Contains("Accept"))
            request.Headers.Add("Accept", "application/json");
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

> **307 redirect gotcha:** On some installations, `GET /api/ui/router/v1?urlType=external` (no trailing slash after `v1`) responds with a **307 redirect** to the trailing-slash form. HTTP clients that do not follow redirects by default — including `httpx` — receive the 307 and an HTML body instead of the JSON response. Either request `/api/ui/router/v1/?urlType=external` (trailing slash) directly, or enable redirect following (`httpx.get(..., follow_redirects=True)`). C# `HttpClient` follows GET redirects by default and is unaffected. Verified live on a 25.2 system (July 2026).

> **XML responses:** As with the token endpoint, some middleware returns **XML** for the router response even with `Accept: application/json`. Parse JSON first and fall back to XML (see [XML Token Responses](#xml-token-responses)).

<!-- tabs -->

**Python:**

```python
"""Resolve the P21 UI server URL needed for Interactive/Transaction API calls."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
# ---------------------------------------------------------------------------


def get_token_v2(base_url: str, username: str, password: str) -> dict:
    """Get token using V2 endpoint (recommended)."""
    response = httpx.post(
        f"{base_url}/api/security/token/v2",
        json={"username": username, "password": password},
        headers={"Accept": "application/json"},
        verify=VERIFY_SSL,
    )
    response.raise_for_status()
    return response.json()


def get_auth_headers(token: str) -> dict:
    """Build authorization headers for API requests."""
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }


def get_ui_server_url(base_url: str, token: str) -> str:
    """Get UI server URL for Interactive/Transaction APIs."""
    response = httpx.get(
        f"{base_url}/api/ui/router/v1/?urlType=external",  # trailing slash avoids a 307
        headers=get_auth_headers(token),
        follow_redirects=True,
        verify=VERIFY_SSL,
    )
    response.raise_for_status()
    # Try JSON first; some middleware returns XML (like the token endpoint)
    try:
        return response.json()["Url"].rstrip("/")
    except (ValueError, KeyError):
        match = re.search(r"<Url>([^<]+)</Url>", response.text)
        if not match:
            raise ValueError(
                f"Could not parse router response: {response.text[:500]}")
        return match.group(1).rstrip("/")


if __name__ == "__main__":
    token_data = get_token_v2(BASE_URL, USERNAME, PASSWORD)
    ui_server = get_ui_server_url(BASE_URL, token_data["AccessToken"])
    print("UI server URL:", ui_server)
```

**C#:**

```csharp
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
// ---------------------------------------------------------------------------

using var authClient = new HttpClient();
var tokenData = await GetTokenV2Async(authClient, BaseUrl, Username, Password);
var token = tokenData.GetProperty("AccessToken").GetString() ?? "";

var uiServer = await GetUiServerUrlAsync(BaseUrl, token);
Console.WriteLine($"UI server URL: {uiServer}");

// --- helpers ---------------------------------------------------------------

static HttpClient CreateAuthorizedClient(string token)
{
    var client = new HttpClient();
    client.DefaultRequestHeaders.Add("Authorization", $"Bearer {token}");
    client.DefaultRequestHeaders.Add("Accept", "application/json");
    return client;
}

static async Task<string> GetUiServerUrlAsync(string baseUrl, string token)
{
    using var client = CreateAuthorizedClient(token);
    var response = await client.GetAsync(
        $"{baseUrl}/api/ui/router/v1?urlType=external");
    response.EnsureSuccessStatusCode();

    // Some middleware returns XML here even when asked for JSON, so try JSON
    // first and fall back to regex extraction of <Url> (same pattern as
    // ParseTokenResponse below).
    var payload = await response.Content.ReadAsStringAsync();
    try
    {
        using var doc = JsonDocument.Parse(payload);
        var url = doc.RootElement.GetProperty("Url").GetString();
        if (!string.IsNullOrEmpty(url)) return url.TrimEnd('/');
    }
    catch (Exception ex) when (ex is JsonException or KeyNotFoundException) { }

    var match = System.Text.RegularExpressions.Regex.Match(payload, "<Url>([^<]+)</Url>");
    if (!match.Success)
        throw new InvalidOperationException(
            $"Could not parse router response: {payload[..Math.Min(500, payload.Length)]}");
    return match.Groups[1].Value.TrimEnd('/');
}

/// <summary>Get token using V2 endpoint (recommended).</summary>
static async Task<JsonElement> GetTokenV2Async(
    HttpClient client, string baseUrl, string username, string password)
{
    var body = new { username, password };
    var content = new StringContent(
        JsonSerializer.Serialize(body),
        Encoding.UTF8, "application/json");
    client.DefaultRequestHeaders.Add("Accept", "application/json");

    var response = await client.PostAsync(
        $"{baseUrl}/api/security/token/v2", content);
    response.EnsureSuccessStatusCode();

    var json = await response.Content.ReadAsStringAsync();
    using var doc = JsonDocument.Parse(json);
    return doc.RootElement.Clone();
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

> **Note:** XML responses use `ExpiresIn`, user credential JSON responses use `ExpiresInSeconds`, and consumer key JSON responses use `ExpiresIn`. All represent the token lifetime in seconds.

### Handling Both Formats

<!-- tabs -->

**Python:**

```python
"""Get a token response and parse it whether the middleware answers JSON or XML."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
# ---------------------------------------------------------------------------


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


if __name__ == "__main__":
    raw_response = httpx.post(
        f"{BASE_URL}/api/security/token/v2",
        json={"username": USERNAME, "password": PASSWORD},
        headers={"Accept": "application/json"},
        verify=VERIFY_SSL,
    )
    raw_response.raise_for_status()
    token_data = parse_token_response(raw_response)
    print("TokenType:", token_data.get("TokenType"))
    print("AccessToken (truncated):", token_data["AccessToken"][:20] + "...")
```

**C#:**

```csharp
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
// ---------------------------------------------------------------------------

using var client = new HttpClient();
var body = new { username = Username, password = Password };
var content = new StringContent(
    JsonSerializer.Serialize(body),
    Encoding.UTF8, "application/json");
client.DefaultRequestHeaders.Add("Accept", "application/json");

var response = await client.PostAsync($"{BaseUrl}/api/security/token/v2", content);
response.EnsureSuccessStatusCode();
var tokenData = ParseTokenResponse(response);
var tokenType = tokenData.TryGetProperty("TokenType", out var tokenTypeEl) ? tokenTypeEl.GetString() : null;
Console.WriteLine($"TokenType: {tokenType}");
var accessToken = tokenData.GetProperty("AccessToken").GetString() ?? "";
Console.WriteLine($"AccessToken (truncated): {accessToken[..Math.Min(20, accessToken.Length)]}...");

// --- helpers ---------------------------------------------------------------

static JsonElement ParseTokenResponse(HttpResponseMessage response)
{
    var text = response.Content.ReadAsStringAsync().Result;

    // Try JSON first
    try
    {
        using var parsed = JsonDocument.Parse(text);
        if (parsed.RootElement.TryGetProperty("AccessToken", out _))
            return parsed.RootElement.Clone();
    }
    catch (JsonException) { }

    // Fall back to XML regex parsing
    var result = new Dictionary<string, string>();
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

    if (!result.ContainsKey("AccessToken"))
        throw new InvalidOperationException(
            $"Could not parse token from response: {text[..Math.Min(text.Length, 500)]}");

    using var doc = JsonDocument.Parse(JsonSerializer.Serialize(result));
    return doc.RootElement.Clone();
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
| 404 | Wrong endpoint | Use `/api/security/token/v2` |
| 200 (XML body) | Middleware returning XML instead of JSON | Use dual-format parser (see [XML Token Responses](#xml-token-responses)) |

---

## Best Practices

1. **Use V2 endpoint** for new integrations
2. **Store credentials securely** — use environment variables, not code
3. **Handle token expiration** — refresh 5 minutes before expiry to avoid failed requests (see [Token Lifetime and Reuse](#token-lifetime-and-reuse))
4. **Use consumer keys** for service accounts — no password rotation needed
5. **Include username** when using consumer keys with Interactive or Transaction APIs — this provides audit trail attribution and is required for session creation
6. **Reuse tokens** — each call to the token endpoint creates a new middleware session; get one token and reuse it across all P21 APIs rather than requesting new tokens per-request (see [Token Lifetime and Reuse](#token-lifetime-and-reuse))
7. **Restrict scopes** to minimum required access
8. **Disable SSL verification** only in development (`verify=False`)
9. **Handle both JSON and XML** token responses for maximum middleware compatibility

---

## Related

- [API Selection Guide](01-API-Selection-Guide.md)
- [Error Handling](06-Error-Handling.md)
- [examples/python/common/auth.py](https://github.com/mrwuss/p21-api-documentation/tree/master/examples/python/common/auth.py) - Authentication module
- [examples/python/common/client.py](https://github.com/mrwuss/p21-api-documentation/tree/master/examples/python/common/client.py) - Reusable P21 API client with auto token refresh
