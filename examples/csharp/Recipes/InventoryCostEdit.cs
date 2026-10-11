// Recipe: Edit Inventory Cost
// Docs:   docs/recipes/inventory-cost-edit.md
//
// Set an item's moving average cost at one location through the
// InventoryCostEdit service, then read the cost back over OData. The save
// posts to the GL immediately (journal IC, the value difference against the
// offset account you supply), so run it on a test tenant first.
//
// Key rules (verified live — see the recipe page):
//   - Three DataElements: QUERY.query (List) and FORM.form keyed by
//     location_id + item_id; FORM.account keyed by account_no.
//   - account_no in its stored form, WITHOUT the dash.
//   - year_for_period BEFORE period, both FISCAL.
//   - No inv_tran / inv_adj row is written — only inv_loc, audit_trail and the GL.

using System.Globalization;
using Newtonsoft.Json.Linq;
using P21Examples.Common;
using static P21Examples.Recipes.RecipeHelpers;

namespace P21Examples.Recipes;

public static class InventoryCostEdit
{
    // Generic placeholders — press Enter at each prompt to keep them.
    private const string ItemId = "ITEM-001";
    private const string LocationId = "10";
    private const string NewCost = "0.02";          // the new moving average cost per unit
    private const string AccountNo = "1111100";     // offset GL account, stored form: NO dash
    private const string YearForPeriod = "2026";    // FISCAL year
    private const string Period = "12";             // FISCAL period

    public static async Task RunAsync()
    {
        Console.WriteLine("Recipe - Edit Inventory Cost (InventoryCostEdit)");
        Console.WriteLine(new string('=', 60));

        var itemId = Ask("Item ID", ItemId);
        var locationId = Ask("Location ID", LocationId);
        var newCost = Ask("New moving average cost", NewCost);
        var accountNo = Ask("Offset GL account (no dash)", AccountNo);
        var year = Ask("Fiscal year_for_period", YearForPeriod);
        var period = Ask("Fiscal period", Period);

        var payload = new JObject
        {
            ["Name"] = "InventoryCostEdit",
            ["UseCodeValues"] = false,
            ["Transactions"] = new JArray
            {
                new JObject
                {
                    ["Status"] = "New",
                    ["DataElements"] = new JArray
                    {
                        Element("QUERY.query", "List", new[] { "location_id", "item_id" },
                            ("location_id", locationId), ("item_id", itemId)),
                        Element("FORM.form", "Form", new[] { "location_id", "item_id" },
                            ("location_id", locationId), ("item_id", itemId), ("new_cost", newCost)),
                        // year_for_period BEFORE period: the window validates the period
                        // against the year already in the form.
                        Element("FORM.account", "Form", new[] { "account_no" },
                            ("account_no", accountNo), ("year_for_period", year), ("period", period)),
                    },
                },
            },
        };

        PrintPayload("InventoryCostEdit payload (POST /api/v2/transaction)", payload);
        Console.WriteLine("\nNOTE: the save posts to the GL immediately.");
        if (!ConfirmExecute())
            return;

        using var client = await P21Client.CreateAsync();

        var before = await ReadCostAsync(client, itemId, locationId);
        if (before is null)
        {
            Console.WriteLine($"{itemId} has no inv_loc row at location {locationId} — skip it.");
            return;
        }
        Console.WriteLine($"Before: cost {before["moving_average_cost"]}, on hand {before["qty_on_hand"]}");
        var target = decimal.Parse(newCost, CultureInfo.InvariantCulture);
        if ((decimal)before["moving_average_cost"]! == target)
        {
            Console.WriteLine("Already at the target cost — nothing to do.");
            return;
        }

        // HTTP 200 even on failure — only the Summary says whether it landed
        var result = await client.Transaction.CreateAsync(payload);
        if (!CheckResult(result))
        {
            Console.WriteLine("Cost edit failed.");
            return;
        }

        var after = await ReadCostAsync(client, itemId, locationId);
        Console.WriteLine($"After:  cost {after?["moving_average_cost"]}, " +
                          $"last maintained by {after?["last_maintained_by"]}");
        var match = after is not null && (decimal)after["moving_average_cost"]! == target;
        Console.WriteLine($"Read-back: {(match ? "OK" : "MISMATCH — investigate before continuing")}");
    }

    /// <summary>One DataElement with one row; edits keep the order given (it matters on FORM.account).</summary>
    private static JObject Element(string name, string type, string[] keys,
                                   params (string Name, string Value)[] edits) => new()
    {
        ["Name"] = name, ["Type"] = type, ["Keys"] = new JArray(keys),
        ["Rows"] = new JArray { new JObject {
            ["Edits"] = new JArray(edits.Select(e => Edit(e.Name, e.Value))),
            ["RelativeDateEdits"] = new JArray() } },
    };

    /// <summary>inv_loc row for the item at the location, chained by inv_mast_uid (no joins).</summary>
    private static async Task<JToken?> ReadCostAsync(P21Client client, string itemId, string locationId)
    {
        var items = (JArray)(await client.OData.QueryAsync(
            "inv_mast", select: "inv_mast_uid", filter: $"item_id eq '{itemId}'"))["value"]!;
        if (items.Count == 0) return null;

        // location_id and inv_mast_uid are numeric — no quotes
        var locs = (JArray)(await client.OData.QueryAsync(
            "inv_loc", select: "moving_average_cost,qty_on_hand,last_maintained_by",
            filter: $"inv_mast_uid eq {items[0]["inv_mast_uid"]} and location_id eq {locationId}"))["value"]!;
        return locs.Count == 0 ? null : locs[0];
    }

    private static string Ask(string label, string fallback)
    {
        Console.Write($"{label} [{fallback}]: ");
        var answer = Console.ReadLine()?.Trim();
        return string.IsNullOrEmpty(answer) ? fallback : answer;
    }
}
