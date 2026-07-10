"""
Create a Sales Order (Order service)

Create a sales order -- header plus line items -- in one stateless
Transaction API call, extract the generated order_no from the result rows,
and read the order back via OData. No assembly lines: the Transaction API
auto-answers the "add as assembly?" prompt No, killing the explode -- use
order_with_assembly.py for those.

Mirrors: docs/recipes/create-sales-order.md

Usage:
    python scripts/recipes/create_sales_order.py            # dry run (default)
    python scripts/recipes/create_sales_order.py --execute  # POST + verify
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
CUSTOMER_ID = "100198"
SALES_LOC_ID = "10"
SOURCE_LOC_ID = "10"       # effectively required -- omitting it fails on tax jurisdiction
ORDER_DATE = "2030-01-05"
REQUESTED_DATE = "2030-01-06"  # must be AFTER order_date
PO_NO = "PO-TEST-001"
TAKER = "JSMITH"
SHIP_TO_ID = "200"
CONTACT_ID = "300"

# (item_id, quantity) -- items must be stocked at the source location
ORDER_LINES = [
    ("WIDGET-001", "5"),
    ("WIDGET-002", "2"),
]


def build_order_payload() -> dict:
    """Build the Order payload: header form + items list.

    Do NOT send company_id -- it is a disabled column on the Order window.

    Returns:
        dict: Complete Transaction API payload.
    """
    item_rows = [
        {"Edits": [
            {"Name": "oe_order_item_id", "Value": item_id},
            {"Name": "unit_quantity",    "Value": qty},
        ], "RelativeDateEdits": []}
        for item_id, qty in ORDER_LINES
    ]
    return {
        "Name": "Order",
        "UseCodeValues": False,
        "Transactions": [{
            "Status": "New",
            "DataElements": [
                {
                    "Name": "TABPAGE_1.order",
                    "Type": "Form",
                    "Keys": [],
                    "Rows": [{
                        "Edits": [
                            {"Name": "customer_id",    "Value": CUSTOMER_ID},
                            {"Name": "sales_loc_id",   "Value": SALES_LOC_ID},
                            {"Name": "source_loc_id",  "Value": SOURCE_LOC_ID},
                            {"Name": "order_date",     "Value": ORDER_DATE},
                            {"Name": "requested_date", "Value": REQUESTED_DATE},
                            {"Name": "po_no",          "Value": PO_NO},
                            {"Name": "taker",          "Value": TAKER},
                            {"Name": "ship_to_id",     "Value": SHIP_TO_ID},
                            {"Name": "contact_id",     "Value": CONTACT_ID},
                        ],
                        "RelativeDateEdits": [],
                    }],
                },
                {
                    "Name": "TP_ITEMS.items",
                    "Type": "List",
                    "Keys": [],
                    "Rows": item_rows,
                },
            ],
        }],
    }


def extract_order_no(result: dict) -> str | None:
    """Pull the generated order_no out of the TABPAGE_1.order result rows.

    Args:
        result: Parsed JSON response from POST /api/v2/transaction.

    Returns:
        str | None: The generated order number, if present.
    """
    order_no = None
    for txn in result["Results"]["Transactions"]:
        if txn.get("Status") != "Passed":
            continue
        for element in txn.get("DataElements", []):
            if element.get("Name") != "TABPAGE_1.order":
                continue
            for row in element.get("Rows", []):
                for edit in row.get("Edits", []):
                    if edit.get("Name") == "order_no":
                        order_no = edit.get("Value")
    return order_no


def main() -> None:
    """Entry point: build payload, POST on --execute, then verify via OData."""
    parser = argparse.ArgumentParser(
        description="Create a sales order (docs/recipes/create-sales-order.md)")
    parser.add_argument("--execute", action="store_true",
                        help="Actually POST the transaction (default: dry run)")
    args = parser.parse_args()

    print("Recipe - Create a Sales Order (Order service)")
    print("=" * 60)

    payload = build_order_payload()

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

    response = httpx.post(f"{ui_server}/api/v2/transaction",
                          headers=headers, json=payload, verify=config.verify_ssl,
                          follow_redirects=True, timeout=120)
    response.raise_for_status()
    result = response.json()

    # HTTP 200 even on failure -- check the Summary, never the status code
    summary = result["Summary"]
    print(f"Succeeded: {summary['Succeeded']}, Failed: {summary['Failed']}")
    if summary["Failed"] > 0 or summary["Succeeded"] == 0:
        for msg in result.get("Messages", []):
            print(f"  {msg}")
        raise SystemExit("Order create failed")

    order_no = extract_order_no(result)
    print(f"Created order_no: {order_no}")
    if not order_no:
        raise SystemExit("No order_no in the result rows")

    # --- Verify: read the order back. Succeeded is not proof every value
    # landed -- a DynaChange auto-answer can drop a line silently. ---
    print("\nVerify (OData read-back):")
    hdr_resp = httpx.get(
        f"{config.base_url}/odataservice/odata/table/oe_hdr",
        params={"$filter": f"order_no eq '{order_no}'"},
        headers=headers, verify=config.verify_ssl, follow_redirects=True,
    )
    hdr_resp.raise_for_status()
    for hdr in hdr_resp.json()["value"]:
        print(f"  Header: taker={hdr.get('taker')} po_no={hdr.get('po_no')} "
              f"ship2={hdr.get('ship2_name') or hdr.get('address_id')}")

    line_resp = httpx.get(
        f"{config.base_url}/odataservice/odata/table/oe_line",
        params={"$filter": f"order_no eq '{order_no}'"},
        headers=headers, verify=config.verify_ssl, follow_redirects=True,
    )
    line_resp.raise_for_status()
    lines = line_resp.json()["value"]
    print(f"  Lines on order: {len(lines)} (expected {len(ORDER_LINES)})")
    for line in lines:
        print(f"    line {line.get('line_no')}: qty_ordered={line.get('qty_ordered')}")
    if len(lines) != len(ORDER_LINES):
        print("  WARNING: line count mismatch -- a DynaChange auto-answer may have "
              "dropped a line while the transaction still reported Succeeded")


if __name__ == "__main__":
    main()
