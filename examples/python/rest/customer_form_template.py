"""
Other REST Families - Customer Form Template Create/Update
(accounting/customerformtemplates)

Sets which report template a customer's invoice/RMA/packing-list/
statement prints use. PUT is the only write verb -- there is no POST on
this family -- but PUT is NOT a blind upsert: a null CustomerFormTemplateUid
means create, and create fails "data already exists" if that customer
already has a row. There is also no keyed GET on this REST family itself
(only the bare, unbounded list) -- so this script checks for an existing
row over OData instead, on the underlying customer_form_template table,
rather than pulling the whole unbounded list to filter client-side.
Dry run by default; --execute actually posts.

Mirrors: docs/15-Other-REST-Families.md#accountingcustomerformtemplates
(see the "PUT is not a blind upsert" correction there -- this script's
read-first approach exists specifically because of that finding.)

Usage:
    python examples/python/rest/customer_form_template.py             # dry run
    python examples/python/rest/customer_form_template.py --execute
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from common.auth import get_token, get_auth_headers
from common.config import load_config

import warnings
warnings.filterwarnings("ignore")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Upsert a customer form template (docs/15 accounting/customerformtemplates)"
    )
    parser.add_argument("--execute", action="store_true", help="Actually PUT (default: dry run)")
    parser.add_argument("--customer-id", type=int, default=12066)
    parser.add_argument("--company-id", default="ACME")
    parser.add_argument("--invoice-filename", default="ZZTEST.rpt")
    args = parser.parse_args()

    print("Other REST Families - Customer Form Template (customerformtemplates)")
    print("=" * 60)

    config = load_config()
    token_data = get_token(config)
    headers = get_auth_headers(token_data["AccessToken"])
    print(f"Server: {config.base_url}")

    # No keyed GET exists on this REST family -- check OData for an
    # existing row instead of pulling the unbounded list.
    existing = httpx.get(
        f"{config.base_url}/odataservice/odata/table/customer_form_template",
        params={"$select": "customer_form_template_uid",
                "$filter": f"customer_id eq {args.customer_id} and company_id eq '{args.company_id}'"},
        headers=headers, verify=config.verify_ssl, timeout=30.0,
    ).json()["value"]
    existing_uid = existing[0]["customer_form_template_uid"] if existing else None
    action = "UPDATE (row exists)" if existing_uid else "CREATE (no row yet)"
    print(f"\nExisting row check: {action}")

    template = httpx.get(f"{config.base_url}/api/accounting/customerformtemplates/new",
                         headers=headers, verify=config.verify_ssl, timeout=30.0).json()
    template.update({"CustomerFormTemplateUid": existing_uid, "CustomerId": args.customer_id,
                     "CompanyId": args.company_id, "InvoiceFilename": args.invoice_filename})

    if not args.execute:
        print("\nDRY RUN - payload that would be PUT to /api/accounting/customerformtemplates/:")
        print(json.dumps(template, indent=2))
        print(f"\nRe-run with --execute to actually {action.split()[0].lower()} it. "
              "There is no POST on this family, and PUT with a null "
              "CustomerFormTemplateUid against a customer that already has a row FAILS "
              "rather than updating it -- see docs/15's correction.")
        return

    r = httpx.put(f"{config.base_url}/api/accounting/customerformtemplates/",
                  headers=headers, json=template, verify=config.verify_ssl, timeout=60.0)
    r.raise_for_status()
    result = r.json()
    print(f"\nCustomerFormTemplateUid={result['CustomerFormTemplateUid']}  "
          f"InvoiceFilename={result['InvoiceFilename']!r}")


if __name__ == "__main__":
    main()
