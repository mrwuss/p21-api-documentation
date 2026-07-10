# Python Examples

Runnable Python examples for every P21 API, mirroring the [C# examples](../csharp/README.md). Each script is standalone; shared auth/config lives in [`common/`](common/).

| Directory | Contents |
|-----------|----------|
| `common/` | Shared auth, config (.env), and client helpers used by every script |
| `odata/` | Read-only queries: basics, filtering, pagination, complex queries |
| `transaction/` | Service discovery, definitions, create single/bulk, updates, async, session-pool diagnostics |
| `interactive/` | Session lifecycle, windows, field changes, saves, response windows, multi-step workflows |
| `entity/` | Entity API CRUD on customers/vendors/contacts/addresses |
| `production/` | Production & Labor services: discovery, definitions, labor hours |
| `recipes/` | End-to-end scripts for the [recipes cookbook](../../docs/recipes/README.md) — **dry-run by default**, `--execute` posts and verifies |

## Setup

```bash
cp .env.example .env    # from the repo root; set P21_BASE_URL, P21_USERNAME, P21_PASSWORD
pip install -r requirements.txt
python examples/python/odata/01_basic_query.py
```

Raw request payloads (JSON and XML) for the documented tasks live in [`../payloads/`](../payloads/) — validate any payload offline with `python scripts/validate_payload.py <file>`.
