"""
Order with an Assembly Line (Interactive API)

Enter a sales order interactively when a line is an assembly that must
explode into components and/or spawn a production order. The Transaction API
auto-answers the "add as assembly?" prompt No, killing the explode -- the
Interactive API lets you answer it (cb_1 = Yes). The session is started with
ResponseWindowHandlingEnabled: true so prompts come back as windowopened
events that this script answers via GET/POST /v2/tools.

Mirrors: docs/recipes/order-with-assembly.md

Usage:
    python examples/python/recipes/order_with_assembly.py            # dry run: print call plan
    python examples/python/recipes/order_with_assembly.py --execute  # run the full session flow
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from common.auth import get_token, get_auth_headers, get_ui_server_url
from common.config import load_config

import warnings
warnings.filterwarnings("ignore")

# --- Configuration (generic placeholders -- substitute your own) ------------
SALES_LOC_ID = "10"
SOURCE_LOC_ID = "10"
CUSTOMER_ID = "100198"
SHIP_TO_ID = "200"
CONTACT_ID = "300"
ORDER_DATE = "2030-01-05"
REQUESTED_DATE = "2030-01-06"  # must differ from order_date
PO_NO = "PO-TEST-001"
TAKER = "JSMITH"               # else the order is attributed to the API user
ASSEMBLY_ITEM_ID = "WIDGET-001"  # an assembly item (assembly_hdr exists)
QUANTITY = "5"

CALL_PLAN = """\
Planned Interactive API call sequence (nothing has been sent):

  1. POST {iapi}/sessions                {{"ResponseWindowHandlingEnabled": true}}
  2. POST {iapi}/v2/window               {{"ServiceName": "Order"}}
  3. PUT  {iapi}/v2/change  (TABPAGE_1 / order, one field per call):
        quote=OFF, sales_loc_id={sales_loc}, source_loc_id={source_loc},
        customer_id={customer}, ship_to_id={ship_to}, contact_id={contact},
        order_date={order_date}  (answers date-cascade prompt with cb_ok),
        requested_date={req_date} (answers date-cascade prompt with cb_ok),
        po_no={po_no}, taker={taker}
  4. PUT  {iapi}/v2/tab                  {{"PageName": "TP_ITEMS"}}
  5. PUT  {iapi}/v2/change  (TP_ITEMS / items, EXISTING first row):
        oe_order_item_id={item}  (answers assembly prompt with cb_1 = Yes)
  6. PUT  {iapi}/v2/change  unit_quantity={qty}
  7. PUT  {iapi}/v2/data    (body = bare window-ID string) -- SAVE
        (follow-on prompts answered with their proceed button)
  8. PUT  {iapi}/v2/tab back to TABPAGE_1, GET {iapi}/v2/data?id=... -> order_no
  9. DELETE {iapi}/v2/window?id=...; DELETE {iapi}/sessions
 10. Verify: OData oe_line assembly codes for the new order
        (B kit parent, N component, P production-order line, S build-to-stock)
"""


def is_blocked(result: dict) -> bool:
    """True when the last action was blocked by a response window.

    Status is an integer (ResultStatus enum: 0 None, 1 Success, 2 Failure,
    3 Blocked) but may appear as a string in some contexts -- handle both.
    """
    return result.get("Status") in (3, "Blocked")


def popup_ids(result: dict) -> list[str]:
    """Window IDs of popups opened by the last action.

    Events[].Data is a key-value list: [{"Key": "windowid", "Value": "..."}].
    """
    ids = []
    for event in result.get("Events", []):
        if event.get("Name") == "windowopened":
            for kv in event.get("Data", []):
                if kv.get("Key") == "windowid":
                    ids.append(kv["Value"])
    return ids


class InteractiveOrderSession:
    """Drives the Order window over the Interactive API v2 endpoints."""

    def __init__(self, ui_server: str, headers: dict, verify_ssl: bool) -> None:
        """Store connection details.

        Args:
            ui_server: UI server URL from get_ui_server_url().
            headers: Auth headers from get_auth_headers().
            verify_ssl: Whether to verify SSL certificates.
        """
        self.iapi = f"{ui_server}/api/ui/interactive"
        self.headers = headers
        self.verify = verify_ssl

    def start_session(self) -> None:
        """Start a session with response-window handling enabled."""
        httpx.post(
            f"{self.iapi}/sessions", headers=self.headers, verify=self.verify,
            json={"ResponseWindowHandlingEnabled": True},
        ).raise_for_status()

    def open_window(self, service_name: str) -> str:
        """Open a window and return its window ID."""
        win = httpx.post(
            f"{self.iapi}/v2/window", headers=self.headers, verify=self.verify,
            json={"ServiceName": service_name},
        )
        win.raise_for_status()
        return win.json()["WindowId"]

    def answer_response_windows(self, result: dict, button: str | None = None) -> dict:
        """Answer every popup the last action opened, then return the last result.

        Discovers buttons via GET /v2/tools?windowId= (the tools endpoint takes
        ?windowId=, NOT ?id=), then clicks via POST /v2/tools with the POPUP's
        window ID. If button is None, picks the first proceed-style button.

        Args:
            result: The blocked result carrying windowopened events.
            button: Specific button to click, or None for the first proceed button.

        Returns:
            dict: The result of the last button click.
        """
        for popup_id in popup_ids(result):
            tools = httpx.get(
                f"{self.iapi}/v2/tools", params={"windowId": popup_id},
                headers=self.headers, verify=self.verify,
            )
            tools.raise_for_status()
            available = [t.get("Name") or t.get("ToolName") for t in tools.json()]
            pick = button
            if pick is None:  # prefer common proceed buttons
                pick = next((b for b in ("cb_ok", "cb_1", "cb_yes") if b in available), None)
            if pick is None or pick not in available:
                raise RuntimeError(f"Popup {popup_id}: buttons {available}, wanted {button}")
            click = httpx.post(
                f"{self.iapi}/v2/tools", headers=self.headers, verify=self.verify,
                json={"WindowId": popup_id, "ToolName": pick},
            )
            click.raise_for_status()
            result = click.json()
        return result

    def change(self, window_id: str, tab: str, dw: str, field: str, value: str,
               answer: str | None = None) -> dict:
        """Change one field; answer the popup it triggers (if any) with answer.

        Args:
            window_id: Target window ID.
            tab: TabName of the field.
            dw: DatawindowName (required on P21 25.2+).
            field: Field name to change.
            value: New value.
            answer: Button to answer a triggered popup with, or None for auto.

        Returns:
            dict: Final result after any popups were answered.

        Raises:
            RuntimeError: When the change comes back as a Failure.
        """
        resp = httpx.put(
            f"{self.iapi}/v2/change", headers=self.headers, verify=self.verify,
            json={"WindowId": window_id, "List": [{
                "TabName": tab, "DatawindowName": dw,  # DatawindowName required on 25.2+
                "FieldName": field, "Value": value,
            }]},
        )
        resp.raise_for_status()
        result = resp.json()
        if result.get("Status") in (2, "Failure"):
            raise RuntimeError(f"{field}: {result.get('Messages')}")
        if is_blocked(result):
            result = self.answer_response_windows(result, answer)
        return result

    def tab(self, window_id: str, page_name: str) -> None:
        """Switch the window's active tab page."""
        httpx.put(
            f"{self.iapi}/v2/tab", headers=self.headers, verify=self.verify,
            json={"WindowId": window_id, "PageName": page_name},
        ).raise_for_status()

    def save(self, window_id: str) -> dict:
        """Save the window; v2 body is the bare window-ID string, not an object.

        Follow-on prompts are answered with their proceed button.

        Raises:
            RuntimeError: When the save comes back as a Failure.
        """
        resp = httpx.put(f"{self.iapi}/v2/data", headers=self.headers,
                         verify=self.verify, json=window_id)
        resp.raise_for_status()
        result = resp.json()
        while is_blocked(result):  # follow-on prompts: answer with proceed button
            result = self.answer_response_windows(result)
        if result.get("Status") in (2, "Failure"):
            raise RuntimeError(f"Save failed: {result.get('Messages')}")
        return result

    def get_data(self, window_id: str) -> list[dict]:
        """Return the datawindows on the window's ACTIVE surface."""
        data = httpx.get(
            f"{self.iapi}/v2/data", params={"id": window_id},
            headers=self.headers, verify=self.verify,
        )
        data.raise_for_status()
        return data.json()

    def cleanup(self, window_id: str | None) -> None:
        """Close the window and end the session (window uses ?id=)."""
        if window_id:
            httpx.delete(f"{self.iapi}/v2/window", params={"id": window_id},
                         headers=self.headers, verify=self.verify)
        httpx.delete(f"{self.iapi}/sessions", headers=self.headers, verify=self.verify)


def run_flow(session: InteractiveOrderSession) -> str | None:
    """Drive the full order-entry flow and return the generated order_no.

    Args:
        session: Connected InteractiveOrderSession.

    Returns:
        str | None: The generated order number, if it could be read back.
    """
    session.start_session()
    window_id = session.open_window("Order")
    order_no = None
    try:
        # Header -- TABPAGE_1 / datawindow "order". quote OFF = real order.
        session.change(window_id, "TABPAGE_1", "order", "quote", "OFF")
        session.change(window_id, "TABPAGE_1", "order", "sales_loc_id", SALES_LOC_ID)
        session.change(window_id, "TABPAGE_1", "order", "source_loc_id", SOURCE_LOC_ID)
        session.change(window_id, "TABPAGE_1", "order", "customer_id", CUSTOMER_ID)
        session.change(window_id, "TABPAGE_1", "order", "ship_to_id", SHIP_TO_ID)
        session.change(window_id, "TABPAGE_1", "order", "contact_id", CONTACT_ID)
        # Dates fire the w_response_common date-cascade prompt even on a NEW order
        session.change(window_id, "TABPAGE_1", "order", "order_date", ORDER_DATE,
                       answer="cb_ok")
        session.change(window_id, "TABPAGE_1", "order", "requested_date", REQUESTED_DATE,
                       answer="cb_ok")
        session.change(window_id, "TABPAGE_1", "order", "po_no", PO_NO)
        session.change(window_id, "TABPAGE_1", "order", "taker", TAKER)

        # Lines tab
        session.tab(window_id, "TP_ITEMS")

        # Item on the EXISTING items row (no /v2/row add for the first line).
        # Assembly prompt: cb_1 = Yes (explode / link prod order).
        session.change(window_id, "TP_ITEMS", "items", "oe_order_item_id",
                       ASSEMBLY_ITEM_ID, answer="cb_1")
        session.change(window_id, "TP_ITEMS", "items", "unit_quantity", QUANTITY)

        # Save -- v2 body is the bare window-ID string (an object => 422)
        session.save(window_id)

        # Read order_no back. GET /v2/data returns the ACTIVE surface --
        # switch back to the header tab first.
        session.tab(window_id, "TABPAGE_1")
        for dw in session.get_data(window_id):
            if dw.get("Name") == "order":
                row = dw["Data"][dw.get("ActiveRow", 0)]
                order_no = row[dw["Columns"].index("order_no")]
                print(f"Created order_no: {order_no}")
    finally:
        session.cleanup(window_id)
    return order_no


def verify_order(config, headers: dict, order_no: str) -> None:
    """Read back the order lines and print their assembly codes.

    Codes: B = kit parent, N = component, P = production-order line,
    S = build-to-stock allocation.

    Args:
        config: Loaded P21Config.
        headers: Auth headers.
        order_no: Order number to verify.
    """
    resp = httpx.get(
        f"{config.base_url}/odataservice/odata/table/oe_line",
        params={"$filter": f"order_no eq '{order_no}'"},
        headers=headers, verify=config.verify_ssl, follow_redirects=True,
    )
    resp.raise_for_status()
    print("\nVerify (oe_line assembly codes):")
    for line in resp.json()["value"]:
        print(f"  line {line.get('line_no')}: assembly={line.get('assembly')} "
              f"qty_ordered={line.get('qty_ordered')}")


def main() -> None:
    """Entry point: print the call plan (dry run) or run the full flow."""
    parser = argparse.ArgumentParser(
        description="Order with an assembly line (docs/recipes/order-with-assembly.md)")
    parser.add_argument("--execute", action="store_true",
                        help="Run the full Interactive API flow (default: print the call plan)")
    args = parser.parse_args()

    print("Recipe - Order with an Assembly Line (Interactive API)")
    print("=" * 60)

    if not args.execute:
        print("\nDRY RUN - no session is opened.\n")
        print(CALL_PLAN.format(
            iapi="{ui_server}/api/ui/interactive",
            sales_loc=SALES_LOC_ID, source_loc=SOURCE_LOC_ID,
            customer=CUSTOMER_ID, ship_to=SHIP_TO_ID, contact=CONTACT_ID,
            order_date=ORDER_DATE, req_date=REQUESTED_DATE,
            po_no=PO_NO, taker=TAKER, item=ASSEMBLY_ITEM_ID, qty=QUANTITY,
        ))
        print("Re-run with --execute to open the session and enter the order.")
        return

    config = load_config()
    token_data = get_token(config)
    headers = get_auth_headers(token_data["AccessToken"])
    ui_server = get_ui_server_url(config.base_url, token_data["AccessToken"], config.verify_ssl)
    print(f"UI Server: {ui_server}")

    session = InteractiveOrderSession(ui_server, headers, config.verify_ssl)
    order_no = run_flow(session)

    if order_no:
        verify_order(config, headers, order_no)
    else:
        print("Could not read order_no back from the window data")


if __name__ == "__main__":
    main()
