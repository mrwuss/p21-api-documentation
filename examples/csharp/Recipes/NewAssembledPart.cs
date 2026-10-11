// Recipe: New Assembled Part Runbook — Item -> BOM -> Job Contract -> Production Order
// Docs:   docs/recipes/new-assembled-part.md
//
// Runs the page step by step for a brand-new part copied from a "template"
// part, reading each step back before the next:
//
//   0. Price it: roll up the copied BOM's component cost, apply the rule    (OData)
//   1. Item + first location                                   (Inventory REST create)
//   2. Every other location, one POST each                     (Transaction Item)
//   3. BOM (template's physical components) + build-to-stock flags (Transaction Assembly)
//   4. The contract line: price, then a Value commission cost  (Transaction JobContractPricing)
//   5. The first build-to-stock production order               (Interactive ProductionOrder)
//
// Step 1 uses the Inventory REST create: on the test tenant every Units of
// Measure column in the Interactive Item window is disabled for the API
// user's role, so that path could not save a new item — see the page.
// After step 5, run the production order with ProductionOrderRunbook.

using System.Globalization;
using Newtonsoft.Json.Linq;
using static P21Examples.Recipes.RunbookSteps;

namespace P21Examples.Recipes;

public static class NewAssembledPart
{
    public static async Task RunAsync()
    {
        Console.WriteLine("Runbook - New Assembled Part: Item -> BOM -> Job Contract -> Production Order");
        Console.WriteLine(new string('=', 60));
        Console.WriteLine("Values (Enter keeps the placeholder):");
        var company = Ask("Company ID", "ACME");
        var item = Ask("New part number", "ASSY-002").ToUpperInvariant();  // the API will not uppercase it
        var description = Ask("Description (max 40)", "Assembly, Example, 2-Port");
        var template = Ask("Template part (known-good BOM)", "ASSY-001");
        var supplier = Ask("Supplier ID", "SUP-100");
        var division = Ask("Division ID", supplier);
        var productGroup = Ask("Product group", "PG-01");
        var salesLocation = Ask("Step 1 location", "10");
        var otherLocations = Ask("Other locations, comma-separated", "20,30").Split(',').Select(s => s.Trim()).ToArray();
        var makeLocation = Ask("Make location (source_loc_id)", "30");
        var partsLocation = Ask("Parts location (inventory_location_id)", "20");
        var jobNo = Ask("Contract job_no", "JOB-001");
        var contractNo = Ask("Contract contract_no", "CONTRACT-001");
        var margin = Num(Ask("Target margin", "0.30"));
        var qtyToMake = Ask("Quantity to make", "1");
        var headerFields = Ask("Production-order header fields name=value;name=value (- = none)", "-");

        Console.WriteLine($"\nStep 0 (OData): copy {template}'s physical components, cost them at location " +
                          $"{partsLocation}, price = cost / (1 - {margin}).");
        RecipeHelpers.PrintPayload("Step 1 POST {base}/api/inventory/parts/ (trailing slash)",
            BuildCreateBody(item, description, supplier, division, productGroup, salesLocation));
        foreach (var loc in otherLocations)
            RecipeHelpers.PrintPayload($"Step 2 Item payload for location {loc}",
                BuildLocationPayload(item, company, loc, productGroup, supplier));
        var (demoCreate, demoFlags) = BuildAssemblyPayloads(item, new List<(string, string, string)> { ("COMP-001", "2", "EA") });
        RecipeHelpers.PrintPayload("Step 3 Assembly create (components copied from the template)", demoCreate);
        RecipeHelpers.PrintPayload("Step 3 Assembly header flags", demoFlags);
        RecipeHelpers.PrintPayload("Step 4 JobContractPricing payload (price/cost from step 0)",
            BuildContractPayload(company, contractNo, jobNo, item, "{price}", "{cost}"));
        Console.WriteLine($"\nStep 5 (Interactive ProductionOrder): source_loc_id={makeLocation}, then " +
                          $"inventory_location_id={partsLocation}, header fields {headerFields}, " +
                          $"assembly_item_id={item}, qty_to_make={qtyToMake}, save.");

        if (!RecipeHelpers.ConfirmExecute())
            return;

        using var rb = await Runbook.CreateAsync();
        if ((await rb.ODataAsync("inv_mast", $"item_id eq '{item}'", "item_id")).Count > 0)
            throw new InvalidOperationException($"{item} already exists — pick a new part number");

        Console.WriteLine($"\nStep 0 - Price it from {template}'s BOM (OData)");
        var components = new List<(string Item, string Qty, string Uom)>();
        var cost = 0m;
        foreach (var row in await rb.ODataAsync("assembly_line",
                     $"inv_mast_uid eq {await rb.ItemUidAsync(template)} and delete_flag eq 'N'",
                     "component_inv_mast_uid,quantity,unit_of_measure,other_charge_item,sequence_number",
                     "sequence_number"))
        {
            var im = await rb.OneAsync("inv_mast", $"inv_mast_uid eq {row["component_inv_mast_uid"]}", "item_id,base_unit");
            if (row["other_charge_item"]?.ToString() == "Y")
            {
                Console.WriteLine($"    skip charge line {im["item_id"]}");
                continue;
            }
            if (row["unit_of_measure"]?.ToString() != im["base_unit"]?.ToString())  // most common copied-BOM defect
                throw new InvalidOperationException(
                    $"{im["item_id"]}: BOM unit {row["unit_of_measure"]} is not the base unit {im["base_unit"]}");
            var mac = Num((await rb.OneAsync("inv_loc",
                $"inv_mast_uid eq {row["component_inv_mast_uid"]} and location_id eq {partsLocation}",
                "moving_average_cost"))["moving_average_cost"]);
            var qty = Num(row["quantity"]);
            Console.WriteLine($"    {im["item_id"]}: {Fmt(qty)} x {Fmt(mac)} = {qty * mac:0.0000}");
            cost += qty * mac;
            components.Add((im["item_id"]!.ToString(), Fmt(qty), row["unit_of_measure"]!.ToString()));
        }
        var price = cost / (1 - margin);
        var priceText = price.ToString("0.00", CultureInfo.InvariantCulture);
        var costText = cost.ToString("0.00", CultureInfo.InvariantCulture);
        Console.WriteLine($"    component cost {costText} -> price {priceText} at margin {margin}");

        Console.WriteLine("\nStep 1 - Item and its first location (Inventory REST create)");
        var resp = await rb.Http.PostAsync($"{rb.BaseUrl}/api/inventory/parts/",   // no slash = 307
            new StringContent(BuildCreateBody(item, description, supplier, division, productGroup, salesLocation)
                .ToString(), System.Text.Encoding.UTF8, "application/json"));
        if (!resp.IsSuccessStatusCode)
            throw new InvalidOperationException(
                $"Item create failed: HTTP {(int)resp.StatusCode} {await resp.Content.ReadAsStringAsync()}");
        var created = await rb.OneAsync("inv_mast", $"item_id eq '{item}'", "item_id,item_desc,inv_mast_uid");
        var itemUid = created["inv_mast_uid"]!.ToString();
        Check("inv_mast.item_desc", created["item_desc"], description.Length > 40 ? description[..40] : description);

        Console.WriteLine("\nStep 2 - The other locations (Transaction Item, one POST per location)");
        foreach (var loc in otherLocations)
            await rb.TransactionAsync(BuildLocationPayload(item, company, loc, productGroup, supplier), $"Item location {loc}");
        var locs = await rb.ODataAsync("inv_loc", $"inv_mast_uid eq {itemUid}",
            "location_id,stockable,product_group_id,primary_supplier_id,gl_account_no", "location_id");
        foreach (var r in locs)
            Console.WriteLine($"    inv_loc {r["location_id"]}: stockable {r["stockable"]} group {r["product_group_id"]} " +
                              $"primary supplier {r["primary_supplier_id"]} GL {r["gl_account_no"]}");
        Check("locations present", string.Join(",", locs.Select(r => r["location_id"]!.ToString()).OrderBy(x => x)),
            string.Join(",", otherLocations.Append(salesLocation).Distinct().OrderBy(x => x)));

        Console.WriteLine("\nStep 3 - BOM and assembly flags (Transaction Assembly)");
        var (create, flags) = BuildAssemblyPayloads(item, components);
        await rb.TransactionAsync(create, "Assembly create");
        await rb.TransactionAsync(flags, "Assembly flags");
        var asm = await rb.OneAsync("assembly_hdr", $"inv_mast_uid eq {itemUid}",
            "production_order_processing,print_incomplete_assemblies,ship_incomplete_assemblies,auto_create_prod_order");
        Check("assembly_hdr.production_order_processing", asm["production_order_processing"], "Y");
        Check("assembly_hdr.print_incomplete_assemblies", asm["print_incomplete_assemblies"], "Y");
        Check("assembly_hdr.ship_incomplete_assemblies", asm["ship_incomplete_assemblies"], "Y");
        Check("assembly_hdr.auto_create_prod_order", asm["auto_create_prod_order"], "N");
        var asmLines = await rb.ODataAsync("assembly_line", $"inv_mast_uid eq {itemUid} and delete_flag eq 'N'", "quantity");
        Check("assembly_line rows", asmLines.Count, components.Count);

        Console.WriteLine("\nStep 4 - The contract line (Transaction JobContractPricing)");
        await rb.TransactionAsync(BuildContractPayload(company, contractNo, jobNo, item, priceText, costText), "Contract line");
        var hdr = await rb.OneAsync("job_price_hdr", $"contract_no eq '{contractNo}' and job_no eq '{jobNo}'", "job_price_hdr_uid");
        var line = await rb.OneAsync("job_price_line",
            $"job_price_hdr_uid eq {hdr["job_price_hdr_uid"]} and inv_mast_uid eq {itemUid}",
            "line_no,price,commission_cost_value");
        Check("job_price_line.price", Num(line["price"]).ToString("0.00", CultureInfo.InvariantCulture), priceText);
        Check("job_price_line.commission_cost_value",
            Num(line["commission_cost_value"]).ToString("0.00", CultureInfo.InvariantCulture), costText);

        Console.WriteLine("\nStep 5 - First production order (Interactive ProductionOrder)");
        var session = await rb.SessionAsync();
        var windowId = await session.OpenAsync("ProductionOrder");
        try
        {
            await session.ChangeAsync(windowId, "TABPAGE_1", "tp_1_dw_1", "source_loc_id", makeLocation);
            await session.ChangeAsync(windowId, "TABPAGE_1", "tp_1_dw_1", "inventory_location_id", partsLocation); // after the make location
            if (headerFields != "-")
                foreach (var pair in headerFields.Split(';'))
                {
                    var parts = pair.Split('=', 2);
                    await session.ChangeAsync(windowId, "TABPAGE_1", "tp_1_dw_1", parts[0].Trim(), parts[1].Trim());
                }
            await session.TabAsync(windowId, "TABPAGE_17");
            await session.ChangeAsync(windowId, "TABPAGE_17", "tp_17_dw_17", "assembly_item_id", item);
            await session.ChangeAsync(windowId, "TABPAGE_17", "tp_17_dw_17", "qty_to_make", qtyToMake);
            await session.SaveAsync(windowId);
        }
        finally
        {
            await session.CloseAsync(windowId);
        }
        // The window clears after the save: find the order by its line's item.
        var pol = await rb.OneAsync("prod_order_line", $"inv_mast_uid eq {itemUid}",
            "prod_order_number,qty_to_make", "prod_order_number desc");
        var poh = await rb.OneAsync("prod_order_hdr", $"prod_order_number eq {pol["prod_order_number"]}",
            "prod_order_number,source_location_id,inventory_location_id");
        Console.WriteLine($"    prod_order_number = {poh["prod_order_number"]}, qty_to_make {pol["qty_to_make"]}");
        Check("prod_order_hdr.source_location_id", poh["source_location_id"], makeLocation);
        Check("prod_order_hdr.inventory_location_id", poh["inventory_location_id"], partsLocation);
        Console.WriteLine("\nNext: print, pick, confirm and complete it — docs/recipes/production-order-runbook.md");
        Console.WriteLine("\nRunbook complete.");
    }

    private static JToken Id(string value) => long.TryParse(value, out var n) ? n : value;

    /// <summary>Step 1: Inventory REST minimum create (item, location, supplier, location supplier).</summary>
    private static JObject BuildCreateBody(
        string item, string description, string supplier, string division, string productGroup, string location) =>
        new()
        {
            ["ItemId"] = item,
            ["ItemDesc"] = description.Length > 40 ? description[..40] : description,  // 40-character limit
            ["ObjectName"] = "inv_mast",
            ["Locations"] = new JObject { ["list"] = new JArray { new JObject {
                ["LocationId"] = Id(location), ["ProductGroupId"] = productGroup, ["ObjectName"] = "inv_loc" } } },
            ["Suppliers"] = new JObject { ["list"] = new JArray { new JObject {
                ["SupplierId"] = Id(supplier), ["DivisionId"] = Id(division), ["ObjectName"] = "inventory_supplier" } } },
            ["LocationSuppliers"] = new JObject { ["list"] = new JArray { new JObject {
                ["LocationId"] = Id(location), ["SupplierId"] = Id(supplier), ["PrimarySupplier"] = "Y",
                ["ObjectName"] = "inventory_supplier_x_loc" } } },
        };

    /// <summary>Step 2: one location per POST. The supplier row keys on BOTH
    /// location_id and supplier_id and needs IgnoreDisabled to insert.</summary>
    private static JObject BuildLocationPayload(
        string item, string company, string location, string productGroup, string supplier) =>
        Payload("Item", true,
            Element("TABPAGE_1.tp_1_dw_1", "Form", new[] { "item_id" }, new[] { Edit("item_id", item) }),
            Element("TABPAGE_17.invloclist", "List", new[] { "location_id" }, new[]
                { Edit("location_id", location), Edit("company_id", company), Edit("stockable", "ON") }),
            Element("TABPAGE_18.inv_loc_detail", "Form", new[] { "location_id" },
                new[] { Edit("product_group_id", productGroup) }),
            Element("SUPPLIER_X_LOCATION.supplier_x_location", "List", new[] { "location_id", "supplier_id" },
                new[] { Edit("location_id", location), Edit("supplier_id", supplier) }));

    /// <summary>Step 3: create with the minimum (production_order_processing sent
    /// explicitly), then the header flags in a second keyed POST.</summary>
    private static (JObject Create, JObject Flags) BuildAssemblyPayloads(
        string item, List<(string Item, string Qty, string Uom)> components) =>
        (Payload("Assembly", false,
            Element("TABPAGE_1.assemblyhdr", "Form", new[] { "inv_mast_item_id" },
                new[] { Edit("inv_mast_item_id", item), Edit("production_order_processing", "ON") }),
            Element("TABPAGE_17.tp_17_dw_17", "List", new[] { "item_id_service_labor_id" },
                components.Select(c => new[]
                {
                    Edit("item_id_service_labor_id", c.Item), Edit("quantity", c.Qty), Edit("unit_of_measure", c.Uom),
                }).ToArray())),
         Payload("Assembly", false,
            Element("TABPAGE_1.assemblyhdr", "Form", new[] { "inv_mast_item_id" }, new[]
            {
                Edit("inv_mast_item_id", item), Edit("print_incomplete_assemblies", "ON"),
                Edit("ship_incomplete_assemblies", "ON"), Edit("auto_create_prod_order", "OFF"),
            })));

    /// <summary>Step 4: ONE line per POST; pricing_method BEFORE price; IgnoreDisabled for the cost.</summary>
    private static JObject BuildContractPayload(
        string company, string contractNo, string jobNo, string item, string price, string commissionCost) =>
        Payload("JobContractPricing", true,
            Element("FORM.d_dw_job_price_hdr", "Form", Array.Empty<string>(), new[]   // Keys stay empty
                { Edit("company_id", company), Edit("contract_no", contractNo), Edit("job_no", jobNo) }),
            Element("JOBPRICELINE.jobpriceline", "List", new[] { "item_id" }, new[]
            {
                Edit("item_id", item), Edit("uom", "EA"),
                Edit("pricing_method", "Price"), Edit("price", price),   // pricing_method FIRST
            }),
            Element("JOBPRICECOST.jobpricecost", "Form", new[] { "item_id" }, new[]
            {
                Edit("item_id", item),
                Edit("commission_cost_type_cd", "Value"),                // type BEFORE value
                Edit("commission_cost_value", commissionCost),
            }));
}
