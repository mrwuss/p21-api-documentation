# P21 Service Definitions (Schema Library)

Raw Transaction API **service definitions** — one JSON per P21 window/service, fetched from a live P21 system. **All 36 files were re-fetched together from 26.1.5940.0 on 2026-08-29**, so the folder is internally consistent rather than a mix of builds. This is the authoritative full-field schema for building payloads: every service's tabs, datawindows, key fields, and field definitions (`DbColumnName`, `DataType`, `Required`, `Label`), plus a ready-to-populate `Template` payload skeleton. [`_manifest.json`](_manifest.json) records the fetch date and the exact service list; a partial `--services` refresh updates only the services it touches, which is the one way the folder can drift back into a mix of builds.

> **Definitions are build-specific, and that matters more than it looks.** Which columns a window disables shifts between builds — a field that is `Required` or writable here may not be on yours. Treat these as a strong starting point and confirm against your own tenant with `GET /api/v2/definition/{Service}` before relying on a field being writable. See [Breaking Changes entry 6](../docs/14-Breaking-Changes.md#6-batched-v2change-is-not-atomic-it-is-sequential-and-fail-fast) for a case where exactly that shift retired a documented repro.

Load **one file for the service you're working on** — don't read the folder.

## What's in each file

Each `<ServiceName>.json` is the (sanitized) response of `GET {ui_server}/api/v2/definition/{ServiceName}`:

- `TransactionDefinition.KeyDefinitions` — the service's key fields.
- `TransactionDefinition.DataElementDefinitions[]` — every tab/datawindow with its `KeyFields` and `FieldDefinitions` (this is where you find field names and types).
- `Template.TransactionSet` — a payload skeleton with every field name and empty values. Copy it, fill the `Edits` you need, delete the rest (or set `IgnoreIfEmpty`), and submit.

> **Read `ValidValues`, not just the field names.** It is the most under-used part of a definition: it publishes the exact strings a field accepts under the default `UseCodeValues: false`, which is how you learn to send `Delete` rather than the `code_p21` integer `700`, and `ON` rather than `Y`. It also answers capability questions the field list alone gets wrong — a grid with no `delete_flag` is not necessarily a grid you cannot delete from, it may simply delete through a differently-named field. Worked example: [03 § Removing a Salesrep Grid Row](../docs/03-Transaction-API.md#customer-service-removing-a-salesrep-grid-row).
>
> ```bash
> python -c "import json;d=json.load(open('definitions/Customer.json'));[print(e['Name'],'|',f['Name'],f['DataType'],f['ValidValues']) for e in d['TransactionDefinition']['DataElementDefinitions'] for f in e['FieldDefinitions'] if f['ValidValues']]"
> ```

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

- **Validate a payload against these schemas** (offline, JSON or XML): `python scripts/validate_payload.py my_payload.json` — checks structure, types, element/field names, and known ordering rules. See [Payload Anatomy](../docs/03-Transaction-API.md#payload-anatomy-types-nesting-and-common-mistakes).
- **XML users:** fetch a definition with `Accept: application/xml` and the `Template` subtree is the correctly-ordered XML skeleton — see [XML Payloads](../docs/03-Transaction-API.md#xml-payloads-content-negotiation).

## Services included

**36 services**, and this list, [`_manifest.json`](_manifest.json) and `DOCUMENTED_SERVICES` in [`scripts/fetch_definitions.py`](../scripts/fetch_definitions.py) are kept in agreement — a default `python scripts/fetch_definitions.py` refreshes exactly the files in this folder, no more and no less. If you add a definition, add it to the fetch list in the same commit.

| Area | Services |
|---|---|
| Sell side | `Order`, `RMA`, `ShipTo`, `Shipping`, `Customer`, `Address`, `Salesrep` |
| Buy side | `PurchaseOrder`, `PurchaseOrderReceipt`, `ConvertPOToVoucher`, `RequisitionPurchaseOrder`, `VoucherByItem`, `Supplier` |
| Inventory | `Item`, `ItemDefaults`, `InventoryAdjustment`, `BinLocation`, `PickZone`, `PutawayZone`, `Assembly` |
| Pricing | `SalesPricePage`, `SalesPriceBook`, `JobContractPricing`, `PurchasePricingPageSupplier`, `PurchasePricingPageSupplierDiscGrp`, `PurchasePricingPageSupplierItem` |
| Production & labor | `ProductionOrder`, `ProductionOrderPicking`, `ProductionOrderProcessing`, `Labor`, `LaborProcess`, `TimeEntry` |
| Reports (`m_*`, hidden from `/api/v2/services` but callable) | `m_picktickets`, `m_reprintpicktickets`, `m_reprintpurchaseorders`, `m_storedprocedureexecutor` |

**Not every service named in `docs/` has a file here, and that is deliberate** — the folder holds the services whose *schema* the documentation leans on, not every service it mentions. The gap is small and closing; if a doc page references a service you cannot find here, fetch it yourself with `--services {Name}`.

The pricing set is worth knowing as a group: sales price pages (`SalesPricePage`), the book that collects them (`SalesPriceBook`), job contracts (`JobContractPricing`), and the three purchase-side page variants — each with its own key set and, unhelpfully, its own name for the break fields. See [08 § Cross-Service Break-Field Names](../docs/08-SalesPricePage-Codes.md#cross-service-break-field-names).

> **Credit:** the schema-library pattern comes from [Alex Westemeier](https://github.com/AWestemeier)'s process playbook.
