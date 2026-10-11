"""
Attach a Ship-To to a Contract, and Update a Line by line_no (JobContractPricing)

Two modes against an existing job contract. Both identify the header the same
way: FORM.d_dw_job_price_hdr with Keys [] and job_no + contract_no in Edits --
and nothing else. Leaving end_date out means the header is not re-saved (its
date_last_modified stays put) and its date validations do not run, so an
expired contract can be edited too.

    attach-ship-to  add a CUSTOMER_SHIP_TO.customer_ship_to row keyed on
                    customer_id + ship_to_id. Contract pricing follows this
                    grid: an order gets the contract price only when its
                    customer AND ship-to are a row here.
    update-line     select a JOBPRICELINE row by line_no (Keys ["line_no"],
                    line_no in Edits) and change its fields. Use this when the
                    contract carries the same item_id on two lines -- keyed by
                    item_id, the write silently lands on the first of them.
                    With --commission-cost, a JOBPRICECOST row follows; it has
                    no line_no key and binds to the line JOBPRICELINE selected.
                    Commission cost needs IgnoreDisabled at the top level.

The script reads the header, the ship-to grid, and the lines over OData
before and after, so you can see that only the targeted line changed and that
the header was not re-saved.

Mirrors: docs/03-Transaction-API.md#attaching-a-ship-to-to-an-existing-contract
         docs/03-Transaction-API.md#updating-an-existing-contract

Usage:
    python examples/python/recipes/contract_shipto_line_no.py attach-ship-to \\
        --job-no 31 --contract-no JOB-1001 --customer-id 100198 --ship-to-id 100199 --execute
    python examples/python/recipes/contract_shipto_line_no.py update-line \\
        --job-no 31 --contract-no JOB-1001 --line-no 2 --set qty_maximum=50 \\
        --commission-cost 7.50 --execute
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from common.tapi import connect, edit, odata, odata_quote, post_transaction

import warnings
warnings.filterwarnings("ignore")

# --- Configuration (generic placeholders -- substitute your own) ------------
JOB_NO = "1001"               # unique per header; survives renewals
CONTRACT_NO = "JOB-1001"

LINE_COLUMNS = ("line_no,inv_mast_uid,price,qty_maximum,"
                "commission_cost_type_cd,commission_cost_value,date_last_modified")


def header_element(job_no: str, contract_no: str) -> dict:
    """Identify the contract by job_no + contract_no only -- no end_date.

    Args:
        job_no: The header's job_no.
        contract_no: The header's contract_no.

    Returns:
        dict: The FORM.d_dw_job_price_hdr DataElement.
    """
    return {"Name": "FORM.d_dw_job_price_hdr", "Type": "Form", "Keys": [],
            "Rows": [{"Edits": [edit("job_no", job_no), edit("contract_no", contract_no)],
                      "RelativeDateEdits": []}]}


def build_payload(args: argparse.Namespace, line_item_id: str | None = None) -> dict:
    """Build the JobContractPricing payload for the chosen mode.

    Args:
        args: Parsed command-line options.
        line_item_id: The item on the selected line (for the commission-cost
            element); a placeholder in a dry run.

    Returns:
        dict: Complete Transaction API payload.
    """
    elements = [header_element(args.job_no, args.contract_no)]
    payload = {"Name": "JobContractPricing", "UseCodeValues": False,
               "Transactions": [{"Status": "New", "DataElements": elements}]}

    if args.mode == "attach-ship-to":
        elements.append({
            "Name": "CUSTOMER_SHIP_TO.customer_ship_to", "Type": "List",
            "Keys": ["customer_id", "ship_to_id"],
            "Rows": [{"Edits": [edit("customer_id", args.customer_id),
                                edit("ship_to_id", args.ship_to_id)],
                      "RelativeDateEdits": []}],
        })
        return payload

    line_edits = [edit("line_no", args.line_no)]
    for pair in args.set or []:
        name, _, value = pair.partition("=")
        line_edits.append(edit(name, value))
    elements.append({"Name": "JOBPRICELINE.jobpriceline", "Type": "List",
                     "Keys": ["line_no"],
                     "Rows": [{"Edits": line_edits, "RelativeDateEdits": []}]})
    if args.commission_cost is not None:
        payload["IgnoreDisabled"] = True   # top level -- required for commission cost
        elements.append({
            "Name": "JOBPRICECOST.jobpricecost", "Type": "Form", "Keys": ["item_id"],
            "Rows": [{"Edits": [
                edit("item_id", line_item_id or "ITEM-001"),
                edit("commission_cost_type_cd", "Value"),          # type before value
                edit("commission_cost_value", args.commission_cost),
            ]}],
        })
    return payload


def snapshot(session, job_no: str, contract_no: str) -> dict:
    """Read the contract header, ship-to grid, and lines.

    Args:
        session: Session from connect().
        job_no: The header's job_no.
        contract_no: The header's contract_no.

    Returns:
        dict: {"header": row, "ship_tos": [...], "lines": {line_no: row}}.
    """
    headers = odata(session, "job_price_hdr",
                    f"job_no eq {odata_quote(job_no)} and "
                    f"contract_no eq {odata_quote(contract_no)}",
                    "job_price_hdr_uid,job_no,contract_no,end_date,date_last_modified")
    if not headers:
        raise SystemExit(f"Contract {contract_no} / job {job_no} not found")
    uid = headers[0]["job_price_hdr_uid"]
    ship_tos = odata(session, "job_price_customer_shipto", f"job_price_hdr_uid eq {uid}",
                     "customer_id,ship_to_id,row_status_flag")
    lines = odata(session, "job_price_line", f"job_price_hdr_uid eq {uid}", LINE_COLUMNS)
    return {"header": headers[0], "ship_tos": ship_tos,
            "lines": {row["line_no"]: row for row in lines}}


def show(label: str, snap: dict) -> None:
    """Print a snapshot.

    Args:
        label: Heading.
        snap: Result of snapshot().
    """
    print(f"\n{label}")
    print(f"  header: {snap['header']}")
    for row in snap["ship_tos"]:
        print(f"  ship-to: {row}")
    for line_no in sorted(snap["lines"]):
        print(f"  line: {snap['lines'][line_no]}")


def main() -> None:
    """Entry point: dry run prints the payload; --execute posts and compares."""
    parser = argparse.ArgumentParser(
        description="Attach a ship-to or update a line by line_no on a job contract")
    parser.add_argument("mode", choices=["attach-ship-to", "update-line"])
    parser.add_argument("--job-no", default=JOB_NO)
    parser.add_argument("--contract-no", default=CONTRACT_NO)
    parser.add_argument("--customer-id", default="100198")
    parser.add_argument("--ship-to-id", default="100199")
    parser.add_argument("--line-no", default="2")
    parser.add_argument("--set", action="append", metavar="FIELD=VALUE",
                        help="JOBPRICELINE field to change (repeatable)")
    parser.add_argument("--commission-cost", default=None,
                        help="Also set a Value commission cost on the selected line")
    parser.add_argument("--execute", action="store_true",
                        help="Actually POST the transaction (default: dry run)")
    args = parser.parse_args()

    print(f"Recipe - Contract: {args.mode} (JobContractPricing)")
    print("=" * 60)
    if not args.execute:
        print("\nDRY RUN - payload that would be POSTed to {ui_server}/api/v2/transaction:")
        print(json.dumps(build_payload(args), indent=2))
        print("\nRe-run with --execute to POST it.")
        return

    session = connect()
    print(f"UI Server: {session.ui_server}")
    before = snapshot(session, args.job_no, args.contract_no)
    show("Before:", before)

    line_item_id = None
    if args.mode == "update-line":
        line = before["lines"].get(int(args.line_no))
        if not line:
            raise SystemExit(f"Line {args.line_no} not found on the contract")
        line_item_id = odata(session, "inv_mast", f"inv_mast_uid eq {line['inv_mast_uid']}",
                             "item_id")[0]["item_id"]

    payload = build_payload(args, line_item_id)
    print()
    post_transaction(session, payload)

    after = snapshot(session, args.job_no, args.contract_no)
    show("After (OData read-back):", after)
    resaved = after["header"]["date_last_modified"] != before["header"]["date_last_modified"]
    print(f"\nHeader re-saved: {'YES' if resaved else 'no'}")
    if args.mode == "attach-ship-to":
        landed = any(str(r["customer_id"]) == args.customer_id and
                     str(r["ship_to_id"]) == args.ship_to_id for r in after["ship_tos"])
        print(f"Ship-to on the contract: {'OK' if landed else 'MISSING'}")
    else:
        changed = [n for n in after["lines"] if after["lines"][n] != before["lines"].get(n)]
        print(f"Lines changed: {changed}  (expected only [{args.line_no}])")


if __name__ == "__main__":
    main()
