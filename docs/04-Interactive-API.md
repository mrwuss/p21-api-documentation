# Interactive API

> **Disclaimer:** This is unofficial, community-created documentation for Epicor Prophet 21 APIs. It is not affiliated with, endorsed by, or supported by Epicor Software Corporation. All product names, trademarks, and registered trademarks are property of their respective owners. Use at your own risk.

---

## Overview

The Interactive API (IAPI) is a **stateful** RESTful API that simulates user interaction with P21 windows. It maintains session state, allowing you to perform complex multi-step operations with full business logic validation.

### Key Characteristics

- **Stateful** - Maintains session like a real user
- **Full business logic** - All validations applied
- **Window-based** - Works with P21 windows and fields
- **Response window handling** - Can handle dialogs
- **Complex workflows** - Multi-step operations supported

### When to Use

- Complex data entry requiring business logic
- Multi-step workflows with dependencies
- Operations that trigger response windows
- When you need to interact like a real user

---

## Endpoints

All Interactive API endpoints use the UI Server URL. First, obtain it:

```http
GET https://{hostname}/api/ui/router/v1?urlType=external
```

Then use the returned URL as base:

### Session Management

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/ui/interactive/sessions` | POST | Create new session |
| `/api/ui/interactive/sessions` | GET | List open sessions |
| `/api/ui/interactive/sessions` | DELETE | End session |

### Window Operations (v2)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/ui/interactive/v2/window` | POST | Open a window |
| `/api/ui/interactive/v2/window?id={windowId}` | GET | Get window state |
| `/api/ui/interactive/v2/window?id={windowId}` | DELETE | Close window |

### Data Operations (v2, Recommended)

> **Important:** Some P21 servers only support v2 endpoints. If you receive 404 errors on v1 endpoints, use v2 instead.

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/ui/interactive/v2/data` | PUT | Save data |
| `/api/ui/interactive/v2/data?id={windowId}` | GET | Get active data |
| `/api/ui/interactive/v2/data?id={windowId}` | DELETE | Clear data |
| `/api/ui/interactive/v2/change` | PUT | Change field values |
| `/api/ui/interactive/v2/tab` | PUT | Change active tab |
| `/api/ui/interactive/v2/row` | POST | Add a row |
| `/api/ui/interactive/v2/row` | PUT | Change current row |
| `/api/ui/interactive/v2/rows/limits` | PUT | Set active row limits |
| `/api/ui/interactive/v2/rows/selected` | POST | Select multiple rows |
| `/api/ui/interactive/v2/tools?windowId={windowId}` | GET | Get available tools |
| `/api/ui/interactive/v2/tools` | POST | Run a tool |

> **Query Parameter Inconsistency:** Most v2 endpoints use `?id=` for the window identifier, but the **tools endpoint uses `?windowId=`**. Verified by live testing:
>
> | Endpoint | Accepts `?id=` | Accepts `?windowId=` |
> |----------|:-:|:-:|
> | GET/DELETE `/v2/window` | **Yes** | No (422) |
> | GET/DELETE `/v2/data` | **Yes** | No (400/422) |
> | GET `/v2/tools` | No (400) | **Yes** |
>
> Using the wrong parameter returns an error — there is no fallback. `GET /v2/tools?id=` fails with HTTP 400 and a validation body (`"The windowId field is required."`).

### Data Operations (v1 - Legacy)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/ui/interactive/v1/data` | PUT | Save data |
| `/api/ui/interactive/v1/data` | GET | Get active data |
| `/api/ui/interactive/v1/data` | DELETE | Clear data |
| `/api/ui/interactive/v1/change` | PUT | Change field values |
| `/api/ui/interactive/v1/tab` | PUT | Change active tab |
| `/api/ui/interactive/v1/row` | POST | Add a row |
| `/api/ui/interactive/v1/row` | PUT | Change current row |
| `/api/ui/interactive/v1/tools` | GET | Get available tools |
| `/api/ui/interactive/v1/tools` | POST | Run a tool |

---

## Authentication

Include the Bearer token in the Authorization header:

```http
POST /api/ui/interactive/sessions HTTP/1.1
Host: {ui-server-host}
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json
```

See [Authentication](00-Authentication.md) for token generation.

---

## Session Lifecycle

### 1. Start Session

```json
POST /api/ui/interactive/sessions
{
    "ResponseWindowHandlingEnabled": false
}
```

Response (**25.2**):
```json
{
    "SessionId": "abc123...",
    "Status": "Active"
}
```

Response (**2026.1** — the identifier is renamed `SessionId` → `Id`):
```json
{
    "Id": "3f2b8c9e-1234-4a5b-9c0d-7e8f9a0b1c2d",
    "Properties": [
        {
            "Name": "Telemetry",
            "Properties": {
                "fullversion": "26.1.5894.1",
                "shortversion": "26.1",
                "configurationid": "3694"
            }
        }
    ]
}
```

> **Read both keys** — `data.get("Id") or data.get("SessionId")` — so one client works across versions. See [Breaking Changes § 2026.1](14-Breaking-Changes.md#p21-20261).

> **This is also how you find your middleware build.** P21 exposes no version endpoint (`/api/version`, `/api/v2/version` and similar all return 404). On 2026.1 the session-create response carries it under `Properties[0].Properties.fullversion` — the most reliable way to confirm which build you're talking to before relying on any version-specific behavior.

#### Session Parameters (UserParameters)

The session creation body accepts these optional parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `SessionType` | string | `"User"` | `User` (real user login), `Auto` (automated process), or `AutoInteractive` (automated without noninteractive API profile). Affects license consumption and behavior |
| `SessionTimeout` | int | Server default (60s) | Inactivity timeout in seconds before the session is cleaned up |
| `ResponseWindowHandlingEnabled` | bool | `true` | When `false`, response windows (dialogs) are auto-answered with the default response (usually "Yes"). Set to `true` if you need to inspect and handle dialogs yourself |
| `ClientPlatformApp` | string | null | Identifier for your application (useful for server-side logging) |
| `WorkstationID` | string | null | User-defined value to identify the PC or device initiating the session |

**Example with multiple parameters:**

```json
POST /api/ui/interactive/sessions
{
    "SessionType": "Auto",
    "SessionTimeout": 120,
    "ResponseWindowHandlingEnabled": false,
    "ClientPlatformApp": "PricePageSync",
    "WorkstationID": "INTEGRATION-01"
}
```

> **Session pool limits:** The server has a finite pool of API instances (default: 5). If all instances are busy, new session requests will wait up to 60 seconds before timing out. See [Session Pool Troubleshooting](07-Session-Pool-Troubleshooting.md) for configuration details and common issues.

### 2. Open Window

There are four ways to identify which window to open:

| Method | Field | Example | When to Use |
|--------|-------|---------|-------------|
| Service name | `ServiceName` | `"SalesPricePage"` | **Recommended — the only reliable identifier.** Works for every openable window |
| Menu title | `Title` | `"Sales Price Page Entry"` | Matches the menu label text — but can 400 where `ServiceName` succeeds (see caveat below) |
| Window name | `Name` | `"w_sales_price_page"` | Internal window name — same unreliability as `Title` |
| Menu ID | `MenuId` | `12345` | Numeric menu ID from P21 |

```json
POST /api/ui/interactive/v2/window
{
    "ServiceName": "SalesPricePage"
}
```

Or by menu title:
```json
{
    "Title": "Sales Price Page Entry"
}
```

Response:
```json
{
    "WindowId": "3f2b8c9e-1234-4a5b-9c0d-7e8f9a0b1c2d",
    "Title": "Sales Price Page Entry",
    "DataElements": [...]
}
```

> **Use `ServiceName` — the by-Name and by-Title paths are unreliable.** On 26.1 (verified 26.1.5894.1, July 2026), opening by `Name` or `Title` can be **rejected with HTTP 400 even for a window whose `ServiceName` opens fine**:
>
> ```text
> {"ServiceName": "Territory"}                 -> 200, window opens
> {"Name": "w_territory_maint"}                -> 400 "Cannot open window w_territory_maint because is not available or user <API_USER> does not have permission."
> {"Title": "Postal Code Group Maintenance"}   -> 400 (the window name resolves to empty in the error text)
> ```
>
> Despite the "not available or user does not have permission" wording, this is the same [undeployed/unavailable-window signal](03-Transaction-API.md#endpoints) seen on the Transaction API — a window is only reliably API-openable through a **registered service name**. Discover the service name for a window via `frame_menu.service_name` (see [Window→Service Discovery](#8-window-to-service-discovery-frame_menu)). Prefer `ServiceName` for every open.

### 3. Change Data

**v2 Format (Recommended):**

```json
PUT /api/ui/interactive/v2/change
{
    "WindowId": "3f2b8c9e-1234-4a5b-9c0d-7e8f9a0b1c2d",
    "List": [
        {
            "TabName": "FORM",
            "FieldName": "description",
            "Value": "New Description",
            "DatawindowName": "form"
        }
    ]
}
```

> **Note:** v2 uses `List` with `TabName`, while v1 uses `ChangeRequests` with `DataWindowName`. The `DatawindowName` field in v2 uses lowercase 'w'.

> **P21 25.2+ Breaking Change:** `DatawindowName` is now effectively **required** for v2 change requests. The 3-parameter form (TabName + FieldName + Value) stopped working after the 25.2 upgrade — you must include `DatawindowName` as the 4th field. Window data structures changed in 25.2 so the server can no longer auto-resolve the target datawindow from TabName alone. **Always include `DatawindowName` in change requests.**
>
> **Affected windows (confirmed):**
>
> | Window | Affected Field | Reporter |
> |--------|---------------|----------|
> | Item | Various | Community reports |
> | PO Receiving Group | `po_criteria_id` on `Criteria` tab | Jeff Patterson, Josiah Shollenberger |
> | Delivery List | Various | Community reports |
> | Group Pick Ticket | Various | Community reports |
> | ConvertPOToVoucher | `po_no` on `Voucher Information` tab | Jeff Patterson, Josiah Shollenberger |
> | Order Entry | `order_no` on `Order` tab | Neil Timmerman |
> | Clippership Auto Shipping | `pick_ticket_no` | Josh Owen |
> | Doc Links | Various | Jaime Nelson |
>
> The bug persists through at least version **25.2.5776.1**. Epicor has acknowledged this as a development bug.

**Fix example (C# SDK)** — the P21 C# SDK's `ChangeData`, not the REST call. For the REST equivalent see the change payloads in [Linking Price Page to Price Book](#example-linking-price-page-to-price-book).

```csharp
// Broken in 25.2+:
porgwindow.ChangeData("Criteria", "po_criteria_id", "20");

// Fixed — include DatawindowName:
porgwindow.ChangeData("Criteria", "tp_1_dw_1", "po_criteria_id", "20");
```

> *Credit: David Sokoloski (first discovered 4-param workaround), Jeff Patterson (confirmed fix)*

#### ValueType

Each change request supports an optional `ValueType` field:

| ValueType | Description |
|-----------|-------------|
| `"Display"` | The value as it appears on screen (default if omitted) |
| `"Data"` | The raw data value (e.g., internal key instead of display text) |

```json
{
    "TabName": "FORM",
    "DatawindowName": "form",
    "FieldName": "supplier_id",
    "Value": "10050",
    "ValueType": "Data"
}
```

Most of the time you can omit `ValueType` — the default `Display` works for typical field changes. Use `Data` when you need to set a field by its internal key value rather than its display text.

**v1 Format (Legacy):**

```json
PUT /api/ui/interactive/v1/change
{
    "WindowId": "w_sales_price_page",
    "ChangeRequests": [
        {
            "DataWindowName": "d_form",
            "FieldName": "description",
            "Value": "New Description"
        }
    ]
}
```

### 4. Save Data

**v2 Format (Recommended):**

```json
PUT /api/ui/interactive/v2/data
"3f2b8c9e-1234-4a5b-9c0d-7e8f9a0b1c2d"
```

> **Critical:** In v2, send just the WindowId GUID string as the JSON body - NOT wrapped in an object. This is a common source of 422 errors.

**v1 Format (Legacy):**

```json
PUT /api/ui/interactive/v1/data
{
    "WindowId": "w_sales_price_page"
}
```

### 5. Close Window

```json
DELETE /api/ui/interactive/v2/window?id=w_sales_price_page
```

### 6. End Session

```json
DELETE /api/ui/interactive/sessions
```

No body, no query parameter. The endpoint deletes **the session belonging to the bearer token you send** — which is why it needs neither.

> **A session can only be deleted by the token that created it.** Verified on 26.1.5910.3 (2026-08-11): create a session and `DELETE` it on the same token and you get `200` and the session is gone. Present a **different** token — a fresh login after your process restarted, another worker, a retry that re-authenticated — and *every* form is refused with `400 {"ErrorMessage":"Invalid session"}`:
>
> | Attempt (different token) | Result |
> |---|---|
> | `DELETE /sessions` (no body, as documented) | `400 Invalid session` |
> | `DELETE /sessions?id={sessionId}` | `400 Invalid session` |
> | `DELETE /sessions?sessionId={sessionId}` | `400 Invalid session` |
> | `DELETE /sessions` body `{"Id": "..."}` | `400 Invalid session` |
> | `DELETE /sessions` body `{"SessionId": "..."}` | `400 Invalid session` |
> | `DELETE /v2/sessions?id={sessionId}` | `404` (no such endpoint) |
>
> The orphan stays visible in `GET /api/ui/interactive/sessions` and there is no documented way to reap it early — you wait out `SessionCleanupExpiration`. The practical rule: **delete the session on the token that opened it, in a `finally`, before that token goes out of scope.** Once the token is gone, so is your ability to clean up.

---

## Finding Field Names

To find the correct field and datawindow names:

1. Open P21 in the web client
2. Navigate to the window
3. Right-click on the field
4. Select **Help > SQL Information**
5. Note the datawindow name and column name

---

## Window Discovery Techniques

> **Source**: Community working code + actual API testing (April 2026). Credit: Jon Christie.

Understanding a window's structure is essential before automating it. These techniques help you discover datawindow names, field names, available tools, and current data.

### 1. Get Window State

After opening a window, call `GetState()` (SDK) or `GET /api/ui/interactive/v2/window?id={windowId}` (REST) to retrieve the window definition — datawindows, fields, tabs, enabled states, and current data.

**The response shape**, verified live on 26.1.5910.3 (2026-08-11):

```jsonc
{
  "Data": { /* current values */ },
  "Definition": {
    "Id": "...", "Name": "...", "Title": "...",
    "TabPageList": [ /* array */ ],
    "Datawindows": {                 // a MAP keyed by datawindow name -- not an array
      "tp_1_dw_1": {
        "Name": "...", "ParentPage": "...", "Style": "...",
        "Fields": { /* also a MAP, keyed by field name */ }
      },
      "tp_17_dw_17": { }
    }
  }
}
```

Three things that catch people out:

- **Everything is under `Definition`.** The datawindows are not at the top level; `Data` is a sibling, not a parent.
- **`Datawindows` and `Fields` are maps, not arrays.** Iterating them positionally yields keys (strings), not objects. `TabPageList` *is* an array — the two shapes sit side by side.
- **You get the ACTIVE tab page's datawindows, not the whole window.** This is the part that misleads people into thinking a field doesn't exist. Verified on `SalesPricePage` (26.1.5910.3) by selecting each tab and re-reading:

  | After selecting tab | `Datawindows` contains |
  |---|---|
  | *(on open)* | `form` |
  | `VALUES` | `values` |
  | `COSTS` | `costs` |
  | `PO COST MULTIPLIERS` | `price_page_po_cost_calc` |

  Each selection **replaces** the previous one. So a datawindow's absence proves only that its tab isn't active — switch tabs with `PUT /v2/tab` (`PageName`) and read again, or use `definitions/{Service}.json` for the whole picture at once. The same caveat applies to `GET /v2/data`.

- **Interactive datawindow names are not the Transaction API's names.** The same tab is `form` here and `d_dw_price_page_main` in `definitions/SalesPricePage.json`; `values` vs `d_dw_price_page_values`; `costs` vs `d_dw_price_page_cost`. Both are correct — for their own API. Sending a `d_dw_*` name in an Interactive `DatawindowName`, or a short name in a Transaction `DataElement`, will not find the datawindow. The tab page names (`FORM`, `VALUES`, `COSTS`, `PO COST MULTIPLIERS`, `USED BY`, `TP_PRICE_PAGE_X_LOCATION`, `TIMESTAMPPRICE_PAGE`) are shared, and come back in `Definition.TabPageList` with their display text and `Enabled` state.

- **Field metadata here carries no dropdown values.** Each field exposes only `Name`, `Label`, `DataType` and `Enabled` — there is no `ValidValues`. To learn what a code field accepts, read the **Transaction** definition (`GET /api/v2/definition/{Service}`) even when you intend to drive the window interactively; it lists the display labels you send under `UseCodeValues: false`. See [SalesPricePage Codes](08-SalesPricePage-Codes.md).

Complete program — authenticates, opens a window by `ServiceName`, prints every tab and datawindow it exposes, then closes the window and the session. Run it against any window whose structure you need before automating it.

<!-- tabs -->

#### Python

```python
"""Open a P21 window and print the tabs, datawindows and fields it exposes."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
SERVICE_NAME = "SalesPricePage"           # window to inspect — always open by ServiceName
# ---------------------------------------------------------------------------


def get_token(client: httpx.Client) -> str:
    """v2 token endpoint — credentials go in the body, never in headers."""
    r = client.post(
        f"{BASE_URL}/api/security/token/v2",
        json={"username": USERNAME, "password": PASSWORD},
        headers={"Accept": "application/json"},
    )
    r.raise_for_status()
    try:
        return r.json()["AccessToken"]
    except (ValueError, KeyError):  # some middleware answers in XML
        match = re.search(r"<AccessToken>([^<]+)</AccessToken>", r.text)
        if not match:
            raise ValueError(f"No AccessToken in response: {r.text[:200]}") from None
        return match.group(1)


def get_ui_server(client: httpx.Client, token: str) -> str:
    """Transaction and Interactive calls go to the UI server, not BASE_URL."""
    r = client.get(
        f"{BASE_URL}/api/ui/router/v1/?urlType=external",  # trailing slash avoids a 307
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )
    r.raise_for_status()
    try:
        return r.json()["Url"].rstrip("/")
    except (ValueError, KeyError):
        match = re.search(r"<Url>([^<]+)</Url>", r.text)
        if not match:
            raise ValueError(f"No Url in router response: {r.text[:200]}") from None
        return match.group(1).rstrip("/")


with httpx.Client(verify=VERIFY_SSL, timeout=120, follow_redirects=True) as client:
    token = get_token(client)
    ui_server = get_ui_server(client, token)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",       # 2026.1 returns an empty 500 without this
        "Content-Type": "application/json",
    }

    r = client.post(
        f"{ui_server}/api/ui/interactive/sessions",
        headers=headers,
        json={"ResponseWindowHandlingEnabled": False},
    )
    r.raise_for_status()
    session = r.json()
    # 25.2 returns SessionId; 2026.1 renamed it Id — read either.
    print("session:", session.get("Id") or session.get("SessionId"))

    window_id = None
    try:
        r = client.post(
            f"{ui_server}/api/ui/interactive/v2/window",
            headers=headers,
            json={"ServiceName": SERVICE_NAME},
        )
        r.raise_for_status()
        opened = r.json()
        window_id = opened.get("WindowId") or opened.get("Id")
        print("window:", window_id)

        r = client.get(
            f"{ui_server}/api/ui/interactive/v2/window",   # note: ?id=, not ?windowId=
            headers=headers,
            params={"id": window_id},
        )
        r.raise_for_status()
        state = r.json()
        definition = state.get("Definition", state)

        for tab in definition.get("TabPageList", []):
            print(f"tab {tab.get('Name')!r:32} enabled={tab.get('Enabled')}")

        # Datawindows arrive as a map keyed by name; normalise to a list either way.
        datawindows = definition.get("Datawindows", {})
        if isinstance(datawindows, dict):
            datawindows = [{"Name": k, **v} for k, v in datawindows.items()]
        for dw in datawindows:
            fields = dw.get("Fields", {})
            names = sorted(fields) if isinstance(fields, dict) else [
                f.get("Name") for f in fields
            ]
            print(f"datawindow {dw.get('Name')} (tab: {dw.get('ParentPage')})")
            print(f"    fields: {names}")
    finally:
        if window_id:
            client.delete(
                f"{ui_server}/api/ui/interactive/v2/window",
                headers=headers,
                params={"id": window_id},
            )
        # Always delete the session: a leaked one 409s ("Session already exists")
        # on your next create until it is cleaned up.
        client.delete(f"{ui_server}/api/ui/interactive/sessions", headers=headers)
```

#### C#

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string ServiceName = "SalesPricePage";           // window to inspect — open by ServiceName
// ---------------------------------------------------------------------------

var handler = new HttpClientHandler
{
    // Test tenants often present a self-signed cert. Delete this line in production.
    ServerCertificateCustomValidationCallback =
        HttpClientHandler.DangerousAcceptAnyServerCertificateValidator,
};
using var client = new HttpClient(handler) { Timeout = TimeSpan.FromMinutes(2) };
client.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));

var token = await GetTokenAsync(client);
var uiServer = await GetUiServerAsync(client, token);
client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);

var sessionResponse = await client.PostAsync(
    $"{uiServer}/api/ui/interactive/sessions",
    Json(new { ResponseWindowHandlingEnabled = false }));
sessionResponse.EnsureSuccessStatusCode();
using (var session = JsonDocument.Parse(await sessionResponse.Content.ReadAsStringAsync()))
{
    // 25.2 returns SessionId; 2026.1 renamed it Id — read either.
    Console.WriteLine($"session: {Field(session.RootElement, "Id") ?? Field(session.RootElement, "SessionId")}");
}

string? windowId = null;
try
{
    var openResponse = await client.PostAsync(
        $"{uiServer}/api/ui/interactive/v2/window",
        Json(new { ServiceName }));
    openResponse.EnsureSuccessStatusCode();
    using (var opened = JsonDocument.Parse(await openResponse.Content.ReadAsStringAsync()))
        windowId = Field(opened.RootElement, "WindowId") ?? Field(opened.RootElement, "Id");
    Console.WriteLine($"window: {windowId}");

    // note: ?id=, not ?windowId=
    var stateResponse = await client.GetAsync(
        $"{uiServer}/api/ui/interactive/v2/window?id={windowId}");
    stateResponse.EnsureSuccessStatusCode();

    using var state = JsonDocument.Parse(await stateResponse.Content.ReadAsStringAsync());
    var definition = state.RootElement.TryGetProperty("Definition", out var d)
        ? d
        : state.RootElement;

    if (definition.TryGetProperty("TabPageList", out var tabs))
        foreach (var tab in tabs.EnumerateArray())
            Console.WriteLine($"tab {Field(tab, "Name")} enabled={Field(tab, "Enabled")}");

    if (definition.TryGetProperty("Datawindows", out var datawindows))
    {
        // Datawindows arrive as a map keyed by name; tolerate an array too.
        var entries = datawindows.ValueKind == JsonValueKind.Object
            ? datawindows.EnumerateObject().Select(p => (Name: p.Name, Value: p.Value))
            : datawindows.EnumerateArray().Select(e => (Name: Field(e, "Name") ?? "", Value: e));

        foreach (var (name, dw) in entries)
        {
            var fields = new List<string>();
            if (dw.TryGetProperty("Fields", out var f))
                fields = f.ValueKind == JsonValueKind.Object
                    ? f.EnumerateObject().Select(p => p.Name).ToList()
                    : f.EnumerateArray().Select(e => Field(e, "Name") ?? "").ToList();

            Console.WriteLine($"datawindow {name} (tab: {Field(dw, "ParentPage")})");
            Console.WriteLine($"    fields: {string.Join(", ", fields)}");
        }
    }
}
finally
{
    if (windowId is not null)
        await client.DeleteAsync($"{uiServer}/api/ui/interactive/v2/window?id={windowId}");

    // Always delete the session: a leaked one 409s ("Session already exists")
    // on your next create until it is cleaned up.
    await client.DeleteAsync($"{uiServer}/api/ui/interactive/sessions");
}

// --- helpers ---------------------------------------------------------------

static StringContent Json(object body) =>
    new(JsonSerializer.Serialize(body), Encoding.UTF8, "application/json");

static string? Field(JsonElement element, string name) =>
    element.TryGetProperty(name, out var value) ? value.ToString() : null;

// v2 token endpoint — credentials go in the body, never in headers.
static async Task<string> GetTokenAsync(HttpClient client)
{
    var payload = JsonSerializer.Serialize(new { username = Username, password = Password });
    var response = await client.PostAsync(
        $"{BaseUrl}/api/security/token/v2",
        new StringContent(payload, Encoding.UTF8, "application/json"));
    response.EnsureSuccessStatusCode();
    return ReadField(await response.Content.ReadAsStringAsync(), "AccessToken");
}

// Transaction and Interactive calls go to the UI server, not BaseUrl.
static async Task<string> GetUiServerAsync(HttpClient client, string token)
{
    using var request = new HttpRequestMessage(
        HttpMethod.Get, $"{BaseUrl}/api/ui/router/v1/?urlType=external");
    request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
    var response = await client.SendAsync(request);
    response.EnsureSuccessStatusCode();
    return ReadField(await response.Content.ReadAsStringAsync(), "Url").TrimEnd('/');
}

// Some middleware answers these two endpoints in XML even when asked for JSON.
static string ReadField(string payload, string field)
{
    try
    {
        var value = JsonDocument.Parse(payload).RootElement.GetProperty(field).GetString();
        if (!string.IsNullOrEmpty(value)) return value;
    }
    catch (Exception ex) when (ex is JsonException or KeyNotFoundException) { }

    var match = System.Text.RegularExpressions.Regex.Match(payload, $"<{field}>([^<]+)</{field}>");
    if (!match.Success)
        throw new InvalidOperationException(
            $"No {field} in response: {payload[..Math.Min(200, payload.Length)]}");
    return match.Groups[1].Value;
}
```

<!-- /tabs -->

**Example response** (sanitized, structure varies by window):

```json
{
  "Definition": {
    "Title": "Order Entry",
    "Datawindows": {
      "form": {
        "Fields": {
          "order_no": {"Label": "Order No", "Enabled": true, "DataType": 1},
          "customer_id": {"Label": "Customer ID", "Enabled": true, "DataType": 1}
        }
      }
    },
    "TabPageList": [
      {"Name": "Order", "DisplayText": "Order"},
      {"Name": "Line_Items", "DisplayText": "Line Items"}
    ]
  }
}
```

> **Tip:** Response windows return an empty `TabPageList` — that is how you can distinguish them from normal windows programmatically.

### 2. Get Available Tools

Call `GetTools()` (SDK) or `GET /api/ui/interactive/v2/tools?windowId={windowId}` (REST) to see available buttons. Tools can be queried at window, datawindow, and field levels by adding `dwName`, `fieldName`, and `row` parameters.

**Example response:**

```json
[
  {"ToolName": "cb_ok", "DatawindowName": null, "FieldName": null},
  {"ToolName": "cb_cancel", "DatawindowName": null, "FieldName": null},
  {"ToolName": "m_addlink", "DatawindowName": "Document_Link", "FieldName": null}
]
```

### 3. Get Current Data

Call `GetData()` (SDK) or `GET /api/ui/interactive/v2/data?id={windowId}` (REST) to retrieve the current data in each datawindow on the active tab. Returns column names, row data, active row index, and total row count.

### 4. Check Result Events

Every API response includes an `Events` collection. When a response window opens, look for `Name: "windowopened"` events. When tabs become enabled, look for `Name: "tabpageenabled"` events. When a new record is saved, look for `Name: "keygenerated"` events.

### 5. P21 SQL Information

In the P21 desktop or web client, right-click any field and select **Help > SQL Information**. This dialog shows:
- **Datawindow name** — the name to use in `DatawindowName` for change requests
- **Column name** — the field name to use in `FieldName`
- **Table name** — the underlying database table

This is the most reliable way to determine the exact names the API expects.

### 6. Browser DevTools

When using the P21 Web Client, open your browser's Developer Tools (F12) and watch the **Network** tab. Every action you perform in the UI generates REST calls to the Interactive API. This lets you see the exact payloads, endpoints, and field names the web client uses — which you can replicate in your automation.

### 7. Transaction API Service Definition

For windows that also exist as Transaction API services (Order, PurchaseOrder, Item, etc.), `GET /api/v2/definition/{ServiceName}` returns the full schema: every DataElement with its `DatawindowName`, `Type` (`Form`/`List`), `KeyFields`, and `FieldDefinitions[]` (field `Name`, `DbColumnName`, `DataType`, `Required`). This is the fastest way to enumerate which datawindows exist and which column names a write needs. See [Get Service Definition](03-Transaction-API.md#get-service-definition) in the Transaction API guide.

> **Warning — don't derive `TABPAGE_N` from the visible tab order:** The `TABPAGE_N` names are **not** sequential with the tabs you see in the UI. The PurchaseOrder window, for example, has 37 tab pages — many disabled or hidden, split across the header and detail bands — so the Items grid that *looks* like the second tab is actually `TABPAGE_17` (`tp_17_dw_17`). Counting visible tabs gives you the wrong name. Read the `TabPageList` from the window state (`GET /api/ui/interactive/v2/window?id={windowId}`) or cross-reference on the **datawindow name** (`tp_N_dw_N` / `d_...`). On the servers tested (25.2/26.x), the Interactive window's `TABPAGE_N` names matched the Transaction API definition's 1:1 — the datawindow name remains the safest identifier either way.

### 8. Window-to-Service Discovery (`frame_menu`)

Because [opening by `Name`/`Title` is unreliable](#2-open-window) and only a registered **service name** reliably opens a window, you need a way to map a menu item / `w_*` window to its service name. The `Prophet21.dbo.frame_menu` table is that map:

```sql
SELECT menu_item_name,      -- the menu label ("Territory Maintenance")
       stringparm,          -- the w_* window name ("w_territory_maint")
       service_name,        -- the ServiceName to open it with ("Territory") — NULL = no API surface
       enabled,             -- menu item enabled
       new_ui_enabled,      -- available in the new (web) UI
       angular_enabled      -- available in the Angular client
FROM   frame_menu
WHERE  stringparm LIKE 'w[_]%';
```

- **`service_name`** is the identifier to pass as `ServiceName` — e.g. Territory Maintenance → `Territory`, Territory Group Maintenance → `TerritoryGroup`.
- **`service_name IS NULL`** marks a window with **no API surface at all** — it 500s on `GET /api/v2/definition/{guess}` and 400s on an Interactive by-Name open. On the tested 26.1 system, Zip Code Maintenance (`w_zip_code_maint`) and Postal Code Group Maintenance (`w_postal_code_group_maint`) are both NULL — classic-desktop-only, undeployed windows (see [Undeployed/unavailable windows](02-OData-API.md#undeployed-unlicensed-windows-readable-tables-no-api-surface)).
- This complements the [`window_x_menu` discovery path](03-Transaction-API.md#pdf-report-generation) documented for report (`m_*`) services: `window_x_menu` finds callable report names; `frame_menu.service_name` finds the interactive/transaction service name behind a maintenance window.

> Environment: verified on 26.1.5894.1 (play), July 2026. (The "does not have permission" wording names whichever user is calling — it's an availability signal, not a grantable permission.)

---

## Response Windows

Response windows (dialogs) can pop up during operations. When this happens:

1. The result will have `Status: 3` (Blocked)
2. Check the `Events` array for `windowopened`
3. Get the new window ID from the event data
4. Handle the response window (interact with it like any other window)
5. Close/dismiss it to resume the original operation

> **The popup's id lives in `Events` — not in the top-level `ResponseWindowId`.** That field exists in the response and is **empty on real 26.1 responses**, so a client that reads it gets `""` and concludes there is no popup to answer. A production integration had *every* blocked save fail this way before switching to the event. Read `Events[] → windowopened → Data[] → windowid`; check the top-level field first only as forward-compatibility, never as the primary source.

> **There is no dedicated "answer this dialog" endpoint** — message boxes (`w_message`) cannot be answered programmatically. Probed and dead (January 2026): `PUT /api/ui/interactive/v2/responsewindow` → 404, `PUT /api/ui/interactive/v2/responsewindows` → 404, `POST /api/ui/interactive/v2/button` → 404, `DELETE /api/ui/interactive/v2/window?button=No` → 400. With `ResponseWindowHandlingEnabled: false` a `w_message` is auto-answered with its default (usually "Yes") — e.g. changing `product_group_id` on `inv_loc` triggers a "update GL accounts?" dialog whose default **overwrites the location's GL, revenue, and COS accounts**. Non-message-box popups ARE drivable: discover buttons via `GET /tools?windowId={id}` and click via `POST /tools` (see [Response Window Types](#response-window-types)).

> **Status codes** match the `ResultStatus` enum in `P21.UI.Service.Model.Interactive.V2.ResultWrapper`:
> `None=0, Success=1, Failure=2, Blocked=3`.
> The API returns Status as an integer. String values (`"Success"`, `"Failure"`, `"Blocked"`) may appear in some contexts — handle both.

Example response with blocked status:
```json
{
    "Status": 3,
    "Events": [
        {
            "Name": "windowopened",
            "Data": [
                { "Key": "windowid", "Value": "w_response_123" }
            ]
        }
    ]
}
```

> **Note:** The `Events[].Data` field uses a key-value list format:
> `[{"Key": "windowid", "Value": "..."}]`

### Response Window Handling (Tabless Windows)

Response windows (popup dialogs) have **no tabs**. When you receive `Status: 3` (Blocked), a response window has appeared and you must interact with it before continuing. The critical difference from normal windows is that change requests on response windows require `TabName = null` because there are no tabs to reference.

**REST API pattern:**

Include `"TabName": null` in the change request payload:

```json
PUT /api/ui/interactive/v2/change
{
    "WindowId": "w_response_123",
    "List": [
        {
            "TabName": null,
            "DatawindowName": "datawindow_name",
            "FieldName": "field_name",
            "Value": "value"
        }
    ]
}
```

**REST examples (Python / C#)** — one step of a longer sequence: the response window must already have been opened by something (a tool, a save), and its ID comes from that call's `windowopened` event.

> Full runnable version: [Recipe: Add a Header Note](#recipe-add-a-header-note)

<!-- tabs -->

#### Python

```python
async def change_response_window_field(
    client: httpx.AsyncClient,
    ui_url: str,
    headers: dict[str, str],
    response_window_id: str,
    datawindow_name: str,
    field_name: str,
    value: str,
) -> dict:
    """Change a field on a tabless response window.

    Args:
        client: httpx async client.
        ui_url: UI server base URL.
        headers: Request headers with auth token.
        response_window_id: The response window ID from the windowopened event.
        datawindow_name: Datawindow name within the response window.
        field_name: Field to change.
        value: New value.

    Returns:
        Parsed response dict.
    """
    response = await client.put(
        f"{ui_url}/api/ui/interactive/v2/change",
        headers=headers,
        json={
            "WindowId": response_window_id,
            "List": [
                {
                    "TabName": None,
                    "DatawindowName": datawindow_name,
                    "FieldName": field_name,
                    "Value": value,
                }
            ],
        },
    )
    response.raise_for_status()
    return response.json()
```

#### C\#

```csharp
public async Task<JsonElement> ChangeResponseWindowFieldAsync(
    HttpClient http,
    string uiUrl,
    string responseWindowId,
    string datawindowName,
    string fieldName,
    string value)
{
    // Response windows have no tabs — set TabName to null
    var payload = new JsonElement
    {
        ["WindowId"] = responseWindowId,
        ["List"] = new JsonElement
        {
            new JsonElement
            {
                ["TabName"] = null,
                ["DatawindowName"] = datawindowName,
                ["FieldName"] = fieldName,
                ["Value"] = value
            }
        }
    };
    var content = new StringContent(payload.ToString(), Encoding.UTF8, "application/json");
    var response = await http.PutAsync($"{uiUrl}/api/ui/interactive/v2/change", content);
    response.EnsureSuccessStatusCode();

    return JsonElement.Parse(await response.Content.ReadAsStringAsync());
}
```

<!-- /tabs -->

> **Note:** The `TabName: null` pattern applies to response windows that accept change requests (editable dialogs with Status: 3/Blocked). `w_message` dialogs cannot be edited programmatically. Use `ResponseWindowHandlingEnabled: false` in the session configuration to auto-answer message box dialogs with their default button.

**Common response window buttons:** `cb_ok`, `cb_cancel`, `cb_finish`, `cb_yes`, `cb_no`

Use `GET /api/ui/interactive/v2/tools?windowId={responseWindowId}` to discover which buttons are available, then `POST /api/ui/interactive/v2/tools` to click them. See the [Response Window Types](#response-window-types) section below for dismissal patterns.

*Credit: Jon Christie*

### Worked Example: "Item Issues Detected" (rule callback)

A concrete `w_rule_callback_response` case from the Item window. Items with data problems pop an **"Item Issues Detected"** dialog; the Transaction API cannot get past it (the change is discarded — see [Item Service gotchas](03-Transaction-API.md#item-service-gotchas)). Interactively, it's answerable:

1. Start the session with `ResponseWindowHandlingEnabled: true`.
2. Open the `Item` window and set `item_id` on `TABPAGE_1.tp_1_dw_1`. **Some items pop the dialog at retrieve time** — the moment `item_id` is set — which blocks the location list from loading. Check the result for a `windowopened` event and answer the popup immediately, not just at save.
3. Navigate and make your edits (e.g. select the location row on `TABPAGE_17.invloclist`, edit `TABPAGE_18.inv_loc_detail`).
4. `save()` — if the dialog opens, the result is Status 3 (Blocked) with a `windowopened` event carrying the popup's window ID.
5. Discover the buttons with `GET /v2/tools?windowId={popupId}`: `cb_1` = **"Yes, Proceed Anyway"**, `cb_2` = "No, Cancel". Run `cb_1` via `POST /v2/tools` with the popup's window ID; the save then commits.

Which items trip the rule is **deterministic**, not environmental luck: a site-configured DynaChange rule fires on every save of the Item window, and you can identify it — and usually fix the data instead — before writing any code. See [Item Issues Detected — Root Cause and Data Fix](03-Transaction-API.md#item-issues-detected-popup-root-cause-and-data-fix). Use this interactive path for the cases you cannot data-fix; don't hard-code a fallback list of items.

> **Credit:** [Alex Westemeier](https://github.com/AWestemeier).

---

## Changing Tabs

Before changing fields on a different tab, select the tab first:

**v2 Format (Recommended):**

```json
PUT /api/ui/interactive/v2/tab
{
    "WindowId": "w_sales_price_page",
    "PageName": "VALUES"
}
```

> **Note:** In v2, use `PageName` directly. In v1, use `PagePath: { PageName: "..." }`.

**v1 Format (Legacy):**

```json
PUT /api/ui/interactive/v1/tab
{
    "WindowId": "w_sales_price_page",
    "PagePath": {
        "PageName": "VALUES"
    }
}
```

---

## Running Tools (Buttons)

Tools include all buttons and right-click (RMB) options available at any point in a session. They exist at three levels:

1. **Window level** — Ribbon buttons, window-level buttons
2. **Datawindow level** — Grid/form buttons, RMB options on a datawindow
3. **Field level** — Field-specific RMB options

### Get Available Tools

Query tools at different levels by specifying optional parameters:

```http
GET /api/ui/interactive/v2/tools?windowId=w_sales_price_page
GET /api/ui/interactive/v2/tools?windowId=w_sales_price_page&dwName=form
GET /api/ui/interactive/v2/tools?windowId=w_sales_price_page&dwName=form&fieldName=description&row=0
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `windowId` | Yes | Window ID |
| `dwName` | No | Datawindow name — returns datawindow-level tools |
| `fieldName` | No | Field name — returns field-level tools |
| `row` | No | Row number — for grid-specific tools |

### Run a Tool

```json
POST /api/ui/interactive/v2/tools
{
    "WindowId": "w_sales_price_page",
    "ToolName": "cb_save",
    "ToolText": "Save"
}
```

> **The key must be `ToolName`.** Posting the button under `Name` — the spelling most other P21 payloads use — is accepted and does **nothing**: P21 returns `Status: 2` (Failure) with no message, so the tool never runs and a popup you were trying to dismiss stays open. Verified live on 26.1. `GET /v2/tools` returns the buttons under `ToolName` too; carry that key straight through to the POST rather than re-mapping it.

For datawindow or field-level tools, include the optional fields:

```json
{
    "WindowId": "w_sales_price_page",
    "ToolName": "tool_name",
    "ToolText": "Tool Label",
    "DatawindowName": "form",
    "FieldName": "description",
    "Row": 0
}
```

---

## Python and C# Examples

### Basic Client Class

The minimum viable Interactive client: authenticate, resolve the UI server, open a session with the [session parameters](#session-parameters-userparameters), read it back from `GET /sessions`, and always delete it. Complete program — it is also the quickest way to print your middleware build, since P21 exposes no version endpoint.

<!-- tabs -->

#### Python

```python
"""Open an Interactive session, print the middleware build, and clean it up."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
SESSION_TYPE = "Auto"                     # User | Auto | AutoInteractive
SESSION_TIMEOUT = 120                     # inactivity seconds before cleanup
CLIENT_APP = "PricePageSync"              # shows up in server-side logging
WORKSTATION_ID = "INTEGRATION-01"         # your identifier for this machine
# ---------------------------------------------------------------------------


def get_token(client: httpx.Client) -> str:
    """v2 token endpoint — credentials go in the body, never in headers."""
    r = client.post(
        f"{BASE_URL}/api/security/token/v2",
        json={"username": USERNAME, "password": PASSWORD},
        headers={"Accept": "application/json"},
    )
    r.raise_for_status()
    try:
        return r.json()["AccessToken"]
    except (ValueError, KeyError):  # some middleware answers in XML
        match = re.search(r"<AccessToken>([^<]+)</AccessToken>", r.text)
        if not match:
            raise ValueError(f"No AccessToken in response: {r.text[:200]}") from None
        return match.group(1)


def get_ui_server(client: httpx.Client, token: str) -> str:
    """Transaction and Interactive calls go to the UI server, not BASE_URL."""
    r = client.get(
        f"{BASE_URL}/api/ui/router/v1/?urlType=external",  # trailing slash avoids a 307
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )
    r.raise_for_status()
    try:
        return r.json()["Url"].rstrip("/")
    except (ValueError, KeyError):
        match = re.search(r"<Url>([^<]+)</Url>", r.text)
        if not match:
            raise ValueError(f"No Url in router response: {r.text[:200]}") from None
        return match.group(1).rstrip("/")


with httpx.Client(verify=VERIFY_SSL, timeout=120, follow_redirects=True) as client:
    token = get_token(client)
    ui_server = get_ui_server(client, token)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",       # 2026.1 returns an empty 500 without this
        "Content-Type": "application/json",
    }

    try:
        r = client.post(
            f"{ui_server}/api/ui/interactive/sessions",
            headers=headers,
            json={
                "SessionType": SESSION_TYPE,
                "SessionTimeout": SESSION_TIMEOUT,
                "ResponseWindowHandlingEnabled": False,
                "ClientPlatformApp": CLIENT_APP,
                "WorkstationID": WORKSTATION_ID,
            },
        )
        r.raise_for_status()
        session = r.json()

        # 25.2 returns SessionId; 2026.1 renamed it Id — read either.
        print("session:", session.get("Id") or session.get("SessionId"))

        # There is no version endpoint: the build rides the create response.
        for prop in session.get("Properties", []):
            build = (prop.get("Properties") or {}).get("fullversion")
            if build:
                print("middleware build:", build)

        # Read-back: list the sessions the server thinks are open.
        r = client.get(f"{ui_server}/api/ui/interactive/sessions", headers=headers)
        r.raise_for_status()
        print("open sessions:", r.text[:400])
    finally:
        # A session left behind 409s ("Session already exists") on the next
        # create — including the ghost left by a failed create. DELETE clears
        # it instantly; don't wait out SessionCleanupExpiration.
        client.delete(f"{ui_server}/api/ui/interactive/sessions", headers=headers)
```

#### C#

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string SessionType = "Auto";                     // User | Auto | AutoInteractive
const int SessionTimeout = 120;                        // inactivity seconds before cleanup
const string ClientApp = "PricePageSync";              // shows up in server-side logging
const string WorkstationId = "INTEGRATION-01";         // your identifier for this machine
// ---------------------------------------------------------------------------

var handler = new HttpClientHandler
{
    // Test tenants often present a self-signed cert. Delete this line in production.
    ServerCertificateCustomValidationCallback =
        HttpClientHandler.DangerousAcceptAnyServerCertificateValidator,
};
using var client = new HttpClient(handler) { Timeout = TimeSpan.FromMinutes(2) };
client.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));

var token = await GetTokenAsync(client);
var uiServer = await GetUiServerAsync(client, token);
client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);

try
{
    var createResponse = await client.PostAsync(
        $"{uiServer}/api/ui/interactive/sessions",
        Json(new
        {
            SessionType,
            SessionTimeout,
            ResponseWindowHandlingEnabled = false,
            ClientPlatformApp = ClientApp,
            WorkstationID = WorkstationId,
        }));
    createResponse.EnsureSuccessStatusCode();

    using (var session = JsonDocument.Parse(await createResponse.Content.ReadAsStringAsync()))
    {
        // 25.2 returns SessionId; 2026.1 renamed it Id — read either.
        var root = session.RootElement;
        Console.WriteLine($"session: {Field(root, "Id") ?? Field(root, "SessionId")}");

        // There is no version endpoint: the build rides the create response.
        if (root.TryGetProperty("Properties", out var properties))
            foreach (var property in properties.EnumerateArray())
                if (property.TryGetProperty("Properties", out var inner) &&
                    inner.TryGetProperty("fullversion", out var build))
                    Console.WriteLine($"middleware build: {build}");
    }

    // Read-back: list the sessions the server thinks are open.
    var listResponse = await client.GetAsync($"{uiServer}/api/ui/interactive/sessions");
    listResponse.EnsureSuccessStatusCode();
    var body = await listResponse.Content.ReadAsStringAsync();
    Console.WriteLine($"open sessions: {body[..Math.Min(400, body.Length)]}");
}
finally
{
    // A session left behind 409s ("Session already exists") on the next create —
    // including the ghost left by a failed create. DELETE clears it instantly;
    // don't wait out SessionCleanupExpiration.
    await client.DeleteAsync($"{uiServer}/api/ui/interactive/sessions");
}

// --- helpers ---------------------------------------------------------------

static StringContent Json(object body) =>
    new(JsonSerializer.Serialize(body), Encoding.UTF8, "application/json");

static string? Field(JsonElement element, string name) =>
    element.TryGetProperty(name, out var value) ? value.ToString() : null;

// v2 token endpoint — credentials go in the body, never in headers.
static async Task<string> GetTokenAsync(HttpClient client)
{
    var payload = JsonSerializer.Serialize(new { username = Username, password = Password });
    var response = await client.PostAsync(
        $"{BaseUrl}/api/security/token/v2",
        new StringContent(payload, Encoding.UTF8, "application/json"));
    response.EnsureSuccessStatusCode();
    return ReadField(await response.Content.ReadAsStringAsync(), "AccessToken");
}

// Transaction and Interactive calls go to the UI server, not BaseUrl.
static async Task<string> GetUiServerAsync(HttpClient client, string token)
{
    using var request = new HttpRequestMessage(
        HttpMethod.Get, $"{BaseUrl}/api/ui/router/v1/?urlType=external");
    request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
    var response = await client.SendAsync(request);
    response.EnsureSuccessStatusCode();
    return ReadField(await response.Content.ReadAsStringAsync(), "Url").TrimEnd('/');
}

// Some middleware answers these two endpoints in XML even when asked for JSON.
static string ReadField(string payload, string field)
{
    try
    {
        var value = JsonDocument.Parse(payload).RootElement.GetProperty(field).GetString();
        if (!string.IsNullOrEmpty(value)) return value;
    }
    catch (Exception ex) when (ex is JsonException or KeyNotFoundException) { }

    var match = System.Text.RegularExpressions.Regex.Match(payload, $"<{field}>([^<]+)</{field}>");
    if (!match.Success)
        throw new InvalidOperationException(
            $"No {field} in response: {payload[..Math.Min(200, payload.Length)]}");
    return match.Groups[1].Value;
}
```

<!-- /tabs -->

### Context Manager / Disposable Usage (Sync)

Structural sketch, not a runnable program — it shows only the lifecycle hooks wrapped around the methods above, and `open_window` / `change_data` / `save` are your own thin wrappers over the REST calls.

> Full runnable version: [Basic Client Class](#basic-client-class)

<!-- tabs -->

#### Python

```python
class InteractiveClient:
    # ... methods above ...

    def __enter__(self):
        self.authenticate()
        self.get_ui_server()
        self.start_session()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.end_session()
        except Exception:
            pass
        return False

# Usage
with InteractiveClient(base_url, username, password) as client:
    window = client.open_window("SalesPricePage")
    window.change_data("description", "New Value")
    window.save()
    window.close()
```

#### C#

```csharp
public class InteractiveClient : IDisposable
{
    // ... fields and methods above ...

    public InteractiveClient Connect()
    {
        AuthenticateAsync().GetAwaiter().GetResult();
        GetUiServerAsync().GetAwaiter().GetResult();
        StartSessionAsync().GetAwaiter().GetResult();
        return this;
    }

    public void Dispose()
    {
        try { EndSessionAsync().GetAwaiter().GetResult(); }
        catch (Exception) { /* ignored */ }
        _http.Dispose();
    }
}

// Usage
using var client = new InteractiveClient(baseUrl, username, password).Connect();
var window = client.OpenWindow("SalesPricePage");
window.ChangeData("description", "New Value");
window.Save();
window.Close();
```

<!-- /tabs -->

### Async Context Manager / IAsyncDisposable (Recommended)

For production code, use async patterns with proper cleanup. Structural sketch — the elided bodies (`# ... get ui_server_url and start session ...`) are the calls shown in full below.

> Full runnable version: [Basic Client Class](#basic-client-class)

<!-- tabs -->

#### Python

```python
import httpx
import logging

logger = logging.getLogger(__name__)

class P21Client:
    def __init__(
        self, base_url: str, username: str,
        password: str, verify_ssl: bool = True,
    ):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.token: dict | None = None
        self.ui_server_url: str | None = None
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                verify=self.verify_ssl,
                timeout=60.0,
                follow_redirects=True
            )
        return self._client

    async def authenticate(self) -> dict:
        url = f"{self.base_url}/api/security/token/v2"
        client = self._get_client()
        response = await client.post(
            url, json={"username": self.username, "password": self.password}
        )
        response.raise_for_status()
        self.token = response.json()
        return self.token

    async def start_session(self) -> None:
        if not self.token:
            await self.authenticate()
        # ... get ui_server_url and start session ...

    async def end_session(self) -> None:
        # ... end session ...
        pass

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self):
        """Async context manager entry - authenticate and start session."""
        await self.authenticate()
        await self.start_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - end session and close client."""
        try:
            await self.end_session()
        except Exception as e:
            logger.debug(f"Session cleanup error (ignored): {e}")
        await self.close()
        return False

# Usage
async with P21Client(base_url, username, password) as client:
    window = await client.open_window(service_name="SalesPricePage")
    await window.change_data("FORM", "description", "New Value", datawindow_name="form")
    await window.save_data()
    await window.close()
```

#### C#

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

public class P21Client : IAsyncDisposable
{
    private readonly string _baseUrl;
    private readonly string _username;
    private readonly string _password;
    private HttpClient? _http;
    private string? _token;
    private string? _uiServerUrl;

    public P21Client(string baseUrl, string username, string password,
                     bool verifySsl = true)
    {
        _baseUrl = baseUrl.TrimEnd('/');
        _username = username;
        _password = password;
        var handler = new HttpClientHandler();
        if (!verifySsl)
            handler.ServerCertificateCustomValidationCallback = (_, _, _, _) => true;

        _http = new HttpClient(handler) { Timeout = TimeSpan.FromSeconds(60) };
    }

    public async Task<JsonElement> AuthenticateAsync()
    {
        var body = JsonSerializer.Serialize(new { username = _username, password = _password });
        var content = new StringContent(body.ToString(), System.Text.Encoding.UTF8, "application/json");
        var response = await _http!.PostAsync($"{_baseUrl}/api/security/token/v2", content);
        response.EnsureSuccessStatusCode();

        using var parsed = JsonDocument.Parse(await response.Content.ReadAsStringAsync());
        _token = parsed["AccessToken"]!.ToString();
        _http.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", _token);
        return parsed;
    }

    public async Task StartSessionAsync()
    {
        if (_token == null)
            await AuthenticateAsync();
        // ... get uiServerUrl and start session ...
    }

    public async Task EndSessionAsync()
    {
        // ... end session ...
    }

    public async ValueTask DisposeAsync()
    {
        try
        {
            await EndSessionAsync();
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"Session cleanup error (ignored): {ex.Message}");
        }

        _http?.Dispose();
        _http = null;
    }
}

// Usage
await using var client = new P21Client(baseUrl, username, password);
await client.AuthenticateAsync();
await client.StartSessionAsync();
var window = await client.OpenWindowAsync(serviceName: "SalesPricePage");
await window.ChangeDataAsync("FORM", "description", "New Value", datawindowName: "form");
await window.SaveDataAsync();
await window.CloseAsync();
```

<!-- /tabs -->

**Key points for async usage:**

1. Use `httpx.AsyncClient` (Python) or `HttpClient` with `async`/`await` (C#)
2. Implement `__aenter__`/`__aexit__` (Python) or `IAsyncDisposable` (C#)
3. Always close the HTTP client on disposal
4. Ignore cleanup errors - session may have timed out
5. Use `async with` (Python) or `await using` (C#) for guaranteed cleanup

---

## Working Example Scripts

See the `examples/python/interactive/` directory:

| Script | Description |
|--------|-------------|
| `01_open_session.py` | Session lifecycle |
| `02_open_window.py` | Open and close windows |
| `03_change_data.py` | Change field values |
| `04_save_and_close.py` | Complete save workflow |
| `05_response_windows.py` | Handle response dialogs |
| `06_complex_workflow.py` | Multi-step example |

---

## Common Windows

| Window Title | Service Name | Purpose |
|--------------|--------------|---------|
| Customer Maintenance | Customer | Customer records |
| Order Entry | Order | Sales orders |
| Invoice Entry | Invoice | Invoices |
| Supplier Maintenance | Supplier | Supplier records |
| Sales Price Page Entry | SalesPricePage | Price pages ([dropdown codes](08-SalesPricePage-Codes.md)) |
| Sales Price Book Entry | SalesPriceBook | Price book maintenance |
| Purchase Order Entry | PurchaseOrder | Purchase orders |
| Inventory Maintenance | InventoryMaster | Inventory items |

### Production & Labor Windows

| Window Title | Service Name | Purpose |
|--------------|--------------|---------|
| Production Order Entry | ProductionOrder | Full production order management |
| Time Entry | TimeEntry | Record labor hours against production orders |
| Time Entry (Service Order) | TimeEntrySO | Record labor hours against service orders |
| Labor Maintenance | Labor | Labor code definitions and rates |
| Labor Process Maintenance | LaborProcess | Labor process templates |
| Job Maintenance | Job | Job CRUD |
| Job Control Maintenance | JobControl | Job sites and contacts |
| Operation Maintenance | Operation | Operation definitions |
| Predefined Routing | PredefinedRouting | Routing templates |
| Assembly Maintenance | Assembly | Assembly definitions |
| Manufacturing Class | ManufacturingClass | Manufacturing classification |
| Shift Maintenance | Shift | Shift definitions |
| Production Order Processing | ProductionOrderProcessing | Process/complete production orders |

> **Pick confirmation MUST be windowed.** A Transaction-API-only confirm produces a shell — the status flips and `qty_confirmed` is set, but `qty_applied` stays 0 and no stock moves. See [Confirming the Pick](12-Production-Labor-API.md#confirming-the-pick-use-the-interactive-api).

See [Production & Labor API](12-Production-Labor-API.md) for detailed field definitions.

---

## Example: Linking Price Page to Price Book

This example shows how to use the SalesPriceBook window to link a price page to a price book. This is a common operation after creating a new price page.

Complete program — session, window, retrieve, tab switch, add row, change, save, read-back, cleanup. It is the reference for every "change a field / add a grid row / save" sequence in this guide.

<!-- tabs -->

#### Python

```python
"""Link a price page to a price book through the SalesPriceBook window."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
PRICE_BOOK_ID = "ACME_BOOK_A"             # the book to load on the FORM tab
PRICE_PAGE_UID = "100198"                 # the page to link — sent as a string
# ---------------------------------------------------------------------------


def get_token(client: httpx.Client) -> str:
    """v2 token endpoint — credentials go in the body, never in headers."""
    r = client.post(
        f"{BASE_URL}/api/security/token/v2",
        json={"username": USERNAME, "password": PASSWORD},
        headers={"Accept": "application/json"},
    )
    r.raise_for_status()
    try:
        return r.json()["AccessToken"]
    except (ValueError, KeyError):  # some middleware answers in XML
        match = re.search(r"<AccessToken>([^<]+)</AccessToken>", r.text)
        if not match:
            raise ValueError(f"No AccessToken in response: {r.text[:200]}") from None
        return match.group(1)


def get_ui_server(client: httpx.Client, token: str) -> str:
    """Transaction and Interactive calls go to the UI server, not BASE_URL."""
    r = client.get(
        f"{BASE_URL}/api/ui/router/v1/?urlType=external",  # trailing slash avoids a 307
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )
    r.raise_for_status()
    try:
        return r.json()["Url"].rstrip("/")
    except (ValueError, KeyError):
        match = re.search(r"<Url>([^<]+)</Url>", r.text)
        if not match:
            raise ValueError(f"No Url in router response: {r.text[:200]}") from None
        return match.group(1).rstrip("/")


with httpx.Client(verify=VERIFY_SSL, timeout=120, follow_redirects=True) as client:
    token = get_token(client)
    ui_server = get_ui_server(client, token)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",       # 2026.1 returns an empty 500 without this
        "Content-Type": "application/json",
    }

    def check(response: httpx.Response, step: str) -> dict:
        """Raise unless the call returned Status 1 (Success)."""
        response.raise_for_status()
        result = response.json()
        status = result.get("Status")
        messages = [m.get("Text") for m in result.get("Messages", [])]
        if status not in (1, "Success"):
            raise RuntimeError(f"{step}: Status={status} {messages}")
        if messages:
            print(f"{step}: {messages}")
        return result

    r = client.post(
        f"{ui_server}/api/ui/interactive/sessions",
        headers=headers,
        json={"ResponseWindowHandlingEnabled": False},
    )
    r.raise_for_status()
    session = r.json()
    print("session:", session.get("Id") or session.get("SessionId"))

    window_id = None
    try:
        # Open by ServiceName — the by-Name and by-Title paths are unreliable.
        r = client.post(
            f"{ui_server}/api/ui/interactive/v2/window",
            headers=headers,
            json={"ServiceName": "SalesPriceBook"},
        )
        r.raise_for_status()
        opened = r.json()
        window_id = opened.get("WindowId") or opened.get("Id")

        # Step 1: retrieve the book by ID on the FORM tab. DatawindowName is
        # required from 25.2 on — the 3-parameter form stopped working.
        check(
            client.put(
                f"{ui_server}/api/ui/interactive/v2/change",
                headers=headers,
                json={
                    "WindowId": window_id,
                    "List": [
                        {
                            "TabName": "FORM",
                            "DatawindowName": "form",
                            "FieldName": "price_book_id",
                            "Value": PRICE_BOOK_ID,
                        }
                    ],
                },
            ),
            "retrieve book",
        )

        # Step 2: switch to the LIST tab (v2 binds PageName, not TabName)
        check(
            client.put(
                f"{ui_server}/api/ui/interactive/v2/tab",
                headers=headers,
                json={"WindowId": window_id, "PageName": "LIST"},
            ),
            "select LIST tab",
        )

        # Step 3: add a new row to the list_detail datawindow
        check(
            client.post(
                f"{ui_server}/api/ui/interactive/v2/row",
                headers=headers,
                json={"WindowId": window_id, "DatawindowName": "list_detail"},
            ),
            "add row",
        )

        # Step 4: set price_page_uid on the new row
        check(
            client.put(
                f"{ui_server}/api/ui/interactive/v2/change",
                headers=headers,
                json={
                    "WindowId": window_id,
                    "List": [
                        {
                            "TabName": "LIST",
                            "DatawindowName": "list_detail",
                            "FieldName": "price_page_uid",
                            "Value": PRICE_PAGE_UID,
                        }
                    ],
                },
            ),
            "set price_page_uid",
        )

        # Step 5: save — the v2 body is the bare window-id GUID as a JSON
        # string, NOT wrapped in an object (a wrapped body 422s).
        check(
            client.put(
                f"{ui_server}/api/ui/interactive/v2/data",
                headers=headers,
                json=window_id,
            ),
            "save",
        )

        # Step 6: read back. /v2/data returns only a varying subset of the
        # window's datawindows, so the LIST tab must be active — and absence
        # still proves nothing. For records that matter, verify out of band
        # too (see "Verifying Writes").
        r = client.get(
            f"{ui_server}/api/ui/interactive/v2/data",
            headers=headers,
            params={"id": window_id},
        )
        r.raise_for_status()
        for dw in r.json():
            if dw.get("Name") == "list_detail":
                print("columns:", dw.get("Columns"))
                for row in dw.get("Data", []):
                    print("row:", row)
    finally:
        if window_id:
            client.delete(
                f"{ui_server}/api/ui/interactive/v2/window",
                headers=headers,
                params={"id": window_id},
            )
        client.delete(f"{ui_server}/api/ui/interactive/sessions", headers=headers)
```

#### C#

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string PriceBookId = "ACME_BOOK_A";              // the book to load on the FORM tab
const string PricePageUid = "100198";                  // the page to link — sent as a string
// ---------------------------------------------------------------------------

var handler = new HttpClientHandler
{
    // Test tenants often present a self-signed cert. Delete this line in production.
    ServerCertificateCustomValidationCallback =
        HttpClientHandler.DangerousAcceptAnyServerCertificateValidator,
};
using var client = new HttpClient(handler) { Timeout = TimeSpan.FromMinutes(2) };
client.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));

var token = await GetTokenAsync(client);
var uiServer = await GetUiServerAsync(client, token);
client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);

var sessionResponse = await client.PostAsync(
    $"{uiServer}/api/ui/interactive/sessions",
    Json(new { ResponseWindowHandlingEnabled = false }));
sessionResponse.EnsureSuccessStatusCode();
using (var session = JsonDocument.Parse(await sessionResponse.Content.ReadAsStringAsync()))
    Console.WriteLine($"session: {Field(session.RootElement, "Id") ?? Field(session.RootElement, "SessionId")}");

string? windowId = null;
try
{
    // Open by ServiceName — the by-Name and by-Title paths are unreliable.
    var openResponse = await client.PostAsync(
        $"{uiServer}/api/ui/interactive/v2/window",
        Json(new { ServiceName = "SalesPriceBook" }));
    openResponse.EnsureSuccessStatusCode();
    using (var opened = JsonDocument.Parse(await openResponse.Content.ReadAsStringAsync()))
        windowId = Field(opened.RootElement, "WindowId") ?? Field(opened.RootElement, "Id");

    // Step 1: retrieve the book by ID on the FORM tab. DatawindowName is
    // required from 25.2 on — the 3-parameter form stopped working.
    await Check(await client.PutAsync(
        $"{uiServer}/api/ui/interactive/v2/change",
        Json(new
        {
            WindowId = windowId,
            List = new[]
            {
                new
                {
                    TabName = "FORM",
                    DatawindowName = "form",
                    FieldName = "price_book_id",
                    Value = PriceBookId,
                },
            },
        })), "retrieve book");

    // Step 2: switch to the LIST tab (v2 binds PageName, not TabName)
    await Check(await client.PutAsync(
        $"{uiServer}/api/ui/interactive/v2/tab",
        Json(new { WindowId = windowId, PageName = "LIST" })), "select LIST tab");

    // Step 3: add a new row to the list_detail datawindow
    await Check(await client.PostAsync(
        $"{uiServer}/api/ui/interactive/v2/row",
        Json(new { WindowId = windowId, DatawindowName = "list_detail" })), "add row");

    // Step 4: set price_page_uid on the new row
    await Check(await client.PutAsync(
        $"{uiServer}/api/ui/interactive/v2/change",
        Json(new
        {
            WindowId = windowId,
            List = new[]
            {
                new
                {
                    TabName = "LIST",
                    DatawindowName = "list_detail",
                    FieldName = "price_page_uid",
                    Value = PricePageUid,
                },
            },
        })), "set price_page_uid");

    // Step 5: save — the v2 body is the bare window-id GUID as a JSON string,
    // NOT wrapped in an object (a wrapped body 422s).
    await Check(await client.PutAsync(
        $"{uiServer}/api/ui/interactive/v2/data",
        new StringContent(JsonSerializer.Serialize(windowId), Encoding.UTF8, "application/json")),
        "save");

    // Step 6: read back. /v2/data returns only a varying subset of the window's
    // datawindows, so the LIST tab must be active — and absence still proves
    // nothing. For records that matter, verify out of band too.
    var dataResponse = await client.GetAsync(
        $"{uiServer}/api/ui/interactive/v2/data?id={windowId}");
    dataResponse.EnsureSuccessStatusCode();

    using var data = JsonDocument.Parse(await dataResponse.Content.ReadAsStringAsync());
    foreach (var dw in data.RootElement.EnumerateArray())
    {
        if (Field(dw, "Name") != "list_detail") continue;
        Console.WriteLine($"columns: {Field(dw, "Columns")}");
        if (dw.TryGetProperty("Data", out var rows))
            foreach (var row in rows.EnumerateArray())
                Console.WriteLine($"row: {row}");
    }
}
finally
{
    if (windowId is not null)
        await client.DeleteAsync($"{uiServer}/api/ui/interactive/v2/window?id={windowId}");

    await client.DeleteAsync($"{uiServer}/api/ui/interactive/sessions");
}

// --- helpers ---------------------------------------------------------------

// Raise unless the call returned Status 1 (Success).
static async Task<JsonDocument> Check(HttpResponseMessage response, string step)
{
    response.EnsureSuccessStatusCode();
    var result = JsonDocument.Parse(await response.Content.ReadAsStringAsync());

    var status = Field(result.RootElement, "Status");
    var messages = new List<string>();
    if (result.RootElement.TryGetProperty("Messages", out var items))
        messages = items.EnumerateArray().Select(m => Field(m, "Text") ?? "").ToList();

    if (status != "1" && status != "Success")
        throw new InvalidOperationException(
            $"{step}: Status={status} {string.Join("; ", messages)}");
    if (messages.Count > 0)
        Console.WriteLine($"{step}: {string.Join("; ", messages)}");

    return result;
}

static StringContent Json(object body) =>
    new(JsonSerializer.Serialize(body), Encoding.UTF8, "application/json");

static string? Field(JsonElement element, string name) =>
    element.TryGetProperty(name, out var value) ? value.ToString() : null;

// v2 token endpoint — credentials go in the body, never in headers.
static async Task<string> GetTokenAsync(HttpClient client)
{
    var payload = JsonSerializer.Serialize(new { username = Username, password = Password });
    var response = await client.PostAsync(
        $"{BaseUrl}/api/security/token/v2",
        new StringContent(payload, Encoding.UTF8, "application/json"));
    response.EnsureSuccessStatusCode();
    return ReadField(await response.Content.ReadAsStringAsync(), "AccessToken");
}

// Transaction and Interactive calls go to the UI server, not BaseUrl.
static async Task<string> GetUiServerAsync(HttpClient client, string token)
{
    using var request = new HttpRequestMessage(
        HttpMethod.Get, $"{BaseUrl}/api/ui/router/v1/?urlType=external");
    request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
    var response = await client.SendAsync(request);
    response.EnsureSuccessStatusCode();
    return ReadField(await response.Content.ReadAsStringAsync(), "Url").TrimEnd('/');
}

// Some middleware answers these two endpoints in XML even when asked for JSON.
static string ReadField(string payload, string field)
{
    try
    {
        var value = JsonDocument.Parse(payload).RootElement.GetProperty(field).GetString();
        if (!string.IsNullOrEmpty(value)) return value;
    }
    catch (Exception ex) when (ex is JsonException or KeyNotFoundException) { }

    var match = System.Text.RegularExpressions.Regex.Match(payload, $"<{field}>([^<]+)</{field}>");
    if (!match.Success)
        throw new InvalidOperationException(
            $"No {field} in response: {payload[..Math.Min(200, payload.Length)]}");
    return match.Groups[1].Value;
}
```

<!-- /tabs -->

**Key points:**

1. Open window by `ServiceName`, not title
2. Retrieve the book first - this loads it into the window
3. Switch to LIST tab before adding/modifying rows
4. Use `add_row('list_detail')` to add a new link row
5. Set `price_page_uid` as a string value
6. Always close the window in a `finally` block

### Price Book Naming and Lookup Strategies

In production P21 environments, price book names are often inconsistent. For example, the same conceptual book might be named differently across environments or suppliers:

- `ACME_BOOK_B`
- `ACME_BOOK_C`
- `ACME_BOOK_D`

**Strategy: Case-Insensitive OData Lookup**

Use `contains()` with case-insensitive matching to find books by partial name. Complete program — OData reads go straight to `BASE_URL`, so no UI-server lookup and no session:

<!-- tabs -->

#### Python

```python
"""Find a price book by trying several partial-name patterns over OData."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
SEARCH_TERMS = ["BOOK_B", "BOOK_C", "BOOK_D"]   # tried in order, first hit wins
# ---------------------------------------------------------------------------


def get_token(client: httpx.Client) -> str:
    """v2 token endpoint — credentials go in the body, never in headers."""
    r = client.post(
        f"{BASE_URL}/api/security/token/v2",
        json={"username": USERNAME, "password": PASSWORD},
        headers={"Accept": "application/json"},
    )
    r.raise_for_status()
    try:
        return r.json()["AccessToken"]
    except (ValueError, KeyError):  # some middleware answers in XML
        match = re.search(r"<AccessToken>([^<]+)</AccessToken>", r.text)
        if not match:
            raise ValueError(f"No AccessToken in response: {r.text[:200]}") from None
        return match.group(1)


with httpx.Client(verify=VERIFY_SSL, timeout=120, follow_redirects=True) as client:
    token = get_token(client)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    book = None
    for term in SEARCH_TERMS:
        filter_expr = (
            f"contains(price_book_id,'{term}') "
            f"and row_status_flag eq 704"
        )
        r = client.get(
            f"{BASE_URL}/odataservice/odata/table/price_book",
            headers=headers,
            params={"$filter": filter_expr, "$select": "price_book_id,description"},
        )
        r.raise_for_status()
        results = r.json().get("value", [])
        print(f"{term}: {len(results)} match(es)")
        if results:
            book = results[0]
            break

    print("resolved book:", book)
```

#### C#

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
// tried in order, first hit wins
string[] searchTerms = ["BOOK_B", "BOOK_C", "BOOK_D"];
// ---------------------------------------------------------------------------

var handler = new HttpClientHandler
{
    // Test tenants often present a self-signed cert. Delete this line in production.
    ServerCertificateCustomValidationCallback =
        HttpClientHandler.DangerousAcceptAnyServerCertificateValidator,
};
using var client = new HttpClient(handler) { Timeout = TimeSpan.FromMinutes(2) };
client.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));

var token = await GetTokenAsync(client);
client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);

JsonElement? book = null;
foreach (var term in searchTerms)
{
    var filterExpr = $"contains(price_book_id,'{term}') and row_status_flag eq 704";
    var url = $"{BaseUrl}/odataservice/odata/table/price_book"
            + $"?$filter={Uri.EscapeDataString(filterExpr)}"
            + $"&$select={Uri.EscapeDataString("price_book_id,description")}";

    var response = await client.GetAsync(url);
    response.EnsureSuccessStatusCode();

    using var payload = JsonDocument.Parse(await response.Content.ReadAsStringAsync());
    var results = payload.RootElement.GetProperty("value");
    Console.WriteLine($"{term}: {results.GetArrayLength()} match(es)");

    if (results.GetArrayLength() > 0)
    {
        book = results[0].Clone();   // Clone: the JsonDocument is disposed below
        break;
    }
}

Console.WriteLine($"resolved book: {book?.ToString() ?? "none"}");

// --- helpers ---------------------------------------------------------------

// v2 token endpoint — credentials go in the body, never in headers.
static async Task<string> GetTokenAsync(HttpClient client)
{
    var payload = JsonSerializer.Serialize(new { username = Username, password = Password });
    var response = await client.PostAsync(
        $"{BaseUrl}/api/security/token/v2",
        new StringContent(payload, Encoding.UTF8, "application/json"));
    response.EnsureSuccessStatusCode();
    return ReadField(await response.Content.ReadAsStringAsync(), "AccessToken");
}

// Some middleware answers the token endpoint in XML even when asked for JSON.
static string ReadField(string payload, string field)
{
    try
    {
        var value = JsonDocument.Parse(payload).RootElement.GetProperty(field).GetString();
        if (!string.IsNullOrEmpty(value)) return value;
    }
    catch (Exception ex) when (ex is JsonException or KeyNotFoundException) { }

    var match = System.Text.RegularExpressions.Regex.Match(payload, $"<{field}>([^<]+)</{field}>");
    if (!match.Success)
        throw new InvalidOperationException(
            $"No {field} in response: {payload[..Math.Min(200, payload.Length)]}");
    return match.Groups[1].Value;
}
```

<!-- /tabs -->

**Strategy: Library-to-Book Resolution**

Price books are organized into libraries. Use the `price_book_x_library` junction table to resolve which books belong to a library. Query shape only — `odata_client.query()` stands in for the OData GET shown in full above:

> Full runnable version: [Price Book Naming and Lookup Strategies](#price-book-naming-and-lookup-strategies)

<!-- tabs -->

#### Python

```python
async def get_books_for_library(
    odata_client: ODataClient,
    library_id: str,
) -> list[dict]:
    """Get all price books linked to a library."""
    links = await odata_client.query(
        "price_book_x_library",
        filter_expr=f"price_library_uid eq {library_id}",
        select="price_book_uid",
    )
    book_uids = [link["price_book_uid"] for link in links]

    books = []
    for uid in book_uids:
        result = await odata_client.query(
            "price_book",
            filter_expr=f"price_book_uid eq {uid} and row_status_flag eq 704",
            select="price_book_id,price_book_uid,description",
        )
        if result:
            books.append(result[0])
    return books
```

#### C#

```csharp
public async Task<List<JsonElement>> GetBooksForLibraryAsync(
    ODataClient odataClient,
    string libraryId)
{
    var links = await odataClient.QueryAsync(
        "price_book_x_library",
        filterExpr: $"price_library_uid eq {libraryId}",
        select: "price_book_uid");

    var bookUids = links.Select(l => l["price_book_uid"]!.ToString()).ToList();
    var books = new List<JsonElement>();

    foreach (var uid in bookUids)
    {
        var result = await odataClient.QueryAsync(
            "price_book",
            filterExpr: $"price_book_uid eq {uid} and row_status_flag eq 704",
            select: "price_book_id,price_book_uid,description");

        if (result.Count > 0)
            books.Add(result[0]);
    }
    return books;
}
```

<!-- /tabs -->

**Strategy: Cache Library-to-Book Mapping**

For bulk operations that link many pages to books, cache the library-to-book mapping to avoid N+1 queries. Caching wrapper only — it makes no calls of its own:

> Full runnable version: [Price Book Naming and Lookup Strategies](#price-book-naming-and-lookup-strategies)

<!-- tabs -->

#### Python

```python
class BookLookupCache:
    """Cache library-to-book mappings for bulk operations."""

    def __init__(self, odata_client: ODataClient):
        self.odata = odata_client
        self._cache: dict[str, list[dict]] = {}

    async def get_books(self, library_id: str) -> list[dict]:
        if library_id not in self._cache:
            self._cache[library_id] = await get_books_for_library(
                self.odata, library_id
            )
        return self._cache[library_id]
```

#### C#

```csharp
public class BookLookupCache
{
    /// <summary>Cache library-to-book mappings for bulk operations.</summary>
    private readonly ODataClient _odata;
    private readonly Dictionary<string, List<JsonElement>> _cache = new();

    public BookLookupCache(ODataClient odataClient)
    {
        _odata = odataClient;
    }

    public async Task<List<JsonElement>> GetBooksAsync(string libraryId)
    {
        if (!_cache.TryGetValue(libraryId, out var books))
        {
            books = await GetBooksForLibraryAsync(_odata, libraryId);
            _cache[libraryId] = books;
        }
        return books;
    }
}
```

<!-- /tabs -->

---

## PurchaseOrder Notepad Writes (Header vs Line)

The PurchaseOrder window exposes **two separate notepad surfaces**, and they use **different tabs and different tools**. Conflating them silently writes to the wrong place with no error.

| | Header notes | Line notes |
|---|---|---|
| **Table** | `po_hdr_notepad` | `po_line_notepad` |
| **Keyed by** | `po_no` only | `po_no` + line |
| **Tab** | "PO Note" tab | Line-notes tab (select a line first) |
| **Datawindow** | `tp_7_dw_7` (`d_update_po_hdr_notes_po_entry`) | `tp_21_dw_21` (`d_update_po_line_notes_po_entry`) |
| **Add / Edit tools** | `cb_add` / `cb_edit` | `cb_add_line` / `cb_edit_line` |

> **Warning — silent misfile:** Both tools are labelled **"Add Note"**, but they are distinct. Using `cb_add_line` (the line tool) when you intend a header note **files the note against the currently-selected line** (line 1 after a fresh load) — a perfectly valid *line* note. Every call returns HTTP 200 / `Status: 1` including the save (`savesucceeded`), and the row simply never appears in `po_hdr_notepad`. Symptom: "header note write succeeds but the note is never there." Verified against P21 25.2; reproduced end-to-end July 2026 (misfiled note landed in `tp_21_dw_21` / `po_line_notepad` bound to line 1).

> **Requirement — `ResponseWindowHandlingEnabled: true`:** Both add tools open the **Notepad Entry** popup (`w_notepad_response_lite`), which is a response window. The session must be created with `"ResponseWindowHandlingEnabled": true`. With `false`, the tool call fails with HTTP 400: `"Unexpected response window: Notepad Entry Window. Window class: w_notepad_response_lite"`.

> **Tip:** Identify the target tab by its **datawindow name** in the window state (`GET /api/ui/interactive/v2/window?id={windowId}`), not by counting tabs in the UI — the window has 37 tab pages, many disabled or hidden (see [tab identification](#7-transaction-api-service-definition)). On the servers tested, the PO Notes tab is `TABPAGE_7` and the PO Line Notes tab is `TABPAGE_21`, matching the Transaction API definition.

### The Notepad Entry Popup

Both recipes go through the same popup. Running the add tool returns `Status: 3` (Blocked) with a `windowopened` event carrying the popup's window ID:

```json
{
    "Status": 3,
    "Events": [
        {"Name": "windowopened", "Data": [{"Key": "windowid", "Value": "{popupWindowId}"}]}
    ]
}
```

The popup (`w_notepad_response_lite`, title "Notepad Entry Window") is tabless and has three datawindows:

| Datawindow | Purpose |
|------------|---------|
| `_dw_hdr` | The note itself — `topic`, `note`, plus prefilled `po_no`, dates, `mandatory`, `delete_flag`. **The line-note variant additionally carries `line_no` and `item_id`** — check for these columns to confirm which surface you opened |
| `_dw_areas` | Available P21 areas the note can appear in (e.g., "Purchase Order Entry", "Purchase Order Receipts") |
| `_dw_select` | Areas currently selected |

Popup tools: `cb_select`, `cb_select_all`, `cb_deselect`, `cb_deselect_all`, `cb_ok`, `cb_cancel`.

Changes to the popup use the **popup's** window ID with `TabName: null` (it is tabless). `cb_ok` closes the popup (a `close` event with `is_response: true`) and stages the new row into the parent grid — the new `note_id` is already assigned and visible in the parent window's data at this point, **before** saving.

### Recipe: Add a Header Note

1. Start the session with `"ResponseWindowHandlingEnabled": true`, open the `PurchaseOrder` window, and load the PO (change `po_no` on `TABPAGE_1`/`tp_1_dw_1`).
2. Switch to the **PO Notes** tab (`tp_7_dw_7`):

   ```json
   PUT /api/ui/interactive/v2/tab
   {"WindowId": "{windowId}", "PageName": "TABPAGE_7"}
   ```

3. Run the **header** add tool — returns `Status: 3` with the popup's window ID in the `windowopened` event:

   ```json
   POST /api/ui/interactive/v2/tools
   {"WindowId": "{windowId}", "ToolName": "cb_add", "ToolText": "Add Note"}
   ```

4. In the popup, set `topic` and `note` on `_dw_hdr` (note `TabName: null` and the **popup's** window ID):

   ```json
   PUT /api/ui/interactive/v2/change
   {
       "WindowId": "{popupWindowId}",
       "List": [
           {"TabName": null, "DatawindowName": "_dw_hdr", "FieldName": "topic", "Value": "MY TOPIC"},
           {"TabName": null, "DatawindowName": "_dw_hdr", "FieldName": "note", "Value": "Note text"}
       ]
   }
   ```

5. Run `cb_select_all` then `cb_ok` on the popup window ID (`POST /api/ui/interactive/v2/tools`). The popup closes and the staged row (with its new `note_id`) appears in `tp_7_dw_7`.
6. Save the window (`PUT /api/ui/interactive/v2/data`) and [verify the write](#verifying-writes-dont-trust-save-status-alone).

Complete program — the whole sequence above, including the response-window handshake and a read-back through a **fresh window load** (a reload proves the row came from the database; the staged row in the window you just saved does not):

<!-- tabs -->

#### Python

```python
"""Add a header note to a purchase order through the Notepad Entry popup."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
PO_NO = "123456"                          # existing purchase order to annotate
TOPIC = "API NOTE"                        # po_hdr_notepad.topic (required)
NOTE_TEXT = "Written through the Interactive API."   # po_hdr_notepad.note
# ---------------------------------------------------------------------------


def get_token(client: httpx.Client) -> str:
    """v2 token endpoint — credentials go in the body, never in headers."""
    r = client.post(
        f"{BASE_URL}/api/security/token/v2",
        json={"username": USERNAME, "password": PASSWORD},
        headers={"Accept": "application/json"},
    )
    r.raise_for_status()
    try:
        return r.json()["AccessToken"]
    except (ValueError, KeyError):  # some middleware answers in XML
        match = re.search(r"<AccessToken>([^<]+)</AccessToken>", r.text)
        if not match:
            raise ValueError(f"No AccessToken in response: {r.text[:200]}") from None
        return match.group(1)


def get_ui_server(client: httpx.Client, token: str) -> str:
    """Transaction and Interactive calls go to the UI server, not BASE_URL."""
    r = client.get(
        f"{BASE_URL}/api/ui/router/v1/?urlType=external",  # trailing slash avoids a 307
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )
    r.raise_for_status()
    try:
        return r.json()["Url"].rstrip("/")
    except (ValueError, KeyError):
        match = re.search(r"<Url>([^<]+)</Url>", r.text)
        if not match:
            raise ValueError(f"No Url in router response: {r.text[:200]}") from None
        return match.group(1).rstrip("/")


with httpx.Client(verify=VERIFY_SSL, timeout=120, follow_redirects=True) as client:
    token = get_token(client)
    ui_server = get_ui_server(client, token)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",       # 2026.1 returns an empty 500 without this
        "Content-Type": "application/json",
    }

    def post(path: str, body: object) -> dict:
        r = client.post(f"{ui_server}{path}", headers=headers, json=body)
        r.raise_for_status()
        return r.json()

    def put(path: str, body: object) -> dict:
        r = client.put(f"{ui_server}{path}", headers=headers, json=body)
        r.raise_for_status()
        return r.json()

    def popup_window_id(result: dict) -> str | None:
        """Pull the popup's ID out of the windowopened event."""
        for event in result.get("Events", []):
            if event.get("Name") == "windowopened":
                for kv in event.get("Data", []):
                    if str(kv.get("Key", "")).lower() == "windowid":
                        return kv.get("Value")
        return None

    def open_po() -> str:
        """Open PurchaseOrder and load PO_NO on the header tab."""
        opened = post("/api/ui/interactive/v2/window", {"ServiceName": "PurchaseOrder"})
        wid = opened.get("WindowId") or opened.get("Id")
        loaded = put(
            "/api/ui/interactive/v2/change",
            {
                "WindowId": wid,
                "List": [
                    {
                        "TabName": "TABPAGE_1",
                        "DatawindowName": "tp_1_dw_1",
                        "FieldName": "po_no",
                        "Value": PO_NO,
                    }
                ],
            },
        )
        # A PO that doesn't exist loads as Status 2 with an empty window on
        # 26.1 ("Enter a valid ID or leave ID blank.") — stop here, not later.
        if loaded.get("Status") not in (1, "Success"):
            raise RuntimeError(f"load {PO_NO}: {loaded}")
        return wid

    # The Notepad Entry popup is a response window: with
    # ResponseWindowHandlingEnabled false, cb_add fails with HTTP 400
    # "Unexpected response window ... w_notepad_response_lite".
    r = client.post(
        f"{ui_server}/api/ui/interactive/sessions",
        headers=headers,
        json={"ResponseWindowHandlingEnabled": True},
    )
    r.raise_for_status()
    session = r.json()
    print("session:", session.get("Id") or session.get("SessionId"))

    window_id = None
    verify_id = None
    try:
        window_id = open_po()

        # PO Notes tab — identified by its datawindow (tp_7_dw_7), not by
        # counting tabs in the UI.
        put(
            "/api/ui/interactive/v2/tab",
            {"WindowId": window_id, "PageName": "TABPAGE_7"},
        )

        # The HEADER add tool. cb_add_line is the line-note tool and would
        # file the note against the selected line instead — silently, with
        # every call still returning Status 1.
        result = post(
            "/api/ui/interactive/v2/tools",
            {"WindowId": window_id, "ToolName": "cb_add", "ToolText": "Add Note"},
        )
        popup_id = popup_window_id(result)   # Status 3 (Blocked) + windowopened
        if not popup_id:
            raise RuntimeError(f"no Notepad Entry popup opened: {result}")
        print("popup:", popup_id)

        # The popup is tabless — TabName must be null, and the window ID is
        # the POPUP's, not the parent's.
        put(
            "/api/ui/interactive/v2/change",
            {
                "WindowId": popup_id,
                "List": [
                    {
                        "TabName": None,
                        "DatawindowName": "_dw_hdr",
                        "FieldName": "topic",
                        "Value": TOPIC,
                    },
                    {
                        "TabName": None,
                        "DatawindowName": "_dw_hdr",
                        "FieldName": "note",
                        "Value": NOTE_TEXT,
                    },
                ],
            },
        )

        post("/api/ui/interactive/v2/tools",
             {"WindowId": popup_id, "ToolName": "cb_select_all"})
        post("/api/ui/interactive/v2/tools",
             {"WindowId": popup_id, "ToolName": "cb_ok"})

        # Save — the v2 body is the bare window-id GUID as a JSON string.
        saved = put("/api/ui/interactive/v2/data", window_id)
        print("save status:", saved.get("Status"))

        # Read-back through a fresh load. A save reports savesucceeded for
        # tp_1_dw_1 whether or not the child row persisted, so reopen the PO.
        client.delete(
            f"{ui_server}/api/ui/interactive/v2/window",
            headers=headers,
            params={"id": window_id},
        )
        window_id = None

        verify_id = open_po()
        put("/api/ui/interactive/v2/tab",
            {"WindowId": verify_id, "PageName": "TABPAGE_7"})
        r = client.get(
            f"{ui_server}/api/ui/interactive/v2/data",
            headers=headers,
            params={"id": verify_id},
        )
        r.raise_for_status()
        for dw in r.json():
            if dw.get("Name") == "tp_7_dw_7":
                print("columns:", dw.get("Columns"))
                for row in dw.get("Data", []):
                    print("note row:", row)
    finally:
        for wid in (window_id, verify_id):
            if wid:
                client.delete(
                    f"{ui_server}/api/ui/interactive/v2/window",
                    headers=headers,
                    params={"id": wid},
                )
        client.delete(f"{ui_server}/api/ui/interactive/sessions", headers=headers)
```

#### C#

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string PoNo = "123456";                          // existing purchase order to annotate
const string Topic = "API NOTE";                       // po_hdr_notepad.topic (required)
const string NoteText = "Written through the Interactive API.";   // po_hdr_notepad.note
// ---------------------------------------------------------------------------

var handler = new HttpClientHandler
{
    // Test tenants often present a self-signed cert. Delete this line in production.
    ServerCertificateCustomValidationCallback =
        HttpClientHandler.DangerousAcceptAnyServerCertificateValidator,
};
using var client = new HttpClient(handler) { Timeout = TimeSpan.FromMinutes(2) };
client.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));

var token = await GetTokenAsync(client);
var uiServer = await GetUiServerAsync(client, token);
client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);

// The Notepad Entry popup is a response window: with
// ResponseWindowHandlingEnabled false, cb_add fails with HTTP 400
// "Unexpected response window ... w_notepad_response_lite".
var createResponse = await client.PostAsync(
    $"{uiServer}/api/ui/interactive/sessions",
    Json(new { ResponseWindowHandlingEnabled = true }));
createResponse.EnsureSuccessStatusCode();
using (var session = JsonDocument.Parse(await createResponse.Content.ReadAsStringAsync()))
    Console.WriteLine($"session: {Field(session.RootElement, "Id") ?? Field(session.RootElement, "SessionId")}");

string? windowId = null;
string? verifyId = null;
try
{
    windowId = await OpenPoAsync();

    // PO Notes tab — identified by its datawindow (tp_7_dw_7), not by counting
    // tabs in the UI.
    await Put("/api/ui/interactive/v2/tab",
        new { WindowId = windowId, PageName = "TABPAGE_7" });

    // The HEADER add tool. cb_add_line is the line-note tool and would file the
    // note against the selected line instead — silently, with every call still
    // returning Status 1.
    var result = await Post("/api/ui/interactive/v2/tools",
        new { WindowId = windowId, ToolName = "cb_add", ToolText = "Add Note" });

    var popupId = PopupWindowId(result);   // Status 3 (Blocked) + windowopened
    if (popupId is null)
        throw new InvalidOperationException($"no Notepad Entry popup opened: {result}");
    Console.WriteLine($"popup: {popupId}");

    // The popup is tabless — TabName must be null, and the window ID is the
    // POPUP's, not the parent's.
    await Put("/api/ui/interactive/v2/change", new
    {
        WindowId = popupId,
        List = new[]
        {
            new
            {
                TabName = (string?)null,
                DatawindowName = "_dw_hdr",
                FieldName = "topic",
                Value = Topic,
            },
            new
            {
                TabName = (string?)null,
                DatawindowName = "_dw_hdr",
                FieldName = "note",
                Value = NoteText,
            },
        },
    });

    await Post("/api/ui/interactive/v2/tools",
        new { WindowId = popupId, ToolName = "cb_select_all" });
    await Post("/api/ui/interactive/v2/tools",
        new { WindowId = popupId, ToolName = "cb_ok" });

    // Save — the v2 body is the bare window-id GUID as a JSON string.
    var saved = await Put("/api/ui/interactive/v2/data", windowId);
    Console.WriteLine($"save status: {Field(saved, "Status")}");

    // Read-back through a fresh load. A save reports savesucceeded for
    // tp_1_dw_1 whether or not the child row persisted, so reopen the PO.
    await client.DeleteAsync($"{uiServer}/api/ui/interactive/v2/window?id={windowId}");
    windowId = null;

    verifyId = await OpenPoAsync();
    await Put("/api/ui/interactive/v2/tab",
        new { WindowId = verifyId, PageName = "TABPAGE_7" });

    var dataResponse = await client.GetAsync(
        $"{uiServer}/api/ui/interactive/v2/data?id={verifyId}");
    dataResponse.EnsureSuccessStatusCode();

    using var data = JsonDocument.Parse(await dataResponse.Content.ReadAsStringAsync());
    foreach (var dw in data.RootElement.EnumerateArray())
    {
        if (Field(dw, "Name") != "tp_7_dw_7") continue;
        Console.WriteLine($"columns: {Field(dw, "Columns")}");
        if (dw.TryGetProperty("Data", out var rows))
            foreach (var row in rows.EnumerateArray())
                Console.WriteLine($"note row: {row}");
    }
}
finally
{
    foreach (var id in new[] { windowId, verifyId })
        if (id is not null)
            await client.DeleteAsync($"{uiServer}/api/ui/interactive/v2/window?id={id}");

    await client.DeleteAsync($"{uiServer}/api/ui/interactive/sessions");
}

// --- helpers ---------------------------------------------------------------

async Task<JsonElement> Post(string path, object body)
{
    var response = await client.PostAsync($"{uiServer}{path}", Json(body));
    response.EnsureSuccessStatusCode();
    using var document = JsonDocument.Parse(await response.Content.ReadAsStringAsync());
    return document.RootElement.Clone();
}

async Task<JsonElement> Put(string path, object body)
{
    var response = await client.PutAsync($"{uiServer}{path}", Json(body));
    response.EnsureSuccessStatusCode();
    using var document = JsonDocument.Parse(await response.Content.ReadAsStringAsync());
    return document.RootElement.Clone();
}

// Open PurchaseOrder and load PoNo on the header tab.
async Task<string> OpenPoAsync()
{
    var opened = await Post("/api/ui/interactive/v2/window", new { ServiceName = "PurchaseOrder" });
    var id = Field(opened, "WindowId") ?? Field(opened, "Id")
             ?? throw new InvalidOperationException($"no window id in open response: {opened}");

    var loaded = await Put("/api/ui/interactive/v2/change", new
    {
        WindowId = id,
        List = new[]
        {
            new
            {
                TabName = "TABPAGE_1",
                DatawindowName = "tp_1_dw_1",
                FieldName = "po_no",
                Value = PoNo,
            },
        },
    });

    // A PO that doesn't exist loads as Status 2 with an empty window on 26.1
    // ("Enter a valid ID or leave ID blank.") — stop here, not later.
    var status = Field(loaded, "Status");
    if (status != "1" && status != "Success")
        throw new InvalidOperationException($"load {PoNo}: Status={status}");
    return id;
}

// Pull the popup's ID out of the windowopened event.
static string? PopupWindowId(JsonElement result)
{
    if (!result.TryGetProperty("Events", out var events)) return null;

    foreach (var evt in events.EnumerateArray())
    {
        if (Field(evt, "Name") != "windowopened") continue;
        if (!evt.TryGetProperty("Data", out var data)) continue;

        foreach (var kv in data.EnumerateArray())
            if (string.Equals(Field(kv, "Key"), "windowid", StringComparison.OrdinalIgnoreCase))
                return Field(kv, "Value");
    }
    return null;
}

static StringContent Json(object body) =>
    new(JsonSerializer.Serialize(body), Encoding.UTF8, "application/json");

static string? Field(JsonElement element, string name) =>
    element.TryGetProperty(name, out var value) ? value.ToString() : null;

// v2 token endpoint — credentials go in the body, never in headers.
static async Task<string> GetTokenAsync(HttpClient client)
{
    var payload = JsonSerializer.Serialize(new { username = Username, password = Password });
    var response = await client.PostAsync(
        $"{BaseUrl}/api/security/token/v2",
        new StringContent(payload, Encoding.UTF8, "application/json"));
    response.EnsureSuccessStatusCode();
    return ReadField(await response.Content.ReadAsStringAsync(), "AccessToken");
}

// Transaction and Interactive calls go to the UI server, not BaseUrl.
static async Task<string> GetUiServerAsync(HttpClient client, string token)
{
    using var request = new HttpRequestMessage(
        HttpMethod.Get, $"{BaseUrl}/api/ui/router/v1/?urlType=external");
    request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
    var response = await client.SendAsync(request);
    response.EnsureSuccessStatusCode();
    return ReadField(await response.Content.ReadAsStringAsync(), "Url").TrimEnd('/');
}

// Some middleware answers these two endpoints in XML even when asked for JSON.
static string ReadField(string payload, string field)
{
    try
    {
        var value = JsonDocument.Parse(payload).RootElement.GetProperty(field).GetString();
        if (!string.IsNullOrEmpty(value)) return value;
    }
    catch (Exception ex) when (ex is JsonException or KeyNotFoundException) { }

    var match = System.Text.RegularExpressions.Regex.Match(payload, $"<{field}>([^<]+)</{field}>");
    if (!match.Success)
        throw new InvalidOperationException(
            $"No {field} in response: {payload[..Math.Min(200, payload.Length)]}");
    return match.Groups[1].Value;
}
```

<!-- /tabs -->

### Recipe: Add a Line Note

1. Start the session with `"ResponseWindowHandlingEnabled": true`, open the `PurchaseOrder` window, and load the PO.
2. **Select the target line row** in the line grid (`tp_17_dw_17`):

   ```json
   PUT /api/ui/interactive/v2/row
   {"WindowId": "{windowId}", "DatawindowName": "tp_17_dw_17", "Row": 0}
   ```

3. Switch to the **PO Line Notes** tab (`tp_21_dw_21`, `PageName: "TABPAGE_21"`).
4. Run the **line** add tool:

   ```json
   POST /api/ui/interactive/v2/tools
   {"WindowId": "{windowId}", "ToolName": "cb_add_line", "ToolText": "Add Note"}
   ```

5. Complete the Notepad Entry popup exactly as in the header recipe (`topic`/`note` on `_dw_hdr` with `TabName: null`, then `cb_select_all`, `cb_ok`) — the popup's `_dw_hdr` shows which `line_no`/`item_id` the note will attach to. Save and verify.

---

## Sales Order Notepad Writes (Header vs Line)

The **Order window has the same two notepad surfaces** as PurchaseOrder, drivable with the same Notepad Entry popup mechanics ([above](#the-notepad-entry-popup)) — verified end-to-end on 26.1 (August 2026), both notes confirmed in the database. This matters doubly because the Transaction API's note surface on `Order` is **entirely closed** ([03 § Limitations](03-Transaction-API.md#limitations)): this is the working path.

| | Header note | Line note |
|---|---|---|
| **Table** | `oe_hdr_notepad` | `oe_line_notepad` |
| **Tab (`PageName`)** | `HDR_NOTE` | `LINE_NOTE` |
| **Add tool** | `hdr_note&&cb_addnote` | `line_note&&cb_addnote` |
| **Before the tool** | nothing extra | select the target line row first |

Two Order-window differences from the PurchaseOrder recipe:

- **Tool names are namespaced** — `{datawindow}&&{button}` (`hdr_note&&cb_addnote`), not the bare `cb_add`/`cb_add_line` of the PO window. Same silent-misfile warning applies: both tools are labelled "Add Note".
- **The tool list is tab-scoped and accumulates.** `GET /v2/tools` right after loading the order does **not** list the note tools — they appear only once their tab has been selected (the list grows as tabs are visited). Select the tab first, then look for the tool; a missing tool usually means a missing tab-select, not a missing feature.

Verified sequence (session created with `"ResponseWindowHandlingEnabled": true`):

1. Open `{"ServiceName": "Order"}`, load the order (`TabName: "TABPAGE_1"`, `DatawindowName: "order"`, `order_no`). Mandatory customer notes surface as `Messages` text on this load — they do not block it.
2. **Header note:** select the tab — `PUT /v2/tab` `{"PageName": "HDR_NOTE"}` — then run `hdr_note&&cb_addnote`. Returns `Status: 3` with the Notepad Entry popup's window ID in the `windowopened` event.
3. **Line note instead:** select the items tab (`PageName: "TP_ITEMS"`), pick the row — `PUT /v2/row` `{"DatawindowName": "items", "Row": 2}` — then select `LINE_NOTE` and run `line_note&&cb_addnote`. The note attaches to the selected row's line (confirmed: `oe_line_notepad.line_no = 2`).
4. Complete the popup exactly as in the [PO recipe](#the-notepad-entry-popup): `topic`/`note` on `_dw_hdr` with `TabName: null` and the **popup's** window ID, then `cb_select_all`, `cb_ok`.
5. Save (`PUT /v2/data`, bare window-GUID body) — `savesucceeded` — and read back.

> **Read notes back through OData, not `/transaction/get`.** The Transaction API read of the same order returns the header note in `HDR_NOTE.hdr_note`, but the **line note never appears** in `LINE_NOTE.line_note` (the element comes back empty). Query the tables directly:
>
> ```http
> GET /odataservice/odata/table/oe_hdr_notepad?$filter=order_no eq '1519092'
> GET /odataservice/odata/table/oe_line_notepad?$filter=order_no eq '1519092'
> ```

## Standalone Notepad Windows (Item/Customer/Supplier)

The standalone notepad services (`ItemNotepad`, `CustomerNotepad`, `SupplierNotepad`, `VendorNotepad`) are **closed to the Transaction API** — their mandatory "where does this note display" area selector is a drag-and-drop control ([03 § Limitations](03-Transaction-API.md#limitations)). The Interactive API opens them: **the same picker is exposed as ordinary button tools** — `cb_select`, `cb_selectall`, `cb_deselect`, `cb_deselectall`, present in the tool list from the moment the window opens.

Verified end-to-end on `ItemNotepad` (26.1, August 2026; note confirmed in the `note` table):

1. Open `{"ServiceName": "ItemNotepad"}` (session with `ResponseWindowHandlingEnabled: true`).
2. Fill the header on `TabName: "TABPAGE_1"`, `DatawindowName: "tp_1_dw_1"` — `inv_mast_item_id`, `topic`, `note` (plus `mandatory`, activation/expiration dates as needed).
3. Select the areas tab (`PageName: "TABPAGE_17"`) and run **`cb_selectall`** (`POST /v2/tools`) — this selects **every** area the note can display in. To pick a single area, select its row in the Available Areas grid (`tp_17_dw_dragdrop`) first and run `cb_select` (not separately verified).
4. Save (`PUT /v2/data`, bare window-GUID body) — `savesucceeded`.

`CustomerNotepad` / `SupplierNotepad` / `VendorNotepad` publish the identical element shape (header form + `TABPAGE_17` area pair) and the same tools; only the header key field differs (`customer_id` / `supplier_id` / `vendor_id`). They have not been separately exercised.

## Sales Order Entry with Assembly Lines

Use the Interactive API to create a sales order when a line is an **assembly** that should explode into components and/or spawn a **production order**. The Transaction API cannot do this: entering an assembly item fires an *"add as assembly?"* prompt, and the stateless API auto-answers **No**, killing the explode (see [Order Service Gotchas](03-Transaction-API.md#order-service-gotchas)). Verified end-to-end: interactive order entry created a sales order whose assembly line (`oe_line.assembly = 'P'`) auto-linked to a new production order.

The flow (session started with `ResponseWindowHandlingEnabled: true`):

1. **Header** on `TabName: "TABPAGE_1"`, `DatawindowName: "order"` — set `quote` (`OFF` = real order, `ON` = quote), `sales_loc_id`, `source_loc_id`, `customer_id`, `ship_to_id`, `contact_id`, `order_date`, `requested_date`, `po_no`, `taker`.
   - **`taker` defaults to the API user** — override it with the real salesperson or the order is attributed to the service account.
   - **Setting the dates fires a date-cascade prompt** (`w_response_common`, buttons `cb_ok`/`cb_cancel`) *even on a brand-new order*. Answer **`cb_ok`** via the popup's window ID (see [Response Windows](#response-windows)).
2. **Lines**: `change_tab` to `TP_ITEMS`, then set fields on the **existing** `items` row (`DatawindowName: "items"` — do **not** add a row for the first line):
   - Setting `oe_order_item_id` on an assembly item fires the **assembly prompt** (buttons `cb_1` = Yes / `cb_2` = No / `cb_3` = Cancel). Answer **`cb_1`** to explode the assembly / link a production order.
   - Then set `unit_quantity`.
   - **Do NOT use the quickmode datawindow** (`d_dw_quickmode_*`) to enter lines — it **bypasses the assembly prompt entirely**, and the line lands without the explode.
3. **Save**, answering any follow-on prompts with their proceed button. Read the generated `order_no` from the window data (`GET /v2/data`).

Assembly behavior is item-level (`assembly_hdr`): `production_order_processing` `Y` = production-order assembly / `N` = kit; `auto_create_prod_order` `Y` = auto-create and link the production order at save. On the saved order, `oe_line.assembly` codes: `B` = kit parent, `N` = component, `P` = production-order line, `S` = build-to-stock allocation. The production-order link is `prod_order_line_link` (`transaction_uid = oe_line.oe_line_uid`, `trans_type = 'O'`). See the [Production & Labor API guide](12-Production-Labor-API.md) for the full production lifecycle.

> **Credit:** [Alex Westemeier](https://github.com/AWestemeier) — flow and gotchas verified end-to-end on a play environment (June 2026).

---

## Data Structures Reference

### Result Object

Every action returns a `Result` with these properties:

| Property | Type | Description |
|----------|------|-------------|
| `Status` | int | `0` (None), `1` (Success), `2` (Failure), `3` (Blocked) |
| `Messages` | array | List of messages triggered by the action |
| `Events` | array | List of events that occurred (fields enabled/disabled, windows opened, keys generated, etc.) |

**Status values** (from `ResultStatus` enum):

| Status | Value | Meaning | Action |
|--------|-------|---------|--------|
| `None` | `0` | No action needed | Status couldn't be determined |
| `Success` | `1` | Action completed | Continue to next step |
| `Failure` | `2` | Action failed | Check `Messages` for details |
| `Blocked` | `3` | Session blocked by dialog | Check `Events` for `windowopened`, handle the response window |

### Messages

Each message has a `Text` and a `Type`:

| MessageType | Description |
|-------------|-------------|
| `Information` | Informational (no action needed) |
| `Warning` | Warning (may need attention) |
| `Error` | Error (action failed) |

### Events

Events describe every discrete action the application took. Key event names:

| Event Name | Description |
|------------|-------------|
| `windowopened` | A response window was opened — `Data` contains the window ID |
| `keygenerated` | A new key was generated (e.g., new record ID on save) |

> **Tip:** For less granular information, query the full window state with `GET /api/ui/interactive/v2/window?id={windowId}` after an action instead of parsing individual events.

### Window Definition

When you open or GET a window, the response includes structural information:

| Property | Description |
|----------|-------------|
| `Id` | Window GUID |
| `Title` | Window title |
| `TabPageList` | Array of tabs — each with `Name`, `Text`, and `Enabled` |
| `Datawindows` | Map of datawindow definitions |

Each **datawindow definition** contains:

| Property | Description |
|----------|-------------|
| `Name` | Datawindow name (used in change/row requests) |
| `ParentPage` | Tab this datawindow belongs to |
| `Style` | `List` (grid) or `Form` |
| `Fields` | Map of field definitions |

Each **field definition** contains:

| Property | Description |
|----------|-------------|
| `Name` | Field name (used in change requests) |
| `Label` | Display label |
| `Enabled` | Whether the field is editable |
| `DataType` | `Char`, `Long`, `Datetime`, `Decimal`, `Number`, or `Time` |

### Window Data

`GET /api/ui/interactive/v2/data?id={windowId}` returns data for each datawindow on the active surface:

| Property | Description |
|----------|-------------|
| `Name` | Datawindow name |
| `FullName` | Fully qualified name |
| `ActiveRow` | Currently selected row index |
| `TotalRows` | Number of rows |
| `Columns` | Array of column names |
| `Data` | Array of arrays — each inner array is a row of values |

---

## Self-Documenting Help Endpoints

The API server exposes built-in help pages that list all available endpoints and their parameters:

```http
https://{ui-server-host}/api/ui/interactive/sessions/help
https://{ui-server-host}/ui/interactive/v1/help
```

> **Tip:** These are useful for discovering endpoints and verifying parameter names on your specific P21 version.

---

## V1 REST Endpoint Reference (SDK Internal)

The C# SDK (`P21.UI.Service.Client`) calls these V1 REST endpoints internally. They are listed here for reference — the V2 endpoints documented [above](#window-operations-v2) are recommended for direct REST access. Understanding the V1 paths is useful when debugging SDK behavior or reading network traces.

| Method | V1 Endpoint | Purpose |
|--------|-------------|---------|
| POST | `/uiserver0/ui/common/v1/sessions` | Create session |
| DELETE | `/uiserver0/ui/common/v1/sessions` | End session |
| POST | `/uiserver0/ui/interactive/v1/window` | Open window |
| GET | `/uiserver0/ui/interactive/v1/window` | Get state |
| DELETE | `/uiserver0/ui/interactive/v1/window` | Close window |
| PUT | `/uiserver0/ui/interactive/v1/change` | Change data |
| PUT | `/uiserver0/ui/interactive/v1/data` | Save data |
| GET | `/uiserver0/ui/interactive/v1/data` | Get data |
| DELETE | `/uiserver0/ui/interactive/v1/data` | Clear data |
| PUT | `/uiserver0/ui/interactive/v1/tab` | Change tab |
| GET | `/uiserver0/ui/interactive/v1/tools` | Get tools |
| POST | `/uiserver0/ui/interactive/v1/tools` | Run tool |
| POST | `/uiserver0/ui/interactive/v1/row` | Add row |
| PUT | `/uiserver0/ui/interactive/v1/row` | Change row |

> **Note:** The `uiserver0` prefix is the UI server instance name assigned during routing. Your environment may use a different instance name — check `GET /api/ui/router/v1?urlType=external` to obtain the correct base URL.

---

## Verifying Writes (Don't Trust Save Status Alone)

An Interactive save (`PUT /api/ui/interactive/v2/data`) can return `Status: 1` with a `savesucceeded` event for the **primary** datawindow (`tp_1_dw_1`) even when a change staged into a **child grid** on another tab never actually persisted. The overall call looks fully successful.

Why status alone is not a reliable "it persisted" signal:

- `savesucceeded` / `Status` reflect the main-window save, not necessarily every sub-record you touched. Verified live: a save that persisted a `po_hdr_notepad` child row still reported `savesucceeded` only for `tp_1_dw_1` — and a save whose note had silently misfiled to the *wrong* table looked byte-for-byte identical (`Status: 1`, `savesucceeded`).
- Status-code semantics differ across P21 versions (e.g., an empty/not-found record surfaces differently on 25.2 vs 26.1), so status alone is not portable.
- The **save response** does not include the new auto-generated key (e.g., `note_id`) for an inserted child row. For notepad rows the key is visible earlier — it appears in the parent grid's data (`GET /api/ui/interactive/v2/window?id=`) as soon as the popup commits — but only a read-back proves it actually reached the database.
- **`GET /v2/data` is not a reliable read-back either.** It returns a *subset* of the window's datawindows, and which ones appear **varies between calls** — verified on 26.1.5894.1, where the same window returned `tp_1_dw_1` + `tp_17_dw_17` after a load but `ship_to` + `tp_17_dw_17` after a change, omitting `tp_1_dw_1` entirely. A datawindow's absence tells you nothing about its field's value. Activate the field's tab first to force its datawindow into the response, or verify out-of-band as below.

**Recommendation:** for records where correctness matters, **read the record back after writing** — out-of-band, not via `/v2/data` — and confirm it exists before treating the write as done — e.g., `POST /api/v2/transaction/get` for the target DataElement (see [Transaction API](03-Transaction-API.md)), or an OData/report read where the table is exposed. Verified live: after the header-note recipe, `transaction/get` keyed by `po_no` returned the `TABPAGE_7.tp_7_dw_7` row with its server-generated `note_id`, and after the misfile scenario it proved the note was in `tp_21_dw_21` instead. This is version-proof, unlike trusting the save's status.

---

## Best Practices

1. **Always end sessions** - Use context managers or try/finally
2. **Handle response windows** - Check for blocked status
3. **Change tabs before fields** - Tab selection required for REST
4. **Find field names in P21** - Use SQL Information dialog
5. **Save before close** - Unsaved changes are lost
6. **Keep sessions short** - Long sessions consume server resources (pool default: 5 instances)
7. **Log window IDs** - Helps debugging
8. **Use SessionType wisely** - `Auto` for background processes, `User` for interactive integrations
9. **Read back after writing** - Save status can report success without persisting a sub-record (see [Verifying Writes](#verifying-writes-dont-trust-save-status-alone))

---

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Invalid/expired token | Re-authenticate |
| "Session not found" | Session ended/timed out | Start new session |
| "Blocked" status | Response window opened | Handle the dialog |
| "Field not found" | Wrong field/datawindow name | Check SQL Information |
| "Window not open" | Window was closed | Re-open the window |

---

## Session vs Transaction API

| Feature | Interactive API | Transaction API |
|---------|-----------------|-----------------|
| Stateful | Yes | No |
| Response windows | Handled | Cause failures |
| Business logic | Full validation | Full validation |
| Complexity | Higher | Lower |
| Performance | Slower | Faster |
| Use case | Complex workflows | Bulk operations |

---

## Known Issues and Workarounds

### Row Selection Synchronization Bug (List → Detail)

When working with windows that have a list/detail pattern (e.g., Item Maintenance with `invloclist` and `inv_loc_detail`), there is a synchronization issue where selecting a row in the list does not immediately update the detail view.

**Symptom:** After selecting row N in a list datawindow and navigating to the detail tab, the detail shows the **previous** row's data instead of row N.

**Pattern observed:**
```text
Row 0 selected → Detail shows row 0 (correct - first selection)
Row 1 selected → Detail shows row 0 (1 behind)
Row 2 selected → Detail shows row 1 (1 behind)
Row 3 selected → Detail shows row 2 (1 behind)
...
Row 5 selected → Detail shows row 4 (1 behind)
```

**Workaround:** Select row N+1 after selecting row N to "push" row N's data through to the detail view.

The calls below are the middle of a sequence — they assume a session, an open `Item` window (`window_id`) with an item already loaded, and the location list populated. Note that `product_group_id` is exactly the field whose GL-account dialog is described in [Response Windows](#response-windows); run it knowingly.

> Full runnable version of the surrounding session/window/save scaffold: [Linking Price Page to Price Book](#example-linking-price-page-to-price-book)

<!-- tabs -->

#### Python

```python
# To edit row 5 (last row in a 6-row list):

# 1. Select target row
await client.put(f"{ui_url}/api/ui/interactive/v2/row", headers=headers,
    json={"WindowId": window_id, "DatawindowName": "invloclist", "Row": 5})

# 2. Select row N+1 to push row N's data through (can be non-existent)
await client.put(f"{ui_url}/api/ui/interactive/v2/row", headers=headers,
    json={"WindowId": window_id, "DatawindowName": "invloclist", "Row": 6})

# 3. Now go to detail tab - it will show row 5's data
await client.put(f"{ui_url}/api/ui/interactive/v2/tab", headers=headers,
    json={"WindowId": window_id, "PageName": "TABPAGE_18"})

# 4. Change the field and save
await client.put(f"{ui_url}/api/ui/interactive/v2/change", headers=headers,
    json={"WindowId": window_id, "List": [
        {"TabName": "TABPAGE_18", "DatawindowName": "inv_loc_detail", "FieldName": "product_group_id", "Value": "NEW_VALUE"}
    ]})
await client.put(
    f"{ui_url}/api/ui/interactive/v2/data",
    headers=headers, json=window_id,
)
```

#### C#

```csharp
// To edit row 5 (last row in a 6-row list):

// 1. Select target row
await http.PutAsJsonAsync($"{uiUrl}/api/ui/interactive/v2/row",
    new { WindowId = windowId, DatawindowName = "invloclist", Row = 5 });

// 2. Select row N+1 to push row N's data through (can be non-existent)
await http.PutAsJsonAsync($"{uiUrl}/api/ui/interactive/v2/row",
    new { WindowId = windowId, DatawindowName = "invloclist", Row = 6 });

// 3. Now go to detail tab - it will show row 5's data
await http.PutAsJsonAsync($"{uiUrl}/api/ui/interactive/v2/tab",
    new { WindowId = windowId, PageName = "TABPAGE_18" });

// 4. Change the field and save
await http.PutAsJsonAsync($"{uiUrl}/api/ui/interactive/v2/change",
    new
    {
        WindowId = windowId,
        List = new[]
        {
            new { TabName = "TABPAGE_18", DatawindowName = "inv_loc_detail", FieldName = "product_group_id", Value = "NEW_VALUE" }
        }
    });
await http.PutAsync($"{uiUrl}/api/ui/interactive/v2/data",
    new StringContent($"\"{windowId}\"", System.Text.Encoding.UTF8, "application/json"));
```

<!-- /tabs -->

**Affected Windows:**
- Item Maintenance (`Item` service) - Location Detail tab
- Likely other windows with list/detail patterns

**Note:** This issue may be specific to certain P21 versions or configurations. Test thoroughly with your environment.

**Related trap — never `select_row` on the detail form itself.** A single-row detail form (e.g. `inv_loc_detail`) is *bound* to the currently-selected parent list row. Sending `PUT /v2/row` against the **detail** datawindow does not select within the detail — it re-selects the *parent* list (row N on the detail = row N on `invloclist`) and **silently flips which record the detail is bound to**, typically to the list's first row. The edit then lands on the wrong location while every call reports success. Select only the parent list row, edit the detail directly, and assert the detail shows exactly the intended record before and after the change (abort without saving on mismatch). The Transaction API's nested pattern keys by `location_id` and has no such trap. *(Credit: [Alex Westemeier](https://github.com/AWestemeier))*

### Row 0 Auto-Selection Quirk

After switching to a tab that contains a list or grid datawindow, row 0 is **automatically selected** by the API. Explicitly calling `change_row(0)` after switching tabs returns HTTP 422 because the row is already selected.

**Symptom:** `PUT /api/ui/interactive/v2/row` with `Row: 0` returns 422 error.

**Workaround:** Skip the `change_row(0)` call when targeting the first row. Start explicit row selection at row 1. Guard helper only — it makes no call of its own:

> Full runnable version of the row/tab calls it wraps: [Linking Price Page to Price Book](#example-linking-price-page-to-price-book)

<!-- tabs -->

#### Python

```python
async def select_row_safe(window: Window, row: int, datawindow_name: str):
    """Select a row, handling the row 0 auto-selection quirk.

    Row 0 is auto-selected when switching to a tab with a grid.
    Calling change_row(0) explicitly returns 422.
    """
    if row == 0:
        # Row 0 is already selected after tab switch - skip
        return
    await window.change_row(row, datawindow_name)
```

#### C#

```csharp
public async Task SelectRowSafeAsync(Window window, int row, string datawindowName)
{
    // Row 0 is auto-selected when switching to a tab with a grid.
    // Calling ChangeRow(0) explicitly returns 422.
    if (row == 0)
    {
        // Row 0 is already selected after tab switch - skip
        return;
    }
    await window.ChangeRowAsync(row, datawindowName);
}
```

<!-- /tabs -->

**Important:** This is different from the [row selection synchronization bug](#row-selection-synchronization-bug-list-detail) documented above. That bug is about list-to-detail data sync being one row behind. This quirk is specifically about row 0 being pre-selected after a tab switch.

### Key Fields Commit the Cursor (Later Fields Silently Ignored)

Sending a grid row's **key field** in a `change` request commits the row cursor — any field in the same `List` (or a later call) that follows the key field is **silently ignored** (the call still returns a success status). Example: on the JobContractPricing BINS grid, `contract_bin_id` is the key; if it appears before the quantity fields, the quantities never land.

**Guidance:**

- When only *changing* values on an already-selected row, **don't send the key field at all** — select the row, then change the non-key fields.
- When the key field must be sent (identifying a row by value), send it **last**.
- After the save, read the values back — a silently-dropped edit is indistinguishable from success by status code alone (see [Verifying Writes](#verifying-writes-dont-trust-save-status-alone)).

*(Credit: [Alex Westemeier](https://github.com/AWestemeier))*

### Numeric Values: Send Integer Strings for Whole Numbers

When setting numeric fields, send whole numbers as integer strings (`"30"`), not float-formatted strings (`"30.0"`) — some windows reject or mishandle the float form. Format values the way a user would type them.

---

## v1 vs v2 API Differences

> **Upgrading P21?** Version-specific middleware changes that break interactive integrations (25.2's required `DatawindowName`, 2026.1's Accept-header 500 / ghost sessions / `SessionId`→`Id` / nonexistent-record loads / non-atomic batched changes) are cataloged in [P21 Breaking Changes by Version](14-Breaking-Changes.md).


> **Important:** Some P21 servers only support v2 endpoints (v1 returns 404). Always try v2 first.

### Summary Table

| Operation | v1 | v2 |
|-----------|----|----|
| **Change** | `ChangeRequests` array | `List` array |
| **Change field ref** | `DataWindowName` (capital W) | `TabName` + `DatawindowName` (lowercase w) — **required in 25.2+** |
| **Save** | `{"WindowId": "..."}` | `"..."` (just GUID string) |
| **Tab change** | `PagePath: {PageName: "..."}` | `PageName: "..."` (direct) |
| **Row change** | `RowNumber` | `Row` |
| **Row datawindow** | `DataWindowName` | `DatawindowName` (lowercase w) |

### Change Request Format

**v1:**
```json
{
    "WindowId": "...",
    "ChangeRequests": [
        {"DataWindowName": "form", "FieldName": "item_id", "Value": "ABC"}
    ]
}
```

**v2:**
```json
{
    "WindowId": "...",
    "List": [
        {"TabName": "FORM", "FieldName": "item_id", "Value": "ABC", "DatawindowName": "form"}
    ]
}
```

### Save Format

**v1:** `{"WindowId": "abc-123..."}`

**v2:** `"abc-123..."` (just the GUID string - this is critical!)

### Tab Change Format

**v1:**
```json
{"WindowId": "...", "PagePath": {"PageName": "TABPAGE_17"}}
```

**v2:**
```json
{"WindowId": "...", "PageName": "TABPAGE_17"}
```

### Row Change Format

**v1:**
```json
{"WindowId": "...", "DataWindowName": "list", "RowNumber": 0}
```

**v2:**
```json
{"WindowId": "...", "DatawindowName": "list", "Row": 0}
```

### Get Window Data / Close Window

**v2:** Use `?id=` query parameter:

```http
GET /api/ui/interactive/v2/data?id={windowId}
DELETE /api/ui/interactive/v2/window?id={windowId}
DELETE /api/ui/interactive/v2/data?id={windowId}
```

---

## Troubleshooting v2 Issues

| Error | Cause | Solution |
|-------|-------|----------|
| 404 on v1 | Server only supports v2 | Use v2 endpoints |
| 422 "Window ID was not provided" | Save payload wrapped in object | Send just the GUID string for v2 |
| 500 on tab change | Using PagePath wrapper | Use PageName directly for v2 |
| Field change doesn't persist | Missing TabName | Include TabName in change request |

---

## Operational Patterns

Patterns discovered through production use of the Interactive API. These cover behaviors that are not documented in the official SDK but are consistent and reproducible.

### Tab Unlock Sequences

Certain windows have tabs that start disabled and unlock progressively as prerequisite fields are populated. The API communicates unlock state via `tabpageenabled` events in responses.

**Example: JobContractPricing**

On window open, 7 tabs are disabled: `CUSTSHIPTOCONSIGN`, `BINS`, `VALUES`, `BIN_ITEMS`, `ITEM_BIN_NOTES`, `SHIPTOCONSIGNCONTROL`, `CONSIGNMENTISSUES`. The unlock sequence is:

1. Set `contract_no` on `FORM` — enables `CUSTOMER_SHIP_TO`
2. Create a customer/ship_to combination on `CUSTOMER_SHIP_TO`, then set `customer_id` and `ship_to_id` on `FORM` — enables `SHIP_TO_ITEM`
3. Set `item_id` on `SHIP_TO_ITEM` and dismiss the scan lookup dialog — enables `VALUES`, `BINS`, `BIN_ITEMS`, `ITEM_BIN_NOTES` simultaneously

> **Important:** P21 rejects setting `customer_id` or `ship_to_id` on the FORM header directly. You must create the combination on `CUSTOMER_SHIP_TO` first. Error: *"Before selecting a Customer ID or Ship To ID, make sure that the combination exists in the Customer/Ship To tab."*

**Example: JobContractPricing — EXISTING contract (BINS editing).** The sequence above is the *creation* flow. For an existing contract, the combination already exists and the recipe differs (verified; credit: [Alex Westemeier](https://github.com/AWestemeier)):

1. Load the contract by setting `job_no`, `customer_id`, and `ship_to_id` on `FORM/d_dw_job_price_hdr` (three separate change calls). **Load by `job_no`, not `contract_no`** — renewals can leave the same `contract_no` on two header rows, while `job_no` is unique.
2. Change to the `CUSTOMER_SHIP_TO` tab and **select the ship-to's grid row** — the BINS tab only unlocks after the ship-to row is selected. Skipping this (or loading by `contract_no` alone) leaves it disabled with *"Tab page is disabled and cannot be selected."*
3. Per line: `JOBPRICELINE` tab → select the line's row → `BINS` tab → the grid is **filtered to the selected ship-to**, so it has exactly one row per line — `select_row("bins", 1)` always targets the right bin. Edit the quantity fields.
4. One `save()` at the end persists every edit in the session (save per ship-to on large runs so a mid-run failure doesn't lose everything).

> For bulk bin-quantity changes, the Transaction API with `IgnoreDisabled: true` is faster — see [Editing Bin Quantities](03-Transaction-API.md#editing-bin-quantities-on-an-existing-contract). Use this interactive recipe when a Transaction-API edge case appears or the contract is expired-adjacent work that needs window logic.

**Detecting tab unlock events** — an event parser plus the single change call that triggers the unlock; it runs inside an established session and window:

> Full runnable version of that change call: [Linking Price Page to Price Book](#example-linking-price-page-to-price-book)

<!-- tabs -->

#### Python

```python
def check_tab_unlocks(result: dict) -> list[str]:
    """Extract tab unlock events from an API response.

    Args:
        result: The parsed JSON response from a change/save operation.

    Returns:
        List of tab names that were just enabled.
    """
    unlocked: list[str] = []
    for event in result.get("Events", []):
        if event.get("Name") == "tabpageenabled":
            for kv in event.get("Data", []):
                if kv.get("Key") == "pagename":
                    unlocked.append(kv["Value"])
    return unlocked


# Usage: monitor unlocks as you populate fields
result = await client.put(
    f"{ui_url}/api/ui/interactive/v2/change",
    headers=headers,
    json={
        "WindowId": window_id,
        "List": [{
            "TabName": "FORM",
            "DatawindowName": "form",
            "FieldName": "contract_no",
            "Value": "1001"
        }]
    }
)
response = result.json()
unlocked = check_tab_unlocks(response)
# unlocked == ["CUSTOMER_SHIP_TO"]
```

#### C\#

```csharp
public List<string> CheckTabUnlocks(JsonElement result)
{
    // Extract tab unlock events from an API response.
    var unlocked = new List<string>();
    var events = result["Events"] as JsonElement ?? new JsonElement();

    foreach (var evt in events)
    {
        if (evt["Name"]?.ToString() == "tabpageenabled")
        {
            var data = evt["Data"] as JsonElement ?? new JsonElement();
            foreach (var kv in data)
            {
                if (kv["Key"]?.ToString() == "pagename")
                    unlocked.Add(kv["Value"]!.ToString());
            }
        }
    }
    return unlocked;
}

// Usage: monitor unlocks as you populate fields
var payload = new JsonElement
{
    ["WindowId"] = windowId,
    ["List"] = new JsonElement
    {
        new JsonElement
        {
            ["TabName"] = "FORM",
            ["DatawindowName"] = "form",
            ["FieldName"] = "contract_no",
            ["Value"] = "1001"
        }
    }
};
var content = new StringContent(payload.ToString(), Encoding.UTF8, "application/json");
var response = await http.PutAsync($"{uiUrl}/api/ui/interactive/v2/change", content);
var result = JsonElement.Parse(await response.Content.ReadAsStringAsync());
var unlocked = CheckTabUnlocks(result);
// unlocked == ["CUSTOMER_SHIP_TO"]
```

<!-- /tabs -->

**General guidance:** Always check `tabpageenabled` events when working with multi-tab windows. Do not attempt to switch to a disabled tab — the API will return an error. Query the window definition (`GET /api/ui/interactive/v2/window?id={windowId}`) to see current tab states via `TabPageList[].Enabled`.

### add_row with Status=2 (Failure)

When calling `add_row`, P21 returns `Status: 2` (Failure) if the **previous** row has incomplete or invalid data. Despite the failure status, the new row **is still created** and ready for data entry. This is expected P21 behavior, not a hard error.

**Example:** `add_row("bins")` returns Status=2 with message *"Required value missing for Bin ID on row 1"* — but row 2 is created and editable.

**Guidance:** When adding multiple rows in sequence, expect Status=2 on subsequent `add_row` calls if prior rows are not fully populated. Do not treat Status=2 as a fatal error in this context — check the messages to determine whether the failure is about the previous row's validation or a real problem. Drop-in replacement for the plain add-row call, taking an existing `window_id`:

> Full runnable version of that call in context: [Linking Price Page to Price Book](#example-linking-price-page-to-price-book)

<!-- tabs -->

#### Python

```python
import logging

import httpx

logger = logging.getLogger(__name__)


async def add_row_tolerant(
    window_id: str,
    datawindow_name: str,
    headers: dict[str, str],
    client: httpx.AsyncClient,
    ui_url: str,
) -> dict:
    """Add a row, tolerating Status=2 from incomplete previous rows.

    Args:
        window_id: The active window ID.
        datawindow_name: Target datawindow (e.g., "bins").
        headers: Request headers with auth token.
        client: httpx async client.
        ui_url: UI server base URL.

    Returns:
        Parsed response dict.

    Raises:
        RuntimeError: If the failure is not a previous-row validation issue.
    """
    response = await client.post(
        f"{ui_url}/api/ui/interactive/v2/row",
        headers=headers,
        json={"WindowId": window_id, "DatawindowName": datawindow_name},
    )
    response.raise_for_status()
    result = response.json()

    status = result.get("Status", 0)
    if status == 2:
        messages = [m.get("Text", "") for m in result.get("Messages", [])]
        # Previous-row validation warnings are expected — row was still added
        if any("required value missing" in m.lower() for m in messages):
            logger.info(
                "add_row returned Status=2, row added"
            )
            return result
        # Unexpected failure — raise
        raise RuntimeError(f"add_row failed: {messages}")

    return result
```

#### C\#

```csharp
public async Task<JsonElement> AddRowTolerantAsync(
    string windowId,
    string datawindowName,
    HttpClient http,
    string uiUrl)
{
    // Add a row, tolerating Status=2 from incomplete previous rows.
    var payload = new JsonElement
    {
        ["WindowId"] = windowId,
        ["DatawindowName"] = datawindowName
    };
    var content = new StringContent(payload.ToString(), Encoding.UTF8, "application/json");
    var response = await http.PostAsync($"{uiUrl}/api/ui/interactive/v2/row", content);
    response.EnsureSuccessStatusCode();

    var result = JsonElement.Parse(await response.Content.ReadAsStringAsync());
    var status = result["Status"]?.Value<int>() ?? 0;

    if (status == 2)
    {
        var messages = result["Messages"]?
            .Select(m => m["Text"]?.ToString() ?? "")
            .ToList() ?? new List<string>();

        // Previous-row validation warnings are expected — row was still added
        if (messages.Any(m => m.Contains("required value missing", StringComparison.OrdinalIgnoreCase)))
        {
            Console.WriteLine($"add_row returned Status=2 (previous row incomplete), row added");
            return result;
        }
        // Unexpected failure — raise
        throw new InvalidOperationException($"add_row failed: {string.Join("; ", messages)}");
    }

    return result;
}
```

<!-- /tabs -->

### Response Window Types

Response windows fall into distinct categories based on what interactions they support. Tool-capable dialogs can be dismissed via `POST /tools`, but message boxes (`w_message`) are auto-answered based on `ResponseWindowHandlingEnabled` configuration.

| Type | Example | Buttons | Field Input | Dismiss Method |
|------|---------|---------|-------------|----------------|
| **Button-only dialog** | `w_rule_callback_response` | `cb_1` through `cb_5` | N/A | `POST /tools` with button name |
| **Form + button dialog** | `w_inventory_scan_lookup` | `cb_ok`, `cb_cancel` | See editability note below | `POST /tools` with button name |
| **Editable form dialog** | `w_notepad_response_lite` | `cb_select_all`, `cb_ok` | **Editable with `TabName: null`** | Fill fields, then `POST /tools` |
| **Message box** | `w_message` | Default-answered | Cannot be inspected | Auto-answered when `ResponseWindowHandlingEnabled: false` |

**Editability (reconciled July 2026):** earlier testing (April 2026) concluded form-type response windows could only be dismissed — `GET /data` returned 400 and `PUT /change` returned 500 with *"Tab with name FORM does not exist"*. Those change attempts addressed the popup's fields with `TabName: "FORM"`. Later work showed form-style response windows **are editable** when the change request uses **`TabName: null`** with the popup's window ID — verified end-to-end on `w_notepad_response_lite` (see [PurchaseOrder Notepad Writes](#purchaseorder-notepad-writes-header-vs-line)). If a popup's fields reject edits, retry with `TabName: null` before concluding the window is dismiss-only. `w_message` boxes remain uneditable and are auto-answered.

**Inspecting and dismissing response windows** — takes the `response_window_id` from a `windowopened` event, so it only runs once something has opened a popup:

> Full runnable version: [Recipe: Add a Header Note](#recipe-add-a-header-note)

<!-- tabs -->

#### Python

```python
import logging

import httpx

logger = logging.getLogger(__name__)


async def handle_response_window(
    window_id: str,
    response_window_id: str,
    headers: dict[str, str],
    client: httpx.AsyncClient,
    ui_url: str,
    button: str = "cb_cancel",
) -> dict:
    """Inspect a response window and dismiss it via button click.

    Args:
        window_id: The parent window ID.
        response_window_id: The response window ID from the windowopened event.
        headers: Request headers with auth token.
        client: httpx async client.
        ui_url: UI server base URL.
        button: Button name to click (default: cb_cancel).

    Returns:
        Parsed response from the tool click.
    """
    # Step 1: Discover available buttons
    tools_resp = await client.get(
        f"{ui_url}/api/ui/interactive/v2/tools",
        headers=headers,
        params={"windowId": response_window_id},
    )
    tools_resp.raise_for_status()
    tools = tools_resp.json()
    available = [t.get("Name") or t.get("ToolName") for t in tools]
    logger.info("Response window %s has buttons: %s", response_window_id, available)

    # Step 2: Click the desired button
    click_resp = await client.post(
        f"{ui_url}/api/ui/interactive/v2/tools",
        headers=headers,
        json={"WindowId": response_window_id, "ToolName": button},
    )
    click_resp.raise_for_status()
    return click_resp.json()
```

#### C\#

```csharp
public async Task<JsonElement> HandleResponseWindowAsync(
    string windowId,
    string responseWindowId,
    HttpClient http,
    string uiUrl,
    string button = "cb_cancel")
{
    // Step 1: Discover available buttons
    var toolsResp = await http.GetAsync(
        $"{uiUrl}/api/ui/interactive/v2/tools?windowId={responseWindowId}");
    toolsResp.EnsureSuccessStatusCode();

    var tools = JsonElement.Parse(await toolsResp.Content.ReadAsStringAsync());
    var available = tools.Select(t => t["Name"]?.ToString() ?? t["ToolName"]?.ToString()).ToList();
    Console.WriteLine($"Response window {WindowId} has buttons: {Buttons}",
        responseWindowId, string.Join(", ", available));

    // Step 2: Click the desired button
    var payload = new JsonElement
    {
        ["WindowId"] = responseWindowId,
        ["ToolName"] = button
    };
    var content = new StringContent(payload.ToString(), Encoding.UTF8, "application/json");
    var clickResp = await http.PostAsync($"{uiUrl}/api/ui/interactive/v2/tools", content);
    clickResp.EnsureSuccessStatusCode();

    return JsonElement.Parse(await clickResp.Content.ReadAsStringAsync());
}
```

<!-- /tabs -->

> **Note:** The `GET /tools` endpoint uses `?windowId=` (not `?id=`). See the [query parameter inconsistency note](#data-operations-v2-recommended) in the Endpoints section.

### UOM Auto-Population

When setting `item_id` via the Interactive API, P21 validates the unit of measure against the item's valid UOM list. Setting an invalid `uom` value results in HTTP 422 with *"Invalid uom value"*.

**Best practice:** Do **not** set `uom` explicitly — let P21 auto-populate it from the item master data. The API fills in the item's default selling or purchasing UOM automatically after `item_id` is set. Only override `uom` if you have confirmed the target value exists in the item's UOM list.

### Timeout Recommendations

Recommended HTTP timeouts based on production experience with large payloads:

| Operation | Recommended Timeout | Notes |
|-----------|-------------------|-------|
| `submit_transaction` (Transaction API, 100+ lines) | 300s | Large payloads with many line items |
| `save_data` (Interactive API) | 120s | Business logic validation can be slow |
| `select_row` / `change_fields` | 60s | Individual field operations |
| Default for all operations | 60s minimum | P21 server processing varies by load |

> These are guidelines from production use. Adjust based on data volume and server performance. The default `httpx` timeout of 5 seconds is almost always too low for P21 operations.

---

## Related

- [Authentication](00-Authentication.md)
- [API Selection Guide](01-API-Selection-Guide.md)
- [Transaction API](03-Transaction-API.md)
- [Production & Labor API](12-Production-Labor-API.md) - TimeEntry, ProductionOrder, and labor services
- [Batch Processing Patterns](09-Batch-Processing-Patterns.md) - Production batch processing, async client, error recovery
- [examples/python/interactive/](https://github.com/mrwuss/p21-api-documentation/tree/master/examples/python/interactive/) - Working examples
