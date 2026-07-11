// OData API - Complex Query Examples
//
// Demonstrates advanced filtering, combining conditions, and real-world queries.
// Mirrors: examples/python/odata/04_complex_queries.py
//
// Topics covered:
//   - Multi-field filter with ordering
//   - OR conditions across multiple values
//   - String contains combined with other filters
//   - Null value checks (ne null, eq null)
//   - Multiple $orderby fields
//   - Join-like pattern (two sequential queries to correlate data)

using System.Net.Http;
using Newtonsoft.Json.Linq;
using P21Examples.Common;

namespace P21Examples.OData;

public static class ComplexQueries
{
    public static async Task RunAsync()
    {
        Console.WriteLine("OData API - Complex Query Examples");
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
        // Example 1: Multi-field filter with ordering
        // -----------------------------------------------------------------
        Console.WriteLine("\n1. Multi-field filter with ordering:");
        Console.WriteLine(new string('-', 40));
        Console.WriteLine("   Query: Active pages for supplier, ordered by effective date");

        var data = await odata.QueryAsync(
            "price_page",
            select: "price_page_uid,description,effective_date,expiration_date,calculation_value1",
            filter: "supplier_id eq 20000 and row_status_flag eq 704",
            orderby: "effective_date desc",
            top: 5);

        foreach (var page in data["value"]!)
        {
            var eff = FormatDate(page["effective_date"]);
            var exp = FormatDate(page["expiration_date"]);
            var val = page["calculation_value1"]?.Value<decimal>() ?? 0m;
            Console.WriteLine($"  {page["price_page_uid"]}: {eff} to {exp} (mult: {val:F3})");
        }

        // -----------------------------------------------------------------
        // Example 2: OR conditions (multiple suppliers)
        // -----------------------------------------------------------------
        Console.WriteLine("\n2. OR conditions (multiple suppliers):");
        Console.WriteLine(new string('-', 40));

        // Parentheses group the OR conditions, then AND with the status check.
        // Pattern: (fieldA eq X or fieldA eq Y) and fieldB eq Z
        data = await odata.QueryAsync(
            "price_page",
            select: "price_page_uid,supplier_id,description",
            filter: "(supplier_id eq 10 or supplier_id eq 20000) and row_status_flag eq 704",
            top: 10,
            count: true);

        var totalMatching = data["@odata.count"]?.ToString() ?? "N/A";
        Console.WriteLine($"  Total matching: {totalMatching}");
        foreach (var page in data["value"]!)
        {
            var desc = Truncate(page["description"]?.ToString(), 40);
            Console.WriteLine($"  Supplier {page["supplier_id"]}: {desc}");
        }

        // -----------------------------------------------------------------
        // Example 3: String contains with other conditions
        // -----------------------------------------------------------------
        Console.WriteLine("\n3. String contains with other conditions:");
        Console.WriteLine(new string('-', 40));

        // Combine contains() with other filters using "and".
        data = await odata.QueryAsync(
            "price_page",
            select: "price_page_uid,description,supplier_id",
            filter: "contains(description,'ACME_BOOK_A') and row_status_flag eq 704",
            top: 5);

        Console.WriteLine("  Pages with 'ACME_BOOK_A' in description:");
        foreach (var page in data["value"]!)
        {
            var desc = page["description"]?.ToString() ?? "N/A";
            Console.WriteLine($"    {page["price_page_uid"]}: {desc}");
        }

        // -----------------------------------------------------------------
        // Example 4: Null value check
        // -----------------------------------------------------------------
        Console.WriteLine("\n4. Null value check:");
        Console.WriteLine(new string('-', 40));

        // Use "ne null" to find records with a value set,
        // or "eq null" to find records where the field is empty.
        data = await odata.QueryAsync(
            "price_page",
            select: "price_page_uid,description,expiration_date",
            filter: "expiration_date ne null and row_status_flag eq 704",
            orderby: "expiration_date asc",
            top: 5);

        Console.WriteLine("  Pages with earliest expiration dates:");
        foreach (var page in data["value"]!)
        {
            var exp = FormatDate(page["expiration_date"]);
            Console.WriteLine($"    {page["price_page_uid"]}: expires {exp}");
        }

        // -----------------------------------------------------------------
        // Example 5: Multiple orderby fields
        // -----------------------------------------------------------------
        Console.WriteLine("\n5. Multiple orderby fields:");
        Console.WriteLine(new string('-', 40));

        // Separate multiple orderby fields with commas.
        // Each field can specify asc or desc independently.
        data = await odata.QueryAsync(
            "price_page",
            select: "price_page_uid,supplier_id,description,effective_date",
            filter: "row_status_flag eq 704",
            orderby: "supplier_id asc,effective_date desc",
            top: 8);

        Console.WriteLine("  Pages ordered by supplier, then by date (newest first):");
        foreach (var page in data["value"]!)
        {
            var eff = FormatDate(page["effective_date"]);
            Console.WriteLine($"    Supplier {page["supplier_id"]}: {page["price_page_uid"]} ({eff})");
        }

        // -----------------------------------------------------------------
        // Example 6: Join-like query (related data from two tables)
        // -----------------------------------------------------------------
        Console.WriteLine("\n6. Getting related data (supplier for price page):");
        Console.WriteLine(new string('-', 40));

        // P21 OData doesn't support $expand (joins). To get related data,
        // query the first table, extract the foreign key, then query the second.

        // Step 1: Get a price page with a supplier_id
        data = await odata.QueryAsync(
            "price_page",
            select: "price_page_uid,description,supplier_id",
            filter: "row_status_flag eq 704",
            top: 1);

        var pages = data["value"]!.ToList();
        if (pages.Count > 0)
        {
            var firstPage = pages[0];
            var supplierId = firstPage["supplier_id"]?.Value<int>();
            Console.WriteLine($"  Price page: {firstPage["price_page_uid"]}");
            Console.WriteLine($"  Supplier ID: {supplierId}");

            // Step 2: Look up the supplier name using the foreign key
            if (supplierId.HasValue)
            {
                var supplierData = await odata.QueryAsync(
                    "supplier",
                    select: "supplier_id,supplier_name",
                    filter: $"supplier_id eq {supplierId.Value}");

                var suppliers = supplierData["value"]!.ToList();
                if (suppliers.Count > 0)
                {
                    var supplierName = suppliers[0]["supplier_name"]?.ToString() ?? "N/A";
                    Console.WriteLine($"  Supplier name: {supplierName}");
                }
            }
        }

        Console.WriteLine($"\n{new string('=', 50)}");
        Console.WriteLine("Complex query examples complete!");
    }

    /// <summary>
    /// Escape single quotes in OData string values.
    /// OData uses doubled single quotes: O'Brien becomes O''Brien
    /// </summary>
    public static string EscapeODataString(string value)
    {
        return value.Replace("'", "''");
    }

    /// <summary>
    /// Format a date token as YYYY-MM-DD, or "N/A" if null.
    /// </summary>
    private static string FormatDate(JToken? token)
    {
        var raw = token?.ToString();
        if (string.IsNullOrEmpty(raw)) return "N/A";
        // Take first 10 characters (YYYY-MM-DD) from ISO format
        return raw.Length >= 10 ? raw[..10] : raw;
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
