"""
Merge One Item or Customer into Another (m_itemmerge / m_customermerge)

Item Merge and Customer Merge run through POST /api/v2/transaction as the
hidden menu services m_itemmerge and m_customermerge (neither is listed in
/api/v2/services). A merge is ONE-WAY: the source is soft-deleted and its
history is moved, rewritten, or deleted. Run it on a test tenant first, on
records you can afford to lose.

    item      FORM.form keyed on source_item_id + target_item_id. The source
              is merged INTO the target; the target survives.
    customer  FORM.form keyed on source_customer_id + target_customer_id.

Guards, before anything is posted:

  * Both IDs are resolved exactly against live records (delete_flag = 'N')
    and must differ. With create_alt_code_flag = ON a merged item ID becomes
    an alternate code on the target, and both ID fields resolve alternate
    codes -- a request that names an already-merged item silently acts on
    whichever live item now holds that code.
  * An item that has an assembly (bill of materials) is refused by P21.

Deciding success:

  * Item merge: Summary reports Succeeded 1. The script still reads back the
    source (delete_flag 'Y', the "Item Merged" description) and
    item_merge_audit.
  * Customer merge: every successful call reports Failed 1 with
    "History is not available for w_customer_merge_maint window" -- and is
    committed. Success comes from customer_merge_audit ("Merge was
    Successful.") and the source customer's delete_flag, never from the
    Summary. Do not retry: the source is already merged, so a retry fails
    "Invalid customer ID."

Mirrors: docs/03-Transaction-API.md#item-merge-and-customer-merge-m_itemmerge-m_customermerge

Usage:
    python examples/python/recipes/item_customer_merge.py item ITEM-002 ITEM-001            # dry run
    python examples/python/recipes/item_customer_merge.py item ITEM-002 ITEM-001 --execute
    python examples/python/recipes/item_customer_merge.py customer CUST-101 CUST-100 \\
        --company ACME --execute
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
COMPANY_ID = "ACME"
CREDIT_LIMIT_TYPES = ["Use Highest Credit Limit", "Keep the Target Customer Credit Limit"]


def build_payload(args: argparse.Namespace) -> dict:
    """Build the merge payload.

    Args:
        args: Parsed command-line options.

    Returns:
        dict: Complete Transaction API payload.
    """
    if args.mode == "item":
        service = "m_itemmerge"
        keys = ["source_item_id", "target_item_id"]
        edits = [
            edit("source_item_id", args.source),
            edit("target_item_id", args.target),     # omitted = silent no-op success
            edit("create_alt_code_flag", args.create_alt_code),
            edit("keep_restrictions_flag", "OFF"),
            edit("schedule_merge_flag", "OFF"),      # ON needs the Item Merge Schedule task
        ]
    else:
        service = "m_customermerge"
        keys = ["source_customer_id", "target_customer_id"]
        edits = [
            edit("company_id", args.company),
            edit("source_customer_id", args.source),
            edit("target_customer_id", args.target),
            edit("credit_limit_type", args.credit_limit_type),
            edit("keep_cust_as_shipto", args.keep_cust_as_shipto),
        ]
    return {"Name": service, "UseCodeValues": False,
            "Transactions": [{"Status": "New", "DataElements": [{
                "Name": "FORM.form", "Type": "Form", "Keys": keys,
                "Rows": [{"Edits": edits}]}]}]}


def resolve_items(session, source: str, target: str) -> tuple[int, int]:
    """Resolve both item IDs exactly to live inv_mast_uids.

    Args:
        session: Session from connect().
        source: Source item ID (merged away).
        target: Target item ID (survives).

    Returns:
        tuple[int, int]: (source uid, target uid).
    """
    uids = []
    for item_id in (source, target):
        rows = odata(session, "inv_mast",
                     f"item_id eq {odata_quote(item_id)} and delete_flag eq 'N'",
                     "inv_mast_uid,item_id")
        # Exact match only: the merge fields also resolve alternate codes.
        rows = [r for r in rows if r["item_id"] == item_id]
        if not rows:
            raise SystemExit(f"{item_id} is not a live item ID -- not posting")
        uids.append(rows[0]["inv_mast_uid"])
    if uids[0] == uids[1]:
        raise SystemExit("Source and target are the same item")
    return uids[0], uids[1]


def resolve_customers(session, source: str, target: str) -> None:
    """Confirm both customers exist and are live.

    Args:
        session: Session from connect().
        source: Source customer ID (merged away).
        target: Target customer ID (survives).
    """
    if source == target:
        raise SystemExit("Source and target are the same customer")
    for customer_id in (source, target):
        rows = odata(session, "customer",
                     f"customer_id eq {customer_id} and delete_flag eq 'N'",
                     "customer_id,customer_name")
        if not rows:
            raise SystemExit(f"{customer_id} is not a live customer -- not posting")


def main() -> None:
    """Entry point: dry run prints the payload; --execute guards, merges, reads back."""
    parser = argparse.ArgumentParser(
        description="Merge an item or a customer (one-way; test tenant first)")
    parser.add_argument("mode", choices=["item", "customer"])
    parser.add_argument("source", help="ID merged away (soft-deleted)")
    parser.add_argument("target", help="ID that survives")
    parser.add_argument("--company", default=COMPANY_ID)
    parser.add_argument("--create-alt-code", choices=["ON", "OFF"], default="ON")
    parser.add_argument("--credit-limit-type", choices=CREDIT_LIMIT_TYPES,
                        default=CREDIT_LIMIT_TYPES[0])
    parser.add_argument("--keep-cust-as-shipto", choices=["ON", "OFF"], default="ON")
    parser.add_argument("--execute", action="store_true",
                        help="Actually POST the merge (default: dry run)")
    args = parser.parse_args()

    print(f"Recipe - {args.mode.title()} merge: {args.source} INTO {args.target}")
    print("=" * 60)
    payload = build_payload(args)
    if not args.execute:
        print("\nDRY RUN - payload that would be POSTed to {ui_server}/api/v2/transaction:")
        print(json.dumps(payload, indent=2))
        print("\nRe-run with --execute to POST it. A merge cannot be undone.")
        return

    session = connect()
    print(f"UI Server: {session.ui_server}\n")

    if args.mode == "item":
        source_uid, target_uid = resolve_items(session, args.source, args.target)
        post_transaction(session, payload)
        checks = [
            ("source inv_mast", "inv_mast", f"inv_mast_uid eq {source_uid}",
             "item_id,delete_flag,item_desc,extended_desc"),
            ("target inv_mast", "inv_mast", f"inv_mast_uid eq {target_uid}",
             "item_id,delete_flag"),
            ("item_merge_audit", "item_merge_audit", f"source_inv_mast_uid eq {source_uid}",
             "item_merge_run,source_item_id,target_item_id,processed_flag,message"),
        ]
        if args.create_alt_code == "ON":
            checks.append(("alternate_code on target", "alternate_code",
                           f"inv_mast_uid eq {target_uid} and "
                           f"alternate_code eq {odata_quote(args.source)}",
                           "alternate_code,delete_flag"))
        print("\nVerify (OData read-back):")
        for label, table, filter_expr, select in checks:
            print(f"  {label}: {odata(session, table, filter_expr, select)}")
        return

    resolve_customers(session, args.source, args.target)
    post_transaction(session, payload)
    print("  (A successful customer merge reports Failed: 1 -- the read-back decides.)")
    audit = odata(session, "customer_merge_audit",
                  f"source_customer_id eq {args.source} and target_customer_id eq {args.target}",
                  "customer_merge_run,processed_flag,merge_message,keep_custas_shipto_flag")
    source = odata(session, "customer", f"customer_id eq {args.source}",
                   "customer_id,customer_name,delete_flag")
    print("\nVerify (OData read-back):")
    print(f"  customer_merge_audit: {audit}")
    print(f"  source customer: {source}")
    merged = (any((row.get("merge_message") or "").startswith("Merge was Successful")
                  for row in audit)
              and bool(source) and source[0]["delete_flag"] == "Y")
    print(f"\nMerge committed: {'YES' if merged else 'NO'}")


if __name__ == "__main__":
    main()
