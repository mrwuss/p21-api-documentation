// Recipe: Record Labor Time on a Production Order
// Docs:   docs/recipes/record-labor-time.md
//
// Post a technician's labor hours to a production order with the TimeEntry
// service, then read the labor grid back.
//
// Key rules (all verified live — see the recipe page):
//   - Strict field order on the labor grid: prod_order_number -> item_id ->
//     component_labor_id -> start_time -> end_time. Out of order, the
//     downstream fields stay disabled and the values don't land.
//   - technician_id is a CONTACT ID, not a P21 user ID.
//   - The accounting period for entry_date must be open.
//   - Time ACCUMULATES: re-posting the same entry doubles the labor.
//   - Log labor before printing the pick ticket (or reprint after).
//   - labor_type_cd is required — Rate, OT Rate, Prem Rate.

using Newtonsoft.Json.Linq;
using P21Examples.Common;
using static P21Examples.Recipes.RecipeHelpers;

namespace P21Examples.Recipes;

public static class RecordLaborTime
{
    private const string ProdOrder = "1000123";

    public static async Task RunAsync()
    {
        Console.WriteLine("Recipe - Record Labor Time (TimeEntry)");
        Console.WriteLine(new string('=', 60));

        using var client = await P21Client.CreateAsync();

        var payload = new JObject
        {
            ["Name"] = "TimeEntry",
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
                            ["Name"] = "TP_TECHNICIAN.tp_technician",
                            ["Type"] = "Form",
                            ["Keys"] = new JArray(),
                            ["Rows"] = new JArray
                            {
                                new JObject
                                {
                                    ["Edits"] = new JArray
                                    {
                                        Edit("company_id", "ACME"),
                                        Edit("technician_id", "300"),  // CONTACT id, not a user id
                                        Edit("entry_date", "2030-01-05"),
                                    },
                                    ["RelativeDateEdits"] = new JArray()
                                }
                            }
                        },
                        new JObject
                        {
                            ["Name"] = "TP_LABORRECORDING.prod_order_line_comp_labor",
                            ["Type"] = "List",
                            ["Keys"] = new JArray { "prod_order_number" },
                            ["Rows"] = new JArray
                            {
                                new JObject
                                {
                                    // Strict order: prod_order_number -> item_id ->
                                    // component_labor_id -> start_time -> end_time
                                    ["Edits"] = new JArray
                                    {
                                        Edit("prod_order_number", ProdOrder),
                                        Edit("item_id", "ASSY-100"),          // the assembly LINE's item
                                        Edit("component_labor_id", "LABOR-SHOP"),
                                        Edit("start_time", "2030-01-05T08:00:00"),
                                        Edit("end_time", "2030-01-05T12:00:00"),
                                        Edit("labor_type_cd", "Rate"),        // required
                                    },
                                    ["RelativeDateEdits"] = new JArray()
                                }
                            }
                        }
                    }
                }
            }
        };

        PrintPayload("TimeEntry payload (4 hours)", payload);
        Console.WriteLine("\nNOTE: time ACCUMULATES — re-posting the same entry doubles the labor.");

        if (!ConfirmExecute())
            return;

        // ------------------------------------------------------------------
        // Write
        // ------------------------------------------------------------------
        var result = await client.Transaction.CreateAsync(payload);
        if (!CheckResult(result))
            return;

        // ------------------------------------------------------------------
        // Verify: read the labor grid back — time_worked should reflect the
        // ACCUMULATED total, not just this entry.
        // ------------------------------------------------------------------
        Console.WriteLine("\nVerify: labor grid via /transaction/get:");
        Console.WriteLine(new string('-', 50));

        var getPayload = new JObject
        {
            ["ServiceName"] = "TimeEntry",
            ["TransactionStates"] = new JArray
            {
                new JObject
                {
                    ["DataElementName"] = "TP_LABORRECORDING.prod_order_line_comp_labor",
                    ["Keys"] = new JArray
                    {
                        new JObject { ["Name"] = "prod_order_number", ["Value"] = ProdOrder }
                    }
                }
            }
        };
        var getResult = await client.Transaction.GetRecordsAsync(getPayload);

        foreach (var txn in getResult["Transactions"] as JArray ?? new JArray())
        foreach (var de in txn["DataElements"] as JArray ?? new JArray())
        foreach (var row in de["Rows"] as JArray ?? new JArray())
        {
            var fields = new Dictionary<string, string>();
            foreach (var edit in row["Edits"] as JArray ?? new JArray())
                fields[edit["Name"]!.ToString()] = edit["Value"]?.ToString() ?? "";
            if (!string.IsNullOrEmpty(fields.GetValueOrDefault("prod_order_number")))
                Console.WriteLine(
                    $"  {fields.GetValueOrDefault("component_labor_id")}: " +
                    $"time_worked={fields.GetValueOrDefault("time_worked")}");
        }
    }
}
