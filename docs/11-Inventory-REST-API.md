# Inventory REST API

> **Disclaimer:** This is unofficial, community-created documentation for Epicor Prophet 21 APIs. It is not affiliated with, endorsed by, or supported by Epicor Software Corporation. All product names, trademarks, and registered trademarks are property of their respective owners. Use at your own risk.

---

> **Added February 2026** — Originally contributed by [@sibinfrancisaj](https://github.com/sibinfrancisaj). PUT/POST behavior verified via live API testing.

---

## Overview

P21 provides an **Inventory REST API** at `/api/inventory/parts` for CRUD operations on inventory items (`inv_mast`). This is a **separate API** from the [Entity API](05-Entity-API.md) at `/api/entity/` — it uses its own base path and has different behavior.

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
| `POST` | `/api/inventory/parts/prices` | Batch pricing | Not tested |

---

## Comparison with Entity API

| Feature | Entity API | Inventory REST API |
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
resp = client.get(f"{base_url}/api/inventory/parts/WIDGET-001")
resp.raise_for_status()
item = resp.json()
print(f"{item['ItemId']}: {item['ItemDesc']}")
```

**C#**

```csharp
using System;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Newtonsoft.Json.Linq;

var resp = await client.GetAsync($"{baseUrl}/api/inventory/parts/WIDGET-001");
resp.EnsureSuccessStatusCode();
var item = JObject.Parse(await resp.Content.ReadAsStringAsync());
Console.WriteLine($"{item["ItemId"]}: {item["ItemDesc"]}");
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
resp = client.get(
    f"{base_url}/api/inventory/parts/WIDGET-001",
    params={"extendedproperties": "*"}
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
var resp = await client.GetAsync(
    $"{baseUrl}/api/inventory/parts/WIDGET-001?extendedproperties=*");
resp.EnsureSuccessStatusCode();
var item = JObject.Parse(await resp.Content.ReadAsStringAsync());

// Access nested Locations (inv_loc data)
var locations = item["Locations"]?["list"] as JArray;
if (locations != null)
{
    foreach (var loc in locations)
    {
        Console.WriteLine($"Loc: {loc["LocationId"]}, Qty: {loc["QtyOnHand"]}");
    }
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

## Updating Existing Location Fields

The GET -> Modify -> PUT pattern also works for **updating fields on existing `inv_loc` records**, not just appending new ones.

**Verified writable fields:** `Sellable`, `ProductGroupId`, `PurchaseDiscountGroup`, `SalesDiscountGroup`

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
import httpx

BASE_URL = "https://play.p21server.com"
TOKEN = "<ACCESS_TOKEN>"

with httpx.Client(
    headers={"Authorization": f"Bearer {TOKEN}"},
    follow_redirects=True,
) as client:
    # 1. GET current item with Locations
    ext = "Locations,Suppliers,LocationSuppliers,UnitsOfMeasure"
    resp = client.get(
        f"{BASE_URL}/api/inventory/parts/WIDGET-001",
        params={"extendedproperties": ext},
    )
    resp.raise_for_status()
    item = resp.json()

    # 2. Modify fields on existing location
    for loc in item["Locations"]["list"]:
        if loc["LocationId"] == 1 and loc["CompanyId"] == "ACME":
            loc["Sellable"] = "N"
            loc["ProductGroupId"] = "MISC"
            loc["PurchaseDiscountGroup"] = "BULK"
            loc["SalesDiscountGroup"] = "RETAIL"
            break

    # 3. PUT back
    resp = client.put(f"{BASE_URL}/api/inventory/parts/WIDGET-001", json=item)
    resp.raise_for_status()
    print(f"Updated: {resp.status_code}")
```

**C#**

```csharp
using System;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Newtonsoft.Json.Linq;

var handler = new HttpClientHandler { AllowAutoRedirect = true };
using var client = new HttpClient(handler);
client.DefaultRequestHeaders.Add("Authorization", "Bearer <ACCESS_TOKEN>");
var baseUrl = "https://play.p21server.com";

// 1. GET current item with Locations
var resp = await client.GetAsync(
    $"{baseUrl}/api/inventory/parts/WIDGET-001?extendedproperties=Locations,Suppliers,LocationSuppliers,UnitsOfMeasure");
resp.EnsureSuccessStatusCode();
var item = JObject.Parse(await resp.Content.ReadAsStringAsync());

// 2. Modify fields on existing location
var locations = item["Locations"]?["list"] as JArray;
var target = locations?.FirstOrDefault(
    l => (int)l["LocationId"] == 1 && (string)l["CompanyId"] == "ACME");
if (target != null)
{
    target["Sellable"] = "N";
    target["ProductGroupId"] = "MISC";
    target["PurchaseDiscountGroup"] = "BULK";
    target["SalesDiscountGroup"] = "RETAIL";
}

// 3. PUT back
var content = new StringContent(item.ToString(), Encoding.UTF8, "application/json");
var putResp = await client.PutAsync($"{baseUrl}/api/inventory/parts/WIDGET-001", content);
putResp.EnsureSuccessStatusCode();
Console.WriteLine($"Updated: {(int)putResp.StatusCode}");
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
import httpx

BASE_URL = "https://play.p21server.com"
TOKEN = "<ACCESS_TOKEN>"

payload = {
    "ItemId": "WIDGET-002",
    "ItemDesc": "Small Widget Assembly",
    "Locations": {
        "list": [
            {
                "LocationId": 1,
                "ProductGroupId": "MISC",
                "ObjectName": "inv_loc"
            }
        ]
    },
    "Suppliers": {
        "list": [
            {
                "SupplierId": 10,
                "DivisionId": 1,
                "ObjectName": "inventory_supplier"
            }
        ]
    },
    "LocationSuppliers": {
        "list": [
            {
                "LocationId": 1,
                "SupplierId": 10,
                "PrimarySupplier": "Y",
                "ObjectName": "inventory_supplier_x_loc"
            }
        ]
    },
    "ObjectName": "inv_mast"
}

with httpx.Client(
    headers={"Authorization": f"Bearer {TOKEN}"},
    follow_redirects=True,
) as client:
    resp = client.post(f"{BASE_URL}/api/inventory/parts/", json=payload)
    resp.raise_for_status()
    print(f"Created: {resp.json()['ItemId']}")
```

**C#**

```csharp
using System;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Newtonsoft.Json.Linq;

var handler = new HttpClientHandler { AllowAutoRedirect = true };
using var client = new HttpClient(handler);
client.DefaultRequestHeaders.Add("Authorization", "Bearer <ACCESS_TOKEN>");
var baseUrl = "https://play.p21server.com";

var payload = new JObject
{
    ["ItemId"] = "WIDGET-002",
    ["ItemDesc"] = "Small Widget Assembly",
    ["ObjectName"] = "inv_mast",
    ["Locations"] = new JObject
    {
        ["list"] = new JArray
        {
            new JObject
            {
                ["LocationId"] = 1,
                ["ProductGroupId"] = "MISC",
                ["ObjectName"] = "inv_loc"
            }
        }
    },
    ["Suppliers"] = new JObject
    {
        ["list"] = new JArray
        {
            new JObject
            {
                ["SupplierId"] = 10,
                ["DivisionId"] = 1,
                ["ObjectName"] = "inventory_supplier"
            }
        }
    },
    ["LocationSuppliers"] = new JObject
    {
        ["list"] = new JArray
        {
            new JObject
            {
                ["LocationId"] = 1,
                ["SupplierId"] = 10,
                ["PrimarySupplier"] = "Y",
                ["ObjectName"] = "inventory_supplier_x_loc"
            }
        }
    }
};

var content = new StringContent(payload.ToString(), Encoding.UTF8, "application/json");
var resp = await client.PostAsync($"{baseUrl}/api/inventory/parts/", content);
resp.EnsureSuccessStatusCode();
var result = JObject.Parse(await resp.Content.ReadAsStringAsync());
Console.WriteLine($"Created: {result["ItemId"]}");
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

### 4. POST Returns 307 Redirect

`POST /api/inventory/parts` (without trailing slash) returns **307 Temporary Redirect** to `/api/inventory/parts/`. Most HTTP clients do not follow redirects on POST by default.

**Fix:** Either add a trailing slash to the URL, or configure your client to follow redirects:

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
import httpx

BASE_URL = "https://play.p21server.com"
TOKEN = "<ACCESS_TOKEN>"

with httpx.Client(
    headers={"Authorization": f"Bearer {TOKEN}"},
    follow_redirects=True,
) as client:
    # 1. GET item with locations
    ext = "Locations,Suppliers,LocationSuppliers,UnitsOfMeasure"
    resp = client.get(
        f"{BASE_URL}/api/inventory/parts/WIDGET-001",
        params={"extendedproperties": ext},
    )
    resp.raise_for_status()
    item = resp.json()

    # 2. Set Delete flag on target location
    for loc in item["Locations"]["list"]:
        if loc["LocationId"] == 2 and loc["CompanyId"] == "ACME":
            loc["Delete"] = "Y"
            break

    # 3. PUT back
    resp = client.put(f"{BASE_URL}/api/inventory/parts/WIDGET-001", json=item)
    resp.raise_for_status()
    print(f"Soft-deleted location: {resp.status_code}")
```

**C#**

```csharp
using System;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Newtonsoft.Json.Linq;

var handler = new HttpClientHandler { AllowAutoRedirect = true };
using var client = new HttpClient(handler);
client.DefaultRequestHeaders.Add("Authorization", "Bearer <ACCESS_TOKEN>");
var baseUrl = "https://play.p21server.com";

// 1. GET item with locations
var resp = await client.GetAsync(
    $"{baseUrl}/api/inventory/parts/WIDGET-001?extendedproperties=Locations,Suppliers,LocationSuppliers,UnitsOfMeasure");
resp.EnsureSuccessStatusCode();
var item = JObject.Parse(await resp.Content.ReadAsStringAsync());

// 2. Set Delete flag on target location
var locations = item["Locations"]?["list"] as JArray;
var target = locations?.FirstOrDefault(
    l => (int)l["LocationId"] == 2 && (string)l["CompanyId"] == "ACME");
if (target != null)
{
    target["Delete"] = "Y";
}

// 3. PUT back
var content = new StringContent(item.ToString(), Encoding.UTF8, "application/json");
var putResp = await client.PutAsync($"{baseUrl}/api/inventory/parts/WIDGET-001", content);
putResp.EnsureSuccessStatusCode();
Console.WriteLine($"Soft-deleted location: {(int)putResp.StatusCode}");
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
import httpx

BASE_URL = "https://play.p21server.com"
API = f"{BASE_URL}/api/inventory/parts"


def process_item(
    client: httpx.Client, item_id: str,
    new_location: dict, new_supplier: dict,
):
    """Add an existing item to a new company/location via GET -> Append -> PUT."""

    # 1. Check if item exists
    try:
        resp = client.get(
            f"{API}/{item_id}",
            params={"extendedproperties": "Locations,Suppliers"},
        )
        resp.raise_for_status()
        current_item = resp.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            # Item doesn't exist — create it with POST
            payload = {"ItemId": item_id, **new_location, **new_supplier}
            resp = client.post(API, json=payload)
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
    resp = client.put(f"{API}/{item_id}", json=current_item)
    resp.raise_for_status()
    return resp.json()
```

**C#**

```csharp
const string BaseUrl = "https://play.p21server.com";
const string Api = BaseUrl + "/api/inventory/parts";

async Task<JObject> ProcessItemAsync(
    HttpClient client, string itemId, JObject newLocation, JObject newSupplier)
{
    // 1. Check if item exists
    var resp = await client.GetAsync($"{Api}/{itemId}?extendedproperties=Locations,Suppliers");

    if (resp.StatusCode == System.Net.HttpStatusCode.NotFound)
    {
        // Item doesn't exist — create it with POST
        var createPayload = new JObject { ["ItemId"] = itemId };
        createPayload.Merge(newLocation);
        createPayload.Merge(newSupplier);
        var createContent = new StringContent(
            createPayload.ToString(), Encoding.UTF8, "application/json");
        var createResp = await client.PostAsync(Api, createContent);
        createResp.EnsureSuccessStatusCode();
        return JObject.Parse(await createResp.Content.ReadAsStringAsync());
    }

    resp.EnsureSuccessStatusCode();
    var currentItem = JObject.Parse(await resp.Content.ReadAsStringAsync());

    // 2. Check if company/location already linked
    var locations = currentItem["Locations"]?["list"] as JArray ?? new JArray();
    var existingCompanies = locations
        .Select(loc => loc["CompanyId"]?.ToString())
        .Where(c => c != null)
        .ToHashSet();

    var targetCompany = newLocation["CompanyId"]?.ToString();
    if (existingCompanies.Contains(targetCompany))
    {
        Console.WriteLine($"Item {itemId} already linked to {targetCompany}");
        return currentItem;
    }

    // 3. Append new records
    locations.Add(newLocation);
    var suppliers = currentItem["Suppliers"]?["list"] as JArray ?? new JArray();
    suppliers.Add(newSupplier);

    // 4. PUT updated payload
    var putContent = new StringContent(
        currentItem.ToString(), Encoding.UTF8, "application/json");
    var putResp = await client.PutAsync($"{Api}/{itemId}", putContent);
    putResp.EnsureSuccessStatusCode();
    return JObject.Parse(await putResp.Content.ReadAsStringAsync());
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
    "HostName": "p21web-22",
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
