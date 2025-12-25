"""
Interactive API - Session Management

Demonstrates opening and closing Interactive API sessions.

Sessions maintain state just like a real P21 user session.
Always end sessions when done to free server resources.

Usage:
    python scripts/interactive/01_open_session.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from common.auth import get_token, get_auth_headers, get_ui_server_url
from common.config import load_config

import warnings
warnings.filterwarnings("ignore")


def start_session(ui_server_url: str, headers: dict, verify_ssl: bool) -> dict:
    """Start a new Interactive API session."""
    response = httpx.post(
        f"{ui_server_url}/api/ui/interactive/sessions/",
        headers=headers,
        json={"ResponseWindowHandlingEnabled": False},
        verify=verify_ssl,
        follow_redirects=True,
        timeout=30.0
    )
    response.raise_for_status()
    return response.json()


def list_sessions(ui_server_url: str, headers: dict, verify_ssl: bool) -> list:
    """List all open sessions."""
    response = httpx.get(
        f"{ui_server_url}/api/ui/interactive/sessions/",
        headers=headers,
        verify=verify_ssl,
        follow_redirects=True,
        timeout=30.0
    )
    response.raise_for_status()
    return response.json()


def end_session(ui_server_url: str, headers: dict, verify_ssl: bool) -> None:
    """End the current session."""
    response = httpx.delete(
        f"{ui_server_url}/api/ui/interactive/sessions/",
        headers=headers,
        verify=verify_ssl,
        follow_redirects=True,
        timeout=30.0
    )
    response.raise_for_status()


def main():
    print("Interactive API - Session Management")
    print("=" * 60)

    config = load_config()
    token_data = get_token(config)
    headers = get_auth_headers(token_data["AccessToken"])
    ui_server_url = get_ui_server_url(config.base_url, token_data["AccessToken"], config.verify_ssl)

    print(f"UI Server: {ui_server_url}")

    # Example 1: Start a session
    print("\n1. Starting a new session:")
    print("-" * 50)

    try:
        result = start_session(ui_server_url, headers, config.verify_ssl)
        print(f"  Session started successfully")
        print(f"  Response: {result}")

    except httpx.HTTPStatusError as e:
        print(f"  Error: {e.response.status_code}")
        print(f"  {e.response.text[:200]}")
        return

    # Example 2: List sessions
    print("\n2. Listing open sessions:")
    print("-" * 50)

    try:
        sessions = list_sessions(ui_server_url, headers, config.verify_ssl)
        print(f"  Found {len(sessions)} open session(s)")
        for sess in sessions:
            print(f"    - {sess}")

    except httpx.HTTPStatusError as e:
        print(f"  Error: {e.response.status_code}")

    # Example 3: End session
    print("\n3. Ending session:")
    print("-" * 50)

    try:
        end_session(ui_server_url, headers, config.verify_ssl)
        print(f"  Session ended successfully")

    except httpx.HTTPStatusError as e:
        print(f"  Error: {e.response.status_code}")
        print(f"  {e.response.text[:200]}")

    # Verify session ended
    print("\n4. Verifying session ended:")
    print("-" * 50)

    try:
        sessions = list_sessions(ui_server_url, headers, config.verify_ssl)
        print(f"  Open sessions: {len(sessions)}")

    except httpx.HTTPStatusError as e:
        print(f"  Error: {e.response.status_code}")

    print("\n" + "=" * 60)
    print("Session management complete!")
    print("\nBest practices:")
    print("- Always end sessions when done")
    print("- Use context managers (try/finally) to ensure cleanup")
    print("- Sessions timeout after inactivity, but don't rely on this")


if __name__ == "__main__":
    main()
