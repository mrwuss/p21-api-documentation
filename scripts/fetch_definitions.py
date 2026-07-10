"""Fetch and sanitize P21 Transaction API service definitions.

Downloads ``GET {ui_server}/api/v2/definition/{Service}`` for a list of
services and writes one sanitized JSON per service to ``definitions/``,
plus a ``_manifest.json`` recording what was fetched and what failed.

Why sanitize
------------
Raw definitions embed **instance data**, not just schema:

* ``ValidValues`` for lookup-backed dropdowns are pulled live from the
  environment's tables (carriers, payment terms, EDI maps, class codes --
  which can contain customer and employee names).
* ``ufc_*`` fields are the environment's user-defined columns.

This script therefore:

1. Drops any field whose name starts with ``ufc_`` (user-defined schema),
   from both ``FieldDefinitions`` and the ``Template`` payload skeleton.
2. Keeps ``ValidValues`` only when the list is boolean-style
   (subset of ON/OFF/Y/N/Yes/No/blank) or the field name is on a reviewed
   allowlist of standard P21 enums. Everything else is emptied and marked
   ``"ValidValuesRedacted": true`` -- run this script against your own
   environment to see the full lists.
3. Optionally refuses to write a file containing any term from the
   ``P21_SCRUB_TERMS`` environment variable (comma-separated,
   case-insensitive) -- set it to your company identifiers before
   publishing fetched definitions.

Usage
-----
    python scripts/fetch_definitions.py                 # documented services
    python scripts/fetch_definitions.py --services Order,Item
    python scripts/fetch_definitions.py --all           # every listed service
    python scripts/fetch_definitions.py --no-sanitize   # local use only!
"""

import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).parent))
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from common.config import load_config  # noqa: E402
from common.auth import get_token  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = REPO_ROOT / "definitions"

# Services documented in docs/ -- the default fetch set.
DOCUMENTED_SERVICES = [
    "Assembly",
    "BinLocation",
    "Customer",
    "InventoryAdjustment",
    "Item",
    "JobContractPricing",
    "Labor",
    "LaborProcess",
    "Order",
    "ProductionOrder",
    "ProductionOrderPicking",
    "ProductionOrderProcessing",
    "PurchaseOrder",
    "SalesPricePage",
    "Shipping",
    "Supplier",
    "TimeEntry",
    # Report services (hidden from /api/v2/services but callable)
    "m_picktickets",
    "m_reprintpicktickets",
    "m_reprintpurchaseorders",
    "m_storedprocedureexecutor",
]

# Boolean-style lists are always safe to keep.
BOOLEAN_VALUES = {"", " ", "ON", "OFF", "Y", "N", "Yes", "No"}

# Field names whose ValidValues were manually reviewed (25.2) and contain
# only standard P21 enum labels -- safe to publish. Anything not listed
# here (and not boolean-style) gets redacted. Deny by default.
VALIDVALUES_ALLOWLIST = {
    "action_number", "age_by", "allow_disassembly", "assignment_option",
    "assembly_usage_accumulation", "auto_update_prices_source_flag",
    "billing_type_cd", "bssheet_price_display_option", "burdened_cost_type_id",
    "c_disposition", "c_shipping_action", "calculation_method",
    "calculation_method_cd", "calculator_type", "cc_include_rfq",
    "child_uom_code_no", "combine_stock_ns_special_cd",
    "commission_cost_calc_method_cd",
    "commission_cost_type_cd", "contact_type_cd", "contract_category",
    "contract_type_cd", "control_value", "country_subdivision_uid",
    "create_po_from_oe", "create_vendor_rfq_cd", "customer_default_disposition",
    "customer_sensitivity_cd", "customer_type_cd", "dea_schedule",
    "default_disposition", "default_shipment", "demand_pattern_behavior_cd",
    "demand_pattern_cd", "dflt_dimension_scale", "display_area_cd",
    "display_end_date", "disposition", "expedite_type", "filter_by",
    "freight_charge_option_cd", "generate_statements_by", "gpo_type_cd",
    "gpt_picking_status", "include_non_alloc_on_pack_list", "include_pm",
    "invoice_comp_cost_cd_tier1", "invoice_comp_cost_cd_tier2",
    "invoice_comp_cost_cd_tier3", "invoice_type", "item_type", "item_type_cd",
    "labor_type_cd", "lead_time_source", "link_area", "list_price_option_cd",
    "mode_of_transport_cd", "ndc_type_cd", "open_item_balance_forward",
    "order_disc_type", "order_type", "other_cost_calc_method_cd",
    "other_cost_type_cd", "override_vmi_status",
    "pack_by", "packing_basis", "packing_weight_tracking_option",
    "payable_to", "payment_acct_type_cd", "pm_status", "po_default_method",
    "po_hdr_po_type", "pocosting_method", "price_page_type_cd",
    "pricing_method", "pricing_method_cd", "pricing_option",
    "pricing_service_option", "processed_flag", "product_type",
    "prorate_cost_by", "quote_price_disposition", "quote_type",
    "release_status_flag", "release_type", "rental_billing_flag",
    "rep_method_cd", "rep_source_cd", "replen_method",
    "replenishment_method_cd", "require_lot_documentation_flag", "responded",
    "retail_size_cd", "round", "round_type", "routing_status_flag",
    "row_status", "row_status_flag", "safety_stock_type", "salutation",
    "scheduling_type_cd", "secondary_rebate_calc_meth_cd",
    "serialized", "service_level_measure",
    "source_area_cd", "source_type",
    "strategic_price_applies_to_cd", "supplementary_value", "tcost",
    "tag_usage_specificity_cd", "terms_of_delivery_cd", "third_party_billing_flag",
    "totaling_method_cd", "trans_type",
    "validation_status", "xmit_invoice_cd",
}
# Deliberately NOT allowlisted despite looking standard: the price-source
# dropdowns (commission_cost_source_cd, other_cost_source_cd,
# secondary_rebate_source_cd, source_price_cd, totaling_basis_cd) are
# lookup-backed and can carry custom environment entries alongside the
# standard Price 1-10 / Strategic values -- verified leak on a live system.


def get_ui_server(cfg, token: str, client: httpx.Client) -> str:
    """Resolve the UI server URL via the router endpoint."""
    resp = client.get(
        f"{cfg.base_url}/api/ui/router/v1/?urlType=external",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )
    resp.raise_for_status()
    try:
        return resp.json()["Url"].rstrip("/")
    except (ValueError, KeyError):
        match = re.search(r"<Url>([^<]+)</Url>", resp.text, re.IGNORECASE)
        if not match:
            raise RuntimeError(f"No Url in router response: {resp.text[:200]}")
        return match.group(1).rstrip("/")


def sanitize_field(field: dict) -> dict | None:
    """Sanitize one FieldDefinition. Returns None if the field must be dropped."""
    name = field.get("Name") or ""
    if name.startswith("ufc_"):
        return None
    valid_values = field.get("ValidValues") or []
    if valid_values:
        keep = set(valid_values) <= BOOLEAN_VALUES or name in VALIDVALUES_ALLOWLIST
        if not keep:
            field = dict(field)
            field["ValidValues"] = []
            field["ValidValuesRedacted"] = True
    return field


def sanitize_definition(definition: dict) -> dict:
    """Apply the sanitization rules to a full definition document."""
    txn_def = definition.get("TransactionDefinition") or {}
    for element in txn_def.get("DataElementDefinitions") or []:
        fields = element.get("FieldDefinitions") or []
        element["FieldDefinitions"] = [
            f for f in (sanitize_field(dict(fd)) for fd in fields) if f is not None
        ]

    template = definition.get("Template") or {}
    for txn_set in template.get("TransactionSet", {}).get("Transactions", []) or []:
        for element in txn_set.get("DataElements") or []:
            for row in element.get("Rows") or []:
                edits = row.get("Edits") or []
                row["Edits"] = [
                    e for e in edits if not (e.get("Name") or "").startswith("ufc_")
                ]
    return definition


def scrub_check(text: str, terms: list[str]) -> list[str]:
    """Return the scrub terms found in text (case-insensitive)."""
    lowered = text.lower()
    return [t for t in terms if t and t.lower() in lowered]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--services", help="Comma-separated service names")
    parser.add_argument("--all", action="store_true",
                        help="Fetch every service listed by /api/v2/services")
    parser.add_argument("--no-sanitize", action="store_true",
                        help="Skip sanitization (LOCAL USE ONLY -- never commit raw output)")
    parser.add_argument("--out", default=str(OUTPUT_DIR), help="Output directory")
    args = parser.parse_args()

    cfg = load_config()
    token = get_token(cfg)["AccessToken"]
    client = httpx.Client(verify=cfg.verify_ssl, timeout=120, follow_redirects=True)
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    ui_server = get_ui_server(cfg, token, client)
    print(f"UI server: {ui_server}")

    if args.services:
        services = [s.strip() for s in args.services.split(",") if s.strip()]
    elif args.all:
        resp = client.get(f"{ui_server}/api/v2/services", headers=headers)
        resp.raise_for_status()
        listed = resp.json()
        services = sorted(
            s if isinstance(s, str) else s.get("Name")
            for s in (listed if isinstance(listed, list) else listed.get("Services", []))
        )
    else:
        services = DOCUMENTED_SERVICES

    scrub_terms = [t.strip() for t in os.environ.get("P21_SCRUB_TERMS", "").split(",") if t.strip()]
    if not scrub_terms and not args.no_sanitize:
        print("NOTE: P21_SCRUB_TERMS is not set -- no company-term gate will run. "
              "Set it (comma-separated) before publishing fetched output.")

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = {"fetched_date": date.today().isoformat(), "sanitized": not args.no_sanitize,
                "ok": [], "skipped": {}}

    for name in services:
        resp = client.get(f"{ui_server}/api/v2/definition/{name}", headers=headers)
        if resp.status_code != 200:
            reason = resp.text[:200]
            manifest["skipped"][name] = f"HTTP {resp.status_code}: {reason}"
            print(f"  SKIP {name}: HTTP {resp.status_code}")
            continue
        definition = resp.json()
        if not args.no_sanitize:
            definition = sanitize_definition(definition)
        text = json.dumps(definition, indent=1, sort_keys=True)
        found = scrub_check(text, scrub_terms)
        if found:
            manifest["skipped"][name] = f"scrub terms present after sanitize: {found}"
            print(f"  BLOCKED {name}: scrub terms {found} still present -- not written")
            continue
        safe_name = re.sub(r"[^A-Za-z0-9_]", "_", name)
        (out_dir / f"{safe_name}.json").write_text(text + "\n", encoding="utf-8")
        manifest["ok"].append(name)
        print(f"  OK   {name} ({len(text) // 1024} KB)")

    (out_dir / "_manifest.json").write_text(
        json.dumps(manifest, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"\nWrote {len(manifest['ok'])} definitions to {out_dir} "
          f"({len(manifest['skipped'])} skipped). Manifest: _manifest.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
