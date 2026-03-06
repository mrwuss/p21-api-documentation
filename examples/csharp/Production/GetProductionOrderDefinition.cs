// Transaction API - Get ProductionOrder Service Definition
//
// Retrieves the schema/template for the ProductionOrder service to understand
// production order structure, especially labor-related DataElements.
// Mirrors: scripts/transaction/02_get_definition.py (for ProductionOrder)
//
// Endpoints:
//   GET /api/v2/definition/ProductionOrder  - Field definitions and template
//   GET /api/v2/defaults/ProductionOrder    - Default values for new records

using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using P21Examples.Common;

namespace P21Examples.Production;

/// <summary>
/// Demonstrates fetching the ProductionOrder service definition and defaults
/// from the Transaction API. Shows all DataElements with focus on labor-related
/// fields for production order management.
/// </summary>
public static class GetProductionOrderDefinition
{
    public static async Task RunAsync()
    {
        Console.WriteLine("Transaction API - Get ProductionOrder Service Definition");
        Console.WriteLine(new string('=', 60));

        using var client = await P21Client.CreateAsync();

        // -----------------------------------------------------------------
        // Step 1: Get the ProductionOrder definition
        // -----------------------------------------------------------------
        var serviceName = "ProductionOrder";
        Console.WriteLine($"\n1. Getting definition for '{serviceName}' service:");
        Console.WriteLine(new string('-', 50));

        try
        {
            var definition = await client.Transaction.GetDefinitionAsync(serviceName);

            // The definition has two main sections:
            //   Template             - The payload structure with DataElements and Rows
            //   TransactionDefinition - Field metadata (types, required, valid values)

            var template = definition["Template"] as JObject;
            var transactionSet = template?["TransactionSet"] ?? template;

            Console.WriteLine($"\n  Service: {transactionSet?["Name"]}");
            Console.WriteLine($"  UseCodeValues: {transactionSet?["UseCodeValues"] ?? false}");

            // Show all DataElements from the template
            var transactions = transactionSet?["Transactions"] as JArray;
            if (transactions?.Count > 0)
            {
                Console.WriteLine("\n  DataElements in template:");
                var firstTrans = transactions[0] as JObject;
                var dataElements = firstTrans?["DataElements"] as JArray;

                if (dataElements != null)
                {
                    Console.WriteLine($"  Total DataElements: {dataElements.Count}\n");

                    foreach (var elem in dataElements)
                    {
                        PrintDataElement(elem as JObject, indent: 2);
                        Console.WriteLine();
                    }
                }
            }

            // Show field definitions for all DataElements
            var transDef = definition["TransactionDefinition"] as JObject;
            var dataElemDefs = transDef?["DataElementDefinitions"] as JArray;

            if (dataElemDefs?.Count > 0)
            {
                Console.WriteLine("\n  Field Definitions (all DataElements):");
                Console.WriteLine(new string('-', 50));

                foreach (var elemDef in dataElemDefs)
                {
                    var obj = elemDef as JObject;
                    var elemName = obj?["Name"]?.ToString() ?? "Unknown";

                    Console.WriteLine($"\n  DataElement: {elemName}");
                    Console.WriteLine($"  Type: {obj?["Type"]}");
                    Console.WriteLine($"  Key Fields: {obj?["KeyFields"]}");

                    // Highlight labor-related DataElements
                    if (elemName.Contains("labor", StringComparison.OrdinalIgnoreCase) ||
                        elemName.Contains("routing", StringComparison.OrdinalIgnoreCase) ||
                        elemName.Contains("operation", StringComparison.OrdinalIgnoreCase) ||
                        elemName.Contains("component", StringComparison.OrdinalIgnoreCase))
                    {
                        Console.WriteLine("  ** Labor/Routing Related **");
                    }

                    var fieldDefs = obj?["FieldDefinitions"] as JArray;
                    if (fieldDefs != null)
                    {
                        // Show required fields
                        var requiredFields = fieldDefs
                            .OfType<JObject>()
                            .Where(f => f["Required"]?.Value<bool>() == true)
                            .ToList();

                        if (requiredFields.Count > 0)
                        {
                            Console.WriteLine("\n    Required Fields:");
                            foreach (var field in requiredFields)
                            {
                                PrintFieldDefinition(field, indent: 3);
                            }
                        }

                        // Show all fields (up to 15 per element)
                        Console.WriteLine($"\n    All Fields ({fieldDefs.Count} total, * = required):");
                        foreach (var field in fieldDefs.Take(15))
                        {
                            PrintFieldDefinition(field as JObject, indent: 3);
                        }

                        if (fieldDefs.Count > 15)
                        {
                            Console.WriteLine($"\n      ... and {fieldDefs.Count - 15} more fields");
                        }
                    }

                    Console.WriteLine();
                }
            }
        }
        catch (HttpRequestException ex)
        {
            Console.WriteLine($"  Error: {ex.StatusCode} - {ex.Message[..Math.Min(200, ex.Message.Length)]}");
            Console.WriteLine("\n  The ProductionOrder service may not be available on this P21 instance.");
            Console.WriteLine("  Run 'List Production Services' to see what services exist.");
        }

        // -----------------------------------------------------------------
        // Step 2: Get default values for ProductionOrder
        // -----------------------------------------------------------------
        Console.WriteLine($"\n\n2. Getting default values for '{serviceName}' service:");
        Console.WriteLine(new string('-', 50));

        try
        {
            var defaults = await client.Transaction.GetDefaultsAsync(serviceName);

            var dataElements = defaults["DataElements"] as JArray;
            if (dataElements?.Count > 0)
            {
                foreach (var elem in dataElements)
                {
                    var elemObj = elem as JObject;
                    Console.WriteLine($"\n  DataElement: {elemObj?["Name"]}");
                    Console.WriteLine("  Default values:");

                    var rows = elemObj?["Rows"] as JArray;
                    if (rows?.Count > 0)
                    {
                        var edits = (rows[0] as JObject)?["Edits"] as JArray;
                        if (edits != null)
                        {
                            var hasDefaults = false;
                            foreach (var edit in edits)
                            {
                                var name = edit["Name"]?.ToString();
                                var value = edit["Value"]?.ToString();

                                // Only show fields with non-empty defaults
                                if (!string.IsNullOrEmpty(value))
                                {
                                    Console.WriteLine($"    {name}: {value}");
                                    hasDefaults = true;
                                }
                            }

                            if (!hasDefaults)
                            {
                                Console.WriteLine("    (no non-empty defaults)");
                            }
                        }
                    }
                }
            }
            else
            {
                Console.WriteLine("  No default values returned.");
            }
        }
        catch (HttpRequestException ex)
        {
            Console.WriteLine($"  Error: {ex.StatusCode} - {ex.Message[..Math.Min(200, ex.Message.Length)]}");
        }

        Console.WriteLine("\n" + new string('=', 60));
        Console.WriteLine("ProductionOrder definition examples complete!");
        Console.WriteLine("\nTip: Save full definition to file for reference:");
        Console.WriteLine("  File.WriteAllText(\"productionorder_definition.json\", definition.ToString(Formatting.Indented))");
    }

    /// <summary>
    /// Print a DataElement structure from the template.
    /// </summary>
    private static void PrintDataElement(JObject? element, int indent)
    {
        if (element == null) return;

        var prefix = new string(' ', indent * 2);
        var name = element["Name"]?.ToString() ?? "Unknown";
        var type = element["Type"]?.ToString() ?? "Unknown";
        var keys = element["Keys"] as JArray;

        Console.WriteLine($"{prefix}DataElement: {name}");
        Console.WriteLine($"{prefix}  Type: {type}");

        if (keys?.Count > 0)
        {
            Console.WriteLine($"{prefix}  Keys: {keys}");
        }

        // Highlight labor-related elements
        if (name.Contains("labor", StringComparison.OrdinalIgnoreCase) ||
            name.Contains("routing", StringComparison.OrdinalIgnoreCase) ||
            name.Contains("operation", StringComparison.OrdinalIgnoreCase) ||
            name.Contains("component", StringComparison.OrdinalIgnoreCase))
        {
            Console.WriteLine($"{prefix}  ** Labor/Routing Related **");
        }

        // Show fields from the first row
        var rows = element["Rows"] as JArray;
        if (rows?.Count > 0)
        {
            var edits = (rows[0] as JObject)?["Edits"] as JArray;
            if (edits != null)
            {
                Console.WriteLine($"{prefix}  Fields ({edits.Count} total):");

                foreach (var edit in edits.Take(10))
                {
                    Console.WriteLine($"{prefix}    - {edit["Name"]}");
                }

                if (edits.Count > 10)
                {
                    Console.WriteLine($"{prefix}    ... and {edits.Count - 10} more");
                }
            }
        }
    }

    /// <summary>
    /// Print a field definition with type, required flag, and valid values.
    /// </summary>
    private static void PrintFieldDefinition(JObject? fieldDef, int indent)
    {
        if (fieldDef == null) return;

        var prefix = new string(' ', indent * 2);
        var name = fieldDef["Name"]?.ToString() ?? "Unknown";
        var dataType = fieldDef["DataType"]?.ToString() ?? "Unknown";
        var required = fieldDef["Required"]?.Value<bool>() ?? false;
        var label = fieldDef["Label"]?.ToString() ?? "";
        var validValues = fieldDef["ValidValues"] as JArray;

        var reqMarker = required ? "*" : " ";
        Console.WriteLine($"{prefix}{reqMarker} {name} ({dataType}): {label}");

        if (validValues?.Count > 0)
        {
            var preview = string.Join(", ", validValues.Take(5).Select(v => v.ToString()));
            var suffix = validValues.Count > 5 ? "..." : "";
            Console.WriteLine($"{prefix}    Valid: [{preview}]{suffix}");
        }
    }
}
