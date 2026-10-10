# Purchasing: Stock PO → Receipt → Voucher, and Drop Ship

The two buy-side paths that end in a vendor voucher in AP: bringing items into stock (create the PO, receive it, vouch it), and drop ship, where the vendor ships straight to the customer (sales order line → direct-ship PO → confirmation → voucher).

**API:** Transaction + Interactive · **Services:** `PurchaseOrder`, `PurchaseOrderReceipt`, `ConvertPOToVoucher`, `Order` (+ its PO wizard), `DirectShipConfirmation` · **Deep dive:** [PurchaseOrder](../03-Transaction-API.md#purchaseorder-service-creating-a-po) · [PurchaseOrderReceipt](../03-Transaction-API.md#purchaseorderreceipt-service-receiving-a-po) · [ConvertPOToVoucher](../03-Transaction-API.md#convertpotovoucher-service-vouching-a-receipt) · [Driving an In-Window Wizard](../04-Interactive-API.md#driving-an-in-window-wizard-direct-ship-po-generation)

This page is a **checklist**, not a script: it strings together sections of the manual that each carry the payload and the traps. For a different PO type, see [create-requisition-po](create-requisition-po.md).

**Status legend:** **Verified** = run with a read-back on a play tenant (August–October 2026), by the credited contributor and, where marked, re-verified in this repo; **Inferred** = follows from verified behavior but was not run as its own step.

## Path A — bring items into stock

| # | Step | Surface | Read-back |
|---|---|---|---|
| A1 | Create the PO | Transaction `PurchaseOrder` | `po_hdr` (`approved`), `po_line` |
| A2 | Receive it | Transaction `PurchaseOrderReceipt` when every line has a usable primary bin; otherwise Interactive | `inventory_receipts_hdr` / `_line`, `po_line.qty_received`, `inv_bin` |
| A3 | Vouch the vendor invoice | Transaction `ConvertPOToVoucher` | `apinv_hdr`, `apinv_line`, receipt lines `vouch_complete = 'Y'` |

**A1 — Create (Verified, re-verified here).** Header `TABPAGE_1.tp_1_dw_1`: `location_id`, `vendor_id`, `buyer_id` (an employee **number**, stored in `po_hdr.requested_by`), `order_date`, `required_date` (genuinely required), optional `external_po_no` to tag the run. Lines `TABPAGE_17.tp_17_dw_17`: `item_id`, `unit_quantity`, `unit_of_measure`, `pricing_unit`, and the price in **`unit_price_display`** — not `unit_price`. Omit `division_id` and `company_id`; they default. [Manual](../03-Transaction-API.md#purchaseorder-service-creating-a-po).

**A2 — Receive (Verified, both surfaces).** Header `TABPAGE_1.tp_1_dw_po`: `po_no`, then `receive_all` = `Y`. That is the whole Transaction payload **when every line's item has a usable primary bin** (re-verified here). When a line has none — typically a primary bin of `0` that is put-locked — the Transaction API cannot address the bin grid, because its rows land on whichever line is selected. Drive the window instead: for each such line, find its row in `tp_17_dw_17` (the column `ufc_inv_loc_primary_bin` shows `0`), `select_row` it, change to `TABPAGE_BIN`, set `bin_cd` and `unit_quantity` on `tabpage_bin`, then save. The receipt number is not in the window after the save; find it by `po_number` in `inventory_receipts_hdr` (lines use `line_number`, not `line_no`). [Manual](../03-Transaction-API.md#purchaseorderreceipt-service-receiving-a-po).

**A3 — Vouch (Verified, re-verified here).** Header `TABPAGE_1.tp_1_dw_1` (key `voucher_no`, left empty): `po_no`, `invoice_no`, `invoice_date`, `invoice_amount` (the real invoice total — it must equal the vouched lines or P21 holds the variance), `vendor_id`. Lines keyed `receipt_number` + `line_number` + `po_no`: `unit_qty_invoiced`, `unit_cost_display`. **Send nothing else** — `company_id`, `branch_id`, `period`, `year_for_period` are marked required and are disabled columns. The voucher lands approved and unpaid. [Manual](../03-Transaction-API.md#convertpotovoucher-service-vouching-a-receipt).

## Path B — drop ship

| # | Step | Surface | Read-back |
|---|---|---|---|
| B1 | Sales order with a direct-ship line (`disposition` = `D`), saved | Interactive `Order` | `oe_line.disposition = 'D'`, `po_cost` |
| B2 | Re-open the order, `c_create_po` = `ON`, save → PO wizard: `cb_next`, `cb_finish` | Interactive `Order` + wizard response window | `po_hdr` (`po_type = 'D'`), `oe_line_po` (`connection_type = 'P'`) |
| B3 | Vendor ships; confirm the direct ship — receipt **and** customer invoice | Interactive `DirectShipConfirmation` (see note) | `inventory_receipts_hdr` (type `P`), `po_line` complete, `oe_line.qty_invoiced`, `invoice_hdr` |
| B4 | Vouch the vendor invoice against that receipt | Transaction `ConvertPOToVoucher` (as A3) | as A3 |

**B1 — The direct-ship line (Verified).** `disposition` can be set **only while the line is being entered**, in the window — never on a saved line, never through the Transaction API. **Set `quote` = `OFF` first**: in quote mode `disposition` looks disabled and the wizard later builds an RFQ instead of a PO ([details](../04-Interactive-API.md#set-quote-to-off-first-the-window-can-open-in-quote-mode)). The header needs `contact_id`. Key the deal's buy price into the line's `po_cost`: it flows to the PO line's price, and without it the PO inherits the supplier's standard cost.

**B2 — Two saves, then the wizard (Verified, re-verified here).** Requesting the PO in the same save that creates the order derails — a new order's save stacks other prompts ahead of the wizard. Save the order, re-open it, set `c_create_po` = `ON`, save. The response window is the wizard only if its tools include `cb_finish`; check before pressing anything.

- The API user needs a **Buyer ID** in User Maintenance, or the trigger refuses.
- `supplier_id` on the wizard is disabled to the API: it defaults to the item's primary supplier. When supplier choice matters, a person creates the PO.
- **The PO is committed at `cb_next`, before `cb_finish`.** An abandoned wizard is not a no-op — go and look for the PO.

**B3 — Confirm the direct ship (Verified — see note).** Interactive `DirectShipConfirmation`: set `TABPAGE_1.tp_1_dw_po.po_no`, `receive_all` = `ON`, save. One save writes the receipt, completes the PO lines, invoices the sales-order lines and creates the customer's invoice. **Do not** try `PurchaseOrderReceipt` on a direct-ship PO; it refuses because the linked sales lines are locked. The confirmation also **overwrites `po_line.supplier_ship_date` on every line** — capture it first if you confirm partials ([details](../04-Interactive-API.md#directshipconfirmation-writes-its-ship-date-down-onto-every-line)).

> **Note — which surface.** The Interactive path above is verified on play 26.1 (October 2026). A Transaction API path (`receive_all` = `Y`, `print_invoice` = `N`, `fax_invoice` = `N`) was reported working on another play tenant in August 2026, but returned an empty no-op result on 26.1.5940.0 in this repo — see [The write path is not reproduced here](../04-Interactive-API.md#the-write-path-is-not-reproduced-here). On either surface, **never send `c_email_invoice`**: it is disabled, and a transaction that tripped on it reported `Failed` **after** writing the receipt, the PO completion and the customer invoice.

**B4 — Vouch (Inferred from A3).** A direct-ship vendor invoice vouches like any other, against the receipt B3 created. A direct-ship PO "with no receipt yet" means the sales side has not confirmed the shipment — it is not a receiving task.

## ⚠️ "Failed" can mean "already committed"

Twice on this path a call reported failure after the work was done: the wizard commits the PO at `cb_next`, and a direct-ship confirmation that tripped on a disabled column had already written the receipt and the invoices. **Treat a failure as "go and read the tables", never as "nothing happened".** See [What `Failed` actually guarantees](../03-Transaction-API.md#what-failed-actually-guarantees).

## Not covered here

Changing or closing a stock PO after creation, receipts for lot- or serial-tracked items, partial receipts across several receipts, and vouchers without a PO (`VoucherByItem`, `ConvertVendorInvoiceToVoucher`) — none verified.

> **Credit:** [Alex Westemeier](https://github.com/AWestemeier) — both paths verified on play, August 2026, with the Interactive receipt, the wizard, the Transaction direct-ship confirmation and the voucher; not re-run here except where marked. Path A's Transaction receipt and voucher and the wizard were re-verified in this repo (August 2026); the Interactive direct-ship confirmation and the quote-mode correction: *@mrwuss*, play 26.1, October 2026 ([#169](https://github.com/mrwuss/p21-api-documentation/issues/169)).
