# Create a Product Group

Create a product group (Product Group Maintenance) in one stateless Transaction API call, after an OData check that the ID is free. The check is not optional: a `New` transaction for an ID that already exists **overwrites that group** and reports success.

**API:** Transaction · **Service:** `ProductGroup` · **Full schema:** [ProductGroup.json](../../definitions/ProductGroup.json)

*Verified on a play tenant, 26.1.6004.0, November 2026, with an OData read-back after every POST.*

## Prerequisites

- P21 credentials. The complete example below authenticates itself; nothing to install but `httpx` (Python) or a bare `net8.0`-or-later console project (C#).
- The three GL accounts the group posts to: asset (inventory), revenue and cost of sales. They must exist for the company. The usual choice is the set an existing sibling group uses; read it from the `product_group` table.

## The window is one form

`ProductGroup` has one element, `FORM.form` (Form), keyed `company_id` + `product_group_id`.

| Field | Required | Notes |
|---|---|---|
| `company_id` | Yes | |
| `product_group_id` | Yes | The new group's ID |
| `product_group_desc` | Yes | |
| `asset_account_no` | Yes | Must exist for the company |
| `revenue_account_no` | Yes | Must exist for the company |
| `cos_account_no` | Yes | Must exist for the company |
| `delete_flag` | No | `ON` / `OFF`; `ON` soft-deletes (stored `Y`) |
| `include_in_size_analysis_flag` | — | **Disabled.** Leave it out (see Gotchas) |

The definition also lists `parker_product_code`, `ta_rental_revenue_account_no`, `cardlock_product_group_type_cd`, `compressor_flag`, `override_flag`, and pick and expedite times; the `*_desc` and `company_name` fields are display-only. Every other `product_group` column, such as `price_rounding_flag` and the profit-check flags, is not on the window and takes its default.

## Payload

```json
POST {ui_server}/api/v2/transaction

{
    "Name": "ProductGroup",
    "UseCodeValues": false,
    "Transactions": [{
        "Status": "New",
        "DataElements": [{
            "Name": "FORM.form",
            "Type": "Form",
            "Keys": [],
            "Rows": [{
                "Edits": [
                    {"Name": "company_id",         "Value": "ACME"},
                    {"Name": "product_group_id",   "Value": "PGSENS"},
                    {"Name": "product_group_desc", "Value": "Sensors"},
                    {"Name": "asset_account_no",   "Value": "ACCT-1000"},
                    {"Name": "revenue_account_no", "Value": "ACCT-4000"},
                    {"Name": "cos_account_no",     "Value": "ACCT-5000"},
                    {"Name": "delete_flag",        "Value": "OFF"}
                ],
                "RelativeDateEdits": []
            }]
        }]
    }]
}
```

To create several groups, send one entry in `Transactions` per group. Each succeeds or fails on its own, and `Summary` counts them.

> **Payload file** (validator-verified): [JSON](../../examples/payloads/json/create-product-group.json).

## Gotchas

- **`Status: "New"` on an existing ID updates it.** A second `New` for the same `product_group_id` returned `Succeeded: 1` and replaced the description on the same `product_group_uid`; no error, no second row. Query `product_group` for the ID first (any `delete_flag`), and stop if it is there.
- **`include_in_size_analysis_flag` is disabled**, on a new group and on an existing one: `Column is disabled: include_in_size_analysis_flag`. The transaction that carries it fails and writes nothing. A new group is stored with `N`.
- **An account that does not exist fails the group**: `This account doesn't exist for company ACME. DataElement: form, Column: asset_account_no, Value: ...`. Nothing is written.
- **Soft delete only.** `delete_flag` `ON` on an existing group stores `Y`; the row stays.
- **Edit with the same shape.** A `New` transaction with the two keys and the fields to change updates an existing group (that is the overwrite above, used on purpose). Fields you leave out keep their values.
- **Read back over OData.** `Succeeded` is not proof every value landed; compare the `product_group` row with what you sent.

## Complete example

The example refuses an ID that already exists, creates the group, checks `Summary`, and reads the row back.

<!-- tabs -->
```python
"""Create a product group after checking the ID is free, then read it back over OData."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.example.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
COMPANY_ID = "ACME"
PRODUCT_GROUP_ID = "PGSENS"               # the new group's ID
DESCRIPTION = "Sensors"
ASSET_ACCOUNT = "ACCT-1000"               # inventory (asset) account
REVENUE_ACCOUNT = "ACCT-4000"
COS_ACCOUNT = "ACCT-5000"
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


def read_group(client: httpx.Client, headers: dict) -> list[dict]:
    """Every product_group row with this ID, deleted or not."""
    r = client.get(
        f"{BASE_URL}/odataservice/odata/table/product_group",
        params={"$filter": f"company_id eq '{COMPANY_ID}' and product_group_id eq '{PRODUCT_GROUP_ID}'"},
        headers=headers,
    )
    r.raise_for_status()
    return r.json()["value"]


with httpx.Client(verify=VERIFY_SSL, timeout=120, follow_redirects=True) as client:
    token = get_token(client)
    ui_server = get_ui_server(client, token)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",       # without this you get XML, not JSON
        "Content-Type": "application/json",
    }

    # 1. A New transaction on an existing ID overwrites that group -- refuse instead.
    existing = read_group(client, headers)
    if existing:
        raise SystemExit(
            f"{PRODUCT_GROUP_ID} already exists (delete_flag {existing[0]['delete_flag']}); nothing sent"
        )

    # 2. Create. include_in_size_analysis_flag is disabled -- leave it out.
    edits = {
        "company_id": COMPANY_ID,
        "product_group_id": PRODUCT_GROUP_ID,
        "product_group_desc": DESCRIPTION,
        "asset_account_no": ASSET_ACCOUNT,
        "revenue_account_no": REVENUE_ACCOUNT,
        "cos_account_no": COS_ACCOUNT,
        "delete_flag": "OFF",
    }
    payload = {
        "Name": "ProductGroup",
        "UseCodeValues": False,
        "Transactions": [{
            "Status": "New",
            "DataElements": [{
                "Name": "FORM.form",
                "Type": "Form",
                "Keys": [],
                "Rows": [{
                    "Edits": [{"Name": k, "Value": v} for k, v in edits.items()],
                    "RelativeDateEdits": [],
                }],
            }],
        }],
    }
    response = client.post(f"{ui_server}/api/v2/transaction", headers=headers, json=payload)
    response.raise_for_status()
    result = response.json()

    # HTTP 200 even on failure -- check the Summary, never the status code
    summary = result["Summary"]
    print(f"Succeeded: {summary['Succeeded']}, Failed: {summary['Failed']}")
    if summary["Failed"] > 0 or summary["Succeeded"] == 0:
        for msg in result.get("Messages", []):
            print(msg)
        raise SystemExit("Product group create failed")

    # 3. Read back -- Succeeded is not proof every value landed
    rows = read_group(client, headers)
    row = rows[0]
    print({k: row.get(k) for k in (
        "product_group_id", "product_group_desc", "asset_account_no", "revenue_account_no",
        "cos_account_no", "include_in_size_analysis_flag", "delete_flag", "product_group_uid")})
    expected = {k: v for k, v in edits.items() if k != "delete_flag"}
    wrong = {k: (row.get(k), v) for k, v in expected.items() if row.get(k) != v}
    if len(rows) != 1 or wrong or row.get("delete_flag") != "N":
        raise SystemExit(f"Read-back does not match: {wrong}")
    print("Read-back matches")
```

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.example.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string CompanyId = "ACME";
const string ProductGroupId = "PGSENS";                 // the new group's ID
const string Description = "Sensors";
const string AssetAccount = "ACCT-1000";                // inventory (asset) account
const string RevenueAccount = "ACCT-4000";
const string CosAccount = "ACCT-5000";
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

var filter = $"company_id eq '{CompanyId}' and product_group_id eq '{ProductGroupId}'";

// 1. A New transaction on an existing ID overwrites that group -- refuse instead.
var existing = await ODataAsync(client, "product_group", filter);
if (existing.Count > 0)
{
    throw new InvalidOperationException(
        $"{ProductGroupId} already exists (delete_flag {Field(existing[0], "delete_flag")}); nothing sent");
}

// 2. Create. include_in_size_analysis_flag is disabled -- leave it out.
var edits = new (string Name, string Value)[]
{
    ("company_id", CompanyId),
    ("product_group_id", ProductGroupId),
    ("product_group_desc", Description),
    ("asset_account_no", AssetAccount),
    ("revenue_account_no", RevenueAccount),
    ("cos_account_no", CosAccount),
    ("delete_flag", "OFF"),
};
var editArray = new JsonArray();
foreach (var (name, value) in edits)
    editArray.Add(new JsonObject { ["Name"] = name, ["Value"] = value });

var payload = new JsonObject
{
    ["Name"] = "ProductGroup",
    ["UseCodeValues"] = false,
    ["Transactions"] = new JsonArray
    {
        new JsonObject
        {
            ["Status"] = "New",
            ["DataElements"] = new JsonArray
            {
                new JsonObject
                {
                    ["Name"] = "FORM.form",
                    ["Type"] = "Form",
                    ["Keys"] = new JsonArray(),
                    ["Rows"] = new JsonArray
                    {
                        new JsonObject { ["Edits"] = editArray, ["RelativeDateEdits"] = new JsonArray() },
                    },
                },
            },
        },
    },
};

using var response = await client.PostAsync(
    $"{uiServer}/api/v2/transaction",
    new StringContent(payload.ToJsonString(), Encoding.UTF8, "application/json"));
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
        Console.Error.WriteLine(messages);
    throw new InvalidOperationException("Product group create failed");
}

// 3. Read back -- Succeeded is not proof every value landed
var rows = await ODataAsync(client, "product_group", filter);
var row = rows[0];
foreach (var key in new[] { "product_group_id", "product_group_desc", "asset_account_no",
             "revenue_account_no", "cos_account_no", "include_in_size_analysis_flag",
             "delete_flag", "product_group_uid" })
    Console.WriteLine($"{key}={Field(row, key)}");
var wrong = edits.Where(e => e.Name != "delete_flag" && Field(row, e.Name) != e.Value)
    .Select(e => e.Name).ToList();
if (rows.Count != 1 || wrong.Count > 0 || Field(row, "delete_flag") != "N")
    throw new InvalidOperationException($"Read-back does not match: {string.Join(", ", wrong)}");
Console.WriteLine("Read-back matches");

// --- helpers ---------------------------------------------------------------

static string Field(JsonElement row, string name) =>
    row.TryGetProperty(name, out var v) ? v.ToString() : "";

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
        throw new InvalidOperationException($"No {field} in response: {payload[..Math.Min(200, payload.Length)]}");
    return match.Groups[1].Value;
}
```

## Verify

```
GET {BASE_URL}/odataservice/odata/table/product_group?$filter=company_id eq 'ACME' and product_group_id eq 'PGSENS'
```

One row, the three accounts you sent, `delete_flag` `N`, `include_in_size_analysis_flag` `N`.
