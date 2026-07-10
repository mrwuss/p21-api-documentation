// Recipe: Create Bins (Bulk)
// Docs:   docs/recipes/create-bins.md
//
// Bulk-create warehouse bins with the BinLocation service — one transaction
// per bin, tens per POST, verified in production at hundreds of bins per run.
//
// Key rules (all verified live — see the recipe page):
//   - IgnoreDisabled: true is mandatory and must be at the payload top level;
//     inside a Transaction it is silently ignored (frozen_flag is disabled).
//   - Pass codes, not uids (bin_type "SHELF", zone "ZONE-A").
//   - Flags are ON/OFF on the form but stored Y/N in dbo.bin — convert when
//     cloning constants from a "twin" bin.
//   - Don't send master_bin_flag — P21 auto-sets it.
//   - Re-running is safe if you skip (bin_id, location_id) pairs that exist.

using Newtonsoft.Json.Linq;
using P21Examples.Common;
using static P21Examples.Recipes.RecipeHelpers;

namespace P21Examples.Recipes;

public static class CreateBins
{
    private const string CompanyId = "ACME";
    private const string LocationId = "10";
    private const int BatchSize = 20;  // tens of transactions per POST is fine and fast

    public static async Task RunAsync()
    {
        Console.WriteLine("Recipe - Create Bins Bulk (BinLocation)");
        Console.WriteLine(new string('=', 60));

        using var client = await P21Client.CreateAsync();

        var newBinIds = new[] { "A01-02-01", "A01-02-02", "A01-02-03", "A01-02-04" };

        // Constants cloned from a "twin" bin of the same bin_type at this location.
        // Flags come back Y/N from the database — convert to ON/OFF for the form.
        var twin = new (string Name, string Value)[]
        {
            ("bin_type", "SHELF"),
            ("putaway_zone_id", "ZONE-A"), ("pick_zone_id", "ZONE-A"),
            ("bin_length", "10"), ("bin_width", "10"), ("bin_height", "11"),
            ("warehouse_sequence", "1"), ("putaway_zone_sequence", "1"), ("pick_zone_sequence", "1"),
            ("max_unique_items", "0"),
            ("pick_locked_flag", "OFF"), ("put_locked_flag", "OFF"),
            ("full_flag", "OFF"), ("frozen_flag", "OFF"),
            ("consolidation_bin_flag", "OFF"), ("stage_bin_flag", "OFF"), ("door_bin_flag", "OFF"),
        };

        // ------------------------------------------------------------------
        // Read-only: skip-existing check via the p21_view_bin view
        // (the raw bin table isn't always exposed via OData)
        // ------------------------------------------------------------------
        var existingRows = (JArray)(await client.OData.QueryViewAsync(
            "p21_view_bin",
            select: "bin_id",
            filter: $"location_id eq {LocationId}"))["value"]!;
        var existing = existingRows.Select(r => (string)r["bin_id"]!).ToHashSet();

        var toCreate = newBinIds.Where(b => !existing.Contains(b)).ToList();
        Console.WriteLine(
            $"\n{newBinIds.Length - toCreate.Count} already exist, creating {toCreate.Count}");
        if (toCreate.Count == 0)
            return;

        var batches = toCreate.Chunk(BatchSize).ToList();
        foreach (var batch in batches)
        {
            var preview = BuildBatchPayload(batch, twin);
            PrintPayload($"Batch payload ({batch.Length} bin(s))", preview);
        }

        if (!ConfirmExecute())
            return;

        // ------------------------------------------------------------------
        // Write: one POST per batch, per-transaction result checks
        // ------------------------------------------------------------------
        foreach (var batch in batches)
        {
            var payload = BuildBatchPayload(batch, twin);
            var result = await client.Transaction.CreateAsync(payload);
            Console.WriteLine();
            CheckResult(result);

            // Transactions pass/fail independently — check each one
            var txns = result.Raw?["Results"]?["Transactions"] as JArray ?? new JArray();
            foreach (var (binId, txn) in batch.Zip(txns))
                if ((string?)txn["Status"] != "Passed")
                    Console.WriteLine($"  FAILED: {binId}");
        }

        // ------------------------------------------------------------------
        // Verify: read the new bins back through p21_view_bin
        // ------------------------------------------------------------------
        Console.WriteLine("\nVerify via p21_view_bin:");
        Console.WriteLine(new string('-', 50));
        foreach (var binId in toCreate)
        {
            var rows = (JArray)(await client.OData.QueryViewAsync(
                "p21_view_bin",
                filter: $"location_id eq {LocationId} and bin_id eq '{binId}'"))["value"]!;
            Console.WriteLine(rows.Count > 0
                ? $"  {binId}: exists (bin_type={rows[0]["bin_type"]})"
                : $"  {binId}: NOT FOUND");
        }
        Console.WriteLine(
            "\n  Compare field-for-field against the twin after the first run" +
            " (remember the Y/N <-> ON/OFF flag mapping).");
    }

    private static JObject BuildBatchPayload(
        string[] batch, (string Name, string Value)[] twin)
    {
        return new JObject
        {
            ["Name"] = "BinLocation",
            ["UseCodeValues"] = false,
            ["IgnoreDisabled"] = true, // TOP LEVEL — inside a Transaction it is silently ignored
            ["Transactions"] = new JArray(batch.Select(b => BuildBinTransaction(b, twin))),
        };
    }

    /// <summary>One Transaction object per bin (keys first, then the twin's constants).</summary>
    private static JObject BuildBinTransaction(string binId, (string Name, string Value)[] twin)
    {
        var edits = new JArray
        {
            Edit("company_id", CompanyId),
            Edit("location_id", LocationId),
            Edit("bin_id", binId),
        };
        foreach (var (name, value) in twin)
            edits.Add(Edit(name, value));

        return new JObject
        {
            ["Status"] = "New",
            ["DataElements"] = new JArray
            {
                new JObject
                {
                    ["Name"] = "FORM.form", ["Type"] = "Form",
                    ["Keys"] = new JArray("company_id", "location_id", "bin_id"),
                    ["Rows"] = new JArray(new JObject { ["Edits"] = edits }),
                }
            },
        };
    }
}
