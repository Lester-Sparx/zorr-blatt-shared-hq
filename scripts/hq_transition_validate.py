#!/usr/bin/env python3
"""Trusted BASE→PR HEAD persistence-boundary validator.

Run this script from protected-main code (for example pull_request_target), never
from the PR checkout. The PR may propose data, but cannot choose its actor or
transition semantics.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import sys
from pathlib import Path
from typing import Any

from hq_adapter import (
    COMMIT_RE, HQError, authenticated_actor, create_owner_lock, load_json,
    record_sha256, role_registry, submit_review,
)
from hq_validate import validate_file, validate_repository


AUTHORITATIVE_SINGLETONS = {
    "hq/state/HQ_STATE.json",
    "hq/tasks/GITHUB_SHARED_HQ.json",
}
RECORD_PREFIXES = ("hq/artifacts/", "hq/reviews/", "hq/locks/")
ALLOWED_AUXILIARY = {"hq/dashboard/HQ_STATUS.md"}


def json_records(root: Path) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for prefix in RECORD_PREFIXES:
        directory = root / prefix
        if directory.exists():
            for path in directory.rglob("*.json"):
                records[path.relative_to(root).as_posix()] = load_json(path)
    return records


def file_bytes(root: Path) -> dict[str, bytes]:
    result: dict[str, bytes] = {}
    for path in root.rglob("*"):
        if path.is_file() and ".git" not in path.parts and "__pycache__" not in path.parts and path.suffix != ".pyc":
            result[path.relative_to(root).as_posix()] = path.read_bytes()
    return result


def strict_transition_files(base: Path, head: Path) -> set[str]:
    before, after = file_bytes(base), file_bytes(head)
    changed = {path for path in set(before) | set(after) if before.get(path) != after.get(path)}
    allowed = AUTHORITATIVE_SINGLETONS | ALLOWED_AUXILIARY
    record_changes = {path for path in changed if path.startswith(RECORD_PREFIXES)}
    invalid_records = sorted(path for path in record_changes if not path.endswith(".json"))
    if invalid_records:
        raise HQError(f"NON-JSON FILE IN EVIDENCE NAMESPACE FORBIDDEN: {invalid_records}")
    allowed.update(record_changes)
    forbidden = changed - allowed
    if forbidden:
        raise HQError(f"TRANSITION PR MODIFIES NON-TRANSITION FILES: {sorted(forbidden)}")
    return changed


def validate_record_path(path: str, record: dict[str, Any]) -> tuple[str, Path]:
    kind: str
    schema: Path
    if path.startswith("hq/artifacts/"):
        kind, schema = "ARTIFACT", Path("schemas/artifact.schema.json")
        expected = f"hq/artifacts/{record['sha256']}.json"
    elif path.startswith("hq/reviews/qc/"):
        kind, schema = "QC", Path("schemas/review.schema.json")
        expected = f"hq/reviews/qc/{record['taskId']}/r{record['revision']:02d}/{record['reviewerGitHubLogin']}.json"
    elif path.startswith("hq/reviews/architecture/"):
        kind, schema = "ARCHITECTURE", Path("schemas/review.schema.json")
        expected = f"hq/reviews/architecture/{record['taskId']}/r{record['revision']:02d}/{record['reviewerGitHubLogin']}.json"
    elif path.startswith("hq/locks/"):
        kind, schema = "LOCK", Path("schemas/lock.schema.json")
        expected = f"hq/locks/{record['taskId']}/r{record['revision']:02d}.json"
    else:
        raise HQError(f"UNKNOWN RECORD PATH: {path}")
    if path != expected:
        raise HQError(f"NON-CANONICAL RECORD PATH: expected {expected}, got {path}")
    return kind, schema


def transition_marker(kind: str, actor: str, task: dict[str, Any], previous_revision: int) -> dict[str, Any]:
    return {
        "kind": kind, "actorGitHubLogin": actor, "taskRevision": task["revision"],
        "candidateCommit": task["candidateCommit"], "artifactSha256": task["artifactSha256"],
        "previousRevision": previous_revision,
    }


def render_dashboard(state: dict[str, Any], task: dict[str, Any]) -> bytes:
    content = f"""# ZORR BLATT — GITHUB SHARED HQ

| Field | Value |
|---|---|
| Gate | `{state['currentGate']}` |
| HQ revision | `r{state['revision']:02d}` |
| Status | `{task['status']}` |
| Builder | `{task['builderGitHubLogin'] or 'PENDING'}` |
| Artifact | `{task['artifactSha256'] or 'PENDING'}` |
| Duncan QC | `{'RECORDED' if task['qcReview'] else 'PENDING'}` |
| Django architecture | `{'RECORDED' if task['architectureReview'] else 'PENDING'}` |
| Owner lock | `{'RECORDED' if task['lockRecord'] else 'PENDING'}` |
| G2 | `BLOCKED` |

This page is read-only. Protected `main` is the authoritative control/workflow state.
"""
    return content.encode("utf-8")


def validate_transition(base: Path, head: Path, *, actor: str, base_sha: str, head_sha: str) -> str:
    if not COMMIT_RE.fullmatch(base_sha) or not COMMIT_RE.fullmatch(head_sha):
        raise HQError("INVALID GITHUB COMMIT CONTEXT")
    validate_repository(base)
    validate_repository(head)
    changed = strict_transition_files(base, head)
    base_state = load_json(base / "hq/state/HQ_STATE.json")
    base_task = load_json(base / "hq/tasks/GITHUB_SHARED_HQ.json")
    head_state = load_json(head / "hq/state/HQ_STATE.json")
    head_task = load_json(head / "hq/tasks/GITHUB_SHARED_HQ.json")
    roles = role_registry(base / ".github/zb/roles.yml")

    base_records, head_records = json_records(base), json_records(head)
    if set(base_records) - set(head_records):
        raise HQError("APPEND-ONLY RECORD DELETION FORBIDDEN")
    modified = [path for path in base_records if base_records[path] != head_records[path]]
    if modified:
        raise HQError(f"IMMUTABLE RECORD MODIFICATION FORBIDDEN: {modified}")
    added = sorted(set(head_records) - set(base_records))

    if not added:
        if changed <= ALLOWED_AUXILIARY and head_state == base_state and head_task == base_task:
            if (head / "hq/dashboard/HQ_STATUS.md").read_bytes() != render_dashboard(base_state, base_task):
                raise HQError("DASHBOARD IS NOT A PURE PROJECTION")
            return "DASHBOARD_ONLY"
        raise HQError("NO AUTHENTICATED RECORD-BACKED TRANSITION DETECTED")
    if len(added) != 1:
        raise HQError("EXACTLY ONE APPEND-ONLY EVIDENCE RECORD REQUIRED PER TRANSITION")

    record_path = added[0]
    record = head_records[record_path]
    record_kind, schema_path = validate_record_path(record_path, record)
    validate_file(head / record_path, head / schema_path)
    expected_state = copy.deepcopy(base_state)
    expected_task = copy.deepcopy(base_task)
    previous_revision = base_task["revision"]

    if record_kind == "ARTIFACT":
        if roles["LESTER"] != actor:
            raise HQError("AUTHENTICATED LESTER REQUIRED FOR ARTIFACT TRANSITION")
        if record["builderGitHubLogin"] != actor or record["sourceCommit"] != base_sha:
            raise HQError("ARTIFACT CREATOR/PROTECTED BASE BINDING FAIL")
        if record["revision"] != previous_revision + 1 or record["taskId"] != base_task["taskId"]:
            raise HQError("ARTIFACT REVISION BINDING FAIL")
        expected_state["revision"] = record["revision"]
        expected_task.update({
            "revision": record["revision"], "parentRevision": previous_revision,
            "expectedMainCommit": base_sha, "candidateCommit": base_sha,
            "status": "ARTIFACT_REGISTERED", "builderGitHubLogin": actor,
            "artifactSha256": record["sha256"], "artifactReleaseTag": record["releaseTag"],
            "qcReview": None, "architectureReview": None, "lockRecord": None,
        })
        marker_kind = "ARTIFACT_REGISTERED"
    elif record_kind in {"QC", "ARCHITECTURE"}:
        if record["kind"] != record_kind:
            raise HQError("REVIEW KIND/PATH MISMATCH")
        expected_task, computed = submit_review(
            base_task, actor=actor, kind=record_kind, result=record["result"],
            report_sha256=record["reportSha256"], roles=roles,
        )
        if computed != record:
            raise HQError("REVIEW RECORD DOES NOT MATCH AUTHENTICATED TRANSITION")
        expected_task["expectedMainCommit"] = base_sha
        marker_kind = "QC_RECORDED" if record_kind == "QC" else "ARCHITECTURE_RECORDED"
    else:
        if roles["OWNER"] != actor:
            raise HQError("AUTHENTICATED OWNER REQUIRED FOR LOCK TRANSITION")
        qc_pointer = base_task.get("qcReview")
        arch_pointer = base_task.get("architectureReview")
        qc = next((item for item in base_records.values() if item.get("kind") == "QC" and record_sha256(item) == qc_pointer), None)
        architecture = next((item for item in base_records.values() if item.get("kind") == "ARCHITECTURE" and record_sha256(item) == arch_pointer), None)
        if qc is None or architecture is None:
            raise HQError("BOUND QC AND ARCHITECTURE RECORDS REQUIRED")
        lock_base_state = copy.deepcopy(base_state)
        lock_base_state["mainCommit"] = base_sha
        expected_task, computed = create_owner_lock(
            lock_base_state, base_task, qc, architecture, actor=actor,
            timestamp=record["ownerDecisionTimestamp"], roles=roles,
        )
        expected_task["expectedMainCommit"] = base_sha
        if computed != record:
            raise HQError("LOCK RECORD DOES NOT MATCH AUTHENTICATED OWNER TRANSITION")
        marker_kind = "OWNER_LOCKED"

    expected_state["mainCommit"] = base_sha
    expected_state["lastTransition"] = transition_marker(marker_kind, actor, expected_task, previous_revision)
    if head_state != expected_state or head_task != expected_task:
        raise HQError("PR HEAD STATE IS NOT THE EXACT AUTHENTICATED TRANSITION")
    if (head / "hq/dashboard/HQ_STATUS.md").read_bytes() != render_dashboard(head_state, head_task):
        raise HQError("DASHBOARD DOES NOT MATCH AUTHORITATIVE STATE")
    return marker_kind


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--head-sha", required=True)
    args = parser.parse_args()
    try:
        actor = authenticated_actor()
        transition = validate_transition(
            Path(args.base).resolve(), Path(args.head).resolve(), actor=actor,
            base_sha=args.base_sha, head_sha=args.head_sha,
        )
        print(f"AUTHENTICATED PR TRANSITION PASS · {transition} · ACTOR {actor}")
    except (HQError, OSError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
