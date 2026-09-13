// Other REST Families - Read an Inventory Adjustment Header
// Docs: docs/15-Other-REST-Families.md#inventoryinventoryadjustments
// Mirrors: examples/python/rest/inventory_adjustment_read.py
//
// Reads one adjustment by AdjustmentNo. Lines is always null here (same
// child-collection pattern as purchasing/purchaseorders); Approved and
// Delete are real booleans on this family, where the PO family uses
// "Y"/"N" strings for the same concepts -- no shared convention.
//
// The four createWms* POST routes take QUERY-STRING parameters, not a
// body, and are NOT exercised in this repo -- they move stock and post
// to the GL. See docs/15's Open Questions.

using Newtonsoft.Json.Linq;

namespace P21Examples.Rest;

public static class InventoryAdjustmentRead
{
    public static async Task RunAsync()
    {
        Console.WriteLine("Other REST Families - Inventory Adjustment (inventory/inventoryadjustments)");
        Console.WriteLine(new string('=', 60));

        Console.Write("AdjustmentNo to read (e.g. 1000002): ");
        var adjustmentNo = Console.ReadLine()?.Trim();
        if (string.IsNullOrEmpty(adjustmentNo))
        {
            Console.WriteLine("No AdjustmentNo given.");
            return;
        }

        var (http, baseUrl) = await RestHelpers.CreateRawClientAsync();
        using var _ = http;
        Console.WriteLine($"Server: {baseUrl}");

        var response = await http.GetAsync(
            $"{baseUrl}/api/inventory/inventoryadjustments/{adjustmentNo}");
        response.EnsureSuccessStatusCode();
        var adj = JObject.Parse(await response.Content.ReadAsStringAsync());

        Console.WriteLine($"\nAdjustment {adj["AdjustmentNo"]}  location={adj["LocationId"]}  " +
                          $"reason={adj["Reason"]}  approved={adj["Approved"]} " +
                          "(real bool, not 'Y'/'N')  " +
                          $"delete={adj["Delete"]}");
        Console.WriteLine($"Lines: {RestHelpers.JsonDisplay(adj["Lines"])}  (always null on this family -- " +
                          "read inv_adj_line over OData)");
    }
}
