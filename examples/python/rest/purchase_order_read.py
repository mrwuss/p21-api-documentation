"""
Other REST Families - Read a Purchase Order Header (purchasing/purchaseorders)

Reads one PO by po_no and shows the family's defining limitation: every
child collection (POLines, POSales, POHdrNotes, POLineNotes) is null on a
keyed GET, with or without any expansion parameter.

Mirrors: docs/15-Other-REST-Families.md#purchasingpurchaseorders

Verified live, 26.1.5950.0:
    - includeLines, expand, $expand, full, includeChildren all return a
      byte-identical 742-byte header-only response. This is not a
      parameter you are missing.
    - UserDefinedFields is always {} even on a PO whose po_hdr_ud row has
      real data -- read UDF values over OData instead.
    - GET /api/purchasing/purchaseorders/ (no key) is an UNBOUNDED
      collection dump that did not return within 180s on the test
      tenant. Never call it -- this script only uses the keyed route.
    - Writes on this family (POST/PUT/async) are NOT exercised anywhere
      in this repo. Use the Transaction API PurchaseOrder service for
      verified writes -- see docs/03-Transaction-API.md.

Usage:
    python examples/python/rest/purchase_order_read.py 998310
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

CHILD_COLLECTIONS = ("POLines", "POSales", "POHdrNotes", "POLineNotes")


def get_po(base_url: str, headers: dict, verify_ssl: bool, po_no: str) -> dict:
    """GET one PO header by po_no."""
    response = httpx.get(
        f"{base_url}/api/purchasing/purchaseorders/{po_no}",
        headers=headers, verify=verify_ssl, follow_redirects=True, timeout=60.0,
    )
    response.raise_for_status()
    return response.json()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Read a PO header (docs/15 purchasing/purchaseorders)"
    )
    parser.add_argument("po_no", help="po_hdr.po_no")
    args = parser.parse_args()

    print("Other REST Families - Purchase Order Header (purchasing/purchaseorders)")
    print("=" * 60)

    config = load_config()
    token_data = get_token(config)
    headers = get_auth_headers(token_data["AccessToken"])
    print(f"Server: {config.base_url}")

    po = get_po(config.base_url, headers, config.verify_ssl, args.po_no)

    print(f"\nPO {po['PoNo']}  vendor={po['VendorId']}  location={po['LocationId']}  "
          f"approved={po['Approved']}  complete={po['Complete']}")

    print("\nChild collections (always null on this family -- see docs/15):")
    for key in CHILD_COLLECTIONS:
        print(f"  {key}: {po.get(key)!r}")

    print(f"\nUserDefinedFields: {po.get('UserDefinedFields')!r}  "
          f"(always {{}} here even when po_hdr_ud has real data -- read UDF "
          f"values over OData)")


if __name__ == "__main__":
    main()
