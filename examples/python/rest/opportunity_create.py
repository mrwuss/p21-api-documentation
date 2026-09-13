"""
Other REST Families - Create a CRM Opportunity (sales/opportunities)

Checks the tenant's CRM lookup tables before attempting a create -- on
the play tenant used to verify this repo, every one of them (
opportunity_status, opportunity_stage, opportunity_type, opportunity_step)
is empty, which makes a successful create impossible regardless of
payload. This script surfaces that precondition instead of failing with
a confusing "Required value missing for Opportunity Status Uid" or
"Accessing the user ID default information has failed." the way a blind
attempt does.

Mirrors: docs/15-Other-REST-Families.md#salesopportunities

Usage:
    python examples/python/rest/opportunity_create.py                 # checks preconditions, dry run
    python examples/python/rest/opportunity_create.py --execute       # also attempts the create
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

LOOKUP_TABLES = ("opportunity_status", "opportunity_stage", "opportunity_type", "opportunity_step")


def check_lookup_tables(base_url: str, headers: dict, verify_ssl: bool) -> bool:
    """Print each CRM lookup table's row count. Returns True if all are non-empty."""
    all_populated = True
    for table in LOOKUP_TABLES:
        r = httpx.get(f"{base_url}/odataservice/odata/table/{table}",
                      params={"$top": "1", "$count": "true"},
                      headers=headers, verify=verify_ssl, timeout=30.0)
        count = r.json().get("@odata.count", "?") if r.status_code == 200 else f"HTTP {r.status_code}"
        print(f"  {table:22} {count}")
        if r.status_code != 200 or r.json().get("@odata.count", 0) == 0:
            all_populated = False
    return all_populated


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a CRM opportunity (docs/15 sales/opportunities)"
    )
    parser.add_argument("--execute", action="store_true",
                        help="Also attempt the create (default: only check preconditions)")
    parser.add_argument("--customer-id", type=int, default=12066)
    parser.add_argument("--company-id", default="ACME")
    parser.add_argument("--location-id", type=int, default=40)
    args = parser.parse_args()

    print("Other REST Families - Opportunity Create (sales/opportunities)")
    print("=" * 60)

    config = load_config()
    token_data = get_token(config)
    headers = get_auth_headers(token_data["AccessToken"])
    print(f"Server: {config.base_url}")

    print("\nCRM lookup table row counts (all must be non-zero for a create to succeed):")
    print("-" * 50)
    ready = check_lookup_tables(config.base_url, headers, config.verify_ssl)

    if not ready:
        print("\nAt least one CRM lookup table is empty on this tenant -- a create cannot "
              "succeed regardless of payload. This is a tenant configuration gap, not an "
              "API defect. See docs/15's sales/opportunities section.")
        if not args.execute:
            return
        print("\n--execute given anyway -- attempting the create to show the real error:")

    opp = httpx.get(f"{config.base_url}/api/sales/opportunities/new",
                    headers=headers, verify=config.verify_ssl, timeout=30.0).json()
    opp.update({"OpportunityName": "ZZ API DOC TEST - safe to delete",
               "CompanyId": args.company_id, "CustomerId": args.customer_id,
               "LocationId": args.location_id})

    if not args.execute:
        print("\nDRY RUN - payload that would be POSTed to /api/sales/opportunities/:")
        print(json.dumps(opp, indent=2)[:600])
        print("\nRe-run with --execute to actually attempt it.")
        return

    r = httpx.post(f"{config.base_url}/api/sales/opportunities/", headers=headers,
                   json=opp, verify=config.verify_ssl, timeout=60.0)
    print(f"\nHTTP {r.status_code}")
    print(r.text[:500])


if __name__ == "__main__":
    main()
