"""
Transaction API - Get TimeEntry Service Definition

Retrieves the schema/template for the TimeEntry service to understand
the required fields, data elements, and default values for recording
labor hours against production orders.

Saves the full definition to a JSON file for offline reference.

Usage:
    python examples/python/production/02_get_timeentry_definition.py
"""

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import httpx
from common.auth import get_token, get_auth_headers, get_ui_server_url
from common.config import load_config
from common.transaction import get_service_definition, get_service_defaults

import warnings
warnings.filterwarnings("ignore")

SERVICE_NAME = "TimeEntry"
OUTPUT_DIR = Path(__file__).parent


def print_data_element(element: dict, indent: int = 0) -> None:
    """Print a DataElement structure with all its fields."""
    prefix = "  " * indent
    name = element.get("Name", "Unknown")
    elem_type = element.get("Type", "Unknown")
    keys = element.get("Keys", [])

    print(f"{prefix}DataElement: {name}")
    print(f"{prefix}  Type: {elem_type}")
    if keys:
        print(f"{prefix}  Keys: {keys}")

    rows = element.get("Rows", [])
    if rows:
        edits = rows[0].get("Edits", [])
        print(f"{prefix}  Fields ({len(edits)} total):")
        for edit in edits:
            value = edit.get("Value", "")
            display = f" = {value}" if value else ""
            print(f"{prefix}    - {edit.get('Name')}{display}")


def print_field_definition(field_def: dict, indent: int = 0) -> None:
    """Print a field definition with type, required status, and valid values."""
    prefix = "  " * indent
    name = field_def.get("Name", "Unknown")
    data_type = field_def.get("DataType", "Unknown")
    required = field_def.get("Required", False)
    label = field_def.get("Label", "")
    valid_values = field_def.get("ValidValues")

    req_marker = "*" if required else " "
    print(f"{prefix}{req_marker} {name} ({data_type}): {label}")

    if valid_values:
        values_preview = valid_values[:8]
        suffix = "..." if len(valid_values) > 8 else ""
        print(f"{prefix}    Valid: {values_preview}{suffix}")


def main() -> None:
    print(f"Transaction API - Get {SERVICE_NAME} Service Definition")
    print("=" * 60)

    config = load_config()
    token_data = get_token(config)
    headers = get_auth_headers(token_data["AccessToken"])
    ui_server_url = get_ui_server_url(
        config.base_url, token_data["AccessToken"], config.verify_ssl
    )
    print(f"UI Server: {ui_server_url}")

    # ------------------------------------------------------------------
    # 1. Get the service definition (schema)
    # ------------------------------------------------------------------
    print(f"\n1. Fetching definition for '{SERVICE_NAME}'...")
    print("-" * 50)

    try:
        definition = get_service_definition(
            ui_server_url, SERVICE_NAME, headers, config.verify_ssl
        )

        # Save full definition to JSON file for reference
        output_file = OUTPUT_DIR / f"{SERVICE_NAME.lower()}_definition.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(definition, f, indent=2)
        print(f"  Saved full definition to: {output_file.name}")

        # Show the template structure
        template = definition.get("Template", {})
        transaction_set = template.get("TransactionSet", template)

        print(f"\n  Service: {transaction_set.get('Name')}")
        print(f"  UseCodeValues: {transaction_set.get('UseCodeValues', False)}")

        # Show all DataElements in the template
        transactions = transaction_set.get("Transactions", [])
        if transactions:
            print("\n  DataElements in template:")
            for trans in transactions[:1]:
                for elem in trans.get("DataElements", []):
                    print()
                    print_data_element(elem, indent=2)

        # Show field definitions (required fields, data types, valid values)
        trans_def = definition.get("TransactionDefinition", {})
        data_elem_defs = trans_def.get("DataElementDefinitions", [])

        if data_elem_defs:
            print("\n\n  Field Definitions by DataElement:")
            print("  " + "-" * 48)
            for elem_def in data_elem_defs:
                print(f"\n  DataElement: {elem_def.get('Name')}")
                print(f"  Type: {elem_def.get('Type')}")
                print(f"  Key Fields: {elem_def.get('KeyFields', [])}")
                print("\n  Fields (* = required):")

                field_defs = elem_def.get("FieldDefinitions", [])
                for field in field_defs:
                    print_field_definition(field, indent=2)

                # Summary of required fields
                required_fields = [
                    f.get("Name") for f in field_defs if f.get("Required")
                ]
                if required_fields:
                    print(f"\n  Required fields: {required_fields}")

    except httpx.HTTPStatusError as e:
        print(f"  Error: {e.response.status_code} - {e.response.text[:300]}")
        if e.response.status_code == 404:
            print(f"\n  '{SERVICE_NAME}' service not found.")
            print("  Run 01_list_production_services.py to find the correct name.")
            return

    # ------------------------------------------------------------------
    # 2. Get the default values
    # ------------------------------------------------------------------
    print(f"\n\n2. Fetching defaults for '{SERVICE_NAME}'...")
    print("-" * 50)

    try:
        defaults = get_service_defaults(
            ui_server_url, SERVICE_NAME, headers, config.verify_ssl
        )

        # Save defaults too
        defaults_file = OUTPUT_DIR / f"{SERVICE_NAME.lower()}_defaults.json"
        with open(defaults_file, "w", encoding="utf-8") as f:
            json.dump(defaults, f, indent=2)
        print(f"  Saved defaults to: {defaults_file.name}")

        # Show default values
        data_elements = defaults.get("DataElements", [])
        if data_elements:
            for elem in data_elements:
                print(f"\n  DataElement: {elem.get('Name')}")
                print("  Default values (non-empty only):")
                rows = elem.get("Rows", [])
                if rows:
                    has_defaults = False
                    for edit in rows[0].get("Edits", []):
                        name = edit.get("Name")
                        value = edit.get("Value", "")
                        if value:
                            print(f"    {name}: {value}")
                            has_defaults = True
                    if not has_defaults:
                        print("    (no default values)")
        else:
            print("  No default data elements returned.")

    except httpx.HTTPStatusError as e:
        print(f"  Error: {e.response.status_code} - {e.response.text[:300]}")

    print("\n" + "=" * 60)
    print(f"{SERVICE_NAME} definition exploration complete!")
    print("\nTip: Review the saved JSON files for the complete schema.")


if __name__ == "__main__":
    main()
