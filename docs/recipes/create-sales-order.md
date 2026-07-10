# Create a Sales Order

Create a sales order — header plus line items — in one stateless Transaction API call.

**API:** Transaction · **Service:** `Order` · **Deep dive:** [Create Order](../03-Transaction-API.md#create-order) · [Order Service Gotchas](../03-Transaction-API.md#order-service-gotchas) · **Full schema:** [Order.json](../../definitions/Order.json)

## Prerequisites

- Token + UI server URL (shared auth helper — see the [recipes README](README.md)).
- The customer, ship-to, contact, and items already exist; the items are stocked at the source location.
- **No assembly lines.** If a line should explode into components or spawn a production order, the Transaction API auto-answers the *"add as assembly?"* prompt **No** and kills the explode — use the [order-with-assembly](order-with-assembly.md) recipe for those.

## Payload

Two DataElements: the header form and the items list. Names come from the [service definition](../../definitions/Order.json) — `TABPAGE_1.order` (Form, datawindow `d_oe_header`, key `order_no`) and `TP_ITEMS.items` (List, datawindow `d_dw_oe_line_dataentry`, key `oe_order_item_id`).

The minimal example in the manual sends only `customer_id` + one item, but a **realistic header sets all of the fields below** — in particular `source_loc_id`, without which the save fails with a *"Jurisdiction ID for Order Header Tax"* error (see Gotchas).

```json
POST {ui_server}/api/v2/transaction

{
    "Name": "Order",
    "UseCodeValues": false,
    "Transactions": [{
        "Status": "New",
        "DataElements": [
            {
                "Name": "TABPAGE_1.order",
                "Type": "Form",
                "Keys": [],
                "Rows": [{
                    "Edits": [
                        {"Name": "customer_id",    "Value": "100198"},
                        {"Name": "sales_loc_id",   "Value": "10"},
                        {"Name": "source_loc_id",  "Value": "10"},
                        {"Name": "order_date",     "Value": "2030-01-05"},
                        {"Name": "requested_date", "Value": "2030-01-06"},
                        {"Name": "po_no",          "Value": "PO-TEST-001"},
                        {"Name": "taker",          "Value": "JSMITH"},
                        {"Name": "ship_to_id",     "Value": "200"},
                        {"Name": "contact_id",     "Value": "300"}
                    ],
                    "RelativeDateEdits": []
                }]
            },
            {
                "Name": "TP_ITEMS.items",
                "Type": "List",
                "Keys": [],
                "Rows": [
                    {
                        "Edits": [
                            {"Name": "oe_order_item_id", "Value": "WIDGET-001"},
                            {"Name": "unit_quantity",    "Value": "5"}
                        ],
                        "RelativeDateEdits": []
                    },
                    {
                        "Edits": [
                            {"Name": "oe_order_item_id", "Value": "WIDGET-002"},
                            {"Name": "unit_quantity",    "Value": "2"}
                        ],
                        "RelativeDateEdits": []
                    }
                ]
            }
        ]
    }]
}
```

Do **not** send `company_id` — it is a disabled column on the Order window. For every other field the service accepts, load [`definitions/Order.json`](../../definitions/Order.json).

## Complete example

<!-- tabs -->
```python
BASE_URL = "https://play.p21server.com"
USERNAME = "api_user"
PASSWORD = "api_pass"

token, ui_server, headers = p21_auth(BASE_URL, USERNAME, PASSWORD)

payload = {
    "Name": "Order",
    "UseCodeValues": False,
    "Transactions": [{
        "Status": "New",
        "DataElements": [
            {
                "Name": "TABPAGE_1.order",
                "Type": "Form",
                "Keys": [],
                "Rows": [{
                    "Edits": [
                        {"Name": "customer_id",    "Value": "100198"},
                        {"Name": "sales_loc_id",   "Value": "10"},
                        {"Name": "source_loc_id",  "Value": "10"},   # required in practice
                        {"Name": "order_date",     "Value": "2030-01-05"},
                        {"Name": "requested_date", "Value": "2030-01-06"},  # must be AFTER order_date
                        {"Name": "po_no",          "Value": "PO-TEST-001"},
                        {"Name": "taker",          "Value": "JSMITH"},
                        {"Name": "ship_to_id",     "Value": "200"},
                        {"Name": "contact_id",     "Value": "300"},
                    ],
                    "RelativeDateEdits": [],
                }],
            },
            {
                "Name": "TP_ITEMS.items",
                "Type": "List",
                "Keys": [],
                "Rows": [
                    {"Edits": [
                        {"Name": "oe_order_item_id", "Value": "WIDGET-001"},
                        {"Name": "unit_quantity",    "Value": "5"},
                    ], "RelativeDateEdits": []},
                    {"Edits": [
                        {"Name": "oe_order_item_id", "Value": "WIDGET-002"},
                        {"Name": "unit_quantity",    "Value": "2"},
                    ], "RelativeDateEdits": []},
                ],
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
    raise SystemExit("Order create failed")

# The generated order_no comes back in the result rows of TABPAGE_1.order
order_no = None
for txn in result["Results"]["Transactions"]:
    if txn.get("Status") != "Passed":
        continue
    for element in txn.get("DataElements", []):
        if element.get("Name") != "TABPAGE_1.order":
            continue
        for row in element.get("Rows", []):
            for edit in row.get("Edits", []):
                if edit.get("Name") == "order_no":
                    order_no = edit.get("Value")

print(f"Created order_no: {order_no}")
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
    ["Name"] = "Order",
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
                    ["Name"] = "TABPAGE_1.order",
                    ["Type"] = "Form",
                    ["Keys"] = new JArray(),
                    ["Rows"] = new JArray
                    {
                        Row(("customer_id", "100198"),
                            ("sales_loc_id", "10"),
                            ("source_loc_id", "10"),          // required in practice
                            ("order_date", "2030-01-05"),
                            ("requested_date", "2030-01-06"), // must be AFTER order_date
                            ("po_no", "PO-TEST-001"),
                            ("taker", "JSMITH"),
                            ("ship_to_id", "200"),
                            ("contact_id", "300")),
                    },
                },
                new JObject
                {
                    ["Name"] = "TP_ITEMS.items",
                    ["Type"] = "List",
                    ["Keys"] = new JArray(),
                    ["Rows"] = new JArray
                    {
                        Row(("oe_order_item_id", "WIDGET-001"), ("unit_quantity", "5")),
                        Row(("oe_order_item_id", "WIDGET-002"), ("unit_quantity", "2")),
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

// HTTP 200 even on failure -- check the Summary, never the status code
var succeeded = (int)result["Summary"]!["Succeeded"]!;
var failed = (int)result["Summary"]!["Failed"]!;
Console.WriteLine($"Succeeded: {succeeded}, Failed: {failed}");
if (failed > 0 || succeeded == 0)
{
    foreach (var msg in result["Messages"] ?? new JArray())
        Console.WriteLine(msg);
    throw new InvalidOperationException("Order create failed");
}

// The generated order_no comes back in the result rows of TABPAGE_1.order
var orderNo = result.SelectTokens(
        "$.Results.Transactions[?(@.Status == 'Passed')].DataElements[?(@.Name == 'TABPAGE_1.order')].Rows[*].Edits[?(@.Name == 'order_no')].Value")
    .FirstOrDefault()?.ToString();

Console.WriteLine($"Created order_no: {orderNo}");
```
<!-- /tabs -->

> **End-to-end files** (runnable from the repo with a `.env`, dry-run by default): [`scripts/recipes/create_sales_order.py`](../../scripts/recipes/create_sales_order.py) · [`examples/csharp/Recipes/CreateSalesOrder.cs`](../../examples/csharp/Recipes/CreateSalesOrder.cs). The snippet above is self-contained; the files use the repo's shared `common` / `P21Examples.Common` helpers like every other example.

## Gotchas

All verified live — details in [Order Service Gotchas](../03-Transaction-API.md#order-service-gotchas):

- **`source_loc_id` is effectively required.** Omitting it fails with a *"Jurisdiction ID for Order Header Tax"* error — the tax jurisdiction does not auto-populate through the API the way it does in the UI.
- **`requested_date` must be after `order_date`.** The same date trips a date-cascade prompt, which the stateless API can't answer.
- **`company_id` is a disabled column** on the Order window — don't send it.
- **DynaChange prompts are auto-answered with the default** (usually "No"), which silently discards the affected line — e.g. *"order line does not have a PO Cost… proceed? [No]"*. On multi-item orders the remaining lines then cascade-fail. This is a P21 configuration matter (exempt the rule for the API user, or fix the data), not something a payload change can work around — see [DynaChange and Popup Handling](../03-Transaction-API.md#dynachange-and-popup-handling).
- **Assembly items cannot be entered via the Transaction API** when they should explode or spawn a production order — the *"add as assembly?"* prompt is auto-answered **No**, killing the explode. Use the [order-with-assembly](order-with-assembly.md) recipe (Interactive API) for those lines.
- **HTTP 200 ≠ success.** The created `order_no` comes back in the result rows; check `Summary.Succeeded` and `Results.Transactions[].Status == "Passed"`, never the HTTP status. Transactions in one POST pass/fail independently.

## Verify

Read the order back — a `Succeeded` response is not proof every value landed:

```http
GET {base_url}/odataservice/odata/table/oe_hdr?$filter=order_no eq '1013938'
GET {base_url}/odataservice/odata/table/oe_line?$filter=order_no eq '1013938'
```

Confirm the header fields you sent (`taker`, `po_no`, dates, ship-to) and that **every** line row exists — a DynaChange auto-answer can drop a line while the transaction still reports `Succeeded` (see Gotchas).

> **Credit:** [Alex Westemeier](https://github.com/AWestemeier)
