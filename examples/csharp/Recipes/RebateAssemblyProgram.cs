// Recipe: Rebate-Tracked Assembly Program Runbook
// Docs:   docs/recipes/rebate-assembly-program.md
//
// Runs the API-reachable steps for one assembled part, reading each step
// back before the next:
//
//   1. Catalog: assemblies the customer ordered that are not on the contract (OData)
//   2. Fix the BOM: a component quantity and/or a component removal  (Transaction Assembly)
//   3. Create the rebate vendor, Track Rebates ON                    (Transaction Vendor)
//   4. Make it the primary supplier at the SHIP-FROM location        (Transaction Item, x2)
//   5. Contract line: price, Value commission cost, Value OTHER cost (Transaction JobContractPricing)
//      + the ship-to on the contract's Customer/Ship To grid
//   6. Acceptance test: order (unit_price blank) -> pick -> ship -> invoice,
//      then invoice_line and vendor_rebate                           (Transaction + Interactive)
//
// The rebate schedule, pricing rule and supplier claim are business inputs;
// step 6's GL check is read by a person. Step 6 needs the assembled part in
// stock at the ship-from location.

using Newtonsoft.Json.Linq;
using static P21Examples.Recipes.RunbookSteps;

namespace P21Examples.Recipes;

public static class RebateAssemblyProgram
{
    public static async Task RunAsync()
    {
        Console.WriteLine("Runbook - Rebate-Tracked Assembly Program");
        Console.WriteLine(new string('=', 60));
        Console.WriteLine("Values (Enter keeps the placeholder):");
        var company = Ask("Company ID", "ACME");
        var customer = Ask("Customer ID", "CUST-100");
        var shipTo = Ask("Ship-to ID", "CUST-100");
        var contact = Ask("Contact ID", "300");
        var taker = Ask("Taker", "JSMITH");
        var jobNo = Ask("Contract job_no", "JOB-001");
        var contractNo = Ask("Contract contract_no", "CONTRACT-001");
        var shipFrom = Ask("Ship-from (source) location", "30");
        var item = Ask("Assembled part", "ASSY-001");
        var bomFixes = Ask("Step 2 component fixes COMP=QTY;COMP=- (- = remove; - alone = none)", "-");
        var vendorName = Ask("Rebate vendor name", "Example Rebate Vendor");
        var apAccount = Ask("AP account (no dash)", "2222200");
        var rebateAccount = Ask("Rebate receivable account", "1111100");
        var allowanceAccount = Ask("Rebate allowance account", "3333300");
        var terms = Ask("Terms (description)", "Net 30 Days");
        var price = Ask("Contract price", "45.00");
        var trueCost = Ask("Commission cost (Value)", "30.60");
        var rebatedCost = Ask("Other cost (Value) = rebated cost", "24.00");
        var since = Ask("Step 1 window start", DaysFromToday(-365));

        List<(string Comp, string? Qty)> fixes = bomFixes == "-"
            ? new List<(string Comp, string? Qty)>()
            : bomFixes.Split(';').Select(p => p.Split('=', 2))
                .Select(p => (p[0].Trim(), p[1].Trim() == "-" ? null : (string?)p[1].Trim())).ToList();

        Console.WriteLine($"\nStep 1 (OData): {customer}'s orders since {since} -> ordered items with an " +
                          "assembly_hdr and no job_price_line on the contract.");
        if (fixes.Count > 0)
            RecipeHelpers.PrintPayload("Step 2 Assembly payload", BuildBomPayload(item, fixes));
        RecipeHelpers.PrintPayload("Step 3 Vendor payload",
            BuildVendorPayload(company, vendorName, apAccount, terms, rebateAccount, allowanceAccount));
        var (demoInsert, demoFlip) = BuildSupplierPayloads(item, shipFrom, "{vendor_id}");
        RecipeHelpers.PrintPayload("Step 4a supplier row insert", demoInsert);
        RecipeHelpers.PrintPayload("Step 4b flip to primary", demoFlip);
        RecipeHelpers.PrintPayload("Step 5 JobContractPricing payload",
            BuildContractPayload(company, contractNo, jobNo, customer, shipTo, item, price, trueCost, rebatedCost));

        if (!RecipeHelpers.ConfirmExecute())
            return;

        using var rb = await Runbook.CreateAsync();
        var itemUid = await rb.ItemUidAsync(item);
        var hdrUid = (await rb.OneAsync("job_price_hdr", $"contract_no eq '{contractNo}' and job_no eq '{jobNo}'",
            "job_price_hdr_uid"))["job_price_hdr_uid"]!.ToString();

        Console.WriteLine("\nStep 1 - Catalog what the customer buys (OData, read-only)");
        var onContract = (await rb.ODataAsync("job_price_line", $"job_price_hdr_uid eq {hdrUid}", "inv_mast_uid"))
            .Select(r => r["inv_mast_uid"]!.ToString()).ToHashSet();
        var orders = await rb.ODataAsync("oe_hdr", $"customer_id eq {customer} and order_date ge {since}T00:00:00Z",
            "order_no", top: 200);
        var seen = new HashSet<string>();
        foreach (var o in orders)
            foreach (var l in await rb.ODataAsync("oe_line", $"order_no eq '{o["order_no"]}' and delete_flag eq 'N'", "inv_mast_uid"))
                seen.Add(l["inv_mast_uid"]!.ToString());
        var gaps = new List<string>();
        foreach (var uid in seen.Except(onContract))
            if ((await rb.ODataAsync("assembly_hdr", $"inv_mast_uid eq {uid}", "inv_mast_uid")).Count > 0)
                gaps.Add((await rb.OneAsync("inv_mast", $"inv_mast_uid eq {uid}", "item_id"))["item_id"]!.ToString());
        Console.WriteLine($"    {orders.Count} order(s) since {since}; {seen.Count} item(s) ordered; " +
                          $"assemblies not on the contract: {(gaps.Count == 0 ? "none" : string.Join(", ", gaps))}");

        if (fixes.Count > 0)
        {
            Console.WriteLine("\nStep 2 - Fix the BOM (Transaction Assembly)");
            await rb.TransactionAsync(BuildBomPayload(item, fixes), "Assembly edit");
            foreach (var row in await rb.ODataAsync("assembly_line", $"inv_mast_uid eq {itemUid}",
                         "component_inv_mast_uid,quantity,unit_of_measure,delete_flag"))
            {
                var comp = (await rb.OneAsync("inv_mast", $"inv_mast_uid eq {row["component_inv_mast_uid"]}", "item_id"))
                    ["item_id"]!.ToString();
                Console.WriteLine($"    {comp}: quantity {Fmt(Num(row["quantity"]))} {row["unit_of_measure"]} " +
                                  $"delete_flag {row["delete_flag"]}");
                foreach (var (fixComp, fixQty) in fixes.Where(f => f.Comp == comp))
                {
                    if (fixQty == null) Check($"{comp} delete_flag", row["delete_flag"], "Y");
                    else Check($"{comp} quantity", Fmt(Num(row["quantity"])), Fmt(Num(fixQty)));
                }
            }
        }

        Console.WriteLine("\nStep 3 - Create the rebate vendor (Transaction Vendor)");
        var result = await rb.TransactionAsync(
            BuildVendorPayload(company, vendorName, apAccount, terms, rebateAccount, allowanceAccount), "Vendor");
        var vendorId = ResultValue(result, "TABPAGE_1.tp_1_dw_1", "id")!;
        var vendor = await rb.OneAsync("vendor", $"vendor_id eq {vendorId}", "vendor_id,track_rebates");
        Check("vendor.track_rebates", vendor["track_rebates"], "Y");
        var link = await rb.OneAsync("vendor_supplier", $"vendor_id eq {vendorId}", "supplier_id,primary_vendor");
        var supplierId = link["supplier_id"]!.ToString();
        Console.WriteLine($"    vendor {vendorId}: same-ID supplier {supplierId} (primary_vendor {link["primary_vendor"]})");

        Console.WriteLine($"\nStep 4 - Primary supplier at ship-from location {shipFrom} (Transaction Item)");
        var (insert, flip) = BuildSupplierPayloads(item, shipFrom, supplierId);
        await rb.TransactionAsync(insert, "Location supplier row");
        await rb.TransactionAsync(flip, "Flip to primary");
        var loc = await rb.OneAsync("inv_loc", $"inv_mast_uid eq {itemUid} and location_id eq {shipFrom}",
            "primary_supplier_id,qty_on_hand");
        Check("inv_loc.primary_supplier_id", loc["primary_supplier_id"], supplierId);

        Console.WriteLine("\nStep 5 - Price and cost the contract line (Transaction JobContractPricing)");
        await rb.TransactionAsync(
            BuildContractPayload(company, contractNo, jobNo, customer, shipTo, item, price, trueCost, rebatedCost),
            "Contract line");
        var line = await rb.OneAsync("job_price_line", $"job_price_hdr_uid eq {hdrUid} and inv_mast_uid eq {itemUid}",
            "price,commission_cost_value,other_cost_value");
        Check("job_price_line.price", Fmt(Num(line["price"])), Fmt(Num(price)));
        Check("job_price_line.other_cost_value", Fmt(Num(line["other_cost_value"])), Fmt(Num(rebatedCost)));
        await rb.OneAsync("job_price_customer_shipto",
            $"job_price_hdr_uid eq {hdrUid} and customer_id eq {customer} and ship_to_id eq {shipTo}", "customer_id");

        Console.WriteLine("\nStep 6 - Acceptance test: order, pick, ship, invoice");
        if (Num(loc["qty_on_hand"]) < 1)
            throw new InvalidOperationException($"{item} has no stock at {shipFrom} — build or receive one first");
        result = await rb.TransactionAsync(BuildOrderPayload(customer, shipTo, contact, shipFrom, shipFrom,
            Today, DaysFromToday(1), $"REBATE-TEST-{vendorId}", taker,
            new[] { (item, "1", (string?)null) }), "Order");          // unit_price blank: the contract binds
        var orderNo = ResultValue(result, "TABPAGE_1.order", "order_no")!;
        var ol = await rb.OneAsync("oe_line", $"order_no eq '{orderNo}' and inv_mast_uid eq {itemUid}",
            "line_no,job_price_hdr_uid,supplier_id,other_cost,assembly");
        Console.WriteLine($"    order {orderNo} line {ol["line_no"]}: assembly {ol["assembly"]} " +
                          $"supplier {ol["supplier_id"]} other_cost {ol["other_cost"]}");
        Check("oe_line.job_price_hdr_uid (bound at entry)", ol["job_price_hdr_uid"], hdrUid);
        Check("oe_line.supplier_id", ol["supplier_id"], supplierId);
        var invoiceNo = await ShipAndInvoiceAsync(rb, await PrintPickTicketAsync(rb, orderNo));

        Console.WriteLine("\nVerify - the invoice and the rebate");
        var lines = await PrintInvoiceAsync(rb, invoiceNo);
        var parent = lines.First(x => x["item_id"]?.ToString() == item && x["invoice_line_uid_parent"]?.ToString() == "0");
        Check("invoice_line.unit_price = contract price", Fmt(Num(parent["unit_price"])), Fmt(Num(price)));
        Check("invoice_line.cogs_amount = contract other cost", Fmt(Num(parent["cogs_amount"])), Fmt(Num(rebatedCost)));
        var rebate = await rb.OneAsync("vendor_rebate",
            $"invoice_no eq '{invoiceNo}' and invoice_line_uid eq {parent["invoice_line_uid"]}",
            "vendor_id,base_cost,after_rebate_cost,rebate_due");
        Console.WriteLine($"    vendor_rebate: base_cost {rebate["base_cost"]} after_rebate_cost " +
                          $"{rebate["after_rebate_cost"]} rebate_due {rebate["rebate_due"]}");
        Check("vendor_rebate.vendor_id", rebate["vendor_id"], vendorId);
        Check("vendor_rebate.after_rebate_cost", Fmt(Num(rebate["after_rebate_cost"])), Fmt(Num(rebatedCost)));
        Console.WriteLine("\nRead the invoice's GL by hand: Sales Journal COGS at moving average, then a " +
                          "Rebate Journal entry for the difference.");
        Console.WriteLine("\nRunbook complete.");
    }

    /// <summary>Step 2: keyed Status "New" edits, no IgnoreDisabled. Changes the item for EVERY customer.</summary>
    private static JObject BuildBomPayload(string item, List<(string Comp, string? Qty)> fixes) =>
        Payload("Assembly", false,
            Element("TABPAGE_1.assemblyhdr", "Form", new[] { "inv_mast_item_id" }, new[] { Edit("inv_mast_item_id", item) }),
            Element("TABPAGE_17.tp_17_dw_17", "List", new[] { "item_id_service_labor_id" },
                fixes.Select(f => new[]
                {
                    Edit("item_id_service_labor_id", f.Comp),
                    f.Qty == null ? Edit("delete_flag", "ON") : Edit("quantity", f.Qty),
                }).ToArray()));

    /// <summary>Step 3: vendor ON, Track Rebates ON, terms by description, no
    /// currency, no supplier tab; id left out so P21 numbers it.</summary>
    private static JObject BuildVendorPayload(
        string company, string name, string apAccount, string terms, string rebateAccount, string allowanceAccount) =>
        Payload("Vendor", false,
            Element("TABPAGE_1.tp_1_dw_1", "Form", new[] { "company_id", "id" }, new[]
            {
                Edit("company_id", company), Edit("vendor", "ON"), Edit("name", name),
                Edit("mail_address1", "100 Main St"), Edit("mail_city", "Springfield"),
                Edit("mail_state", "IL"), Edit("mail_postal_code", "62701"),
                Edit("ap_account_no", apAccount), Edit("default_terms_id", terms), Edit("track_rebates", "ON"),
            }),
            Element("REBATE_ACCOUNTS.d_vendor_rebate_accounts", "Form", Array.Empty<string>(), new[]
            {
                Edit("rebate_account_no", rebateAccount), Edit("rebate_allowance_account_no", allowanceAccount),
            }));

    /// <summary>Step 4: insert the location supplier row (both keys + IgnoreDisabled), then flip it primary.</summary>
    private static (JObject Insert, JObject Flip) BuildSupplierPayloads(string item, string location, string supplierId)
    {
        JObject ItemPayload(JObject detail, bool ignore) => Payload("Item", ignore,
            Element("TABPAGE_1.tp_1_dw_1", "Form", new[] { "item_id" }, new[] { Edit("item_id", item) }),
            Element("TABPAGE_17.invloclist", "List", new[] { "location_id" }, new[] { Edit("location_id", location) }),
            detail);
        return (
            ItemPayload(Element("SUPPLIER_X_LOCATION.supplier_x_location", "List", new[] { "location_id", "supplier_id" },
                new[] { Edit("location_id", location), Edit("supplier_id", supplierId) }), true),
            ItemPayload(Element("SUPPLIER_X_LOCATION.supplier_x_location", "List", new[] { "supplier_id" },
                new[] { Edit("supplier_id", supplierId), Edit("primary_supplier", "ON") }), false));
    }

    /// <summary>Step 5: ship-to on the grid; pricing_method BEFORE price; both costs type Value.</summary>
    private static JObject BuildContractPayload(
        string company, string contractNo, string jobNo, string customer, string shipTo, string item,
        string price, string trueCost, string rebatedCost) =>
        Payload("JobContractPricing", true,
            Element("FORM.d_dw_job_price_hdr", "Form", Array.Empty<string>(), new[]
                { Edit("company_id", company), Edit("contract_no", contractNo), Edit("job_no", jobNo) }),
            Element("CUSTOMER_SHIP_TO.customer_ship_to", "List", new[] { "customer_id", "ship_to_id" },
                new[] { Edit("customer_id", customer), Edit("ship_to_id", shipTo) }),
            Element("JOBPRICELINE.jobpriceline", "List", new[] { "item_id" }, new[]
                { Edit("item_id", item), Edit("uom", "EA"), Edit("pricing_method", "Price"), Edit("price", price) }),
            Element("JOBPRICECOST.jobpricecost", "Form", new[] { "item_id" }, new[]
            {
                Edit("item_id", item),
                Edit("commission_cost_type_cd", "Value"), Edit("commission_cost_value", trueCost),
                Edit("other_cost_type_cd", "Value"), Edit("other_cost_value", rebatedCost),
            }));
}
