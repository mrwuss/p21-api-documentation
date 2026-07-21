// Recipe: Create a Requisition Purchase Order
// Docs:   docs/recipes/create-requisition-po.md
//
// Create a requisition PO — P21's internal / not-for-resale purchasing type —
// in one stateless Transaction API call (service: RequisitionPurchaseOrder).
// Result: a PO with po_hdr.po_type = 'R'.
//
// Key rules (all verified live — see the recipe page):
//   - Type is chosen by the SERVICE, not a field: po_hdr_po_type is disabled
//     on the standard PurchaseOrder service.
//   - vendor_supplier_id goes on the HEADER; omitting it fails at the line
//     with a misleading "A supplier ID must be entered ... Column: item_id".
//   - vendor_id != supplier_id (different records).
//   - Only requisition items (inv_loc.requisition = 'Y') may be purchased.
//   - HTTP 200 is not success; the generated po_no comes back in the result
//     rows of TABPAGE_1.tp_1_dw_1.

using Newtonsoft.Json.Linq;
using P21Examples.Common;
using static P21Examples.Recipes.RecipeHelpers;

namespace P21Examples.Recipes;

public static class CreateRequisitionPo
{
    public static async Task RunAsync()
    {
        Console.WriteLine("Recipe - Create a Requisition Purchase Order");
        Console.WriteLine(new string('=', 60));

        using var client = await P21Client.CreateAsync();

        var payload = BuildRequisitionPoPayload();
        PrintPayload("RequisitionPurchaseOrder payload", payload);

        if (!ConfirmExecute())
            return;

        // ------------------------------------------------------------------
        // Write
        // ------------------------------------------------------------------
        var result = await client.Transaction.CreateAsync(payload);
        if (!CheckResult(result))
            return;

        // The generated po_no comes back in the TABPAGE_1.tp_1_dw_1 rows
        var poNo = (result.Raw?.SelectTokens(
                "$.Results.Transactions[?(@.Status == 'Passed')]" +
                ".DataElements[?(@.Name == 'TABPAGE_1.tp_1_dw_1')]" +
                ".Rows[*].Edits[?(@.Name == 'po_no')].Value")
            ?? Enumerable.Empty<JToken>()).FirstOrDefault()?.ToString();

        Console.WriteLine($"\nCreated po_no: {poNo}");
        if (string.IsNullOrEmpty(poNo))
            return;

        // ------------------------------------------------------------------
        // Verify: read the PO back and confirm po_type == 'R'
        // ------------------------------------------------------------------
        Console.WriteLine("\nVerify via OData:");
        Console.WriteLine(new string('-', 50));

        var hdrRows = (JArray)(await client.OData.QueryAsync(
            "po_hdr", filter: $"po_no eq {poNo}"))["value"]!;
        if (hdrRows.Count > 0)
        {
            var poType = hdrRows[0]["po_type"]?.ToString();
            var flag = poType == "R" ? "OK" : "WARNING: expected R";
            Console.WriteLine($"  po_no={hdrRows[0]["po_no"]} po_type={poType} [{flag}] " +
                              $"vendor_id={hdrRows[0]["vendor_id"]}");
        }
        else
        {
            Console.WriteLine("  PO header NOT FOUND");
        }

        var lineRows = (JArray)(await client.OData.QueryAsync(
            "po_line", filter: $"po_no eq {poNo}"))["value"]!;
        Console.WriteLine($"  Lines: {lineRows.Count} (expected 1)");
    }

    private static JObject BuildRequisitionPoPayload()
    {
        JObject Row(params (string Name, string Value)[] edits) => new JObject
        {
            ["Edits"] = new JArray(edits.Select(e => Edit(e.Name, e.Value))),
            ["RelativeDateEdits"] = new JArray(),
        };

        return new JObject
        {
            ["Name"] = "RequisitionPurchaseOrder",
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
                                Row(("location_id", "10"),
                                    ("vendor_id", "21445"),
                                    ("vendor_supplier_id", "22132")),   // header, NOT the line
                            },
                        },
                        new JObject
                        {
                            ["Name"] = "TABPAGE_17.tp_17_dw_17",
                            ["Type"] = "List",
                            ["Keys"] = new JArray(),
                            ["Rows"] = new JArray
                            {
                                Row(("item_id", "WIDGET-001"),           // must be a requisition item
                                    ("unit_quantity", "10")),
                            },
                        },
                    },
                },
            },
        };
    }
}
