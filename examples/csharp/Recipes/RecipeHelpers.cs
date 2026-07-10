// Shared helpers for the recipe examples.
//
// - Write-safety gate: every recipe prints its payload and asks for console
//   confirmation before any POST that writes. Anything other than EXECUTE
//   is a dry run; read-only lookups always run.
// - Auth/config comes from the Common project (P21Client / P21Config /
//   P21Auth), not the recipes' inline P21Session helper.

using Newtonsoft.Json.Linq;
using P21Examples.Common;
using P21Examples.Common.Models;

namespace P21Examples.Recipes;

internal static class RecipeHelpers
{
    /// <summary>Build a Transaction API edit: {"Name": ..., "Value": ...}.</summary>
    public static JObject Edit(string name, string value) =>
        new JObject { ["Name"] = name, ["Value"] = value };

    /// <summary>Print a payload before asking for write confirmation.</summary>
    public static void PrintPayload(string title, JToken payload)
    {
        Console.WriteLine();
        Console.WriteLine($"{title}:");
        Console.WriteLine(new string('-', 50));
        Console.WriteLine(payload.ToString());
    }

    /// <summary>
    /// WRITE SAFETY gate. Returns true only when the user types EXECUTE;
    /// anything else means dry run (nothing is posted).
    /// </summary>
    public static bool ConfirmExecute()
    {
        Console.WriteLine();
        Console.Write("Type EXECUTE to post, anything else = dry run: ");
        var answer = Console.ReadLine()?.Trim();
        if (answer == "EXECUTE")
            return true;

        Console.WriteLine("Dry run - nothing was posted.");
        return false;
    }

    /// <summary>
    /// Print Summary.Succeeded / Summary.Failed and every message.
    /// HTTP 200 is NOT success on the Transaction API — only the Summary is.
    /// </summary>
    public static bool CheckResult(TransactionResult result)
    {
        Console.WriteLine($"  Succeeded: {result.Succeeded}, Failed: {result.Failed}");
        foreach (var msg in result.Messages)
            Console.WriteLine($"  {msg}");
        return result.Failed == 0 && result.Succeeded > 0;
    }

    /// <summary>
    /// Authenticated raw HttpClient + UI server URL for endpoints P21Client
    /// does not wrap (POST /api/v2/process/pdfreport, popup /v2/tools calls).
    /// Built from the Common project's config/auth helpers. Caller disposes Http.
    /// </summary>
    public static async Task<(HttpClient Http, string UiServer, string BaseUrl)> CreateRawClientAsync()
    {
        var config = P21Config.FromEnvironment();

        var handler = new HttpClientHandler();
        if (!config.VerifySsl)
        {
            handler.ServerCertificateCustomValidationCallback =
                HttpClientHandler.DangerousAcceptAnyServerCertificateValidator;
        }

        var http = new HttpClient(handler) { Timeout = TimeSpan.FromSeconds(120) };
        var token = await P21Auth.GetTokenAsync(http, config);
        P21Auth.SetAuthHeaders(http, token.AccessToken);
        var uiServer = await P21Auth.GetUiServerUrlAsync(http, config.BaseUrl);

        return (http, uiServer, config.BaseUrl);
    }
}
