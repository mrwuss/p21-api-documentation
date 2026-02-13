# Changelog

> **Disclaimer:** This is unofficial, community-created documentation for Epicor Prophet 21 APIs. It is not affiliated with, endorsed by, or supported by Epicor Software Corporation. All product names, trademarks, and registered trademarks are property of their respective owners. Use at your own risk.

---

All notable changes to this documentation project are listed below, grouped by date. This project uses [Conventional Commits](https://www.conventionalcommits.org/).

---

## 2026-02-13

- **docs:** Add Inventory REST API documentation to Entity API guide — verified endpoints, caveats, extended properties — *Sibin Francis ([@sibinfrancisaj](https://github.com/sibinfrancisaj))* via [PR #23](https://github.com/mrwuss/p21-api-documentation/pull/23)
- **fix:** Disable Jekyll rendering and add root URL redirect to HTML docs — *Josh Scarbrough*

## 2026-02-12

- **feat:** Add reusable P21 API client (`scripts/common/client.py`) with sync/async support, namespace helpers for all 4 APIs, and auto token refresh — *Claude Jones ([@RadAJones](https://github.com/RadAJones))* via [PR #16](https://github.com/mrwuss/p21-api-documentation/pull/16)
- **fix:** Address CodeRabbit + live API testing feedback on client — duplicate parser removal, query param fixes (`?id=` vs `?windowId=`), entity address guards, response window forwarding — *Josh Scarbrough*
- **docs:** Add XML token responses section, query parameter testing results, and cross-reference updates across Auth, Interactive, Entity, and Error Handling docs — *Josh Scarbrough*
- **docs:** Fix Entity API address limitations, add SOAP/mobile endpoints and error codes — *Josh Scarbrough*
- **feat:** Add sidebar navigation with page index and on-page table of contents to all HTML docs — *Josh Scarbrough*
- **docs:** Expand Transaction API with commands endpoint, async limits, and special scenarios — *Josh Scarbrough*
- **docs:** Expand Interactive API with session params, data structures, and missing endpoints — *Josh Scarbrough*
- **docs:** Fix OData pagination guidance — page size defaults and performance — *Josh Scarbrough*

## 2026-02-11

- **docs:** Add complete field listings for all Entity API templates — *Josh Scarbrough*
- **docs:** Rewrite Entity API docs based on verified live testing — confirmed working, composite keys, address limitations — *Josh Scarbrough*
- **docs:** Add OData Dataservice Permissions prerequisites and fix OData version (v3, not v4) — *Josh Scarbrough*

## 2026-02-09

- **docs:** Add production learnings from 700+ bulk Interactive API operations — session batching, error recovery, page expiration patterns — *Josh Scarbrough* via [PR #11](https://github.com/mrwuss/p21-api-documentation/pull/11)

## 2026-01-20

- **docs:** Add Interactive API v1 vs v2 differences — endpoint comparison, migration guide — *Josh Scarbrough* via [PR #9](https://github.com/mrwuss/p21-api-documentation/pull/9)
- **chore:** Cleanup repo — reorganize HTML to `docs/html/`, fix broken paths, restore Known Issues — *Josh Scarbrough*

## 2026-01-19

- **docs:** Add working endpoint for responding to P21 dialogs — *Josh Scarbrough*

## 2026-01-02

- **docs:** Add row selection bug workaround and `inv_loc` example for Interactive API — *Josh Scarbrough*
- **docs:** Add Interactive API v1 vs v2 differences — *Josh Scarbrough*

## 2025-12-27

- **docs:** Add lessons learned from Cube Writer project — session pool contamination patterns — *Josh Scarbrough* via [PR #8](https://github.com/mrwuss/p21-api-documentation/pull/8)

## 2025-12-26

- **docs:** Add disclaimer to all documentation pages — *Josh Scarbrough*
- **docs:** Add SalesPricePage dropdown codes reference — *Josh Scarbrough* via [PR #1](https://github.com/mrwuss/p21-api-documentation/pull/1)

## 2025-12-25 — Initial Release

- **feat:** Initial project setup with full documentation for all 4 P21 APIs — *Josh Scarbrough*
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
| Josh Scarbrough | [@mrwuss](https://github.com/mrwuss) | Project creator, all documentation, HTML generation, maintenance |
| Claude Jones | [@RadAJones](https://github.com/RadAJones) | Reusable P21 API client with sync/async support ([PR #16](https://github.com/mrwuss/p21-api-documentation/pull/16)) |
| Sibin Francis | [@sibinfrancisaj](https://github.com/sibinfrancisaj) | Inventory REST API documentation ([PR #23](https://github.com/mrwuss/p21-api-documentation/pull/23)) |

---

## Related

- [GitHub Repository](https://github.com/mrwuss/p21-api-documentation)
- [Authentication](00-Authentication.md)
- [API Selection Guide](01-API-Selection-Guide.md)
