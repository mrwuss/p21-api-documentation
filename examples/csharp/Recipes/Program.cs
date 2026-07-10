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
