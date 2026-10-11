// Recipe: Confirm a Direct Ship (DirectShipConfirmation window)
// Docs:   docs/04-Interactive-API.md#the-interactive-path-works
//
// Confirms a direct-ship PO in full: open DirectShipConfirmation, set the PO
// number, tick receive_all, save. One save receives the PO, completes the PO
// line and invoices the linked sales-order line; all three are read back.
//
// Key rules (verified on play 26.1.5950.0, October 2026):
//   - Fields are on TABPAGE_1.tp_1_dw_po (po_no, receive_all = ON/OFF).
//   - shipment_date, period and year_for_period come pre-filled. shipment_date
//     is written to po_line.supplier_ship_date on every line confirmed.
//   - No popups on the verified run; any popup stops the recipe.

using static P21Examples.Recipes.RecipeHelpers;

namespace P21Examples.Recipes;

public static class DirectShipConfirmation
{
    public sealed record Options(string PoNo = "500100");

    public static Task RunAsync() => RunAsync(new Options());

    public static async Task RunAsync(Options o)
    {
        Console.WriteLine("Recipe - Direct Ship Confirmation (Interactive API)");
        Console.WriteLine(new string('=', 60));
        Console.WriteLine($@"
Planned calls:
  POST v2/window {{""ServiceName"": ""DirectShipConfirmation""}}
  PUT  v2/change TABPAGE_1/tp_1_dw_po: po_no={o.PoNo}
  PUT  v2/change TABPAGE_1/tp_1_dw_po: receive_all=ON
  PUT  v2/data   save
  OData: po_line, oe_line, invoice_hdr read-back");
        if (!ConfirmExecute())
            return;

        var (http, uiServer, baseUrl) = await InteractiveHelpers.CreateRawClientAsync();
        using var _ = http;

        var po = await InteractiveHelpers.ODataAsync(http, baseUrl, "po_hdr", $"po_no eq {o.PoNo}");
        if (po.Count == 0 || (string)po[0]["po_type"]! != "D")
        {
            Console.WriteLine($"PO {o.PoNo} not found or not a direct-ship (po_type D) PO");
            return;
        }
        if (await ShowStateAsync(http, baseUrl, o.PoNo, "Before") == 0)
        {
            Console.WriteLine("No oe_line_po link -- nothing to confirm against");
            return;
        }

        await using (var s = new WindowSession(http, uiServer))
        {
            await s.StartAsync(responseWindows: true);
            var window = await s.OpenWindowAsync("DirectShipConfirmation");
            try
            {
                await s.ChangeAsync(window, "TABPAGE_1", "tp_1_dw_po", "po_no", o.PoNo);
                await s.ChangeAsync(window, "TABPAGE_1", "tp_1_dw_po", "receive_all", "ON");
                var pre = await s.ActiveRowAsync(window, "tp_1_dw_1");
                Console.WriteLine($"\nPre-filled: shipment_date={pre.GetValueOrDefault("shipment_date")} " +
                                  $"period={pre.GetValueOrDefault("period")} year_for_period={pre.GetValueOrDefault("year_for_period")}");
                var result = await s.SaveAsync(window);
                if ((int?)result["Status"] == WindowSession.Blocked)
                    throw new InvalidOperationException(
                        $"Save opened a popup: {string.Join(", ", await s.ToolsAsync(WindowSession.PopupIds(result)[0]))}");
                Console.WriteLine("Saved.");
            }
            finally
            {
                await s.CloseWindowAsync(window);
            }
        }

        await ShowStateAsync(http, baseUrl, o.PoNo, "After");
    }

    /// <summary>Print PO line, linked order line and invoice state; return the link count.</summary>
    private static async Task<int> ShowStateAsync(HttpClient http, string baseUrl, string poNo, string label)
    {
        Console.WriteLine($"\n{label}:");
        foreach (var line in await InteractiveHelpers.ODataAsync(http, baseUrl, "po_line", $"po_no eq {poNo}"))
            Console.WriteLine($"  po_line {line["line_no"]}: complete={line["complete"]} " +
                              $"qty_received={line["qty_received"]}/{line["qty_ordered"]} " +
                              $"supplier_ship_date={line["supplier_ship_date"]}");
        var links = await InteractiveHelpers.ODataAsync(http, baseUrl, "oe_line_po", $"po_no eq {poNo}");
        foreach (var link in links)
        {
            var orderNo = (string)link["order_number"]!;
            foreach (var ol in await InteractiveHelpers.ODataAsync(http, baseUrl, "oe_line",
                         $"order_no eq '{orderNo}' and line_no eq {link["line_number"]}"))
                Console.WriteLine($"  oe_line {orderNo}/{ol["line_no"]}: qty_invoiced={ol["qty_invoiced"]} complete={ol["complete"]}");
            foreach (var inv in await InteractiveHelpers.ODataAsync(http, baseUrl, "invoice_hdr", $"order_no eq '{orderNo}'"))
                Console.WriteLine($"  invoice_hdr {inv["invoice_no"]}: total_amount={inv["total_amount"]}");
        }
        return links.Count;
    }
}
