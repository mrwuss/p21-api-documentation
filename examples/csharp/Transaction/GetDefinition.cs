// Transaction API - Get Service Definition
//
// Retrieves the schema/template for a service to understand required fields.
// Mirrors: examples/python/transaction/02_get_definition.py
//
// Endpoints:
//   GET /api/v2/definition/{serviceName}  - Field definitions and template
//   GET /api/v2/defaults/{serviceName}    - Default values for new records

using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using P21Examples.Common;

namespace P21Examples.Transaction;

/// <summary>
/// Demonstrates fetching service definitions and default values from
/// the Transaction API. Essential for understanding payload structure.
/// </summary>
public static class GetDefinition
{
    public static async Task RunAsync()
    {
        Console.WriteLine("Transaction API - Get Service Definition");
        Console.WriteLine(new string('=', 60));

        using var client = await P21Client.CreateAsync();

        // -----------------------------------------------------------------
        // Example 1: Get Order definition
        // -----------------------------------------------------------------
        var serviceName = "Order";
        Console.WriteLine($"\n1. Getting definition for '{serviceName}' service:");
        Console.WriteLine(new string('-', 50));

        try
        {
            var definition = await client.Transaction.GetDefinitionAsync(serviceName);

            // The definition has two main sections:
            //   Template         - The payload structure with DataElements and Rows
            //   TransactionDefinition - Field metadata (types, required, valid values)

            var template = definition["Template"] as JObject;
            var transactionSet = template?["TransactionSet"] ?? template;

            Console.WriteLine($"\n  Service: {transactionSet?["Name"]}");
            Console.WriteLine($"  UseCodeValues: {transactionSet?["UseCodeValues"] ?? false}");

            // Show DataElements from the template
            var transactions = transactionSet?["Transactions"] as JArray;
            if (transactions?.Count > 0)
            {
                Console.WriteLine("\n  DataElements in template:");
                var firstTrans = transactions[0] as JObject;
                var dataElements = firstTrans?["DataElements"] as JArray;

                if (dataElements != null)
                {
                    foreach (var elem in dataElements.Take(5))
                    {
                        PrintDataElement(elem as JObject, indent: 2);
                        Console.WriteLine();
                    }
                }
            }

            // Show field definitions (metadata about each field)
            var transDef = definition["TransactionDefinition"] as JObject;
            var dataElemDefs = transDef?["DataElementDefinitions"] as JArray;

            if (dataElemDefs?.Count > 0)
            {
                Console.WriteLine("\n  Field Definitions (first DataElement):");
                var firstElem = dataElemDefs[0] as JObject;
                Console.WriteLine($"    DataElement: {firstElem?["Name"]}");
                Console.WriteLine($"    Key Fields: {firstElem?["KeyFields"]}");
                Console.WriteLine("\n    Fields (* = required):");

                var fieldDefs = firstElem?["FieldDefinitions"] as JArray;
                if (fieldDefs != null)
                {
                    foreach (var field in fieldDefs.Take(15))
                    {
                        PrintFieldDefinition(field as JObject, indent: 3);
                    }

                    if (fieldDefs.Count > 15)
                    {
                        Console.WriteLine($"\n    ... and {fieldDefs.Count - 15} more fields");
                    }
                }
            }
        }
        catch (HttpRequestException ex)
        {
            Console.WriteLine($"  Error: {ex.StatusCode} - {ex.Message[..Math.Min(200, ex.Message.Length)]}");
        }

        // -----------------------------------------------------------------
        // Example 2: Get SalesPricePage definition (commonly used)
        // -----------------------------------------------------------------
        serviceName = "SalesPricePage";
        Console.WriteLine($"\n\n2. Getting definition for '{serviceName}' service:");
        Console.WriteLine(new string('-', 50));

        try
        {
            var definition = await client.Transaction.GetDefinitionAsync(serviceName);

            var transDef = definition["TransactionDefinition"] as JObject;
            var dataElemDefs = transDef?["DataElementDefinitions"] as JArray;

            if (dataElemDefs != null)
            {
                foreach (var elemDef in dataElemDefs.Take(2))
                {
                    var obj = elemDef as JObject;
                    Console.WriteLine($"\n  DataElement: {obj?["Name"]}");
                    Console.WriteLine($"  Type: {obj?["Type"]}");

                    Console.WriteLine("\n  Required Fields:");
                    var fieldDefs = obj?["FieldDefinitions"] as JArray;
                    if (fieldDefs != null)
                    {
                        foreach (var field in fieldDefs)
                        {
                            var fieldObj = field as JObject;
                            if (fieldObj?["Required"]?.Value<bool>() == true)
                            {
                                PrintFieldDefinition(fieldObj, indent: 2);
                            }
                        }
                    }
                }
            }
        }
        catch (HttpRequestException ex)
        {
            Console.WriteLine($"  Error: {ex.StatusCode} - {ex.Message[..Math.Min(200, ex.Message.Length)]}");
        }

        // -----------------------------------------------------------------
        // Example 3: Get default values
        // -----------------------------------------------------------------
        Console.WriteLine($"\n\n3. Getting default values for 'Order' service:");
        Console.WriteLine(new string('-', 50));

        try
        {
            var defaults = await client.Transaction.GetDefaultsAsync("Order");

            var dataElements = defaults["DataElements"] as JArray;
            if (dataElements?.Count > 0)
            {
                var elem = dataElements[0] as JObject;
                Console.WriteLine($"\n  DataElement: {elem?["Name"]}");
                Console.WriteLine("\n  Default values:");

                var rows = elem?["Rows"] as JArray;
                if (rows?.Count > 0)
                {
                    var edits = (rows[0] as JObject)?["Edits"] as JArray;
                    if (edits != null)
                    {
                        foreach (var edit in edits.Take(10))
                        {
                            var name = edit["Name"]?.ToString();
                            var value = edit["Value"]?.ToString();

                            // Only show fields with non-empty defaults
                            if (!string.IsNullOrEmpty(value))
                            {
                                Console.WriteLine($"    {name}: {value}");
                            }
                        }
                    }
                }
            }
        }
        catch (HttpRequestException ex)
        {
            Console.WriteLine($"  Error: {ex.StatusCode} - {ex.Message[..Math.Min(200, ex.Message.Length)]}");
        }

        Console.WriteLine("\n" + new string('=', 60));
        Console.WriteLine("Definition examples complete!");
        Console.WriteLine("\nTip: Save full definition to file for reference:");
        Console.WriteLine("  File.WriteAllText(\"definition.json\", definition.ToString(Formatting.Indented))");
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
