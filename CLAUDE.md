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
| **ui/full (web client)** | Drives any *web-enabled* window by menu class name | The window has no `service_name` — no TAPI/Interactive route | Working (`{ui}/ui/full/`) |
| **UDT Service API** | CRUD on user-defined tables | Custom table maintenance | Working (`/udtservice/api/udtdata/`) |
| **Other REST families** | 16 families: UDF metadata, GL, CRM tasks/opportunities/consignment orders, PO headers, inventory (adjustments/movement/counts/scan/serial info), file storage, system info, customer form templates, service orders, exchange rates | UDF discovery, journal-entry reads, task/PO/GL/adjustment/movement/count writes, filesystem access | Reads and writes verified across the platform-level five and the business-object eleven; 3 blocked only by empty tenant config (opportunities, CUO, exchange rates), 2 by an unresolved precondition (tag adjustments, serial extended info) |

---

## Where the detail lives

| Topic | File |
|---|---|
| Known issues and verified hazards: the routing table to the docs | `.claude/rules/hazards.md` (loads when you open `docs/`, `examples/`, `definitions/` or `postman/`) |
| Project structure: every folder and the repo tooling in `scripts/` | `.claude/rules/structure.md` |

> **API behavior facts live in `docs/`, never in this file or in `.claude/rules/`** — one source of truth prevents drift. When you verify something new, write it into the linked doc and add an INDEX.md row.

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
| `P21_BASE_URL` | Yes | P21 server URL (e.g., `https://play.example.com`) |
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
4. **The community**: P21WWUG forum topics, conference sessions, and colleagues' scripts — a **lead, never a fact until re-verified here**. Cite the person (public profile only; never link a private repo), state the build you verified on, and say so inline when you *couldn't* verify. See [CONTRIBUTING § Provenance and Attribution](https://github.com/mrwuss/p21-api-documentation/blob/master/CONTRIBUTING.md#provenance-and-attribution).

---

## Key Principles

- **Facts only** - No guesses about undocumented behavior
- **Verified examples** - All code runs without errors
- **Real payloads** - Request/response examples from actual API calls
- **Known issues documented** - Session pool contamination, async limitations

---
