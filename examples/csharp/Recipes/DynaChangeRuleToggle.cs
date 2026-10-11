// Recipe: Disable and Re-enable a DynaChange Business Rule
// Docs:   docs/04-Interactive-API.md#managing-business-rules-through-the-dynachange-organizer
//
// No service maintains business rules; the route is the DynaChange
// Organizer tool "dc.organizer.rule" on any open window, which opens
// w_business_rule_organizer as a response window. This finds one rule by
// rule_name + field_name + window_title, switches it to the opposite status,
// applies, reads business_rule.row_status_flag back through the
// p21_view_business_rule OData view, then (unless you answer LEAVE) puts the
// original status back and verifies again.
//
// Key rules (verified on play 26.1.5950.0, October 2026):
//   - Select the row first (PUT v2/row); a change lands on the ACTIVE row.
//   - row_status_flag takes "Active" / "Inactive" (stored 704 / 705).
//   - cb_apply commits; cb_cancel closes the organizer.
//   - The grid has no business_rule_uid; rule_name alone is not unique.

using static P21Examples.Recipes.RecipeHelpers;

namespace P21Examples.Recipes;

public static class DynaChangeRuleToggle
{
    public sealed record Options(
        string RuleName = "ExampleRule",
        string FieldName = "item_id",
        string WindowTitle = "Item Maintenance",
        string HostService = "Customer");

    private static readonly Dictionary<int, string> Label = new() { [704] = "Active", [705] = "Inactive" };

    public static Task RunAsync() => RunAsync(new Options());

    public static async Task RunAsync(Options o)
    {
        Console.WriteLine("Recipe - DynaChange Organizer: disable / re-enable one rule");
        Console.WriteLine(new string('=', 60));
        Console.WriteLine($@"
Planned calls:
  POST v2/window {{""ServiceName"": ""{o.HostService}""}}
  POST v2/tools  dc.organizer.rule -> Status 3, organizer window id
  GET  v2/data   LIST.list -> rule_name={o.RuleName}, field_name={o.FieldName}, window_title={o.WindowTitle}
  PUT  v2/row    list, Row n;  PUT v2/change LIST/list row_status_flag=<opposite>;  POST v2/tools cb_apply
  OData p21_view_business_rule read-back; then the same with the original status");
        if (!ConfirmExecute())
            return;

        var (http, uiServer, baseUrl) = await InteractiveHelpers.CreateRawClientAsync();
        using var _ = http;

        var before = await StatusAsync(http, baseUrl, o);
        if (before.Count != 1)
        {
            Console.WriteLine($"Expected one matching rule, found {before.Count}");
            return;
        }
        var original = Label[(int)before[0]["row_status_flag"]!];
        var flipped = original == "Active" ? "Inactive" : "Active";
        Console.WriteLine($"\nRule {before[0]["business_rule_uid"]}: {original}");

        await using var s = new WindowSession(http, uiServer);
        await s.StartAsync(responseWindows: true);
        var host = await s.OpenWindowAsync(o.HostService);
        string? organizer = null;
        try
        {
            organizer = WindowSession.PopupIds(await s.RunToolAsync(host, "dc.organizer.rule"))[0];
            var rows = await s.RowsAsync(organizer, "list");
            var index = rows.FindIndex(r => r["rule_name"] == o.RuleName && r["field_name"] == o.FieldName
                                            && r["window_title"] == o.WindowTitle) + 1;
            if (index == 0)
            {
                Console.WriteLine("Rule not in the organizer list (internal rules are not listed)");
                return;
            }

            await SetStatusAsync(s, organizer, index, flipped);
            var now = (int)(await StatusAsync(http, baseUrl, o))[0]["row_status_flag"]!;
            Console.WriteLine($"Set {flipped}: row_status_flag={now} -> {(Label[now] == flipped ? "OK" : "NOT APPLIED")}");

            Console.WriteLine();
            Console.Write($"Type LEAVE to keep it {flipped}, anything else = restore {original}: ");
            if (Console.ReadLine()?.Trim() == "LEAVE")
                return;
            await SetStatusAsync(s, organizer, index, original);
            now = (int)(await StatusAsync(http, baseUrl, o))[0]["row_status_flag"]!;
            Console.WriteLine($"Restored {original}: row_status_flag={now} -> {(Label[now] == original ? "OK" : "NOT RESTORED")}");
        }
        finally
        {
            if (organizer is not null)
                await s.RunToolAsync(organizer, "cb_cancel");
            await s.CloseWindowAsync(host);
        }
    }

    private static async Task SetStatusAsync(WindowSession s, string organizer, int row, string status)
    {
        await s.SelectRowAsync(organizer, "list", row);                          // select FIRST
        await s.ChangeAsync(organizer, "LIST", "list", "row_status_flag", status);
        await s.RunToolAsync(organizer, "cb_apply");                             // commit
    }

    private static Task<Newtonsoft.Json.Linq.JArray> StatusAsync(HttpClient http, string baseUrl, Options o) =>
        InteractiveHelpers.ODataAsync(http, baseUrl, "p21_view_business_rule",
            $"rule_name eq '{o.RuleName}' and field_name eq '{o.FieldName}' and window_title eq '{o.WindowTitle}'",
            view: true, select: "business_rule_uid,row_status_flag,date_last_modified");
}
