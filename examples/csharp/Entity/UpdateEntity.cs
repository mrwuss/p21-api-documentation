// Entity API - Update Entity
//
// Demonstrates updating an existing entity record.
// Mirrors: examples/python/entity/04_update_entity.py
//
// This example shows both approaches:
//   1. Raw HttpClient - full control, educational
//   2. P21Client.Entity wrapper - concise, recommended for production
//
// Update workflow:
//   1. GET /api/entity/{resource}/{key}           - Fetch existing record
//   2. Modify the fields you want to change
//   3. PUT /api/entity/{resource}/{key}           - Update with key in URL
//
// IMPORTANT: Updates use PUT (not POST). Include the composite key in
// the URL and the key fields in the body. Only changed fields need
// to be in the payload.

using System.Net.Http;
using System.Text;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using P21Examples.Common;

namespace P21Examples.Entity;

public static class UpdateEntity
{
    public static async Task RunAsync()
    {
        Console.WriteLine("Entity API - Update Entity");
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
        // Example 1: Get an existing customer - raw HttpClient
        // -----------------------------------------------------------------
        Console.WriteLine("\n1. Getting existing customer by composite key:");
        Console.WriteLine(new string('-', 50));

        // Customer composite key format: {CompanyId}_{CustomerId}
        // Example: ACME_10 means CompanyId=ACME, CustomerId=10
        var customerKey = "ACME_10";

        try
        {
            // GET /api/entity/customers/{compositeKey}
            var response = await http.GetAsync(
                $"{config.EntityUrl}/customers/{customerKey}");
            response.EnsureSuccessStatusCode();

            var json = await response.Content.ReadAsStringAsync();
            var customer = JObject.Parse(json);

            Console.WriteLine($"  Key:          {customerKey}");
            Console.WriteLine($"  CompanyId:    {customer["CompanyId"]}");
            Console.WriteLine($"  CustomerId:   {customer["CustomerId"]}");
            Console.WriteLine($"  CustomerName: {customer["CustomerName"]}");
            Console.WriteLine($"  CreditStatus: {customer["CreditStatus"]}");
            Console.WriteLine($"  Taxable:      {customer["Taxable"]}");
        }
        catch (HttpRequestException ex)
        {
            Console.WriteLine($"  Error: {ex.StatusCode} - {ex.Message}");
            Console.WriteLine("  Trying to list first available customer instead...");

            // Fall back to listing customers to find a valid key
            try
            {
                var entityApi = new EntityApi(http, config.EntityUrl);
                var result = await entityApi.ListAsync("customers");
                if (result is JArray arr && arr.Count > 0)
                {
                    var first = arr[0];
                    var companyId = first["CompanyId"]?.ToString() ?? "";
                    var customerId = first["CustomerId"]?.ToString() ?? "";
                    customerKey = $"{companyId}_{customerId}";
                    Console.WriteLine($"  Found customer: {customerKey}");
                    Console.WriteLine($"  CustomerName: {first["CustomerName"]}");
                }
            }
            catch (Exception listEx)
            {
                Console.WriteLine($"  Could not list customers: {listEx.Message}");
            }
        }

        // -----------------------------------------------------------------
        // Example 2: Get customer with extended properties - raw HttpClient
        // -----------------------------------------------------------------
        Console.WriteLine("\n2. Getting customer with extended properties:");
        Console.WriteLine(new string('-', 50));

        try
        {
            // The extendedproperties parameter populates nested objects
            // that are normally null. Use * for all, or a specific name.
            var response = await http.GetAsync(
                $"{config.EntityUrl}/customers/{customerKey}?extendedproperties=CustomerAddress");
            response.EnsureSuccessStatusCode();

            var json = await response.Content.ReadAsStringAsync();
            var customer = JObject.Parse(json);

            Console.WriteLine($"  Customer: {customer["CustomerName"]}");

            var address = customer["CustomerAddress"];
            if (address != null && address.Type != JTokenType.Null)
            {
                Console.WriteLine($"  Address:  {address["MailAddress1"]}");
                Console.WriteLine($"            {address["MailCity"]}, {address["MailState"]} {address["MailPostalCode"]}");
                Console.WriteLine($"  Phone:    {address["CentralPhoneNumber"]}");
            }
            else
            {
                Console.WriteLine("  Address:  (not available)");
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"  Error: {ex.Message}");
        }

        // -----------------------------------------------------------------
        // Example 3: Get customer with ALL extended properties - wrapper
        // -----------------------------------------------------------------
        Console.WriteLine("\n3. Getting customer with all extended properties (via wrapper):");
        Console.WriteLine(new string('-', 50));

        try
        {
            // The EntityApi.GetAsync wrapper accepts an optional extendedProperties parameter.
            // Use "*" for all nested objects.
            var entityApi = new EntityApi(http, config.EntityUrl);
            var customer = await entityApi.GetAsync("customers", customerKey, "*");

            Console.WriteLine($"  Customer: {customer["CustomerName"]}");

            // List which extended properties are populated vs null
            string[] extProps = ["CustomerAddress", "CustomerContacts",
                                 "CustomerShipTos", "CustomerSalesreps",
                                 "CustomerTerms", "CustomerPriceLibraries"];
            Console.WriteLine("  Extended properties:");
            foreach (var prop in extProps)
            {
                var value = customer[prop];
                var status = (value == null || value.Type == JTokenType.Null)
                    ? "null" : "populated";
                Console.WriteLine($"    {prop,-30} {status}");
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"  Error: {ex.Message}");
        }

        // -----------------------------------------------------------------
        // Example 4: Show update workflow (demonstration - no actual update)
        // -----------------------------------------------------------------
        Console.WriteLine("\n4. Update workflow (demonstration only):");
        Console.WriteLine(new string('-', 50));

        Console.WriteLine("  To update a customer, you would:");
        Console.WriteLine($"  1. Identify the composite key: {customerKey}");
        Console.WriteLine("  2. Build payload with key fields + changed fields:");
        Console.WriteLine();

        // Build a sample update payload
        var sampleUpdate = new JObject
        {
            ["CompanyId"] = "ACME",
            ["CustomerId"] = 10,
            ["CustomerName"] = "Updated Customer Name"
        };

        Console.WriteLine(sampleUpdate.ToString(Formatting.Indented));
        Console.WriteLine();
        Console.WriteLine($"  3. PUT to: /api/entity/customers/{customerKey}");

        // -----------------------------------------------------------------
        // Example 5: Show how to make the PUT request
        // -----------------------------------------------------------------
        Console.WriteLine("\n5. How to make the update request:");
        Console.WriteLine(new string('-', 50));

        Console.WriteLine("  // Using raw HttpClient:");
        Console.WriteLine("  var payload = new JObject");
        Console.WriteLine("  {");
        Console.WriteLine("      [\"CompanyId\"] = \"ACME\",");
        Console.WriteLine("      [\"CustomerId\"] = 10,");
        Console.WriteLine("      [\"CustomerName\"] = \"Updated Customer Name\"");
        Console.WriteLine("  };");
        Console.WriteLine("  var content = new StringContent(");
        Console.WriteLine("      payload.ToString(), Encoding.UTF8, \"application/json\");");
        Console.WriteLine("  var response = await http.PutAsync(");
        Console.WriteLine($"      $\"{{config.EntityUrl}}/customers/{customerKey}\", content);");
        Console.WriteLine();
        Console.WriteLine("  // Using EntityApi wrapper:");
        Console.WriteLine($"  var result = await entityApi.UpdateAsync(");
        Console.WriteLine($"      \"customers\", \"{customerKey}\", payload);");

        // -----------------------------------------------------------------
        // Example 6: Get a vendor by composite key
        // -----------------------------------------------------------------
        Console.WriteLine("\n6. Get vendor by composite key:");
        Console.WriteLine(new string('-', 50));

        try
        {
            // Vendors also use composite keys: {CompanyId}_{VendorId}
            // Note: VendorId != supplier_id (different database tables)
            var entityApi = new EntityApi(http, config.EntityUrl);
            var vendors = await entityApi.ListAsync("vendors");

            if (vendors is JArray arr && arr.Count > 0)
            {
                var first = arr[0];
                var companyId = first["CompanyId"]?.ToString() ?? "";
                var vendorId = first["VendorId"]?.ToString() ?? "";
                var vendorKey = $"{companyId}_{vendorId}";

                Console.WriteLine($"  Vendor key:  {vendorKey}");
                Console.WriteLine($"  VendorName:  {first["VendorName"]}");
                Console.WriteLine();
                Console.WriteLine("  Vendor update would use:");
                Console.WriteLine($"  PUT /api/entity/vendors/{vendorKey}");
                Console.WriteLine("  with CompanyId and VendorId in the body");
            }
            else
            {
                Console.WriteLine("  No vendors found");
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"  Error: {ex.Message}");
        }

        // -----------------------------------------------------------------
        // Example 7: Delete via update (soft delete)
        // -----------------------------------------------------------------
        Console.WriteLine("\n7. Delete workflow (via PUT with Delete flag):");
        Console.WriteLine(new string('-', 50));

        Console.WriteLine("  The Entity API uses a soft-delete pattern.");
        Console.WriteLine("  Set the Delete field to true in a PUT request:");
        Console.WriteLine();

        var deletePayload = new JObject
        {
            ["CompanyId"] = "ACME",
            ["CustomerId"] = 10,
            ["Delete"] = true
        };

        Console.WriteLine(deletePayload.ToString(Formatting.Indented));
        Console.WriteLine();
        Console.WriteLine("  PUT /api/entity/customers/ACME_10");
        Console.WriteLine("  (There is no dedicated DELETE HTTP method for entities)");

        // -----------------------------------------------------------------
        // Example 8: Important considerations
        // -----------------------------------------------------------------
        Console.WriteLine("\n8. Important considerations:");
        Console.WriteLine(new string('-', 50));

        Console.WriteLine("  - Updates use PUT with the composite key in the URL");
        Console.WriteLine("  - Include key fields (CompanyId + CustomerId) in the body");
        Console.WriteLine("  - Only changed fields need to be in the payload");
        Console.WriteLine("  - Fields not included remain unchanged");
        Console.WriteLine("  - Some fields may be read-only (API returns error)");
        Console.WriteLine("  - Validation errors are returned in the response body");
        Console.WriteLine("  - Addresses cannot be updated via Entity API (use Interactive)");
        Console.WriteLine("  - VendorId is not the same as supplier_id (different tables)");

        // -----------------------------------------------------------------
        // Summary
        // -----------------------------------------------------------------
        Console.WriteLine($"\n{new string('=', 60)}");
        Console.WriteLine("Update entity examples complete!");
        Console.WriteLine("\nKey points:");
        Console.WriteLine("- PUT /api/entity/{resource}/{key} for updates");
        Console.WriteLine("- POST /api/entity/{resource} for creates (see CreateEntity)");
        Console.WriteLine("- Composite keys: {CompanyId}_{Id} for customers/vendors");
        Console.WriteLine("- Simple numeric IDs for contacts/addresses");
        Console.WriteLine("- Use extendedproperties=* to see nested/related data");
        Console.WriteLine("- Delete via PUT with Delete=true (no HTTP DELETE method)");
    }
}
