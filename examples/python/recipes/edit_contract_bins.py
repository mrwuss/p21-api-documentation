"""
Edit Contract Bin Quantities (JobContractPricing + IgnoreDisabled)

Change min_qty, max_qty, reorder_qty, and capacity on the bins of an existing
job contract via the Transaction API. The BINS sub-tab is normally disabled;
IgnoreDisabled: true at the payload TOP LEVEL unlocks it. Batching is fine
here (unlike line inserts) -- one POST covers every bin, then an OData
read-back confirms the quantities.

Mirrors: docs/recipes/edit-contract-bins.md

Usage:
    python examples/python/recipes/edit_contract_bins.py            # dry run (default)
    python examples/python/recipes/edit_contract_bins.py --execute  # POST + verify
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
CONTRACT_NO = "A120-12"   # used for the OData read-back
JOB_NO = "31"             # unique across renewals -- load the header by this
CUSTOMER_ID = "100198"
SHIP_TO_ID = "200"

# Per bin: the line's item_id, the bin id, and the new quantities.
BIN_EDITS = [
    {"item_id": "WIDGET-001", "bin_id": "A01-02",
     "min_qty": 30, "max_qty": 100, "reorder_qty": 40, "capacity": 100},
    {"item_id": "WIDGET-002", "bin_id": "A01-02",
     "min_qty": 5,  "max_qty": 50,  "reorder_qty": 10, "capacity": 50},
]


def build_bin_payload(job_no: str, customer_id: str, ship_to_id: str,
                      edits: list[dict]) -> dict:
    """Build one Transaction with a JOBPRICELINE + BINS.bins pair per bin.

    Args:
        job_no: Contract job number (unique across renewals).
        customer_id: Customer on the contract header.
        ship_to_id: Ship-to on the contract header.
        edits: One dict per bin with item_id, bin_id, and the new quantities.

    Returns:
        dict: Complete Transaction API payload (IgnoreDisabled at top level).
    """
    elements = [
        {"Name": "FORM.d_dw_job_price_hdr", "Type": "Form", "Keys": [],
         "Rows": [{"Edits": [
             {"Name": "job_no",      "Value": job_no},
             {"Name": "customer_id", "Value": customer_id},
             {"Name": "ship_to_id",  "Value": ship_to_id},
         ]}]},
    ]
    for e in edits:
        elements.append(
            {"Name": "JOBPRICELINE.jobpriceline", "Type": "List",
             "Keys": ["item_id"],   # select by item_id, NOT line_no
             "Rows": [{"Edits": [{"Name": "item_id", "Value": e["item_id"]}]}]})
        elements.append(
            {"Name": "BINS.bins", "Type": "List",
             "Keys": ["contract_bin_id", "customer_id", "ship_to_id"],
             "Rows": [{"Edits": [
                 {"Name": "contract_bin_id", "Value": e["bin_id"]},
                 {"Name": "customer_id",     "Value": customer_id},
                 {"Name": "ship_to_id",      "Value": ship_to_id},
                 {"Name": "min_qty",         "Value": str(e["min_qty"])},
                 {"Name": "max_qty",         "Value": str(e["max_qty"])},
                 {"Name": "reorder_qty",     "Value": str(e["reorder_qty"])},
                 {"Name": "capacity",        "Value": str(e["capacity"])},
             ]}]})
    return {"Name": "JobContractPricing", "UseCodeValues": False,
            "IgnoreDisabled": True,  # top level -- mandatory for the BINS sub-tab
            "Transactions": [{"Status": "New", "DataElements": elements}]}


def odata(base_url: str, headers: dict, verify_ssl: bool,
          table: str, filter_expr: str) -> list[dict]:
    """Query an OData table and return its value rows.

    Args:
        base_url: P21 base URL.
        headers: Auth headers.
        verify_ssl: Whether to verify SSL certificates.
        table: OData table name.
        filter_expr: OData $filter expression.

    Returns:
        list[dict]: Matching rows.
    """
    resp = httpx.get(f"{base_url}/odataservice/odata/table/{table}",
                     params={"$filter": filter_expr},
                     headers=headers, verify=verify_ssl, follow_redirects=True)
    resp.raise_for_status()
    return resp.json()["value"]


def main() -> None:
    """Entry point: build payload, POST on --execute, then verify via OData."""
    parser = argparse.ArgumentParser(
        description="Edit contract bin quantities (docs/recipes/edit-contract-bins.md)")
    parser.add_argument("--execute", action="store_true",
                        help="Actually POST the transaction (default: dry run)")
    args = parser.parse_args()

    print("Recipe - Edit Contract Bin Quantities (JobContractPricing)")
    print("=" * 60)

    payload = build_bin_payload(JOB_NO, CUSTOMER_ID, SHIP_TO_ID, BIN_EDITS)

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
                      follow_redirects=True, timeout=60)
    resp.raise_for_status()  # HTTP 200 even when the transaction failed
    result = resp.json()
    summary = result["Summary"]
    print(f"Succeeded: {summary['Succeeded']}, Failed: {summary['Failed']}")
    if summary["Failed"] or not summary["Succeeded"]:
        for msg in result.get("Messages", []):
            print(f"  FAILED: {msg}")
        raise SystemExit(1)

    # --- Verify via OData (no joins: chain the uid columns) ---
    print("\nVerify (OData read-back):")
    hdr = odata(config.base_url, headers, config.verify_ssl,
                "job_price_hdr", f"contract_no eq '{CONTRACT_NO}'")[0]
    for e in BIN_EDITS:
        im_uid = odata(config.base_url, headers, config.verify_ssl,
                       "inv_mast", f"item_id eq '{e['item_id']}'")[0]["inv_mast_uid"]
        line = odata(config.base_url, headers, config.verify_ssl,
                     "job_price_line",
                     f"job_price_hdr_uid eq {hdr['job_price_hdr_uid']} "
                     f"and inv_mast_uid eq {im_uid}")[0]
        for bin_row in odata(config.base_url, headers, config.verify_ssl,
                             "job_price_bin",
                             f"job_price_line_uid eq {line['job_price_line_uid']}"):
            print(f"  {e['item_id']}: min={bin_row['min_qty']} max={bin_row['max_qty']} "
                  f"reorder={bin_row['reorder_qty']} "
                  f"(expected {e['min_qty']}/{e['max_qty']}/{e['reorder_qty']})")


if __name__ == "__main__":
    main()
