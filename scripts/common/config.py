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
    username: str
    password: str
    verify_ssl: bool = False

    @property
    def token_url(self) -> str:
        """Token generation endpoint."""
        return f"{self.base_url}/api/security/token"

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
        P21_BASE_URL: P21 server URL (e.g., https://play.ifpusa.com)
        P21_USERNAME: API username
        P21_PASSWORD: API password

    Optional variables:
        P21_VERIFY_SSL: Whether to verify SSL certificates (default: false)

    Returns:
        P21Config: Configuration object

    Raises:
        ValueError: If required environment variables are missing
    """
    # Find and load .env file
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    env_file = project_root / ".env"

    if env_file.exists():
        load_dotenv(env_file)

    # Get required variables
    base_url = os.getenv("P21_BASE_URL")
    username = os.getenv("P21_USERNAME")
    password = os.getenv("P21_PASSWORD")

    # Validate required variables
    missing = []
    if not base_url:
        missing.append("P21_BASE_URL")
    if not username:
        missing.append("P21_USERNAME")
    if not password:
        missing.append("P21_PASSWORD")

    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    # Get optional variables
    verify_ssl = os.getenv("P21_VERIFY_SSL", "false").lower() == "true"

    return P21Config(
        base_url=base_url.rstrip("/"),
        username=username,
        password=password,
        verify_ssl=verify_ssl
    )


if __name__ == "__main__":
    # Test configuration loading
    try:
        config = load_config()
        print(f"Base URL: {config.base_url}")
        print(f"Username: {config.username}")
        print(f"Password: {'*' * len(config.password)}")
        print(f"Verify SSL: {config.verify_ssl}")
        print(f"Token URL: {config.token_url}")
        print(f"OData URL: {config.odata_url}")
    except ValueError as e:
        print(f"Configuration error: {e}")
