// Transaction API - Update Existing Records
//
// Demonstrates updating existing records using the Transaction API.
// Mirrors: examples/python/transaction/05_update_existing.py
//
// To update a record:
//   1. Fetch it via POST /api/v2/transaction/get (with key fields)
//   2. Build an update payload that IDENTIFIES the record (its key field
//      goes in the FORM Edits — for SalesPricePage that is price_page_uid,
//      per the KeyDefinitions in GET /api/v2/definition/SalesPricePage:
//      [{"Location": "form", "Name": "price_page_uid"}]) plus only the
//      changed fields
//   3. Send via POST /api/v2/transaction (Status is still "New" — sending
//      "New" is the only value the Status enum accepts)
//
// !!! UNVERIFIED: the SalesPricePage update path shown here has NOT been
// !!! verified live. The corrected payload shape follows the VERIFIED
// !!! JobContractPricing update pattern (Status "New", FORM Keys empty,
// !!! key fields inside Edits) — see docs/03-Transaction-API.md,
// !!! "Updating an Existing Contract". Verify with a read-back before
// !!! relying on it.
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
        Console.WriteLine("  Updates use Status \"New\" and identify the record by its");
        Console.WriteLine("  key field (price_page_uid) inside the FORM Edits, alongside");
        Console.WriteLine("  the changed fields. Fetch current values via /get first.");
        Console.WriteLine("  NOTE: this exact service's update path is UNVERIFIED — the");
        Console.WriteLine("  shape follows the verified JobContractPricing pattern");
        Console.WriteLine("  (docs/03-Transaction-API.md, 'Updating an Existing Contract').");

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
        Console.WriteLine("- Include the identifying key (price_page_uid) in the FORM Edits,");
        Console.WriteLine("  plus only the fields you want to change");
        Console.WriteLine("- The 'Status' in the request is still 'New' for updates");
        Console.WriteLine("  ('New' is the only value the Status enum accepts)");
        Console.WriteLine("- SalesPricePage updates are UNVERIFIED; the verified reference");
        Console.WriteLine("  is JobContractPricing (docs/03, 'Updating an Existing Contract')");
        Console.WriteLine("- Verify with a read-back (/transaction/get) after any update");
    }

    /// <summary>
    /// Build a Transaction API payload for updating a price page.
    /// Identifies the record via price_page_uid (the service's only
    /// KeyDefinition, located on "form") in the FORM Edits — mirroring the
    /// verified JobContractPricing pattern where FORM Keys stays empty and
    /// key fields ride in Edits — plus only the fields being changed.
    ///
    /// UNVERIFIED for SalesPricePage specifically: this shape follows the
    /// verified JobContractPricing update path (docs/03-Transaction-API.md,
    /// "Updating an Existing Contract"). Verify with a read-back.
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
        // Build edits for the FORM data element. The identifying key field
        // (price_page_uid, per the definition's KeyDefinitions) goes FIRST
        // in Edits; FORM Keys stays empty, as in the verified
        // JobContractPricing update pattern.
        var formEdits = new JArray
        {
            new JObject
            {
                ["Name"] = "price_page_uid",
                ["Value"] = pricePageUid.ToString(System.Globalization.CultureInfo.InvariantCulture)
            }
        };

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
                            new JObject { ["Name"] = "calculation_value1", ["Value"] = newMultiplier.Value.ToString(System.Globalization.CultureInfo.InvariantCulture) }
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
