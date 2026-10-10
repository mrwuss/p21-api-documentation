# New Assembled Part: Item → Job Contract → Production Order

Set up a brand-new assembled part end to end — the item and its locations, its bill of materials, its line on a customer's job contract, and its first build-to-stock production order — by copying a similar "template" part that already exists.

**API:** Interactive + Transaction · **Services:** `Item`, `Assembly`, `JobContractPricing`, `ProductionOrder` · **Deep dive:** [Creating an Item in the Item Window](../04-Interactive-API.md#creating-an-item-in-the-item-window) · [Assembly Service](../03-Transaction-API.md#assembly-service) · [JobContractPricing Service](../03-Transaction-API.md#jobcontractpricing-service) · [Production Order Lifecycle](../12-Production-Labor-API.md#production-order-lifecycle-end-to-end)

This page is a **checklist**, not a script. Each step names the surface, the fields that matter and the read-back. If the part belongs to a supplier-rebate program, do this page and then the rebate steps in [rebate-assembly-program](rebate-assembly-program.md).

**Status legend:** **Verified** = run end to end with a read-back by the credited contributor on production (two parts, September 2026); **Verified here** = re-tested by the maintainer on 26.1.5950.0; **Inferred** = follows from verified behavior but was not run as its own step.

## Inputs

- The new part number (here `ASSY-002`) and a **template part** in the same family (here `ASSY-001`) with a known-good BOM, contract line and locations.
- The customer's job contract (`job_no` `JOB-001`, `contract_no` `CONTRACT-001`), and its pricing rule (price from cost and target margin — a business input, not something P21 derives).
- The locations the part needs: here sales location `10`, a parts location `20` and a make (WIP) location `30`.

## Runbook

### Step 0 — Price it first (Inferred method, Verified use)

Work out the component cost from the template's BOM and the new part's differences, then the price from your pricing rule. **Check the method against a neighbor already on the contract**: it must reproduce that line's commission cost to the cent. If it does not, stop — the BOM or the rule is wrong.

### Step 1 — Item and its first location (Interactive `Item`) (Verified)

The Transaction API cannot create an item; the Interactive window can ([steps](../04-Interactive-API.md#creating-an-item-in-the-item-window)). Pass `item_desc` explicitly rather than copying the template's — a template's description can carry its own typo. Set all four unit flags on the Units of Measure row, answer **Yes** to the product-group GL prompt, fill the location's supplier row, save. **Only one location per session.** (The [Inventory REST create](../11-Inventory-REST-API.md#minimum-create-payload) is the alternative when you do not need the window's prompts.)

### Step 2 — The other locations (Transaction `Item`) (Verified)

One POST per location, `Status: "New"`, `IgnoreDisabled: true` at the payload top level: `TABPAGE_1.tp_1_dw_1` (`item_id`) → `TABPAGE_17.invloclist` (`location_id`, `company_id`, `stockable`) → `TABPAGE_18.inv_loc_detail` (groups, tax group, `track_bins`) → `SUPPLIER_X_LOCATION.supplier_x_location` keyed on **both** `location_id` and `supplier_id` ([why](../03-Transaction-API.md#adding-a-location-supplier-row-the-prerequisite-insert)). Make the make and parts locations stockable.

Read back `inv_loc` per location (GL accounts and primary supplier included).

### Step 3 — BOM and assembly flags (`Assembly`) (Verified here)

A **new** part number is not yet a component of anything, so the Transaction API creates the assembly: header `TABPAGE_1.assemblyhdr` (`inv_mast_item_id`) plus one `TABPAGE_17.tp_17_dw_17` row per component (`item_id_service_labor_id`, `quantity`, `unit_of_measure`). If the item **is** already a component of another assembly, the Transaction create fails and you must use the Interactive window ([details](../03-Transaction-API.md#part-assembly-creation-workflow)).

- **Copy only physical components** from the template. Leave out charge lines (labor, burden, other charge items) if your costing replaces them.
- **Component UOM must match the component's base unit** — a mismatch was the most common defect found in copied BOMs.
- Header flags for a build-to-stock part: `production_order_processing` `ON`, `print_incomplete_assemblies` `ON`, `ship_incomplete_assemblies` `ON`, `auto_create_prod_order` `OFF` ([what each does](../12-Production-Labor-API.md#assembly-behavior-flags)).

Read back `assembly_hdr` and `assembly_line` (`quantity`, unit, no charge lines).

### Step 4 — The contract line (Transaction `JobContractPricing`) (Verified)

One line per POST (inserts collide when batched). Header `FORM.d_dw_job_price_hdr` with `Keys: []` and `job_no` + `contract_no` in `Edits`; `JOBPRICELINE.jobpriceline` keyed on `item_id` with **`pricing_method` = `Price` before `price`** (the other order silently saves $0); `JOBPRICECOST.jobpricecost` with `commission_cost_type_cd` = `Value` and the commission cost, plus — for a rebate program — `other_cost_type_cd` = `Value` and the rebated cost. `IgnoreDisabled: true` at the top level for the cost fields. [Manual](../03-Transaction-API.md#commission-costs).

Read back `job_price_line`. A line already **bound** to a sales order re-reads its cost from the contract at invoicing, so the other cost can be set later; an order line entered before this contract line existed **never** binds ([details](../03-Transaction-API.md#binding-happens-once-at-line-entry)).

### Step 5 — First production order (`ProductionOrder`) (Verified)

Interactive `ProductionOrder`: header `source_loc_id` (make) **before** `inventory_location_id` (parts), in separate calls, then any required header UD fields; the assembly line on `TABPAGE_17.tp_17_dw_17` (`assembly_item_id`, `qty_to_make`); save. Then print the form, run the pick ticket **only when every component is fully allocated**, confirm the pick promptly, and complete when built. Every trap on the way: [12 § Production Order Gotchas](../12-Production-Labor-API.md#production-order-gotchas-field-verified) and the [production-order-runbook](production-order-runbook.md).

## Checks that caught real mistakes

- A template whose own description disagreed with its own dimensions — always pass the new description explicitly.
- Component UOMs that did not match the component's base unit.
- A pick ticket run on a short order — the partial ticket had to be cancelled (`row_status_flag` = `"Canceled"`).

> **Credit:** [Alex Westemeier](https://github.com/AWestemeier) — runbook done on production for two parts, September 2026; not re-run here except step 3's Transaction create, which was verified here by the maintainer on 26.1.5950.0 (October 2026).
