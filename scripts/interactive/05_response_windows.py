"""
Interactive API - Response Windows

Demonstrates handling response windows (dialogs) that can pop up
during Interactive API operations.

IMPORTANT FINDINGS (January 2026):
==================================
1. ResponseWindowHandlingEnabled: false = Auto-answer with DEFAULT (usually "Yes")
   ResponseWindowHandlingEnabled: true = Dialog events returned to your code

2. When a dialog opens with ResponseWindowHandlingEnabled: true:
   - Status is numeric 3 (not string "Blocked")
   - Events array contains "windowopened" with dialog's windowid

3. KNOWN LIMITATION: There is NO documented endpoint to respond to message
   box dialogs (w_message windows). You cannot programmatically click "Yes"
   or "No" buttons on these dialogs.

4. Attempting to continue while dialog is open results in error:
   "Unable to process request on window X since response window Y blocks it"

Usage:
    python scripts/interactive/05_response_windows.py
"""

import sys
from pathlib import Path

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
        self.client.delete(
            f"{self.ui_server_url}/api/ui/interactive/v2/window",
            params={"windowId": window_id},
            headers=self.headers
        )

    def change_data_v2(self, window_id: str, changes: list) -> dict:
        """Change data using v2 API (List format)."""
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

    def save_data(self, window_id: str) -> dict:
        response = self.client.put(
            f"{self.ui_server_url}/api/ui/interactive/v2/data",
            headers=self.headers,
            json=window_id  # v2 API takes just the window ID
        )
        response.raise_for_status()
        return response.json()

    def try_response_window_endpoints(self, dialog_window_id: str) -> dict:
        """
        Attempt various endpoints to respond to a dialog.

        KNOWN ISSUE: None of these endpoints work as of P21 25.2.x
        This method documents what was tested.
        """
        results = {}

        # Endpoint 1: PUT responsewindow (singular)
        try:
            response = self.client.put(
                f"{self.ui_server_url}/api/ui/interactive/v2/responsewindow",
                headers=self.headers,
                json={"ResponseWindowId": dialog_window_id, "Button": "No"}
            )
            results["PUT /v2/responsewindow"] = response.status_code
        except Exception as e:
            results["PUT /v2/responsewindow"] = str(e)

        # Endpoint 2: PUT responsewindows (plural)
        try:
            response = self.client.put(
                f"{self.ui_server_url}/api/ui/interactive/v2/responsewindows",
                headers=self.headers,
                json={"ResponseWindowId": dialog_window_id, "Button": "No"}
            )
            results["PUT /v2/responsewindows"] = response.status_code
        except Exception as e:
            results["PUT /v2/responsewindows"] = str(e)

        # Endpoint 3: DELETE window with button param
        try:
            response = self.client.delete(
                f"{self.ui_server_url}/api/ui/interactive/v2/window",
                params={"windowId": dialog_window_id, "button": "No"},
                headers=self.headers
            )
            results["DELETE /v2/window?button=No"] = response.status_code
        except Exception as e:
            results["DELETE /v2/window?button=No"] = str(e)

        # Endpoint 4: POST button
        try:
            response = self.client.post(
                f"{self.ui_server_url}/api/ui/interactive/v2/button",
                headers=self.headers,
                json={"WindowId": dialog_window_id, "ButtonName": "No"}
            )
            results["POST /v2/button"] = response.status_code
        except Exception as e:
            results["POST /v2/button"] = str(e)

        return results


def check_for_response_window(result: dict) -> str | None:
    """
    Check if a response window was opened.

    With ResponseWindowHandlingEnabled: true, dialogs return:
    - Status: 3 (numeric, not string "Blocked")
    - Events array with "windowopened" event

    Returns:
        Window ID of response window, or None if no response window
    """
    # Check for Status 3 (dialog opened)
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


def main():
    print("Interactive API - Response Windows")
    print("=" * 60)
    print()
    print("⚠️  IMPORTANT: As of P21 25.2.x, there is NO documented endpoint")
    print("    to respond to message box dialogs programmatically.")
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
        # Use an item that exists in your P21 - adjust as needed
        result = session.change_data_v2(window_id, [
            {"TabName": "TABPAGE_1", "FieldName": "item_id", "Value": "CBCALHN"}
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
        result = session.change_data_v2(window_id, [
            {"TabName": "TABPAGE_18", "FieldName": "product_group_id",
             "Value": "SU5K", "DatawindowName": "inv_loc_detail"}
        ])
        print(f"  Status: {result.get('Status')}")
        print(f"  Events: {len(result.get('Events', []))} events")

        # Check for dialog
        dialog_id = check_for_response_window(result)
        if dialog_id:
            print(f"\n  ✓ DIALOG DETECTED!")
            print(f"    Dialog Window ID: {dialog_id}")

            # Get dialog info
            dialog_info = session.get_window_info(dialog_id)
            definition = dialog_info.get("Definition", {})
            print(f"    Title: {definition.get('Title')}")
            print(f"    Name: {definition.get('Name')}")

            print("\n6. Attempting to respond to dialog:")
            print("-" * 50)
            print("  Testing various endpoints (all expected to fail)...")

            results = session.try_response_window_endpoints(dialog_id)
            for endpoint, status in results.items():
                print(f"    {endpoint}: {status}")

            print("\n  ⚠️  No working endpoint found to respond 'No' to dialog")
            print("  The dialog will block further operations on the main window")

            print("\n7. Attempting to save (will fail while dialog open):")
            print("-" * 50)
            try:
                save_result = session.save_data(window_id)
                print(f"  Save Status: {save_result.get('Status')}")
            except httpx.HTTPStatusError as e:
                error_text = e.response.text[:200] if hasattr(e.response, 'text') else str(e)
                print(f"  Expected error: {e.response.status_code}")
                print(f"  Error indicates dialog is blocking: Yes" if "blocks it" in error_text else f"  {error_text}")

        else:
            print("  No dialog opened (product group may already be set to target value)")
            print("  Try changing to a different product_group_id to trigger dialog")

    except httpx.HTTPStatusError as e:
        print(f"\n  HTTP Error: {e.response.status_code}")
        print(f"  Response: {e.response.text[:300]}")

    except Exception as e:
        print(f"\n  Error: {type(e).__name__}: {e}")

    finally:
        print("\n8. Cleanup:")
        print("-" * 50)
        if window_id:
            try:
                session.close_window(window_id)
                print("  Window closed")
            except:
                print("  Window close failed (may have been blocked by dialog)")
        try:
            session.end()
            print("  Session ended")
        except:
            pass

    print("\n" + "=" * 60)
    print("SUMMARY - Response Window Handling")
    print("=" * 60)
    print("""
Key findings:
1. ResponseWindowHandlingEnabled: false = auto-answer with DEFAULT (usually Yes)
2. ResponseWindowHandlingEnabled: true = dialog info returned, but...
3. NO KNOWN ENDPOINT to respond "No" to message box dialogs
4. Dialogs block the main window until dismissed

Impact on Product Group changes:
- Changing product_group_id triggers GL account dialog
- Default "Yes" overwrites GL, revenue, and COS account fields
- Cannot programmatically answer "No" to preserve existing GL accounts

Workarounds:
- Accept GL changes (not ideal)
- Restore GL accounts via direct SQL after API change
- Contact Epicor for response window endpoint documentation
    """)


if __name__ == "__main__":
    main()
