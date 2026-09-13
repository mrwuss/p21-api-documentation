// Other REST Families - Read a Purchase Order Header
// Docs: docs/15-Other-REST-Families.md#purchasingpurchaseorders
// Mirrors: examples/python/rest/purchase_order_read.py
//
// Reads one PO by po_no and shows the family's defining limitation: every
// child collection is null on a keyed GET, with or without any expansion
// parameter -- includeLines, expand, $expand, full, and includeChildren
// all return a byte-identical 742-byte header-only response.
//
// Writes on this family (POST/PUT/async) are NOT exercised anywhere in
// this repo. Use the Transaction API PurchaseOrder service for verified
// writes -- see docs/03-Transaction-API.md.

using Newtonsoft.Json.Linq;

namespace P21Examples.Rest;

public static class PurchaseOrderRead
{
    private static readonly string[] ChildCollections =
        { "POLines", "POSales", "POHdrNotes", "POLineNotes" };

    public static async Task RunAsync()
    {
        Console.WriteLine("Other REST Families - Purchase Order Header (purchasing/purchaseorders)");
        Console.WriteLine(new string('=', 60));

        Console.Write("po_no to read (e.g. 998310): ");
        var poNo = Console.ReadLine()?.Trim();
        if (string.IsNullOrEmpty(poNo))
        {
            Console.WriteLine("No po_no given.");
            return;
        }

        var (http, baseUrl) = await RestHelpers.CreateRawClientAsync();
        using var _ = http;
        Console.WriteLine($"Server: {baseUrl}");

        var response = await http.GetAsync($"{baseUrl}/api/purchasing/purchaseorders/{poNo}");
        response.EnsureSuccessStatusCode();
        var po = JObject.Parse(await response.Content.ReadAsStringAsync());

        Console.WriteLine($"\nPO {po["PoNo"]}  vendor={po["VendorId"]}  " +
                          $"location={po["LocationId"]}  approved={po["Approved"]}  " +
                          $"complete={po["Complete"]}");

        Console.WriteLine("\nChild collections (always null on this family -- see docs/15):");
        foreach (var key in ChildCollections)
            Console.WriteLine($"  {key}: {RestHelpers.JsonDisplay(po[key])}");

        Console.WriteLine($"\nUserDefinedFields: {po["UserDefinedFields"]}  " +
                          "(always {} here even when po_hdr_ud has real data -- " +
                          "read UDF values over OData)");
    }
}
