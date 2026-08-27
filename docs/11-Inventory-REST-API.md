# Inventory REST API

> **Disclaimer:** This is unofficial, community-created documentation for Epicor Prophet 21 APIs. It is not affiliated with, endorsed by, or supported by Epicor Software Corporation. All product names, trademarks, and registered trademarks are property of their respective owners. Use at your own risk.

---

> **Added February 2026** — Originally contributed by [@sibinfrancisaj](https://github.com/sibinfrancisaj). PUT/POST behavior verified via live API testing.

---

## Overview

P21 provides inventory item CRUD at `/api/inventory/parts` (backed by `inv_mast`). This is **part of the same REST API** as the [`/api/entity/` endpoints](05-Entity-API.md) — a different **endpoint family** with its own base path and behavior, documented separately for readability only. (In Epicor's naming, "Entity API" is an umbrella term covering the whole REST API plus the eCommerce SOAP API — see [Terminology](05-Entity-API.md#terminology-epicors-naming-july-2026).)

The Inventory REST API is significant because it provides:
- **Read access** to `inv_loc` (inventory location) records via extended properties
- **Write access** to append new `inv_loc` and `inventory_supplier` records, or update existing ones, via PUT
- Direct item-level CRUD without sessions or stateful workflows

### When to Use

- Reading inventory item details including location-specific data (GL accounts, costs, stock levels)
- Adding existing items to new companies/locations (multi-company workflows)
- Creating new inventory items
- Checking item availability and pricing

### Limitations

- **No `/new` template** — `GET /api/inventory/parts/new` returns 404
- **List endpoint hangs** — `GET /api/inventory/parts/` without `$query` tries to load all items and times out
- **Not all items accessible** — Some items in `inv_mast` (via OData) return 404 from this API

---

## Base URL

```http
https://{hostname}/api/inventory/parts
```

Example: `https://play.p21server.com/api/inventory/parts`

---

## Endpoints

| Method | Path | Description | Verified |
|--------|------|-------------|----------|
| `GET` | `/api/inventory/parts/ping` | Health check | Yes |
| `GET` | `/api/inventory/parts/{ItemId}` | Get single item | Yes |
| `PUT` | `/api/inventory/parts/{ItemId}` | Update item (append locations/suppliers) | Yes |
| `POST` | `/api/inventory/parts` | Create new item (see [307 redirect note](#4-post-returns-307-redirect)) | Yes |
| `GET` | `/api/inventory/parts/{ItemId}/availability` | Item availability | Not tested |
| `GET` | `/api/inventory/parts/{ItemId}/v2/price` | Single item pricing (V2) | Yes |
| `GET` | `/api/inventory/v2/parts/v2/price/{ItemId}` | Single item pricing (alternative path) | Yes |
| `POST` | `/api/inventory/parts/itemsAvailability` | Batch availability | Not tested |
| `POST` | `/api/inventory/parts/prices` | Batch pricing (JSON or XML, see [Batch Pricing](#batch-pricing)) | Yes |
| `POST` | `/api/inventory/v2/parts/prices` | Batch pricing (alternative path, identical behavior) | Yes |

---

## Comparison with Entity API

Both endpoint families belong to the **same REST API** (see [Terminology — Epicor's Naming](05-Entity-API.md#terminology-epicors-naming-july-2026)); this table contrasts how the two families behave:

| Feature | `/api/entity/` endpoints | `/api/inventory/parts` |
|---------|-----------|-------------------|
| Base path | `/api/entity/{resource}` | `/api/inventory/parts` |
| Key format | Composite (`ACME_10`) or numeric | String ItemId (`WIDGET-001`) |
| `/new` template | Yes (customers, vendors, contacts) | **No** — "new" is treated as an item ID |
| List endpoint | Works (returns 307 redirect) | **Hangs** without filtering — needs `$query` |
| Record accessibility | All records accessible | Some items return 404 despite existing in `inv_mast` |
| Write support | PUT for updates | PUT for updates, POST for creates |

---

## Reading Items

### Basic GET

<!-- tabs -->

**Python**

```python
"""Read a single inventory item via the Inventory REST API."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
ITEM_ID = "WIDGET-001"                    # item to look up
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

    resp = client.get(f"{BASE_URL}/api/inventory/parts/{ITEM_ID}", headers=headers)
    resp.raise_for_status()
    item = resp.json()
    print(f"{item['ItemId']}: {item['ItemDesc']}")
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
const string ItemId = "WIDGET-001";                     // item to look up
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

var resp = await client.GetAsync($"{BaseUrl}/api/inventory/parts/{ItemId}");
resp.EnsureSuccessStatusCode();
var item = JsonDocument.Parse(await resp.Content.ReadAsStringAsync()).RootElement;
Console.WriteLine($"{item.GetProperty("ItemId")}: {item.GetProperty("ItemDesc")}");

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

// Some middleware answers this endpoint in XML even when asked for JSON.
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

**Sample Response:**

```json
{
    "ItemId": "WIDGET-001",
    "ItemDesc": "Standard Widget Assembly",
    "Delete": "N",
    "Weight": 0.0,
    "NetWeight": 0.0,
    "ClassId1": "",
    "ClassId2": "",
    "Serialized": "N",
    "ShortCode": "",
    "TrackLots": "N",
    "Price1": 0.0,
    "Price2": 0.0,
    "ExtendedDesc": "",
    "DefaultSellingUnit": "1",
    "DefaultPurchasingUnit": "1",
    "InvMastUid": 15,
    "Keywords": "Standard Widget Assembly",
    "BaseUnit": "1",
    "UserDefinedFields": {},
    "ObjectName": "inv_mast"
}
```

> **Note:** Response truncated for brevity. Full response contains 60+ fields from the `inv_mast` table. Without `extendedproperties`, all child collections (Locations, Suppliers, etc.) are `null`.

### GET with Extended Properties

Use `extendedproperties` to include child collections (`inv_loc`, `inventory_supplier`, etc.):

```http
GET /api/inventory/parts/WIDGET-001?extendedproperties=*
Authorization: Bearer <ACCESS_TOKEN>
```

Or fetch only what you need:

```http
GET /api/inventory/parts/WIDGET-001?extendedproperties=Locations,Suppliers,LocationSuppliers,UnitsOfMeasure
Authorization: Bearer <ACCESS_TOKEN>
```

<!-- tabs -->

**Python**

```python
"""Read an inventory item plus its inv_loc, supplier, and UOM child records."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
ITEM_ID = "WIDGET-001"                    # item to look up
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

    resp = client.get(
        f"{BASE_URL}/api/inventory/parts/{ITEM_ID}",
        headers=headers,
        params={"extendedproperties": "*"},
    )
    resp.raise_for_status()
    item = resp.json()

    # Access nested Locations (inv_loc data)
    if item.get("Locations"):
        for loc in item["Locations"]["list"]:
            print(f"Loc: {loc['LocationId']}, Qty: {loc['QtyOnHand']}")
```

**C#**

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string ItemId = "WIDGET-001";                     // item to look up
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

var resp = await client.GetAsync($"{BaseUrl}/api/inventory/parts/{ItemId}?extendedproperties=*");
resp.EnsureSuccessStatusCode();
var item = JsonNode.Parse(await resp.Content.ReadAsStringAsync())!;

// Access nested Locations (inv_loc data)
var locations = item["Locations"]?["list"]?.AsArray();
if (locations != null)
{
    foreach (var loc in locations)
    {
        Console.WriteLine($"Loc: {loc!["LocationId"]}, Qty: {loc["QtyOnHand"]}");
    }
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

// Some middleware answers this endpoint in XML even when asked for JSON.
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

With `extendedproperties=*`, child collections are populated as `{"list": [...]}` objects:

```json
{
    "ItemId": "WIDGET-001",
    "ItemDesc": "Standard Widget Assembly",
    "InvMastUid": 15,
    "ObjectName": "inv_mast",
    "Locations": {
        "list": [
            {
                "ItemId": "WIDGET001",
                "LocationId": 1,
                "QtyOnHand": 0.0,
                "CompanyId": "ACME",
                "GlAccountNo": "1300-000",
                "RevenueAccountNo": "4000-000",
                "CosAccountNo": "5000-000",
                "Sellable": "Y",
                "Stockable": "Y",
                "ProductGroupId": "MISC",
                "MovingAverageCost": 0.0,
                "StandardCost": 0.0,
                "ReplenishmentMethod": "Min/Max",
                "ObjectName": "inv_loc"
            }
        ]
    },
    "Suppliers": {
        "list": [
            {
                "ItemId": "WIDGET-001",
                "SupplierId": 10,
                "SupplierPartNo": "",
                "ListPrice": 0.0,
                "Cost": 0.0,
                "ObjectName": "inventory_supplier"
            }
        ]
    },
    "UnitsOfMeasure": {
        "list": [
            {
                "ItemId": "WIDGET-001",
                "UnitOfMeasure": "1",
                "UnitSize": 1.0,
                "ObjectName": "item_uom"
            }
        ]
    },
    "LocationSuppliers": { "list": [] },
    "Lot": null,
    "LocationMSPs": { "list": [] },
    "Service": null,
    "ServiceContracts": null,
    "Notes": { "list": [] },
    "MSDS": null,
    "RestrictedClasses": null,
    "AltCodes": { "list": [] }
}
```

> **Significant:** The `Locations` extended property returns full `inv_loc` records including GL accounts, product groups, costs, and all inventory location fields. This provides read access to `inv_loc` data that is difficult to obtain through other APIs.

### Extended Properties Reference

| Property | ObjectName | Description |
|----------|-----------|-------------|
| `Locations` | `inv_loc` | Warehouse stock levels, GL accounts, costs, product groups |
| `Suppliers` | `inventory_supplier` | Vendor/supplier information, costs, lead times |
| `UnitsOfMeasure` | `item_uom` | UOM definitions and conversion factors |
| `LocationSuppliers` | `inventory_supplier_x_loc` | Supplier-location specific data |
| `Lot` | — | Lot tracking information |
| `LocationMSPs` | `inv_loc_msp` | Location-specific pricing |
| `Service` | — | Service-related data |
| `ServiceContracts` | — | Linked service contracts |
| `Notes` | — | Item notes |
| `MSDS` | — | Material Safety Data Sheets |
| `RestrictedClasses` | — | Class restrictions |
| `AltCodes` | `alternate_code` | Alternate item codes |

### Data Fields (Partial)

Key fields from `GET /api/inventory/parts/{ItemId}` (maps to `inv_mast` table):

| Field | Type | Description |
|-------|------|-------------|
| `ItemId` | string | Item identifier |
| `ItemDesc` | string | Item description |
| `ExtendedDesc` | string | Extended description |
| `Keywords` | string | Search keywords |
| `ShortCode` | string | Short code |
| `ClassId1`...`ClassId5` | string | Classification fields |
| `Weight` / `NetWeight` | decimal | Item weight |
| `Price1`...`Price10` | decimal | Base pricing structure |
| `DefaultSellingUnit` | string | Default selling UOM |
| `DefaultPurchasingUnit` | string | Default purchasing UOM |
| `BaseUnit` | string | Base unit of measure |
| `TrackLots` | string | Lot tracking flag (Y/N) |
| `Serialized` | string | Serialized flag (Y/N) |
| `InvMastUid` | int | Internal unique identifier |
| `DefaultPurchaseDiscGroup` | string | Default purchase discount group (item-level) |
| `DefaultSalesDiscountGroup` | string | Default sales discount group (item-level) |
| `UserDefinedFields` | object | User-defined fields |
| `ObjectName` | string | Always `"inv_mast"` |

### Location-Level Fields (inv_loc)

Key fields on `inv_loc` records within `Locations.list` (requires `extendedproperties=Locations`):

| Field | Type | Description |
|-------|------|-------------|
| `LocationId` | int | Warehouse/location identifier |
| `CompanyId` | string | Company the location belongs to |
| `ProductGroupId` | string | Product group for this location |
| `Sellable` | string | Whether item is sellable at this location (Y/N) |
| `Stockable` | string | Whether item is stockable at this location (Y/N) |
| `GlAccountNo` | string | GL inventory account |
| `RevenueAccountNo` | string | GL revenue account |
| `CosAccountNo` | string | GL cost-of-sale account |
| `PurchaseDiscountGroup` | string | Purchase discount group (location-level) |
| `SalesDiscountGroup` | string | Sales discount group (location-level) |
| `QtyOnHand` | decimal | Current quantity on hand |
| `MovingAverageCost` | decimal | Moving average cost |
| `StandardCost` | decimal | Standard cost |
| `ReplenishmentMethod` | string | Replenishment method (e.g., "Min/Max") |
| `Delete` | string | Soft-delete flag (Y/N) — see [Location Soft-Delete](#5-location-soft-delete-via-delete-flag) |
| `ObjectName` | string | Always `"inv_loc"` |

> **Note:** `PurchaseDiscountGroup` and `SalesDiscountGroup` on `inv_loc` are **separate** from the item-level `DefaultPurchaseDiscGroup` and `DefaultSalesDiscountGroup` on `inv_mast`. Values can differ between levels — the location-level fields override the item-level defaults for that specific location.

---

## Writing Items

### PUT — Update Existing Item

`PUT /api/inventory/parts/{ItemId}` accepts the full item payload and processes changes including appended child records and modifications to existing records.

**Verified behavior:**
- Sending back the same data unchanged returns 200 (idempotent)
- Appending new `inv_loc` records in `Locations.list` triggers P21 business logic validation (company validation, GL account checks)
- Modifying fields on existing `inv_loc` records applies the changes (see [Updating Existing Location Fields](#updating-existing-location-fields))
- Invalid data produces descriptive P21 error messages

### POST — Create New Item

`POST /api/inventory/parts` creates a new inventory item. If the `ItemId` already exists, P21 returns an error:

```http
POST /api/inventory/parts
Authorization: Bearer <ACCESS_TOKEN>
Content-Type: application/json

{
    "ItemId": "WIDGET-001",
    "ItemDesc": "Standard Widget Assembly"
}
```

**Error Response (duplicate item):**

```json
{
    "ErrorMessage": "Error updating WIDGET-001: Error updating inv_mast: The proposed item ID already exists in the database.",
    "ErrorType": "P21.Common.Exceptions.Prophet21Exception"
}
```

This happens because `inv_mast` (Inventory Master) is the global definition of the item. The `ItemId` must be unique across all companies. Company-specific data lives in `inv_loc` and `inventory_supplier`, which are child records of `inv_mast`.

---

## Multi-Company Inventory Workflow

> Contributed by [@sibinfrancisaj](https://github.com/sibinfrancisaj). Append mechanism verified via live API testing (February 2026).

In a multi-company P21 environment, inventory items are shared across companies but require distinct configuration (Locations, Suppliers, GL accounts) for each company. Since `ItemId` is globally unique, you cannot `POST` an existing item to add it to a new company — you must **append** the new company's data to the existing item via `PUT`.

### The Pattern: GET → Append → PUT

1. **GET** the existing item with `extendedproperties=Locations,Suppliers,LocationSuppliers,UnitsOfMeasure`
2. **Append** new Location and Supplier objects to the existing `list` arrays
3. **PUT** the updated payload back to the API

### Step 1: GET the Item

```http
GET /api/inventory/parts/WIDGET-001?extendedproperties=Locations,Suppliers,LocationSuppliers,UnitsOfMeasure
Authorization: Bearer <ACCESS_TOKEN>
```

### Step 2: Append New Company Data

Add the new company's Location and Supplier records to the existing arrays. **Do not remove existing entries** — include all original records plus the new ones.

### Step 3: PUT the Updated Payload

```http
PUT /api/inventory/parts/WIDGET-001
Authorization: Bearer <ACCESS_TOKEN>
Content-Type: application/json

{
    "ItemId": "WIDGET-001",
    "InvMastUid": 15,
    "ItemDesc": "Standard Widget Assembly",
    "ObjectName": "inv_mast",
    "Locations": {
        "list": [
            {
                "ItemId": "WIDGET-001",
                "LocationId": 1,
                "CompanyId": "ACME",
                "ObjectName": "inv_loc"
            },
            {
                "ItemId": "WIDGET-001",
                "LocationId": 2,
                "CompanyId": "ACME-WEST",
                "GlAccountNo": "1300-000",
                "RevenueAccountNo": "4000-000",
                "CosAccountNo": "5000-000",
                "Sellable": "Y",
                "Stockable": "Y",
                "ObjectName": "inv_loc"
            }
        ]
    },
    "Suppliers": {
        "list": [
            {
                "ItemId": "WIDGET-001",
                "SupplierId": 10,
                "ObjectName": "inventory_supplier"
            },
            {
                "ItemId": "WIDGET-001",
                "SupplierId": 20,
                "DivisionId": 2,
                "LeadTimeDays": 5,
                "ObjectName": "inventory_supplier"
            }
        ]
    }
}
```

On success, the API returns the updated item object (HTTP 200).

### Verified Error Messages

These errors confirm the API processes appended records through P21 business logic:

**Invalid company:**
```json
{
    "ErrorMessage": "Error updating WIDGET-001: Error updating inv_mast: The company \"FAKE99\" could not be retrieved. - Potential reasons: 1)The company does not exist. 2)The company has been deleted.",
    "ErrorType": "P21.Common.Exceptions.Prophet21Exception"
}
```

**Invalid GL account for company:**
```json
{
    "ErrorMessage": "Error updating WIDGET-001: Error updating inv_mast: This account doesn't exist for company ACME-WEST.",
    "ErrorType": "P21.Common.Exceptions.Prophet21Exception"
}
```

These errors prove the API is actively processing the appended Location records — validating the CompanyId and GL accounts against P21's chart of accounts.

---

## Location-Append & Update Gotchas (Verified at Scale)

Findings from a production run appending **138 items × 2 locations** (276 rows) through `PUT /api/inventory/parts/{ItemId}` with the GET → append → PUT pattern, each verified by SQL read-back ([issue #110](https://github.com/mrwuss/p21-api-documentation/issues/110) and [#112](https://github.com/mrwuss/p21-api-documentation/issues/112), 2026-08-14):

1. **`LocationSuppliers` append works — and sets the location's primary supplier.** Appending an `inventory_supplier_x_loc` object alongside the appended `Locations` entry in the *same* PUT creates the supplier-x-loc row **and** sets `inv_loc.primary_supplier_id`:

   ```json
   {"ItemId": "...", "LocationId": 10, "SupplierId": 64284,
    "PrimarySupplier": "Y", "ObjectName": "inventory_supplier_x_loc"}
   ```

   This is a simpler alternative to the Transaction API's `SUPPLIER_X_LOCATION` flag pattern and avoids its silent-no-op gotcha — the same PUT can also append the item-level `Suppliers` entry when the item–supplier link doesn't exist yet (verified: one call created `inventory_supplier` + the x_loc row + the primary flag together).

2. **GL accounts are required when the target location has no defaults.** "GL auto-derives" is true only when the location/company has an `inventory_defaults` row. Appending to a freshly created location without one fails with `Required value missing for Revenue Account (for Inventory Location) on row N`. Two fixes: create the defaults row first via the [ItemDefaults Transaction service](03-Transaction-API.md#itemdefaults-service-per-location-item-defaults), or always send `GlAccountNo`/`RevenueAccountNo`/`CosAccountNo` copied from a same-branch template row.

3. **Kit items reject `Buy: "Y"` on appended locations** — `Error updating inv_mast: A Kit item cannot be marked as a Buy item.` — even when the item's older `inv_loc` rows carry `buy = Y` (legacy data). Omit `Buy`/`Make` for kit/assembly items and let P21 default them.

4. **`ReplenishmentMethod: "OP/OQ"` requires a positive order quantity.** Copying an OP/OQ template without `order_quantity` fails with `The order quantity must be greater than zero when using the order point/order quantity inventory method... Invalid datawindow row specified`. Fall back to `Min/Max` on appended rows.

5. **Transient 500s happen at scale.** One item of 138 failed with an opaque `Exception has been thrown by the target of an invocation` and succeeded unchanged on retry. Bulk scripts should retry once before reporting failure.

6. **`PrimaryBin` is writable on `Locations` objects.** GET → modify → PUT of `Locations.list[].PrimaryBin` (a bin-id string) persists to `inv_loc.primary_bin` — verified across all 276 rows. This complements the Transaction API primary-bin path and handles both of an item's locations in one PUT. **The bin must already exist at that location** (create bins — and on a fresh location, their zones first — per [PutawayZone/PickZone](03-Transaction-API.md#putawayzone-pickzone-services-creating-bin-zones) + [create-bins](recipes/create-bins.md)).

Also confirmed on appended `Locations` entries: `Stockable`, `Sellable`, `ProductGroupId`, `SalesDiscountGroup`, `PurchaseDiscountGroup`, `TaxGroupId`, `TrackBins`, `ReplenishmentMethod`, and `ReplenishmentLocation` are all honored — and **re-PUT with an already-present location is a safe no-op**, so bulk runs are idempotent and re-runnable.

## Updating Existing Location Fields

The GET -> Modify -> PUT pattern also works for **updating fields on existing `inv_loc` records**, not just appending new ones.

**Verified writable fields:** `Sellable`, `ProductGroupId`, `PurchaseDiscountGroup`, `SalesDiscountGroup`, `ReplenishmentLocation`, `PrimaryBin` (see [Location-Append & Update Gotchas](#location-append-update-gotchas-verified-at-scale) — `PrimaryBin` verified across 276 rows; the bin must already exist at that location)

This API is the recommended path for `inv_loc` modifications generally: the Interactive API's Item window keeps its location GL account fields (TABPAGE_24) **read-only**, so they cannot be edited there either.

P21 validates changed values through business logic. For example, setting an invalid `ProductGroupId` returns:

```json
{
    "ErrorMessage": "Error updating WIDGET-001: Error updating inv_mast: Product group ID does not exist for this company ID.",
    "ErrorType": "P21.Common.Exceptions.Prophet21Exception"
}
```

### Example: Update Location Fields

<!-- tabs -->

**Python**

```python
"""GET -> modify -> PUT existing inv_loc fields, then re-GET to confirm the write."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
ITEM_ID = "WIDGET-001"                    # item to update
TARGET_LOCATION_ID = 1                    # inv_loc.LocationId to modify
TARGET_COMPANY_ID = "ACME"                # inv_loc.CompanyId to modify
EXTENDED_PROPS = "Locations,Suppliers,LocationSuppliers,UnitsOfMeasure"
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

    # 1. GET current item with Locations
    resp = client.get(
        f"{BASE_URL}/api/inventory/parts/{ITEM_ID}",
        headers=headers,
        params={"extendedproperties": EXTENDED_PROPS},
    )
    resp.raise_for_status()
    item = resp.json()

    # 2. Modify fields on the existing location -- do not drop the other records
    for loc in item["Locations"]["list"]:
        if loc["LocationId"] == TARGET_LOCATION_ID and loc["CompanyId"] == TARGET_COMPANY_ID:
            loc["Sellable"] = "N"
            loc["ProductGroupId"] = "MISC"
            loc["PurchaseDiscountGroup"] = "BULK"
            loc["SalesDiscountGroup"] = "RETAIL"
            break

    # 3. PUT the whole item back
    resp = client.put(f"{BASE_URL}/api/inventory/parts/{ITEM_ID}", headers=headers, json=item)
    resp.raise_for_status()
    print(f"PUT status: {resp.status_code}")

    # 4. Re-GET to prove what actually landed -- HTTP 200 alone does not confirm a write
    resp = client.get(
        f"{BASE_URL}/api/inventory/parts/{ITEM_ID}",
        headers=headers,
        params={"extendedproperties": EXTENDED_PROPS},
    )
    resp.raise_for_status()
    after = resp.json()
    for loc in after["Locations"]["list"]:
        if loc["LocationId"] == TARGET_LOCATION_ID and loc["CompanyId"] == TARGET_COMPANY_ID:
            print(
                f"Sellable={loc['Sellable']} ProductGroupId={loc['ProductGroupId']} "
                f"PurchaseDiscountGroup={loc['PurchaseDiscountGroup']} "
                f"SalesDiscountGroup={loc['SalesDiscountGroup']}"
            )
            break
```

**C#**

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string ItemId = "WIDGET-001";                     // item to update
const int TargetLocationId = 1;                         // inv_loc.LocationId to modify
const string TargetCompanyId = "ACME";                  // inv_loc.CompanyId to modify
const string ExtendedProps = "Locations,Suppliers,LocationSuppliers,UnitsOfMeasure";
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

// 1. GET current item with Locations
var getUrl = $"{BaseUrl}/api/inventory/parts/{ItemId}?extendedproperties={ExtendedProps}";
var getResp = await client.GetAsync(getUrl);
getResp.EnsureSuccessStatusCode();
var item = JsonNode.Parse(await getResp.Content.ReadAsStringAsync())!;

// 2. Modify fields on the existing location -- do not drop the other records
var locations = item["Locations"]!["list"]!.AsArray();
var target = locations.FirstOrDefault(
    l => (int)l!["LocationId"]! == TargetLocationId && (string)l["CompanyId"]! == TargetCompanyId);
if (target != null)
{
    target["Sellable"] = "N";
    target["ProductGroupId"] = "MISC";
    target["PurchaseDiscountGroup"] = "BULK";
    target["SalesDiscountGroup"] = "RETAIL";
}

// 3. PUT the whole item back
var putContent = new StringContent(item.ToJsonString(), Encoding.UTF8, "application/json");
var putResp = await client.PutAsync($"{BaseUrl}/api/inventory/parts/{ItemId}", putContent);
putResp.EnsureSuccessStatusCode();
Console.WriteLine($"PUT status: {(int)putResp.StatusCode}");

// 4. Re-GET to prove what actually landed -- HTTP 200 alone does not confirm a write
var afterResp = await client.GetAsync(getUrl);
afterResp.EnsureSuccessStatusCode();
var after = JsonNode.Parse(await afterResp.Content.ReadAsStringAsync())!;
var afterTarget = after["Locations"]!["list"]!.AsArray().FirstOrDefault(
    l => (int)l!["LocationId"]! == TargetLocationId && (string)l["CompanyId"]! == TargetCompanyId);
if (afterTarget != null)
{
    Console.WriteLine(
        $"Sellable={afterTarget["Sellable"]} ProductGroupId={afterTarget["ProductGroupId"]} " +
        $"PurchaseDiscountGroup={afterTarget["PurchaseDiscountGroup"]} " +
        $"SalesDiscountGroup={afterTarget["SalesDiscountGroup"]}");
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

// Some middleware answers this endpoint in XML even when asked for JSON.
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

> **Important:** Always include **all** existing child records (Locations, Suppliers, etc.) in the PUT payload. Omitting records may cause P21 to remove them.

---

## Minimum Create Payload

`POST /api/inventory/parts` requires a minimal set of fields. P21 auto-derives GL accounts from `ProductGroupId` + `LocationId`, so you do not need to specify them explicitly.

**Required fields:**

- `ItemId` (string, unique across all companies)
- `ItemDesc` (string, **max 40 characters** — see [Common Issues](#3-itemdesc-max-40-characters))
- `Locations` with at least one entry: `LocationId` + `ProductGroupId` (P21 infers `CompanyId` from the location if omitted)
- `Suppliers` with at least one entry: `SupplierId` + `DivisionId`
- `LocationSuppliers` linking the location and supplier: `LocationId` + `SupplierId` + `PrimarySupplier`

<!-- tabs -->

**Python**

```python
"""Create a new inventory item with the minimum required fields, then re-GET it."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
NEW_ITEM_ID = "WIDGET-002"                # must not already exist in inv_mast
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

    payload = {
        "ItemId": NEW_ITEM_ID,
        "ItemDesc": "Small Widget Assembly",
        "Locations": {
            "list": [
                {
                    "LocationId": 1,
                    "ProductGroupId": "MISC",
                    "ObjectName": "inv_loc",
                }
            ]
        },
        "Suppliers": {
            "list": [
                {
                    "SupplierId": 10,
                    "DivisionId": 1,
                    "ObjectName": "inventory_supplier",
                }
            ]
        },
        "LocationSuppliers": {
            "list": [
                {
                    "LocationId": 1,
                    "SupplierId": 10,
                    "PrimarySupplier": "Y",
                    "ObjectName": "inventory_supplier_x_loc",
                }
            ]
        },
        "ObjectName": "inv_mast",
    }

    # POST returns 307 without a trailing slash -- see "POST Returns 307 Redirect" below
    resp = client.post(f"{BASE_URL}/api/inventory/parts/", headers=headers, json=payload)
    resp.raise_for_status()
    created = resp.json()
    print(f"Created: {created['ItemId']}")

    # Re-GET to confirm what actually landed -- HTTP 200 alone does not confirm a write
    resp = client.get(f"{BASE_URL}/api/inventory/parts/{NEW_ITEM_ID}", headers=headers)
    resp.raise_for_status()
    confirmed = resp.json()
    print(f"Confirmed: {confirmed['ItemId']}: {confirmed['ItemDesc']}")
```

**C#**

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string NewItemId = "WIDGET-002";                  // must not already exist in inv_mast
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

var payload = new JsonObject
{
    ["ItemId"] = NewItemId,
    ["ItemDesc"] = "Small Widget Assembly",
    ["ObjectName"] = "inv_mast",
    ["Locations"] = new JsonObject
    {
        ["list"] = new JsonArray
        {
            new JsonObject
            {
                ["LocationId"] = 1,
                ["ProductGroupId"] = "MISC",
                ["ObjectName"] = "inv_loc",
            }
        }
    },
    ["Suppliers"] = new JsonObject
    {
        ["list"] = new JsonArray
        {
            new JsonObject
            {
                ["SupplierId"] = 10,
                ["DivisionId"] = 1,
                ["ObjectName"] = "inventory_supplier",
            }
        }
    },
    ["LocationSuppliers"] = new JsonObject
    {
        ["list"] = new JsonArray
        {
            new JsonObject
            {
                ["LocationId"] = 1,
                ["SupplierId"] = 10,
                ["PrimarySupplier"] = "Y",
                ["ObjectName"] = "inventory_supplier_x_loc",
            }
        }
    }
};

// POST returns 307 without a trailing slash -- see "POST Returns 307 Redirect" below
var content = new StringContent(payload.ToJsonString(), Encoding.UTF8, "application/json");
var resp = await client.PostAsync($"{BaseUrl}/api/inventory/parts/", content);
resp.EnsureSuccessStatusCode();
var created = JsonNode.Parse(await resp.Content.ReadAsStringAsync())!;
Console.WriteLine($"Created: {created["ItemId"]}");

// Re-GET to confirm what actually landed -- HTTP 200 alone does not confirm a write
var confirmResp = await client.GetAsync($"{BaseUrl}/api/inventory/parts/{NewItemId}");
confirmResp.EnsureSuccessStatusCode();
var confirmed = JsonNode.Parse(await confirmResp.Content.ReadAsStringAsync())!;
Console.WriteLine($"Confirmed: {confirmed["ItemId"]}: {confirmed["ItemDesc"]}");

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

// Some middleware answers this endpoint in XML even when asked for JSON.
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

> **Note:** `CompanyId` is optional on Location records — P21 infers the default company from the `LocationId`. GL accounts (`GlAccountNo`, `RevenueAccountNo`, `CosAccountNo`) are auto-derived from the `ProductGroupId` and location configuration.

---

## Common Issues

### 1. "Item ID already exists"

**Cause:** Using `POST` for an item that already exists in `inv_mast`.

**Fix:** Use the GET → Append → PUT workflow described above.

### 2. "Account doesn't exist for company"

**Cause:** The `GlAccountNo`, `RevenueAccountNo`, or `CosAccountNo` in your new Location record is not valid for the target company.

**Fix:** Look up valid GL accounts for the target company before constructing the Location payload.

### 3. ItemDesc Max 40 Characters

The `ItemDesc` field on `inv_mast` has a **40-character maximum**. Behavior differs by method:

- **POST** with >40 chars fails with a misleading error: `"Required value missing for Item Description"` (the value is present, just too long)
- **PUT** with >40 chars **silently discards** the value — no error, but the description is not updated

Always validate before sending:

> Full runnable version: [Minimum Create Payload](#minimum-create-payload) — run `validate_item_desc`/`ValidateItemDesc` on `ItemDesc` before calling POST or PUT.

<!-- tabs -->

**Python**

```python
MAX_ITEM_DESC_LENGTH = 40

def validate_item_desc(desc: str) -> str:
    """Validate ItemDesc length before API call."""
    if len(desc) > MAX_ITEM_DESC_LENGTH:
        raise ValueError(
            f"ItemDesc '{desc}' is {len(desc)} chars (max {MAX_ITEM_DESC_LENGTH}). "
            "POST will fail with misleading error; PUT will silently discard."
        )
    return desc
```

**C#**

```csharp
const int MaxItemDescLength = 40;

static string ValidateItemDesc(string desc)
{
    if (desc.Length > MaxItemDescLength)
    {
        throw new ArgumentException(
            $"ItemDesc '{desc}' is {desc.Length} chars (max {MaxItemDescLength}). " +
            "POST will fail with misleading error; PUT will silently discard.");
    }
    return desc;
}
```

<!-- /tabs -->

#### Character set and whitespace (verified)

On a **26.1** tenant, the Inventory REST API enforces **no character restriction** on `ItemDesc`. Every printable ASCII symbol round-trips intact through GET → PUT → GET — including characters that commonly trip up other layers:

```
" ' ` & < > # / \ | , ; : . ( ) [ ] { } * + = % $ @ ! ? ~ ^ _ -
```

Extended/Unicode characters (e.g. `é`, `½`, `°`) also store and read back unchanged.

> ⚠️ **Version- and pipeline-dependent.** This was verified on a 26.1 tenant. **25.x tenants and downstream consumers (reporting, label/barcode printing, EDI) may reject characters the 26.1 REST API accepts** — the double-quote `"` is a known offender. If you target 25.x or feed any reporting/printing flow, strip risky symbols (notably `"`) from descriptions **and** part numbers before writing, rather than relying on the API's permissiveness.

Two behaviors **are** enforced at this layer:

- **Length** — exactly 40 characters is accepted; **41 or more is silently discarded** on PUT (HTTP 200, but the value is *not* written and the previous description is retained). POST with >40 fails with the misleading `"Required value missing for Item Description"`.
- **Trailing whitespace is trimmed**; leading whitespace is preserved.

> **If your environment rejects certain symbols in item descriptions, the restriction is _not_ coming from the Inventory REST API.** Look instead at the P21 desktop UI / DynaChange validation rules or the specific downstream consumer (EDI, label/barcode printing, report formatting).

Verified against **Prophet21Play (26.1)** by setting each candidate symbol on a live item via PUT and confirming the value on a fresh GET (then restoring the original description):

<!-- tabs -->

**Python**

```python
"""Probe whether candidate symbols survive a PUT -> GET round-trip on ItemDesc, then restore it."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
ITEM_ID = "WIDGET-001"                    # item to probe -- ItemDesc is overwritten, then restored
EXTENDED_PROPS = "Locations,Suppliers,LocationSuppliers"
CANDIDATE_SYMBOLS = ['"', "'", "&", "<", ">", "#", "/", "\\", "%", "@"]
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


def get_item(client: httpx.Client, headers: dict, item_id: str) -> dict:
    resp = client.get(
        f"{BASE_URL}/api/inventory/parts/{item_id}",
        headers=headers,
        params={"extendedproperties": EXTENDED_PROPS},
    )
    resp.raise_for_status()
    return resp.json()


def symbol_round_trips(client: httpx.Client, headers: dict, item_id: str, symbol: str) -> bool:
    """Probe whether a symbol survives a round-trip (PUT then GET)."""
    part = get_item(client, headers, item_id)
    test = f"AA{symbol}BB"
    part["ItemDesc"] = test
    client.put(f"{BASE_URL}/api/inventory/parts/{item_id}", headers=headers, json=part)
    after = get_item(client, headers, item_id)["ItemDesc"]
    return after == test  # True => allowed; baseline value => silently discarded


with httpx.Client(verify=VERIFY_SSL, timeout=120, follow_redirects=True) as client:
    token = get_token(client)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",       # 2026.1 returns an empty 500 without this
        "Content-Type": "application/json",
    }

    original_desc = get_item(client, headers, ITEM_ID)["ItemDesc"]

    for symbol in CANDIDATE_SYMBOLS:
        allowed = symbol_round_trips(client, headers, ITEM_ID, symbol)
        print(f"{symbol!r}: {'allowed' if allowed else 'discarded'}")

    # Restore the original description
    part = get_item(client, headers, ITEM_ID)
    part["ItemDesc"] = original_desc
    client.put(f"{BASE_URL}/api/inventory/parts/{ITEM_ID}", headers=headers, json=part)
    restored = get_item(client, headers, ITEM_ID)["ItemDesc"]
    print(f"Restored: {restored == original_desc}")
```

**C#**

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string ItemId = "WIDGET-001";                     // item to probe -- ItemDesc is overwritten, then restored
const string ExtendedProps = "Locations,Suppliers,LocationSuppliers";
string[] CandidateSymbols = { "\"", "'", "&", "<", ">", "#", "/", "\\", "%", "@" };
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

var originalDesc = (await GetItemAsync(client, ItemId))["ItemDesc"]?.ToString();

foreach (var symbol in CandidateSymbols)
{
    var allowed = await SymbolRoundTripsAsync(client, ItemId, symbol);
    Console.WriteLine($"\"{symbol}\": {(allowed ? "allowed" : "discarded")}");
}

// Restore the original description
var part = await GetItemAsync(client, ItemId);
part["ItemDesc"] = originalDesc;
await client.PutAsync(
    $"{BaseUrl}/api/inventory/parts/{ItemId}",
    new StringContent(part.ToJsonString(), Encoding.UTF8, "application/json"));
var restored = (await GetItemAsync(client, ItemId))["ItemDesc"]?.ToString();
Console.WriteLine($"Restored: {restored == originalDesc}");

// --- helpers ---------------------------------------------------------------

static async Task<JsonNode> GetItemAsync(HttpClient client, string itemId)
{
    var resp = await client.GetAsync(
        $"{BaseUrl}/api/inventory/parts/{itemId}?extendedproperties={ExtendedProps}");
    resp.EnsureSuccessStatusCode();
    return JsonNode.Parse(await resp.Content.ReadAsStringAsync())!;
}

// Probe whether a symbol survives a round-trip (PUT then GET).
static async Task<bool> SymbolRoundTripsAsync(HttpClient client, string itemId, string symbol)
{
    var part = await GetItemAsync(client, itemId);
    var test = $"AA{symbol}BB";
    part["ItemDesc"] = test;
    await client.PutAsync(
        $"{BaseUrl}/api/inventory/parts/{itemId}",
        new StringContent(part.ToJsonString(), Encoding.UTF8, "application/json"));
    var after = (await GetItemAsync(client, itemId))["ItemDesc"]?.ToString();
    return after == test; // true => allowed; baseline value => silently discarded
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

// Some middleware answers this endpoint in XML even when asked for JSON.
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

### 4. POST Returns 307 Redirect

`POST /api/inventory/parts` (without trailing slash) returns **307 Temporary Redirect** to `/api/inventory/parts/`. Most HTTP clients do not follow redirects on POST by default.

**Fix:** Either add a trailing slash to the URL, or configure your client to follow redirects:

> Full runnable version: [Minimum Create Payload](#minimum-create-payload) — already POSTs to the trailing-slash URL with a redirect-following client.

<!-- tabs -->

**Python**

```python
import httpx

# Option 1: Trailing slash
resp = client.post(f"{BASE_URL}/api/inventory/parts/", json=payload)

# Option 2: follow_redirects
client = httpx.Client(
    headers={"Authorization": f"Bearer {TOKEN}"},
    follow_redirects=True,
)
resp = client.post(f"{BASE_URL}/api/inventory/parts", json=payload)
```

**C#**

```csharp
// Option 1: Trailing slash
var resp = await client.PostAsync($"{baseUrl}/api/inventory/parts/", content);

// Option 2: AllowAutoRedirect (default is true for HttpClientHandler)
var handler = new HttpClientHandler { AllowAutoRedirect = true };
using var client = new HttpClient(handler);
var resp = await client.PostAsync($"{baseUrl}/api/inventory/parts", content);
```

<!-- /tabs -->

> **Note:** `GET` and `PUT` (which include the ItemId in the URL path) are not affected.

### 5. Location Soft-Delete via Delete Flag

To remove an item from a location without deleting the `inv_loc` record, set the `Delete` flag to `"Y"`. This is a **soft-delete** — the record still exists in the database but is excluded from business operations (ordering, selling, etc.).

<!-- tabs -->

**Python**

```python
"""GET -> set Delete='Y' on one inv_loc -> PUT -> re-GET to confirm the soft-delete."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
ITEM_ID = "WIDGET-001"                    # item to update
TARGET_LOCATION_ID = 2                    # inv_loc.LocationId to soft-delete
TARGET_COMPANY_ID = "ACME"                # inv_loc.CompanyId to soft-delete
EXTENDED_PROPS = "Locations,Suppliers,LocationSuppliers,UnitsOfMeasure"
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

    # 1. GET item with locations
    resp = client.get(
        f"{BASE_URL}/api/inventory/parts/{ITEM_ID}",
        headers=headers,
        params={"extendedproperties": EXTENDED_PROPS},
    )
    resp.raise_for_status()
    item = resp.json()

    # 2. Set Delete flag on the target location -- do not drop the other records
    for loc in item["Locations"]["list"]:
        if loc["LocationId"] == TARGET_LOCATION_ID and loc["CompanyId"] == TARGET_COMPANY_ID:
            loc["Delete"] = "Y"
            break

    # 3. PUT the whole item back
    resp = client.put(f"{BASE_URL}/api/inventory/parts/{ITEM_ID}", headers=headers, json=item)
    resp.raise_for_status()
    print(f"PUT status: {resp.status_code}")

    # 4. Re-GET to prove what actually landed -- HTTP 200 alone does not confirm a write
    resp = client.get(
        f"{BASE_URL}/api/inventory/parts/{ITEM_ID}",
        headers=headers,
        params={"extendedproperties": EXTENDED_PROPS},
    )
    resp.raise_for_status()
    after = resp.json()
    for loc in after["Locations"]["list"]:
        if loc["LocationId"] == TARGET_LOCATION_ID and loc["CompanyId"] == TARGET_COMPANY_ID:
            print(f"Delete flag is now: {loc['Delete']}")
            break
```

**C#**

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string ItemId = "WIDGET-001";                     // item to update
const int TargetLocationId = 2;                         // inv_loc.LocationId to soft-delete
const string TargetCompanyId = "ACME";                  // inv_loc.CompanyId to soft-delete
const string ExtendedProps = "Locations,Suppliers,LocationSuppliers,UnitsOfMeasure";
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

// 1. GET item with locations
var getUrl = $"{BaseUrl}/api/inventory/parts/{ItemId}?extendedproperties={ExtendedProps}";
var getResp = await client.GetAsync(getUrl);
getResp.EnsureSuccessStatusCode();
var item = JsonNode.Parse(await getResp.Content.ReadAsStringAsync())!;

// 2. Set Delete flag on the target location -- do not drop the other records
var locations = item["Locations"]!["list"]!.AsArray();
var target = locations.FirstOrDefault(
    l => (int)l!["LocationId"]! == TargetLocationId && (string)l["CompanyId"]! == TargetCompanyId);
if (target != null)
{
    target["Delete"] = "Y";
}

// 3. PUT the whole item back
var putContent = new StringContent(item.ToJsonString(), Encoding.UTF8, "application/json");
var putResp = await client.PutAsync($"{BaseUrl}/api/inventory/parts/{ItemId}", putContent);
putResp.EnsureSuccessStatusCode();
Console.WriteLine($"PUT status: {(int)putResp.StatusCode}");

// 4. Re-GET to prove what actually landed -- HTTP 200 alone does not confirm a write
var afterResp = await client.GetAsync(getUrl);
afterResp.EnsureSuccessStatusCode();
var after = JsonNode.Parse(await afterResp.Content.ReadAsStringAsync())!;
var afterTarget = after["Locations"]!["list"]!.AsArray().FirstOrDefault(
    l => (int)l!["LocationId"]! == TargetLocationId && (string)l["CompanyId"]! == TargetCompanyId);
if (afterTarget != null)
{
    Console.WriteLine($"Delete flag is now: {afterTarget["Delete"]}");
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

// Some middleware answers this endpoint in XML even when asked for JSON.
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

> **Note:** To restore a soft-deleted location, set `Delete` back to `"N"` using the same pattern.

### 6. UOM Handling

Units of Measure (`UnitsOfMeasure`) are defined at the `inv_mast` level and shared across all companies. You typically do not need to add company-specific UOMs — standard units like "EA", "BOX", etc. apply globally. Ensure existing UOMs are included in your PUT payload.

---

## Automation Example

<!-- tabs -->

**Python**

```python
"""Add an existing item to a new company/location via GET -> Append -> PUT."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
ITEM_ID = "WIDGET-001"                    # item to append the new company/location to
API = f"{BASE_URL}/api/inventory/parts"
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


def process_item(
    client: httpx.Client, headers: dict, item_id: str,
    new_location: dict, new_supplier: dict,
) -> dict:
    """Add an existing item to a new company/location via GET -> Append -> PUT."""

    # 1. Check if item exists
    try:
        resp = client.get(
            f"{API}/{item_id}",
            headers=headers,
            params={"extendedproperties": "Locations,Suppliers"},
        )
        resp.raise_for_status()
        current_item = resp.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            # Item doesn't exist — create it with POST
            payload = {"ItemId": item_id, **new_location, **new_supplier}
            resp = client.post(f"{API}/", headers=headers, json=payload)
            resp.raise_for_status()
            return resp.json()
        raise

    # 2. Check if company/location already linked
    existing_companies = {
        loc.get("CompanyId")
        for loc in current_item.get("Locations", {}).get("list", [])
    }
    if new_location.get("CompanyId") in existing_companies:
        print(f"Item {item_id} already linked to {new_location['CompanyId']}")
        return current_item

    # 3. Append new records
    current_item["Locations"]["list"].append(new_location)
    current_item["Suppliers"]["list"].append(new_supplier)

    # 4. PUT updated payload
    resp = client.put(f"{API}/{item_id}", headers=headers, json=current_item)
    resp.raise_for_status()
    return resp.json()


with httpx.Client(verify=VERIFY_SSL, timeout=120, follow_redirects=True) as client:
    token = get_token(client)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",       # 2026.1 returns an empty 500 without this
        "Content-Type": "application/json",
    }

    new_location = {
        "ItemId": ITEM_ID,
        "LocationId": 2,
        "CompanyId": "ACME-WEST",
        "GlAccountNo": "1300-000",
        "RevenueAccountNo": "4000-000",
        "CosAccountNo": "5000-000",
        "Sellable": "Y",
        "Stockable": "Y",
        "ObjectName": "inv_loc",
    }
    new_supplier = {
        "ItemId": ITEM_ID,
        "SupplierId": 20,
        "DivisionId": 2,
        "LeadTimeDays": 5,
        "ObjectName": "inventory_supplier",
    }

    result = process_item(client, headers, ITEM_ID, new_location, new_supplier)

    # Read-back what actually landed
    linked = {loc["CompanyId"] for loc in result.get("Locations", {}).get("list", [])}
    print(f"Item {ITEM_ID} now linked to companies: {sorted(linked)}")
```

**C#**

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string ItemId = "WIDGET-001";                     // item to append the new company/location to
const string Api = BaseUrl + "/api/inventory/parts";
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

var newLocation = new JsonObject
{
    ["ItemId"] = ItemId,
    ["LocationId"] = 2,
    ["CompanyId"] = "ACME-WEST",
    ["GlAccountNo"] = "1300-000",
    ["RevenueAccountNo"] = "4000-000",
    ["CosAccountNo"] = "5000-000",
    ["Sellable"] = "Y",
    ["Stockable"] = "Y",
    ["ObjectName"] = "inv_loc",
};
var newSupplier = new JsonObject
{
    ["ItemId"] = ItemId,
    ["SupplierId"] = 20,
    ["DivisionId"] = 2,
    ["LeadTimeDays"] = 5,
    ["ObjectName"] = "inventory_supplier",
};

var result = await ProcessItemAsync(client, ItemId, newLocation, newSupplier);

// Read-back what actually landed
var linked = result["Locations"]?["list"]?.AsArray()
    .Select(loc => loc!["CompanyId"]?.ToString())
    .Distinct()
    .ToList() ?? new List<string?>();
Console.WriteLine($"Item {ItemId} now linked to companies: {string.Join(", ", linked)}");

// --- helpers ---------------------------------------------------------------

// Add an existing item to a new company/location via GET -> Append -> PUT.
static async Task<JsonNode> ProcessItemAsync(
    HttpClient client, string itemId, JsonObject newLocation, JsonObject newSupplier)
{
    // 1. Check if item exists
    var resp = await client.GetAsync($"{Api}/{itemId}?extendedproperties=Locations,Suppliers");

    if (resp.StatusCode == System.Net.HttpStatusCode.NotFound)
    {
        // Item doesn't exist — create it with POST
        var createPayload = new JsonObject { ["ItemId"] = itemId };
        foreach (var kv in newLocation) createPayload[kv.Key] = kv.Value?.DeepClone();
        foreach (var kv in newSupplier) createPayload[kv.Key] = kv.Value?.DeepClone();
        var createContent = new StringContent(
            createPayload.ToJsonString(), Encoding.UTF8, "application/json");
        var createResp = await client.PostAsync($"{Api}/", createContent);
        createResp.EnsureSuccessStatusCode();
        return JsonNode.Parse(await createResp.Content.ReadAsStringAsync())!;
    }

    resp.EnsureSuccessStatusCode();
    var currentItem = JsonNode.Parse(await resp.Content.ReadAsStringAsync())!;

    // 2. Check if company/location already linked
    var locations = currentItem["Locations"]?["list"]?.AsArray() ?? new JsonArray();
    var existingCompanies = locations
        .Select(loc => loc?["CompanyId"]?.ToString())
        .Where(c => c != null)
        .ToHashSet();

    var targetCompany = newLocation["CompanyId"]?.ToString();
    if (existingCompanies.Contains(targetCompany))
    {
        Console.WriteLine($"Item {itemId} already linked to {targetCompany}");
        return currentItem;
    }

    // 3. Append new records
    locations.Add(newLocation.DeepClone());
    var suppliers = currentItem["Suppliers"]?["list"]?.AsArray() ?? new JsonArray();
    suppliers.Add(newSupplier.DeepClone());

    // 4. PUT updated payload
    var putContent = new StringContent(
        currentItem.ToJsonString(), Encoding.UTF8, "application/json");
    var putResp = await client.PutAsync($"{Api}/{itemId}", putContent);
    putResp.EnsureSuccessStatusCode();
    return JsonNode.Parse(await putResp.Content.ReadAsStringAsync())!;
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

// Some middleware answers this endpoint in XML even when asked for JSON.
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

### Batch Processing Tips

For large datasets (thousands of items):

1. **Batch size** — Process items in chunks (e.g., 500–1000) to avoid overwhelming the API
2. **Concurrency** — Use multiple workers if the API permits, but be cautious of `inv_mast` table locking
3. **Error logging** — Log failures with item IDs and error messages for manual review
4. **Retry logic** — P21 may return transient lock errors; retry with a short delay (1–2 seconds)

---

## Pricing Endpoints

> **Added April 2026** — Community-sourced discovery. Credit: Felipe Maurer, John Kennedy.

The Inventory REST API provides multiple pricing endpoints for retrieving customer-specific pricing.

### Single Item Pricing

Two URL patterns are available for single-item pricing:

```http
GET /api/inventory/parts/{ItemId}/v2/price?companyId=ACME&customerId=10&salesLocId=100&sourceLocId=100&uom=EA&priceUom=EA&unitQuantity=1
Authorization: Bearer {token}
Accept: application/json
```

```http
GET /api/inventory/v2/parts/v2/price/{ItemId}?companyid=ACME&customerId=10&sourceLocId=100&salesLocId=100
Authorization: Bearer {token}
Accept: application/json
```

Both endpoints accept the same query parameters and return customer-specific pricing.

**Required parameters:**
- `companyId` — Company ID
- `customerId` — Customer ID for pricing lookup
- `salesLocId` — Sales location ID
- `sourceLocId` — Source/ship location ID
- `uom` — Unit of measure (e.g., `EA`)
- `priceUom` — Price unit of measure (e.g., `EA`)
- `unitQuantity` — Quantity for price break calculation

### Verified Pricing Response

The pricing endpoint returns both pricing AND availability data for the requested location in a single response:

```json
{
    "UnitPrice": 15.750000000,
    "BaseUnitPrice": 15.750000000,
    "UOM": "EA",
    "UOMUnitSize": 1.000000000,
    "PricePageUid": 0,
    "PriceUOM": "EA",
    "PriceUnitSize": 1.000000000,
    "ExtendedPrice": 15.750000000,
    "CalcValue": 1.000000000,
    "UnitCommissionCost": 8.500000000,
    "UnitOtherCost": 8.500000000,
    "UnitSalesCost": 8.500000000,
    "LotCosted": "N",
    "ItemId": "WIDGET-001",
    "CompanyId": null,
    "LocationId": 100,
    "QuantityAvailable": 250.000000000,
    "QuantityOnHand": 300.000000000,
    "QuantityAllocated": 50.000000000,
    "QuantityNonPickable": 0.0,
    "QuantityQuarantined": 0.0,
    "QuantityFrozen": 0.0,
    "LocationType": "Standard"
}
```

> **Note:** The response includes both pricing AND availability data for the requested location. `QuantityAvailable` = `QuantityOnHand` - `QuantityAllocated` (minus non-pickable, quarantined, and frozen). `CompanyId` may be `null` in the response even when specified in the request.

**Key fields:**

| Field | Description |
|-------|-------------|
| `UnitPrice` | Customer-specific unit price after price page evaluation |
| `BaseUnitPrice` | Base unit price before customer-specific adjustments |
| `ExtendedPrice` | `UnitPrice` x `unitQuantity` from request |
| `UnitCommissionCost` / `UnitOtherCost` / `UnitSalesCost` | Cost breakdown for margin calculations |
| `PricePageUid` | Price page that determined the price (`0` = no price page matched) |
| `QuantityAvailable` | Available to sell (on hand minus allocated/holds) |
| `QuantityOnHand` | Physical quantity at the location |
| `LocationType` | Location type (e.g., `"Standard"`) |

### Pricing Error Response

When the item is not valid or not defined at the requested location, the API returns the standard P21 error envelope:

```json
{
    "DateTimeStamp": "/Date(1776347610527)/",
    "ErrorMessage": "Item is not valid or not defined at this location",
    "ErrorType": "P21.Business.Common.BusinessException",
    "HostName": "p21web-01",
    "InnerException": null
}
```

> **Note:** The `DateTimeStamp` uses the Microsoft JSON date format (`/Date(milliseconds)/`). The `ErrorType` for pricing errors is `P21.Business.Common.BusinessException`, distinct from the `P21.Common.Exceptions.Prophet21Exception` used by item CRUD errors.

### URL Encoding for Special Characters

When item IDs contain special characters, URL encoding is required:

| Character | Encoding | Status |
|-----------|----------|--------|
| `#` | `%23` | **Works** — e.g., `ORDER%23TEST` |
| `/` | `%2F` | **Broken** — returns 404 "Endpoint not found" |
| `&` | `%26` | Use standard URL encoding |
| `+` | `%2B` | Use standard URL encoding |

> **Known Issue**: Forward slash (`/`) in item IDs cannot be URL-encoded for the pricing endpoints. The API (or IIS) interprets `%2F` as a literal path separator, returning 404. There is no known workaround for items containing `/` in their ID. (Credit: John Kennedy, confirmed by Felipe Maurer)

---

### Batch Pricing

> **Added August 2026** — Live-verified against Prophet21Play (26.1).

`POST /api/inventory/parts/prices` (and the identical `POST /api/inventory/v2/parts/prices`) price and check availability for **multiple items in one call**. Unlike single-item pricing, `ItemId` is in the request body, not the URL — so the [forward-slash URL-encoding limitation](#url-encoding-for-special-characters) above does not apply here.

```http
POST /api/inventory/parts/prices?companyId=ACME&customerId=10&salesLocId=100
Authorization: Bearer {token}
Content-Type: application/json
Accept: application/json

[
    { "ItemId": "WIDGET-001", "SourceLocId": 100 },
    { "ItemId": "WIDGET-002", "SourceLocId": 100 }
]
```

**Required query parameters** (verified — omitting any one produces a distinct error naming exactly that parameter, checked in this order):

1. `companyId`
2. `customerId`
3. `salesLocId`

P21 validates these one at a time and fails on the first missing one, so an incomplete request appears to fail "progressively" as you add parameters — each retry reveals the next missing one rather than listing all of them up front:

```json
{"ErrorMessage": "Please provide a value for required parameter companyId.", "ErrorType": "System.ArgumentException", ...}
```

The WCF method signature (visible in the stack trace) also accepts `optionalShipToId`, `optionalOrderDate`, and `optionalJobNo` as query parameters — not verified.

**Request body** — a JSON array or an XML `ArrayOfItemPriceInfo` of per-item objects. Verified minimum: `ItemId` + `SourceLocId`. Also accepted per item: `CustomerPartNo`, `UnitQuantity`, `UnitSize`, `UOM`, `PriceUom` (all optional — P21 defaults `UOM`/`PriceUom` to the item's base unit when omitted).

**Response** — a JSON array or an XML `ArrayOfItemPrice`, one entry per requested item, in the same shape as [single-item pricing](#verified-pricing-response) (pricing **and** availability fields together).

#### Content-Type must match the body — this is not "XML only" (verified)

This endpoint is often mistaken for XML-only. **It is not** — both JSON and XML request/response bodies work. It's a WCF REST endpoint that selects its (de)serializer from the `Content-Type` header, not by inspecting the body, so sending a body that doesn't match `Content-Type` produces a confusing failure that looks like a format rejection:

| `Content-Type` sent | Actual body | Result |
|---|---|---|
| `application/json` | JSON | **200** — works |
| `application/xml` | XML | **200** — works |
| *(omitted, `Accept: application/json`)* | JSON | **200** — works (defaults to JSON) |
| `application/xml` | JSON | **400** — generic WCF "Request Error" HTML page pointing at `/help`; no P21 error, no mention of a header mismatch |
| `application/json` | XML | **500** — at least a real P21 error: `BadRequestException: Invalid JSON or request body for parameter 'itemInfo'. Unexpected character encountered while parsing value: <...` |

The `application/xml` + JSON-body case is what creates the "XML only" impression: the response gives no hint that the body was even parsed, let alone that the fix is the `Content-Type` header rather than the body format. If a batch pricing POST comes back as that generic WCF "Request Error" page, check that `Content-Type` matches what you actually sent before concluding the endpoint rejects JSON.

<!-- tabs -->

**Python**

```python
"""Batch price + availability lookup via the Inventory REST API (JSON body)."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
COMPANY_ID = "ACME"                       # required query param
CUSTOMER_ID = "10"                        # required query param
SALES_LOC_ID = "100"                      # required query param
ITEMS = [
    {"ItemId": "WIDGET-001", "SourceLocId": 100},
    {"ItemId": "WIDGET-002", "SourceLocId": 100},
]
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
        # Content-Type must match the body -- application/json here because ITEMS
        # is sent as JSON. Sending application/xml with a JSON body 400s (see above).
        "Content-Type": "application/json",
    }

    resp = client.post(
        f"{BASE_URL}/api/inventory/parts/prices",
        headers=headers,
        params={"companyId": COMPANY_ID, "customerId": CUSTOMER_ID, "salesLocId": SALES_LOC_ID},
        json=ITEMS,
    )
    resp.raise_for_status()
    for price in resp.json():
        print(
            f"{price['ItemId']}: UnitPrice={price['UnitPrice']} "
            f"QtyAvailable={price['QuantityAvailable']}"
        )
```

**C#**

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string CompanyId = "ACME";                        // required query param
const string CustomerId = "10";                         // required query param
const string SalesLocId = "100";                        // required query param
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

var items = new JsonArray
{
    new JsonObject { ["ItemId"] = "WIDGET-001", ["SourceLocId"] = 100 },
    new JsonObject { ["ItemId"] = "WIDGET-002", ["SourceLocId"] = 100 },
};

// Content-Type must match the body -- application/json here because items is
// sent as JSON. Sending application/xml with a JSON body 400s (see above).
var url = $"{BaseUrl}/api/inventory/parts/prices" +
          $"?companyId={CompanyId}&customerId={CustomerId}&salesLocId={SalesLocId}";
var content = new StringContent(items.ToJsonString(), Encoding.UTF8, "application/json");
var resp = await client.PostAsync(url, content);
resp.EnsureSuccessStatusCode();

var prices = JsonNode.Parse(await resp.Content.ReadAsStringAsync())!.AsArray();
foreach (var price in prices)
{
    Console.WriteLine(
        $"{price!["ItemId"]}: UnitPrice={price["UnitPrice"]} " +
        $"QtyAvailable={price["QuantityAvailable"]}");
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

// Some middleware answers this endpoint in XML even when asked for JSON.
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

**Sample response** (one entry per requested item, same fields as [single-item pricing](#verified-pricing-response)):

```json
[
    {
        "UnitPrice": 10.780000000,
        "BaseUnitPrice": 10.780000000,
        "UOM": "EA",
        "UOMUnitSize": 1.000000000,
        "PricePageUid": 0,
        "PriceUOM": "EA",
        "PriceUnitSize": 1.000000000,
        "ExtendedPrice": 10.780000000,
        "CalcValue": 1.000000000,
        "UnitCommissionCost": 5.308224600,
        "UnitOtherCost": 5.390000000,
        "UnitSalesCost": 5.308224600,
        "LotCosted": "N",
        "ItemId": "WIDGET-001",
        "CompanyId": null,
        "LocationId": 100,
        "QuantityAvailable": 41.000000000,
        "QuantityOnHand": 41.000000000,
        "QuantityAllocated": 0.000000000,
        "QuantityNonPickable": 0.0,
        "QuantityQuarantined": 0.0,
        "QuantityFrozen": 0.0,
        "LocationType": "Standard"
    },
    {
        "ItemId": "WIDGET-002",
        "PricePageUid": 813,
        "...": "one object per requested item, same shape"
    }
]
```

> **Note:** As with single-item pricing, `CompanyId` in the response can be `null` even though it was required in the request.

#### Equivalent XML request/response

The same call, sent as XML instead — only the `Content-Type`/`Accept` headers and body format change; the query parameters and URL are identical:

```http
POST /api/inventory/parts/prices?companyId=ACME&customerId=10&salesLocId=100
Authorization: Bearer {token}
Content-Type: application/xml
Accept: application/xml

<ArrayOfItemPriceInfo>
    <ItemPriceInfo>
        <ItemId>WIDGET-001</ItemId>
        <SourceLocId>100</SourceLocId>
    </ItemPriceInfo>
    <ItemPriceInfo>
        <ItemId>WIDGET-002</ItemId>
        <SourceLocId>100</SourceLocId>
    </ItemPriceInfo>
</ArrayOfItemPriceInfo>
```

```xml
<?xml version="1.0"?>
<ArrayOfItemPrice xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <ItemPrice>
    <ItemId>WIDGET-001</ItemId>
    <LocationId>100</LocationId>
    <QuantityAvailable>41.000000000</QuantityAvailable>
    <QuantityOnHand>41.000000000</QuantityOnHand>
    <QuantityAllocated>0.000000000</QuantityAllocated>
    <QuantityNonPickable>0</QuantityNonPickable>
    <QuantityQuarantined>0</QuantityQuarantined>
    <QuantityFrozen>0</QuantityFrozen>
    <LocationType>Standard</LocationType>
    <UnitPrice>10.780000000</UnitPrice>
    <BaseUnitPrice>10.780000000</BaseUnitPrice>
    <UOM>EA</UOM>
    <UOMUnitSize>1.000000000</UOMUnitSize>
    <PricePageUid>0</PricePageUid>
    <PriceUOM>EA</PriceUOM>
    <PriceUnitSize>1.000000000</PriceUnitSize>
    <ExtendedPrice>10.780000000</ExtendedPrice>
    <CalcValue>1.000000000</CalcValue>
    <UnitCommissionCost>5.308224600</UnitCommissionCost>
    <UnitOtherCost>5.390000000</UnitOtherCost>
    <UnitSalesCost>5.308224600</UnitSalesCost>
    <LotCosted>N</LotCosted>
  </ItemPrice>
  <!-- one <ItemPrice> per requested item -->
</ArrayOfItemPrice>
```

> Full runnable version: adapt the [Python/C# example above](#batch-pricing) — swap the JSON body/headers for the XML shown here, no other change needed.

---

## Known Limitations

1. **No `/new` template** — Unlike the Entity API, there is no template endpoint. You must know the required fields for POST (see [Minimum Create Payload](#minimum-create-payload)).

2. **List endpoint performance** — Always use `$query` filtering. The unfiltered list endpoint attempts to load all inventory and times out.

3. **Item accessibility** — Some items that exist in `inv_mast` (visible via OData) return 404 from this API. This may be related to item status or configuration.

4. **Forward slash in item IDs** — The `%2F` URL encoding for `/` is interpreted as a path separator by IIS, causing 404 errors on pricing and other endpoints that include the item ID in the URL path. This affects both pricing endpoint URL patterns.

---

## Related

- [Entity API](05-Entity-API.md) — CRUD for customers, vendors, contacts, addresses
- [Authentication](00-Authentication.md) — Token generation
- [API Selection Guide](01-API-Selection-Guide.md) — Which API to use when
- [OData API](02-OData-API.md) — Read-only queries on any table including `inv_mast` and `inv_loc`
- [Error Handling](06-Error-Handling.md) — Common P21 error patterns
