# Generate Pick Ticket and PO PDFs

Generate or reprint pick tickets and purchase orders as base64-encoded PDFs via the dedicated report endpoint.

**API:** Transaction (`POST /api/v2/process/pdfreport`) · **Service:** `m_picktickets`, `m_reprintpicktickets`, `m_reprintpurchaseorders` · **Deep dive:** [PDF Report Generation](../03-Transaction-API.md#pdf-report-generation) · **Full schema:** [m_picktickets.json](../../definitions/m_picktickets.json) · [m_reprintpicktickets.json](../../definitions/m_reprintpicktickets.json) · [m_reprintpurchaseorders.json](../../definitions/m_reprintpurchaseorders.json)

## Prerequisites

- P21 credentials — the complete example below authenticates itself; nothing to install but `httpx` (Python) or a bare `net9.0` console project (C#).
- **For `m_picktickets` against a production order**: the production order's form must already be printed (`prod_order_hdr.printed = 'Y'`) — run a `ProductionOrder` transaction with `print_form = ON` first.
- The `m_*` report services are **hidden from `GET /api/v2/services`** (`?type=report` returns an empty list), but `GET /api/v2/definition/{service_name}` and `GET /api/v2/defaults/{service_name}` both work for them — use those for criteria field names and defaults. On a 25.2 test system, probing candidates from the `window_x_menu` table yields ~157 callable report services (`m_picktickets`, `m_reprintpicktickets`, `m_productionorders`, `m_orderacknowledgements`, `m_invoices`, `m_packinglists`, `m_customerstatements`, …) — see the Discovery note in the [deep dive](../03-Transaction-API.md#pdf-report-generation).

> **Wrong-endpoint trap:** `POST /api/v2/transaction` *accepts* an `m_*` report payload and returns `Succeeded` — but **emits nothing**. A report is a process, not a record edit; it must go to `POST /api/v2/process/pdfreport`.

## Payload

Constants for **every** report payload: `Status` and `Type` are **numeric `0`** (not the `"New"` record-edit shape) and the DataElement carries `Keys: []`. Only `Name`, the DataElement name, and the criteria `Edits` change per service.

**`m_picktickets`** — *creates* the pick-ticket record at `location_id` **and** returns its PDF in one call (verified worked example). Requires `UseCodeValues: true` with the code `"P"` (Production Order):

```json
POST {ui_server}/api/v2/process/pdfreport

{
  "Name": "m_picktickets",
  "UseCodeValues": true,
  "Transactions": [{
    "Status": 0,
    "DataElements": [{
      "Keys": [],
      "Type": 0,
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

**`m_reprintpurchaseorders`** — PO reprint (verified with `UseCodeValues: false`). DataElement name is `TABPAGE_1.poreportcriteriadw`:

```json
{ "Name": "company_id", "Value": "ACME" },
{ "Name": "beg_po_no",  "Value": "500100" },
{ "Name": "end_po_no",  "Value": "500100" },
{ "Name": "reprint_flag", "Value": "Y" }
```

**`m_reprintpicktickets`** — pick-ticket reprint. DataElement name is `TABPAGE_1.tp_1_dw_1` (datawindow `d_reprint_pick_ticket_criteria`); the [definition](../../definitions/m_reprintpicktickets.json) marks `company_id`, `location_id`, and `print_qty` required, with ranges `beg_pick_ticket_no`/`end_pick_ticket_no` (sales-order tickets) and `beg_prod_pick_ticket_no`/`end_prod_pick_ticket_no` (production tickets). Its `pick_ticket_type` takes the display values `Sales Order`, `Production Order` or `Both`, and `print_dea_pick_tickets` takes `Yes`, `No` or `Only` (from the live definition, 2026-08-11).

> **`UseCodeValues` for this service is unconfirmed.** It could not be settled on the Play tenant, where *every* report returns an empty HTTP 500 — including `m_reprintpurchaseorders`, which runs at production volume elsewhere. If you hit an error here, try `UseCodeValues: true` with code values from the definition; and read [An empty 5xx has several causes](../03-Transaction-API.md#an-empty-5xx-has-several-causes-and-is-usually-transient) first, because a 5xx here is most often a transient report-engine fault that a retry clears, not a payload problem.

For any *other* report, swap `Name` and the criteria `Edits` (field names from `GET /api/v2/definition/{name}`); the endpoint, `Status`/`Type: 0`, `Keys: []`, and the `DocumentData` extraction stay the same.

## Complete example

Generates a production-order pick ticket with `m_picktickets`, decodes the base64 PDF to `OUTPUT_DIR`, and handles both failure shapes (document-level `ResponseStatus` and the P21 error envelope). Because `m_picktickets` also **creates** the ticket row, the program finishes with the read-back from the Verify section: a `m_reprintpicktickets` run on the new ticket number, whose second PDF proves the record landed.

<!-- tabs -->
```python
"""Generate a production-order pick ticket PDF, save it, and re-read it back."""
import base64
import os
import re
import time

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
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
        # FileName includes .pdf, e.g. "PPT<nnn> PRODUCTION_PICK_TICKET.pdf"
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
        "Accept": "application/json",       # 2026.1 returns an empty 500 without this
        "Content-Type": "application/json",
    }

    payload = {
        "Name": "m_picktickets",
        "UseCodeValues": True,   # required here -- False returns HTTP 500
        "Transactions": [{
            "Status": 0,         # numeric 0 for report payloads
            "DataElements": [{
                "Keys": [],      # always empty for reports
                "Type": 0,       # numeric 0 for report payloads
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
    saved = save_documents(run_report(client, ui_server, headers, payload),
                           "pick_ticket")

    # --- Read-back: m_picktickets CREATED a ticket row, so reprint it. ---
    # A second PDF proves the pick-ticket record exists in P21.
    for filename in saved:
        match = re.match(r"PPT(\d+)", filename)
        if not match:
            continue
        ticket_no = match.group(1)
        reprint = {
            "Name": "m_reprintpicktickets",
            # if this errors on correct criteria, retry with True + code values
            "UseCodeValues": False,
            "Transactions": [{
                "Status": 0,
                "DataElements": [{
                    "Keys": [],
                    "Type": 0,
                    "Name": "TABPAGE_1.tp_1_dw_1",
                    "Rows": [{"Edits": [
                        {"Name": "company_id", "Value": "ACME"},
                        {"Name": "location_id", "Value": LOCATION_ID},
                        {"Name": "print_qty", "Value": "1"},
                        {"Name": "beg_prod_pick_ticket_no", "Value": ticket_no},
                        {"Name": "end_prod_pick_ticket_no", "Value": ticket_no},
                    ]}],
                }],
            }],
        }
        print(f"Reprinting ticket {ticket_no} to prove the record landed:")
        save_documents(run_report(client, ui_server, headers, reprint),
                       f"reprint_{ticket_no}")
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
            Status = 0,     // numeric 0 for report payloads
            DataElements = new object[]
            {
                new
                {
                    Keys = Array.Empty<string>(),   // always empty for reports
                    Type = 0,                       // numeric 0 for report payloads
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

var saved = SaveDocuments(await RunReportAsync(client, uiServer, payload), "pick_ticket");

// --- Read-back: m_picktickets CREATED a ticket row, so reprint it. ---
// A second PDF proves the pick-ticket record exists in P21.
foreach (var filename in saved)
{
    var match = System.Text.RegularExpressions.Regex.Match(filename, @"^PPT(\d+)");
    if (!match.Success) continue;
    var ticketNo = match.Groups[1].Value;
    var reprint = new
    {
        Name = "m_reprintpicktickets",
        // if this errors on correct criteria, retry with true + code values
        UseCodeValues = false,
        Transactions = new object[]
        {
            new
            {
                Status = 0,
                DataElements = new object[]
                {
                    new
                    {
                        Keys = Array.Empty<string>(),
                        Type = 0,
                        Name = "TABPAGE_1.tp_1_dw_1",
                        Rows = new object[]
                        {
                            new
                            {
                                Edits = new[]
                                {
                                    new { Name = "company_id", Value = CompanyId },
                                    new { Name = "location_id", Value = LocationId },
                                    new { Name = "print_qty", Value = "1" },
                                    new { Name = "beg_prod_pick_ticket_no", Value = ticketNo },
                                    new { Name = "end_prod_pick_ticket_no", Value = ticketNo },
                                },
                            },
                        },
                    },
                },
            },
        },
    };
    Console.WriteLine($"Reprinting ticket {ticketNo} to prove the record landed:");
    SaveDocuments(await RunReportAsync(client, uiServer, reprint), $"reprint_{ticketNo}");
}

// --- helpers ---------------------------------------------------------------

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
        // FileName includes .pdf, e.g. "PPT<nnn> PRODUCTION_PICK_TICKET.pdf"
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
- **Retry an empty 5xx before believing it.** The report engine faults intermittently — a production integration generating PO PDFs all day logged **3 empty 500s and one dropped connection against 154 successes in a single afternoon**, and every affected PO succeeded moments later. Generating a document is an idempotent read, so retry (3 attempts, 0.5 s × attempt) as the examples above do. A *deterministic* empty 5xx is a different animal: criteria that match nothing (a wrong `company_id`), a record that isn't printable, or an environment where report generation isn't available. See [An empty 5xx has several causes](../03-Transaction-API.md#an-empty-5xx-has-several-causes-and-is-usually-transient).
- **Read the error envelope before the status code.** This endpoint returns P21's `ErrorType`/`ErrorMessage` envelope, and it can arrive on a **200** as well as a 4xx/5xx. Checking `response.status_code` first discards the one message that explains the failure — the examples above parse the body first for that reason.
- **Check the record exists first.** A missing record and a transient engine fault both surface as an unhelpful 5xx. A cheap OData read before the report call turns "not found" into your own clear error and leaves the 5xx meaning only "the engine faulted".
- **`UseCodeValues` requirements vary per report service.** `m_reprintpurchaseorders` works with `UseCodeValues: false`, but `m_picktickets` **requires `UseCodeValues: true` with code values** — `create_pick_ticket_type` must be the code `"P"`; the display label `"Production Order"` is rejected, and `UseCodeValues: false` returns HTTP 500. When a report errors on seemingly-correct criteria, retry with `UseCodeValues: true` and the code values from the definition's `ValidValues`.
- **`Status` and `Type` are numeric `0`** with `Keys: []` — not the `"New"` record-edit shape.
- **`m_picktickets` prerequisite**: the production order's form must already be printed (`prod_order_hdr.printed = 'Y'`) — run a `ProductionOrder` transaction with `print_form = ON` first. No date range is needed; `location_id` is the location the components pick from.
- **`m_picktickets` has a side effect**: the pick-ticket row now exists in P21 at that location and can be confirmed/completed like any other.
- **Print flags on `/transaction` have limits.** A service's print flags (e.g. `ProductionOrder` `print_pick_ticket`/`print_form` on `TABPAGE_1.tp_1_dw_1`) return PDFs at `Results.Transactions[].Documents[].DocumentData`, but only on a **savable** transaction (a bare reprint errors with *"Save is not enabled"*), and `print_pick_ticket` emits only at the order's **make location** — if components stock elsewhere, generate with `m_picktickets` at the stock `location_id` instead.
- **Success is a JSON array** (even for one document); **errors use the P21 error envelope** (`ErrorType`/`ErrorMessage`), not the `Summary`/`Messages` format of `/transaction` — e.g. *"No records to print for this range."* when the range matches nothing.

## Verify

- The saved file opens as a PDF (`DocumentContentType` is `"application/pdf"`, `DocumentFormat` is `5`, and the decoded bytes start with `%PDF`).
- `ResponseStatus.StatusCode` is `"Success"` and `ResponseStatus.Message` reports the form request completed.
- For `m_picktickets`: the ticket number is in `FileName` (`"PPT<nnn> PRODUCTION_PICK_TICKET.pdf"`). Confirm the record landed by reprinting it — run `m_reprintpicktickets` with `beg_prod_pick_ticket_no`/`end_prod_pick_ticket_no` set to that number; a second PDF proves the pick-ticket row exists.

> **Credit:** [Alex Westemeier](https://github.com/AWestemeier) — worked example verified end-to-end (report run → pick ticket row created → PDF returned → ticket confirmed and completed). Jeff Poss discovered the `/api/v2/process/pdfreport` endpoint.
