"""
New Assembled Part Runbook -- Item -> BOM -> Job Contract -> Production Order

Runs docs/recipes/new-assembled-part.md step by step for a brand-new part
copied from a "template" part, reading each step back before the next:

  0. Price it: roll up the copied BOM's component cost and apply the rule   (OData)
  1. Item + first location                                    (Inventory REST create)
  2. Every other location, one POST each                      (Transaction Item)
  3. BOM (template's physical components) + build-to-stock flags  (Transaction Assembly)
  4. The contract line: price, then a Value commission cost   (Transaction JobContractPricing)
  5. The first build-to-stock production order                (Interactive ProductionOrder)

Step 1 uses the Inventory REST create. The page's Interactive Item window
path could not be run here: on the test tenant every Units of Measure
column is disabled for the API user's role, so the window cannot save a
new item -- see the page.

After step 5, print, pick, confirm and complete the order with
production_order_runbook.py / docs/recipes/production-order-runbook.md.

Mirrors: docs/recipes/new-assembled-part.md

Usage:
    python examples/python/recipes/new_assembled_part.py            # dry run
    python examples/python/recipes/new_assembled_part.py --execute  # run + verify
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from runbook_common import (TIMEOUT, P21Runbook, check, edit, element, payload, result_value,
                            show)

import warnings
warnings.filterwarnings("ignore")

# --- Configuration (generic placeholders -- substitute your own) ------------
COMPANY_ID = "ACME"
NEW_ITEM = "ASSY-002"
DESCRIPTION = "Assembly, Example, 2-Port"     # pass it explicitly -- never copy the template's
TEMPLATE_ITEM = "ASSY-001"                     # same family, known-good BOM
SUPPLIER_ID = "SUP-100"
DIVISION_ID = "SUP-100"                        # often equals the supplier ID -- read a sibling item
PRODUCT_GROUP = "PG-01"
SALES_LOCATION = "10"                          # step 1 location
OTHER_LOCATIONS = ["20", "30"]                 # step 2: parts and make locations
MAKE_LOCATION = "30"                           # production order source_loc_id
PARTS_LOCATION = "20"                          # production order inventory_location_id
JOB_NO = "JOB-001"
CONTRACT_NO = "CONTRACT-001"
TARGET_MARGIN = "0.30"                         # pricing rule: price = cost / (1 - margin)
QTY_TO_MAKE = "1"
HEADER_FIELDS: list[str] = []                  # required production-order header UD fields, name=value


def component_cost(rb: P21Runbook, components: list[dict], parts_location: str) -> float:
    """Step 0: sum of quantity x moving average cost at the parts location."""
    total = 0.0
    for comp in components:
        loc = rb.one("inv_loc", f"inv_mast_uid eq {comp['component_inv_mast_uid']} and "
                                f"location_id eq {parts_location}", "moving_average_cost")
        cost = float(comp["quantity"]) * float(loc["moving_average_cost"])
        print(f"    {comp['item_id']}: {comp['quantity']:g} x {float(loc['moving_average_cost']):g}"
              f" = {cost:.4f}")
        total += cost
    return total


def template_components(rb: P21Runbook, template: str) -> list[dict]:
    """The template's live physical components -- charge lines are left out."""
    rows = rb.odata("assembly_line", f"inv_mast_uid eq {rb.item_uid(template)} and delete_flag eq 'N'",
                    "component_inv_mast_uid,quantity,unit_of_measure,other_charge_item,sequence_number",
                    orderby="sequence_number")
    comps = []
    for row in rows:
        im = rb.one("inv_mast", f"inv_mast_uid eq {row['component_inv_mast_uid']}",
                    "item_id,base_unit")
        if row["other_charge_item"] == "Y":
            print(f"    skip charge line {im['item_id']}")
            continue
        if row["unit_of_measure"] != im["base_unit"]:   # the most common copied-BOM defect
            raise SystemExit(f"{im['item_id']}: BOM unit {row['unit_of_measure']} is not the "
                             f"component's base unit {im['base_unit']} -- fix the template first")
        comps.append({"item_id": im["item_id"], "quantity": float(row["quantity"]),
                      "uom": row["unit_of_measure"],
                      "component_inv_mast_uid": row["component_inv_mast_uid"]})
    return comps


def _id(value: str) -> int | str:
    """REST bodies take numeric IDs as numbers."""
    return int(value) if value.isdigit() else value


def build_create_body(args: argparse.Namespace) -> dict:
    """Step 1: Inventory REST minimum create (item, location, supplier, location supplier)."""
    return {
        "ItemId": args.item.upper(),               # the API does not uppercase for you
        "ItemDesc": args.description[:40],         # 40-character limit
        "ObjectName": "inv_mast",
        "Locations": {"list": [{"LocationId": _id(args.sales_location),
                                "ProductGroupId": args.product_group, "ObjectName": "inv_loc"}]},
        "Suppliers": {"list": [{"SupplierId": _id(args.supplier), "DivisionId": _id(args.division),
                                "ObjectName": "inventory_supplier"}]},
        "LocationSuppliers": {"list": [{"LocationId": _id(args.sales_location),
                                        "SupplierId": _id(args.supplier), "PrimarySupplier": "Y",
                                        "ObjectName": "inventory_supplier_x_loc"}]},
    }


def build_location_payload(args: argparse.Namespace, location: str) -> dict:
    """Step 2: one location per POST -- the location row, its detail, its supplier row.

    The supplier row keys on BOTH location_id and supplier_id and needs
    IgnoreDisabled to insert.
    """
    return payload("Item", [
        element("TABPAGE_1.tp_1_dw_1", "Form", ["item_id"], [[edit("item_id", args.item)]]),
        element("TABPAGE_17.invloclist", "List", ["location_id"],
                [[edit("location_id", location), edit("company_id", args.company),
                  edit("stockable", "ON")]]),
        element("TABPAGE_18.inv_loc_detail", "Form", ["location_id"],
                [[edit("product_group_id", args.product_group)]]),
        element("SUPPLIER_X_LOCATION.supplier_x_location", "List", ["location_id", "supplier_id"],
                [[edit("location_id", location), edit("supplier_id", args.supplier)]]),
    ], ignore_disabled=True)


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


def create_production_order(rb: P21Runbook, args: argparse.Namespace) -> str:
    """Step 5: Interactive ProductionOrder -- make location, THEN parts location."""
    session = rb.session()
    window_id = session.open_window("ProductionOrder")
    try:
        session.change(window_id, "TABPAGE_1", "tp_1_dw_1", "source_loc_id", args.make_location)
        session.change(window_id, "TABPAGE_1", "tp_1_dw_1", "inventory_location_id",
                       args.parts_location)                  # separate call, after the make location
        for pair in args.header_field:                        # e.g. a required UD column
            name, value = pair.split("=", 1)
            session.change(window_id, "TABPAGE_1", "tp_1_dw_1", name, value)
        session.tab(window_id, "TABPAGE_17")
        session.change(window_id, "TABPAGE_17", "tp_17_dw_17", "assembly_item_id", args.item)
        session.change(window_id, "TABPAGE_17", "tp_17_dw_17", "qty_to_make", args.qty_to_make)
        session.save(window_id)
    finally:
        session.cleanup(window_id)
    # The window clears after the save: find the order by its line's item.
    line = rb.one("prod_order_line", f"inv_mast_uid eq {rb.item_uid(args.item)}",
                  "prod_order_number,qty_to_make", orderby="prod_order_number desc")
    hdr = rb.one("prod_order_hdr", f"prod_order_number eq {line['prod_order_number']}",
                 "prod_order_number,source_location_id,inventory_location_id,approved")
    print(f"    prod_order_number = {hdr['prod_order_number']}, qty_to_make {line['qty_to_make']}")
    check("prod_order_hdr.source_location_id", hdr["source_location_id"], int(args.make_location))
    check("prod_order_hdr.inventory_location_id", hdr["inventory_location_id"],
          int(args.parts_location))
    return str(hdr["prod_order_number"])


def main() -> None:
    """Entry point: dry run prints the payloads; --execute runs and verifies each step."""
    parser = argparse.ArgumentParser(
        description="New assembled part runbook (docs/recipes/new-assembled-part.md)")
    parser.add_argument("--company", default=COMPANY_ID)
    parser.add_argument("--item", default=NEW_ITEM)
    parser.add_argument("--description", default=DESCRIPTION)
    parser.add_argument("--template", default=TEMPLATE_ITEM)
    parser.add_argument("--supplier", default=SUPPLIER_ID)
    parser.add_argument("--division", default=DIVISION_ID)
    parser.add_argument("--product-group", default=PRODUCT_GROUP)
    parser.add_argument("--sales-location", default=SALES_LOCATION)
    parser.add_argument("--other-locations", nargs="*", default=OTHER_LOCATIONS)
    parser.add_argument("--make-location", default=MAKE_LOCATION)
    parser.add_argument("--parts-location", default=PARTS_LOCATION)
    parser.add_argument("--job-no", default=JOB_NO)
    parser.add_argument("--contract-no", default=CONTRACT_NO)
    parser.add_argument("--margin", default=TARGET_MARGIN)
    parser.add_argument("--qty-to-make", default=QTY_TO_MAKE)
    parser.add_argument("--header-field", action="append", default=list(HEADER_FIELDS),
                        help="Production-order header field name=value (repeatable)")
    parser.add_argument("--execute", action="store_true",
                        help="Actually run the steps (default: dry run)")
    args = parser.parse_args()
    args.item = args.item.upper()

    print("Runbook - New Assembled Part: Item -> BOM -> Job Contract -> Production Order")
    print("=" * 60)
    if not args.execute:
        print(f"\nStep 0 (OData): copy {args.template}'s physical components, cost them at "
              f"location {args.parts_location}, price = cost / (1 - {args.margin}).")
        print("\nStep 1 POST {base}/api/inventory/parts/ (trailing slash):")
        print(json.dumps(build_create_body(args), indent=2))
        for loc in args.other_locations:
            show(f"Step 2 Item payload for location {loc}", build_location_payload(args, loc))
        demo = [{"item_id": "COMP-001", "quantity": 2.0, "uom": "EA"}]
        create, flags = build_assembly_payloads(args.item, demo)
        show("Step 3 Assembly create (components copied from the template)", create)
        show("Step 3 Assembly header flags", flags)
        show("Step 4 JobContractPricing payload (price/cost from step 0)",
             build_contract_payload(args, "{price}", "{cost}"))
        print(f"\nStep 5 (Interactive ProductionOrder): source_loc_id={args.make_location}, then "
              f"inventory_location_id={args.parts_location}, header fields {args.header_field}, "
              f"TABPAGE_17 assembly_item_id={args.item}, qty_to_make={args.qty_to_make}, save.")
        print("\nRe-run with --execute to run it.")
        return

    rb = P21Runbook()
    if rb.odata("inv_mast", f"item_id eq '{args.item}'", "item_id"):
        raise SystemExit(f"{args.item} already exists -- pick a new part number")

    print(f"\nStep 0 - Price it from {args.template}'s BOM (OData)")
    components = template_components(rb, args.template)
    cost = component_cost(rb, components, args.parts_location)
    price = cost / (1 - float(args.margin))
    print(f"    component cost {cost:.2f} -> price {price:.2f} at margin {args.margin}")

    print("\nStep 1 - Item and its first location (Inventory REST create)")
    resp = httpx.post(f"{rb.base_url}/api/inventory/parts/",   # no slash = 307
                      headers=rb.headers, json=build_create_body(args), verify=rb.verify,
                      timeout=TIMEOUT)
    if resp.status_code >= 400:
        raise SystemExit(f"Item create failed: HTTP {resp.status_code} {resp.text[:300]}")
    item = rb.one("inv_mast", f"item_id eq '{args.item}'", "item_id,item_desc,inv_mast_uid")
    check("inv_mast.item_desc", item["item_desc"], args.description[:40])

    print("\nStep 2 - The other locations (Transaction Item, one POST per location)")
    for loc in args.other_locations:
        rb.transaction(build_location_payload(args, loc), f"Item location {loc}")
    for row in rb.odata("inv_loc", f"inv_mast_uid eq {item['inv_mast_uid']}",
                        "location_id,stockable,product_group_id,primary_supplier_id,gl_account_no"):
        print(f"    inv_loc {row['location_id']}: stockable {row['stockable']} group "
              f"{row['product_group_id']} primary supplier {row['primary_supplier_id']} "
              f"GL {row['gl_account_no']}")
    locs = {str(r["location_id"]) for r in rb.odata("inv_loc", f"inv_mast_uid eq {item['inv_mast_uid']}",
                                                     "location_id")}
    check("locations present", sorted(locs), sorted({args.sales_location, *args.other_locations}))

    print("\nStep 3 - BOM and assembly flags (Transaction Assembly)")
    create, flags = build_assembly_payloads(args.item, components)
    rb.transaction(create, "Assembly create")
    rb.transaction(flags, "Assembly flags")
    hdr = rb.one("assembly_hdr", f"inv_mast_uid eq {item['inv_mast_uid']}",
                 "production_order_processing,print_incomplete_assemblies,"
                 "ship_incomplete_assemblies,auto_create_prod_order")
    for flag, expected in (("production_order_processing", "Y"), ("print_incomplete_assemblies", "Y"),
                           ("ship_incomplete_assemblies", "Y"), ("auto_create_prod_order", "N")):
        check(f"assembly_hdr.{flag}", hdr[flag], expected)
    lines = rb.odata("assembly_line", f"inv_mast_uid eq {item['inv_mast_uid']} and delete_flag eq 'N'",
                     "component_inv_mast_uid,quantity,unit_of_measure,other_charge_item")
    check("assembly_line rows", len(lines), len(components))

    print("\nStep 4 - The contract line (Transaction JobContractPricing)")
    rb.transaction(build_contract_payload(args, f"{price:.2f}", f"{cost:.2f}"), "Contract line")
    hdr = rb.one("job_price_hdr", f"contract_no eq '{args.contract_no}' and job_no eq '{args.job_no}'",
                 "job_price_hdr_uid")
    line = rb.one("job_price_line", f"job_price_hdr_uid eq {hdr['job_price_hdr_uid']} and "
                                    f"inv_mast_uid eq {item['inv_mast_uid']}",
                  "line_no,price,commission_cost_value")
    check("job_price_line.price", f"{float(line['price']):.2f}", f"{price:.2f}")
    check("job_price_line.commission_cost_value", f"{float(line['commission_cost_value']):.2f}",
          f"{cost:.2f}")

    print("\nStep 5 - First production order (Interactive ProductionOrder)")
    create_production_order(rb, args)
    print("\nNext: print, pick, confirm and complete it -- docs/recipes/production-order-runbook.md")
    print("\nRunbook complete.")


if __name__ == "__main__":
    main()
