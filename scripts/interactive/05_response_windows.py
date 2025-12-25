"""
Interactive API - Response Windows

Demonstrates handling response windows (dialogs) that can pop up
during Interactive API operations.

When a response window opens:
1. The main operation returns Status: "Blocked"
2. Check Events array for "windowopened" event
3. Get the new window ID
4. Handle the dialog
5. Close it to resume

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

    def start(self):
        response = self.client.post(
            f"{self.ui_server_url}/api/ui/interactive/sessions/",
            headers=self.headers,
            json={"ResponseWindowHandlingEnabled": True}  # Enable response window handling
        )
        response.raise_for_status()

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

    def close_window(self, window_id: str):
        self.client.delete(
            f"{self.ui_server_url}/api/ui/interactive/v2/window",
            params={"windowId": window_id},
            headers=self.headers
        )

    def change_data(self, window_id: str, changes: list) -> dict:
        response = self.client.put(
            f"{self.ui_server_url}/api/ui/interactive/v1/change",
            headers=self.headers,
            json={"WindowId": window_id, "ChangeRequests": changes}
        )
        response.raise_for_status()
        return response.json()

    def save_data(self, window_id: str) -> dict:
        response = self.client.put(
            f"{self.ui_server_url}/api/ui/interactive/v1/data",
            headers=self.headers,
            json={"WindowId": window_id}
        )
        response.raise_for_status()
        return response.json()

    def run_tool(self, window_id: str, tool_name: str, tool_text: str) -> dict:
        """Run a button/tool in the window."""
        response = self.client.post(
            f"{self.ui_server_url}/api/ui/interactive/v1/tools",
            headers=self.headers,
            json={
                "WindowId": window_id,
                "ToolName": tool_name,
                "ToolText": tool_text
            }
        )
        response.raise_for_status()
        return response.json()

    def get_tools(self, window_id: str) -> list:
        """Get available tools (buttons) for a window."""
        response = self.client.get(
            f"{self.ui_server_url}/api/ui/interactive/v1/tools",
            params={"windowId": window_id},
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()


def check_for_response_window(result: dict) -> str:
    """
    Check if a response window was opened.

    Returns:
        Window ID of response window, or None if no response window
    """
    if result.get("Status") != "Blocked":
        return None

    events = result.get("Events", [])
    for event in events:
        if event.get("Name") == "windowopened":
            data = event.get("Data", {})
            return data.get("WindowId")

    return None


def main():
    print("Interactive API - Response Windows")
    print("=" * 60)

    config = load_config()
    token_data = get_token(config)
    headers = get_auth_headers(token_data["AccessToken"])
    ui_server_url = get_ui_server_url(config.base_url, token_data["AccessToken"], config.verify_ssl)

    print(f"UI Server: {ui_server_url}")

    session = InteractiveSession(ui_server_url, headers, config.verify_ssl)

    try:
        print("\n1. Starting session with ResponseWindowHandlingEnabled:")
        print("-" * 50)
        session.start()
        print("  Session started")

        print("\n2. Opening SalesPricePage window:")
        print("-" * 50)
        window_data = session.open_window("SalesPricePage")
        window_id = window_data["WindowId"]
        print(f"  Window ID: {window_id}")

        # Check for response window on open
        response_window = check_for_response_window(window_data)
        if response_window:
            print(f"  [!] Response window detected: {response_window}")

        print("\n3. Getting available tools:")
        print("-" * 50)
        tools = session.get_tools(window_id)
        print(f"  Found {len(tools)} tools")
        for tool in tools[:5]:  # Show first 5
            name = tool.get("ToolName", "Unknown")
            text = tool.get("ToolText", "Unknown")
            print(f"    - {name}: {text}")

        print("\n4. Simulating an operation that might trigger a dialog:")
        print("-" * 50)

        # Make a change that could trigger validation
        result = session.change_data(window_id, [
            {"DataWindowName": "d_form", "FieldName": "price_page_type_cd",
             "Value": "Supplier / Product Group"}
        ])

        # Check for response window
        response_window = check_for_response_window(result)
        if response_window:
            print(f"  Response window opened: {response_window}")
            print("  Handling response window...")

            # Example: Get info about the response window
            response_tools = session.get_tools(response_window)
            print(f"  Response window has {len(response_tools)} tools")

            # Close the response window
            session.close_window(response_window)
            print("  Response window closed")
        else:
            print(f"  No response window (Status: {result.get('Status', 'Unknown')})")

        print("\n5. Response window handling pattern:")
        print("-" * 50)
        print("""
  def handle_operation(session, window_id, operation):
      result = operation()

      response_window = check_for_response_window(result)
      if response_window:
          # Handle the dialog
          # Option 1: Click OK/Cancel
          session.run_tool(response_window, "cb_ok", "OK")

          # Option 2: Fill in form and submit
          session.change_data(response_window, [...])
          session.run_tool(response_window, "cb_finish", "Finish")

          # Close if needed
          session.close_window(response_window)

      return result
        """)

    except httpx.HTTPStatusError as e:
        print(f"\n  HTTP Error: {e.response.status_code}")
        print(f"  Response: {e.response.text[:300]}")

    except Exception as e:
        print(f"\n  Error: {type(e).__name__}: {e}")

    finally:
        print("\n6. Cleanup:")
        print("-" * 50)
        try:
            session.close_window(window_id)
            print("  Window closed")
        except:
            pass
        try:
            session.end()
            print("  Session ended")
        except:
            pass

    print("\n" + "=" * 60)
    print("Response window examples complete!")
    print("\nKey points:")
    print("- Check Status: 'Blocked' indicates a response window")
    print("- Find window ID in Events array")
    print("- Handle the dialog before continuing")
    print("- Response windows block the original operation")


if __name__ == "__main__":
    main()
