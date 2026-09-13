"""
Other REST Families - Cross-Entity Part Lookup (inventory/partscan)

Resolves a scan/search term to an item, optionally scoped by customer,
supplier, or location. Read-only.

Mirrors: docs/15-Other-REST-Families.md#inventorypartscan

Usage:
    python examples/python/rest/part_scan.py GBY
    python examples/python/rest/part_scan.py GBY --company-id ACME
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from common.auth import get_token, get_auth_headers
from common.config import load_config

import warnings
warnings.filterwarnings("ignore")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Cross-entity part lookup (docs/15 inventory/partscan)"
    )
    parser.add_argument("part_search", help="Scan term, item id, or customer/supplier part number")
    parser.add_argument("--company-id", default="")
    parser.add_argument("--location-id", default="")
    parser.add_argument("--customer-id", default="")
    parser.add_argument("--supplier-id", default="")
    args = parser.parse_args()

    print("Other REST Families - Part Scan (inventory/partscan)")
    print("=" * 60)

    config = load_config()
    token_data = get_token(config)
    headers = get_auth_headers(token_data["AccessToken"])
    print(f"Server: {config.base_url}")

    # Trailing slash before the query string matters here -- the bare
    # form without it 307-redirects.
    response = httpx.get(
        f"{config.base_url}/api/inventory/partscan/",
        params={"partSearch": args.part_search, "companyId": args.company_id,
                "locationId": args.location_id, "customerId": args.customer_id,
                "supplierId": args.supplier_id},
        headers=headers, verify=config.verify_ssl, follow_redirects=True, timeout=40.0,
    )
    response.raise_for_status()

    print(f"\nMatches for {args.part_search!r}:")
    print("-" * 50)
    for match in response.json():
        print(f"  ItemId={match['ItemId']:20} Source={match['Source']!r:20} "
              f"InvMastUid={match['InvMastUid']}")


if __name__ == "__main__":
    main()
