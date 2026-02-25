// Entity API - Create Entity
//
// Demonstrates creating a new entity record.
// Mirrors: scripts/entity/03_create_entity.py
//
// This example shows both approaches:
//   1. Raw HttpClient - full control, educational
//   2. P21Client.Entity wrapper - concise, recommended for production
//
// Create workflow:
//   1. GET /api/entity/{resource}/new  - Get a blank template with defaults
//   2. Fill in required fields
//   3. POST /api/entity/{resource}     - Create (no key field = insert)
//
// IMPORTANT: The absence of the key field (e.g., CustomerId = null)
// tells the API to INSERT a new record. If the key field is present,
// the API treats it as an UPDATE.

using System.Net.Http;
using System.Text;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using P21Examples.Common;

namespace P21Examples.Entity;

public static class CreateEntity
{
    public static async Task RunAsync()
    {
        Console.WriteLine("Entity API - Create Entity");
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
        // Example 1: Get a new customer template - raw HttpClient
        // -----------------------------------------------------------------
        Console.WriteLine("\n1. Getting new customer template:");
        Console.WriteLine(new string('-', 50));

        JObject? template = null;
        try
        {
            // GET /api/entity/customers/new returns a blank template
            // with all fields and their default values.
            var response = await http.GetAsync($"{config.EntityUrl}/customers/new");
            response.EnsureSuccessStatusCode();

            var json = await response.Content.ReadAsStringAsync();
            template = JObject.Parse(json);

            Console.WriteLine($"  Template has {template.Properties().Count()} fields");
            Console.WriteLine("\n  Key required fields:");

            // Show some important fields from the template
            string[] important = ["CompanyId", "CustomerId", "CustomerName",
                                  "SalesrepId", "TermsId", "CodRequiredFlag", "Taxable"];
            foreach (var field in important)
            {
                var value = template[field];
                string display;
                if (value == null || value.Type == JTokenType.Null)
                    display = "(null)";
                else if (string.IsNullOrEmpty(value.ToString()))
                    display = "(empty string)";
                else
                    display = value.ToString();
                Console.WriteLine($"    {field,-25} {display}");
            }

            Console.WriteLine("\n  Note: CustomerId is null in the template.");
            Console.WriteLine("  Leaving it null signals INSERT (create new record).");
        }
        catch (HttpRequestException ex)
        {
            Console.WriteLine($"  Error: {ex.Message}");
            return;
        }

        // -----------------------------------------------------------------
        // Example 2: Get a new vendor template - using EntityApi wrapper
        // -----------------------------------------------------------------
        Console.WriteLine("\n2. Getting new vendor template (via EntityApi wrapper):");
        Console.WriteLine(new string('-', 50));

        try
        {
            var entityApi = new EntityApi(http, config.EntityUrl);
            var vendorTemplate = await entityApi.GetTemplateAsync("vendors");

            Console.WriteLine($"  Vendor template has {vendorTemplate.Properties().Count()} fields");
            Console.WriteLine("\n  Key fields:");

            string[] vendorFields = ["CompanyId", "VendorId", "VendorName",
                                     "DefaultTermsId", "CurrencyId"];
            foreach (var field in vendorFields)
            {
                var value = vendorTemplate[field];
                string display;
                if (value == null || value.Type == JTokenType.Null)
                    display = "(null)";
                else if (string.IsNullOrEmpty(value.ToString()))
                    display = "(empty string)";
                else
                    display = value.ToString();
                Console.WriteLine($"    {field,-25} {display}");
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"  Error: {ex.Message}");
        }

        // -----------------------------------------------------------------
        // Example 3: Get a new contact template
        // -----------------------------------------------------------------
        Console.WriteLine("\n3. Getting new contact template:");
        Console.WriteLine(new string('-', 50));

        try
        {
            var entityApi = new EntityApi(http, config.EntityUrl);
            var contactTemplate = await entityApi.GetTemplateAsync("contacts");

            Console.WriteLine($"  Contact template has {contactTemplate.Properties().Count()} fields");
            Console.WriteLine("\n  Key fields:");

            string[] contactFields = ["Id", "FirstName", "LastName", "Title",
                                      "EmailAddress", "DirectPhone"];
            foreach (var field in contactFields)
            {
                var value = contactTemplate[field];
                string display;
                if (value == null || value.Type == JTokenType.Null)
                    display = "(null)";
                else if (string.IsNullOrEmpty(value.ToString()))
                    display = "(empty string)";
                else
                    display = value.ToString();
                Console.WriteLine($"    {field,-25} {display}");
            }

            Console.WriteLine("\n  Note: Contacts use simple numeric IDs, not composite keys.");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"  Error: {ex.Message}");
        }

        // -----------------------------------------------------------------
        // Example 4: Show create workflow (demonstration only - no actual create)
        // -----------------------------------------------------------------
        Console.WriteLine("\n4. Create workflow (demonstration only):");
        Console.WriteLine(new string('-', 50));

        Console.WriteLine("  To create a customer, you would:");
        Console.WriteLine("  1. Get template:  GET /api/entity/customers/new");
        Console.WriteLine("  2. Fill required fields:");
        Console.WriteLine("     template[\"CompanyId\"]    = \"ACME\"");
        Console.WriteLine("     template[\"CustomerName\"] = \"New Customer Inc.\"");
        Console.WriteLine("     template[\"SalesrepId\"]   = \"1100\"");
        Console.WriteLine("     template[\"TermsId\"]      = \"1\"");
        Console.WriteLine("     template[\"Taxable\"]      = \"Y\"");
        Console.WriteLine("  3. Leave CustomerId as null (signals INSERT)");
        Console.WriteLine("  4. POST to: /api/entity/customers");

        // -----------------------------------------------------------------
        // Example 5: Show the payload structure
        // -----------------------------------------------------------------
        Console.WriteLine("\n5. Sample create payload:");
        Console.WriteLine(new string('-', 50));

        // Build a sample payload showing what a create request looks like.
        // In production, start from the /new template and fill fields.
        var samplePayload = new JObject
        {
            ["CompanyId"] = "ACME",
            // CustomerId is intentionally omitted (null = INSERT)
            ["CustomerName"] = "New Customer Inc.",
            ["SalesrepId"] = "1100",
            ["TermsId"] = "1",
            ["CodRequiredFlag"] = "N",
            ["Taxable"] = "Y"
        };

        Console.WriteLine(samplePayload.ToString(Formatting.Indented));

        Console.WriteLine("\n  Note: CustomerId is NOT included = new record (INSERT)");
        Console.WriteLine("        If CustomerId IS included = update (see UpdateEntity)");

        // -----------------------------------------------------------------
        // Example 6: Show how to make the POST request
        // -----------------------------------------------------------------
        Console.WriteLine("\n6. How to make the create request:");
        Console.WriteLine(new string('-', 50));

        Console.WriteLine("  // Using raw HttpClient:");
        Console.WriteLine("  var content = new StringContent(");
        Console.WriteLine("      JsonConvert.SerializeObject(payload),");
        Console.WriteLine("      Encoding.UTF8, \"application/json\");");
        Console.WriteLine("  var response = await http.PostAsync(");
        Console.WriteLine("      $\"{config.EntityUrl}/customers\", content);");
        Console.WriteLine();
        Console.WriteLine("  // Using EntityApi wrapper:");
        Console.WriteLine("  var result = await entityApi.CreateAsync(\"customers\", payload);");
        Console.WriteLine();
        Console.WriteLine("  On success, the API returns the created record with");
        Console.WriteLine("  the system-generated CustomerId filled in.");

        // -----------------------------------------------------------------
        // Example 7: Address limitations
        // -----------------------------------------------------------------
        Console.WriteLine("\n7. Address entity limitations:");
        Console.WriteLine(new string('-', 50));

        Console.WriteLine("  The Address entity has a reduced API surface:");
        Console.WriteLine("  - No /new template endpoint (returns 500)");
        Console.WriteLine("  - No PUT for updates (only POST for create)");
        Console.WriteLine("  - To create an address, POST directly with field values");
        Console.WriteLine("  - To update an address, use Interactive API or direct SQL");

        // -----------------------------------------------------------------
        // Summary
        // -----------------------------------------------------------------
        Console.WriteLine($"\n{new string('=', 60)}");
        Console.WriteLine("Create entity examples complete!");
        Console.WriteLine("\nKey points:");
        Console.WriteLine("- GET /api/entity/{resource}/new to get template with defaults");
        Console.WriteLine("- Omit key field (e.g., CustomerId) for INSERT");
        Console.WriteLine("- Include key field for UPDATE (use PUT, see UpdateEntity)");
        Console.WriteLine("- Only include fields you want to set");
        Console.WriteLine("- Addresses: no /new template, no PUT update");
    }
}
