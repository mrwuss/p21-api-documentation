# Edit Contract Bin Quantities

Change `min_qty`, `max_qty`, `reorder_qty`, and `capacity` on the bins of an existing job contract.

**API:** Transaction with `IgnoreDisabled: true` (Interactive API fallback) · **Service:** `JobContractPricing` · **Deep dive:** [Editing Bin Quantities](../03-Transaction-API.md#editing-bin-quantities-on-an-existing-contract) · [IgnoreDisabled](../03-Transaction-API.md#ignoredisabled) · [Tab Unlock Sequences (Interactive fallback)](../04-Interactive-API.md#tab-unlock-sequences) · **Full schema:** [`definitions/JobContractPricing.json`](../../definitions/JobContractPricing.json)

## Prerequisites

- The contract, its lines, and its bins already exist. Know the contract's `job_no`, the `customer_id`/`ship_to_id` combination, and per bin the line's `item_id` and the `contract_bin_id` (e.g. `A01-02`).
- The BINS grid lives on a sub-tab that is normally disabled until a parent row is selected — which the stateless Transaction API cannot do. `IgnoreDisabled: true` at the **payload top level** is what unlocks it.
- No `end_date` is required on this path — it works on **expired** contracts too, unlike line-field updates.

## Payload

One POST, batchable: repeat the `JOBPRICELINE` + `BINS.bins` pair per bin inside the same Transaction. The `JOBPRICELINE` element only *selects* the line (by `item_id`); the `BINS.bins` element carries the edits.

```jsonc
{
    "Name": "JobContractPricing",
    "UseCodeValues": false,
    "IgnoreDisabled": true,        // MANDATORY, and at the top level — inside a Transaction it is silently ignored
    "Transactions": [{
        "Status": "New",           // "New" even though the contract exists — "Existing" returns HTTP 500
        "DataElements": [
            {
                // Load the contract header. job_no is unique across renewals.
                "Name": "FORM.d_dw_job_price_hdr", "Type": "Form", "Keys": [],
                "Rows": [{"Edits": [
                    {"Name": "job_no",      "Value": "31"},
                    {"Name": "customer_id", "Value": "100198"},
                    {"Name": "ship_to_id",  "Value": "200"}
                ]}]
            },
            {
                // Select the line by item_id (NOT line_no).
                "Name": "JOBPRICELINE.jobpriceline", "Type": "List", "Keys": ["item_id"],
                "Rows": [{"Edits": [
                    {"Name": "item_id", "Value": "WIDGET-001"}
                ]}]
            },
            {
                // Edit the bin quantities.
                "Name": "BINS.bins", "Type": "List",
                "Keys": ["contract_bin_id", "customer_id", "ship_to_id"],
                "Rows": [{"Edits": [
                    {"Name": "contract_bin_id", "Value": "A01-02"},
                    {"Name": "customer_id",     "Value": "100198"},
                    {"Name": "ship_to_id",      "Value": "200"},
                    {"Name": "min_qty",         "Value": "30"},
                    {"Name": "max_qty",         "Value": "100"},
                    {"Name": "reorder_qty",     "Value": "40"},
                    {"Name": "capacity",        "Value": "100"}
                ]}]
            }
            // ...repeat the JOBPRICELINE + BINS.bins pair for each additional bin
        ]
    }]
}
```

## Complete example

<!-- tabs -->
```python
import httpx  # p21_auth() from recipes/README.md

BASE_URL = "https://play.p21server.com"
token, ui_server, headers = p21_auth(BASE_URL, "api_user", "api_pass")

CONTRACT_NO = "A120-12"
JOB_NO, CUSTOMER_ID, SHIP_TO_ID = "31", "100198", "200"

# Per bin: the line's item_id, the bin id, and the new quantities.
bin_edits = [
    {"item_id": "WIDGET-001", "bin_id": "A01-02",
     "min_qty": 30, "max_qty": 100, "reorder_qty": 40, "capacity": 100},
    {"item_id": "WIDGET-002", "bin_id": "A01-02",
     "min_qty": 5,  "max_qty": 50,  "reorder_qty": 10, "capacity": 50},
]


def build_bin_payload(job_no: str, customer_id: str, ship_to_id: str,
                      edits: list[dict]) -> dict:
    """One Transaction, one JOBPRICELINE + BINS.bins pair per bin."""
    elements = [
        {"Name": "FORM.d_dw_job_price_hdr", "Type": "Form", "Keys": [],
         "Rows": [{"Edits": [
             {"Name": "job_no",      "Value": job_no},
             {"Name": "customer_id", "Value": customer_id},
             {"Name": "ship_to_id",  "Value": ship_to_id},
         ]}]},
    ]
    for e in edits:
        elements.append(
            {"Name": "JOBPRICELINE.jobpriceline", "Type": "List",
             "Keys": ["item_id"],   # select by item_id, NOT line_no
             "Rows": [{"Edits": [{"Name": "item_id", "Value": e["item_id"]}]}]})
        elements.append(
            {"Name": "BINS.bins", "Type": "List",
             "Keys": ["contract_bin_id", "customer_id", "ship_to_id"],
             "Rows": [{"Edits": [
                 {"Name": "contract_bin_id", "Value": e["bin_id"]},
                 {"Name": "customer_id",     "Value": customer_id},
                 {"Name": "ship_to_id",      "Value": ship_to_id},
                 {"Name": "min_qty",         "Value": str(e["min_qty"])},
                 {"Name": "max_qty",         "Value": str(e["max_qty"])},
                 {"Name": "reorder_qty",     "Value": str(e["reorder_qty"])},
                 {"Name": "capacity",        "Value": str(e["capacity"])},
             ]}]})
    return {"Name": "JobContractPricing", "UseCodeValues": False,
            "IgnoreDisabled": True,  # top level — mandatory for the BINS sub-tab
            "Transactions": [{"Status": "New", "DataElements": elements}]}


payload = build_bin_payload(JOB_NO, CUSTOMER_ID, SHIP_TO_ID, bin_edits)
resp = httpx.post(f"{ui_server}/api/v2/transaction",
                  headers=headers, json=payload, verify=False, timeout=60)
resp.raise_for_status()  # HTTP 200 even when the transaction failed
result = resp.json()
summary = result["Summary"]
print(f"Succeeded: {summary['Succeeded']}, Failed: {summary['Failed']}")
if summary["Failed"] or not summary["Succeeded"]:
    for msg in result.get("Messages", []):
        print(f"  FAILED: {msg}")
    raise SystemExit(1)

# --- Verify via OData (no joins: chain the uid columns) ---
def odata(table: str, filter_expr: str) -> list[dict]:
    resp = httpx.get(f"{BASE_URL}/odataservice/odata/table/{table}",
                     params={"$filter": filter_expr},
                     headers=headers, verify=False)
    resp.raise_for_status()
    return resp.json()["value"]

hdr = odata("job_price_hdr", f"contract_no eq '{CONTRACT_NO}'")[0]
for e in bin_edits:
    im_uid = odata("inv_mast", f"item_id eq '{e['item_id']}'")[0]["inv_mast_uid"]
    line = odata("job_price_line",
                 f"job_price_hdr_uid eq {hdr['job_price_hdr_uid']} "
                 f"and inv_mast_uid eq {im_uid}")[0]
    for bin_row in odata("job_price_bin",
                         f"job_price_line_uid eq {line['job_price_line_uid']}"):
        print(f"{e['item_id']}: min={bin_row['min_qty']} max={bin_row['max_qty']} "
              f"reorder={bin_row['reorder_qty']} "
              f"(expected {e['min_qty']}/{e['max_qty']}/{e['reorder_qty']})")
```

```csharp
using System.Net.Http;
using System.Text;
using Newtonsoft.Json.Linq;

var session = await P21Session.CreateAsync(
    "https://play.p21server.com", "api_user", "api_pass");
const string BaseUrl = "https://play.p21server.com";

const string ContractNo = "A120-12";
const string JobNo = "31", CustomerId = "100198", ShipToId = "200";

// Per bin: the line's item_id, the bin id, and the new quantities.
var binEdits = new (string ItemId, string BinId, int Min, int Max, int Reorder, int Capacity)[]
{
    ("WIDGET-001", "A01-02", 30, 100, 40, 100),
    ("WIDGET-002", "A01-02", 5, 50, 10, 50),
};

JObject Edit(string name, string value) =>
    new JObject { ["Name"] = name, ["Value"] = value };

JObject BuildBinPayload()
{
    var elements = new JArray
    {
        new JObject
        {
            ["Name"] = "FORM.d_dw_job_price_hdr", ["Type"] = "Form",
            ["Keys"] = new JArray(),
            ["Rows"] = new JArray { new JObject { ["Edits"] = new JArray {
                Edit("job_no",      JobNo),
                Edit("customer_id", CustomerId),
                Edit("ship_to_id",  ShipToId),
            } } }
        }
    };
    foreach (var e in binEdits)
    {
        elements.Add(new JObject
        {
            ["Name"] = "JOBPRICELINE.jobpriceline", ["Type"] = "List",
            ["Keys"] = new JArray { "item_id" },   // select by item_id, NOT line_no
            ["Rows"] = new JArray { new JObject {
                ["Edits"] = new JArray { Edit("item_id", e.ItemId) } } }
        });
        elements.Add(new JObject
        {
            ["Name"] = "BINS.bins", ["Type"] = "List",
            ["Keys"] = new JArray { "contract_bin_id", "customer_id", "ship_to_id" },
            ["Rows"] = new JArray { new JObject { ["Edits"] = new JArray {
                Edit("contract_bin_id", e.BinId),
                Edit("customer_id",     CustomerId),
                Edit("ship_to_id",      ShipToId),
                Edit("min_qty",         e.Min.ToString()),
                Edit("max_qty",         e.Max.ToString()),
                Edit("reorder_qty",     e.Reorder.ToString()),
                Edit("capacity",        e.Capacity.ToString()),
            } } }
        });
    }
    return new JObject
    {
        ["Name"] = "JobContractPricing", ["UseCodeValues"] = false,
        ["IgnoreDisabled"] = true,  // top level — mandatory for the BINS sub-tab
        ["Transactions"] = new JArray {
            new JObject { ["Status"] = "New", ["DataElements"] = elements } }
    };
}

var resp = await session.Http.PostAsync(
    $"{session.UiServer}/api/v2/transaction",
    new StringContent(BuildBinPayload().ToString(), Encoding.UTF8, "application/json"));
resp.EnsureSuccessStatusCode();  // HTTP 200 even when the transaction failed
var result = JObject.Parse(await resp.Content.ReadAsStringAsync());
var summary = result["Summary"]!;
Console.WriteLine($"Succeeded: {summary["Succeeded"]}, Failed: {summary["Failed"]}");
if ((int)summary["Failed"]! > 0 || (int)summary["Succeeded"]! == 0)
{
    foreach (var msg in result["Messages"] as JArray ?? new JArray())
        Console.WriteLine($"  FAILED: {msg}");
    return;
}

// --- Verify via OData (no joins: chain the uid columns) ---
async Task<JArray> ODataAsync(string table, string filter)
{
    var url = $"{BaseUrl}/odataservice/odata/table/{table}" +
              $"?$filter={Uri.EscapeDataString(filter)}";
    var r = await session.Http.GetAsync(url);
    r.EnsureSuccessStatusCode();
    return (JArray)JObject.Parse(await r.Content.ReadAsStringAsync())["value"]!;
}

var hdr = (JObject)(await ODataAsync("job_price_hdr", $"contract_no eq '{ContractNo}'"))[0];
foreach (var e in binEdits)
{
    var imUid = (await ODataAsync("inv_mast", $"item_id eq '{e.ItemId}'"))[0]["inv_mast_uid"];
    var line = (await ODataAsync("job_price_line",
        $"job_price_hdr_uid eq {hdr["job_price_hdr_uid"]} and inv_mast_uid eq {imUid}"))[0];
    foreach (var binRow in await ODataAsync("job_price_bin",
        $"job_price_line_uid eq {line["job_price_line_uid"]}"))
    {
        Console.WriteLine($"{e.ItemId}: min={binRow["min_qty"]} max={binRow["max_qty"]} " +
                          $"reorder={binRow["reorder_qty"]} " +
                          $"(expected {e.Min}/{e.Max}/{e.Reorder})");
    }
}
```
<!-- /tabs -->

## Gotchas

All verified live:

- **`IgnoreDisabled: true` is mandatory** — without it the defaults template trips *"Column is disabled: ..."* and the BINS tab stays locked.
- **`IgnoreDisabled` goes at the payload top level** (alongside `Name`/`Transactions`). Inside a Transaction object it is **silently ignored** and every transaction fails with `Column is disabled: <column>`.
- **Select the line by `item_id`** (the `JOBPRICELINE` key). Selecting by `line_no` alone fails with *"Sequence contains no matching element."* If the same item appears on multiple lines, add `line_no` as a second key.
- **Batching is fine here** — repeat the `JOBPRICELINE` + `BINS.bins` pair per bin inside the same Transaction. Unlike line inserts, bin edits don't collide on the header.
- **No `end_date` required on this path** — it works on **expired** contracts too, unlike line-field updates.
- **`Status: "New"` even for an existing contract** — `"Existing"` returns HTTP 500 (`NullReferenceException`).
- **HTTP 200 can still carry `Summary.Failed > 0`** — check `Summary` and `Messages`, never the HTTP status.
- **Interactive fallback** (slower; use when a Transaction-API edge case appears or the work needs window logic) — the EXISTING-contract unlock sequence from [Tab Unlock Sequences](../04-Interactive-API.md#tab-unlock-sequences):
  1. Load the contract by setting `job_no`, `customer_id`, and `ship_to_id` on `FORM/d_dw_job_price_hdr` (three separate change calls). **Load by `job_no`, not `contract_no`** — renewals can leave the same `contract_no` on two header rows.
  2. Change to the `CUSTOMER_SHIP_TO` tab and **select the ship-to's grid row** — the BINS tab only unlocks after the row is selected. Skipping this (or loading by `contract_no` alone) leaves it disabled with *"Tab page is disabled and cannot be selected."*
  3. Per line: `JOBPRICELINE` tab → select the line's row → `BINS` tab. The grid is **filtered to the selected ship-to**, so it has exactly one row per line — selecting row 1 of `bins` always targets the right bin. Edit the quantity fields.
  4. One save at the end persists every edit in the session (save per ship-to on large runs so a mid-run failure doesn't lose everything).

## Verify

Chain OData uid lookups (no joins): `job_price_hdr` by `contract_no` → `job_price_line` by `job_price_hdr_uid` (+ `inv_mast_uid` from `inv_mast` for the item) → `job_price_bin` by `job_price_line_uid`, then confirm `min_qty` / `max_qty` / `reorder_qty`:

```http
GET /odataservice/odata/table/job_price_bin?$filter=job_price_line_uid eq {line_uid}
```

The complete example above does this for every edited bin.

> **Credit:** [Alex Westemeier](https://github.com/AWestemeier) — discovered and verified the `IgnoreDisabled` bins path (single and multi-bin batches, database-confirmed) and the Interactive-API existing-contract unlock sequence.
