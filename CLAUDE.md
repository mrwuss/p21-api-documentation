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
| **Transaction API** | Stateless bulk data manipulation | Bulk creates, keyed updates/upserts, external integrations | Working |
| **Interactive API** | Stateful window interactions with business logic | Complex workflows, validation needed | Working |
| **Entity API** | REST CRUD — `/api/entity/` (4 entities) plus other endpoint families (e.g. `/api/sales/orders`) | Simple record operations on 4 entities | Working (`/api/entity/`) |
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
│   ├── 14-Breaking-Changes.md
│   └── html/                    # Generated HTML versions
│
├── definitions/                 # Sanitized full-field service definition JSONs (schema library)
│
├── examples/
│   ├── python/                  # Python examples
│   │   ├── common/              # Shared auth/config (used by every script)
│   │   ├── odata/ transaction/ interactive/ entity/ production/
│   │   └── recipes/             # End-to-end recipe scripts (dry-run by default)
│   ├── csharp/                  # C# console app examples (P21Examples.sln)
│   │   ├── Common/              # Shared library (auth, config, client)
│   │   ├── OData/ Transaction/ Interactive/ Entity/ Production/
│   │   └── Recipes/             # End-to-end recipe classes (EXECUTE-gated)
│   └── payloads/                # Standalone request payloads, validator-verified
│       ├── json/                # One .json per documented task
│       └── xml/                 # DataContract-correct XML counterparts
│
├── postman/                     # Postman collection for all APIs
│
└── scripts/                     # Repo tooling (NOT API examples)
    ├── fetch_definitions.py     # Fetch + sanitize service definitions into definitions/
    ├── validate_payload.py      # Offline payload validator (JSON/XML shape + schema checks)
    ├── check_anchors.py         # Validate internal doc links against the generated HTML
    ├── test_client.py           # Smoke-test client against a live tenant
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
python examples/python/odata/01_basic_query.py
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `P21_BASE_URL` | Yes | P21 server URL (e.g., `https://play.p21server.com`) |
| `P21_USERNAME` | Yes* | P21 API username |
| `P21_PASSWORD` | Yes* | P21 API password |
| `P21_CONSUMER_KEY` | No | Consumer key GUID (alternative to username/password) |
| `P21_CONSUMER_USERNAME` | No | P21 username for consumer key auth (required for Interactive API) |
| `P21_VERIFY_SSL` | No | Set `true` to verify TLS certificates; example ships `false` for test tenants |

*Not required when using consumer key authentication. See [Authentication docs](docs/00-Authentication.md).

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

## Known Issues & Verified Hazards — routed, not stored

> **API behavior facts live in `docs/`, never in this file** — one source of truth prevents drift. This table only routes. When you verify something new, write it into the linked doc (and add an INDEX.md row); do not restate it here.

| Hazard / behavior | Where it lives |
|---|---|
| **2026.1 breaking changes** — `SessionId`→`Id`, sequential fail-fast `/v2/change`, silent-false-success loads, UDT delete no-op, `IgnoreDisabled` false success, bad-`DatawindowName` eats the next request. **Accept-header empty 500 + ghost sessions are FIXED in 26.1.5940.0** and kept as resolved entries | [docs/14-Breaking-Changes.md](docs/14-Breaking-Changes.md) (version-indexed registry; **which entries apply depends on the build** — check before touching Interactive code) |
| **An empty HTTP 500 on the interactive surface no longer means the `Accept` header** — on current builds it means a bad `DatawindowName` on the *previous* request burned this one | [docs/14 entry 9](docs/14-Breaking-Changes.md#9-a-bad-datawindowname-eats-the-next-request-on-that-window-empty-http-500) |
| Transaction `Status` — **`"New"` is the only string the enum accepts** (case-insensitive); `"Existing"`/`"Update"`/etc. are HTTP 400 on 5940.0, HTTP 500 on older builds; integers bind silently, never send one | [docs/03 § Status: "New" is the only value](docs/03-Transaction-API.md#status-new-is-the-only-value-the-enum-accepts) |
| **P21 supports both .NET and .NET Framework for business rules, for now** — the middleware's own .NET 10 move did not drag rule code with it; client runtime is unconstrained (`net8.0`+) | [docs/14 § The middleware runtime](docs/14-Breaking-Changes.md#the-middleware-runtime-and-what-it-does-not-dictate) |
| **25.2** — `DatawindowName` required in change requests | [docs/14 § 25.2](docs/14-Breaking-Changes.md#p21-252) |
| `IgnoreDisabled: true` reports success on writes that write nothing (3 services confirmed) — never trust a `Passed` under this flag, read the record back | [docs/14 entry 8](docs/14-Breaking-Changes.md#8-ignoredisabled-true-reports-success-on-writes-that-write-nothing) · [docs/03 § IgnoreDisabled](docs/03-Transaction-API.md#ignoredisabled) |
| Transaction `Status: "Existing"` HTTP 500 (platform-wide); updates go through keyed `Status: "New"` upserts | [docs/03 § Upsert Semantics](docs/03-Transaction-API.md#upsert-semantics-keyed-rows-insert-when-absent) · [§ Updating an Existing Contract](docs/03-Transaction-API.md#updating-an-existing-contract) |
| `Keys` row collapse (same-key rows fold, last value wins, `Succeeded: 1`) and over-keying turning updates into inserts | [docs/03 § Keys — Row Identity and the Collapse Trap](docs/03-Transaction-API.md#keys-row-identity-and-the-collapse-trap) |
| Reading records / cloning via `POST /transaction/get`; the three discovery endpoints (`definition` / `defaults` / `basics`) | [docs/03 § Reading One Record](docs/03-Transaction-API.md#reading-one-record-post-transactionget) · [§ Endpoints](docs/03-Transaction-API.md#endpoints) |
| **Notes: three surfaces, three answers** — `/transaction` refuses everywhere; `/commands` writes the standalone `*Notepad` services (verified); Interactive writes both order and standalone notes | [docs/03 § Limitations](docs/03-Transaction-API.md#limitations) (comparison table) · [docs/04 § Sales Order Notepad Writes](docs/04-Interactive-API.md#sales-order-notepad-writes-header-vs-line) |
| `/api/v2/commands` request shape + `Action` codes (sanctioned path for commands-only services) | [docs/03 § Commands Endpoint](docs/03-Transaction-API.md#commands-endpoint) |
| **OData is v4** (not v3), no server-driven paging; second surface `/data/erp/views/v1` does single-row key lookups | [docs/02 § Protocol version](docs/02-OData-API.md#protocol-version) · [docs/02 § The other OData surface](docs/02-OData-API.md#the-other-odata-surface-dataerpviewsv1) |
| Which REST families a tenant exposes (`apiref.aspx`, per-family `/help`) | [docs/05 § Discovering what your tenant actually exposes](docs/05-Entity-API.md#discovering-what-your-tenant-actually-exposes) |
| Application Security settings that gate API access (*Access to SOA Admin Page*, audit-trail user override) | [docs/00 § Application Security settings](docs/00-Authentication.md#application-security-settings-that-affect-api-access) |
| **Router URL needs its trailing slash** — `/api/ui/router/v1?urlType=external` 307s, and .NET `HttpClient` **strips `Authorization` on any redirect**, so the call 401s with a perfectly good token | [docs/00 § UI Server URL](docs/00-Authentication.md#ui-server-url) · [docs/06 § 401 Authorization header was not present](docs/06-Error-Handling.md#401-authorization-header-was-not-present-or-bearer-was-missing) |
| Lowercase `item_id` accepted by TAPI, crashes the client on open — uppercase in code, never reproduce to test | [docs/03 § Item Service Gotchas](docs/03-Transaction-API.md#item-service-gotchas) |
| **Buy side**: `PurchaseOrder` create · `PurchaseOrderReceipt` (TAPI works when every line has a usable primary bin) · `ConvertPOToVoucher` — full build→receive→vouch verified | [docs/03 § PurchaseOrder](docs/03-Transaction-API.md#purchaseorder-service-creating-a-po) · [§ Receipt](docs/03-Transaction-API.md#purchaseorderreceipt-service-receiving-a-po) · [§ Voucher](docs/03-Transaction-API.md#convertpotovoucher-service-vouching-a-receipt) |
| `Order` refuses **RMAs** — use the `RMA` service (same form, keyed `order_no`) | [docs/03 § RMA Service](docs/03-Transaction-API.md#rma-service-orders-the-order-service-refuses) |
| **Grid deletes are not all `delete_flag`** — the Customer salesrep grid deletes via `row_status_flag: "Delete"` (label, not the `700` code); soft delete, so both OData *and* `/transaction/get` still return the row | [docs/03 § Removing a Salesrep Grid Row](docs/03-Transaction-API.md#customer-service-removing-a-salesrep-grid-row) |
| What `Failed` guarantees (Transaction atomic; Transactions in one POST are **not**) and why `Required`/`basics` mislead | [docs/03 § What Failed actually guarantees](docs/03-Transaction-API.md#what-failed-actually-guarantees) · [§ What Required actually means](docs/03-Transaction-API.md#what-required-actually-means) |
| Driving an **in-window wizard** (direct-ship PO) — commits at `cb_next` | [docs/04 § Driving an In-Window Wizard](docs/04-Interactive-API.md#driving-an-in-window-wizard-direct-ship-po-generation) |
| Response windows: no answer-a-dialog endpoint, `w_message` auto-answered (GL-overwrite trap), drivable popups via `/tools`, editable popups via `TabName: null` | [docs/04 § Response Windows](docs/04-Interactive-API.md#response-windows) · [§ Response Window Types](docs/04-Interactive-API.md#response-window-types) |
| `ResultStatus` enum (`None=0, Success=1, Failure=2, Blocked=3` — 2 is Failure, not Blocked) | [docs/04 § Response Windows](docs/04-Interactive-API.md#response-windows) |
| `inv_loc` read/append/update paths (all resolved); Item-window GL fields stay read-only | [docs/11 § Updating Existing Location Fields](docs/11-Inventory-REST-API.md#updating-existing-location-fields) |
| UDT Service quirks (errorMessage/errorNo, SQL-keyword filter, row_uid conditions) and the 2026.1 Bulk Data API (headerless-CSV silent zero-insert, scale rounding) | [docs/13-UDT-Service-API.md](docs/13-UDT-Service-API.md) · [§ Bulk Data API](docs/13-UDT-Service-API.md#bulk-data-api-20261) |

---

*Last updated: 2026-08-26*
