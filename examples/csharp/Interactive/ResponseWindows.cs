using System.Net.Http;
using System.Text;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using P21Examples.Common;
using P21Examples.Common.Models;

namespace P21Examples.Interactive;

/// <summary>
/// Interactive API - Response Windows
///
/// Demonstrates handling response windows (dialogs) that can pop up
/// during Interactive API operations.
///
/// IMPORTANT FINDINGS (January 2026):
/// ==================================
/// 1. ResponseWindowHandlingEnabled: false = Auto-answer with DEFAULT (usually "Yes")
///    ResponseWindowHandlingEnabled: true  = Dialog events returned to your code
///
/// 2. When a dialog opens with ResponseWindowHandlingEnabled: true:
///    - Status is numeric 3 (not string "Blocked")
///    - Events array contains "windowopened" with dialog's windowid
///
/// 3. KNOWN LIMITATION: There is NO documented endpoint to respond to message
///    box dialogs (w_message windows). You cannot programmatically click "Yes"
///    or "No" buttons on these dialogs.
///
/// 4. Attempting to continue while dialog is open results in error:
///    "Unable to process request on window X since response window Y blocks it"
///
/// Mirrors: examples/python/interactive/05_response_windows.py
/// </summary>
public static class ResponseWindows
{
    public static async Task RunAsync()
    {
        Console.WriteLine("Interactive API - Response Windows");
        Console.WriteLine(new string('=', 60));
        Console.WriteLine();
        Console.WriteLine("  IMPORTANT: As of P21 25.2.x, there is NO documented endpoint");
        Console.WriteLine("  to respond to message box dialogs programmatically.");
        Console.WriteLine();

        // ==================================================================
        // HIGH-LEVEL APPROACH — using InteractiveResult.GetOpenedWindowId()
        // ==================================================================
        Console.WriteLine("--- High-level approach ---");

        using var client = await P21Client.CreateAsync();

        // Create session with responseWindows: true so dialogs are returned to us
        await using var session = client.Interactive.CreateSession(responseWindows: true);
        InteractiveWindow? window = null;

        try
        {
            Console.WriteLine("\n1. Starting session with ResponseWindowHandlingEnabled: TRUE");
            Console.WriteLine(new string('-', 50));
            await session.StartAsync();
            Console.WriteLine("  Session started");
            Console.WriteLine("  (Dialogs will be returned to our code)");

            Console.WriteLine("\n2. Opening Item window:");
            Console.WriteLine(new string('-', 50));
            window = await session.OpenWindowAsync(serviceName: "Item");
            Console.WriteLine($"  Window ID: {window.WindowId}");

            Console.WriteLine("\n3. Retrieving an item:");
            Console.WriteLine(new string('-', 50));

            // Use an item that exists in your P21 — adjust as needed
            var result = await window.ChangeDataAsync(
                tabName: "TABPAGE_1",
                fieldName: "item_id",
                value: "WIDGET-001",
                datawindowName: "");  // item_id field may not need DatawindowName

            Console.WriteLine($"  Status: {result.Status}");

            if (result.Status != 1)
            {
                Console.WriteLine("  Item not found or error - adjust item_id in script");

                // Check if a response window opened (Status 3)
                if (result.Status == 3)
                {
                    var dialogId = result.GetOpenedWindowId();
                    if (dialogId != null)
                    {
                        Console.WriteLine($"  Response window opened: {dialogId}");
                        await HandleResponseWindowDemoAsync(client, window, dialogId);
                    }
                }
                return;
            }

            Console.WriteLine("\n4. Navigating to Location Detail:");
            Console.WriteLine(new string('-', 50));

            await window.SelectTabAsync("TABPAGE_17");  // Locations list
            Console.WriteLine("  Switched to TABPAGE_17 (Locations list)");

            // Note: row change would need raw HTTP — the high-level API
            // doesn't have a ChangeRowAsync method on InteractiveWindow.
            // We'll show the full raw flow below.
            Console.WriteLine("  (Row selection requires raw HTTP - see raw approach below)");

            Console.WriteLine("\n5. Changing product_group_id (may trigger dialog):");
            Console.WriteLine(new string('-', 50));

            result = await window.ChangeDataAsync(
                tabName: "TABPAGE_18",
                fieldName: "product_group_id",
                value: "MISC",
                datawindowName: "inv_loc_detail");

            Console.WriteLine($"  Status: {result.Status}");
            Console.WriteLine($"  Events: {result.Events.Count} event(s)");

            // Check for dialog using the built-in helper
            var responseWindowId = result.GetOpenedWindowId();
            if (responseWindowId != null)
            {
                Console.WriteLine($"\n  DIALOG DETECTED!");
                Console.WriteLine($"    Dialog Window ID: {responseWindowId}");
                await HandleResponseWindowDemoAsync(client, window, responseWindowId);
            }
            else if (result.Status == 3)
            {
                Console.WriteLine("  Status 3 (Blocked) but no windowopened event found");
            }
            else
            {
                Console.WriteLine("  No dialog opened");
                Console.WriteLine("  (product group may already be set to target value)");
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
        finally
        {
            Console.WriteLine("\n8. Cleanup:");
            Console.WriteLine(new string('-', 50));

            if (window != null)
            {
                try
                {
                    await window.CloseAsync();
                    Console.WriteLine("  Window closed");
                }
                catch
                {
                    Console.WriteLine("  Window close failed (may have been blocked by dialog)");
                }
            }
            // Session ends via DisposeAsync
        }

        // ==================================================================
        // RAW HTTP APPROACH — full response window workflow
        // ==================================================================
        Console.WriteLine("\n--- Raw HTTP approach ---");
        await RunRawHttpDemoAsync();

        // ------------------------------------------------------------------
        // Summary
        // ------------------------------------------------------------------
        Console.WriteLine("\n" + new string('=', 60));
        Console.WriteLine("SUMMARY - Response Window Handling");
        Console.WriteLine(new string('=', 60));
        Console.WriteLine(@"
Key findings:
1. ResponseWindowHandlingEnabled: false = auto-answer with DEFAULT (usually Yes)
2. ResponseWindowHandlingEnabled: true = dialog info returned, but...
3. NO KNOWN ENDPOINT to respond 'No' to message box dialogs
4. Dialogs block the main window until dismissed

Impact on Product Group changes:
- Changing product_group_id triggers GL account dialog
- Default 'Yes' overwrites GL, revenue, and COS account fields
- Cannot programmatically answer 'No' to preserve existing GL accounts

Workarounds:
- Accept GL changes (not ideal)
- Restore GL accounts via direct SQL after API change
- Contact Epicor for response window endpoint documentation
");
    }

    /// <summary>
    /// Demonstrate handling a response window when one is detected.
    /// Shows the /tools endpoint for non-message-box dialogs.
    /// </summary>
    private static async Task HandleResponseWindowDemoAsync(
        P21Client client, InteractiveWindow mainWindow, string dialogWindowId)
    {
        // Create a temporary InteractiveWindow for the dialog
        // to use the GetToolsAsync helper
        Console.WriteLine("\n6. Inspecting dialog with /tools endpoint:");
        Console.WriteLine(new string('-', 50));

        // The /tools endpoint works for non-message-box dialogs
        // (e.g., w_inventory_scan_lookup) but NOT for w_message dialogs.
        Console.WriteLine("  Note: /tools works for popup windows like w_inventory_scan_lookup");
        Console.WriteLine("  but does NOT work for w_message dialogs.");

        Console.WriteLine("\n7. Attempting to save (will fail while dialog open):");
        Console.WriteLine(new string('-', 50));

        try
        {
            var saveResult = await mainWindow.SaveDataAsync();
            Console.WriteLine($"  Save Status: {saveResult.Status}");
        }
        catch (HttpRequestException ex)
        {
            var message = ex.Message;
            Console.WriteLine($"  Expected error: {ex.StatusCode}");
            Console.WriteLine(message.Contains("blocks it")
                ? "  Error indicates dialog is blocking: Yes"
                : $"  {message}");
        }
    }

    /// <summary>
    /// Raw HTTP approach showing all the response window detection logic.
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
            // Start session with response windows enabled
            Console.WriteLine("\n1. Starting session with response windows enabled...");

            var sessionPayload = JsonConvert.SerializeObject(
                new { ResponseWindowHandlingEnabled = true });
            var resp = await http.PostAsync(
                $"{uiServerUrl}/api/ui/interactive/sessions",
                new StringContent(sessionPayload, Encoding.UTF8, "application/json"));
            resp.EnsureSuccessStatusCode();

            var sessionBody = await resp.Content.ReadAsStringAsync();
            Console.WriteLine($"  Response: {sessionBody}");

            // Open Item window
            Console.WriteLine("\n2. Opening Item window...");

            var windowPayload = JsonConvert.SerializeObject(
                new { ServiceName = "Item" });
            resp = await http.PostAsync(
                $"{uiServerUrl}/api/ui/interactive/v2/window",
                new StringContent(windowPayload, Encoding.UTF8, "application/json"));
            resp.EnsureSuccessStatusCode();

            var windowBody = await resp.Content.ReadAsStringAsync();
            windowId = JObject.Parse(windowBody)["WindowId"]?.ToString();
            Console.WriteLine($"  Window ID: {windowId}");

            // Retrieve an item
            Console.WriteLine("\n3. Retrieving item WIDGET-001...");

            var changePayload = JsonConvert.SerializeObject(new
            {
                WindowId = windowId,
                List = new[]
                {
                    new { TabName = "TABPAGE_1", FieldName = "item_id",
                          Value = "WIDGET-001", DatawindowName = "" }
                }
            });

            resp = await http.PutAsync(
                $"{uiServerUrl}/api/ui/interactive/v2/change",
                new StringContent(changePayload, Encoding.UTF8, "application/json"));
            resp.EnsureSuccessStatusCode();

            var changeBody = await resp.Content.ReadAsStringAsync();
            var changeResult = JObject.Parse(changeBody);
            var status = changeResult["Status"]?.Value<int>() ?? 0;
            Console.WriteLine($"  Status: {status}");

            // Check for response window in the result
            var dialogId = CheckForResponseWindow(changeResult);
            if (dialogId != null)
            {
                Console.WriteLine($"\n  DIALOG DETECTED: {dialogId}");

                // Try various endpoints to respond (all expected to fail for w_message)
                Console.WriteLine("\n4. Testing response endpoints (all expected to fail):");
                Console.WriteLine(new string('-', 50));

                await TryResponseEndpointsAsync(http, uiServerUrl, dialogId);
            }
            else if (status == 1)
            {
                Console.WriteLine("  Item retrieved successfully, no dialog");
            }
            else
            {
                Console.WriteLine($"  Unexpected status: {status}");
            }
        }
        catch (HttpRequestException ex)
        {
            Console.WriteLine($"\n  HTTP Error: {ex.StatusCode}");
            Console.WriteLine($"  {ex.Message}");
        }
        finally
        {
            Console.WriteLine("\n  Cleanup:");

            if (windowId != null)
            {
                try
                {
                    await http.DeleteAsync(
                        $"{uiServerUrl}/api/ui/interactive/v2/window?id={windowId}");
                    Console.WriteLine("  Window closed");
                }
                catch
                {
                    Console.WriteLine("  Window close failed (may be blocked by dialog)");
                }
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
    /// Check if a response window was opened.
    ///
    /// With ResponseWindowHandlingEnabled: true, dialogs return:
    /// - Status: 3 (numeric, not string "Blocked")
    /// - Events array with "windowopened" event
    /// - Event Data is a KV-list: [{"Key": "windowid", "Value": "..."}]
    /// </summary>
    private static string? CheckForResponseWindow(JObject result)
    {
        var status = result["Status"]?.Value<int>() ?? 0;
        if (status != 3)
            return null;

        var events = result["Events"] as JArray;
        if (events == null)
            return null;

        foreach (var evt in events)
        {
            var name = evt["Name"]?.ToString() ?? "";
            if (!string.Equals(name, "windowopened", StringComparison.OrdinalIgnoreCase))
                continue;

            var data = evt["Data"];

            // Data is a KV-list: [{"Key": "windowid", "Value": "..."}]
            if (data is JArray kvList)
            {
                foreach (var item in kvList)
                {
                    var key = item["Key"]?.ToString() ?? "";
                    if (string.Equals(key, "windowid", StringComparison.OrdinalIgnoreCase))
                        return item["Value"]?.ToString();
                }
            }
        }

        return null;
    }

    /// <summary>
    /// Attempt various endpoints to respond to a dialog.
    ///
    /// KNOWN ISSUE: None of these endpoints work for w_message dialogs as of P21 25.2.x.
    /// This method documents what was tested.
    /// </summary>
    private static async Task TryResponseEndpointsAsync(
        HttpClient http, string uiServerUrl, string dialogWindowId)
    {
        var endpoints = new (string Name, Func<Task<int?>> Action)[]
        {
            // Endpoint 1: PUT responsewindow (singular)
            ("PUT /v2/responsewindow", async () =>
            {
                var payload = JsonConvert.SerializeObject(
                    new { ResponseWindowId = dialogWindowId, Button = "No" });
                var resp = await http.PutAsync(
                    $"{uiServerUrl}/api/ui/interactive/v2/responsewindow",
                    new StringContent(payload, Encoding.UTF8, "application/json"));
                return (int)resp.StatusCode;
            }),

            // Endpoint 2: PUT responsewindows (plural)
            ("PUT /v2/responsewindows", async () =>
            {
                var payload = JsonConvert.SerializeObject(
                    new { ResponseWindowId = dialogWindowId, Button = "No" });
                var resp = await http.PutAsync(
                    $"{uiServerUrl}/api/ui/interactive/v2/responsewindows",
                    new StringContent(payload, Encoding.UTF8, "application/json"));
                return (int)resp.StatusCode;
            }),

            // Endpoint 3: DELETE window with button param
            ("DELETE /v2/window?button=No", async () =>
            {
                var resp = await http.DeleteAsync(
                    $"{uiServerUrl}/api/ui/interactive/v2/window?windowId={dialogWindowId}&button=No");
                return (int)resp.StatusCode;
            }),

            // Endpoint 4: POST button
            ("POST /v2/button", async () =>
            {
                var payload = JsonConvert.SerializeObject(
                    new { WindowId = dialogWindowId, ButtonName = "No" });
                var resp = await http.PostAsync(
                    $"{uiServerUrl}/api/ui/interactive/v2/button",
                    new StringContent(payload, Encoding.UTF8, "application/json"));
                return (int)resp.StatusCode;
            }),
        };

        foreach (var (name, action) in endpoints)
        {
            try
            {
                var statusCode = await action();
                Console.WriteLine($"    {name}: {statusCode}");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"    {name}: {ex.Message}");
            }
        }

        Console.WriteLine();
        Console.WriteLine("  No working endpoint found to respond 'No' to dialog");
        Console.WriteLine("  The dialog will block further operations on the main window");
    }
}
