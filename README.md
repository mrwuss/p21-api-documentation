# P21 Transaction API Troubleshooting Guide

Documentation and diagnostic tools for troubleshooting P21 Transaction API intermittent failures.

## The Problem

When using the P21 Transaction API, requests may fail intermittently with:

```
Unexpected response window: Email Purchase Order(s)
Window class: w_email_response
```

The failures have no predictable pattern - the same request may pass, fail, pass, fail with no correlation to timing or payload.

## Root Cause

**Session Pool Contamination** - The Transaction API reuses sessions from a pool. If a previous operation triggered a modal dialog (like an email prompt) and failed, that session is returned to the pool with the dialog still open. When your request randomly gets that "dirty" session, it fails.

## Quick Start

### 1. Setup

```bash
# Clone repo
git clone <repo-url>
cd p21-transaction-api-guide

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your P21 credentials
```

### 2. Run Diagnostic Test

```bash
python scripts/test_session_pool.py
```

This runs 40 requests across 5 patterns to identify session pool issues.

### 3. View Documentation

Open `docs/P21_Transaction_API_Troubleshooting_Guide.html` in a browser, or read the markdown version directly.

## Solutions

1. **Retry with Jitter** - Implement retry logic with random delays
2. **Use Async Endpoint** - `/api/v2/transaction/async` may use dedicated sessions
3. **Disable Email Triggers** - Configure API user to suppress email dialogs
4. **Report to Epicor** - This is arguably a bug in session pool management

## Documentation

- [Full Troubleshooting Guide](docs/P21_Transaction_API_Troubleshooting_Guide.md)
- [PDF Version](docs/P21_Transaction_API_Troubleshooting_Guide.html) (open in browser, print to PDF)

## License

Internal use only - IFP IT
