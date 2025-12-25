"""
Interactive API - Change Data

Demonstrates changing field values in P21 windows.

To change data you need:
1. Window ID (from opening the window)
2. DataWindow name (from SQL Information dialog in P21)
3. Field name (column name from SQL Information)
4. New value

Usage:
    python scripts/interactive/03_change_data.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from datetime import datetime
from common.auth import get_token, get_auth_headers, get_ui_server_url
from common.config import load_config

import warnings
warnings.filterwarnings("ignore")


class InteractiveSession:
    """Helper class for Interactive API operations."""

    def __init__(self, ui_server_url: str, headers: dict, verify_ssl: bool):
        self.ui_server_url = ui_server_url
        self.headers = headers
        self.verify_ssl = verify_ssl
        self.client = httpx.Client(verify=verify_ssl, timeout=30.0, follow_redirects=True)

    def start(self):
        response = self.client.post(
            f"{self.ui_server_url}/api/ui/interactive/sessions/",
            headers=self.headers,
            json={"ResponseWindowHandlingEnabled": False}
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
        """
        Change field values in a window.

        Args:
            window_id: The window ID
            changes: List of dicts with DataWindowName, FieldName, Value

        Returns:
            API response
        """
        payload = {
            "WindowId": window_id,
            "ChangeRequests": changes
        }

        response = self.client.put(
            f"{self.ui_server_url}/api/ui/interactive/v1/change",
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()

    def change_tab(self, window_id: str, tab_name: str) -> dict:
        """Switch to a different tab."""
        payload = {
            "WindowId": window_id,
            "PagePath": {"PageName": tab_name}
        }

        response = self.client.put(
            f"{self.ui_server_url}/api/ui/interactive/v1/tab",
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()

    def get_data(self, window_id: str) -> dict:
        """Get the current data from a window."""
        response = self.client.get(
            f"{self.ui_server_url}/api/ui/interactive/v1/data",
            params={"windowId": window_id},
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()


def main():
    print("Interactive API - Change Data")
    print("=" * 60)

    config = load_config()
    token_data = get_token(config)
    headers = get_auth_headers(token_data["AccessToken"])
    ui_server_url = get_ui_server_url(config.base_url, token_data["AccessToken"], config.verify_ssl)

    print(f"UI Server: {ui_server_url}")

    session = InteractiveSession(ui_server_url, headers, config.verify_ssl)

    try:
        # Start session
        print("\n1. Starting session...")
        session.start()
        print("  Session started")

        # Open window
        print("\n2. Opening SalesPricePage window...")
        window_data = session.open_window("SalesPricePage")
        window_id = window_data["WindowId"]
        print(f"  Window ID: {window_id}")

        # Example 1: Change a single field
        print("\n3. Changing single field:")
        print("-" * 50)

        result = session.change_data(window_id, [
            {
                "DataWindowName": "d_form",
                "FieldName": "price_page_type_cd",
                "Value": "Supplier / Product Group"
            }
        ])
        print(f"  Changed price_page_type_cd")
        print(f"  Status: {result.get('Status', 'Unknown')}")

        # Example 2: Change multiple fields
        print("\n4. Changing multiple fields:")
        print("-" * 50)

        timestamp = datetime.now().strftime("%H%M%S")
        changes = [
            {"DataWindowName": "d_form", "FieldName": "company_id", "Value": "IFPG"},
            {"DataWindowName": "d_form", "FieldName": "supplier_id", "Value": "10"},
            {"DataWindowName": "d_form", "FieldName": "product_group_id", "Value": "FA5"},
            {"DataWindowName": "d_form", "FieldName": "description", "Value": f"IAPI-TEST-{timestamp}"},
        ]

        result = session.change_data(window_id, changes)
        print(f"  Changed {len(changes)} fields")
        print(f"  Status: {result.get('Status', 'Unknown')}")

        # Show what was changed
        for change in changes:
            print(f"    {change['FieldName']}: {change['Value']}")

        # Example 3: Change tab and then change fields
        print("\n5. Changing to VALUES tab:")
        print("-" * 50)

        result = session.change_tab(window_id, "VALUES")
        print(f"  Tab changed to VALUES")

        # Change fields on new tab
        result = session.change_data(window_id, [
            {"DataWindowName": "d_values", "FieldName": "calculation_method_cd", "Value": "Multiplier"},
            {"DataWindowName": "d_values", "FieldName": "calculation_value1", "Value": "0.75"},
        ])
        print(f"  Changed calculation fields")

        # Get current data
        print("\n6. Getting current window data:")
        print("-" * 50)

        data = session.get_data(window_id)
        print(f"  Retrieved data for window {window_id}")

        # Note: Not saving - just demonstrating change operations

    except httpx.HTTPStatusError as e:
        print(f"\n  HTTP Error: {e.response.status_code}")
        print(f"  Response: {e.response.text[:300]}")

    except Exception as e:
        print(f"\n  Error: {type(e).__name__}: {e}")

    finally:
        print("\n7. Cleanup:")
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
    print("Change data examples complete!")
    print("\nTo find field names in P21:")
    print("1. Right-click on field in P21 web client")
    print("2. Select Help > SQL Information")
    print("3. Note the DataWindow and Column names")


if __name__ == "__main__":
    main()
