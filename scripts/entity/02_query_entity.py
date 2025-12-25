"""
Entity API - Query Entities

Demonstrates querying entities with filters using the $query parameter.

The Entity API supports OData-like query syntax for filtering.

Usage:
    python scripts/entity/02_query_entity.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from common.auth import get_token, get_auth_headers
from common.config import load_config

import warnings
warnings.filterwarnings("ignore")


def query_entity(base_url: str, endpoint: str, query: str, headers: dict,
                  verify_ssl: bool, top: int = 10) -> list:
    """Query an entity with a filter expression."""
    params = {"$query": query}
    if top:
        params["$top"] = top

    response = httpx.get(
        f"{base_url}{endpoint}",
        params=params,
        headers=headers,
        verify=verify_ssl,
        follow_redirects=True,
        timeout=30.0
    )
    response.raise_for_status()
    return response.json()


def main():
    print("Entity API - Query Entities")
    print("=" * 60)

    config = load_config()
    token_data = get_token(config)
    headers = get_auth_headers(token_data["AccessToken"])

    print(f"Server: {config.base_url}")

    # Example 1: Simple equality filter
    print("\n1. Equality filter (State eq 'NY'):")
    print("-" * 50)

    try:
        customers = query_entity(
            config.base_url,
            "/api/sales/customers",
            "State eq 'NY'",
            headers,
            config.verify_ssl,
            top=5
        )

        print(f"  Found {len(customers)} customer(s) in Iowa:")
        for customer in customers[:5]:
            code = customer.get("CustomerCode", "N/A")
            name = customer.get("CustomerName", "Unknown")[:35]
            city = customer.get("City", "N/A")
            print(f"    {code}: {name} ({city})")

    except httpx.HTTPStatusError as e:
        print(f"  Error: {e.response.status_code}")
    except Exception as e:
        print(f"  Error: {e}")

    # Example 2: Comparison operator
    print("\n2. Comparison filter (CreditLimit gt 10000):")
    print("-" * 50)

    try:
        customers = query_entity(
            config.base_url,
            "/api/sales/customers",
            "CreditLimit gt 10000",
            headers,
            config.verify_ssl,
            top=5
        )

        print(f"  Found {len(customers)} customer(s) with high credit:")
        for customer in customers[:5]:
            code = customer.get("CustomerCode", "N/A")
            name = customer.get("CustomerName", "Unknown")[:30]
            limit = customer.get("CreditLimit", 0)
            print(f"    {code}: {name} (${limit:,.2f})")

    except httpx.HTTPStatusError as e:
        print(f"  Error: {e.response.status_code}")
    except Exception as e:
        print(f"  Error: {e}")

    # Example 3: String function (startswith)
    print("\n3. String function (startswith):")
    print("-" * 50)

    try:
        customers = query_entity(
            config.base_url,
            "/api/sales/customers",
            "startswith(CustomerName, 'A')",
            headers,
            config.verify_ssl,
            top=5
        )

        print(f"  Found {len(customers)} customer(s) starting with 'A':")
        for customer in customers[:5]:
            code = customer.get("CustomerCode", "N/A")
            name = customer.get("CustomerName", "Unknown")[:40]
            print(f"    {code}: {name}")

    except httpx.HTTPStatusError as e:
        print(f"  Error: {e.response.status_code}")
    except Exception as e:
        print(f"  Error: {e}")

    # Example 4: Logical AND
    print("\n4. Logical AND (State and CreditLimit):")
    print("-" * 50)

    try:
        customers = query_entity(
            config.base_url,
            "/api/sales/customers",
            "State eq 'NY' and CreditLimit gt 5000",
            headers,
            config.verify_ssl,
            top=5
        )

        print(f"  Found {len(customers)} Iowa customer(s) with credit > $5000:")
        for customer in customers[:5]:
            code = customer.get("CustomerCode", "N/A")
            name = customer.get("CustomerName", "Unknown")[:30]
            limit = customer.get("CreditLimit", 0)
            print(f"    {code}: {name} (${limit:,.2f})")

    except httpx.HTTPStatusError as e:
        print(f"  Error: {e.response.status_code}")
    except Exception as e:
        print(f"  Error: {e}")

    # Example 5: Logical OR
    print("\n5. Logical OR (multiple states):")
    print("-" * 50)

    try:
        customers = query_entity(
            config.base_url,
            "/api/sales/customers",
            "State eq 'NY' or State eq 'IL'",
            headers,
            config.verify_ssl,
            top=5
        )

        print(f"  Found {len(customers)} customer(s) in IA or IL:")
        for customer in customers[:5]:
            code = customer.get("CustomerCode", "N/A")
            name = customer.get("CustomerName", "Unknown")[:30]
            state = customer.get("State", "N/A")
            print(f"    {code}: {name} ({state})")

    except httpx.HTTPStatusError as e:
        print(f"  Error: {e.response.status_code}")
    except Exception as e:
        print(f"  Error: {e}")

    print("\n" + "=" * 60)
    print("Query examples complete!")
    print("\nSupported operators:")
    print("  Comparison: eq, ne, gt, ge, lt, le")
    print("  Logical: and, or, not")
    print("  String: startswith(), endswith(), substringof()")


if __name__ == "__main__":
    main()
