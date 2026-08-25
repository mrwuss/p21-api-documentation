// Recipe: Reassign a Customer and Ship-To Salesrep
// Docs:   docs/recipes/reassign-salesrep.md
//
// Move a customer and its default ship-to from one salesrep to another
// (services: Customer, ShipTo), then read both grids back over OData.
//
// Key rules (all verified live — see the recipe page):
//   - The two grids delete differently. CUSTOMERSALESREP.customersalesrep
//     has no delete_flag; it removes rows with row_status_flag = "Delete".
//     TABPAGE_SALESREP.tabpage_salesrep on ShipTo does have delete_flag.
//   - Send the LABEL, not the code. row_status_flag is typed Long and the
//     column stores code_p21 integers (704 Active / 700 Delete), but under
//     UseCodeValues = false both "700" and "704" are rejected.
//   - Promote before you delete, in that row order. P21 refuses to leave a
//     record without a primary salesrep, so deleting the outgoing rep first
//     fails the whole transaction.
//   - Both deletes are soft: the old rows survive at row_status_flag 700 /
//     delete_flag 'Y'. Filter them out on every read.
//   - The OData key columns are Edm.Decimal — quoting the value 404s.

using Newtonsoft.Json.Linq;
using P21Examples.Common;
using static P21Examples.Recipes.RecipeHelpers;

namespace P21Examples.Recipes;

public static class ReassignSalesrep
{
    // Generic placeholders — substitute your own values.
    private const string CompanyId = "ACME";
    private const string CustomerId = "100198";
    private const string ShipToId = "100198";     // DEFAULT ship-to: address_id == customer_id
    private const string OldSalesrepId = "100";
    private const string NewSalesrepId = "200";

    private const int RowStatusActive = 704;      // code_p21 label "Active"

    public static async Task RunAsync()
    {
        Console.WriteLine("Recipe - Reassign a Customer and Ship-To Salesrep");
        Console.WriteLine(new string('=', 60));

        using var client = await P21Client.CreateAsync();

        var customerPayload = BuildCustomerPayload();
        var shipToPayload = BuildShipToPayload();
        PrintPayload("Customer payload", customerPayload);
        PrintPayload("ShipTo payload", shipToPayload);

        if (!ConfirmExecute())
            return;

        // ------------------------------------------------------------------
        // Write — both halves, customer first
        // ------------------------------------------------------------------
        Console.WriteLine("\nCustomer:");
        if (!CheckResult(await client.Transaction.CreateAsync(customerPayload)))
            return;

        Console.WriteLine("ShipTo:");
        if (!CheckResult(await client.Transaction.CreateAsync(shipToPayload)))
            return;

        // ------------------------------------------------------------------
        // Verify: read both grids back via OData
        // The outgoing rep's rows are still here — soft-deleted, not removed.
        // ------------------------------------------------------------------
        Console.WriteLine("\nVerify via OData:");
        Console.WriteLine(new string('-', 50));

        var customerRows = (JArray)(await client.OData.QueryAsync(
            "customer_salesrep", filter: $"customer_id eq {CustomerId}"))["value"]!;
        foreach (var row in customerRows)
        {
            var status = row["row_status_flag"]?.Value<int>();
            var state = status == RowStatusActive ? "active" : "deleted";
            Console.WriteLine($"  customer: salesrep_id={row["salesrep_id"]} " +
                              $"primary={row["primary_salesrep_flag"]} " +
                              $"row_status_flag={status} ({state})");
        }

        var shipToRows = (JArray)(await client.OData.QueryAsync(
            "ship_to_salesrep", filter: $"ship_to_id eq {ShipToId}"))["value"]!;
        foreach (var row in shipToRows)
        {
            var deleted = row["delete_flag"]?.ToString() == "Y";
            Console.WriteLine($"  ship-to:  salesrep_id={row["salesrep_id"]} " +
                              $"primary={row["primary_salesrep"]} " +
                              $"delete_flag={row["delete_flag"]} " +
                              $"({(deleted ? "deleted" : "active")})");
        }
    }

    private static JObject Row(params (string Name, string Value)[] edits) => new JObject
    {
        ["Edits"] = new JArray(edits.Select(e => Edit(e.Name, e.Value))),
        ["RelativeDateEdits"] = new JArray(),
    };

    private static JObject BuildCustomerPayload() => new JObject
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
                            Row(("company_id", CompanyId),
                                ("customer_id", CustomerId),
                                ("salesrep_id", NewSalesrepId)),
                        },
                    },
                    new JObject
                    {
                        ["Name"] = "CUSTOMERSALESREP.customersalesrep",
                        ["Type"] = "List",
                        ["Keys"] = new JArray { "salesrep_id" },
                        // Promote first, THEN delete — the reverse order fails with
                        // "This salesrep is set up as the primary salesrep ...".
                        ["Rows"] = new JArray
                        {
                            Row(("salesrep_id", NewSalesrepId),
                                ("primary_salesrep_flag", "ON"),
                                ("commission_percentage", "100")),
                            Row(("salesrep_id", OldSalesrepId),
                                ("row_status_flag", "Delete")),   // the label, never 700
                        },
                    },
                },
            },
        },
    };

    private static JObject BuildShipToPayload() => new JObject
    {
        ["Name"] = "ShipTo",
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
                        ["Name"] = "TABPAGE_1.shiptomain",
                        ["Type"] = "Form",
                        ["Keys"] = new JArray(),
                        // Omit customer_id on a DEFAULT ship-to — it is disabled there.
                        ["Rows"] = new JArray
                        {
                            Row(("company_id", CompanyId),
                                ("address_id", ShipToId)),
                        },
                    },
                    new JObject
                    {
                        ["Name"] = "TABPAGE_SALESREP.tabpage_salesrep",
                        ["Type"] = "List",
                        ["Keys"] = new JArray { "salesrep_id" },
                        ["Rows"] = new JArray
                        {
                            Row(("salesrep_id", NewSalesrepId),
                                ("primary_salesrep", "ON")),
                            Row(("salesrep_id", OldSalesrepId),
                                ("delete_flag", "ON")),           // this grid DOES have one
                        },
                    },
                },
            },
        },
    };
}
