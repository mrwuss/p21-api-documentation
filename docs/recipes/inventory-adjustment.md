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

Writes off 5 units of `WIDGET-001` at location `10`, then reads the adjustment back by its server-generated `adjustment_number`. Auth comes from the [shared helper](README.md#shared-conventions-recipes-dont-repeat-these).

<!-- tabs -->
```python
import httpx

BASE_URL = "https://play.p21server.com"
token, ui_server, headers = p21_auth(BASE_URL, "api_user", "api_pass")

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
                        {"Name": "company_id", "Value": "ACME"},
                        {"Name": "location_id", "Value": "10"},
                        {"Name": "reason_id", "Value": "ADJUST"},  # display text
                        {"Name": "inv_adj_description", "Value": "Cycle count write-off"},
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
                        {"Name": "item_id", "Value": "WIDGET-001"},
                        {"Name": "unit_quantity", "Value": "-5"},  # signed delta, NOT new on-hand
                    ],
                    "RelativeDateEdits": [],
                }],
            },
        ],
    }],
}

resp = httpx.post(f"{ui_server}/api/v2/transaction",
                  headers=headers, json=payload, verify=False, timeout=120)
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
resp = httpx.post(f"{ui_server}/api/v2/transaction/get",
                  headers=headers, json=get_payload, verify=False)
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
var session = await P21Session.CreateAsync(
    "https://play.p21server.com", "api_user", "api_pass");

var payload = new JObject
{
    ["Name"] = "InventoryAdjustment",
    ["UseCodeValues"] = false,  // reason_id is the display text, not the code
    ["Transactions"] = new JArray
    {
        new JObject
        {
            ["Status"] = "New",
            ["DataElements"] = new JArray
            {
                new JObject
                {
                    ["Name"] = "TABPAGE_1.tp_1_dw_1",
                    ["Type"] = "Form",
                    ["Keys"] = new JArray(),
                    ["Rows"] = new JArray
                    {
                        new JObject
                        {
                            ["Edits"] = new JArray
                            {
                                new JObject { ["Name"] = "company_id", ["Value"] = "ACME" },
                                new JObject { ["Name"] = "location_id", ["Value"] = "10" },
                                new JObject { ["Name"] = "reason_id", ["Value"] = "ADJUST" }, // display text
                                new JObject { ["Name"] = "inv_adj_description", ["Value"] = "Cycle count write-off" }
                            },
                            ["RelativeDateEdits"] = new JArray()
                        }
                    }
                },
                new JObject
                {
                    ["Name"] = "TABPAGE_17.tp_17_dw_17",
                    ["Type"] = "List",
                    ["Keys"] = new JArray(),
                    ["Rows"] = new JArray
                    {
                        new JObject
                        {
                            ["Edits"] = new JArray
                            {
                                new JObject { ["Name"] = "item_id", ["Value"] = "WIDGET-001" },
                                // signed delta, NOT new on-hand
                                new JObject { ["Name"] = "unit_quantity", ["Value"] = "-5" }
                            },
                            ["RelativeDateEdits"] = new JArray()
                        }
                    }
                }
            }
        }
    }
};

var resp = await session.Http.PostAsync(
    $"{session.UiServer}/api/v2/transaction",
    new StringContent(payload.ToString(), Encoding.UTF8, "application/json"));
resp.EnsureSuccessStatusCode();  // HTTP 200 even on failure -- check the Summary
var result = JObject.Parse(await resp.Content.ReadAsStringAsync());

var summary = result["Summary"]!;
Console.WriteLine($"Succeeded: {summary["Succeeded"]}, Failed: {summary["Failed"]}");
if ((int)summary["Failed"]! > 0)
{
    foreach (var msg in result["Messages"] as JArray ?? new JArray())
        Console.WriteLine($"  {msg}");
    throw new Exception("Adjustment failed");
}

// Pull the server-generated adjustment_number out of the echoed DataElements
string? adjustmentNumber = null;
foreach (var txn in result["Results"]?["Transactions"] as JArray ?? new JArray())
foreach (var de in txn["DataElements"] as JArray ?? new JArray())
{
    if (de["Name"]?.ToString() != "TABPAGE_1.tp_1_dw_1") continue;
    foreach (var row in de["Rows"] as JArray ?? new JArray())
    foreach (var edit in row["Edits"] as JArray ?? new JArray())
        if (edit["Name"]?.ToString() == "adjustment_number" &&
            !string.IsNullOrEmpty(edit["Value"]?.ToString()))
            adjustmentNumber = edit["Value"]!.ToString();
}
Console.WriteLine($"Adjustment number: {adjustmentNumber}");

// --- Read the adjustment back ---
var getPayload = new JObject
{
    ["ServiceName"] = "InventoryAdjustment",
    ["TransactionStates"] = new JArray
    {
        new JObject
        {
            ["DataElementName"] = "TABPAGE_1.tp_1_dw_1",
            ["Keys"] = new JArray
            {
                new JObject { ["Name"] = "adjustment_number", ["Value"] = adjustmentNumber }
            }
        }
    }
};
var getResp = await session.Http.PostAsync(
    $"{session.UiServer}/api/v2/transaction/get",
    new StringContent(getPayload.ToString(), Encoding.UTF8, "application/json"));
getResp.EnsureSuccessStatusCode();
var getResult = JObject.Parse(await getResp.Content.ReadAsStringAsync());

var wanted = new[] { "adjustment_number", "location_id", "reason_id",
                     "item_id", "unit_quantity", "new_qoh" };
foreach (var txn in getResult["Transactions"] as JArray ?? new JArray())
foreach (var de in txn["DataElements"] as JArray ?? new JArray())
foreach (var row in de["Rows"] as JArray ?? new JArray())
foreach (var edit in row["Edits"] as JArray ?? new JArray())
    if (wanted.Contains(edit["Name"]?.ToString()))
        Console.WriteLine($"  {edit["Name"]}: {edit["Value"]}");
```
<!-- /tabs -->

> **End-to-end files** (runnable from the repo with a `.env`, dry-run by default): [`scripts/recipes/inventory_adjustment.py`](../../scripts/recipes/inventory_adjustment.py) · [`examples/csharp/Recipes/InventoryAdjustment.cs`](../../examples/csharp/Recipes/InventoryAdjustment.cs). The snippet above is self-contained; the files use the repo's shared `common` / `P21Examples.Common` helpers like every other example.

## Gotchas

- **`reason_id` takes the display text** of the reason — not its code — with `UseCodeValues: false`.
- **`unit_quantity` is the signed delta**, not the new on-hand. `-5` removes 5 units; the resulting quantity shows in `new_qoh`. To zero an item out, post the negative of its current on-hand.
- **The save posts the adjustment** — there is no draft state in this flow, and no invoice is involved.
- **Definition-required header fields:** besides `location_id` and `reason_id` (the manual's verified pair), the [definition](../../definitions/InventoryAdjustment.json) marks `company_id`, `period`, and `year_for_period` as `Required` on `tp_1_dw_1`.
- **HTTP 200 is not success** — check `Summary.Succeeded` / `Summary.Failed` and print `Messages`.

## Verify

Read the adjustment back by its key (second half of the example): `POST /api/v2/transaction/get` on `InventoryAdjustment`, element `TABPAGE_1.tp_1_dw_1`, keyed by the server-generated `adjustment_number` — confirm the header (`location_id`, `reason_id`) and the line's `item_id` / `unit_quantity` landed, and check `new_qoh` for the resulting on-hand.

> **Credit:** [Alex Westemeier](https://github.com/AWestemeier)
