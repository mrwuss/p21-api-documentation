# Adjust On-Hand Quantity (Write-Off)

Post an inventory adjustment — a signed on-hand quantity change with no invoice — via the `InventoryAdjustment` service.

**API:** Transaction · **Service:** `InventoryAdjustment` · **Deep dive:** [Inventory Adjustment (Write-Offs)](../12-Production-Labor-API.md#inventory-adjustment-write-offs) · **Full schema:** [definitions/InventoryAdjustment.json](../../definitions/InventoryAdjustment.json)

## Prerequisites

- The item (here `WIDGET-001`) is set up at the location (here `10`).
- An adjustment **reason** exists in P21 (here the display text `ADJUST`) — you pass its display text, not its code.
- Run against a test/play environment first: the save **posts the adjustment** immediately.

## Payload

`POST {ui_server}/api/v2/transaction`, `Status: "New"`, `UseCodeValues: false`. Two DataElements:

**Header — `TABPAGE_1.tp_1_dw_1` (Form, business object `inv_adj_hdr`, key `adjustment_number`)**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `adjustment_number` | Decimal | Key | Server-generated — leave unset on a new adjustment |
| `company_id` | Char | Yes | Company ID |
| `location_id` | Decimal | Yes | Location being adjusted |
| `reason_id` | Char | Yes | The reason's **display text** (with `UseCodeValues: false`), not its code |
| `period` / `year_for_period` | Decimal | Yes (per definition) | Accounting period / year for the adjustment |
| `inv_adj_description` | Char | No | Free-text description |
| `approved` | Char | No | `ON` / `OFF` |

The verified minimal header from the manual is `location_id` + `reason_id`; the definition additionally marks `company_id`, `period`, and `year_for_period` as `Required`.

**Lines — `TABPAGE_17.tp_17_dw_17` (List, business object `inv_adj_line`)**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `item_id` | Char | Yes | Item to adjust |
| `unit_quantity` | Decimal | Yes | **The signed delta** (label "Adjustment Amount") — e.g. `-5` writes off 5 units; negative on-hand zeroes it out |
| `unit_of_measure` | Char | No | |
| `unit_size` | Decimal | Yes (per definition) | From `item_uom.unit_size` |
| `new_qoh` | Decimal | No | Resulting quantity on hand (display) |

The verified minimal line from the manual is `item_id` + `unit_quantity`.

## Complete example

Writes off 5 units of `WIDGET-001` at location `10`, then reads the adjustment back by its server-generated `adjustment_number`.

<!-- tabs -->
```python
"""Post an inventory adjustment, then read it back by its adjustment_number."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
COMPANY_ID = "ACME"
LOCATION_ID = "10"
REASON_ID = "ADJUST"                      # the reason's DISPLAY TEXT, not its code
DESCRIPTION = "Cycle count write-off"
ITEM_ID = "WIDGET-001"
UNIT_QUANTITY = "-5"                      # signed delta, NOT the new on-hand
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
        "Name": "InventoryAdjustment",
        "UseCodeValues": False,  # reason_id is the display text, not the code
        "Transactions": [{
            "Status": "New",
            "DataElements": [
                {
                    "Name": "TABPAGE_1.tp_1_dw_1",
                    "Type": "Form",
                    "Keys": [],
                    "Rows": [{
                        "Edits": [
                            {"Name": "company_id", "Value": COMPANY_ID},
                            {"Name": "location_id", "Value": LOCATION_ID},
                            {"Name": "reason_id", "Value": REASON_ID},
                            {"Name": "inv_adj_description", "Value": DESCRIPTION},
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
                            {"Name": "item_id", "Value": ITEM_ID},
                            {"Name": "unit_quantity", "Value": UNIT_QUANTITY},
                        ],
                        "RelativeDateEdits": [],
                    }],
                },
            ],
        }],
    }

    resp = client.post(f"{ui_server}/api/v2/transaction",
                       headers=headers, json=payload)
    resp.raise_for_status()  # HTTP 200 even on failure -- check the Summary
    result = resp.json()

    summary = result["Summary"]
    print(f"Succeeded: {summary['Succeeded']}, Failed: {summary['Failed']}")
    if summary["Failed"] > 0:
        for msg in result.get("Messages", []):
            print(f"  {msg}")
        raise SystemExit("Adjustment failed")

    # Pull the server-generated adjustment_number out of the echoed DataElements
    adjustment_number = None
    for txn in result.get("Results", {}).get("Transactions", []):
        for de in txn.get("DataElements", []):
            if de.get("Name") == "TABPAGE_1.tp_1_dw_1":
                for row in de.get("Rows", []):
                    for edit in row.get("Edits", []):
                        if edit["Name"] == "adjustment_number" and edit.get("Value"):
                            adjustment_number = edit["Value"]
    print(f"Adjustment number: {adjustment_number}")

    # --- Read the adjustment back ---
    get_payload = {
        "ServiceName": "InventoryAdjustment",
        "TransactionStates": [{
            "DataElementName": "TABPAGE_1.tp_1_dw_1",
            "Keys": [{"Name": "adjustment_number", "Value": adjustment_number}],
        }],
    }
    resp = client.post(f"{ui_server}/api/v2/transaction/get",
                       headers=headers, json=get_payload)
    resp.raise_for_status()
    for txn in resp.json().get("Transactions", []):
        for de in txn.get("DataElements", []):
            for row in de.get("Rows", []):
                for edit in row.get("Edits", []):
                    if edit["Name"] in ("adjustment_number", "location_id", "reason_id",
                                        "item_id", "unit_quantity", "new_qoh"):
                        print(f"  {edit['Name']}: {edit['Value']}")
```

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string CompanyId = "ACME";
const string LocationId = "10";
const string ReasonId = "ADJUST";       // the reason's DISPLAY TEXT, not its code
const string Description = "Cycle count write-off";
const string ItemId = "WIDGET-001";
const string UnitQuantity = "-5";       // signed delta, NOT the new on-hand
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
    Name = "InventoryAdjustment",
    UseCodeValues = false,  // reason_id is the display text, not the code
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
                                new { Name = "company_id", Value = CompanyId },
                                new { Name = "location_id", Value = LocationId },
                                new { Name = "reason_id", Value = ReasonId },
                                new { Name = "inv_adj_description", Value = Description },
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

using var resp = await client.PostAsync(
    $"{uiServer}/api/v2/transaction",
    new StringContent(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json"));
resp.EnsureSuccessStatusCode();  // HTTP 200 even on failure -- check the Summary
using var result = JsonDocument.Parse(await resp.Content.ReadAsStringAsync());

var summary = result.RootElement.GetProperty("Summary");
Console.WriteLine($"Succeeded: {summary.GetProperty("Succeeded")}, " +
                  $"Failed: {summary.GetProperty("Failed")}");
if (summary.GetProperty("Failed").GetInt32() > 0)
{
    if (result.RootElement.TryGetProperty("Messages", out var messages))
    {
        Console.Error.WriteLine($"  {messages}");
    }
    throw new InvalidOperationException("Adjustment failed");
}

// Pull the server-generated adjustment_number out of the echoed DataElements
string? adjustmentNumber = null;
foreach (var txn in result.RootElement.GetProperty("Results")
             .GetProperty("Transactions").EnumerateArray())
{
    foreach (var de in txn.GetProperty("DataElements").EnumerateArray())
    {
        if (de.GetProperty("Name").GetString() != "TABPAGE_1.tp_1_dw_1") continue;
        foreach (var row in de.GetProperty("Rows").EnumerateArray())
        {
            foreach (var edit in row.GetProperty("Edits").EnumerateArray())
            {
                var value = edit.GetProperty("Value").GetString();
                if (edit.GetProperty("Name").GetString() == "adjustment_number" &&
                    !string.IsNullOrEmpty(value))
                {
                    adjustmentNumber = value;
                }
            }
        }
    }
}
Console.WriteLine($"Adjustment number: {adjustmentNumber}");

// --- Read the adjustment back ---
var getPayload = new
{
    ServiceName = "InventoryAdjustment",
    TransactionStates = new[]
    {
        new
        {
            DataElementName = "TABPAGE_1.tp_1_dw_1",
            Keys = new[] { new { Name = "adjustment_number", Value = adjustmentNumber } },
        },
    },
};
using var getResp = await client.PostAsync(
    $"{uiServer}/api/v2/transaction/get",
    new StringContent(JsonSerializer.Serialize(getPayload), Encoding.UTF8, "application/json"));
getResp.EnsureSuccessStatusCode();
using var getResult = JsonDocument.Parse(await getResp.Content.ReadAsStringAsync());

var wanted = new[] { "adjustment_number", "location_id", "reason_id",
                     "item_id", "unit_quantity", "new_qoh" };
foreach (var txn in getResult.RootElement.GetProperty("Transactions").EnumerateArray())
{
    foreach (var de in txn.GetProperty("DataElements").EnumerateArray())
    {
        foreach (var row in de.GetProperty("Rows").EnumerateArray())
        {
            foreach (var edit in row.GetProperty("Edits").EnumerateArray())
            {
                var name = edit.GetProperty("Name").GetString();
                if (wanted.Contains(name))
                {
                    Console.WriteLine($"  {name}: {edit.GetProperty("Value")}");
                }
            }
        }
    }
}

// --- helpers ---------------------------------------------------------------

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

> **Payload files:** [JSON](../../examples/payloads/json/inventory-adjustment.json) · [XML](../../examples/payloads/xml/inventory-adjustment.xml) — validator-verified, see [payloads README](../../examples/payloads/README.md).
>
> **End-to-end files** (runnable from the repo with a `.env`, dry-run by default): [`examples/python/recipes/inventory_adjustment.py`](../../examples/python/recipes/inventory_adjustment.py) · [`examples/csharp/Recipes/InventoryAdjustment.cs`](../../examples/csharp/Recipes/InventoryAdjustment.cs). The snippet above is self-contained; the files use the repo's shared `common` / `P21Examples.Common` helpers like every other example.

## Gotchas

- **`reason_id` takes the display text** of the reason — not its code — with `UseCodeValues: false`.
- **`unit_quantity` is the signed delta**, not the new on-hand. `-5` removes 5 units; the resulting quantity shows in `new_qoh`. To zero an item out, post the negative of its current on-hand.
- **The save posts the adjustment** — there is no draft state in this flow, and no invoice is involved.
- **Definition-required header fields:** besides `location_id` and `reason_id` (the manual's verified pair), the [definition](../../definitions/InventoryAdjustment.json) marks `company_id`, `period`, and `year_for_period` as `Required` on `tp_1_dw_1`.
- **HTTP 200 is not success** — check `Summary.Succeeded` / `Summary.Failed` and print `Messages`.

## Verify

Read the adjustment back by its key (second half of the example): `POST /api/v2/transaction/get` on `InventoryAdjustment`, element `TABPAGE_1.tp_1_dw_1`, keyed by the server-generated `adjustment_number` — confirm the header (`location_id`, `reason_id`) and the line's `item_id` / `unit_quantity` landed, and check `new_qoh` for the resulting on-hand.

> **Credit:** [Alex Westemeier](https://github.com/AWestemeier)
