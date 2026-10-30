"""
Rebate-Tracked Assembly Program Runbook

Runs the API-reachable steps of docs/recipes/rebate-assembly-program.md for
one assembled part, reading each step back before the next one starts:

  1. Catalog: assemblies the customer ordered that are not on the contract (OData)
  2. Fix the BOM: a component quantity and/or a component removal  (Transaction Assembly)
  3. Create the rebate vendor, Track Rebates ON                    (Transaction Vendor)
  4. Make it the primary supplier at the SHIP-FROM location        (Transaction Item, x2)
  5. Contract line: price, Value commission cost, Value OTHER cost (Transaction JobContractPricing)
     + the ship-to on the contract's Customer/Ship To grid
  6. Acceptance test: order (unit_price blank) -> pick -> ship -> invoice, then
     invoice_line and vendor_rebate                                (Transaction + Interactive)

The rebate schedule, the pricing rule and the supplier claim are business
inputs; step 6's GL check (Sales Journal + Rebate Journal) is read by a
person -- see the page. Step 6 needs the assembled part in stock at the
ship-from location.

Mirrors: docs/recipes/rebate-assembly-program.md

Usage:
    python examples/python/recipes/rebate_assembly_program.py            # dry run
    python examples/python/recipes/rebate_assembly_program.py --execute  # run + verify
"""

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from runbook_common import (
    P21Runbook,
    build_order_payload,
    check,
    edit,
    element,
    payload,
    print_invoice,
    print_pick_ticket,
    result_value,
    ship_and_invoice,
    show,
)

import warnings

warnings.filterwarnings("ignore")

# --- Configuration (generic placeholders -- substitute your own) ------------
COMPANY_ID = "ACME"
CUSTOMER_ID = "CUST-100"
SHIP_TO_ID = "CUST-100"
CONTACT_ID = "300"
TAKER = "JSMITH"
JOB_NO = "JOB-001"
CONTRACT_NO = "CONTRACT-001"
SHIP_FROM = "30"  # source location -- decides the primary supplier
ITEM_ID = "ASSY-001"  # the assembled part (in stock at SHIP_FROM for step 6)
COMPONENT_QTY: list[str] = []  # step 2 fixes, COMPONENT=QTY
REMOVE_COMPONENTS: list[str] = []  # step 2 removals (charge lines, duplicates)
VENDOR_NAME = "Example Rebate Vendor"
VENDOR_ADDRESS = {
    "mail_address1": "100 Main St",
    "mail_city": "Springfield",
    "mail_state": "IL",
    "mail_postal_code": "62701",
}
AP_ACCOUNT = "2222200"  # stored form, no dash
REBATE_ACCOUNT = "1111100"
REBATE_ALLOWANCE_ACCOUNT = "3333300"
TERMS = "Net 30 Days"  # the terms DESCRIPTION, not the ID
PRICE = "45.00"
TRUE_COST = "30.60"  # commission cost (Value)
REBATED_COST = "24.00"  # other cost (Value) -- below the actual cost
SINCE = (date.today() - timedelta(days=365)).isoformat()  # step 1 window

TODAY = date.today()


def catalog(rb: P21Runbook, args: argparse.Namespace, hdr_uid: int) -> None:
    """Step 1 (read-only): assemblies the customer ordered that the contract lacks."""
    on_contract = {
        r["inv_mast_uid"]
        for r in rb.odata(
            "job_price_line", f"job_price_hdr_uid eq {hdr_uid}", "inv_mast_uid"
        )
    }
    orders = rb.odata(
        "oe_hdr",
        f"customer_id eq {args.customer} and order_date ge {args.since}T00:00:00Z",
        "order_no",
        top=200,
    )
    seen: set[int] = set()
    for order in orders:
        for line in rb.odata(
            "oe_line",
            f"order_no eq '{order['order_no']}' and delete_flag eq 'N'",
            "inv_mast_uid",
        ):
            seen.add(line["inv_mast_uid"])
    gaps = []
    for uid in sorted(seen - on_contract):
        if rb.odata("assembly_hdr", f"inv_mast_uid eq {uid}", "inv_mast_uid"):
            gaps.append(
                rb.one("inv_mast", f"inv_mast_uid eq {uid}", "item_id")["item_id"]
            )
    print(
        f"    {len(orders)} order(s) since {args.since}; {len(seen)} item(s) ordered; "
        f"assemblies not on the contract: {gaps or 'none'}"
    )


def build_bom_payload(args: argparse.Namespace) -> dict:
    """Step 2: keyed Status "New" edits -- no IgnoreDisabled. Changes the item for EVERY customer."""
    rows = []
    for pair in args.component_qty:
        comp, qty = pair.split("=", 1)
        rows.append([edit("item_id_service_labor_id", comp), edit("quantity", qty)])
    for comp in args.remove_component:
        rows.append([edit("item_id_service_labor_id", comp), edit("delete_flag", "ON")])
    return payload(
        "Assembly",
        [
            element(
                "TABPAGE_1.assemblyhdr",
                "Form",
                ["inv_mast_item_id"],
                [[edit("inv_mast_item_id", args.item)]],
            ),
            element(
                "TABPAGE_17.tp_17_dw_17", "List", ["item_id_service_labor_id"], rows
            ),
        ],
    )


def build_vendor_payload(args: argparse.Namespace) -> dict:
    """Step 3: vendor ON, Track Rebates ON, terms by description, no currency, no supplier tab.

    id is left out -- P21 numbers the vendor from the address sequence and
    the save creates the same-ID supplier.
    """
    header = [
        edit("company_id", args.company),
        edit("vendor", "ON"),
        edit("name", args.vendor_name),
        *(edit(k, v) for k, v in VENDOR_ADDRESS.items()),
        edit("ap_account_no", args.ap_account),
        edit("default_terms_id", args.terms),
        edit("track_rebates", "ON"),
    ]
    return payload(
        "Vendor",
        [
            element("TABPAGE_1.tp_1_dw_1", "Form", ["company_id", "id"], [header]),
            element(
                "REBATE_ACCOUNTS.d_vendor_rebate_accounts",
                "Form",
                [],
                [
                    [
                        edit("rebate_account_no", args.rebate_account),
                        edit(
                            "rebate_allowance_account_no", args.rebate_allowance_account
                        ),
                    ]
                ],
            ),
        ],
    )


def build_supplier_payloads(
    args: argparse.Namespace, supplier_id: str
) -> tuple[dict, dict]:
    """Step 4: insert the location supplier row (both keys + IgnoreDisabled), then flip primary."""

    def item_payload(detail: dict, ignore: bool) -> dict:
        return payload(
            "Item",
            [
                element(
                    "TABPAGE_1.tp_1_dw_1",
                    "Form",
                    ["item_id"],
                    [[edit("item_id", args.item)]],
                ),
                element(
                    "TABPAGE_17.invloclist",
                    "List",
                    ["location_id"],
                    [[edit("location_id", args.ship_from)]],
                ),
                detail,
            ],
            ignore_disabled=ignore,
        )

    insert = item_payload(
        element(
            "SUPPLIER_X_LOCATION.supplier_x_location",
            "List",
            ["location_id", "supplier_id"],
            [[edit("location_id", args.ship_from), edit("supplier_id", supplier_id)]],
        ),
        True,
    )
    flip = item_payload(
        element(
            "SUPPLIER_X_LOCATION.supplier_x_location",
            "List",
            ["supplier_id"],
            [[edit("supplier_id", supplier_id), edit("primary_supplier", "ON")]],
        ),
        False,
    )
    return insert, flip


def build_contract_payload(args: argparse.Namespace) -> dict:
    """Step 5: ship-to on the grid; pricing_method BEFORE price; both costs type Value."""
    return payload(
        "JobContractPricing",
        [
            element(
                "FORM.d_dw_job_price_hdr",
                "Form",
                [],
                [
                    [
                        edit("company_id", args.company),
                        edit("contract_no", args.contract_no),
                        edit("job_no", args.job_no),
                    ]
                ],
            ),
            element(
                "CUSTOMER_SHIP_TO.customer_ship_to",
                "List",
                ["customer_id", "ship_to_id"],
                [
                    [
                        edit("customer_id", args.customer),
                        edit("ship_to_id", args.ship_to),
                    ]
                ],
            ),
            element(
                "JOBPRICELINE.jobpriceline",
                "List",
                ["item_id"],
                [
                    [
                        edit("item_id", args.item),
                        edit("uom", "EA"),
                        edit("pricing_method", "Price"),
                        edit("price", args.price),
                    ]
                ],
            ),
            element(
                "JOBPRICECOST.jobpricecost",
                "Form",
                ["item_id"],
                [
                    [
                        edit("item_id", args.item),
                        edit("commission_cost_type_cd", "Value"),
                        edit("commission_cost_value", args.true_cost),
                        edit("other_cost_type_cd", "Value"),
                        edit("other_cost_value", args.rebated_cost),
                    ]
                ],
            ),
        ],
        ignore_disabled=True,
    )


def main() -> None:
    """Entry point: dry run prints the payloads; --execute runs and verifies each step."""
    parser = argparse.ArgumentParser(
        description="Rebate-tracked assembly program (docs/recipes/rebate-assembly-program.md)"
    )
    for flag, default in (
        ("--company", COMPANY_ID),
        ("--customer", CUSTOMER_ID),
        ("--ship-to", SHIP_TO_ID),
        ("--contact", CONTACT_ID),
        ("--taker", TAKER),
        ("--job-no", JOB_NO),
        ("--contract-no", CONTRACT_NO),
        ("--ship-from", SHIP_FROM),
        ("--item", ITEM_ID),
        ("--vendor-name", VENDOR_NAME),
        ("--ap-account", AP_ACCOUNT),
        ("--rebate-account", REBATE_ACCOUNT),
        ("--rebate-allowance-account", REBATE_ALLOWANCE_ACCOUNT),
        ("--terms", TERMS),
        ("--price", PRICE),
        ("--true-cost", TRUE_COST),
        ("--rebated-cost", REBATED_COST),
        ("--since", SINCE),
    ):
        parser.add_argument(flag, default=default)
    parser.add_argument(
        "--component-qty",
        action="append",
        default=list(COMPONENT_QTY),
        help="Step 2: COMPONENT=QTY (repeatable)",
    )
    parser.add_argument(
        "--remove-component",
        action="append",
        default=list(REMOVE_COMPONENTS),
        help="Step 2: component to delete (repeatable)",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually run the steps (default: dry run)",
    )
    args = parser.parse_args()

    print("Runbook - Rebate-Tracked Assembly Program")
    print("=" * 60)
    if not args.execute:
        print(
            f"\nStep 1 (OData): {args.customer}'s orders since {args.since} -> ordered items with an "
            "assembly_hdr and no job_price_line on the contract."
        )
        if args.component_qty or args.remove_component:
            show("Step 2 Assembly payload", build_bom_payload(args))
        show("Step 3 Vendor payload", build_vendor_payload(args))
        insert, flip = build_supplier_payloads(args, "{vendor_id}")
        show("Step 4a supplier row insert", insert)
        show("Step 4b flip to primary", flip)
        show("Step 5 JobContractPricing payload", build_contract_payload(args))
        show(
            "Step 6 Order payload (unit_price left blank for the contract)",
            build_order_payload(
                args.customer,
                args.ship_to,
                args.contact,
                args.ship_from,
                args.ship_from,
                TODAY.isoformat(),
                (TODAY + timedelta(days=1)).isoformat(),
                "REBATE-TEST",
                args.taker,
                [(args.item, "1", None)],
            ),
        )
        print("\nRe-run with --execute to run it.")
        return

    rb = P21Runbook()
    item_uid = rb.item_uid(args.item)
    hdr = rb.one(
        "job_price_hdr",
        f"contract_no eq '{args.contract_no}' and job_no eq '{args.job_no}'",
        "job_price_hdr_uid,approved,end_date",
    )
    hdr_uid = hdr["job_price_hdr_uid"]

    print("\nStep 1 - Catalog what the customer buys (OData, read-only)")
    catalog(rb, args, hdr_uid)

    if args.component_qty or args.remove_component:
        print("\nStep 2 - Fix the BOM (Transaction Assembly)")
        rb.transaction(build_bom_payload(args), "Assembly edit")
        for row in rb.odata(
            "assembly_line",
            f"inv_mast_uid eq {item_uid}",
            "component_inv_mast_uid,quantity,unit_of_measure,delete_flag",
        ):
            comp = rb.one(
                "inv_mast",
                f"inv_mast_uid eq {row['component_inv_mast_uid']}",
                "item_id",
            )
            print(
                f"    {comp['item_id']}: quantity {row['quantity']:g} {row['unit_of_measure']} "
                f"delete_flag {row['delete_flag']}"
            )
            for pair in args.component_qty:
                name, qty = pair.split("=", 1)
                if name == comp["item_id"]:
                    check(f"{name} quantity", float(row["quantity"]), float(qty))
            if comp["item_id"] in args.remove_component:
                check(f"{comp['item_id']} delete_flag", row["delete_flag"], "Y")

    print("\nStep 3 - Create the rebate vendor (Transaction Vendor)")
    result = rb.transaction(build_vendor_payload(args), "Vendor")
    vendor_id = result_value(result, "TABPAGE_1.tp_1_dw_1", "id")
    vendor = rb.one(
        "vendor",
        f"vendor_id eq {vendor_id}",
        "vendor_id,track_rebates,rebate_account_no",
    )
    check("vendor.track_rebates", vendor["track_rebates"], "Y")
    link = rb.one(
        "vendor_supplier", f"vendor_id eq {vendor_id}", "supplier_id,primary_vendor"
    )
    print(
        f"    vendor {vendor_id}: same-ID supplier {link['supplier_id']} "
        f"(primary_vendor {link['primary_vendor']})"
    )
    supplier_id = str(link["supplier_id"])

    print(
        f"\nStep 4 - Primary supplier at ship-from location {args.ship_from} (Transaction Item)"
    )
    insert, flip = build_supplier_payloads(args, supplier_id)
    rb.transaction(insert, "Location supplier row")
    rb.transaction(flip, "Flip to primary")
    loc = rb.one(
        "inv_loc",
        f"inv_mast_uid eq {item_uid} and location_id eq {args.ship_from}",
        "primary_supplier_id,qty_on_hand,moving_average_cost",
    )
    check("inv_loc.primary_supplier_id", loc["primary_supplier_id"], int(supplier_id))

    print(
        "\nStep 5 - Price and cost the contract line (Transaction JobContractPricing)"
    )
    rb.transaction(build_contract_payload(args), "Contract line")
    line = rb.one(
        "job_price_line",
        f"job_price_hdr_uid eq {hdr_uid} and inv_mast_uid eq {item_uid}",
        "price,commission_cost_value,other_cost_value",
    )
    check("job_price_line.price", float(line["price"]), float(args.price))
    check(
        "job_price_line.other_cost_value",
        float(line["other_cost_value"]),
        float(args.rebated_cost),
    )
    rb.one(
        "job_price_customer_shipto",
        f"job_price_hdr_uid eq {hdr_uid} and customer_id eq "
        f"{args.customer} and ship_to_id eq {args.ship_to}",
        "customer_id",
    )

    print("\nStep 6 - Acceptance test: order, pick, ship, invoice")
    if float(loc["qty_on_hand"]) < 1:
        raise SystemExit(
            f"{args.item} has no stock at {args.ship_from} -- build or receive one first"
        )
    tag = f"REBATE-TEST-{vendor_id}"
    result = rb.transaction(
        build_order_payload(
            args.customer,
            args.ship_to,
            args.contact,
            args.ship_from,
            args.ship_from,
            TODAY.isoformat(),
            (TODAY + timedelta(days=1)).isoformat(),
            tag,
            args.taker,
            [(args.item, "1", None)],
        ),
        "Order",
    )  # unit_price blank: the contract binds
    order_no = result_value(result, "TABPAGE_1.order", "order_no")
    ol = rb.one(
        "oe_line",
        f"order_no eq '{order_no}' and inv_mast_uid eq {item_uid}",
        "line_no,job_price_hdr_uid,unit_price,other_cost,supplier_id,assembly",
    )
    print(
        f"    order {order_no} line {ol['line_no']}: assembly {ol['assembly']} supplier "
        f"{ol['supplier_id']} other_cost {ol['other_cost']}"
    )
    check(
        "oe_line.job_price_hdr_uid (bound at entry)", ol["job_price_hdr_uid"], hdr_uid
    )
    check("oe_line.supplier_id", ol["supplier_id"], int(supplier_id))
    invoice_no = ship_and_invoice(rb, print_pick_ticket(rb, order_no))

    print("\nVerify - the invoice and the rebate")
    lines = print_invoice(rb, invoice_no)
    parent = next(
        x
        for x in lines
        if x["item_id"] == args.item and x["invoice_line_uid_parent"] == 0
    )
    check(
        "invoice_line.unit_price = contract price",
        float(parent["unit_price"]),
        float(args.price),
    )
    check(
        "invoice_line.cogs_amount = contract other cost",
        float(parent["cogs_amount"]),
        float(args.rebated_cost),
    )
    rebate = rb.one(
        "vendor_rebate",
        f"invoice_no eq '{invoice_no}' and "
        f"invoice_line_uid eq {parent['invoice_line_uid']}",
        "vendor_id,base_cost,after_rebate_cost,rebate_due",
    )
    print(
        f"    vendor_rebate: base_cost {rebate['base_cost']} after_rebate_cost "
        f"{rebate['after_rebate_cost']} rebate_due {rebate['rebate_due']}"
    )
    check("vendor_rebate.vendor_id", rebate["vendor_id"], int(vendor_id))
    check(
        "vendor_rebate.after_rebate_cost",
        float(rebate["after_rebate_cost"]),
        float(args.rebated_cost),
    )
    print(
        "\nRead the invoice's GL by hand: Sales Journal COGS at moving average, then a "
        "Rebate Journal entry for the difference."
    )
    print("\nRunbook complete.")


if __name__ == "__main__":
    main()
