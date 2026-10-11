// Recipe: Add (or Remove) a Customer Price Library
// Docs:   docs/04-Interactive-API.md#customer-window-adding-a-price-library
//
// A customer's price libraries are the TABPAGE_7.tp_7_dw_price_library grid
// on the Customer window. This adds one library row -- price_library_id,
// then optionally sequence_number -- saves, and reads every row's
// sequence_number back from price_library_x_cust_x_cmpy. Remove = true
// deletes the row instead (row_status_flag Delete on the selected row).
//
// Key rules (verified on play 26.1.5950.0, October 2026):
//   - Service name "Customer"; load via TABPAGE_1.tp_1_dw_1.customer_id.
//   - price_library_id is the ID string, not price_library_uid.
//   - Set price_library_id BEFORE sequence_number: that order saved the row
//     at the sequence sent; sequence first, or none, did not.
//   - Changes land on the ACTIVE row: select it before setting row_status_flag.

using static P21Examples.Recipes.RecipeHelpers;

namespace P21Examples.Recipes;

public static class CustomerPriceLibrary
{
    public sealed record Options(
        string CustomerId = "100",
        string LibraryId = "LIB-001",
        string? Sequence = null,
        bool Remove = false);

    private const string Tab = "TABPAGE_7", Grid = "tp_7_dw_price_library";

    public static Task RunAsync() => RunAsync(new Options());

    public static async Task RunAsync(Options o)
    {
        Console.WriteLine($"Recipe - Customer window: price library {(o.Remove ? "remove" : "add")}");
        Console.WriteLine(new string('=', 60));
        Console.WriteLine($"\nPlanned: open Customer, customer_id={o.CustomerId}, tab {Tab}, " +
                          (o.Remove
                              ? $"select the {o.LibraryId} row, row_status_flag=Delete"
                              : $"add_row, price_library_id={o.LibraryId}" +
                                (o.Sequence is null ? "" : $", then sequence_number={o.Sequence}")) +
                          ", save, OData read-back");
        if (!ConfirmExecute())
            return;

        var (http, uiServer, baseUrl) = await InteractiveHelpers.CreateRawClientAsync();
        using var _ = http;

        Console.WriteLine($"\nBefore: {await ReadBackAsync(http, baseUrl, o.CustomerId)}");

        await using (var s = new WindowSession(http, uiServer))
        {
            await s.StartAsync(responseWindows: true);
            var window = await s.OpenWindowAsync("Customer");
            try
            {
                await s.ChangeAsync(window, "TABPAGE_1", "tp_1_dw_1", "customer_id", o.CustomerId);
                await s.SelectTabAsync(window, Tab);
                if (o.Remove)
                {
                    var rows = await s.RowsAsync(window, Grid);
                    var index = rows.FindIndex(r => r.GetValueOrDefault("price_library_id") == o.LibraryId) + 1;
                    if (index == 0)
                    {
                        Console.WriteLine($"{o.LibraryId} is not on customer {o.CustomerId}");
                        return;
                    }
                    await s.SelectRowAsync(window, Grid, index);   // changes land on the ACTIVE row
                    await s.ChangeAsync(window, Tab, Grid, "row_status_flag", "Delete");
                }
                else
                {
                    await s.AddRowAsync(window, Grid);
                    await s.ChangeAsync(window, Tab, Grid, "price_library_id", o.LibraryId);   // first
                    if (o.Sequence is not null)
                        await s.ChangeAsync(window, Tab, Grid, "sequence_number", o.Sequence); // then
                }
                var result = await s.SaveAsync(window);
                if ((int?)result["Status"] == WindowSession.Blocked)
                    throw new InvalidOperationException(
                        $"Save opened a popup: {string.Join(", ", await s.ToolsAsync(WindowSession.PopupIds(result)[0]))}");
            }
            finally
            {
                await s.CloseWindowAsync(window);
            }
        }

        var after = await ReadBackRowsAsync(http, baseUrl, o.CustomerId);
        Console.WriteLine($"After:  {Format(after)}");
        var mine = after.Where(r => r.LibraryId == o.LibraryId).ToList();
        if (o.Remove)
            Console.WriteLine($"Verify: {o.LibraryId} rows left = {mine.Count} -> {(mine.Count == 0 ? "OK" : "STILL PRESENT")}");
        else if (mine.Count > 0)
            Console.WriteLine($"Verify: {o.LibraryId} saved at sequence {mine[^1].Sequence} (sent: {o.Sequence ?? "last"})");
        else
            Console.WriteLine($"Verify: {o.LibraryId} NOT saved");
    }

    private static async Task<string> ReadBackAsync(HttpClient http, string baseUrl, string customerId) =>
        Format(await ReadBackRowsAsync(http, baseUrl, customerId));

    private static string Format(List<(int Sequence, string LibraryId)> rows) =>
        "[" + string.Join(", ", rows.Select(r => $"({r.Sequence}, {r.LibraryId})")) + "]";

    /// <summary>(sequence_number, price_library_id) for the customer, in sequence order.</summary>
    private static async Task<List<(int Sequence, string LibraryId)>> ReadBackRowsAsync(
        HttpClient http, string baseUrl, string customerId)
    {
        var rows = new List<(int, string)>();
        foreach (var link in await InteractiveHelpers.ODataAsync(http, baseUrl,
                     "price_library_x_cust_x_cmpy", $"customer_id eq {customerId}"))
        {
            var lib = (await InteractiveHelpers.ODataAsync(http, baseUrl, "price_library",
                $"price_library_uid eq {link["price_library_uid"]}"))[0];
            rows.Add(((int)link["sequence_number"]!, (string)lib["price_library_id"]!));
        }
        return rows.OrderBy(r => r.Item1).ToList();
    }
}
