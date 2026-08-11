"""
Set an Item's Primary Bin or Primary Supplier at a Location (Item service)

Update an item's primary bin or primary supplier for one stocking location
via the Item service's nested Form -> List -> detail pattern, with a
MANDATORY OData read-back: the primary-supplier write silently no-ops when
the supplier has no location-level row (inventory_supplier_x_loc), while the
transaction still reports Succeeded = 1.

Mirrors: docs/recipes/set-primary-bin-supplier.md

Usage:
    python examples/python/recipes/set_primary_bin_supplier.py                          # dry run, supplier variant
    python examples/python/recipes/set_primary_bin_supplier.py --target bin             # dry run, bin variant
    python examples/python/recipes/set_primary_bin_supplier.py --execute                # write + verify supplier
    python examples/python/recipes/set_primary_bin_supplier.py --target bin --execute   # write + verify bin
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from common.auth import get_token, get_auth_headers, get_ui_server_url
from common.config import load_config

import warnings
warnings.filterwarnings("ignore")

# --- Configuration (generic placeholders -- substitute your own) ------------
ITEM_ID = "WIDGET-001"
LOCATION_ID = "10"
SUPPLIER_ID = "10050"   # --target supplier: must already have an
                        # inventory_supplier_x_loc row at LOCATION_ID
PRIMARY_BIN = "A01-02"  # --target bin


def build_payload(target: str) -> dict:
    """Build the nested Item payload for the chosen target.

    Status "New" with populated Keys updates the existing keyed record --
    it does not create a new item.

    Args:
        target: "supplier" (Form -> List -> List) or "bin" (Form -> List -> Form).

    Returns:
        dict: Complete Transaction API payload.
    """
    if target == "supplier":
        detail = {"Name": "SUPPLIER_X_LOCATION.supplier_x_location", "Type": "List",
                  "Keys": ["supplier_id"],
                  "Rows": [{"Edits": [
                      {"Name": "supplier_id", "Value": SUPPLIER_ID},
                      {"Name": "primary_supplier", "Value": "ON"},
                  ]}]}
    else:
        detail = {"Name": "TABPAGE_18.inv_loc_detail", "Type": "Form",
                  "Keys": ["location_id"],
                  "Rows": [{"Edits": [
                      {"Name": "location_id", "Value": LOCATION_ID},
                      {"Name": "bin", "Value": PRIMARY_BIN},
                  ]}]}
    return {
        "Name": "Item",
        "UseCodeValues": False,
        "Transactions": [{
            "Status": "New",  # updates the keyed record; does not create a new item
            "DataElements": [
                {"Name": "TABPAGE_1.tp_1_dw_1", "Type": "Form", "Keys": ["item_id"],
                 "Rows": [{"Edits": [{"Name": "item_id", "Value": ITEM_ID}]}]},
                {"Name": "TABPAGE_17.invloclist", "Type": "List", "Keys": ["location_id"],
                 "Rows": [{"Edits": [{"Name": "location_id", "Value": LOCATION_ID}]}]},
                detail,
            ],
        }],
    }


def read_inv_loc_field(config, headers: dict, field: str) -> str:
    """Resolve inv_mast_uid from ITEM_ID, then read one inv_loc field.

    Args:
        config: Loaded P21Config.
        headers: Auth headers.
        field: inv_loc column to read (primary_supplier_id or primary_bin).

    Returns:
        str: The field's current value as a string.
    """
    mast = httpx.get(
        f"{config.base_url}/odataservice/odata/table/inv_mast",
        params={"$filter": f"item_id eq '{ITEM_ID}'", "$select": "inv_mast_uid"},
        headers=headers, verify=config.verify_ssl, follow_redirects=True,
    )
    mast.raise_for_status()
    inv_mast_uid = mast.json()["value"][0]["inv_mast_uid"]

    loc = httpx.get(
        f"{config.base_url}/odataservice/odata/table/inv_loc",
        params={
            "$filter": f"inv_mast_uid eq {inv_mast_uid} and location_id eq {LOCATION_ID}",
            "$select": field,
        },
        headers=headers, verify=config.verify_ssl, follow_redirects=True,
    )
    loc.raise_for_status()
    return str(loc.json()["value"][0][field])


def main() -> None:
    """Entry point: build payload, POST on --execute, then verify via OData."""
    parser = argparse.ArgumentParser(
        description="Set primary bin/supplier (docs/recipes/set-primary-bin-supplier.md)")
    parser.add_argument("--target", choices=["supplier", "bin"], default="supplier",
                        help="Which primary to set (default: supplier)")
    parser.add_argument("--execute", action="store_true",
                        help="Actually POST the transaction (default: dry run)")
    args = parser.parse_args()

    print(f"Recipe - Set Primary {args.target.capitalize()} at a Location (Item service)")
    print("=" * 60)

    payload = build_payload(args.target)

    if not args.execute:
        print("\nDRY RUN - payload that would be POSTed to {ui_server}/api/v2/transaction:")
        print(json.dumps(payload, indent=2))
        print("\nRe-run with --execute to POST it.")
        return

    config = load_config()
    token_data = get_token(config)
    headers = get_auth_headers(token_data["AccessToken"])
    ui_server = get_ui_server_url(config.base_url, token_data["AccessToken"], config.verify_ssl)
    print(f"UI Server: {ui_server}")

    resp = httpx.post(f"{ui_server}/api/v2/transaction",
                      headers=headers, json=payload, verify=config.verify_ssl,
                      follow_redirects=True, timeout=120)
    resp.raise_for_status()
    result = resp.json()
    print(f"Succeeded: {result['Summary']['Succeeded']}, "
          f"Failed: {result['Summary']['Failed']}")
    for msg in result.get("Messages") or []:
        print(f"  {msg}")  # watch for 'Unexpected response window: Item Issues Detected'

    # MANDATORY verification -- a silent no-op still reports Succeeded = 1.
    # Supplier: write the inventory_supplier_x_loc flag, READ inv_loc.primary_supplier_id.
    print("\nVerify (OData read-back):")
    if args.target == "supplier":
        actual = read_inv_loc_field(config, headers, "primary_supplier_id")
        if actual == SUPPLIER_ID:
            print(f"  VERIFIED: primary_supplier_id = {actual}")
        else:
            # Most likely cause: no inventory_supplier_x_loc row at this location.
            # Add the location supplier row first, then set the flag again.
            print(f"  SILENT NO-OP: primary_supplier_id is {actual}, expected {SUPPLIER_ID}")
    else:
        actual = read_inv_loc_field(config, headers, "primary_bin")
        if actual == PRIMARY_BIN:
            print(f"  VERIFIED: primary_bin = {actual}")
        else:
            print(f"  MISMATCH: primary_bin is {actual}, expected {PRIMARY_BIN}")


if __name__ == "__main__":
    main()
