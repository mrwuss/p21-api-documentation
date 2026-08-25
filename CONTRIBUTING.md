# Contributing to P21 API Documentation

> **Note:** This is unofficial, community-created documentation not affiliated with Epicor Software Corporation.

Thank you for your interest in improving P21 API documentation! This project aims to be the comprehensive resource for Prophet 21 API integration that the community deserves.

## Ways to Contribute

### 1. Report Issues
- Found an error in the docs? [Open a bug report](../../issues/new?template=bug-report.md)
- Something unclear? [Request clarification](../../issues/new?template=documentation-request.md)

### 2. Request Documentation
- Need docs for an API endpoint we haven't covered?
- Have a use case that should be documented?
- [Submit a documentation request](../../issues/new?template=documentation-request.md)

### 3. Share Your Knowledge
- Have working P21 API code? Share it!
- Discovered undocumented behavior? Tell us!
- [Submit a contribution](../../issues/new?template=contribution.md)

### 4. Submit Pull Requests
1. Fork the repository
2. Create a branch (`git checkout -b feature/new-endpoint-docs`)
3. Make your changes
4. Test any code examples
5. Submit a PR

## Guidelines

### Documentation Standards
- **Facts only** - No guesses about undocumented behavior; disputed or community-reported behavior gets live-verified before it's documented
- **Verified examples** - All code should run without errors
- **Real payloads** - Include actual API request/response examples (generalized placeholder data only — `ACME`, `WIDGET-001`, `play.p21server.com`; never real company/customer identifiers)
- **Note limitations** - Document known issues and workarounds
- **Keep the routing layer in sync** - new task-worthy sections get a row in [docs/INDEX.md](docs/INDEX.md); renaming a heading must update its index anchors

### Code Examples

Every example that calls P21 is a **complete program**: paste it into a file, edit the constants at the top, run it. No repo clone, no `.env`, no helper imported from another page. A reader should never have to assemble an example from two places.

- **Both languages, adjacent**: Python (`httpx`) *and* C#, inside `<!-- tabs -->` / `<!-- /tabs -->` markers. `scripts/generate_html.py` builds the tab labels from the **fence language**, so the fence goes directly after the opening marker; it discards other text inside the region. Match whatever label style the file you are editing already uses.
- **Zero install beyond the language**: Python needs only `httpx`. C# targets **`net8.0` or later** with `ImplicitUsings` + `Nullable` and **System.Text.Json** — no NuGet packages, so `dotnet new console` + paste + `dotnet run` works. `net8.0` is the floor because that is the SDK the [csharp examples](examples/csharp/README.md) ask you to install; all 80 complete C# page programs are verified to build on it. Do not introduce Newtonsoft or `Microsoft.Extensions.*` into a docs example.
- **An `EDIT THESE` block at the top** holding `BASE_URL`, credentials, `VERIFY_SSL` and the task's own variables — one per line with a trailing comment. Copy the auth preamble verbatim from an existing converted example (e.g. [reassign-salesrep](docs/recipes/reassign-salesrep.md)) rather than writing your own; it handles the v2 token, the router 307, and the XML fallback.
- **Only where it is used**: include the UI-server helper for Transaction/Interactive examples; omit it for OData, Entity, Inventory REST and UDT, which call `BASE_URL` directly.
- **Every write ends in a read-back** that prints what actually landed. In this API HTTP 200 routinely lies — a save can report success and write nothing.
- **Illustrative fragments stay fragments.** A payload shape, a two-line field-order demonstration or an error sample should not be inflated into a full program; add a `Full runnable version:` callout linking to the nearest one.
- **V2 auth only** for username/password (credentials in the request body); the V1 header form leaks credentials into proxy/server logs. A 26.1 session failure is *not* a reason to fall back to V1 — see [Breaking Changes entry 1](docs/14-Breaking-Changes.md#1-interactive-api-returns-an-empty-http-500-without-an-explicit-accept-applicationjson-header).
- Include error handling — check `Summary.Succeeded`/`Failed`, never the HTTP status alone
- Validate example payloads with `python scripts/validate_payload.py <file>` (works for JSON and XML)
- Add comments explaining P21-specific behavior
- Test against a P21 environment before submitting

Before opening the PR, check the examples mechanically: every Python block should parse (`ast.parse`), and every complete C# block should build in a scratch `net8.0` console project. "Complete" excludes blocks the prose labels a **structural sketch** (elided bodies, a usage trailer calling methods defined elsewhere) — those are illustrations and are not expected to compile.

### What We're Looking For
- Additional API endpoints not yet documented
- Real-world integration examples
- P21 version-specific differences
- Performance tips and best practices
- Error messages and their solutions

## Questions?

Use [GitHub Discussions](../../discussions) for questions and community help.

## Recognition

Contributors will be recognized in the project. Thank you for helping the P21 community!
