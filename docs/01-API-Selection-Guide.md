# P21 API Selection Guide

> **Disclaimer:** This is unofficial, community-created documentation for Epicor Prophet 21 APIs. It is not affiliated with, endorsed by, or supported by Epicor Software Corporation. All product names, trademarks, and registered trademarks are property of their respective owners. Use at your own risk.

---

## Overview

Prophet 21 provides four different APIs for external data access and manipulation. This guide helps you choose the right API for your use case.

## Quick Decision Table

| Need | Best API | Why |
|------|----------|-----|
| Read data quickly | **OData** | Standard protocol, efficient queries |
| Bulk create records | **Transaction API** | Stateless, supports batching |
| Complex business workflows | **Interactive API** | Full business logic, validation |
| Simple CRUD operations | ~~Entity API~~ | **Not working** - use Interactive API |
| Update existing records | **Interactive API** | Reliable field-level updates |
| Handle response dialogs | **Interactive API** | Only API with dialog handling |

---

## API Comparison

| Feature | OData | Transaction | Interactive | Entity* |
|---------|-------|-------------|-------------|---------|
| **Read Data** | Excellent | Limited | Good | N/A |
| **Create Data** | No | Excellent | Good | N/A |
| **Update Data** | No | Limited** | Excellent | N/A |
| **Delete Data** | No | No | Via UI | N/A |
| **Bulk Operations** | Yes (read) | Yes | No | N/A |
| **Business Logic** | No | Partial | Full | N/A |
| **Session Required** | No | No | Yes | N/A |
| **Stateful** | No | No | Yes | N/A |
| **Response Dialogs** | N/A | N/A | Yes | N/A |

*Entity API is currently non-functional (Dec 2025) - see [Entity API](05-Entity-API.md)
**Transaction API updates have known issues - see [Session Pool Troubleshooting](07-Session-Pool-Troubleshooting.md)

---

## OData API

### Best For
- Reporting and data exports
- Quick lookups and searches
- Dashboard data
- Data validation
- Any read-only operation

### Characteristics
- **Standard OData v4 protocol** - familiar to most developers
- **Read-only** - cannot create, update, or delete
- **No session management** - simple request/response
- **Efficient** - supports filtering, pagination, field selection
- **Direct table/view access** - query any P21 table or view

### Use When
- You only need to read data
- Performance is critical
- You need standard query capabilities ($filter, $select, $orderby)
- You want to minimize complexity

### Don't Use When
- You need to create or modify data
- You need business logic validation

### Example Use Cases
- Get supplier list for dropdown
- Search for products
- Export pricing data
- Validate customer exists
- Dashboard metrics

---

## Transaction API

### Best For
- Bulk record creation
- External system integration
- Automated data import
- High-volume operations

### Characteristics
- **Stateless** - each request is independent
- **Bulk operations** - multiple records per request
- **Metadata-driven** - follows P21 window schemas
- **Fast** - 50-100x faster than Interactive API for creates
- **Limited updates** - update operations have known issues

### Use When
- Creating many records at once
- Building integrations from external systems
- Performance is critical for creation
- You don't need complex validation feedback

### Don't Use When
- Updating existing records (use Interactive API)
- You need to handle response dialogs
- You need field-by-field validation feedback

### Known Issues
- **Session Pool Contamination** - intermittent failures with some windows
- **Update operations** - may fail with NullReferenceException
- See [Session Pool Troubleshooting](07-Session-Pool-Troubleshooting.md)

### Example Use Cases
- Import price pages from spreadsheet
- Sync products from external catalog
- Bulk create purchase orders
- Automated data migration

---

## Interactive API

### Best For
- Complex business workflows
- Record updates
- Operations requiring validation
- Handling response dialogs

### Characteristics
- **Stateful** - maintains session between requests
- **Full business logic** - all P21 validation and rules
- **Window-based** - interacts with P21 windows
- **Response dialogs** - can handle pop-up confirmations
- **Reliable updates** - field-level control

### Use When
- Updating existing records
- You need full P21 business validation
- Operations may trigger dialogs (email, confirmations)
- Complex multi-step workflows
- You need to mimic user interaction

### Don't Use When
- Simple reads (use OData - faster)
- Bulk creates (use Transaction API - faster)
- You don't need business logic

### Performance Note
The Interactive API is slower than Transaction API for creates (~5s vs 0.05s per record) but more reliable for updates.

### Version Note
Some P21 servers only support v2 Interactive API endpoints. If you receive 404 errors on `/api/ui/interactive/v1/*` endpoints, use `/api/ui/interactive/v2/*` instead. The v2 endpoints have different payload formats - see [Interactive API v1 vs v2](04-Interactive-API.md#v1-vs-v2-api-differences).

### Example Use Cases
- Update purchase order status
- Modify customer records
- Complex order entry
- Any operation with approval dialogs

---

## Entity API

> **Warning: Currently Non-Functional**
>
> As of December 2025, the Entity API is not working. Use **Interactive API** for CRUD operations instead. This section is preserved for reference in case Epicor fixes the API in a future release.

### Best For
- Simple CRUD on business objects
- Quick single-record operations
- When you know the entity structure

### Characteristics
- **Entity-based** - works with P21 business objects
- **Simple CRUD** - create, read, update, delete
- **Less overhead** - simpler than Interactive API
- **Object-oriented** - works with entity instances

### Use When
- ~~Simple single-record operations~~ **Not currently working**
- ~~You prefer object-based access~~ **Use Interactive API instead**
- ~~Transaction or Interactive API is overkill~~

### Don't Use When
- **Always** - API is currently non-functional

### Example Use Cases
- ~~Look up single customer~~ → Use OData or Interactive API
- ~~Update a specific field~~ → Use Interactive API
- ~~Simple record creation~~ → Use Transaction or Interactive API

---

## Decision Flowchart

```
Start
  │
  ├─ Need to READ data only?
  │   │
  │   └─ Yes → Use OData API
  │
  ├─ Need to CREATE multiple records?
  │   │
  │   └─ Yes → Use Transaction API
  │
  ├─ Need to UPDATE records?
  │   │
  │   └─ Yes → Use Interactive API
  │
  ├─ Need response dialog handling?
  │   │
  │   └─ Yes → Use Interactive API
  │
  └─ Single-record CREATE?
      │
      ├─ High volume → Use Transaction API
      │
      └─ Low volume / needs validation → Use Interactive API
```

---

## Hybrid Approaches

### Read with OData, Write with Transaction/Interactive

The most common pattern:
1. Use **OData** for all reads (fast, simple)
2. Use **Transaction API** for bulk creates (fast)
3. Use **Interactive API** for updates (reliable)

### Example: Price Page Management

```python
# Read existing pages - OData (fast)
pages = odata.get_price_pages(supplier_id=21274)

# Create new pages - Transaction API (bulk, fast)
new_pages = transaction.create_pages([...])

# Update existing page - Interactive API (reliable)
with interactive.open_window("SalesPricePage") as window:
    window.change_data("calculation_value1", "0.55")
    window.save()
```

---

## Performance Benchmarks

Measured against production P21 instance:

| Operation | OData | Transaction | Interactive |
|-----------|-------|-------------|-------------|
| Read 160 records | 0.12s | N/A | ~2s |
| Create 1 record | N/A | 0.05s | 2.5s |
| Create 25 records | N/A | 1.4s | 62s |
| Update 1 record | N/A | Unreliable* | 2.0s |

*Transaction API updates may fail - see known issues

---

## Related

- [Authentication](00-Authentication.md)
- [OData API](02-OData-API.md)
- [Transaction API](03-Transaction-API.md)
- [Interactive API](04-Interactive-API.md)
- [Entity API](05-Entity-API.md)
- [Session Pool Troubleshooting](07-Session-Pool-Troubleshooting.md)
