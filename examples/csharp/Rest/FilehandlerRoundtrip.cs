// Other REST Families - File Upload/Download/Delete Round Trip (filehandler)
// Docs: docs/15-Other-REST-Families.md#filehandler
// Mirrors: examples/python/rest/filehandler_roundtrip.py
//
// This is a real network file share, not a sandbox -- verified files
// landed at the middleware's own configured default path. Treat this
// family as filesystem access, not a data API.
//
// Casing split: file/detail takes lowercase `filename`; every other
// route takes `fileName`. A detail check on a deleted file returns
// HTTP 200 with a JSON null body, not a 404.

using System.Text;
using Newtonsoft.Json.Linq;

namespace P21Examples.Rest;

public static class FilehandlerRoundtrip
{
    private const string FileName = "zz_api_doc_test.txt";
    private static readonly byte[] Content = Encoding.UTF8.GetBytes(
        "ZZ API DOC TEST - safe to delete\nCreated by p21-api-documentation verification run.\n");

    public static async Task RunAsync()
    {
        Console.WriteLine("Other REST Families - File Round Trip (filehandler)");
        Console.WriteLine(new string('=', 60));

        var (http, baseUrl) = await RestHelpers.CreateRawClientAsync();
        using var _ = http;
        Console.WriteLine($"Server: {baseUrl}");

        Console.WriteLine("\n1. Upload:");
        Console.WriteLine(new string('-', 50));
        var upload = await http.PostAsync(
            $"{baseUrl}/api/filehandler/file?fileName={FileName}",
            new ByteArrayContent(Content));
        upload.EnsureSuccessStatusCode();
        Console.WriteLine($"  Uploaded {FileName} ({Content.Length} bytes)");

        Console.WriteLine("\n2. Detail (note lowercase 'filename' here):");
        Console.WriteLine(new string('-', 50));
        var detail = await http.GetAsync($"{baseUrl}/api/filehandler/file/detail?filename={FileName}");
        detail.EnsureSuccessStatusCode();
        var info = JObject.Parse(await detail.Content.ReadAsStringAsync());
        Console.WriteLine($"  Path: {info["Path"]}");
        Console.WriteLine($"  SizeInBytes: {info["SizeInBytes"]}");

        Console.WriteLine("\n3. Download:");
        Console.WriteLine(new string('-', 50));
        var download = await http.GetAsync($"{baseUrl}/api/filehandler/file?fileName={FileName}");
        download.EnsureSuccessStatusCode();
        var downloaded = await download.Content.ReadAsByteArrayAsync();
        Console.WriteLine($"  Content matches: {downloaded.SequenceEqual(Content)}");

        Console.WriteLine("\n4. Delete:");
        Console.WriteLine(new string('-', 50));
        var delete = await http.DeleteAsync($"{baseUrl}/api/filehandler/file?fileName={FileName}");
        delete.EnsureSuccessStatusCode();
        Console.WriteLine($"  Delete response: {await delete.Content.ReadAsStringAsync()}");

        Console.WriteLine("\n5. Confirm gone (200 + null, NOT a 404):");
        Console.WriteLine(new string('-', 50));
        var after = await http.GetAsync($"{baseUrl}/api/filehandler/file/detail?filename={FileName}");
        Console.WriteLine($"  HTTP {(int)after.StatusCode}, body: {await after.Content.ReadAsStringAsync()}");
    }
}
