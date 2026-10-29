# Purchasing: Stock PO → Receipt → Voucher, and Drop Ship

The two buy-side paths that end in a vendor voucher in AP: bringing items into stock (create the PO, receive it, vouch it), and drop ship, where the vendor ships straight to the customer (sales order line → direct-ship PO → confirmation → voucher).

**API:** Transaction + Interactive · **Services:** `PurchaseOrder`, `PurchaseOrderReceipt`, `ConvertPOToVoucher`, `Order` (+ its PO wizard), `DirectShipConfirmation` · **Deep dive:** [PurchaseOrder](../03-Transaction-API.md#purchaseorder-service-creating-a-po) · [PurchaseOrderReceipt](../03-Transaction-API.md#purchaseorderreceipt-service-receiving-a-po) · [ConvertPOToVoucher](../03-Transaction-API.md#convertpotovoucher-service-vouching-a-receipt) · [Driving an In-Window Wizard](../04-Interactive-API.md#driving-an-in-window-wizard-direct-ship-po-generation)

Every step on this page is a step in one runnable program, in Python and C#, that runs it and reads it back before the next step starts: [`examples/python/recipes/purchase_receive_vouch.py`](../../examples/python/recipes/purchase_receive_vouch.py) · [`examples/csharp/Recipes/PurchaseReceiveVouch.cs`](../../examples/csharp/Recipes/PurchaseReceiveVouch.cs) (menu item 33). Both are dry runs until you pass `--execute` or type `EXECUTE`. For a different PO type, see [create-requisition-po](create-requisition-po.md).

**Status legend:** **Run on play 26.1.5950.0, 2026-10-10** = the step ran in both the Python and the C# runbook against a play tenant on that build and date, with a read-back of the tables named below. **Verified** = run with a read-back on a play tenant (August–October 2026) by the credited contributor.

## Run it

```bash
python examples/python/recipes/purchase_receive_vouch.py                 # dry run: payloads + call plan
python examples/python/recipes/purchase_receive_vouch.py --path A \
    --location 10 --vendor SUP-100 --buyer 100 --item ITEM-001 --qty 2 --price 6.55 --execute
python examples/python/recipes/purchase_receive_vouch.py --path B --auth consumer \
    --location 10 --customer CUST-100 --ship-to CUST-100 --contact 300 --taker JSMITH \
    --ds-item ITEM-002 --ds-qty 3 --ds-price 4.00 --ds-po-cost 2.50 --execute
```

Path B needs an API user with a **Buyer ID**. `--auth consumer` (C#: answer `y` at the consumer-key prompt) writes as `P21_CONSUMER_USERNAME` through `P21_CONSUMER_KEY` — use it when that is the user with the Buyer ID. A consumer key's [OData table allow-list](../00-Authentication.md#odata-table-scopes) can leave out a table the read-back needs (in the verification run `inventory_receipts_hdr` answered `401` to the consumer-key token), so the runbooks read back with the password login when one is configured.

## Path A — bring items into stock

| # | Step | Surface | Read-back | Status |
|---|---|---|---|---|
| A1 | Create the PO | Transaction `PurchaseOrder` | `po_hdr` (`approved`), `po_line` | Run on play 26.1.5950.0, 2026-10-10 |
| A2 | Receive it | Transaction `PurchaseOrderReceipt` when every line has a usable primary bin; otherwise Interactive | `inventory_receipts_hdr` / `_line`, `po_line.qty_received`, `inv_bin` | Run on play 26.1.5950.0, 2026-10-10 (Transaction path) |
| A3 | Vouch the vendor invoice | Transaction `ConvertPOToVoucher` | `apinv_hdr`, `apinv_line`, receipt lines `vouch_complete = 'Y'` | Run on play 26.1.5950.0, 2026-10-10 |

**A1 — Create (Verified; run on play 26.1.5950.0, 2026-10-10).** Header `TABPAGE_1.tp_1_dw_1`: `location_id`, `vendor_id`, `buyer_id` (an employee **number**, stored in `po_hdr.requested_by`), `order_date`, `required_date` (genuinely required), optional `external_po_no` to tag the run. Lines `TABPAGE_17.tp_17_dw_17`: `item_id`, `unit_quantity`, `unit_of_measure`, `pricing_unit`, and the price in **`unit_price_display`** — not `unit_price`. Omit `division_id` and `company_id`; they default. The new `po_no` comes back in the header's result row. [Manual](../03-Transaction-API.md#purchaseorder-service-creating-a-po).

**A2 — Receive (Verified, both surfaces; Transaction path run on play 26.1.5950.0, 2026-10-10).** Header `TABPAGE_1.tp_1_dw_po`: `po_no`, then `receive_all` = `Y`. That is the whole Transaction payload **when every line's item has a usable primary bin**; the new `receipt_number` comes back on the same element's result row. When a line has none — typically a primary bin of `0` that is put-locked — the Transaction API cannot address the bin grid, because its rows land on whichever line is selected. Drive the window instead: for each such line, find its row in `tp_17_dw_17` (the column `ufc_inv_loc_primary_bin` shows `0`), `select_row` it, change to `TABPAGE_BIN`, set `bin_cd` and `unit_quantity` on `tabpage_bin`, then save. The receipt number is not in the window after the save; find it by `po_number` in `inventory_receipts_hdr` (lines use `line_number`, not `line_no`). [Manual](../03-Transaction-API.md#purchaseorderreceipt-service-receiving-a-po). The runbooks implement the Transaction path only: give the item a usable primary bin first ([set-primary-bin-supplier](set-primary-bin-supplier.md)), or receive in the window as described.

**A3 — Vouch (Verified; run on play 26.1.5950.0, 2026-10-10).** Header `TABPAGE_1.tp_1_dw_1` (key `voucher_no`, left empty): `po_no`, `invoice_no`, `invoice_date`, `invoice_amount` (the real invoice total — it must equal the vouched lines or P21 holds the variance), `vendor_id`. Lines keyed `receipt_number` + `line_number` + `po_no`: `unit_qty_invoiced`, `unit_cost_display`. **Send nothing else** — `company_id`, `branch_id`, `period`, `year_for_period` are marked required and are disabled columns. The voucher lands approved and unpaid. The runbooks build one line per `inventory_receipts_line` row (`qty_received`, `unit_cost`). [Manual](../03-Transaction-API.md#convertpotovoucher-service-vouching-a-receipt).

## Path B — drop ship

| # | Step | Surface | Read-back | Status |
|---|---|---|---|---|
| B1 | Sales order with a direct-ship line (`disposition` = `D`), saved | Interactive `Order` | `oe_line.disposition = 'D'`, `po_cost` | Run on play 26.1.5950.0, 2026-10-10 |
| B2 | Re-open the order, `c_create_po` = `ON`, save → PO wizard: `cb_next`, `cb_finish` | Interactive `Order` + wizard response window | `po_hdr` (`po_type = 'D'`), `oe_line_po` (`connection_type = 'P'`) | Run on play 26.1.5950.0, 2026-10-10 |
| B3 | Vendor ships; confirm the direct ship — receipt **and** customer invoice | Interactive `DirectShipConfirmation` | `inventory_receipts_hdr` (type `P`), `po_line` complete, `oe_line.qty_invoiced`, `invoice_hdr` | Run on play 26.1.5950.0, 2026-10-10 |
| B4 | Vouch the vendor invoice against that receipt | Transaction `ConvertPOToVoucher` (as A3) | as A3 | Run on play 26.1.5950.0, 2026-10-10 |

**B1 — The direct-ship line (Verified; run on play 26.1.5950.0, 2026-10-10).** `disposition` can be set **only while the line is being entered**, in the window — never on a saved line, never through the Transaction API. **Set `quote` = `OFF` first**: in quote mode `disposition` looks disabled and the wizard later builds an RFQ instead of a PO ([details](../04-Interactive-API.md#set-quote-to-off-first-the-window-can-open-in-quote-mode)). The header needs `contact_id`. Key the deal's buy price into the line's `po_cost`: it flows to the PO line's price, and without it the PO inherits the supplier's standard cost. The window clears after the save; find the order by its customer `po_no` and the newest `oe_hdr_uid`.

> **For a user with a Buyer ID, this first save can open the PO wizard by itself.** In the verification runs the API user's *Create PO from OE* setting was *Create All*, and saving the new order — without `c_create_po` — raised the wizard (`cb_finish` in its tools). The runbooks cancel it with `cb_cancel` before `cb_next`, so nothing is committed, and create the PO deliberately in B2. A user without a Buyer ID saw no wizard at this point.

**B2 — Two saves, then the wizard (Verified; run on play 26.1.5950.0, 2026-10-10).** Save the order, re-open it by `order_no`, set `c_create_po` = `ON`, save. The response window is the wizard only if its tools include `cb_finish`; check before pressing anything. Page 1 (`items`) shows the line, `qty_to_purchase`, the supplier and `quote_item = N`; after `cb_next`, page 2 (`po_print`) shows the new `po_no` and `po_type = D`.

- The API user needs a **Buyer ID** in User Maintenance, or the trigger refuses: `To create a PO, you must have a valid Buyer ID.` (seen again in the verification run with a password user that has none).
- `supplier_id` on the wizard is disabled to the API: it defaults to the item's primary supplier. When supplier choice matters, a person creates the PO.
- **The PO is committed at `cb_next`, before `cb_finish`.** An abandoned wizard is not a no-op — go and look for the PO.

**B3 — Confirm the direct ship (Verified; run on play 26.1.5950.0, 2026-10-10).** Interactive `DirectShipConfirmation`: set `TABPAGE_1.tp_1_dw_po.po_no`, `receive_all` = `ON`, save. `shipment_date`, `period` and `year_for_period` pre-fill. One save writes the receipt, completes the PO lines, invoices the sales-order lines and creates the customer's invoice — with no popups, and as either a password user or the consumer-key user. **Do not** try `PurchaseOrderReceipt` on a direct-ship PO; it refuses because the linked sales lines are locked. The confirmation also **overwrites `po_line.supplier_ship_date` on every line** — capture it first if you confirm partials ([details](../04-Interactive-API.md#directshipconfirmation-writes-its-ship-date-down-onto-every-line)).

> **Note — which surface.** The Interactive path above is the one the runbooks run. A Transaction API path (one `DirectShipConfirmation` POST keyed by `po_no`, `receive_all` on, `print_invoice` and `fax_invoice` off) returned an empty no-op result on 26.1.5940.0 but confirmed in full on play 26.1.5950.0, 2026-10-10 — see [The Transaction API path works on 26.1.5950.0](../04-Interactive-API.md#the-transaction-api-path-works-on-26159500). On either surface, **never send `c_email_invoice`**: it is disabled, and a transaction that tripped on it reported `Failed` **after** writing the receipt, the PO completion and the customer invoice.

**B4 — Vouch (run on play 26.1.5950.0, 2026-10-10).** A direct-ship vendor invoice vouches like any other, against the receipt B3 created: the same `ConvertPOToVoucher` payload as A3, with the PO's `vendor_id`. A direct-ship PO "with no receipt yet" means the sales side has not confirmed the shipment — it is not a receiving task.

## The wizard step, in code

B2 is the step with the most ways to go wrong, so here it is from the runbooks. `session` is the response-window-enabled Interactive session from the shared helpers ([`runbook_common.py`](../../examples/python/recipes/runbook_common.py) · [`RunbookSteps.cs`](../../examples/csharp/Recipes/RunbookSteps.cs)); the rest of each step is in the files.

<!-- tabs -->
```python
def create_po_from_order(rb: P21Runbook, order_no: str) -> str:
    """B2: re-open the saved order, c_create_po ON, save, and drive the PO wizard.

    The wizard is identified by its buttons (cb_finish present) before
    anything is pressed. The PO is committed at cb_next, before cb_finish.
    """
    print("\nB2 - Re-open, c_create_po = ON, save, PO wizard (Interactive Order)")
    session = rb.session()
    window_id = session.open_window("Order")
    wizard_po = None
    try:
        session.change(window_id, "TABPAGE_1", "order", "order_no", order_no)
        session.change(window_id, "TABPAGE_1", "order", "c_create_po", "ON")  # needs a Buyer ID
        result = session.save_raw(window_id)
        for _ in range(10):
            if not is_blocked(result):
                break
            for popup_id in popup_ids(result):
                tools = session.tools(popup_id)
                if "cb_finish" not in tools:          # some other prompt: proceed
                    pick = next(b for b in ("cb_ok", "cb_1", "cb_yes") if b in tools)
                    result = session.click(popup_id, pick)
                    continue
                for row in session.rows(popup_id, "items"):
                    print(f"    wizard page 1: {row.get('item_id')} qty {row.get('qty_to_purchase')} "
                          f"supplier {row.get('supplier_id')} quote_item={row.get('quote_item')}")
                session.click(popup_id, "cb_next")    # <-- the PO is committed HERE
                for row in session.rows(popup_id, "po_print"):
                    wizard_po = row.get("po_no")
                    print(f"    wizard page 2: po_no {wizard_po}, po_type {row.get('po_type')}")
                result = session.click(popup_id, "cb_finish")
    finally:
        session.cleanup(window_id)
    link = rb.one("oe_line_po", f"order_number eq '{order_no}'",
                  "order_number,line_number,po_no,po_line_number,connection_type")
    check("oe_line_po.connection_type", link["connection_type"], "P")
    po_no = str(link["po_no"])
    hdr = rb.one("po_hdr", f"po_no eq {po_no}", "po_no,po_type,approved,external_po_no")
    check("po_hdr.po_type", hdr["po_type"], "D")
    if wizard_po and str(wizard_po) != po_no:
        raise SystemExit(f"Wizard showed PO {wizard_po}, oe_line_po links {po_no}")
    return po_no
```

```csharp
/// <summary>
/// B2: re-open the saved order, c_create_po ON, save, drive the wizard.
/// The wizard is identified by its buttons (cb_finish) before anything is
/// pressed; the PO is committed at cb_next, before cb_finish.
/// </summary>
private static async Task<string> CreatePoFromOrderAsync(Runbook rb, string orderNo)
{
    var session = await rb.SessionAsync();
    var windowId = await session.OpenAsync("Order");
    string? wizardPo = null;
    try
    {
        await session.ChangeAsync(windowId, "TABPAGE_1", "order", "order_no", orderNo);
        await session.ChangeAsync(windowId, "TABPAGE_1", "order", "c_create_po", "ON"); // needs a Buyer ID
        var result = await session.SaveRawAsync(windowId);
        for (var i = 0; i < 10 && RunbookSession.IsBlocked(result); i++)
        {
            foreach (var popupId in RunbookSession.PopupIds(result))
            {
                var tools = await session.ToolsAsync(popupId);
                if (!tools.Contains("cb_finish"))       // some other prompt: proceed
                {
                    result = await session.ClickAsync(popupId,
                        new[] { "cb_ok", "cb_1", "cb_yes" }.First(tools.Contains));
                    continue;
                }
                foreach (var row in await session.RowsAsync(popupId, "items"))
                    Console.WriteLine($"    wizard page 1: {row["item_id"]} qty {row["qty_to_purchase"]} " +
                                      $"supplier {row["supplier_id"]} quote_item={row["quote_item"]}");
                await session.ClickAsync(popupId, "cb_next");   // <-- the PO is committed HERE
                foreach (var row in await session.RowsAsync(popupId, "po_print"))
                {
                    wizardPo = row["po_no"];
                    Console.WriteLine($"    wizard page 2: po_no {wizardPo}, po_type {row["po_type"]}");
                }
                result = await session.ClickAsync(popupId, "cb_finish");
            }
        }
    }
    finally
    {
        await session.CloseAsync(windowId);
    }

    var link = await rb.OneAsync("oe_line_po", $"order_number eq '{orderNo}'",
        "order_number,line_number,po_no,connection_type");
    Check("oe_line_po.connection_type", link["connection_type"], "P");
    var poNo = link["po_no"]!.ToString();
    var hdr = await rb.OneAsync("po_hdr", $"po_no eq {poNo}", "po_no,po_type");
    Check("po_hdr.po_type", hdr["po_type"], "D");
    if (wizardPo != null && wizardPo != poNo)
        throw new InvalidOperationException($"Wizard showed PO {wizardPo}, oe_line_po links {poNo}");
    return poNo;
}
```
<!-- /tabs -->

> **Payload files** (validator-verified, JSON only): [A1 PO](../../examples/payloads/json/purchase-order-create.json) · [A2 receipt](../../examples/payloads/json/purchase-order-receipt.json) · [A3/B4 voucher](../../examples/payloads/json/convert-po-to-voucher.json) — see [payloads README](../../examples/payloads/README.md). B1–B3 are Interactive window steps and have no single payload.

## ⚠️ "Failed" can mean "already committed"

Twice on this path a call reported failure after the work was done: the wizard commits the PO at `cb_next`, and a direct-ship confirmation that tripped on a disabled column had already written the receipt and the invoices. **Treat a failure as "go and read the tables", never as "nothing happened".** See [What `Failed` actually guarantees](../03-Transaction-API.md#what-failed-actually-guarantees).

## Not covered here

Changing or closing a stock PO after creation, receipts for lot- or serial-tracked items, partial receipts across several receipts, the Interactive bin-grid receipt for lines without a usable primary bin (described in A2, not in the runbooks), and vouchers without a PO (`VoucherByItem`, `ConvertVendorInvoiceToVoucher`) — none run here.

> **Credit:** [Alex Westemeier](https://github.com/AWestemeier) — both paths verified on play, August 2026, with the Interactive receipt, the wizard, the Transaction direct-ship confirmation and the voucher. Path A's Transaction receipt and voucher and the wizard were re-verified in this repo (August 2026); the Interactive direct-ship confirmation and the quote-mode correction: *@mrwuss*, play 26.1, October 2026 ([#169](https://github.com/mrwuss/p21-api-documentation/issues/169)). Runnable Python and C# runbooks for both paths: run end to end on play 26.1.5950.0, 2026-10-10.
