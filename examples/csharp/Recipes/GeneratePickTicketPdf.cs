// Recipe: Generate Pick Ticket and PO PDFs
// Docs:   docs/recipes/generate-pick-ticket-pdf.md
//
// Generate a production-order pick ticket as a base64-encoded PDF via the
// dedicated report endpoint POST /api/v2/process/pdfreport (service
// m_picktickets). NOTE: m_picktickets is a WRITE — it creates the
// pick-ticket record at location_id AND returns its PDF in one call.
//
// Key rules (all verified live — see the recipe page):
//   - Wrong-endpoint trap: POST /api/v2/transaction accepts an m_* payload
//     and returns Succeeded but emits NOTHING. Reports go to
//     /api/v2/process/pdfreport.
//   - m_picktickets REQUIRES UseCodeValues: true and the code "P"
//     (Production Order); UseCodeValues: false returns HTTP 500.
//   - Status and Type are numeric 0 with Keys: [] — not the "New" shape.
//   - Prerequisite: prod_order_hdr.printed = 'Y' (run a ProductionOrder
//     transaction with print_form = ON first).
//   - Success is a JSON ARRAY; errors use the P21 error envelope
//     (ErrorType/ErrorMessage), not Summary/Messages.
//
// The pdfreport endpoint is not wrapped by P21Client, so this uses a raw
// HttpClient authenticated through the Common project's P21Config/P21Auth
// helpers (RecipeHelpers.CreateRawClientAsync).

using System.Text;
using Newtonsoft.Json.Linq;
using static P21Examples.Recipes.RecipeHelpers;

namespace P21Examples.Recipes;

public static class GeneratePickTicketPdf
{
    private const string ProdOrder = "1000123";  // production order number
    private const string LocationId = "10";      // location whose inventory the components pick from

    public static async Task RunAsync()
    {
        Console.WriteLine("Recipe - Generate Pick Ticket PDF (m_picktickets)");
        Console.WriteLine(new string('=', 60));

        var payload = new JObject
        {
            ["Name"] = "m_picktickets",
            ["UseCodeValues"] = true,   // required here -- false returns HTTP 500
            ["Transactions"] = new JArray
            {
                new JObject
                {
                    ["Status"] = 0,     // numeric 0 for report payloads
                    ["DataElements"] = new JArray
                    {
                        new JObject
                        {
                            ["Keys"] = new JArray(),  // always empty for reports
                            ["Type"] = 0,             // numeric 0 for report payloads
                            ["Name"] = "TABPAGE_1.tp_1_dw_1",
                            ["Rows"] = new JArray
                            {
                                new JObject
                                {
                                    ["Edits"] = new JArray
                                    {
                                        // code "P" = Production Order (label is rejected)
                                        Edit("create_pick_ticket_type", "P"),
                                        Edit("beg_prod_order", ProdOrder),
                                        Edit("end_prod_order", ProdOrder),
                                        Edit("location_id", LocationId),
                                    }
                                }
                            }
                        }
                    }
                }
            }
        };

        PrintPayload("m_picktickets payload (POST /api/v2/process/pdfreport)", payload);
        Console.WriteLine(
            "\nNOTE: this WRITES — it creates the pick-ticket record at the location" +
            " in addition to returning the PDF.");

        if (!ConfirmExecute())
            return;

        var (rawHttp, uiServer, _) = await CreateRawClientAsync();
        using var http = rawHttp;

        // ------------------------------------------------------------------
        // Write: generate the report (creates the ticket + returns the PDF)
        // ------------------------------------------------------------------
        var response = await http.PostAsync(
            $"{uiServer}/api/v2/process/pdfreport",  // NOT /api/v2/transaction
            new StringContent(payload.ToString(), Encoding.UTF8, "application/json"));
        var bodyText = await response.Content.ReadAsStringAsync();

        // Errors come back as the standard P21 error envelope (ErrorType/ErrorMessage),
        // NOT the Summary/Messages format used by /transaction.
        if (!response.IsSuccessStatusCode)
        {
            Console.WriteLine($"HTTP {(int)response.StatusCode}: {bodyText}");
            return;
        }

        var parsed = JToken.Parse(bodyText);
        if (parsed is JObject envelope && envelope["ErrorMessage"] != null)
        {
            Console.WriteLine($"{envelope["ErrorType"]}: {envelope["ErrorMessage"]}");
            return;
        }

        // Success is a JSON ARRAY -- even for a single document
        if (parsed is not JArray documents || documents.Count == 0)
        {
            Console.WriteLine($"No documents returned: {parsed}");
            return;
        }

        // ------------------------------------------------------------------
        // Save + verify each document
        // ------------------------------------------------------------------
        foreach (var doc in documents.OfType<JObject>())
        {
            var status = doc["ResponseStatus"]?["StatusCode"]?.ToString();
            var documentData = doc["DocumentData"]?.ToString();
            if (status != "Success" || string.IsNullOrEmpty(documentData))
            {
                var msg = doc["ResponseStatus"]?["Message"]?.ToString() ?? "Unknown error";
                Console.WriteLine($"Document failed: {msg}");
                continue;
            }

            var pdfBytes = Convert.FromBase64String(documentData);
            // FileName includes .pdf, e.g. "PPT<nnn> PRODUCTION_PICK_TICKET.pdf"
            var filename = doc["FileName"]?.ToString() ?? "pick_ticket.pdf";
            await File.WriteAllBytesAsync(filename, pdfBytes);
            Console.WriteLine($"Saved {filename} ({pdfBytes.Length} bytes)");

            // Verify: decoded bytes start with %PDF and content type is PDF
            var isPdf = pdfBytes.Length > 4 &&
                        pdfBytes[0] == (byte)'%' && pdfBytes[1] == (byte)'P' &&
                        pdfBytes[2] == (byte)'D' && pdfBytes[3] == (byte)'F';
            Console.WriteLine($"  Starts with %PDF: {(isPdf ? "yes" : "NO")}");
            Console.WriteLine($"  DocumentContentType: {doc["DocumentContentType"]}");
            Console.WriteLine($"  ResponseStatus.Message: {doc["ResponseStatus"]?["Message"]}");
        }

        Console.WriteLine(
            "\nTo prove the pick-ticket row landed, reprint it: run" +
            " m_reprintpicktickets with beg_prod_pick_ticket_no/end_prod_pick_ticket_no" +
            " set to the number from the FileName — a second PDF confirms the record.");
    }
}
