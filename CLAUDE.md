# Project: P21 API Documentation

> Comprehensive documentation and working examples for all P21 APIs.

---

## Quick Context

This project provides developer-focused documentation for Prophet 21's integration APIs. All content is based on official Epicor SDK documentation and verified working implementations - no guesses or assumptions.

---

## APIs Covered

| API | Purpose | Use When |
|-----|---------|----------|
| **OData** | Read-only data access via standard OData protocol | Quick reads, reporting, lookups |
| **Transaction API** | Stateless bulk data manipulation | Bulk creates, external integrations |
| **Interactive API** | Stateful window interactions with business logic | Complex workflows, validation needed |
| **Entity API** | Simple CRUD on business objects | Basic record operations |

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
│   └── html/                    # Generated HTML versions
│
├── scripts/
│   ├── common/                  # Shared auth/config
│   ├── odata/                   # OData examples
│   ├── transaction/             # Transaction API examples
│   ├── interactive/             # Interactive API examples
│   ├── entity/                  # Entity API examples
│   └── generate_html.py         # MD to HTML converter
│
└── examples/                    # Real-world scenarios
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

*Last updated: 2025-12-25*
