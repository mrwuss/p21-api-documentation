"""
Sales Order -> Pick Ticket -> Invoice Runbook

Runs docs/recipes/sales-order-to-invoice.md step by step, reading each step
back before the next one starts:

  1. Create the order          Transaction Order (quote OFF, plain stock lines)
  2. Print the pick ticket     Transaction Order, TP_FRONTCOUNTER.print_tix = ON
  3. Confirm the shipment      Interactive Shipping -- the save ships AND invoices
  Verify                       invoice_hdr/invoice_line, oe_line.qty_invoiced,
                               inv_loc.qty_on_hand relieved at the source location

For lines that must answer a prompt (an assembly that explodes), enter the
order with order_with_assembly.py instead and start this runbook at step 2.

Mirrors: docs/recipes/sales-order-to-invoice.md

Usage:
    python examples/python/recipes/sales_order_to_invoice.py            # dry run
    python examples/python/recipes/sales_order_to_invoice.py --execute  # run + verify
"""

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from runbook_common import (P21Runbook, build_order_payload, build_print_tix_payload, check,
                            print_invoice, print_pick_ticket, result_value, ship_and_invoice, show)

import warnings
warnings.filterwarnings("ignore")

# --- Configuration (generic placeholders -- substitute your own) ------------
CUSTOMER_ID = "CUST-100"
SHIP_TO_ID = "CUST-100"
CONTACT_ID = "300"
LOCATION_ID = "10"            # sales and source (ship-from) location
TAKER = "JSMITH"
ITEM_ID = "ITEM-001"          # stocked at LOCATION_ID, with a packaging code
QTY = "2"
PRICE = "12.00"               # pass --price "" to leave unit_price to pricing / a contract
PO_NO = "RUNBOOK-001"         # the customer PO number -- tags the order

TODAY = date.today()


def build_payload(args: argparse.Namespace) -> dict:
    """Step 1 payload: header + one line; requested_date after order_date."""
    return build_order_payload(
        args.customer, args.ship_to, args.contact, args.location, args.location,
        TODAY.isoformat(), (TODAY + timedelta(days=1)).isoformat(), args.po_no, args.taker,
        [(args.item, args.qty, args.price or None)])


def on_hand(rb: P21Runbook, item_uid: int, location: str) -> float:
    """inv_loc.qty_on_hand for one item at one location."""
    row = rb.one("inv_loc", f"inv_mast_uid eq {item_uid} and location_id eq {location}",
                 "qty_on_hand")
    return float(row["qty_on_hand"])


def main() -> None:
    """Entry point: dry run prints the payloads; --execute runs and verifies each step."""
    parser = argparse.ArgumentParser(
        description="Sales order to invoice runbook (docs/recipes/sales-order-to-invoice.md)")
    parser.add_argument("--customer", default=CUSTOMER_ID)
    parser.add_argument("--ship-to", default=SHIP_TO_ID)
    parser.add_argument("--contact", default=CONTACT_ID)
    parser.add_argument("--location", default=LOCATION_ID)
    parser.add_argument("--taker", default=TAKER)
    parser.add_argument("--item", default=ITEM_ID)
    parser.add_argument("--qty", default=QTY)
    parser.add_argument("--price", default=PRICE)
    parser.add_argument("--po-no", default=PO_NO)
    parser.add_argument("--execute", action="store_true",
                        help="Actually run the steps (default: dry run)")
    args = parser.parse_args()

    print("Runbook - Sales Order -> Pick Ticket -> Invoice")
    print("=" * 60)
    if not args.execute:
        show("Step 1 Order payload", build_payload(args))
        show("Step 2 print_tix payload (order_no from step 1)", build_print_tix_payload("{order_no}"))
        print("\nStep 3 (Interactive Shipping): open Shipping, set TABPAGE_1.tp_1_dw_1."
              "pick_ticket_no, save -- answer proceed prompts cb_1/cb_ok/cb_yes, never cb_cancel.")
        print("\nRe-run with --execute to run it.")
        return

    rb = P21Runbook()
    item_uid = rb.item_uid(args.item)
    before = on_hand(rb, item_uid, args.location)

    print("\nStep 1 - Create the order (Transaction Order)")
    result = rb.transaction(build_payload(args), "Order")
    order_no = result_value(result, "TABPAGE_1.order", "order_no")
    hdr = rb.one("oe_hdr", f"order_no eq '{order_no}'", "order_no,projected_order,packing_basis")
    print(f"    order_no = {order_no}, packing_basis = {hdr['packing_basis']}")
    check("oe_hdr.projected_order (N = a real order, not a quote)", hdr["projected_order"], "N")
    for line in rb.odata("oe_line", f"order_no eq '{order_no}'",
                         "line_no,qty_ordered,qty_allocated,unit_price,supplier_id,"
                         "job_price_hdr_uid,other_cost,assembly"):
        print(f"    line {line['line_no']}: qty {line['qty_ordered']} allocated "
              f"{line['qty_allocated']} price {line['unit_price']} supplier {line['supplier_id']} "
              f"contract {line['job_price_hdr_uid']} other_cost {line['other_cost']}")
        check(f"line {line['line_no']} qty_allocated", float(line["qty_allocated"]),
              float(line["qty_ordered"]))
    if hdr["packing_basis"] == "Hold":
        raise SystemExit("The order is on Hold -- release it before printing the pick ticket")

    print("\nStep 2 - Print the pick ticket (Transaction Order, print_tix)")
    pick_ticket_no = print_pick_ticket(rb, order_no)

    print("\nStep 3 - Confirm the shipment and invoice (Interactive Shipping)")
    invoice_no = ship_and_invoice(rb, pick_ticket_no)

    print("\nVerify")
    print_invoice(rb, invoice_no)
    for line in rb.odata("oe_line", f"order_no eq '{order_no}'", "line_no,qty_ordered,qty_invoiced"):
        check(f"oe_line {line['line_no']} qty_invoiced", float(line["qty_invoiced"]),
              float(line["qty_ordered"]))
    check(f"inv_loc.qty_on_hand at {args.location}", on_hand(rb, item_uid, args.location),
          before - float(args.qty))
    print("\nRunbook complete.")


if __name__ == "__main__":
    main()
