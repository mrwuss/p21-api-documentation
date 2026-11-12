"""
Inventory Return Notes, and a Task Linked to a Return (Interactive + Transaction API)

Two commands for one job: keeping a written trail on a return to a supplier.

    note   Add a header or line note through the InventoryReturn window's
           Notepad Entry popup. Works while the return is Unapproved (971),
           Approved (972) or Printed (973).
    task   Create a task linked to the return through the Task service, or
           update an existing one. Works in every status, including Shipped
           (974) and Vouched (975), where the notes are closed.

Key rules (verified on play 26.1.6004.0, November 2026):
    - Header tab HDR_NOTE, tool hdr_note&&cb_addnote; line tab LINE_NOTE,
      tool line_note&&cb_addnote. Select the line's row on LIST first.
    - The LIST grid has no line number column; row N is the Nth line.
    - Once the return is Shipped or Vouched the window cannot save. The
      plain save (PUT /v2/data) returns Status 2 with no message. The
      Quick.Save tool reports savesucceeded and writes nothing, so this
      script reads the status first and never uses that tool.
    - Task: transaction_type_cd takes the label "Inventory Return";
      transaction_no is the return number. company_id is a disabled column
      on create. Updates key on activity_trans_no.
    - An open task prompts its assignee when they load the return, so an
      Interactive load can come back Status 3 with a w_message to answer.

Mirrors: docs/04-Interactive-API.md#inventory-return-notes-and-the-lock-after-shipping

Usage:
    python examples/python/recipes/inventory_return_note.py note                  # dry run
    python examples/python/recipes/inventory_return_note.py note --execute \\
        --return-number 7000200 --topic "RGA 12345" --note "Sent for evaluation."
    python examples/python/recipes/inventory_return_note.py note --execute \\
        --return-number 7000200 --line 2 --topic "CORE" --note "Core credit expected."
    python examples/python/recipes/inventory_return_note.py task --execute \\
        --return-number 7000200 --subject "Return 7000200 status" \\
        --comments "Supplier is repairing the part."
    python examples/python/recipes/inventory_return_note.py task --execute \\
        --task-no 5001 --comments "Repaired part ships next week."
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from common.auth import get_auth_headers, get_token, get_ui_server_url
from common.config import load_config
from common.interactive_session import (
    BLOCKED,
    InteractiveSession,
    popup_ids,
    status_code,
)

import warnings

warnings.filterwarnings("ignore")

OPEN_STATUSES = {971: "Unapproved", 972: "Approved", 973: "Printed"}
CLOSED_STATUSES = {974: "Shipped", 975: "Vouched", 976: "Canceled"}
RETURN_TRANSACTION_TYPE = 987  # code_p21: Inventory Return, as stored on activity_trans


def odata(http: httpx.Client, base_url: str, table: str, flt: str) -> list[dict]:
    """Rows of one OData table matching a filter."""
    r = http.get(
        f"{base_url}/odataservice/odata/table/{table}", params={"$filter": flt}
    )
    r.raise_for_status()
    return r.json()["value"]


def read_return(http: httpx.Client, base_url: str, return_number: str) -> dict:
    """The return header row, or exit when there is none."""
    rows = odata(
        http, base_url, "inventory_return_hdr", f"return_number eq {return_number}"
    )
    if not rows:
        raise SystemExit(f"Inventory return {return_number} was not found")
    return rows[0]


def note_rows(
    http: httpx.Client, base_url: str, header_uid: int, line: int | None
) -> list[dict]:
    """Header notes, or the notes of one line, for a return."""
    if line is None:
        return odata(
            http,
            base_url,
            "inventory_return_hdr_notepad",
            f"inventory_return_hdr_uid eq {header_uid}",
        )
    lines = odata(
        http,
        base_url,
        "inventory_return_line",
        f"inventory_return_hdr_uid eq {header_uid} and line_number eq {line}",
    )
    if not lines:
        raise SystemExit(f"The return has no line {line}")
    uid = lines[0]["inventory_return_line_uid"]
    return odata(
        http,
        base_url,
        "inventory_return_line_notepad",
        f"inventory_return_line_uid eq {uid}",
    )


def answer_no(s: InteractiveSession, result: dict) -> None:
    """Answer No to a w_message opened by a load (the open-task prompt)."""
    for popup in popup_ids(result):
        if s.window_name(popup) == "w_message":
            s.run_tool(popup, "cb_2")


def add_note(args: argparse.Namespace) -> None:
    """Add a header or line note and read it back."""
    tab, tool = (
        ("LINE_NOTE", "line_note&&cb_addnote")
        if args.line
        else ("HDR_NOTE", "hdr_note&&cb_addnote")
    )
    if not args.execute:
        print("\nDRY RUN - planned calls (nothing sent):")
        print(
            f"  OData  inventory_return_hdr: return_number eq {args.return_number} (status check)"
        )
        print('  POST v2/window {"ServiceName": "InventoryReturn"}')
        print(f"  PUT  v2/change FORM/form: return_number={args.return_number}")
        if args.line:
            print("  PUT  v2/tab    LIST")
            print(f"  PUT  v2/row    list -> row {args.line}")
        print(f"  PUT  v2/tab    {tab}")
        print(f"  POST v2/tools  {tool}   (opens w_notepad_response_lite)")
        print(
            f"  PUT  v2/change popup _dw_hdr: topic={args.topic!r}, note={args.note!r}"
        )
        print("  POST v2/tools  popup cb_select_all, then cb_ok")
        print("  PUT  v2/data   save\n  OData: notepad read-back")
        print("\nRe-run with --execute.")
        return

    config = load_config()
    token = get_token(config)["AccessToken"]
    headers = get_auth_headers(token)
    ui_server = get_ui_server_url(config.base_url, token, config.verify_ssl)

    with httpx.Client(
        headers=headers, verify=config.verify_ssl, follow_redirects=True, timeout=60
    ) as http:
        header = read_return(http, config.base_url, args.return_number)
        status = header["row_status_flag"]
        if status in CLOSED_STATUSES:
            raise SystemExit(
                f"Return {args.return_number} is {CLOSED_STATUSES[status]} ({status}): the InventoryReturn "
                "window cannot save, so no note can be added here. Use the task command instead."
            )
        before = {
            n["note_id"]
            for n in note_rows(
                http, config.base_url, header["inventory_return_hdr_uid"], args.line
            )
        }

        s = InteractiveSession(ui_server, headers, config.verify_ssl)
        s.start(response_windows=True)
        window = s.open_window("InventoryReturn")
        try:
            loaded = s.change(
                window, "FORM", "form", "return_number", args.return_number
            )
            if status_code(loaded) == BLOCKED:
                answer_no(s, loaded)
            if args.line:
                s.select_tab(window, "LIST")
                s.select_row(window, "list", args.line)  # row N is the Nth line
            s.select_tab(window, tab)
            opened = s.run_tool(window, tool)
            popups = popup_ids(opened)
            if not popups:
                raise RuntimeError(f"{tool} did not open the Notepad Entry popup")
            popup = popups[0]
            s.change(popup, None, "_dw_hdr", "topic", args.topic)
            s.change(popup, None, "_dw_hdr", "note", args.note)
            s.run_tool(popup, "cb_select_all")
            s.run_tool(popup, "cb_ok")
            s.save(window)  # raises on Status 2
        finally:
            s.close_window(window)
            s.end()

        after = note_rows(
            http, config.base_url, header["inventory_return_hdr_uid"], args.line
        )
        new = [n for n in after if n["note_id"] not in before]
        print(f"Status: {OPEN_STATUSES.get(status, status)}")
        for n in new:
            print(
                f"Saved note_id {n['note_id']}: topic={n['topic']!r} note={n['note']!r}"
            )
        print(f"Verify: {'OK' if new else 'NOT SAVED'}")


def task_payload(args: argparse.Namespace, supplier_id: str) -> dict:
    """Transaction API payload that creates or updates the task."""
    if args.task_no:
        edits = [("activity_trans_no", args.task_no), ("comments", args.comments)]
        if args.complete:
            edits.append(("completed_flag", "ON"))
        keys = ["activity_trans_no"]
    else:
        edits = [
            ("subject", args.subject),
            ("activity_id", args.activity_id),
            ("link_type_cd", "Supplier"),
            ("link_id", supplier_id),
            ("transaction_type_cd", "Inventory Return"),
            ("transaction_no", args.return_number),
            ("comments", args.comments),
        ]
        keys = []
    return {
        "Name": "Task",
        "UseCodeValues": False,
        "Transactions": [
            {
                "Status": "New",
                "DataElements": [
                    {
                        "Name": "FORM.form",
                        "Type": "Form",
                        "Keys": keys,
                        "Rows": [
                            {
                                "Edits": [{"Name": n, "Value": v} for n, v in edits],
                                "RelativeDateEdits": [],
                            }
                        ],
                    }
                ],
            }
        ],
    }


def write_task(args: argparse.Namespace) -> None:
    """Create a task linked to the return, or update one, and read it back."""
    if not args.execute:
        print(
            "\nDRY RUN - payload (nothing sent; <supplier_id> is read from the return):"
        )
        print(json.dumps(task_payload(args, "<supplier_id>"), indent=2))
        print("\nRe-run with --execute.")
        return

    config = load_config()
    token = get_token(config)["AccessToken"]
    headers = get_auth_headers(token)
    ui_server = get_ui_server_url(config.base_url, token, config.verify_ssl)

    with httpx.Client(
        headers=headers, verify=config.verify_ssl, follow_redirects=True, timeout=120
    ) as http:
        supplier_id = ""
        if not args.task_no:
            header = read_return(http, config.base_url, args.return_number)
            supplier_id = str(int(header["supplier_id"]))
        r = http.post(
            f"{ui_server}/api/v2/transaction", json=task_payload(args, supplier_id)
        )
        r.raise_for_status()
        body = r.json()
        print(f"Summary: {body.get('Summary')}")
        if (body.get("Summary") or {}).get("Succeeded") != 1:
            raise SystemExit(f"Task write failed: {body.get('Messages')}")
        task_no = args.task_no
        for transaction in (body.get("Results") or {}).get("Transactions") or []:
            for element in transaction.get("DataElements") or []:
                for row in element.get("Rows") or []:
                    for e in row.get("Edits") or []:
                        if e["Name"] == "activity_trans_no" and e["Value"]:
                            task_no = e["Value"]
        # activity_trans_no is a string over OData: quote it, or the filter 404s.
        row = odata(
            http, config.base_url, "activity_trans", f"activity_trans_no eq '{task_no}'"
        )[0]
        print(
            f"Task {task_no}: transaction_type_cd={row['transaction_type_cd']} "
            f"transaction_no={str(row['transaction_no']).strip()!r} completed={row['completed_flag']} "
            f"comments={row['comments']!r}"
        )
        linked = args.task_no or (
            row["transaction_type_cd"] == RETURN_TRANSACTION_TYPE
            and str(row["transaction_no"]).strip() == args.return_number
        )
        print(
            f"Verify: {'OK' if linked and row['comments'] == args.comments else 'CHECK THE ROW'}"
        )


def main() -> None:
    """Entry point: dry run prints the plan; --execute writes, then reads back."""
    p = argparse.ArgumentParser(description="Inventory return notes and linked tasks")
    sub = p.add_subparsers(dest="command", required=True)

    note = sub.add_parser("note", help="Add a header or line note (open returns only)")
    note.add_argument(
        "--execute", action="store_true", help="Run the session (default: dry run)"
    )
    note.add_argument("--return-number", default="7000200")
    note.add_argument(
        "--line",
        type=int,
        default=None,
        help="Line number for a line note (default: header note)",
    )
    note.add_argument("--topic", default="API NOTE", help="Up to 30 characters")
    note.add_argument("--note", default="Written through the Interactive API.")

    task = sub.add_parser(
        "task", help="Create or update a task linked to the return (any status)"
    )
    task.add_argument(
        "--execute", action="store_true", help="Send the transaction (default: dry run)"
    )
    task.add_argument("--return-number", default="7000200")
    task.add_argument(
        "--task-no", default=None, help="activity_trans_no of a task to update"
    )
    task.add_argument("--subject", default="Inventory return status")
    task.add_argument(
        "--activity-id",
        default="FOLLOW UP",
        help="An activity ID that exists on your tenant",
    )
    task.add_argument("--comments", default="Supplier is evaluating the part.")
    task.add_argument(
        "--complete", action="store_true", help="With --task-no: mark the task complete"
    )

    args = p.parse_args()
    print(f"Inventory return - {args.command}")
    print("=" * 60)
    if args.command == "note":
        add_note(args)
    else:
        write_task(args)


if __name__ == "__main__":
    main()
