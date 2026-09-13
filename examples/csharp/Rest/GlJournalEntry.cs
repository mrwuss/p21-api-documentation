// Other REST Families - Read a GL Journal Entry
// Docs: docs/15-Other-REST-Families.md#accountinggl
// Mirrors: examples/python/rest/gl_journal_entry.py
//
// Reads every distribution line of one GL transaction in a single call,
// confirms the entry balances to zero, and follows Source back to the
// originating document for a known JournalId.
//
// Verified live, 26.1.5950.0: an unknown transaction number returns
// HTTP 200 [] -- not a 404.

using Newtonsoft.Json.Linq;

namespace P21Examples.Rest;

public static class GlJournalEntry
{
    // JournalId -> the family that reads Source back. Extend as more are verified.
    private static readonly Dictionary<string, string> SourceFamily = new()
    {
        ["IA"] = "inventory/inventoryadjustments",
    };

    public static async Task RunAsync()
    {
        Console.WriteLine("Other REST Families - GL Journal Entry");
        Console.WriteLine(new string('=', 60));

        Console.Write("gl.transaction_number to read (e.g. 3): ");
        var transactionNumber = Console.ReadLine()?.Trim();
        if (string.IsNullOrEmpty(transactionNumber))
        {
            Console.WriteLine("No transaction number given.");
            return;
        }

        var (http, baseUrl) = await RestHelpers.CreateRawClientAsync();
        using var _ = http;
        Console.WriteLine($"Server: {baseUrl}");

        var response = await http.GetAsync($"{baseUrl}/api/accounting/gl/{transactionNumber}");
        response.EnsureSuccessStatusCode();
        var lines = JArray.Parse(await response.Content.ReadAsStringAsync());

        if (lines.Count == 0)
        {
            Console.WriteLine($"\nTransaction {transactionNumber}: no lines " +
                              "(HTTP 200 [] -- unknown transaction number)");
            return;
        }

        Console.WriteLine($"\nTransaction {transactionNumber}: {lines.Count} line(s)");
        Console.WriteLine(new string('-', 50));
        decimal total = 0m;
        foreach (var line in lines)
        {
            var amount = (decimal)line["Amount"]!;
            total += amount;
            Console.WriteLine($"  {(string)line["AccountNumber"]!,-14} {amount,14:N2}  " +
                              $"journal={line["JournalId"]}  source={line["Source"]}");
        }
        Console.WriteLine($"\n  Balance: {total:N2}  " +
                          $"({(Math.Abs(total) < 0.005m ? "balanced" : "NOT BALANCED")})");

        var journalId = (string?)lines[0]["JournalId"];
        if (journalId != null && SourceFamily.TryGetValue(journalId, out var family))
        {
            var source = (string)lines[0]["Source"]!;
            Console.WriteLine($"\nFollowing Source on the first line ({family}/{source}):");
            var docResponse = await http.GetAsync($"{baseUrl}/api/{family}/{source}");
            docResponse.EnsureSuccessStatusCode();
            var doc = JObject.Parse(await docResponse.Content.ReadAsStringAsync());
            foreach (var prop in doc.Properties())
            {
                if (prop.Name is "Lines" or "UserDefinedFields") continue;
                Console.WriteLine($"    {prop.Name}: {prop.Value}");
            }
        }
    }
}
