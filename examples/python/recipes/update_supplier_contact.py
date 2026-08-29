"""
Update a Supplier's Contact Info (Address service)

Write a supplier's email address and central phone number, then read them
back through the same service.

The catch is where these fields live. supplier.supplier_id shares its id
with an address row (address.id == supplier_id), and the email and central
phone that purchasing documents and views surface come from
address.email_address and address.central_phone_number -- not from the
supplier table, whose only email-ish columns are email_po_flag and
supplier_redemption_email. So the write goes through the Address service,
which is also the smaller surface: ~9 KB of definition against ~70 KB for
Supplier, keyed on nothing but the address id.

Two payload details worth keeping:

  * Status "New" is the upsert shape. An existing id updates that record;
    "New" is the only value the Status enum accepts.
  * IgnoreIfEmpty: True on the contact edits means an empty value leaves the
    stored field untouched. This payload can add or replace contact info but
    can never blank it -- which is the safe default for a bulk run.

Mirrors: docs/recipes/update-supplier-contact.md

Usage:
    python examples/python/recipes/update_supplier_contact.py            # dry run (default)
    python examples/python/recipes/update_supplier_contact.py --execute  # POST + verify
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
SUPPLIER_ID = "10050"                    # address.id == supplier.supplier_id
EMAIL_ADDRESS = "orders@example.com"
CENTRAL_PHONE = "319-555-0100"

CONTACT_TAB = "TABPAGE_3.tp_3_dw_3"      # Phone tab: email + central phone/fax


def build_payload() -> dict:
    """Build the Address payload that sets email and central phone.

    IgnoreDisabled is set because several Address columns are read-only once
    the record exists. Per docs/14 entry 8 the flag can also report success
    while writing nothing, which is exactly why main() reads back.

    Returns:
        dict: Complete Transaction API payload.
    """
    return {
        "Name": "Address",
        "UseCodeValues": False,
        "IgnoreDisabled": True,
        "Transactions": [{
            "Status": "New",
            "DataElements": [
                {
                    "Name": "TABPAGE_1.tp_1_dw_1",
                    "Type": "Form",
                    "Keys": ["id"],
                    "Rows": [{
                        "Edits": [
                            {"Name": "id", "Value": SUPPLIER_ID,
                             "IgnoreIfEmpty": False},
                        ],
                        "RelativeDateEdits": [],
                    }],
                },
                {
                    "Name": CONTACT_TAB,
                    "Type": "Form",
                    "Keys": [],
                    "Rows": [{
                        "Edits": [
                            {"Name": "email_address", "Value": EMAIL_ADDRESS,
                             "IgnoreIfEmpty": True},
                            {"Name": "address_central_phone_number",
                             "Value": CENTRAL_PHONE, "IgnoreIfEmpty": True},
                        ],
                        "RelativeDateEdits": [],
                    }],
                },
            ],
        }],
    }


def read_contact(ui_server: str, headers: dict, verify_ssl: bool) -> dict:
    """Read the address record back and return its contact fields.

    Args:
        ui_server: UI Server base URL.
        headers: Authorization headers.
        verify_ssl: Whether to verify TLS certificates.

    Returns:
        dict: Field name -> value for the contact tab, empty if not found.
    """
    resp = httpx.post(
        f"{ui_server}/api/v2/transaction/get",
        headers=headers, verify=verify_ssl, follow_redirects=True, timeout=120,
        json={"ServiceName": "Address", "TransactionStates": [{
            "DataElementName": "TABPAGE_1.tp_1_dw_1",
            "Keys": [{"Name": "id", "Value": SUPPLIER_ID}],
        }]},
    )
    resp.raise_for_status()
    for element in resp.json()["Transactions"][0]["DataElements"]:
        if element["Name"] != CONTACT_TAB:
            continue
        rows = element.get("Rows") or []
        if not rows:
            return {}
        return {edit["Name"]: edit["Value"] for edit in rows[0].get("Edits", [])}
    return {}


def show(label: str, contact: dict) -> None:
    """Print the two fields this recipe writes.

    Args:
        label: Heading to print above the values.
        contact: Mapping returned by read_contact().
    """
    print(f"\n{label}")
    print(f"  email_address                = {contact.get('email_address', '')!r}")
    print("  address_central_phone_number = "
          f"{contact.get('address_central_phone_number', '')!r}")


def main() -> None:
    """Entry point: build the payload, POST on --execute, read the record back."""
    parser = argparse.ArgumentParser(
        description="Update supplier contact info "
                    "(docs/recipes/update-supplier-contact.md)")
    parser.add_argument("--execute", action="store_true",
                        help="Actually POST the transaction (default: dry run)")
    args = parser.parse_args()

    print("Recipe - Update Supplier Contact Info")
    print("=" * 60)

    payload = build_payload()
    if not args.execute:
        print("\nDRY RUN - would POST to {ui_server}/api/v2/transaction:")
        print(json.dumps(payload, indent=2))
        print("\nRe-run with --execute to POST the transaction.")
        return

    config = load_config()
    token_data = get_token(config)
    headers = get_auth_headers(token_data["AccessToken"])
    ui_server = get_ui_server_url(config.base_url, token_data["AccessToken"],
                                  config.verify_ssl)
    print(f"UI Server: {ui_server}")

    show("Before:", read_contact(ui_server, headers, config.verify_ssl))

    resp = httpx.post(f"{ui_server}/api/v2/transaction", headers=headers,
                      json=payload, verify=config.verify_ssl,
                      follow_redirects=True, timeout=120)
    resp.raise_for_status()          # HTTP 200 does NOT mean the write succeeded
    result = resp.json()
    print(f"\nSummary: {result['Summary']}")
    for message in result.get("Messages") or []:
        print(f"  Message: {message}")

    # IgnoreDisabled can report Succeeded and write nothing -- docs/14 entry 8.
    show("After (read-back is the only proof):",
         read_contact(ui_server, headers, config.verify_ssl))


if __name__ == "__main__":
    main()
