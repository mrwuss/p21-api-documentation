"""
Transaction API - Create Single Record

Demonstrates creating a single record using the Transaction API.

This example creates a price page, which is relatively safe for testing
as it can be easily expired/deactivated.

By default the script is a DRY RUN: it prints the payload and exits
without posting. Pass --execute to actually create the record.

Usage:
    python examples/python/transaction/03_create_single.py            # dry run
    python examples/python/transaction/03_create_single.py --execute  # creates
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
import json
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
                                {"Name": "supplier_id", "Value": str(supplier_id)},
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


def read_back_price_page(ui_server_url: str, price_page_uid: str, headers: dict,
                         verify_ssl: bool) -> dict:
    """Read back a created price page via POST /api/v2/transaction/get.

    Read-back is the only proof of persistence — HTTP 200 + Summary alone
    only proves the request was processed.
    """
    payload = {
        "ServiceName": "SalesPricePage",
        "TransactionStates": [
            {
                "DataElementName": "FORM.form",
                "Keys": [
                    {"Name": "price_page_uid", "Value": str(price_page_uid)}
                ]
            }
        ]
    }
    response = httpx.post(
        f"{ui_server_url}/api/v2/transaction/get",
        headers=headers,
        json=payload,
        verify=verify_ssl,
        follow_redirects=True,
        timeout=30.0
    )
    response.raise_for_status()
    return response.json()


def main():
    parser = argparse.ArgumentParser(description="Create a single price page via the Transaction API")
    parser.add_argument("--execute", action="store_true",
                        help="Actually POST the transaction (default: dry run, print payload only)")
    args = parser.parse_args()

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
        product_group="MISC",  # A common product group
        multiplier=0.75
    )

    print("\n  Request payload structure:")
    print(f"    Service: {payload['Name']}")
    print(f"    UseCodeValues: {payload['UseCodeValues']}")
    print(f"    Transactions: {len(payload['Transactions'])}")
    print(f"    DataElements: {len(payload['Transactions'][0]['DataElements'])}")

    if not args.execute:
        print("\n  DRY RUN - full payload that would be posted:")
        print(json.dumps(payload, indent=2))
        print("\n  Re-run with --execute to create the record.")
        print("\n" + "=" * 60)
        print("Create single record example complete (dry run)!")
        return

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
            created_uid = None

            if transactions:
                trans = transactions[0]
                status = trans.get("Status")
                print(f"\n    Transaction Status: {status}")

                # Get the generated UID
                for elem in trans.get("DataElements", []):
                    for row in elem.get("Rows", []):
                        for edit in row.get("Edits", []):
                            if edit.get("Name") == "price_page_uid":
                                created_uid = edit.get("Value")
                                print(f"    Created UID: {created_uid}")

            print("\n  SUCCESS: Price page created!")

            # Verify with a read-back: fetch the created page via
            # /api/v2/transaction/get. Read-back is the only proof of
            # persistence.
            if created_uid:
                print("\n  Verifying via /api/v2/transaction/get...")
                try:
                    readback = read_back_price_page(
                        ui_server_url, created_uid, headers, config.verify_ssl
                    )
                    rb_desc = None
                    for trans in readback.get("Transactions", []):
                        for elem in trans.get("DataElements", []):
                            for row in elem.get("Rows", []):
                                for edit in row.get("Edits", []):
                                    if edit.get("Name") == "description":
                                        rb_desc = edit.get("Value")
                    if rb_desc == description:
                        print(f"  VERIFIED: read-back returned description '{rb_desc}'")
                    elif rb_desc is not None:
                        print(f"  WARNING: read-back description mismatch: '{rb_desc}'")
                    else:
                        print("  WARNING: read-back returned no description field")
                except httpx.HTTPStatusError as e:
                    print(f"  Read-back failed: HTTP {e.response.status_code}")
            else:
                print("\n  WARNING: no price_page_uid in response - cannot read back")

        else:
            print("\n  FAILED: Record not created")
            print("    Check messages above for details")

    except httpx.HTTPStatusError as e:
        print(f"\n  HTTP Error: {e.response.status_code}")
        print(f"  Response: {e.response.text[:500]}")

    except Exception as e:
        print(f"\n  Error: {type(e).__name__}: {e}")

    print("\n" + "=" * 60)
    print("Create single record example complete!")


if __name__ == "__main__":
    main()
