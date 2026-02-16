# Multi-Company Inventory Management

> **Disclaimer:** This is unofficial, community-created documentation for Epicor Prophet 21 APIs. It is not affiliated with, endorsed by, or supported by Epicor Software Corporation. Use at your own risk.

---

## Overview

In a multi-company Prophet 21 (P21) environment, inventory items are often shared across companies but require distinct configuration (Suppliers, Locations) for each entity.

A common challenge arises when attempting to "add" an existing item to a new company or location. Since the Item ID (`ItemId`) must be unique globally within the P21 database, attempting to `POST` the item again for a new company will result in a duplicate key error.

This guide details the correct workflow: **Update (PUT)** the existing item with appended company/location data, rather than creating a new one.

---

## The Problem: "Item ID already exists"

When you have an item (e.g., `1001`) already set up for Company A, and you want to add it to Company B, you might intuitively try to `POST` the item again with Company B's data.

### Fails: POST Request
```http
POST /api/inventory/parts
{
  "ItemId": "1001",
  "CompanyId": "CompanyB",
  ...
}
```

### Error Response
You will likely receive an error indicating the item already exists:
```json
{
    "ErrorMessage": "Error updating 1001: Error updating inv_mast: The proposed item ID already exists in the database.",
    "ErrorType": "P21.Common.Exceptions.Prophet21Exception"
}
```

This happens because `inv_mast` (Inventory Master) is the global definition of the part, while `inv_loc` (Inventory Location) and `inventory_supplier` differ per company.

---

## The Solution: GET, Append, PUT

To add an existing item to a new company/location, you must:

1.  **GET** the existing item using `extendedproperties=*` (or specific properties).
2.  **Append** the new Company/Location/Supplier records to the existing lists in the response.
3.  **PUT** the updated object back to the API.

### Workflow

1.  **Check if item exists**: Query the item by ID.
2.  **If it exists**:
    *   Retrieve full details (`extendedproperties=*`).
    *   Add your new `Location`, `Supplier`, `LocationSupplier`, and `UnitOfMeasure` objects to the respective lists.
    *   Send a `PUT` request to update the item.
3.  **If it does not exist**:
    *   Send a `POST` request to create it (standard creation process).

---

## Step-by-Step Implementation

### 1. GET Existing Item

Retrieve the item including all its related tables.

**Request:**
```http
GET /api/inventory/parts/002.047?extendedproperties=*
```
*Optimized Request (fetch only what you need):*
```http
GET /api/inventory/parts/002.047?extendedproperties=Locations,Suppliers,LocationSuppliers,UnitsOfMeasure
```

**Response (Simplified):**
```json
{
    "ItemId": "002.047",
    "InvMastUid": 15,
    "ItemDesc": "M14 HEXAGON NUT CLASS 8",
    "Locations": {
        "list": [
            {
                "ItemId": "002.047",
                "LocationId": 13,
                "CompanyId": "13",
                "QtyOnHand": 100.0
            }
        ]
    },
    "Suppliers": {
        "list": [
            {
                "ItemId": "002.047",
                "SupplierId": 13
            }
        ]
    }
}
```

### 2. Append New Data

Add the new company configuration to the arrays. Do **not** remove existing entries, or you might accidentally delete them (depending on API behavior, though usually P21 merges or errors on delete without a flag).

**Constructing the PUT Body:**

```json
{
    "ItemId": "002.047",
    "InvMastUid": 15,
    "ItemDesc": "M14 HEXAGON NUT CLASS 8",
    "ObjectName": "inv_mast",
    "Locations": {
        "list": [
            {
                "ItemId": "002.047",
                "LocationId": 13,
                "CompanyId": "13",
                "ObjectName": "inv_loc"
            },
            {
                "ItemId": "002.047",
                "LocationId": 18,
                "CompanyId": "18",
                "GlAccountNo": "14100",
                "RevenueAccountNo": "34100",
                "CosAccountNo": "44100",
                "Sellable": "Y",
                "Stockable": "Y",
                "ObjectName": "inv_loc"
            }
        ]
    },
    "Suppliers": {
        "list": [
            {
                "ItemId": "002.047",
                "SupplierId": 13,
                "ObjectName": "inventory_supplier"
            },
            {
                "ItemId": "002.047",
                "SupplierId": 18,
                "DivisionId": 18,
                "LeadTimeDays": 5,
                "ObjectName": "inventory_supplier"
            }
        ]
    }
}
```

### 3. PUT Update

Send the updated payload back to the server.

**Request:**
```http
PUT /api/inventory/parts/002.047
Content-Type: application/json

{ ... JSON payload from Step 2 ... }
```

**Response:**
On success, you will receive the updated item object. On failure, check the `ErrorMessage`.

---

## Common Challenges & Tips

### 1. `UnitsOfMeasure` (UOM)
UOMs are typically defined at the `inv_mast` level, meaning they are shared across all companies. You usually do not need to duplicate UOMs for each company unless you have company-specific UOM overrides (which are rare/complex).

If the UOMs are global:
*   Ensure they are present in your PUT payload.
*   You don't need to add "Company 18" specific UOMs if they are just standard "EA", "BOX", etc.

### 2. "Account doesn't exist for company" Error
```json
"ErrorMessage": "Error updating 002.047: Error updating inv_mast: This account doesn't exist for company 18."
```
**Cause:** You are trying to adding a Location Record that references a GL Account (e.g., `GlAccountNo`, `RevenueAccountNo`) that is not valid for the new Company (Company 18).
**Fix:** Ensure you are mapping the correct GL Accounts for the specific Company ID you are adding.

### 3. Large Dataset Automation
If you have 50k+ items to update:
1.  **Batching**: Do not try to process all 50k in one go. Process in chunks (e.g., 10000 items).
2.  **Concurrency**: Use multiple threads/workers if the API limit permits, but be careful of locking `inv_mast`.
3.  **Error Handling**: Wrap each Item update in a try-catch block. Log failures to a CSV file for manual review.
    *   *Retry logic*: Sometimes P21 locks tables. Implementing a retry mechanism (wait 1s, retry) can resolve transient lock errors.


## Example: Automation Logic (Pseudo-code)

```python
def process_item(item_id, new_company_data):
    # 1. Check if item exists
    try:
        current_item = api.get(f"/api/inventory/parts/{item_id}?extendedproperties=Locations,Suppliers")
    except 404:
        # Item doesn't exist globaly - CREATE IT
        return api.post("/api/inventory/parts", new_company_data)

    # 2. Item exists - APPEND new data
    # Check if this company/location already exists to avoid duplicates
    if company_already_linked(current_item, new_company_data['CompanyId']):
        return "Already Linked"

    # Append new records
    current_item['Locations']['list'].append(new_company_data['Location'])
    current_item['Suppliers']['list'].append(new_company_data['Supplier'])
    
    # 3. UPDATE
    return api.put(f"/api/inventory/parts/{item_id}", current_item)
```
