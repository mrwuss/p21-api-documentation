using System.Net.Http;
using System.Text;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using P21Examples.Common;

namespace P21Examples.Interactive;

/// <summary>
/// Interactive API - Session Management
///
/// Demonstrates opening and closing Interactive API sessions.
///
/// Sessions maintain state just like a real P21 user session.
/// Always end sessions when done to free server resources.
///
/// Mirrors: examples/python/interactive/01_open_session.py
/// </summary>
public static class OpenSession
{
    public static async Task RunAsync()
    {
        Console.WriteLine("Interactive API - Session Management");
        Console.WriteLine(new string('=', 60));

        // ------------------------------------------------------------------
        // Setup: authenticate and resolve the UI Server URL
        // ------------------------------------------------------------------
        using var client = await P21Client.CreateAsync();
        Console.WriteLine("Authenticated and resolved UI Server URL.");

        // The P21Client.Interactive property uses the high-level helpers.
        // Below we also show the raw HttpClient approach for educational value.

        // ==================================================================
        // HIGH-LEVEL APPROACH — using InteractiveSession from Common
        // ==================================================================
        Console.WriteLine("\n--- High-level approach (InteractiveSession) ---");

        // CreateSession returns an IAsyncDisposable session.
        // responseWindows: false means dialogs are auto-answered with the default.
        await using (var session = client.Interactive.CreateSession(responseWindows: false))
        {
            // 1. Start session
            Console.WriteLine("\n1. Starting a new session:");
            Console.WriteLine(new string('-', 50));

            await session.StartAsync();
            Console.WriteLine("  Session started successfully");

            // 2. Open and close a window just to prove the session works
            Console.WriteLine("\n2. Verifying session with a quick window open:");
            Console.WriteLine(new string('-', 50));

            var window = await session.OpenWindowAsync(serviceName: "SalesPricePage");
            Console.WriteLine($"  Opened window: {window.WindowId}");
            await window.CloseAsync();
            Console.WriteLine("  Window closed");

            // 3. Session ends automatically via DisposeAsync
            Console.WriteLine("\n3. Session will end automatically on dispose...");
        }

        Console.WriteLine("  Session ended (disposed)");

        // ==================================================================
        // RAW HTTP APPROACH — educational, showing exact endpoints
        // ==================================================================
        Console.WriteLine("\n--- Raw HTTP approach (HttpClient) ---");

        await RunRawHttpDemoAsync();

        // ------------------------------------------------------------------
        // Best practices
        // ------------------------------------------------------------------
        Console.WriteLine("\n" + new string('=', 60));
        Console.WriteLine("Session management complete!");
        Console.WriteLine();
        Console.WriteLine("Best practices:");
        Console.WriteLine("- Always end sessions when done");
        Console.WriteLine("- Use 'await using' for automatic cleanup in C#");
        Console.WriteLine("- Sessions timeout after inactivity, but don't rely on this");
    }

    /// <summary>
    /// Demonstrates the raw HTTP calls for session management.
    /// This mirrors the Python script more closely and shows the exact
    /// endpoints, headers, and payloads involved.
    /// </summary>
    private static async Task RunRawHttpDemoAsync()
    {
        var config = P21Config.FromEnvironment();

        // Build an HttpClient that skips SSL verification (like verify=False in Python)
        var handler = new HttpClientHandler();
        if (!config.VerifySsl)
        {
            handler.ServerCertificateCustomValidationCallback =
                HttpClientHandler.DangerousAcceptAnyServerCertificateValidator;
        }

        using var http = new HttpClient(handler) { Timeout = TimeSpan.FromSeconds(30) };

        // Authenticate
        var token = await P21Auth.GetTokenAsync(http, config);
        P21Auth.SetAuthHeaders(http, token.AccessToken);

        // Resolve UI Server
        var uiServerUrl = await P21Auth.GetUiServerUrlAsync(http, config.BaseUrl);
        Console.WriteLine($"  UI Server: {uiServerUrl}");

        // 1. Start a session
        // POST /api/ui/interactive/sessions
        // Body: {"ResponseWindowHandlingEnabled": false}
        Console.WriteLine("\n1. Starting a new session (raw HTTP):");
        Console.WriteLine(new string('-', 50));

        try
        {
            var startPayload = JsonConvert.SerializeObject(
                new { ResponseWindowHandlingEnabled = false });
            var startContent = new StringContent(startPayload, Encoding.UTF8, "application/json");

            var startResponse = await http.PostAsync(
                $"{uiServerUrl}/api/ui/interactive/sessions", startContent);
            startResponse.EnsureSuccessStatusCode();

            var startBody = await startResponse.Content.ReadAsStringAsync();
            Console.WriteLine($"  Session started successfully");
            Console.WriteLine($"  Response: {startBody}");
        }
        catch (HttpRequestException ex)
        {
            Console.WriteLine($"  Error: {ex.Message}");
            return;
        }

        // 2. List open sessions
        // GET /api/ui/interactive/sessions
        Console.WriteLine("\n2. Listing open sessions (raw HTTP):");
        Console.WriteLine(new string('-', 50));

        try
        {
            var listResponse = await http.GetAsync(
                $"{uiServerUrl}/api/ui/interactive/sessions");
            listResponse.EnsureSuccessStatusCode();

            var listBody = await listResponse.Content.ReadAsStringAsync();
            var sessions = JArray.Parse(listBody);
            Console.WriteLine($"  Found {sessions.Count} open session(s)");
            foreach (var sess in sessions)
            {
                Console.WriteLine($"    - {sess}");
            }
        }
        catch (HttpRequestException ex)
        {
            Console.WriteLine($"  Error: {ex.Message}");
        }

        // 3. End session
        // DELETE /api/ui/interactive/sessions
        Console.WriteLine("\n3. Ending session (raw HTTP):");
        Console.WriteLine(new string('-', 50));

        try
        {
            var endResponse = await http.DeleteAsync(
                $"{uiServerUrl}/api/ui/interactive/sessions");
            endResponse.EnsureSuccessStatusCode();
            Console.WriteLine("  Session ended successfully");
        }
        catch (HttpRequestException ex)
        {
            Console.WriteLine($"  Error: {ex.Message}");
        }

        // 4. Verify session ended
        Console.WriteLine("\n4. Verifying session ended:");
        Console.WriteLine(new string('-', 50));

        try
        {
            var verifyResponse = await http.GetAsync(
                $"{uiServerUrl}/api/ui/interactive/sessions");
            verifyResponse.EnsureSuccessStatusCode();

            var verifyBody = await verifyResponse.Content.ReadAsStringAsync();
            var remaining = JArray.Parse(verifyBody);
            Console.WriteLine($"  Open sessions: {remaining.Count}");
        }
        catch (HttpRequestException ex)
        {
            Console.WriteLine($"  Error: {ex.Message}");
        }
    }
}
