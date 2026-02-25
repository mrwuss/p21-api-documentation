// Entity API - Query Entities
//
// Demonstrates querying entities with filters using the $query parameter.
// Mirrors: scripts/entity/02_query_entity.py
//
// This example shows both approaches:
//   1. Raw HttpClient - full control, educational
//   2. P21Client.Entity wrapper - concise, recommended for production
//
// IMPORTANT: The Entity API uses $query (NOT $filter like OData).
// Supported operators: eq, ne, gt, ge, lt, le, and, or, not
// Supported functions: startswith(), endswith(), substringof()

using System.Net.Http;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using P21Examples.Common;

namespace P21Examples.Entity;

public static class QueryEntity
{
    /// <summary>
    /// Query an entity with a $query filter expression using raw HttpClient.
    /// </summary>
    private static async Task<JArray> QueryAsync(
        HttpClient http, string entityUrl, string resource,
        string query, int? top = null)
    {
        // Build URL with trailing slash (avoids 307 redirect) and $query parameter
        var url = $"{entityUrl}/{resource}/?$query={Uri.EscapeDataString(query)}";
        if (top.HasValue)
            url += $"&$top={top.Value}";

        var response = await http.GetAsync(url);
        response.EnsureSuccessStatusCode();
        var json = await response.Content.ReadAsStringAsync();
        return JArray.Parse(json);
    }

    public static async Task RunAsync()
    {
        Console.WriteLine("Entity API - Query Entities");
        Console.WriteLine(new string('=', 60));

        // Load configuration and authenticate
        var config = P21Config.FromEnvironment();
        Console.WriteLine($"Server: {config.BaseUrl}");

        using var handler = new HttpClientHandler();
        if (!config.VerifySsl)
        {
            handler.ServerCertificateCustomValidationCallback =
                HttpClientHandler.DangerousAcceptAnyServerCertificateValidator;
        }
        handler.AllowAutoRedirect = true;

        using var http = new HttpClient(handler) { Timeout = TimeSpan.FromSeconds(30) };

        var token = await P21Auth.GetTokenAsync(http, config);
        P21Auth.SetAuthHeaders(http, token.AccessToken);

        // -----------------------------------------------------------------
        // Example 1: Simple equality filter - raw HttpClient
        // -----------------------------------------------------------------
        Console.WriteLine("\n1. Equality filter - customers by company:");
        Console.WriteLine(new string('-', 50));

        try
        {
            // $query uses OData-like syntax: FieldName operator Value
            // String values must be quoted with single quotes
            var customers = await QueryAsync(
                http, config.EntityUrl, "customers",
                "CompanyId eq 'ACME'", top: 5);

            Console.WriteLine($"  Found {customers.Count} customer(s) in company ACME:");
            foreach (var c in customers.Take(5))
            {
                var id = c["CustomerId"]?.ToString() ?? "N/A";
                var name = c["CustomerName"]?.ToString() ?? "Unknown";
                if (name.Length > 35) name = name[..35];
                Console.WriteLine($"    ACME_{id}: {name}");
            }
        }
        catch (HttpRequestException ex)
        {
            Console.WriteLine($"  Error: {ex.StatusCode} - {ex.Message}");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"  Error: {ex.Message}");
        }

        // -----------------------------------------------------------------
        // Example 2: Comparison operator - raw HttpClient
        // -----------------------------------------------------------------
        Console.WriteLine("\n2. Comparison filter (CreditLimit gt 10000):");
        Console.WriteLine(new string('-', 50));

        try
        {
            // Numeric comparisons do not need quotes around the value
            var customers = await QueryAsync(
                http, config.EntityUrl, "customers",
                "CreditLimit gt 10000", top: 5);

            Console.WriteLine($"  Found {customers.Count} customer(s) with high credit:");
            foreach (var c in customers.Take(5))
            {
                var companyId = c["CompanyId"]?.ToString() ?? "N/A";
                var id = c["CustomerId"]?.ToString() ?? "N/A";
                var name = c["CustomerName"]?.ToString() ?? "Unknown";
                if (name.Length > 30) name = name[..30];
                var limit = c["CreditLimit"]?.Value<decimal>() ?? 0m;
                Console.WriteLine($"    {companyId}_{id}: {name} (${limit:N2})");
            }
        }
        catch (HttpRequestException ex)
        {
            Console.WriteLine($"  Error: {ex.StatusCode} - {ex.Message}");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"  Error: {ex.Message}");
        }

        // -----------------------------------------------------------------
        // Example 3: String function (startswith) - using EntityApi wrapper
        // -----------------------------------------------------------------
        Console.WriteLine("\n3. String function - startswith (via EntityApi wrapper):");
        Console.WriteLine(new string('-', 50));

        try
        {
            // The EntityApi.ListAsync wrapper accepts an optional $query string
            // and handles URL encoding, trailing slashes, and JSON parsing.
            var entityApi = new EntityApi(http, config.EntityUrl);
            var result = await entityApi.ListAsync(
                "customers", "startswith(CustomerName, 'ABC')");

            if (result is JArray arr)
            {
                Console.WriteLine($"  Found {arr.Count} customer(s) starting with 'ABC':");
                foreach (var c in arr.Take(5))
                {
                    var companyId = c["CompanyId"]?.ToString() ?? "N/A";
                    var id = c["CustomerId"]?.ToString() ?? "N/A";
                    var name = c["CustomerName"]?.ToString() ?? "Unknown";
                    if (name.Length > 40) name = name[..40];
                    Console.WriteLine($"    {companyId}_{id}: {name}");
                }
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"  Error: {ex.Message}");
        }

        // -----------------------------------------------------------------
        // Example 4: Logical AND - raw HttpClient
        // -----------------------------------------------------------------
        Console.WriteLine("\n4. Logical AND (CompanyId and CreditLimit):");
        Console.WriteLine(new string('-', 50));

        try
        {
            // Combine conditions with 'and' / 'or' operators
            var customers = await QueryAsync(
                http, config.EntityUrl, "customers",
                "CompanyId eq 'ACME' and CreditLimit gt 5000", top: 5);

            Console.WriteLine($"  Found {customers.Count} ACME customer(s) with credit > $5000:");
            foreach (var c in customers.Take(5))
            {
                var id = c["CustomerId"]?.ToString() ?? "N/A";
                var name = c["CustomerName"]?.ToString() ?? "Unknown";
                if (name.Length > 30) name = name[..30];
                var limit = c["CreditLimit"]?.Value<decimal>() ?? 0m;
                Console.WriteLine($"    ACME_{id}: {name} (${limit:N2})");
            }
        }
        catch (HttpRequestException ex)
        {
            Console.WriteLine($"  Error: {ex.StatusCode} - {ex.Message}");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"  Error: {ex.Message}");
        }

        // -----------------------------------------------------------------
        // Example 5: Query vendors (different entity) - raw HttpClient
        // -----------------------------------------------------------------
        Console.WriteLine("\n5. Query vendors - startswith:");
        Console.WriteLine(new string('-', 50));

        try
        {
            var vendors = await QueryAsync(
                http, config.EntityUrl, "vendors",
                "startswith(VendorName, 'ABC')", top: 5);

            Console.WriteLine($"  Found {vendors.Count} vendor(s) starting with 'ABC':");
            foreach (var v in vendors.Take(5))
            {
                var companyId = v["CompanyId"]?.ToString() ?? "N/A";
                var vendorId = v["VendorId"]?.ToString() ?? "N/A";
                var name = v["VendorName"]?.ToString() ?? "Unknown";
                if (name.Length > 40) name = name[..40];

                // Vendors also use composite keys: {CompanyId}_{VendorId}
                Console.WriteLine($"    {companyId}_{vendorId}: {name}");
            }
        }
        catch (HttpRequestException ex)
        {
            Console.WriteLine($"  Error: {ex.StatusCode} - {ex.Message}");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"  Error: {ex.Message}");
        }

        // -----------------------------------------------------------------
        // Example 6: Query contacts (simple ID entity) - raw HttpClient
        // -----------------------------------------------------------------
        Console.WriteLine("\n6. Query contacts - substringof:");
        Console.WriteLine(new string('-', 50));

        try
        {
            // substringof checks if a substring exists within a field
            // Syntax: substringof('needle', FieldName)
            var contacts = await QueryAsync(
                http, config.EntityUrl, "contacts",
                "substringof('John', FirstName)", top: 5);

            Console.WriteLine($"  Found {contacts.Count} contact(s) with 'John' in first name:");
            foreach (var c in contacts.Take(5))
            {
                var id = c["Id"]?.ToString() ?? "N/A";
                var first = c["FirstName"]?.ToString() ?? "";
                var last = c["LastName"]?.ToString() ?? "";
                Console.WriteLine($"    Contact {id}: {first} {last}");
            }
        }
        catch (HttpRequestException ex)
        {
            Console.WriteLine($"  Error: {ex.StatusCode} - {ex.Message}");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"  Error: {ex.Message}");
        }

        // -----------------------------------------------------------------
        // Summary
        // -----------------------------------------------------------------
        Console.WriteLine($"\n{new string('=', 60)}");
        Console.WriteLine("Query examples complete!");
        Console.WriteLine("\nSupported $query operators:");
        Console.WriteLine("  Comparison: eq, ne, gt, ge, lt, le");
        Console.WriteLine("  Logical:    and, or, not");
        Console.WriteLine("  String:     startswith(Field, 'value')");
        Console.WriteLine("              endswith(Field, 'value')");
        Console.WriteLine("              substringof('value', Field)");
        Console.WriteLine("\nRemember: Entity API uses $query, NOT $filter (OData).");
        Console.WriteLine("List endpoints need trailing slash to avoid 307 redirect.");
    }
}
