// Recipe: Append Lines, Release a Hold, or Cancel a Saved Order (Order service)
// Docs:   docs/03-Transaction-API.md#order-service-line-appends-cancels-holds-and-item-lookup
//
// Each mode loads the order with the keyed header TABPAGE_1.order
// (Keys ["order_no"]) and sends one more element:
//   append        every new line as a row of ONE TP_ITEMS.items element (Keys []);
//                 one Transaction per line collides with the saved lines
//   release-hold  packing_basis on TP_SHIPINFO.shipinfo (enabled even where the
//                 header copy is a disabled column)
//   cancel        cancel_flag = ON on the header
//
// Pre-checks: the order exists, is not deleted/canceled, and is not held open
// (completed = 'T'). Append refuses an item already on the order -- that row
// would update the existing line instead of adding one. The read-back filters
// oe_line on delete_flag = 'N': a failed append leaves soft-deleted rows.

using Newtonsoft.Json.Linq;
using P21Examples.Common;
using static P21Examples.Recipes.RecipeHelpers;
using static P21Examples.Recipes.WritePathHelpers;

namespace P21Examples.Recipes;

public static class OrderAppendHoldCancel
{
    private const string HeaderColumns = "order_no,packing_basis,cancel_flag,completed,delete_flag";
    private const string LineColumns = "line_no,inv_mast_uid,qty_ordered,qty_allocated,cancel_flag,delete_flag";

    public static async Task RunAsync()
    {
        Console.WriteLine("Recipe - Order: Append / Release Hold / Cancel (Order service)");
        Console.WriteLine(new string('=', 60));

        var mode = Ask("Mode (append, release-hold, cancel)", "append").ToLowerInvariant();
        var orderNo = Ask("Order no", "1001234");

        var headerEdits = new List<JObject> { Edit("order_no", orderNo) };
        if (mode == "cancel")
            headerEdits.Add(Edit("cancel_flag", "ON"));
        var elements = new List<JObject>
        {
            Element("TABPAGE_1.order", "Form", new[] { "order_no" }, headerEdits.ToArray()),
        };

        var lineSpecs = Array.Empty<string>();
        if (mode == "append")
        {
            lineSpecs = Ask("Lines as ITEM:QTY[:PRICE], comma-separated", "ITEM-001:2,ITEM-002:3")
                .Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);
            var rows = new JArray();
            foreach (var spec in lineSpecs)
            {
                var parts = spec.Split(':');
                var edits = new JArray { Edit("oe_order_item_id", parts[0]), Edit("unit_quantity", parts[1]) };
                if (parts.Length > 2)
                    edits.Add(Edit("unit_price", parts[2]));
                rows.Add(new JObject { ["Edits"] = edits, ["RelativeDateEdits"] = new JArray() });
            }
            // Every new line is a row of ONE element in ONE Transaction.
            elements.Add(new JObject
            {
                ["Name"] = "TP_ITEMS.items", ["Type"] = "List", ["Keys"] = new JArray(), ["Rows"] = rows
            });
        }
        else if (mode == "release-hold")
        {
            var basis = Ask("Packing basis that replaces Hold", "Partial");
            elements.Add(Element("TP_SHIPINFO.shipinfo", "Form", Array.Empty<string>(),
                Edit("packing_basis", basis)));
        }
        else if (mode != "cancel")
        {
            Console.WriteLine($"Unknown mode: {mode}");
            return;
        }

        var payload = Payload("Order", elements.ToArray());
        PrintPayload("Payload", payload);
        if (!ConfirmExecute())
            return;

        using var client = await P21Client.CreateAsync();
        var (hdr, lines) = await ReadOrder(client, orderNo);
        if (hdr == null)
        {
            Console.WriteLine($"Order {orderNo} not found");
            return;
        }
        Show("Before:", hdr, lines);
        if ((string?)hdr["delete_flag"] == "Y" || (string?)hdr["cancel_flag"] == "Y")
        {
            Console.WriteLine("Order is deleted or canceled");
            return;
        }
        if ((string?)hdr["completed"] == "T")
        {
            Console.WriteLine("Order is held open (completed = 'T') -- every write would be refused");
            return;
        }

        if (mode == "append")
        {
            var onOrder = lines.Select(l => (long)l["inv_mast_uid"]!).ToHashSet();
            foreach (var spec in lineSpecs)
            {
                var itemId = spec.Split(':')[0];
                var found = await Rows(client, "inv_mast",
                    $"item_id eq {Q(itemId)} and delete_flag eq 'N'", "inv_mast_uid");
                if (found.Count == 0)
                {
                    Console.WriteLine($"Item {itemId} not found (exact ID, live items only)");
                    return;
                }
                if (onOrder.Contains((long)found[0]["inv_mast_uid"]!))
                {
                    Console.WriteLine($"{itemId} is already on the order -- the row would update that line, not add one");
                    return;
                }
            }
        }

        Console.WriteLine();
        CheckResult(await client.Transaction.CreateAsync(payload));
        var (hdrAfter, linesAfter) = await ReadOrder(client, orderNo);
        Show("After (OData read-back, live lines only):", hdrAfter, linesAfter);
    }

    private static async Task<(JObject? Header, List<JObject> Lines)> ReadOrder(P21Client client, string orderNo)
    {
        var hdr = await Rows(client, "oe_hdr", $"order_no eq {Q(orderNo)}", HeaderColumns);
        var lines = await Rows(client, "oe_line",
            $"order_no eq {Q(orderNo)} and delete_flag eq 'N'", LineColumns);
        return (hdr.Count > 0 ? (JObject)hdr[0] : null,
                lines.Cast<JObject>().OrderBy(l => (int)l["line_no"]!).ToList());
    }

    private static void Show(string label, JObject? hdr, List<JObject> lines)
    {
        Console.WriteLine($"\n{label}");
        Console.WriteLine($"  oe_hdr: {hdr?.ToString(Newtonsoft.Json.Formatting.None)}");
        foreach (var l in lines)
            Console.WriteLine($"  oe_line: {l.ToString(Newtonsoft.Json.Formatting.None)}");
    }
}
