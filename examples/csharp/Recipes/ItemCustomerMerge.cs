// Recipe: Merge One Item or Customer into Another (m_itemmerge / m_customermerge)
// Docs:   docs/03-Transaction-API.md#item-merge-and-customer-merge-m_itemmerge-m_customermerge
//
// Hidden menu services (not in /api/v2/services) driven through
// POST /api/v2/transaction. A merge is ONE-WAY: the source is soft-deleted and
// its history moved, rewritten, or deleted. Test tenant first.
//
// Guards before posting: both IDs resolve exactly to live records and differ.
// With create_alt_code_flag = ON, a merged item ID becomes an alternate code on
// the target, and both ID fields resolve alternate codes -- naming an
// already-merged item would act on whichever live item holds that code.
//
// Deciding success: an item merge reports Succeeded 1. A customer merge
// reports Failed 1 ("History is not available for w_customer_merge_maint
// window") on EVERY success -- read customer_merge_audit and the source's
// delete_flag instead, and never retry.

using Newtonsoft.Json.Linq;
using P21Examples.Common;
using static P21Examples.Recipes.RecipeHelpers;
using static P21Examples.Recipes.WritePathHelpers;

namespace P21Examples.Recipes;

public static class ItemCustomerMerge
{
    public static async Task RunAsync()
    {
        Console.WriteLine("Recipe - Item / Customer Merge (one-way; test tenant first)");
        Console.WriteLine(new string('=', 60));

        var mode = Ask("Mode (item, customer)", "item").ToLowerInvariant();
        JObject payload;
        string source, target, company = "";
        if (mode == "item")
        {
            source = Ask("Source item ID (merged away)", "ITEM-002");
            target = Ask("Target item ID (survives)", "ITEM-001");
            payload = Payload("m_itemmerge",
                MergeForm(new[] { "source_item_id", "target_item_id" },
                    Edit("source_item_id", source),
                    Edit("target_item_id", target),            // omitted = silent no-op success
                    Edit("create_alt_code_flag", "ON"),
                    Edit("keep_restrictions_flag", "OFF"),
                    Edit("schedule_merge_flag", "OFF")));      // ON needs the Item Merge Schedule task
        }
        else if (mode == "customer")
        {
            company = Ask("Company ID", "ACME");
            source = Ask("Source customer ID (merged away)", "CUST-101");
            target = Ask("Target customer ID (survives)", "CUST-100");
            payload = Payload("m_customermerge",
                MergeForm(new[] { "source_customer_id", "target_customer_id" },
                    Edit("company_id", company),
                    Edit("source_customer_id", source),
                    Edit("target_customer_id", target),
                    Edit("credit_limit_type", "Use Highest Credit Limit"),
                    Edit("keep_cust_as_shipto", "ON")));
        }
        else
        {
            Console.WriteLine($"Unknown mode: {mode}");
            return;
        }

        PrintPayload("Payload", payload);
        Console.WriteLine("A merge cannot be undone.");
        if (!ConfirmExecute())
            return;

        using var client = await P21Client.CreateAsync();

        if (mode == "item")
        {
            var uids = new List<long>();
            foreach (var id in new[] { source, target })
            {
                var rows = (await Rows(client, "inv_mast",
                        $"item_id eq {Q(id)} and delete_flag eq 'N'", "inv_mast_uid,item_id"))
                    .Where(r => (string?)r["item_id"] == id).ToList();   // exact match only
                if (rows.Count == 0)
                {
                    Console.WriteLine($"{id} is not a live item ID -- not posting");
                    return;
                }
                uids.Add((long)rows[0]["inv_mast_uid"]!);
            }
            if (uids[0] == uids[1])
            {
                Console.WriteLine("Source and target are the same item");
                return;
            }

            CheckResult(await client.Transaction.CreateAsync(payload));
            Console.WriteLine("\nVerify (OData read-back):");
            Console.WriteLine($"  source inv_mast: {Compact(await Rows(client, "inv_mast", $"inv_mast_uid eq {uids[0]}", "item_id,delete_flag,item_desc,extended_desc"))}");
            Console.WriteLine($"  target inv_mast: {Compact(await Rows(client, "inv_mast", $"inv_mast_uid eq {uids[1]}", "item_id,delete_flag"))}");
            Console.WriteLine($"  item_merge_audit: {Compact(await Rows(client, "item_merge_audit", $"source_inv_mast_uid eq {uids[0]}", "item_merge_run,source_item_id,target_item_id,processed_flag,message"))}");
            Console.WriteLine($"  alternate_code on target: {Compact(await Rows(client, "alternate_code", $"inv_mast_uid eq {uids[1]} and alternate_code eq {Q(source)}", "alternate_code,delete_flag"))}");
            return;
        }

        if (source == target)
        {
            Console.WriteLine("Source and target are the same customer");
            return;
        }
        foreach (var id in new[] { source, target })
        {
            if ((await Rows(client, "customer", $"customer_id eq {id} and delete_flag eq 'N'", "customer_id")).Count == 0)
            {
                Console.WriteLine($"{id} is not a live customer -- not posting");
                return;
            }
        }

        CheckResult(await client.Transaction.CreateAsync(payload));
        Console.WriteLine("  (A successful customer merge reports Failed: 1 -- the read-back decides.)");
        var audit = await Rows(client, "customer_merge_audit",
            $"source_customer_id eq {source} and target_customer_id eq {target}",
            "customer_merge_run,processed_flag,merge_message,keep_custas_shipto_flag");
        var src = await Rows(client, "customer", $"customer_id eq {source}", "customer_id,customer_name,delete_flag");
        Console.WriteLine("\nVerify (OData read-back):");
        Console.WriteLine($"  customer_merge_audit: {Compact(audit)}");
        Console.WriteLine($"  source customer: {Compact(src)}");
        var merged = audit.Any(r => ((string?)r["merge_message"] ?? "").StartsWith("Merge was Successful"))
                     && src.Count > 0 && (string?)src[0]["delete_flag"] == "Y";
        Console.WriteLine($"\nMerge committed: {(merged ? "YES" : "NO")}");
    }

    /// <summary>The merge window's single FORM.form element.</summary>
    private static JObject MergeForm(string[] keys, params JObject[] edits) =>
        new JObject
        {
            ["Name"] = "FORM.form", ["Type"] = "Form", ["Keys"] = new JArray(keys),
            ["Rows"] = new JArray { new JObject { ["Edits"] = new JArray(edits) } }
        };

    private static string Compact(JToken token) => token.ToString(Newtonsoft.Json.Formatting.None);
}
