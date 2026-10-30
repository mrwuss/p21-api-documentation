"""
Enter a Sales Order with quote = OFF, Optionally as a Direct Ship (Interactive API)

The Order window can open in quote mode (quote = ON). Everything saved that
way is a quote (oe_hdr.projected_order = 'Y'): it never allocates, and the
PO wizard builds an RFQ instead of a PO. This script reads the window's
quote default, sets quote = OFF as the first header edit, enters one line,
saves, and reads projected_order back.

With --direct-ship the line is entered with disposition D and a po_cost,
the header gets c_create_po = ON, and the save opens the "Create
RFQ/Purchase Orders" wizard (w_create_po_from_oe_wzd); the script presses
cb_next (the PO is committed here) and cb_finish, then reads back the
po_type = 'D' PO and its oe_line_po link. Feed that PO number to
direct_ship_confirmation.py.

Key rules (verified on play 26.1.5950.0, October 2026):
    - Read quote before you write anything; set it OFF first.
    - c_create_po needs a user with a Buyer ID ("To create a PO, you must
      have a valid Buyer ID." otherwise). --consumer-key authenticates as
      P21_CONSUMER_KEY / P21_CONSUMER_USERNAME instead of the password user.
    - The wizard did not open for a line whose supplier was an internal
      (intercompany) supplier; the same flow with an outside supplier did.
    - w_message prompts on save ("no PO cost specified", "profit above the
      acceptable limit") are answered Yes (cb_1). Any other popup stops the
      script -- never blind-answer a window you have not identified.
    - The new oe_line_uid arrives on the item change's keygenerated event;
      the script reads the order back from it.

Mirrors: docs/04-Interactive-API.md#set-quote-to-off-first-the-window-can-open-in-quote-mode

Usage:
    python examples/python/recipes/order_entry_quote_off.py                 # dry run: call plan
    python examples/python/recipes/order_entry_quote_off.py --execute \\
        --customer-id 100 --ship-to-id 100 --contact-id 300 --item-id ITEM-001
    python examples/python/recipes/order_entry_quote_off.py --execute --direct-ship \\
        --consumer-key --po-cost 8 ...
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from common.auth import get_token, get_auth_headers, get_ui_server_url
from common.config import load_config
from common.interactive_session import (
    BLOCKED,
    InteractiveSession,
    event_value,
    popup_ids,
)

import warnings

warnings.filterwarnings("ignore")

CALL_PLAN = """\
Planned Interactive API calls (nothing sent):
  POST sessions/ {{"ResponseWindowHandlingEnabled": true}}
  POST v2/window {{"ServiceName": "Order"}}
  GET  v2/data   -> read TABPAGE_1.order.quote (the default)
  PUT  v2/change TABPAGE_1/order: quote=OFF   <- first header edit
  PUT  v2/change TABPAGE_1/order: sales_loc_id={loc}, source_loc_id={loc},
                 customer_id={cust}, ship_to_id={ship}, contact_id={contact}, po_no={po}
  PUT  v2/tab    TP_ITEMS
  PUT  v2/change TP_ITEMS/items: oe_order_item_id={item} (keygenerated -> oe_line_uid),
                 unit_quantity={qty}{ds}
  PUT  v2/data   save; w_message prompts -> cb_1{wiz}
  OData: oe_line (oe_line_uid) -> oe_hdr.projected_order must be 'N'{ds_verify}
"""


def answer_popups(s: InteractiveSession, result: dict) -> str | None:
    """Answer what the save opened. Returns the PO number when the wizard ran.

    Args:
        s: Open session.
        result: The blocked save result.

    Returns:
        str | None: po_no from the wizard's second page, if the wizard ran.
    """
    po_no = None
    while result.get("Status") == BLOCKED:
        popup = popup_ids(result)[0]
        tools = s.tools(popup)  # includes the parent's ribbon -- search by name
        if "cb_finish" in tools:  # the Create RFQ/Purchase Orders wizard
            for row in s.rows(popup, "items"):
                print(
                    f"  wizard line: item={row.get('item_id')} disposition={row.get('disposition')} "
                    f"supplier={row.get('supplier_id')} quote_item={row.get('quote_item')} "
                    f"qty={row.get('qty_to_purchase')}"
                )
            s.run_tool(popup, "cb_next")  # the PO is COMMITTED here
            page2 = s.active_row(popup, "po_print")
            po_no = page2.get("po_no")
            print(f"  wizard page 2: po_no={po_no} po_type={page2.get('po_type')}")
            result = s.run_tool(popup, "cb_finish")
        elif s.window_name(popup) == "w_message" and "cb_1" in tools:
            print("  w_message -> cb_1 (Yes)")
            result = s.run_tool(popup, "cb_1")
        else:
            raise RuntimeError(f"Unexpected popup {s.window_name(popup)}: {tools}")
    return po_no


def odata(http: httpx.Client, base_url: str, table: str, flt: str) -> list[dict]:
    """Return the rows of an OData table query."""
    r = http.get(
        f"{base_url}/odataservice/odata/table/{table}", params={"$filter": flt}
    )
    r.raise_for_status()
    return r.json()["value"]


def main() -> None:
    """Entry point: print the call plan, or enter the order and verify it."""
    p = argparse.ArgumentParser(
        description="Order entry with quote OFF (Interactive API)"
    )
    p.add_argument(
        "--execute", action="store_true", help="Run the session (default: dry run)"
    )
    p.add_argument(
        "--direct-ship",
        action="store_true",
        help="Enter the line as disposition D and create its PO through the wizard",
    )
    p.add_argument(
        "--consumer-key",
        action="store_true",
        help="Authenticate with P21_CONSUMER_KEY/P21_CONSUMER_USERNAME (a Buyer ID user)",
    )
    p.add_argument("--location-id", default="10", help="sales_loc_id and source_loc_id")
    p.add_argument("--customer-id", default="100")
    p.add_argument("--ship-to-id", default="100")
    p.add_argument("--contact-id", default="300")
    p.add_argument("--po-no", default="PO-TEST-001", help="Customer PO number")
    p.add_argument("--item-id", default="ITEM-001")
    p.add_argument("--quantity", default="1")
    p.add_argument("--po-cost", default="8", help="Line po_cost (direct ship only)")
    args = p.parse_args()

    print("Order entry with quote = OFF (Interactive API)")
    print("=" * 60)
    if not args.execute:
        print(
            CALL_PLAN.format(
                loc=args.location_id,
                cust=args.customer_id,
                ship=args.ship_to_id,
                contact=args.contact_id,
                po=args.po_no,
                item=args.item_id,
                qty=args.quantity,
                ds=(
                    f",\n                 disposition=D, po_cost={args.po_cost};"
                    "\n  PUT  v2/change TABPAGE_1/order: c_create_po=ON"
                )
                if args.direct_ship
                else "",
                wiz="; wizard (cb_finish present) -> cb_next, cb_finish"
                if args.direct_ship
                else "",
                ds_verify="\n         oe_line_po -> po_hdr.po_type must be 'D'"
                if args.direct_ship
                else "",
            )
        )
        print("Re-run with --execute to enter the order.")
        return

    config = load_config()
    if args.consumer_key:
        token = get_token(
            config, consumer_key=config.consumer_key, username=config.consumer_username
        )["AccessToken"]
    else:
        token = get_token(config)["AccessToken"]
    headers = get_auth_headers(token)
    ui_server = get_ui_server_url(config.base_url, token, config.verify_ssl)

    s = InteractiveSession(ui_server, headers, config.verify_ssl)
    s.start(response_windows=True)
    window = s.open_window("Order")
    oe_line_uid = None
    try:
        print(f"\nquote default on open: {s.active_row(window, 'order').get('quote')}")
        s.change(window, "TABPAGE_1", "order", "quote", "OFF")  # first header edit
        print(f"quote after OFF:       {s.active_row(window, 'order').get('quote')}")
        for field, value in [
            ("sales_loc_id", args.location_id),
            ("source_loc_id", args.location_id),
            ("customer_id", args.customer_id),
            ("ship_to_id", args.ship_to_id),
            ("contact_id", args.contact_id),
            ("po_no", args.po_no),
        ]:
            s.change(window, "TABPAGE_1", "order", field, value)

        s.select_tab(window, "TP_ITEMS")
        result = s.change(window, "TP_ITEMS", "items", "oe_order_item_id", args.item_id)
        oe_line_uid = event_value(result, "keygenerated", "value")
        s.change(window, "TP_ITEMS", "items", "unit_quantity", args.quantity)
        if args.direct_ship:
            s.change(
                window, "TP_ITEMS", "items", "disposition", "D"
            )  # at entry, or later once the line holds no allocation
            s.change(window, "TP_ITEMS", "items", "po_cost", args.po_cost)
            s.select_tab(window, "TABPAGE_1")
            s.change(window, "TABPAGE_1", "order", "c_create_po", "ON")

        answer_popups(s, s.save(window))
    finally:
        s.close_window(window)
        s.end()

    if not oe_line_uid:
        raise SystemExit("No oe_line_uid came back from the item change")
    with httpx.Client(
        headers=headers, verify=config.verify_ssl, follow_redirects=True, timeout=60
    ) as http:
        line = odata(http, config.base_url, "oe_line", f"oe_line_uid eq {oe_line_uid}")[
            0
        ]
        order_no = line["order_no"]
        hdr = odata(http, config.base_url, "oe_hdr", f"order_no eq '{order_no}'")[0]
        print(
            f"\nVerify: order {order_no} projected_order={hdr['projected_order']} -> "
            f"{'OK (order)' if hdr['projected_order'] == 'N' else 'QUOTE'}"
        )
        print(
            f"  line {line['line_no']}: disposition={line['disposition']!r} "
            f"qty_ordered={line['qty_ordered']}"
        )
        if args.direct_ship:
            links = odata(
                http, config.base_url, "oe_line_po", f"order_number eq '{order_no}'"
            )
            for link in links:
                po = odata(
                    http, config.base_url, "po_hdr", f"po_no eq {link['po_no']}"
                )[0]
                print(
                    f"  oe_line_po: po_no={link['po_no']} connection_type={link['connection_type']} "
                    f"po_type={po['po_type']} -> {'OK' if po['po_type'] == 'D' else 'CHECK'}"
                )
            if not links:
                print(
                    "  no oe_line_po row -> no PO was created (check Buyer ID and supplier)"
                )


if __name__ == "__main__":
    main()
