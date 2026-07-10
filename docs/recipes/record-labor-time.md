# Record Labor Time on a Production Order

Post a technician's labor hours to a production order with the `TimeEntry` service.

**API:** Transaction · **Service:** `TimeEntry` · **Deep dive:** [Recording Labor Hours](../12-Production-Labor-API.md#recording-labor-hours-timeentry-service), [Quick Time Entry mechanics](../12-Production-Labor-API.md#time-entry-against-a-production-order-quick-time-entry), [Labor timing](../12-Production-Labor-API.md#labor-timing--log-labor-before-printing) · **Full schema:** [definitions/TimeEntry.json](../../definitions/TimeEntry.json)

## Prerequisites

- A production order exists (here `1000123`) with an assembly line (item `ASSY-100`) carrying a labor component (here `LABOR-SHOP`).
- `technician_id` is a **contact ID** (here `300`) — not a P21 user ID.
- The **accounting period for `entry_date` must be open**, or the save fails.
- If the order will be completed later: **log labor before printing the pick ticket** (or reprint after) — labor must land on a pick ticket to be consumed at completion. See [the runbook](production-order-runbook.md).
- For labor against **service orders**, use the separate `TimeEntrySO` service instead.

## Payload

`POST {ui_server}/api/v2/transaction`, `Status: "New"`, `UseCodeValues: false`. Two DataElements:

**Header — `TP_TECHNICIAN.tp_technician` (Form)**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `company_id` | Char | Yes | Company ID |
| `technician_id` | Char | Yes | **A contact ID**, not a user ID |
| `entry_date` | Datetime | Yes | Accounting period for this date must be open |

**Labor lines — `TP_LABORRECORDING.prod_order_line_comp_labor` (List, key `prod_order_number`)**

Enter the fields **in this order** — out of order, the downstream fields stay disabled:

| # | Field | Type | Notes |
|---|-------|------|-------|
| 1 | `prod_order_number` | Decimal | Key. The production order |
| 2 | `item_id` | Char | The assembly **line's** item (not the component) |
| 3 | `component_labor_id` | Char | The labor component on that line |
| 4 | `start_time` | Datetime | |
| 5 | `end_time` | Datetime | |

Other fields from the definition: `service_labor_id` (labor ID from the `Labor` service — the alternate lookup used in the [manual's reference example](../12-Production-Labor-API.md#recording-labor-hours-timeentry-service)), `time_worked` (Char, `HH:MM`), `labor_type_cd` (Long, **required** — valid values `Rate`, `OT Rate`, `Prem Rate`), `operation_cd`, `cc_completeprodorder`.

Time is stored per line at minute granularity and **accumulates across entries**; cost = minutes × the labor code's rate.

## Complete example

Posts 4 hours against the labor component, then reads the labor grid back. Auth comes from the [shared helper](README.md#shared-conventions-recipes-dont-repeat-these).

<!-- tabs -->
```python
import httpx

BASE_URL = "https://play.p21server.com"
token, ui_server, headers = p21_auth(BASE_URL, "api_user", "api_pass")

PROD_ORDER = "1000123"

payload = {
    "Name": "TimeEntry",
    "UseCodeValues": False,
    "Transactions": [{
        "Status": "New",
        "DataElements": [
            {
                "Name": "TP_TECHNICIAN.tp_technician",
                "Type": "Form",
                "Keys": [],
                "Rows": [{
                    "Edits": [
                        {"Name": "company_id", "Value": "ACME"},
                        {"Name": "technician_id", "Value": "300"},  # CONTACT id
                        {"Name": "entry_date", "Value": "2030-01-05"},
                    ],
                    "RelativeDateEdits": [],
                }],
            },
            {
                "Name": "TP_LABORRECORDING.prod_order_line_comp_labor",
                "Type": "List",
                "Keys": ["prod_order_number"],
                "Rows": [{
                    # Strict order: prod_order_number -> item_id ->
                    # component_labor_id -> start_time -> end_time
                    "Edits": [
                        {"Name": "prod_order_number", "Value": PROD_ORDER},
                        {"Name": "item_id", "Value": "ASSY-100"},
                        {"Name": "component_labor_id", "Value": "LABOR-SHOP"},
                        {"Name": "start_time", "Value": "2030-01-05T08:00:00"},
                        {"Name": "end_time", "Value": "2030-01-05T12:00:00"},
                        {"Name": "labor_type_cd", "Value": "Rate"},
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
    raise SystemExit("Time entry failed")

# --- Read back the labor grid for the order ---
get_payload = {
    "ServiceName": "TimeEntry",
    "TransactionStates": [{
        "DataElementName": "TP_LABORRECORDING.prod_order_line_comp_labor",
        "Keys": [{"Name": "prod_order_number", "Value": PROD_ORDER}],
    }],
}
resp = httpx.post(f"{ui_server}/api/v2/transaction/get",
                  headers=headers, json=get_payload, verify=False)
resp.raise_for_status()
for txn in resp.json().get("Transactions", []):
    for de in txn.get("DataElements", []):
        for row in de.get("Rows", []):
            fields = {e["Name"]: e["Value"] for e in row.get("Edits", [])}
            if fields.get("prod_order_number"):
                print(f"  {fields.get('component_labor_id') or fields.get('service_labor_id')}: "
                      f"time_worked={fields.get('time_worked')}")
```

```csharp
var session = await P21Session.CreateAsync(
    "https://play.p21server.com", "api_user", "api_pass");

const string prodOrder = "1000123";

var payload = new JObject
{
    ["Name"] = "TimeEntry",
    ["UseCodeValues"] = false,
    ["Transactions"] = new JArray
    {
        new JObject
        {
            ["Status"] = "New",
            ["DataElements"] = new JArray
            {
                new JObject
                {
                    ["Name"] = "TP_TECHNICIAN.tp_technician",
                    ["Type"] = "Form",
                    ["Keys"] = new JArray(),
                    ["Rows"] = new JArray
                    {
                        new JObject
                        {
                            ["Edits"] = new JArray
                            {
                                new JObject { ["Name"] = "company_id", ["Value"] = "ACME" },
                                new JObject { ["Name"] = "technician_id", ["Value"] = "300" }, // CONTACT id
                                new JObject { ["Name"] = "entry_date", ["Value"] = "2030-01-05" }
                            },
                            ["RelativeDateEdits"] = new JArray()
                        }
                    }
                },
                new JObject
                {
                    ["Name"] = "TP_LABORRECORDING.prod_order_line_comp_labor",
                    ["Type"] = "List",
                    ["Keys"] = new JArray { "prod_order_number" },
                    ["Rows"] = new JArray
                    {
                        new JObject
                        {
                            // Strict order: prod_order_number -> item_id ->
                            // component_labor_id -> start_time -> end_time
                            ["Edits"] = new JArray
                            {
                                new JObject { ["Name"] = "prod_order_number", ["Value"] = prodOrder },
                                new JObject { ["Name"] = "item_id", ["Value"] = "ASSY-100" },
                                new JObject { ["Name"] = "component_labor_id", ["Value"] = "LABOR-SHOP" },
                                new JObject { ["Name"] = "start_time", ["Value"] = "2030-01-05T08:00:00" },
                                new JObject { ["Name"] = "end_time", ["Value"] = "2030-01-05T12:00:00" },
                                new JObject { ["Name"] = "labor_type_cd", ["Value"] = "Rate" }
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
    throw new Exception("Time entry failed");
}

// --- Read back the labor grid for the order ---
var getPayload = new JObject
{
    ["ServiceName"] = "TimeEntry",
    ["TransactionStates"] = new JArray
    {
        new JObject
        {
            ["DataElementName"] = "TP_LABORRECORDING.prod_order_line_comp_labor",
            ["Keys"] = new JArray
            {
                new JObject { ["Name"] = "prod_order_number", ["Value"] = prodOrder }
            }
        }
    }
};
var getResp = await session.Http.PostAsync(
    $"{session.UiServer}/api/v2/transaction/get",
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
    if (!string.IsNullOrEmpty(fields.GetValueOrDefault("prod_order_number")))
        Console.WriteLine($"  {fields.GetValueOrDefault("component_labor_id")}: " +
                          $"time_worked={fields.GetValueOrDefault("time_worked")}");
}
```
<!-- /tabs -->

## Gotchas

- **Strict field order** on the labor grid: `prod_order_number` → `item_id` → `component_labor_id` → `start_time` → `end_time`. Out of order, the downstream fields stay disabled and the values don't land.
- **`technician_id` is a contact ID**, not a P21 user ID.
- **The accounting period for `entry_date` must be open** — a closed period fails the save.
- **Time accumulates.** Each entry adds to the line's stored hours/minutes; re-posting the same entry doubles the labor (and its cost = minutes × the labor code's rate).
- **Log labor before printing the pick ticket** (or reprint after adding it). Labor on no ticket has `qty_on_pick_tickets = 0` and order completion fails with *"components have a quantity used of 0."*
- **Cost timing:** labor posted before completion lands in the `PROP` receipt cost; labor posted after completion misses it; labor posted after invoicing generates a separate *"Post Freight/Labor Prod. Order: NNNN"* invoice ($0 price, ± COGS). See [the cost model](../12-Production-Labor-API.md#cost-model--know-this-before-trusting-cogs).
- **`labor_type_cd` is required** — valid values `Rate`, `OT Rate`, `Prem Rate` (with `UseCodeValues: false`).
- **HTTP 200 is not success** — check `Summary.Succeeded` / `Summary.Failed` and print `Messages`.

## Verify

Read the labor grid back (second half of the example): `POST /api/v2/transaction/get` on `TimeEntry`, element `TP_LABORRECORDING.prod_order_line_comp_labor`, keyed by `prod_order_number` — the line's `time_worked` should reflect the **accumulated** total, not just this entry. A successful post also returns `Status: "Passed"` on the transaction with `Summary.Succeeded: 1`.

> **Credit:** [Alex Westemeier](https://github.com/AWestemeier)
