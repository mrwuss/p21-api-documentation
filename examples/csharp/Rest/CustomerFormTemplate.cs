// Other REST Families - Customer Form Template Create/Update
// (accounting/customerformtemplates)
// Docs: docs/15-Other-REST-Families.md#accountingcustomerformtemplates
// Mirrors: examples/python/rest/customer_form_template.py
//
// PUT is the only write verb -- there is no POST -- but PUT is NOT a
// blind upsert: a null CustomerFormTemplateUid means create, and create
// fails "data already exists" if that customer already has a row. There
// is also no keyed GET on this REST family (only the unbounded list), so
// this checks OData for an existing row instead of pulling the whole list.

using System.Net.Http.Headers;
using Newtonsoft.Json.Linq;

namespace P21Examples.Rest;

public static class CustomerFormTemplate
{
    public static async Task RunAsync()
    {
        Console.WriteLine("Other REST Families - Customer Form Template (customerformtemplates)");
        Console.WriteLine(new string('=', 60));

        var (http, baseUrl) = await RestHelpers.CreateRawClientAsync();
        using var _ = http;
        Console.WriteLine($"Server: {baseUrl}");

        const int customerId = 12066;
        const string companyId = "ACME";

        var existingResp = await http.GetAsync(
            $"{baseUrl}/odataservice/odata/table/customer_form_template" +
            $"?$select=customer_form_template_uid&$filter=customer_id eq {customerId} " +
            $"and company_id eq '{companyId}'");
        var existingRows = (JObject.Parse(await existingResp.Content.ReadAsStringAsync())["value"] as JArray)!;
        var existingUid = existingRows.Count > 0 ? existingRows[0]["customer_form_template_uid"] : null;
        Console.WriteLine($"\nExisting row check: {(existingUid != null ? "UPDATE (row exists)" : "CREATE (no row yet)")}");

        var templateResp = await http.GetAsync($"{baseUrl}/api/accounting/customerformtemplates/new");
        var template = JObject.Parse(await templateResp.Content.ReadAsStringAsync());
        template["CustomerFormTemplateUid"] = existingUid;
        template["CustomerId"] = customerId;
        template["CompanyId"] = companyId;
        template["InvoiceFilename"] = "ZZTEST.rpt";

        Console.WriteLine("\nPayload:");
        Console.WriteLine(template.ToString());
        Console.WriteLine("\nNOTE: PUT with a null CustomerFormTemplateUid against a customer " +
                          "that already has a row FAILS rather than updating it.");

        if (!RestHelpers.ConfirmExecute())
            return;

        var content = new StringContent(template.ToString());
        content.Headers.ContentType = new MediaTypeHeaderValue("application/json");
        var resp = await http.PutAsync($"{baseUrl}/api/accounting/customerformtemplates/", content);
        if (!resp.IsSuccessStatusCode)
        {
            Console.WriteLine($"\nFailed: HTTP {(int)resp.StatusCode}");
            Console.WriteLine(await resp.Content.ReadAsStringAsync());
            return;
        }

        var result = JObject.Parse(await resp.Content.ReadAsStringAsync());
        Console.WriteLine($"\nCustomerFormTemplateUid={result["CustomerFormTemplateUid"]}  " +
                          $"InvoiceFilename={result["InvoiceFilename"]}");
    }
}
