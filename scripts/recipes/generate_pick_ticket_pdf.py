"""
Generate a Pick Ticket PDF (m_picktickets via /api/v2/process/pdfreport)

Generate a production-order pick ticket as a base64-encoded PDF via the
dedicated report endpoint. m_picktickets CREATES the pick-ticket record at
location_id AND returns its PDF in one call -- which is why this script is
gated behind --execute. Never post an m_* report to /api/v2/transaction: it
returns Succeeded and emits nothing.

Prerequisite: the production order's form must already be printed
(prod_order_hdr.printed = 'Y') -- run a ProductionOrder transaction with
print_form = ON first.

Mirrors: docs/recipes/generate-pick-ticket-pdf.md

Usage:
    python scripts/recipes/generate_pick_ticket_pdf.py            # dry run (default)
    python scripts/recipes/generate_pick_ticket_pdf.py --execute  # run report, save PDF
"""

import argparse
import base64
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
PROD_ORDER = "1000123"  # production order number
LOCATION_ID = "10"      # location whose inventory the components pick from


def build_report_payload() -> dict:
    """Build the m_picktickets report payload.

    Reports use numeric Status/Type 0 and Keys: [] -- not the "New"
    record-edit shape. m_picktickets requires UseCodeValues: true with the
    code "P" (Production Order); False returns HTTP 500.

    Returns:
        dict: Complete pdfreport payload.
    """
    return {
        "Name": "m_picktickets",
        "UseCodeValues": True,   # required here -- False returns HTTP 500
        "Transactions": [{
            "Status": 0,         # numeric 0 for report payloads
            "DataElements": [{
                "Keys": [],      # always empty for reports
                "Type": 0,       # numeric 0 for report payloads
                "Name": "TABPAGE_1.tp_1_dw_1",
                "Rows": [{"Edits": [
                    # code "P" = Production Order (the display label is rejected)
                    {"Name": "create_pick_ticket_type", "Value": "P"},
                    {"Name": "beg_prod_order", "Value": PROD_ORDER},
                    {"Name": "end_prod_order", "Value": PROD_ORDER},
                    {"Name": "location_id", "Value": LOCATION_ID},
                ]}],
            }],
        }],
    }


def run_report(ui_server: str, headers: dict, verify_ssl: bool, payload: dict) -> list[dict]:
    """POST the report payload and return the document array.

    Errors come back as the standard P21 error envelope
    (ErrorType/ErrorMessage), NOT the Summary/Messages format of /transaction.

    Args:
        ui_server: UI server URL.
        headers: Auth headers.
        verify_ssl: Whether to verify SSL certificates.
        payload: Report payload from build_report_payload().

    Returns:
        list[dict]: Documents (success is a JSON array, even for one document).

    Raises:
        SystemExit: On HTTP errors, error envelopes, or an empty result.
    """
    response = httpx.post(
        f"{ui_server}/api/v2/process/pdfreport",  # NOT /api/v2/transaction
        headers=headers, json=payload, verify=verify_ssl,
        follow_redirects=True, timeout=120,
    )
    if response.status_code >= 400:
        raise SystemExit(f"HTTP {response.status_code}: {response.text}")
    result = response.json()
    if isinstance(result, dict) and "ErrorMessage" in result:
        raise SystemExit(f"{result.get('ErrorType')}: {result['ErrorMessage']}")
    if not (isinstance(result, list) and result):
        raise SystemExit(f"No documents returned: {result}")
    return result


def save_documents(documents: list[dict]) -> None:
    """Decode and save each returned document, verifying it is a PDF.

    Args:
        documents: Document array from run_report().
    """
    for doc in documents:
        status = doc.get("ResponseStatus", {}).get("StatusCode")
        if status != "Success" or not doc.get("DocumentData"):
            msg = doc.get("ResponseStatus", {}).get("Message", "Unknown error")
            print(f"Document failed: {msg}")
            continue
        pdf_bytes = base64.b64decode(doc["DocumentData"])
        # FileName includes .pdf, e.g. "PPT<nnn> PRODUCTION_PICK_TICKET.pdf"
        filename = doc.get("FileName", "pick_ticket.pdf")
        with open(filename, "wb") as f:
            f.write(pdf_bytes)
        # Verify: decoded bytes must start with %PDF
        is_pdf = pdf_bytes.startswith(b"%PDF")
        print(f"Saved {filename} ({len(pdf_bytes)} bytes) "
              f"{'-- verified %PDF header' if is_pdf else '-- WARNING: not a PDF'}")


def main() -> None:
    """Entry point: build payload; on --execute run the report and save the PDF."""
    parser = argparse.ArgumentParser(
        description="Generate a pick-ticket PDF (docs/recipes/generate-pick-ticket-pdf.md)")
    parser.add_argument("--execute", action="store_true",
                        help="Actually run the report -- this CREATES the pick-ticket "
                             "record in P21 (default: dry run)")
    args = parser.parse_args()

    print("Recipe - Generate Pick Ticket PDF (m_picktickets)")
    print("=" * 60)

    payload = build_report_payload()

    if not args.execute:
        print("\nDRY RUN - payload that would be POSTed to "
              "{ui_server}/api/v2/process/pdfreport")
        print("(side effect at execute time: the pick-ticket record is CREATED at "
              f"location {LOCATION_ID}):")
        print(json.dumps(payload, indent=2))
        print("\nRe-run with --execute to run the report.")
        return

    config = load_config()
    token_data = get_token(config)
    headers = get_auth_headers(token_data["AccessToken"])
    ui_server = get_ui_server_url(config.base_url, token_data["AccessToken"], config.verify_ssl)
    print(f"UI Server: {ui_server}")

    documents = run_report(ui_server, headers, config.verify_ssl, payload)
    save_documents(documents)
    print("\nTo prove the pick-ticket row landed, reprint it with "
          "m_reprintpicktickets using the ticket number from the FileName "
          "(beg_prod_pick_ticket_no / end_prod_pick_ticket_no).")


if __name__ == "__main__":
    main()
