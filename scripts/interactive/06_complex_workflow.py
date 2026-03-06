"""
Interactive API - Complex Workflow (v2)

Demonstrates a multi-step workflow using the Interactive API v2.

This example shows:
- Context manager for session cleanup
- Error handling at each step
- Multiple field changes with DatawindowName (required in P21 25.2+)
- Tab switching
- Saving with validation checking

Usage:
    python scripts/interactive/06_complex_workflow.py
"""

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from datetime import datetime
from common.auth import get_token, get_auth_headers, get_ui_server_url
from common.config import load_config

import warnings
warnings.filterwarnings("ignore")


class Window:
    """Represents an open P21 window."""

    def __init__(self, session, window_id: str, data: dict):
        self.session = session
        self.window_id = window_id
        self.data = data

    def change(self, tab_name: str, datawindow_name: str,
               field_name: str, value: str):
        """Change a single field (v2 format with DatawindowName)."""
        return self.session.change_data(self.window_id, [
            {"TabName": tab_name, "DatawindowName": datawindow_name,
             "FieldName": field_name, "Value": value}
        ])

    def change_multiple(self, changes: list):
        """Change multiple fields at once."""
        return self.session.change_data(self.window_id, changes)

    def select_tab(self, tab_name: str):
        """Switch to a tab."""
        return self.session.change_tab(self.window_id, tab_name)

    def save(self):
        """Save the data."""
        return self.session.save_data(self.window_id)

    def close(self):
        """Close the window."""
        return self.session.close_window(self.window_id)


class InteractiveClient:
    """Full-featured Interactive API v2 client."""

    def __init__(self, base_url: str, username: str, password: str, verify_ssl: bool = False):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.token = None
        self.ui_server_url = None
        self.client = None

    def __enter__(self):
        self.client = httpx.Client(verify=self.verify_ssl, timeout=60.0, follow_redirects=True)
        self._authenticate()
        self._get_ui_server()
        self._start_session()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self._end_session()
        except (httpx.HTTPError, OSError):
            pass
        if self.client:
            self.client.close()
        return False

    def _authenticate(self):
        response = self.client.post(
            f"{self.base_url}/api/security/token",
            headers={
                "username": self.username,
                "password": self.password,
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            content=""
        )
        response.raise_for_status()
        self.token = response.json()["AccessToken"]

    def _get_ui_server(self):
        response = self.client.get(
            f"{self.base_url}/api/ui/router/v1?urlType=external",
            headers={"Authorization": f"Bearer {self.token}", "Accept": "application/json"}
        )
        response.raise_for_status()
        self.ui_server_url = response.json()["Url"].rstrip("/")

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def _start_session(self):
        response = self.client.post(
            f"{self.ui_server_url}/api/ui/interactive/sessions/",
            headers=self._headers(),
            json={"ResponseWindowHandlingEnabled": False}
        )
        response.raise_for_status()

    def _end_session(self):
        self.client.delete(
            f"{self.ui_server_url}/api/ui/interactive/sessions/",
            headers=self._headers()
        )

    def open_window(self, service_name: str) -> Window:
        """Open a window and return a Window object."""
        response = self.client.post(
            f"{self.ui_server_url}/api/ui/interactive/v2/window",
            headers=self._headers(),
            json={"ServiceName": service_name}
        )
        response.raise_for_status()
        data = response.json()
        return Window(self, data["WindowId"], data)

    def change_data(self, window_id: str, changes: list) -> dict:
        """Change field values using v2 List format.

        Each change dict should include:
            TabName, DatawindowName, FieldName, Value

        DatawindowName is required in P21 25.2+.
        """
        response = self.client.put(
            f"{self.ui_server_url}/api/ui/interactive/v2/change",
            headers=self._headers(),
            json={"WindowId": window_id, "List": changes}
        )
        response.raise_for_status()
        return response.json()

    def change_tab(self, window_id: str, tab_name: str) -> dict:
        """Switch to a different tab using v2 format."""
        response = self.client.put(
            f"{self.ui_server_url}/api/ui/interactive/v2/tab",
            headers=self._headers(),
            json={"WindowId": window_id, "PageName": tab_name}
        )
        response.raise_for_status()
        return response.json()

    def save_data(self, window_id: str) -> dict:
        """Save data using v2 format (bare GUID string body)."""
        response = self.client.put(
            f"{self.ui_server_url}/api/ui/interactive/v2/data",
            headers=self._headers(),
            json=window_id  # v2: just the GUID string
        )
        response.raise_for_status()
        return response.json()

    def close_window(self, window_id: str):
        self.client.delete(
            f"{self.ui_server_url}/api/ui/interactive/v2/window",
            params={"windowId": window_id},
            headers=self._headers()
        )


def create_price_page_workflow(client: InteractiveClient, description: str,
                                supplier_id: int, product_group: str, multiplier: float):
    """
    Complete workflow to create a price page.

    Steps:
    1. Open SalesPricePage window
    2. Set page type
    3. Fill required fields
    4. Switch to VALUES tab
    5. Set calculation values
    6. Save
    7. Close window
    """
    print(f"\n  Creating: {description}")

    # Step 1: Open window
    print("    Opening window...", end=" ")
    window = client.open_window("SalesPricePage")
    print(f"OK (ID: {window.window_id[:20]}...)")

    try:
        # Step 2: Set page type
        print("    Setting page type...", end=" ")
        window.change("FORM", "form", "price_page_type_cd", "Supplier / Product Group")
        print("OK")

        # Step 3: Fill required fields (order matters for some fields)
        print("    Setting company...", end=" ")
        window.change("FORM", "form", "company_id", "ACME")
        print("OK")

        print("    Setting product group...", end=" ")
        window.change("FORM", "form", "product_group_id", product_group)
        print("OK")

        print("    Setting supplier...", end=" ")
        window.change("FORM", "form", "supplier_id", str(supplier_id))
        print("OK")

        print("    Setting remaining fields...", end=" ")
        window.change_multiple([
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
        print("OK")

        # Step 4: Switch to VALUES tab
        print("    Switching to VALUES tab...", end=" ")
        window.select_tab("VALUES")
        print("OK")

        # Step 5: Set calculation values
        print("    Setting calculation values...", end=" ")
        window.change_multiple([
            {"TabName": "VALUES", "DatawindowName": "d_values",
             "FieldName": "calculation_method_cd", "Value": "Multiplier"},
            {"TabName": "VALUES", "DatawindowName": "d_values",
             "FieldName": "calculation_value1", "Value": str(multiplier)},
        ])
        print("OK")

        # Step 6: Save
        print("    Saving...", end=" ")
        result = window.save()
        # Status 3 = Blocked (response window opened)
        if result.get("Status") == 3:
            raise RuntimeError("Save blocked by response window")
        print("OK")

        # Step 7: Close window
        print("    Closing window...", end=" ")
        window.close()
        print("OK")

        return True

    except Exception as e:
        print(f"FAILED ({e})")
        try:
            window.close()
        except (httpx.HTTPError, OSError):
            pass
        raise


def main():
    print("Interactive API - Complex Workflow (v2)")
    print("=" * 60)

    config = load_config()

    print(f"Server: {config.base_url}")
    timestamp = datetime.now().strftime("%H%M%S")

    # Use context manager for automatic cleanup
    try:
        with InteractiveClient(
            config.base_url,
            config.username,
            config.password,
            config.verify_ssl
        ) as client:

            print("\n1. Session started via context manager")
            print("-" * 50)

            # Create a single price page
            print("\n2. Creating single price page:")
            print("-" * 50)

            create_price_page_workflow(
                client,
                description=f"WORKFLOW-{timestamp}-A",
                supplier_id=10,
                product_group="MISC",
                multiplier=0.75
            )

            print("\n  Price page created successfully!")

            # Could create more records here...

            print("\n3. Session will end automatically on exit")
            print("-" * 50)

    except httpx.HTTPStatusError as e:
        print(f"\nHTTP Error: {e.response.status_code}")
        print(f"Response: {e.response.text[:300]}")

    except Exception as e:
        print(f"\nError: {type(e).__name__}: {e}")

    print("\n" + "=" * 60)
    print("Complex workflow complete!")
    print("\nKey patterns demonstrated:")
    print("- Context manager for automatic session cleanup")
    print("- Window class for cleaner field operations")
    print("- v2 API format with DatawindowName (required in P21 25.2+)")
    print("- Step-by-step logging for debugging")
    print("- Error handling at each step")


if __name__ == "__main__":
    main()
