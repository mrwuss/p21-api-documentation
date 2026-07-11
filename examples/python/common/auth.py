"""
P21 API Authentication

Provides functions for obtaining and using P21 API tokens.

Two authentication methods are supported:
1. User Credentials - Username and password in the request body (V2 endpoint)
2. Consumer Key - Application key for service accounts

See docs/00-Authentication.md for full documentation.
"""

import re
import httpx
from typing import Optional

try:
    from .config import P21Config, load_config
except ImportError:
    from config import P21Config, load_config


def _parse_token_response(response: httpx.Response) -> dict:
    """Parse token response, handling both JSON and XML formats.

    Some P21 middleware instances return XML instead of JSON for token
    endpoints. This tries JSON first, then falls back to XML regex parsing.
    """
    text = response.text
    # Try JSON first
    try:
        data = response.json()
        if isinstance(data, dict) and ("AccessToken" in data or "access_token" in data):
            return data
    except (ValueError, KeyError):
        pass  # Not valid JSON or missing expected keys — fall back to XML

    # Fall back to XML regex parsing (handles namespaces, BOM, control chars)
    result = {}
    for field in ("AccessToken", "TokenType", "ExpiresIn", "ExpiresInSeconds",
                  "RefreshToken", "Scope", "SessionId", "ConsumerUid"):
        match = re.search(rf"<{field}>([^<]*)</{field}>", text)
        if match and match.group(1):
            result[field] = match.group(1)

    if "AccessToken" not in result:
        raise ValueError(f"Could not parse AccessToken from response: {text[:500]}")

    return result


def _parse_router_response(response: httpx.Response) -> str:
    """Parse the router response, handling both JSON and XML formats.

    Like the token endpoints, the router can return XML instead of JSON on
    some middleware instances. Tries JSON first, then falls back to XML
    regex parsing (mirrors _parse_token_response).
    """
    try:
        data = response.json()
        if isinstance(data, dict) and data.get("Url"):
            return data["Url"]
    except (ValueError, KeyError):
        pass  # Not valid JSON — fall back to XML

    match = re.search(r"<Url>([^<]+)</Url>", response.text)
    if match:
        return match.group(1)

    raise ValueError(f"Could not parse Url from router response: {response.text[:500]}")


def get_token(
    config: Optional[P21Config] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    consumer_key: Optional[str] = None,
    use_v2: bool = True
) -> dict:
    """
    Obtain an access token from P21.

    Args:
        config: P21Config object. If not provided, loads from environment.
        username: Override username from config
        password: Override password from config
        consumer_key: Use consumer key authentication instead of credentials
        use_v2: Use V2 endpoint (credentials in body). Defaults to True.
            Password auth REQUIRES V2 — the V1 endpoint puts credentials in
            HTTP headers, which proxies and log pipelines capture. V1 is only
            allowed for consumer-key (appkey header) authentication.

    Returns:
        dict: Token response containing:
            - AccessToken: Bearer token for API calls
            - RefreshToken: Token for refreshing access
            - ExpiresInSeconds: Token lifetime
            - TokenType: Always "Bearer"

    Raises:
        httpx.HTTPStatusError: If authentication fails

    Example:
        >>> token_data = get_token()
        >>> print(token_data["AccessToken"][:50])
        'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1bmlxdWV...'
    """
    if config is None:
        config = load_config()

    with httpx.Client(verify=config.verify_ssl, follow_redirects=True) as client:
        if use_v2:
            # V2 endpoint - credentials in body (recommended)
            url = f"{config.base_url}/api/security/token/v2"

            if consumer_key:
                body = {
                    "ClientSecret": consumer_key,
                    "GrantType": "client_credentials"
                }
                if username:
                    body["username"] = username
            else:
                body = {
                    "username": username or config.username,
                    "password": password or config.password
                }

            response = client.post(
                url,
                json=body,
                headers={"Accept": "application/json"}
            )
        else:
            # V1 endpoint - only valid for consumer-key (appkey header) auth.
            # Username/password in headers is a security risk (headers get
            # logged by proxies) and is deliberately not supported here.
            if not consumer_key:
                raise ValueError(
                    "Password authentication requires the V2 endpoint "
                    "(credentials in the request body). The V1 endpoint puts "
                    "username/password in HTTP headers, which get captured by "
                    "proxies and logs. Call get_token() with use_v2=True "
                    "(the default)."
                )

            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "appkey": consumer_key,
            }
            if username:
                headers["username"] = username

            response = client.post(
                config.token_url,
                headers=headers,
                content=""
            )

        response.raise_for_status()
        return _parse_token_response(response)


def get_auth_headers(token: str) -> dict:
    """
    Build authorization headers for API requests.

    Args:
        token: Access token from get_token()

    Returns:
        dict: Headers to include in API requests

    Example:
        >>> token_data = get_token()
        >>> headers = get_auth_headers(token_data["AccessToken"])
        >>> # Use headers in subsequent API calls
    """
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }


def get_ui_server_url(base_url: str, token: str, verify_ssl: bool = False) -> str:
    """
    Get the UI server URL for Interactive/Transaction API calls.

    The UI server URL is required for:
    - Interactive API session management
    - Transaction API operations

    Args:
        base_url: P21 base URL
        token: Access token
        verify_ssl: Whether to verify SSL certificates

    Returns:
        str: UI server URL (e.g., "https://play.p21server.com/uiserver0")

    Example:
        >>> token_data = get_token()
        >>> ui_url = get_ui_server_url(config.base_url, token_data["AccessToken"])
        >>> print(ui_url)
        'https://play.p21server.com/uiserver0'
    """
    with httpx.Client(verify=verify_ssl, follow_redirects=True) as client:
        response = client.get(
            f"{base_url}/api/ui/router/v1?urlType=external",
            headers=get_auth_headers(token)
        )
        response.raise_for_status()
        # Router may respond with JSON or XML — handle both
        return _parse_router_response(response).rstrip("/")


if __name__ == "__main__":
    # Test authentication
    import warnings
    warnings.filterwarnings("ignore")

    print("Testing P21 Authentication")
    print("=" * 50)

    try:
        config = load_config()
        print(f"Server: {config.base_url}")

        # Get token
        print("\n1. Getting access token...")
        token_data = get_token(config)
        print(f"   Token type: {token_data.get('TokenType', 'N/A')}")
        print(f"   Expires in: {token_data.get('ExpiresInSeconds', 'N/A')} seconds")
        print(f"   Access token: {token_data['AccessToken'][:50]}...")

        # Get UI server
        print("\n2. Getting UI server URL...")
        ui_url = get_ui_server_url(
            config.base_url,
            token_data["AccessToken"],
            config.verify_ssl
        )
        print(f"   UI Server: {ui_url}")

        print("\n" + "=" * 50)
        print("Authentication successful!")

    except httpx.HTTPStatusError as e:
        print(f"\nAuthentication failed: {e.response.status_code}")
        print(f"Response: {e.response.text[:200]}")
    except Exception as e:
        print(f"\nError: {e}")
