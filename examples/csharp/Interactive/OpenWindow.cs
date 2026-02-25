using System.Net.Http;
using System.Text;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using P21Examples.Common;

namespace P21Examples.Interactive;

/// <summary>
/// Interactive API - Open Window
///
/// Demonstrates opening P21 windows via the Interactive API.
///
/// Windows can be opened by:
/// - ServiceName (e.g., "SalesPricePage", "Order")
/// - Title (e.g., "Sales Price Page Entry")
///
/// Mirrors: scripts/interactive/02_open_window.py
/// </summary>
public static class OpenWindow
{
    public static async Task RunAsync()
    {
        Console.WriteLine("Interactive API - Open Window");
        Console.WriteLine(new string('=', 60));

        // ------------------------------------------------------------------
        // Setup
        // ------------------------------------------------------------------
        using var client = await P21Client.CreateAsync();

        // ==================================================================
        // HIGH-LEVEL APPROACH — InteractiveSession + InteractiveWindow
        // ==================================================================
        Console.WriteLine("\n--- High-level approach ---");

        await using var session = client.Interactive.CreateSession(responseWindows: false);

        try
        {
            // Start session
            Console.WriteLine("\n1. Starting session...");
            Console.WriteLine(new string('-', 50));
            await session.StartAsync();
            Console.WriteLine("  Session started");

            // Open window by service name
            Console.WriteLine("\n2. Opening window by ServiceName:");
            Console.WriteLine(new string('-', 50));

            var window = await session.OpenWindowAsync(serviceName: "SalesPricePage");
            Console.WriteLine($"  Window opened!");
            Console.WriteLine($"    Window ID: {window.WindowId}");

            // Get window data to see available fields
            Console.WriteLine("\n3. Getting window data:");
            Console.WriteLine(new string('-', 50));

            var dataResult = await window.GetDataAsync();
            Console.WriteLine($"  Status: {dataResult.Status} (1=Success)");
            Console.WriteLine($"  Has data: {dataResult.Data != null}");

            // Get available tools/buttons
            Console.WriteLine("\n4. Getting available tools:");
            Console.WriteLine(new string('-', 50));

            var toolsResult = await window.GetToolsAsync();
            Console.WriteLine($"  Status: {toolsResult.Status}");
            if (toolsResult.Data is JObject toolsData)
            {
                var tools = toolsData["Tools"] ?? toolsData["tools"];
                if (tools is JArray toolArray)
                {
                    Console.WriteLine($"  Available tools: {toolArray.Count}");
                    foreach (var tool in toolArray.Take(5))
                    {
                        var name = tool["Name"]?.ToString() ?? tool["ToolName"]?.ToString() ?? "?";
                        Console.WriteLine($"    - {name}");
                    }
                    if (toolArray.Count > 5)
                        Console.WriteLine($"    ... and {toolArray.Count - 5} more");
                }
            }

            // Close window
            Console.WriteLine("\n5. Closing window:");
            Console.WriteLine(new string('-', 50));

            await window.CloseAsync();
            Console.WriteLine("  Window closed");
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
        // RAW HTTP APPROACH — showing exact endpoints
        // ==================================================================
        Console.WriteLine("\n--- Raw HTTP approach ---");

        await RunRawHttpDemoAsync();

        // ------------------------------------------------------------------
        // Reference
        // ------------------------------------------------------------------
        Console.WriteLine("\n" + new string('=', 60));
        Console.WriteLine("Window operations complete!");
        Console.WriteLine();
        Console.WriteLine("Common windows and their service names:");
        Console.WriteLine("  - SalesPricePage: Sales Price Page Entry");
        Console.WriteLine("  - Order: Order Entry");
        Console.WriteLine("  - Customer: Customer Maintenance");
        Console.WriteLine("  - Supplier: Supplier Maintenance");
        Console.WriteLine("  - Item: Item Maintenance");
    }

    /// <summary>
    /// Raw HTTP calls showing the exact requests for opening/closing windows.
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

        Console.WriteLine($"  UI Server: {uiServerUrl}");

        try
        {
            // Start session
            Console.WriteLine("\n1. Starting session (raw HTTP)...");
            var sessionPayload = JsonConvert.SerializeObject(
                new { ResponseWindowHandlingEnabled = false });
            var sessionContent = new StringContent(
                sessionPayload, Encoding.UTF8, "application/json");

            var sessionResp = await http.PostAsync(
                $"{uiServerUrl}/api/ui/interactive/sessions", sessionContent);
            sessionResp.EnsureSuccessStatusCode();
            Console.WriteLine("  Session started");

            // Open window by ServiceName
            // POST /api/ui/interactive/v2/window
            // Body: {"ServiceName": "SalesPricePage"}
            Console.WriteLine("\n2. Opening window by ServiceName (raw HTTP):");
            Console.WriteLine(new string('-', 50));

            var windowPayload = JsonConvert.SerializeObject(
                new { ServiceName = "SalesPricePage" });
            var windowContent = new StringContent(
                windowPayload, Encoding.UTF8, "application/json");

            var windowResp = await http.PostAsync(
                $"{uiServerUrl}/api/ui/interactive/v2/window", windowContent);
            windowResp.EnsureSuccessStatusCode();

            var windowBody = await windowResp.Content.ReadAsStringAsync();
            var windowData = JObject.Parse(windowBody);

            var windowId = windowData["WindowId"]?.ToString();
            var title = windowData["Title"]?.ToString() ?? "Unknown";

            Console.WriteLine($"  Window opened!");
            Console.WriteLine($"    Window ID: {windowId}");
            Console.WriteLine($"    Title: {title}");

            // Show DataElements if present
            var dataElements = windowData["DataElements"] as JArray;
            if (dataElements != null && dataElements.Count > 0)
            {
                Console.WriteLine($"\n  DataElements ({dataElements.Count}):");
                foreach (var elem in dataElements.Take(3))
                {
                    Console.WriteLine($"    - {elem["Name"] ?? "Unknown"}");
                }
            }

            // Get window state
            // GET /api/ui/interactive/v2/window?windowId={windowId}
            Console.WriteLine("\n3. Getting window state (raw HTTP):");
            Console.WriteLine(new string('-', 50));

            var stateResp = await http.GetAsync(
                $"{uiServerUrl}/api/ui/interactive/v2/window?id={windowId}");
            stateResp.EnsureSuccessStatusCode();

            var stateBody = await stateResp.Content.ReadAsStringAsync();
            var stateData = JObject.Parse(stateBody);
            Console.WriteLine($"  Window ID: {stateData["WindowId"]}");
            Console.WriteLine($"  Status: {stateData["Status"] ?? "Unknown"}");

            // Close window
            // DELETE /api/ui/interactive/v2/window?id={windowId}
            Console.WriteLine("\n4. Closing window (raw HTTP):");
            Console.WriteLine(new string('-', 50));

            var closeResp = await http.DeleteAsync(
                $"{uiServerUrl}/api/ui/interactive/v2/window?id={windowId}");
            Console.WriteLine("  Window closed");

            // End session
            Console.WriteLine("\n5. Ending session (raw HTTP):");
            Console.WriteLine(new string('-', 50));
            await http.DeleteAsync($"{uiServerUrl}/api/ui/interactive/sessions");
            Console.WriteLine("  Session ended");
        }
        catch (HttpRequestException ex)
        {
            Console.WriteLine($"\n  HTTP Error: {ex.StatusCode}");
            Console.WriteLine($"  {ex.Message}");

            // Always try to end session
            try
            {
                await http.DeleteAsync($"{uiServerUrl}/api/ui/interactive/sessions");
            }
            catch { /* cleanup */ }
        }
    }
}
