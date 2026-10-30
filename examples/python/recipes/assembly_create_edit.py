"""
Create an Assembly on a Plain Item, Then Edit It (Assembly service)

Four modes, all keyed Status "New" Transactions on the Assembly service and
none of them using IgnoreDisabled:

    create            header TABPAGE_1.assemblyhdr (inv_mast_item_id +
                      production_order_processing) plus one
                      TABPAGE_17.tp_17_dw_17 row per component
    set-flag          a header flag, keyed on inv_mast_item_id
    set-qty           one component's quantity, keyed on item_id_service_labor_id
    delete-component  delete_flag = ON on one component row

Create rules:

  * The item must already exist (create it with the Inventory REST API) and
    must not already have an assembly.
  * The item must not already be a component of another assembly. The window
    asks "...is a component of an existing assembly, continue?", the
    Transaction API answers No, and the save fails with a SQL NULL-insert
    error. The script checks assembly_line first and stops; use the
    Interactive Assembly window for that item.
  * Send production_order_processing explicitly -- its default can be ON,
    which makes the item a production-order assembly rather than a kit.
  * item_desc and prorate_cost_by are disabled on create; set other header
    fields with a set-flag call afterwards.
  * allow_disassembly is disabled while production_order_processing is OFF,
    and turning production_order_processing OFF resets it to N.

Every mode reads assembly_hdr and assembly_line back over OData.

Mirrors: docs/03-Transaction-API.md#assembly-service

Usage:
    python examples/python/recipes/assembly_create_edit.py create ITEM-001 \\
        --component COMP-A:2 --component COMP-B:1                       # dry run
    python examples/python/recipes/assembly_create_edit.py create ITEM-001 \\
        --component COMP-A:2 --component COMP-B:1 --execute             # POST + verify
    python examples/python/recipes/assembly_create_edit.py set-flag ITEM-001 \\
        --field production_order_processing --value ON --execute
    python examples/python/recipes/assembly_create_edit.py set-qty ITEM-001 COMP-A 5 --execute
    python examples/python/recipes/assembly_create_edit.py delete-component ITEM-001 COMP-B --execute
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from common.tapi import connect, edit, odata, odata_quote, post_transaction

import warnings

warnings.filterwarnings("ignore")

HEADER = "TABPAGE_1.assemblyhdr"
COMPONENTS = "TABPAGE_17.tp_17_dw_17"


def header_element(item_id: str, extra: list[dict] | None = None) -> dict:
    """Build the assembly header element, keyed on the assembly's item ID.

    Args:
        item_id: The assembly (parent) item ID.
        extra: Header edits to send after the key.

    Returns:
        dict: The TABPAGE_1.assemblyhdr DataElement.
    """
    return {
        "Name": HEADER,
        "Type": "Form",
        "Keys": ["inv_mast_item_id"],
        "Rows": [
            {
                "Edits": [edit("inv_mast_item_id", item_id)] + (extra or []),
                "RelativeDateEdits": [],
            }
        ],
    }


def component_element(rows: list[list[dict]]) -> dict:
    """Build the component grid element, keyed on the component item ID.

    Args:
        rows: One list of edits per component row.

    Returns:
        dict: The TABPAGE_17.tp_17_dw_17 DataElement.
    """
    return {
        "Name": COMPONENTS,
        "Type": "List",
        "Keys": ["item_id_service_labor_id"],
        "Rows": [{"Edits": edits, "RelativeDateEdits": []} for edits in rows],
    }


def build_payload(args: argparse.Namespace) -> dict:
    """Build the Assembly payload for the chosen mode.

    Args:
        args: Parsed command-line options.

    Returns:
        dict: Complete Transaction API payload.
    """
    if args.mode == "create":
        components = []
        for spec in args.component:
            component_id, _, qty = spec.rpartition(":")
            components.append(
                [edit("item_id_service_labor_id", component_id), edit("quantity", qty)]
            )
        elements = [
            header_element(
                args.item_id,
                [edit("production_order_processing", args.production_order_processing)],
            ),
            component_element(components),
        ]
    elif args.mode == "set-flag":
        elements = [header_element(args.item_id, [edit(args.field, args.value)])]
    elif args.mode == "set-qty":
        elements = [
            header_element(args.item_id),
            component_element(
                [
                    [
                        edit("item_id_service_labor_id", args.component_id),
                        edit("quantity", args.quantity),
                    ]
                ]
            ),
        ]
    else:  # delete-component
        elements = [
            header_element(args.item_id),
            component_element(
                [
                    [
                        edit("item_id_service_labor_id", args.component_id),
                        edit("delete_flag", "ON"),
                    ]
                ]
            ),
        ]
    return {
        "Name": "Assembly",
        "UseCodeValues": False,
        "Transactions": [{"Status": "New", "DataElements": elements}],
    }


def item_uid(session, item_id: str) -> int:
    """Resolve an item ID to its inv_mast_uid (live items only).

    Args:
        session: Session from connect().
        item_id: Exact item ID.

    Returns:
        int: The item's inv_mast_uid.
    """
    rows = odata(
        session,
        "inv_mast",
        f"item_id eq {odata_quote(item_id)} and delete_flag eq 'N'",
        "inv_mast_uid",
    )
    if not rows:
        raise SystemExit(f"Item {item_id} not found")
    return rows[0]["inv_mast_uid"]


def show_assembly(session, uid: int) -> None:
    """Print assembly_hdr and its assembly_line rows.

    Args:
        session: Session from connect().
        uid: The assembly item's inv_mast_uid.
    """
    hdr = odata(
        session,
        "assembly_hdr",
        f"inv_mast_uid eq {uid}",
        "inv_mast_uid,production_order_processing,allow_disassembly,delete_flag",
    )
    print(f"  assembly_hdr: {hdr if hdr else 'NONE'}")
    for line in odata(
        session,
        "assembly_line",
        f"inv_mast_uid eq {uid}",
        "sequence_number,component_inv_mast_uid,quantity,delete_flag",
    ):
        component = odata(
            session,
            "inv_mast",
            f"inv_mast_uid eq {line['component_inv_mast_uid']}",
            "item_id",
        )
        line["component_item_id"] = component[0]["item_id"] if component else None
        print(f"  assembly_line: {line}")


def main() -> None:
    """Entry point: dry run prints the payload; --execute checks, posts, reads back."""
    parser = argparse.ArgumentParser(
        description="Create or edit an assembly (docs/03-Transaction-API.md#assembly-service)"
    )
    sub = parser.add_subparsers(dest="mode", required=True)
    create = sub.add_parser("create")
    create.add_argument("item_id")
    create.add_argument(
        "--component",
        action="append",
        required=True,
        help="COMPONENT_ID:QTY (repeat per component)",
    )
    create.add_argument(
        "--production-order-processing", choices=["ON", "OFF"], default="OFF"
    )
    flag = sub.add_parser("set-flag")
    flag.add_argument("item_id")
    flag.add_argument("--field", default="production_order_processing")
    flag.add_argument("--value", choices=["ON", "OFF"], required=True)
    qty = sub.add_parser("set-qty")
    qty.add_argument("item_id")
    qty.add_argument("component_id")
    qty.add_argument("quantity")
    delete = sub.add_parser("delete-component")
    delete.add_argument("item_id")
    delete.add_argument("component_id")
    for p in (create, flag, qty, delete):
        p.add_argument(
            "--execute",
            action="store_true",
            help="Actually POST the transaction (default: dry run)",
        )
    args = parser.parse_args()

    print(f"Recipe - Assembly: {args.mode} (Assembly service)")
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
    uid = item_uid(session, args.item_id)

    if args.mode == "create":
        if odata(session, "assembly_hdr", f"inv_mast_uid eq {uid}", "inv_mast_uid"):
            raise SystemExit(
                f"{args.item_id} already has an assembly -- edit it instead"
            )
        used_in = odata(
            session,
            "assembly_line",
            f"component_inv_mast_uid eq {uid} and delete_flag eq 'N'",
            "inv_mast_uid",
        )
        if used_in:
            raise SystemExit(
                f"{args.item_id} is a component of {len(used_in)} assembly(ies): "
                "the Transaction API cannot answer the popup -- use the "
                "Interactive Assembly window"
            )
    else:
        print("\nBefore:")
        show_assembly(session, uid)

    print()
    post_transaction(session, payload)
    print("\nAfter (OData read-back):")
    show_assembly(session, uid)


if __name__ == "__main__":
    main()
