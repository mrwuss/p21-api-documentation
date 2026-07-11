# P21 Breaking Changes by Version

> **Disclaimer:** This is unofficial, community-created documentation for Epicor Prophet 21 APIs. It is not affiliated with, endorsed by, or supported by Epicor Software Corporation. All product names, trademarks, and registered trademarks are property of their respective owners. Use at your own risk.

---

## Overview

A version-indexed registry of P21 middleware changes that **break or silently corrupt existing API integrations**. Every entry here was found the hard way during a real upgrade validation and verified against live tenants — including confirming the behavior does *not* exist on the prior version. Check this page **before** any P21 upgrade, and re-test the listed surfaces on your own test tenant first.

| Version | Entries | Severity |
|---------|---------|----------|
| [2026.1](#p21-20261) | Empty 500 without `Accept` header · ghost sessions (500/409) · `SessionId` → `Id` · `TabName` no longer accepted on `/v2/tab` · **two silent-false-success hazards** | High — one hard break, two data-integrity hazards |
| [25.2](#p21-252) | `DatawindowName` required in change requests | High — hard break for 3-param change calls |

---

## P21 2026.1

All findings verified on **2026.1.5873.1** (self-hosted middleware, test tenant) during upgrade validation, June 2026. **None reproduce on 2025.2.5855.0** with identical requests. The empty-500 defect has been reported to Epicor; the contract changes are awaiting written confirmation of intent. Re-verify against your own 2026.1 tenant before relying on the details.

### 1. Interactive API returns an empty HTTP 500 without an explicit `Accept: application/json` header

**Hard break — every interactive endpoint.**

On 2026.1, any request to `/uiserver0/api/ui/interactive/...` that omits the `Accept` header — or sends `Accept: */*`, which is the **default for most HTTP libraries, including Python `httpx` and .NET `HttpClient`** — fails with an **empty-body HTTP 500**. The identical request with `Accept: application/json` added succeeds. 2025.2 falls back to a default representation instead of failing.

```http
POST {uiserver}/api/ui/interactive/sessions/ HTTP/1.1
Authorization: Bearer {token}
Content-Type: application/json
Accept: application/json        <-- REQUIRED on 2026.1; omit it and you get an empty 500

{"ResponseWindowHandlingEnabled": true}
```

**Mitigation:** send `Accept: application/json` on **every** P21 request, ideally forced in one shared header builder rather than per call site. Every example in this repo already does this — the consequence of omitting it is what changed.

### 2. Ghost sessions: the failed create still half-creates the session (alternating 500/409)

**Diagnosis trap that amplifies #1.**

When the session create fails with the empty 500 above, the session is still **partially created server-side** — it appears in UI Server Administration and blocks subsequent creates with **409 "Session already exists"** until `SessionCleanupExpiration` (~6 minutes) passes. A retrying integration therefore sees an **alternating 500 / 409 pattern** that looks like a session-pool or concurrency problem and is very hard to trace back to a missing header.

**Mitigation:** fix the `Accept` header (#1). If you see 500/409 alternation on 2026.1, check the headers before anything else; waiting out `SessionCleanupExpiration` clears the ghost.

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

### 5. Silent false success: loading a nonexistent record returns `Status: 2` with an **empty window**

**Data-integrity hazard.**

On 2026.1, keying a window to a record that doesn't exist (e.g., setting `po_no` to a nonexistent PO) returns **`Status: 2`** and leaves the window **empty**. 2025.2 returned `Status: 0` for the same action. An integration that treats "not found" as `Status: 0` — or that doesn't gate on load status at all — will **silently proceed to write against an empty window**.

**Mitigation (verified):** do not infer existence from the load status at all. Gate with an **existence pre-read** (OData or `POST /api/v2/transaction/get`) *before* opening/keying the window, and abort on no-match. Treat any non-Success load status as fatal.

### 6. Silent false success: multi-field `/v2/change` drops fields on non-active tabs while returning `Status: 1`

**Data-integrity hazard.**

A single `PUT /v2/change` carrying multiple fields where at least one field belongs to a **tab that is not currently active** returns **`Status: 1` (Success)** while **silently not applying** that field. Observed live on 2026.1: a batched change partially applied, with one date field dropped, and nothing in the response indicated it.

**Mitigation (verified):** write **one field per `/change` call**, activating each tab (`PUT /v2/tab`) before changing its fields, and check the status of every call. Then prove the result with a **read-back** — see [Verifying Writes](04-Interactive-API.md#verifying-writes-dont-trust-save-status-alone). A production run of 81 records using this pattern read back with zero silent drops.

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
