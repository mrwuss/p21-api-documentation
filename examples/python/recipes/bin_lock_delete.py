"""
Lock, Unlock, Delete, or Restore Bins (BinLocation)

Edit existing warehouse bins with the BinLocation service: the same
FORM.form element and the same three-field key (company_id, location_id,
bin_id) that creates a bin. A keyed Status "New" row lands on the existing
bin and changes only the flags you send.

    lock     pick_locked_flag + put_locked_flag = ON
    unlock   the same flags = OFF
    delete   delete_flag = ON   (soft delete -- the row stays, flagged Y)
    restore  delete_flag = OFF  (undoes a delete)

Before it writes, the script prints each bin's current flags (your backup)
and refuses to lock or delete a bin that holds stock or is an item's primary
bin. After the write it reads every bin back through the p21_view_bin OData
view -- the raw bin table is not reachable over OData -- and reports any bin
whose flags did not land. A skipped delete returns no error, so the read-back
is the only proof.

Mirrors: docs/03-Transaction-API.md#locking-unlocking-and-deleting-bins

Usage:
    python examples/python/recipes/bin_lock_delete.py lock A01-02-03                  # dry run
    python examples/python/recipes/bin_lock_delete.py lock A01-02-03 --execute        # POST + verify
    python examples/python/recipes/bin_lock_delete.py delete A01-02-03 A01-02-04 --location 10 --execute
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from common.tapi import connect, edit, odata, odata_quote, post_transaction

import warnings
warnings.filterwarnings("ignore")

# --- Configuration (generic placeholders -- substitute your own) ------------
COMPANY_ID = "ACME"
LOCATION_ID = "10"

# mode -> (edits to send, expected p21_view_bin values after the write)
MODES = {
    "lock":    ({"pick_locked_flag": "ON",  "put_locked_flag": "ON"},
                {"pick_locked_flag": "Y",   "put_locked_flag": "Y"}),
    "unlock":  ({"pick_locked_flag": "OFF", "put_locked_flag": "OFF"},
                {"pick_locked_flag": "N",   "put_locked_flag": "N"}),
    "delete":  ({"delete_flag": "ON"},  {"delete_flag": "Y"}),
    "restore": ({"delete_flag": "OFF"}, {"delete_flag": "N"}),
}
FLAG_COLUMNS = "bin_id,delete_flag,pick_locked_flag,put_locked_flag"


def build_payload(company_id: str, location_id: str, bin_ids: list[str],
                  edits: dict[str, str]) -> dict:
    """Build one BinLocation payload with one Transaction per bin.

    No IgnoreDisabled: the lock flags and delete_flag are enabled columns.
    (Creating a bin needs it only because creation sends system columns
    such as frozen_flag.)

    Args:
        company_id: Company of the bins.
        location_id: Location of the bins.
        bin_ids: Bins to change.
        edits: Flag name -> ON/OFF.

    Returns:
        dict: Complete Transaction API payload.
    """
    return {
        "Name": "BinLocation",
        "UseCodeValues": False,
        "Transactions": [{
            "Status": "New",
            "DataElements": [{
                "Name": "FORM.form",
                "Type": "Form",
                "Keys": ["company_id", "location_id", "bin_id"],
                "Rows": [{
                    "Edits": [edit("company_id", company_id),
                              edit("location_id", location_id),
                              edit("bin_id", bin_id)]
                             + [edit(name, value) for name, value in edits.items()],
                    "RelativeDateEdits": [],
                }],
            }],
        } for bin_id in bin_ids],
    }


def read_bins(session, location_id: str, bin_ids: list[str]) -> dict[str, dict]:
    """Read the bins' flags through the p21_view_bin view.

    Args:
        session: Session from connect().
        location_id: Location of the bins.
        bin_ids: Bins to read.

    Returns:
        dict[str, dict]: bin_id -> row (flags stored as Y/N).
    """
    ids = " or ".join(f"bin_id eq {odata_quote(b)}" for b in bin_ids)
    rows = odata(session, "p21_view_bin",
                 f"location_id eq {location_id} and ({ids})", FLAG_COLUMNS,
                 surface="view")
    return {row["bin_id"]: row for row in rows}


def bins_in_use(session, location_id: str, bin_ids: list[str]) -> list[str]:
    """Find bins that hold stock or are an item's primary bin at the location.

    Args:
        session: Session from connect().
        location_id: Location of the bins.
        bin_ids: Bins to check.

    Returns:
        list[str]: One line per bin that is in use.
    """
    problems = []
    for bin_id in bin_ids:
        stock = odata(session, "inv_bin",
                      f"location_id eq {location_id} and bin eq {odata_quote(bin_id)} "
                      "and quantity gt 0", "inv_mast_uid,quantity")
        if stock:
            problems.append(f"{bin_id}: holds stock for {len(stock)} item(s)")
        primary = odata(session, "inv_loc",
                        f"location_id eq {location_id} and primary_bin eq {odata_quote(bin_id)}",
                        "inv_mast_uid")
        if primary:
            problems.append(f"{bin_id}: primary bin for {len(primary)} item(s)")
    return problems


def main() -> None:
    """Entry point: dry run prints the payload; --execute backs up, posts, verifies."""
    parser = argparse.ArgumentParser(
        description="Lock, unlock, delete, or restore bins "
                    "(docs/03-Transaction-API.md#locking-unlocking-and-deleting-bins)")
    parser.add_argument("mode", choices=sorted(MODES))
    parser.add_argument("bin_ids", nargs="+", help="Bin IDs at the location")
    parser.add_argument("--company", default=COMPANY_ID)
    parser.add_argument("--location", default=LOCATION_ID)
    parser.add_argument("--execute", action="store_true",
                        help="Actually POST the transactions (default: dry run)")
    args = parser.parse_args()

    edits, expected = MODES[args.mode]
    payload = build_payload(args.company, args.location, args.bin_ids, edits)

    print(f"Recipe - Bins: {args.mode} (BinLocation)")
    print("=" * 60)
    if not args.execute:
        print("\nDRY RUN - payload that would be POSTed to {ui_server}/api/v2/transaction:")
        print(json.dumps(payload, indent=2))
        print("\nRe-run with --execute to POST it.")
        return

    session = connect()
    print(f"UI Server: {session.ui_server}")

    before = read_bins(session, args.location, args.bin_ids)
    missing = [b for b in args.bin_ids if b not in before]
    if missing:
        raise SystemExit(f"Not found at location {args.location}: {', '.join(missing)}")
    print("\nBefore (keep this as your backup):")
    for bin_id in args.bin_ids:
        print(f"  {before[bin_id]}")

    if args.mode in ("lock", "delete"):
        problems = bins_in_use(session, args.location, args.bin_ids)
        if problems:
            print("\nRefusing: locking or deleting a bin in use strands stock and putaways.")
            for line in problems:
                print(f"  {line}")
            raise SystemExit(1)

    print()
    post_transaction(session, payload)

    # A skipped write reports no error -- the read-back decides.
    print("\nVerify (p21_view_bin read-back):")
    after = read_bins(session, args.location, args.bin_ids)
    failures = 0
    for bin_id in args.bin_ids:
        row = after.get(bin_id, {})
        ok = all(row.get(column) == value for column, value in expected.items())
        failures += not ok
        print(f"  {bin_id}: {'OK' if ok else 'NOT APPLIED'} {row}")
    if failures:
        raise SystemExit(f"{failures} bin(s) did not change")


if __name__ == "__main__":
    main()
