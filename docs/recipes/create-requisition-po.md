# Create a Requisition Purchase Order

Create a **requisition PO** — P21's internal / not-for-resale purchasing type — in one stateless Transaction API call. The result is a PO with `po_hdr.po_type = 'R'`.

**API:** Transaction · **Service:** `RequisitionPurchaseOrder` · **Deep dive:** [Purchase Order Types](../03-Transaction-API.md#purchase-order-types-and-the-disabled-po_hdr_po_type-column) · **Full schema:** [RequisitionPurchaseOrder.json](../../definitions/RequisitionPurchaseOrder.json)

## Why a separate service

You **cannot** set the PO type by writing `po_hdr_po_type` on the `PurchaseOrder` service — it is a disabled column (`Column is disabled: po_hdr_po_type`). You pick the type by choosing the **type-specific service**. `RequisitionPurchaseOrder` is that service for requisition POs — same window as PO Entry (`w_purchase_order_entry_sheet`), type preset to Requisition. It's a listed service in `/api/v2/services` but easy to miss.

## Prerequisites

- Token + UI server URL (shared auth helper — see the [recipes README](README.md)).
- The **item is flagged as a requisition item** at the PO location (`inv_loc.requisition = 'Y'`). *Only requisition items may be purchased on a requisition PO* — this is enforced at the API layer.
- You have the **vendor id** and its **supplier id** — these are different numbers (e.g. vendor `21445` "Acme Technology Corp" ↔ supplier `22132` "ACME-PENNSYLVANIA"). Passing a supplier id as `vendor_id` fails with *"Record specified was not found."*

## Payload

Header (`TABPAGE_1.tp_1_dw_1`, Form, key `po_no`) + line grid (`TABPAGE_17.tp_17_dw_17`, List, keys `line_no`/`item_id`). `po_no` is auto-assigned and returned in the result rows.

```json
POST {ui_server}/api/v2/transaction

{
    "Name": "RequisitionPurchaseOrder",
    "UseCodeValues": false,
    "Transactions": [{
        "Status": "New",
        "DataElements": [
            {
                "Name": "TABPAGE_1.tp_1_dw_1",
                "Type": "Form",
                "Keys": [],
                "Rows": [{
                    "Edits": [
                        {"Name": "location_id",        "Value": "10"},
                        {"Name": "vendor_id",          "Value": "21445"},
                        {"Name": "vendor_supplier_id", "Value": "22132"}
                    ],
                    "RelativeDateEdits": []
                }]
            },
            {
                "Name": "TABPAGE_17.tp_17_dw_17",
                "Type": "List",
                "Keys": [],
                "Rows": [{
                    "Edits": [
                        {"Name": "item_id",       "Value": "WIDGET-001"},
                        {"Name": "unit_quantity", "Value": "10"}
                    ],
                    "RelativeDateEdits": []
                }]
            }
        ]
    }]
}
```

The definition also marks `company_id`, `division_id`, `buyer_id`, `order_date`, and `required_date` required on the header, and `unit_of_measure` / `pricing_unit` required on the line — these are supplied by the **defaults template** (`GET {ui_server}/api/v2/defaults/RequisitionPurchaseOrder`) and the item's default UOM. For every field the service accepts, load [`definitions/RequisitionPurchaseOrder.json`](../../definitions/RequisitionPurchaseOrder.json).

## Complete example

<!-- tabs -->
```python
import httpx  # p21_auth() from recipes/README.md

BASE_URL = "https://play.p21server.com"
USERNAME = "api_user"
PASSWORD = "api_pass"

token, ui_server, headers = p21_auth(BASE_URL, USERNAME, PASSWORD)

payload = {
    "Name": "RequisitionPurchaseOrder",
    "UseCodeValues": False,
    "Transactions": [{
        "Status": "New",
        "DataElements": [
            {
                "Name": "TABPAGE_1.tp_1_dw_1",
                "Type": "Form",
                "Keys": [],
                "Rows": [{
                    "Edits": [
                        {"Name": "location_id",        "Value": "10"},
                        {"Name": "vendor_id",          "Value": "21445"},
                        {"Name": "vendor_supplier_id", "Value": "22132"},  # header, NOT the line
                    ],
                    "RelativeDateEdits": [],
                }],
            },
            {
                "Name": "TABPAGE_17.tp_17_dw_17",
                "Type": "List",
                "Keys": [],
                "Rows": [{
                    "Edits": [
                        {"Name": "item_id",       "Value": "WIDGET-001"},  # must be a requisition item
                        {"Name": "unit_quantity", "Value": "10"},
                    ],
                    "RelativeDateEdits": [],
                }],
            },
        ],
    }],
}

response = httpx.post(
    f"{ui_server}/api/v2/transaction",
    headers=headers, json=payload, verify=False, timeout=120,
)
response.raise_for_status()
result = response.json()

# HTTP 200 even on failure -- check the Summary, never the status code
summary = result["Summary"]
print(f"Succeeded: {summary['Succeeded']}, Failed: {summary['Failed']}")
if summary["Failed"] > 0 or summary["Succeeded"] == 0:
    for msg in result.get("Messages", []):
        print(msg)
    raise SystemExit("Requisition PO create failed")

# The generated po_no comes back in the TABPAGE_1.tp_1_dw_1 result rows
po_no = None
for txn in result["Results"]["Transactions"]:
    if txn.get("Status") != "Passed":
        continue
    for element in txn.get("DataElements", []):
        if element.get("Name") != "TABPAGE_1.tp_1_dw_1":
            continue
        for row in element.get("Rows", []):
            for edit in row.get("Edits", []):
                if edit.get("Name") == "po_no":
                    po_no = edit.get("Value")

print(f"Created po_no: {po_no}")

# Read back via OData -- confirm po_type == 'R'
hdr = httpx.get(
    f"{BASE_URL}/odataservice/odata/table/po_hdr",
    params={"$filter": f"po_no eq {po_no}", "$select": "po_no,po_type,vendor_id"},
    headers=headers, verify=False,
)
hdr.raise_for_status()
for row in hdr.json()["value"]:
    print(f"  po_no={row['po_no']} po_type={row['po_type']} (expected R) vendor_id={row['vendor_id']}")
```

```csharp
var session = await P21Session.CreateAsync(
    "https://play.p21server.com", "api_user", "api_pass");

JObject Row(params (string Name, string Value)[] edits) => new JObject
{
    ["Edits"] = new JArray(edits.Select(e =>
        new JObject { ["Name"] = e.Name, ["Value"] = e.Value })),
    ["RelativeDateEdits"] = new JArray(),
};

var payload = new JObject
{
    ["Name"] = "RequisitionPurchaseOrder",
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
                    ["Name"] = "TABPAGE_1.tp_1_dw_1",
                    ["Type"] = "Form",
                    ["Keys"] = new JArray(),
                    ["Rows"] = new JArray
                    {
                        Row(("location_id", "10"),
                            ("vendor_id", "21445"),
                            ("vendor_supplier_id", "22132")),   // header, NOT the line
                    },
                },
                new JObject
                {
                    ["Name"] = "TABPAGE_17.tp_17_dw_17",
                    ["Type"] = "List",
                    ["Keys"] = new JArray(),
                    ["Rows"] = new JArray
                    {
                        Row(("item_id", "WIDGET-001"),           // must be a requisition item
                            ("unit_quantity", "10")),
                    },
                },
            },
        },
    },
};

var response = await session.Http.PostAsync(
    $"{session.UiServer}/api/v2/transaction",
    new StringContent(payload.ToString(), Encoding.UTF8, "application/json"));
response.EnsureSuccessStatusCode();
var result = JObject.Parse(await response.Content.ReadAsStringAsync());

var succeeded = (int)result["Summary"]!["Succeeded"]!;
var failed = (int)result["Summary"]!["Failed"]!;
Console.WriteLine($"Succeeded: {succeeded}, Failed: {failed}");
if (failed > 0 || succeeded == 0)
{
    foreach (var msg in result["Messages"] ?? new JArray())
        Console.WriteLine(msg);
    throw new InvalidOperationException("Requisition PO create failed");
}

var poNo = result.SelectTokens(
        "$.Results.Transactions[?(@.Status == 'Passed')].DataElements[?(@.Name == 'TABPAGE_1.tp_1_dw_1')].Rows[*].Edits[?(@.Name == 'po_no')].Value")
    .FirstOrDefault()?.ToString();

Console.WriteLine($"Created po_no: {poNo}");
```
<!-- /tabs -->

> **End-to-end files** (runnable from the repo with a `.env`, dry-run by default): [`examples/python/recipes/create_requisition_po.py`](../../examples/python/recipes/create_requisition_po.py) · [`examples/csharp/Recipes/CreateRequisitionPo.cs`](../../examples/csharp/Recipes/CreateRequisitionPo.cs).

## Gotchas (verified live on Play 26.1.5894.1, 2026-07)

- **`vendor_supplier_id` goes on the header, but omitting it fails at the *line* with a misleading message:** *"A supplier ID must be entered. DataElement: tp_17_dw_17, Column: item_id"*. The pointer to the line's `item_id` is wrong — the fix is `vendor_supplier_id` on `TABPAGE_1.tp_1_dw_1`.
- **`vendor_id` ≠ `supplier_id`.** They are different ids on different records. Passing a supplier id where `vendor_id` belongs fails with *"Record specified was not found."*
- **Only requisition items are allowed.** The line item must have `inv_loc.requisition = 'Y'` at the PO location, or the create fails with *"Only requisition items may be purchased on a requisition PO."*
- **Type is chosen by the service, not a field.** Do not send `po_hdr_po_type` — it is disabled. `RequisitionPurchaseOrder` produces `po_hdr.po_type = 'R'` (verified). See the [PO type letter table](../03-Transaction-API.md#purchase-order-types-and-the-disabled-po_hdr_po_type-column).
- **HTTP 200 ≠ success.** Check `Summary.Succeeded` and `Results.Transactions[].Status == "Passed"`; the generated `po_no` comes back in the result rows.

## Verify

```http
GET {base_url}/odataservice/odata/table/po_hdr?$filter=po_no eq 12345&$select=po_no,po_type,vendor_id
GET {base_url}/odataservice/odata/table/po_line?$filter=po_no eq 12345
```

Confirm `po_type` is `R` and every line you submitted is present.
