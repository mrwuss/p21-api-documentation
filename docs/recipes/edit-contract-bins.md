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
"""Edit contract bin quantities, then read every edited bin back over OData."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
CONTRACT_NO = "JOB-1001"
JOB_NO = "31"                             # unique across renewals
CUSTOMER_ID = "100198"
SHIP_TO_ID = "200"
# Per bin: the line's item_id, the bin id, and the new quantities.
BIN_EDITS = [
    {"item_id": "WIDGET-001", "bin_id": "A01-02",
     "min_qty": 30, "max_qty": 100, "reorder_qty": 40, "capacity": 100},
    {"item_id": "WIDGET-002", "bin_id": "A01-02",
     "min_qty": 5,  "max_qty": 50,  "reorder_qty": 10, "capacity": 50},
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


with httpx.Client(verify=VERIFY_SSL, timeout=120, follow_redirects=True) as client:
    token = get_token(client)
    ui_server = get_ui_server(client, token)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",       # 2026.1 returns an empty 500 without this
        "Content-Type": "application/json",
    }

    def odata(table: str, filter_expr: str) -> list[dict]:
        r = client.get(f"{BASE_URL}/odataservice/odata/table/{table}",
                       params={"$filter": filter_expr}, headers=headers)
        r.raise_for_status()
        return r.json()["value"]

    payload = build_bin_payload(JOB_NO, CUSTOMER_ID, SHIP_TO_ID, BIN_EDITS)
    resp = client.post(f"{ui_server}/api/v2/transaction",
                       headers=headers, json=payload)
    resp.raise_for_status()  # HTTP 200 even when the transaction failed
    result = resp.json()
    summary = result["Summary"]
    print(f"Succeeded: {summary['Succeeded']}, Failed: {summary['Failed']}")
    if summary["Failed"] or not summary["Succeeded"]:
        for msg in result.get("Messages", []):
            print(f"  FAILED: {msg}")
        raise SystemExit(1)

    # --- Verify via OData (no joins: chain the uid columns) ---
    # Renewals can return two headers for one contract_no — match job_no too.
    hdr = odata("job_price_hdr",
                f"contract_no eq '{CONTRACT_NO}' and job_no eq '{JOB_NO}'")[0]
    for e in BIN_EDITS:
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
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string ContractNo = "JOB-1001";
const string JobNo = "31";              // unique across renewals
const string CustomerId = "100198";
const string ShipToId = "200";
// Per bin: the line's item_id, the bin id, and the new quantities.
var binEdits = new (string ItemId, string BinId, int Min, int Max, int Reorder, int Capacity)[]
{
    ("WIDGET-001", "A01-02", 30, 100, 40, 100),
    ("WIDGET-002", "A01-02", 5, 50, 10, 50),
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

static object Edit(string name, string value) => new { Name = name, Value = value };

object BuildBinPayload()
{
    var elements = new List<object>
    {
        new
        {
            Name = "FORM.d_dw_job_price_hdr",
            Type = "Form",
            Keys = Array.Empty<string>(),
            Rows = new object[]
            {
                new
                {
                    Edits = new[]
                    {
                        Edit("job_no", JobNo),
                        Edit("customer_id", CustomerId),
                        Edit("ship_to_id", ShipToId),
                    },
                },
            },
        },
    };
    foreach (var e in binEdits)
    {
        elements.Add(new
        {
            Name = "JOBPRICELINE.jobpriceline",
            Type = "List",
            Keys = new[] { "item_id" },   // select by item_id, NOT line_no
            Rows = new object[] { new { Edits = new[] { Edit("item_id", e.ItemId) } } },
        });
        elements.Add(new
        {
            Name = "BINS.bins",
            Type = "List",
            Keys = new[] { "contract_bin_id", "customer_id", "ship_to_id" },
            Rows = new object[]
            {
                new
                {
                    Edits = new[]
                    {
                        Edit("contract_bin_id", e.BinId),
                        Edit("customer_id", CustomerId),
                        Edit("ship_to_id", ShipToId),
                        Edit("min_qty", e.Min.ToString()),
                        Edit("max_qty", e.Max.ToString()),
                        Edit("reorder_qty", e.Reorder.ToString()),
                        Edit("capacity", e.Capacity.ToString()),
                    },
                },
            },
        });
    }
    return new
    {
        Name = "JobContractPricing",
        UseCodeValues = false,
        IgnoreDisabled = true,  // top level — mandatory for the BINS sub-tab
        Transactions = new object[] { new { Status = "New", DataElements = elements } },
    };
}

using var resp = await client.PostAsync(
    $"{uiServer}/api/v2/transaction",
    new StringContent(JsonSerializer.Serialize(BuildBinPayload()), Encoding.UTF8, "application/json"));
resp.EnsureSuccessStatusCode();  // HTTP 200 even when the transaction failed
using var result = JsonDocument.Parse(await resp.Content.ReadAsStringAsync());
var summary = result.RootElement.GetProperty("Summary");
var succeeded = summary.GetProperty("Succeeded").GetInt32();
var failed = summary.GetProperty("Failed").GetInt32();
Console.WriteLine($"Succeeded: {succeeded}, Failed: {failed}");
if (failed > 0 || succeeded == 0)
{
    if (result.RootElement.TryGetProperty("Messages", out var messages))
    {
        Console.Error.WriteLine($"  FAILED: {messages}");
    }
    return;
}

// --- Verify via OData (no joins: chain the uid columns) ---
// Renewals can return two headers for one contract_no — match job_no too.
var hdr = (await ODataAsync(client, "job_price_hdr",
    $"contract_no eq '{ContractNo}' and job_no eq '{JobNo}'"))[0];
foreach (var e in binEdits)
{
    var imUid = (await ODataAsync(client, "inv_mast", $"item_id eq '{e.ItemId}'"))[0]
        .GetProperty("inv_mast_uid");
    var line = (await ODataAsync(client, "job_price_line",
        $"job_price_hdr_uid eq {hdr.GetProperty("job_price_hdr_uid")} " +
        $"and inv_mast_uid eq {imUid}"))[0];
    foreach (var binRow in await ODataAsync(client, "job_price_bin",
        $"job_price_line_uid eq {line.GetProperty("job_price_line_uid")}"))
    {
        Console.WriteLine(
            $"{e.ItemId}: min={binRow.GetProperty("min_qty")} " +
            $"max={binRow.GetProperty("max_qty")} " +
            $"reorder={binRow.GetProperty("reorder_qty")} " +
            $"(expected {e.Min}/{e.Max}/{e.Reorder})");
    }
}

// --- helpers ---------------------------------------------------------------

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

> **Payload files:** [JSON](../../examples/payloads/json/edit-contract-bins.json) · [XML](../../examples/payloads/xml/edit-contract-bins.xml) — validator-verified, see [payloads README](../../examples/payloads/README.md).
>
> **End-to-end files** (runnable from the repo with a `.env`, dry-run by default): [`examples/python/recipes/edit_contract_bins.py`](../../examples/python/recipes/edit_contract_bins.py) · [`examples/csharp/Recipes/EditContractBins.cs`](../../examples/csharp/Recipes/EditContractBins.cs). The snippet above is self-contained; the files use the repo's shared `common` / `P21Examples.Common` helpers like every other example.

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
