# Task Index — Find the Right Section Fast

> **How to use this repo without drowning in it:** the numbered docs are the deep *manual* — most are over 1,000 lines. Don't read a whole doc for one task. Find your task below and open **only the linked section**. If you're an AI assistant: read `CLAUDE.md`, then this index, then just the sections your task needs.

Every task assumes you already have a token and (for Transaction/Interactive) the UI server URL — see [Getting a token](#first-call-of-any-session) below.

**Doing, not studying?** The [recipes cookbook](recipes/README.md) has self-contained copy-and-run pages (complete payload + full script + gotchas) for the most common tasks — start there and fall back to the manual sections for depth.

---

## First call of any session

| Task | Where |
|------|-------|
| Get a bearer token (v2, credentials in body) | [00 § Method 1: User Credentials](00-Authentication.md#method-1-user-credentials) |
| Authenticate with a consumer key | [00 § Method 2: Consumer Key](00-Authentication.md#method-2-consumer-key) |
| Get the UI server URL (Transaction/Interactive base) — 307 redirect gotcha | [00 § UI Server URL](00-Authentication.md#ui-server-url) |
| Token TTL / reuse across APIs | [00 § Token Lifetime and Reuse](00-Authentication.md#token-lifetime-and-reuse) |
| Fix "not authorized" (P21 user permissions) | [00 § P21 Permissions](00-Authentication.md#p21-permissions-user-credential-auth) |
| Pick which API to use for a task | [01 API Selection Guide](01-API-Selection-Guide.md) (short — read whole) |
| A write failed — will the *other* API get through? (usually no) | [01 § Interactive Is Not an Escape Hatch](01-API-Selection-Guide.md#before-you-choose-interactive-is-not-an-escape-hatch) |

## Read data (OData)

| Task | Where |
|------|-------|
| Query a table or view | [02 § Query Parameters](02-OData-API.md#query-parameters) |
| Filter syntax, operators, string functions | [02 § Filter Expressions](02-OData-API.md#filter-expressions) |
| Only active rows — `row_status_flag` **or** `delete_flag`, depending on the table | [02 § Active Record Filter](02-OData-API.md#active-record-filter) |
| Company column is `company_id` on some tables, `company_no` on others | [02 § Company Scoping](02-OData-API.md#company-scoping-company_id-vs-company_no) |
| Traverse relationships (no joins — chain by `_uid`) | [02 § No Joins](02-OData-API.md#no-joins-chain-queries-by-uid) |
| Page through large result sets (no nextLink) | [02 § Pagination Helper](02-OData-API.md#pagination-helper) · [02 § Page Size Guidance](02-OData-API.md#page-size-guidance) |
| Date filters (`now()` is unsupported) | [02 § now() Not Supported](02-OData-API.md#now-function-not-supported) |
| New table/column missing from OData | [02 § OData Schema Refresh](02-OData-API.md#odata-schema-refresh) |
| Table reads fine but is empty/inert (undeployed feature, e.g. zip→rep) | [02 § Undeployed / Unlicensed Windows](02-OData-API.md#undeployed-unlicensed-windows-readable-tables-no-api-surface) |

## Create / update records (Transaction API)

| Task | Where |
|------|-------|
| Payload anatomy (TransactionSet / DataElements / Edits) | [03 § Request Structure](03-Transaction-API.md#request-structure) |
| Payload rejected / values not landing (shape & type mistakes) | [03 § Payload Anatomy](03-Transaction-API.md#payload-anatomy-types-nesting-and-common-mistakes) |
| Validate a payload offline before posting (JSON or XML) | [`scripts/validate_payload.py`](../scripts/validate_payload.py) · [03 § Payload Anatomy](03-Transaction-API.md#payload-anatomy-types-nesting-and-common-mistakes) |
| Copy-ready payload files (JSON and XML, validator-verified) | [`examples/payloads/`](../examples/payloads/README.md) |
| Send/receive **XML** instead of JSON | [03 § XML Payloads](03-Transaction-API.md#xml-payloads-content-negotiation) |
| Get a service's schema, template, defaults | [03 § Endpoints](03-Transaction-API.md#endpoints) · committed full-field JSON in [`definitions/`](../definitions/README.md) |
| **Update an existing record** (Status `"New"` + keys; `"Existing"` is broken) | [03 § Updating an Existing Contract](03-Transaction-API.md#updating-an-existing-contract) |
| **Insert new keyed rows (upsert)** + one-tx-per-POST rule | [03 § Upsert Semantics](03-Transaction-API.md#upsert-semantics-keyed-rows-insert-when-absent) |
| Write through disabled columns/tabs (`IgnoreDisabled`) | [03 § IgnoreDisabled](03-Transaction-API.md#ignoredisabled) — **not a universal unlock; it can report success and write nothing** |
| Contract break tiers refuse to save / "Tab page is disabled" | [03 § VALUES Writes Are Refused on 26.1](03-Transaction-API.md#values-writes-are-refused-on-261) · [14 § entry 8](14-Breaking-Changes.md#8-ignoredisabled-true-reports-success-on-writes-that-write-nothing) |
| Field order silently changing values | [03 § Field Order Matters](03-Transaction-API.md#field-order-matters) |
| Labels vs code_no (`UseCodeValues`, `code_p21`) | [03 § UseCodeValues](03-Transaction-API.md#usecodevalues) |
| Check success properly (HTTP 200 lies; per-tx pass/fail) | [03 § Response Format](03-Transaction-API.md#response-format) · [06 § Transaction API Errors](06-Error-Handling.md#transaction-api-errors) |
| Read a record back / verify a write | [03 § Endpoints — `/transaction/get`](03-Transaction-API.md#endpoints) |
| Long-running / async transactions | [03 § Async Operations](03-Transaction-API.md#async-operations) |
| DynaChange rules & popup suppression for the API user | [03 § DynaChange and Popup Handling](03-Transaction-API.md#dynachange-and-popup-handling) |
| Run a stored procedure via API | [03 § Stored Procedure Executor](03-Transaction-API.md#stored-procedure-executor) |

### By record type

| Task | Recipe | Manual |
|------|--------|--------|
| Create a **sales order** + gotchas (source_loc_id, dates, DynaChange) | [create-sales-order](recipes/create-sales-order.md) | [03 § Create Order](03-Transaction-API.md#create-order) · [03 § Order Service Gotchas](03-Transaction-API.md#order-service-gotchas) |
| Order with an **assembly line** (explode / spawn prod order) | [order-with-assembly](recipes/order-with-assembly.md) | [04 § Sales Order Entry with Assembly Lines](04-Interactive-API.md#sales-order-entry-with-assembly-lines) |
| **Job contract**: create, lines, breaks | — | [03 § JobContractPricing Service](03-Transaction-API.md#jobcontractpricing-service) |
| Job contract: update / add lines / commission costs | [update-contract-lines](recipes/update-contract-lines.md) | [03 § Updating an Existing Contract](03-Transaction-API.md#updating-an-existing-contract) · [03 § Upsert Semantics](03-Transaction-API.md#upsert-semantics-keyed-rows-insert-when-absent) · [03 § Commission Costs](03-Transaction-API.md#commission-costs) |
| Job contract: **bin quantities** | [edit-contract-bins](recipes/edit-contract-bins.md) | [03 § Editing Bin Quantities](03-Transaction-API.md#editing-bin-quantities-on-an-existing-contract) (Interactive fallback: [04 § Tab Unlock Sequences](04-Interactive-API.md#tab-unlock-sequences)) |
| **Assembly / BOM** definition | — | [03 § Assembly Service](03-Transaction-API.md#assembly-service) |
| Item: **primary bin / primary supplier** at a location | [set-primary-bin-supplier](recipes/set-primary-bin-supplier.md) | [03 § Item Service](03-Transaction-API.md#item-service-nested-location-edits) |
| **Create warehouse bins** | [create-bins](recipes/create-bins.md) | [03 § BinLocation Service](03-Transaction-API.md#binlocation-service-creating-bins) |
| **Sales price pages** (codes, breaks, field order) | — | [08 SalesPricePage Codes](08-SalesPricePage-Codes.md) · [08 § Transaction API Alternative](08-SalesPricePage-Codes.md#transaction-api-alternative) |
| **Purchase-side pricing pages** (supplier / item / discount group) | — | [08 § Purchase-Side Pricing Services](08-SalesPricePage-Codes.md#purchase-side-pricing-services) |
| Break fields named differently per service (`calculation_value1` vs `value1`) | — | [08 § Cross-Service Break-Field Names](08-SalesPricePage-Codes.md#cross-service-break-field-names) |
| **Set a carrier tracking number** on a pick ticket (and why not after invoicing) | — | [03 § Shipping Service — Carrier Tracking Number](03-Transaction-API.md#shipping-service-carrier-tracking-number) |
| **Reassign a salesrep** (customer + ship-to) | [reassign-salesrep](recipes/reassign-salesrep.md) | [03 § Payload Anatomy](03-Transaction-API.md#payload-anatomy-types-nesting-and-common-mistakes) |
| **Create a customer** (salesrep_id + default_branch gotchas, no zip→rep cascade) | [create-customer](recipes/create-customer.md) | [03 § Common Services](03-Transaction-API.md#common-services) |
| **Create a requisition PO** (`po_type` 'R'; disabled `po_hdr_po_type`; vendor vs supplier) | [create-requisition-po](recipes/create-requisition-po.md) | [03 § Purchase Order Types](03-Transaction-API.md#purchase-order-types-and-the-disabled-po_hdr_po_type-column) |
| **GL dimensions via API** (voucher services carry them; POs don't) | — | [03 § GL Dimensions in the API](03-Transaction-API.md#gl-dimensions-in-the-api) |
| Customers / vendors / contacts / addresses (simple CRUD) | — | [05 § CRUD Operations](05-Entity-API.md#crud-operations) |
| Read/create **sales orders via REST** (`/api/sales/orders`) | — | [05 § Other REST Endpoint Families](05-Entity-API.md#other-rest-endpoint-families) |
| Inventory items: read / create / update locations | — | [11 § Reading Items](11-Inventory-REST-API.md#reading-items) · [11 § Minimum Create Payload](11-Inventory-REST-API.md#minimum-create-payload) · [11 § Updating Existing Location Fields](11-Inventory-REST-API.md#updating-existing-location-fields) |
| Customer-specific **price + availability** lookup | — | [11 § Pricing Endpoints](11-Inventory-REST-API.md#pricing-endpoints) |
| User-defined tables (UDT) rows | — | [13 § Insert](13-UDT-Service-API.md#insert) · [13 § Update](13-UDT-Service-API.md#update) · [13 § Delete](13-UDT-Service-API.md#delete) — **update/delete need a `row_uid` column; 2026.1-created UDTs don't have one** |
| UDT delete "succeeds" but nothing is deleted | — | [06 § `[0] rows deleted`](06-Error-Handling.md#0-rows-deleted-successfully-a-delete-that-deletes-nothing-20261) · [14 § entry 7](14-Breaking-Changes.md#7-udt-service-updatedelete-cannot-target-rows-in-a-udt-created-on-20261) |
| Bulk-load a UDT from CSV (2026.1+) | — | [13 § Bulk Data API](13-UDT-Service-API.md#bulk-data-api-20261) — CSV upload; **headerless file silently inserts nothing** |

## Drive a window (Interactive API)

| Task | Where |
|------|-------|
| Session → window → change → save lifecycle | [04 § Session Lifecycle](04-Interactive-API.md#session-lifecycle) |
| v2 payload shapes (save body is the bare GUID, etc.) | [04 § v1 vs v2 API Differences](04-Interactive-API.md#v1-vs-v2-api-differences) |
| Find field / tab / datawindow names | [04 § Finding Field Names](04-Interactive-API.md#finding-field-names) · [04 § Window Discovery](04-Interactive-API.md#window-discovery-techniques) |
| Open a window (use `ServiceName` — Name/Title can 400) · map window→service | [04 § Open Window](04-Interactive-API.md#2-open-window) · [04 § Window→Service Discovery](04-Interactive-API.md#8-window-to-service-discovery-frame_menu) |
| **Handle popups / response windows** (Status 3, windowopened) | [04 § Response Windows](04-Interactive-API.md#response-windows) · [04 § Response Window Types](04-Interactive-API.md#response-window-types) |
| Answer a rule-callback dialog ("Item Issues Detected") | [04 § Worked Example](04-Interactive-API.md#worked-example-item-issues-detected-rule-callback) — but fix the data first: [03 § Root Cause and Data Fix](03-Transaction-API.md#item-issues-detected-popup-root-cause-and-data-fix) |
| Fill fields in a popup (`TabName: null`) | [04 § Response Window Handling (Tabless)](04-Interactive-API.md#response-window-handling-tabless-windows) |
| Buttons / tools (`?windowId=`, not `?id=`) | [04 § Running Tools](04-Interactive-API.md#running-tools-buttons) |
| Unlock a disabled tab | [04 § Tab Unlock Sequences](04-Interactive-API.md#tab-unlock-sequences) |
| Row selection traps (sync bug, detail-form rebind, row 0) | [04 § Known Issues and Workarounds](04-Interactive-API.md#known-issues-and-workarounds) |
| Key field silently swallowing later edits | [04 § Key Fields Commit the Cursor](04-Interactive-API.md#key-fields-commit-the-cursor-later-fields-silently-ignored) |
| Verify a save actually persisted | [04 § Verifying Writes](04-Interactive-API.md#verifying-writes-dont-trust-save-status-alone) |
| PO notepad notes (header vs line) | [04 § PurchaseOrder Notepad Writes](04-Interactive-API.md#purchaseorder-notepad-writes-header-vs-line) |
| Bulk/batch interactive work (session reuse, error recovery) | [09 Batch Processing Patterns](09-Batch-Processing-Patterns.md) |
| Intermittent "Unexpected Response Window" in production | [07 Session Pool Troubleshooting](07-Session-Pool-Troubleshooting.md) |

## Production & manufacturing

| Task | Where |
|------|-------|
| Service catalog & schemas (ProductionOrder, TimeEntry, …) | [12 § Available Services](12-Production-Labor-API.md#available-services) |
| Assembly behavior flags (prod-order vs kit vs build-to-stock) | [12 § Assembly Behavior Flags](12-Production-Labor-API.md#assembly-behavior-flags) |
| **Full runbook: create → print → confirm → complete → ship** | [recipe: production-order-runbook](recipes/production-order-runbook.md) · [12 § Production Order Lifecycle](12-Production-Labor-API.md#production-order-lifecycle-end-to-end) |
| Pick ticket won't generate (make loc vs stock loc) | [12 § Printing the Pick Ticket](12-Production-Labor-API.md#printing-the-pick-ticket-and-form) · [03 § m_picktickets example](03-Transaction-API.md#example-generate-a-production-order-pick-ticket-m_picktickets) |
| Confirm a pick (shell-confirm trap — use Interactive) | [12 § Confirming the Pick](12-Production-Labor-API.md#confirming-the-pick-use-the-interactive-api) |
| Complete / production receipt (+ per-component cost override) | [12 § Completing the Production Order](12-Production-Labor-API.md#completing-the-production-order-production-receipt) |
| Record labor hours | [recipe: record-labor-time](recipes/record-labor-time.md) · [12 § Recording Labor Hours](12-Production-Labor-API.md#recording-labor-hours-timeentry-service) · [12 § Time Entry Against a Production Order](12-Production-Labor-API.md#time-entry-against-a-production-order-quick-time-entry) |
| Ship + invoice | [12 § Shipping and Invoicing](12-Production-Labor-API.md#shipping-and-invoicing-the-linked-sales-order) |
| Inventory write-off / adjustment | [recipe: inventory-adjustment](recipes/inventory-adjustment.md) · [12 § Inventory Adjustment](12-Production-Labor-API.md#inventory-adjustment-write-offs) |
| Why COGS doesn't match the receipt | [12 § Cost Model](12-Production-Labor-API.md#cost-model-know-this-before-trusting-cogs) |

## Documents & reports (PDF)

| Task | Where |
|------|-------|
| Generate any `m_*` report as PDF | [recipe: generate-pick-ticket-pdf](recipes/generate-pick-ticket-pdf.md) · [03 § PDF Report Generation](03-Transaction-API.md#pdf-report-generation) |
| Discover callable report names (hidden from /services) | [03 § PDF Report Generation](03-Transaction-API.md#pdf-report-generation) (Discovery note) |
| Production pick ticket at a specific location | [03 § m_picktickets example](03-Transaction-API.md#example-generate-a-production-order-pick-ticket-m_picktickets) |
| PDFs from print flags on a normal transaction | [03 § PDFs from the /transaction endpoint](03-Transaction-API.md#pdfs-from-the-transaction-endpoint-print-flags) |

## When something breaks

| Task | Where |
|------|-------|
| **Upgrading P21? What breaks between versions** | [14 Breaking Changes](14-Breaking-Changes.md) — 2026.1 (Accept-header 500, ghost sessions, non-atomic batched changes) · 25.2 (DatawindowName) |
| Which middleware build am I on? | [14 § Reading the middleware version](14-Breaking-Changes.md#reading-the-middleware-version) — no version endpoint; it rides the session-create response |
| Error catalog by API | [06 Error Handling](06-Error-Handling.md) (per-API sections) |
| Quick symptom → cause table | [06 § Common Issues Quick Reference](06-Error-Handling.md#common-issues-quick-reference) |
| Auth failures | [06 § Authentication Errors](06-Error-Handling.md#authentication-errors) |
| Intermittent interactive failures under load | [07 Session Pool Troubleshooting](07-Session-Pool-Troubleshooting.md) |
| What changed in these docs recently | [10 Changelog](10-Changelog.md) |

---

## Doc inventory (what each file is)

| Doc | Scope | Size |
|-----|-------|------|
| [00-Authentication](00-Authentication.md) | Tokens (v2/consumer key), permissions, UI server URL | large |
| [01-API-Selection-Guide](01-API-Selection-Guide.md) | Which API for which job | small — read whole |
| [02-OData-API](02-OData-API.md) | Read-only queries | large |
| [03-Transaction-API](03-Transaction-API.md) | Stateless create/update + service reference + PDF reports | very large — use anchors |
| [04-Interactive-API](04-Interactive-API.md) | Stateful window driving, popups, traps | very large — use anchors |
| [05-Entity-API](05-Entity-API.md) | REST CRUD on 4 entities | medium |
| [06-Error-Handling](06-Error-Handling.md) | Errors across all APIs | large |
| [07-Session-Pool-Troubleshooting](07-Session-Pool-Troubleshooting.md) | One deep-dive: session pool contamination | medium — single topic |
| [08-SalesPricePage-Codes](08-SalesPricePage-Codes.md) | SalesPricePage field codes/order | medium — single service |
| [09-Batch-Processing-Patterns](09-Batch-Processing-Patterns.md) | Interactive bulk patterns + async client | very large |
| [10-Changelog](10-Changelog.md) | Doc change history | small |
| [11-Inventory-REST-API](11-Inventory-REST-API.md) | `/api/inventory/parts` read/append/update | large |
| [12-Production-Labor-API](12-Production-Labor-API.md) | Production services + end-to-end lifecycle | large |
| [13-UDT-Service-API](13-UDT-Service-API.md) | User-defined table CRUD | large |
| [14-Breaking-Changes](14-Breaking-Changes.md) | P21 version breaking-change registry (check before upgrading) | small — read whole |
| [`definitions/`](../definitions/README.md) | Full-field service definition JSONs (every DataElement, field, key, label + payload template) | load one file per service |
