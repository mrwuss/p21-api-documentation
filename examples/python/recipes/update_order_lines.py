"""Modify an existing sales order: update a line in place + add a line.

Dry run by default; pass --execute to POST. Mirrors docs/recipes/update-order-lines.md.
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
ORDER_NO = "1013938"

# (user_line_no, item_id, quantity)
# An EXISTING handle updates that line; a NEW handle inserts a line.
LINES = [
    ("010", "WIDGET-001", "4"),   # existing handle -> quantity updated in place
    ("030", "WIDGET-002", "1"),   # new handle      -> line inserted
]


def build_payload() -> dict:
    """Header loads the order by key; the keyed items list upserts each row."""
    return {
        "Name": "Order",
        "UseCodeValues": False,
        "Transactions": [{
            "Status": "New",
            "DataElements": [
                {
                    "Name": "TABPAGE_1.order",
                    "Type": "Form",
                    "Keys": ["order_no"],
                    # ONLY the key. Re-sending header fields fails on
                    # disabled columns (customer_id) once the order exists.
                    "Rows": [{
                        "Edits": [{"Name": "order_no", "Value": ORDER_NO}],
                        "RelativeDateEdits": [],
                    }],
                },
                {
                    "Name": "TP_ITEMS.items",
                    "Type": "List",
                    "Keys": ["user_line_no"],
                    "Rows": [
                        {"Edits": [
                            {"Name": "user_line_no",     "Value": handle},
                            {"Name": "oe_order_item_id", "Value": item_id},
                            {"Name": "unit_quantity",    "Value": qty},
                        ], "RelativeDateEdits": []}
                        for handle, item_id, qty in LINES
                    ],
                },
            ],
        }],
    }


def read_lines(ui_server: str, headers: dict, verify_ssl: bool) -> list[dict]:
    """Read the order's lines back -- the only proof the write landed."""
    resp = httpx.post(
        f"{ui_server}/api/v2/transaction/get",
        headers=headers, verify=verify_ssl, follow_redirects=True, timeout=120,
        json={"ServiceName": "Order", "TransactionStates": [{
            "DataElementName": "TABPAGE_1.order",
            "Keys": [{"Name": "order_no", "Value": ORDER_NO}],
        }]},
    )
    resp.raise_for_status()
    for element in resp.json()["Transactions"][0]["DataElements"]:
        if element["Name"] != "TP_ITEMS.items":
            continue
        rows = [{edit["Name"]: edit["Value"] for edit in row.get("Edits", [])}
                for row in element.get("Rows", [])]
        return [row for row in rows if row.get("oe_order_item_id")]
    return []


def main() -> None:
    """Entry point: build the payload, POST on --execute, read the lines back."""
    parser = argparse.ArgumentParser(
        description="Modify an existing sales order (docs/recipes/update-order-lines.md)")
    parser.add_argument("--execute", action="store_true",
                        help="Actually POST the transaction (default: dry run)")
    args = parser.parse_args()

    print("Recipe - Modify an Existing Sales Order")
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

    print("\nBefore:")
    for row in read_lines(ui_server, headers, config.verify_ssl):
        print(f"  {row.get('user_line_no')}: {row.get('oe_order_item_id')}"
              f" x {row.get('unit_quantity')}")

    resp = httpx.post(f"{ui_server}/api/v2/transaction", headers=headers,
                      json=payload, verify=config.verify_ssl,
                      follow_redirects=True, timeout=120)
    resp.raise_for_status()          # HTTP 200 does NOT mean the write succeeded
    result = resp.json()
    print(f"\nSummary: {result['Summary']}")
    for message in result.get("Messages") or []:
        print(f"  Message: {message}")

    print("\nAfter (read-back is the only proof):")
    for row in read_lines(ui_server, headers, config.verify_ssl):
        print(f"  {row.get('user_line_no')}: {row.get('oe_order_item_id')}"
              f" x {row.get('unit_quantity')}")


if __name__ == "__main__":
    main()
