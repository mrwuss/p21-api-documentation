"""
Create a Ship-To (ShipTo service)

Add a new ship-to to an existing customer in one stateless Transaction API
call, then read the ship-to, its address and its salesrep grid back over
OData. The ship-to's address_id is assigned by P21 and returned in the
response.

A new ship-to inherits the customer's primary salesrep. To give it a
different rep, the same call adds the wanted rep (primary, 100%) and retires
the inherited one with delete_flag "Y"; when the inherited rep is already the
one you want, the salesrep grid is left out entirely.

Mirrors: docs/recipes/create-ship-to.md

Usage:
    python examples/python/recipes/create_ship_to.py            # dry run (default)
    python examples/python/recipes/create_ship_to.py --customer-id 1001 \\
        --salesrep-id 200 --execute                              # POST + verify
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
COMPANY_ID = "ACME"
CUSTOMER_ID = "1001"  # existing customer
ADDRESS_NAME = "ACME Industrial - East Plant"
DEFAULT_BRANCH = "10"
PREFERRED_LOCATION_ID = "10"
TERMS_ID = "1"  # the STORED terms_id code, not its description
INVOICE_TYPE = "IN"  # stored code ("Invoice" is the label)
TAX_GROUP_ID = "TAX-01"  # stored tax group code
SALESREP_ID = "200"  # the rep this ship-to should carry
ADDRESS = {
    "address1": "456 Industrial Pkwy",
    "city": "Des Moines",
    "state": "IA",
    "postal_code": "50309",
    "country": "USA",
}
PHONE = "515-555-0100"

ROW_STATUS_ACTIVE = 704  # customer_salesrep.row_status_flag "Active"


def form(name: str, edits: dict[str, str]) -> dict:
    """Build one Form DataElement with its Edits.

    Args:
        name: DataElement name, e.g. "TABPAGE_1.shiptomain".
        edits: Field name -> value, in the order they should be applied.

    Returns:
        dict: The DataElement.
    """
    return {
        "Name": name,
        "Type": "Form",
        "Keys": [],
        "Rows": [
            {
                "Edits": [{"Name": k, "Value": v} for k, v in edits.items()],
                "RelativeDateEdits": [],
            }
        ],
    }


def rep_rows(inherited: list[str], salesrep_id: str) -> list[dict]:
    """Salesrep grid rows: add the wanted rep first, then retire each inherited one.

    Args:
        inherited: The customer's live primary rep(s) -- what the ship-to inherits.
        salesrep_id: The rep the ship-to should carry.

    Returns:
        list[dict]: Rows for TABPAGE_SALESREP.tabpage_salesrep; empty when the
        inherited rep is already the wanted one.
    """
    if inherited == [salesrep_id]:
        return []
    rows = [
        {
            "Edits": [
                {"Name": "salesrep_id", "Value": salesrep_id},
                {"Name": "primary_salesrep", "Value": "Y"},
                {"Name": "commission_percentage", "Value": "100"},
            ],
            "RelativeDateEdits": [],
        }
    ]
    for rep in inherited:
        if rep != salesrep_id:
            rows.append(
                {
                    "Edits": [
                        {"Name": "salesrep_id", "Value": rep},
                        {"Name": "delete_flag", "Value": "Y"},
                    ],
                    "RelativeDateEdits": [],
                }
            )
    return rows


def build_payload(args: argparse.Namespace, rows: list[dict]) -> dict:
    """Build the ShipTo create payload.

    Args:
        args: Parsed command-line values.
        rows: Salesrep grid rows from rep_rows(); omitted when empty.

    Returns:
        dict: Complete Transaction API payload.
    """
    elements = [
        form(
            "TABPAGE_1.shiptomain",
            {
                "company_id": args.company_id,
                "customer_id": args.customer_id,
                "address_name": args.address_name,
                "default_branch": args.default_branch,
                "terms_id": args.terms_id,
                "invoice_type": args.invoice_type,
                "tax_group_id": args.tax_group_id,
                "phys_address1": ADDRESS["address1"],
                "phys_city": ADDRESS["city"],
                "phys_state": ADDRESS["state"],
                "phys_postal_code": ADDRESS["postal_code"],
                "phys_country": ADDRESS["country"],
            },
        ),
        form(
            "TABPAGE_2.tp_2_dw_2",
            {
                "mail_address1": ADDRESS["address1"],
                "mail_city": ADDRESS["city"],
                "mail_state": ADDRESS["state"],
                "mail_postal_code": ADDRESS["postal_code"],
                "mail_country": ADDRESS["country"],
            },
        ),
        form("TABPAGE_5.tp_5_dw_5", {"central_phone_number": PHONE}),
        form(
            "TABPAGE_OEOPTIONS.tabpage_oeoptions",
            {"preferred_location_id": args.preferred_location_id},
        ),
    ]
    if rows:
        elements.append(
            {
                "Name": "TABPAGE_SALESREP.tabpage_salesrep",
                "Type": "List",
                "Keys": ["salesrep_id"],
                "Rows": rows,
            }
        )
    return {
        "Name": "ShipTo",
        "UseCodeValues": True,  # send stored codes: terms_id, invoice_type, Y/N flags
        "Transactions": [{"Status": "New", "DataElements": elements}],
    }


def odata(
    client: httpx.Client, base_url: str, table: str, filter_expr: str
) -> list[dict]:
    """Query an OData table and return its value rows.

    Args:
        client: Authenticated httpx client.
        base_url: P21 base URL.
        table: OData table name.
        filter_expr: OData $filter expression.

    Returns:
        list[dict]: Matching rows.
    """
    resp = client.get(
        f"{base_url}/odataservice/odata/table/{table}", params={"$filter": filter_expr}
    )
    resp.raise_for_status()
    return resp.json()["value"]


def generated_address_id(result: dict) -> str | None:
    """Pull the generated address_id out of the passed transaction's result rows.

    Args:
        result: Parsed /api/v2/transaction response.

    Returns:
        str | None: The new ship-to's address_id, or None when absent.
    """
    found = None
    for txn in result["Results"]["Transactions"]:
        if txn.get("Status") != "Passed":
            continue
        for element in txn.get("DataElements", []):
            for row in element.get("Rows", []):
                for edit in row.get("Edits", []):
                    if edit.get("Name") == "address_id" and edit.get("Value"):
                        found = edit["Value"]
    return found


def main() -> None:
    """Entry point: look up the inherited rep, build the payload, POST on --execute, verify."""
    parser = argparse.ArgumentParser(
        description="Create a ship-to on an existing customer (docs/recipes/create-ship-to.md)"
    )
    parser.add_argument("--company-id", default=COMPANY_ID)
    parser.add_argument("--customer-id", default=CUSTOMER_ID)
    parser.add_argument("--address-name", default=ADDRESS_NAME)
    parser.add_argument("--default-branch", default=DEFAULT_BRANCH)
    parser.add_argument("--preferred-location-id", default=PREFERRED_LOCATION_ID)
    parser.add_argument("--terms-id", default=TERMS_ID, help="stored terms code")
    parser.add_argument(
        "--invoice-type", default=INVOICE_TYPE, help="stored code, e.g. IN"
    )
    parser.add_argument("--tax-group-id", default=TAX_GROUP_ID)
    parser.add_argument(
        "--salesrep-id", default=SALESREP_ID, help="rep the ship-to should carry"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually POST the ship-to (default: dry run)",
    )
    args = parser.parse_args()

    print("Recipe - Create a Ship-To (ShipTo)")
    print("=" * 60)

    if not args.execute:
        # The rep swap depends on the customer's live primary rep, read at run
        # time; the dry run shows the swap shape with a placeholder inherited rep.
        payload = build_payload(args, rep_rows(["100"], args.salesrep_id))
        print(
            "\nDRY RUN - POST {ui_server}/api/v2/transaction "
            "(assuming the customer's primary rep is 100):"
        )
        print(json.dumps(payload, indent=2))
        print("\nRe-run with --execute to look up the real primary rep and POST.")
        return

    config = load_config()
    token = get_token(config)["AccessToken"]
    ui_server = get_ui_server_url(config.base_url, token, config.verify_ssl)
    print(f"UI Server: {ui_server}")

    with httpx.Client(
        headers=get_auth_headers(token),
        verify=config.verify_ssl,
        timeout=120,
        follow_redirects=True,
    ) as client:
        # 1. The rep the new ship-to will inherit: the customer's live primary rep.
        #    customer_id is numeric on OData -- no quotes. OData returns the stored
        #    column primary_salesrep_flag; the ShipTo grid calls it primary_salesrep.
        reps = odata(
            client,
            config.base_url,
            "customer_salesrep",
            f"customer_id eq {args.customer_id} "
            f"and row_status_flag eq {ROW_STATUS_ACTIVE}",
        )
        inherited = [
            r["salesrep_id"] for r in reps if r.get("primary_salesrep_flag") == "Y"
        ]
        print(f"Customer's primary rep (inherited by the ship-to): {inherited}")

        payload = build_payload(args, rep_rows(inherited, args.salesrep_id))

        # 2. Create -- HTTP 200 even on failure, so check the Summary
        resp = client.post(f"{ui_server}/api/v2/transaction", json=payload)
        resp.raise_for_status()
        result = resp.json()
        summary = result["Summary"]
        print(f"Succeeded: {summary['Succeeded']}, Failed: {summary['Failed']}")
        if summary["Failed"] or not summary["Succeeded"]:
            for msg in result.get("Messages", []):
                print(f"  {msg}")
            raise SystemExit("Ship-to create failed")

        ship_to_id = generated_address_id(result)
        print(f"Created ship-to (address_id): {ship_to_id}")
        if not ship_to_id:
            raise SystemExit(
                "No address_id in the response -- look the ship-to up by name"
            )

        # 3. Read back via OData -- Succeeded is not proof every value landed
        print("\nVerify (OData read-back):")
        for row in odata(
            client, config.base_url, "ship_to", f"ship_to_id eq {ship_to_id}"
        ):
            print(
                "  ship_to:",
                {
                    k: row.get(k)
                    for k in (
                        "ship_to_id",
                        "customer_id",
                        "default_branch",
                        "terms_id",
                        "invoice_type",
                        "tax_group_id",
                        "preferred_location_id",
                    )
                },
            )
        for row in odata(client, config.base_url, "address", f"id eq {ship_to_id}"):
            print(
                "  address:",
                {
                    k: row.get(k)
                    for k in (
                        "name",
                        "phys_address1",
                        "phys_city",
                        "mail_address1",
                        "central_phone_number",
                    )
                },
            )
        live = []
        for row in odata(
            client, config.base_url, "ship_to_salesrep", f"ship_to_id eq {ship_to_id}"
        ):
            print(
                "  rep:",
                {
                    k: row.get(k)
                    for k in (
                        "salesrep_id",
                        "primary_salesrep",
                        "commission_percentage",
                        "delete_flag",
                    )
                },
            )
            if row.get("delete_flag") != "Y":
                live.append(row)
    ok = (
        len(live) == 1
        and live[0]["salesrep_id"] == args.salesrep_id
        and live[0].get("primary_salesrep") == "Y"
        and float(live[0].get("commission_percentage") or 0) == 100
    )
    print(
        f"\nOne live primary rep {args.salesrep_id} at 100%: {'OK' if ok else 'MISMATCH'}"
    )


if __name__ == "__main__":
    main()
