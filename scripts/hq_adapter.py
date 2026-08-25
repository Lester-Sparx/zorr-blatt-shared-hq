#!/usr/bin/env python3
"""Pure transition engine for GitHub Shared HQ v0.

The adapter never edits LOCKED Control Tower or ZB CORE. It validates a proposed
transition against authenticated GitHub context and returns candidate records.
Persistence happens only through a protected-main pull request.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parent.parent
CT_LOCK = ROOT / "hq" / "policy" / "control-tower-v1.lock.json"
ROLES_PATH = ROOT / ".github" / "zb" / "roles.yml"
SHA256_RE = re.compile(r"^[A-F0-9]{64}$")
COMMIT_RE = re.compile(r"^[a-f0-9]{40}$")


class HQError(RuntimeError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise HQError(f"Expected object: {path}")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def record_sha256(record: Mapping[str, Any]) -> str:
    canonical = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest().upper()


def role_registry(path: Path = ROLES_PATH) -> dict[str, str]:
    roles = load_json(path)  # JSON is valid YAML and avoids an unpinned YAML parser.
    required = {"OWNER", "LESTER", "DUNCAN", "DJANGO"}
    if set(roles) != required:
        raise HQError("ROLE REGISTRY KEYS INVALID")
    if any(not isinstance(login, str) or not login for login in roles.values()):
        raise HQError("ROLE LOGIN INVALID")
    if len(set(roles.values())) != len(roles):
        raise HQError("ONE GITHUB IDENTITY CANNOT HOLD MULTIPLE ENFORCEMENT ROLES")
    return roles


def authenticated_actor(env: Mapping[str, str] | None = None) -> str:
    context = os.environ if env is None else env
    if context.get("GITHUB_ACTIONS") != "true":
        raise HQError("AUTHENTICATED GITHUB ACTIONS CONTEXT REQUIRED")
    if context.get("GITHUB_EVENT_NAME") not in {"pull_request", "pull_request_target", "workflow_dispatch"}:
        raise HQError("UNTRUSTED GITHUB EVENT")
    actor = context.get("GITHUB_ACTOR", "")
    if not actor:
        raise HQError("GITHUB ACTOR MISSING")
    return actor


def require_role(actor: str, role: str, roles: Mapping[str, str]) -> None:
    if roles.get(role) != actor:
        raise HQError(f"AUTHENTICATED {role} IDENTITY REQUIRED")


def verify_control_tower_artifact(path: Path) -> str:
    lock = load_json(CT_LOCK)
    actual = sha256_file(path)
    if actual != lock["sha256"]:
        raise HQError(f"CONTROL TOWER HASH FAIL: expected {lock['sha256']}, got {actual}")
    return actual


def verify_safe_artifact(path_value: str, artifact_root: Path) -> tuple[Path, str]:
    root = artifact_root.resolve()
    path = (root / path_value).resolve()
    if path == root or root not in path.parents or not path.is_file():
        raise HQError("ARTIFACT PATH OUTSIDE TRUSTED DOWNLOAD ROOT")
    return path, sha256_file(path)


def assert_cas(
    state: Mapping[str, Any], task: Mapping[str, Any], expected_revision: int,
    expected_main: str, current_main: str | None = None,
) -> None:
    if state["revision"] != expected_revision or task["revision"] != expected_revision:
        raise HQError("TASK REVISION CAS FAIL")
    if not COMMIT_RE.fullmatch(expected_main):
        raise HQError("MAIN COMMIT CAS FAIL")
    if current_main is not None and current_main != expected_main:
        raise HQError("MAIN COMMIT CAS FAIL")


def assert_candidate_binding(task: Mapping[str, Any], record: Mapping[str, Any]) -> None:
    expected = (task["taskId"], task["revision"], task["candidateCommit"], task["artifactSha256"])
    actual = (record["taskId"], record["revision"], record["candidateCommit"], record["artifactSha256"])
    if actual != expected:
        raise HQError("STALE OR FOREIGN EVIDENCE BINDING")


def register_artifact(
    state: Mapping[str, Any], task: Mapping[str, Any], *, actor: str,
    expected_revision: int, expected_main: str, candidate_commit: str,
    artifact_path: str, artifact_root: Path, release_tag: str,
    current_main: str | None = None,
    roles: Mapping[str, str] | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    registry = role_registry() if roles is None else dict(roles)
    if len(set(registry.values())) != 4:
        raise HQError("ROLE SEPARATION FAIL")
    require_role(actor, "LESTER", registry)
    assert_cas(state, task, expected_revision, expected_main, current_main)
    if not COMMIT_RE.fullmatch(candidate_commit) or not release_tag:
        raise HQError("INVALID CANDIDATE IDENTITY")
    _, digest = verify_safe_artifact(artifact_path, artifact_root)
    revision = expected_revision + 1
    new_state = copy.deepcopy(state)
    new_task = copy.deepcopy(task)
    new_state["revision"] = revision
    new_state["mainCommit"] = expected_main
    new_state["lastTransition"] = {
        "kind": "ARTIFACT_REGISTERED", "actorGitHubLogin": actor,
        "taskRevision": revision, "candidateCommit": candidate_commit,
        "artifactSha256": digest, "previousRevision": expected_revision,
    }
    new_task.update({
        "revision": revision, "parentRevision": expected_revision,
        "expectedMainCommit": expected_main, "candidateCommit": candidate_commit,
        "status": "ARTIFACT_REGISTERED", "builderGitHubLogin": actor,
        "artifactSha256": digest, "artifactReleaseTag": release_tag,
        "qcReview": None, "architectureReview": None, "lockRecord": None,
    })
    manifest = {
        "taskId": new_task["taskId"], "revision": revision, "sha256": digest,
        "releaseTag": release_tag, "sourceCommit": candidate_commit,
        "builderGitHubLogin": actor, "immutable": True,
    }
    return new_state, new_task, manifest


def submit_review(
    task: Mapping[str, Any], *, actor: str, kind: str, result: str,
    report: Mapping[str, Any], roles: Mapping[str, str] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    registry = role_registry() if roles is None else dict(roles)
    if task.get("status") not in {"ARTIFACT_REGISTERED", "QC_PASS", "QC_PARTIAL", "QC_FAIL"}:
        raise HQError("CURRENT VERIFIED ARTIFACT REVISION REQUIRED BEFORE REVIEW")
    if not SHA256_RE.fullmatch(task.get("artifactSha256") or "") or not COMMIT_RE.fullmatch(task.get("candidateCommit") or ""):
        raise HQError("CURRENT ARTIFACT/COMMIT BINDING REQUIRED BEFORE REVIEW")
    required_role = {"QC": "DUNCAN", "ARCHITECTURE": "DJANGO"}.get(kind)
    allowed = {"QC": {"PASS", "PARTIAL", "FAIL"}, "ARCHITECTURE": {"ACCEPTED", "CHANGES_REQUIRED"}}
    if required_role is None or result not in allowed[kind] or not isinstance(report, Mapping):
        raise HQError("INVALID REVIEW")
    if report.get("overallResult") != result:
        raise HQError("REVIEW RESULT/REPORT RESULT MISMATCH")
    require_role(actor, required_role, registry)
    if actor == task["builderGitHubLogin"]:
        raise HQError("SELF REVIEW FORBIDDEN")
    embedded_report = copy.deepcopy(dict(report))
    review = {
        "kind": kind, "taskId": task["taskId"], "revision": task["revision"],
        "candidateCommit": task["candidateCommit"], "artifactSha256": task["artifactSha256"],
        "reviewerGitHubLogin": actor, "result": result, "report": embedded_report,
        "reportSha256": record_sha256(embedded_report),
    }
    new_task = copy.deepcopy(task)
    key = "qcReview" if kind == "QC" else "architectureReview"
    new_task[key] = record_sha256(review)
    if kind == "QC":
        new_task["status"] = {"PASS": "QC_PASS", "PARTIAL": "QC_PARTIAL", "FAIL": "QC_FAIL"}[result]
    return new_task, review


def create_owner_lock(
    state: Mapping[str, Any], task: Mapping[str, Any], qc: Mapping[str, Any], architecture: Mapping[str, Any],
    *, actor: str, timestamp: str, roles: Mapping[str, str] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    registry = role_registry() if roles is None else dict(roles)
    require_role(actor, "OWNER", registry)
    assert_candidate_binding(task, qc)
    assert_candidate_binding(task, architecture)
    if qc["kind"] != "QC" or qc["result"] != "PASS":
        raise HQError("INDEPENDENT QC PASS REQUIRED")
    if architecture["kind"] != "ARCHITECTURE" or architecture["result"] != "ACCEPTED":
        raise HQError("ARCHITECTURE ACCEPTANCE REQUIRED")
    if task.get("qcReview") != record_sha256(qc) or task.get("architectureReview") != record_sha256(architecture):
        raise HQError("TASK REVIEW POINTERS DO NOT MATCH EVIDENCE")
    if len({task["builderGitHubLogin"], qc["reviewerGitHubLogin"], architecture["reviewerGitHubLogin"], actor}) != 4:
        raise HQError("BUILDER/QC/ARCHITECTURE/OWNER IDENTITIES MUST BE DISTINCT")
    lock = {
        "taskId": task["taskId"], "revision": task["revision"],
        "artifactSha256": task["artifactSha256"], "candidateCommit": task["candidateCommit"],
        "qcReportSha256": qc["reportSha256"], "architectureReportSha256": architecture["reportSha256"],
        "ownerGitHubLogin": actor, "ownerDecisionTimestamp": timestamp,
        "baseMainCommit": state["mainCommit"],
    }
    new_task = copy.deepcopy(task)
    new_task["status"] = "LOCKED"
    new_task["lockRecord"] = record_sha256(lock)
    return new_task, lock


def main() -> None:
    parser = argparse.ArgumentParser(description="ZB GitHub Shared HQ external adapter")
    commands = parser.add_subparsers(dest="command", required=True)
    verify = commands.add_parser("verify-control-tower")
    verify.add_argument("--artifact", required=True)
    task_artifact = commands.add_parser("verify-task-artifact")
    task_artifact.add_argument("--artifact-root", required=True)
    task_artifact.add_argument("--asset-name", required=True)
    task_artifact.add_argument("--task", default=str(ROOT / "hq/tasks/GITHUB_SHARED_HQ.json"))
    owner_lock = commands.add_parser("prepare-owner-lock")
    owner_lock.add_argument("--timestamp", required=True)
    owner_lock.add_argument("--output", required=True)
    release_tag = commands.add_parser("release-tag")
    release_tag.add_argument("--task", required=True)
    release_directory = commands.add_parser("verify-release-directory")
    release_directory.add_argument("--artifact-root", required=True)
    release_directory.add_argument("--task", required=True)
    commands.add_parser("identity")
    args = parser.parse_args()
    try:
        if args.command == "verify-control-tower":
            print(f"CONTROL TOWER VERIFIED {verify_control_tower_artifact(Path(args.artifact))}")
        elif args.command == "verify-task-artifact":
            task = load_json(Path(args.task))
            if task.get("status") == "IMPLEMENTATION_PENDING" or not SHA256_RE.fullmatch(task.get("artifactSha256") or ""):
                raise HQError("REGISTERED TASK ARTIFACT REQUIRED")
            _, actual = verify_safe_artifact(args.asset_name, Path(args.artifact_root))
            if actual != task["artifactSha256"]:
                raise HQError(f"ARTIFACT HASH FAIL: expected {task['artifactSha256']}, got {actual}")
            print(f"TASK ARTIFACT VERIFIED {actual}")
        elif args.command == "prepare-owner-lock":
            actor = authenticated_actor()
            roles = role_registry()
            state = load_json(ROOT / "hq/state/HQ_STATE.json")
            task = load_json(ROOT / "hq/tasks/GITHUB_SHARED_HQ.json")
            current_main = os.environ.get("GITHUB_SHA", "")
            if not COMMIT_RE.fullmatch(current_main):
                raise HQError("CURRENT PROTECTED MAIN COMMIT REQUIRED")
            working_state = copy.deepcopy(state)
            working_state["mainCommit"] = current_main
            reviews = [load_json(path) for path in (ROOT / "hq/reviews").rglob("*.json")]
            qc = next((item for item in reviews if item.get("kind") == "QC" and record_sha256(item) == task.get("qcReview")), None)
            architecture = next((item for item in reviews if item.get("kind") == "ARCHITECTURE" and record_sha256(item) == task.get("architectureReview")), None)
            if qc is None or architecture is None:
                raise HQError("BOUND QC AND ARCHITECTURE RECORDS REQUIRED")
            proposed_task, lock = create_owner_lock(
                working_state, task, qc, architecture, actor=actor, timestamp=args.timestamp, roles=roles,
            )
            proposed_task["expectedMainCommit"] = current_main
            output = Path(args.output).resolve()
            output.mkdir(parents=True, exist_ok=False)
            lock_path = output / "hq/locks" / task["taskId"] / f"r{task['revision']:02d}.json"
            task_path = output / "hq/tasks/GITHUB_SHARED_HQ.json"
            state_path = output / "hq/state/HQ_STATE.json"
            for path in (lock_path, task_path, state_path):
                path.parent.mkdir(parents=True, exist_ok=True)
            lock_path.write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
            task_path.write_text(json.dumps(proposed_task, indent=2) + "\n", encoding="utf-8")
            proposed_state = copy.deepcopy(working_state)
            proposed_state["lastTransition"] = {
                "kind": "OWNER_LOCKED", "actorGitHubLogin": actor,
                "taskRevision": task["revision"], "candidateCommit": task["candidateCommit"],
                "artifactSha256": task["artifactSha256"], "previousRevision": task["revision"],
            }
            state_path.write_text(json.dumps(proposed_state, indent=2) + "\n", encoding="utf-8")
            print(f"OWNER LOCK PROPOSAL CREATED {output}")
        elif args.command == "release-tag":
            task = load_json(Path(args.task))
            tag = task.get("artifactReleaseTag") or ""
            if re.fullmatch(r"[A-Za-z0-9._-]+", tag) is None:
                raise HQError("SAFE REGISTERED RELEASE TAG REQUIRED")
            print(tag)
        elif args.command == "verify-release-directory":
            task = load_json(Path(args.task))
            expected = task.get("artifactSha256") or ""
            if not SHA256_RE.fullmatch(expected):
                raise HQError("REGISTERED TASK ARTIFACT REQUIRED")
            root = Path(args.artifact_root).resolve()
            matches = [path for path in root.iterdir() if path.is_file() and sha256_file(path) == expected]
            if len(matches) != 1:
                raise HQError(f"IMMUTABLE RELEASE ARTIFACT MATCH COUNT {len(matches)}")
            print(f"TASK ARTIFACT VERIFIED {expected} · {matches[0].name}")
        else:
            actor = authenticated_actor()
            roles = role_registry()
            role = next((name for name, login in roles.items() if login == actor), None)
            if role is None:
                raise HQError("AUTHENTICATED ACTOR HAS NO ENFORCEMENT ROLE")
            print(f"AUTHENTICATED GITHUB ACTOR {actor} · ROLE {role}")
    except (HQError, OSError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
