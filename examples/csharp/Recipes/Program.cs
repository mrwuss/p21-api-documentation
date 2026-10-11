// P21 Cookbook Recipes - C#
//
// Menu-driven runner for the docs/recipes/ cookbook — one end-to-end class
// per recipe page. Each example is a static class with an async RunAsync()
// method.
//
// WRITE SAFETY: every recipe prints its payload and asks for console
// confirmation (Type EXECUTE to post, anything else = dry run) before any
// POST that writes; read-only lookups run freely.
//
// Prerequisites:
//   - .env file with P21_BASE_URL, P21_USERNAME, P21_PASSWORD
//   - Network access to the P21 server
//   - Always run against a test/play environment first
//
// Usage:
//   dotnet run --project examples/csharp/Recipes
//
// Or from Visual Studio, set Recipes as the startup project.

using P21Examples.Recipes;

Console.WriteLine("P21 Cookbook Recipes (C#)");
Console.WriteLine(new string('=', 50));
Console.WriteLine();

while (true)
{
    Console.WriteLine("Select a recipe to run:");
    Console.WriteLine();
    Console.WriteLine("   1. Update Contract Lines      - JobContractPricing line/price upsert");
    Console.WriteLine("   2. Edit Contract Bins         - Bin min/max/reorder via IgnoreDisabled");
    Console.WriteLine("   3. Create Bins (Bulk)         - BinLocation twin-clone batch create");
    Console.WriteLine("   4. Create Sales Order         - Order header + lines in one POST");
    Console.WriteLine("   5. Order with Assembly        - Interactive flow with response windows");
    Console.WriteLine("   6. Set Primary Bin/Supplier   - Item nested edit + mandatory read-back");
    Console.WriteLine("   7. Generate Pick Ticket PDF   - m_picktickets via /process/pdfreport");
    Console.WriteLine("   8. Production Order Runbook   - Checklist + pick-ticket stage");
    Console.WriteLine("   9. Record Labor Time          - TimeEntry labor hours");
    Console.WriteLine("  10. Inventory Adjustment       - Signed on-hand delta write-off");
    Console.WriteLine("  11. Create Customer            - Customer header + ship-to in one POST");
    Console.WriteLine("  12. Create Requisition PO      - RequisitionPurchaseOrder (po_type 'R')");
    Console.WriteLine("  13. Update Order Lines         - Edit/add lines on an existing order");
    Console.WriteLine("  14. Reassign Salesrep          - Customer + ShipTo grids, two delete mechanisms");
    Console.WriteLine("  15. Update Supplier Contact    - Email/central phone via the Address service");
    Console.WriteLine("  16. Clone Item                 - Inventory REST GET -> strip -> POST");
    Console.WriteLine("  17. Create Ship-To             - ShipTo service + inherited-rep swap");
    Console.WriteLine("  18. Inventory Cost Edit        - InventoryCostEdit moving average cost");
    Console.WriteLine("  19. Reprint Purchase Order PDF - m_reprintpurchaseorders, flag = po_hdr.printed");
    Console.WriteLine("  20. Bin Lock/Delete            - BinLocation lock, unlock, delete, restore");
    Console.WriteLine("  21. Vendor Create              - Vendor + its auto-created supplier");
    Console.WriteLine("  22. Assembly Create/Edit       - Create on a plain item; flag, qty, delete");
    Console.WriteLine("  23. Contract Ship-To/line_no   - Attach ship-to; update a line by line_no");
    Console.WriteLine("  24. Order Append/Hold/Cancel   - Multi-line append, release Hold, cancel");
    Console.WriteLine("  25. Item/Customer Merge        - m_itemmerge / m_customermerge (one-way)");
    Console.WriteLine("  26. Sales Price Page + Book    - SalesPricePage create, SalesPriceBook link/unlink");
    Console.WriteLine("  27. Purchase Pricing Page Edit - PurchasePricingPageSupplierItem in-place edit");
    Console.WriteLine("  28. Inventory ListPrice/Stock  - Inventory REST PUT of ListPrice + Stockable");
    Console.WriteLine("  29. Order Entry, quote OFF     - Order window quote check (+ direct-ship wizard)");
    Console.WriteLine("  30. Direct Ship Confirmation   - DirectShipConfirmation window, receive_all");
    Console.WriteLine("  31. Customer Price Library     - Customer window TABPAGE_7 add/remove + sequence");
    Console.WriteLine("  32. DynaChange Rule Toggle     - dc.organizer.rule disable/re-enable");
    Console.WriteLine();
    Console.WriteLine("  Q. Quit");
    Console.WriteLine();
    Console.Write("Choice: ");

    var choice = Console.ReadLine()?.Trim().ToUpper();
    Console.WriteLine();

    try
    {
        switch (choice)
        {
            case "1":
                await UpdateContractLines.RunAsync();
                break;

            case "2":
                await EditContractBins.RunAsync();
                break;

            case "3":
                await CreateBins.RunAsync();
                break;

            case "4":
                await CreateSalesOrder.RunAsync();
                break;

            case "5":
                await OrderWithAssembly.RunAsync();
                break;

            case "6":
                await SetPrimaryBinSupplier.RunAsync();
                break;

            case "7":
                await GeneratePickTicketPdf.RunAsync();
                break;

            case "8":
                await ProductionOrderRunbook.RunAsync();
                break;

            case "9":
                await RecordLaborTime.RunAsync();
                break;

            case "10":
                await InventoryAdjustment.RunAsync();
                break;

            case "11":
                await CreateCustomer.RunAsync();
                break;

            case "12":
                await CreateRequisitionPo.RunAsync();
                break;

            case "13":
                await UpdateOrderLines.RunAsync();
                break;

            case "15":
                await UpdateSupplierContact.RunAsync();
                break;

            case "14":
                await ReassignSalesrep.RunAsync();
                break;

            case "16":
                await CloneItem.RunAsync();
                break;

            case "17":
                await CreateShipTo.RunAsync();
                break;

            case "18":
                await InventoryCostEdit.RunAsync();
                break;

            case "19":
                await ReprintPurchaseOrder.RunAsync();
                break;

            case "20":
                await BinLockDelete.RunAsync();
                break;

            case "21":
                await VendorCreate.RunAsync();
                break;

            case "22":
                await AssemblyCreateEdit.RunAsync();
                break;

            case "23":
                await ContractShipToLineNo.RunAsync();
                break;

            case "24":
                await OrderAppendHoldCancel.RunAsync();
                break;

            case "25":
                await ItemCustomerMerge.RunAsync();
                break;

            case "26":
                await SalesPricePageCreateLink.RunAsync();
                break;

            case "27":
                await PurchasePricingPageEdit.RunAsync();
                break;

            case "28":
                await InventoryUpdateListPriceStockable.RunAsync();
                break;

            case "29":
                await OrderEntryQuoteOff.RunAsync();
                break;

            case "30":
                await DirectShipConfirmation.RunAsync();
                break;

            case "31":
                await CustomerPriceLibrary.RunAsync();
                break;

            case "32":
                await DynaChangeRuleToggle.RunAsync();
                break;

            case "Q":
            case null:
                Console.WriteLine("Goodbye!");
                return;

            default:
                Console.WriteLine($"Unknown choice: {choice}");
                break;
        }
    }
    catch (Exception ex)
    {
        Console.WriteLine($"\nUnhandled error: {ex.GetType().Name}");
        Console.WriteLine($"  {ex.Message}");

        if (ex.InnerException != null)
        {
            Console.WriteLine($"  Inner: {ex.InnerException.Message}");
        }
    }

    Console.WriteLine();
    Console.WriteLine(new string('-', 50));
    Console.WriteLine();
}
