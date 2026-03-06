"""
Transaction API - Get ProductionOrder Service Definition

Retrieves the schema for the ProductionOrder service to understand
its DataElements, field definitions, and especially the labor-related
and completion-related structures.

Usage:
    python scripts/production/04_get_production_order_definition.py
"""

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import httpx
from common.auth import get_token, get_auth_headers, get_ui_server_url
from common.config import load_config

import warnings
warnings.filterwarnings("ignore")

SERVICE_NAME = "ProductionOrder"
OUTPUT_DIR = Path(__file__).parent

# Keywords for highlighting labor/completion-related DataElements and fields
LABOR_KEYWORDS = [
    "labor", "time", "technician", "hours", "worked", "rate",
    "cost", "completion", "complete", "finish", "quantity",
]


def get_service_definition(
    ui_server_url: str, service_name: str, headers: dict, verify_ssl: bool
) -> dict:
    """Fetch the definition for a service."""
    response = httpx.get(
        f"{ui_server_url}/api/v2/definition/{service_name}",
        headers=headers,
        verify=verify_ssl,
        follow_redirects=True,
        timeout=60.0,
    )
    response.raise_for_status()
    return response.json()


def is_labor_related(name: str) -> bool:
    """Check if a name matches labor/completion keywords."""
    lower_name = name.lower()
    return any(kw in lower_name for kw in LABOR_KEYWORDS)


def print_data_element_summary(element: dict, indent: int = 0) -> None:
    """Print a concise summary of a DataElement."""
    prefix = "  " * indent
    name = element.get("Name", "Unknown")
    elem_type = element.get("Type", "Unknown")
    keys = element.get("Keys", [])

    # Highlight labor-related elements
    marker = " *** LABOR/COMPLETION ***" if is_labor_related(name) else ""
    print(f"{prefix}{name} (Type: {elem_type}){marker}")
    if keys:
        print(f"{prefix}  Keys: {keys}")

    rows = element.get("Rows", [])
    if rows:
        edits = rows[0].get("Edits", [])
        print(f"{prefix}  Fields: {len(edits)}")


def print_field_definition(field_def: dict, indent: int = 0) -> None:
    """Print a field definition with type and required status."""
    prefix = "  " * indent
    name = field_def.get("Name", "Unknown")
    data_type = field_def.get("DataType", "Unknown")
    required = field_def.get("Required", False)
    label = field_def.get("Label", "")
    valid_values = field_def.get("ValidValues")

    # Highlight labor-related fields
    marker = " <-- LABOR" if is_labor_related(name) else ""
    req_marker = "*" if required else " "
    print(f"{prefix}{req_marker} {name} ({data_type}): {label}{marker}")

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
    # 1. Get the service definition
    # ------------------------------------------------------------------
    print(f"\n1. Fetching definition for '{SERVICE_NAME}'...")
    print("-" * 50)

    try:
        definition = get_service_definition(
            ui_server_url, SERVICE_NAME, headers, config.verify_ssl
        )

        # Save full definition to JSON for reference
        output_file = OUTPUT_DIR / f"{SERVICE_NAME.lower()}_definition.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(definition, f, indent=2)
        print(f"  Saved full definition to: {output_file.name}")

    except httpx.HTTPStatusError as e:
        print(f"  Error: {e.response.status_code} - {e.response.text[:300]}")
        if e.response.status_code == 404:
            print(f"\n  '{SERVICE_NAME}' service not found.")
            print("  Run 01_list_production_services.py to find the correct name.")
        return

    # ------------------------------------------------------------------
    # 2. Show all DataElements in the template
    # ------------------------------------------------------------------
    template = definition.get("Template", {})
    transaction_set = template.get("TransactionSet", template)

    print(f"\n  Service: {transaction_set.get('Name')}")
    print(f"  UseCodeValues: {transaction_set.get('UseCodeValues', False)}")

    transactions = transaction_set.get("Transactions", [])
    if transactions:
        print("\n2. All DataElements in template:")
        print("-" * 50)
        for trans in transactions[:1]:
            elements = trans.get("DataElements", [])
            print(f"  Total DataElements: {len(elements)}\n")
            for elem in elements:
                print_data_element_summary(elem, indent=1)
                print()

    # ------------------------------------------------------------------
    # 3. Show full field definitions, grouped by DataElement
    # ------------------------------------------------------------------
    trans_def = definition.get("TransactionDefinition", {})
    data_elem_defs = trans_def.get("DataElementDefinitions", [])

    if data_elem_defs:
        print("\n3. Field Definitions by DataElement:")
        print("-" * 50)

        # First pass: show all element names for overview
        print("\n  DataElement overview:")
        for elem_def in data_elem_defs:
            name = elem_def.get("Name", "Unknown")
            field_count = len(elem_def.get("FieldDefinitions", []))
            marker = " *** LABOR/COMPLETION ***" if is_labor_related(name) else ""
            print(f"    {name} ({field_count} fields){marker}")

        # Second pass: show full details for each DataElement
        for elem_def in data_elem_defs:
            elem_name = elem_def.get("Name", "Unknown")
            elem_type = elem_def.get("Type", "Unknown")
            key_fields = elem_def.get("KeyFields", [])
            field_defs = elem_def.get("FieldDefinitions", [])

            print(f"\n  {'=' * 48}")
            marker = " *** LABOR/COMPLETION ***" if is_labor_related(elem_name) else ""
            print(f"  DataElement: {elem_name}{marker}")
            print(f"  Type: {elem_type}")
            print(f"  Key Fields: {key_fields}")
            print(f"  Total Fields: {len(field_defs)}")
            print(f"\n  Fields (* = required):")

            for field in field_defs:
                print_field_definition(field, indent=2)

            # Summary of required fields
            required_fields = [
                f.get("Name") for f in field_defs if f.get("Required")
            ]
            if required_fields:
                print(f"\n  Required: {required_fields}")

    # ------------------------------------------------------------------
    # 4. Highlight labor-specific fields across all DataElements
    # ------------------------------------------------------------------
    print("\n\n4. Labor-Related Fields (across all DataElements):")
    print("-" * 50)

    labor_fields_found = False
    for elem_def in data_elem_defs:
        elem_name = elem_def.get("Name", "Unknown")
        field_defs = elem_def.get("FieldDefinitions", [])

        labor_fields = [f for f in field_defs if is_labor_related(f.get("Name", ""))]
        if labor_fields:
            labor_fields_found = True
            print(f"\n  {elem_name}:")
            for field in labor_fields:
                print_field_definition(field, indent=2)

    if not labor_fields_found:
        print("  No fields matching labor/completion keywords found.")
        print("  The production order may use separate services for labor recording.")
        print("  Check the TimeEntry service instead (02_get_timeentry_definition.py).")

    print("\n" + "=" * 60)
    print(f"{SERVICE_NAME} definition exploration complete!")
    print("\nNext steps:")
    print("  1. Review the saved JSON file for complete schema details")
    print("  2. Use 02_get_timeentry_definition.py for labor recording schema")
    print("  3. Use 03_record_labor_hours.py to submit labor entries")


if __name__ == "__main__":
    main()
