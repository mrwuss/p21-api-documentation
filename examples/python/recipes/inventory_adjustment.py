"""
Adjust On-Hand Quantity / Write-Off (InventoryAdjustment service)

Post an inventory adjustment -- a signed on-hand quantity change with no
invoice -- via the InventoryAdjustment service, then read the adjustment
back by its server-generated adjustment_number. unit_quantity is the SIGNED
DELTA (e.g. -5 writes off 5 units), not the new on-hand, and the save posts
the adjustment immediately (no draft state).

Mirrors: docs/recipes/inventory-adjustment.md

Usage:
    python examples/python/recipes/inventory_adjustment.py            # dry run (default)
    python examples/python/recipes/inventory_adjustment.py --execute  # POST + read-back
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
REASON_ID = "ADJUST"          # the reason's DISPLAY TEXT (UseCodeValues: false)
DESCRIPTION = "Cycle count write-off"
ITEM_ID = "WIDGET-001"
UNIT_QUANTITY = "-5"          # SIGNED delta, NOT the new on-hand


def build_adjustment_payload() -> dict:
    """Build the InventoryAdjustment payload: header form + one line.

    adjustment_number is server-generated -- leave it unset on a new
    adjustment.

    Returns:
        dict: Complete Transaction API payload.
    """
    return {
        "Name": "InventoryAdjustment",
        "UseCodeValues": False,  # reason_id is the display text, not the code
        "Transactions": [{
            "Status": "New",
            "DataElements": [
                {
                    "Name": "TABPAGE_1.tp_1_dw_1",
                    "Type": "Form",
                    "Keys": [],
                    "Rows": [{
                        "Edits": [
                            {"Name": "company_id", "Value": COMPANY_ID},
                            {"Name": "location_id", "Value": LOCATION_ID},
                            {"Name": "reason_id", "Value": REASON_ID},  # display text
                            {"Name": "inv_adj_description", "Value": DESCRIPTION},
                        ],
                        "RelativeDateEdits": [],
                    }],
                },
                {
                    "Name": "TABPAGE_17.tp_17_dw_17",
                    "Type": "List",
                    "Keys": [],
                    "Rows": [{
                        "Edits": [
                            {"Name": "item_id", "Value": ITEM_ID},
                            {"Name": "unit_quantity", "Value": UNIT_QUANTITY},  # signed delta
                        ],
                        "RelativeDateEdits": [],
                    }],
                },
            ],
        }],
    }


def extract_adjustment_number(result: dict) -> str | None:
    """Pull the server-generated adjustment_number out of the echoed DataElements.

    Args:
        result: Parsed JSON response from POST /api/v2/transaction.

    Returns:
        str | None: The adjustment number, if present.
    """
    adjustment_number = None
    for txn in result.get("Results", {}).get("Transactions", []):
        for de in txn.get("DataElements", []):
            if de.get("Name") == "TABPAGE_1.tp_1_dw_1":
                for row in de.get("Rows", []):
                    for edit in row.get("Edits", []):
                        if edit["Name"] == "adjustment_number" and edit.get("Value"):
                            adjustment_number = edit["Value"]
    return adjustment_number


def read_adjustment(ui_server: str, headers: dict, verify_ssl: bool,
                    adjustment_number: str) -> None:
    """Read the adjustment back by its key and print the fields that matter.

    Args:
        ui_server: UI server URL.
        headers: Auth headers.
        verify_ssl: Whether to verify SSL certificates.
        adjustment_number: Server-generated adjustment number.
    """
    get_payload = {
        "ServiceName": "InventoryAdjustment",
        "TransactionStates": [{
            "DataElementName": "TABPAGE_1.tp_1_dw_1",
            "Keys": [{"Name": "adjustment_number", "Value": adjustment_number}],
        }],
    }
    resp = httpx.post(f"{ui_server}/api/v2/transaction/get",
                      headers=headers, json=get_payload, verify=verify_ssl,
                      follow_redirects=True, timeout=60)
    resp.raise_for_status()
    wanted = ("adjustment_number", "location_id", "reason_id",
              "item_id", "unit_quantity", "new_qoh")
    for txn in resp.json().get("Transactions", []):
        for de in txn.get("DataElements", []):
            for row in de.get("Rows", []):
                for edit in row.get("Edits", []):
                    if edit["Name"] in wanted:
                        print(f"  {edit['Name']}: {edit['Value']}")


def main() -> None:
    """Entry point: build payload, POST on --execute, then read it back."""
    parser = argparse.ArgumentParser(
        description="Inventory adjustment (docs/recipes/inventory-adjustment.md)")
    parser.add_argument("--execute", action="store_true",
                        help="Actually POST the adjustment -- the save POSTS it "
                             "immediately, no draft state (default: dry run)")
    args = parser.parse_args()

    print("Recipe - Adjust On-Hand Quantity (InventoryAdjustment)")
    print("=" * 60)

    payload = build_adjustment_payload()

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
    resp.raise_for_status()  # HTTP 200 even on failure -- check the Summary
    result = resp.json()

    summary = result["Summary"]
    print(f"Succeeded: {summary['Succeeded']}, Failed: {summary['Failed']}")
    if summary["Failed"] > 0:
        for msg in result.get("Messages", []):
            print(f"  {msg}")
        raise SystemExit("Adjustment failed")

    adjustment_number = extract_adjustment_number(result)
    print(f"Adjustment number: {adjustment_number}")
    if not adjustment_number:
        raise SystemExit("No adjustment_number in the echoed DataElements")

    # --- Verify: read the adjustment back by its server-generated key ---
    print("\nVerify (transaction/get read-back):")
    read_adjustment(ui_server, headers, config.verify_ssl, adjustment_number)


if __name__ == "__main__":
    main()
