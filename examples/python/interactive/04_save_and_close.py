"""
Interactive API - Save and Close (v2)

Demonstrates a complete workflow: open, modify, save, and close.

This is the typical pattern for creating records via the Interactive API.

IMPORTANT: As of P21 25.2, DatawindowName is REQUIRED in change requests.

By default the script drives the window read-only and SKIPS the save
(field changes are discarded when the window closes). Pass --execute
to actually save the record.

Usage:
    python examples/python/interactive/04_save_and_close.py            # no save
    python examples/python/interactive/04_save_and_close.py --execute  # saves
"""

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
import httpx
from datetime import datetime
from common.auth import get_token, get_auth_headers, get_ui_server_url
from common.config import load_config

import warnings
warnings.filterwarnings("ignore")


class InteractiveSession:
    """Complete Interactive API v2 session manager."""

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
        # Note: /v2/window uses ?id= (only /v2/tools uses ?windowId=)
        self.client.delete(
            f"{self.ui_server_url}/api/ui/interactive/v2/window",
            params={"id": window_id},
            headers=self.headers
        )

    def change_data(self, window_id: str, changes: list) -> dict:
        """Change field values using v2 API.

        Args:
            window_id: The window ID
            changes: List of dicts with TabName, DatawindowName, FieldName, Value
        """
        response = self.client.put(
            f"{self.ui_server_url}/api/ui/interactive/v2/change",
            headers=self.headers,
            json={"WindowId": window_id, "List": changes}
        )
        response.raise_for_status()
        return response.json()

    def change_tab(self, window_id: str, tab_name: str) -> dict:
        """Switch to a different tab using v2 API."""
        response = self.client.put(
            f"{self.ui_server_url}/api/ui/interactive/v2/tab",
            headers=self.headers,
            json={"WindowId": window_id, "PageName": tab_name}
        )
        response.raise_for_status()
        return response.json()

    def save_data(self, window_id: str) -> dict:
        """Save the data in the window using v2 API.

        Note: v2 save takes just the window ID string, not a dict.
        """
        response = self.client.put(
            f"{self.ui_server_url}/api/ui/interactive/v2/data",
            headers=self.headers,
            json=window_id  # v2: just the GUID string
        )
        response.raise_for_status()
        return response.json()

    def get_data(self, window_id: str) -> dict:
        """Get current data from window."""
        # Note: /v2/data uses ?id= (only /v2/tools uses ?windowId=)
        response = self.client.get(
            f"{self.ui_server_url}/api/ui/interactive/v2/data",
            params={"id": window_id},
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()


def create_price_page(session: InteractiveSession, supplier_id: int,
                       product_group: str, description: str, multiplier: float,
                       execute: bool = False) -> dict:
    """
    Create a price page using the Interactive API v2.

    This demonstrates the complete workflow:
    1. Open window
    2. Set page type
    3. Fill in form fields
    4. Change to VALUES tab
    5. Set calculation fields
    6. Save (only when execute=True; otherwise skipped and discarded)
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
            {"TabName": "FORM", "DatawindowName": "form",
             "FieldName": "price_page_type_cd", "Value": "Supplier / Product Group"}
        ])

        # Step 3: Fill in required fields (order matters!)
        session.change_data(window_id, [
            {"TabName": "FORM", "DatawindowName": "form",
             "FieldName": "company_id", "Value": "ACME"},
        ])

        session.change_data(window_id, [
            {"TabName": "FORM", "DatawindowName": "form",
             "FieldName": "product_group_id", "Value": product_group},
        ])

        session.change_data(window_id, [
            {"TabName": "FORM", "DatawindowName": "form",
             "FieldName": "supplier_id", "Value": str(supplier_id)},
        ])

        session.change_data(window_id, [
            {"TabName": "FORM", "DatawindowName": "form",
             "FieldName": "description", "Value": description},
            {"TabName": "FORM", "DatawindowName": "form",
             "FieldName": "pricing_method_cd", "Value": "Source"},
            {"TabName": "FORM", "DatawindowName": "form",
             "FieldName": "source_price_cd", "Value": "Supplier List Price"},
            {"TabName": "FORM", "DatawindowName": "form",
             "FieldName": "effective_date", "Value": datetime.now().strftime("%Y-%m-%d")},
            {"TabName": "FORM", "DatawindowName": "form",
             "FieldName": "expiration_date", "Value": "2030-12-31"},
            {"TabName": "FORM", "DatawindowName": "form",
             "FieldName": "row_status_flag", "Value": "Active"},
        ])

        # Step 4: Switch to VALUES tab
        session.change_tab(window_id, "VALUES")

        # Step 5: Set calculation method and value
        session.change_data(window_id, [
            {"TabName": "VALUES", "DatawindowName": "values",
             "FieldName": "calculation_method_cd", "Value": "Multiplier"},
            {"TabName": "VALUES", "DatawindowName": "values",
             "FieldName": "calculation_value1", "Value": str(multiplier)},
        ])

        # Step 6: Save (gated - skipped on dry runs)
        if not execute:
            print("    DRY RUN: skipping save (window changes are discarded on close)")
            session.close_window(window_id)
            window_id = None
            return {"success": True, "saved": False, "data": None}

        result = session.save_data(window_id)

        # ResultStatus: None=0, Success=1, Failure=2, Blocked=3
        status = result.get("Status")
        if status == 2:
            # Failure - surface the validation messages and bail out
            messages = result.get("Messages") or []
            print("    SAVE FAILED (Status 2):")
            for msg in messages:
                print(f"      - {msg}")
            raise RuntimeError(f"Save failed: {messages or 'no messages returned'}")
        if status == 3:
            raise RuntimeError("Save blocked by response window - manual intervention needed")

        # Get the saved data to retrieve UID
        data = session.get_data(window_id)

        # Step 7: Close window
        session.close_window(window_id)
        window_id = None

        return {"success": True, "saved": True, "data": data}

    except (httpx.HTTPError, OSError, RuntimeError):
        if window_id:
            try:
                session.close_window(window_id)
            except (httpx.HTTPError, OSError):
                pass
        raise


def main():
    parser = argparse.ArgumentParser(description="Interactive API save-and-close workflow")
    parser.add_argument("--execute", action="store_true",
                        help="Actually save the record (default: drive the window read-only, skip save)")
    args = parser.parse_args()

    print("Interactive API - Save and Close (v2)")
    print("=" * 60)
    if not args.execute:
        print("DRY RUN: save will be skipped (pass --execute to save)")

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
            product_group="MISC",
            description=description,
            multiplier=0.80,
            execute=args.execute
        )

        if result["success"] and result.get("saved"):
            print("\n  SUCCESS: Price page created!")
            print(f"  Description: {description}")
        elif result["success"]:
            print("\n  DRY RUN complete - window driven, nothing saved.")
            print("  Re-run with --execute to save the record.")
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
        except (httpx.HTTPError, OSError):
            pass

    print("\n" + "=" * 60)
    print("Save and close workflow complete!")


if __name__ == "__main__":
    main()
