# Project: P21 Transaction API Guide

> Documentation and testing tools for P21 Transaction API troubleshooting.

---

## Quick Context

This project provides documentation and diagnostic tools for troubleshooting P21 Transaction API issues, specifically session pool contamination that causes intermittent "Unexpected response window" errors.

---

## Key Files

| File | Purpose |
|------|---------|
| `docs/P21_Transaction_API_Troubleshooting_Guide.md` | Main documentation |
| `docs/P21_Transaction_API_Troubleshooting_Guide.html` | PDF-ready HTML version |
| `scripts/test_session_pool.py` | Session pool behavior test |
| `scripts/generate_pdf_doc.py` | MD to HTML converter |

---

## Usage

### Run Session Pool Test

```bash
python scripts/test_session_pool.py
```

Tests 5 patterns (40 total requests):
- Rapid fire (no delay)
- 500ms delay
- 2000ms delay
- Parallel (5 concurrent)
- Random jitter

### Generate PDF Documentation

```bash
python scripts/generate_pdf_doc.py
```

Opens HTML in browser, use Print > Save as PDF.

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `P21_BASE_URL` | Yes | P21 server URL |
| `P21_USERNAME` | Yes | P21 API username |
| `P21_PASSWORD` | Yes | P21 API password |

---

## Key Findings

### Session Pool Contamination

The Transaction API uses a pool of reusable sessions. If a previous operation triggers a modal dialog (like email) and fails, the session is returned to the pool with the dialog still open. Subsequent requests that get this "dirty" session fail with:

```
Unexpected response window: Email Purchase Order(s)
Window class: w_email_response
```

### Window-Specific Behavior

- **Purchase Order Entry** - Triggers email dialogs, prone to contamination
- **SalesPricePage** - No email triggers, sessions remain clean

### Recommended Solutions

1. Implement retry with random jitter
2. Use async endpoint (`/api/v2/transaction/async`)
3. Disable email notifications for API user
4. Report to Epicor as session pool hygiene bug

---

## Project Structure

```
p21-transaction-api-guide/
├── CLAUDE.md              # This file
├── README.md              # User-facing documentation
├── requirements.txt       # Python dependencies
├── .env.example           # Environment template
├── docs/
│   ├── P21_Transaction_API_Troubleshooting_Guide.md
│   └── P21_Transaction_API_Troubleshooting_Guide.html
└── scripts/
    ├── test_session_pool.py
    ├── generate_pdf_doc.py
    └── session_pool_results.json
```

---

*Last updated: 2025-12-25*
