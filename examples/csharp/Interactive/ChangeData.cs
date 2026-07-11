using System.Net.Http;
using System.Text;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using P21Examples.Common;
using P21Examples.Common.Models;

namespace P21Examples.Interactive;

/// <summary>
/// Interactive API - Change Data (v2)
///
/// Demonstrates changing field values in P21 windows using the v2 API.
///
/// To change data you need:
/// 1. Window ID (from opening the window)
/// 2. Tab name (tab page containing the field)
/// 3. DataWindow name (from SQL Information dialog in P21)
/// 4. Field name (column name from SQL Information)
/// 5. New value
///
/// IMPORTANT: As of P21 25.2, DatawindowName is REQUIRED in change requests.
/// The 3-parameter form (TabName + FieldName + Value) no longer works.
///
/// Mirrors: examples/python/interactive/03_change_data.py
/// </summary>
public static class ChangeData
{
    public static async Task RunAsync()
    {
        Console.WriteLine("Interactive API - Change Data (v2)");
        Console.WriteLine(new string('=', 60));

        using var client = await P21Client.CreateAsync();

        // ==================================================================
        // HIGH-LEVEL APPROACH — InteractiveWindow helpers
        // ==================================================================
        Console.WriteLine("\n--- High-level approach ---");

        await using var session = client.Interactive.CreateSession(responseWindows: false);
        InteractiveWindow? window = null;

        try
        {
            // Start session
            Console.WriteLine("\n1. Starting session...");
            await session.StartAsync();
            Console.WriteLine("  Session started");

            // Open window
            Console.WriteLine("\n2. Opening SalesPricePage window...");
            window = await session.OpenWindowAsync(serviceName: "SalesPricePage");
            Console.WriteLine($"  Window ID: {window.WindowId}");

            // Example 1: Change a single field
            // ChangeDataAsync takes tab, field, value, and datawindow name.
            // DatawindowName is REQUIRED in P21 25.2+.
            Console.WriteLine("\n3. Changing single field:");
            Console.WriteLine(new string('-', 50));

            var result = await window.ChangeDataAsync(
                tabName: "FORM",
                fieldName: "price_page_type_cd",
                value: "Supplier / Product Group",
                datawindowName: "form");

            Console.WriteLine($"  Changed price_page_type_cd");
            Console.WriteLine($"  Status: {result.Status} (1=Success, 2=Failure)");

            // Example 2: Change multiple fields in one request
            // ChangeFieldsAsync sends all fields on the same tab/datawindow.
            Console.WriteLine("\n4. Changing multiple fields (same tab/datawindow):");
            Console.WriteLine(new string('-', 50));

            var timestamp = DateTime.Now.ToString("HHmmss");
            var fields = new Dictionary<string, string>
            {
                ["company_id"] = "ACME",
                ["supplier_id"] = "10",
                ["product_group_id"] = "MISC",
                ["description"] = $"IAPI-TEST-{timestamp}"
            };

            result = await window.ChangeFieldsAsync(
                tabName: "FORM",
                fields: fields,
                datawindowName: "form");

            Console.WriteLine($"  Changed {fields.Count} fields");
            Console.WriteLine($"  Status: {result.Status}");
            foreach (var kvp in fields)
            {
                Console.WriteLine($"    {kvp.Key}: {kvp.Value}");
            }

            // Example 3: Change tab, then change fields on new tab
            Console.WriteLine("\n5. Changing to VALUES tab:");
            Console.WriteLine(new string('-', 50));

            result = await window.SelectTabAsync("VALUES");
            Console.WriteLine($"  Tab changed to VALUES");
            Console.WriteLine($"  Status: {result.Status}");

            // Change fields on the VALUES tab using a different datawindow name
            result = await window.ChangeFieldsAsync(
                tabName: "VALUES",
                fields: new Dictionary<string, string>
                {
                    ["calculation_method_cd"] = "Multiplier",
                    ["calculation_value1"] = "0.75"
                },
                datawindowName: "d_values");

            Console.WriteLine($"  Changed calculation fields");
            Console.WriteLine($"  Status: {result.Status}");

            // Get current data
            Console.WriteLine("\n6. Getting current window data:");
            Console.WriteLine(new string('-', 50));

            var dataResult = await window.GetDataAsync();
            Console.WriteLine($"  Retrieved data for window {window.WindowId}");
            Console.WriteLine($"  Status: {dataResult.Status}");

            // Note: Not saving - just demonstrating change operations
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
        finally
        {
            Console.WriteLine("\n7. Cleanup:");
            Console.WriteLine(new string('-', 50));

            if (window != null)
            {
                try
                {
                    await window.CloseAsync();
                    Console.WriteLine("  Window closed");
                }
                catch { /* cleanup */ }
            }
            // Session ends via DisposeAsync
        }

        // ==================================================================
        // RAW HTTP APPROACH — showing exact v2 change payloads
        // ==================================================================
        Console.WriteLine("\n--- Raw HTTP approach ---");
        await RunRawHttpDemoAsync();

        // ------------------------------------------------------------------
        // Reference
        // ------------------------------------------------------------------
        Console.WriteLine("\n" + new string('=', 60));
        Console.WriteLine("Change data examples complete!");
        Console.WriteLine();
        Console.WriteLine("To find field and datawindow names in P21:");
        Console.WriteLine("1. Right-click on field in P21 web client");
        Console.WriteLine("2. Select Help > SQL Information");
        Console.WriteLine("3. Note the DataWindow and Column names");
        Console.WriteLine();
        Console.WriteLine("IMPORTANT: As of P21 25.2, DatawindowName is required");
        Console.WriteLine("in all change requests (3-param form no longer works).");
    }

    /// <summary>
    /// Raw HTTP approach showing exact v2 change request payloads.
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

        using var http = new HttpClient(handler) { Timeout = TimeSpan.FromSeconds(30) };

        var token = await P21Auth.GetTokenAsync(http, config);
        P21Auth.SetAuthHeaders(http, token.AccessToken);
        var uiServerUrl = await P21Auth.GetUiServerUrlAsync(http, config.BaseUrl);

        string? windowId = null;

        try
        {
            // Start session
            Console.WriteLine("\n1. Starting session...");
            var sessionPayload = JsonConvert.SerializeObject(
                new { ResponseWindowHandlingEnabled = false });
            var resp = await http.PostAsync(
                $"{uiServerUrl}/api/ui/interactive/sessions",
                new StringContent(sessionPayload, Encoding.UTF8, "application/json"));
            resp.EnsureSuccessStatusCode();
            Console.WriteLine("  Session started");

            // Open window
            Console.WriteLine("\n2. Opening window...");
            var windowPayload = JsonConvert.SerializeObject(
                new { ServiceName = "SalesPricePage" });
            resp = await http.PostAsync(
                $"{uiServerUrl}/api/ui/interactive/v2/window",
                new StringContent(windowPayload, Encoding.UTF8, "application/json"));
            resp.EnsureSuccessStatusCode();

            var windowBody = await resp.Content.ReadAsStringAsync();
            windowId = JObject.Parse(windowBody)["WindowId"]?.ToString();
            Console.WriteLine($"  Window ID: {windowId}");

            // Change data using v2 format
            // PUT /api/ui/interactive/v2/change
            // Body: {"WindowId": "...", "List": [{TabName, DatawindowName, FieldName, Value}]}
            Console.WriteLine("\n3. Changing data (raw v2 payload):");
            Console.WriteLine(new string('-', 50));

            var timestamp = DateTime.Now.ToString("HHmmss");

            // Build the exact v2 change payload
            var changePayload = new
            {
                WindowId = windowId,
                List = new[]
                {
                    new { TabName = "FORM", DatawindowName = "form",
                          FieldName = "price_page_type_cd", Value = "Supplier / Product Group" }
                }
            };

            var changeJson = JsonConvert.SerializeObject(changePayload);
            Console.WriteLine($"  Payload: {changeJson}");

            resp = await http.PutAsync(
                $"{uiServerUrl}/api/ui/interactive/v2/change",
                new StringContent(changeJson, Encoding.UTF8, "application/json"));
            resp.EnsureSuccessStatusCode();

            var changeBody = await resp.Content.ReadAsStringAsync();
            var changeResult = JObject.Parse(changeBody);
            Console.WriteLine($"  Status: {changeResult["Status"]}");

            // Change tab
            // PUT /api/ui/interactive/v2/tab
            // Body: {"WindowId": "...", "PageName": "VALUES"}
            Console.WriteLine("\n4. Changing tab (raw HTTP):");
            Console.WriteLine(new string('-', 50));

            var tabPayload = JsonConvert.SerializeObject(
                new { WindowId = windowId, PageName = "VALUES" });

            resp = await http.PutAsync(
                $"{uiServerUrl}/api/ui/interactive/v2/tab",
                new StringContent(tabPayload, Encoding.UTF8, "application/json"));
            resp.EnsureSuccessStatusCode();

            var tabBody = await resp.Content.ReadAsStringAsync();
            var tabResult = JObject.Parse(tabBody);
            Console.WriteLine($"  Tab changed to VALUES");
            Console.WriteLine($"  Status: {tabResult["Status"]}");

            // Get data
            // GET /api/ui/interactive/v2/data?id={windowId}
            Console.WriteLine("\n5. Getting data (raw HTTP):");
            Console.WriteLine(new string('-', 50));

            resp = await http.GetAsync(
                $"{uiServerUrl}/api/ui/interactive/v2/data?id={windowId}");
            resp.EnsureSuccessStatusCode();
            Console.WriteLine("  Data retrieved successfully");
        }
        catch (HttpRequestException ex)
        {
            Console.WriteLine($"\n  HTTP Error: {ex.StatusCode}");
            Console.WriteLine($"  {ex.Message}");
        }
        finally
        {
            Console.WriteLine("\n6. Cleanup:");
            Console.WriteLine(new string('-', 50));

            if (windowId != null)
            {
                try
                {
                    await http.DeleteAsync(
                        $"{uiServerUrl}/api/ui/interactive/v2/window?id={windowId}");
                    Console.WriteLine("  Window closed");
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
}
