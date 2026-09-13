"""
Other REST Families - CRM Task CRUD Round Trip (sales/tasks)

Create -> read -> update a P21 CRM task (activity_trans) via sales/tasks.
Dry run by default; --execute actually posts.

Mirrors: docs/15-Other-REST-Families.md#salestasks

Key rules (verified live, 26.1.5950.0):
    - There is no CustomerId field on the object. The create fails
      "Customer ID is required" and the error also says "CRUD Update
      error: Update failed" on what is a CREATE -- the middleware routes
      both verbs through one CRUD path. The customer goes in LinkId,
      paired with LinkTypeCd (1203 in the server's own /new template).
    - ContactAddressName is server-derived from LinkId -- do not set it.
    - There is no delete route. Close a task with Completed: "Y".
    - GET /api/sales/tasks/ (no key) is an UNBOUNDED collection dump --
      never call it. This script only ever uses /new and keyed routes.

Usage:
    python examples/python/rest/task_crud.py                    # dry run
    python examples/python/rest/task_crud.py --execute \\
        --contact-id 17055 --customer-id 12066
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from common.auth import get_token, get_auth_headers
from common.config import load_config

import warnings
warnings.filterwarnings("ignore")


def get_new_template(base_url: str, headers: dict, verify_ssl: bool) -> dict:
    """GET the server-defaulted template for a new task."""
    response = httpx.get(
        f"{base_url}/api/sales/tasks/new",
        headers=headers, verify=verify_ssl, follow_redirects=True, timeout=30.0,
    )
    response.raise_for_status()
    return response.json()


def create_task(base_url: str, headers: dict, verify_ssl: bool, task: dict) -> dict:
    """POST a new task. Trailing slash matters -- the list route 307s without it."""
    response = httpx.post(
        f"{base_url}/api/sales/tasks/",
        headers={**headers, "Content-Type": "application/json"},
        json=task, verify=verify_ssl, follow_redirects=True, timeout=60.0,
    )
    response.raise_for_status()
    return response.json()


def get_task(base_url: str, headers: dict, verify_ssl: bool, task_no: str) -> dict:
    """GET one task by ActivityTransNo."""
    response = httpx.get(
        f"{base_url}/api/sales/tasks/{task_no}",
        headers=headers, verify=verify_ssl, follow_redirects=True, timeout=30.0,
    )
    response.raise_for_status()
    return response.json()


def update_task(base_url: str, headers: dict, verify_ssl: bool, task_no: str,
                 task: dict) -> dict:
    """PUT the task back. Send the record you read, not one you built by hand --
    the server fills in fields (ActivityDesc, ContactAddressName) a PUT expects."""
    response = httpx.put(
        f"{base_url}/api/sales/tasks/{task_no}",
        headers={**headers, "Content-Type": "application/json"},
        json=task, verify=verify_ssl, follow_redirects=True, timeout=60.0,
    )
    response.raise_for_status()
    return response.json()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CRM task create/read/update round trip (docs/15 sales/tasks)"
    )
    parser.add_argument("--execute", action="store_true",
                        help="Actually POST/PUT (default: dry run)")
    parser.add_argument("--contact-id", default="17055", help="activity_trans.contact_id")
    parser.add_argument("--customer-id", default="12066",
                        help="Customer id -> LinkId. This is what \"Customer ID is "
                             "required\" actually means.")
    parser.add_argument("--subject", default="ZZ API DOC TEST - safe to delete")
    args = parser.parse_args()

    print("Other REST Families - CRM Task CRUD (sales/tasks)")
    print("=" * 60)

    config = load_config()
    token_data = get_token(config)
    headers = get_auth_headers(token_data["AccessToken"])
    print(f"Server: {config.base_url}")

    template = get_new_template(config.base_url, headers, config.verify_ssl)
    print(f"\nServer template (/new): AssignedById={template['AssignedById']!r} "
          f"LinkTypeCd={template['LinkTypeCd']}")

    task = dict(template)
    task.update({
        "ActivityId": "FOLLOW UP",
        "ContactId": args.contact_id,
        "LinkId": int(args.customer_id),   # the field "Customer ID is required" means
        "Subject": args.subject,
        "Comments": "Created by examples/python/rest/task_crud.py",
        "TargetCompleteDate": "2026-09-30T15:00:00",
    })

    if not args.execute:
        print("\nDRY RUN - payload that would be POSTed to /api/sales/tasks/:")
        print(json.dumps(task, indent=2))
        print("\nRe-run with --execute to actually create, read back, and close it.")
        return

    print("\n1. Create:")
    print("-" * 50)
    created = create_task(config.base_url, headers, config.verify_ssl, task)
    task_no = created["ActivityTransNo"]
    print(f"  Created ActivityTransNo={task_no}")

    print("\n2. Read back:")
    print("-" * 50)
    current = get_task(config.base_url, headers, config.verify_ssl, task_no)
    print(f"  ContactAddressName (server-derived from LinkId): "
          f"{current['ContactAddressName']!r}")

    print("\n3. Update (mark complete):")
    print("-" * 50)
    current["Completed"] = "Y"
    current["Comments"] = "Closed by examples/python/rest/task_crud.py"
    updated = update_task(config.base_url, headers, config.verify_ssl, task_no, current)
    print(f"  Completed={updated['Completed']!r}")

    print("\n" + "=" * 60)
    print(f"Round trip complete. Task {task_no} left Completed=Y "
          f"(there is no delete route on this family).")


if __name__ == "__main__":
    main()
