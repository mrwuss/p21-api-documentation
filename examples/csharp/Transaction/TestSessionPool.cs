// Transaction API - Session Pool Behavior Test
//
// Tests for session pool contamination issues.
// Mirrors: scripts/transaction/test_session_pool.py
//
// This script runs multiple test patterns to diagnose intermittent failures
// caused by dirty session pools:
//   1. Rapid fire requests (no delay)
//   2. Requests with 500ms delay
//   3. Requests with 2000ms delay
//   4. Parallel/concurrent requests
//   5. Random jitter delays
//
// Results help identify:
//   - Alternating success/failure patterns
//   - "Unexpected window" errors (dirty session)
//   - Failure rate vs request timing

using System.Diagnostics;
using System.Net.Http;
using System.Text;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using P21Examples.Common;

namespace P21Examples.Transaction;

/// <summary>
/// Tests P21 Transaction API session pool behavior with various
/// request patterns to detect contamination issues.
/// </summary>
public static class TestSessionPool
{
    /// <summary>
    /// Result of a single API call.
    /// </summary>
    private record TestResult(
        int Attempt,
        string Timestamp,
        int ElapsedMs,
        bool Success,
        int StatusCode,
        string? ErrorType = null,
        string? ErrorMessage = null,
        Dictionary<string, string>? SessionHeaders = null,
        string ResponsePreview = "");

    public static async Task RunAsync()
    {
        Console.WriteLine(new string('=', 70));
        Console.WriteLine("P21 Transaction API - Session Pool Behavior Test");
        Console.WriteLine(new string('=', 70));

        var config = P21Config.FromEnvironment();
        Console.WriteLine($"Server: {config.BaseUrl}");
        Console.WriteLine($"Time: {DateTime.Now:O}");

        // Create an HttpClient for raw control (no P21Client wrapper here,
        // because we need precise timing and header inspection)
        var handler = new HttpClientHandler();
        if (!config.VerifySsl)
        {
            handler.ServerCertificateCustomValidationCallback =
                HttpClientHandler.DangerousAcceptAnyServerCertificateValidator;
        }
        using var http = new HttpClient(handler) { Timeout = TimeSpan.FromSeconds(60) };

        // Authenticate
        var tokenResponse = await P21Auth.GetTokenAsync(http, config);
        P21Auth.SetAuthHeaders(http, tokenResponse.AccessToken);

        var uiServerUrl = await P21Auth.GetUiServerUrlAsync(http, config.BaseUrl);

        // Run all test patterns
        var allResults = new Dictionary<string, List<TestResult>>();

        // TEST 1: Rapid fire
        Console.WriteLine("\n" + new string('=', 70));
        Console.WriteLine("TEST 1: Rapid Fire (10 requests, no delay)");
        Console.WriteLine(new string('=', 70));
        allResults["rapid_fire"] = await RunRapidTestAsync(http, uiServerUrl, count: 10, delayMs: 0);

        await Task.Delay(2000);

        // TEST 2: 500ms delay
        Console.WriteLine("\n" + new string('=', 70));
        Console.WriteLine("TEST 2: With 500ms Delay (10 requests)");
        Console.WriteLine(new string('=', 70));
        allResults["delayed_500ms"] = await RunRapidTestAsync(http, uiServerUrl, count: 10, delayMs: 500);

        await Task.Delay(2000);

        // TEST 3: 2000ms delay
        Console.WriteLine("\n" + new string('=', 70));
        Console.WriteLine("TEST 3: With 2000ms Delay (5 requests)");
        Console.WriteLine(new string('=', 70));
        allResults["delayed_2000ms"] = await RunRapidTestAsync(http, uiServerUrl, count: 5, delayMs: 2000);

        await Task.Delay(2000);

        // TEST 4: Parallel requests
        Console.WriteLine("\n" + new string('=', 70));
        Console.WriteLine("TEST 4: Parallel Requests (5 concurrent)");
        Console.WriteLine(new string('=', 70));
        allResults["parallel"] = await RunParallelTestAsync(http, uiServerUrl, count: 5);

        await Task.Delay(2000);

        // TEST 5: Random jitter
        Console.WriteLine("\n" + new string('=', 70));
        Console.WriteLine("TEST 5: Random Jitter (10 requests, 100-1000ms random delay)");
        Console.WriteLine(new string('=', 70));
        allResults["random_jitter"] = await RunJitterTestAsync(http, uiServerUrl, count: 10);

        // Analyze and print report
        AnalyzeResults(allResults);

        // Save results to JSON file
        SaveResults(allResults);
    }

    /// <summary>
    /// Run sequential requests with a fixed delay between each.
    /// </summary>
    private static async Task<List<TestResult>> RunRapidTestAsync(
        HttpClient http, string uiServerUrl, int count, int delayMs)
    {
        var results = new List<TestResult>();

        for (var i = 0; i < count; i++)
        {
            var result = await MakeRequestAsync(http, uiServerUrl, i + 1);
            results.Add(result);

            var status = result.Success ? "OK" : "FAIL";
            Console.WriteLine($"  [{i + 1,2}] {status} {result.ElapsedMs,4}ms - {Truncate(result.ResponsePreview, 50)}");

            if (delayMs > 0 && i < count - 1)
            {
                await Task.Delay(delayMs);
            }
        }

        return results;
    }

    /// <summary>
    /// Run concurrent/parallel requests to stress test the session pool.
    /// </summary>
    private static async Task<List<TestResult>> RunParallelTestAsync(
        HttpClient http, string uiServerUrl, int count)
    {
        // Launch all requests concurrently
        var tasks = Enumerable.Range(1, count)
            .Select(i => MakeRequestAsync(http, uiServerUrl, i))
            .ToArray();

        var results = await Task.WhenAll(tasks);

        foreach (var result in results)
        {
            var status = result.Success ? "OK" : "FAIL";
            Console.WriteLine($"  [{result.Attempt,2}] {status} {result.ElapsedMs,4}ms - {Truncate(result.ResponsePreview, 50)}");
        }

        return results.ToList();
    }

    /// <summary>
    /// Run requests with random jitter between 100-1000ms.
    /// </summary>
    private static async Task<List<TestResult>> RunJitterTestAsync(
        HttpClient http, string uiServerUrl, int count)
    {
        var results = new List<TestResult>();
        var random = new Random();

        for (var i = 0; i < count; i++)
        {
            var result = await MakeRequestAsync(http, uiServerUrl, i + 1);
            results.Add(result);

            var status = result.Success ? "OK" : "FAIL";
            Console.WriteLine($"  [{i + 1,2}] {status} {result.ElapsedMs,4}ms - {Truncate(result.ResponsePreview, 50)}");

            if (i < count - 1)
            {
                var jitter = random.Next(100, 1001);
                await Task.Delay(jitter);
            }
        }

        return results;
    }

    /// <summary>
    /// Make a single Transaction API request and capture timing/headers.
    /// </summary>
    private static async Task<TestResult> MakeRequestAsync(
        HttpClient http, string uiServerUrl, int attempt)
    {
        var timestamp = DateTime.Now.ToString("O");
        var sw = Stopwatch.StartNew();

        var payload = BuildTestPayload();

        try
        {
            var content = new StringContent(
                JsonConvert.SerializeObject(payload),
                Encoding.UTF8,
                "application/json");

            var response = await http.PostAsync($"{uiServerUrl}/api/v2/transaction", content);

            sw.Stop();
            var elapsedMs = (int)sw.ElapsedMilliseconds;

            // Capture session-related response headers
            var sessionHeaders = new Dictionary<string, string>();
            foreach (var header in response.Headers)
            {
                var key = header.Key.ToLower();
                if (key.Contains("session") || key.Contains("x-p21") ||
                    key.Contains("server") || key.Contains("instance"))
                {
                    sessionHeaders[header.Key] = string.Join(", ", header.Value);
                }
            }

            if (response.IsSuccessStatusCode)
            {
                var body = await response.Content.ReadAsStringAsync();
                var data = JObject.Parse(body);
                var summary = data["Summary"] as JObject;
                var succeeded = summary?["Succeeded"]?.Value<int>() ?? 0;
                var failed = summary?["Failed"]?.Value<int>() ?? 0;
                var messages = data["Messages"] as JArray;

                if (succeeded > 0 && failed == 0)
                {
                    return new TestResult(
                        attempt, timestamp, elapsedMs,
                        Success: true, StatusCode: 200,
                        SessionHeaders: sessionHeaders,
                        ResponsePreview: $"Succeeded: {succeeded}");
                }
                else
                {
                    var errorMsg = messages?.FirstOrDefault()?.ToString() ?? "Unknown error";
                    return new TestResult(
                        attempt, timestamp, elapsedMs,
                        Success: false, StatusCode: 200,
                        ErrorType: "ValidationError",
                        ErrorMessage: Truncate(errorMsg, 200),
                        SessionHeaders: sessionHeaders,
                        ResponsePreview: $"Failed: {failed}, Messages: {messages?.Count ?? 0}");
                }
            }
            else
            {
                var errorText = await response.Content.ReadAsStringAsync();
                var errorType = errorText.Contains("Unexpected response window")
                    ? "UnexpectedWindow"
                    : "HTTPError";

                return new TestResult(
                    attempt, timestamp, elapsedMs,
                    Success: false, StatusCode: (int)response.StatusCode,
                    ErrorType: errorType,
                    ErrorMessage: Truncate(errorText, 200),
                    SessionHeaders: sessionHeaders,
                    ResponsePreview: Truncate(errorText, 100));
            }
        }
        catch (Exception ex)
        {
            sw.Stop();
            return new TestResult(
                attempt, timestamp, (int)sw.ElapsedMilliseconds,
                Success: false, StatusCode: 0,
                ErrorType: ex.GetType().Name,
                ErrorMessage: Truncate(ex.Message, 200));
        }
    }

    /// <summary>
    /// Build a SalesPricePage test payload that should succeed.
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
                                        new JObject { ["Name"] = "description", ["Value"] = $"SESSION-TEST-{timestamp}" },
                                        new JObject { ["Name"] = "pricing_method_cd", ["Value"] = "Source" },
                                        new JObject { ["Name"] = "source_price_cd", ["Value"] = "Supplier List Price" },
                                        new JObject { ["Name"] = "effective_date", ["Value"] = "2025-01-01" },
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
    /// Analyze all test results and print a summary report.
    /// </summary>
    private static void AnalyzeResults(Dictionary<string, List<TestResult>> allResults)
    {
        Console.WriteLine("\n" + new string('=', 70));
        Console.WriteLine("SESSION POOL BEHAVIOR ANALYSIS");
        Console.WriteLine(new string('=', 70));

        var totalRequests = 0;
        var totalFailures = 0;
        var failurePatterns = new Dictionary<string, int>();

        foreach (var (testName, results) in allResults)
        {
            var successes = results.Count(r => r.Success);
            var failures = results.Count - successes;
            totalRequests += results.Count;
            totalFailures += failures;

            Console.WriteLine($"\n{testName.ToUpper()}:");
            Console.WriteLine($"  Total: {results.Count}, Success: {successes}, Failed: {failures}");
            Console.WriteLine($"  Success Rate: {(double)successes / results.Count * 100:F1}%");

            // Track failure patterns
            foreach (var r in results.Where(r => !r.Success))
            {
                var errorKey = r.ErrorType ?? "Unknown";
                failurePatterns.TryGetValue(errorKey, out var count);
                failurePatterns[errorKey] = count + 1;
            }

            // Check for alternating success/failure pattern
            if (results.Count >= 4)
            {
                var pattern = results.Select(r => r.Success).ToList();
                var alternating = true;
                for (var i = 0; i < pattern.Count - 1; i++)
                {
                    if (pattern[i] == pattern[i + 1])
                    {
                        alternating = false;
                        break;
                    }
                }
                if (alternating)
                {
                    Console.WriteLine("  [!] ALTERNATING PATTERN DETECTED!");
                }
            }

            // Check consecutive failures
            var maxConsecutiveFail = 0;
            var currentConsecutive = 0;
            foreach (var r in results)
            {
                if (!r.Success)
                {
                    currentConsecutive++;
                    maxConsecutiveFail = Math.Max(maxConsecutiveFail, currentConsecutive);
                }
                else
                {
                    currentConsecutive = 0;
                }
            }
            if (maxConsecutiveFail > 2)
            {
                Console.WriteLine($"  [!] Max consecutive failures: {maxConsecutiveFail}");
            }
        }

        Console.WriteLine("\n" + new string('-', 70));
        Console.WriteLine("SUMMARY:");
        Console.WriteLine($"  Total Requests: {totalRequests}");
        Console.WriteLine($"  Total Failures: {totalFailures}");
        Console.WriteLine($"  Overall Success Rate: {(double)(totalRequests - totalFailures) / totalRequests * 100:F1}%");

        if (failurePatterns.Count > 0)
        {
            Console.WriteLine("\n  Failure Types:");
            foreach (var (errorType, count) in failurePatterns.OrderByDescending(x => x.Value))
            {
                Console.WriteLine($"    - {errorType}: {count}");
            }
        }

        // Conclusions
        Console.WriteLine("\n" + new string('-', 70));
        Console.WriteLine("CONCLUSIONS:");

        if (totalFailures == 0)
        {
            Console.WriteLine("  [OK] No failures detected - session pool appears healthy");
        }
        else if ((double)totalFailures / totalRequests > 0.3)
        {
            Console.WriteLine("  [!] High failure rate (>30%) - likely session pool contamination");
            Console.WriteLine("  [!] Consider using async endpoint or implementing retry logic");
        }
        else
        {
            Console.WriteLine("  [!] Intermittent failures detected");
            Console.WriteLine("  [!] Pattern suggests session pool issues");
        }

        if (failurePatterns.ContainsKey("UnexpectedWindow"))
        {
            Console.WriteLine("  [!] 'Unexpected window' errors confirm dirty session pool");
            Console.WriteLine("  [!] Previous operations left dialogs open in pooled sessions");
        }
    }

    /// <summary>
    /// Save detailed results to a JSON file.
    /// </summary>
    private static void SaveResults(Dictionary<string, List<TestResult>> allResults)
    {
        var outputFile = Path.Combine(AppContext.BaseDirectory, "session_pool_results.json");

        var jsonResults = new JObject();
        foreach (var (testName, results) in allResults)
        {
            var array = new JArray();
            foreach (var r in results)
            {
                array.Add(new JObject
                {
                    ["attempt"] = r.Attempt,
                    ["timestamp"] = r.Timestamp,
                    ["elapsed_ms"] = r.ElapsedMs,
                    ["success"] = r.Success,
                    ["status_code"] = r.StatusCode,
                    ["error_type"] = r.ErrorType,
                    ["error_message"] = r.ErrorMessage,
                    ["session_headers"] = r.SessionHeaders != null
                        ? JObject.FromObject(r.SessionHeaders)
                        : new JObject()
                });
            }
            jsonResults[testName] = array;
        }

        File.WriteAllText(outputFile, jsonResults.ToString(Formatting.Indented));
        Console.WriteLine($"\nDetailed results saved to: {outputFile}");
    }

    /// <summary>
    /// Truncate a string to a maximum length.
    /// </summary>
    private static string Truncate(string? value, int maxLength)
    {
        if (string.IsNullOrEmpty(value)) return "";
        return value.Length <= maxLength ? value : value[..maxLength];
    }
}
