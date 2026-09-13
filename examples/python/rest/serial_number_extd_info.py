"""
Other REST Families - Serial Number Extended Info Upsert
(inventory/serialnumberextdinfo)

Finds a real, currently-tracked serial number and attempts to attach
extended info to it. Refusal is verified even against a genuine serial;
the real precondition for success is unresolved -- see docs/15.

Mirrors: docs/15-Other-REST-Families.md#inventoryserialnumberextdinfo

The trap this script encodes: InvMastItemId looks derived (InvMastUid is
the natural-looking key) but is read by the backend regardless -- omit it
and the error message itself corrupts ("item 1" and a literal "%s"
instead of the real item id and line number). Sending it doesn't fix the
outcome, but it makes every failure this route can produce legible.

Usage:
    python examples/python/rest/serial_number_extd_info.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from common.auth import get_token, get_auth_headers
from common.config import load_config

import warnings
warnings.filterwarnings("ignore")


def main() -> None:
    print("Other REST Families - Serial Extended Info (serialnumberextdinfo)")
    print("=" * 60)

    config = load_config()
    token_data = get_token(config)
    headers = get_auth_headers(token_data["AccessToken"])
    print(f"Server: {config.base_url}")

    serials = httpx.get(
        f"{config.base_url}/odataservice/odata/table/serial_number",
        params={"$select": "inv_mast_uid,serial_number", "$filter": "delete_flag eq 'N'", "$top": "1"},
        headers=headers, verify=config.verify_ssl, timeout=30.0,
    ).json()["value"]
    if not serials:
        raise SystemExit("No serial_number rows on this tenant to test against.")
    uid, serial = serials[0]["inv_mast_uid"], serials[0]["serial_number"]

    item = httpx.get(f"{config.base_url}/odataservice/odata/table/inv_mast",
                     params={"$select": "item_id", "$filter": f"inv_mast_uid eq {uid}"},
                     headers=headers, verify=config.verify_ssl, timeout=30.0).json()["value"][0]
    item_id = item["item_id"]
    print(f"\nUsing a real, existing serial: inv_mast_uid={uid} item_id={item_id!r} "
          f"serial_number={serial!r}")

    body = {"InvMastUid": uid, "InvMastItemId": item_id, "SerialNumber": serial,
           "Comments": "ZZ API DOC TEST"}
    r = httpx.put(f"{config.base_url}/api/inventory/serialnumberextdinfo/",
                  headers=headers, json=body, verify=config.verify_ssl, timeout=60.0)
    print(f"\nHTTP {r.status_code}")
    if r.status_code != 200:
        stack = r.json().get("StackTrace", r.text)
        # Pull just the ErrorMessage line out of the wrapped fault detail.
        for line in stack.splitlines():
            if "ErrorMessage:" in line:
                print(f"  {line.strip()}")
                break
        else:
            print(f"  {stack[:300]}")
    else:
        print(r.text[:400])


if __name__ == "__main__":
    main()
