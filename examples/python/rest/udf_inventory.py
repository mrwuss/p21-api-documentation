"""
Other REST Families - User-Defined Field Inventory

Enumerates every user-defined field in the system via the
extensibility/userdefinedfields family, grouped by the *_ud table it
extends, and separates real UDFs from the table's own key-column plumbing.

Mirrors: docs/15-Other-REST-Families.md#extensibilityuserdefinedfields

The convention (verified live, 26.1.5950.0):
    - ColumnOrder 1 is always the *_ud table's surrogate key.
    - The NOT NULL columns after it are the join key back to the base table
      (composite on some tables, e.g. ship_to_ud: company_id + ship_to_id).
    - The nullable columns are the real user-defined fields.
    - One tenant-observed exception: customer_ud.autoorder_flag is NOT NULL
      and is a genuine UDF (it has a default). The rule is a strong
      convention, not a guarantee -- read the names.

Usage:
    python examples/python/rest/udf_inventory.py
    python examples/python/rest/udf_inventory.py --table oe_hdr_ud
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from common.auth import get_token, get_auth_headers
from common.config import load_config

import warnings
warnings.filterwarnings("ignore")


def fetch_tables(base_url: str, headers: dict, verify_ssl: bool) -> list[dict]:
    """GET the UDF list grouped by table.

    Args:
        base_url: P21 base URL.
        headers: Auth headers.
        verify_ssl: Whether to verify SSL certificates.

    Returns:
        list[dict]: One entry per *_ud table, each carrying TableName,
            BaseTableName, and UserDefinedFields.list.
    """
    response = httpx.get(
        f"{base_url}/api/extensibility/userdefinedfields/tables",
        headers=headers,
        verify=verify_ssl,
        follow_redirects=True,
        timeout=60.0,
    )
    response.raise_for_status()
    return response.json()["list"]


def real_udfs(fields: list[dict]) -> list[dict]:
    """Split plumbing from genuine user-defined fields.

    ColumnOrder 1 is always the surrogate key. Everything NOT NULL after it
    is treated as the join key back to the base table; everything nullable
    is a real UDF. Verified across all 23 tables on the test tenant, with
    one known exception (customer_ud.autoorder_flag) -- this heuristic
    sorts a long list fast, it does not replace reading the names.

    Args:
        fields: The table's UserDefinedFields.list, any order.

    Returns:
        list[dict]: The fields classified as real UDFs.
    """
    ordered = sorted(fields, key=lambda f: f["ColumnOrder"])
    if not ordered:
        return []
    tail = ordered[1:]  # drop the surrogate key
    seen_nullable = False
    out = []
    for f in tail:
        if f["IsNullable"] == "Y":
            seen_nullable = True
            out.append(f)
        elif not seen_nullable:
            continue  # still inside the join-key run
        else:
            out.append(f)  # NOT NULL after a nullable one -- flag it anyway
    return out


def main() -> None:
    parser = argparse.ArgumentParser(
        description="List user-defined fields (docs/15 extensibility/userdefinedfields)"
    )
    parser.add_argument(
        "--table", help="Show only this *_ud table (e.g. oe_hdr_ud). Case-insensitive."
    )
    args = parser.parse_args()

    print("Other REST Families - User-Defined Field Inventory")
    print("=" * 60)

    config = load_config()
    token_data = get_token(config)
    headers = get_auth_headers(token_data["AccessToken"])
    print(f"Server: {config.base_url}")

    tables = fetch_tables(config.base_url, headers, config.verify_ssl)
    if args.table:
        tables = [t for t in tables if t["TableName"].lower() == args.table.lower()]
        if not tables:
            raise SystemExit(f"No UD table named {args.table!r}")

    total_real = 0
    for t in tables:
        fields = t["UserDefinedFields"]["list"]
        udfs = real_udfs(fields)
        total_real += len(udfs)
        print(f"\n{t['TableName']}  (extends {t['BaseTableName']})")
        print("-" * 50)
        if not udfs:
            print("  (no user-defined fields beyond the join key)")
            continue
        for f in udfs:
            print(f"  {f['ColumnName']:32} {f['DataType']}({f['Length']})  "
                  f"null={f['IsNullable']}")

    print("\n" + "=" * 60)
    print(f"{len(tables)} table(s), {total_real} user-defined field(s)")


if __name__ == "__main__":
    main()
