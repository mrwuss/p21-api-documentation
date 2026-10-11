// Recipe: Create a Sales Price Page and Link It to a Price Book
// Docs:   docs/08-SalesPricePage-Codes.md#creating-a-page-through-the-transaction-api
//
// Creates an item-level SalesPricePage (fixed price, cost Value on the COSTS
// tab) in one POST, links it to an existing book through SalesPriceBook
// (FORM.form keyed price_book_id + LIST.list_detail keyed price_page_uid),
// and reads both back over OData. Optionally unlinks it (row_status_flag
// Delete on the same list_detail row -- a physical delete of the
// price_page_x_book row) and soft-deletes the page.
//
// Key rules (verified on play 26.1.5950.0, October 2026):
//   - price_page_type_cd first, then company_id, then the key field.
//   - Omit calculator_type and strategic_price_applies_to_cd
//     (the latter is "Column is disabled" on create; it defaults to Core).
//   - The new price_page_uid is the first Edit of FORM.form in Results.
//   - Link through SalesPriceBook, never through the page's USED BY element.

using Newtonsoft.Json.Linq;
using P21Examples.Common;
using static P21Examples.Recipes.RecipeHelpers;

namespace P21Examples.Recipes;

public static class SalesPricePageCreateLink
{
    public sealed record Options(
        string Company = "ACME",
        string ItemId = "ITEM-001",
        string BookId = "BOOK-001",
        string Description = "ITEM-001 contract price",
        string Contract = "CONTRACT-1",
        string Price = "12.34",
        string Cost = "5.67",
        string Effective = "2030-01-01",
        string Expiration = "2030-12-31");

    public static Task RunAsync() => RunAsync(new Options());

    public static async Task RunAsync(Options o)
    {
        Console.WriteLine("Recipe - Create a Sales Price Page + link it to a Price Book");
        Console.WriteLine(new string('=', 60));

        var create = PagePayload(o);
        PrintPayload("1) SalesPricePage create", create);
        PrintPayload("2) SalesPriceBook link (price_page_uid filled in after step 1)",
            LinkPayload(o.BookId, "<price_page_uid>", unlink: false));
        if (!ConfirmExecute())
            return;

        using var client = await P21Client.CreateAsync();

        var book = (JArray)(await client.OData.QueryAsync(
            "price_book", filter: $"price_book_id eq '{o.BookId}'"))["value"]!;
        if (book.Count == 0)
        {
            Console.WriteLine($"Price book {o.BookId} not found");
            return;
        }
        var bookUid = (int)book[0]["price_book_uid"]!;

        // 1. Create the page; the new uid comes back in Results.
        var created = await client.Transaction.CreateAsync(create);
        if (!CheckResult(created)) return;
        var uid = created.Results!["Transactions"]![0]!["DataElements"]!
            .First(e => (string?)e["Name"] == "FORM.form")["Rows"]![0]!["Edits"]!
            .First(e => (string?)e["Name"] == "price_page_uid")["Value"]!.ToString();
        Console.WriteLine($"\n1. Created price_page_uid {uid}");

        // 2. Link it straight away -- an unlinked page is invisible to pricing.
        if (!CheckResult(await client.Transaction.CreateAsync(LinkPayload(o.BookId, uid, unlink: false))))
            return;
        Console.WriteLine($"2. Linked to {o.BookId}");

        // 3. Verify both.
        var page = (await client.OData.QueryAsync("price_page", filter: $"price_page_uid eq {uid}"))["value"]![0]!;
        Console.WriteLine($"\n3. Verify price_page {uid}: type={page["price_page_type_cd"]} price={page["price"]} " +
                          $"pricing_method_cd={page["pricing_method_cd"]} other_cost_value={page["other_cost_value"]} " +
                          $"row_status_flag={page["row_status_flag"]}");
        var links = (JArray)(await client.OData.QueryAsync("price_page_x_book",
            filter: $"price_page_uid eq {uid} and price_book_uid eq {bookUid}"))["value"]!;
        Console.WriteLine($"   price_page_x_book rows: {links.Count} -> {(links.Count == 1 ? "OK" : "MISSING")}");

        Console.WriteLine();
        Console.Write("Type CLEANUP to unlink and soft-delete this page, anything else = keep: ");
        if (Console.ReadLine()?.Trim() != "CLEANUP")
        {
            Console.WriteLine($"Left in place: page {uid}, linked to {o.BookId}.");
            return;
        }

        // 4. Unlink (physical delete of the link row), then soft-delete the page.
        if (!CheckResult(await client.Transaction.CreateAsync(LinkPayload(o.BookId, uid, unlink: true))))
            return;
        links = (JArray)(await client.OData.QueryAsync("price_page_x_book",
            filter: $"price_page_uid eq {uid}"))["value"]!;
        Console.WriteLine($"\n4. Unlinked: price_page_x_book rows now {links.Count} -> {(links.Count == 0 ? "OK" : "STILL LINKED")}");
        if (!CheckResult(await client.Transaction.CreateAsync(PageDeletePayload(uid))))
            return;
        page = (await client.OData.QueryAsync("price_page", filter: $"price_page_uid eq {uid}"))["value"]![0]!;
        Console.WriteLine($"   Page {uid} row_status_flag={page["row_status_flag"]} (700 = Delete)");
    }

    private static JObject Element(string name, string type, JArray keys, params JObject[] edits) => new()
    {
        ["Name"] = name, ["Type"] = type, ["Keys"] = keys,
        ["Rows"] = new JArray { new JObject { ["Edits"] = new JArray(edits), ["RelativeDateEdits"] = new JArray() } }
    };

    private static JObject Payload(string service, params JObject[] elements) => new()
    {
        ["Name"] = service, ["UseCodeValues"] = false,
        ["Transactions"] = new JArray { new JObject { ["Status"] = "New", ["DataElements"] = new JArray(elements) } }
    };

    /// <summary>SalesPricePage create: FORM.form + COSTS.costs + VALUES.values.</summary>
    private static JObject PagePayload(Options o) => Payload("SalesPricePage",
        Element("FORM.form", "Form", new JArray(),
            Edit("price_page_type_cd", "Item"),      // FIRST: the type decides which keys are valid
            Edit("company_id", o.Company),           // before the key field
            Edit("item_id", o.ItemId),
            Edit("description", o.Description),
            Edit("effective_date", o.Effective),
            Edit("expiration_date", o.Expiration),
            Edit("contract_number", o.Contract),
            Edit("pricing_method_cd", "Price"),
            Edit("price", o.Price),
            Edit("totaling_method_cd", "Item"),
            Edit("totaling_basis_cd", "Sales Unit")),
            // calculator_type and strategic_price_applies_to_cd are left out on purpose.
        Element("COSTS.costs", "Form", new JArray(),
            Edit("other_cost_type_cd", "Value"),
            Edit("other_cost_value", o.Cost),
            Edit("commission_cost_type_cd", "Value"),
            Edit("commission_cost_value", o.Cost)),
        Element("VALUES.values", "Form", new JArray(),
            Edit("calculation_method_cd", "Multiplier"),
            Edit("calculation_value1", "1")));

    /// <summary>SalesPriceBook link, or unlink with row_status_flag Delete.</summary>
    private static JObject LinkPayload(string bookId, string pageUid, bool unlink)
    {
        var row = new List<JObject> { Edit("price_page_uid", pageUid) };
        if (unlink) row.Add(Edit("row_status_flag", "Delete"));
        return Payload("SalesPriceBook",
            Element("FORM.form", "Form", new JArray { "price_book_id" }, Edit("price_book_id", bookId)),
            Element("LIST.list_detail", "List", new JArray { "price_page_uid" }, row.ToArray()));
    }

    private static JObject PageDeletePayload(string pageUid) => Payload("SalesPricePage",
        Element("FORM.form", "Form", new JArray { "price_page_uid" },
            Edit("price_page_uid", pageUid), Edit("row_status_flag", "Delete")));
}
