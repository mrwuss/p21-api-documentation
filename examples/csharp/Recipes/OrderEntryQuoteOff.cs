// Recipe: Enter a Sales Order with quote = OFF, Optionally as a Direct Ship
// Docs:   docs/04-Interactive-API.md#set-quote-to-off-first-the-window-can-open-in-quote-mode
//
// The Order window can open with quote = ON; everything saved that way is a
// quote (oe_hdr.projected_order = 'Y'). This reads the quote default, sets
// quote = OFF as the first header edit, enters one line, saves and reads
// projected_order back. With DirectShip the line is entered with
// disposition D and a po_cost, c_create_po = ON goes on the header, and the
// save opens the "Create RFQ/Purchase Orders" wizard: cb_next (the PO is
// committed here), then cb_finish. The po_type 'D' PO and its oe_line_po
// link are read back.
//
// Key rules (verified on play 26.1.5950.0, October 2026):
//   - Read quote before writing anything; set it OFF first.
//   - c_create_po needs a user with a Buyer ID. UseConsumerKey signs in as
//     P21_CONSUMER_KEY / P21_CONSUMER_USERNAME instead of the password user.
//   - The wizard did not open for a line whose supplier was an internal
//     (intercompany) supplier; with an outside supplier it did.
//   - w_message prompts on save are answered Yes (cb_1). Any other popup
//     stops the recipe.
//   - The new oe_line_uid arrives on the item change's keygenerated event.

using Newtonsoft.Json.Linq;
using static P21Examples.Recipes.RecipeHelpers;

namespace P21Examples.Recipes;

public static class OrderEntryQuoteOff
{
    public sealed record Options(
        string LocationId = "10",
        string CustomerId = "100",
        string ShipToId = "100",
        string ContactId = "300",
        string PoNo = "PO-TEST-001",
        string ItemId = "ITEM-001",
        string Quantity = "1",
        bool DirectShip = false,
        string PoCost = "8",
        bool UseConsumerKey = false);

    public static Task RunAsync() => RunAsync(new Options());

    public static async Task RunAsync(Options o)
    {
        Console.WriteLine("Recipe - Order entry with quote = OFF (Interactive API)");
        Console.WriteLine(new string('=', 60));
        Console.WriteLine($@"
Planned calls:
  POST v2/window {{""ServiceName"": ""Order""}}; read TABPAGE_1.order.quote
  PUT  v2/change TABPAGE_1/order: quote=OFF (first), sales_loc_id/source_loc_id={o.LocationId},
                 customer_id={o.CustomerId}, ship_to_id={o.ShipToId}, contact_id={o.ContactId}, po_no={o.PoNo}
  PUT  v2/change TP_ITEMS/items: oe_order_item_id={o.ItemId}, unit_quantity={o.Quantity}" +
            (o.DirectShip ? $", disposition=D, po_cost={o.PoCost}\n  PUT  v2/change TABPAGE_1/order: c_create_po=ON" : "") + @"
  PUT  v2/data   save; w_message -> cb_1" + (o.DirectShip ? "; wizard -> cb_next, cb_finish" : ""));
        if (!ConfirmExecute())
            return;

        var (http, uiServer, baseUrl) = await InteractiveHelpers.CreateRawClientAsync(o.UseConsumerKey);
        using var _ = http;

        string? oeLineUid;
        await using (var s = new WindowSession(http, uiServer))
        {
            await s.StartAsync(responseWindows: true);
            var window = await s.OpenWindowAsync("Order");
            try
            {
                Console.WriteLine($"\nquote default on open: {(await s.ActiveRowAsync(window, "order"))["quote"]}");
                await s.ChangeAsync(window, "TABPAGE_1", "order", "quote", "OFF");   // first header edit
                Console.WriteLine($"quote after OFF:       {(await s.ActiveRowAsync(window, "order"))["quote"]}");
                foreach (var (field, value) in new[] {
                    ("sales_loc_id", o.LocationId), ("source_loc_id", o.LocationId),
                    ("customer_id", o.CustomerId), ("ship_to_id", o.ShipToId),
                    ("contact_id", o.ContactId), ("po_no", o.PoNo) })
                    await s.ChangeAsync(window, "TABPAGE_1", "order", field, value);

                await s.SelectTabAsync(window, "TP_ITEMS");
                var item = await s.ChangeAsync(window, "TP_ITEMS", "items", "oe_order_item_id", o.ItemId);
                oeLineUid = WindowSession.EventValue(item, "keygenerated", "value");
                await s.ChangeAsync(window, "TP_ITEMS", "items", "unit_quantity", o.Quantity);
                if (o.DirectShip)
                {
                    await s.ChangeAsync(window, "TP_ITEMS", "items", "disposition", "D");   // only at line entry
                    await s.ChangeAsync(window, "TP_ITEMS", "items", "po_cost", o.PoCost);
                    await s.SelectTabAsync(window, "TABPAGE_1");
                    await s.ChangeAsync(window, "TABPAGE_1", "order", "c_create_po", "ON");
                }

                await AnswerPopupsAsync(s, await s.SaveAsync(window));
            }
            finally
            {
                await s.CloseWindowAsync(window);
            }
        }

        if (oeLineUid is null)
        {
            Console.WriteLine("No oe_line_uid came back from the item change");
            return;
        }
        var line = (await InteractiveHelpers.ODataAsync(http, baseUrl, "oe_line", $"oe_line_uid eq {oeLineUid}"))[0];
        var orderNo = (string)line["order_no"]!;
        var hdr = (await InteractiveHelpers.ODataAsync(http, baseUrl, "oe_hdr", $"order_no eq '{orderNo}'"))[0];
        Console.WriteLine($"\nVerify: order {orderNo} projected_order={hdr["projected_order"]} -> " +
                          ((string)hdr["projected_order"]! == "N" ? "OK (order)" : "QUOTE"));
        Console.WriteLine($"  line {line["line_no"]}: disposition='{line["disposition"]}' qty_ordered={line["qty_ordered"]}");
        if (!o.DirectShip) return;

        var links = await InteractiveHelpers.ODataAsync(http, baseUrl, "oe_line_po", $"order_number eq '{orderNo}'");
        foreach (var link in links)
        {
            var po = (await InteractiveHelpers.ODataAsync(http, baseUrl, "po_hdr", $"po_no eq {link["po_no"]}"))[0];
            Console.WriteLine($"  oe_line_po: po_no={link["po_no"]} connection_type={link["connection_type"]} " +
                              $"po_type={po["po_type"]} -> {((string)po["po_type"]! == "D" ? "OK" : "CHECK")}");
        }
        if (links.Count == 0)
            Console.WriteLine("  no oe_line_po row -> no PO was created (check Buyer ID and supplier)");
    }

    /// <summary>Answer w_message prompts Yes, drive the PO wizard, refuse anything else.</summary>
    private static async Task AnswerPopupsAsync(WindowSession s, JObject result)
    {
        while ((int?)result["Status"] == WindowSession.Blocked)
        {
            var popup = WindowSession.PopupIds(result)[0];
            var tools = await s.ToolsAsync(popup);   // includes the parent's ribbon -- search by name
            if (tools.Contains("cb_finish"))         // the Create RFQ/Purchase Orders wizard
            {
                foreach (var row in await s.RowsAsync(popup, "items"))
                    Console.WriteLine($"  wizard line: item={row["item_id"]} disposition={row["disposition"]} " +
                                      $"supplier={row["supplier_id"]} quote_item={row["quote_item"]} qty={row["qty_to_purchase"]}");
                await s.RunToolAsync(popup, "cb_next");   // the PO is COMMITTED here
                var page2 = await s.ActiveRowAsync(popup, "po_print");
                Console.WriteLine($"  wizard page 2: po_no={page2.GetValueOrDefault("po_no")} po_type={page2.GetValueOrDefault("po_type")}");
                result = await s.RunToolAsync(popup, "cb_finish");
            }
            else if (await s.WindowNameAsync(popup) == "w_message" && tools.Contains("cb_1"))
            {
                Console.WriteLine("  w_message -> cb_1 (Yes)");
                result = await s.RunToolAsync(popup, "cb_1");
            }
            else
            {
                throw new InvalidOperationException($"Unexpected popup: {string.Join(", ", tools)}");
            }
        }
    }
}
