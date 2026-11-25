"""
Interactive API - Move Part of a PO Link off a Production Order Component (v2)

A PO line is linked to a production order component (PurchaseOrder window,
Items tab, Backorders tab, links_for_po.linked_qty). This script moves part
of that link to an approved sales order line and lowers the component by the
same amount, in the three saves P21 allows:

    a. PurchaseOrder window, one save: the component row (PR ORD) N -> 0,
       then the sales order row (REG) 0 -> SHARE.
    b. ProductionOrder window, TABPAGE_18.components: qty_per_assembly
       lowered to NEW_QTY.
    c. PurchaseOrder window again: the component row 0 -> N - SHARE.

Why three saves (verified on play 26.1.6004.0, November 2026):
    - The component refuses any qty_per_assembly edit while ANY PO link is
      live on it -- even 3 of 4 linked, and even when the new quantity still
      covers allocated + linked: "This component has linked PO or Transfer
      lines.  You can not edit this information."
    - In one PO save, set the decrease before the increase: a save whose rows
      add up to more than the PO line's quantity fails with "The sum of the
      linked backorders is greater than the purchase quantity."
    - A sales order line is on the Backorders tab only once the order is
      approved and not on hold (a credit hold keeps it off the tab).

The unlinked component row stays in prod_ord_line_po at row_status_flag
700 (quantity kept); step c sets it back to 702 with the new quantity.

Every step reads prod_ord_line_po, oe_line_po and the component back over
OData. The dry run (default) reads the current state, checks the guards and
prints the plan; nothing is written without --execute.

Usage:
    python examples/python/interactive/07_po_link_partial_move.py \\
        --po 500100 --prod-order 1000123 --component 3 --item WIDGET-001 \\
        --order 1001234 --share 1 --new-qty 4             # dry run
    python examples/python/interactive/07_po_link_partial_move.py ... --execute
"""

import argparse
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from common.auth import get_auth_headers, get_token, get_ui_server_url
from common.config import load_config
from common.interactive_session import (
    BLOCKED,
    SUCCESS,
    InteractiveSession,
    popup_ids,
    status_code,
)

import warnings

warnings.filterwarnings("ignore")

LIVE, UNLINKED = 702, 700  # prod_ord_line_po.row_status_flag


def odata(http: httpx.Client, base_url: str, table: str, flt: str, select: str) -> list[dict]:
    """Rows of one OData table query."""
    r = http.get(
        f"{base_url}/odataservice/odata/table/{table}",
        params={"$filter": flt, "$select": select},
    )
    r.raise_for_status()
    return r.json()["value"]


def state(http: httpx.Client, base_url: str, args: argparse.Namespace, label: str) -> dict:
    """Print and return the component, its PO link and the order line's PO link."""
    comp = odata(
        http, base_url, "prod_order_line_component",
        f"prod_order_number eq {args.prod_order} and line_number eq {args.prod_line} "
        f"and component_number eq {args.component}",
        "qty_per_assembly,qty_requested,qty_allocated,disposition",
    )
    comp_links = odata(
        http, base_url, "prod_ord_line_po",
        f"po_number eq {args.po} and po_line_number eq {args.po_line} "
        f"and prod_order_number eq {args.prod_order} and line_number eq {args.prod_line} "
        f"and component_number eq {args.component}",
        "quantity,row_status_flag",
    )
    # oe_line_po holds transfer links too (connection_type T, po_no = transfer number).
    order_links = odata(
        http, base_url, "oe_line_po",
        f"po_no eq {args.po} and po_line_number eq {args.po_line} and connection_type eq 'P' "
        f"and order_number eq '{args.order}' and line_number eq {args.order_line}",
        "quantity_on_po,delete_flag",
    )
    if not comp:
        raise SystemExit("Component not found: check --prod-order, --prod-line, --component")
    linked = sum(float(r["quantity"]) for r in comp_links if r["row_status_flag"] == LIVE)
    on_order = sum(float(r["quantity_on_po"]) for r in order_links if r["delete_flag"] == "N")
    print(f"\n{label}:")
    print(f"  component       {comp[0]}")
    print(f"  prod_ord_line_po {comp_links}  -> linked {linked:g}")
    print(f"  oe_line_po       {order_links}  -> linked {on_order:g}")
    return {"comp": comp[0], "linked": linked, "on_order": on_order}


def set_links(s: InteractiveSession, args: argparse.Namespace, targets: list[tuple[str, str]]) -> None:
    """PurchaseOrder window, Backorders tab: set linked_qty on each (row, qty) in order, one save."""
    window = s.open_window("PurchaseOrder")
    try:
        s.change(window, "TABPAGE_1", "tp_1_dw_1", "po_no", args.po)
        s.select_tab(window, "TABPAGE_17")
        s.select_row(window, "tp_17_dw_17", args.po_line)
        s.select_tab(window, "BACKORDERS")
        for row_kind, qty in targets:
            # GET /v2/data returns text; numbers can carry a decimal part.
            rows = s.rows(window, "links_for_po")
            if row_kind == "component":
                hits = [i for i, r in enumerate(rows, 1) if r["c_ordertype"] == "PR ORD"
                        and r["order_no"].split(".")[0] == args.prod_order
                        and r["component_number"].split(".")[0] == str(args.component)]
            else:
                # Not listed until the order is approved and off hold.
                hits = [i for i, r in enumerate(rows, 1) if r["c_ordertype"] != "PR ORD"
                        and r["order_no"].split(".")[0] == args.order
                        and r["line_no"].split(".")[0] == str(args.order_line)]
            if len(hits) != 1:
                raise RuntimeError(f"{row_kind} row not on the Backorders tab: {rows}")
            s.select_row(window, "links_for_po", hits[0])
            s.change(window, "BACKORDERS", "links_for_po", "linked_qty", qty)
            print(f"  {row_kind} linked_qty -> {qty}")
        answer_prompts(s, s.save(window))
    finally:
        s.close_window(window)


def answer_prompts(s: InteractiveSession, result: dict) -> None:
    """Answer w_message prompts with Yes (cb_1); stop on any other response window."""
    for _ in range(10):
        if status_code(result) == SUCCESS:
            return
        if status_code(result) != BLOCKED:
            raise RuntimeError(f"Save did not succeed: {result.get('Messages')}")
        for popup in popup_ids(result):
            name = s.window_name(popup)
            if name != "w_message":
                raise RuntimeError(f"Unexpected response window {name}: {s.tools(popup)}")
            # Seen here: "Production Order N has the following uncosted components: ...
            # Do you wish to continue?"
            print("  w_message on save: answered Yes (cb_1)")
            result = s.run_tool(popup, "cb_1")
    raise RuntimeError("Save still blocked after 10 prompts")


def lower_component(s: InteractiveSession, args: argparse.Namespace) -> None:
    """ProductionOrder window, Components tab: set the component's qty_per_assembly and save."""
    window = s.open_window("ProductionOrder")
    try:
        s.change(window, "TABPAGE_1", "tp_1_dw_1", "prod_order_number", args.prod_order)
        s.select_tab(window, "TABPAGE_17")
        s.select_row(window, "tp_17_dw_17", args.prod_line)
        s.select_tab(window, "TABPAGE_18")
        # The components grid has no component_number; match the item instead.
        rows = s.rows(window, "components")
        hits = [i for i, r in enumerate(rows, 1) if r["item_id_service_labor_id"] == args.item]
        if len(hits) != 1:
            raise RuntimeError(f"{args.item} is on {len(hits)} component rows; expected 1")
        s.select_row(window, "components", hits[0])
        s.change(window, "TABPAGE_18", "components", "qty_per_assembly", args.new_qty)
        print(f"  qty_per_assembly -> {args.new_qty}")
        answer_prompts(s, s.save(window))
    finally:
        s.close_window(window)


def main() -> None:
    """Entry point: the dry run checks the guards and prints the plan; --execute runs it."""
    p = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    p.add_argument("--po", required=True, help="PO number")
    p.add_argument("--po-line", type=int, default=1, help="PO line (row on the Items tab)")
    p.add_argument("--prod-order", required=True, help="Production order number")
    p.add_argument("--prod-line", type=int, default=1, help="Production order line")
    p.add_argument("--component", type=int, required=True, help="component_number on that line")
    p.add_argument("--item", required=True, help="The component's item ID (to find its grid row)")
    p.add_argument("--order", required=True, help="Approved sales order number")
    p.add_argument("--order-line", type=int, default=1, help="Sales order line")
    p.add_argument("--share", type=float, required=True, help="Quantity to move to the order line")
    p.add_argument("--new-qty", required=True, help="The component's new qty_per_assembly")
    p.add_argument("--execute", action="store_true", help="Save (default: dry run)")
    args = p.parse_args()

    config = load_config()
    token = get_token(config)["AccessToken"]
    headers = get_auth_headers(token)
    ui_server = get_ui_server_url(config.base_url, token, config.verify_ssl)

    with httpx.Client(headers=headers, verify=config.verify_ssl, timeout=60) as http:
        before = state(http, config.base_url, args, "Before")
        linked, comp = before["linked"], before["comp"]
        rest = linked - args.share
        new_qty, allocated = float(args.new_qty), float(comp["qty_allocated"])
        if before["on_order"]:
            raise SystemExit("The order line already holds a link from this PO line")
        if not 0 < args.share <= linked:
            raise SystemExit(f"--share must be above 0 and at most the linked {linked:g}")
        if not new_qty < float(comp["qty_per_assembly"]):
            raise SystemExit("--new-qty must be below the current qty_per_assembly")
        if rest > new_qty - allocated:
            raise SystemExit(f"The rest ({rest:g}) does not fit the lowered component's "
                             f"open quantity ({new_qty - allocated:g})")
        print(f"\nPlan: a) component {linked:g} -> 0, order line 0 -> {args.share:g}; "
              f"b) qty_per_assembly -> {args.new_qty}; c) component 0 -> {rest:g}")
        if not args.execute:
            print("DRY RUN: nothing saved. Re-run with --execute.")
            return

        s = InteractiveSession(ui_server, headers, config.verify_ssl)
        s.start(response_windows=True)
        step = "a"
        try:
            print("\na) PurchaseOrder window: unlink the component, link the order line")
            set_links(s, args, [("component", "0"), ("order line", f"{args.share:g}")])
            state(http, config.base_url, args, "After a")
            step = "b"
            print("\nb) ProductionOrder window: lower the component")
            lower_component(s, args)
            state(http, config.base_url, args, "After b")
            step = "c"
            print("\nc) PurchaseOrder window: link the rest back to the component")
            set_links(s, args, [("component", f"{rest:g}")])
        except RuntimeError:
            if step != "a":
                # Step a saved: the component is unlinked and the order line holds the share.
                print(f"\nStopped at step {step}. Finish by hand from the state below: lower "
                      f"the component if step b did not save, then link {rest:g} back to it.")
                state(http, config.base_url, args, "State now")
            raise
        finally:
            s.end()
        after = state(http, config.base_url, args, "After c")
        ok = after["linked"] == rest and after["on_order"] == args.share
        ok = ok and float(after["comp"]["qty_per_assembly"]) == new_qty
        print("\nRead-back:", "OK" if ok else "MISMATCH")
        if not ok:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
