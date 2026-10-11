// Recipe: Create a Ship-To
// Docs:   docs/recipes/create-ship-to.md
//
// Add a new ship-to to an existing customer in one stateless Transaction API
// call (ShipTo service), then read the ship-to, its address and its salesrep
// grid back over OData. address_id is assigned by P21 and echoed in the result.
//
// Key rules (verified live — see the recipe page):
//   - UseCodeValues: true with STORED codes (terms_id code, invoice_type "IN",
//     Y/N flags). Under false, terms_id wants the description.
//   - salesrep_id and ship_to_name are NOT on TABPAGE_1.shiptomain (Invalid
//     column name). The rep goes on TABPAGE_SALESREP.tabpage_salesrep; the
//     ship-to's name is address_name.
//   - The new ship-to inherits the customer's primary rep. For a different rep,
//     add the wanted rep (primary Y, 100%) FIRST, then retire the inherited one
//     with delete_flag "Y" — in the same call. Same rep: leave the grid out.

using Newtonsoft.Json.Linq;
using P21Examples.Common;
using static P21Examples.Recipes.RecipeHelpers;

namespace P21Examples.Recipes;

public static class CreateShipTo
{
    // Generic placeholders — press Enter at each prompt to keep them.
    private const string CompanyId = "ACME";
    private const string CustomerId = "1001";              // existing customer
    private const string AddressName = "ACME Industrial - East Plant";
    private const string DefaultBranch = "10";
    private const string PreferredLocationId = "10";
    private const string TermsId = "1";                    // the STORED terms_id code
    private const string InvoiceType = "IN";               // stored code ("Invoice" is the label)
    private const string TaxGroupId = "TAX-01";            // stored tax group code
    private const string SalesrepId = "200";               // the rep this ship-to should carry
    private const string Address1 = "456 Industrial Pkwy";
    private const string City = "Des Moines";
    private const string State = "IA";
    private const string PostalCode = "50309";
    private const string Country = "USA";
    private const string Phone = "515-555-0100";

    private const int RowStatusActive = 704;               // customer_salesrep "Active"

    public static async Task RunAsync()
    {
        Console.WriteLine("Recipe - Create a Ship-To (ShipTo)");
        Console.WriteLine(new string('=', 60));

        var companyId = Ask("Company ID", CompanyId);
        var customerId = Ask("Customer ID", CustomerId);
        var addressName = Ask("Ship-to name (address_name)", AddressName);
        var branch = Ask("Default branch", DefaultBranch);
        var location = Ask("Preferred location ID", PreferredLocationId);
        var termsId = Ask("Terms ID (stored code)", TermsId);
        var taxGroupId = Ask("Tax group ID", TaxGroupId);
        var salesrepId = Ask("Salesrep ID for the ship-to", SalesrepId);

        using var client = await P21Client.CreateAsync();

        // 1. The rep the new ship-to will inherit: the customer's live primary rep.
        //    customer_id is numeric on OData — no quotes. OData returns the stored
        //    column primary_salesrep_flag; the ShipTo grid calls it primary_salesrep.
        var reps = (JArray)(await client.OData.QueryAsync("customer_salesrep",
            filter: $"customer_id eq {customerId} and row_status_flag eq {RowStatusActive}"))["value"]!;
        var inherited = reps
            .Where(r => r["primary_salesrep_flag"]?.ToString() == "Y")
            .Select(r => r["salesrep_id"]!.ToString())
            .ToList();
        Console.WriteLine($"Customer's primary rep (inherited by the ship-to): {string.Join(", ", inherited)}");

        // 2. Salesrep rows: add the wanted rep first, then retire each inherited one.
        var repRows = new JArray();
        if (!(inherited.Count == 1 && inherited[0] == salesrepId))
        {
            repRows.Add(Row(("salesrep_id", salesrepId), ("primary_salesrep", "Y"),
                            ("commission_percentage", "100")));
            foreach (var rep in inherited.Where(r => r != salesrepId))
                repRows.Add(Row(("salesrep_id", rep), ("delete_flag", "Y")));
        }

        var elements = new JArray
        {
            Form("TABPAGE_1.shiptomain",
                ("company_id", companyId), ("customer_id", customerId), ("address_name", addressName),
                ("default_branch", branch), ("terms_id", termsId), ("invoice_type", InvoiceType),
                ("tax_group_id", taxGroupId), ("phys_address1", Address1), ("phys_city", City),
                ("phys_state", State), ("phys_postal_code", PostalCode), ("phys_country", Country)),
            Form("TABPAGE_2.tp_2_dw_2",
                ("mail_address1", Address1), ("mail_city", City), ("mail_state", State),
                ("mail_postal_code", PostalCode), ("mail_country", Country)),
            Form("TABPAGE_5.tp_5_dw_5", ("central_phone_number", Phone)),
            Form("TABPAGE_OEOPTIONS.tabpage_oeoptions", ("preferred_location_id", location)),
        };
        if (repRows.Count > 0)
        {
            elements.Add(new JObject
            {
                ["Name"] = "TABPAGE_SALESREP.tabpage_salesrep", ["Type"] = "List",
                ["Keys"] = new JArray { "salesrep_id" }, ["Rows"] = repRows,
            });
        }

        var payload = new JObject
        {
            ["Name"] = "ShipTo",
            ["UseCodeValues"] = true,   // send stored codes: terms_id, invoice_type, Y/N flags
            ["Transactions"] = new JArray {
                new JObject { ["Status"] = "New", ["DataElements"] = elements } },
        };

        PrintPayload("ShipTo payload (POST /api/v2/transaction)", payload);
        if (!ConfirmExecute())
            return;

        // 3. Create — HTTP 200 even on failure, so check the Summary
        var result = await client.Transaction.CreateAsync(payload);
        if (!CheckResult(result))
        {
            Console.WriteLine("Ship-to create failed.");
            return;
        }

        // The generated address_id comes back in the passed transaction's result rows
        var shipToId = result.Results?["Transactions"]?
            .Where(t => t["Status"]?.ToString() == "Passed")
            .SelectMany(t => t["DataElements"]!)
            .SelectMany(e => e["Rows"]!)
            .SelectMany(r => r["Edits"]!)
            .Where(e => e["Name"]?.ToString() == "address_id" && !string.IsNullOrEmpty(e["Value"]?.ToString()))
            .Select(e => e["Value"]!.ToString())
            .LastOrDefault();
        Console.WriteLine($"Created ship-to (address_id): {shipToId}");
        if (string.IsNullOrEmpty(shipToId))
        {
            Console.WriteLine("No address_id in the response — look the ship-to up by name.");
            return;
        }

        // 4. Read back via OData — Succeeded is not proof every value landed
        Console.WriteLine("\nVerify via OData:");
        Console.WriteLine(new string('-', 50));
        foreach (var r in (JArray)(await client.OData.QueryAsync(
                     "ship_to", filter: $"ship_to_id eq {shipToId}"))["value"]!)
            Console.WriteLine($"  ship_to: customer_id={r["customer_id"]} default_branch={r["default_branch"]} " +
                              $"terms_id={r["terms_id"]} invoice_type={r["invoice_type"]} " +
                              $"tax_group_id={r["tax_group_id"]} preferred_location_id={r["preferred_location_id"]}");
        foreach (var r in (JArray)(await client.OData.QueryAsync(
                     "address", filter: $"id eq {shipToId}"))["value"]!)
            Console.WriteLine($"  address: name={r["name"]} phys_address1={r["phys_address1"]} " +
                              $"phys_city={r["phys_city"]} central_phone_number={r["central_phone_number"]}");

        var live = new List<JToken>();
        foreach (var r in (JArray)(await client.OData.QueryAsync(
                     "ship_to_salesrep", filter: $"ship_to_id eq {shipToId}"))["value"]!)
        {
            Console.WriteLine($"  rep: salesrep_id={r["salesrep_id"]} primary_salesrep={r["primary_salesrep"]} " +
                              $"commission_percentage={r["commission_percentage"]} delete_flag={r["delete_flag"]}");
            if (r["delete_flag"]?.ToString() != "Y") live.Add(r);
        }
        var ok = live.Count == 1 && live[0]["salesrep_id"]?.ToString() == salesrepId
                 && live[0]["primary_salesrep"]?.ToString() == "Y"
                 && (decimal?)live[0]["commission_percentage"] == 100m;
        Console.WriteLine($"\nOne live primary rep {salesrepId} at 100%: {(ok ? "OK" : "MISMATCH")}");
    }

    private static JObject Row(params (string Name, string Value)[] edits) => new()
    {
        ["Edits"] = new JArray(edits.Select(e => Edit(e.Name, e.Value))),
        ["RelativeDateEdits"] = new JArray(),
    };

    private static JObject Form(string name, params (string Name, string Value)[] edits) => new()
    {
        ["Name"] = name, ["Type"] = "Form", ["Keys"] = new JArray(),
        ["Rows"] = new JArray { Row(edits) },
    };

    private static string Ask(string label, string fallback)
    {
        Console.Write($"{label} [{fallback}]: ");
        var answer = Console.ReadLine()?.Trim();
        return string.IsNullOrEmpty(answer) ? fallback : answer;
    }
}
