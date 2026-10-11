"""
Small Transaction API helpers shared by the write-path recipe scripts.

Every script that uses these follows the same shape: build a payload, print
it (dry run), and only with --execute connect, POST, and read the result back
through OData. These helpers keep that plumbing out of the scripts so each
one shows only its payload and its read-back.
"""

from dataclasses import dataclass

import httpx

try:
    from .auth import get_auth_headers, get_token, get_ui_server_url
    from .config import load_config
except ImportError:
    from auth import get_auth_headers, get_token, get_ui_server_url
    from config import load_config


@dataclass
class Session:
    """Connection details for one script run."""

    base_url: str
    ui_server: str
    headers: dict
    verify_ssl: bool


def connect() -> Session:
    """Authenticate from .env and resolve the UI server.

    Returns:
        Session: Base URL, UI server URL, auth headers, and the SSL setting.
    """
    config = load_config()
    token = get_token(config)["AccessToken"]
    ui_server = get_ui_server_url(config.base_url, token, config.verify_ssl)
    return Session(config.base_url, ui_server, get_auth_headers(token), config.verify_ssl)


def edit(name: str, value: str) -> dict:
    """Build one Transaction API edit.

    Args:
        name: Field name from the service definition.
        value: Field value. Always a string, even for numbers and flags.

    Returns:
        dict: {"Name": name, "Value": value}.
    """
    return {"Name": name, "Value": value}


def post_transaction(session: Session, payload: dict, timeout: float = 300) -> dict:
    """POST a payload to /api/v2/transaction and print the Summary.

    HTTP 200 does not mean the write landed: the Summary and Messages do.
    The caller still reads the record back.

    Args:
        session: Session from connect().
        payload: Complete Transaction API payload.
        timeout: Client timeout in seconds. Keep it long: a request the client
            abandons keeps running on the server and holds its record lock.

    Returns:
        dict: The parsed response body.
    """
    resp = httpx.post(f"{session.ui_server}/api/v2/transaction",
                      headers=session.headers, json=payload,
                      verify=session.verify_ssl, follow_redirects=True,
                      timeout=timeout)
    resp.raise_for_status()
    result = resp.json()
    summary = result.get("Summary") or {}
    print(f"Summary: Succeeded={summary.get('Succeeded')}, Failed={summary.get('Failed')}")
    for message in result.get("Messages") or []:
        print(f"  Message: {message}")
    return result


def succeeded(result: dict) -> bool:
    """True when the Summary reports at least one success and no failure.

    Args:
        result: Parsed response from post_transaction().

    Returns:
        bool: Whether the Summary says the transaction landed.
    """
    summary = result.get("Summary") or {}
    return bool(summary.get("Succeeded")) and not summary.get("Failed")


def result_value(result: dict, element: str, field: str) -> str | None:
    """Read a field from a passed transaction's echoed result rows.

    Args:
        result: Parsed response from post_transaction().
        element: DataElement name, for example "TABPAGE_1.tp_1_dw_1".
        field: Field name, for example "id".

    Returns:
        str | None: The value from the first matching row, if any.
    """
    for txn in (result.get("Results") or {}).get("Transactions") or []:
        if txn.get("Status") != "Passed":
            continue
        for data_element in txn.get("DataElements") or []:
            if data_element.get("Name") != element:
                continue
            for row in data_element.get("Rows") or []:
                for item in row.get("Edits") or []:
                    if item.get("Name") == field and item.get("Value"):
                        return item["Value"]
    return None


def odata(session: Session, name: str, filter_expr: str, select: str | None = None,
          surface: str = "table") -> list[dict]:
    """Query an OData table (or view) and return its rows.

    Args:
        session: Session from connect().
        name: Table or view name.
        filter_expr: OData $filter expression.
        select: Optional comma-separated $select list.
        surface: "table" or "view" -- the two surfaces do not overlap.

    Returns:
        list[dict]: Matching rows.
    """
    params = {"$filter": filter_expr}
    if select:
        params["$select"] = select
    resp = httpx.get(f"{session.base_url}/odataservice/odata/{surface}/{name}",
                     params=params, headers=session.headers,
                     verify=session.verify_ssl, follow_redirects=True, timeout=120)
    resp.raise_for_status()
    return resp.json()["value"]


def odata_quote(value: str) -> str:
    """Quote a string literal for an OData $filter (doubles single quotes).

    Args:
        value: Raw string value.

    Returns:
        str: The value wrapped in single quotes.
    """
    return "'" + value.replace("'", "''") + "'"
