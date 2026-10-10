# Dispose of Zero-Value Stock with a $0 Order

Ship unwanted stock out of a location on a sales order priced at $0, to an internal "disposal" customer, so the units leave inventory through the normal pick → ship → invoice path at their already-written-down cost.

**API:** Interactive + Transaction · **Services:** `Order`, `Shipping` · **Before this:** [inventory-cost-edit](inventory-cost-edit.md) · **Deep dive:** [Order Service — Line Appends, Cancels, Holds](../03-Transaction-API.md#order-service-line-appends-cancels-holds-and-item-lookup) · [Large Sales Orders](../09-Batch-Processing-Patterns.md#large-sales-orders-split-at-about-100-lines)

This page is a **checklist**, not a script. Each step names the surface, the fields that matter and the read-back. For runnable code on the individual calls, see [create-sales-order](create-sales-order.md), [update-order-lines](update-order-lines.md) and [generate-pick-ticket-pdf](generate-pick-ticket-pdf.md).

**Status legend:** **Verified** = run end to end with a read-back by the credited contributor (play and production, September 2026); **Inferred** = follows from verified behavior but was not run as its own step.

## Prerequisites

- **The cost is already written down** at the location ([inventory-cost-edit](inventory-cost-edit.md)), so the shipment relieves inventory at the token cost.
- **A disposal customer and ship-to exist** (here `CUST-DISPOSAL`), with a contact.
- **A sales rep that is allowed at the location.** Many sites carry a DynaChange rule that refuses a rep at a location it is not assigned to, and another that refuses two full-commission reps on one order. Know which rep the order must carry (here `REP-HOUSE`) and whether the customer's **default** rep passes your rules.
- Run against a test/play environment first.

## Runbook

### Step 1 — Build the item list from live data (Verified)

Read `inv_loc` at the location for items whose `moving_average_cost` equals your token cost and `qty_on_hand > 0`, and check `qty_allocated = 0`. Write `item_id, qty` from that — **never** from the count spreadsheet. Between a count and the disposal run, items move, quantities get keyed wrong, and [merged items](../06-Error-Handling.md#transaction-api-errors) fail with *"'X' has been deleted"*.

### Step 2 — Create the header and line 1 (Interactive) (Verified)

Use the Interactive `Order` window when the customer's default rep would trip a rep rule — the Transaction API cannot replace the default rep on a new order (any rep row you send is [added on top of it](../03-Transaction-API.md#order-service-line-appends-cancels-holds-and-item-lookup), and two full-commission rows fail).

1. `TABPAGE_1.order`: **`quote` = `OFF` first** ([why](../04-Interactive-API.md#set-quote-to-off-first-the-window-can-open-in-quote-mode)), `sales_loc_id`, `source_loc_id`, `customer_id`, `ship_to_id`, `contact_id`, `order_date`, `requested_date` = tomorrow (answer the date-cascade prompt with `cb_ok`), `po_no` (a recognizable label such as the month and year), `taker` (the real person — it defaults to the API user).
2. `TP_SALESREPS`: select row 1, set `salesrep_id` to the rep the order must carry. No popup.
3. Put the order on Hold (`packing_basis` = `Hold`) so it does not pick before you finish. On some tenants the header copy is disabled; use `TP_SHIPINFO.shipinfo` instead.
4. `TP_ITEMS.items`: the first line on the existing row — `oe_order_item_id`, `unit_quantity`, `unit_price` = `0`. Answer *"add as assembly?"* with **No** (`cb_2`) so kits go in as plain lines.
5. Save. Read back `oe_hdr` and `oe_hdr_salesrep` — exactly one rep row, the one you set.

If the customer's default rep already passes your rules, skip the Interactive step and create the whole order with the Transaction API in one POST (Inferred — the faster form, not run).

### Step 3 — Append the remaining lines (Transaction) (Verified)

One Transaction per order: header `TABPAGE_1.order` keyed on `order_no`, and **all** remaining lines as rows of one `TP_ITEMS.items` element (`Keys: []`), each with `oe_order_item_id`, `unit_quantity`, `unit_price` = `0`.

- **Never one Transaction per line** — rows collide with the existing line (*"Item ID X has been saved; therefore, the Item ID cannot be edited"*).
- **Hundreds of lines → split into orders of about 100.** Per-line time grows with the order's size; ten 100-line orders ran at a flat speed where one thousand-line order took twice as long ([numbers](../09-Batch-Processing-Patterns.md#large-sales-orders-split-at-about-100-lines)). Suffix each order's `po_no` (`- 01`, `- 02`, …).
- **A line that cannot allocate fails the whole Transaction** — *"The order line does not have a PO Cost specified. Proceed?"* is auto-answered No. The failed rows stay behind soft-deleted ([details](../03-Transaction-API.md#a-failed-create-leaves-rows-behind)); re-read live rows before any retry. On a test tenant, leftover test orders holding the same stock cause this — cancel them first.
- **If the order is locked by your own API user, wait** — a killed client's Transaction is still running ([details](../06-Error-Handling.md#locks-and-orphaned-sessions)).

### Step 4 — Release the Hold (Transaction) (Verified)

`TABPAGE_1.order` keyed on `order_no`, then `TP_SHIPINFO.shipinfo` (`Keys: []`) with `packing_basis` = `Partial`. Allocation is untouched. From here a scheduled pick run, or the warehouse, can take over.

### Step 5 — Pick ticket, ship, and $0 invoice (Verified on play)

1. Pick ticket: Transaction `Order`, `TABPAGE_1.order` keyed on `order_no`, `TP_FRONTCOUNTER.tp_frontcounter` with `print_tix` = `ON`. Read the new ticket from `oe_pick_ticket`.
2. Ship: Interactive `Shipping` — set `pick_ticket_no` on `TABPAGE_1.tp_1_dw_1`, leave `create_invoice` at its default ON, save. **Every $0 line raises an "item is unpriced — ship anyway?" prompt**; answer each with `cb_1`. On the API side they cost a few hundredths of a second each with no slowdown (the growing delay users see is the desktop client). Never answer with `cb_cancel`.
3. A save `Status` of 1 or 2 are both normal here — judge by the invoice row, not the status.

## Verify

| After | Check |
|---|---|
| Steps 2–3 | `oe_hdr`: `taker`, `packing_basis`, `completed = 'N'`, `cancel_flag = 'N'`; `oe_hdr_salesrep`: one row, the intended rep, primary. `oe_line` **filtered on `delete_flag = 'N' AND cancel_flag = 'N'`**: every item once across all orders, `qty_ordered` = the list, `SUM(qty_allocated) = SUM(qty_ordered)`, `MAX(unit_price) = 0`, ship and source location = the location |
| Step 4 | `oe_hdr.packing_basis = 'Partial'`; allocation unchanged |
| Step 5 | `invoice_hdr` total $0; `invoice_line.cogs_amount` = units × the token cost; `oe_line.qty_invoiced` = ordered; `inv_loc.qty_on_hand` relieved |

**To back out** a test order: Transaction `Order`, header keyed on `order_no`, `cancel_flag` = `ON` — releases allocation; P21 reloads the order first, so a large one takes minutes.

> **Credit:** [Alex Westemeier](https://github.com/AWestemeier) — run on production (several orders, about a thousand lines) and end to end on play including the API ship-confirm, September 2026; not re-run here.
