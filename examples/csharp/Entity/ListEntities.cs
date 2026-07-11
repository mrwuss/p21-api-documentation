// Entity API - List Available Entities
//
// Demonstrates entity discovery: ping health checks, listing records,
// and retrieving new-record templates.
// Mirrors: examples/python/entity/01_list_entities.py
//
// This example shows both approaches:
//   1. Raw HttpClient - full control, educational
//   2. P21Client.Entity wrapper - concise, recommended for production
//
// IMPORTANT: /api/entity/ is the 4-entity surface (customers, vendors,
// contacts, addresses). It is one part of Epicor's broader "Entity API"
// umbrella — other REST surfaces exist too (e.g., /api/sales/orders exists
// and works). See docs/05-Entity-API.md for the full taxonomy.

using System.Net.Http;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using P21Examples.Common;

namespace P21Examples.Entity;

public static class ListEntities
{
    public static async Task RunAsync()
    {
        Console.WriteLine("Entity API - List Available Entities");
        Console.WriteLine(new string('=', 60));

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
        // Allow automatic redirect following (Entity list endpoints return 307)
        handler.AllowAutoRedirect = true;

        using var http = new HttpClient(handler) { Timeout = TimeSpan.FromSeconds(30) };

        // Authenticate
        var token = await P21Auth.GetTokenAsync(http, config);
        P21Auth.SetAuthHeaders(http, token.AccessToken);

        // -----------------------------------------------------------------
        // Example 1: Ping each entity endpoint - raw HttpClient
        // -----------------------------------------------------------------
        Console.WriteLine("\n1. Health check (ping) for each entity:");
        Console.WriteLine(new string('-', 50));

        // These are the only 4 entities available via /api/entity/
        var entities = new[]
        {
            ("Customers", "customers"),
            ("Vendors",   "vendors"),
            ("Contacts",  "contacts"),
            ("Addresses", "addresses"),
        };

        foreach (var (name, resource) in entities)
        {
            try
            {
                // GET /api/entity/{resource}/ping
                var response = await http.GetAsync($"{config.EntityUrl}/{resource}/ping");

                if (response.IsSuccessStatusCode)
                {
                    var json = await response.Content.ReadAsStringAsync();
                    var data = JObject.Parse(json);
                    var message = data["ResponseMessage"]?.ToString() ?? "N/A";
                    Console.WriteLine($"  [OK] {name,-12} /api/entity/{resource}/ping -> {message}");
                }
                else
                {
                    Console.WriteLine($"  [--] {name,-12} HTTP {(int)response.StatusCode}");
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"  [--] {name,-12} Error: {ex.Message[..Math.Min(50, ex.Message.Length)]}");
            }
        }

        // -----------------------------------------------------------------
        // Example 2: Get a new customer template - raw HttpClient
        // -----------------------------------------------------------------
        Console.WriteLine("\n2. Getting new customer template:");
        Console.WriteLine(new string('-', 50));

        try
        {
            // GET /api/entity/customers/new returns a blank template with all fields
            // and their default values. Use this to discover required fields.
            var response = await http.GetAsync($"{config.EntityUrl}/customers/new");
            response.EnsureSuccessStatusCode();

            var json = await response.Content.ReadAsStringAsync();
            var template = JObject.Parse(json);

            Console.WriteLine($"  Template has {template.Properties().Count()} fields");
            Console.WriteLine("\n  Key fields from template:");

            // Show some important fields
            string[] important = ["CompanyId", "CustomerId", "CustomerName",
                                  "SalesrepId", "TermsId", "CreditStatus", "Taxable"];
            foreach (var field in important)
            {
                var value = template[field];
                var display = value == null || value.Type == JTokenType.Null
                    ? "(null)"
                    : value.ToString().Length > 30
                        ? value.ToString()[..30]
                        : value.ToString();

                if (string.IsNullOrEmpty(display)) display = "(empty string)";
                Console.WriteLine($"    {field,-20} {display}");
            }

            // Note: addresses do NOT have a /new endpoint (returns 500)
            Console.WriteLine("\n  Note: GET /api/entity/addresses/new returns 500");
            Console.WriteLine("  (Address entity does not support templates by design)");
        }
        catch (HttpRequestException ex)
        {
            Console.WriteLine($"  Error: {ex.Message}");
        }

        // -----------------------------------------------------------------
        // Example 3: List first 3 customers - using P21Client.Entity wrapper
        // -----------------------------------------------------------------
        Console.WriteLine("\n3. Getting sample customer data (via EntityApi wrapper):");
        Console.WriteLine(new string('-', 50));

        try
        {
            // The EntityApi wrapper handles URL construction and JSON parsing.
            // ListAsync adds a trailing slash to avoid the 307 redirect.
            var entityApi = new EntityApi(http, config.EntityUrl);
            var customers = await entityApi.ListAsync("customers");

            // The list endpoint returns a JArray of customer objects
            if (customers is JArray arr && arr.Count > 0)
            {
                var count = Math.Min(3, arr.Count);
                Console.WriteLine($"  Showing first {count} of {arr.Count} customers:");

                for (var i = 0; i < count; i++)
                {
                    var c = arr[i];
                    var companyId = c["CompanyId"]?.ToString() ?? "N/A";
                    var customerId = c["CustomerId"]?.ToString() ?? "N/A";
                    var name = c["CustomerName"]?.ToString() ?? "Unknown";
                    if (name.Length > 40) name = name[..40];

                    // Entity API uses composite key: {CompanyId}_{CustomerId}
                    Console.WriteLine($"    {companyId}_{customerId}: {name}");
                }
            }
            else
            {
                Console.WriteLine("  No customers found");
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"  Error: {ex.Message}");
        }

        // -----------------------------------------------------------------
        // Example 4: List contacts - raw HttpClient with redirect handling
        // -----------------------------------------------------------------
        Console.WriteLine("\n4. Getting sample contact data (raw HttpClient):");
        Console.WriteLine(new string('-', 50));

        try
        {
            // List endpoints return 307 redirect if no trailing slash.
            // We set AllowAutoRedirect = true on the handler, so this is handled.
            // Alternatively, always include the trailing slash in the URL.
            var response = await http.GetAsync($"{config.EntityUrl}/contacts/");
            response.EnsureSuccessStatusCode();

            var json = await response.Content.ReadAsStringAsync();
            var contacts = JArray.Parse(json);

            var count = Math.Min(3, contacts.Count);
            Console.WriteLine($"  Showing first {count} of {contacts.Count} contacts:");

            for (var i = 0; i < count; i++)
            {
                var c = contacts[i];
                var id = c["Id"]?.ToString() ?? "N/A";
                var first = c["FirstName"]?.ToString() ?? "";
                var last = c["LastName"]?.ToString() ?? "";
                var email = c["EmailAddress"]?.ToString();
                var emailDisplay = string.IsNullOrEmpty(email) ? "(no email)" : email;

                // Contacts use simple numeric IDs (not composite keys)
                Console.WriteLine($"    Contact {id}: {first} {last} - {emailDisplay}");
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"  Error: {ex.Message}");
        }

        // -----------------------------------------------------------------
        // Summary
        // -----------------------------------------------------------------
        Console.WriteLine($"\n{new string('=', 60)}");
        Console.WriteLine("Entity discovery complete!");
        Console.WriteLine("\nEntity API URL pattern:");
        Console.WriteLine("  Base: /api/entity/{resource}");
        Console.WriteLine("  GET    /api/entity/{resource}/ping        - Health check");
        Console.WriteLine("  GET    /api/entity/{resource}/new         - Get template");
        Console.WriteLine("  GET    /api/entity/{resource}/            - List all (trailing slash!)");
        Console.WriteLine("  GET    /api/entity/{resource}/{key}       - Get one");
        Console.WriteLine("  POST   /api/entity/{resource}             - Create");
        Console.WriteLine("  PUT    /api/entity/{resource}/{key}       - Update");
        Console.WriteLine("\nAvailable entities: customers, vendors, contacts, addresses");
        Console.WriteLine("Key format: customers/vendors use {CompanyId}_{Id} (e.g., ACME_10)");
        Console.WriteLine("            contacts/addresses use simple numeric ID (e.g., 1)");
    }
}
