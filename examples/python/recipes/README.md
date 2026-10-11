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
| `update_supplier_contact.py` | [update-supplier-contact.md](../../../docs/recipes/update-supplier-contact.md) |

### Reference-doc examples

These have no recipe page; each runs the write path of a reference-doc section and links back to it. The Interactive ones share [`common/interactive_session.py`](../common/interactive_session.py); the C# versions share `examples/csharp/Recipes/InteractiveHelpers.cs`.

| Script | C# (Recipes menu) | Doc section |
|--------|-------------------|-------------|
| `sales_price_page_create_link.py` | `SalesPricePageCreateLink.cs` (16) | [08 § Creating a Page Through the Transaction API](../../../docs/08-SalesPricePage-Codes.md#creating-a-page-through-the-transaction-api) |
| `purchase_pricing_page_edit.py` | `PurchasePricingPageEdit.cs` (17) | [08 § Editing a Supplier/Item Purchase Page](../../../docs/08-SalesPricePage-Codes.md#editing-a-supplieritem-purchase-page-purchasepricingpagesupplieritem) |
| `inventory_update_list_price_stockable.py` | `InventoryUpdateListPriceStockable.cs` (18) | [11 § Updating Existing Location Fields](../../../docs/11-Inventory-REST-API.md#updating-existing-location-fields) |
| `order_entry_quote_off.py` | `OrderEntryQuoteOff.cs` (19) | [04 § Set `quote` to `OFF` first](../../../docs/04-Interactive-API.md#set-quote-to-off-first-the-window-can-open-in-quote-mode) |
| `direct_ship_confirmation.py` | `DirectShipConfirmation.cs` (20) | [04 § The Interactive path works](../../../docs/04-Interactive-API.md#the-interactive-path-works) |
| `customer_price_library.py` | `CustomerPriceLibrary.cs` (21) | [04 § Customer Window: Adding a Price Library](../../../docs/04-Interactive-API.md#customer-window-adding-a-price-library) |
| `dynachange_rule_toggle.py` | `DynaChangeRuleToggle.cs` (22) | [04 § Managing Business Rules Through the DynaChange Organizer](../../../docs/04-Interactive-API.md#managing-business-rules-through-the-dynachange-organizer) |

`purchase_pricing_page_edit.py` reads the page before its dry run, so that dry run needs credentials. The Interactive scripts print their planned calls as the dry run.

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
