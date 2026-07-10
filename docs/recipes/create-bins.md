# Create Bins (Bulk)

Bulk-create warehouse bins with the `BinLocation` service — one transaction per bin, tens per POST, verified in production at hundreds of bins per run.

**API:** Transaction · **Service:** `BinLocation` · **Deep dive:** [BinLocation Service — Creating Bins](../03-Transaction-API.md#binlocation-service----creating-bins), [IgnoreDisabled](../03-Transaction-API.md#ignoredisabled) · **Full schema:** [`definitions/BinLocation.json`](../../definitions/BinLocation.json)

The `BinLocation` service *is* the **Bin Location Maintenance** window: its form element `FORM.form` is business object `bin` (datawindow `d_dw_bin_form`), and every field in the payload is a real field on that screen.

## Prerequisites

- Bearer token + UI server from the [shared auth helper](README.md#shared-conventions-recipes-dont-repeat-these).
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
import httpx

BASE_URL = "https://play.p21server.com"
token, ui_server, headers = p21_auth(BASE_URL, "api_user", "password")

COMPANY_ID = "ACME"
LOCATION_ID = "10"
NEW_BIN_IDS = ["A01-02-01", "A01-02-02", "A01-02-03", "A01-02-04"]

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


# Skip-existing check via the p21_view_bin view (raw bin table isn't always in OData)
existing_resp = httpx.get(
    f"{BASE_URL}/odataservice/odata/view/p21_view_bin",
    params={"$filter": f"location_id eq {LOCATION_ID}", "$select": "bin_id"},
    headers=headers, verify=False,
)
existing_resp.raise_for_status()
existing = {row["bin_id"] for row in existing_resp.json()["value"]}

to_create = [b for b in NEW_BIN_IDS if b not in existing]
print(f"{len(NEW_BIN_IDS) - len(to_create)} already exist, creating {len(to_create)}")

BATCH_SIZE = 20  # tens of transactions per POST is fine and fast
for start in range(0, len(to_create), BATCH_SIZE):
    batch = to_create[start:start + BATCH_SIZE]
    payload = {
        "Name": "BinLocation",
        "UseCodeValues": False,
        "IgnoreDisabled": True,  # TOP LEVEL — inside a Transaction it is silently ignored
        "Transactions": [build_bin_transaction(b, LOCATION_ID, TWIN) for b in batch],
    }
    resp = httpx.post(f"{ui_server}/api/v2/transaction",
                      headers=headers, json=payload, verify=False, timeout=300)
    resp.raise_for_status()
    result = resp.json()

    summary = result["Summary"]
    print(f"Batch {start // BATCH_SIZE + 1}: "
          f"Succeeded={summary['Succeeded']}, Failed={summary['Failed']}")
    if summary["Failed"] > 0:
        for msg in result.get("Messages") or []:
            print(f"  {msg}")
    # Transactions pass/fail independently — check each one
    for bin_id, txn in zip(batch, (result.get("Results") or {}).get("Transactions") or []):
        if txn["Status"] != "Passed":
            print(f"  FAILED: {bin_id}")
```

```csharp
var session = await P21Session.CreateAsync(
    "https://play.p21server.com", "api_user", "password");

const string CompanyId = "ACME";
const string LocationId = "10";
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

JObject BuildBinTransaction(string binId)
{
    var edits = new JArray
    {
        new JObject { ["Name"] = "company_id", ["Value"] = CompanyId },
        new JObject { ["Name"] = "location_id", ["Value"] = LocationId },
        new JObject { ["Name"] = "bin_id", ["Value"] = binId },
    };
    foreach (var (name, value) in twin)
        edits.Add(new JObject { ["Name"] = name, ["Value"] = value });

    return new JObject
    {
        ["Status"] = "New",
        ["DataElements"] = new JArray
        {
            new JObject
            {
                ["Name"] = "FORM.form", ["Type"] = "Form",
                ["Keys"] = new JArray("company_id", "location_id", "bin_id"),
                ["Rows"] = new JArray(new JObject { ["Edits"] = edits }),
            }
        },
    };
}

// Skip-existing check via the p21_view_bin view (raw bin table isn't always in OData)
var existingResp = await session.Http.GetAsync(
    "https://play.p21server.com/odataservice/odata/view/p21_view_bin" +
    $"?$filter=location_id eq {LocationId}&$select=bin_id");
existingResp.EnsureSuccessStatusCode();
var existing = JObject.Parse(await existingResp.Content.ReadAsStringAsync())["value"]!
    .Select(r => (string)r["bin_id"]!).ToHashSet();

var toCreate = newBinIds.Where(b => !existing.Contains(b)).ToList();
Console.WriteLine($"{newBinIds.Length - toCreate.Count} already exist, creating {toCreate.Count}");

const int BatchSize = 20; // tens of transactions per POST is fine and fast
foreach (var batch in toCreate.Chunk(BatchSize))
{
    var payload = new JObject
    {
        ["Name"] = "BinLocation",
        ["UseCodeValues"] = false,
        ["IgnoreDisabled"] = true, // TOP LEVEL — inside a Transaction it is silently ignored
        ["Transactions"] = new JArray(batch.Select(BuildBinTransaction)),
    };
    var resp = await session.Http.PostAsync(
        $"{session.UiServer}/api/v2/transaction",
        new StringContent(payload.ToString(), Encoding.UTF8, "application/json"));
    resp.EnsureSuccessStatusCode();
    var result = JObject.Parse(await resp.Content.ReadAsStringAsync());

    Console.WriteLine($"Succeeded={result["Summary"]!["Succeeded"]}, " +
                      $"Failed={result["Summary"]!["Failed"]}");
    if ((int)result["Summary"]!["Failed"]! > 0)
        foreach (var msg in result["Messages"] as JArray ?? new JArray())
            Console.WriteLine($"  {msg}");

    // Transactions pass/fail independently — check each one
    var txns = result["Results"]?["Transactions"] as JArray ?? new JArray();
    foreach (var (binId, txn) in batch.Zip(txns))
        if ((string?)txn["Status"] != "Passed")
            Console.WriteLine($"  FAILED: {binId}");
}
```
<!-- /tabs -->

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
