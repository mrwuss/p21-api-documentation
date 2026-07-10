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
- **Both languages**: documentation code blocks come in Python (`httpx`) *and* C# (`HttpClient` + Newtonsoft) tabs — see any recipe page for the format
- **V2 auth only** for username/password (credentials in the request body); the V1 header form leaks credentials into proxy/server logs
- Include error handling — check `Summary.Succeeded`/`Failed`, never the HTTP status alone
- Verify writes with a read-back (OData or `POST /api/v2/transaction/get`)
- Validate example payloads with `python scripts/validate_payload.py <file>` (works for JSON and XML)
- Add comments explaining P21-specific behavior
- Test against a P21 environment before submitting

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
