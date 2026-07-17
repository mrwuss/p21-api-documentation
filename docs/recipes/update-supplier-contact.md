# Update Supplier Contact Info (Email / Central Phone)

Write a supplier's email address and central phone number into P21 — the fields purchasing documents and views read from the supplier's **address** record.

**API:** Transaction (`POST /api/v2/transaction`) · **Service:** `Address` · **Deep dive:** [Transaction API](../03-Transaction-API.md) · **Full schema:** [Address.json](../../definitions/Address.json)

## Where supplier contact info actually lives

`supplier.supplier_id` shares its id with an `address` row (`address.id = supplier_id`). The email and central phone shown for a supplier come from **`address.email_address`** and **`address.central_phone_number`** — not from the `supplier` table (its only email-ish columns are `email_po_flag` / `supplier_redemption_email`). Verified against a live 2026 system: the supplier's address row carried exactly the values surfaced by purchasing views.

The `Address` service (window: Address maintenance) is the smallest write surface for these fields — its definition is ~9 KB vs ~70 KB for `Supplier`, and it needs only the address `id` as key.

## Payload

`Status: "New"` is the **upsert** shape — an existing `id` updates that record (see [Status "Existing" is not valid](../03-Transaction-API.md#updating-an-existing-contract)). `IgnoreIfEmpty: true` on the contact edits means an empty value **leaves the stored field untouched** — this payload can add or replace contact info but can never blank it.

```json
POST {ui_server}/api/v2/transaction

{
  "Name": "Address",
  "UseCodeValues": false,
  "IgnoreDisabled": true,
  "Transactions": [{
    "Status": "New",
    "DataElements": [
      {
        "Name": "TABPAGE_1.tp_1_dw_1",
        "Type": "Form",
        "Keys": ["id"],
        "Rows": [{ "Edits": [
          { "Name": "id", "Value": "20488", "IgnoreIfEmpty": false }
        ] }]
      },
      {
        "Name": "TABPAGE_3.tp_3_dw_3",
        "Type": "Form",
        "Keys": [],
        "Rows": [{ "Edits": [
          { "Name": "email_address",                "Value": "orders@example.com", "IgnoreIfEmpty": true },
          { "Name": "address_central_phone_number", "Value": "319-555-0100",       "IgnoreIfEmpty": true }
        ] }]
      }
    ]
  }]
}
```

Field names on the Phone tab (`TABPAGE_3.tp_3_dw_3`): `address_central_phone_number`, `address_central_fax_number`, `email_address`.

## Verify (read-after-write)

Don't trust `Summary.Succeeded` alone — read the record back ([why](../04-Interactive-API.md#verifying-writes-dont-trust-save-status-alone)):

```json
POST {ui_server}/api/v2/transaction/get

{
  "ServiceName": "Address",
  "TransactionStates": [
    { "DataElementName": "TABPAGE_1.tp_1_dw_1", "Keys": [{ "Name": "id", "Value": "20488" }] },
    { "DataElementName": "TABPAGE_3.tp_3_dw_3", "Keys": [{ "Name": "id", "Value": "20488" }] }
  ]
}
```

The response's `TABPAGE_3.tp_3_dw_3` row echoes `email_address` / `address_central_phone_number` as stored.

## Gotchas (verified live on Play, 2026-07)

- **The wrong `/transaction/get` shape returns a BLANK template with HTTP 200** — a body using top-level `Keys` (no `TransactionStates`) "succeeds" but every `Value` comes back empty, which reads exactly like a missing record. Use the `TransactionStates`/`DataElementName` shape above.
- **Write + read-back round trip confirmed**: values persisted and were read back verbatim; a subsequent write restored the originals the same way.
- **Empty values are no-ops**, not clears, because of `IgnoreIfEmpty: true` — deliberate here; flip to `false` only if you truly mean to blank a field.

## Python

```python
import httpx

def update_supplier_contact(ui_server: str, token: str, supplier_id: int,
                            email: str = "", phone: str = "") -> None:
    """Upsert supplier contact fields on the shared address record."""
    payload = {
        "Name": "Address", "UseCodeValues": False, "IgnoreDisabled": True,
        "Transactions": [{
            "Status": "New",
            "DataElements": [
                {"Name": "TABPAGE_1.tp_1_dw_1", "Type": "Form", "Keys": ["id"],
                 "Rows": [{"Edits": [
                     {"Name": "id", "Value": str(supplier_id), "IgnoreIfEmpty": False}]}]},
                {"Name": "TABPAGE_3.tp_3_dw_3", "Type": "Form", "Keys": [],
                 "Rows": [{"Edits": [
                     {"Name": "email_address", "Value": email, "IgnoreIfEmpty": True},
                     {"Name": "address_central_phone_number", "Value": phone,
                      "IgnoreIfEmpty": True}]}]},
            ],
        }],
    }
    resp = httpx.post(
        f"{ui_server}/api/v2/transaction", json=payload,
        headers={"Authorization": f"Bearer {token}",
                 "Accept": "application/json", "Content-Type": "application/json"},
        timeout=60,
    )
    resp.raise_for_status()
    summary = resp.json().get("Summary") or {}
    if summary.get("Failed"):
        raise RuntimeError(f"Address write failed: {resp.text[:300]}")
```
