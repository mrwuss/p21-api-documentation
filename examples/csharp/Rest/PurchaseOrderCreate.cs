// Other REST Families - Create a Purchase Order (purchasing/purchaseorders)
// Docs: docs/15-Other-REST-Families.md#creating-a-po-verified
// Mirrors: examples/python/rest/purchase_order_create.py
//
// Two undocumented preconditions found live, 26.1.5950.0:
//   - An empty BuyerId (its value in the /new template) fails with an
//     escaped <ImportReturn> XML error naming "Invalid buyer ID" AND an
//     unrelated-looking "Sales/Production/PO Intersection" complaint --
//     the second is cascade noise from the first. Supply a real BuyerId.
//   - UnitPrice sent on create is NOT honored -- stored as 0.00 regardless
//     (PriceEdit: "N" routes pricing through lookup instead). Use the
//     Transaction API PurchaseOrder service when price must be exact.
//
// POLines comes back POPULATED on this create response -- the only place
// this family's child collections are not null. An immediate GET on the
// same PO still returns POLines: null.

using System.Net.Http.Headers;
using Newtonsoft.Json.Linq;

namespace P21Examples.Rest;

public static class PurchaseOrderCreate
{
    public static async Task RunAsync()
    {
        Console.WriteLine("Other REST Families - Create a Purchase Order (purchasing/purchaseorders)");
        Console.WriteLine(new string('=', 60));

        var (http, baseUrl) = await RestHelpers.CreateRawClientAsync();
        using var _ = http;
        Console.WriteLine($"Server: {baseUrl}");

        var templateResp = await http.GetAsync($"{baseUrl}/api/purchasing/purchaseorders/new");
        templateResp.EnsureSuccessStatusCode();
        var po = JObject.Parse(await templateResp.Content.ReadAsStringAsync());

        po["CompanyNo"] = "ACME";
        po["LocationId"] = 20;
        po["VendorId"] = 25753;
        po["SupplierId"] = 25753;
        po["PoType"] = "S";
        po["OrderDate"] = "2026-09-12T00:00:00";
        po["DateDue"] = "2026-09-19T00:00:00";
        po["Terms"] = "1";
        po["CarrierId"] = "100";
        // Empty BuyerId is the trap -- "Customer ID is required"'s PO-family sibling.
        po["BuyerId"] = "812";
        po["PoDesc"] = "ZZ API DOC TEST - safe to delete (REST create)";

        var line = (JObject)((JArray)po["POLines"]!["list"]!)[0];
        line["ItemId"] = "ETS-727K-G-006";
        line["UnitOfMeasure"] = "EA";
        line["UnitQuantity"] = 1;
        line["PricingUnit"] = "EA";
        line["UnitPrice"] = 5.00m;  // sent, but NOT honored -- see file header

        Console.WriteLine("\nPayload (trimmed):");
        Console.WriteLine(new JObject
        {
            ["CompanyNo"] = po["CompanyNo"], ["LocationId"] = po["LocationId"],
            ["VendorId"] = po["VendorId"], ["BuyerId"] = po["BuyerId"],
            ["PoDesc"] = po["PoDesc"], ["POLines"] = po["POLines"],
        }.ToString());

        if (!RestHelpers.ConfirmExecute())
            return;

        var content = new StringContent(po.ToString());
        content.Headers.ContentType = new MediaTypeHeaderValue("application/json");
        var created = await http.PostAsync($"{baseUrl}/api/purchasing/purchaseorders/", content);
        if (!created.IsSuccessStatusCode)
        {
            Console.WriteLine($"\nCreate failed: HTTP {(int)created.StatusCode}");
            Console.WriteLine(await created.Content.ReadAsStringAsync());
            return;
        }

        var createdPo = JObject.Parse(await created.Content.ReadAsStringAsync());
        var poNo = createdPo["PoNo"];
        Console.WriteLine($"\nCreated PO {poNo}");
        var createdLine = ((JArray)createdPo["POLines"]!["list"]!)[0];
        Console.WriteLine($"  POLines (populated on THIS response only): {createdLine}");

        Console.WriteLine($"\nRead-back GET /api/purchasing/purchaseorders/{poNo}:");
        Console.WriteLine(new string('-', 50));
        var rb = await http.GetAsync($"{baseUrl}/api/purchasing/purchaseorders/{poNo}");
        rb.EnsureSuccessStatusCode();
        var rbPo = JObject.Parse(await rb.Content.ReadAsStringAsync());
        Console.WriteLine($"  PoNo={rbPo["PoNo"]}  POLines={RestHelpers.JsonDisplay(rbPo["POLines"])}  (always null on GET)");
    }
}
