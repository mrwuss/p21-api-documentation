# Write Off Small Residual Inventory Cost (Edit Inventory Cost)

Set an item's moving average cost at one location to a token value — the usual first half of disposing of stock nobody wants — through the `InventoryCostEdit` service, then read the new cost back.

**API:** Transaction · **Service:** `InventoryCostEdit` · **Deep dive:** [InventoryCostEdit Service](../03-Transaction-API.md#inventorycostedit-service-changing-an-items-average-cost) · **Next step:** [dispose-zero-value-stock](dispose-zero-value-stock.md)

## Prerequisites

- The item (here `WIDGET-001`) has an `inv_loc` row at the location (here `10`). Items with no row at the location cannot be edited; skip them.
- You know the **offset GL account** the value difference posts to, in its stored form without the dash (the window shows `11111-00`; you send `1111100`), and the **fiscal** period and year to post in. Ask whoever owns the GL — the account and the period are business decisions, not something to guess.
- Run against a test/play environment first. **The save posts to the GL immediately.**

## When to use it

A count turns up stock that will never sell. Rather than adjusting it out item by item, some sites write the cost down to a token value per unit (a few cents) so the write-off lands in one GL account, then ship the units out on a [$0 order](dispose-zero-value-stock.md). Picking a recognizable token cost — for example one that encodes the disposal year — makes the written-down items easy to find again with a simple `moving_average_cost` filter.

## Payload

`POST {ui_server}/api/v2/transaction`, `Status: "New"`, `UseCodeValues: false`. Three DataElements, all keyed the way the window is:

| Element | Type | Keys | Edits |
|---|---|---|---|
| `QUERY.query` | List | `location_id`, `item_id` | the same two — selects the item/location row |
| `FORM.form` | Form | `location_id`, `item_id` | the same two plus **`new_cost`** |
| `FORM.account` | Form | `account_no` | **`account_no`**, then **`year_for_period`**, then **`period`** — all three required, in this order |

> **Payload file** (validator-clean): [JSON](../../examples/payloads/json/inventory-cost-edit.json).

## Complete example

Reads the current cost over OData, skips the item if it is already at the target, posts the cost edit, and reads the cost back.

<!-- tabs -->
```python
"""Edit an item's moving average cost at one location, then read it back."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.example.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
ITEM_ID = "WIDGET-001"
LOCATION_ID = "10"
NEW_COST = "0.02"                         # the new moving average cost per unit
ACCOUNT_NO = "1111100"                    # offset GL account, stored form: NO dash
YEAR_FOR_PERIOD = "2026"                  # FISCAL year
PERIOD = "12"                             # FISCAL period
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


def read_cost(client: httpx.Client, headers: dict) -> dict | None:
    """Return the inv_loc row (cost + on hand) for ITEM_ID at LOCATION_ID, or None."""
    r = client.get(
        f"{BASE_URL}/odataservice/odata/table/inv_mast",
        headers=headers,
        params={"$filter": f"item_id eq '{ITEM_ID}'", "$select": "inv_mast_uid"},
    )
    r.raise_for_status()
    items = r.json().get("value", [])
    if not items:
        return None
    uid = items[0]["inv_mast_uid"]
    r = client.get(
        f"{BASE_URL}/odataservice/odata/table/inv_loc",
        headers=headers,
        params={
            # location_id and inv_mast_uid are numeric -- no quotes
            "$filter": f"inv_mast_uid eq {uid} and location_id eq {LOCATION_ID}",
            "$select": "moving_average_cost,qty_on_hand,last_maintained_by",
        },
    )
    r.raise_for_status()
    rows = r.json().get("value", [])
    return rows[0] if rows else None


def row(edits: dict) -> dict:
    """One Rows entry, edits in the order given (order matters on FORM.account)."""
    return {"Edits": [{"Name": k, "Value": v} for k, v in edits.items()],
            "RelativeDateEdits": []}


with httpx.Client(verify=VERIFY_SSL, timeout=300, follow_redirects=True) as client:
    token = get_token(client)
    ui_server = get_ui_server(client, token)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",       # without this you get XML, not JSON
        "Content-Type": "application/json",
    }

    before = read_cost(client, headers)
    if before is None:
        raise SystemExit(f"{ITEM_ID} has no inv_loc row at location {LOCATION_ID} -- skip it")
    print(f"Before: cost {before['moving_average_cost']}, on hand {before['qty_on_hand']}")
    if float(before["moving_average_cost"]) == float(NEW_COST):
        raise SystemExit("Already at the target cost -- nothing to do")

    keys = {"location_id": LOCATION_ID, "item_id": ITEM_ID}
    payload = {
        "Name": "InventoryCostEdit",
        "UseCodeValues": False,
        "Transactions": [{
            "Status": "New",
            "DataElements": [
                {"Name": "QUERY.query", "Type": "List",
                 "Keys": ["location_id", "item_id"], "Rows": [row(keys)]},
                {"Name": "FORM.form", "Type": "Form",
                 "Keys": ["location_id", "item_id"],
                 "Rows": [row({**keys, "new_cost": NEW_COST})]},
                # year_for_period BEFORE period: the window validates the period
                # against the year already in the form.
                {"Name": "FORM.account", "Type": "Form", "Keys": ["account_no"],
                 "Rows": [row({"account_no": ACCOUNT_NO,
                               "year_for_period": YEAR_FOR_PERIOD,
                               "period": PERIOD})]},
            ],
        }],
    }

    resp = client.post(f"{ui_server}/api/v2/transaction", headers=headers, json=payload)
    resp.raise_for_status()  # HTTP 200 even on failure -- check the Summary
    result = resp.json()
    summary = result["Summary"]
    print(f"Succeeded: {summary['Succeeded']}, Failed: {summary['Failed']}")
    if summary["Failed"] > 0:
        for msg in result.get("Messages") or []:
            print(f"  {msg}")
        raise SystemExit("Cost edit failed")

    after = read_cost(client, headers)
    print(f"After:  cost {after['moving_average_cost']}, "
          f"last maintained by {after['last_maintained_by']}")
    if float(after["moving_average_cost"]) != float(NEW_COST):
        raise SystemExit("Read-back does not match -- investigate before continuing")
```

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.example.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string ItemId = "WIDGET-001";
const string LocationId = "10";
const string NewCost = "0.02";          // the new moving average cost per unit
const string AccountNo = "1111100";     // offset GL account, stored form: NO dash
const string YearForPeriod = "2026";    // FISCAL year
const string Period = "12";             // FISCAL period
// ---------------------------------------------------------------------------

var handler = new HttpClientHandler
{
    // Test tenants often present a self-signed cert. Delete this line in production.
    ServerCertificateCustomValidationCallback =
        HttpClientHandler.DangerousAcceptAnyServerCertificateValidator,
};
using var client = new HttpClient(handler) { Timeout = TimeSpan.FromMinutes(5) };
client.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));

var token = await GetTokenAsync(client);
var uiServer = await GetUiServerAsync(client, token);
client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);

var before = await ReadCostAsync(client);
if (before is null)
{
    Console.WriteLine($"{ItemId} has no inv_loc row at location {LocationId} -- skip it");
    return;
}
Console.WriteLine($"Before: cost {before.Value.Cost}, on hand {before.Value.OnHand}");
if (before.Value.Cost == decimal.Parse(NewCost))
{
    Console.WriteLine("Already at the target cost -- nothing to do");
    return;
}

var payload = new
{
    Name = "InventoryCostEdit",
    UseCodeValues = false,
    Transactions = new[]
    {
        new
        {
            Status = "New",
            DataElements = new object[]
            {
                Element("QUERY.query", "List", new[] { "location_id", "item_id" },
                    ("location_id", LocationId), ("item_id", ItemId)),
                Element("FORM.form", "Form", new[] { "location_id", "item_id" },
                    ("location_id", LocationId), ("item_id", ItemId), ("new_cost", NewCost)),
                // year_for_period BEFORE period: the window validates the period
                // against the year already in the form.
                Element("FORM.account", "Form", new[] { "account_no" },
                    ("account_no", AccountNo), ("year_for_period", YearForPeriod),
                    ("period", Period)),
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
    throw new InvalidOperationException("Cost edit failed");
}

var after = await ReadCostAsync(client)
    ?? throw new InvalidOperationException("inv_loc row disappeared");
Console.WriteLine($"After:  cost {after.Cost}, last maintained by {after.MaintainedBy}");
if (after.Cost != decimal.Parse(NewCost))
{
    throw new InvalidOperationException("Read-back does not match -- investigate before continuing");
}

// --- helpers ---------------------------------------------------------------

// One DataElement with one row; edits keep the order given (it matters on FORM.account).
static object Element(string name, string type, string[] keys, params (string Name, string Value)[] edits) =>
    new
    {
        Name = name,
        Type = type,
        Keys = keys,
        Rows = new[]
        {
            new
            {
                Edits = edits.Select(e => new { e.Name, e.Value }).ToArray(),
                RelativeDateEdits = Array.Empty<object>(),
            },
        },
    };

// inv_loc row for ItemId at LocationId over OData (chained by inv_mast_uid -- no joins).
static async Task<CostRow?> ReadCostAsync(HttpClient client)
{
    var itemUrl = $"{BaseUrl}/odataservice/odata/table/inv_mast" +
                  $"?$filter={Uri.EscapeDataString($"item_id eq '{ItemId}'")}&$select=inv_mast_uid";
    using var items = JsonDocument.Parse(await client.GetStringAsync(itemUrl));
    var itemRows = items.RootElement.GetProperty("value");
    if (itemRows.GetArrayLength() == 0) return null;
    var uid = itemRows[0].GetProperty("inv_mast_uid").GetRawText();

    // location_id and inv_mast_uid are numeric -- no quotes
    var locUrl = $"{BaseUrl}/odataservice/odata/table/inv_loc" +
                 $"?$filter={Uri.EscapeDataString($"inv_mast_uid eq {uid} and location_id eq {LocationId}")}" +
                 "&$select=moving_average_cost,qty_on_hand,last_maintained_by";
    using var locs = JsonDocument.Parse(await client.GetStringAsync(locUrl));
    var locRows = locs.RootElement.GetProperty("value");
    if (locRows.GetArrayLength() == 0) return null;
    var r = locRows[0];
    return new CostRow(
        r.GetProperty("moving_average_cost").GetDecimal(),
        r.GetProperty("qty_on_hand").GetDecimal(),
        r.GetProperty("last_maintained_by").GetString() ?? "");
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

record struct CostRow(decimal Cost, decimal OnHand, string MaintainedBy);
```
<!-- /tabs -->

> **End-to-end files** (runnable from the repo with a `.env`, dry-run by default): [`examples/python/recipes/inventory_cost_edit.py`](../../examples/python/recipes/inventory_cost_edit.py) · [`examples/csharp/Recipes/InventoryCostEdit.cs`](../../examples/csharp/Recipes/InventoryCostEdit.cs). The programs above are self-contained; the files use the repo's shared `common` / `P21Examples.Common` helpers.

## Running it for many items

- **Build the item list from live `inv_loc` at run time**, not from a count spreadsheet. Quantities drift, items get merged, and keyed sheets carry typos.
- One POST per item is fine — about a third of a second per item on a test tenant. Re-running is safe because items already at the target cost are skipped.
- Write a before-file of every item's current cost before the first POST, so you can reverse a mistake with the same service.

## Gotchas

- **`account_no` without the dash.** The dashed form fails *"A valid GL account must be entered"* and nothing posts.
- **`year_for_period` before `period`.** Reversed, the window validates the period against its default year and fails *"Period 12, Year 2000 have not been setup for company …"*.
- **Fiscal, not calendar.** A period of `0` fails *"Period has no value or is zero"*.
- **There is no inventory transaction.** The edit writes no `inv_tran` row and no `inv_adj` row — only `inv_loc`, one `audit_trail` row and the GL. Reports built on `inv_tran` will not see it.
- **HTTP 200 is not success** — check `Summary` and read the cost back.

## Verify

- `inv_loc.moving_average_cost` = the new cost at the location (the example's read-back), `last_maintained_by` = your API user.
- One `audit_trail` row with `column_changed = 'moving_average_cost'`.
- A GL pair under journal `IC`, description `Cost Edit - <old> TO <new>`: inventory account against your offset account, amount `qty_on_hand × (old − new)`; sub-cent rounding posts to a separate rounding account. Reconcile the batch total against the sum of the per-item amounts.
- **With nothing on hand there is no GL pair.** An edit at a location with `qty_on_hand = 0` changes `inv_loc` and writes its `audit_trail` row, and posts nothing to `gl`. That makes a zero-stock location the low-impact place to try the service.

> **Credit:** [Alex Westemeier](https://github.com/AWestemeier) — service shape, ordering rule and GL behavior verified on play (about a thousand items in one run) and on production, September 2026. Python and C# examples run on play 26.1.5950.0, 2026-10-10: both programs above and both repo files, each editing a throwaway item's cost at a location with nothing on hand, in an open fiscal period. Each run was confirmed by the `inv_loc.moving_average_cost` read-back and one `audit_trail` row (`table_changed = 'inv_loc'`, old and new value), with no `inv_tran` row. Because nothing was on hand, these runs posted no GL; the GL pair described under Verify is from the September runs, not re-checked here. The `account_no` dash, period-order and period-zero failures in Gotchas are also from those runs.
