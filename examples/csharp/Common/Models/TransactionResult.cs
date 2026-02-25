using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Threading.Tasks;
using Newtonsoft.Json.Linq;

namespace P21Examples.Common.Models
{
    /// <summary>
    /// Transaction API response.
    /// </summary>
    public class TransactionResult
    {
        public int HttpStatusCode { get; set; }
        public int Succeeded { get; set; }
        public int Failed { get; set; }
        public List<string> Messages { get; set; } = new();
        public JToken? Results { get; set; }
        public JObject? Raw { get; set; }

        public static async Task<TransactionResult> FromResponseAsync(
            HttpResponseMessage response)
        {
            var result = new TransactionResult
            {
                HttpStatusCode = (int)response.StatusCode
            };

            var body = await response.Content.ReadAsStringAsync();
            try
            {
                var obj = JObject.Parse(body);
                result.Raw = obj;

                var summary = obj["Summary"] as JObject;
                if (summary != null)
                {
                    result.Succeeded = summary["Succeeded"]?.Value<int>() ?? 0;
                    result.Failed = summary["Failed"]?.Value<int>() ?? 0;
                }

                var msgs = obj["Messages"];
                if (msgs is JArray msgArray)
                    result.Messages = msgArray.Select(m => m.ToString()).ToList();
                else if (msgs != null)
                    result.Messages = new List<string> { msgs.ToString() };

                result.Results = obj["Results"];
            }
            catch
            {
                result.Messages.Add(body.Length > 500 ? body.Substring(0, 500) : body);
            }

            return result;
        }
    }
}
