"""
Transaction API - Record Labor Hours Against a Production Order

Demonstrates recording technician labor hours using the TimeEntry
Transaction API service. This creates a labor recording entry that
associates a technician's worked time with a production order.

IMPORTANT: Run 02_get_timeentry_definition.py first to verify the
exact field names and DataElement structure for your P21 version.
The field names below are based on the standard TimeEntry service
definition and may need adjustment.

Usage:
    python scripts/production/03_record_labor_hours.py
"""

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import httpx
from datetime import datetime, timedelta
from common.auth import get_token, get_auth_headers, get_ui_server_url
from common.config import load_config

import warnings
warnings.filterwarnings("ignore")


def build_timeentry_payload(
    company_id: str,
    technician_id: str,
    entry_date: str,
    prod_order_number: int,
    service_labor_id: str,
    start_time: str,
    end_time: str,
    time_worked: float,
    labor_type_cd: str = "Rate",
) -> dict:
    """Build a Transaction API payload for recording labor hours.

    The TimeEntry service typically uses two DataElements:
      1. TP_TECHNICIAN.tp_technician - Header with technician/date info
      2. TP_LABORRECORDING.prod_order_line_comp_labor - Line item with
         production order details and time worked

    NOTE: The exact DataElement names (e.g., "TP_TECHNICIAN.tp_technician")
    come from the service definition. Run 02_get_timeentry_definition.py
    to confirm these names match your P21 version.

    Args:
        company_id: Company identifier (e.g., "ACME")
        technician_id: Technician/employee ID who performed the work
        entry_date: Date of the labor entry (YYYY-MM-DD format)
        prod_order_number: Production order number to record hours against
        service_labor_id: Service/labor code identifier
        start_time: Start time of work (HH:MM format)
        end_time: End time of work (HH:MM format)
        time_worked: Total hours worked (decimal, e.g., 2.5 for 2h 30m)
        labor_type_cd: Labor type code. Common values:
            - "Rate": Standard rate-based labor (default)
            - "Fixed": Fixed-cost labor
            - "None": No labor cost

    Returns:
        dict: Transaction API payload ready for POST to /api/v2/transaction
    """
    return {
        "Name": "TimeEntry",
        "UseCodeValues": False,
        "Transactions": [
            {
                "Status": "New",
                "DataElements": [
                    # --------------------------------------------------
                    # Header: Technician identification and entry date
                    # --------------------------------------------------
                    {
                        "Name": "TP_TECHNICIAN.tp_technician",
                        "Type": "Form",
                        "Keys": [],
                        "Rows": [
                            {
                                "Edits": [
                                    # Company this labor entry belongs to
                                    {"Name": "company_id", "Value": company_id},
                                    # Technician/employee performing the work
                                    {"Name": "technician_id", "Value": technician_id},
                                    # Date the labor was performed
                                    {"Name": "entry_date", "Value": entry_date},
                                ],
                                "RelativeDateEdits": [],
                            }
                        ],
                    },
                    # --------------------------------------------------
                    # Line: Production order labor details
                    # --------------------------------------------------
                    {
                        "Name": "TP_LABORRECORDING.prod_order_line_comp_labor",
                        "Type": "Form",
                        "Keys": [],
                        "Rows": [
                            {
                                "Edits": [
                                    # Production order to charge hours against
                                    {
                                        "Name": "prod_order_no",
                                        "Value": float(prod_order_number),
                                    },
                                    # Service/labor code (defines the type of work)
                                    {
                                        "Name": "service_labor_id",
                                        "Value": service_labor_id,
                                    },
                                    # Start time of the labor period
                                    {"Name": "start_time", "Value": start_time},
                                    # End time of the labor period
                                    {"Name": "end_time", "Value": end_time},
                                    # Total hours worked (decimal hours)
                                    {
                                        "Name": "time_worked",
                                        "Value": float(time_worked),
                                    },
                                    # Labor type determines how cost is calculated:
                                    #   "Rate" = hourly rate * time_worked
                                    #   "Fixed" = flat amount
                                    #   "None" = no cost
                                    {
                                        "Name": "labor_type_cd",
                                        "Value": labor_type_cd,
                                    },
                                ],
                                "RelativeDateEdits": [],
                            }
                        ],
                    },
                ],
            }
        ],
    }


def submit_transaction(
    ui_server_url: str, payload: dict, headers: dict, verify_ssl: bool
) -> dict:
    """Submit a Transaction API request."""
    response = httpx.post(
        f"{ui_server_url}/api/v2/transaction",
        headers=headers,
        json=payload,
        verify=verify_ssl,
        follow_redirects=True,
        timeout=30.0,
    )
    response.raise_for_status()
    return response.json()


def main() -> None:
    print("Transaction API - Record Labor Hours")
    print("=" * 60)

    config = load_config()
    token_data = get_token(config)
    headers = get_auth_headers(token_data["AccessToken"])
    ui_server_url = get_ui_server_url(
        config.base_url, token_data["AccessToken"], config.verify_ssl
    )
    print(f"UI Server: {ui_server_url}")

    # ------------------------------------------------------------------
    # Build the labor entry payload with generic test data
    # ------------------------------------------------------------------
    # NOTE: Replace these values with valid data for your P21 environment.
    # Using obviously fake values to prevent accidental real transactions.
    entry_date = datetime.now().strftime("%Y-%m-%d")
    start_time = "08:00"
    end_time = "10:30"
    time_worked = 2.5  # 2 hours 30 minutes

    print(f"\nBuilding labor entry:")
    print(f"  Company:          ACME")
    print(f"  Technician:       TECH001")
    print(f"  Date:             {entry_date}")
    print(f"  Production Order: 1001")
    print(f"  Service/Labor ID: LABOR-STD")
    print(f"  Time:             {start_time} - {end_time} ({time_worked}h)")
    print(f"  Labor Type:       Rate")

    payload = build_timeentry_payload(
        company_id="ACME",
        technician_id="TECH001",
        entry_date=entry_date,
        prod_order_number=1001,
        service_labor_id="LABOR-STD",
        start_time=start_time,
        end_time=end_time,
        time_worked=time_worked,
        labor_type_cd="Rate",
    )

    # ------------------------------------------------------------------
    # Show the payload structure before submitting
    # ------------------------------------------------------------------
    print("\n" + "-" * 50)
    print("Request payload structure:")
    print(f"  Service: {payload['Name']}")
    print(f"  UseCodeValues: {payload['UseCodeValues']}")
    print(f"  Transactions: {len(payload['Transactions'])}")
    for i, trans in enumerate(payload["Transactions"]):
        print(f"  Transaction[{i}]:")
        print(f"    Status: {trans['Status']}")
        print(f"    DataElements: {len(trans['DataElements'])}")
        for elem in trans["DataElements"]:
            field_count = len(elem["Rows"][0]["Edits"])
            print(f"      - {elem['Name']} ({field_count} fields)")

    print("\nFull payload:")
    print(json.dumps(payload, indent=2))

    # ------------------------------------------------------------------
    # Submit the transaction
    # ------------------------------------------------------------------
    print("\n" + "-" * 50)
    print("Submitting labor entry...")

    try:
        result = submit_transaction(
            ui_server_url, payload, headers, config.verify_ssl
        )

        # Parse the response
        summary = result.get("Summary", {})
        succeeded = summary.get("Succeeded", 0)
        failed = summary.get("Failed", 0)
        messages = result.get("Messages", [])

        print(f"\n  Response Summary:")
        print(f"    Succeeded: {succeeded}")
        print(f"    Failed:    {failed}")

        if messages:
            print(f"    Messages:")
            for msg in messages:
                print(f"      - {msg}")

        if succeeded > 0:
            # Extract created record details from the results
            results = result.get("Results", {})
            transactions = results.get("Transactions", [])

            if transactions:
                trans = transactions[0]
                status = trans.get("Status")
                print(f"\n    Transaction Status: {status}")

                # Show returned data elements and any generated IDs
                for elem in trans.get("DataElements", []):
                    print(f"\n    DataElement: {elem.get('Name')}")
                    for row in elem.get("Rows", []):
                        for edit in row.get("Edits", []):
                            name = edit.get("Name")
                            value = edit.get("Value", "")
                            if value:
                                print(f"      {name}: {value}")

            print("\n  SUCCESS: Labor hours recorded!")
        else:
            print("\n  FAILED: Labor entry not created")
            print("  Check messages above for details.")
            print("\n  Common failure reasons:")
            print("    - Invalid technician_id (must exist in P21)")
            print("    - Invalid prod_order_no (must be an open production order)")
            print("    - Invalid service_labor_id (must be a valid labor code)")
            print("    - Missing required fields (run 02_get_timeentry_definition.py)")

        # Always show full response for debugging
        print(f"\n  Full response:")
        print(json.dumps(result, indent=2))

    except httpx.HTTPStatusError as e:
        print(f"\n  HTTP Error: {e.response.status_code}")
        print(f"  Response: {e.response.text[:500]}")

        if e.response.status_code == 404:
            print("\n  The 'TimeEntry' service may not exist on this P21 instance.")
            print("  Run 01_list_production_services.py to find the correct service name.")
        elif e.response.status_code == 400:
            print("\n  Bad request - the payload structure may be incorrect.")
            print("  Run 02_get_timeentry_definition.py to verify the DataElement names.")

    except Exception as e:
        print(f"\n  Error: {type(e).__name__}: {e}")

    print("\n" + "=" * 60)
    print("Labor hours recording example complete!")


if __name__ == "__main__":
    main()
