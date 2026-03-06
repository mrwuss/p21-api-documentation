// P21 Production & Labor API Examples - C#
//
// Menu-driven runner for all Production/Labor API examples.
// Each example is a static class with an async RunAsync() method.
//
// Prerequisites:
//   - .env file with P21_BASE_URL, P21_USERNAME, P21_PASSWORD
//   - Network access to the P21 server
//
// Usage:
//   dotnet run --project examples/csharp/Production
//
// Or from Visual Studio, set Production as the startup project.

using P21Examples.Production;

Console.WriteLine("P21 Production & Labor API Examples (C#)");
Console.WriteLine(new string('=', 50));
Console.WriteLine();

while (true)
{
    Console.WriteLine("Select an example to run:");
    Console.WriteLine();
    Console.WriteLine("  1. List Production Services      - Discover production/labor Transaction API services");
    Console.WriteLine("  2. Get TimeEntry Definition      - Fetch TimeEntry schema, fields, and defaults");
    Console.WriteLine("  3. Get ProductionOrder Definition - Fetch ProductionOrder schema and labor elements");
    Console.WriteLine("  4. Record Labor Hours             - Record labor hours against a production order");
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
                await ListProductionServices.RunAsync();
                break;

            case "2":
                await GetTimeEntryDefinition.RunAsync();
                break;

            case "3":
                await GetProductionOrderDefinition.RunAsync();
                break;

            case "4":
                await RecordLaborHours.RunAsync();
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
