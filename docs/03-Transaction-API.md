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

Note that the no-trailing-slash form can return a 307 redirect and the response may be XML on some middleware — use the trailing-slash form (`/api/ui/router/v1/`) and follow redirects; see [00-Authentication § UI Server URL](00-Authentication.md#ui-server-url).

Then use the returned URL as base:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v2/services` | GET | List available services (transaction business objects only — all `m_*` services, reports and `m_storedprocedureexecutor` alike, are hidden from the list but still callable via `definition`/`defaults`; see [PDF Report Generation](#pdf-report-generation)) |
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

> **Definition endpoint 500s for unavailable windows:** `GET /api/v2/definition/{name}` can return HTTP 500 with *"Window &lt;&lt;X&gt;&gt; is not available or user does not have permission to open it"* for a service that `/api/v2/services` lists. Despite the wording, this is usually **not a grantable permission problem** — the same window fails for fully-privileged users in the Service Explorer. It means the window isn't available in that environment (unlicensed or undeployed module), and which services fail differs per environment. On one 25.2 test system, 238 of the 299 listed services had fetchable definitions. *(Credit: [Alex Westemeier](https://github.com/AWestemeier))*

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
| `IgnoreDisabled` | No | If `true`, allow the transaction to proceed past disabled fields (see [IgnoreDisabled](#ignoredisabled) below) |
| `Query` | No | Optional query filter for the service |
| `FieldMap` | No | Optional field name mappings |
| `TransactionSplitMethod` | No | `"Standard"` (default) or `"NoSplit"` |
| `Parameters` | No | Additional service-specific parameters |

### Transaction Fields

| Field | Description |
|-------|-------------|
| `Status` | `"New"` for create **and** update (there is no working `"Existing"` status — it returns HTTP 500); responses echo `"Passed"`/`"Failed"` |
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

## Payload Anatomy -- Types, Nesting, and Common Mistakes

Most first-integration failures are payload **shape** mistakes, not wrong endpoints: a string where an array is expected, a field at the wrong nesting level, or a boolean in quotes. JSON indentation is cosmetic -- what matters is the **nesting** and the **type at every level**. This skeleton annotates both:

```jsonc
{                                       // ROOT: object
  "Name": "JobContractPricing",         // string  — the service name
  "UseCodeValues": false,               // boolean — NOT the string "false"
  "IgnoreDisabled": true,               // boolean — ONLY valid at THIS level
  "Transactions": [                     // ARRAY of Transaction objects
    {
      "Status": "New",                  // string — "New" for create AND update
      "DataElements": [                 // ARRAY of DataElement objects
        {
          "Name": "FORM.d_dw_job_price_hdr",  // string — "ELEMENT.datawindow"
          "Type": "Form",               // string — "Form" or "List"
          "Keys": ["item_id"],          // ARRAY of strings — even for ONE key
          "Rows": [                     // ARRAY of Row objects — even for ONE row
            {
              "Edits": [                // ARRAY of Edit objects
                { "Name": "item_id", "Value": "WIDGET-001" }   // Value: STRING
              ],
              "RelativeDateEdits": []   // array (may be empty)
            }
          ]
        }
      ]
    }
  ]
}
```

### Common mistakes and their symptoms

| Mistake | Wrong | Right | Symptom |
|---------|-------|-------|---------|
| `Keys` as a string | `"Keys": "item_id"` | `"Keys": ["item_id"]` | Deserialization/validation error, or keys ignored |
| `IgnoreDisabled` inside a Transaction | `Transactions[0].IgnoreDisabled` | Top level, beside `Name` | **Silently ignored** — `Column is disabled: ...` persists ([details](#ignoredisabled)) |
| Boolean in quotes | `"UseCodeValues": "false"` | `"UseCodeValues": false` | The string `"false"` is truthy-ish to some binders — behavior undefined |
| `Rows`/`Edits` as an object | `"Rows": { "Edits": ... }` | `"Rows": [ { "Edits": [...] } ]` | Deserialization error or empty save |
| `Value` as a number | `"Value": 36.58` | `"Value": "36.58"` | Every verified example sends **strings**; other types are untested territory |
| `Status: "Existing"` | — | `"Status": "New"` | HTTP 500 `NullReferenceException` — [use "New" for updates too](#updating-an-existing-contract) |
| Report payload to `/transaction` | — | `POST /api/v2/process/pdfreport` | Returns `Succeeded`, emits **nothing** ([details](#pdf-report-generation)) |
| Wrong property case | `"transactions": [...]` | `"Transactions": [...]` | Property silently unbound — behaves like it was never sent |
| Fields in UI-cascade-breaking order | `price` before `pricing_method` | Match the UI order | Value silently cleared while reporting Succeeded ([details](#field-order-matters)) |

Two tools take the guesswork out:

- **Start from the service's `Template`** — `GET /api/v2/definition/{Service}` (or the committed [`definitions/{Service}.json`](../definitions/README.md)) contains a `Template.TransactionSet` skeleton with every element and field already correctly shaped. Copy it, fill the `Edits` you need, delete the rest.
- **Validate before you POST** — [`scripts/validate_payload.py`](../scripts/validate_payload.py) checks a payload file (JSON **or** XML) offline against these rules and the `definitions/` schema, with exact paths to each problem:

  ```bash
  python scripts/validate_payload.py my_payload.json
  python scripts/validate_payload.py my_payload.xml
  ```

---

## XML Payloads (Content Negotiation)

The Transaction API endpoints speak **XML as well as JSON**, in both directions, negotiated per-request with standard headers (verified live on 25.2, July 2026):

| You want | Headers |
|----------|---------|
| JSON in, JSON out | `Content-Type: application/json`, `Accept: application/json` |
| XML in, XML out | `Content-Type: application/xml`, `Accept: application/xml` |
| XML in, JSON out | `Content-Type: application/xml`, `Accept: application/json` |
| JSON in, XML out | `Content-Type: application/json`, `Accept: application/xml` |

All four combinations are verified working on `GET /definition`, `GET /services`, `POST /transaction`, and `POST /transaction/get`. Error responses follow the Accept header too (RFC-7807 `application/problem+xml` / `+json`).

### The XML request shape (DataContract)

The same TransactionSet as above, as a working XML body:

```xml
<?xml version="1.0" encoding="utf-8"?>
<TransactionSet xmlns="http://schemas.datacontract.org/2004/07/P21.Transactions.Model.V2">
  <IgnoreDisabled>false</IgnoreDisabled>
  <Name>JobContractPricing</Name>
  <Transactions>
    <Transaction>
      <DataElements>
        <DataElement>
          <Keys xmlns:a="http://schemas.microsoft.com/2003/10/Serialization/Arrays">
            <a:string>item_id</a:string>
          </Keys>
          <Name>JOBPRICELINE.jobpriceline</Name>
          <Rows>
            <Row>
              <Edits>
                <Edit><Name>item_id</Name><Value>WIDGET-001</Value></Edit>
                <Edit><Name>pricing_method</Name><Value>Price</Value></Edit>
                <Edit><Name>price</Name><Value>36.58</Value></Edit>
              </Edits>
              <RelativeDateEdits />
            </Row>
          </Rows>
          <Type>List</Type>
        </DataElement>
      </DataElements>
      <Status>New</Status>
    </Transaction>
  </Transactions>
  <UseCodeValues>false</UseCodeValues>
</TransactionSet>
```

Three rules make or break XML bodies — all verified live:

1. **The root namespace is mandatory.** Without `xmlns="http://schemas.datacontract.org/2004/07/P21.Transactions.Model.V2"` the body deserializes to null and the server returns 400 *"The content field is required."*
2. **Element order is ALPHABETICAL within each parent** (WCF DataContract ordering) — note `<Name>` before `<Transactions>` before `<UseCodeValues>`, `<Keys>` before `<Name>` inside a DataElement, `<Name>` before `<Value>` inside an Edit. Violations are **not** politely rejected: a misordered top-level element returns HTTP 500, and a misordered element deeper down is **silently dropped** — the transaction then fails with *"Object reference not set to an instance of an object."*
3. **`Keys` items use the arrays namespace**: `<a:string>` with `xmlns:a="http://schemas.microsoft.com/2003/10/Serialization/Arrays"`.

**Don't hand-build the shape — ask the server for it.** `GET /api/v2/definition/{Service}` with `Accept: application/xml` returns the service's `Template` as XML *in exactly the required element order*. Fill in the `<Value>`s and post it back.

Other verified XML specifics:

- `POST /api/v2/transaction/get` XML bodies use the root `<TransactionStateRequest>` (same namespace).
- Response roots: `<TransactionSetResult>` from `/transaction`, `<ServiceDefinition>` from `/definition`, `<ArrayOfServiceInfo>` from `/services`.
- [`scripts/validate_payload.py`](../scripts/validate_payload.py) checks XML payloads offline — namespace, element order, `Keys` item namespace, and all the JSON-level semantic rules.

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
| `m_storedprocedureexecutor` | Stored Procedure Executor | Load and execute stored procedure definitions (see [Stored Procedure Executor](#stored-procedure-executor)) (hidden from `/api/v2/services` — see the [PDF Report Generation](#pdf-report-generation) discovery note) |

### Report Services

| Service | P21 Window | Purpose |
|---------|------------|---------|
| `m_reprintpurchaseorders` | PO Reprint | Purchase order PDF reprints (see [PDF Report Generation](#pdf-report-generation)) |
| `m_reprintpicktickets` | Pick Ticket Reprint | Pick ticket PDF reprints |
| `m_picktickets` | Pick Ticket generation | Creates the pick ticket and returns its PDF (see [PDF Report Generation](#pdf-report-generation)) |

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

> **Transactions pass/fail independently.** In a bulk POST, each Transaction in the array is processed on its own: one failing does not roll back the others (no cascade), and `Summary` tallies the outcomes (`Succeeded`/`Failed`/`Other`). Check `Results.Transactions[].Status` (`"Passed"`/`"Failed"`) to see which specific transactions landed — never the HTTP status, which is 200 either way. (Exception: transactions that each re-save the same shared header record can collide — see [Upsert Semantics](#upsert-semantics-keyed-rows-insert-when-absent).)

---

## Field Order Matters

For some services, the order of fields in the request is significant. The API processes fields sequentially and mirrors the window's UI cascades — some fields trigger validation, auto-population, or **clearing** of other fields, exactly as they would when typed into the window in that order.

### Example: SalesPricePage

Fields must be set in this order:
1. `price_page_type_cd` - Triggers type-specific validation
2. `company_id` - Required before product group
3. `product_group_id` or `discount_group_id`
4. `supplier_id`
5. Other fields...

### Example: JobContractPricing — `pricing_method` before `price`

Changing `pricing_method` **clears the typed price**, just like in the UI. If a line row's Edits send `price` before `pricing_method`, the line is created/updated with **price = $0** — and the transaction still reports `Succeeded`. Order the Edits `item_id`, `pricing_method`, `price`. Verified live: reversing the order silently zeroes the price.

> **Rule of thumb:** when a write "succeeds" but a value doesn't stick, suspect a field-order cascade. Order Edits the way a user would fill in the window, and verify written values with OData or `POST /api/v2/transaction/get` after the first run.
>
> **Credit:** [Alex Westemeier](https://github.com/AWestemeier) for the JobContractPricing ordering discovery.

---

## IgnoreDisabled

`IgnoreDisabled: true` does more than suppress errors — it is the documented unlock for writing through **system-disabled columns** and **disabled sub-tabs** that the Transaction API otherwise cannot touch:

- Forms whose defaults carry read-only/system columns (e.g. bin maintenance flags) fail with `General Exception: Column is disabled: <column>` unless the flag is set.
- Some grids that live on a disabled sub-tab (e.g. job contract **BINS** quantities) accept keyed edits once the flag is set — see [Editing Bin Quantities](#editing-bin-quantities-on-an-existing-contract).

Two placement rules:

1. **`IgnoreDisabled` goes at the payload top level** — alongside `Name` and `Transactions`. Placed inside a Transaction object it is **silently ignored**, and every transaction fails with `Column is disabled: <column>`.
2. It applies to the whole TransactionSet — there is no per-transaction form.

```json
{
    "Name": "JobContractPricing",
    "UseCodeValues": false,
    "IgnoreDisabled": true,
    "Transactions": [ ... ]
}
```

> **Caution:** the flag lets edits through columns P21 normally protects. Only send fields you intend to change, and verify results after the first run.
>
> **Credit:** [Alex Westemeier](https://github.com/AWestemeier) for mapping the placement failure mode and the disabled-tab unlock behavior.

---

## UseCodeValues

This setting controls how dropdown/checkbox values are interpreted:

| UseCodeValues | Pass | Example |
|---------------|------|---------|
| `false` (default) | Display value | `"Cancelled": "ON"` |
| `true` | Code value | `"Cancelled": "Y"` |

**Recommendation**: Use `false` (display values) for better readability. (Exception: some report services require code values — see [PDF Report Generation](#pdf-report-generation).)

### Labels vs What the Database Stores (code_p21)

For enum-style columns, the API's display labels come from the **`code_p21`** table (`language_id = 9`), but the database stores the integer **`code_no`** — which is what OData reads return. When you verify a write via OData, map the numbers back to labels with:

```sql
SELECT code_no, code_description
FROM code_p21
WHERE language_id = '9';
```

Verified examples (JobContractPricing cost/pricing enums):

| Enum | Label → code_no |
|------|-----------------|
| Cost type (`*_cost_type_cd`) | `Order`=222, `Source`=220, `Value`=227, `None`=300 |
| Pricing method (`job_price_line.pricing_method`) | `Price`=221, `Source`=220, `Pricing Libraries`=234, `None`=300 |
| Calc method (`*_calc_method_cd`) | `Multiplier`=211, `Percentage`=230, `Difference`=228, `Mark up`=229 |

*(Credit: [Alex Westemeier](https://github.com/AWestemeier) — maps verified against `code_p21`.)*

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
                        {"Name": "oe_order_item_id", "Value": "WIDGET-001"},
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
result = response.json()
succeeded = result['Summary']['Succeeded']
failed = result['Summary']['Failed']
print(f"Succeeded: {succeeded}, Failed: {failed}")

if result["Summary"]["Failed"] > 0:
    for msg in result.get("Messages", []):
        print(f"  Message: {msg}")
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
                            new { Name = "oe_order_item_id", Value = "WIDGET-001" },
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

#### Order Service Gotchas

All verified live (credit: [Alex Westemeier](https://github.com/AWestemeier)):

- **`source_loc_id` is effectively required.** Omitting it fails with a *"Jurisdiction ID for Order Header Tax"* error — the tax jurisdiction does not auto-populate through the API the way it does in the UI. A realistic header sets `customer_id`, `sales_loc_id`, `source_loc_id`, `order_date`, `requested_date`, `po_no`, `taker`, `ship_to_id`, and `contact_id`.
- **`requested_date` must be after `order_date`.** The same date trips a date-cascade prompt, which the stateless API can't answer.
- **`company_id` is a disabled column** on the Order window — don't send it.
- **DynaChange prompts are auto-answered with the default** (usually "No"), which silently discards the affected line — e.g. *"order line does not have a PO Cost… proceed? [No]"*. On multi-item orders the remaining lines then cascade-fail. This is a P21 configuration matter (exempt the rule for the API user, or fix the data), not something a payload change can work around — see [DynaChange and Popup Handling](#dynachange-and-popup-handling).
- **Assembly items cannot be entered via the Transaction API** when they should explode or spawn a production order — the *"add as assembly?"* prompt is auto-answered **No**, killing the explode. Use the Interactive API for those lines: see [Sales Order Entry with Assembly Lines](04-Interactive-API.md#sales-order-entry-with-assembly-lines).
- The created `order_no` comes back in the result rows; check `Summary.Succeeded`, not the HTTP status.

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

The `JOBPRICECOST` DataElement includes `commission_cost_value` and related commission fields. These columns are **disabled by default** -- without special handling the API returns "Column is disabled: commission_cost_value".

**They are writable with `IgnoreDisabled: true`** at the payload top level (see [IgnoreDisabled](#ignoredisabled)). Key the element by `item_id` and set the cost type before the value -- verified live, including in the same transaction as a line insert:

```json
{
    "Name": "JOBPRICECOST.jobpricecost",
    "Type": "Form",
    "Keys": ["item_id"],
    "Rows": [{
        "Edits": [
            {"Name": "item_id", "Value": "WIDGET-001"},
            {"Name": "commission_cost_type_cd", "Value": "Value"},
            {"Name": "commission_cost_value", "Value": "17.19"}
        ]
    }]
}
```

`commission_cost_type_cd` accepts the display labels `Order`, `Source`, `Value`, `None` (with `UseCodeValues: false`). Setting only the commission cost leaves `other_cost` untouched.

> **Credit:** [Alex Westemeier](https://github.com/AWestemeier) verified the `IgnoreDisabled` commission-cost write path. The Interactive API (JobContractPricing window) remains an alternative.

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
- **`end_date` must be >= today.** The header is validated on every save; a past date is rejected with *"end date must be equal to or greater than today"*. This means you cannot edit lines on an **expired** contract without also moving its `end_date` forward (a real side effect) -- for expired contracts, use the Interactive API instead.
- **Identify renewals by `job_no`.** Contract renewals can leave the same `contract_no` on two header rows; `job_no` is unique. Include it in the FORM Edits whenever it's known.

#### Upsert Semantics -- Keyed Rows Insert When Absent

`Status: "New"` with a keyed List row is an **upsert**: if the key matches an existing row it updates that row, and if it doesn't match, P21 **inserts a new row**. This means the Transaction API can add brand-new lines to an existing contract -- no Interactive API needed. Verified live: 81 new lines added to an existing contract in one run (price, pricing_method, and commission cost all confirmed in the database with unique `line_no` values).

The payload is identical to the update example above -- the only difference is whether `item_id` already exists on the contract.

**Concurrency gotcha -- one transaction per POST when inserting lines.** Every transaction re-saves the shared FORM header. If you batch several line-insert transactions into one POST:

- all but one fail with an optimistic-concurrency error (*"Your changes could not be saved because changes to this information have been made outside of..."*), and
- the transactions that do land can get **duplicate `line_no`** values, because `line_no` is not incremented across transactions within a single POST.

Submit each insert as its own POST -- each one then sees the current max `line_no` and increments it correctly. (This applies to **inserts that re-save the same header**; editing existing keyed rows -- prices, bin quantities -- batches fine in one POST.)

> **Credit:** [Alex Westemeier](https://github.com/AWestemeier) verified the upsert behavior and the header-collision failure mode.

#### Editing Bin Quantities on an Existing Contract

Contract bin quantities (`BINS.bins` -- `min_qty`, `max_qty`, `reorder_qty`, `capacity`) live on a sub-tab that is normally disabled until a parent row is selected, which the stateless Transaction API cannot do. **`IgnoreDisabled: true` unlocks it** (see [IgnoreDisabled](#ignoredisabled)). One POST, batchable across many bins:

```json
{
    "Name": "JobContractPricing",
    "UseCodeValues": false,
    "IgnoreDisabled": true,
    "Transactions": [{
        "Status": "New",
        "DataElements": [
            {
                "Name": "FORM.d_dw_job_price_hdr", "Type": "Form", "Keys": [],
                "Rows": [{"Edits": [
                    {"Name": "job_no", "Value": "31"},
                    {"Name": "customer_id", "Value": "100198"},
                    {"Name": "ship_to_id", "Value": "200"}
                ]}]
            },
            {
                "Name": "JOBPRICELINE.jobpriceline", "Type": "List", "Keys": ["item_id"],
                "Rows": [{"Edits": [
                    {"Name": "item_id", "Value": "WIDGET-001"}
                ]}]
            },
            {
                "Name": "BINS.bins", "Type": "List",
                "Keys": ["contract_bin_id", "customer_id", "ship_to_id"],
                "Rows": [{"Edits": [
                    {"Name": "contract_bin_id", "Value": "A01-02"},
                    {"Name": "customer_id", "Value": "100198"},
                    {"Name": "ship_to_id", "Value": "200"},
                    {"Name": "min_qty", "Value": "30"},
                    {"Name": "max_qty", "Value": "100"},
                    {"Name": "reorder_qty", "Value": "40"},
                    {"Name": "capacity", "Value": "100"}
                ]}]
            }
        ]
    }]
}
```

Gotchas (all verified live):

- **`IgnoreDisabled: true` is mandatory** -- without it the defaults template trips *"Column is disabled: ..."* and the BINS tab stays locked.
- **Select the line by `item_id`** (the JOBPRICELINE key). Selecting by `line_no` alone fails with *"Sequence contains no matching element."* If the same item appears on multiple lines, add `line_no` as a second key.
- **Batching is fine here**: repeat the `JOBPRICELINE` + `BINS.bins` pair per bin inside the same Transaction. Unlike line inserts, bin edits don't collide on the header.
- **No `end_date` required** on this path -- it works on expired contracts too, unlike line-field updates.
- HTTP 200 can still carry `Summary.Failed > 0` -- check `Summary` and `Messages`.

> **Credit:** [Alex Westemeier](https://github.com/AWestemeier) discovered and verified the `IgnoreDisabled` bins path (single and multi-bin batches, database-confirmed). The Interactive API (select ship-to row, then line, then BINS tab) also works as a slower fallback.

#### Known Limitations

- **Commission fields disabled by default:** require `IgnoreDisabled: true` (see [Commission Costs](#commission-costs) above).
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
    f"{base_url}/api/ui/router/v1/?urlType=external",
    headers={"Authorization": f"Bearer {token}"},
    verify=False,
    follow_redirects=True,
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
    f"{base_url}/api/ui/router/v1/?urlType=external",
    headers={"Authorization": f"Bearer {token}"},
    verify=False,
    follow_redirects=True,
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

### Item Service -- Nested Location Edits

The `Item` service (Item Maintenance window) supports **nested DataElement navigation** that mirrors the UI: select the item, select a location row, then edit that location's detail. This is the Transaction-API equivalent of "select parent row → edit child detail," and it works because the Item window's tabs aren't gated behind row selection. It's a good template for any nested edit.

#### Set an item's primary bin at a location (Form → List → Form)

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

`Status: "New"` with populated `Keys` updates the existing keyed record (it does not create a new item).

#### Set an item's primary supplier at a location (Form → List → List)

Same window, one level different — the third element is the supplier list:

```json
{ "Name": "SUPPLIER_X_LOCATION.supplier_x_location", "Type": "List", "Keys": ["supplier_id"],
  "Rows": [{ "Edits": [
      {"Name": "supplier_id", "Value": "20000"},
      {"Name": "primary_supplier", "Value": "ON"}
  ] }] }
```

What this writes, and the cascade (verified on a 68-item production run):

- `primary_supplier` maps to `inventory_supplier_x_loc.primary_supplier` (a Y/N flag) — **not** `inv_loc.primary_supplier_id`.
- Setting it `ON` makes P21 auto-unset the previous primary at that location **and** update `inv_loc.primary_supplier_id` to the new supplier. So the flag is the field to **write**; `inv_loc.primary_supplier_id` is the field to **read** when verifying.

#### Item Service Gotchas

- **Silent no-op — the big one.** The target supplier must already have a *location-level* row (`inventory_supplier_x_loc`) at that location. If it doesn't, the transaction still returns `Succeeded = 1` but **nothing flips** — there is no row to promote. (P21 allows cutting a PO to a supplier without location setup, so a supplier can appear in PO history yet be absent from the location's supplier list.) **Always verify `inv_loc.primary_supplier_id` after writing** — do not trust `Succeeded`. Fix: add the location supplier row first, then set the flag.
- **"Item Issues Detected" popup.** Items with data problems return an `Unexpected response window: Item Issues Detected` (`w_rule_callback_response`) in the response `Messages`. The Transaction API cannot get past this popup — it effectively answers "No" and discards the change. Use the Interactive API for those items and answer the popup with `cb_1` ("Yes, Proceed Anyway") — see [Item window popups](04-Interactive-API.md#worked-example-item-issues-detected-rule-callback). Which items trip the rule differs per environment (it fires on each item's data state) — run transaction-first, verify, and fall back to the Interactive API for whatever didn't stick.
- `SUPPLIER_X_LOCATION` is keyed by `supplier_id` scoped to the selected location row in the Transaction API, so the nested pattern is safe here. (The equivalent *interactive* flow must match rows on both `location_id` and `supplier_id` — the grid holds every location's rows.)

> **Credit:** [Alex Westemeier](https://github.com/AWestemeier) — patterns and gotchas verified in production (July 2026).

### BinLocation Service -- Creating Bins

The `BinLocation` service *is* the **Bin Location Maintenance** window: its form element `FORM.form` is business object `bin` (datawindow `d_dw_bin_form`), and every field in the payload is a real field on that screen. Bulk bin creation is a clean Transaction API use case — verified in production at hundreds of bins per run.

```json
{
  "Name": "BinLocation",
  "UseCodeValues": false,
  "IgnoreDisabled": true,
  "Transactions": [
    {
      "Status": "New",
      "DataElements": [
        { "Name": "FORM.form", "Type": "Form",
          "Keys": ["company_id", "location_id", "bin_id"],
          "Rows": [ { "Edits": [
            {"Name": "company_id",      "Value": "ACME"},
            {"Name": "location_id",     "Value": "10"},
            {"Name": "bin_id",          "Value": "A01-02-03"},
            {"Name": "bin_type",        "Value": "SHELF"},
            {"Name": "putaway_zone_id", "Value": "ZONE-A"},
            {"Name": "pick_zone_id",    "Value": "ZONE-A"},
            {"Name": "bin_length", "Value": "10"}, {"Name": "bin_width", "Value": "10"}, {"Name": "bin_height", "Value": "11"},
            {"Name": "warehouse_sequence", "Value": "1"}, {"Name": "putaway_zone_sequence", "Value": "1"}, {"Name": "pick_zone_sequence", "Value": "1"},
            {"Name": "max_unique_items", "Value": "0"},
            {"Name": "pick_locked_flag", "Value": "OFF"}, {"Name": "put_locked_flag", "Value": "OFF"},
            {"Name": "full_flag", "Value": "OFF"}, {"Name": "frozen_flag", "Value": "OFF"},
            {"Name": "consolidation_bin_flag", "Value": "OFF"}, {"Name": "stage_bin_flag", "Value": "OFF"}, {"Name": "door_bin_flag", "Value": "OFF"}
          ] } ] }
      ]
    }
  ]
}
```

`Status: "New"` with the three-field key makes this a create when the `(company_id, location_id, bin_id)` combination doesn't exist yet.

#### BinLocation Gotchas

- **`IgnoreDisabled: true` is mandatory — and it must be at the payload top level.** `frozen_flag` and other system columns are disabled on the bin form; without the flag every transaction fails with `General Exception: Column is disabled: frozen_flag`. Placed inside a Transaction object instead of the top level, the flag is silently ignored and you get the same failure (see [IgnoreDisabled](#ignoredisabled)).
- **Pass codes, not uids.** `bin_type` and the zone fields take the **code** (`SHELF`, `ZONE-A`), not the internal uid. The zone code is the same across stocking locations; only the internal uid differs, and P21 resolves it from code + location.
- **Flags are `ON`/`OFF` on the form but stored `Y`/`N` in `dbo.bin`.** When cloning field values from an existing bin, convert (`Y`→`ON`, `N`→`OFF`).
- **Don't send `master_bin_flag`** — P21 auto-sets it.
- **Clone the constants from a "twin," don't invent them.** Query an existing bin of the same `bin_type` and copy the type, both zone codes, dimensions, sequences, `max_unique_items`, and flags — that guarantees new bins match what the warehouse already uses. Zone codes come from joining `bin.putaway_zone_uid` / `bin.pick_zone_uid` → `bin_zone.bin_zone_uid` → `bin_zone.bin_zone_id`.
- **HTTP 200 ≠ success.** Check `Results.Transactions[].Status == "Passed"` (or `Summary`) — in a bulk POST each transaction passes/fails independently.
- **Bulk is fine and fast** (tens of transactions per POST). Re-running is safe if you skip `(bin_id, location_id)` pairs that already exist.
- **Read-back:** the raw `bin` table isn't always exposed via OData — verify through the `p21_view_bin` view instead, and compare field-for-field against the twin after the first run.

> **Credit:** [Alex Westemeier](https://github.com/AWestemeier) — pattern verified in production (July 2026), including the `IgnoreDisabled` placement failure mode.

---

## PDF Report Generation

The Transaction API includes a dedicated endpoint for generating PDF documents -- purchase orders, pick tickets, and other printable reports. The endpoint returns the rendered PDF as a base64-encoded string in the response body.

**Endpoint:** `POST {ui_server}/api/v2/process/pdfreport`

> **Wrong-endpoint trap:** `POST /api/v2/transaction` *accepts* an `m_*` report payload and returns `Succeeded` — but **emits nothing**. A report is a process, not a record edit; it must go to `POST /api/v2/process/pdfreport`. (Credit: [Alex Westemeier](https://github.com/AWestemeier) — "this was the single biggest gotcha.")

### Verified Report Services

| Service Name | Report Type |
|-------------|-------------|
| `m_reprintpurchaseorders` | Purchase Order reprints |
| `m_reprintpicktickets` | Pick Ticket reprints |
| `m_picktickets` | Pick ticket generation — **creates** the pick ticket record and returns its PDF (see [worked example below](#example-generate-a-production-order-pick-ticket-m_picktickets)) |

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

Constants that apply to every report payload: `Status` and `Type` are **numeric `0`** (not the `"New"` record-edit shape) and the DataElement carries `Keys: []`. Get the criteria field names from `GET /api/v2/definition/{service_name}` and default values from `GET /api/v2/defaults/{service_name}`.

> **`UseCodeValues` requirements vary per report service.** `m_reprintpurchaseorders` works with `UseCodeValues: false` (as above), but `m_picktickets` **requires `UseCodeValues: true` with code values** — e.g. `create_pick_ticket_type` must be the code `"P"`; the display label `"Production Order"` is rejected, and `UseCodeValues: false` returns HTTP 500. When a report errors on seemingly-correct criteria, retry with `UseCodeValues: true` and the code values from the service's definition (`ValidValues`).

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
    "HostName": "p21web-01",
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
    f"{base_url}/api/ui/router/v1/?urlType=external",
    headers={"Authorization": f"Bearer {token}"},
    verify=False,
    follow_redirects=True,
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

### Example: Generate a Production-Order Pick Ticket (m_picktickets)

Running `m_picktickets` **creates the pick-ticket record** at the given `location_id` **and** returns the PDF in a single call. This matters for production orders that are built at one location while their components stock at another — the `ProductionOrder` transaction print flag only emits at the *make* location (see [PDFs from the /transaction endpoint](#pdfs-from-the-transaction-endpoint-print-flags) below), but this report generates the ticket at whatever location you specify.

```json
POST /api/v2/process/pdfreport

{
  "Name": "m_picktickets",
  "UseCodeValues": true,
  "Transactions": [
    {
      "Status": 0,
      "DataElements": [
        {
          "Keys": [],
          "Type": 0,
          "Name": "TABPAGE_1.tp_1_dw_1",
          "Rows": [{ "Edits": [
            { "Name": "create_pick_ticket_type", "Value": "P" },
            { "Name": "beg_prod_order", "Value": "1000123" },
            { "Name": "end_prod_order", "Value": "1000123" },
            { "Name": "location_id",    "Value": "10" }
          ] }]
        }
      ]
    }
  ]
}
```

Every one of these is required to make it fire:

- Endpoint **`/api/v2/process/pdfreport`** (not `/api/v2/transaction` — see the wrong-endpoint trap above).
- `Status` and `Type` numeric **`0`**, `Keys: []`.
- `create_pick_ticket_type` = the **code** `"P"` (Production Order) with **`UseCodeValues: true`** — the label is rejected, and `UseCodeValues: false` returns HTTP 500.
- `location_id` = the location whose inventory the components pick from. No date range needed.
- **Prerequisite:** the production order's form must already be printed (`prod_order_hdr.printed = 'Y'`) — run a `ProductionOrder` transaction with `print_form = ON` first.

The response is the standard document array; the PDF is base64 at `[0].DocumentData` (`FileName` like `"PPT<nnn> PRODUCTION_PICK_TICKET.pdf"`). Side effect: the pick-ticket row now exists in P21 at that location and can be confirmed/completed like any other.

For any *other* report, swap `Name` and the criteria `Edits` (field names from `GET /api/v2/definition/{name}`); the endpoint, `Status`/`Type: 0`, `Keys: []`, and the `DocumentData` extraction stay the same.

> **Credit:** [Alex Westemeier](https://github.com/AWestemeier) — verified end-to-end (report run → pick ticket row created → PDF returned → ticket confirmed and completed).

### PDFs from the /transaction endpoint (print flags)

The regular `POST /api/v2/transaction` endpoint can also return generated PDFs: when a service exposes print flags (e.g. `ProductionOrder` with `print_pick_ticket = ON` and `print_form = ON` on `TABPAGE_1.tp_1_dw_1`), the successful transaction response carries the rendered documents at `Results.Transactions[].Documents[].DocumentData` (base64, one entry per document).

Caveats (verified on `ProductionOrder`):

- Documents are only returned on a **savable** transaction — a bare reprint with nothing new to save errors with *"Save is not enabled"*.
- `print_pick_ticket` emits only at the order's **make location**. If components stock elsewhere, the pick ticket comes back empty or missing — generate it with `m_picktickets` at the stock `location_id` instead (previous section).

> **Credit:** [Alex Westemeier](https://github.com/AWestemeier).

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
    f"{base_url}/api/ui/router/v1/?urlType=external",
    headers={"Authorization": f"Bearer {token}"},
    verify=False,
    follow_redirects=True,
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

See the `examples/python/transaction/` (Python) and `examples/csharp/Transaction/` (C#) directories for working examples:

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
- [examples/python/transaction/](https://github.com/mrwuss/p21-api-documentation/tree/master/examples/python/transaction/) - Working examples
- [examples/python/production/](https://github.com/mrwuss/p21-api-documentation/tree/master/examples/python/production/) - Production & labor examples
