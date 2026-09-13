// Other REST Families - Post a GL Journal Entry (accounting/gl)
// Docs: docs/15-Other-REST-Families.md#posting-a-journal-entry-verified
// Mirrors: examples/python/rest/gl_post.py
//
// POSTs a balanced 2-line entry (an array, the same shape the keyed GET
// returns), then reads it back. The server assigns TransactionNumber,
// Approved: true and a SourceTypeCd automatically.
//
// The balance IS enforced server-side: a single unbalanced line is
// refused with "Records do not balance" (P21.Business.Common.
// BusinessException from GlManager.UpdateAllRecords), not silently
// accepted.

using Newtonsoft.Json.Linq;

namespace P21Examples.Rest;

public static class GlPost
{
    public static async Task RunAsync()
    {
        Console.WriteLine("Other REST Families - Post a GL Journal Entry (accounting/gl)");
        Console.WriteLine(new string('=', 60));

        var (http, baseUrl) = await RestHelpers.CreateRawClientAsync();
        using var _ = http;
        Console.WriteLine($"Server: {baseUrl}");

        const string companyId = "ACME";
        // Percent-encode the filter value, matching P21Client.OData's own
        // convention (Uri.EscapeDataString) -- not strictly required by
        // this endpoint, but keeps the query string well-formed regardless
        // of what the filter value contains.
        var filter = Uri.EscapeDataString($"company_no eq '{companyId}' and period_closed eq 'N'");
        var odataUrl = $"{baseUrl}/odataservice/odata/table/periods?$select=period,year_for_period" +
            $"&$filter={filter}&$orderby=year_for_period desc,period desc&$top=1";
        var periodsResp = await http.GetAsync(odataUrl);
        periodsResp.EnsureSuccessStatusCode();
        var periodRow = (JObject.Parse(await periodsResp.Content.ReadAsStringAsync())["value"] as JArray)![0];
        int period = (int)periodRow["period"]!;
        int year = (int)periodRow["year_for_period"]!;
        Console.WriteLine($"Open period: {period}/{year}");

        var lines = new JArray
        {
            new JObject
            {
                ["CompanyNo"] = companyId, ["AccountNumber"] = "11120010",
                ["Period"] = period, ["YearForPeriod"] = year, ["JournalId"] = "AC",
                ["Amount"] = 0.01, ["ForeignAmount"] = 0.01,
                ["Description"] = "ZZ API DOC TEST - safe to delete", ["Source"] = "ZZDOCTEST",
                ["TransactionDate"] = "2026-09-12T00:00:00",
            },
            new JObject
            {
                ["CompanyNo"] = companyId, ["AccountNumber"] = "11130010",
                ["Period"] = period, ["YearForPeriod"] = year, ["JournalId"] = "AC",
                ["Amount"] = -0.01, ["ForeignAmount"] = -0.01,
                ["Description"] = "ZZ API DOC TEST - safe to delete", ["Source"] = "ZZDOCTEST",
                ["TransactionDate"] = "2026-09-12T00:00:00",
            },
        };

        Console.WriteLine("\nPayload:");
        Console.WriteLine(lines.ToString());
        Console.WriteLine("\nNOTE: the balance IS enforced server-side -- an unbalanced batch is " +
                          "refused with \"Records do not balance\", not silently accepted.");

        if (!RestHelpers.ConfirmExecute())
            return;

        var content = new StringContent(lines.ToString());
        content.Headers.ContentType = new System.Net.Http.Headers.MediaTypeHeaderValue("application/json");
        var posted = await http.PostAsync($"{baseUrl}/api/accounting/gl/", content);
        if (!posted.IsSuccessStatusCode)
        {
            Console.WriteLine($"\nPOST failed: HTTP {(int)posted.StatusCode}");
            Console.WriteLine(await posted.Content.ReadAsStringAsync());
            return;
        }

        var postedLines = JArray.Parse(await posted.Content.ReadAsStringAsync());
        var txn = postedLines[0]["TransactionNumber"];
        Console.WriteLine($"\nPosted. TransactionNumber={txn}");
        foreach (var line in postedLines)
            Console.WriteLine($"  {line["AccountNumber"],-14} {(decimal)line["Amount"]!,10:N2}  " +
                              $"Approved={line["Approved"]}  SourceTypeCd={line["SourceTypeCd"]}");

        Console.WriteLine("\nRead-back:");
        Console.WriteLine(new string('-', 50));
        var readBack = await http.GetAsync($"{baseUrl}/api/accounting/gl/{txn}");
        readBack.EnsureSuccessStatusCode();
        var readLines = JArray.Parse(await readBack.Content.ReadAsStringAsync());
        decimal total = 0m;
        foreach (var line in readLines)
        {
            var amount = (decimal)line["Amount"]!;
            total += amount;
            Console.WriteLine($"  {line["AccountNumber"],-14} {amount,10:N2}");
        }
        Console.WriteLine($"  Balance: {total:N2} ({(Math.Abs(total) < 0.005m ? "balanced" : "NOT BALANCED")})");
    }
}
