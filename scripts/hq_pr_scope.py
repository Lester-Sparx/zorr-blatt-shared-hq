#!/usr/bin/env python3
"""Classify a PR without executing untrusted head code."""

from __future__ import annotations

import argparse
from pathlib import Path


AUTHORITATIVE_SINGLETONS = {
    "hq/state/HQ_STATE.json",
    "hq/tasks/GITHUB_SHARED_HQ.json",
}
RECORD_PREFIXES = ("hq/artifacts/", "hq/reviews/", "hq/locks/")
DASHBOARD = "hq/dashboard/HQ_STATUS.md"


def file_bytes(root: Path) -> dict[str, bytes]:
    result: dict[str, bytes] = {}
    for path in root.rglob("*"):
        if (
            path.is_file()
            and ".git" not in path.parts
            and "__pycache__" not in path.parts
            and path.suffix != ".pyc"
        ):
            result[path.relative_to(root).as_posix()] = path.read_bytes()
    return result


def changed_files(base: Path, head: Path) -> set[str]:
    before, after = file_bytes(base), file_bytes(head)
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
