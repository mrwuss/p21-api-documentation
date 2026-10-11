// Recipe: Clone an Existing Inventory Item
// Docs:   docs/11-Inventory-REST-API.md § Cloning an Existing Item
//
// Create an item set up like one you already have — same locations, product
// and discount groups, suppliers and costs, units of measure — through the
// Inventory REST API: GET the source with its child records, drop the fields
// that belong to the source record, re-key every row to the new ID, POST it,
// then re-GET the new item and compare its setup to the source.
//
// Key rules (verified live — see the doc section):
//   - POST /api/inventory/parts/ needs its trailing slash, or it 307s.
//   - Drop the uids, the stock fields (QtyOnHand, MovingAverageCost, PrimaryBin,
//     first-stocked period/year, pattern-like fields) and every UserDefinedFields
//     block — the header one carries the source's own InvMastUdUid/InvMastUid.
//   - ItemDesc is 40 characters or fewer; P21 silently drops the rest.
//
// The Inventory REST API is not wrapped by P21Client, so this uses a raw
// HttpClient authenticated through the Common project's P21Config/P21Auth
// helpers (RecipeHelpers.CreateRawClientAsync). The source GET is read-only
// and runs before the EXECUTE prompt.

using System.Text;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using static P21Examples.Recipes.RecipeHelpers;

namespace P21Examples.Recipes;

public static class CloneItem
{
    // Generic placeholders — press Enter at each prompt to keep them.
    private const string SourceItemId = "ITEM-001";              // item to copy
    private const string NewItemId = "ITEM-002";                 // must not already exist
    private const string NewItemDesc = "Widget Assembly, Large"; // 40 characters or fewer
    private const string ExtendedProps = "Locations,Suppliers,LocationSuppliers,UnitsOfMeasure";

    // Header fields that belong to the source record.
    private static readonly string[] DropHeader = { "InvMastUid", "UserDefinedFields" };

    // Fields that identify the source record or describe its stock, per child list.
    private static readonly Dictionary<string, string[]> Drop = new()
    {
        ["Locations"] = new[] { "QtyOnHand", "MovingAverageCost", "PrimaryBin", "PeriodFirstStocked",
                                "YearFirstStocked", "PatternLikeInvMastUid", "PatternLikeLocationId",
                                "UserDefinedFields" },
        ["Suppliers"] = new[] { "InventorySupplierUid", "UserDefinedFields" },
        ["LocationSuppliers"] = new[] { "InventorySupplierXLocUid", "UserDefinedFields" },
        ["UnitsOfMeasure"] = new[] { "ItemUomUid", "UserDefinedFields" },
    };

    // Keep dates as the strings the API sent, so the POST echoes them unchanged.
    private static readonly JsonSerializerSettings Raw = new() { DateParseHandling = DateParseHandling.None };

    public static async Task RunAsync()
    {
        Console.WriteLine("Recipe - Clone an Existing Item (Inventory REST API)");
        Console.WriteLine(new string('=', 60));

        var sourceId = Ask("Source item ID", SourceItemId);
        var newId = Ask("New item ID", NewItemId);
        var newDesc = Ask("New item description", NewItemDesc);
        var supplierPartNo = Ask("Supplier part no for every supplier row", newId);
        if (newDesc.Length > 40)
        {
            Console.WriteLine("ItemDesc is over 40 characters — P21 silently drops the rest.");
            return;
        }

        var (rawHttp, _, baseUrl) = await CreateRawClientAsync();
        using var http = rawHttp;

        // 1. GET the source item with its child records (read-only)
        var getResp = await GetItemAsync(http, baseUrl, sourceId);
        getResp.EnsureSuccessStatusCode();
        var source = JsonConvert.DeserializeObject<JObject>(
            await getResp.Content.ReadAsStringAsync(), Raw)!;
        var payload = BuildClone(source, newId, newDesc, supplierPartNo);

        PrintPayload("POST /api/inventory/parts/ payload", payload);
        if (!ConfirmExecute())
            return;

        // 2. Refuse to overwrite: the POST fails anyway, but say why up front.
        if ((await GetItemAsync(http, baseUrl, newId)).IsSuccessStatusCode)
        {
            Console.WriteLine($"{newId} already exists — pick another ID.");
            return;
        }

        // 3. POST the clone — trailing slash, or the POST 307s
        var postResp = await http.PostAsync($"{baseUrl}/api/inventory/parts/",
            new StringContent(payload.ToString(Formatting.None), Encoding.UTF8, "application/json"));
        if (!postResp.IsSuccessStatusCode)
        {
            var body = await postResp.Content.ReadAsStringAsync();
            Console.WriteLine($"POST {(int)postResp.StatusCode}: {body[..Math.Min(500, body.Length)]}");
            return;
        }

        // 4. Re-GET to prove what actually landed — HTTP 200 alone does not confirm a write
        var afterResp = await GetItemAsync(http, baseUrl, newId);
        afterResp.EnsureSuccessStatusCode();
        var created = JsonConvert.DeserializeObject<JObject>(
            await afterResp.Content.ReadAsStringAsync(), Raw)!;

        Console.WriteLine($"\nCreated {created["ItemId"]}: {created["ItemDesc"]}");
        foreach (var loc in Rows(created, "Locations"))
            Console.WriteLine($"  location {loc["LocationId"]}: ProductGroupId={loc["ProductGroupId"]} " +
                              $"Stockable={loc["Stockable"]} Sellable={loc["Sellable"]}");
        foreach (var sup in Rows(created, "Suppliers"))
            Console.WriteLine($"  supplier {sup["SupplierId"]}: Cost={sup["Cost"]} " +
                              $"ListPrice={sup["ListPrice"]} SupplierPartNo={sup["SupplierPartNo"]}");

        foreach (var (key, fields) in new Dictionary<string, string[]>
                 {
                     ["Locations"] = new[] { "LocationId", "ProductGroupId", "Stockable", "Sellable" },
                     ["Suppliers"] = new[] { "SupplierId", "DivisionId", "Cost", "ListPrice" },
                     ["LocationSuppliers"] = new[] { "LocationId", "SupplierId", "PrimarySupplier" },
                     ["UnitsOfMeasure"] = new[] { "UnitOfMeasure", "UnitSize" },
                 })
        {
            var want = Setup(source, key, fields);
            var got = Setup(created, key, fields);
            var status = want.SequenceEqual(got) ? "OK" : "MISMATCH";
            Console.WriteLine($"  {key}: {got.Count} row(s) -> {status}");
        }
    }

    /// <summary>Copy the source item, drop identity/stock fields, and re-key it to the new ID.</summary>
    private static JObject BuildClone(JObject source, string newId, string newDesc, string supplierPartNo)
    {
        // Top level: drop the source-record fields and any null header fields.
        var payload = new JObject();
        foreach (var (key, value) in source)
        {
            if (DropHeader.Contains(key) || Drop.ContainsKey(key)) continue;
            if ((value is null || value.Type == JTokenType.Null) && char.IsUpper(key[0])) continue;
            payload[key] = value?.DeepClone();
        }
        payload["ItemId"] = newId;
        payload["ItemDesc"] = newDesc;

        foreach (var (key, fields) in Drop)
        {
            var rows = new JArray();
            foreach (var src in Rows(source, key))
            {
                var row = (JObject)src.DeepClone();
                foreach (var f in fields) row.Remove(f);
                row["ItemId"] = newId;
                if (key == "Suppliers") row["SupplierPartNo"] = supplierPartNo;
                rows.Add(row);
            }
            payload[key] = new JObject { ["list"] = rows };
        }
        return payload;
    }

    private static Task<HttpResponseMessage> GetItemAsync(HttpClient http, string baseUrl, string itemId) =>
        http.GetAsync($"{baseUrl}/api/inventory/parts/{Uri.EscapeDataString(itemId)}" +
                      $"?extendedproperties={ExtendedProps}");

    private static IEnumerable<JObject> Rows(JObject item, string key) =>
        (item[key]?["list"] as JArray)?.OfType<JObject>() ?? Enumerable.Empty<JObject>();

    /// <summary>One sorted line per row of the fields a clone must share with its source.</summary>
    private static List<string> Setup(JObject item, string key, string[] fields) =>
        Rows(item, key)
            .Select(r => string.Join("|", fields.Select(f => r[f]?.ToString() ?? "")))
            .OrderBy(s => s, StringComparer.Ordinal)
            .ToList();

    private static string Ask(string label, string fallback)
    {
        Console.Write($"{label} [{fallback}]: ");
        var answer = Console.ReadLine()?.Trim();
        return string.IsNullOrEmpty(answer) ? fallback : answer;
    }
}
