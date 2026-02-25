# Batch Processing Patterns

> **Disclaimer:** This is unofficial, community-created documentation for Epicor Prophet 21 APIs. It is not affiliated with, endorsed by, or supported by Epicor Software Corporation. All product names, trademarks, and registered trademarks are property of their respective owners. Use at your own risk.

---

## Overview

The existing Interactive API documentation covers single-operation workflows. Real production use often requires processing dozens or hundreds of operations in sequence, which introduces session timeout, error recovery, and batching concerns.

This document covers patterns learned from operating a production system that created **700+ price pages** across 25+ suppliers using the Interactive API (v2).

---

## Session-Per-Batch Pattern

Interactive API sessions have a default idle timeout of approximately **6 minutes**. When processing many operations, a single session will time out between operations if any individual operation takes longer than expected or if there are delays between operations.

### Pattern

Start a new session for each batch of ~25 operations. This keeps each session well within the timeout window while minimizing session creation overhead.

```python
async def process_in_batches(
    client: P21Client,
    items: list[dict],
    batch_size: int = 25
) -> list[dict]:
    """Process items in batches with a fresh session per batch.

    Args:
        client: Authenticated P21Client (no active session needed)
        items: List of items to process
        batch_size: Number of operations per session (default 25)

    Returns:
        List of results for each item
    """
    results = []

    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(items) + batch_size - 1) // batch_size

        logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} items)")

        # New session for each batch
        async with client.session() as session:
            batch_results = await process_batch(session, batch)
            results.extend(batch_results)

    return results
```

### Verified Timing Data

From production measurements creating price pages with book linking:

| Metric | Value |
|--------|-------|
| Time per page creation (including book linking) | ~2.5s |
| Time for 25-page batch | ~62s |
| Session overhead (start + end) | ~1s |
| Total for 700 pages (28 batches) | ~30 min |

---

## Window Reuse Within a Batch

Opening a P21 window is expensive (~500ms). Within a batch, open the window once and reuse it for multiple operations by calling `clear_data()` between records.

### Pattern

```python
async def process_batch(
    session: P21Session,
    items: list[dict]
) -> list[dict]:
    """Process a batch of items using a single window.

    Opens the window once, processes all items, then closes.
    Uses clear_data() between records to reset the form.
    """
    results = []

    # Open window once for the entire batch
    window = await session.open_window(service_name="SalesPricePage")

    try:
        for i, item in enumerate(items):
            try:
                result = await create_price_page(window, item)
                results.append({"item": item, "success": True, "result": result})

                # Clear the form for the next record (skip on last item)
                if i < len(items) - 1:
                    await window.clear_data()

            except Exception as e:
                logger.error(f"Failed to process item {item}: {e}")
                results.append({"item": item, "success": False, "error": str(e)})

                # On error, close and reopen the window (see Error Recovery below)
                await window.close()
                window = await session.open_window(service_name="SalesPricePage")

    finally:
        await window.close()

    return results
```

### Key Points

- Call `clear_data()` after saving each record to reset the form
- Do NOT call `clear_data()` after the last record (the window close handles cleanup)
- If an error occurs, close and reopen the window rather than trying to recover in-place

---

## Error Recovery Pattern

When an error occurs during an Interactive API operation, the window state may be corrupted (partial field values, unsaved changes, open dialogs). Attempting to continue using a corrupted window leads to cascading failures.

### Pattern: Close and Reopen on Error

```python
async def create_price_page_with_recovery(
    session: P21Session,
    window: Window,
    item: dict,
    max_retries: int = 2
) -> tuple[Window, dict]:
    """Create a price page with error recovery.

    On failure, closes the corrupted window and opens a fresh one.

    Args:
        session: Active P21 session
        window: Current window (may be replaced on error)
        item: Price page data to create
        max_retries: Number of retry attempts

    Returns:
        Tuple of (current_window, result_dict)
    """
    for attempt in range(max_retries + 1):
        try:
            result = await create_price_page(window, item)
            return window, {"success": True, "result": result}

        except Exception as e:
            logger.warning(
                f"Attempt {attempt + 1} failed for {item.get('description', '?')}: {e}"
            )

            # Close the potentially corrupted window
            try:
                await window.close()
            except Exception:
                pass  # Window may already be in bad state

            if attempt < max_retries:
                # Open a fresh window and retry
                window = await session.open_window(service_name="SalesPricePage")
            else:
                # All retries exhausted - reopen window for next item
                window = await session.open_window(service_name="SalesPricePage")
                return window, {"success": False, "error": str(e)}

    # Should not reach here, but just in case
    return window, {"success": False, "error": "Unexpected retry exhaustion"}
```

### Why Not Recover In-Place?

| Recovery Strategy | Outcome |
|-------------------|---------|
| Clear data and retry | May fail - unsaved changes can persist |
| Cancel changes and retry | May fail - dialogs may be blocking |
| Close window and reopen | Reliable - guaranteed clean state |

The close-and-reopen strategy costs ~500ms but guarantees a clean state. For bulk operations, this reliability far outweighs the small performance cost.

---

## Page Expiration Workflow

Creating new price pages often requires expiring old ones to prevent pricing conflicts. If both an old and new page are active for the same supplier/product group, P21 may apply either one unpredictably.

### Pattern: Expire Before Replace

```python
async def expire_price_page(
    window: Window,
    price_page_uid: int,
    expiration_date: str
) -> bool:
    """Expire a price page by setting its expiration date.

    Args:
        window: Open SalesPricePage window
        price_page_uid: UID of the page to expire
        expiration_date: Date to expire the page (YYYY-MM-DD format)

    Returns:
        True if successful
    """
    # Load the page by UID
    result = await window.change_data(
        "FORM", "form", "price_page_uid", str(price_page_uid)
    )
    if not result.success:
        logger.error(f"Failed to load page {price_page_uid}: {result.messages}")
        return False

    # Set the expiration date
    result = await window.change_data(
        "FORM", "form", "expiration_date", expiration_date
    )
    if not result.success:
        logger.error(f"Failed to set expiration date: {result.messages}")
        return False

    # Save
    result = await window.save_data()
    if not result.success:
        logger.error(f"Failed to save expiration: {result.messages}")
        return False

    logger.info(f"Expired page {price_page_uid} (expires {expiration_date})")
    return True
```

### Bulk Expiration

Expiration follows the same batch patterns as creation. Process in batches with session-per-batch:

```python
async def expire_old_pages(
    client: P21Client,
    page_uids: list[int],
    expiration_date: str,
    batch_size: int = 25
) -> dict:
    """Bulk expire price pages.

    Args:
        client: Authenticated P21Client
        page_uids: List of price page UIDs to expire
        expiration_date: Expiration date (YYYY-MM-DD)
        batch_size: Pages per session batch

    Returns:
        Summary with success/failure counts
    """
    succeeded = 0
    failed = 0

    for i in range(0, len(page_uids), batch_size):
        batch = page_uids[i:i + batch_size]

        async with client.session() as session:
            window = await session.open_window(service_name="SalesPricePage")

            try:
                for uid in batch:
                    success = await expire_price_page(window, uid, expiration_date)
                    if success:
                        succeeded += 1
                        await window.clear_data()
                    else:
                        failed += 1
                        # Reopen window on failure
                        await window.close()
                        window = await session.open_window(
                            service_name="SalesPricePage"
                        )
            finally:
                await window.close()

    return {"succeeded": succeeded, "failed": failed, "total": len(page_uids)}
```

---

## Production-Grade Async Client

The example scripts in this project use synchronous `httpx`. For production batch processing, a full async client is recommended. Below is a complete, production-tested client architecture.

### Result Class

Parse Interactive API responses into a structured result:

```python
from dataclasses import dataclass, field


@dataclass
class Result:
    """Parsed result from an Interactive API response."""

    status_code: int  # 0=None, 1=Success, 2=Failure, 3=Blocked
    success: bool
    messages: list[str] = field(default_factory=list)
    events: list[dict] = field(default_factory=list)
    raw: dict = field(default_factory=dict)

    @classmethod
    def from_response(cls, response_data: dict) -> "Result":
        """Parse an API response dict into a Result.

        Status codes match the official ResultStatus enum from
        P21.UI.Service.Model.Interactive.V2.ResultWrapper:
            None=0, Success=1, Failure=2, Blocked=3

        The API may return Status as an integer (1, 2, 3) or a string
        ("Success", "Failure", "Blocked") depending on context.
        """
        status = response_data.get("Status", 0)

        # Official ResultStatus enum: None=0, Success=1, Failure=2, Blocked=3
        status_code = {
            "None": 0,
            "Success": 1,
            "Failure": 2,
            "Blocked": 3,
        }.get(status, 0) if isinstance(status, str) else status

        messages = []
        for event in response_data.get("Events", []):
            if event.get("Name") == "message":
                messages.append(event.get("Data", {}).get("Message", ""))

        return cls(
            status_code=status_code,
            success=status_code == 1,
            messages=messages,
            events=response_data.get("Events", []),
            raw=response_data,
        )

    def get_event(self, event_name: str) -> dict | None:
        """Get the first event matching the given name."""
        for event in self.events:
            if event.get("Name") == event_name:
                return event.get("Data", {})
        return None
```

### Event Parsing Helpers

Common events you need to extract from API responses:

```python
def get_generated_key(result: Result) -> int | None:
    """Extract auto-generated key (e.g., price_page_uid) from result events.

    After saving a new record, P21 fires a 'keygenerated' event
    containing the new UID.
    """
    event_data = result.get_event("keygenerated")
    if event_data:
        return int(event_data.get("Value", 0))
    return None


def get_opened_window_id(result: Result) -> str | None:
    """Extract window ID from a 'windowopened' event.

    When a response window/dialog opens, the API returns this event
    with the new window's ID.
    """
    event_data = result.get_event("windowopened")
    if event_data:
        return event_data.get("WindowId")
    return None
```

### Complete Window Class

```python
class Window:
    """Represents an open P21 Interactive API window."""

    def __init__(self, client: "P21Client", window_id: str):
        self.client = client
        self.window_id = window_id

    async def change_data(
        self,
        tab_name: str,
        datawindow_name: str,
        field_name: str,
        value: str,
    ) -> Result:
        """Change a single field value.

        Note: datawindow_name is required in P21 25.2+. Window data
        structures changed so the server can no longer auto-resolve
        the target datawindow from TabName alone.
        """
        payload = {
            "WindowId": self.window_id,
            "List": [
                {
                    "TabName": tab_name,
                    "DatawindowName": datawindow_name,
                    "FieldName": field_name,
                    "Value": value,
                }
            ],
        }
        resp = await self.client._put("/api/ui/interactive/v2/change", json=payload)
        return Result.from_response(resp)

    async def change_data_batch(
        self,
        changes: list[dict],
    ) -> Result:
        """Change multiple field values in a single request.

        Args:
            changes: List of dicts with keys: tab_name, datawindow_name,
                     field_name, value
        """
        payload = {
            "WindowId": self.window_id,
            "List": [
                {
                    "TabName": c["tab_name"],
                    "DatawindowName": c["datawindow_name"],
                    "FieldName": c["field_name"],
                    "Value": c["value"],
                }
                for c in changes
            ],
        }
        resp = await self.client._put("/api/ui/interactive/v2/change", json=payload)
        return Result.from_response(resp)

    async def select_tab(self, page_name: str) -> Result:
        """Switch to a different tab."""
        payload = {"WindowId": self.window_id, "PageName": page_name}
        resp = await self.client._put("/api/ui/interactive/v2/tab", json=payload)
        return Result.from_response(resp)

    async def change_row(self, row: int, datawindow_name: str) -> Result:
        """Select a specific row in a datawindow."""
        payload = {
            "WindowId": self.window_id,
            "DatawindowName": datawindow_name,
            "Row": row,
        }
        resp = await self.client._put("/api/ui/interactive/v2/row", json=payload)
        return Result.from_response(resp)

    async def add_row(self, datawindow_name: str) -> Result:
        """Add a new row to a datawindow."""
        payload = {
            "WindowId": self.window_id,
            "DatawindowName": datawindow_name,
        }
        resp = await self.client._post("/api/ui/interactive/v2/row", json=payload)
        return Result.from_response(resp)

    async def save_data(self) -> Result:
        """Save the current window data."""
        # v2 sends just the window ID string as the body
        resp = await self.client._put(
            "/api/ui/interactive/v2/data", content=f'"{self.window_id}"'
        )
        return Result.from_response(resp)

    async def clear_data(self) -> Result:
        """Clear the current window data (reset form for next record)."""
        resp = await self.client._delete(
            f"/api/ui/interactive/v2/data?id={self.window_id}"
        )
        return Result.from_response(resp)

    async def get_data(self) -> dict:
        """Get the current window data."""
        resp = await self.client._get(
            f"/api/ui/interactive/v2/data?id={self.window_id}"
        )
        return resp

    async def get_state(self) -> dict:
        """Get the current window state."""
        resp = await self.client._get(
            f"/api/ui/interactive/v2/window?windowId={self.window_id}"
        )
        return resp

    async def get_tools(self) -> list[dict]:
        """Get available tools (buttons) for the window."""
        resp = await self.client._get(
            f"/api/ui/interactive/v2/tools?windowId={self.window_id}"
        )
        return resp

    async def run_tool(self, tool_name: str, tool_text: str = "") -> Result:
        """Run a tool (click a button) in the window."""
        payload = {
            "WindowId": self.window_id,
            "ToolName": tool_name,
            "ToolText": tool_text,
        }
        resp = await self.client._post("/api/ui/interactive/v2/tools", json=payload)
        return Result.from_response(resp)

    async def close(self) -> None:
        """Close this window."""
        await self.client._delete(
            f"/api/ui/interactive/v2/window?windowId={self.window_id}"
        )
```

### Complete P21Client Class

```python
import httpx
import logging

logger = logging.getLogger(__name__)


class P21Client:
    """Production async client for P21 Interactive API.

    Handles authentication, session management, and window operations.
    Tested against 700+ operations in production.

    Usage:
        async with P21Client(base_url, username, password) as client:
            window = await client.open_window(service_name="SalesPricePage")
            result = await window.change_data("FORM", "description", "Test")
            await window.save_data()
            await window.close()
    """

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        verify_ssl: bool = True,
        timeout: float = 60.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.token: str | None = None
        self.ui_server_url: str | None = None
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                verify=self.verify_ssl,
                timeout=self.timeout,
                follow_redirects=True,
            )
        return self._client

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def authenticate(self) -> None:
        """Obtain a bearer token from P21."""
        client = self._get_client()
        response = await client.post(
            f"{self.base_url}/api/security/token",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "username": self.username,
                "password": self.password,
            },
            content="",
        )
        response.raise_for_status()
        self.token = response.json()["AccessToken"]

    async def get_ui_server(self) -> None:
        """Discover the UI server URL."""
        client = self._get_client()
        response = await client.get(
            f"{self.base_url}/api/ui/router/v1?urlType=external",
            headers=self._headers,
        )
        response.raise_for_status()
        self.ui_server_url = response.json()["Url"].rstrip("/")

    async def start_session(self) -> None:
        """Start an Interactive API session."""
        await self._post(
            "/api/ui/interactive/sessions/",
            json={"ResponseWindowHandlingEnabled": False},
        )

    async def end_session(self) -> None:
        """End the current Interactive API session."""
        try:
            await self._delete("/api/ui/interactive/sessions/")
        except Exception as e:
            logger.debug(f"Session cleanup error (ignored): {e}")

    async def open_window(self, service_name: str) -> Window:
        """Open a P21 window by service name."""
        resp = await self._post(
            "/api/ui/interactive/v2/window",
            json={"ServiceName": service_name},
        )
        window_id = resp.get("WindowId", resp.get("windowId", ""))
        return Window(self, window_id)

    # --- HTTP helpers ---

    async def _get(self, path: str, **kwargs) -> dict:
        client = self._get_client()
        resp = await client.get(
            f"{self.ui_server_url}{path}", headers=self._headers, **kwargs
        )
        resp.raise_for_status()
        return resp.json()

    async def _post(self, path: str, **kwargs) -> dict:
        client = self._get_client()
        resp = await client.post(
            f"{self.ui_server_url}{path}", headers=self._headers, **kwargs
        )
        resp.raise_for_status()
        return resp.json()

    async def _put(self, path: str, **kwargs) -> dict:
        client = self._get_client()
        resp = await client.put(
            f"{self.ui_server_url}{path}", headers=self._headers, **kwargs
        )
        resp.raise_for_status()
        return resp.json()

    async def _delete(self, path: str, **kwargs) -> dict | None:
        client = self._get_client()
        resp = await client.delete(
            f"{self.ui_server_url}{path}", headers=self._headers, **kwargs
        )
        resp.raise_for_status()
        if resp.content:
            return resp.json()
        return None

    # --- Context manager ---

    async def __aenter__(self) -> "P21Client":
        await self.authenticate()
        await self.get_ui_server()
        await self.start_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        await self.end_session()
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
        return False
```

---

## Complete Batch Workflow Example

Putting it all together: expire old pages, create new ones, and link to books.

```python
import asyncio
import logging

logger = logging.getLogger(__name__)


async def replace_supplier_pages(
    client: P21Client,
    supplier_id: int,
    old_page_uids: list[int],
    new_pages: list[dict],
    book_ids: list[str],
    expiration_date: str,
    batch_size: int = 25,
) -> dict:
    """Replace supplier price pages: expire old, create new, link to books.

    Args:
        client: Authenticated P21Client (no active session needed)
        supplier_id: Supplier ID
        old_page_uids: UIDs of pages to expire
        new_pages: List of page definitions to create
        book_ids: Price book IDs to link new pages to
        expiration_date: Date to set on old pages
        batch_size: Operations per session batch

    Returns:
        Summary dict with counts
    """
    summary = {"expired": 0, "created": 0, "linked": 0, "errors": []}

    # Phase 1: Expire old pages
    if old_page_uids:
        logger.info(f"Expiring {len(old_page_uids)} old pages...")
        result = await expire_old_pages(
            client, old_page_uids, expiration_date, batch_size
        )
        summary["expired"] = result["succeeded"]

    # Phase 2: Create new pages
    created_uids = []
    for i in range(0, len(new_pages), batch_size):
        batch = new_pages[i:i + batch_size]

        async with client.session() as session:
            window = await session.open_window(service_name="SalesPricePage")

            try:
                for page_def in batch:
                    try:
                        uid = await create_single_page(window, page_def)
                        created_uids.append(uid)
                        summary["created"] += 1
                        await window.clear_data()
                    except Exception as e:
                        summary["errors"].append(str(e))
                        await window.close()
                        window = await session.open_window(
                            service_name="SalesPricePage"
                        )
            finally:
                await window.close()

    # Phase 3: Link new pages to books
    for i in range(0, len(created_uids), batch_size):
        batch = created_uids[i:i + batch_size]

        async with client.session() as session:
            for uid in batch:
                for book_id in book_ids:
                    try:
                        await link_page_to_book(session, uid, book_id)
                        summary["linked"] += 1
                    except Exception as e:
                        summary["errors"].append(f"Link {uid}->{book_id}: {e}")

    logger.info(
        f"Complete: {summary['expired']} expired, "
        f"{summary['created']} created, "
        f"{summary['linked']} linked, "
        f"{len(summary['errors'])} errors"
    )
    return summary
```

---

## Performance Summary

Measured from production use creating and managing 700+ price pages:

| Operation | Time | Notes |
|-----------|------|-------|
| Authenticate | ~200ms | One-time per client |
| Start session | ~300ms | Once per batch |
| Open window | ~500ms | Once per batch |
| Change field | ~100ms | Per field |
| Save record | ~400ms | Per record |
| Clear data | ~200ms | Between records |
| Close window | ~200ms | Once per batch |
| End session | ~100ms | Once per batch |
| **Full page creation** | **~2.5s** | Including all fields + save |
| **25-page batch** | **~62s** | Including session overhead |

---

## Related

- [Interactive API](04-Interactive-API.md) - Core Interactive API documentation
- [SalesPricePage Codes](08-SalesPricePage-Codes.md) - Dropdown codes and field order
- [Error Handling](06-Error-Handling.md) - Error handling patterns
- [Session Pool Troubleshooting](07-Session-Pool-Troubleshooting.md) - Session pool issues
