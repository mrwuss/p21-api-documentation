---
paths:
  - "docs/**"
  - "examples/**"
  - "definitions/**"
  - "postman/**"
  - "scripts/validate_payload.py"
  - "scripts/test_client.py"
  - "scripts/**"
  - "README.md"
  - "CONTRIBUTING.md"
  - "release-kit.toml"
  - "requirements.txt"
---

## Project Structure

```
p21-api-documentation/
├── docs/
│   ├── INDEX.md                 # Task → section routing map (start here)
│   ├── recipes/                 # Self-contained copy-and-run task pages (one task = one page)
│   ├── 00-Authentication.md
│   ├── 01-API-Selection-Guide.md
│   ├── 02-OData-API.md
│   ├── 03-Transaction-API.md
│   ├── 04-Interactive-API.md
│   ├── 05-Entity-API.md
│   ├── 06-Error-Handling.md
│   ├── 07-Session-Pool-Troubleshooting.md
│   ├── 08-SalesPricePage-Codes.md
│   ├── 09-Batch-Processing-Patterns.md
│   ├── 10-Changelog.md
│   ├── 11-Inventory-REST-API.md
│   ├── 12-Production-Labor-API.md
│   ├── 13-UDT-Service-API.md
│   ├── 14-Breaking-Changes.md
│   ├── 15-Other-REST-Families.md
│   ├── 16-Window-Field-Maps.md
│   ├── img/                     # Screenshots used by the docs (00-Authentication)
│   ├── index.html               # GitHub Pages landing page (redirects into html/)
│   └── html/                    # Generated HTML versions
│
├── definitions/                 # Sanitized full-field service definition JSONs (schema library)
│   └── window-maps/             # Scrubbed field-to-table maps for 7 windows (docs/16)
│
├── examples/
│   ├── python/                  # Python examples
│   │   ├── common/              # Shared auth/config (used by every script)
│   │   ├── odata/ transaction/ interactive/ entity/ production/
│   │   ├── recipes/             # End-to-end recipe scripts (dry-run by default)
│   │   └── rest/                # Other REST families (doc 15) read/write scripts
│   ├── csharp/                  # C# console app examples (P21Examples.sln)
│   │   ├── Common/              # Shared library (auth, config, client)
│   │   ├── OData/ Transaction/ Interactive/ Entity/ Production/
│   │   ├── Recipes/             # End-to-end recipe classes (EXECUTE-gated)
│   │   └── Rest/                # Other REST families (doc 15), menu-driven
│   └── payloads/                # Standalone request payloads, validator-verified
│       ├── json/                # One .json per documented task
│       └── xml/                 # DataContract-correct XML counterparts
│
├── postman/                     # Postman collection (auth, OData, Transaction, Interactive, Entity, other REST families)
│
└── scripts/                     # Repo tooling (NOT API examples)
    ├── README.md                # What each tool does and when to run it
    ├── fetch_definitions.py     # Fetch + sanitize service definitions into definitions/
    ├── validate_payload.py      # Offline payload validator (JSON/XML shape + schema checks)
    ├── check_anchors.py         # Validate internal doc links against the generated HTML
    ├── test_client.py           # Smoke-test client against a live tenant
    └── generate_html.py         # MD to HTML converter (supports tabbed code blocks)
```
