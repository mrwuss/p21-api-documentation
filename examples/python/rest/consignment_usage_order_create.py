"""
Other REST Families - Create a Consignment Usage Order
(sales/consignmentusageorders)

Attempts a create and surfaces the real blocker: a CUO bills against an
existing consignment contract, and this family's error names the field
plainly -- "Contract ID is required." -- once you know to read the
<ImportReturn> XML wrapper. No consignment_contract-named OData object
was found on the verification tenant; P21's consignment pricing lives
inside the JobContractPricing family under a different name (see
docs/03), and whether one of those contract numbers satisfies this
family's ContractId is unresolved.

Mirrors: docs/15-Other-REST-Families.md#salesconsignmentusageorders

Usage:
    python examples/python/rest/consignment_usage_order_create.py                     # dry run
    python examples/python/rest/consignment_usage_order_create.py --execute
    python examples/python/rest/consignment_usage_order_create.py --execute \\
        --contract-id 12345   # once you have found a real one
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
        description="Create a consignment usage order (docs/15 sales/consignmentusageorders)"
    )
    parser.add_argument("--execute", action="store_true", help="Actually POST (default: dry run)")
    parser.add_argument("--customer-id", type=int, default=12066)
    parser.add_argument("--company-id", default="ACME")
    parser.add_argument("--location-id", type=int, default=40)
    parser.add_argument("--contract-id", default=None,
                        help="Not set by default -- the create fails with 'Contract ID is "
                             "required.' either way until you supply one from a real "
                             "consignment contract on your tenant")
    args = parser.parse_args()

    print("Other REST Families - CUO Create (sales/consignmentusageorders)")
    print("=" * 60)

    config = load_config()
    token_data = get_token(config)
    headers = get_auth_headers(token_data["AccessToken"])
    print(f"Server: {config.base_url}")

    cuo = httpx.get(f"{config.base_url}/api/sales/consignmentusageorders/new",
                    headers=headers, verify=config.verify_ssl, timeout=30.0).json()
    cuo.update({"CustomerId": args.customer_id, "CompanyId": args.company_id,
               "LocationId": args.location_id, "PoNo": "ZZ-CUO-TEST",
               "OrderDate": "2026-09-12T00:00:00"})
    if args.contract_id:
        cuo["ContractId"] = args.contract_id

    if not args.execute:
        print("\nDRY RUN - payload that would be POSTed to /api/sales/consignmentusageorders/:")
        print(json.dumps(cuo, indent=2)[:600])
        if not args.contract_id:
            print("\nNo --contract-id given -- this WILL fail with 'Contract ID is required.'")
        print("\nRe-run with --execute to actually attempt it.")
        return

    r = httpx.post(f"{config.base_url}/api/sales/consignmentusageorders/", headers=headers,
                   json=cuo, verify=config.verify_ssl, timeout=60.0)
    print(f"\nHTTP {r.status_code}")
    print(r.text[:600])


if __name__ == "__main__":
    main()
