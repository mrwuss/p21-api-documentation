# Set an Item's Primary Bin or Primary Supplier at a Location

Update an item's primary bin or primary supplier for one stocking location via the `Item` service's nested Form → List → detail pattern — with a mandatory read-back, because the primary-supplier write can silently no-op.

**API:** Transaction (`Item`), Interactive fallback · **Service:** `Item` · **Deep dive:** [Item Service — Nested Location Edits](../03-Transaction-API.md#item-service-nested-location-edits), [Item Service Gotchas](../03-Transaction-API.md#item-service-gotchas), [Worked Example: "Item Issues Detected"](../04-Interactive-API.md#worked-example-item-issues-detected-rule-callback) · **Full schema:** [`definitions/Item.json`](../../definitions/Item.json)

The `Item` service (Item Maintenance window) supports **nested DataElement navigation** that mirrors the UI: select the item, select a location row, then edit that location's detail. It works because the Item window's tabs aren't gated behind row selection — a good template for any nested edit.

## Prerequisites

- P21 credentials — the complete example below authenticates itself; nothing to install but `httpx` (Python) or a bare `net8.0`-or-later console project (C#).
- The item and stocking location already exist.
- **For the primary-supplier write:** the target supplier must already have a *location-level* row (`inventory_supplier_x_loc`) at that location. If it doesn't, the write is a **silent no-op** — see Gotchas.
- OData read access to `inv_mast` and `inv_loc` for the mandatory verification.

## Payload

**Primary bin** (Form → List → Form). `Status: "New"` with populated `Keys` updates the existing keyed record — it does not create a new item.

```json
{
    "Name": "Item",
    "UseCodeValues": false,
    "Transactions": [{
        "Status": "New",
        "DataElements": [
            { "Name": "TABPAGE_1.tp_1_dw_1", "Type": "Form", "Keys": ["item_id"],
              "Rows": [{ "Edits": [ {"Name": "item_id", "Value": "WIDGET-001"} ] }] },
            { "Name": "TABPAGE_17.invloclist", "Type": "List", "Keys": ["location_id"],
              "Rows": [{ "Edits": [ {"Name": "location_id", "Value": "10"} ] }] },
            { "Name": "TABPAGE_18.inv_loc_detail", "Type": "Form", "Keys": ["location_id"],
              "Rows": [{ "Edits": [
                  {"Name": "location_id", "Value": "10"},
                  {"Name": "bin", "Value": "A01-02"}
              ] }] }
        ]
    }]
}
```

**Primary supplier** (Form → List → List). Same window, one level different — swap the third element for the supplier list:

```json
{ "Name": "SUPPLIER_X_LOCATION.supplier_x_location", "Type": "List", "Keys": ["supplier_id"],
  "Rows": [{ "Edits": [
      {"Name": "supplier_id", "Value": "10050"},
      {"Name": "primary_supplier", "Value": "ON"}
  ] }] }
```

What the supplier write does (verified on a 68-item production run): `primary_supplier` maps to `inventory_supplier_x_loc.primary_supplier` (a Y/N flag) — **not** `inv_loc.primary_supplier_id`. Setting it `ON` makes P21 auto-unset the previous primary at that location **and** update `inv_loc.primary_supplier_id` to the new supplier. The flag is the field to **write**; `inv_loc.primary_supplier_id` is the field to **read** when verifying.

## Complete example

Sets the primary supplier, then performs the **mandatory** OData verification of `inv_loc.primary_supplier_id` — `Succeeded = 1` alone proves nothing here (see Gotchas). For the primary-bin variant, swap in the `TABPAGE_18.inv_loc_detail` element from the payload above and verify `inv_loc.primary_bin` the same way.

<!-- tabs -->
```python
"""Set an item's primary supplier at a location, then verify inv_loc over OData."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
ITEM_ID = "WIDGET-001"
LOCATION_ID = "10"
SUPPLIER_ID = "10050"                     # must already have a row at LOCATION_ID
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

    payload = {
        "Name": "Item",
        "UseCodeValues": False,
        "Transactions": [{
            "Status": "New",  # updates the keyed record; does not create a new item
            "DataElements": [
                {"Name": "TABPAGE_1.tp_1_dw_1", "Type": "Form", "Keys": ["item_id"],
                 "Rows": [{"Edits": [{"Name": "item_id", "Value": ITEM_ID}]}]},
                {"Name": "TABPAGE_17.invloclist", "Type": "List", "Keys": ["location_id"],
                 "Rows": [{"Edits": [{"Name": "location_id", "Value": LOCATION_ID}]}]},
                {"Name": "SUPPLIER_X_LOCATION.supplier_x_location", "Type": "List",
                 "Keys": ["supplier_id"],
                 "Rows": [{"Edits": [
                     {"Name": "supplier_id", "Value": SUPPLIER_ID},
                     {"Name": "primary_supplier", "Value": "ON"},
                 ]}]},
            ],
        }],
    }

    resp = client.post(f"{ui_server}/api/v2/transaction",
                       headers=headers, json=payload)
    resp.raise_for_status()
    result = resp.json()
    summary = result["Summary"]
    print(f"Succeeded: {summary['Succeeded']}, Failed: {summary['Failed']}")
    if summary["Failed"] > 0 or summary["Succeeded"] == 0:
        # A hard failure is NOT the silent no-op — read the Messages and stop here.
        for msg in result.get("Messages") or []:
            # watch for 'Unexpected response window: Item Issues Detected'
            print(f"  {msg}")
        raise SystemExit("Write failed")

    # MANDATORY verification (success path) — a silent no-op still reports
    # Succeeded = 1. Write target is the inventory_supplier_x_loc flag;
    # READ inv_loc.primary_supplier_id.
    mast = client.get(
        f"{BASE_URL}/odataservice/odata/table/inv_mast",
        params={"$filter": f"item_id eq '{ITEM_ID}'", "$select": "inv_mast_uid"},
        headers=headers,
    )
    mast.raise_for_status()
    inv_mast_uid = mast.json()["value"][0]["inv_mast_uid"]

    loc = client.get(
        f"{BASE_URL}/odataservice/odata/table/inv_loc",
        params={
            "$filter": f"inv_mast_uid eq {inv_mast_uid} and location_id eq {LOCATION_ID}",
            "$select": "primary_supplier_id",
        },
        headers=headers,
    )
    loc.raise_for_status()
    actual = str(loc.json()["value"][0]["primary_supplier_id"])

    if actual == SUPPLIER_ID:
        print(f"VERIFIED: primary_supplier_id = {actual}")
    else:
        # Most likely cause: no inventory_supplier_x_loc row at this location.
        # Add the location supplier row first, then set the flag again.
        print(f"SILENT NO-OP: primary_supplier_id is {actual}, expected {SUPPLIER_ID}")
```

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string ItemId = "WIDGET-001";
const string LocationId = "10";
const string SupplierId = "10050";     // must already have a row at LocationId
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

static object Element(string name, string type, string key,
    params (string Name, string Value)[] edits) => new
    {
        Name = name,
        Type = type,
        Keys = new[] { key },
        Rows = new object[]
        {
            new { Edits = edits.Select(e => new { e.Name, e.Value }).ToArray() },
        },
    };

var payload = new
{
    Name = "Item",
    UseCodeValues = false,
    Transactions = new object[]
    {
        new
        {
            Status = "New", // updates the keyed record; does not create a new item
            DataElements = new[]
            {
                Element("TABPAGE_1.tp_1_dw_1", "Form", "item_id", ("item_id", ItemId)),
                Element("TABPAGE_17.invloclist", "List", "location_id",
                    ("location_id", LocationId)),
                Element("SUPPLIER_X_LOCATION.supplier_x_location", "List", "supplier_id",
                    ("supplier_id", SupplierId), ("primary_supplier", "ON")),
            },
        },
    },
};

using var resp = await client.PostAsync(
    $"{uiServer}/api/v2/transaction",
    new StringContent(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json"));
resp.EnsureSuccessStatusCode();
using var result = JsonDocument.Parse(await resp.Content.ReadAsStringAsync());
var summary = result.RootElement.GetProperty("Summary");
var succeeded = summary.GetProperty("Succeeded").GetInt32();
var failed = summary.GetProperty("Failed").GetInt32();
Console.WriteLine($"Succeeded: {succeeded}, Failed: {failed}");
if (failed > 0 || succeeded == 0)
{
    // A hard failure is NOT the silent no-op — read the Messages and stop here.
    // Watch for 'Unexpected response window: Item Issues Detected'.
    if (result.RootElement.TryGetProperty("Messages", out var messages))
    {
        Console.Error.WriteLine($"  {messages}");
    }
    return;
}

// MANDATORY verification (success path) — a silent no-op still reports Succeeded = 1.
// Write target is the inventory_supplier_x_loc flag; READ inv_loc.primary_supplier_id.
var invMastUid = (await ODataAsync(client, "inv_mast", $"item_id eq '{ItemId}'",
    "inv_mast_uid"))[0].GetProperty("inv_mast_uid");

var locRows = await ODataAsync(client, "inv_loc",
    $"inv_mast_uid eq {invMastUid} and location_id eq {LocationId}",
    "primary_supplier_id");
var primarySupplier = locRows[0].GetProperty("primary_supplier_id");
var actual = primarySupplier.ValueKind == JsonValueKind.String
    ? primarySupplier.GetString()
    : primarySupplier.ToString();

if (actual == SupplierId)
{
    Console.WriteLine($"VERIFIED: primary_supplier_id = {actual}");
}
else
{
    // Most likely cause: no inventory_supplier_x_loc row at this location.
    // Add the location supplier row first, then set the flag again.
    Console.WriteLine($"SILENT NO-OP: primary_supplier_id is {actual}, expected {SupplierId}");
}

// --- helpers ---------------------------------------------------------------

static async Task<List<JsonElement>> ODataAsync(
    HttpClient client, string table, string filter, string select)
{
    using var response = await client.GetAsync(
        $"{BaseUrl}/odataservice/odata/table/{table}" +
        $"?$filter={Uri.EscapeDataString(filter)}&$select={select}");
    response.EnsureSuccessStatusCode();
    using var doc = JsonDocument.Parse(await response.Content.ReadAsStringAsync());
    return doc.RootElement.GetProperty("value").EnumerateArray()
        .Select(x => x.Clone()).ToList();
}

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

> **Payload files:** bin [JSON](../../examples/payloads/json/set-primary-bin.json) · [XML](../../examples/payloads/xml/set-primary-bin.xml); supplier [JSON](../../examples/payloads/json/set-primary-supplier.json) · [XML](../../examples/payloads/xml/set-primary-supplier.xml) — validator-verified, see [payloads README](../../examples/payloads/README.md).
>
> **End-to-end files** (runnable from the repo with a `.env`, dry-run by default): [`examples/python/recipes/set_primary_bin_supplier.py`](../../examples/python/recipes/set_primary_bin_supplier.py) · [`examples/csharp/Recipes/SetPrimaryBinSupplier.cs`](../../examples/csharp/Recipes/SetPrimaryBinSupplier.cs). The snippet above is self-contained; the files use the repo's shared `common` / `P21Examples.Common` helpers like every other example.

## Gotchas

- **Silent no-op — the big one.** The target supplier must already have a *location-level* row (`inventory_supplier_x_loc`) at that location. If it doesn't, the transaction still returns `Succeeded = 1` but **nothing flips** — there is no row to promote. (P21 allows cutting a PO to a supplier without location setup, so a supplier can appear in PO history yet be absent from the location's supplier list.) **Always verify `inv_loc.primary_supplier_id` after writing** — do not trust `Succeeded`. Fix: add the location supplier row first, then set the flag.
- **Write the flag, read the id.** `primary_supplier` maps to `inventory_supplier_x_loc.primary_supplier` (Y/N), not `inv_loc.primary_supplier_id`; setting it `ON` auto-unsets the previous primary and updates `inv_loc.primary_supplier_id`. Verify against the id.
- **"Item Issues Detected" popup.** Items with data problems return `Unexpected response window: Item Issues Detected` (`w_rule_callback_response`) in the response `Messages`. The Transaction API cannot get past this popup — it effectively answers "No" and discards the change. **Interactive fallback** ([worked example](../04-Interactive-API.md#worked-example-item-issues-detected-rule-callback)): start the session with `ResponseWindowHandlingEnabled: true`; open the `Item` window and set `item_id` on `TABPAGE_1.tp_1_dw_1` — **some items pop the dialog at retrieve time**, blocking the location list, so answer it immediately, not just at save; make your edits; `save()` — a blocked save returns Status 3 with a `windowopened` event carrying the popup's window ID; discover buttons via `GET /v2/tools?windowId={popupId}` (`cb_1` = **"Yes, Proceed Anyway"**, `cb_2` = "No, Cancel") and run `cb_1` via `POST /v2/tools`; the save then commits.
- **Which items trip the rule differs per environment** — it fires on each item's data state. Don't hard-code a fallback list: run transaction-first, verify, and fall back to the Interactive API for whatever didn't stick.
- **`SUPPLIER_X_LOCATION` keying is safe here** — it's keyed by `supplier_id` scoped to the selected location row in the Transaction API. The equivalent *interactive* flow must match rows on both `location_id` and `supplier_id`, because the grid holds every location's rows.
- **Interactive fallback trap — never `select_row` on the detail form itself.** A single-row detail form (e.g. `inv_loc_detail`) is *bound* to the currently-selected parent list row. Sending `PUT /v2/row` against the **detail** datawindow re-selects the *parent* list (row N on the detail = row N on `invloclist`) and **silently flips which record the detail is bound to**, typically to the list's first row — the edit lands on the wrong location while every call reports success. Select only the parent list row, edit the detail directly, and assert the detail shows exactly the intended record before and after the change (abort without saving on mismatch). The Transaction API's nested pattern keys by `location_id` and has no such trap.
- `Status: "New"` with populated `Keys` **updates** the existing keyed record — it does not create a new item.
- **Primary bin has a lighter REST path.** `Locations.list[].PrimaryBin` is writable via the Inventory REST API's GET → modify → PUT (verified across 276 rows in production; the bin must already exist at that location) and handles both of an item's locations in one call — see [11 § Location-Append & Update Gotchas](../11-Inventory-REST-API.md#location-append-update-gotchas-verified-at-scale). The Transaction path in this recipe remains the one to use when you're already in a TAPI batch or need the supplier flag in the same transaction.

## Verify

Not optional for the supplier write — the silent no-op makes read-back the only proof. Resolve `inv_mast_uid` from `item_id`, then read `inv_loc`:

```http
GET /odataservice/odata/table/inv_mast?$filter=item_id eq 'WIDGET-001'&$select=inv_mast_uid
GET /odataservice/odata/table/inv_loc?$filter=inv_mast_uid eq {uid} and location_id eq 10&$select=primary_supplier_id
```

For the primary-bin variant, read back the bin field on the same `inv_loc` row.

> **Credit:** [Alex Westemeier](https://github.com/AWestemeier) — patterns and gotchas verified in production (July 2026).
