// Transaction API - Bulk Create Records
//
// Demonstrates creating multiple records in a single request.
// Mirrors: scripts/transaction/04_create_bulk.py
//
// The Transaction API can process multiple transactions at once, which is
// more efficient than making individual requests. All transactions in a
// single request share the same session pool context.

using Newtonsoft.Json.Linq;
using P21Examples.Common;

namespace P21Examples.Transaction;

/// <summary>
/// Creates multiple records in a single Transaction API request.
/// Demonstrates bulk payload construction with multiple Transactions.
/// </summary>
public static class CreateBulk
{
    /// <summary>
    /// Record definition for a price page to create.
    /// </summary>
    private record PricePageRecord(
        string Description,
        int SupplierId,
        string ProductGroup,
        double Multiplier);

    public static async Task RunAsync()
    {
        Console.WriteLine("Transaction API - Bulk Create Records");
        Console.WriteLine(new string('=', 60));

        using var client = await P21Client.CreateAsync();

        // Prepare test records with timestamped descriptions
        var timestamp = DateTime.Now.ToString("HHmmss");

        var records = new PricePageRecord[]
        {
            new($"BULK-TEST-{timestamp}-A", SupplierId: 10, ProductGroup: "MISC", Multiplier: 0.70),
            new($"BULK-TEST-{timestamp}-B", SupplierId: 10, ProductGroup: "MISC", Multiplier: 0.75),
            new($"BULK-TEST-{timestamp}-C", SupplierId: 10, ProductGroup: "MISC", Multiplier: 0.80)
        };

        Console.WriteLine($"\nCreating {records.Length} price pages in single request:");
        Console.WriteLine(new string('-', 50));

        for (var i = 0; i < records.Length; i++)
        {
            Console.WriteLine($"  {i + 1}. {records[i].Description} (multiplier: {records[i].Multiplier})");
        }

        // Build the bulk payload (multiple Transactions in one TransactionSet)
        var payload = BuildBulkPayload(records);

        Console.WriteLine($"\n  Payload:");
        Console.WriteLine($"    Service: {payload["Name"]}");
        Console.WriteLine($"    Transactions: {(payload["Transactions"] as JArray)?.Count}");

        try
        {
            var result = await client.Transaction.CreateAsync(payload);

            // Analyze results
            Console.WriteLine("\n  Results:");
            Console.WriteLine($"    HTTP Status: {result.HttpStatusCode}");
            Console.WriteLine($"    Succeeded: {result.Succeeded}");
            Console.WriteLine($"    Failed: {result.Failed}");

            // Show per-transaction messages
            if (result.Messages.Count > 0)
            {
                Console.WriteLine("\n  Transaction Messages:");
                foreach (var msg in result.Messages)
                {
                    Console.WriteLine($"    - {msg}");
                }
            }

            // Show created UIDs from the Results
            var resultsObj = result.Results as JObject;
            var transactions = resultsObj?["Transactions"] as JArray;

            if (transactions?.Count > 0)
            {
                Console.WriteLine("\n  Created Records:");

                for (var i = 0; i < transactions.Count; i++)
                {
                    var trans = transactions[i] as JObject;
                    var status = trans?["Status"]?.ToString() ?? "Unknown";

                    // Walk DataElements to find the generated UID
                    var uid = CreateSingle.ExtractFieldValue(trans, "price_page_uid");

                    var statusMarker = status == "Passed" ? "OK" : "FAIL";
                    Console.WriteLine($"    [{statusMarker}] Transaction {i + 1}: UID={uid ?? "N/A"}, Status={status}");
                }
            }

            // Summary
            Console.WriteLine("\n" + new string('-', 50));
            if (result.Succeeded == records.Length)
            {
                Console.WriteLine($"  SUCCESS: All {result.Succeeded} records created!");
            }
            else if (result.Succeeded > 0)
            {
                Console.WriteLine($"  PARTIAL: {result.Succeeded} created, {result.Failed} failed");
            }
            else
            {
                Console.WriteLine("  FAILED: No records created");
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
        Console.WriteLine("Bulk create example complete!");
        Console.WriteLine("\nNote: Bulk operations are more efficient than individual requests,");
        Console.WriteLine("but all transactions share the same session pool context.");
    }

    /// <summary>
    /// Build a Transaction API payload for creating multiple price pages.
    /// Each record becomes a separate Transaction in the Transactions array.
    /// </summary>
    private static JObject BuildBulkPayload(PricePageRecord[] records)
    {
        var transactions = new JArray();

        foreach (var record in records)
        {
            var transaction = new JObject
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
                                    new JObject { ["Name"] = "supplier_id", ["Value"] = (double)record.SupplierId },
                                    new JObject { ["Name"] = "product_group_id", ["Value"] = record.ProductGroup },
                                    new JObject { ["Name"] = "description", ["Value"] = record.Description },
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
                                    new JObject { ["Name"] = "calculation_value1", ["Value"] = record.Multiplier.ToString() }
                                },
                                ["RelativeDateEdits"] = new JArray()
                            }
                        }
                    }
                }
            };

            transactions.Add(transaction);
        }

        return new JObject
        {
            ["Name"] = "SalesPricePage",
            ["UseCodeValues"] = false,
            ["Transactions"] = transactions
        };
    }
}
