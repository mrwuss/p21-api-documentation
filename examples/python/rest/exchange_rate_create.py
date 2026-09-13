"""
Other REST Families - Create an Exchange Rate (accounting/exchangerates)

Checks how many currencies the tenant has configured before attempting a
create -- the verification tenant has exactly one (currency_id 1, U.S.
Dollars), which makes a genuine cross-currency rate impossible to create
regardless of payload. The one validation this tenant COULD exercise is
real: sending the same currency on both sides is refused cleanly with
"The currencies cannot be the same."

Mirrors: docs/15-Other-REST-Families.md#accountingexchangerates

Usage:
    python examples/python/rest/exchange_rate_create.py                          # checks + dry run
    python examples/python/rest/exchange_rate_create.py --execute --to-currency-id 1
    python examples/python/rest/exchange_rate_create.py --execute --to-currency-id 2 --rate 1.35
"""

import argparse
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
        description="Create an exchange rate (docs/15 accounting/exchangerates)"
    )
    parser.add_argument("--execute", action="store_true", help="Actually POST (default: dry run)")
    parser.add_argument("--currency-id", type=int, default=1)
    parser.add_argument("--to-currency-id", type=int, default=1,
                        help="Defaults to the same as --currency-id, which WILL be refused -- "
                             "pass a genuinely different, tenant-configured currency to test "
                             "a real create")
    parser.add_argument("--rate", type=float, default=1.0)
    args = parser.parse_args()

    print("Other REST Families - Exchange Rate Create (accounting/exchangerates)")
    print("=" * 60)

    config = load_config()
    token_data = get_token(config)
    headers = get_auth_headers(token_data["AccessToken"])
    print(f"Server: {config.base_url}")

    currencies = httpx.get(f"{config.base_url}/odataservice/odata/table/currency_hdr",
                           params={"$select": "currency_id,currency_desc"},
                           headers=headers, verify=config.verify_ssl, timeout=30.0).json()["value"]
    print(f"\nConfigured currencies: {currencies}")
    if len(currencies) < 2:
        print("Fewer than 2 currencies configured -- a genuine cross-currency rate "
              "cannot be created regardless of payload. This is a tenant limitation, "
              "not an API defect.")

    payload = {"CurrencyId": args.currency_id, "ToCurrencyId": args.to_currency_id,
              "Rate": args.rate, "ExchangeDate": "2026-09-12T00:00:00",
              "ExchangeCost": 0.0, "DeleteFlag": False, "RateType": 0}

    if not args.execute:
        print(f"\nDRY RUN - payload that would be POSTed to /api/accounting/exchangerates/:")
        print(payload)
        print("\nRe-run with --execute to actually attempt it.")
        return

    r = httpx.post(f"{config.base_url}/api/accounting/exchangerates/", headers=headers,
                   json=payload, verify=config.verify_ssl, timeout=60.0)
    print(f"\nHTTP {r.status_code}")
    print(r.text[:500])


if __name__ == "__main__":
    main()
