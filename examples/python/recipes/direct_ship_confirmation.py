"""
Confirm a Direct Ship (Interactive API, DirectShipConfirmation window)

Confirms a direct-ship purchase order in full: open the
DirectShipConfirmation window, set the PO number, tick receive_all, save.
One save receives the PO, completes the PO line, and invoices the linked
sales-order line. The script then reads all three back.

Key rules (verified on play 26.1.5950.0, October 2026):
    - Fields live on TABPAGE_1.tp_1_dw_po (po_no, receive_all); checkboxes
      take ON / OFF.
    - shipment_date, period and year_for_period come pre-filled (today and
      the current period). shipment_date is written to po_line.supplier_ship_date
      on every line the confirmation touches -- capture it first if you
      confirm partials.
    - No popups on the verified run; any popup stops the script.
    - A one-POST Transaction API confirmation keyed by po_no also works on
      26.1.5950.0 (it returned an empty result on 26.1.5940.0); see the doc.
      This script shows the window path.

Mirrors: docs/04-Interactive-API.md#the-interactive-path-works

Usage:
    python examples/python/recipes/direct_ship_confirmation.py                    # dry run
    python examples/python/recipes/direct_ship_confirmation.py --execute --po-no 500100
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from common.auth import get_token, get_auth_headers, get_ui_server_url
from common.config import load_config
from common.interactive_session import BLOCKED, InteractiveSession, popup_ids

import warnings

warnings.filterwarnings("ignore")


def odata(http: httpx.Client, base_url: str, table: str, flt: str) -> list[dict]:
    """Return the rows of an OData table query."""
    r = http.get(
        f"{base_url}/odataservice/odata/table/{table}", params={"$filter": flt}
    )
    r.raise_for_status()
    return r.json()["value"]


def show_state(http: httpx.Client, base_url: str, po_no: str, label: str) -> list[dict]:
    """Print PO line, linked sales-order line and invoice state; return the links."""
    print(f"\n{label}:")
    for line in odata(http, base_url, "po_line", f"po_no eq {po_no}"):
        print(
            f"  po_line {line['line_no']}: complete={line['complete']} "
            f"qty_received={line['qty_received']}/{line['qty_ordered']} "
            f"supplier_ship_date={line.get('supplier_ship_date')}"
        )
    links = odata(http, base_url, "oe_line_po", f"po_no eq {po_no}")
    for link in links:
        order_no = link["order_number"]
        for ol in odata(
            http,
            base_url,
            "oe_line",
            f"order_no eq '{order_no}' and line_no eq {link['line_number']}",
        ):
            print(
                f"  oe_line {order_no}/{ol['line_no']}: qty_invoiced={ol['qty_invoiced']} "
                f"complete={ol['complete']}"
            )
        for inv in odata(http, base_url, "invoice_hdr", f"order_no eq '{order_no}'"):
            print(
                f"  invoice_hdr {inv['invoice_no']}: total_amount={inv['total_amount']}"
            )
    return links


def main() -> None:
    """Entry point: dry run prints the plan; --execute confirms and verifies."""
    p = argparse.ArgumentParser(
        description="Confirm a direct-ship PO (Interactive API)"
    )
    p.add_argument(
        "--execute", action="store_true", help="Run the session (default: dry run)"
    )
    p.add_argument(
        "--po-no",
        default="500100",
        help="An open po_type 'D' PO linked to a sales order",
    )
    args = p.parse_args()

    print("Direct Ship Confirmation (Interactive API)")
    print("=" * 60)
    if not args.execute:
        print(f"""
DRY RUN - planned calls (nothing sent):
  POST sessions/ {{"ResponseWindowHandlingEnabled": true}}
  POST v2/window {{"ServiceName": "DirectShipConfirmation"}}
  PUT  v2/change TABPAGE_1/tp_1_dw_po: po_no={args.po_no}
  PUT  v2/change TABPAGE_1/tp_1_dw_po: receive_all=ON
  PUT  v2/data   save
  OData: po_line.complete, oe_line.qty_invoiced, invoice_hdr for the linked order
Re-run with --execute to confirm the PO.""")
        return

    config = load_config()
    token = get_token(config)["AccessToken"]
    headers = get_auth_headers(token)
    ui_server = get_ui_server_url(config.base_url, token, config.verify_ssl)

    with httpx.Client(
        headers=headers, verify=config.verify_ssl, follow_redirects=True, timeout=60
    ) as http:
        po = odata(http, config.base_url, "po_hdr", f"po_no eq {args.po_no}")
        if not po or po[0]["po_type"] != "D":
            raise SystemExit(
                f"PO {args.po_no} not found or not a direct-ship (po_type D) PO"
            )
        if not show_state(http, config.base_url, args.po_no, "Before"):
            raise SystemExit("No oe_line_po link -- nothing to confirm against")

        s = InteractiveSession(ui_server, headers, config.verify_ssl)
        s.start(response_windows=True)
        window = s.open_window("DirectShipConfirmation")
        try:
            s.change(window, "TABPAGE_1", "tp_1_dw_po", "po_no", args.po_no)
            s.change(window, "TABPAGE_1", "tp_1_dw_po", "receive_all", "ON")
            pre = s.active_row(window, "tp_1_dw_1")
            print(
                f"\nPre-filled: shipment_date={pre.get('shipment_date')} "
                f"period={pre.get('period')} year_for_period={pre.get('year_for_period')}"
            )
            result = s.save(window)
            if result.get("Status") == BLOCKED:
                raise RuntimeError(
                    f"Save opened a popup: {s.tools(popup_ids(result)[0])}"
                )
            print("Saved.")
        finally:
            s.close_window(window)
            s.end()

        show_state(http, config.base_url, args.po_no, "After")


if __name__ == "__main__":
    main()
