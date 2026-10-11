"""
Thin Interactive API v2 helper used by the write examples.

Wraps the raw endpoints with no abstraction beyond error checking, so each
example still shows the real call sequence:

    POST   {ui}/api/ui/interactive/sessions/        start (ResponseWindowHandlingEnabled)
    POST   {ui}/api/ui/interactive/v2/window        open a window by ServiceName
    PUT    {ui}/api/ui/interactive/v2/change        change one field
    PUT    {ui}/api/ui/interactive/v2/tab           select a tab page
    PUT    {ui}/api/ui/interactive/v2/row           select a row (POST adds one)
    GET    {ui}/api/ui/interactive/v2/data?id=      datawindows on the active surface
    GET    {ui}/api/ui/interactive/v2/tools?windowId=   buttons/tools of a window or popup
    POST   {ui}/api/ui/interactive/v2/tools         click a button/tool
    PUT    {ui}/api/ui/interactive/v2/data          save (body = bare window-ID string)
    DELETE {ui}/api/ui/interactive/v2/window?id=    close
    DELETE {ui}/api/ui/interactive/sessions/        end

See docs/04-Interactive-API.md.
"""

from __future__ import annotations

import httpx

SUCCESS, FAILURE, BLOCKED = 1, 2, 3  # ResultStatus enum (0 = None)


def popup_ids(result: dict) -> list[str]:
    """Window IDs of response windows opened by the last call.

    The id is on the ``windowopened`` event, not in ``ResponseWindowId``
    (that field is empty on 26.1 responses).

    Args:
        result: Parsed JSON body of an Interactive call.

    Returns:
        list[str]: Popup window IDs, in the order they opened.
    """
    ids = []
    for event in result.get("Events") or []:
        if event.get("Name") == "windowopened":
            for kv in event.get("Data") or []:
                if kv.get("Key") == "windowid":
                    ids.append(kv["Value"])
    return ids


def event_value(result: dict, event_name: str, key: str) -> str | None:
    """Return the first ``key`` value carried by an event of ``event_name``.

    Args:
        result: Parsed JSON body of an Interactive call.
        event_name: Event name, e.g. ``keygenerated``.
        key: Data key inside the event, e.g. ``value``.

    Returns:
        str | None: The value, or None when no such event is present.
    """
    for event in result.get("Events") or []:
        if event.get("Name") == event_name:
            for kv in event.get("Data") or []:
                if kv.get("Key") == key:
                    return kv.get("Value")
    return None


class InteractiveSession:
    """One Interactive API session against the UI server."""

    def __init__(self, ui_server: str, headers: dict, verify_ssl: bool) -> None:
        """Store connection details.

        Args:
            ui_server: UI server URL from ``get_ui_server_url()``.
            headers: Auth headers from ``get_auth_headers()``.
            verify_ssl: Whether to verify SSL certificates.
        """
        self.base = f"{ui_server}/api/ui/interactive"
        self.http = httpx.Client(headers=headers, verify=verify_ssl,
                                 follow_redirects=True, timeout=180)

    def _check(self, response: httpx.Response, what: str) -> dict:
        """Raise on HTTP errors (with the body) and on Status 2 (Failure)."""
        if response.status_code >= 400:
            raise RuntimeError(f"{what}: HTTP {response.status_code} {response.text[:400]}")
        result = response.json() if response.text else {}
        if isinstance(result, dict) and result.get("Status") == FAILURE:
            texts = [m.get("Text", m) if isinstance(m, dict) else m
                     for m in result.get("Messages") or []]
            raise RuntimeError(f"{what}: {texts}")
        return result

    def start(self, response_windows: bool = True) -> None:
        """Start the session. ``True`` makes popups come back as windows to answer."""
        self._check(self.http.post(f"{self.base}/sessions/",
                                   json={"ResponseWindowHandlingEnabled": response_windows}),
                    "start session")

    def open_window(self, service_name: str) -> str:
        """Open a window by service name and return its window ID."""
        return self._check(self.http.post(f"{self.base}/v2/window",
                                          json={"ServiceName": service_name}),
                           f"open {service_name}")["WindowId"]

    def change(self, window_id: str, tab: str, datawindow: str, field: str,
               value: str) -> dict:
        """Change one field (``DatawindowName`` is required on 25.2+)."""
        return self._check(self.http.put(f"{self.base}/v2/change", json={
            "WindowId": window_id,
            "List": [{"TabName": tab, "DatawindowName": datawindow,
                      "FieldName": field, "Value": value}],
        }), f"change {field}={value}")

    def select_tab(self, window_id: str, page_name: str) -> dict:
        """Make ``page_name`` the active tab page."""
        return self._check(self.http.put(f"{self.base}/v2/tab",
                                         json={"WindowId": window_id, "PageName": page_name}),
                           f"tab {page_name}")

    def select_row(self, window_id: str, datawindow: str, row: int) -> dict:
        """Make ``row`` (1-based) the active row. Changes land on the ACTIVE row."""
        return self._check(self.http.put(f"{self.base}/v2/row", json={
            "WindowId": window_id, "DatawindowName": datawindow, "Row": row}),
            f"select row {row} of {datawindow}")

    def add_row(self, window_id: str, datawindow: str) -> dict:
        """Append a row to a grid datawindow and make it active."""
        return self._check(self.http.post(f"{self.base}/v2/row", json={
            "WindowId": window_id, "DatawindowName": datawindow}),
            f"add row to {datawindow}")

    def datawindows(self, window_id: str) -> list[dict]:
        """Datawindows on the window's active surface (``GET /v2/data``)."""
        response = self.http.get(f"{self.base}/v2/data", params={"id": window_id})
        if response.status_code >= 400:
            raise RuntimeError(f"get data: HTTP {response.status_code} {response.text[:400]}")
        return response.json()

    def rows(self, window_id: str, datawindow: str) -> list[dict]:
        """All rows of one datawindow as column -> value dicts."""
        for dw in self.datawindows(window_id):
            if dw.get("Name") == datawindow:
                return [dict(zip(dw["Columns"], row)) for row in dw.get("Data") or []]
        return []

    def active_row(self, window_id: str, datawindow: str) -> dict:
        """The active row of one datawindow. ``ActiveRow`` is 1-based."""
        for dw in self.datawindows(window_id):
            if dw.get("Name") == datawindow and dw.get("Data"):
                index = max((dw.get("ActiveRow") or 1) - 1, 0)
                return dict(zip(dw["Columns"], dw["Data"][index]))
        return {}

    def tools(self, window_id: str) -> list[str]:
        """Tool/button names of a window or popup (``?windowId=``, not ``?id=``)."""
        response = self.http.get(f"{self.base}/v2/tools", params={"windowId": window_id})
        if response.status_code >= 400:
            raise RuntimeError(f"get tools: HTTP {response.status_code} {response.text[:400]}")
        return [t.get("ToolName") for t in response.json()]

    def run_tool(self, window_id: str, tool_name: str) -> dict:
        """Click a button or run a tool on a window or popup."""
        return self._check(self.http.post(f"{self.base}/v2/tools", json={
            "WindowId": window_id, "ToolName": tool_name}), f"tool {tool_name}")

    def window_name(self, window_id: str) -> str:
        """Window class name from ``GET /v2/window`` (e.g. ``w_message``)."""
        response = self.http.get(f"{self.base}/v2/window", params={"id": window_id})
        if response.status_code >= 400:
            return ""
        return ((response.json() or {}).get("Definition") or {}).get("Name") or ""

    def save(self, window_id: str) -> dict:
        """Save. The v2 body is the bare window-ID string (an object is a 422)."""
        return self._check(self.http.put(f"{self.base}/v2/data", json=window_id), "save")

    def close_window(self, window_id: str) -> None:
        """Close a window. Errors are ignored so cleanup always continues."""
        self.http.delete(f"{self.base}/v2/window", params={"id": window_id})

    def end(self) -> None:
        """End the session and release the HTTP client."""
        try:
            self.http.delete(f"{self.base}/sessions/")
        finally:
            self.http.close()
