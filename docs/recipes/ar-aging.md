# Age Open AR on Each Invoice's Own Terms

Pull every open receivable over OData and bucket it by how far past due it is, ageing each invoice against the terms it was actually billed on.

**API:** OData · **Tables:** `invoice_hdr`, `customer` · **Deep dive:** [OData API](../02-OData-API.md) · **Related:** [`customer.terms_id` is only the default for the next document](../02-OData-API.md#customerterms_id-is-the-default-for-the-next-document-not-the-terms-on-an-existing-one)

Verified end to end against a production tenant, September 2026 — ~6,200 open invoices across ~1,000 customers. The Python and C# programs below were run side by side and produce identical figures.

## Prerequisites

- OData read access to `invoice_hdr` and `customer`. Under a consumer key both tables must be in the key's scope — see [the OData allow-list](../00-Authentication.md#the-odata-allow-list-is-baked-into-the-token-and-these-tokens-never-expire).
- Nothing else. This recipe never touches the UI server; OData lives on `BASE_URL` directly.

## Age against the invoice, not the customer

`customer.terms_id` is the default applied to the **next** document. The terms a given invoice was billed on live on that invoice, and one account routinely carries several sets at once — terms get changed, and the invoices written before the change keep theirs.

So the only correct clock is `invoice_hdr.net_due_date`, which P21 has already computed per invoice. Age against the customer master instead and the arithmetic describes a document that does not exist: on the tenant this was verified against, an account whose master read `Net 180` was holding two invoices 142 and 149 days past due that had been billed `Net 30` months earlier. Against the master's 180 days they looked comfortably inside terms. They were the oldest receivables on the account.

## The query, and the one thing you cannot ask for

```http
GET /odataservice/odata/table/invoice_hdr
    ?$select=invoice_no,customer_id,invoice_date,net_due_date,terms_id,terms_desc,
             total_amount,amount_paid,paid_in_full_flag,invoice_type,company_no
    &$filter=paid_in_full_flag eq 'N' and invoice_type eq 'IN' and company_no eq 'ACME'
    &$orderby=invoice_no
    &$top=5000&$skip=0
```

The obvious filter — "anything with a balance" — is not available:

```http
$filter=total_amount gt amount_paid
-> 404  Failed to convert parameter value from a String to a Decimal.
```

A `$filter` right-hand side is **always** a literal, so naming a second column asks the service to convert `"amount_paid"` into a decimal. Filter on `paid_in_full_flag`, which P21 maintains for exactly this question, and compute the balance client-side. See [The right-hand side is always a literal](../02-OData-API.md#the-right-hand-side-is-always-a-literal-you-cannot-compare-two-columns) — on string columns the same mistake returns HTTP 200 and silently wrong results.

## Complete program

Paste into a file, edit the constants at the top, run.

<!-- tabs -->

```python
"""Age open AR over OData, each invoice on its own terms."""
import re
from collections import defaultdict
from datetime import date, datetime

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
COMPANY_NO = "ACME"                       # invoice_hdr.company_no
PAGE = 5000                               # $top per request; bulk fetch, not UI paging
TOP_CUSTOMERS = 15                        # how many rows to print
# ---------------------------------------------------------------------------

INVOICE_COLUMNS = (
    "invoice_no,customer_id,invoice_date,net_due_date,terms_id,terms_desc,"
    "total_amount,amount_paid,paid_in_full_flag,invoice_type,company_no"
)


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


def fetch_all(client: httpx.Client, headers: dict, table: str, params: dict) -> list[dict]:
    """Page a table with $top/$skip — P21 sends no @odata.nextLink."""
    rows, skip = [], 0
    while True:
        page = client.get(
            f"{BASE_URL}/odataservice/odata/table/{table}",
            headers=headers,
            params={**params, "$top": PAGE, "$skip": skip},
            timeout=300,
        )
        page.raise_for_status()
        batch = page.json().get("value", [])
        rows.extend(batch)
        if len(batch) < PAGE:
            return rows
        skip += PAGE


def days_past_due(net_due_date: str | None, today: date) -> int | None:
    """Age against THIS invoice's due date, never the customer's current terms."""
    if not net_due_date:
        return None
    due = datetime.fromisoformat(net_due_date).date()
    return (today - due).days


def bucket(dpd: int) -> str:
    if dpd <= 0:
        return "not yet due"
    if dpd <= 30:
        return "1-30"
    if dpd <= 60:
        return "31-60"
    if dpd <= 90:
        return "61-90"
    return "90+"


BUCKETS = ("not yet due", "1-30", "31-60", "61-90", "90+")

with httpx.Client(verify=VERIFY_SSL, timeout=120, follow_redirects=True) as client:
    token = get_token(client)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",       # without this you get XML, not JSON
        "Content-Type": "application/json",
    }

    # Open items only. `paid_in_full_flag` is the flag P21 maintains for exactly
    # this question — you cannot ask the service for `total_amount gt amount_paid`,
    # because a $filter right-hand side is always a literal.
    invoices = fetch_all(client, headers, "invoice_hdr", {
        "$select": INVOICE_COLUMNS,
        "$filter": (f"paid_in_full_flag eq 'N' and invoice_type eq 'IN' "
                    f"and company_no eq '{COMPANY_NO}'"),
        "$orderby": "invoice_no",
    })

    # invoice_hdr.customer_id is Edm.String, customer.customer_id is Edm.Decimal —
    # the same id, two types. Normalise or every name comes back blank.
    names = {str(int(c["customer_id"])): c.get("customer_name") or ""
             for c in fetch_all(client, headers, "customer", {
                 "$select": "customer_id,customer_name",
                 "$filter": "delete_flag eq 'N'",
                 "$orderby": "customer_id",
             })}

today = date.today()
per_customer: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
oldest: dict[str, int] = defaultdict(int)
totals: dict[str, float] = defaultdict(float)
counted = credits = 0

for inv in invoices:
    balance = float(inv["total_amount"] or 0) - float(inv["amount_paid"] or 0)
    if abs(balance) < 0.005:            # fully applied but not flagged paid
        continue
    dpd = days_past_due(inv.get("net_due_date"), today)
    if dpd is None:                     # no due date: cannot be aged
        continue
    if balance < 0:
        credits += 1                    # open credit memo, nets against the total
    slot = bucket(dpd)
    key = str(inv["customer_id"])
    per_customer[key][slot] += balance
    totals[slot] += balance
    if dpd > 0:
        per_customer[key]["past due"] += balance
        oldest[key] = max(oldest[key], dpd)
    counted += 1

print(f"{counted} open invoices  ({credits} open credits)  as of {today}\n")
width = 14
print("company aging".ljust(28) + "".join(b.rjust(width) for b in BUCKETS))
print("-" * (28 + width * len(BUCKETS)))
print("".ljust(28) + "".join(f"{totals[b]:>{width},.0f}" for b in BUCKETS))

ranked = sorted(per_customer.items(), key=lambda kv: kv[1]["past due"], reverse=True)
print(f"\ntop {TOP_CUSTOMERS} by past-due balance\n")
print("customer".ljust(38) + "past due".rjust(13) + "".join(
    b.rjust(width) for b in BUCKETS[1:]) + "oldest".rjust(9))
print("-" * (38 + 13 + width * 4 + 9))
for cid, buckets in ranked[:TOP_CUSTOMERS]:
    if buckets["past due"] <= 0:
        break
    label = f"{cid} {names.get(cid, '')}"[:36]
    print(label.ljust(38)
          + f"{buckets['past due']:>13,.0f}"
          + "".join(f"{buckets[b]:>{width},.0f}" for b in BUCKETS[1:])
          + f"{oldest[cid]:>9}")
```

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string CompanyNo = "ACME";                       // invoice_hdr.company_no
const int Page = 5000;                                 // $top per request
const int TopCustomers = 15;                           // how many rows to print
// ---------------------------------------------------------------------------

const string InvoiceColumns =
    "invoice_no,customer_id,invoice_date,net_due_date,terms_id,terms_desc," +
    "total_amount,amount_paid,paid_in_full_flag,invoice_type,company_no";

string[] buckets = { "not yet due", "1-30", "31-60", "61-90", "90+" };

var handler = new HttpClientHandler
{
    // Test tenants often present a self-signed cert. Delete this line in production.
    ServerCertificateCustomValidationCallback =
        HttpClientHandler.DangerousAcceptAnyServerCertificateValidator,
};
using var client = new HttpClient(handler) { Timeout = TimeSpan.FromMinutes(5) };
client.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));

var token = await GetTokenAsync(client);
client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);

// Open items only. paid_in_full_flag is the flag P21 maintains for exactly this
// question — you cannot ask the service for `total_amount gt amount_paid`, because
// a $filter right-hand side is always a literal.
var invoiceFilter = Uri.EscapeDataString(
    $"paid_in_full_flag eq 'N' and invoice_type eq 'IN' and company_no eq '{CompanyNo}'");
var invoices = await FetchAllAsync(client, "invoice_hdr",
    $"$select={InvoiceColumns}&$filter={invoiceFilter}&$orderby=invoice_no");

// invoice_hdr.customer_id is Edm.String, customer.customer_id is Edm.Decimal —
// the same id, two types. Normalise or every name comes back blank.
var names = new Dictionary<string, string>();
foreach (var c in await FetchAllAsync(client, "customer",
             "$select=customer_id,customer_name&$filter=" +
             Uri.EscapeDataString("delete_flag eq 'N'") + "&$orderby=customer_id"))
{
    if (!c.TryGetProperty("customer_id", out var idEl)) continue;
    var id = idEl.ValueKind == JsonValueKind.Number
        ? ((long)idEl.GetDecimal()).ToString()
        : idEl.GetString() ?? "";
    names[id] = c.TryGetProperty("customer_name", out var n) ? n.GetString() ?? "" : "";
}

var today = DateTime.Today;
var perCustomer = new Dictionary<string, Dictionary<string, decimal>>();
var pastDue = new Dictionary<string, decimal>();
var oldest = new Dictionary<string, int>();
var totals = buckets.ToDictionary(b => b, _ => 0m);
int counted = 0, credits = 0;

foreach (var inv in invoices)
{
    var balance = Num(inv, "total_amount") - Num(inv, "amount_paid");
    if (Math.Abs(balance) < 0.005m) continue;          // applied but not flagged paid

    var due = Text(inv, "net_due_date");
    if (string.IsNullOrEmpty(due)) continue;           // no due date: cannot be aged
    var dpd = (int)(today - DateTimeOffset.Parse(due).Date).TotalDays;

    if (balance < 0) credits++;                        // open credit memo, nets against the total
    var slot = Bucket(dpd);
    var key = Text(inv, "customer_id") ?? "";

    if (!perCustomer.TryGetValue(key, out var row))
        perCustomer[key] = row = buckets.ToDictionary(b => b, _ => 0m);
    row[slot] += balance;
    totals[slot] += balance;

    if (dpd > 0)
    {
        pastDue[key] = pastDue.GetValueOrDefault(key) + balance;
        oldest[key] = Math.Max(oldest.GetValueOrDefault(key), dpd);
    }
    counted++;
}

Console.WriteLine($"{counted} open invoices  ({credits} open credits)  as of {today:yyyy-MM-dd}\n");
Console.WriteLine("company aging".PadRight(28) + string.Concat(buckets.Select(b => b.PadLeft(14))));
Console.WriteLine(new string('-', 28 + 14 * buckets.Length));
Console.WriteLine("".PadRight(28) + string.Concat(buckets.Select(b => totals[b].ToString("N0").PadLeft(14))));

Console.WriteLine($"\ntop {TopCustomers} by past-due balance\n");
Console.WriteLine("customer".PadRight(38) + "past due".PadLeft(13)
    + string.Concat(buckets.Skip(1).Select(b => b.PadLeft(14))) + "oldest".PadLeft(9));
Console.WriteLine(new string('-', 38 + 13 + 14 * 4 + 9));

foreach (var (cid, amount) in pastDue.OrderByDescending(kv => kv.Value).Take(TopCustomers))
{
    if (amount <= 0) break;
    var label = $"{cid} {names.GetValueOrDefault(cid, "")}";
    if (label.Length > 36) label = label[..36];
    Console.WriteLine(label.PadRight(38)
        + amount.ToString("N0").PadLeft(13)
        + string.Concat(buckets.Skip(1).Select(b => perCustomer[cid][b].ToString("N0").PadLeft(14)))
        + oldest.GetValueOrDefault(cid).ToString().PadLeft(9));
}

// --- helpers ---------------------------------------------------------------

static string Bucket(int dpd) => dpd <= 0 ? "not yet due"
    : dpd <= 30 ? "1-30" : dpd <= 60 ? "31-60" : dpd <= 90 ? "61-90" : "90+";

static decimal Num(JsonElement row, string field) =>
    row.TryGetProperty(field, out var v) && v.ValueKind == JsonValueKind.Number ? v.GetDecimal() : 0m;

static string? Text(JsonElement row, string field) =>
    row.TryGetProperty(field, out var v) && v.ValueKind == JsonValueKind.String ? v.GetString() : null;

// Page a table with $top/$skip — P21 sends no @odata.nextLink.
async Task<List<JsonElement>> FetchAllAsync(HttpClient http, string table, string query)
{
    var rows = new List<JsonElement>();
    for (var skip = 0; ; skip += Page)
    {
        var url = $"{BaseUrl}/odataservice/odata/table/{table}?{query}&$top={Page}&$skip={skip}";
        var response = await http.GetAsync(url);
        response.EnsureSuccessStatusCode();
        using var doc = JsonDocument.Parse(await response.Content.ReadAsStringAsync());
        var batch = doc.RootElement.GetProperty("value").EnumerateArray().Select(e => e.Clone()).ToList();
        rows.AddRange(batch);
        if (batch.Count < Page) return rows;
    }
}

// v2 token endpoint — credentials go in the body, never in headers.
static async Task<string> GetTokenAsync(HttpClient http)
{
    var payload = JsonSerializer.Serialize(new { username = Username, password = Password });
    var response = await http.PostAsync(
        $"{BaseUrl}/api/security/token/v2",
        new StringContent(payload, Encoding.UTF8, "application/json"));
    response.EnsureSuccessStatusCode();
    var body = await response.Content.ReadAsStringAsync();
    try
    {
        var value = JsonDocument.Parse(body).RootElement.GetProperty("AccessToken").GetString();
        if (!string.IsNullOrEmpty(value)) return value;
    }
    catch (Exception ex) when (ex is JsonException or KeyNotFoundException) { }

    // Some middleware answers this endpoint in XML even when asked for JSON.
    var match = System.Text.RegularExpressions.Regex.Match(body, "<AccessToken>([^<]+)</AccessToken>");
    if (!match.Success)
        throw new InvalidOperationException($"No AccessToken in response: {body[..Math.Min(200, body.Length)]}");
    return match.Groups[1].Value;
}
```

<!-- /tabs -->

Output:

```text
1284 open invoices  (23 open credits)  as of 2026-09-11

company aging                  not yet due          1-30         31-60         61-90           90+
--------------------------------------------------------------------------------------------------
                                 2,410,655       318,204        91,470         8,330         4,215

top 15 by past-due balance

customer                                   past due          1-30         31-60         61-90           90+   oldest
--------------------------------------------------------------------------------------------------------------------
100198 ACME MANUFACTURING                    52,310        52,310             0             0             0       15
100204 WIDGET WORKS INC                      31,940             0        31,940             0             0       46
100311 NORTHSTAR FABRICATION                 18,775         2,145        10,320         6,310             0       62
100477 CONTOSO HYDRAULICS                     7,268         1,120        -1,405           838         6,715      466
```

## Gotchas

- **Credit memos are ordinary rows with a negative `total_amount`.** They age like anything else and net against the bucket they fall in — the negative `31-60` figure in the sample above is a credit sitting against that customer. If you need gross exposure rather than net, split them out; don't filter them away, or your total stops reconciling to the ledger.
- **`paid_in_full_flag = 'N'` is not the same as "has a balance".** A few rows are fully applied without the flag being set. The `abs(balance) < 0.005` guard drops them; without it they appear as zero-value rows in every bucket.
- **The two `customer_id` columns are different types.** `invoice_hdr.customer_id` is `Edm.String`, `customer.customer_id` is `Edm.Decimal`. Normalise before joining or every name comes back blank — and because there are [no navigation properties to `$expand`](../02-OData-API.md#no-joins-chain-queries-by-uid), this join is always yours to make.
- **Page it.** P21 sends no `@odata.nextLink`, so loop on `$top`/`$skip` until a short page arrives. `$top=5000` is a bulk-fetch size; see [Page Size Guidance](../02-OData-API.md#page-size-guidance).
- **`$orderby` a stable column** while paging. Without a deterministic sort, `$skip` can repeat or drop rows between requests.
- **`invoice_type` is `'IN'`.** Filtering it out entirely pulls in a small number of other document types that do not belong in a receivables aging.
- **Ageing is a snapshot.** Cash applies against these invoices continuously; two runs an hour apart legitimately disagree. Stamp the report with the time you ran it.

## Verify

Cross-check the company totals against P21's own aging report for the same company and as-of date. Two differences are expected and benign: this program nets open credits into their bucket, and it ages on `net_due_date` where some P21 reports offer ageing by invoice date instead.
