using System.Net.Http;
using System.Text;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using P21Examples.Common;
using P21Examples.Common.Models;

namespace P21Examples.Interactive;

/// <summary>
/// Interactive API - Complex Workflow (v2)
///
/// Demonstrates a multi-step workflow using the Interactive API v2.
///
/// This example shows:
/// - Context manager / IAsyncDisposable for session cleanup
/// - Error handling at each step
/// - Multiple field changes with DatawindowName (required in P21 25.2+)
/// - Tab switching
/// - Saving with validation checking
///
/// Mirrors: scripts/interactive/06_complex_workflow.py
/// </summary>
public static class ComplexWorkflow
{
    public static async Task RunAsync()
    {
        Console.WriteLine("Interactive API - Complex Workflow (v2)");
        Console.WriteLine(new string('=', 60));

        // ==================================================================
        // HIGH-LEVEL APPROACH — P21Client + InteractiveSession (await using)
        // ==================================================================
        Console.WriteLine("\n--- High-level approach ---");

        using var client = await P21Client.CreateAsync();
        Console.WriteLine($"Authenticated.");

        var timestamp = DateTime.Now.ToString("HHmmss");

        // The session is IAsyncDisposable — 'await using' ensures cleanup
        // even if an exception is thrown (like Python's context manager).
        await using (var session = client.Interactive.CreateSession(responseWindows: false))
        {
            await session.StartAsync();
            Console.WriteLine("\n1. Session started via 'await using'");
            Console.WriteLine(new string('-', 50));

            // Create a single price page
            Console.WriteLine("\n2. Creating single price page:");
            Console.WriteLine(new string('-', 50));

            await CreatePricePageWorkflowAsync(session, new PricePageConfig
            {
                Description = $"WORKFLOW-{timestamp}-A",
                SupplierId = 10,
                ProductGroup = "MISC",
                Multiplier = 0.75
            });

            Console.WriteLine("\n  Price page created successfully!");

            // Could create more records in the same session...

            Console.WriteLine("\n3. Session will end automatically on dispose");
            Console.WriteLine(new string('-', 50));
        }

        Console.WriteLine("  Session ended (disposed).");

        // ==================================================================
        // RAW HTTP APPROACH — self-contained client with manual cleanup
        // ==================================================================
        Console.WriteLine("\n--- Raw HTTP approach (self-contained client) ---");
        await RunRawHttpDemoAsync();

        Console.WriteLine("\n" + new string('=', 60));
        Console.WriteLine("Complex workflow complete!");
        Console.WriteLine();
        Console.WriteLine("Key patterns demonstrated:");
        Console.WriteLine("- 'await using' for automatic session cleanup (IAsyncDisposable)");
        Console.WriteLine("- InteractiveWindow for cleaner field operations");
        Console.WriteLine("- v2 API format with DatawindowName (required in P21 25.2+)");
        Console.WriteLine("- Step-by-step logging for debugging");
        Console.WriteLine("- Error handling at each step");
    }

    // ------------------------------------------------------------------
    // Data types
    // ------------------------------------------------------------------

    private class PricePageConfig
    {
        public string Description { get; set; } = "";
        public int SupplierId { get; set; }
        public string ProductGroup { get; set; } = "";
        public double Multiplier { get; set; }
    }

    // ------------------------------------------------------------------
    // High-level workflow
    // ------------------------------------------------------------------

    /// <summary>
    /// Complete workflow to create a price page using high-level helpers.
    ///
    /// Steps:
    /// 1. Open SalesPricePage window
    /// 2. Set page type
    /// 3. Fill required fields
    /// 4. Switch to VALUES tab
    /// 5. Set calculation values
    /// 6. Save
    /// 7. Close window
    /// </summary>
    private static async Task CreatePricePageWorkflowAsync(
        InteractiveSession session, PricePageConfig p)
    {
        Console.WriteLine($"\n  Creating: {p.Description}");

        // Step 1: Open window
        Console.Write("    Opening window... ");
        var window = await session.OpenWindowAsync(serviceName: "SalesPricePage");
        Console.WriteLine($"OK (ID: {window.WindowId[..Math.Min(20, window.WindowId.Length)]}...)");

        try
        {
            // Step 2: Set page type (triggers validation rules)
            Console.Write("    Setting page type... ");
            await window.ChangeDataAsync("FORM", "price_page_type_cd",
                "Supplier / Product Group", "form");
            Console.WriteLine("OK");

            // Step 3: Fill required fields (order matters for some fields)
            Console.Write("    Setting company... ");
            await window.ChangeDataAsync("FORM", "company_id", "ACME", "form");
            Console.WriteLine("OK");

            Console.Write("    Setting product group... ");
            await window.ChangeDataAsync("FORM", "product_group_id", p.ProductGroup, "form");
            Console.WriteLine("OK");

            Console.Write("    Setting supplier... ");
            await window.ChangeDataAsync("FORM", "supplier_id", p.SupplierId.ToString(), "form");
            Console.WriteLine("OK");

            Console.Write("    Setting remaining fields... ");
            await window.ChangeFieldsAsync("FORM", new Dictionary<string, string>
            {
                ["description"] = p.Description,
                ["pricing_method_cd"] = "Source",
                ["source_price_cd"] = "Supplier List Price",
                ["effective_date"] = DateTime.Now.ToString("yyyy-MM-dd"),
                ["expiration_date"] = "2030-12-31",
                ["row_status_flag"] = "Active"
            }, datawindowName: "form");
            Console.WriteLine("OK");

            // Step 4: Switch to VALUES tab
            Console.Write("    Switching to VALUES tab... ");
            await window.SelectTabAsync("VALUES");
            Console.WriteLine("OK");

            // Step 5: Set calculation values
            Console.Write("    Setting calculation values... ");
            await window.ChangeFieldsAsync("VALUES", new Dictionary<string, string>
            {
                ["calculation_method_cd"] = "Multiplier",
                ["calculation_value1"] = p.Multiplier.ToString("F2")
            }, datawindowName: "d_values");
            Console.WriteLine("OK");

            // Step 6: Save
            Console.Write("    Saving... ");
            var result = await window.SaveDataAsync();

            // Status 3 = Blocked (response window opened)
            if (result.Status == 3)
                throw new InvalidOperationException("Save blocked by response window");

            if (result.Status == 2)
            {
                var messages = string.Join("; ", result.Messages);
                throw new InvalidOperationException($"Save failed: {messages}");
            }

            Console.WriteLine("OK");

            // Step 7: Close window
            Console.Write("    Closing window... ");
            await window.CloseAsync();
            Console.WriteLine("OK");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"FAILED ({ex.Message})");
            try { await window.CloseAsync(); }
            catch { /* cleanup */ }
            throw;
        }
    }

    // ------------------------------------------------------------------
    // Raw HTTP approach — mirrors Python's InteractiveClient context manager
    // ------------------------------------------------------------------

    /// <summary>
    /// Self-contained raw HTTP client that mirrors the Python InteractiveClient
    /// context manager pattern. Shows manual authentication, session management,
    /// and the full create workflow using raw HTTP calls.
    /// </summary>
    private static async Task RunRawHttpDemoAsync()
    {
        var config = P21Config.FromEnvironment();
        Console.WriteLine($"  Server: {config.BaseUrl}");

        var handler = new HttpClientHandler();
        if (!config.VerifySsl)
        {
            handler.ServerCertificateCustomValidationCallback =
                HttpClientHandler.DangerousAcceptAnyServerCertificateValidator;
        }

        using var http = new HttpClient(handler) { Timeout = TimeSpan.FromSeconds(60) };

        // Authenticate (mirrors Python's _authenticate)
        var token = await P21Auth.GetTokenAsync(http, config);
        P21Auth.SetAuthHeaders(http, token.AccessToken);

        // Get UI Server URL (mirrors Python's _get_ui_server)
        var uiServerUrl = await P21Auth.GetUiServerUrlAsync(http, config.BaseUrl);

        // Start session (mirrors Python's _start_session)
        await PostJsonAsync(http, $"{uiServerUrl}/api/ui/interactive/sessions",
            new { ResponseWindowHandlingEnabled = false });

        Console.WriteLine("\n1. Session started (raw HTTP)");
        Console.WriteLine(new string('-', 50));

        string? windowId = null;

        try
        {
            var timestamp = DateTime.Now.ToString("HHmmss");
            var description = $"WORKFLOW-RAW-{timestamp}";
            Console.WriteLine($"\n2. Creating price page: {description}");
            Console.WriteLine(new string('-', 50));

            // Open window
            Console.Write("    Opening window... ");
            var windowData = await PostJsonAsync(http,
                $"{uiServerUrl}/api/ui/interactive/v2/window",
                new { ServiceName = "SalesPricePage" });
            windowId = windowData["WindowId"]?.ToString()!;
            Console.WriteLine($"OK (ID: {windowId[..Math.Min(20, windowId.Length)]}...)");

            // Set page type
            Console.Write("    Setting page type... ");
            await PutChangeAsync(http, uiServerUrl, windowId, new object[]
            {
                new { TabName = "FORM", DatawindowName = "form",
                      FieldName = "price_page_type_cd", Value = "Supplier / Product Group" }
            });
            Console.WriteLine("OK");

            // Set company
            Console.Write("    Setting company... ");
            await PutChangeAsync(http, uiServerUrl, windowId, new object[]
            {
                new { TabName = "FORM", DatawindowName = "form",
                      FieldName = "company_id", Value = "ACME" }
            });
            Console.WriteLine("OK");

            // Set product group
            Console.Write("    Setting product group... ");
            await PutChangeAsync(http, uiServerUrl, windowId, new object[]
            {
                new { TabName = "FORM", DatawindowName = "form",
                      FieldName = "product_group_id", Value = "MISC" }
            });
            Console.WriteLine("OK");

            // Set supplier
            Console.Write("    Setting supplier... ");
            await PutChangeAsync(http, uiServerUrl, windowId, new object[]
            {
                new { TabName = "FORM", DatawindowName = "form",
                      FieldName = "supplier_id", Value = "10" }
            });
            Console.WriteLine("OK");

            // Set remaining fields
            Console.Write("    Setting remaining fields... ");
            await PutChangeAsync(http, uiServerUrl, windowId, new object[]
            {
                new { TabName = "FORM", DatawindowName = "form",
                      FieldName = "description", Value = description },
                new { TabName = "FORM", DatawindowName = "form",
                      FieldName = "pricing_method_cd", Value = "Source" },
                new { TabName = "FORM", DatawindowName = "form",
                      FieldName = "source_price_cd", Value = "Supplier List Price" },
                new { TabName = "FORM", DatawindowName = "form",
                      FieldName = "effective_date", Value = DateTime.Now.ToString("yyyy-MM-dd") },
                new { TabName = "FORM", DatawindowName = "form",
                      FieldName = "expiration_date", Value = "2030-12-31" },
                new { TabName = "FORM", DatawindowName = "form",
                      FieldName = "row_status_flag", Value = "Active" },
            });
            Console.WriteLine("OK");

            // Switch to VALUES tab
            Console.Write("    Switching to VALUES tab... ");
            await PutJsonAsync(http, $"{uiServerUrl}/api/ui/interactive/v2/tab",
                new { WindowId = windowId, PageName = "VALUES" });
            Console.WriteLine("OK");

            // Set calculation values
            Console.Write("    Setting calculation values... ");
            await PutChangeAsync(http, uiServerUrl, windowId, new object[]
            {
                new { TabName = "VALUES", DatawindowName = "d_values",
                      FieldName = "calculation_method_cd", Value = "Multiplier" },
                new { TabName = "VALUES", DatawindowName = "d_values",
                      FieldName = "calculation_value1", Value = "0.75" },
            });
            Console.WriteLine("OK");

            // Save — v2 sends bare GUID string body
            Console.Write("    Saving... ");
            var saveContent = new StringContent(
                JsonConvert.SerializeObject(windowId),
                Encoding.UTF8, "application/json");
            var saveResp = await http.PutAsync(
                $"{uiServerUrl}/api/ui/interactive/v2/data", saveContent);
            saveResp.EnsureSuccessStatusCode();

            var saveBody = await saveResp.Content.ReadAsStringAsync();
            var saveResult = JObject.Parse(saveBody);
            var status = saveResult["Status"]?.Value<int>() ?? 0;

            if (status == 3)
                throw new InvalidOperationException("Save blocked by response window");

            Console.WriteLine("OK");

            // Close window
            Console.Write("    Closing window... ");
            await http.DeleteAsync(
                $"{uiServerUrl}/api/ui/interactive/v2/window?id={windowId}");
            windowId = null;
            Console.WriteLine("OK");

            Console.WriteLine($"\n  Price page '{description}' created successfully!");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"FAILED ({ex.Message})");
            if (windowId != null)
            {
                try
                {
                    await http.DeleteAsync(
                        $"{uiServerUrl}/api/ui/interactive/v2/window?id={windowId}");
                }
                catch { /* cleanup */ }
            }
        }
        finally
        {
            // End session (mirrors Python's __exit__ / _end_session)
            Console.WriteLine("\n3. Ending session...");
            try
            {
                await http.DeleteAsync($"{uiServerUrl}/api/ui/interactive/sessions");
                Console.WriteLine("  Session ended");
            }
            catch { /* cleanup */ }
        }
    }

    // ---------------------------------------------------------------
    // Raw HTTP helpers
    // ---------------------------------------------------------------

    private static async Task<JObject> PostJsonAsync(
        HttpClient http, string url, object payload)
    {
        var content = new StringContent(
            JsonConvert.SerializeObject(payload), Encoding.UTF8, "application/json");
        var resp = await http.PostAsync(url, content);
        resp.EnsureSuccessStatusCode();
        var body = await resp.Content.ReadAsStringAsync();
        return JObject.Parse(body);
    }

    private static async Task<JObject> PutJsonAsync(
        HttpClient http, string url, object payload)
    {
        var content = new StringContent(
            JsonConvert.SerializeObject(payload), Encoding.UTF8, "application/json");
        var resp = await http.PutAsync(url, content);
        resp.EnsureSuccessStatusCode();
        var body = await resp.Content.ReadAsStringAsync();
        return JObject.Parse(body);
    }

    private static async Task<JObject> PutChangeAsync(
        HttpClient http, string uiServerUrl, string windowId, object changes)
    {
        return await PutJsonAsync(http,
            $"{uiServerUrl}/api/ui/interactive/v2/change",
            new { WindowId = windowId, List = changes });
    }
}
