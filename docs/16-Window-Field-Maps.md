# Window Field-to-Table Maps

> Which table and column does this field write? The Transaction API names fields, not columns, and the names often differ from the database. These maps answer it for seven windows.

[`definitions/window-maps/`](../definitions/window-maps/) holds, for **Order Entry, Item Maintenance, Shipping, Purchase Order Entry, Production Order Entry, Customer Maintenance and Assembly Maintenance**, every tab and datawindow the API could reach: the design-time `SELECT`, the table a save updates, and each field the window's [Transaction definition](../definitions/README.md) names, resolved to `table.column` or to a computed expression. Across the seven windows that is 228 datawindows and 2,927 fields. Read on play 26.1 in October 2026.

## Why the field name is not the column name

A field in a Transaction payload is the **datawindow column name**. It is not always the database column. Some that differ (each is `probed`, see [Basis](#basis) and [Limits](#limits-of-the-maps)):

| Window / datawindow | API field | Stored in |
|---|---|---|
| Order `TABPAGE_1.order` | `sales_loc_id` | `oe_hdr.location_id` |
| Order `TABPAGE_1.order` | `source_loc_id` | `oe_hdr.source_location_id` |
| Order `TP_ITEMS.items` | `oe_order_item_id` | `inv_mast.item_id` (the line stores `inv_mast_uid`) |
| PurchaseOrder `TABPAGE_1.tp_1_dw_1` | `vendor_supplier_id` | `po_hdr.supplier_id` |
| PurchaseOrder `TABPAGE_1.tp_1_dw_1` | `buyer_id` | `po_hdr.requested_by` |
| PurchaseOrder `TABPAGE_1.tp_1_dw_1` | `required_date` | `po_hdr.date_due` |
| Item `TABPAGE_1.tp_1_dw_1` | `sales_discount_group_id` | `inv_mast.default_sales_discount_group` |
| ProductionOrder | `source_loc_id` | `prod_order_hdr.source_location_id` |
| Assembly `TABPAGE_1.assemblyhdr` | `inv_mast_item_id` | `inv_mast.item_id` |

Checked live on play: an order entered with `sales_loc_id` = `40` reads `oe_hdr.location_id = 40`, and `po_hdr` has `requested_by` but no `buyer_id` column. The same names matter for OData filters: filter on the column, send the field.

## Look a field up

Each `<Service>.json` holds the window's `tabs`; each tab holds its `datawindows`; each datawindow holds `fields`. This reads the files offline — it makes no P21 call. Edit `MAPS` if you keep the folder elsewhere:

```python
"""Which table.column does a window field write? Reads definitions/window-maps offline."""
import json
import sys
from pathlib import Path

MAPS = Path("definitions/window-maps")  # EDIT: the folder you cloned or downloaded


def where_is(service: str, field: str) -> list[dict]:
    """Every datawindow of the window that names the field, with its resolved column."""
    window = json.loads((MAPS / f"{service}.json").read_text(encoding="utf-8"))
    found = []
    for tab in window["tabs"]:
        for dw in tab["datawindows"]:
            entry = dw["fields"].get(field)
            if entry:
                found.append({"element": dw["fullname"], "update_table": dw["update_table"], **entry})
    return found


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: where_is.py SERVICE FIELD   (e.g. Order sales_loc_id)")
    service, field = sys.argv[1:3]
    for hit in where_is(service, field) or [{"element": "(not named by the window)"}]:
        print(hit)
```

```text
$ python where_is.py Order sales_loc_id
{'element': 'TABPAGE_1.order', 'update_table': 'oe_hdr', 'column': 'oe_hdr.location_id', 'expression': None, 'basis': 'probed'}
```

A field the window does not name is a wrong name: the Transaction definition would refuse it too. The `<Service>.md` pages and [`index.md`](../definitions/window-maps/index.md) are the same data as tables, for reading.

## What each file holds

For each window, `<Service>.json`:

| Key | Holds |
|---|---|
| `service`, `title`, `window_class`, `menu_class` | the window |
| `definition` | every data element of the live Transaction definition and its field names, in order |
| `tabs[]` | each tab (`tab`, `text`, `select_status`) and its mapped `datawindows[]` |
| `unreachable[]` | tabs and datawindows SQL Information never reached, each with the reason |

For each mapped datawindow:

| Key | Holds |
|---|---|
| `name`, `fullname` | the datawindow and `TAB.datawindow`, the name a payload's data element uses |
| `select_sql` | the design-time `SELECT` |
| `update_table`, `update_table_note` | the table the tool says a save updates; the note marks a value the tool misparsed |
| `columns[]` | the column report: each displayed column's label and `table.column` or expression |
| `fields{}` | every field the definition names on this datawindow: `column` (`table.column`), `expression`, `basis` |

### Basis

`basis` says how a field was resolved. Of the 2,927 fields: 853 `probed`, 1,264 `column`, 312 `alias`, 287 `dw_name`, 211 `no_sql`.

| Basis | Meaning |
|---|---|
| `probed` | Per-field SQL Information named the column. The tool's own answer — the strongest evidence here, not a guarantee (see [Limits](#limits-of-the-maps)). |
| `alias` | The field is an alias in the `SELECT` (a name match). |
| `column` | The field is the name of exactly one column in the `SELECT` (a name match). |
| `dw_name` | A name P21 gives a field the datawindow computes (`cf_`, `c_`, `compute`). |
| `no_sql` | The datawindow has no `SELECT` (external source data). |
| `ambiguous`, `unresolved` | The name matches two columns, or none. None remain in the published files. |

## What the maps tell you about writes

1. **Many tabs are views of one result set.** In Order, 18 datawindows share a single `SELECT`; in Customer 11, Item 7, PurchaseOrder 6. A field written on any of them lands on the same row, so the data element your payload names decides which datawindow exposes the field, not which table it writes.
2. **Columns from a joined table are shown, not saved.** Header datawindows show names and descriptions from `address`, `users`, `shipping_route`, `currency_line` and similar. A save updates the datawindow's `update_table` only, so a joined column is display data: an edit to it is not stored in the joined table. That follows from the update table and was not write-tested field by field. Read `update_table` before you rely on a write, and read the record back after ([`Succeeded` does not prove a write landed](14-Breaking-Changes.md#8-ignoredisabled-true-reports-success-on-writes-that-write-nothing)).
3. **The tool's update table is unreliable for read-only grids.** It reports `system_setting` (the first `FROM` table) for order-history, PO and open-order grids, and a misparse (`clause*/`) where the `SELECT` carries `/*MAIN FROM CLAUSE*/` comments. Those rows carry `update_table_note`; treat them as read-only.
4. **Audit Trail tabs read generated per-tenant views** (`p21_view_audit_trail_<table>_<id>`, shown as `<id>`). Aging, Front Counter, Timestamp and a few filter datawindows are external source data with no `SELECT`.
5. **Most unreachable datawindows sit on record-dependent tabs** (lot, serial and bin, tags, service, labor, routing, job control, RFQ, consignment). They answer only once a record is loaded and a tab is enabled; `unreachable[]` gives each reason.

## Limits of the maps

These are what the SQL Information tool reported plus name matching, read from play. They were not write-tested field by field.

- **Check a mapping before you build a write on it.** Re-ask the tool for that one field (`FieldName` set, see [Read a Window's SQL](recipes/window-sql-information.md)), then save and read the record back.
- **Only `probed` is the tool's own answer.** `column`, `alias`, `dw_name` and `no_sql` are matches against the `SELECT` (2,074 of 2,927 fields), so read `select_sql` next to the column for any description or label field.
- **A window can blank a field the map still lists.** Assembly `price_return_to_stock_components` is blanked in the window, yet the map matches both the column report and the `SELECT`; the map describes the datawindow, not what the window shows for your record.
- **`expression` is not always SQL.** For a field the `SELECT` does not read, it can hold a bare identifier (Customer `label_definition_id`) or a short sentence naming what the tool reported (Assembly `revision_level`). Treat `column: null` as "no stored column found", not as a computed value.
- **`TIMESTAMP` datawindows are marked `off_tab`.** The API cannot select a tab whose name is shared by several tabs, but SQL Information reads an instantiated datawindow whichever tab is active, so their `SELECT`s are present. In all, 12 datawindows carry this marker; check `select_status` on every other tab (for Order, 51 of 84 tabs read `selected`).

## How the maps were made

Each datawindow was read with the client's **SQL Information** tool through the API: `m_sqlinformation` on the Interactive API, the `SELECT` from the web client's `ui/full` surface, the column report from its `showreport` grid, and a per-field call (`FieldName` set) for every field the name matching left uncertain. The full method, with complete Python and C# programs, is [Read a Window's SQL](recipes/window-sql-information.md). The fields of each window come from its live definition, `GET /api/v2/definition/{Service}`.

What the published copy leaves out, because it is a tenant's rather than standard P21: user-defined fields (`ufc_*`) and their joins, `*_ud` tables, custom-column tables, record captions and the records read, and generated object ids (replaced by `<id>`). The generator refuses to write a file in which any of these survive, and the published files were checked again for tenant names, record numbers and identifiers before they were committed. Your tenant has its own user-defined fields and custom columns; read them from your own definition and SQL Information, not from these files.

> **Credit:** *@mrwuss* — maps built and verified on play 26.1, October 2026.
