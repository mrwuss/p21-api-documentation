// Recipe: Lock, Unlock, Delete, or Restore Bins (BinLocation)
// Docs:   docs/03-Transaction-API.md#locking-unlocking-and-deleting-bins
//
// Same service, element, and three-field key as bin creation. A keyed
// Status "New" row lands on the existing bin and changes only the flags sent:
//   lock     pick_locked_flag + put_locked_flag = ON
//   unlock   the same flags = OFF
//   delete   delete_flag = ON  (soft delete)
//   restore  delete_flag = OFF
//
// No IgnoreDisabled: these are enabled columns. Before writing, the recipe
// prints the current flags (your backup) and refuses to lock or delete a bin
// that holds stock or is an item's primary bin. A skipped delete reports no
// error, so the p21_view_bin read-back afterwards is the proof.

using Newtonsoft.Json.Linq;
using P21Examples.Common;
using static P21Examples.Recipes.RecipeHelpers;
using static P21Examples.Recipes.WritePathHelpers;

namespace P21Examples.Recipes;

public static class BinLockDelete
{
    private static readonly Dictionary<string, (Dictionary<string, string> Edits, Dictionary<string, string> Expected)> Modes = new()
    {
        ["lock"] = (new() { ["pick_locked_flag"] = "ON", ["put_locked_flag"] = "ON" },
                    new() { ["pick_locked_flag"] = "Y", ["put_locked_flag"] = "Y" }),
        ["unlock"] = (new() { ["pick_locked_flag"] = "OFF", ["put_locked_flag"] = "OFF" },
                      new() { ["pick_locked_flag"] = "N", ["put_locked_flag"] = "N" }),
        ["delete"] = (new() { ["delete_flag"] = "ON" }, new() { ["delete_flag"] = "Y" }),
        ["restore"] = (new() { ["delete_flag"] = "OFF" }, new() { ["delete_flag"] = "N" }),
    };

    private const string FlagColumns = "bin_id,delete_flag,pick_locked_flag,put_locked_flag";

    public static async Task RunAsync()
    {
        Console.WriteLine("Recipe - Lock / Unlock / Delete / Restore Bins (BinLocation)");
        Console.WriteLine(new string('=', 60));

        var mode = Ask("Mode (lock, unlock, delete, restore)", "lock").ToLowerInvariant();
        if (!Modes.ContainsKey(mode))
        {
            Console.WriteLine($"Unknown mode: {mode}");
            return;
        }
        var companyId = Ask("Company ID", "ACME");
        var locationId = Ask("Location ID", "10");
        var binIds = Ask("Bin IDs (comma-separated)", "A01-02-03")
            .Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);

        var (edits, expected) = Modes[mode];
        var payload = BuildPayload(companyId, locationId, binIds, edits);
        PrintPayload("Payload", payload);

        if (!ConfirmExecute())
            return;

        using var client = await P21Client.CreateAsync();

        var before = await ReadBins(client, locationId, binIds);
        var missing = binIds.Where(b => !before.ContainsKey(b)).ToList();
        if (missing.Count > 0)
        {
            Console.WriteLine($"Not found at location {locationId}: {string.Join(", ", missing)}");
            return;
        }
        Console.WriteLine("\nBefore (keep this as your backup):");
        foreach (var b in binIds)
            Console.WriteLine($"  {before[b].ToString(Newtonsoft.Json.Formatting.None)}");

        if (mode is "lock" or "delete")
        {
            var problems = new List<string>();
            foreach (var b in binIds)
            {
                var stock = await Rows(client, "inv_bin",
                    $"location_id eq {locationId} and bin eq {Q(b)} and quantity gt 0", "inv_mast_uid");
                if (stock.Count > 0) problems.Add($"{b}: holds stock for {stock.Count} item(s)");
                var primary = await Rows(client, "inv_loc",
                    $"location_id eq {locationId} and primary_bin eq {Q(b)}", "inv_mast_uid");
                if (primary.Count > 0) problems.Add($"{b}: primary bin for {primary.Count} item(s)");
            }
            if (problems.Count > 0)
            {
                Console.WriteLine("Refusing: locking or deleting a bin in use strands stock and putaways.");
                problems.ForEach(p => Console.WriteLine($"  {p}"));
                return;
            }
        }

        Console.WriteLine();
        CheckResult(await client.Transaction.CreateAsync(payload));

        // A skipped write reports no error -- the read-back decides.
        Console.WriteLine("\nVerify (p21_view_bin read-back):");
        var after = await ReadBins(client, locationId, binIds);
        var failures = 0;
        foreach (var b in binIds)
        {
            var row = after.GetValueOrDefault(b);
            var ok = row != null && expected.All(kv => (string?)row[kv.Key] == kv.Value);
            if (!ok) failures++;
            Console.WriteLine($"  {b}: {(ok ? "OK" : "NOT APPLIED")} {row?.ToString(Newtonsoft.Json.Formatting.None)}");
        }
        if (failures > 0)
            Console.WriteLine($"{failures} bin(s) did not change");
    }

    /// <summary>One BinLocation payload, one Transaction per bin.</summary>
    private static JObject BuildPayload(
        string companyId, string locationId, string[] binIds, Dictionary<string, string> flags)
    {
        var transactions = new JArray();
        foreach (var binId in binIds)
        {
            var edits = new List<JObject>
            {
                Edit("company_id", companyId),
                Edit("location_id", locationId),
                Edit("bin_id", binId),
            };
            edits.AddRange(flags.Select(kv => Edit(kv.Key, kv.Value)));
            transactions.Add(new JObject
            {
                ["Status"] = "New",
                ["DataElements"] = new JArray {
                    Element("FORM.form", "Form", new[] { "company_id", "location_id", "bin_id" },
                            edits.ToArray()) }
            });
        }
        return new JObject
        {
            ["Name"] = "BinLocation", ["UseCodeValues"] = false,
            ["Transactions"] = transactions
        };
    }

    /// <summary>Read the bins' flags through the p21_view_bin view (Y/N values).</summary>
    private static async Task<Dictionary<string, JObject>> ReadBins(
        P21Client client, string locationId, string[] binIds)
    {
        var ids = string.Join(" or ", binIds.Select(b => $"bin_id eq {Q(b)}"));
        var rows = await Rows(client, "p21_view_bin",
            $"location_id eq {locationId} and ({ids})", FlagColumns, view: true);
        return rows.Cast<JObject>().ToDictionary(r => (string)r["bin_id"]!, r => r);
    }
}
