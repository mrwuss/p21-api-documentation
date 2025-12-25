"""
Transaction API - Update Existing Records

Demonstrates updating existing records using the Transaction API.

To update a record, you need:
1. The key field(s) to identify the record
2. The fields you want to change

Usage:
    python scripts/transaction/05_update_existing.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from common.auth import get_token, get_auth_headers, get_ui_server_url
from common.config import load_config

import warnings
warnings.filterwarnings("ignore")


def build_update_payload(price_page_uid: int, new_description: str = None,
                          new_multiplier: float = None, expire: bool = False) -> dict:
    """
    Build a Transaction API payload for updating a price page.

    For updates, you need to include:
    - The key field(s) to identify the record
    - Only the fields you want to change
    """
    edits = []

    # Description update
    if new_description:
        edits.append({"Name": "description", "Value": new_description})

    # Expiration
    if expire:
        edits.append({"Name": "row_status_flag", "Value": "Expired"})

    # Build the payload
    data_elements = [
        {
            "Name": "FORM.form",
            "Type": "Form",
            "Keys": [],
            "Rows": [{
                "Edits": edits,
                "RelativeDateEdits": []
            }]
        }
    ]

    # If updating multiplier, need to include VALUES tab
    if new_multiplier is not None:
        data_elements.append({
            "Name": "VALUES.values",
            "Type": "Form",
            "Keys": [],
            "Rows": [{
                "Edits": [
                    {"Name": "calculation_value1", "Value": str(new_multiplier)}
                ],
                "RelativeDateEdits": []
            }]
        })

    return {
        "Name": "SalesPricePage",
        "UseCodeValues": False,
        "Transactions": [
            {
                "Status": "New",  # Still "New" for updates
                "DataElements": data_elements
            }
        ]
    }


def get_price_page(ui_server_url: str, price_page_uid: int, headers: dict, verify_ssl: bool) -> dict:
    """
    Get an existing price page using the Transaction API /get endpoint.

    This is used to load a record before updating it.
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
    print("Transaction API - Update Existing Records")
    print("=" * 60)

    config = load_config()
    token_data = get_token(config)
    headers = get_auth_headers(token_data["AccessToken"])
    ui_server_url = get_ui_server_url(config.base_url, token_data["AccessToken"], config.verify_ssl)

    print(f"UI Server: {ui_server_url}")

    # Example 1: Get an existing record
    print("\n1. Get existing record using /transaction/get:")
    print("-" * 50)

    # Use a known test UID - in real usage, you'd query for this
    test_uid = 45557  # Replace with a valid UID from your system

    try:
        print(f"  Fetching price page UID: {test_uid}")

        result = get_price_page(ui_server_url, test_uid, headers, config.verify_ssl)

        # Parse the result
        transactions = result.get("Transactions", [])
        if transactions:
            for trans in transactions[:1]:
                for elem in trans.get("DataElements", []):
                    print(f"\n  DataElement: {elem.get('Name')}")
                    rows = elem.get("Rows", [])
                    if rows:
                        print("  Current values:")
                        for edit in rows[0].get("Edits", [])[:8]:
                            name = edit.get("Name")
                            value = edit.get("Value", "")
                            if value:
                                print(f"    {name}: {value}")
        else:
            print("  No transaction data returned")

    except httpx.HTTPStatusError as e:
        print(f"  Error: {e.response.status_code}")
        if e.response.status_code == 404:
            print(f"  Record UID {test_uid} not found")
        else:
            print(f"  {e.response.text[:200]}")

    # Example 2: Show update payload structure
    print("\n\n2. Update payload structure:")
    print("-" * 50)
    print("  Updates require identifying the record via /get first,")
    print("  then sending only the changed fields.")

    payload = build_update_payload(
        price_page_uid=test_uid,
        new_description="Updated Description",
        new_multiplier=0.85
    )

    print("\n  Sample update payload:")
    print(f"    Service: {payload['Name']}")
    print(f"    Transactions: {len(payload['Transactions'])}")

    for trans in payload["Transactions"]:
        for elem in trans["DataElements"]:
            print(f"\n    DataElement: {elem['Name']}")
            for row in elem["Rows"]:
                print("      Fields to update:")
                for edit in row["Edits"]:
                    print(f"        {edit['Name']}: {edit['Value']}")

    # Example 3: Show expire payload
    print("\n\n3. Expire record payload structure:")
    print("-" * 50)

    expire_payload = build_update_payload(
        price_page_uid=test_uid,
        expire=True
    )

    for trans in expire_payload["Transactions"]:
        for elem in trans["DataElements"]:
            for row in elem["Rows"]:
                for edit in row["Edits"]:
                    print(f"    {edit['Name']}: {edit['Value']}")

    print("\n  Note: Setting row_status_flag to 'Expired' deactivates the record.")

    print("\n" + "=" * 60)
    print("Update examples complete!")
    print("\nImportant notes:")
    print("- Always fetch the record first with /transaction/get")
    print("- Only include fields you want to change")
    print("- The 'Status' in the request is still 'New' for updates")


if __name__ == "__main__":
    main()
