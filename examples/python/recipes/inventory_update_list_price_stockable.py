"""
Update a Supplier's ListPrice and a Location's Stockable Flag (Inventory REST API)

GET -> modify -> PUT on /api/inventory/parts/{ItemId}: change
Suppliers.list[].ListPrice (inventory_supplier.list_price) for one supplier
and Locations.list[].Stockable (inv_loc.stockable) for one location, then
read both back twice -- through the REST GET and through OData. By default
the script then puts the original values back and verifies the restore;
pass --keep to leave the new values in place.

Key rules (verified on play 26.1.5950.0, October 2026):
    - PUT the WHOLE payload you got from the GET (with the same
      extendedproperties), changed in place. Leaving a child list out of
      the PUT is not a way to "not touch" it.
    - Stockable takes "Y" / "N" on this API.
    - HTTP 200 alone does not prove the write -- read the columns back.
    - An ItemId containing "/" cannot use this path (the GET 404s).

Mirrors: docs/11-Inventory-REST-API.md#updating-existing-location-fields

Usage:
    python examples/python/recipes/inventory_update_list_price_stockable.py          # dry run
    python examples/python/recipes/inventory_update_list_price_stockable.py --execute \\
        --item-id ITEM-001 --supplier-id 100 --location-id 10 --list-price 11.25 --stockable Y
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

EXTENDED = "Locations,Suppliers,LocationSuppliers,UnitsOfMeasure"


def get_part(http: httpx.Client, base_url: str, item_id: str) -> dict:
    """GET the item with its child lists."""
    resp = http.get(f"{base_url}/api/inventory/parts/{item_id}",
                    params={"extendedproperties": EXTENDED})
    resp.raise_for_status()
    return resp.json()


def put_part(http: httpx.Client, base_url: str, item_id: str, part: dict) -> None:
    """PUT the full item payload back."""
    resp = http.put(f"{base_url}/api/inventory/parts/{item_id}", json=part)
    if resp.status_code != 200:
        raise SystemExit(f"PUT {resp.status_code}: {resp.text[:500]}")


def pick(part: dict, supplier_id: int, location_id: int) -> tuple[dict, dict]:
    """Return the supplier row and the location row to change."""
    sup = next((s for s in part["Suppliers"]["list"] if s["SupplierId"] == supplier_id), None)
    loc = next((x for x in part["Locations"]["list"] if x["LocationId"] == location_id), None)
    if sup is None or loc is None:
        raise SystemExit(f"Supplier {supplier_id} or location {location_id} not on the item")
    return sup, loc


def odata_values(http: httpx.Client, base_url: str, inv_mast_uid: int,
                 supplier_id: int, location_id: int) -> tuple[float, str]:
    """Read inventory_supplier.list_price and inv_loc.stockable over OData."""
    def rows(table: str, flt: str) -> list[dict]:
        r = http.get(f"{base_url}/odataservice/odata/table/{table}", params={"$filter": flt})
        r.raise_for_status()
        return r.json()["value"]

    sup = rows("inventory_supplier",
               f"inv_mast_uid eq {inv_mast_uid} and supplier_id eq {supplier_id}")[0]
    loc = rows("inv_loc", f"inv_mast_uid eq {inv_mast_uid} and location_id eq {location_id}")[0]
    return float(sup["list_price"]), loc["stockable"]


def write_and_verify(http: httpx.Client, base_url: str, args: argparse.Namespace,
                     list_price: float, stockable: str, label: str) -> bool:
    """GET, set both values, PUT, then verify through REST and OData."""
    part = get_part(http, base_url, args.item_id)
    sup, loc = pick(part, args.supplier_id, args.location_id)
    sup["ListPrice"] = list_price
    loc["Stockable"] = stockable
    put_part(http, base_url, args.item_id, part)

    again = get_part(http, base_url, args.item_id)
    sup2, loc2 = pick(again, args.supplier_id, args.location_id)
    db_price, db_stockable = odata_values(http, base_url, again["InvMastUid"],
                                          args.supplier_id, args.location_id)
    ok = (float(sup2["ListPrice"]) == list_price and loc2["Stockable"] == stockable
          and db_price == list_price and db_stockable == stockable)
    print(f"{label}: REST ListPrice={sup2['ListPrice']} Stockable={loc2['Stockable']} | "
          f"OData list_price={db_price} stockable={db_stockable} -> {'OK' if ok else 'MISMATCH'}")
    return ok


def main() -> None:
    """Entry point: show current values (dry run) or write, verify and restore."""
    p = argparse.ArgumentParser(description="Update ListPrice + Stockable via the Inventory REST API")
    p.add_argument("--execute", action="store_true", help="PUT (default: dry run)")
    p.add_argument("--keep", action="store_true", help="Do not restore the original values")
    p.add_argument("--item-id", default="ITEM-001")
    p.add_argument("--supplier-id", type=int, default=100)
    p.add_argument("--location-id", type=int, default=10)
    p.add_argument("--list-price", type=float, default=11.25)
    p.add_argument("--stockable", choices=["Y", "N"], default="Y")
    args = p.parse_args()

    print("Inventory REST - update supplier ListPrice + location Stockable")
    print("=" * 60)
    if not args.execute:
        print(f"\nDRY RUN - would GET /api/inventory/parts/{args.item_id}"
              f"?extendedproperties={EXTENDED},\n  set Suppliers[{args.supplier_id}].ListPrice="
              f"{args.list_price} and Locations[{args.location_id}].Stockable={args.stockable},\n"
              f"  PUT the full payload back, verify, then restore the originals.")
        print("\nRe-run with --execute to write.")
        return

    config = load_config()
    token = get_token(config)["AccessToken"]
    with httpx.Client(headers=get_auth_headers(token), verify=config.verify_ssl,
                      follow_redirects=True, timeout=180) as http:
        sup, loc = pick(get_part(http, config.base_url, args.item_id),
                        args.supplier_id, args.location_id)
        original = (float(sup["ListPrice"]), loc["Stockable"])
        print(f"\nBefore: ListPrice={original[0]} Stockable={original[1]}")

        write_and_verify(http, config.base_url, args, args.list_price, args.stockable, "Changed ")
        if not args.keep:
            write_and_verify(http, config.base_url, args, original[0], original[1], "Restored")


if __name__ == "__main__":
    main()
