"""
Clone an Existing Inventory Item (Inventory REST API)

Create an item set up like one you already have -- same locations, product
and discount groups, suppliers and costs, units of measure. GET the source
item with its child records, drop the fields that belong to the source
record (uids, stock, its UD row), re-key every row to the new ID, POST the
result as a new item, then re-GET the new item and compare it to the source.

Mirrors: docs/11-Inventory-REST-API.md § Cloning an Existing Item

Usage:
    python examples/python/recipes/clone_item.py                         # dry run (default)
    python examples/python/recipes/clone_item.py --source ITEM-001 \\
        --new-item-id ITEM-002 --new-desc "Widget Assembly, Large" --execute
"""

import argparse
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from common.auth import get_token, get_auth_headers
from common.config import load_config

import warnings
warnings.filterwarnings("ignore")

# --- Configuration (generic placeholders -- substitute your own) ------------
SOURCE_ITEM_ID = "ITEM-001"               # item to copy
NEW_ITEM_ID = "ITEM-002"                  # must not already exist in inv_mast
NEW_ITEM_DESC = "Widget Assembly, Large"  # 40 characters or fewer
EXTENDED_PROPS = "Locations,Suppliers,LocationSuppliers,UnitsOfMeasure"

# Header fields that belong to the source record. UserDefinedFields carries the
# source's own InvMastUdUid and InvMastUid.
DROP_HEADER = {"InvMastUid", "UserDefinedFields"}

# Fields that identify the source record or describe its stock, per child list.
DROP = {
    "Locations": {"QtyOnHand", "MovingAverageCost", "PrimaryBin", "PeriodFirstStocked",
                  "YearFirstStocked", "PatternLikeInvMastUid", "PatternLikeLocationId",
                  "UserDefinedFields"},
    "Suppliers": {"InventorySupplierUid", "UserDefinedFields"},
    "LocationSuppliers": {"InventorySupplierXLocUid", "UserDefinedFields"},
    "UnitsOfMeasure": {"ItemUomUid", "UserDefinedFields"},
}


def build_clone(source: dict, new_item_id: str, new_desc: str,
                supplier_part_no: str) -> dict:
    """Copy the source item, drop identity/stock fields, and re-key it to the new ID.

    Args:
        source: The source item as returned by GET with EXTENDED_PROPS.
        new_item_id: ItemId for the new item.
        new_desc: ItemDesc for the new item (40 characters or fewer).
        supplier_part_no: SupplierPartNo written to every supplier row.

    Returns:
        dict: The POST body for the new item.
    """
    # Top level: drop the source-record fields and any null header fields.
    payload = {k: v for k, v in copy.deepcopy(source).items()
               if k not in DROP_HEADER and not (v is None and k[0].isupper())}
    payload["ItemId"] = new_item_id
    payload["ItemDesc"] = new_desc
    for key, drop in DROP.items():
        rows = []
        for row in (source.get(key) or {}).get("list") or []:
            row = {k: v for k, v in row.items() if k not in drop}
            row["ItemId"] = new_item_id
            if key == "Suppliers":
                row["SupplierPartNo"] = supplier_part_no
            rows.append(row)
        payload[key] = {"list": rows}
    return payload


def get_item(client: httpx.Client, base_url: str, item_id: str) -> httpx.Response:
    """GET one item with its locations, suppliers, location-suppliers and units.

    Args:
        client: Authenticated httpx client.
        base_url: P21 base URL.
        item_id: Item to read.

    Returns:
        httpx.Response: The raw response (404 when the item does not exist).
    """
    return client.get(f"{base_url}/api/inventory/parts/{item_id}",
                      params={"extendedproperties": EXTENDED_PROPS})


def setup_of(item: dict) -> dict:
    """Reduce an item to the setup a clone should share with its source.

    Args:
        item: An item as returned by GET with EXTENDED_PROPS.

    Returns:
        dict: Comparable per-list summaries, independent of ItemId and uids.
    """
    def rows(key: str) -> list:
        return (item.get(key) or {}).get("list") or []
    return {
        "Locations": sorted((r["LocationId"], r.get("ProductGroupId"), r.get("Stockable"),
                             r.get("Sellable")) for r in rows("Locations")),
        "Suppliers": sorted((r["SupplierId"], r.get("DivisionId"), r.get("Cost"),
                             r.get("ListPrice")) for r in rows("Suppliers")),
        "LocationSuppliers": sorted((r["LocationId"], r["SupplierId"], r.get("PrimarySupplier"))
                                    for r in rows("LocationSuppliers")),
        "UnitsOfMeasure": sorted((r["UnitOfMeasure"], r.get("UnitSize"))
                                 for r in rows("UnitsOfMeasure")),
    }


def main() -> None:
    """Entry point: GET the source, build the clone, POST on --execute, then verify."""
    parser = argparse.ArgumentParser(
        description="Clone an inventory item (docs/11-Inventory-REST-API.md)")
    parser.add_argument("--source", default=SOURCE_ITEM_ID, help="Item to copy")
    parser.add_argument("--new-item-id", default=NEW_ITEM_ID, help="ItemId for the new item")
    parser.add_argument("--new-desc", default=NEW_ITEM_DESC, help="ItemDesc, 40 chars or fewer")
    parser.add_argument("--supplier-part-no", default=None,
                        help="SupplierPartNo for every supplier row (default: the new item ID)")
    parser.add_argument("--execute", action="store_true",
                        help="Actually POST the new item (default: dry run)")
    args = parser.parse_args()
    supplier_part_no = args.supplier_part_no or args.new_item_id

    print("Recipe - Clone an Existing Item (Inventory REST API)")
    print("=" * 60)
    if len(args.new_desc) > 40:
        raise SystemExit("ItemDesc is over 40 characters -- P21 silently drops the rest")

    # The source GET is read-only, so even a dry run needs credentials.
    config = load_config()
    token = get_token(config)["AccessToken"]
    headers = get_auth_headers(token)  # Accept: application/json, or the API answers XML

    with httpx.Client(headers=headers, verify=config.verify_ssl, timeout=180,
                      follow_redirects=True) as client:
        # 1. GET the source item with its child records
        resp = get_item(client, config.base_url, args.source)
        resp.raise_for_status()
        source = resp.json()
        payload = build_clone(source, args.new_item_id, args.new_desc, supplier_part_no)

        if not args.execute:
            print(json.dumps(payload, indent=2))
            print("\nDRY RUN -- nothing written. Re-run with --execute to POST the new item.")
            return

        # 2. Refuse to overwrite: the POST fails anyway, but say why up front.
        if get_item(client, config.base_url, args.new_item_id).status_code == 200:
            raise SystemExit(f"{args.new_item_id} already exists -- pick another ID")

        # 3. POST the clone -- trailing slash, or the POST 307s
        resp = client.post(f"{config.base_url}/api/inventory/parts/", json=payload)
        if resp.status_code not in (200, 201):
            raise SystemExit(f"POST {resp.status_code}: {resp.text[:500]}")

        # 4. Re-GET to prove what actually landed -- HTTP 200 alone does not confirm a write
        resp = get_item(client, config.base_url, args.new_item_id)
        resp.raise_for_status()
        new = resp.json()

    print(f"Created {new['ItemId']}: {new['ItemDesc']}")
    for loc in new["Locations"]["list"]:
        print(f"  location {loc['LocationId']}: ProductGroupId={loc.get('ProductGroupId')} "
              f"Stockable={loc.get('Stockable')} Sellable={loc.get('Sellable')}")
    for sup in new["Suppliers"]["list"]:
        print(f"  supplier {sup['SupplierId']}: Cost={sup.get('Cost')} "
              f"ListPrice={sup.get('ListPrice')} SupplierPartNo={sup.get('SupplierPartNo')}")

    want, got = setup_of(source), setup_of(new)
    for key in want:
        status = "OK" if want[key] == got[key] else f"MISMATCH source={want[key]} new={got[key]}"
        print(f"  {key}: {len(got[key])} row(s) -> {status}")


if __name__ == "__main__":
    main()
