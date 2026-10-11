# P21 API Postman Collection

This directory contains a **Postman Collection** for part of the Prophet 21 API surface, for trying requests without writing code.

**What it covers:** authentication (v2 token and UI-server router), OData table queries, the Transaction API (service list, `definition` / `defaults` / `basics`, `transaction/get`, and one order create), a short Interactive API session (open, change, save, close), the `/api/entity/` family, and the [other REST families](../docs/15-Other-REST-Families.md) listed under folder 05.

**What it does not cover:** the [Inventory REST API](../docs/11-Inventory-REST-API.md), the [UDT Service API](../docs/13-UDT-Service-API.md), the [`ui/full` surface](../docs/04-Interactive-API.md#the-uifull-surface-the-web-clients-own-rest-api), the [`/api/v2/commands` endpoint](../docs/03-Transaction-API.md#commands-endpoint), [`/api/v2/process/pdfreport`](../docs/03-Transaction-API.md#pdf-report-generation) reports, and the [Production and Labor](../docs/12-Production-Labor-API.md) services. Use the docs and `examples/` for those.

## Getting Started

1.  **Import:** Open Postman and click **Import** > **File** > Select `p21-api-documentation.postman_collection.json`.
2.  **Configure Variables:** Click the collection name, go to the **Variables** tab, and fill in:
    * `P21_BASE_URL` (e.g., `https://play.example.com`)
    * `P21_USERNAME`
    * `P21_PASSWORD`
    * All other variables (`TOKEN`, `UI_SERVER_URL`, `SESSION_ID`, `WINDOW_ID`) are auto-filled by test scripts.
3.  **Run:** Start with the **00. Authentication** folder to generate your token and UI Server URL.

## Important Notes

- **Run Auth first** - Most endpoints require the TOKEN and UI_SERVER_URL variables, which are set automatically when you run the Authentication requests.
- **Transaction and Interactive APIs** use the UI Server URL (auto-captured), not the base P21 URL.
- **Interactive API requests must run in order** - they share a stateful session. Always end your session when done.
- **Entity API** — `/api/entity/` covers 4 entities (customers, vendors, contacts, addresses; composite keys like `ACME_10`); other REST endpoint families exist — see [docs/05-Entity-API.md](../docs/05-Entity-API.md).
- **05. Other REST Families** covers UDF metadata, GL journal reads, a full CRM task create/read/update chain (the `TASK_NO` collection variable carries the created task's key between requests, set by the Create request's test script), and PO / inventory-adjustment header reads — see [docs/15-Other-REST-Families.md](../docs/15-Other-REST-Families.md).

## How to Contribute

Because Postman Collections are large JSON files, they can be difficult to merge if not handled correctly. Please follow this workflow:

1.  **Import** the existing `p21-api-documentation.postman_collection.json` into your Postman.
2.  **Make Changes:** Add requests, fix bugs, or improve documentation.
3.  **Clean Up:** Before exporting, ensure you **remove any personal credentials** from the "Initial Value" column of your variables.
4.  **Export:** Right-click the collection > **Export** > **Collection v2.1 (recommended)**.
5.  **Overwrite:** Save the file over the existing `.json` file in this directory.
6.  **Submit:** Create a Pull Request with your updates.

> **Note:** Please try to avoid renaming folders or requests unnecessarily to keep the Git diff readable.
