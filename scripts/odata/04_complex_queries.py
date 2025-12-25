"""
OData API - Complex Query Examples

Demonstrates advanced filtering, combining conditions, and real-world queries.

Usage:
    python scripts/odata/04_complex_queries.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from common.auth import get_token, get_auth_headers
from common.config import load_config

import warnings
warnings.filterwarnings("ignore")


def escape_odata_string(value: str) -> str:
    """Escape single quotes in OData string values."""
    return value.replace("'", "''")


def main():
    print("OData API - Complex Query Examples")
    print("=" * 50)

    config = load_config()
    token_data = get_token(config)
    headers = get_auth_headers(token_data["AccessToken"])

    # Example 1: Multi-field filter with ordering
    print("\n1. Multi-field filter with ordering:")
    print("-" * 40)
    print("   Query: Active pages for supplier, ordered by effective date")

    response = httpx.get(
        f"{config.odata_url}/table/price_page",
        params={
            "$filter": "supplier_id eq 21274 and row_status_flag eq 704",
            "$select": "price_page_uid,description,effective_date,expiration_date,calculation_value1",
            "$orderby": "effective_date desc",
            "$top": 5
        },
        headers=headers,
        verify=config.verify_ssl,
        follow_redirects=True
    )
    response.raise_for_status()
    data = response.json()

    for page in data["value"]:
        eff = str(page.get('effective_date', 'N/A'))[:10]
        exp = str(page.get('expiration_date', 'N/A'))[:10]
        val = page.get('calculation_value1', 0)
        print(f"  {page['price_page_uid']}: {eff} to {exp} (mult: {val:.3f})")

    # Example 2: OR conditions on same field
    print("\n2. OR conditions (multiple suppliers):")
    print("-" * 40)

    response = httpx.get(
        f"{config.odata_url}/table/price_page",
        params={
            "$filter": "(supplier_id eq 10 or supplier_id eq 21274) and row_status_flag eq 704",
            "$select": "price_page_uid,supplier_id,description",
            "$top": 10,
            "$count": "true"
        },
        headers=headers,
        verify=config.verify_ssl,
        follow_redirects=True
    )
    response.raise_for_status()
    data = response.json()

    print(f"  Total matching: {data.get('@odata.count', 'N/A')}")
    for page in data["value"]:
        print(f"  Supplier {page['supplier_id']}: {page.get('description', 'N/A')[:40]}")

    # Example 3: String contains with other conditions
    print("\n3. String contains with other conditions:")
    print("-" * 40)

    response = httpx.get(
        f"{config.odata_url}/table/price_page",
        params={
            "$filter": "contains(description,'IND_OEM') and row_status_flag eq 704",
            "$select": "price_page_uid,description,supplier_id",
            "$top": 5
        },
        headers=headers,
        verify=config.verify_ssl,
        follow_redirects=True
    )
    response.raise_for_status()
    data = response.json()

    print(f"  Pages with 'IND_OEM' in description:")
    for page in data["value"]:
        print(f"    {page['price_page_uid']}: {page.get('description', 'N/A')}")

    # Example 4: Null value check
    print("\n4. Null value check:")
    print("-" * 40)

    response = httpx.get(
        f"{config.odata_url}/table/price_page",
        params={
            "$filter": "expiration_date ne null and row_status_flag eq 704",
            "$select": "price_page_uid,description,expiration_date",
            "$orderby": "expiration_date asc",
            "$top": 5
        },
        headers=headers,
        verify=config.verify_ssl,
        follow_redirects=True
    )
    response.raise_for_status()
    data = response.json()

    print(f"  Pages with earliest expiration dates:")
    for page in data["value"]:
        exp = str(page.get('expiration_date', 'N/A'))[:10]
        print(f"    {page['price_page_uid']}: expires {exp}")

    # Example 5: Multiple orderby fields
    print("\n5. Multiple orderby fields:")
    print("-" * 40)

    response = httpx.get(
        f"{config.odata_url}/table/price_page",
        params={
            "$filter": "row_status_flag eq 704",
            "$select": "price_page_uid,supplier_id,description,effective_date",
            "$orderby": "supplier_id asc,effective_date desc",
            "$top": 8
        },
        headers=headers,
        verify=config.verify_ssl,
        follow_redirects=True
    )
    response.raise_for_status()
    data = response.json()

    print(f"  Pages ordered by supplier, then by date (newest first):")
    for page in data["value"]:
        eff = str(page.get('effective_date', 'N/A'))[:10]
        print(f"    Supplier {page['supplier_id']}: {page['price_page_uid']} ({eff})")

    # Example 6: Join-like query (related data)
    print("\n6. Getting related data (supplier for price page):")
    print("-" * 40)

    # First get a price page
    response = httpx.get(
        f"{config.odata_url}/table/price_page",
        params={
            "$filter": "row_status_flag eq 704",
            "$select": "price_page_uid,description,supplier_id",
            "$top": 1
        },
        headers=headers,
        verify=config.verify_ssl,
        follow_redirects=True
    )
    response.raise_for_status()
    data = response.json()

    if data["value"]:
        page = data["value"][0]
        supplier_id = page.get("supplier_id")
        print(f"  Price page: {page['price_page_uid']}")
        print(f"  Supplier ID: {supplier_id}")

        # Then get supplier details
        if supplier_id:
            response = httpx.get(
                f"{config.odata_url}/table/supplier",
                params={
                    "$filter": f"supplier_id eq {supplier_id}",
                    "$select": "supplier_id,supplier_name"
                },
                headers=headers,
                verify=config.verify_ssl,
                follow_redirects=True
            )
            response.raise_for_status()
            supplier_data = response.json()

            if supplier_data["value"]:
                supplier = supplier_data["value"][0]
                print(f"  Supplier name: {supplier.get('supplier_name', 'N/A')}")

    print("\n" + "=" * 50)
    print("Complex query examples complete!")


if __name__ == "__main__":
    main()
