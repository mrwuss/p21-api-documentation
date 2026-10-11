// Recipe: Sales Order -> Pick Ticket -> Invoice Runbook
// Docs:   docs/recipes/sales-order-to-invoice.md
//
// Runs the page step by step, reading each step back before the next:
//
//   1. Create the order       Transaction Order (quote OFF, plain stock lines)
//   2. Print the pick ticket  Transaction Order, TP_FRONTCOUNTER.print_tix = ON
//   3. Confirm the shipment   Interactive Shipping — the save ships AND invoices
//   Verify                    invoice_hdr/invoice_line, oe_line.qty_invoiced,
//                             inv_loc.qty_on_hand relieved at the source location
//
// For lines that must answer a prompt (an assembly that explodes), enter the
// order with OrderWithAssembly instead and start this runbook at step 2.

using static P21Examples.Recipes.RunbookSteps;

namespace P21Examples.Recipes;

public static class SalesOrderToInvoice
{
    public static async Task RunAsync()
    {
        Console.WriteLine("Runbook - Sales Order -> Pick Ticket -> Invoice");
        Console.WriteLine(new string('=', 60));
        Console.WriteLine("Values (Enter keeps the placeholder):");
        var customer = Ask("Customer ID", "CUST-100");
        var shipTo = Ask("Ship-to ID", "CUST-100");
        var contact = Ask("Contact ID", "300");
        var location = Ask("Sales/source location", "10");
        var taker = Ask("Taker", "JSMITH");
        var item = Ask("Item (stocked, with a packaging code)", "ITEM-001");
        var qty = Ask("Quantity", "2");
        var price = Ask("Unit price (- = leave to pricing / a contract)", "12.00");
        var poNo = Ask("Customer PO number (tags the order)", "RUNBOOK-001");

        var orderPayload = BuildOrderPayload(customer, shipTo, contact, location, location,
            Today, DaysFromToday(1), poNo, taker, new[] { (item, qty, price == "-" ? null : (string?)price) });
        RecipeHelpers.PrintPayload("Step 1 Order payload", orderPayload);
        RecipeHelpers.PrintPayload("Step 2 print_tix payload (order_no from step 1)",
            BuildPrintTixPayload("{order_no}"));
        Console.WriteLine("\nStep 3 (Interactive Shipping): set TABPAGE_1.tp_1_dw_1.pick_ticket_no, save —" +
                          " answer proceed prompts cb_1/cb_ok/cb_yes, never cb_cancel.");

        if (!RecipeHelpers.ConfirmExecute())
            return;

        using var rb = await Runbook.CreateAsync();
        var itemUid = await rb.ItemUidAsync(item);
        var before = await OnHandAsync(rb, itemUid, location);

        Console.WriteLine("\nStep 1 - Create the order (Transaction Order)");
        var result = await rb.TransactionAsync(orderPayload, "Order");
        var orderNo = ResultValue(result, "TABPAGE_1.order", "order_no")!;
        var hdr = await rb.OneAsync("oe_hdr", $"order_no eq '{orderNo}'", "order_no,projected_order,packing_basis");
        Console.WriteLine($"    order_no = {orderNo}, packing_basis = {hdr["packing_basis"]}");
        Check("oe_hdr.projected_order (N = a real order, not a quote)", hdr["projected_order"], "N");
        foreach (var l in await rb.ODataAsync("oe_line", $"order_no eq '{orderNo}'",
                     "line_no,qty_ordered,qty_allocated,unit_price,supplier_id,job_price_hdr_uid,other_cost"))
        {
            Console.WriteLine($"    line {l["line_no"]}: qty {l["qty_ordered"]} allocated {l["qty_allocated"]} " +
                              $"price {l["unit_price"]} supplier {l["supplier_id"]} " +
                              $"contract {l["job_price_hdr_uid"]} other_cost {l["other_cost"]}");
            Check($"line {l["line_no"]} qty_allocated", Fmt(Num(l["qty_allocated"])), Fmt(Num(l["qty_ordered"])));
        }
        if (hdr["packing_basis"]?.ToString() == "Hold")
            throw new InvalidOperationException("The order is on Hold — release it before printing");

        Console.WriteLine("\nStep 2 - Print the pick ticket (Transaction Order, print_tix)");
        var pickTicketNo = await PrintPickTicketAsync(rb, orderNo);

        Console.WriteLine("\nStep 3 - Confirm the shipment and invoice (Interactive Shipping)");
        var invoiceNo = await ShipAndInvoiceAsync(rb, pickTicketNo);

        Console.WriteLine("\nVerify");
        await PrintInvoiceAsync(rb, invoiceNo);
        foreach (var l in await rb.ODataAsync("oe_line", $"order_no eq '{orderNo}'", "line_no,qty_ordered,qty_invoiced"))
            Check($"oe_line {l["line_no"]} qty_invoiced", Fmt(Num(l["qty_invoiced"])), Fmt(Num(l["qty_ordered"])));
        Check($"inv_loc.qty_on_hand at {location}", Fmt(await OnHandAsync(rb, itemUid, location)),
            Fmt(before - Num(qty)));
        Console.WriteLine("\nRunbook complete.");
    }

    private static async Task<decimal> OnHandAsync(Runbook rb, string itemUid, string location) =>
        Num((await rb.OneAsync("inv_loc", $"inv_mast_uid eq {itemUid} and location_id eq {location}",
            "qty_on_hand"))["qty_on_hand"]);
}
