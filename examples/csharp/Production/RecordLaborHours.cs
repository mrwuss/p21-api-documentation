// Transaction API - Record Labor Hours
//
// Demonstrates recording labor hours against a production order using the
// TimeEntry Transaction API service.
// Mirrors: examples/python/transaction/03_create_single.py (adapted for TimeEntry)
//
// Transaction API payload structure for TimeEntry:
//   {
//     "Name": "TimeEntry",
//     "UseCodeValues": false,
//     "Transactions": [
//       {
//         "Status": "New",
//         "DataElements": [
//           {
//             "Name": "TP_TECHNICIAN.tp_technician",   // Technician header
//             "Type": "Form",
//             "Keys": [],
//             "Rows": [{ "Edits": [...] }]
//           },
//           {
//             "Name": "TP_LABORRECORDING.prod_order_line_comp_labor",  // Labor lines
//             "Type": "List",
//             "Keys": [],
//             "Rows": [{ "Edits": [...] }]
//           }
//         ]
//       }
//     ]
//   }

using System.Globalization;
using Newtonsoft.Json.Linq;
using P21Examples.Common;

namespace P21Examples.Production;

/// <summary>
/// Creates a labor time entry recording against a production order via the
/// Transaction API. Shows both payload construction and response parsing.
/// </summary>
public static class RecordLaborHours
{
    public static async Task RunAsync()
    {
        Console.WriteLine("Transaction API - Record Labor Hours");
        Console.WriteLine(new string('=', 60));

        using var client = await P21Client.CreateAsync();

        // Build a test labor entry with today's date
        var entryDate = DateTime.Now.ToString("yyyy-MM-dd");
        var startTime = "08:00";
        var endTime = "12:00";
        var hoursWorked = 4.0;

        Console.WriteLine($"\nRecording labor hours:");
        Console.WriteLine($"  Technician: 300 (a contact ID, not a user ID)");
        Console.WriteLine($"  Production Order: 1000123");
        Console.WriteLine($"  Date: {entryDate}");
        Console.WriteLine($"  Time: {startTime} - {endTime} ({hoursWorked} hours)");
        Console.WriteLine(new string('-', 50));

        // Build the Transaction API payload
        var payload = BuildLaborEntryPayload(
            companyId: "ACME",
            technicianId: "300",          // contact ID, not a user ID
            entryDate: entryDate,
            prodOrderNumber: 1000123,
            itemId: "ASSY-100",           // the assembly line's item
            componentLaborId: "LABOR-SHOP",
            startTime: startTime,
            endTime: endTime,
            timeWorked: hoursWorked,
            laborTypeCd: "Rate"
        );

        Console.WriteLine("\n  Request payload structure:");
        Console.WriteLine($"    Service: {payload["Name"]}");
        Console.WriteLine($"    UseCodeValues: {payload["UseCodeValues"]}");
        Console.WriteLine($"    Transactions: {(payload["Transactions"] as JArray)?.Count}");
        Console.WriteLine($"    DataElements: {((payload["Transactions"] as JArray)?[0]?["DataElements"] as JArray)?.Count}");

        // Print the DataElement details
        var dataElements = (payload["Transactions"] as JArray)?[0]?["DataElements"] as JArray;
        if (dataElements != null)
        {
            foreach (var elem in dataElements)
            {
                var elemName = elem["Name"]?.ToString() ?? "Unknown";
                var rows = elem["Rows"] as JArray;
                Console.WriteLine($"\n    DataElement: {elemName}");
                Console.WriteLine($"      Rows: {rows?.Count ?? 0}");

                if (rows?.Count > 0)
                {
                    var edits = (rows[0] as JObject)?["Edits"] as JArray;
                    if (edits != null)
                    {
                        foreach (var edit in edits)
                        {
                            Console.WriteLine($"        {edit["Name"]}: {edit["Value"]}");
                        }
                    }
                }
            }
        }

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

                if (transactions?.Count > 0)
                {
                    var trans = transactions[0] as JObject;
                    Console.WriteLine($"\n    Transaction Status: {trans?["Status"]}");

                    // Walk the DataElements to find generated keys
                    var laborUid = ExtractFieldValue(trans, "time_entry_uid");
                    if (laborUid != null)
                    {
                        Console.WriteLine($"    Created Time Entry UID: {laborUid}");
                    }

                    var technicianUid = ExtractFieldValue(trans, "technician_uid");
                    if (technicianUid != null)
                    {
                        Console.WriteLine($"    Technician UID: {technicianUid}");
                    }
                }

                Console.WriteLine("\n  SUCCESS: Labor hours recorded!");

                // READ-BACK — the only proof of persistence is reading the
                // entry back. Verify via POST /api/v2/transaction/get
                // (ServiceName "TimeEntry") or an OData query against
                // prod_order_line_comp_labor for this prod_order_number.
                Console.WriteLine("\n  Verify: read the entry back via /transaction/get or OData");
                Console.WriteLine("  (prod_order_line_comp_labor) before trusting the write.");
            }
            else
            {
                Console.WriteLine("\n  FAILED: Labor entry not created");
                Console.WriteLine("    Check messages above for details");

                // Show the raw response for debugging
                if (result.Raw != null)
                {
                    Console.WriteLine("\n  Raw Response (truncated):");
                    var rawStr = result.Raw.ToString(Newtonsoft.Json.Formatting.Indented);
                    Console.WriteLine($"    {rawStr[..Math.Min(500, rawStr.Length)]}");
                }
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
        Console.WriteLine("Record labor hours example complete!");
        Console.WriteLine("\nNote: This example uses test data (ACME/300/1000123).");
        Console.WriteLine("Adjust company_id, technician_id (a contact ID), and");
        Console.WriteLine("prod_order_number for your environment.");
    }

    /// <summary>
    /// Build a Transaction API payload for recording labor hours via TimeEntry.
    ///
    /// Field order in the labor grid is STRICT (see docs/12-Production-Labor-API.md,
    /// "Time Entry Against a Production Order (Quick Time Entry)"):
    /// prod_order_number -> item_id -> component_labor_id -> start_time -> end_time.
    /// Out of order, the downstream fields stay disabled.
    /// </summary>
    /// <param name="companyId">Company ID (e.g., "ACME").</param>
    /// <param name="technicianId">Technician ID — a CONTACT ID (e.g., "300"), not a user ID.</param>
    /// <param name="entryDate">Date of the labor entry (yyyy-MM-dd). The accounting period must be open.</param>
    /// <param name="prodOrderNumber">Production order number.</param>
    /// <param name="itemId">The assembly line's item ID (e.g., "ASSY-100").</param>
    /// <param name="componentLaborId">Labor component ID (e.g., "LABOR-SHOP").</param>
    /// <param name="startTime">Start time (HH:mm).</param>
    /// <param name="endTime">End time (HH:mm).</param>
    /// <param name="timeWorked">Total hours worked (decimal).</param>
    /// <param name="laborTypeCd">Labor type code (e.g., "Rate").</param>
    public static JObject BuildLaborEntryPayload(
        string companyId,
        string technicianId,
        string entryDate,
        int prodOrderNumber,
        string itemId,
        string componentLaborId,
        string startTime,
        string endTime,
        double timeWorked,
        string laborTypeCd = "Rate")
    {
        return new JObject
        {
            ["Name"] = "TimeEntry",
            ["UseCodeValues"] = false,
            ["Transactions"] = new JArray
            {
                new JObject
                {
                    ["Status"] = "New",
                    ["DataElements"] = new JArray
                    {
                        // TP_TECHNICIAN — Technician header with company and date
                        new JObject
                        {
                            ["Name"] = "TP_TECHNICIAN.tp_technician",
                            ["Type"] = "Form",
                            ["Keys"] = new JArray(),
                            ["Rows"] = new JArray
                            {
                                new JObject
                                {
                                    ["Edits"] = new JArray
                                    {
                                        new JObject { ["Name"] = "company_id", ["Value"] = companyId },
                                        new JObject { ["Name"] = "technician_id", ["Value"] = technicianId },
                                        new JObject { ["Name"] = "entry_date", ["Value"] = entryDate }
                                    },
                                    ["RelativeDateEdits"] = new JArray()
                                }
                            }
                        },
                        // TP_LABORRECORDING — Labor line with production order details
                        new JObject
                        {
                            ["Name"] = "TP_LABORRECORDING.prod_order_line_comp_labor",
                            ["Type"] = "List",
                            ["Keys"] = new JArray(),
                            ["Rows"] = new JArray
                            {
                                new JObject
                                {
                                    // STRICT edit order (docs/12, Quick Time Entry):
                                    // prod_order_number -> item_id -> component_labor_id
                                    // -> start_time -> end_time. Downstream fields stay
                                    // disabled if entered out of order.
                                    ["Edits"] = new JArray
                                    {
                                        // Value is always a STRING in Transaction API payloads
                                        new JObject { ["Name"] = "prod_order_number", ["Value"] = prodOrderNumber.ToString(CultureInfo.InvariantCulture) },
                                        new JObject { ["Name"] = "item_id", ["Value"] = itemId },
                                        new JObject { ["Name"] = "component_labor_id", ["Value"] = componentLaborId },
                                        new JObject { ["Name"] = "start_time", ["Value"] = startTime },
                                        new JObject { ["Name"] = "end_time", ["Value"] = endTime },
                                        new JObject { ["Name"] = "time_worked", ["Value"] = FormatTimeWorked(timeWorked) },
                                        new JObject { ["Name"] = "labor_type_cd", ["Value"] = laborTypeCd }
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
    /// Format decimal hours as HH:MM string for the time_worked field.
    /// </summary>
    internal static string FormatTimeWorked(double hours)
    {
        var totalMinutes = (int)(hours * 60);
        var h = totalMinutes / 60;
        var m = totalMinutes % 60;
        return $"{h}:{m:D2}";
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
