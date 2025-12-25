"""
Interactive API - Save and Close

Demonstrates a complete workflow: open, modify, save, and close.

This is the typical pattern for creating records via the Interactive API.

Usage:
    python scripts/interactive/04_save_and_close.py
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
    """Complete Interactive API session manager."""

    def __init__(self, ui_server_url: str, headers: dict, verify_ssl: bool):
        self.ui_server_url = ui_server_url
        self.headers = headers
        self.verify_ssl = verify_ssl
        self.client = httpx.Client(verify=verify_ssl, timeout=60.0, follow_redirects=True)

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
        response = self.client.put(
            f"{self.ui_server_url}/api/ui/interactive/v1/change",
            headers=self.headers,
            json={"WindowId": window_id, "ChangeRequests": changes}
        )
        response.raise_for_status()
        return response.json()

    def change_tab(self, window_id: str, tab_name: str) -> dict:
        response = self.client.put(
            f"{self.ui_server_url}/api/ui/interactive/v1/tab",
            headers=self.headers,
            json={"WindowId": window_id, "PagePath": {"PageName": tab_name}}
        )
        response.raise_for_status()
        return response.json()

    def save_data(self, window_id: str) -> dict:
        """Save the data in the window."""
        response = self.client.put(
            f"{self.ui_server_url}/api/ui/interactive/v1/data",
            headers=self.headers,
            json={"WindowId": window_id}
        )
        response.raise_for_status()
        return response.json()

    def get_data(self, window_id: str) -> dict:
        """Get current data from window."""
        response = self.client.get(
            f"{self.ui_server_url}/api/ui/interactive/v1/data",
            params={"windowId": window_id},
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()


def create_price_page(session: InteractiveSession, supplier_id: int,
                       product_group: str, description: str, multiplier: float) -> dict:
    """
    Create a price page using the Interactive API.

    This demonstrates the complete workflow:
    1. Open window
    2. Set page type
    3. Fill in form fields
    4. Change to VALUES tab
    5. Set calculation fields
    6. Save
    7. Close window

    Returns:
        Dict with created record info
    """
    window_id = None

    try:
        # Step 1: Open window
        window_data = session.open_window("SalesPricePage")
        window_id = window_data["WindowId"]

        # Step 2: Set page type first (triggers validation rules)
        session.change_data(window_id, [
            {"DataWindowName": "d_form", "FieldName": "price_page_type_cd",
             "Value": "Supplier / Product Group"}
        ])

        # Step 3: Fill in required fields (order matters!)
        session.change_data(window_id, [
            {"DataWindowName": "d_form", "FieldName": "company_id", "Value": "IFPG"},
        ])

        session.change_data(window_id, [
            {"DataWindowName": "d_form", "FieldName": "product_group_id", "Value": product_group},
        ])

        session.change_data(window_id, [
            {"DataWindowName": "d_form", "FieldName": "supplier_id", "Value": str(supplier_id)},
        ])

        session.change_data(window_id, [
            {"DataWindowName": "d_form", "FieldName": "description", "Value": description},
            {"DataWindowName": "d_form", "FieldName": "pricing_method_cd", "Value": "Source"},
            {"DataWindowName": "d_form", "FieldName": "source_price_cd", "Value": "Supplier List Price"},
            {"DataWindowName": "d_form", "FieldName": "effective_date", "Value": datetime.now().strftime("%Y-%m-%d")},
            {"DataWindowName": "d_form", "FieldName": "expiration_date", "Value": "2030-12-31"},
            {"DataWindowName": "d_form", "FieldName": "row_status_flag", "Value": "Active"},
        ])

        # Step 4: Switch to VALUES tab
        session.change_tab(window_id, "VALUES")

        # Step 5: Set calculation method and value
        session.change_data(window_id, [
            {"DataWindowName": "d_values", "FieldName": "calculation_method_cd", "Value": "Multiplier"},
            {"DataWindowName": "d_values", "FieldName": "calculation_value1", "Value": str(multiplier)},
        ])

        # Step 6: Save
        result = session.save_data(window_id)

        # Check for blocked status (response window)
        if result.get("Status") == "Blocked":
            raise RuntimeError("Save blocked by response window - manual intervention needed")

        # Get the saved data to retrieve UID
        data = session.get_data(window_id)

        # Step 7: Close window
        session.close_window(window_id)
        window_id = None

        return {"success": True, "data": data}

    except Exception as e:
        if window_id:
            try:
                session.close_window(window_id)
            except:
                pass
        raise


def main():
    print("Interactive API - Save and Close")
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

        # Create a price page
        timestamp = datetime.now().strftime("%H%M%S")
        description = f"IAPI-SAVE-{timestamp}"

        print(f"\n2. Creating price page: {description}")
        print("-" * 50)

        result = create_price_page(
            session,
            supplier_id=10,
            product_group="FA5",
            description=description,
            multiplier=0.80
        )

        if result["success"]:
            print("\n  SUCCESS: Price page created!")
            print(f"  Description: {description}")
        else:
            print("\n  FAILED to create price page")

    except httpx.HTTPStatusError as e:
        print(f"\n  HTTP Error: {e.response.status_code}")
        print(f"  Response: {e.response.text[:300]}")

    except Exception as e:
        print(f"\n  Error: {type(e).__name__}: {e}")

    finally:
        print("\n3. Ending session...")
        try:
            session.end()
            print("  Session ended")
        except:
            pass

    print("\n" + "=" * 60)
    print("Save and close workflow complete!")


if __name__ == "__main__":
    main()
