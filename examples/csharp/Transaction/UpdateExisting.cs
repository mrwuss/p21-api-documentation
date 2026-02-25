// Transaction API - Update Existing Records
//
// Demonstrates updating existing records using the Transaction API.
// Mirrors: scripts/transaction/05_update_existing.py
//
// To update a record:
//   1. Fetch it via POST /api/v2/transaction/get (with key fields)
//   2. Build an update payload with only the changed fields
//   3. Send via POST /api/v2/transaction (Status is still "New")
//
// The /get endpoint uses a different payload structure:
//   {
//     "ServiceName": "SalesPricePage",
//     "TransactionStates": [
//       {
//         "DataElementName": "FORM.form",
//         "Keys": [
//           {"Name": "price_page_uid", "Value": "12345"}
//         ]
//       }
//     ]
//   }

using Newtonsoft.Json.Linq;
using P21Examples.Common;

namespace P21Examples.Transaction;

/// <summary>
/// Demonstrates fetching and updating existing records via the Transaction API.
/// Shows the /transaction/get endpoint for record retrieval.
/// </summary>
public static class UpdateExisting
{
    public static async Task RunAsync()
    {
        Console.WriteLine("Transaction API - Update Existing Records");
        Console.WriteLine(new string('=', 60));

        using var client = await P21Client.CreateAsync();

        // -----------------------------------------------------------------
        // Example 1: Get an existing record via /transaction/get
        // -----------------------------------------------------------------
        Console.WriteLine("\n1. Get existing record using /transaction/get:");
        Console.WriteLine(new string('-', 50));

        // Use a known test UID — in real usage, you'd query for this
        var testUid = 45557; // Replace with a valid UID from your system

        try
        {
            Console.WriteLine($"  Fetching price page UID: {testUid}");

            // Build the /get payload (different structure from create)
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
                            new JObject
                            {
                                ["Name"] = "price_page_uid",
                                ["Value"] = testUid.ToString()
                            }
                        }
                    }
                }
            };

            // P21Client.Transaction.GetRecordsAsync wraps POST /api/v2/transaction/get
            var result = await client.Transaction.GetRecordsAsync(getPayload);

            var transactions = result["Transactions"] as JArray;
            if (transactions?.Count > 0)
            {
                foreach (var trans in transactions.Take(1))
                {
                    var dataElements = trans["DataElements"] as JArray;
                    if (dataElements == null) continue;

                    foreach (var elem in dataElements)
                    {
                        Console.WriteLine($"\n  DataElement: {elem["Name"]}");
                        var rows = elem["Rows"] as JArray;
                        if (rows?.Count > 0)
                        {
                            Console.WriteLine("  Current values:");
                            var edits = (rows[0] as JObject)?["Edits"] as JArray;
                            if (edits != null)
                            {
                                foreach (var edit in edits.Take(8))
                                {
                                    var name = edit["Name"]?.ToString();
                                    var value = edit["Value"]?.ToString();
                                    if (!string.IsNullOrEmpty(value))
                                    {
                                        Console.WriteLine($"    {name}: {value}");
                                    }
                                }
                            }
                        }
                    }
                }
            }
            else
            {
                Console.WriteLine("  No transaction data returned");
            }
        }
        catch (HttpRequestException ex)
        {
            Console.WriteLine($"  Error: {ex.StatusCode}");
            if (ex.StatusCode == System.Net.HttpStatusCode.NotFound)
            {
                Console.WriteLine($"  Record UID {testUid} not found");
            }
            else
            {
                Console.WriteLine($"  {ex.Message[..Math.Min(200, ex.Message.Length)]}");
            }
        }

        // -----------------------------------------------------------------
        // Example 2: Show update payload structure
        // -----------------------------------------------------------------
        Console.WriteLine("\n\n2. Update payload structure:");
        Console.WriteLine(new string('-', 50));
        Console.WriteLine("  Updates require identifying the record via /get first,");
        Console.WriteLine("  then sending only the changed fields.");

        var updatePayload = BuildUpdatePayload(
            pricePageUid: testUid,
            newDescription: "Updated Description",
            newMultiplier: 0.85
        );

        Console.WriteLine("\n  Sample update payload:");
        Console.WriteLine($"    Service: {updatePayload["Name"]}");
        Console.WriteLine($"    Transactions: {(updatePayload["Transactions"] as JArray)?.Count}");

        var updateTransactions = updatePayload["Transactions"] as JArray;
        if (updateTransactions != null)
        {
            foreach (var trans in updateTransactions)
            {
                var dataElements = trans["DataElements"] as JArray;
                if (dataElements == null) continue;

                foreach (var elem in dataElements)
                {
                    Console.WriteLine($"\n    DataElement: {elem["Name"]}");
                    var rows = elem["Rows"] as JArray;
                    if (rows == null) continue;

                    foreach (var row in rows)
                    {
                        Console.WriteLine("      Fields to update:");
                        var edits = row["Edits"] as JArray;
                        if (edits == null) continue;

                        foreach (var edit in edits)
                        {
                            Console.WriteLine($"        {edit["Name"]}: {edit["Value"]}");
                        }
                    }
                }
            }
        }

        // -----------------------------------------------------------------
        // Example 3: Show expire payload
        // -----------------------------------------------------------------
        Console.WriteLine("\n\n3. Expire record payload structure:");
        Console.WriteLine(new string('-', 50));

        var expirePayload = BuildUpdatePayload(
            pricePageUid: testUid,
            expire: true
        );

        var expireTransactions = expirePayload["Transactions"] as JArray;
        if (expireTransactions != null)
        {
            foreach (var trans in expireTransactions)
            {
                var dataElements = trans["DataElements"] as JArray;
                if (dataElements == null) continue;

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
                            Console.WriteLine($"    {edit["Name"]}: {edit["Value"]}");
                        }
                    }
                }
            }
        }

        Console.WriteLine("\n  Note: Setting row_status_flag to 'Expired' deactivates the record.");

        Console.WriteLine("\n" + new string('=', 60));
        Console.WriteLine("Update examples complete!");
        Console.WriteLine("\nImportant notes:");
        Console.WriteLine("- Always fetch the record first with /transaction/get");
        Console.WriteLine("- Only include fields you want to change");
        Console.WriteLine("- The 'Status' in the request is still 'New' for updates");
    }

    /// <summary>
    /// Build a Transaction API payload for updating a price page.
    /// Only includes the fields that are being changed.
    /// </summary>
    /// <param name="pricePageUid">The UID of the price page to update.</param>
    /// <param name="newDescription">New description, or null to skip.</param>
    /// <param name="newMultiplier">New multiplier, or null to skip.</param>
    /// <param name="expire">If true, sets row_status_flag to "Expired".</param>
    private static JObject BuildUpdatePayload(
        int pricePageUid,
        string? newDescription = null,
        double? newMultiplier = null,
        bool expire = false)
    {
        // Build edits for the FORM data element (only changed fields)
        var formEdits = new JArray();

        if (!string.IsNullOrEmpty(newDescription))
        {
            formEdits.Add(new JObject { ["Name"] = "description", ["Value"] = newDescription });
        }

        if (expire)
        {
            formEdits.Add(new JObject { ["Name"] = "row_status_flag", ["Value"] = "Expired" });
        }

        // Build data elements
        var dataElements = new JArray
        {
            new JObject
            {
                ["Name"] = "FORM.form",
                ["Type"] = "Form",
                ["Keys"] = new JArray(),
                ["Rows"] = new JArray
                {
                    new JObject
                    {
                        ["Edits"] = formEdits,
                        ["RelativeDateEdits"] = new JArray()
                    }
                }
            }
        };

        // If updating multiplier, add the VALUES data element
        if (newMultiplier.HasValue)
        {
            dataElements.Add(new JObject
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
                            new JObject { ["Name"] = "calculation_value1", ["Value"] = newMultiplier.Value.ToString() }
                        },
                        ["RelativeDateEdits"] = new JArray()
                    }
                }
            });
        }

        return new JObject
        {
            ["Name"] = "SalesPricePage",
            ["UseCodeValues"] = false,
            ["Transactions"] = new JArray
            {
                new JObject
                {
                    ["Status"] = "New",  // Still "New" for updates
                    ["DataElements"] = dataElements
                }
            }
        };
    }
}
