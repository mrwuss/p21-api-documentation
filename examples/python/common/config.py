"""
P21 API Configuration

Loads environment variables and provides a typed configuration object.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv


@dataclass
class P21Config:
    """P21 API configuration."""
    base_url: str
    username: str = ""
    password: str = ""
    consumer_key: str | None = None
    consumer_username: str | None = None
    verify_ssl: bool = False

    @property
    def token_url(self) -> str:
        """V1 token generation endpoint."""
        return f"{self.base_url}/api/security/token"

    @property
    def token_url_v2(self) -> str:
        """V2 token generation endpoint (credentials in body)."""
        return f"{self.base_url}/api/security/token/v2"

    @property
    def odata_url(self) -> str:
        """OData service base URL."""
        return f"{self.base_url}/odataservice/odata"

    @property
    def entity_url(self) -> str:
        """Entity API base URL."""
        return f"{self.base_url}/api/entity"


def load_config() -> P21Config:
    """
    Load P21 configuration from environment variables.

    Looks for .env file in project root.

    Required variables:
        P21_BASE_URL: P21 server URL (e.g., https://play.p21server.com)
        P21_USERNAME: API username
        P21_PASSWORD: API password

    Optional variables:
        P21_VERIFY_SSL: Whether to verify SSL certificates (default: false)

    Returns:
        P21Config: Configuration object

    Raises:
        ValueError: If required environment variables are missing
    """
    # Find and load .env file: this file lives at examples/python/common/,
    # so the repo root is three parents up. Walk upward as a fallback so the
    # helper keeps working if the tree moves again.
    project_root = Path(__file__).resolve().parent.parent.parent
    env_file = project_root / ".env"
    if not env_file.exists():
        for parent in Path(__file__).resolve().parents:
            if (parent / ".env").exists():
                env_file = parent / ".env"
                break

    if env_file.exists():
        load_dotenv(env_file)

    # Get variables
    base_url = os.getenv("P21_BASE_URL")
    username = os.getenv("P21_USERNAME", "")
    password = os.getenv("P21_PASSWORD", "")
    consumer_key = os.getenv("P21_CONSUMER_KEY")
    consumer_username = os.getenv("P21_CONSUMER_USERNAME")

    # Validate: need base_url always, and either consumer_key or username+password
    missing = []
    if not base_url:
        missing.append("P21_BASE_URL")
    if not consumer_key and not username:
        missing.append("P21_USERNAME (or P21_CONSUMER_KEY)")
    if not consumer_key and not password:
        missing.append("P21_PASSWORD (or P21_CONSUMER_KEY)")

    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    # Get optional variables
    verify_ssl = os.getenv("P21_VERIFY_SSL", "false").lower() == "true"

    return P21Config(
        base_url=base_url.rstrip("/"),
        username=username,
        password=password,
        consumer_key=consumer_key,
        consumer_username=consumer_username,
        verify_ssl=verify_ssl
    )


if __name__ == "__main__":
    # Test configuration loading
    try:
        config = load_config()
        print(f"Base URL: {config.base_url}")
        print(f"Username: {config.username}")
        print(f"Password: {'*' * len(config.password)}")
        print(f"Consumer Key: {'set' if config.consumer_key else 'not set'}")
        print(f"Consumer Username: {config.consumer_username or 'not set'}")
        print(f"Verify SSL: {config.verify_ssl}")
        print(f"Token URL: {config.token_url}")
        print(f"Token URL V2: {config.token_url_v2}")
        print(f"OData URL: {config.odata_url}")
    except ValueError as e:
        print(f"Configuration error: {e}")
