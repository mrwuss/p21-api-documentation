# Sales Order → Pick Ticket → Invoice

Take a sales order from entry to a customer invoice through the API: create the order, print its pick ticket, then confirm the shipment, which creates the invoice.

**API:** Transaction + Interactive · **Services:** `Order`, `Shipping` · **Deep dive:** [Create Order](../03-Transaction-API.md#create-order) · [Sales Order Entry with Assembly Lines](../04-Interactive-API.md#sales-order-entry-with-assembly-lines) · [Shipping and Invoicing](../12-Production-Labor-API.md#shipping-and-invoicing-the-linked-sales-order)

This page is a **checklist**, not a script. Runnable code for each step: [create-sales-order](create-sales-order.md) (step 1, Transaction), [order-with-assembly](order-with-assembly.md) (step 1, Interactive), [generate-pick-ticket-pdf](generate-pick-ticket-pdf.md) (step 2, report route).

**Status legend:** **Verified** = run end to end with a read-back by the credited contributor on play (many orders) and on production; **Inferred** = follows from verified behavior but was not run as its own step.

## Runbook

| # | Step | Surface | Read-back |
|---|---|---|---|
| 1 | Create the order | Transaction `Order` (plain stock lines) or Interactive `Order` (anything with a prompt) | `oe_hdr`, `oe_line` |
| 2 | Print the pick ticket | Transaction `Order` — `TP_FRONTCOUNTER.tp_frontcounter.print_tix` = `ON` | `oe_pick_ticket` |
| 3 | Confirm the shipment (creates the invoice) | Interactive `Shipping` — retrieve `pick_ticket_no`, save | `invoice_hdr`, `invoice_line` |

### Step 1 — Create the order (Verified)

Header on `TABPAGE_1.order`: `quote` = `OFF` (Interactive — the window [can open in quote mode](../04-Interactive-API.md#set-quote-to-off-first-the-window-can-open-in-quote-mode)), **`sales_loc_id` then `source_loc_id`**, `customer_id`, `ship_to_id`, `contact_id`, `order_date`, `requested_date` (after the order date), `po_no`, `taker`. Lines on `TP_ITEMS.items`: `oe_order_item_id`, `unit_quantity`, and `unit_price` only if you are overriding pricing.

Choose the surface by the prompts the order will raise — the Transaction API answers every prompt with its default, usually No:

- **"Add as assembly?"** on a production-order assembly item: **Yes** (`cb_1`) makes a production-order line and, if the assembly auto-creates, spawns and links a production order. **No** (`cb_2`) makes a plain stock line that can never become a production-order line later. Interactive only for Yes.
- **Date cascade** when the dates are set: answer `cb_ok`.
- **Salesrep not allowed at a location** (a site DynaChange rule): pick a sales/source location pair the customer's rep is valid at.

`source_loc_id` is the ship-from location. It decides `oe_line.supplier_id` (the item's primary supplier **there**), which in turn decides any supplier rebate at invoice — see [Rebate prerequisites](../03-Transaction-API.md#rebate-prerequisites-other-cost-value-a-rebate-tracking-vendor).

**Contract pricing binds here, once.** If the customer, ship-to and item are on an approved contract in date, the line gets the contract price, `job_price_hdr_uid`, and a snapshot of the contract cost. That binding is permanent for the line — [details](../03-Transaction-API.md#binding-happens-once-at-line-entry).

Read back: `oe_hdr` (the new `order_no` — in the Transaction response rows; on the Interactive path, find the order by its newest `oe_hdr_uid`, because `order_no` is a string and does not sort numerically), `oe_line` (`assembly`, `disposition`, `qty_allocated`, `supplier_id`, `job_price_hdr_uid`, `other_cost`). An order on Hold has `packing_basis = 'Hold'`; release it before step 2.

### Step 2 — Print the pick ticket (Verified)

Transaction `Order`, `TABPAGE_1.order` keyed on `order_no`, plus `TP_FRONTCOUNTER.tp_frontcounter` with `print_tix` = `ON`. It creates `oe_pick_ticket` and returns the PDF in `Results.Transactions[].Documents[].DocumentData`. It allocates nothing new: a backordered line is simply not on the ticket.

Read back the newest `pick_ticket_no` for the order from `oe_pick_ticket`.

### Step 3 — Confirm the shipment and invoice (Verified)

Interactive `Shipping`: set `pick_ticket_no` on `TABPAGE_1.tp_1_dw_1`; optionally set picked quantities on the items grid; leave `create_invoice` ("Confirm Shipment") at its default `ON`; save, and answer the proceed prompts with their Yes/OK button (`cb_1` / `cb_ok` / `cb_yes`). Never answer `cb_cancel`.

- **Partial shipments work** — the ticket ships what it carries; print another ticket later for the rest.
- **Usual blockers:** an item with no packaging code (the save refuses), and an order left in a `t~` status by a crashed session (re-open the order in the `Order` window, save it, then ship — [details](../06-Error-Handling.md#locks-and-orphaned-sessions)).
- For a direct-ship line the invoice comes from Direct Ship Confirmation instead — see [purchase-receive-vouch](purchase-receive-vouch.md#path-b-drop-ship).

**Shortcut for counter sales (Verified on play 26.1):** on the Interactive `Order` window, `fc_create_invoice` = `ON` with `quote` = `OFF` on a stocked line creates the pick ticket **and** the invoice in the order's own save.

## Verify

- `invoice_hdr` by `order_no`; `invoice_line`: `unit_price`, `other_cost`, `commission_cost`, `cogs_amount`, `supplier_id`.
- Inventory relieved at the source location; `oe_line.qty_invoiced` = shipped.
- **What the invoice cost should be:** for a line bound to a contract with an other cost, the contract value (re-read at invoicing); otherwise the item's moving average cost at the source location. Commission cost: a contract `Value` × its multiplier, or COGS × the multiplier for type `Order` — [table](../03-Transaction-API.md#order-entry-effect-of-each-commission-cost-setting).
- **If a rebate should have fired:** a `vendor_rebate` row for the invoice, and GL rows for the invoice showing the Sales Journal at full moving average cost plus a Rebate Journal entry for the difference.

> **Credit:** [Alex Westemeier](https://github.com/AWestemeier) — runbook verified on play (dozens of orders) and production, September 2026; not re-run here. The counter-sale shortcut and the commission-cost results: *@mrwuss*, play 26.1, October 2026 ([#169](https://github.com/mrwuss/p21-api-documentation/issues/169)).
