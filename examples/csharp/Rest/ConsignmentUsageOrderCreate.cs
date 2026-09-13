// Other REST Families - Create a Consignment Usage Order
// (sales/consignmentusageorders)
// Docs: docs/15-Other-REST-Families.md#salesconsignmentusageorders
// Mirrors: examples/python/rest/consignment_usage_order_create.py
//
// Attempts a create and surfaces the real blocker: a CUO bills against
// an existing consignment contract, and the error names the field
// plainly once you unwrap the <ImportReturn> XML -- "Contract ID is
// required." No consignment_contract-named OData object was found on
// the verification tenant; whether a JobContractPricing contract number
// satisfies ContractId is unresolved.

using System.Net.Http.Headers;
using Newtonsoft.Json.Linq;

namespace P21Examples.Rest;

public static class ConsignmentUsageOrderCreate
{
    public static async Task RunAsync()
    {
        Console.WriteLine("Other REST Families - CUO Create (sales/consignmentusageorders)");
        Console.WriteLine(new string('=', 60));

        var (http, baseUrl) = await RestHelpers.CreateRawClientAsync();
        using var _ = http;
        Console.WriteLine($"Server: {baseUrl}");

        var newResp = await http.GetAsync($"{baseUrl}/api/sales/consignmentusageorders/new");
        var cuo = JObject.Parse(await newResp.Content.ReadAsStringAsync());
        cuo["CustomerId"] = 12066;
        cuo["CompanyId"] = "ACME";
        cuo["LocationId"] = 40;
        cuo["PoNo"] = "ZZ-CUO-TEST";
        cuo["OrderDate"] = "2026-09-12T00:00:00";

        Console.WriteLine("\nPayload does not include ContractId -- this WILL fail with " +
                          "'Contract ID is required.' unless you find a real consignment " +
                          "contract number on your tenant first.");

        if (!RestHelpers.ConfirmExecute())
            return;

        var content = new StringContent(cuo.ToString());
        content.Headers.ContentType = new MediaTypeHeaderValue("application/json");
        var resp = await http.PostAsync($"{baseUrl}/api/sales/consignmentusageorders/", content);
        Console.WriteLine($"\nHTTP {(int)resp.StatusCode}");
        Console.WriteLine(await resp.Content.ReadAsStringAsync());
    }
}
