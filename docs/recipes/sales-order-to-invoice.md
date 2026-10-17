# Sales Order → Pick Ticket → Invoice

Take a sales order from entry to a customer invoice through the API: create the order, print its pick ticket, then confirm the shipment, which creates the invoice.

**API:** Transaction + Interactive · **Services:** `Order`, `Shipping` · **Deep dive:** [Create Order](../03-Transaction-API.md#create-order) · [Sales Order Entry with Assembly Lines](../04-Interactive-API.md#sales-order-entry-with-assembly-lines) · [Shipping and Invoicing](../12-Production-Labor-API.md#shipping-and-invoicing-the-linked-sales-order)

The three steps below are one runnable program, in Python and C#, that runs each step and reads it back before the next: [`examples/python/recipes/sales_order_to_invoice.py`](../../examples/python/recipes/sales_order_to_invoice.py) · [`examples/csharp/Recipes/SalesOrderToInvoice.cs`](../../examples/csharp/Recipes/SalesOrderToInvoice.cs) (menu item 34). Both are dry runs until you pass `--execute` or type `EXECUTE`. Step 1 on the Interactive surface (lines that raise a prompt) is [order-with-assembly](order-with-assembly.md); the report route for step 2 is [generate-pick-ticket-pdf](generate-pick-ticket-pdf.md).

**Status legend:** **Run on play 26.1.5950.0, 2026-10-10** = the step ran in both the Python and the C# runbook against a play tenant on that build and date, with a read-back. **Verified** = run end to end with a read-back by the credited contributor on play (many orders) and on production.

## Run it

```bash
python examples/python/recipes/sales_order_to_invoice.py            # dry run: payloads
python examples/python/recipes/sales_order_to_invoice.py --customer CUST-100 --ship-to CUST-100 \
    --contact 300 --location 10 --taker JSMITH --item ITEM-001 --qty 2 --price 12.00 \
    --po-no RUNBOOK-001 --execute
```

## Runbook

| # | Step | Surface | Read-back | Status |
|---|---|---|---|---|
| 1 | Create the order | Transaction `Order` (plain stock lines) or Interactive `Order` (anything with a prompt) | `oe_hdr`, `oe_line` | Run on play 26.1.5950.0, 2026-10-10 (Transaction) |
| 2 | Print the pick ticket | Transaction `Order` — `TP_FRONTCOUNTER.tp_frontcounter.print_tix` = `ON` | `oe_pick_ticket` | Run on play 26.1.5950.0, 2026-10-10 |
| 3 | Confirm the shipment (creates the invoice) | Interactive `Shipping` — retrieve `pick_ticket_no`, save | `invoice_hdr`, `invoice_line` | Run on play 26.1.5950.0, 2026-10-10 |

### Step 1 — Create the order (Verified; run on play 26.1.5950.0, 2026-10-10)

Header on `TABPAGE_1.order`: **`quote` = `OFF` first**, **`sales_loc_id` then `source_loc_id`**, `customer_id`, `ship_to_id`, `contact_id`, `order_date`, `requested_date` (after the order date), `po_no`, `taker`. Lines on `TP_ITEMS.items`: `oe_order_item_id`, `unit_quantity`, and `unit_price` only if you are overriding pricing.

> **`quote` = `OFF` matters on the Transaction API too.** The Interactive window [can open in quote mode](../04-Interactive-API.md#set-quote-to-off-first-the-window-can-open-in-quote-mode), and so can a Transaction create: for the verification API user, whose user record carries `default_quote_order = 'Y'`, an `Order` POST without `quote` saved a quote (`oe_hdr.projected_order = 'Y'`), and step 2 then failed with *"You cannot print, fax or email a pick ticket for a quotation."* The same POST with `quote` = `OFF` as its first header edit saved a real order. Read `projected_order` back after step 1 (play 26.1.5950.0, 2026-10-10).

Choose the surface by the prompts the order will raise — the Transaction API answers every prompt with its default, usually No:

- **"Add as assembly?"** on a production-order assembly item: **Yes** (`cb_1`) makes a production-order line and, if the assembly auto-creates, spawns and links a production order. **No** (`cb_2`) makes a plain stock line that can never become a production-order line later. Interactive only for Yes.
- **Date cascade** when the dates are set: answer `cb_ok`.
- **Salesrep not allowed at a location** (a site DynaChange rule): pick a sales/source location pair the customer's rep is valid at.
- **Profit-percentage rules** are prompts too. On the verification tenant a line priced far above cost failed the Transaction with *"The order line (…) profit percentage of 99.59% is greater than the acceptable limit of 85.00%. Continue? [Response: No]"* — the Transaction API answered No for you.

`source_loc_id` is the ship-from location. It decides `oe_line.supplier_id` (the item's primary supplier **there**), which in turn decides any supplier rebate at invoice — see [Rebate prerequisites](../03-Transaction-API.md#rebate-prerequisites-other-cost-below-actual-a-rebate-tracking-vendor).

**Contract pricing binds here, once.** If the customer, ship-to and item are on an approved contract in date, the line gets the contract price, `job_price_hdr_uid`, and a snapshot of the contract cost. That binding is permanent for the line — [details](../03-Transaction-API.md#binding-happens-once-at-line-entry).

Read back: `oe_hdr` (the new `order_no` — in the Transaction response rows; on the Interactive path, find the order by its newest `oe_hdr_uid`, because `order_no` is a string and does not sort numerically), `oe_line` (`assembly`, `disposition`, `qty_allocated`, `supplier_id`, `job_price_hdr_uid`, `other_cost`). An order on Hold has `packing_basis = 'Hold'`; release it before step 2.

### Step 2 — Print the pick ticket (Verified; run on play 26.1.5950.0, 2026-10-10)

Transaction `Order`, `TABPAGE_1.order` keyed on `order_no`, plus `TP_FRONTCOUNTER.tp_frontcounter` with `print_tix` = `ON`. It creates `oe_pick_ticket` and returns the PDF in `Results.Transactions[].Documents[].DocumentData`. It allocates nothing new: a backordered line is simply not on the ticket.

Read back the newest `pick_ticket_no` for the order from `oe_pick_ticket`. **Do not take it from the PDF's file name** — in the verification runs the returned `FileName` (`PT…`) carried a different number from the `pick_ticket_no` the ticket was saved under.

### Step 3 — Confirm the shipment and invoice (Verified; run on play 26.1.5950.0, 2026-10-10)

Interactive `Shipping`: set `pick_ticket_no` on `TABPAGE_1.tp_1_dw_1`; optionally set picked quantities on the items grid; leave `create_invoice` ("Confirm Shipment") at its default `ON`; save, and answer the proceed prompts with their Yes/OK button (`cb_1` / `cb_ok` / `cb_yes`). Never answer `cb_cancel`. Read the new `invoice_no` from `oe_pick_ticket`.

- **Partial shipments work** — the ticket ships what it carries; print another ticket later for the rest.
- **Usual blockers:** an item with no packaging code (the save refuses), and an order left in a `t~` status by a crashed session (re-open the order in the `Order` window, save it, then ship — [details](../06-Error-Handling.md#locks-and-orphaned-sessions)).
- For a direct-ship line the invoice comes from Direct Ship Confirmation instead — see [purchase-receive-vouch](purchase-receive-vouch.md#path-b-drop-ship).

**Shortcut for counter sales (Verified on play 26.1; not in the runbooks):** on the Interactive `Order` window, `fc_create_invoice` = `ON` with `quote` = `OFF` on a stocked line creates the pick ticket **and** the invoice in the order's own save.

## Steps 1 and 3, in code

From the shared runbook helpers ([`runbook_common.py`](../../examples/python/recipes/runbook_common.py) · [`RunbookSteps.cs`](../../examples/csharp/Recipes/RunbookSteps.cs)), which the disposal and rebate runbooks reuse:

<!-- tabs -->
```python
def build_order_payload(customer: str, ship_to: str, contact: str, sales_loc: str,
                        source_loc: str, order_date: str, requested_date: str,
                        po_no: str, taker: str,
                        lines: list[tuple[str, str, str | None]]) -> dict:
    """Transaction sales order: header plus every line in one POST.

    quote = OFF goes first: when the API user's default is "quote", a header
    without it saves a quote (oe_hdr.projected_order = 'Y'), and a quote
    refuses a pick ticket. A line price of None leaves unit_price unset so a
    contract price can bind.
    """
    header = [edit("quote", "OFF"), edit("customer_id", customer),
              edit("sales_loc_id", sales_loc), edit("source_loc_id", source_loc),
              edit("order_date", order_date), edit("requested_date", requested_date),
              edit("po_no", po_no), edit("taker", taker),
              edit("ship_to_id", ship_to), edit("contact_id", contact)]
    rows = []
    for item_id, qty, price in lines:
        row = [edit("oe_order_item_id", item_id), edit("unit_quantity", qty)]
        if price is not None:
            row.append(edit("unit_price", price))
        rows.append(row)
    return payload("Order", [element("TABPAGE_1.order", "Form", [], [header]),
                             element("TP_ITEMS.items", "List", [], rows)])


def ship_and_invoice(rb: P21Runbook, pick_ticket_no: str) -> str:
    """Confirm the shipment in the Interactive Shipping window; return the invoice_no.

    create_invoice ("Confirm Shipment") defaults ON, so the save ships AND
    invoices. Proceed prompts -- one per unpriced line on a $0 order -- are
    answered with cb_1 / cb_ok / cb_yes, never cb_cancel.
    """
    session = rb.session()
    window_id = session.open_window("Shipping")
    try:
        session.change(window_id, "TABPAGE_1", "tp_1_dw_1", "pick_ticket_no", pick_ticket_no)
        session.save(window_id)
    finally:
        session.cleanup(window_id)
    ticket = rb.one("oe_pick_ticket", f"pick_ticket_no eq {pick_ticket_no}",
                    "pick_ticket_no,ship_date,invoice_no")
    if not ticket.get("invoice_no"):
        raise SystemExit(f"Pick ticket {pick_ticket_no} has no invoice after the save")
    print(f"    shipped {ticket['ship_date']}, invoice_no = {ticket['invoice_no']}")
    return str(ticket["invoice_no"])
```

```csharp
/// <summary>
/// Transaction sales order, header plus every line in one POST. quote = OFF
/// goes first: when the API user's default is "quote", a header without it
/// saves a quote, and a quote refuses a pick ticket. A null price leaves
/// unit_price unset so a contract price can bind.
/// </summary>
public static JObject BuildOrderPayload(
    string customer, string shipTo, string contact, string salesLoc, string sourceLoc,
    string orderDate, string requestedDate, string poNo, string taker,
    IEnumerable<(string Item, string Qty, string? Price)> lines)
{
    var header = new[]
    {
        Edit("quote", "OFF"), Edit("customer_id", customer),
        Edit("sales_loc_id", salesLoc), Edit("source_loc_id", sourceLoc),
        Edit("order_date", orderDate), Edit("requested_date", requestedDate),
        Edit("po_no", poNo), Edit("taker", taker),
        Edit("ship_to_id", shipTo), Edit("contact_id", contact),
    };
    var rows = lines.Select(l =>
    {
        var row = new List<JObject> { Edit("oe_order_item_id", l.Item), Edit("unit_quantity", l.Qty) };
        if (l.Price != null) row.Add(Edit("unit_price", l.Price));
        return row.ToArray();
    }).ToArray();
    return Payload("Order", false,
        Element("TABPAGE_1.order", "Form", Array.Empty<string>(), header),
        Element("TP_ITEMS.items", "List", Array.Empty<string>(), rows));
}

/// <summary>
/// Confirm the shipment in the Interactive Shipping window; return the
/// invoice_no. create_invoice defaults ON, so the save ships AND invoices.
/// Proceed prompts (one per unpriced line on a $0 order) get cb_1 / cb_ok /
/// cb_yes — never cb_cancel.
/// </summary>
public static async Task<string> ShipAndInvoiceAsync(Runbook rb, string pickTicketNo)
{
    var session = await rb.SessionAsync();
    var windowId = await session.OpenAsync("Shipping");
    try
    {
        await session.ChangeAsync(windowId, "TABPAGE_1", "tp_1_dw_1", "pick_ticket_no", pickTicketNo);
        await session.SaveAsync(windowId);
    }
    finally
    {
        await session.CloseAsync(windowId);
    }
    var ticket = await rb.OneAsync("oe_pick_ticket", $"pick_ticket_no eq {pickTicketNo}",
        "pick_ticket_no,ship_date,invoice_no");
    if (string.IsNullOrEmpty(ticket["invoice_no"]?.ToString()))
        throw new InvalidOperationException($"Pick ticket {pickTicketNo} has no invoice after the save");
    Console.WriteLine($"    shipped {ticket["ship_date"]}, invoice_no = {ticket["invoice_no"]}");
    return ticket["invoice_no"]!.ToString();
}
```
<!-- /tabs -->

> **Payload files** (validator-verified, JSON only): [step 1 order](../../examples/payloads/json/create-sales-order.json) (add `quote` = `OFF` as the first header edit) · [step 2 print_tix](../../examples/payloads/json/order-print-pick-ticket.json) — see [payloads README](../../examples/payloads/README.md). Step 3 is an Interactive window step.

## Verify

The runbooks check the first two of these automatically:

- `invoice_hdr` by `order_no`; `invoice_line`: `unit_price`, `other_cost`, `commission_cost`, `cogs_amount`, `supplier_id`. `oe_line.qty_invoiced` = shipped.
- Inventory relieved at the source location (`inv_loc.qty_on_hand` down by the shipped quantity).
- **What the invoice cost should be:** for a line bound to a contract with an other cost, the contract value (re-read at invoicing); otherwise the item's moving average cost at the source location. Commission cost: a contract `Value` × its multiplier, or COGS × the multiplier for type `Order` — [table](../03-Transaction-API.md#order-entry-effect-of-each-commission-cost-setting).
- **If a rebate should have fired:** a `vendor_rebate` row for the invoice, and GL rows for the invoice showing the Sales Journal at full moving average cost plus a Rebate Journal entry for the difference — the [rebate-assembly-program](rebate-assembly-program.md) runbook checks the `vendor_rebate` row.

> **Credit:** [Alex Westemeier](https://github.com/AWestemeier) — runbook verified on play (dozens of orders) and production, September 2026. The counter-sale shortcut and the commission-cost results: *@mrwuss*, play 26.1, October 2026 ([#169](https://github.com/mrwuss/p21-api-documentation/issues/169)). Runnable Python and C# runbook, and the Transaction-side `quote` finding: run end to end on play 26.1.5950.0, 2026-10-10.
