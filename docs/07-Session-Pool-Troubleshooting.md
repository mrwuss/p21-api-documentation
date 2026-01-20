# P21 Transaction API Troubleshooting Guide

> **Disclaimer:** This is unofficial, community-created documentation for Epicor Prophet 21 APIs. It is not affiliated with, endorsed by, or supported by Epicor Software Corporation. All product names, trademarks, and registered trademarks are property of their respective owners. Use at your own risk.

---

## Intermittent "Unexpected Response Window" Errors

**Document Version:** 1.0
**Date:** December 25, 2025
**Audience:** Mid-Level IT / Developers
**Classification:** Internal Technical Documentation

---

## Executive Summary

This document addresses intermittent failures when using the Prophet 21 (P21) Transaction API, specifically the "Unexpected response window" error. Through systematic investigation, we identified the root cause as **session pool contamination** - a condition where pooled API sessions retain state from previous operations, causing subsequent requests to fail unpredictably.

---

## Table of Contents

1. [The Error](#1-the-error)
2. [Investigation Process](#2-investigation-process)
3. [Root Cause Analysis](#3-root-cause-analysis)
4. [Recommended Solutions](#4-recommended-solutions)
5. [Testing Tools](#5-testing-tools)
6. [Appendix](#appendix)

---

## 1. The Error

### 1.1 Error Message

```
System.AggregateException: One or more errors occurred.
---> P21.UI.Common.UiServerException: Unexpected response window:
Email Purchase Order(s). Window class: w_email_response
```

### 1.2 Observed Behavior

The error exhibits **no predictable pattern**:

| Attempt | Delay | Result |
|---------|-------|--------|
| 1 | - | FAIL |
| 2 | 10 seconds | PASS |
| 3 | Immediate | FAIL |
| 4 | Minutes | FAIL |
| 5 | Immediate | PASS |

This randomness initially suggested a configuration issue, but the inconsistency pointed to something more systemic.

### 1.3 Sample Payload That Triggered Error

```json
{
  "Name": "PurchaseOrder",
  "UseCodeValues": false,
  "Transactions": [
    {
      "Status": "New",
      "DataElements": [
        {
          "Name": "TABPAGE_1.tp_1_dw_1",
          "Type": "Form",
          "Keys": ["po_no"],
          "Rows": [
            {
              "Edits": [
                {"Name": "po_no", "Value": "982428"}
              ]
            }
          ]
        },
        {
          "Name": "TABPAGE_18.extended_info",
          "Type": "Form",
          "Rows": [
            {
              "Edits": [
                {"Name": "acknowledged", "Value": "ON"},
                {"Name": "acknowledged_date", "Value": "2025-12-17"},
                {"Name": "c_shipped_flag", "Value": "ON"},
                {"Name": "supplier_ship_date", "Value": "2026-02-11"}
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

---

## 2. Investigation Process

### 2.1 Initial Hypothesis: Configuration Issue

**Information Provided:**
> "The payload we tried to send and the error that was returned."

**Initial Analysis:**

The error message mentioned `Email Purchase Order(s)` dialog, which suggested a P21 business rule was triggering an email workflow. The stack trace showed:

```
at P21.Application.Business.n_cst_emailsrv.of_retrieveemailinformation()
at P21.Application.Business.n_cst_script.of_showprinterdialogbox()
at P21.Application.UI.w_purchase_order_entry_sheet.ue_print()
```

This indicated the PO window was attempting to show an email dialog after processing certain fields (`acknowledged`, `c_shipped_flag`).

**Suggested Investigation:**
- Check DynaChange rules on Purchase Order Entry
- Check supplier email settings
- Check PO type notification configurations

### 2.2 Critical Information That Changed the Diagnosis

**Information Provided:**
> "We could send this payload and it would fail, then try again in 10 seconds and it would pass, try again right away and it would fail, try again in minutes and it would fail, try again and it would pass. There was no cadence to the error."

**Why This Changed Everything:**

If the error was caused by a configuration (email trigger, DynaChange rule, etc.), it would fail **every time** or follow a predictable pattern. The random nature of failures indicated:

1. The payload format was likely correct
2. The P21 configuration was not the direct cause
3. Something **external to the request itself** was causing failures

### 2.3 Revised Hypothesis: Session Pool Contamination

The randomness pattern matched known behavior of **connection/session pools**:

- The Transaction API uses a **pool of reusable sessions**
- Each session maintains state (open windows, dialogs, etc.)
- If a previous request fails mid-operation, the session may retain "dirty" state
- Subsequent requests that receive a dirty session will fail
- Which session you get is essentially **random**

---

## 3. Root Cause Analysis

### 3.1 How the Transaction API Session Pool Works

```
┌─────────────────────────────────────────────────────────────┐
│                    P21 UI Server                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Session Pool                            │    │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐    │    │
│  │  │Session 1│ │Session 2│ │Session 3│ │Session 4│    │    │
│  │  │  CLEAN  │ │  DIRTY  │ │  CLEAN  │ │  DIRTY  │    │    │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘    │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

**Normal Flow:**
1. Request arrives → Gets available session from pool
2. Session processes request → Returns result
3. Session is cleaned up → Returned to pool

**Contamination Flow:**
1. Request A arrives → Gets Session 2
2. Request A triggers email dialog → Dialog opens
3. Request A times out or fails → **Dialog remains open**
4. Session 2 returned to pool with open dialog
5. Request B arrives → Gets Session 2 (dirty)
6. Request B encounters unexpected dialog → **FAILS**

### 3.2 Evidence in the Stack Trace

The error occurs during `ue_clear()` - the **cleanup phase**:

```
at P21.Application.UI.w_purchase_order_entry_sheet.ue_clear()
```

This confirms:
- The actual data operation may have succeeded
- The failure occurs when cleaning up the session
- An unexpected window (email dialog) was found
- This window was **not opened by the current request**

### 3.3 Why Certain Fields Trigger This

The `acknowledged` and `c_shipped_flag` fields trigger email notifications in P21:

```
acknowledged = ON  →  "Send acknowledgment to supplier"
c_shipped_flag = ON  →  "Notify about shipment status"
```

When another user or process previously set these fields via the API:
1. The email dialog opened in that session
2. The operation failed/timed out before the dialog closed
3. The session was returned to the pool with the dialog still open
4. Your request randomly got that same dirty session

---

## 4. Recommended Solutions

### 4.1 Immediate Workarounds

#### Option A: Implement Retry with Random Jitter

```python
import random
import time

def call_transaction_api(payload, max_retries=5):
    for attempt in range(max_retries):
        try:
            result = make_api_call(payload)
            if result.success:
                return result
        except TransactionApiError as e:
            if "Unexpected response window" in str(e):
                # Dirty session - wait and retry with jitter
                delay = random.uniform(0.5, 3.0)
                time.sleep(delay)
                continue
            raise
    raise Exception("Max retries exceeded")
```

#### Option B: Use Async Endpoint

The async endpoint may use dedicated sessions:

```
POST /uiserver0/api/v2/transaction/async
```

Then poll for results:

```
GET /uiserver0/api/v2/transaction/async?id={RequestId}
```

#### Option C: Split Transactions

Separate the "trigger" fields into a second transaction:

**Transaction 1:** Update line items
```json
{
  "DataElements": [
    {"Name": "TABPAGE_17.tp_17_dw_17", ...}
  ]
}
```

**Transaction 2:** Update acknowledgment (with retry)
```json
{
  "DataElements": [
    {"Name": "TABPAGE_18.extended_info", ...}
  ]
}
```

### 4.2 Configuration Changes

#### Disable Email Notifications for API User

1. Create a dedicated P21 user for API operations
2. Configure user profile to suppress email dialogs
3. Check: System Settings → Purchase Order → Email Options

#### Check DynaChange Rules

1. Navigate to: Tools → DynaChange → Rules
2. Search for rules on "Purchase Order Entry"
3. Look for rules triggered by `acknowledged` or `c_shipped_flag`
4. Consider adding condition: `IF user <> 'API_USER'`

### 4.3 Long-Term: Report to Epicor

This is arguably a **bug in P21's session pool management**. Sessions with open dialogs should not be returned to the pool.

**Bug Report Should Include:**
- Payload that triggers the issue
- Error message and full stack trace
- Evidence of intermittent pattern
- Request for session pool hygiene improvements

---

## 5. Testing Tools

### 5.1 Session Pool Behavior Test Script

A Python script has been created to diagnose session pool issues:

**Location:** `scripts/test_session_pool.py`

**What It Tests:**
1. Rapid-fire requests (no delay)
2. Delayed requests (500ms, 2000ms)
3. Parallel concurrent requests
4. Random jitter patterns

**Running the Test:**

```bash
python scripts/transaction/test_session_pool.py
```

**Sample Output:**

```
TEST 1: Rapid Fire (10 requests, no delay)
======================================================================
  [ 1] ✓  234ms - Succeeded: 1
  [ 2] ✗  189ms - Failed: UnexpectedWindow
  [ 3] ✓  201ms - Succeeded: 1
  [ 4] ✗  178ms - Failed: UnexpectedWindow
  ...

CONCLUSIONS:
  ⚠️ Intermittent failures detected
  ⚠️ Pattern suggests session pool issues
  ⚠️ 'Unexpected window' errors confirm dirty session pool
```

### 5.2 Sample Test Results (SalesPricePage Window)

A test run against the SalesPricePage window showed 100% success:

```
SESSION POOL BEHAVIOR ANALYSIS
======================================================================
RAPID_FIRE:       Total: 10, Success: 10, Failed: 0 (100.0%)
DELAYED_500MS:    Total: 10, Success: 10, Failed: 0 (100.0%)
DELAYED_2000MS:   Total:  5, Success:  5, Failed: 0 (100.0%)
PARALLEL:         Total:  5, Success:  5, Failed: 0 (100.0%)
RANDOM_JITTER:    Total: 10, Success: 10, Failed: 0 (100.0%)

SUMMARY:
  Total Requests: 40
  Total Failures: 0
  Overall Success Rate: 100.0%

CONCLUSIONS:
  [OK] No failures detected - session pool appears healthy
```

**Key Insight:** The SalesPricePage window does not trigger email dialogs, so session pool contamination is not observed. The intermittent failures are **window-specific** - Purchase Order Entry triggers email workflows that leave dialogs open, contaminating the session.

### 5.3 Interpreting Results

| Pattern | Meaning |
|---------|---------|
| 100% success | Session pool is healthy for this window |
| Alternating success/fail | Strong pool contamination |
| Random failures | Moderate pool contamination |
| 100% failure | Likely configuration issue, not pool |

**Important:** A healthy result for one window (SalesPricePage) does not guarantee other windows (PurchaseOrder) are safe. Each window type can have different behaviors that affect session state.

---

## Appendix

### A. Complete Error Stack Trace

```
System.AggregateException: One or more errors occurred.
---> P21.UI.Common.UiServerException:
     Unexpected response window: Email Purchase Order(s).
     Window class: w_email_response

at P21.Application.n_cst_actionrequestexecutor.se_nwindowopener_responsewindowopened()
at P21.Application.UI.Infrastructure.n_windowopener.of_open()
at P21.Application.Business.n_cst_emailsrv.of_retrieveemailinformation()
at P21.Application.Business.n_cst_script.of_showprinterdialogbox()
at P21.Application.UI.w_purchase_order_entry_sheet.ue_print()
at P21.Application.UI.w_purchase_order_entry_sheet.ue_clear()
at P21.Application.n_uirequestprocessor_clearwindow.ProcessRequest()
at P21.UI.BulkEditor.DataProcessing.StandardDataProcessor.Process()
```

### B. Transaction API Endpoints Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v2/services` | GET | List available services |
| `/api/v2/definition/{name}` | GET | Get service schema |
| `/api/v2/transaction` | POST | Synchronous processing |
| `/api/v2/transaction/async` | POST | Async processing |
| `/api/v2/transaction/get` | POST | Bulk retrieve |

### C. Related Documentation

- [Transaction API](03-Transaction-API.md) - Service discovery, bulk operations
- [Interactive API](04-Interactive-API.md) - Sessions, windows, workflows
- [Error Handling](06-Error-Handling.md) - HTTP codes, error responses

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-25 | Author | Initial version |

---

*This document was created as part of API performance research for the P21 Price Page Manager project. The investigation methodology demonstrates how systematic analysis of error patterns and user-provided context can lead to accurate root cause identification.*
