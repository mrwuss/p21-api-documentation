"""
OData API - Pagination Examples

Demonstrates $skip, $top, and $count for paginating results.

Usage:
    python scripts/odata/03_pagination.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from common.auth import get_token, get_auth_headers
from common.config import load_config

import warnings
warnings.filterwarnings("ignore")


def get_page(base_url: str, table: str, headers: dict,
             page_num: int, page_size: int, verify_ssl: bool = False) -> dict:
    """Fetch a specific page of results."""
    skip = (page_num - 1) * page_size

    response = httpx.get(
        f"{base_url}/table/{table}",
        params={
            "$skip": skip,
            "$top": page_size,
            "$count": "true",
            "$select": "supplier_id,supplier_name",
            "$orderby": "supplier_id"
        },
        headers=headers,
        verify=verify_ssl,
        follow_redirects=True
    )
    response.raise_for_status()
    return response.json()


def get_all_records(base_url: str, table: str, headers: dict,
                    filter_expr: str = None, page_size: int = 100,
                    verify_ssl: bool = False) -> list:
    """Fetch all records with automatic pagination."""
    records = []
    skip = 0

    while True:
        params = {
            "$skip": skip,
            "$top": page_size,
            "$count": "true"
        }
        if filter_expr:
            params["$filter"] = filter_expr

        response = httpx.get(
            f"{base_url}/table/{table}",
            params=params,
            headers=headers,
            verify=verify_ssl,
            follow_redirects=True
        )
        response.raise_for_status()
        data = response.json()

        records.extend(data["value"])
        total = data.get("@odata.count", len(records))

        print(f"    Fetched {len(records)} of {total} records...")

        if len(records) >= total:
            break
        skip += page_size

    return records


def main():
    print("OData API - Pagination Examples")
    print("=" * 50)

    config = load_config()
    token_data = get_token(config)
    headers = get_auth_headers(token_data["AccessToken"])

    # Example 1: Manual pagination
    print("\n1. Manual pagination (page 1 of suppliers):")
    print("-" * 40)

    page_size = 5
    data = get_page(config.odata_url, "supplier", headers,
                    page_num=1, page_size=page_size, verify_ssl=config.verify_ssl)

    total = data.get("@odata.count", "?")
    total_pages = (int(total) + page_size - 1) // page_size if isinstance(total, int) else "?"

    print(f"  Total records: {total}")
    print(f"  Page size: {page_size}")
    print(f"  Total pages: {total_pages}")
    print(f"  Page 1 results:")
    for supplier in data["value"]:
        print(f"    {supplier['supplier_id']}: {supplier['supplier_name']}")

    # Example 2: Page 2
    print("\n2. Page 2 of suppliers:")
    print("-" * 40)

    data = get_page(config.odata_url, "supplier", headers,
                    page_num=2, page_size=page_size, verify_ssl=config.verify_ssl)

    print(f"  Page 2 results:")
    for supplier in data["value"]:
        print(f"    {supplier['supplier_id']}: {supplier['supplier_name']}")

    # Example 3: Automatic pagination with filter
    print("\n3. Fetch all active price pages for supplier 21274:")
    print("-" * 40)

    records = get_all_records(
        config.odata_url,
        "price_page",
        headers,
        filter_expr="supplier_id eq 21274 and row_status_flag eq 704",
        page_size=50,
        verify_ssl=config.verify_ssl
    )

    print(f"\n  Total records fetched: {len(records)}")
    if records:
        print(f"  Sample records:")
        for page in records[:3]:
            print(f"    {page.get('price_page_uid')}: {page.get('description', 'N/A')[:40]}")

    # Example 4: Count only (without fetching data)
    print("\n4. Count only (no data fetch):")
    print("-" * 40)

    response = httpx.get(
        f"{config.odata_url}/table/price_page",
        params={
            "$count": "true",
            "$top": 0  # Fetch count but no records
        },
        headers=headers,
        verify=config.verify_ssl,
        follow_redirects=True
    )
    response.raise_for_status()
    data = response.json()

    print(f"  Total price pages: {data.get('@odata.count', 'N/A')}")

    print("\n" + "=" * 50)
    print("Pagination examples complete!")


if __name__ == "__main__":
    main()
