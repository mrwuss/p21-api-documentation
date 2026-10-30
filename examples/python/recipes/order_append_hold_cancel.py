"""
Append Lines, Release a Hold, or Cancel a Saved Order (Order service)

Three edits to an existing sales order. Each loads the order with the keyed
header TABPAGE_1.order (Keys ["order_no"]) and sends one more element:

    append        all new lines as rows of ONE TP_ITEMS.items element
                  (Keys []). Do not send one Transaction per line: they
                  collide with the saved lines ("Item ID X has been saved;
                  therefore, the Item ID cannot be edited").
    release-hold  packing_basis on TP_SHIPINFO.shipinfo (Form, Keys []).
                  On some tenants the header copy of packing_basis is a
                  disabled column for the API user; this one is enabled.
    cancel        cancel_flag = ON on the header. P21 sets cancel_flag and
                  completed on the header and cancel_flag on every line.

Pre-checks before any write: the order exists, is not deleted or canceled,
and is not held open (oe_hdr.completed = 'T' means someone -- possibly your
own API user -- has it in edit, and every write is refused). For append, an
item already on the order is refused: a row with that item ID updates the
existing line's quantity instead of adding a line.

After the write the script reads oe_hdr and the live oe_line rows
(delete_flag = 'N') back over OData. A failed append leaves soft-deleted
rows, so always filter on delete_flag.

Mirrors: docs/03-Transaction-API.md#order-service-line-appends-cancels-holds-and-item-lookup

Usage:
    python examples/python/recipes/order_append_hold_cancel.py append 1001234 \\
        --line ITEM-001:2 --line ITEM-002:3 --execute
    python examples/python/recipes/order_append_hold_cancel.py release-hold 1001234 --execute
    python examples/python/recipes/order_append_hold_cancel.py cancel 1001234 --execute
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from common.tapi import connect, edit, odata, odata_quote, post_transaction

import warnings

warnings.filterwarnings("ignore")

HEADER_COLUMNS = "order_no,packing_basis,cancel_flag,completed,delete_flag"
LINE_COLUMNS = "line_no,inv_mast_uid,qty_ordered,qty_allocated,cancel_flag,delete_flag"


def build_payload(args: argparse.Namespace) -> dict:
    """Build the Order payload for the chosen mode.

    Args:
        args: Parsed command-line options.

    Returns:
        dict: Complete Transaction API payload.
    """
    header_edits = [edit("order_no", args.order_no)]
    if args.mode == "cancel":
        header_edits.append(edit("cancel_flag", "ON"))
    elements = [
        {
            "Name": "TABPAGE_1.order",
            "Type": "Form",
            "Keys": ["order_no"],
            "Rows": [{"Edits": header_edits, "RelativeDateEdits": []}],
        }
    ]

    if args.mode == "append":
        rows = []
        for spec in args.line:
            item_id, qty, *price = spec.split(":")
            edits = [edit("oe_order_item_id", item_id), edit("unit_quantity", qty)]
            if price:
                edits.append(edit("unit_price", price[0]))
            rows.append({"Edits": edits, "RelativeDateEdits": []})
        # Every new line is a row of ONE element in ONE Transaction.
        elements.append(
            {"Name": "TP_ITEMS.items", "Type": "List", "Keys": [], "Rows": rows}
        )
    elif args.mode == "release-hold":
        elements.append(
            {
                "Name": "TP_SHIPINFO.shipinfo",
                "Type": "Form",
                "Keys": [],
                "Rows": [
                    {
                        "Edits": [edit("packing_basis", args.packing_basis)],
                        "RelativeDateEdits": [],
                    }
                ],
            }
        )

    return {
        "Name": "Order",
        "UseCodeValues": False,
        "Transactions": [{"Status": "New", "DataElements": elements}],
    }


def read_order(session, order_no: str) -> tuple[dict | None, list[dict]]:
    """Read the header and its live lines.

    Args:
        session: Session from connect().
        order_no: The order number.

    Returns:
        tuple: (oe_hdr row or None, live oe_line rows).
    """
    hdr = odata(
        session, "oe_hdr", f"order_no eq {odata_quote(order_no)}", HEADER_COLUMNS
    )
    lines = odata(
        session,
        "oe_line",
        f"order_no eq {odata_quote(order_no)} and delete_flag eq 'N'",
        LINE_COLUMNS,
    )
    return (hdr[0] if hdr else None), sorted(lines, key=lambda r: r["line_no"])


def show(label: str, hdr: dict | None, lines: list[dict]) -> None:
    """Print the header and lines.

    Args:
        label: Heading.
        hdr: oe_hdr row.
        lines: oe_line rows.
    """
    print(f"\n{label}")
    print(f"  oe_hdr: {hdr}")
    for line in lines:
        print(f"  oe_line: {line}")


def main() -> None:
    """Entry point: dry run prints the payload; --execute checks, posts, reads back."""
    parser = argparse.ArgumentParser(
        description="Append lines, release a hold, or cancel a saved order"
    )
    parser.add_argument("mode", choices=["append", "release-hold", "cancel"])
    parser.add_argument("order_no")
    parser.add_argument(
        "--line",
        action="append",
        metavar="ITEM:QTY[:PRICE]",
        help="Line to append (repeatable; append mode)",
    )
    parser.add_argument(
        "--packing-basis",
        default="Partial",
        help="Value that replaces Hold (release-hold mode)",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually POST the transaction (default: dry run)",
    )
    args = parser.parse_args()
    if args.mode == "append" and not args.line:
        parser.error("append needs at least one --line ITEM:QTY")

    print(f"Recipe - Order: {args.mode} (Order service)")
    print("=" * 60)
    payload = build_payload(args)
    if not args.execute:
        print(
            "\nDRY RUN - payload that would be POSTed to {ui_server}/api/v2/transaction:"
        )
        print(json.dumps(payload, indent=2))
        print("\nRe-run with --execute to POST it.")
        return

    session = connect()
    print(f"UI Server: {session.ui_server}")
    hdr, lines = read_order(session, args.order_no)
    if not hdr:
        raise SystemExit(f"Order {args.order_no} not found")
    show("Before:", hdr, lines)
    if hdr["delete_flag"] == "Y" or hdr["cancel_flag"] == "Y":
        raise SystemExit("Order is deleted or canceled")
    if hdr["completed"] == "T":
        raise SystemExit(
            "Order is held open (completed = 'T') -- every write would be refused"
        )

    if args.mode == "append":
        on_order = {line["inv_mast_uid"] for line in lines}
        for spec in args.line:
            item_id = spec.split(":")[0]
            found = odata(
                session,
                "inv_mast",
                f"item_id eq {odata_quote(item_id)} and delete_flag eq 'N'",
                "inv_mast_uid",
            )
            if not found:
                raise SystemExit(
                    f"Item {item_id} not found (exact ID, live items only)"
                )
            if found[0]["inv_mast_uid"] in on_order:
                raise SystemExit(
                    f"{item_id} is already on the order -- the row would "
                    "update that line, not add one"
                )

    print()
    post_transaction(session, payload, timeout=900)  # a cancel reloads the whole order
    show(
        "After (OData read-back, live lines only):", *read_order(session, args.order_no)
    )


if __name__ == "__main__":
    main()
