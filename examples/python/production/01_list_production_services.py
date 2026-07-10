"""
Transaction API - List Production and Labor Services

Discovers all production/labor-related services available through
the Transaction API, and checks which ones have definitions.

Usage:
    python examples/python/production/01_list_production_services.py
"""

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from common.auth import get_token, get_auth_headers, get_ui_server_url
from common.config import load_config

import warnings
warnings.filterwarnings("ignore")

# Keywords that indicate production/labor/manufacturing services
PRODUCTION_KEYWORDS = [
    "production", "labor", "timeentry", "time_entry", "technician",
    "work_order", "workorder", "manufacturing", "bom", "routing",
    "shop", "schedule", "completion", "assembly", "component",
]


def matches_production(name: str) -> bool:
    """Check if a service name matches production/labor keywords."""
    lower_name = name.lower()
    return any(kw in lower_name for kw in PRODUCTION_KEYWORDS)


def check_definition_available(
    ui_server_url: str, service_name: str, headers: dict, verify_ssl: bool
) -> bool:
    """Check if a service has a definition endpoint available."""
    try:
        response = httpx.get(
            f"{ui_server_url}/api/v2/definition/{service_name}",
            headers=headers,
            verify=verify_ssl,
            follow_redirects=True,
            timeout=15.0,
        )
        return response.status_code == 200
    except (httpx.HTTPError, httpx.TimeoutException):
        return False


def main() -> None:
    print("Transaction API - List Production & Labor Services")
    print("=" * 60)

    config = load_config()
    token_data = get_token(config)
    headers = get_auth_headers(token_data["AccessToken"])
    ui_server_url = get_ui_server_url(
        config.base_url, token_data["AccessToken"], config.verify_ssl
    )
    print(f"UI Server: {ui_server_url}")

    # Step 1: Fetch all available services
    print("\nFetching all services...")
    print("-" * 50)

    response = httpx.get(
        f"{ui_server_url}/api/v2/services",
        headers=headers,
        verify=config.verify_ssl,
        follow_redirects=True,
        timeout=30.0,
    )
    response.raise_for_status()
    data = response.json()

    services = data if isinstance(data, list) else data.get("value", data)

    # Step 2: Filter for production/labor-related services
    production_services: list[str] = []
    for service in sorted(services, key=lambda x: x.get("Name", x) if isinstance(x, dict) else x):
        name = service.get("Name") if isinstance(service, dict) else service
        if matches_production(name):
            production_services.append(name)

    print(f"\nFound {len(production_services)} production/labor-related services "
          f"(out of {len(services)} total):\n")

    # Step 3: Check which ones have definitions available
    for name in production_services:
        has_def = check_definition_available(
            ui_server_url, name, headers, config.verify_ssl
        )
        status = "[definition available]" if has_def else "[no definition]"
        print(f"  {name:40s} {status}")

    # Step 4: Also show a broader keyword scan to catch anything missed
    print("\n" + "-" * 50)
    print("Full service list scan (partial matches):")
    print("-" * 50)

    # Broader keywords to catch related services
    broad_keywords = ["prod", "labor", "time", "tech", "shop", "bom",
                      "route", "schedule", "complet", "assem", "manuf"]

    broad_matches: list[str] = []
    for service in sorted(services, key=lambda x: x.get("Name", x) if isinstance(x, dict) else x):
        name = service.get("Name") if isinstance(service, dict) else service
        lower_name = name.lower()
        matched_kw = [kw for kw in broad_keywords if kw in lower_name]
        if matched_kw and name not in production_services:
            broad_matches.append(name)
            print(f"  {name:40s} (matched: {', '.join(matched_kw)})")

    if not broad_matches:
        print("  (no additional matches)")

    # Summary
    print("\n" + "=" * 60)
    print("Key services to explore:")
    print("  - TimeEntry         : Record technician labor hours")
    print("  - ProductionOrder   : Production order management")
    print("  - LaborRecording    : Labor recording entries")
    print("  (names may differ - check output above for actual names)")
    print("\n" + "=" * 60)
    print("Production service discovery complete!")


if __name__ == "__main__":
    main()
