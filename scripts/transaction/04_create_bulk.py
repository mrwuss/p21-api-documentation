"""
Transaction API - Bulk Create Records

Demonstrates creating multiple records in a single request.

The Transaction API can process multiple transactions at once,
which is more efficient than making individual requests.

Usage:
    python scripts/transaction/04_create_bulk.py
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


def build_bulk_payload(records: list[dict]) -> dict:
    """
    Build a Transaction API payload for creating multiple records.

    Args:
        records: List of dicts with description, supplier_id, product_group, multiplier

    Returns:
        TransactionSet payload with multiple Transactions
    """
    transactions = []

    for record in records:
        transaction = {
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
                            {"Name": "supplier_id", "Value": float(record["supplier_id"])},
                            {"Name": "product_group_id", "Value": record["product_group"]},
                            {"Name": "description", "Value": record["description"]},
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
                            {"Name": "calculation_value1", "Value": str(record.get("multiplier", 0.5))}
                        ],
                        "RelativeDateEdits": []
                    }]
                }
            ]
        }
        transactions.append(transaction)

    return {
        "Name": "SalesPricePage",
        "UseCodeValues": False,
        "Transactions": transactions
    }


def create_bulk(ui_server_url: str, payload: dict, headers: dict, verify_ssl: bool) -> dict:
    """Send a bulk Transaction API create request."""
    response = httpx.post(
        f"{ui_server_url}/api/v2/transaction",
        headers=headers,
        json=payload,
        verify=verify_ssl,
        follow_redirects=True,
        timeout=60.0  # Longer timeout for bulk operations
    )
    response.raise_for_status()
    return response.json()


def main():
    print("Transaction API - Bulk Create Records")
    print("=" * 60)

    config = load_config()
    token_data = get_token(config)
    headers = get_auth_headers(token_data["AccessToken"])
    ui_server_url = get_ui_server_url(config.base_url, token_data["AccessToken"], config.verify_ssl)

    print(f"UI Server: {ui_server_url}")

    # Prepare test records
    timestamp = datetime.now().strftime("%H%M%S")

    records = [
        {
            "description": f"BULK-TEST-{timestamp}-A",
            "supplier_id": 10,
            "product_group": "FA5",
            "multiplier": 0.70
        },
        {
            "description": f"BULK-TEST-{timestamp}-B",
            "supplier_id": 10,
            "product_group": "FA5",
            "multiplier": 0.75
        },
        {
            "description": f"BULK-TEST-{timestamp}-C",
            "supplier_id": 10,
            "product_group": "FA5",
            "multiplier": 0.80
        }
    ]

    print(f"\nCreating {len(records)} price pages in single request:")
    print("-" * 50)

    for i, rec in enumerate(records, 1):
        print(f"  {i}. {rec['description']} (multiplier: {rec['multiplier']})")

    payload = build_bulk_payload(records)

    print(f"\n  Payload:")
    print(f"    Service: {payload['Name']}")
    print(f"    Transactions: {len(payload['Transactions'])}")

    try:
        result = create_bulk(ui_server_url, payload, headers, config.verify_ssl)

        # Analyze results
        summary = result.get("Summary", {})
        succeeded = summary.get("Succeeded", 0)
        failed = summary.get("Failed", 0)
        messages = result.get("Messages", [])

        print("\n  Results:")
        print(f"    Succeeded: {succeeded}")
        print(f"    Failed: {failed}")

        # Show per-transaction messages
        if messages:
            print("\n  Transaction Messages:")
            for msg in messages:
                print(f"    - {msg}")

        # Show created UIDs
        results = result.get("Results", {})
        transactions = results.get("Transactions", [])

        if transactions:
            print("\n  Created Records:")
            for i, trans in enumerate(transactions, 1):
                status = trans.get("Status", "Unknown")
                uid = None

                for elem in trans.get("DataElements", []):
                    for row in elem.get("Rows", []):
                        for edit in row.get("Edits", []):
                            if edit.get("Name") == "price_page_uid":
                                uid = edit.get("Value")

                status_marker = "OK" if status == "Passed" else "FAIL"
                print(f"    [{status_marker}] Transaction {i}: UID={uid}, Status={status}")

        # Summary
        print("\n" + "-" * 50)
        if succeeded == len(records):
            print(f"  SUCCESS: All {succeeded} records created!")
        elif succeeded > 0:
            print(f"  PARTIAL: {succeeded} created, {failed} failed")
        else:
            print(f"  FAILED: No records created")

    except httpx.HTTPStatusError as e:
        print(f"\n  HTTP Error: {e.response.status_code}")
        print(f"  Response: {e.response.text[:500]}")

    except Exception as e:
        print(f"\n  Error: {type(e).__name__}: {e}")

    print("\n" + "=" * 60)
    print("Bulk create example complete!")
    print("\nNote: Bulk operations are more efficient than individual requests,")
    print("but all transactions share the same session pool context.")


if __name__ == "__main__":
    main()
