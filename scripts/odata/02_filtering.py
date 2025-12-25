"""
OData API - Filtering Examples

Demonstrates various filter expressions and operators.

Usage:
    python scripts/odata/02_filtering.py
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
    print("OData API - Filtering Examples")
    print("=" * 50)

    config = load_config()
    token_data = get_token(config)
    headers = get_auth_headers(token_data["AccessToken"])

    # Example 1: Equality filter
    print("\n1. Equality filter (supplier_id eq 21274):")
    print("-" * 40)

    response = httpx.get(
        f"{config.odata_url}/table/price_page",
        params={
            "$filter": "supplier_id eq 21274",
            "$select": "price_page_uid,description,supplier_id",
            "$top": 5
        },
        headers=headers,
        verify=config.verify_ssl,
        follow_redirects=True
    )
    response.raise_for_status()
    data = response.json()

    print(f"  Found {len(data['value'])} records:")
    for page in data["value"]:
        print(f"    {page['price_page_uid']}: {page.get('description', 'N/A')[:40]}")

    # Example 2: Multiple conditions (AND)
    print("\n2. Multiple conditions (AND):")
    print("-" * 40)

    response = httpx.get(
        f"{config.odata_url}/table/price_page",
        params={
            "$filter": "supplier_id eq 21274 and row_status_flag eq 704",
            "$select": "price_page_uid,description,row_status_flag",
            "$top": 5
        },
        headers=headers,
        verify=config.verify_ssl,
        follow_redirects=True
    )
    response.raise_for_status()
    data = response.json()

    print(f"  Active pages for supplier 21274: {len(data['value'])} found")
    for page in data["value"]:
        print(f"    {page['price_page_uid']}: {page.get('description', 'N/A')[:40]}")

    # Example 3: String function (startswith)
    print("\n3. String function (startswith):")
    print("-" * 40)

    response = httpx.get(
        f"{config.odata_url}/table/supplier",
        params={
            "$filter": "startswith(supplier_name,'A')",
            "$select": "supplier_id,supplier_name",
            "$top": 5,
            "$orderby": "supplier_name"
        },
        headers=headers,
        verify=config.verify_ssl,
        follow_redirects=True
    )
    response.raise_for_status()
    data = response.json()

    print(f"  Suppliers starting with 'A':")
    for supplier in data["value"]:
        print(f"    {supplier['supplier_id']}: {supplier['supplier_name']}")

    # Example 4: Contains filter
    print("\n4. Contains filter:")
    print("-" * 40)

    response = httpx.get(
        f"{config.odata_url}/table/product_group",
        params={
            "$filter": "contains(product_group_id,'F')",
            "$select": "product_group_id,product_group_desc",
            "$top": 5
        },
        headers=headers,
        verify=config.verify_ssl,
        follow_redirects=True
    )
    response.raise_for_status()
    data = response.json()

    print(f"  Product groups containing 'F':")
    for group in data["value"]:
        print(f"    {group['product_group_id']}: {group.get('product_group_desc', 'N/A')}")

    # Example 5: Comparison operators
    print("\n5. Comparison operators (greater than):")
    print("-" * 40)

    response = httpx.get(
        f"{config.odata_url}/table/price_page",
        params={
            "$filter": "calculation_value1 gt 0.5 and calculation_value1 lt 1.0",
            "$select": "price_page_uid,description,calculation_value1",
            "$top": 5,
            "$orderby": "calculation_value1 desc"
        },
        headers=headers,
        verify=config.verify_ssl,
        follow_redirects=True
    )
    response.raise_for_status()
    data = response.json()

    print(f"  Pages with multiplier between 0.5 and 1.0:")
    for page in data["value"]:
        val = page.get('calculation_value1', 0)
        print(f"    {page['price_page_uid']}: {val:.3f} - {page.get('description', 'N/A')[:30]}")

    print("\n" + "=" * 50)
    print("Filtering examples complete!")


if __name__ == "__main__":
    main()
