"""
Other REST Families - File Upload/Download/Delete Round Trip (filehandler)

Uploads a small text file, reads its detail, downloads it back, and
deletes it. Every step verified live, 26.1.5950.0.

Mirrors: docs/15-Other-REST-Families.md#filehandler

Key facts:
    - This is a real network file share, not a sandbox -- verified files
      landed at \\fileserver01\data\Internal\Computer\P21\Scripts\Play on the
      test tenant, the middleware's own configured default path. Treat
      this family as filesystem access.
    - Upload/download take/return raw bytes, not JSON -- only
      file/detail and delete use the JSON envelope.
    - Casing split: file/detail takes lowercase `filename`; every other
      route takes `fileName`. Both are literal from the SDK contract.
    - A detail check on a deleted (or never-existing) file returns
      HTTP 200 with a JSON null body, not a 404 -- "gone" and "never
      existed" look identical.

Usage:
    python examples/python/rest/filehandler_roundtrip.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from common.auth import get_token, get_auth_headers
from common.config import load_config

import warnings
warnings.filterwarnings("ignore")

FILE_NAME = "zz_api_doc_test.txt"
CONTENT = b"ZZ API DOC TEST - safe to delete\nCreated by p21-api-documentation verification run.\n"


def main() -> None:
    print("Other REST Families - File Round Trip (filehandler)")
    print("=" * 60)

    config = load_config()
    token_data = get_token(config)
    headers = get_auth_headers(token_data["AccessToken"])
    print(f"Server: {config.base_url}")

    print("\n1. Upload:")
    print("-" * 50)
    upload = httpx.post(
        f"{config.base_url}/api/filehandler/file", params={"fileName": FILE_NAME},
        headers=headers, content=CONTENT, verify=config.verify_ssl, timeout=60.0,
    )
    upload.raise_for_status()
    print(f"  Uploaded {FILE_NAME} ({len(CONTENT)} bytes)")

    print("\n2. Detail (note lowercase 'filename' here, unlike every other route):")
    print("-" * 50)
    detail = httpx.get(
        f"{config.base_url}/api/filehandler/file/detail", params={"filename": FILE_NAME},
        headers=headers, verify=config.verify_ssl, timeout=30.0,
    )
    detail.raise_for_status()
    info = detail.json()
    print(f"  Path: {info['Path']}")
    print(f"  SizeInBytes: {info['SizeInBytes']}")

    print("\n3. Download:")
    print("-" * 50)
    download = httpx.get(
        f"{config.base_url}/api/filehandler/file", params={"fileName": FILE_NAME},
        headers=headers, verify=config.verify_ssl, timeout=30.0,
    )
    download.raise_for_status()
    print(f"  Content matches: {download.content == CONTENT}")

    print("\n4. Delete:")
    print("-" * 50)
    delete = httpx.delete(
        f"{config.base_url}/api/filehandler/file", params={"fileName": FILE_NAME},
        headers=headers, verify=config.verify_ssl, timeout=30.0,
    )
    delete.raise_for_status()
    print(f"  Delete response: {delete.json()!r}")

    print("\n5. Confirm gone (200 + null, NOT a 404):")
    print("-" * 50)
    after = httpx.get(
        f"{config.base_url}/api/filehandler/file/detail", params={"filename": FILE_NAME},
        headers=headers, verify=config.verify_ssl, timeout=30.0,
    )
    print(f"  HTTP {after.status_code}, body: {after.text!r}")


if __name__ == "__main__":
    main()
