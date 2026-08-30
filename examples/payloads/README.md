# Payload Library — Copy-Ready Request Bodies

Standalone request payloads for the documented tasks, for people who work in raw **JSON** or **XML** rather than Python/C#. Every file here is machine-verified with the repo validator:

```bash
python scripts/validate_payload.py examples/payloads/json/update-contract-lines.json
python scripts/validate_payload.py examples/payloads/xml/update-contract-lines.xml
```

Placeholders (`ACME`, `WIDGET-001`, customer `100198`, …) are generic — substitute your own values, then re-run the validator before posting.

## Files

| Task | JSON | XML | Endpoint |
|------|------|-----|----------|
| Update/insert contract lines + commission cost | [json](json/update-contract-lines.json) | [xml](xml/update-contract-lines.xml) | `POST /api/v2/transaction` |
| Edit contract bin quantities | [json](json/edit-contract-bins.json) | [xml](xml/edit-contract-bins.xml) | `POST /api/v2/transaction` |
| Create a warehouse bin | [json](json/create-bins.json) | [xml](xml/create-bins.xml) | `POST /api/v2/transaction` |
| Create a sales order | [json](json/create-sales-order.json) | [xml](xml/create-sales-order.xml) | `POST /api/v2/transaction` |
| Modify an existing sales order (edit a line, add a line) | [json](json/update-order-lines.json) | [xml](xml/update-order-lines.xml) | `POST /api/v2/transaction` |
| Create a customer | [json](json/create-customer.json) | [xml](xml/create-customer.xml) | `POST /api/v2/transaction` |
| Create a requisition PO | [json](json/create-requisition-po.json) | [xml](xml/create-requisition-po.xml) | `POST /api/v2/transaction` |
| Set an item's primary bin | [json](json/set-primary-bin.json) | [xml](xml/set-primary-bin.xml) | `POST /api/v2/transaction` |
| Set an item's primary supplier | [json](json/set-primary-supplier.json) | [xml](xml/set-primary-supplier.xml) | `POST /api/v2/transaction` |
| Add a supplier to an item's location list (prerequisite for the flip) | [json](json/add-supplier-x-loc.json) | [xml](xml/add-supplier-x-loc.xml) | `POST /api/v2/transaction` |
| Enable bin tracking at a location | [json](json/set-track-bins.json) | [xml](xml/set-track-bins.xml) | `POST /api/v2/transaction` |
| Record labor time | [json](json/record-labor-time.json) | [xml](xml/record-labor-time.xml) | `POST /api/v2/transaction` |
| Inventory adjustment (write-off) | [json](json/inventory-adjustment.json) | [xml](xml/inventory-adjustment.xml) | `POST /api/v2/transaction` |
| Reassign a customer's salesrep (promote new, delete old) | [json](json/reassign-salesrep.json) | [xml](xml/reassign-salesrep.xml) | `POST /api/v2/transaction` |
| Update a supplier's email / central phone | [json](json/update-supplier-contact.json) | [xml](xml/update-supplier-contact.xml) | `POST /api/v2/transaction` |
| Retrieve a record (get request) | [json](json/transaction-get-contract.json) | [xml](xml/transaction-get-contract.xml) | `POST /api/v2/transaction/get` |
| Generate a production pick ticket PDF | [json](json/generate-pick-ticket-pdf.json) | — | `POST /api/v2/process/pdfreport` |
| Reprint a purchase order PDF | [json](json/reprint-purchase-order-pdf.json) | — | `POST /api/v2/process/pdfreport` |

## JSON notes

Indentation is cosmetic — **nesting and types** are what matter: `Keys`, `Transactions`, `DataElements`, `Rows`, and `Edits` are always arrays (even with one entry); `UseCodeValues`/`IgnoreDisabled` are booleans, not quoted strings; `Value` is always a string; `IgnoreDisabled` is only honored at the payload top level. Full rules: [Payload Anatomy](../../docs/03-Transaction-API.md#payload-anatomy-types-nesting-and-common-mistakes).

## XML notes

The XML files are in verified **DataContract** shape: the `P21.Transactions.Model.V2` root namespace (mandatory), **alphabetical element order** within every parent (violations get silently dropped or 500), and `Keys` items as `<a:string>` in the Microsoft arrays namespace. Set `Content-Type: application/xml`; `Accept` independently controls the response format. Full rules and verification details: [XML Payloads](../../docs/03-Transaction-API.md#xml-payloads-content-negotiation).

XML versions of the two **report** payloads are omitted: the `/api/v2/process/pdfreport` endpoint has not been verified with XML bodies — the JSON forms are the tested shape.

## Where these come from

Each payload is the canonical example from its [recipe page](../../docs/recipes/README.md), which carries the gotchas, the runnable code, and the verify read-back. For **every field** a service accepts, load its schema from [`definitions/`](../../definitions/README.md).
