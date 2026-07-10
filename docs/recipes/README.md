# Recipes — Copy-and-Run Task Pages

One page per task, **self-contained**: the complete working payload, a full runnable script (Python and C#), the verified gotchas, and a verify step. Doing one task? Load one recipe — not the whole manual. For concept depth, each recipe links into the [manual](../INDEX.md); for the complete field list of any service, load its JSON from [`definitions/`](../../definitions/README.md).

> If you're an AI assistant: read this file, then **only** the recipe for your task. The recipe is the source of truth for that process; the manual sections it links to are the deep dive.

## Index

| Recipe | Task | API |
|--------|------|-----|
| [update-contract-lines](update-contract-lines.md) | Update or insert job-contract lines, prices, commission costs | Transaction |
| [edit-contract-bins](edit-contract-bins.md) | Change contract bin min/max/reorder/capacity | Transaction (`IgnoreDisabled`), Interactive fallback |
| [create-bins](create-bins.md) | Bulk-create warehouse bins | Transaction (`BinLocation`) |
| [create-sales-order](create-sales-order.md) | Create a sales order | Transaction (`Order`) |
| [order-with-assembly](order-with-assembly.md) | Order a line that explodes / spawns a production order | Interactive |
| [set-primary-bin-supplier](set-primary-bin-supplier.md) | Set an item's primary bin or primary supplier at a location | Transaction (`Item`), Interactive fallback |
| [generate-pick-ticket-pdf](generate-pick-ticket-pdf.md) | Generate/reprint pick tickets and POs as PDF | `pdfreport` (`m_*` services) |
| [production-order-runbook](production-order-runbook.md) | Full production cycle: create → print → confirm → complete → ship | Transaction + Interactive |
| [record-labor-time](record-labor-time.md) | Post labor hours to a production order | Transaction (`TimeEntry`) |
| [inventory-adjustment](inventory-adjustment.md) | Adjust on-hand quantity (write-offs) | Transaction (`InventoryAdjustment`) |

## Shared conventions (recipes don't repeat these)

**Environment.** Examples use `https://play.p21server.com` with user `api_user` and generic data (`ACME`, `WIDGET-001`, customer `100198`). Substitute your own. Always run against a **test/play environment first**.

**Auth preamble.** Every script below starts with this (shown once here; recipes reference `p21_auth()` / `P21Session.CreateAsync()`):

<!-- tabs -->
```python
import httpx

def p21_auth(base_url: str, username: str, password: str) -> tuple[str, str, dict]:
    """Authenticate and resolve the UI server. Returns (token, ui_server, headers)."""
    auth = httpx.post(
        f"{base_url}/api/security/token/v2",
        json={"username": username, "password": password},
        headers={"Accept": "application/json"},
        verify=False,
    )
    auth.raise_for_status()
    token = auth.json()["AccessToken"]

    router = httpx.get(
        f"{base_url}/api/ui/router/v1/?urlType=external",  # trailing slash avoids a 307
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        verify=False, follow_redirects=True,
    )
    router.raise_for_status()
    ui_server = router.json()["Url"].rstrip("/")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    return token, ui_server, headers
```

```csharp
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using Newtonsoft.Json.Linq;

public sealed class P21Session
{
    public required HttpClient Http { get; init; }
    public required string UiServer { get; init; }

    public static async Task<P21Session> CreateAsync(
        string baseUrl, string username, string password)
    {
        var http = new HttpClient();
        http.DefaultRequestHeaders.Add("Accept", "application/json");

        var authBody = new JObject { ["username"] = username, ["password"] = password };
        var authResp = await http.PostAsync(
            $"{baseUrl}/api/security/token/v2",
            new StringContent(authBody.ToString(), Encoding.UTF8, "application/json"));
        authResp.EnsureSuccessStatusCode();
        var token = JObject.Parse(await authResp.Content.ReadAsStringAsync())["AccessToken"]!.ToString();

        http.DefaultRequestHeaders.Authorization =
            new AuthenticationHeaderValue("Bearer", token);

        // trailing slash avoids a 307 redirect on some installs
        var routerResp = await http.GetAsync($"{baseUrl}/api/ui/router/v1/?urlType=external");
        routerResp.EnsureSuccessStatusCode();
        var uiServer = JObject.Parse(await routerResp.Content.ReadAsStringAsync())["Url"]!
            .ToString().TrimEnd('/');

        return new P21Session { Http = http, UiServer = uiServer };
    }
}
```
<!-- /tabs -->

**Validate payloads before posting.** Shape mistakes (a string where an array belongs, `IgnoreDisabled` at the wrong level, booleans in quotes) fail in confusing ways. Run [`scripts/validate_payload.py`](../../scripts/validate_payload.py) on your payload file (JSON or XML) — it checks structure and field names against [`definitions/`](../../definitions/README.md) offline. See [Payload Anatomy](../03-Transaction-API.md#payload-anatomy----types-nesting-and-common-mistakes).

**Check the result, not the HTTP status.** The Transaction API returns HTTP 200 even when everything failed. Every recipe checks `Summary.Succeeded` / `Summary.Failed` and prints `Messages` on failure; transactions in one POST pass/fail independently.

**Verify after writing.** A `Succeeded` response is not proof the value landed (field-order cascades and silent no-ops exist). Each recipe ends with a read-back — OData or `POST /api/v2/transaction/get`.

**Full field lists.** Recipes show the fields that matter for the task. For *every* field a service accepts (names, types, keys, labels, payload template), load `definitions/{Service}.json` — see the [definitions README](../../definitions/README.md).

**Snippets vs end-to-end files.** The tabs on each page are self-contained snippets (portable — paste anywhere). Each recipe also links **complete runnable files** under [`examples/python/recipes/`](../../examples/python/recipes/README.md) (Python) and [`examples/csharp/Recipes/`](../../examples/csharp/Recipes/) (C#): they use the repo's shared config/auth helpers, run against your `.env`, **dry-run by default** (print the payload; `--execute` / typing `EXECUTE` posts), and end with the verify read-back.

> **Credit:** the cookbook pattern and much of the verified content come from [Alex Westemeier](https://github.com/AWestemeier)'s process playbook.
