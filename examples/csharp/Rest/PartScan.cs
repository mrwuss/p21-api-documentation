// Other REST Families - Cross-Entity Part Lookup (inventory/partscan)
// Docs: docs/15-Other-REST-Families.md#inventorypartscan
// Mirrors: examples/python/rest/part_scan.py

using Newtonsoft.Json.Linq;

namespace P21Examples.Rest;

public static class PartScan
{
    public static async Task RunAsync()
    {
        Console.WriteLine("Other REST Families - Part Scan (inventory/partscan)");
        Console.WriteLine(new string('=', 60));

        var (http, baseUrl) = await RestHelpers.CreateRawClientAsync();
        using var _ = http;
        Console.WriteLine($"Server: {baseUrl}");

        Console.Write("Search term [GBY]: ");
        var term = Console.ReadLine()?.Trim();
        term = string.IsNullOrEmpty(term) ? "GBY" : term;

        // Trailing slash before the query string matters -- the bare
        // form without it 307-redirects.
        var response = await http.GetAsync(
            $"{baseUrl}/api/inventory/partscan/?partSearch={term}&companyId=ACME" +
            "&locationId=&customerId=&supplierId=");
        response.EnsureSuccessStatusCode();
        var matches = JArray.Parse(await response.Content.ReadAsStringAsync());

        Console.WriteLine($"\nMatches for \"{term}\":");
        Console.WriteLine(new string('-', 50));
        foreach (var match in matches)
            Console.WriteLine($"  ItemId={match["ItemId"],-20} Source={match["Source"],-20} " +
                              $"InvMastUid={match["InvMastUid"]}");
    }
}
