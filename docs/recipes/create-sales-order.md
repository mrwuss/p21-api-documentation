# Create a Sales Order

Create a sales order — header plus line items — in one stateless Transaction API call.

**API:** Transaction · **Service:** `Order` · **Deep dive:** [Create Order](../03-Transaction-API.md#create-order) · [Order Service Gotchas](../03-Transaction-API.md#order-service-gotchas) · **Full schema:** [Order.json](../../definitions/Order.json)

> **There is a second path.** `POST /api/sales/orders/` creates an order from plain domain JSON — no `DataElements`, no string-typed values — contributed and tested on 25.2 ([05 § Creating an Order](../05-Entity-API.md#creating-an-order-post-apisalesorders)). It is the lighter payload; this Transaction recipe is the one verified here, reports errors in a documented envelope, and creates many orders per call. The [side-by-side comparison](../05-Entity-API.md#rest-vs-the-transaction-api-for-order-creation) picks between them.

## Prerequisites

- P21 credentials — the complete example below authenticates itself; nothing to install but `httpx` (Python) or a bare `net9.0` console project (C#).
- The customer, ship-to, contact, and items already exist; the items are stocked at the source location.
- **No assembly lines.** If a line should explode into components or spawn a production order, the Transaction API auto-answers the *"add as assembly?"* prompt **No** and kills the explode — use the [order-with-assembly](order-with-assembly.md) recipe for those.

## Payload

Two DataElements: the header form and the items list. Names come from the [service definition](../../definitions/Order.json) — `TABPAGE_1.order` (Form, datawindow `d_oe_header`, key `order_no`) and `TP_ITEMS.items` (List, datawindow `d_dw_oe_line_dataentry`, key `oe_order_item_id`).

The minimal example in the manual sends only `customer_id` + one item, but a **realistic header sets all of the fields below** — in particular `source_loc_id`, without which the save fails with a *"Jurisdiction ID for Order Header Tax"* error (see Gotchas).

```json
POST {ui_server}/api/v2/transaction

{
    "Name": "Order",
    "UseCodeValues": false,
    "Transactions": [{
        "Status": "New",
        "DataElements": [
            {
                "Name": "TABPAGE_1.order",
                "Type": "Form",
                "Keys": [],
                "Rows": [{
                    "Edits": [
                        {"Name": "customer_id",    "Value": "100198"},
                        {"Name": "sales_loc_id",   "Value": "10"},
                        {"Name": "source_loc_id",  "Value": "10"},
                        {"Name": "order_date",     "Value": "2030-01-05"},
                        {"Name": "requested_date", "Value": "2030-01-06"},
                        {"Name": "po_no",          "Value": "PO-TEST-001"},
                        {"Name": "taker",          "Value": "JSMITH"},
                        {"Name": "ship_to_id",     "Value": "200"},
                        {"Name": "contact_id",     "Value": "300"}
                    ],
                    "RelativeDateEdits": []
                }]
            },
            {
                "Name": "TP_ITEMS.items",
                "Type": "List",
                "Keys": [],
                "Rows": [
                    {
                        "Edits": [
                            {"Name": "oe_order_item_id", "Value": "WIDGET-001"},
                            {"Name": "unit_quantity",    "Value": "5"}
                        ],
                        "RelativeDateEdits": []
                    },
                    {
                        "Edits": [
                            {"Name": "oe_order_item_id", "Value": "WIDGET-002"},
                            {"Name": "unit_quantity",    "Value": "2"}
                        ],
                        "RelativeDateEdits": []
                    }
                ]
            }
        ]
    }]
}
```

Do **not** send `company_id` — it is a disabled column on the Order window. For every other field the service accepts, load [`definitions/Order.json`](../../definitions/Order.json).

## Complete example

<!-- tabs -->
```python
"""Create a sales order (header + two lines), then read the order back."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
CUSTOMER_ID = "100198"
SALES_LOC_ID = "10"
SOURCE_LOC_ID = "10"                      # required in practice (see Gotchas)
ORDER_DATE = "2030-01-05"
REQUESTED_DATE = "2030-01-06"             # must be AFTER order_date
PO_NO = "PO-TEST-001"
TAKER = "JSMITH"
SHIP_TO_ID = "200"
CONTACT_ID = "300"
LINES = [("WIDGET-001", "5"), ("WIDGET-002", "2")]   # (oe_order_item_id, unit_quantity)
# ---------------------------------------------------------------------------


def get_token(client: httpx.Client) -> str:
    """v2 token endpoint — credentials go in the body, never in headers."""
    r = client.post(
        f"{BASE_URL}/api/security/token/v2",
        json={"username": USERNAME, "password": PASSWORD},
        headers={"Accept": "application/json"},
    )
    r.raise_for_status()
    try:
        return r.json()["AccessToken"]
    except (ValueError, KeyError):  # some middleware answers in XML
        match = re.search(r"<AccessToken>([^<]+)</AccessToken>", r.text)
        if not match:
            raise ValueError(f"No AccessToken in response: {r.text[:200]}") from None
        return match.group(1)


def get_ui_server(client: httpx.Client, token: str) -> str:
    """Transaction and Interactive calls go to the UI server, not BASE_URL."""
    r = client.get(
        f"{BASE_URL}/api/ui/router/v1/?urlType=external",  # trailing slash avoids a 307
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )
    r.raise_for_status()
    try:
        return r.json()["Url"].rstrip("/")
    except (ValueError, KeyError):
        match = re.search(r"<Url>([^<]+)</Url>", r.text)
        if not match:
            raise ValueError(f"No Url in router response: {r.text[:200]}") from None
        return match.group(1).rstrip("/")


with httpx.Client(verify=VERIFY_SSL, timeout=120, follow_redirects=True) as client:
    token = get_token(client)
    ui_server = get_ui_server(client, token)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",       # 2026.1 returns an empty 500 without this
        "Content-Type": "application/json",
    }

    payload = {
        "Name": "Order",
        "UseCodeValues": False,
        "Transactions": [{
            "Status": "New",
            "DataElements": [
                {
                    "Name": "TABPAGE_1.order",
                    "Type": "Form",
                    "Keys": [],
                    "Rows": [{
                        "Edits": [
                            {"Name": "customer_id",    "Value": CUSTOMER_ID},
                            {"Name": "sales_loc_id",   "Value": SALES_LOC_ID},
                            {"Name": "source_loc_id",  "Value": SOURCE_LOC_ID},
                            {"Name": "order_date",     "Value": ORDER_DATE},
                            {"Name": "requested_date", "Value": REQUESTED_DATE},
                            {"Name": "po_no",          "Value": PO_NO},
                            {"Name": "taker",          "Value": TAKER},
                            {"Name": "ship_to_id",     "Value": SHIP_TO_ID},
                            {"Name": "contact_id",     "Value": CONTACT_ID},
                        ],
                        "RelativeDateEdits": [],
                    }],
                },
                {
                    "Name": "TP_ITEMS.items",
                    "Type": "List",
                    "Keys": [],
                    "Rows": [
                        {"Edits": [
                            {"Name": "oe_order_item_id", "Value": item_id},
                            {"Name": "unit_quantity",    "Value": qty},
                        ], "RelativeDateEdits": []}
                        for item_id, qty in LINES
                    ],
                },
            ],
        }],
    }

    response = client.post(f"{ui_server}/api/v2/transaction",
                           headers=headers, json=payload)
    response.raise_for_status()
    result = response.json()

    # HTTP 200 even on failure -- check the Summary, never the status code
    summary = result["Summary"]
    print(f"Succeeded: {summary['Succeeded']}, Failed: {summary['Failed']}")
    if summary["Failed"] > 0 or summary["Succeeded"] == 0:
        for msg in result.get("Messages", []):
            print(msg)
        raise SystemExit("Order create failed")

    # The generated order_no comes back in the result rows of TABPAGE_1.order
    order_no = None
    for txn in result["Results"]["Transactions"]:
        if txn.get("Status") != "Passed":
            continue
        for element in txn.get("DataElements", []):
            if element.get("Name") != "TABPAGE_1.order":
                continue
            for row in element.get("Rows", []):
                for edit in row.get("Edits", []):
                    if edit.get("Name") == "order_no":
                        order_no = edit.get("Value")

    print(f"Created order_no: {order_no}")

    # Read back via OData -- Succeeded is not proof every value landed (see Verify)
    hdr = client.get(
        f"{BASE_URL}/odataservice/odata/table/oe_hdr",
        params={"$filter": f"order_no eq '{order_no}'"},
        headers=headers,
    )
    hdr.raise_for_status()
    for row in hdr.json()["value"]:
        print({
            "order_no": row.get("order_no"),
            "taker": row.get("taker"),
            "po_no": row.get("po_no"),
            "ship_to_id": row.get("ship_to_id"),
        })

    lines = client.get(
        f"{BASE_URL}/odataservice/odata/table/oe_line",
        params={"$filter": f"order_no eq '{order_no}'"},
        headers=headers,
    )
    lines.raise_for_status()
    line_count = len(lines.json()["value"])
    if line_count != len(LINES):
        print(f"WARNING: {line_count} oe_line rows, submitted {len(LINES)} -- "
              "a DynaChange auto-answer can drop a line while the transaction "
              "still reports Succeeded (see Gotchas)")
    else:
        print(f"All {line_count} lines present")
```

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string CustomerId = "100198";
const string SalesLocId = "10";
const string SourceLocId = "10";           // required in practice (see Gotchas)
const string OrderDate = "2030-01-05";
const string RequestedDate = "2030-01-06"; // must be AFTER order_date
const string PoNo = "PO-TEST-001";
const string Taker = "JSMITH";
const string ShipToId = "200";
const string ContactId = "300";
var lines = new (string ItemId, string Quantity)[]
{
    ("WIDGET-001", "5"),
    ("WIDGET-002", "2"),
};
// ---------------------------------------------------------------------------

var handler = new HttpClientHandler
{
    // Test tenants often present a self-signed cert. Delete this line in production.
    ServerCertificateCustomValidationCallback =
        HttpClientHandler.DangerousAcceptAnyServerCertificateValidator,
};
using var client = new HttpClient(handler) { Timeout = TimeSpan.FromMinutes(2) };
client.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));

var token = await GetTokenAsync(client);
var uiServer = await GetUiServerAsync(client, token);
client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);

var payload = new
{
    Name = "Order",
    UseCodeValues = false,
    Transactions = new[]
    {
        new
        {
            Status = "New",
            DataElements = new object[]
            {
                new
                {
                    Name = "TABPAGE_1.order",
                    Type = "Form",
                    Keys = Array.Empty<string>(),
                    Rows = new object[]
                    {
                        new
                        {
                            Edits = new[]
                            {
                                new { Name = "customer_id", Value = CustomerId },
                                new { Name = "sales_loc_id", Value = SalesLocId },
                                new { Name = "source_loc_id", Value = SourceLocId },
                                new { Name = "order_date", Value = OrderDate },
                                new { Name = "requested_date", Value = RequestedDate },
                                new { Name = "po_no", Value = PoNo },
                                new { Name = "taker", Value = Taker },
                                new { Name = "ship_to_id", Value = ShipToId },
                                new { Name = "contact_id", Value = ContactId },
                            },
                            RelativeDateEdits = Array.Empty<object>(),
                        },
                    },
                },
                new
                {
                    Name = "TP_ITEMS.items",
                    Type = "List",
                    Keys = Array.Empty<string>(),
                    Rows = lines.Select(l => (object)new
                    {
                        Edits = new[]
                        {
                            new { Name = "oe_order_item_id", Value = l.ItemId },
                            new { Name = "unit_quantity", Value = l.Quantity },
                        },
                        RelativeDateEdits = Array.Empty<object>(),
                    }).ToArray(),
                },
            },
        },
    },
};

using var response = await client.PostAsync(
    $"{uiServer}/api/v2/transaction",
    new StringContent(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json"));
response.EnsureSuccessStatusCode();
using var result = JsonDocument.Parse(await response.Content.ReadAsStringAsync());

// HTTP 200 even on failure -- check the Summary, never the status code
var summary = result.RootElement.GetProperty("Summary");
var succeeded = summary.GetProperty("Succeeded").GetInt32();
var failed = summary.GetProperty("Failed").GetInt32();
Console.WriteLine($"Succeeded: {succeeded}, Failed: {failed}");
if (failed > 0 || succeeded == 0)
{
    if (result.RootElement.TryGetProperty("Messages", out var messages))
    {
        Console.Error.WriteLine(messages);
    }
    throw new InvalidOperationException("Order create failed");
}

// The generated order_no comes back in the result rows of TABPAGE_1.order
var orderNo = ResultValue(result.RootElement, "TABPAGE_1.order", "order_no");
Console.WriteLine($"Created order_no: {orderNo}");

// Read back via OData -- Succeeded is not proof every value landed (see Verify)
foreach (var row in await ODataAsync(client, "oe_hdr", $"order_no eq '{orderNo}'"))
{
    Console.WriteLine(
        $"order_no={row.GetProperty("order_no")} taker={row.GetProperty("taker")} " +
        $"po_no={row.GetProperty("po_no")} ship_to_id={row.GetProperty("ship_to_id")}");
}

var lineRows = await ODataAsync(client, "oe_line", $"order_no eq '{orderNo}'");
Console.WriteLine(lineRows.Count != lines.Length
    ? $"WARNING: {lineRows.Count} oe_line rows, submitted {lines.Length} -- a DynaChange " +
      "auto-answer can drop a line while the transaction still reports Succeeded (see Gotchas)"
    : $"All {lineRows.Count} lines present");

// --- helpers ---------------------------------------------------------------

// Pull one echoed field out of a passed transaction's result rows.
static string? ResultValue(JsonElement root, string elementName, string fieldName)
{
    foreach (var txn in root.GetProperty("Results").GetProperty("Transactions").EnumerateArray())
    {
        if (txn.GetProperty("Status").GetString() != "Passed") continue;
        foreach (var element in txn.GetProperty("DataElements").EnumerateArray())
        {
            if (element.GetProperty("Name").GetString() != elementName) continue;
            foreach (var row in element.GetProperty("Rows").EnumerateArray())
            {
                foreach (var edit in row.GetProperty("Edits").EnumerateArray())
                {
                    if (edit.GetProperty("Name").GetString() == fieldName)
                    {
                        return edit.GetProperty("Value").GetString();
                    }
                }
            }
        }
    }
    return null;
}

static async Task<List<JsonElement>> ODataAsync(HttpClient client, string table, string filter)
{
    using var response = await client.GetAsync(
        $"{BaseUrl}/odataservice/odata/table/{table}?$filter=" + Uri.EscapeDataString(filter));
    response.EnsureSuccessStatusCode();
    using var doc = JsonDocument.Parse(await response.Content.ReadAsStringAsync());
    return doc.RootElement.GetProperty("value").EnumerateArray()
        .Select(x => x.Clone()).ToList();
}

// v2 token endpoint — credentials go in the body, never in headers.
static async Task<string> GetTokenAsync(HttpClient client)
{
    var payload = JsonSerializer.Serialize(new { username = Username, password = Password });
    var response = await client.PostAsync(
        $"{BaseUrl}/api/security/token/v2",
        new StringContent(payload, Encoding.UTF8, "application/json"));
    response.EnsureSuccessStatusCode();
    return ReadField(await response.Content.ReadAsStringAsync(), "AccessToken");
}

// Transaction and Interactive calls go to the UI server, not BaseUrl.
static async Task<string> GetUiServerAsync(HttpClient client, string token)
{
    using var request = new HttpRequestMessage(
        HttpMethod.Get, $"{BaseUrl}/api/ui/router/v1/?urlType=external");
    request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
    var response = await client.SendAsync(request);
    response.EnsureSuccessStatusCode();
    return ReadField(await response.Content.ReadAsStringAsync(), "Url").TrimEnd('/');
}

// Some middleware answers these two endpoints in XML even when asked for JSON.
static string ReadField(string payload, string field)
{
    try
    {
        var value = JsonDocument.Parse(payload).RootElement.GetProperty(field).GetString();
        if (!string.IsNullOrEmpty(value)) return value;
    }
    catch (Exception ex) when (ex is JsonException or KeyNotFoundException) { }

    var match = System.Text.RegularExpressions.Regex.Match(payload, $"<{field}>([^<]+)</{field}>");
    if (!match.Success)
        throw new InvalidOperationException(
            $"No {field} in response: {payload[..Math.Min(200, payload.Length)]}");
    return match.Groups[1].Value;
}
```
<!-- /tabs -->

> **Payload files:** [JSON](../../examples/payloads/json/create-sales-order.json) · [XML](../../examples/payloads/xml/create-sales-order.xml) — validator-verified, see [payloads README](../../examples/payloads/README.md).
>
> **End-to-end files** (runnable from the repo with a `.env`, dry-run by default): [`examples/python/recipes/create_sales_order.py`](../../examples/python/recipes/create_sales_order.py) · [`examples/csharp/Recipes/CreateSalesOrder.cs`](../../examples/csharp/Recipes/CreateSalesOrder.cs). The snippet above is self-contained; the files use the repo's shared `common` / `P21Examples.Common` helpers like every other example.

## Gotchas

All verified live — details in [Order Service Gotchas](../03-Transaction-API.md#order-service-gotchas):

- **`source_loc_id` is effectively required.** Omitting it fails with a *"Jurisdiction ID for Order Header Tax"* error — the tax jurisdiction does not auto-populate through the API the way it does in the UI.
- **`requested_date` must be after `order_date`.** The same date trips a date-cascade prompt, which the stateless API can't answer.
- **`company_id` is a disabled column** on the Order window — don't send it.
- **DynaChange prompts are auto-answered with the default** (usually "No"), which silently discards the affected line — e.g. *"order line does not have a PO Cost… proceed? [No]"*. On multi-item orders the remaining lines then cascade-fail. This is a P21 configuration matter (exempt the rule for the API user, or fix the data), not something a payload change can work around — see [DynaChange and Popup Handling](../03-Transaction-API.md#dynachange-and-popup-handling).
- **Assembly items cannot be entered via the Transaction API** when they should explode or spawn a production order — the *"add as assembly?"* prompt is auto-answered **No**, killing the explode. Use the [order-with-assembly](order-with-assembly.md) recipe (Interactive API) for those lines.
- **The same item on two lines collapses to one** with `Keys: []` — the items list folds rows on `oe_order_item_id`, last value wins, and the response still reports `Succeeded: 1`. Add `Keys: ["unit_quantity"]` (or another column that differs between the rows) when an order legitimately repeats an item — see [Keys — Row Identity and the Collapse Trap](../03-Transaction-API.md#keys-row-identity-and-the-collapse-trap).
- **HTTP 200 ≠ success.** The created `order_no` comes back in the result rows; check `Summary.Succeeded` and `Results.Transactions[].Status == "Passed"`, never the HTTP status. Transactions in one POST pass/fail independently.

## Verify

Read the order back — a `Succeeded` response is not proof every value landed:

```http
GET {base_url}/odataservice/odata/table/oe_hdr?$filter=order_no eq '1013938'
GET {base_url}/odataservice/odata/table/oe_line?$filter=order_no eq '1013938'
```

Confirm the header fields you sent (`taker`, `po_no`, dates, ship-to) and that **every** line row exists — a DynaChange auto-answer can drop a line while the transaction still reports `Succeeded` (see Gotchas).

> **Credit:** [Alex Westemeier](https://github.com/AWestemeier)
