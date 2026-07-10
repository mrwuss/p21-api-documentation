// Recipe: Create a Sales Order
// Docs:   docs/recipes/create-sales-order.md
//
// Create a sales order — header plus line items — in one stateless
// Transaction API call (service: Order).
//
// Key rules (all verified live — see the recipe page):
//   - source_loc_id is effectively required; omitting it fails with a
//     "Jurisdiction ID for Order Header Tax" error.
//   - requested_date must be AFTER order_date (same date trips a prompt).
//   - Do NOT send company_id — it is a disabled column on the Order window.
//   - No assembly lines here — the Transaction API auto-answers the
//     "add as assembly?" prompt No. Use the OrderWithAssembly recipe instead.
//   - HTTP 200 is not success; the generated order_no comes back in the
//     result rows of TABPAGE_1.order.

using Newtonsoft.Json.Linq;
using P21Examples.Common;
using static P21Examples.Recipes.RecipeHelpers;

namespace P21Examples.Recipes;

public static class CreateSalesOrder
{
    public static async Task RunAsync()
    {
        Console.WriteLine("Recipe - Create a Sales Order (Order)");
        Console.WriteLine(new string('=', 60));

        using var client = await P21Client.CreateAsync();

        var payload = BuildOrderPayload();
        PrintPayload("Order payload", payload);

        if (!ConfirmExecute())
            return;

        // ------------------------------------------------------------------
        // Write
        // ------------------------------------------------------------------
        var result = await client.Transaction.CreateAsync(payload);
        if (!CheckResult(result))
            return;

        // The generated order_no comes back in the result rows of TABPAGE_1.order
        var orderNo = (result.Raw?.SelectTokens(
                "$.Results.Transactions[?(@.Status == 'Passed')]" +
                ".DataElements[?(@.Name == 'TABPAGE_1.order')]" +
                ".Rows[*].Edits[?(@.Name == 'order_no')].Value")
            ?? Enumerable.Empty<JToken>()).FirstOrDefault()?.ToString();

        Console.WriteLine($"\nCreated order_no: {orderNo}");
        if (string.IsNullOrEmpty(orderNo))
            return;

        // ------------------------------------------------------------------
        // Verify: read the order back — Succeeded is not proof every value
        // landed (a DynaChange auto-answer can silently drop a line).
        // ------------------------------------------------------------------
        Console.WriteLine("\nVerify via OData:");
        Console.WriteLine(new string('-', 50));

        var hdrRows = (JArray)(await client.OData.QueryAsync(
            "oe_hdr", filter: $"order_no eq '{orderNo}'"))["value"]!;
        if (hdrRows.Count > 0)
        {
            var hdr = hdrRows[0];
            Console.WriteLine($"  Header: taker={hdr["taker"]} po_no={hdr["po_no"]} " +
                              $"order_date={hdr["order_date"]}");
        }
        else
        {
            Console.WriteLine("  Header NOT FOUND");
        }

        var lineRows = (JArray)(await client.OData.QueryAsync(
            "oe_line", filter: $"order_no eq '{orderNo}'"))["value"]!;
        Console.WriteLine($"  Lines: {lineRows.Count} (expected 2 — a dropped line means " +
                          "a DynaChange prompt was auto-answered)");
        foreach (var line in lineRows)
            Console.WriteLine($"    line {line["line_no"]}: " +
                              $"qty_ordered={line["qty_ordered"]}");
    }

    private static JObject BuildOrderPayload()
    {
        JObject Row(params (string Name, string Value)[] edits) => new JObject
        {
            ["Edits"] = new JArray(edits.Select(e => Edit(e.Name, e.Value))),
            ["RelativeDateEdits"] = new JArray(),
        };

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
                            ["Name"] = "TABPAGE_1.order",
                            ["Type"] = "Form",
                            ["Keys"] = new JArray(),
                            ["Rows"] = new JArray
                            {
                                Row(("customer_id", "100198"),
                                    ("sales_loc_id", "10"),
                                    ("source_loc_id", "10"),          // required in practice
                                    ("order_date", "2030-01-05"),
                                    ("requested_date", "2030-01-06"), // must be AFTER order_date
                                    ("po_no", "PO-TEST-001"),
                                    ("taker", "JSMITH"),
                                    ("ship_to_id", "200"),
                                    ("contact_id", "300")),
                            },
                        },
                        new JObject
                        {
                            ["Name"] = "TP_ITEMS.items",
                            ["Type"] = "List",
                            ["Keys"] = new JArray(),
                            ["Rows"] = new JArray
                            {
                                Row(("oe_order_item_id", "WIDGET-001"), ("unit_quantity", "5")),
                                Row(("oe_order_item_id", "WIDGET-002"), ("unit_quantity", "2")),
                            },
                        },
                    },
                },
            },
        };
    }
}
