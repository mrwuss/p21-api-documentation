"""
Other REST Families - Read Middleware System Info (environment/systems)

Reads the middleware's own build/config metadata. A JSON alternative to
serverinfo that returns JSON directly, no Accept-header XML trap.

Mirrors: docs/15-Other-REST-Families.md#environmentsystems

There is no /ping on this family (the SDK contract never declares one) --
the bare GET is the availability check.

Usage:
    python examples/python/rest/environment_systems.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from common.auth import get_token, get_auth_headers
from common.config import load_config

import warnings
warnings.filterwarnings("ignore")


def main() -> None:
    print("Other REST Families - System Info (environment/systems)")
    print("=" * 60)

    config = load_config()
    token_data = get_token(config)
    headers = get_auth_headers(token_data["AccessToken"])
    print(f"Server: {config.base_url}")

    response = httpx.get(
        f"{config.base_url}/api/environment/systems",
        headers=headers, verify=config.verify_ssl, follow_redirects=True, timeout=30.0,
    )
    response.raise_for_status()
    systems = response.json()["list"]

    for system in systems:
        print(f"\n{system['Id']} ({system['Type']})")
        print(f"  Version: {system['Version']}")
        for prop in system["Properties"]["list"]:
            print(f"  {prop['Name']}: {prop['Value']}")


if __name__ == "__main__":
    main()
