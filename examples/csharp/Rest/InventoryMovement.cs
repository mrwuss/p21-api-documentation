// Other REST Families - Bin-to-Bin Inventory Movement
// (inventory/inventorymovement moveinventory)
// Docs: docs/15-Other-REST-Families.md#inventoryinventorymovement
// Mirrors: examples/python/rest/inventory_movement.py
//
// Undocumented preconditions found live, 26.1.5950.0:
//   - moveAvailable/moveAllocations are Y/N strings, not booleans --
//     "true"/"false" fails with "Move Available is a Y/N column."
//   - toBin must be a bin this item/location already has a stock
//     association with -- "A valid inventory bin must be entered."
//   - toBin == fromBin is refused.
//   - A real bin can still be put-locked.
//   - "success" does NOT mean a nonzero quantity moved -- read
//     TransactionDetail.QuantityMoved; a source bin with no real stock
//     still returns 200 with QuantityMoved: "0".

using Newtonsoft.Json.Linq;

namespace P21Examples.Rest;

public static class InventoryMovement
{
    public static async Task RunAsync()
    {
        Console.WriteLine("Other REST Families - Inventory Movement (inventorymovement)");
        Console.WriteLine(new string('=', 60));

        var (http, baseUrl) = await RestHelpers.CreateRawClientAsync();
        using var _ = http;
        Console.WriteLine($"Server: {baseUrl}");

        Console.Write("Item id [GBY]: ");
        var itemId = Console.ReadLine()?.Trim();
        itemId = string.IsNullOrEmpty(itemId) ? "GBY" : itemId;
        Console.Write("Location id [40]: ");
        var locationId = Console.ReadLine()?.Trim();
        locationId = string.IsNullOrEmpty(locationId) ? "40" : locationId;
        Console.Write("From bin [FGA040]: ");
        var fromBin = Console.ReadLine()?.Trim();
        fromBin = string.IsNullOrEmpty(fromBin) ? "FGA040" : fromBin;
        Console.Write("To bin (must already be a bin this item/location holds stock "
                      + "associations for) [XDOCK]: ");
        var toBin = Console.ReadLine()?.Trim();
        toBin = string.IsNullOrEmpty(toBin) ? "XDOCK" : toBin;

        var query = $"location={locationId}&itemId={itemId}&toBin={toBin}&fromBin={fromBin}" +
                   "&lot=&uom=EA&quantity=1&moveAvailable=Y&moveAllocations=N";
        Console.WriteLine($"\nWould POST to /api/inventory/inventorymovement/moveinventory?{query}");

        if (!RestHelpers.ConfirmExecute())
            return;

        var resp = await http.PostAsync(
            $"{baseUrl}/api/inventory/inventorymovement/moveinventory?{query}",
            new StringContent(""));
        if (!resp.IsSuccessStatusCode)
        {
            Console.WriteLine($"\nMove failed: HTTP {(int)resp.StatusCode}");
            Console.WriteLine(await resp.Content.ReadAsStringAsync());
            return;
        }

        var result = JObject.Parse(await resp.Content.ReadAsStringAsync());
        var moved = result["TransactionDetail"]!["QuantityMoved"];
        Console.WriteLine($"\n{result["ResponseMessage"]}: moved {moved} " +
                          $"{result["TransactionDetail"]!["QuantityMovedUOM"]} " +
                          $"from {fromBin} to {toBin}");
        if ((double)moved! == 0)
            Console.WriteLine("  WARNING: QuantityMoved is 0 -- \"success\" here does not mean " +
                              "anything actually relocated.");
    }
}
