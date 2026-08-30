# P21 API Selection Guide

> **Disclaimer:** This is unofficial, community-created documentation for Epicor Prophet 21 APIs. It is not affiliated with, endorsed by, or supported by Epicor Software Corporation. All product names, trademarks, and registered trademarks are property of their respective owners. Use at your own risk.

---

## Overview

Prophet 21 provides several APIs for external data access and manipulation. This guide helps you choose the right API for your use case.

## Before You Choose: Interactive Is Not an Escape Hatch

The Interactive API is **not** a way around a disabled column or a window-level gate. Both the Transaction API and the Interactive API drive the same PowerBuilder windows and enforce the same business rules — a window that refuses a record or disables a column refuses/disables it for **both** APIs. The Interactive API only adds a stateful session with multi-step window interaction. Choose it because a workflow genuinely needs that statefulness (multi-step entry, answering response windows) — never because a write failed on one API and you're hoping the other will let it through.

Two verified instances (2026-08-11), both documented in detail in the [Transaction API](03-Transaction-API.md) guide:
- The `Shipping` service refuses an already-invoiced pick ticket at record selection, so a tracking number cannot be set post-invoice through either API — see [Shipping Service — Carrier Tracking Number](03-Transaction-API.md#shipping-service-carrier-tracking-number).
- `c_tracking_no` on the `Order` / `FrontCounter` / `RMA` / `ServiceOrder` shipment grids is a computed, disabled display column (`Column is disabled: c_tracking_no`) — not a write path, in either API.

**The genuine exception is response-window dialogs.** The Interactive API can answer some dialogs the Transaction API cannot — see the ["Item Issues Detected" rule-callback worked example](04-Interactive-API.md#worked-example-item-issues-detected-rule-callback). That is a real capability difference about *handling a dialog*, not about bypassing a disabled column or a window gate. Interactive answers dialogs; it does not unlock what the window has locked.

## Quick Decision Table

| Need | Best API | Why |
|------|----------|-----|
| Read data quickly | **OData** | Standard protocol, efficient queries |
| Bulk create records | **Transaction API** | Stateless, supports batching |
| Complex business workflows | **Interactive API** | Full business logic, validation |
| Simple CRUD (customers, vendors, contacts, addresses) | **Entity API** | Stateless, domain objects |
| CRUD on inventory items and locations (`inv_loc`) | **Inventory REST API** | Stateless GET → modify → PUT |
| Write to user-defined tables (`udt_*`) | **UDT Service API** | Stateless insert/update/delete; read via OData |
| Update existing records (keyed fields) | **Transaction API** | `Status: "New"` + keyed rows updates and upserts (verified) |
| Update records behind dialogs/prompts | **Interactive API** | Only API that can answer response windows |
| Handle response dialogs | **Interactive API** | Only API with dialog handling |
| Record labor hours to production orders | **Transaction API** | TimeEntry service, stateless |
| Bulk create production orders | **Transaction API** | Stateless, high-volume creation |
| Modify or complete production orders | **Interactive API** | Stateful workflow with validation |

---

## API Comparison

| Feature | OData | Transaction | Interactive | Entity | Inventory REST | UDT Service |
|---------|-------|-------------|-------------|--------|----------------|-------------|
| **Read Data** | Excellent | Limited | Good | Good (4 entities) | Good (items) | No (use OData) |
| **Create Data** | No | Excellent | Good | Good (4 entities) | Good (items) | Good (UDT rows) |
| **Update Data** | No | Good* | Excellent | Good (4 entities) | Good (items/locations) | Good (by `row_uid`) |
| **Delete Data** | No | No | Via UI | Via flag | No | Yes |
| **Bulk Operations** | Yes (read) | Yes | No | No | No | Yes (multi-row insert) |
| **Business Logic** | No | Partial | Full | No | Partial (validation) | No |
| **Session Required** | No | No | Yes | No | No | No |
| **Stateful** | No | No | Yes | No | No | No |
| **Response Dialogs** | N/A | N/A | Yes | N/A | N/A | N/A |

*Transaction API updates use `Status: "New"` with keyed rows — [`"New"` is the only value the enum accepts](03-Transaction-API.md#status-new-is-the-only-value-the-enum-accepts). Keyed rows behave as an **upsert**: update if the key matches, insert if it doesn't. Verified at scale (170+ line updates, 80+ line inserts on JobContractPricing). See [Updating an Existing Contract](03-Transaction-API.md#updating-an-existing-contract). Flows that pop validation dialogs still need the Interactive API.

---

## OData API

### Best For
- Reporting and data exports
- Quick lookups and searches
- Dashboard data
- Data validation
- Any read-only operation

### Characteristics
- **Standard OData v4 protocol** - familiar to most developers
- **Read-only** - cannot create, update, or delete
- **No session management** - simple request/response
- **Efficient** - supports filtering, pagination, field selection
- **Direct table/view access** - query any P21 table or view

### Use When
- You only need to read data
- Performance is critical
- You need standard query capabilities ($filter, $select, $orderby)
- You want to minimize complexity

### Don't Use When
- You need to create or modify data
- You need business logic validation

### Example Use Cases
- Get supplier list for dropdown
- Search for products
- Export pricing data
- Validate customer exists
- Dashboard metrics

---

## Transaction API

### Best For
- Bulk record creation
- External system integration
- Automated data import
- High-volume operations

### Characteristics
- **Stateless** - each request is independent
- **Bulk operations** - multiple records per request
- **Metadata-driven** - follows P21 window schemas
- **Fast** - 50-100x faster than Interactive API for creates
- **Updates via `Status: "New"` + keys** - keyed rows upsert (update if the key matches, insert if not); `"New"` is the [only value the enum accepts](03-Transaction-API.md#status-new-is-the-only-value-the-enum-accepts)

### Use When
- Creating many records at once
- Updating or inserting keyed fields/rows on existing records
- Building integrations from external systems
- Performance is critical
- You don't need complex validation feedback

### Don't Use When
- The operation pops validation dialogs / response windows (use Interactive API)
- A sub-tab stays disabled until a parent row is selected and `IgnoreDisabled` doesn't unlock it (use Interactive API)
- You need field-by-field validation feedback

### Known Issues
- **Session Pool Contamination** - intermittent failures with some windows
- **`Status: "Existing"` is not a value** - the enum has [exactly one member, `"New"`](03-Transaction-API.md#status-new-is-the-only-value-the-enum-accepts); `"Existing"` is HTTP 400 on 26.1.5940.0 and an HTTP 500 `NullReferenceException` on older builds. Use `"New"` for updates too (see [Transaction API](03-Transaction-API.md#updating-an-existing-contract))
- **Prompts are auto-answered with the default** - a DynaChange or validation prompt kills the affected line/record silently
- See [Session Pool Troubleshooting](07-Session-Pool-Troubleshooting.md)

### Example Use Cases
- Import price pages from spreadsheet
- Sync products from external catalog
- Bulk create purchase orders
- Automated data migration
- Record labor hours against production orders (TimeEntry service)
- Bulk create production orders

---

## Interactive API

### Best For
- Complex business workflows
- Record updates
- Operations requiring validation
- Handling response dialogs

### Characteristics
- **Stateful** - maintains session between requests
- **Full business logic** - all P21 validation and rules
- **Window-based** - interacts with P21 windows
- **Response dialogs** - can handle pop-up confirmations
- **Reliable updates** - field-level control

### Use When
- Operations may trigger dialogs (email, confirmations) that must be answered
- Updating records where the Transaction API path hits disabled tabs or prompts
- You need full P21 business validation
- Complex multi-step workflows
- You need to mimic user interaction

### Don't Use When
- Simple reads (use OData - faster)
- Bulk creates (use Transaction API - faster)
- You don't need business logic

### Performance Note
The Interactive API is slower than the Transaction API (~5s vs 0.05s per created record; a windowed edit typically takes ~5 round-trips). Prefer the Transaction API when a keyed update works, and fall back to the Interactive API when the flow needs real window logic or dialog answers.

### Version Note
Some P21 servers only support v2 Interactive API endpoints. If you receive 404 errors on `/api/ui/interactive/v1/*` endpoints, use `/api/ui/interactive/v2/*` instead. The v2 endpoints have different payload formats - see [Interactive API v1 vs v2](04-Interactive-API.md#v1-vs-v2-api-differences).

### Example Use Cases
- Update purchase order status
- Modify customer records
- Complex order entry
- Any operation with approval dialogs
- Manage production orders (open, modify, complete)
- Record labor hours via Time Entry window

---

## Entity API

### Best For
- Customer, vendor, contact, and address CRUD
- Quick single-record operations on supported entities
- B2B integrations needing domain object models

### Characteristics
- **Entity-based** - works with P21 domain objects (not raw table rows)
- **Simple CRUD** - create, read, update via REST
- **Stateless** - no session management required
- **Umbrella term** - Epicor's "Entity API" covers the whole REST API, including the `/api/entity/`, `/api/inventory/`, and `/api/sales/` endpoint families (see the Terminology section of the [Entity API doc](05-Entity-API.md))
- **`/api/entity/` scope** - the `/api/entity/` endpoint family covers only 4 entities: customers, vendors, contacts, addresses
- **Composite keys** - customers/vendors use `{CompanyId}_{Id}` format
- **Address limitations** - Address entity has no `/new` template and no PUT/update (read and create only)

### Use When
- You need CRUD on customers, vendors, contacts, or addresses
- You want cleaner domain objects than raw OData table rows
- You prefer stateless REST over Interactive API session management

### Don't Use When
- You need orders — those live in the same REST API at `/api/sales/orders`, which reads *and* creates ([Other REST Endpoint Families](05-Entity-API.md#other-rest-endpoint-families) · [Creating an Order](05-Entity-API.md#creating-an-order-post-apisalesorders))
- You need inventory items — use the [Inventory REST API](11-Inventory-REST-API.md) (`/api/inventory/parts`)
- You need invoices, POs, or other business objects (no endpoint family found)
- You need bulk operations (use Transaction API)
- You need full business logic validation (use Interactive API)

### Example Use Cases
- Look up customer with address: `GET /api/entity/customers/ACME_10?extendedproperties=CustomerAddress`
- Search vendors: `GET /api/entity/vendors/?$query=startswith(VendorName, 'ABC')`
- Get contact details: `GET /api/entity/contacts/1`

---

## Inventory REST API

### Best For
- Inventory item CRUD, including location-level (`inv_loc`) data
- Multi-company workflows (adding items to new companies/locations)
- Item availability and pricing lookups

### Characteristics
- **Stateless** - no session management required
- **Item-centric** - single base path `/api/inventory/parts`, keyed by ItemId
- **GET → modify → PUT pattern** - fetch the full payload, change or append, PUT it back
- **`inv_loc` access** - read, append, and update location records via extended properties
- **Validation** - P21 validates changed values (e.g., invalid ProductGroupId is rejected)

### Use When
- You need to read item details including location-specific data
- You need to append or update `inv_loc` / `inventory_supplier` records
- You need to create items or add existing items to new companies

### Don't Use When
- You only need read access (use OData - faster, no payload round-trip)
- You need bulk operations across many items (use Transaction API)
- The change triggers dialogs or complex window logic (use Interactive API)

### Example Use Cases
- Read an item with locations: `GET /api/inventory/parts/WIDGET-001?extendedproperties=*`
- Add an item to a new company/location (GET → append → PUT)
- Update `inv_loc` fields like Sellable or ProductGroupId (GET → modify → PUT)

See [Inventory REST API](11-Inventory-REST-API.md) for full details.

---

## UDT Service API

### Best For
- Writing to user-defined tables (`udt_*`) from external systems
- Automating data entry for custom workflows built on UDTs

### Characteristics
- **Write-only** - insert, update, and delete endpoints; read UDT data via OData
- **Stateless** - no session management required
- **Column-based payloads** - data sent as column name/value pairs
- **Condition-based targeting** - updates and deletes identify rows via `row_uid`

### Use When
- You need to insert, update, or delete rows in a `udt_*` table
- B2B integrations that write to custom P21 tables

### Don't Use When
- You need to read UDT data (use OData - the UDT Service API has no read endpoints)
- You're working with standard P21 tables (use the other APIs)

### Example Use Cases
- Insert rows: `POST /udtservice/api/udtdata/insertudtdata`
- Update rows by `row_uid`: `PUT /udtservice/api/udtdata/updateudtdata`
- Delete rows: `DELETE /udtservice/api/udtdata/deleteudtdata`

See [UDT Service API](13-UDT-Service-API.md) for full details.

---

## ui/full — the Web Client's Surface (Last Resort)

### Best For
- Windows the service registry does not expose — `frame_menu.service_name` is NULL, so no `ServiceName` exists to open them with

### Characteristics
- **Stateful**, like the Interactive API, but a separate session (`{ui}/ui/common/v1/sessions/`)
- **Opens by menu class name** (`m_*`), not by service name
- **No `/api/` prefix** on its routes — `{ui}/ui/full/v2/...`
- **Different envelope** — `Success` + `State`, not `Status` 1/2/3
- **Thin failure reporting** — a refused call is HTTP 200, `Success: false`, no message

### Use When
- The window you need has a NULL `service_name` *and* the web client can open it

### Don't Use When
- A registered service exists. Prefer the Transaction API, then the Interactive API — both are better documented and report failures properly.
- The window is classic-desktop-only (`new_ui_enabled` / `angular_enabled` = `'N'`). Nothing reaches it.

See [The ui/full Surface](04-Interactive-API.md#the-uifull-surface-the-web-clients-own-rest-api) for the endpoint table and worked example.

---

## Decision Flowchart

```
Start
  │
  ├─ Need to READ data only?
  │   │
  │   └─ Yes → Use OData API
  │
  ├─ Writing to a user-defined table (udt_*)?
  │   │
  │   └─ Yes → Use UDT Service API
  │
  ├─ CRUD on inventory items / inv_loc?
  │   │
  │   └─ Yes → Use Inventory REST API
  │
  ├─ Need to CREATE multiple records?
  │   │
  │   └─ Yes → Use Transaction API
  │
  ├─ Need to UPDATE records?
  │   │
  │   ├─ Keyed fields/rows, no dialogs → Use Transaction API (Status "New")
  │   │
  │   └─ Dialogs, disabled tabs, complex flows → Use Interactive API
  │
  ├─ Need response dialog handling?
  │   │
  │   └─ Yes → Use Interactive API
  │
  └─ Single-record CREATE?
      │
      ├─ High volume → Use Transaction API
      │
      └─ Low volume / needs validation → Use Interactive API
```

---

## Hybrid Approaches

### Read with OData, Write with Transaction/Interactive

The most common pattern:
1. Use **OData** for all reads (fast, simple)
2. Use **Transaction API** for creates and keyed updates (fast)
3. Use **Interactive API** for flows that need window logic or dialog answers

### Example: Price Page Management

The snippet below is illustrative — `odata`, `transaction`, and `interactive` are
stand-ins for whichever client wrapper you build, shown here only to sketch the
three-API hybrid pattern.

> Full runnable version: [OData filtered query](02-OData-API.md#filtered-query),
> [Transaction API create example](03-Transaction-API.md#example-create-a-job-contract-with-break-and-non-break-lines),
> [Interactive API price page linking](04-Interactive-API.md#example-linking-price-page-to-price-book)

<!-- tabs -->
```python
# Read existing pages - OData (fast)
pages = odata.get_price_pages(supplier_id=10050)

# Create new pages - Transaction API (bulk, fast)
new_pages = transaction.create_pages([...])

# Update existing page - Interactive API (reliable)
with interactive.open_window("SalesPricePage") as window:
    window.change_data("calculation_value1", "0.55")
    window.save()
```

```csharp
// Read existing pages - OData (fast)
var pages = await client.OData.QueryAsync("price_page",
    filter: "supplier_id eq 10050");

// Create new pages - Transaction API (bulk, fast)
var result = await client.Transaction.CreateAsync(newPagesPayload);

// Update existing page - Interactive API (reliable)
await using var session = client.Interactive.CreateSession();
await session.StartAsync();
var window = await session.OpenWindowAsync("SalesPricePage");
await window.ChangeDataAsync("FORM", "calculation_value1", "0.55",
    datawindowName: "form");
await window.SaveDataAsync();
await window.CloseAsync();
```
<!-- /tabs -->

---

## Performance Benchmarks

Measured against production P21 instance:

| Operation | OData | Transaction | Interactive |
|-----------|-------|-------------|-------------|
| Read 160 records | 0.12s | N/A | ~2s |
| Create 1 record | N/A | 0.05s | 2.5s |
| Create 25 records | N/A | 1.4s | 62s |
| Update 1 record | N/A | ~0.8s* | 2.0s |

*Transaction API keyed update via `Status: "New"` (verified on JobContractPricing; per-line latency ~0.8s). Flows that trip prompts or disabled tabs still need the Interactive API.

---

## Related

- [Authentication](00-Authentication.md)
- [OData API](02-OData-API.md)
- [Transaction API](03-Transaction-API.md)
- [Interactive API](04-Interactive-API.md)
- [Entity API](05-Entity-API.md)
- [Inventory REST API](11-Inventory-REST-API.md)
- [Production & Labor API](12-Production-Labor-API.md)
- [UDT Service API](13-UDT-Service-API.md)
- [Session Pool Troubleshooting](07-Session-Pool-Troubleshooting.md)
