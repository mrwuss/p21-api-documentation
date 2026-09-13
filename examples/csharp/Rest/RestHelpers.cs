// Shared helpers for the "Other REST Families" examples (docs/15).
//
// These five families (extensibility/userdefinedfields, accounting/gl,
// sales/tasks, purchasing/purchaseorders, inventory/inventoryadjustments)
// live on the base host, not the UI server -- the same shape as the
// Entity API -- so P21Client's family-specific wrappers don't cover them.
// This gives a raw authenticated HttpClient against config.BaseUrl,
// mirroring RecipeHelpers.CreateRawClientAsync() for the UI-server case.

using Newtonsoft.Json.Linq;
using P21Examples.Common;

namespace P21Examples.Rest;

internal static class RestHelpers
{
    /// <summary>
    /// Render a JToken for console display, printing the literal "null"
    /// for a JSON null -- JValue.ToString() on JTokenType.Null returns an
    /// empty string, and it is not a C# null either, so `token ?? "null"`
    /// silently prints nothing instead of the null these child-collection
    /// fields actually are.
    /// </summary>
    public static string JsonDisplay(JToken? token) =>
        token == null || token.Type == JTokenType.Null ? "null" : token.ToString();

    /// <summary>
    /// Authenticated raw HttpClient targeting the base host (config.BaseUrl),
    /// for REST families P21Client does not wrap. Caller disposes Http.
    /// </summary>
    public static async Task<(HttpClient Http, string BaseUrl)> CreateRawClientAsync()
    {
        var config = P21Config.FromEnvironment();

        var handler = new HttpClientHandler();
        if (!config.VerifySsl)
        {
            handler.ServerCertificateCustomValidationCallback =
                HttpClientHandler.DangerousAcceptAnyServerCertificateValidator;
        }
        handler.AllowAutoRedirect = true;

        var http = new HttpClient(handler) { Timeout = TimeSpan.FromSeconds(60) };
        var token = await P21Auth.GetTokenAsync(http, config);
        P21Auth.SetAuthHeaders(http, token.AccessToken);

        return (http, config.BaseUrl);
    }

    /// <summary>
    /// WRITE SAFETY gate, matching RecipeHelpers.ConfirmExecute(). Returns
    /// true only when the user types EXECUTE.
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
}
