#!/usr/bin/env python3
"""Verify OxiHuman core-pack bytes against its provenance record.

O0 experiment utility only. This does not promote donor data to ZB authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_pack(pack_path: Path, provenance_path: Path) -> dict[str, Any]:
    pack_path = Path(pack_path)
    provenance_path = Path(provenance_path)
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    pack = provenance.get("pack")
    errors: list[str] = []
    if not isinstance(pack, dict):
        return {"ok": False, "errors": ["PACK_RECORD_MISSING"]}

    actual_bytes = pack_path.stat().st_size
    actual_sha256 = _sha256(pack_path)

    if pack.get("name") != pack_path.name:
        errors.append("PACK_NAME_MISMATCH")
    if pack.get("format") != "OHPK v1":
        errors.append("FORMAT_NOT_OHPK_V1")
    if pack.get("license") != "CC0-1.0":
        errors.append("LICENSE_NOT_CC0_1_0")
    if pack.get("bytes") != actual_bytes:
        errors.append("BYTE_COUNT_MISMATCH")
    if pack.get("sha256") != actual_sha256:
        errors.append("SHA256_MISMATCH")

    return {
        "ok": not errors,
        "errors": errors,
        "pack": pack_path.name,
        "actual_bytes": actual_bytes,
        "expected_bytes": pack.get("bytes"),
        "actual_sha256": actual_sha256,
        "expected_sha256": pack.get("sha256"),
        "format": pack.get("format"),
        "license": pack.get("license"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pack", required=True, type=Path)
    parser.add_argument("--provenance", required=True, type=Path)
    args = parser.parse_args()
    result = verify_pack(args.pack, args.provenance)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
