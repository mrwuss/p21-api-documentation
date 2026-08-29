// Recipe: Edit Contract Bin Quantities
// Docs:   docs/recipes/edit-contract-bins.md
//
// Change min_qty, max_qty, reorder_qty, and capacity on the bins of an
// existing job contract via the Transaction API with IgnoreDisabled: true.
//
// Key rules (all verified live — see the recipe page):
//   - IgnoreDisabled: true is MANDATORY and goes at the payload top level;
//     inside a Transaction it is silently ignored ("Column is disabled: ...").
//   - Select the line by item_id (the JOBPRICELINE key), not line_no.
//   - Batching is fine here — repeat the JOBPRICELINE + BINS.bins pair per bin.
//   - No end_date required; works on expired contracts too.
//   - Status "New" even for an existing contract (the only value the enum accepts).

using Newtonsoft.Json.Linq;
using P21Examples.Common;
using static P21Examples.Recipes.RecipeHelpers;

namespace P21Examples.Recipes;

public static class EditContractBins
{
    private const string ContractNo = "JOB-1001";
    private const string JobNo = "31";
    private const string CustomerId = "100198";
    private const string ShipToId = "200";

    public static async Task RunAsync()
    {
        Console.WriteLine("Recipe - Edit Contract Bin Quantities (JobContractPricing)");
        Console.WriteLine(new string('=', 60));

        using var client = await P21Client.CreateAsync();

        // Per bin: the line's item_id, the bin id, and the new quantities.
        var binEdits = new (string ItemId, string BinId, int Min, int Max, int Reorder, int Capacity)[]
        {
            ("WIDGET-001", "A01-02", 30, 100, 40, 100),
            ("WIDGET-002", "A01-02", 5, 50, 10, 50),
        };

        var payload = BuildBinPayload(binEdits);
        PrintPayload("Bin edit payload (one POST, batched)", payload);

        if (!ConfirmExecute())
            return;

        // ------------------------------------------------------------------
        // Write: one POST covers every bin
        // ------------------------------------------------------------------
        var result = await client.Transaction.CreateAsync(payload);
        if (!CheckResult(result))
            return;

        // ------------------------------------------------------------------
        // Verify via OData (no joins: chain the uid columns)
        // ------------------------------------------------------------------
        Console.WriteLine("\nVerify via OData:");
        Console.WriteLine(new string('-', 50));

        var hdrRows = (JArray)(await client.OData.QueryAsync(
            "job_price_hdr", filter: $"contract_no eq '{ContractNo}'"))["value"]!;
        if (hdrRows.Count == 0)
        {
            Console.WriteLine($"  Contract {ContractNo} not found");
            return;
        }
        var hdrUid = hdrRows[0]["job_price_hdr_uid"];

        foreach (var e in binEdits)
        {
            var imRows = (JArray)(await client.OData.QueryAsync(
                "inv_mast", filter: $"item_id eq '{e.ItemId}'"))["value"]!;
            if (imRows.Count == 0)
            {
                Console.WriteLine($"  {e.ItemId}: item not found in inv_mast");
                continue;
            }
            var imUid = imRows[0]["inv_mast_uid"];

            var lineRows = (JArray)(await client.OData.QueryAsync(
                "job_price_line",
                filter: $"job_price_hdr_uid eq {hdrUid} and inv_mast_uid eq {imUid}"))["value"]!;
            if (lineRows.Count == 0)
            {
                Console.WriteLine($"  {e.ItemId}: no contract line found");
                continue;
            }

            var binRows = (JArray)(await client.OData.QueryAsync(
                "job_price_bin",
                filter: $"job_price_line_uid eq {lineRows[0]["job_price_line_uid"]}"))["value"]!;
            foreach (var binRow in binRows)
            {
                Console.WriteLine(
                    $"  {e.ItemId}: min={binRow["min_qty"]} max={binRow["max_qty"]} " +
                    $"reorder={binRow["reorder_qty"]} " +
                    $"(expected {e.Min}/{e.Max}/{e.Reorder})");
            }
        }
    }

    private static JObject BuildBinPayload(
        (string ItemId, string BinId, int Min, int Max, int Reorder, int Capacity)[] binEdits)
    {
        var elements = new JArray
        {
            new JObject
            {
                // Load the contract header. job_no is unique across renewals.
                ["Name"] = "FORM.d_dw_job_price_hdr", ["Type"] = "Form",
                ["Keys"] = new JArray(),
                ["Rows"] = new JArray { new JObject { ["Edits"] = new JArray {
                    Edit("job_no",      JobNo),
                    Edit("customer_id", CustomerId),
                    Edit("ship_to_id",  ShipToId),
                } } }
            }
        };

        foreach (var e in binEdits)
        {
            elements.Add(new JObject
            {
                // Select the line by item_id (NOT line_no).
                ["Name"] = "JOBPRICELINE.jobpriceline", ["Type"] = "List",
                ["Keys"] = new JArray { "item_id" },
                ["Rows"] = new JArray { new JObject {
                    ["Edits"] = new JArray { Edit("item_id", e.ItemId) } } }
            });
            elements.Add(new JObject
            {
                // Edit the bin quantities.
                ["Name"] = "BINS.bins", ["Type"] = "List",
                ["Keys"] = new JArray { "contract_bin_id", "customer_id", "ship_to_id" },
                ["Rows"] = new JArray { new JObject { ["Edits"] = new JArray {
                    Edit("contract_bin_id", e.BinId),
                    Edit("customer_id",     CustomerId),
                    Edit("ship_to_id",      ShipToId),
                    Edit("min_qty",         e.Min.ToString()),
                    Edit("max_qty",         e.Max.ToString()),
                    Edit("reorder_qty",     e.Reorder.ToString()),
                    Edit("capacity",        e.Capacity.ToString()),
                } } }
            });
        }

        return new JObject
        {
            ["Name"] = "JobContractPricing", ["UseCodeValues"] = false,
            ["IgnoreDisabled"] = true,  // top level — mandatory for the BINS sub-tab
            ["Transactions"] = new JArray {
                new JObject { ["Status"] = "New", ["DataElements"] = elements } }
        };
    }
}
