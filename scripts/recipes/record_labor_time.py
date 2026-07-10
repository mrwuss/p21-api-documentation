"""
Record Labor Time on a Production Order (TimeEntry service)

Post a technician's labor hours to a production order with the TimeEntry
service, then read the labor grid back via POST /api/v2/transaction/get.
Labor grid fields must be entered in strict order (prod_order_number ->
item_id -> component_labor_id -> start_time -> end_time) or downstream
fields stay disabled. Time ACCUMULATES across entries -- re-posting the same
entry doubles the labor.

Mirrors: docs/recipes/record-labor-time.md

Usage:
    python scripts/recipes/record_labor_time.py            # dry run (default)
    python scripts/recipes/record_labor_time.py --execute  # POST + read-back
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
PROD_ORDER = "1000123"
TECHNICIAN_ID = "300"          # a CONTACT id, not a P21 user id
ENTRY_DATE = "2030-01-05"      # accounting period for this date must be open
ASSEMBLY_ITEM_ID = "ASSY-100"  # the assembly LINE's item (not the component)
LABOR_COMPONENT_ID = "LABOR-SHOP"
START_TIME = "2030-01-05T08:00:00"
END_TIME = "2030-01-05T12:00:00"
LABOR_TYPE = "Rate"            # required -- valid: Rate, OT Rate, Prem Rate


def build_time_entry_payload() -> dict:
    """Build the TimeEntry payload: technician header + one labor line.

    Returns:
        dict: Complete Transaction API payload.
    """
    return {
        "Name": "TimeEntry",
        "UseCodeValues": False,
        "Transactions": [{
            "Status": "New",
            "DataElements": [
                {
                    "Name": "TP_TECHNICIAN.tp_technician",
                    "Type": "Form",
                    "Keys": [],
                    "Rows": [{
                        "Edits": [
                            {"Name": "company_id", "Value": COMPANY_ID},
                            {"Name": "technician_id", "Value": TECHNICIAN_ID},  # CONTACT id
                            {"Name": "entry_date", "Value": ENTRY_DATE},
                        ],
                        "RelativeDateEdits": [],
                    }],
                },
                {
                    "Name": "TP_LABORRECORDING.prod_order_line_comp_labor",
                    "Type": "List",
                    "Keys": ["prod_order_number"],
                    "Rows": [{
                        # Strict order: prod_order_number -> item_id ->
                        # component_labor_id -> start_time -> end_time
                        "Edits": [
                            {"Name": "prod_order_number", "Value": PROD_ORDER},
                            {"Name": "item_id", "Value": ASSEMBLY_ITEM_ID},
                            {"Name": "component_labor_id", "Value": LABOR_COMPONENT_ID},
                            {"Name": "start_time", "Value": START_TIME},
                            {"Name": "end_time", "Value": END_TIME},
                            {"Name": "labor_type_cd", "Value": LABOR_TYPE},
                        ],
                        "RelativeDateEdits": [],
                    }],
                },
            ],
        }],
    }


def read_labor_grid(ui_server: str, headers: dict, verify_ssl: bool) -> None:
    """Read the labor grid back for PROD_ORDER and print accumulated time.

    Args:
        ui_server: UI server URL.
        headers: Auth headers.
        verify_ssl: Whether to verify SSL certificates.
    """
    get_payload = {
        "ServiceName": "TimeEntry",
        "TransactionStates": [{
            "DataElementName": "TP_LABORRECORDING.prod_order_line_comp_labor",
            "Keys": [{"Name": "prod_order_number", "Value": PROD_ORDER}],
        }],
    }
    resp = httpx.post(f"{ui_server}/api/v2/transaction/get",
                      headers=headers, json=get_payload, verify=verify_ssl,
                      follow_redirects=True, timeout=60)
    resp.raise_for_status()
    for txn in resp.json().get("Transactions", []):
        for de in txn.get("DataElements", []):
            for row in de.get("Rows", []):
                fields = {e["Name"]: e["Value"] for e in row.get("Edits", [])}
                if fields.get("prod_order_number"):
                    print(f"  {fields.get('component_labor_id') or fields.get('service_labor_id')}: "
                          f"time_worked={fields.get('time_worked')}")


def main() -> None:
    """Entry point: build payload, POST on --execute, then read the grid back."""
    parser = argparse.ArgumentParser(
        description="Record labor time (docs/recipes/record-labor-time.md)")
    parser.add_argument("--execute", action="store_true",
                        help="Actually POST the time entry -- labor ACCUMULATES, "
                             "re-posting doubles it (default: dry run)")
    args = parser.parse_args()

    print("Recipe - Record Labor Time (TimeEntry)")
    print("=" * 60)

    payload = build_time_entry_payload()

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
        raise SystemExit("Time entry failed")

    # --- Verify: read back the labor grid for the order. time_worked should
    # reflect the ACCUMULATED total, not just this entry. ---
    print("\nVerify (labor grid read-back):")
    read_labor_grid(ui_server, headers, config.verify_ssl)


if __name__ == "__main__":
    main()
