// Recipe: Production Order Runbook — Create to Invoice
// Docs:   docs/recipes/production-order-runbook.md
//
// The recipe page is a CHECKLIST, not a script: create the production order,
// log labor, print the pick ticket(s), confirm the pick, complete (receive)
// the order, and ship + invoice the linked sales order. This example prints
// that checklist as guidance and automates the one stage most people script
// first: generating the pick ticket with m_picktickets and reading the new
// ticket's status back via POST /api/v2/transaction/get.
//
// Key traps (all verified live — see the recipe page):
//   - Shell confirm: confirming a pick via a bare Transaction POST flips the
//     status to 1962 but qty_applied stays 0 and NO stock moves — confirm
//     through the Interactive API ProductionOrderPicking window.
//   - Labor must land on a pick ticket before completion.
//   - bin_cd and unit_quantity are two SEPARATE change calls at completion.
//   - Reports go to /api/v2/process/pdfreport, never /api/v2/transaction.
//
// Uses a raw HttpClient (Common P21Config/P21Auth) because pdfreport is not
// wrapped by P21Client.

using System.Text;
using System.Text.RegularExpressions;
using Newtonsoft.Json.Linq;
using static P21Examples.Recipes.RecipeHelpers;

namespace P21Examples.Recipes;

public static class ProductionOrderRunbook
{
    private const string ProdOrder = "1000123";     // production order number
    private const string StockLocation = "10";      // where the components stock (NOT necessarily the make location)

    public static async Task RunAsync()
    {
        Console.WriteLine("Recipe - Production Order Runbook (Create to Invoice)");
        Console.WriteLine(new string('=', 60));

        PrintChecklist();

        // ------------------------------------------------------------------
        // Automated stage: print the pick ticket and read back its status
        // ------------------------------------------------------------------
        Console.WriteLine("\nAutomated stage — Stage 3: generate the production pick ticket");
        Console.WriteLine(new string('-', 60));

        var report = new JObject
        {
            ["Name"] = "m_picktickets",
            ["UseCodeValues"] = true,  // m_picktickets REQUIRES code values; false returns HTTP 500
            ["Transactions"] = new JArray
            {
                new JObject
                {
                    ["Status"] = 0,    // reports use numeric 0, not "New"
                    ["DataElements"] = new JArray
                    {
                        new JObject
                        {
                            ["Keys"] = new JArray(),
                            ["Type"] = 0,
                            ["Name"] = "TABPAGE_1.tp_1_dw_1",
                            ["Rows"] = new JArray
                            {
                                new JObject
                                {
                                    ["Edits"] = new JArray
                                    {
                                        Edit("create_pick_ticket_type", "P"), // code "P" = Production Order
                                        Edit("beg_prod_order", ProdOrder),
                                        Edit("end_prod_order", ProdOrder),
                                        Edit("location_id", StockLocation),
                                    }
                                }
                            }
                        }
                    }
                }
            }
        };

        PrintPayload("m_picktickets payload (POST /api/v2/process/pdfreport)", report);
        Console.WriteLine(
            "\nNOTE: this WRITES — it creates the pick-ticket record at the stock" +
            " location in addition to returning the PDF.\n" +
            "Prerequisite: prod_order_hdr.printed = 'Y' (ProductionOrder transaction" +
            " with print_form = ON).");

        if (!ConfirmExecute())
            return;

        var (rawHttp, uiServer, _) = await CreateRawClientAsync();
        using var http = rawHttp;

        // --- 1. Generate the pick ticket (creates the record + returns the PDF) ---
        // NOT /api/v2/transaction (silent no-op there)
        var reportResp = await http.PostAsync(
            $"{uiServer}/api/v2/process/pdfreport",
            new StringContent(report.ToString(), Encoding.UTF8, "application/json"));
        var reportText = await reportResp.Content.ReadAsStringAsync();
        if (!reportResp.IsSuccessStatusCode)
        {
            Console.WriteLine($"HTTP {(int)reportResp.StatusCode}: {reportText}");
            return;
        }

        var reportBody = JToken.Parse(reportText);
        if (reportBody.Type != JTokenType.Array)  // errors come back as an envelope, not an array
        {
            Console.WriteLine($"Report failed: {reportBody["ErrorMessage"]}");
            return;
        }

        var doc = (JObject)((JArray)reportBody)[0];
        if (doc["ResponseStatus"]?["StatusCode"]?.ToString() != "Success" ||
            string.IsNullOrEmpty(doc["DocumentData"]?.ToString()))
        {
            Console.WriteLine($"Report failed: {doc["ResponseStatus"]?["Message"]}");
            return;
        }

        var fileName = doc["FileName"]!.ToString(); // e.g. "PPT123456 PRODUCTION_PICK_TICKET.pdf"
        await File.WriteAllBytesAsync(
            fileName, Convert.FromBase64String(doc["DocumentData"]!.ToString()));
        Console.WriteLine($"Saved {fileName}");

        // --- 2. Verify: read the new ticket back (number comes from the FileName) ---
        var match = Regex.Match(fileName, @"PPT(\d+)");
        if (!match.Success)
        {
            Console.WriteLine($"Could not parse a ticket number from '{fileName}'");
            return;
        }
        var ticketNo = match.Groups[1].Value;

        Console.WriteLine($"\nVerify: reading ticket {ticketNo} back via /transaction/get:");
        Console.WriteLine(new string('-', 50));

        var getPayload = new JObject
        {
            ["ServiceName"] = "ProductionOrderPicking",
            ["TransactionStates"] = new JArray
            {
                new JObject
                {
                    ["DataElementName"] = "TP_PRODPICKTICKETCONF.tp_prodpickticketconf",
                    ["Keys"] = new JArray
                    {
                        new JObject { ["Name"] = "prod_pick_ticket_number", ["Value"] = ticketNo }
                    }
                }
            }
        };

        var getResp = await http.PostAsync(
            $"{uiServer}/api/v2/transaction/get",
            new StringContent(getPayload.ToString(), Encoding.UTF8, "application/json"));
        getResp.EnsureSuccessStatusCode();
        var getResult = JObject.Parse(await getResp.Content.ReadAsStringAsync());

        foreach (var txn in getResult["Transactions"] as JArray ?? new JArray())
        foreach (var de in txn["DataElements"] as JArray ?? new JArray())
        foreach (var row in de["Rows"] as JArray ?? new JArray())
        {
            var fields = new Dictionary<string, string>();
            foreach (var edit in row["Edits"] as JArray ?? new JArray())
                fields[edit["Name"]!.ToString()] = edit["Value"]?.ToString() ?? "";
            if (fields.ContainsKey("row_status_flag"))
                // 702 = Open, 1962 = Confirmed, 1268 = Completed
                Console.WriteLine(
                    $"  Ticket {fields.GetValueOrDefault("prod_pick_ticket_number")} " +
                    $"for prod order {fields.GetValueOrDefault("prod_order_number")}: " +
                    $"status {fields.GetValueOrDefault("row_status_flag")} " +
                    "(702 Open / 1962 Confirmed / 1268 Completed)");
        }
    }

    private static void PrintChecklist()
    {
        Console.WriteLine(@"
Runbook checklist (each stage links to a deep dive in the recipe page):

  Stage 1 - Create the production order
    Path A: sales order auto-create (Interactive API when the line must
            explode — see OrderWithAssembly). Auto-create NETS against
            stock: on-hand means no production order spawns.
    Path B: direct build-to-stock via the ProductionOrder window
            (header source_loc_id; TABPAGE_17.tp_17_dw_17
            assembly_item_id + qty_to_make).
    Traps:  salesrep must be valid at the sales location; order date
            must differ from required date.

  Stage 2 - Log labor BEFORE printing (see RecordLaborTime)
    Trap:   labor added after printing (no reprint) sits at
            qty_on_pick_tickets = 0 and completion fails with
            ""components have a quantity used of 0"".

  Stage 3 - Print the pick ticket and form  [AUTOMATED BELOW]
    ProductionOrder transaction (print_pick_ticket/print_form = ON) or
    m_picktickets at POST /api/v2/process/pdfreport.
    Traps:  print_pick_ticket emits only at the MAKE location; never
            post m_* reports to /api/v2/transaction (silent no-op).

  Stage 4 - Confirm the pick (Interactive API ONLY)
    ProductionOrderPicking window, header key prod_pick_ticket_number,
    set row_status_flag = ""Confirm"", save. Confirm EVERY ticket.
    Trap:   a bare Transaction POST produces a SHELL confirm — status
            1962 but qty_applied = 0 and no stock moves.

  Stage 5 - Complete the order (production receipt)
    ProductionOrderProcessing window: qty_to_complete on the line, then
    bin_cd and unit_quantity on TABPAGE_ASSEMBLY_BIN as TWO SEPARATE
    change calls; optional new_cost per component; save (inv_tran PROP).
    Trap:   combining bin_cd and unit_quantity in one call drops the
            quantity.

  Stage 6 - Ship + invoice the linked sales order
    Order transaction with print_tix = ON (creates oe_pick_ticket), then
    the Shipping service keyed by pick_ticket_no — retrieve and save
    (create_invoice defaults ON, so the save ships AND invoices).
    Traps:  the item needs a packaging code; leave unit_price unset for
            contract pricing.

  Stage 7 - Fix quantity fallout (see InventoryAdjustment)

  Cost model: PROP receipt cost = components + labor posted BEFORE
  completion; shipment COGS is the moving average at ship time.");
    }
}
