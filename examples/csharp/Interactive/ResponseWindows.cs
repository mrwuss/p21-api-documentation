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
/// VERIFIED FLOW (2026):
/// =====================
/// 1. ResponseWindowHandlingEnabled: false = Auto-answer with DEFAULT (usually "Yes")
///    ResponseWindowHandlingEnabled: true  = Dialog events returned to your code
///
/// 2. When a dialog opens with ResponseWindowHandlingEnabled: true:
///    - Status is 3 (Blocked)
///    - Events array contains "windowopened" whose Data KV-list carries
///      the POPUP's window ID: [{"Key": "windowid", "Value": "..."}]
///
/// 3. Answer the popup via the /tools endpoints using the POPUP's window ID:
///    - GET  /api/ui/interactive/v2/tools?windowId={popupId}  -> discover buttons
///      (e.g., cb_ok, cb_cancel on w_inventory_scan_lookup; cb_1..cb_5 on
///      w_rule_callback_response)
///    - POST /api/ui/interactive/v2/tools                     -> click a button
///
/// 4. Form-style response windows (e.g., w_notepad_response_lite) are fully
///    EDITABLE: change their fields with TabName: null, then click their tools.
///
/// 5. REMAINING LIMITATION — scoped to w_message ONLY: plain message boxes
///    (w_message) expose no usable tools and are auto-answered with the
///    default button. Historical note: PUT /v2/responsewindow,
///    PUT /v2/responsewindows, DELETE /v2/window?button=No and
///    POST /v2/button were all tested and do NOT exist (404/400).
///
/// 6. Attempting to continue while a dialog is open results in error:
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
        Console.WriteLine("  Popups are answered via GET/POST /v2/tools using the POPUP's");
        Console.WriteLine("  window ID from the 'windowopened' event. Only w_message boxes");
        Console.WriteLine("  remain unanswerable (auto-answered with the default button).");
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
                datawindowName: "tp_1_dw_1");

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
2. ResponseWindowHandlingEnabled: true = Status 3 (Blocked) + 'windowopened'
   event carrying the POPUP's window ID
3. Answer popups via the /tools endpoints with the POPUP's window ID:
   GET /v2/tools?windowId={popupId} to discover buttons, POST /v2/tools
   to click one (verified: w_inventory_scan_lookup, w_rule_callback_response)
4. Form-style response windows (e.g., w_notepad_response_lite) are fully
   editable — change their fields with TabName: null, then click their tools
5. Remaining limitation is scoped to w_message boxes ONLY: they expose no
   usable tools and get the default answer. (Historical: /v2/responsewindow,
   /v2/responsewindows, DELETE window?button=, /v2/button all 404/400.)
6. Dialogs block the main window until dismissed

Impact on Product Group changes:
- Changing product_group_id triggers a GL account w_message dialog
- Default 'Yes' overwrites GL, revenue, and COS account fields

Recommendation:
- For inv_loc field changes (product group, sellable, discount groups),
  prefer the Inventory REST API (PUT /api/inventory/parts/{ItemId}) —
  see docs/11-Inventory-REST-API.md — which avoids the dialog entirely
");
    }

    /// <summary>
    /// Handle a response window using the VERIFIED flow: attach to the
    /// popup's window ID (from the "windowopened" event), discover its
    /// buttons via GET /v2/tools?windowId={popupId}, then click one via
    /// POST /v2/tools. Works for popups like w_inventory_scan_lookup and
    /// w_rule_callback_response; w_message boxes expose no usable tools.
    /// Form-style response windows (e.g., w_notepad_response_lite) can also
    /// have their fields edited first, using TabName: null.
    /// </summary>
    private static async Task HandleResponseWindowDemoAsync(
        P21Client client, InteractiveWindow mainWindow, string dialogWindowId)
    {
        Console.WriteLine("\n6. Discovering the popup's buttons via /tools:");
        Console.WriteLine(new string('-', 50));

        // Attach to the POPUP's window ID — all tools calls target the
        // popup, not the main window.
        var popup = client.Interactive.AttachWindow(dialogWindowId);

        var tools = await popup.GetToolsAsync();
        Console.WriteLine($"  GET /v2/tools?windowId={dialogWindowId}");
        Console.WriteLine($"  HTTP {tools.HttpStatusCode}");

        // The response is a JSON array of tools:
        //   [{"ToolName": "cb_ok", "DatawindowName": null, "FieldName": null}, ...]
        var toolNames = new List<string>();
        if (!string.IsNullOrEmpty(tools.RawBody))
        {
            try
            {
                foreach (var tool in JArray.Parse(tools.RawBody))
                {
                    var name = tool["ToolName"]?.ToString();
                    if (!string.IsNullOrEmpty(name))
                        toolNames.Add(name);
                }
            }
            catch (JsonReaderException)
            {
                // Not an array — no tools to list
            }
        }

        if (toolNames.Count > 0)
        {
            Console.WriteLine($"  Available tools: {string.Join(", ", toolNames)}");

            // Click Cancel/No if available (safe choice for a demo);
            // otherwise click the first button.
            var button = toolNames.FirstOrDefault(
                    n => n.Contains("cancel", StringComparison.OrdinalIgnoreCase))
                ?? toolNames[0];

            Console.WriteLine($"\n7. Clicking '{button}' via POST /v2/tools:");
            Console.WriteLine(new string('-', 50));

            var clickResult = await popup.RunToolAsync(button);
            Console.WriteLine($"  Status: {clickResult.Status} (1=Success)");
            Console.WriteLine("  Popup answered - the main window is unblocked");
        }
        else
        {
            // w_message boxes land here: no usable tools are exposed.
            Console.WriteLine("  No usable tools returned - this is a w_message box.");
            Console.WriteLine("  w_message dialogs cannot be answered via the API; they are");
            Console.WriteLine("  auto-answered with the default button. For inv_loc changes,");
            Console.WriteLine("  prefer the Inventory REST API (docs/11) to avoid the dialog.");
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
                    new { TabName = "TABPAGE_1", DatawindowName = "tp_1_dw_1",
                          FieldName = "item_id", Value = "WIDGET-001" }
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

                // Answer it via the verified /tools flow, using the POPUP's ID
                Console.WriteLine("\n4. Answering the popup via /tools:");
                Console.WriteLine(new string('-', 50));

                await AnswerPopupViaToolsAsync(http, uiServerUrl, dialogId);
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
    /// Answer a popup with the VERIFIED /tools flow (raw HTTP):
    ///   1. GET  /api/ui/interactive/v2/tools?windowId={popupId}  -> list buttons
    ///   2. POST /api/ui/interactive/v2/tools                     -> click one
    /// Both calls use the POPUP's window ID, not the main window's.
    ///
    /// Form-style response windows (e.g., w_notepad_response_lite) can also
    /// have their fields edited first via PUT /v2/change with TabName: null.
    ///
    /// Historical note — these four endpoints were tested and do NOT exist
    /// (do not use them):
    ///   PUT  /v2/responsewindow          -> 404
    ///   PUT  /v2/responsewindows         -> 404
    ///   DELETE /v2/window?...&button=No  -> 400
    ///   POST /v2/button                  -> 404
    /// </summary>
    private static async Task AnswerPopupViaToolsAsync(
        HttpClient http, string uiServerUrl, string dialogWindowId)
    {
        // Step 1: discover the popup's buttons
        var toolsResp = await http.GetAsync(
            $"{uiServerUrl}/api/ui/interactive/v2/tools?windowId={dialogWindowId}");
        var toolsBody = await toolsResp.Content.ReadAsStringAsync();
        Console.WriteLine($"  GET /v2/tools?windowId={dialogWindowId}: {(int)toolsResp.StatusCode}");

        // Response is a JSON array:
        //   [{"ToolName": "cb_ok", "DatawindowName": null, "FieldName": null}, ...]
        var toolNames = new List<string>();
        try
        {
            foreach (var tool in JArray.Parse(toolsBody))
            {
                var name = tool["ToolName"]?.ToString();
                if (!string.IsNullOrEmpty(name))
                    toolNames.Add(name);
            }
        }
        catch (JsonReaderException)
        {
            // Not an array — no tools to list
        }

        if (toolNames.Count == 0)
        {
            // w_message boxes land here: no usable tools.
            Console.WriteLine("  No usable tools - this is a w_message box (cannot be answered");
            Console.WriteLine("  via the API; it gets the default answer). For inv_loc changes,");
            Console.WriteLine("  prefer the Inventory REST API (docs/11) to avoid the dialog.");
            return;
        }

        Console.WriteLine($"  Available tools: {string.Join(", ", toolNames)}");

        // Step 2: click a button (Cancel/No is the safe demo choice)
        var button = toolNames.FirstOrDefault(
                n => n.Contains("cancel", StringComparison.OrdinalIgnoreCase))
            ?? toolNames[0];

        var clickPayload = JsonConvert.SerializeObject(new
        {
            WindowId = dialogWindowId,  // the POPUP's window ID
            ToolName = button,
            ToolText = ""
        });
        var clickResp = await http.PostAsync(
            $"{uiServerUrl}/api/ui/interactive/v2/tools",
            new StringContent(clickPayload, Encoding.UTF8, "application/json"));
        Console.WriteLine($"  POST /v2/tools (ToolName={button}): {(int)clickResp.StatusCode}");
        Console.WriteLine("  Popup answered - the main window is unblocked");
    }
}
