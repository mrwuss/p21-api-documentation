// Modify an existing sales order: update a line in place + add a line.
// Mirrors docs/recipes/update-order-lines.md. See the runnable class at
// examples/csharp/Recipes/UpdateOrderLines.cs (menu option in the Recipes
// project; prints the payload and asks for EXECUTE before posting).

using System.Text;
using Newtonsoft.Json.Linq;
using P21Examples.Common;
using static P21Examples.Recipes.RecipeHelpers;

namespace P21Examples.Recipes;

public static class UpdateOrderLines
{
    private const string OrderNo = "1013938";

    // (handle, item, qty): existing handle -> update; new handle -> insert.
    private static readonly (string Handle, string ItemId, string Qty)[] Lines =
    {
        ("010", "WIDGET-001", "4"),
        ("030", "WIDGET-002", "1"),
    };

    public static async Task RunAsync()
    {
        Console.WriteLine("Recipe - Modify an Existing Sales Order");
        Console.WriteLine(new string('=', 60));

        using var client = await P21Client.CreateAsync();

        Console.WriteLine("\nBefore:");
        await PrintLinesAsync();

        var payload = BuildPayload();
        PrintPayload("Payload", payload);
        if (!ConfirmExecute())
            return;

        var result = await client.Transaction.CreateAsync(payload);
        if (!CheckResult(result))
            return;

        Console.WriteLine("\nAfter (read-back is the only proof):");
        await PrintLinesAsync();
    }

    private static JObject BuildPayload()
    {
        var itemRows = new JArray();
        foreach (var (handle, itemId, qty) in Lines)
        {
            itemRows.Add(new JObject
            {
                ["Edits"] = new JArray
                {
                    Edit("user_line_no", handle),
                    Edit("oe_order_item_id", itemId),
                    Edit("unit_quantity", qty),
                },
                ["RelativeDateEdits"] = new JArray(),
            });
        }

        return new JObject
        {
            ["Name"] = "Order",
            ["UseCodeValues"] = false,
            ["Transactions"] = new JArray
            {
                new JObject
                {
                    ["Status"] = "New",
                    ["DataElements"] = new JArray
                    {
                        new JObject
                        {
                            // ONLY the key -- re-sending header fields fails on
                            // disabled columns (customer_id) once the order exists.
                            ["Name"] = "TABPAGE_1.order", ["Type"] = "Form",
                            ["Keys"] = new JArray { "order_no" },
                            ["Rows"] = new JArray { new JObject {
                                ["Edits"] = new JArray { Edit("order_no", OrderNo) },
                                ["RelativeDateEdits"] = new JArray() } },
                        },
                        new JObject
                        {
                            ["Name"] = "TP_ITEMS.items", ["Type"] = "List",
                            ["Keys"] = new JArray { "user_line_no" },
                            ["Rows"] = itemRows,
                        },
                    },
                },
            },
        };
    }

    private static async Task PrintLinesAsync()
    {
        var (http, uiServer, _) = await CreateRawClientAsync();
        var request = new JObject
        {
            ["ServiceName"] = "Order",
            ["TransactionStates"] = new JArray { new JObject {
                ["DataElementName"] = "TABPAGE_1.order",
                ["Keys"] = new JArray { new JObject {
                    ["Name"] = "order_no", ["Value"] = OrderNo } } } },
        };
        var response = await http.PostAsync(
            $"{uiServer}/api/v2/transaction/get",
            new StringContent(request.ToString(), Encoding.UTF8, "application/json"));
        response.EnsureSuccessStatusCode();

        var body = JObject.Parse(await response.Content.ReadAsStringAsync());
        foreach (var element in body["Transactions"]![0]!["DataElements"]!)
        {
            if ((string?)element["Name"] != "TP_ITEMS.items")
                continue;
            foreach (var row in element["Rows"]!)
            {
                var edits = row["Edits"]!.ToDictionary(
                    e => (string)e["Name"]!, e => (string?)e["Value"]);
                if (string.IsNullOrEmpty(edits.GetValueOrDefault("oe_order_item_id")))
                    continue;
                Console.WriteLine(
                    $"  {edits.GetValueOrDefault("user_line_no")}: " +
                    $"{edits.GetValueOrDefault("oe_order_item_id")} x " +
                    $"{edits.GetValueOrDefault("unit_quantity")}");
            }
        }
    }
}
