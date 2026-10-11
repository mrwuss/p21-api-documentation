// Recipe: Create a Vendor and Its Supplier (Vendor service)
// Docs:   docs/03-Transaction-API.md#vendor-service-creating-a-vendor-and-its-supplier
//
// Create the vendor first: saving it creates the same-ID supplier, its
// division, and the vendor_supplier link (primary_vendor = 'Y').
//
// Rules the payload follows:
//   - vendor = ON is required.
//   - Leave id blank and P21 numbers the vendor; the ID comes back in the
//     result rows. A typed id must already exist in address, otherwise
//     "Enter a valid ID or leave ID blank."
//   - default_terms_id takes the terms description, not the terms ID.
//   - Omit currency_id; do not send the supplier tab (TABPAGE_6).
//   - Rebate accounts only with track_rebates = ON.

using Newtonsoft.Json.Linq;
using P21Examples.Common;
using static P21Examples.Recipes.RecipeHelpers;
using static P21Examples.Recipes.WritePathHelpers;

namespace P21Examples.Recipes;

public static class VendorCreate
{
    private const string Header = "TABPAGE_1.tp_1_dw_1";

    public static async Task RunAsync()
    {
        Console.WriteLine("Recipe - Create a Vendor and Its Supplier (Vendor service)");
        Console.WriteLine(new string('=', 60));

        var companyId = Ask("Company ID", "ACME");
        var id = Ask("Existing address ID to use, or '-' for blank (P21 assigns)", "-");
        var name = Ask("Vendor name", "Example Vendor");
        var apAccount = Ask("AP account (stored form, no dashes)", "2222200");
        var terms = Ask("Terms description", "Net 30 Days");
        var trackRebates = Ask("Track rebates (Y/N)", "N").ToUpperInvariant() == "Y";
        var rebateAccount = trackRebates ? Ask("Rebate account", "1111100") : "";
        var allowanceAccount = trackRebates ? Ask("Rebate allowance account", "3333300") : "";

        var header = new List<JObject> { Edit("company_id", companyId) };
        if (id != "-")
            header.Add(Edit("id", id));                  // must already exist in address
        header.AddRange(new[]
        {
            Edit("vendor", "ON"),                        // required for a vendor create
            Edit("name", name),
            Edit("mail_address1", "100 Main St"),
            Edit("mail_city", "Springfield"),
            Edit("mail_state", "IL"),
            Edit("mail_postal_code", "62701"),
            Edit("ap_account_no", apAccount),
            Edit("default_terms_id", terms),             // description, not ID
        });
        if (trackRebates)
            header.Add(Edit("track_rebates", "ON"));

        var elements = new List<JObject>
        {
            Element(Header, "Form", new[] { "company_id", "id" }, header.ToArray()),
        };
        if (trackRebates)
        {
            elements.Add(Element("REBATE_ACCOUNTS.d_vendor_rebate_accounts", "Form",
                Array.Empty<string>(),
                Edit("rebate_account_no", rebateAccount),
                Edit("rebate_allowance_account_no", allowanceAccount)));
        }
        var payload = Payload("Vendor", elements.ToArray());
        PrintPayload("Payload", payload);

        if (!ConfirmExecute())
            return;

        using var client = await P21Client.CreateAsync();
        var result = await client.Transaction.CreateAsync(payload);
        if (!CheckResult(result))
        {
            Console.WriteLine("Vendor create failed");
            return;
        }

        var vendorId = ResultValue(result, Header, "id") ?? id;
        Console.WriteLine($"Vendor ID: {vendorId}");

        // The vendor save also wrote the supplier and the link -- confirm all four.
        Console.WriteLine("\nVerify (OData read-back):");
        var checks = new (string Table, string Filter, string Select)[]
        {
            ("address", $"id eq {vendorId}", "id,name,delete_flag"),
            ("vendor", $"vendor_id eq {vendorId}",
             "vendor_id,ap_account_no,default_terms_id,track_rebates,rebate_account_no,rebate_allowance_account_no,delete_flag"),
            ("supplier", $"supplier_id eq {vendorId}", "supplier_id,supplier_name,delete_flag"),
            ("vendor_supplier", $"vendor_id eq {vendorId}", "vendor_id,supplier_id,primary_vendor,delete_flag"),
        };
        foreach (var (table, filter, select) in checks)
        {
            var rows = await Rows(client, table, filter, select);
            Console.WriteLine(rows.Count > 0
                ? $"  {table}: {rows.ToString(Newtonsoft.Json.Formatting.None)}"
                : $"  {table}: MISSING");
        }
    }
}
