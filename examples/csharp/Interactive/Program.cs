namespace P21Examples.Interactive;

/// <summary>
/// Interactive API Examples — Main Entry Point
///
/// Provides a menu to select which Interactive API example to run.
///
/// Each example mirrors its corresponding Python script in
/// scripts/interactive/ and demonstrates both the high-level
/// P21Client/InteractiveSession helpers and raw HTTP calls.
///
/// Prerequisites:
///   - .env file with P21_BASE_URL, P21_USERNAME, P21_PASSWORD
///   - P21 server accessible from this machine
///
/// Usage:
///   dotnet run                     (shows menu)
///   dotnet run -- 1                (runs example 1 directly)
///   dotnet run -- --all            (runs all examples in sequence)
/// </summary>
internal static class Program
{
    private static readonly (string Name, string Description, Func<Task> Action)[] Examples =
    {
        ("OpenSession",      "Session management (open, list, close)",      OpenSession.RunAsync),
        ("OpenWindow",       "Open and inspect P21 windows",                OpenWindow.RunAsync),
        ("ChangeData",       "Change field values in windows (v2)",         ChangeData.RunAsync),
        ("SaveAndClose",     "Complete create workflow (open, edit, save)",  SaveAndClose.RunAsync),
        ("ResponseWindows",  "Response window / dialog handling",           ResponseWindows.RunAsync),
        ("ComplexWorkflow",  "Multi-step workflow with context manager",    ComplexWorkflow.RunAsync),
    };

    static async Task<int> Main(string[] args)
    {
        // If an argument is passed, use it directly
        if (args.Length > 0)
        {
            if (args[0] == "--all")
                return await RunAllAsync();

            if (int.TryParse(args[0], out var num) && num >= 1 && num <= Examples.Length)
                return await RunExampleAsync(num - 1);

            Console.WriteLine($"Unknown argument: {args[0]}");
            Console.WriteLine("Usage: dotnet run -- [1-6 | --all]");
            return 1;
        }

        // Interactive menu
        while (true)
        {
            PrintMenu();
            Console.Write("\nSelect example (1-6, 'a' for all, 'q' to quit): ");
            var input = Console.ReadLine()?.Trim().ToLower();

            if (string.IsNullOrEmpty(input) || input == "q")
                break;

            if (input == "a")
            {
                await RunAllAsync();
                continue;
            }

            if (int.TryParse(input, out var choice) && choice >= 1 && choice <= Examples.Length)
            {
                await RunExampleAsync(choice - 1);
                Console.WriteLine("\nPress Enter to return to menu...");
                Console.ReadLine();
            }
            else
            {
                Console.WriteLine("Invalid selection. Please enter 1-6, 'a', or 'q'.");
            }
        }

        return 0;
    }

    private static void PrintMenu()
    {
        Console.WriteLine();
        Console.WriteLine("P21 Interactive API Examples (C#)");
        Console.WriteLine(new string('=', 50));
        Console.WriteLine();

        for (var i = 0; i < Examples.Length; i++)
        {
            Console.WriteLine($"  {i + 1}. {Examples[i].Name,-20} - {Examples[i].Description}");
        }

        Console.WriteLine();
        Console.WriteLine("  a. Run all examples in sequence");
        Console.WriteLine("  q. Quit");
    }

    private static async Task<int> RunExampleAsync(int index)
    {
        var (name, description, action) = Examples[index];

        Console.WriteLine();
        Console.WriteLine($"Running: {name} - {description}");
        Console.WriteLine(new string('=', 60));

        try
        {
            await action();
            return 0;
        }
        catch (Exception ex)
        {
            Console.WriteLine();
            Console.WriteLine($"UNHANDLED ERROR in {name}:");
            Console.WriteLine($"  {ex.GetType().Name}: {ex.Message}");

            if (ex.InnerException != null)
                Console.WriteLine($"  Inner: {ex.InnerException.Message}");

            return 1;
        }
    }

    private static async Task<int> RunAllAsync()
    {
        Console.WriteLine();
        Console.WriteLine("Running ALL Interactive API examples...");
        Console.WriteLine(new string('=', 60));

        var failures = 0;

        for (var i = 0; i < Examples.Length; i++)
        {
            Console.WriteLine();
            Console.WriteLine($">>> Example {i + 1}/{Examples.Length}: {Examples[i].Name}");
            Console.WriteLine(new string('-', 60));

            var result = await RunExampleAsync(i);
            if (result != 0)
                failures++;

            Console.WriteLine();
        }

        Console.WriteLine(new string('=', 60));
        Console.WriteLine($"Completed: {Examples.Length - failures}/{Examples.Length} succeeded");

        if (failures > 0)
            Console.WriteLine($"  {failures} example(s) had errors");

        return failures > 0 ? 1 : 0;
    }
}
