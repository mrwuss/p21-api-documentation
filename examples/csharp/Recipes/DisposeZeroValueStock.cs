// Recipe: Dispose of Zero-Value Stock with a $0 Order (runbook)
// Docs:   docs/recipes/dispose-zero-value-stock.md
//
// Runs the page step by step, reading each step back before the next:
//
//   1. Build the item list from live inv_loc rows at the token cost   (OData)
//   2. Header + line 1, the rep the order must carry, on Hold         (Interactive Order)
//   3. Append the remaining lines in ONE Transaction per order        (Transaction Order)
//   4. Release the Hold (packing_basis = Partial)                      (Transaction Order)
//   5. Pick ticket, then ship-confirm -> the $0 invoice               (Transaction + Interactive)
//
// Write the cost down first (docs/recipes/inventory-cost-edit.md). Every $0
// line raises an "unpriced — ship anyway?" prompt at shipping; each is
// answered with its proceed button.

using Newtonsoft.Json.Linq;
using static P21Examples.Recipes.RunbookSteps;

namespace P21Examples.Recipes;

public static class DisposeZeroValueStock
{
    private const int LinesPerOrder = 100;  // per-line time grows with order size

    public static async Task RunAsync()
    {
        Console.WriteLine("Runbook - Dispose of Zero-Value Stock with a $0 Order");
        Console.WriteLine(new string('=', 60));
        Console.WriteLine("Values (Enter keeps the placeholder):");
        var location = Ask("Location", "10");
        var tokenCost = Ask("Token cost (moving_average_cost)", "0.02");
        var only = Ask("Only these item IDs, comma-separated (- = all)", "-");
        var customer = Ask("Disposal customer ID", "CUST-100");
        var shipTo = Ask("Ship-to ID", "CUST-100");
        var contact = Ask("Contact ID", "300");
        var salesrep = Ask("Salesrep the order must carry", "REP-HOUSE");
        var taker = Ask("Taker", "JSMITH");
        var poNo = Ask("PO number label", "DISPOSAL 2026-10");
        var filterItems = only == "-" ? new HashSet<string>() : only.Split(',').Select(s => s.Trim()).ToHashSet();

        Console.WriteLine($@"
Step 1 (OData): inv_loc where location_id eq {location} and moving_average_cost eq {tokenCost}
        and qty_on_hand gt 0; keep qty_allocated = 0.
Step 2 (Interactive Order, per order of up to {LinesPerOrder} lines): quote=OFF, header,
        TP_SALESREPS row 1 salesrep_id={salesrep}, packing_basis=Hold, line 1 at unit_price 0.");
        RecipeHelpers.PrintPayload("Step 3 append payload (order_no from step 2, lines 2..n)",
            BuildAppendPayload("{order_no}", new List<(string, string)> { ("ITEM-002", "4"), ("ITEM-003", "1") }));
        RecipeHelpers.PrintPayload("Step 4 release payload", BuildReleasePayload("{order_no}"));
        Console.WriteLine("\nStep 5: print_tix, then Interactive Shipping save (cb_1 per unpriced line).");

        if (!RecipeHelpers.ConfirmExecute())
            return;

        using var rb = await Runbook.CreateAsync();

        Console.WriteLine("\nStep 1 - Build the item list from live data (OData inv_loc)");
        var items = new List<(string Item, string Qty)>();
        foreach (var row in await rb.ODataAsync("inv_loc",
                     $"location_id eq {location} and moving_average_cost eq {tokenCost} and qty_on_hand gt 0",
                     "inv_mast_uid,qty_on_hand,qty_allocated"))
        {
            var itemId = (await rb.OneAsync("inv_mast", $"inv_mast_uid eq {row["inv_mast_uid"]}", "item_id"))
                ["item_id"]!.ToString();
            if (filterItems.Count > 0 && !filterItems.Contains(itemId)) continue;
            if (Num(row["qty_allocated"]) != 0)
            {
                Console.WriteLine($"    skip {itemId}: qty_allocated {row["qty_allocated"]}");
                continue;
            }
            items.Add((itemId, Fmt(Num(row["qty_on_hand"]))));
            Console.WriteLine($"    {itemId}: {Fmt(Num(row["qty_on_hand"]))} on hand at {tokenCost}");
        }
        if (items.Count == 0)
            throw new InvalidOperationException("Nothing on hand at the token cost — nothing to dispose");

        var chunks = items.Chunk(LinesPerOrder).ToList();
        for (var n = 0; n < chunks.Count; n++)
        {
            var orderPo = chunks.Count == 1 ? poNo : $"{poNo} - {n + 1:00}";
            await DisposeOrderAsync(rb, chunks[n].ToList(), orderPo,
                location, customer, shipTo, contact, salesrep, taker);
        }

        Console.WriteLine("\nVerify - inventory relieved at the location");
        foreach (var (itemId, _) in items)
        {
            var uid = await rb.ItemUidAsync(itemId);
            var row = await rb.OneAsync("inv_loc", $"inv_mast_uid eq {uid} and location_id eq {location}", "qty_on_hand");
            Check($"{itemId} qty_on_hand", Fmt(Num(row["qty_on_hand"])), "0");
        }
        Console.WriteLine("\nRunbook complete.");
    }

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

    /// <summary>Step 3: every remaining line as rows of ONE TP_ITEMS element (Keys []).
    /// One Transaction per line collides with the existing line.</summary>
    private static JObject BuildAppendPayload(string orderNo, List<(string Item, string Qty)> lines) =>
        Payload("Order", false,
            Element("TABPAGE_1.order", "Form", new[] { "order_no" }, new[] { Edit("order_no", orderNo) }),
            Element("TP_ITEMS.items", "List", Array.Empty<string>(),
                lines.Select(l => new[]
                {
                    Edit("oe_order_item_id", l.Item), Edit("unit_quantity", l.Qty), Edit("unit_price", "0"),
                }).ToArray()));

    /// <summary>Step 4: release the Hold through TP_SHIPINFO; allocation is untouched.</summary>
    private static JObject BuildReleasePayload(string orderNo) =>
        Payload("Order", false,
            Element("TABPAGE_1.order", "Form", new[] { "order_no" }, new[] { Edit("order_no", orderNo) }),
            Element("TP_SHIPINFO.shipinfo", "Form", Array.Empty<string>(), new[] { Edit("packing_basis", "Partial") }));
}
