# Generate Pick Ticket and PO PDFs

Generate or reprint pick tickets and purchase orders as base64-encoded PDFs via the dedicated report endpoint. The production-order pick ticket is the worked example below; a **sales-order** pick ticket takes a different payload and has two eligibility traps — see [Sales-order pick ticket](#sales-order-pick-ticket).

**API:** Transaction (`POST /api/v2/process/pdfreport`) · **Service:** `m_picktickets`, `m_reprintpicktickets`, `m_reprintpurchaseorders` · **Deep dive:** [PDF Report Generation](../03-Transaction-API.md#pdf-report-generation) · **Full schema:** [m_picktickets.json](../../definitions/m_picktickets.json) · [m_reprintpicktickets.json](../../definitions/m_reprintpicktickets.json) · [m_reprintpurchaseorders.json](../../definitions/m_reprintpurchaseorders.json)

## Prerequisites

- P21 credentials — the complete example below authenticates itself; nothing to install but `httpx` (Python) or a bare `net8.0`-or-later console project (C#).
- **For `m_picktickets` against a production order**: the production order's form must already be printed (`prod_order_hdr.printed = 'Y'`) — run a `ProductionOrder` transaction with `print_form = ON` first.
- The `m_*` report services are **hidden from `GET /api/v2/services`** (`?type=report` returns an empty list), but `GET /api/v2/definition/{service_name}` and `GET /api/v2/defaults/{service_name}` both work for them — use those for criteria field names and defaults. On a 25.2 test system, probing candidates from the `window_x_menu` table yields ~157 callable report services (`m_picktickets`, `m_reprintpicktickets`, `m_productionorders`, `m_orderacknowledgements`, `m_invoices`, `m_packinglists`, `m_customerstatements`, …) — see the Discovery note in the [deep dive](../03-Transaction-API.md#pdf-report-generation).

> **Wrong-endpoint trap:** `POST /api/v2/transaction` *accepts* an `m_*` report payload and returns `Succeeded` — but **emits nothing**. A report is a process, not a record edit; it must go to `POST /api/v2/process/pdfreport`.

## Payload

Constants for **every** report payload: `Status` is `"New"`, the same and only value the [Transaction API enum accepts](../03-Transaction-API.md#status-new-is-the-only-value-the-enum-accepts); `Type` is `"Form"`; and the DataElement carries `Keys: []`. Only `Name`, the DataElement name, and the criteria `Edits` change per service.

**`m_picktickets`** — *creates* the pick-ticket record at `location_id` **and** returns its PDF in one call (verified worked example). For a **production order** it requires `UseCodeValues: true` with the code `"P"`; a sales order is the other way round — labels with `UseCodeValues: false`, see [Sales-order payload](#sales-order-payload):

```json
POST {ui_server}/api/v2/process/pdfreport

{
  "Name": "m_picktickets",
  "UseCodeValues": true,
  "Transactions": [{
    "Status": "New",
    "DataElements": [{
      "Keys": [],
      "Type": "Form",
      "Name": "TABPAGE_1.tp_1_dw_1",
      "Rows": [{ "Edits": [
        { "Name": "create_pick_ticket_type", "Value": "P" },
        { "Name": "beg_prod_order", "Value": "1000123" },
        { "Name": "end_prod_order", "Value": "1000123" },
        { "Name": "location_id",    "Value": "10" }
      ] }]
    }]
  }]
}
```

**`m_reprintpurchaseorders`** — PO print or reprint (verified with `UseCodeValues: false`). DataElement name is `TABPAGE_1.poreportcriteriadw`:

```json
{ "Name": "company_id", "Value": "ACME" },
{ "Name": "beg_po_no",  "Value": "500100" },
{ "Name": "end_po_no",  "Value": "500100" },
{ "Name": "reprint_flag", "Value": "<po_hdr.printed: Y or N>" }
```

> **`reprint_flag` is not a constant.** It must equal the PO's own `po_hdr.printed`: `N` for a PO that was never printed, `Y` for one that was. A mismatch returns an empty HTTP 500 on every attempt, which looks like the transient fault a retry clears but is not. Read `printed` over OData first (`po_hdr?$filter=po_no eq 500100&$select=po_no,printed`), and re-read it before each retry. A first print with `N` marks the PO printed. Detail: [`reprint_flag` must match the PO's `po_hdr.printed`](../03-Transaction-API.md#reprint_flag-must-match-the-pos-po_hdrprinted). Runnable PO print/reprint: [`examples/python/recipes/reprint_purchase_order.py`](../../examples/python/recipes/reprint_purchase_order.py) · [`examples/csharp/Recipes/ReprintPurchaseOrder.cs`](../../examples/csharp/Recipes/ReprintPurchaseOrder.cs) — run on play 26.1.5950.0, 2026-10-10, against a never-printed PO and the same PO once printed; both succeed.

**`m_reprintpicktickets`** — pick-ticket reprint. DataElement name is `TABPAGE_1.tp_1_dw_1` (datawindow `d_reprint_pick_ticket_criteria`); the [definition](../../definitions/m_reprintpicktickets.json) marks `company_id`, `location_id`, and `print_qty` required, with ranges `beg_pick_ticket_no`/`end_pick_ticket_no` (sales-order tickets) and `beg_prod_pick_ticket_no`/`end_prod_pick_ticket_no` (production tickets). Its `pick_ticket_type` takes the display values `Sales Order`, `Production Order` or `Both`, and `print_dea_pick_tickets` takes `Yes`, `No` or `Only` (from the live definition, 2026-08-11).

> **`UseCodeValues: false` with the display values works on 26.1.5950.0.** A scratch test on play 26.1.5950.0, 2026-10-10, reprinted one sales-order pick ticket (`beg_pick_ticket_no` = `end_pick_ticket_no`, `company_id`, `location_id`, `print_qty` = `1`, `pick_ticket_type` = `Sales Order`) and got HTTP 200 with one document, `StatusCode` `Success`, a one-page PDF of that ticket and order (`FileName` `PT<nnn> PICK_TICKET.pdf`, a document counter, not the ticket number). Results by setting:
>
> | `UseCodeValues` | `pick_ticket_type` | Result |
> |---|---|---|
> | `false` | `Sales Order`, or omitted | PDF |
> | `true` | `S`, or omitted | PDF |
> | `true` | `Sales Order` | Empty HTTP 500 on three attempts in a row; a label under `UseCodeValues: true` is a deterministic failure, not a transient one |
>
> A **direct-ship** pick ticket (the one `DirectShipConfirmation` creates) returned HTTP 200 with an empty array `[]` — no document and no error — on every attempt, while a stock ticket from the same location printed. Check for an empty array as well as for a failed `ResponseStatus`. The production-ticket case is under [Verify](#verify). Before you treat any other 5xx as a payload problem, read [An empty 5xx has several causes](../03-Transaction-API.md#an-empty-5xx-has-several-causes-and-is-usually-transient); on the Play tenant at 26.1.5910.3 *every* report returned an empty HTTP 500.

For any *other* report, swap `Name` and the criteria `Edits` (field names from `GET /api/v2/definition/{name}`); the endpoint, `Status`/`Type: 0`, `Keys: []`, and the `DocumentData` extraction stay the same.

## Complete example

Generates a production-order pick ticket with `m_picktickets`, decodes the base64 PDF to `OUTPUT_DIR`, and handles both failure shapes (document-level `ResponseStatus` and the P21 error envelope). Because `m_picktickets` also **creates** the ticket row, the program finishes with the read-back from the Verify section: the production order's `prod_pick_ticket_hdr` rows over OData, before and after the run.

<!-- tabs -->
```python
"""Generate a production-order pick ticket PDF, save it, and re-read it back."""
import base64
import os
import re
import time

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.example.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
PROD_ORDER = "1000123"                    # production order number (beg = end)
LOCATION_ID = "10"                        # location the components pick from
OUTPUT_DIR = "."                          # where the .pdf files are written
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


def save_documents(result: list, prefix: str) -> list[str]:
    """Write every returned base64 document to OUTPUT_DIR; return the paths."""
    saved = []
    for doc in result:
        status = doc.get("ResponseStatus", {}).get("StatusCode")
        if status != "Success" or not doc.get("DocumentData"):
            msg = doc.get("ResponseStatus", {}).get("Message", "Unknown error")
            print(f"Document failed: {msg}")
            continue
        pdf_bytes = base64.b64decode(doc["DocumentData"])
        # FileName includes .pdf, e.g. "PPT<nnn> PRODUCTION_PICK_TICKET.pdf";
        # <nnn> is a document counter, not the pick-ticket number
        filename = doc.get("FileName", f"{prefix}.pdf")
        path = os.path.join(OUTPUT_DIR, filename)
        with open(path, "wb") as f:
            f.write(pdf_bytes)
        # A real PDF starts with the %PDF magic bytes
        print(f"Saved {path} ({len(pdf_bytes)} bytes, "
              f"starts with {pdf_bytes[:4]!r})")
        saved.append(filename)
    return saved


def run_report(client: httpx.Client, ui_server: str, headers: dict,
               payload: dict, attempts: int = 3) -> list:
    """POST a report payload and return its document array.

    Retries transient faults: the report engine emits occasional empty 5xx
    responses that clear on the next try (in production, 3 empty 500s and one
    dropped connection against 154 successes in an afternoon). Generating a
    document is an idempotent read, so a retry costs latency, not correctness.
    """
    for attempt in range(1, attempts + 1):
        response = client.post(f"{ui_server}/api/v2/process/pdfreport",
                               headers=headers, json=payload)

        # Parse the body BEFORE looking at the status code. This endpoint
        # returns P21's ErrorType/ErrorMessage envelope -- not the
        # Summary/Messages shape of /transaction -- and that envelope can
        # arrive on a 200 as well as a 4xx/5xx. Branching on the status first
        # throws away the only message that explains the failure.
        try:
            result = response.json()
        except ValueError:
            result = None
        if isinstance(result, dict) and result.get("ErrorMessage"):
            # A real, explained rejection (e.g. "No records to print for this
            # range.") -- retrying will not change it.
            raise SystemExit(f"{result.get('ErrorType')}: {result['ErrorMessage']}")

        if response.status_code < 400:
            break
        if attempt < attempts:
            time.sleep(0.5 * attempt)
    else:
        response = None

    if response is None or response.status_code >= 400:
        # An empty 5xx has several unrelated causes: a transient engine fault
        # (retried above), criteria that match nothing (e.g. a wrong
        # company_id), or a record that is not printable.
        raise SystemExit(
            f"HTTP {response.status_code} after {attempts} attempts. "
            f"Body: {(response.text or '(empty)')[:300]}")

    # Success is a JSON ARRAY -- even for a single document
    if not (isinstance(result, list) and result):
        raise SystemExit(f"No documents returned: {result}")
    return result


with httpx.Client(verify=VERIFY_SSL, timeout=120, follow_redirects=True) as client:
    token = get_token(client)
    ui_server = get_ui_server(client, token)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",       # without this you get XML, not JSON
        "Content-Type": "application/json",
    }

    payload = {
        "Name": "m_picktickets",
        "UseCodeValues": True,   # required here -- False returns HTTP 500
        "Transactions": [{
            "Status": "New",
            "DataElements": [{
                "Keys": [],      # always empty for reports
                "Type": "Form",
                "Name": "TABPAGE_1.tp_1_dw_1",
                "Rows": [{"Edits": [
                    # code "P" = Production Order (the display label is rejected)
                    {"Name": "create_pick_ticket_type", "Value": "P"},
                    {"Name": "beg_prod_order", "Value": PROD_ORDER},
                    {"Name": "end_prod_order", "Value": PROD_ORDER},
                    # location whose inventory the components pick from
                    {"Name": "location_id", "Value": LOCATION_ID},
                ]}],
            }],
        }],
    }
    def read_tickets() -> dict:
        """The order's production pick tickets, read over OData."""
        r = client.get(
            f"{BASE_URL}/odataservice/odata/table/prod_pick_ticket_hdr",
            params={"$filter": f"prod_order_number eq {PROD_ORDER}",
                    "$select": "prod_pick_ticket_number,location_id,row_status_flag"},
            headers=headers,
        )
        r.raise_for_status()
        return {row["prod_pick_ticket_number"]: row for row in r.json()["value"]}

    before = read_tickets()
    save_documents(run_report(client, ui_server, headers, payload), "pick_ticket")

    # --- Read-back: m_picktickets CREATED a ticket row; find it over OData. ---
    # The FileName number (PPT<nnn>) is a document counter, not the ticket
    # number, so compare the order's tickets before and after the run.
    after = read_tickets()
    new = [after[n] for n in sorted(set(after) - set(before))]
    if not new:
        raise SystemExit(f"No new pick ticket on production order {PROD_ORDER}")
    for ticket in new:
        # row_status_flag: 702 = Open, 1962 = Confirmed, 1268 = Completed
        print(f"New ticket {ticket['prod_pick_ticket_number']} at location "
              f"{ticket['location_id']}: status {ticket['row_status_flag']}")
```

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.example.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string ProdOrder = "1000123";     // production order number (beg = end)
const string LocationId = "10";         // location the components pick from
const string OutputDir = ".";           // where the .pdf files are written
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
    Name = "m_picktickets",
    UseCodeValues = true,   // required here -- false returns HTTP 500
    Transactions = new object[]
    {
        new
        {
            Status = "New",
            DataElements = new object[]
            {
                new
                {
                    Keys = Array.Empty<string>(),   // always empty for reports
                    Type = "Form",
                    Name = "TABPAGE_1.tp_1_dw_1",
                    Rows = new object[]
                    {
                        new
                        {
                            Edits = new[]
                            {
                                // code "P" = Production Order (label is rejected)
                                new { Name = "create_pick_ticket_type", Value = "P" },
                                new { Name = "beg_prod_order", Value = ProdOrder },
                                new { Name = "end_prod_order", Value = ProdOrder },
                                // location whose inventory the components pick from
                                new { Name = "location_id", Value = LocationId },
                            },
                        },
                    },
                },
            },
        },
    },
};

var before = await ReadTicketsAsync(client);
SaveDocuments(await RunReportAsync(client, uiServer, payload), "pick_ticket");

// --- Read-back: m_picktickets CREATED a ticket row; find it over OData. ---
// The FileName number (PPT<nnn>) is a document counter, not the ticket
// number, so compare the order's tickets before and after the run.
var after = await ReadTicketsAsync(client);
var created = after.Keys.Except(before.Keys).OrderBy(n => n).ToList();
if (created.Count == 0)
    throw new InvalidOperationException($"No new pick ticket on production order {ProdOrder}");
foreach (var number in created)
{
    var ticket = after[number];
    // row_status_flag: 702 = Open, 1962 = Confirmed, 1268 = Completed
    Console.WriteLine($"New ticket {number} at location {ticket.GetProperty("location_id")}: " +
                      $"status {ticket.GetProperty("row_status_flag")}");
}

// --- helpers ---------------------------------------------------------------

// The order's production pick tickets, read over OData, keyed by ticket number.
static async Task<Dictionary<long, JsonElement>> ReadTicketsAsync(HttpClient client)
{
    var filter = Uri.EscapeDataString($"prod_order_number eq {ProdOrder}");
    using var response = await client.GetAsync(
        $"{BaseUrl}/odataservice/odata/table/prod_pick_ticket_hdr?$filter={filter}" +
        "&$select=prod_pick_ticket_number,location_id,row_status_flag");
    response.EnsureSuccessStatusCode();
    using var doc = JsonDocument.Parse(await response.Content.ReadAsStringAsync());
    return doc.RootElement.GetProperty("value").EnumerateArray().ToDictionary(
        row => row.GetProperty("prod_pick_ticket_number").GetInt64(), row => row.Clone());
}

// POST a report payload and return its document array.
//
// Retries transient faults: the report engine emits occasional empty 5xx
// responses that clear on the next try (in production, 3 empty 500s and one
// dropped connection against 154 successes in an afternoon). Generating a
// document is an idempotent read, so a retry costs latency, not correctness.
static async Task<List<JsonElement>> RunReportAsync(
    HttpClient client, string uiServer, object payload, int attempts = 3)
{
    var body = JsonSerializer.Serialize(payload);
    for (var attempt = 1; ; attempt++)
    {
        using var response = await client.PostAsync(
            $"{uiServer}/api/v2/process/pdfreport",
            new StringContent(body, Encoding.UTF8, "application/json"));
        var bodyText = await response.Content.ReadAsStringAsync();

        // Parse the body BEFORE looking at the status code. This endpoint
        // returns P21's ErrorType/ErrorMessage envelope -- not the
        // Summary/Messages shape of /transaction -- and that envelope can
        // arrive on a 200 as well as a 4xx/5xx. Branching on the status first
        // throws away the only message that explains the failure.
        JsonDocument? parsed = null;
        try { parsed = JsonDocument.Parse(bodyText); }
        catch (JsonException) { /* empty or non-JSON body */ }

        using (parsed)
        {
            var root = parsed?.RootElement;
            if (root is { ValueKind: JsonValueKind.Object } obj &&
                obj.TryGetProperty("ErrorMessage", out var err))
            {
                // A real, explained rejection ("No records to print for this
                // range.") -- retrying will not change it.
                throw new InvalidOperationException($"{obj.GetProperty("ErrorType")}: {err}");
            }

            if (response.IsSuccessStatusCode)
            {
                // Success is a JSON ARRAY -- even for a single document
                if (root is not { ValueKind: JsonValueKind.Array } arr || arr.GetArrayLength() == 0)
                    throw new InvalidOperationException($"No documents returned: {bodyText}");
                return arr.EnumerateArray().Select(x => x.Clone()).ToList();
            }

            if (attempt >= attempts)
            {
                // An empty 5xx has several unrelated causes: a transient engine
                // fault (retried above), criteria that match nothing (e.g. a
                // wrong company_id), or a record that is not printable.
                throw new InvalidOperationException(
                    $"HTTP {(int)response.StatusCode} after {attempts} attempts. " +
                    $"Body: {(string.IsNullOrEmpty(bodyText) ? "(empty)" : bodyText)}");
            }
        }
        await Task.Delay(TimeSpan.FromSeconds(0.5 * attempt));
    }
}

// Write every returned base64 document to OutputDir; return the file names.
static List<string> SaveDocuments(List<JsonElement> documents, string prefix)
{
    var saved = new List<string>();
    foreach (var doc in documents)
    {
        var responseStatus = doc.GetProperty("ResponseStatus");
        var status = responseStatus.GetProperty("StatusCode").GetString();
        var documentData = doc.TryGetProperty("DocumentData", out var d) ? d.GetString() : null;
        if (status != "Success" || string.IsNullOrEmpty(documentData))
        {
            var message = responseStatus.TryGetProperty("Message", out var m)
                ? m.GetString() : "Unknown error";
            Console.WriteLine($"Document failed: {message}");
            continue;
        }
        var pdfBytes = Convert.FromBase64String(documentData);
        // FileName includes .pdf, e.g. "PPT<nnn> PRODUCTION_PICK_TICKET.pdf";
        // <nnn> is a document counter, not the pick-ticket number
        var filename = doc.TryGetProperty("FileName", out var f)
            ? f.GetString()! : $"{prefix}.pdf";
        var path = Path.Combine(OutputDir, filename);
        File.WriteAllBytes(path, pdfBytes);
        // A real PDF starts with the %PDF magic bytes
        Console.WriteLine($"Saved {path} ({pdfBytes.Length} bytes, starts with " +
                          $"{Encoding.ASCII.GetString(pdfBytes, 0, 4)})");
        saved.Add(filename);
    }
    return saved;
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

> **Payload files:** [JSON](../../examples/payloads/json/generate-pick-ticket-pdf.json) · [reprint JSON](../../examples/payloads/json/reprint-purchase-order-pdf.json) (XML untested for the pdfreport endpoint) — validator-verified, see [payloads README](../../examples/payloads/README.md).
>
> **End-to-end files** (runnable from the repo with a `.env`, dry-run by default): [`examples/python/recipes/generate_pick_ticket_pdf.py`](../../examples/python/recipes/generate_pick_ticket_pdf.py) · [`examples/csharp/Recipes/GeneratePickTicketPdf.cs`](../../examples/csharp/Recipes/GeneratePickTicketPdf.cs). The snippet above is self-contained; the files use the repo's shared `common` / `P21Examples.Common` helpers like every other example.

## Gotchas

All verified live — details in [PDF Report Generation](../03-Transaction-API.md#pdf-report-generation):

- **Wrong-endpoint trap** — `POST /api/v2/transaction` *accepts* an `m_*` payload and returns `Succeeded`, but **emits nothing**. Reports must go to `POST /api/v2/process/pdfreport`. ("This was the single biggest gotcha.")
- **Retry an empty 5xx before believing it.** The report engine faults intermittently — a production integration generating PO PDFs all day logged **3 empty 500s and one dropped connection against 154 successes in a single afternoon**, and every affected PO succeeded moments later. Generating a document is an idempotent read, so retry (3 attempts, 0.5 s × attempt) as the examples above do. A *deterministic* empty 5xx is a different animal: criteria that match nothing (a wrong `company_id`), a PO `reprint_flag` that doesn't match `po_hdr.printed`, a record that isn't printable, or an environment where report generation isn't available. See [An empty 5xx has several causes](../03-Transaction-API.md#an-empty-5xx-has-several-causes-and-is-usually-transient).
- **Read the error envelope before the status code.** This endpoint returns P21's `ErrorType`/`ErrorMessage` envelope, and it can arrive on a **200** as well as a 4xx/5xx. Checking `response.status_code` first discards the one message that explains the failure — the examples above parse the body first for that reason.
- **Check the record exists first.** A missing record and a transient engine fault both surface as an unhelpful 5xx. A cheap OData read before the report call turns "not found" into your own clear error and leaves the 5xx meaning only "the engine faulted".
- **`UseCodeValues` requirements vary per report service, and within `m_picktickets` per ticket type.** `m_reprintpurchaseorders` works with `UseCodeValues: false`. A production-order `m_picktickets` run **requires `UseCodeValues: true` with code values** — `create_pick_ticket_type` must be the code `"P"`; the display label `"Production Order"` is rejected, and `UseCodeValues: false` returns HTTP 500. A sales-order run is the reverse: the label `"Sales Order"` with `UseCodeValues: false` works, and `true` with `"S"` or `"O"` returned an empty HTTP 500 (play 26.1.5950.0, 2026-10-17). When a report errors on seemingly-correct criteria, try the other setting: `UseCodeValues: true` with the code values from the definition's `ValidValues`, or `false` with the labels.
- **`m_reprintpurchaseorders`: `reprint_flag` must equal `po_hdr.printed`.** `N` renders only never-printed POs and `Y` only printed ones; the wrong one is a deterministic empty 500 that a retry never clears. Read `printed` over OData before each call, including before a retry, because another user can print the PO in between. A first print marks the PO printed.
- **`Status` is `"New"`, `Type` is `"Form"`**, with `Keys: []`. Older copies of these payloads sent the integers `0`/`0`; integer `0` binds to the same enum member, so they rendered the same PDF, but integers are never range-checked. Send the strings.
- **`m_picktickets` prerequisite (production order)**: the production order's form must already be printed (`prod_order_hdr.printed = 'Y'`) — run a `ProductionOrder` transaction with `print_form = ON` first. No date range is needed for a production order (a sales order needs all three — see [Eligibility traps](#eligibility-traps)); `location_id` is the location the components pick from.
- **`m_picktickets` has a side effect**: the pick-ticket row now exists in P21 at that location and can be confirmed/completed like any other.
- **Print flags on `/transaction` have limits.** A service's print flags (e.g. `ProductionOrder` `print_pick_ticket`/`print_form` on `TABPAGE_1.tp_1_dw_1`) return PDFs at `Results.Transactions[].Documents[].DocumentData`, but only on a **savable** transaction (a bare reprint errors with *"Save is not enabled"*), and `print_pick_ticket` emits only at the order's **make location** — if components stock elsewhere, generate with `m_picktickets` at the stock `location_id` instead.
- **An empty array is not success.** A sales-order run whose criteria match nothing printable returns HTTP 200 with `[]` and creates no ticket — see [Eligibility traps](#eligibility-traps).
- **Success is a JSON array** (even for one document); **errors use the P21 error envelope** (`ErrorType`/`ErrorMessage`), not the `Summary`/`Messages` format of `/transaction` — e.g. *"No records to print for this range."* when the range matches nothing.

## Verify

- The saved file opens as a PDF (`DocumentContentType` is `"application/pdf"`, `DocumentFormat` is `5`, and the decoded bytes start with `%PDF`).
- `ResponseStatus.StatusCode` is `"Success"` and `ResponseStatus.Message` reports the form request completed.
- For `m_picktickets`: read the production order's tickets over OData — `GET /odataservice/odata/table/prod_pick_ticket_hdr?$filter=prod_order_number eq 1000123` — before and after the run; the new `prod_pick_ticket_number` (status `702`, Open) is the record the report created. **The number in `FileName` (`"PPT<nnn> PRODUCTION_PICK_TICKET.pdf"`) is not the ticket number**: on play 26.1.5950.0 it was a document counter shared with other report runs (a PO reprint's `PO<nnn>` came from the same sequence), while the ticket itself was numbered separately. `POST /transaction/get` on `ProductionOrderPicking` returned blank values for a real ticket, and an `m_reprintpicktickets` run on a production ticket succeeded once (`pick_ticket_type = Both`, blank sales-ticket range) and returned an empty HTTP 500 on every other attempt, including two repeats of that same payload, so neither is a reliable read-back.

Python and C# examples (`generate_pick_ticket_pdf.py`, `GeneratePickTicketPdf.cs`) run on play 26.1.5950.0, 2026-10-10, each against its own throwaway production order (form printed, no pick ticket yet): each saved the PDF and found exactly one new ticket at status `702` over OData.

> **Credit:** [Alex Westemeier](https://github.com/AWestemeier) — worked example verified end-to-end (report run → pick ticket row created → PDF returned → ticket confirmed and completed). Jeff Poss discovered the `/api/v2/process/pdfreport` endpoint.

## Sales-order pick ticket

`m_picktickets` also generates **sales-order** pick tickets: the batch, criteria-driven path of the client's *Pick Ticket* window. It creates the `oe_pick_ticket` row and returns the PDF in one call, like the production-order case above, but the payload differs in two ways that matter: it takes **labels** with `UseCodeValues: false`, and it needs **every date range sent explicitly**. For one order you already have open in a transaction, the per-order alternative is the `Order` service's `print_tix` flag — see [sales-order-to-invoice, step 2](sales-order-to-invoice.md#step-2-print-the-pick-ticket-verified-run-on-play-26159500-2026-10-10).

Verified on play 26.1.5950.0, 2026-10-17.

### Sales-order payload

```json
POST {ui_server}/api/v2/process/pdfreport

{
  "Name": "m_picktickets",
  "UseCodeValues": false,
  "Transactions": [{
    "Status": "New",
    "DataElements": [{
      "Keys": [],
      "Type": "Form",
      "Name": "TABPAGE_1.tp_1_dw_1",
      "Rows": [{ "Edits": [
        { "Name": "company_id",              "Value": "ACME" },
        { "Name": "create_pick_ticket_type", "Value": "Sales Order" },
        { "Name": "order_no",                "Value": "1001234" },
        { "Name": "order_number",            "Value": "1001234" },
        { "Name": "location_id",             "Value": "10" },
        { "Name": "dt_beg_date2",            "Value": "1900-01-01T00:00:00" },
        { "Name": "dt_end_date2",            "Value": "2099-12-31T23:59:59" },
        { "Name": "beg_order_date",          "Value": "1900-01-01T00:00:00" },
        { "Name": "end_order_date",          "Value": "2099-12-31T23:59:59" },
        { "Name": "beg_pick_date",           "Value": "1900-01-01T00:00:00" },
        { "Name": "end_pick_date",           "Value": "2099-12-31T23:59:59" },
        { "Name": "print_qty",               "Value": "1" }
      ] }]
    }]
  }]
}
```

- `order_no` and `order_number` are the *from* and *to* of the order range; send the same order in both.
- `dt_beg_date2`/`dt_end_date2` is the **Sales Order Required Date** range, `beg_order_date`/`end_order_date` the **Order Date** range and `beg_pick_date`/`end_pick_date` the **Pick Date** range. Send all three — see [the date-range trap](#an-omitted-date-range-takes-a-default-that-can-end-in-the-past).
- **`UseCodeValues: false` with the label `Sales Order`.** `UseCodeValues: true` with the code `S` or `O` returned an empty HTTP 500. That is the opposite of the production-order case, which needs `true` and the code `P`.
- The response is one document: a base64 PDF whose `FileName` is `PT<nnn> PICK_TICKET.pdf`. `<nnn>` is a document counter, **not** the pick-ticket number; read the ticket number from `oe_pick_ticket` by `order_no`.
- `process_doclinks` (*Transmit Document Links*) is accepted, but linked documents are not added to the returned PDF — see [item-document-links § Gotchas](item-document-links.md#gotchas-verified-on-play-26159500-2026-10-17).

### Eligibility traps

Both traps return **HTTP 200 with an empty array `[]`** — no document, no error message and no ticket. Treat an empty array as "nothing matched", not as success, and do not retry it.

#### An omitted date range takes a default that can end in the past

Any criterion you leave out takes the server's value from `GET /api/v2/defaults/m_picktickets`. On play, all three date ranges in those defaults ended on the same fixed date, one week **before** the day of the test (the order-date range covered that one day only), so an order entered on the day of the test fell outside them and was silently excluded. The defaults did not move with the current date. Sending only the pick-date range was not enough; the ticket generated only when the required-date, order-date and pick-date ranges were all sent wide. Read the defaults on your tenant if you want to know what an omitted field becomes, but send every date range yourself rather than depend on them.

#### A kit or assembly that cannot fully allocate skips the whole order

When a kit or assembly parent line cannot fully allocate — in the test, a component was cancelled for lack of stock, and the assembly has `print_incomplete_assemblies` = `N` — the run skips the **entire order**, not just that line. The client's own *Pick Ticket* window gives the same answer for that order: *"No records exist to print for this range."* Setting *Release Partials* (`delete_flag` `ON`) on the order did not change it. A kit with every component allocated generated a ticket normally.

Before you blame the payload, check the order the way the client would: allocated quantity at `location_id` that is not already on a ticket (`oe_line.qty_allocated`, `oe_line.qty_on_pick_tickets`), and every kit component allocated. An order whose allocated quantity is already on a ticket also returns `[]`; running the examples below a second time on the same order created no second ticket.

### Complete example: sales order

Takes the order number and location as arguments (`python so_pick_ticket.py 1001234 10`, `dotnet run -- 1001234 10`), generates the ticket, saves the PDF to `OUTPUT_DIR`, and reads the new `oe_pick_ticket` row back over OData by comparing the order's tickets before and after the run. An empty array stops with the eligibility checklist above. The programs retry an empty 5xx like the production example, but here the retry is **not** free of side effects: `m_picktickets` creates the ticket, so a 5xx after the ticket was created makes the retry return `[]`. That is why both programs read `oe_pick_ticket` before they treat an empty array as "nothing matched", and why an HTTP error after the last attempt tells you to check `oe_pick_ticket` before you rerun. If a ticket exists without a PDF, reprint it with `m_reprintpicktickets`.

<!-- tabs -->
```python
"""Generate a sales-order pick ticket with m_picktickets, save the PDF, read the ticket back.

Usage: python so_pick_ticket.py [ORDER_NO] [LOCATION_ID]
"""
import base64
import os
import re
import sys
import time

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.example.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
COMPANY_ID = "ACME"                       # company the order belongs to
ORDER_NO = "1001234"                      # sales order number (argument 1 overrides)
LOCATION_ID = "10"                        # location to pick from (argument 2 overrides)
DATE_FROM = "1900-01-01T00:00:00"         # every date range is sent this wide --
DATE_TO = "2099-12-31T23:59:59"           # the server defaults can end in the past
OUTPUT_DIR = "."                          # where the .pdf file is written
# ---------------------------------------------------------------------------

if len(sys.argv) > 1:
    ORDER_NO = sys.argv[1]
if len(sys.argv) > 2:
    LOCATION_ID = sys.argv[2]
if not (ORDER_NO.isdigit() and LOCATION_ID.isdigit()):  # both go into an OData filter
    raise SystemExit("ORDER_NO and LOCATION_ID must be numbers")


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


def run_report(client: httpx.Client, ui_server: str, headers: dict,
               payload: dict, attempts: int = 3) -> list:
    """POST a report payload and return its document array (possibly empty).

    Retries an empty 5xx, which the report engine emits now and then and which
    clears on the next try. This retry is not free of side effects here:
    m_picktickets creates the ticket, so a 5xx after the ticket was created
    makes the retry return [] -- the caller reads oe_pick_ticket before it
    reports a failure. Do not retry an empty array itself: it is a
    deterministic "nothing matched" (see the eligibility traps).
    """
    for attempt in range(1, attempts + 1):
        response = client.post(f"{ui_server}/api/v2/process/pdfreport",
                               headers=headers, json=payload)
        # Parse the body BEFORE looking at the status code: the ErrorType /
        # ErrorMessage envelope can arrive on a 200 as well as a 4xx/5xx.
        try:
            result = response.json()
        except ValueError:
            result = None
        if isinstance(result, dict) and result.get("ErrorMessage"):
            raise SystemExit(f"{result.get('ErrorType')}: {result['ErrorMessage']}")
        if response.status_code < 500:  # only a 5xx is worth retrying
            break
        if attempt < attempts:
            time.sleep(0.5 * attempt)
    if response.status_code >= 400:
        hint = (" -- an attempt may still have created the ticket; check oe_pick_ticket "
                "before rerunning." if response.status_code >= 500 else "")
        raise SystemExit(f"HTTP {response.status_code} after {attempt} attempt(s). "
                         f"Body: {(response.text or '(empty)')[:300]}{hint}")
    if not isinstance(result, list):
        raise SystemExit(f"Unexpected response: {str(result)[:300]}")
    return result


def save_documents(result: list) -> int:
    """Write every returned base64 document to OUTPUT_DIR; return how many were saved."""
    saved = 0
    for doc in result:
        response_status = doc.get("ResponseStatus") or {}
        if response_status.get("StatusCode") != "Success" or not doc.get("DocumentData"):
            print(f"Document failed: {response_status.get('Message') or doc}")
            continue
        pdf_bytes = base64.b64decode(doc["DocumentData"])
        # FileName is like "PT<nnn> PICK_TICKET.pdf"; <nnn> is a document
        # counter, not the pick-ticket number
        name = os.path.basename(doc.get("FileName") or f"pick_ticket_{ORDER_NO}.pdf")
        path = os.path.join(OUTPUT_DIR, name)
        with open(path, "wb") as f:
            f.write(pdf_bytes)
        print(f"Saved {path} ({len(pdf_bytes)} bytes, starts with {pdf_bytes[:4]!r})")
        saved += 1
    return saved


with httpx.Client(verify=VERIFY_SSL, timeout=300, follow_redirects=True) as client:
    token = get_token(client)
    ui_server = get_ui_server(client, token)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",       # without this you get XML, not JSON
        "Content-Type": "application/json",
    }

    def read_tickets() -> dict:
        """The order's pick tickets, read over OData, keyed by ticket number."""
        r = client.get(
            f"{BASE_URL}/odataservice/odata/table/oe_pick_ticket",
            params={"$filter": f"order_no eq '{ORDER_NO}'",
                    "$select": "pick_ticket_no,order_no,location_id,print_date"},
            headers=headers,
        )
        r.raise_for_status()
        return {row["pick_ticket_no"]: row for row in r.json()["value"]}

    payload = {
        "Name": "m_picktickets",
        "UseCodeValues": False,  # labels; true with "S" or "O" is an empty 500
        "Transactions": [{
            "Status": "New",
            "DataElements": [{
                "Keys": [],      # always empty for reports
                "Type": "Form",
                "Name": "TABPAGE_1.tp_1_dw_1",
                "Rows": [{"Edits": [
                    {"Name": "company_id", "Value": COMPANY_ID},
                    {"Name": "create_pick_ticket_type", "Value": "Sales Order"},
                    # order range: from and to are the same order
                    {"Name": "order_no", "Value": ORDER_NO},
                    {"Name": "order_number", "Value": ORDER_NO},
                    {"Name": "location_id", "Value": LOCATION_ID},
                    # All three date ranges, sent wide. Any range you omit takes
                    # the server default, which can end on a past date and drop
                    # current orders: HTTP 200, empty array, no ticket.
                    {"Name": "dt_beg_date2", "Value": DATE_FROM},    # SO required date
                    {"Name": "dt_end_date2", "Value": DATE_TO},
                    {"Name": "beg_order_date", "Value": DATE_FROM},
                    {"Name": "end_order_date", "Value": DATE_TO},
                    {"Name": "beg_pick_date", "Value": DATE_FROM},
                    {"Name": "end_pick_date", "Value": DATE_TO},
                    {"Name": "print_qty", "Value": "1"},
                ]}],
            }],
        }],
    }

    before = read_tickets()
    documents = run_report(client, ui_server, headers, payload)
    saved = save_documents(documents)

    # --- Read-back: m_picktickets CREATED an oe_pick_ticket row. ---
    # Read it even when no document came back: a retried 5xx can leave a ticket
    # created by the first attempt and an empty array from the retry.
    after = read_tickets()
    new = [after[n] for n in sorted(set(after) - set(before))]
    if not new and documents:
        raise SystemExit(f"{len(documents)} document(s) returned but no new "
                         f"oe_pick_ticket row on order {ORDER_NO}")
    if not new:
        # HTTP 200 with [] means the criteria matched nothing printable.
        raise SystemExit(
            f"No pick ticket generated for order {ORDER_NO} at location {LOCATION_ID}. "
            "Check: the order has allocated quantity at that location not already on a "
            "ticket; every kit/assembly parent line can fully allocate; the order and "
            "required dates fall inside the date ranges sent.")
    for ticket in new:
        print(f"New pick ticket {ticket['pick_ticket_no']} on order {ticket['order_no']} "
              f"at location {ticket['location_id']}, printed {ticket['print_date']}")
    if saved == 0:
        raise SystemExit("The ticket exists but no PDF was saved; "
                         "reprint it with m_reprintpicktickets.")
```

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

// Usage: dotnet run -- [ORDER_NO] [LOCATION_ID]

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.example.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string CompanyId = "ACME";                // company the order belongs to
const string DefaultOrderNo = "1001234";        // sales order number (argument 1 overrides)
const string DefaultLocationId = "10";          // location to pick from (argument 2 overrides)
const string DateFrom = "1900-01-01T00:00:00";  // every date range is sent this wide --
const string DateTo = "2099-12-31T23:59:59";    // the server defaults can end in the past
const string OutputDir = ".";                   // where the .pdf file is written
// ---------------------------------------------------------------------------

var orderNo = args.Length > 0 ? args[0] : DefaultOrderNo;
var locationId = args.Length > 1 ? args[1] : DefaultLocationId;
// Both go into an OData filter, so accept digits only.
if (orderNo.Length == 0 || !orderNo.All(char.IsAsciiDigit) ||
    locationId.Length == 0 || !locationId.All(char.IsAsciiDigit))
    throw new ArgumentException("Order number and location ID must be numbers");

var handler = new HttpClientHandler
{
    // Test tenants often present a self-signed cert. Delete this line in production.
    ServerCertificateCustomValidationCallback =
        HttpClientHandler.DangerousAcceptAnyServerCertificateValidator,
};
using var client = new HttpClient(handler) { Timeout = TimeSpan.FromMinutes(5) };
client.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));

var token = await GetTokenAsync(client);
var uiServer = await GetUiServerAsync(client, token);
client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);

var payload = new
{
    Name = "m_picktickets",
    UseCodeValues = false,   // labels; true with "S" or "O" is an empty 500
    Transactions = new object[]
    {
        new
        {
            Status = "New",
            DataElements = new object[]
            {
                new
                {
                    Keys = Array.Empty<string>(),   // always empty for reports
                    Type = "Form",
                    Name = "TABPAGE_1.tp_1_dw_1",
                    Rows = new object[]
                    {
                        new
                        {
                            Edits = new[]
                            {
                                new { Name = "company_id", Value = CompanyId },
                                new { Name = "create_pick_ticket_type", Value = "Sales Order" },
                                // order range: from and to are the same order
                                new { Name = "order_no", Value = orderNo },
                                new { Name = "order_number", Value = orderNo },
                                new { Name = "location_id", Value = locationId },
                                // All three date ranges, sent wide. Any range you omit
                                // takes the server default, which can end on a past date
                                // and drop current orders: HTTP 200, empty array, no ticket.
                                new { Name = "dt_beg_date2", Value = DateFrom },   // SO required date
                                new { Name = "dt_end_date2", Value = DateTo },
                                new { Name = "beg_order_date", Value = DateFrom },
                                new { Name = "end_order_date", Value = DateTo },
                                new { Name = "beg_pick_date", Value = DateFrom },
                                new { Name = "end_pick_date", Value = DateTo },
                                new { Name = "print_qty", Value = "1" },
                            },
                        },
                    },
                },
            },
        },
    },
};

var before = await ReadTicketsAsync(client, orderNo);
var documents = await RunReportAsync(client, uiServer, payload);
var saved = SaveDocuments(documents, orderNo);

// --- Read-back: m_picktickets CREATED an oe_pick_ticket row. ---
// Read it even when no document came back: a retried 5xx can leave a ticket
// created by the first attempt and an empty array from the retry.
var after = await ReadTicketsAsync(client, orderNo);
var created = after.Keys.Except(before.Keys).OrderBy(n => n).ToList();
if (created.Count == 0 && documents.Count > 0)
{
    throw new InvalidOperationException(
        $"{documents.Count} document(s) returned but no new oe_pick_ticket row on order {orderNo}");
}
if (created.Count == 0)
{
    // HTTP 200 with [] means the criteria matched nothing printable.
    throw new InvalidOperationException(
        $"No pick ticket generated for order {orderNo} at location {locationId}. Check: the " +
        "order has allocated quantity at that location not already on a ticket; every " +
        "kit/assembly parent line can fully allocate; the order and required dates fall " +
        "inside the date ranges sent.");
}
foreach (var number in created)
{
    var ticket = after[number];
    Console.WriteLine($"New pick ticket {number} on order {ticket.GetProperty("order_no")} " +
                      $"at location {ticket.GetProperty("location_id")}, " +
                      $"printed {ticket.GetProperty("print_date")}");
}
if (saved == 0)
{
    throw new InvalidOperationException(
        "The ticket exists but no PDF was saved; reprint it with m_reprintpicktickets.");
}

// --- helpers ---------------------------------------------------------------

// The order's pick tickets, read over OData, keyed by ticket number.
static async Task<Dictionary<long, JsonElement>> ReadTicketsAsync(HttpClient client, string orderNo)
{
    var filter = Uri.EscapeDataString($"order_no eq '{orderNo}'");
    using var response = await client.GetAsync(
        $"{BaseUrl}/odataservice/odata/table/oe_pick_ticket?$filter={filter}" +
        "&$select=pick_ticket_no,order_no,location_id,print_date");
    response.EnsureSuccessStatusCode();
    using var doc = JsonDocument.Parse(await response.Content.ReadAsStringAsync());
    return doc.RootElement.GetProperty("value").EnumerateArray().ToDictionary(
        row => row.GetProperty("pick_ticket_no").GetInt64(), row => row.Clone());
}

// POST a report payload and return its document array (possibly empty).
// Retries an empty 5xx, which the report engine emits now and then and which
// clears on the next try. This retry is not free of side effects here:
// m_picktickets creates the ticket, so a 5xx after the ticket was created
// makes the retry return [] -- the caller reads oe_pick_ticket before it
// reports a failure. Do not retry an empty array itself: it is a
// deterministic "nothing matched" (see the eligibility traps).
static async Task<List<JsonElement>> RunReportAsync(
    HttpClient client, string uiServer, object payload, int attempts = 3)
{
    var body = JsonSerializer.Serialize(payload);
    for (var attempt = 1; ; attempt++)
    {
        using var response = await client.PostAsync(
            $"{uiServer}/api/v2/process/pdfreport",
            new StringContent(body, Encoding.UTF8, "application/json"));
        var bodyText = await response.Content.ReadAsStringAsync();

        // Parse the body BEFORE looking at the status code: the ErrorType /
        // ErrorMessage envelope can arrive on a 200 as well as a 4xx/5xx.
        JsonDocument? parsed = null;
        try { parsed = JsonDocument.Parse(bodyText); }
        catch (JsonException) { /* empty or non-JSON body */ }

        using (parsed)
        {
            var root = parsed?.RootElement;
            if (root is { ValueKind: JsonValueKind.Object } obj &&
                obj.TryGetProperty("ErrorMessage", out var err))
            {
                throw new InvalidOperationException($"{obj.GetProperty("ErrorType")}: {err}");
            }

            if (response.IsSuccessStatusCode)
            {
                if (root is not { ValueKind: JsonValueKind.Array } arr)
                    throw new InvalidOperationException($"Unexpected response: {bodyText}");
                return arr.EnumerateArray().Select(x => x.Clone()).ToList();
            }

            // Only a 5xx is worth retrying.
            if ((int)response.StatusCode < 500 || attempt >= attempts)
            {
                var hint = (int)response.StatusCode >= 500
                    ? " -- an attempt may still have created the ticket; check oe_pick_ticket before rerunning."
                    : "";
                throw new InvalidOperationException(
                    $"HTTP {(int)response.StatusCode} after {attempt} attempt(s). " +
                    $"Body: {(string.IsNullOrEmpty(bodyText) ? "(empty)" : bodyText)}{hint}");
            }
        }
        await Task.Delay(TimeSpan.FromSeconds(0.5 * attempt));
    }
}

// Write every returned base64 document to OutputDir; return how many were saved.
static int SaveDocuments(List<JsonElement> documents, string orderNo)
{
    var saved = 0;
    foreach (var doc in documents)
    {
        var hasStatus = doc.TryGetProperty("ResponseStatus", out var responseStatus) &&
                        responseStatus.ValueKind == JsonValueKind.Object;
        var status = hasStatus && responseStatus.TryGetProperty("StatusCode", out var s)
            ? s.GetString() : null;
        var documentData = doc.TryGetProperty("DocumentData", out var d) ? d.GetString() : null;
        if (status != "Success" || string.IsNullOrEmpty(documentData))
        {
            Console.WriteLine($"Document failed: {(hasStatus ? responseStatus.ToString() : doc.ToString())}");
            continue;
        }
        var pdfBytes = Convert.FromBase64String(documentData);
        // FileName is like "PT<nnn> PICK_TICKET.pdf"; <nnn> is a document
        // counter, not the pick-ticket number
        var filename = doc.TryGetProperty("FileName", out var f) && !string.IsNullOrEmpty(f.GetString())
            ? f.GetString()! : $"pick_ticket_{orderNo}.pdf";
        var path = Path.Combine(OutputDir, Path.GetFileName(filename));
        File.WriteAllBytes(path, pdfBytes);
        Console.WriteLine($"Saved {path} ({pdfBytes.Length} bytes, starts with " +
                          $"{Encoding.ASCII.GetString(pdfBytes, 0, 4)})");
        saved++;
    }
    return saved;
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

### Verify a sales-order ticket

- The saved file starts with `%PDF` and is the ticket for the requested order.
- `GET /odataservice/odata/table/oe_pick_ticket?$filter=order_no eq '1001234'&$select=pick_ticket_no,location_id,print_date` shows one more row than before the run, at `location_id`.

Python and C# examples run on play 26.1.5950.0, 2026-10-17, each against its own new single-line order for a stocked item at one location: each saved a one-page PDF of that order and found exactly one new `oe_pick_ticket` row at that location. A second Python run on the same order returned `[]` and created nothing.
