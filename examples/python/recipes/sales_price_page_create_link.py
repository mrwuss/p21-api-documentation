"""
Create a Sales Price Page and Link It to a Price Book (Transaction API)

Creates an item-level SalesPricePage (fixed price, cost Value on the COSTS
tab) in one POST, then links it to an existing price book through the
SalesPriceBook service -- FORM.form keyed price_book_id plus a LIST.list_detail
row keyed price_page_uid. Reads both back over OData. --cleanup then unlinks
the page (row_status_flag Delete on the same list_detail row, which physically
deletes the price_page_x_book row) and soft-deletes the page.

Key rules (verified on play 26.1.5950.0, October 2026):
    - Send price_page_type_cd first, then company_id, then the key field.
    - Omit calculator_type (its stored value "B" is refused) and
      strategic_price_applies_to_cd (Column is disabled on create; it
      defaults to Core).
    - The new price_page_uid comes back as the first Edit of FORM.form in
      Results -- read it there, not from a second query.
    - Link through SalesPriceBook, never through the page's own USED BY
      element (disabled; with IgnoreDisabled it reports success and writes
      nothing).
    - Link immediately: an unlinked page is invisible to pricing.

Mirrors: docs/08-SalesPricePage-Codes.md#creating-a-page-through-the-transaction-api

Usage:
    python examples/python/recipes/sales_price_page_create_link.py              # dry run
    python examples/python/recipes/sales_price_page_create_link.py --execute \\
        --item-id ITEM-001 --book-id BOOK-001
    python examples/python/recipes/sales_price_page_create_link.py --execute --cleanup ...
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from common.auth import get_token, get_auth_headers, get_ui_server_url
from common.config import load_config

import warnings
warnings.filterwarnings("ignore")


def edit(name: str, value: str) -> dict:
    """Build one Transaction API edit."""
    return {"Name": name, "Value": value}


def page_payload(args: argparse.Namespace) -> dict:
    """SalesPricePage create: FORM.form + COSTS.costs + VALUES.values in one transaction.

    Args:
        args: Parsed CLI arguments.

    Returns:
        dict: Transaction API payload.
    """
    form = [
        edit("price_page_type_cd", "Item"),       # FIRST: the type decides which keys are valid
        edit("company_id", args.company),         # before the key field
        edit("item_id", args.item_id),
        edit("description", args.description),
        edit("effective_date", args.effective),
        edit("expiration_date", args.expiration),
        edit("contract_number", args.contract),
        edit("pricing_method_cd", "Price"),
        edit("price", args.price),
        edit("totaling_method_cd", "Item"),
        edit("totaling_basis_cd", "Sales Unit"),
        # calculator_type and strategic_price_applies_to_cd are left out on purpose.
    ]
    costs = [
        edit("other_cost_type_cd", "Value"),
        edit("other_cost_value", args.cost),
        edit("commission_cost_type_cd", "Value"),
        edit("commission_cost_value", args.cost),
    ]
    values = [
        edit("calculation_method_cd", "Multiplier"),
        edit("calculation_value1", "1"),
    ]
    return {
        "Name": "SalesPricePage",
        "UseCodeValues": False,
        "Transactions": [{
            "Status": "New",
            "DataElements": [
                {"Name": "FORM.form", "Type": "Form", "Keys": [],
                 "Rows": [{"Edits": form, "RelativeDateEdits": []}]},
                {"Name": "COSTS.costs", "Type": "Form", "Keys": [],
                 "Rows": [{"Edits": costs, "RelativeDateEdits": []}]},
                {"Name": "VALUES.values", "Type": "Form", "Keys": [],
                 "Rows": [{"Edits": values, "RelativeDateEdits": []}]},
            ],
        }],
    }


def link_payload(book_id: str, price_page_uid: str, unlink: bool = False) -> dict:
    """SalesPriceBook link (or unlink) of one page.

    Args:
        book_id: price_book_id of the book.
        price_page_uid: The page to link.
        unlink: True sends row_status_flag Delete, which removes the link row.

    Returns:
        dict: Transaction API payload.
    """
    row = [edit("price_page_uid", price_page_uid)]
    if unlink:
        row.append(edit("row_status_flag", "Delete"))
    return {
        "Name": "SalesPriceBook",
        "UseCodeValues": False,
        "Transactions": [{
            "Status": "New",
            "DataElements": [
                {"Name": "FORM.form", "Type": "Form", "Keys": ["price_book_id"],
                 "Rows": [{"Edits": [edit("price_book_id", book_id)],
                           "RelativeDateEdits": []}]},
                {"Name": "LIST.list_detail", "Type": "List", "Keys": ["price_page_uid"],
                 "Rows": [{"Edits": row, "RelativeDateEdits": []}]},
            ],
        }],
    }


def page_delete_payload(price_page_uid: str) -> dict:
    """Soft-delete a page (row_status_flag Delete, stored as 700)."""
    return {
        "Name": "SalesPricePage",
        "UseCodeValues": False,
        "Transactions": [{
            "Status": "New",
            "DataElements": [
                {"Name": "FORM.form", "Type": "Form", "Keys": ["price_page_uid"],
                 "Rows": [{"Edits": [edit("price_page_uid", price_page_uid),
                                     edit("row_status_flag", "Delete")],
                           "RelativeDateEdits": []}]},
            ],
        }],
    }


def post(ui_server: str, headers: dict, verify: bool, payload: dict) -> dict:
    """POST a transaction; raise unless Summary says it landed.

    Returns:
        dict: Parsed response body.
    """
    resp = httpx.post(f"{ui_server}/api/v2/transaction", headers=headers, json=payload,
                      verify=verify, follow_redirects=True, timeout=120)
    resp.raise_for_status()  # HTTP 200 even when the transaction failed
    result = resp.json()
    summary = result["Summary"]
    if summary["Failed"] or not summary["Succeeded"]:
        raise RuntimeError(f"{payload['Name']} failed: {result.get('Messages')}")
    return result


def new_page_uid(result: dict) -> str:
    """Read the generated price_page_uid from FORM.form in Results."""
    for txn in result["Results"]["Transactions"]:
        for element in txn["DataElements"]:
            if element["Name"] == "FORM.form":
                for e in element["Rows"][0]["Edits"]:
                    if e["Name"] == "price_page_uid" and e.get("Value"):
                        return e["Value"]
    raise RuntimeError("No price_page_uid in the create response")


def odata(base_url: str, headers: dict, verify: bool, table: str, flt: str) -> list[dict]:
    """Return the rows of an OData table query."""
    resp = httpx.get(f"{base_url}/odataservice/odata/table/{table}",
                     params={"$filter": flt}, headers=headers, verify=verify,
                     follow_redirects=True, timeout=60)
    resp.raise_for_status()
    return resp.json()["value"]


def main() -> None:
    """Entry point: dry run prints both payloads; --execute creates, links and verifies."""
    p = argparse.ArgumentParser(description="Create a sales price page and link it to a book")
    p.add_argument("--execute", action="store_true", help="POST (default: dry run)")
    p.add_argument("--cleanup", action="store_true",
                   help="After verifying, unlink the page and soft-delete it")
    p.add_argument("--company", default="ACME")
    p.add_argument("--item-id", default="ITEM-001")
    p.add_argument("--book-id", default="BOOK-001", help="Existing price_book_id")
    p.add_argument("--description", default="ITEM-001 contract price")
    p.add_argument("--contract", default="CONTRACT-1")
    p.add_argument("--price", default="12.34")
    p.add_argument("--cost", default="5.67", help="Other cost and commission cost Value")
    p.add_argument("--effective", default="2030-01-01")
    p.add_argument("--expiration", default="2030-12-31")
    args = p.parse_args()

    print("Create a Sales Price Page + link it to a Price Book (Transaction API)")
    print("=" * 60)

    if not args.execute:
        print("\nDRY RUN - 1) POST {ui_server}/api/v2/transaction:")
        print(json.dumps(page_payload(args), indent=2))
        print("\n2) then link the new price_page_uid:")
        print(json.dumps(link_payload(args.book_id, "<price_page_uid>"), indent=2))
        print("\nRe-run with --execute to create, link and verify.")
        return

    config = load_config()
    token = get_token(config)["AccessToken"]
    headers = get_auth_headers(token)
    ui_server = get_ui_server_url(config.base_url, token, config.verify_ssl)
    verify = config.verify_ssl

    book = odata(config.base_url, headers, verify, "price_book",
                 f"price_book_id eq '{args.book_id}'")
    if not book:
        raise SystemExit(f"Price book {args.book_id} not found")
    book_uid = book[0]["price_book_uid"]

    # 1. Create the page
    uid = new_page_uid(post(ui_server, headers, verify, page_payload(args)))
    print(f"\n1. Created price_page_uid {uid}")

    # 2. Link it to the book straight away
    post(ui_server, headers, verify, link_payload(args.book_id, uid))
    print(f"2. Linked to {args.book_id}")

    # 3. Verify both
    page = odata(config.base_url, headers, verify, "price_page", f"price_page_uid eq {uid}")[0]
    print(f"\n3. Verify price_page {uid}: type={page['price_page_type_cd']} "
          f"price={page['price']} pricing_method_cd={page['pricing_method_cd']} "
          f"other_cost_value={page['other_cost_value']} row_status_flag={page['row_status_flag']}")
    links = odata(config.base_url, headers, verify, "price_page_x_book",
                  f"price_page_uid eq {uid} and price_book_uid eq {book_uid}")
    print(f"   price_page_x_book rows: {len(links)} -> {'OK' if len(links) == 1 else 'MISSING'}")

    if not args.cleanup:
        print(f"\nLeft in place: page {uid}, linked to {args.book_id}.")
        return

    # 4. Unlink (physical delete of the link row), then soft-delete the page
    post(ui_server, headers, verify, link_payload(args.book_id, uid, unlink=True))
    links = odata(config.base_url, headers, verify, "price_page_x_book",
                  f"price_page_uid eq {uid}")
    print(f"\n4. Unlinked: price_page_x_book rows now {len(links)} -> "
          f"{'OK' if not links else 'STILL LINKED'}")
    post(ui_server, headers, verify, page_delete_payload(uid))
    page = odata(config.base_url, headers, verify, "price_page", f"price_page_uid eq {uid}")[0]
    print(f"   Page {uid} row_status_flag={page['row_status_flag']} (700 = Delete)")


if __name__ == "__main__":
    main()
