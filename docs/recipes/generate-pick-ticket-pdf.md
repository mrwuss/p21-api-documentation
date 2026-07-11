# Generate Pick Ticket and PO PDFs

Generate or reprint pick tickets and purchase orders as base64-encoded PDFs via the dedicated report endpoint.

**API:** Transaction (`POST /api/v2/process/pdfreport`) · **Service:** `m_picktickets`, `m_reprintpicktickets`, `m_reprintpurchaseorders` · **Deep dive:** [PDF Report Generation](../03-Transaction-API.md#pdf-report-generation) · **Full schema:** [m_picktickets.json](../../definitions/m_picktickets.json) · [m_reprintpicktickets.json](../../definitions/m_reprintpicktickets.json) · [m_reprintpurchaseorders.json](../../definitions/m_reprintpurchaseorders.json)

## Prerequisites

- Token + UI server URL (shared auth helper — see the [recipes README](README.md)).
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

**`m_reprintpicktickets`** — pick-ticket reprint. DataElement name is `TABPAGE_1.tp_1_dw_1` (datawindow `d_reprint_pick_ticket_criteria`); the [definition](../../definitions/m_reprintpicktickets.json) marks `company_id`, `location_id`, and `print_qty` required, with ranges `beg_pick_ticket_no`/`end_pick_ticket_no` (sales-order tickets) and `beg_prod_pick_ticket_no`/`end_prod_pick_ticket_no` (production tickets).

For any *other* report, swap `Name` and the criteria `Edits` (field names from `GET /api/v2/definition/{name}`); the endpoint, `Status`/`Type: 0`, `Keys: []`, and the `DocumentData` extraction stay the same.

## Complete example

Generates a production-order pick ticket with `m_picktickets`, decodes the base64 PDF, and handles both failure shapes (document-level `ResponseStatus` and the P21 error envelope).

<!-- tabs -->
```python
import base64

import httpx  # p21_auth() from recipes/README.md

BASE_URL = "https://play.p21server.com"
USERNAME = "api_user"
PASSWORD = "api_pass"

token, ui_server, headers = p21_auth(BASE_URL, USERNAME, PASSWORD)

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
                {"Name": "beg_prod_order", "Value": "1000123"},
                {"Name": "end_prod_order", "Value": "1000123"},
                # location whose inventory the components pick from
                {"Name": "location_id", "Value": "10"},
            ]}],
        }],
    }],
}

response = httpx.post(
    f"{ui_server}/api/v2/process/pdfreport",
    headers=headers, json=payload, verify=False, timeout=120,
)

# Errors come back as the standard P21 error envelope (ErrorType/ErrorMessage),
# NOT the Summary/Messages format used by /transaction.
if response.status_code >= 400:
    raise SystemExit(f"HTTP {response.status_code}: {response.text}")
result = response.json()
if isinstance(result, dict) and "ErrorMessage" in result:
    raise SystemExit(f"{result.get('ErrorType')}: {result['ErrorMessage']}")

# Success is a JSON ARRAY -- even for a single document
if not (isinstance(result, list) and result):
    raise SystemExit(f"No documents returned: {result}")

for doc in result:
    status = doc.get("ResponseStatus", {}).get("StatusCode")
    if status != "Success" or not doc.get("DocumentData"):
        msg = doc.get("ResponseStatus", {}).get("Message", "Unknown error")
        print(f"Document failed: {msg}")
        continue
    pdf_bytes = base64.b64decode(doc["DocumentData"])
    # FileName includes .pdf, e.g. "PPT<nnn> PRODUCTION_PICK_TICKET.pdf"
    filename = doc.get("FileName", "pick_ticket.pdf")
    with open(filename, "wb") as f:
        f.write(pdf_bytes)
    print(f"Saved {filename} ({len(pdf_bytes)} bytes)")
```

```csharp
var session = await P21Session.CreateAsync(
    "https://play.p21server.com", "api_user", "api_pass");

var payload = new JObject
{
    ["Name"] = "m_picktickets",
    ["UseCodeValues"] = true,   // required here -- false returns HTTP 500
    ["Transactions"] = new JArray
    {
        new JObject
        {
            ["Status"] = 0,     // numeric 0 for report payloads
            ["DataElements"] = new JArray
            {
                new JObject
                {
                    ["Keys"] = new JArray(),  // always empty for reports
                    ["Type"] = 0,             // numeric 0 for report payloads
                    ["Name"] = "TABPAGE_1.tp_1_dw_1",
                    ["Rows"] = new JArray
                    {
                        new JObject
                        {
                            ["Edits"] = new JArray
                            {
                                // code "P" = Production Order (label is rejected)
                                new JObject { ["Name"] = "create_pick_ticket_type", ["Value"] = "P" },
                                new JObject { ["Name"] = "beg_prod_order", ["Value"] = "1000123" },
                                new JObject { ["Name"] = "end_prod_order", ["Value"] = "1000123" },
                                // location whose inventory the components pick from
                                new JObject { ["Name"] = "location_id", ["Value"] = "10" },
                            }
                        }
                    }
                }
            }
        }
    }
};

var response = await session.Http.PostAsync(
    $"{session.UiServer}/api/v2/process/pdfreport",
    new StringContent(payload.ToString(), Encoding.UTF8, "application/json"));
var bodyText = await response.Content.ReadAsStringAsync();

// Errors come back as the standard P21 error envelope (ErrorType/ErrorMessage),
// NOT the Summary/Messages format used by /transaction.
if (!response.IsSuccessStatusCode)
    throw new InvalidOperationException($"HTTP {(int)response.StatusCode}: {bodyText}");

var parsed = JToken.Parse(bodyText);
if (parsed is JObject envelope && envelope["ErrorMessage"] != null)
    throw new InvalidOperationException(
        $"{envelope["ErrorType"]}: {envelope["ErrorMessage"]}");

// Success is a JSON ARRAY -- even for a single document
if (parsed is not JArray documents || documents.Count == 0)
    throw new InvalidOperationException($"No documents returned: {parsed}");

foreach (var doc in documents.OfType<JObject>())
{
    var status = doc["ResponseStatus"]?["StatusCode"]?.ToString();
    var documentData = doc["DocumentData"]?.ToString();
    if (status != "Success" || string.IsNullOrEmpty(documentData))
    {
        var msg = doc["ResponseStatus"]?["Message"]?.ToString() ?? "Unknown error";
        Console.WriteLine($"Document failed: {msg}");
        continue;
    }
    var pdfBytes = Convert.FromBase64String(documentData);
    // FileName includes .pdf, e.g. "PPT<nnn> PRODUCTION_PICK_TICKET.pdf"
    var filename = doc["FileName"]?.ToString() ?? "pick_ticket.pdf";
    await File.WriteAllBytesAsync(filename, pdfBytes);
    Console.WriteLine($"Saved {filename} ({pdfBytes.Length} bytes)");
}
```
<!-- /tabs -->

> **Payload files:** [JSON](../../examples/payloads/json/generate-pick-ticket-pdf.json) · [reprint JSON](../../examples/payloads/json/reprint-purchase-order-pdf.json) (XML untested for the pdfreport endpoint) — validator-verified, see [payloads README](../../examples/payloads/README.md).
>
> **End-to-end files** (runnable from the repo with a `.env`, dry-run by default): [`examples/python/recipes/generate_pick_ticket_pdf.py`](../../examples/python/recipes/generate_pick_ticket_pdf.py) · [`examples/csharp/Recipes/GeneratePickTicketPdf.cs`](../../examples/csharp/Recipes/GeneratePickTicketPdf.cs). The snippet above is self-contained; the files use the repo's shared `common` / `P21Examples.Common` helpers like every other example.

## Gotchas

All verified live — details in [PDF Report Generation](../03-Transaction-API.md#pdf-report-generation):

- **Wrong-endpoint trap** — `POST /api/v2/transaction` *accepts* an `m_*` payload and returns `Succeeded`, but **emits nothing**. Reports must go to `POST /api/v2/process/pdfreport`. ("This was the single biggest gotcha.")
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
