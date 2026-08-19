# P21 Breaking Changes by Version

> **Disclaimer:** This is unofficial, community-created documentation for Epicor Prophet 21 APIs. It is not affiliated with, endorsed by, or supported by Epicor Software Corporation. All product names, trademarks, and registered trademarks are property of their respective owners. Use at your own risk.

---

## Overview

A version-indexed registry of P21 middleware changes that **break or silently corrupt existing API integrations**. Every entry here was found the hard way during real upgrade validation and verified live. Most were also confirmed **not** to occur on the prior version; where no prior-version tenant was still available to A/B against, the entry **says so explicitly** rather than implying a comparison we didn't make. Check this page **before** any P21 upgrade, and re-test the listed surfaces on your own test tenant first.

| Version | Entries | Severity |
|---------|---------|----------|
| [2026.1](#p21-20261) | Empty 500 without `Accept: application/json` · ghost sessions (500/409) · `SessionId` → `Id` · `TabName` no longer accepted on `/v2/tab` · **silent-false-success on nonexistent-record loads** · **non-atomic batched changes** · **UDT update/delete can't target rows (delete silently no-ops)** · **`IgnoreDisabled` reports success on JobContractPricing `VALUES.values` writes that write nothing** | High — one hard break, four data-integrity hazards |
| [25.2](#p21-252) | `DatawindowName` required in change requests | High — hard break for 3-param change calls |

---

## P21 2026.1

Originally found on **2026.1.5873.1** during upgrade validation (June 2026), where none of it reproduced on 2025.2.5855.0 with identical requests. **Re-verified July 2026 against a production tenant on 26.1.5894.1**, a later build: entries 1–5 all still reproduce, with the refinements noted below. Entry 6 has been rewritten — the originally reported mechanism did not reproduce on 5894.1 (see that entry). The empty-500 defect has been reported to Epicor; the contract changes are awaiting written confirmation of intent.

> **Finding your build:** there is no version endpoint, but the session-create response carries it — `Properties[0].Properties.fullversion` (e.g. `26.1.5894.1`) and `shortversion` (`26.1`). See [Reading the middleware version](#reading-the-middleware-version) below.

### 1. Interactive API returns an empty HTTP 500 without an explicit `Accept: application/json` header

**Hard break — every interactive endpoint.**

On 2026.1, any request to `/uiserver0/api/ui/interactive/...` whose `Accept` header does not include `application/json` fails with an **empty-body HTTP 500**. That includes `Accept: */*` — the **default for most HTTP libraries, including Python `httpx` and .NET `HttpClient`**. 2025.2 falls back to a default representation instead of failing.

The rule is *"`application/json` must be present"*, not *"`*/*` is rejected"* — a list containing both works. Verified on 26.1.5894.1, each variant tested from a clean slate:

| `Accept` | Result |
|----------|--------|
| `application/json` | 200 |
| *(header omitted)* | **500, empty body** |
| `*/*` | **500, empty body** |
| `application/xml` | **500, empty body** |
| `text/html` | **500, empty body** |
| `application/json, */*` | 200 |

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

### 2. Ghost sessions: the failed create still half-creates the session (alternating 500/409)

**Diagnosis trap that amplifies #1.**

When the session create fails with the empty 500 above, the session is still **partially created server-side** — it appears in UI Server Administration and blocks subsequent creates with **409 `{"ErrorMessage":"Session already exists."}`** A retrying integration therefore sees an **alternating 500 / 409 pattern** that looks like a session-pool or concurrency problem and is very hard to trace back to a missing header.

The ghost also **masks the original error**: once one call has poisoned the session, every subsequent create returns 409 regardless of its headers — so the very header experiment you would run to diagnose #1 reports the wrong answer unless you clear the ghost between attempts.

**Mitigation:** fix the `Accept` header (#1). If you see 500/409 alternation on 2026.1, check the headers before anything else.

**To clear a ghost, `DELETE` the session — don't wait it out.** `DELETE {uiserver}/api/ui/interactive/sessions` returns 200 and a clean create succeeds **immediately** afterward (verified on 26.1.5894.1). Waiting for `SessionCleanupExpiration` (~6 min) also works but is unnecessary; make the delete the first step of your retry path.

> **This only works while you still hold the token that created the session.** Verified on 26.1.5910.3: the delete is scoped to the bearer token, so a ghost left by a *previous* token — a crashed process, a worker that re-authenticated, a retry path that fetched a fresh token before cleaning up — cannot be deleted at all. Query parameters and body forms carrying the session id are all refused with `400 {"ErrorMessage":"Invalid session"}`, and only `SessionCleanupExpiration` will reap it. Keep the token alive until the session is closed; do not re-authenticate as part of your recovery path before deleting. Full attempt matrix: [Interactive API § End Session](04-Interactive-API.md#6-end-session).

### 3. Session-create response field renamed: `SessionId` → `Id`

`POST /api/ui/interactive/sessions/` returns the session identifier under **`Id`** on 2026.1; 2025.2 returned **`SessionId`**.

**Mitigation:** read both (`data.get("Id") or data.get("SessionId")` / the C# equivalent) so one client works across versions.

### 4. `PUT /v2/tab` no longer accepts `TabName`

2026.1 binds **`PageName`** (PagePath structure) only; 2025.2 also tolerated `TabName` in the body. Requests still sending `TabName` stop working.

```json
PUT /api/ui/interactive/v2/tab
{"WindowId": "{windowId}", "PageName": "TP_ITEMS"}
```

**Mitigation:** none needed if you follow the documented v2 shape — this repo has always documented `PageName` ([Interactive API § Changing Tabs](04-Interactive-API.md#changing-tabs)). Audit any legacy client for `TabName` in tab-change bodies.

**`TabName` is ignored, not rejected — which matters for the error message you get.** Verified on 26.1.5910.3 against `SalesPricePage`, switching tabs and reading back which datawindow the window exposes:

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

**Mitigation (verified):** do not infer existence from the load status at all. Gate with an **existence pre-read** (OData or `POST /api/v2/transaction/get`) *before* opening/keying the window, and abort on no-match. Treat any non-Success load status as fatal, and inspect `Messages` when logging the reason.

### 6. Batched `/v2/change` is not atomic — a rejected field does not roll back its neighbours

**Data-integrity hazard.**

`PUT /v2/change` takes a `List` of field changes but returns **one top-level result for the whole batch** — there is no per-item status. When one item in the batch is rejected, the call returns an **HTTP 400 error envelope with no `Status` field at all**, while **the other fields in the same batch have already been applied**. Verified on 26.1.5894.1 (PurchaseOrder, no save issued):

```jsonc
// One /v2/change carrying two fields: a header field and a disabled line field
[{"TabName": "TABPAGE_1",  "DatawindowName": "tp_1_dw_1",     "FieldName": "external_po_no", "Value": "ZZ_HDR"},
 {"TabName": "TABPAGE_18", "DatawindowName": "extended_info", "FieldName": "extended_desc",  "Value": "ZZ_LINE"}]

// Response: HTTP 400
{"ErrorMessage": "Column is disabled: extended_desc", "ErrorType": null, ...}
// ...but a read-back shows external_po_no == "ZZ_HDR" — applied and still in the buffer.
```

A client that treats the 400 as "the change did not happen" is wrong: part of it did. If it then retries or falls through to a save, it commits a partially-applied edit it never intended.

**Mitigation (verified):** write **one field per `/change` call** and check the status of every call, so a failure is unambiguously attributable to one field. Then prove the result with a **read-back** — see [Verifying Writes](04-Interactive-API.md#verifying-writes-dont-trust-save-status-alone). A production run of 81 records using this pattern read back with zero silent drops.

> **Correction (July 2026).** This entry originally reported the mechanism as *"a batch containing a field on a **non-active tab** returns `Status: 1` while silently not applying that field."* That does **not** reproduce on 26.1.5894.1. Across eight configurations on the PurchaseOrder window — batched and single-field, `DatawindowName` supplied and omitted, target tab active and inactive — the non-active-tab field was **applied every time** with `Status: 1`. The original observation was made on 26.1.5873.1, which is no longer available to re-test, so we cannot distinguish "fixed in a later build" from "misattributed mechanism" — and the batch **is** genuinely non-atomic, which produces the same end result (a partially-applied batch) by a different route. The one-field-per-call mitigation was correct and is unchanged.
>
> **Re-tested again on 26.1.5910.3 (August 2026), still no reproduction.** PurchaseOrder, no save issued: with `TABPAGE_1` active, a write to `supplier_ship_date` on `TABPAGE_18` returned `Status: 1` and the value **was present** in the buffer after switching to that tab — matching the control that switched tabs first. The specific field named in the original 5873.1 report therefore applies normally on this build.
>
> **Write tab-by-tab anyway.** The client that filed the original report still groups its field writes by tab and switches before each group, and that remains the right shape regardless of which build you are on: it costs one `/v2/tab` call per tab, removes the question entirely, and matches how the window behaves for a human. Treat it as cheap insurance, not as a workaround for a bug we can currently demonstrate.

### 7. UDT Service update/delete cannot target rows in a UDT created on 2026.1

**Data-integrity hazard — silent false success on delete.**

> **Verification scope:** unlike entries 1–6, this one has **no prior-version comparison** — by the time it was found, no pre-2026.1 tenant remained available. What follows is verified on 2026.1; whether it is a *regression* or has always depended on how the table was created is **unproven**. Treated as a 2026.1 hazard because 2026.1's table-creation UI is what produces the incompatible shape.

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

**And it is not limited to `JobContractPricing`.** The same shape reproduces on `Order` (26.1, 2026-08-19). `LINE_NOTE.line_note` is published in the `Order` definition as an ordinary keyed `List`, but every one of its columns is disabled; without the flag the write is refused loudly:

```text
General Exception: Column is disabled: note
```

Add `IgnoreDisabled: true` — payload otherwise byte-identical — and it returns `Summary: {"Failed": 0, "Succeeded": 1}` with no messages, while a `/transaction/get` read-back shows the note still empty. That makes three unrelated services showing the same false success, which is what marks this as a platform behavior rather than a `JobContractPricing` quirk.

So `IgnoreDisabled` has two outcomes that are **indistinguishable in the response**: it genuinely unlocks the write (as it does for contract BINS quantities and JOBPRICECOST commission fields), or it swallows the refusal and writes nothing. You cannot tell which you got without reading the record back.

**Mitigation:** always read back after any write that used `IgnoreDisabled: true`, on any service — whether updating an existing line, inserting a new line, or creating a brand-new contract. Treat `Status: "Passed"` under `IgnoreDisabled` as **unverified** until a read-back confirms the value actually changed; per the control above, the Transaction API cannot currently be relied on to write `VALUES.values` at all, on any of the three paths. See [Transaction API § IgnoreDisabled](03-Transaction-API.md#ignoredisabled) and [Verifying Writes](04-Interactive-API.md#verifying-writes-dont-trust-save-status-alone) for the same read-back discipline applied elsewhere in this repo.

### Related 2026.1 observations (not breaking changes)

Found while re-verifying the above on 26.1.5894.1. None of these are regressions, but each will mislead you while debugging one.

#### Reading the middleware version

There is no version endpoint (`/api/version`, `/api/v2/version` and friends all 404). The **session-create response** carries the build:

```jsonc
POST {uiserver}/api/ui/interactive/sessions   // Accept: application/json
{
  "Id": "3c2aca0b-...",
  "Properties": [{"Name": "Telemetry", "Properties": {
      "fullversion": "26.1.5894.1", "shortversion": "26.1", "configurationid": "3694", ...
  }}]
}
```

This is the most reliable way to confirm which build you are actually talking to before trusting any entry on this page.

#### `GET /v2/data` returns only a *subset* of the window's datawindows

The response is a list of datawindow objects, and **which ones appear varies between calls** on the same window — immediately after a load it returned `tp_1_dw_1` + `tp_17_dw_17`; after a change touching the ship-to tab it returned `ship_to` + `tp_17_dw_17` and **omitted `tp_1_dw_1` entirely**. A datawindow's absence therefore proves nothing about the field's value.

Consequence for verification: `/v2/data` is not a reliable field-level read-back. Activate the field's tab first (which reliably brings its datawindow into the response), or verify out-of-band with OData / `POST /api/v2/transaction/get` — the approach [Verifying Writes](04-Interactive-API.md#verifying-writes-dont-trust-save-status-alone) already recommends.

#### A nonexistent `DatawindowName` fails loudly, not silently

Naming a datawindow that doesn't exist on the window returns **HTTP 400 `"Unable to find datawindow named dw_1"`** and applies nothing. This is worth knowing precisely *because* it is not a silent-failure mode: if you are hunting a field that "didn't take", a wrong datawindow name is not the culprit — you would have seen a 400.

Relatedly, on 26.1 `DatawindowName` is **optional for header-level fields** — `{"TabName": "SHIP_TO", "FieldName": "ship2_name", "Value": "..."}` with no `DatawindowName` resolves by tab + field and applies correctly. Supplying the correct name also works. Keep sending it: it is still **required** on 25.2 (see [below](#p21-252)), so including it is what makes one client work across both versions.

---

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
