"""
Transaction API - Get Service Definition

Retrieves the schema/template for a service to understand required fields.

Usage:
    python scripts/transaction/02_get_definition.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
import json
from common.auth import get_token, get_auth_headers, get_ui_server_url
from common.config import load_config

import warnings
warnings.filterwarnings("ignore")


def get_service_definition(ui_server_url: str, service_name: str, headers: dict, verify_ssl: bool) -> dict:
    """Fetch the definition for a service."""
    response = httpx.get(
        f"{ui_server_url}/api/v2/definition/{service_name}",
        headers=headers,
        verify=verify_ssl,
        follow_redirects=True,
        timeout=60.0  # Large definitions can take time
    )
    response.raise_for_status()
    return response.json()


def get_service_defaults(ui_server_url: str, service_name: str, headers: dict, verify_ssl: bool) -> dict:
    """Fetch the default values for a service."""
    response = httpx.get(
        f"{ui_server_url}/api/v2/defaults/{service_name}",
        headers=headers,
        verify=verify_ssl,
        follow_redirects=True,
        timeout=60.0
    )
    response.raise_for_status()
    return response.json()


def print_data_element(element: dict, indent: int = 0):
    """Print a DataElement structure."""
    prefix = "  " * indent
    name = element.get("Name", "Unknown")
    elem_type = element.get("Type", "Unknown")
    keys = element.get("Keys", [])

    print(f"{prefix}DataElement: {name}")
    print(f"{prefix}  Type: {elem_type}")
    if keys:
        print(f"{prefix}  Keys: {keys}")

    # Print rows/edits
    rows = element.get("Rows", [])
    if rows:
        print(f"{prefix}  Fields ({len(rows[0].get('Edits', []))} total):")
        for edit in rows[0].get("Edits", [])[:10]:  # Show first 10
            print(f"{prefix}    - {edit.get('Name')}")
        if len(rows[0].get("Edits", [])) > 10:
            print(f"{prefix}    ... and {len(rows[0].get('Edits', [])) - 10} more")


def print_field_definition(field_def: dict, indent: int = 0):
    """Print a field definition."""
    prefix = "  " * indent
    name = field_def.get("Name", "Unknown")
    data_type = field_def.get("DataType", "Unknown")
    required = field_def.get("Required", False)
    label = field_def.get("Label", "")
    valid_values = field_def.get("ValidValues")

    req_marker = "*" if required else " "
    print(f"{prefix}{req_marker} {name} ({data_type}): {label}")

    if valid_values:
        values_preview = valid_values[:5]
        print(f"{prefix}    Valid: {values_preview}" + ("..." if len(valid_values) > 5 else ""))


def main():
    print("Transaction API - Get Service Definition")
    print("=" * 60)

    config = load_config()
    token_data = get_token(config)
    headers = get_auth_headers(token_data["AccessToken"])
    ui_server_url = get_ui_server_url(config.base_url, token_data["AccessToken"], config.verify_ssl)

    # Example 1: Get Order definition
    service_name = "Order"
    print(f"\n1. Getting definition for '{service_name}' service:")
    print("-" * 50)

    try:
        definition = get_service_definition(ui_server_url, service_name, headers, config.verify_ssl)

        # Show template structure
        template = definition.get("Template", {})
        transaction_set = template.get("TransactionSet", template)

        print(f"\n  Service: {transaction_set.get('Name')}")
        print(f"  UseCodeValues: {transaction_set.get('UseCodeValues', False)}")

        transactions = transaction_set.get("Transactions", [])
        if transactions:
            print(f"\n  DataElements in template:")
            for trans in transactions[:1]:  # First transaction
                for elem in trans.get("DataElements", [])[:5]:  # First 5 elements
                    print_data_element(elem, indent=2)
                    print()

        # Show field definitions
        trans_def = definition.get("TransactionDefinition", {})
        data_elem_defs = trans_def.get("DataElementDefinitions", [])

        if data_elem_defs:
            print("\n  Field Definitions (first DataElement):")
            first_elem = data_elem_defs[0]
            print(f"    DataElement: {first_elem.get('Name')}")
            print(f"    Key Fields: {first_elem.get('KeyFields', [])}")
            print("\n    Fields (* = required):")

            field_defs = first_elem.get("FieldDefinitions", [])
            for field in field_defs[:15]:  # Show first 15 fields
                print_field_definition(field, indent=3)

            if len(field_defs) > 15:
                print(f"\n    ... and {len(field_defs) - 15} more fields")

    except httpx.HTTPStatusError as e:
        print(f"  Error: {e.response.status_code} - {e.response.text[:200]}")

    # Example 2: Get SalesPricePage definition (commonly used)
    service_name = "SalesPricePage"
    print(f"\n\n2. Getting definition for '{service_name}' service:")
    print("-" * 50)

    try:
        definition = get_service_definition(ui_server_url, service_name, headers, config.verify_ssl)

        trans_def = definition.get("TransactionDefinition", {})
        data_elem_defs = trans_def.get("DataElementDefinitions", [])

        for elem_def in data_elem_defs[:2]:  # Show first 2 data elements
            print(f"\n  DataElement: {elem_def.get('Name')}")
            print(f"  Type: {elem_def.get('Type')}")

            print("\n  Required Fields:")
            for field in elem_def.get("FieldDefinitions", []):
                if field.get("Required"):
                    print_field_definition(field, indent=2)

    except httpx.HTTPStatusError as e:
        print(f"  Error: {e.response.status_code} - {e.response.text[:200]}")

    # Example 3: Get default values
    print(f"\n\n3. Getting default values for 'Order' service:")
    print("-" * 50)

    try:
        defaults = get_service_defaults(ui_server_url, "Order", headers, config.verify_ssl)

        # Show some default values
        data_elements = defaults.get("DataElements", [])
        if data_elements:
            elem = data_elements[0]
            print(f"\n  DataElement: {elem.get('Name')}")
            print("\n  Default values:")

            rows = elem.get("Rows", [])
            if rows:
                for edit in rows[0].get("Edits", [])[:10]:
                    name = edit.get("Name")
                    value = edit.get("Value", "")
                    if value:  # Only show non-empty defaults
                        print(f"    {name}: {value}")

    except httpx.HTTPStatusError as e:
        print(f"  Error: {e.response.status_code} - {e.response.text[:200]}")

    print("\n" + "=" * 60)
    print("Definition examples complete!")
    print("\nTip: Save full definition to file for reference:")
    print("  response.json() | json.dump(f, indent=2)")


if __name__ == "__main__":
    main()
