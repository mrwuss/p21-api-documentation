# Inventory REST API

> **Disclaimer:** This is unofficial, community-created documentation for Epicor Prophet 21 APIs. It is not affiliated with, endorsed by, or supported by Epicor Software Corporation. All product names, trademarks, and registered trademarks are property of their respective owners. Use at your own risk.

---

> **Added February 2026** — Originally contributed by [@sibinfrancisaj](https://github.com/sibinfrancisaj). PUT/POST behavior verified via live API testing.

---

## Overview

P21 provides an **Inventory REST API** at `/api/inventory/parts` for CRUD operations on inventory items (`inv_mast`). This is a **separate API** from the [Entity API](05-Entity-API.md) at `/api/entity/` — it uses its own base path and has different behavior.

The Inventory REST API is significant because it provides:
- **Read access** to `inv_loc` (inventory location) records via extended properties
- **Write access** to append new `inv_loc` and `inventory_supplier` records via PUT
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
- **Cannot update existing `inv_loc` fields** — You can append new location records but not modify fields on existing ones (see [Known Limitations](#known-limitations))

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
| `POST` | `/api/inventory/parts` | Create new item | Yes (error for duplicates) |
| `GET` | `/api/inventory/parts/{ItemId}/availability` | Item availability | Not tested |
| `GET` | `/api/inventory/parts/{ItemId}/price` | Item pricing | Not tested |
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
| `UserDefinedFields` | object | User-defined fields |
| `ObjectName` | string | Always `"inv_mast"` |

---

## Writing Items

### PUT — Update Existing Item

`PUT /api/inventory/parts/{ItemId}` accepts the full item payload and processes changes including appended child records (Locations, Suppliers).

**Verified behavior:**
- Sending back the same data unchanged returns 200 (idempotent)
- Appending new `inv_loc` records in `Locations.list` triggers P21 business logic validation (company validation, GL account checks)
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

## Common Issues

### 1. "Item ID already exists"

**Cause:** Using `POST` for an item that already exists in `inv_mast`.

**Fix:** Use the GET → Append → PUT workflow described above.

### 2. "Account doesn't exist for company"

**Cause:** The `GlAccountNo`, `RevenueAccountNo`, or `CosAccountNo` in your new Location record is not valid for the target company.

**Fix:** Look up valid GL accounts for the target company before constructing the Location payload.

### 3. UOM Handling

Units of Measure (`UnitsOfMeasure`) are defined at the `inv_mast` level and shared across all companies. You typically do not need to add company-specific UOMs — standard units like "EA", "BOX", etc. apply globally. Ensure existing UOMs are included in your PUT payload.

---

## Automation Example

<!-- tabs -->

**Python**

```python
import httpx

BASE_URL = "https://play.p21server.com"
API = f"{BASE_URL}/api/inventory/parts"


def process_item(client: httpx.Client, item_id: str, new_location: dict, new_supplier: dict):
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

## Known Limitations

1. **Append only, not update** — You can append new `inv_loc` records to an item, but modifying fields on *existing* `inv_loc` records via this API has not been verified. For updating existing location fields (GL accounts, product group, etc.), the Interactive API Item window or direct SQL may be required.

2. **No `/new` template** — Unlike the Entity API, there is no template endpoint. You must know the required fields for POST.

3. **List endpoint performance** — Always use `$query` filtering. The unfiltered list endpoint attempts to load all inventory and times out.

4. **Item accessibility** — Some items that exist in `inv_mast` (visible via OData) return 404 from this API. This may be related to item status or configuration.

---

## Related

- [Entity API](05-Entity-API.md) — CRUD for customers, vendors, contacts, addresses
- [Authentication](00-Authentication.md) — Token generation
- [API Selection Guide](01-API-Selection-Guide.md) — Which API to use when
- [OData API](02-OData-API.md) — Read-only queries on any table including `inv_mast` and `inv_loc`
- [Error Handling](06-Error-Handling.md) — Common P21 error patterns
