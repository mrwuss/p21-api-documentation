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
    /// Mirrors Python scripts/common/auth.py.
    /// </summary>
    public static class P21Auth
    {
        /// <summary>
        /// Obtain an access token using V1 endpoint (credentials in headers).
        /// </summary>
        public static async Task<TokenResponse> GetTokenV1Async(
            HttpClient client, P21Config config)
        {
            var request = new HttpRequestMessage(HttpMethod.Post, config.TokenUrl);
            request.Content = new StringContent("", Encoding.UTF8, "application/json");
            request.Headers.TryAddWithoutValidation("Accept", "application/json");

            if (!string.IsNullOrEmpty(config.ConsumerKey))
            {
                request.Headers.TryAddWithoutValidation("appkey", config.ConsumerKey);
                if (!string.IsNullOrEmpty(config.Username))
                    request.Headers.TryAddWithoutValidation("username", config.Username);
            }
            else
            {
                request.Headers.TryAddWithoutValidation("username", config.Username);
                request.Headers.TryAddWithoutValidation("password", config.Password);
            }

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
        /// Get token using the default method (V1).
        /// </summary>
        public static async Task<TokenResponse> GetTokenAsync(
            HttpClient client, P21Config config, bool useV2 = false)
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
        /// </summary>
        public static async Task<string> GetUiServerUrlAsync(
            HttpClient client, string baseUrl)
        {
            var response = await client.GetAsync(
                $"{baseUrl}/api/ui/router/v1?urlType=external");
            response.EnsureSuccessStatusCode();
            var json = await response.Content.ReadAsStringAsync();
            var data = JObject.Parse(json);
            return data["Url"]!.ToString().TrimEnd('/');
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
