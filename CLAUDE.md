# Project: P21 API Documentation

> Comprehensive documentation and working examples for all P21 APIs.

---

## Quick Context

This project provides developer-focused documentation for Prophet 21's integration APIs. All content is based on official Epicor SDK documentation and verified working implementations - no guesses or assumptions.

---

## APIs Covered

| API | Purpose | Use When | Status |
|-----|---------|----------|--------|
| **OData** | Read-only data access via standard OData protocol | Quick reads, reporting, lookups | Working |
| **Transaction API** | Stateless bulk data manipulation | Bulk creates, external integrations | Working |
| **Interactive API** | Stateful window interactions with business logic | Complex workflows, validation needed | Working |
| **Entity API** | CRUD on domain objects (customer, vendor, contact, address) | Simple record operations on 4 entities | Working (`/api/entity/`) |
| **Inventory REST API** | CRUD on inventory items, multi-company workflows | Item reads, appending locations/suppliers | Working (`/api/inventory/parts`) |

---

## Project Structure

```
p21-api-documentation/
├── docs/
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
│   └── html/                    # Generated HTML versions
│
└── scripts/
    ├── common/                  # Shared auth/config
    ├── odata/                   # OData examples
    ├── transaction/             # Transaction API examples
    ├── interactive/             # Interactive API examples
    ├── entity/                  # Entity API examples
    └── generate_html.py         # MD to HTML converter
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

### Interactive API - ResultStatus Enum (February 2026)

**Official status codes** from `P21.UI.Service.Model.Interactive.V2.ResultWrapper`:
```text
None=0, Success=1, Failure=2, Blocked=3
```

**Important**: Status `2` is **Failure**, not Blocked. Earlier versions of `09-Batch-Processing-Patterns.md` incorrectly mapped `2=Blocked, 3=Dialog` — this has been corrected.

The API returns Status as integers. String values (`"Success"`, `"Failure"`, `"Blocked"`) may appear in some serialization contexts — handle both.

---

### inv_loc Write Access — Partially Resolved (February 2026)

**Appending new `inv_loc` records** (resolved):
- The **Inventory REST API** `PUT /api/inventory/parts/{ItemId}` can append new `inv_loc` and `inventory_supplier` records
- Use the GET → Append → PUT pattern: retrieve item with `extendedproperties=*`, add new Location/Supplier to the lists, PUT back
- P21 validates appended records through full business logic (company validation, GL account checks)
- See [Inventory REST API docs](docs/11-Inventory-REST-API.md) for details

**Reading `inv_loc` data** (resolved):
- `GET /api/inventory/parts/{ItemId}?extendedproperties=*` returns full `inv_loc` data including GL accounts, product groups, and costs
- OData also provides read access to `inv_loc` table

**Updating existing `inv_loc` fields** (still unresolved):

| API | Result |
|-----|--------|
| **Interactive API (Item window)** | GL account fields on TABPAGE_24 are **read-only** - cannot be modified |
| **Transaction API** | No `InvLoc` service exists. Item service returns 500 errors for inv_loc updates |
| **Inventory REST API** | Can append new records, but modifying fields on existing `inv_loc` records not verified |

**Impact**: Cannot programmatically:
1. Change `product_group_id` on existing locations without triggering GL account dialog
2. Restore GL accounts after they've been changed by the dialog
3. Update individual fields on existing `inv_loc` records

**Workarounds**:
1. **Inventory REST API** - Can append new `inv_loc` records (multi-company workflows)
2. **Direct SQL** - Update `inv_loc` table directly (bypasses business logic, use with caution)
3. **Epicor Support** - Request response window endpoint documentation

---

*Last updated: 2026-02-17*
