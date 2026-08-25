using System;
using System.Net.Http;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace P21Examples.Common
{
    /// <summary>
    /// P21 API authentication — token V1/V2, XML/JSON dual parsing.
    /// Mirrors Python examples/python/common/auth.py.
    /// </summary>
    public static class P21Auth
    {
        /// <summary>
        /// Obtain an access token using the V1 endpoint. Only valid for
        /// consumer-key (appkey header) authentication — password auth via V1
        /// puts credentials in HTTP headers, which proxies and log pipelines
        /// capture, and is deliberately not supported. Use GetTokenV2Async
        /// (or GetTokenAsync, which defaults to V2) for passwords.
        /// </summary>
        public static async Task<TokenResponse> GetTokenV1Async(
            HttpClient client, P21Config config)
        {
            if (string.IsNullOrEmpty(config.ConsumerKey))
                throw new InvalidOperationException(
                    "Password authentication requires the V2 endpoint " +
                    "(credentials in the request body). The V1 endpoint puts " +
                    "username/password in HTTP headers, which get captured " +
                    "by proxies and logs. Use GetTokenV2Async instead.");

            var request = new HttpRequestMessage(HttpMethod.Post, config.TokenUrl);
            request.Content = new StringContent("", Encoding.UTF8, "application/json");
            request.Headers.TryAddWithoutValidation("Accept", "application/json");
            request.Headers.TryAddWithoutValidation("appkey", config.ConsumerKey);
            if (!string.IsNullOrEmpty(config.Username))
                request.Headers.TryAddWithoutValidation("username", config.Username);

            var response = await client.SendAsync(request);
            response.EnsureSuccessStatusCode();
            var body = await response.Content.ReadAsStringAsync();
            return ParseTokenResponse(body);
        }

        /// <summary>
        /// Obtain an access token using V2 endpoint (credentials in body).
        /// </summary>
        public static async Task<TokenResponse> GetTokenV2Async(
            HttpClient client, P21Config config)
        {
            object payload;
            if (!string.IsNullOrEmpty(config.ConsumerKey))
            {
                payload = new
                {
                    ClientSecret = config.ConsumerKey,
                    GrantType = "client_credentials",
                    username = config.Username
                };
            }
            else
            {
                payload = new
                {
                    username = config.Username,
                    password = config.Password
                };
            }

            var json = JsonConvert.SerializeObject(payload);
            var content = new StringContent(json, Encoding.UTF8, "application/json");

            var request = new HttpRequestMessage(HttpMethod.Post, config.TokenUrlV2);
            request.Content = content;
            request.Headers.TryAddWithoutValidation("Accept", "application/json");

            var response = await client.SendAsync(request);
            response.EnsureSuccessStatusCode();
            var body = await response.Content.ReadAsStringAsync();
            return ParseTokenResponse(body);
        }

        /// <summary>
        /// Get token using the default method (V2 — credentials in the body).
        /// Pass useV2: false only for consumer-key (appkey header) auth;
        /// password auth via V1 throws.
        /// </summary>
        public static async Task<TokenResponse> GetTokenAsync(
            HttpClient client, P21Config config, bool useV2 = true)
        {
            return useV2
                ? await GetTokenV2Async(client, config)
                : await GetTokenV1Async(client, config);
        }

        /// <summary>
        /// Build standard authorization headers for API requests.
        /// </summary>
        public static void SetAuthHeaders(HttpClient client, string accessToken)
        {
            client.DefaultRequestHeaders.Clear();
            client.DefaultRequestHeaders.TryAddWithoutValidation(
                "Authorization", $"Bearer {accessToken}");
            client.DefaultRequestHeaders.TryAddWithoutValidation(
                "Accept", "application/json");
        }

        /// <summary>
        /// Get the UI Server URL for Interactive/Transaction API calls.
        ///
        /// The trailing slash after v1 is required, not cosmetic. Without it
        /// the server answers 307 to the trailing-slash form, and HttpClient
        /// strips the Authorization header when it follows a redirect — so the
        /// second request arrives unauthenticated and the call fails with 401
        /// "Authorization header was not present or 'Bearer' was missing."
        /// </summary>
        public static async Task<string> GetUiServerUrlAsync(
            HttpClient client, string baseUrl)
        {
            var response = await client.GetAsync(
                $"{baseUrl}/api/ui/router/v1/?urlType=external");
            response.EnsureSuccessStatusCode();
            var body = await response.Content.ReadAsStringAsync();

            // Try JSON first (mirrors ParseTokenResponse's dual-format approach)
            try
            {
                var data = JObject.Parse(body);
                var jsonUrl = data["Url"]?.ToString();
                if (!string.IsNullOrEmpty(jsonUrl))
                    return jsonUrl.TrimEnd('/');
            }
            catch (JsonReaderException)
            {
                // Not valid JSON — fall through to XML parsing
            }

            // Fall back to XML (some P21 instances return XML from the router)
            var match = Regex.Match(body, @"<Url>([^<]+)</Url>");
            if (match.Success)
                return match.Groups[1].Value.TrimEnd('/');

            throw new InvalidOperationException(
                $"Could not parse Url from router response: {body.Substring(0, Math.Min(500, body.Length))}");
        }

        /// <summary>
        /// Parse token response, handling both JSON and XML formats.
        /// Some P21 instances return XML instead of JSON.
        /// </summary>
        internal static TokenResponse ParseTokenResponse(string body)
        {
            // Try JSON first
            try
            {
                var obj = JObject.Parse(body);
                var accessToken = obj["AccessToken"]?.ToString()
                    ?? obj["access_token"]?.ToString();
                if (!string.IsNullOrEmpty(accessToken))
                {
                    return new TokenResponse
                    {
                        AccessToken = accessToken,
                        TokenType = obj["TokenType"]?.ToString() ?? "Bearer",
                        ExpiresInSeconds = int.TryParse(
                            obj["ExpiresInSeconds"]?.ToString()
                            ?? obj["ExpiresIn"]?.ToString(),
                            out var exp) ? exp : 3600,
                        RefreshToken = obj["RefreshToken"]?.ToString(),
                        SessionId = obj["SessionId"]?.ToString()
                    };
                }
            }
            catch (JsonReaderException)
            {
                // Not valid JSON — fall through to XML parsing
            }

            // Fall back to XML regex parsing (handles namespaces, BOM, etc.)
            var token = ExtractXmlField(body, "AccessToken");
            if (string.IsNullOrEmpty(token))
                throw new InvalidOperationException(
                    $"Could not parse AccessToken from response: {body.Substring(0, Math.Min(500, body.Length))}");

            return new TokenResponse
            {
                AccessToken = token,
                TokenType = ExtractXmlField(body, "TokenType") ?? "Bearer",
                ExpiresInSeconds = int.TryParse(
                    ExtractXmlField(body, "ExpiresIn")
                    ?? ExtractXmlField(body, "ExpiresInSeconds"),
                    out var xmlExp) ? xmlExp : 3600,
                RefreshToken = ExtractXmlField(body, "RefreshToken"),
                SessionId = ExtractXmlField(body, "SessionId")
            };
        }

        private static string? ExtractXmlField(string xml, string field)
        {
            var match = Regex.Match(xml, $@"<{field}>([^<]*)</{field}>");
            return match.Success && !string.IsNullOrEmpty(match.Groups[1].Value)
                ? match.Groups[1].Value
                : null;
        }
    }

    /// <summary>
    /// Token response from P21 authentication endpoints.
    /// </summary>
    public class TokenResponse
    {
        public string AccessToken { get; set; } = "";
        public string TokenType { get; set; } = "Bearer";
        public int ExpiresInSeconds { get; set; } = 3600;
        public string? RefreshToken { get; set; }
        public string? SessionId { get; set; }
    }
}
