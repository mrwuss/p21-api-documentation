// OData API - Filtering Examples
//
// Demonstrates various $filter expressions and operators.
// Mirrors: examples/python/odata/02_filtering.py
//
// OData filter operators supported by P21:
//   eq, ne, gt, ge, lt, le     — comparison
//   and, or, not               — logical
//   startswith(), endswith()    — string prefix/suffix
//   contains()                 — substring match
//   null                       — null checks (eq null, ne null)

using System.Net.Http;
using Newtonsoft.Json.Linq;
using P21Examples.Common;

namespace P21Examples.OData;

public static class Filtering
{
    public static async Task RunAsync()
    {
        Console.WriteLine("OData API - Filtering Examples");
        Console.WriteLine(new string('=', 50));

        // Authenticate
        var config = P21Config.FromEnvironment();
        using var handler = new HttpClientHandler();
        if (!config.VerifySsl)
        {
            handler.ServerCertificateCustomValidationCallback =
                HttpClientHandler.DangerousAcceptAnyServerCertificateValidator;
        }
        using var http = new HttpClient(handler) { Timeout = TimeSpan.FromSeconds(30) };

        var token = await P21Auth.GetTokenAsync(http, config);
        P21Auth.SetAuthHeaders(http, token.AccessToken);

        var odata = new ODataApi(http, config.ODataUrl);

        // -----------------------------------------------------------------
        // Example 1: Equality filter
        // -----------------------------------------------------------------
        Console.WriteLine("\n1. Equality filter (supplier_id eq 20000):");
        Console.WriteLine(new string('-', 40));

        // The "eq" operator tests exact equality.
        // Numeric fields don't need quotes; string fields use single quotes.
        var data = await odata.QueryAsync(
            "price_page",
            select: "price_page_uid,description,supplier_id",
            filter: "supplier_id eq 20000",
            top: 5);

        var values = data["value"]!;
        Console.WriteLine($"  Found {values.Count()} records:");
        foreach (var page in values)
        {
            var desc = Truncate(page["description"]?.ToString(), 40);
            Console.WriteLine($"    {page["price_page_uid"]}: {desc}");
        }

        // -----------------------------------------------------------------
        // Example 2: Multiple conditions (AND)
        // -----------------------------------------------------------------
        Console.WriteLine("\n2. Multiple conditions (AND):");
        Console.WriteLine(new string('-', 40));

        // Combine filters with "and". Row status 704 = active in P21.
        data = await odata.QueryAsync(
            "price_page",
            select: "price_page_uid,description,row_status_flag",
            filter: "supplier_id eq 20000 and row_status_flag eq 704",
            top: 5);

        values = data["value"]!;
        Console.WriteLine($"  Active pages for supplier 20000: {values.Count()} found");
        foreach (var page in values)
        {
            var desc = Truncate(page["description"]?.ToString(), 40);
            Console.WriteLine($"    {page["price_page_uid"]}: {desc}");
        }

        // -----------------------------------------------------------------
        // Example 3: String function (startswith)
        // -----------------------------------------------------------------
        Console.WriteLine("\n3. String function (startswith):");
        Console.WriteLine(new string('-', 40));

        // String functions wrap the field name: startswith(field,'value')
        // Note: single quotes around the string value, no spaces after comma.
        data = await odata.QueryAsync(
            "supplier",
            select: "supplier_id,supplier_name",
            filter: "startswith(supplier_name,'A')",
            orderby: "supplier_name",
            top: 5);

        Console.WriteLine("  Suppliers starting with 'A':");
        foreach (var supplier in data["value"]!)
        {
            Console.WriteLine($"    {supplier["supplier_id"]}: {supplier["supplier_name"]}");
        }

        // -----------------------------------------------------------------
        // Example 4: Contains filter
        // -----------------------------------------------------------------
        Console.WriteLine("\n4. Contains filter:");
        Console.WriteLine(new string('-', 40));

        // contains(field,'substring') matches anywhere in the field value.
        data = await odata.QueryAsync(
            "product_group",
            select: "product_group_id,product_group_desc",
            filter: "contains(product_group_id,'F')",
            top: 5);

        Console.WriteLine("  Product groups containing 'F':");
        foreach (var group in data["value"]!)
        {
            var desc = group["product_group_desc"]?.ToString() ?? "N/A";
            Console.WriteLine($"    {group["product_group_id"]}: {desc}");
        }

        // -----------------------------------------------------------------
        // Example 5: Comparison operators (range filter)
        // -----------------------------------------------------------------
        Console.WriteLine("\n5. Comparison operators (greater than):");
        Console.WriteLine(new string('-', 40));

        // Use gt/lt/ge/le for numeric range queries.
        // This finds price pages with multiplier between 0.5 and 1.0.
        data = await odata.QueryAsync(
            "price_page",
            select: "price_page_uid,description,calculation_value1",
            filter: "calculation_value1 gt 0.5 and calculation_value1 lt 1.0",
            orderby: "calculation_value1 desc",
            top: 5);

        Console.WriteLine("  Pages with multiplier between 0.5 and 1.0:");
        foreach (var page in data["value"]!)
        {
            var val = page["calculation_value1"]?.Value<decimal>() ?? 0m;
            var desc = Truncate(page["description"]?.ToString(), 30);
            Console.WriteLine($"    {page["price_page_uid"]}: {val:F3} - {desc}");
        }

        Console.WriteLine($"\n{new string('=', 50)}");
        Console.WriteLine("Filtering examples complete!");
    }

    /// <summary>
    /// Truncate a string to a maximum length, appending "..." if truncated.
    /// </summary>
    private static string Truncate(string? value, int maxLength)
    {
        if (string.IsNullOrEmpty(value)) return "N/A";
        return value.Length <= maxLength ? value : value[..maxLength] + "...";
    }
}
