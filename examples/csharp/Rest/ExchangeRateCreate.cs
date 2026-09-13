// Other REST Families - Create an Exchange Rate (accounting/exchangerates)
// Docs: docs/15-Other-REST-Families.md#accountingexchangerates
// Mirrors: examples/python/rest/exchange_rate_create.py
//
// Checks how many currencies the tenant has configured -- the
// verification tenant has exactly one, which makes a genuine
// cross-currency rate impossible regardless of payload. The one
// validation this tenant COULD exercise is real: same currency on both
// sides is refused with "The currencies cannot be the same."

using System.Net.Http.Headers;
using Newtonsoft.Json.Linq;

namespace P21Examples.Rest;

public static class ExchangeRateCreate
{
    public static async Task RunAsync()
    {
        Console.WriteLine("Other REST Families - Exchange Rate Create (accounting/exchangerates)");
        Console.WriteLine(new string('=', 60));

        var (http, baseUrl) = await RestHelpers.CreateRawClientAsync();
        using var _ = http;
        Console.WriteLine($"Server: {baseUrl}");

        var currResp = await http.GetAsync(
            $"{baseUrl}/odataservice/odata/table/currency_hdr?$select=currency_id,currency_desc");
        var currencies = (JObject.Parse(await currResp.Content.ReadAsStringAsync())["value"] as JArray)!;
        Console.WriteLine($"\nConfigured currencies: {currencies}");
        if (currencies.Count < 2)
            Console.WriteLine("Fewer than 2 currencies configured -- a genuine cross-currency " +
                              "rate cannot be created regardless of payload.");

        var payload = new JObject
        {
            ["CurrencyId"] = 1, ["ToCurrencyId"] = 1, ["Rate"] = 1.0,
            ["ExchangeDate"] = "2026-09-12T00:00:00", ["ExchangeCost"] = 0.0,
            ["DeleteFlag"] = false, ["RateType"] = 0,
        };
        Console.WriteLine($"\nPayload (CurrencyId == ToCurrencyId -- will be refused): {payload}");

        if (!RestHelpers.ConfirmExecute())
            return;

        var content = new StringContent(payload.ToString());
        content.Headers.ContentType = new MediaTypeHeaderValue("application/json");
        var resp = await http.PostAsync($"{baseUrl}/api/accounting/exchangerates/", content);
        Console.WriteLine($"\nHTTP {(int)resp.StatusCode}");
        Console.WriteLine(await resp.Content.ReadAsStringAsync());
    }
}
