# P21 window field-to-table maps

For seven P21 windows (Order Entry, Item Maintenance, Shipping, Purchase Order Entry, Production Order Entry, Customer Maintenance, Assembly Maintenance): every tab and datawindow the API could reach, with its design-time `SELECT`, its update table, and each Transaction-definition field resolved to `table.column` or a computed expression.

- `<Service>.json` — the data. `<Service>.md` — the same data as readable tables. [`index.md`](index.md) — the windows and counts.
- What the files hold, how to look a field up, what `basis` means, and how the maps were made: [docs/16-Window-Field-Maps.md](../../docs/16-Window-Field-Maps.md).

The files hold standard P21 schema only. User-defined fields (`ufc_*`), `_ud` tables, custom-column tables, record captions and generated object ids (shown as `<id>`) were removed; your tenant's own are in your own definition and SQL Information output.
