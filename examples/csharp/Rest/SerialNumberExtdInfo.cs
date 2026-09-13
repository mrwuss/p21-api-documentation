// Other REST Families - Serial Number Extended Info Upsert
// (inventory/serialnumberextdinfo)
// Docs: docs/15-Other-REST-Families.md#inventoryserialnumberextdinfo
// Mirrors: examples/python/rest/serial_number_extd_info.py
//
// Finds a real, currently-tracked serial number and attempts to attach
// extended info to it. Refusal is verified even against a genuine
// serial; the real precondition for success is unresolved.
//
// The trap: InvMastItemId looks derived (InvMastUid is the natural-
// looking key) but is read by the backend regardless -- omit it and the
// error message itself corrupts ("item 1" and a literal "%s" instead of
// the real item id and line number).

using System.Net.Http.Headers;
using Newtonsoft.Json.Linq;

namespace P21Examples.Rest;

public static class SerialNumberExtdInfo
{
    public static async Task RunAsync()
    {
        Console.WriteLine("Other REST Families - Serial Extended Info (serialnumberextdinfo)");
        Console.WriteLine(new string('=', 60));

        var (http, baseUrl) = await RestHelpers.CreateRawClientAsync();
        using var _ = http;
        Console.WriteLine($"Server: {baseUrl}");

        var serialResp = await http.GetAsync(
            $"{baseUrl}/odataservice/odata/table/serial_number?$select=inv_mast_uid,serial_number" +
            "&$filter=delete_flag eq 'N'&$top=1");
        var serials = (JObject.Parse(await serialResp.Content.ReadAsStringAsync())["value"] as JArray)!;
        if (serials.Count == 0)
        {
            Console.WriteLine("No serial_number rows on this tenant to test against.");
            return;
        }
        var uid = serials[0]["inv_mast_uid"];
        var serial = serials[0]["serial_number"];

        var itemResp = await http.GetAsync(
            $"{baseUrl}/odataservice/odata/table/inv_mast?$select=item_id&$filter=inv_mast_uid eq {uid}");
        var itemId = ((JObject.Parse(await itemResp.Content.ReadAsStringAsync())["value"] as JArray)![0])["item_id"];

        Console.WriteLine($"\nUsing a real, existing serial: inv_mast_uid={uid} item_id={itemId} " +
                          $"serial_number={serial}");

        var body = new JObject
        {
            ["InvMastUid"] = uid, ["InvMastItemId"] = itemId, ["SerialNumber"] = serial,
            ["Comments"] = "ZZ API DOC TEST",
        };
        var content = new StringContent(body.ToString());
        content.Headers.ContentType = new MediaTypeHeaderValue("application/json");
        var resp = await http.PutAsync($"{baseUrl}/api/inventory/serialnumberextdinfo/", content);
        Console.WriteLine($"\nHTTP {(int)resp.StatusCode}");
        var text = await resp.Content.ReadAsStringAsync();
        if (!resp.IsSuccessStatusCode)
        {
            var stack = (string?)JObject.Parse(text)["StackTrace"] ?? text;
            var line = stack.Split('\n').FirstOrDefault(l => l.Contains("ErrorMessage:"));
            Console.WriteLine($"  {(line ?? stack).Trim()}");
        }
        else
        {
            Console.WriteLine(text);
        }
    }
}
