# P21 API Postman Collection

This directory contains a **Postman Collection** for the Prophet 21 APIs. It allows developers to test OData, Transaction, Interactive, and Entity endpoints immediately without writing Python code.

## Getting Started

1.  **Import:** Open Postman and click **Import** > **File** > Select `p21-api-documentation.postman_collection.json`.
2.  **Configure Variables:** Click the collection name, go to the **Variables** tab, and fill in:
    * `P21_BASE_URL` (e.g., `https://play.p21server.com`)
    * `P21_USERNAME`
    * `P21_PASSWORD`
    * All other variables (`TOKEN`, `UI_SERVER_URL`, `SESSION_ID`, `WINDOW_ID`) are auto-filled by test scripts.
3.  **Run:** Start with the **00. Authentication** folder to generate your token and UI Server URL.

## Important Notes

- **Run Auth first** - Most endpoints require the TOKEN and UI_SERVER_URL variables, which are set automatically when you run the Authentication requests.
- **Transaction and Interactive APIs** use the UI Server URL (auto-captured), not the base P21 URL.
- **Interactive API requests must run in order** - they share a stateful session. Always end your session when done.
- **Entity API** — `/api/entity/` covers 4 entities (customers, vendors, contacts, addresses; composite keys like `ACME_10`); other REST endpoint families exist — see [docs/05-Entity-API.md](../docs/05-Entity-API.md).

## How to Contribute

Because Postman Collections are large JSON files, they can be difficult to merge if not handled correctly. Please follow this workflow:

1.  **Import** the existing `p21-api-documentation.postman_collection.json` into your Postman.
2.  **Make Changes:** Add requests, fix bugs, or improve documentation.
3.  **Clean Up:** Before exporting, ensure you **remove any personal credentials** from the "Initial Value" column of your variables.
4.  **Export:** Right-click the collection > **Export** > **Collection v2.1 (recommended)**.
5.  **Overwrite:** Save the file over the existing `.json` file in this directory.
6.  **Submit:** Create a Pull Request with your updates.

> **Note:** Please try to avoid renaming folders or requests unnecessarily to keep the Git diff readable.
