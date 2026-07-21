# Create a Customer

Create a customer master record in one stateless Transaction API call. `customer_id` is auto-assigned and returned in the response.

**API:** Transaction · **Service:** `Customer` · **Deep dive:** [Transaction API](../03-Transaction-API.md) · **Full schema:** [Customer.json](../../definitions/Customer.json)

## Prerequisites

- Token + UI server URL (shared auth helper — see the [recipes README](README.md)).
- The salesrep exists (`salesrep_id`) and the branch exists (`default_branch`).

## What the defaults template already fills

The `Customer` defaults template (`GET {ui_server}/api/v2/defaults/Customer`) prefills `company_id`, `terms_id` ("To Be Determined"), and `customer_type_cd`. So a minimal create only has to supply:

- **`TABPAGE_1.tp_1_dw_1`** (Form): `customer_name`, `salesrep_id`, and the mailing-address fields.
- **`SHIP_TO_GENERAL.ship_to_general`** (Form): `default_branch`.

`customer_id` is auto-assigned — leave it out; the generated value comes back in the result rows (key: `company_id` + `customer_id`).

## Payload

```json
POST {ui_server}/api/v2/transaction

{
    "Name": "Customer",
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
                        {"Name": "customer_name",    "Value": "ACME Industrial Supply"},
                        {"Name": "salesrep_id",      "Value": "100"},
                        {"Name": "mail_address1",    "Value": "123 Main St"},
                        {"Name": "mail_city",        "Value": "Des Moines"},
                        {"Name": "mail_state",       "Value": "IA"},
                        {"Name": "mail_postal_code", "Value": "50309"},
                        {"Name": "mail_country",     "Value": "USA"}
                    ],
                    "RelativeDateEdits": []
                }]
            },
            {
                "Name": "SHIP_TO_GENERAL.ship_to_general",
                "Type": "Form",
                "Keys": [],
                "Rows": [{
                    "Edits": [
                        {"Name": "default_branch", "Value": "10"}
                    ],
                    "RelativeDateEdits": []
                }]
            }
        ]
    }]
}
```

For every other field the service accepts, load [`definitions/Customer.json`](../../definitions/Customer.json).

## Complete example

<!-- tabs -->
```python
import httpx  # p21_auth() from recipes/README.md

BASE_URL = "https://play.p21server.com"
USERNAME = "api_user"
PASSWORD = "api_pass"

token, ui_server, headers = p21_auth(BASE_URL, USERNAME, PASSWORD)

payload = {
    "Name": "Customer",
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
                        {"Name": "customer_name",    "Value": "ACME Industrial Supply"},
                        {"Name": "salesrep_id",      "Value": "100"},   # hard-required (see Gotchas)
                        {"Name": "mail_address1",    "Value": "123 Main St"},
                        {"Name": "mail_city",        "Value": "Des Moines"},
                        {"Name": "mail_state",       "Value": "IA"},
                        {"Name": "mail_postal_code", "Value": "50309"},
                        {"Name": "mail_country",     "Value": "USA"},
                    ],
                    "RelativeDateEdits": [],
                }],
            },
            {
                "Name": "SHIP_TO_GENERAL.ship_to_general",
                "Type": "Form",
                "Keys": [],
                "Rows": [{
                    "Edits": [
                        {"Name": "default_branch", "Value": "10"},  # required, NOT defaulted
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
    raise SystemExit("Customer create failed")

# The generated customer_id comes back in the TABPAGE_1.tp_1_dw_1 result rows
customer_id = None
for txn in result["Results"]["Transactions"]:
    if txn.get("Status") != "Passed":
        continue
    for element in txn.get("DataElements", []):
        if element.get("Name") != "TABPAGE_1.tp_1_dw_1":
            continue
        for row in element.get("Rows", []):
            for edit in row.get("Edits", []):
                if edit.get("Name") == "customer_id":
                    customer_id = edit.get("Value")

print(f"Created customer_id: {customer_id}")

# Read back via OData
cust = httpx.get(
    f"{BASE_URL}/odataservice/odata/table/customer",
    params={"$filter": f"customer_id eq {customer_id}"},
    headers=headers, verify=False,
)
cust.raise_for_status()
print(f"customer rows: {len(cust.json()['value'])}")
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
    ["Name"] = "Customer",
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
                        Row(("customer_name", "ACME Industrial Supply"),
                            ("salesrep_id", "100"),          // hard-required (see Gotchas)
                            ("mail_address1", "123 Main St"),
                            ("mail_city", "Des Moines"),
                            ("mail_state", "IA"),
                            ("mail_postal_code", "50309"),
                            ("mail_country", "USA")),
                    },
                },
                new JObject
                {
                    ["Name"] = "SHIP_TO_GENERAL.ship_to_general",
                    ["Type"] = "Form",
                    ["Keys"] = new JArray(),
                    ["Rows"] = new JArray
                    {
                        Row(("default_branch", "10")),       // required, NOT defaulted
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
    throw new InvalidOperationException("Customer create failed");
}

// The generated customer_id comes back in the TABPAGE_1.tp_1_dw_1 result rows
var customerId = result.SelectTokens(
        "$.Results.Transactions[?(@.Status == 'Passed')].DataElements[?(@.Name == 'TABPAGE_1.tp_1_dw_1')].Rows[*].Edits[?(@.Name == 'customer_id')].Value")
    .FirstOrDefault()?.ToString();

Console.WriteLine($"Created customer_id: {customerId}");
```
<!-- /tabs -->

> **End-to-end files** (runnable from the repo with a `.env`, dry-run by default): [`examples/python/recipes/create_customer.py`](../../examples/python/recipes/create_customer.py) · [`examples/csharp/Recipes/CreateCustomer.cs`](../../examples/csharp/Recipes/CreateCustomer.cs).

## Gotchas (verified live on Play 26.1.5894.1, 2026-07)

- **`salesrep_id` is hard-required, and the error surfaces on the ship-to, not the field.** Omitting it fails the whole transaction with *"Salesrep ID is required for a new ship to."* — even though the field lives on `TABPAGE_1.tp_1_dw_1`. Don't chase the ship-to when you see that message; supply `salesrep_id` on the Form.
- **`default_branch` is required and NOT defaulted.** The defaults template fills `packing_basis`/`freight_cd`/`fob` but leaves `default_branch` empty. Omitting it fails with *"'Default Branch' is a required column."*
- **No zip → salesrep cascade.** Setting `mail_postal_code` (or `phys_postal_code` on TABPAGE_5) does **not** default `salesrep_id`, even with matching rows seeded in `salesrep_postalcode` / `postal_code_group_hdr`. Those tables are [dead storage on an undeployed install](../02-OData-API.md#undeployed-unlicensed-windows-readable-tables-no-api-surface). The rep must be supplied explicitly and passes through verbatim.
- **HTTP 200 ≠ success.** Check `Summary.Succeeded` and `Results.Transactions[].Status == "Passed"`; the generated `customer_id` comes back in the result rows.

## Verify

```http
GET {base_url}/odataservice/odata/table/customer?$filter=customer_id eq 123456
```

Confirm `customer_name`, `salesrep_id`, and the mailing-address fields you sent.
