# Recipe Scripts

End-to-end runnable Python versions of the [cookbook recipes](../../../docs/recipes/README.md). Each script mirrors its page's Python example, adapted to this repo's conventions (`common.auth` / `common.config` instead of the inline `p21_auth()` helper). Most recipe pages have one; the pages not listed below are page-only for now, and their tabs are still complete standalone programs.

| Script | Recipe page |
|--------|-------------|
| `update_contract_lines.py` | [update-contract-lines.md](../../../docs/recipes/update-contract-lines.md) |
| `update_order_lines.py` | [update-order-lines.md](../../../docs/recipes/update-order-lines.md) |
| `edit_contract_bins.py` | [edit-contract-bins.md](../../../docs/recipes/edit-contract-bins.md) |
| `create_bins.py` | [create-bins.md](../../../docs/recipes/create-bins.md) |
| `create_sales_order.py` | [create-sales-order.md](../../../docs/recipes/create-sales-order.md) |
| `order_with_assembly.py` | [order-with-assembly.md](../../../docs/recipes/order-with-assembly.md) |
| `set_primary_bin_supplier.py` | [set-primary-bin-supplier.md](../../../docs/recipes/set-primary-bin-supplier.md) |
| `generate_pick_ticket_pdf.py` | [generate-pick-ticket-pdf.md](../../../docs/recipes/generate-pick-ticket-pdf.md) |
| `production_order_runbook.py` | [production-order-runbook.md](../../../docs/recipes/production-order-runbook.md) |
| `record_labor_time.py` | [record-labor-time.md](../../../docs/recipes/record-labor-time.md) |
| `inventory_adjustment.py` | [inventory-adjustment.md](../../../docs/recipes/inventory-adjustment.md) |
| `create_customer.py` | [create-customer.md](../../../docs/recipes/create-customer.md) |
| `create_requisition_po.py` | [create-requisition-po.md](../../../docs/recipes/create-requisition-po.md) |
| `reassign_salesrep.py` | [reassign-salesrep.md](../../../docs/recipes/reassign-salesrep.md) |

## Setup

```bash
cp .env.example .env   # set P21_BASE_URL, P21_USERNAME, P21_PASSWORD
pip install -r requirements.txt
python examples/python/recipes/create_sales_order.py           # dry run
python examples/python/recipes/create_sales_order.py --execute # write + verify
```

Configuration constants at the top of each script use generic placeholders (`ACME`, `WIDGET-001`, customer `100198`) — substitute your own values before running.

## Dry run by default

Every script that writes to P21 **defaults to a dry run**: it builds and pretty-prints the payload, then exits without sending anything (no credentials needed). Pass `--execute` to actually POST — the script then checks `Summary.Succeeded`/`Failed`, prints `Messages`, and runs the recipe's verify read-back (OData or `POST /api/v2/transaction/get`). Always run against a **test/play environment first**; a `Succeeded` response is not proof the value landed.
