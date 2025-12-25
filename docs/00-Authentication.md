# P21 API Authentication

## Overview

All P21 APIs require authentication via Bearer tokens. This guide covers the two authentication methods:

1. **User Credentials** - Username and password authentication
2. **Consumer Key** - Pre-authenticated application key

## Token Endpoints

### V2 Endpoint (Recommended)

```
POST https://{hostname}/api/security/token/v2
```

The V2 endpoint accepts credentials in the request body.

### V1 Endpoint (Deprecated)

```
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
Host: play.ifpusa.com
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
Host: play.ifpusa.com
username: api_user
password: your_password
Content-Type: application/json
Accept: application/json
```

**Response:** Same as V2.

### Python Example

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

---

## Method 2: Consumer Key

Use for service accounts and automated integrations. Consumer keys are created in the SOA Admin console.

### Creating a Consumer Key

1. Log in to SOA Admin Page (`https://{hostname}/api/admin`)
2. Open the **API Console** tab
3. Click **Register Consumer Key**
4. Configure:
   - **Consumer**: Descriptive name
   - **SDK Access**: Enable for SDK access
   - **Token Expire**: Key validity duration
   - **API Scope**: Restrict access (see Scopes section)

### Request

```http
POST /api/security/token/v2 HTTP/1.1
Host: play.ifpusa.com
Content-Type: application/json
Accept: application/json

{
    "ClientSecret": "62ccc18a-25e2-440c-bf6d-749c117fa9db",
    "GrantType": "client_credentials"
}
```

With optional username (required for Interactive API):
```json
{
    "ClientSecret": "62ccc18a-25e2-440c-bf6d-749c117fa9db",
    "GrantType": "client_credentials",
    "username": "api_user"
}
```

### API-Specific Behavior

| API | Without Username | With Username |
|-----|------------------|---------------|
| **OData** | Works - uses consumer key scope | Username ignored |
| **Transaction** | Works - uses P21 install user | Uses specified user |
| **Interactive** | **Does not work** - username required | Works |
| **Entity** | Works - uses admin by default | Uses specified user |

---

## API Scopes

Consumer keys can restrict access to specific endpoints and data.

### URL Scopes

| Scope | Access |
|-------|--------|
| `/api` | All API endpoints |
| `/uiserver0` | Interactive and Transaction APIs |
| `/odata` | OData endpoints (must specify tables) |
| `/api;/uiserver0` | Multiple scopes (semicolon delimiter) |

### OData Table Scopes

For OData access, specify allowed tables/views:

```
/odata:price_page,supplier,product_group
```

This restricts the token to only those tables.

---

## Using the Token

Include the token in the `Authorization` header for all API requests:

```http
GET /odataservice/odata/table/supplier HTTP/1.1
Host: play.ifpusa.com
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

### Python Example

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
```

---

## Token Expiration

| Property | Value |
|----------|-------|
| Default lifetime | 24 hours (86400 seconds) |
| Returned in | `ExpiresInSeconds` field |
| Refresh token | Provided for token renewal |

### Handling Expiration

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

---

## UI Server URL

The Interactive and Transaction APIs require the UI server URL, which is obtained after authentication:

```http
GET /api/ui/router/v1?urlType=external HTTP/1.1
Host: play.ifpusa.com
Authorization: Bearer {token}
Accept: application/json
```

**Response:**
```json
{
    "Url": "https://play.ifpusa.com/uiserver0"
}
```

### Python Example

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

---

## Common Errors

| HTTP Code | Cause | Solution |
|-----------|-------|----------|
| 401 | Invalid credentials | Check username/password |
| 401 | Expired token | Request new token |
| 401 | Invalid consumer key | Verify key in SOA Admin |
| 403 | Scope restriction | Check consumer key scope |
| 404 | Wrong endpoint | Use `/api/security/token` or `/api/security/token/v2` |

---

## Best Practices

1. **Use V2 endpoint** for new integrations
2. **Store credentials securely** - use environment variables, not code
3. **Handle token expiration** - refresh before expiry
4. **Use consumer keys** for service accounts
5. **Restrict scopes** to minimum required access
6. **Disable SSL verification** only in development (`verify=False`)

---

## Related

- [API Selection Guide](01-API-Selection-Guide.md)
- [Error Handling](06-Error-Handling.md)
- [scripts/common/auth.py](../scripts/common/auth.py) - Authentication module
