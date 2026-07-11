using System.Globalization;
using System.Net.Http;
using System.Text;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using P21Examples.Common;
using P21Examples.Common.Models;

namespace P21Examples.Interactive;

/// <summary>
/// Interactive API - Save and Close (v2)
///
/// Demonstrates a complete workflow: open, modify, save, and close.
///
/// This is the typical pattern for creating records via the Interactive API.
///
/// IMPORTANT: As of P21 25.2, DatawindowName is REQUIRED in change requests.
///
/// Mirrors: examples/python/interactive/04_save_and_close.py
/// </summary>
public static class SaveAndClose
{
    public static async Task RunAsync()
    {
        Console.WriteLine("Interactive API - Save and Close (v2)");
        Console.WriteLine(new string('=', 60));

        using var client = await P21Client.CreateAsync();

        await using var session = client.Interactive.CreateSession(responseWindows: false);

        try
        {
            // Start session
            Console.WriteLine("\n1. Starting session...");
            await session.StartAsync();
            Console.WriteLine("  Session started");

            // Create a price page
            var timestamp = DateTime.Now.ToString("HHmmss");
            var description = $"IAPI-SAVE-{timestamp}";

            Console.WriteLine($"\n2. Creating price page: {description}");
            Console.WriteLine(new string('-', 50));

            var success = await CreatePricePageAsync(session, new PricePageParams
            {
                SupplierId = 10,
                ProductGroup = "MISC",
                Description = description,
                Multiplier = 0.80
            });

            if (success)
            {
                Console.WriteLine($"\n  SUCCESS: Price page created!");
                Console.WriteLine($"  Description: {description}");
            }
            else
            {
                Console.WriteLine("\n  Price page not created (save failed or dry run)");
            }
        }
        catch (HttpRequestException ex)
        {
            Console.WriteLine($"\n  HTTP Error: {ex.StatusCode}");
            Console.WriteLine($"  {ex.Message}");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"\n  Error: {ex.GetType().Name}: {ex.Message}");
        }

        // Session ends automatically via DisposeAsync

        // ==================================================================
        // RAW HTTP APPROACH — full create workflow
        // ==================================================================
        Console.WriteLine("\n--- Raw HTTP approach ---");
        await RunRawHttpDemoAsync();

        Console.WriteLine("\n" + new string('=', 60));
        Console.WriteLine("Save and close workflow complete!");
    }

    /// <summary>
    /// Parameters for creating a price page.
    /// </summary>
    private class PricePageParams
    {
        public int SupplierId { get; set; }
        public string ProductGroup { get; set; } = "";
        public string Description { get; set; } = "";
        public double Multiplier { get; set; }
    }

    /// <summary>
    /// Create a price page using the high-level InteractiveWindow API.
    ///
    /// This demonstrates the complete workflow:
    /// 1. Open window
    /// 2. Set page type
    /// 3. Fill in form fields
    /// 4. Change to VALUES tab
    /// 5. Set calculation fields
    /// 6. Save
    /// 7. Close window
    /// </summary>
    private static async Task<bool> CreatePricePageAsync(
        InteractiveSession session, PricePageParams p)
    {
        InteractiveWindow? window = null;

        try
        {
            // Step 1: Open window
            window = await session.OpenWindowAsync(serviceName: "SalesPricePage");
            Console.WriteLine($"    Window ID: {window.WindowId}");

            // Step 2: Set page type first (triggers validation rules)
            await window.ChangeDataAsync("FORM", "price_page_type_cd",
                "Supplier / Product Group", "form");

            // Step 3: Fill in required fields (order matters!)
            await window.ChangeDataAsync("FORM", "company_id", "ACME", "form");
            await window.ChangeDataAsync("FORM", "product_group_id", p.ProductGroup, "form");
            await window.ChangeDataAsync("FORM", "supplier_id", p.SupplierId.ToString(), "form");

            // Set remaining fields in batch
            await window.ChangeFieldsAsync("FORM", new Dictionary<string, string>
            {
                ["description"] = p.Description,
                ["pricing_method_cd"] = "Source",
                ["source_price_cd"] = "Supplier List Price",
                ["effective_date"] = DateTime.Now.ToString("yyyy-MM-dd"),
                ["expiration_date"] = "2030-12-31",
                ["row_status_flag"] = "Active"
            }, datawindowName: "form");

            // Step 4: Switch to VALUES tab
            await window.SelectTabAsync("VALUES");

            // Step 5: Set calculation method and value
            await window.ChangeFieldsAsync("VALUES", new Dictionary<string, string>
            {
                ["calculation_method_cd"] = "Multiplier",
                ["calculation_value1"] = p.Multiplier.ToString("F2", CultureInfo.InvariantCulture)
            }, datawindowName: "d_values");

            // Step 6: Save — WRITE SAFETY gate first.
            Console.WriteLine($"    About to SAVE price page '{p.Description}' " +
                              $"(supplier {p.SupplierId}, group {p.ProductGroup}, " +
                              $"multiplier {p.Multiplier.ToString("F2", CultureInfo.InvariantCulture)})");
            if (!ConfirmExecute())
            {
                await window.CloseAsync();
                window = null;
                return false;
            }

            // v2 save sends just the window ID string as the body, not an object.
            var saveResult = await window.SaveDataAsync();

            // Check for blocked status (Status 3 = dialog opened)
            if (saveResult.Status == 3)
            {
                throw new InvalidOperationException(
                    "Save blocked by response window - manual intervention needed");
            }

            if (saveResult.Status == 2)
            {
                var messages = string.Join("; ", saveResult.Messages);
                Console.WriteLine($"    Save returned Failure: {messages}");
                return false;
            }

            // Get saved data to confirm. NOTE: save status alone is not
            // proof of persistence — verify with an independent read-back
            // (OData or /transaction/get). See docs/04-Interactive-API.md,
            // "Verifying Writes (Don't Trust Save Status Alone)".
            var data = await window.GetDataAsync();
            Console.WriteLine($"    Data saved (Status: {data.Status})");
            Console.WriteLine("    Verify with an independent read-back (see docs/04, Verifying Writes)");

            // Step 7: Close window
            await window.CloseAsync();
            window = null; // Prevent double-close in finally

            return true;
        }
        catch
        {
            // Ensure window is closed on error
            if (window != null)
            {
                try { await window.CloseAsync(); }
                catch { /* cleanup */ }
            }
            throw;
        }
    }

    /// <summary>
    /// Raw HTTP approach showing the full save workflow.
    /// </summary>
    private static async Task RunRawHttpDemoAsync()
    {
        var config = P21Config.FromEnvironment();
        var handler = new HttpClientHandler();
        if (!config.VerifySsl)
        {
            handler.ServerCertificateCustomValidationCallback =
                HttpClientHandler.DangerousAcceptAnyServerCertificateValidator;
        }

        using var http = new HttpClient(handler) { Timeout = TimeSpan.FromSeconds(60) };

        var token = await P21Auth.GetTokenAsync(http, config);
        P21Auth.SetAuthHeaders(http, token.AccessToken);
        var uiServerUrl = await P21Auth.GetUiServerUrlAsync(http, config.BaseUrl);

        string? windowId = null;

        try
        {
            // Start session
            Console.WriteLine("\n1. Starting session...");
            await PostJsonAsync(http, $"{uiServerUrl}/api/ui/interactive/sessions",
                new { ResponseWindowHandlingEnabled = false });
            Console.WriteLine("  Session started");

            // Open window
            Console.WriteLine("\n2. Opening window...");
            var windowData = await PostJsonAsync(http,
                $"{uiServerUrl}/api/ui/interactive/v2/window",
                new { ServiceName = "SalesPricePage" });
            windowId = windowData["WindowId"]?.ToString();
            Console.WriteLine($"  Window ID: {windowId}");

            var timestamp = DateTime.Now.ToString("HHmmss");

            // Change data — set page type
            Console.WriteLine("\n3. Setting fields (raw HTTP)...");

            await PutChangeAsync(http, uiServerUrl, windowId!, new[]
            {
                new { TabName = "FORM", DatawindowName = "form",
                      FieldName = "price_page_type_cd", Value = "Supplier / Product Group" }
            });
            Console.WriteLine("  Set price_page_type_cd");

            await PutChangeAsync(http, uiServerUrl, windowId!, new[]
            {
                new { TabName = "FORM", DatawindowName = "form",
                      FieldName = "company_id", Value = "ACME" },
                new { TabName = "FORM", DatawindowName = "form",
                      FieldName = "supplier_id", Value = "10" },
                new { TabName = "FORM", DatawindowName = "form",
                      FieldName = "product_group_id", Value = "MISC" },
                new { TabName = "FORM", DatawindowName = "form",
                      FieldName = "description", Value = $"IAPI-RAW-{timestamp}" },
            });
            Console.WriteLine("  Set company, supplier, product group, description");

            // Change tab
            Console.WriteLine("\n4. Switching to VALUES tab...");
            await PutJsonAsync(http, $"{uiServerUrl}/api/ui/interactive/v2/tab",
                new { WindowId = windowId, PageName = "VALUES" });
            Console.WriteLine("  Tab changed");

            // Set calculation values
            await PutChangeAsync(http, uiServerUrl, windowId!, new[]
            {
                new { TabName = "VALUES", DatawindowName = "d_values",
                      FieldName = "calculation_method_cd", Value = "Multiplier" },
                new { TabName = "VALUES", DatawindowName = "d_values",
                      FieldName = "calculation_value1", Value = "0.80" },
            });
            Console.WriteLine("  Set calculation fields");

            // Save — WRITE SAFETY gate first.
            // PUT /api/ui/interactive/v2/data
            // Body: bare GUID string (not an object!) — e.g., "\"abc-123-...\""
            Console.WriteLine("\n5. Saving...");
            Console.WriteLine($"  About to SAVE price page 'IAPI-RAW-{timestamp}'");
            if (!ConfirmExecute())
                return;  // finally block closes the window and ends the session

            var saveContent = new StringContent(
                JsonConvert.SerializeObject(windowId),  // Serializes as "\"guid-string\""
                Encoding.UTF8,
                "application/json");

            var saveResp = await http.PutAsync(
                $"{uiServerUrl}/api/ui/interactive/v2/data", saveContent);
            saveResp.EnsureSuccessStatusCode();

            var saveBody = await saveResp.Content.ReadAsStringAsync();
            var saveResult = JObject.Parse(saveBody);
            var status = saveResult["Status"]?.Value<int>() ?? 0;
            Console.WriteLine($"  Save status: {status} (1=Success, 2=Failure, 3=Blocked)");

            if (status == 3)
                Console.WriteLine("  WARNING: Save blocked by response window!");

            // Save status alone is not proof of persistence — verify with an
            // independent read-back (OData or /transaction/get). See
            // docs/04-Interactive-API.md, "Verifying Writes (Don't Trust
            // Save Status Alone)".
            Console.WriteLine("  Verify with an independent read-back (see docs/04, Verifying Writes)");

            // Close window
            Console.WriteLine("\n6. Closing window...");
            await http.DeleteAsync(
                $"{uiServerUrl}/api/ui/interactive/v2/window?id={windowId}");
            windowId = null;
            Console.WriteLine("  Window closed");
        }
        catch (HttpRequestException ex)
        {
            Console.WriteLine($"\n  HTTP Error: {ex.StatusCode}");
            Console.WriteLine($"  {ex.Message}");
        }
        finally
        {
            if (windowId != null)
            {
                try
                {
                    await http.DeleteAsync(
                        $"{uiServerUrl}/api/ui/interactive/v2/window?id={windowId}");
                }
                catch { /* cleanup */ }
            }

            try
            {
                await http.DeleteAsync($"{uiServerUrl}/api/ui/interactive/sessions");
                Console.WriteLine("  Session ended");
            }
            catch { /* cleanup */ }
        }
    }

    /// <summary>
    /// WRITE SAFETY gate (same pattern as Recipes/RecipeHelpers.ConfirmExecute).
    /// Returns true only when the user types EXECUTE; anything else = dry run.
    /// </summary>
    internal static bool ConfirmExecute()
    {
        Console.WriteLine();
        Console.Write("Type EXECUTE to save, anything else = dry run: ");
        var answer = Console.ReadLine()?.Trim();
        if (answer == "EXECUTE")
            return true;

        Console.WriteLine("Dry run - nothing was saved.");
        return false;
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
