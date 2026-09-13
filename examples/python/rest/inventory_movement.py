"""
Other REST Families - Bin-to-Bin Inventory Movement
(inventory/inventorymovement moveinventory)

Moves stock between two bins for the same item/location -- total
qty_on_hand is unchanged, only its bin distribution moves. Dry run by
default; --execute actually posts.

Mirrors: docs/15-Other-REST-Families.md#inventoryinventorymovement

Undocumented preconditions found live, 26.1.5950.0:
    - moveAvailable/moveAllocations look boolean but are Y/N strings --
      "true"/"false" fails with "Move Available is a Y/N column."
    - toBin must be a bin this item/location already has a stock
      association with, not merely a bin that exists at the location --
      "A valid inventory bin must be entered." names neither the item
      nor location when it isn't.
    - toBin == fromBin is refused: "Destination bin has to be different
      from source bin."
    - A real bin can still be put-locked: "The Put Lock is set for this
      bin. You must select another."
    - GET /odataservice/odata/table/bin itself 404s on every casing and
      surface (see docs/02) -- find candidate bins via inv_loc.primary_bin
      instead, the way this script does.

Usage:
    python examples/python/rest/inventory_movement.py                 # dry run
    python examples/python/rest/inventory_movement.py --execute
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
        description="Bin-to-bin inventory movement (docs/15 inventory/inventorymovement)"
    )
    parser.add_argument("--execute", action="store_true", help="Actually POST (default: dry run)")
    parser.add_argument("--item-id", default="GBY")
    parser.add_argument("--location-id", default="40")
    parser.add_argument("--from-bin", default="FGA040",
                        help="Must be a bin this item/location currently holds stock in")
    parser.add_argument("--to-bin", default="XDOCK",
                        help="Must be a bin this item/location already has a stock "
                             "association with -- not just any bin at the location")
    parser.add_argument("--quantity", default="1")
    args = parser.parse_args()

    print("Other REST Families - Inventory Movement (inventorymovement)")
    print("=" * 60)

    config = load_config()
    token_data = get_token(config)
    headers = get_auth_headers(token_data["AccessToken"])
    print(f"Server: {config.base_url}")

    params = {
        "location": args.location_id, "itemId": args.item_id,
        "toBin": args.to_bin, "fromBin": args.from_bin,
        "lot": "", "uom": "EA", "quantity": args.quantity,
        "moveAvailable": "Y", "moveAllocations": "N",  # Y/N, NOT true/false -- see docstring
    }

    if not args.execute:
        print("\nDRY RUN - would POST to /api/inventory/inventorymovement/moveinventory")
        print("  with query parameters:")
        for k, v in params.items():
            print(f"    {k}={v!r}")
        print("\nRe-run with --execute to actually move it.")
        return

    r = httpx.post(f"{config.base_url}/api/inventory/inventorymovement/moveinventory",
                   params=params, headers=headers, verify=config.verify_ssl,
                   follow_redirects=True, timeout=60.0)
    if r.status_code != 200:
        print(f"\nMove failed: HTTP {r.status_code}\n{r.text[:500]}")
        raise SystemExit(1)

    result = r.json()
    moved = result["TransactionDetail"]["QuantityMoved"]
    print(f"\n{result['ResponseMessage']}: moved {moved} "
          f"{result['TransactionDetail']['QuantityMovedUOM']} "
          f"from {args.from_bin} to {args.to_bin}")
    if float(moved) == 0:
        print("  WARNING: QuantityMoved is 0 -- \"success\" here does not mean anything "
              "actually relocated. The source bin likely had no real stock to move.")


if __name__ == "__main__":
    main()
