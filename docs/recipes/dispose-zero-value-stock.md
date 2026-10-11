# Dispose of Zero-Value Stock with a $0 Order

Ship unwanted stock out of a location on a sales order priced at $0, to an internal "disposal" customer, so the units leave inventory through the normal pick → ship → invoice path at their already-written-down cost.

**API:** Interactive + Transaction · **Services:** `Order`, `Shipping` · **Before this:** [inventory-cost-edit](inventory-cost-edit.md) · **Deep dive:** [Order Service — Line Appends, Cancels, Holds](../03-Transaction-API.md#order-service-line-appends-cancels-holds-and-item-lookup) · [Large Sales Orders](../09-Batch-Processing-Patterns.md#large-sales-orders-split-at-about-100-lines)

Steps 1–5 are one runnable program, in Python and C#, that runs each step and reads it back before the next: [`examples/python/recipes/dispose_zero_value_stock.py`](../../examples/python/recipes/dispose_zero_value_stock.py) · [`examples/csharp/Recipes/DisposeZeroValueStock.cs`](../../examples/csharp/Recipes/DisposeZeroValueStock.cs) (menu item 18). Both are dry runs until you pass `--execute` or type `EXECUTE`. They split the list into orders of 100 lines.

**Status legend:** **Run on play 26.1.5950.0, 2026-10-10** = the step ran in both the Python and the C# runbook against a play tenant on that build and date, with a read-back. **Verified** = run end to end with a read-back by the credited contributor (play and production, September 2026); **Inferred** = follows from verified behavior but was not run as its own step.

## Prerequisites

- **The cost is already written down** at the location ([inventory-cost-edit](inventory-cost-edit.md)), so the shipment relieves inventory at the token cost.
- **A disposal customer and ship-to exist** (here `CUST-DISPOSAL`), with a contact linked to the customer.
- **A sales rep that is allowed at the location.** Many sites carry a DynaChange rule that refuses a rep at a location it is not assigned to, and another that refuses two full-commission reps on one order. Know which rep the order must carry (here `REP-HOUSE`) and whether the customer's **default** rep passes your rules.
- Run against a test/play environment first.

## Run it

```bash
python examples/python/recipes/dispose_zero_value_stock.py            # dry run: plan + payloads
python examples/python/recipes/dispose_zero_value_stock.py --location 10 --token-cost 0.02 \
    --customer CUST-DISPOSAL --ship-to CUST-DISPOSAL --contact 300 --salesrep REP-HOUSE \
    --taker JSMITH --po-no "DISPOSAL 2026-10" --execute
```

`--items ITEM-001 ITEM-002` limits step 1 to named items; without it, every unallocated item on hand at the token cost goes on the orders.

## Runbook

### Step 1 — Build the item list from live data (Verified; run on play 26.1.5950.0, 2026-10-10)

Read `inv_loc` at the location for items whose `moving_average_cost` equals your token cost and `qty_on_hand > 0`, and check `qty_allocated = 0`. Write `item_id, qty` from that — **never** from the count spreadsheet. Between a count and the disposal run, items move, quantities get keyed wrong, and [merged items](../06-Error-Handling.md#transaction-api-errors) fail with *"'X' has been deleted"*.

The token cost is what `inv_loc.moving_average_cost` actually holds, not the number you typed: on the verification tenant, stock received on a PO at `0.02` carried a moving average of `0.0204`. Read one row before choosing the filter value.

### Step 2 — Create the header and line 1 (Interactive) (Verified; run on play 26.1.5950.0, 2026-10-10)

Use the Interactive `Order` window when the customer's default rep would trip a rep rule — the Transaction API cannot replace the default rep on a new order (any rep row you send is [added on top of it](../03-Transaction-API.md#order-service-line-appends-cancels-holds-and-item-lookup), and two full-commission rows fail).

1. `TABPAGE_1.order`: **`quote` = `OFF` first** ([why](../04-Interactive-API.md#set-quote-to-off-first-the-window-can-open-in-quote-mode)), `sales_loc_id`, `source_loc_id`, `customer_id`, `ship_to_id`, `contact_id`, `order_date`, `requested_date` (answer the date-cascade prompt with `cb_ok`), `po_no` (a recognizable label such as the month and year), `taker` (the real person — it defaults to the API user).
2. `TP_SALESREPS`: select row 1, set `salesrep_id` to the rep the order must carry. No popup.
3. Put the order on Hold (`packing_basis` = `Hold`) so it does not pick before you finish. On some tenants the header copy is disabled; use `TP_SHIPINFO.shipinfo` instead. (The header copy took the edit on the verification tenant.)
4. `TP_ITEMS.items`: the first line on the existing row — `oe_order_item_id`, `unit_quantity`, `unit_price` = `0`. Answer *"add as assembly?"* with **No** (`cb_2`) so kits go in as plain lines.
5. Save. The window clears; find the order by its `po_no` and newest `oe_hdr_uid`. Read back `oe_hdr` and `oe_hdr_salesrep` — exactly one rep row, the one you set.

If the customer's default rep already passes your rules, skip the Interactive step and create the whole order with the Transaction API in one POST (Inferred — the faster form, not run).

### Step 3 — Append the remaining lines (Transaction) (Verified; run on play 26.1.5950.0, 2026-10-10)

One Transaction per order: header `TABPAGE_1.order` keyed on `order_no`, and **all** remaining lines as rows of one `TP_ITEMS.items` element (`Keys: []`), each with `oe_order_item_id`, `unit_quantity`, `unit_price` = `0`.

- **Never one Transaction per line** — rows collide with the existing line (*"Item ID X has been saved; therefore, the Item ID cannot be edited"*).
- **Hundreds of lines → split into orders of about 100.** Per-line time grows with the order's size; ten 100-line orders ran at a flat speed where one thousand-line order took twice as long ([numbers](../09-Batch-Processing-Patterns.md#large-sales-orders-split-at-about-100-lines)). Suffix each order's `po_no` (`- 01`, `- 02`, …).
- **A line that cannot allocate fails the whole Transaction** — *"The order line does not have a PO Cost specified. Proceed?"* is auto-answered No. The failed rows stay behind soft-deleted ([details](../03-Transaction-API.md#a-failed-create-leaves-rows-behind)); re-read live rows before any retry. On a test tenant, leftover test orders holding the same stock cause this — cancel them first.
- **If the order is locked by your own API user, wait** — a killed client's Transaction is still running ([details](../06-Error-Handling.md#locks-and-orphaned-sessions)).

### Step 4 — Release the Hold (Transaction) (Verified; run on play 26.1.5950.0, 2026-10-10)

`TABPAGE_1.order` keyed on `order_no`, then `TP_SHIPINFO.shipinfo` (`Keys: []`) with `packing_basis` = `Partial`. Allocation is untouched. From here a scheduled pick run, or the warehouse, can take over.

### Step 5 — Pick ticket, ship, and $0 invoice (Verified on play; run on play 26.1.5950.0, 2026-10-10)

1. Pick ticket: Transaction `Order`, `TABPAGE_1.order` keyed on `order_no`, `TP_FRONTCOUNTER.tp_frontcounter` with `print_tix` = `ON`. Read the new ticket from `oe_pick_ticket`.
2. Ship: Interactive `Shipping` — set `pick_ticket_no` on `TABPAGE_1.tp_1_dw_1`, leave `create_invoice` at its default ON, save. **Every $0 line raises an "item is unpriced — ship anyway?" prompt**; answer each with `cb_1`. On the API side they cost a few hundredths of a second each with no slowdown (the growing delay users see is the desktop client). Never answer with `cb_cancel`.
3. A save `Status` of 1 or 2 are both normal here — judge by the invoice row, not the status.

## Steps 2–5, in code

One order's worth, from the runbooks. `enter_order` / `EnterOrderAsync`, `print_pick_ticket` and `ship_and_invoice` are the shared helpers in [`runbook_common.py`](../../examples/python/recipes/runbook_common.py) · [`RunbookSteps.cs`](../../examples/csharp/Recipes/RunbookSteps.cs).

<!-- tabs -->
```python
def dispose_order(rb: P21Runbook, args: argparse.Namespace, po_no: str,
                  lines: list[tuple[str, str]]) -> None:
    """Steps 2-5 for one order of up to LINES_PER_ORDER lines."""
    print(f"\nStep 2 - Header + line 1 on Hold, rep {args.salesrep} (Interactive Order)")
    header = {"sales_loc_id": args.location, "source_loc_id": args.location,
              "customer_id": args.customer, "ship_to_id": args.ship_to,
              "contact_id": args.contact, "order_date": TODAY.isoformat(),
              "requested_date": (TODAY + timedelta(days=2)).isoformat(),
              "po_no": po_no, "taker": args.taker}
    first_item, first_qty = lines[0]
    order_no = enter_order(rb, header, [[("oe_order_item_id", first_item),
                                         ("unit_quantity", first_qty), ("unit_price", "0")]],
                           salesrep=args.salesrep, hold=True)
    reps = rb.odata("oe_hdr_salesrep", f"order_number eq '{order_no}' and delete_flag eq 'N'",
                    "salesrep_id,primary_salesrep")
    check("oe_hdr_salesrep rows", len(reps), 1)
    check("oe_hdr_salesrep.salesrep_id", reps[0]["salesrep_id"], args.salesrep)

    if len(lines) > 1:
        print(f"\nStep 3 - Append {len(lines) - 1} line(s) in one Transaction (Transaction Order)")
        rb.transaction(build_append_payload(order_no, lines[1:]), "Append lines")

    live = rb.odata("oe_line", f"order_no eq '{order_no}' and delete_flag eq 'N' and cancel_flag eq 'N'",
                    "line_no,qty_ordered,qty_allocated,unit_price")
    check("live oe_line rows", len(live), len(lines))
    check("SUM(qty_allocated) = SUM(qty_ordered)", sum(float(r["qty_allocated"]) for r in live),
          sum(float(r["qty_ordered"]) for r in live))
    check("MAX(unit_price)", max(float(r["unit_price"]) for r in live), 0.0)

    print("\nStep 4 - Release the Hold (Transaction Order, TP_SHIPINFO)")
    rb.transaction(build_release_payload(order_no), "Release hold")
    hdr = rb.one("oe_hdr", f"order_no eq '{order_no}'", "packing_basis")
    check("oe_hdr.packing_basis", hdr["packing_basis"], "Partial")

    print("\nStep 5 - Pick ticket, ship, $0 invoice")
    pick_ticket_no = print_pick_ticket(rb, order_no)
    invoice_no = ship_and_invoice(rb, pick_ticket_no)  # one cb_1 per unpriced line
    inv_lines = print_invoice(rb, invoice_no)
    check("invoice total of unit prices", sum(float(x["unit_price"]) for x in inv_lines), 0.0)
    for line in rb.odata("oe_line", f"order_no eq '{order_no}'", "line_no,qty_ordered,qty_invoiced"):
        check(f"oe_line {line['line_no']} qty_invoiced", float(line["qty_invoiced"]),
              float(line["qty_ordered"]))
```

```csharp
/// <summary>Steps 2-5 for one order of up to LinesPerOrder lines.</summary>
private static async Task DisposeOrderAsync(
    Runbook rb, List<(string Item, string Qty)> lines, string poNo, string location,
    string customer, string shipTo, string contact, string salesrep, string taker)
{
    Console.WriteLine($"\nStep 2 - Header + line 1 on Hold, rep {salesrep} (Interactive Order)");
    var orderNo = await EnterOrderAsync(rb,
        new[]
        {
            ("sales_loc_id", location), ("source_loc_id", location),
            ("customer_id", customer), ("ship_to_id", shipTo), ("contact_id", contact),
            ("order_date", Today), ("requested_date", DaysFromToday(2)),
            ("po_no", poNo), ("taker", taker),
        },
        new[] { new[] { ("oe_order_item_id", lines[0].Item), ("unit_quantity", lines[0].Qty), ("unit_price", "0") } },
        salesrep: salesrep, hold: true);
    var reps = await rb.ODataAsync("oe_hdr_salesrep", $"order_number eq '{orderNo}' and delete_flag eq 'N'",
        "salesrep_id,primary_salesrep");
    Check("oe_hdr_salesrep rows", reps.Count, 1);
    Check("oe_hdr_salesrep.salesrep_id", reps[0]["salesrep_id"], salesrep);

    if (lines.Count > 1)
    {
        Console.WriteLine($"\nStep 3 - Append {lines.Count - 1} line(s) in one Transaction (Transaction Order)");
        await rb.TransactionAsync(BuildAppendPayload(orderNo, lines.Skip(1).ToList()), "Append lines");
    }
    var live = await rb.ODataAsync("oe_line",
        $"order_no eq '{orderNo}' and delete_flag eq 'N' and cancel_flag eq 'N'",
        "line_no,qty_ordered,qty_allocated,unit_price");
    Check("live oe_line rows", live.Count, lines.Count);
    Check("SUM(qty_allocated) = SUM(qty_ordered)", Fmt(live.Sum(r => Num(r["qty_allocated"]))),
        Fmt(live.Sum(r => Num(r["qty_ordered"]))));
    Check("MAX(unit_price)", Fmt(live.Max(r => Num(r["unit_price"]))), "0");

    Console.WriteLine("\nStep 4 - Release the Hold (Transaction Order, TP_SHIPINFO)");
    await rb.TransactionAsync(BuildReleasePayload(orderNo), "Release hold");
    var hdr = await rb.OneAsync("oe_hdr", $"order_no eq '{orderNo}'", "packing_basis");
    Check("oe_hdr.packing_basis", hdr["packing_basis"], "Partial");

    Console.WriteLine("\nStep 5 - Pick ticket, ship, $0 invoice");
    var pickTicketNo = await PrintPickTicketAsync(rb, orderNo);
    var invoiceNo = await ShipAndInvoiceAsync(rb, pickTicketNo);  // one cb_1 per unpriced line
    var invLines = await PrintInvoiceAsync(rb, invoiceNo);
    Check("invoice total of unit prices", Fmt(invLines.Sum(x => Num(x["unit_price"]))), "0");
    foreach (var l in await rb.ODataAsync("oe_line", $"order_no eq '{orderNo}'", "line_no,qty_ordered,qty_invoiced"))
        Check($"oe_line {l["line_no"]} qty_invoiced", Fmt(Num(l["qty_invoiced"])), Fmt(Num(l["qty_ordered"])));
}
```
<!-- /tabs -->

> **Payload files** (validator-verified, JSON only): [step 3 append](../../examples/payloads/json/order-append-zero-price-lines.json) · [step 4 release](../../examples/payloads/json/order-release-hold.json) · [step 5 print_tix](../../examples/payloads/json/order-print-pick-ticket.json) — see [payloads README](../../examples/payloads/README.md).

## Verify

The runbooks check every row of this table after the step it belongs to.

| After | Check |
|---|---|
| Steps 2–3 | `oe_hdr`: `taker`, `packing_basis`, `completed = 'N'`, `cancel_flag = 'N'`; `oe_hdr_salesrep`: one row, the intended rep, primary. `oe_line` **filtered on `delete_flag = 'N' AND cancel_flag = 'N'`**: every item once across all orders, `qty_ordered` = the list, `SUM(qty_allocated) = SUM(qty_ordered)`, `MAX(unit_price) = 0`, ship and source location = the location |
| Step 4 | `oe_hdr.packing_basis = 'Partial'`; allocation unchanged |
| Step 5 | `invoice_hdr` total $0; `invoice_line.cogs_amount` = units × the token cost; `oe_line.qty_invoiced` = ordered; `inv_loc.qty_on_hand` relieved |

**To back out** a test order: Transaction `Order`, header keyed on `order_no`, `cancel_flag` = `ON` — releases allocation; P21 reloads the order first, so a large one takes minutes. (Not run here.)

> **Credit:** [Alex Westemeier](https://github.com/AWestemeier) — run on production (several orders, about a thousand lines) and end to end on play including the API ship-confirm, September 2026. Runnable Python and C# runbook: run end to end on play 26.1.5950.0, 2026-10-10 (two-line orders; the 100-line split was not exercised at size).
