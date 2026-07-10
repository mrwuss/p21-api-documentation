// Recipe: Adjust On-Hand Quantity (Write-Off)
// Docs:   docs/recipes/inventory-adjustment.md
//
// Post an inventory adjustment — a signed on-hand quantity change with no
// invoice — via the InventoryAdjustment service, then read it back by its
// server-generated adjustment_number.
//
// Key rules (all verified live — see the recipe page):
//   - reason_id takes the reason's DISPLAY TEXT (with UseCodeValues: false),
//     not its code.
//   - unit_quantity is the SIGNED DELTA, not the new on-hand: -5 removes
//     5 units; to zero an item out, post the negative of its on-hand.
//   - The save POSTS the adjustment immediately — there is no draft state.
//   - HTTP 200 is not success — check Summary.Succeeded / Failed.

using Newtonsoft.Json.Linq;
using P21Examples.Common;
using static P21Examples.Recipes.RecipeHelpers;

namespace P21Examples.Recipes;

public static class InventoryAdjustment
{
    public static async Task RunAsync()
    {
        Console.WriteLine("Recipe - Inventory Adjustment / Write-Off (InventoryAdjustment)");
        Console.WriteLine(new string('=', 60));

        using var client = await P21Client.CreateAsync();

        var payload = new JObject
        {
            ["Name"] = "InventoryAdjustment",
            ["UseCodeValues"] = false,  // reason_id is the display text, not the code
            ["Transactions"] = new JArray
            {
                new JObject
                {
                    ["Status"] = "New",
                    ["DataElements"] = new JArray
                    {
                        new JObject
                        {
                            ["Name"] = "TABPAGE_1.tp_1_dw_1",
                            ["Type"] = "Form",
                            ["Keys"] = new JArray(),
                            ["Rows"] = new JArray
                            {
                                new JObject
                                {
                                    ["Edits"] = new JArray
                                    {
                                        Edit("company_id", "ACME"),
                                        Edit("location_id", "10"),
                                        Edit("reason_id", "ADJUST"),  // display text
                                        Edit("inv_adj_description", "Cycle count write-off"),
                                    },
                                    ["RelativeDateEdits"] = new JArray()
                                }
                            }
                        },
                        new JObject
                        {
                            ["Name"] = "TABPAGE_17.tp_17_dw_17",
                            ["Type"] = "List",
                            ["Keys"] = new JArray(),
                            ["Rows"] = new JArray
                            {
                                new JObject
                                {
                                    ["Edits"] = new JArray
                                    {
                                        Edit("item_id", "WIDGET-001"),
                                        // signed delta, NOT new on-hand
                                        Edit("unit_quantity", "-5"),
                                    },
                                    ["RelativeDateEdits"] = new JArray()
                                }
                            }
                        }
                    }
                }
            }
        };

        PrintPayload("InventoryAdjustment payload (write off 5 units)", payload);
        Console.WriteLine("\nNOTE: the save POSTS the adjustment immediately — no draft state.");

        if (!ConfirmExecute())
            return;

        // ------------------------------------------------------------------
        // Write
        // ------------------------------------------------------------------
        var result = await client.Transaction.CreateAsync(payload);
        if (!CheckResult(result))
            return;

        // Pull the server-generated adjustment_number out of the echoed DataElements
        string? adjustmentNumber = null;
        foreach (var txn in result.Raw?["Results"]?["Transactions"] as JArray ?? new JArray())
        foreach (var de in txn["DataElements"] as JArray ?? new JArray())
        {
            if (de["Name"]?.ToString() != "TABPAGE_1.tp_1_dw_1") continue;
            foreach (var row in de["Rows"] as JArray ?? new JArray())
            foreach (var edit in row["Edits"] as JArray ?? new JArray())
                if (edit["Name"]?.ToString() == "adjustment_number" &&
                    !string.IsNullOrEmpty(edit["Value"]?.ToString()))
                    adjustmentNumber = edit["Value"]!.ToString();
        }
        Console.WriteLine($"\nAdjustment number: {adjustmentNumber}");
        if (string.IsNullOrEmpty(adjustmentNumber))
            return;

        // ------------------------------------------------------------------
        // Verify: read the adjustment back by its key
        // ------------------------------------------------------------------
        Console.WriteLine("\nVerify via /transaction/get:");
        Console.WriteLine(new string('-', 50));

        var getPayload = new JObject
        {
            ["ServiceName"] = "InventoryAdjustment",
            ["TransactionStates"] = new JArray
            {
                new JObject
                {
                    ["DataElementName"] = "TABPAGE_1.tp_1_dw_1",
                    ["Keys"] = new JArray
                    {
                        new JObject
                        {
                            ["Name"] = "adjustment_number",
                            ["Value"] = adjustmentNumber
                        }
                    }
                }
            }
        };
        var getResult = await client.Transaction.GetRecordsAsync(getPayload);

        var wanted = new[] { "adjustment_number", "location_id", "reason_id",
                             "item_id", "unit_quantity", "new_qoh" };
        foreach (var txn in getResult["Transactions"] as JArray ?? new JArray())
        foreach (var de in txn["DataElements"] as JArray ?? new JArray())
        foreach (var row in de["Rows"] as JArray ?? new JArray())
        foreach (var edit in row["Edits"] as JArray ?? new JArray())
            if (wanted.Contains(edit["Name"]?.ToString()))
                Console.WriteLine($"  {edit["Name"]}: {edit["Value"]}");
    }
}
