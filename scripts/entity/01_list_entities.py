"""
Entity API - List Available Entities

The Entity API provides CRUD operations on domain objects.
This script demonstrates basic entity access.

Usage:
    python scripts/entity/01_list_entities.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from common.auth import get_token, get_auth_headers
from common.config import load_config

import warnings
warnings.filterwarnings("ignore")


def main():
    print("Entity API - List Available Entities")
    print("=" * 60)

    config = load_config()
    token_data = get_token(config)
    headers = get_auth_headers(token_data["AccessToken"])

    print(f"Server: {config.base_url}")

    # Common Entity API endpoints
    entities = [
        ("Sales - Customers", "/api/sales/customers"),
        ("Sales - Orders", "/api/sales/orders"),
        ("Sales - Invoices", "/api/sales/invoices"),
        ("Sales - Quotes", "/api/sales/quotes"),
        ("Inventory - Parts", "/api/inventory/parts"),
        ("Purchasing - Suppliers", "/api/purchasing/suppliers"),
        ("Purchasing - PurchaseOrders", "/api/purchasing/purchaseorders"),
        ("Contacts", "/api/contacts"),
    ]

    print("\n1. Testing common Entity API endpoints:")
    print("-" * 50)

    available = []
    for name, endpoint in entities:
        try:
            # Try to get first record to verify endpoint exists
            response = httpx.get(
                f"{config.base_url}{endpoint}",
                params={"$top": 1},
                headers=headers,
                verify=config.verify_ssl,
                follow_redirects=True,
                timeout=30.0
            )

            if response.status_code == 200:
                data = response.json()
                count = len(data) if isinstance(data, list) else 1
                print(f"  [OK] {name}: {endpoint}")
                available.append((name, endpoint))
            else:
                print(f"  [--] {name}: {response.status_code}")

        except Exception as e:
            print(f"  [--] {name}: Error - {str(e)[:50]}")

    # Example 2: Get a new template
    print("\n2. Getting new customer template:")
    print("-" * 50)

    try:
        response = httpx.get(
            f"{config.base_url}/api/sales/customers/new",
            headers=headers,
            verify=config.verify_ssl,
            follow_redirects=True,
            timeout=30.0
        )

        if response.status_code == 200:
            template = response.json()
            print("  Template fields available:")

            # Show some fields from the template
            fields = list(template.keys())[:15]
            for field in fields:
                value = template.get(field)
                value_str = str(value)[:30] if value else "(empty)"
                print(f"    - {field}: {value_str}")

            if len(template) > 15:
                print(f"    ... and {len(template) - 15} more fields")
        else:
            print(f"  Error: {response.status_code}")

    except Exception as e:
        print(f"  Error: {e}")

    # Example 3: Get sample customer data
    print("\n3. Getting sample customer data:")
    print("-" * 50)

    try:
        response = httpx.get(
            f"{config.base_url}/api/sales/customers",
            params={"$top": 3},
            headers=headers,
            verify=config.verify_ssl,
            follow_redirects=True,
            timeout=30.0
        )

        if response.status_code == 200:
            customers = response.json()
            print(f"  Found {len(customers)} customer(s):")

            for customer in customers[:3]:
                code = customer.get("CustomerCode", "N/A")
                name = customer.get("CustomerName", "Unknown")[:40]
                print(f"    {code}: {name}")
        else:
            print(f"  Error: {response.status_code}")

    except Exception as e:
        print(f"  Error: {e}")

    print("\n" + "=" * 60)
    print("Entity discovery complete!")
    print(f"\nFound {len(available)} accessible endpoints")
    print("\nEntity API URL pattern:")
    print("  GET    /api/{category}/{entity}        - List all")
    print("  GET    /api/{category}/{entity}/{id}   - Get one")
    print("  GET    /api/{category}/{entity}/new    - Get template")
    print("  POST   /api/{category}/{entity}        - Create/Update")
    print("  DELETE /api/{category}/{entity}/{id}   - Delete")
    print("\nNote: Entity API availability depends on P21 configuration.")
    print("Some endpoints may require specific licensing or setup.")


if __name__ == "__main__":
    main()
