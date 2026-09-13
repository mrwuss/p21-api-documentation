"""
Other REST Families - Post a GL Journal Entry (accounting/gl)

POST a balanced 2-line GL entry, then read it back with gl_journal_entry.py's
approach. Dry run by default; --execute actually posts.

Mirrors: docs/15-Other-REST-Families.md#posting-a-journal-entry-verified

Verified live, 26.1.5950.0:
    - The body is an ARRAY of lines (the same shape the keyed GET returns),
      posted together as one entry -- not one line per call.
    - The server assigns TransactionNumber, sets Approved: true, and fills
      in a SourceTypeCd automatically (3495 for a manual post via this
      endpoint).
    - The balance IS enforced server-side: a single unbalanced line is
      refused with "Records do not balance" (a P21.Business.Common.
      BusinessException from GlManager.UpdateAllRecords), not accepted
      and left for a human to notice later.
    - Period/YearForPeriod must name an OPEN period -- periods.period_closed
      eq 'N' over OData finds one. Posting into a closed period was not
      tested.

Usage:
    python examples/python/rest/gl_post.py                     # dry run
    python examples/python/rest/gl_post.py --execute \\
        --account 11120010 --offset-account 11130010 --amount 0.01
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


def find_open_period(base_url: str, headers: dict, verify_ssl: bool,
                      company_id: str) -> tuple[int, int]:
    """Find the most recent open period for a company over OData."""
    response = httpx.get(
        f"{base_url}/odataservice/odata/table/periods",
        params={"$select": "period,year_for_period",
                "$filter": f"company_no eq '{company_id}' and period_closed eq 'N'",
                "$orderby": "year_for_period desc,period desc", "$top": "1"},
        headers=headers, verify=verify_ssl, timeout=60.0,
    )
    response.raise_for_status()
    rows = response.json()["value"]
    if not rows:
        raise SystemExit(f"No open period found for company {company_id!r}")
    return rows[0]["period"], rows[0]["year_for_period"]


def post_entry(base_url: str, headers: dict, verify_ssl: bool, lines: list[dict]) -> httpx.Response:
    """POST an array of GL lines as one entry."""
    return httpx.post(
        f"{base_url}/api/accounting/gl/",
        headers={**headers, "Content-Type": "application/json"},
        json=lines, verify=verify_ssl, follow_redirects=True, timeout=90.0,
    )


def get_entry(base_url: str, headers: dict, verify_ssl: bool, transaction_number) -> list[dict]:
    """Read a journal entry back by transaction number."""
    response = httpx.get(
        f"{base_url}/api/accounting/gl/{transaction_number}",
        headers=headers, verify=verify_ssl, follow_redirects=True, timeout=60.0,
    )
    response.raise_for_status()
    return response.json()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Post a balanced GL entry (docs/15 accounting/gl)"
    )
    parser.add_argument("--execute", action="store_true",
                        help="Actually POST (default: dry run)")
    parser.add_argument("--company-id", default="ACME")
    parser.add_argument("--account", default="11120010", help="First account number")
    parser.add_argument("--offset-account", default="11130010",
                        help="Second account number -- must differ from --account")
    parser.add_argument("--amount", type=float, default=0.01,
                        help="Amount on the first line; the second line is the negative")
    parser.add_argument("--journal-id", default="AC",
                        help="journal.journal_id -- 'AC' (Accruals) is a safe generic choice "
                             "for a manual test entry; avoid subledger-owned ids like 'IA' "
                             "unless you also create the document that subledger expects")
    parser.add_argument("--source", default="ZZDOCTEST",
                        help="gl.source -- a free-text tag, not validated against anything")
    args = parser.parse_args()

    print("Other REST Families - Post a GL Journal Entry (accounting/gl)")
    print("=" * 60)

    config = load_config()
    token_data = get_token(config)
    headers = get_auth_headers(token_data["AccessToken"])
    print(f"Server: {config.base_url}")

    period, year = find_open_period(config.base_url, headers, config.verify_ssl, args.company_id)
    print(f"Open period: {period}/{year}")

    date = "2026-09-12T00:00:00"
    lines = [
        {"CompanyNo": args.company_id, "AccountNumber": args.account,
         "Period": period, "YearForPeriod": year, "JournalId": args.journal_id,
         "Amount": args.amount, "ForeignAmount": args.amount,
         "Description": "ZZ API DOC TEST - safe to delete", "Source": args.source,
         "TransactionDate": date},
        {"CompanyNo": args.company_id, "AccountNumber": args.offset_account,
         "Period": period, "YearForPeriod": year, "JournalId": args.journal_id,
         "Amount": -args.amount, "ForeignAmount": -args.amount,
         "Description": "ZZ API DOC TEST - safe to delete", "Source": args.source,
         "TransactionDate": date},
    ]

    if not args.execute:
        print("\nDRY RUN - payload that would be POSTed to /api/accounting/gl/:")
        print(json.dumps(lines, indent=2))
        print("\nRe-run with --execute to actually post it.")
        print("\nNOTE: the balance IS enforced server-side -- an unbalanced batch is")
        print("refused with \"Records do not balance\", not silently accepted.")
        return

    r = post_entry(config.base_url, headers, config.verify_ssl, lines)
    if r.status_code != 200:
        print(f"\nPOST failed: HTTP {r.status_code}")
        print(r.text[:500])
        raise SystemExit(1)

    posted = r.json()
    txn = posted[0]["TransactionNumber"]
    print(f"\nPosted. TransactionNumber={txn}")
    for line in posted:
        print(f"  {line['AccountNumber']:14} {line['Amount']:>10.2f}  "
              f"Approved={line['Approved']}  SourceTypeCd={line['SourceTypeCd']}")

    print("\nRead-back:")
    print("-" * 50)
    total = 0.0
    for line in get_entry(config.base_url, headers, config.verify_ssl, txn):
        total += line["Amount"]
        print(f"  {line['AccountNumber']:14} {line['Amount']:>10.2f}")
    print(f"  Balance: {total:.2f} ({'balanced' if abs(total) < 0.005 else 'NOT BALANCED'})")


if __name__ == "__main__":
    main()
