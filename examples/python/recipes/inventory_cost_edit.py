"""
Edit Inventory Cost (InventoryCostEdit service)

Set an item's moving average cost at one location -- the usual first half of
writing off stock nobody wants -- then read the cost back over OData. The
save posts to the GL immediately (journal IC, the value difference against
the offset account you supply), so run it on a test tenant first.

Mirrors: docs/recipes/inventory-cost-edit.md

Usage:
    python examples/python/recipes/inventory_cost_edit.py            # dry run (default)
    python examples/python/recipes/inventory_cost_edit.py --item-id ITEM-001 \\
        --location-id 10 --new-cost 0.02 --account-no 1111100 \\
        --year 2026 --period 12 --execute                             # POST + verify
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
ITEM_ID = "ITEM-001"
LOCATION_ID = "10"
NEW_COST = "0.02"  # the new moving average cost per unit
ACCOUNT_NO = "1111100"  # offset GL account, stored form: NO dash
YEAR_FOR_PERIOD = "2026"  # FISCAL year
PERIOD = "12"  # FISCAL period


def row(edits: dict[str, str]) -> dict:
    """Build one Rows entry, edits in the order given (order matters on FORM.account).

    Args:
        edits: Field name -> value.

    Returns:
        dict: A Rows entry.
    """
    return {
        "Edits": [{"Name": k, "Value": v} for k, v in edits.items()],
        "RelativeDateEdits": [],
    }


def build_payload(
    item_id: str,
    location_id: str,
    new_cost: str,
    account_no: str,
    year_for_period: str,
    period: str,
) -> dict:
    """Build the InventoryCostEdit payload: query row, new cost, GL offset.

    Args:
        item_id: Item to edit.
        location_id: Location whose inv_loc row is edited.
        new_cost: New moving average cost per unit.
        account_no: Offset GL account, stored form without the dash.
        year_for_period: Fiscal year to post in.
        period: Fiscal period to post in.

    Returns:
        dict: Complete Transaction API payload.
    """
    keys = {"location_id": location_id, "item_id": item_id}
    return {
        "Name": "InventoryCostEdit",
        "UseCodeValues": False,
        "Transactions": [
            {
                "Status": "New",
                "DataElements": [
                    {
                        "Name": "QUERY.query",
                        "Type": "List",
                        "Keys": ["location_id", "item_id"],
                        "Rows": [row(keys)],
                    },
                    {
                        "Name": "FORM.form",
                        "Type": "Form",
                        "Keys": ["location_id", "item_id"],
                        "Rows": [row({**keys, "new_cost": new_cost})],
                    },
                    # year_for_period BEFORE period: the window validates the period
                    # against the year already in the form.
                    {
                        "Name": "FORM.account",
                        "Type": "Form",
                        "Keys": ["account_no"],
                        "Rows": [
                            row(
                                {
                                    "account_no": account_no,
                                    "year_for_period": year_for_period,
                                    "period": period,
                                }
                            )
                        ],
                    },
                ],
            }
        ],
    }


def read_cost(
    client: httpx.Client, base_url: str, item_id: str, location_id: str
) -> dict | None:
    """Return the inv_loc row (cost, on hand, last maintained by), or None.

    Args:
        client: Authenticated httpx client.
        base_url: P21 base URL.
        item_id: Item to read.
        location_id: Location to read.

    Returns:
        dict | None: The inv_loc row, or None when the item has no row there.
    """
    r = client.get(
        f"{base_url}/odataservice/odata/table/inv_mast",
        params={"$filter": f"item_id eq '{item_id}'", "$select": "inv_mast_uid"},
    )
    r.raise_for_status()
    items = r.json().get("value", [])
    if not items:
        return None
    r = client.get(
        f"{base_url}/odataservice/odata/table/inv_loc",
        params={
            # location_id and inv_mast_uid are numeric -- no quotes
            "$filter": f"inv_mast_uid eq {items[0]['inv_mast_uid']} and location_id eq {location_id}",
            "$select": "moving_average_cost,qty_on_hand,last_maintained_by",
        },
    )
    r.raise_for_status()
    rows = r.json().get("value", [])
    return rows[0] if rows else None


def main() -> None:
    """Entry point: read the cost, POST the edit on --execute, read the cost back."""
    parser = argparse.ArgumentParser(
        description="Edit an item's moving average cost (docs/recipes/inventory-cost-edit.md)"
    )
    parser.add_argument("--item-id", default=ITEM_ID)
    parser.add_argument("--location-id", default=LOCATION_ID)
    parser.add_argument("--new-cost", default=NEW_COST)
    parser.add_argument(
        "--account-no", default=ACCOUNT_NO, help="offset GL account, no dash"
    )
    parser.add_argument(
        "--year", default=YEAR_FOR_PERIOD, help="fiscal year_for_period"
    )
    parser.add_argument("--period", default=PERIOD, help="fiscal period")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually POST the cost edit (default: dry run)",
    )
    args = parser.parse_args()

    print("Recipe - Edit Inventory Cost (InventoryCostEdit)")
    print("=" * 60)

    payload = build_payload(
        args.item_id,
        args.location_id,
        args.new_cost,
        args.account_no,
        args.year,
        args.period,
    )
    if not args.execute:
        print("\nDRY RUN - POST {ui_server}/api/v2/transaction:")
        print(json.dumps(payload, indent=2))
        print("\nRe-run with --execute to POST. The save posts to the GL immediately.")
        return

    config = load_config()
    token = get_token(config)["AccessToken"]
    ui_server = get_ui_server_url(config.base_url, token, config.verify_ssl)
    print(f"UI Server: {ui_server}")

    with httpx.Client(
        headers=get_auth_headers(token),
        verify=config.verify_ssl,
        timeout=300,
        follow_redirects=True,
    ) as client:
        before = read_cost(client, config.base_url, args.item_id, args.location_id)
        if before is None:
            raise SystemExit(
                f"{args.item_id} has no inv_loc row at location "
                f"{args.location_id} -- skip it"
            )
        print(
            f"Before: cost {before['moving_average_cost']}, on hand {before['qty_on_hand']}"
        )
        if float(before["moving_average_cost"]) == float(args.new_cost):
            print("Already at the target cost -- nothing to do")
            return

        resp = client.post(f"{ui_server}/api/v2/transaction", json=payload)
        resp.raise_for_status()  # HTTP 200 even on failure -- check the Summary
        result = resp.json()
        summary = result["Summary"]
        print(f"Succeeded: {summary['Succeeded']}, Failed: {summary['Failed']}")
        if summary["Failed"] or not summary["Succeeded"]:
            for msg in result.get("Messages") or []:
                print(f"  {msg}")
            raise SystemExit("Cost edit failed")

        after = read_cost(client, config.base_url, args.item_id, args.location_id)

    print(
        f"After:  cost {after['moving_average_cost']}, "
        f"last maintained by {after['last_maintained_by']}"
    )
    match = float(after["moving_average_cost"]) == float(args.new_cost)
    print(
        f"Read-back: {'OK' if match else 'MISMATCH -- investigate before continuing'}"
    )


if __name__ == "__main__":
    main()
