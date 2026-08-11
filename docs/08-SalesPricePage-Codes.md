# Sales Price Page Dropdown Codes

> **Disclaimer:** This is unofficial, community-created documentation for Epicor Prophet 21 APIs. It is not affiliated with, endorsed by, or supported by Epicor Software Corporation. All product names, trademarks, and registered trademarks are property of their respective owners. Use at your own risk.

---

## Overview

When working with the SalesPricePage window via the Interactive API, dropdown fields require specific **display values** (not codes). This document provides the mappings discovered through API testing.

**Important:** P21's code tables (`code_p21`) may not be accessible via OData in all environments. These values were discovered by testing the Interactive API directly.

**Note:** Code mappings may vary between P21 versions and configurations. Always verify codes in your specific environment.

---

## Field Order Requirements

When creating or modifying price pages, fields must be set in a specific order. Setting fields out of order can cause validation failures or incorrect data.

### Required Field Order for Page Creation

1. **`price_page_type_cd`** - Set page type FIRST (e.g., "Supplier / Product Group")
2. **`company_id`** - Required BEFORE product_group_id
3. **`product_group_id`** or **`discount_group_id`** - Depends on page type
4. **`supplier_id`**
5. **`description`**
6. **`pricing_method_cd`** - Use display value "Source"
7. **`source_price_cd`** - Use display value "Supplier List Price"
8. **`effective_date`** / **`expiration_date`**
9. Switch to **VALUES** tab
10. **`calculation_method_cd`** - Use display value "Multiplier"
11. **`calculation_value1`** (and additional break values if needed)

### Example: Creating a Price Page

<!-- tabs -->

**Python**

```python
"""Create a SalesPricePage through the Interactive API, in the required field order."""
import json
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
COMPANY_ID = "ACME"
PRODUCT_GROUP_ID = "HVAC"
SUPPLIER_ID = "10050"
DESCRIPTION = "P2-L5-10050-HVAC-WHOLESALE"
EFFECTIVE_DATE = "2025-01-01"
EXPIRATION_DATE = "2030-12-31"
MULTIPLIER = "0.85"                       # calculation_value1 -- tier 1, qty 1+
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

    def change(tab: str, datawindow: str, field: str, value: str) -> None:
        """One field per call -- a batched /v2/change is non-atomic on 2026.1."""
        r = client.put(
            f"{ui_server}/api/ui/interactive/v2/change",
            headers=headers,
            json={
                "WindowId": window_id,
                "List": [{
                    "TabName": tab,
                    "DatawindowName": datawindow,   # required since 25.2
                    "FieldName": field,
                    "Value": value,
                }],
            },
        )
        r.raise_for_status()

    # A session must exist before any window can be opened.
    session = client.post(
        f"{ui_server}/api/ui/interactive/sessions",
        headers=headers,
        json={"ResponseWindowHandlingEnabled": False},
    )
    session.raise_for_status()

    # ServiceName is the only reliable window identifier -- Name/Title can 400.
    opened = client.post(
        f"{ui_server}/api/ui/interactive/v2/window",
        headers=headers,
        json={"ServiceName": "SalesPricePage"},
    )
    opened.raise_for_status()
    window_id = opened.json()["WindowId"]
    print("Window opened:", window_id)

    try:
        # Step 1: page type FIRST -- it determines which fields are available
        change("FORM", "form", "price_page_type_cd", "Supplier / Product Group")

        # Step 2: company_id BEFORE product_group_id
        change("FORM", "form", "company_id", COMPANY_ID)

        # Step 3: product group
        change("FORM", "form", "product_group_id", PRODUCT_GROUP_ID)

        # Step 4: supplier
        change("FORM", "form", "supplier_id", SUPPLIER_ID)

        # Step 5: description
        change("FORM", "form", "description", DESCRIPTION)

        # Steps 6-7: pricing method and source price
        change("FORM", "form", "pricing_method_cd", "Source")
        change("FORM", "form", "source_price_cd", "Supplier List Price")

        # Step 8: dates
        change("FORM", "form", "effective_date", EFFECTIVE_DATE)
        change("FORM", "form", "expiration_date", EXPIRATION_DATE)

        # Step 9: switch to the VALUES tab (2026.1 binds PageName, not TabName)
        tab = client.put(
            f"{ui_server}/api/ui/interactive/v2/tab",
            headers=headers,
            json={"WindowId": window_id, "PageName": "VALUES"},
        )
        tab.raise_for_status()

        # Steps 10-11: calculation method, then the tier-1 value
        change("VALUES", "values", "calculation_method_cd", "Multiplier")
        change("VALUES", "values", "calculation_value1", MULTIPLIER)

        # Save -- v2 takes the bare WindowId string as the JSON body
        saved = client.put(
            f"{ui_server}/api/ui/interactive/v2/data",
            headers=headers,
            content=json.dumps(window_id),
        )
        saved.raise_for_status()
        result = saved.json()
        # ResultStatus: None=0, Success=1, Failure=2, Blocked=3
        print("Save status:", result.get("Status"))
        for message in result.get("Messages") or []:
            print("  Message:", message)

        # ---- read-back: HTTP 200 alone does not mean the save landed --------
        read_back = client.get(
            f"{ui_server}/api/ui/interactive/v2/data",
            params={"id": window_id},
            headers=headers,
        )
        read_back.raise_for_status()
        # /v2/data returns the datawindows of the ACTIVE tab, and only a subset
        # of them -- absence here is not proof that a field failed to save.
        print(json.dumps(read_back.json())[:2000])
    finally:
        client.delete(
            f"{ui_server}/api/ui/interactive/v2/window",
            params={"id": window_id},
            headers=headers,
        )
        # Always end the session -- a leaked one blocks the next create with 409
        client.delete(f"{ui_server}/api/ui/interactive/sessions", headers=headers)
```

**C#**

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string CompanyId = "ACME";
const string ProductGroupId = "HVAC";
const string SupplierId = "10050";
const string Description = "P2-L5-10050-HVAC-WHOLESALE";
const string EffectiveDate = "2025-01-01";
const string ExpirationDate = "2030-12-31";
const string Multiplier = "0.85";          // calculation_value1 -- tier 1, qty 1+
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

// A session must exist before any window can be opened.
var sessionResponse = await client.PostAsync(
    $"{uiServer}/api/ui/interactive/sessions",
    Json(new { ResponseWindowHandlingEnabled = false }));
sessionResponse.EnsureSuccessStatusCode();

// ServiceName is the only reliable window identifier -- Name/Title can 400.
var openResponse = await client.PostAsync(
    $"{uiServer}/api/ui/interactive/v2/window",
    Json(new { ServiceName = "SalesPricePage" }));
openResponse.EnsureSuccessStatusCode();

using var opened = JsonDocument.Parse(await openResponse.Content.ReadAsStringAsync());
var windowId = opened.RootElement.GetProperty("WindowId").GetString()!;
Console.WriteLine($"Window opened: {windowId}");

// One field per call -- a batched /v2/change is non-atomic on 2026.1.
async Task ChangeAsync(string tab, string datawindow, string field, string value)
{
    var response = await client.PutAsync(
        $"{uiServer}/api/ui/interactive/v2/change",
        Json(new
        {
            WindowId = windowId,
            List = new[]
            {
                new
                {
                    TabName = tab,
                    DatawindowName = datawindow,     // required since 25.2
                    FieldName = field,
                    Value = value,
                }
            }
        }));
    response.EnsureSuccessStatusCode();
}

try
{
    // Step 1: page type FIRST -- it determines which fields are available
    await ChangeAsync("FORM", "form", "price_page_type_cd", "Supplier / Product Group");

    // Step 2: company_id BEFORE product_group_id
    await ChangeAsync("FORM", "form", "company_id", CompanyId);

    // Step 3: product group
    await ChangeAsync("FORM", "form", "product_group_id", ProductGroupId);

    // Step 4: supplier
    await ChangeAsync("FORM", "form", "supplier_id", SupplierId);

    // Step 5: description
    await ChangeAsync("FORM", "form", "description", Description);

    // Steps 6-7: pricing method and source price
    await ChangeAsync("FORM", "form", "pricing_method_cd", "Source");
    await ChangeAsync("FORM", "form", "source_price_cd", "Supplier List Price");

    // Step 8: dates
    await ChangeAsync("FORM", "form", "effective_date", EffectiveDate);
    await ChangeAsync("FORM", "form", "expiration_date", ExpirationDate);

    // Step 9: switch to the VALUES tab (2026.1 binds PageName, not TabName)
    var tabResponse = await client.PutAsync(
        $"{uiServer}/api/ui/interactive/v2/tab",
        Json(new { WindowId = windowId, PageName = "VALUES" }));
    tabResponse.EnsureSuccessStatusCode();

    // Steps 10-11: calculation method, then the tier-1 value
    await ChangeAsync("VALUES", "values", "calculation_method_cd", "Multiplier");
    await ChangeAsync("VALUES", "values", "calculation_value1", Multiplier);

    // Save -- v2 takes the bare WindowId string as the JSON body
    var saveResponse = await client.PutAsync(
        $"{uiServer}/api/ui/interactive/v2/data", Json(windowId));
    saveResponse.EnsureSuccessStatusCode();

    using var result = JsonDocument.Parse(await saveResponse.Content.ReadAsStringAsync());
    // ResultStatus: None=0, Success=1, Failure=2, Blocked=3
    if (result.RootElement.TryGetProperty("Status", out var status))
        Console.WriteLine($"Save status: {status}");
    if (result.RootElement.TryGetProperty("Messages", out var messages))
    {
        foreach (var message in messages.EnumerateArray())
            Console.WriteLine($"  Message: {message}");
    }

    // ---- read-back: HTTP 200 alone does not mean the save landed ----------
    var readBackResponse = await client.GetAsync(
        $"{uiServer}/api/ui/interactive/v2/data?id={windowId}");
    readBackResponse.EnsureSuccessStatusCode();

    // /v2/data returns the datawindows of the ACTIVE tab, and only a subset of
    // them -- absence here is not proof that a field failed to save.
    var raw = await readBackResponse.Content.ReadAsStringAsync();
    Console.WriteLine(raw.Length > 2000 ? raw[..2000] : raw);
}
finally
{
    await client.DeleteAsync($"{uiServer}/api/ui/interactive/v2/window?id={windowId}");
    // Always end the session -- a leaked one blocks the next create with 409
    await client.DeleteAsync($"{uiServer}/api/ui/interactive/sessions");
}

// --- helpers ---------------------------------------------------------------

static StringContent Json(object payload) =>
    new(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json");

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

### Why Order Matters

- Setting `product_group_id` before `price_page_type_cd` will fail validation
- Setting `product_group_id` before `company_id` may cause lookup errors
- The VALUES tab fields are only available after FORM tab fields are set
- Some fields become read-only after others are set

## Transaction API Alternative

`SalesPricePage` is also available as a Transaction API service. Its full definition is
available from `GET /api/v2/services`, and the service exposes these data elements:

> **Two naming systems, both correct — don't mix them.** The `DatawindowName` column below (`d_dw_price_page_main`, `d_dw_price_page_values`, `d_dw_price_page_cost`) is what the **Transaction** definition reports. The **Interactive** API names the same datawindows `form`, `values` and `costs` — those short names are what the Interactive examples above send as `DatawindowName`, and they are what `GET /v2/window` returns. Verified live on 26.1.5910.3 by selecting each tab and reading the window state. The tab page names (`FORM`, `VALUES`, `COSTS`, `PO COST MULTIPLIERS`, `USED BY`, `TP_PRICE_PAGE_X_LOCATION`, `TIMESTAMPPRICE_PAGE`) are shared by both APIs. See [Get Window State](04-Interactive-API.md#1-get-window-state).

| DataElement | Type | KeyFields | DatawindowName | BusinessObjectName |
|-------------|------|-----------|----------------|--------------------|
| `FORM.form` | Form | `price_page_uid` | `d_dw_price_page_main` | `price_page` |
| `VALUES.values` | Form | none | `d_dw_price_page_values` | `price_page` |
| `COSTS.costs` | Form | none | `d_dw_price_page_cost` | `price_page` |
| `PO COST MULTIPLIERS.price_page_po_cost_calc` | List | `customer_id` | `d_dw_price_page_po_cost_calc_dataentry` | `price_page_po_cost_calc` |
| `USED BY.price_book_x_page` | List | none | `d_ds_price_book_x_page` | `price_book` |
| `TP_PRICE_PAGE_X_LOCATION.price_page_x_location` | List | none | `d_dw_price_page_x_location_maint` | `price_page_location` |

For **updating an existing page**, the Transaction API is much simpler than the Interactive
field-order sequence: `FORM.form` keys on `price_page_uid`, so it supports a keyed upsert via
`POST /api/v2/transaction`. Interactive remains the better choice for **creating** a page,
where the page type determines which subsequent fields are valid or required. In short, use
Interactive for create workflows and the Transaction API for keyed updates.

---

## Calculation Method (VALUES Tab)

The `calculation_method_cd` field on the VALUES tab controls how pricing calculations are applied.

| Code | Display Value | Description |
|------|---------------|-------------|
| 211 | Multiplier | Multiply by value (most common) |
| 228 | Difference | Subtract value from source price |
| 229 | Mark Up | Add markup percentage to cost |
| 230 | Percentage | Apply as percentage |
| 1292 | Fixed Price | Use fixed price value |

**Usage Example:**

> Fragment -- it exists to contrast a display value with a code, not to run.
> Full runnable version: [Example: Creating a Price Page](#example-creating-a-price-page).

<!-- tabs -->

**Python**

```python
# Correct - use display value
change("VALUES", "values", "calculation_method_cd", "Mark Up")

# Incorrect - do not use code
change("VALUES", "values", "calculation_method_cd", "229")
```

**C#**

```csharp
// Correct - use display value
await ChangeAsync("VALUES", "values", "calculation_method_cd", "Mark Up");

// Incorrect - do not use code
await ChangeAsync("VALUES", "values", "calculation_method_cd", "229");
```

<!-- /tabs -->

---

## Price Page Type (FORM Tab)

The `price_page_type_cd` field determines the page type.

| Code | Display Value | Key Field |
|------|---------------|-----------|
| 210 | Customer | `customer_id` |
| 211 | Customer / Item | `customer_id` + `item_id` |
| 213 | Supplier / Discount Group | `discount_group_id` |
| 214 | Supplier / Product Group | `product_group_id` |
| 215 | Supplier / Discount Group (alt) | `discount_group_id` |

> **Note:** Type 213 ("Supplier / Discount Group") uses `discount_group_id` instead of `product_group_id`. The field order changes slightly for this type - see [Discount Group Pages](#discount-group-pages-type-213) below.

---

## Pricing Method (FORM Tab)

The `pricing_method_cd` field controls how the source price is used.

| Code | Display Value |
|------|---------------|
| 220 | Source |
| 221 | Price |
| 234 | Pricing Libraries |
| 300 | None |

**Note:** Corrected against live `code_p21` reads (July 2026); earlier published values were misassigned. Code mappings may still vary between P21 versions — always verify in your environment.

---

## Source Price (FORM Tab)

The `source_price_cd` field determines the base price source.

| Code | Display Value | Notes |
|------|---------------|-------|
| 200 | Supplier List Price | Use with Multiplier (211) calculation method |
| 201 | Replacement Cost | Also known as "Primary Supplier Cost". Use with Mark Up (229) |
| 202 | Average Cost | |

### Source Price and Calculation Method Pairing

Using the wrong combination of source price and calculation method produces incorrect pricing. Follow these pairings:

| Calculation Method | Recommended Source Price | Why |
|--------------------|------------------------|-----|
| Multiplier (211) | Supplier List Price (200) | Multiplier applies a factor to list price |
| Mark Up (229) | Replacement Cost / Primary Supplier Cost (201) | Mark up adds margin above cost |

> **Important:** Source Price code 201 is labeled "Replacement Cost" in the dropdown but represents the **Primary Supplier Cost** in P21's pricing engine. This distinction matters when building pricing logic.

---

## Cost Type (COSTS Tab)

| Code | Display Value |
|------|---------------|
| 220 | Source |
| 222 | Order |
| 227 | Value |
| 300 | None |

**Note:** Corrected against live `code_p21` reads (July 2026); earlier published values were misassigned.

---

## Commission Cost Calculation Method (COSTS Tab)

The `commission_cost_calc_method_cd` on the COSTS tab (different from VALUES tab).

| Code | Display Value |
|------|---------------|
| 211 | Multiplier |
| 212 | Difference |
| 213 | Mark Up |
| 214 | Percentage |

**Note:** These codes differ from the VALUES tab `calculation_method_cd` codes.

---

## Discovery Method

> **The fastest source is the Transaction definition, not the window.** `GET /api/v2/definition/SalesPricePage` returns each code field's accepted **display labels** in `ValidValues` — exactly the strings you send under `UseCodeValues: false` — even if you intend to drive the window interactively. The Interactive window state does **not** carry them: its field metadata is only `Name`, `Label`, `DataType` and `Enabled` (verified 26.1.5910.3). Confirmed live from the definition:
>
> | Field | Accepted display values |
> |---|---|
> | `price_page_type_cd` | Item · Supplier / Discount Group · Supplier / Product Group · Supplier / Manufacturing Class · Supplier · Discount Group · Product Group · Customer Part Number · Price Family · Supplier/Price Family |
> | `pricing_method_cd` | Source · Price · None |
> | `source_price_cd` | Price 1–10 · Supplier List Price · Primary Supplier Cost · Standard Cost · Average Cost · Last Received PO Cost · Next Due in PO Cost · Other Cost · Strategic List Price · Strategic Cost |
> | `calculation_method_cd` | Difference · Multiplier · Mark up · Percentage · Fixed Price |
>
> All four are typed `Long` — you send the label, not the number, when `UseCodeValues` is `false`. Your environment's list may differ; re-run the definition call against your own tenant rather than trusting this table.

The numeric codes below were discovered by:

1. Opening the SalesPricePage window via Interactive API
2. Setting each dropdown to different display values
3. Reading the resulting code from window state
4. Verifying against live database records

<!-- tabs -->

**Python**

```python
"""Discovery: set a dropdown by display value, then read the window state back."""
import json
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
PRICE_PAGE_UID = "45556"                  # an existing page to probe
DISPLAY_VALUE = "Mark Up"                 # the dropdown label under test
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

    def change(tab: str, datawindow: str, field: str, value: str) -> None:
        """One field per call -- a batched /v2/change is non-atomic on 2026.1."""
        r = client.put(
            f"{ui_server}/api/ui/interactive/v2/change",
            headers=headers,
            json={
                "WindowId": window_id,
                "List": [{
                    "TabName": tab,
                    "DatawindowName": datawindow,   # required since 25.2
                    "FieldName": field,
                    "Value": value,
                }],
            },
        )
        r.raise_for_status()

    session = client.post(
        f"{ui_server}/api/ui/interactive/sessions",
        headers=headers,
        json={"ResponseWindowHandlingEnabled": False},
    )
    session.raise_for_status()

    opened = client.post(
        f"{ui_server}/api/ui/interactive/v2/window",
        headers=headers,
        json={"ServiceName": "SalesPricePage"},
    )
    opened.raise_for_status()
    window_id = opened.json()["WindowId"]

    try:
        # Load a specific price page, then move to the tab that owns the field
        change("FORM", "form", "price_page_uid", PRICE_PAGE_UID)

        tab = client.put(
            f"{ui_server}/api/ui/interactive/v2/tab",
            headers=headers,
            json={"WindowId": window_id, "PageName": "VALUES"},
        )
        tab.raise_for_status()

        # Try setting a display value
        change("VALUES", "values", "calculation_method_cd", DISPLAY_VALUE)

        # Read the window state back and find the code the label resolved to
        state = client.get(
            f"{ui_server}/api/ui/interactive/v2/data",
            params={"id": window_id},
            headers=headers,
        )
        state.raise_for_status()
        # Shape varies by window -- dump it and locate calculation_method_cd
        print(json.dumps(state.json(), indent=2)[:3000])
    finally:
        client.delete(
            f"{ui_server}/api/ui/interactive/v2/window",
            params={"id": window_id},
            headers=headers,
        )
        client.delete(f"{ui_server}/api/ui/interactive/sessions", headers=headers)
```

**C#**

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string PricePageUid = "45556";                   // an existing page to probe
const string DisplayValue = "Mark Up";                 // the dropdown label under test
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

var openResponse = await client.PostAsync(
    $"{uiServer}/api/ui/interactive/v2/window",
    Json(new { ServiceName = "SalesPricePage" }));
openResponse.EnsureSuccessStatusCode();

using var opened = JsonDocument.Parse(await openResponse.Content.ReadAsStringAsync());
var windowId = opened.RootElement.GetProperty("WindowId").GetString()!;

// One field per call -- a batched /v2/change is non-atomic on 2026.1.
async Task ChangeAsync(string tab, string datawindow, string field, string value)
{
    var response = await client.PutAsync(
        $"{uiServer}/api/ui/interactive/v2/change",
        Json(new
        {
            WindowId = windowId,
            List = new[]
            {
                new
                {
                    TabName = tab,
                    DatawindowName = datawindow,     // required since 25.2
                    FieldName = field,
                    Value = value,
                }
            }
        }));
    response.EnsureSuccessStatusCode();
}

try
{
    // Load a specific price page, then move to the tab that owns the field
    await ChangeAsync("FORM", "form", "price_page_uid", PricePageUid);

    var tabResponse = await client.PutAsync(
        $"{uiServer}/api/ui/interactive/v2/tab",
        Json(new { WindowId = windowId, PageName = "VALUES" }));
    tabResponse.EnsureSuccessStatusCode();

    // Try setting a display value
    await ChangeAsync("VALUES", "values", "calculation_method_cd", DisplayValue);

    // Read the window state back and find the code the label resolved to
    var stateResponse = await client.GetAsync(
        $"{uiServer}/api/ui/interactive/v2/data?id={windowId}");
    stateResponse.EnsureSuccessStatusCode();

    // Shape varies by window -- dump it and locate calculation_method_cd
    var raw = await stateResponse.Content.ReadAsStringAsync();
    Console.WriteLine(raw.Length > 3000 ? raw[..3000] : raw);
}
finally
{
    await client.DeleteAsync($"{uiServer}/api/ui/interactive/v2/window?id={windowId}");
    await client.DeleteAsync($"{uiServer}/api/ui/interactive/sessions");
}

// --- helpers ---------------------------------------------------------------

static StringContent Json(object payload) =>
    new(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json");

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

---

## Price Breaks (Quantity-Based Pricing)

Price pages support up to 15 calculation values and 14 break quantities for quantity-based pricing.

### Fields

| Field | Type | Label | Purpose |
|-------|------|-------|---------|
| `calculation_value1` - `calculation_value15` | Decimal | - | Price or calculation value for each tier; tier 1 applies to quantity 1+ |
| `break1` - `break14` | Decimal | - | Quantity thresholds for tiers 2 through 15 |
| `uom1` - `uom14` | Char | UOM | Per-tier unit of measure for tiers 1 through 14 |
| `other_cost1` - `other_cost15` | Decimal | - | Per-tier other cost value |
| `calculation_method_cd` | Long | - | Calculation method |
| `values_currency_id` | Long | Calculation Currency ID | Calculation currency |

The VALUES tab repeats `calculation_value{n}`, `break{n}`, `uom{n}`, and
`other_cost{n}` for each tier. Tier 15 has `calculation_value15` and `other_cost15`, but
does not have `break15` or `uom15`.

### Cross-Service Break-Field Names

The same tiered-price concept uses different field names across services. Sending the wrong
spelling does not necessarily error; the tier can silently fail to land.

| Service | Tier 1 field | Tiers 2..n | Breaks | Per-tier UOM |
|---------|--------------|------------|--------|--------------|
| `SalesPricePage` | `calculation_value1` | `calculation_value2`-`calculation_value15` | `break1`-`break14` | `uom1`-`uom14` |
| `JobContractPricing` | `calculation_value1` | `calculation_value2`-`calculation_value15` | `break1`-`break14` | none |
| `SalesPriceBook` (`LIST.list_detail`, read-back summary) | `calculation_value1` | `calculation_value2` | `break1` | none |
| `PurchasePricingPageSupplier` / `...Item` / `...DiscGrp` | `value1` | `value2`-`value15` | `break1`-`break14` | `uom1`-`uom14` |

On the purchase-side services, the API field is `value{n}`, while the underlying database
column is `purchase_pricing_page.Calculation_Value{n}`. The database column name and API
field name therefore disagree, and neither matches the field names used by the other three
services above.

### Example: Setting Up Price Breaks

<!-- tabs -->

**Python**

```python
"""Set quantity-based price break tiers on an existing price page."""
import json
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
PRICE_PAGE_UID = "45556"                  # the page whose tiers you are setting
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

    def change(tab: str, datawindow: str, field: str, value: str) -> None:
        """One field per call -- a batched /v2/change is non-atomic on 2026.1."""
        r = client.put(
            f"{ui_server}/api/ui/interactive/v2/change",
            headers=headers,
            json={
                "WindowId": window_id,
                "List": [{
                    "TabName": tab,
                    "DatawindowName": datawindow,   # required since 25.2
                    "FieldName": field,
                    "Value": value,
                }],
            },
        )
        r.raise_for_status()

    session = client.post(
        f"{ui_server}/api/ui/interactive/sessions",
        headers=headers,
        json={"ResponseWindowHandlingEnabled": False},
    )
    session.raise_for_status()

    opened = client.post(
        f"{ui_server}/api/ui/interactive/v2/window",
        headers=headers,
        json={"ServiceName": "SalesPricePage"},
    )
    opened.raise_for_status()
    window_id = opened.json()["WindowId"]

    try:
        change("FORM", "form", "price_page_uid", PRICE_PAGE_UID)

        tab = client.put(
            f"{ui_server}/api/ui/interactive/v2/tab",
            headers=headers,
            json={"WindowId": window_id, "PageName": "VALUES"},
        )
        tab.raise_for_status()

        # Base multiplier: 0.85 for qty 1+
        change("VALUES", "values", "calculation_value1", "0.85")

        # Price break at qty 6: 0.82 multiplier
        change("VALUES", "values", "break1", "6")
        change("VALUES", "values", "calculation_value2", "0.82")

        # Price break at qty 25: 0.78 multiplier
        change("VALUES", "values", "break2", "25")
        change("VALUES", "values", "calculation_value3", "0.78")

        # Price break at qty 100: 0.75 multiplier
        change("VALUES", "values", "break3", "100")
        change("VALUES", "values", "calculation_value4", "0.75")

        # Save -- v2 takes the bare WindowId string as the JSON body
        saved = client.put(
            f"{ui_server}/api/ui/interactive/v2/data",
            headers=headers,
            content=json.dumps(window_id),
        )
        saved.raise_for_status()
        result = saved.json()
        # ResultStatus: None=0, Success=1, Failure=2, Blocked=3
        print("Save status:", result.get("Status"))
        for message in result.get("Messages") or []:
            print("  Message:", message)

        # ---- read-back: the only proof the tiers landed ---------------------
        read_back = client.get(
            f"{ui_server}/api/ui/interactive/v2/data",
            params={"id": window_id},
            headers=headers,
        )
        read_back.raise_for_status()
        print(json.dumps(read_back.json())[:2000])
    finally:
        client.delete(
            f"{ui_server}/api/ui/interactive/v2/window",
            params={"id": window_id},
            headers=headers,
        )
        client.delete(f"{ui_server}/api/ui/interactive/sessions", headers=headers)
```

**C#**

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string PricePageUid = "45556";        // the page whose tiers you are setting
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

var openResponse = await client.PostAsync(
    $"{uiServer}/api/ui/interactive/v2/window",
    Json(new { ServiceName = "SalesPricePage" }));
openResponse.EnsureSuccessStatusCode();

using var opened = JsonDocument.Parse(await openResponse.Content.ReadAsStringAsync());
var windowId = opened.RootElement.GetProperty("WindowId").GetString()!;

// One field per call -- a batched /v2/change is non-atomic on 2026.1.
async Task ChangeAsync(string tab, string datawindow, string field, string value)
{
    var response = await client.PutAsync(
        $"{uiServer}/api/ui/interactive/v2/change",
        Json(new
        {
            WindowId = windowId,
            List = new[]
            {
                new
                {
                    TabName = tab,
                    DatawindowName = datawindow,     // required since 25.2
                    FieldName = field,
                    Value = value,
                }
            }
        }));
    response.EnsureSuccessStatusCode();
}

try
{
    await ChangeAsync("FORM", "form", "price_page_uid", PricePageUid);

    var tabResponse = await client.PutAsync(
        $"{uiServer}/api/ui/interactive/v2/tab",
        Json(new { WindowId = windowId, PageName = "VALUES" }));
    tabResponse.EnsureSuccessStatusCode();

    // Base multiplier: 0.85 for qty 1+
    await ChangeAsync("VALUES", "values", "calculation_value1", "0.85");

    // Price break at qty 6: 0.82 multiplier
    await ChangeAsync("VALUES", "values", "break1", "6");
    await ChangeAsync("VALUES", "values", "calculation_value2", "0.82");

    // Price break at qty 25: 0.78 multiplier
    await ChangeAsync("VALUES", "values", "break2", "25");
    await ChangeAsync("VALUES", "values", "calculation_value3", "0.78");

    // Price break at qty 100: 0.75 multiplier
    await ChangeAsync("VALUES", "values", "break3", "100");
    await ChangeAsync("VALUES", "values", "calculation_value4", "0.75");

    // Save -- v2 takes the bare WindowId string as the JSON body
    var saveResponse = await client.PutAsync(
        $"{uiServer}/api/ui/interactive/v2/data", Json(windowId));
    saveResponse.EnsureSuccessStatusCode();

    using var result = JsonDocument.Parse(await saveResponse.Content.ReadAsStringAsync());
    // ResultStatus: None=0, Success=1, Failure=2, Blocked=3
    if (result.RootElement.TryGetProperty("Status", out var status))
        Console.WriteLine($"Save status: {status}");
    if (result.RootElement.TryGetProperty("Messages", out var messages))
    {
        foreach (var message in messages.EnumerateArray())
            Console.WriteLine($"  Message: {message}");
    }

    // ---- read-back: the only proof the tiers landed ------------------------
    var readBackResponse = await client.GetAsync(
        $"{uiServer}/api/ui/interactive/v2/data?id={windowId}");
    readBackResponse.EnsureSuccessStatusCode();

    var raw = await readBackResponse.Content.ReadAsStringAsync();
    Console.WriteLine(raw.Length > 2000 ? raw[..2000] : raw);
}
finally
{
    await client.DeleteAsync($"{uiServer}/api/ui/interactive/v2/window?id={windowId}");
    await client.DeleteAsync($"{uiServer}/api/ui/interactive/sessions");
}

// --- helpers ---------------------------------------------------------------

static StringContent Json(object payload) =>
    new(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json");

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

### Mapping

| Quantity Range | Calculation Value |
|----------------|-------------------|
| 1 to (break1-1) | `calculation_value1` |
| break1 to (break2-1) | `calculation_value2` |
| break2 to (break3-1) | `calculation_value3` |
| ... | ... |

### Notes

- `calculation_value1` is always the base price (qty 1+)
- `break1` corresponds to `calculation_value2` (not `calculation_value1`)
- Unused break/value fields should be 0 or null
- Maximum 14 break points (15 price levels including base)

---

## Discount Group Pages (Type 213)

Discount group pages use `discount_group_id` instead of `product_group_id`. The field order differs from the standard product group page creation sequence.

### Field Order for Type 213

1. **`price_page_type_cd`** - Set to "Supplier / Discount Group"
2. **`company_id`** - Required before discount_group_id
3. **`discount_group_id`** - Replaces `product_group_id`
4. **`supplier_id`**
5. **`description`**
6. **`pricing_method_cd`** - "Source"
7. **`source_price_cd`** - "Supplier List Price"
8. **`effective_date`** / **`expiration_date`**
9. Switch to **VALUES** tab
10. **`calculation_method_cd`** and values

### Example: Creating a Discount Group Page

<!-- tabs -->

**Python**

```python
"""Create a type-213 (Supplier / Discount Group) price page."""
import json
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
COMPANY_ID = "ACME"
DISCOUNT_GROUP_ID = "DG001"               # replaces product_group_id on type 213
SUPPLIER_ID = "10050"
DESCRIPTION = "P2-L5-10050-DG001-WHOLESALE"
EFFECTIVE_DATE = "2025-01-01"
EXPIRATION_DATE = "2030-12-31"
MULTIPLIER = "0.85"                       # calculation_value1 -- tier 1, qty 1+
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

    def change(tab: str, datawindow: str, field: str, value: str) -> None:
        """One field per call -- a batched /v2/change is non-atomic on 2026.1."""
        r = client.put(
            f"{ui_server}/api/ui/interactive/v2/change",
            headers=headers,
            json={
                "WindowId": window_id,
                "List": [{
                    "TabName": tab,
                    "DatawindowName": datawindow,   # required since 25.2
                    "FieldName": field,
                    "Value": value,
                }],
            },
        )
        r.raise_for_status()

    session = client.post(
        f"{ui_server}/api/ui/interactive/sessions",
        headers=headers,
        json={"ResponseWindowHandlingEnabled": False},
    )
    session.raise_for_status()

    opened = client.post(
        f"{ui_server}/api/ui/interactive/v2/window",
        headers=headers,
        json={"ServiceName": "SalesPricePage"},
    )
    opened.raise_for_status()
    window_id = opened.json()["WindowId"]

    try:
        # Step 1: page type to Discount Group
        change("FORM", "form", "price_page_type_cd", "Supplier / Discount Group")

        # Step 2: company_id first
        change("FORM", "form", "company_id", COMPANY_ID)

        # Step 3: discount group (NOT product_group_id)
        change("FORM", "form", "discount_group_id", DISCOUNT_GROUP_ID)

        # Step 4: supplier
        change("FORM", "form", "supplier_id", SUPPLIER_ID)

        # Steps 5-8: same as a product group page
        change("FORM", "form", "description", DESCRIPTION)
        change("FORM", "form", "pricing_method_cd", "Source")
        change("FORM", "form", "source_price_cd", "Supplier List Price")
        change("FORM", "form", "effective_date", EFFECTIVE_DATE)
        change("FORM", "form", "expiration_date", EXPIRATION_DATE)

        # Step 9: switch to the VALUES tab (2026.1 binds PageName, not TabName)
        tab = client.put(
            f"{ui_server}/api/ui/interactive/v2/tab",
            headers=headers,
            json={"WindowId": window_id, "PageName": "VALUES"},
        )
        tab.raise_for_status()

        # Step 10: calculation method and values
        change("VALUES", "values", "calculation_method_cd", "Multiplier")
        change("VALUES", "values", "calculation_value1", MULTIPLIER)

        # Save -- v2 takes the bare WindowId string as the JSON body
        saved = client.put(
            f"{ui_server}/api/ui/interactive/v2/data",
            headers=headers,
            content=json.dumps(window_id),
        )
        saved.raise_for_status()
        result = saved.json()
        # ResultStatus: None=0, Success=1, Failure=2, Blocked=3
        print("Save status:", result.get("Status"))
        for message in result.get("Messages") or []:
            print("  Message:", message)

        # ---- read-back: the only proof the page landed ----------------------
        read_back = client.get(
            f"{ui_server}/api/ui/interactive/v2/data",
            params={"id": window_id},
            headers=headers,
        )
        read_back.raise_for_status()
        print(json.dumps(read_back.json())[:2000])
    finally:
        client.delete(
            f"{ui_server}/api/ui/interactive/v2/window",
            params={"id": window_id},
            headers=headers,
        )
        client.delete(f"{ui_server}/api/ui/interactive/sessions", headers=headers)
```

**C#**

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string CompanyId = "ACME";
const string DiscountGroupId = "DG001";     // replaces product_group_id on type 213
const string SupplierId = "10050";
const string Description = "P2-L5-10050-DG001-WHOLESALE";
const string EffectiveDate = "2025-01-01";
const string ExpirationDate = "2030-12-31";
const string Multiplier = "0.85";           // calculation_value1 -- tier 1, qty 1+
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

var openResponse = await client.PostAsync(
    $"{uiServer}/api/ui/interactive/v2/window",
    Json(new { ServiceName = "SalesPricePage" }));
openResponse.EnsureSuccessStatusCode();

using var opened = JsonDocument.Parse(await openResponse.Content.ReadAsStringAsync());
var windowId = opened.RootElement.GetProperty("WindowId").GetString()!;

// One field per call -- a batched /v2/change is non-atomic on 2026.1.
async Task ChangeAsync(string tab, string datawindow, string field, string value)
{
    var response = await client.PutAsync(
        $"{uiServer}/api/ui/interactive/v2/change",
        Json(new
        {
            WindowId = windowId,
            List = new[]
            {
                new
                {
                    TabName = tab,
                    DatawindowName = datawindow,     // required since 25.2
                    FieldName = field,
                    Value = value,
                }
            }
        }));
    response.EnsureSuccessStatusCode();
}

try
{
    // Step 1: page type to Discount Group
    await ChangeAsync("FORM", "form", "price_page_type_cd", "Supplier / Discount Group");

    // Step 2: company_id first
    await ChangeAsync("FORM", "form", "company_id", CompanyId);

    // Step 3: discount group (NOT product_group_id)
    await ChangeAsync("FORM", "form", "discount_group_id", DiscountGroupId);

    // Step 4: supplier
    await ChangeAsync("FORM", "form", "supplier_id", SupplierId);

    // Steps 5-8: same as a product group page
    await ChangeAsync("FORM", "form", "description", Description);
    await ChangeAsync("FORM", "form", "pricing_method_cd", "Source");
    await ChangeAsync("FORM", "form", "source_price_cd", "Supplier List Price");
    await ChangeAsync("FORM", "form", "effective_date", EffectiveDate);
    await ChangeAsync("FORM", "form", "expiration_date", ExpirationDate);

    // Step 9: switch to the VALUES tab (2026.1 binds PageName, not TabName)
    var tabResponse = await client.PutAsync(
        $"{uiServer}/api/ui/interactive/v2/tab",
        Json(new { WindowId = windowId, PageName = "VALUES" }));
    tabResponse.EnsureSuccessStatusCode();

    // Step 10: calculation method and values
    await ChangeAsync("VALUES", "values", "calculation_method_cd", "Multiplier");
    await ChangeAsync("VALUES", "values", "calculation_value1", Multiplier);

    // Save -- v2 takes the bare WindowId string as the JSON body
    var saveResponse = await client.PutAsync(
        $"{uiServer}/api/ui/interactive/v2/data", Json(windowId));
    saveResponse.EnsureSuccessStatusCode();

    using var result = JsonDocument.Parse(await saveResponse.Content.ReadAsStringAsync());
    // ResultStatus: None=0, Success=1, Failure=2, Blocked=3
    if (result.RootElement.TryGetProperty("Status", out var status))
        Console.WriteLine($"Save status: {status}");
    if (result.RootElement.TryGetProperty("Messages", out var messages))
    {
        foreach (var message in messages.EnumerateArray())
            Console.WriteLine($"  Message: {message}");
    }

    // ---- read-back: the only proof the page landed -------------------------
    var readBackResponse = await client.GetAsync(
        $"{uiServer}/api/ui/interactive/v2/data?id={windowId}");
    readBackResponse.EnsureSuccessStatusCode();

    var raw = await readBackResponse.Content.ReadAsStringAsync();
    Console.WriteLine(raw.Length > 2000 ? raw[..2000] : raw);
}
finally
{
    await client.DeleteAsync($"{uiServer}/api/ui/interactive/v2/window?id={windowId}");
    await client.DeleteAsync($"{uiServer}/api/ui/interactive/sessions");
}

// --- helpers ---------------------------------------------------------------

static StringContent Json(object payload) =>
    new(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json");

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

### OData Queries for Both Page Types

When querying price pages, check both `product_group_id` and `discount_group_id`:

<!-- tabs -->

**Python**

```python
"""List every active price page for one supplier -- product group and discount group."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
SUPPLIER_ID = "10050"                     # numeric -- no quotes in the filter
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
        "Accept": "application/json",       # 2026.1 returns an empty 500 without this
        "Content-Type": "application/json",
    }

    # Get ALL active pages for a supplier (both types)
    params = {
        "$filter": (
            f"supplier_id eq {SUPPLIER_ID} "
            f"and row_status_flag eq 704 "
            f"and (product_group_id ne null or discount_group_id ne null)"
        ),
        "$select": (
            "price_page_uid,description,price_page_type_cd,"
            "product_group_id,discount_group_id,supplier_id"
        ),
    }

    # OData goes to BASE_URL directly -- no UI-server routing
    response = client.get(
        f"{BASE_URL}/odataservice/odata/table/price_page",
        params=params,          # httpx URL-encodes the query string
        headers=headers,
    )
    response.raise_for_status()

    rows = response.json()["value"]
    print(f"{len(rows)} active pages for supplier {SUPPLIER_ID}")
    for row in rows:
        print(f"  {row.get('price_page_uid')}"
              f"  type={row.get('price_page_type_cd')}"
              f"  pg={row.get('product_group_id')}"
              f"  dg={row.get('discount_group_id')}"
              f"  {row.get('description')}")
```

**C#**

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string SupplierId = "10050";                     // numeric -- no quotes in the filter
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

// Get ALL active pages for a supplier (both types)
var filter = $"supplier_id eq {SupplierId} " +
    "and row_status_flag eq 704 " +
    "and (product_group_id ne null or discount_group_id ne null)";
var select = "price_page_uid,description,price_page_type_cd," +
    "product_group_id,discount_group_id,supplier_id";

// OData goes to BaseUrl directly -- no UI-server routing
var queryUrl = $"{BaseUrl}/odataservice/odata/table/price_page" +
    $"?$filter={Uri.EscapeDataString(filter)}&$select={Uri.EscapeDataString(select)}";
var response = await client.GetAsync(queryUrl);
response.EnsureSuccessStatusCode();

using var document = JsonDocument.Parse(await response.Content.ReadAsStringAsync());
var rows = document.RootElement.GetProperty("value");
Console.WriteLine($"{rows.GetArrayLength()} active pages for supplier {SupplierId}");
foreach (var row in rows.EnumerateArray())
{
    Console.WriteLine(
        $"  {Field(row, "price_page_uid")}" +
        $"  type={Field(row, "price_page_type_cd")}" +
        $"  pg={Field(row, "product_group_id")}" +
        $"  dg={Field(row, "discount_group_id")}" +
        $"  {Field(row, "description")}");
}

// --- helpers ---------------------------------------------------------------

static string Field(JsonElement row, string name) =>
    row.TryGetProperty(name, out var value) ? value.ToString() : "";

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

---

## Dollar-Based Price Breaks

In addition to quantity-based breaks (documented above), price pages support **dollar-based breaks** where break values represent total order value rather than unit quantities.

### Configuration Fields

Dollar-based breaks require additional fields on the VALUES tab:

| Field | Display Value | Code | Purpose |
|-------|---------------|------|---------|
| `totaling_method_cd` | Discount Group | 217 | Group items by discount group for break calculation |
| `totaling_basis_cd` | Supplier List Price | 200 | Use supplier list price as the dollar total basis |

### Example: Dollar-Based Breaks

<!-- tabs -->

**Python**

```python
"""Configure dollar-based (order-value) price breaks on an existing price page."""
import json
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
PRICE_PAGE_UID = "45556"                  # the page whose tiers you are setting
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

    def change(tab: str, datawindow: str, field: str, value: str) -> None:
        """One field per call -- a batched /v2/change is non-atomic on 2026.1."""
        r = client.put(
            f"{ui_server}/api/ui/interactive/v2/change",
            headers=headers,
            json={
                "WindowId": window_id,
                "List": [{
                    "TabName": tab,
                    "DatawindowName": datawindow,   # required since 25.2
                    "FieldName": field,
                    "Value": value,
                }],
            },
        )
        r.raise_for_status()

    session = client.post(
        f"{ui_server}/api/ui/interactive/sessions",
        headers=headers,
        json={"ResponseWindowHandlingEnabled": False},
    )
    session.raise_for_status()

    opened = client.post(
        f"{ui_server}/api/ui/interactive/v2/window",
        headers=headers,
        json={"ServiceName": "SalesPricePage"},
    )
    opened.raise_for_status()
    window_id = opened.json()["WindowId"]

    try:
        change("FORM", "form", "price_page_uid", PRICE_PAGE_UID)

        # Switch to VALUES tab
        tab = client.put(
            f"{ui_server}/api/ui/interactive/v2/tab",
            headers=headers,
            json={"WindowId": window_id, "PageName": "VALUES"},
        )
        tab.raise_for_status()

        # Set calculation method
        change("VALUES", "values", "calculation_method_cd", "Multiplier")

        # Configure dollar-based totaling
        change("VALUES", "values", "totaling_method_cd", "Discount Group")
        change("VALUES", "values", "totaling_basis_cd", "Supplier List Price")

        # Set dollar-based breaks (total order value thresholds)
        # $0-$4,999: 0.85 multiplier
        change("VALUES", "values", "calculation_value1", "0.85")

        # $5,000-$9,999: 0.82 multiplier
        change("VALUES", "values", "break1", "5000")
        change("VALUES", "values", "calculation_value2", "0.82")

        # $10,000-$14,999: 0.78 multiplier
        change("VALUES", "values", "break2", "10000")
        change("VALUES", "values", "calculation_value3", "0.78")

        # $15,000-$19,999: 0.75 multiplier
        change("VALUES", "values", "break3", "15000")
        change("VALUES", "values", "calculation_value4", "0.75")

        # $20,000+: 0.72 multiplier
        change("VALUES", "values", "break4", "10050")
        change("VALUES", "values", "calculation_value5", "0.72")

        # Save -- v2 takes the bare WindowId string as the JSON body
        saved = client.put(
            f"{ui_server}/api/ui/interactive/v2/data",
            headers=headers,
            content=json.dumps(window_id),
        )
        saved.raise_for_status()
        result = saved.json()
        # ResultStatus: None=0, Success=1, Failure=2, Blocked=3
        print("Save status:", result.get("Status"))
        for message in result.get("Messages") or []:
            print("  Message:", message)

        # ---- read-back: the only proof the tiers landed ---------------------
        read_back = client.get(
            f"{ui_server}/api/ui/interactive/v2/data",
            params={"id": window_id},
            headers=headers,
        )
        read_back.raise_for_status()
        print(json.dumps(read_back.json())[:2000])
    finally:
        client.delete(
            f"{ui_server}/api/ui/interactive/v2/window",
            params={"id": window_id},
            headers=headers,
        )
        client.delete(f"{ui_server}/api/ui/interactive/sessions", headers=headers)
```

**C#**

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string PricePageUid = "45556";        // the page whose tiers you are setting
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

var openResponse = await client.PostAsync(
    $"{uiServer}/api/ui/interactive/v2/window",
    Json(new { ServiceName = "SalesPricePage" }));
openResponse.EnsureSuccessStatusCode();

using var opened = JsonDocument.Parse(await openResponse.Content.ReadAsStringAsync());
var windowId = opened.RootElement.GetProperty("WindowId").GetString()!;

// One field per call -- a batched /v2/change is non-atomic on 2026.1.
async Task ChangeAsync(string tab, string datawindow, string field, string value)
{
    var response = await client.PutAsync(
        $"{uiServer}/api/ui/interactive/v2/change",
        Json(new
        {
            WindowId = windowId,
            List = new[]
            {
                new
                {
                    TabName = tab,
                    DatawindowName = datawindow,     // required since 25.2
                    FieldName = field,
                    Value = value,
                }
            }
        }));
    response.EnsureSuccessStatusCode();
}

try
{
    await ChangeAsync("FORM", "form", "price_page_uid", PricePageUid);

    // Switch to VALUES tab
    var tabResponse = await client.PutAsync(
        $"{uiServer}/api/ui/interactive/v2/tab",
        Json(new { WindowId = windowId, PageName = "VALUES" }));
    tabResponse.EnsureSuccessStatusCode();

    // Set calculation method
    await ChangeAsync("VALUES", "values", "calculation_method_cd", "Multiplier");

    // Configure dollar-based totaling
    await ChangeAsync("VALUES", "values", "totaling_method_cd", "Discount Group");
    await ChangeAsync("VALUES", "values", "totaling_basis_cd", "Supplier List Price");

    // Set dollar-based breaks (total order value thresholds)
    // $0-$4,999: 0.85 multiplier
    await ChangeAsync("VALUES", "values", "calculation_value1", "0.85");

    // $5,000-$9,999: 0.82 multiplier
    await ChangeAsync("VALUES", "values", "break1", "5000");
    await ChangeAsync("VALUES", "values", "calculation_value2", "0.82");

    // $10,000-$14,999: 0.78 multiplier
    await ChangeAsync("VALUES", "values", "break2", "10000");
    await ChangeAsync("VALUES", "values", "calculation_value3", "0.78");

    // $15,000-$19,999: 0.75 multiplier
    await ChangeAsync("VALUES", "values", "break3", "15000");
    await ChangeAsync("VALUES", "values", "calculation_value4", "0.75");

    // $20,000+: 0.72 multiplier
    await ChangeAsync("VALUES", "values", "break4", "10050");
    await ChangeAsync("VALUES", "values", "calculation_value5", "0.72");

    // Save -- v2 takes the bare WindowId string as the JSON body
    var saveResponse = await client.PutAsync(
        $"{uiServer}/api/ui/interactive/v2/data", Json(windowId));
    saveResponse.EnsureSuccessStatusCode();

    using var result = JsonDocument.Parse(await saveResponse.Content.ReadAsStringAsync());
    // ResultStatus: None=0, Success=1, Failure=2, Blocked=3
    if (result.RootElement.TryGetProperty("Status", out var status))
        Console.WriteLine($"Save status: {status}");
    if (result.RootElement.TryGetProperty("Messages", out var messages))
    {
        foreach (var message in messages.EnumerateArray())
            Console.WriteLine($"  Message: {message}");
    }

    // ---- read-back: the only proof the tiers landed ------------------------
    var readBackResponse = await client.GetAsync(
        $"{uiServer}/api/ui/interactive/v2/data?id={windowId}");
    readBackResponse.EnsureSuccessStatusCode();

    var raw = await readBackResponse.Content.ReadAsStringAsync();
    Console.WriteLine(raw.Length > 2000 ? raw[..2000] : raw);
}
finally
{
    await client.DeleteAsync($"{uiServer}/api/ui/interactive/v2/window?id={windowId}");
    await client.DeleteAsync($"{uiServer}/api/ui/interactive/sessions");
}

// --- helpers ---------------------------------------------------------------

static StringContent Json(object payload) =>
    new(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json");

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

### Quantity vs Dollar Breaks Comparison

| Aspect | Quantity Breaks | Dollar Breaks |
|--------|----------------|---------------|
| Break values represent | Unit quantities | Total order value ($) |
| `totaling_method_cd` | Not set (default) | "Discount Group" (217) |
| `totaling_basis_cd` | Not set (default) | "Supplier List Price" (200) |
| Typical use case | Volume discounts per SKU | Order-level discounts |
| Break example | 6 units, 25 units, 100 units | $5K, $10K, $15K, $20K |

---

## COSTS Tab Configuration

The COSTS tab is a separate tab on the SalesPricePage window that controls **commission cost calculation**. This determines how cost is calculated for commission purposes, separate from the selling price configured on the VALUES tab.

### Accessing the COSTS Tab

<!-- tabs -->

**Python**

```python
"""Set commission cost calculation on the COSTS tab of an existing price page."""
import json
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
PRICE_PAGE_UID = "45556"                  # the page whose COSTS tab you are setting
COMMISSION_COST_VALUE = "1.01"            # 1.01 = pass-through costing, 1% margin
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

    def change(tab: str, datawindow: str, field: str, value: str) -> None:
        """One field per call -- a batched /v2/change is non-atomic on 2026.1."""
        r = client.put(
            f"{ui_server}/api/ui/interactive/v2/change",
            headers=headers,
            json={
                "WindowId": window_id,
                "List": [{
                    "TabName": tab,
                    "DatawindowName": datawindow,   # required since 25.2
                    "FieldName": field,
                    "Value": value,
                }],
            },
        )
        r.raise_for_status()

    session = client.post(
        f"{ui_server}/api/ui/interactive/sessions",
        headers=headers,
        json={"ResponseWindowHandlingEnabled": False},
    )
    session.raise_for_status()

    opened = client.post(
        f"{ui_server}/api/ui/interactive/v2/window",
        headers=headers,
        json={"ServiceName": "SalesPricePage"},
    )
    opened.raise_for_status()
    window_id = opened.json()["WindowId"]

    try:
        change("FORM", "form", "price_page_uid", PRICE_PAGE_UID)

        # Switch to COSTS tab
        tab = client.put(
            f"{ui_server}/api/ui/interactive/v2/tab",
            headers=headers,
            json={"WindowId": window_id, "PageName": "COSTS"},
        )
        tab.raise_for_status()

        # Set commission cost calculation method -- COSTS codes differ from VALUES
        change("COSTS", "costs", "commission_cost_calc_method_cd", "Multiplier")

        # Set commission cost value (1.01 = pass-through costing with 1% margin)
        change("COSTS", "costs", "commission_cost_value1", COMMISSION_COST_VALUE)

        # Save -- v2 takes the bare WindowId string as the JSON body
        saved = client.put(
            f"{ui_server}/api/ui/interactive/v2/data",
            headers=headers,
            content=json.dumps(window_id),
        )
        saved.raise_for_status()
        result = saved.json()
        # ResultStatus: None=0, Success=1, Failure=2, Blocked=3
        print("Save status:", result.get("Status"))
        for message in result.get("Messages") or []:
            print("  Message:", message)

        # ---- read-back: the only proof the COSTS values landed --------------
        read_back = client.get(
            f"{ui_server}/api/ui/interactive/v2/data",
            params={"id": window_id},
            headers=headers,
        )
        read_back.raise_for_status()
        print(json.dumps(read_back.json())[:2000])
    finally:
        client.delete(
            f"{ui_server}/api/ui/interactive/v2/window",
            params={"id": window_id},
            headers=headers,
        )
        client.delete(f"{ui_server}/api/ui/interactive/sessions", headers=headers)
```

**C#**

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string PricePageUid = "45556";        // the page whose COSTS tab you are setting
const string CommissionCostValue = "1.01";  // 1.01 = pass-through costing, 1% margin
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

var openResponse = await client.PostAsync(
    $"{uiServer}/api/ui/interactive/v2/window",
    Json(new { ServiceName = "SalesPricePage" }));
openResponse.EnsureSuccessStatusCode();

using var opened = JsonDocument.Parse(await openResponse.Content.ReadAsStringAsync());
var windowId = opened.RootElement.GetProperty("WindowId").GetString()!;

// One field per call -- a batched /v2/change is non-atomic on 2026.1.
async Task ChangeAsync(string tab, string datawindow, string field, string value)
{
    var response = await client.PutAsync(
        $"{uiServer}/api/ui/interactive/v2/change",
        Json(new
        {
            WindowId = windowId,
            List = new[]
            {
                new
                {
                    TabName = tab,
                    DatawindowName = datawindow,     // required since 25.2
                    FieldName = field,
                    Value = value,
                }
            }
        }));
    response.EnsureSuccessStatusCode();
}

try
{
    await ChangeAsync("FORM", "form", "price_page_uid", PricePageUid);

    // Switch to COSTS tab
    var tabResponse = await client.PutAsync(
        $"{uiServer}/api/ui/interactive/v2/tab",
        Json(new { WindowId = windowId, PageName = "COSTS" }));
    tabResponse.EnsureSuccessStatusCode();

    // Set commission cost calculation method -- COSTS codes differ from VALUES
    await ChangeAsync("COSTS", "costs", "commission_cost_calc_method_cd", "Multiplier");

    // Set commission cost value (1.01 = pass-through costing with 1% margin)
    await ChangeAsync("COSTS", "costs", "commission_cost_value1", CommissionCostValue);

    // Save -- v2 takes the bare WindowId string as the JSON body
    var saveResponse = await client.PutAsync(
        $"{uiServer}/api/ui/interactive/v2/data", Json(windowId));
    saveResponse.EnsureSuccessStatusCode();

    using var result = JsonDocument.Parse(await saveResponse.Content.ReadAsStringAsync());
    // ResultStatus: None=0, Success=1, Failure=2, Blocked=3
    if (result.RootElement.TryGetProperty("Status", out var status))
        Console.WriteLine($"Save status: {status}");
    if (result.RootElement.TryGetProperty("Messages", out var messages))
    {
        foreach (var message in messages.EnumerateArray())
            Console.WriteLine($"  Message: {message}");
    }

    // ---- read-back: the only proof the COSTS values landed -----------------
    var readBackResponse = await client.GetAsync(
        $"{uiServer}/api/ui/interactive/v2/data?id={windowId}");
    readBackResponse.EnsureSuccessStatusCode();

    var raw = await readBackResponse.Content.ReadAsStringAsync();
    Console.WriteLine(raw.Length > 2000 ? raw[..2000] : raw);
}
finally
{
    await client.DeleteAsync($"{uiServer}/api/ui/interactive/v2/window?id={windowId}");
    await client.DeleteAsync($"{uiServer}/api/ui/interactive/sessions");
}

// --- helpers ---------------------------------------------------------------

static StringContent Json(object payload) =>
    new(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json");

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

### Common Pattern: Pass-Through Costing

For pages where commission cost should simply pass through at cost:

> Fragment -- the pattern is just the two COSTS fields below, set to a `Multiplier`
> of `1.01`. Full runnable version: [Accessing the COSTS Tab](#accessing-the-costs-tab).

<!-- tabs -->

**Python**

```python
change("COSTS", "costs", "commission_cost_calc_method_cd", "Multiplier")
change("COSTS", "costs", "commission_cost_value1", "1.01")
```

**C#**

```csharp
await ChangeAsync("COSTS", "costs", "commission_cost_calc_method_cd", "Multiplier");
await ChangeAsync("COSTS", "costs", "commission_cost_value1", "1.01");
```

<!-- /tabs -->

### Commission Cost Codes (Different from VALUES Tab)

The COSTS tab uses **different code numbers** than the VALUES tab for calculation methods:

| Tab | Code | Display Value |
|-----|------|---------------|
| VALUES | 211 | Multiplier |
| VALUES | 228 | Difference |
| VALUES | 229 | Mark Up |
| VALUES | 230 | Percentage |
| COSTS | 211 | Multiplier |
| COSTS | 212 | Difference |
| COSTS | 213 | Mark Up |
| COSTS | 214 | Percentage |

> **Warning:** Do not assume codes are the same across tabs. "Difference" is 228 on VALUES but 212 on COSTS.

---

## Purchase-Side Pricing Services

The five-service picture includes sales price pages, sales price books, job contracts, and three purchase page variants: supplier, item, and discount group. Each service has its own key set.

All three page variants share one shape: a header Form on `TABPAGE_1.tp_1_dw_1` carrying the keys, and an unkeyed values Form on `TABPAGE_2.tp_2_dw_2` carrying `calculation_type` plus `value1`-`value15`, `break1`-`break14`, and `uom1`-`uom14`. They differ only in which field the key set adds, and in the values datawindow name.

The tier structure is identical to a sales price page — 15 value slots, 14 break thresholds, and a 15th catch-all tier with no break. Only the field *names* differ (`value{n}` here, `calculation_value{n}` there). The DB columns disagree with both: `value1` maps to `purchase_pricing_page.Calculation_Value1`, `uom1` to `purchase_pricing_page.UOM1`.

Where to find them in the desktop client (from `frame_menu.service_name`, verified 2026-08-11):

| Service | P21 window | Window class |
|---------|-----------|--------------|
| `PurchasePricingPageSupplier` | Page Maintenance By Supplier ID | `m_bysupplierid` |
| `PurchasePricingPageSupplierItem` | Page Maintenance By Supplier ID/Item ID | `m_bysupplieriditemid` |
| `PurchasePricingPageSupplierDiscGrp` | Page Maintenance By Supplier ID/Discount Group | `m_bysupplieriddiscountgroup` |

`frame_menu` is the window-to-service map generally — query it over OData to find the service name behind any window, or the window behind any service. A `NULL` `service_name` means the window has no API surface.

| Service | Header datawindow | Values datawindow | KeyFields |
|---------|-------------------|-------------------|-----------|
| `PurchasePricingPageSupplier` | `d_pur_source_price_supplier` | `d_pur_source_price_supplier_values` | `company_id`, `purchase_pricing_book_id`, `supplier_id`, `effective_date`, `expiration_date` |
| `PurchasePricingPageSupplierItem` | `d_pur_source_price_supplier_item` | `d_pur_source_price_supplier_item_values` | ...the same five, plus `inv_mast_item_id` |
| `PurchasePricingPageSupplierDiscGrp` | `d_pur_source_price_supplier_disc` | `d_pur_source_price_supplier_disc_values` | ...the same five, plus `discount_group_id` |

### Header Fields (`TABPAGE_1.tp_1_dw_1`)

| Field | Notes |
|-------|-------|
| `company_id` | Key |
| `purchase_pricing_book_id` | Key. Maps to `purchase_pricing_page.pricing_book_id` |
| `supplier_id` | Key |
| `effective_date` · `expiration_date` | Keys — a page is identified by its date range, so re-pricing means a new page, not an edit |
| `location_id` | |
| `pricing_description` · `contract_number` | |
| `pricing_method` · `source_price` · `price` | |
| `totaling_basis` · `totaling_method` | |
| `major_group_id` | |
| `delete_flag` | |

### Header and Link Services

These carry no break fields — they exist to name a book or tie pages to it.

| Service | DataElement | Datawindow | KeyFields |
|---------|-------------|------------|-----------|
| `PurchasePricingBook` | `FORM.form` | `d_dw_purchase_pricing_book_form` | `company_id`, `purchase_pricing_book_id` |
| `SupplierPricing` | `TABPAGE_1.tp_1_dw_1` | `d_supplier_pricing_hdr` | `company_id`, `supplier_id` |
| `SupplierPricing` | `TABPAGE_17.tp_17_dw_17` (List) | `d_supplier_pricing_detail` | `purchase_price_library_id` |
| `SalesPriceBook` | `FORM.form` | `d_dw_price_book_form` | `price_book_id` |
| `SalesPriceBook` | `LIST.list_detail` (List) | `d_dw_price_page_x_book_grid` | `price_page_uid` |

`SalesPriceBook`'s `LIST.list_detail` exposes `calculation_value1`, `calculation_value2`, `break1`, and `other_cost_value` as a read-back summary of each page in the book — a convenient way to see a book's pages without opening each one.

> **The purchase-side write path is untested.** Everything above is read from the service definitions and confirmed by a live read. No write to a purchase pricing page has been verified, so treat creating or updating one as unproven until you have tested it in your own environment.

<!-- tabs -->

**Python**

```python
"""Read a purchase pricing page and print its quantity-break tiers."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
COMPANY_ID = "ACME"                       # the five key fields below identify one page
PRICING_BOOK_ID = "PB-2026"
SUPPLIER_ID = "10050"
EFFECTIVE_DATE = "2026-01-01"
EXPIRATION_DATE = "2030-12-31"
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


TIER_FIELD = re.compile(r"^(value|break|uom)(\d+)$")

with httpx.Client(verify=VERIFY_SSL, timeout=120, follow_redirects=True) as client:
    token = get_token(client)
    ui_server = get_ui_server(client, token)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",       # 2026.1 returns an empty 500 without this
        "Content-Type": "application/json",
    }

    response = client.post(
        f"{ui_server}/api/v2/transaction/get",
        headers=headers,
        json={
            "ServiceName": "PurchasePricingPageSupplier",
            "TransactionStates": [
                {
                    "DataElementName": "TABPAGE_1.tp_1_dw_1",
                    "Keys": [
                        {"Name": "company_id", "Value": COMPANY_ID},
                        {"Name": "purchase_pricing_book_id", "Value": PRICING_BOOK_ID},
                        {"Name": "supplier_id", "Value": SUPPLIER_ID},
                        {"Name": "effective_date", "Value": EFFECTIVE_DATE},
                        {"Name": "expiration_date", "Value": EXPIRATION_DATE},
                    ],
                },
                {"DataElementName": "TABPAGE_2.tp_2_dw_2", "Keys": []},
            ],
        },
    )
    response.raise_for_status()
    result = response.json()

    # Fields come back as {"Name": ..., "Value": ...} entries inside each row's
    # Edits array — not as top-level keys.
    values = {}
    for transaction in result.get("Transactions", []):
        for element in transaction.get("DataElements", []):
            for row in element.get("Rows", []):
                for edit in row.get("Edits", []):
                    values[edit.get("Name")] = edit.get("Value")

    print(f"calculation_type: {values.get('calculation_type', '')}")
    # 15 value slots, but only 14 break thresholds and UOMs — tier 15 is the
    # catch-all above the last break.
    for tier in range(1, 16):
        value, brk, uom = (values.get(f"value{tier}", ""),
                           values.get(f"break{tier}", ""),
                           values.get(f"uom{tier}", ""))
        if any((value, brk, uom)):
            print(f"  tier {tier:>2}: value={value:<12} break={brk:<10} uom={uom}")
```

**C#**

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string CompanyId = "ACME";                       // the five key fields below
const string PricingBookId = "PB-2026";                     // identify one pricing page
const string SupplierId = "10050";
const string EffectiveDate = "2026-01-01";
const string ExpirationDate = "2030-12-31";
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

var body = JsonSerializer.Serialize(new
{
    ServiceName = "PurchasePricingPageSupplier",
    TransactionStates = new object[]
    {
        new
        {
            DataElementName = "TABPAGE_1.tp_1_dw_1",
            Keys = new[]
            {
                new { Name = "company_id", Value = CompanyId },
                new { Name = "purchase_pricing_book_id", Value = PricingBookId },
                new { Name = "supplier_id", Value = SupplierId },
                new { Name = "effective_date", Value = EffectiveDate },
                new { Name = "expiration_date", Value = ExpirationDate },
            },
        },
        new { DataElementName = "TABPAGE_2.tp_2_dw_2", Keys = Array.Empty<object>() },
    },
});

using var response = await client.PostAsync(
    $"{uiServer}/api/v2/transaction/get",
    new StringContent(body, Encoding.UTF8, "application/json"));
response.EnsureSuccessStatusCode();

// Fields come back as {"Name": ..., "Value": ...} entries inside each row's
// Edits array — not as top-level keys.
var values = new Dictionary<string, string>();
using var document = JsonDocument.Parse(await response.Content.ReadAsStringAsync());
if (document.RootElement.TryGetProperty("Transactions", out var transactions))
{
    foreach (var transaction in transactions.EnumerateArray())
    {
        if (!transaction.TryGetProperty("DataElements", out var elements)) continue;
        foreach (var element in elements.EnumerateArray())
        {
            if (!element.TryGetProperty("Rows", out var rows)) continue;
            foreach (var row in rows.EnumerateArray())
            {
                if (!row.TryGetProperty("Edits", out var edits)) continue;
                foreach (var edit in edits.EnumerateArray())
                {
                    var name = edit.GetProperty("Name").GetString();
                    if (name is not null)
                        values[name] = edit.GetProperty("Value").GetString() ?? "";
                }
            }
        }
    }
}

values.TryGetValue("calculation_type", out var calculationType);
Console.WriteLine($"calculation_type: {calculationType}");
// 15 value slots, but only 14 break thresholds and UOMs — tier 15 is the
// catch-all above the last break.
for (var tier = 1; tier <= 15; tier++)
{
    values.TryGetValue($"value{tier}", out var value);
    values.TryGetValue($"break{tier}", out var threshold);
    values.TryGetValue($"uom{tier}", out var uom);
    if (!string.IsNullOrEmpty(value) || !string.IsNullOrEmpty(threshold) || !string.IsNullOrEmpty(uom))
        Console.WriteLine($"  tier {tier,2}: value={value,-12} break={threshold,-10} uom={uom}");
}

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

---

## Related

- [Interactive API](04-Interactive-API.md)
- [Batch Processing Patterns](09-Batch-Processing-Patterns.md)
- [Error Handling](06-Error-Handling.md)
