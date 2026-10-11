"""
Dispose of Zero-Value Stock with a $0 Order (runbook)

Runs docs/recipes/dispose-zero-value-stock.md step by step, reading each step
back before the next one starts:

  1. Build the item list from live inv_loc rows at the token cost   (OData)
  2. Header + line 1, the rep the order must carry, on Hold         (Interactive Order)
  3. Append the remaining lines in ONE Transaction per order        (Transaction Order)
  4. Release the Hold (packing_basis = Partial)                      (Transaction Order)
  5. Pick ticket, then ship-confirm -> the $0 invoice               (Transaction + Interactive)

Write the cost down first (docs/recipes/inventory-cost-edit.md) so the
shipment relieves inventory at the token cost. Every $0 line raises an
"unpriced -- ship anyway?" prompt at shipping; each is answered with its
proceed button.

Mirrors: docs/recipes/dispose-zero-value-stock.md

Usage:
    python examples/python/recipes/dispose_zero_value_stock.py            # dry run
    python examples/python/recipes/dispose_zero_value_stock.py --execute  # run + verify
"""

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from runbook_common import (P21Runbook, check, edit, element, enter_order, payload,
                            print_invoice, print_pick_ticket, ship_and_invoice, show)

import warnings
warnings.filterwarnings("ignore")

# --- Configuration (generic placeholders -- substitute your own) ------------
LOCATION_ID = "10"
TOKEN_COST = "0.02"            # inv_loc.moving_average_cost after the write-down
CUSTOMER_ID = "CUST-100"       # the internal disposal customer
SHIP_TO_ID = "CUST-100"
CONTACT_ID = "300"
SALESREP_ID = "REP-HOUSE"      # the rep the order must carry -- allowed at LOCATION_ID
TAKER = "JSMITH"               # the real person; it defaults to the API user
PO_NO = "DISPOSAL 2026-10"     # a recognizable label; orders past the first get " - 02", ...
LINES_PER_ORDER = 100          # per-line time grows with order size -- split at ~100

TODAY = date.today()


def build_item_list(rb: P21Runbook, args: argparse.Namespace) -> list[tuple[str, str]]:
    """Step 1: (item_id, qty) for every unallocated item on hand at the token cost.

    Built from live inv_loc rows -- never from a count spreadsheet.
    """
    rows = rb.odata("inv_loc",
                    f"location_id eq {args.location} and moving_average_cost eq {args.token_cost} "
                    "and qty_on_hand gt 0",
                    "inv_mast_uid,qty_on_hand,qty_allocated,moving_average_cost")
    items = []
    for row in rows:
        item_id = rb.one("inv_mast", f"inv_mast_uid eq {row['inv_mast_uid']}",
                         "item_id,delete_flag")["item_id"]
        if args.items and item_id not in args.items:
            continue
        if float(row["qty_allocated"]) != 0:
            print(f"    skip {item_id}: qty_allocated {row['qty_allocated']}")
            continue
        items.append((item_id, f"{float(row['qty_on_hand']):g}"))
    for item_id, qty in items:
        print(f"    {item_id}: {qty} on hand at {args.token_cost}")
    return items


def build_append_payload(order_no: str, lines: list[tuple[str, str]]) -> dict:
    """Step 3: every remaining line as rows of ONE TP_ITEMS element (Keys []).

    One Transaction per line collides with the existing line; one row that
    cannot allocate fails the whole Transaction.
    """
    rows = [[edit("oe_order_item_id", item_id), edit("unit_quantity", qty),
             edit("unit_price", "0")] for item_id, qty in lines]
    return payload("Order", [
        element("TABPAGE_1.order", "Form", ["order_no"], [[edit("order_no", order_no)]]),
        element("TP_ITEMS.items", "List", [], rows),
    ])


def build_release_payload(order_no: str) -> dict:
    """Step 4: release the Hold through TP_SHIPINFO; allocation is untouched."""
    return payload("Order", [
        element("TABPAGE_1.order", "Form", ["order_no"], [[edit("order_no", order_no)]]),
        element("TP_SHIPINFO.shipinfo", "Form", [], [[edit("packing_basis", "Partial")]]),
    ])


def dispose_order(rb: P21Runbook, args: argparse.Namespace, po_no: str,
                  lines: list[tuple[str, str]]) -> None:
    """Steps 2-5 for one order of up to LINES_PER_ORDER lines."""
    print(f"\nStep 2 - Header + line 1 on Hold, rep {args.salesrep} (Interactive Order)")
    header = {"sales_loc_id": args.location, "source_loc_id": args.location,
              "customer_id": args.customer, "ship_to_id": args.ship_to,
              "contact_id": args.contact, "order_date": TODAY.isoformat(),
              "requested_date": (TODAY + timedelta(days=2)).isoformat(),
              "po_no": po_no, "taker": args.taker}
    first_item, first_qty = lines[0]
    order_no = enter_order(rb, header, [[("oe_order_item_id", first_item),
                                         ("unit_quantity", first_qty), ("unit_price", "0")]],
                           salesrep=args.salesrep, hold=True)
    reps = rb.odata("oe_hdr_salesrep", f"order_number eq '{order_no}' and delete_flag eq 'N'",
                    "salesrep_id,primary_salesrep")
    check("oe_hdr_salesrep rows", len(reps), 1)
    check("oe_hdr_salesrep.salesrep_id", reps[0]["salesrep_id"], args.salesrep)

    if len(lines) > 1:
        print(f"\nStep 3 - Append {len(lines) - 1} line(s) in one Transaction (Transaction Order)")
        rb.transaction(build_append_payload(order_no, lines[1:]), "Append lines")

    live = rb.odata("oe_line", f"order_no eq '{order_no}' and delete_flag eq 'N' and cancel_flag eq 'N'",
                    "line_no,qty_ordered,qty_allocated,unit_price")
    check("live oe_line rows", len(live), len(lines))
    check("SUM(qty_allocated) = SUM(qty_ordered)", sum(float(r["qty_allocated"]) for r in live),
          sum(float(r["qty_ordered"]) for r in live))
    check("MAX(unit_price)", max(float(r["unit_price"]) for r in live), 0.0)

    print("\nStep 4 - Release the Hold (Transaction Order, TP_SHIPINFO)")
    rb.transaction(build_release_payload(order_no), "Release hold")
    hdr = rb.one("oe_hdr", f"order_no eq '{order_no}'", "packing_basis")
    check("oe_hdr.packing_basis", hdr["packing_basis"], "Partial")

    print("\nStep 5 - Pick ticket, ship, $0 invoice")
    pick_ticket_no = print_pick_ticket(rb, order_no)
    invoice_no = ship_and_invoice(rb, pick_ticket_no)  # one cb_1 per unpriced line
    inv_lines = print_invoice(rb, invoice_no)
    check("invoice total of unit prices", sum(float(x["unit_price"]) for x in inv_lines), 0.0)
    for line in rb.odata("oe_line", f"order_no eq '{order_no}'", "line_no,qty_ordered,qty_invoiced"):
        check(f"oe_line {line['line_no']} qty_invoiced", float(line["qty_invoiced"]),
              float(line["qty_ordered"]))


def main() -> None:
    """Entry point: dry run prints the plan; --execute runs and verifies each step."""
    parser = argparse.ArgumentParser(
        description="Dispose of zero-value stock (docs/recipes/dispose-zero-value-stock.md)")
    parser.add_argument("--location", default=LOCATION_ID)
    parser.add_argument("--token-cost", default=TOKEN_COST)
    parser.add_argument("--items", nargs="*", default=[],
                        help="Only these item IDs (default: every item at the token cost)")
    parser.add_argument("--customer", default=CUSTOMER_ID)
    parser.add_argument("--ship-to", default=SHIP_TO_ID)
    parser.add_argument("--contact", default=CONTACT_ID)
    parser.add_argument("--salesrep", default=SALESREP_ID)
    parser.add_argument("--taker", default=TAKER)
    parser.add_argument("--po-no", default=PO_NO)
    parser.add_argument("--execute", action="store_true",
                        help="Actually run the steps (default: dry run)")
    args = parser.parse_args()

    print("Runbook - Dispose of Zero-Value Stock with a $0 Order")
    print("=" * 60)
    if not args.execute:
        print(f"""
Step 1 (OData): inv_loc where location_id eq {args.location} and moving_average_cost eq
        {args.token_cost} and qty_on_hand gt 0; keep qty_allocated = 0.
Step 2 (Interactive Order, per order of up to {LINES_PER_ORDER} lines): quote=OFF, header,
        TP_SALESREPS row 1 salesrep_id={args.salesrep}, packing_basis=Hold, line 1 at
        unit_price 0 (assembly prompt -> cb_2), save.""")
        show("Step 3 append payload (order_no from step 2, lines 2..n)",
             build_append_payload("{order_no}", [("ITEM-002", "4"), ("ITEM-003", "1")]))
        show("Step 4 release payload", build_release_payload("{order_no}"))
        print("\nStep 5: print_tix, then Interactive Shipping save (cb_1 per unpriced line).")
        print("\nRe-run with --execute to run it.")
        return

    rb = P21Runbook()
    print("\nStep 1 - Build the item list from live data (OData inv_loc)")
    items = build_item_list(rb, args)
    if not items:
        raise SystemExit("Nothing on hand at the token cost -- nothing to dispose")
    before = {i: float(q) for i, q in items}

    chunks = [items[i:i + LINES_PER_ORDER] for i in range(0, len(items), LINES_PER_ORDER)]
    for n, chunk in enumerate(chunks, start=1):
        po_no = args.po_no if len(chunks) == 1 else f"{args.po_no} - {n:02d}"
        dispose_order(rb, args, po_no, chunk)

    print("\nVerify - inventory relieved at the location")
    for item_id, qty in before.items():
        row = rb.one("inv_loc", f"inv_mast_uid eq {rb.item_uid(item_id)} and "
                                f"location_id eq {args.location}", "qty_on_hand")
        check(f"{item_id} qty_on_hand", float(row["qty_on_hand"]), 0.0)
    print("\nRunbook complete.")


if __name__ == "__main__":
    main()
