"""
P21 Reusable API Client

Unified sync and async clients covering all four P21 APIs:
- OData (read-only queries)
- Transaction (stateless bulk operations)
- Interactive (stateful window interactions)
- Entity (CRUD on customer/vendor/contact/address)

Usage (sync):
    with P21Client.from_env() as client:
        services = client.transaction.list_services()
        rows = client.odata.query("supplier", top=5)
        with client.interactive.session() as session:
            window = session.open_window("Customer")
            window.change_data("FORM", "customer_name", "Test", datawindow_name="form")
            window.save_data()
            window.close()

Usage (async):
    async with AsyncP21Client.from_env() as client:
        services = await client.transaction.list_services()
        async with client.interactive.session() as session:
            window = await session.open_window("Customer")
            await window.close()
"""

from __future__ import annotations

import time
import logging
from dataclasses import dataclass, field
from typing import Any

import httpx

try:
    from .config import P21Config, load_config
    from .auth import _parse_token_response, _parse_router_response
except ImportError:
    from config import P21Config, load_config
    from auth import _parse_token_response, _parse_router_response

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Dataclasses for structured responses
# ---------------------------------------------------------------------------

@dataclass
class Result:
    """Interactive API response."""
    status_code: int
    success: bool
    data: dict | list | None = None
    messages: list[str] = field(default_factory=list)
    events: list[dict] = field(default_factory=list)
    window_id: str | None = None
    raw: Any = None

    @classmethod
    def from_response(cls, response: httpx.Response) -> Result:
        status_code = response.status_code
        try:
            data = response.json()
        except (ValueError, KeyError):
            data = response.text

        if isinstance(data, dict):
            messages = data.get("Messages") or data.get("messages") or []
            if isinstance(messages, str):
                messages = [messages]
            events = data.get("Events") or data.get("events") or []
            window_id = data.get("WindowId") or data.get("windowId")
            # Status field: 1 = Success, 2 = Failure, 3 = Blocked (integer)
            status_val = data.get("Status") or data.get("status")
            success = status_code in (200, 201) and status_val not in (2, 3, "Failure", "Blocked")
        else:
            messages = []
            events = []
            window_id = None
            success = status_code in (200, 201)

        return cls(
            status_code=status_code,
            success=success,
            data=data,
            messages=messages,
            events=events,
            window_id=window_id,
            raw=data,
        )


@dataclass
class TransactionResult:
    """Transaction API response."""
    status_code: int
    succeeded: int = 0
    failed: int = 0
    messages: list[str] = field(default_factory=list)
    results: dict | None = None
    raw: Any = None

    @classmethod
    def from_response(cls, response: httpx.Response) -> TransactionResult:
        status_code = response.status_code
        try:
            data = response.json()
        except (ValueError, KeyError):
            return cls(
                status_code=status_code,
                messages=[response.text[:500]],
                raw=response.text,
            )

        summary = data.get("Summary") or {}
        messages = data.get("Messages") or []
        if isinstance(messages, str):
            messages = [messages]

        return cls(
            status_code=status_code,
            succeeded=summary.get("Succeeded", 0),
            failed=summary.get("Failed", 0),
            messages=messages,
            results=data.get("Results"),
            raw=data,
        )


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def get_generated_key(result: Result) -> str | None:
    """Extract auto-generated key from Result events (e.g., new record ID)."""
    for event in result.events:
        name = event.get("Name") or event.get("name") or ""
        if name.lower() == "generatedkey":
            return event.get("Data") or event.get("data")
    return None


def get_opened_window_id(result: Result) -> str | None:
    """Extract window ID from a 'windowopened' event (response windows).

    Event Data is a KV-list: [{"Key": "windowid", "Value": "..."}]
    """
    for event in result.events:
        name = event.get("Name") or event.get("name") or ""
        if name.lower() == "windowopened":
            data = event.get("Data") or event.get("data")
            if isinstance(data, list):
                # KV-list format: [{"Key": "windowid", "Value": "..."}]
                for item in data:
                    key = (item.get("Key") or item.get("key") or "").lower()
                    if key == "windowid":
                        return item.get("Value") or item.get("value")
            elif isinstance(data, dict):
                return data.get("WindowId") or data.get("windowId")
            elif data:
                return str(data)
    return None


# _parse_token_response is imported from auth.py (single source of truth)


# ---------------------------------------------------------------------------
# Sync Window
# ---------------------------------------------------------------------------

class Window:
    """Sync interactive window handle."""

    def __init__(self, window_id: str, client: httpx.Client, ui_server: str):
        self.window_id = window_id
        self._client = client
        self._ui = ui_server

    def _headers(self) -> dict:
        return dict(self._client.headers)

    def change_data(
        self,
        tab_name: str,
        field_name: str,
        value: str,
        datawindow_name: str,
    ) -> Result:
        """Change a field value (v2 List format).

        Args:
            tab_name: Tab page containing the field (e.g., "FORM").
            field_name: Column name from SQL Information.
            value: New value (always a string).
            datawindow_name: Datawindow containing the field (e.g., "form").
                REQUIRED — P21 25.2+ rejects change requests without it.
        """
        change: dict[str, str] = {
            "TabName": tab_name,
            "DatawindowName": datawindow_name,
            "FieldName": field_name,
            "Value": value,
        }
        body = {"WindowId": self.window_id, "List": [change]}
        resp = self._client.put(f"{self._ui}/api/ui/interactive/v2/change", json=body)
        return Result.from_response(resp)

    def change_fields(self, tab_name: str, fields: dict[str, str],
                      datawindow_name: str) -> Result:
        """Change multiple fields at once.

        Args:
            tab_name: Tab page containing the fields (e.g., "FORM").
            fields: Mapping of field name -> new value.
            datawindow_name: Datawindow containing the fields (e.g., "form").
                REQUIRED — P21 25.2+ rejects change requests without it.
        """
        changes = []
        for fname, fval in fields.items():
            change: dict[str, str] = {
                "TabName": tab_name,
                "DatawindowName": datawindow_name,
                "FieldName": fname,
                "Value": fval,
            }
            changes.append(change)
        body = {"WindowId": self.window_id, "List": changes}
        resp = self._client.put(f"{self._ui}/api/ui/interactive/v2/change", json=body)
        return Result.from_response(resp)

    def save_data(self) -> Result:
        """Save data (v2 format: bare GUID string body)."""
        resp = self._client.put(
            f"{self._ui}/api/ui/interactive/v2/data",
            json=self.window_id,
        )
        return Result.from_response(resp)

    def get_data(self) -> Result:
        """Get current window data."""
        resp = self._client.get(
            f"{self._ui}/api/ui/interactive/v2/data",
            params={"id": self.window_id},
        )
        return Result.from_response(resp)

    def clear_data(self) -> Result:
        """Clear current data (new record mode)."""
        resp = self._client.delete(
            f"{self._ui}/api/ui/interactive/v2/data",
            params={"id": self.window_id},
        )
        return Result.from_response(resp)

    def select_tab(self, page_name: str) -> Result:
        """Change active tab (v2 format)."""
        body = {"WindowId": self.window_id, "PageName": page_name}
        resp = self._client.put(f"{self._ui}/api/ui/interactive/v2/tab", json=body)
        return Result.from_response(resp)

    def add_row(self, datawindow_name: str) -> Result:
        """Add a new row to a datawindow."""
        body = {"WindowId": self.window_id, "DatawindowName": datawindow_name}
        resp = self._client.post(f"{self._ui}/api/ui/interactive/v2/row", json=body)
        return Result.from_response(resp)

    def change_row(self, row: int, datawindow_name: str) -> Result:
        """Select a row (v2 format)."""
        body = {"WindowId": self.window_id, "DatawindowName": datawindow_name, "Row": row}
        resp = self._client.put(f"{self._ui}/api/ui/interactive/v2/row", json=body)
        return Result.from_response(resp)

    def get_tools(self) -> Result:
        """Get available tools/buttons."""
        resp = self._client.get(
            f"{self._ui}/api/ui/interactive/v2/tools",
            params={"windowId": self.window_id},
        )
        return Result.from_response(resp)

    def run_tool(self, tool_name: str, tool_text: str = "") -> Result:
        """Run a tool/button."""
        body = {"WindowId": self.window_id, "ToolName": tool_name, "ToolText": tool_text}
        resp = self._client.post(f"{self._ui}/api/ui/interactive/v2/tools", json=body)
        return Result.from_response(resp)

    def close(self) -> Result:
        """Close this window."""
        resp = self._client.delete(
            f"{self._ui}/api/ui/interactive/v2/window",
            params={"id": self.window_id},
        )
        return Result.from_response(resp)


# ---------------------------------------------------------------------------
# Async Window
# ---------------------------------------------------------------------------

class AsyncWindow:
    """Async interactive window handle."""

    def __init__(self, window_id: str, client: httpx.AsyncClient, ui_server: str):
        self.window_id = window_id
        self._client = client
        self._ui = ui_server

    async def change_data(
        self,
        tab_name: str,
        field_name: str,
        value: str,
        datawindow_name: str,
    ) -> Result:
        """Change a field value.

        datawindow_name is REQUIRED — P21 25.2+ rejects change requests
        without it.
        """
        change: dict[str, str] = {
            "TabName": tab_name,
            "DatawindowName": datawindow_name,
            "FieldName": field_name,
            "Value": value,
        }
        body = {"WindowId": self.window_id, "List": [change]}
        resp = await self._client.put(f"{self._ui}/api/ui/interactive/v2/change", json=body)
        return Result.from_response(resp)

    async def change_fields(self, tab_name: str, fields: dict[str, str],
                            datawindow_name: str) -> Result:
        """Change multiple fields.

        datawindow_name is REQUIRED — P21 25.2+ rejects change requests
        without it.
        """
        changes = []
        for fname, fval in fields.items():
            change: dict[str, str] = {
                "TabName": tab_name,
                "DatawindowName": datawindow_name,
                "FieldName": fname,
                "Value": fval,
            }
            changes.append(change)
        body = {"WindowId": self.window_id, "List": changes}
        resp = await self._client.put(f"{self._ui}/api/ui/interactive/v2/change", json=body)
        return Result.from_response(resp)

    async def save_data(self) -> Result:
        resp = await self._client.put(
            f"{self._ui}/api/ui/interactive/v2/data",
            json=self.window_id,
        )
        return Result.from_response(resp)

    async def get_data(self) -> Result:
        resp = await self._client.get(
            f"{self._ui}/api/ui/interactive/v2/data",
            params={"id": self.window_id},
        )
        return Result.from_response(resp)

    async def clear_data(self) -> Result:
        resp = await self._client.delete(
            f"{self._ui}/api/ui/interactive/v2/data",
            params={"id": self.window_id},
        )
        return Result.from_response(resp)

    async def select_tab(self, page_name: str) -> Result:
        body = {"WindowId": self.window_id, "PageName": page_name}
        resp = await self._client.put(f"{self._ui}/api/ui/interactive/v2/tab", json=body)
        return Result.from_response(resp)

    async def add_row(self, datawindow_name: str) -> Result:
        body = {"WindowId": self.window_id, "DatawindowName": datawindow_name}
        resp = await self._client.post(f"{self._ui}/api/ui/interactive/v2/row", json=body)
        return Result.from_response(resp)

    async def change_row(self, row: int, datawindow_name: str) -> Result:
        body = {"WindowId": self.window_id, "DatawindowName": datawindow_name, "Row": row}
        resp = await self._client.put(f"{self._ui}/api/ui/interactive/v2/row", json=body)
        return Result.from_response(resp)

    async def get_tools(self) -> Result:
        resp = await self._client.get(
            f"{self._ui}/api/ui/interactive/v2/tools",
            params={"windowId": self.window_id},
        )
        return Result.from_response(resp)

    async def run_tool(self, tool_name: str, tool_text: str = "") -> Result:
        body = {"WindowId": self.window_id, "ToolName": tool_name, "ToolText": tool_text}
        resp = await self._client.post(f"{self._ui}/api/ui/interactive/v2/tools", json=body)
        return Result.from_response(resp)

    async def close(self) -> Result:
        resp = await self._client.delete(
            f"{self._ui}/api/ui/interactive/v2/window",
            params={"id": self.window_id},
        )
        return Result.from_response(resp)


# ---------------------------------------------------------------------------
# Sync Interactive Session
# ---------------------------------------------------------------------------

class InteractiveSession:
    """Sync interactive session (context manager)."""

    def __init__(self, client: httpx.Client, ui_server: str,
                 response_windows: bool = False):
        self._client = client
        self._ui = ui_server
        self._started = False
        self._response_windows = response_windows

    def start(self, response_windows: bool | None = None) -> dict:
        if response_windows is None:
            response_windows = self._response_windows
        resp = self._client.post(
            f"{self._ui}/api/ui/interactive/sessions",
            json={"ResponseWindowHandlingEnabled": response_windows},
        )
        resp.raise_for_status()
        self._started = True
        try:
            return resp.json()
        except (ValueError, KeyError):
            return {"status": resp.status_code}

    def end(self) -> None:
        if self._started:
            try:
                self._client.delete(f"{self._ui}/api/ui/interactive/sessions")
            except Exception as e:
                logger.debug(f"Session cleanup error (ignored): {e}")
            self._started = False

    def open_window(self, service_name: str | None = None,
                    title: str | None = None) -> Window:
        body: dict[str, Any] = {}
        if service_name:
            body["ServiceName"] = service_name
        if title:
            body["Title"] = title
        resp = self._client.post(f"{self._ui}/api/ui/interactive/v2/window", json=body)
        resp.raise_for_status()
        data = resp.json()
        window_id = data.get("WindowId") or data.get("windowId")
        if not window_id:
            raise ValueError(f"No WindowId in response: {data}")
        return Window(window_id, self._client, self._ui)

    def list_sessions(self) -> list:
        resp = self._client.get(f"{self._ui}/api/ui/interactive/sessions")
        resp.raise_for_status()
        return resp.json()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end()
        return False


# ---------------------------------------------------------------------------
# Async Interactive Session
# ---------------------------------------------------------------------------

class AsyncInteractiveSession:
    """Async interactive session (async context manager)."""

    def __init__(self, client: httpx.AsyncClient, ui_server: str,
                 response_windows: bool = False):
        self._client = client
        self._ui = ui_server
        self._started = False
        self._response_windows = response_windows

    async def start(self, response_windows: bool | None = None) -> dict:
        if response_windows is None:
            response_windows = self._response_windows
        resp = await self._client.post(
            f"{self._ui}/api/ui/interactive/sessions",
            json={"ResponseWindowHandlingEnabled": response_windows},
        )
        resp.raise_for_status()
        self._started = True
        try:
            return resp.json()
        except (ValueError, KeyError):
            return {"status": resp.status_code}

    async def end(self) -> None:
        if self._started:
            try:
                await self._client.delete(f"{self._ui}/api/ui/interactive/sessions")
            except Exception as e:
                logger.debug(f"Session cleanup error (ignored): {e}")
            self._started = False

    async def open_window(self, service_name: str | None = None,
                          title: str | None = None) -> AsyncWindow:
        body: dict[str, Any] = {}
        if service_name:
            body["ServiceName"] = service_name
        if title:
            body["Title"] = title
        resp = await self._client.post(
            f"{self._ui}/api/ui/interactive/v2/window", json=body
        )
        resp.raise_for_status()
        data = resp.json()
        window_id = data.get("WindowId") or data.get("windowId")
        if not window_id:
            raise ValueError(f"No WindowId in response: {data}")
        return AsyncWindow(window_id, self._client, self._ui)

    async def list_sessions(self) -> list:
        resp = await self._client.get(f"{self._ui}/api/ui/interactive/sessions")
        resp.raise_for_status()
        return resp.json()

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.end()
        return False


# ---------------------------------------------------------------------------
# Sync API namespaces
# ---------------------------------------------------------------------------

class ODataAPI:
    """OData API namespace (read-only queries)."""

    def __init__(self, client: httpx.Client, odata_url: str):
        self._client = client
        self._url = odata_url

    def query(
        self,
        table: str,
        *,
        select: str | None = None,
        filter: str | None = None,
        top: int | None = None,
        skip: int | None = None,
        orderby: str | None = None,
        count: bool = False,
    ) -> dict:
        """Query a table. Returns the full OData response dict."""
        params: dict[str, Any] = {}
        if select:
            params["$select"] = select
        if filter:
            params["$filter"] = filter
        if top is not None:
            params["$top"] = top
        if skip is not None:
            params["$skip"] = skip
        if orderby:
            params["$orderby"] = orderby
        if count:
            params["$count"] = "true"
        resp = self._client.get(f"{self._url}/table/{table}", params=params)
        resp.raise_for_status()
        return resp.json()

    def query_view(
        self,
        view: str,
        *,
        select: str | None = None,
        filter: str | None = None,
        top: int | None = None,
        skip: int | None = None,
        orderby: str | None = None,
        count: bool = False,
    ) -> dict:
        """Query a view. Returns the full OData response dict."""
        params: dict[str, Any] = {}
        if select:
            params["$select"] = select
        if filter:
            params["$filter"] = filter
        if top is not None:
            params["$top"] = top
        if skip is not None:
            params["$skip"] = skip
        if orderby:
            params["$orderby"] = orderby
        if count:
            params["$count"] = "true"
        resp = self._client.get(f"{self._url}/view/{view}", params=params)
        resp.raise_for_status()
        return resp.json()


class TransactionAPI:
    """Transaction API namespace (stateless bulk operations)."""

    def __init__(self, client: httpx.Client, ui_server: str):
        self._client = client
        self._ui = ui_server

    def list_services(self) -> list:
        resp = self._client.get(f"{self._ui}/api/v2/services")
        resp.raise_for_status()
        return resp.json()

    def get_definition(self, service_name: str) -> dict:
        resp = self._client.get(f"{self._ui}/api/v2/definition/{service_name}")
        resp.raise_for_status()
        return resp.json()

    def get_defaults(self, service_name: str) -> dict:
        resp = self._client.get(f"{self._ui}/api/v2/defaults/{service_name}")
        resp.raise_for_status()
        return resp.json()

    def create(self, payload: dict) -> TransactionResult:
        """Submit a synchronous transaction."""
        resp = self._client.post(f"{self._ui}/api/v2/transaction", json=payload)
        return TransactionResult.from_response(resp)

    def create_async(self, payload: dict) -> dict:
        """Submit an async transaction. Returns {RequestId, Status}."""
        resp = self._client.post(f"{self._ui}/api/v2/transaction/async", json=payload)
        resp.raise_for_status()
        return resp.json()

    def get_async_status(self, request_id: str) -> dict:
        resp = self._client.get(
            f"{self._ui}/api/v2/transaction/async",
            params={"id": request_id},
        )
        resp.raise_for_status()
        return resp.json()

    def get_records(self, payload: dict) -> dict:
        """Retrieve existing records via Transaction GET."""
        resp = self._client.post(f"{self._ui}/api/v2/transaction/get", json=payload)
        resp.raise_for_status()
        return resp.json()


class InteractiveAPI:
    """Interactive API namespace — yields InteractiveSession via context manager."""

    def __init__(self, client: httpx.Client, ui_server: str):
        self._client = client
        self._ui = ui_server

    def session(self, response_windows: bool = False) -> InteractiveSession:
        """Return an InteractiveSession (use as context manager)."""
        return InteractiveSession(self._client, self._ui, response_windows=response_windows)


class EntityAPI:
    """Entity API namespace (CRUD on customer/vendor/contact/address)."""

    def __init__(self, client: httpx.Client, entity_url: str):
        self._client = client
        self._url = entity_url

    def ping(self, resource: str = "customers") -> dict:
        resp = self._client.get(f"{self._url}/{resource}/ping")
        resp.raise_for_status()
        return resp.json()

    def get(self, resource: str, key: str, extended_properties: str | None = None) -> dict:
        params = {}
        if extended_properties:
            params["extendedproperties"] = extended_properties
        resp = self._client.get(f"{self._url}/{resource}/{key}", params=params)
        resp.raise_for_status()
        return resp.json()

    def list(self, resource: str, query: str | None = None) -> list | dict:
        params = {}
        if query:
            params["$query"] = query
        resp = self._client.get(f"{self._url}/{resource}/", params=params)
        resp.raise_for_status()
        return resp.json()

    # Resources that do not support /new or PUT (by design)
    _NO_TEMPLATE = {"addresses"}
    _NO_UPDATE = {"addresses"}

    def get_template(self, resource: str) -> dict:
        if resource in self._NO_TEMPLATE:
            raise ValueError(
                f"Entity '{resource}' does not have a /new template endpoint. "
                "Use customers, vendors, or contacts instead."
            )
        resp = self._client.get(f"{self._url}/{resource}/new")
        resp.raise_for_status()
        return resp.json()

    def create(self, resource: str, data: dict) -> dict:
        resp = self._client.post(f"{self._url}/{resource}", json=data)
        resp.raise_for_status()
        return resp.json()

    def update(self, resource: str, key: str, data: dict) -> dict:
        if resource in self._NO_UPDATE:
            raise ValueError(
                f"Entity '{resource}' does not support PUT/update. "
                "Use the Interactive API (Address Maintenance) or direct SQL."
            )
        resp = self._client.put(f"{self._url}/{resource}/{key}", json=data)
        resp.raise_for_status()
        return resp.json()


# ---------------------------------------------------------------------------
# Async API namespaces
# ---------------------------------------------------------------------------

class AsyncODataAPI:
    def __init__(self, client: httpx.AsyncClient, odata_url: str):
        self._client = client
        self._url = odata_url

    async def query(
        self,
        table: str,
        *,
        select: str | None = None,
        filter: str | None = None,
        top: int | None = None,
        skip: int | None = None,
        orderby: str | None = None,
        count: bool = False,
    ) -> dict:
        params: dict[str, Any] = {}
        if select:
            params["$select"] = select
        if filter:
            params["$filter"] = filter
        if top is not None:
            params["$top"] = top
        if skip is not None:
            params["$skip"] = skip
        if orderby:
            params["$orderby"] = orderby
        if count:
            params["$count"] = "true"
        resp = await self._client.get(f"{self._url}/table/{table}", params=params)
        resp.raise_for_status()
        return resp.json()

    async def query_view(
        self,
        view: str,
        *,
        select: str | None = None,
        filter: str | None = None,
        top: int | None = None,
        skip: int | None = None,
        orderby: str | None = None,
        count: bool = False,
    ) -> dict:
        params: dict[str, Any] = {}
        if select:
            params["$select"] = select
        if filter:
            params["$filter"] = filter
        if top is not None:
            params["$top"] = top
        if skip is not None:
            params["$skip"] = skip
        if orderby:
            params["$orderby"] = orderby
        if count:
            params["$count"] = "true"
        resp = await self._client.get(f"{self._url}/view/{view}", params=params)
        resp.raise_for_status()
        return resp.json()


class AsyncTransactionAPI:
    def __init__(self, client: httpx.AsyncClient, ui_server: str):
        self._client = client
        self._ui = ui_server

    async def list_services(self) -> list:
        resp = await self._client.get(f"{self._ui}/api/v2/services")
        resp.raise_for_status()
        return resp.json()

    async def get_definition(self, service_name: str) -> dict:
        resp = await self._client.get(f"{self._ui}/api/v2/definition/{service_name}")
        resp.raise_for_status()
        return resp.json()

    async def get_defaults(self, service_name: str) -> dict:
        resp = await self._client.get(f"{self._ui}/api/v2/defaults/{service_name}")
        resp.raise_for_status()
        return resp.json()

    async def create(self, payload: dict) -> TransactionResult:
        resp = await self._client.post(f"{self._ui}/api/v2/transaction", json=payload)
        return TransactionResult.from_response(resp)

    async def create_async(self, payload: dict) -> dict:
        resp = await self._client.post(f"{self._ui}/api/v2/transaction/async", json=payload)
        resp.raise_for_status()
        return resp.json()

    async def get_async_status(self, request_id: str) -> dict:
        resp = await self._client.get(
            f"{self._ui}/api/v2/transaction/async",
            params={"id": request_id},
        )
        resp.raise_for_status()
        return resp.json()

    async def get_records(self, payload: dict) -> dict:
        resp = await self._client.post(f"{self._ui}/api/v2/transaction/get", json=payload)
        resp.raise_for_status()
        return resp.json()


class AsyncInteractiveAPI:
    def __init__(self, client: httpx.AsyncClient, ui_server: str):
        self._client = client
        self._ui = ui_server

    def session(self, response_windows: bool = False) -> AsyncInteractiveSession:
        return AsyncInteractiveSession(self._client, self._ui, response_windows=response_windows)


class AsyncEntityAPI:
    def __init__(self, client: httpx.AsyncClient, entity_url: str):
        self._client = client
        self._url = entity_url

    async def ping(self, resource: str = "customers") -> dict:
        resp = await self._client.get(f"{self._url}/{resource}/ping")
        resp.raise_for_status()
        return resp.json()

    async def get(self, resource: str, key: str,
                  extended_properties: str | None = None) -> dict:
        params = {}
        if extended_properties:
            params["extendedproperties"] = extended_properties
        resp = await self._client.get(f"{self._url}/{resource}/{key}", params=params)
        resp.raise_for_status()
        return resp.json()

    async def list(self, resource: str, query: str | None = None) -> list | dict:
        params = {}
        if query:
            params["$query"] = query
        resp = await self._client.get(f"{self._url}/{resource}/", params=params)
        resp.raise_for_status()
        return resp.json()

    _NO_TEMPLATE = EntityAPI._NO_TEMPLATE
    _NO_UPDATE = EntityAPI._NO_UPDATE

    async def get_template(self, resource: str) -> dict:
        if resource in self._NO_TEMPLATE:
            raise ValueError(
                f"Entity '{resource}' does not have a /new template endpoint. "
                "Use customers, vendors, or contacts instead."
            )
        resp = await self._client.get(f"{self._url}/{resource}/new")
        resp.raise_for_status()
        return resp.json()

    async def create(self, resource: str, data: dict) -> dict:
        resp = await self._client.post(f"{self._url}/{resource}", json=data)
        resp.raise_for_status()
        return resp.json()

    async def update(self, resource: str, key: str, data: dict) -> dict:
        if resource in self._NO_UPDATE:
            raise ValueError(
                f"Entity '{resource}' does not support PUT/update. "
                "Use the Interactive API (Address Maintenance) or direct SQL."
            )
        resp = await self._client.put(f"{self._url}/{resource}/{key}", json=data)
        resp.raise_for_status()
        return resp.json()


# ---------------------------------------------------------------------------
# Sync P21Client
# ---------------------------------------------------------------------------

class P21Client:
    """Sync P21 API client with namespace-based access to all four APIs.

    Usage:
        with P21Client.from_env() as client:
            services = client.transaction.list_services()
            data = client.odata.query("supplier", top=5)
    """

    def __init__(self, config: P21Config):
        self.config = config
        self._client: httpx.Client | None = None
        self._token: str | None = None
        self._token_expires: float = 0
        self._ui_server: str | None = None

        # API namespaces (initialized after authenticate)
        self.odata: ODataAPI | None = None
        self.transaction: TransactionAPI | None = None
        self.interactive: InteractiveAPI | None = None
        self.entity: EntityAPI | None = None

    @classmethod
    def from_env(cls) -> P21Client:
        return cls(load_config())

    def _get_client(self) -> httpx.Client:
        if self._client is None or self._client.is_closed:
            self._client = httpx.Client(
                verify=self.config.verify_ssl,
                timeout=60.0,
                follow_redirects=True,
            )
        return self._client

    def authenticate(self) -> str:
        """Authenticate and return the access token."""
        client = self._get_client()
        cfg = self.config

        if cfg.consumer_key:
            # Consumer key auth via V2 endpoint
            body: dict[str, str] = {
                "ClientSecret": cfg.consumer_key,
                "GrantType": "client_credentials",
            }
            if cfg.username:
                body["username"] = cfg.username
            resp = client.post(cfg.token_url_v2, json=body)
        elif cfg.password:
            # Username/password auth via V2 endpoint (credentials in the
            # body -- NEVER the V1 header form, which proxies/logs capture)
            resp = client.post(
                cfg.token_url_v2,
                json={"username": cfg.username, "password": cfg.password},
                headers={"Accept": "application/json"},
            )
        else:
            raise ValueError("No consumer_key or password configured")

        resp.raise_for_status()
        token_data = _parse_token_response(resp)
        self._token = token_data["AccessToken"]

        # Parse expiry — ExpiresIn (XML) or ExpiresInSeconds (JSON)
        expires_str = token_data.get("ExpiresIn") or token_data.get("ExpiresInSeconds") or "3600"
        try:
            expires_in = int(expires_str)
        except ValueError:
            expires_in = 3600
        # Refresh 5 minutes early
        self._token_expires = time.time() + expires_in - 300

        # Set auth header on client
        self._get_client().headers["Authorization"] = f"Bearer {self._token}"
        self._get_client().headers["Accept"] = "application/json"
        self._get_client().headers["Content-Type"] = "application/json"

        return self._token

    def _ensure_token(self) -> None:
        """Re-authenticate if token is expired or missing."""
        if not self._token or time.time() >= self._token_expires:
            self.authenticate()

    def _resolve_ui_server(self) -> str:
        """Get UI server URL (cached)."""
        if self._ui_server:
            return self._ui_server
        self._ensure_token()
        client = self._get_client()
        resp = client.get(f"{self.config.base_url}/api/ui/router/v1/?urlType=external")  # trailing slash avoids a 307
        resp.raise_for_status()
        # Router may respond with JSON or XML — handle both
        self._ui_server = _parse_router_response(resp).rstrip("/")
        return self._ui_server

    def _init_namespaces(self) -> None:
        """Initialize API namespace objects."""
        client = self._get_client()
        ui = self._resolve_ui_server()
        self.odata = ODataAPI(client, self.config.odata_url)
        self.transaction = TransactionAPI(client, ui)
        self.interactive = InteractiveAPI(client, ui)
        self.entity = EntityAPI(client, self.config.entity_url)

    def connect(self) -> P21Client:
        """Authenticate and initialize all API namespaces."""
        self.authenticate()
        self._init_namespaces()
        return self

    def close(self) -> None:
        if self._client and not self._client.is_closed:
            self._client.close()
            self._client = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False


# ---------------------------------------------------------------------------
# Async P21Client
# ---------------------------------------------------------------------------

class AsyncP21Client:
    """Async P21 API client with namespace-based access to all four APIs.

    Usage:
        async with AsyncP21Client.from_env() as client:
            services = await client.transaction.list_services()
    """

    def __init__(self, config: P21Config):
        self.config = config
        self._client: httpx.AsyncClient | None = None
        self._token: str | None = None
        self._token_expires: float = 0
        self._ui_server: str | None = None

        self.odata: AsyncODataAPI | None = None
        self.transaction: AsyncTransactionAPI | None = None
        self.interactive: AsyncInteractiveAPI | None = None
        self.entity: AsyncEntityAPI | None = None

    @classmethod
    def from_env(cls) -> AsyncP21Client:
        return cls(load_config())

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                verify=self.config.verify_ssl,
                timeout=60.0,
                follow_redirects=True,
            )
        return self._client

    async def authenticate(self) -> str:
        client = self._get_client()
        cfg = self.config

        if cfg.consumer_key:
            body: dict[str, str] = {
                "ClientSecret": cfg.consumer_key,
                "GrantType": "client_credentials",
            }
            if cfg.username:
                body["username"] = cfg.username
            resp = await client.post(cfg.token_url_v2, json=body)
        elif cfg.password:
            # V2 endpoint -- credentials in the body, never in headers
            resp = await client.post(
                cfg.token_url_v2,
                json={"username": cfg.username, "password": cfg.password},
                headers={"Accept": "application/json"},
            )
        else:
            raise ValueError("No consumer_key or password configured")

        resp.raise_for_status()
        token_data = _parse_token_response(resp)
        self._token = token_data["AccessToken"]

        expires_str = token_data.get("ExpiresIn") or token_data.get("ExpiresInSeconds") or "3600"
        try:
            expires_in = int(expires_str)
        except ValueError:
            expires_in = 3600
        self._token_expires = time.time() + expires_in - 300

        self._get_client().headers["Authorization"] = f"Bearer {self._token}"
        self._get_client().headers["Accept"] = "application/json"
        self._get_client().headers["Content-Type"] = "application/json"

        return self._token

    async def _ensure_token(self) -> None:
        if not self._token or time.time() >= self._token_expires:
            await self.authenticate()

    async def _resolve_ui_server(self) -> str:
        if self._ui_server:
            return self._ui_server
        await self._ensure_token()
        client = self._get_client()
        resp = await client.get(f"{self.config.base_url}/api/ui/router/v1/?urlType=external")  # trailing slash avoids a 307
        resp.raise_for_status()
        # Router may respond with JSON or XML — handle both
        self._ui_server = _parse_router_response(resp).rstrip("/")
        return self._ui_server

    async def _init_namespaces(self) -> None:
        client = self._get_client()
        ui = await self._resolve_ui_server()
        self.odata = AsyncODataAPI(client, self.config.odata_url)
        self.transaction = AsyncTransactionAPI(client, ui)
        self.interactive = AsyncInteractiveAPI(client, ui)
        self.entity = AsyncEntityAPI(client, self.config.entity_url)

    async def connect(self) -> AsyncP21Client:
        await self.authenticate()
        await self._init_namespaces()
        return self

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
        return False
