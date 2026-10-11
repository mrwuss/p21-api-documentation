// Recipe: Edit a Supplier/Item Purchase Pricing Page in Place
// Docs:   docs/08-SalesPricePage-Codes.md#editing-a-supplieritem-purchase-page-purchasepricingpagesupplieritem
//
// Changes the price on an existing PurchasePricingPageSupplierItem page
// without creating a second page: read the page over OData, mirror its
// current field set (stored codes mapped back to window labels), change only
// the price, and post Status "New" with the page's exact keys. Then confirm
// the same purchase_pricing_page_uid carries the new price and no duplicate
// appeared.
//
// Key rules (verified on play 26.1.5950.0, October 2026):
//   - Status "Edit" is HTTP 400. "New" + exact keys edits in place.
//   - A different effective_date created a SECOND page; a different
//     expiration_date re-dated the existing one. Send both as stored.
//   - Stored PRICE / ITEM / MULTIPLIER -> send Price / Item / Multiplier.
//   - Mirror the full field set (totaling_basis is required on every save).

using System.Globalization;
using Newtonsoft.Json.Linq;
using static P21Examples.Recipes.RecipeHelpers;

namespace P21Examples.Recipes;

public static class PurchasePricingPageEdit
{
    public sealed record Options(
        string Company = "ACME",
        string BookId = "PB-2026",
        string SupplierId = "100",
        string ItemId = "ITEM-001",
        string Effective = "2030-01-01",   // exactly as stored
        string Expiration = "2030-12-31",  // exactly as stored
        string Price = "4.75");

    private static readonly string[] Keys =
        { "company_id", "purchase_pricing_book_id", "supplier_id", "inv_mast_item_id",
          "effective_date", "expiration_date" };

    // Stored code -> window label. Anything not listed is sent as stored.
    private static readonly Dictionary<string, Dictionary<string, string>> Labels = new()
    {
        ["pricing_method"] = new() { ["PRICE"] = "Price", ["SOURCE"] = "Source", ["NONE"] = "None" },
        ["totaling_method"] = new() { ["ITEM"] = "Item", ["SUPPLIER"] = "Supplier", ["ORDER"] = "Order",
            ["DISCOUNT GROUP"] = "Discount Group", ["PRODUCT GROUP"] = "Product Group",
            ["MAJOR GROUP"] = "Major Group" },
        ["calculation_type"] = new() { ["MULTIPLIER"] = "Multiplier", ["FIXED"] = "Fixed Price",
            ["DIFFERENCE"] = "Difference", ["MARKUP"] = "Mark up", ["PERCENTAGE"] = "Percentage" },
    };

    private static string Label(string field, string stored) =>
        Labels.TryGetValue(field, out var map) && map.TryGetValue(stored.ToUpperInvariant(), out var l)
            ? l : stored;

    public static Task RunAsync() => RunAsync(new Options());

    public static async Task RunAsync(Options o)
    {
        Console.WriteLine("Recipe - Edit a Purchase Pricing Page in place (PurchasePricingPageSupplierItem)");
        Console.WriteLine(new string('=', 60));

        var (http, uiServer, baseUrl) = await InteractiveHelpers.CreateRawClientAsync();
        using var _ = http;

        var pages = await FindPagesAsync(http, baseUrl, o);
        if (pages.Count != 1)
        {
            Console.WriteLine($"Expected exactly one live page for these keys, found {pages.Count}");
            return;
        }
        var page = pages[0];
        var uid = (int)page["purchase_pricing_page_uid"]!;
        Console.WriteLine($"\nCurrent page {uid}: pricing_method={page["pricing_method"]} price={page["price"]} " +
                          $"calculation_type={page["calculation_type"]} totaling_basis={page["totaling_basis"]}");

        var payload = EditPayload(page, o);
        PrintPayload("Payload for POST {ui_server}/api/v2/transaction", payload);
        if (!ConfirmExecute())
            return;

        if (!CheckResult(await InteractiveHelpers.PostTransactionAsync(http, uiServer, payload)))
            return;

        var after = await FindPagesAsync(http, baseUrl, o);
        Console.WriteLine("\nVerify (OData read-back):");
        Console.WriteLine($"  live pages for these keys: {after.Count} -> {(after.Count == 1 ? "OK" : "DUPLICATE")}");
        var same = after.FirstOrDefault(r => (int)r["purchase_pricing_page_uid"]! == uid);
        if (same is null)
        {
            Console.WriteLine($"  page {uid} no longer matches the keys -> CHECK");
            return;
        }
        var ok = (decimal)same["price"]! == decimal.Parse(o.Price, CultureInfo.InvariantCulture);
        Console.WriteLine($"  page {uid}: price={same["price"]} expected={o.Price} -> {(ok ? "OK" : "MISMATCH")}");
    }

    /// <summary>Live (delete_flag N) pages matching all six keys; dates compared on the date part.</summary>
    private static async Task<List<JToken>> FindPagesAsync(HttpClient http, string baseUrl, Options o)
    {
        var item = await InteractiveHelpers.ODataAsync(http, baseUrl, "inv_mast", $"item_id eq '{o.ItemId}'");
        if (item.Count == 0) throw new InvalidOperationException($"Item {o.ItemId} not found");
        var rows = await InteractiveHelpers.ODataAsync(http, baseUrl, "purchase_pricing_page",
            $"company_id eq '{o.Company}' and pricing_book_id eq '{o.BookId}' " +
            $"and supplier_id eq {o.SupplierId} and inv_mast_uid eq {item[0]["inv_mast_uid"]} " +
            "and delete_flag eq 'N'");
        // Dates arrive as strings with a time zone; compare the date part.
        return rows.Where(r => r["effective_date"]!.ToString()[..10] == o.Effective
                            && r["expiration_date"]!.ToString()[..10] == o.Expiration).ToList();
    }

    private static string Num(JToken? t) =>
        (t is null || t.Type == JTokenType.Null ? 0m : (decimal)t).ToString("0.######", CultureInfo.InvariantCulture);

    private static bool Has(JToken page, string field) =>
        page[field] is { } v && v.Type != JTokenType.Null && v.ToString() != "";

    /// <summary>Mirror the page's current fields, with the new price.</summary>
    private static JObject EditPayload(JToken page, Options o)
    {
        var header = new JArray
        {
            Edit("company_id", o.Company),
            Edit("purchase_pricing_book_id", o.BookId),
            Edit("supplier_id", o.SupplierId),
            Edit("inv_mast_item_id", o.ItemId),
            Edit("effective_date", o.Effective),
            Edit("expiration_date", o.Expiration),
        };
        if (Has(page, "location_id")) header.Add(Edit("location_id", page["location_id"]!.ToString()));
        foreach (var f in new[] { "pricing_description", "contract_number" })
            if (Has(page, f)) header.Add(Edit(f, page[f]!.ToString()));
        var method = page["pricing_method"]!.ToString();
        header.Add(Edit("pricing_method", Label("pricing_method", method)));
        if (Has(page, "source_price")) header.Add(Edit("source_price", page["source_price"]!.ToString()));
        if (method.Equals("PRICE", StringComparison.OrdinalIgnoreCase))
            header.Add(Edit("price", o.Price));                                   // the one real change
        header.Add(Edit("totaling_method", Label("totaling_method", page["totaling_method"]!.ToString())));
        header.Add(Edit("totaling_basis", page["totaling_basis"]!.ToString())); // required on every save
        if (Has(page, "major_group_id")) header.Add(Edit("major_group_id", page["major_group_id"]!.ToString()));

        var values = new JArray { Edit("calculation_type", Label("calculation_type", page["calculation_type"]!.ToString())) };
        var last = Enumerable.Range(1, 15).Where(n => Has(page, $"calculation_value{n}")
                       && (decimal)page[$"calculation_value{n}"]! != 0m).DefaultIfEmpty(1).Max();
        for (var n = 1; n <= last; n++)
        {
            values.Add(Edit($"value{n}", Num(page[$"calculation_value{n}"])));
            if (n < last) values.Add(Edit($"break{n}", Num(page[$"break{n}"])));
        }

        JObject Element(string name, JArray keys, JArray edits) => new()
        {
            ["Name"] = name, ["Type"] = "Form", ["Keys"] = keys,
            ["Rows"] = new JArray { new JObject { ["Edits"] = edits, ["RelativeDateEdits"] = new JArray() } }
        };

        return new JObject
        {
            ["Name"] = "PurchasePricingPageSupplierItem",
            ["UseCodeValues"] = false,
            ["Transactions"] = new JArray { new JObject
            {
                ["Status"] = "New",   // "Edit" is not a valid status -- exact keys make this an edit
                ["DataElements"] = new JArray
                {
                    Element("TABPAGE_1.tp_1_dw_1", new JArray(Keys), header),
                    Element("TABPAGE_2.tp_2_dw_2", new JArray(), values),
                }
            } }
        };
    }
}
