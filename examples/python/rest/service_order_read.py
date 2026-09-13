"""
Other REST Families - Read a Service Order (service/serviceorders)

Reads an order by number. The finding here is what the family actually
is: its fields are the shape of an ordinary sales order header, and this
route resolves against ANY oe_hdr.order_no -- verified against an
ordinary order used elsewhere in this repo's own examples, with no
"service" flag checked or required.

Mirrors: docs/15-Other-REST-Families.md#serviceserviceorders

PUT on this family was attempted and refused -- "Unable to find Order
Header using Order No" -- against the identical order number this GET
just read. See docs/15 for the exact error and what remains unresolved.

Usage:
    python examples/python/rest/service_order_read.py 999991
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from common.auth import get_token, get_auth_headers
from common.config import load_config

import warnings
warnings.filterwarnings("ignore")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Read a service order (docs/15 service/serviceorders)"
    )
    parser.add_argument("order_no", help="Any oe_hdr.order_no -- this family is not "
                                         "restricted to orders flagged as 'service'")
    args = parser.parse_args()

    print("Other REST Families - Service Order Read (service/serviceorders)")
    print("=" * 60)

    config = load_config()
    token_data = get_token(config)
    headers = get_auth_headers(token_data["AccessToken"])
    print(f"Server: {config.base_url}")

    response = httpx.get(f"{config.base_url}/api/service/serviceorders/{args.order_no}",
                         headers=headers, verify=config.verify_ssl, timeout=40.0)
    response.raise_for_status()
    order = response.json()

    print(f"\nOrder {order['OrderNo']}  customer={order['CustomerId']}  "
          f"location={order['LocationId']}  po_no={order['PoNo']!r}")
    print(f"Ship to: {order['Ship2Name']}")
    print(f"\nLines={order['Lines']!r}  Salesreps={order['Salesreps']!r}  Notes={order['Notes']!r}")
    print("\nThis is an ordinary sales order read through a differently-shaped view -- "
          "the same order also answers on sales/tasks' LinkId lookups and the "
          "Transaction API Order service.")


if __name__ == "__main__":
    main()
