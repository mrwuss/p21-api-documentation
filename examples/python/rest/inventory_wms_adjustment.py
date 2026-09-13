"""
Other REST Families - Post a WMS Inventory Adjustment
(inventory/inventoryadjustments createWmsAdjustment / createWmsAdjustmentWithCost)

Adjust an item's on-hand quantity by a signed delta, then read the location
back. Dry run by default; --execute actually posts.

Mirrors: docs/15-Other-REST-Families.md#createwmsadjustment-verified

Two undocumented preconditions found live, 26.1.5950.0, both worth
checking before you call this against your own data:
    - `reason` must name a currently ACTIVE reason record (reason.delete_flag
      eq 'N' over OData). A historical inactive one -- even one still shown
      as the Reason text on old adjustment records -- fails with
      "This Adjustment Reason record could not be retrieved."
    - `binCd` is required whenever the item/location is bin-tracked
      (inv_loc.track_bins eq 'Y'). Omitting it fails with "Bin is required.",
      naming neither the item nor the location. Find the bin via
      inv_loc.primary_bin -- GET /odataservice/odata/table/bin itself 404s
      on this tenant regardless of casing or surface (see docs/02).

`unitQuantity` is a SIGNED DELTA, confirmed by posting the same positive
value twice from a 0 on-hand and watching it accumulate rather than repeat.

Unlike purchasing/purchaseorders' UnitPrice, `unitCost` on the WithCost
variant IS honored exactly -- pass --unit-cost to exercise it.

The tag variants (createWmsTagAdjustment / WithCost) are NOT covered by
this script: every item tried, including one with inv_mast.use_tags_flag
= 'Y', was refused "is not a tagged item". See docs/15's Open Questions.

Usage:
    python examples/python/rest/inventory_wms_adjustment.py                    # dry run
    python examples/python/rest/inventory_wms_adjustment.py --execute
    python examples/python/rest/inventory_wms_adjustment.py --execute --unit-cost 99.99
    python examples/python/rest/inventory_wms_adjustment.py --execute --quantity -1  # write off
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


def get_qty_on_hand(base_url: str, headers: dict, verify_ssl: bool,
                     item_id: str, location_id: str) -> float:
    """Read qty_on_hand for an item at a location via OData."""
    item = httpx.get(f"{base_url}/odataservice/odata/table/inv_mast",
                     params={"$select": "inv_mast_uid", "$filter": f"item_id eq '{item_id}'"},
                     headers=headers, verify=verify_ssl, timeout=30.0).json()["value"]
    if not item:
        raise SystemExit(f"No such item: {item_id!r}")
    uid = item[0]["inv_mast_uid"]
    loc = httpx.get(f"{base_url}/odataservice/odata/table/inv_loc",
                    params={"$select": "qty_on_hand,primary_bin,track_bins",
                            "$filter": f"inv_mast_uid eq {uid} and location_id eq {location_id}"},
                    headers=headers, verify=verify_ssl, timeout=30.0).json()["value"]
    if not loc:
        raise SystemExit(f"Item {item_id!r} is not stocked at location {location_id!r}")
    return loc[0]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Post a WMS inventory adjustment (docs/15 inventory/inventoryadjustments)"
    )
    parser.add_argument("--execute", action="store_true", help="Actually POST (default: dry run)")
    parser.add_argument("--item-id", default="GBY")
    parser.add_argument("--location-id", default="40")
    parser.add_argument("--quantity", type=float, default=1,
                        help="SIGNED DELTA -- positive adds, negative removes")
    parser.add_argument("--uom", default="EA")
    parser.add_argument("--reason", default="ADJUST",
                        help="Must be an ACTIVE reason record -- see docstring")
    parser.add_argument("--bin", default=None,
                        help="Required if the location is bin-tracked. If omitted, this "
                             "script looks up inv_loc.primary_bin for you.")
    parser.add_argument("--unit-cost", type=float, default=None,
                        help="If given, uses createWmsAdjustmentWithCost -- the value is "
                             "honored exactly, unlike PO's UnitPrice")
    args = parser.parse_args()

    print("Other REST Families - WMS Inventory Adjustment")
    print("=" * 60)

    config = load_config()
    token_data = get_token(config)
    headers = get_auth_headers(token_data["AccessToken"])
    print(f"Server: {config.base_url}")

    loc = get_qty_on_hand(config.base_url, headers, config.verify_ssl,
                          args.item_id, args.location_id)
    bin_cd = args.bin or loc.get("primary_bin") or ""
    print(f"\n{args.item_id} @ location {args.location_id}: "
          f"qty_on_hand={loc['qty_on_hand']}  track_bins={loc['track_bins']}  "
          f"bin={bin_cd!r}")
    if loc["track_bins"] == "Y" and not bin_cd:
        raise SystemExit("Location is bin-tracked and no bin was found/given -- "
                         "the create will fail with \"Bin is required.\"")

    route = "createWmsAdjustmentWithCost" if args.unit_cost is not None else "createWmsAdjustment"
    params = {
        "locationId": args.location_id, "reason": args.reason, "approved": "Y",
        "description": "ZZ API DOC TEST", "itemId": args.item_id,
        "unitQuantity": str(args.quantity), "unitOfMeasure": args.uom,
        "binCd": bin_cd, "lotCd": "", "serialNumber": "",
    }
    if args.unit_cost is not None:
        params["unitCost"] = str(args.unit_cost)

    if not args.execute:
        print(f"\nDRY RUN - would POST to /api/inventory/inventoryadjustments/{route}")
        print("  with query parameters:")
        for k, v in params.items():
            print(f"    {k}={v!r}")
        print("\nRe-run with --execute to actually post it.")
        return

    r = httpx.post(f"{config.base_url}/api/inventory/inventoryadjustments/{route}",
                   params=params, headers=headers, verify=config.verify_ssl, timeout=90.0)
    if r.status_code != 200:
        print(f"\nAdjustment failed: HTTP {r.status_code}\n{r.text[:500]}")
        raise SystemExit(1)

    adj = r.json()
    line = adj["Lines"]["list"][0]
    print(f"\nAdjustmentNo={adj['AdjustmentNo']}  Cost={line['Cost']}")

    after = get_qty_on_hand(config.base_url, headers, config.verify_ssl,
                            args.item_id, args.location_id)
    print(f"qty_on_hand: {loc['qty_on_hand']} -> {after['qty_on_hand']} "
          f"(delta {args.quantity:+.0f} applied)")


if __name__ == "__main__":
    main()
