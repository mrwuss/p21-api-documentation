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
| `JobContractPricing` | Job contract pricing |
| `WorkCenter` | Work center maintenance |
| `Operation` | Operation definitions |
| `PredefinedRouting` | Routing templates |
| `Assembly` | Assembly maintenance |
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
| `technician_id` | Char | Yes | Technician/worker ID |
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

### Example: Record Labor Hours

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
                        {"Name": "technician_id", "Value": "TECH001"},
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
                                new JObject { ["Name"] = "technician_id", ["Value"] = "TECH001" },
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
                                new JObject { ["Name"] = "prod_order_number", ["Value"] = 1001 },
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
import httpx

# After authentication and getting ui_server_url...
headers = {"Authorization": "Bearer <token>", "Content-Type": "application/json", "Accept": "application/json"}

# Open Production Order Entry window
open_payload = {
    "ServiceName": "ProductionOrder",
    "ResponseWindowHandlingEnabled": False
}

response = httpx.post(
    f"{ui_server_url}/api/ui/interactive/v2/window",
    headers=headers,
    json=open_payload,
    verify=False
)
response.raise_for_status()
result = response.json()
window_id = result["WindowId"]
print(f"Window opened: {window_id}")

# Retrieve a production order
change_payload = {
    "WindowId": window_id,
    "Changes": [{
        "TabName": "TABPAGE_1",
        "DatawindowName": "tp_1_dw_1",
        "FieldName": "prod_order_number",
        "Value": "1001"
    }]
}

response = httpx.put(
    f"{ui_server_url}/api/ui/interactive/v2/change",
    headers=headers,
    json=change_payload,
    verify=False
)
response.raise_for_status()

# Read current window data
response = httpx.get(
    f"{ui_server_url}/api/ui/interactive/v2/data",
    params={"id": window_id},
    headers=headers,
    verify=False
)
response.raise_for_status()
data = response.json()
```

```csharp
// Open Production Order Entry window
var openPayload = new JObject
{
    ["ServiceName"] = "ProductionOrder",
    ["ResponseWindowHandlingEnabled"] = false
};

var openContent = new StringContent(
    openPayload.ToString(), Encoding.UTF8, "application/json");
var openResp = await client.PostAsync(
    $"{uiServerUrl}/api/ui/interactive/v2/window", openContent);
openResp.EnsureSuccessStatusCode();

var openResult = JObject.Parse(
    await openResp.Content.ReadAsStringAsync());
var windowId = openResult["WindowId"].ToString();
Console.WriteLine($"Window opened: {windowId}");

// Retrieve a production order
var changePayload = new JObject
{
    ["WindowId"] = windowId,
    ["Changes"] = new JArray
    {
        new JObject
        {
            ["TabName"] = "TABPAGE_1",
            ["DatawindowName"] = "tp_1_dw_1",
            ["FieldName"] = "prod_order_number",
            ["Value"] = "1001"
        }
    }
};

var changeContent = new StringContent(
    changePayload.ToString(), Encoding.UTF8, "application/json");
var changeResp = await client.PutAsync(
    $"{uiServerUrl}/api/ui/interactive/v2/change", changeContent);
changeResp.EnsureSuccessStatusCode();

// Read current window data
var dataResp = await client.GetAsync(
    $"{uiServerUrl}/api/ui/interactive/v2/data?id={windowId}");
dataResp.EnsureSuccessStatusCode();
var data = JObject.Parse(
    await dataResp.Content.ReadAsStringAsync());
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
import httpx

# After authentication...
headers = {"Authorization": "Bearer <token>", "Content-Type": "application/json", "Accept": "application/json"}

# Query production orders (after enabling in SOA Admin)
response = httpx.get(
    f"{base_url}/api/dataaccess/v1/prod_order_hdr",
    params={"$filter": "company_id eq 'ACME'", "$top": "10"},
    headers=headers,
    verify=False
)
response.raise_for_status()
orders = response.json()["value"]
for order in orders:
    print(f"PO# {order['prod_order_number']}: {order['complete']}")
```

```csharp
var response = await client.GetAsync(
    $"{baseUrl}/api/dataaccess/v1/prod_order_hdr" +
    "?$filter=company_id eq 'ACME'&$top=10");
response.EnsureSuccessStatusCode();

var data = JObject.Parse(
    await response.Content.ReadAsStringAsync());
var orders = data["value"] as JArray;
foreach (var order in orders)
{
    Console.WriteLine(
        $"PO# {order["prod_order_number"]}: {order["complete"]}");
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
6. **Consider async for bulk** - Use the async Transaction endpoint (`/api/v2/transaction/async`) for large batches of labor entries to avoid session pool issues.
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

See the `scripts/production/` (Python) and `examples/csharp/Production/` (C#) directories for working examples.

---

## Related

- [Authentication](00-Authentication.md) -- Token generation
- [API Selection Guide](01-API-Selection-Guide.md) -- Which API to use when
- [Transaction API](03-Transaction-API.md) -- Stateless bulk operations (used by all production services)
- [Interactive API](04-Interactive-API.md) -- Stateful window interaction (for complex production workflows)
- [Batch Processing Patterns](09-Batch-Processing-Patterns.md) -- Patterns for bulk labor entry
