# Production Order & Labor Hour APIs

> **Disclaimer:** This is unofficial, community-created documentation for Epicor Prophet 21 APIs. It is not affiliated with, endorsed by, or supported by Epicor Software Corporation. All product names, trademarks, and registered trademarks are property of their respective owners. Use at your own risk.

---

## Overview

P21 provides production order management and labor hour tracking through the **Transaction API** and **Interactive API**. There are no dedicated REST endpoints for production or labor -- these capabilities use the existing Transaction and Interactive patterns documented in [Transaction API](03-Transaction-API.md) and [Interactive API](04-Interactive-API.md).

### Key Characteristics

- **No dedicated REST endpoints** - Uses Transaction API (`/api/v2/transaction`) and Interactive API (`/api/ui/interactive/v2/`)
- **Full production lifecycle** - Create orders, record labor, track costs, process completions
- **OData tables not exposed by default** - Production-related tables require SOA Admin configuration before OData access
- **Service-based** - Each production function maps to a named service

### When to Use

- Creating and managing production orders
- Recording labor hours against production orders or service orders
- Maintaining labor codes, work centers, and routing templates
- Tracking production costs (material, labor, freight, process)
- Automating production order processing and completion

---

## Available Services

All services below are accessed through the Transaction API. Use `GET /api/v2/services` to confirm availability on your P21 instance. Use `GET /api/v2/definition/{ServiceName}` to retrieve the full schema and template for any service.

### Core Production Services

| Service | Purpose |
|---------|---------|
| `ProductionOrder` | Create and manage production orders with assemblies, components, labor, routing |
| `ProductionOrderProcessing` | Process and complete production orders |
| `ProductionOrderPicking` | Pick ticket management for production orders |
| `ProductionOrderFreightEntry` | Freight cost entry for production orders |
| `CompletedProducitonOrderAdjustment` | Adjust completed production orders |

> **Note:** The service name `CompletedProducitonOrderAdjustment` contains a typo ("Produciton" instead of "Production"). This is P21's actual service name -- you must use the misspelled version in API calls.

### Labor & Time Services

| Service | Purpose |
|---------|---------|
| `TimeEntry` | Record labor hours against production orders |
| `TimeEntrySO` | Record labor hours against service orders |
| `Labor` | Labor code maintenance (rates, types, costs) |
| `LaborProcess` | Labor process templates with operation sequences |

### Supporting Services

| Service | Purpose |
|---------|---------|
| `Job` | Job maintenance |
| `JobControl` | Job control with customer/site info |
| `JobContractPricing` | Job contract pricing (see [detailed docs](03-Transaction-API.md#jobcontractpricing-service)) |
| `WorkCenter` | Work center maintenance |
| `Operation` | Operation definitions |
| `PredefinedRouting` | Routing templates |
| `Assembly` | Assembly/BOM definitions (see [detailed docs](03-Transaction-API.md#assembly-service)) |
| `AssemblyClass` | Assembly classification |
| `ManufacturingClass` | Manufacturing classification |
| `Shift` | Shift definitions |

---

## Recording Labor Hours (TimeEntry Service)

The `TimeEntry` service is the primary service for posting labor hours to production orders. It uses a header/detail pattern with a technician header and one or more labor line items.

### Service Definition

Retrieve the full schema with:

```http
GET /api/v2/definition/TimeEntry
```

#### Header -- `TP_TECHNICIAN.tp_technician` (Form)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `company_id` | Char | Yes | Company ID |
| `technician_id` | Char | Yes | Technician's **contact ID** (a contact record, not a P21 user ID) |
| `entry_date` | Datetime | Yes | Date of time entry |

#### Labor Lines -- `TP_LABORRECORDING.prod_order_line_comp_labor` (List)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `prod_order_number` | Decimal | No (key) | Production order number |
| `item_id` | Char | No | Assembly item ID |
| `component_labor_id` | Char | No | Component labor ID |
| `operation_cd` | Char | No | Operation code |
| `service_labor_id` | Char | No | Labor ID (from Labor service) |
| `start_time` | Datetime | No | Start time |
| `end_time` | Datetime | No | End time |
| `time_worked` | Char | No | Time worked (HH:MM format) |
| `labor_type_cd` | Long | Yes | `Rate`, `OT Rate`, or `Prem Rate` |
| `cc_completeprodorder` | Char | No | Complete production order flag |

> **Field order matters.** On the labor grid, fields must be entered in a strict order or the downstream fields stay disabled: `prod_order_number` → `item_id` → `component_labor_id` → `start_time` → `end_time`. See [Time Entry Against a Production Order (Quick Time Entry)](#time-entry-against-a-production-order-quick-time-entry) for the verified mechanics.

### Example: Record Labor Hours

The example below posts labor by `service_labor_id` without `item_id` — the **service-labor variant**. To record labor against a specific production-order assembly line and labor component, use the production-order grid path (`prod_order_number` → `item_id` → `component_labor_id` → `start_time` → `end_time`) described in [Quick Time Entry](#time-entry-against-a-production-order-quick-time-entry).

This is one step of the full production order lifecycle — see the [Production Order Runbook](recipes/production-order-runbook.md#stage-2-log-labor-before-printing) for the end-to-end sequence, and the standalone [record-labor-time recipe](recipes/record-labor-time.md) for a complete, paste-and-run version of this call (using the `item_id`/`component_labor_id` variant).

<!-- tabs -->
```python
import httpx

# After authentication and getting ui_server_url...
headers = {"Authorization": "Bearer <token>", "Content-Type": "application/json", "Accept": "application/json"}

payload = {
    "Name": "TimeEntry",
    "UseCodeValues": False,
    "Transactions": [{
        "Status": "New",
        "DataElements": [
            {
                "Name": "TP_TECHNICIAN.tp_technician",
                "Type": "Form",
                "Keys": [],
                "Rows": [{
                    "Edits": [
                        {"Name": "company_id", "Value": "ACME"},
                        {"Name": "technician_id", "Value": "300"},
                        {"Name": "entry_date", "Value": "2026-03-06"}
                    ],
                    "RelativeDateEdits": []
                }]
            },
            {
                "Name": "TP_LABORRECORDING.prod_order_line_comp_labor",
                "Type": "List",
                "Keys": ["prod_order_number"],
                "Rows": [{
                    "Edits": [
                        {"Name": "prod_order_number", "Value": "1001"},
                        {"Name": "service_labor_id", "Value": "LABOR01"},
                        {"Name": "start_time", "Value": "2026-03-06T08:00:00"},
                        {"Name": "end_time", "Value": "2026-03-06T12:00:00"},
                        {"Name": "time_worked", "Value": "4:00"},
                        {"Name": "labor_type_cd", "Value": "Rate"}
                    ],
                    "RelativeDateEdits": []
                }]
            }
        ]
    }]
}

response = httpx.post(
    f"{ui_server_url}/api/v2/transaction",
    headers=headers,
    json=payload,
    verify=False
)
response.raise_for_status()
result = response.json()
print(f"Succeeded: {result['Summary']['Succeeded']}")
```

```csharp
var payload = new JObject
{
    ["Name"] = "TimeEntry",
    ["UseCodeValues"] = false,
    ["Transactions"] = new JArray
    {
        new JObject
        {
            ["Status"] = "New",
            ["DataElements"] = new JArray
            {
                new JObject
                {
                    ["Name"] = "TP_TECHNICIAN.tp_technician",
                    ["Type"] = "Form",
                    ["Keys"] = new JArray(),
                    ["Rows"] = new JArray
                    {
                        new JObject
                        {
                            ["Edits"] = new JArray
                            {
                                new JObject { ["Name"] = "company_id", ["Value"] = "ACME" },
                                new JObject { ["Name"] = "technician_id", ["Value"] = "300" },
                                new JObject { ["Name"] = "entry_date", ["Value"] = "2026-03-06" }
                            },
                            ["RelativeDateEdits"] = new JArray()
                        }
                    }
                },
                new JObject
                {
                    ["Name"] = "TP_LABORRECORDING.prod_order_line_comp_labor",
                    ["Type"] = "List",
                    ["Keys"] = new JArray { "prod_order_number" },
                    ["Rows"] = new JArray
                    {
                        new JObject
                        {
                            ["Edits"] = new JArray
                            {
                                new JObject { ["Name"] = "prod_order_number", ["Value"] = "1001" },
                                new JObject { ["Name"] = "service_labor_id", ["Value"] = "LABOR01" },
                                new JObject { ["Name"] = "start_time", ["Value"] = "2026-03-06T08:00:00" },
                                new JObject { ["Name"] = "end_time", ["Value"] = "2026-03-06T12:00:00" },
                                new JObject { ["Name"] = "time_worked", ["Value"] = "4:00" },
                                new JObject { ["Name"] = "labor_type_cd", ["Value"] = "Rate" }
                            },
                            ["RelativeDateEdits"] = new JArray()
                        }
                    }
                }
            }
        }
    }
};

var content = new StringContent(
    payload.ToString(), Encoding.UTF8, "application/json");
var response = await client.PostAsync(
    $"{uiServerUrl}/api/v2/transaction", content);
response.EnsureSuccessStatusCode();

var result = JObject.Parse(
    await response.Content.ReadAsStringAsync());
Console.WriteLine($"Succeeded: {result["Summary"]["Succeeded"]}");
```
<!-- /tabs -->

### Response

A successful time entry returns:

```json
{
    "Messages": ["Transaction 1:: "],
    "Results": {
        "Name": "TimeEntry",
        "Transactions": [
            {
                "DataElements": [...],
                "Status": "Passed"
            }
        ]
    },
    "Summary": {
        "Succeeded": 1,
        "Failed": 0,
        "Other": 0
    }
}
```

---

## ProductionOrder Service -- Full Structure

The `ProductionOrder` service is the most complex production service, with DataElements covering headers, assemblies, components, labor, routing, costs, and completion tracking.

Retrieve the full schema with:

```http
GET /api/v2/definition/ProductionOrder
```

### DataElements

#### 1. `TABPAGE_1.tp_1_dw_1` (Form) -- Production Order Header

Key: `prod_order_number`

Contains 54+ fields for the production order header:

| Field | Type | Description |
|-------|------|-------------|
| `prod_order_number` | Decimal | Production order number (auto-assigned on create) |
| `source_loc_id` | Long | Source location/warehouse |
| `order_date` | Datetime | Order creation date |
| `required_date` | Datetime | Required completion date |
| `expedite_date` | Datetime | Expedite date |
| `company_id` | Char | Company ID |
| `entered_by` | Char | User who created the order |
| `approved` | Char | Approval flag |
| `cancel` | Char | Cancellation flag |
| `priority` | Long | Priority level |
| `complete` | Char | Completion flag |
| `notes` | Char | Order notes |

#### 2. `TABPAGE_17.tp_17_dw_17` (List) -- Assembly Lines

Assembly items to be manufactured on this production order:

| Field | Type | Description |
|-------|------|-------------|
| `assembly_item_id` | Char | Assembly item ID |
| `qty_to_make` | Decimal | Quantity to manufacture |
| `qty_completed` | Decimal | Quantity completed so far |
| `required_date` | Datetime | Required date for this assembly |
| `process_cd` | Char | Route/process code |

#### 3. `TABPAGE_18.components` (List) -- Component Materials

Bill of materials for the production order:

| Field | Type | Description |
|-------|------|-------------|
| `item_id` | Char | Component item ID |
| `qty_per_assembly` | Decimal | Quantity required per assembly |
| `unit_of_measure` | Char | Unit of measure |
| `operation_cd` | Char | Operation code |
| `estimated_labor_cost` | Decimal | Estimated labor cost |
| `estimated_material_cost` | Decimal | Estimated material cost |
| `technician_id` | Char | Assigned technician |
| `operation_sequence` | Long | Operation sequence order |

#### 4. `TP_LABOR.tp_labor` (List) -- Labor Entries

Labor lines recorded against the production order:

| Field | Type | Description |
|-------|------|-------------|
| `service_center_id` | Char | Work center ID |
| `technician_id` | Char | Technician/worker ID |
| `service_labor_id` | Char | Labor code ID |
| `time_worked` | Char | Time worked (HH:MM format) |
| `labor_type_cd` | Char | Rate type: `Rate`, `OT Rate`, or `Prem Rate` |

#### 5. `TP_LABORDETAIL.tp_labordetail` (Form) -- Labor Entry Detail

Detail view for a selected labor entry:

| Field | Type | Description |
|-------|------|-------------|
| `applied_labor_acct` | Char | GL account for applied labor |
| `bill_to_customer_flag` | Char | Bill labor to customer flag |
| `skill_level` | Char | Required skill level |
| `time_worked` | Char | Time worked |
| `unit_cost` | Decimal | Unit cost |
| `location_id` | Long | Location ID |

#### 6. `TP_LABORSCHEDULEDISPLAY.tp_laborscheduledisplay` (List) -- Labor Schedule/History

Read-only display of labor recorded against the production order:

| Field | Type | Description |
|-------|------|-------------|
| `component_labor_id` | Char | Component labor ID |
| `operation_cd` | Char | Operation code |
| `service_center_id` | Char | Work center |
| `technician_id` | Char | Technician |
| `recorded_date` | Datetime | Date labor was recorded |
| `time_worked` | Char | Time worked |
| `start_time` | Datetime | Start time |
| `end_time` | Datetime | End time |
| `labor_type_cd` | Char | Rate type |
| `sales_cost` | Decimal | Sales cost |
| `total_cost` | Decimal | Total cost |

#### 7. `COMPLETION.completion` (List) -- Completion Records

Tracks completion milestones with cost breakdowns:

| Field | Type | Description |
|-------|------|-------------|
| `date_created` | Datetime | Completion date |
| `qty_completed` | Decimal | Quantity completed |
| `material_cost` | Decimal | Material cost |
| `labor_cost` | Decimal | Direct labor cost |
| `labor_cost_indirect` | Decimal | Indirect labor cost |
| `other_charge_cost` | Decimal | Other charges |
| `freight_cost` | Decimal | Freight cost |
| `process_cost` | Decimal | Process/routing cost |
| `additional_material_cost` | Decimal | Additional material cost |
| `additional_labor_cost` | Decimal | Additional direct labor cost |
| `additional_labor_cost_indirect` | Decimal | Additional indirect labor cost |
| `additional_other_charge_cost` | Decimal | Additional other charges |
| `additional_freight_cost` | Decimal | Additional freight cost |
| `additional_process_cost` | Decimal | Additional process cost |

#### 8. `ROUTING_TABPAGE.process_x_transaction` (Form) -- Routing/Process Info

Routing and process details for the production order:

| Field | Type | Description |
|-------|------|-------------|
| `process_code` | Char | Process/routing code |
| `raw_item_id` | Char | Raw material item ID |
| `finished_item_id` | Char | Finished goods item ID |
| `qty_requested` | Decimal | Quantity requested |
| `qty_completed` | Decimal | Quantity completed |

#### 9. `TP_ASSEMBLYCOSTS.tp_assemblycosts` (Form) -- Assembly Cost Summary

Estimated vs. actual cost comparison:

| Field | Type | Description |
|-------|------|-------------|
| `estimated_freight_cost` | Decimal | Estimated freight |
| `actual_freight_cost` | Decimal | Actual freight |
| `estimated_direct_labor_cost` | Decimal | Estimated direct labor |
| `actual_direct_labor_cost` | Decimal | Actual direct labor |
| `estimated_indirect_labor_cost` | Decimal | Estimated indirect labor |
| `actual_indirect_labor_cost` | Decimal | Actual indirect labor |
| `estimated_other_charge_cost` | Decimal | Estimated other charges |
| `actual_other_charge_cost` | Decimal | Actual other charges |
| `estimated_process_cost` | Decimal | Estimated process cost |
| `actual_process_cost` | Decimal | Actual process cost |

### Additional DataElements

The `ProductionOrder` service also includes DataElements for:

- **Pick tickets** -- Production order picking
- **Document links** -- Attached documents and files
- **Notes** -- Order notes and annotations
- **Serial numbers** -- Serial tracking for produced items
- **Lot numbers** -- Lot tracking
- **Bin locations** -- Bin allocation
- **Stock availability** -- Component availability checking
- **PO linkage** -- Links to purchase orders for components

Use `GET /api/v2/definition/ProductionOrder` to see the complete list of DataElements and all available fields.

---

## Assembly Service (Cross-Reference)

Assembly definitions (BOM/bill of materials) are a prerequisite for production orders -- you cannot create a production order for an item that does not have an assembly definition. The `Assembly` Transaction API service creates these definitions, specifying which components make up an assembled product along with routing steps and cost estimates.

**Full documentation:** See [Transaction API -- Assembly Service](03-Transaction-API.md#assembly-service) for the complete service structure, field reference, known limitations, and code examples.

**Typical workflow:**
1. Create the inventory item via Inventory REST API (`POST /api/inventory/parts`)
2. Create the assembly/BOM definition via Transaction API (`Assembly` service)
3. Create production orders via Transaction API (`ProductionOrder` service) referencing the assembled item

### Assembly Behavior Flags

Three ON/OFF flags on the assembly header (`assembly_hdr`, header datawindow `assemblyhdr`, key `inv_mast_item_id`) control how the item behaves at order entry and in production:

| Flag | `Y` | `N` |
|------|-----|-----|
| `production_order_processing` | Production-order assembly (a sales order line spawns/links a production order) | Kit — explodes to components on the order, no production order |
| `auto_create_prod_order` | Auto-create and link the production order when the sales order saves | Create and link the production order manually |
| `assembly_for_stock` | Build-to-stock item (units dwell in inventory) | Make-to-order |

On a saved sales order, `oe_line.assembly` reflects the outcome: `B` = kit parent, `N` = kit component, `P` = production-order line, `S` = build-to-stock line allocated from on-hand.

> **Credit:** [Alex Westemeier](https://github.com/AWestemeier) — flag semantics verified end-to-end.

---

## Production Order Lifecycle (End-to-End)

Everything in this section was verified live against a P21 test environment (credit: [Alex Westemeier](https://github.com/AWestemeier), June–July 2026). It covers the behavior the schema tables above don't: how orders spawn, why pick tickets go missing, why a "confirmed" pick can move no stock, and how costs flow to the invoice.

### How Production Orders Get Created

**Path A — Sales order auto-create (make-to-order).** A sales order line for a `production_order_processing = Y` assembly gets `oe_line.assembly = 'P'`. With `auto_create_prod_order = Y`, P21 **nets against available stock**:

- Stock on hand → the line **allocates it and no production order spawns** (`qty_allocated > 0`, no link).
- Short → a production order spawns **for the shortfall**, linked via `prod_order_line_link` (`transaction_uid = oe_line.oe_line_uid`, `trans_type = 'O'`).

Neither min/max settings nor `make = 'Y'` is required for this path. Gotchas: the customer's **salesrep must be valid at the sales location** (a DynaChange rule blocks the order otherwise), and the **`requested_date` must be after the `order_date`**. Enter the order via the Interactive API when the line must explode — see [Sales Order Entry with Assembly Lines](04-Interactive-API.md#sales-order-entry-with-assembly-lines).

**Path B — Direct build-to-stock.** Drive the `ProductionOrder` window: set the header `source_loc_id` (the make location — where components are stocked *and* the finished item exists) plus any required user-defined fields, then on `TABPAGE_17.tp_17_dw_17` set `assembly_item_id` and `qty_to_make` (add a row and select it for each additional line). No sales order involved. If the finished item isn't set up at the source location, the save fails with *"item ID does not exist at your source location."*

Location notes: the production order's make location comes from `prod_order_hdr.source_location_id`. Physical components source from the stocking location; **intangible components** (labor, burden, charge items) can source from a paired non-stock location if the environment is configured that way — which is why a production order commonly has **two pick tickets** (parts + labor/intangibles). Dates stay synced between a linked sales order and its production order; quantities are copied once at entry and then move independently.

### Printing the Pick Ticket and Form

Print via a `ProductionOrder` transaction with `print_pick_ticket = ON` and `print_form = ON` on `TABPAGE_1.tp_1_dw_1`. This creates the pick ticket, sets `prod_order_hdr.printed = 'Y'`, and returns the PDFs in the response — see [PDFs from the /transaction endpoint](03-Transaction-API.md#pdfs-from-the-transaction-endpoint-print-flags).

- **`print_pick_ticket` emits only at the MAKE location.** If the components stock at a different location, you get the form but no usable pick ticket. Generate the ticket at the stock location with the `m_picktickets` report instead — see [the worked example](03-Transaction-API.md#example-generate-a-production-order-pick-ticket-m_picktickets).
- A **parts** pick ticket generates only if the components have **stock at the source location** — `assembly_for_stock` is not required.
- Documents only return on a **savable** order; a bare reprint with nothing new to pick errors *"Save is not enabled."*

### Labor Timing — Log Labor BEFORE Printing

Labor posted through Time Entry becomes a labor charge component on the production order, and that component **must land on a pick ticket to be consumed at completion**:

- **Log labor → then print** (the ticket picks up the labor), **or reprint after adding labor** — the reprint generates a separate **labor/intangibles pick ticket** for allocated-but-unticketed labor.
- If you print first and add labor after (without reprinting), the labor is allocated but on no ticket (`qty_on_pick_tickets = 0`) → completion fails with *"components have a quantity used of 0."* Fix: reprint, confirm the new ticket.

### Confirming the Pick — Use the Interactive API

Confirm with the `ProductionOrderPicking` window: header `tp_prodpickticketconf` (key `prod_pick_ticket_number`), set the Confirm Pick field `row_status_flag` to `"Confirm"`, and save. Confirm **every** ticket (parts and labor/intangibles).

> ⚠️ **Shell-confirm warning — do NOT confirm with a bare Transaction API POST.** Posting `row_status_flag = 'Confirm'` through `/api/v2/transaction` flips the ticket status (1962) and stamps `qty_confirmed`, but leaves **`qty_applied = 0` and moves no stock** — a shell confirm. The per-bin posted quantities live in a disabled `TP_BIN` grid that only the windowed (Interactive API or desktop) confirm populates. The real confirm applies the pick and moves the picked components to the make location's WIP bin (`inv_loc.primary_bin` at `prod_order_hdr.source_location_id`; bin `0` when no primary is set).

Pick ticket status codes (`prod_pick_ticket_hdr.row_status_flag`): `702` = Open, `1962` = Confirmed, `1268` = Completed. Detail rows: `704` = normal, `1268` at completion.

### Completing the Production Order (Production Receipt)

Complete with the `ProductionOrderProcessing` window:

1. Select the line on `TABPAGE_17.tp_17_dw_17` and set **`qty_to_complete`** (partial completion is supported). `qty_completed` is a read-only rollup.
2. Set the receiving bin on `TABPAGE_ASSEMBLY_BIN.tabpage_assembly_bin`: **`bin_cd`** (the finished item's `inv_loc.primary_bin`, often `0`) and **`unit_quantity`** (= the completion quantity) — **as two separate change calls.** Combining them in one call drops the quantity, and a subsequent completion errors *"sum of bin quantity ... does not equal quantity made."*
3. Save → the assembly is received into inventory (`inv_tran` type `PROP`) and the ticketed components are consumed.

**Per-component cost override at completion:** once `qty_to_complete` is set, the component grid (`TABPAGE_18.tp_18_dw_18`) exposes an editable **`new_cost`** per component (the read-only `inventory_cost` beside it is the current moving average). A `new_cost` override flows: `new_cost` → `PROP` receipt cost → the finished item's moving average → invoice COGS. Use it to book an agreed cost (e.g. a rebated component cost) instead of the moving average.

### Time Entry Against a Production Order (Quick Time Entry)

Complementing the [TimeEntry service reference](#recording-labor-hours-timeentry-service) above, the production-order labor grid path has strict mechanics:

- Header `TP_TECHNICIAN.tp_technician`: `company_id`, `technician_id` — **a contact ID**, not a user ID — and `entry_date`.
- Labor grid `prod_order_line_comp_labor`: enter fields **in this order** — `prod_order_number` → `item_id` (the assembly line's item) → `component_labor_id` (the labor component) → `start_time` → `end_time`. Out of order, the downstream fields stay disabled.
- Time is stored per line in hours/minutes at minute granularity and **accumulates** across entries; cost = minutes × the labor code's rate.
- ⚠️ **The accounting period for `entry_date` must be open**, or the save fails.

### Shipping and Invoicing the Linked Sales Order

1. Print the sales order pick ticket: `Order` service transaction with `print_tix = ON` on `TP_FRONTCOUNTER.tp_frontcounter` (creates `oe_pick_ticket`).
2. Ship + invoice: the `Shipping` service, header `tp_1_dw_1` keyed by `pick_ticket_no` — retrieve and **save**. `create_invoice` defaults ON, so the save ships the order **and** creates the invoice in one step. Partial shipments are supported. The item needs a **packaging code** or the save fails.

Contract pricing note: leave `unit_price` unset on the sales order line and P21 auto-fills the job-contract price, binding `oe_line.job_price_hdr_uid` — the contract must cover that **specific ship-to**. Works for production-order assemblies, not just kits.

### Inventory Adjustment (Write-Offs)

The `InventoryAdjustment` service posts on-hand adjustments with no invoice: header `tp_1_dw_1` takes `location_id` and `reason_id` (pass the reason's **display text**, not its code, with `UseCodeValues: false`); line `tp_17_dw_17` takes `item_id` and `unit_quantity` = the signed delta (e.g. negative on-hand to zero it out). Save posts the adjustment.

### Cost Model — Know This Before Trusting COGS

- **Assembly receipt cost** (`inv_tran` `PROP` `unit_cost_amt`) = component costs **+ labor posted before completion**. Labor logged after completion misses the receipt.
- **Shipment COGS** (`invoice_line.cogs_amount`, `inv_tran` `WO`) = the item's **moving-average cost at ship time**, NOT that order's specific receipt.
- **Moving-average pooling:** while two or more units of the same item sit in stock, a cost added to one (e.g. a labor overrun) smears across all of them — an unrelated unit ships at a blended cost. Make-to-order (one in, one out) is largely immune; **build-to-stock is exposed by design**. True per-job cost is the `PROP` receipt, not the invoice COGS.
- **Labor posted after invoicing** generates a separate *"Post Freight/Labor Prod. Order: NNNN"* invoice ($0 price, ± COGS) — P21's standard post-order cost-adjustment channel; the original invoice is untouched.

### Key Tables

`assembly_hdr` / `assembly_line` (BOM + behavior flags) · `oe_hdr` / `oe_line` (`assembly` B/N/P/S) · `prod_order_line_link` · `prod_order_hdr` / `prod_order_line` / `prod_order_line_component` · `prod_pick_ticket_hdr` / `prod_pick_ticket_detail` · `oe_pick_ticket` · `prod_order_line_comp_labor` · `invoice_hdr` / `invoice_line` · `inv_loc` (min/max, moving average, primary bin) · `inv_tran` (`PROP` receipt / `WO` ship).

---

## Labor Service -- Labor Code Maintenance

The `Labor` service manages labor code definitions including rates, types, and cost structures.

Retrieve the full schema with:

```http
GET /api/v2/definition/Labor
```

### Key Field

`service_labor_id` -- Unique identifier for the labor code.

### Header Fields

| Field | Type | Description |
|-------|------|-------------|
| `service_labor_id` | Char | Labor code ID |
| `service_labor_desc` | Char | Description |
| `estimated_hours` | Decimal | Default estimated hours |
| `labor_type_cd` | Char | `Direct` or `Indirect` |
| `estimate_rate_level` | Char | Rate level for estimates |
| `skill_level` | Char | Required skill level |
| `min_hours_charged` | Decimal | Minimum hours charged |
| `row_status_flag` | Long | Record status |

### Rate Tables

Each labor code can have multiple rate levels:

| Field | Type | Description |
|-------|------|-------------|
| `base_rate` | Decimal | Base rate amount |
| `hourly_rate` | Decimal | Standard hourly rate |
| `ot_rate` | Decimal | Overtime rate |
| `prem_rate` | Decimal | Premium rate |
| `rate_amount` | Decimal | Rate amount per level |

### Cost Data

Cost fields exist at both global and per-location levels:

| Field | Type | Description |
|-------|------|-------------|
| `estimated_labor_cost` | Decimal | Estimated labor cost |
| `hourly_cost` | Decimal | Standard hourly cost |
| `overtime_hourly_cost` | Decimal | Overtime hourly cost |
| `premium_hourly_cost` | Decimal | Premium hourly cost |
| `burdened_cost` | Decimal | Burdened (loaded) cost |
| `commission_cost` | Decimal | Commission cost |

---

## LaborProcess Service -- Process Templates

The `LaborProcess` service defines labor process templates with ordered operation sequences. These templates can be applied to production orders to pre-populate labor steps.

Retrieve the full schema with:

```http
GET /api/v2/definition/LaborProcess
```

### Key Field

`service_labor_process_id` -- Unique identifier for the labor process template.

### Header Fields

| Field | Type | Description |
|-------|------|-------------|
| `service_labor_process_id` | Char | Process template ID |
| `service_labor_process_desc` | Char | Description |
| `row_status_flag` | Long | Record status |
| `labor_operation_sequence_flag` | Char | Operation sequencing flag |

### Labor Process List (Operations)

| Field | Type | Description |
|-------|------|-------------|
| `service_labor_id` | Char | Labor code ID |
| `estimated_hours` | Decimal | Estimated hours for this operation |
| `previous_operation` | Long | Previous operation in sequence |
| `operation_sequence` | Long | This operation's sequence number |
| `next_operation` | Long | Next operation in sequence |

---

## Interactive API Windows

All of the following windows can be opened via the Interactive API for stateful, step-by-step interaction with full business logic validation. See [Interactive API](04-Interactive-API.md) for session management and window operation details.

| ServiceName | Window | Use Case |
|-------------|--------|----------|
| `ProductionOrder` | Production Order Entry | Full production order management |
| `Labor` | Labor Maintenance | Labor code CRUD |
| `LaborProcess` | Labor Process Maintenance | Process template management |
| `TimeEntry` | Time Entry | Record labor hours |
| `TimeEntrySO` | Time Entry (Service Order) | Service order labor |
| `Job` | Job Maintenance | Job CRUD |
| `JobControl` | Job Control Maintenance | Job sites and contacts |
| `Operation` | Operation Maintenance | Operation definitions |
| `PredefinedRouting` | Predefined Routing | Routing templates |
| `Assembly` | Assembly Maintenance | Assembly definitions |
| `ManufacturingClass` | Manufacturing Class | Classification maintenance |
| `Shift` | Shift Maintenance | Shift definitions |
| `ProductionOrderProcessing` | Production Order Processing | Process and complete production orders |

> **Note:** `WorkCenter` returns HTTP 500 when opened via the Interactive API. This may require specific licensing or server-side configuration. Use the Transaction API for work center operations instead.

### Opening a Production Window

<!-- tabs -->
```python
"""Open the ProductionOrder Interactive API window and load a specific order."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
PROD_ORDER_NUMBER = "1001"                # production order to load
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

    # Create the session first -- response window handling is a session-level
    # setting, not a window-open option
    response = client.post(
        f"{ui_server}/api/ui/interactive/sessions",
        headers=headers,
        json={"ResponseWindowHandlingEnabled": True},
    )
    response.raise_for_status()

    # Open Production Order Entry window
    open_payload = {"ServiceName": "ProductionOrder"}
    response = client.post(
        f"{ui_server}/api/ui/interactive/v2/window",
        headers=headers,
        json=open_payload,
    )
    response.raise_for_status()
    result = response.json()
    window_id = result["WindowId"]
    print(f"Window opened: {window_id}")

    # Retrieve a production order
    change_payload = {
        "WindowId": window_id,
        "List": [{
            "TabName": "TABPAGE_1",
            "DatawindowName": "tp_1_dw_1",
            "FieldName": "prod_order_number",
            "Value": PROD_ORDER_NUMBER,
        }],
    }
    response = client.put(
        f"{ui_server}/api/ui/interactive/v2/change",
        headers=headers,
        json=change_payload,
    )
    response.raise_for_status()

    # Read current window data -- confirms what the change call actually loaded
    response = client.get(
        f"{ui_server}/api/ui/interactive/v2/data",
        params={"id": window_id},
        headers=headers,
    )
    response.raise_for_status()
    data = response.json()
    print(f"Window data keys: {sorted(data.keys())}")
```

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string ProdOrderNumber = "1001";                  // production order to load
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

// Create the session first -- response window handling is a session-level
// setting, not a window-open option
var sessionPayload = new JsonObject { ["ResponseWindowHandlingEnabled"] = true };
var sessionContent = new StringContent(
    sessionPayload.ToJsonString(), Encoding.UTF8, "application/json");
var sessionResp = await client.PostAsync(
    $"{uiServer}/api/ui/interactive/sessions", sessionContent);
sessionResp.EnsureSuccessStatusCode();

// Open Production Order Entry window
var openPayload = new JsonObject { ["ServiceName"] = "ProductionOrder" };
var openContent = new StringContent(
    openPayload.ToJsonString(), Encoding.UTF8, "application/json");
var openResp = await client.PostAsync(
    $"{uiServer}/api/ui/interactive/v2/window", openContent);
openResp.EnsureSuccessStatusCode();

var openResult = JsonNode.Parse(await openResp.Content.ReadAsStringAsync())!;
var windowId = openResult["WindowId"]!.ToString();
Console.WriteLine($"Window opened: {windowId}");

// Retrieve a production order
var changePayload = new JsonObject
{
    ["WindowId"] = windowId,
    ["List"] = new JsonArray
    {
        new JsonObject
        {
            ["TabName"] = "TABPAGE_1",
            ["DatawindowName"] = "tp_1_dw_1",
            ["FieldName"] = "prod_order_number",
            ["Value"] = ProdOrderNumber,
        }
    }
};
var changeContent = new StringContent(
    changePayload.ToJsonString(), Encoding.UTF8, "application/json");
var changeResp = await client.PutAsync(
    $"{uiServer}/api/ui/interactive/v2/change", changeContent);
changeResp.EnsureSuccessStatusCode();

// Read current window data -- confirms what the change call actually loaded
var dataResp = await client.GetAsync(
    $"{uiServer}/api/ui/interactive/v2/data?id={windowId}");
dataResp.EnsureSuccessStatusCode();
var data = JsonNode.Parse(await dataResp.Content.ReadAsStringAsync())!.AsObject();
Console.WriteLine($"Window data keys: {string.Join(", ", data.Select(kv => kv.Key))}");

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

> **Important:** Always include `DatawindowName` in v2 change requests. P21 25.2+ requires it -- omitting it causes `Status: 2` (Failure) responses. See [Interactive API - DatawindowName Required](04-Interactive-API.md) for details.

---

## Data Access (OData)

Production and labor tables are **not exposed** in OData by default. To enable OData access to production data:

1. Open **SOA Admin > Administration**
2. Add production-related tables/views to OData permissions
3. Click **Refresh OData API service**

### Common Tables to Expose

| Table Name | Description |
|------------|-------------|
| `prod_order_hdr` | Production order headers |
| `prod_order_line` | Production order lines |
| `prod_order_line_comp_labor` | Labor recorded against production orders |
| `work_center` | Work center definitions |
| `service_labor` | Labor code definitions |

Once exposed, query them via the OData API:

<!-- tabs -->
```python
"""Query production orders via OData, after enabling the tables in SOA Admin."""
import re

import httpx

# ---- EDIT THESE -----------------------------------------------------------
BASE_URL = "https://play.p21server.com"   # your P21 server
USERNAME = "apiuser"
PASSWORD = "your-password"
VERIFY_SSL = False                        # True once you trust the cert chain
COMPANY_ID = "ACME"                       # company to filter on
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


with httpx.Client(verify=VERIFY_SSL, timeout=120, follow_redirects=True) as client:
    token = get_token(client)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",       # 2026.1 returns an empty 500 without this
        "Content-Type": "application/json",
    }

    # Query production orders (after enabling in SOA Admin)
    response = client.get(
        f"{BASE_URL}/odataservice/odata/table/prod_order_hdr",
        headers=headers,
        params={"$filter": f"company_id eq '{COMPANY_ID}'", "$top": "10"},
    )
    response.raise_for_status()
    orders = response.json()["value"]
    for order in orders:
        print(f"PO# {order['prod_order_number']}: {order['complete']}")
```

```csharp
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;

// ---- EDIT THESE -----------------------------------------------------------
const string BaseUrl = "https://play.p21server.com";   // your P21 server
const string Username = "apiuser";
const string Password = "your-password";
const string CompanyId = "ACME";                        // company to filter on
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
client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);

// Query production orders (after enabling in SOA Admin)
var response = await client.GetAsync(
    $"{BaseUrl}/odataservice/odata/table/prod_order_hdr" +
    $"?$filter=company_id eq '{CompanyId}'&$top=10");
response.EnsureSuccessStatusCode();

var data = JsonNode.Parse(await response.Content.ReadAsStringAsync())!;
var orders = data["value"]!.AsArray();
foreach (var order in orders)
{
    Console.WriteLine($"PO# {order!["prod_order_number"]}: {order["complete"]}");
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

// Some middleware answers this endpoint in XML even when asked for JSON.
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

See [OData API](02-OData-API.md) for full query syntax including `$filter`, `$select`, `$orderby`, and `$expand`.

---

## Best Practices

1. **Get definitions first** - Always retrieve the service definition (`GET /api/v2/definition/{ServiceName}`) before building payloads. Field names and valid values vary by P21 version.
2. **Use display values** - Set `UseCodeValues: false` for readability (e.g., `"Rate"` instead of internal codes).
3. **Validate labor codes** - Ensure `service_labor_id` values exist before referencing them in `TimeEntry` payloads. Use the `Labor` service or OData to look up valid codes.
4. **Include DatawindowName** - Always include `DatawindowName` in Interactive API v2 change requests. This is required in P21 25.2+.
5. **Check Summary on responses** - Always check `Summary.Succeeded` and `Summary.Failed` in Transaction API responses.
6. **Consider async for bulk** - Use the async Transaction endpoint (`/api/v2/transaction/async`) for large batches of labor entries to avoid session pool issues (note the default async queue capacity is 2).
7. **Time format** - The `time_worked` field uses `HH:MM` string format (e.g., `"4:00"` for 4 hours), not decimal hours.

---

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| 400 Bad Request | Malformed payload or missing required fields | Check against service definition |
| 401 Unauthorized | Invalid/expired token | Refresh authentication token |
| 500 on WorkCenter | Service may require licensing/config | Use Transaction API instead of Interactive |
| "Invalid technician" | Technician ID not found | Verify `technician_id` exists in P21 |
| "Invalid labor code" | Labor code not found | Verify `service_labor_id` via Labor service |
| "Production order not found" | Invalid `prod_order_number` | Verify order exists and is not cancelled |
| Status 2 (Failure) with no messages | Missing `DatawindowName` in v2 change | Add `DatawindowName` to change payload |

---

## Code Examples

See the `examples/python/production/` (Python) and `examples/csharp/Production/` (C#) directories for working examples.

---

## Related

- [Authentication](00-Authentication.md) -- Token generation
- [API Selection Guide](01-API-Selection-Guide.md) -- Which API to use when
- [Transaction API](03-Transaction-API.md) -- Stateless bulk operations (used by all production services)
- [Interactive API](04-Interactive-API.md) -- Stateful window interaction (for complex production workflows)
- [Batch Processing Patterns](09-Batch-Processing-Patterns.md) -- Patterns for bulk labor entry
