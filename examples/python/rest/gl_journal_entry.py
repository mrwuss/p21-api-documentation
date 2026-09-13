"""
Other REST Families - Read a GL Journal Entry

Reads every distribution line of one GL transaction in a single call via
accounting/gl, confirms the entry balances to zero, and follows Source
back to the originating document when JournalId identifies a known
subledger.

Mirrors: docs/15-Other-REST-Families.md#accountinggl

Verified live, 26.1.5950.0:
    - An unknown transaction number returns HTTP 200 [] -- not a 404.
    - JournalId "IA" (inventory adjustment) carries the adjustment number
      in Source, readable back via inventory/inventoryadjustments/{Source}.

Usage:
    python examples/python/rest/gl_journal_entry.py 3
    python examples/python/rest/gl_journal_entry.py 3 --follow-source
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

# JournalId -> the family that reads Source back. Extend as more are verified.
SOURCE_FAMILY = {
    "IA": "inventory/inventoryadjustments",
}


def get_gl_lines(base_url: str, headers: dict, verify_ssl: bool,
                  transaction_number: str) -> list[dict]:
    """GET every distribution line of one GL transaction.

    Args:
        base_url: P21 base URL.
        headers: Auth headers.
        verify_ssl: Whether to verify SSL certificates.
        transaction_number: gl.transaction_number.

    Returns:
        list[dict]: The transaction's lines. Empty if the number is unknown
            -- the endpoint returns HTTP 200 [] rather than 404.
    """
    response = httpx.get(
        f"{base_url}/api/accounting/gl/{transaction_number}",
        headers=headers,
        verify=verify_ssl,
        follow_redirects=True,
        timeout=60.0,
    )
    response.raise_for_status()
    return response.json()


def follow_source(base_url: str, headers: dict, verify_ssl: bool, line: dict) -> None:
    """Read the document a GL line's Source points at, if the journal is known.

    Args:
        base_url: P21 base URL.
        headers: Auth headers.
        verify_ssl: Whether to verify SSL certificates.
        line: One GL distribution line.
    """
    family = SOURCE_FAMILY.get(line.get("JournalId"))
    if not family:
        print(f"  (no known family for JournalId {line.get('JournalId')!r} -- "
              f"add it to SOURCE_FAMILY once verified)")
        return
    source = line["Source"]
    response = httpx.get(
        f"{base_url}/api/{family}/{source}",
        headers=headers,
        verify=verify_ssl,
        follow_redirects=True,
        timeout=60.0,
    )
    response.raise_for_status()
    print(f"  {family}/{source}:")
    for k, v in response.json().items():
        if k not in ("Lines", "UserDefinedFields"):
            print(f"    {k}: {v}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Read a GL journal entry (docs/15 accounting/gl)"
    )
    parser.add_argument("transaction_number", help="gl.transaction_number")
    parser.add_argument(
        "--follow-source", action="store_true",
        help="Also read the document named by the first line's Source"
    )
    args = parser.parse_args()

    print("Other REST Families - GL Journal Entry")
    print("=" * 60)

    config = load_config()
    token_data = get_token(config)
    headers = get_auth_headers(token_data["AccessToken"])
    print(f"Server: {config.base_url}")

    lines = get_gl_lines(config.base_url, headers, config.verify_ssl,
                         args.transaction_number)

    if not lines:
        print(f"\nTransaction {args.transaction_number}: no lines "
              f"(HTTP 200 [] -- unknown transaction number)")
        return

    print(f"\nTransaction {args.transaction_number}: {len(lines)} line(s)")
    print("-" * 50)
    total = 0.0
    for line in lines:
        total += line["Amount"]
        print(f"  {line['AccountNumber']:14} {line['Amount']:>14,.2f}  "
              f"journal={line['JournalId']}  source={line['Source']}")
    print(f"\n  Balance: {total:,.2f}  ({'balanced' if abs(total) < 0.005 else 'NOT BALANCED'})")

    if args.follow_source:
        print("\nFollowing Source on the first line:")
        follow_source(config.base_url, headers, config.verify_ssl, lines[0])


if __name__ == "__main__":
    main()
