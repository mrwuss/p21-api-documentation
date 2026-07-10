# Changelog

> **Disclaimer:** This is unofficial, community-created documentation for Epicor Prophet 21 APIs. It is not affiliated with, endorsed by, or supported by Epicor Software Corporation. All product names, trademarks, and registered trademarks are property of their respective owners. Use at your own risk.

---

All notable changes to this documentation project are listed below, grouped by date. This project uses [Conventional Commits](https://www.conventionalcommits.org/).

---

## 2026-07-10 — v1.1.0

Example-layout reorg: the repo now serves all four consumption styles symmetrically — Python, C#, JSON, XML.

- **refactor:** Python examples moved from `scripts/` to **`examples/python/`** (clean git renames) for symmetry with `examples/csharp/`; `scripts/` now holds repo tooling only (`generate_html.py`, `fetch_definitions.py`, `validate_payload.py`). All path references updated across docs, recipe pages, README, CLAUDE.md, C# header comments, and `.gitignore`; new `examples/python/README.md` mirrors the C# one — Fixes #87 — *@mrwuss*
- **feat:** New **`examples/payloads/`** library — 11 JSON + 9 XML standalone, copy-ready request bodies for the documented tasks, generated from one source of truth (the XML can never drift out of DataContract element order) and **every file machine-verified** with `scripts/validate_payload.py`. Report (`pdfreport`) payloads ship JSON-only pending XML verification of that endpoint. Recipe pages link their payload files alongside the end-to-end code files — Fixes #87 — *@mrwuss*
- **feat:** `validate_payload.py` now recognizes `POST /api/v2/transaction/get` request bodies (`ServiceName`/`TransactionStates` shape with object-style `Keys`) — *@mrwuss*

## 2026-07-10 — v1.0.0

First tagged release. This wave cross-checked the docs against a community process playbook — every disputed claim was live-verified against a 25.2 test tenant — and restructured the repo for progressive disclosure: task routing, a schema library, a recipes cookbook, end-to-end example files, and payload-correctness tooling. Verified findings credit: *[Alex Westemeier](https://github.com/AWestemeier)*.

**Corrections (our docs were wrong):**

- **fix:** Report-service discovery — `GET /api/v2/services?type=report` returns an **empty list**, not the report services; the `m_*` services are hidden from `/api/v2/services` entirely (exactly 299 transaction objects) but remain fully callable via `definition`/`defaults`/`pdfreport`. Documented the definition-probe and `window_x_menu` menu-leaf discovery paths. Also: `GET /v2/tools?id=` returns HTTP **400** (not 500), and the router endpoint without a trailing slash can respond **307** (breaks non-redirect-following clients) — all verified live — Fixes #54 — *[Alex Westemeier](https://github.com/AWestemeier), @mrwuss*
- **fix:** API Selection Guide no longer steers all updates to the Interactive API — `Status: "New"` + keyed rows is a verified Transaction API update path and an **upsert** (inserts when the key doesn't match; 81 lines added in one verified run). Related JobContractPricing corrections: commission costs ARE writable with `IgnoreDisabled: true` (previously documented as Interactive-only); `end_date >= today` header validation; one-transaction-per-POST rule for line inserts (header optimistic-concurrency collisions + duplicate `line_no`); `pricing_method` must precede `price` (silent $0 line). New `IgnoreDisabled` section: unlocks disabled columns AND disabled sub-tabs (contract BINS), top-level placement only (silently ignored inside a Transaction) — Fixes #56 — *[Alex Westemeier](https://github.com/AWestemeier), @mrwuss*
- **fix:** Reconciled the April 2026 "form-type response windows are dismiss-only" limitation with the July 2026 `TabName: null` editable-response-window finding — the earlier tests addressed popup fields with `TabName: "FORM"`; retry with `TabName: null` before concluding a popup is dismiss-only — Fixes #68 — *@mrwuss*
- **fix(site):** `docs/INDEX.md` rendered to `INDEX.html`, which on case-insensitive filesystems is the same file as the landing page `index.html` — the Task Index HTML was silently clobbered every build and its sidebar links 404'd on the published site. The generator now emits it as `task-index.html` — Fixes #84 — *@mrwuss*
- Not adopted after testing: the community claim that `company_id` is a disabled column on the JobContractPricing FORM did **not** reproduce (header saves pass with it included) — the documented #44 update path stands.

**New verified content:**

- **docs:** PDF report generation expansion — the wrong-endpoint trap (`/api/v2/transaction` accepts `m_*` payloads, returns `Succeeded`, emits nothing), per-service `UseCodeValues` differences (`m_picktickets` requires `true` + code values; `false` returns HTTP 500), a worked `m_picktickets` example (creates the pick-ticket record at the requested location AND returns the PDF; `printed='Y'` prerequisite), and print flags on `/transaction` returning PDFs at `Results.Transactions[].Documents[]` with the make-location limitation — Fixes #58 — *[Alex Westemeier](https://github.com/AWestemeier), @mrwuss*
- **docs:** Order service — `source_loc_id` effectively required (tax-jurisdiction error), `requested_date` must follow `order_date`, DynaChange prompts auto-answered with the default silently kill lines; new Interactive API "Sales Order Entry with Assembly Lines" flow (assembly prompt `cb_1`, date-cascade `w_response_common` on new orders, `taker` defaults to the API user, quickmode bypasses the assembly prompt) — Fixes #60 — *[Alex Westemeier](https://github.com/AWestemeier), @mrwuss*
- **docs:** Item service nested-element recipes — primary bin (Form→List→Form) and primary supplier (Form→List→List) with the write-flag vs read-field distinction and the **silent no-op** when the supplier lacks a location-level row; "Item Issues Detected" rule-callback answering (`cb_1`, retrieve-time popups); the detail-form `select_row` trap — Fixes #62 — *[Alex Westemeier](https://github.com/AWestemeier), @mrwuss*
- **docs:** BinLocation bulk bin creation — three-field keyed create, mandatory top-level `IgnoreDisabled`, codes-not-uids, `ON`/`OFF` ↔ `Y`/`N` flag conversion, clone-a-twin practice, `p21_view_bin` read-back — Fixes #64 — *[Alex Westemeier](https://github.com/AWestemeier), @mrwuss*
- **docs:** Production Order Lifecycle (end-to-end) — stock netting on sales-order auto-create, make-location pick-ticket limitation, labor-before-print timing, the **shell-confirm trap** (a bare Transaction API confirm flips status/`qty_confirmed` but `qty_applied=0` and moves no stock — confirm interactively), completion mechanics (separate `bin_cd`/`unit_quantity` calls, per-component `new_cost` override, status codes 702/1962/1268), Quick Time Entry strict field order and open-period requirement, `Shipping` (ship + invoice in one save), `InventoryAdjustment`, and the cost model (receipt vs moving-average COGS, pooling) — Fixes #66 — *[Alex Westemeier](https://github.com/AWestemeier), @mrwuss*
- **docs:** OData — explicit no-`@odata.nextLink` note, "No Joins — Chain Queries by UID" pattern with `p21_view_*` guidance, base-host-not-ui_server note; Interactive — key fields commit the cursor (later fields in the same change call silently ignored), integer-string numerics, the verified BINS unlock recipe for existing contracts (load by `job_no`) — Fixes #68 — *[Alex Westemeier](https://github.com/AWestemeier), @mrwuss*
- **docs:** `UseCodeValues` ↔ `code_p21` mapping (labels from `code_p21` language_id 9; DB/OData return the integer `code_no`) with verified enum maps; definition-endpoint HTTP 500 *"Window <<X>> is not available"* documented as environment availability, not permissions (238/299 fetchable on the test tenant) — Fixes #70 — *[Alex Westemeier](https://github.com/AWestemeier), @mrwuss*
- **docs:** Payload Anatomy — type-annotated TransactionSet skeleton and a mistakes→symptoms table (`Keys` as string, misplaced `IgnoreDisabled`, quoted booleans, object-for-array nesting, non-string `Value`s, wrong property case, cascade-breaking field order); **XML Payloads** — full content negotiation verified on every `/api/v2` endpoint (all four Content-Type/Accept combinations), the mandatory DataContract namespace, **alphabetical element order** (top-level violation → HTTP 500; nested → silently dropped element → NullReference failure), `Keys` arrays namespace, `TransactionStateRequest` root for `/transaction/get`, and the fetch-the-Template-as-XML practice — Fixes #82 — *@mrwuss*

**Structure & tooling:**

- **feat:** Task Index routing layer — `docs/INDEX.md` maps ~80 tasks to exact section anchors so readers (and AI agents) load only what a task needs; navigation convention documented — Fixes #72 — *@mrwuss*
- **feat:** Service-definition schema library — `definitions/` holds sanitized full-field definition JSON (every DataElement, field, key, type, label + payload template) for all 21 documented services; `scripts/fetch_definitions.py` refreshes and **sanitizes** (drops environment-specific `ufc_*` fields, redacts lookup-backed `ValidValues` that carry live instance data, scrub-term gate) — Fixes #74 — *@mrwuss*
- **feat:** Recipes cookbook — `docs/recipes/` with 10 self-contained task pages (complete payload, full runnable Python + C# example, verified gotchas, verify read-back) plus a conventions README; INDEX routes tasks to recipes first — Fixes #76 — *@mrwuss*
- **feat:** End-to-end example files — `examples/python/recipes/` (dry-run by default, `--execute` gates writes) and the `examples/csharp/Recipes/` solution project (menu runner, `EXECUTE`-gated writes); every recipe page links its files — Fixes #79 — *@mrwuss*
- **feat(site):** Recipes published on the HTML site — subfolder conversion with depth-aware sidebars, a Recipes nav section and landing-page grid, and repo-file links (`definitions/`, example files) rewritten to GitHub; landing page gains the Task Index card and the previously missing Production & Labor and UDT cards — Fixes #77 — *@mrwuss*
- **feat:** Offline payload validator — `scripts/validate_payload.py` checks JSON **and** XML payload files against the shape rules and `definitions/` schemas (exact paths to each problem, did-you-mean suggestions, XML namespace + element-order enforcement, verified field-order rules); `--self-test` included — Fixes #82 — *@mrwuss*

## 2026-07-06

- **docs:** Correct Entity API taxonomy — Epicor's **"Entity API"** is an umbrella term for two APIs: the **REST API** (the `/api/entity/`, `/api/inventory/`, and `/api/sales/` endpoint families) and the **eCommerce API** (Entity SOAP API); URL segments are arbitrary and don't define API boundaries, so the repo's `/api/entity/`-only framing and "Inventory is a separate API" language were wrong. Removed the incorrect warning that category URLs "do not work": `/api/sales/orders` **exists and responds** (verified July 2026: ping 200, `/new` returns a full order template, GET by order number returns ~70 fields, `/approve` route present); other category families (`sales/customers`, `purchasing/*`, `ar/*`, …) 404 on the tested tenant. Adds a Terminology section and an "Other REST Endpoint Families" section — *Felipe Maurer ([P21WWUG](https://forums.p21ww.org/UserInfo10045.aspx), taxonomy correction, 25.1 middleware evidence, [forum topic](https://forums.p21ww.org/Topic245514-3.aspx))*, verified and documented by *@mrwuss* — Fixes #53
- **docs:** Add PurchaseOrder notepad writes documentation (Interactive API) — header notes (`po_hdr_notepad`, PO Notes tab `TABPAGE_7`, datawindow `tp_7_dw_7`, tools `cb_add`/`cb_edit`) vs line notes (`po_line_notes`, `TABPAGE_21`/`tp_21_dw_21` after selecting a row in `tp_17_dw_17`, tools `cb_add_line`/`cb_edit_line`), full popup walkthrough (`w_notepad_response_lite`: `_dw_hdr`/`_dw_areas`/`_dw_select`, `TabName: null`, `cb_select_all` → `cb_ok`), and the silent-misfile warning: both tools are labelled "Add Note" but `cb_add_line` files the note against the currently-selected line with HTTP 200/`savesucceeded` and no error. Requires `ResponseWindowHandlingEnabled: true` — with `false` the add tool returns HTTP 400 "Unexpected response window". Both recipes and the misfile scenario verified end-to-end on a live test tenant (July 2026, read-back confirmed) — Fixes #49 — *@mrwuss*
- **docs:** Document `GET /api/v2/definition/{Service}` as the authoritative schema map — response shape `TransactionDefinition.DataElementDefinitions[]` with `Name`, `DatawindowName`, `Type`, `KeyFields`, and `FieldDefinitions[]` (`Name`, `DbColumnName`, `DataType`, `Required`); added as window discovery technique #7 in the Interactive API guide. Warning boxes in both guides: `TABPAGE_N` names are not sequential with the visible tab order (PurchaseOrder carries 37 tab pages, many hidden — the grid that looks like the second tab is `TABPAGE_17`), so match on the datawindow name (`tp_N_dw_N` / `d_...`) or read the window's `TabPageList`; live testing on two servers showed the Interactive window's `TABPAGE_N` names matching the Transaction definition 1:1 — Fixes #50 — *@mrwuss*
- **docs:** Add "Verifying Writes" section to Interactive API guide — a save can return `Status: 1` with `savesucceeded` for the primary datawindow while a child-grid change never persists (verified: a correctly-persisted note and a silently-misfiled one produce identical save responses); status semantics vary across P21 versions, and the save response never includes inserted child keys (`note_id` appears in the parent grid once the notepad popup commits, but only a read-back proves persistence). Recommendation: read the record back via `POST /api/v2/transaction/get` (or OData) before treating the write as done — verified live: the read-back recovered the server-generated `note_id` and located a misfiled note; cross-linked from the Transaction API guide — Fixes #51 — *@mrwuss*

## 2026-06-15

- **docs:** Document Inventory REST API `ItemDesc` character-set and whitespace behavior — on a **26.1** tenant the API enforces **no symbol restriction** (all printable ASCII `" ' \` & < > # / \ | , ; : . ( ) [ ] { } * + = % $ @ ! ? ~ ^ _ -` and Unicode such as `é`, `½`, `°` round-trip intact via GET → PUT → GET); only the 40-char limit (41+ **silently discarded** on PUT, HTTP 200) and trailing-whitespace trim apply. **Version/pipeline caveat:** 25.x tenants and downstream consumers (reporting, label printing, EDI) may reject characters the 26.1 REST API accepts — the double-quote `"` is a known offender — so strip risky symbols from descriptions and part numbers before writing if targeting 25.x or feeding reporting. Includes a round-trip probe snippet. Verified against Prophet21Play (26.1) — Fixes #47 — *@mrwuss*

## 2026-05-22

- **fix:** Correct JobContractPricing update guidance — Transaction API **does** update existing `job_price_line` rows when called with `Status: "New"` and the FORM key fields (`company_id`, `contract_no`, `job_no`, `end_date`) in `Edits` (not `Keys`); previous docs incorrectly deflected readers to the Interactive API. Adds *Updating an Existing Contract* subsection with verified payload shape, notes that `pricing_method` Source → Price conversion works in the same call, and inlines a `/api/v2/transaction/get` retrieval example. Empirically verified by 173 successful price updates against contract `A120-12` on a production tenant (HTTP 200, OData re-read confirmed). The `Status: "Existing"` 500 caveat remains as an "unused — use New instead" note, no longer a write ban — Fixes #44 — *@mrwuss* via [PR #45](https://github.com/mrwuss/p21-api-documentation/pull/45)

## 2026-04-16

- **docs:** Add UDT Service API documentation (`docs/13-UDT-Service-API.md`) — complete CRUD documentation for `/udtservice/api/udtdata/` endpoints (insert, update, delete), OData read patterns, response format quirks, SQL keyword false positives, SaaS hostname differences, Python and C# examples — *Felipe Maurer (discovery and testing), David Sokoloski (P21 help docs reference), Brad Vandenbogaerde (database tables, SaaS hostname fix), John Kennedy (SQL keyword issue), Jon Christie (response format quirk), @mrwuss*
- **docs:** Add Inventory REST API pricing endpoints — two verified V2 pricing URL patterns, URL encoding requirements for special characters, forward slash (`/`) encoding confirmed broken (returns 404), verified pricing response structure with availability data — *Felipe Maurer, John Kennedy, @mrwuss*
- **docs:** Add Interactive API response window handling for tabless windows — `TabName: null` pattern for changing fields on popup dialogs, common response window buttons — *Jon Christie* — *@mrwuss*
- **docs:** Add window discovery techniques section — GetState, GetTools, GetData, result event inspection, P21 SQL Information dialog, browser DevTools — *@mrwuss*
- **docs:** Add V1 REST endpoint reference table — internal SDK endpoints for debugging and network trace analysis — *@mrwuss*
- **docs:** Expand 25.2 DatawindowName breaking change — add ConvertPOToVoucher (*Jeff Patterson, Josiah Shollenberger*), Order Entry (*Neil Timmerman*), Clippership Auto Shipping (*Josh Owen*), Doc Links (*Jaime Nelson*) to affected windows list; bug confirmed through 25.2.5776.1, acknowledged by Epicor as development bug; add PO Receiving Group fix example — *David Sokoloski (first discovered 4-param workaround), Jeff Patterson (confirmed fix)* — *@mrwuss*
- **docs:** Add PDF Report Generation section to Transaction API — `/api/v2/process/pdfreport` endpoint for generating base64-encoded PDF documents (purchase orders, pick tickets), verified services `m_reprintpurchaseorders` and `m_reprintpicktickets`, Python and C# examples — *Jeff Poss (endpoint discovery), @mrwuss*
- **docs:** Add Stored Procedure Executor section to Transaction API — `m_storedprocedureexecutor` service for loading SP definitions via Transaction API, UID lookup workflow, `argument_list` parameter discovery, database tables (`stored_procedure_def`, `spe_parameter_info`, `spe_procedure_info`) — *Felipe Maurer, Kevin Landry, Brad Vandenbogaerde, @mrwuss*
- **docs:** Add DynaChange and Popup Handling section to Transaction API — DynaChange enforcement in TAPI workflows, popup suppression pattern for API user profiles, Visual Rule limitations with response/callback attributes, "Column is disabled" root causes, HTTP 200 response validation gotcha — *Felipe Maurer, Brad Vandenbogaerde, Justin Cassidy, Neil Timmerman, @mrwuss*

## 2026-04-10

- **docs:** Correct Inventory REST API — existing `inv_loc` fields CAN be updated via GET → modify → PUT (previously documented as append-only), add ItemDesc 40-char limit, POST 307 redirect, location soft-delete via `Delete: "Y"`, PurchaseDiscountGroup/SalesDiscountGroup fields, minimum create payload — Fixes #31 — *@mrwuss*
- **docs:** Add JobContractPricing service documentation — full-service structure (25 DataElements), multi-line break interleaving pattern, 15-tier break structure, non-break vs break line patterns, Status "Existing" NullReferenceException (platform-wide bug), commission cost column limitations — Fixes #32 — *@mrwuss*
- **docs:** Add Assembly service documentation — full-service structure (15 DataElements), component_type valid values (hose-specific), copy_item_id field, item-must-exist-first validation, Part + Assembly creation workflow, Status "Existing" bug — Fixes #33 — *@mrwuss*
- **docs:** Add Interactive API operational patterns — tab unlock sequences (JobContractPricing example), add_row Status=2 creates row despite failure status, response window type taxonomy (button-only vs form+button vs message box), UOM auto-population best practice, timeout recommendations — Fixes #34 — *@mrwuss*
- **docs:** Expand authentication documentation — token TTL and reuse patterns, multi-API token reuse, TokenManager class examples (Python + C#)

## 2026-04-04

- **docs:** Expand consumer key authentication documentation — verified consumer key + username works for Interactive API sessions, added SOA Admin configuration fields, JWT token claims, API-specific behavior table, scope behavior, Python and C# code examples — *@mrwuss*
- **feat:** Add `consumer_username` to P21Config and `load_config()` for consumer key auth support
- **chore:** Scrub all personal and company-specific data from repository history via git-filter-repo

## 2026-03-06

- **feat:** Add Production & Labor API documentation — TimeEntry service for recording labor hours against production orders, ProductionOrder service with full field definitions (54 header fields, assembly lines, components, labor entries, completions, routing), Labor/LaborProcess services for labor code maintenance, 24 production-related Transaction API services discovered, 13 Interactive API windows verified working — *@mrwuss*
- **feat:** Add Python example scripts for production/labor — service discovery, TimeEntry definition, labor hour recording, ProductionOrder definition (`examples/python/production/`)
- **feat:** Add C# example code for production/labor — mirrors Python examples (`examples/csharp/Production/`)
- **docs:** Update API Selection Guide with production/labor use cases and decision table entries
- **docs:** Update Transaction API with production & labor services table
- **docs:** Update Interactive API with production & labor windows table

## 2026-02-25

- **feat:** Add C# code examples alongside Python across all documentation — tabbed code blocks (Python/C#) in generated HTML with global language sync and localStorage persistence, 23 C# console app examples mirroring every Python script, shared C# client library (`examples/csharp/Common/`) with auth, config, and HttpClient wrapper — *@mrwuss*

- **fix:** Correct Interactive API `ResultStatus` enum mapping — `None=0, Success=1, Failure=2, Blocked=3` (was incorrectly `0=Failure, 2=Blocked, 3=Dialog`), verified against source (`ResultWrapper.cs`) and live API — [PR #26](https://github.com/mrwuss/p21-api-documentation/pull/26)
- **docs:** Update Data Structures Reference to show integer status types with numeric values
- **docs:** Document `/tools` endpoint workaround for non-message-box response windows — `GET /tools` discovers buttons, `POST /tools` clicks them (verified on `w_inventory_scan_lookup`)
- **docs:** Update Event Data format documentation — confirmed KV-list format `[{"Key": "...", "Value": "..."}]`
- **fix:** Document P21 25.2 breaking change — `DatawindowName` now required in Interactive API change requests (3-parameter `ChangeData` method no longer works, must use 4-parameter form). Affects Item, PO Receiving Group, Delivery List, Group Pick Ticket, and likely other windows. Updated all code examples and batch processing patterns. Source: community forum reports.
- **fix:** Rewrite `06_complex_workflow.py` from v1 to v2 — endpoints, payload format (`List` not `ChangeRequests`), `DatawindowName` casing, integer status checks, v2 save format
- **fix:** Fix `get_opened_window_id()` in reusable client to handle KV-list Event Data format `[{"Key": "windowid", "Value": "..."}]`
- **fix:** Fix Error Handling doc — Blocked status is integer `3` (not string), Event Data uses KV-list format

## 2026-02-17

- **docs:** Add standalone Inventory REST API documentation — moved from Entity API doc, added verified PUT/POST behavior, multi-company inventory workflow (GET → Append → PUT), error examples, automation patterns — *Sibin Francis ([@sibinfrancisaj](https://github.com/sibinfrancisaj))* via [PR #25](https://github.com/mrwuss/p21-api-documentation/pull/25), verified and restructured by *@mrwuss*
- **fix:** Update inv_loc write access known issue — PUT can append new inv_loc records via Inventory REST API (partially resolved)

## 2026-02-16

- **feat:** Add Postman Collection for all P21 APIs — pre-configured requests for Auth, OData, Transaction, Interactive, and Entity APIs with auto-capture test scripts — *NextTWis ([@NextTWis](https://github.com/NextTWis))* via [PR #24](https://github.com/mrwuss/p21-api-documentation/pull/24)
- **fix:** Correct API endpoints in Postman collection — verified all URLs against live server, fixed Entity/Interactive/Transaction paths and payloads — *@mrwuss*

## 2026-02-13

- **docs:** Add Inventory REST API documentation to Entity API guide — verified endpoints, caveats, extended properties — *Sibin Francis ([@sibinfrancisaj](https://github.com/sibinfrancisaj))* via [PR #23](https://github.com/mrwuss/p21-api-documentation/pull/23)
- **fix:** Disable Jekyll rendering and add root URL redirect to HTML docs — *@mrwuss*

## 2026-02-12

- **feat:** Add reusable P21 API client (`examples/python/common/client.py`) with sync/async support, namespace helpers for all 4 APIs, and auto token refresh — *Claude Jones ([@RadAJones](https://github.com/RadAJones))* via [PR #16](https://github.com/mrwuss/p21-api-documentation/pull/16)
- **fix:** Address CodeRabbit + live API testing feedback on client — duplicate parser removal, query param fixes (`?id=` vs `?windowId=`), entity address guards, response window forwarding — *@mrwuss*
- **docs:** Add XML token responses section, query parameter testing results, and cross-reference updates across Auth, Interactive, Entity, and Error Handling docs — *@mrwuss*
- **docs:** Fix Entity API address limitations, add SOAP/mobile endpoints and error codes — *@mrwuss*
- **feat:** Add sidebar navigation with page index and on-page table of contents to all HTML docs — *@mrwuss*
- **docs:** Expand Transaction API with commands endpoint, async limits, and special scenarios — *@mrwuss*
- **docs:** Expand Interactive API with session params, data structures, and missing endpoints — *@mrwuss*
- **docs:** Fix OData pagination guidance — page size defaults and performance — *@mrwuss*

## 2026-02-11

- **docs:** Add complete field listings for all Entity API templates — *@mrwuss*
- **docs:** Rewrite Entity API docs based on verified live testing — confirmed working, composite keys, address limitations — *@mrwuss*
- **docs:** Add OData Dataservice Permissions prerequisites and fix OData version (v3, not v4) — *@mrwuss*

## 2026-02-09

- **docs:** Add production learnings from 700+ bulk Interactive API operations — session batching, error recovery, page expiration patterns — *@mrwuss* via [PR #11](https://github.com/mrwuss/p21-api-documentation/pull/11)

## 2026-01-20

- **docs:** Add Interactive API v1 vs v2 differences — endpoint comparison, migration guide — *@mrwuss* via [PR #9](https://github.com/mrwuss/p21-api-documentation/pull/9)
- **chore:** Cleanup repo — reorganize HTML to `docs/html/`, fix broken paths, restore Known Issues — *@mrwuss*

## 2026-01-19

- **docs:** Add working endpoint for responding to P21 dialogs — *@mrwuss*

## 2026-01-02

- **docs:** Add row selection bug workaround and `inv_loc` example for Interactive API — *@mrwuss*
- **docs:** Add Interactive API v1 vs v2 differences — *@mrwuss*

## 2025-12-27

- **docs:** Add lessons learned from Cube Writer project — session pool contamination patterns — *@mrwuss* via [PR #8](https://github.com/mrwuss/p21-api-documentation/pull/8)

## 2025-12-26

- **docs:** Add disclaimer to all documentation pages — *@mrwuss*
- **docs:** Add SalesPricePage dropdown codes reference — *@mrwuss* via [PR #1](https://github.com/mrwuss/p21-api-documentation/pull/1)

## 2025-12-25 — Initial Release

- **feat:** Initial project setup with full documentation for all 4 P21 APIs — *@mrwuss*
- **docs:** Authentication — token endpoints (V1/V2), credentials vs consumer keys, API scopes, token refresh
- **docs:** API Selection Guide — decision flowchart and comparison table
- **docs:** OData API — query syntax, filtering, pagination, example scripts
- **docs:** Transaction API — service discovery, bulk operations, async patterns, example scripts
- **docs:** Interactive API — session management, window operations, response handling, example scripts
- **docs:** Entity API — CRUD operations on customers, vendors, contacts, addresses
- **docs:** Error Handling — HTTP status codes, API-specific errors, Python patterns
- **feat:** GitHub Pages support with card-based landing page
- **feat:** HTML generation script with print/PDF support
- **feat:** Community contribution templates (CONTRIBUTING.md, issue templates)

---

## Contributors

| Contributor | GitHub | Contributions |
|-------------|--------|---------------|
| @mrwuss | [@mrwuss](https://github.com/mrwuss) | Project creator, all documentation, HTML generation, maintenance |
| Claude Jones | [@RadAJones](https://github.com/RadAJones) | Reusable P21 API client with sync/async support ([PR #16](https://github.com/mrwuss/p21-api-documentation/pull/16)) |
| Sibin Francis | [@sibinfrancisaj](https://github.com/sibinfrancisaj) | Inventory REST API documentation ([PR #23](https://github.com/mrwuss/p21-api-documentation/pull/23)) |
| NextTWis | [@NextTWis](https://github.com/NextTWis) | Postman Collection for P21 API verification ([PR #24](https://github.com/mrwuss/p21-api-documentation/pull/24)) |
| Jeff Poss | | PDF Report Generation endpoint discovery |
| Felipe Maurer | | Stored Procedure Executor UID discovery, DynaChange enforcement in TAPI |
| Kevin Landry | | Stored Procedure Executor execution via Interactive API |
| Brad Vandenbogaerde | | SP Executor database tables, Visual Rule response/callback TAPI limitation |
| Justin Cassidy | | DynaChange as root cause for "Column is disabled" errors |
| Neil Timmerman | | TAPI HTTP 200 response validation gotcha |

---

## Related

- [GitHub Repository](https://github.com/mrwuss/p21-api-documentation)
- [Authentication](00-Authentication.md)
- [API Selection Guide](01-API-Selection-Guide.md)
