"""
P21 API Authentication

Provides functions for obtaining and using P21 API tokens.

Two authentication methods are supported:
1. User Credentials - Username and password in headers
2. Consumer Key - Application key for service accounts

See docs/00-Authentication.md for full documentation.
"""

import httpx
from typing import Optional

try:
    from .config import P21Config, load_config
except ImportError:
    from config import P21Config, load_config


def get_token(
    config: Optional[P21Config] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    consumer_key: Optional[str] = None,
    use_v2: bool = False
) -> dict:
    """
    Obtain an access token from P21.

    Args:
        config: P21Config object. If not provided, loads from environment.
        username: Override username from config
        password: Override password from config
        consumer_key: Use consumer key authentication instead of credentials
        use_v2: Use V2 endpoint (credentials in body). Default False uses V1.

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
            # V1 endpoint - credentials in headers (legacy but widely used)
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }

            if consumer_key:
                headers["appkey"] = consumer_key
                if username:
                    headers["username"] = username
            else:
                headers["username"] = username or config.username
                headers["password"] = password or config.password

            response = client.post(
                config.token_url,
                headers=headers,
                content=""
            )

        response.raise_for_status()
        return response.json()


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
        str: UI server URL (e.g., "https://play.ifpusa.com/uiserver0")

    Example:
        >>> token_data = get_token()
        >>> ui_url = get_ui_server_url(config.base_url, token_data["AccessToken"])
        >>> print(ui_url)
        'https://play.ifpusa.com/uiserver0'
    """
    with httpx.Client(verify=verify_ssl, follow_redirects=True) as client:
        response = client.get(
            f"{base_url}/api/ui/router/v1?urlType=external",
            headers=get_auth_headers(token)
        )
        response.raise_for_status()
        return response.json()["Url"].rstrip("/")


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
