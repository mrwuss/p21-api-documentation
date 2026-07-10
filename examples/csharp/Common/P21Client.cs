using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using P21Examples.Common.Models;

namespace P21Examples.Common
{
    /// <summary>
    /// Raw HttpClient wrapper for all P21 APIs.
    /// Mirrors Python examples/python/common/client.py.
    ///
    /// Usage:
    ///     using var client = await P21Client.CreateAsync();
    ///     var services = await client.Transaction.ListServicesAsync();
    ///     var rows = await client.OData.QueryAsync("supplier", top: 5);
    /// </summary>
    public class P21Client : IDisposable
    {
        private readonly HttpClient _http;
        private readonly P21Config _config;
        private string? _uiServerUrl;

        public ODataApi OData { get; }
        public TransactionApi Transaction { get; }
        public InteractiveApi Interactive { get; }
        public EntityApi Entity { get; }

        private P21Client(HttpClient http, P21Config config, string uiServerUrl)
        {
            _http = http;
            _config = config;
            _uiServerUrl = uiServerUrl;

            OData = new ODataApi(http, config.ODataUrl);
            Transaction = new TransactionApi(http, uiServerUrl);
            Interactive = new InteractiveApi(http, uiServerUrl);
            Entity = new EntityApi(http, config.EntityUrl);
        }

        /// <summary>
        /// Create an authenticated P21 client from environment variables.
        /// </summary>
        public static async Task<P21Client> CreateAsync(P21Config? config = null)
        {
            config ??= P21Config.FromEnvironment();

            var handler = new HttpClientHandler();
            if (!config.VerifySsl)
            {
                handler.ServerCertificateCustomValidationCallback =
                    HttpClientHandler.DangerousAcceptAnyServerCertificateValidator;
            }

            var http = new HttpClient(handler) { Timeout = TimeSpan.FromSeconds(60) };

            // Authenticate
            var token = await P21Auth.GetTokenAsync(http, config);
            P21Auth.SetAuthHeaders(http, token.AccessToken);

            // Get UI Server URL
            var uiServerUrl = await P21Auth.GetUiServerUrlAsync(http, config.BaseUrl);

            return new P21Client(http, config, uiServerUrl);
        }

        public void Dispose()
        {
            _http.Dispose();
        }
    }

    // =========================================================================
    // OData API
    // =========================================================================

    public class ODataApi
    {
        private readonly HttpClient _http;
        private readonly string _baseUrl;

        public ODataApi(HttpClient http, string baseUrl)
        {
            _http = http;
            _baseUrl = baseUrl;
        }

        /// <summary>
        /// Query a table. Returns the parsed JSON response.
        /// </summary>
        public async Task<JObject> QueryAsync(
            string table,
            string? select = null,
            string? filter = null,
            int? top = null,
            int? skip = null,
            string? orderby = null,
            bool count = false)
        {
            var queryParams = BuildODataParams(select, filter, top, skip, orderby, count);
            var url = $"{_baseUrl}/table/{table}{queryParams}";
            var response = await _http.GetAsync(url);
            response.EnsureSuccessStatusCode();
            var json = await response.Content.ReadAsStringAsync();
            return JObject.Parse(json);
        }

        /// <summary>
        /// Query a view. Returns the parsed JSON response.
        /// </summary>
        public async Task<JObject> QueryViewAsync(
            string view,
            string? select = null,
            string? filter = null,
            int? top = null,
            int? skip = null,
            string? orderby = null,
            bool count = false)
        {
            var queryParams = BuildODataParams(select, filter, top, skip, orderby, count);
            var url = $"{_baseUrl}/view/{view}{queryParams}";
            var response = await _http.GetAsync(url);
            response.EnsureSuccessStatusCode();
            var json = await response.Content.ReadAsStringAsync();
            return JObject.Parse(json);
        }

        private static string BuildODataParams(
            string? select, string? filter, int? top, int? skip,
            string? orderby, bool count)
        {
            var parts = new List<string>();
            if (!string.IsNullOrEmpty(select)) parts.Add($"$select={select}");
            if (!string.IsNullOrEmpty(filter)) parts.Add($"$filter={Uri.EscapeDataString(filter)}");
            if (top.HasValue) parts.Add($"$top={top}");
            if (skip.HasValue) parts.Add($"$skip={skip}");
            if (!string.IsNullOrEmpty(orderby)) parts.Add($"$orderby={orderby}");
            if (count) parts.Add("$count=true");
            return parts.Count > 0 ? "?" + string.Join("&", parts) : "";
        }
    }

    // =========================================================================
    // Transaction API
    // =========================================================================

    public class TransactionApi
    {
        private readonly HttpClient _http;
        private readonly string _uiServer;

        public TransactionApi(HttpClient http, string uiServer)
        {
            _http = http;
            _uiServer = uiServer;
        }

        public async Task<JArray> ListServicesAsync()
        {
            var response = await _http.GetAsync($"{_uiServer}/api/v2/services");
            response.EnsureSuccessStatusCode();
            var json = await response.Content.ReadAsStringAsync();
            return JArray.Parse(json);
        }

        public async Task<JObject> GetDefinitionAsync(string serviceName)
        {
            var response = await _http.GetAsync(
                $"{_uiServer}/api/v2/definition/{serviceName}");
            response.EnsureSuccessStatusCode();
            var json = await response.Content.ReadAsStringAsync();
            return JObject.Parse(json);
        }

        public async Task<JObject> GetDefaultsAsync(string serviceName)
        {
            var response = await _http.GetAsync(
                $"{_uiServer}/api/v2/defaults/{serviceName}");
            response.EnsureSuccessStatusCode();
            var json = await response.Content.ReadAsStringAsync();
            return JObject.Parse(json);
        }

        public async Task<TransactionResult> CreateAsync(object payload)
        {
            var content = new StringContent(
                JsonConvert.SerializeObject(payload),
                Encoding.UTF8,
                "application/json");
            var response = await _http.PostAsync(
                $"{_uiServer}/api/v2/transaction", content);
            return await TransactionResult.FromResponseAsync(response);
        }

        public async Task<JObject> CreateAsyncOperation(object payload)
        {
            var content = new StringContent(
                JsonConvert.SerializeObject(payload),
                Encoding.UTF8,
                "application/json");
            var response = await _http.PostAsync(
                $"{_uiServer}/api/v2/transaction/async", content);
            response.EnsureSuccessStatusCode();
            var json = await response.Content.ReadAsStringAsync();
            return JObject.Parse(json);
        }

        public async Task<JObject> GetAsyncStatusAsync(string requestId)
        {
            var response = await _http.GetAsync(
                $"{_uiServer}/api/v2/transaction/async?id={requestId}");
            response.EnsureSuccessStatusCode();
            var json = await response.Content.ReadAsStringAsync();
            return JObject.Parse(json);
        }

        public async Task<JObject> GetRecordsAsync(object payload)
        {
            var content = new StringContent(
                JsonConvert.SerializeObject(payload),
                Encoding.UTF8,
                "application/json");
            var response = await _http.PostAsync(
                $"{_uiServer}/api/v2/transaction/get", content);
            response.EnsureSuccessStatusCode();
            var json = await response.Content.ReadAsStringAsync();
            return JObject.Parse(json);
        }
    }

    // =========================================================================
    // Interactive API
    // =========================================================================

    public class InteractiveApi
    {
        private readonly HttpClient _http;
        private readonly string _uiServer;

        public InteractiveApi(HttpClient http, string uiServer)
        {
            _http = http;
            _uiServer = uiServer;
        }

        /// <summary>
        /// Create an interactive session (use as IAsyncDisposable).
        /// </summary>
        public InteractiveSession CreateSession(bool responseWindows = false)
        {
            return new InteractiveSession(_http, _uiServer, responseWindows);
        }
    }

    /// <summary>
    /// Interactive API session — IAsyncDisposable for automatic cleanup.
    /// Mirrors Python InteractiveSession context manager.
    /// </summary>
    public class InteractiveSession : IAsyncDisposable
    {
        private readonly HttpClient _http;
        private readonly string _uiServer;
        private readonly bool _responseWindows;
        private bool _started;

        public InteractiveSession(HttpClient http, string uiServer, bool responseWindows)
        {
            _http = http;
            _uiServer = uiServer;
            _responseWindows = responseWindows;
        }

        public async Task StartAsync()
        {
            var payload = new { ResponseWindowHandlingEnabled = _responseWindows };
            var content = new StringContent(
                JsonConvert.SerializeObject(payload),
                Encoding.UTF8,
                "application/json");
            var response = await _http.PostAsync(
                $"{_uiServer}/api/ui/interactive/sessions", content);
            response.EnsureSuccessStatusCode();
            _started = true;
        }

        public async Task EndAsync()
        {
            if (!_started) return;
            try
            {
                await _http.DeleteAsync($"{_uiServer}/api/ui/interactive/sessions");
            }
            catch
            {
                // Cleanup errors are ignored
            }
            _started = false;
        }

        public async Task<InteractiveWindow> OpenWindowAsync(
            string? serviceName = null, string? title = null)
        {
            var payload = new JObject();
            if (!string.IsNullOrEmpty(serviceName))
                payload["ServiceName"] = serviceName;
            if (!string.IsNullOrEmpty(title))
                payload["Title"] = title;

            var content = new StringContent(
                payload.ToString(),
                Encoding.UTF8,
                "application/json");
            var response = await _http.PostAsync(
                $"{_uiServer}/api/ui/interactive/v2/window", content);
            response.EnsureSuccessStatusCode();

            var json = await response.Content.ReadAsStringAsync();
            var data = JObject.Parse(json);
            var windowId = data["WindowId"]?.ToString()
                ?? throw new InvalidOperationException(
                    $"No WindowId in response: {json}");

            return new InteractiveWindow(windowId, _http, _uiServer);
        }

        public async ValueTask DisposeAsync()
        {
            await EndAsync();
        }
    }

    /// <summary>
    /// Interactive API window handle.
    /// Mirrors Python Window class.
    /// </summary>
    public class InteractiveWindow
    {
        public string WindowId { get; }
        private readonly HttpClient _http;
        private readonly string _uiServer;

        public InteractiveWindow(string windowId, HttpClient http, string uiServer)
        {
            WindowId = windowId;
            _http = http;
            _uiServer = uiServer;
        }

        /// <summary>
        /// Change a field value (v2 format).
        /// DatawindowName is required in P21 25.2+.
        /// </summary>
        public async Task<InteractiveResult> ChangeDataAsync(
            string tabName, string fieldName, string value,
            string datawindowName = "")
        {
            var change = new JObject
            {
                ["TabName"] = tabName,
                ["FieldName"] = fieldName,
                ["Value"] = value
            };
            if (!string.IsNullOrEmpty(datawindowName))
                change["DatawindowName"] = datawindowName;

            var payload = new JObject
            {
                ["WindowId"] = WindowId,
                ["List"] = new JArray { change }
            };
            return await PutAsync("change", payload);
        }

        /// <summary>
        /// Change multiple fields at once (v2 format).
        /// </summary>
        public async Task<InteractiveResult> ChangeFieldsAsync(
            string tabName, Dictionary<string, string> fields,
            string datawindowName = "")
        {
            var changes = new JArray();
            foreach (var kvp in fields)
            {
                var change = new JObject
                {
                    ["TabName"] = tabName,
                    ["FieldName"] = kvp.Key,
                    ["Value"] = kvp.Value
                };
                if (!string.IsNullOrEmpty(datawindowName))
                    change["DatawindowName"] = datawindowName;
                changes.Add(change);
            }

            var payload = new JObject
            {
                ["WindowId"] = WindowId,
                ["List"] = changes
            };
            return await PutAsync("change", payload);
        }

        /// <summary>
        /// Save data (v2 format: bare GUID string body).
        /// </summary>
        public async Task<InteractiveResult> SaveDataAsync()
        {
            var content = new StringContent(
                JsonConvert.SerializeObject(WindowId),
                Encoding.UTF8,
                "application/json");
            var response = await _http.PutAsync(
                $"{_uiServer}/api/ui/interactive/v2/data", content);
            return InteractiveResult.FromResponse(response,
                await response.Content.ReadAsStringAsync());
        }

        /// <summary>
        /// Get current window data.
        /// </summary>
        public async Task<InteractiveResult> GetDataAsync()
        {
            var response = await _http.GetAsync(
                $"{_uiServer}/api/ui/interactive/v2/data?id={WindowId}");
            return InteractiveResult.FromResponse(response,
                await response.Content.ReadAsStringAsync());
        }

        /// <summary>
        /// Clear data (new record mode).
        /// </summary>
        public async Task<InteractiveResult> ClearDataAsync()
        {
            var response = await _http.DeleteAsync(
                $"{_uiServer}/api/ui/interactive/v2/data?id={WindowId}");
            return InteractiveResult.FromResponse(response,
                await response.Content.ReadAsStringAsync());
        }

        /// <summary>
        /// Change active tab.
        /// </summary>
        public async Task<InteractiveResult> SelectTabAsync(string pageName)
        {
            var payload = new JObject
            {
                ["WindowId"] = WindowId,
                ["PageName"] = pageName
            };
            return await PutAsync("tab", payload);
        }

        /// <summary>
        /// Get available tools/buttons for this window.
        /// </summary>
        public async Task<InteractiveResult> GetToolsAsync()
        {
            var response = await _http.GetAsync(
                $"{_uiServer}/api/ui/interactive/v2/tools?windowId={WindowId}");
            return InteractiveResult.FromResponse(response,
                await response.Content.ReadAsStringAsync());
        }

        /// <summary>
        /// Run a tool/button.
        /// </summary>
        public async Task<InteractiveResult> RunToolAsync(
            string toolName, string toolText = "")
        {
            var payload = new JObject
            {
                ["WindowId"] = WindowId,
                ["ToolName"] = toolName,
                ["ToolText"] = toolText
            };
            var content = new StringContent(
                payload.ToString(), Encoding.UTF8, "application/json");
            var response = await _http.PostAsync(
                $"{_uiServer}/api/ui/interactive/v2/tools", content);
            return InteractiveResult.FromResponse(response,
                await response.Content.ReadAsStringAsync());
        }

        /// <summary>
        /// Close this window.
        /// </summary>
        public async Task<InteractiveResult> CloseAsync()
        {
            var response = await _http.DeleteAsync(
                $"{_uiServer}/api/ui/interactive/v2/window?id={WindowId}");
            return InteractiveResult.FromResponse(response,
                await response.Content.ReadAsStringAsync());
        }

        private async Task<InteractiveResult> PutAsync(string endpoint, JObject payload)
        {
            var content = new StringContent(
                payload.ToString(), Encoding.UTF8, "application/json");
            var response = await _http.PutAsync(
                $"{_uiServer}/api/ui/interactive/v2/{endpoint}", content);
            return InteractiveResult.FromResponse(response,
                await response.Content.ReadAsStringAsync());
        }
    }

    // =========================================================================
    // Entity API
    // =========================================================================

    public class EntityApi
    {
        private readonly HttpClient _http;
        private readonly string _baseUrl;

        public EntityApi(HttpClient http, string baseUrl)
        {
            _http = http;
            _baseUrl = baseUrl;
        }

        public async Task<JObject> PingAsync(string resource = "customers")
        {
            var response = await _http.GetAsync($"{_baseUrl}/{resource}/ping");
            response.EnsureSuccessStatusCode();
            var json = await response.Content.ReadAsStringAsync();
            return JObject.Parse(json);
        }

        public async Task<JObject> GetAsync(
            string resource, string key, string? extendedProperties = null)
        {
            var url = $"{_baseUrl}/{resource}/{key}";
            if (!string.IsNullOrEmpty(extendedProperties))
                url += $"?extendedproperties={Uri.EscapeDataString(extendedProperties)}";

            var response = await _http.GetAsync(url);
            response.EnsureSuccessStatusCode();
            var json = await response.Content.ReadAsStringAsync();
            return JObject.Parse(json);
        }

        public async Task<JToken> ListAsync(string resource, string? query = null)
        {
            var url = $"{_baseUrl}/{resource}/";
            if (!string.IsNullOrEmpty(query))
                url += $"?$query={Uri.EscapeDataString(query)}";

            var response = await _http.GetAsync(url);
            response.EnsureSuccessStatusCode();
            var json = await response.Content.ReadAsStringAsync();
            return JToken.Parse(json);
        }

        public async Task<JObject> GetTemplateAsync(string resource)
        {
            var response = await _http.GetAsync($"{_baseUrl}/{resource}/new");
            response.EnsureSuccessStatusCode();
            var json = await response.Content.ReadAsStringAsync();
            return JObject.Parse(json);
        }

        public async Task<JObject> CreateAsync(string resource, object data)
        {
            var content = new StringContent(
                JsonConvert.SerializeObject(data),
                Encoding.UTF8,
                "application/json");
            var response = await _http.PostAsync($"{_baseUrl}/{resource}", content);
            response.EnsureSuccessStatusCode();
            var json = await response.Content.ReadAsStringAsync();
            return JObject.Parse(json);
        }

        public async Task<JObject> UpdateAsync(string resource, string key, object data)
        {
            var content = new StringContent(
                JsonConvert.SerializeObject(data),
                Encoding.UTF8,
                "application/json");
            var response = await _http.PutAsync(
                $"{_baseUrl}/{resource}/{key}", content);
            response.EnsureSuccessStatusCode();
            var json = await response.Content.ReadAsStringAsync();
            return JObject.Parse(json);
        }
    }
}
