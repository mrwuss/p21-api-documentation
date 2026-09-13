// Other REST Families - C# examples (docs/15-Other-REST-Families.md)
//
// Menu-driven runner for the five families in doc 15: UDF metadata, GL
// journal entries, CRM task CRUD, PO header reads, and inventory
// adjustment header reads.
//
// WRITE SAFETY: the CRM task example prints its payload and asks for
// console confirmation (type EXECUTE to post, anything else = dry run)
// before any write; every other example here is read-only.
//
// Prerequisites:
//   - .env file with P21_BASE_URL, P21_USERNAME, P21_PASSWORD
//   - Network access to the P21 server
//   - Always run against a test/play environment first
//
// Usage:
//   dotnet run --project examples/csharp/Rest

using P21Examples.Rest;

Console.WriteLine("P21 Other REST Families Examples (C#)");
Console.WriteLine(new string('=', 50));
Console.WriteLine();

while (true)
{
    Console.WriteLine("Select an example to run:");
    Console.WriteLine();
    Console.WriteLine("   1. UDF Inventory              - extensibility/userdefinedfields");
    Console.WriteLine("   2. GL Journal Entry            - accounting/gl (read + follow Source)");
    Console.WriteLine("   3. CRM Task CRUD               - sales/tasks (create/read/update)");
    Console.WriteLine("   4. Purchase Order Header        - purchasing/purchaseorders (read)");
    Console.WriteLine("   5. Inventory Adjustment Header  - inventory/inventoryadjustments (read)");
    Console.WriteLine("   6. Post GL Entry                - accounting/gl (write, EXECUTE-gated)");
    Console.WriteLine("   7. Create Purchase Order        - purchasing/purchaseorders (write, EXECUTE-gated)");
    Console.WriteLine("   8. WMS Inventory Adjustment     - createWmsAdjustment (write, EXECUTE-gated)");
    Console.WriteLine("   9. File Round Trip              - filehandler (upload/detail/download/delete)");
    Console.WriteLine("  10. System Info                  - environment/systems");
    Console.WriteLine("  11. Inventory Movement           - inventorymovement (write, EXECUTE-gated)");
    Console.WriteLine("  12. External Count Create        - inventory/externalcounts (write, EXECUTE-gated)");
    Console.WriteLine("  13. Part Scan                    - inventory/partscan");
    Console.WriteLine("  14. Customer Form Template       - accounting/customerformtemplates (write, EXECUTE-gated)");
    Console.WriteLine("  15. Service Order Read           - service/serviceorders");
    Console.WriteLine("  16. Opportunity Create           - sales/opportunities (blocked by tenant config, write EXECUTE-gated)");
    Console.WriteLine("  17. CUO Create                   - sales/consignmentusageorders (blocked, write EXECUTE-gated)");
    Console.WriteLine("  18. Exchange Rate Create         - accounting/exchangerates (blocked, write EXECUTE-gated)");
    Console.WriteLine("  19. Serial Extended Info         - inventory/serialnumberextdinfo (write, not gated -- refusal expected)");
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
                await UdfInventory.RunAsync();
                break;

            case "2":
                await GlJournalEntry.RunAsync();
                break;

            case "3":
                await TaskCrud.RunAsync();
                break;

            case "4":
                await PurchaseOrderRead.RunAsync();
                break;

            case "5":
                await InventoryAdjustmentRead.RunAsync();
                break;

            case "6":
                await GlPost.RunAsync();
                break;

            case "7":
                await PurchaseOrderCreate.RunAsync();
                break;

            case "8":
                await InventoryWmsAdjustment.RunAsync();
                break;

            case "9":
                await FilehandlerRoundtrip.RunAsync();
                break;

            case "10":
                await EnvironmentSystems.RunAsync();
                break;

            case "11":
                await InventoryMovement.RunAsync();
                break;

            case "12":
                await ExternalCountCreate.RunAsync();
                break;

            case "13":
                await PartScan.RunAsync();
                break;

            case "14":
                await CustomerFormTemplate.RunAsync();
                break;

            case "15":
                await ServiceOrderRead.RunAsync();
                break;

            case "16":
                await OpportunityCreate.RunAsync();
                break;

            case "17":
                await ConsignmentUsageOrderCreate.RunAsync();
                break;

            case "18":
                await ExchangeRateCreate.RunAsync();
                break;

            case "19":
                await SerialNumberExtdInfo.RunAsync();
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
