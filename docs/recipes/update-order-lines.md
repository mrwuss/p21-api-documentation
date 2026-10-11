# Modify an Existing Sales Order

Change a line's quantity in place and add a new line to an existing sales order — one stateless Transaction API POST, no session, no window.

**API:** Transaction · **Service:** `Order` · **Deep dive:** [Keys — Row Identity and the Collapse Trap](../03-Transaction-API.md#keys-row-identity-and-the-collapse-trap) · [Design for updates: line handles](../03-Transaction-API.md#design-for-updates-assign-your-own-line-handles) · **Full schema:** [Order.json](../../definitions/Order.json)

Everything here was verified live on 26.1 (August 2026) with `/transaction/get` read-backs: the in-place update, the insert, both together in one POST, and every gotcha below.

## Prerequisites

- P21 credentials — the complete example below authenticates itself; nothing to install but `httpx` (Python) or a bare `net8.0`-or-later console project (C#).
- An existing, editable order (not fully invoiced/closed) that is **not an RMA** — see the RMA gotcha below.
- **Know each target line's `user_line_no`.** It is the stable update key. If your integration created the order, you ideally [assigned handles at create time](../03-Transaction-API.md#design-for-updates-assign-your-own-line-handles); otherwise read them back first (see [Finding the handles](#finding-the-handles)).

## How it works

A keyed `Status: "New"` row is an [upsert](../03-Transaction-API.md#upsert-semantics-keyed-rows-insert-when-absent): when the key matches an existing row it **updates** that row, when it doesn't it **inserts** a new one. So one `TP_ITEMS.items` element keyed on `user_line_no` does both jobs — send an existing handle to edit that line, a new handle to add a line.

The header element does the *loading*: `Keys: ["order_no"]` with `order_no` as its only edit.

## Payload

Updates line `010` to quantity 4 and adds a new line `030` — in one transaction:

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
                "Keys": ["order_no"],
                "Rows": [{
                    "Edits": [
                        {"Name": "order_no", "Value": "1001234"}
                    ],
                    "RelativeDateEdits": []
                }]
            },
            {
                "Name": "TP_ITEMS.items",
                "Type": "List",
                "Keys": ["user_line_no"],
                "Rows": [
                    {
                        "Edits": [
                            {"Name": "user_line_no",     "Value": "010"},
                            {"Name": "oe_order_item_id", "Value": "WIDGET-001"},
                            {"Name": "unit_quantity",    "Value": "4"}
                        ],
                        "RelativeDateEdits": []
                    },
                    {
                        "Edits": [
                            {"Name": "user_line_no",     "Value": "030"},
                            {"Name": "oe_order_item_id", "Value": "WIDGET-002"},
                            {"Name": "unit_quantity",    "Value": "1"}
                        ],
                        "RelativeDateEdits": []
                    }
                ]
            }
        ]
    }]
}
```

> **Payload files** (validator-verified): [JSON](../../examples/payloads/json/update-order-lines.json) · [XML](../../examples/payloads/xml/update-order-lines.xml)

## Finding the handles

When you don't know the order's `user_line_no` values, read them back first — `POST /api/v2/transaction/get` returns every line with its handle:

```json
POST {ui_server}/api/v2/transaction/get

{
    "ServiceName": "Order",
    "TransactionStates": [{
        "DataElementName": "TABPAGE_1.order",
        "Keys": [{"Name": "order_no", "Value": "1001234"}]
    }]
}
```

Walk the response's `TP_ITEMS.items` rows and map `user_line_no` → (`oe_order_item_id`, `unit_quantity`). P21 auto-assigns `001`, `002`, … when the creator didn't.

## Complete example

<!-- tabs -->
```python
"""Modify an existing sales order: update a line in place and add a line, then read it back."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.example.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
ORDER_NO = "1001234"
# (user_line_no, oe_order_item_id, unit_quantity): an EXISTING handle updates
# that line in place, a NEW handle inserts a line.
LINES = [
    ("010", "WIDGET-001", "4"),
    ("030", "WIDGET-002", "1"),
]
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


def read_lines(client: httpx.Client, ui_server: str, headers: dict) -> list[dict]:
    """Read the order's lines back with /transaction/get -- the only proof."""
    r = client.post(
        f"{ui_server}/api/v2/transaction/get", headers=headers,
        json={"ServiceName": "Order", "TransactionStates": [{
            "DataElementName": "TABPAGE_1.order",
            "Keys": [{"Name": "order_no", "Value": ORDER_NO}],
        }]},
    )
    r.raise_for_status()
    for element in r.json()["Transactions"][0]["DataElements"]:
        if element["Name"] != "TP_ITEMS.items":
            continue
        rows = [{edit["Name"]: edit["Value"] for edit in row.get("Edits", [])}
                for row in element.get("Rows", [])]
        return [row for row in rows if row.get("oe_order_item_id")]
    return []


with httpx.Client(verify=VERIFY_SSL, timeout=120, follow_redirects=True) as client:
    token = get_token(client)
    ui_server = get_ui_server(client, token)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",       # without this you get XML, not JSON
        "Content-Type": "application/json",
    }

    before = read_lines(client, ui_server, headers)
    print(f"Before: {len(before)} line(s)")
    for row in before:
        print(f"  {row['user_line_no']}: {row['oe_order_item_id']} x {row['unit_quantity']}")

    payload = {
        "Name": "Order",
        "UseCodeValues": False,
        "Transactions": [{
            "Status": "New",
            "DataElements": [
                {
                    # ONLY the key. Re-sending header fields fails on disabled
                    # columns (customer_id) once the order exists.
                    "Name": "TABPAGE_1.order",
                    "Type": "Form",
                    "Keys": ["order_no"],
                    "Rows": [{
                        "Edits": [{"Name": "order_no", "Value": ORDER_NO}],
                        "RelativeDateEdits": [],
                    }],
                },
                {
                    "Name": "TP_ITEMS.items",
                    "Type": "List",
                    "Keys": ["user_line_no"],
                    "Rows": [
                        {"Edits": [
                            {"Name": "user_line_no",     "Value": handle},
                            {"Name": "oe_order_item_id", "Value": item_id},
                            {"Name": "unit_quantity",    "Value": qty},
                        ], "RelativeDateEdits": []}
                        for handle, item_id, qty in LINES
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
        raise SystemExit("Order update failed")

    # Read back: each handle carries its value, and no unexpected line appeared
    after = read_lines(client, ui_server, headers)
    print(f"After: {len(after)} line(s)")
    by_handle = {row["user_line_no"]: row for row in after}
    for handle, item_id, qty in LINES:
        row = by_handle.get(handle)
        landed = (row is not None and row["oe_order_item_id"] == item_id
                  and float(row["unit_quantity"]) == float(qty))
        detail = f" ({row['oe_order_item_id']} x {row['unit_quantity']})" if row else ""
        print(f"  {handle}: {'OK' if landed else 'NOT APPLIED'}{detail}")
    expected = len({row["user_line_no"] for row in before} | {h for h, _, _ in LINES})
    if len(after) != expected:
        print(f"WARNING: expected {expected} lines, found {len(after)} -- a key problem "
              "appends lines while reporting Succeeded (see Gotchas)")
```

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.example.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string OrderNo = "1001234";
// (user_line_no, oe_order_item_id, unit_quantity): an EXISTING handle updates
// that line in place, a NEW handle inserts a line.
var lines = new (string Handle, string ItemId, string Quantity)[]
{
    ("010", "WIDGET-001", "4"),
    ("030", "WIDGET-002", "1"),
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

var before = await ReadLinesAsync(client, uiServer);
Console.WriteLine($"Before: {before.Count} line(s)");
foreach (var row in before)
{
    Console.WriteLine($"  {row["user_line_no"]}: {row["oe_order_item_id"]} x {row["unit_quantity"]}");
}

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
                // ONLY the key. Re-sending header fields fails on disabled
                // columns (customer_id) once the order exists.
                new
                {
                    Name = "TABPAGE_1.order",
                    Type = "Form",
                    Keys = new[] { "order_no" },
                    Rows = new object[]
                    {
                        new
                        {
                            Edits = new[] { new { Name = "order_no", Value = OrderNo } },
                            RelativeDateEdits = Array.Empty<object>(),
                        },
                    },
                },
                new
                {
                    Name = "TP_ITEMS.items",
                    Type = "List",
                    Keys = new[] { "user_line_no" },
                    Rows = lines.Select(l => (object)new
                    {
                        Edits = new[]
                        {
                            new { Name = "user_line_no", Value = l.Handle },
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
    throw new InvalidOperationException("Order update failed");
}

// Read back: each handle carries its value, and no unexpected line appeared
var after = await ReadLinesAsync(client, uiServer);
Console.WriteLine($"After: {after.Count} line(s)");
foreach (var (handle, itemId, quantity) in lines)
{
    var row = after.FirstOrDefault(r => r["user_line_no"] == handle);
    var landed = row is not null && row["oe_order_item_id"] == itemId
        && decimal.Parse(row["unit_quantity"]) == decimal.Parse(quantity);
    var detail = row is null ? "" : $" ({row["oe_order_item_id"]} x {row["unit_quantity"]})";
    Console.WriteLine($"  {handle}: {(landed ? "OK" : "NOT APPLIED")}{detail}");
}
var expected = before.Select(r => r["user_line_no"])
    .Union(lines.Select(l => l.Handle)).Count();
if (after.Count != expected)
{
    Console.WriteLine($"WARNING: expected {expected} lines, found {after.Count} -- a key " +
                      "problem appends lines while reporting Succeeded (see Gotchas)");
}

// --- helpers ---------------------------------------------------------------

// Read the order's lines back with /transaction/get -- the only proof.
static async Task<List<Dictionary<string, string>>> ReadLinesAsync(HttpClient client, string uiServer)
{
    var request = JsonSerializer.Serialize(new
    {
        ServiceName = "Order",
        TransactionStates = new[]
        {
            new
            {
                DataElementName = "TABPAGE_1.order",
                Keys = new[] { new { Name = "order_no", Value = OrderNo } },
            },
        },
    });
    using var response = await client.PostAsync($"{uiServer}/api/v2/transaction/get",
        new StringContent(request, Encoding.UTF8, "application/json"));
    response.EnsureSuccessStatusCode();
    using var doc = JsonDocument.Parse(await response.Content.ReadAsStringAsync());
    var rows = new List<Dictionary<string, string>>();
    foreach (var element in doc.RootElement.GetProperty("Transactions")[0]
                 .GetProperty("DataElements").EnumerateArray())
    {
        if (element.GetProperty("Name").GetString() != "TP_ITEMS.items") continue;
        foreach (var row in element.GetProperty("Rows").EnumerateArray())
        {
            var edits = row.GetProperty("Edits").EnumerateArray().ToDictionary(
                e => e.GetProperty("Name").GetString()!,
                e => e.GetProperty("Value").GetString() ?? "");
            if (!string.IsNullOrEmpty(edits.GetValueOrDefault("oe_order_item_id")))
            {
                rows.Add(edits);
            }
        }
    }
    return rows;
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

> **End-to-end files** (runnable from the repo with a `.env`, dry-run by default): [`examples/python/recipes/update_order_lines.py`](../../examples/python/recipes/update_order_lines.py) · [`examples/csharp/Recipes/UpdateOrderLines.cs`](../../examples/csharp/Recipes/UpdateOrderLines.cs). The snippets above are self-contained; the files use the repo's shared `common` / `P21Examples.Common` helpers like every other example. Python and C# examples (the snippets above and both files) run on play 26.1.5950.0, 2026-10-10, each against a throwaway two-line order: one existing handle's quantity changed in place and one new handle inserted, both confirmed by the `/transaction/get` read-back with no extra lines.

## Gotchas

All verified live on 26.1 — details in [Keys — Row Identity and the Collapse Trap](../03-Transaction-API.md#keys-row-identity-and-the-collapse-trap):

- **Send only `order_no` in the header element.** Re-sending create-time header fields fails the update on disabled columns — `Column is disabled: customer_id` was the verified refusal. The header's job here is loading the order, nothing more.
- **Key on `user_line_no`, not on data fields.** Keying on `unit_quantity` (or any field you're changing) means the new value no longer matches the row's key — the "update" silently **appends a new line** with `Succeeded: 1`. Verified: a qty 10→20 edit keyed on `unit_quantity` produced a third line.
- **`user_line_no` must be in each row's `Edits`.** A key field that isn't sent fails the transaction with the opaque `General Exception: Sequence contains no matching element`.
- **A new handle inserts; that's the feature and the risk.** A typo'd handle doesn't error — it quietly adds a line. The read-back below catches it.
- **DynaChange prompts are auto-answered with the default** — same as order creation; a dropped change still reports `Succeeded`. See [create-sales-order § Gotchas](create-sales-order.md#gotchas).
- **RMAs need a different service.** An order with `oe_hdr.rma_flag = 'Y'` cannot be loaded through `Order` at all — it fails with `You cannot retrieve an RMA from the Order Entry/Front Counter window.` Use the **`RMA`** service instead: identical `TABPAGE_1.order` form, keyed the same way, same fields. Bulk jobs over open orders hit this routinely, so route per order on `rma_flag` rather than discovering it as a failure. See [03 § RMA Service](../03-Transaction-API.md#rma-service-orders-the-order-service-refuses).
- **HTTP 200 ≠ success.** Check `Summary` and `Results.Transactions[].Status == "Passed"`.

## Verify

Read the order back — a `Succeeded` response is not proof:

- `POST /api/v2/transaction/get` (as in the example) and compare every line: the edited handle carries the new quantity, the new handle exists, and **no unexpected extra lines appeared** (the signature of a key problem).
- Or via OData: `GET /odataservice/odata/view/p21_view_oe_line?$filter=order_no eq '1001234'`.
