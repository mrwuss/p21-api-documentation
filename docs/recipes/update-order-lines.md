# Modify an Existing Sales Order

Change a line's quantity in place and add a new line to an existing sales order — one stateless Transaction API POST, no session, no window.

**API:** Transaction · **Service:** `Order` · **Deep dive:** [Keys — Row Identity and the Collapse Trap](../03-Transaction-API.md#keys-row-identity-and-the-collapse-trap) · [Design for updates: line handles](../03-Transaction-API.md#design-for-updates-assign-your-own-line-handles) · **Full schema:** [Order.json](../../definitions/Order.json)

Everything here was verified live on 26.1 (August 2026) with `/transaction/get` read-backs: the in-place update, the insert, both together in one POST, and every gotcha below.

## Prerequisites

- P21 credentials — the complete example below authenticates itself; nothing to install but `httpx` (Python) or a bare `net9.0` console project (C#).
- An existing, editable order (not fully invoiced/closed) that is **not an RMA** — see the RMA gotcha below.
- **Know each target line's `user_line_no`.** It is the stable update key. If your integration created the order, you ideally [assigned handles at create time](../03-Transaction-API.md#design-for-updates-assign-your-own-line-handles); otherwise read them back first (see [Finding the handles](#finding-the-handles)).

## How it works

A keyed `Status: "New"` row is an [upsert](../03-Transaction-API.md#upsert-semantics-keyed-rows-insert-when-absent): when the key matches an existing row it **updates** that row, when it doesn't it **inserts** a new one. So one `TP_ITEMS.items` element keyed on `user_line_no` does both jobs — send an existing handle to edit that line, a new handle to add a line.

The header element does the *loading*: `Keys: ["order_no"]` with `order_no` as its only edit.

## Payload

Updates line `010` to quantity 4 and adds a new line `030` — in one transaction:

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
                "Keys": ["order_no"],
                "Rows": [{
                    "Edits": [
                        {"Name": "order_no", "Value": "1013938"}
                    ],
                    "RelativeDateEdits": []
                }]
            },
            {
                "Name": "TP_ITEMS.items",
                "Type": "List",
                "Keys": ["user_line_no"],
                "Rows": [
                    {
                        "Edits": [
                            {"Name": "user_line_no",     "Value": "010"},
                            {"Name": "oe_order_item_id", "Value": "WIDGET-001"},
                            {"Name": "unit_quantity",    "Value": "4"}
                        ],
                        "RelativeDateEdits": []
                    },
                    {
                        "Edits": [
                            {"Name": "user_line_no",     "Value": "030"},
                            {"Name": "oe_order_item_id", "Value": "WIDGET-002"},
                            {"Name": "unit_quantity",    "Value": "1"}
                        ],
                        "RelativeDateEdits": []
                    }
                ]
            }
        ]
    }]
}
```

> **Payload files** (validator-verified): [JSON](../../examples/payloads/json/update-order-lines.json) · [XML](../../examples/payloads/xml/update-order-lines.xml)

## Finding the handles

When you don't know the order's `user_line_no` values, read them back first — `POST /api/v2/transaction/get` returns every line with its handle:

```json
POST {ui_server}/api/v2/transaction/get

{
    "ServiceName": "Order",
    "TransactionStates": [{
        "DataElementName": "TABPAGE_1.order",
        "Keys": [{"Name": "order_no", "Value": "1013938"}]
    }]
}
```

Walk the response's `TP_ITEMS.items` rows and map `user_line_no` → (`oe_order_item_id`, `unit_quantity`). P21 auto-assigns `001`, `002`, … when the creator didn't.

## Complete example

<!-- tabs -->

**Python**

```python
"""Modify an existing sales order: update a line in place + add a line.

Dry run by default; pass --execute to POST. Mirrors docs/recipes/update-order-lines.md.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from common.auth import get_token, get_auth_headers, get_ui_server_url
from common.config import load_config

import warnings
warnings.filterwarnings("ignore")

# --- Configuration (generic placeholders -- substitute your own) ------------
ORDER_NO = "1013938"

# (user_line_no, item_id, quantity)
# An EXISTING handle updates that line; a NEW handle inserts a line.
LINES = [
    ("010", "WIDGET-001", "4"),   # existing handle -> quantity updated in place
    ("030", "WIDGET-002", "1"),   # new handle      -> line inserted
]


def build_payload() -> dict:
    """Header loads the order by key; the keyed items list upserts each row."""
    return {
        "Name": "Order",
        "UseCodeValues": False,
        "Transactions": [{
            "Status": "New",
            "DataElements": [
                {
                    "Name": "TABPAGE_1.order",
                    "Type": "Form",
                    "Keys": ["order_no"],
                    # ONLY the key. Re-sending header fields fails on
                    # disabled columns (customer_id) once the order exists.
                    "Rows": [{
                        "Edits": [{"Name": "order_no", "Value": ORDER_NO}],
                        "RelativeDateEdits": [],
                    }],
                },
                {
                    "Name": "TP_ITEMS.items",
                    "Type": "List",
                    "Keys": ["user_line_no"],
                    "Rows": [
                        {"Edits": [
                            {"Name": "user_line_no",     "Value": handle},
                            {"Name": "oe_order_item_id", "Value": item_id},
                            {"Name": "unit_quantity",    "Value": qty},
                        ], "RelativeDateEdits": []}
                        for handle, item_id, qty in LINES
                    ],
                },
            ],
        }],
    }


def read_lines(ui_server: str, headers: dict, verify_ssl: bool) -> list[dict]:
    """Read the order's lines back -- the only proof the write landed."""
    resp = httpx.post(
        f"{ui_server}/api/v2/transaction/get",
        headers=headers, verify=verify_ssl, follow_redirects=True, timeout=120,
        json={"ServiceName": "Order", "TransactionStates": [{
            "DataElementName": "TABPAGE_1.order",
            "Keys": [{"Name": "order_no", "Value": ORDER_NO}],
        }]},
    )
    resp.raise_for_status()
    for element in resp.json()["Transactions"][0]["DataElements"]:
        if element["Name"] != "TP_ITEMS.items":
            continue
        rows = [{edit["Name"]: edit["Value"] for edit in row.get("Edits", [])}
                for row in element.get("Rows", [])]
        return [row for row in rows if row.get("oe_order_item_id")]
    return []


def main() -> None:
    """Entry point: build the payload, POST on --execute, read the lines back."""
    parser = argparse.ArgumentParser(
        description="Modify an existing sales order (docs/recipes/update-order-lines.md)")
    parser.add_argument("--execute", action="store_true",
                        help="Actually POST the transaction (default: dry run)")
    args = parser.parse_args()

    print("Recipe - Modify an Existing Sales Order")
    print("=" * 60)

    payload = build_payload()
    if not args.execute:
        print("\nDRY RUN - would POST to {ui_server}/api/v2/transaction:")
        print(json.dumps(payload, indent=2))
        print("\nRe-run with --execute to POST the transaction.")
        return

    config = load_config()
    token_data = get_token(config)
    headers = get_auth_headers(token_data["AccessToken"])
    ui_server = get_ui_server_url(config.base_url, token_data["AccessToken"],
                                  config.verify_ssl)
    print(f"UI Server: {ui_server}")

    print("\nBefore:")
    for row in read_lines(ui_server, headers, config.verify_ssl):
        print(f"  {row.get('user_line_no')}: {row.get('oe_order_item_id')}"
              f" x {row.get('unit_quantity')}")

    resp = httpx.post(f"{ui_server}/api/v2/transaction", headers=headers,
                      json=payload, verify=config.verify_ssl,
                      follow_redirects=True, timeout=120)
    resp.raise_for_status()          # HTTP 200 does NOT mean the write succeeded
    result = resp.json()
    print(f"\nSummary: {result['Summary']}")
    for message in result.get("Messages") or []:
        print(f"  Message: {message}")

    print("\nAfter (read-back is the only proof):")
    for row in read_lines(ui_server, headers, config.verify_ssl):
        print(f"  {row.get('user_line_no')}: {row.get('oe_order_item_id')}"
              f" x {row.get('unit_quantity')}")


if __name__ == "__main__":
    main()
```

**C#**

```csharp
// Modify an existing sales order: update a line in place + add a line.
// Mirrors docs/recipes/update-order-lines.md. See the runnable class at
// examples/csharp/Recipes/UpdateOrderLines.cs (menu option in the Recipes
// project; prints the payload and asks for EXECUTE before posting).

using System.Text;
using Newtonsoft.Json.Linq;
using P21Examples.Common;
using static P21Examples.Recipes.RecipeHelpers;

namespace P21Examples.Recipes;

public static class UpdateOrderLines
{
    private const string OrderNo = "1013938";

    // (handle, item, qty): existing handle -> update; new handle -> insert.
    private static readonly (string Handle, string ItemId, string Qty)[] Lines =
    {
        ("010", "WIDGET-001", "4"),
        ("030", "WIDGET-002", "1"),
    };

    public static async Task RunAsync()
    {
        Console.WriteLine("Recipe - Modify an Existing Sales Order");
        Console.WriteLine(new string('=', 60));

        using var client = await P21Client.CreateAsync();

        Console.WriteLine("\nBefore:");
        await PrintLinesAsync();

        var payload = BuildPayload();
        PrintPayload("Payload", payload);
        if (!ConfirmExecute())
            return;

        var result = await client.Transaction.CreateAsync(payload);
        if (!CheckResult(result))
            return;

        Console.WriteLine("\nAfter (read-back is the only proof):");
        await PrintLinesAsync();
    }

    private static JObject BuildPayload()
    {
        var itemRows = new JArray();
        foreach (var (handle, itemId, qty) in Lines)
        {
            itemRows.Add(new JObject
            {
                ["Edits"] = new JArray
                {
                    Edit("user_line_no", handle),
                    Edit("oe_order_item_id", itemId),
                    Edit("unit_quantity", qty),
                },
                ["RelativeDateEdits"] = new JArray(),
            });
        }

        return new JObject
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
                            // ONLY the key -- re-sending header fields fails on
                            // disabled columns (customer_id) once the order exists.
                            ["Name"] = "TABPAGE_1.order", ["Type"] = "Form",
                            ["Keys"] = new JArray { "order_no" },
                            ["Rows"] = new JArray { new JObject {
                                ["Edits"] = new JArray { Edit("order_no", OrderNo) },
                                ["RelativeDateEdits"] = new JArray() } },
                        },
                        new JObject
                        {
                            ["Name"] = "TP_ITEMS.items", ["Type"] = "List",
                            ["Keys"] = new JArray { "user_line_no" },
                            ["Rows"] = itemRows,
                        },
                    },
                },
            },
        };
    }

    private static async Task PrintLinesAsync()
    {
        var (http, uiServer, _) = await CreateRawClientAsync();
        var request = new JObject
        {
            ["ServiceName"] = "Order",
            ["TransactionStates"] = new JArray { new JObject {
                ["DataElementName"] = "TABPAGE_1.order",
                ["Keys"] = new JArray { new JObject {
                    ["Name"] = "order_no", ["Value"] = OrderNo } } } },
        };
        var response = await http.PostAsync(
            $"{uiServer}/api/v2/transaction/get",
            new StringContent(request.ToString(), Encoding.UTF8, "application/json"));
        response.EnsureSuccessStatusCode();

        var body = JObject.Parse(await response.Content.ReadAsStringAsync());
        foreach (var element in body["Transactions"]![0]!["DataElements"]!)
        {
            if ((string?)element["Name"] != "TP_ITEMS.items")
                continue;
            foreach (var row in element["Rows"]!)
            {
                var edits = row["Edits"]!.ToDictionary(
                    e => (string)e["Name"]!, e => (string?)e["Value"]);
                if (string.IsNullOrEmpty(edits.GetValueOrDefault("oe_order_item_id")))
                    continue;
                Console.WriteLine(
                    $"  {edits.GetValueOrDefault("user_line_no")}: " +
                    $"{edits.GetValueOrDefault("oe_order_item_id")} x " +
                    $"{edits.GetValueOrDefault("unit_quantity")}");
            }
        }
    }
}
```

<!-- /tabs -->

> **End-to-end files** (runnable from the repo with a `.env`, dry-run by default): [`examples/python/recipes/update_order_lines.py`](../../examples/python/recipes/update_order_lines.py) · [`examples/csharp/Recipes/UpdateOrderLines.cs`](../../examples/csharp/Recipes/UpdateOrderLines.cs). The snippets above are self-contained; the files use the repo's shared `common` / `P21Examples.Common` helpers like every other example.

## Gotchas

All verified live on 26.1 — details in [Keys — Row Identity and the Collapse Trap](../03-Transaction-API.md#keys-row-identity-and-the-collapse-trap):

- **Send only `order_no` in the header element.** Re-sending create-time header fields fails the update on disabled columns — `Column is disabled: customer_id` was the verified refusal. The header's job here is loading the order, nothing more.
- **Key on `user_line_no`, not on data fields.** Keying on `unit_quantity` (or any field you're changing) means the new value no longer matches the row's key — the "update" silently **appends a new line** with `Succeeded: 1`. Verified: a qty 10→20 edit keyed on `unit_quantity` produced a third line.
- **`user_line_no` must be in each row's `Edits`.** A key field that isn't sent fails the transaction with the opaque `General Exception: Sequence contains no matching element`.
- **A new handle inserts; that's the feature and the risk.** A typo'd handle doesn't error — it quietly adds a line. The read-back below catches it.
- **DynaChange prompts are auto-answered with the default** — same as order creation; a dropped change still reports `Succeeded`. See [create-sales-order § Gotchas](create-sales-order.md#gotchas).
- **RMAs need a different service.** An order with `oe_hdr.rma_flag = 'Y'` cannot be loaded through `Order` at all — it fails with `You cannot retrieve an RMA from the Order Entry/Front Counter window.` Use the **`RMA`** service instead: identical `TABPAGE_1.order` form, keyed the same way, same fields. Bulk jobs over open orders hit this routinely, so route per order on `rma_flag` rather than discovering it as a failure. See [03 § RMA Service](../03-Transaction-API.md#rma-service-orders-the-order-service-refuses).
- **HTTP 200 ≠ success.** Check `Summary` and `Results.Transactions[].Status == "Passed"`.

## Verify

Read the order back — a `Succeeded` response is not proof:

- `POST /api/v2/transaction/get` (as in the example) and compare every line: the edited handle carries the new quantity, the new handle exists, and **no unexpected extra lines appeared** (the signature of a key problem).
- Or via OData: `GET /odataservice/odata/view/p21_view_oe_line?$filter=order_no eq '1013938'`.
