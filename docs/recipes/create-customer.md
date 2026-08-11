# Create a Customer

Create a customer master record in one stateless Transaction API call. `customer_id` is auto-assigned and returned in the response.

**API:** Transaction · **Service:** `Customer` · **Deep dive:** [Transaction API](../03-Transaction-API.md) · **Full schema:** [Customer.json](../../definitions/Customer.json)

## Prerequisites

- P21 credentials — the complete example below authenticates itself; nothing to install but `httpx` (Python) or a bare `net9.0` console project (C#).
- The salesrep exists (`salesrep_id`) and the branch exists (`default_branch`).

## What the defaults template already fills

The `Customer` defaults template (`GET {ui_server}/api/v2/defaults/Customer`) prefills `company_id`, `terms_id` ("To Be Determined"), and `customer_type_cd`. So a minimal create only has to supply:

- **`TABPAGE_1.tp_1_dw_1`** (Form): `customer_name`, `salesrep_id`, and the mailing-address fields.
- **`SHIP_TO_GENERAL.ship_to_general`** (Form): `default_branch`.

`customer_id` is auto-assigned — leave it out; the generated value comes back in the result rows (key: `company_id` + `customer_id`).

## Payload

```json
POST {ui_server}/api/v2/transaction

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
                        {"Name": "customer_name",    "Value": "ACME Industrial Supply"},
                        {"Name": "salesrep_id",      "Value": "100"},
                        {"Name": "mail_address1",    "Value": "123 Main St"},
                        {"Name": "mail_city",        "Value": "Des Moines"},
                        {"Name": "mail_state",       "Value": "IA"},
                        {"Name": "mail_postal_code", "Value": "50309"},
                        {"Name": "mail_country",     "Value": "USA"}
                    ],
                    "RelativeDateEdits": []
                }]
            },
            {
                "Name": "SHIP_TO_GENERAL.ship_to_general",
                "Type": "Form",
                "Keys": [],
                "Rows": [{
                    "Edits": [
                        {"Name": "default_branch", "Value": "10"}
                    ],
                    "RelativeDateEdits": []
                }]
            }
        ]
    }]
}
```

For every other field the service accepts, load [`definitions/Customer.json`](../../definitions/Customer.json).

## Complete example

<!-- tabs -->
```python
"""Create a customer master record, then read it back over OData."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
CUSTOMER_NAME = "ACME Industrial Supply"
SALESREP_ID = "100"                       # hard-required (see Gotchas)
DEFAULT_BRANCH = "10"                     # required, NOT defaulted
MAIL_ADDRESS1 = "123 Main St"
MAIL_CITY = "Des Moines"
MAIL_STATE = "IA"
MAIL_POSTAL_CODE = "50309"
MAIL_COUNTRY = "USA"
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
                            {"Name": "customer_name",    "Value": CUSTOMER_NAME},
                            {"Name": "salesrep_id",      "Value": SALESREP_ID},
                            {"Name": "mail_address1",    "Value": MAIL_ADDRESS1},
                            {"Name": "mail_city",        "Value": MAIL_CITY},
                            {"Name": "mail_state",       "Value": MAIL_STATE},
                            {"Name": "mail_postal_code", "Value": MAIL_POSTAL_CODE},
                            {"Name": "mail_country",     "Value": MAIL_COUNTRY},
                        ],
                        "RelativeDateEdits": [],
                    }],
                },
                {
                    "Name": "SHIP_TO_GENERAL.ship_to_general",
                    "Type": "Form",
                    "Keys": [],
                    "Rows": [{
                        "Edits": [
                            {"Name": "default_branch", "Value": DEFAULT_BRANCH},
                        ],
                        "RelativeDateEdits": [],
                    }],
                },
            ],
        }],
    }

    response = client.post(f"{ui_server}/api/v2/transaction",
                           headers=headers, json=payload)
    response.raise_for_status()
    result = response.json()

    # HTTP 200 even on failure -- check the Summary, never the status code
    summary = result["Summary"]
    print(f"Succeeded: {summary['Succeeded']}, Failed: {summary['Failed']}")
    if summary["Failed"] > 0 or summary["Succeeded"] == 0:
        for msg in result.get("Messages", []):
            print(msg)
        raise SystemExit("Customer create failed")

    # The generated customer_id comes back in the TABPAGE_1.tp_1_dw_1 result rows
    customer_id = None
    for txn in result["Results"]["Transactions"]:
        if txn.get("Status") != "Passed":
            continue
        for element in txn.get("DataElements", []):
            if element.get("Name") != "TABPAGE_1.tp_1_dw_1":
                continue
            for row in element.get("Rows", []):
                for edit in row.get("Edits", []):
                    if edit.get("Name") == "customer_id":
                        customer_id = edit.get("Value")

    print(f"Created customer_id: {customer_id}")

    # Read back via OData -- Succeeded is not proof every value landed
    cust = client.get(
        f"{BASE_URL}/odataservice/odata/table/customer",
        params={"$filter": f"customer_id eq {customer_id}"},
        headers=headers,
    )
    cust.raise_for_status()
    for row in cust.json()["value"]:
        print({
            "customer_id": row.get("customer_id"),
            "customer_name": row.get("customer_name"),
            "salesrep_id": row.get("salesrep_id"),
            "mail_city": row.get("mail_city"),
        })
```

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string CustomerName = "ACME Industrial Supply";
const string SalesrepId = "100";        // hard-required (see Gotchas)
const string DefaultBranch = "10";      // required, NOT defaulted
const string MailAddress1 = "123 Main St";
const string MailCity = "Des Moines";
const string MailState = "IA";
const string MailPostalCode = "50309";
const string MailCountry = "USA";
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
                                new { Name = "customer_name", Value = CustomerName },
                                new { Name = "salesrep_id", Value = SalesrepId },
                                new { Name = "mail_address1", Value = MailAddress1 },
                                new { Name = "mail_city", Value = MailCity },
                                new { Name = "mail_state", Value = MailState },
                                new { Name = "mail_postal_code", Value = MailPostalCode },
                                new { Name = "mail_country", Value = MailCountry },
                            },
                            RelativeDateEdits = Array.Empty<object>(),
                        },
                    },
                },
                new
                {
                    Name = "SHIP_TO_GENERAL.ship_to_general",
                    Type = "Form",
                    Keys = Array.Empty<string>(),
                    Rows = new[]
                    {
                        new
                        {
                            Edits = new[]
                            {
                                new { Name = "default_branch", Value = DefaultBranch },
                            },
                            RelativeDateEdits = Array.Empty<object>(),
                        },
                    },
                },
            },
        },
    },
};

using var response = await client.PostAsync(
    $"{uiServer}/api/v2/transaction",
    new StringContent(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json"));
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
    {
        Console.Error.WriteLine(messages);
    }
    throw new InvalidOperationException("Customer create failed");
}

// The generated customer_id comes back in the TABPAGE_1.tp_1_dw_1 result rows
var customerId = ResultValue(result.RootElement, "TABPAGE_1.tp_1_dw_1", "customer_id");
Console.WriteLine($"Created customer_id: {customerId}");

// Read back via OData -- Succeeded is not proof every value landed
foreach (var row in await ODataAsync(client, "customer", $"customer_id eq {customerId}"))
{
    Console.WriteLine(
        $"customer_id={row.GetProperty("customer_id")} " +
        $"customer_name={row.GetProperty("customer_name")} " +
        $"salesrep_id={row.GetProperty("salesrep_id")} " +
        $"mail_city={row.GetProperty("mail_city")}");
}

// --- helpers ---------------------------------------------------------------

// Pull one echoed field out of a passed transaction's result rows.
static string? ResultValue(JsonElement root, string elementName, string fieldName)
{
    foreach (var txn in root.GetProperty("Results").GetProperty("Transactions").EnumerateArray())
    {
        if (txn.GetProperty("Status").GetString() != "Passed") continue;
        foreach (var element in txn.GetProperty("DataElements").EnumerateArray())
        {
            if (element.GetProperty("Name").GetString() != elementName) continue;
            foreach (var row in element.GetProperty("Rows").EnumerateArray())
            {
                foreach (var edit in row.GetProperty("Edits").EnumerateArray())
                {
                    if (edit.GetProperty("Name").GetString() == fieldName)
                    {
                        return edit.GetProperty("Value").GetString();
                    }
                }
            }
        }
    }
    return null;
}

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

> **End-to-end files** (runnable from the repo with a `.env`, dry-run by default): [`examples/python/recipes/create_customer.py`](../../examples/python/recipes/create_customer.py) · [`examples/csharp/Recipes/CreateCustomer.cs`](../../examples/csharp/Recipes/CreateCustomer.cs).

## Gotchas (verified live on Play 26.1.5894.1, 2026-07)

- **`salesrep_id` is hard-required, and the error surfaces on the ship-to, not the field.** Omitting it fails the whole transaction with *"Salesrep ID is required for a new ship to."* — even though the field lives on `TABPAGE_1.tp_1_dw_1`. Don't chase the ship-to when you see that message; supply `salesrep_id` on the Form.
- **`default_branch` is required and NOT defaulted.** The defaults template fills `packing_basis`/`freight_cd`/`fob` but leaves `default_branch` empty. Omitting it fails with *"'Default Branch' is a required column."*
- **No zip → salesrep cascade.** Setting `mail_postal_code` (or `phys_postal_code` on TABPAGE_5) does **not** default `salesrep_id`, even with matching rows seeded in `salesrep_postalcode` / `postal_code_group_hdr`. Those tables are [dead storage on an undeployed install](../02-OData-API.md#undeployed-unlicensed-windows-readable-tables-no-api-surface). The rep must be supplied explicitly and passes through verbatim.
- **HTTP 200 ≠ success.** Check `Summary.Succeeded` and `Results.Transactions[].Status == "Passed"`; the generated `customer_id` comes back in the result rows.

## Verify

```http
GET {base_url}/odataservice/odata/table/customer?$filter=customer_id eq 123456
```

Confirm `customer_name`, `salesrep_id`, and the mailing-address fields you sent.
