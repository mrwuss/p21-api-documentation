# P21 API Documentation

> **Disclaimer:** This is unofficial, community-created documentation for Epicor Prophet 21 APIs. It is not affiliated with, endorsed by, or supported by Epicor Software Corporation. All product names, trademarks, and registered trademarks are property of their respective owners. Use at your own risk.

Comprehensive documentation and working examples — **Python, C#, JSON, and XML** — for all Prophet 21 integration APIs.

Every code example that calls P21 is a **complete program**: paste it into a file, edit the constants in its `EDIT THESE` block, and run it. Python needs only `httpx`; C# targets **`net8.0` or later** with System.Text.Json and **no NuGet packages**, so `dotnet new console` + paste + `dotnet run` works. Writes end with a read-back that prints what actually landed, because in this API a 200 routinely lies.

**[View Online Documentation](https://mrwuss.github.io/p21-api-documentation/html/)**

## How This Repo Is Organized (start here)

The repo is built for **progressive disclosure**: this README routes you, each area's README is the source of truth for that area, and the [Task Index](docs/INDEX.md) maps tasks to exact doc sections. Load only what your task needs — most files here are reference material you should never read end-to-end.

> **If you're an AI assistant:** read [CLAUDE.md](CLAUDE.md), then [docs/INDEX.md](docs/INDEX.md), then only the sections or recipe your task needs. Don't load whole docs or whole folders; the folder READMEs below tell you what's inside without opening it.

| Area | What's there | Start at |
|------|--------------|----------|
| [`docs/INDEX.md`](docs/INDEX.md) | "I want to…" → exact doc-section routing map | the index itself |
| [`docs/`](docs/INDEX.md#doc-inventory-what-each-file-is) | The deep manual — 15 numbered guides (auth, each API, errors, patterns) | Task Index, not the raw files |
| [`docs/recipes/`](docs/recipes/README.md) | Copy-and-run task pages: complete payload + runnable Python & C# + verified gotchas | [recipes README](docs/recipes/README.md) |
| [`definitions/`](definitions/README.md) | Full-field service schemas (every DataElement, field, key, label + payload template), sanitized | [definitions README](definitions/README.md) |
| [`examples/python/`](examples/python/README.md) | Runnable Python examples for every API + end-to-end recipe scripts (dry-run by default) | [python README](examples/python/README.md) |
| [`examples/csharp/`](examples/csharp/README.md) | Equivalent C# console apps (`P21Examples.sln`) + shared client library | [csharp README](examples/csharp/README.md) |
| [`examples/payloads/`](examples/payloads/README.md) | Standalone copy-ready request bodies — JSON and DataContract-correct XML, validator-verified | [payloads README](examples/payloads/README.md) |
| [`postman/`](postman/README.md) | Postman collection covering all APIs (import-and-go) | [postman README](postman/README.md) |
| [`scripts/`](scripts/README.md) | Repo tooling: payload validator, definition fetcher, HTML generator | [scripts README](scripts/README.md) |

## APIs Covered

| API | Purpose | Best For |
|-----|---------|----------|
| [OData](docs/02-OData-API.md) | Read-only data access via standard OData protocol | Reporting, lookups, data exports |
| [Transaction API](docs/03-Transaction-API.md) | Stateless data manipulation (create, update/upsert, bulk) | Creates, keyed updates, external integrations |
| [Interactive API](docs/04-Interactive-API.md) | Stateful window interactions with business logic | Dialogs, disabled tabs, complex workflows |
| [Entity API](docs/05-Entity-API.md) | Simple CRUD on business objects | Basic record operations |
| [Inventory REST API](docs/11-Inventory-REST-API.md) | Inventory item CRUD, multi-company workflows | Item reads, appending locations/suppliers |
| [Production & Labor](docs/12-Production-Labor-API.md) | Production orders, labor hours, time entry | Manufacturing workflows, labor tracking |
| [UDT Service API](docs/13-UDT-Service-API.md) | CRUD on user-defined tables | Custom table maintenance |
| [ui/full (web client)](docs/04-Interactive-API.md#the-uifull-surface-the-web-clients-own-rest-api) | Drives web-enabled windows by menu class name | A window has no service name — no Transaction/Interactive route |

## Quick Start

```bash
git clone https://github.com/mrwuss/p21-api-documentation.git
cd p21-api-documentation

pip install -r requirements.txt
cp .env.example .env        # add your P21 credentials

# Read something
python examples/python/odata/01_basic_query.py

# Validate a write payload before ever posting it
python scripts/validate_payload.py examples/payloads/json/create-sales-order.json
```

For C#: `cd examples/csharp && dotnet build`, then `dotnet run --project <Project>` — see the [csharp README](examples/csharp/README.md).

## Documentation

> **Start with the [Task Index](docs/INDEX.md)** — a "what do you want to do" → exact-section map. The docs below are the deep manual; the index gets you to the right 50 lines instead of the right 2,000.

- **Getting started:** [Authentication](docs/00-Authentication.md) · [API Selection Guide](docs/01-API-Selection-Guide.md)
- **API reference:** [OData](docs/02-OData-API.md) · [Transaction](docs/03-Transaction-API.md) · [Interactive](docs/04-Interactive-API.md) · [Entity](docs/05-Entity-API.md) · [Inventory REST](docs/11-Inventory-REST-API.md) · [Production & Labor](docs/12-Production-Labor-API.md) · [UDT Service](docs/13-UDT-Service-API.md)
- **Troubleshooting:** [P21 Breaking Changes](docs/14-Breaking-Changes.md) · [Error Handling](docs/06-Error-Handling.md) · [Session Pool Issues](docs/07-Session-Pool-Troubleshooting.md)
- **Reference:** [SalesPricePage Codes](docs/08-SalesPricePage-Codes.md) · [Batch Processing Patterns](docs/09-Batch-Processing-Patterns.md) · [Changelog](docs/10-Changelog.md)

All documentation pages include tabbed Python/C# code blocks; the [online docs](https://mrwuss.github.io/p21-api-documentation/html/) sync language selection across every block on a page.

**Sharing a section:** on the online [Changelog](https://mrwuss.github.io/p21-api-documentation/html/10-Changelog.html) and [Breaking Changes](https://mrwuss.github.io/p21-api-documentation/html/14-Breaking-Changes.html) pages, hovering any section heading reveals a **Copy BBCode** button — handy for quoting a release or a single breaking-change entry on the [P21 forum](https://forums.p21ww.org/). It copies that section only (a parent section brings its subsections with it), as forum-ready BBCode with every link rewritten to an absolute URL so it still resolves once pasted.

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

## Content Sources

All documentation is derived from:
- **Official SDK**: Epicor P21 SDK documentation
- **Working Code**: Verified implementations from production projects
- **Actual Testing**: Tested against P21 test environments — disputed or community-reported behavior is live-verified before it's documented
- **The community**: P21WWUG forum topics, conference sessions and shared scripts — credited by name, and treated as a lead to verify rather than a fact to repeat ([how we handle it](CONTRIBUTING.md#provenance-and-attribution))

## Contributing

This documentation is a community effort! We welcome contributions:

- **Found an error?** [Open an issue](../../issues/new?template=bug-report.md)
- **Need something documented?** [Request it](../../issues/new?template=documentation-request.md)
- **Have P21 knowledge to share?** [Contribute](../../issues/new?template=contribution.md)
- **Questions?** [Start a discussion](../../discussions)

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - See LICENSE file
