// Recipe: Create a Customer
// Docs:   docs/recipes/create-customer.md
//
// Create a customer master record in one stateless Transaction API call
// (service: Customer). customer_id is auto-assigned and returned in the
// result rows.
//
// Key rules (all verified live — see the recipe page):
//   - salesrep_id is hard-required; omitting it fails with the misleading
//     "Salesrep ID is required for a new ship to." (the field is on TABPAGE_1).
//   - default_branch is required and NOT defaulted by the template.
//   - No zip -> salesrep cascade; the rep must be supplied explicitly.
//   - HTTP 200 is not success; the generated customer_id comes back in the
//     result rows of TABPAGE_1.tp_1_dw_1.

using Newtonsoft.Json.Linq;
using P21Examples.Common;
using static P21Examples.Recipes.RecipeHelpers;

namespace P21Examples.Recipes;

public static class CreateCustomer
{
    public static async Task RunAsync()
    {
        Console.WriteLine("Recipe - Create a Customer (Customer)");
        Console.WriteLine(new string('=', 60));

        using var client = await P21Client.CreateAsync();

        var payload = BuildCustomerPayload();
        PrintPayload("Customer payload", payload);

        if (!ConfirmExecute())
            return;

        // ------------------------------------------------------------------
        // Write
        // ------------------------------------------------------------------
        var result = await client.Transaction.CreateAsync(payload);
        if (!CheckResult(result))
            return;

        // The generated customer_id comes back in the TABPAGE_1.tp_1_dw_1 rows
        var customerId = (result.Raw?.SelectTokens(
                "$.Results.Transactions[?(@.Status == 'Passed')]" +
                ".DataElements[?(@.Name == 'TABPAGE_1.tp_1_dw_1')]" +
                ".Rows[*].Edits[?(@.Name == 'customer_id')].Value")
            ?? Enumerable.Empty<JToken>()).FirstOrDefault()?.ToString();

        Console.WriteLine($"\nCreated customer_id: {customerId}");
        if (string.IsNullOrEmpty(customerId))
            return;

        // ------------------------------------------------------------------
        // Verify: read the customer back via OData
        // ------------------------------------------------------------------
        Console.WriteLine("\nVerify via OData:");
        Console.WriteLine(new string('-', 50));

        var rows = (JArray)(await client.OData.QueryAsync(
            "customer", filter: $"customer_id eq {customerId}"))["value"]!;
        if (rows.Count > 0)
        {
            var cust = rows[0];
            Console.WriteLine($"  customer_id={cust["customer_id"]} " +
                              $"name={cust["customer_name"]} salesrep_id={cust["salesrep_id"]}");
        }
        else
        {
            Console.WriteLine("  Customer NOT FOUND");
        }
    }

    private static JObject BuildCustomerPayload()
    {
        JObject Row(params (string Name, string Value)[] edits) => new JObject
        {
            ["Edits"] = new JArray(edits.Select(e => Edit(e.Name, e.Value))),
            ["RelativeDateEdits"] = new JArray(),
        };

        return new JObject
        {
            ["Name"] = "Customer",
            ["UseCodeValues"] = false,
            ["Transactions"] = new JArray
            {
                new JObject
                {
                    ["Status"] = "New",
                    ["DataElements"] = new JArray
                    {
                        new JObject
                        {
                            ["Name"] = "TABPAGE_1.tp_1_dw_1",
                            ["Type"] = "Form",
                            ["Keys"] = new JArray(),
                            ["Rows"] = new JArray
                            {
                                Row(("customer_name", "ACME Industrial Supply"),
                                    ("salesrep_id", "100"),          // hard-required
                                    ("mail_address1", "123 Main St"),
                                    ("mail_city", "Des Moines"),
                                    ("mail_state", "IA"),
                                    ("mail_postal_code", "50309"),
                                    ("mail_country", "USA")),
                            },
                        },
                        new JObject
                        {
                            ["Name"] = "SHIP_TO_GENERAL.ship_to_general",
                            ["Type"] = "Form",
                            ["Keys"] = new JArray(),
                            ["Rows"] = new JArray
                            {
                                Row(("default_branch", "10")),       // required, NOT defaulted
                            },
                        },
                    },
                },
            },
        };
    }
}
