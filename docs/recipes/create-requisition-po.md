# Create a Requisition Purchase Order

Create a **requisition PO** — P21's internal / not-for-resale purchasing type — in one stateless Transaction API call. The result is a PO with `po_hdr.po_type = 'R'`.

**API:** Transaction · **Service:** `RequisitionPurchaseOrder` · **Deep dive:** [Purchase Order Types](../03-Transaction-API.md#purchase-order-types-and-the-disabled-po_hdr_po_type-column) · **Full schema:** [RequisitionPurchaseOrder.json](../../definitions/RequisitionPurchaseOrder.json)

## Why a separate service

You **cannot** set the PO type by writing `po_hdr_po_type` on the `PurchaseOrder` service — it is a disabled column (`Column is disabled: po_hdr_po_type`). You pick the type by choosing the **type-specific service**. `RequisitionPurchaseOrder` is that service for requisition POs — same window as PO Entry (`w_purchase_order_entry_sheet`), type preset to Requisition. It's a listed service in `/api/v2/services` but easy to miss.

## Prerequisites

- P21 credentials — the complete example below authenticates itself; nothing to install but `httpx` (Python) or a bare `net8.0`-or-later console project (C#).
- The **item is flagged as a requisition item** at the PO location (`inv_loc.requisition = 'Y'`). *Only requisition items may be purchased on a requisition PO* — this is enforced at the API layer.
- You have the **vendor id** and its **supplier id** — these are different numbers (e.g. vendor `99001` "Acme Technology Corp" ↔ supplier `10050` "ACME-PENNSYLVANIA"). Passing a supplier id as `vendor_id` fails with *"Record specified was not found."*

## Payload

Header (`TABPAGE_1.tp_1_dw_1`, Form, key `po_no`) + line grid (`TABPAGE_17.tp_17_dw_17`, List, keys `line_no`/`item_id`). `po_no` is auto-assigned and returned in the result rows.

```json
POST {ui_server}/api/v2/transaction

{
    "Name": "RequisitionPurchaseOrder",
    "UseCodeValues": false,
    "Transactions": [{
        "Status": "New",
        "DataElements": [
            {
                "Name": "TABPAGE_1.tp_1_dw_1",
                "Type": "Form",
                "Keys": [],
                "Rows": [{
                    "Edits": [
                        {"Name": "location_id",        "Value": "10"},
                        {"Name": "vendor_id",          "Value": "99001"},
                        {"Name": "vendor_supplier_id", "Value": "10050"}
                    ],
                    "RelativeDateEdits": []
                }]
            },
            {
                "Name": "TABPAGE_17.tp_17_dw_17",
                "Type": "List",
                "Keys": [],
                "Rows": [{
                    "Edits": [
                        {"Name": "item_id",       "Value": "WIDGET-001"},
                        {"Name": "unit_quantity", "Value": "10"}
                    ],
                    "RelativeDateEdits": []
                }]
            }
        ]
    }]
}
```

The definition also marks `company_id`, `division_id`, `buyer_id`, `order_date`, and `required_date` required on the header, and `unit_of_measure` / `pricing_unit` required on the line — these are supplied by the **defaults template** (`GET {ui_server}/api/v2/defaults/RequisitionPurchaseOrder`) and the item's default UOM. For every field the service accepts, load [`definitions/RequisitionPurchaseOrder.json`](../../definitions/RequisitionPurchaseOrder.json).

## Complete example

<!-- tabs -->
```python
"""Create a requisition PO, then read the header back and confirm po_type = 'R'."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
LOCATION_ID = "10"
VENDOR_ID = "99001"                       # vendor id, NOT the supplier id
VENDOR_SUPPLIER_ID = "10050"              # header, NOT the line
ITEM_ID = "WIDGET-001"                    # must be a requisition item at LOCATION_ID
UNIT_QUANTITY = "10"
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
        "Accept": "application/json",       # without this you get XML, not JSON
        "Content-Type": "application/json",
    }

    payload = {
        "Name": "RequisitionPurchaseOrder",
        "UseCodeValues": False,
        "Transactions": [{
            "Status": "New",
            "DataElements": [
                {
                    "Name": "TABPAGE_1.tp_1_dw_1",
                    "Type": "Form",
                    "Keys": [],
                    "Rows": [{
                        "Edits": [
                            {"Name": "location_id",        "Value": LOCATION_ID},
                            {"Name": "vendor_id",          "Value": VENDOR_ID},
                            {"Name": "vendor_supplier_id", "Value": VENDOR_SUPPLIER_ID},
                        ],
                        "RelativeDateEdits": [],
                    }],
                },
                {
                    "Name": "TABPAGE_17.tp_17_dw_17",
                    "Type": "List",
                    "Keys": [],
                    "Rows": [{
                        "Edits": [
                            {"Name": "item_id",       "Value": ITEM_ID},
                            {"Name": "unit_quantity", "Value": UNIT_QUANTITY},
                        ],
                        "RelativeDateEdits": [],
                    }],
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
        raise SystemExit("Requisition PO create failed")

    # The generated po_no comes back in the TABPAGE_1.tp_1_dw_1 result rows
    po_no = None
    for txn in result["Results"]["Transactions"]:
        if txn.get("Status") != "Passed":
            continue
        for element in txn.get("DataElements", []):
            if element.get("Name") != "TABPAGE_1.tp_1_dw_1":
                continue
            for row in element.get("Rows", []):
                for edit in row.get("Edits", []):
                    if edit.get("Name") == "po_no":
                        po_no = edit.get("Value")

    print(f"Created po_no: {po_no}")

    # Read back via OData -- confirm po_type == 'R'
    hdr = client.get(
        f"{BASE_URL}/odataservice/odata/table/po_hdr",
        params={"$filter": f"po_no eq {po_no}", "$select": "po_no,po_type,vendor_id"},
        headers=headers,
    )
    hdr.raise_for_status()
    for row in hdr.json()["value"]:
        print(f"  po_no={row['po_no']} po_type={row['po_type']} (expected R) "
              f"vendor_id={row['vendor_id']}")

    # ...and confirm every line you submitted is present
    lines = client.get(
        f"{BASE_URL}/odataservice/odata/table/po_line",
        params={"$filter": f"po_no eq {po_no}"},
        headers=headers,
    )
    lines.raise_for_status()
    print(f"  po_line rows: {len(lines.json()['value'])} (submitted 1)")
```

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string LocationId = "10";
const string VendorId = "99001";           // vendor id, NOT the supplier id
const string VendorSupplierId = "10050";   // header, NOT the line
const string ItemId = "WIDGET-001";        // must be a requisition item at LocationId
const string UnitQuantity = "10";
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
    Name = "RequisitionPurchaseOrder",
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
                    Name = "TABPAGE_1.tp_1_dw_1",
                    Type = "Form",
                    Keys = Array.Empty<string>(),
                    Rows = new[]
                    {
                        new
                        {
                            Edits = new[]
                            {
                                new { Name = "location_id", Value = LocationId },
                                new { Name = "vendor_id", Value = VendorId },
                                new { Name = "vendor_supplier_id", Value = VendorSupplierId },
                            },
                            RelativeDateEdits = Array.Empty<object>(),
                        },
                    },
                },
                new
                {
                    Name = "TABPAGE_17.tp_17_dw_17",
                    Type = "List",
                    Keys = Array.Empty<string>(),
                    Rows = new[]
                    {
                        new
                        {
                            Edits = new[]
                            {
                                new { Name = "item_id", Value = ItemId },
                                new { Name = "unit_quantity", Value = UnitQuantity },
                            },
                            RelativeDateEdits = Array.Empty<object>(),
                        },
                    },
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
    throw new InvalidOperationException("Requisition PO create failed");
}

// The generated po_no comes back in the TABPAGE_1.tp_1_dw_1 result rows
var poNo = ResultValue(result.RootElement, "TABPAGE_1.tp_1_dw_1", "po_no");
Console.WriteLine($"Created po_no: {poNo}");

// Read back via OData -- confirm po_type == 'R'
foreach (var row in await ODataAsync(client, "po_hdr", $"po_no eq {poNo}"))
{
    Console.WriteLine(
        $"  po_no={row.GetProperty("po_no")} po_type={row.GetProperty("po_type")} " +
        $"(expected R) vendor_id={row.GetProperty("vendor_id")}");
}

// ...and confirm every line you submitted is present
var poLines = await ODataAsync(client, "po_line", $"po_no eq {poNo}");
Console.WriteLine($"  po_line rows: {poLines.Count} (submitted 1)");

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

> **End-to-end files** (runnable from the repo with a `.env`, dry-run by default): [`examples/python/recipes/create_requisition_po.py`](../../examples/python/recipes/create_requisition_po.py) · [`examples/csharp/Recipes/CreateRequisitionPo.cs`](../../examples/csharp/Recipes/CreateRequisitionPo.cs).

## Gotchas (verified live on Play 26.1.5894.1, 2026-07)

- **`vendor_supplier_id` goes on the header, but omitting it fails at the *line* with a misleading message:** *"A supplier ID must be entered. DataElement: tp_17_dw_17, Column: item_id"*. The pointer to the line's `item_id` is wrong — the fix is `vendor_supplier_id` on `TABPAGE_1.tp_1_dw_1`.
- **`vendor_id` ≠ `supplier_id`.** They are different ids on different records. Passing a supplier id where `vendor_id` belongs fails with *"Record specified was not found."*
- **Only requisition items are allowed.** The line item must have `inv_loc.requisition = 'Y'` at the PO location, or the create fails with *"Only requisition items may be purchased on a requisition PO."*
- **Type is chosen by the service, not a field.** Do not send `po_hdr_po_type` — it is disabled. `RequisitionPurchaseOrder` produces `po_hdr.po_type = 'R'` (verified). See the [PO type letter table](../03-Transaction-API.md#purchase-order-types-and-the-disabled-po_hdr_po_type-column).
- **HTTP 200 ≠ success.** Check `Summary.Succeeded` and `Results.Transactions[].Status == "Passed"`; the generated `po_no` comes back in the result rows.

## Verify

```http
GET {base_url}/odataservice/odata/table/po_hdr?$filter=po_no eq 12345&$select=po_no,po_type,vendor_id
GET {base_url}/odataservice/odata/table/po_line?$filter=po_no eq 12345
```

Confirm `po_type` is `R` and every line you submitted is present.
