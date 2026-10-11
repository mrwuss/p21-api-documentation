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
| `create_ship_to.py` | [create-ship-to.md](../../../docs/recipes/create-ship-to.md) |
| `inventory_cost_edit.py` | [inventory-cost-edit.md](../../../docs/recipes/inventory-cost-edit.md) |
| `reprint_purchase_order.py` | [03 § Example: Generate and Save a PO Reprint](../../../docs/03-Transaction-API.md#example-generate-and-save-a-po-reprint) (also [generate-pick-ticket-pdf.md](../../../docs/recipes/generate-pick-ticket-pdf.md)) |
| `clone_item.py` | [11 § Cloning an Existing Item](../../../docs/11-Inventory-REST-API.md#cloning-an-existing-item) — its dry run GETs the source item, so it needs credentials |

## Scripts for Transaction API write paths

These have no recipe page: each is the runnable version of a section of the [Transaction API guide](../../../docs/03-Transaction-API.md). Each has a C# twin in [`examples/csharp/Recipes`](../../csharp/Recipes/) (menu items 20-25), a payload in [`examples/payloads/json`](../../payloads/json/), and reads its result back over OData only. Record IDs are command-line arguments (C#: prompts), so nothing tenant-specific lives in the source.

| Script | C# class | Modes | Doc section |
|--------|----------|-------|-------------|
| `bin_lock_delete.py` | `BinLockDelete` | lock, unlock, delete, restore | [Locking, Unlocking, and Deleting Bins](../../../docs/03-Transaction-API.md#locking-unlocking-and-deleting-bins) |
| `vendor_create.py` | `VendorCreate` | create (vendor + its supplier) | [Vendor Service](../../../docs/03-Transaction-API.md#vendor-service-creating-a-vendor-and-its-supplier) |
| `assembly_create_edit.py` | `AssemblyCreateEdit` | create, set-flag, set-qty, delete-component | [Assembly Service](../../../docs/03-Transaction-API.md#assembly-service) |
| `contract_shipto_line_no.py` | `ContractShipToLineNo` | attach-ship-to, update-line (by `line_no`) | [Attaching a ship-to](../../../docs/03-Transaction-API.md#attaching-a-ship-to-to-an-existing-contract) · [Updating an Existing Contract](../../../docs/03-Transaction-API.md#updating-an-existing-contract) |
| `order_append_hold_cancel.py` | `OrderAppendHoldCancel` | append, release-hold, cancel | [Order Service — Line Appends, Cancels, Holds](../../../docs/03-Transaction-API.md#order-service-line-appends-cancels-holds-and-item-lookup) |
| `item_customer_merge.py` | `ItemCustomerMerge` | item, customer (one-way) | [Item Merge and Customer Merge](../../../docs/03-Transaction-API.md#item-merge-and-customer-merge-m_itemmerge-m_customermerge) |

They share the small helpers in [`common/tapi.py`](../common/tapi.py) (connect, POST with Summary check, OData read-back). Run each with no `--execute` first to see the payload:

```bash
python examples/python/recipes/bin_lock_delete.py lock A01-02-03 --location 10
python examples/python/recipes/order_append_hold_cancel.py append 1001234 --line ITEM-001:2 --line ITEM-002:3
```

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

Configuration constants at the top of each script use generic placeholders (`ACME`, `WIDGET-001`, customer `100198`) — substitute your own values before running. Some scripts also take them as command-line options (`--help` lists them).

## Dry run by default

Every script that writes to P21 **defaults to a dry run**: it builds and pretty-prints the payload, then exits without sending anything (no credentials needed). Pass `--execute` to actually POST — the script then checks `Summary.Succeeded`/`Failed`, prints `Messages`, and runs the recipe's verify read-back (OData or `POST /api/v2/transaction/get`). Always run against a **test/play environment first**; a `Succeeded` response is not proof the value landed.
