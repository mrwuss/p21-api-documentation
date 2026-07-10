// Transaction API - List Available Services
//
// Discovers all services available through the Transaction API.
// Mirrors: examples/python/transaction/01_list_services.py
//
// The Transaction API uses a UI Server URL (different from the base URL).
// Services are discovered via GET /api/v2/services.

using Newtonsoft.Json.Linq;
using P21Examples.Common;

namespace P21Examples.Transaction;

/// <summary>
/// Lists all services available through the P21 Transaction API.
/// Uses both P21Client (convenience) and raw HttpClient (educational).
/// </summary>
public static class ListServices
{
    // Well-known services to check for availability
    private static readonly string[] CommonServices =
    {
        "Order", "Invoice", "Customer", "Supplier", "SalesPricePage",
        "PurchaseOrder", "InventoryMaster", "Task"
    };

    public static async Task RunAsync()
    {
        Console.WriteLine("Transaction API - List Available Services");
        Console.WriteLine(new string('=', 50));

        // -----------------------------------------------------------------
        // Approach 1: Using P21Client (recommended for most use cases)
        // -----------------------------------------------------------------
        Console.WriteLine("\n--- Using P21Client ---");

        using var client = await P21Client.CreateAsync();

        Console.WriteLine("\nFetching available services...");
        Console.WriteLine(new string('-', 40));

        // ListServicesAsync returns a JArray of service objects
        var services = await client.Transaction.ListServicesAsync();

        Console.WriteLine($"\nFound {services.Count} services:\n");

        // Group by first letter for readability
        var currentLetter = "";
        var sortedServices = services
            .Select(s => s is JObject obj ? obj["Name"]?.ToString() ?? s.ToString() : s.ToString())
            .Where(name => !string.IsNullOrEmpty(name))
            .OrderBy(name => name)
            .ToList();

        foreach (var name in sortedServices)
        {
            var firstLetter = name[..1].ToUpper();

            if (firstLetter != currentLetter)
            {
                currentLetter = firstLetter;
                Console.WriteLine($"\n  [{currentLetter}]");
            }

            Console.WriteLine($"    {name}");
        }

        // Check which common services are available
        Console.WriteLine("\n" + new string('=', 50));
        Console.WriteLine("Common Services:");
        Console.WriteLine(new string('-', 40));

        var serviceNames = new HashSet<string>(sortedServices, StringComparer.OrdinalIgnoreCase);

        foreach (var svc in CommonServices)
        {
            var status = serviceNames.Contains(svc) ? "Available" : "Not found";
            Console.WriteLine($"  {svc}: {status}");
        }

        // -----------------------------------------------------------------
        // Approach 2: Raw HttpClient (educational — shows exact HTTP calls)
        // -----------------------------------------------------------------
        Console.WriteLine("\n\n--- Raw HttpClient Approach ---");
        Console.WriteLine("(Showing the HTTP mechanics behind P21Client)");

        var config = P21Config.FromEnvironment();

        // Create an HttpClient that skips SSL verification (dev environments)
        var handler = new HttpClientHandler();
        if (!config.VerifySsl)
        {
            handler.ServerCertificateCustomValidationCallback =
                HttpClientHandler.DangerousAcceptAnyServerCertificateValidator;
        }
        using var http = new HttpClient(handler) { Timeout = TimeSpan.FromSeconds(60) };

        // Step 1: Authenticate
        var tokenResponse = await P21Auth.GetTokenAsync(http, config);
        P21Auth.SetAuthHeaders(http, tokenResponse.AccessToken);

        // Step 2: Get UI Server URL (Transaction API uses a separate server)
        var uiServerUrl = await P21Auth.GetUiServerUrlAsync(http, config.BaseUrl);
        Console.WriteLine($"UI Server: {uiServerUrl}");

        // Step 3: GET /api/v2/services
        var rawResponse = await http.GetAsync($"{uiServerUrl}/api/v2/services");
        rawResponse.EnsureSuccessStatusCode();

        var rawJson = await rawResponse.Content.ReadAsStringAsync();
        var rawServices = JArray.Parse(rawJson);

        Console.WriteLine($"Raw response contains {rawServices.Count} services");
        Console.WriteLine("(First 5 shown):");

        foreach (var svc in rawServices.Take(5))
        {
            var name = svc is JObject obj ? obj["Name"]?.ToString() : svc.ToString();
            Console.WriteLine($"  - {name}");
        }

        Console.WriteLine("\n" + new string('=', 50));
        Console.WriteLine("Service list complete!");
    }
}
