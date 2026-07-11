// Recipe: Update Contract Lines
// Docs:   docs/recipes/update-contract-lines.md
//
// Update prices on existing JobContractPricing lines, insert new lines onto
// an existing contract (upsert), and set commission costs — all through the
// stateless Transaction API.
//
// Key rules (all verified live — see the recipe page):
//   - Status is "New" for BOTH create and update ("Existing" returns HTTP 500).
//   - pricing_method MUST precede price in the Edits, or price lands as $0.
//   - One POST per line: inserts re-save the shared header and collide when batched.
//   - end_date must be >= today; the header is re-validated on every save.
//   - IgnoreDisabled: true (top level) is required for commission-cost writes.

using System.Globalization;
using Newtonsoft.Json.Linq;
using P21Examples.Common;
using static P21Examples.Recipes.RecipeHelpers;

namespace P21Examples.Recipes;

public static class UpdateContractLines
{
    private const string CompanyId = "ACME";
    private const string ContractNo = "A120-12";
    private const string JobNo = "31";           // unique across renewals — always include it
    private const string EndDate = "2030-01-01"; // required on EVERY submit, must be >= today

    public static async Task RunAsync()
    {
        Console.WriteLine("Recipe - Update Contract Lines (JobContractPricing)");
        Console.WriteLine(new string('=', 60));

        using var client = await P21Client.CreateAsync();

        var lines = new (string ItemId, string Uom, decimal Price, decimal? Commission)[]
        {
            ("WIDGET-001", "EA", 36.58m, 17.19m),  // already on contract -> updated
            ("WIDGET-002", "EA", 12.40m, null),    // not on contract     -> inserted (upsert)
        };

        // One POST per line: inserts re-save the shared header and collide when batched.
        var payloads = lines.Select(l => LinePayload(l.ItemId, l.Uom, l.Price, l.Commission)).ToList();
        for (var i = 0; i < lines.Length; i++)
            PrintPayload($"Payload for {lines[i].ItemId}", payloads[i]);

        if (!ConfirmExecute())
            return;

        // ------------------------------------------------------------------
        // Write: one transaction per POST
        // ------------------------------------------------------------------
        foreach (var (line, payload) in lines.Zip(payloads))
        {
            Console.WriteLine($"\nPosting {line.ItemId}...");
            var result = await client.Transaction.CreateAsync(payload);
            Console.WriteLine(CheckResult(result)
                ? $"  {line.ItemId}: OK"
                : $"  {line.ItemId}: FAILED");
        }

        // ------------------------------------------------------------------
        // Verify via OData (no joins: chain the uid columns)
        // ------------------------------------------------------------------
        Console.WriteLine("\nVerify via OData:");
        Console.WriteLine(new string('-', 50));

        // Renewals can return two headers for one contract_no — match job_no too.
        var hdrRows = (JArray)(await client.OData.QueryAsync(
            "job_price_hdr", filter: $"contract_no eq '{ContractNo}'"))["value"]!;
        if (hdrRows.Count == 0)
        {
            Console.WriteLine($"  Contract {ContractNo} not found");
            return;
        }
        var hdrUid = hdrRows[0]["job_price_hdr_uid"];

        foreach (var l in lines)
        {
            var imRows = (JArray)(await client.OData.QueryAsync(
                "inv_mast", filter: $"item_id eq '{l.ItemId}'"))["value"]!;
            if (imRows.Count == 0)
            {
                Console.WriteLine($"  {l.ItemId}: item not found in inv_mast");
                continue;
            }
            var imUid = imRows[0]["inv_mast_uid"];

            var lineRows = (JArray)(await client.OData.QueryAsync(
                "job_price_line",
                filter: $"job_price_hdr_uid eq {hdrUid} and inv_mast_uid eq {imUid}"))["value"]!;
            if (lineRows.Count == 0)
            {
                Console.WriteLine($"  {l.ItemId}: no contract line found");
                continue;
            }

            var match = (decimal)lineRows[0]["price"]! == l.Price ? "OK" : "MISMATCH";
            Console.WriteLine(
                $"  {l.ItemId}: price={lineRows[0]["price"]} expected={l.Price} -> {match}");
        }
    }

    /// <summary>Build a one-line upsert payload, optionally with a commission cost.</summary>
    private static JObject LinePayload(
        string itemId, string uom, decimal price, decimal? commissionCost)
    {
        var elements = new JArray
        {
            new JObject
            {
                // Header: Keys stays EMPTY; the key fields go in Edits.
                ["Name"] = "FORM.d_dw_job_price_hdr", ["Type"] = "Form",
                ["Keys"] = new JArray(),
                ["Rows"] = new JArray { new JObject {
                    ["Edits"] = new JArray {
                        Edit("company_id",  CompanyId),
                        Edit("contract_no", ContractNo),
                        Edit("job_no",      JobNo),
                        Edit("end_date",    EndDate),
                    },
                    ["RelativeDateEdits"] = new JArray() } }
            },
            new JObject
            {
                // Line: keyed by item_id — updates the row if it exists, inserts if not.
                ["Name"] = "JOBPRICELINE.jobpriceline", ["Type"] = "List",
                ["Keys"] = new JArray { "item_id" },
                ["Rows"] = new JArray { new JObject {
                    ["Edits"] = new JArray {
                        Edit("item_id",        itemId),
                        Edit("uom",            uom),
                        Edit("pricing_method", "Price"),           // MUST come before price
                        Edit("price",          price.ToString(CultureInfo.InvariantCulture)),
                    },
                    ["RelativeDateEdits"] = new JArray() } }
            },
        };

        var payload = new JObject
        {
            ["Name"] = "JobContractPricing", ["UseCodeValues"] = false,
            ["Transactions"] = new JArray {
                new JObject { ["Status"] = "New", ["DataElements"] = elements } }
        };

        if (commissionCost is not null)
        {
            payload["IgnoreDisabled"] = true;  // top level, NOT inside the Transaction
            elements.Add(new JObject
            {
                ["Name"] = "JOBPRICECOST.jobpricecost", ["Type"] = "Form",
                ["Keys"] = new JArray { "item_id" },
                ["Rows"] = new JArray { new JObject { ["Edits"] = new JArray {
                    Edit("item_id",                 itemId),
                    Edit("commission_cost_type_cd", "Value"),      // type BEFORE value
                    Edit("commission_cost_value",   commissionCost.Value.ToString(CultureInfo.InvariantCulture)),
                } } }
            });
        }

        return payload;
    }
}
