"""
Production Order Runbook -- Create to Invoice (checklist + one automated stage)

The runbook page is a checklist, not a script. This file prints that
checklist (stages 1-2 and 4-7: what to call, the fields that matter, and the
trap for each), and automates the stage most people automate first --
Stage 3: generate the production pick ticket at the STOCK location with
m_picktickets (creates the ticket record AND returns the PDF), then read the
new ticket back with POST /api/v2/transaction/get to check its status.

Mirrors: docs/recipes/production-order-runbook.md

Usage:
    python scripts/recipes/production_order_runbook.py            # checklist + dry run
    python scripts/recipes/production_order_runbook.py --execute  # run Stage 3 + read-back
"""

import argparse
import base64
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from common.auth import get_token, get_auth_headers, get_ui_server_url
from common.config import load_config

import warnings
warnings.filterwarnings("ignore")

# --- Configuration (generic placeholders -- substitute your own) ------------
PROD_ORDER = "1000123"   # production order number
STOCK_LOCATION = "10"    # where the components stock (NOT necessarily the make location)

CHECKLIST = """\
Runbook stages (this script automates Stage 3 only -- see the recipe page
docs/recipes/production-order-runbook.md and the linked recipes for the rest):

Stage 1 - Create the production order
  Path A: sales order auto-create (make-to-order) -- enter the assembly line
          via the Interactive API (scripts/recipes/order_with_assembly.py).
          Auto-create NETS AGAINST STOCK: on-hand means no order spawns.
  Path B: direct build-to-stock -- ProductionOrder window: header
          source_loc_id, then TABPAGE_17.tp_17_dw_17 assembly_item_id +
          qty_to_make.
  Traps:  salesrep must be valid at the sales location; order date must
          differ from required date.

Stage 2 - Log labor BEFORE printing (scripts/recipes/record_labor_time.py)
  Trap:   labor added after printing (no reprint) sits on no ticket
          (qty_on_pick_tickets = 0) and completion fails with
          "components have a quantity used of 0."

Stage 3 - Print the pick ticket and form  [AUTOMATED BELOW]
  m_picktickets at POST /api/v2/process/pdfreport, at the STOCK location.
  Traps:  print_pick_ticket on a ProductionOrder transaction emits only at
          the MAKE location; never post an m_* report to /api/v2/transaction
          (it returns Succeeded and emits nothing); the order's form must
          already be printed (prod_order_hdr.printed = 'Y').

Stage 4 - Confirm the pick (Interactive API ONLY)
  ProductionOrderPicking window: load the ticket on
  TP_PRODPICKTICKETCONF.tp_prodpickticketconf (key prod_pick_ticket_number),
  set row_status_flag = "Confirm", save. Confirm EVERY ticket -- parts AND
  labor/intangibles.
  Trap:   a bare Transaction API confirm is a SHELL confirm -- status flips
          to 1962 but qty_applied stays 0 and no stock moves.

Stage 5 - Complete the order (ProductionOrderProcessing window)
  Select the line on TABPAGE_17.tp_17_dw_17, set qty_to_complete; then on
  TABPAGE_ASSEMBLY_BIN.tabpage_assembly_bin set bin_cd and unit_quantity as
  TWO SEPARATE change calls; optional new_cost on TABPAGE_18.tp_18_dw_18; save.
  Trap:   combining bin_cd and unit_quantity in one call drops the quantity.

Stage 6 - Ship and invoice the linked sales order
  Order transaction with print_tix = ON on TP_FRONTCOUNTER.tp_frontcounter,
  then the Shipping service keyed by pick_ticket_no -- retrieve and save
  (create_invoice defaults ON: the save ships AND invoices).
  Traps:  the item needs a packaging code; for contract pricing leave
          unit_price unset.

Stage 7 - Fix quantity fallout (scripts/recipes/inventory_adjustment.py)

Ticket status codes (prod_pick_ticket_hdr.row_status_flag):
  702 Open / 1962 Confirmed / 1268 Completed
  A 1962 alone does not prove stock moved (see shell confirm).
"""


def build_report_payload() -> dict:
    """Build the Stage 3 m_picktickets payload for PROD_ORDER at STOCK_LOCATION.

    Returns:
        dict: Complete pdfreport payload (numeric Status/Type 0, Keys []).
    """
    return {
        "Name": "m_picktickets",
        "UseCodeValues": True,  # m_picktickets REQUIRES code values; False returns HTTP 500
        "Transactions": [{
            "Status": 0,        # reports use numeric 0, not "New"
            "DataElements": [{
                "Keys": [],
                "Type": 0,
                "Name": "TABPAGE_1.tp_1_dw_1",
                "Rows": [{"Edits": [
                    {"Name": "create_pick_ticket_type", "Value": "P"},  # code "P" = Production Order
                    {"Name": "beg_prod_order", "Value": PROD_ORDER},
                    {"Name": "end_prod_order", "Value": PROD_ORDER},
                    {"Name": "location_id", "Value": STOCK_LOCATION},
                ]}],
            }],
        }],
    }


def generate_pick_ticket(ui_server: str, headers: dict, verify_ssl: bool) -> str:
    """Run m_picktickets, save the PDF, and return the saved file name.

    Args:
        ui_server: UI server URL.
        headers: Auth headers.
        verify_ssl: Whether to verify SSL certificates.

    Returns:
        str: The saved PDF file name (contains the ticket number).

    Raises:
        SystemExit: When the report fails.
    """
    resp = httpx.post(
        f"{ui_server}/api/v2/process/pdfreport",  # NOT /api/v2/transaction (silent no-op there)
        headers=headers, json=build_report_payload(), verify=verify_ssl,
        follow_redirects=True, timeout=120,
    )
    resp.raise_for_status()
    result = resp.json()

    if not isinstance(result, list):  # errors come back as an envelope, not an array
        raise SystemExit(f"Report failed: {result.get('ErrorMessage')}")

    doc = result[0]
    if doc["ResponseStatus"]["StatusCode"] != "Success" or not doc.get("DocumentData"):
        raise SystemExit(f"Report failed: {doc['ResponseStatus'].get('Message')}")

    file_name = doc["FileName"]  # e.g. "PPT123456 PRODUCTION_PICK_TICKET.pdf"
    with open(file_name, "wb") as f:
        f.write(base64.b64decode(doc["DocumentData"]))
    print(f"Saved {file_name}")
    return file_name


def read_ticket_status(ui_server: str, headers: dict, verify_ssl: bool,
                       ticket_no: str) -> None:
    """Read the new ticket back via /transaction/get and print its status.

    Args:
        ui_server: UI server URL.
        headers: Auth headers.
        verify_ssl: Whether to verify SSL certificates.
        ticket_no: Production pick-ticket number (from the PDF FileName).
    """
    get_payload = {
        "ServiceName": "ProductionOrderPicking",
        "TransactionStates": [{
            "DataElementName": "TP_PRODPICKTICKETCONF.tp_prodpickticketconf",
            "Keys": [{"Name": "prod_pick_ticket_number", "Value": ticket_no}],
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
                if "row_status_flag" in fields:
                    # 702 = Open, 1962 = Confirmed, 1268 = Completed
                    print(f"Ticket {fields.get('prod_pick_ticket_number')} "
                          f"for prod order {fields.get('prod_order_number')}: "
                          f"status {fields.get('row_status_flag')}")


def main() -> None:
    """Entry point: print the runbook checklist; on --execute run Stage 3."""
    parser = argparse.ArgumentParser(
        description="Production order runbook (docs/recipes/production-order-runbook.md)")
    parser.add_argument("--execute", action="store_true",
                        help="Run Stage 3 (m_picktickets) -- CREATES the pick-ticket "
                             "record in P21 (default: dry run)")
    args = parser.parse_args()

    print("Recipe - Production Order Runbook (Create to Invoice)")
    print("=" * 60)
    print()
    print(CHECKLIST)

    if not args.execute:
        print("DRY RUN - Stage 3 payload that would be POSTed to "
              "{ui_server}/api/v2/process/pdfreport:")
        print(json.dumps(build_report_payload(), indent=2))
        print("\nRe-run with --execute to generate the pick ticket and read its status back.")
        return

    config = load_config()
    token_data = get_token(config)
    headers = get_auth_headers(token_data["AccessToken"])
    ui_server = get_ui_server_url(config.base_url, token_data["AccessToken"], config.verify_ssl)
    print(f"UI Server: {ui_server}")

    # --- Stage 3, part 1: generate the pick ticket (record + PDF) ---
    file_name = generate_pick_ticket(ui_server, headers, config.verify_ssl)

    # --- Stage 3, part 2: read the new ticket back (number from the FileName) ---
    match = re.match(r"PPT(\d+)", file_name)
    if not match:
        raise SystemExit(f"Could not extract ticket number from '{file_name}'")
    read_ticket_status(ui_server, headers, config.verify_ssl, match.group(1))


if __name__ == "__main__":
    main()
