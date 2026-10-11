// Recipe: Print or Reprint a Purchase Order PDF
// Docs:   docs/03-Transaction-API.md § Example: Generate and Save a PO Reprint
//         docs/recipes/generate-pick-ticket-pdf.md (m_reprintpurchaseorders)
//
// Generate one PO as a base64-encoded PDF through POST /api/v2/process/pdfreport
// (service m_reprintpurchaseorders), save it, and read the PO's print history back.
//
// Key rules (verified live — see the doc section):
//   - reprint_flag must EQUAL the PO's own po_hdr.printed: "N" for a PO never
//     printed, "Y" for one that was. A mismatch is an empty HTTP 500 on every
//     attempt. Read printed over OData first, and re-read it before each retry.
//   - A first print ("N") marks the PO printed.
//   - Status "New" (the same enum as /transaction), Type "Form", Keys: [].
//   - Classify the ErrorType/ErrorMessage envelope before the status code;
//     success is per document (StatusCode "Success" AND non-empty DocumentData).
//
// The pdfreport endpoint is not wrapped by P21Client, so this uses a raw
// HttpClient authenticated through the Common project's P21Config/P21Auth
// helpers (RecipeHelpers.CreateRawClientAsync).

using System.Text;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using static P21Examples.Recipes.RecipeHelpers;

namespace P21Examples.Recipes;

public static class ReprintPurchaseOrder
{
    // Generic placeholders — press Enter at each prompt to keep them.
    private const string CompanyId = "ACME";
    private const string PoNo = "500100";       // single PO: beg_po_no == end_po_no
    private const int Attempts = 3;             // report-engine faults are usually transient

    public static async Task RunAsync()
    {
        Console.WriteLine("Recipe - Print or Reprint a Purchase Order PDF (m_reprintpurchaseorders)");
        Console.WriteLine(new string('=', 60));

        var companyId = Ask("Company ID", CompanyId);
        var poNo = Ask("PO number", PoNo);

        PrintPayload("m_reprintpurchaseorders payload (POST /api/v2/process/pdfreport)",
                     BuildPayload(companyId, poNo, "<po_hdr.printed>"));
        Console.WriteLine("\nreprint_flag is read from po_hdr.printed at run time." +
                          " A first print marks the PO printed.");
        if (!ConfirmExecute())
            return;

        var (rawHttp, uiServer, baseUrl) = await CreateRawClientAsync();
        using var http = rawHttp;

        JToken? body = null;
        var flag = "N";
        for (var attempt = 1; attempt <= Attempts; attempt++)
        {
            flag = await GetPrintedFlagAsync(http, baseUrl, poNo);   // re-read before every try
            var response = await http.PostAsync($"{uiServer}/api/v2/process/pdfreport",
                new StringContent(BuildPayload(companyId, poNo, flag).ToString(Formatting.None),
                                  Encoding.UTF8, "application/json"));
            var text = await response.Content.ReadAsStringAsync();
            try { body = string.IsNullOrEmpty(text) ? null : JToken.Parse(text); }
            catch (JsonReaderException) { body = null; }

            // Classify the P21 error envelope BEFORE the status code — it can ride a 200.
            if (body is JObject env && env["ErrorMessage"] != null) break;
            if (response.IsSuccessStatusCode && body is JArray) break;

            Console.WriteLine($"  attempt {attempt} (reprint_flag={flag}): " +
                              $"HTTP {(int)response.StatusCode}, {text.Length}-char body");
            await Task.Delay(TimeSpan.FromSeconds(0.5 * attempt));
        }
        Console.WriteLine($"reprint_flag sent: {flag} (po_hdr.printed)");

        if (body is JObject envelope && envelope["ErrorMessage"] != null)
        {
            Console.WriteLine($"{envelope["ErrorType"]}: {envelope["ErrorMessage"]}");
            return;
        }
        if (body is not JArray documents || documents.Count == 0)
        {
            Console.WriteLine($"No documents after {Attempts} attempts — re-check the PO, " +
                              "company_id and the PO's printed flag.");
            return;
        }

        // Success is per document: StatusCode "Success" AND non-empty DocumentData.
        var saved = 0;
        foreach (var doc in documents.OfType<JObject>())
        {
            var status = doc["ResponseStatus"]?["StatusCode"]?.ToString();
            var data = doc["DocumentData"]?.ToString();
            if (status != "Success" || string.IsNullOrEmpty(data))
            {
                Console.WriteLine($"  document failed: {doc["ResponseStatus"]?["Message"]}");
                continue;
            }
            var pdf = Convert.FromBase64String(data);
            // FileName's number is a document number, not necessarily the PO number.
            var fileName = Path.GetFileName(doc["FileName"]?.ToString() ?? $"PO_{poNo}.pdf");
            await File.WriteAllBytesAsync(fileName, pdf);
            saved++;
            var isPdf = pdf.Length > 4 && Encoding.ASCII.GetString(pdf, 0, 4) == "%PDF";
            Console.WriteLine($"  saved {Path.GetFullPath(fileName)} " +
                              $"({new FileInfo(fileName).Length} bytes, starts with %PDF: {isPdf})");
        }

        // Read-back: a successful print leaves the PO marked printed.
        var after = await GetPrintedFlagAsync(http, baseUrl, poNo);
        Console.WriteLine($"po_hdr.printed after: {after}");
        Console.WriteLine($"Verify: {(saved > 0 && after == "Y" ? "OK" : "CHECK")} ({saved} document(s) saved)");
    }

    /// <summary>The report payload: Status "New", Type "Form", Keys [].</summary>
    private static JObject BuildPayload(string companyId, string poNo, string reprintFlag) => new()
    {
        ["Name"] = "m_reprintpurchaseorders",
        ["Transactions"] = new JArray { new JObject
        {
            ["DataElements"] = new JArray { new JObject
            {
                ["Keys"] = new JArray(),
                ["Name"] = "TABPAGE_1.poreportcriteriadw",
                ["Rows"] = new JArray { new JObject { ["Edits"] = new JArray
                {
                    Edit("company_id", companyId),   // criteria name; po_hdr stores company_no
                    Edit("beg_po_no", poNo),
                    Edit("end_po_no", poNo),
                    Edit("reprint_flag", reprintFlag),
                } } },
                ["Type"] = "Form",
            } },
            ["Status"] = "New",
        } },
        ["UseCodeValues"] = false,
    };

    /// <summary>reprint_flag must equal po_hdr.printed, or the report returns an empty 500.</summary>
    private static async Task<string> GetPrintedFlagAsync(HttpClient http, string baseUrl, string poNo)
    {
        var filter = Uri.EscapeDataString($"po_no eq {poNo}");   // numeric: no quotes
        var response = await http.GetAsync(
            $"{baseUrl}/odataservice/odata/table/po_hdr?$filter={filter}&$select=po_no,printed");
        response.EnsureSuccessStatusCode();
        var rows = (JArray)JObject.Parse(await response.Content.ReadAsStringAsync())["value"]!;
        if (rows.Count == 0)
            throw new InvalidOperationException($"PO {poNo} not found — check it before calling the report");
        return rows[0]["printed"]?.ToString() == "Y" ? "Y" : "N";
    }

    private static string Ask(string label, string fallback)
    {
        Console.Write($"{label} [{fallback}]: ");
        var answer = Console.ReadLine()?.Trim();
        return string.IsNullOrEmpty(answer) ? fallback : answer;
    }
}
