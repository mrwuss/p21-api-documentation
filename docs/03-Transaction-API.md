# Transaction API

> **Disclaimer:** This is unofficial, community-created documentation for Epicor Prophet 21 APIs. It is not affiliated with, endorsed by, or supported by Epicor Software Corporation. All product names, trademarks, and registered trademarks are property of their respective owners. Use at your own risk.

---

## Overview

The Transaction API is a **stateless RESTful** web service for bulk data manipulation in P21. It allows creating and updating records across any P21 window without maintaining session state.

### Key Characteristics

- **Stateless** - No session management required
- **Bulk operations** - Process multiple records in single request
- **Service-based** - Each P21 window maps to a service
- **JSON or XML** - Supports both formats
- **Async support** - Long operations can run asynchronously

### When to Use

- Creating multiple records (orders, invoices, etc.)
- Bulk updates
- Automated data import
- Integration with external systems

---

## Endpoints

All Transaction API endpoints use the UI Server URL. First, obtain the UI Server URL:

```http
GET https://{hostname}/api/ui/router/v1?urlType=external
```

Then use the returned URL as base:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v2/services` | GET | List available services (transaction business objects only — report services are not listed; see [PDF Report Generation](#pdf-report-generation)) |
| `/api/v2/definition/{name}` | GET | Get service schema and template |
| `/api/v2/defaults/{name}` | GET | Get default values for a service |
| `/api/v2/transaction/get` | POST | Retrieve existing records |
| `/api/v2/transaction` | POST | Create or update records (sync) |
| `/api/v2/transaction/async` | POST | Async create/update (returns RequestId) |
| `/api/v2/transaction/async/callback` | POST | Async with callback URL |
| `/api/v2/transaction/async?id={id}` | GET | Check async request status |
| `/api/v2/commands` | POST | Process special commands (see [Commands Endpoint](#commands-endpoint)) |
| `/api/v2/process/pdfreport` | POST | Generate PDF reports (see [PDF Report Generation](#pdf-report-generation)) |

> **Service Explorer:** The P21 middleware includes a web-based Transaction API Service Explorer tool for browsing available services and their definitions interactively. Access it from the SOA Middleware admin pages.

> **Read-after-write verification:** `POST /api/v2/transaction/get` is also the recommended way to verify that an Interactive API write actually persisted — a save can report success without persisting a sub-record, and the read-back is the only way to recover a server-generated key. See [Verifying Writes](04-Interactive-API.md#verifying-writes-dont-trust-save-status-alone) in the Interactive API guide.

---

## Authentication

Include the Bearer token in the Authorization header:

```http
POST /api/v2/transaction HTTP/1.1
Host: {ui-server-host}
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json
```

See [Authentication](00-Authentication.md) for token generation.

---

## Request Structure

### TransactionSet

The main request body for create/update operations:

```json
{
    "Name": "ServiceName",
    "UseCodeValues": false,
    "Transactions": [
        {
            "Status": "New",
            "DataElements": [
                {
                    "Name": "TABPAGE_1.table_name",
                    "Type": "Form",
                    "Keys": [],
                    "Rows": [
                        {
                            "Edits": [
                                {"Name": "field_name", "Value": "field_value"}
                            ],
                            "RelativeDateEdits": []
                        }
                    ]
                }
            ]
        }
    ]
}
```

### TransactionSet Fields

| Field | Required | Description |
|-------|----------|-------------|
| `Name` | Yes | Service name (e.g., "Order", "SalesPricePage") |
| `UseCodeValues` | No | If `true`, use code values; if `false` (default), use display values |
| `Transactions` | Yes | Array of Transaction objects to process |
| `IgnoreDisabled` | No | If `true`, skip disabled fields instead of erroring |
| `Query` | No | Optional query filter for the service |
| `FieldMap` | No | Optional field name mappings |
| `TransactionSplitMethod` | No | `"Standard"` (default) or `"NoSplit"` |
| `Parameters` | No | Additional service-specific parameters |

### Transaction Fields

| Field | Description |
|-------|-------------|
| `Status` | `"New"` for create, `"Passed"` on success, `"Failed"` on error |
| `DataElements` | Array of tabs/sections in the window |
| `Documents` | Optional array of file attachments |

### DataElement Fields

| Field | Description |
|-------|-------------|
| `Name` | Tab and table name (e.g., `"TABPAGE_1.order"`) |
| `Type` | `"Form"` for single record, `"List"` for grid/multiple rows |
| `Keys` | Key field names for List-type elements (used to identify rows) |
| `Rows` | Array of Row objects |

### Row / Edit Fields

| Field | Description |
|-------|-------------|
| `Edits` | Array of `{Name, Value}` pairs for field values |
| `RelativeDateEdits` | Array of date edits using relative offsets (e.g., "today + 30 days") instead of absolute dates |

Each **Edit** object supports:

| Field | Required | Description |
|-------|----------|-------------|
| `Name` | Yes | Field name |
| `Value` | Yes | Field value |
| `IgnoreIfEmpty` | No | If `true`, skip this edit when Value is empty instead of sending a blank |

---

## Common Services

| Service | P21 Window | Purpose |
|---------|------------|---------|
| `Order` | Order Entry | Create/edit sales orders |
| `Invoice` | Invoice Entry | Create/edit invoices |
| `Customer` | Customer Maintenance | Customer records |
| `Supplier` | Supplier Maintenance | Supplier records |
| `SalesPricePage` | Sales Price Page | Price page management |
| `PurchaseOrder` | Purchase Order Entry | Create POs |
| `InventoryMaster` | Inventory Maintenance | Item records |
| `Task` | Task Entry | Create tasks/activities |
| `m_storedprocedureexecutor` | Stored Procedure Executor | Load and execute stored procedure definitions (see [Stored Procedure Executor](#stored-procedure-executor)) |

### Report Services

| Service | P21 Window | Purpose |
|---------|------------|---------|
| `m_reprintpurchaseorders` | PO Reprint | Purchase order PDF reprints (see [PDF Report Generation](#pdf-report-generation)) |
| `m_reprintpicktickets` | Pick Ticket Reprint | Pick ticket PDF reprints |

### Production, Assembly & Labor Services

| Service | P21 Window | Purpose |
|---------|------------|---------|
| `ProductionOrder` | Production Order Entry | Create and manage production orders |
| `Assembly` | Assembly Maintenance | Assembly/BOM definitions for items (see [Assembly Service](#assembly-service)) |
| `JobContractPricing` | Job Contract Pricing | Job contract price pages with quantity breaks (see [JobContractPricing Service](#jobcontractpricing-service)) |
| `TimeEntry` | Time Entry | Record labor hours against production orders |
| `TimeEntrySO` | Time Entry (Service Order) | Record labor hours against service orders |
| `Labor` | Labor Maintenance | Labor code definitions and rates |
| `LaborProcess` | Labor Process Maintenance | Labor process templates |
| `WorkCenter` | Work Center Maintenance | Work center definitions |
| `Operation` | Operation Maintenance | Operation definitions |
| `PredefinedRouting` | Predefined Routing | Routing templates |
| `ProductionOrderProcessing` | Production Order Processing | Process/complete production orders |

See [Production & Labor API](12-Production-Labor-API.md) for detailed field definitions and examples.

---

## Response Format

### Success Response

```json
{
    "Messages": ["Transaction 1:: "],
    "Results": {
        "Name": "Order",
        "Transactions": [
            {
                "DataElements": [
                    {
                        "Name": "TABPAGE_1.order",
                        "Rows": [{
                            "Edits": [
                                {"Name": "order_no", "Value": "1013938"}
                            ]
                        }]
                    }
                ],
                "Status": "Passed"
            }
        ]
    },
    "Summary": {
        "Succeeded": 1,
        "Failed": 0,
        "Other": 0
    }
}
```

### Error Response

```json
{
    "Messages": [
        "Transaction 1:: Customer ID is required"
    ],
    "Results": null,
    "Summary": {
        "Succeeded": 0,
        "Failed": 1,
        "Other": 0
    }
}
```

---

## Field Order Matters

For some services, the order of fields in the request is significant. The API processes fields sequentially, and some fields trigger validation or auto-population of other fields.

### Example: SalesPricePage

Fields must be set in this order:
1. `price_page_type_cd` - Triggers type-specific validation
2. `company_id` - Required before product group
3. `product_group_id` or `discount_group_id`
4. `supplier_id`
5. Other fields...

---

## UseCodeValues

This setting controls how dropdown/checkbox values are interpreted:

| UseCodeValues | Pass | Example |
|---------------|------|---------|
| `false` (default) | Display value | `"Cancelled": "ON"` |
| `true` | Code value | `"Cancelled": "Y"` |

**Recommendation**: Use `false` (display values) for better readability.

---

## Async Operations

For long-running operations, use the async endpoint. Async requests run in a dedicated session (avoiding session pool contamination) but have a limited queue.

> **Queue capacity:** The server defaults to only **2 concurrent async requests** (`AsyncRequests.QueueCapacity` in Web.config). Additional requests are queued and may time out under heavy load. Plan batch operations accordingly.

### Submit Async Request

```http
POST /api/v2/transaction/async
```

Response includes a request ID:

```json
{
    "RequestId": "ad8f6f74-bc27-4324-a812-0ca7d6cc6a7d",
    "Status": "Active"
}
```

### Check Status

```http
GET /api/v2/transaction/async?id=ad8f6f74-bc27-4324-a812-0ca7d6cc6a7d
```

Response:

```json
{
    "RequestId": "ad8f6f74-bc27-4324-a812-0ca7d6cc6a7d",
    "Status": "Complete",
    "Messages": "...",
    "CompletedDate": "2025-01-15T16:34:53"
}
```

Status values: `Active`, `Complete`, `Failed`

> **Note:** The async POST returns HTTP **202 Accepted** (not 200) to indicate the request was queued successfully.

### With Callback

Use the callback endpoint to receive notification when complete:

```json
{
    "Content": {
        "Name": "Order",
        "Transactions": [...]
    },
    "Callback": {
        "Url": "https://your-server.com/webhook",
        "Method": "POST",
        "ContentType": "application/json",
        "Headers": [
            {"Name": "X-API-Key", "Value": "your-key"}
        ]
    }
}
```

---

## Commands Endpoint

Some P21 services **cannot** use the standard `/api/v2/transaction` endpoint. These must use the commands endpoint instead:

```http
POST /api/v2/commands
```

### Services Requiring Commands Endpoint

| Service | Purpose |
|---------|---------|
| `TransferPalletShipping` | Pallet transfer shipping |
| `SupplierNotepad` | Supplier notes |
| `VendorNotepad` | Vendor notes |
| `ItemNotepad` | Item notes |
| `CustomerPartNumberNotes` | Customer part number notes |
| `RestateForeignCurrencyAccount` | Foreign currency restatement |
| `ServiceNoteTemplate` | Service note templates |
| `ReverseARPayment` | AR payment reversal |
| `VATReturnWorksheet` | VAT return processing |
| `SlabAdjustment` | Slab adjustments |
| `ContainerBuilding` | Container building |

> **Important:** If you send these services to the standard `/transaction` endpoint, they will fail. Always check the service documentation or test with the Service Explorer to determine which endpoint to use.

---

## Special Scenarios

### Field and DataElement Ordering

Some services require specific ordering of DataElements or Edits within a request. The API processes them sequentially, and some fields trigger validation or auto-population of other fields.

**Credit Card Payment Orders:**
DataElements must appear in this order:
1. Order header
2. Items
3. Remittances
4. CC Transaction Response (`TP_CCTRANSACTIONRESPONSE.cctransactionresponse`)

**Multiple Lot Items:**
When creating items with lot tracking, interleave item and lot DataElements:
1. Item 1 → Lot 1
2. Item 2 → Lot 2
3. *(not: Item 1 → Item 2 → Lot 1 → Lot 2)*

**Task Creation with Dates:**
The `target_date` edit must appear before `start_date` in the Edits array (due to validation ordering).

**SalesPricePage Fields:**
1. `price_page_type_cd` — triggers type-specific validation
2. `company_id` — required before product group
3. `product_group_id` or `discount_group_id`
4. `supplier_id`
5. Other fields...

---

## Examples

### Get Service Definition

<!-- tabs -->
```python
import httpx

response = httpx.get(
    f"{ui_server_url}/api/v2/definition/Order",
    headers={"Authorization": f"Bearer {token}"},
    verify=False
)
response.raise_for_status()

definition = response.json()
# definition["Template"] - blank template for creating records
# definition["TransactionDefinition"] - field definitions with valid values
```

```csharp
var response = await client.GetAsync(
    $"{uiServerUrl}/api/v2/definition/Order");
response.EnsureSuccessStatusCode();

var definition = JObject.Parse(
    await response.Content.ReadAsStringAsync());
// definition["Template"] - blank template for creating records
// definition["TransactionDefinition"] - field definitions with valid values
```
<!-- /tabs -->

The definition is the **authoritative schema map** for a service. The response shape is `{"Name": ..., "TransactionDefinition": {"KeyDefinitions": [...], "DataElementDefinitions": [...]}, "Template": {...}}` — the elements live under `TransactionDefinition.DataElementDefinitions`. Each element carries:

| Field | Description |
|-------|-------------|
| `Name` | DataElement name used in payloads (e.g., `TABPAGE_7.tp_7_dw_7`) |
| `DatawindowName` | Underlying datawindow (e.g., `d_update_po_hdr_notes_po_entry`) |
| `Type` | `Form` or `List` |
| `KeyFields` | Fields that identify a row in `Keys` (e.g., `["note_id"]`) |
| `FieldDefinitions[]` | Every writable field — `Name`, `DbColumnName`, `DataType`, `Required` |
| `ParentText`, `BusinessObjectName` | Display/back-end context for the element |

Use it to discover which tab/datawindow a given table lives on and exactly which column names and required fields a write needs. The API field `Name` is frequently **not** what you'd guess from the underlying table column — check `DbColumnName` in `FieldDefinitions` to map between the two.

> **Warning — don't derive `TABPAGE_N` from the visible tab order:** `TABPAGE_N` names are **not** sequential with the tabs visible in the P21 UI — windows carry many disabled/hidden tab pages (PurchaseOrder has 37), so the grid that *looks* like the second tab can be `TABPAGE_17` (`tp_17_dw_17`). When cross-referencing the definition against live Interactive calls, match on the **datawindow name** (`tp_N_dw_N` / `d_...`) or read the Interactive window's `TabPageList` (`GET /api/ui/interactive/v2/window?id={windowId}`) — never count tabs on screen. On the servers tested (25.2/26.x), the Interactive window's `TABPAGE_N` names matched the definition's 1:1.

### Create Order

<!-- tabs -->
```python
payload = {
    "Name": "Order",
    "UseCodeValues": False,
    "Transactions": [{
        "Status": "New",
        "DataElements": [
            {
                "Name": "TABPAGE_1.order",
                "Type": "Form",
                "Keys": [],
                "Rows": [{
                    "Edits": [
                        {"Name": "customer_id", "Value": "100198"}
                    ],
                    "RelativeDateEdits": []
                }]
            },
            {
                "Name": "TP_ITEMS.items",
                "Type": "List",
                "Keys": [],
                "Rows": [{
                    "Edits": [
                        {"Name": "oe_order_item_id", "Value": "ITEM123"},
                        {"Name": "unit_quantity", "Value": "1"}
                    ],
                    "RelativeDateEdits": []
                }]
            }
        ]
    }]
}

response = httpx.post(
    f"{ui_server_url}/api/v2/transaction",
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    },
    json=payload,
    verify=False
)
response.raise_for_status()
```

```csharp
var payload = new
{
    Name = "Order",
    UseCodeValues = false,
    Transactions = new[] {
        new {
            Status = "New",
            DataElements = new object[] {
                new {
                    Name = "TABPAGE_1.order",
                    Type = "Form",
                    Keys = Array.Empty<string>(),
                    Rows = new[] {
                        new { Edits = new[] {
                            new { Name = "customer_id", Value = "100198" }
                        }}
                    }
                },
                new {
                    Name = "TP_ITEMS.items",
                    Type = "List",
                    Keys = Array.Empty<string>(),
                    Rows = new[] {
                        new { Edits = new[] {
                            new { Name = "oe_order_item_id", Value = "ITEM123" },
                            new { Name = "unit_quantity", Value = "1" }
                        }}
                    }
                }
            }
        }
    }
};

var content = new StringContent(
    JsonConvert.SerializeObject(payload),
    Encoding.UTF8, "application/json");
var response = await client.PostAsync(
    $"{uiServerUrl}/api/v2/transaction", content);
```
<!-- /tabs -->

---

## Service Reference

### JobContractPricing Service

The `JobContractPricing` service creates **and updates** job contract price pages -- customer-specific pricing agreements with optional quantity breaks. It has 25 DataElements; the key ones are documented below.

#### Service Definition

```http
GET /api/v2/definition/JobContractPricing
```

#### Header -- `FORM.d_dw_job_price_hdr` (Form)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `company_id` | Char | Yes | Company ID |
| `contract_no` | Char | No | Contract number (auto-assigned if blank) |
| `customer_id` | Decimal | Yes | Customer ID |
| `taker` | Char | No | Order taker / salesperson |
| `end_date` | Datetime | No | Contract end date |
| `corp_address_id` | Long | No | Corporate address ID (read-only after initial save) |
| `ship_to_id` | Long | No | Ship-to address ID |
| `job_no` | Char | No | Associated job number |
| `approved` | Char | No | Approval flag |
| `cancelled` | Char | No | Cancellation flag |
| `consignment_flag` | Char | No | Consignment contract flag |

> **Important:** `corp_address_id` must be set during initial creation. Based on production reports, this field becomes read-only after the contract is saved.

#### Customer/Ship To -- `CUSTOMER_SHIP_TO.customer_ship_to` (List)

| Field | Type | Description |
|-------|------|-------------|
| `customer_id` | Decimal | Customer ID |
| `ship_to_id` | Long | Ship-to address ID |
| `activation_date` | Datetime | Ship-to activation date |
| `expiration_date` | Datetime | Ship-to expiration date |
| `address_name` | Char | Ship-to address name |

#### Line Items -- `JOBPRICELINE.jobpriceline` (List, 29 fields)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `item_id` | Char | Yes | Item ID |
| `uom` | Char | Yes | Unit of measure |
| `pricing_method` | Char | Yes | Pricing method (see valid values below) |
| `price` | Decimal | Conditional | Fixed price (for non-break lines only) |
| `multiplier` | Decimal | Conditional | Price multiplier (for break lines only) |
| `source_price` | Char | Conditional | Source price reference (for break lines only) |
| `customer_part_no` | Char | No | Customer's part number |

**`pricing_method` valid values:**

| Value | Use Case |
|-------|----------|
| `Pricing Libraries` | Use pricing library rules |
| `Source` | Source-based pricing with quantity breaks |
| `Price` | Fixed price (no breaks) |
| `None` | No pricing |

**Non-break vs break lines:**

- **Non-break (fixed price):** Set `pricing_method` to `"Price"` and `price` to the value. Do NOT send `source_price` or `multiplier`.
- **Break (quantity-based):** Set `pricing_method` to `"Source"`, `source_price` to `"Supplier List Price"` (or other source), and `multiplier` to `1` (or desired multiplier). Do NOT send `price`.

#### Values/Breaks -- `VALUES.values` (Form, 46 fields)

The VALUES DataElement defines quantity break tiers for a line item.

| Field | Type | Description |
|-------|------|-------------|
| `calculation_method_cd` | Char | Calculation method (see valid values below) |
| `break1` through `break14` | Decimal | Break threshold quantities |
| `calculation_value` through `calculation_value14` | Decimal | Price/value at each tier |
| `other_cost` through `other_cost14` | Decimal | Other cost at each tier |

**`calculation_method_cd` valid values:** `Difference`, `Multiplier`, `Mark up`, `Percentage`, `Fixed Price`

##### Break Tier Structure

The service supports 15 price levels: 14 break thresholds (`break1`-`break14`) plus one catch-all tier. Break values represent the **starting quantity of the next tier** (advance thresholds).

Rules:
- `break1` should NOT be 0 -- it defines where the second tier starts
- The last active tier has its break set to `0`, signaling no further advance
- `calculation_value` (no suffix) is the first tier; `calculation_value2` through `calculation_value14` are tiers 2-14; the 15th tier has no break threshold

**Example -- 3 tiers with Fixed Price method:**

| Tier | Quantity Range | Field | Value | Break Field | Break Value |
|------|---------------|-------|-------|-------------|-------------|
| 1 | 1-9 | `calculation_value` | `10.00` | `break1` | `10` |
| 2 | 10-49 | `calculation_value2` | `8.50` | `break2` | `50` |
| 3 | 50+ | `calculation_value3` | `7.00` | `break3` | `0` |

Tier 1 applies for quantities 1-9 (below `break1`=10). Tier 2 applies for 10-49 (below `break2`=50). Tier 3 applies for 50+ (`break3`=0 means no further advance).

##### Multi-Line Break Interleaving

VALUES is `Type: Form` (single row), so it applies to the **current JOBPRICELINE cursor position**. For contracts with multiple break lines, you must send a SEPARATE `JOBPRICELINE` DataElement (1 row) followed by its own `VALUES` DataElement for each line. Putting all lines in a single multi-row `JOBPRICELINE` causes only the last line to receive breaks.

**Correct interleaving:**
```text
DataElements:
  1. FORM.d_dw_job_price_hdr (header)
  2. JOBPRICELINE.jobpriceline (Line A -- 1 row)
  3. VALUES.values (breaks for Line A)
  4. JOBPRICELINE.jobpriceline (Line B -- 1 row)
  5. VALUES.values (breaks for Line B)
```

**Incorrect (only Line B gets breaks):**
```text
DataElements:
  1. FORM.d_dw_job_price_hdr (header)
  2. JOBPRICELINE.jobpriceline (Lines A and B -- 2 rows)
  3. VALUES.values (breaks -- applies only to last row)
```

#### Commission Costs

The `JOBPRICECOST` DataElement includes `commission_cost_value` and related commission fields, but these are **disabled** -- the API returns "Column is disabled: commission_cost_value". Commission costs must be set via the Interactive API (JobContractPricing window) after contract creation.

#### Updating an Existing Contract

Use `Status = "New"` to update existing contracts -- there is no separate "Update" or "Existing" status. The Transaction API distinguishes create from update by whether the FORM key fields land on an existing record:

- Leave the FORM `Keys` array empty.
- Send the FORM key fields (`company_id`, `contract_no`, `job_no`) inside `Edits`.
- Also include `end_date` in `Edits` -- the API validates required fields on every submit and rejects with `"Required value missing for End Date"` if it's absent.
- On `JOBPRICELINE`, set `Keys: ["item_id"]` and put the `item_id` value in `Edits` alongside the fields you're changing.

> Empirically verified 2026-05-14: 173 successful price updates against contract `A120-12` on a production tenant. Each call returned HTTP 200 with `Summary.Succeeded = 1`, and OData confirmed each `job_price_line.price` matched the submitted value.

**Example -- update one line's price:**

```python
payload = {
    "Name": "JobContractPricing",
    "UseCodeValues": False,
    "Transactions": [{
        "Status": "New",                          # still "New" for updates
        "DataElements": [
            {
                "Name": "FORM.d_dw_job_price_hdr",
                "Type": "Form",
                "Keys": [],                       # empty
                "Rows": [{
                    "Edits": [
                        {"Name": "company_id",  "Value": "ACME"},
                        {"Name": "contract_no", "Value": "A120-12"},
                        {"Name": "job_no",      "Value": "31"},
                        {"Name": "end_date",    "Value": "2030-01-01"},
                    ],
                    "RelativeDateEdits": [],
                }],
            },
            {
                "Name": "JOBPRICELINE.jobpriceline",
                "Type": "List",
                "Keys": ["item_id"],
                "Rows": [{
                    "Edits": [
                        {"Name": "item_id",        "Value": "WIDGET-001"},
                        {"Name": "uom",            "Value": "EA"},
                        {"Name": "pricing_method", "Value": "Price"},
                        {"Name": "price",          "Value": "36.58"},
                    ],
                    "RelativeDateEdits": [],
                }],
            },
        ],
    }],
}
```

**Notes:**

- **Converting `pricing_method` from `"Source"` to `"Price"`** works in the same call. The previously-set `source_price` and `multiplier` are NOT auto-cleared on the row, but become dormant since the `"Price"` method only reads `price`.
- **Use `POST /api/v2/transaction/get`** to retrieve the existing FORM values (`company_id`, `job_no`, `end_date`) before submitting the update:

  ```json
  {
    "ServiceName": "JobContractPricing",
    "TransactionStates": [{
      "DataElementName": "FORM.d_dw_job_price_hdr",
      "Keys": [{"Name": "contract_no", "Value": "A120-12"}]
    }]
  }
  ```
- **Per-line latency** observed at ~0.8s. For bulk updates, single-line calls are easier to retry on failure than batches.

#### Known Limitations

- **Commission fields disabled:** Cannot set commission costs via Transaction API (see above).
- **`corp_address_id` read-only after save:** Must be set during initial creation.
- **Status `"Existing"` is not a valid Transaction status:** Setting `Transactions[0].Status = "Existing"` (or `"Update"`, `"Change"`) returns HTTP 500 (`NullReferenceException` at `ToInternalBeSpecification`). Use `"New"` for both create and update -- see [Updating an Existing Contract](#updating-an-existing-contract).

#### Example: Create a Job Contract with Break and Non-Break Lines

<!-- tabs -->
```python
import httpx

# Authenticate and get UI server URL
base_url = "https://play.p21server.com"
auth_resp = httpx.post(
    f"{base_url}/api/security/token/v2",
    json={"username": "api_user", "password": "api_pass"},
    verify=False,
)
auth_resp.raise_for_status()
token = auth_resp.json()["AccessToken"]

router_resp = httpx.get(
    f"{base_url}/api/ui/router/v1?urlType=external",
    headers={"Authorization": f"Bearer {token}"},
    verify=False,
)
router_resp.raise_for_status()
ui_server_url = router_resp.json()["Url"].rstrip("/")

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}

# Create a contract with one fixed-price line and one break line
payload = {
    "Name": "JobContractPricing",
    "UseCodeValues": False,
    "Transactions": [{
        "Status": "New",
        "DataElements": [
            # 1. Contract header
            {
                "Name": "FORM.d_dw_job_price_hdr",
                "Type": "Form",
                "Keys": [],
                "Rows": [{
                    "Edits": [
                        {"Name": "company_id", "Value": "ACME"},
                        {"Name": "customer_id", "Value": "100198"},
                        {"Name": "corp_address_id", "Value": "1"},
                        {"Name": "end_date", "Value": "2027-12-31"},
                        {"Name": "approved", "Value": "ON"},
                    ],
                    "RelativeDateEdits": [],
                }],
            },
            # 2. Fixed-price line (no breaks)
            {
                "Name": "JOBPRICELINE.jobpriceline",
                "Type": "List",
                "Keys": ["item_id"],
                "Rows": [{
                    "Edits": [
                        {"Name": "item_id", "Value": "WIDGET-001"},
                        {"Name": "uom", "Value": "EA"},
                        {"Name": "pricing_method", "Value": "Price"},
                        {"Name": "price", "Value": "25.00"},
                    ],
                    "RelativeDateEdits": [],
                }],
            },
            # 3. Break line -- JOBPRICELINE (1 row)
            {
                "Name": "JOBPRICELINE.jobpriceline",
                "Type": "List",
                "Keys": ["item_id"],
                "Rows": [{
                    "Edits": [
                        {"Name": "item_id", "Value": "WIDGET-002"},
                        {"Name": "uom", "Value": "EA"},
                        {"Name": "pricing_method", "Value": "Source"},
                        {"Name": "source_price", "Value": "Supplier List Price"},
                        {"Name": "multiplier", "Value": "1"},
                    ],
                    "RelativeDateEdits": [],
                }],
            },
            # 4. Break tiers for WIDGET-002 (must follow its JOBPRICELINE)
            {
                "Name": "VALUES.values",
                "Type": "Form",
                "Keys": [],
                "Rows": [{
                    "Edits": [
                        {"Name": "calculation_method_cd", "Value": "Fixed Price"},
                        # Tier 1: qty 1-9 @ $10.00
                        {"Name": "calculation_value", "Value": "10.00"},
                        {"Name": "break1", "Value": "10"},
                        # Tier 2: qty 10-49 @ $8.50
                        {"Name": "calculation_value2", "Value": "8.50"},
                        {"Name": "break2", "Value": "50"},
                        # Tier 3: qty 50+ @ $7.00
                        {"Name": "calculation_value3", "Value": "7.00"},
                        {"Name": "break3", "Value": "0"},
                    ],
                    "RelativeDateEdits": [],
                }],
            },
        ],
    }],
}

response = httpx.post(
    f"{ui_server_url}/api/v2/transaction",
    headers=headers,
    json=payload,
    verify=False,
)
response.raise_for_status()
result = response.json()
succeeded = result['Summary']['Succeeded']
failed = result['Summary']['Failed']
print(f"Succeeded: {succeeded}, Failed: {failed}")

if result["Summary"]["Succeeded"] > 0:
    txn = result["Results"]["Transactions"][0]
    contract_no = txn["DataElements"][0]["Rows"][0]["Edits"]
    for edit in contract_no:
        if edit["Name"] == "contract_no":
            print(f"Contract #: {edit['Value']}")
            break
```

```csharp
using System.Net.Http;
using System.Text;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

// Authenticate and get UI server URL
using var httpClient = new HttpClient();
httpClient.DefaultRequestHeaders.Add("Accept", "application/json");

var authBody = new JObject { ["username"] = "api_user", ["password"] = "api_pass" };
var authContent = new StringContent(authBody.ToString(), Encoding.UTF8, "application/json");
var authResp = await httpClient.PostAsync(
    "https://play.p21server.com/api/security/token/v2", authContent);
authResp.EnsureSuccessStatusCode();
var authJson = JObject.Parse(await authResp.Content.ReadAsStringAsync());
var token = authJson["AccessToken"]!.ToString();

httpClient.DefaultRequestHeaders.Authorization =
    new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", token);

var routerResp = await httpClient.GetAsync(
    "https://play.p21server.com/api/ui/router/v1?urlType=external");
routerResp.EnsureSuccessStatusCode();
var routerJson = JObject.Parse(await routerResp.Content.ReadAsStringAsync());
var uiServerUrl = routerJson["Url"]!.ToString().TrimEnd('/');

// Create a contract with one fixed-price line and one break line
var payload = new JObject
{
    ["Name"] = "JobContractPricing",
    ["UseCodeValues"] = false,
    ["Transactions"] = new JArray
    {
        new JObject
        {
            ["Status"] = "New",
            ["DataElements"] = new JArray
            {
                // 1. Contract header
                new JObject
                {
                    ["Name"] = "FORM.d_dw_job_price_hdr",
                    ["Type"] = "Form",
                    ["Keys"] = new JArray(),
                    ["Rows"] = new JArray
                    {
                        new JObject
                        {
                            ["Edits"] = new JArray
                            {
                                new JObject { ["Name"] = "company_id", ["Value"] = "ACME" },
                                new JObject { ["Name"] = "customer_id", ["Value"] = "100198" },
                                new JObject { ["Name"] = "corp_address_id", ["Value"] = "1" },
                                new JObject { ["Name"] = "end_date", ["Value"] = "2027-12-31" },
                                new JObject { ["Name"] = "approved", ["Value"] = "ON" },
                            },
                            ["RelativeDateEdits"] = new JArray()
                        }
                    }
                },
                // 2. Fixed-price line (no breaks)
                new JObject
                {
                    ["Name"] = "JOBPRICELINE.jobpriceline",
                    ["Type"] = "List",
                    ["Keys"] = new JArray { "item_id" },
                    ["Rows"] = new JArray
                    {
                        new JObject
                        {
                            ["Edits"] = new JArray
                            {
                                new JObject { ["Name"] = "item_id", ["Value"] = "WIDGET-001" },
                                new JObject { ["Name"] = "uom", ["Value"] = "EA" },
                                new JObject { ["Name"] = "pricing_method", ["Value"] = "Price" },
                                new JObject { ["Name"] = "price", ["Value"] = "25.00" },
                            },
                            ["RelativeDateEdits"] = new JArray()
                        }
                    }
                },
                // 3. Break line -- JOBPRICELINE (1 row)
                new JObject
                {
                    ["Name"] = "JOBPRICELINE.jobpriceline",
                    ["Type"] = "List",
                    ["Keys"] = new JArray { "item_id" },
                    ["Rows"] = new JArray
                    {
                        new JObject
                        {
                            ["Edits"] = new JArray
                            {
                                new JObject { ["Name"] = "item_id", ["Value"] = "WIDGET-002" },
                                new JObject { ["Name"] = "uom", ["Value"] = "EA" },
                                new JObject { ["Name"] = "pricing_method", ["Value"] = "Source" },
                                new JObject { ["Name"] = "source_price", ["Value"] = "Supplier List Price" },
                                new JObject { ["Name"] = "multiplier", ["Value"] = "1" },
                            },
                            ["RelativeDateEdits"] = new JArray()
                        }
                    }
                },
                // 4. Break tiers for WIDGET-002 (must follow its JOBPRICELINE)
                new JObject
                {
                    ["Name"] = "VALUES.values",
                    ["Type"] = "Form",
                    ["Keys"] = new JArray(),
                    ["Rows"] = new JArray
                    {
                        new JObject
                        {
                            ["Edits"] = new JArray
                            {
                                new JObject { ["Name"] = "calculation_method_cd", ["Value"] = "Fixed Price" },
                                // Tier 1: qty 1-9 @ $10.00
                                new JObject { ["Name"] = "calculation_value", ["Value"] = "10.00" },
                                new JObject { ["Name"] = "break1", ["Value"] = "10" },
                                // Tier 2: qty 10-49 @ $8.50
                                new JObject { ["Name"] = "calculation_value2", ["Value"] = "8.50" },
                                new JObject { ["Name"] = "break2", ["Value"] = "50" },
                                // Tier 3: qty 50+ @ $7.00
                                new JObject { ["Name"] = "calculation_value3", ["Value"] = "7.00" },
                                new JObject { ["Name"] = "break3", ["Value"] = "0" },
                            },
                            ["RelativeDateEdits"] = new JArray()
                        }
                    }
                }
            }
        }
    }
};

var content = new StringContent(
    payload.ToString(), Encoding.UTF8, "application/json");
var response = await httpClient.PostAsync(
    $"{uiServerUrl}/api/v2/transaction", content);
response.EnsureSuccessStatusCode();

var result = JObject.Parse(await response.Content.ReadAsStringAsync());
Console.WriteLine(
    $"Succeeded: {result["Summary"]!["Succeeded"]}, " +
    $"Failed: {result["Summary"]!["Failed"]}");

if ((int)result["Summary"]!["Succeeded"]! > 0)
{
    var edits = result["Results"]!["Transactions"]![0]!["DataElements"]![0]!["Rows"]![0]!["Edits"]!;
    foreach (var edit in edits)
    {
        if (edit["Name"]!.ToString() == "contract_no")
        {
            Console.WriteLine($"Contract #: {edit["Value"]}");
            break;
        }
    }
}
```
<!-- /tabs -->

---

### Assembly Service

The `Assembly` service creates assembly/BOM (bill of materials) definitions for existing inventory items. It defines which components make up an assembled product, along with routing steps and cost estimates. It has 15 DataElements; the key ones are documented below.

See also: [Production & Labor API](12-Production-Labor-API.md) for production order workflows that consume assembly definitions.

#### Service Definition

```http
GET /api/v2/definition/Assembly
```

#### Header -- `TABPAGE_1.assemblyhdr` (Form, 36 fields)

Key: `inv_mast_item_id`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `inv_mast_item_id` | Char | Yes | Item ID (must exist in inventory) |
| `pricing_option` | Char | No | Pricing option for the assembly |
| `default_disposition` | Char | No | Default disposition code |
| `production_order_processing` | Char | No | Production order processing flag |
| `copy_item_id` | Char | No | Copy BOM from existing assembly (`cc_` prefix = computed/client column) |
| `revision_level` | Char | No | Assembly revision level |
| `allow_disassembly` | Char | No | Allow disassembly flag |
| `hose_assembly_flag` | Char | No | Hose assembly indicator |

> **Important:** `inv_mast_item_id` must reference an existing inventory item. Non-existent items return "This item ID is not valid". Items that already have assembly definitions are blocked from re-creation.

#### Components/BOM -- `TABPAGE_17.tp_17_dw_17` (List, 20 fields)

Key: `item_id_service_labor_id`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `item_id_service_labor_id` | Char | Yes | Component item ID or labor ID |
| `quantity` (`qty_needed`) | Decimal | No | Quantity needed per assembly |
| `component_type` | Char | No | Component type (see valid values below) |
| `operation_cd` | Char | No | Operation code |
| `unit_of_measure` | Char | No | UOM (auto-populated from item master if omitted) |
| `backflush_flag` | Char | No | Backflush flag |

**`component_type` valid values:** `Hose fitting/adaptor`, `Hose sleeve`, `Hose/cable`, `None`

These values are hose-assembly-specific. For non-hose assemblies, omit `component_type` entirely -- it defaults to empty (`IgnoreIfEmpty: true`).

**`unit_of_measure`:** Not required (`IgnoreIfEmpty: true`). When omitted, P21 auto-populates from the item master -- standard P21 behavior.

#### Routing -- `ROUTING_TABPAGE.process` (Form) + `ROUTING_TABPAGE.stage_x_process` (List, 22 fields)

| Field | Type | Description |
|-------|------|-------------|
| `process_code` | Char | Process/routing code |
| `sequence_no` | Long | Operation sequence number |
| `cost` | Decimal | Cost for this routing step |
| `cost_type` | Char | Cost type classification |
| `estimated_hours` | Decimal | Estimated hours for this step |

#### Part + Assembly Creation Workflow

Assembly definitions are metadata attached to existing inventory items. Creating a new assembly-item from scratch requires two steps:

1. **Create the item** via Inventory REST API (`POST /api/inventory/parts`)
2. **Create the assembly definition** via Transaction API (`Assembly` service)

The Assembly service does NOT create new inventory items -- it adds BOM metadata to an item that already exists.

#### Known Limitations

- **Status "Existing" returns HTTP 500:** Same `NullReferenceException` at `ToInternalBeSpecification` as other services. Use the Interactive API (Assembly window) for modifications to existing assemblies.
- **Item must exist first:** `inv_mast_item_id` must reference an existing item.
- **No re-creation:** Items that already have assembly definitions cannot have a second assembly created.

#### Example: Create an Assembly Definition

<!-- tabs -->
```python
import httpx

# Authenticate and get UI server URL
base_url = "https://play.p21server.com"
auth_resp = httpx.post(
    f"{base_url}/api/security/token/v2",
    json={"username": "api_user", "password": "api_pass"},
    verify=False,
)
auth_resp.raise_for_status()
token = auth_resp.json()["AccessToken"]

router_resp = httpx.get(
    f"{base_url}/api/ui/router/v1?urlType=external",
    headers={"Authorization": f"Bearer {token}"},
    verify=False,
)
router_resp.raise_for_status()
ui_server_url = router_resp.json()["Url"].rstrip("/")

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}

# Create assembly definition for an existing item
# The item WIDGET-001 must already exist in inventory
payload = {
    "Name": "Assembly",
    "UseCodeValues": False,
    "Transactions": [{
        "Status": "New",
        "DataElements": [
            # Assembly header
            {
                "Name": "TABPAGE_1.assemblyhdr",
                "Type": "Form",
                "Keys": ["inv_mast_item_id"],
                "Rows": [{
                    "Edits": [
                        {"Name": "inv_mast_item_id", "Value": "WIDGET-001"},
                        {"Name": "allow_disassembly", "Value": "ON"},
                    ],
                    "RelativeDateEdits": [],
                }],
            },
            # BOM components
            {
                "Name": "TABPAGE_17.tp_17_dw_17",
                "Type": "List",
                "Keys": ["item_id_service_labor_id"],
                "Rows": [
                    {
                        "Edits": [
                            {
                                "Name": "item_id_service_labor_id",
                                "Value": "COMPONENT-A",
                            },
                            {"Name": "quantity", "Value": "2"},
                            {"Name": "operation_cd", "Value": "ASSY"},
                        ],
                        "RelativeDateEdits": [],
                    },
                    {
                        "Edits": [
                            {
                                "Name": "item_id_service_labor_id",
                                "Value": "COMPONENT-B",
                            },
                            {"Name": "quantity", "Value": "1"},
                            {"Name": "operation_cd", "Value": "ASSY"},
                        ],
                        "RelativeDateEdits": [],
                    },
                ],
            },
        ],
    }],
}

response = httpx.post(
    f"{ui_server_url}/api/v2/transaction",
    headers=headers,
    json=payload,
    verify=False,
)
response.raise_for_status()
result = response.json()
succeeded = result['Summary']['Succeeded']
failed = result['Summary']['Failed']
print(f"Succeeded: {succeeded}, Failed: {failed}")

if result["Summary"]["Failed"] > 0:
    for msg in result.get("Messages", []):
        print(f"  Message: {msg}")
```

```csharp
using System.Net.Http;
using System.Text;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

// Authenticate and get UI server URL
using var httpClient = new HttpClient();
httpClient.DefaultRequestHeaders.Add("Accept", "application/json");

var authBody = new JObject { ["username"] = "api_user", ["password"] = "api_pass" };
var authContent = new StringContent(authBody.ToString(), Encoding.UTF8, "application/json");
var authResp = await httpClient.PostAsync(
    "https://play.p21server.com/api/security/token/v2", authContent);
authResp.EnsureSuccessStatusCode();
var authJson = JObject.Parse(await authResp.Content.ReadAsStringAsync());
var token = authJson["AccessToken"]!.ToString();

httpClient.DefaultRequestHeaders.Authorization =
    new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", token);

var routerResp = await httpClient.GetAsync(
    "https://play.p21server.com/api/ui/router/v1?urlType=external");
routerResp.EnsureSuccessStatusCode();
var routerJson = JObject.Parse(await routerResp.Content.ReadAsStringAsync());
var uiServerUrl = routerJson["Url"]!.ToString().TrimEnd('/');

// Create assembly definition for an existing item
// The item WIDGET-001 must already exist in inventory
var payload = new JObject
{
    ["Name"] = "Assembly",
    ["UseCodeValues"] = false,
    ["Transactions"] = new JArray
    {
        new JObject
        {
            ["Status"] = "New",
            ["DataElements"] = new JArray
            {
                // Assembly header
                new JObject
                {
                    ["Name"] = "TABPAGE_1.assemblyhdr",
                    ["Type"] = "Form",
                    ["Keys"] = new JArray { "inv_mast_item_id" },
                    ["Rows"] = new JArray
                    {
                        new JObject
                        {
                            ["Edits"] = new JArray
                            {
                                new JObject { ["Name"] = "inv_mast_item_id", ["Value"] = "WIDGET-001" },
                                new JObject { ["Name"] = "allow_disassembly", ["Value"] = "ON" },
                            },
                            ["RelativeDateEdits"] = new JArray()
                        }
                    }
                },
                // BOM components
                new JObject
                {
                    ["Name"] = "TABPAGE_17.tp_17_dw_17",
                    ["Type"] = "List",
                    ["Keys"] = new JArray { "item_id_service_labor_id" },
                    ["Rows"] = new JArray
                    {
                        new JObject
                        {
                            ["Edits"] = new JArray
                            {
                                new JObject { ["Name"] = "item_id_service_labor_id", ["Value"] = "COMPONENT-A" },
                                new JObject { ["Name"] = "quantity", ["Value"] = "2" },
                                new JObject { ["Name"] = "operation_cd", ["Value"] = "ASSY" },
                            },
                            ["RelativeDateEdits"] = new JArray()
                        },
                        new JObject
                        {
                            ["Edits"] = new JArray
                            {
                                new JObject { ["Name"] = "item_id_service_labor_id", ["Value"] = "COMPONENT-B" },
                                new JObject { ["Name"] = "quantity", ["Value"] = "1" },
                                new JObject { ["Name"] = "operation_cd", ["Value"] = "ASSY" },
                            },
                            ["RelativeDateEdits"] = new JArray()
                        }
                    }
                }
            }
        }
    }
};

var content = new StringContent(
    payload.ToString(), Encoding.UTF8, "application/json");
var response = await httpClient.PostAsync(
    $"{uiServerUrl}/api/v2/transaction", content);
response.EnsureSuccessStatusCode();

var result = JObject.Parse(await response.Content.ReadAsStringAsync());
Console.WriteLine(
    $"Succeeded: {result["Summary"]!["Succeeded"]}, " +
    $"Failed: {result["Summary"]!["Failed"]}");

if ((int)result["Summary"]!["Failed"]! > 0)
{
    var messages = result["Messages"] as JArray;
    if (messages != null)
    {
        foreach (var msg in messages)
            Console.WriteLine($"  Message: {msg}");
    }
}
```
<!-- /tabs -->

---

## PDF Report Generation

The Transaction API includes a dedicated endpoint for generating PDF documents -- purchase orders, pick tickets, and other printable reports. The endpoint returns the rendered PDF as a base64-encoded string in the response body.

**Endpoint:** `POST {ui_server}/api/v2/process/pdfreport`

### Verified Report Services

| Service Name | Report Type |
|-------------|-------------|
| `m_reprintpurchaseorders` | Purchase Order reprints |
| `m_reprintpicktickets` | Pick Ticket reprints |

> **Discovery:** The `m_*` report services are **hidden from `GET /api/v2/services`** — that endpoint lists only the transaction business objects (299 on a 25.2 test system), and `?type=report` returns an empty list (verified live; `?type=window` returns the same transaction list, other `?type=` values return HTTP 400 `"Service Type is invalid."`). The report services are still fully callable: `GET /api/v2/definition/{service_name}` and `GET /api/v2/defaults/{service_name}` both work for them. To discover callable report names, probe the definition endpoint directly, or pull candidate names from the `window_x_menu` table — the callable service name is the last `/`-segment of `menu_name`:
>
> ```sql
> SELECT DISTINCT RIGHT(menu_name, CHARINDEX('/', REVERSE(menu_name) + '/') - 1) AS callable_name
> FROM window_x_menu
> WHERE menu_name LIKE 'm[_]%';
> ```
>
> Probe each candidate with `GET /api/v2/definition/{name}` — the ones that return 200 are callable. On a 25.2 test system this yields ~157 callable report services, including `m_picktickets`, `m_reprintpicktickets`, `m_productionorders`, `m_orderacknowledgements`, `m_invoices`, `m_packinglists`, and `m_customerstatements`.
>
> **Credit:** [Alex Westemeier](https://github.com/AWestemeier) identified that report services are hidden from the services list and worked out the `window_x_menu` discovery path.

### Request Structure

The payload follows the standard TransactionSet format. Report-specific criteria go in the DataElement's `Edits` array:

```json
{
    "Name": "m_reprintpurchaseorders",
    "Transactions": [{
        "DataElements": [{
            "Keys": [],
            "Name": "TABPAGE_1.poreportcriteriadw",
            "Rows": [{
                "Edits": [
                    {"Name": "company_id", "Value": "ACME"},
                    {"Name": "beg_po_no", "Value": "500100"},
                    {"Name": "end_po_no", "Value": "500100"},
                    {"Name": "reprint_flag", "Value": "Y"}
                ]
            }],
            "Type": 0
        }],
        "Status": 0
    }],
    "UseCodeValues": false
}
```

### Response

The response is a **JSON array** (even for a single document). Each element contains document metadata and the base64-encoded PDF content. Decode the `DocumentData` field and write the bytes to a `.pdf` file.

**Verified success response** (generalized from live PO reprint):

```json
[
  {
    "ClientId": "9a58084c-b2e5-451f-a8d3-6564594017f2",
    "RequestId": null,
    "DocumentType": 1,
    "DocumentId": "PO500100 PURCHASE_ORDER",
    "DocumentFormat": 5,
    "DocumentName": "PO500100 PURCHASE_ORDER",
    "FileName": "PO500100 PURCHASE_ORDER.pdf",
    "DocumentContentType": "application/pdf",
    "DocumentData": "JVBERi0xLjQK... (base64-encoded PDF bytes, ~150KB for a typical PO)",
    "ResponseStatus": {
      "StatusCode": "Success",
      "Message": "Form request '' for Form ID PO500100 PURCHASE_ORDER has completed.",
      "StackTrace": null
    },
    "Batch": null,
    "DocumentAssociations": []
  }
]
```

**Key notes:**

- Response is a **JSON array**, not a single object -- even when generating one document
- `DocumentData` contains the base64-encoded PDF bytes (~150KB for a typical PO)
- `FileName` includes the `.pdf` extension (e.g., `"PO500100 PURCHASE_ORDER.pdf"`)
- `ResponseStatus.StatusCode` is `"Success"` on success
- `DocumentFormat` value `5` corresponds to PDF format
- `DocumentContentType` is `"application/pdf"`

**Error response** (e.g., PO not found):

```json
{
    "DateTimeStamp": "/Date(1776344580327)/",
    "ErrorMessage": "Unexpected results generating document request from criteria. --> Messages returned during document request processing: <No records to print for this range.",
    "ErrorType": "P21.UI.BulkEditor.BulkEditException",
    "HostName": "p21web-22",
    "InnerException": null
}
```

> **Note:** Error responses use the standard P21 error envelope (with `ErrorType` and `ErrorMessage`), not the `Summary`/`Messages` format used by the `/transaction` endpoint.

### Example: Generate and Save a PO Reprint

<!-- tabs -->
```python
import base64
import httpx

# Authenticate and get UI server URL
base_url = "https://play.p21server.com"
auth_resp = httpx.post(
    f"{base_url}/api/security/token/v2",
    json={"username": "api_user", "password": "api_pass"},
    verify=False,
)
auth_resp.raise_for_status()
token = auth_resp.json()["AccessToken"]

router_resp = httpx.get(
    f"{base_url}/api/ui/router/v1?urlType=external",
    headers={"Authorization": f"Bearer {token}"},
    verify=False,
)
router_resp.raise_for_status()
ui_server_url = router_resp.json()["Url"].rstrip("/")

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}

# Generate PO reprint PDF
payload = {
    "Name": "m_reprintpurchaseorders",
    "Transactions": [{
        "DataElements": [{
            "Keys": [],
            "Name": "TABPAGE_1.poreportcriteriadw",
            "Rows": [{
                "Edits": [
                    {"Name": "company_id", "Value": "ACME"},
                    {"Name": "beg_po_no", "Value": "500100"},
                    {"Name": "end_po_no", "Value": "500100"},
                    {"Name": "reprint_flag", "Value": "Y"},
                ]
            }],
            "Type": 0,
        }],
        "Status": 0,
    }],
    "UseCodeValues": False,
}

response = httpx.post(
    f"{ui_server_url}/api/v2/process/pdfreport",
    headers=headers,
    json=payload,
    verify=False,
)
response.raise_for_status()
result = response.json()

# Response is a JSON array -- even for a single document
if isinstance(result, list) and len(result) > 0:
    doc = result[0]
    status = doc.get("ResponseStatus", {}).get("StatusCode")
    if status == "Success" and doc.get("DocumentData"):
        pdf_bytes = base64.b64decode(doc["DocumentData"])
        filename = doc.get("FileName", "PO_500100.pdf")
        with open(filename, "wb") as f:
            f.write(pdf_bytes)
        print(f"Saved {filename} ({len(pdf_bytes)} bytes)")
    else:
        msg = doc.get("ResponseStatus", {}).get("Message", "Unknown error")
        print(f"Report failed: {msg}")
else:
    print("No documents returned")
    print(f"Response: {result}")
```

```csharp
using System;
using System.IO;
using System.Net.Http;
using System.Text;
using Newtonsoft.Json.Linq;

// Authenticate and get UI server URL
using var httpClient = new HttpClient();
httpClient.DefaultRequestHeaders.Add("Accept", "application/json");

var authBody = new JObject { ["username"] = "api_user", ["password"] = "api_pass" };
var authContent = new StringContent(authBody.ToString(), Encoding.UTF8, "application/json");
var authResp = await httpClient.PostAsync(
    "https://play.p21server.com/api/security/token/v2", authContent);
authResp.EnsureSuccessStatusCode();
var authJson = JObject.Parse(await authResp.Content.ReadAsStringAsync());
var token = authJson["AccessToken"]!.ToString();

httpClient.DefaultRequestHeaders.Authorization =
    new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", token);

var routerResp = await httpClient.GetAsync(
    "https://play.p21server.com/api/ui/router/v1?urlType=external");
routerResp.EnsureSuccessStatusCode();
var routerJson = JObject.Parse(await routerResp.Content.ReadAsStringAsync());
var uiServerUrl = routerJson["Url"]!.ToString().TrimEnd('/');

// Generate PO reprint PDF
var payload = new JObject
{
    ["Name"] = "m_reprintpurchaseorders",
    ["Transactions"] = new JArray
    {
        new JObject
        {
            ["DataElements"] = new JArray
            {
                new JObject
                {
                    ["Keys"] = new JArray(),
                    ["Name"] = "TABPAGE_1.poreportcriteriadw",
                    ["Rows"] = new JArray
                    {
                        new JObject
                        {
                            ["Edits"] = new JArray
                            {
                                new JObject { ["Name"] = "company_id", ["Value"] = "ACME" },
                                new JObject { ["Name"] = "beg_po_no", ["Value"] = "500100" },
                                new JObject { ["Name"] = "end_po_no", ["Value"] = "500100" },
                                new JObject { ["Name"] = "reprint_flag", ["Value"] = "Y" },
                            }
                        }
                    },
                    ["Type"] = 0
                }
            },
            ["Status"] = 0
        }
    },
    ["UseCodeValues"] = false
};

var content = new StringContent(
    payload.ToString(), Encoding.UTF8, "application/json");
var response = await httpClient.PostAsync(
    $"{uiServerUrl}/api/v2/process/pdfreport", content);
response.EnsureSuccessStatusCode();

var resultArray = JArray.Parse(await response.Content.ReadAsStringAsync());

// Response is a JSON array -- even for a single document
if (resultArray.Count > 0)
{
    var doc = resultArray[0] as JObject;
    var status = doc?["ResponseStatus"]?["StatusCode"]?.ToString();
    var documentData = doc?["DocumentData"]?.ToString();

    if (status == "Success" && !string.IsNullOrEmpty(documentData))
    {
        var pdfBytes = Convert.FromBase64String(documentData);
        var filename = doc?["FileName"]?.ToString() ?? "PO_500100.pdf";
        await File.WriteAllBytesAsync(filename, pdfBytes);
        Console.WriteLine($"Saved {filename} ({pdfBytes.Length} bytes)");
    }
    else
    {
        var msg = doc?["ResponseStatus"]?["Message"]?.ToString() ?? "Unknown error";
        Console.WriteLine($"Report failed: {msg}");
    }
}
else
{
    Console.WriteLine("No documents returned");
}
```
<!-- /tabs -->

> **Credit:** Jeff Poss discovered the `/api/v2/process/pdfreport` endpoint and payload structure.

---

## Stored Procedure Executor

The `m_storedprocedureexecutor` service provides Transaction API access to P21's Stored Procedure Executor, allowing you to discover and load stored procedure definitions configured in the P21 UI.

### Discovery

```http
GET {ui_server}/api/v2/definition/m_storedprocedureexecutor
GET {ui_server}/api/v2/defaults/m_storedprocedureexecutor
```

### Loading a Stored Procedure Definition

Use `POST /api/v2/transaction/get` with the `stored_procedure_def_uid` key to retrieve a specific stored procedure definition and its parameters:

<!-- tabs -->
```python
import httpx

# Authenticate and get UI server URL (see Authentication examples above)
base_url = "https://play.p21server.com"
auth_resp = httpx.post(
    f"{base_url}/api/security/token/v2",
    json={"username": "api_user", "password": "api_pass"},
    verify=False,
)
auth_resp.raise_for_status()
token = auth_resp.json()["AccessToken"]

router_resp = httpx.get(
    f"{base_url}/api/ui/router/v1?urlType=external",
    headers={"Authorization": f"Bearer {token}"},
    verify=False,
)
router_resp.raise_for_status()
ui_server_url = router_resp.json()["Url"].rstrip("/")

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}

# Load a stored procedure definition by UID
sp_uid = "12345"  # Found in P21 Stored Procedure Executor UI
payload = {
    "ServiceName": "m_storedprocedureexecutor",
    "TransactionStates": [{
        "DataElementName": "DEFINITION.stored_procedure_def",
        "Keys": [{
            "Name": "stored_procedure_def_uid",
            "Value": sp_uid,
        }],
    }],
}

response = httpx.post(
    f"{ui_server_url}/api/v2/transaction/get",
    headers=headers,
    json=payload,
    verify=False,
)
response.raise_for_status()
result = response.json()

# The response includes the SP definition and its argument_list parameters
for txn in result.get("Transactions", []):
    for de in txn.get("DataElements", []):
        print(f"DataElement: {de['Name']}")
        for row in de.get("Rows", []):
            for edit in row.get("Edits", []):
                print(f"  {edit['Name']}: {edit['Value']}")
```

```csharp
using System;
using System.Net.Http;
using System.Text;
using Newtonsoft.Json.Linq;

// Authenticate and get UI server URL (see Authentication examples above)
using var httpClient = new HttpClient();
httpClient.DefaultRequestHeaders.Add("Accept", "application/json");

var authBody = new JObject { ["username"] = "api_user", ["password"] = "api_pass" };
var authContent = new StringContent(authBody.ToString(), Encoding.UTF8, "application/json");
var authResp = await httpClient.PostAsync(
    "https://play.p21server.com/api/security/token/v2", authContent);
authResp.EnsureSuccessStatusCode();
var authJson = JObject.Parse(await authResp.Content.ReadAsStringAsync());
var token = authJson["AccessToken"]!.ToString();

httpClient.DefaultRequestHeaders.Authorization =
    new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", token);

var routerResp = await httpClient.GetAsync(
    "https://play.p21server.com/api/ui/router/v1?urlType=external");
routerResp.EnsureSuccessStatusCode();
var routerJson = JObject.Parse(await routerResp.Content.ReadAsStringAsync());
var uiServerUrl = routerJson["Url"]!.ToString().TrimEnd('/');

// Load a stored procedure definition by UID
var spUid = "12345"; // Found in P21 Stored Procedure Executor UI
var payload = new JObject
{
    ["ServiceName"] = "m_storedprocedureexecutor",
    ["TransactionStates"] = new JArray
    {
        new JObject
        {
            ["DataElementName"] = "DEFINITION.stored_procedure_def",
            ["Keys"] = new JArray
            {
                new JObject
                {
                    ["Name"] = "stored_procedure_def_uid",
                    ["Value"] = spUid
                }
            }
        }
    }
};

var content = new StringContent(
    payload.ToString(), Encoding.UTF8, "application/json");
var response = await httpClient.PostAsync(
    $"{uiServerUrl}/api/v2/transaction/get", content);
response.EnsureSuccessStatusCode();

var result = JObject.Parse(await response.Content.ReadAsStringAsync());

// The response includes the SP definition and its argument_list parameters
var transactions = result["Transactions"] as JArray;
if (transactions != null)
{
    foreach (var txn in transactions)
    {
        var dataElements = txn["DataElements"] as JArray;
        if (dataElements == null) continue;
        foreach (var de in dataElements)
        {
            Console.WriteLine($"DataElement: {de["Name"]}");
            var rows = de["Rows"] as JArray;
            if (rows == null) continue;
            foreach (var row in rows)
            {
                var edits = row["Edits"] as JArray;
                if (edits == null) continue;
                foreach (var edit in edits)
                    Console.WriteLine($"  {edit["Name"]}: {edit["Value"]}");
            }
        }
    }
}
```
<!-- /tabs -->

### Verified Service Definition

The definition endpoint returns the following structure for the `DEFINITION.stored_procedure_def` DataElement:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `stored_procedure_def_uid` | Long | Key | Unique identifier for the SP definition |
| `stored_procedure_description` | Char | No | Human-readable description of the stored procedure |
| `stored_procedure_default_timeout` | Long | No | Default execution timeout (seconds) |
| `row_status_flag` | Long | No | Record status (ValidValues: `Active`, `Delete`) |
| `stored_procedure` | Char | Yes | The stored procedure name to execute |

> **Note:** The key field is `stored_procedure_def_uid`, which is a Long (not a string). The `stored_procedure` field is the only required field besides the key.

### Endpoint Status

- `GET /api/v2/definition/m_storedprocedureexecutor` -- returns HTTP 200 with DataElements list describing the service structure, including the fields above.
- `GET /api/v2/defaults/m_storedprocedureexecutor` -- returns HTTP 200 with ~30KB response containing full default field values.

> **Tip:** The defaults endpoint returns the full field structure (~30KB). Use the definition and defaults endpoints to discover available fields before constructing payloads.

### Key Notes

- **Finding the UID:** The `stored_procedure_def_uid` is found in the P21 Stored Procedure Executor UI -- double-click the Executor Definition ID field to see it. UIDs are only created after first saving an SP definition in the P21 UI, and they differ across environments (dev vs production). *(Credit: Felipe Maurer)*
- **Parameters:** The SP's configurable parameters are returned in the `argument_list` section of the response.
- **Execution:** Loading an SP definition via the Transaction API retrieves its metadata and parameters, but actually executing the stored procedure may require the Interactive API (the Execute button must be clicked in the SP Executor window). *(Credit: Kevin Landry)*
- **Database tables:** The underlying tables are `stored_procedure_def` (UIDs), `spe_parameter_info` (parameter definitions), and `spe_procedure_info` (procedure names). These can be queried via OData for bulk discovery. *(Credit: Brad Vandenbogaerde)*

---

## DynaChange and Popup Handling

The Transaction API respects and enforces **all DynaChange configurations** -- menu changes, screen changes, required user-defined fields, and on-event business rules all fire during TAPI processing, just as they would in the P21 desktop client. *(Credit: Felipe Maurer)*

> **Source**: Community-verified patterns. Tested on P21 version 25.2. Applies to all Transaction API endpoints.
> **Discovery date**: April 2026 (documented); pattern in production use by multiple organizations.

### Popup Suppression Pattern

When a TAPI workflow triggers a popup dialog (e.g., a DynaChange rule showing a confirmation), the transaction may fail or behave unexpectedly. The recommended pattern is to deploy **Popup Suppression rules** on the API user's profile to handle these dialogs without needing the Interactive API.

Key characteristics:
- Suppression rules can be **conditional** -- configure them to fire only for the TAPI user's profile, leaving desktop users unaffected
- Suppression rules are configured in P21's DynaChange module (not via the API itself)
- This approach avoids the complexity of opening an Interactive API session just to dismiss a dialog

### Limitations

| Scenario | Workaround |
|----------|-----------|
| Visual Rules with response/callback attributes | (Community-reported) These break TAPI -- cause "Column is disabled" errors. Remove or disable these rules for the API user's profile. *(Credit: Brad Vandenbogaerde)* |
| Wizard-type popups requiring user input | (Verified) Must use the Interactive API (IAPI) -- TAPI cannot provide multi-step input |
| "Column is disabled" errors | (Community-reported) Often caused by DynaChange business rules, not by the API itself. Check the user's DynaChange profile for rules that disable fields or trigger response attributes. *(Credit: Justin Cassidy)* |

### Response Validation

> **Important:** The Transaction API returns **HTTP 200 even for failed transactions**. Always check the `Summary` and `Messages` sections of the response body -- never rely on the HTTP status code alone to determine success or failure. *(Credit: Neil Timmerman)*

<!-- tabs -->
```python
response = httpx.post(
    f"{ui_server_url}/api/v2/transaction",
    headers=headers,
    json=payload,
    verify=False,
)
# HTTP 200 does NOT mean the transaction succeeded
response.raise_for_status()
result = response.json()

# Always check the Summary
succeeded = result["Summary"]["Succeeded"]
failed = result["Summary"]["Failed"]

if failed > 0:
    print(f"Transaction failed ({failed} failures)")
    for msg in result.get("Messages", []):
        print(f"  Error: {msg}")
else:
    print(f"Transaction succeeded ({succeeded} records)")
```

```csharp
var response = await httpClient.PostAsync(
    $"{uiServerUrl}/api/v2/transaction", content);
// HTTP 200 does NOT mean the transaction succeeded
response.EnsureSuccessStatusCode();

var result = JObject.Parse(await response.Content.ReadAsStringAsync());

// Always check the Summary
var succeeded = (int)result["Summary"]!["Succeeded"]!;
var failed = (int)result["Summary"]!["Failed"]!;

if (failed > 0)
{
    Console.WriteLine($"Transaction failed ({failed} failures)");
    var messages = result["Messages"] as JArray;
    if (messages != null)
    {
        foreach (var msg in messages)
            Console.WriteLine($"  Error: {msg}");
    }
}
else
{
    Console.WriteLine($"Transaction succeeded ({succeeded} records)");
}
```
<!-- /tabs -->

---

## Code Examples

See the `scripts/transaction/` (Python) and `examples/csharp/Transaction/` (C#) directories for working examples:

| Script | Description |
|--------|-------------|
| `01_list_services.py` | List all available services |
| `02_get_definition.py` | Get service schema/template |
| `03_create_single.py` | Create a single record |
| `04_create_bulk.py` | Create multiple records |
| `05_update_existing.py` | Update existing records |
| `06_async_operations.py` | Use async endpoints |
| `test_session_pool.py` | Session pool diagnostic |

---

## Known Issues

### Session Pool Contamination

The Transaction API uses a session pool on the server. When a transaction fails mid-process (e.g., due to validation errors), the session may be left in a "dirty" state with dialogs still open. Subsequent requests using that pooled session may fail with errors like:

- "Unexpected response window"
- "Object reference not set"
- Validation errors for fields that weren't changed

**Workarounds:**

1. **Use the async endpoint** - Creates dedicated session per request
2. **Implement retry logic** - Retry failed requests after a delay
3. **Add jitter** - Random delays between rapid requests
4. **Restart middleware** - Clears the session pool (last resort)

See [Session Pool Troubleshooting](07-Session-Pool-Troubleshooting.md) for detailed analysis.

---

## Best Practices

1. **Get definition first** - Fetch the service definition to understand required fields
2. **Use display values** - Set `UseCodeValues: false` for clarity
3. **Check Summary** - Always check `Summary.Succeeded` and `Summary.Failed`
4. **Handle failures gracefully** - Messages array contains error details
5. **Consider async for bulk** - Use async endpoint for large batches
6. **Add delays between requests** - Prevents session pool issues
7. **Validate locally first** - Check required fields before sending

---

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| 400 Bad Request | Malformed request | Check JSON structure |
| 401 Unauthorized | Invalid/expired token | Refresh token |
| 202 Accepted | Async request queued (not an error) | Poll with GET `/async?id=` for status |
| "Required field missing" | Missing required field | Check definition for required fields |
| "Unexpected response window" | Session pool dirty | Retry or use async endpoint |
| "Invalid value" | Wrong dropdown value | Use `UseCodeValues: false` with display values |
| Service fails on `/transaction` | Service requires commands endpoint | Use `/api/v2/commands` instead (see [Commands Endpoint](#commands-endpoint)) |

---

## Related

- [Authentication](00-Authentication.md)
- [API Selection Guide](01-API-Selection-Guide.md)
- [Production & Labor API](12-Production-Labor-API.md) - TimeEntry, ProductionOrder, and labor services
- [Session Pool Troubleshooting](07-Session-Pool-Troubleshooting.md)
- [scripts/transaction/](https://github.com/mrwuss/p21-api-documentation/tree/master/scripts/transaction/) - Working examples
- [scripts/production/](https://github.com/mrwuss/p21-api-documentation/tree/master/scripts/production/) - Production & labor examples
