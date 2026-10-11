// Thin Interactive API v2 helper for the write recipes (docs/04-Interactive-API.md).
//
// Wraps the raw endpoints with error checking only, so each recipe still
// shows the real call sequence:
//   POST   sessions/          start (ResponseWindowHandlingEnabled)
//   POST   v2/window          open by ServiceName
//   PUT    v2/change          change one field
//   PUT    v2/tab             select a tab page
//   PUT    v2/row             select a row (POST v2/row adds one)
//   GET    v2/data?id=        datawindows on the active surface
//   GET    v2/tools?windowId= buttons/tools of a window or popup
//   POST   v2/tools           click a button/tool
//   PUT    v2/data            save (body = bare window-ID string)
//   DELETE v2/window?id=      close;  DELETE sessions/  end
//
// Also: an authenticated raw client that can sign in with the consumer key
// (P21_CONSUMER_KEY + P21_CONSUMER_USERNAME) for flows that need a user
// with a Buyer ID, and a one-line OData reader.

using System.Text;
using System.Text.RegularExpressions;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using P21Examples.Common;

namespace P21Examples.Recipes;

internal sealed class WindowSession : IAsyncDisposable
{
    public const int Success = 1, Failure = 2, Blocked = 3;   // ResultStatus enum (0 = None)

    private readonly HttpClient _http;
    private readonly string _base;

    public WindowSession(HttpClient http, string uiServer)
    {
        _http = http;
        _base = $"{uiServer}/api/ui/interactive";
    }

    /// <summary>Start the session. true makes popups come back as windows to answer.</summary>
    public Task StartAsync(bool responseWindows = true) =>
        SendAsync(HttpMethod.Post, "sessions/",
            new JObject { ["ResponseWindowHandlingEnabled"] = responseWindows }, "start session");

    public async Task<string> OpenWindowAsync(string serviceName) =>
        (string)(await SendAsync(HttpMethod.Post, "v2/window",
            new JObject { ["ServiceName"] = serviceName }, $"open {serviceName}"))["WindowId"]!;

    /// <summary>Change one field (DatawindowName is required on 25.2+).</summary>
    public Task<JObject> ChangeAsync(string windowId, string tab, string datawindow,
        string field, string value) =>
        SendAsync(HttpMethod.Put, "v2/change", new JObject
        {
            ["WindowId"] = windowId,
            ["List"] = new JArray { new JObject {
                ["TabName"] = tab, ["DatawindowName"] = datawindow,
                ["FieldName"] = field, ["Value"] = value } }
        }, $"change {field}={value}");

    public Task<JObject> SelectTabAsync(string windowId, string pageName) =>
        SendAsync(HttpMethod.Put, "v2/tab",
            new JObject { ["WindowId"] = windowId, ["PageName"] = pageName }, $"tab {pageName}");

    /// <summary>Make a row (1-based) active. Changes land on the ACTIVE row.</summary>
    public Task<JObject> SelectRowAsync(string windowId, string datawindow, int row) =>
        SendAsync(HttpMethod.Put, "v2/row", new JObject
            { ["WindowId"] = windowId, ["DatawindowName"] = datawindow, ["Row"] = row },
            $"select row {row} of {datawindow}");

    public Task<JObject> AddRowAsync(string windowId, string datawindow) =>
        SendAsync(HttpMethod.Post, "v2/row",
            new JObject { ["WindowId"] = windowId, ["DatawindowName"] = datawindow },
            $"add row to {datawindow}");

    public Task<JObject> RunToolAsync(string windowId, string toolName) =>
        SendAsync(HttpMethod.Post, "v2/tools",
            new JObject { ["WindowId"] = windowId, ["ToolName"] = toolName }, $"tool {toolName}");

    /// <summary>Save. The v2 body is the bare window-ID string (an object is a 422).</summary>
    public Task<JObject> SaveAsync(string windowId) =>
        SendAsync(HttpMethod.Put, "v2/data", new JValue(windowId), "save");

    public async Task<JArray> DataAsync(string windowId)
    {
        var body = await GetAsync($"v2/data?id={windowId}", "get data");
        return JArray.Parse(body);
    }

    /// <summary>All rows of one datawindow as column -> value maps.</summary>
    public async Task<List<Dictionary<string, string>>> RowsAsync(string windowId, string datawindow)
    {
        foreach (var dw in await DataAsync(windowId))
        {
            if ((string?)dw["Name"] != datawindow) continue;
            var cols = dw["Columns"]!.Select(c => (string)c!).ToList();
            return (dw["Data"] as JArray ?? new JArray())
                .Select(r => cols.Zip(r, (c, v) => (c, v: v.Type == JTokenType.Null ? "" : v.ToString()))
                    .ToDictionary(x => x.c, x => x.v))
                .ToList();
        }
        return new();
    }

    /// <summary>The active row of one datawindow. ActiveRow is 1-based.</summary>
    public async Task<Dictionary<string, string>> ActiveRowAsync(string windowId, string datawindow)
    {
        foreach (var dw in await DataAsync(windowId))
        {
            if ((string?)dw["Name"] != datawindow) continue;
            var rows = await RowsAsync(windowId, datawindow);
            var index = Math.Max(((int?)dw["ActiveRow"] ?? 1) - 1, 0);
            return rows.Count > index ? rows[index] : new();
        }
        return new();
    }

    /// <summary>Tool/button names (?windowId=, not ?id=). Includes the parent's ribbon.</summary>
    public async Task<List<string>> ToolsAsync(string windowId)
    {
        var body = await GetAsync($"v2/tools?windowId={windowId}", "get tools");
        return JArray.Parse(body).Select(t => (string)t["ToolName"]!).ToList();
    }

    /// <summary>Window class name from GET v2/window (e.g. "w_message").</summary>
    public async Task<string> WindowNameAsync(string windowId)
    {
        var response = await _http.GetAsync($"{_base}/v2/window?id={windowId}");
        if (!response.IsSuccessStatusCode) return "";
        var obj = JObject.Parse(await response.Content.ReadAsStringAsync());
        return (string?)obj["Definition"]?["Name"] ?? "";
    }

    public async Task CloseWindowAsync(string windowId) =>
        await _http.DeleteAsync($"{_base}/v2/window?id={windowId}");

    public async ValueTask DisposeAsync() => await _http.DeleteAsync($"{_base}/sessions/");

    /// <summary>Popup window IDs from the windowopened events (ResponseWindowId is empty on 26.1).</summary>
    public static List<string> PopupIds(JObject result) =>
        (result["Events"] as JArray ?? new JArray())
            .Where(e => (string?)e["Name"] == "windowopened")
            .SelectMany(e => e["Data"] as JArray ?? new JArray())
            .Where(kv => (string?)kv["Key"] == "windowid")
            .Select(kv => (string)kv["Value"]!)
            .ToList();

    /// <summary>First value of a key on an event, e.g. keygenerated/value.</summary>
    public static string? EventValue(JObject result, string eventName, string key) =>
        (result["Events"] as JArray ?? new JArray())
            .Where(e => (string?)e["Name"] == eventName)
            .SelectMany(e => e["Data"] as JArray ?? new JArray())
            .Where(kv => (string?)kv["Key"] == key)
            .Select(kv => (string?)kv["Value"])
            .FirstOrDefault();

    private async Task<string> GetAsync(string path, string what)
    {
        var response = await _http.GetAsync($"{_base}/{path}");
        var body = await response.Content.ReadAsStringAsync();
        if (!response.IsSuccessStatusCode)
            throw new InvalidOperationException($"{what}: HTTP {(int)response.StatusCode} {Trim(body)}");
        return body;
    }

    /// <summary>Send a request; throw on HTTP errors (with the body) and on Status 2.</summary>
    private async Task<JObject> SendAsync(HttpMethod method, string path, JToken body, string what)
    {
        var request = new HttpRequestMessage(method, $"{_base}/{path}")
        {
            Content = new StringContent(body.ToString(Formatting.None), Encoding.UTF8, "application/json")
        };
        var response = await _http.SendAsync(request);
        var text = await response.Content.ReadAsStringAsync();
        if (!response.IsSuccessStatusCode)
            throw new InvalidOperationException($"{what}: HTTP {(int)response.StatusCode} {Trim(text)}");
        var result = string.IsNullOrWhiteSpace(text) ? new JObject() : JObject.Parse(text);
        if ((int?)result["Status"] == Failure)
            throw new InvalidOperationException(
                $"{what}: {string.Join(" | ", (result["Messages"] as JArray ?? new JArray()).Select(m => (string?)m["Text"] ?? m.ToString()))}");
        return result;
    }

    private static string Trim(string s) => s.Length > 400 ? s[..400] : s;
}

internal static class InteractiveHelpers
{
    /// <summary>
    /// Authenticated raw HttpClient + UI server + base URL. With useConsumerKey
    /// the token is requested with P21_CONSUMER_KEY and P21_CONSUMER_USERNAME
    /// (the user the token acts as); otherwise with the .env username/password.
    /// </summary>
    public static async Task<(HttpClient Http, string UiServer, string BaseUrl)> CreateRawClientAsync(
        bool useConsumerKey = false)
    {
        var config = P21Config.FromEnvironment();   // also loads .env into the environment
        var handler = new HttpClientHandler();
        if (!config.VerifySsl)
            handler.ServerCertificateCustomValidationCallback =
                HttpClientHandler.DangerousAcceptAnyServerCertificateValidator;
        var http = new HttpClient(handler) { Timeout = TimeSpan.FromSeconds(180) };

        string accessToken;
        if (useConsumerKey)
        {
            var payload = new JObject
            {
                ["ClientSecret"] = Environment.GetEnvironmentVariable("P21_CONSUMER_KEY"),
                ["GrantType"] = "client_credentials",
                ["username"] = Environment.GetEnvironmentVariable("P21_CONSUMER_USERNAME"),
            };
            var request = new HttpRequestMessage(HttpMethod.Post, config.TokenUrlV2)
            {
                Content = new StringContent(payload.ToString(), Encoding.UTF8, "application/json")
            };
            request.Headers.TryAddWithoutValidation("Accept", "application/json");
            var response = await http.SendAsync(request);
            response.EnsureSuccessStatusCode();
            var body = await response.Content.ReadAsStringAsync();
            var match = Regex.Match(body, "\"AccessToken\"\\s*:\\s*\"([^\"]+)\"|<AccessToken>([^<]+)</AccessToken>");
            if (!match.Success) throw new InvalidOperationException("No AccessToken in token response");
            accessToken = match.Groups[1].Success ? match.Groups[1].Value : match.Groups[2].Value;
        }
        else
        {
            accessToken = (await P21Auth.GetTokenAsync(http, config)).AccessToken;
        }

        P21Auth.SetAuthHeaders(http, accessToken);
        var uiServer = await P21Auth.GetUiServerUrlAsync(http, config.BaseUrl);
        return (http, uiServer, config.BaseUrl);
    }

    /// <summary>
    /// Rows of an OData table (or view) query. Dates stay strings exactly as
    /// the server sent them (no local-time conversion).
    /// </summary>
    public static async Task<JArray> ODataAsync(HttpClient http, string baseUrl, string table,
        string filter, bool view = false, string? select = null)
    {
        var url = $"{baseUrl}/odataservice/odata/{(view ? "view" : "table")}/{table}" +
                  $"?$filter={Uri.EscapeDataString(filter)}" +
                  (select is null ? "" : $"&$select={select}");
        var response = await http.GetAsync(url);
        response.EnsureSuccessStatusCode();
        using var reader = new JsonTextReader(new StringReader(await response.Content.ReadAsStringAsync()))
            { DateParseHandling = DateParseHandling.None };
        return (JArray)JObject.Load(reader)["value"]!;
    }

    /// <summary>POST /api/v2/transaction. Check Summary, not the HTTP status.</summary>
    public static async Task<P21Examples.Common.Models.TransactionResult> PostTransactionAsync(
        HttpClient http, string uiServer, JObject payload)
    {
        var response = await http.PostAsync($"{uiServer}/api/v2/transaction",
            new StringContent(payload.ToString(Formatting.None), Encoding.UTF8, "application/json"));
        return await P21Examples.Common.Models.TransactionResult.FromResponseAsync(response);
    }
}
