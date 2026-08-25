#!/usr/bin/env python3
"""Classify a PR without executing untrusted head code."""

from __future__ import annotations

import argparse
import os
import stat
from pathlib import Path


AUTHORITATIVE_SINGLETONS = {
    "hq/state/HQ_STATE.json",
    "hq/tasks/GITHUB_SHARED_HQ.json",
}
RECORD_PREFIXES = ("hq/artifacts/", "hq/reviews/", "hq/locks/")
DASHBOARD = "hq/dashboard/HQ_STATUS.md"


def file_entries(root: Path) -> dict[str, tuple[str, bytes]]:
    """Snapshot path type and bytes without following untrusted symlinks."""
    result: dict[str, tuple[str, bytes]] = {}
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if (
            ".git" in relative.parts
            or "__pycache__" in relative.parts
            or path.suffix == ".pyc"
        ):
            continue
        mode = path.lstat().st_mode
        key = relative.as_posix()
        if stat.S_ISLNK(mode):
            result[key] = ("symlink", os.readlink(path).encode("utf-8"))
        elif stat.S_ISREG(mode):
            result[key] = ("regular", path.read_bytes())
        elif not stat.S_ISDIR(mode):
            result[key] = ("non-regular", b"")
    return result


def changed_files(base: Path, head: Path) -> set[str]:
    before, after = file_entries(base), file_entries(head)
    return {
        path
        for path in set(before) | set(after)
        if before.get(path) != after.get(path)
    }


def classify(base: Path, head: Path, kind: str) -> bool:
    changed = changed_files(base, head)
    if kind == "transition":
        return any(
            path in AUTHORITATIVE_SINGLETONS
            or path == DASHBOARD
            or path.startswith(RECORD_PREFIXES)
            for path in changed
        )
    if kind == "artifact":
        return any(
            path == "hq/tasks/GITHUB_SHARED_HQ.json"
            or path.startswith(RECORD_PREFIXES)
            for path in changed
        )
    raise ValueError(f"Unknown classification: {kind}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--kind", choices=("transition", "artifact"), required=True)
    args = parser.parse_args()
    print("true" if classify(Path(args.base), Path(args.head), args.kind) else "false")


if __name__ == "__main__":
    main()
