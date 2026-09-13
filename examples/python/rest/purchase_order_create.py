"""
Other REST Families - Create a Purchase Order (purchasing/purchaseorders)

Create a PO with one line, then read it back. Dry run by default;
--execute actually posts.

Mirrors: docs/15-Other-REST-Families.md#creating-a-po-verified

Two undocumented preconditions found live, 26.1.5950.0:
    - An empty BuyerId (its value in the /new template) fails with an
      escaped <ImportReturn> XML error naming "Invalid buyer ID" AND an
      unrelated-looking "Sales/Production/PO Intersection" complaint --
      the second is cascade noise from the first, not a separate
      requirement. Supply a real BuyerId.
    - UnitPrice sent on create is NOT honored -- it is stored as 0.00
      regardless of what you send (PriceEdit: "N" routes pricing through
      lookup instead). Use the Transaction API PurchaseOrder service
      when the price must be exact -- see docs/03-Transaction-API.md.

Response shape note: POLines comes back POPULATED on this create response
(server-assigned PoLineUid, pricing-lookup fields filled in) -- the only
place this family's child collections are not null. An immediate GET on
the same PO still returns POLines: null.

Usage:
    python examples/python/rest/purchase_order_create.py                 # dry run
    python examples/python/rest/purchase_order_create.py --execute \\
        --async-create   # exercises POST .../async instead of the sync route
"""

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from common.auth import get_token, get_auth_headers
from common.config import load_config

import warnings
warnings.filterwarnings("ignore")


def get_new_template(base_url: str, headers: dict, verify_ssl: bool) -> dict:
    response = httpx.get(
        f"{base_url}/api/purchasing/purchaseorders/new",
        headers=headers, verify=verify_ssl, follow_redirects=True, timeout=30.0,
    )
    response.raise_for_status()
    return response.json()


def build_po(template: dict, args: argparse.Namespace) -> dict:
    po = dict(template)
    po.update({
        "CompanyNo": args.company_id, "LocationId": args.location_id,
        "VendorId": args.vendor_id, "SupplierId": args.vendor_id,
        "PoType": "S", "OrderDate": "2026-09-12T00:00:00", "DateDue": "2026-09-19T00:00:00",
        "Terms": "1", "CarrierId": "100",
        # BuyerId empty is the trap -- "Customer ID is required"'s PO-family
        # sibling. See the module docstring.
        "BuyerId": args.buyer_id,
        "PoDesc": "ZZ API DOC TEST - safe to delete (REST create)",
    })
    line = dict(po["POLines"]["list"][0])
    line.update({
        "ItemId": args.item_id, "UnitOfMeasure": args.uom,
        "UnitQuantity": args.quantity, "PricingUnit": args.uom,
        # Sent for completeness -- NOT honored on create. See docstring.
        "UnitPrice": args.unit_price,
    })
    po["POLines"] = {"list": [line]}
    return po


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a PO with one line (docs/15 purchasing/purchaseorders)"
    )
    parser.add_argument("--execute", action="store_true", help="Actually POST (default: dry run)")
    parser.add_argument("--async-create", action="store_true",
                        help="POST to .../async and poll for completion instead of the sync route")
    parser.add_argument("--company-id", default="ACME")
    parser.add_argument("--location-id", type=int, default=20)
    parser.add_argument("--vendor-id", type=int, default=25753)
    parser.add_argument("--buyer-id", default="812",
                        help="Required in practice -- an empty value fails create. "
                             "Find a real one via GET /api/purchasing/purchaseorders/{po_no} "
                             "on an existing PO.")
    parser.add_argument("--item-id", default="ETS-727K-G-006")
    parser.add_argument("--uom", default="EA")
    parser.add_argument("--quantity", type=float, default=1)
    parser.add_argument("--unit-price", type=float, default=5.00,
                        help="Sent but NOT honored on create -- documented as 0.00 on read-back "
                             "regardless of this value")
    args = parser.parse_args()

    print("Other REST Families - Create a Purchase Order (purchasing/purchaseorders)")
    print("=" * 60)

    config = load_config()
    token_data = get_token(config)
    headers = get_auth_headers(token_data["AccessToken"])
    print(f"Server: {config.base_url}")

    template = get_new_template(config.base_url, headers, config.verify_ssl)
    po = build_po(template, args)

    if not args.execute:
        print("\nDRY RUN - payload that would be POSTed to /api/purchasing/purchaseorders/:")
        print(json.dumps({k: v for k, v in po.items()
                          if k not in ("POSales", "POHdrNotes", "POLineNotes")}, indent=2))
        print("\nRe-run with --execute to actually create it.")
        return

    route = "async" if args.async_create else ""
    url = f"{config.base_url}/api/purchasing/purchaseorders/{route}"
    r = httpx.post(url, headers={**headers, "Content-Type": "application/json"},
                   json=po, verify=config.verify_ssl, follow_redirects=True, timeout=90.0)
    if r.status_code != 200:
        print(f"\nCreate failed: HTTP {r.status_code}\n{r.text[:800]}")
        raise SystemExit(1)

    if args.async_create:
        request_id = r.json()["RequestId"]
        print(f"\nAsync request: {request_id}, polling...")
        for _ in range(15):
            time.sleep(2)
            status = httpx.get(f"{config.base_url}/api/purchasing/purchaseorders/async",
                               params={"requestId": request_id}, headers=headers,
                               verify=config.verify_ssl, timeout=30.0).json()
            print(f"  Status={status['Status']}  Messages={status.get('Messages')}")
            if status["Status"] == 2:  # observed value for "complete"
                po_no = status["Messages"]
                break
        else:
            raise SystemExit("Async create did not complete in time")
    else:
        created = r.json()
        po_no = created["PoNo"]
        print(f"\nCreated PO {po_no}")
        print(f"  POLines (populated on THIS response only): "
              f"{json.dumps(created['POLines']['list'][0], indent=2)[:400]}")

    print(f"\nRead-back GET /api/purchasing/purchaseorders/{po_no}:")
    print("-" * 50)
    rb = httpx.get(f"{config.base_url}/api/purchasing/purchaseorders/{po_no}",
                   headers=headers, verify=config.verify_ssl, timeout=30.0).json()
    print(f"  PoNo={rb['PoNo']}  POLines={rb['POLines']!r}  (always null on GET)")


if __name__ == "__main__":
    main()
