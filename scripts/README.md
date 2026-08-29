# Repo Tooling

Maintenance tools for this repository — **not** API examples (those live in [`examples/`](../examples/python/README.md)).

| Script | Purpose |
|--------|---------|
| [`validate_payload.py`](validate_payload.py) | Offline payload validator (JSON **and** XML): structure/type checks with exact paths, element/field names against [`definitions/`](../definitions/README.md), XML namespace + DataContract element-order enforcement. `--self-test` included; exits 1 on errors. |
| [`fetch_definitions.py`](fetch_definitions.py) | Fetches `GET /api/v2/definition/{Service}` for the documented services and **sanitizes** before writing to `definitions/` (drops environment-specific `ufc_*` fields, redacts lookup-backed ValidValues, `P21_SCRUB_TERMS` gate). |
| [`generate_html.py`](generate_html.py) | Converts `docs/` + `docs/recipes/` markdown to the static site in `docs/html/` (tabbed code blocks, task-index rename, GitHub-blob rewriting for repo-file links). Run after **every** markdown edit. |
| [`check_anchors.py`](check_anchors.py) | Validates every internal `docs/` link against the ids the HTML generator actually emits. Run after `generate_html.py`; exits 1 on a broken anchor. Catches the common trap that an em dash in a heading collapses to **one** hyphen in the id. |
| [`test_client.py`](test_client.py) | Smoke test for the shared Python client against a live environment. |

```bash
python scripts/validate_payload.py examples/payloads/json/create-sales-order.json
python scripts/fetch_definitions.py --services Order
python scripts/generate_html.py
```
