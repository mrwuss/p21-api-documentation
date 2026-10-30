"""
Create a Vendor and Its Supplier (Vendor service)

Create the vendor first: saving it creates the same-ID supplier, its
division, and the vendor_supplier link (primary_vendor = 'Y') for you.
Creating the supplier first is a dead end -- the Supplier service requires
"at least one valid primary vendor".

Rules the payload follows:

  * vendor = ON is required ("To add a vendor, the vendor flag must be checked").
  * Leave id out and P21 numbers the vendor from the shared address sequence;
    the new ID comes back in the result rows. A typed id is accepted only if
    that ID already exists in address; any other typed ID fails
    "Enter a valid ID or leave ID blank."
  * default_terms_id takes the terms *description* (Net 30 Days), not the ID.
  * Omit currency_id: the ID is rejected and the company currency is the default.
  * Do not send the supplier tab (TABPAGE_6.tp_6_dw_6) -- the supplier does
    not exist yet.
  * Rebate accounts are optional; send them with track_rebates = ON for a
    vendor that books supplier rebates.

After the create the script reads back address, vendor, supplier, and
vendor_supplier over OData.

Mirrors: docs/03-Transaction-API.md#vendor-service-creating-a-vendor-and-its-supplier

Usage:
    python examples/python/recipes/vendor_create.py                     # dry run
    python examples/python/recipes/vendor_create.py --name "Example Vendor" \\
        --ap-account 2222200 --execute                                  # POST + verify
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from common.tapi import connect, edit, odata, post_transaction, result_value, succeeded

import warnings

warnings.filterwarnings("ignore")

# --- Configuration (generic placeholders -- substitute your own) ------------
COMPANY_ID = "ACME"
VENDOR_NAME = "Example Vendor"
AP_ACCOUNT = "2222200"  # stored form, no dashes
TERMS = "Net 30 Days"  # the terms description, not the terms ID
ADDRESS = {
    "mail_address1": "100 Main St",
    "mail_city": "Springfield",
    "mail_state": "IL",
    "mail_postal_code": "62701",
}
REBATE_ACCOUNT = "1111100"  # used only with --track-rebates
REBATE_ALLOWANCE_ACCOUNT = "3333300"

HEADER = "TABPAGE_1.tp_1_dw_1"


def build_payload(args: argparse.Namespace) -> dict:
    """Build the Vendor create payload.

    Args:
        args: Parsed command-line options.

    Returns:
        dict: Complete Transaction API payload.
    """
    header = [edit("company_id", args.company)]
    if args.id:
        header.append(edit("id", args.id))  # must already exist in address
    header += [
        edit("vendor", "ON"),  # required for a vendor create
        edit("name", args.name),
        *(edit(field, value) for field, value in ADDRESS.items()),
        edit("ap_account_no", args.ap_account),
        edit("default_terms_id", args.terms),
    ]
    if args.track_rebates:
        header.append(edit("track_rebates", "ON"))
    elements = [
        {
            "Name": HEADER,
            "Type": "Form",
            "Keys": ["company_id", "id"],
            "Rows": [{"Edits": header, "RelativeDateEdits": []}],
        }
    ]
    if args.track_rebates:
        elements.append(
            {
                "Name": "REBATE_ACCOUNTS.d_vendor_rebate_accounts",
                "Type": "Form",
                "Keys": [],
                "Rows": [
                    {
                        "Edits": [
                            edit("rebate_account_no", args.rebate_account),
                            edit(
                                "rebate_allowance_account_no",
                                args.rebate_allowance_account,
                            ),
                        ],
                        "RelativeDateEdits": [],
                    }
                ],
            }
        )
    return {
        "Name": "Vendor",
        "UseCodeValues": False,
        "Transactions": [{"Status": "New", "DataElements": elements}],
    }


def main() -> None:
    """Entry point: dry run prints the payload; --execute creates and reads back."""
    parser = argparse.ArgumentParser(
        description="Create a vendor and its supplier "
        "(docs/03-Transaction-API.md#vendor-service-creating-a-vendor-and-its-supplier)"
    )
    parser.add_argument("--company", default=COMPANY_ID)
    parser.add_argument(
        "--id",
        default="",
        help="Existing address ID to use (default: blank, P21 assigns one)",
    )
    parser.add_argument("--name", default=VENDOR_NAME)
    parser.add_argument("--ap-account", default=AP_ACCOUNT)
    parser.add_argument("--terms", default=TERMS, help="Terms description")
    parser.add_argument("--track-rebates", action="store_true")
    parser.add_argument("--rebate-account", default=REBATE_ACCOUNT)
    parser.add_argument("--rebate-allowance-account", default=REBATE_ALLOWANCE_ACCOUNT)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually POST the transaction (default: dry run)",
    )
    args = parser.parse_args()

    print("Recipe - Create a Vendor and Its Supplier (Vendor service)")
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
    print(f"UI Server: {session.ui_server}\n")
    result = post_transaction(session, payload)
    if not succeeded(result):
        raise SystemExit("Vendor create failed")

    vendor_id = result_value(result, HEADER, "id") or args.id
    print(f"Vendor ID: {vendor_id}")

    # The vendor save also wrote the supplier and the link -- confirm all four.
    print("\nVerify (OData read-back):")
    checks = [
        ("address", f"id eq {vendor_id}", "id,name,delete_flag"),
        (
            "vendor",
            f"vendor_id eq {vendor_id}",
            "vendor_id,ap_account_no,default_terms_id,track_rebates,"
            "rebate_account_no,rebate_allowance_account_no,delete_flag",
        ),
        (
            "supplier",
            f"supplier_id eq {vendor_id}",
            "supplier_id,supplier_name,delete_flag",
        ),
        (
            "vendor_supplier",
            f"vendor_id eq {vendor_id}",
            "vendor_id,supplier_id,primary_vendor,delete_flag",
        ),
    ]
    missing = 0
    for table, filter_expr, select in checks:
        rows = odata(session, table, filter_expr, select)
        missing += not rows
        print(f"  {table}: {rows if rows else 'MISSING'}")
    if missing:
        raise SystemExit(f"{missing} expected row(s) missing")


if __name__ == "__main__":
    main()
