"""
Transaction API - Create Single Record

Demonstrates creating a single record using the Transaction API.

This example creates a price page, which is relatively safe for testing
as it can be easily expired/deactivated.

Usage:
    python scripts/transaction/03_create_single.py
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


def build_price_page_payload(description: str, supplier_id: int, product_group: str,
                              multiplier: float = 0.5) -> dict:
    """Build a Transaction API payload for creating a price page."""
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
                                {"Name": "company_id", "Value": "ACME"},
                                {"Name": "supplier_id", "Value": float(supplier_id)},
                                {"Name": "product_group_id", "Value": product_group},
                                {"Name": "description", "Value": description},
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
                                {"Name": "calculation_value1", "Value": str(multiplier)}
                            ],
                            "RelativeDateEdits": []
                        }]
                    }
                ]
            }
        ]
    }


def create_record(ui_server_url: str, payload: dict, headers: dict, verify_ssl: bool) -> dict:
    """Send a Transaction API create request."""
    response = httpx.post(
        f"{ui_server_url}/api/v2/transaction",
        headers=headers,
        json=payload,
        verify=verify_ssl,
        follow_redirects=True,
        timeout=30.0
    )
    response.raise_for_status()
    return response.json()


def main():
    print("Transaction API - Create Single Record")
    print("=" * 60)

    config = load_config()
    token_data = get_token(config)
    headers = get_auth_headers(token_data["AccessToken"])
    ui_server_url = get_ui_server_url(config.base_url, token_data["AccessToken"], config.verify_ssl)

    print(f"UI Server: {ui_server_url}")

    # Create a test price page
    timestamp = datetime.now().strftime("%H%M%S")
    description = f"API-TEST-{timestamp}"

    print(f"\nCreating price page: {description}")
    print("-" * 50)

    payload = build_price_page_payload(
        description=description,
        supplier_id=10,  # A common test supplier
        product_group="FA5",  # A common product group
        multiplier=0.75
    )

    print("\n  Request payload structure:")
    print(f"    Service: {payload['Name']}")
    print(f"    UseCodeValues: {payload['UseCodeValues']}")
    print(f"    Transactions: {len(payload['Transactions'])}")
    print(f"    DataElements: {len(payload['Transactions'][0]['DataElements'])}")

    try:
        result = create_record(ui_server_url, payload, headers, config.verify_ssl)

        # Check summary
        summary = result.get("Summary", {})
        succeeded = summary.get("Succeeded", 0)
        failed = summary.get("Failed", 0)
        messages = result.get("Messages", [])

        print("\n  Response:")
        print(f"    Succeeded: {succeeded}")
        print(f"    Failed: {failed}")

        if messages:
            print(f"    Messages:")
            for msg in messages:
                print(f"      - {msg}")

        if succeeded > 0:
            # Extract created record details
            results = result.get("Results", {})
            transactions = results.get("Transactions", [])

            if transactions:
                trans = transactions[0]
                status = trans.get("Status")
                print(f"\n    Transaction Status: {status}")

                # Get the generated UID
                for elem in trans.get("DataElements", []):
                    for row in elem.get("Rows", []):
                        for edit in row.get("Edits", []):
                            if edit.get("Name") == "price_page_uid":
                                print(f"    Created UID: {edit.get('Value')}")

            print("\n  SUCCESS: Price page created!")

        else:
            print("\n  FAILED: Record not created")
            print(f"    Check messages above for details")

    except httpx.HTTPStatusError as e:
        print(f"\n  HTTP Error: {e.response.status_code}")
        print(f"  Response: {e.response.text[:500]}")

    except Exception as e:
        print(f"\n  Error: {type(e).__name__}: {e}")

    print("\n" + "=" * 60)
    print("Create single record example complete!")


if __name__ == "__main__":
    main()
