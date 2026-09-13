// Other REST Families - Post a WMS Inventory Adjustment
// (inventory/inventoryadjustments createWmsAdjustment)
// Docs: docs/15-Other-REST-Families.md#createwmsadjustment-verified
// Mirrors: examples/python/rest/inventory_wms_adjustment.py
//
// Two undocumented preconditions found live, 26.1.5950.0:
//   - `reason` must name a currently ACTIVE reason record (reason.delete_flag
//     eq 'N' over OData). A historical inactive one fails with "This
//     Adjustment Reason record could not be retrieved."
//   - `binCd` is required whenever the item/location is bin-tracked
//     (inv_loc.track_bins eq 'Y'). Omitting it fails with "Bin is required.",
//     naming neither the item nor the location.
//
// unitQuantity is a SIGNED DELTA, confirmed by posting the same positive
// value twice from a 0 on-hand and watching it accumulate.
//
// The tag variants (createWmsTagAdjustment) are not covered here -- every
// item tried was refused "is not a tagged item", including one with
// inv_mast.use_tags_flag = 'Y'. See docs/15's Open Questions.

using Newtonsoft.Json.Linq;

namespace P21Examples.Rest;

public static class InventoryWmsAdjustment
{
    public static async Task RunAsync()
    {
        Console.WriteLine("Other REST Families - WMS Inventory Adjustment");
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

        Console.Write("Signed quantity delta [1]: ");
        var qtyStr = Console.ReadLine()?.Trim();
        qtyStr = string.IsNullOrEmpty(qtyStr) ? "1" : qtyStr;

        async Task<(decimal Qty, string Bin, string TrackBins)> ReadLoc()
        {
            var itemResp = await http.GetAsync(
                $"{baseUrl}/odataservice/odata/table/inv_mast?$select=inv_mast_uid" +
                $"&$filter=item_id eq '{itemId}'");
            itemResp.EnsureSuccessStatusCode();
            var itemRows = (JObject.Parse(await itemResp.Content.ReadAsStringAsync())["value"] as JArray)!;
            if (itemRows.Count == 0) throw new InvalidOperationException($"No such item: {itemId}");
            var uid = itemRows[0]["inv_mast_uid"];

            var locResp = await http.GetAsync(
                $"{baseUrl}/odataservice/odata/table/inv_loc?$select=qty_on_hand,primary_bin,track_bins" +
                $"&$filter=inv_mast_uid eq {uid} and location_id eq {locationId}");
            locResp.EnsureSuccessStatusCode();
            var locRows = (JObject.Parse(await locResp.Content.ReadAsStringAsync())["value"] as JArray)!;
            if (locRows.Count == 0)
                throw new InvalidOperationException($"{itemId} is not stocked at location {locationId}");
            var row = locRows[0];
            return ((decimal)row["qty_on_hand"]!, (string?)row["primary_bin"] ?? "", (string)row["track_bins"]!);
        }

        var before = await ReadLoc();
        Console.WriteLine($"\n{itemId} @ location {locationId}: qty_on_hand={before.Qty}  " +
                          $"track_bins={before.TrackBins}  bin={before.Bin!}");
        if (before.TrackBins == "Y" && string.IsNullOrEmpty(before.Bin))
        {
            Console.WriteLine("Location is bin-tracked and no bin was found -- " +
                              "the create will fail with \"Bin is required.\"");
            return;
        }

        var query = $"locationId={locationId}&reason=ADJUST&approved=Y" +
                   $"&description=ZZ%20API%20DOC%20TEST&itemId={itemId}&unitQuantity={qtyStr}" +
                   $"&unitOfMeasure=EA&binCd={before.Bin}&lotCd=&serialNumber=";
        Console.WriteLine($"\nWould POST to /api/inventory/inventoryadjustments/createWmsAdjustment?{query}");

        if (!RestHelpers.ConfirmExecute())
            return;

        var resp = await http.PostAsync(
            $"{baseUrl}/api/inventory/inventoryadjustments/createWmsAdjustment?{query}",
            new StringContent(""));
        if (!resp.IsSuccessStatusCode)
        {
            Console.WriteLine($"\nAdjustment failed: HTTP {(int)resp.StatusCode}");
            Console.WriteLine(await resp.Content.ReadAsStringAsync());
            return;
        }

        var adj = JObject.Parse(await resp.Content.ReadAsStringAsync());
        var line = ((JArray)adj["Lines"]!["list"]!)[0];
        Console.WriteLine($"\nAdjustmentNo={adj["AdjustmentNo"]}  Cost={line["Cost"]}");

        var after = await ReadLoc();
        Console.WriteLine($"qty_on_hand: {before.Qty} -> {after.Qty} (delta {qtyStr} applied)");
    }
}
