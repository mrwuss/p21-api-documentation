"""
Interactive API - Response Windows

Demonstrates handling response windows (dialogs) that can pop up
during Interactive API operations.

HOW IT WORKS (verified February 2026):
=======================================
1. ResponseWindowHandlingEnabled: false = Auto-answer with DEFAULT (usually "Yes")
   ResponseWindowHandlingEnabled: true = Dialog events returned to your code

2. When a dialog opens with ResponseWindowHandlingEnabled: true:
   - Status is numeric 3 (Blocked; ResultStatus: None=0, Success=1,
     Failure=2, Blocked=3)
   - Events array contains "windowopened" with the dialog's windowid

3. ANSWERING THE DIALOG (the verified path):
   - Extract the popup's window ID from the "windowopened" event
   - GET /api/ui/interactive/v2/tools?windowId={popupId} to discover
     the available buttons (note: /v2/tools uses ?windowId=, unlike
     the other v2 endpoints which use ?id=)
   - POST /api/ui/interactive/v2/tools with the POPUP's window ID and
     the chosen ToolName (e.g., cb_ok, cb_cancel)

4. Form-style response windows are also EDITABLE: send change requests
   against the popup's window ID with TabName: null (verified on
   w_notepad_response_lite - see docs/04-Interactive-API.md).

5. REMAINING LIMITATION: message box dialogs (w_message windows) are the
   weak spot - their fields are NOT editable, the cb_1/cb_2/cb_3 button
   names carry no documented Yes/No mapping (verify the effect with a
   read-back before trusting an answer), and with handling disabled they
   auto-answer with the default.

6. Attempting to continue on the parent while a dialog is open errors:
   "Unable to process request on window X since response window Y blocks it"

NOTE: this example pokes at inv_loc fields only to trigger a dialog and
never saves. For real inv_loc changes, prefer the Inventory REST API
(docs/11-Inventory-REST-API.md) over the Item window.

Usage:
    python examples/python/interactive/05_response_windows.py
"""

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from common.auth import get_token, get_auth_headers, get_ui_server_url
from common.config import load_config

import warnings
warnings.filterwarnings("ignore")


class InteractiveSession:
    """Interactive API session with response window handling."""

    def __init__(self, ui_server_url: str, headers: dict, verify_ssl: bool):
        self.ui_server_url = ui_server_url
        self.headers = headers
        self.verify_ssl = verify_ssl
        self.client = httpx.Client(verify=verify_ssl, timeout=60.0, follow_redirects=True)

    def start(self, response_window_handling: bool = True):
        """Start session.

        Args:
            response_window_handling:
                True = dialogs returned to your code (you must handle them)
                False = dialogs auto-answered with default (usually "Yes")
        """
        response = self.client.post(
            f"{self.ui_server_url}/api/ui/interactive/sessions/",
            headers=self.headers,
            json={"ResponseWindowHandlingEnabled": response_window_handling}
        )
        response.raise_for_status()
        return response.json()

    def end(self):
        self.client.delete(
            f"{self.ui_server_url}/api/ui/interactive/sessions/",
            headers=self.headers
        )
        self.client.close()

    def open_window(self, service_name: str) -> dict:
        response = self.client.post(
            f"{self.ui_server_url}/api/ui/interactive/v2/window",
            headers=self.headers,
            json={"ServiceName": service_name}
        )
        response.raise_for_status()
        return response.json()

    def get_window_info(self, window_id: str) -> dict:
        """Get window definition and data."""
        response = self.client.get(
            f"{self.ui_server_url}/api/ui/interactive/v2/window",
            params={"id": window_id},
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def close_window(self, window_id: str):
        # Note: /v2/window uses ?id= (only /v2/tools uses ?windowId=)
        self.client.delete(
            f"{self.ui_server_url}/api/ui/interactive/v2/window",
            params={"id": window_id},
            headers=self.headers
        )

    def change_data_v2(self, window_id: str, changes: list) -> dict:
        """Change data using v2 API (List format).

        Each change dict needs TabName, DatawindowName (required in
        P21 25.2+), FieldName, Value.
        """
        response = self.client.put(
            f"{self.ui_server_url}/api/ui/interactive/v2/change",
            headers=self.headers,
            json={"WindowId": window_id, "List": changes}
        )
        response.raise_for_status()
        return response.json()

    def change_tab(self, window_id: str, page_name: str) -> dict:
        response = self.client.put(
            f"{self.ui_server_url}/api/ui/interactive/v2/tab",
            headers=self.headers,
            json={"WindowId": window_id, "PageName": page_name}
        )
        response.raise_for_status()
        return response.json()

    def change_row(self, window_id: str, datawindow_name: str, row: int) -> dict:
        response = self.client.put(
            f"{self.ui_server_url}/api/ui/interactive/v2/row",
            headers=self.headers,
            json={"WindowId": window_id, "DatawindowName": datawindow_name, "Row": row}
        )
        response.raise_for_status()
        return response.json()

    def get_tools(self, window_id: str) -> dict:
        """Discover the tools/buttons available on a window.

        IMPORTANT: /v2/tools is the one endpoint that uses ?windowId=
        (all other v2 endpoints use ?id=; sending ?id= here returns
        HTTP 400).
        """
        response = self.client.get(
            f"{self.ui_server_url}/api/ui/interactive/v2/tools",
            params={"windowId": window_id},
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def run_tool(self, window_id: str, tool_name: str, tool_text: str = "") -> dict:
        """Click a tool/button on a window (works on response windows too)."""
        response = self.client.post(
            f"{self.ui_server_url}/api/ui/interactive/v2/tools",
            headers=self.headers,
            json={"WindowId": window_id, "ToolName": tool_name, "ToolText": tool_text}
        )
        response.raise_for_status()
        return response.json()

    # HISTORICAL NOTE (January 2026): before the /v2/tools path was
    # discovered, these endpoints were probed and all failed:
    #   PUT  /api/ui/interactive/v2/responsewindow      -> 404
    #   PUT  /api/ui/interactive/v2/responsewindows     -> 404
    #   DELETE /api/ui/interactive/v2/window?button=No  -> 400
    #   POST /api/ui/interactive/v2/button              -> 404
    # They do not exist - use GET/POST /v2/tools with the popup's
    # window ID instead (see get_tools/run_tool above).


def check_for_response_window(result: dict) -> str | None:
    """
    Check if a response window was opened.

    With ResponseWindowHandlingEnabled: true, dialogs return:
    - Status: 3 (numeric Blocked, not string)
    - Events array with "windowopened" event whose Data is a KV list

    Returns:
        Window ID of response window, or None if no response window
    """
    # Check for Status 3 (Blocked - dialog opened)
    if result.get("Status") != 3:
        return None

    events = result.get("Events", [])
    for event in events:
        if event.get("Name") == "windowopened":
            data = event.get("Data", [])
            # Data is a list of key-value pairs
            for item in data:
                if item.get("Key") == "windowid":
                    return item.get("Value")

    return None


def extract_tool_names(tools_response) -> list[str]:
    """Pull tool names out of a GET /v2/tools response.

    The response is a list of tool objects (or a dict wrapping one);
    each has a Name (e.g., cb_ok, cb_cancel).
    """
    if isinstance(tools_response, dict):
        tools = tools_response.get("Tools") or tools_response.get("List") or []
    else:
        tools = tools_response or []

    names = []
    for tool in tools:
        if isinstance(tool, dict):
            name = tool.get("Name") or tool.get("ToolName")
            if name:
                names.append(name)
        elif isinstance(tool, str):
            names.append(tool)
    return names


def choose_dismiss_button(tool_names: list[str]) -> str | None:
    """Pick a cancel/no-style button so the demo stays read-only."""
    for candidate in ("cb_cancel", "cb_no", "cb_2"):
        if candidate in tool_names:
            return candidate
    # Fall back to any cancel-ish name
    for name in tool_names:
        if "cancel" in name.lower() or name.lower().endswith("_no"):
            return name
    return None


def main():
    print("Interactive API - Response Windows")
    print("=" * 60)
    print()
    print("Verified path: after a Blocked (Status 3) result, answer the")
    print("dialog via GET/POST /v2/tools using the POPUP's window ID.")
    print("w_message boxes are the remaining weak spot (see summary).")
    print()

    config = load_config()
    token_data = get_token(config)
    headers = get_auth_headers(token_data["AccessToken"])
    ui_server_url = get_ui_server_url(config.base_url, token_data["AccessToken"], config.verify_ssl)

    print(f"UI Server: {ui_server_url}")

    session = InteractiveSession(ui_server_url, headers, config.verify_ssl)
    window_id = None

    try:
        print("\n1. Starting session with ResponseWindowHandlingEnabled: TRUE")
        print("-" * 50)
        session_info = session.start(response_window_handling=True)
        print(f"  Session ID: {session_info.get('Id', 'Unknown')}")
        print("  (Dialogs will be returned to our code)")

        print("\n2. Opening Item window:")
        print("-" * 50)
        window_data = session.open_window("Item")
        window_id = window_data["WindowId"]
        print(f"  Window ID: {window_id}")

        print("\n3. Retrieving an item:")
        print("-" * 50)
        # Use an item that exists in your P21 - adjust as needed.
        # DatawindowName is required in P21 25.2+ (Item header = tp_1_dw_1).
        result = session.change_data_v2(window_id, [
            {"TabName": "TABPAGE_1", "DatawindowName": "tp_1_dw_1",
             "FieldName": "item_id", "Value": "WIDGET-001"}
        ])
        print(f"  Status: {result.get('Status')}")
        if result.get("Status") != 1:
            print("  Item not found or error - adjust item_id in script")
            return

        print("\n4. Navigating to Location Detail:")
        print("-" * 50)
        session.change_tab(window_id, "TABPAGE_17")  # Locations list
        session.change_row(window_id, "invloclist", 1)  # Select first row
        session.change_tab(window_id, "TABPAGE_18")  # Location detail
        print("  Now on TABPAGE_18 (Location Detail)")

        print("\n5. Changing product_group_id (may trigger dialog):")
        print("-" * 50)
        # This only edits the window buffer to provoke a dialog - the
        # script never saves. Real inv_loc updates belong on the
        # Inventory REST API (docs/11-Inventory-REST-API.md).
        result = session.change_data_v2(window_id, [
            {"TabName": "TABPAGE_18", "FieldName": "product_group_id",
             "Value": "MISC", "DatawindowName": "inv_loc_detail"}
        ])
        print(f"  Status: {result.get('Status')}")
        print(f"  Events: {len(result.get('Events', []))} events")

        # Check for dialog (Status 3 + windowopened event)
        dialog_id = check_for_response_window(result)
        if dialog_id:
            print("\n  DIALOG DETECTED!")
            print(f"    Dialog Window ID: {dialog_id}")

            # Get dialog info
            dialog_info = session.get_window_info(dialog_id)
            definition = dialog_info.get("Definition", {})
            dialog_name = definition.get("Name") or ""
            print(f"    Title: {definition.get('Title')}")
            print(f"    Name: {dialog_name}")

            print("\n6. Answering the dialog via /v2/tools:")
            print("-" * 50)
            try:
                # Discover the popup's buttons (?windowId= is required here)
                tools_response = session.get_tools(dialog_id)
                tool_names = extract_tool_names(tools_response)
                print(f"  Available tools: {tool_names or '(none)'}")

                button = choose_dismiss_button(tool_names)
                if button:
                    print(f"  Clicking '{button}' on the popup...")
                    answer_result = session.run_tool(dialog_id, button)
                    print(f"  Answer Status: {answer_result.get('Status')} "
                          "(1=Success)")
                    print("  Dialog dismissed - the parent window is unblocked.")
                    if dialog_name == "w_message":
                        print("  CAUTION: on w_message boxes the cb_N-to-Yes/No")
                        print("  mapping is undocumented - verify the effect with")
                        print("  a read-back before trusting the chosen answer.")
                elif tool_names:
                    print("  No cancel/no-style button found; available buttons")
                    print("  can be clicked the same way via run_tool().")
                else:
                    print("  No tools exposed on this popup - it will keep")
                    print("  blocking the parent window until closed.")
            except httpx.HTTPStatusError as e:
                print(f"  Tools call failed: HTTP {e.response.status_code}")
                print(f"  {e.response.text[:200]}")

            print("\n  NOTE: form-style response windows are also editable -")
            print("  send change requests against the popup's window ID with")
            print("  TabName: null (verified on w_notepad_response_lite; see")
            print("  docs/04-Interactive-API.md).")

        else:
            print("  No dialog opened (product group may already be set to target value)")
            print("  Try changing to a different product_group_id to trigger dialog")

    except httpx.HTTPStatusError as e:
        print(f"\n  HTTP Error: {e.response.status_code}")
        print(f"  Response: {e.response.text[:300]}")

    except Exception as e:
        print(f"\n  Error: {type(e).__name__}: {e}")

    finally:
        print("\n7. Cleanup (nothing was saved):")
        print("-" * 50)
        if window_id:
            try:
                session.close_window(window_id)
                print("  Window closed")
            except (httpx.HTTPError, OSError):
                print("  Window close failed (may have been blocked by dialog)")
        try:
            session.end()
            print("  Session ended")
        except (httpx.HTTPError, OSError):
            pass

    print("\n" + "=" * 60)
    print("SUMMARY - Response Window Handling")
    print("=" * 60)
    print("""
Key findings:
1. ResponseWindowHandlingEnabled: false = auto-answer with DEFAULT (usually Yes)
2. ResponseWindowHandlingEnabled: true = Status 3 (Blocked) + a
   "windowopened" event carrying the popup's window ID
3. Answer the popup via GET /v2/tools?windowId={popupId} to discover
   buttons, then POST /v2/tools with the chosen ToolName
4. Form-style response windows are editable with TabName: null
5. REMAINING LIMITATION: w_message boxes - fields are not editable, the
   cb_1/cb_2/cb_3 button names have no documented Yes/No mapping (verify
   with a read-back before trusting an answer), and with handling
   disabled they auto-answer with the default

Historical note (January 2026): PUT /v2/responsewindow(s),
DELETE /v2/window?button=No, and POST /v2/button were all probed and
do not exist (404/400). Use /v2/tools instead.

Impact on Product Group changes:
- Changing product_group_id can trigger a GL account dialog; if it is a
  w_message box, the default answer ("Yes") overwrites GL, revenue, and
  COS account fields
- For inv_loc changes, prefer the Inventory REST API
  (docs/11-Inventory-REST-API.md) - it is the verified update path and
  avoids the dialog entirely
    """)


if __name__ == "__main__":
    main()
