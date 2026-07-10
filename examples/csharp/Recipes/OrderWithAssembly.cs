// Recipe: Order with an Assembly Line
// Docs:   docs/recipes/order-with-assembly.md
//
// Enter a sales order interactively when a line is an assembly that must
// explode into components and/or spawn a production order. The Transaction
// API auto-answers the "add as assembly?" prompt No (killing the explode),
// so this flow uses the Interactive API with response-window handling ON
// and answers the prompts itself.
//
// Key rules (all verified end-to-end — see the recipe page):
//   - Session must start with ResponseWindowHandlingEnabled: true.
//   - Date fields fire the w_response_common date-cascade prompt even on a
//     brand-new order — answer cb_ok against the POPUP's window ID.
//   - Assembly prompt buttons: cb_1 = Yes (explode) / cb_2 = No / cb_3 = Cancel.
//   - Set the first line on the EXISTING items row (no /v2/row add for it).
//   - PUT /v2/data takes the bare window-ID string as the JSON body.
//   - /v2/window and /v2/data take ?id=; /v2/tools takes ?windowId=.
//   - Status may be an integer or a string (3 or "Blocked") — handle both.
//   - DatawindowName is required in v2 change requests on P21 25.2+.
//
// This recipe drives popup windows directly, which P21Client's typed helpers
// don't cover — it uses a raw HttpClient authenticated through the Common
// project's P21Config/P21Auth helpers (RecipeHelpers.CreateRawClientAsync).

using System.Text;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using static P21Examples.Recipes.RecipeHelpers;

namespace P21Examples.Recipes;

public static class OrderWithAssembly
{
    private const string CustomerId = "100198";
    private const string AssemblyItemId = "WIDGET-001";
    private const string Quantity = "5";

    public static async Task RunAsync()
    {
        Console.WriteLine("Recipe - Order with an Assembly Line (Interactive API)");
        Console.WriteLine(new string('=', 60));

        // Dry run = print the planned call sequence; EXECUTE = run it.
        Console.WriteLine(@"
Planned call sequence:
  1. POST /api/ui/interactive/sessions   {ResponseWindowHandlingEnabled: true}
  2. POST /api/ui/interactive/v2/window  {ServiceName: ""Order""}
  3. PUT  /v2/change TABPAGE_1/order: quote=OFF, sales_loc_id=10,
          source_loc_id=10, customer_id=" + CustomerId + @", ship_to_id=200,
          contact_id=300, order_date=2030-01-05 (answer cb_ok),
          requested_date=2030-01-06 (answer cb_ok), po_no=PO-TEST-001,
          taker=JSMITH
  4. PUT  /v2/tab  -> TP_ITEMS
  5. PUT  /v2/change TP_ITEMS/items: oe_order_item_id=" + AssemblyItemId + @"
          (assembly prompt -> answer cb_1 = Yes, explode / link prod order)
  6. PUT  /v2/change TP_ITEMS/items: unit_quantity=" + Quantity + @"
  7. PUT  /v2/data (bare window-ID string body) -> answer follow-on prompts
  8. PUT  /v2/tab -> TABPAGE_1, GET /v2/data?id={windowId} -> read order_no
  9. DELETE /v2/window?id={windowId}, DELETE /sessions
Verify: OData oe_line for the new order_no -> assembly codes
        (B kit parent, N component, P production-order line, S build-to-stock)");

        if (!ConfirmExecute())
            return;

        var (rawHttp, uiServer, baseUrl) = await CreateRawClientAsync();
        using var http = rawHttp;
        var iapi = $"{uiServer}/api/ui/interactive";

        // 1. Session with response-window handling ON
        var sessBody = new JObject { ["ResponseWindowHandlingEnabled"] = true };
        (await http.PostAsync($"{iapi}/sessions",
            new StringContent(sessBody.ToString(), Encoding.UTF8, "application/json")))
            .EnsureSuccessStatusCode();
        Console.WriteLine("\nSession started (ResponseWindowHandlingEnabled: true)");

        // 2. Open the Order window
        var winBody = new JObject { ["ServiceName"] = "Order" };
        var winResp = await http.PostAsync($"{iapi}/v2/window",
            new StringContent(winBody.ToString(), Encoding.UTF8, "application/json"));
        winResp.EnsureSuccessStatusCode();
        var windowId = JObject.Parse(
            await winResp.Content.ReadAsStringAsync())["WindowId"]!.ToString();
        Console.WriteLine($"Order window opened: {windowId}");

        try
        {
            // 3. Header -- TABPAGE_1 / datawindow "order". quote OFF = real order.
            await ChangeAsync(http, iapi, windowId, "TABPAGE_1", "order", "quote", "OFF");
            await ChangeAsync(http, iapi, windowId, "TABPAGE_1", "order", "sales_loc_id", "10");
            await ChangeAsync(http, iapi, windowId, "TABPAGE_1", "order", "source_loc_id", "10");
            await ChangeAsync(http, iapi, windowId, "TABPAGE_1", "order", "customer_id", CustomerId);
            await ChangeAsync(http, iapi, windowId, "TABPAGE_1", "order", "ship_to_id", "200");
            await ChangeAsync(http, iapi, windowId, "TABPAGE_1", "order", "contact_id", "300");
            // Dates fire the w_response_common date-cascade prompt even on a NEW order
            await ChangeAsync(http, iapi, windowId, "TABPAGE_1", "order", "order_date", "2030-01-05", "cb_ok");
            await ChangeAsync(http, iapi, windowId, "TABPAGE_1", "order", "requested_date", "2030-01-06", "cb_ok");
            await ChangeAsync(http, iapi, windowId, "TABPAGE_1", "order", "po_no", "PO-TEST-001");
            await ChangeAsync(http, iapi, windowId, "TABPAGE_1", "order", "taker", "JSMITH"); // else = API user
            Console.WriteLine("Header fields set");

            // 4. Lines tab
            var tabBody = new JObject { ["WindowId"] = windowId, ["PageName"] = "TP_ITEMS" };
            (await http.PutAsync($"{iapi}/v2/tab",
                new StringContent(tabBody.ToString(), Encoding.UTF8, "application/json")))
                .EnsureSuccessStatusCode();

            // 5. Item on the EXISTING items row; assembly prompt: cb_1 = Yes (explode)
            await ChangeAsync(http, iapi, windowId, "TP_ITEMS", "items",
                "oe_order_item_id", AssemblyItemId, "cb_1");
            // 6. Quantity
            await ChangeAsync(http, iapi, windowId, "TP_ITEMS", "items",
                "unit_quantity", Quantity);
            Console.WriteLine($"Line entered: {AssemblyItemId} x {Quantity}");

            // 7. Save -- v2 body is the bare window-ID JSON string (an object => 422)
            var saveResp = await http.PutAsync($"{iapi}/v2/data",
                new StringContent(JsonConvert.SerializeObject(windowId),
                    Encoding.UTF8, "application/json"));
            saveResp.EnsureSuccessStatusCode();
            var result = JObject.Parse(await saveResp.Content.ReadAsStringAsync());
            while (IsBlocked(result))  // follow-on prompts: answer with proceed button
                result = await AnswerResponseWindowsAsync(http, iapi, result);
            if (result["Status"]?.ToString() is "2" or "Failure")
                throw new InvalidOperationException($"Save failed: {result["Messages"]}");
            Console.WriteLine("Order saved");

            // 8. Read order_no back -- /v2/data returns the ACTIVE surface, so
            //    switch back to the header tab first.
            var backBody = new JObject { ["WindowId"] = windowId, ["PageName"] = "TABPAGE_1" };
            (await http.PutAsync($"{iapi}/v2/tab",
                new StringContent(backBody.ToString(), Encoding.UTF8, "application/json")))
                .EnsureSuccessStatusCode();
            var dataResp = await http.GetAsync($"{iapi}/v2/data?id={windowId}");
            dataResp.EnsureSuccessStatusCode();

            string? orderNo = null;
            foreach (var dw in JArray.Parse(await dataResp.Content.ReadAsStringAsync()))
            {
                if (dw["Name"]?.ToString() != "order") continue;
                var columns = (dw["Columns"] as JArray)!.Select(c => c.ToString()).ToList();
                var row = (dw["Data"] as JArray)![(int?)dw["ActiveRow"] ?? 0];
                orderNo = row[columns.IndexOf("order_no")]?.ToString();
                Console.WriteLine($"Created order_no: {orderNo}");
            }

            // Verify: assembly codes on the saved lines
            // (B kit parent, N component, P production-order line, S build-to-stock)
            if (!string.IsNullOrEmpty(orderNo))
            {
                Console.WriteLine("\nVerify via OData (oe_line assembly codes):");
                Console.WriteLine(new string('-', 50));
                var filter = Uri.EscapeDataString($"order_no eq '{orderNo}'");
                var lineResp = await http.GetAsync(
                    $"{baseUrl}/odataservice/odata/table/oe_line?$filter={filter}");
                lineResp.EnsureSuccessStatusCode();
                var lines = (JArray)JObject.Parse(
                    await lineResp.Content.ReadAsStringAsync())["value"]!;
                foreach (var line in lines)
                    Console.WriteLine($"  line {line["line_no"]}: assembly={line["assembly"]} " +
                                      $"qty_ordered={line["qty_ordered"]}");
                Console.WriteLine("  For auto_create_prod_order items, also check " +
                                  "prod_order_line_link (trans_type 'O').");
            }
        }
        finally
        {
            // 9. Clean up (window uses ?id=; sessions endpoint takes no parameter)
            await http.DeleteAsync($"{iapi}/v2/window?id={windowId}");
            await http.DeleteAsync($"{iapi}/sessions");
            Console.WriteLine("\nWindow closed, session ended");
        }
    }

    /// <summary>Status may be an integer or a string form — handle both.</summary>
    private static bool IsBlocked(JObject r) =>
        r["Status"]?.ToString() is "3" or "Blocked";

    /// <summary>Window IDs of popups opened by the last action.
    /// Events[].Data is a key-value list: [{"Key": "windowid", "Value": "..."}].</summary>
    private static List<string> PopupIds(JObject r) =>
        (r["Events"] as JArray ?? new JArray())
            .Where(e => e["Name"]?.ToString() == "windowopened")
            .SelectMany(e => e["Data"] as JArray ?? new JArray())
            .Where(kv => kv["Key"]?.ToString() == "windowid")
            .Select(kv => kv["Value"]!.ToString())
            .ToList();

    /// <summary>
    /// Answer every popup the last action opened, then return the last result.
    /// Discovers buttons via GET /v2/tools?windowId= (the tools endpoint takes
    /// ?windowId=, NOT ?id=), then clicks via POST /v2/tools with the POPUP's
    /// window ID. If button is null, picks the first proceed-style button.
    /// </summary>
    private static async Task<JObject> AnswerResponseWindowsAsync(
        HttpClient http, string iapi, JObject result, string? button = null)
    {
        foreach (var popupId in PopupIds(result))
        {
            var toolsResp = await http.GetAsync($"{iapi}/v2/tools?windowId={popupId}");
            toolsResp.EnsureSuccessStatusCode();
            var available = JArray.Parse(await toolsResp.Content.ReadAsStringAsync())
                .Select(t => (t["Name"] ?? t["ToolName"])?.ToString()).ToList();
            var pick = button
                ?? new[] { "cb_ok", "cb_1", "cb_yes" }.FirstOrDefault(available.Contains)
                ?? throw new InvalidOperationException(
                    $"Popup {popupId}: buttons [{string.Join(", ", available)}]");
            Console.WriteLine($"  Popup {popupId}: answering {pick}");

            var clickBody = new JObject { ["WindowId"] = popupId, ["ToolName"] = pick };
            var clickResp = await http.PostAsync($"{iapi}/v2/tools",
                new StringContent(clickBody.ToString(), Encoding.UTF8, "application/json"));
            clickResp.EnsureSuccessStatusCode();
            result = JObject.Parse(await clickResp.Content.ReadAsStringAsync());
        }
        return result;
    }

    /// <summary>Change one field; answer the popup it triggers (if any) with answer.</summary>
    private static async Task<JObject> ChangeAsync(
        HttpClient http, string iapi, string windowId, string tab, string dw,
        string field, string value, string? answer = null)
    {
        var body = new JObject
        {
            ["WindowId"] = windowId,
            ["List"] = new JArray { new JObject
            {
                ["TabName"] = tab,
                ["DatawindowName"] = dw,   // required on 25.2+
                ["FieldName"] = field,
                ["Value"] = value,
            }},
        };
        var resp = await http.PutAsync($"{iapi}/v2/change",
            new StringContent(body.ToString(), Encoding.UTF8, "application/json"));
        resp.EnsureSuccessStatusCode();
        var result = JObject.Parse(await resp.Content.ReadAsStringAsync());
        if (result["Status"]?.ToString() is "2" or "Failure")
            throw new InvalidOperationException($"{field}: {result["Messages"]}");
        return IsBlocked(result)
            ? await AnswerResponseWindowsAsync(http, iapi, result, answer)
            : result;
    }
}
