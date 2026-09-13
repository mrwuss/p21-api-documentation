"""
Other REST Families - Read an Inventory Adjustment Header
(inventory/inventoryadjustments)

Reads one adjustment by AdjustmentNo and, when it was posted by a
CreateWmsAdjustment-family call, follows the GL journal entry it created
via accounting/gl.

Mirrors: docs/15-Other-REST-Families.md#inventoryinventoryadjustments

Verified live, 26.1.5950.0:
    - Lines is always null on a keyed GET here, same as the child-collection
      pattern on purchasing/purchaseorders -- read inv_adj_line over OData.
    - Approved and Delete are real booleans on this family, where the PO
      family uses "Y"/"N" strings for the same concepts. No shared
      convention across families -- check each one.
    - GET /api/inventory/inventoryadjustments/ (no key) is an UNBOUNDED
      dump -- 63 MB on the test tenant. Never call it.
    - The four createWms* POST routes (createWmsAdjustment,
      createWmsAdjustmentWithCost, createWmsTagAdjustment,
      createWmsTagAdjustmentWithCost) take QUERY-STRING parameters, not a
      body, and are NOT exercised in this repo -- they move stock and post
      to the GL. See docs/15's Open Questions.

Usage:
    python examples/python/rest/inventory_adjustment_read.py 1000002
    python examples/python/rest/inventory_adjustment_read.py 1000002 --gl-transaction 3
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


def get_adjustment(base_url: str, headers: dict, verify_ssl: bool,
                    adjustment_no: str) -> dict:
    """GET one adjustment header by AdjustmentNo."""
    response = httpx.get(
        f"{base_url}/api/inventory/inventoryadjustments/{adjustment_no}",
        headers=headers, verify=verify_ssl, follow_redirects=True, timeout=60.0,
    )
    response.raise_for_status()
    return response.json()


def get_gl_lines(base_url: str, headers: dict, verify_ssl: bool,
                  transaction_number: str) -> list[dict]:
    """GET the GL journal entry the adjustment posted, if known.

    See gl_journal_entry.py for the general-purpose version of this call.
    """
    response = httpx.get(
        f"{base_url}/api/accounting/gl/{transaction_number}",
        headers=headers, verify=verify_ssl, follow_redirects=True, timeout=60.0,
    )
    response.raise_for_status()
    return response.json()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Read an inventory adjustment header "
                     "(docs/15 inventory/inventoryadjustments)"
    )
    parser.add_argument("adjustment_no", help="inv_adj_hdr.adjustment_number")
    parser.add_argument("--gl-transaction",
                        help="Also read this gl.transaction_number, to show the "
                             "adjustment's own GL posting (found via JournalId "
                             "'IA' + Source on the accounting/gl family)")
    args = parser.parse_args()

    print("Other REST Families - Inventory Adjustment (inventory/inventoryadjustments)")
    print("=" * 60)

    config = load_config()
    token_data = get_token(config)
    headers = get_auth_headers(token_data["AccessToken"])
    print(f"Server: {config.base_url}")

    adj = get_adjustment(config.base_url, headers, config.verify_ssl, args.adjustment_no)

    print(f"\nAdjustment {adj['AdjustmentNo']}  location={adj['LocationId']}  "
          f"reason={adj['Reason']!r}  approved={adj['Approved']!r} "
          f"(real bool, not 'Y'/'N')  delete={adj['Delete']!r}")
    print(f"Lines: {adj.get('Lines')!r}  (always null on this family -- "
          f"read inv_adj_line over OData)")

    if args.gl_transaction:
        print(f"\nGL journal entry for transaction {args.gl_transaction}:")
        print("-" * 50)
        for line in get_gl_lines(config.base_url, headers, config.verify_ssl,
                                  args.gl_transaction):
            print(f"  {line['AccountNumber']:14} {line['Amount']:>14,.2f}  "
                  f"journal={line['JournalId']}  source={line['Source']}")


if __name__ == "__main__":
    main()
