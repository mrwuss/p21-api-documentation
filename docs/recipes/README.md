# Recipes — Copy-and-Run Task Pages

One page per task, **self-contained**: the complete working payload, a full runnable script (Python and C#), the verified gotchas, and a verify step. Doing one task? Load one recipe — not the whole manual. For concept depth, each recipe links into the [manual](../INDEX.md); for the complete field list of any service, load its JSON from [`definitions/`](../../definitions/README.md).

> If you're an AI assistant: read this file, then **only** the recipe for your task. The recipe is the source of truth for that process; the manual sections it links to are the deep dive.

## Index

| Recipe | Task | API |
|--------|------|-----|
| [update-contract-lines](update-contract-lines.md) | Update or insert job-contract lines, prices, commission costs | Transaction |
| [update-order-lines](update-order-lines.md) | Modify an existing sales order: edit a line in place, add a line | Transaction (`Order`, `user_line_no` handles) |
| [edit-contract-bins](edit-contract-bins.md) | Change contract bin min/max/reorder/capacity | Transaction (`IgnoreDisabled`), Interactive fallback |
| [create-bins](create-bins.md) | Bulk-create warehouse bins | Transaction (`BinLocation`) |
| [create-sales-order](create-sales-order.md) | Create a sales order | Transaction (`Order`) |
| [order-with-assembly](order-with-assembly.md) | Order a line that explodes / spawns a production order | Interactive |
| [set-primary-bin-supplier](set-primary-bin-supplier.md) | Set an item's primary bin or primary supplier at a location | Transaction (`Item`), Interactive fallback |
| [generate-pick-ticket-pdf](generate-pick-ticket-pdf.md) | Generate/reprint pick tickets and POs as PDF | `pdfreport` (`m_*` services) |
| [production-order-runbook](production-order-runbook.md) | Full production cycle: create → print → confirm → complete → ship | Transaction + Interactive |
| [record-labor-time](record-labor-time.md) | Post labor hours to a production order | Transaction (`TimeEntry`) |
| [inventory-adjustment](inventory-adjustment.md) | Adjust on-hand quantity (write-offs) | Transaction (`InventoryAdjustment`) |
| [update-supplier-contact](update-supplier-contact.md) | Write a supplier's email / central phone (shared `address` record) | Transaction (`Address`) |
| [create-customer](create-customer.md) | Create a customer master record (salesrep + default_branch gotchas) | Transaction (`Customer`) |
| [create-requisition-po](create-requisition-po.md) | Create a requisition PO (`po_type` 'R'; vendor vs supplier) | Transaction (`RequisitionPurchaseOrder`) |
| [reassign-salesrep](reassign-salesrep.md) | Reassign a customer's and ship-tos' salesrep | Transaction |

## Shared conventions (recipes don't repeat these)

**Environment.** Examples use `https://play.p21server.com` with user `apiuser` and generic data (`ACME`, `WIDGET-001`, customer `100198`). Substitute your own. Always run against a **test/play environment first**.

**Auth preamble.** Every recipe's complete example is a **standalone program** — it carries its own copy of the preamble below, so you never have to come back to this page to make a recipe run. It is reproduced here once for reference (and because it is handy on its own: paste it, edit the constants, run it, and it prints the token and the UI server URL). Recipes that only talk to OData, the Entity API, the Inventory REST API or the UDT service drop `get_ui_server` / `GetUiServerAsync` — those endpoints live on `BASE_URL` directly.

<!-- tabs -->
```python
"""Authenticate against P21 and resolve the UI server URL."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
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

    print(f"Token acquired ({len(token)} chars); UI server: {ui_server}")
```

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
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

Console.WriteLine($"Token acquired ({token.Length} chars); UI server: {uiServer}");

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

**Validate payloads before posting.** Shape mistakes (a string where an array belongs, `IgnoreDisabled` at the wrong level, booleans in quotes) fail in confusing ways. Run [`scripts/validate_payload.py`](../../scripts/validate_payload.py) on your payload file (JSON or XML) — it checks structure and field names against [`definitions/`](../../definitions/README.md) offline. See [Payload Anatomy](../03-Transaction-API.md#payload-anatomy-types-nesting-and-common-mistakes).

**Check the result, not the HTTP status.** The Transaction API returns HTTP 200 even when everything failed. Every recipe checks `Summary.Succeeded` / `Summary.Failed` and prints `Messages` on failure; transactions in one POST pass/fail independently.

**Verify after writing.** A `Succeeded` response is not proof the value landed (field-order cascades and silent no-ops exist). Each recipe ends with a read-back — OData or `POST /api/v2/transaction/get`.

**Full field lists.** Recipes show the fields that matter for the task. For *every* field a service accepts (names, types, keys, labels, payload template), load `definitions/{Service}.json` — see the [definitions README](../../definitions/README.md).

**Page programs vs repo files.** The tabs on each page are **complete programs**: paste one into a file, edit the constants in its `EDIT THESE` block, run it. No repo clone, no `.env`, no shared import. Python needs only `httpx`; C# targets `net9.0` (`dotnet new console`, paste, `dotnet run`) with `System.Text.Json` and no NuGet packages. Each recipe also links **repo files** under [`examples/python/recipes/`](../../examples/python/recipes/README.md) (Python) and [`examples/csharp/Recipes/`](../../examples/csharp/Recipes/) (C#): those use the repo's shared config/auth helpers, run against your `.env`, and are **dry-run by default** (print the payload; `--execute` / typing `EXECUTE` posts).

> **Credit:** the cookbook pattern and much of the verified content come from [Alex Westemeier](https://github.com/AWestemeier)'s process playbook.
