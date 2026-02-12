"""
Verification test for the P21 API client.

Tests:
1. Authentication with consumer key + domain-qualified username
2. Transaction API: list services
3. Interactive API: open/close session + Customer window
4. OData API: query attempt (expected 401 — consumer key lacks OData scope)
5. Entity API: ping
"""

import sys
import os

# Add project root to path so we can import scripts.common
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.common.client import P21Client

import httpx


def main():
    print("=" * 60)
    print("P21 Client Verification Test")
    print("=" * 60)

    # --- 1. Authenticate ---
    print("\n1. Authenticating...")
    try:
        client = P21Client.from_env()
        token = client.authenticate()
        print(f"   OK — Token: {token[:50]}...")
        client._init_namespaces()
        print(f"   UI Server: {client._ui_server}")
    except Exception as e:
        print(f"   FAIL — {e}")
        return

    try:
        # --- 2. Transaction API: list services ---
        print("\n2. Transaction API — list services...")
        try:
            services = client.transaction.list_services()
            print(f"   OK — {len(services)} services found")
            if services:
                # Show first 5 service names
                names = [s if isinstance(s, str) else s.get("Name", s.get("name", str(s)))
                         for s in services[:5]]
                print(f"   First 5: {names}")
        except Exception as e:
            print(f"   FAIL — {e}")

        # --- 3. Interactive API: session + Customer window ---
        print("\n3. Interactive API — session + Customer window...")
        try:
            with client.interactive.session() as session:
                print("   Session created OK")

                window = session.open_window("Customer")
                print(f"   Customer window opened OK — WindowId: {window.window_id}")

                # Try closing the window (may return 400 on some servers)
                close_result = window.close()
                print(f"   Window close — status: {close_result.status_code}")

            print("   Session ended OK")
        except Exception as e:
            print(f"   FAIL — {e}")

        # --- 4. OData API: query (expected 401) ---
        print("\n4. OData API — query supplier (expected 401)...")
        try:
            result = client.odata.query("supplier", top=1)
            print(f"   Unexpected OK — {result}")
        except httpx.HTTPStatusError as e:
            print(f"   Expected error — {e.response.status_code}: {e.response.text[:200]}")
        except Exception as e:
            print(f"   Error — {e}")

        # --- 5. Entity API: ping ---
        print("\n5. Entity API — ping customers...")
        try:
            result = client.entity.ping("customers")
            print(f"   OK — {result}")
        except httpx.HTTPStatusError as e:
            print(f"   HTTP {e.response.status_code}: {e.response.text[:200]}")
        except Exception as e:
            print(f"   Error — {e}")

    finally:
        client.close()

    print("\n" + "=" * 60)
    print("Verification complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
