# Update Supplier Contact Info (Email / Central Phone)

Write a supplier's email address and central phone number into P21 — the fields purchasing documents and views read from the supplier's **address** record.

**API:** Transaction (`POST /api/v2/transaction`) · **Service:** `Address` · **Deep dive:** [Transaction API](../03-Transaction-API.md) · **Full schema:** [Address.json](../../definitions/Address.json)

## Where supplier contact info actually lives

`supplier.supplier_id` shares its id with an `address` row (`address.id = supplier_id`). The email and central phone shown for a supplier come from **`address.email_address`** and **`address.central_phone_number`** — not from the `supplier` table (its only email-ish columns are `email_po_flag` / `supplier_redemption_email`). Verified against a live 2026 system: the supplier's address row carried exactly the values surfaced by purchasing views.

The `Address` service (window: Address maintenance) is the smallest write surface for these fields — its definition is ~9 KB vs ~70 KB for `Supplier`, and it needs only the address `id` as key.

## Payload

`Status: "New"` is the **upsert** shape — an existing `id` updates that record (see [Status "Existing" is not valid](../03-Transaction-API.md#updating-an-existing-contract)). `IgnoreIfEmpty: true` on the contact edits means an empty value **leaves the stored field untouched** — this payload can add or replace contact info but can never blank it.

```json
POST {ui_server}/api/v2/transaction

{
  "Name": "Address",
  "UseCodeValues": false,
  "IgnoreDisabled": true,
  "Transactions": [{
    "Status": "New",
    "DataElements": [
      {
        "Name": "TABPAGE_1.tp_1_dw_1",
        "Type": "Form",
        "Keys": ["id"],
        "Rows": [{ "Edits": [
          { "Name": "id", "Value": "10050", "IgnoreIfEmpty": false }
        ] }]
      },
      {
        "Name": "TABPAGE_3.tp_3_dw_3",
        "Type": "Form",
        "Keys": [],
        "Rows": [{ "Edits": [
          { "Name": "email_address",                "Value": "orders@example.com", "IgnoreIfEmpty": true },
          { "Name": "address_central_phone_number", "Value": "319-555-0100",       "IgnoreIfEmpty": true }
        ] }]
      }
    ]
  }]
}
```

Field names on the Phone tab (`TABPAGE_3.tp_3_dw_3`): `address_central_phone_number`, `address_central_fax_number`, `email_address`.

## Verify (read-after-write)

Don't trust `Summary.Succeeded` alone — read the record back ([why](../04-Interactive-API.md#verifying-writes-dont-trust-save-status-alone)):

```json
POST {ui_server}/api/v2/transaction/get

{
  "ServiceName": "Address",
  "TransactionStates": [
    { "DataElementName": "TABPAGE_1.tp_1_dw_1", "Keys": [{ "Name": "id", "Value": "10050" }] },
    { "DataElementName": "TABPAGE_3.tp_3_dw_3", "Keys": [{ "Name": "id", "Value": "10050" }] }
  ]
}
```

The response's `TABPAGE_3.tp_3_dw_3` row echoes `email_address` / `address_central_phone_number` as stored.

## Gotchas (verified live on Play, 2026-07)

- **The wrong `/transaction/get` shape returns a BLANK template with HTTP 200** — a body using top-level `Keys` (no `TransactionStates`) "succeeds" but every `Value` comes back empty, which reads exactly like a missing record. Use the `TransactionStates`/`DataElementName` shape above.
- **Write + read-back round trip confirmed**: values persisted and were read back verbatim; a subsequent write restored the originals the same way.
- **Empty values are no-ops**, not clears, because of `IgnoreIfEmpty: true` — deliberate here; flip to `false` only if you truly mean to blank a field.

## Complete example

Upserts the supplier's email and central phone on the shared `address` record, then reads both fields back with the `TransactionStates` shape from the Verify section — the wrong `/transaction/get` shape returns a blank template with HTTP 200, so the read-back has to use this one.

<!-- tabs -->
```python
"""Write a supplier's email / central phone, then read the address record back."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
SUPPLIER_ID = "10050"                     # address.id == supplier.supplier_id
EMAIL = "orders@example.com"              # "" leaves the stored value untouched
PHONE = "319-555-0100"                    # "" leaves the stored value untouched
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
        "Name": "Address", "UseCodeValues": False, "IgnoreDisabled": True,
        "Transactions": [{
            "Status": "New",   # the upsert shape — an existing id updates that record
            "DataElements": [
                {"Name": "TABPAGE_1.tp_1_dw_1", "Type": "Form", "Keys": ["id"],
                 "Rows": [{"Edits": [
                     {"Name": "id", "Value": SUPPLIER_ID, "IgnoreIfEmpty": False}]}]},
                {"Name": "TABPAGE_3.tp_3_dw_3", "Type": "Form", "Keys": [],
                 "Rows": [{"Edits": [
                     # IgnoreIfEmpty: an empty value is a NO-OP, never a clear
                     {"Name": "email_address", "Value": EMAIL, "IgnoreIfEmpty": True},
                     {"Name": "address_central_phone_number", "Value": PHONE,
                      "IgnoreIfEmpty": True}]}]},
            ],
        }],
    }

    resp = client.post(f"{ui_server}/api/v2/transaction",
                       headers=headers, json=payload)
    resp.raise_for_status()   # HTTP 200 even on failure -- check the Summary
    summary = resp.json().get("Summary") or {}
    print(f"Succeeded: {summary.get('Succeeded')}, Failed: {summary.get('Failed')}")
    if summary.get("Failed"):
        raise SystemExit(f"Address write failed: {resp.text[:300]}")

    # --- Read back (TransactionStates shape; the top-level Keys shape returns
    #     a blank template with HTTP 200 and reads like a missing record) ---
    get_payload = {
        "ServiceName": "Address",
        "TransactionStates": [
            {"DataElementName": "TABPAGE_1.tp_1_dw_1",
             "Keys": [{"Name": "id", "Value": SUPPLIER_ID}]},
            {"DataElementName": "TABPAGE_3.tp_3_dw_3",
             "Keys": [{"Name": "id", "Value": SUPPLIER_ID}]},
        ],
    }
    resp = client.post(f"{ui_server}/api/v2/transaction/get",
                       headers=headers, json=get_payload)
    resp.raise_for_status()
    for txn in resp.json().get("Transactions", []):
        for de in txn.get("DataElements", []):
            for row in de.get("Rows", []):
                for edit in row.get("Edits", []):
                    if edit["Name"] in ("id", "email_address",
                                        "address_central_phone_number"):
                        print(f"  {edit['Name']}: {edit['Value']}")
```

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string SupplierId = "10050";           // address.id == supplier.supplier_id
const string Email = "orders@example.com";   // "" leaves the stored value untouched
const string Phone = "319-555-0100";         // "" leaves the stored value untouched
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
    Name = "Address",
    UseCodeValues = false,
    IgnoreDisabled = true,
    Transactions = new[]
    {
        new
        {
            Status = "New",   // the upsert shape — an existing id updates that record
            DataElements = new object[]
            {
                new
                {
                    Name = "TABPAGE_1.tp_1_dw_1",
                    Type = "Form",
                    Keys = new[] { "id" },
                    Rows = new object[]
                    {
                        new
                        {
                            Edits = new[]
                            {
                                new { Name = "id", Value = SupplierId, IgnoreIfEmpty = false },
                            },
                        },
                    },
                },
                new
                {
                    Name = "TABPAGE_3.tp_3_dw_3",
                    Type = "Form",
                    Keys = Array.Empty<string>(),
                    Rows = new object[]
                    {
                        new
                        {
                            // IgnoreIfEmpty: an empty value is a NO-OP, never a clear
                            Edits = new[]
                            {
                                new { Name = "email_address", Value = Email,
                                      IgnoreIfEmpty = true },
                                new { Name = "address_central_phone_number", Value = Phone,
                                      IgnoreIfEmpty = true },
                            },
                        },
                    },
                },
            },
        },
    },
};

using var resp = await client.PostAsync(
    $"{uiServer}/api/v2/transaction",
    new StringContent(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json"));
resp.EnsureSuccessStatusCode();   // HTTP 200 even on failure -- check the Summary
var body = await resp.Content.ReadAsStringAsync();
using var result = JsonDocument.Parse(body);
var summary = result.RootElement.GetProperty("Summary");
var failed = summary.GetProperty("Failed").GetInt32();
Console.WriteLine($"Succeeded: {summary.GetProperty("Succeeded")}, Failed: {failed}");
if (failed > 0)
{
    throw new InvalidOperationException(
        $"Address write failed: {body[..Math.Min(300, body.Length)]}");
}

// --- Read back (TransactionStates shape; the top-level Keys shape returns
//     a blank template with HTTP 200 and reads like a missing record) ---
var getPayload = new
{
    ServiceName = "Address",
    TransactionStates = new[]
    {
        new
        {
            DataElementName = "TABPAGE_1.tp_1_dw_1",
            Keys = new[] { new { Name = "id", Value = SupplierId } },
        },
        new
        {
            DataElementName = "TABPAGE_3.tp_3_dw_3",
            Keys = new[] { new { Name = "id", Value = SupplierId } },
        },
    },
};
using var getResp = await client.PostAsync(
    $"{uiServer}/api/v2/transaction/get",
    new StringContent(JsonSerializer.Serialize(getPayload), Encoding.UTF8, "application/json"));
getResp.EnsureSuccessStatusCode();
using var getResult = JsonDocument.Parse(await getResp.Content.ReadAsStringAsync());

var wanted = new[] { "id", "email_address", "address_central_phone_number" };
foreach (var txn in getResult.RootElement.GetProperty("Transactions").EnumerateArray())
{
    foreach (var de in txn.GetProperty("DataElements").EnumerateArray())
    {
        foreach (var row in de.GetProperty("Rows").EnumerateArray())
        {
            foreach (var edit in row.GetProperty("Edits").EnumerateArray())
            {
                var name = edit.GetProperty("Name").GetString();
                if (wanted.Contains(name))
                {
                    Console.WriteLine($"  {name}: {edit.GetProperty("Value")}");
                }
            }
        }
    }
}

// --- helpers ---------------------------------------------------------------

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
