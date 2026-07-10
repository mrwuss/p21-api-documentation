// Transaction API - Async Operations
//
// Demonstrates using the async endpoint for long-running operations.
// Mirrors: examples/python/transaction/06_async_operations.py
//
// The async endpoint:
//   POST /api/v2/transaction/async     - Submit transaction, get request ID
//   GET  /api/v2/transaction/async?id= - Poll for completion status
//
// Benefits:
//   - Immediately returns a request ID (non-blocking)
//   - Processes the transaction in a background session
//   - Uses a dedicated session (avoids session pool contamination)
//   - Supports callback URLs for notification on completion

using Newtonsoft.Json.Linq;
using P21Examples.Common;

namespace P21Examples.Transaction;

/// <summary>
/// Demonstrates the async Transaction API endpoint for long-running
/// operations. Shows submission, polling, and callback structure.
/// </summary>
public static class AsyncOperations
{
    public static async Task RunAsync()
    {
        Console.WriteLine("Transaction API - Async Operations");
        Console.WriteLine(new string('=', 60));

        using var client = await P21Client.CreateAsync();

        // -----------------------------------------------------------------
        // Example 1: Submit async request
        // -----------------------------------------------------------------
        Console.WriteLine("\n1. Submit async transaction:");
        Console.WriteLine(new string('-', 50));

        var payload = BuildTestPayload();
        Console.WriteLine("  Submitting async request for: SalesPricePage");

        try
        {
            // P21Client.Transaction.CreateAsyncOperation wraps POST /api/v2/transaction/async
            var result = await client.Transaction.CreateAsyncOperation(payload);

            var requestId = result["RequestId"]?.ToString();
            var status = result["Status"]?.ToString();

            Console.WriteLine("\n  Async Request Submitted:");
            Console.WriteLine($"    Request ID: {requestId}");
            Console.WriteLine($"    Initial Status: {status}");

            if (string.IsNullOrEmpty(requestId))
            {
                Console.WriteLine("  Error: No request ID returned");
                return;
            }

            // -----------------------------------------------------------------
            // Example 2: Poll for completion
            // -----------------------------------------------------------------
            Console.WriteLine("\n\n2. Polling for completion:");
            Console.WriteLine(new string('-', 50));

            var finalStatus = await WaitForCompletionAsync(
                client,
                requestId,
                timeoutSeconds: 60,
                pollIntervalSeconds: 2
            );

            Console.WriteLine("\n  Final Result:");
            Console.WriteLine($"    Request ID: {finalStatus["RequestId"]}");
            Console.WriteLine($"    Status: {finalStatus["Status"]}");
            Console.WriteLine($"    Completed: {finalStatus["CompletedDate"] ?? "N/A"}");

            var messages = finalStatus["Messages"]?.ToString();
            if (!string.IsNullOrEmpty(messages))
            {
                // Messages may contain the full result or error details
                var preview = messages.Length > 200 ? messages[..200] + "..." : messages;
                Console.WriteLine($"    Messages: {preview}");
            }
        }
        catch (HttpRequestException ex)
        {
            Console.WriteLine($"\n  HTTP Error: {ex.StatusCode}");
            Console.WriteLine($"  Message: {ex.Message[..Math.Min(500, ex.Message.Length)]}");
        }
        catch (TimeoutException ex)
        {
            Console.WriteLine($"\n  Timeout: {ex.Message}");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"\n  Error: {ex.GetType().Name}: {ex.Message}");
        }

        // -----------------------------------------------------------------
        // Example 3: Show callback structure (documentation only)
        // -----------------------------------------------------------------
        Console.WriteLine("\n\n3. Async with Callback (structure only):");
        Console.WriteLine(new string('-', 50));
        Console.WriteLine("  For long-running operations, you can request a callback:");
        Console.WriteLine();
        Console.WriteLine("  POST /api/v2/transaction/async/callback");
        Console.WriteLine("  {");
        Console.WriteLine("    \"Content\": { ... transaction payload ... },");
        Console.WriteLine("    \"Callback\": {");
        Console.WriteLine("      \"Url\": \"https://your-server.com/webhook\",");
        Console.WriteLine("      \"Method\": \"POST\",");
        Console.WriteLine("      \"ContentType\": \"application/json\",");
        Console.WriteLine("      \"Headers\": [");
        Console.WriteLine("        {\"Name\": \"X-API-Key\", \"Value\": \"your-key\"}");
        Console.WriteLine("      ]");
        Console.WriteLine("    }");
        Console.WriteLine("  }");
        Console.WriteLine();
        Console.WriteLine("  The callback receives the AsyncRequest with final status.");

        Console.WriteLine("\n" + new string('=', 60));
        Console.WriteLine("Async operations complete!");
        Console.WriteLine("\nBenefits of async endpoint:");
        Console.WriteLine("- Uses dedicated session (no pool contamination)");
        Console.WriteLine("- Better for long-running operations");
        Console.WriteLine("- Callback support for notification");
        Console.WriteLine("- Request ID for tracking/retry");
    }

    /// <summary>
    /// Build a simple test payload for async submission.
    /// </summary>
    private static JObject BuildTestPayload()
    {
        var timestamp = DateTime.Now.ToString("HHmmssfff");
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
                                        new JObject { ["Name"] = "supplier_id", ["Value"] = 10.0 },
                                        new JObject { ["Name"] = "product_group_id", ["Value"] = "MISC" },
                                        new JObject { ["Name"] = "description", ["Value"] = $"ASYNC-TEST-{timestamp}" },
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
                                        new JObject { ["Name"] = "calculation_value1", ["Value"] = "0.5" }
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
    /// Poll for async request completion with timeout.
    /// </summary>
    /// <param name="client">Authenticated P21Client.</param>
    /// <param name="requestId">The async request ID to poll.</param>
    /// <param name="timeoutSeconds">Maximum seconds to wait.</param>
    /// <param name="pollIntervalSeconds">Seconds between polls.</param>
    /// <returns>The final status response.</returns>
    /// <exception cref="TimeoutException">If the request does not complete in time.</exception>
    private static async Task<JObject> WaitForCompletionAsync(
        P21Client client,
        string requestId,
        int timeoutSeconds = 60,
        int pollIntervalSeconds = 2)
    {
        var deadline = DateTime.UtcNow.AddSeconds(timeoutSeconds);

        while (DateTime.UtcNow < deadline)
        {
            // P21Client.Transaction.GetAsyncStatusAsync wraps GET /api/v2/transaction/async?id=
            var status = await client.Transaction.GetAsyncStatusAsync(requestId);

            var currentStatus = status["Status"]?.ToString() ?? "Unknown";
            Console.WriteLine($"    Status: {currentStatus}");

            if (currentStatus is "Complete" or "Failed")
            {
                return status;
            }

            await Task.Delay(pollIntervalSeconds * 1000);
        }

        throw new TimeoutException(
            $"Request {requestId} did not complete within {timeoutSeconds} seconds");
    }
}
