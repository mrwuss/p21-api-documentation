"""
Create a Requisition Purchase Order (RequisitionPurchaseOrder service)

Create a requisition PO -- P21's internal / not-for-resale purchasing type --
in one stateless Transaction API call, extract the generated po_no from the
result rows, and read it back via OData confirming po_hdr.po_type == 'R'.

The PO type is chosen by the SERVICE, not by a field: po_hdr_po_type is a
disabled column on the standard PurchaseOrder service. RequisitionPurchaseOrder
is the type-specific service for requisition POs.

Mirrors: docs/recipes/create-requisition-po.md

Usage:
    python examples/python/recipes/create_requisition_po.py            # dry run (default)
    python examples/python/recipes/create_requisition_po.py --execute  # POST + verify
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
LOCATION_ID = "10"
VENDOR_ID = "99001"            # vendor_id != supplier_id -- different records
VENDOR_SUPPLIER_ID = "10050"   # goes on the HEADER (omitting it fails at the line)

# (item_id, quantity) -- item must have inv_loc.requisition = 'Y' at LOCATION_ID
PO_LINES = [
    ("WIDGET-001", "10"),
]


def build_requisition_po_payload() -> dict:
    """Build the RequisitionPurchaseOrder payload: header form + line grid.

    po_no is auto-assigned. Do NOT send po_hdr_po_type -- it is disabled;
    the service preselects the Requisition type.

    Returns:
        dict: Complete Transaction API payload.
    """
    line_rows = [
        {"Edits": [
            {"Name": "item_id",       "Value": item_id},
            {"Name": "unit_quantity", "Value": qty},
        ], "RelativeDateEdits": []}
        for item_id, qty in PO_LINES
    ]
    return {
        "Name": "RequisitionPurchaseOrder",
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
                            {"Name": "location_id",        "Value": LOCATION_ID},
                            {"Name": "vendor_id",          "Value": VENDOR_ID},
                            {"Name": "vendor_supplier_id", "Value": VENDOR_SUPPLIER_ID},
                        ],
                        "RelativeDateEdits": [],
                    }],
                },
                {
                    "Name": "TABPAGE_17.tp_17_dw_17",
                    "Type": "List",
                    "Keys": [],
                    "Rows": line_rows,
                },
            ],
        }],
    }


def extract_po_no(result: dict) -> str | None:
    """Pull the generated po_no out of the TABPAGE_1.tp_1_dw_1 result rows.

    Args:
        result: Parsed JSON response from POST /api/v2/transaction.

    Returns:
        str | None: The generated PO number, if present.
    """
    po_no = None
    for txn in result["Results"]["Transactions"]:
        if txn.get("Status") != "Passed":
            continue
        for element in txn.get("DataElements", []):
            if element.get("Name") != "TABPAGE_1.tp_1_dw_1":
                continue
            for row in element.get("Rows", []):
                for edit in row.get("Edits", []):
                    if edit.get("Name") == "po_no":
                        po_no = edit.get("Value")
    return po_no


def main() -> None:
    """Entry point: build payload, POST on --execute, then verify via OData."""
    parser = argparse.ArgumentParser(
        description="Create a requisition PO (docs/recipes/create-requisition-po.md)")
    parser.add_argument("--execute", action="store_true",
                        help="Actually POST the transaction (default: dry run)")
    args = parser.parse_args()

    print("Recipe - Create a Requisition Purchase Order")
    print("=" * 60)

    payload = build_requisition_po_payload()

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

    # HTTP 200 even on failure -- check the Summary, never the status code.
    # A missing vendor_supplier_id fails at the line with a misleading
    # "A supplier ID must be entered ... Column: item_id" -- fix is on the header.
    summary = result["Summary"]
    print(f"Succeeded: {summary['Succeeded']}, Failed: {summary['Failed']}")
    if summary["Failed"] > 0 or summary["Succeeded"] == 0:
        for msg in result.get("Messages", []):
            print(f"  {msg}")
        raise SystemExit("Requisition PO create failed")

    po_no = extract_po_no(result)
    print(f"Created po_no: {po_no}")
    if not po_no:
        raise SystemExit("No po_no in the result rows")

    # --- Verify: read the PO back and confirm po_type == 'R' ---
    print("\nVerify (OData read-back):")
    hdr_resp = httpx.get(
        f"{config.base_url}/odataservice/odata/table/po_hdr",
        params={"$filter": f"po_no eq {po_no}",
                "$select": "po_no,po_type,vendor_id"},
        headers=headers, verify=config.verify_ssl, follow_redirects=True,
    )
    hdr_resp.raise_for_status()
    for hdr in hdr_resp.json()["value"]:
        po_type = hdr.get("po_type")
        flag = "OK" if po_type == "R" else "WARNING: expected R"
        print(f"  po_no={hdr.get('po_no')} po_type={po_type} [{flag}] "
              f"vendor_id={hdr.get('vendor_id')}")

    line_resp = httpx.get(
        f"{config.base_url}/odataservice/odata/table/po_line",
        params={"$filter": f"po_no eq {po_no}"},
        headers=headers, verify=config.verify_ssl, follow_redirects=True,
    )
    line_resp.raise_for_status()
    lines = line_resp.json()["value"]
    print(f"  Lines on PO: {len(lines)} (expected {len(PO_LINES)})")


if __name__ == "__main__":
    main()
