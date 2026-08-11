# Reassign a Customer and Ship-To Salesrep

Reassign a customer's and its default ship-to's salesrep through the Transaction API.

**API:** Transaction · **Service:** `Customer`, `ShipTo` · **Deep dive:** [Transaction API](../03-Transaction-API.md) · **Full schema:** [`Customer.json`](../../definitions/Customer.json), [`ShipTo.json`](../../definitions/ShipTo.json)

Verified on P21 26.1 (build 26.1.5894.1), production + play, 2026-07-28, while driving a ~150-customer sales-rep territory realignment (148 customers, 216 ship-to rows) entirely through the Transaction API so the changes land in P21's audit log.

## Prerequisites

- The customer and ship-to already exist, and the old and new salesreps exist.
- Token + UI server URL. The complete examples below authenticate without a shared helper.

## Where the salesrep lives

Customer salesrep data must be written in two places together: the `salesrep_id` header field on `customer` (`TABPAGE_1.tp_1_dw_1`, Form), and the `CUSTOMERSALESREP.customersalesrep` grid (List, key `salesrep_id`, `BusinessObjectName` `customer_salesrep`). In that grid, `primary_salesrep_flag` marks the primary rep. `primary_salesrep_flag` is unused/empty at the item level elsewhere in P21, but it is the operative flag here.

Ship-to salesrep data lives only in the `TABPAGE_SALESREP.tabpage_salesrep` grid (List, key `salesrep_id`, `BusinessObjectName` `ship_to_salesrep`); there is no salesrep field on `ship_to` itself. Its columns are `salesrep_id`, `primary_salesrep`, `commission_percentage`, `delete_flag`, and `primary_service_rep`.

> **HTTP 200 is not success.** Check `Summary.Succeeded` / `Summary.Failed` and `Results.Transactions[0].Status == "Passed"`. HTTP 200 alone does not mean the write landed.

Both `primary_salesrep_flag` and `primary_salesrep` / `delete_flag` are Char fields with valid values `"ON"` and `"OFF"`. The Form DataElement's own `Keys` array stays empty; identifying key values go into that row's `Edits`. The List/grid DataElement's `Keys` array names the grid key column: `["salesrep_id"]`.

## Payload

### Customer

```json
{
    "Name": "Customer",
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
                        {"Name": "company_id",  "Value": "ACME"},
                        {"Name": "customer_id", "Value": "100198"},
                        {"Name": "salesrep_id", "Value": "200"}
                    ],
                    "RelativeDateEdits": []
                }]
            },
            {
                "Name": "CUSTOMERSALESREP.customersalesrep",
                "Type": "List",
                "Keys": ["salesrep_id"],
                "Rows": [
                    {
                        "Edits": [
                            {"Name": "salesrep_id",          "Value": "100"},
                            {"Name": "primary_salesrep_flag", "Value": "OFF"},
                            {"Name": "commission_percentage", "Value": "0"}
                        ],
                        "RelativeDateEdits": []
                    },
                    {
                        "Edits": [
                            {"Name": "salesrep_id",          "Value": "200"},
                            {"Name": "primary_salesrep_flag", "Value": "ON"},
                            {"Name": "commission_percentage", "Value": "100"}
                        ],
                        "RelativeDateEdits": []
                    }
                ]
            }
        ]
    }]
}
```

### ShipTo

```json
{
    "Name": "ShipTo",
    "UseCodeValues": false,
    "Transactions": [{
        "Status": "New",
        "DataElements": [
            {
                "Name": "TABPAGE_1.shiptomain",
                "Type": "Form",
                "Keys": [],
                "Rows": [{
                    "Edits": [
                        {"Name": "company_id", "Value": "ACME"},
                        {"Name": "address_id", "Value": "100198"}
                    ],
                    "RelativeDateEdits": []
                }]
            },
            {
                "Name": "TABPAGE_SALESREP.tabpage_salesrep",
                "Type": "List",
                "Keys": ["salesrep_id"],
                "Rows": [
                    {
                        "Edits": [
                            {"Name": "salesrep_id",     "Value": "200"},
                            {"Name": "primary_salesrep", "Value": "ON"}
                        ],
                        "RelativeDateEdits": []
                    },
                    {
                        "Edits": [
                            {"Name": "salesrep_id", "Value": "100"},
                            {"Name": "delete_flag", "Value": "ON"}
                        ],
                        "RelativeDateEdits": []
                    }
                ]
            }
        ]
    }]
}
```

For full field lists, load [`definitions/Customer.json`](../../definitions/Customer.json) and [`definitions/ShipTo.json`](../../definitions/ShipTo.json).

## Complete example

<!-- tabs -->
```python
"""Reassign a customer's and default ship-to's salesrep, then read them back."""
import re
import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "api_user"
PASSWORD = "api_pass"
VERIFY_SSL = False                        # True once you trust the cert chain
COMPANY_ID = "ACME"
CUSTOMER_ID = "100198"
SHIP_TO_ID = "100198"
OLD_SALESREP_ID = "100"
NEW_SALESREP_ID = "200"
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
    except (ValueError, KeyError):
        match = re.search(r"<AccessToken>([^<]+)</AccessToken>", r.text)
        if not match:
            raise ValueError(f"No AccessToken in response: {r.text[:200]}") from None
        return match.group(1)


def get_ui_server(client: httpx.Client, token: str) -> str:
    """Transaction and Interactive calls go to the UI server, not BASE_URL."""
    r = client.get(
        f"{BASE_URL}/api/ui/router/v1/?urlType=external",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        },
    )
    r.raise_for_status()
    try:
        return r.json()["Url"].rstrip("/")
    except (ValueError, KeyError):
        match = re.search(r"<Url>([^<]+)</Url>", r.text)
        if not match:
            raise ValueError(f"No Url in response: {r.text[:200]}") from None
        return match.group(1).rstrip("/")


def post_transaction(client, ui_server, headers, payload):
    r = client.post(
        f"{ui_server}/api/v2/transaction",
        headers=headers,
        json=payload,
    )
    r.raise_for_status()
    result = r.json()
    summary = result["Summary"]
    status = result["Results"]["Transactions"][0]["Status"]
    if summary["Failed"] or not summary["Succeeded"] or status != "Passed":
        print(result.get("Messages", []))
        raise RuntimeError(f"Transaction failed: {summary}; status={status}")


def odata(client, headers, table, filter_expr):
    r = client.get(
        f"{BASE_URL}/odataservice/odata/table/{table}",
        params={"$filter": filter_expr},
        headers=headers,
    )
    r.raise_for_status()
    return r.json()["value"]


with httpx.Client(verify=VERIFY_SSL, timeout=120, follow_redirects=True) as client:
    token = get_token(client)
    ui_server = get_ui_server(client, token)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    customer = {
        "Name": "Customer",
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
                            {"Name": "company_id", "Value": COMPANY_ID},
                            {"Name": "customer_id", "Value": CUSTOMER_ID},
                            {"Name": "salesrep_id", "Value": NEW_SALESREP_ID},
                        ],
                        "RelativeDateEdits": [],
                    }],
                },
                {
                    "Name": "CUSTOMERSALESREP.customersalesrep",
                    "Type": "List",
                    "Keys": ["salesrep_id"],
                    "Rows": [
                        {
                            "Edits": [
                                {"Name": "salesrep_id", "Value": OLD_SALESREP_ID},
                                {"Name": "primary_salesrep_flag", "Value": "OFF"},
                                {"Name": "commission_percentage", "Value": "0"},
                            ],
                            "RelativeDateEdits": [],
                        },
                        {
                            "Edits": [
                                {"Name": "salesrep_id", "Value": NEW_SALESREP_ID},
                                {"Name": "primary_salesrep_flag", "Value": "ON"},
                                {"Name": "commission_percentage", "Value": "100"},
                            ],
                            "RelativeDateEdits": [],
                        },
                    ],
                },
            ],
        }],
    }
    shipto = {
        "Name": "ShipTo",
        "UseCodeValues": False,
        "Transactions": [{
            "Status": "New",
            "DataElements": [
                {
                    "Name": "TABPAGE_1.shiptomain",
                    "Type": "Form",
                    "Keys": [],
                    "Rows": [{
                        "Edits": [
                            {"Name": "company_id", "Value": COMPANY_ID},
                            {"Name": "address_id", "Value": SHIP_TO_ID},
                        ],
                        "RelativeDateEdits": [],
                    }],
                },
                {
                    "Name": "TABPAGE_SALESREP.tabpage_salesrep",
                    "Type": "List",
                    "Keys": ["salesrep_id"],
                    "Rows": [
                        {
                            "Edits": [
                                {"Name": "salesrep_id", "Value": NEW_SALESREP_ID},
                                {"Name": "primary_salesrep", "Value": "ON"},
                            ],
                            "RelativeDateEdits": [],
                        },
                        {
                            "Edits": [
                                {"Name": "salesrep_id", "Value": OLD_SALESREP_ID},
                                {"Name": "delete_flag", "Value": "ON"},
                            ],
                            "RelativeDateEdits": [],
                        },
                    ],
                },
            ],
        }],
    }
    post_transaction(client, ui_server, headers, customer)
    post_transaction(client, ui_server, headers, shipto)
    for row in odata(client, headers, "customer_salesrep", f"customer_id eq '{CUSTOMER_ID}'"):
        print({
            "salesrep_id": row.get("salesrep_id"),
            "primary_salesrep_flag": row.get("primary_salesrep_flag"),
        })
    for row in odata(client, headers, "ship_to_salesrep", f"ship_to_id eq '{SHIP_TO_ID}'"):
        print({
            "salesrep_id": row.get("salesrep_id"),
            "primary_salesrep": row.get("primary_salesrep"),
        })
```

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "api_user";
const string Password = "api_pass";
const string CompanyId = "ACME";
const string CustomerId = "100198";
const string ShipToId = "100198";
const string OldSalesrepId = "100";
const string NewSalesrepId = "200";
// ---------------------------------------------------------------------------

var handler = new HttpClientHandler
{
    ServerCertificateCustomValidationCallback =
        HttpClientHandler.DangerousAcceptAnyServerCertificateValidator,
};
using var client = new HttpClient(handler) { Timeout = TimeSpan.FromMinutes(2) };
client.DefaultRequestHeaders.Accept.Add(
    new MediaTypeWithQualityHeaderValue("application/json"));
var token = await GetTokenAsync(client);
var uiServer = await GetUiServerAsync(client, token);
client.DefaultRequestHeaders.Authorization =
    new AuthenticationHeaderValue("Bearer", token);

var customer = new
{
    Name = "Customer",
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
                                new { Name = "company_id", Value = CompanyId },
                                new { Name = "customer_id", Value = CustomerId },
                                new { Name = "salesrep_id", Value = NewSalesrepId },
                            },
                            RelativeDateEdits = Array.Empty<object>(),
                        },
                    },
                },
                new
                {
                    Name = "CUSTOMERSALESREP.customersalesrep",
                    Type = "List",
                    Keys = new[] { "salesrep_id" },
                    Rows = new[]
                    {
                        new
                        {
                            Edits = new[]
                            {
                                new { Name = "salesrep_id", Value = OldSalesrepId },
                                new { Name = "primary_salesrep_flag", Value = "OFF" },
                                new { Name = "commission_percentage", Value = "0" },
                            },
                            RelativeDateEdits = Array.Empty<object>(),
                        },
                        new
                        {
                            Edits = new[]
                            {
                                new { Name = "salesrep_id", Value = NewSalesrepId },
                                new { Name = "primary_salesrep_flag", Value = "ON" },
                                new { Name = "commission_percentage", Value = "100" },
                            },
                            RelativeDateEdits = Array.Empty<object>(),
                        },
                    },
                },
            },
        },
    },
};

var shipto = new
{
    Name = "ShipTo",
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
                    Name = "TABPAGE_1.shiptomain",
                    Type = "Form",
                    Keys = Array.Empty<string>(),
                    Rows = new[]
                    {
                        new
                        {
                            Edits = new[]
                            {
                                new { Name = "company_id", Value = CompanyId },
                                new { Name = "address_id", Value = ShipToId },
                            },
                            RelativeDateEdits = Array.Empty<object>(),
                        },
                    },
                },
                new
                {
                    Name = "TABPAGE_SALESREP.tabpage_salesrep",
                    Type = "List",
                    Keys = new[] { "salesrep_id" },
                    Rows = new[]
                    {
                        new
                        {
                            Edits = new[]
                            {
                                new { Name = "salesrep_id", Value = NewSalesrepId },
                                new { Name = "primary_salesrep", Value = "ON" },
                            },
                            RelativeDateEdits = Array.Empty<object>(),
                        },
                        new
                        {
                            Edits = new[]
                            {
                                new { Name = "salesrep_id", Value = OldSalesrepId },
                                new { Name = "delete_flag", Value = "ON" },
                            },
                            RelativeDateEdits = Array.Empty<object>(),
                        },
                    },
                },
            },
        },
    },
};

await PostTransactionAsync(client, uiServer, customer);
await PostTransactionAsync(client, uiServer, shipto);

foreach (var row in await ODataAsync(
    client, "customer_salesrep", $"customer_id eq '{CustomerId}'"))
{
    Console.WriteLine(
        $"customer: salesrep_id={row.GetProperty("salesrep_id")} " +
        $"primary_salesrep_flag={row.GetProperty("primary_salesrep_flag")}");
}

foreach (var row in await ODataAsync(
    client, "ship_to_salesrep", $"ship_to_id eq '{ShipToId}'"))
{
    Console.WriteLine(
        $"ship-to: salesrep_id={row.GetProperty("salesrep_id")} " +
        $"primary_salesrep={row.GetProperty("primary_salesrep")}");
}

static async Task PostTransactionAsync(HttpClient c, string ui, object p)
{
    using var r = await c.PostAsync(
        $"{ui}/api/v2/transaction",
        new StringContent(JsonSerializer.Serialize(p), Encoding.UTF8, "application/json"));
    r.EnsureSuccessStatusCode();
    using var d = JsonDocument.Parse(await r.Content.ReadAsStringAsync());
    var s = d.RootElement.GetProperty("Summary");
    var st = d.RootElement.GetProperty("Results")
        .GetProperty("Transactions")[0]
        .GetProperty("Status")
        .GetString();
    if (s.GetProperty("Failed").GetInt32() > 0 ||
        s.GetProperty("Succeeded").GetInt32() == 0 ||
        st != "Passed")
    {
        Console.Error.WriteLine(d.RootElement.GetProperty("Messages"));
        throw new InvalidOperationException($"Transaction failed; status={st}");
    }
}

static async Task<List<JsonElement>> ODataAsync(
    HttpClient c, string table, string filter)
{
    using var r = await c.GetAsync(
        $"{BaseUrl}/odataservice/odata/table/{table}?$filter=" +
        Uri.EscapeDataString(filter));
    r.EnsureSuccessStatusCode();
    using var d = JsonDocument.Parse(await r.Content.ReadAsStringAsync());
    return d.RootElement.GetProperty("value")
        .EnumerateArray()
        .Select(x => x.Clone())
        .ToList();
}

// v2 token endpoint — credentials go in the body, never in headers.
static async Task<string> GetTokenAsync(HttpClient c)
{
    var p = JsonSerializer.Serialize(new { username = Username, password = Password });
    using var r = await c.PostAsync(
        $"{BaseUrl}/api/security/token/v2",
        new StringContent(p, Encoding.UTF8, "application/json"));
    r.EnsureSuccessStatusCode();
    return ReadField(await r.Content.ReadAsStringAsync(), "AccessToken");
}

// Transaction and Interactive calls go to the UI server, not BaseUrl.
static async Task<string> GetUiServerAsync(HttpClient c, string token)
{
    using var q = new HttpRequestMessage(
        HttpMethod.Get, $"{BaseUrl}/api/ui/router/v1/?urlType=external");
    q.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
    using var r = await c.SendAsync(q);
    r.EnsureSuccessStatusCode();
    return ReadField(await r.Content.ReadAsStringAsync(), "Url").TrimEnd('/');
}

// Some middleware answers these two endpoints in XML even when asked for JSON.
static string ReadField(string p, string f)
{
    try
    {
        var v = JsonDocument.Parse(p).RootElement.GetProperty(f).GetString();
        if (!string.IsNullOrEmpty(v))
        {
            return v;
        }
    }
    catch (Exception ex) when (
        ex is JsonException or KeyNotFoundException)
    {
    }

    var m = System.Text.RegularExpressions.Regex.Match(
        p, $"<{f}>([^<]+)</{f}>");
    if (!m.Success)
    {
        throw new InvalidOperationException(
            $"No {f} in response: {p[..Math.Min(200, p.Length)]}");
    }
    return m.Groups[1].Value;
}
```
<!-- /tabs -->

## Gotchas (verified live on P21 26.1.5894.1, 2026-07-28)

- **`Keys` must be an array of key-column-name strings, not objects.** Passing `[{"Name": "...", "Value": "..."}]` inside a DataElement's `Keys` array returns HTTP 400: `Unexpected character encountered while parsing value: { ... Path 'Transactions[0].DataElements[0].Keys'`. This is a general Transaction API parsing rule; key values belong in row `Edits`.
- **The two grids are not symmetric — this is the trap.** `CUSTOMERSALESREP.customersalesrep` has no `delete_flag`; sending one returns `General Exception: Invalid column name: delete_flag`. Demote the old customer row (`primary_salesrep_flag: "OFF"`, `commission_percentage: "0"`) and promote the new row (`primary_salesrep_flag: "ON"`, `commission_percentage: "100"`); both rows stay. ShipTo has `delete_flag`: add the new row (`primary_salesrep: "ON"`) and mark the old row `delete_flag: "ON"`. Do not assume the same remove/replace pattern works on both grids because their columns differ.
- **`customer_id` is disabled for a DEFAULT ship-to.** When `address_id` equals `customer_id`, including `customer_id` in `TABPAGE_1.shiptomain` Edits returns `Column is disabled: customer_id`; only that one ship-to's transaction fails while others in the batch succeed. Omit it; `company_id` + `address_id` in Edits is sufficient. This was confirmed for DEFAULT ship-tos only; non-default ship-tos were not tested.
- **HTTP 200 is not success.** Check `Summary.Succeeded` / `Summary.Failed` and `Results.Transactions[0].Status == "Passed"`; HTTP 200 alone does not mean the write landed.
- **Observed ShipTo read-path quirk.** `POST {ui_server}/api/v2/transaction/get` against ShipTo returned an empty-body HTTP 500 in the test environment. The UPDATE (`POST .../transaction`) worked regardless. This was observed only for ShipTo, not Customer, so the read-back uses OData.
- **You write `ON`/`OFF` but you read back `Y`/`N`.** The service definition's `ValidValues` for these flags are `ON`/`OFF`, and that is what a `UseCodeValues: false` payload sends. The underlying column stores `Y`/`N`, which is what OData returns. Do not "fix" a read-back that shows `Y` — that is the success case. Both spellings are in fact accepted on write (verified 2026-08-11: `ON` and `Y` both returned `Passed`; `OFF` and `N` both reached the same business-rule validation), so a payload built from either convention will land. Prefer `ON`/`OFF` to match the definition.
- **You cannot demote the only primary.** Sending `primary_salesrep_flag: "OFF"` (or `"N"`) for a customer's sole salesrep row fails the whole transaction with `Primary salesrep is required.` — the value parsed fine; the window refuses to leave the customer with no primary. Demote and promote must therefore travel together: put both grid rows in the same transaction, or promote the incoming rep before demoting the outgoing one. A demote-only call is never valid.

## Verify

```text
GET {base_url}/odataservice/odata/table/customer_salesrep?$filter=customer_id eq '100198'
GET {base_url}/odataservice/odata/table/ship_to_salesrep?$filter=ship_to_id eq '100198'
```

Confirm the returned rows show `salesrep_id` `200` as the primary. The flags read back as **`Y`**, not the `ON` you wrote — the definition exposes `ON`/`OFF` while the column stores `Y`/`N`. A row showing `primary_salesrep_flag` `Y` for the customer and `primary_salesrep` `Y` for the ship-to is the success case.
