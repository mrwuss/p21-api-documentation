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
| **Entity API** | Simple CRUD on business objects | Basic record operations | **Not working** (Dec 2025) |

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

**Status**: Unresolved. Need to contact Epicor support for response window endpoint documentation or alternative approach.

---

### No Direct inv_loc API Access (January 2026)

**Problem**: There is no API that allows direct updates to `inv_loc` records without going through the Item window.

**APIs Tested**:

| API | Result |
|-----|--------|
| **Interactive API (Item window)** | GL account fields on TABPAGE_24 are **read-only** - cannot be modified |
| **Transaction API** | No `InvLoc` service exists. Item service returns 500 errors for inv_loc updates |
| **OData API** | Read-only - no write support |
| **Entity API** | Not working (Dec 2025) |

**Transaction API Findings**:
- No `InvLoc`, `InventoryLocation`, or `ItemLocation` service exists
- The `Item` service definition shows `inv_loc_detail` and `inv_loc_accounts` DataElements, but they are designed for **creating** new items, not updating existing inv_loc records
- Attempting to update existing inv_loc via Transaction API returns `NullReferenceException`
- Async endpoint gets stuck on status "Active" indefinitely

**Impact**: Cannot programmatically:
1. Change `product_group_id` without triggering GL account dialog
2. Restore GL accounts after they've been changed by the dialog
3. Update inv_loc fields independently of the Item window

**Potential Workarounds** (not verified):
1. **Direct SQL** - Update inv_loc table directly (bypasses business logic, use with caution)
2. **Epicor Support** - Request response window endpoint documentation
3. **Custom P21 Development** - Create a custom window/service for inv_loc updates

---

*Last updated: 2026-01-18*
