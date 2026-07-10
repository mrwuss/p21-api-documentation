# Project: P21 API Documentation

> Comprehensive documentation and working examples for all P21 APIs.

---

## Quick Context

This project provides developer-focused documentation for Prophet 21's integration APIs. All content is based on official Epicor SDK documentation and verified working implementations - no guesses or assumptions.

## How to Navigate (read this before opening docs)

The numbered docs are the deep *manual* — several exceed 1,000 lines. **Do not read a whole doc for one task.** The routing flow is:

1. Read this file (you're here).
2. Open **[docs/INDEX.md](docs/INDEX.md)** — a task → section-anchor map.
3. Load **only the linked section(s)** your task needs.

When editing docs, keep INDEX.md's anchors in sync (renaming a heading breaks its index entry), and add an index row for any new task-worthy section.

---

## APIs Covered

| API | Purpose | Use When | Status |
|-----|---------|----------|--------|
| **OData** | Read-only data access via standard OData protocol | Quick reads, reporting, lookups | Working |
| **Transaction API** | Stateless bulk data manipulation | Bulk creates, external integrations | Working |
| **Interactive API** | Stateful window interactions with business logic | Complex workflows, validation needed | Working |
| **Entity API** | CRUD on domain objects (customer, vendor, contact, address) | Simple record operations on 4 entities | Working (`/api/entity/`) |
| **Inventory REST API** | CRUD on inventory items, multi-company workflows | Item reads, appending locations/suppliers | Working (`/api/inventory/parts`) |
| **Production & Labor** | Production orders, labor hours, time entry | Manufacturing workflows, labor tracking | Working (Transaction + Interactive) |
| **UDT Service API** | CRUD on user-defined tables | Custom table maintenance | Working (`/udtservice/api/udtdata/`) |

---

## Project Structure

```
p21-api-documentation/
├── docs/
│   ├── INDEX.md                 # Task → section routing map (start here)
│   ├── recipes/                 # Self-contained copy-and-run task pages (one task = one page)
│   ├── 00-Authentication.md
│   ├── 01-API-Selection-Guide.md
│   ├── 02-OData-API.md
│   ├── 03-Transaction-API.md
│   ├── 04-Interactive-API.md
│   ├── 05-Entity-API.md
│   ├── 06-Error-Handling.md
│   ├── 07-Session-Pool-Troubleshooting.md
│   ├── 08-SalesPricePage-Codes.md
│   ├── 09-Batch-Processing-Patterns.md
│   ├── 10-Changelog.md
│   ├── 11-Inventory-REST-API.md
│   ├── 12-Production-Labor-API.md
│   ├── 13-UDT-Service-API.md
│   └── html/                    # Generated HTML versions
│
├── definitions/                 # Sanitized full-field service definition JSONs (schema library)
│
├── examples/
│   └── csharp/                  # C# console app examples
│       ├── Common/              # Shared library (auth, config, client)
│       ├── OData/               # OData API examples
│       ├── Transaction/         # Transaction API examples
│       ├── Interactive/         # Interactive API examples
│       ├── Entity/              # Entity API examples
│       └── Production/          # Production & Labor examples
│
└── scripts/
    ├── common/                  # Shared auth/config (Python)
    ├── odata/                   # OData examples (Python)
    ├── transaction/             # Transaction API examples (Python)
    ├── interactive/             # Interactive API examples (Python)
    ├── entity/                  # Entity API examples (Python)
    ├── production/              # Production & Labor examples (Python)
    ├── fetch_definitions.py     # Fetch + sanitize service definitions into definitions/
    ├── validate_payload.py      # Offline payload validator (JSON/XML shape + schema checks)
    └── generate_html.py         # MD to HTML converter (supports tabbed code blocks)
```

---

## Running Scripts

```bash
# Setup
cp .env.example .env
# Edit .env with P21 credentials

# Install dependencies
pip install -r requirements.txt

# Run any example
python scripts/odata/01_basic_query.py
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `P21_BASE_URL` | Yes | P21 server URL (e.g., `https://play.p21server.com`) |
| `P21_USERNAME` | Yes | P21 API username |
| `P21_PASSWORD` | Yes | P21 API password |

---

## Content Sources

All documentation is derived from:
1. **Official SDK Docs**: Epicor P21 SDK documentation
2. **Working Code**: Verified production implementations
3. **Actual Testing**: Verified against P21 test environments

---

## Key Principles

- **Facts only** - No guesses about undocumented behavior
- **Verified examples** - All code runs without errors
- **Real payloads** - Request/response examples from actual API calls
- **Known issues documented** - Session pool contamination, async limitations

---

## Known Issues

### Interactive API - Response Window Limitation (January 2026)

**Problem**: There is no documented endpoint to respond to message box dialogs (w_message windows) programmatically.

**Impact**: When an operation triggers a dialog (like changing `product_group_id`), you cannot answer "No" via the API. With `ResponseWindowHandlingEnabled: false`, dialogs are auto-answered with the default (usually "Yes").

**Specific Case**: Changing `product_group_id` on `inv_loc` triggers a dialog asking to update GL accounts. The default "Yes" response overwrites location-specific GL, revenue, and COS account fields.

**Tested endpoints that do NOT work**:
- `PUT /api/ui/interactive/v2/responsewindow` → 404
- `PUT /api/ui/interactive/v2/responsewindows` → 404
- `DELETE /api/ui/interactive/v2/window?button=No` → 400
- `POST /api/ui/interactive/v2/button` → 404

**Workaround (February 2026)**: For non-message-box response windows (e.g., `w_inventory_scan_lookup`, `w_popup_processing_msg`), discover available buttons via `GET /api/ui/interactive/v2/tools?windowId={id}` and click them via `POST /api/ui/interactive/v2/tools`. Verified working on `w_inventory_scan_lookup` (returns `cb_ok`, `cb_cancel`, etc.). Message box dialogs (`w_message`) remain unresolved.

**Editable response windows (July 2026)**: Form-style response windows are fully drivable when the session has `ResponseWindowHandlingEnabled: true` — the triggering call returns `Status: 3` with a `windowopened` event carrying the popup's window ID; edit its fields with `TabName: null` and click its tools. Verified end-to-end on `w_notepad_response_lite` (PurchaseOrder notepad — see [Interactive API guide](docs/04-Interactive-API.md#purchaseorder-notepad-writes-header-vs-line)). With `ResponseWindowHandlingEnabled: false`, tools that open such windows fail with HTTP 400 "Unexpected response window".

### Interactive API - ResultStatus Enum (February 2026)

**Official status codes** from `P21.UI.Service.Model.Interactive.V2.ResultWrapper`:
```text
None=0, Success=1, Failure=2, Blocked=3
```

**Important**: Status `2` is **Failure**, not Blocked. Earlier versions of `09-Batch-Processing-Patterns.md` incorrectly mapped `2=Blocked, 3=Dialog` — this has been corrected.

The API returns Status as integers. String values (`"Success"`, `"Failure"`, `"Blocked"`) may appear in some serialization contexts — handle both.

### Interactive API - DatawindowName Required in 25.2+ (February 2026)

**Breaking Change**: P21 25.2 changed window data structures so that `DatawindowName` is now **required** in change requests. The 3-parameter form (TabName + FieldName + Value) no longer works — you must include `DatawindowName`.

**Affected windows** (reported): Item, PO Receiving Group, Delivery List, Group Pick Ticket. Likely affects other windows as well.

**C# SDK impact**:
```text
// Broken in 25.2+:
window.ChangeData("Criteria", "po_criteria_id", "20");

// Fixed — include DatawindowName:
window.ChangeData("Criteria", "tp_1_dw_1", "po_criteria_id", "20");
```

**REST API impact**: Always include `DatawindowName` in v2 change request payloads:
```json
{"TabName": "FORM", "DatawindowName": "form", "FieldName": "field", "Value": "value"}
```

**Source**: Community forum reports confirmed by multiple users after 25.2 upgrade.

---

### inv_loc Write Access — Resolved (April 2026)

**All three operations now have verified API paths:**

| Operation | API | Status |
|-----------|-----|--------|
| **Appending new `inv_loc` records** | Inventory REST API `PUT /api/inventory/parts/{ItemId}` — GET → Append → PUT pattern | Resolved (Feb 2026) |
| **Reading `inv_loc` data** | Inventory REST API `GET /api/inventory/parts/{ItemId}?extendedproperties=*` or OData | Resolved (Feb 2026) |
| **Updating existing `inv_loc` fields** | Inventory REST API `PUT /api/inventory/parts/{ItemId}` — GET → Modify → PUT pattern | **Resolved (Apr 2026)** |

**Updating existing fields** — verified working: Sellable, ProductGroupId, PurchaseDiscountGroup, SalesDiscountGroup. P21 validates changed values (e.g., invalid ProductGroupId returns "Product group ID does not exist for this company ID"). See [Inventory REST API docs](docs/11-Inventory-REST-API.md) for details.

**Remaining limitation**: Interactive API Item window GL account fields on TABPAGE_24 are still read-only. The Inventory REST API is the recommended path for `inv_loc` modifications.

### Transaction API — Status "Existing" Platform Bug (April 2026)

`POST /api/v2/transaction` with `Status: "Existing"` returns HTTP 500 `NullReferenceException` at `ToInternalBeSpecification`. This is a **platform-wide bug**, not service-specific — confirmed on JobContractPricing, Assembly, SalesPricePage, and TimeEntry.

**Retrieval**: Use `POST /api/v2/transaction/get` with `TransactionStates` to read existing records.

**Updates**: `Status: "Existing"` is *unused*, not a write ban. For JobContractPricing the verified update path is `Status: "New"` with FORM key fields (`company_id`, `contract_no`, `job_no`, `end_date`) in `Edits` and List `Keys` identifying the row by `item_id` — see [JobContractPricing > Updating an Existing Contract](docs/03-Transaction-API.md#updating-an-existing-contract) (Fixes #44, May 2026). Other services (Assembly, SalesPricePage, TimeEntry) are untested but likely follow the same pattern; the Interactive API remains a fallback.

**Upserts (July 2026)**: keyed `Status: "New"` List rows are an upsert — update when the key matches, **insert a new row when it doesn't** (verified: 81 new JobContractPricing lines in one run, DB-confirmed; credit Alex Westemeier). Gotchas: order `pricing_method` before `price` in Edits (cascade silently zeroes the price); one transaction per POST when inserts re-save a shared FORM header (optimistic-concurrency collisions + duplicate `line_no`); header saves validate `end_date` ≥ today. `IgnoreDisabled: true` (payload top level ONLY — silently ignored inside a Transaction object) unlocks disabled columns and tabs, e.g. contract BINS quantities and JOBPRICECOST commission fields.

---

*Last updated: 2026-07-10*
