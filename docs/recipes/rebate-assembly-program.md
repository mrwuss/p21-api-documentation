# Rebate-Tracked Assembly Program

Set up a customer program where assembled parts are sold on a job contract and their components carry a supplier rebate — so that each invoice books cost at the **rebated** value and P21 writes the rebate receivable automatically, instead of the rebate being reconciled by hand.

**API:** Transaction + Interactive · **Services:** `JobContractPricing`, `Vendor`, `Item`, `Assembly`, `Order`, `Shipping` · **Deep dive:** [How Contract Costs Reach the Order and the Invoice](../03-Transaction-API.md#how-contract-costs-reach-the-order-and-the-invoice) · [Vendor Service](../03-Transaction-API.md#vendor-service-creating-a-vendor-and-its-supplier) · [Rebate prerequisites](../03-Transaction-API.md#rebate-prerequisites-other-cost-value-a-rebate-tracking-vendor)

This page is a **checklist**, not a script — a template you fill in per program. Adding a single new part to a running program: [new-assembled-part](new-assembled-part.md).

**Status legend:** **Verified** = proven end to end with a read-back by the credited contributor (play, and production for the contract and BOM work, 2026); **Inferred** = the business method or a step that follows from verified behavior but was not run as its own step.

## Why it exists

Assemblies priced off a job contract cost wrong when the parent's cost rolls up **non-rebated** component cost, and when BOMs carry hand-entered charge lines or duplicate components. The invoice shows a phantom loss and under-credits the rep's margin. The fix is to put the rebated cost on the contract and let P21 book the rebate — which only happens when every prerequisite below is in place.

## Parameters (fill these in)

| Parameter | Example | Notes |
|---|---|---|
| Customer and ship-tos | `CUST-100`, ship-tos `CUST-100-A`, `CUST-100-B` | Every ship-to that orders must be on the contract or it does not price |
| Contract | `job_no` `JOB-001`, `contract_no` `CONTRACT-001` | Approved, in date |
| Ship-from (source) location | `30` | Decides which primary supplier — and so which vendor — the rebate goes to |
| Rebate vendor | `100500` | Track Rebates on (step 3) |
| Rebate schedule | percent by component product code | From the supplier agreement — confirm with the supplier |
| Pricing rule | price = true cost ÷ (1 − target margin) | A business decision |

## Runbook

### Step 1 — Catalog what the customer actually buys (Inferred method)

Sweep the customer's order and invoice history (read-only) for every assembly they have ordered, and compare with the contract's `job_price_line` rows. Items ordered but not on the contract are the gap to add. Repeat this sweep periodically — new assemblies appear over time.

### Step 2 — Fix the BOMs (Transaction `Assembly`) (Verified)

Edits to existing assemblies work through keyed `Status: "New"` Transactions ([details](../03-Transaction-API.md#part-assembly-creation-workflow)):

- **Remove charge lines** (labor, burden and other charge items) if your costing replaces them: `delete_flag` = `ON` on the component row keyed `item_id_service_labor_id`.
- **Fix duplicated or wrong-quantity components** — a duplicate component double-counts real COGS.
- **Fix component units** that do not match the component's base unit.

These change the item for **every** customer, so confirm before running. Read back `assembly_line` (`delete_flag`, `quantity`, unit).

### Step 3 — Create the rebate vendor (Transaction `Vendor`) (Verified)

Create the vendor with `vendor` = `ON`, `track_rebates` = `ON`, terms by description, no currency, and its rebate receivable and allowance accounts on `REBATE_ACCOUNTS.d_vendor_rebate_accounts`. The save creates the same-ID supplier. [Payload and traps](../03-Transaction-API.md#vendor-service-creating-a-vendor-and-its-supplier).

Some programs book the receivable against a dedicated internal vendor (one per location) rather than the real supplier, and file the claim to the supplier separately; P21 does not care which, as long as Track Rebates is on.

### Step 4 — Make it the primary supplier at the ship-from location (Transaction + Interactive `Item`) (Verified)

Per assembly item, at the **ship-from** location — not the sales location:

1. Insert the vendor's supplier row on the location's supplier list: Transaction `Item`, `SUPPLIER_X_LOCATION` keyed on both `location_id` and `supplier_id`, `IgnoreDisabled: true` ([details](../03-Transaction-API.md#adding-a-location-supplier-row-the-prerequisite-insert)).
2. Flip it to primary. Items with a zero supplier cost or list price trip the *Item Issues Detected* rule, which the Transaction API cannot answer — use the [Interactive fallback](../04-Interactive-API.md#worked-example-item-issues-detected-rule-callback) and answer `cb_1`, or [fix the data](../03-Transaction-API.md#item-issues-detected-popup-root-cause-and-data-fix).

Read back `inv_loc.primary_supplier_id` at the ship-from location — the flag write can succeed and flip nothing.

### Step 5 — Price and cost the contract lines (Transaction `JobContractPricing`) (Verified)

One line per POST. For each assembly: `pricing_method` = `Price` **before** `price`; `commission_cost_type_cd` = `Value` with the true cost; **`other_cost_type_cd` = `Value` with the rebated component cost**. [Payload](../03-Transaction-API.md#commission-costs).

Attach every ship-to that orders to the contract ([details](../03-Transaction-API.md#attaching-a-ship-to-to-an-existing-contract)) — pricing follows the ship-to grid, not the contract header.

### Step 6 — Order entry and invoicing (Verified)

Enter orders with `unit_price` blank so the contract price and binding fill in at entry ([sales-order-to-invoice](sales-order-to-invoice.md)). A line is bound once, at entry: a bound line re-reads the contract's other cost at invoicing; a line entered before the item was on the contract never binds — delete and re-enter it.

## Verify — the acceptance test is a real invoice

On a test order shipped and invoiced:

- `invoice_line.unit_price` = the contract price; `commission_cost` = the contract value × its multiplier; `oe_line.job_price_hdr_uid` = the contract.
- `invoice_line.cogs_amount` = the contract's **other cost** value, not the moving average.
- A `vendor_rebate` row for the invoice: vendor = the rebate vendor, base cost = moving average, after-rebate cost = the contract value, due = the difference.
- GL for the invoice: the Sales Journal books COGS at the full moving average, then a Rebate Journal entry debits the rebate receivable (re-suffixed to the sales location) and credits COGS — net COGS = the contract value.
- No charge lines on the exploded order.

If COGS dropped but **no** `vendor_rebate` row appeared, the primary supplier at the ship-from location is not the Track Rebates vendor (step 4). The same mechanics apply to assemblies built on production orders, linked or build-to-stock.

## Maintenance

| Trigger | Action |
|---|---|
| Periodically | Re-run step 1 and add newly ordered assemblies |
| New assembly first ordered | [new-assembled-part](new-assembled-part.md), then steps 4–5 for it |
| Rebate percent or supplier list price changes | Recompute costs and prices; re-push step 5 |
| New ship-to | Attach it to the contract |
| Contract nearing its end date | Renew or extend — orders past the end date do not price |

> **Credit:** [Alex Westemeier](https://github.com/AWestemeier) — program built and proven on play and production, 2026, including the rebate trigger end to end on play (September 2026); not re-run here.
