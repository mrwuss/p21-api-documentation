"""
Print or Reprint a Purchase Order PDF (m_reprintpurchaseorders)

Generate one PO as a base64-encoded PDF through POST /api/v2/process/pdfreport,
save it, and read the PO's print history back.

reprint_flag is not a "reprint please" switch: it must EQUAL the PO's own
po_hdr.printed -- "N" for a PO that was never printed, "Y" for one that was.
A mismatch returns an empty HTTP 500 on every attempt. So this script reads
printed over OData first, sends it, and re-reads it before any retry (another
user can print the PO in between). A first print ("N") marks the PO printed.

Mirrors: docs/03-Transaction-API.md § Example: Generate and Save a PO Reprint
         docs/recipes/generate-pick-ticket-pdf.md (m_reprintpurchaseorders)

Usage:
    python examples/python/recipes/reprint_purchase_order.py             # dry run (default)
    python examples/python/recipes/reprint_purchase_order.py --company-id ACME \\
        --po-no 500100 --execute                                          # generate + save
"""

import argparse
import base64
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from common.auth import get_token, get_auth_headers, get_ui_server_url
from common.config import load_config

import warnings
warnings.filterwarnings("ignore")

# --- Configuration (generic placeholders -- substitute your own) ------------
COMPANY_ID = "ACME"
PO_NO = "500100"             # single PO: beg_po_no == end_po_no
ATTEMPTS = 3                 # report-engine faults are usually transient
BACKOFF_SECONDS = 0.5        # x attempt number


def build_payload(company_id: str, po_no: str, reprint_flag: str) -> dict:
    """Build the m_reprintpurchaseorders report payload for one PO.

    Args:
        company_id: Company (criteria name company_id; po_hdr stores company_no).
        po_no: The PO number.
        reprint_flag: The PO's own po_hdr.printed value, "Y" or "N".

    Returns:
        dict: Report payload -- numeric Status/Type 0, Keys [].
    """
    return {
        "Name": "m_reprintpurchaseorders",
        "Transactions": [{
            "DataElements": [{
                "Keys": [],
                "Name": "TABPAGE_1.poreportcriteriadw",
                "Rows": [{"Edits": [
                    {"Name": "company_id", "Value": company_id},
                    {"Name": "beg_po_no", "Value": po_no},
                    {"Name": "end_po_no", "Value": po_no},
                    {"Name": "reprint_flag", "Value": reprint_flag},
                ]}],
                "Type": 0,
            }],
            "Status": 0,
        }],
        "UseCodeValues": False,
    }


def get_printed_flag(client: httpx.Client, base_url: str, po_no: str) -> str:
    """Read po_hdr.printed -- reprint_flag must equal it, or the report 500s.

    Args:
        client: Authenticated httpx client.
        base_url: P21 base URL.
        po_no: The PO number (numeric on OData -- no quotes).

    Returns:
        str: "Y" when the PO has been printed, otherwise "N".
    """
    r = client.get(f"{base_url}/odataservice/odata/table/po_hdr",
                   params={"$filter": f"po_no eq {po_no}", "$select": "po_no,printed"})
    r.raise_for_status()
    rows = r.json().get("value", [])
    if not rows:
        raise SystemExit(f"PO {po_no} not found -- check it before calling the report")
    return "Y" if rows[0].get("printed") == "Y" else "N"


def run_report(client: httpx.Client, ui_server: str, base_url: str, args: argparse.Namespace):
    """POST the report, re-reading printed and backing off between attempts.

    Args:
        client: Authenticated httpx client.
        ui_server: UI server URL.
        base_url: P21 base URL.
        args: Parsed command-line values.

    Returns:
        tuple[str, list | dict | None]: The reprint_flag of the last attempt and
        the parsed body -- a document array on success, an error envelope, or None.
    """
    body = None
    flag = "N"
    for attempt in range(1, ATTEMPTS + 1):
        flag = get_printed_flag(client, base_url, args.po_no)  # re-read before every try
        resp = client.post(f"{ui_server}/api/v2/process/pdfreport",
                           json=build_payload(args.company_id, args.po_no, flag))
        try:
            body = resp.json()
        except ValueError:
            body = None  # the empty-bodied 5xx
        # Classify the P21 error envelope BEFORE the status code -- it can ride a 200.
        if isinstance(body, dict) and body.get("ErrorMessage"):
            return flag, body
        if resp.status_code == 200 and isinstance(body, list):
            return flag, body
        print(f"  attempt {attempt} (reprint_flag={flag}): HTTP {resp.status_code}, "
              f"{len(resp.content)}-byte body")
        time.sleep(BACKOFF_SECONDS * attempt)
    return flag, body


def main() -> None:
    """Entry point: dry run, or generate the PDF, save it, and verify."""
    parser = argparse.ArgumentParser(
        description="Print or reprint a PO PDF (docs/03-Transaction-API.md#pdf-report-generation)")
    parser.add_argument("--company-id", default=COMPANY_ID)
    parser.add_argument("--po-no", default=PO_NO)
    parser.add_argument("--output-dir", default=".", help="where to save the PDF")
    parser.add_argument("--execute", action="store_true",
                        help="Actually generate the report (default: dry run)")
    args = parser.parse_args()

    print("Recipe - Print or Reprint a Purchase Order PDF (m_reprintpurchaseorders)")
    print("=" * 60)

    if not args.execute:
        print("\nDRY RUN - POST {ui_server}/api/v2/process/pdfreport "
              "(reprint_flag is read from po_hdr.printed at run time):")
        print(json.dumps(build_payload(args.company_id, args.po_no, "<po_hdr.printed>"), indent=2))
        print("\nRe-run with --execute to generate. A first print marks the PO printed.")
        return

    config = load_config()
    token = get_token(config)["AccessToken"]
    ui_server = get_ui_server_url(config.base_url, token, config.verify_ssl)

    with httpx.Client(headers=get_auth_headers(token), verify=config.verify_ssl,
                      timeout=180, follow_redirects=True) as client:
        flag, body = run_report(client, ui_server, config.base_url, args)
        print(f"reprint_flag sent: {flag} (po_hdr.printed)")

        if isinstance(body, dict) and body.get("ErrorMessage"):
            raise SystemExit(f"{body.get('ErrorType')}: {body['ErrorMessage']}")
        if not isinstance(body, list) or not body:
            raise SystemExit(f"No documents after {ATTEMPTS} attempts -- re-check the PO, "
                             "company_id and the PO's printed flag")

        # Success is per document: StatusCode "Success" AND non-empty DocumentData.
        saved = 0
        for doc in body:
            status = (doc.get("ResponseStatus") or {}).get("StatusCode")
            if status != "Success" or not doc.get("DocumentData"):
                print(f"  document failed: {(doc.get('ResponseStatus') or {}).get('Message')}")
                continue
            pdf = base64.b64decode(doc["DocumentData"])
            # FileName's number is a document number, not necessarily the PO number.
            path = Path(args.output_dir) / doc.get("FileName", f"PO_{args.po_no}.pdf")
            path.write_bytes(pdf)
            saved += 1
            print(f"  saved {path} ({path.stat().st_size} bytes, "
                  f"starts with %PDF: {pdf[:4] == b'%PDF'})")

        # Read-back: a successful print leaves the PO marked printed.
        after = get_printed_flag(client, config.base_url, args.po_no)
    print(f"po_hdr.printed after: {after}")
    print(f"Verify: {'OK' if saved and after == 'Y' else 'CHECK'} "
          f"({saved} document(s) saved)")


if __name__ == "__main__":
    main()
