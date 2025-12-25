"""
Transaction API - Async Operations

Demonstrates using the async endpoint for long-running operations.

The async endpoint:
- Immediately returns a request ID
- Processes the transaction in the background
- Uses a dedicated session (avoids session pool issues)
- Can send callbacks when complete

Usage:
    python scripts/transaction/06_async_operations.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
import time
from datetime import datetime
from common.auth import get_token, get_auth_headers, get_ui_server_url
from common.config import load_config

import warnings
warnings.filterwarnings("ignore")


def build_test_payload() -> dict:
    """Build a simple test payload."""
    timestamp = datetime.now().strftime("%H%M%S%f")
    return {
        "Name": "SalesPricePage",
        "UseCodeValues": False,
        "Transactions": [
            {
                "Status": "New",
                "DataElements": [
                    {
                        "Name": "FORM.form",
                        "Type": "Form",
                        "Keys": [],
                        "Rows": [{
                            "Edits": [
                                {"Name": "price_page_type_cd", "Value": "Supplier / Product Group"},
                                {"Name": "company_id", "Value": "IFPG"},
                                {"Name": "supplier_id", "Value": 10.0},
                                {"Name": "product_group_id", "Value": "FA5"},
                                {"Name": "description", "Value": f"ASYNC-TEST-{timestamp}"},
                                {"Name": "pricing_method_cd", "Value": "Source"},
                                {"Name": "source_price_cd", "Value": "Supplier List Price"},
                                {"Name": "effective_date", "Value": datetime.now().strftime("%Y-%m-%d")},
                                {"Name": "expiration_date", "Value": "2030-12-31"},
                                {"Name": "totaling_method_cd", "Value": "Item"},
                                {"Name": "totaling_basis_cd", "Value": "Supplier List Price"},
                                {"Name": "row_status_flag", "Value": "Active"}
                            ],
                            "RelativeDateEdits": []
                        }]
                    },
                    {
                        "Name": "VALUES.values",
                        "Type": "Form",
                        "Keys": [],
                        "Rows": [{
                            "Edits": [
                                {"Name": "calculation_method_cd", "Value": "Multiplier"},
                                {"Name": "calculation_value1", "Value": "0.5"}
                            ],
                            "RelativeDateEdits": []
                        }]
                    }
                ]
            }
        ]
    }


def submit_async(ui_server_url: str, payload: dict, headers: dict, verify_ssl: bool) -> dict:
    """Submit an async transaction request."""
    response = httpx.post(
        f"{ui_server_url}/api/v2/transaction/async",
        headers=headers,
        json=payload,
        verify=verify_ssl,
        follow_redirects=True,
        timeout=30.0
    )
    response.raise_for_status()
    return response.json()


def check_async_status(ui_server_url: str, request_id: str, headers: dict, verify_ssl: bool) -> dict:
    """Check the status of an async request."""
    response = httpx.get(
        f"{ui_server_url}/api/v2/transaction/async",
        params={"id": request_id},
        headers=headers,
        verify=verify_ssl,
        follow_redirects=True,
        timeout=30.0
    )
    response.raise_for_status()
    return response.json()


def wait_for_completion(ui_server_url: str, request_id: str, headers: dict,
                        verify_ssl: bool, timeout: int = 60, poll_interval: int = 2) -> dict:
    """Poll for async request completion."""
    start_time = time.time()

    while time.time() - start_time < timeout:
        status = check_async_status(ui_server_url, request_id, headers, verify_ssl)

        current_status = status.get("Status", "Unknown")
        print(f"    Status: {current_status}")

        if current_status in ("Complete", "Failed"):
            return status

        time.sleep(poll_interval)

    raise TimeoutError(f"Request {request_id} did not complete within {timeout} seconds")


def main():
    print("Transaction API - Async Operations")
    print("=" * 60)

    config = load_config()
    token_data = get_token(config)
    headers = get_auth_headers(token_data["AccessToken"])
    ui_server_url = get_ui_server_url(config.base_url, token_data["AccessToken"], config.verify_ssl)

    print(f"UI Server: {ui_server_url}")

    # Example 1: Submit async request
    print("\n1. Submit async transaction:")
    print("-" * 50)

    payload = build_test_payload()
    print(f"  Submitting async request for: SalesPricePage")

    try:
        result = submit_async(ui_server_url, payload, headers, config.verify_ssl)

        request_id = result.get("RequestId")
        status = result.get("Status")

        print(f"\n  Async Request Submitted:")
        print(f"    Request ID: {request_id}")
        print(f"    Initial Status: {status}")

        if not request_id:
            print("  Error: No request ID returned")
            return

        # Example 2: Poll for completion
        print("\n\n2. Polling for completion:")
        print("-" * 50)

        final_status = wait_for_completion(
            ui_server_url, request_id, headers, config.verify_ssl,
            timeout=60, poll_interval=2
        )

        print(f"\n  Final Result:")
        print(f"    Request ID: {final_status.get('RequestId')}")
        print(f"    Status: {final_status.get('Status')}")
        print(f"    Completed: {final_status.get('CompletedDate', 'N/A')}")

        messages = final_status.get("Messages", "")
        if messages:
            # Messages may contain the result or error
            print(f"    Messages: {messages[:200]}...")

    except httpx.HTTPStatusError as e:
        print(f"\n  HTTP Error: {e.response.status_code}")
        print(f"  Response: {e.response.text[:500]}")

    except TimeoutError as e:
        print(f"\n  Timeout: {e}")

    except Exception as e:
        print(f"\n  Error: {type(e).__name__}: {e}")

    # Example 3: Show callback structure
    print("\n\n3. Async with Callback (structure only):")
    print("-" * 50)
    print("  For long-running operations, you can request a callback:")
    print()
    print("  POST /api/v2/transaction/async/callback")
    print("  {")
    print("    \"Content\": { ... transaction payload ... },")
    print("    \"Callback\": {")
    print("      \"Url\": \"https://your-server.com/webhook\",")
    print("      \"Method\": \"POST\",")
    print("      \"ContentType\": \"application/json\",")
    print("      \"Headers\": [")
    print("        {\"Name\": \"X-API-Key\", \"Value\": \"your-key\"}")
    print("      ]")
    print("    }")
    print("  }")
    print()
    print("  The callback receives the AsyncRequest with final status.")

    print("\n" + "=" * 60)
    print("Async operations complete!")
    print("\nBenefits of async endpoint:")
    print("- Uses dedicated session (no pool contamination)")
    print("- Better for long-running operations")
    print("- Callback support for notification")
    print("- Request ID for tracking/retry")


if __name__ == "__main__":
    main()
