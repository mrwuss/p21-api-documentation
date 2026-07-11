// Transaction API - Create Single Record
//
// Demonstrates creating a single record using the Transaction API.
// Mirrors: examples/python/transaction/03_create_single.py
//
// This example creates a SalesPricePage, which is relatively safe for testing
// as it can be easily expired/deactivated.
//
// Transaction API payload structure:
//   {
//     "Name": "SalesPricePage",         // Service name
//     "UseCodeValues": false,            // Use codes vs display values
//     "Transactions": [                  // Array of transactions
//       {
//         "Status": "New",              // Always "New" for creates
//         "DataElements": [             // Data groups (FORM, VALUES, etc.)
//           {
//             "Name": "FORM.form",      // Tab.Datawindow reference
//             "Type": "Form",           // Element type
//             "Keys": [],               // Key fields (empty for new records)
//             "Rows": [{                // One row per record
//               "Edits": [              // Field values
//                 {"Name": "field", "Value": "value"}
//               ]
//             }]
//           }
//         ]
//       }
//     ]
//   }

using System.Globalization;
using Newtonsoft.Json.Linq;
using P21Examples.Common;

namespace P21Examples.Transaction;

/// <summary>
/// Creates a single record (SalesPricePage) via the Transaction API.
/// Shows both P21Client and raw payload construction.
/// </summary>
public static class CreateSingle
{
    public static async Task RunAsync()
    {
        Console.WriteLine("Transaction API - Create Single Record");
        Console.WriteLine(new string('=', 60));

        using var client = await P21Client.CreateAsync();

        // Build a test price page with timestamped description
        var timestamp = DateTime.Now.ToString("HHmmss");
        var description = $"API-TEST-{timestamp}";

        Console.WriteLine($"\nCreating price page: {description}");
        Console.WriteLine(new string('-', 50));

        // Build the Transaction API payload
        var payload = BuildPricePagePayload(
            description: description,
            supplierId: 10,           // A common test supplier
            productGroup: "MISC",     // A common product group
            multiplier: 0.75
        );

        Console.WriteLine("\n  Request payload structure:");
        Console.WriteLine($"    Service: {payload["Name"]}");
        Console.WriteLine($"    UseCodeValues: {payload["UseCodeValues"]}");
        Console.WriteLine($"    Transactions: {(payload["Transactions"] as JArray)?.Count}");
        Console.WriteLine($"    DataElements: {((payload["Transactions"] as JArray)?[0]?["DataElements"] as JArray)?.Count}");

        // WRITE SAFETY gate — print the full payload and require EXECUTE.
        Console.WriteLine("\n  Full payload:");
        Console.WriteLine(payload.ToString());
        if (!ConfirmExecute())
            return;

        try
        {
            // P21Client.Transaction.CreateAsync handles the POST and parses the response
            var result = await client.Transaction.CreateAsync(payload);

            Console.WriteLine("\n  Response:");
            Console.WriteLine($"    HTTP Status: {result.HttpStatusCode}");
            Console.WriteLine($"    Succeeded: {result.Succeeded}");
            Console.WriteLine($"    Failed: {result.Failed}");

            if (result.Messages.Count > 0)
            {
                Console.WriteLine("    Messages:");
                foreach (var msg in result.Messages)
                {
                    Console.WriteLine($"      - {msg}");
                }
            }

            if (result.Succeeded > 0)
            {
                // Extract created record details from the Results
                var results = result.Results as JObject;
                var transactions = results?["Transactions"] as JArray;

                string? uid = null;
                if (transactions?.Count > 0)
                {
                    var trans = transactions[0] as JObject;
                    Console.WriteLine($"\n    Transaction Status: {trans?["Status"]}");

                    // Walk the DataElements to find the generated UID
                    uid = ExtractFieldValue(trans, "price_page_uid");
                    if (uid != null)
                    {
                        Console.WriteLine($"    Created UID: {uid}");
                    }
                }

                Console.WriteLine("\n  SUCCESS: Price page created!");

                // READ-BACK — the only proof of persistence is reading the
                // record back (POST /api/v2/transaction/get keyed by UID).
                if (uid != null)
                {
                    await VerifyCreatedAsync(client, uid, description);
                }
            }
            else
            {
                Console.WriteLine("\n  FAILED: Record not created");
                Console.WriteLine("    Check messages above for details");
            }
        }
        catch (HttpRequestException ex)
        {
            Console.WriteLine($"\n  HTTP Error: {ex.StatusCode}");
            Console.WriteLine($"  Message: {ex.Message[..Math.Min(500, ex.Message.Length)]}");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"\n  Error: {ex.GetType().Name}: {ex.Message}");
        }

        Console.WriteLine("\n" + new string('=', 60));
        Console.WriteLine("Create single record example complete!");
    }

    /// <summary>
    /// Build a Transaction API payload for creating a price page.
    /// </summary>
    /// <param name="description">Price page description (appears in P21 UI).</param>
    /// <param name="supplierId">Supplier ID (numeric).</param>
    /// <param name="productGroup">Product group code (e.g., "MISC").</param>
    /// <param name="multiplier">Pricing multiplier (e.g., 0.75 = 75% of source).</param>
    public static JObject BuildPricePagePayload(
        string description,
        int supplierId,
        string productGroup,
        double multiplier = 0.5)
    {
        return new JObject
        {
            ["Name"] = "SalesPricePage",
            ["UseCodeValues"] = false,
            ["Transactions"] = new JArray
            {
                new JObject
                {
                    ["Status"] = "New",
                    ["DataElements"] = new JArray
                    {
                        // FORM data element — main record fields
                        new JObject
                        {
                            ["Name"] = "FORM.form",
                            ["Type"] = "Form",
                            ["Keys"] = new JArray(),
                            ["Rows"] = new JArray
                            {
                                new JObject
                                {
                                    ["Edits"] = new JArray
                                    {
                                        new JObject { ["Name"] = "price_page_type_cd", ["Value"] = "Supplier / Product Group" },
                                        new JObject { ["Name"] = "company_id", ["Value"] = "ACME" },
                                        // Value is always a STRING in Transaction API payloads
                                        new JObject { ["Name"] = "supplier_id", ["Value"] = supplierId.ToString(CultureInfo.InvariantCulture) },
                                        new JObject { ["Name"] = "product_group_id", ["Value"] = productGroup },
                                        new JObject { ["Name"] = "description", ["Value"] = description },
                                        new JObject { ["Name"] = "pricing_method_cd", ["Value"] = "Source" },
                                        new JObject { ["Name"] = "source_price_cd", ["Value"] = "Supplier List Price" },
                                        new JObject { ["Name"] = "effective_date", ["Value"] = DateTime.Now.ToString("yyyy-MM-dd") },
                                        new JObject { ["Name"] = "expiration_date", ["Value"] = "2030-12-31" },
                                        new JObject { ["Name"] = "totaling_method_cd", ["Value"] = "Item" },
                                        new JObject { ["Name"] = "totaling_basis_cd", ["Value"] = "Supplier List Price" },
                                        new JObject { ["Name"] = "row_status_flag", ["Value"] = "Active" }
                                    },
                                    ["RelativeDateEdits"] = new JArray()
                                }
                            }
                        },
                        // VALUES data element — calculation settings
                        new JObject
                        {
                            ["Name"] = "VALUES.values",
                            ["Type"] = "Form",
                            ["Keys"] = new JArray(),
                            ["Rows"] = new JArray
                            {
                                new JObject
                                {
                                    ["Edits"] = new JArray
                                    {
                                        new JObject { ["Name"] = "calculation_method_cd", ["Value"] = "Multiplier" },
                                        new JObject { ["Name"] = "calculation_value1", ["Value"] = multiplier.ToString(CultureInfo.InvariantCulture) }
                                    },
                                    ["RelativeDateEdits"] = new JArray()
                                }
                            }
                        }
                    }
                }
            }
        };
    }

    /// <summary>
    /// WRITE SAFETY gate (same pattern as Recipes/RecipeHelpers.ConfirmExecute).
    /// Returns true only when the user types EXECUTE; anything else = dry run.
    /// </summary>
    internal static bool ConfirmExecute()
    {
        Console.WriteLine();
        Console.Write("Type EXECUTE to post this write, anything else = dry run: ");
        var answer = Console.ReadLine()?.Trim();
        if (answer == "EXECUTE")
            return true;

        Console.WriteLine("Dry run - nothing was posted.");
        return false;
    }

    /// <summary>
    /// Read the created price page back via POST /api/v2/transaction/get
    /// (keyed by price_page_uid — the service's KeyDefinition) and confirm
    /// the description matches what was submitted.
    /// </summary>
    internal static async Task VerifyCreatedAsync(
        P21Client client, string uid, string expectedDescription)
    {
        Console.WriteLine("\n  Read-back verification (POST /api/v2/transaction/get):");
        try
        {
            var getPayload = new JObject
            {
                ["ServiceName"] = "SalesPricePage",
                ["TransactionStates"] = new JArray
                {
                    new JObject
                    {
                        ["DataElementName"] = "FORM.form",
                        ["Keys"] = new JArray
                        {
                            new JObject { ["Name"] = "price_page_uid", ["Value"] = uid }
                        }
                    }
                }
            };

            var readBack = await client.Transaction.GetRecordsAsync(getPayload);
            var trans = (readBack["Transactions"] as JArray)?[0] as JObject;
            var description = ExtractFieldValue(trans, "description");

            if (description == expectedDescription)
            {
                Console.WriteLine($"    VERIFIED: UID {uid} persisted with description '{description}'");
            }
            else
            {
                Console.WriteLine($"    WARNING: read-back description '{description}' " +
                                  $"does not match submitted '{expectedDescription}'");
            }
        }
        catch (HttpRequestException ex)
        {
            Console.WriteLine($"    Read-back failed: {ex.StatusCode} {ex.Message}");
        }
    }

    /// <summary>
    /// Walk a transaction's DataElements to find a specific field value.
    /// </summary>
    internal static string? ExtractFieldValue(JObject? transaction, string fieldName)
    {
        if (transaction == null) return null;

        var dataElements = transaction["DataElements"] as JArray;
        if (dataElements == null) return null;

        foreach (var elem in dataElements)
        {
            var rows = elem["Rows"] as JArray;
            if (rows == null) continue;

            foreach (var row in rows)
            {
                var edits = row["Edits"] as JArray;
                if (edits == null) continue;

                foreach (var edit in edits)
                {
                    if (string.Equals(edit["Name"]?.ToString(), fieldName, StringComparison.OrdinalIgnoreCase))
                    {
                        return edit["Value"]?.ToString();
                    }
                }
            }
        }

        return null;
    }
}
