// Other REST Families - Create a Staged Cycle Count (inventory/externalcounts)
// Docs: docs/15-Other-REST-Families.md#inventoryexternalcounts
// Mirrors: examples/python/rest/external_count_create.py
//
// Does NOT change inv_loc.qty_on_hand -- confirmed by reading it back
// unchanged after a successful create.
//
// The trap: ItemId must be repeated on the BIN sub-record, not just the
// line -- it is not inherited, and omitting it produces an error about
// "Bin Detail Record... missing/unmatched" that does not name the cause.

using Newtonsoft.Json.Linq;

namespace P21Examples.Rest;

public static class ExternalCountCreate
{
    public static async Task RunAsync()
    {
        Console.WriteLine("Other REST Families - External Count Create (externalcounts)");
        Console.WriteLine(new string('=', 60));

        var (http, baseUrl) = await RestHelpers.CreateRawClientAsync();
        using var _ = http;
        Console.WriteLine($"Server: {baseUrl}");

        const string itemId = "GBY";
        const int locationId = 40;
        const string bin = "FGA040";
        const double qty = 5.0;

        var payload = new JObject
        {
            ["LocationId"] = locationId,
            ["CountDate"] = "2026-09-12T00:00:00",
            ["Lines"] = new JObject
            {
                ["list"] = new JArray
                {
                    new JObject
                    {
                        ["ItemId"] = itemId, ["UnitQuantity"] = qty, ["UnitOfMeasure"] = "EA",
                        // ItemId repeated here on purpose -- see file header.
                        ["Bins"] = new JObject { ["list"] = new JArray {
                            new JObject { ["ItemId"] = itemId, ["BinCd"] = bin,
                                         ["UnitQuantity"] = qty, ["UnitOfMeasure"] = "EA" } } },
                    },
                },
            },
        };

        Console.WriteLine("\nPayload:");
        Console.WriteLine(payload.ToString());

        if (!RestHelpers.ConfirmExecute())
            return;

        async Task<double> QtyOnHand()
        {
            var itemResp = await http.GetAsync(
                $"{baseUrl}/odataservice/odata/table/inv_mast?$select=inv_mast_uid&$filter=item_id eq '{itemId}'");
            var uid = ((JObject.Parse(await itemResp.Content.ReadAsStringAsync())["value"] as JArray)![0])["inv_mast_uid"];
            var locResp = await http.GetAsync(
                $"{baseUrl}/odataservice/odata/table/inv_loc?$select=qty_on_hand" +
                $"&$filter=inv_mast_uid eq {uid} and location_id eq {locationId}");
            return (double)((JObject.Parse(await locResp.Content.ReadAsStringAsync())["value"] as JArray)![0])["qty_on_hand"]!;
        }

        var before = await QtyOnHand();

        var content = new StringContent(payload.ToString());
        content.Headers.ContentType = new System.Net.Http.Headers.MediaTypeHeaderValue("application/json");
        var resp = await http.PostAsync($"{baseUrl}/api/inventory/externalcounts/", content);
        if (!resp.IsSuccessStatusCode)
        {
            Console.WriteLine($"\nCreate failed: HTTP {(int)resp.StatusCode}");
            Console.WriteLine(await resp.Content.ReadAsStringAsync());
            return;
        }
        Console.WriteLine("\nCreated.");

        var after = await QtyOnHand();
        Console.WriteLine($"qty_on_hand: {before} -> {after} " +
                          $"(unchanged: {before == after} -- this is a STAGED count)");
    }
}
