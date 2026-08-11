# Create Bins (Bulk)

Bulk-create warehouse bins with the `BinLocation` service — one transaction per bin, tens per POST, verified in production at hundreds of bins per run.

**API:** Transaction · **Service:** `BinLocation` · **Deep dive:** [BinLocation Service — Creating Bins](../03-Transaction-API.md#binlocation-service-creating-bins), [IgnoreDisabled](../03-Transaction-API.md#ignoredisabled) · **Full schema:** [`definitions/BinLocation.json`](../../definitions/BinLocation.json)

The `BinLocation` service *is* the **Bin Location Maintenance** window: its form element `FORM.form` is business object `bin` (datawindow `d_dw_bin_form`), and every field in the payload is a real field on that screen.

## Prerequisites

- P21 credentials — the complete example below authenticates itself; nothing else to install but `httpx` (Python) or a bare `net9.0` console project (C#).
- A **"twin"** — an existing bin of the same `bin_type` at the target location. Copy its type, both zone codes, dimensions, sequences, `max_unique_items`, and flags rather than inventing them; that guarantees new bins match what the warehouse already uses. (Zone codes come from joining `bin.putaway_zone_uid` / `bin.pick_zone_uid` → `bin_zone.bin_zone_uid` → `bin_zone.bin_zone_id`.)
- OData read access to the `p21_view_bin` view — for the skip-existing check and the read-back (the raw `bin` table isn't always exposed via OData).

## Payload

One bin per Transaction. `Status: "New"` with the three-field key makes this a **create** when the `(company_id, location_id, bin_id)` combination doesn't exist yet. Note `IgnoreDisabled: true` at the **top level** — not inside a Transaction (see Gotchas).

```json
{
  "Name": "BinLocation",
  "UseCodeValues": false,
  "IgnoreDisabled": true,
  "Transactions": [
    {
      "Status": "New",
      "DataElements": [
        { "Name": "FORM.form", "Type": "Form",
          "Keys": ["company_id", "location_id", "bin_id"],
          "Rows": [ { "Edits": [
            {"Name": "company_id",      "Value": "ACME"},
            {"Name": "location_id",     "Value": "10"},
            {"Name": "bin_id",          "Value": "A01-02-03"},
            {"Name": "bin_type",        "Value": "SHELF"},
            {"Name": "putaway_zone_id", "Value": "ZONE-A"},
            {"Name": "pick_zone_id",    "Value": "ZONE-A"},
            {"Name": "bin_length", "Value": "10"}, {"Name": "bin_width", "Value": "10"}, {"Name": "bin_height", "Value": "11"},
            {"Name": "warehouse_sequence", "Value": "1"}, {"Name": "putaway_zone_sequence", "Value": "1"}, {"Name": "pick_zone_sequence", "Value": "1"},
            {"Name": "max_unique_items", "Value": "0"},
            {"Name": "pick_locked_flag", "Value": "OFF"}, {"Name": "put_locked_flag", "Value": "OFF"},
            {"Name": "full_flag", "Value": "OFF"}, {"Name": "frozen_flag", "Value": "OFF"},
            {"Name": "consolidation_bin_flag", "Value": "OFF"}, {"Name": "stage_bin_flag", "Value": "OFF"}, {"Name": "door_bin_flag", "Value": "OFF"}
          ] } ] }
      ]
    }
  ]
}
```

## Complete example

Builds each bin's transaction from a twin's constants, skips bins that already exist (re-running is then safe), batches several transactions per POST, and checks per-transaction results — not the HTTP status.

<!-- tabs -->
```python
"""Bulk-create warehouse bins from a twin's constants, then read each one back."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
COMPANY_ID = "ACME"
LOCATION_ID = "10"                        # stocking location the bins belong to
NEW_BIN_IDS = ["A01-02-01", "A01-02-02", "A01-02-03", "A01-02-04"]
BATCH_SIZE = 20                           # tens of transactions per POST is fine and fast
# Constants cloned from a "twin" bin of the same bin_type at this location.
# Flags come back Y/N from the database — convert to ON/OFF for the form.
TWIN = {
    "bin_type": "SHELF",
    "putaway_zone_id": "ZONE-A", "pick_zone_id": "ZONE-A",
    "bin_length": "10", "bin_width": "10", "bin_height": "11",
    "warehouse_sequence": "1", "putaway_zone_sequence": "1", "pick_zone_sequence": "1",
    "max_unique_items": "0",
    "pick_locked_flag": "OFF", "put_locked_flag": "OFF",
    "full_flag": "OFF", "frozen_flag": "OFF",
    "consolidation_bin_flag": "OFF", "stage_bin_flag": "OFF", "door_bin_flag": "OFF",
}
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


def build_bin_transaction(bin_id: str, location_id: str, twin: dict) -> dict:
    """One Transaction object per bin (keys first, then the twin's constants)."""
    edits = [
        {"Name": "company_id", "Value": COMPANY_ID},
        {"Name": "location_id", "Value": location_id},
        {"Name": "bin_id", "Value": bin_id},
    ] + [{"Name": name, "Value": value} for name, value in twin.items()]
    return {
        "Status": "New",
        "DataElements": [{
            "Name": "FORM.form", "Type": "Form",
            "Keys": ["company_id", "location_id", "bin_id"],
            "Rows": [{"Edits": edits}],
        }],
    }


with httpx.Client(verify=VERIFY_SSL, timeout=120, follow_redirects=True) as client:
    token = get_token(client)
    ui_server = get_ui_server(client, token)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",       # 2026.1 returns an empty 500 without this
        "Content-Type": "application/json",
    }

    # Skip-existing check via p21_view_bin (raw bin table isn't always in OData)
    existing_resp = client.get(
        f"{BASE_URL}/odataservice/odata/view/p21_view_bin",
        params={"$filter": f"location_id eq {LOCATION_ID}", "$select": "bin_id"},
        headers=headers,
    )
    existing_resp.raise_for_status()
    existing = {row["bin_id"] for row in existing_resp.json()["value"]}

    to_create = [b for b in NEW_BIN_IDS if b not in existing]
    print(f"{len(NEW_BIN_IDS) - len(to_create)} already exist, creating {len(to_create)}")

    for start in range(0, len(to_create), BATCH_SIZE):
        batch = to_create[start:start + BATCH_SIZE]
        payload = {
            "Name": "BinLocation",
            "UseCodeValues": False,
            # TOP LEVEL — inside a Transaction it is silently ignored
            "IgnoreDisabled": True,
            "Transactions": [build_bin_transaction(b, LOCATION_ID, TWIN) for b in batch],
        }
        resp = client.post(f"{ui_server}/api/v2/transaction",
                           headers=headers, json=payload)
        resp.raise_for_status()
        result = resp.json()

        summary = result["Summary"]
        print(f"Batch {start // BATCH_SIZE + 1}: "
              f"Succeeded={summary['Succeeded']}, Failed={summary['Failed']}")
        if summary["Failed"] > 0:
            for msg in result.get("Messages") or []:
                print(f"  {msg}")
        # Transactions pass/fail independently — check each one
        transactions = (result.get("Results") or {}).get("Transactions") or []
        for bin_id, txn in zip(batch, transactions):
            if txn["Status"] != "Passed":
                print(f"  FAILED: {bin_id}")

    # Read back every created bin through p21_view_bin (mirrors the Verify section)
    for bin_id in to_create:
        check = client.get(
            f"{BASE_URL}/odataservice/odata/view/p21_view_bin",
            params={"$filter": f"location_id eq {LOCATION_ID} and bin_id eq '{bin_id}'"},
            headers=headers,
        )
        check.raise_for_status()
        found = bool(check.json()["value"])
        print(f"{bin_id}: {'found' if found else 'MISSING'}")
```

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string CompanyId = "ACME";
const string LocationId = "10";                        // stocking location
const int BatchSize = 20;   // tens of transactions per POST is fine and fast
var newBinIds = new[] { "A01-02-01", "A01-02-02", "A01-02-03", "A01-02-04" };
// Constants cloned from a "twin" bin of the same bin_type at this location.
// Flags come back Y/N from the database — convert to ON/OFF for the form.
var twin = new (string Name, string Value)[]
{
    ("bin_type", "SHELF"),
    ("putaway_zone_id", "ZONE-A"), ("pick_zone_id", "ZONE-A"),
    ("bin_length", "10"), ("bin_width", "10"), ("bin_height", "11"),
    ("warehouse_sequence", "1"), ("putaway_zone_sequence", "1"), ("pick_zone_sequence", "1"),
    ("max_unique_items", "0"),
    ("pick_locked_flag", "OFF"), ("put_locked_flag", "OFF"),
    ("full_flag", "OFF"), ("frozen_flag", "OFF"),
    ("consolidation_bin_flag", "OFF"), ("stage_bin_flag", "OFF"), ("door_bin_flag", "OFF"),
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

object BuildBinTransaction(string binId)
{
    var edits = new List<object>
    {
        new { Name = "company_id", Value = CompanyId },
        new { Name = "location_id", Value = LocationId },
        new { Name = "bin_id", Value = binId },
    };
    foreach (var (name, value) in twin)
    {
        edits.Add(new { Name = name, Value = value });
    }

    return new
    {
        Status = "New",
        DataElements = new object[]
        {
            new
            {
                Name = "FORM.form",
                Type = "Form",
                Keys = new[] { "company_id", "location_id", "bin_id" },
                Rows = new object[] { new { Edits = edits } },
            },
        },
    };
}

// Skip-existing check via p21_view_bin (raw bin table isn't always in OData)
var existing = new HashSet<string>();
foreach (var row in await ODataAsync(
    client, "view/p21_view_bin", $"location_id eq {LocationId}", "bin_id"))
{
    existing.Add(row.GetProperty("bin_id").GetString()!);
}

var toCreate = newBinIds.Where(b => !existing.Contains(b)).ToList();
Console.WriteLine($"{newBinIds.Length - toCreate.Count} already exist, creating {toCreate.Count}");

var batchNo = 0;
foreach (var batch in toCreate.Chunk(BatchSize))
{
    batchNo++;
    var payload = new
    {
        Name = "BinLocation",
        UseCodeValues = false,
        // TOP LEVEL — inside a Transaction it is silently ignored
        IgnoreDisabled = true,
        Transactions = batch.Select(BuildBinTransaction).ToArray(),
    };
    using var resp = await client.PostAsync(
        $"{uiServer}/api/v2/transaction",
        new StringContent(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json"));
    resp.EnsureSuccessStatusCode();
    using var doc = JsonDocument.Parse(await resp.Content.ReadAsStringAsync());

    var summary = doc.RootElement.GetProperty("Summary");
    var failed = summary.GetProperty("Failed").GetInt32();
    Console.WriteLine($"Batch {batchNo}: " +
                      $"Succeeded={summary.GetProperty("Succeeded")}, Failed={failed}");
    if (failed > 0 && doc.RootElement.TryGetProperty("Messages", out var messages))
    {
        Console.WriteLine($"  {messages}");
    }

    // Transactions pass/fail independently — check each one
    if (doc.RootElement.TryGetProperty("Results", out var results) &&
        results.TryGetProperty("Transactions", out var txns))
    {
        foreach (var (binId, txn) in batch.Zip(txns.EnumerateArray()))
        {
            if (txn.GetProperty("Status").GetString() != "Passed")
            {
                Console.WriteLine($"  FAILED: {binId}");
            }
        }
    }
}

// Read back every created bin through p21_view_bin (mirrors the Verify section)
foreach (var binId in toCreate)
{
    var rows = await ODataAsync(
        client, "view/p21_view_bin",
        $"location_id eq {LocationId} and bin_id eq '{binId}'", null);
    Console.WriteLine($"{binId}: {(rows.Count > 0 ? "found" : "MISSING")}");
}

// --- helpers ---------------------------------------------------------------

static async Task<List<JsonElement>> ODataAsync(
    HttpClient client, string path, string filter, string? select)
{
    var url = $"{BaseUrl}/odataservice/odata/{path}?$filter={Uri.EscapeDataString(filter)}";
    if (select is not null) url += $"&$select={select}";
    using var response = await client.GetAsync(url);
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

> **Payload files:** [JSON](../../examples/payloads/json/create-bins.json) · [XML](../../examples/payloads/xml/create-bins.xml) — validator-verified, see [payloads README](../../examples/payloads/README.md).
>
> **End-to-end files** (runnable from the repo with a `.env`, dry-run by default): [`examples/python/recipes/create_bins.py`](../../examples/python/recipes/create_bins.py) · [`examples/csharp/Recipes/CreateBins.cs`](../../examples/csharp/Recipes/CreateBins.cs). The snippet above is self-contained; the files use the repo's shared `common` / `P21Examples.Common` helpers like every other example.

## Gotchas

- **`IgnoreDisabled: true` is mandatory — and it must be at the payload top level**, alongside `Name` and `Transactions`. `frozen_flag` and other system columns are disabled on the bin form; without the flag every transaction fails with `General Exception: Column is disabled: frozen_flag`. Placed inside a Transaction object instead of the top level, the flag is **silently ignored** and you get the same failure. See [IgnoreDisabled](../03-Transaction-API.md#ignoredisabled).
- **Pass codes, not uids.** `bin_type` and the zone fields take the **code** (`SHELF`, `ZONE-A`), not the internal uid. The zone code is the same across stocking locations; only the internal uid differs, and P21 resolves it from code + location.
- **Flags are `ON`/`OFF` on the form but stored `Y`/`N` in `dbo.bin`.** When cloning field values from an existing bin, convert (`Y`→`ON`, `N`→`OFF`).
- **Don't send `master_bin_flag`** — P21 auto-sets it.
- **Clone the constants from a "twin," don't invent them.** Query an existing bin of the same `bin_type` and copy the type, both zone codes, dimensions, sequences, `max_unique_items`, and flags.
- **HTTP 200 ≠ success.** Check `Results.Transactions[].Status == "Passed"` (or `Summary`) — in a bulk POST each transaction passes/fails independently; one failing does not roll back the others.
- **Re-running is safe** if you skip `(bin_id, location_id)` pairs that already exist — the script above does.

## Verify

The raw `bin` table isn't always exposed via OData — read back through the **`p21_view_bin`** view instead, and compare **field-for-field against the twin** after the first run (remember the `Y`/`N` ↔ `ON`/`OFF` flag mapping):

```http
GET /odataservice/odata/view/p21_view_bin?$filter=location_id eq 10 and bin_id eq 'A01-02-03'
```

> **Credit:** [Alex Westemeier](https://github.com/AWestemeier) — pattern verified in production (July 2026), including the `IgnoreDisabled` placement failure mode.
