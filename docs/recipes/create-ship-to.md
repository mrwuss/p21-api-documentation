# Create a Ship-To

Add a new ship-to to an existing customer in one stateless Transaction API call. The ship-to's `address_id` is auto-assigned and returned in the response.

**API:** Transaction · **Service:** `ShipTo` · **Deep dive:** [03 § ShipTo Service — Creating a Ship-To](../03-Transaction-API.md#shipto-service-creating-a-ship-to) · **Full schema:** [ShipTo.json](../../definitions/ShipTo.json)

## Prerequisites

- P21 credentials — the complete example below authenticates itself; nothing to install but `httpx` (Python) or a bare `net8.0`-or-later console project (C#).
- The customer exists, and you know the **stored codes** for its terms, tax group and invoice type (this recipe sends codes, not labels — see Gotchas).
- The branch (`default_branch`), the preferred location and the salesrep exist.

## Which element holds each field

A merged field dump of the service is misleading: send each field on the element that owns it. Two fields you would expect on the main form are not there — `salesrep_id` and `ship_to_name` both fail with `Invalid column name` on `TABPAGE_1.shiptomain`.

| Element | Type | Fields |
|---|---|---|
| `TABPAGE_1.shiptomain` | Form | `company_id`, `customer_id`, `address_name`, `default_branch`, `terms_id`, `invoice_type` (required); `tax_group_id`; `phys_address1`, `phys_address2`, `phys_city`, `phys_state`, `phys_postal_code`, `phys_country` |
| `TABPAGE_2.tp_2_dw_2` | Form | `mail_address1`, `mail_address2`, `mail_city`, `mail_state`, `mail_postal_code`, `mail_country` |
| `TABPAGE_5.tp_5_dw_5` | Form | `central_phone_number` |
| `TABPAGE_OEOPTIONS.tabpage_oeoptions` | Form | `preferred_location_id` (required); `packing_basis`, `pick_ticket_type` |
| `TABPAGE_SALESREP.tabpage_salesrep` | List, key `salesrep_id` | `salesrep_id`, `primary_salesrep`, `commission_percentage`, `delete_flag` |

Leave `address_id` out: it is the new ship-to's ID, assigned by P21.

## The ship-to inherits the customer's primary rep

A new ship-to starts with the **customer's primary salesrep** on its salesrep grid. To give it a different rep, do both of these in the same call, in this row order:

1. Add the new rep with `primary_salesrep` = `Y` and `commission_percentage` = `100`.
2. Retire the inherited rep with `delete_flag` = `Y`.

Send only the new rep and the save fails: *"The total commission percentage for all outside salesreps must equal 100 percent."* When the customer's primary rep is the rep you want, leave the salesrep grid out of the payload entirely.

## Payload

```json
POST {ui_server}/api/v2/transaction

{
    "Name": "ShipTo",
    "UseCodeValues": true,
    "Transactions": [{
        "Status": "New",
        "DataElements": [
            {
                "Name": "TABPAGE_1.shiptomain",
                "Type": "Form",
                "Keys": [],
                "Rows": [{
                    "Edits": [
                        {"Name": "company_id",       "Value": "ACME"},
                        {"Name": "customer_id",      "Value": "1001"},
                        {"Name": "address_name",     "Value": "ACME Industrial - East Plant"},
                        {"Name": "default_branch",   "Value": "10"},
                        {"Name": "terms_id",         "Value": "1"},
                        {"Name": "invoice_type",     "Value": "IN"},
                        {"Name": "tax_group_id",     "Value": "TAX-01"},
                        {"Name": "phys_address1",    "Value": "456 Industrial Pkwy"},
                        {"Name": "phys_city",        "Value": "Des Moines"},
                        {"Name": "phys_state",       "Value": "IA"},
                        {"Name": "phys_postal_code", "Value": "50309"},
                        {"Name": "phys_country",     "Value": "USA"}
                    ],
                    "RelativeDateEdits": []
                }]
            },
            {
                "Name": "TABPAGE_2.tp_2_dw_2",
                "Type": "Form",
                "Keys": [],
                "Rows": [{
                    "Edits": [
                        {"Name": "mail_address1",    "Value": "456 Industrial Pkwy"},
                        {"Name": "mail_city",        "Value": "Des Moines"},
                        {"Name": "mail_state",       "Value": "IA"},
                        {"Name": "mail_postal_code", "Value": "50309"},
                        {"Name": "mail_country",     "Value": "USA"}
                    ],
                    "RelativeDateEdits": []
                }]
            },
            {
                "Name": "TABPAGE_5.tp_5_dw_5",
                "Type": "Form",
                "Keys": [],
                "Rows": [{
                    "Edits": [
                        {"Name": "central_phone_number", "Value": "515-555-0100"}
                    ],
                    "RelativeDateEdits": []
                }]
            },
            {
                "Name": "TABPAGE_OEOPTIONS.tabpage_oeoptions",
                "Type": "Form",
                "Keys": [],
                "Rows": [{
                    "Edits": [
                        {"Name": "preferred_location_id", "Value": "10"}
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
                            {"Name": "salesrep_id",           "Value": "200"},
                            {"Name": "primary_salesrep",      "Value": "Y"},
                            {"Name": "commission_percentage", "Value": "100"}
                        ],
                        "RelativeDateEdits": []
                    },
                    {
                        "Edits": [
                            {"Name": "salesrep_id", "Value": "100"},
                            {"Name": "delete_flag", "Value": "Y"}
                        ],
                        "RelativeDateEdits": []
                    }
                ]
            }
        ]
    }]
}
```

Here `200` is the rep you want and `100` is the customer's primary rep that the ship-to would otherwise inherit. For every other field the service accepts, load [`definitions/ShipTo.json`](../../definitions/ShipTo.json).

## Complete example

The example reads the customer's primary rep over OData, so it adds the retire row only when that rep differs from the one you want.

<!-- tabs -->
```python
"""Create a ship-to on an existing customer, then read it back over OData."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
COMPANY_ID = "ACME"
CUSTOMER_ID = "1001"                      # existing customer
ADDRESS_NAME = "ACME Industrial - East Plant"
DEFAULT_BRANCH = "10"
PREFERRED_LOCATION_ID = "10"
TERMS_ID = "1"                            # the STORED terms_id code, not its description
INVOICE_TYPE = "IN"                       # stored code ("Invoice" is the label)
TAX_GROUP_ID = "TAX-01"                   # stored tax group code
SALESREP_ID = "200"                       # the rep this ship-to should carry
ADDRESS1 = "456 Industrial Pkwy"
CITY = "Des Moines"
STATE = "IA"
POSTAL_CODE = "50309"
COUNTRY = "USA"
PHONE = "515-555-0100"
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


def form(name: str, edits: dict[str, str]) -> dict:
    """One Form DataElement with its Edits."""
    return {
        "Name": name,
        "Type": "Form",
        "Keys": [],
        "Rows": [{
            "Edits": [{"Name": k, "Value": v} for k, v in edits.items()],
            "RelativeDateEdits": [],
        }],
    }


with httpx.Client(verify=VERIFY_SSL, timeout=120, follow_redirects=True) as client:
    token = get_token(client)
    ui_server = get_ui_server(client, token)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",       # without this you get XML, not JSON
        "Content-Type": "application/json",
    }

    # 1. Find the rep the new ship-to will inherit: the customer's live primary rep.
    #    customer_id is numeric on OData -- no quotes.
    reps = client.get(
        f"{BASE_URL}/odataservice/odata/table/customer_salesrep",
        params={"$filter": f"customer_id eq {CUSTOMER_ID} and row_status_flag eq 704"},
        headers=headers,
    )
    reps.raise_for_status()
    inherited = [r["salesrep_id"] for r in reps.json()["value"]
                 if r.get("primary_salesrep_flag") == "Y"]
    print(f"Customer's primary rep (inherited by the ship-to): {inherited}")

    # 2. Salesrep rows: add the wanted rep first, then retire each inherited one.
    rep_rows = []
    if inherited != [SALESREP_ID]:
        rep_rows.append({"Edits": [
            {"Name": "salesrep_id", "Value": SALESREP_ID},
            {"Name": "primary_salesrep", "Value": "Y"},
            {"Name": "commission_percentage", "Value": "100"},
        ], "RelativeDateEdits": []})
        for rep in inherited:
            if rep != SALESREP_ID:
                rep_rows.append({"Edits": [
                    {"Name": "salesrep_id", "Value": rep},
                    {"Name": "delete_flag", "Value": "Y"},
                ], "RelativeDateEdits": []})

    elements = [
        form("TABPAGE_1.shiptomain", {
            "company_id": COMPANY_ID,
            "customer_id": CUSTOMER_ID,
            "address_name": ADDRESS_NAME,
            "default_branch": DEFAULT_BRANCH,
            "terms_id": TERMS_ID,
            "invoice_type": INVOICE_TYPE,
            "tax_group_id": TAX_GROUP_ID,
            "phys_address1": ADDRESS1,
            "phys_city": CITY,
            "phys_state": STATE,
            "phys_postal_code": POSTAL_CODE,
            "phys_country": COUNTRY,
        }),
        form("TABPAGE_2.tp_2_dw_2", {
            "mail_address1": ADDRESS1,
            "mail_city": CITY,
            "mail_state": STATE,
            "mail_postal_code": POSTAL_CODE,
            "mail_country": COUNTRY,
        }),
        form("TABPAGE_5.tp_5_dw_5", {"central_phone_number": PHONE}),
        form("TABPAGE_OEOPTIONS.tabpage_oeoptions",
             {"preferred_location_id": PREFERRED_LOCATION_ID}),
    ]
    if rep_rows:
        elements.append({
            "Name": "TABPAGE_SALESREP.tabpage_salesrep",
            "Type": "List",
            "Keys": ["salesrep_id"],
            "Rows": rep_rows,
        })

    payload = {
        "Name": "ShipTo",
        "UseCodeValues": True,   # send stored codes: terms_id, invoice_type, Y/N flags
        "Transactions": [{"Status": "New", "DataElements": elements}],
    }

    # 3. Create
    response = client.post(f"{ui_server}/api/v2/transaction", headers=headers, json=payload)
    response.raise_for_status()
    result = response.json()

    # HTTP 200 even on failure -- check the Summary, never the status code
    summary = result["Summary"]
    print(f"Succeeded: {summary['Succeeded']}, Failed: {summary['Failed']}")
    if summary["Failed"] > 0 or summary["Succeeded"] == 0:
        for msg in result.get("Messages", []):
            print(msg)
        raise SystemExit("Ship-to create failed")

    # The generated address_id comes back in the result rows
    ship_to_id = None
    for txn in result["Results"]["Transactions"]:
        if txn.get("Status") != "Passed":
            continue
        for element in txn.get("DataElements", []):
            for row in element.get("Rows", []):
                for edit in row.get("Edits", []):
                    if edit.get("Name") == "address_id" and edit.get("Value"):
                        ship_to_id = edit["Value"]
    print(f"Created ship-to (address_id): {ship_to_id}")

    # 4. Read back via OData -- Succeeded is not proof every value landed
    for table in ("ship_to", "ship_to_salesrep"):
        resp = client.get(
            f"{BASE_URL}/odataservice/odata/table/{table}",
            params={"$filter": f"ship_to_id eq {ship_to_id}"},
            headers=headers,
        )
        resp.raise_for_status()
        for row in resp.json()["value"]:
            if table == "ship_to":
                print({k: row.get(k) for k in
                       ("ship_to_id", "customer_id", "default_branch", "terms_id")})
            else:
                print({k: row.get(k) for k in
                       ("salesrep_id", "primary_salesrep", "commission_percentage",
                        "delete_flag")})
```

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string CompanyId = "ACME";
const string CustomerId = "1001";                       // existing customer
const string AddressName = "ACME Industrial - East Plant";
const string DefaultBranch = "10";
const string PreferredLocationId = "10";
const string TermsId = "1";                             // the STORED terms_id code, not its description
const string InvoiceType = "IN";                        // stored code ("Invoice" is the label)
const string TaxGroupId = "TAX-01";                     // stored tax group code
const string SalesrepId = "200";                        // the rep this ship-to should carry
const string Address1 = "456 Industrial Pkwy";
const string City = "Des Moines";
const string State = "IA";
const string PostalCode = "50309";
const string Country = "USA";
const string Phone = "515-555-0100";
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

// 1. Find the rep the new ship-to will inherit: the customer's live primary rep.
//    customer_id is numeric on OData -- no quotes.
var inherited = (await ODataAsync(client, "customer_salesrep",
        $"customer_id eq {CustomerId} and row_status_flag eq 704"))
    .Where(r => r.TryGetProperty("primary_salesrep_flag", out var f) && f.GetString() == "Y")
    .Select(r => r.GetProperty("salesrep_id").GetString()!)
    .ToList();
Console.WriteLine($"Customer's primary rep (inherited by the ship-to): {string.Join(", ", inherited)}");

// 2. Salesrep rows: add the wanted rep first, then retire each inherited one.
var repRows = new JsonArray();
if (!(inherited.Count == 1 && inherited[0] == SalesrepId))
{
    repRows.Add(Row(("salesrep_id", SalesrepId), ("primary_salesrep", "Y"),
                    ("commission_percentage", "100")));
    foreach (var rep in inherited.Where(r => r != SalesrepId))
        repRows.Add(Row(("salesrep_id", rep), ("delete_flag", "Y")));
}

var elements = new JsonArray
{
    Form("TABPAGE_1.shiptomain",
        ("company_id", CompanyId), ("customer_id", CustomerId), ("address_name", AddressName),
        ("default_branch", DefaultBranch), ("terms_id", TermsId), ("invoice_type", InvoiceType),
        ("tax_group_id", TaxGroupId), ("phys_address1", Address1), ("phys_city", City),
        ("phys_state", State), ("phys_postal_code", PostalCode), ("phys_country", Country)),
    Form("TABPAGE_2.tp_2_dw_2",
        ("mail_address1", Address1), ("mail_city", City), ("mail_state", State),
        ("mail_postal_code", PostalCode), ("mail_country", Country)),
    Form("TABPAGE_5.tp_5_dw_5", ("central_phone_number", Phone)),
    Form("TABPAGE_OEOPTIONS.tabpage_oeoptions", ("preferred_location_id", PreferredLocationId)),
};
if (repRows.Count > 0)
{
    elements.Add(new JsonObject
    {
        ["Name"] = "TABPAGE_SALESREP.tabpage_salesrep",
        ["Type"] = "List",
        ["Keys"] = new JsonArray("salesrep_id"),
        ["Rows"] = repRows,
    });
}

var payload = new JsonObject
{
    ["Name"] = "ShipTo",
    ["UseCodeValues"] = true,   // send stored codes: terms_id, invoice_type, Y/N flags
    ["Transactions"] = new JsonArray
    {
        new JsonObject { ["Status"] = "New", ["DataElements"] = elements },
    },
};

// 3. Create
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
    {
        Console.Error.WriteLine(messages);
    }
    throw new InvalidOperationException("Ship-to create failed");
}

// The generated address_id comes back in the result rows
var shipToId = ResultValue(result.RootElement, "address_id");
Console.WriteLine($"Created ship-to (address_id): {shipToId}");

// 4. Read back via OData -- Succeeded is not proof every value landed
foreach (var row in await ODataAsync(client, "ship_to", $"ship_to_id eq {shipToId}"))
{
    Console.WriteLine(
        $"ship_to_id={Field(row, "ship_to_id")} customer_id={Field(row, "customer_id")} " +
        $"default_branch={Field(row, "default_branch")} terms_id={Field(row, "terms_id")}");
}
foreach (var row in await ODataAsync(client, "ship_to_salesrep", $"ship_to_id eq {shipToId}"))
{
    Console.WriteLine(
        $"salesrep_id={Field(row, "salesrep_id")} primary_salesrep={Field(row, "primary_salesrep")} " +
        $"commission_percentage={Field(row, "commission_percentage")} " +
        $"delete_flag={Field(row, "delete_flag")}");
}

// --- helpers ---------------------------------------------------------------

static JsonObject Row(params (string Name, string Value)[] edits)
{
    var list = new JsonArray();
    foreach (var (name, value) in edits)
        list.Add(new JsonObject { ["Name"] = name, ["Value"] = value });
    return new JsonObject { ["Edits"] = list, ["RelativeDateEdits"] = new JsonArray() };
}

static JsonObject Form(string name, params (string Name, string Value)[] edits) => new()
{
    ["Name"] = name,
    ["Type"] = "Form",
    ["Keys"] = new JsonArray(),
    ["Rows"] = new JsonArray { Row(edits) },
};

static string Field(JsonElement row, string name) =>
    row.TryGetProperty(name, out var v) ? v.ToString() : "";

// Pull one echoed field out of any passed transaction's result rows.
static string? ResultValue(JsonElement root, string fieldName)
{
    string? found = null;
    foreach (var txn in root.GetProperty("Results").GetProperty("Transactions").EnumerateArray())
    {
        if (txn.GetProperty("Status").GetString() != "Passed") continue;
        foreach (var element in txn.GetProperty("DataElements").EnumerateArray())
        {
            foreach (var row in element.GetProperty("Rows").EnumerateArray())
            {
                foreach (var edit in row.GetProperty("Edits").EnumerateArray())
                {
                    if (edit.GetProperty("Name").GetString() == fieldName)
                    {
                        var value = edit.GetProperty("Value").GetString();
                        if (!string.IsNullOrEmpty(value)) found = value;
                    }
                }
            }
        }
    }
    return found;
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

The element placement, the code conventions and the add-then-retire rep rows are what was verified. The complete examples build the same payload; they were not run separately.

## Gotchas (verified live on play 26.1, September 2026)

- **Send `UseCodeValues: true` with stored codes.** Under `false`, `terms_id` demands the terms *description* rather than the code. With `true`, send the codes the database stores: `terms_id` as its code, `invoice_type` as `IN`, `tax_group_id` as the group's ID.
- **Flags are `Y`/`N` under `UseCodeValues: true`.** The definition and the defaults template show `ON`/`OFF` — that is the `false`-mode form. Sending `primary_salesrep: "ON"` with `UseCodeValues: true` fails with `Invalid primary_salesrep value: ON`.
- **The inherited rep must be retired in the same call** when you want a different rep, or the commission total fails — see [The ship-to inherits the customer's primary rep](#the-ship-to-inherits-the-customers-primary-rep). The retire is soft: the inherited rep's row stays in `ship_to_salesrep` with `delete_flag = 'Y'`.
- **`salesrep_id` and `ship_to_name` are not on `TABPAGE_1.shiptomain`.** Both fail with `Invalid column name`. The rep goes on `TABPAGE_SALESREP.tabpage_salesrep`; the ship-to's name is `address_name`.
- **Read back with OData.** `POST /api/v2/transaction/get` against `ShipTo` has returned an empty-body HTTP 500 ([reassign-salesrep](reassign-salesrep.md)). The OData keys `customer_id` and `ship_to_id` are numeric — don't quote them.
- **HTTP 200 ≠ success.** Check `Summary.Succeeded` and `Results.Transactions[].Status == "Passed"`.

## Verify

```http
GET {base_url}/odataservice/odata/table/ship_to?$filter=ship_to_id eq {address_id}
GET {base_url}/odataservice/odata/table/ship_to_salesrep?$filter=ship_to_id eq {address_id}
```

Confirm the ship-to belongs to the right customer and branch, and that exactly one live rep (`delete_flag` not `Y`) is `primary_salesrep` = `Y` at `100` percent.

> **Credit:** *@mrwuss* — created on play 26.1, September 2026 ([#182](https://github.com/mrwuss/p21-api-documentation/issues/182)).
