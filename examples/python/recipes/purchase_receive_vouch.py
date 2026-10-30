"""
Purchasing Runbook -- Stock PO -> Receipt -> Voucher, and Drop Ship

Runs both buy-side paths from docs/recipes/purchase-receive-vouch.md, one
step at a time, reading each step back before the next one starts:

  Path A (stock):     A1 PurchaseOrder -> A2 PurchaseOrderReceipt
                      -> A3 ConvertPOToVoucher                (Transaction API)
  Path B (drop ship): B1 Order with a disposition-D line      (Interactive)
                      B2 re-open, c_create_po ON, PO wizard   (Interactive)
                      B3 DirectShipConfirmation               (Interactive)
                      B4 ConvertPOToVoucher on that receipt   (Transaction API)

Path A needs an item whose primary bin at the location is usable (not a
put-locked bin such as '0'). Path B needs an API user with a Buyer ID in
User Maintenance -- run it with --auth consumer when your consumer-key user
is the one that has it.

Mirrors: docs/recipes/purchase-receive-vouch.md

Usage:
    python examples/python/recipes/purchase_receive_vouch.py                      # dry run
    python examples/python/recipes/purchase_receive_vouch.py --path A --execute   # stock path
    python examples/python/recipes/purchase_receive_vouch.py --path B --auth consumer --execute
"""

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from runbook_common import (
    P21Runbook,
    check,
    edit,
    element,
    enter_order,
    is_blocked,
    payload,
    popup_ids,
    result_value,
    show,
)

import warnings

warnings.filterwarnings("ignore")

# --- Configuration (generic placeholders -- substitute your own) ------------
LOCATION_ID = "10"
VENDOR_ID = "SUP-100"  # vendor_id; the same ID as the supplier
BUYER_ID = "100"  # an employee NUMBER -- stored in po_hdr.requested_by
STOCK_ITEM = "ITEM-001"  # Path A: primary bin at LOCATION_ID must be usable
STOCK_QTY = "2"
STOCK_PRICE = "6.55"  # sent as unit_price_display, not unit_price
CUSTOMER_ID = "CUST-100"  # Path B
SHIP_TO_ID = "CUST-100"
CONTACT_ID = "300"
TAKER = "JSMITH"
DS_ITEM = "ITEM-002"  # Path B: its primary supplier at LOCATION_ID gets the PO
DS_QTY = "3"
DS_PRICE = "4.00"
DS_PO_COST = "2.50"  # the deal's buy price -> the PO line price
TAG = "RUNBOOK-001"  # tags the PO (external_po_no) and the order (po_no)

TODAY = date.today()


# --- Path A ------------------------------------------------------------------


def build_po_payload(args: argparse.Namespace) -> dict:
    """A1: PurchaseOrder header + one line. Omit division_id/company_id; they default."""
    header = [
        edit("location_id", args.location),
        edit("vendor_id", args.vendor),
        edit("buyer_id", args.buyer),
        edit("order_date", TODAY.isoformat()),
        edit("required_date", (TODAY + timedelta(days=5)).isoformat()),
        edit("external_po_no", f"{args.tag}-A"),
    ]
    line = [
        edit("item_id", args.item),
        edit("unit_quantity", args.qty),
        edit("unit_of_measure", "EA"),
        edit("pricing_unit", "EA"),
        edit("unit_price_display", args.price),
    ]  # "PO Price" -- NOT unit_price
    return payload(
        "PurchaseOrder",
        [
            element("TABPAGE_1.tp_1_dw_1", "Form", [], [header]),
            element("TABPAGE_17.tp_17_dw_17", "List", ["item_id"], [line]),
        ],
    )


def build_receipt_payload(po_no: str, tag: str) -> dict:
    """A2: receive every line at its remaining quantity -- the whole payload."""
    return payload(
        "PurchaseOrderReceipt",
        [
            element(
                "TABPAGE_1.tp_1_dw_po",
                "Form",
                [],
                [[edit("po_no", po_no), edit("receive_all", "Y")]],
            ),
            element(
                "TABPAGE_1.tp_1_dw_1",
                "Form",
                [],
                [[edit("external_reference_no", tag)]],
            ),
        ],
    )


def build_voucher_payload(
    po_no: str, receipt_no: str, vendor: str, invoice_no: str, lines: list[dict]
) -> dict:
    """A3/B4: voucher header + one row per receipt line.

    Send these five header fields and nothing else: company_id, branch_id,
    period and year_for_period are marked required AND are disabled columns.
    invoice_amount must equal the vouched lines or P21 holds the variance.
    """
    amount = sum(float(r["qty"]) * float(r["cost"]) for r in lines)
    header = [
        edit("po_no", po_no),
        edit("invoice_no", invoice_no),
        edit("invoice_date", TODAY.isoformat()),
        edit("invoice_amount", f"{amount:.2f}"),
        edit("vendor_id", vendor),
    ]
    rows = [
        [
            edit("receipt_number", receipt_no),
            edit("line_number", str(r["line_number"])),
            edit("po_no", po_no),
            edit("unit_qty_invoiced", str(r["qty"])),
            edit("unit_cost_display", str(r["cost"])),
        ]
        for r in lines
    ]
    return payload(
        "ConvertPOToVoucher",
        [
            element(
                "TABPAGE_1.tp_1_dw_1", "Form", ["voucher_no"], [header]
            ),  # voucher_no empty = create
            element(
                "TABPAGE_17.tp_17_dw_17",
                "List",
                ["receipt_number", "line_number", "po_no"],
                rows,
            ),
        ],
    )


def create_po(rb: P21Runbook, args: argparse.Namespace) -> str:
    """A1: create the stock PO and read po_hdr/po_line back."""
    print("\nA1 - Create the PO (Transaction PurchaseOrder)")
    result = rb.transaction(build_po_payload(args), "PurchaseOrder")
    po_no = result_value(result, "TABPAGE_1.tp_1_dw_1", "po_no")
    hdr = rb.one(
        "po_hdr", f"po_no eq {po_no}", "po_no,po_type,approved,vendor_id,location_id"
    )
    print(
        f"    po_no = {po_no}, po_type = {hdr['po_type']}, approved = {hdr['approved']}"
    )
    line = rb.one("po_line", f"po_no eq {po_no}", "line_no,qty_ordered,unit_price")
    check("po_line.unit_price", float(line["unit_price"]), float(args.price))
    return po_no


def receive_po(rb: P21Runbook, po_no: str, tag: str) -> str:
    """A2: receive the whole PO and read the receipt and po_line back."""
    print("\nA2 - Receive it (Transaction PurchaseOrderReceipt)")
    result = rb.transaction(build_receipt_payload(po_no, tag), "PurchaseOrderReceipt")
    receipt_no = (
        result_value(result, "TABPAGE_1.tp_1_dw_po", "receipt_number")
        or rb.one(
            "inventory_receipts_hdr",
            f"po_number eq {po_no}",
            "receipt_number",
            orderby="receipt_number desc",
        )["receipt_number"]
    )
    print(f"    receipt_number = {receipt_no}")
    for line in rb.odata(
        "po_line", f"po_no eq {po_no}", "line_no,qty_ordered,qty_received"
    ):
        check(
            f"po_line {line['line_no']} qty_received",
            float(line["qty_received"]),
            float(line["qty_ordered"]),
        )
    return str(receipt_no)


def receipt_lines(rb: P21Runbook, receipt_no: str) -> list[dict]:
    """Receipt lines to vouch (inventory_receipts_line uses line_number, not line_no)."""
    rows = rb.odata(
        "inventory_receipts_line",
        f"receipt_number eq {receipt_no}",
        "line_number,qty_received,unit_cost",
    )
    return [
        {
            "line_number": r["line_number"],
            "qty": f"{float(r['qty_received']):g}",
            "cost": f"{float(r['unit_cost']):g}",
        }
        for r in rows
    ]


def vouch(
    rb: P21Runbook, po_no: str, receipt_no: str, vendor: str, invoice_no: str
) -> str:
    """A3/B4: vouch the vendor invoice against the receipt and read it back."""
    lines = receipt_lines(rb, receipt_no)
    result = rb.transaction(
        build_voucher_payload(po_no, receipt_no, vendor, invoice_no, lines),
        "ConvertPOToVoucher",
    )
    voucher_no = result_value(result, "TABPAGE_1.tp_1_dw_1", "voucher_no")
    hdr = rb.one(
        "apinv_hdr",
        f"voucher_no eq '{voucher_no}'",
        "voucher_no,po_no,invoice_no,invoice_amount,approved",
    )
    print(
        f"    voucher_no = {voucher_no}, invoice_amount = {hdr['invoice_amount']}, "
        f"approved = {hdr['approved']}"
    )
    for line in rb.odata(
        "inventory_receipts_line",
        f"receipt_number eq {receipt_no}",
        "line_number,qty_received,qty_vouched,vouch_complete",
    ):
        check(
            f"receipt line {line['line_number']} vouch_complete",
            line["vouch_complete"],
            "Y",
        )
    return voucher_no


# --- Path B ------------------------------------------------------------------


def enter_direct_ship_order(rb: P21Runbook, args: argparse.Namespace) -> str:
    """B1: a sales order whose line is disposition D, set while the line is entered."""
    print("\nB1 - Sales order with a direct-ship line (Interactive Order)")
    header = {
        "sales_loc_id": args.location,
        "source_loc_id": args.location,
        "customer_id": args.customer,
        "ship_to_id": args.ship_to,
        "contact_id": args.contact,
        "order_date": TODAY.isoformat(),
        "requested_date": (TODAY + timedelta(days=2)).isoformat(),
        "po_no": f"{args.tag}-B",
        "taker": args.taker,
    }
    line = [
        ("oe_order_item_id", args.ds_item),
        ("unit_quantity", args.ds_qty),
        ("disposition", "D"),  # at entry, or later once the line holds no allocation
        ("unit_price", args.ds_price),
        ("po_cost", args.ds_po_cost),
    ]  # flows to the PO line's price
    order_no = enter_order(rb, header, [line])
    row = rb.one("oe_line", f"order_no eq '{order_no}'", "line_no,disposition,po_cost")
    check("oe_line.disposition", row["disposition"], "D")
    return order_no


def create_po_from_order(rb: P21Runbook, order_no: str) -> str:
    """B2: re-open the saved order, c_create_po ON, save, and drive the PO wizard.

    The wizard is identified by its buttons (cb_finish present) before
    anything is pressed. The PO is committed at cb_next, before cb_finish.
    """
    print("\nB2 - Re-open, c_create_po = ON, save, PO wizard (Interactive Order)")
    session = rb.session()
    window_id = session.open_window("Order")
    wizard_po = None
    try:
        session.change(window_id, "TABPAGE_1", "order", "order_no", order_no)
        session.change(
            window_id, "TABPAGE_1", "order", "c_create_po", "ON"
        )  # needs a Buyer ID
        result = session.save_raw(window_id)
        for _ in range(10):
            if not is_blocked(result):
                break
            for popup_id in popup_ids(result):
                tools = session.tools(popup_id)
                if "cb_finish" not in tools:  # some other prompt: proceed
                    pick = next(b for b in ("cb_ok", "cb_1", "cb_yes") if b in tools)
                    result = session.click(popup_id, pick)
                    continue
                for row in session.rows(popup_id, "items"):
                    print(
                        f"    wizard page 1: {row.get('item_id')} qty {row.get('qty_to_purchase')} "
                        f"supplier {row.get('supplier_id')} quote_item={row.get('quote_item')}"
                    )
                session.click(popup_id, "cb_next")  # <-- the PO is committed HERE
                for row in session.rows(popup_id, "po_print"):
                    wizard_po = row.get("po_no")
                    print(
                        f"    wizard page 2: po_no {wizard_po}, po_type {row.get('po_type')}"
                    )
                result = session.click(popup_id, "cb_finish")
    finally:
        session.cleanup(window_id)
    link = rb.one(
        "oe_line_po",
        f"order_number eq '{order_no}'",
        "order_number,line_number,po_no,po_line_number,connection_type",
    )
    check("oe_line_po.connection_type", link["connection_type"], "P")
    po_no = str(link["po_no"])
    hdr = rb.one("po_hdr", f"po_no eq {po_no}", "po_no,po_type,approved,external_po_no")
    check("po_hdr.po_type", hdr["po_type"], "D")
    if wizard_po and str(wizard_po) != po_no:
        raise SystemExit(f"Wizard showed PO {wizard_po}, oe_line_po links {po_no}")
    return po_no


def confirm_direct_ship(rb: P21Runbook, po_no: str, order_no: str) -> str:
    """B3: Interactive DirectShipConfirmation -- receipt AND customer invoice in one save.

    Never send c_email_invoice. shipment_date, period and year_for_period
    pre-fill; the save writes shipment_date onto every po_line.supplier_ship_date.
    """
    print("\nB3 - Confirm the direct ship (Interactive DirectShipConfirmation)")
    session = rb.session()
    window_id = session.open_window("DirectShipConfirmation")
    try:
        session.change(window_id, "TABPAGE_1", "tp_1_dw_po", "po_no", po_no)
        session.change(window_id, "TABPAGE_1", "tp_1_dw_po", "receive_all", "ON")
        session.save(window_id)
    finally:
        session.cleanup(window_id)
    receipt = rb.one(
        "inventory_receipts_hdr",
        f"po_number eq {po_no}",
        "receipt_number,receipt_type,shipment_date",
        orderby="receipt_number desc",
    )
    print(
        f"    receipt_number = {receipt['receipt_number']} (type {receipt['receipt_type']}, "
        f"shipment_date {receipt['shipment_date']})"
    )
    for line in rb.odata(
        "po_line", f"po_no eq {po_no}", "line_no,complete,qty_received"
    ):
        check(f"po_line {line['line_no']} complete", line["complete"], "Y")
    for line in rb.odata(
        "oe_line", f"order_no eq '{order_no}'", "line_no,qty_ordered,qty_invoiced"
    ):
        check(
            f"oe_line {line['line_no']} qty_invoiced",
            float(line["qty_invoiced"]),
            float(line["qty_ordered"]),
        )
    inv = rb.one("invoice_hdr", f"order_no eq '{order_no}'", "invoice_no,total_amount")
    print(f"    customer invoice {inv['invoice_no']}, total {inv['total_amount']}")
    return str(receipt["receipt_number"])


# --- Runner ------------------------------------------------------------------


def dry_run(args: argparse.Namespace) -> None:
    """Print every Transaction payload and the Interactive call plan."""
    if args.path in ("A", "both"):
        show("A1 PurchaseOrder payload", build_po_payload(args))
        show(
            "A2 PurchaseOrderReceipt payload (po_no from A1)",
            build_receipt_payload("{po_no}", f"{args.tag}-A"),
        )
        show(
            "A3 ConvertPOToVoucher payload (one row per receipt line from A2)",
            build_voucher_payload(
                "{po_no}",
                "{receipt_number}",
                args.vendor,
                f"{args.tag}-A",
                [{"line_number": 1, "qty": args.qty, "cost": args.price}],
            ),
        )
    if args.path in ("B", "both"):
        print(f"""
Path B call plan (Interactive API, session with ResponseWindowHandlingEnabled):
  B1 Order window: quote=OFF, sales/source_loc_id={args.location}, customer_id={args.customer},
     ship_to_id={args.ship_to}, contact_id={args.contact}, dates (cb_ok), po_no={args.tag}-B,
     taker={args.taker}; TP_ITEMS: oe_order_item_id={args.ds_item}, unit_quantity={args.ds_qty},
     disposition=D, unit_price={args.ds_price}, po_cost={args.ds_po_cost}; save.
  B2 Order window: order_no=<B1>, c_create_po=ON, save -> wizard (cb_finish in its tools):
     cb_next (PO committed), cb_finish. Read oe_line_po (connection_type P), po_hdr (po_type D).
  B3 DirectShipConfirmation: tp_1_dw_po.po_no=<B2>, receive_all=ON, save.
  B4 ConvertPOToVoucher against the B3 receipt (payload as A3).""")
    print("\nRe-run with --execute to run it.")


def main() -> None:
    """Entry point: dry run prints the plan; --execute runs and verifies each step."""
    parser = argparse.ArgumentParser(
        description="Purchasing runbook (docs/recipes/purchase-receive-vouch.md)"
    )
    parser.add_argument("--path", choices=["A", "B", "both"], default="both")
    parser.add_argument(
        "--auth",
        choices=["password", "consumer"],
        default="password",
        help="consumer = P21_CONSUMER_KEY as P21_CONSUMER_USERNAME",
    )
    parser.add_argument("--location", default=LOCATION_ID)
    parser.add_argument("--vendor", default=VENDOR_ID)
    parser.add_argument("--buyer", default=BUYER_ID)
    parser.add_argument("--item", default=STOCK_ITEM)
    parser.add_argument("--qty", default=STOCK_QTY)
    parser.add_argument("--price", default=STOCK_PRICE)
    parser.add_argument("--customer", default=CUSTOMER_ID)
    parser.add_argument("--ship-to", default=SHIP_TO_ID)
    parser.add_argument("--contact", default=CONTACT_ID)
    parser.add_argument("--taker", default=TAKER)
    parser.add_argument("--ds-item", default=DS_ITEM)
    parser.add_argument("--ds-qty", default=DS_QTY)
    parser.add_argument("--ds-price", default=DS_PRICE)
    parser.add_argument("--ds-po-cost", default=DS_PO_COST)
    parser.add_argument("--tag", default=TAG)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually run the steps (default: dry run)",
    )
    args = parser.parse_args()

    print("Runbook - Purchasing: Stock PO -> Receipt -> Voucher, and Drop Ship")
    print("=" * 60)
    if not args.execute:
        dry_run(args)
        return

    rb = P21Runbook(args.auth)
    if args.path in ("A", "both"):
        po_no = create_po(rb, args)
        receipt_no = receive_po(rb, po_no, f"{args.tag}-A")
        print("\nA3 - Vouch the vendor invoice (Transaction ConvertPOToVoucher)")
        vouch(rb, po_no, receipt_no, args.vendor, f"{args.tag}-A")
    if args.path in ("B", "both"):
        order_no = enter_direct_ship_order(rb, args)
        po_no = create_po_from_order(rb, order_no)
        receipt_no = confirm_direct_ship(rb, po_no, order_no)
        print(
            "\nB4 - Vouch the vendor invoice against the B3 receipt (ConvertPOToVoucher)"
        )
        vendor = str(rb.one("po_hdr", f"po_no eq {po_no}", "vendor_id")["vendor_id"])
        vouch(rb, po_no, receipt_no, vendor, f"{args.tag}-B")
    print("\nRunbook complete.")


if __name__ == "__main__":
    main()
