// P21 OData API Examples — Entry Point
//
// Run with: dotnet run --project OData
//
// Presents a menu to select which example to run.
// Each example mirrors its Python counterpart in scripts/odata/.

namespace P21Examples.OData;

class Program
{
    static async Task<int> Main(string[] args)
    {
        Console.WriteLine();
        Console.WriteLine("P21 OData API Examples (C#)");
        Console.WriteLine(new string('=', 40));
        Console.WriteLine();
        Console.WriteLine("  1. Basic Query       — simple table queries, field selection, $count");
        Console.WriteLine("  2. Filtering         — $filter operators: eq, and, startswith, contains, gt/lt");
        Console.WriteLine("  3. Pagination        — $skip/$top pagination, automatic page-through");
        Console.WriteLine("  4. Complex Queries   — OR conditions, null checks, multi-sort, join pattern");
        Console.WriteLine("  5. Run All           — execute all examples sequentially");
        Console.WriteLine("  0. Exit");
        Console.WriteLine();

        // Allow passing the choice as a command-line argument for scripting:
        //   dotnet run --project OData -- 1
        string? choice;
        if (args.Length > 0)
        {
            choice = args[0];
            Console.WriteLine($"Selected: {choice} (from command line)");
        }
        else
        {
            Console.Write("Select an example (0-5): ");
            choice = Console.ReadLine()?.Trim();
        }

        Console.WriteLine();

        try
        {
            switch (choice)
            {
                case "1":
                    await BasicQuery.RunAsync();
                    break;

                case "2":
                    await Filtering.RunAsync();
                    break;

                case "3":
                    await Pagination.RunAsync();
                    break;

                case "4":
                    await ComplexQueries.RunAsync();
                    break;

                case "5":
                    await RunAllAsync();
                    break;

                case "0":
                case null:
                case "":
                    Console.WriteLine("Exiting.");
                    return 0;

                default:
                    Console.WriteLine($"Unknown selection: {choice}");
                    return 1;
            }
        }
        catch (HttpRequestException ex)
        {
            Console.WriteLine();
            Console.WriteLine($"HTTP Error: {ex.Message}");
            Console.WriteLine();
            Console.WriteLine("Troubleshooting:");
            Console.WriteLine("  - Verify P21_BASE_URL, P21_USERNAME, P21_PASSWORD in .env");
            Console.WriteLine("  - Ensure the P21 server is reachable");
            Console.WriteLine("  - Check that your user has OData API permissions:");
            Console.WriteLine("    1. User Maintenance > Application Security > 'Allow OData API Service'");
            Console.WriteLine("    2. Role Maintenance > Dataservice Permission > Allow specific tables");
            return 1;
        }
        catch (InvalidOperationException ex)
        {
            Console.WriteLine();
            Console.WriteLine($"Configuration Error: {ex.Message}");
            Console.WriteLine("Ensure .env file exists with P21_BASE_URL, P21_USERNAME, P21_PASSWORD");
            return 1;
        }
        catch (Exception ex)
        {
            Console.WriteLine();
            Console.WriteLine($"Unexpected Error: {ex.GetType().Name}: {ex.Message}");
            return 1;
        }

        return 0;
    }

    /// <summary>
    /// Run all four examples back-to-back with separators.
    /// </summary>
    private static async Task RunAllAsync()
    {
        Console.WriteLine("Running all OData examples...");
        Console.WriteLine();

        await BasicQuery.RunAsync();

        Console.WriteLine();
        Console.WriteLine(new string('*', 60));
        Console.WriteLine();

        await Filtering.RunAsync();

        Console.WriteLine();
        Console.WriteLine(new string('*', 60));
        Console.WriteLine();

        await Pagination.RunAsync();

        Console.WriteLine();
        Console.WriteLine(new string('*', 60));
        Console.WriteLine();

        await ComplexQueries.RunAsync();

        Console.WriteLine();
        Console.WriteLine(new string('*', 60));
        Console.WriteLine();
        Console.WriteLine("All OData examples complete!");
    }
}
