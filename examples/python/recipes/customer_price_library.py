"""
Add (or Remove) a Customer Price Library (Interactive API, Customer window)

A customer's price libraries are the TABPAGE_7.tp_7_dw_price_library grid on
the Customer window. This script adds one library row -- price_library_id,
then optionally sequence_number -- saves, and reads every row's
sequence_number back from price_library_x_cust_x_cmpy. --remove deletes a
library row instead (row_status_flag Delete on the selected row).

Key rules (verified on play 26.1.5950.0, October 2026):
    - Service name is "Customer"; load the customer through
      TABPAGE_1.tp_1_dw_1.customer_id.
    - price_library_id is the library's ID string, not price_library_uid.
    - Set price_library_id BEFORE sequence_number. That order saved the row
      at the sequence sent and moved the others down; sending
      sequence_number first, or none, did not (see the doc section).
    - Read the sequence back -- what you sent is not proof of what saved.
    - Changes land on the ACTIVE row: select the row (PUT /v2/row) before
      setting row_status_flag. Delete removes the table row.

Mirrors: docs/04-Interactive-API.md#customer-window-adding-a-price-library

Usage:
    python examples/python/recipes/customer_price_library.py                     # dry run
    python examples/python/recipes/customer_price_library.py --execute \\
        --customer-id 100 --library-id LIB-001 --sequence 1
    python examples/python/recipes/customer_price_library.py --execute --remove \\
        --customer-id 100 --library-id LIB-001
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from common.auth import get_token, get_auth_headers, get_ui_server_url
from common.config import load_config
from common.interactive_session import BLOCKED, InteractiveSession, popup_ids

import warnings
warnings.filterwarnings("ignore")

TAB, GRID = "TABPAGE_7", "tp_7_dw_price_library"


def read_back(http: httpx.Client, base_url: str, customer_id: str) -> list[tuple]:
    """(sequence_number, price_library_id, row uid) for the customer, in sequence order."""
    def rows(table: str, flt: str) -> list[dict]:
        r = http.get(f"{base_url}/odataservice/odata/table/{table}", params={"$filter": flt})
        r.raise_for_status()
        return r.json()["value"]

    links = rows("price_library_x_cust_x_cmpy", f"customer_id eq {customer_id}")
    out = []
    for link in links:
        lib = rows("price_library", f"price_library_uid eq {link['price_library_uid']}")[0]
        out.append((link["sequence_number"], lib["price_library_id"],
                    link["price_lib_x_cust_x_cmpy_uid"]))
    return sorted(out)


def main() -> None:
    """Entry point: dry run prints the plan; --execute adds or removes, then reads back."""
    p = argparse.ArgumentParser(description="Add or remove a customer price library")
    p.add_argument("--execute", action="store_true", help="Run the session (default: dry run)")
    p.add_argument("--remove", action="store_true", help="Delete the library row instead")
    p.add_argument("--customer-id", default="100")
    p.add_argument("--library-id", default="LIB-001", help="price_library_id (the ID string)")
    p.add_argument("--sequence", default=None, help="Optional sequence_number for the new row")
    args = p.parse_args()

    print("Customer window - price library " + ("remove" if args.remove else "add"))
    print("=" * 60)
    if not args.execute:
        steps = ([f"PUT  v2/row    {GRID} -> the row whose price_library_id={args.library_id}",
                  f"PUT  v2/change {TAB}/{GRID}: row_status_flag=Delete"] if args.remove else
                 [f"POST v2/row    {GRID}  (add_row)",
                  f"PUT  v2/change {TAB}/{GRID}: price_library_id={args.library_id}"]
                 + ([f"PUT  v2/change {TAB}/{GRID}: sequence_number={args.sequence}"]
                    if args.sequence else []))
        print("\nDRY RUN - planned calls (nothing sent):")
        print('  POST v2/window {"ServiceName": "Customer"}')
        print(f"  PUT  v2/change TABPAGE_1/tp_1_dw_1: customer_id={args.customer_id}")
        print(f"  PUT  v2/tab    {TAB}")
        for step in steps:
            print(f"  {step}")
        print("  PUT  v2/data   save\n  OData: price_library_x_cust_x_cmpy sequence read-back")
        print("\nRe-run with --execute.")
        return

    config = load_config()
    token = get_token(config)["AccessToken"]
    headers = get_auth_headers(token)
    ui_server = get_ui_server_url(config.base_url, token, config.verify_ssl)

    with httpx.Client(headers=headers, verify=config.verify_ssl,
                      follow_redirects=True, timeout=60) as http:
        print(f"\nBefore: {read_back(http, config.base_url, args.customer_id)}")

        s = InteractiveSession(ui_server, headers, config.verify_ssl)
        s.start(response_windows=True)
        window = s.open_window("Customer")
        try:
            s.change(window, "TABPAGE_1", "tp_1_dw_1", "customer_id", args.customer_id)
            s.select_tab(window, TAB)
            if args.remove:
                rows = s.rows(window, GRID)
                index = next((i for i, r in enumerate(rows, start=1)
                              if r.get("price_library_id") == args.library_id), None)
                if index is None:
                    raise SystemExit(f"{args.library_id} is not on customer {args.customer_id}")
                s.select_row(window, GRID, index)  # changes land on the ACTIVE row
                s.change(window, TAB, GRID, "row_status_flag", "Delete")
            else:
                s.add_row(window, GRID)
                s.change(window, TAB, GRID, "price_library_id", args.library_id)  # first
                if args.sequence:
                    s.change(window, TAB, GRID, "sequence_number", args.sequence)  # then
            result = s.save(window)
            if result.get("Status") == BLOCKED:
                raise RuntimeError(f"Save opened a popup: {s.tools(popup_ids(result)[0])}")
        finally:
            s.close_window(window)
            s.end()

        after = read_back(http, config.base_url, args.customer_id)
        print(f"After:  {after}")
        mine = [row for row in after if row[1] == args.library_id]
        if args.remove:
            print(f"Verify: {args.library_id} rows left = {len(mine)} -> "
                  f"{'OK' if not mine else 'STILL PRESENT'}")
        elif mine:
            want = args.sequence or "last"
            print(f"Verify: {args.library_id} saved at sequence {mine[-1][0]} (sent: {want})")
        else:
            print(f"Verify: {args.library_id} NOT saved")


if __name__ == "__main__":
    main()
