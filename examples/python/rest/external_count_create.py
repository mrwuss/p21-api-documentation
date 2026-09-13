"""
Other REST Families - Create a Staged Cycle Count (inventory/externalcounts)

Stages a count for one item at one bin. Does NOT change inv_loc.qty_on_hand
-- confirmed by reading it back unchanged after a successful create.
Dry run by default; --execute actually posts.

Mirrors: docs/15-Other-REST-Families.md#inventoryexternalcounts

The trap, found live on 26.1.5950.0: ItemId must be repeated on the BIN
sub-record, not just the line -- it is not inherited from its parent
line, and omitting it produces an error about "Bin Detail Record...
missing/unmatched" that does not name the actual cause.

Usage:
    python examples/python/rest/external_count_create.py                 # dry run
    python examples/python/rest/external_count_create.py --execute
"""

import argparse
import json
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
        description="Create a staged cycle count (docs/15 inventory/externalcounts)"
    )
    parser.add_argument("--execute", action="store_true", help="Actually POST (default: dry run)")
    parser.add_argument("--item-id", default="GBY")
    parser.add_argument("--location-id", type=int, default=40)
    parser.add_argument("--bin", default="FGA040")
    parser.add_argument("--quantity", type=float, default=5.0)
    args = parser.parse_args()

    print("Other REST Families - External Count Create (externalcounts)")
    print("=" * 60)

    config = load_config()
    token_data = get_token(config)
    headers = get_auth_headers(token_data["AccessToken"])
    print(f"Server: {config.base_url}")

    payload = {
        "LocationId": args.location_id,
        "CountDate": "2026-09-12T00:00:00",
        "Lines": {"list": [{
            "ItemId": args.item_id, "UnitQuantity": args.quantity, "UnitOfMeasure": "EA",
            # ItemId repeated here on purpose -- see docstring. Omitting it
            # fails with an error that does not name this field.
            "Bins": {"list": [{"ItemId": args.item_id, "BinCd": args.bin,
                               "UnitQuantity": args.quantity, "UnitOfMeasure": "EA"}]},
        }]},
    }

    if not args.execute:
        print("\nDRY RUN - payload that would be POSTed to /api/inventory/externalcounts/:")
        print(json.dumps(payload, indent=2))
        print("\nRe-run with --execute to actually create it.")
        return

    def qty_on_hand() -> float:
        item = httpx.get(f"{config.base_url}/odataservice/odata/table/inv_mast",
                         params={"$select": "inv_mast_uid", "$filter": f"item_id eq '{args.item_id}'"},
                         headers=headers, verify=config.verify_ssl, timeout=30.0).json()["value"][0]
        loc = httpx.get(f"{config.base_url}/odataservice/odata/table/inv_loc",
                        params={"$select": "qty_on_hand",
                                "$filter": f"inv_mast_uid eq {item['inv_mast_uid']} "
                                          f"and location_id eq {args.location_id}"},
                        headers=headers, verify=config.verify_ssl, timeout=30.0).json()["value"][0]
        return loc["qty_on_hand"]

    before = qty_on_hand()

    r = httpx.post(f"{config.base_url}/api/inventory/externalcounts/", headers=headers,
                   json=payload, verify=config.verify_ssl, follow_redirects=True, timeout=60.0)
    if r.status_code != 200:
        print(f"\nCreate failed: HTTP {r.status_code}\n{r.text[:500]}")
        raise SystemExit(1)

    print(f"\nCreated. Response: {json.dumps(r.json(), indent=2)[:400]}")

    after = qty_on_hand()
    print(f"\nqty_on_hand: {before} -> {after} "
          f"(unchanged: {before == after} -- this is a STAGED count, not a live adjustment)")


if __name__ == "__main__":
    main()
