// Update a supplier's email address and central phone number.
// Mirrors docs/recipes/update-supplier-contact.md.
//
// These fields do not live on the Supplier service. supplier.supplier_id
// shares its id with an address row (address.id == supplier_id), and the
// email and central phone that purchasing documents surface come from
// address.email_address and address.central_phone_number. The Address
// service is also the smaller write surface: ~9 KB of definition against
// ~70 KB for Supplier, keyed on nothing but the address id.

using System.Text;
using Newtonsoft.Json.Linq;
using P21Examples.Common;
using static P21Examples.Recipes.RecipeHelpers;

namespace P21Examples.Recipes;

public static class UpdateSupplierContact
{
    private const string SupplierId = "10050";          // address.id == supplier_id
    private const string EmailAddress = "orders@example.com";
    private const string CentralPhone = "319-555-0100";

    // Phone tab: email + central phone/fax.
    private const string ContactTab = "TABPAGE_3.tp_3_dw_3";

    public static async Task RunAsync()
    {
        Console.WriteLine("Recipe - Update Supplier Contact Info");
        Console.WriteLine(new string('=', 60));

        using var client = await P21Client.CreateAsync();

        Console.WriteLine("\nBefore:");
        await PrintContactAsync();

        var payload = BuildPayload();
        PrintPayload("Payload", payload);
        if (!ConfirmExecute())
            return;

        var result = await client.Transaction.CreateAsync(payload);
        if (!CheckResult(result))
            return;

        // IgnoreDisabled can report Succeeded and write nothing --
        // docs/14-Breaking-Changes.md entry 8. The read-back is the proof.
        Console.WriteLine("\nAfter (read-back is the only proof):");
        await PrintContactAsync();
    }

    private static JObject BuildPayload() => new()
    {
        ["Name"] = "Address",
        ["UseCodeValues"] = false,
        // Several Address columns are read-only once the record exists.
        ["IgnoreDisabled"] = true,
        ["Transactions"] = new JArray
        {
            new JObject
            {
                // "New" is the upsert shape, and the only value the enum accepts.
                ["Status"] = "New",
                ["DataElements"] = new JArray
                {
                    new JObject
                    {
                        ["Name"] = "TABPAGE_1.tp_1_dw_1", ["Type"] = "Form",
                        ["Keys"] = new JArray { "id" },
                        ["Rows"] = new JArray { new JObject {
                            ["Edits"] = new JArray { KeyEdit("id", SupplierId) },
                            ["RelativeDateEdits"] = new JArray() } },
                    },
                    new JObject
                    {
                        // IgnoreIfEmpty leaves the stored value alone when the
                        // edit is blank -- this payload can add or replace
                        // contact info but can never blank it.
                        ["Name"] = ContactTab, ["Type"] = "Form",
                        ["Keys"] = new JArray(),
                        ["Rows"] = new JArray { new JObject {
                            ["Edits"] = new JArray
                            {
                                OptionalEdit("email_address", EmailAddress),
                                OptionalEdit("address_central_phone_number", CentralPhone),
                            },
                            ["RelativeDateEdits"] = new JArray() } },
                    },
                },
            },
        },
    };

    private static JObject KeyEdit(string name, string value) => new()
    {
        ["Name"] = name, ["Value"] = value, ["IgnoreIfEmpty"] = false,
    };

    private static JObject OptionalEdit(string name, string value) => new()
    {
        ["Name"] = name, ["Value"] = value, ["IgnoreIfEmpty"] = true,
    };

    private static async Task PrintContactAsync()
    {
        var (http, uiServer, _) = await CreateRawClientAsync();
        var request = new JObject
        {
            ["ServiceName"] = "Address",
            ["TransactionStates"] = new JArray { new JObject {
                ["DataElementName"] = "TABPAGE_1.tp_1_dw_1",
                ["Keys"] = new JArray { new JObject {
                    ["Name"] = "id", ["Value"] = SupplierId } } } },
        };
        var response = await http.PostAsync(
            $"{uiServer}/api/v2/transaction/get",
            new StringContent(request.ToString(), Encoding.UTF8, "application/json"));
        response.EnsureSuccessStatusCode();

        var body = JObject.Parse(await response.Content.ReadAsStringAsync());
        foreach (var element in body["Transactions"]![0]!["DataElements"]!)
        {
            if ((string?)element["Name"] != ContactTab)
                continue;
            var rows = element["Rows"];
            if (rows is null || !rows.Any())
                break;
            var edits = rows[0]!["Edits"]!.ToDictionary(
                e => (string)e["Name"]!, e => (string?)e["Value"] ?? "");
            edits.TryGetValue("email_address", out var email);
            edits.TryGetValue("address_central_phone_number", out var phone);
            Console.WriteLine($"  email_address                = '{email}'");
            Console.WriteLine($"  address_central_phone_number = '{phone}'");
            return;
        }
        Console.WriteLine($"  (no address record found for id {SupplierId})");
    }
}
