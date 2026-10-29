// Shared plumbing for the end-to-end runbook classes:
// PurchaseReceiveVouch, SalesOrderToInvoice, NewAssembledPart,
// RebateAssemblyProgram and DisposeZeroValueStock. Each runs one
// docs/recipes/ runbook page step by step and reads every step back before
// the next one starts.
//
//   Runbook        - one authenticated connection: Transaction POSTs judged by
//                    Summary (never the HTTP status), OData read-backs, and
//                    Interactive sessions.
//   RunbookSession - an Interactive v2 driver (ResponseWindowHandlingEnabled)
//                    with the popup rules from OrderWithAssembly: discover a
//                    popup's buttons before pressing one, never answer blind.
//   RunbookSteps   - payload builders, prompts, and the steps more than one
//                    runbook runs: a Transaction sales order (quote OFF),
//                    Interactive order entry, the pick ticket, and the
//                    Shipping confirmation that creates the invoice.

using System.Globalization;
using System.Text;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using P21Examples.Common;

namespace P21Examples.Recipes;

/// <summary>One authenticated connection shared by every step of a runbook.</summary>
internal sealed class Runbook : IDisposable
{
    private const int TimeoutSeconds = 180;  // saves that ship, invoice or post are slow

    public HttpClient Http { get; }
    public string UiServer { get; }
    public string BaseUrl { get; }
    private readonly HttpClient _reader;

    private Runbook(HttpClient http, HttpClient reader, string uiServer, string baseUrl)
    {
        Http = http;
        _reader = reader;
        UiServer = uiServer;
        BaseUrl = baseUrl;
    }

    /// <summary>
    /// Authenticate and resolve the UI server. consumer = true writes as
    /// P21_CONSUMER_KEY acting for P21_CONSUMER_USERNAME (use the account
    /// whose P21 user has what a step needs, such as a Buyer ID). A consumer
    /// key's OData table allow-list can leave out a table a read-back needs
    /// (401), so read-backs use the password login when one is configured.
    /// </summary>
    public static async Task<Runbook> CreateAsync(bool consumer = false)
    {
        var config = P21Config.FromEnvironment();
        var hasPassword = !string.IsNullOrEmpty(config.Username) &&
                          !string.IsNullOrEmpty(config.Password);

        var writerConfig = config;
        if (consumer)
        {
            var key = Environment.GetEnvironmentVariable("P21_CONSUMER_KEY");
            var user = Environment.GetEnvironmentVariable("P21_CONSUMER_USERNAME");
            if (string.IsNullOrEmpty(key) || string.IsNullOrEmpty(user))
                throw new InvalidOperationException(
                    "Consumer auth needs P21_CONSUMER_KEY and P21_CONSUMER_USERNAME in .env");
            writerConfig = new P21Config(config.BaseUrl, user, "", key, config.VerifySsl);
        }

        var http = await NewClientAsync(writerConfig);
        var reader = consumer && hasPassword ? await NewClientAsync(config) : http;
        var uiServer = await P21Auth.GetUiServerUrlAsync(http, config.BaseUrl);
        Console.WriteLine($"UI Server: {uiServer}");
        return new Runbook(http, reader, uiServer, config.BaseUrl);
    }

    private static async Task<HttpClient> NewClientAsync(P21Config config)
    {
        var handler = new HttpClientHandler();
        if (!config.VerifySsl)
            handler.ServerCertificateCustomValidationCallback =
                HttpClientHandler.DangerousAcceptAnyServerCertificateValidator;
        var http = new HttpClient(handler) { Timeout = TimeSpan.FromSeconds(TimeoutSeconds) };
        var token = await P21Auth.GetTokenAsync(http, config);
        P21Auth.SetAuthHeaders(http, token.AccessToken);
        return http;
    }

    /// <summary>
    /// POST a Transaction and stop the runbook unless Summary says it passed.
    /// HTTP 200 comes back on failure too — only Summary.Succeeded/Failed count.
    /// </summary>
    public async Task<JObject> TransactionAsync(JObject payload, string label)
    {
        var resp = await Http.PostAsync($"{UiServer}/api/v2/transaction",
            new StringContent(payload.ToString(), Encoding.UTF8, "application/json"));
        resp.EnsureSuccessStatusCode();
        var result = JObject.Parse(await resp.Content.ReadAsStringAsync());
        var succeeded = (int?)result["Summary"]?["Succeeded"] ?? 0;
        var failed = (int?)result["Summary"]?["Failed"] ?? 0;
        Console.WriteLine($"  {label}: Succeeded={succeeded} Failed={failed}");
        foreach (var msg in result["Messages"] as JArray ?? new JArray())
            Console.WriteLine($"    {msg}");
        if (failed > 0 || succeeded == 0)
            throw new InvalidOperationException(
                $"{label} failed — read the tables before retrying: a Failed summary " +
                "does not always mean nothing was written");
        return result;
    }

    /// <summary>Read rows from the OData table surface.</summary>
    public async Task<JArray> ODataAsync(
        string table, string filter, string? select = null, string? orderBy = null, int? top = null)
    {
        var query = $"$filter={Uri.EscapeDataString(filter)}";
        if (select != null) query += $"&$select={Uri.EscapeDataString(select)}";
        if (orderBy != null) query += $"&$orderby={Uri.EscapeDataString(orderBy)}";
        if (top != null) query += $"&$top={top}";
        var resp = await _reader.GetAsync($"{BaseUrl}/odataservice/odata/table/{table}?{query}");
        resp.EnsureSuccessStatusCode();
        return (JArray)JObject.Parse(await resp.Content.ReadAsStringAsync())["value"]!;
    }

    /// <summary>Read exactly one row (the first by orderBy); throw when none matches.</summary>
    public async Task<JObject> OneAsync(
        string table, string filter, string? select = null, string? orderBy = null)
    {
        var rows = await ODataAsync(table, filter, select, orderBy, 1);
        if (rows.Count == 0)
            throw new InvalidOperationException($"Read-back found no {table} row for {filter}");
        return (JObject)rows[0];
    }

    /// <summary>inv_mast_uid for an item ID (OData has no joins — chain the uids).</summary>
    public async Task<string> ItemUidAsync(string itemId) =>
        (await OneAsync("inv_mast", $"item_id eq '{itemId}'", "inv_mast_uid"))["inv_mast_uid"]!.ToString();

    /// <summary>A new Interactive session with response-window handling on.</summary>
    public async Task<RunbookSession> SessionAsync()
    {
        var session = new RunbookSession(Http, $"{UiServer}/api/ui/interactive");
        await session.StartAsync();
        return session;
    }

    public void Dispose()
    {
        if (!ReferenceEquals(_reader, Http)) _reader.Dispose();
        Http.Dispose();
    }
}

/// <summary>Interactive v2 driver used by the runbooks.</summary>
internal sealed class RunbookSession
{
    private readonly HttpClient _http;
    private readonly string _iapi;

    public RunbookSession(HttpClient http, string iapi)
    {
        _http = http;
        _iapi = iapi;
    }

    private static StringContent Json(JToken body) =>
        new(body.ToString(Formatting.None), Encoding.UTF8, "application/json");

    public async Task StartAsync() =>
        (await _http.PostAsync($"{_iapi}/sessions",
            Json(new JObject { ["ResponseWindowHandlingEnabled"] = true })))
        .EnsureSuccessStatusCode();

    public async Task<string> OpenAsync(string serviceName)
    {
        var resp = await _http.PostAsync($"{_iapi}/v2/window",
            Json(new JObject { ["ServiceName"] = serviceName }));
        resp.EnsureSuccessStatusCode();
        return JObject.Parse(await resp.Content.ReadAsStringAsync())["WindowId"]!.ToString();
    }

    /// <summary>Close the window (?id=) and end the session.</summary>
    public async Task CloseAsync(string windowId)
    {
        await _http.DeleteAsync($"{_iapi}/v2/window?id={windowId}");
        await _http.DeleteAsync($"{_iapi}/sessions");
    }

    /// <summary>Status may be an integer or a string form — handle both.</summary>
    public static bool IsBlocked(JObject r) => r["Status"]?.ToString() is "3" or "Blocked";

    private static bool IsFailure(JObject r) => r["Status"]?.ToString() is "2" or "Failure";

    /// <summary>Window IDs of popups the last action opened.</summary>
    public static List<string> PopupIds(JObject r) =>
        (r["Events"] as JArray ?? new JArray())
            .Where(e => e["Name"]?.ToString() == "windowopened")
            .SelectMany(e => e["Data"] as JArray ?? new JArray())
            .Where(kv => kv["Key"]?.ToString() == "windowid")
            .Select(kv => kv["Value"]!.ToString())
            .ToList();

    /// <summary>Button names on a popup (GET /v2/tools takes ?windowId=, not ?id=).</summary>
    public async Task<List<string>> ToolsAsync(string popupId)
    {
        var resp = await _http.GetAsync($"{_iapi}/v2/tools?windowId={popupId}");
        resp.EnsureSuccessStatusCode();
        return JArray.Parse(await resp.Content.ReadAsStringAsync())
            .Select(t => (t["Name"] ?? t["ToolName"])?.ToString() ?? "").ToList();
    }

    /// <summary>Press one button on a popup.</summary>
    public async Task<JObject> ClickAsync(string popupId, string tool)
    {
        var resp = await _http.PostAsync($"{_iapi}/v2/tools",
            Json(new JObject { ["WindowId"] = popupId, ["ToolName"] = tool }));
        resp.EnsureSuccessStatusCode();
        return JObject.Parse(await resp.Content.ReadAsStringAsync());
    }

    /// <summary>
    /// Answer every popup the last action opened. A PO/RFQ wizard (cb_finish in
    /// its tools) that a save opens on its own is cancelled — nothing is
    /// committed before cb_next. Anything else gets the requested button, or
    /// the first proceed button.
    /// </summary>
    public async Task<JObject> AnswerAsync(JObject result, string? button = null)
    {
        foreach (var popupId in PopupIds(result))
        {
            var tools = await ToolsAsync(popupId);
            if (tools.Contains("cb_finish"))
            {
                Console.WriteLine("    (PO wizard opened by this save — cancelled before cb_next)");
                result = await ClickAsync(popupId, "cb_cancel");
                continue;
            }
            var pick = button ?? new[] { "cb_ok", "cb_1", "cb_yes" }.FirstOrDefault(tools.Contains);
            if (pick == null || !tools.Contains(pick))
                throw new InvalidOperationException(
                    $"Popup {popupId}: buttons [{string.Join(", ", tools)}], wanted {button}");
            result = await ClickAsync(popupId, pick);
        }
        return result;
    }

    /// <summary>Change one field; answer the popup it raises (if any) with answer.</summary>
    public async Task<JObject> ChangeAsync(
        string windowId, string tab, string dw, string field, string value, string? answer = null)
    {
        var body = new JObject
        {
            ["WindowId"] = windowId,
            ["List"] = new JArray { new JObject {
                ["TabName"] = tab, ["DatawindowName"] = dw,   // DatawindowName required on 25.2+
                ["FieldName"] = field, ["Value"] = value } },
        };
        var resp = await _http.PutAsync($"{_iapi}/v2/change", Json(body));
        var text = await resp.Content.ReadAsStringAsync();
        if (!resp.IsSuccessStatusCode)  // "Column is disabled" comes back as HTTP 400
            throw new InvalidOperationException($"{field}: HTTP {(int)resp.StatusCode} {text}");
        var result = JObject.Parse(text);
        if (IsFailure(result))
            throw new InvalidOperationException($"{field}: {result["Messages"]}");
        return IsBlocked(result) ? await AnswerAsync(result, answer) : result;
    }

    public async Task TabAsync(string windowId, string pageName) =>
        (await _http.PutAsync($"{_iapi}/v2/tab",
            Json(new JObject { ["WindowId"] = windowId, ["PageName"] = pageName })))
        .EnsureSuccessStatusCode();

    public async Task AddRowAsync(string windowId, string dw) =>
        (await _http.PostAsync($"{_iapi}/v2/row",
            Json(new JObject { ["WindowId"] = windowId, ["DatawindowName"] = dw })))
        .EnsureSuccessStatusCode();

    /// <summary>Save without answering anything — for saves that open a wizard.
    /// The v2 body is the bare window-ID JSON string, not an object.</summary>
    public async Task<JObject> SaveRawAsync(string windowId)
    {
        var resp = await _http.PutAsync($"{_iapi}/v2/data",
            new StringContent(JsonConvert.SerializeObject(windowId), Encoding.UTF8, "application/json"));
        resp.EnsureSuccessStatusCode();
        return JObject.Parse(await resp.Content.ReadAsStringAsync());
    }

    /// <summary>Save and answer every follow-on prompt with answer (or a proceed button).</summary>
    public async Task<JObject> SaveAsync(string windowId, string? answer = null)
    {
        var result = await SaveRawAsync(windowId);
        for (var i = 0; i < 50 && IsBlocked(result); i++)  // one prompt per unpriced $0 line
            result = await AnswerAsync(result, answer);
        if (IsFailure(result))
            throw new InvalidOperationException($"Save failed: {result["Messages"]}");
        return result;
    }

    /// <summary>Rows of one datawindow on the active surface of a window or popup.</summary>
    public async Task<List<Dictionary<string, string>>> RowsAsync(string windowId, string dwName)
    {
        var resp = await _http.GetAsync($"{_iapi}/v2/data?id={windowId}");
        resp.EnsureSuccessStatusCode();
        var rows = new List<Dictionary<string, string>>();
        foreach (var dw in JArray.Parse(await resp.Content.ReadAsStringAsync()))
        {
            if (dw["Name"]?.ToString() != dwName) continue;
            var columns = (dw["Columns"] as JArray)!.Select(c => c.ToString()).ToList();
            foreach (var row in dw["Data"] as JArray ?? new JArray())
                rows.Add(columns.Zip(row.Select(v => v.ToString()))
                    .ToDictionary(p => p.First, p => p.Second));
        }
        return rows;
    }
}

/// <summary>Payload builders, prompts, and the steps several runbooks share.</summary>
internal static class RunbookSteps
{
    public static string Today => DateTime.Today.ToString("yyyy-MM-dd");
    public static string DaysFromToday(int days) => DateTime.Today.AddDays(days).ToString("yyyy-MM-dd");

    /// <summary>Prompt for a value; Enter keeps the placeholder default.</summary>
    public static string Ask(string label, string defaultValue)
    {
        Console.Write($"  {label} [{defaultValue}]: ");
        var answer = Console.ReadLine()?.Trim();
        return string.IsNullOrEmpty(answer) ? defaultValue : answer;
    }

    public static JObject Edit(string name, string value) =>
        new() { ["Name"] = name, ["Value"] = value };

    /// <summary>One DataElement; rows is a list of edit lists.</summary>
    public static JObject Element(string name, string type, string[] keys, params JObject[][] rows) =>
        new()
        {
            ["Name"] = name, ["Type"] = type, ["Keys"] = new JArray(keys),
            ["Rows"] = new JArray(rows.Select(r => new JObject
            {
                ["Edits"] = new JArray(r), ["RelativeDateEdits"] = new JArray(),
            })),
        };

    /// <summary>A one-Transaction Status "New" payload (the only Status the enum accepts).</summary>
    public static JObject Payload(string service, bool ignoreDisabled, params JObject[] elements)
    {
        var body = new JObject
        {
            ["Name"] = service, ["UseCodeValues"] = false,
            ["Transactions"] = new JArray { new JObject {
                ["Status"] = "New", ["DataElements"] = new JArray(elements) } },
        };
        if (ignoreDisabled) body["IgnoreDisabled"] = true;  // top level only
        return body;
    }

    /// <summary>Read a field the server wrote back into a Transaction response's rows.</summary>
    public static string? ResultValue(JObject result, string elementName, string field) =>
        result.SelectTokens("Results.Transactions[*].DataElements[*]")
            .Where(de => de["Name"]?.ToString() == elementName)
            .SelectMany(de => de.SelectTokens("Rows[*].Edits[*]"))
            .Where(e => e["Name"]?.ToString() == field && !string.IsNullOrEmpty(e["Value"]?.ToString()))
            .Select(e => e["Value"]!.ToString())
            .FirstOrDefault();

    public static decimal Num(JToken? t) =>
        decimal.Parse(t?.ToString() ?? "0", NumberStyles.Float, CultureInfo.InvariantCulture);

    public static string Fmt(decimal d) => d.ToString("0.######", CultureInfo.InvariantCulture);

    /// <summary>Print one read-back comparison; throw on a mismatch.</summary>
    public static void Check(string label, object? actual, object expected)
    {
        var ok = string.Equals(actual?.ToString(), expected.ToString(), StringComparison.Ordinal);
        Console.WriteLine($"    {label} = {actual} (expected {expected}) -> {(ok ? "OK" : "MISMATCH")}");
        if (!ok) throw new InvalidOperationException($"Read-back mismatch on {label}");
    }

    /// <summary>
    /// Transaction sales order, header plus every line in one POST. quote = OFF
    /// goes first: when the API user's default is "quote", a header without it
    /// saves a quote, and a quote refuses a pick ticket. A null price leaves
    /// unit_price unset so a contract price can bind.
    /// </summary>
    public static JObject BuildOrderPayload(
        string customer, string shipTo, string contact, string salesLoc, string sourceLoc,
        string orderDate, string requestedDate, string poNo, string taker,
        IEnumerable<(string Item, string Qty, string? Price)> lines)
    {
        var header = new[]
        {
            Edit("quote", "OFF"), Edit("customer_id", customer),
            Edit("sales_loc_id", salesLoc), Edit("source_loc_id", sourceLoc),
            Edit("order_date", orderDate), Edit("requested_date", requestedDate),
            Edit("po_no", poNo), Edit("taker", taker),
            Edit("ship_to_id", shipTo), Edit("contact_id", contact),
        };
        var rows = lines.Select(l =>
        {
            var row = new List<JObject> { Edit("oe_order_item_id", l.Item), Edit("unit_quantity", l.Qty) };
            if (l.Price != null) row.Add(Edit("unit_price", l.Price));
            return row.ToArray();
        }).ToArray();
        return Payload("Order", false,
            Element("TABPAGE_1.order", "Form", Array.Empty<string>(), header),
            Element("TP_ITEMS.items", "List", Array.Empty<string>(), rows));
    }

    /// <summary>Print the sales-order pick ticket: Order keyed on order_no + print_tix ON.</summary>
    public static JObject BuildPrintTixPayload(string orderNo) =>
        Payload("Order", false,
            Element("TABPAGE_1.order", "Form", new[] { "order_no" }, new[] { Edit("order_no", orderNo) }),
            Element("TP_FRONTCOUNTER.tp_frontcounter", "Form", Array.Empty<string>(),
                new[] { Edit("print_tix", "ON") }));

    /// <summary>
    /// Enter and save a sales order in the Interactive Order window; return its
    /// order_no. quote = OFF first; both dates answer the date-cascade prompt
    /// cb_ok; the first line uses the existing row, later lines POST /v2/row;
    /// entering an item answers "add as assembly?" No (cb_2). The window clears
    /// after the save, so the order is found by its customer PO number.
    /// </summary>
    public static async Task<string> EnterOrderAsync(
        Runbook rb, (string Field, string Value)[] header, (string Field, string Value)[][] lines,
        string? salesrep = null, bool hold = false)
    {
        var session = await rb.SessionAsync();
        var windowId = await session.OpenAsync("Order");
        try
        {
            await session.ChangeAsync(windowId, "TABPAGE_1", "order", "quote", "OFF");
            foreach (var (field, value) in header)
                await session.ChangeAsync(windowId, "TABPAGE_1", "order", field, value,
                    field.EndsWith("_date") ? "cb_ok" : null);
            if (salesrep != null)
            {
                await session.TabAsync(windowId, "TP_SALESREPS");
                await session.ChangeAsync(windowId, "TP_SALESREPS", "tp_salesreps", "salesrep_id", salesrep);
                await session.TabAsync(windowId, "TABPAGE_1");
            }
            if (hold)
                await session.ChangeAsync(windowId, "TABPAGE_1", "order", "packing_basis", "Hold");
            await session.TabAsync(windowId, "TP_ITEMS");
            for (var i = 0; i < lines.Length; i++)
            {
                if (i > 0) await session.AddRowAsync(windowId, "items");
                foreach (var (field, value) in lines[i])
                    await session.ChangeAsync(windowId, "TP_ITEMS", "items", field, value,
                        field == "oe_order_item_id" ? "cb_2" : null);
            }
            await session.SaveAsync(windowId);
        }
        finally
        {
            await session.CloseAsync(windowId);
        }

        var poNo = header.First(h => h.Field == "po_no").Value;
        var hdr = await rb.OneAsync("oe_hdr", $"po_no eq '{poNo}'",
            "order_no,projected_order,packing_basis,taker", "oe_hdr_uid desc");
        Console.WriteLine($"    order_no = {hdr["order_no"]} (projected_order={hdr["projected_order"]}, " +
                          $"packing_basis={hdr["packing_basis"]}, taker={hdr["taker"]})");
        if (hdr["projected_order"]?.ToString() != "N")
            throw new InvalidOperationException("The order saved as a quote — quote = OFF did not take");
        return hdr["order_no"]!.ToString();
    }

    /// <summary>Print the pick ticket; return its number read back from oe_pick_ticket.
    /// The PDF's file name carries a different number — read the table.</summary>
    public static async Task<string> PrintPickTicketAsync(Runbook rb, string orderNo)
    {
        await rb.TransactionAsync(BuildPrintTixPayload(orderNo), "Pick ticket (print_tix)");
        var ticket = await rb.OneAsync("oe_pick_ticket",
            $"order_no eq '{orderNo}' and delete_flag eq 'N'",
            "pick_ticket_no,location_id,invoice_no", "pick_ticket_no desc");
        Console.WriteLine($"    pick_ticket_no = {ticket["pick_ticket_no"]} at location {ticket["location_id"]}");
        return ticket["pick_ticket_no"]!.ToString();
    }

    /// <summary>
    /// Confirm the shipment in the Interactive Shipping window; return the
    /// invoice_no. create_invoice defaults ON, so the save ships AND invoices.
    /// Proceed prompts (one per unpriced line on a $0 order) get cb_1 / cb_ok /
    /// cb_yes — never cb_cancel.
    /// </summary>
    public static async Task<string> ShipAndInvoiceAsync(Runbook rb, string pickTicketNo)
    {
        var session = await rb.SessionAsync();
        var windowId = await session.OpenAsync("Shipping");
        try
        {
            await session.ChangeAsync(windowId, "TABPAGE_1", "tp_1_dw_1", "pick_ticket_no", pickTicketNo);
            await session.SaveAsync(windowId);
        }
        finally
        {
            await session.CloseAsync(windowId);
        }
        var ticket = await rb.OneAsync("oe_pick_ticket", $"pick_ticket_no eq {pickTicketNo}",
            "pick_ticket_no,ship_date,invoice_no");
        if (string.IsNullOrEmpty(ticket["invoice_no"]?.ToString()))
            throw new InvalidOperationException($"Pick ticket {pickTicketNo} has no invoice after the save");
        Console.WriteLine($"    shipped {ticket["ship_date"]}, invoice_no = {ticket["invoice_no"]}");
        return ticket["invoice_no"]!.ToString();
    }

    /// <summary>Read back the invoice header and lines; return the lines.</summary>
    public static async Task<JArray> PrintInvoiceAsync(Runbook rb, string invoiceNo)
    {
        var hdr = await rb.OneAsync("invoice_hdr", $"invoice_no eq '{invoiceNo}'",
            "invoice_no,order_no,total_amount");
        Console.WriteLine($"    invoice {hdr["invoice_no"]} for order {hdr["order_no"]}: total {hdr["total_amount"]}");
        var lines = await rb.ODataAsync("invoice_line", $"invoice_no eq '{invoiceNo}'",
            "line_no,item_id,qty_shipped,unit_price,cogs_amount,other_cost,commission_cost," +
            "invoice_line_uid,invoice_line_uid_parent", "line_no");
        foreach (var l in lines)
            Console.WriteLine($"      line {l["line_no"]} {l["item_id"]}: qty {l["qty_shipped"]} " +
                              $"price {l["unit_price"]} cogs {l["cogs_amount"]} other_cost {l["other_cost"]} " +
                              $"commission_cost {l["commission_cost"]}");
        return lines;
    }
}
