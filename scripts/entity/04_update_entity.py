"""
Entity API - Update Entity

Demonstrates updating an existing entity record.

To update a record:
1. GET the existing record (optional, for reference)
2. Create payload with key field + changed fields
3. POST with key field (presence of key = update)

Usage:
    python scripts/entity/04_update_entity.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from common.auth import get_token, get_auth_headers
from common.config import load_config

import warnings
warnings.filterwarnings("ignore")


def get_entity(base_url: str, endpoint: str, entity_id: str,
                headers: dict, verify_ssl: bool) -> dict:
    """Get an entity by ID."""
    response = httpx.get(
        f"{base_url}{endpoint}/{entity_id}",
        headers=headers,
        verify=verify_ssl,
        follow_redirects=True,
        timeout=30.0
    )
    response.raise_for_status()
    return response.json()


def get_entity_extended(base_url: str, endpoint: str, entity_id: str,
                         headers: dict, verify_ssl: bool, props: str = "*") -> dict:
    """Get an entity with extended properties."""
    response = httpx.get(
        f"{base_url}{endpoint}/{entity_id}",
        params={"extendedproperties": props},
        headers=headers,
        verify=verify_ssl,
        follow_redirects=True,
        timeout=30.0
    )
    response.raise_for_status()
    return response.json()


def update_entity(base_url: str, endpoint: str, data: dict,
                   headers: dict, verify_ssl: bool) -> dict:
    """Update an entity record."""
    response = httpx.post(
        f"{base_url}{endpoint}",
        headers={**headers, "Content-Type": "application/json"},
        json=data,
        verify=verify_ssl,
        follow_redirects=True,
        timeout=30.0
    )
    response.raise_for_status()
    return response.json()


def main():
    print("Entity API - Update Entity")
    print("=" * 60)

    config = load_config()
    token_data = get_token(config)
    headers = get_auth_headers(token_data["AccessToken"])

    print(f"Server: {config.base_url}")

    # Example 1: Get an existing customer
    print("\n1. Getting existing customer:")
    print("-" * 50)

    # Get first customer to use as example
    try:
        response = httpx.get(
            f"{config.base_url}/api/sales/customers",
            params={"$top": 1},
            headers=headers,
            verify=config.verify_ssl,
            follow_redirects=True,
            timeout=30.0
        )
        response.raise_for_status()
        customers = response.json()

        if customers:
            customer = customers[0]
            customer_code = customer.get("CustomerCode")
            print(f"  CustomerCode: {customer_code}")
            print(f"  CustomerName: {customer.get('CustomerName')}")
            print(f"  City: {customer.get('City')}")
            print(f"  State: {customer.get('State')}")
        else:
            print("  No customers found")
            customer_code = None

    except httpx.HTTPStatusError as e:
        print(f"  Error: {e.response.status_code}")
        customer_code = None

    # Example 2: Get with extended properties
    print("\n2. Getting entity with extended properties:")
    print("-" * 50)

    try:
        # Try to get an order with extended properties
        response = httpx.get(
            f"{config.base_url}/api/sales/orders",
            params={"$top": 1},
            headers=headers,
            verify=config.verify_ssl,
            follow_redirects=True,
            timeout=30.0
        )
        response.raise_for_status()
        orders = response.json()

        if orders:
            order = orders[0]
            order_id = order.get("OrderNumber") or order.get("OrderNo") or order.get("Id")
            print(f"  Order ID: {order_id}")
            print(f"  Attempting to get extended properties...")

            # Try getting with extended properties
            try:
                extended = get_entity_extended(
                    config.base_url,
                    "/api/sales/orders",
                    str(order_id),
                    headers,
                    config.verify_ssl,
                    "*"
                )
                print(f"  Extended properties available: {list(extended.keys())[:5]}...")
            except:
                print("  Extended properties not available for this order")

    except httpx.HTTPStatusError as e:
        print(f"  Error: {e.response.status_code}")

    # Example 3: Show update workflow
    print("\n3. Update workflow (demonstration):")
    print("-" * 50)

    print("  To update a customer, you would:")
    print("  1. Create payload with key field + changes:")
    print()
    print("  update_payload = {")
    print(f'      "CustomerCode": {customer_code},  # Key = UPDATE')
    print('      "CustomerName": "Updated Name"     # Changed field')
    print("  }")
    print()
    print("  2. POST to /api/sales/customers")
    print()
    print("  The presence of CustomerCode tells API to UPDATE, not INSERT")

    # Example 4: Show update payload structure
    print("\n4. Sample update payload:")
    print("-" * 50)

    sample_update = {
        "CustomerCode": customer_code or 100000,
        "CustomerName": "Updated Customer Name",
        "City": "New City"
    }

    print("  {")
    for key, value in sample_update.items():
        if isinstance(value, str):
            print(f'    "{key}": "{value}",')
        else:
            print(f'    "{key}": {value},')
    print("  }")

    print("\n  Note:")
    print("  - CustomerCode IS included = update")
    print("  - Only changed fields need to be in payload")
    print("  - Fields not included remain unchanged")

    # Example 5: Important considerations
    print("\n5. Important considerations:")
    print("-" * 50)
    print("  - Entity API uses POST for both create AND update")
    print("  - Key field presence determines insert vs update")
    print("  - Extended properties (related data) may require")
    print("    multiple API calls to update")
    print("  - Some fields may be read-only")
    print("  - Validation errors return in response body")

    print("\n" + "=" * 60)
    print("Update entity examples complete!")
    print("\nKey points:")
    print("- Include key field (e.g., CustomerCode) for UPDATE")
    print("- Omit key field for INSERT (create new)")
    print("- Only include fields you want to change")
    print("- Use extendedproperties=* to see related data")


if __name__ == "__main__":
    main()
