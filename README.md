# P21 API Documentation

> **Disclaimer:** This is unofficial, community-created documentation for Epicor Prophet 21 APIs. It is not affiliated with, endorsed by, or supported by Epicor Software Corporation. All product names, trademarks, and registered trademarks are property of their respective owners. Use at your own risk.

Comprehensive documentation and working examples (Python and C#) for all Prophet 21 integration APIs.

## Overview

This repository provides developer-focused documentation for P21's integration APIs. All content is based on official Epicor SDK documentation and verified working implementations.

**[View Online Documentation](https://mrwuss.github.io/p21-api-documentation/html/)**

## APIs Covered

| API | Purpose | Best For |
|-----|---------|----------|
| [OData](docs/02-OData-API.md) | Read-only data access via standard OData protocol | Reporting, lookups, data exports |
| [Transaction API](docs/03-Transaction-API.md) | Stateless bulk data manipulation | Bulk creates, external integrations |
| [Interactive API](docs/04-Interactive-API.md) | Stateful window interactions with business logic | Complex workflows, validation |
| [Entity API](docs/05-Entity-API.md) | Simple CRUD on business objects | Basic record operations |
| [Inventory REST API](docs/11-Inventory-REST-API.md) | Inventory item CRUD, multi-company workflows | Item reads, appending locations/suppliers |
| [Production & Labor](docs/12-Production-Labor-API.md) | Production orders, labor hours, time entry | Manufacturing workflows, labor tracking |
| [UDT Service API](docs/13-UDT-Service-API.md) | CRUD on user-defined tables | Custom table maintenance |

## Quick Start

```bash
# Clone and setup
git clone https://github.com/mrwuss/p21-api-documentation.git
cd p21-api-documentation

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your P21 credentials

# Run an example
python scripts/odata/01_basic_query.py
```

## Documentation

### Getting Started
- [Authentication](docs/00-Authentication.md) - Token generation, credentials vs consumer key, Interactive API auth
- [API Selection Guide](docs/01-API-Selection-Guide.md) - Which API to use when

### API Reference
- [OData API](docs/02-OData-API.md) - Query syntax, filtering, pagination
- [Transaction API](docs/03-Transaction-API.md) - Service discovery, bulk operations
- [Interactive API](docs/04-Interactive-API.md) - Sessions, windows, workflows
- [Entity API](docs/05-Entity-API.md) - Entity CRUD operations
- [Inventory REST API](docs/11-Inventory-REST-API.md) - Inventory CRUD, multi-company workflows
- [Production & Labor API](docs/12-Production-Labor-API.md) - Production orders, labor tracking
- [UDT Service API](docs/13-UDT-Service-API.md) - User-defined table CRUD via `/udtservice/api/udtdata/`

### Troubleshooting
- [Error Handling](docs/06-Error-Handling.md) - HTTP codes, error responses
- [Session Pool Issues](docs/07-Session-Pool-Troubleshooting.md) - Intermittent failures

### Reference
- [SalesPricePage Dropdown Codes](docs/08-SalesPricePage-Codes.md) - Valid values for price page fields
- [Batch Processing Patterns](docs/09-Batch-Processing-Patterns.md) - Production batch operation patterns
- [Changelog](docs/10-Changelog.md) - All changes and contributors

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
- `scripts/interactive/05_response_windows.py` - Dialog handling and response windows
- `scripts/interactive/06_complex_workflow.py` - Multi-step workflows

### Entity API
- `scripts/entity/01_list_entities.py` - Discover entities
- `scripts/entity/02_query_entity.py` - Query records
- `scripts/entity/03_create_entity.py` - Create record

## C# Examples

The `examples/csharp/` directory contains equivalent C# console applications for every Python script, plus a shared client library.

```bash
# Build all C# examples
cd examples/csharp
dotnet build

# Run a specific example
dotnet run --project OData
dotnet run --project Transaction
dotnet run --project Interactive
dotnet run --project Entity
```

See [examples/csharp/README.md](examples/csharp/README.md) for setup details.

All documentation pages include tabbed code blocks showing both Python and C# side-by-side. The [online HTML docs](https://mrwuss.github.io/p21-api-documentation/html/) support language switching with global sync across all code blocks on a page.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `P21_BASE_URL` | Yes | P21 server URL (e.g., `https://play.p21server.com`) |
| `P21_USERNAME` | Yes* | P21 API username |
| `P21_PASSWORD` | Yes* | P21 API password |
| `P21_CONSUMER_KEY` | No | Consumer key GUID (alternative to username/password) |
| `P21_CONSUMER_USERNAME` | No | P21 username for consumer key auth (required for Interactive API) |

*Not required when using consumer key authentication. See [Authentication docs](docs/00-Authentication.md).

## Content Sources

All documentation is derived from:
- **Official SDK**: Epicor P21 SDK documentation
- **Working Code**: Verified implementations from production projects
- **Actual Testing**: Tested against P21 test environments

## Contributing

This documentation is a community effort! We welcome contributions:

- **Found an error?** [Open an issue](../../issues/new?template=bug-report.md)
- **Need something documented?** [Request it](../../issues/new?template=documentation-request.md)
- **Have P21 knowledge to share?** [Contribute](../../issues/new?template=contribution.md)
- **Questions?** [Start a discussion](../../discussions)

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - See LICENSE file
