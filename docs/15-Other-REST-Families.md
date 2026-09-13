# Other REST Endpoint Families

> **Disclaimer:** This is unofficial, community-created documentation for Epicor Prophet 21 APIs. It is not affiliated with, endorsed by, or supported by Epicor Software Corporation. All product names, trademarks, and registered trademarks are property of their respective owners. Use at your own risk.

---

> **Added September 2026, extended September 2026** — verified live against **26.1.5950.0**. All sixteen families on this page were surfaced by reading [the middleware's own family list](05-Entity-API.md#discovering-what-your-tenant-actually-exposes) rather than by guessing names, and none of them had been documented here before.

---

## Overview

P21's REST API is divided into **endpoint families**, each with its own base path. Four are documented on their own pages — [`/api/entity/`](05-Entity-API.md) (customers, vendors, contacts, addresses), [`/api/inventory/parts`](11-Inventory-REST-API.md), `/api/sales/orders` and the [UDT service](13-UDT-Service-API.md). This page covers sixteen more that a 26.1 tenant publishes, in two groups.

**The first five** (documented first, and the deepest write coverage on this page):

| Family | What it reaches | Verified here |
|---|---|---|
| [`extensibility/userdefinedfields`](#extensibilityuserdefinedfields) | Every UDF in the system, with type metadata | **Reads fully verified** |
| [`accounting/gl`](#accountinggl) | GL distribution lines by transaction number | **Read and POST fully verified**, including the server-side balance check |
| [`sales/tasks`](#salestasks) | CRM tasks (`activity_trans`) | **Full CRUD round trip verified** |
| [`purchasing/purchaseorders`](#purchasingpurchaseorders) | Purchase order headers | **Create, update, and async create verified**; `async/callback` not exercised |
| [`inventory/inventoryadjustments`](#inventoryinventoryadjustments) | Inventory adjustment headers; WMS adjustment creation | **Reads and two of four create routes fully verified**; the two tag-adjustment routes have a verified refusal path but no reproduced success |

**The next eleven** — smaller in route count, business-object families rather than the platform-level five above:

| Family | What it reaches | Verified here |
|---|---|---|
| [`filehandler`](#filehandler) | A real network file share P21's own storage points at | **Full upload/detail/download/delete round trip verified** |
| [`environment/systems`](#environmentsystems) | Middleware build, config, and log metadata | **Read verified** |
| [`inventory/inventorymovement`](#inventoryinventorymovement) | Bin-to-bin and tag stock relocation | **Non-tag move fully verified**; tag moves not exercised (same tagged-item gap as [`createWmsTagAdjustment`](#createwmstagadjustment-createwmstagadjustmentwithcost-refusal-verified-success-not-reproduced)) |
| [`inventory/externalcounts`](#inventoryexternalcounts) | Staged cycle-count records | **Create fully verified** |
| [`inventory/partscan`](#inventorypartscan) | Cross-entity part lookup (item/customer/supplier/location) | **Fully verified** |
| [`accounting/customerformtemplates`](#accountingcustomerformtemplates) | Per-customer document filenames (invoice, RMA, packing list forms) | **Both create and update verified** — and are not the same call shape, see below |
| [`service/serviceorders`](#serviceserviceorders) | Field-service orders — turns out to be ordinary sales orders | **Read verified** (and is the finding); update refused |
| [`sales/opportunities`](#salesopportunities) | CRM opportunities | Blocked by tenant configuration, not the API — see below |
| [`sales/consignmentusageorders`](#salesconsignmentusageorders) | Consignment usage orders | Blocked by a missing prerequisite (a contract), not reproduced further |
| [`accounting/exchangerates`](#accountingexchangerates) | Currency exchange rates | Read verified (empty); create blocked by the tenant being single-currency |
| [`inventory/serialnumberextdinfo`](#inventoryserialnumberextdinfo) | Extended data on a tracked serial number | Refusal verified against a real serial; success not reproduced |

**Where a route is marked "not exercised" or "blocked", this page says so rather than describing it as if it had been run — and says why.** Several of the eleven above could not be pushed to a clean success not because the route is broken, but because the play tenant's own configuration has no data behind it: no consignment contracts, no opportunity pipeline configured, only one currency. That is itself worth knowing before you assume a 500 means the API doesn't work.

> **Discover, don't guess.** The families on your tenant are listed at `/docs/apiref.aspx`, and a family is confirmed with `GET {base}/{family}/help` — **not** `/ping`, which several families in both groups don't implement (`environment/systems` and `inventory/inventorymovement` among them — verified below). See [Discovering what your tenant actually exposes](05-Entity-API.md#discovering-what-your-tenant-actually-exposes).

---

## What the first five have in common

Same middleware, same contract. Everything in this section was verified on all five of the platform-level families above unless noted — the eleven business-object families further down do **not** all share these patterns, and each says explicitly where it agrees or differs.

### Authentication and headers

Identical to every other P21 REST call: a bearer token from [`/api/security/token/v2`](00-Authentication.md), and **`Accept: application/json`** or you get DataContract XML.

```http
GET /api/sales/tasks/16922 HTTP/1.1
Host: play.p21server.com
Authorization: Bearer {token}
Accept: application/json
```

### The route vocabulary

Each family publishes some subset of the same five routes:

| Route | Method | Purpose |
|---|---|---|
| `/{family}/ping` | GET | `{"ResponseMessage":"success"}` — **only where implemented**; a 404 here does not mean the family is absent |
| `/{family}/new` | GET | A template object with server-supplied defaults, meant as the starting point for a POST |
| `/{family}/` | GET | **The whole table. See the hazard below.** |
| `/{family}/{key}` | GET | One record by key |
| `/{family}/` and `/{family}/{key}` | POST / PUT | Create and update |

### ⚠ The bare collection GET is an unbounded full-table dump

**This is the one thing to know before calling any of these families.** `GET /{family}/` takes no filter, no paging, and no row limit — it serializes the entire underlying table into a single response.

Measured on the 26.1.5950.0 test tenant:

| Call | Result |
|---|---|
| `GET /api/sales/tasks/` | **28,332,703 bytes**, 17,050 records, 68 s |
| `GET /api/inventory/inventoryadjustments/` | **63,015,950 bytes**, 19 s |
| `GET /api/purchasing/purchaseorders/` | no response before the client gave up at 180 s |
| `GET /api/accounting/gl/` | no response before the client gave up at 180 s |

**And the obvious guard is silently ignored.** `$top` does not limit the response — it is neither honored nor rejected:

```text
GET /api/sales/tasks/            -> 200, 28,332,703 bytes, 17,050 records
GET /api/sales/tasks/?$top=2     -> 200, 28,332,703 bytes, 17,050 records   <- byte-identical
```

`page`/`pageSize`, `limit` and `top` behaved the same way. This is the same silent-success shape as [OData's `in` operator being accepted and ignored](02-OData-API.md#logical-operators): nothing in the response tells you your limit did not apply, and a client that sends `$top=2` and reads the first element will appear to work while transferring the whole table every time.

**Use the keyed GET, and find your keys elsewhere.** [OData](02-OData-API.md) is the query surface — filter there, then fetch the records you want by key:

```http
GET /odataservice/odata/table/activity_trans?$select=activity_trans_no&$filter=completed eq 'N'&$top=50
GET /api/sales/tasks/{activity_trans_no}
```

### Child collections are always `null` on read

Every one of these families publishes child collections in its contract and populates **none** of them on a keyed GET. On `purchasing/purchaseorders`, `POLines`, `POSales`, `POHdrNotes` and `POLineNotes` all come back `null`; on `inventory/inventoryadjustments`, `Lines` does.

This is not a parameter you are missing. Verified against `purchasing/purchaseorders/{poNo}` with `includeLines`, `expand`, `$expand`, `full` and `includeChildren` — **all five returned a byte-identical 742-byte header-only response**. Read lines from OData (`po_line`, `inv_adj_line`) or through the [Transaction API](03-Transaction-API.md), which does return them.

### `UserDefinedFields` is present and always empty

Every object on these families carries a `UserDefinedFields` key, and it is `{}` on every read — **including on records that genuinely have user-defined data**. Purchase order 584441 on the test tenant has a `po_hdr_ud` row with `received_flag: "Y"`; `GET /api/purchasing/purchaseorders/584441` returns `"UserDefinedFields": {}`.

Treat the key as a contract placeholder, not as evidence. To read UDF *values*, query the `*_ud` table over OData; to find out which UDFs exist at all, use [`extensibility/userdefinedfields`](#extensibilityuserdefinedfields) below.

---

## `extensibility/userdefinedfields`

**The machine-readable answer to "what custom fields does this P21 have?"** Read-only, fast, and the only surface in this documentation that enumerates UDFs with their types.

### Routes

| Route | Method | Returns |
|---|---|---|
| `/api/extensibility/userdefinedfields/` | GET | Every UDF on the system, flat |
| `/api/extensibility/userdefinedfields/tables` | GET | The same fields grouped by table, with each table's base table |
| `/api/extensibility/userdefinedfields/tables/{tableId}` | GET | One table's fields |
| `/api/extensibility/userdefinedfields/generate` | GET | *"Generates User Defined Field Assembly"* — **not exercised here** |
| `/api/extensibility/userdefinedfields/ping` | GET | Availability |

Unlike the other four families, the collection GET here is safe: the flat list was **28 KB** on the test tenant, not 28 MB.

### Response shape

```jsonc
// GET /api/extensibility/userdefinedfields/
{"list": [
  {"TableName": "address_ud", "ColumnName": "air_freight", "DisplayName": "AirFreight",
   "ColumnOrder": 3, "DataType": "char", "Length": 1, "Precision": 1,
   "DecimalPlaces": null, "IsNullable": "Y"},
  ...
]}
```

```jsonc
// GET /api/extensibility/userdefinedfields/tables
{"list": [
  {"TableName": "address_ud", "BaseTableName": "address",
   "UserDefinedFields": {"list": [ /* same field objects, TableName null inside */ ]}},
  ...
]}
```

Note the double nesting on the grouped form — `list` → table → `UserDefinedFields` → `list` — and that `TableName` is `null` on the inner field objects because the parent already carries it. `DataType` values seen: `char`, `datetime`, `decimal`, `int`, `text`, `varchar`.

The two routes agree: 152 fields across 23 tables on the test tenant, and the grouped counts summed to exactly the flat count.

### `{tableId}` is the `*_ud` table name, not the base table

The parameter name suggests an id. It is the **UD table's name**, and it is case-insensitive:

| Request | Result |
|---|---|
| `tables/address_ud` | 200 |
| `tables/OE_HDR_UD` | 200 — same payload as lowercase |
| `tables/address` (the *base* table) | **404** `Your query did not yield any results.` |
| `tables/1` | **404** |

The base-table name is the natural guess and the one that fails. Read `BaseTableName` off the grouped response when you need the mapping in that direction.

### Not every returned column is a custom field

The list includes each UD table's own plumbing alongside genuine UDFs, and the layout is consistent enough to filter on. Verified across all 23 tables:

- **`ColumnOrder: 1` is always `{table}_uid`** — the UD table's surrogate primary key. 23 of 23.
- **The columns after it, up to the first nullable one, are the join key back to the base table.** Often one column (`po_hdr_ud.po_no`), sometimes composite (`ship_to_ud`: `company_id` + `ship_to_id`; `oe_line_ud`: `order_no` + `line_no`).
- **The nullable columns are the actual user-defined fields.**

```text
ship_to_ud (base: ship_to)
   1  ship_to_ud_uid   int      N   <- surrogate key
   2  company_id       varchar  N   <- join key, part 1
   3  ship_to_id       decimal  N   <- join key, part 2
   4  edi_id           varchar  Y   <- the actual UDF
```

Filtering that way gives **96 real UDFs of the 152 rows** on the test tenant — 23 surrogate keys and 34 join-key columns are plumbing (34, not 23, because `ship_to_ud` and `oe_line_ud` each contribute a second join-key column); the other 95 are nullable, plus the one exception below.

> **Correction (September 2026).** This entry originally reported the count as "128 of the 152," arrived at as `152 − 24`. That arithmetic only holds if every table's join key is a single column, and two of the 23 are not (`ship_to_ud`, `oe_line_ud`) — the join-key deduction is 34 columns, not 23. Re-verified live: 23 (surrogate) + 34 (join key) + 95 (nullable) = 152, exactly.

> **The nullability rule is a strong convention, not a guarantee.** One field on the test tenant breaks it: `customer_ud.autoorder_flag` is `NOT NULL` and is a genuine custom field, because whoever created it gave it a default. Use the rule to sort a long list quickly, then read the names — do not build a pipeline that silently drops any `NOT NULL` column.

### Worked example

```python
"""List every user-defined field in P21, grouped by the table it extends."""
import httpx

BASE_URL = "https://play.p21server.com"
TOKEN = "..."  # see docs/00-Authentication.md

r = httpx.get(
    f"{BASE_URL}/api/extensibility/userdefinedfields/tables",
    headers={"Authorization": f"Bearer {TOKEN}", "Accept": "application/json"},
    timeout=120,
)
r.raise_for_status()

for table in r.json()["list"]:
    fields = sorted(table["UserDefinedFields"]["list"], key=lambda f: f["ColumnOrder"])
    # ColumnOrder 1 is the surrogate key; the NOT NULL columns after it are the
    # join key back to the base table. Read the names -- the rule has exceptions.
    custom = [f for f in fields[1:] if f["IsNullable"] == "Y"]
    if not custom:
        continue
    print(f"{table['TableName']} (extends {table['BaseTableName']})")
    for f in custom:
        print(f"    {f['ColumnName']:32} {f['DataType']}({f['Length']})")
```

```csharp
// List every user-defined field in P21, grouped by the table it extends.
using System.Net.Http.Headers;
using System.Text.Json;

const string BaseUrl = "https://play.p21server.com";
const string Token = "...";  // see docs/00-Authentication.md

using var client = new HttpClient { Timeout = TimeSpan.FromSeconds(120) };
client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", Token);
client.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));

var json = await client.GetStringAsync($"{BaseUrl}/api/extensibility/userdefinedfields/tables");
using var doc = JsonDocument.Parse(json);

foreach (var table in doc.RootElement.GetProperty("list").EnumerateArray())
{
    var fields = table.GetProperty("UserDefinedFields").GetProperty("list").EnumerateArray()
        .OrderBy(f => f.GetProperty("ColumnOrder").GetInt32())
        .ToList();

    // ColumnOrder 1 is the surrogate key; the NOT NULL columns after it are the
    // join key back to the base table. Read the names -- the rule has exceptions.
    var custom = fields.Skip(1)
        .Where(f => f.GetProperty("IsNullable").GetString() == "Y")
        .ToList();
    if (custom.Count == 0) continue;

    Console.WriteLine($"{table.GetProperty("TableName").GetString()} " +
                      $"(extends {table.GetProperty("BaseTableName").GetString()})");
    foreach (var f in custom)
        Console.WriteLine($"    {f.GetProperty("ColumnName").GetString(),-32} " +
                          $"{f.GetProperty("DataType").GetString()}({f.GetProperty("Length").GetInt32()})");
}
```

---

## `accounting/gl`

### Routes

| Route | Method | Notes |
|---|---|---|
| `/api/accounting/gl/{transactionNumber}` | GET | **The useful one** — returns every GL line of that transaction |
| `/api/accounting/gl/` | GET | Unbounded; did not return within 180 s on the test tenant |
| `/api/accounting/gl/` | POST | **Verified** — posts a balanced journal entry |
| `/api/accounting/gl/ping` | GET | Availability |

### The keyed GET returns a whole journal entry

`{transactionNumber}` is `gl.transaction_number`, and the response is an **array of GL distribution lines** — both sides of the entry, not a single row:

```jsonc
// GET /api/accounting/gl/3
[
  {"CompanyNo": "ACME", "AccountNumber": "11120010", "Period": 4, "YearForPeriod": 2011,
   "JournalId": "IA", "Amount": -44631.09, "Source": "1000002", "Description": "GO LIVE",
   "TransactionDate": "2011-01-27T01:11:32.703", "TransactionNumber": 3,
   "Approved": true, "SequenceNumber": 1, "GlUid": 4, "RecordTypeCd": 1367, ...},
  {"AccountNumber": "11130010", "Amount": 44631.09, "SequenceNumber": 2, ...}
]
```

The two lines sum to **0.00** — you get a balanced entry from one call, which is what makes this endpoint worth knowing. Reproducing it from OData means filtering `gl` on `transaction_number` yourself.

**An unknown transaction number returns `200 []`**, not a 404. Check for an empty array.

### `Source` links the entry back to the document that created it

`JournalId` names the subledger and `Source` carries that subledger's own key. In the example above, `JournalId: "IA"` and `Source: "1000002"` point at inventory adjustment 1000002 — the same record [`inventory/inventoryadjustments`](#inventoryinventoryadjustments) serves:

```http
GET /api/inventory/inventoryadjustments/1000002
  -> {"AdjustmentNo": 1000002, "Reason": "GO LIVE", "LocationId": 18, ...}
```

That pairing is the practical use of this family: find GL activity over OData, then pull the full entry and walk `Source` back to the originating document.

### Posting a journal entry (verified)

`POST /api/accounting/gl/` takes the same shape the GET returns: **an array of lines**, sent together as one balanced entry. Confirmed against the SDK's own contract (`Gl[] CreateGl(Gl[] toCreate)`) and run live:

```jsonc
// POST /api/accounting/gl/
[
  {"CompanyNo": "ACME", "AccountNumber": "11120010", "Period": 12, "YearForPeriod": 2026,
   "JournalId": "AC", "Amount": 0.01, "ForeignAmount": 0.01,
   "Description": "...", "Source": "...", "TransactionDate": "2026-09-12T00:00:00"},
  {"CompanyNo": "ACME", "AccountNumber": "11130010", "Period": 12, "YearForPeriod": 2026,
   "JournalId": "AC", "Amount": -0.01, "ForeignAmount": -0.01,
   "Description": "...", "Source": "...", "TransactionDate": "2026-09-12T00:00:00"}
]
```

`Period`/`YearForPeriod` must name an open period — `periods.period_closed eq 'N'` over OData finds one; posting into a closed period was not tested. The response echoes every line back with the fields the server fills in: a shared, auto-assigned `TransactionNumber`, `Approved: true` (no approval step on this path), `SourceTypeCd` set automatically (`3495` for a manually-posted entry via this endpoint, distinct from the `1367` seen on an inventory-adjustment-sourced entry), and real `GlUid`/`DateCreated`/`LastMaintainedBy` values.

**The balance check is real and server-side.** A single-line, self-evidently unbalanced POST was refused cleanly:

```jsonc
HTTP 500
{"ErrorMessage": "Records do not balance",
 "ErrorType": "P21.Business.Common.BusinessException", ...}
```

The error surfaces as a `BusinessException` from `GlManager.UpdateAllRecords`, not as a generic CRUD failure — this is a deliberate validation, not an incidental side effect of some other check. A caller does not need to sum its own lines defensively before posting; the endpoint will refuse an unbalanced batch outright.

Read the entry back with the same keyed GET this section opened with — `GET /api/accounting/gl/{transactionNumber}` confirmed both lines, correctly balanced.

---

## `sales/tasks`

CRM tasks, backed by `activity_trans` — what P21 shows as Task/Activity entry against a customer or contact. **This is the family whose full create-read-update cycle was verified end to end.**

### Routes

| Route | Method | Notes |
|---|---|---|
| `/api/sales/tasks/new` | GET | Template with server defaults |
| `/api/sales/tasks/` | POST | **Create — verified** |
| `/api/sales/tasks/{activityTransID}` | GET | **Read — verified** |
| `/api/sales/tasks/{activityTransID}` | PUT | **Update — verified** |
| `/api/sales/tasks/` | GET | Unbounded — 28 MB / 17,050 records on the test tenant |
| `/api/sales/tasks/ping` | GET | Availability |

### `GET /new` first

The template arrives with the calling user and company already filled in, plus the code values the record needs. Start from it rather than hand-building the object:

```jsonc
// GET /api/sales/tasks/new
{
  "ActivityTransNo": "", "ActivityId": "", "ContactId": "",
  "EntryDate": "2026-09-12T00:00:00",
  "AssignedById": "apiuser", "AssignedToId": "apiuser",   // the calling user
  "Completed": "N", "Comments": "", "Subject": "",
  "ReminderTimeOffset": 0, "ReminderTimeOffsetCd": 1413,
  "PrivateTask": "N", "TargetCompleteDate": "2026-09-12T11:10:34.5-05:00",
  "Followup": "N", "FollowupCommentCd": 1441,
  "ActivityDesc": "", "CompanyId": "ACME",
  "LinkId": 0, "LinkTypeCd": 1203,
  "ContactAddressName": "", "HardTouch": "", "ProblemCodeId": "",
  "CreateOutlookTask": "N", "TransactionNo": "", "TransactionTypeCode": 300,
  "Reminder": "N", "UserDefinedFields": {}, "ObjectName": "activity_trans"
}
```

### "Customer ID is required" means `LinkId`

The first create attempt filled in `ActivityId`, `ContactId` and `Subject` and was refused:

```jsonc
HTTP 500
{"ErrorMessage": "Customer ID is required....CRUD Update error: Update failed for activity_trans. (-1)",
 "ErrorType": "P21.DataAccess.PbNet.Common.PbService.P21ServerException", ...}
```

**There is no `CustomerId` field on the object.** The customer is `LinkId`, paired with `LinkTypeCd` (`1203` in the template, which is what the working record used). Setting `LinkId` to the customer id made the identical payload succeed. Two things worth noting about that error:

- The message names a field that does not exist in the contract you were sent. Map "Customer ID" to **`LinkId`**.
- It says **`Update` failed** on what was a create — the middleware routes both through the same CRUD verb, so the word "Update" in an error is not evidence you hit the wrong route.

`ContactAddressName` is server-derived: supply `LinkId: 12066` and the read-back comes back with `"ContactAddressName": "ABC Supply Company"`.

### Verified round trip

```python
"""Create, read and update a P21 CRM task. Verified on 26.1.5950.0."""
import httpx

BASE_URL = "https://play.p21server.com"
TOKEN = "..."               # see docs/00-Authentication.md
CONTACT_ID = "17055"
CUSTOMER_ID = 12066         # goes in LinkId -- "Customer ID is required" means this

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/json",
    "Content-Type": "application/json",
}

with httpx.Client(timeout=120, follow_redirects=True) as client:
    # 1. Start from the server's own template.
    task = client.get(f"{BASE_URL}/api/sales/tasks/new", headers=headers).json()
    task.update({
        "ActivityId": "FOLLOW UP",
        "ContactId": CONTACT_ID,
        "LinkId": CUSTOMER_ID,
        "Subject": "Quote follow-up",
        "Comments": "Raised from the integration",
        "TargetCompleteDate": "2026-09-30T15:00:00",
    })

    # 2. Create. The trailing slash matters -- the list route 307s without it.
    created = client.post(f"{BASE_URL}/api/sales/tasks/", headers=headers, json=task)
    created.raise_for_status()
    task_no = created.json()["ActivityTransNo"]
    print(f"created task {task_no}")

    # 3. Read back, then update the record you were given rather than the one you sent:
    #    the server fills in fields (ActivityDesc, ContactAddressName) that a PUT expects.
    current = client.get(f"{BASE_URL}/api/sales/tasks/{task_no}", headers=headers).json()
    current["Completed"] = "Y"
    current["Comments"] = "Closed out by the integration"

    updated = client.put(
        f"{BASE_URL}/api/sales/tasks/{task_no}", headers=headers, json=current
    )
    updated.raise_for_status()
    print(f"completed: {updated.json()['Completed']}")
```

```csharp
// Create, read and update a P21 CRM task. Verified on 26.1.5950.0.
using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Text.Json.Nodes;

const string BaseUrl = "https://play.p21server.com";
const string Token = "...";          // see docs/00-Authentication.md
const string ContactId = "17055";
const int CustomerId = 12066;        // goes in LinkId -- "Customer ID is required" means this

using var client = new HttpClient { Timeout = TimeSpan.FromSeconds(120) };
client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", Token);
client.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));

// 1. Start from the server's own template.
var task = await client.GetFromJsonAsync<JsonObject>($"{BaseUrl}/api/sales/tasks/new");
task!["ActivityId"] = "FOLLOW UP";
task["ContactId"] = ContactId;
task["LinkId"] = CustomerId;
task["Subject"] = "Quote follow-up";
task["Comments"] = "Raised from the integration";
task["TargetCompleteDate"] = "2026-09-30T15:00:00";

// 2. Create. The trailing slash matters -- the list route 307s without it.
var created = await client.PostAsJsonAsync($"{BaseUrl}/api/sales/tasks/", task);
created.EnsureSuccessStatusCode();
var taskNo = (await created.Content.ReadFromJsonAsync<JsonObject>())!["ActivityTransNo"]!.GetValue<string>();
Console.WriteLine($"created task {taskNo}");

// 3. Read back, then update the record you were given rather than the one you sent:
//    the server fills in fields (ActivityDesc, ContactAddressName) that a PUT expects.
var current = await client.GetFromJsonAsync<JsonObject>($"{BaseUrl}/api/sales/tasks/{taskNo}");
current!["Completed"] = "Y";
current["Comments"] = "Closed out by the integration";

var updated = await client.PutAsJsonAsync($"{BaseUrl}/api/sales/tasks/{taskNo}", current);
updated.EnsureSuccessStatusCode();
Console.WriteLine($"completed: {(await updated.Content.ReadFromJsonAsync<JsonObject>())!["Completed"]}");
```

The PUT returns the updated object, and a follow-up GET confirmed both changed fields persisted.

> **There is no delete route.** `/help` publishes GET, POST and PUT only. Close a task by setting `Completed: "Y"`.

---

## `purchasing/purchaseorders`

### Routes

| Route | Method | Notes |
|---|---|---|
| `/api/purchasing/purchaseorders/{poNo}` | GET | **Verified** — header only, children `null` |
| `/api/purchasing/purchaseorders/new` | GET | **Verified** — template, `POLines` pre-seeded with one blank line |
| `/api/purchasing/purchaseorders/` | POST | **Verified** — creates a PO with real lines |
| `/api/purchasing/purchaseorders/{poNo}` | PUT | **Verified** — updates persist |
| `/api/purchasing/purchaseorders/async` | POST / GET | **Verified** — GET takes `?requestId=` |
| `/api/purchasing/purchaseorders/async/callback` | POST | Published. **Not exercised** — needs a reachable callback URL |
| `/api/purchasing/purchaseorders/` | GET | Unbounded; did not return within 180 s |
| `/api/purchasing/purchaseorders/ping` | GET | Availability |

### The keyed read

```jsonc
// GET /api/purchasing/purchaseorders/998310
{"POLines": null, "POSales": null, "POHdrNotes": null, "POLineNotes": null,
 "DirectShipTo": {"Name": "", "Address1": "", "City": "", "State": "", "Country": "", "Zip": ""},
 "PoNo": 998310, "CompanyNo": "ACME", "LocationId": 20,
 "VendorId": 25753, "SupplierId": 25753, "DivisionId": 25753,
 "BuyerId": "812", "PoType": "X", "OrderDate": "2026-08-27T10:17:20.887",
 "DateDue": "2026-08-27T00:00:00", "Approved": "Y", "Terms": "1", "CarrierId": "100",
 "Printed": "N", "Delete": "N", "PoHdrUid": 468174, "Complete": "N", "CurrencyId": 1,
 "UserDefinedFields": {}, ...}
```

742 bytes, header only. `DirectShipTo` is an inline object rather than a child collection, so it *is* populated (with empty strings on a non-direct-ship PO). For lines, see [child collections are always null](#child-collections-are-always-null-on-read) — that section is about *reads*; see below for what a *create* actually returns.

### Creating a PO (verified)

Start from `GET /new`, which pre-populates `POLines.list` with one blank line at `LineNo: 223` — a suggested starting line number, not a real one; the created PO below landed its first line at `LineNo: 1` regardless. Fill in the header and at least one line, then `POST` the whole object:

```jsonc
// PO /new template, trimmed to the fields a create needs
{"POLines": {"list": [{"LineNo": 223, "ItemId": "", "UnitOfMeasure": "", "UnitQuantity": null,
                       "UnitPrice": 0.0, "PricingUnit": "", ...}]},
 "CompanyNo": "", "LocationId": null, "VendorId": null, "SupplierId": null,
 "BuyerId": "", "PoType": "S", "Approved": "N", ...}
```

**`BuyerId` is not marked required in the contract, but an empty one fails create with a misleading error.** Leaving it `""` (its value in the `/new` template) produces:

```jsonc
HTTP 500
{"ErrorMessage": "<ImportReturn type=\"CREATE\">...Buyer ID (G): Null filter expression passed to of_Retrieve for Contacts....Invalid buyer ID....Sales/Production/PO Intersection Detail Record must be part of Import Set, but is unmatched...(Return value: -8 , Import is ok but some records failed )...",
 "ErrorType": "P21.DataAccess.PbNet.Common.PbService.P21ServerException", ...}
```

Two things worth knowing about that error, both confirmed by re-running with a real `BuyerId`: **the create is implemented on top of P21's Import/Export engine** — the whole error body is an escaped `<ImportReturn>` XML document, which is why it reads nothing like the clean `Column is disabled:`-style errors elsewhere in this documentation. And **the second complaint about `POSales`/"Import Set" is cascade noise from the same root cause**, not a separate requirement — supplying a real `BuyerId` (a real value from an existing PO, e.g. `"812"`) and changing nothing else made both messages disappear and the create succeed.

The successful response is the one place this family's child collections are *not* null — `POLines.list` comes back with the real, server-assigned `PoLineUid`, `LineNo`, and pricing-lookup fields (`ExtendedDesc`, `CalcType`, `UnitSize` filled in from the item master). **But `UnitPrice` is not one of the fields honored from your request**: a line sent with `"UnitPrice": 5.00` came back — and was actually stored, confirmed over OData on `po_line.unit_price` — as `0.00`. `PriceEdit: "N"` on the template line suggests price is meant to come from a pricing lookup rather than the caller; sending a price does not override it on this path. If the PO needs a specific price, set it after creation through a surface that supports a manual override, and verify with a read-back either way.

A `GET` on the newly-created PO immediately afterward still returned `POLines: null` — confirming [the null-on-read behavior](#child-collections-are-always-null-on-read) is a genuine property of the GET route, not a caching artifact of an older record.

### Updating a PO (verified)

`PUT /api/purchasing/purchaseorders/{poNo}` with the record read back from `GET` (edited in place) persisted the changes on a subsequent read. Its response shape is a third variant: `POLines: {"list": []}` — an **empty list**, neither the `null` a GET returns nor the populated list a POST returns.

### Creating a PO asynchronously (verified)

`POST /api/purchasing/purchaseorders/async` accepts the identical `PurchaseOrder` body and returns immediately with a request handle:

```jsonc
// POST .../async  ->  202-shaped response, HTTP 200
{"RequestId": "f996e37a-...", "RequestType": "PurchaseOrder", "Status": 3,
 "StartDate": "...", "CompletedDate": null, "Messages": null}
```

Poll `GET .../async?requestId={RequestId}` until it completes. Observed values: **`Status: 3`** while running, **`Status: 2`** once complete — at which point `Messages` carries the new PO number as a plain string (`"998313"`), not a structured object, and `CompletedDate` is populated. The created PO reads back normally through the ordinary keyed GET. `async/callback` (a webhook-style variant taking a callback URL) was not exercised — it needs a reachable endpoint to receive the callback, which a documentation run against a shared test tenant cannot safely stand up.

### Which PO surface should you use?

Three surfaces write purchase orders:

| Surface | Use it for |
|---|---|
| **This family** | Now verified for header + line create, update, and async create. Still missing: a working manual unit price, and any read-back for `POSales`/notes |
| [Transaction API `PurchaseOrder`](03-Transaction-API.md#purchaseorder-service-creating-a-po) | **The most thoroughly verified path in this documentation** — full build → receive → vouch, lines included, and price sticks |
| [Interactive API](04-Interactive-API.md) | Wizards and anything needing window business logic, e.g. [direct-ship PO generation](04-Interactive-API.md#driving-an-in-window-wizard-direct-ship-po-generation) |

Prefer the Transaction API when the price needs to be exact. This family is now a legitimate option for a REST-shaped integration that can tolerate pricing-lookup-driven prices, or that sets price through a separate step. It has its **own** async endpoint, separate from [the Transaction API's](03-Transaction-API.md#endpoints) — and the Transaction API's async path carries [a documented no-cancel hazard](03-Transaction-API.md#endpoints) that has not been specifically re-tested here but is worth assuming applies equally.

---

## `inventory/inventoryadjustments`

### Routes

| Route | Method | Notes |
|---|---|---|
| `/api/inventory/inventoryadjustments/{adjustmentNo}` | GET | **Verified** — header only, `Lines` always `null` |
| `/api/inventory/inventoryadjustments/createWmsAdjustment` | POST | **Verified** — moves stock, signed delta |
| `/api/inventory/inventoryadjustments/createWmsAdjustmentWithCost` | POST | **Verified** — as above, `unitCost` is honored |
| `/api/inventory/inventoryadjustments/createWmsTagAdjustment` | POST | Requires a genuinely tag-controlled item. **Refusal verified; a success was not reproducible** — see below |
| `/api/inventory/inventoryadjustments/createWmsTagAdjustmentWithCost` | POST | Same open question as the tag variant above |
| `/api/inventory/inventoryadjustments/` | GET | Unbounded — 63 MB on the test tenant |
| `/api/inventory/inventoryadjustments/ping` | GET | Availability |

### The keyed read

```jsonc
// GET /api/inventory/inventoryadjustments/1000002
{"Lines": null, "AdjustmentNo": 1000002, "CompanyId": "ACME", "LocationId": 18,
 "Reason": "GO LIVE", "Approved": true, "Delete": false, "Description": "",
 "UserDefinedFields": {}, "ObjectName": "inv_adj_hdr"}
```

Note `Approved` and `Delete` are real booleans here, where the PO family uses `"Y"`/`"N"` strings for the same concepts. The families do not share a convention.

To see what an adjustment did to stock, read `inv_adj_line` over OData, or follow it into the GL — `gl.source` carries the adjustment number under `JournalId: "IA"` ([worked example above](#source-links-the-entry-back-to-the-document-that-created-it)).

### The create routes take query-string parameters, not a body

Unusual for a POST, and the reason a body-shaped attempt will confuse you. From the family's own `/help`:

```http
POST /api/inventory/inventoryadjustments/createWmsAdjustment
    ?locationId={locationId}
    &reason={reason}
    &approved={approved}
    &description={optionalDescription}
    &itemId={itemId}
    &unitQuantity={unitQuantity}
    &unitOfMeasure={unitOfMeasure}
    &binCd={optionalBinCd}
    &lotCd={optionalLotCd}
    &serialNumber={optionalSerialNumber}
```

`createWmsAdjustmentWithCost` adds `&unitCost={unitCost}`. The tag variants replace `serialNumber` with `&tagNo={optionalTagNo}&qtyPerPackage={optionalQtyPerPackage}&packageType={optionalPackageType}`.

The published description is *"Adjust quantity for a single item. Return the created adjustment."* — one item per call, and the `Wms` naming suggests these exist for warehouse-management integrations rather than as a general adjustment API.

### `createWmsAdjustment` (verified)

Two preconditions are not documented anywhere in `/help` and both fail with a clear, distinct error, so treat them as a checklist:

1. **`reason` must name an *active* `reason` record.** An inactive one — `reason.delete_flag eq 'Y'` over OData, and note that historical `inv_adj_hdr` rows can carry an inactive reason's text, since the reason was presumably active when they were created — fails with `This Adjustment Reason record could not be retrieved.` A currently-active reason (`reason.delete_flag eq 'N'`) is required.
2. **`binCd` is required whenever the item/location is bin-tracked** (`inv_loc.track_bins eq 'Y'`) — omitting it on a bin-tracked location fails with `Bin is required.`, naming neither the item nor the location. Find the item's bin over OData (`inv_loc.primary_bin`) rather than guessing.

With both satisfied, the call succeeds and **`unitQuantity` is a signed delta**, matching the Transaction API `InventoryAdjustment` service's own convention — confirmed by posting `unitQuantity: "1"` twice against a starting on-hand of 0 and watching it reach 2, not stay at 1:

```jsonc
// POST .../createWmsAdjustment?locationId=40&reason=ADJUST&approved=Y&description=...
//      &itemId=GBY&unitQuantity=1&unitOfMeasure=EA&binCd=FGA040&lotCd=&serialNumber=
HTTP 200
{"Lines": {"list": [{"Bins": {"list": [{"BinCd": "FGA040", "UnitQuantity": 1.0, ...}]},
                     "AdjustmentNo": 1309659, "ItemId": "GBY", "UnitQuantity": 1.0,
                     "Cost": 42.9938015, "ObjectName": "inv_adj_line"}]},
 "AdjustmentNo": 1309659, "CompanyId": "ACME", "LocationId": 40, "Reason": "ADJUST",
 "Approved": true, ...}
```

Note `Lines` is populated here, on the POST response — the same null-on-GET, populated-on-write split already seen on `purchasing/purchaseorders`. `Cost` is filled in automatically (moving-average cost) when no cost is supplied — see the `WithCost` variant below for what happens when you supply one.

### `createWmsAdjustmentWithCost` (verified)

Identical call shape plus `&unitCost={value}`. Unlike `purchasing/purchaseorders`' `UnitPrice`, **the supplied cost is honored exactly**: sending `unitCost=99.99` produced `"Cost": 99.99` in the response, not a recalculated moving-average value. The two routes make opposite choices about whether a caller-supplied money value survives, and there is no way to tell which behavior a given route has without testing it — which is the whole reason this section states outcomes per route rather than assuming they generalize.

### `createWmsTagAdjustment` / `createWmsTagAdjustmentWithCost` — refusal verified, success not reproduced

Both calls refuse identically and immediately, naming the item precisely:

```jsonc
HTTP 500
{"ErrorMessage": "ProcessAction (CREATEWMSADJUSTMENTTAG ): Error: Method CreateWmsTagAdjustment failed: {ItemId} is not a tagged item. Please enter a tagged item. (-1)",
 "ErrorType": "P21.DataAccess.PbNet.Common.PbService.P21ServerException", ...}
```

That much is a clean, verified precondition. What is *not* settled: **`inv_mast.use_tags_flag = 'Y'` is not sufficient to satisfy it.** Two different items carrying that flag, one of them (`CAEKLHN`) stocked and bin-tracked at the same location used for the successful non-tag tests, both produced the identical refusal. No `tag`/`inv_tag`/`inventory_tag` OData object exists to inspect existing tag records directly, so whether the real precondition is an existing physical tag (created through receiving/putaway, not through this endpoint) or something else on the item master is unresolved. Anyone with a genuinely tag-controlled item and a live tag number on their tenant can settle this in one call; until then, treat these two routes as **published and reachable, with a confirmed rejection path, but an unconfirmed success path.**

For an adjustment path with a fully verified success case regardless of tag status, see the [Transaction API `InventoryAdjustment` service](03-Transaction-API.md) and the [inventory-adjustment payload](../examples/payloads/json/inventory-adjustment.json).

---

## `filehandler`

Routes to a real network file share — not a P21 business object at all, but a general-purpose file store the middleware exposes over REST. Every route was exercised end to end.

### Routes

| Route | Method | Notes |
|---|---|---|
| `/api/filehandler/ping` | GET | Availability |
| `/api/filehandler/file/detail?filename={name}` | GET | **Verified** — file metadata |
| `/api/filehandler/file/detail/path?fileName={name}&path={path}` | GET | Same, at an explicit path |
| `/api/filehandler/files` | GET | **Verified** — lists every file in the default path |
| `/api/filehandler/files/path?path={path}` | GET | Same, at an explicit path |
| `/api/filehandler/file?fileName={name}` | POST | **Verified** — upload (raw body = file content) |
| `/api/filehandler/file/path?fileName={name}&path={path}` | POST | Same, at an explicit path |
| `/api/filehandler/file?fileName={name}` | PUT | Published — replace an existing file. Not exercised (POST already covers the create/verify path) |
| `/api/filehandler/file?fileName={name}` | GET | **Verified** — download (raw bytes, not JSON) |
| `/api/filehandler/file?fileName={name}` | DELETE | **Verified** — returns a bare JSON `true` |
| `/api/filehandler/files/path/verify?path={path}` | PUT | Published — batch existence check. Not exercised |

### The path is a real network share, not a sandbox

`GET /api/filehandler/files` on the play tenant returned real files sitting at `\\fileserver01\data\Internal\Computer\P21\Scripts\Play` — the middleware's own configured default storage path, not a scoped or virtualized location. An uploaded file landed at the identical path:

```jsonc
// POST /api/filehandler/file?fileName=zz_api_doc_test.txt   (body = raw bytes)
// Content-Type header not required -- the body is read as a stream regardless
HTTP 200  // XML by default -- send Accept: application/json for the JSON shape shown below
{"ResourceKind": 0, "Name": "zz_api_doc_test.txt",
 "Path": "\\\\fileserver01\\data\\Internal\\Computer\\P21\\Scripts\\Play",
 "SizeInBytes": 84, "FullPath": "...\\zz_api_doc_test.txt", "Properties": [...]}
```

**Treat this family as filesystem access, not a data API.** Whoever can reach it can list, read, write, and delete real files on a real path the middleware's process account can reach — the same caution [this documentation already gives consumer keys](00-Authentication.md#method-2-consumer-key) applies here for a different reason: the blast radius is a filesystem, not just P21 data.

### Full round trip (verified)

Upload → detail → download → delete, each step confirmed against the previous:

```python
import httpx

FILE_NAME = "zz_api_doc_test.txt"
content = b"ZZ API DOC TEST - safe to delete\n"

httpx.post(f"{BASE_URL}/api/filehandler/file", params={"fileName": FILE_NAME},
           headers=AUTH_HEADERS, content=content)                    # -> 200, file created

httpx.get(f"{BASE_URL}/api/filehandler/file/detail",
          params={"filename": FILE_NAME}, headers=JSON_HEADERS)      # -> 200, SizeInBytes: 84

httpx.get(f"{BASE_URL}/api/filehandler/file",
          params={"fileName": FILE_NAME}, headers=AUTH_HEADERS)      # -> 200, raw bytes back

httpx.delete(f"{BASE_URL}/api/filehandler/file",
             params={"fileName": FILE_NAME}, headers=JSON_HEADERS)   # -> 200, body: true

# detail on the same name afterward returns 200 with a JSON null body,
# not a 404 -- "gone" and "never existed" look identical here.
```

Note the `filename`/`fileName` casing split across routes — `file/detail` takes lowercase `filename`, everything else takes `fileName`. Both are literal query-parameter names from the SDK contract, not a typo in this documentation.

---

## `environment/systems`

Middleware self-description: build number, configuration id, and (via child routes) logs — a REST alternative to [the `serverinfo` endpoint](00-Authentication.md#server-info-endpoint-version-environment-detection) that returns JSON directly with no XML-by-default trap.

### Routes

| Route | Method | Notes |
|---|---|---|
| `/api/environment/systems` | GET | **Verified** — no `/ping` on this family; this is the availability check |
| `/api/environment/systems/{systemId}` | GET | One system's detail |
| `/api/environment/systems/{systemId}/properties` | GET | All properties for a system |
| `/api/environment/systems/{systemId}/properties/{propertyId}` | GET | One property |
| `/api/environment/systems/{systemId}/logs` | GET | Log list |
| `/api/environment/systems/{systemId}/logs/{logId}` | GET | One log's metadata |
| `/api/environment/systems/{systemId}/logs/{logId}/content` | GET | Raw log content (a stream) |
| `/api/environment/systems/{systemId}/logs/{logId}` | DELETE | Delete a log. Not exercised |

**There is no `/ping`.** The contract (`ISystemResource`) never declares one — confirmed by the 404 it returns, `"Not Found Error. The resource \"ping\" was not found."` The bare `GET /api/environment/systems/` is the actual availability check, and it is cheap and small — not the unbounded-dump risk the platform-level families carry.

### Verified read

```jsonc
// GET /api/environment/systems
{"list": [{
  "Id": "ERP_SYSTEM", "Type": "Prophet 21", "Version": "0026.0001.5950.0000",
  "Properties": {"list": [
    {"Name": "ads_login_domain", "Value": "example.com"},
    {"Name": "configuration_id", "Value": "3694"},
    {"Name": "database_schema_version", "Value": "0026.0001.5950.0000"}
  ]}
}]}
```

`Version` and `database_schema_version` both carry the full build number in a dotted four-segment form (`0026.0001.5950.0000`) rather than the `26.1.5950.0` shape `serverinfo` and session-create use — the same build, a different string format. Match on the trailing two segments if you need to compare against those other sources.

---

## `inventory/inventorymovement`

Bin-to-bin and tag relocation, independent of the WMS adjustment family — this moves stock between bins without changing the total on-hand quantity.

### Routes

| Route | Method | Notes |
|---|---|---|
| `/api/inventory/inventorymovement/moveinventory` | POST | **Verified** — non-tag bin-to-bin move |
| `/api/inventory/inventorymovement/moveinventoryfortransaction` | POST | Non-tag move tied to a specific document/line. Not exercised |
| `/api/inventory/inventorymovement/moveinventorytagtobin` | POST | Tag relocation. Not exercised — same tagged-item gap as [`createWmsTagAdjustment`](#createwmstagadjustment-createwmstagadjustmentwithcost-refusal-verified-success-not-reproduced) |
| `/api/inventory/inventorymovement/moveinventorytagtocontainer` | POST | Tag-into-tag relocation. Not exercised, same reason |

**There is no `/ping`** on this family either — a bare probe 404s with an HTML body, not the JSON `NotFoundException` shape `environment/systems` gives; treat both as "this family has no ping route," not as evidence the family is absent (see [the `/ping` correction](05-Entity-API.md#probe-with-help-not-ping-a-ping-404-proves-nothing)).

### `moveinventory` (verified)

Every parameter is a query string, and several are stricter than their names suggest:

```jsonc
POST /api/inventory/inventorymovement/moveinventory
    ?location={location}&itemId={itemId}&toBin={toBin}&fromBin={fromBin}
    &lot={lot}&uom={uom}&quantity={quantity}
    &moveAvailable={moveAvailable}&moveAllocations={moveAllocations}
```

`moveAvailable`/`moveAllocations` look boolean but are **not** — `"true"`/`"false"` fail with `System.ArgumentException: Move Available is a Y/N column.`; send `"Y"`/`"N"`. Once that is right, the mechanism enforces real warehouse rules, each with a distinct, clean error:

| Condition tried | Result |
|---|---|
| `toBin` equal to `fromBin` | `400`-shaped `ArgumentException`: `"Destination bin has to be different from source bin"` |
| `toBin` not a bin this item/location actually has stock associations for | `"A valid inventory bin must be entered."` — not every bin that physically exists at the location qualifies |
| `toBin` genuinely exists but is put-locked | `"The Put Lock is set for this bin. You must select another."` |
| A real, unlocked, item-associated bin | **`200`**, moves the stock |

```jsonc
// A working move, verified: GBY at location 40, 1 unit, FGA040 -> XDOCK
HTTP 200
{"TransactionDetail": {"QuantityMoved": "1", "QuantityMovedUOM": "EA"}, "ResponseMessage": "success"}
```

Total `qty_on_hand` is unchanged by a bin-to-bin move — confirmed before and after. **`GET /odataservice/odata/table/bin` cannot help you find a valid destination bin** ([it 404s regardless of casing or surface](02-OData-API.md#one-object-name-is-unreachable-regardless-of-surface-bin)); read `inv_loc.primary_bin` for bins already associated with specific items instead, the way this verification did.

> **`"success"` does not always mean a nonzero quantity actually moved — and which behavior you get depends on which bin is empty.** Re-running the same move a second time from a **secondary, ad-hoc bin** (one this same run had just created a stock association for by moving into it) that by then held no real stock returned the identical `200 {"ResponseMessage": "success"}` shape — with `"QuantityMoved": "0"`. But moving out of the item's **primary bin** once it, too, held zero stock was refused outright: `"There are no items in this bin."` The item's well-established primary-bin association gets a real check; a bin association the route itself created moments earlier does not. Read `TransactionDetail.QuantityMoved` on a `200` before treating it as evidence anything relocated, and do not assume a hard failure on one bin means the same check applies everywhere.

---

## `inventory/externalcounts`

Stages a cycle count for later reconciliation — creating one does **not** change `inv_loc.qty_on_hand`, confirmed by reading it back unchanged immediately after a successful create.

### Routes

| Route | Method | Notes |
|---|---|---|
| `/api/inventory/externalcounts/ping` | GET | Availability |
| `/api/inventory/externalcounts/` | POST | **Verified** |

### Creating a count (verified) — the same field has to be sent twice

The header needs a `Lines.list`, and each line needs a `Bins.list` — bin detail is mandatory the moment a line carries a quantity, matching [`createWmsAdjustment`'s bin requirement](#createwmsadjustment-verified) on a bin-tracked location. The trap: **`ItemId` must be repeated on the bin sub-record, not just the line** — the bin object has its own `ItemId` field, and it is not inherited from its parent line.

```jsonc
// This fails -- ItemId given only on the line:
{"LocationId": 40, "CountDate": "2026-09-12T00:00:00",
 "Lines": {"list": [{"ItemId": "GBY", "UnitQuantity": 5.0, "UnitOfMeasure": "EA",
                     "Bins": {"list": [{"BinCd": "FGA040", "UnitQuantity": 5.0, "UnitOfMeasure": "EA"}]}}]}}
// HTTP 500, <ImportReturn>: "Bin Detail Record Required for Import Set, but is missing"
//                            "Bin Detail Record must be part of Import Set, but is unmatched"

// This succeeds -- ItemId on BOTH the line and the bin:
{"LocationId": 40, "CountDate": "2026-09-12T00:00:00",
 "Lines": {"list": [{"ItemId": "GBY", "UnitQuantity": 5.0, "UnitOfMeasure": "EA",
                     "Bins": {"list": [{"ItemId": "GBY", "BinCd": "FGA040",
                                       "UnitQuantity": 5.0, "UnitOfMeasure": "EA"}]}}]}}
// HTTP 200
```

Both error messages talk about "the bin detail record," which reads like the bin block itself is missing — it was present the whole time. Nothing in either message names the actual cause (a missing field one level down), which is exactly the shape of trap worth writing down: the fix is one field, and the error does not point at it.

---

## `inventory/partscan`

A single, cross-entity part lookup — one call answers "what item does this scan/search term resolve to," optionally scoped by customer, supplier, or location.

### Routes

| Route | Method | Notes |
|---|---|---|
| `/api/inventory/partscan/ping` | GET | Availability |
| `/api/inventory/partscan/?partSearch={term}&companyId={id}&locationId={id}&customerId={id}&supplierId={id}` | GET | **Verified** |

### Verified read

All four scope parameters are optional in practice — sending them empty still resolves a plain item-id search, and the trailing slash before the query string matters (the bare form without it 307-redirects):

```jsonc
// GET /api/inventory/partscan/?partSearch=GBY&companyId=ACME&locationId=&customerId=&supplierId=
HTTP 200
[{"ItemId": "GBY", "Source": "Item ID", "InvMastUid": "35923"}]
```

`Source` names *how* the term matched (`"Item ID"` here) — worth reading when `partSearch` is a barcode, customer part number, or supplier part number rather than a literal `item_id`, since the field tells you which of those it resolved through. Cross-search behavior across those other identifier types was not separately exercised.

---

## `accounting/customerformtemplates`

Per-customer document filenames — which report template a customer's invoice, RMA, packing list, and statement print jobs use. One record per customer, both created and updated through `PUT`, with **no separate create route** — the contract has no `POST` at all.

### Routes

| Route | Method | Notes |
|---|---|---|
| `/api/accounting/customerformtemplates/ping` | GET | Availability |
| `/api/accounting/customerformtemplates/new` | GET | **Verified** — blank template |
| `/api/accounting/customerformtemplates/` | GET | List. Unbounded — not run |
| `/api/accounting/customerformtemplates/` | PUT | **Verified** — create when `CustomerFormTemplateUid` is null, update when it is the real existing one |

> **There is no POST on this family.** A `POST` to `/api/accounting/customerformtemplates/` returns a **405**, an IIS-level "Method Not Allowed" HTML page, not a P21 error — the SDK contract (`ICustomerFormTemplateResource`) never declares one.

### `PUT` is not a blind upsert — correction from an earlier version of this page

The first verification run sent the `/new` template's `null` `CustomerFormTemplateUid` and got a clean create, which this page originally described as "`PUT` upserts." **Running the identical create a second time disproved that**, and the failure is exactly the kind a demo script catches that a single successful call does not:

```jsonc
// Same payload, second time, CustomerFormTemplateUid still null
HTTP 500
{"ErrorMessage": "The customer_form_template data already exists....CRUD Update error: Update failed for customer_form_template. (-1)", ...}
```

`PUT` with a null `CustomerFormTemplateUid` is **create-only** — the identical name is doing two jobs the parameter doesn't distinguish, and only the record's own key does. Sending the correct existing uid switches it to a real update:

```jsonc
// PUT /api/accounting/customerformtemplates/
{"CustomerFormTemplateUid": 1, "CustomerId": 12066, "CompanyId": "ACME", "InvoiceFilename": "ZZTEST2.rpt"}
HTTP 200
{"CustomerFormTemplateUid": 1, "CustomerId": 12066, "CompanyId": "ACME", "InvoiceFilename": "ZZTEST2.rpt", ...}
```

**Read the record first (or track the uid your own create returned) before calling `PUT` a second time for the same customer.** A null-uid `PUT` against a customer that already has a row does not update it — it fails.

---

## `service/serviceorders`

**The finding here is what the family actually is.** Its fields (`CustomerId`, `LocationId`, `PoNo`, `ContactId`, `Ship2Name`, `CarrierId`, `Terms`, `Class1id`–`Class5id`, `FreightCd`) are the shape of an ordinary P21 sales order header, and that is exactly what the read confirmed: `GET /api/service/serviceorders/{orderNo}` resolves against **any** `oe_hdr.order_no`, service-flagged or not.

### Routes

| Route | Method | Notes |
|---|---|---|
| `/api/service/serviceorders/ping` | GET | Availability |
| `/api/service/serviceorders/{orderNo}` | GET | **Verified** |
| `/api/service/serviceorders/{orderNo}` | PUT | Attempted; refused — see below |

There is **no create route** in the contract — this family only reads and updates orders created elsewhere (Order Entry, the Transaction API's `Order` service, or wherever a service order is actually raised).

### Verified read: an ordinary order number resolves

```jsonc
// GET /api/service/serviceorders/999991  -- an ordinary sales order, not
// specially flagged as a "service" order in any way this documentation
// controlled for
HTTP 200
{"Lines": null, "Salesreps": null, "Notes": null, "OrderNo": "999991",
 "CustomerId": 14278, "CompanyId": "ACME", "LocationId": 20,
 "PoNo": "Cylinder / Filter / Regulator", "ContactId": "10501",
 "Ship2Name": "ABC SUPPLY COMPANY", ...}
```

The same order also answers on the ordinary [`sales/tasks`](#salestasks) and Transaction API `Order` surfaces — this family is a differently-shaped **view** onto the same header, not a separate class of record with its own storage.

### The update path disagrees with the read path about whether the order exists

`PUT` on that same order number, changing nothing but one blank text field, was refused:

```jsonc
HTTP 500
<ImportReturn type="UPDATE">
  <ImportMessage severity="error">...Import Set No (A): 1: Unable to find Order Header using Order No (B): = 999991</ImportMessage>
  <ImportMessage severity="info">(Return value: -8, Import is ok but some records failed)</ImportMessage>
</ImportReturn>
```

The GET that produced the object being edited had just returned that exact order. Nothing was changed by the failed call — a read-back confirmed the field untouched — so the failure is clean, not a corrupting one, but the mechanism is unresolved: whether the update path's own Import Set logic only matches orders carrying some service-specific flag `oe_hdr` doesn't expose to a plain read, or requires `OrderNo` in a different type/format than the string the GET echoes, was not determined. Treat `PUT` on this family as **unverified pending a genuinely service-flagged order** to test against.

---

## `sales/opportunities`

CRM opportunity tracking. The routes are real and well-formed; **creation could not be exercised because the play tenant's own CRM configuration is empty** — this is a tenant-data gap, not an API defect, and the failure sequence below is worth reading as a demonstration of *how* to tell the two apart.

### Routes

| Route | Method | Notes |
|---|---|---|
| `/api/sales/opportunities/ping` | GET | Availability |
| `/api/sales/opportunities/new` | GET | **Verified** — template |
| `/api/sales/opportunities/{opportunityId}` | GET | Verified against the empty result set below |
| `/api/sales/opportunities/` | GET | List. Unbounded — not run |
| `/api/sales/opportunities/` | POST | Attempted; blocked by tenant configuration, not reproduced further |
| `/api/sales/opportunities/{opportunityId}` | PUT | Not exercised — no record exists to update |

### Why create could not be pushed to success

Each attempt narrowed the cause, and the narrowing is the useful part:

| Payload | Result |
|---|---|
| No `AssignedToId`, no `SalesrepId` | `"Required value missing for Opportunity Status Uid... Please enter a value."` |
| `SalesrepId: "812"` (a real buyer id, not a salesrep) | `"Invalid salesrep ID."` |
| `AssignedToId: "apiuser"` | `"Accessing the user ID default information has failed."` |

Following the first message to its source: `opportunity_status` over OData returns **`[]`** — this tenant has zero configured opportunity statuses. So does `opportunity_stage`, `opportunity_type`, and `opportunity_step`. **The CRM module's own lookup tables are empty on this tenant**, which means no payload can supply a valid `OpportunityStatusUid` — the route cannot succeed here regardless of what else is correct, and that is a fact about the tenant, not the API. The `AssignedToId` error's own cause was not separately isolated once the status-table gap was found, since fixing it would not have produced a working create either way.

**To actually exercise this route, find or stand up a tenant with the CRM/Opportunity module configured** — `opportunity_status`/`opportunity_stage`/`opportunity_type`/`opportunity_step` all populated over OData is the precondition check.

---

## `sales/consignmentusageorders`

Consignment usage orders — billing for material drawn down from a consignment stock arrangement. Blocked by the same shape of gap as opportunities: a required parent record this tenant doesn't have.

### Routes

| Route | Method | Notes |
|---|---|---|
| `/api/sales/consignmentusageorders/ping` | GET | Availability |
| `/api/sales/consignmentusageorders/new` | GET | **Verified** — template |
| `/api/sales/consignmentusageorders/{orderNo}` | GET | Not exercised — no record exists |
| `/api/sales/consignmentusageorders/` | GET | List. Unbounded — not run |
| `/api/sales/consignmentusageorders/` | POST | Attempted; blocked, not reproduced further |

### Why create could not be pushed to success

```jsonc
HTTP 500
<ImportReturn type="CREATE">
  <ImportMessage severity="error">...Import Set No (A): 1: Contract ID is required.</ImportMessage>
</ImportReturn>
```

A consignment usage order bills against an existing **consignment contract** — no `consignment_contract`-named OData object was found on this tenant to source a real contract id from, and P21's consignment pricing lives inside the `JobContractPricing` family already [documented in the Transaction API](03-Transaction-API.md#jobcontractpricing-service) under a different name. Establishing whether a `JobContractPricing` contract number satisfies this family's `ContractId`, and if so which contract type, is unresolved — recorded as the next concrete step rather than guessed at.

---

## `accounting/exchangerates`

Currency conversion rates. The route works; **the tenant's own single-currency configuration is what stops a create from succeeding**, and the one validation that did fire is real and useful on its own.

### Routes

| Route | Method | Notes |
|---|---|---|
| `/api/accounting/exchangerates/ping` | GET | Availability |
| `/api/accounting/exchangerates/` | GET | **Verified** — returned `[]` |
| `/api/accounting/exchangerates/` | POST | Attempted; blocked by the tenant having one currency |

### The tenant has exactly one currency

`GET /api/accounting/exchangerates/` returning `[]` is not a null-vs-empty ambiguity to chase — `currency_hdr` over OData confirms it directly: **`currency_id: 1` (U.S. Dollars) is the only row.** Every `CurrencyId` seen anywhere else in this documentation (GL lines, PO headers) is `1` for the same reason.

### The one validation that did fire

```jsonc
// POST with CurrencyId and ToCurrencyId both 1
HTTP 500
{"ErrorMessage": "The currencies cannot be the same. (-1)", ...}
```

That confirms the route enforces a real business rule rather than accepting anything — but a genuine create, and the response shape a rate actually takes, needs a tenant with a second currency configured to observe.

---

## `inventory/serialnumberextdinfo`

Extended data (comments, area/dimension adjustments) attached to a specific tracked serial number. **Refusal verified against a real, existing serial; success not reproduced** — the same shape of open question as [`createWmsTagAdjustment`](#createwmstagadjustment-createwmstagadjustmentwithcost-refusal-verified-success-not-reproduced).

### Routes

| Route | Method | Notes |
|---|---|---|
| `/api/inventory/serialnumberextdinfo/ping` | GET | Availability |
| `/api/inventory/serialnumberextdinfo/{uid}` | GET | Not exercised — no extended-info row exists on this tenant to key against |
| `/api/inventory/serialnumberextdinfo/?itemId={id}&serialNumber={sn}` | GET | Not exercised |
| `/api/inventory/serialnumberextdinfo/` | GET | List. Not exercised |
| `/api/inventory/serialnumberextdinfo/` | PUT | Attempted against a real serial; refused — see below |

The [`serial_number_extd_info` OData table](02-OData-API.md) itself is empty on this tenant — no row exists anywhere to read, so the GET routes above have nothing to confirm against even though their shape is not in question.

### A missing field corrupts the error message, not just the request

The first attempt sent `InvMastUid` (the natural-looking key) and a real, currently-existing serial number (`serial_number.serial_number = "1"`, `inv_mast_uid = 74298`, confirmed over OData):

```jsonc
HTTP 500
"ErrorMessage": "Invalid serial number 1 for item 1 on line number %s. Process aborted during setup...."
```

**"item 1" and the literal `%s` are template placeholders that never got filled in** — the real item id is `6408-HHP-06`, not `1`. Adding `InvMastItemId` (present on the domain object, read-only-looking, easy to assume is server-derived) to the payload fixed the error text itself:

```jsonc
HTTP 500
"ErrorMessage": "Invalid serial number 1 for item 6408-HHP-06 on line number 1. Process aborted during setup...."
```

Correctly formatted now — and still refused, against a serial number that genuinely exists for that exact item. **`InvMastItemId` is read by the backend despite looking derived, and omitting it degrades the diagnostic on every other failure this route can produce, not just this one.** Whatever the real precondition for a successful `PUT` is here remains open; send `InvMastItemId` regardless; the fix so far only makes the error message trustworthy.

---

## Open questions

Recorded so the next person does not have to rediscover that they are open. Shorter than it was: `userdefinedfields/generate`, `accounting/gl` POST, the PO create/update/async family, and two of the four `createWms*` routes were all exercised live on 26.1.5950.0 and are documented above.

- **`purchasing/purchaseorders/async/callback`** — the webhook-style variant, taking a callback URL. Not exercised; it needs a reachable endpoint to receive the callback, which a documentation pass against a shared test tenant cannot safely stand up alone.
- **`createWmsTagAdjustment` / `createWmsTagAdjustmentWithCost` on a genuinely tag-controlled item.** The refusal path is fully verified (`"{item} is not a tagged item"`), reproduced on two different items including one with `inv_mast.use_tags_flag = 'Y'`. The success path is not — that flag alone did not satisfy the precondition, no `tag`-named OData object exists to inspect existing tag records, and it is unresolved whether the real requirement is a live physical tag created through receiving/putaway rather than anything settable through this endpoint or the item master.
- **Whether the Transaction API's async no-cancel hazard also applies to `purchasing/purchaseorders/async`.** Both endpoints share the shape (submit, poll by `RequestId`); [the Transaction API's async path is documented as having no cancel route](03-Transaction-API.md#endpoints), and this family's own `/help` publishes no cancel operation either, which is suggestive but was not independently confirmed by trying to cancel a real request.
- **Whether GL posting requires an open period, or merely tolerates one.** Confirmed: `period_closed eq 'N'` posts cleanly. Not tested: whether a closed period is rejected with a clear error or produces something worse.
- **Whether any family has a filter parameter at all.** `$top`, `$filter`, `page`/`pageSize`, `limit` and `top` were all ignored on `sales/tasks`. If a supported parameter exists it is not in `/help` and not guessable — which is why [OData](02-OData-API.md) is the query surface in every example above.
- **`inventory/serialnumberextdinfo` PUT against a real serial still refuses.** Sending the correct `InvMastItemId` fixes the error message but not the outcome — see [the write-up above](#inventoryserialnumberextdinfo). The real precondition is unresolved.
- **`service/serviceorders` PUT disagrees with its own GET about whether an order exists.** [Documented above](#serviceserviceorders) with the exact error; whether a genuinely service-flagged order behaves differently was not tested — this tenant's real orders used for verification elsewhere in this documentation are ordinary sales orders, not service orders.
- **`sales/opportunities` and `sales/consignmentusageorders` creation, on a tenant with the relevant module actually configured.** Both are blocked here by empty lookup tables and a missing contract prerequisite respectively, not by anything the API itself refuses — see each section above for the exact precondition to satisfy first.
- **`accounting/exchangerates` creation, on a tenant with a second currency.** The one validation this tenant could exercise (`"The currencies cannot be the same"`) confirms the route enforces real rules; a genuine create and its response shape are unverified.
- **The two tag-relocation routes on `inventory/inventorymovement`** (`moveinventorytagtobin`, `moveinventorytagtocontainer`) — same tagged-item gap as `createWmsTagAdjustment`, not independently re-investigated.

---

## See Also

- [Entity API](05-Entity-API.md) — the 4 `/api/entity/` entities, and [how to list the families your tenant exposes](05-Entity-API.md#discovering-what-your-tenant-actually-exposes)
- [Inventory REST API](11-Inventory-REST-API.md) — `/api/inventory/parts`
- [OData API](02-OData-API.md) — the query surface these families lack
- [Transaction API](03-Transaction-API.md) — the verified write path for POs and inventory adjustments
- [Authentication](00-Authentication.md) — tokens, and the `Accept` header these families share
