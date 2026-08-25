"""
Reassign a Customer and Ship-To Salesrep (Customer + ShipTo services)

Move a customer and its default ship-to from one salesrep to another, then
read both grids back over OData.

The two grids delete differently, and that is the whole trick:

  * CUSTOMERSALESREP.customersalesrep has no delete_flag. It removes rows
    with row_status_flag -- the label "Delete", never the code_p21 integer
    700, because UseCodeValues is False.
  * TABPAGE_SALESREP.tabpage_salesrep on ShipTo does have delete_flag,
    retired with "ON".

Promotion has to come first in both payloads: P21 refuses to leave a record
without a primary salesrep, so a row that deletes the outgoing rep before the
incoming one is promoted fails the whole transaction.

Mirrors: docs/recipes/reassign-salesrep.md

Usage:
    python examples/python/recipes/reassign_salesrep.py            # dry run (default)
    python examples/python/recipes/reassign_salesrep.py --execute  # POST + verify
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
CUSTOMER_ID = "100198"
SHIP_TO_ID = "100198"       # a DEFAULT ship-to: address_id == customer_id
OLD_SALESREP_ID = "100"
NEW_SALESREP_ID = "200"

ROW_STATUS_ACTIVE = 704     # code_p21 label "Active" -- what OData returns
ROW_STATUS_DELETE = 700     # code_p21 label "Delete"


def build_customer_payload() -> dict:
    """Build the Customer payload: header salesrep_id plus the grid swap.

    The grid rows are ordered promote-then-delete on purpose. Reversing them
    fails with "This salesrep is set up as the primary salesrep for this
    record. You cannot delete it."

    Returns:
        dict: Complete Transaction API payload.
    """
    return {
        "Name": "Customer",
        "UseCodeValues": False,
        "Transactions": [{
            "Status": "New",
            "DataElements": [
                {
                    "Name": "TABPAGE_1.tp_1_dw_1",
                    "Type": "Form",
                    "Keys": [],
                    "Rows": [{
                        "Edits": [
                            {"Name": "company_id",  "Value": COMPANY_ID},
                            {"Name": "customer_id", "Value": CUSTOMER_ID},
                            {"Name": "salesrep_id", "Value": NEW_SALESREP_ID},
                        ],
                        "RelativeDateEdits": [],
                    }],
                },
                {
                    "Name": "CUSTOMERSALESREP.customersalesrep",
                    "Type": "List",
                    "Keys": ["salesrep_id"],
                    "Rows": [
                        {
                            "Edits": [
                                {"Name": "salesrep_id",           "Value": NEW_SALESREP_ID},
                                {"Name": "primary_salesrep_flag", "Value": "ON"},
                                {"Name": "commission_percentage", "Value": "100"},
                            ],
                            "RelativeDateEdits": [],
                        },
                        {
                            "Edits": [
                                {"Name": "salesrep_id",     "Value": OLD_SALESREP_ID},
                                {"Name": "row_status_flag", "Value": "Delete"},
                            ],
                            "RelativeDateEdits": [],
                        },
                    ],
                },
            ],
        }],
    }


def build_shipto_payload() -> dict:
    """Build the ShipTo payload: the sibling grid, retired with delete_flag.

    company_id plus address_id in the Edits is enough to identify the record.
    Sending customer_id as well returns "Column is disabled: customer_id"
    when the ship-to is the customer's DEFAULT.

    Returns:
        dict: Complete Transaction API payload.
    """
    return {
        "Name": "ShipTo",
        "UseCodeValues": False,
        "Transactions": [{
            "Status": "New",
            "DataElements": [
                {
                    "Name": "TABPAGE_1.shiptomain",
                    "Type": "Form",
                    "Keys": [],
                    "Rows": [{
                        "Edits": [
                            {"Name": "company_id", "Value": COMPANY_ID},
                            {"Name": "address_id", "Value": SHIP_TO_ID},
                        ],
                        "RelativeDateEdits": [],
                    }],
                },
                {
                    "Name": "TABPAGE_SALESREP.tabpage_salesrep",
                    "Type": "List",
                    "Keys": ["salesrep_id"],
                    "Rows": [
                        {
                            "Edits": [
                                {"Name": "salesrep_id",      "Value": NEW_SALESREP_ID},
                                {"Name": "primary_salesrep", "Value": "ON"},
                            ],
                            "RelativeDateEdits": [],
                        },
                        {
                            "Edits": [
                                {"Name": "salesrep_id", "Value": OLD_SALESREP_ID},
                                {"Name": "delete_flag", "Value": "ON"},
                            ],
                            "RelativeDateEdits": [],
                        },
                    ],
                },
            ],
        }],
    }


def post_transaction(ui_server: str, headers: dict, payload: dict,
                     verify_ssl: bool, label: str) -> None:
    """POST one transaction and fail loudly unless it actually landed.

    Args:
        ui_server: UI server base URL.
        headers: Authorization headers.
        payload: Transaction API payload.
        verify_ssl: Whether to verify TLS certificates.
        label: Human-readable name for the log line.

    Raises:
        SystemExit: If the transaction did not pass.
    """
    response = httpx.post(f"{ui_server}/api/v2/transaction",
                          headers=headers, json=payload, verify=verify_ssl,
                          follow_redirects=True, timeout=120)
    response.raise_for_status()
    result = response.json()

    # HTTP 200 even on failure -- check the Summary, never the status code.
    summary = result["Summary"]
    status = result["Results"]["Transactions"][0]["Status"]
    print(f"{label}: Succeeded={summary['Succeeded']} Failed={summary['Failed']} "
          f"Status={status}")
    if summary["Failed"] > 0 or summary["Succeeded"] == 0 or status != "Passed":
        for msg in result.get("Messages", []):
            print(f"  {msg}")
        raise SystemExit(f"{label} failed")


def odata(base_url: str, headers: dict, table: str, filter_expr: str,
          verify_ssl: bool) -> list[dict]:
    """Query one OData table.

    The key columns here are Edm.Decimal -- quoting the value returns 404
    with "Found operand types 'Edm.Decimal' and 'Edm.String'", so filter
    expressions pass the id bare.

    Args:
        base_url: P21 base URL (OData does not use the UI server).
        headers: Authorization headers.
        table: Table name.
        filter_expr: OData $filter expression.
        verify_ssl: Whether to verify TLS certificates.

    Returns:
        list[dict]: The rows returned.
    """
    response = httpx.get(f"{base_url}/odataservice/odata/table/{table}",
                         params={"$filter": filter_expr}, headers=headers,
                         verify=verify_ssl, follow_redirects=True, timeout=60)
    response.raise_for_status()
    return response.json()["value"]


def main() -> None:
    """Entry point: build both payloads, POST on --execute, then verify."""
    parser = argparse.ArgumentParser(
        description="Reassign a salesrep (docs/recipes/reassign-salesrep.md)")
    parser.add_argument("--execute", action="store_true",
                        help="Actually POST the transactions (default: dry run)")
    args = parser.parse_args()

    print("Recipe - Reassign a Customer and Ship-To Salesrep")
    print("=" * 60)

    customer_payload = build_customer_payload()
    shipto_payload = build_shipto_payload()

    if not args.execute:
        print("\nDRY RUN - payloads that would be POSTed to "
              "{ui_server}/api/v2/transaction:")
        print("\n--- Customer ---")
        print(json.dumps(customer_payload, indent=2))
        print("\n--- ShipTo ---")
        print(json.dumps(shipto_payload, indent=2))
        print("\nRe-run with --execute to POST them.")
        return

    config = load_config()
    token_data = get_token(config)
    headers = get_auth_headers(token_data["AccessToken"])
    ui_server = get_ui_server_url(config.base_url, token_data["AccessToken"],
                                  config.verify_ssl)
    print(f"UI Server: {ui_server}")

    post_transaction(ui_server, headers, customer_payload, config.verify_ssl, "Customer")
    post_transaction(ui_server, headers, shipto_payload, config.verify_ssl, "ShipTo")

    # --- Verify: read both grids back via OData ---
    # Both deletes are soft, so the outgoing rep's rows are still here:
    # row_status_flag 700 on the customer, delete_flag 'Y' on the ship-to.
    print("\nVerify (OData read-back):")
    for row in odata(config.base_url, headers, "customer_salesrep",
                     f"customer_id eq {CUSTOMER_ID}", config.verify_ssl):
        status = row.get("row_status_flag")
        state = "active" if status == ROW_STATUS_ACTIVE else "deleted"
        print(f"  customer: salesrep_id={row.get('salesrep_id')} "
              f"primary={row.get('primary_salesrep_flag')} "
              f"row_status_flag={status} ({state})")

    for row in odata(config.base_url, headers, "ship_to_salesrep",
                     f"ship_to_id eq {SHIP_TO_ID}", config.verify_ssl):
        deleted = row.get("delete_flag") == "Y"
        print(f"  ship-to:  salesrep_id={row.get('salesrep_id')} "
              f"primary={row.get('primary_salesrep')} "
              f"delete_flag={row.get('delete_flag')} "
              f"({'deleted' if deleted else 'active'})")

    print(f"\nOnly rows at row_status_flag={ROW_STATUS_ACTIVE} are live; "
          f"{ROW_STATUS_DELETE} is the soft-deleted state.")


if __name__ == "__main__":
    main()
