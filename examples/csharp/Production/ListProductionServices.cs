// Transaction API - List Production/Labor Services
//
// Discovers production and labor-related services available through the
// Transaction API. Filters the full service list for relevant keywords.
// Mirrors: scripts/transaction/01_list_services.py (filtered for production)
//
// The Transaction API uses a UI Server URL (different from the base URL).
// Services are discovered via GET /api/v2/services.

using Newtonsoft.Json.Linq;
using P21Examples.Common;

namespace P21Examples.Production;

/// <summary>
/// Lists production and labor-related services available through the
/// P21 Transaction API. Filters results by production/labor keywords.
/// </summary>
public static class ListProductionServices
{
    // Keywords to filter production/labor services
    private static readonly string[] ProductionKeywords =
    {
        "production", "labor", "timeentry", "time entry",
        "workcenter", "work center",
        "routing", "predefinedrouting", "predefined routing",
        "manufacturing", "operation", "assembly", "shift", "job"
    };

    // Services documented in 12-Production-Labor-API.md, checked by exact name
    private static readonly string[] KnownProductionServices =
    {
        // Core Production
        "ProductionOrder", "ProductionOrderProcessing",
        "ProductionOrderPicking", "ProductionOrderFreightEntry",
        "CompletedProducitonOrderAdjustment",
        // Labor & Time
        "TimeEntry", "TimeEntrySO", "Labor", "LaborProcess",
        // Supporting
        "WorkCenter", "Operation", "PredefinedRouting",
        "Assembly", "AssemblyClass", "ManufacturingClass",
        "Shift", "Job", "JobControl", "JobContractPricing"
    };

    public static async Task RunAsync()
    {
        Console.WriteLine("Transaction API - List Production/Labor Services");
        Console.WriteLine(new string('=', 60));

        using var client = await P21Client.CreateAsync();

        Console.WriteLine("\nFetching all available services...");
        Console.WriteLine(new string('-', 50));

        // ListServicesAsync returns a JArray of service objects
        var services = await client.Transaction.ListServicesAsync();

        // Extract service names
        var allServiceNames = services
            .Select(s => s is JObject obj ? obj["Name"]?.ToString() ?? s.ToString() : s.ToString())
            .Where(name => !string.IsNullOrEmpty(name))
            .OrderBy(name => name)
            .ToList();

        Console.WriteLine($"\nTotal services available: {allServiceNames.Count}");

        // -----------------------------------------------------------------
        // Filter for production/labor-related services
        // -----------------------------------------------------------------
        Console.WriteLine("\n\nProduction/Labor Related Services:");
        Console.WriteLine(new string('-', 50));

        var matchedServices = allServiceNames
            .Where(name => ProductionKeywords.Any(kw =>
                name.Contains(kw, StringComparison.OrdinalIgnoreCase)))
            .ToList();

        if (matchedServices.Count > 0)
        {
            Console.WriteLine($"\nFound {matchedServices.Count} matching services:\n");
            foreach (var name in matchedServices)
            {
                Console.WriteLine($"    {name}");
            }
        }
        else
        {
            Console.WriteLine("\n  No services matched production/labor keywords.");
            Console.WriteLine("  This may indicate different naming conventions on your P21 instance.");
        }

        // -----------------------------------------------------------------
        // Check for known production service names
        // -----------------------------------------------------------------
        Console.WriteLine("\n\nKnown Production Services:");
        Console.WriteLine(new string('-', 50));

        var serviceSet = new HashSet<string>(allServiceNames, StringComparer.OrdinalIgnoreCase);

        foreach (var svc in KnownProductionServices)
        {
            var status = serviceSet.Contains(svc) ? "Available" : "Not found";
            Console.WriteLine($"  {svc}: {status}");
        }

        // -----------------------------------------------------------------
        // Show all services for manual inspection (optional)
        // -----------------------------------------------------------------
        Console.WriteLine("\n\nAll Available Services (for reference):");
        Console.WriteLine(new string('-', 50));

        var currentLetter = "";
        foreach (var name in allServiceNames)
        {
            var firstLetter = name[..1].ToUpper();

            if (firstLetter != currentLetter)
            {
                currentLetter = firstLetter;
                Console.WriteLine($"\n  [{currentLetter}]");
            }

            // Highlight production-related services
            var highlight = matchedServices.Contains(name) ? " <-- Production/Labor" : "";
            Console.WriteLine($"    {name}{highlight}");
        }

        Console.WriteLine("\n" + new string('=', 60));
        Console.WriteLine("Production service list complete!");
        Console.WriteLine("\nTip: Use 'Get TimeEntry Definition' or 'Get ProductionOrder Definition'");
        Console.WriteLine("to explore the schema of any discovered service.");
    }
}
