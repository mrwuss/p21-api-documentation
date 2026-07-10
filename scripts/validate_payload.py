"""Offline P21 Transaction API payload validator.

Checks a payload file (JSON or XML) for the shape mistakes that cause the
most integration failures -- a string where an array is expected, fields at
the wrong nesting level, booleans sent as strings, unknown field/element
names -- and validates names against the committed schema library in
``definitions/`` when available.

No network access; safe to run anywhere. Exit code 1 when errors are found
(warnings alone exit 0), so it can gate scripts or CI.

Usage:
    python scripts/validate_payload.py payload.json
    python scripts/validate_payload.py payload.xml
    python scripts/validate_payload.py payload.json --definitions definitions/
    python scripts/validate_payload.py --self-test
"""

import argparse
import difflib
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DEFINITIONS = REPO_ROOT / "definitions"

V2_NS = "http://schemas.datacontract.org/2004/07/P21.Transactions.Model.V2"
ARRAYS_NS = "http://schemas.microsoft.com/2003/10/Serialization/Arrays"

KNOWN_ROOT_KEYS = {"Name", "UseCodeValues", "IgnoreDisabled", "Transactions",
                   "Query", "FieldMap", "TransactionSplitMethod", "Parameters",
                   "Description"}
KNOWN_TXN_KEYS = {"Status", "DataElements", "Documents"}
KNOWN_ELEMENT_KEYS = {"Name", "Type", "Keys", "Rows", "BusinessObjectName"}
KNOWN_ROW_KEYS = {"Edits", "RelativeDateEdits"}
KNOWN_EDIT_KEYS = {"Name", "Value", "IgnoreIfEmpty"}

# DataContract (alphabetical) child order per complex type -- XML bodies must
# follow it; out-of-order elements are dropped by the deserializer.
XML_ORDER = {
    "TransactionSet": ["Description", "FieldMap", "IgnoreDisabled", "Name",
                       "Parameters", "Query", "TransactionSplitMethod",
                       "Transactions", "UseCodeValues"],
    "Transaction": ["DataElements", "Documents", "Status"],
    "DataElement": ["BusinessObjectName", "Keys", "Name", "Rows", "Type"],
    "Row": ["Edits", "RelativeDateEdits"],
    "Edit": ["IgnoreIfEmpty", "Name", "Value"],
}

# Verified field-order rules: (service, element-suffix, must-precede pairs)
FIELD_ORDER_RULES = [
    ("JobContractPricing", "jobpriceline", "pricing_method", "price",
     "changing pricing_method clears the typed price -- a line sent price-first "
     "lands at $0 while still reporting Succeeded"),
]


class Report:
    """Collects findings and renders them."""

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.notes: list[str] = []

    def error(self, path: str, msg: str) -> None:
        self.errors.append(f"ERROR  {path}: {msg}")

    def warn(self, path: str, msg: str) -> None:
        self.warnings.append(f"WARN   {path}: {msg}")

    def note(self, path: str, msg: str) -> None:
        self.notes.append(f"NOTE   {path}: {msg}")

    def dump(self) -> int:
        for line in self.errors + self.warnings + self.notes:
            print(line)
        print(f"\n{len(self.errors)} error(s), {len(self.warnings)} warning(s), "
              f"{len(self.notes)} note(s)")
        return 1 if self.errors else 0


def load_definition(name: str, definitions_dir: Path, rpt: Report) -> dict | None:
    """Load definitions/{name}.json if present; None (with a note) otherwise."""
    if not name:
        return None
    path = definitions_dir / f"{name}.json"
    if not path.exists():
        rpt.note("Name", f"no schema at {path} -- element/field names not checked "
                         f"(fetch with scripts/fetch_definitions.py --services {name})")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        rpt.warn("Name", f"could not read schema {path}: {exc}")
        return None


def element_map(definition: dict | None) -> dict[str, dict]:
    """Map DataElement Name -> its definition entry."""
    if not definition:
        return {}
    elements = (definition.get("TransactionDefinition") or {}).get(
        "DataElementDefinitions") or []
    return {e.get("Name"): e for e in elements if e.get("Name")}


def suggest(name: str, candidates: list[str]) -> str:
    """Render a did-you-mean suffix for an unknown name."""
    close = difflib.get_close_matches(name, candidates, n=2, cutoff=0.6)
    return f" (did you mean: {', '.join(close)}?)" if close else ""


def expect_list(value, path: str, what: str, rpt: Report) -> bool:
    """Assert value is a list; classify the common wrong shapes."""
    if isinstance(value, list):
        return True
    if isinstance(value, str):
        rpt.error(path, f"{what} must be an ARRAY, got a string -- "
                        f'write ["{value}"] instead of "{value}"')
    elif isinstance(value, dict):
        rpt.error(path, f"{what} must be an ARRAY of objects, got a single "
                        f"object -- wrap it in [ ... ]")
    else:
        rpt.error(path, f"{what} must be an array, got {type(value).__name__}")
    return False


def expect_bool(value, path: str, what: str, rpt: Report) -> None:
    """Assert value is a real boolean, not the string 'true'/'false'."""
    if isinstance(value, bool) or value is None:
        return
    if isinstance(value, str):
        rpt.error(path, f'{what} must be a JSON boolean (true/false), got the '
                        f'STRING "{value}" -- remove the quotes')
    else:
        rpt.warn(path, f"{what} should be a boolean, got {type(value).__name__}")


def check_edit(edit, path: str, fields: dict[str, dict], rpt: Report) -> str | None:
    """Validate one Edit object; returns the field name if identifiable."""
    if not isinstance(edit, dict):
        rpt.error(path, f'each Edit must be an object like '
                        f'{{"Name": "field", "Value": "..."}}, got '
                        f"{type(edit).__name__}")
        return None
    name = edit.get("Name")
    if not isinstance(name, str) or not name:
        rpt.error(path, 'Edit is missing "Name" (string)')
        name = None
    if "Value" not in edit:
        rpt.error(path, 'Edit is missing "Value"')
    else:
        value = edit["Value"]
        if value is not None and not isinstance(value, str):
            rpt.warn(path, f"Value is a {type(value).__name__} "
                           f"({value!r}) -- every verified example sends Values "
                           f'as STRINGS (e.g. "{value}"); numbers/booleans are '
                           f"not a documented, tested form")
    for key in edit:
        if key not in KNOWN_EDIT_KEYS:
            rpt.warn(f"{path}.{key}", f"unknown Edit property"
                                      f"{suggest(key, sorted(KNOWN_EDIT_KEYS))}")
    if name and fields and name not in fields:
        rpt.warn(path, f'field "{name}" is not in the schema for this element'
                       f"{suggest(name, list(fields))} -- note: committed "
                       f"definitions omit environment-specific ufc_* fields")
    return name


def check_field_order(service: str, element_name: str, edit_names: list[str],
                      path: str, rpt: Report) -> None:
    """Apply verified must-precede field-order rules."""
    for svc, elem_suffix, first, second, why in FIELD_ORDER_RULES:
        if service == svc and element_name.lower().endswith(elem_suffix):
            if first in edit_names and second in edit_names:
                if edit_names.index(first) > edit_names.index(second):
                    rpt.error(path, f'"{first}" must come BEFORE "{second}" '
                                    f"in the Edits: {why}")


def check_data_element(element, path: str, service: str,
                       elements: dict[str, dict], rpt: Report) -> None:
    """Validate one DataElement."""
    if not isinstance(element, dict):
        rpt.error(path, f"each DataElement must be an object, got "
                        f"{type(element).__name__}")
        return
    if "IgnoreDisabled" in element:
        rpt.error(f"{path}.IgnoreDisabled",
                  "IgnoreDisabled belongs at the PAYLOAD TOP LEVEL (next to "
                  "Name/Transactions); anywhere else it is silently ignored")
    name = element.get("Name")
    fields: dict[str, dict] = {}
    if not isinstance(name, str) or not name:
        rpt.error(path, 'DataElement is missing "Name" (e.g. "FORM.form")')
        name = ""
    elif elements:
        if name not in elements:
            rpt.error(f"{path}.Name", f'unknown DataElement "{name}" for service '
                                      f'"{service}"{suggest(name, list(elements))}')
        else:
            defn = elements[name]
            fields = {f.get("Name"): f for f in defn.get("FieldDefinitions") or []
                      if f.get("Name")}
            expected_type = defn.get("Type")
            actual_type = element.get("Type")
            if (isinstance(actual_type, str) and isinstance(expected_type, str)
                    and expected_type in ("Form", "List")
                    and actual_type != expected_type):
                rpt.warn(f"{path}.Type", f'schema says this element is '
                                         f'"{expected_type}", payload says '
                                         f'"{actual_type}"')

    keys = element.get("Keys")
    if keys is not None and expect_list(keys, f"{path}.Keys", "Keys", rpt):
        for i, key in enumerate(keys):
            if not isinstance(key, str):
                rpt.error(f"{path}.Keys[{i}]", f"key names must be strings, got "
                                               f"{type(key).__name__}")
            elif fields and key not in fields:
                rpt.warn(f"{path}.Keys[{i}]", f'key "{key}" is not a field of '
                                              f"this element{suggest(key, list(fields))}")

    rows = element.get("Rows")
    if rows is None:
        rpt.warn(path, 'DataElement has no "Rows"')
    elif expect_list(rows, f"{path}.Rows", "Rows", rpt):
        for r_i, row in enumerate(rows):
            r_path = f"{path}.Rows[{r_i}]"
            if not isinstance(row, dict):
                rpt.error(r_path, f'each Row must be an object like '
                                  f'{{"Edits": [...]}}, got {type(row).__name__}')
                continue
            edits = row.get("Edits")
            if edits is None:
                rpt.warn(r_path, 'Row has no "Edits"')
                continue
            if expect_list(edits, f"{r_path}.Edits", "Edits", rpt):
                edit_names = []
                for e_i, edit in enumerate(edits):
                    field = check_edit(edit, f"{r_path}.Edits[{e_i}]", fields, rpt)
                    if field:
                        edit_names.append(field)
                check_field_order(service, name, edit_names, f"{r_path}.Edits", rpt)
            rde = row.get("RelativeDateEdits")
            if rde is not None:
                expect_list(rde, f"{r_path}.RelativeDateEdits",
                            "RelativeDateEdits", rpt)

    for key in element:
        if key not in KNOWN_ELEMENT_KEYS | {"IgnoreDisabled"}:
            rpt.warn(f"{path}.{key}", f"unknown DataElement property"
                                      f"{suggest(key, sorted(KNOWN_ELEMENT_KEYS))}")


def check_transaction(txn, path: str, service: str, elements: dict[str, dict],
                      rpt: Report) -> None:
    """Validate one Transaction."""
    if not isinstance(txn, dict):
        rpt.error(path, f"each Transaction must be an object, got "
                        f"{type(txn).__name__}")
        return
    if "IgnoreDisabled" in txn:
        rpt.error(f"{path}.IgnoreDisabled",
                  "IgnoreDisabled belongs at the PAYLOAD TOP LEVEL (next to "
                  "Name/Transactions); inside a Transaction it is SILENTLY "
                  "ignored and disabled-column errors persist")
    status = txn.get("Status")
    if status is None:
        rpt.warn(path, 'Transaction has no "Status" -- record edits use "New"')
    elif isinstance(status, str):
        if status in ("Existing", "Update", "Change"):
            rpt.error(f"{path}.Status",
                      f'"{status}" is broken platform-wide (HTTP 500 '
                      f'NullReferenceException). Use "New" for BOTH create and '
                      f"update -- keyed rows upsert")
        elif status != "New" and service and not service.startswith("m_"):
            rpt.warn(f"{path}.Status", f'unusual Status "{status}" -- record '
                                       f'edits use "New"')
    elif isinstance(status, int):
        rpt.note(f"{path}.Status",
                 "numeric Status is the report-process shape -- report (m_*) "
                 "payloads go to POST /api/v2/process/pdfreport, NOT "
                 "/api/v2/transaction (which accepts them and emits nothing)")
    data_elements = txn.get("DataElements")
    if data_elements is None:
        rpt.error(path, 'Transaction has no "DataElements"')
    elif expect_list(data_elements, f"{path}.DataElements", "DataElements", rpt):
        for i, element in enumerate(data_elements):
            check_data_element(element, f"{path}.DataElements[{i}]",
                               service, elements, rpt)
    for key in txn:
        if key not in KNOWN_TXN_KEYS | {"IgnoreDisabled"}:
            rpt.warn(f"{path}.{key}", f"unknown Transaction property"
                                      f"{suggest(key, sorted(KNOWN_TXN_KEYS))}")


def validate_get_request(payload: dict, definitions_dir: Path, rpt: Report) -> None:
    """Validate a POST /api/v2/transaction/get request body."""
    service = payload.get("ServiceName")
    if not isinstance(service, str) or not service:
        rpt.error("$.ServiceName", "missing service name")
        service = ""
    elements = element_map(load_definition(service, definitions_dir, rpt))
    states = payload.get("TransactionStates")
    if states is None:
        rpt.error("$", 'missing "TransactionStates" array')
        return
    if not expect_list(states, "$.TransactionStates", "TransactionStates", rpt):
        return
    for i, state in enumerate(states):
        path = f"$.TransactionStates[{i}]"
        if not isinstance(state, dict):
            rpt.error(path, f"each TransactionState must be an object, got "
                            f"{type(state).__name__}")
            continue
        name = state.get("DataElementName")
        if not isinstance(name, str) or not name:
            rpt.error(path, 'missing "DataElementName"')
        elif elements and name not in elements:
            rpt.error(f"{path}.DataElementName",
                      f'unknown DataElement "{name}"{suggest(name, list(elements))}')
        keys = state.get("Keys")
        if keys is not None and expect_list(keys, f"{path}.Keys", "Keys", rpt):
            for k_i, key in enumerate(keys):
                if not (isinstance(key, dict) and "Name" in key and "Value" in key):
                    rpt.error(f"{path}.Keys[{k_i}]",
                              'get-request keys are objects: '
                              '{"Name": "field", "Value": "..."} '
                              '(unlike TransactionSet Keys, which are strings)')
    rpt.note("$", "transaction/get request — POST to /api/v2/transaction/get")


def validate_payload_dict(payload: dict, definitions_dir: Path, rpt: Report) -> None:
    """Validate a parsed TransactionSet payload."""
    if not isinstance(payload, dict):
        rpt.error("$", f"payload root must be an object, got "
                       f"{type(payload).__name__}")
        return
    if "ServiceName" in payload or "TransactionStates" in payload:
        validate_get_request(payload, definitions_dir, rpt)
        return
    service = payload.get("Name")
    if not isinstance(service, str) or not service:
        rpt.error("$.Name", 'missing service name (e.g. "Order")')
        service = ""
    definition = load_definition(service, definitions_dir, rpt)
    elements = element_map(definition)

    expect_bool(payload.get("UseCodeValues"), "$.UseCodeValues", "UseCodeValues", rpt)
    expect_bool(payload.get("IgnoreDisabled"), "$.IgnoreDisabled", "IgnoreDisabled", rpt)

    transactions = payload.get("Transactions")
    if transactions is None:
        rpt.error("$", 'missing "Transactions" array')
    elif expect_list(transactions, "$.Transactions", "Transactions", rpt):
        for i, txn in enumerate(transactions):
            check_transaction(txn, f"$.Transactions[{i}]", service, elements, rpt)

    for key in payload:
        if key not in KNOWN_ROOT_KEYS:
            rpt.warn(f"$.{key}", f"unknown top-level property"
                                 f"{suggest(key, sorted(KNOWN_ROOT_KEYS))} -- "
                                 f"property names are case-sensitive")


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _check_xml_order(node: ET.Element, type_name: str, path: str, rpt: Report) -> None:
    """Enforce DataContract child ordering for a known complex type."""
    order = XML_ORDER.get(type_name)
    if not order:
        return
    last_index = -1
    for child in node:
        name = _local(child.tag)
        if name not in order:
            rpt.warn(f"{path}/{name}", f"unexpected element in <{type_name}>"
                                       f"{suggest(name, order)}")
            continue
        index = order.index(name)
        if index < last_index:
            rpt.error(f"{path}/{name}",
                      f"out of order in <{type_name}> -- DataContract XML "
                      f"requires ALPHABETICAL element order "
                      f"({' < '.join(order)}). Out-of-order elements are "
                      f"dropped by the deserializer (top-level: HTTP 500; "
                      f"inside an Edit: silent drop, then a NullReference "
                      f"transaction failure)")
        last_index = max(last_index, index)


def _iter_local(node: ET.Element, name: str):
    """Iterate descendants whose local tag name matches, namespace-agnostic."""
    for child in node.iter():
        if _local(child.tag) == name:
            yield child


def xml_to_payload(root: ET.Element, rpt: Report, has_ns: bool) -> dict:
    """Convert a TransactionSet XML element to the JSON-shaped dict.

    Traversal matches on local names so that documents missing the namespace
    (already flagged as an error) still get the full set of findings.
    """
    def text_of(node, name):
        for child in node:
            if _local(child.tag) == name:
                return child.text or ""
        return None

    def to_bool(value):
        return None if value is None else value.strip().lower() == "true"

    _check_xml_order(root, "TransactionSet", "/TransactionSet", rpt)
    payload: dict = {"Name": text_of(root, "Name")}
    if (ucv := text_of(root, "UseCodeValues")) is not None:
        payload["UseCodeValues"] = to_bool(ucv)
    if (igd := text_of(root, "IgnoreDisabled")) is not None:
        payload["IgnoreDisabled"] = to_bool(igd)

    payload["Transactions"] = []
    for t_i, txn_node in enumerate(_iter_local(root, "Transaction")):
        _check_xml_order(txn_node, "Transaction", f"/Transactions[{t_i}]", rpt)
        txn: dict = {"Status": text_of(txn_node, "Status"), "DataElements": []}
        for d_i, de_node in enumerate(_iter_local(txn_node, "DataElement")):
            de_path = f"/Transactions[{t_i}]/DataElements[{d_i}]"
            _check_xml_order(de_node, "DataElement", de_path, rpt)
            element: dict = {"Name": text_of(de_node, "Name"),
                             "Type": text_of(de_node, "Type"), "Keys": [], "Rows": []}
            keys_node = next((c for c in de_node if _local(c.tag) == "Keys"), None)
            if keys_node is not None:
                for key_child in keys_node:
                    if has_ns and key_child.tag != f"{{{ARRAYS_NS}}}string":
                        rpt.error(f"{de_path}/Keys",
                                  f"Keys items must be <string> in the arrays "
                                  f'namespace ({ARRAYS_NS}), got '
                                  f"<{_local(key_child.tag)}>")
                    element["Keys"].append(key_child.text or "")
            for r_i, row_node in enumerate(_iter_local(de_node, "Row")):
                r_path = f"{de_path}/Rows[{r_i}]"
                _check_xml_order(row_node, "Row", r_path, rpt)
                row: dict = {"Edits": []}
                for e_i, edit_node in enumerate(_iter_local(row_node, "Edit")):
                    _check_xml_order(edit_node, "Edit", f"{r_path}/Edits[{e_i}]", rpt)
                    row["Edits"].append({"Name": text_of(edit_node, "Name"),
                                         "Value": text_of(edit_node, "Value")})
                element["Rows"].append(row)
            txn["DataElements"].append(element)
        payload["Transactions"].append(txn)
    return payload


def validate_xml(text: str, definitions_dir: Path, rpt: Report) -> None:
    """Validate an XML TransactionSet payload."""
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        rpt.error("$", f"XML parse error: {exc}")
        return
    local = _local(root.tag)
    ns = root.tag[1:].rsplit("}", 1)[0] if root.tag.startswith("{") else ""
    if local == "TransactionStateRequest":
        rpt.note("/", "transaction/get request detected -- structural checks "
                      "only apply to <TransactionSet> bodies")
    elif local != "TransactionSet":
        rpt.error("/", f"root must be <TransactionSet> (or "
                       f"<TransactionStateRequest> for /transaction/get), got "
                       f"<{local}>")
    if ns != V2_NS:
        rpt.error("/", f'root is missing the DataContract namespace -- without '
                       f'xmlns="{V2_NS}" the body deserializes to null and the '
                       f'server returns 400 "The content field is required."')
    if local == "TransactionSet":
        payload = xml_to_payload(root, rpt, has_ns=(ns == V2_NS))
        validate_payload_dict(payload, definitions_dir, rpt)


def self_test() -> int:
    """Run the validator against built-in good/bad payloads."""
    good = {"Name": "JobContractPricing", "UseCodeValues": False,
            "Transactions": [{"Status": "New", "DataElements": [
                {"Name": "FORM.d_dw_job_price_hdr", "Type": "Form", "Keys": [],
                 "Rows": [{"Edits": [
                     {"Name": "contract_no", "Value": "A120-12"},
                     {"Name": "end_date", "Value": "2030-01-01"}]}]},
                {"Name": "JOBPRICELINE.jobpriceline", "Type": "List",
                 "Keys": ["item_id"],
                 "Rows": [{"Edits": [
                     {"Name": "item_id", "Value": "WIDGET-001"},
                     {"Name": "pricing_method", "Value": "Price"},
                     {"Name": "price", "Value": "36.58"}]}]}]}]}
    bad = {"Name": "JobContractPricing", "UseCodeValues": "false",
           "Transactions": [{
               "Status": "Existing",
               "IgnoreDisabled": True,
               "DataElements": [
                   {"Name": "JOBPRICELINE.jobpriceline", "Type": "List",
                    "Keys": "item_id",
                    "Rows": [{"Edits": [
                        {"Name": "item_id", "Value": "WIDGET-001"},
                        {"Name": "price", "Value": 36.58},
                        {"Name": "pricing_method", "Value": "Price"}]}]}]}]}
    print("--- self-test: GOOD payload (expect 0 errors) ---")
    rpt = Report()
    validate_payload_dict(good, DEFAULT_DEFINITIONS, rpt)
    good_rc = rpt.dump()
    print("\n--- self-test: BAD payload (expect errors: string UseCodeValues, "
          "Existing status, misplaced IgnoreDisabled, Keys string, "
          "field order) ---")
    rpt = Report()
    validate_payload_dict(bad, DEFAULT_DEFINITIONS, rpt)
    bad_rc = rpt.dump()
    ok = good_rc == 0 and bad_rc == 1
    print(f"\nself-test {'PASSED' if ok else 'FAILED'}")
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("payload", nargs="?", help="Payload file (.json or .xml)")
    parser.add_argument("--definitions", default=str(DEFAULT_DEFINITIONS),
                        help="Directory of definition JSONs (default: definitions/)")
    parser.add_argument("--self-test", action="store_true",
                        help="Validate built-in good/bad payloads and exit")
    args = parser.parse_args()

    if args.self_test:
        return self_test()
    if not args.payload:
        parser.error("payload file required (or --self-test)")

    path = Path(args.payload)
    if not path.exists():
        print(f"File not found: {path}")
        return 1
    text = path.read_text(encoding="utf-8-sig")
    definitions_dir = Path(args.definitions)
    rpt = Report()

    stripped = text.lstrip()
    if stripped.startswith("<"):
        validate_xml(text, definitions_dir, rpt)
    else:
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            rpt.error("$", f"JSON parse error at line {exc.lineno}, column "
                           f"{exc.colno}: {exc.msg}")
            return rpt.dump()
        validate_payload_dict(payload, definitions_dir, rpt)
    return rpt.dump()


if __name__ == "__main__":
    sys.exit(main())
