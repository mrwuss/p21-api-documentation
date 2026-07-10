// OData API - Pagination Examples
//
// Demonstrates $skip, $top, and $count for paginating large result sets.
// Mirrors: examples/python/odata/03_pagination.py
//
// Key concepts:
//   $top=N      — return at most N rows
//   $skip=N     — skip the first N rows
//   $count=true — include total row count in response (as @odata.count)
//   $top=0      — return count only, no data rows (useful for totals)
//
// Automatic pagination: loop with $skip increments until all rows are fetched.

using System.Net.Http;
using Newtonsoft.Json.Linq;
using P21Examples.Common;

namespace P21Examples.OData;

public static class Pagination
{
    public static async Task RunAsync()
    {
        Console.WriteLine("OData API - Pagination Examples");
        Console.WriteLine(new string('=', 50));

        // Authenticate
        var config = P21Config.FromEnvironment();
        using var handler = new HttpClientHandler();
        if (!config.VerifySsl)
        {
            handler.ServerCertificateCustomValidationCallback =
                HttpClientHandler.DangerousAcceptAnyServerCertificateValidator;
        }
        using var http = new HttpClient(handler) { Timeout = TimeSpan.FromSeconds(60) };

        var token = await P21Auth.GetTokenAsync(http, config);
        P21Auth.SetAuthHeaders(http, token.AccessToken);

        var odata = new ODataApi(http, config.ODataUrl);

        // -----------------------------------------------------------------
        // Example 1: Manual pagination — page 1
        // -----------------------------------------------------------------
        Console.WriteLine("\n1. Manual pagination (page 1 of suppliers):");
        Console.WriteLine(new string('-', 40));

        const int pageSize = 5;

        var page1 = await GetPageAsync(
            odata, "supplier", pageNum: 1, pageSize: pageSize);

        var total = page1["@odata.count"]?.Value<int>() ?? 0;
        var totalPages = (total + pageSize - 1) / pageSize;

        Console.WriteLine($"  Total records: {total}");
        Console.WriteLine($"  Page size: {pageSize}");
        Console.WriteLine($"  Total pages: {totalPages}");
        Console.WriteLine("  Page 1 results:");
        foreach (var supplier in page1["value"]!)
        {
            Console.WriteLine($"    {supplier["supplier_id"]}: {supplier["supplier_name"]}");
        }

        // -----------------------------------------------------------------
        // Example 2: Manual pagination — page 2
        // -----------------------------------------------------------------
        Console.WriteLine("\n2. Page 2 of suppliers:");
        Console.WriteLine(new string('-', 40));

        var page2 = await GetPageAsync(
            odata, "supplier", pageNum: 2, pageSize: pageSize);

        Console.WriteLine("  Page 2 results:");
        foreach (var supplier in page2["value"]!)
        {
            Console.WriteLine($"    {supplier["supplier_id"]}: {supplier["supplier_name"]}");
        }

        // -----------------------------------------------------------------
        // Example 3: Automatic pagination with filter
        // -----------------------------------------------------------------
        Console.WriteLine("\n3. Fetch all active price pages for supplier 20000:");
        Console.WriteLine(new string('-', 40));

        var allRecords = await GetAllRecordsAsync(
            odata,
            "price_page",
            filter: "supplier_id eq 20000 and row_status_flag eq 704",
            pageSize: 50);

        Console.WriteLine($"\n  Total records fetched: {allRecords.Count}");
        if (allRecords.Count > 0)
        {
            Console.WriteLine("  Sample records:");
            foreach (var page in allRecords.Take(3))
            {
                var desc = page["description"]?.ToString() ?? "N/A";
                if (desc.Length > 40) desc = desc[..40] + "...";
                Console.WriteLine($"    {page["price_page_uid"]}: {desc}");
            }
        }

        // -----------------------------------------------------------------
        // Example 4: Count only (no data rows)
        // -----------------------------------------------------------------
        Console.WriteLine("\n4. Count only (no data fetch):");
        Console.WriteLine(new string('-', 40));

        // Setting $top=0 with $count=true gives you the total count
        // without transferring any row data — fast and lightweight.
        var countData = await odata.QueryAsync(
            "price_page",
            top: 0,
            count: true);

        var totalPages2 = countData["@odata.count"]?.ToString() ?? "N/A";
        Console.WriteLine($"  Total price pages: {totalPages2}");

        Console.WriteLine($"\n{new string('=', 50)}");
        Console.WriteLine("Pagination examples complete!");
    }

    /// <summary>
    /// Fetch a single page of supplier results.
    /// Page numbers are 1-based (page 1, 2, 3...).
    /// </summary>
    private static async Task<JObject> GetPageAsync(
        ODataApi odata, string table, int pageNum, int pageSize)
    {
        // $skip is 0-based: page 1 skips 0, page 2 skips pageSize, etc.
        var skip = (pageNum - 1) * pageSize;

        return await odata.QueryAsync(
            table,
            select: "supplier_id,supplier_name",
            orderby: "supplier_id",
            top: pageSize,
            skip: skip,
            count: true);
    }

    /// <summary>
    /// Fetch all matching records with automatic pagination.
    /// Loops through pages until all rows are retrieved.
    /// </summary>
    /// <param name="odata">OData API client.</param>
    /// <param name="table">Table name.</param>
    /// <param name="filter">Optional OData $filter expression.</param>
    /// <param name="pageSize">Rows per request (default 100).</param>
    /// <returns>All matching rows as a list of JTokens.</returns>
    private static async Task<List<JToken>> GetAllRecordsAsync(
        ODataApi odata, string table, string? filter = null, int pageSize = 100)
    {
        var allRecords = new List<JToken>();
        var skip = 0;

        while (true)
        {
            var data = await odata.QueryAsync(
                table,
                filter: filter,
                top: pageSize,
                skip: skip,
                count: true);

            var rows = data["value"]!.ToList();
            allRecords.AddRange(rows);

            var total = data["@odata.count"]?.Value<int>() ?? allRecords.Count;
            Console.WriteLine($"    Fetched {allRecords.Count} of {total} records...");

            // Stop when we have all records
            if (allRecords.Count >= total)
                break;

            skip += pageSize;
        }

        return allRecords;
    }
}
