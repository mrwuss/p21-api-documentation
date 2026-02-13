# P21 API Postman Collection

This directory contains a **Postman Collection** for the Prophet 21 APIs. It allows developers to test OData, Transaction, and Interactive endpoints immediately without writing Python code.

## 🚀 Getting Started

1.  **Import:** Open Postman and click **Import** > **File** > Select `P21_API.postman_collection.json`.
2.  **Environment:** Create a Postman Environment with the following variables:
    * `P21_BASE_URL` (e.g., `https://play.p21server.com`)
    * `P21_USERNAME`
    * `P21_PASSWORD`
    * `TOKEN` (Leave blank; auto-filled by scripts)
    * `UI_SERVER_URL` (Leave blank; auto-filled by scripts)
3.  **Run:** Start with the **00. Authentication** folder to generate your tokens.

## 🤝 How to Contribute

Because Postman Collections are large JSON files, they can be difficult to merge if not handled correctly. Please follow this workflow:

1.  **Import** the existing `P21_API.postman_collection.json` into your Postman.
2.  **Make Changes:** Add requests, fix bugs, or improve documentation.
3.  **Clean Up:** Before exporting, ensure you **remove any personal credentials** from the "Initial Value" column of your variables.
4.  **Export:** Right-click the collection > **Export** > **Collection v2.1 (recommended)**.
5.  **Overwrite:** Save the file over the existing `.json` file in this directory.
6.  **Submit:** Create a Pull Request with your updates.

> **Note:** Please try to avoid renaming folders or requests unnecessarily to keep the Git diff readable.