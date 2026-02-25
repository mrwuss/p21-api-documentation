// Entity API Examples - Menu
//
// Run a specific Entity API example by number or name.
//
// Usage:
//   dotnet run                    # Show menu
//   dotnet run -- 1               # Run ListEntities
//   dotnet run -- list            # Run ListEntities
//   dotnet run -- 2               # Run QueryEntity
//   dotnet run -- query           # Run QueryEntity
//   dotnet run -- 3               # Run CreateEntity
//   dotnet run -- create          # Run CreateEntity
//   dotnet run -- 4               # Run UpdateEntity
//   dotnet run -- update          # Run UpdateEntity
//
// Prerequisites:
//   - .env file with P21_BASE_URL, P21_USERNAME, P21_PASSWORD
//   - P21 server accessible from this machine

namespace P21Examples.Entity;

public static class Program
{
    private static readonly (string Number, string Name, string Description, Func<Task> Runner)[] Examples =
    [
        ("1", "list",   "List Available Entities  (ping, templates, sample data)", ListEntities.RunAsync),
        ("2", "query",  "Query Entities           ($query filters, operators)",    QueryEntity.RunAsync),
        ("3", "create", "Create Entity            (templates, POST workflow)",     CreateEntity.RunAsync),
        ("4", "update", "Update Entity            (GET, PUT, extended properties)", UpdateEntity.RunAsync),
    ];

    public static async Task Main(string[] args)
    {
        // If an argument was provided, run that example directly
        if (args.Length > 0)
        {
            var choice = args[0].Trim().ToLowerInvariant();
            var example = FindExample(choice);

            if (example.Runner != null)
            {
                await RunExample(example.Runner);
                return;
            }

            Console.WriteLine($"Unknown example: '{args[0]}'");
            Console.WriteLine();
        }

        // Show interactive menu
        while (true)
        {
            Console.WriteLine();
            Console.WriteLine("P21 Entity API Examples");
            Console.WriteLine(new string('=', 60));
            Console.WriteLine();
            Console.WriteLine("Available examples:");
            Console.WriteLine();

            foreach (var (number, name, description, _) in Examples)
            {
                Console.WriteLine($"  {number}. {description}");
            }

            Console.WriteLine();
            Console.WriteLine("  q. Quit");
            Console.WriteLine();
            Console.Write("Select an example (1-4, or q): ");

            var input = Console.ReadLine()?.Trim().ToLowerInvariant();
            if (string.IsNullOrEmpty(input) || input == "q" || input == "quit" || input == "exit")
                break;

            var selected = FindExample(input);

            if (selected.Runner != null)
            {
                Console.WriteLine();
                await RunExample(selected.Runner);
                Console.WriteLine();
                Console.Write("Press Enter to continue...");
                Console.ReadLine();
            }
            else
            {
                Console.WriteLine($"Invalid selection: '{input}'. Enter 1-4 or q to quit.");
            }
        }
    }

    private static (Func<Task>? Runner, string? Name) FindExample(string input)
    {
        foreach (var (number, name, _, runner) in Examples)
        {
            if (input == number || input == name)
                return (runner, name);
        }
        return (null, null);
    }

    private static async Task RunExample(Func<Task> runner)
    {
        try
        {
            await runner();
        }
        catch (Exception ex)
        {
            Console.WriteLine();
            Console.WriteLine($"ERROR: {ex.GetType().Name}: {ex.Message}");

            if (ex.Message.Contains("P21_BASE_URL") ||
                ex.Message.Contains("P21_USERNAME"))
            {
                Console.WriteLine();
                Console.WriteLine("Make sure you have a .env file with:");
                Console.WriteLine("  P21_BASE_URL=https://play.p21server.com");
                Console.WriteLine("  P21_USERNAME=your_username");
                Console.WriteLine("  P21_PASSWORD=your_password");
            }
        }
    }
}
