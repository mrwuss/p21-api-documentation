using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using Newtonsoft.Json.Linq;

namespace P21Examples.Common.Models
{
    /// <summary>
    /// Interactive API response.
    /// Status codes: 0=None, 1=Success, 2=Failure, 3=Blocked
    /// </summary>
    public class InteractiveResult
    {
        public int HttpStatusCode { get; set; }
        public bool Success { get; set; }
        public int Status { get; set; }
        public JToken? Data { get; set; }
        public List<string> Messages { get; set; } = new();
        public List<JObject> Events { get; set; } = new();
        public string? WindowId { get; set; }
        public string? RawBody { get; set; }

        public static InteractiveResult FromResponse(
            HttpResponseMessage response, string body)
        {
            var result = new InteractiveResult
            {
                HttpStatusCode = (int)response.StatusCode,
                RawBody = body
            };

            try
            {
                var obj = JObject.Parse(body);
                result.Data = obj;
                result.WindowId = obj["WindowId"]?.ToString()
                    ?? obj["windowId"]?.ToString();

                // Status: usually an integer (0=None, 1=Success, 2=Failure,
                // 3=Blocked), but some serialization contexts return the
                // enum name as a string — handle both without throwing.
                result.Status = ParseStatus(obj["Status"]);

                // Messages
                var msgs = obj["Messages"] ?? obj["messages"];
                if (msgs is JArray msgArray)
                    result.Messages = msgArray.Select(m => m.ToString()).ToList();
                else if (msgs != null)
                    result.Messages = new List<string> { msgs.ToString() };

                // Events
                var events = obj["Events"] ?? obj["events"];
                if (events is JArray eventArray)
                    result.Events = eventArray.OfType<JObject>().ToList();

                result.Success = result.HttpStatusCode is 200 or 201
                    && result.Status != 2 && result.Status != 3;
            }
            catch
            {
                result.Success = result.HttpStatusCode is 200 or 201;
            }

            return result;
        }

        /// <summary>
        /// Parse the Status token as an integer or as an enum-name string
        /// ("None"/"Success"/"Failure"/"Blocked", or a numeric string).
        /// Never throws; unknown values map to 0 (None).
        /// </summary>
        internal static int ParseStatus(JToken? token)
        {
            if (token == null || token.Type == JTokenType.Null)
                return 0;

            if (token.Type == JTokenType.Integer)
                return token.Value<int>();

            var text = token.ToString().Trim();
            if (int.TryParse(text, out var numeric))
                return numeric;

            return text.ToLowerInvariant() switch
            {
                "none" => 0,
                "success" => 1,
                "failure" => 2,
                "blocked" => 3,
                _ => 0
            };
        }

        /// <summary>
        /// Extract auto-generated key from events (e.g., new record ID).
        /// </summary>
        public string? GetGeneratedKey()
        {
            foreach (var evt in Events)
            {
                var name = (evt["Name"] ?? evt["name"])?.ToString() ?? "";
                if (name.ToLower() == "generatedkey")
                    return (evt["Data"] ?? evt["data"])?.ToString();
            }
            return null;
        }

        /// <summary>
        /// Extract window ID from a "windowopened" event (response windows).
        /// Event Data is a KV-list: [{"Key": "windowid", "Value": "..."}]
        /// </summary>
        public string? GetOpenedWindowId()
        {
            foreach (var evt in Events)
            {
                var name = (evt["Name"] ?? evt["name"])?.ToString() ?? "";
                if (name.ToLower() != "windowopened") continue;

                var data = evt["Data"] ?? evt["data"];
                if (data is JArray kvList)
                {
                    foreach (var item in kvList.OfType<JObject>())
                    {
                        var key = (item["Key"] ?? item["key"])?.ToString() ?? "";
                        if (key.ToLower() == "windowid")
                            return (item["Value"] ?? item["value"])?.ToString();
                    }
                }
                else if (data is JObject dict)
                {
                    return (dict["WindowId"] ?? dict["windowId"])?.ToString();
                }
                else if (data != null)
                {
                    return data.ToString();
                }
            }
            return null;
        }
    }
}
