"""
Shared plumbing for the end-to-end runbook scripts

purchase_receive_vouch.py, sales_order_to_invoice.py, new_assembled_part.py,
rebate_assembly_program.py and dispose_zero_value_stock.py each run one
docs/recipes/ runbook page step by step, reading every step back before the
next one starts. This module holds what they share:

  * P21Runbook     -- one authenticated connection: Transaction POSTs judged
                      by Summary (never the HTTP status), OData read-backs,
                      and Interactive sessions.
  * RunbookSession -- the Interactive driver from order_with_assembly.py with
                      longer timeouts, plus the calls the runbooks add: a raw
                      save, popup buttons, and reading a window's rows.
  * The steps more than one runbook runs: a Transaction sales order (quote
    OFF), the sales-order pick ticket (print_tix), and the Shipping
    confirmation that creates the invoice.

This file is a library, not a recipe -- it has no main().
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from common.auth import get_token, get_auth_headers, get_ui_server_url
from common.config import load_config
from order_with_assembly import InteractiveOrderSession, is_blocked, popup_ids

TIMEOUT = 180  # saves that ship, invoice or post can take well over httpx's 5 s default


# --- Payload builders --------------------------------------------------------

def edit(name: str, value: str) -> dict:
    """One Transaction API edit."""
    return {"Name": name, "Value": value}


def element(name: str, type_: str, keys: list[str], rows: list[list[dict]]) -> dict:
    """One DataElement; rows is a list of edit lists."""
    return {"Name": name, "Type": type_, "Keys": keys,
            "Rows": [{"Edits": r, "RelativeDateEdits": []} for r in rows]}


def payload(service: str, elements: list[dict], ignore_disabled: bool = False) -> dict:
    """A one-Transaction Status "New" payload (the only Status the enum accepts)."""
    body = {"Name": service, "UseCodeValues": False,
            "Transactions": [{"Status": "New", "DataElements": elements}]}
    if ignore_disabled:
        body["IgnoreDisabled"] = True  # top level -- inside a Transaction it is ignored
    return body


def result_value(result: dict, element_name: str, field: str) -> str | None:
    """Read a field the server wrote back into a Transaction response's rows."""
    for txn in result.get("Results", {}).get("Transactions", []):
        for de in txn.get("DataElements", []):
            if de.get("Name") != element_name:
                continue
            for row in de.get("Rows", []):
                for e in row.get("Edits", []):
                    if e.get("Name") == field and e.get("Value") not in (None, ""):
                        return str(e["Value"])
    return None


def show(title: str, body: dict) -> None:
    """Print a payload for the dry run."""
    print(f"\n{title}:")
    print(json.dumps(body, indent=2))


# --- Connection --------------------------------------------------------------

class RunbookSession(InteractiveOrderSession):
    """Interactive v2 driver: order_with_assembly's session with runbook additions."""

    def answer_response_windows(self, result: dict, button: str | None = None) -> dict:
        """Answer every popup the last action opened (see the parent class).

        Same rules as the parent -- discover the buttons first, never answer
        blind -- with a timeout long enough for a click that resumes a save.

        Raises:
            RuntimeError: When the popup does not carry the wanted button.
        """
        for popup_id in popup_ids(result):
            available = self.tools(popup_id)
            if "cb_finish" in available:
                # The PO/RFQ wizard: a save can open it on its own when the user
                # has a Buyer ID. Cancel it -- nothing is committed before
                # cb_next -- and create the PO deliberately (purchase_receive_vouch B2).
                print("    (PO wizard opened by this save -- cancelled before cb_next)")
                result = self.click(popup_id, "cb_cancel")
                continue
            pick = button or next((b for b in ("cb_ok", "cb_1", "cb_yes") if b in available), None)
            if pick is None or pick not in available:
                raise RuntimeError(f"Popup {popup_id}: buttons {available}, wanted {button}")
            result = self.click(popup_id, pick)
        return result

    def change(self, window_id: str, tab: str, dw: str, field: str, value: str,
               answer: str | None = None) -> dict:
        """Change one field and answer any popup it raises (see the parent class).

        Raises:
            RuntimeError: When the change fails (HTTP 4xx or Status 2).
        """
        resp = httpx.put(
            f"{self.iapi}/v2/change", headers=self.headers, verify=self.verify,
            timeout=TIMEOUT,
            json={"WindowId": window_id, "List": [{
                "TabName": tab, "DatawindowName": dw, "FieldName": field, "Value": value}]},
        )
        if resp.status_code >= 400:  # e.g. "Column is disabled" comes back as HTTP 400
            raise RuntimeError(f"{field}: HTTP {resp.status_code} {resp.text[:300]}")
        result = resp.json()
        if result.get("Status") in (2, "Failure"):
            raise RuntimeError(f"{field}: {result.get('Messages')}")
        if is_blocked(result):
            result = self.answer_response_windows(result, answer)
        return result

    def save_raw(self, window_id: str) -> dict:
        """Save without answering anything -- for saves that open a wizard."""
        resp = httpx.put(f"{self.iapi}/v2/data", headers=self.headers,
                         verify=self.verify, json=window_id, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()

    def save(self, window_id: str, answer: str | None = None) -> dict:
        """Save and answer every follow-on prompt with answer (or a proceed button).

        Raises:
            RuntimeError: When the save comes back as a Failure.
        """
        result = self.save_raw(window_id)
        for _ in range(50):  # one prompt per unpriced line on a large $0 order
            if not is_blocked(result):
                break
            result = self.answer_response_windows(result, answer)
        if result.get("Status") in (2, "Failure"):
            raise RuntimeError(f"Save failed: {result.get('Messages')}")
        return result

    def tools(self, popup_id: str) -> list[str]:
        """Button names on a popup (GET /v2/tools takes ?windowId=, not ?id=)."""
        resp = httpx.get(f"{self.iapi}/v2/tools", params={"windowId": popup_id},
                         headers=self.headers, verify=self.verify, timeout=TIMEOUT)
        resp.raise_for_status()
        return [t.get("Name") or t.get("ToolName") for t in resp.json()]

    def click(self, popup_id: str, tool: str) -> dict:
        """Press one button on a popup."""
        resp = httpx.post(f"{self.iapi}/v2/tools", headers=self.headers, verify=self.verify,
                          json={"WindowId": popup_id, "ToolName": tool}, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()

    def get_data(self, window_id: str) -> list[dict]:
        """Datawindows on the window's (or popup's) active surface."""
        resp = httpx.get(f"{self.iapi}/v2/data", params={"id": window_id},
                         headers=self.headers, verify=self.verify, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()

    def rows(self, window_id: str, dw_name: str) -> list[dict]:
        """Rows of one datawindow on the active surface, as column -> value dicts."""
        for dw in self.get_data(window_id):
            if dw.get("Name") == dw_name:
                return [dict(zip(dw["Columns"], row)) for row in dw.get("Data") or []]
        return []


class P21Runbook:
    """One authenticated connection shared by every step of a runbook."""

    def __init__(self, auth: str = "password") -> None:
        """Authenticate and resolve the UI server.

        Args:
            auth: "password" (P21_USERNAME/P21_PASSWORD) or "consumer"
                (P21_CONSUMER_KEY acting as P21_CONSUMER_USERNAME) -- use the
                account whose P21 user has the setup a step needs, such as a
                Buyer ID for the direct-ship PO wizard.
        """
        self.config = load_config()
        has_password = bool(self.config.username and self.config.password)
        if auth == "consumer":
            if not (self.config.consumer_key and self.config.consumer_username):
                raise SystemExit("--auth consumer needs P21_CONSUMER_KEY and "
                                 "P21_CONSUMER_USERNAME in .env")
            token = get_token(self.config, consumer_key=self.config.consumer_key,
                              username=self.config.consumer_username)["AccessToken"]
        else:
            token = get_token(self.config)["AccessToken"]
        self.headers = get_auth_headers(token)
        # A consumer key's API Scope can withhold OData tables (401) while it
        # still writes through the Transaction and Interactive APIs -- read
        # back with the password login when there is one.
        self.read_headers = (get_auth_headers(get_token(self.config)["AccessToken"])
                             if auth == "consumer" and has_password else self.headers)
        self.base_url = self.config.base_url
        self.verify = self.config.verify_ssl
        self.ui_server = get_ui_server_url(self.base_url, token, self.verify)
        print(f"UI Server: {self.ui_server}")

    def transaction(self, body: dict, label: str) -> dict:
        """POST a Transaction and stop the runbook unless Summary says it passed.

        HTTP 200 comes back on failure too -- only Summary.Succeeded/Failed count.

        Raises:
            SystemExit: When the transaction failed or did nothing.
        """
        resp = httpx.post(f"{self.ui_server}/api/v2/transaction", headers=self.headers,
                          json=body, verify=self.verify, timeout=TIMEOUT)
        resp.raise_for_status()
        result = resp.json()
        summary = result["Summary"]
        print(f"  {label}: Succeeded={summary['Succeeded']} Failed={summary['Failed']}")
        for msg in result.get("Messages", []):
            print(f"    {msg}")
        if summary["Failed"] > 0 or summary["Succeeded"] == 0:
            raise SystemExit(f"{label} failed -- read the tables before retrying: "
                             "a Failed summary does not always mean nothing was written")
        return result

    def odata(self, table: str, filter_: str, select: str | None = None,
              orderby: str | None = None, top: int | None = None) -> list[dict]:
        """Read rows from the OData table surface."""
        params = {"$filter": filter_}
        if select:
            params["$select"] = select
        if orderby:
            params["$orderby"] = orderby
        if top:
            params["$top"] = str(top)
        resp = httpx.get(f"{self.base_url}/odataservice/odata/table/{table}", params=params,
                         headers=self.read_headers, verify=self.verify, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()["value"]

    def one(self, table: str, filter_: str, select: str | None = None,
            orderby: str | None = None) -> dict:
        """Read exactly one row (the first by orderby).

        Raises:
            SystemExit: When no row matches -- the step did not land.
        """
        rows = self.odata(table, filter_, select, orderby, top=1)
        if not rows:
            raise SystemExit(f"Read-back found no {table} row for {filter_}")
        return rows[0]

    def item_uid(self, item_id: str) -> int:
        """inv_mast_uid for an item ID (OData has no joins -- chain the uids)."""
        return self.one("inv_mast", f"item_id eq '{item_id}'", "inv_mast_uid")["inv_mast_uid"]

    def session(self) -> RunbookSession:
        """A new Interactive session with response-window handling on."""
        s = RunbookSession(self.ui_server, self.headers, self.verify)
        s.start_session()
        return s


def check(label: str, actual, expected) -> None:
    """Print one read-back comparison and stop the runbook on a mismatch."""
    ok = str(actual) == str(expected)
    print(f"    {label} = {actual} (expected {expected}) -> {'OK' if ok else 'MISMATCH'}")
    if not ok:
        raise SystemExit(f"Read-back mismatch on {label}")


# --- Steps shared by several runbooks -----------------------------------------

def build_order_payload(customer: str, ship_to: str, contact: str, sales_loc: str,
                        source_loc: str, order_date: str, requested_date: str,
                        po_no: str, taker: str,
                        lines: list[tuple[str, str, str | None]]) -> dict:
    """Transaction sales order: header plus every line in one POST.

    quote = OFF goes first: when the API user's default is "quote", a header
    without it saves a quote (oe_hdr.projected_order = 'Y'), and a quote
    refuses a pick ticket. A line price of None leaves unit_price unset so a
    contract price can bind.
    """
    header = [edit("quote", "OFF"), edit("customer_id", customer),
              edit("sales_loc_id", sales_loc), edit("source_loc_id", source_loc),
              edit("order_date", order_date), edit("requested_date", requested_date),
              edit("po_no", po_no), edit("taker", taker),
              edit("ship_to_id", ship_to), edit("contact_id", contact)]
    rows = []
    for item_id, qty, price in lines:
        row = [edit("oe_order_item_id", item_id), edit("unit_quantity", qty)]
        if price is not None:
            row.append(edit("unit_price", price))
        rows.append(row)
    return payload("Order", [element("TABPAGE_1.order", "Form", [], [header]),
                             element("TP_ITEMS.items", "List", [], rows)])


def enter_order(rb: P21Runbook, header: dict[str, str], lines: list[list[tuple[str, str]]],
                salesrep: str | None = None, hold: bool = False) -> str:
    """Enter and save a sales order in the Interactive Order window; return its order_no.

    Header fields go one change at a time, quote = OFF first (the window can
    open in quote mode). Both dates raise the date-cascade prompt even on a
    new order -- answered cb_ok. The first line goes on the row that already
    exists; each further line gets POST /v2/row first. Entering the item
    answers "add as assembly?" with No (cb_2) when it asks.

    The window clears after the save, so the order is found by its customer
    PO number (newest oe_hdr_uid -- order_no is a string and does not sort).

    Args:
        rb: Connection.
        header: TABPAGE_1.order fields in entry order (dates included).
        lines: Per line, (field, value) pairs in entry order -- item first.
        salesrep: Replace the customer's default rep on TP_SALESREPS row 1.
        hold: Put the order on Hold (packing_basis) before saving.
    """
    session = rb.session()
    window_id = session.open_window("Order")
    try:
        session.change(window_id, "TABPAGE_1", "order", "quote", "OFF")
        for field, value in header.items():
            answer = "cb_ok" if field.endswith("_date") else None
            session.change(window_id, "TABPAGE_1", "order", field, value, answer=answer)
        if salesrep:
            session.tab(window_id, "TP_SALESREPS")
            session.change(window_id, "TP_SALESREPS", "tp_salesreps", "salesrep_id", salesrep)
            session.tab(window_id, "TABPAGE_1")
        if hold:
            session.change(window_id, "TABPAGE_1", "order", "packing_basis", "Hold")
        session.tab(window_id, "TP_ITEMS")
        for i, line in enumerate(lines):
            if i > 0:
                httpx.post(f"{session.iapi}/v2/row", headers=session.headers,
                           verify=session.verify, timeout=TIMEOUT,
                           json={"WindowId": window_id, "DatawindowName": "items"}
                           ).raise_for_status()
            for field, value in line:
                answer = "cb_2" if field == "oe_order_item_id" else None
                session.change(window_id, "TP_ITEMS", "items", field, value, answer=answer)
        session.save(window_id)
    finally:
        session.cleanup(window_id)
    hdr = rb.one("oe_hdr", f"po_no eq '{header['po_no']}'",
                 "order_no,projected_order,packing_basis,taker", orderby="oe_hdr_uid desc")
    print(f"    order_no = {hdr['order_no']} (projected_order={hdr['projected_order']}, "
          f"packing_basis={hdr['packing_basis']}, taker={hdr['taker']})")
    if hdr["projected_order"] != "N":
        raise SystemExit("The order saved as a quote -- quote = OFF did not take")
    return str(hdr["order_no"])


def build_print_tix_payload(order_no: str) -> dict:
    """Print the sales-order pick ticket: Order keyed on order_no + print_tix ON."""
    return payload("Order", [
        element("TABPAGE_1.order", "Form", ["order_no"], [[edit("order_no", order_no)]]),
        element("TP_FRONTCOUNTER.tp_frontcounter", "Form", [], [[edit("print_tix", "ON")]]),
    ])


def print_pick_ticket(rb: P21Runbook, order_no: str) -> str:
    """Print the pick ticket and return its number, read back from oe_pick_ticket.

    The PDF's file name carries a different number -- read the table instead.
    """
    rb.transaction(build_print_tix_payload(order_no), "Pick ticket (print_tix)")
    ticket = rb.one("oe_pick_ticket", f"order_no eq '{order_no}' and delete_flag eq 'N'",
                    "pick_ticket_no,location_id,invoice_no", orderby="pick_ticket_no desc")
    print(f"    pick_ticket_no = {ticket['pick_ticket_no']} at location {ticket['location_id']}")
    return str(ticket["pick_ticket_no"])


def ship_and_invoice(rb: P21Runbook, pick_ticket_no: str) -> str:
    """Confirm the shipment in the Interactive Shipping window; return the invoice_no.

    create_invoice ("Confirm Shipment") defaults ON, so the save ships AND
    invoices. Proceed prompts -- one per unpriced line on a $0 order -- are
    answered with cb_1 / cb_ok / cb_yes, never cb_cancel.
    """
    session = rb.session()
    window_id = session.open_window("Shipping")
    try:
        session.change(window_id, "TABPAGE_1", "tp_1_dw_1", "pick_ticket_no", pick_ticket_no)
        session.save(window_id)
    finally:
        session.cleanup(window_id)
    ticket = rb.one("oe_pick_ticket", f"pick_ticket_no eq {pick_ticket_no}",
                    "pick_ticket_no,ship_date,invoice_no")
    if not ticket.get("invoice_no"):
        raise SystemExit(f"Pick ticket {pick_ticket_no} has no invoice after the save")
    print(f"    shipped {ticket['ship_date']}, invoice_no = {ticket['invoice_no']}")
    return str(ticket["invoice_no"])


def print_invoice(rb: P21Runbook, invoice_no: str) -> list[dict]:
    """Read back the invoice header and lines; return the lines."""
    hdr = rb.one("invoice_hdr", f"invoice_no eq '{invoice_no}'", "invoice_no,order_no,total_amount")
    print(f"    invoice {hdr['invoice_no']} for order {hdr['order_no']}: "
          f"total {hdr['total_amount']}")
    lines = rb.odata("invoice_line", f"invoice_no eq '{invoice_no}'",
                     "line_no,item_id,qty_shipped,unit_price,cogs_amount,other_cost,"
                     "commission_cost,invoice_line_uid,invoice_line_uid_parent")
    for line in sorted(lines, key=lambda x: x["line_no"]):
        print(f"      line {line['line_no']} {line['item_id']}: qty {line['qty_shipped']} "
              f"price {line['unit_price']} cogs {line['cogs_amount']} "
              f"other_cost {line['other_cost']} commission_cost {line['commission_cost']}")
    return lines
