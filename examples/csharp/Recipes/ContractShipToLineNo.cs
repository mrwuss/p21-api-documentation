// Recipe: Attach a Ship-To to a Contract, and Update a Line by line_no
//         (JobContractPricing)
// Docs:   docs/03-Transaction-API.md#attaching-a-ship-to-to-an-existing-contract
//         docs/03-Transaction-API.md#updating-an-existing-contract
//
// Both modes identify the header by job_no + contract_no in Edits (Keys [])
// and nothing else. Without end_date the header is not re-saved and its date
// validations do not run, so an expired contract can be edited too.
//   attach-ship-to  CUSTOMER_SHIP_TO.customer_ship_to row keyed on
//                   customer_id + ship_to_id (pricing follows this grid)
//   update-line     JOBPRICELINE selected by line_no -- needed when an item_id
//                   repeats, because an item_id key lands on the first match.
//                   An optional JOBPRICECOST row binds to the selected line
//                   and needs IgnoreDisabled at the top level.

using Newtonsoft.Json.Linq;
using P21Examples.Common;
using static P21Examples.Recipes.RecipeHelpers;
using static P21Examples.Recipes.WritePathHelpers;

namespace P21Examples.Recipes;

public static class ContractShipToLineNo
{
    private const string LineColumns =
        "line_no,inv_mast_uid,price,qty_maximum,commission_cost_type_cd,commission_cost_value,date_last_modified";

    public static async Task RunAsync()
    {
        Console.WriteLine("Recipe - Contract Ship-To / Update by line_no (JobContractPricing)");
        Console.WriteLine(new string('=', 60));

        var mode = Ask("Mode (attach-ship-to, update-line)", "attach-ship-to").ToLowerInvariant();
        var jobNo = Ask("Job no", "1001");
        var contractNo = Ask("Contract no", "JOB-1001");

        // Header: job_no + contract_no only. No end_date -> no header re-save.
        var header = Element("FORM.d_dw_job_price_hdr", "Form", Array.Empty<string>(),
            Edit("job_no", jobNo), Edit("contract_no", contractNo));

        string customerId = "", shipToId = "", lineNo = "", field = "", value = "", commission = "";
        if (mode == "attach-ship-to")
        {
            customerId = Ask("Customer ID", "100198");
            shipToId = Ask("Ship-to ID", "100199");
        }
        else if (mode == "update-line")
        {
            lineNo = Ask("Line no", "2");
            field = Ask("JOBPRICELINE field to change", "qty_maximum");
            value = Ask("New value", "50");
            commission = Ask("Value commission cost, or '-' for none", "-");
        }
        else
        {
            Console.WriteLine($"Unknown mode: {mode}");
            return;
        }

        // Dry run uses a placeholder item for the commission-cost row.
        PrintPayload("Payload", BuildPayload(mode, header, customerId, shipToId,
                                             lineNo, field, value, commission, "ITEM-001"));
        if (!ConfirmExecute())
            return;

        using var client = await P21Client.CreateAsync();
        var before = await Snapshot(client, jobNo, contractNo);
        if (before == null)
        {
            Console.WriteLine($"Contract {contractNo} / job {jobNo} not found");
            return;
        }
        Show("Before:", before.Value);

        var lineItemId = "ITEM-001";
        if (mode == "update-line")
        {
            if (!before.Value.Lines.TryGetValue(lineNo, out var line))
            {
                Console.WriteLine($"Line {lineNo} not found on the contract");
                return;
            }
            var item = await Rows(client, "inv_mast", $"inv_mast_uid eq {line["inv_mast_uid"]}", "item_id");
            lineItemId = (string)item[0]["item_id"]!;
        }

        var payload = BuildPayload(mode, header, customerId, shipToId,
                                   lineNo, field, value, commission, lineItemId);
        Console.WriteLine();
        CheckResult(await client.Transaction.CreateAsync(payload));

        var after = (await Snapshot(client, jobNo, contractNo))!.Value;
        Show("After (OData read-back):", after);
        var resaved = (string?)after.Header["date_last_modified"] != (string?)before.Value.Header["date_last_modified"];
        Console.WriteLine($"\nHeader re-saved: {(resaved ? "YES" : "no")}");
        if (mode == "attach-ship-to")
        {
            var landed = after.ShipTos.Any(r => (string?)r["customer_id"] == customerId &&
                                                (string?)r["ship_to_id"] == shipToId);
            Console.WriteLine($"Ship-to on the contract: {(landed ? "OK" : "MISSING")}");
        }
        else
        {
            var changed = after.Lines.Keys.Where(k =>
                !before.Value.Lines.TryGetValue(k, out var b) || !JToken.DeepEquals(b, after.Lines[k]));
            Console.WriteLine($"Lines changed: [{string.Join(", ", changed)}]  (expected only [{lineNo}])");
        }
    }

    private static JObject BuildPayload(string mode, JObject header, string customerId, string shipToId,
        string lineNo, string field, string value, string commission, string lineItemId)
    {
        if (mode == "attach-ship-to")
        {
            return Payload("JobContractPricing", header,
                Element("CUSTOMER_SHIP_TO.customer_ship_to", "List", new[] { "customer_id", "ship_to_id" },
                    Edit("customer_id", customerId), Edit("ship_to_id", shipToId)));
        }

        var elements = new List<JObject>
        {
            header,
            // Select the line by line_no: an item_id key lands on the FIRST line with that item.
            Element("JOBPRICELINE.jobpriceline", "List", new[] { "line_no" },
                Edit("line_no", lineNo), Edit(field, value)),
        };
        var payload = Payload("JobContractPricing", elements.ToArray());
        if (commission != "-")
        {
            payload["IgnoreDisabled"] = true;  // top level -- required for commission cost
            // No line_no key on JOBPRICECOST: it binds to the line selected above.
            ((JArray)payload["Transactions"]![0]!["DataElements"]!).Add(new JObject
            {
                ["Name"] = "JOBPRICECOST.jobpricecost", ["Type"] = "Form",
                ["Keys"] = new JArray { "item_id" },
                ["Rows"] = new JArray { new JObject { ["Edits"] = new JArray {
                    Edit("item_id", lineItemId),
                    Edit("commission_cost_type_cd", "Value"),   // type before value
                    Edit("commission_cost_value", commission),
                } } }
            });
        }
        return payload;
    }

    private static async Task<(JObject Header, JArray ShipTos, Dictionary<string, JObject> Lines)?> Snapshot(
        P21Client client, string jobNo, string contractNo)
    {
        var headers = await Rows(client, "job_price_hdr",
            $"job_no eq {Q(jobNo)} and contract_no eq {Q(contractNo)}",
            "job_price_hdr_uid,job_no,contract_no,end_date,date_last_modified");
        if (headers.Count == 0)
            return null;
        var uid = headers[0]["job_price_hdr_uid"];
        var shipTos = await Rows(client, "job_price_customer_shipto", $"job_price_hdr_uid eq {uid}",
            "customer_id,ship_to_id,row_status_flag");
        var lines = await Rows(client, "job_price_line", $"job_price_hdr_uid eq {uid}", LineColumns);
        return ((JObject)headers[0], shipTos,
                lines.Cast<JObject>().ToDictionary(l => (string)l["line_no"]!, l => l));
    }

    private static void Show(string label, (JObject Header, JArray ShipTos, Dictionary<string, JObject> Lines) snap)
    {
        Console.WriteLine($"\n{label}");
        Console.WriteLine($"  header: {snap.Header.ToString(Newtonsoft.Json.Formatting.None)}");
        foreach (var r in snap.ShipTos)
            Console.WriteLine($"  ship-to: {r.ToString(Newtonsoft.Json.Formatting.None)}");
        foreach (var k in snap.Lines.Keys.OrderBy(int.Parse))
            Console.WriteLine($"  line: {snap.Lines[k].ToString(Newtonsoft.Json.Formatting.None)}");
    }
}
