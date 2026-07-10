# Update Contract Lines

Update prices on existing `JobContractPricing` lines, insert new lines onto an existing contract (upsert), and set commission costs — all through the stateless Transaction API.

**API:** Transaction (`POST {ui_server}/api/v2/transaction`) · **Service:** `JobContractPricing` · **Deep dive:** [JobContractPricing Service](../03-Transaction-API.md#jobcontractpricing-service) · [Updating an Existing Contract](../03-Transaction-API.md#updating-an-existing-contract) · [Upsert Semantics](../03-Transaction-API.md#upsert-semantics----keyed-rows-insert-when-absent) · [Commission Costs](../03-Transaction-API.md#commission-costs) · [Field Order Matters](../03-Transaction-API.md#field-order-matters) · [Known Limitations](../03-Transaction-API.md#known-limitations) · **Full schema:** [`definitions/JobContractPricing.json`](../../definitions/JobContractPricing.json)

## Prerequisites

- The contract already exists — know its `contract_no` and its `job_no`. Renewals can leave the same `contract_no` on two header rows; `job_no` is unique, so include it whenever it's known.
- Look up the current header values (`company_id`, `job_no`, `end_date`) before writing — the header is re-validated on every save. Use `POST {ui_server}/api/v2/transaction/get`:

  ```json
  {
    "ServiceName": "JobContractPricing",
    "TransactionStates": [{
      "DataElementName": "FORM.d_dw_job_price_hdr",
      "Keys": [{"Name": "contract_no", "Value": "A120-12"}]
    }]
  }
  ```
- The contract's `end_date` must be **>= today** (or you must move it forward in the same call — a real side effect). Expired contracts cannot have their lines edited this way; use the Interactive API for those.
- For **commission costs only**: the payload needs `IgnoreDisabled: true` at the top level — see [IgnoreDisabled](../03-Transaction-API.md#ignoredisabled).

## Payload

`Status` is `"New"` for both create and update — the API distinguishes them by whether the FORM key fields (`company_id`, `contract_no`, `job_no`) land on an existing record. The keyed `JOBPRICELINE` row is an **upsert**: matching `item_id` updates that line; no match inserts a new line.

```jsonc
{
    "Name": "JobContractPricing",
    "UseCodeValues": false,
    "IgnoreDisabled": true,            // top level — only needed when writing commission costs
    "Transactions": [{
        "Status": "New",               // "New" for BOTH create and update — "Existing" returns HTTP 500
        "DataElements": [
            {
                // Header: Keys stays EMPTY; the key fields go in Edits.
                "Name": "FORM.d_dw_job_price_hdr",
                "Type": "Form",
                "Keys": [],
                "Rows": [{
                    "Edits": [
                        {"Name": "company_id",  "Value": "ACME"},
                        {"Name": "contract_no", "Value": "A120-12"},
                        {"Name": "job_no",      "Value": "31"},        // unique across renewals
                        {"Name": "end_date",    "Value": "2030-01-01"} // required on EVERY submit, must be >= today
                    ],
                    "RelativeDateEdits": []
                }]
            },
            {
                // Line: keyed by item_id — updates the row if it exists, inserts it if not
                "Name": "JOBPRICELINE.jobpriceline",
                "Type": "List",
                "Keys": ["item_id"],
                "Rows": [{
                    "Edits": [
                        {"Name": "item_id",        "Value": "WIDGET-001"},
                        {"Name": "uom",            "Value": "EA"},
                        {"Name": "pricing_method", "Value": "Price"},  // MUST come before price
                        {"Name": "price",          "Value": "36.58"}
                    ],
                    "RelativeDateEdits": []
                }]
            },
            {
                // Optional: commission cost (requires IgnoreDisabled above)
                "Name": "JOBPRICECOST.jobpricecost",
                "Type": "Form",
                "Keys": ["item_id"],
                "Rows": [{
                    "Edits": [
                        {"Name": "item_id",                 "Value": "WIDGET-001"},
                        {"Name": "commission_cost_type_cd", "Value": "Value"},   // type BEFORE value; labels: Order, Source, Value, None
                        {"Name": "commission_cost_value",   "Value": "17.19"}
                    ]
                }]
            }
        ]
    }]
}
```

**Break-line variant:** for quantity-break lines set `pricing_method` to `"Source"`, `source_price` to `"Supplier List Price"` (or other source), and `multiplier` — do **not** send `price`. See [JobContractPricing Service](../03-Transaction-API.md#jobcontractpricing-service) for the VALUES break-tier structure.

## Complete example

<!-- tabs -->
```python
import httpx  # p21_auth() from recipes/README.md

BASE_URL = "https://play.p21server.com"
token, ui_server, headers = p21_auth(BASE_URL, "api_user", "api_pass")

CONTRACT = {"company_id": "ACME", "contract_no": "A120-12",
            "job_no": "31", "end_date": "2030-01-01"}


def line_payload(contract: dict, item_id: str, uom: str, price: float,
                 commission_cost: float | None = None) -> dict:
    """Build a one-line upsert payload, optionally with a commission cost."""
    elements = [
        {"Name": "FORM.d_dw_job_price_hdr", "Type": "Form", "Keys": [],
         "Rows": [{"Edits": [
             {"Name": "company_id",  "Value": contract["company_id"]},
             {"Name": "contract_no", "Value": contract["contract_no"]},
             {"Name": "job_no",      "Value": contract["job_no"]},
             {"Name": "end_date",    "Value": contract["end_date"]},
         ], "RelativeDateEdits": []}]},
        {"Name": "JOBPRICELINE.jobpriceline", "Type": "List", "Keys": ["item_id"],
         "Rows": [{"Edits": [
             {"Name": "item_id",        "Value": item_id},
             {"Name": "uom",            "Value": uom},
             {"Name": "pricing_method", "Value": "Price"},   # before price!
             {"Name": "price",          "Value": str(price)},
         ], "RelativeDateEdits": []}]},
    ]
    payload = {"Name": "JobContractPricing", "UseCodeValues": False,
               "Transactions": [{"Status": "New", "DataElements": elements}]}
    if commission_cost is not None:
        payload["IgnoreDisabled"] = True  # top level, NOT inside the Transaction
        elements.append(
            {"Name": "JOBPRICECOST.jobpricecost", "Type": "Form", "Keys": ["item_id"],
             "Rows": [{"Edits": [
                 {"Name": "item_id",                 "Value": item_id},
                 {"Name": "commission_cost_type_cd", "Value": "Value"},  # type before value
                 {"Name": "commission_cost_value",   "Value": str(commission_cost)},
             ]}]})
    return payload


def post_line(payload: dict) -> bool:
    """POST one transaction; True only if the Summary says it landed."""
    resp = httpx.post(f"{ui_server}/api/v2/transaction",
                      headers=headers, json=payload, verify=False, timeout=60)
    resp.raise_for_status()  # HTTP 200 even when the transaction failed
    result = resp.json()
    summary = result["Summary"]
    if summary["Failed"] or not summary["Succeeded"]:
        for msg in result.get("Messages", []):
            print(f"  FAILED: {msg}")
        return False
    return True


# One POST per line: inserts re-save the shared header and collide when batched.
lines = [
    ("WIDGET-001", "EA", 36.58, 17.19),  # already on contract -> updated
    ("WIDGET-002", "EA", 12.40, None),   # not on contract     -> inserted (upsert)
]
for item_id, uom, price, commission in lines:
    ok = post_line(line_payload(CONTRACT, item_id, uom, price, commission))
    print(f"{item_id}: {'OK' if ok else 'failed'}")

# --- Verify via OData (no joins: chain the uid columns) ---
def odata(table: str, filter_expr: str) -> list[dict]:
    resp = httpx.get(f"{BASE_URL}/odataservice/odata/table/{table}",
                     params={"$filter": filter_expr},
                     headers=headers, verify=False)
    resp.raise_for_status()
    return resp.json()["value"]

# Renewals can return two headers for one contract_no — match job_no too.
hdr = odata("job_price_hdr", f"contract_no eq '{CONTRACT['contract_no']}'")[0]
for item_id, _uom, price, _c in lines:
    im_uid = odata("inv_mast", f"item_id eq '{item_id}'")[0]["inv_mast_uid"]
    line = odata("job_price_line",
                 f"job_price_hdr_uid eq {hdr['job_price_hdr_uid']} "
                 f"and inv_mast_uid eq {im_uid}")[0]
    match = "OK" if float(line["price"]) == price else "MISMATCH"
    print(f"{item_id}: price={line['price']} expected={price} -> {match}")
```

```csharp
using System.Net.Http;
using System.Text;
using Newtonsoft.Json.Linq;

var session = await P21Session.CreateAsync(
    "https://play.p21server.com", "api_user", "api_pass");
const string BaseUrl = "https://play.p21server.com";

var contract = new { CompanyId = "ACME", ContractNo = "A120-12",
                     JobNo = "31", EndDate = "2030-01-01" };

JObject Edit(string name, string value) =>
    new JObject { ["Name"] = name, ["Value"] = value };

JObject LinePayload(string itemId, string uom, decimal price, decimal? commissionCost)
{
    var elements = new JArray
    {
        new JObject
        {
            ["Name"] = "FORM.d_dw_job_price_hdr", ["Type"] = "Form",
            ["Keys"] = new JArray(),
            ["Rows"] = new JArray { new JObject {
                ["Edits"] = new JArray {
                    Edit("company_id",  contract.CompanyId),
                    Edit("contract_no", contract.ContractNo),
                    Edit("job_no",      contract.JobNo),
                    Edit("end_date",    contract.EndDate),
                },
                ["RelativeDateEdits"] = new JArray() } }
        },
        new JObject
        {
            ["Name"] = "JOBPRICELINE.jobpriceline", ["Type"] = "List",
            ["Keys"] = new JArray { "item_id" },
            ["Rows"] = new JArray { new JObject {
                ["Edits"] = new JArray {
                    Edit("item_id",        itemId),
                    Edit("uom",            uom),
                    Edit("pricing_method", "Price"),          // before price!
                    Edit("price",          price.ToString()),
                },
                ["RelativeDateEdits"] = new JArray() } }
        },
    };
    var payload = new JObject
    {
        ["Name"] = "JobContractPricing", ["UseCodeValues"] = false,
        ["Transactions"] = new JArray {
            new JObject { ["Status"] = "New", ["DataElements"] = elements } }
    };
    if (commissionCost is not null)
    {
        payload["IgnoreDisabled"] = true;  // top level, NOT inside the Transaction
        elements.Add(new JObject
        {
            ["Name"] = "JOBPRICECOST.jobpricecost", ["Type"] = "Form",
            ["Keys"] = new JArray { "item_id" },
            ["Rows"] = new JArray { new JObject { ["Edits"] = new JArray {
                Edit("item_id",                 itemId),
                Edit("commission_cost_type_cd", "Value"),     // type before value
                Edit("commission_cost_value",   commissionCost.ToString()!),
            } } }
        });
    }
    return payload;
}

async Task<bool> PostLineAsync(JObject payload)
{
    var resp = await session.Http.PostAsync(
        $"{session.UiServer}/api/v2/transaction",
        new StringContent(payload.ToString(), Encoding.UTF8, "application/json"));
    resp.EnsureSuccessStatusCode();  // HTTP 200 even when the transaction failed
    var result = JObject.Parse(await resp.Content.ReadAsStringAsync());
    var summary = result["Summary"]!;
    if ((int)summary["Failed"]! > 0 || (int)summary["Succeeded"]! == 0)
    {
        foreach (var msg in result["Messages"] as JArray ?? new JArray())
            Console.WriteLine($"  FAILED: {msg}");
        return false;
    }
    return true;
}

// One POST per line: inserts re-save the shared header and collide when batched.
var lines = new (string ItemId, string Uom, decimal Price, decimal? Commission)[]
{
    ("WIDGET-001", "EA", 36.58m, 17.19m),  // already on contract -> updated
    ("WIDGET-002", "EA", 12.40m, null),    // not on contract     -> inserted (upsert)
};
foreach (var l in lines)
{
    var ok = await PostLineAsync(LinePayload(l.ItemId, l.Uom, l.Price, l.Commission));
    Console.WriteLine($"{l.ItemId}: {(ok ? "OK" : "failed")}");
}

// --- Verify via OData (no joins: chain the uid columns) ---
async Task<JArray> ODataAsync(string table, string filter)
{
    var url = $"{BaseUrl}/odataservice/odata/table/{table}" +
              $"?$filter={Uri.EscapeDataString(filter)}";
    var resp = await session.Http.GetAsync(url);
    resp.EnsureSuccessStatusCode();
    return (JArray)JObject.Parse(await resp.Content.ReadAsStringAsync())["value"]!;
}

// Renewals can return two headers for one contract_no — match job_no too.
var hdr = (JObject)(await ODataAsync("job_price_hdr",
    $"contract_no eq '{contract.ContractNo}'"))[0];
foreach (var l in lines)
{
    var imUid = (await ODataAsync("inv_mast", $"item_id eq '{l.ItemId}'"))[0]["inv_mast_uid"];
    var line = (await ODataAsync("job_price_line",
        $"job_price_hdr_uid eq {hdr["job_price_hdr_uid"]} and inv_mast_uid eq {imUid}"))[0];
    var match = (decimal)line["price"]! == l.Price ? "OK" : "MISMATCH";
    Console.WriteLine($"{l.ItemId}: price={line["price"]} expected={l.Price} -> {match}");
}
```
<!-- /tabs -->

## Gotchas

- **`pricing_method` must precede `price` in the Edits.** Changing `pricing_method` clears the typed price, exactly as in the UI — reversed order writes the line with **price = $0** and the transaction still reports `Succeeded`. Verified live. Order the Edits `item_id`, `pricing_method`, `price`.
- **One transaction per POST when inserting lines.** Every transaction re-saves the shared FORM header; batched inserts collide — all but one fail with an optimistic-concurrency error, and the ones that land can get **duplicate `line_no`** values. Edits to existing keyed rows batch fine.
- **`Status: "Existing"` (or `"Update"`, `"Change"`) returns HTTP 500** (`NullReferenceException`). Use `"New"` for both create and update.
- **`end_date` must be >= today** — the header is validated on every save, so you cannot edit lines on an expired contract without also moving its `end_date` forward. For expired contracts, use the Interactive API.
- **Include `job_no` to disambiguate renewals** — the same `contract_no` can exist on two header rows; `job_no` is unique.
- **`IgnoreDisabled: true` goes at the payload top level** (alongside `Name`/`Transactions`). Inside a Transaction object it is silently ignored and commission-cost writes fail with `Column is disabled: commission_cost_value`.
- **Set `commission_cost_type_cd` before `commission_cost_value`.** Accepted display labels (with `UseCodeValues: false`): `Order`, `Source`, `Value`, `None`. Setting only the commission cost leaves `other_cost` untouched.
- **Non-break vs break lines:** fixed price → `pricing_method: "Price"` + `price` (no `source_price`/`multiplier`); breaks → `pricing_method: "Source"` + `source_price` + `multiplier` (no `price`). Converting `"Source"` → `"Price"` works in one call; the old `source_price`/`multiplier` are not auto-cleared but become dormant.
- **`corp_address_id` is read-only after the initial save** — it can only be set at creation.
- **HTTP 200 is not success.** Check `Summary.Succeeded`/`Summary.Failed` and print `Messages`; transactions in a bulk POST pass/fail independently.
- **Per-line latency ~0.8s.** For bulk updates, single-line POSTs are easier to retry than batches.

## Verify

Chain OData uid lookups (no joins): `job_price_hdr` by `contract_no` → `job_price_hdr_uid`; `inv_mast` by `item_id` → `inv_mast_uid`; then check the line:

```http
GET /odataservice/odata/table/job_price_line?$filter=job_price_hdr_uid eq {uid} and inv_mast_uid eq {im_uid}
```

Confirm `price` matches what you submitted (the complete example above does this for every line). Commission costs and `line_no` uniqueness can be confirmed the same way after inserts.

> **Credit:** [Alex Westemeier](https://github.com/AWestemeier) — verified the update path, the upsert/header-collision behavior, the `pricing_method` ordering cascade, and the `IgnoreDisabled` commission-cost write path.
