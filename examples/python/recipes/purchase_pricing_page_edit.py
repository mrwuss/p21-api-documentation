"""
Edit a Supplier/Item Purchase Pricing Page in Place (Transaction API)

Changes the price on an existing PurchasePricingPageSupplierItem page without
creating a second page: read the page over OData, mirror its current field
set (mapping stored codes back to window labels), change only the price, and
post with Status "New" and the page's exact key values. Then read it back and
confirm the same purchase_pricing_page_uid now carries the new price and no
duplicate page appeared.

Key rules (verified on play 26.1.5950.0, October 2026):
    - Status "Edit" is HTTP 400 (enum). "New" + exact keys edits in place.
    - effective_date is part of the match: a different effective_date
      created a SECOND page. A different expiration_date did not -- it
      re-dated the existing page. Send both exactly as stored.
    - The table stores PRICE / ITEM / MULTIPLIER; the service wants the
      window labels Price / Item / Multiplier. Map before sending.
    - Mirror the full field set. A keys-plus-price edit also succeeded on
      this build, but the window re-validates required fields on save
      (totaling_basis is required) and other builds have refused it.

Mirrors: docs/08-SalesPricePage-Codes.md#editing-a-supplieritem-purchase-page-purchasepricingpagesupplieritem

Usage:
    python examples/python/recipes/purchase_pricing_page_edit.py              # dry run (reads, prints)
    python examples/python/recipes/purchase_pricing_page_edit.py --execute \\
        --book-id PB-2026 --supplier-id 100 --item-id ITEM-001 \\
        --effective 2030-01-01 --expiration 2030-12-31 --price 4.75
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

KEYS = ["company_id", "purchase_pricing_book_id", "supplier_id", "inv_mast_item_id",
        "effective_date", "expiration_date"]

# Stored code -> window label. Anything not listed is sent as stored.
LABELS = {
    "pricing_method": {"PRICE": "Price", "SOURCE": "Source", "NONE": "None"},
    "totaling_method": {"ITEM": "Item", "SUPPLIER": "Supplier", "ORDER": "Order",
                        "DISCOUNT GROUP": "Discount Group", "PRODUCT GROUP": "Product Group",
                        "MAJOR GROUP": "Major Group"},
    "calculation_type": {"MULTIPLIER": "Multiplier", "FIXED": "Fixed Price",
                         "DIFFERENCE": "Difference", "MARKUP": "Mark up",
                         "PERCENTAGE": "Percentage"},
}


def label(field: str, stored: str) -> str:
    """Map a stored value to the label the service accepts."""
    return LABELS.get(field, {}).get(str(stored).upper(), str(stored))


def num(value) -> str:
    """Format a number for an Edit value without float noise."""
    return f"{float(value):g}"


def odata(base_url: str, headers: dict, verify: bool, table: str, flt: str) -> list[dict]:
    """Return the rows of an OData table query."""
    resp = httpx.get(f"{base_url}/odataservice/odata/table/{table}",
                     params={"$filter": flt}, headers=headers, verify=verify,
                     follow_redirects=True, timeout=60)
    resp.raise_for_status()
    return resp.json()["value"]


def find_pages(base_url: str, headers: dict, verify: bool, args: argparse.Namespace) -> list[dict]:
    """Live (delete_flag N) pages matching all six keys.

    Dates are compared on their date part; OData returns them with a time zone.
    """
    item = odata(base_url, headers, verify, "inv_mast", f"item_id eq '{args.item_id}'")
    if not item:
        raise SystemExit(f"Item {args.item_id} not found")
    rows = odata(base_url, headers, verify, "purchase_pricing_page",
                 f"company_id eq '{args.company}' and pricing_book_id eq '{args.book_id}' "
                 f"and supplier_id eq {args.supplier_id} "
                 f"and inv_mast_uid eq {item[0]['inv_mast_uid']} and delete_flag eq 'N'")
    return [r for r in rows
            if r["effective_date"][:10] == args.effective
            and r["expiration_date"][:10] == args.expiration]


def edit_payload(page: dict, args: argparse.Namespace) -> dict:
    """Mirror the page's current fields, with the new price.

    Args:
        page: The purchase_pricing_page row read over OData.
        args: Parsed CLI arguments (keys + new price).

    Returns:
        dict: Transaction API payload.
    """
    def e(name: str, value) -> dict:
        return {"Name": name, "Value": str(value)}

    header = [
        e("company_id", args.company),
        e("purchase_pricing_book_id", args.book_id),
        e("supplier_id", args.supplier_id),
        e("inv_mast_item_id", args.item_id),
        e("effective_date", args.effective),
        e("expiration_date", args.expiration),
    ]
    if page.get("location_id"):
        header.append(e("location_id", page["location_id"]))
    for field in ("pricing_description", "contract_number"):
        if page.get(field):
            header.append(e(field, page[field]))
    header.append(e("pricing_method", label("pricing_method", page["pricing_method"])))
    if page.get("source_price"):
        header.append(e("source_price", page["source_price"]))
    if str(page["pricing_method"]).upper() == "PRICE":
        header.append(e("price", args.price))                # the one real change
    header.append(e("totaling_method", label("totaling_method", page["totaling_method"])))
    header.append(e("totaling_basis", page["totaling_basis"]))  # required on every save
    if page.get("major_group_id"):
        header.append(e("major_group_id", page["major_group_id"]))

    values = [e("calculation_type", label("calculation_type", page["calculation_type"]))]
    last = max([n for n in range(1, 16) if page.get(f"calculation_value{n}")] or [1])
    for n in range(1, last + 1):
        values.append(e(f"value{n}", num(page.get(f"calculation_value{n}") or 0)))
        if n < last:
            values.append(e(f"break{n}", num(page.get(f"break{n}") or 0)))

    return {
        "Name": "PurchasePricingPageSupplierItem",
        "UseCodeValues": False,
        "Transactions": [{
            "Status": "New",  # "Edit" is not a valid status -- exact keys make this an edit
            "DataElements": [
                {"Name": "TABPAGE_1.tp_1_dw_1", "Type": "Form", "Keys": KEYS,
                 "Rows": [{"Edits": header, "RelativeDateEdits": []}]},
                {"Name": "TABPAGE_2.tp_2_dw_2", "Type": "Form", "Keys": [],
                 "Rows": [{"Edits": values, "RelativeDateEdits": []}]},
            ],
        }],
    }


def main() -> None:
    """Entry point: read the page, build the edit, POST on --execute, verify."""
    p = argparse.ArgumentParser(description="Edit a supplier/item purchase pricing page in place")
    p.add_argument("--execute", action="store_true", help="POST (default: dry run)")
    p.add_argument("--company", default="ACME")
    p.add_argument("--book-id", default="PB-2026", help="purchase_pricing_book_id")
    p.add_argument("--supplier-id", default="100")
    p.add_argument("--item-id", default="ITEM-001")
    p.add_argument("--effective", default="2030-01-01", help="Exactly as stored (YYYY-MM-DD)")
    p.add_argument("--expiration", default="2030-12-31", help="Exactly as stored (YYYY-MM-DD)")
    p.add_argument("--price", default="4.75", help="New price")
    args = p.parse_args()

    print("Edit a Purchase Pricing Page in place (PurchasePricingPageSupplierItem)")
    print("=" * 60)

    config = load_config()
    token = get_token(config)["AccessToken"]
    headers = get_auth_headers(token)
    verify = config.verify_ssl

    pages = find_pages(config.base_url, headers, verify, args)
    if len(pages) != 1:
        raise SystemExit(f"Expected exactly one live page for these keys, found {len(pages)}")
    page = pages[0]
    uid = page["purchase_pricing_page_uid"]
    print(f"\nCurrent page {uid}: pricing_method={page['pricing_method']} "
          f"price={page.get('price')} calculation_type={page['calculation_type']} "
          f"totaling_basis={page['totaling_basis']}")

    payload = edit_payload(page, args)
    print("\nPayload for POST {ui_server}/api/v2/transaction:")
    print(json.dumps(payload, indent=2))
    if not args.execute:
        print("\nDRY RUN - nothing posted. Re-run with --execute.")
        return

    ui_server = get_ui_server_url(config.base_url, token, verify)
    resp = httpx.post(f"{ui_server}/api/v2/transaction", headers=headers, json=payload,
                      verify=verify, follow_redirects=True, timeout=120)
    resp.raise_for_status()
    result = resp.json()
    print(f"\nSummary: {result['Summary']}  Messages: {result.get('Messages')}")
    if result["Summary"]["Failed"] or not result["Summary"]["Succeeded"]:
        raise SystemExit("Edit failed")

    after = find_pages(config.base_url, headers, verify, args)
    same = [r for r in after if r["purchase_pricing_page_uid"] == uid]
    print("\nVerify (OData read-back):")
    print(f"  live pages for these keys: {len(after)} -> {'OK' if len(after) == 1 else 'DUPLICATE'}")
    if same:
        ok = abs(float(same[0]["price"]) - float(args.price)) < 1e-9
        print(f"  page {uid}: price={same[0]['price']} expected={args.price} -> "
              f"{'OK' if ok else 'MISMATCH'}")
    else:
        print(f"  page {uid} no longer matches the keys -> CHECK")


if __name__ == "__main__":
    main()
