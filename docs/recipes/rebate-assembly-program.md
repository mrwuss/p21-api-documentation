# Rebate-Tracked Assembly Program

Set up a customer program where assembled parts are sold on a job contract and their components carry a supplier rebate — so that each invoice books cost at the **rebated** value and P21 writes the rebate receivable automatically, instead of the rebate being reconciled by hand.

**API:** Transaction + Interactive · **Services:** `JobContractPricing`, `Vendor`, `Item`, `Assembly`, `Order`, `Shipping` · **Deep dive:** [How Contract Costs Reach the Order and the Invoice](../03-Transaction-API.md#how-contract-costs-reach-the-order-and-the-invoice) · [Vendor Service](../03-Transaction-API.md#vendor-service-creating-a-vendor-and-its-supplier) · [Rebate prerequisites](../03-Transaction-API.md#rebate-prerequisites-other-cost-below-actual-a-rebate-tracking-vendor)

This page is a template you fill in per program. The API-reachable steps, for one assembled part, are one runnable program in Python and C# that runs each step and reads it back before the next: [`examples/python/recipes/rebate_assembly_program.py`](../../examples/python/recipes/rebate_assembly_program.py) · [`examples/csharp/Recipes/RebateAssemblyProgram.cs`](../../examples/csharp/Recipes/RebateAssemblyProgram.cs) (menu item 37). Both are dry runs until you pass `--execute` or type `EXECUTE`. Adding a single new part to a running program: [new-assembled-part](new-assembled-part.md).

**Status legend:** **Run on play 26.1.5950.0, 2026-10-10** = the step ran in both the Python and the C# runbook against a play tenant on that build and date, with a read-back. **Manual** = a business decision or a check a person makes; the runbooks do not do it. **Verified** = proven end to end with a read-back by the credited contributor (play, and production for the contract and BOM work, 2026); **Inferred** = the business method or a step that follows from verified behavior but was not run as its own step.

## Why it exists

Assemblies priced off a job contract cost wrong when the parent's cost rolls up **non-rebated** component cost, and when BOMs carry hand-entered charge lines or duplicate components. The invoice shows a phantom loss and under-credits the rep's margin. The fix is to put the rebated cost on the contract and let P21 book the rebate — which only happens when every prerequisite below is in place.

## Parameters (fill these in)

| Parameter | Example | Notes |
|---|---|---|
| Customer and ship-tos | `CUST-100`, ship-tos `CUST-100-A`, `CUST-100-B` | Every ship-to that orders must be on the contract or it does not price |
| Contract | `job_no` `JOB-001`, `contract_no` `CONTRACT-001` | Approved, in date |
| Source location | `30` | The line's `source_loc_id`. Its primary supplier usually becomes `oe_line.supplier_id`, and so the rebate vendor. On a transfer line it differs from the ship location (the runbooks' `--ship-from` is used as the order's sales location and the line's source location; a stock line then ships from it too, so the runbooks never exercise a source location that differs from the sales location) |
| Rebate vendor | created in step 3 | Track Rebates on |
| Rebate schedule | percent by component product code | From the supplier agreement — confirm with the supplier (manual) |
| Pricing rule | price = true cost ÷ (1 − target margin) | A business decision (manual) |

## Run it

```bash
python examples/python/recipes/rebate_assembly_program.py            # dry run: payloads
python examples/python/recipes/rebate_assembly_program.py --company ACME --customer CUST-100 \
    --ship-to CUST-100 --contact 300 --taker JSMITH --job-no JOB-001 --contract-no CONTRACT-001 \
    --ship-from 30 --item ASSY-001 --component-qty COMP-001=2 --vendor-name "Example Rebate Vendor" \
    --ap-account 2222200 --rebate-account 1111100 --rebate-allowance-account 3333300 \
    --price 45.00 --true-cost 30.60 --rebated-cost 24.00 --execute
```

Step 6 sells one unit, so the assembled part must be **in stock at the source location** first (built on a production order, or received).

## Runbook

| # | Step | Surface | Status |
|---|---|---|---|
| 1 | Catalog what the customer buys | OData (read-only) | Run on play 26.1.5950.0, 2026-10-10 |
| 2 | Fix the BOMs | Transaction `Assembly` | Run on play 26.1.5950.0, 2026-10-10 (quantity fix) |
| 3 | Create the rebate vendor | Transaction `Vendor` | Run on play 26.1.5950.0, 2026-10-10 |
| 4 | Primary supplier at the source location | Transaction `Item` | Run on play 26.1.5950.0, 2026-10-10 |
| 5 | Price and cost the contract lines | Transaction `JobContractPricing` | Run on play 26.1.5950.0, 2026-10-10 |
| 6 | Order entry and invoicing | Transaction `Order` + Interactive `Shipping` | Run on play 26.1.5950.0, 2026-10-10 |
| — | GL check, supplier claim, rebate schedule | — | Manual |

### Step 1 — Catalog what the customer actually buys (Inferred method; run on play 26.1.5950.0, 2026-10-10)

Sweep the customer's order and invoice history (read-only) for every assembly they have ordered, and compare with the contract's `job_price_line` rows. Items ordered but not on the contract are the gap to add. Repeat this sweep periodically — new assemblies appear over time. The runbooks read up to 200 of the customer's orders since `--since`, collect the ordered `inv_mast_uid`s, and list those that have an `assembly_hdr` and no line on the contract.

### Step 2 — Fix the BOMs (Transaction `Assembly`) (Verified; run on play 26.1.5950.0, 2026-10-10)

Edits to existing assemblies work through keyed `Status: "New"` Transactions ([details](../03-Transaction-API.md#part-assembly-creation-workflow)):

- **Remove charge lines** (labor, burden and other charge items) if your costing replaces them: `delete_flag` = `ON` on the component row keyed `item_id_service_labor_id`. (`--remove-component` in the runbooks; the verification runs exercised the quantity fix only — the removal is [verified in the manual](../03-Transaction-API.md#part-assembly-creation-workflow).)
- **Fix duplicated or wrong-quantity components** — a duplicate component double-counts real COGS. (`--component-qty COMP=QTY`; run.)
- **Fix component units** that do not match the component's base unit.

These change the item for **every** customer, so confirm before running. Read back `assembly_line` (`delete_flag`, `quantity`, unit).

### Step 3 — Create the rebate vendor (Transaction `Vendor`) (Verified; run on play 26.1.5950.0, 2026-10-10)

Create the vendor with `vendor` = `ON`, `track_rebates` = `ON`, terms by description, no currency, and its rebate receivable and allowance accounts on `REBATE_ACCOUNTS.d_vendor_rebate_accounts`. The runbooks leave `id` out: P21 numbered the vendor from the address sequence and returned it in the header's result row, and the save created the same-ID supplier with `vendor_supplier.primary_vendor = 'Y'`. [Payload and traps](../03-Transaction-API.md#vendor-service-creating-a-vendor-and-its-supplier).

Some programs book the receivable against a dedicated internal vendor (one per location) rather than the real supplier, and file the claim to the supplier separately; P21 does not care which, as long as Track Rebates is on.

### Step 4 — Make it the primary supplier at the source location (Transaction `Item`) (Verified; run on play 26.1.5950.0, 2026-10-10)

Per assembly item, at the **source** location (`source_loc_id`; the ship location, except on a transfer line). When the sales location differs from it, the sales location's primary supplier does not count; the runbooks use one location for both:

1. Insert the vendor's supplier row on the location's supplier list: Transaction `Item`, `SUPPLIER_X_LOCATION` keyed on both `location_id` and `supplier_id`, `IgnoreDisabled: true` ([details](../03-Transaction-API.md#adding-a-location-supplier-row-the-prerequisite-insert)).
2. Flip it to primary. Items with a zero supplier cost or list price trip the *Item Issues Detected* rule, which the Transaction API cannot answer — use the [Interactive fallback](../04-Interactive-API.md#worked-example-item-issues-detected-rule-callback) and answer `cb_1`, or [fix the data](../03-Transaction-API.md#item-issues-detected-popup-root-cause-and-data-fix). (The verification item did not trip it.)

Read back `inv_loc.primary_supplier_id` at the source location — the flag write can succeed and flip nothing — and, after order entry, read `oe_line.supplier_id`: it is usually, not always, that primary supplier.

### Step 5 — Price and cost the contract lines (Transaction `JobContractPricing`) (Verified; run on play 26.1.5950.0, 2026-10-10)

One line per POST. For each assembly: `pricing_method` = `Price` **before** `price`; `commission_cost_type_cd` = `Value` with the true cost; **`other_cost_type_cd` = `Value` with the rebated component cost**. [Payload](../03-Transaction-API.md#commission-costs). If the supplier pays a fixed amount per unit instead, set the other cost to `Source` / `Average Cost` / `Difference` with the rebate as a **positive** value; the accrual then stays exactly that amount as moving average moves ([details](../03-Transaction-API.md#a-fixed-per-unit-rebate-source-average-cost-difference)).

Attach every ship-to that orders to the contract ([details](../03-Transaction-API.md#attaching-a-ship-to-to-an-existing-contract)) — pricing follows the ship-to grid, not the contract header. The runbooks send the ship-to as a keyed `CUSTOMER_SHIP_TO.customer_ship_to` row in the same POST and read `job_price_customer_shipto` back; in the verification runs the ship-to was already on the contract, so attaching a *new* one was not exercised.

### Step 6 — Order entry and invoicing (Verified; run on play 26.1.5950.0, 2026-10-10)

Enter orders with `unit_price` blank so the contract price and binding fill in at entry ([sales-order-to-invoice](sales-order-to-invoice.md)). A line is bound once, at entry: a bound line re-reads the contract's other cost at invoicing; a line entered before the item was on the contract never binds — delete and re-enter it. The runbooks enter one unit through the Transaction API (`quote` = `OFF`), check `oe_line.job_price_hdr_uid` and `oe_line.supplier_id`, print the pick ticket and ship-confirm it.

> **Observed on the test tenant:** the assembled part (`production_order_processing` = `Y`, `auto_create_prod_order` = `N`, stock on hand) entered through the Transaction API came back as an `assembly = 'P'` line that allocated the finished unit, followed by its components as `assembly = 'N'` lines at $0. The components appeared on the invoice with `qty_shipped` and `cogs_amount` filled, while their `oe_line.qty_invoiced` stayed 0 and their on-hand did not move — the double-counting trap described under *Reporting cost and margin without double-counting* below.

## Verify — the acceptance test is a real invoice

On a test order shipped and invoiced (the runbooks check the first three automatically):

- `invoice_line.unit_price` = the contract price; `commission_cost` = the contract value × its multiplier; `oe_line.job_price_hdr_uid` = the contract.
- `invoice_line.cogs_amount` = the contract's **other cost** value, not the moving average.
- A `vendor_rebate` row for the invoice line: vendor = the rebate vendor, base cost = moving average, after-rebate cost = the contract value, due = the difference.
- GL for the invoice: the Sales Journal books COGS at the full moving average, then a Rebate Journal entry debits the rebate receivable (re-suffixed to the sales location) and credits COGS — net COGS = the contract value. The full entry, line by line: [The GL flow of a contract rebate](../03-Transaction-API.md#the-gl-flow-of-a-contract-rebate).
- No charge lines on the exploded order.

If COGS dropped but **no** `vendor_rebate` row appeared, the line's supplier is not the Track Rebates vendor: `vendor_rebate.vendor_id` is `oe_line.supplier_id`, usually stamped at entry from the primary supplier at the line's source location (step 4); read it back to confirm. The parent line accrues the same way whether the assembly was built on a production order linked to the sale, built to stock, or sold as a plain stock line; a kit parent on a contract whose own supplier does not track rebates instead lets its components accrue from their own rebate pages, with no parent row (a parent supplier that tracks rebates is untested). Verified on play 26.1.5950.0, 2026-10-17: [Rebates on assembled parents](../03-Transaction-API.md#rebates-on-assembled-parents-production-orders-build-to-stock-and-kits) · [GL flow](../03-Transaction-API.md#the-gl-flow-of-a-contract-rebate).

## Steps 4 and 5, in code

The two payload builders where the rebate is won or lost; the step sequencing and read-backs are in the files.

<!-- tabs -->
```python
def build_supplier_payloads(args: argparse.Namespace, supplier_id: str) -> tuple[dict, dict]:
    """Step 4: insert the location supplier row (both keys + IgnoreDisabled), then flip primary."""
    def item_payload(detail: dict, ignore: bool) -> dict:
        return payload("Item", [
            element("TABPAGE_1.tp_1_dw_1", "Form", ["item_id"], [[edit("item_id", args.item)]]),
            element("TABPAGE_17.invloclist", "List", ["location_id"],
                    [[edit("location_id", args.ship_from)]]),
            detail,
        ], ignore_disabled=ignore)
    insert = item_payload(element("SUPPLIER_X_LOCATION.supplier_x_location", "List",
                                  ["location_id", "supplier_id"],
                                  [[edit("location_id", args.ship_from),
                                    edit("supplier_id", supplier_id)]]), True)
    flip = item_payload(element("SUPPLIER_X_LOCATION.supplier_x_location", "List", ["supplier_id"],
                                [[edit("supplier_id", supplier_id),
                                  edit("primary_supplier", "ON")]]), False)
    return insert, flip


def build_contract_payload(args: argparse.Namespace) -> dict:
    """Step 5: ship-to on the grid; pricing_method BEFORE price; both costs type Value."""
    return payload("JobContractPricing", [
        element("FORM.d_dw_job_price_hdr", "Form", [],
                [[edit("company_id", args.company), edit("contract_no", args.contract_no),
                  edit("job_no", args.job_no)]]),
        element("CUSTOMER_SHIP_TO.customer_ship_to", "List", ["customer_id", "ship_to_id"],
                [[edit("customer_id", args.customer), edit("ship_to_id", args.ship_to)]]),
        element("JOBPRICELINE.jobpriceline", "List", ["item_id"],
                [[edit("item_id", args.item), edit("uom", "EA"),
                  edit("pricing_method", "Price"), edit("price", args.price)]]),
        element("JOBPRICECOST.jobpricecost", "Form", ["item_id"],
                [[edit("item_id", args.item),
                  edit("commission_cost_type_cd", "Value"), edit("commission_cost_value", args.true_cost),
                  edit("other_cost_type_cd", "Value"), edit("other_cost_value", args.rebated_cost)]]),
    ], ignore_disabled=True)
```

```csharp
/// <summary>Step 4: insert the location supplier row (both keys + IgnoreDisabled), then flip it primary.</summary>
private static (JObject Insert, JObject Flip) BuildSupplierPayloads(string item, string location, string supplierId)
{
    JObject ItemPayload(JObject detail, bool ignore) => Payload("Item", ignore,
        Element("TABPAGE_1.tp_1_dw_1", "Form", new[] { "item_id" }, new[] { Edit("item_id", item) }),
        Element("TABPAGE_17.invloclist", "List", new[] { "location_id" }, new[] { Edit("location_id", location) }),
        detail);
    return (
        ItemPayload(Element("SUPPLIER_X_LOCATION.supplier_x_location", "List", new[] { "location_id", "supplier_id" },
            new[] { Edit("location_id", location), Edit("supplier_id", supplierId) }), true),
        ItemPayload(Element("SUPPLIER_X_LOCATION.supplier_x_location", "List", new[] { "supplier_id" },
            new[] { Edit("supplier_id", supplierId), Edit("primary_supplier", "ON") }), false));
}

/// <summary>Step 5: ship-to on the grid; pricing_method BEFORE price; both costs type Value.</summary>
private static JObject BuildContractPayload(
    string company, string contractNo, string jobNo, string customer, string shipTo, string item,
    string price, string trueCost, string rebatedCost) =>
    Payload("JobContractPricing", true,
        Element("FORM.d_dw_job_price_hdr", "Form", Array.Empty<string>(), new[]
            { Edit("company_id", company), Edit("contract_no", contractNo), Edit("job_no", jobNo) }),
        Element("CUSTOMER_SHIP_TO.customer_ship_to", "List", new[] { "customer_id", "ship_to_id" },
            new[] { Edit("customer_id", customer), Edit("ship_to_id", shipTo) }),
        Element("JOBPRICELINE.jobpriceline", "List", new[] { "item_id" }, new[]
            { Edit("item_id", item), Edit("uom", "EA"), Edit("pricing_method", "Price"), Edit("price", price) }),
        Element("JOBPRICECOST.jobpricecost", "Form", new[] { "item_id" }, new[]
        {
            Edit("item_id", item),
            Edit("commission_cost_type_cd", "Value"), Edit("commission_cost_value", trueCost),
            Edit("other_cost_type_cd", "Value"), Edit("other_cost_value", rebatedCost),
        }));
```
<!-- /tabs -->

> **Payload files** (validator-verified, JSON only): [step 4 supplier row](../../examples/payloads/json/add-supplier-x-loc.json) · [step 4 flip](../../examples/payloads/json/set-primary-supplier.json) · [step 5 contract line](../../examples/payloads/json/contract-line-rebate-costs.json) — see [payloads README](../../examples/payloads/README.md).

## Reporting cost and margin without double-counting (Verified)

Margin reports on a program like this go wrong in two ways, even when the setup above is correct:

- **Kit parent `commission_cost` ignores rebate pages.** A kit parent line rolls up its components' pre-rebate `sales_cost` into `commission_cost`, even when rebate price pages lower the components' own cost. On `assembly = 'B'` parents, `other_cost` and COGS get the rebated rollup. On `assembly = 'P'` parents, the invoice posts both `commission_cost` and `other_cost` at the pre-rebate rollup. A report on `commission_cost` shows the program at a loss. A contract line with commission cost type `Value` on the kit parent replaces the rollup: the parent's `commission_cost` is then the contract value ([verified](../03-Transaction-API.md#rebates-on-assembled-parents-production-orders-build-to-stock-and-kits)).
- **Component lines carry COGS too.** Summing cost over every invoice line counts each kit twice. `invoice_line.invoice_line_uid_parent` ≠ 0 marks a component line; take cost from the parents or from the components, not both.

Detail and an OData query: [02 § Kit and assembly lines](../02-OData-API.md#kit-and-assembly-lines-parent-cost-ignores-rebates-and-component-lines-carry-cogs-too).

> **Credit:** *@mrwuss* — reporting traps verified against production data 26.1, June 2026, re-checked October 2026 ([#183](https://github.com/mrwuss/p21-api-documentation/issues/183)).

## Maintenance

| Trigger | Action |
|---|---|
| Periodically | Re-run step 1 and add newly ordered assemblies |
| New assembly first ordered | [new-assembled-part](new-assembled-part.md), then steps 4–5 for it |
| Rebate percent or supplier list price changes | Recompute costs and prices; re-push step 5 |
| New ship-to | Attach it to the contract |
| Contract nearing its end date | Renew or extend — orders past the end date do not price |

> **Credit:** [Alex Westemeier](https://github.com/AWestemeier) — program built and proven on play and production, 2026, including the rebate trigger end to end on play (September 2026). Runnable Python and C# runbook, rebate trigger included: run end to end on play 26.1.5950.0, 2026-10-10.
