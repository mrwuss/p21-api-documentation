"""
Insert, Update or Delete a UDT Row Through Its Maintenance Window (Interactive API)

A user-defined table's generated maintenance window (w_udt_data_maint) has no
service name. This script opens it by its menu label, then inserts a row,
updates one column of a row by Row ID, or deletes a row by Row ID, saves, and
reads the table back over OData.

Key rules (verified on play 26.1.6004.0, November 2026):
    - The window exists only after "Create Maintenance Window" is set for the
      table in User Defined Table Maintenance; its window name is the Title.
    - Tab TP_USERDEFINEDTABLE, datawindow tp_userdefinedtable (one form).
    - Setting udt_{name}_uid ("Row ID") loads the row; an unknown ID is
      Status 2, "Enter a valid ID or leave ID blank."
    - delete_row = Y and a save delete the row, with no confirmation dialog.

Mirrors: docs/04-Interactive-API.md#udt-maintenance-windows-edit-a-udt-row-through-its-window

Usage:
    python examples/python/recipes/udt_window_edit.py                    # dry run
    python examples/python/recipes/udt_window_edit.py --execute update \
        --title "Example Table Maintenance" --table udt_example --row-id 5 --set status=done
    python examples/python/recipes/udt_window_edit.py --execute insert \
        --title "Example Table Maintenance" --table udt_example --set status=new --set note=hello
    python examples/python/recipes/udt_window_edit.py --execute delete \
        --title "Example Table Maintenance" --table udt_example --row-id 5
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

TAB, DW = "TP_USERDEFINEDTABLE", "tp_userdefinedtable"


def read_rows(http: httpx.Client, base_url: str, table: str, flt: str) -> dict:
    """UDT rows matching an OData filter, keyed by udt_{name}_uid, values stripped."""
    r = http.get(
        f"{base_url}/odataservice/odata/table/{table}", params={"$filter": flt}
    )
    r.raise_for_status()
    pk = f"{table}_uid"
    return {
        row[pk]: {k: (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
        for row in r.json()["value"]
    }


def last_uid(http: httpx.Client, base_url: str, table: str) -> int:
    """The highest udt_{name}_uid in the table (0 when it is empty)."""
    pk = f"{table}_uid"
    r = http.get(
        f"{base_url}/odataservice/odata/table/{table}",
        params={"$select": pk, "$orderby": f"{pk} desc", "$top": "1"},
    )
    r.raise_for_status()
    rows = r.json()["value"]
    return rows[0][pk] if rows else 0


def main() -> None:
    """Entry point: dry run prints the plan; --execute writes, then reads back."""
    p = argparse.ArgumentParser(
        description="Edit a UDT row through its maintenance window"
    )
    p.add_argument(
        "action", nargs="?", default="update", choices=["insert", "update", "delete"]
    )
    p.add_argument(
        "--execute", action="store_true", help="Run the session (default: dry run)"
    )
    p.add_argument(
        "--title", default="Example Table Maintenance", help="The window's menu label"
    )
    p.add_argument("--table", default="udt_example", help="The UDT, for the read-back")
    p.add_argument(
        "--row-id", default="5", help="udt_{name}_uid of the row (update, delete)"
    )
    p.add_argument(
        "--set",
        action="append",
        default=[],
        metavar="COLUMN=VALUE",
        help="Column to set (insert, update); repeat for several",
    )
    args = p.parse_args()
    if any("=" not in pair for pair in args.set):
        p.error("--set takes COLUMN=VALUE")
    edits = [tuple(pair.split("=", 1)) for pair in args.set]
    if args.action != "delete" and not edits:
        p.error(f"{args.action} needs at least one --set COLUMN=VALUE")
    pk = f"{args.table}_uid"

    print(f"UDT maintenance window - {args.action}")
    print("=" * 60)
    steps = []
    if args.action != "insert":
        steps.append(f"PUT  v2/change {TAB}/{DW}: {pk}={args.row_id}  (load the row)")
    if args.action == "delete":
        steps.append(f"PUT  v2/change {TAB}/{DW}: delete_row=Y")
    else:
        steps += [f"PUT  v2/change {TAB}/{DW}: {c}={v}" for c, v in edits]
    if not args.execute:
        print("\nDRY RUN - planned calls (nothing sent):")
        print(f'  POST v2/window {{"Title": "{args.title}"}}')
        for step in steps:
            print(f"  {step}")
        print(f"  PUT  v2/data   save\n  OData: {args.table} read-back")
        print("\nRe-run with --execute.")
        return

    config = load_config()
    token = get_token(config)["AccessToken"]
    headers = get_auth_headers(token)
    ui_server = get_ui_server_url(config.base_url, token, config.verify_ssl)

    with httpx.Client(
        headers=headers, verify=config.verify_ssl, follow_redirects=True, timeout=60
    ) as http:
        before = last_uid(http, config.base_url, args.table)
        s = InteractiveSession(ui_server, headers, config.verify_ssl)
        s.start(response_windows=True)
        window = None
        try:
            window = s.open_window_by_title(args.title)
            if args.action != "insert":
                s.change(
                    window, TAB, DW, pk, args.row_id
                )  # Status 2 if the ID is unknown
            if args.action == "delete":
                s.change(window, TAB, DW, "delete_row", "Y")
            else:
                for column, value in edits:
                    s.change(window, TAB, DW, column, value)
            result = s.save(window)
            if result.get("Status") == BLOCKED:
                raise RuntimeError(
                    f"Save opened a popup: {s.tools(popup_ids(result)[0])}"
                )
            print(
                f"\nsave: Status {result.get('Status')} {result.get('Messages') or ''}"
            )
        finally:
            if window:
                s.close_window(window)
            s.end()

        if args.action == "insert":
            new = read_rows(http, config.base_url, args.table, f"{pk} gt {before}")
            print(f"Verify: inserted {pk} {list(new)} -> {list(new.values())}")
            return
        after = read_rows(http, config.base_url, args.table, f"{pk} eq {args.row_id}")
        if args.action == "delete":
            gone = not after
            print(
                f"Verify: {pk} {args.row_id} {'deleted' if gone else 'STILL PRESENT'}"
            )
        else:
            row = after.get(int(args.row_id))
            print(f"Verify: {row}")


if __name__ == "__main__":
    main()
