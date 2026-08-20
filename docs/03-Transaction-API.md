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
| `/api/v2/basics/{name}` | GET | Abbreviated field list for a service, as a ready-to-fill payload skeleton (see note below) |
| `/api/v2/transaction/get` | POST | Retrieve existing records |
| `/api/v2/transaction` | POST | Create or update records (sync) |
| `/api/v2/transaction/async` | POST | Async create/update (returns RequestId) |
| `/api/v2/transaction/async/callback` | POST | Async with callback URL |
| `/api/v2/transaction/async?id={id}` | GET | Check async request status |
| `/api/v2/commands` | POST | Process special commands (see [Commands Endpoint](#commands-endpoint)) |
| `/api/v2/process/pdfreport` | POST | Generate PDF reports (see [PDF Report Generation](#pdf-report-generation)) |

> **The three discovery endpoints, and which one answers your question.** `definition`, `defaults` and `basics` take the same `{service_name}` path segment and are the routine way to learn a window's shape without opening P21. Between them: **`definition`** returns the full schema — every DataElement, field, `DataType`, `KeyFields`, and the accepted values for dropdown/code fields, which is where valid values for site-specific fields such as `carrier_id` come from (see [Get Service Definition](#get-service-definition)); **`defaults`** returns the service's default values and a payload template you can fill in and post back; **`basics`** returns the same element list carrying only each element's headline fields, already shaped as a `Status: "New"` TransactionSet with `Keys` prefilled from the element's `KeyFields` and `IgnoreIfEmpty: true` on every edit — fill in the values and POST it. The abbreviation is severe and that is the point: on `Order` all three return the same **102** elements, but `basics` carries **103** fields against `definition`/`defaults`' **1,266**.
>
> The community session's warning about `basics` holds in both directions, so treat it as a starting point rather than a contract — verified on 26.1 with `Order`:
>
> - **It omits fields you need.** Its header element lists `order_no`, `sales_loc_id`, `contact_id`, `po_no`, `order_date`, `company_id`, `taker`, `requested_date` — but a create also needs `customer_id`, `source_loc_id` and `ship_to_id`, none of which appear. Omitting `ship_to_id` fails the save with the unattributed message `This column is required.` (no column named).
>
> - **It includes fields you cannot write.** `company_id` is in that same list and is refused on save with `Column is disabled: company_id`.
>
> `basics` also answers for **report services** (`m_*`) — and there it shines: a report window carries only a handful of criteria fields, so `basics` returns a ready-to-fill criteria skeleton in a few hundred bytes (`m_picktickets`: 601 bytes against `definition`'s 15.8 KB), the API-side equivalent of reading the criteria names out of *SQL Help* (see [PDF Report Generation](#pdf-report-generation)). An unknown service name returns an **empty HTTP 500**, the same shape `definition` and `defaults` give. *(Endpoint and behavior verified against a 26.1 tenant, August 2026; originally surfaced in a community session, Felipe Maurer, 2026.)*

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

> Payload shape only. Full runnable version: [Create Order](#create-order).

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

## Keys -- Row Identity and the Collapse Trap

The `Keys` array on a DataElement is **not** an authentication key, a consumer key, or a database primary key. It is how the Transaction API decides **which rows in a `List` element are the same row**. Most payloads never need it, which is why it goes unnoticed — but when it matters, the failure is silent: the API returns `Succeeded`, and the record is simply not what you sent.

> **Provenance:** first described in a community conference session on the P21 APIs (*Felipe Maurer*, 2026), then **verified end-to-end against a 26.1 tenant** (August 2026) — the collapse, the `Keys` fix, the over-keying failure and the stable-key update below are each a live `Order` create or update with a `/transaction/get` read-back. It is the same rule as the independently verified [Upsert Semantics](#upsert-semantics-keyed-rows-insert-when-absent) and [contract bin](#editing-bin-quantities-on-an-existing-contract) behavior, seen from the row-identity side.

### The collapse: two rows in, one row out

Send an order with the same item twice at different quantities and no `Keys`:

```json
{
    "Name": "TP_ITEMS.items",
    "Type": "List",
    "Keys": [],
    "Rows": [
        {"Edits": [{"Name": "oe_order_item_id", "Value": "WIDGET-001"},
                   {"Name": "unit_quantity",    "Value": "5"}]},
        {"Edits": [{"Name": "oe_order_item_id", "Value": "WIDGET-001"},
                   {"Name": "unit_quantity",    "Value": "10"}]}
    ]
}
```

You do not get two lines of `WIDGET-001`. You get **one line, quantity 10** — the two rows were treated as one row and the **last** value written for each field won. No error, no warning, `Succeeded: 1`.

Two *different* item IDs in the same payload behave exactly as you expect, which is why this trap stays hidden until the day a real order legitimately carries the same item on more than one line (different lengths cut from one stock item, separate scheduled releases, split shipping dates).

### Keys are a `GROUP BY`

If you know SQL, the model is straightforward: the API is grouping the rows you send, and `Keys` is the `GROUP BY` list. Rows that agree on every key field are one row; name a field whose value **differs** between the rows and they split apart.

For the payload above, the field that actually differs is the quantity:

```json
    "Keys": ["unit_quantity"],
```

Now the same two rows produce two lines — quantity 5 as `user_line_no` 001 and quantity 10 as 002. Two *different* item IDs need no `Keys` at all: with `Keys: []` they already come back as two lines.

### Choosing a key

- **You cannot invent one, and you must send it.** A key must be a real column on that element *and* appear in every row's `Edits` — there is no synthetic row-id or ascending-integer you can supply. Both failures are hard, not silent, and their messages are worth recognizing: naming a column you did not put in `Edits` fails the transaction with the opaque `General Exception: Sequence contains no matching element`; naming something that is not a column at all fails with the clearer `Invalid column name: {name}`. Either way `Failed: 1`, nothing is written.
- **Pick the column that differs.** On an order line, `oe_order_item_id` is a *bad* key for this problem precisely because it is the value that is the same. Fields that commonly work: quantity, a customer/user line number (`user_line_no` on `TP_ITEMS.items`), or a date field where the rows genuinely differ.
- **Timestamp columns are a last resort.** Some elements have no natural discriminator, leaving `date_created`-style columns as the only option. They usually differ, but rows written in the same operation — or loaded by an import — can share a timestamp, and then the collapse comes back.
- **Compound keys are allowed** — as many columns as it takes to make the rows unique.
- **Surplus keys are accepted silently.** A key that is real and sent but doesn't discriminate is not an error — `Keys: ["unit_quantity", "oe_order_item_id"]` splits the two rows above exactly as `["unit_quantity"]` alone does, with no warning that the second key separated nothing. Adding keys until the behavior changes is a legitimate debugging tactic, but it means a wrong key set looks exactly like a right one.
- **Deleted rows are still rows.** Keying on a positional or UID-style line identifier read from the UI can miss soft-deleted lines that the window doesn't show, so the key you send points at a different row than the one you counted.

### Over-keying breaks updates

Keys make rows unique in **both** directions. Because a keyed `Status: "New"` row is an [upsert](#upsert-semantics-keyed-rows-insert-when-absent) — update when the key matches, insert when it doesn't — a key set that is *too* specific stops matching the row you meant to change, and the "update" silently becomes a new line.

The classic case: keying on the quantity (the fix above) and then trying to change that quantity from 10 to 20. The new value doesn't match the existing row's key, so P21 appends a line instead of editing one. Verified against the two-line order created above:

```json
{"Name": "TP_ITEMS.items", "Type": "List",
 "Keys": ["unit_quantity"],
 "Rows": [{"Edits": [{"Name": "oe_order_item_id", "Value": "WIDGET-001"},
                     {"Name": "unit_quantity",    "Value": "20"}]}]}
```

`Succeeded: 1`, no messages — and the order now has **three** lines (5, 10, 20) instead of two. Key on something **stable** when updating: the same edit keyed on `user_line_no`, with `user_line_no` sent in `Edits`, changes that line in place and leaves the line count alone.

```json
{"Name": "TP_ITEMS.items", "Type": "List",
 "Keys": ["user_line_no"],
 "Rows": [{"Edits": [{"Name": "user_line_no",     "Value": "003"},
                     {"Name": "oe_order_item_id", "Value": "WIDGET-001"},
                     {"Name": "unit_quantity",    "Value": "33"}]}]}
```

Key on the discriminator when creating; key on something stable when updating.

### Design for updates: assign your own line handles

`user_line_no` is **caller-assignable at create time**, which turns the stable-key advice from a debugging move into a design: give every line a handle you chose, and every later update is deterministic. Verified on 26.1 — an order created with the same item on handles `010` and `020` (`Keys: ["user_line_no"]`, so it also solves the collapse), then updated by handle:

```json
{"Name": "TP_ITEMS.items", "Type": "List",
 "Keys": ["user_line_no"],
 "Rows": [{"Edits": [{"Name": "user_line_no",     "Value": "020"},
                     {"Name": "oe_order_item_id", "Value": "WIDGET-001"},
                     {"Name": "unit_quantity",    "Value": "9"}]}]}
```

changes exactly that line in place — no phantom inserts, no dependence on P21's own numbering. Integrations that create-then-maintain order lines should assign handles on day one (gapped values like `010`/`020` leave room to insert between).

### What the definition already tells you

Every element in [`definitions/{Service}.json`](../definitions/README.md) carries a `KeyFields` array — the key fields P21 declares for that element. Read it before sending repeated rows: in the cases below the declared fields line up exactly with the behavior described above, which makes `KeyFields` the best available predictor of what your rows will be folded on. (Confirm with a read-back on a service you haven't tried — the correspondence is consistent across the services documented here, but the collapse itself was exercised live only on `Order`.) Across the committed definitions, **214 of 335 `List` elements declare key fields**; the remaining third declare none.

| Service | Element | Declared `KeyFields` |
|---------|---------|----------------------|
| `Order` | `TP_ITEMS.items` | `["oe_order_item_id"]` |
| `JobContractPricing` | `JOBPRICELINE.jobpriceline` | `["item_id", "line_no"]` |
| `Item` | `TABPAGE_17.invloclist` | `["location_id"]` |
| `ConvertPOToVoucher` | `TABPAGE_17.tp_17_dw_17` | `["receipt_number", "line_number", "po_no"]` |

`Order`'s item grid declaring `oe_order_item_id` is exactly why the collapse above happens on the item ID. And `JOBPRICELINE` declaring `["item_id", "line_no"]` is the same rule from the other side — which is why the verified contract-line guidance says to select by `item_id` and to **add `line_no` as a second key when the same item appears on multiple lines** (see [Editing Bin Quantities](#editing-bin-quantities-on-an-existing-contract)).

Read them straight out of the JSON:

```bash
python -c "import json;d=json.load(open('definitions/Order.json'));[print(e['Name'],e.get('KeyFields')) for e in d['TransactionDefinition']['DataElementDefinitions'] if e['Type']=='List']"
```

The live endpoint carries the same field — see [Get Service Definition](#get-service-definition), which prints `KeyFields` per element.

### Debugging a key problem

The symptom is always the same shape: **the write succeeded and the data is wrong** — a line missing, a quantity belonging to a different line, or an update that appeared as a new row. When that happens:

1. Read the record back with [`POST /api/v2/transaction/get`](#endpoints) and compare it to what you sent, row for row.
2. Look up the element's `KeyFields` in its definition — that is what your rows were folded on.
3. Add the column that genuinely differs between your rows to `Keys`, resend, read back again.

Do this deliberately on a test system before you need it: send ten rows of the same item at ten quantities, predict the result, then compare. It is a fast way to build the instinct, and it is the one Transaction-API behavior that reads as the API being broken when it is doing exactly what it was told.

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
| `SalesPricePage` | Sales Price Page Maintenance | Price page management — also drivable through the Transaction API, see [08 § Transaction API Alternative](08-SalesPricePage-Codes.md#transaction-api-alternative) |
| `PurchaseOrder` | Purchase Order Entry | Create POs (Regular). Pick a non-Regular PO type via a **type-specific service**, not by setting `po_hdr_po_type` — see [Purchase Order Types](#purchase-order-types-and-the-disabled-po_hdr_po_type-column) |
| `RequisitionPurchaseOrder` | Purchase Order Entry (type preset to Requisition) | Create requisition (internal / not-for-resale) POs — `po_hdr.po_type = 'R'`. Same window as PO Entry; easy to miss in `/api/v2/services`. See [create-requisition-po](recipes/create-requisition-po.md) |
| `Shipping` | Shipping | Confirm shipments and set the carrier tracking number — the only service that writes `oe_pick_ticket.tracking_no`, and it refuses an already-invoiced pick ticket. See [Shipping Service — Carrier Tracking Number](#shipping-service-carrier-tracking-number) |
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

### Purchase Order Types and the disabled `po_hdr_po_type` column

You **cannot** choose a PO type by setting `po_hdr_po_type` on the `PurchaseOrder` service — it is a **disabled column** and sending it fails with `Column is disabled: po_hdr_po_type`. The PO type is selected by choosing the **type-specific service** instead (each maps to the same PO Entry window, `w_purchase_order_entry_sheet`, with the type preset). `RequisitionPurchaseOrder` is the verified example; see [create-requisition-po](recipes/create-requisition-po.md).

The `po_hdr_po_type` `ValidValues` in the definition carry **display names only, no code list** — the stored `po_hdr.po_type` letters are undocumented. Verified/inferred mapping from the definition's display list plus live data:

| Letter | Display name | Notes |
|--------|-------------|-------|
| `B` | Regular | Backorder |
| `S` | Regular | Stock replenishment (both `B` and `S` display "Regular") |
| `P` | Special | |
| `D` | Direct Ship | |
| `N` | Non-Stock | |
| `R` | **Requisition** | **verified** via `RequisitionPurchaseOrder` create + DB read-back |
| `X` | Process PO | |
| `Q` | Vendor RFQ | |

> Only `R` (Requisition) is verified end-to-end; the rest are inferred from the display-name order and live data — treat them as strong hints, not confirmed. Environment: 26.1.5894.1 (play), July 2026.

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

> **It is not a universal unlock — and it can hide the failure.** On P21 26.1, writes to the JobContractPricing `VALUES.values` element are refused with `General Exception: Tab page is disabled and cannot be selected`. Adding `IgnoreDisabled: true` flips the response to `Summary: {"Failed": 0, "Succeeded": 1}` / `Status: "Passed"` and **writes nothing** — the echoed response even drops the affected DataElements, so the omission is invisible in the response body. The same false success reproduces on the JobContractPricing header column `corp_address_id` and on `Order`'s `LINE_NOTE.line_note` — three unrelated surfaces, marking it as platform behavior. **Always read back after a write that used this flag.** Detail: [VALUES Writes Are Refused on 26.1](#values-writes-are-refused-on-261) and [Breaking Changes entry 8](14-Breaking-Changes.md#8-ignoredisabled-true-reports-success-on-writes-that-write-nothing).

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

## Reading One Record -- POST /transaction/get

`POST /api/v2/transaction/get` is the Transaction API's read side. It is a **POST despite being called "get"** — the key you are looking up travels in the body, not the query string, so a GET against this path is not the call you want.

Give it a service name and the key identifying one record, and it returns **that record as a complete TransactionSet** — every populated field across every tab of the window, in the same shape you would POST back to `/transaction`. Examples throughout this doc use it as the read-back after a write; the same call is also the fastest way to see what a window actually holds.

### When this, and when OData

Both read data and neither writes. They differ in shape, and the choice is usually obvious once stated:

| | `POST /transaction/get` | OData |
|---|---|---|
| **Scope** | One record | Many records |
| **Breadth** | The whole window — every tab assembled for you | One table or view per query |
| **Joins** | Already done, exactly as the window does them | Yours to do — chain queries by `_uid` or build a view |
| **Use it for** | Inspecting or cloning a single order/item/customer, verifying a write | Reporting, exports, bulk lookups, dashboards |

The practical difference is the assembly. Pulling one item's full picture over OData means knowing that `inv_mast`, `inv_loc`, `inventory_supplier` and friends go together and querying each; `/transaction/get` returns what the window shows, already joined. Past one record, that advantage inverts and OData wins outright.

### Clone an existing record

Because the response is shaped like a request, the read output is a ready-made template: **read one record, change the key field, POST the result to `/transaction`.** It is the practical way to duplicate a well-configured record rather than reconstructing it field by field — a "standard CSR" user copied to a new hire, a customer or location modeled on an existing one, an item cloned from its nearest sibling.

Expect to edit the payload rather than replaying it verbatim, and budget for these:

- **Disabled and auto-generated fields come back in the response** even though you cannot write them. On `Order` the replay stops one field at a time — `Column is disabled: customer_name`, then `Column is disabled: company_id` — because the read returns display columns the window computes rather than accepts. `IgnoreDisabled: true` is the usual reach, but it is **not a reliable unlock** and it can report success while writing nothing; see [IgnoreDisabled](#ignoredisabled) and [Breaking Changes entry 8](14-Breaking-Changes.md#8-ignoredisabled-true-reports-success-on-writes-that-write-nothing). Deleting the offending fields is the cleaner fix, and **[`GET /api/v2/basics/{name}`](#endpoints) is a good filter to delete them by** — intersecting the read-back with the `basics` field list (then adding back the keys `basics` omits) turned a failing verbatim replay of a two-line order into a clean clone in one pass.
- **Popups, locked tabs and stale references** (a location that no longer exists, say) stop the replay the same way they would stop any other transaction. So does ordinary cross-field validation on values that were fine on the original record: a verbatim replay of a same-day order failed on `The Expedite Date must be on or before the Required Date`, because the read hands back both dates and the window re-validates them on the way in.
- **Read the clone back** before treating it as done. A partially-applied clone reports success like any other transaction.

### Reading several records in one call

`TransactionStates` is a list, and it behaves like one: give it *N* key sets and the response carries *N* `Transactions`, each a complete record.

```json
{
  "ServiceName": "Order",
  "TransactionStates": [
    {"DataElementName": "TABPAGE_1.order", "Keys": [{"Name": "order_no", "Value": "1000001"}]},
    {"DataElementName": "TABPAGE_1.order", "Keys": [{"Name": "order_no", "Value": "1000002"}]}
  ]
}
```

Size the request with that in mind — one `Order` record is a few hundred KB of JSON, so this is a way to fetch a handful of records, not a bulk export. For anything wider, use OData.

**There is no server-side subsetting** (probed on 26.1): the response envelope's `Query`, `FieldMap` and `TransactionSplitMethod` fields are echo-only on this endpoint — sending them back populated, or adding element-list fields, changes nothing (byte-identical response). Keying a `TransactionState` on a `List` element (`TP_ITEMS.items` by `oe_order_item_id`) fails the read outright. You always get the whole window; filter client-side.

*(Section contributed from a community session, Felipe Maurer, 2026; verified against a 26.1 tenant, August 2026 — 102 elements returned for one `Order`, and two `TransactionStates` returning two `Transactions`.)*

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
    "RequestId": "11111111-2222-3333-4444-555555555555",
    "Status": "Active"
}
```

### Check Status

```http
GET /api/v2/transaction/async?id=11111111-2222-3333-4444-555555555555
```

Response:

```json
{
    "RequestId": "11111111-2222-3333-4444-555555555555",
    "Status": "Complete",
    "Messages": "...",
    "CompletedDate": "2025-01-15T16:34:53"
}
```

Status values: `Active`, `Complete`, `Failed`

> **Note:** The async POST returns HTTP **202 Accepted** (not 200) to indicate the request was queued successfully.

**What the immediate response does and does not tell you.** The submit returns in milliseconds with a request ID, and that is an acknowledgement of *queueing only* — not of validation, and not of success. A transaction that the synchronous endpoint would have rejected returns a perfectly normal request ID here. The status GET is where the outcome lives, and it carries the same `Messages` the synchronous call would have returned — a request that failed shows its `Failed` count and the business-rule text (*"You cannot cancel an order that is fully invoiced"*, for instance) only once you go and read it. Treat the request ID as something you must persist and follow up on; work submitted and never checked is work whose outcome nobody knows.

> **There is no cancel.** Once transactions are queued there is no endpoint to stop them — probed on a 26.1 tenant, every cancel-shaped route 404s (`DELETE /api/v2/transaction/async/{id}`, `DELETE /api/v2/transaction/{id}`, `POST /api/v2/transaction/async/cancel`), and `DELETE /api/v2/transaction/async` returns 405: the route exists, for POST only — a loop that submits 50,000 wrong requests will run all 50,000, and every one fires the same DynaChange rules, alerts and event rules a synchronous call would. This is the endpoint's real hazard: it removes the natural backpressure of waiting for each response, so a payload bug that a synchronous run would have surfaced on record one instead surfaces after the whole batch has landed. Validate the payload synchronously against a single record before submitting a batch async. *(Community session, Felipe Maurer, 2026.)*

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

#### The general rule: repeat the element pair, don't batch it

The Transaction API replays a payload the way an operator would work the window: it applies elements top to bottom, and a child element attaches to **whichever parent row is current at that point in the sequence**. So when several parent rows each need child data on another tab, repeat the pair per row rather than sending all the parents and then all the children:

```text
Correct:  item A → its detail A → item B → its detail B
Wrong:    item A → item B → detail A → detail B
```

The second form doesn't error — it applies both details to whatever row was current, which is the last one. Verified on a 26.1 tenant with a two-line order and `TP_EXTDINFO.extd_info`: sending `item A → item B → extd "EXT-FOR-A" → extd "EXT-FOR-B"` returns `Succeeded: 1` with no messages and lands **both** descriptions on line 2, last one winning, leaving line 1's `extended_desc` null. The interleaved sequence puts each description on its own line. An element may appear **as many times as you need** in a single transaction; a ten-line order that also sets extended info per line is ten repetitions of the pair, in order. This is the same rule the lot-item and break-line cases below are specific instances of. *(General statement of the rule: community session, Felipe Maurer, 2026; verified August 2026.)*

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
"""Print a Transaction API service definition -- elements, keys, and field names."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
SERVICE_NAME = "Order"                    # any name from GET /api/v2/services
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

    response = client.get(
        f"{ui_server}/api/v2/definition/{SERVICE_NAME}", headers=headers
    )
    response.raise_for_status()
    definition = response.json()

    # definition["Template"] is a blank payload template for creating records.
    # The elements live under TransactionDefinition.DataElementDefinitions.
    elements = definition["TransactionDefinition"]["DataElementDefinitions"]
    print(f"{SERVICE_NAME}: {len(elements)} DataElements")
    for element in elements:
        print(f"  {element.get('Name')}"
              f"  Type={element.get('Type')}"
              f"  Datawindow={element.get('DatawindowName')}"
              f"  Keys={element.get('KeyFields')}")

    # The API field Name is frequently NOT the underlying column name --
    # DbColumnName is what maps a field back to the table you know.
    first = elements[0]
    print(f"\nFirst 10 fields on {first.get('Name')}:")
    for field in first.get("FieldDefinitions", [])[:10]:
        print(f"  {str(field.get('Name')):<30}"
              f" db={str(field.get('DbColumnName')):<30}"
              f" type={field.get('DataType')} required={field.get('Required')}")
```

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string ServiceName = "Order";                    // any name from GET /api/v2/services
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

var response = await client.GetAsync($"{uiServer}/api/v2/definition/{ServiceName}");
response.EnsureSuccessStatusCode();

using var definition = JsonDocument.Parse(await response.Content.ReadAsStringAsync());

// definition.RootElement.GetProperty("Template") is a blank payload template for
// creating records. The elements live under TransactionDefinition.DataElementDefinitions.
var elements = definition.RootElement
    .GetProperty("TransactionDefinition")
    .GetProperty("DataElementDefinitions");

Console.WriteLine($"{ServiceName}: {elements.GetArrayLength()} DataElements");
foreach (var element in elements.EnumerateArray())
{
    Console.WriteLine(
        $"  {element.GetProperty("Name")}" +
        $"  Type={element.GetProperty("Type")}" +
        $"  Datawindow={element.GetProperty("DatawindowName")}" +
        $"  Keys={element.GetProperty("KeyFields")}");
}

// The API field Name is frequently NOT the underlying column name --
// DbColumnName is what maps a field back to the table you know.
var first = elements[0];
Console.WriteLine($"\nFirst 10 fields on {first.GetProperty("Name")}:");
foreach (var field in first.GetProperty("FieldDefinitions").EnumerateArray().Take(10))
{
    Console.WriteLine(
        $"  {field.GetProperty("Name"),-30}" +
        $" db={field.GetProperty("DbColumnName"),-30}" +
        $" type={field.GetProperty("DataType")} required={field.GetProperty("Required")}");
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
"""Create a sales order, then read the created order back by its order_no."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
CUSTOMER_ID = "100198"                    # customer the order is placed for
SOURCE_LOC_ID = "100"                     # effectively required -- see the gotchas below
SALES_LOC_ID = "100"                      # selling location
ITEM_ID = "WIDGET-001"                    # item on the first line
QUANTITY = "1"                            # unit quantity for that line
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


def walk(node):
    """Yield every {"Name": ..., "Value": ...} pair anywhere in a response."""
    if isinstance(node, dict):
        if "Name" in node and "Value" in node:
            yield node["Name"], node["Value"]
        for value in node.values():
            yield from walk(value)
    elif isinstance(node, list):
        for item in node:
            yield from walk(item)


with httpx.Client(verify=VERIFY_SSL, timeout=120, follow_redirects=True) as client:
    token = get_token(client)
    ui_server = get_ui_server(client, token)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",       # 2026.1 returns an empty 500 without this
        "Content-Type": "application/json",
    }

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
                            {"Name": "customer_id", "Value": CUSTOMER_ID},
                            # Omit source_loc_id and the save fails with a
                            # "Jurisdiction ID for Order Header Tax" error.
                            {"Name": "sales_loc_id", "Value": SALES_LOC_ID},
                            {"Name": "source_loc_id", "Value": SOURCE_LOC_ID},
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
                            {"Name": "oe_order_item_id", "Value": ITEM_ID},
                            {"Name": "unit_quantity", "Value": QUANTITY}
                        ],
                        "RelativeDateEdits": []
                    }]
                }
            ]
        }]
    }

    response = client.post(f"{ui_server}/api/v2/transaction", headers=headers, json=payload)
    response.raise_for_status()          # HTTP 200 does NOT mean the write succeeded
    result = response.json()
    print("Summary:", result.get("Summary"))
    for transaction in result.get("Results", {}).get("Transactions", []):
        print("  Transaction status:", transaction.get("Status"))
    for message in result.get("Messages") or []:
        print("  Message:", message)

    # ---- read-back: the only proof the order landed -------------------------
    # The generated order_no comes back in the result rows.
    order_no = next((value for name, value in walk(result) if name == "order_no"), None)
    print("Created order_no:", order_no)

    if order_no:
        read_back = client.post(
            f"{ui_server}/api/v2/transaction/get",
            headers=headers,
            json={
                "ServiceName": "Order",
                "TransactionStates": [{
                    "DataElementName": "TABPAGE_1.order",   # KeyFields: ["order_no"]
                    "Keys": [{"Name": "order_no", "Value": order_no}],
                }],
            },
        )
        read_back.raise_for_status()

        wanted = {"order_no", "customer_id", "order_date"}
        for name, value in walk(read_back.json()):
            if name in wanted:
                print(f"  {name} = {value}")
```

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string CustomerId = "100198";                    // customer the order is for
const string SourceLocId = "100";                      // effectively required -- see gotchas
const string SalesLocId = "100";                       // selling location
const string ItemId = "WIDGET-001";                    // item on the first line
const string Quantity = "1";                           // unit quantity for that line
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
                            new { Name = "customer_id", Value = CustomerId },
                            // Omit source_loc_id and the save fails with a
                            // "Jurisdiction ID for Order Header Tax" error.
                            new { Name = "sales_loc_id", Value = SalesLocId },
                            new { Name = "source_loc_id", Value = SourceLocId },
                        }}
                    }
                },
                new {
                    Name = "TP_ITEMS.items",
                    Type = "List",
                    Keys = Array.Empty<string>(),
                    Rows = new[] {
                        new { Edits = new[] {
                            new { Name = "oe_order_item_id", Value = ItemId },
                            new { Name = "unit_quantity", Value = Quantity }
                        }}
                    }
                }
            }
        }
    }
};

var response = await client.PostAsync(
    $"{uiServer}/api/v2/transaction",
    new StringContent(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json"));
response.EnsureSuccessStatusCode();     // HTTP 200 does NOT mean the write succeeded

using var result = JsonDocument.Parse(await response.Content.ReadAsStringAsync());
Console.WriteLine($"Summary: {result.RootElement.GetProperty("Summary")}");
if (result.RootElement.TryGetProperty("Results", out var results)
    && results.TryGetProperty("Transactions", out var resultTransactions))
{
    foreach (var transaction in resultTransactions.EnumerateArray())
        Console.WriteLine($"  Transaction status: {transaction.GetProperty("Status")}");
}
if (result.RootElement.TryGetProperty("Messages", out var messages))
{
    foreach (var message in messages.EnumerateArray())
        Console.WriteLine($"  Message: {message}");
}

// ---- read-back: the only proof the order landed ---------------------------
// The generated order_no comes back in the result rows.
string? orderNo = null;
foreach (var (name, value) in Walk(result.RootElement))
{
    if (name == "order_no") { orderNo = value; break; }
}
Console.WriteLine($"Created order_no: {orderNo}");

if (!string.IsNullOrEmpty(orderNo))
{
    var getPayload = new
    {
        ServiceName = "Order",
        TransactionStates = new[]
        {
            new
            {
                DataElementName = "TABPAGE_1.order",     // KeyFields: ["order_no"]
                Keys = new[] { new { Name = "order_no", Value = orderNo } },
            }
        }
    };

    var readBackResponse = await client.PostAsync(
        $"{uiServer}/api/v2/transaction/get",
        new StringContent(JsonSerializer.Serialize(getPayload), Encoding.UTF8, "application/json"));
    readBackResponse.EnsureSuccessStatusCode();

    using var readBack = JsonDocument.Parse(await readBackResponse.Content.ReadAsStringAsync());
    var wanted = new HashSet<string> { "order_no", "customer_id", "order_date" };
    foreach (var (name, value) in Walk(readBack.RootElement))
    {
        if (wanted.Contains(name))
            Console.WriteLine($"  {name} = {value}");
    }
}

// --- helpers ---------------------------------------------------------------

// Yield every {"Name": ..., "Value": ...} pair anywhere in a response.
static IEnumerable<(string Name, string Value)> Walk(JsonElement node)
{
    if (node.ValueKind == JsonValueKind.Object)
    {
        if (node.TryGetProperty("Name", out var name) && node.TryGetProperty("Value", out var value))
            yield return (name.ToString(), value.ToString());
        foreach (var property in node.EnumerateObject())
            foreach (var pair in Walk(property.Value))
                yield return pair;
    }
    else if (node.ValueKind == JsonValueKind.Array)
    {
        foreach (var item in node.EnumerateArray())
            foreach (var pair in Walk(item))
                yield return pair;
    }
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

#### Order Service Gotchas

All verified live (credit: [Alex Westemeier](https://github.com/AWestemeier)):

- **`source_loc_id` is effectively required.** Omitting it fails with a *"Jurisdiction ID for Order Header Tax"* error — the tax jurisdiction does not auto-populate through the API the way it does in the UI. A realistic header sets `customer_id`, `sales_loc_id`, `source_loc_id`, `order_date`, `requested_date`, `po_no`, `taker`, `ship_to_id`, and `contact_id`.
- **`requested_date` must be after `order_date`.** The same date trips a date-cascade prompt, which the stateless API can't answer.
- **`company_id` is a disabled column** on the Order window — don't send it.
- **DynaChange prompts are auto-answered with the default** (usually "No"), which silently discards the affected line — e.g. *"order line does not have a PO Cost… proceed? [No]"*. On multi-item orders the remaining lines then cascade-fail. This is a P21 configuration matter (exempt the rule for the API user, or fix the data), not something a payload change can work around — see [DynaChange and Popup Handling](#dynachange-and-popup-handling).
- **Assembly items cannot be entered via the Transaction API** when they should explode or spawn a production order — the *"add as assembly?"* prompt is auto-answered **No**, killing the explode. Use the Interactive API for those lines: see [Sales Order Entry with Assembly Lines](04-Interactive-API.md#sales-order-entry-with-assembly-lines).
- **The same item on two lines collapses to one** with `Keys: []` — `TP_ITEMS.items` folds rows on its declared key (`oe_order_item_id`), last value wins, `Succeeded: 1`, no warning. Add `Keys: ["unit_quantity"]` (or another differing column) when an order legitimately repeats an item — see [Keys — Row Identity and the Collapse Trap](#keys-row-identity-and-the-collapse-trap).
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
| `contract_no` | Char | **Yes** | Contract number. The definition marks it optional, but a create without it fails: `Required value missing for Contract No (for Job/Contract Hdr) on row 1.` P21 does not assign one on this path — see [Example: Create a Job Contract](#example-create-a-job-contract-with-break-and-non-break-lines) |
| `customer_id` | Decimal | Yes | Customer ID |
| `taker` | Char | No | Order taker / salesperson |
| `end_date` | Datetime | No | Contract end date |
| `corp_address_id` | Long | No | Corporate address ID (read-only after initial save) |
| `ship_to_id` | Long | No | Ship-to address ID |
| `job_no` | Char | No | Associated job number |
| `approved` | Char | No | Approval flag |
| `cancelled` | Char | No | Cancellation flag |
| `consignment_flag` | Char | No | Consignment contract flag |

> **Important:** `corp_address_id` must be set during initial creation — it is read-only once the contract is saved. Verified on 26.1.5910.3 (2026-08-11): changing it on a saved contract fails with `General Exception: Column is disabled: corp_address_id`, and adding `IgnoreDisabled: true` does **not** unlock it — the transaction then reports `Succeeded: 1` while leaving the value untouched (see [entry 8](14-Breaking-Changes.md#8-ignoredisabled-true-reports-success-on-writes-that-write-nothing)).

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

> **Stop before you build a payload around this element.** On P21 26.1 every attempt to write `VALUES.values` through the Transaction API is refused, and `IgnoreDisabled: true` turns that refusal into a silent no-op. Read [VALUES Writes Are Refused on 26.1](#values-writes-are-refused-on-261) first — the field reference below is accurate, but the write path is not currently usable.

| Field | Type | Description |
|-------|------|-------------|
| `calculation_method_cd` | Long | Calculation method (see valid values below). `definitions/JobContractPricing.json` types this **Long**, not Char — with `UseCodeValues: false` you still send the display label |
| `break1` through `break14` | Decimal | Break threshold quantities |
| `calculation_value1` through `calculation_value15` | Decimal | Price/value at each tier |
| `other_cost1` through `other_cost15` | Decimal | Other cost at each tier |

**`calculation_method_cd` valid values:** `Difference`, `Multiplier`, `Mark up`, `Percentage`, `Fixed Price`

> **Every tier field is numbered from 1.** There is no unsuffixed `calculation_value` or `other_cost` — the first tier is `calculation_value1` / `other_cost1`. Verified against `definitions/JobContractPricing.json` (both `FieldDefinitions` and the payload `Template`) and the live `GET /api/v2/definition/JobContractPricing`. The element also has **no per-tier `uom` field** — that is `SalesPricePage`, not this service.

##### Break Tier Structure

The service supports 15 price levels: 14 break thresholds (`break1`-`break14`) plus one catch-all tier. Break values represent the **starting quantity of the next tier** (advance thresholds).

Rules:
- `break1` should NOT be 0 -- it defines where the second tier starts
- The last active tier has its break set to `0`, signaling no further advance
- `calculation_value1` is the first tier; `calculation_value2` through `calculation_value14` are tiers 2-14; `calculation_value15` is the 15th tier, which has no break threshold (there is no `break15`)

**Example -- 3 tiers with Fixed Price method:**

| Tier | Quantity Range | Field | Value | Break Field | Break Value |
|------|---------------|-------|-------|-------------|-------------|
| 1 | 1-9 | `calculation_value1` | `10.00` | `break1` | `10` |
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

##### VALUES Writes Are Refused on 26.1

> **Warning -- verified live on a P21 26.1 tenant, 2026-08-11.** Every write path to `VALUES.values` is refused by the server, and `IgnoreDisabled: true` converts the refusal into a **silent no-op that reports success**. The break-tier documentation above describes the element's real schema; it does not currently describe a working write.

All three paths fail with the same error:

```text
General Exception: Tab page is disabled and cannot be selected
```

which also surfaces per-element as:

```text
VALUES.values: Error processing data element: values : Tab page is disabled and cannot be selected
```

| Path attempted | Result |
|----------------|--------|
| Update `VALUES` on a line of an **existing** contract | Refused |
| Insert a new line (keyed upsert on `item_id`) onto an existing contract, with `VALUES` in the same transaction | Refused — **atomically**; the line is not created either |
| Create a brand-new contract (header + fully specified `Source` line + `VALUES`) in one transaction | Refused — **atomically**; the contract is not created either |

**The control, so you can size the damage.** The identical create transaction with the `VALUES.values` DataElement **removed** succeeds: `Summary: {"Succeeded": 1}`, the contract is created, the `Source`-priced line is created, both confirmed by read-back. Contract and line creation through the Transaction API work fine. It is specifically the `VALUES.values` DataElement that is refused.

Other things checked, all on the same tenant:

- **Resending the line's `pricing_method` / `source_price` / `multiplier`** in the same transaction — an attempt to make the window "select" the tab the way a user would — does **not** help. Identical failure.
- **Both `calculation_value` and `calculation_value1` fail identically**, so this is not a field-naming problem. (`calculation_value1` is nonetheless the correct name — see [above](#break-tier-structure).)
- **`IgnoreDisabled: true` at payload top level makes it worse.** The response flips to `Summary: {"Failed": 0, "Succeeded": 1}` with `Status: "Passed"` — and **nothing is written**. Read-back shows the row unchanged (an existing tier value of `42.50` survived a `"Passed"` response) or still absent. The echoed response also **silently drops the `JOBPRICELINE` and `VALUES` DataElements**, echoing only the header, so even the echo does not reveal the omission.

**Whether this is a 26.1 regression or long-standing behavior is unknown** — no earlier build was available to compare against. Do not read it as a regression; read it as the behavior of the build in front of you, and re-test on yours.

**Takeaway beyond this element:** `IgnoreDisabled: true` is not a universal unlock. It genuinely unlocks some disabled columns and tabs (see [IgnoreDisabled](#ignoredisabled)), but on this path it only converts a loud failure into a quiet one. **Always read back after a write that used it** — via `POST /api/v2/transaction/get` or OData — rather than trusting `Succeeded`.

#### Commission Costs

The `JOBPRICECOST` DataElement includes `commission_cost_value` and related commission fields. These columns are **disabled by default** -- without special handling the API returns "Column is disabled: commission_cost_value".

**They are writable with `IgnoreDisabled: true`** at the payload top level (see [IgnoreDisabled](#ignoredisabled)). Key the element by `item_id` and set the cost type before the value -- verified live, including in the same transaction as a line insert:

> Payload shape only -- drop this DataElement into a full program. Full runnable version: [Updating an Existing Contract](#updating-an-existing-contract).

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

`commission_cost_type_cd` accepts the display labels `Order`, `Source`, `Value`, `None` (with `UseCodeValues: false`). Setting only the commission cost leaves the element's `other_cost_*` fields (`other_cost_type_cd`, `other_cost_value`, `other_cost_source_cd`, `other_cost_calc_method_cd`, `other_cost_calc_value`) untouched.

> **Credit:** [Alex Westemeier](https://github.com/AWestemeier) verified the `IgnoreDisabled` commission-cost write path. The Interactive API (JobContractPricing window) remains an alternative.

#### Updating an Existing Contract

Use `Status = "New"` to update existing contracts -- there is no separate "Update" or "Existing" status. The Transaction API distinguishes create from update by whether the FORM key fields land on an existing record:

- Leave the FORM `Keys` array empty.
- Send the FORM key fields (`company_id`, `contract_no`, `job_no`) inside `Edits`.
- Also include `end_date` in `Edits` -- the API validates required fields on every submit and rejects with `"Required value missing for End Date"` if it's absent.
- On `JOBPRICELINE`, set `Keys: ["item_id"]` and put the `item_id` value in `Edits` alongside the fields you're changing.

> Empirically verified 2026-05-14: 173 successful price updates against contract `JOB-1001` on a production tenant. Each call returned HTTP 200 with `Summary.Succeeded = 1`, and OData confirmed each `job_price_line.price` matched the submitted value.

**Example -- update one line's price:**

<!-- tabs -->
```python
"""Update one line's price on an existing job contract, then read it back."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
COMPANY_ID = "ACME"                       # FORM key fields go in Edits, not Keys
CONTRACT_NO = "JOB-1001"
JOB_NO = "31"                             # unique per header; survives renewals
END_DATE = "2030-01-01"                   # must be >= today -- validated every save
ITEM_ID = "WIDGET-001"                    # the line to update
UOM = "EA"
PRICE = "36.58"
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


def walk(node):
    """Yield every {"Name": ..., "Value": ...} pair anywhere in a response."""
    if isinstance(node, dict):
        if "Name" in node and "Value" in node:
            yield node["Name"], node["Value"]
        for value in node.values():
            yield from walk(value)
    elif isinstance(node, list):
        for item in node:
            yield from walk(item)


with httpx.Client(verify=VERIFY_SSL, timeout=120, follow_redirects=True) as client:
    token = get_token(client)
    ui_server = get_ui_server(client, token)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",       # 2026.1 returns an empty 500 without this
        "Content-Type": "application/json",
    }

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
                            {"Name": "company_id",  "Value": COMPANY_ID},
                            {"Name": "contract_no", "Value": CONTRACT_NO},
                            {"Name": "job_no",      "Value": JOB_NO},
                            {"Name": "end_date",    "Value": END_DATE},
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
                            # pricing_method BEFORE price -- reversing them zeroes the price
                            {"Name": "item_id",        "Value": ITEM_ID},
                            {"Name": "uom",            "Value": UOM},
                            {"Name": "pricing_method", "Value": "Price"},
                            {"Name": "price",          "Value": PRICE},
                        ],
                        "RelativeDateEdits": [],
                    }],
                },
            ],
        }],
    }

    response = client.post(f"{ui_server}/api/v2/transaction", headers=headers, json=payload)
    response.raise_for_status()          # HTTP 200 does NOT mean the write succeeded
    result = response.json()
    print("Summary:", result.get("Summary"))
    for transaction in result.get("Results", {}).get("Transactions", []):
        print("  Transaction status:", transaction.get("Status"))
    for message in result.get("Messages") or []:
        print("  Message:", message)

    # ---- read-back: the only proof the price landed -------------------------
    read_back = client.post(
        f"{ui_server}/api/v2/transaction/get",
        headers=headers,
        json={
            "ServiceName": "JobContractPricing",
            "TransactionStates": [
                {
                    "DataElementName": "FORM.d_dw_job_price_hdr",
                    "Keys": [{"Name": "contract_no", "Value": CONTRACT_NO}],
                },
                {"DataElementName": "JOBPRICELINE.jobpriceline", "Keys": []},
            ],
        },
    )
    read_back.raise_for_status()

    wanted = {"contract_no", "job_no", "item_id", "pricing_method", "price"}
    for name, value in walk(read_back.json()):
        if name in wanted:
            print(f"  {name} = {value}")
```

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string CompanyId = "ACME";              // FORM key fields go in Edits, not Keys
const string ContractNo = "JOB-1001";
const string JobNo = "31";                    // unique per header; survives renewals
const string EndDate = "2030-01-01";          // must be >= today -- validated every save
const string ItemId = "WIDGET-001";           // the line to update
const string Uom = "EA";
const string Price = "36.58";
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

var payload = new
{
    Name = "JobContractPricing",
    UseCodeValues = false,
    Transactions = new[]
    {
        new
        {
            Status = "New",                          // still "New" for updates
            DataElements = new object[]
            {
                new
                {
                    Name = "FORM.d_dw_job_price_hdr",
                    Type = "Form",
                    Keys = Array.Empty<string>(),     // empty
                    Rows = new[]
                    {
                        new
                        {
                            Edits = new[]
                            {
                                new { Name = "company_id", Value = CompanyId },
                                new { Name = "contract_no", Value = ContractNo },
                                new { Name = "job_no", Value = JobNo },
                                new { Name = "end_date", Value = EndDate },
                            },
                            RelativeDateEdits = Array.Empty<object>(),
                        }
                    }
                },
                new
                {
                    Name = "JOBPRICELINE.jobpriceline",
                    Type = "List",
                    Keys = new[] { "item_id" },
                    Rows = new[]
                    {
                        new
                        {
                            Edits = new[]
                            {
                                // pricing_method BEFORE price -- reversing them zeroes the price
                                new { Name = "item_id", Value = ItemId },
                                new { Name = "uom", Value = Uom },
                                new { Name = "pricing_method", Value = "Price" },
                                new { Name = "price", Value = Price },
                            },
                            RelativeDateEdits = Array.Empty<object>(),
                        }
                    }
                }
            }
        }
    }
};

var response = await client.PostAsync(
    $"{uiServer}/api/v2/transaction",
    new StringContent(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json"));
response.EnsureSuccessStatusCode();     // HTTP 200 does NOT mean the write succeeded

using var result = JsonDocument.Parse(await response.Content.ReadAsStringAsync());
Console.WriteLine($"Summary: {result.RootElement.GetProperty("Summary")}");
if (result.RootElement.TryGetProperty("Results", out var results)
    && results.TryGetProperty("Transactions", out var resultTransactions))
{
    foreach (var transaction in resultTransactions.EnumerateArray())
        Console.WriteLine($"  Transaction status: {transaction.GetProperty("Status")}");
}
if (result.RootElement.TryGetProperty("Messages", out var messages))
{
    foreach (var message in messages.EnumerateArray())
        Console.WriteLine($"  Message: {message}");
}

// ---- read-back: the only proof the price landed ---------------------------
var getPayload = new
{
    ServiceName = "JobContractPricing",
    TransactionStates = new object[]
    {
        new
        {
            DataElementName = "FORM.d_dw_job_price_hdr",
            Keys = new[] { new { Name = "contract_no", Value = ContractNo } },
        },
        new { DataElementName = "JOBPRICELINE.jobpriceline", Keys = Array.Empty<object>() },
    }
};

var readBackResponse = await client.PostAsync(
    $"{uiServer}/api/v2/transaction/get",
    new StringContent(JsonSerializer.Serialize(getPayload), Encoding.UTF8, "application/json"));
readBackResponse.EnsureSuccessStatusCode();

using var readBack = JsonDocument.Parse(await readBackResponse.Content.ReadAsStringAsync());
var wanted = new HashSet<string>
{
    "contract_no", "job_no", "item_id", "pricing_method", "price"
};
foreach (var (name, value) in Walk(readBack.RootElement))
{
    if (wanted.Contains(name))
        Console.WriteLine($"  {name} = {value}");
}

// --- helpers ---------------------------------------------------------------

// Yield every {"Name": ..., "Value": ...} pair anywhere in a response.
static IEnumerable<(string Name, string Value)> Walk(JsonElement node)
{
    if (node.ValueKind == JsonValueKind.Object)
    {
        if (node.TryGetProperty("Name", out var name) && node.TryGetProperty("Value", out var value))
            yield return (name.ToString(), value.ToString());
        foreach (var property in node.EnumerateObject())
            foreach (var pair in Walk(property.Value))
                yield return pair;
    }
    else if (node.ValueKind == JsonValueKind.Array)
    {
        foreach (var item in node.EnumerateArray())
            foreach (var pair in Walk(item))
                yield return pair;
    }
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

**Notes:**

- **Converting `pricing_method` from `"Source"` to `"Price"`** works in the same call. The previously-set `source_price` and `multiplier` are NOT auto-cleared on the row, but become dormant since the `"Price"` method only reads `price`.
- **Use `POST /api/v2/transaction/get`** to retrieve the existing FORM values (`company_id`, `job_no`, `end_date`) before submitting the update:

  ```json
  {
    "ServiceName": "JobContractPricing",
    "TransactionStates": [{
      "DataElementName": "FORM.d_dw_job_price_hdr",
      "Keys": [{"Name": "contract_no", "Value": "JOB-1001"}]
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

> Payload shape only. Full runnable version -- same POST, same response checks: [Updating an Existing Contract](#updating-an-existing-contract).

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

> **This example cannot succeed on P21 26.1.** It sends a `VALUES.values` DataElement, and every write to that element is refused — atomically, so the transaction creates **no contract and no lines**. See [VALUES Writes Are Refused on 26.1](#values-writes-are-refused-on-261). The example is kept because it is the correct payload *shape* (header → line → its VALUES, interleaved per break line) and because the same transaction **with the `VALUES.values` element deleted** does succeed. Delete DataElement 4 to get a runnable version.

Separately -- and unrelated to that hazard -- two ordinary validation requirements that this example originally got wrong, both verified on 26.1:

- **`contract_no` is required on the header.** A header submitted without it fails with `Required value missing for Contract No (for Job/Contract Hdr) on row 1.` P21 does not assign the number for you on this path, so it is included in the payload below. Reading `contract_no` back out of the response (as the code at the end of each tab does) is only meaningful as a confirmation of the number **you** supplied.
- **A contract cannot be created as a bare header.** The transaction must include a fully specified line, `uom` included; a header sent with no line element at all fails with `Required value missing for Uom (for Job/Contract Line) on row 1.` You cannot create the header first and add lines in a later call.

<!-- tabs -->
```python
"""Create a job contract with a fixed-price line and a break line (VALUES refused on 26.1)."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
COMPANY_ID = "ACME"
CONTRACT_NO = "JOB-1001"                  # required -- P21 does not assign it here
CUSTOMER_ID = "100198"
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


def walk(node):
    """Yield every {"Name": ..., "Value": ...} pair anywhere in a response."""
    if isinstance(node, dict):
        if "Name" in node and "Value" in node:
            yield node["Name"], node["Value"]
        for value in node.values():
            yield from walk(value)
    elif isinstance(node, list):
        for item in node:
            yield from walk(item)


with httpx.Client(verify=VERIFY_SSL, timeout=120, follow_redirects=True) as client:
    token = get_token(client)
    ui_server = get_ui_server(client, token)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",       # 2026.1 returns an empty 500 without this
        "Content-Type": "application/json",
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
                            {"Name": "company_id", "Value": COMPANY_ID},
                            {"Name": "contract_no", "Value": CONTRACT_NO},   # required
                            {"Name": "customer_id", "Value": CUSTOMER_ID},
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
                # 4. Break tiers for WIDGET-002 (must follow its JOBPRICELINE).
                #    DELETE THIS ELEMENT to get a version that succeeds on 26.1.
                {
                    "Name": "VALUES.values",
                    "Type": "Form",
                    "Keys": [],
                    "Rows": [{
                        "Edits": [
                            {"Name": "calculation_method_cd", "Value": "Fixed Price"},
                            # Tier 1: qty 1-9 @ $10.00
                            {"Name": "calculation_value1", "Value": "10.00"},
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

    response = client.post(f"{ui_server}/api/v2/transaction", headers=headers, json=payload)
    response.raise_for_status()          # HTTP 200 does NOT mean the write succeeded
    result = response.json()
    print("Summary:", result.get("Summary"))
    for transaction in result.get("Results", {}).get("Transactions", []):
        print("  Transaction status:", transaction.get("Status"))
    for message in result.get("Messages") or []:
        print("  Message:", message)

    if (result.get("Summary") or {}).get("Succeeded", 0) > 0:
        txn = result["Results"]["Transactions"][0]
        for edit in txn["DataElements"][0]["Rows"][0]["Edits"]:
            if edit["Name"] == "contract_no":
                # Only a confirmation of the number YOU supplied above.
                print(f"Contract #: {edit['Value']}")
                break

    # ---- read-back: on 26.1 this prints nothing -- the VALUES refusal is
    # atomic, so no contract and no lines were created.
    read_back = client.post(
        f"{ui_server}/api/v2/transaction/get",
        headers=headers,
        json={
            "ServiceName": "JobContractPricing",
            "TransactionStates": [{
                "DataElementName": "FORM.d_dw_job_price_hdr",
                "Keys": [{"Name": "contract_no", "Value": CONTRACT_NO}],
            }],
        },
    )
    read_back.raise_for_status()

    wanted = {"contract_no", "job_no", "customer_id", "end_date"}
    for name, value in walk(read_back.json()):
        if name in wanted:
            print(f"  {name} = {value}")
```

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string CompanyId = "ACME";
const string ContractNo = "JOB-1001";       // required -- P21 does not assign it here
const string CustomerId = "100198";
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

// Create a contract with one fixed-price line and one break line
var payload = new
{
    Name = "JobContractPricing",
    UseCodeValues = false,
    Transactions = new[]
    {
        new
        {
            Status = "New",
            DataElements = new object[]
            {
                // 1. Contract header
                new
                {
                    Name = "FORM.d_dw_job_price_hdr",
                    Type = "Form",
                    Keys = Array.Empty<string>(),
                    Rows = new[]
                    {
                        new
                        {
                            Edits = new[]
                            {
                                new { Name = "company_id", Value = CompanyId },
                                new { Name = "contract_no", Value = ContractNo },
                                new { Name = "customer_id", Value = CustomerId },
                                new { Name = "corp_address_id", Value = "1" },
                                new { Name = "end_date", Value = "2027-12-31" },
                                new { Name = "approved", Value = "ON" },
                            },
                            RelativeDateEdits = Array.Empty<object>(),
                        }
                    }
                },
                // 2. Fixed-price line (no breaks)
                new
                {
                    Name = "JOBPRICELINE.jobpriceline",
                    Type = "List",
                    Keys = new[] { "item_id" },
                    Rows = new[]
                    {
                        new
                        {
                            Edits = new[]
                            {
                                new { Name = "item_id", Value = "WIDGET-001" },
                                new { Name = "uom", Value = "EA" },
                                new { Name = "pricing_method", Value = "Price" },
                                new { Name = "price", Value = "25.00" },
                            },
                            RelativeDateEdits = Array.Empty<object>(),
                        }
                    }
                },
                // 3. Break line -- JOBPRICELINE (1 row)
                new
                {
                    Name = "JOBPRICELINE.jobpriceline",
                    Type = "List",
                    Keys = new[] { "item_id" },
                    Rows = new[]
                    {
                        new
                        {
                            Edits = new[]
                            {
                                new { Name = "item_id", Value = "WIDGET-002" },
                                new { Name = "uom", Value = "EA" },
                                new { Name = "pricing_method", Value = "Source" },
                                new { Name = "source_price", Value = "Supplier List Price" },
                                new { Name = "multiplier", Value = "1" },
                            },
                            RelativeDateEdits = Array.Empty<object>(),
                        }
                    }
                },
                // 4. Break tiers for WIDGET-002 (must follow its JOBPRICELINE).
                //    DELETE THIS ELEMENT to get a version that succeeds on 26.1.
                new
                {
                    Name = "VALUES.values",
                    Type = "Form",
                    Keys = Array.Empty<string>(),
                    Rows = new[]
                    {
                        new
                        {
                            Edits = new[]
                            {
                                new { Name = "calculation_method_cd", Value = "Fixed Price" },
                                // Tier 1: qty 1-9 @ $10.00
                                new { Name = "calculation_value1", Value = "10.00" },
                                new { Name = "break1", Value = "10" },
                                // Tier 2: qty 10-49 @ $8.50
                                new { Name = "calculation_value2", Value = "8.50" },
                                new { Name = "break2", Value = "50" },
                                // Tier 3: qty 50+ @ $7.00
                                new { Name = "calculation_value3", Value = "7.00" },
                                new { Name = "break3", Value = "0" },
                            },
                            RelativeDateEdits = Array.Empty<object>(),
                        }
                    }
                }
            }
        }
    }
};

var response = await client.PostAsync(
    $"{uiServer}/api/v2/transaction",
    new StringContent(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json"));
response.EnsureSuccessStatusCode();     // HTTP 200 does NOT mean the write succeeded

using var result = JsonDocument.Parse(await response.Content.ReadAsStringAsync());
Console.WriteLine($"Summary: {result.RootElement.GetProperty("Summary")}");
if (result.RootElement.TryGetProperty("Results", out var results)
    && results.TryGetProperty("Transactions", out var resultTransactions))
{
    foreach (var transaction in resultTransactions.EnumerateArray())
        Console.WriteLine($"  Transaction status: {transaction.GetProperty("Status")}");

    if (result.RootElement.GetProperty("Summary").GetProperty("Succeeded").GetInt32() > 0)
    {
        var edits = resultTransactions[0]
            .GetProperty("DataElements")[0]
            .GetProperty("Rows")[0]
            .GetProperty("Edits");
        foreach (var edit in edits.EnumerateArray())
        {
            if (edit.GetProperty("Name").GetString() == "contract_no")
            {
                // Only a confirmation of the number YOU supplied above.
                Console.WriteLine($"Contract #: {edit.GetProperty("Value")}");
                break;
            }
        }
    }
}
if (result.RootElement.TryGetProperty("Messages", out var messages))
{
    foreach (var message in messages.EnumerateArray())
        Console.WriteLine($"  Message: {message}");
}

// ---- read-back: on 26.1 this prints nothing -- the VALUES refusal is
// atomic, so no contract and no lines were created.
var getPayload = new
{
    ServiceName = "JobContractPricing",
    TransactionStates = new[]
    {
        new
        {
            DataElementName = "FORM.d_dw_job_price_hdr",
            Keys = new[] { new { Name = "contract_no", Value = ContractNo } },
        }
    }
};

var readBackResponse = await client.PostAsync(
    $"{uiServer}/api/v2/transaction/get",
    new StringContent(JsonSerializer.Serialize(getPayload), Encoding.UTF8, "application/json"));
readBackResponse.EnsureSuccessStatusCode();

using var readBack = JsonDocument.Parse(await readBackResponse.Content.ReadAsStringAsync());
var wanted = new HashSet<string> { "contract_no", "job_no", "customer_id", "end_date" };
foreach (var (name, value) in Walk(readBack.RootElement))
{
    if (wanted.Contains(name))
        Console.WriteLine($"  {name} = {value}");
}

// --- helpers ---------------------------------------------------------------

// Yield every {"Name": ..., "Value": ...} pair anywhere in a response.
static IEnumerable<(string Name, string Value)> Walk(JsonElement node)
{
    if (node.ValueKind == JsonValueKind.Object)
    {
        if (node.TryGetProperty("Name", out var name) && node.TryGetProperty("Value", out var value))
            yield return (name.ToString(), value.ToString());
        foreach (var property in node.EnumerateObject())
            foreach (var pair in Walk(property.Value))
                yield return pair;
    }
    else if (node.ValueKind == JsonValueKind.Array)
    {
        foreach (var item in node.EnumerateArray())
            foreach (var pair in Walk(item))
                yield return pair;
    }
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
"""Create an assembly/BOM definition on an existing inventory item, then read it back."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
ITEM_ID = "WIDGET-001"                    # must ALREADY exist in inventory
COMPONENT_A = "COMPONENT-A"               # component items, also pre-existing
COMPONENT_B = "COMPONENT-B"
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


def walk(node):
    """Yield every {"Name": ..., "Value": ...} pair anywhere in a response."""
    if isinstance(node, dict):
        if "Name" in node and "Value" in node:
            yield node["Name"], node["Value"]
        for value in node.values():
            yield from walk(value)
    elif isinstance(node, list):
        for item in node:
            yield from walk(item)


with httpx.Client(verify=VERIFY_SSL, timeout=120, follow_redirects=True) as client:
    token = get_token(client)
    ui_server = get_ui_server(client, token)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",       # 2026.1 returns an empty 500 without this
        "Content-Type": "application/json",
    }

    # Create assembly definition for an existing item.
    # The Assembly service does NOT create the inventory item itself.
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
                            {"Name": "inv_mast_item_id", "Value": ITEM_ID},
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
                                    "Value": COMPONENT_A,
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
                                    "Value": COMPONENT_B,
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

    response = client.post(f"{ui_server}/api/v2/transaction", headers=headers, json=payload)
    response.raise_for_status()          # HTTP 200 does NOT mean the write succeeded
    result = response.json()
    print("Summary:", result.get("Summary"))
    for transaction in result.get("Results", {}).get("Transactions", []):
        print("  Transaction status:", transaction.get("Status"))
    for message in result.get("Messages") or []:
        print("  Message:", message)

    # ---- read-back: the only proof the definition landed --------------------
    read_back = client.post(
        f"{ui_server}/api/v2/transaction/get",
        headers=headers,
        json={
            "ServiceName": "Assembly",
            "TransactionStates": [
                {
                    "DataElementName": "TABPAGE_1.assemblyhdr",  # Keys: inv_mast_item_id
                    "Keys": [{"Name": "inv_mast_item_id", "Value": ITEM_ID}],
                },
                {"DataElementName": "TABPAGE_17.tp_17_dw_17", "Keys": []},
            ],
        },
    )
    read_back.raise_for_status()

    wanted = {"inv_mast_item_id", "allow_disassembly",
              "item_id_service_labor_id", "quantity"}
    for name, value in walk(read_back.json()):
        if name in wanted:
            print(f"  {name} = {value}")
```

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string ItemId = "WIDGET-001";                    // must ALREADY exist in inventory
const string ComponentA = "COMPONENT-A";               // components, also pre-existing
const string ComponentB = "COMPONENT-B";
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

// Create assembly definition for an existing item.
// The Assembly service does NOT create the inventory item itself.
var payload = new
{
    Name = "Assembly",
    UseCodeValues = false,
    Transactions = new[]
    {
        new
        {
            Status = "New",
            DataElements = new object[]
            {
                // Assembly header
                new
                {
                    Name = "TABPAGE_1.assemblyhdr",
                    Type = "Form",
                    Keys = new[] { "inv_mast_item_id" },
                    Rows = new[]
                    {
                        new
                        {
                            Edits = new[]
                            {
                                new { Name = "inv_mast_item_id", Value = ItemId },
                                new { Name = "allow_disassembly", Value = "ON" },
                            },
                            RelativeDateEdits = Array.Empty<object>(),
                        }
                    }
                },
                // BOM components
                new
                {
                    Name = "TABPAGE_17.tp_17_dw_17",
                    Type = "List",
                    Keys = new[] { "item_id_service_labor_id" },
                    Rows = new[]
                    {
                        new
                        {
                            Edits = new[]
                            {
                                new { Name = "item_id_service_labor_id", Value = ComponentA },
                                new { Name = "quantity", Value = "2" },
                                new { Name = "operation_cd", Value = "ASSY" },
                            },
                            RelativeDateEdits = Array.Empty<object>(),
                        },
                        new
                        {
                            Edits = new[]
                            {
                                new { Name = "item_id_service_labor_id", Value = ComponentB },
                                new { Name = "quantity", Value = "1" },
                                new { Name = "operation_cd", Value = "ASSY" },
                            },
                            RelativeDateEdits = Array.Empty<object>(),
                        }
                    }
                }
            }
        }
    }
};

var response = await client.PostAsync(
    $"{uiServer}/api/v2/transaction",
    new StringContent(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json"));
response.EnsureSuccessStatusCode();     // HTTP 200 does NOT mean the write succeeded

using var result = JsonDocument.Parse(await response.Content.ReadAsStringAsync());
Console.WriteLine($"Summary: {result.RootElement.GetProperty("Summary")}");
if (result.RootElement.TryGetProperty("Results", out var results)
    && results.TryGetProperty("Transactions", out var resultTransactions))
{
    foreach (var transaction in resultTransactions.EnumerateArray())
        Console.WriteLine($"  Transaction status: {transaction.GetProperty("Status")}");
}
if (result.RootElement.TryGetProperty("Messages", out var messages))
{
    foreach (var message in messages.EnumerateArray())
        Console.WriteLine($"  Message: {message}");
}

// ---- read-back: the only proof the definition landed ----------------------
var getPayload = new
{
    ServiceName = "Assembly",
    TransactionStates = new object[]
    {
        new
        {
            DataElementName = "TABPAGE_1.assemblyhdr",       // Keys: inv_mast_item_id
            Keys = new[] { new { Name = "inv_mast_item_id", Value = ItemId } },
        },
        new { DataElementName = "TABPAGE_17.tp_17_dw_17", Keys = Array.Empty<object>() },
    }
};

var readBackResponse = await client.PostAsync(
    $"{uiServer}/api/v2/transaction/get",
    new StringContent(JsonSerializer.Serialize(getPayload), Encoding.UTF8, "application/json"));
readBackResponse.EnsureSuccessStatusCode();

using var readBack = JsonDocument.Parse(await readBackResponse.Content.ReadAsStringAsync());
var wanted = new HashSet<string>
{
    "inv_mast_item_id", "allow_disassembly", "item_id_service_labor_id", "quantity"
};
foreach (var (name, value) in Walk(readBack.RootElement))
{
    if (wanted.Contains(name))
        Console.WriteLine($"  {name} = {value}");
}

// --- helpers ---------------------------------------------------------------

// Yield every {"Name": ..., "Value": ...} pair anywhere in a response.
static IEnumerable<(string Name, string Value)> Walk(JsonElement node)
{
    if (node.ValueKind == JsonValueKind.Object)
    {
        if (node.TryGetProperty("Name", out var name) && node.TryGetProperty("Value", out var value))
            yield return (name.ToString(), value.ToString());
        foreach (var property in node.EnumerateObject())
            foreach (var pair in Walk(property.Value))
                yield return pair;
    }
    else if (node.ValueKind == JsonValueKind.Array)
    {
        foreach (var item in node.EnumerateArray())
            foreach (var pair in Walk(item))
                yield return pair;
    }
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

### Item Service -- Nested Location Edits

The `Item` service (Item Maintenance window) supports **nested DataElement navigation** that mirrors the UI: select the item, select a location row, then edit that location's detail. This is the Transaction-API equivalent of "select parent row → edit child detail," and it works because the Item window's tabs aren't gated behind row selection. It's a good template for any nested edit.

> The two payloads below are shapes, not programs -- swap either into the `payload` of a complete example. Full runnable version: [Create Order](#create-order).

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
      {"Name": "supplier_id", "Value": "10050"},
      {"Name": "primary_supplier", "Value": "ON"}
  ] }] }
```

What this writes, and the cascade (verified on a 68-item production run):

- `primary_supplier` maps to `inventory_supplier_x_loc.primary_supplier` (a Y/N flag) — **not** `inv_loc.primary_supplier_id`.
- Setting it `ON` makes P21 auto-unset the previous primary at that location **and** update `inv_loc.primary_supplier_id` to the new supplier. So the flag is the field to **write**; `inv_loc.primary_supplier_id` is the field to **read** when verifying.

#### Item Service Gotchas

- **Silent no-op — the big one.** The target supplier must already have a *location-level* row (`inventory_supplier_x_loc`) at that location. If it doesn't, the transaction still returns `Succeeded = 1` but **nothing flips** — there is no row to promote. (P21 allows cutting a PO to a supplier without location setup, so a supplier can appear in PO history yet be absent from the location's supplier list.) **Always verify `inv_loc.primary_supplier_id` after writing** — do not trust `Succeeded`. Fix: add the location supplier row first, then set the flag.
- **"Item Issues Detected" popup — a data defect you can fix, not an API limitation.** Affected items return an `Unexpected response window: Item Issues Detected` (`w_rule_callback_response`) in the response `Messages`. The Transaction API cannot answer the popup, so the transaction aborts and the edit is discarded. The popup comes from a **site-configured DynaChange business rule with `apply_during_save_flag = 'Y'`**, which fires on *every* save of the Item window — so it blocks **all** Item-service writes, not just `product_group_id` changes. The behavior is **deterministic, not per-run session state**: retries fail every time until the underlying data is corrected, and once it is corrected the identical transaction succeeds. Identify the rule and its trigger, fix the data, re-run — see [Item Issues Detected Popup Root Cause and Data Fix](#item-issues-detected-popup-root-cause-and-data-fix). For items you cannot data-fix, fall back to the Interactive API and answer the popup with `cb_1` ("Yes, Proceed Anyway") — see [Item window popups](04-Interactive-API.md#worked-example-item-issues-detected-rule-callback).
- **Uppercase your `item_id` yourself — the API will not.** The P21 client folds a typed item ID to uppercase before it saves, so lowercase item IDs cannot be created through the UI. **The Transaction API applies no such conversion**: a lowercase `item_id` is accepted and the item is created successfully. The resulting record is then effectively unusable — opening it in **Item Maintenance / Item Master Inquiry crashes the client** (reported by maintainers as crashing the browser in the web client), and it is not clear that item-repair tooling detects it. Normalize `item_id` to uppercase in your own code before every create; there is no API-side guard. This is the one place where the Transaction API is known to accept input the application itself would reject. *(Community session, Felipe Maurer, 2026; independently confirmed from production experience. Deliberately **not** re-tested for this documentation — the item it creates cannot be cleaned up through the UI, so do not reproduce it to check, on production or anywhere else.)*
- `SUPPLIER_X_LOCATION` is keyed by `supplier_id` scoped to the selected location row in the Transaction API, so the nested pattern is safe here. (The equivalent *interactive* flow must match rows on both `location_id` and `supplier_id` — the grid holds every location's rows.)

> **Credit:** [Alex Westemeier](https://github.com/AWestemeier) — patterns and gotchas verified in production (July 2026).

### BinLocation Service -- Creating Bins

The `BinLocation` service *is* the **Bin Location Maintenance** window: its form element `FORM.form` is business object `bin` (datawindow `d_dw_bin_form`), and every field in the payload is a real field on that screen. Bulk bin creation is a clean Transaction API use case — verified in production at hundreds of bins per run.

> Payload shape only. Full runnable version -- same endpoint and response checks: [Create Order](#create-order). A complete bin-creation walkthrough lives in [recipes/create-bins.md](recipes/create-bins.md).

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

### Shipping Service -- Carrier Tracking Number

**`Shipping` is the only service that writes `oe_pick_ticket.tracking_no`.** A scan of all **299** services returned by `GET /api/v2/services` (240 returned a definition; the rest answer with the unavailable-window HTTP 500) found the column in exactly one writable place. *Verified on a P21 26.1 tenant, 2026-08-11.*

#### The element

| Property | Value |
|----------|-------|
| DataElement | `TABPAGE_1.tp_1_dw_1` |
| BusinessObjectName | `oe_pick_ticket` |
| DatawindowName | `d_ship` |
| KeyFields | `['pick_ticket_no']` |

| Field | DataType | Label | Notes |
|-------|----------|-------|-------|
| `tracking_no` | Char | Carrier Tracking Number | Writes `oe_pick_ticket.tracking_no` |
| `carrier_id` | Decimal | Carrier | Carries `ValidValues` — with `UseCodeValues: false` you send the carrier's **display name**, not the id |
| `create_invoice` | Char | Confirm Shipment | `ValidValues`: `ON` / `OFF` |

#### The limitation: invoiced pick tickets refuse the write

Once the pick ticket has been **invoiced**, the write is refused:

```text
Summary: {"Failed": 1, "Succeeded": 0}
General Exception: This pick ticket has already been invoiced.
```

The error is attributed to `DataElement: tp_1_dw_1, Column: pick_ticket_no` — **not** to `tracking_no`. That attribution is the tell: the gate fires at **record selection**, before any field-level validation, so **there is no edit you can drop from the payload to get past it.** Sending `tracking_no` alone fails exactly the same way.

#### Other services expose a tracking column, but none writes this one

Each of these writes a *different* column — none of them reaches `oe_pick_ticket.tracking_no`:

- **`Shipping`** — `tracking_no` on `TP_SCANPACK.scan_pack_container_hdr`, which is the scan-pack container's own number (`scan_pack_container_hdr.tracking_no`), not the pick ticket's.
- **`Order`, `FrontCounter`, `RMA`, `ServiceOrder`, `ServiceOrderRMA`, `ConsignmentReplenishmentOrder`** — `c_tracking_no` on `TP_SHIPMENTS.tp_shipments` and `TABPAGE_LINESHIPMENT.tabpage_lineshipment`. **Computed and disabled** — a display of the pick ticket's value, not a write path.
- **`DirectShipConfirmation`** — `tracking_no` on `TABPAGE_1.tp_1_dw_po`, also backed by the computed `c_tracking_no`.
- **`Transfer`, `TransferShipping`** — `carrier_tracking_no` on `ITEM_SHIPMENTS.item_shipments`, `SHIPMENTS.shipments` and `TABPAGE_1.tp_1_dw_1`, writing `transfer_shipment_hdr.carrier_tracking_no` — the *transfer's* tracking number.
- **`ProcessPOShipping`** — `tracking_number` on `FORM.form`, writing `process_po_shipment_hdr.tracking_number`.

#### The Order shipment grids are not a post-invoice back door

They look like one — both are keyed grids on the `Order` service that survive invoicing:

- `TABPAGE_LINESHIPMENT.tabpage_lineshipment` — List, `d_oe_line_pick_tickets`, KeyFields `['invoice_no']`
- `TP_SHIPMENTS.tp_shipments` — List, `d_dw_pick_ticket_oe`, KeyFields `[]`

Editing `c_tracking_no` on either returns `General Exception: Column is disabled: c_tracking_no`. It is a **computed display column**, not storage. Keying on `invoice_no` does not help.

#### Workarounds

1. **Set `tracking_no` in the same transaction that sets `create_invoice`** ("Confirm Shipment"). This is the normal path and it works — but only when the tracking number already exists at confirm time. The example below does exactly this.
2. **A user-defined field on `oe_pick_ticket_ud`,** writable through the [UDT Service API](13-UDT-Service-API.md). **Caveat:** it does **not** populate the native `oe_pick_ticket.tracking_no`, so customer portals, EDI, and third-party shipping integrations that read the native column will not see it.

#### Open question: `company.edit_tracking_number_flag`

`company.edit_tracking_number_flag` (`varchar(1)`) is P21's own switch for tracking-number editing. **Treat this as unproven, not as a finding.** On the system under test it was `'N'`; flipping it to `'Y'` and retrying produced identical errors. That is **not** a disproof — the SOA middleware pools PowerBuilder sessions and reads company settings at session creation, so the change plausibly requires a middleware restart, which the test environment could not perform. If you can restart middleware, this is the first thing to re-test.

#### Example: set the tracking number while confirming a shipment

<!-- tabs -->
```python
"""Set carrier + tracking number on a pick ticket while confirming its shipment."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
PICK_TICKET_NO = "123456"                 # must NOT be invoiced yet
CARRIER = "ACME FREIGHT"                  # carrier DISPLAY name (UseCodeValues: false)
TRACKING_NO = "TRACK-0000000000001"       # the carrier's tracking number
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


def walk(node):
    """Yield every {"Name": ..., "Value": ...} pair anywhere in a response."""
    if isinstance(node, dict):
        if "Name" in node and "Value" in node:
            yield node["Name"], node["Value"]
        for value in node.values():
            yield from walk(value)
    elif isinstance(node, list):
        for item in node:
            yield from walk(item)


with httpx.Client(verify=VERIFY_SSL, timeout=120, follow_redirects=True) as client:
    token = get_token(client)
    ui_server = get_ui_server(client, token)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",       # 2026.1 returns an empty 500 without this
        "Content-Type": "application/json",
    }

    # Status "New" with a populated Keys array updates the keyed pick ticket.
    payload = {
        "Name": "Shipping",
        "UseCodeValues": False,
        "Transactions": [{
            "Status": "New",
            "DataElements": [{
                "Name": "TABPAGE_1.tp_1_dw_1",
                "Type": "Form",
                "Keys": ["pick_ticket_no"],
                "Rows": [{
                    "Edits": [
                        {"Name": "pick_ticket_no", "Value": PICK_TICKET_NO},
                        {"Name": "carrier_id", "Value": CARRIER},
                        {"Name": "tracking_no", "Value": TRACKING_NO},
                        {"Name": "create_invoice", "Value": "ON"},   # Confirm Shipment
                    ],
                    "RelativeDateEdits": [],
                }],
            }],
        }],
    }

    response = client.post(f"{ui_server}/api/v2/transaction", headers=headers, json=payload)
    response.raise_for_status()          # HTTP 200 does NOT mean the write succeeded
    result = response.json()
    print("Summary:", result.get("Summary"))
    for message in result.get("Messages") or []:
        print("  Message:", message)

    # ---- read-back: the only proof the value landed -------------------------
    read_back = client.post(
        f"{ui_server}/api/v2/transaction/get",
        headers=headers,
        json={
            "ServiceName": "Shipping",
            "TransactionStates": [{
                "DataElementName": "TABPAGE_1.tp_1_dw_1",
                "Keys": [{"Name": "pick_ticket_no", "Value": PICK_TICKET_NO}],
            }],
        },
    )
    read_back.raise_for_status()

    wanted = {"pick_ticket_no", "carrier_id", "tracking_no", "invoice_no"}
    for name, value in walk(read_back.json()):
        if name in wanted:
            print(f"  {name} = {value}")
```

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string PickTicketNo = "123456";                  // must NOT be invoiced yet
const string Carrier = "ACME FREIGHT";                 // carrier DISPLAY name
const string TrackingNo = "TRACK-0000000000001";       // the carrier's tracking number
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

// Status "New" with a populated Keys array updates the keyed pick ticket.
var payload = new
{
    Name = "Shipping",
    UseCodeValues = false,
    Transactions = new[]
    {
        new
        {
            Status = "New",
            DataElements = new[]
            {
                new
                {
                    Name = "TABPAGE_1.tp_1_dw_1",
                    Type = "Form",
                    Keys = new[] { "pick_ticket_no" },
                    Rows = new[]
                    {
                        new
                        {
                            Edits = new[]
                            {
                                new { Name = "pick_ticket_no", Value = PickTicketNo },
                                new { Name = "carrier_id", Value = Carrier },
                                new { Name = "tracking_no", Value = TrackingNo },
                                new { Name = "create_invoice", Value = "ON" },   // Confirm Shipment
                            },
                            RelativeDateEdits = Array.Empty<object>(),
                        }
                    }
                }
            }
        }
    }
};

var response = await client.PostAsync(
    $"{uiServer}/api/v2/transaction",
    new StringContent(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json"));
response.EnsureSuccessStatusCode();     // HTTP 200 does NOT mean the write succeeded

using var result = JsonDocument.Parse(await response.Content.ReadAsStringAsync());
Console.WriteLine($"Summary: {result.RootElement.GetProperty("Summary")}");
if (result.RootElement.TryGetProperty("Messages", out var messages))
{
    foreach (var message in messages.EnumerateArray())
        Console.WriteLine($"  Message: {message}");
}

// ---- read-back: the only proof the value landed ---------------------------
var getPayload = new
{
    ServiceName = "Shipping",
    TransactionStates = new[]
    {
        new
        {
            DataElementName = "TABPAGE_1.tp_1_dw_1",
            Keys = new[] { new { Name = "pick_ticket_no", Value = PickTicketNo } },
        }
    }
};

var readBackResponse = await client.PostAsync(
    $"{uiServer}/api/v2/transaction/get",
    new StringContent(JsonSerializer.Serialize(getPayload), Encoding.UTF8, "application/json"));
readBackResponse.EnsureSuccessStatusCode();

using var readBack = JsonDocument.Parse(await readBackResponse.Content.ReadAsStringAsync());
var wanted = new HashSet<string> { "pick_ticket_no", "carrier_id", "tracking_no", "invoice_no" };
foreach (var (name, value) in Walk(readBack.RootElement))
{
    if (wanted.Contains(name))
        Console.WriteLine($"  {name} = {value}");
}

// --- helpers ---------------------------------------------------------------

// Yield every {"Name": ..., "Value": ...} pair anywhere in a response.
static IEnumerable<(string Name, string Value)> Walk(JsonElement node)
{
    if (node.ValueKind == JsonValueKind.Object)
    {
        if (node.TryGetProperty("Name", out var name) && node.TryGetProperty("Value", out var value))
            yield return (name.ToString(), value.ToString());
        foreach (var property in node.EnumerateObject())
            foreach (var pair in Walk(property.Value))
                yield return pair;
    }
    else if (node.ValueKind == JsonValueKind.Array)
    {
        foreach (var item in node.EnumerateArray())
            foreach (var pair in Walk(item))
                yield return pair;
    }
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

> **Third discovery path — ask P21 for the window name.** If you can open the report in the desktop client, you don't need to probe for its name at all: **right-click any field in the report window and choose *SQL Help***, which names the window (the `m_*` string) along with the field you clicked. Feed that name to `definition`/`defaults` for the field list, or straight to `pdfreport`. Because report windows carry only a handful of criteria fields, reading the criteria names out of SQL Help is often faster than pulling the whole definition — unlike a transaction window such as Order, where hand-collecting field names is not practical. *(Community session, Felipe Maurer, 2026.)*

**Report windows are still windows.** The endpoint runs the same PowerBuilder report window a user runs, with the same gates:

- **The API user needs access to that report window.** No permission, no report.
- **DynaChange data-change rules apply.** Sites commonly restrict these windows — capping date ranges so nobody runs a report wide open, for instance — and a `pdfreport` call hits those same restrictions. That is usually what you want; it also means a payload that works for one user can fail for another.
- **A wide-open report can run for days.** Criteria that would be reckless in the client are equally reckless here: an unbounded inventory-valuation run has been reported executing for three days before exhausting server memory. **Cancelling the HTTP request does not stop it** — the server keeps generating until it finishes or dies. Bound your criteria before the first call, and test new report payloads against a narrow date/company range. *(Community session, Felipe Maurer, 2026.)*

### Request Structure

The payload follows the standard TransactionSet format. Report-specific criteria go in the DataElement's `Edits` array:

> Payload shape only. Full runnable version: [Example: Generate and Save a PO Reprint](#example-generate-and-save-a-po-reprint).

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

#### An empty 5xx has several causes — and is usually transient

This endpoint runs at production volume: one integration generates PO PDFs for supplier emails all day, logging **154 successes against 3 empty 500s and 1 dropped connection in a single afternoon** — and every affected PO succeeded moments later on retry.

So an empty-bodied 5xx here is **not** a signal that your payload is wrong. It has at least three unrelated causes, and the response body cannot tell them apart:

| Cause | How to tell |
|---|---|
| **Transient report-engine fault** (most common) | The identical request succeeds seconds later. Retry before investigating anything else. |
| **Bad criteria** — e.g. a `company_id` that doesn't exist | Deterministic: every attempt fails. Verified on Play 26.1 — a wrong `company_id` returns an empty 500, not a useful message. |
| **The record isn't printable**, or report generation isn't available in that environment | Deterministic. On the Play tenant at 26.1.5910.3 **every** report returned an empty 500 — `m_reprintpurchaseorders` and `m_reprintpicktickets`, criteria straight from each service's own `/defaults`, both `UseCodeValues` settings, and six `Accept` variants — while `/definition` and `/defaults` for those same services returned 200. The same payload shape works in production, so treat a blanket failure like that as an environment property, not a payload bug. |

**Retry idempotent report calls.** Generating a PDF reads data and emits a document; running it twice costs latency, not correctness. The production integration uses **3 attempts with a 0.5 s × attempt backoff**, which covers the observed fault rate without masking a real outage.

**Do the existence check yourself, first.** A missing record and a transient fault both surface as an unhelpful 5xx, so read the record over OData before calling the report. That turns "not found" into a clear error of your own and leaves the 5xx meaning only "the report engine faulted".

**Classify the error envelope *before* the status code.** Unlike `/transaction`, which reports failure through `Summary`/`Messages`, this endpoint returns P21's `ErrorType`/`ErrorMessage` envelope — and it can arrive on a **200 as well as a 4xx/5xx**. Parse the body and check for `ErrorMessage` first; if you branch on `response.status_code` alone you will mask the one message that explains the failure (for example `No records to print for this range.`).

### Response

The response is a **JSON array** (even for a single document). Each element contains document metadata and the base64-encoded PDF content. Decode the `DocumentData` field and write the bytes to a `.pdf` file.

**Verified success response** (generalized from live PO reprint):

```json
[
  {
    "ClientId": "66666666-7777-8888-9999-aaaaaaaaaaaa",
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
- `DocumentFormat` value `5` corresponds to PDF format
- `DocumentContentType` is `"application/pdf"`
- **Success is per document, and HTTP 200 does not imply it.** Each element carries its own `ResponseStatus.StatusCode` — a **string** (`"Success"` / `"Failure"`), not an HTTP code. Treat a document as good only when `StatusCode == "Success"` **and** `DocumentData` is non-empty; otherwise read `ResponseStatus.Message` for the reason. A 200 can carry a failed document, and a multi-document request can mix both, so check every element rather than the first.

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
"""Generate a PO reprint PDF and save it to disk."""
import base64
import os
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
COMPANY_ID = "ACME"
PO_NO = "500100"                          # single PO: beg_po_no == end_po_no
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

    # Generate PO reprint PDF -- reports go to /process/pdfreport, never /transaction
    payload = {
        "Name": "m_reprintpurchaseorders",
        "Transactions": [{
            "DataElements": [{
                "Keys": [],
                "Name": "TABPAGE_1.poreportcriteriadw",
                "Rows": [{
                    "Edits": [
                        {"Name": "company_id", "Value": COMPANY_ID},
                        {"Name": "beg_po_no", "Value": PO_NO},
                        {"Name": "end_po_no", "Value": PO_NO},
                        {"Name": "reprint_flag", "Value": "Y"},
                    ]
                }],
                "Type": 0,
            }],
            "Status": 0,
        }],
        "UseCodeValues": False,
    }

    response = client.post(
        f"{ui_server}/api/v2/process/pdfreport", headers=headers, json=payload
    )
    response.raise_for_status()
    result = response.json()

    # Response is a JSON array -- even for a single document
    if isinstance(result, list) and len(result) > 0:
        doc = result[0]
        status = doc.get("ResponseStatus", {}).get("StatusCode")
        if status == "Success" and doc.get("DocumentData"):
            pdf_bytes = base64.b64decode(doc["DocumentData"])
            filename = doc.get("FileName", f"PO_{PO_NO}.pdf")
            with open(filename, "wb") as f:
                f.write(pdf_bytes)
            # read-back: what actually landed on disk
            print(f"Saved {filename} ({os.path.getsize(filename)} bytes)")
        else:
            msg = doc.get("ResponseStatus", {}).get("Message", "Unknown error")
            print(f"Report failed: {msg}")
    else:
        # Errors use the standard P21 envelope (ErrorType / ErrorMessage)
        print("No documents returned")
        print(f"Response: {result}")
```

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string CompanyId = "ACME";
const string PoNo = "500100";                          // single PO: beg == end
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

// Generate PO reprint PDF -- reports go to /process/pdfreport, never /transaction
var payload = new
{
    Name = "m_reprintpurchaseorders",
    Transactions = new[]
    {
        new
        {
            DataElements = new[]
            {
                new
                {
                    Keys = Array.Empty<string>(),
                    Name = "TABPAGE_1.poreportcriteriadw",
                    Rows = new[]
                    {
                        new
                        {
                            Edits = new[]
                            {
                                new { Name = "company_id", Value = CompanyId },
                                new { Name = "beg_po_no", Value = PoNo },
                                new { Name = "end_po_no", Value = PoNo },
                                new { Name = "reprint_flag", Value = "Y" },
                            }
                        }
                    },
                    Type = 0
                }
            },
            Status = 0
        }
    },
    UseCodeValues = false
};

var response = await client.PostAsync(
    $"{uiServer}/api/v2/process/pdfreport",
    new StringContent(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json"));
response.EnsureSuccessStatusCode();

using var result = JsonDocument.Parse(await response.Content.ReadAsStringAsync());

// Response is a JSON array -- even for a single document
if (result.RootElement.ValueKind == JsonValueKind.Array && result.RootElement.GetArrayLength() > 0)
{
    var doc = result.RootElement[0];
    var status = doc.GetProperty("ResponseStatus").GetProperty("StatusCode").GetString();
    var documentData = doc.TryGetProperty("DocumentData", out var data) ? data.GetString() : null;

    if (status == "Success" && !string.IsNullOrEmpty(documentData))
    {
        var pdfBytes = Convert.FromBase64String(documentData);
        var filename = doc.GetProperty("FileName").GetString() ?? $"PO_{PoNo}.pdf";
        await File.WriteAllBytesAsync(filename, pdfBytes);
        // read-back: what actually landed on disk
        Console.WriteLine($"Saved {filename} ({new FileInfo(filename).Length} bytes)");
    }
    else
    {
        var message = doc.GetProperty("ResponseStatus").GetProperty("Message").GetString();
        Console.WriteLine($"Report failed: {message ?? "Unknown error"}");
    }
}
else
{
    // Errors use the standard P21 envelope (ErrorType / ErrorMessage)
    Console.WriteLine("No documents returned");
    Console.WriteLine($"Response: {result.RootElement}");
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

> **Credit:** Jeff Poss discovered the `/api/v2/process/pdfreport` endpoint and payload structure.

### Example: Generate a Production-Order Pick Ticket (m_picktickets)

Running `m_picktickets` **creates the pick-ticket record** at the given `location_id` **and** returns the PDF in a single call. This matters for production orders that are built at one location while their components stock at another — the `ProductionOrder` transaction print flag only emits at the *make* location (see [PDFs from the /transaction endpoint](#pdfs-from-the-transaction-endpoint-print-flags) below), but this report generates the ticket at whatever location you specify.

> Payload shape only -- note `UseCodeValues: true` and the code values. Full runnable version (swap in this payload): [Example: Generate and Save a PO Reprint](#example-generate-and-save-a-po-reprint). End-to-end walkthrough: [recipes/generate-pick-ticket-pdf.md](recipes/generate-pick-ticket-pdf.md).

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

## GL Dimensions in the API

GL dimensions (P21's dimensional-accounting tags) attach to accounting lines, **not to purchase orders**. If you need a PO pre-tagged with a dimension, the PO tables can't carry it — the tag must be applied downstream at vouchering, invoicing, or journal-entry time.

**Where dimensions live in the schema:**

| Table | Role |
|-------|------|
| `gl_dimen_type` / `gl_dimen_type_x_value` | Dimension types (`record_type_cd` 932 user / 933 system) and their valid values |
| `gl` (`gl_dimen_type_uid`, `gl_dimension_id`) | One dimension per GL distribution row |
| `apinv_line` (+ `recur_apinv_line`) | One dimension per AP voucher line — the manual-tagging-at-voucher-entry surface |
| `invoice_line` | One dimension per AR invoice line |
| `oe_hdr.gl_dimension_project_no` | Project dimension on an order header (hidden field, added via Field Chooser) |
| `trans_x_gl_dimension` / `gl_trans_x_dimension` | Multi-dimension tags at transaction / journal-entry level |
| **`po_hdr` / `po_line`** | **No dimension columns at all** — POs are outside the dimension model |

Dimensions are labels, not postings: P21 lets you edit them after posting by design, with dedicated audit-trail tables.

**Which services expose the fields:** the voucher-creation services **`ConvertPOToVoucher`** and **`VoucherByItem`** both carry the dimension fields (`gl_dimen_type_id`, `gl_dimen_type_uid`, `gl_dimension_id`, `gl_dimension_desc`, `gl_dimen_type_desc`) **plus a `TP_TRANS_X_GL_DIMENSION.tp_trans_x_gl_dimension` List** — the transaction-level multi-dimension grid. `VoucherByItem` additionally exposes the dimension fields on its line grid (`TABPAGE_17.tp_17_dw_17`). So voucher-creation automation *can* apply GL dimensions at vouchering time. Full schema: [ConvertPOToVoucher.json](../definitions/ConvertPOToVoucher.json), [VoucherByItem.json](../definitions/VoucherByItem.json).

**Gotchas:**

- **Pre-tagging a PO is not possible** through native columns — `po_hdr`/`po_line` have no dimension fields. A PO can only carry a dimension via user-defined (UD) fields; the dimension itself attaches from a voucher/invoice/JE surface.
- **`VendorInvoice` returns HTTP 500 on `/api/v2/definition`** (the [unavailable-window signal](#endpoints)) even though it appears in `/api/v2/services` — use `ConvertPOToVoucher` / `VoucherByItem` for voucher automation.
- `ConvertPOToVoucher` is a **commands-endpoint** service with field-ordering sensitivities (see [Field Order Matters](#field-order-matters) and the [25.2 breaking changes](14-Breaking-Changes.md)).

> Verified on 26.1.5894.1 (play), July 2026.

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
"""Load a stored procedure definition and print its fields and parameters."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
SP_UID = "12345"                          # from the P21 Stored Procedure Executor UI
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
        "ServiceName": "m_storedprocedureexecutor",
        "TransactionStates": [{
            "DataElementName": "DEFINITION.stored_procedure_def",
            "Keys": [{
                "Name": "stored_procedure_def_uid",
                "Value": SP_UID,
            }],
        }],
    }

    response = client.post(
        f"{ui_server}/api/v2/transaction/get", headers=headers, json=payload
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
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string SpUid = "12345";              // from the P21 Stored Procedure Executor UI
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

var payload = new
{
    ServiceName = "m_storedprocedureexecutor",
    TransactionStates = new[]
    {
        new
        {
            DataElementName = "DEFINITION.stored_procedure_def",
            Keys = new[]
            {
                new { Name = "stored_procedure_def_uid", Value = SpUid }
            }
        }
    }
};

var response = await client.PostAsync(
    $"{uiServer}/api/v2/transaction/get",
    new StringContent(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json"));
response.EnsureSuccessStatusCode();

using var result = JsonDocument.Parse(await response.Content.ReadAsStringAsync());

// The response includes the SP definition and its argument_list parameters
if (result.RootElement.TryGetProperty("Transactions", out var transactions))
{
    foreach (var txn in transactions.EnumerateArray())
    {
        if (!txn.TryGetProperty("DataElements", out var dataElements)) continue;
        foreach (var de in dataElements.EnumerateArray())
        {
            Console.WriteLine($"DataElement: {de.GetProperty("Name")}");
            if (!de.TryGetProperty("Rows", out var rows)) continue;
            foreach (var row in rows.EnumerateArray())
            {
                if (!row.TryGetProperty("Edits", out var edits)) continue;
                foreach (var edit in edits.EnumerateArray())
                    Console.WriteLine($"  {edit.GetProperty("Name")}: {edit.GetProperty("Value")}");
            }
        }
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
| In-window **wizards** launched from another window — the PO wizard and assembly decoder from Order Entry, credit-card entry (an embedded merchant-gateway form, not a P21 window) | (Community-reported) Not drivable from TAPI. Use the Interactive API. For credit cards, the documented TAPI path takes a **token you generated elsewhere** — the entry form itself is out of reach. *(Community session, Felipe Maurer, 2026)* |
| Drag-and-drop windows | No TAPI path. Verified on the standalone `*Notepad` services (26.1, Aug 2026): their mandatory **area selector** is a drag-and-drop control, and no payload satisfies it — omit the areas element and the save fails with `You must select at least one area where this note will display.`; send a row into the Selected Areas list (`TABPAGE_17.tp_17_dw_17`) and it fails with `Column is disabled: area`. `IgnoreDisabled: true` changes neither. *(Community session, Felipe Maurer, 2026; verified August 2026)* |
| **Mandatory notes** blocking a save | (Community-reported) A mandatory note diverts the window to the notes tab and strands the transaction. A **user setting** on the API user's profile — the option to receive mandatory notes as prompts/alerts rather than as a hard stop (bottom-left of the login/user settings) — lets the transaction proceed. Weigh this before enabling it: mandatory notes usually exist for a reason, and this suppresses them for that user. *(Community session, Felipe Maurer, 2026)* |

> **Order notes: the elements are published, and they are all disabled.** The `Order` definition looks encouraging — it publishes **`LINE_NOTE.line_note`** and **`HDR_NOTE.hdr_note`** as ordinary `List` DataElements keyed on `note_id`, each with `note`, `topic` and `notepad_class_desc` fields, plus `TP_ITEMNOTES.tp_itemnotes` keyed on `note_uid`. None of it is writable. Tested against a 26.1 tenant on a live order (August 2026), **every column of both note elements is refused**, one at a time, whichever you send: `Column is disabled: topic`, `Column is disabled: notepad_class_desc`, `Column is disabled: note`. `TP_ITEMNOTES` refuses a step earlier still, with `Tab page is disabled and cannot be selected`.
>
> **And `IgnoreDisabled: true` makes it worse, not better.** The same `LINE_NOTE` write that fails loudly without the flag returns `Succeeded: 1` with it — and the note is still empty on read-back. That is [Breaking Changes entry 8](14-Breaking-Changes.md#8-ignoredisabled-true-reports-success-on-writes-that-write-nothing) exactly: the flag swallows the refusal and reports success on a write that wrote nothing.
>
> The standalone notepad services close the loop the same way. `ItemNotepad`, `CustomerNotepad`, `SupplierNotepad` and `VendorNotepad` (see [Common Services](#common-services)) each publish a perfectly ordinary header form — `note_id`, `topic`, `note`, `mandatory`, activation/expiration dates, a `notepad_class` with `ValidValues` — and every create dies on the same wall (tested on the first three, 26.1, August 2026): the mandatory **"where does this note display" area selector is a drag-and-drop control**. Omit it and the save fails with `You must select at least one area where this note will display.`; send the area as a row into the Selected Areas list (`TABPAGE_17.tp_17_dw_17`, declared `KeyFields: ["area"]`) and it fails with `Column is disabled: area`; the Available Areas side (`tp_17_dw_dragdrop`) accepts the row and then fails the save on the same missing selection. `IgnoreDisabled: true` changes none of it. This is the [drag-and-drop limitation](#limitations) with a paper trail.
>
> So **"the Transaction API can't do notes" is simply true — notes are Interactive API territory.** Not for the reason usually given (the *Add Line Note* wizard — true, but incidental): every path is independently closed. `Order`'s embedded note elements are disabled columns; the standalone `*Notepad` services stall on a drag-and-drop area picker. Use the Interactive API's verified paths: [PurchaseOrder Notepad Writes](04-Interactive-API.md#purchaseorder-notepad-writes-header-vs-line) and [Sales Order Notepad Writes](04-Interactive-API.md#sales-order-notepad-writes-header-vs-line) — the Order path is verified end-to-end (header and line notes, DB-confirmed) with the same popup mechanics. *(Community session, Felipe Maurer, 2026, for the wizard claim; both closures and the working Order path verified live, August 2026.)*

### Item Issues Detected Popup Root Cause and Data Fix

*Verified on production P21, 2026-08-10.*

The `Unexpected response window: Item Issues Detected` abort that kills `Item`-service transactions (see [Item Service Gotchas](#item-service-gotchas)) is not random and not environment luck. It is a **DynaChange business rule with `apply_during_save_flag = 'Y'`**, which fires on **every save of the Item window** — including the save the Transaction API performs internally. The rule raises a `w_rule_callback_response` modal, the Transaction API has no way to answer it, and the transaction aborts with the edit discarded.

Two consequences worth stating plainly:

- It blocks **all** `Item`-service writes on an affected item, not only `product_group_id` changes.
- It is **deterministic**. Retrying the same transaction fails every time. Once the underlying data is corrected, the identical transaction succeeds with no other change.

#### Step 1 -- Identify the responsible rule

Join `business_rule` to `business_rule_data_element` for the window you are writing to. On the system under test the rule was:

| Attribute | Value on the system under test |
|-----------|-------------------------------|
| `rule_name` | `ItemDefaults` |
| `window_name` | `w_inventory_sheet` |
| `window_title` | `Item Maintenance` |
| `class_name` | `d_inventory2` |
| `apply_during_save_flag` | `Y` |

> The rule uid on that system was `25`. **That is environment-specific** — rule uids are assigned per site and are not a universal identifier. Look the rule up by `window_name` on your own system; the name, uid, and field list will all differ.

Its `business_rule_data_element` rows covered:

- `d_inventory2`: `delete_flag`, `item_desc`, `item_id`, `purchase_discount_group_id`, `sales_discount_group_id`
- `d_item_suppliers`: `cost`, `list_price`, `supplier_part_no`

#### Step 2 -- Find the rows that trip it

On that system the specific trigger was an `inventory_supplier` row with **`cost = 0` AND `list_price = 0`**. Either value being non-zero satisfies the rule (confirmed in both directions).

**It is the zero rows that matter, not the primary supplier row.** An item can have one supplier row carrying a real cost and still be blocked by a *different* supplier row on the same item with both values at zero. Find them all:

```sql
SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;
SET LOCK_TIMEOUT 10000;

SELECT m.item_id, s.inventory_supplier_uid, s.supplier_id, s.cost, s.list_price
FROM inventory_supplier s WITH (NOLOCK)
JOIN inv_mast m WITH (NOLOCK) ON m.inv_mast_uid = s.inv_mast_uid
WHERE s.delete_flag = 'N'
  AND ISNULL(s.cost, 0) = 0
  AND ISNULL(s.list_price, 0) = 0;
```

#### Step 3 -- Populate a cost, then re-run

Set `cost` on the offending rows **before** the API call. The most defensible source is the item's own purchase history with that supplier — the most recent non-zero PO line unit price:

```sql
SELECT TOP 1 pl.unit_price, ph.order_date, ph.po_no
FROM po_hdr ph WITH (NOLOCK)
JOIN po_line pl WITH (NOLOCK) ON pl.po_no = ph.po_no
WHERE pl.inv_mast_uid = ? AND ph.supplier_id = ? AND pl.unit_price > 0
ORDER BY ph.order_date DESC;
```

Items with **no PO history** have no value to derive and need an operator-chosen fallback — that decision belongs to whoever owns the item data, not to the integration.

With the costs populated, re-running the identical transaction succeeds. Verified on **28 of 28 items across two suppliers**, with no manual UI work. Retries *before* the data fix failed every time.

#### When you cannot fix the data

Use the Interactive API and answer the popup with `cb_1` ("Yes, Proceed Anyway") — see [Item window popups](04-Interactive-API.md#worked-example-item-issues-detected-rule-callback). Lead with the data fix: it is faster, it is bulk-safe, and it leaves the item correct for desktop users too.

### Response Validation

> **Important:** The Transaction API returns **HTTP 200 even for failed transactions**. Always check the `Summary` and `Messages` sections of the response body -- never rely on the HTTP status code alone to determine success or failure. *(Credit: Neil Timmerman)*

> Fragment -- shows only the check. Full runnable version: [Create Order](#create-order).

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
