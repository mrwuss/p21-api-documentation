// P21 Transaction API Examples - C#
//
// Menu-driven runner for all Transaction API examples.
// Each example is a static class with an async RunAsync() method.
//
// Prerequisites:
//   - .env file with P21_BASE_URL, P21_USERNAME, P21_PASSWORD
//   - Network access to the P21 server
//
// Usage:
//   dotnet run --project examples/csharp/Transaction
//
// Or from Visual Studio, set Transaction as the startup project.

using P21Examples.Transaction;

Console.WriteLine("P21 Transaction API Examples (C#)");
Console.WriteLine(new string('=', 50));
Console.WriteLine();

while (true)
{
    Console.WriteLine("Select an example to run:");
    Console.WriteLine();
    Console.WriteLine("  1. List Services          - Discover available Transaction API services");
    Console.WriteLine("  2. Get Definition         - Fetch service schemas and field metadata");
    Console.WriteLine("  3. Create Single Record   - Create one SalesPricePage record");
    Console.WriteLine("  4. Create Bulk Records    - Create multiple records in one request");
    Console.WriteLine("  5. Update Existing Record - Fetch and update an existing record");
    Console.WriteLine("  6. Async Operations       - Submit async transaction with polling");
    Console.WriteLine("  7. Session Pool Test      - Diagnose session pool contamination");
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
                await ListServices.RunAsync();
                break;

            case "2":
                await GetDefinition.RunAsync();
                break;

            case "3":
                await CreateSingle.RunAsync();
                break;

            case "4":
                await CreateBulk.RunAsync();
                break;

            case "5":
                await UpdateExisting.RunAsync();
                break;

            case "6":
                await AsyncOperations.RunAsync();
                break;

            case "7":
                await TestSessionPool.RunAsync();
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
