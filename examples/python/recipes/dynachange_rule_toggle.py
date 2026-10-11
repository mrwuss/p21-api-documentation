"""
Disable and Re-enable a DynaChange Business Rule (Interactive API, Rules organizer)

No service maintains business rules. The route is the DynaChange Organizer
tool "dc.organizer.rule", which every open window carries: running it opens
w_business_rule_organizer as a response window. This script opens it from a
host window, finds one rule by rule_name + field_name + window_title,
switches it to the opposite status, applies, reads business_rule.row_status_flag
back through the p21_view_business_rule OData view, then puts the original
status back and verifies again. Use --leave to keep the rule switched.

Key rules (verified on play 26.1.5950.0, October 2026):
    - Select the row first (PUT /v2/row). A /v2/change lands on the ACTIVE
      row; a Row inside the change item is ignored.
    - row_status_flag takes "Active" / "Inactive" here (stored 704 / 705).
    - cb_apply commits. Close the organizer with cb_cancel afterwards.
    - The grid has no business_rule_uid; rule_name alone is not unique.
    - Test with the account your integration uses: the verified run used a
      user that has DynaChange rights.

Mirrors: docs/04-Interactive-API.md#managing-business-rules-through-the-dynachange-organizer

Usage:
    python examples/python/recipes/dynachange_rule_toggle.py                 # dry run
    python examples/python/recipes/dynachange_rule_toggle.py --execute \\
        --rule-name ExampleRule --field-name item_id --window-title "Item Maintenance"
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from common.auth import get_token, get_auth_headers, get_ui_server_url
from common.config import load_config
from common.interactive_session import InteractiveSession, popup_ids

import warnings
warnings.filterwarnings("ignore")

LABEL = {704: "Active", 705: "Inactive"}


def rule_status(http: httpx.Client, base_url: str, args: argparse.Namespace) -> list[dict]:
    """Read the matching rule(s) from the p21_view_business_rule OData view."""
    flt = (f"rule_name eq '{args.rule_name}' and field_name eq '{args.field_name}' "
           f"and window_title eq '{args.window_title}'")
    r = http.get(f"{base_url}/odataservice/odata/view/p21_view_business_rule",
                 params={"$filter": flt,
                         "$select": "business_rule_uid,row_status_flag,date_last_modified"})
    r.raise_for_status()
    return r.json()["value"]


def set_status(s: InteractiveSession, organizer: str, row: int, status: str) -> None:
    """Select the rule row, change its status, and apply."""
    s.select_row(organizer, "list", row)                         # select FIRST
    s.change(organizer, "LIST", "list", "row_status_flag", status)
    s.run_tool(organizer, "cb_apply")                            # commit


def main() -> None:
    """Entry point: dry run prints the plan; --execute toggles, verifies and restores."""
    p = argparse.ArgumentParser(description="Toggle a DynaChange rule through the organizer")
    p.add_argument("--execute", action="store_true", help="Run the session (default: dry run)")
    p.add_argument("--leave", action="store_true", help="Do not restore the original status")
    p.add_argument("--rule-name", default="ExampleRule")
    p.add_argument("--field-name", default="item_id")
    p.add_argument("--window-title", default="Item Maintenance")
    p.add_argument("--host-service", default="Customer", help="Any window that opens")
    args = p.parse_args()

    print("DynaChange Organizer - disable / re-enable one rule")
    print("=" * 60)
    if not args.execute:
        print(f"""
DRY RUN - planned calls (nothing sent):
  POST sessions/ {{"ResponseWindowHandlingEnabled": true}}
  POST v2/window {{"ServiceName": "{args.host_service}"}}
  POST v2/tools  {{"ToolName": "dc.organizer.rule"}}  -> Status 3, organizer window id
  GET  v2/data   organizer LIST.list -> row where rule_name={args.rule_name},
                 field_name={args.field_name}, window_title={args.window_title}
  PUT  v2/row    list, Row n
  PUT  v2/change LIST/list: row_status_flag=<opposite>;  POST v2/tools cb_apply
  OData p21_view_business_rule -> row_status_flag (704 Active / 705 Inactive)
  ... same three calls with the original status, read back again
  POST v2/tools  cb_cancel (close the organizer); close the host window
Re-run with --execute.""")
        return

    config = load_config()
    token = get_token(config)["AccessToken"]
    headers = get_auth_headers(token)
    ui_server = get_ui_server_url(config.base_url, token, config.verify_ssl)

    with httpx.Client(headers=headers, verify=config.verify_ssl,
                      follow_redirects=True, timeout=60) as http:
        before = rule_status(http, config.base_url, args)
        if len(before) != 1:
            raise SystemExit(f"Expected one matching rule, found {len(before)}")
        original = LABEL[before[0]["row_status_flag"]]
        flipped = "Inactive" if original == "Active" else "Active"
        print(f"\nRule {before[0]['business_rule_uid']}: {original}")

        s = InteractiveSession(ui_server, headers, config.verify_ssl)
        s.start(response_windows=True)
        host = s.open_window(args.host_service)
        organizer = None
        try:
            organizer = popup_ids(s.run_tool(host, "dc.organizer.rule"))[0]
            rows = s.rows(organizer, "list")
            index = next((i for i, r in enumerate(rows, start=1)
                          if r["rule_name"] == args.rule_name
                          and r["field_name"] == args.field_name
                          and r["window_title"] == args.window_title), None)
            if index is None:
                raise SystemExit("Rule not in the organizer list (internal rules are not listed)")

            set_status(s, organizer, index, flipped)
            now = rule_status(http, config.base_url, args)[0]["row_status_flag"]
            print(f"Set {flipped}: row_status_flag={now} -> "
                  f"{'OK' if LABEL[now] == flipped else 'NOT APPLIED'}")

            if not args.leave:
                set_status(s, organizer, index, original)
                now = rule_status(http, config.base_url, args)[0]["row_status_flag"]
                print(f"Restored {original}: row_status_flag={now} -> "
                      f"{'OK' if LABEL[now] == original else 'NOT RESTORED'}")
        finally:
            if organizer:
                s.run_tool(organizer, "cb_cancel")
            s.close_window(host)
            s.end()


if __name__ == "__main__":
    main()
