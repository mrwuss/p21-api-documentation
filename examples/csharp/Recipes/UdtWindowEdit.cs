// Recipe: Insert, Update or Delete a UDT Row Through Its Maintenance Window
// Docs:   docs/04-Interactive-API.md#udt-maintenance-windows-edit-a-udt-row-through-its-window
//
// A user-defined table's generated maintenance window (w_udt_data_maint) has
// no service name. This opens it by its menu label, then inserts a row,
// updates columns of a row by Row ID, or deletes a row by Row ID, saves, and
// reads the table back over OData.
//
// Key rules (verified on play 26.1.6004.0, November 2026):
//   - The window exists only after "Create Maintenance Window" is set for the
//     table in User Defined Table Maintenance; its window name is the Title.
//   - Tab TP_USERDEFINEDTABLE, datawindow tp_userdefinedtable (one form).
//   - Setting udt_{name}_uid ("Row ID") loads the row; an unknown ID is
//     Status 2, "Enter a valid ID or leave ID blank."
//   - delete_row = Y and a save delete the row, with no confirmation dialog.

using Newtonsoft.Json.Linq;
using static P21Examples.Recipes.RecipeHelpers;

namespace P21Examples.Recipes;

public static class UdtWindowEdit
{
    public enum Mode { Insert, Update, Delete }

    public sealed record Options(
        Mode Action = Mode.Update,
        string Title = "Example Table Maintenance",
        string Table = "udt_example",
        string RowId = "5",
        string Edits = "status=done");   // COLUMN=VALUE pairs, comma-separated

    private const string Tab = "TP_USERDEFINEDTABLE", Dw = "tp_userdefinedtable";

    public static Task RunAsync() => RunAsync(new Options());

    public static async Task RunAsync(Options o)
    {
        var pk = $"{o.Table}_uid";
        var edits = o.Edits.Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries)
            .Select(pair => pair.Split('=', 2))
            .Select(kv => kv.Length == 2
                ? (Column: kv[0], Value: kv[1])
                : throw new ArgumentException($"Edits takes COLUMN=VALUE pairs, got '{string.Join("=", kv)}'"))
            .ToList();
        if (o.Action != Mode.Delete && edits.Count == 0)
            throw new ArgumentException($"{o.Action} needs at least one COLUMN=VALUE edit");

        Console.WriteLine($"Recipe - UDT maintenance window: {o.Action}");
        Console.WriteLine(new string('=', 60));
        Console.WriteLine($"\nPlanned: open {{\"Title\": \"{o.Title}\"}}" +
                          (o.Action == Mode.Insert ? "" : $", {pk}={o.RowId}") +
                          (o.Action == Mode.Delete
                              ? ", delete_row=Y"
                              : ", " + string.Join(", ", edits.Select(e => $"{e.Column}={e.Value}"))) +
                          $", save, OData read-back of {o.Table}");
        if (!ConfirmExecute())
            return;

        var (http, uiServer, baseUrl) = await InteractiveHelpers.CreateRawClientAsync();
        using var _ = http;

        var before = await LastUidAsync(http, baseUrl, o.Table, pk);

        await using (var s = new WindowSession(http, uiServer))
        {
            await s.StartAsync(responseWindows: true);
            var window = await s.OpenWindowByTitleAsync(o.Title);
            try
            {
                if (o.Action != Mode.Insert)
                    await s.ChangeAsync(window, Tab, Dw, pk, o.RowId);   // Status 2 if the ID is unknown
                if (o.Action == Mode.Delete)
                {
                    await s.ChangeAsync(window, Tab, Dw, "delete_row", "Y");
                }
                else
                {
                    foreach (var (column, value) in edits)
                        await s.ChangeAsync(window, Tab, Dw, column, value);
                }
                var result = await s.SaveAsync(window);
                if ((int?)result["Status"] == WindowSession.Blocked)
                    throw new InvalidOperationException(
                        $"Save opened a popup: {string.Join(", ", await s.ToolsAsync(WindowSession.PopupIds(result)[0]))}");
                Console.WriteLine($"\nsave: Status {result["Status"]} {result["Messages"]?.ToString(Newtonsoft.Json.Formatting.None)}");
            }
            finally
            {
                await s.CloseWindowAsync(window);
            }
        }

        var after = await ReadRowsAsync(http, baseUrl, o.Table, pk,
            o.Action == Mode.Insert ? $"{pk} gt {before}" : $"{pk} eq {o.RowId}");
        switch (o.Action)
        {
            case Mode.Insert:
                var added = after.Keys.ToList();
                Console.WriteLine($"Verify: inserted {pk} [{string.Join(", ", added)}] -> " +
                                  string.Join("; ", added.Select(k => after[k].ToString(Newtonsoft.Json.Formatting.None))));
                break;
            case Mode.Delete:
                Console.WriteLine($"Verify: {pk} {o.RowId} {(after.ContainsKey(o.RowId) ? "STILL PRESENT" : "deleted")}");
                break;
            default:
                Console.WriteLine(after.TryGetValue(o.RowId, out var row)
                    ? $"Verify: {row.ToString(Newtonsoft.Json.Formatting.None)}"
                    : $"Verify: {pk} {o.RowId} not found");
                break;
        }
    }

    /// <summary>The highest udt_{name}_uid in the table (0 when it is empty).</summary>
    private static async Task<long> LastUidAsync(HttpClient http, string baseUrl, string table, string pk)
    {
        var response = await http.GetAsync(
            $"{baseUrl}/odataservice/odata/table/{table}?$select={pk}&$orderby={pk}%20desc&$top=1");
        response.EnsureSuccessStatusCode();
        var rows = (JArray)JObject.Parse(await response.Content.ReadAsStringAsync())["value"]!;
        return rows.Count == 0 ? 0 : (long)rows[0][pk]!;
    }

    /// <summary>UDT rows matching an OData filter, keyed by udt_{name}_uid.</summary>
    private static async Task<Dictionary<string, JObject>> ReadRowsAsync(
        HttpClient http, string baseUrl, string table, string pk, string filter)
    {
        var rows = new Dictionary<string, JObject>();
        foreach (var row in await InteractiveHelpers.ODataAsync(http, baseUrl, table, filter))
        {
            var o = (JObject)row;
            foreach (var p in o.Properties().Where(p => p.Value.Type == JTokenType.String).ToList())
                p.Value = ((string)p.Value!).Trim();
            rows[(string)o[pk]!] = o;
        }
        return rows;
    }
}
