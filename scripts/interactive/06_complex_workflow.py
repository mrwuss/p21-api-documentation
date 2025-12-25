"""
Interactive API - Complex Workflow

Demonstrates a multi-step workflow using the Interactive API.

This example shows:
- Context manager for session cleanup
- Error handling at each step
- Multiple field changes
- Tab switching
- Saving with validation checking

Usage:
    python scripts/interactive/06_complex_workflow.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from datetime import datetime
from contextlib import contextmanager
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

    def change(self, field_name: str, value: str, datawindow: str = "d_form"):
        """Change a single field."""
        return self.session.change_data(self.window_id, [
            {"DataWindowName": datawindow, "FieldName": field_name, "Value": value}
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
    """Full-featured Interactive API client."""

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
        except:
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
        response = self.client.put(
            f"{self.ui_server_url}/api/ui/interactive/v1/change",
            headers=self._headers(),
            json={"WindowId": window_id, "ChangeRequests": changes}
        )
        response.raise_for_status()
        return response.json()

    def change_tab(self, window_id: str, tab_name: str) -> dict:
        response = self.client.put(
            f"{self.ui_server_url}/api/ui/interactive/v1/tab",
            headers=self._headers(),
            json={"WindowId": window_id, "PagePath": {"PageName": tab_name}}
        )
        response.raise_for_status()
        return response.json()

    def save_data(self, window_id: str) -> dict:
        response = self.client.put(
            f"{self.ui_server_url}/api/ui/interactive/v1/data",
            headers=self._headers(),
            json={"WindowId": window_id}
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
        window.change("price_page_type_cd", "Supplier / Product Group")
        print("OK")

        # Step 3: Fill required fields (order matters for some fields)
        print("    Setting company...", end=" ")
        window.change("company_id", "IFPG")
        print("OK")

        print("    Setting product group...", end=" ")
        window.change("product_group_id", product_group)
        print("OK")

        print("    Setting supplier...", end=" ")
        window.change("supplier_id", str(supplier_id))
        print("OK")

        print("    Setting remaining fields...", end=" ")
        window.change_multiple([
            {"DataWindowName": "d_form", "FieldName": "description", "Value": description},
            {"DataWindowName": "d_form", "FieldName": "pricing_method_cd", "Value": "Source"},
            {"DataWindowName": "d_form", "FieldName": "source_price_cd", "Value": "Supplier List Price"},
            {"DataWindowName": "d_form", "FieldName": "effective_date",
             "Value": datetime.now().strftime("%Y-%m-%d")},
            {"DataWindowName": "d_form", "FieldName": "expiration_date", "Value": "2030-12-31"},
            {"DataWindowName": "d_form", "FieldName": "row_status_flag", "Value": "Active"},
        ])
        print("OK")

        # Step 4: Switch to VALUES tab
        print("    Switching to VALUES tab...", end=" ")
        window.select_tab("VALUES")
        print("OK")

        # Step 5: Set calculation values
        print("    Setting calculation values...", end=" ")
        window.change_multiple([
            {"DataWindowName": "d_values", "FieldName": "calculation_method_cd", "Value": "Multiplier"},
            {"DataWindowName": "d_values", "FieldName": "calculation_value1", "Value": str(multiplier)},
        ])
        print("OK")

        # Step 6: Save
        print("    Saving...", end=" ")
        result = window.save()
        if result.get("Status") == "Blocked":
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
        except:
            pass
        raise


def main():
    print("Interactive API - Complex Workflow")
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
                product_group="FA5",
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
    print("- Step-by-step logging for debugging")
    print("- Error handling at each step")


if __name__ == "__main__":
    main()
