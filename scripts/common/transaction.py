"""
Shared Transaction API helpers.

Provides reusable functions for interacting with the P21 Transaction API,
including fetching service definitions and default values.
"""

import httpx


def get_service_definition(
    ui_server_url: str, service_name: str, headers: dict, verify_ssl: bool
) -> dict:
    """Fetch the definition (schema/template) for a Transaction API service.

    Args:
        ui_server_url: The UI Server base URL.
        service_name: Name of the service (e.g., "TimeEntry", "ProductionOrder").
        headers: HTTP headers including Authorization.
        verify_ssl: Whether to verify SSL certificates.

    Returns:
        dict containing Template and TransactionDefinition sections.
    """
    response = httpx.get(
        f"{ui_server_url}/api/v2/definition/{service_name}",
        headers=headers,
        verify=verify_ssl,
        follow_redirects=True,
        timeout=60.0,
    )
    response.raise_for_status()
    return response.json()


def get_service_defaults(
    ui_server_url: str, service_name: str, headers: dict, verify_ssl: bool
) -> dict:
    """Fetch the default values for a Transaction API service.

    Args:
        ui_server_url: The UI Server base URL.
        service_name: Name of the service (e.g., "TimeEntry", "ProductionOrder").
        headers: HTTP headers including Authorization.
        verify_ssl: Whether to verify SSL certificates.

    Returns:
        dict containing DataElements with default field values.
    """
    response = httpx.get(
        f"{ui_server_url}/api/v2/defaults/{service_name}",
        headers=headers,
        verify=verify_ssl,
        follow_redirects=True,
        timeout=60.0,
    )
    response.raise_for_status()
    return response.json()
