// Other REST Families - Read Middleware System Info (environment/systems)
// Docs: docs/15-Other-REST-Families.md#environmentsystems
// Mirrors: examples/python/rest/environment_systems.py
//
// There is no /ping on this family -- the SDK contract never declares
// one. The bare GET is the availability check.
//
// The trailing slash is required in C#: the no-slash form 307-redirects,
// and HttpClient strips the Authorization header across that redirect
// (deliberate .NET behavior, already documented -- see
// docs/06-Error-Handling.md#401-authorization-header-was-not-present-or-bearer-was-missing).
// httpx does not have this failure mode, which is why the Python sibling
// of this script gets away with the no-slash form.

using Newtonsoft.Json.Linq;

namespace P21Examples.Rest;

public static class EnvironmentSystems
{
    public static async Task RunAsync()
    {
        Console.WriteLine("Other REST Families - System Info (environment/systems)");
        Console.WriteLine(new string('=', 60));

        var (http, baseUrl) = await RestHelpers.CreateRawClientAsync();
        using var _ = http;
        Console.WriteLine($"Server: {baseUrl}");

        var response = await http.GetAsync($"{baseUrl}/api/environment/systems/");
        response.EnsureSuccessStatusCode();
        var systems = (JObject.Parse(await response.Content.ReadAsStringAsync())["list"] as JArray)!;

        foreach (var system in systems)
        {
            Console.WriteLine($"\n{system["Id"]} ({system["Type"]})");
            Console.WriteLine($"  Version: {system["Version"]}");
            foreach (var prop in (JArray)system["Properties"]!["list"]!)
                Console.WriteLine($"  {prop["Name"]}: {prop["Value"]}");
        }
    }
}
