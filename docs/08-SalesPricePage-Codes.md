# Sales Price Page Dropdown Codes

## Overview

When working with the SalesPricePage window via the Interactive API, dropdown fields require specific **display values** (not codes). This document provides the mappings discovered through API testing.

**Important:** P21's code tables (`code_p21`) may not be accessible via OData in all environments. These values were discovered by testing the Interactive API directly.

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

```python
# Correct - use display value
window.change_data("VALUES", "calculation_method_cd", "Mark Up", datawindow_name="values")

# Incorrect - do not use code
window.change_data("VALUES", "calculation_method_cd", "229", datawindow_name="values")
```

---

## Price Page Type (FORM Tab)

The `price_page_type_cd` field determines the page type.

| Code | Display Value |
|------|---------------|
| 210 | Customer |
| 211 | Customer / Item |
| 214 | Supplier / Product Group |
| 215 | Supplier / Discount Group |

---

## Pricing Method (FORM Tab)

The `pricing_method_cd` field controls how the source price is used.

| Code | Display Value |
|------|---------------|
| 220 | Source |
| 221 | Margin |
| 222 | Fixed |

---

## Source Price (FORM Tab)

The `source_price_cd` field determines the base price source.

| Code | Display Value |
|------|---------------|
| 200 | Supplier List Price |
| 201 | Replacement Cost |
| 202 | Average Cost |

---

## Cost Type (COSTS Tab)

| Code | Display Value |
|------|---------------|
| 220 | Value |
| 221 | Source |
| 222 | Order |

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

---

## Related

- [Interactive API](04-Interactive-API.md)
- [Error Handling](06-Error-Handling.md)
