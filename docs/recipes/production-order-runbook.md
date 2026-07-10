# Production Order Runbook — Create to Invoice

Run a production order end-to-end: create it, log labor, print the pick ticket(s), confirm the pick, complete (receive) the order, and ship + invoice the linked sales order.

**API:** Transaction + Interactive · **Service:** `ProductionOrder`, `m_picktickets`, `TimeEntry`, `ProductionOrderPicking`, `ProductionOrderProcessing`, `Order`, `Shipping` · **Deep dive:** [Production Order Lifecycle (End-to-End)](../12-Production-Labor-API.md#production-order-lifecycle-end-to-end) · **Full schema:** [ProductionOrder](../../definitions/ProductionOrder.json), [ProductionOrderPicking](../../definitions/ProductionOrderPicking.json), [ProductionOrderProcessing](../../definitions/ProductionOrderProcessing.json), [m_picktickets](../../definitions/m_picktickets.json)

This page is a **checklist**, not a script. Each stage says what to call, the fields that matter, and the trap that costs an afternoon — with a link to the deep section. The one complete example below covers the stage most people automate first: generating the pick ticket and reading back its status. For runnable code on the other stages, see [record-labor-time](record-labor-time.md), [inventory-adjustment](inventory-adjustment.md), [order-with-assembly](order-with-assembly.md), [create-sales-order](create-sales-order.md), and [generate-pick-ticket-pdf](generate-pick-ticket-pdf.md).

## Prerequisites

- **An assembly (BOM) definition exists** for the item — you cannot create a production order for an item without one. Create it with the Transaction API `Assembly` service ([manual](../12-Production-Labor-API.md#assembly-service-cross-reference)).
- **The finished item is set up at the source location**, or the save fails with *"item ID does not exist at your source location."*
- **Know your assembly behavior flags** ([manual](../12-Production-Labor-API.md#assembly-behavior-flags)) — three ON/OFF flags on `assembly_hdr` decide how the item behaves:

| Flag | `Y` | `N` |
|------|-----|-----|
| `production_order_processing` | Production-order assembly (sales order line spawns/links a production order) | Kit — explodes to components, no production order |
| `auto_create_prod_order` | Auto-create + link the production order when the sales order saves | Create and link manually |
| `assembly_for_stock` | Build-to-stock (units dwell in inventory) | Make-to-order |

On a saved sales order, `oe_line.assembly` shows the outcome: `B` kit parent, `N` kit component, `P` production-order line, `S` build-to-stock line allocated from on-hand.

## Runbook

### Stage 1 — Create the production order

Two paths ([deep dive](../12-Production-Labor-API.md#how-production-orders-get-created)):

- **Path A — sales order auto-create (make-to-order).** Enter a sales order line for a `production_order_processing = Y` assembly (via the Interactive API when the line must explode — [order-with-assembly recipe](order-with-assembly.md)). With `auto_create_prod_order = Y`, P21 **nets against available stock**: stock on hand → the line allocates it and **no production order spawns**; short → an order spawns for the shortfall, linked via `prod_order_line_link`.
- **Path B — direct build-to-stock.** Drive the `ProductionOrder` window: header `source_loc_id` (the make location) plus any required user-defined fields, then on `TABPAGE_17.tp_17_dw_17` set `assembly_item_id` and `qty_to_make` (add + select a row per extra line). No sales order involved.

**The traps:** on Path A, the customer's **salesrep must be valid at the sales location** (a DynaChange rule blocks the order otherwise) and the **order date must differ from the required date**. A production order commonly gets **two pick tickets** — parts, plus labor/intangibles when intangible components source from a paired non-stock location.

### Stage 2 — Log labor BEFORE printing

Post labor via the `TimeEntry` service — [record-labor-time recipe](record-labor-time.md), [deep dive](../12-Production-Labor-API.md#labor-timing--log-labor-before-printing). Labor becomes a charge component that **must land on a pick ticket to be consumed at completion**.

**The trap:** print first, add labor after (no reprint) → the labor is allocated but on no ticket (`qty_on_pick_tickets = 0`) and completion fails with *"components have a quantity used of 0."* Fix: reprint (generates a separate labor/intangibles ticket), then confirm the new ticket.

### Stage 3 — Print the pick ticket and form

Two ways ([deep dive](../12-Production-Labor-API.md#printing-the-pick-ticket-and-form)):

- **`ProductionOrder` transaction** with `print_pick_ticket = ON` and `print_form = ON` on `TABPAGE_1.tp_1_dw_1` — creates the ticket, sets `prod_order_hdr.printed = 'Y'`, returns the PDFs in the response ([manual](../03-Transaction-API.md#pdfs-from-the-transaction-endpoint-print-flags)).
- **`m_picktickets` report** at `POST /api/v2/process/pdfreport` — creates the ticket at whatever `location_id` you specify and returns the PDF ([worked example](../03-Transaction-API.md#example-generate-a-production-order-pick-ticket-m_picktickets), and the complete example below).

**The traps:** `print_pick_ticket` emits **only at the make location** — components stocked elsewhere means the form comes back but no usable ticket; use `m_picktickets` at the stock location instead. A parts ticket only generates if the components have **stock at the source location**. Documents only return on a **savable** order — a bare reprint with nothing new errors *"Save is not enabled."* And never post an `m_*` report to `/api/v2/transaction` — it returns `Succeeded` and **emits nothing**.

### Stage 4 — Confirm the pick (Interactive API ONLY)

Open the `ProductionOrderPicking` window, load the ticket on header `TP_PRODPICKTICKETCONF.tp_prodpickticketconf` (key `prod_pick_ticket_number`), set the Confirm Pick field `row_status_flag` to `"Confirm"`, save. Confirm **every** ticket — parts *and* labor/intangibles. [Deep dive](../12-Production-Labor-API.md#confirming-the-pick--use-the-interactive-api).

**The trap (the star of this page):** posting `row_status_flag = 'Confirm'` through a bare `POST /api/v2/transaction` produces a **shell confirm** — the ticket status flips to `1962` and `qty_confirmed` gets stamped, but **`qty_applied` stays 0 and no stock moves**. The per-bin posted quantities live in a disabled `TP_BIN` grid that only the windowed (Interactive API or desktop) confirm populates. The real confirm applies the pick and moves components to the make location's WIP bin (`inv_loc.primary_bin` at `prod_order_hdr.source_location_id`; bin `0` when no primary is set).

Ticket status codes (`prod_pick_ticket_hdr.row_status_flag`): `702` Open · `1962` Confirmed · `1268` Completed. Detail rows: `704` normal, `1268` at completion.

### Stage 5 — Complete the order (production receipt)

Drive the `ProductionOrderProcessing` window ([deep dive](../12-Production-Labor-API.md#completing-the-production-order-production-receipt)):

1. Select the line on `TABPAGE_17.tp_17_dw_17`, set **`qty_to_complete`** (partial completion is supported; `qty_completed` is a read-only rollup).
2. On `TABPAGE_ASSEMBLY_BIN.tabpage_assembly_bin` set **`bin_cd`** (the finished item's `inv_loc.primary_bin`, often `0`) and **`unit_quantity`** (= the completion quantity) — **as two separate change calls**.
3. Optional per-component cost override: once `qty_to_complete` is set, `TABPAGE_18.tp_18_dw_18` exposes an editable **`new_cost`** per component; it flows `new_cost` → `PROP` receipt cost → moving average → invoice COGS.
4. Save → the assembly is received into inventory (`inv_tran` type `PROP`) and the ticketed components are consumed.

**The trap:** combining `bin_cd` and `unit_quantity` in one change call **drops the quantity**, and a later completion errors *"sum of bin quantity ... does not equal quantity made."*

### Stage 6 — Ship and invoice the linked sales order

[Deep dive](../12-Production-Labor-API.md#shipping-and-invoicing-the-linked-sales-order):

1. Print the **sales order** pick ticket: `Order` service transaction with `print_tix = ON` on `TP_FRONTCOUNTER.tp_frontcounter` (creates `oe_pick_ticket`).
2. Ship + invoice: the `Shipping` service, header `tp_1_dw_1` keyed by `pick_ticket_no` — retrieve and **save**. `create_invoice` defaults ON, so the save ships **and** invoices in one step. Partial shipments are supported.

**The traps:** the item needs a **packaging code** or the save fails. For contract pricing, leave `unit_price` unset and P21 auto-fills the job-contract price (binding `oe_line.job_price_hdr_uid`) — the contract must cover that **specific ship-to**.

### Stage 7 — Fix quantity fallout (write-offs)

If on-hand ends up wrong, post an `InventoryAdjustment` — [inventory-adjustment recipe](inventory-adjustment.md), [deep dive](../12-Production-Labor-API.md#inventory-adjustment-write-offs).

> **Cost model — before trusting COGS** ([deep dive](../12-Production-Labor-API.md#cost-model--know-this-before-trusting-cogs)): the `PROP` receipt cost = components + labor posted **before** completion. Shipment COGS is the **moving average at ship time**, not that order's receipt — while 2+ units sit in stock, a cost added to one smears across all (build-to-stock is exposed by design; make-to-order is largely immune). Labor posted after invoicing spawns a separate *"Post Freight/Labor Prod. Order: NNNN"* invoice ($0 price, ± COGS); the original invoice is untouched.

## Complete example — print the pick ticket and read back its status

Generates the production pick ticket at the **stock** location with `m_picktickets` (creates the ticket record *and* returns the PDF), then reads the new ticket back with `POST /api/v2/transaction/get` to check its status. Prerequisite: the order's form must already be printed (`prod_order_hdr.printed = 'Y'`) — run a `ProductionOrder` transaction with `print_form = ON` first. Auth comes from the [shared helper](README.md#shared-conventions-recipes-dont-repeat-these).

<!-- tabs -->
```python
import base64
import re

import httpx

BASE_URL = "https://play.p21server.com"
token, ui_server, headers = p21_auth(BASE_URL, "api_user", "api_pass")

PROD_ORDER = "1000123"   # production order number
STOCK_LOCATION = "10"    # where the components stock (NOT necessarily the make location)

# --- 1. Generate the pick ticket (creates the record + returns the PDF) ---
report = {
    "Name": "m_picktickets",
    "UseCodeValues": True,  # m_picktickets REQUIRES code values; False returns HTTP 500
    "Transactions": [{
        "Status": 0,        # reports use numeric 0, not "New"
        "DataElements": [{
            "Keys": [],
            "Type": 0,
            "Name": "TABPAGE_1.tp_1_dw_1",
            "Rows": [{"Edits": [
                {"Name": "create_pick_ticket_type", "Value": "P"},  # code "P" = Production Order
                {"Name": "beg_prod_order", "Value": PROD_ORDER},
                {"Name": "end_prod_order", "Value": PROD_ORDER},
                {"Name": "location_id", "Value": STOCK_LOCATION},
            ]}],
        }],
    }],
}

resp = httpx.post(
    f"{ui_server}/api/v2/process/pdfreport",  # NOT /api/v2/transaction (silent no-op there)
    headers=headers, json=report, verify=False, timeout=120,
)
resp.raise_for_status()
result = resp.json()

if not isinstance(result, list):  # errors come back as an envelope, not an array
    raise SystemExit(f"Report failed: {result.get('ErrorMessage')}")

doc = result[0]
if doc["ResponseStatus"]["StatusCode"] != "Success" or not doc.get("DocumentData"):
    raise SystemExit(f"Report failed: {doc['ResponseStatus'].get('Message')}")

file_name = doc["FileName"]  # e.g. "PPT123456 PRODUCTION_PICK_TICKET.pdf"
with open(file_name, "wb") as f:
    f.write(base64.b64decode(doc["DocumentData"]))
print(f"Saved {file_name}")

# --- 2. Read the new ticket back (ticket number comes from the FileName) ---
ticket_no = re.match(r"PPT(\d+)", file_name).group(1)
get_payload = {
    "ServiceName": "ProductionOrderPicking",
    "TransactionStates": [{
        "DataElementName": "TP_PRODPICKTICKETCONF.tp_prodpickticketconf",
        "Keys": [{"Name": "prod_pick_ticket_number", "Value": ticket_no}],
    }],
}
resp = httpx.post(
    f"{ui_server}/api/v2/transaction/get",
    headers=headers, json=get_payload, verify=False,
)
resp.raise_for_status()

for txn in resp.json().get("Transactions", []):
    for de in txn.get("DataElements", []):
        for row in de.get("Rows", []):
            fields = {e["Name"]: e["Value"] for e in row.get("Edits", [])}
            if "row_status_flag" in fields:
                # 702 = Open, 1962 = Confirmed, 1268 = Completed
                print(f"Ticket {fields.get('prod_pick_ticket_number')} "
                      f"for prod order {fields.get('prod_order_number')}: "
                      f"status {fields.get('row_status_flag')}")
```

```csharp
using System.Text.RegularExpressions;

var session = await P21Session.CreateAsync(
    "https://play.p21server.com", "api_user", "api_pass");

const string prodOrder = "1000123";   // production order number
const string stockLocation = "10";    // where the components stock

// --- 1. Generate the pick ticket (creates the record + returns the PDF) ---
var report = new JObject
{
    ["Name"] = "m_picktickets",
    ["UseCodeValues"] = true,  // m_picktickets REQUIRES code values; false returns HTTP 500
    ["Transactions"] = new JArray
    {
        new JObject
        {
            ["Status"] = 0,    // reports use numeric 0, not "New"
            ["DataElements"] = new JArray
            {
                new JObject
                {
                    ["Keys"] = new JArray(),
                    ["Type"] = 0,
                    ["Name"] = "TABPAGE_1.tp_1_dw_1",
                    ["Rows"] = new JArray
                    {
                        new JObject
                        {
                            ["Edits"] = new JArray
                            {
                                new JObject { ["Name"] = "create_pick_ticket_type", ["Value"] = "P" },
                                new JObject { ["Name"] = "beg_prod_order", ["Value"] = prodOrder },
                                new JObject { ["Name"] = "end_prod_order", ["Value"] = prodOrder },
                                new JObject { ["Name"] = "location_id", ["Value"] = stockLocation }
                            }
                        }
                    }
                }
            }
        }
    }
};

// NOT /api/v2/transaction (silent no-op there)
var reportResp = await session.Http.PostAsync(
    $"{session.UiServer}/api/v2/process/pdfreport",
    new StringContent(report.ToString(), Encoding.UTF8, "application/json"));
reportResp.EnsureSuccessStatusCode();
var reportBody = JToken.Parse(await reportResp.Content.ReadAsStringAsync());

if (reportBody.Type != JTokenType.Array)  // errors come back as an envelope, not an array
    throw new Exception($"Report failed: {reportBody["ErrorMessage"]}");

var doc = (JObject)((JArray)reportBody)[0];
if (doc["ResponseStatus"]?["StatusCode"]?.ToString() != "Success")
    throw new Exception($"Report failed: {doc["ResponseStatus"]?["Message"]}");

var fileName = doc["FileName"]!.ToString(); // e.g. "PPT123456 PRODUCTION_PICK_TICKET.pdf"
await File.WriteAllBytesAsync(fileName, Convert.FromBase64String(doc["DocumentData"]!.ToString()));
Console.WriteLine($"Saved {fileName}");

// --- 2. Read the new ticket back (ticket number comes from the FileName) ---
var ticketNo = Regex.Match(fileName, @"PPT(\d+)").Groups[1].Value;
var getPayload = new JObject
{
    ["ServiceName"] = "ProductionOrderPicking",
    ["TransactionStates"] = new JArray
    {
        new JObject
        {
            ["DataElementName"] = "TP_PRODPICKTICKETCONF.tp_prodpickticketconf",
            ["Keys"] = new JArray
            {
                new JObject { ["Name"] = "prod_pick_ticket_number", ["Value"] = ticketNo }
            }
        }
    }
};

var getResp = await session.Http.PostAsync(
    $"{session.UiServer}/api/v2/transaction/get",
    new StringContent(getPayload.ToString(), Encoding.UTF8, "application/json"));
getResp.EnsureSuccessStatusCode();
var getResult = JObject.Parse(await getResp.Content.ReadAsStringAsync());

foreach (var txn in getResult["Transactions"] as JArray ?? new JArray())
foreach (var de in txn["DataElements"] as JArray ?? new JArray())
foreach (var row in de["Rows"] as JArray ?? new JArray())
{
    var fields = new Dictionary<string, string>();
    foreach (var edit in row["Edits"] as JArray ?? new JArray())
        fields[edit["Name"]!.ToString()] = edit["Value"]?.ToString() ?? "";
    if (fields.ContainsKey("row_status_flag"))
        // 702 = Open, 1962 = Confirmed, 1268 = Completed
        Console.WriteLine($"Ticket {fields.GetValueOrDefault("prod_pick_ticket_number")} " +
                          $"for prod order {fields.GetValueOrDefault("prod_order_number")}: " +
                          $"status {fields.GetValueOrDefault("row_status_flag")}");
}
```
<!-- /tabs -->

> **End-to-end files** (runnable from the repo with a `.env`, dry-run by default): [`examples/python/recipes/production_order_runbook.py`](../../examples/python/recipes/production_order_runbook.py) · [`examples/csharp/Recipes/ProductionOrderRunbook.cs`](../../examples/csharp/Recipes/ProductionOrderRunbook.cs). The snippet above is self-contained; the files use the repo's shared `common` / `P21Examples.Common` helpers like every other example.

## Gotchas

- **Shell confirm (the big one).** Confirming a pick with a bare Transaction API POST flips the status to `1962` and stamps `qty_confirmed`, but leaves **`qty_applied = 0` and moves no stock** — confirm through the Interactive API `ProductionOrderPicking` window (Stage 4).
- **Labor must be on a pick ticket before completion.** Labor added after printing, without a reprint, sits at `qty_on_pick_tickets = 0` and completion fails with *"components have a quantity used of 0"* (Stage 2).
- **`bin_cd` and `unit_quantity` are two separate change calls** at completion — one combined call drops the quantity → *"sum of bin quantity ... does not equal quantity made"* (Stage 5).
- **`print_pick_ticket` emits only at the make location** — components stocked elsewhere need `m_picktickets` at the stock `location_id` (Stage 3).
- **`m_picktickets` needs `UseCodeValues: true`** and the code `"P"`; the display label is rejected, `UseCodeValues: false` returns HTTP 500. `Status`/`Type` numeric `0`, `Keys: []`.
- **Reports go to `/api/v2/process/pdfreport`.** `/api/v2/transaction` accepts the payload, returns `Succeeded`, and emits nothing.
- **Status codes:** `702` Open, `1962` Confirmed, `1268` Completed — a `1962` alone does not prove stock moved (see shell confirm).
- **Auto-create nets against stock** — stock on hand means no production order spawns; salesrep must be valid at the sales location; order date must differ from required date (Stage 1).
- **Confirm every ticket** — parts *and* the labor/intangibles ticket.

## Verify

After each stage, read back — don't trust the HTTP status:

| Stage | Check |
|-------|-------|
| Print | Pick ticket exists and is `702` Open (example above); `prod_order_hdr.printed = 'Y'` |
| Confirm | Ticket `row_status_flag = 1962` **and** quantities applied (`qty_applied > 0`) — a `1962` with `qty_applied = 0` is a shell confirm |
| Complete | Ticket/detail rows at `1268`; assembly receipt posted as `inv_tran` type `PROP` |
| Ship + invoice | Invoice created by the `Shipping` save; shipment posts `inv_tran` type `WO` |

> **Credit:** [Alex Westemeier](https://github.com/AWestemeier)
