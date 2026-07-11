# Set an Item's Primary Bin or Primary Supplier at a Location

Update an item's primary bin or primary supplier for one stocking location via the `Item` service's nested Form → List → detail pattern — with a mandatory read-back, because the primary-supplier write can silently no-op.

**API:** Transaction (`Item`), Interactive fallback · **Service:** `Item` · **Deep dive:** [Item Service — Nested Location Edits](../03-Transaction-API.md#item-service----nested-location-edits), [Item Service Gotchas](../03-Transaction-API.md#item-service-gotchas), [Worked Example: "Item Issues Detected"](../04-Interactive-API.md#worked-example-item-issues-detected-rule-callback) · **Full schema:** [`definitions/Item.json`](../../definitions/Item.json)

The `Item` service (Item Maintenance window) supports **nested DataElement navigation** that mirrors the UI: select the item, select a location row, then edit that location's detail. It works because the Item window's tabs aren't gated behind row selection — a good template for any nested edit.

## Prerequisites

- Bearer token + UI server from the [shared auth helper](README.md#shared-conventions-recipes-dont-repeat-these).
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
      {"Name": "supplier_id", "Value": "20000"},
      {"Name": "primary_supplier", "Value": "ON"}
  ] }] }
```

What the supplier write does (verified on a 68-item production run): `primary_supplier` maps to `inventory_supplier_x_loc.primary_supplier` (a Y/N flag) — **not** `inv_loc.primary_supplier_id`. Setting it `ON` makes P21 auto-unset the previous primary at that location **and** update `inv_loc.primary_supplier_id` to the new supplier. The flag is the field to **write**; `inv_loc.primary_supplier_id` is the field to **read** when verifying.

## Complete example

Sets the primary supplier, then performs the **mandatory** OData verification of `inv_loc.primary_supplier_id` — `Succeeded = 1` alone proves nothing here (see Gotchas). For the primary-bin variant, swap in the `TABPAGE_18.inv_loc_detail` element from the payload above and verify `inv_loc.primary_bin` the same way.

<!-- tabs -->
```python
import httpx

BASE_URL = "https://play.p21server.com"
token, ui_server, headers = p21_auth(BASE_URL, "api_user", "password")

ITEM_ID = "WIDGET-001"
LOCATION_ID = "10"
SUPPLIER_ID = "20000"

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

resp = httpx.post(f"{ui_server}/api/v2/transaction",
                  headers=headers, json=payload, verify=False, timeout=120)
resp.raise_for_status()
result = resp.json()
summary = result["Summary"]
print(f"Succeeded: {summary['Succeeded']}, Failed: {summary['Failed']}")
if summary["Failed"] > 0 or summary["Succeeded"] == 0:
    # A hard failure is NOT the silent no-op — read the Messages and stop here.
    for msg in result.get("Messages") or []:
        print(f"  {msg}")  # watch for 'Unexpected response window: Item Issues Detected'
    raise SystemExit("Write failed")

# MANDATORY verification (success path) — a silent no-op still reports Succeeded = 1.
# Write target is the inventory_supplier_x_loc flag; READ inv_loc.primary_supplier_id.
mast = httpx.get(
    f"{BASE_URL}/odataservice/odata/table/inv_mast",
    params={"$filter": f"item_id eq '{ITEM_ID}'", "$select": "inv_mast_uid"},
    headers=headers, verify=False,
)
mast.raise_for_status()
inv_mast_uid = mast.json()["value"][0]["inv_mast_uid"]

loc = httpx.get(
    f"{BASE_URL}/odataservice/odata/table/inv_loc",
    params={
        "$filter": f"inv_mast_uid eq {inv_mast_uid} and location_id eq {LOCATION_ID}",
        "$select": "primary_supplier_id",
    },
    headers=headers, verify=False,
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
var session = await P21Session.CreateAsync(
    "https://play.p21server.com", "api_user", "password");

const string ItemId = "WIDGET-001";
const string LocationId = "10";
const string SupplierId = "20000";

JObject Element(string name, string type, string key, params (string Name, string Value)[] edits) =>
    new JObject
    {
        ["Name"] = name, ["Type"] = type, ["Keys"] = new JArray(key),
        ["Rows"] = new JArray(new JObject
        {
            ["Edits"] = new JArray(edits.Select(e =>
                new JObject { ["Name"] = e.Name, ["Value"] = e.Value })),
        }),
    };

var payload = new JObject
{
    ["Name"] = "Item",
    ["UseCodeValues"] = false,
    ["Transactions"] = new JArray(new JObject
    {
        ["Status"] = "New", // updates the keyed record; does not create a new item
        ["DataElements"] = new JArray
        {
            Element("TABPAGE_1.tp_1_dw_1", "Form", "item_id", ("item_id", ItemId)),
            Element("TABPAGE_17.invloclist", "List", "location_id", ("location_id", LocationId)),
            Element("SUPPLIER_X_LOCATION.supplier_x_location", "List", "supplier_id",
                ("supplier_id", SupplierId), ("primary_supplier", "ON")),
        },
    }),
};

var resp = await session.Http.PostAsync(
    $"{session.UiServer}/api/v2/transaction",
    new StringContent(payload.ToString(), Encoding.UTF8, "application/json"));
resp.EnsureSuccessStatusCode();
var result = JObject.Parse(await resp.Content.ReadAsStringAsync());
var summary = result["Summary"]!;
Console.WriteLine($"Succeeded: {summary["Succeeded"]}, Failed: {summary["Failed"]}");
if ((int)summary["Failed"]! > 0 || (int)summary["Succeeded"]! == 0)
{
    // A hard failure is NOT the silent no-op — read the Messages and stop here.
    foreach (var msg in result["Messages"] as JArray ?? new JArray())
        Console.WriteLine($"  {msg}"); // watch for 'Unexpected response window: Item Issues Detected'
    return;
}

// MANDATORY verification (success path) — a silent no-op still reports Succeeded = 1.
// Write target is the inventory_supplier_x_loc flag; READ inv_loc.primary_supplier_id.
var mastResp = await session.Http.GetAsync(
    "https://play.p21server.com/odataservice/odata/table/inv_mast" +
    $"?$filter=item_id eq '{ItemId}'&$select=inv_mast_uid");
mastResp.EnsureSuccessStatusCode();
var invMastUid = (string)JObject.Parse(
    await mastResp.Content.ReadAsStringAsync())["value"]![0]!["inv_mast_uid"]!;

var locResp = await session.Http.GetAsync(
    "https://play.p21server.com/odataservice/odata/table/inv_loc" +
    $"?$filter=inv_mast_uid eq {invMastUid} and location_id eq {LocationId}" +
    "&$select=primary_supplier_id");
locResp.EnsureSuccessStatusCode();
var actual = (string?)JObject.Parse(
    await locResp.Content.ReadAsStringAsync())["value"]![0]!["primary_supplier_id"];

if (actual == SupplierId)
    Console.WriteLine($"VERIFIED: primary_supplier_id = {actual}");
else
    // Most likely cause: no inventory_supplier_x_loc row at this location.
    // Add the location supplier row first, then set the flag again.
    Console.WriteLine($"SILENT NO-OP: primary_supplier_id is {actual}, expected {SupplierId}");
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

## Verify

Not optional for the supplier write — the silent no-op makes read-back the only proof. Resolve `inv_mast_uid` from `item_id`, then read `inv_loc`:

```http
GET /odataservice/odata/table/inv_mast?$filter=item_id eq 'WIDGET-001'&$select=inv_mast_uid
GET /odataservice/odata/table/inv_loc?$filter=inv_mast_uid eq {uid} and location_id eq 10&$select=primary_supplier_id
```

For the primary-bin variant, read back the bin field on the same `inv_loc` row.

> **Credit:** [Alex Westemeier](https://github.com/AWestemeier) — patterns and gotchas verified in production (July 2026).
