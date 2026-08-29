# Update Contract Lines

Update prices on existing `JobContractPricing` lines, insert new lines onto an existing contract (upsert), and set commission costs — all through the stateless Transaction API.

**API:** Transaction (`POST {ui_server}/api/v2/transaction`) · **Service:** `JobContractPricing` · **Deep dive:** [JobContractPricing Service](../03-Transaction-API.md#jobcontractpricing-service) · [Updating an Existing Contract](../03-Transaction-API.md#updating-an-existing-contract) · [Upsert Semantics](../03-Transaction-API.md#upsert-semantics-keyed-rows-insert-when-absent) · [Commission Costs](../03-Transaction-API.md#commission-costs) · [Field Order Matters](../03-Transaction-API.md#field-order-matters) · [Known Limitations](../03-Transaction-API.md#known-limitations) · **Full schema:** [`definitions/JobContractPricing.json`](../../definitions/JobContractPricing.json)

> **Warning (verified on P21 26.1, 2026-08-11):** every write path for `JOBPRICELINE`'s
> `VALUES.values` break-tier data on `JobContractPricing` is refused with `General
> Exception: Tab page is disabled and cannot be selected` — updating `VALUES` on an
> existing line, inserting a new line (the keyed upsert this recipe documents) with
> `VALUES` in the same transaction, and creating a brand-new contract (header + line +
> `VALUES` in one transaction) all fail identically. Each of these fails atomically —
> nothing is created or changed, including the header/line that would otherwise have
> succeeded. As a control: the identical transaction with the `VALUES.values` element
> removed succeeds — contract and line creation both work fine; it is specifically the
> `VALUES.values` DataElement that is refused. For an existing line, adding
> `IgnoreDisabled: true` at the top level flips the response to `Succeeded: 1` /
> `Status: "Passed"` while writing NOTHING — the read-back shows the row unchanged, and
> the echoed response silently drops the `JOBPRICELINE` and `VALUES` elements. **In
> practice: the line upsert this recipe documents below still works, as long as the
> payload carries no `VALUES.values` element — the moment you add break tiers, the
> whole transaction is refused and the line does not land either.** Full write-up:
> [VALUES Writes Are Refused on 26.1](../03-Transaction-API.md#values-writes-are-refused-on-261).

## Prerequisites

- The contract already exists — know its `contract_no` and its `job_no`. Renewals can leave the same `contract_no` on two header rows; `job_no` is unique, so include it whenever it's known.
- Look up the current header values (`company_id`, `job_no`, `end_date`) before writing — the header is re-validated on every save. Use `POST {ui_server}/api/v2/transaction/get`:

  ```json
  {
    "ServiceName": "JobContractPricing",
    "TransactionStates": [{
      "DataElementName": "FORM.d_dw_job_price_hdr",
      "Keys": [{"Name": "contract_no", "Value": "JOB-1001"}]
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
        "Status": "New",               // "New" for BOTH create and update — it is the only value the enum takes
        "DataElements": [
            {
                // Header: Keys stays EMPTY; the key fields go in Edits.
                "Name": "FORM.d_dw_job_price_hdr",
                "Type": "Form",
                "Keys": [],
                "Rows": [{
                    "Edits": [
                        {"Name": "company_id",  "Value": "ACME"},
                        {"Name": "contract_no", "Value": "JOB-1001"},
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
"""Upsert job-contract lines (price + optional commission cost), then verify."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
CONTRACT = {"company_id": "ACME", "contract_no": "JOB-1001",
            "job_no": "31", "end_date": "2030-01-01"}   # end_date must be >= today
# One POST per line: inserts re-save the shared header and collide when batched.
LINES = [
    ("WIDGET-001", "EA", 36.58, 17.19),  # already on contract -> updated
    ("WIDGET-002", "EA", 12.40, None),   # not on contract     -> inserted (upsert)
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


with httpx.Client(verify=VERIFY_SSL, timeout=120, follow_redirects=True) as client:
    token = get_token(client)
    ui_server = get_ui_server(client, token)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",       # without this you get XML, not JSON
        "Content-Type": "application/json",
    }

    def post_line(payload: dict) -> bool:
        """POST one transaction; True only if the Summary says it landed."""
        resp = client.post(f"{ui_server}/api/v2/transaction",
                           headers=headers, json=payload)
        resp.raise_for_status()  # HTTP 200 even when the transaction failed
        result = resp.json()
        summary = result["Summary"]
        if summary["Failed"] or not summary["Succeeded"]:
            for msg in result.get("Messages", []):
                print(f"  FAILED: {msg}")
            return False
        return True

    def odata(table: str, filter_expr: str) -> list[dict]:
        resp = client.get(f"{BASE_URL}/odataservice/odata/table/{table}",
                          params={"$filter": filter_expr}, headers=headers)
        resp.raise_for_status()
        return resp.json()["value"]

    for item_id, uom, price, commission in LINES:
        ok = post_line(line_payload(CONTRACT, item_id, uom, price, commission))
        print(f"{item_id}: {'OK' if ok else 'failed'}")

    # --- Verify via OData (no joins: chain the uid columns) ---
    # Renewals can return two headers for one contract_no — match job_no too.
    hdr = odata("job_price_hdr",
                f"contract_no eq '{CONTRACT['contract_no']}' "
                f"and job_no eq '{CONTRACT['job_no']}'")[0]
    for item_id, _uom, price, _c in LINES:
        im_uid = odata("inv_mast", f"item_id eq '{item_id}'")[0]["inv_mast_uid"]
        line = odata("job_price_line",
                     f"job_price_hdr_uid eq {hdr['job_price_hdr_uid']} "
                     f"and inv_mast_uid eq {im_uid}")[0]
        match = "OK" if float(line["price"]) == price else "MISMATCH"
        print(f"{item_id}: price={line['price']} expected={price} -> {match}")
```

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
var contract = new
{
    CompanyId = "ACME",
    ContractNo = "JOB-1001",
    JobNo = "31",
    EndDate = "2030-01-01",   // must be >= today
};
// One POST per line: inserts re-save the shared header and collide when batched.
var lines = new (string ItemId, string Uom, decimal Price, decimal? Commission)[]
{
    ("WIDGET-001", "EA", 36.58m, 17.19m),  // already on contract -> updated
    ("WIDGET-002", "EA", 12.40m, null),    // not on contract     -> inserted (upsert)
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

// The payload is a Dictionary so IgnoreDisabled can be added at the TOP LEVEL only
// when it is needed — inside a Transaction object it is silently ignored.
Dictionary<string, object> LinePayload(
    string itemId, string uom, decimal price, decimal? commissionCost)
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
                        Edit("company_id", contract.CompanyId),
                        Edit("contract_no", contract.ContractNo),
                        Edit("job_no", contract.JobNo),
                        Edit("end_date", contract.EndDate),
                    },
                    RelativeDateEdits = Array.Empty<object>(),
                },
            },
        },
        new
        {
            Name = "JOBPRICELINE.jobpriceline",
            Type = "List",
            Keys = new[] { "item_id" },
            Rows = new object[]
            {
                new
                {
                    Edits = new[]
                    {
                        Edit("item_id", itemId),
                        Edit("uom", uom),
                        Edit("pricing_method", "Price"),          // before price!
                        Edit("price", price.ToString()),
                    },
                    RelativeDateEdits = Array.Empty<object>(),
                },
            },
        },
    };
    var payload = new Dictionary<string, object>
    {
        ["Name"] = "JobContractPricing",
        ["UseCodeValues"] = false,
        ["Transactions"] = new object[]
        {
            new { Status = "New", DataElements = elements },
        },
    };
    if (commissionCost is not null)
    {
        payload["IgnoreDisabled"] = true;  // top level, NOT inside the Transaction
        elements.Add(new
        {
            Name = "JOBPRICECOST.jobpricecost",
            Type = "Form",
            Keys = new[] { "item_id" },
            Rows = new object[]
            {
                new
                {
                    Edits = new[]
                    {
                        Edit("item_id", itemId),
                        Edit("commission_cost_type_cd", "Value"),   // type before value
                        Edit("commission_cost_value", commissionCost.Value.ToString()),
                    },
                },
            },
        });
    }
    return payload;
}

async Task<bool> PostLineAsync(Dictionary<string, object> payload)
{
    using var resp = await client.PostAsync(
        $"{uiServer}/api/v2/transaction",
        new StringContent(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json"));
    resp.EnsureSuccessStatusCode();  // HTTP 200 even when the transaction failed
    using var result = JsonDocument.Parse(await resp.Content.ReadAsStringAsync());
    var summary = result.RootElement.GetProperty("Summary");
    if (summary.GetProperty("Failed").GetInt32() > 0 ||
        summary.GetProperty("Succeeded").GetInt32() == 0)
    {
        if (result.RootElement.TryGetProperty("Messages", out var messages))
        {
            Console.WriteLine($"  FAILED: {messages}");
        }
        return false;
    }
    return true;
}

foreach (var l in lines)
{
    var ok = await PostLineAsync(LinePayload(l.ItemId, l.Uom, l.Price, l.Commission));
    Console.WriteLine($"{l.ItemId}: {(ok ? "OK" : "failed")}");
}

// --- Verify via OData (no joins: chain the uid columns) ---
// Renewals can return two headers for one contract_no — match job_no too.
var hdr = (await ODataAsync(client, "job_price_hdr",
    $"contract_no eq '{contract.ContractNo}' and job_no eq '{contract.JobNo}'"))[0];
foreach (var l in lines)
{
    var imUid = (await ODataAsync(client, "inv_mast", $"item_id eq '{l.ItemId}'"))[0]
        .GetProperty("inv_mast_uid");
    var line = (await ODataAsync(client, "job_price_line",
        $"job_price_hdr_uid eq {hdr.GetProperty("job_price_hdr_uid")} " +
        $"and inv_mast_uid eq {imUid}"))[0];
    var actual = line.GetProperty("price").GetDecimal();
    Console.WriteLine($"{l.ItemId}: price={actual} expected={l.Price} -> " +
                      $"{(actual == l.Price ? "OK" : "MISMATCH")}");
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

> **Payload files:** [JSON](../../examples/payloads/json/update-contract-lines.json) · [XML](../../examples/payloads/xml/update-contract-lines.xml) — validator-verified, see [payloads README](../../examples/payloads/README.md).
>
> **End-to-end files** (runnable from the repo with a `.env`, dry-run by default): [`examples/python/recipes/update_contract_lines.py`](../../examples/python/recipes/update_contract_lines.py) · [`examples/csharp/Recipes/UpdateContractLines.cs`](../../examples/csharp/Recipes/UpdateContractLines.cs). The snippet above is self-contained; the files use the repo's shared `common` / `P21Examples.Common` helpers like every other example.

## Gotchas

- **`pricing_method` must precede `price` in the Edits.** Changing `pricing_method` clears the typed price, exactly as in the UI — reversed order writes the line with **price = $0** and the transaction still reports `Succeeded`. Verified live. Order the Edits `item_id`, `pricing_method`, `price`.
- **One transaction per POST when inserting lines.** Every transaction re-saves the shared FORM header; batched inserts collide — all but one fail with an optimistic-concurrency error, and the ones that land can get **duplicate `line_no`** values. Edits to existing keyed rows batch fine.
- **`Status: "Existing"` (or `"Update"`, `"Change"`) is rejected** — [the enum has one member, `"New"`](../03-Transaction-API.md#status-new-is-the-only-value-the-enum-accepts). HTTP 400 on 26.1.5940.0, HTTP 500 `NullReferenceException` on older builds. Use `"New"` for both create and update.
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
