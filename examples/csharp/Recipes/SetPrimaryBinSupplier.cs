// Recipe: Set an Item's Primary Bin or Primary Supplier at a Location
// Docs:   docs/recipes/set-primary-bin-supplier.md
//
// Update an item's primary supplier (or primary bin) for one stocking
// location via the Item service's nested Form -> List -> detail pattern —
// with a MANDATORY read-back, because the primary-supplier write can
// silently no-op.
//
// Key rules (all verified live — see the recipe page):
//   - Silent no-op: the target supplier must already have a location-level
//     row (inventory_supplier_x_loc) at that location, or the transaction
//     returns Succeeded = 1 and nothing flips. Always verify.
//   - Write the flag, read the id: primary_supplier maps to
//     inventory_supplier_x_loc.primary_supplier; verify against
//     inv_loc.primary_supplier_id.
//   - Status "New" with populated Keys updates the existing keyed record.
//   - "Item Issues Detected" popups need the Interactive API fallback.

using Newtonsoft.Json.Linq;
using P21Examples.Common;
using static P21Examples.Recipes.RecipeHelpers;

namespace P21Examples.Recipes;

public static class SetPrimaryBinSupplier
{
    private const string ItemId = "WIDGET-001";
    private const string LocationId = "10";
    private const string SupplierId = "10050";

    public static async Task RunAsync()
    {
        Console.WriteLine("Recipe - Set Primary Bin / Primary Supplier (Item)");
        Console.WriteLine(new string('=', 60));

        using var client = await P21Client.CreateAsync();

        JObject Element(string name, string type, string key,
            params (string Name, string Value)[] edits) => new JObject
        {
            ["Name"] = name, ["Type"] = type, ["Keys"] = new JArray(key),
            ["Rows"] = new JArray(new JObject
            {
                ["Edits"] = new JArray(edits.Select(e => Edit(e.Name, e.Value))),
            }),
        };

        // Primary supplier: Form -> List -> List.
        var payload = new JObject
        {
            ["Name"] = "Item",
            ["UseCodeValues"] = false,
            ["Transactions"] = new JArray(new JObject
            {
                ["Status"] = "New", // updates the keyed record; does not create a new item
                ["DataElements"] = new JArray
                {
                    Element("TABPAGE_1.tp_1_dw_1", "Form", "item_id", ("item_id", ItemId)),
                    Element("TABPAGE_17.invloclist", "List", "location_id",
                        ("location_id", LocationId)),
                    Element("SUPPLIER_X_LOCATION.supplier_x_location", "List", "supplier_id",
                        ("supplier_id", SupplierId), ("primary_supplier", "ON")),
                },
            }),
        };

        PrintPayload("Primary-supplier payload", payload);
        Console.WriteLine(
            "\nPrimary-BIN variant: swap the third element for\n" +
            "  TABPAGE_18.inv_loc_detail (Form, key location_id) with edits\n" +
            "  location_id + bin, then verify inv_loc.primary_bin the same way.");

        if (!ConfirmExecute())
            return;

        // ------------------------------------------------------------------
        // Write
        // ------------------------------------------------------------------
        var result = await client.Transaction.CreateAsync(payload);
        CheckResult(result); // watch for 'Unexpected response window: Item Issues Detected'

        // ------------------------------------------------------------------
        // MANDATORY verification — a silent no-op still reports Succeeded = 1.
        // Write target is the inventory_supplier_x_loc flag;
        // READ inv_loc.primary_supplier_id.
        // ------------------------------------------------------------------
        Console.WriteLine("\nVerify via OData (mandatory):");
        Console.WriteLine(new string('-', 50));

        var mastRows = (JArray)(await client.OData.QueryAsync(
            "inv_mast",
            select: "inv_mast_uid",
            filter: $"item_id eq '{ItemId}'"))["value"]!;
        if (mastRows.Count == 0)
        {
            Console.WriteLine($"  Item {ItemId} not found in inv_mast");
            return;
        }
        var invMastUid = mastRows[0]["inv_mast_uid"]!.ToString();

        var locRows = (JArray)(await client.OData.QueryAsync(
            "inv_loc",
            select: "primary_supplier_id",
            filter: $"inv_mast_uid eq {invMastUid} and location_id eq {LocationId}"))["value"]!;
        if (locRows.Count == 0)
        {
            Console.WriteLine($"  No inv_loc row for item {ItemId} at location {LocationId}");
            return;
        }
        var actual = locRows[0]["primary_supplier_id"]?.ToString();

        if (actual == SupplierId)
            Console.WriteLine($"  VERIFIED: primary_supplier_id = {actual}");
        else
            // Most likely cause: no inventory_supplier_x_loc row at this location.
            // Add the location supplier row first, then set the flag again.
            Console.WriteLine(
                $"  SILENT NO-OP: primary_supplier_id is {actual}, expected {SupplierId}");
    }
}
