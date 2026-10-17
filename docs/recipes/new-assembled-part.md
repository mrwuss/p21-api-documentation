# New Assembled Part: Item → Job Contract → Production Order

Set up a brand-new assembled part end to end — the item and its locations, its bill of materials, its line on a customer's job contract, and its first build-to-stock production order — by copying a similar "template" part that already exists.

**API:** Inventory REST + Transaction + Interactive · **Services:** `Item`, `Assembly`, `JobContractPricing`, `ProductionOrder` · **Deep dive:** [Creating an Item in the Item Window](../04-Interactive-API.md#creating-an-item-in-the-item-window) · [Minimum Create Payload](../11-Inventory-REST-API.md#minimum-create-payload) · [Assembly Service](../03-Transaction-API.md#assembly-service) · [JobContractPricing Service](../03-Transaction-API.md#jobcontractpricing-service) · [Production Order Lifecycle](../12-Production-Labor-API.md#production-order-lifecycle-end-to-end)

Steps 0–5 are one runnable program, in Python and C#, that runs each step and reads it back before the next: [`examples/python/recipes/new_assembled_part.py`](../../examples/python/recipes/new_assembled_part.py) · [`examples/csharp/Recipes/NewAssembledPart.cs`](../../examples/csharp/Recipes/NewAssembledPart.cs) (menu item 36). Both are dry runs until you pass `--execute` or type `EXECUTE`. If the part belongs to a supplier-rebate program, run this page and then [rebate-assembly-program](rebate-assembly-program.md).

**Status legend:** **Run on play 26.1.5950.0, 2026-10-10** = the step ran in both the Python and the C# runbook against a play tenant on that build and date, with a read-back. **Manual** = not run by the runbooks; a person does it, or another page's program does. **Verified** = run end to end with a read-back by the credited contributor on production (two parts, September 2026); **Inferred** = follows from verified behavior but was not run as its own step.

## Inputs

- The new part number (here `ASSY-002`) and a **template part** in the same family (here `ASSY-001`) with a known-good BOM, contract line and locations.
- The customer's job contract (`job_no` `JOB-001`, `contract_no` `CONTRACT-001`), and its pricing rule (price from cost and target margin — a business input, not something P21 derives). The contract's customer must have **Job/Contract Pricing** enabled. A customer created through the API usually has `use_vendor_contracts_flag = Y`, which disables `customer.job_pricing`; set `use_vendor_contracts_flag = N` first, then `job_pricing = Y`, in the same `Customer` transaction ([03 § Customer Service — Turning On Job/Contract Pricing](../03-Transaction-API.md#customer-service-turning-on-jobcontract-pricing)).
- The locations the part needs: here sales location `10`, a parts location `20` and a make (WIP) location `30`.
- Any **header fields your production orders require.** On the test tenant two user-defined header columns were required, and the save named them one at a time (*"'…' is a required column."*). Pass them with `--header-field name=value`.

## Run it

```bash
python examples/python/recipes/new_assembled_part.py            # dry run: payloads + plan
python examples/python/recipes/new_assembled_part.py --company ACME --item ASSY-002 \
    --description "Assembly, Example, 2-Port" --template ASSY-001 --supplier SUP-100 \
    --division SUP-100 --product-group PG-01 --sales-location 10 --other-locations 20 30 \
    --make-location 30 --parts-location 20 --job-no JOB-001 --contract-no CONTRACT-001 \
    --margin 0.30 --qty-to-make 1 --header-field ufc_prod_order_hdr_ud_example=VALUE --execute
```

## Runbook

| # | Step | Surface | Status |
|---|---|---|---|
| 0 | Price it from the template's BOM | OData | Run on play 26.1.5950.0, 2026-10-10 (the neighbor check is manual) |
| 1 | Item and its first location | Inventory REST create (the Interactive `Item` window: manual — see below) | Run on play 26.1.5950.0, 2026-10-10 |
| 2 | The other locations | Transaction `Item` | Run on play 26.1.5950.0, 2026-10-10 |
| 3 | BOM and assembly flags | Transaction `Assembly` | Run on play 26.1.5950.0, 2026-10-10 |
| 4 | The contract line | Transaction `JobContractPricing` | Run on play 26.1.5950.0, 2026-10-10 |
| 5 | First production order — create | Interactive `ProductionOrder` | Run on play 26.1.5950.0, 2026-10-10 |
| 5 | Print, pick, confirm, complete | See [production-order-runbook](production-order-runbook.md) | Manual |

### Step 0 — Price it first (Inferred method; run on play 26.1.5950.0, 2026-10-10)

Work out the component cost from the template's BOM and the new part's differences, then the price from your pricing rule. The runbooks read the template's live `assembly_line` rows, drop charge lines (`other_charge_item = 'Y'`), stop if a component's unit is not its `inv_mast.base_unit`, and sum `quantity` × `inv_loc.moving_average_cost` at the parts location; price = cost ÷ (1 − margin). **Check the method against a neighbor already on the contract** (manual): it must reproduce that line's commission cost to the cent. If it does not, stop — the BOM or the rule is wrong.

### Step 1 — Item and its first location (Inventory REST in the runbooks; Interactive `Item` window: Verified on production, manual here)

**Runbooks: the [Inventory REST create](../11-Inventory-REST-API.md#minimum-create-payload)** — `ItemId` (uppercase it yourself), `ItemDesc` (passed explicitly, 40 characters at most), one location with its product group, one supplier with its division, and the location–supplier row as primary. Read back `inv_mast.item_desc`. The created location came back `stockable = 'N'`.

**The Interactive `Item` window** ([steps](../04-Interactive-API.md#creating-an-item-in-the-item-window)) is the path the contributor used on production: pass `item_desc` explicitly rather than copying the template's, set all four unit flags on the Units of Measure row, answer **Yes** to the product-group GL prompt, fill the location's supplier row, save — **one location per session**. It could not be run on the test tenant: after a new `item_id`, **every column on the Units of Measure grid (`TABPAGE_2.tp_2_dw_2`) was disabled** for both API users tried (`Column is disabled: unit_id`, and the same for each unit flag), so the save failed *"A Default Sales Unit, Sales Pricing Unit, Default Purchasing Unit And Purchase Pricing Unit Must Each Be Specified."* — the DynaChange screen-version lock described [on that section](../04-Interactive-API.md#creating-an-item-in-the-item-window). Use the window when your role can edit that grid and you need its prompts.

### Step 2 — The other locations (Transaction `Item`) (Verified; run on play 26.1.5950.0, 2026-10-10)

One POST per location, `Status: "New"`, `IgnoreDisabled: true` at the payload top level: `TABPAGE_1.tp_1_dw_1` (`item_id`) → `TABPAGE_17.invloclist` (`location_id`, `company_id`, `stockable`) → `TABPAGE_18.inv_loc_detail` (groups, tax group, `track_bins`) → `SUPPLIER_X_LOCATION.supplier_x_location` keyed on **both** `location_id` and `supplier_id` ([why](../03-Transaction-API.md#adding-a-location-supplier-row-the-prerequisite-insert)). Make the make and parts locations stockable.

Read back `inv_loc` per location (GL accounts and primary supplier included). In the verification runs the new location's supplier row became its primary supplier without a separate flip.

### Step 3 — BOM and assembly flags (`Assembly`) (Verified here; run on play 26.1.5950.0, 2026-10-10)

A **new** part number is not yet a component of anything, so the Transaction API creates the assembly: header `TABPAGE_1.assemblyhdr` (`inv_mast_item_id`, and `production_order_processing` sent explicitly) plus one `TABPAGE_17.tp_17_dw_17` row per component (`item_id_service_labor_id`, `quantity`, `unit_of_measure`). Set the other header flags with a second keyed `Status: "New"` POST. If the item **is** already a component of another assembly, the Transaction create fails and you must use the Interactive window ([details](../03-Transaction-API.md#part-assembly-creation-workflow)).

- **Copy only physical components** from the template. Leave out charge lines (labor, burden, other charge items) if your costing replaces them.
- **Component UOM must match the component's base unit** — a mismatch was the most common defect found in copied BOMs.
- Header flags for a build-to-stock part: `production_order_processing` `ON`, `print_incomplete_assemblies` `ON`, `ship_incomplete_assemblies` `ON`, `auto_create_prod_order` `OFF` ([what each does](../12-Production-Labor-API.md#assembly-behavior-flags)).

Read back `assembly_hdr` and `assembly_line` (`quantity`, unit, no charge lines). The per-component quantity is `assembly_line.quantity`; `qty_needed` stayed `0` on every row created this way.

### Step 4 — The contract line (Transaction `JobContractPricing`) (Verified; run on play 26.1.5950.0, 2026-10-10)

One line per POST (inserts collide when batched). Header `FORM.d_dw_job_price_hdr` with `Keys: []` and `job_no` + `contract_no` in `Edits`; `JOBPRICELINE.jobpriceline` keyed on `item_id` with **`pricing_method` = `Price` before `price`** (the other order silently saves $0); `JOBPRICECOST.jobpricecost` with `commission_cost_type_cd` = `Value` and the commission cost, plus — for a rebate program — `other_cost_type_cd` = `Value` and the rebated cost. `IgnoreDisabled: true` at the top level for the cost fields. [Manual](../03-Transaction-API.md#commission-costs).

Read back `job_price_line`. A line already **bound** to a sales order re-reads its cost from the contract at invoicing, so the other cost can be set later; an order line entered before this contract line existed **never** binds ([details](../03-Transaction-API.md#binding-happens-once-at-line-entry)).

### Step 5 — First production order (`ProductionOrder`) (Verified; create run on play 26.1.5950.0, 2026-10-10; the rest manual)

Interactive `ProductionOrder`: header `source_loc_id` (make) **before** `inventory_location_id` (parts), in separate calls, then any required header UD fields; the assembly line on `TABPAGE_17.tp_17_dw_17` (`assembly_item_id`, `qty_to_make`); save. The window clears after the save — find the order through `prod_order_line` by the item's `inv_mast_uid` (newest `prod_order_number`), then read `prod_order_hdr.source_location_id` and `inventory_location_id` back.

Then print the form, run the pick ticket **only when every component is fully allocated**, confirm the pick promptly, and complete when built — the runbooks stop at the create; every trap on the way is in [12 § Production Order Gotchas](../12-Production-Labor-API.md#production-order-gotchas-field-verified) and the [production-order-runbook](production-order-runbook.md).

## Steps 3 and 4, in code

The two payload builders from the runbooks; the step sequencing and read-backs are in the files.

<!-- tabs -->
```python
def build_assembly_payloads(item: str, components: list[dict]) -> tuple[dict, dict]:
    """Step 3: create with the minimum, then set the header flags in a second keyed POST.

    production_order_processing is sent explicitly on the create (its default
    can be ON); item_desc and prorate_cost_by are disabled on create.
    """
    create = payload("Assembly", [
        element("TABPAGE_1.assemblyhdr", "Form", ["inv_mast_item_id"],
                [[edit("inv_mast_item_id", item), edit("production_order_processing", "ON")]]),
        element("TABPAGE_17.tp_17_dw_17", "List", ["item_id_service_labor_id"],
                [[edit("item_id_service_labor_id", c["item_id"]),
                  edit("quantity", f"{c['quantity']:g}"),
                  edit("unit_of_measure", c["uom"])] for c in components]),
    ])
    flags = payload("Assembly", [
        element("TABPAGE_1.assemblyhdr", "Form", ["inv_mast_item_id"],
                [[edit("inv_mast_item_id", item), edit("print_incomplete_assemblies", "ON"),
                  edit("ship_incomplete_assemblies", "ON"), edit("auto_create_prod_order", "OFF")]]),
    ])
    return create, flags


def build_contract_payload(args: argparse.Namespace, price: str, commission_cost: str) -> dict:
    """Step 4: ONE line per POST; pricing_method BEFORE price; IgnoreDisabled for the cost."""
    return payload("JobContractPricing", [
        element("FORM.d_dw_job_price_hdr", "Form", [],      # Keys stay empty
                [[edit("company_id", args.company), edit("contract_no", args.contract_no),
                  edit("job_no", args.job_no)]]),
        element("JOBPRICELINE.jobpriceline", "List", ["item_id"],
                [[edit("item_id", args.item), edit("uom", "EA"),
                  edit("pricing_method", "Price"), edit("price", price)]]),
        element("JOBPRICECOST.jobpricecost", "Form", ["item_id"],
                [[edit("item_id", args.item),
                  edit("commission_cost_type_cd", "Value"),      # type BEFORE value
                  edit("commission_cost_value", commission_cost)]]),
    ], ignore_disabled=True)
```

```csharp
/// <summary>Step 3: create with the minimum (production_order_processing sent
/// explicitly), then the header flags in a second keyed POST.</summary>
private static (JObject Create, JObject Flags) BuildAssemblyPayloads(
    string item, List<(string Item, string Qty, string Uom)> components) =>
    (Payload("Assembly", false,
        Element("TABPAGE_1.assemblyhdr", "Form", new[] { "inv_mast_item_id" },
            new[] { Edit("inv_mast_item_id", item), Edit("production_order_processing", "ON") }),
        Element("TABPAGE_17.tp_17_dw_17", "List", new[] { "item_id_service_labor_id" },
            components.Select(c => new[]
            {
                Edit("item_id_service_labor_id", c.Item), Edit("quantity", c.Qty), Edit("unit_of_measure", c.Uom),
            }).ToArray())),
     Payload("Assembly", false,
        Element("TABPAGE_1.assemblyhdr", "Form", new[] { "inv_mast_item_id" }, new[]
        {
            Edit("inv_mast_item_id", item), Edit("print_incomplete_assemblies", "ON"),
            Edit("ship_incomplete_assemblies", "ON"), Edit("auto_create_prod_order", "OFF"),
        })));

/// <summary>Step 4: ONE line per POST; pricing_method BEFORE price; IgnoreDisabled for the cost.</summary>
private static JObject BuildContractPayload(
    string company, string contractNo, string jobNo, string item, string price, string commissionCost) =>
    Payload("JobContractPricing", true,
        Element("FORM.d_dw_job_price_hdr", "Form", Array.Empty<string>(), new[]   // Keys stay empty
            { Edit("company_id", company), Edit("contract_no", contractNo), Edit("job_no", jobNo) }),
        Element("JOBPRICELINE.jobpriceline", "List", new[] { "item_id" }, new[]
        {
            Edit("item_id", item), Edit("uom", "EA"),
            Edit("pricing_method", "Price"), Edit("price", price),   // pricing_method FIRST
        }),
        Element("JOBPRICECOST.jobpricecost", "Form", new[] { "item_id" }, new[]
        {
            Edit("item_id", item),
            Edit("commission_cost_type_cd", "Value"),                // type BEFORE value
            Edit("commission_cost_value", commissionCost),
        }));
```
<!-- /tabs -->

## Checks that caught real mistakes

- A template whose own description disagreed with its own dimensions — always pass the new description explicitly.
- Component UOMs that did not match the component's base unit (the runbooks stop on one).
- A pick ticket run on a short order — the partial ticket had to be cancelled (`row_status_flag` = `"Canceled"`).

> **Credit:** [Alex Westemeier](https://github.com/AWestemeier) — runbook done on production for two parts, September 2026, through the Interactive `Item` window. Step 3's Transaction create was verified by the maintainer on 26.1.5950.0 (October 2026). Runnable Python and C# runbook (REST item create, steps 0–5 create): run end to end on play 26.1.5950.0, 2026-10-10.
