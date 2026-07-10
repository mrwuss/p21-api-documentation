// OData API - Basic Query Example
//
// Demonstrates simple table queries with field selection.
// Mirrors: examples/python/odata/01_basic_query.py
//
// This example shows both approaches:
//   1. Raw HttpClient — full control, educational
//   2. P21Client.OData wrapper — concise, recommended for production

using System.Net.Http;
using Newtonsoft.Json.Linq;
using P21Examples.Common;

namespace P21Examples.OData;

public static class BasicQuery
{
    public static async Task RunAsync()
    {
        Console.WriteLine("OData API - Basic Query Example");
        Console.WriteLine(new string('=', 50));

        // Load configuration and authenticate
        var config = P21Config.FromEnvironment();
        Console.WriteLine($"Server: {config.BaseUrl}");

        // Create an HttpClient that skips SSL verification (common for dev/test P21 servers)
        using var handler = new HttpClientHandler();
        if (!config.VerifySsl)
        {
            handler.ServerCertificateCustomValidationCallback =
                HttpClientHandler.DangerousAcceptAnyServerCertificateValidator;
        }
        using var http = new HttpClient(handler) { Timeout = TimeSpan.FromSeconds(30) };

        // Authenticate — get an access token
        var token = await P21Auth.GetTokenAsync(http, config);
        P21Auth.SetAuthHeaders(http, token.AccessToken);

        // -----------------------------------------------------------------
        // Example 1: Query suppliers (first 5) — raw HttpClient
        // -----------------------------------------------------------------
        Console.WriteLine("\n1. Query suppliers (first 5):");
        Console.WriteLine(new string('-', 30));

        // Build the OData URL with query parameters.
        // P21 OData endpoint: {BaseUrl}/odataservice/odata/table/{tableName}
        var url = $"{config.ODataUrl}/table/supplier"
            + "?$top=5"
            + "&$select=supplier_id,supplier_name"
            + "&$orderby=supplier_name";

        var response = await http.GetAsync(url);
        response.EnsureSuccessStatusCode();
        var json = await response.Content.ReadAsStringAsync();
        var data = JObject.Parse(json);

        // OData responses wrap rows in a "value" array
        foreach (var supplier in data["value"]!)
        {
            Console.WriteLine($"  {supplier["supplier_id"]}: {supplier["supplier_name"]}");
        }

        // -----------------------------------------------------------------
        // Example 2: Query product groups — using P21Client wrapper
        // -----------------------------------------------------------------
        Console.WriteLine("\n2. Query product groups (first 5):");
        Console.WriteLine(new string('-', 30));

        // The ODataApi wrapper builds the URL and parses the response for you.
        // Note: we reuse the same HttpClient that's already authenticated.
        var odata = new ODataApi(http, config.ODataUrl);

        var groupData = await odata.QueryAsync(
            "product_group",
            select: "product_group_id,product_group_desc",
            orderby: "product_group_id",
            top: 5);

        foreach (var group in groupData["value"]!)
        {
            var desc = group["product_group_desc"]?.ToString() ?? "N/A";
            Console.WriteLine($"  {group["product_group_id"]}: {desc}");
        }

        // -----------------------------------------------------------------
        // Example 3: Query with $count — raw HttpClient
        // -----------------------------------------------------------------
        Console.WriteLine("\n3. Query price pages with count:");
        Console.WriteLine(new string('-', 30));

        // $count=true adds an "@odata.count" field with the total record count,
        // regardless of $top. Useful for building pagination UI.
        url = $"{config.ODataUrl}/table/price_page"
            + "?$top=3"
            + "&$count=true"
            + "&$select=price_page_uid,description";

        response = await http.GetAsync(url);
        response.EnsureSuccessStatusCode();
        json = await response.Content.ReadAsStringAsync();
        data = JObject.Parse(json);

        var totalCount = data["@odata.count"]?.ToString() ?? "N/A";
        Console.WriteLine($"  Total price pages in database: {totalCount}");
        Console.WriteLine("  First 3 records:");
        foreach (var page in data["value"]!)
        {
            var desc = page["description"]?.ToString() ?? "N/A";
            // Truncate long descriptions to 50 characters
            if (desc.Length > 50) desc = desc[..50];
            Console.WriteLine($"    {page["price_page_uid"]}: {desc}");
        }

        Console.WriteLine($"\n{new string('=', 50)}");
        Console.WriteLine("Basic query examples complete!");
    }
}
