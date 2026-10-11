// Recipe: Create an Assembly on a Plain Item, Then Edit It (Assembly service)
// Docs:   docs/03-Transaction-API.md#assembly-service
//
// Four modes, all keyed Status "New" Transactions, none using IgnoreDisabled:
//   create            header (inv_mast_item_id + production_order_processing)
//                     plus one TABPAGE_17.tp_17_dw_17 row per component
//   set-flag          a header flag, keyed on inv_mast_item_id
//   set-qty           one component's quantity, keyed on item_id_service_labor_id
//   delete-component  delete_flag = ON on one component row
//
// Create rules: the item must exist, must not already have an assembly, and
// must not already be a component of another assembly (the Transaction API
// answers that popup No and the save fails -- use the Interactive window).
// Send production_order_processing explicitly. allow_disassembly is disabled
// while production_order_processing is OFF.

using Newtonsoft.Json.Linq;
using P21Examples.Common;
using static P21Examples.Recipes.RecipeHelpers;
using static P21Examples.Recipes.WritePathHelpers;

namespace P21Examples.Recipes;

public static class AssemblyCreateEdit
{
    private const string Header = "TABPAGE_1.assemblyhdr";
    private const string Components = "TABPAGE_17.tp_17_dw_17";

    public static async Task RunAsync()
    {
        Console.WriteLine("Recipe - Create / Edit an Assembly (Assembly service)");
        Console.WriteLine(new string('=', 60));

        var mode = Ask("Mode (create, set-flag, set-qty, delete-component)", "create").ToLowerInvariant();
        var itemId = Ask("Assembly item ID", "ITEM-001");

        JObject payload;
        switch (mode)
        {
            case "create":
            {
                var specs = Ask("Components as ID:QTY, comma-separated", "COMP-A:2,COMP-B:1")
                    .Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);
                var pop = Ask("production_order_processing (ON/OFF)", "OFF");
                var rows = new JArray();
                foreach (var spec in specs)
                {
                    var cut = spec.LastIndexOf(':');
                    rows.Add(Row(Edit("item_id_service_labor_id", spec[..cut]),
                                 Edit("quantity", spec[(cut + 1)..])));
                }
                payload = Payload("Assembly",
                    HeaderElement(itemId, Edit("production_order_processing", pop)),
                    ComponentElement(rows));
                break;
            }
            case "set-flag":
            {
                var field = Ask("Header field", "production_order_processing");
                var value = Ask("Value (ON/OFF)", "ON");
                payload = Payload("Assembly", HeaderElement(itemId, Edit(field, value)));
                break;
            }
            case "set-qty":
            {
                var componentId = Ask("Component item ID", "COMP-A");
                var qty = Ask("New quantity", "5");
                payload = Payload("Assembly", HeaderElement(itemId), ComponentElement(new JArray {
                    Row(Edit("item_id_service_labor_id", componentId), Edit("quantity", qty)) }));
                break;
            }
            case "delete-component":
            {
                var componentId = Ask("Component item ID", "COMP-B");
                payload = Payload("Assembly", HeaderElement(itemId), ComponentElement(new JArray {
                    Row(Edit("item_id_service_labor_id", componentId), Edit("delete_flag", "ON")) }));
                break;
            }
            default:
                Console.WriteLine($"Unknown mode: {mode}");
                return;
        }

        PrintPayload("Payload", payload);
        if (!ConfirmExecute())
            return;

        using var client = await P21Client.CreateAsync();
        var items = await Rows(client, "inv_mast",
            $"item_id eq {Q(itemId)} and delete_flag eq 'N'", "inv_mast_uid");
        if (items.Count == 0)
        {
            Console.WriteLine($"Item {itemId} not found");
            return;
        }
        var uid = (long)items[0]["inv_mast_uid"]!;

        if (mode == "create")
        {
            if ((await Rows(client, "assembly_hdr", $"inv_mast_uid eq {uid}", "inv_mast_uid")).Count > 0)
            {
                Console.WriteLine($"{itemId} already has an assembly -- edit it instead");
                return;
            }
            var usedIn = await Rows(client, "assembly_line",
                $"component_inv_mast_uid eq {uid} and delete_flag eq 'N'", "inv_mast_uid");
            if (usedIn.Count > 0)
            {
                Console.WriteLine($"{itemId} is a component of {usedIn.Count} assembly(ies): the " +
                                  "Transaction API cannot answer the popup -- use the Interactive Assembly window");
                return;
            }
        }
        else
        {
            Console.WriteLine("\nBefore:");
            await ShowAssembly(client, uid);
        }

        Console.WriteLine();
        CheckResult(await client.Transaction.CreateAsync(payload));
        Console.WriteLine("\nAfter (OData read-back):");
        await ShowAssembly(client, uid);
    }

    private static JObject Row(params JObject[] edits) =>
        new JObject { ["Edits"] = new JArray(edits), ["RelativeDateEdits"] = new JArray() };

    private static JObject HeaderElement(string itemId, params JObject[] extra)
    {
        var edits = new List<JObject> { Edit("inv_mast_item_id", itemId) };
        edits.AddRange(extra);
        return Element(Header, "Form", new[] { "inv_mast_item_id" }, edits.ToArray());
    }

    private static JObject ComponentElement(JArray rows) =>
        new JObject
        {
            ["Name"] = Components, ["Type"] = "List",
            ["Keys"] = new JArray { "item_id_service_labor_id" }, ["Rows"] = rows
        };

    private static async Task ShowAssembly(P21Client client, long uid)
    {
        var hdr = await Rows(client, "assembly_hdr", $"inv_mast_uid eq {uid}",
            "inv_mast_uid,production_order_processing,allow_disassembly,delete_flag");
        Console.WriteLine($"  assembly_hdr: {(hdr.Count > 0 ? hdr.ToString(Newtonsoft.Json.Formatting.None) : "NONE")}");
        foreach (var line in await Rows(client, "assembly_line", $"inv_mast_uid eq {uid}",
                     "sequence_number,component_inv_mast_uid,quantity,delete_flag"))
        {
            var comp = await Rows(client, "inv_mast",
                $"inv_mast_uid eq {line["component_inv_mast_uid"]}", "item_id");
            line["component_item_id"] = comp.Count > 0 ? comp[0]["item_id"] : null;
            Console.WriteLine($"  assembly_line: {line.ToString(Newtonsoft.Json.Formatting.None)}");
        }
    }
}
