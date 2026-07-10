"""
Update Contract Lines (JobContractPricing)

Update prices on existing JobContractPricing lines, insert new lines onto an
existing contract (upsert), and set commission costs -- all through the
stateless Transaction API. One POST per line (inserts re-save the shared
header and collide when batched), then an OData read-back of every price.

Mirrors: docs/recipes/update-contract-lines.md

Usage:
    python scripts/recipes/update_contract_lines.py            # dry run (default)
    python scripts/recipes/update_contract_lines.py --execute  # POST + verify
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
CONTRACT = {
    "company_id": "ACME",
    "contract_no": "A120-12",
    "job_no": "31",            # unique across renewals -- include it
    "end_date": "2030-01-01",  # required on EVERY submit, must be >= today
}

# (item_id, uom, price, commission_cost or None)
LINES = [
    ("WIDGET-001", "EA", 36.58, 17.19),  # already on contract -> updated
    ("WIDGET-002", "EA", 12.40, None),   # not on contract     -> inserted (upsert)
]


def line_payload(contract: dict, item_id: str, uom: str, price: float,
                 commission_cost: float | None = None) -> dict:
    """Build a one-line upsert payload, optionally with a commission cost.

    Args:
        contract: Header key fields (company_id, contract_no, job_no, end_date).
        item_id: Item on the contract line (the JOBPRICELINE upsert key).
        uom: Unit of measure for the line.
        price: Fixed price (pricing_method "Price").
        commission_cost: Optional commission cost value; requires
            IgnoreDisabled at the payload top level.

    Returns:
        dict: Complete Transaction API payload for one line.
    """
    elements = [
        {"Name": "FORM.d_dw_job_price_hdr", "Type": "Form", "Keys": [],
         "Rows": [{"Edits": [
             {"Name": "company_id",  "Value": contract["company_id"]},
             {"Name": "contract_no", "Value": contract["contract_no"]},
             {"Name": "job_no",      "Value": contract["job_no"]},
             {"Name": "end_date",    "Value": contract["end_date"]},
         ], "RelativeDateEdits": []}]},
        {"Name": "JOBPRICELINE.jobpriceline", "Type": "List", "Keys": ["item_id"],
         "Rows": [{"Edits": [
             {"Name": "item_id",        "Value": item_id},
             {"Name": "uom",            "Value": uom},
             {"Name": "pricing_method", "Value": "Price"},   # MUST come before price
             {"Name": "price",          "Value": str(price)},
         ], "RelativeDateEdits": []}]},
    ]
    payload = {"Name": "JobContractPricing", "UseCodeValues": False,
               "Transactions": [{"Status": "New", "DataElements": elements}]}
    if commission_cost is not None:
        payload["IgnoreDisabled"] = True  # top level, NOT inside the Transaction
        elements.append(
            {"Name": "JOBPRICECOST.jobpricecost", "Type": "Form", "Keys": ["item_id"],
             "Rows": [{"Edits": [
                 {"Name": "item_id",                 "Value": item_id},
                 {"Name": "commission_cost_type_cd", "Value": "Value"},  # type before value
                 {"Name": "commission_cost_value",   "Value": str(commission_cost)},
             ]}]})
    return payload


def post_line(ui_server: str, headers: dict, verify_ssl: bool, payload: dict) -> bool:
    """POST one transaction; True only if the Summary says it landed.

    Args:
        ui_server: UI server URL from get_ui_server_url().
        headers: Auth headers from get_auth_headers().
        verify_ssl: Whether to verify SSL certificates.
        payload: Transaction API payload from line_payload().

    Returns:
        bool: True when Summary.Succeeded > 0 and Summary.Failed == 0.
    """
    resp = httpx.post(f"{ui_server}/api/v2/transaction",
                      headers=headers, json=payload, verify=verify_ssl,
                      follow_redirects=True, timeout=60)
    resp.raise_for_status()  # HTTP 200 even when the transaction failed
    result = resp.json()
    summary = result["Summary"]
    if summary["Failed"] or not summary["Succeeded"]:
        for msg in result.get("Messages", []):
            print(f"  FAILED: {msg}")
        return False
    return True


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
    """Entry point: build payloads, POST on --execute, then verify via OData."""
    parser = argparse.ArgumentParser(
        description="Update/insert JobContractPricing lines (docs/recipes/update-contract-lines.md)")
    parser.add_argument("--execute", action="store_true",
                        help="Actually POST the transactions (default: dry run)")
    args = parser.parse_args()

    print("Recipe - Update Contract Lines (JobContractPricing)")
    print("=" * 60)

    payloads = [(item_id, line_payload(CONTRACT, item_id, uom, price, commission))
                for item_id, uom, price, commission in LINES]

    if not args.execute:
        print("\nDRY RUN - one POST per line to {ui_server}/api/v2/transaction:")
        for item_id, payload in payloads:
            print(f"\n--- {item_id} ---")
            print(json.dumps(payload, indent=2))
        print("\nRe-run with --execute to POST the transactions.")
        return

    config = load_config()
    token_data = get_token(config)
    headers = get_auth_headers(token_data["AccessToken"])
    ui_server = get_ui_server_url(config.base_url, token_data["AccessToken"], config.verify_ssl)
    print(f"UI Server: {ui_server}")

    # One POST per line: inserts re-save the shared header and collide when batched.
    for item_id, payload in payloads:
        ok = post_line(ui_server, headers, config.verify_ssl, payload)
        print(f"{item_id}: {'OK' if ok else 'failed'}")

    # --- Verify via OData (no joins: chain the uid columns) ---
    print("\nVerify (OData read-back):")
    # Renewals can return two headers for one contract_no -- match job_no too.
    hdr = odata(config.base_url, headers, config.verify_ssl,
                "job_price_hdr", f"contract_no eq '{CONTRACT['contract_no']}'")[0]
    for item_id, _uom, price, _commission in LINES:
        im_uid = odata(config.base_url, headers, config.verify_ssl,
                       "inv_mast", f"item_id eq '{item_id}'")[0]["inv_mast_uid"]
        line = odata(config.base_url, headers, config.verify_ssl,
                     "job_price_line",
                     f"job_price_hdr_uid eq {hdr['job_price_hdr_uid']} "
                     f"and inv_mast_uid eq {im_uid}")[0]
        match = "OK" if float(line["price"]) == price else "MISMATCH"
        print(f"  {item_id}: price={line['price']} expected={price} -> {match}")


if __name__ == "__main__":
    main()
