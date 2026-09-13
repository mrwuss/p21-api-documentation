// Other REST Families - Create a CRM Opportunity (sales/opportunities)
// Docs: docs/15-Other-REST-Families.md#salesopportunities
// Mirrors: examples/python/rest/opportunity_create.py
//
// Checks the tenant's CRM lookup tables before attempting a create -- on
// the play tenant, every one of them is empty, which makes a successful
// create impossible regardless of payload. This is a tenant
// configuration gap, not an API defect.

using System.Net.Http.Headers;
using Newtonsoft.Json.Linq;

namespace P21Examples.Rest;

public static class OpportunityCreate
{
    private static readonly string[] LookupTables =
        { "opportunity_status", "opportunity_stage", "opportunity_type", "opportunity_step" };

    public static async Task RunAsync()
    {
        Console.WriteLine("Other REST Families - Opportunity Create (sales/opportunities)");
        Console.WriteLine(new string('=', 60));

        var (http, baseUrl) = await RestHelpers.CreateRawClientAsync();
        using var _ = http;
        Console.WriteLine($"Server: {baseUrl}");

        Console.WriteLine("\nCRM lookup table row counts (all must be non-zero for a create to succeed):");
        Console.WriteLine(new string('-', 50));
        var allPopulated = true;
        foreach (var table in LookupTables)
        {
            var resp = await http.GetAsync(
                $"{baseUrl}/odataservice/odata/table/{table}?$top=1&$count=true");
            var count = resp.IsSuccessStatusCode
                ? (int?)JObject.Parse(await resp.Content.ReadAsStringAsync())["@odata.count"] ?? 0
                : -1;
            Console.WriteLine($"  {table,-22} {count}");
            if (count <= 0) allPopulated = false;
        }

        if (!allPopulated)
            Console.WriteLine("\nAt least one CRM lookup table is empty on this tenant -- a " +
                              "create cannot succeed regardless of payload. This is a tenant " +
                              "configuration gap, not an API defect.");

        if (!RestHelpers.ConfirmExecute())
            return;

        var oppResp = await http.GetAsync($"{baseUrl}/api/sales/opportunities/new");
        var opp = JObject.Parse(await oppResp.Content.ReadAsStringAsync());
        opp["OpportunityName"] = "ZZ API DOC TEST - safe to delete";
        opp["CompanyId"] = "ACME";
        opp["CustomerId"] = 12066;
        opp["LocationId"] = 40;

        var content = new StringContent(opp.ToString());
        content.Headers.ContentType = new MediaTypeHeaderValue("application/json");
        var resp2 = await http.PostAsync($"{baseUrl}/api/sales/opportunities/", content);
        Console.WriteLine($"\nHTTP {(int)resp2.StatusCode}");
        Console.WriteLine(await resp2.Content.ReadAsStringAsync());
    }
}
