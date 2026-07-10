"""
Create Bins in Bulk (BinLocation)

Bulk-create warehouse bins with the BinLocation service -- one transaction
per bin, tens per POST. Constants are cloned from a "twin" bin of the same
bin_type at the location; bins that already exist are skipped so re-running
is safe. IgnoreDisabled: true at the payload TOP LEVEL is mandatory
(frozen_flag and other system columns are disabled on the bin form).

Mirrors: docs/recipes/create-bins.md

Usage:
    python examples/python/recipes/create_bins.py            # dry run (default)
    python examples/python/recipes/create_bins.py --execute  # skip-existing check, POST + verify
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
COMPANY_ID = "ACME"
LOCATION_ID = "10"
NEW_BIN_IDS = ["A01-02-01", "A01-02-02", "A01-02-03", "A01-02-04"]
BATCH_SIZE = 20  # tens of transactions per POST is fine and fast

# Constants cloned from a "twin" bin of the same bin_type at this location.
# Flags come back Y/N from the database -- convert to ON/OFF for the form.
TWIN = {
    "bin_type": "SHELF",
    "putaway_zone_id": "ZONE-A", "pick_zone_id": "ZONE-A",
    "bin_length": "10", "bin_width": "10", "bin_height": "11",
    "warehouse_sequence": "1", "putaway_zone_sequence": "1", "pick_zone_sequence": "1",
    "max_unique_items": "0",
    "pick_locked_flag": "OFF", "put_locked_flag": "OFF",
    "full_flag": "OFF", "frozen_flag": "OFF",
    "consolidation_bin_flag": "OFF", "stage_bin_flag": "OFF", "door_bin_flag": "OFF",
}


def build_bin_transaction(bin_id: str, location_id: str, twin: dict) -> dict:
    """Build one Transaction object per bin (keys first, then twin constants).

    Args:
        bin_id: New bin ID to create.
        location_id: Stocking location for the bin.
        twin: Field constants cloned from an existing bin of the same type.

    Returns:
        dict: Transaction object for the BinLocation payload.
    """
    edits = [
        {"Name": "company_id", "Value": COMPANY_ID},
        {"Name": "location_id", "Value": location_id},
        {"Name": "bin_id", "Value": bin_id},
    ] + [{"Name": name, "Value": value} for name, value in twin.items()]
    return {
        "Status": "New",
        "DataElements": [{
            "Name": "FORM.form", "Type": "Form",
            "Keys": ["company_id", "location_id", "bin_id"],
            "Rows": [{"Edits": edits}],
        }],
    }


def build_payload(bin_ids: list[str]) -> dict:
    """Wrap bin transactions in the top-level BinLocation payload.

    Args:
        bin_ids: Bin IDs for this batch.

    Returns:
        dict: Complete Transaction API payload (IgnoreDisabled at top level).
    """
    return {
        "Name": "BinLocation",
        "UseCodeValues": False,
        "IgnoreDisabled": True,  # TOP LEVEL -- inside a Transaction it is silently ignored
        "Transactions": [build_bin_transaction(b, LOCATION_ID, TWIN) for b in bin_ids],
    }


def main() -> None:
    """Entry point: dry run prints the payload; --execute skips existing bins,
    POSTs batches, and reads the created bins back via p21_view_bin."""
    parser = argparse.ArgumentParser(
        description="Bulk-create warehouse bins (docs/recipes/create-bins.md)")
    parser.add_argument("--execute", action="store_true",
                        help="Actually POST the transactions (default: dry run)")
    args = parser.parse_args()

    print("Recipe - Create Bins in Bulk (BinLocation)")
    print("=" * 60)

    if not args.execute:
        print("\nDRY RUN - payload that would be POSTed to {ui_server}/api/v2/transaction")
        print("(at execute time, bins that already exist at the location are skipped):")
        print(json.dumps(build_payload(NEW_BIN_IDS), indent=2))
        print("\nRe-run with --execute to POST it.")
        return

    config = load_config()
    token_data = get_token(config)
    headers = get_auth_headers(token_data["AccessToken"])
    ui_server = get_ui_server_url(config.base_url, token_data["AccessToken"], config.verify_ssl)
    print(f"UI Server: {ui_server}")

    # Skip-existing check via the p21_view_bin view (raw bin table isn't always in OData)
    existing_resp = httpx.get(
        f"{config.base_url}/odataservice/odata/view/p21_view_bin",
        params={"$filter": f"location_id eq {LOCATION_ID}", "$select": "bin_id"},
        headers=headers, verify=config.verify_ssl, follow_redirects=True,
    )
    existing_resp.raise_for_status()
    existing = {row["bin_id"] for row in existing_resp.json()["value"]}

    to_create = [b for b in NEW_BIN_IDS if b not in existing]
    print(f"{len(NEW_BIN_IDS) - len(to_create)} already exist, creating {len(to_create)}")

    for start in range(0, len(to_create), BATCH_SIZE):
        batch = to_create[start:start + BATCH_SIZE]
        resp = httpx.post(f"{ui_server}/api/v2/transaction",
                          headers=headers, json=build_payload(batch),
                          verify=config.verify_ssl, follow_redirects=True, timeout=300)
        resp.raise_for_status()
        result = resp.json()

        summary = result["Summary"]
        print(f"Batch {start // BATCH_SIZE + 1}: "
              f"Succeeded={summary['Succeeded']}, Failed={summary['Failed']}")
        if summary["Failed"] > 0:
            for msg in result.get("Messages") or []:
                print(f"  {msg}")
        # Transactions pass/fail independently -- check each one
        for bin_id, txn in zip(batch, (result.get("Results") or {}).get("Transactions") or []):
            if txn["Status"] != "Passed":
                print(f"  FAILED: {bin_id}")

    # --- Verify: read the new bins back through the p21_view_bin view ---
    print("\nVerify (p21_view_bin read-back -- compare field-for-field against the twin;")
    print("flags are stored Y/N in the database vs ON/OFF on the form):")
    for bin_id in to_create:
        check = httpx.get(
            f"{config.base_url}/odataservice/odata/view/p21_view_bin",
            params={"$filter": f"location_id eq {LOCATION_ID} and bin_id eq '{bin_id}'"},
            headers=headers, verify=config.verify_ssl, follow_redirects=True,
        )
        check.raise_for_status()
        rows = check.json()["value"]
        print(f"  {bin_id}: {'FOUND' if rows else 'MISSING'}")


if __name__ == "__main__":
    main()
