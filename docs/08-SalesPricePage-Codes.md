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
# Step 1: Set page type FIRST - this determines available fields
await window.change_data("FORM", "price_page_type_cd",
                         "Supplier / Product Group", datawindow_name="form")

# Step 2: Set company_id BEFORE product_group_id
await window.change_data("FORM", "company_id", "ACME", datawindow_name="form")

# Step 3: Set product group
await window.change_data("FORM", "product_group_id", "HVAC", datawindow_name="form")

# Step 4: Set supplier
await window.change_data("FORM", "supplier_id", "10050", datawindow_name="form")

# Step 5: Set description
await window.change_data("FORM", "description", "P2-L5-10050-HVAC-WHOLESALE",
                         datawindow_name="form")

# Step 6-7: Set pricing method and source
await window.change_data("FORM", "pricing_method_cd", "Source", datawindow_name="form")
await window.change_data("FORM", "source_price_cd", "Supplier List Price",
                         datawindow_name="form")

# Step 8: Set dates
await window.change_data("FORM", "effective_date", "2025-01-01", datawindow_name="form")
await window.change_data("FORM", "expiration_date", "2030-12-31", datawindow_name="form")

# Step 9: Switch to VALUES tab
await window.select_tab("VALUES")

# Step 10-11: Set calculation method and value
await window.change_data("VALUES", "calculation_method_cd", "Multiplier",
                         datawindow_name="values")
await window.change_data("VALUES", "calculation_value1", "0.85", datawindow_name="values")

# Save
result = await window.save_data()
```

**C#**

```csharp
using System;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

// Helper to send a v2 change request to the Interactive API
async Task ChangeDataAsync(HttpClient client, string baseUrl, string windowId,
    string tabName, string datawindowName, string fieldName, string value)
{
    var payload = new JObject
    {
        ["WindowId"] = windowId,
        ["List"] = new JArray
        {
            new JObject
            {
                ["TabName"] = tabName,
                ["DatawindowName"] = datawindowName,
                ["FieldName"] = fieldName,
                ["Value"] = value
            }
        }
    };
    var content = new StringContent(payload.ToString(), Encoding.UTF8, "application/json");
    var resp = await client.PutAsync(
        $"{baseUrl}/api/ui/interactive/v2/change", content);
    resp.EnsureSuccessStatusCode();
}

// Step 1: Set page type FIRST - this determines available fields
await ChangeDataAsync(client, baseUrl, windowId,
    "FORM", "form", "price_page_type_cd", "Supplier / Product Group");

// Step 2: Set company_id BEFORE product_group_id
await ChangeDataAsync(client, baseUrl, windowId,
    "FORM", "form", "company_id", "ACME");

// Step 3: Set product group
await ChangeDataAsync(client, baseUrl, windowId,
    "FORM", "form", "product_group_id", "HVAC");

// Step 4: Set supplier
await ChangeDataAsync(client, baseUrl, windowId,
    "FORM", "form", "supplier_id", "10050");

// Step 5: Set description
await ChangeDataAsync(client, baseUrl, windowId,
    "FORM", "form", "description", "P2-L5-10050-HVAC-WHOLESALE");

// Step 6-7: Set pricing method and source
await ChangeDataAsync(client, baseUrl, windowId,
    "FORM", "form", "pricing_method_cd", "Source");
await ChangeDataAsync(client, baseUrl, windowId,
    "FORM", "form", "source_price_cd", "Supplier List Price");

// Step 8: Set dates
await ChangeDataAsync(client, baseUrl, windowId,
    "FORM", "form", "effective_date", "2025-01-01");
await ChangeDataAsync(client, baseUrl, windowId,
    "FORM", "form", "expiration_date", "2030-12-31");

// Step 9: Switch to VALUES tab
var tabPayload = new JObject { ["WindowId"] = windowId, ["PageName"] = "VALUES" };
var tabContent = new StringContent(tabPayload.ToString(), Encoding.UTF8, "application/json");
await client.PutAsync($"{baseUrl}/api/ui/interactive/v2/tab", tabContent);

// Step 10-11: Set calculation method and value
await ChangeDataAsync(client, baseUrl, windowId,
    "VALUES", "values", "calculation_method_cd", "Multiplier");
await ChangeDataAsync(client, baseUrl, windowId,
    "VALUES", "values", "calculation_value1", "0.85");

// Save — v2 takes the bare WindowId string as the JSON body
var saveContent = new StringContent($"\"{windowId}\"", Encoding.UTF8, "application/json");
var saveResp = await client.PutAsync(
    $"{baseUrl}/api/ui/interactive/v2/data", saveContent);
saveResp.EnsureSuccessStatusCode();
var result = JObject.Parse(await saveResp.Content.ReadAsStringAsync());
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

<!-- tabs -->

**Python**

```python
# Correct - use display value
window.change_data("VALUES", "calculation_method_cd", "Mark Up", datawindow_name="values")

# Incorrect - do not use code
window.change_data("VALUES", "calculation_method_cd", "229", datawindow_name="values")
```

**C#**

```csharp
// Correct - use display value
var payload = new JObject
{
    ["WindowId"] = windowId,
    ["List"] = new JArray
    {
        new JObject
        {
            ["TabName"] = "VALUES",
            ["DatawindowName"] = "values",
            ["FieldName"] = "calculation_method_cd",
            ["Value"] = "Mark Up"
        }
    }
};
var content = new StringContent(payload.ToString(), Encoding.UTF8, "application/json");
await client.PutAsync($"{baseUrl}/api/ui/interactive/v2/change", content);

// Incorrect - do not use code
// ["Value"] = "229"  // This will NOT work
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

These codes were discovered by:

1. Opening the SalesPricePage window via Interactive API
2. Setting each dropdown to different display values
3. Reading the resulting code from window state
4. Verifying against live database records

<!-- tabs -->

**Python**

```python
# Example discovery code
window = api.open_window(service_name="SalesPricePage")
window.change_data("FORM", "price_page_uid", "45556", datawindow_name="form")
window.select_tab("VALUES")

# Try setting a display value
result = window.change_data("VALUES", "calculation_method_cd", "Mark Up", datawindow_name="values")

# Read back the code from window state
state = window.get_state()
# Extract calculation_method_cd from state['Data']
```

**C#**

```csharp
// Example discovery code — open window and load a price page
var openPayload = new JObject { ["ServiceName"] = "SalesPricePage" };
var openContent = new StringContent(openPayload.ToString(), Encoding.UTF8, "application/json");
var openResp = await client.PostAsync(
    $"{baseUrl}/api/ui/interactive/v2/window", openContent);
var openResult = JObject.Parse(await openResp.Content.ReadAsStringAsync());
var windowId = openResult["WindowId"]?.ToString();

// Load a specific price page (ChangeDataAsync helper defined above)
await ChangeDataAsync(client, baseUrl, windowId,
    "FORM", "form", "price_page_uid", "45556");

// Switch to VALUES tab
var tabPayload = new JObject { ["WindowId"] = windowId, ["PageName"] = "VALUES" };
var tabContent = new StringContent(tabPayload.ToString(), Encoding.UTF8, "application/json");
await client.PutAsync($"{baseUrl}/api/ui/interactive/v2/tab", tabContent);

// Try setting a display value
await ChangeDataAsync(client, baseUrl, windowId,
    "VALUES", "values", "calculation_method_cd", "Mark Up");

// Read back the code from window state
var stateResp = await client.GetAsync(
    $"{baseUrl}/api/ui/interactive/v2/data?id={windowId}");
var state = JObject.Parse(await stateResp.Content.ReadAsStringAsync());
// Extract calculation_method_cd from state["Data"]
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
# Base multiplier: 0.85 for qty 1+
await window.change_data("VALUES", "calculation_value1", "0.85", datawindow_name="values")

# Price break at qty 6: 0.82 multiplier
await window.change_data("VALUES", "break1", "6", datawindow_name="values")
await window.change_data("VALUES", "calculation_value2", "0.82", datawindow_name="values")

# Price break at qty 25: 0.78 multiplier
await window.change_data("VALUES", "break2", "25", datawindow_name="values")
await window.change_data("VALUES", "calculation_value3", "0.78", datawindow_name="values")

# Price break at qty 100: 0.75 multiplier
await window.change_data("VALUES", "break3", "100", datawindow_name="values")
await window.change_data("VALUES", "calculation_value4", "0.75", datawindow_name="values")
```

**C#**

```csharp
// Base multiplier: 0.85 for qty 1+
await ChangeDataAsync(client, baseUrl, windowId,
    "VALUES", "values", "calculation_value1", "0.85");

// Price break at qty 6: 0.82 multiplier
await ChangeDataAsync(client, baseUrl, windowId,
    "VALUES", "values", "break1", "6");
await ChangeDataAsync(client, baseUrl, windowId,
    "VALUES", "values", "calculation_value2", "0.82");

// Price break at qty 25: 0.78 multiplier
await ChangeDataAsync(client, baseUrl, windowId,
    "VALUES", "values", "break2", "25");
await ChangeDataAsync(client, baseUrl, windowId,
    "VALUES", "values", "calculation_value3", "0.78");

// Price break at qty 100: 0.75 multiplier
await ChangeDataAsync(client, baseUrl, windowId,
    "VALUES", "values", "break3", "100");
await ChangeDataAsync(client, baseUrl, windowId,
    "VALUES", "values", "calculation_value4", "0.75");
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
# Step 1: Set page type to Discount Group
await window.change_data("FORM", "price_page_type_cd",
                         "Supplier / Discount Group", datawindow_name="form")

# Step 2: Company ID first
await window.change_data("FORM", "company_id", "ACME", datawindow_name="form")

# Step 3: Discount group (NOT product_group_id)
await window.change_data("FORM", "discount_group_id", "DG001", datawindow_name="form")

# Step 4: Supplier
await window.change_data("FORM", "supplier_id", "10050", datawindow_name="form")

# Steps 5-11: Same as product group pages...
```

**C#**

```csharp
// Step 1: Set page type to Discount Group
await ChangeDataAsync(client, baseUrl, windowId,
    "FORM", "form", "price_page_type_cd", "Supplier / Discount Group");

// Step 2: Company ID first
await ChangeDataAsync(client, baseUrl, windowId,
    "FORM", "form", "company_id", "ACME");

// Step 3: Discount group (NOT product_group_id)
await ChangeDataAsync(client, baseUrl, windowId,
    "FORM", "form", "discount_group_id", "DG001");

// Step 4: Supplier
await ChangeDataAsync(client, baseUrl, windowId,
    "FORM", "form", "supplier_id", "10050");

// Steps 5-11: Same as product group pages...
```

<!-- /tabs -->

### OData Queries for Both Page Types

When querying price pages, check both `product_group_id` and `discount_group_id`:

<!-- tabs -->

**Python**

```python
# Get ALL active pages for a supplier (both types)
params = {
    "$filter": (
        f"supplier_id eq {supplier_id} "
        f"and row_status_flag eq 704 "
        f"and (product_group_id ne null or discount_group_id ne null)"
    ),
    "$select": (
        "price_page_uid,description,price_page_type_cd,"
        "product_group_id,discount_group_id,supplier_id"
    ),
}
```

**C#**

```csharp
// Get ALL active pages for a supplier (both types)
var filter = $"supplier_id eq {supplierId} " +
    "and row_status_flag eq 704 " +
    "and (product_group_id ne null or discount_group_id ne null)";
var select = "price_page_uid,description,price_page_type_cd," +
    "product_group_id,discount_group_id,supplier_id";

var queryUrl = $"{baseUrl}/odataservice/odata/table/sales_price_page" +
    $"?$filter={Uri.EscapeDataString(filter)}&$select={Uri.EscapeDataString(select)}";
var resp = await client.GetAsync(queryUrl);
resp.EnsureSuccessStatusCode();
var data = JObject.Parse(await resp.Content.ReadAsStringAsync());
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
# Switch to VALUES tab
await window.select_tab("VALUES")

# Set calculation method
await window.change_data("VALUES", "calculation_method_cd", "Multiplier",
                         datawindow_name="values")

# Configure dollar-based totaling
await window.change_data("VALUES", "totaling_method_cd", "Discount Group",
                         datawindow_name="values")
await window.change_data("VALUES", "totaling_basis_cd", "Supplier List Price",
                         datawindow_name="values")

# Set dollar-based breaks (total order value thresholds)
# $0-$4,999: 0.85 multiplier
await window.change_data("VALUES", "calculation_value1", "0.85",
                         datawindow_name="values")

# $5,000-$9,999: 0.82 multiplier
await window.change_data("VALUES", "break1", "5000", datawindow_name="values")
await window.change_data("VALUES", "calculation_value2", "0.82",
                         datawindow_name="values")

# $10,000-$14,999: 0.78 multiplier
await window.change_data("VALUES", "break2", "10000", datawindow_name="values")
await window.change_data("VALUES", "calculation_value3", "0.78",
                         datawindow_name="values")

# $15,000-$19,999: 0.75 multiplier
await window.change_data("VALUES", "break3", "15000", datawindow_name="values")
await window.change_data("VALUES", "calculation_value4", "0.75",
                         datawindow_name="values")

# $20,000+: 0.72 multiplier
await window.change_data("VALUES", "break4", "20000", datawindow_name="values")
await window.change_data("VALUES", "calculation_value5", "0.72",
                         datawindow_name="values")
```

**C#**

```csharp
// Switch to VALUES tab
var tabPayload = new JObject { ["WindowId"] = windowId, ["PageName"] = "VALUES" };
var tabContent = new StringContent(tabPayload.ToString(), Encoding.UTF8, "application/json");
await client.PutAsync($"{baseUrl}/api/ui/interactive/v2/tab", tabContent);

// Set calculation method
await ChangeDataAsync(client, baseUrl, windowId,
    "VALUES", "values", "calculation_method_cd", "Multiplier");

// Configure dollar-based totaling
await ChangeDataAsync(client, baseUrl, windowId,
    "VALUES", "values", "totaling_method_cd", "Discount Group");
await ChangeDataAsync(client, baseUrl, windowId,
    "VALUES", "values", "totaling_basis_cd", "Supplier List Price");

// Set dollar-based breaks (total order value thresholds)
// $0-$4,999: 0.85 multiplier
await ChangeDataAsync(client, baseUrl, windowId,
    "VALUES", "values", "calculation_value1", "0.85");

// $5,000-$9,999: 0.82 multiplier
await ChangeDataAsync(client, baseUrl, windowId,
    "VALUES", "values", "break1", "5000");
await ChangeDataAsync(client, baseUrl, windowId,
    "VALUES", "values", "calculation_value2", "0.82");

// $10,000-$14,999: 0.78 multiplier
await ChangeDataAsync(client, baseUrl, windowId,
    "VALUES", "values", "break2", "10000");
await ChangeDataAsync(client, baseUrl, windowId,
    "VALUES", "values", "calculation_value3", "0.78");

// $15,000-$19,999: 0.75 multiplier
await ChangeDataAsync(client, baseUrl, windowId,
    "VALUES", "values", "break3", "15000");
await ChangeDataAsync(client, baseUrl, windowId,
    "VALUES", "values", "calculation_value4", "0.75");

// $20,000+: 0.72 multiplier
await ChangeDataAsync(client, baseUrl, windowId,
    "VALUES", "values", "break4", "20000");
await ChangeDataAsync(client, baseUrl, windowId,
    "VALUES", "values", "calculation_value5", "0.72");
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
# Switch to COSTS tab
await window.select_tab("COSTS")

# Set commission cost calculation method
await window.change_data("COSTS", "commission_cost_calc_method_cd", "Multiplier",
                         datawindow_name="costs")

# Set commission cost value (1.01 = pass-through costing with 1% margin)
await window.change_data("COSTS", "commission_cost_value1", "1.01",
                         datawindow_name="costs")
```

**C#**

```csharp
// Switch to COSTS tab
var tabPayload = new JObject { ["WindowId"] = windowId, ["PageName"] = "COSTS" };
var tabContent = new StringContent(tabPayload.ToString(), Encoding.UTF8, "application/json");
await client.PutAsync($"{baseUrl}/api/ui/interactive/v2/tab", tabContent);

// Set commission cost calculation method
await ChangeDataAsync(client, baseUrl, windowId,
    "COSTS", "costs", "commission_cost_calc_method_cd", "Multiplier");

// Set commission cost value (1.01 = pass-through costing with 1% margin)
await ChangeDataAsync(client, baseUrl, windowId,
    "COSTS", "costs", "commission_cost_value1", "1.01");
```

<!-- /tabs -->

### Common Pattern: Pass-Through Costing

For pages where commission cost should simply pass through at cost:

<!-- tabs -->

**Python**

```python
await window.select_tab("COSTS")
await window.change_data("COSTS", "commission_cost_calc_method_cd", "Multiplier",
                         datawindow_name="costs")
await window.change_data("COSTS", "commission_cost_value1", "1.01",
                         datawindow_name="costs")
```

**C#**

```csharp
var tabPayload = new JObject { ["WindowId"] = windowId, ["PageName"] = "COSTS" };
var tabContent = new StringContent(tabPayload.ToString(), Encoding.UTF8, "application/json");
await client.PutAsync($"{baseUrl}/api/ui/interactive/v2/tab", tabContent);

await ChangeDataAsync(client, baseUrl, windowId,
    "COSTS", "costs", "commission_cost_calc_method_cd", "Multiplier");
await ChangeDataAsync(client, baseUrl, windowId,
    "COSTS", "costs", "commission_cost_value1", "1.01");
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
PRICING_BOOK_ID = "19"
SUPPLIER_ID = "19"
EFFECTIVE_DATE = "2013-02-21"
EXPIRATION_DATE = "2020-02-21"
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
const string PricingBookId = "19";                     // identify one pricing page
const string SupplierId = "19";
const string EffectiveDate = "2013-02-21";
const string ExpirationDate = "2020-02-21";
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
