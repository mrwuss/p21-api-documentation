# P21 API Documentation

Comprehensive documentation and working Python examples for all Prophet 21 integration APIs.

## Overview

This repository provides developer-focused documentation for P21's four integration APIs. All content is based on official Epicor SDK documentation and verified working implementations.

## APIs Covered

| API | Purpose | Best For |
|-----|---------|----------|
| [OData](docs/02-OData-API.md) | Read-only data access via standard OData protocol | Reporting, lookups, data exports |
| [Transaction API](docs/03-Transaction-API.md) | Stateless bulk data manipulation | Bulk creates, external integrations |
| [Interactive API](docs/04-Interactive-API.md) | Stateful window interactions with business logic | Complex workflows, validation |
| [Entity API](docs/05-Entity-API.md) | Simple CRUD on business objects | Basic record operations |

## Quick Start

```bash
# Clone and setup
git clone <repo-url>
cd p21-api-documentation

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your P21 credentials

# Run an example
python scripts/odata/01_basic_query.py
```

## Online Documentation

This documentation is available online via GitHub Pages:

**[View Documentation](https://mrwuss.github.io/p21-api-documentation/)**

### Enabling GitHub Pages (for forks)

1. Go to repository **Settings** > **Pages**
2. Under "Source", select **Deploy from a branch**
3. Choose branch: `master`, folder: `/docs`
4. Click **Save**
5. Your docs will be live at `https://<username>.github.io/p21-api-documentation/`

---

## Documentation

### Getting Started
- [Authentication](docs/00-Authentication.md) - Token generation, credentials vs consumer key
- [API Selection Guide](docs/01-API-Selection-Guide.md) - Which API to use when

### API Reference
- [OData API](docs/02-OData-API.md) - Query syntax, filtering, pagination
- [Transaction API](docs/03-Transaction-API.md) - Service discovery, bulk operations
- [Interactive API](docs/04-Interactive-API.md) - Sessions, windows, workflows
- [Entity API](docs/05-Entity-API.md) - Entity CRUD operations

### Troubleshooting
- [Error Handling](docs/06-Error-Handling.md) - HTTP codes, error responses
- [Session Pool Issues](docs/07-Session-Pool-Troubleshooting.md) - Intermittent failures

## Example Scripts

### OData
- `scripts/odata/01_basic_query.py` - Simple table query
- `scripts/odata/02_filtering.py` - Filter expressions
- `scripts/odata/03_pagination.py` - Skip, top, count
- `scripts/odata/04_complex_queries.py` - Advanced queries

### Transaction API
- `scripts/transaction/01_list_services.py` - Discover services
- `scripts/transaction/02_get_definition.py` - Get service schema
- `scripts/transaction/03_create_single.py` - Create one record
- `scripts/transaction/04_create_bulk.py` - Batch operations
- `scripts/transaction/test_session_pool.py` - Diagnose pool issues

### Interactive API
- `scripts/interactive/01_open_session.py` - Session lifecycle
- `scripts/interactive/02_open_window.py` - Window operations
- `scripts/interactive/03_change_data.py` - Field manipulation
- `scripts/interactive/04_save_and_close.py` - Save workflow

### Entity API
- `scripts/entity/01_list_entities.py` - Discover entities
- `scripts/entity/02_query_entity.py` - Query records
- `scripts/entity/03_create_entity.py` - Create record

### Real-World Examples
- `examples/price_page_create.py` - Create price page workflow
- `examples/supplier_lookup.py` - Lookup supplier data
- `examples/bulk_update.py` - Bulk update operations

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `P21_BASE_URL` | Yes | P21 server URL (e.g., `https://play.p21server.com`) |
| `P21_USERNAME` | Yes | P21 API username |
| `P21_PASSWORD` | Yes | P21 API password |

## Content Sources

All documentation is derived from:
- **Official SDK**: Epicor P21 SDK documentation
- **Working Code**: Verified implementations from production projects
- **Actual Testing**: Tested against P21 test environments

## License

MIT License - See LICENSE file
