"""
OData API - Basic Query Example

Demonstrates simple table queries with field selection.

Usage:
    python scripts/odata/01_basic_query.py
"""

import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from common.auth import get_token, get_auth_headers
from common.config import load_config

import warnings
warnings.filterwarnings("ignore")


def main():
    print("OData API - Basic Query Example")
    print("=" * 50)

    # Load configuration and authenticate
    config = load_config()
    print(f"Server: {config.base_url}")

    token_data = get_token(config)
    headers = get_auth_headers(token_data["AccessToken"])

    # Example 1: Query suppliers (first 5)
    print("\n1. Query suppliers (first 5):")
    print("-" * 30)

    response = httpx.get(
        f"{config.odata_url}/table/supplier",
        params={
            "$top": 5,
            "$select": "supplier_id,supplier_name",
            "$orderby": "supplier_name"
        },
        headers=headers,
        verify=config.verify_ssl,
        follow_redirects=True
    )
    response.raise_for_status()
    data = response.json()

    for supplier in data["value"]:
        print(f"  {supplier['supplier_id']}: {supplier['supplier_name']}")

    # Example 2: Query product groups
    print("\n2. Query product groups (first 5):")
    print("-" * 30)

    response = httpx.get(
        f"{config.odata_url}/table/product_group",
        params={
            "$top": 5,
            "$select": "product_group_id,product_group_desc",
            "$orderby": "product_group_id"
        },
        headers=headers,
        verify=config.verify_ssl,
        follow_redirects=True
    )
    response.raise_for_status()
    data = response.json()

    for group in data["value"]:
        print(f"  {group['product_group_id']}: {group.get('product_group_desc', 'N/A')}")

    # Example 3: Query with count
    print("\n3. Query price pages with count:")
    print("-" * 30)

    response = httpx.get(
        f"{config.odata_url}/table/price_page",
        params={
            "$top": 3,
            "$count": "true",
            "$select": "price_page_uid,description"
        },
        headers=headers,
        verify=config.verify_ssl,
        follow_redirects=True
    )
    response.raise_for_status()
    data = response.json()

    total_count = data.get("@odata.count", "N/A")
    print(f"  Total price pages in database: {total_count}")
    print(f"  First 3 records:")
    for page in data["value"]:
        print(f"    {page['price_page_uid']}: {page.get('description', 'N/A')[:50]}")

    print("\n" + "=" * 50)
    print("Basic query examples complete!")


if __name__ == "__main__":
    main()
