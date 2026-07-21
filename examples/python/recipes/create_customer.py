"""
Create a Customer (Customer service)

Create a customer master record in one stateless Transaction API call,
extract the auto-assigned customer_id from the result rows, and read it
back via OData.

The defaults template supplies company_id, terms_id, and customer_type_cd;
a minimal create only sends customer_name, salesrep_id, the mailing address,
and default_branch. Two non-obvious required fields trip people up -- see the
notes below and docs/recipes/create-customer.md.

Mirrors: docs/recipes/create-customer.md

Usage:
    python examples/python/recipes/create_customer.py            # dry run (default)
    python examples/python/recipes/create_customer.py --execute  # POST + verify
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from common.auth import get_token, get_auth_headers, get_ui_server_url
from common.config import load_config

import warnings
warnings.filterwarnings("ignore")

# --- Configuration (generic placeholders -- substitute your own) ------------
CUSTOMER_NAME = "ACME Industrial Supply"
SALESREP_ID = "100"        # hard-required; error surfaces on the ship-to (see below)
MAIL_ADDRESS1 = "123 Main St"
MAIL_CITY = "Des Moines"
MAIL_STATE = "IA"
MAIL_POSTAL_CODE = "50309"
MAIL_COUNTRY = "USA"
DEFAULT_BRANCH = "10"      # required, NOT defaulted by the template


def build_customer_payload() -> dict:
    """Build the Customer payload: TABPAGE_1 form + ship-to general form.

    customer_id is auto-assigned -- leave it out. company_id, terms_id, and
    customer_type_cd come from the defaults template.

    Returns:
        dict: Complete Transaction API payload.
    """
    return {
        "Name": "Customer",
        "UseCodeValues": False,
        "Transactions": [{
            "Status": "New",
            "DataElements": [
                {
                    "Name": "TABPAGE_1.tp_1_dw_1",
                    "Type": "Form",
                    "Keys": [],
                    "Rows": [{
                        "Edits": [
                            {"Name": "customer_name",    "Value": CUSTOMER_NAME},
                            {"Name": "salesrep_id",      "Value": SALESREP_ID},
                            {"Name": "mail_address1",    "Value": MAIL_ADDRESS1},
                            {"Name": "mail_city",        "Value": MAIL_CITY},
                            {"Name": "mail_state",       "Value": MAIL_STATE},
                            {"Name": "mail_postal_code", "Value": MAIL_POSTAL_CODE},
                            {"Name": "mail_country",     "Value": MAIL_COUNTRY},
                        ],
                        "RelativeDateEdits": [],
                    }],
                },
                {
                    "Name": "SHIP_TO_GENERAL.ship_to_general",
                    "Type": "Form",
                    "Keys": [],
                    "Rows": [{
                        "Edits": [
                            {"Name": "default_branch", "Value": DEFAULT_BRANCH},
                        ],
                        "RelativeDateEdits": [],
                    }],
                },
            ],
        }],
    }


def extract_customer_id(result: dict) -> str | None:
    """Pull the generated customer_id out of the TABPAGE_1.tp_1_dw_1 result rows.

    Args:
        result: Parsed JSON response from POST /api/v2/transaction.

    Returns:
        str | None: The generated customer id, if present.
    """
    customer_id = None
    for txn in result["Results"]["Transactions"]:
        if txn.get("Status") != "Passed":
            continue
        for element in txn.get("DataElements", []):
            if element.get("Name") != "TABPAGE_1.tp_1_dw_1":
                continue
            for row in element.get("Rows", []):
                for edit in row.get("Edits", []):
                    if edit.get("Name") == "customer_id":
                        customer_id = edit.get("Value")
    return customer_id


def main() -> None:
    """Entry point: build payload, POST on --execute, then verify via OData."""
    parser = argparse.ArgumentParser(
        description="Create a customer (docs/recipes/create-customer.md)")
    parser.add_argument("--execute", action="store_true",
                        help="Actually POST the transaction (default: dry run)")
    args = parser.parse_args()

    print("Recipe - Create a Customer (Customer service)")
    print("=" * 60)

    payload = build_customer_payload()

    if not args.execute:
        print("\nDRY RUN - payload that would be POSTed to {ui_server}/api/v2/transaction:")
        print(json.dumps(payload, indent=2))
        print("\nRe-run with --execute to POST it.")
        return

    config = load_config()
    token_data = get_token(config)
    headers = get_auth_headers(token_data["AccessToken"])
    ui_server = get_ui_server_url(config.base_url, token_data["AccessToken"], config.verify_ssl)
    print(f"UI Server: {ui_server}")

    response = httpx.post(f"{ui_server}/api/v2/transaction",
                          headers=headers, json=payload, verify=config.verify_ssl,
                          follow_redirects=True, timeout=120)
    response.raise_for_status()
    result = response.json()

    # HTTP 200 even on failure -- check the Summary, never the status code.
    # Two common failures: "Salesrep ID is required for a new ship to."
    # (supply salesrep_id) and "'Default Branch' is a required column."
    summary = result["Summary"]
    print(f"Succeeded: {summary['Succeeded']}, Failed: {summary['Failed']}")
    if summary["Failed"] > 0 or summary["Succeeded"] == 0:
        for msg in result.get("Messages", []):
            print(f"  {msg}")
        raise SystemExit("Customer create failed")

    customer_id = extract_customer_id(result)
    print(f"Created customer_id: {customer_id}")
    if not customer_id:
        raise SystemExit("No customer_id in the result rows")

    # --- Verify: read the customer back via OData ---
    print("\nVerify (OData read-back):")
    cust_resp = httpx.get(
        f"{config.base_url}/odataservice/odata/table/customer",
        params={"$filter": f"customer_id eq {customer_id}",
                "$select": "customer_id,customer_name,salesrep_id"},
        headers=headers, verify=config.verify_ssl, follow_redirects=True,
    )
    cust_resp.raise_for_status()
    for cust in cust_resp.json()["value"]:
        print(f"  customer_id={cust.get('customer_id')} "
              f"name={cust.get('customer_name')} salesrep_id={cust.get('salesrep_id')}")


if __name__ == "__main__":
    main()
