// Other REST Families - CRM Task CRUD Round Trip (sales/tasks)
// Docs: docs/15-Other-REST-Families.md#salestasks
// Mirrors: examples/python/rest/task_crud.py
//
// Create -> read -> update a P21 CRM task (activity_trans).
//
// Key rules (verified live, 26.1.5950.0):
//   - There is no CustomerId field. The create fails "Customer ID is
//     required" and the error also says "CRUD Update error: Update
//     failed" on what is a CREATE -- the middleware routes both verbs
//     through one CRUD path. The customer goes in LinkId, paired with
//     LinkTypeCd (1203 in the server's own /new template).
//   - ContactAddressName is server-derived from LinkId -- do not set it.
//   - There is no delete route. Close a task with Completed: "Y".
//   - GET /api/sales/tasks/ (no key) is an UNBOUNDED collection dump --
//     never call it. This example only uses /new and keyed routes.

using System.Net.Http.Headers;
using Newtonsoft.Json.Linq;

namespace P21Examples.Rest;

public static class TaskCrud
{
    public static async Task RunAsync()
    {
        Console.WriteLine("Other REST Families - CRM Task CRUD (sales/tasks)");
        Console.WriteLine(new string('=', 60));

        var (http, baseUrl) = await RestHelpers.CreateRawClientAsync();
        using var _ = http;
        Console.WriteLine($"Server: {baseUrl}");

        var templateResponse = await http.GetAsync($"{baseUrl}/api/sales/tasks/new");
        templateResponse.EnsureSuccessStatusCode();
        var task = JObject.Parse(await templateResponse.Content.ReadAsStringAsync());
        Console.WriteLine($"\nServer template (/new): AssignedById={task["AssignedById"]}  " +
                          $"LinkTypeCd={task["LinkTypeCd"]}");

        Console.Write("\nContactId [17055]: ");
        var contactId = Console.ReadLine()?.Trim();
        contactId = string.IsNullOrEmpty(contactId) ? "17055" : contactId;

        Console.Write("Customer id -> LinkId [12066] (this is what \"Customer ID is " +
                      "required\" actually means): ");
        var customerId = Console.ReadLine()?.Trim();
        customerId = string.IsNullOrEmpty(customerId) ? "12066" : customerId;

        task["ActivityId"] = "FOLLOW UP";
        task["ContactId"] = contactId;
        task["LinkId"] = int.Parse(customerId);
        task["Subject"] = "ZZ API DOC TEST - safe to delete";
        task["Comments"] = "Created by examples/csharp/Rest/TaskCrud.cs";
        task["TargetCompleteDate"] = "2026-09-30T15:00:00";

        Console.WriteLine("\nPayload that would be POSTed to /api/sales/tasks/:");
        Console.WriteLine(new string('-', 50));
        Console.WriteLine(task.ToString());

        if (!RestHelpers.ConfirmExecute())
            return;

        Console.WriteLine("\n1. Create:");
        Console.WriteLine(new string('-', 50));
        var createContent = new StringContent(task.ToString());
        createContent.Headers.ContentType = new MediaTypeHeaderValue("application/json");
        var created = await http.PostAsync($"{baseUrl}/api/sales/tasks/", createContent);
        created.EnsureSuccessStatusCode();
        var createdTask = JObject.Parse(await created.Content.ReadAsStringAsync());
        var taskNo = (string)createdTask["ActivityTransNo"]!;
        Console.WriteLine($"  Created ActivityTransNo={taskNo}");

        Console.WriteLine("\n2. Read back:");
        Console.WriteLine(new string('-', 50));
        var readResponse = await http.GetAsync($"{baseUrl}/api/sales/tasks/{taskNo}");
        readResponse.EnsureSuccessStatusCode();
        var current = JObject.Parse(await readResponse.Content.ReadAsStringAsync());
        Console.WriteLine($"  ContactAddressName (server-derived from LinkId): " +
                          $"{current["ContactAddressName"]}");

        Console.WriteLine("\n3. Update (mark complete):");
        Console.WriteLine(new string('-', 50));
        current["Completed"] = "Y";
        current["Comments"] = "Closed by examples/csharp/Rest/TaskCrud.cs";
        var updateContent = new StringContent(current.ToString());
        updateContent.Headers.ContentType = new MediaTypeHeaderValue("application/json");
        var updated = await http.PutAsync($"{baseUrl}/api/sales/tasks/{taskNo}", updateContent);
        updated.EnsureSuccessStatusCode();
        var updatedTask = JObject.Parse(await updated.Content.ReadAsStringAsync());
        Console.WriteLine($"  Completed={updatedTask["Completed"]}");

        Console.WriteLine("\n" + new string('=', 60));
        Console.WriteLine($"Round trip complete. Task {taskNo} left Completed=Y " +
                          "(there is no delete route on this family).");
    }
}
