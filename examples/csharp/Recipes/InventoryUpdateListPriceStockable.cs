// Recipe: Update a Supplier's ListPrice and a Location's Stockable Flag
// Docs:   docs/11-Inventory-REST-API.md#updating-existing-location-fields
//
// GET -> modify -> PUT on /api/inventory/parts/{ItemId}: change
// Suppliers.list[].ListPrice (inventory_supplier.list_price) for one supplier
// and Locations.list[].Stockable (inv_loc.stockable) for one location, then
// verify through the REST GET and through OData. Then, unless you answer
// KEEP, put the original values back and verify the restore.
//
// Key rules (verified on play 26.1.5950.0, October 2026):
//   - PUT the whole payload from the GET (same extendedproperties), changed
//     in place. Parse it with dates left as strings so the PUT sends them
//     back unchanged.
//   - Stockable takes "Y" / "N" on this API.
//   - HTTP 200 alone does not prove the write -- read the columns back.

using System.Globalization;
using System.Text;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using static P21Examples.Recipes.RecipeHelpers;

namespace P21Examples.Recipes;

public static class InventoryUpdateListPriceStockable
{
    public sealed record Options(
        string ItemId = "ITEM-001",
        int SupplierId = 100,
        int LocationId = 10,
        decimal ListPrice = 11.25m,
        string Stockable = "Y");

    private const string Extended = "Locations,Suppliers,LocationSuppliers,UnitsOfMeasure";

    public static Task RunAsync() => RunAsync(new Options());

    public static async Task RunAsync(Options o)
    {
        Console.WriteLine("Recipe - Inventory REST: update supplier ListPrice + location Stockable");
        Console.WriteLine(new string('=', 60));
        Console.WriteLine($"\nWill GET /api/inventory/parts/{o.ItemId}?extendedproperties={Extended},");
        Console.WriteLine($"set Suppliers[{o.SupplierId}].ListPrice={o.ListPrice} and " +
                          $"Locations[{o.LocationId}].Stockable={o.Stockable}, PUT the full payload, verify.");
        if (!ConfirmExecute())
            return;

        var (http, _, baseUrl) = await InteractiveHelpers.CreateRawClientAsync();
        using var __ = http;

        var (sup, loc) = Pick(await GetPartAsync(http, baseUrl, o.ItemId), o);
        var originalPrice = (decimal)sup["ListPrice"]!;
        var originalStockable = (string)loc["Stockable"]!;
        Console.WriteLine($"\nBefore: ListPrice={originalPrice} Stockable={originalStockable}");

        await WriteAndVerifyAsync(http, baseUrl, o, o.ListPrice, o.Stockable, "Changed ");

        Console.WriteLine();
        Console.Write("Type KEEP to leave the new values, anything else = restore the originals: ");
        if (Console.ReadLine()?.Trim() == "KEEP")
            return;
        await WriteAndVerifyAsync(http, baseUrl, o, originalPrice, originalStockable, "Restored");
    }

    private static async Task<JObject> GetPartAsync(HttpClient http, string baseUrl, string itemId)
    {
        var response = await http.GetAsync($"{baseUrl}/api/inventory/parts/{itemId}?extendedproperties={Extended}");
        response.EnsureSuccessStatusCode();
        using var reader = new JsonTextReader(new StringReader(await response.Content.ReadAsStringAsync()))
            { DateParseHandling = DateParseHandling.None };   // send dates back exactly as received
        return JObject.Load(reader);
    }

    private static (JObject Sup, JObject Loc) Pick(JObject part, Options o)
    {
        var sup = part["Suppliers"]!["list"]!.Cast<JObject>().FirstOrDefault(s => (int)s["SupplierId"]! == o.SupplierId);
        var loc = part["Locations"]!["list"]!.Cast<JObject>().FirstOrDefault(l => (int)l["LocationId"]! == o.LocationId);
        if (sup is null || loc is null)
            throw new InvalidOperationException($"Supplier {o.SupplierId} or location {o.LocationId} not on the item");
        return (sup, loc);
    }

    private static async Task WriteAndVerifyAsync(HttpClient http, string baseUrl, Options o,
        decimal listPrice, string stockable, string label)
    {
        var part = await GetPartAsync(http, baseUrl, o.ItemId);
        var (sup, loc) = Pick(part, o);
        sup["ListPrice"] = listPrice;
        loc["Stockable"] = stockable;
        var put = await http.PutAsync($"{baseUrl}/api/inventory/parts/{o.ItemId}",
            new StringContent(part.ToString(Formatting.None), Encoding.UTF8, "application/json"));
        if (!put.IsSuccessStatusCode)
            throw new InvalidOperationException($"PUT {(int)put.StatusCode}: {await put.Content.ReadAsStringAsync()}");

        var again = await GetPartAsync(http, baseUrl, o.ItemId);
        var (sup2, loc2) = Pick(again, o);
        var uid = again["InvMastUid"]!.ToString();
        var dbSup = (await InteractiveHelpers.ODataAsync(http, baseUrl, "inventory_supplier",
            $"inv_mast_uid eq {uid} and supplier_id eq {o.SupplierId}"))[0];
        var dbLoc = (await InteractiveHelpers.ODataAsync(http, baseUrl, "inv_loc",
            $"inv_mast_uid eq {uid} and location_id eq {o.LocationId}"))[0];
        var ok = (decimal)sup2["ListPrice"]! == listPrice && (string)loc2["Stockable"]! == stockable
                 && (decimal)dbSup["list_price"]! == listPrice && (string)dbLoc["stockable"]! == stockable;
        Console.WriteLine($"{label}: REST ListPrice={((decimal)sup2["ListPrice"]!).ToString(CultureInfo.InvariantCulture)} " +
                          $"Stockable={loc2["Stockable"]} | OData list_price={dbSup["list_price"]} " +
                          $"stockable={dbLoc["stockable"]} -> {(ok ? "OK" : "MISMATCH")}");
    }
}
