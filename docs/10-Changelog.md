# Changelog

> **Disclaimer:** This is unofficial, community-created documentation for Epicor Prophet 21 APIs. It is not affiliated with, endorsed by, or supported by Epicor Software Corporation. All product names, trademarks, and registered trademarks are property of their respective owners. Use at your own risk.

---

All notable changes to this documentation project are listed below, grouped by date. This project uses [Conventional Commits](https://www.conventionalcommits.org/).

---

## 2026-06-15

- **docs:** Document Inventory REST API `ItemDesc` character-set and whitespace behavior — empirically verified that the API enforces **no symbol restriction** (all printable ASCII `" ' \` & < > # / \ | , ; : . ( ) [ ] { } * + = % $ @ ! ? ~ ^ _ -` and Unicode such as `é`, `½`, `°` round-trip intact via GET → PUT → GET); only the 40-char limit (41+ **silently discarded** on PUT, HTTP 200) and trailing-whitespace trim apply; clarifies that symbol restrictions users encounter originate from the P21 desktop UI / DynaChange or downstream consumers, not the REST API. Includes a round-trip probe snippet. Verified against Prophet21Play — Fixes #47 — *@mrwuss*

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
- **feat:** Add Python example scripts for production/labor — service discovery, TimeEntry definition, labor hour recording, ProductionOrder definition (`scripts/production/`)
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

- **feat:** Add reusable P21 API client (`scripts/common/client.py`) with sync/async support, namespace helpers for all 4 APIs, and auto token refresh — *Claude Jones ([@RadAJones](https://github.com/RadAJones))* via [PR #16](https://github.com/mrwuss/p21-api-documentation/pull/16)
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
