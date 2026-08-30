# P21 Breaking Changes by Version

> **Disclaimer:** This is unofficial, community-created documentation for Epicor Prophet 21 APIs. It is not affiliated with, endorsed by, or supported by Epicor Software Corporation. All product names, trademarks, and registered trademarks are property of their respective owners. Use at your own risk.

---

## Overview

A version-indexed registry of P21 middleware changes that **break or silently corrupt existing API integrations**. Every entry here was found the hard way during real upgrade validation and verified live. Most were also confirmed **not** to occur on the prior version; where no prior-version tenant was still available to A/B against, the entry **says so explicitly** rather than implying a comparison we didn't make. Check this page **before** any P21 upgrade, and re-test the listed surfaces on your own test tenant first.

| Version | Still live on the latest build we have | Resolved | Severity |
|---------|---------|----------|----------|
| [2026.1](#p21-20261) | `SessionId` → `Id` · `TabName` no longer accepted on `/v2/tab` · **silent-false-success on nonexistent-record loads** · **batched changes are sequential and fail-fast** · **UDT update/delete can't target rows (delete silently no-ops)** · **`IgnoreDisabled` reports success on writes that write nothing** · **a bad `DatawindowName` eats the next request on that window** | [Empty 500 without `Accept: application/json`](#1-interactive-api-returns-an-empty-http-500-without-an-explicit-accept-applicationjson-header) and the [ghost sessions](#2-ghost-sessions-the-failed-create-still-half-creates-the-session-alternating-500409) it caused — both fixed in **26.1.5940.0** | High — four data-integrity hazards |
| [25.2](#p21-252) | `DatawindowName` required in change requests | — | High — hard break for 3-param change calls |

> **Resolved entries stay on this page.** A fix in a later 2026.1 build does not help you if you are upgrading *from* an affected one, and the symptom is what you will search for when it bites. Resolved entries are marked at the top and moved to the end of their version's section.

---

## P21 2026.1

Originally found on **2026.1.5873.1** during upgrade validation (June 2026), where none of it reproduced on 2025.2.5855.0 with identical requests. Re-verified against **26.1.5894.1** (July 2026) and **26.1.5910.3** (August 2026), then re-run in full against **26.1.5940.0** (August 2026).

**On 26.1.5940.0, entries 3–8 all still reproduce**, with the refinements noted in each. **Entries 1 and 2 are fixed** and have moved to [Resolved in a later 2026.1 build](#resolved-in-a-later-20261-build) at the end of this section. **Entry 6's mechanism is sharpened** — the batch turns out to be sequential and fail-fast, which is a more useful rule than "not atomic". **Entry 9 is new**, and it inherits entry 1's symptom: an empty HTTP 500 on the interactive surface now means something else entirely.

> **Read entry 9 before you debug an empty 500 on a current build.** The empty-500 signature that entry 1 made famous no longer comes from the `Accept` header. It comes from [a bad `DatawindowName` on the *previous* request](#9-a-bad-datawindowname-eats-the-next-request-on-that-window-empty-http-500).

The empty-500 defect was reported to Epicor and is fixed as of 5940.0; the contract changes are still awaiting written confirmation of intent.

> **Finding your build:** there is no version endpoint, but the session-create response carries it — `Properties[0].Properties.fullversion` (e.g. `26.1.5940.0`) and `shortversion` (`26.1`). See [Reading the middleware version](#reading-the-middleware-version) below. **Which entries apply to you depends on this number**, so read it before trusting the page.

### 3. Session-create response field renamed: `SessionId` → `Id`

`POST /api/ui/interactive/sessions/` returns the session identifier under **`Id`** on 2026.1; 2025.2 returned **`SessionId`**.

**Mitigation:** read both (`data.get("Id") or data.get("SessionId")` / the C# equivalent) so one client works across versions.

Still `Id` on 26.1.5940.0 — the rename was permanent, not a transitional build.

### 4. `PUT /v2/tab` no longer accepts `TabName`

2026.1 binds **`PageName`** (PagePath structure) only; 2025.2 also tolerated `TabName` in the body. Requests still sending `TabName` stop working.

```json
PUT /api/ui/interactive/v2/tab
{"WindowId": "{windowId}", "PageName": "TP_ITEMS"}
```

**Mitigation:** none needed if you follow the documented v2 shape — this repo has always documented `PageName` ([Interactive API § Changing Tabs](04-Interactive-API.md#changing-tabs)). Audit any legacy client for `TabName` in tab-change bodies.

**`TabName` is ignored, not rejected — which matters for the error message you get.** Verified on 26.1.5910.3 and re-verified unchanged on **26.1.5940.0**, against `SalesPricePage`, switching tabs and reading back which datawindow the window exposes:

| Body | Result |
|---|---|
| `{"PageName": "VALUES"}` | 200 — switched |
| `{"TabName": "COSTS"}` | **400** — `Tab with name or display text of  does not exist.` |
| `{"TabName": "COSTS", "PageName": "COSTS"}` | 200 — switched |
| `{"TabName": "VALUES", "PageName": "COSTS"}` | 200 — switched to **COSTS** |

The last row is the proof: when the two disagree, `PageName` wins and `TabName` contributes nothing. So a client that sends **both** — as some cross-version clients do to support 25.2 and 26.1 from one code path — is safe here; only `TabName` *alone* fails.

Note the error text when it does fail: **the tab name in the message is blank**, because the server is reporting on the `PageName` it never received rather than on the `TabName` you sent. It reads as "your tab name is wrong" when the real problem is the field name. If you see `Tab with name or display text of  does not exist.` with that empty slot, check the *key* you used before you check the tab.

### 5. Silent false success: loading a nonexistent record returns `Status: 2` with an **empty window**

**Data-integrity hazard.**

On 2026.1, keying a window to a record that doesn't exist (e.g., setting `po_no` to a nonexistent PO) returns **`Status: 2`** and leaves the window **empty**. 2025.2 returned `Status: 0` for the same action. An integration that treats "not found" as `Status: 0` — or that doesn't gate on load status at all — will **silently proceed to write against an empty window**.

The response does carry a diagnostic, which the original report missed — a successful load returns `Messages: []`, while the nonexistent-record load returns:

```json
{"Status": 2, "Events": [{"Name": "dwcontentchanged", "Data": [...]}],
 "Messages": [{"Text": "Enter a valid ID or leave ID blank.", "Type": 2}]}
```

So the failure is detectable in-band. It is still a false-success hazard for any client that gates on `Status` alone, because `Status: 2` on a *load* is easy to mistake for a benign non-success, and the window is left silently empty and writable.

Re-verified on **26.1.5940.0**, `PurchaseOrder` keyed by `po_no`, against a control that loaded a real PO in the same run: the real PO returns `Status: 1`, `Messages: []` and a populated `tp_1_dw_1`; the nonexistent one returns `Status: 2`, the message above, and a datawindow that is present but empty. Both are HTTP 200.

**Mitigation (verified):** do not infer existence from the load status at all. Gate with an **existence pre-read** (OData or `POST /api/v2/transaction/get`) *before* opening/keying the window, and abort on no-match. Treat any non-Success load status as fatal, and inspect `Messages` when logging the reason.

### 6. Batched `/v2/change` is not atomic — it is sequential and fail-fast

**Data-integrity hazard.**

`PUT /v2/change` takes a `List` of field changes but returns **one top-level result for the whole batch** — there is no per-item status. When one item is rejected, the call returns an **HTTP 400 error envelope with no `Status` field at all**, and the batch is **not** rolled back.

**The rule, verified on 26.1.5940.0: the list is applied in order and stops at the first rejection.** Fields *before* the bad one are applied and stay applied; fields *after* it are never attempted. So a field's **position in the list** decides whether it survives — which is why the same two-field batch gives opposite results depending only on the order you wrote it in. PurchaseOrder keyed to an existing PO, `company_id` as the disabled field, no save issued, read-back after each:

| Batch | Response | `external_po_no` after |
|---|---|---|
| `[external_po_no, company_id]` | `400 Column is disabled: company_id` | **`ZZ_HDR` — applied** |
| `[company_id, external_po_no]` | `400 Column is disabled: company_id` | `''` — never attempted |

```jsonc
// The first row above, in full
[{"TabName": "TABPAGE_1", "DatawindowName": "tp_1_dw_1", "FieldName": "external_po_no", "Value": "ZZ_HDR"},
 {"TabName": "TABPAGE_1", "DatawindowName": "tp_1_dw_1", "FieldName": "company_id",     "Value": "XX"}]

// Response: HTTP 400 — note there is no Status field to check
{"ErrorMessage": "Column is disabled: company_id", "ErrorType": null, ...}
// ...but a read-back shows external_po_no == "ZZ_HDR" — applied and still in the buffer.
```

A client that treats the 400 as "the change did not happen" is wrong: part of it did, and *which* part depends on list order. If it then retries or falls through to a save, it commits a partially-applied edit it never intended.

> **Sequential fail-fast is the precise claim; "not atomic" was the observable.** The earlier framing was correct about the consequence and vague about the cause — it left open whether surviving fields were applied at random or by rule. They are applied by rule, and the rule is worth knowing: it means a batch whose risky field is **first** fails cleanly with nothing applied, while the same batch with the risky field **last** leaves everything before it committed to the buffer. That is a footgun you can reason about rather than merely fear.

**Mitigation (verified):** write **one field per `/change` call** and check the status of every call, so a failure is unambiguously attributable to one field. Then prove the result with a **read-back** — see [Verifying Writes](04-Interactive-API.md#verifying-writes-dont-trust-save-status-alone). A production run of 81 records using this pattern read back with zero silent drops.

> **Correction (July 2026).** This entry originally reported the mechanism as *"a batch containing a field on a **non-active tab** returns `Status: 1` while silently not applying that field."* That does **not** reproduce on 26.1.5894.1. Across eight configurations on the PurchaseOrder window — batched and single-field, `DatawindowName` supplied and omitted, target tab active and inactive — the non-active-tab field was **applied every time** with `Status: 1`. The original observation was made on 26.1.5873.1, which is no longer available to re-test, so we cannot distinguish "fixed in a later build" from "misattributed mechanism" — and the batch **is** genuinely non-atomic, which produces the same end result (a partially-applied batch) by a different route. The one-field-per-call mitigation was correct and is unchanged.
>
> **Re-tested again on 26.1.5910.3 (August 2026), still no reproduction.** PurchaseOrder, no save issued: with `TABPAGE_1` active, a write to `supplier_ship_date` on `TABPAGE_18` returned `Status: 1` and the value **was present** in the buffer after switching to that tab — matching the control that switched tabs first. The specific field named in the original 5873.1 report therefore applies normally on this build.
>
> **The 5894.1 repro is also dead as of 5940.0, for an unrelated reason.** That example used `TABPAGE_18.extended_info.extended_desc` as its disabled field; on 5940.0 that column is **no longer disabled** and writes cleanly (`Status: 1`, value in the buffer). Nothing about entry 6 changed — the field did. The table above re-establishes the behavior with `company_id`, which is disabled on a saved PO on every build we have tested. Worth noting generally: **which columns a window disables shifts between builds**, so a repro pinned to one field name has a shorter shelf life than the behavior it demonstrates.
>
> **Write tab-by-tab anyway.** The client that filed the original report still groups its field writes by tab and switches before each group, and that remains the right shape regardless of which build you are on: it costs one `/v2/tab` call per tab, removes the question entirely, and matches how the window behaves for a human. Treat it as cheap insurance, not as a workaround for a bug we can currently demonstrate.

### 7. UDT Service update/delete cannot target rows in a UDT created on 2026.1

**Data-integrity hazard — silent false success on delete.**

> **Verification scope:** unlike entries 1–6, this one has **no prior-version comparison** — by the time it was found, no pre-2026.1 tenant remained available. What follows is verified on 2026.1; whether it is a *regression* or has always depended on how the table was created is **unproven**. Treated as a 2026.1 hazard because 2026.1's table-creation UI is what produces the incompatible shape.
>
> **Partially re-verified on 26.1.5940.0 (August 2026).** The `row_uid` existence probe, the update `400 {"error":["Invalid Row Uid!"]}` for *every* condition name — including the table's real primary key — and the nested-`conditions` payload trap all reproduce verbatim. **The delete half could not be re-tested**: the tenant available for the re-run carries no user-created UDT (its only `udt_*` table is a P21 system table), so the `[0] rows deleted ... successfully!` silent no-op is carried forward on the original July 2026 verification rather than re-confirmed. Flagged rather than quietly restated, because that half is the dangerous one.

`PUT /udtservice/api/udtdata/updateudtdata` and `DELETE .../deleteudtdata` identify rows by a column named **exactly `row_uid`**. P21's **User Defined Table Maintenance** on 2026.1 names the primary key **`udt_{tablename}_uid`** and creates **no** `row_uid` column — so on any UDT built there, neither endpoint can reach a single row:

```jsonc
// Update — returns this for EVERY condition: the real PK name, any other
// column, any casing, value as string or int.
400 {"error": ["Invalid Row Uid!"]}

// Delete — HTTP 200, and nothing is deleted.
200 {"id": 0, "errorNo": 0,
     "errorMessage": "[0] rows deleted from [udt_bulk_probe] table successfully!"}
```

The delete is the dangerous half. `errorNo: 0` and the word *"successfully"* read as a clean delete to any client checking status or `errorNo` — **only the `[0]` row count reveals it did nothing.** A purge or retention job built on this reports success indefinitely while the table grows without bound.

> **This is a naming mismatch, not a missing identifier — which is why it reads as a defect.** P21's own documentation for the maintenance windows this UI generates describes a **Row ID** field at the top of every generated window: *"To create a new database entry, populate the fields while leaving Row ID blank and save... To edit an existing entry, enter that row's ID to recall its values... To delete an existing database row, recall it with the Row ID, check Delete Row, and save."* It is also *"always a searchable field"*, unlike the others.
>
> So the per-row identifier the API says it needs **does exist and the UI uses it for exactly these three operations** — it is simply surfaced as "Row ID" over the `udt_{tablename}_uid` primary key, while the service accepts only a column named literally `row_uid`. The window and the service disagree about the name of the same thing. *(Source: P21 26.2 help, System Administration > Creating a User-Defined Database Table.)*

Confirm the column is genuinely absent rather than mis-typed:

```http
GET /odataservice/odata/table/{udt}?$select=row_uid
→ 404 "Could not find a property named 'row_uid' on type 'dbo.{udt}'."
```

**Mitigation:** before relying on UDT update/delete, **check that `row_uid` exists** (above). If it doesn't, these endpoints cannot reach your data at all — use P21's maintenance UI or direct SQL, and don't build an integration on them. Where they *do* work, **parse the `[N]` row count out of `errorMessage`** and treat `[0]` as a failure; never trust `errorNo: 0` alone. The `row_uid` convention is well-attested by the contributors who first documented these endpoints, so tables predating 2026.1 evidently do carry the column. Full detail: [UDT Service API § Update](13-UDT-Service-API.md#update).

Related payload trap: **delete reads `conditions` from the payload's top level**, not nested inside `rows[]` — the nested form returns `400 {"error":["Conditions cannot be blank or none!"]}` on 2026.1. See [UDT Service API § Delete](13-UDT-Service-API.md#delete).

### 8. `IgnoreDisabled: true` reports success on writes that write nothing

**Data-integrity hazard — silent false success.**

> **Verification scope:** like entry 7, this one has **no prior-version comparison** — no earlier build was available to A/B against. What follows is verified on 26.1; whether it's a *regression* or has always been true is **unproven**.

Writing `VALUES.values` on an **existing** `JobContractPricing` contract line is refused — including on the exact case this repo documents as a working update (an active contract, `end_date` well in the future, on a Source-priced line):

```jsonc
{
  "Summary": {"Failed": 1, "Succeeded": 0, "Other": 0},
  "Messages": [
    "Transaction 1:: General Exception: Tab page is disabled and cannot be selected",
    "Transaction 1: VALUES.values: Error processing data element: values : Tab page is disabled and cannot be selected"
  ]
}
```

Resending the line's `pricing_method` / `source_price` / `multiplier` alongside `values` in the same transaction, to try to re-trigger the cascade that unlocks the tab, does not help — identical failure.

**All three write paths for `VALUES.values` are refused, identically:**
1. Updating `values` on an existing contract line.
2. Inserting a new line (keyed upsert on `item_id`) onto an *existing* contract, with `VALUES.values` in the same transaction — fails atomically; the line is not created.
3. Creating a brand-new contract (header + a fully specified Source-priced line + `VALUES.values`) in one transaction — also fails atomically; the contract is not created.

All three return the identical `General Exception: Tab page is disabled and cannot be selected`, confirmed by read-back in each case.

**Control — this isolates the finding to the `VALUES` DataElement specifically.** The identical create transaction (header + Source-priced line) with the `VALUES` DataElement *removed* succeeds: `Succeeded: 1`, and read-back confirms both the contract and the Source-priced line were created. Contract and line creation through the Transaction API work fine; it is specifically writing `VALUES.values` that the disabled-tab check refuses, on all three paths above.

Adding **`IgnoreDisabled: true` at the payload top level** (the [documented unlock](03-Transaction-API.md#ignoredisabled) for disabled columns and sub-tabs) flips the response to a clean-looking success:

```jsonc
{
  "Summary": {"Failed": 0, "Succeeded": 1, "Other": 0},
  "Results": {"Transactions": [{"Status": "Passed", "DataElements": [ /* header only */ ]}]}
}
```

...and writes **nothing**. A read-back of the target row shows it unchanged: in one run an existing value of `42.50` survived a `"Passed"` response; in another the value was still absent. The echoed response doesn't reveal the omission either — it drops the `JOBPRICELINE` and `VALUES` DataElements entirely and echoes only the header, so there's nothing in the response to notice is missing.

Both the correct tier-1 field name (`calculation_value1`) and the incorrect unsuffixed spelling (`calculation_value`) fail identically — this is not a field-naming issue.

**It is not limited to the `VALUES` tab — it is how the flag fails generally.** The same false success appears on a disabled *column*. `corp_address_id` on the contract header is read-only once the contract is saved; without the flag the write is refused loudly:

```text
General Exception: Column is disabled: corp_address_id
```

Add `IgnoreDisabled: true` and the identical payload returns `Summary: {"Failed": 0, "Succeeded": 1}` — and a read-back shows the value unchanged (verified 26.1.5910.3, 2026-08-11, on a throwaway contract).

**And it is not limited to `JobContractPricing`.** The same shape reproduces on `Order` (26.1, 2026-08-19; re-verified on **26.1.5940.0**, 2026-08-26, with the note read back unchanged before and after). `LINE_NOTE.line_note` is published in the `Order` definition as an ordinary keyed `List`, but every one of its columns is disabled; without the flag the write is refused loudly:

```text
General Exception: Column is disabled: note
```

Add `IgnoreDisabled: true` — payload otherwise byte-identical — and it returns `Summary: {"Failed": 0, "Succeeded": 1}`, `Status: "Passed"` and no messages, while a `/transaction/get` read-back shows the note **unchanged**. The echoed transaction drops the `LINE_NOTE.line_note` element entirely and returns only `TABPAGE_1.order`, so nothing in the response marks the omission. That was three unrelated services showing the same false success, which is what marked this as a platform behavior rather than a `JobContractPricing` quirk.

**A fourth service, and the same signature again** (26.1.5940.0, 2026-08-30). The `ProductionOrder` window's header-note grid — `PROD_ORDER_HDR_NOTE_TAB.prod_order_hdr_note_tab`, keyed `note_uid` — behaves identically. Without the flag:

```text
General Exception: Column is disabled: note
```

With `IgnoreDisabled: true`: `Summary: {"Failed": 0, "Succeeded": 1}`, `Status: "Passed"`, no messages, the echoed transaction reduced to `TABPAGE_1.tp_1_dw_1` alone — and the note's `date_last_modified` still reading its original value five weeks earlier. Row *creation* on the same grid behaves the same way (`Column is disabled: topic` without the flag, clean false success with it), with or without `Keys`. The working path for those notes is the [Interactive popup](04-Interactive-API.md#production-order-notes-header).

**The contrast case matters as much as the failures.** On the same build, minutes apart, `IgnoreDisabled: true` genuinely unlocked a write: inserting a location supplier row on the `Item` window (`SUPPLIER_X_LOCATION.supplier_x_location`, keyed on **both** `location_id` and `supplier_id`) returned `Succeeded: 1` and the row was really there on read-back. The control — same element, `Keys: ["supplier_id"]` alone and no flag — failed loudly with `Column is disabled: location_id` and wrote nothing. So the flag's two outcomes are not split by service, or by window, or by anything you can see in the request: [the same service](03-Transaction-API.md#adding-a-location-supplier-row-the-prerequisite-insert) produces both.

So `IgnoreDisabled` has two outcomes that are **indistinguishable in the response**: it genuinely unlocks the write (as it does for contract BINS quantities, JOBPRICECOST commission fields and the location supplier insert above), or it swallows the refusal and writes nothing. You cannot tell which you got without reading the record back.

**Mitigation:** always read back after any write that used `IgnoreDisabled: true`, on any service — whether updating an existing line, inserting a new line, or creating a brand-new contract. Treat `Status: "Passed"` under `IgnoreDisabled` as **unverified** until a read-back confirms the value actually changed; per the control above, the Transaction API cannot currently be relied on to write `VALUES.values` at all, on any of the three paths. See [Transaction API § IgnoreDisabled](03-Transaction-API.md#ignoredisabled) and [Verifying Writes](04-Interactive-API.md#verifying-writes-dont-trust-save-status-alone) for the same read-back discipline applied elsewhere in this repo.

### 9. A bad `DatawindowName` eats the **next** request on that window (empty HTTP 500)

**Diagnosis trap — and the reason an empty 500 no longer means what entry 1 says it means.**

Naming a datawindow the window doesn't have returns a clean `400 "Unable to find datawindow named {name}"` and applies nothing. That much is [documented below](#a-nonexistent-datawindowname-fails-loudly-not-silently) and is fine. What is not fine is what happens to the **next** call on that window: it returns an **empty-body HTTP 500** and does nothing, whatever kind of call it is.

Verified on 26.1.5940.0, PurchaseOrder keyed to an existing PO, deterministic across 4/4 runs:

```text
PUT /v2/change  {"DatawindowName": "dw_1", ...}    → 400  "Unable to find datawindow named dw_1"
PUT /v2/change  {  a perfectly valid change    }    → 500  <empty body>   <- eaten, applies nothing
PUT /v2/change  {  the same valid change again }    → 200  Status: 1, value applied
```

The burnt call does not have to be a change — `GET /v2/data` and `PUT /v2/tab` are consumed the same way if either is what follows the 400. It is exactly **one** request, and the window is healthy again afterward; no session reset or window reopen is needed.

**It is specific to this error, not to 400s in general.** The control is a `Column is disabled` 400, which is the other 400 you routinely hit on this surface:

| Preceding error | Next request on that window |
|---|---|
| `400 Unable to find datawindow named dw_1` | **500, empty body — applies nothing** |
| `400 Column is disabled: company_id` | 200, applies normally |

**Why this one matters out of proportion to its size.** [Entry 1](#1-interactive-api-returns-an-empty-http-500-without-an-explicit-accept-applicationjson-header) taught a generation of P21 integrations that an empty 500 on the interactive surface means a missing `Accept` header. That defect is **fixed** as of 26.1.5940.0 — so on a current build, an empty 500 here is this instead, and chasing the header will waste the afternoon. The two are easy to tell apart: entry 1's fires on **session-create, every time**; this one fires **once, immediately after a 400 you already received**.

**Mitigation:** get the datawindow name right — `GET /api/v2/definition/{Service}` or the committed [`definitions/{Service}.json`](../definitions/README.md) lists every `TAB.datawindow` pair for the window, so there is no reason to guess. If you do take the 400, treat the following request as **lost**: re-send it, and check its result rather than assuming the first attempt landed. A client that retries the *failed* change but not the one after it will silently drop a field — the 500 carries no body to tell you otherwise.

### Related 2026.1 observations (not breaking changes)

Found while re-verifying the above on 26.1.5894.1, and re-checked on 26.1.5940.0. None of these are regressions, but each will mislead you while debugging one.

#### Reading the middleware version

**There is a version endpoint — it is just not where you would look for it.** `/api/version`, `/api/v2/version`, `/api/ui/version` and `/version` all 404 on the UI server. The build is reported by **`GET {uiserver}/ui/common/v1/serverinfo`** (undocumented, same bearer auth, `Accept: application/json` or you get XML), and by the **session-create response**.

**Prefer `serverinfo`: it needs no session.** That matters precisely here, because the interactive surface is what these entries break — if session-create is failing you cannot read the version from it, which is exactly when you need to know which entries apply. Read `Version/Application Version`, not `Monitoring/shortversion` — the latter returned `"0.0"` on 26.1.5930.1 while carrying a real value on 26.1.5940.0. Full response shape, key table and runnable examples: [Authentication § Server Info Endpoint](00-Authentication.md#server-info-endpoint-version-environment-detection).

The **session-create response** carries the same build, and is worth knowing as the fallback:

```jsonc
POST {uiserver}/api/ui/interactive/sessions   // Accept: application/json
{
  "Id": "3c2aca0b-...",
  "Properties": [{"Name": "Telemetry", "Properties": {
      "fullversion": "26.1.5940.0", "shortversion": "26.1", "configurationid": "3694", ...
  }}]
}
```

This is the most reliable way to confirm which build you are actually talking to before trusting any entry on this page — and on this page it is now load-bearing, because [entries 1 and 2](#resolved-in-a-later-20261-build) apply to some 2026.1 builds and not others.

The same response also carries the session-handling configuration you will want when debugging [entry 2](#2-ghost-sessions-the-failed-create-still-half-creates-the-session-alternating-500409) — `SessionHandling.SessionCleanupExpiration` (`00:06:00` on the tenants we have measured), `TimedCleanupInterval`, `PoolSize` and `WarmStartCount`.

**This probe needs a session; `serverinfo` above does not.** A tenant refusing session-create will not tell you its build this way — which is precisely when you most want to know — so reach for `serverinfo` first and keep this as the fallback. `/api/version`, `/api/v2/version`, `/api/ui/version` and `/version` were all re-probed on 5940.0 and all four still 404.

#### The middleware runtime, and what it does not dictate

Epicor attributes 2026.1's platform work to *".NET Platform Modernization: migration to .NET 10 and a re-architected middleware home page"*. It is reasonable to suspect that migration is behind the content-negotiation and contract changes on this page, and Epicor has not confirmed that, so treat the link as circumstantial.

What matters for integration work is how little it dictates:

| | Runtime |
|---|---|
| **P21 middleware** (server side) | .NET 10 as of 2026.1 — Epicor's, not yours to choose |
| **DynaChange business rules** | **Both .NET and .NET Framework are supported, for now** |
| **Your API client** | Anything that speaks HTTP. This repo's C# examples target [`net8.0` or later](../examples/csharp/README.md) |

**The server moving to .NET 10 did not drag business rules with it.** Rule code can still target .NET Framework as well as modern .NET. Read "for now" as load-bearing — dual support is a transition state rather than a commitment, so new rules are better written against modern .NET than against Framework, and existing Framework rules are worth treating as migration debt with an unannounced due date.

**Nothing about your client's runtime changed either.** The examples here build and run on `net8.0` through `net10.0`, and the one .NET-specific hazard in this documentation — [`HttpClient` dropping `Authorization` across a redirect](06-Error-Handling.md#401-authorization-header-was-not-present-or-bearer-was-missing) — behaves **identically on .NET 9.0.19 and .NET 10.0.11**, re-verified against 26.1.5940.0. That is deliberate `HttpClient` behavior, so no runtime upgrade will fix it for you.

#### `GET /v2/data` returns only a *subset* of the window's datawindows

The response is a list of datawindow objects, and **which ones appear varies between calls** on the same window — immediately after a load it returned `tp_1_dw_1` + `tp_17_dw_17`; after a change touching the ship-to tab it returned `ship_to` + `tp_17_dw_17` and **omitted `tp_1_dw_1` entirely**. A datawindow's absence therefore proves nothing about the field's value.

Reproduced exactly on 26.1.5940.0, same window and same two calls — the response tracks *the tab you last touched*, not the window's full contents:

```text
after keying po_no          → ['TABPAGE_1.tp_1_dw_1', 'TABPAGE_17.tp_17_dw_17']
after a SHIP_TO field write → ['SHIP_TO.ship_to',     'TABPAGE_17.tp_17_dw_17']   <- tp_1_dw_1 gone
```

Consequence for verification: `/v2/data` is not a reliable field-level read-back. Activate the field's tab first (which reliably brings its datawindow into the response), or verify out-of-band with OData / `POST /api/v2/transaction/get` — the approach [Verifying Writes](04-Interactive-API.md#verifying-writes-dont-trust-save-status-alone) already recommends.

#### A nonexistent `DatawindowName` fails loudly, not silently

Naming a datawindow that doesn't exist on the window returns **HTTP 400 `"Unable to find datawindow named dw_1"`** and applies nothing. This is worth knowing precisely *because* it is not a silent-failure mode: if you are hunting a field that "didn't take", a wrong datawindow name is not the culprit — you would have seen a 400.

> **But it is not free.** The 400 itself is loud; the request *after* it is silently destroyed. That is [entry 9](#9-a-bad-datawindowname-eats-the-next-request-on-that-window-empty-http-500) — read it before you write a retry path around this 400.

Relatedly, on 26.1 `DatawindowName` is **optional for header-level fields** — `{"TabName": "SHIP_TO", "FieldName": "ship2_name", "Value": "..."}` with no `DatawindowName` resolves by tab + field and applies correctly. Supplying the correct name also works. Keep sending it: it is still **required** on 25.2 (see [below](#p21-252)), so including it is what makes one client work across both versions.

Re-verified on 26.1.5940.0, each on a clean window with a read-back — **omitted, `""` and `null` are all equivalent to supplying the right name**:

| `DatawindowName` sent | Result |
|---|---|
| `"tp_1_dw_1"` (correct) | 200, applied |
| *(key omitted)* | 200, applied |
| `""` | 200, applied |
| `null` | 200, applied |
| `"dw_1"` (nonexistent) | **400**, applies nothing — and burns the next request ([entry 9](#9-a-bad-datawindowname-eats-the-next-request-on-that-window-empty-http-500)) |

The first run of this matrix appeared to show the omitted form returning an empty 500. It did not — that run followed a `dw_1` probe, and what it actually measured was entry 9. On a clean window the optional form has never failed. Worth stating because it is the exact trap entry 9 sets: **one bad datawindow name upstream will make the next thing you test look broken.**

---

---

## Resolved in a later 2026.1 build

The two entries below **no longer reproduce on 26.1.5940.0**. They are kept because they still bite anyone upgrading *from* an affected build, and because their symptoms are what you will search for when they do. Each carries its fix build at the top.

### 1. Interactive API returns an empty HTTP 500 without an explicit `Accept: application/json` header

> **FIXED in 26.1.5940.0.** Affected builds: **5873.1 through 5910.3**. On 5940.0 every `Accept` variant returns HTTP 200 — but **the mitigation below has not changed**, because what you get without `application/json` is now XML. See [What replaced it](#what-replaced-it-on-59400) at the end of this entry.

**Hard break on affected builds — every interactive endpoint.**

On 2026.1 builds up to 5910.3, any request to `/uiserver0/api/ui/interactive/...` whose `Accept` header does not include `application/json` fails with an **empty-body HTTP 500**. That includes `Accept: */*` — the **default for most HTTP libraries, including Python `httpx` and .NET `HttpClient`**. 2025.2 falls back to a default representation instead of failing.

The rule is *"`application/json` must be present"*, not *"`*/*` is rejected"* — a list containing both works. Verified on 26.1.5894.1, each variant tested from a clean slate, with the 5940.0 column added from the August 2026 re-run:

| `Accept` | 5873.1 – 5910.3 | 26.1.5940.0 |
|----------|--------|--------|
| `application/json` | 200 | 200, JSON |
| *(header omitted)* | **500, empty body** | 200, **XML** |
| `*/*` | **500, empty body** | 200, **XML** |
| `application/xml` | **500, empty body** | 200, **XML** |
| `text/html` | **500, empty body** | 200, **XML** |
| `application/json, */*` | 200 | 200, JSON |

```http
POST {uiserver}/api/ui/interactive/sessions/ HTTP/1.1
Authorization: Bearer {token}
Content-Type: application/json
Accept: application/json        <-- REQUIRED on 2026.1; omit it and you get an empty 500

{"ResponseWindowHandlingEnabled": true}
```

Note that `application/xml` also fails here, even though the `/api/v2` Transaction endpoints negotiate XML happily — this is specific to the interactive surface.

**Mitigation:** send `Accept: application/json` on **every** P21 request, ideally forced in one shared header builder rather than per call site. Every example in this repo already does this — the consequence of omitting it is what changed.

> **It will look like an authentication problem. It isn't — don't downgrade your auth.** The empty 500 lands on session-create, so the natural reading is *"our v2 tokens can no longer open sessions on 26.1"*. A production integration reached exactly that conclusion and shipped a fallback to the legacy `/api/security/token` endpoint before a controlled test — same token, one request with `Accept`, one without — isolated the header as the real cause. Their write-up records the correction: it "masqueraded as a 'v2 tokens can't open sessions' regression until a controlled same-token test isolated the header."
>
> **v2 tokens open sessions normally on 26.1**, confirmed independently here on 26.1.5910.3: a v2 token created a session, opened a window, and read its state with no trouble — the only requirement was the `Accept` header.
>
> This matters because the "fix" is a real security regression for no benefit. The v1 endpoint takes **credentials in HTTP headers**, where proxies and log pipelines capture them (see [Authentication § V1 Endpoint](00-Authentication.md#v1-endpoint-deprecated-security-risk)), and it also **forfeits per-operator attribution** — the legacy endpoint has no consumer key, so every write is attributed to the service account instead of the person who triggered it. Fix the header; keep v2.
>
> Diagnostic that settles it in two requests: send the **same** token twice to session-create, once with `Accept: application/json` and once without. A 200 and an empty 500 mean the header, not the token. If both fail, look at the token.
>
> **On 5940.0 that diagnostic changes shape** — both requests now return 200, and the one without the header returns XML. Compare `Content-Type`, not status.

#### What replaced it on 5940.0

The 500 is gone; the content negotiation is not. Without `application/json` in `Accept`, session-create returns **HTTP 200 with a DataContract XML body**:

```http
POST {uiserver}/api/ui/interactive/sessions/     # Accept: */*
HTTP/1.1 200 OK
Content-Type: application/xml; charset=utf-8

<Session xmlns="http://schemas.datacontract.org/2004/07/P21.UI.Service.Request">
  <Id>70e67fa6-0083-458d-9afa-cb3c3e7596f5</Id>
  <Properties>...</Properties>
</Session>
```

That is the 2025.2 behavior restored — a default representation instead of a failure. **It is still a break for any client that assumes JSON**, which is every client written against this API:

- Python `httpx` — `response.json()` raises `JSONDecodeError`.
- .NET `HttpClient` with `System.Text.Json` — `JsonDocument.Parse` raises `JsonException`.

Both confirmed on 26.1.5940.0. So the failure moved from *"an empty 500 I can see in the status code"* to *"a 200 that blows up one frame deeper, in the parser"* — arguably harder to attribute, since a 200 in the log looks like the call worked.

**The mitigation is unchanged and still required: send `Accept: application/json` on every P21 request.** If you fixed your headers for the 500, you are already correct on 5940.0 and need do nothing.

### 2. Ghost sessions: the failed create still half-creates the session (alternating 500/409)

> **No longer reachable as of 26.1.5940.0.** Affected builds: **5873.1 through 5910.3**. This entry is downstream of [entry 1](#1-interactive-api-returns-an-empty-http-500-without-an-explicit-accept-applicationjson-header) — it needs a *failed* session create to produce the ghost, and creates no longer fail that way. **The token-scoping rule at the bottom of this entry is not part of the defect and still applies on every build** — re-verified on 5940.0.

**Diagnosis trap that amplifies #1, on affected builds.**

When the session create fails with the empty 500 above, the session is still **partially created server-side** — it appears in UI Server Administration and blocks subsequent creates with **409 `{"ErrorMessage":"Session already exists."}`** A retrying integration therefore sees an **alternating 500 / 409 pattern** that looks like a session-pool or concurrency problem and is very hard to trace back to a missing header.

The ghost also **masks the original error**: once one call has poisoned the session, every subsequent create returns 409 regardless of its headers — so the very header experiment you would run to diagnose #1 reports the wrong answer unless you clear the ghost between attempts.

**Mitigation:** fix the `Accept` header (#1). If you see 500/409 alternation on 2026.1, check the headers before anything else.

**To clear a ghost, `DELETE` the session — don't wait it out.** `DELETE {uiserver}/api/ui/interactive/sessions` returns 200 and a clean create succeeds **immediately** afterward (verified on 26.1.5894.1). Waiting for `SessionCleanupExpiration` (~6 min) also works but is unnecessary; make the delete the first step of your retry path.

> **This only works while you still hold the token that created the session.** Verified on 26.1.5910.3 and re-verified on 26.1.5940.0 — **this half is current behavior, not a resolved defect.** The delete is scoped to the bearer token, so a ghost left by a *previous* token — a crashed process, a worker that re-authenticated, a retry path that fetched a fresh token before cleaning up — cannot be deleted at all. Query parameters and body forms carrying the session id are all refused with `400 {"ErrorMessage":"Invalid session"}`, and only `SessionCleanupExpiration` will reap it. Keep the token alive until the session is closed; do not re-authenticate as part of your recovery path before deleting. Full attempt matrix: [Interactive API § End Session](04-Interactive-API.md#6-end-session).

## P21 25.2

### `DatawindowName` is required in Interactive API change requests

25.2 changed window data structures so `DatawindowName` is **required** in v2 change payloads — the 3-parameter form (TabName + FieldName + Value) stops working. Confirmed through 25.2.5776.1 and acknowledged by Epicor as a development bug; affected windows include Item, PO Receiving Group, Delivery List, Group Pick Ticket, ConvertPOToVoucher, Order Entry, Clippership Auto Shipping, and Doc Links.

```json
{"TabName": "FORM", "DatawindowName": "form", "FieldName": "field", "Value": "value"}
```

Full detail, affected-window credits, and C# SDK impact: [Interactive API § v1 vs v2 differences](04-Interactive-API.md#v1-vs-v2-api-differences) and the [Known Issues](04-Interactive-API.md#known-issues-and-workarounds) section.

---

## Reporting new breaking changes

Found a behavior change during an upgrade? [Open an issue](https://github.com/mrwuss/p21-api-documentation/issues/new?template=bug-report.md) with the exact middleware versions (working and broken), a deterministic repro, and — for anything in the silent-false-success class — the read-back evidence. Entries are added here only after live verification on both sides of the version line.

## Related

- [Interactive API](04-Interactive-API.md) — the surface most version changes hit
- [Error Handling](06-Error-Handling.md) — symptom → cause tables
- [Session Pool Troubleshooting](07-Session-Pool-Troubleshooting.md) — the other source of "mystery" interactive failures
- [Changelog](10-Changelog.md) — documentation change history and standing alerts
