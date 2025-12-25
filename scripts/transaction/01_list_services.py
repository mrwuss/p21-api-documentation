"""
Transaction API - List Available Services

Discovers all services available through the Transaction API.

Usage:
    python scripts/transaction/01_list_services.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from common.auth import get_token, get_auth_headers, get_ui_server_url
from common.config import load_config

import warnings
warnings.filterwarnings("ignore")


def main():
    print("Transaction API - List Available Services")
    print("=" * 50)

    config = load_config()
    token_data = get_token(config)
    headers = get_auth_headers(token_data["AccessToken"])

    # Get UI Server URL (Transaction API uses different base URL)
    ui_server_url = get_ui_server_url(config.base_url, token_data["AccessToken"], config.verify_ssl)
    print(f"UI Server: {ui_server_url}")

    # List all available services
    print("\nFetching available services...")
    print("-" * 40)

    response = httpx.get(
        f"{ui_server_url}/api/v2/services",
        headers=headers,
        verify=config.verify_ssl,
        follow_redirects=True
    )
    response.raise_for_status()
    data = response.json()

    # Services are returned as array of ServiceInfo objects
    services = data if isinstance(data, list) else data.get("value", data)

    print(f"\nFound {len(services)} services:\n")

    # Group by first letter for readability
    current_letter = ""
    for service in sorted(services, key=lambda x: x.get("Name", x) if isinstance(x, dict) else x):
        name = service.get("Name") if isinstance(service, dict) else service
        first_letter = name[0].upper() if name else ""

        if first_letter != current_letter:
            current_letter = first_letter
            print(f"\n  [{current_letter}]")

        print(f"    {name}")

    # Show some common services
    common_services = ["Order", "Invoice", "Customer", "Supplier", "SalesPricePage",
                       "PurchaseOrder", "InventoryMaster", "Task"]

    print("\n" + "=" * 50)
    print("Common Services:")
    print("-" * 40)

    for svc in common_services:
        found = any(
            (s.get("Name") if isinstance(s, dict) else s) == svc
            for s in services
        )
        status = "Available" if found else "Not found"
        print(f"  {svc}: {status}")

    print("\n" + "=" * 50)
    print("Service list complete!")


if __name__ == "__main__":
    main()
