"""
Interactive API - Open Window

Demonstrates opening P21 windows via the Interactive API.

Windows can be opened by:
- ServiceName (e.g., "SalesPricePage", "Order")
- Title (e.g., "Sales Price Page Entry")

Usage:
    python scripts/interactive/02_open_window.py
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
    """Helper class for managing Interactive API sessions."""

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
        return response.json()

    def end(self):
        self.client.delete(
            f"{self.ui_server_url}/api/ui/interactive/sessions/",
            headers=self.headers
        )
        self.client.close()

    def open_window(self, service_name: str = None, title: str = None) -> dict:
        """Open a window by service name or title."""
        if service_name:
            payload = {"ServiceName": service_name}
        elif title:
            payload = {"Title": title}
        else:
            raise ValueError("Must specify service_name or title")

        response = self.client.post(
            f"{self.ui_server_url}/api/ui/interactive/v2/window",
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()

    def get_window(self, window_id: str) -> dict:
        """Get the current state of a window."""
        response = self.client.get(
            f"{self.ui_server_url}/api/ui/interactive/v2/window",
            params={"windowId": window_id},
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def close_window(self, window_id: str) -> None:
        """Close a window."""
        response = self.client.delete(
            f"{self.ui_server_url}/api/ui/interactive/v2/window",
            params={"windowId": window_id},
            headers=self.headers
        )
        response.raise_for_status()


def main():
    print("Interactive API - Open Window")
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
        print("-" * 50)
        session.start()
        print("  Session started")

        # Example 1: Open window by service name
        print("\n2. Opening window by ServiceName:")
        print("-" * 50)

        window_data = session.open_window(service_name="SalesPricePage")

        window_id = window_data.get("WindowId")
        title = window_data.get("Title", "Unknown")

        print(f"  Window opened!")
        print(f"    Window ID: {window_id}")
        print(f"    Title: {title}")

        # Show available data elements
        data_elements = window_data.get("DataElements", [])
        if data_elements:
            print(f"\n  DataElements ({len(data_elements)}):")
            for elem in data_elements[:3]:
                print(f"    - {elem.get('Name', 'Unknown')}")

        # Get window state
        print("\n3. Getting window state:")
        print("-" * 50)

        state = session.get_window(window_id)
        print(f"  Window ID: {state.get('WindowId')}")
        print(f"  Status: {state.get('Status', 'Unknown')}")

        # Close window
        print("\n4. Closing window:")
        print("-" * 50)

        session.close_window(window_id)
        print(f"  Window closed")

    except httpx.HTTPStatusError as e:
        print(f"\n  HTTP Error: {e.response.status_code}")
        print(f"  Response: {e.response.text[:300]}")

    except Exception as e:
        print(f"\n  Error: {type(e).__name__}: {e}")

    finally:
        # Always end session
        print("\n5. Ending session:")
        print("-" * 50)
        try:
            session.end()
            print("  Session ended")
        except:
            pass

    print("\n" + "=" * 60)
    print("Window operations complete!")
    print("\nCommon windows and their service names:")
    print("  - SalesPricePage: Sales Price Page Entry")
    print("  - Order: Order Entry")
    print("  - Customer: Customer Maintenance")
    print("  - Supplier: Supplier Maintenance")


if __name__ == "__main__":
    main()
