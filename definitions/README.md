# P21 Service Definitions (Schema Library)

Raw Transaction API **service definitions** — one JSON per P21 window/service, fetched from a live P21 system (most from 25.2; `ConvertPOToVoucher`, `RequisitionPurchaseOrder`, `Salesrep`, and `VoucherByItem` from 26.1.5894.1). This is the authoritative full-field schema for building payloads: every service's tabs, datawindows, key fields, and field definitions (`DbColumnName`, `DataType`, `Required`, `Label`), plus a ready-to-populate `Template` payload skeleton. `_manifest.json` records the per-run fetch date; a partial `--services` refresh updates only the services it touches.

Load **one file for the service you're working on** — don't read the folder.

## What's in each file

Each `<ServiceName>.json` is the (sanitized) response of `GET {ui_server}/api/v2/definition/{ServiceName}`:

- `TransactionDefinition.KeyDefinitions` — the service's key fields.
- `TransactionDefinition.DataElementDefinitions[]` — every tab/datawindow with its `KeyFields` and `FieldDefinitions` (this is where you find field names and types).
- `Template.TransactionSet` — a payload skeleton with every field name and empty values. Copy it, fill the `Edits` you need, delete the rest (or set `IgnoreIfEmpty`), and submit.

`_manifest.json` records the fetch date and any services that failed.

## Sanitization (why some ValidValues are empty)

Raw definitions embed **live instance data**, not just schema — `ValidValues` for lookup-backed dropdowns (carriers, payment terms, class codes, custom cost sources) are pulled from the source system's tables. Committed files are sanitized by `scripts/fetch_definitions.py`:

- Fields named `ufc_*` (user-defined columns — instance-specific schema) are **removed**.
- `ValidValues` are kept only for boolean-style lists and a reviewed allowlist of standard P21 enums; everything else is emptied and marked `"ValidValuesRedacted": true`.

To see the full dropdown contents for **your** environment, refresh locally:

```bash
python scripts/fetch_definitions.py                    # the documented services
python scripts/fetch_definitions.py --services Order   # one service
python scripts/fetch_definitions.py --all              # everything /api/v2/services lists
```

Set `P21_SCRUB_TERMS` (comma-separated company identifiers) before publishing any fetched output; the script refuses to write a file still containing a listed term.

> **Note:** some services return HTTP 500 *"Window <<X>> is not available or user does not have permission"* — that's an environment-availability signal (unlicensed/undeployed module), not a grantable permission. See the [Transaction API guide](../docs/03-Transaction-API.md#endpoints).

## Related tools

- **Validate a payload against these schemas** (offline, JSON or XML): `python scripts/validate_payload.py my_payload.json` — checks structure, types, element/field names, and known ordering rules. See [Payload Anatomy](../docs/03-Transaction-API.md#payload-anatomy----types-nesting-and-common-mistakes).
- **XML users:** fetch a definition with `Accept: application/xml` and the `Template` subtree is the correctly-ordered XML skeleton — see [XML Payloads](../docs/03-Transaction-API.md#xml-payloads-content-negotiation).

## Services included

The services documented in [`docs/`](../docs/INDEX.md): Assembly, BinLocation, ConvertPOToVoucher, Customer, InventoryAdjustment, Item, JobContractPricing, Labor, LaborProcess, Order, ProductionOrder, ProductionOrderPicking, ProductionOrderProcessing, PurchaseOrder, RequisitionPurchaseOrder, Salesrep, SalesPricePage, Shipping, Supplier, TimeEntry, VoucherByItem, and the report services `m_picktickets`, `m_reprintpicktickets`, `m_reprintpurchaseorders`, `m_storedprocedureexecutor`.

> **Credit:** the schema-library pattern comes from [Alex Westemeier](https://github.com/AWestemeier)'s process playbook.
