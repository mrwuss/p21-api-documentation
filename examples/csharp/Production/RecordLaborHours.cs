// Transaction API - Record Labor Hours
//
// Demonstrates recording labor hours against a production order using the
// TimeEntry Transaction API service.
// Mirrors: scripts/transaction/03_create_single.py (adapted for TimeEntry)
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
        Console.WriteLine($"  Technician: TECH001");
        Console.WriteLine($"  Production Order: 1001");
        Console.WriteLine($"  Date: {entryDate}");
        Console.WriteLine($"  Time: {startTime} - {endTime} ({hoursWorked} hours)");
        Console.WriteLine(new string('-', 50));

        // Build the Transaction API payload
        var payload = BuildLaborEntryPayload(
            companyId: "ACME",
            technicianId: "TECH001",
            entryDate: entryDate,
            prodOrderNumber: 1001,
            serviceLaborId: "LABOR01",
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
        Console.WriteLine("\nNote: This example uses test data (ACME/TECH001/1001).");
        Console.WriteLine("Adjust company_id, technician_id, and prod_order_number for your environment.");
    }

    /// <summary>
    /// Build a Transaction API payload for recording labor hours via TimeEntry.
    /// </summary>
    /// <param name="companyId">Company ID (e.g., "ACME").</param>
    /// <param name="technicianId">Technician ID (e.g., "TECH001").</param>
    /// <param name="entryDate">Date of the labor entry (yyyy-MM-dd).</param>
    /// <param name="prodOrderNumber">Production order number.</param>
    /// <param name="serviceLaborId">Service/labor ID (e.g., "LABOR01").</param>
    /// <param name="startTime">Start time (HH:mm).</param>
    /// <param name="endTime">End time (HH:mm).</param>
    /// <param name="timeWorked">Total hours worked (decimal).</param>
    /// <param name="laborTypeCd">Labor type code (e.g., "Rate").</param>
    public static JObject BuildLaborEntryPayload(
        string companyId,
        string technicianId,
        string entryDate,
        int prodOrderNumber,
        string serviceLaborId,
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
                                    ["Edits"] = new JArray
                                    {
                                        new JObject { ["Name"] = "prod_order_number", ["Value"] = (double)prodOrderNumber },
                                        new JObject { ["Name"] = "service_labor_id", ["Value"] = serviceLaborId },
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
