#!/usr/bin/env python3
"""Validate GitHub Shared HQ repository state and scope using only stdlib."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

from hq_adapter import HQError, load_json, record_sha256, role_registry


ROOT = Path(__file__).resolve().parent.parent
EXPECTED_CT_SHA = "AAADF06A0B64AF27F8E205596D09369705F36974CEED27DA05890DEA465A59EE"
FORBIDDEN_KEYS = {
    "lockedTiming", "lockedPlateSha256", "principalX", "principalY", "cameraFov",
    "weaponPosition", "contactPoint", "nearT", "minimumT", "frameTiming",
}


def type_ok(value: Any, kind: str) -> bool:
    return {
        "null": value is None, "object": isinstance(value, dict), "array": isinstance(value, list),
        "string": isinstance(value, str), "boolean": isinstance(value, bool),
        "integer": isinstance(value, int) and not isinstance(value, bool),
    }.get(kind, False)


def validate_schema(value: Any, schema: dict[str, Any], path: str = "$") -> None:
    if "oneOf" in schema:
        matches = 0
        for candidate in schema["oneOf"]:
            try:
                validate_schema(value, candidate, path)
                matches += 1
            except HQError:
                pass
        if matches != 1:
            raise HQError(f"SCHEMA {path}: oneOf matched {matches}")
        return
    if "const" in schema and value != schema["const"]:
        raise HQError(f"SCHEMA {path}: const mismatch")
    if "enum" in schema and value not in schema["enum"]:
        raise HQError(f"SCHEMA {path}: enum mismatch")
    kinds = schema.get("type")
    if kinds is not None:
        choices = [kinds] if isinstance(kinds, str) else kinds
        if not any(type_ok(value, kind) for kind in choices):
            raise HQError(f"SCHEMA {path}: invalid type")
    if isinstance(value, dict):
        required = schema.get("required", [])
        missing = [key for key in required if key not in value]
        if missing:
            raise HQError(f"SCHEMA {path}: missing {missing}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extra = set(value) - set(properties)
            if extra:
                raise HQError(f"SCHEMA {path}: extra {sorted(extra)}")
        for key, child in value.items():
            if key in properties:
                validate_schema(child, properties[key], f"{path}.{key}")
    if isinstance(value, list) and "items" in schema:
        for index, child in enumerate(value):
            validate_schema(child, schema["items"], f"{path}[{index}]")
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            raise HQError(f"SCHEMA {path}: too short")
        if "pattern" in schema and re.fullmatch(schema["pattern"], value) is None:
            raise HQError(f"SCHEMA {path}: pattern mismatch")
    if isinstance(value, int) and not isinstance(value, bool) and value < schema.get("minimum", value):
        raise HQError(f"SCHEMA {path}: below minimum")


def validate_file(data_path: Path, schema_path: Path) -> dict[str, Any]:
    data = load_json(data_path)
    schema = load_json(schema_path)
    validate_schema(data, schema)
    return data


def reject_production_values(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_KEYS:
                raise HQError(f"PRODUCTION VALUE FORBIDDEN: {path}.{key}")
            reject_production_values(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            reject_production_values(child, f"{path}[{index}]")


def validate_review_evidence(review: dict[str, Any]) -> None:
    report = review.get("report")
    if not isinstance(report, dict):
        raise HQError("REVIEW REPORT MISSING")
    expected_format = {
        "QC": "ZB_QC_REPORT_V1",
        "ARCHITECTURE": "ZB_ARCHITECTURE_REPORT_V1",
    }.get(review.get("kind"))
    if report.get("format") != expected_format:
        raise HQError("REVIEW KIND/REPORT FORMAT MISMATCH")
    if review.get("reportSha256") != record_sha256(report):
        raise HQError("REVIEW REPORT SHA256 MISMATCH")
    if review.get("result") != report.get("overallResult"):
        raise HQError("REVIEW RESULT/REPORT RESULT MISMATCH")


def validate_repository(root: Path = ROOT) -> None:
    state = validate_file(root / "hq/state/HQ_STATE.json", root / "schemas/hq-state.schema.json")
    task = validate_file(root / "hq/tasks/GITHUB_SHARED_HQ.json", root / "schemas/task.schema.json")
    lock = load_json(root / "hq/policy/control-tower-v1.lock.json")
    policy = load_json(root / ".github/zb/hq-policy.yml")
    roles = role_registry(root / ".github/zb/roles.yml")
    if lock != {
        "artifact": "ZB_CONTROL_TOWER_v1_METADATA_BOUNDARY_LOCAL_FIX_QC.zip",
        "releaseTag": "control-tower-v1-locked",
        "sha256": EXPECTED_CT_SHA, "immutable": True,
        "usage": "EXTERNAL_ENFORCEMENT_REFERENCE_ONLY",
    }:
        raise HQError("CONTROL TOWER LOCK MANIFEST FAIL")
    if policy["controlTowerSha256"] != EXPECTED_CT_SHA or not policy["productionWritesForbidden"]:
        raise HQError("HQ POLICY FAIL")
    if not roles["approvedTransportActors"] or not {"LESTER", "DUNCAN", "DJANGO", "OWNER"} <= roles["logicalRoles"]:
        raise HQError("TRANSPORT/LOGICAL ROLE REGISTRY FAIL")
    if state["revision"] != task["revision"]:
        raise HQError("STATE/TASK REVISION DIVERGENCE")
    if state["mainCommit"] != task["expectedMainCommit"]:
        raise HQError("STATE/TASK BASE COMMIT DIVERGENCE")
    if set(state["blockedGates"]) != {"G2", "VOICE_TO_SHOT"}:
        raise HQError("BLOCKED GATE POLICY FAIL")
    reject_production_values(state)
    reject_production_values(task)

    artifacts: list[dict[str, Any]] = []
    reviews: list[dict[str, Any]] = []
    locks: list[dict[str, Any]] = []
    allowed_namespace_docs = {
        "hq/artifacts/README.md", "hq/reviews/README.md", "hq/locks/README.md",
    }
    for namespace in ("hq/artifacts", "hq/reviews", "hq/locks"):
        for path in (root / namespace).rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(root).as_posix()
            if relative not in allowed_namespace_docs and path.suffix != ".json":
                raise HQError(f"NON-JSON FILE IN EVIDENCE NAMESPACE FORBIDDEN: {relative}")
    for path in (root / "hq/artifacts").glob("*.json"):
        record = validate_file(path, root / "schemas/artifact.schema.json")
        if path.name != f"{record['sha256']}.json":
            raise HQError("ARTIFACT RECORD PATH/SHA MISMATCH")
        artifacts.append(record)
    for namespace in ("qc", "architecture"):
        directory = root / "hq/reviews" / namespace
        if directory.exists():
            for path in directory.rglob("*.json"):
                record = validate_file(path, root / "schemas/review.schema.json")
                validate_review_evidence(record)
                expected_kind = "QC" if namespace == "qc" else "ARCHITECTURE"
                expected = directory / record["taskId"] / f"r{record['revision']:02d}" / f"{record['reviewerGitHubLogin']}.json"
                if record["kind"] != expected_kind or path != expected:
                    raise HQError("REVIEW RECORD PATH/BINDING MISMATCH")
                reviews.append(record)
    for path in (root / "hq/locks").rglob("*.json"):
        record = validate_file(path, root / "schemas/lock.schema.json")
        expected = root / "hq/locks" / record["taskId"] / f"r{record['revision']:02d}.json"
        if path != expected:
            raise HQError("LOCK RECORD PATH/BINDING MISMATCH")
        locks.append(record)

    if task["artifactSha256"] is not None:
        artifact = next((item for item in artifacts if item["sha256"] == task["artifactSha256"]), None)
        if artifact is None or (
            artifact["taskId"], artifact["revision"], artifact["sourceCommit"], artifact["builderGitHubLogin"]
        ) != (task["taskId"], task["revision"], task["candidateCommit"], task["builderGitHubLogin"]):
            raise HQError("CURRENT TASK ARTIFACT RECORD MISSING OR STALE")
        if "logicalRole" in artifact and (
            artifact["logicalRole"] != "LESTER"
            or artifact.get("transportActor") != artifact["builderGitHubLogin"]
            or artifact["transportActor"] not in roles["approvedTransportActors"]
        ):
            raise HQError("TASK ARTIFACT LOGICAL ROLE/TRANSPORT INVALID")
    for pointer, kind, expected_role in (
        (task["qcReview"], "QC", "DUNCAN"),
        (task["architectureReview"], "ARCHITECTURE", "DJANGO"),
    ):
        if pointer is None:
            continue
        review = next((item for item in reviews if record_sha256(item) == pointer), None)
        if review is None or review["kind"] != kind:
            raise HQError("TASK REVIEW POINTER INVALID")
        if "logicalRole" in review and (
            review["logicalRole"] != expected_role
            or review.get("transportActor") != review["reviewerGitHubLogin"]
            or review["transportActor"] not in roles["approvedTransportActors"]
        ):
            raise HQError("TASK REVIEW LOGICAL ROLE/TRANSPORT INVALID")
        if (review["taskId"], review["revision"], review["candidateCommit"], review["artifactSha256"]) != (
            task["taskId"], task["revision"], task["candidateCommit"], task["artifactSha256"]
        ):
            raise HQError("TASK REVIEW POINTER STALE")
    if task["lockRecord"] is not None:
        lock = next((item for item in locks if record_sha256(item) == task["lockRecord"]), None)
        if lock is None:
            raise HQError("TASK LOCK POINTER INVALID")
        if "logicalRole" in lock and (
            lock["logicalRole"] != "OWNER"
            or lock.get("transportActor") != lock["ownerGitHubLogin"]
            or lock["transportActor"] not in roles["approvedTransportActors"]
        ):
            raise HQError("TASK LOCK LOGICAL ROLE/TRANSPORT INVALID")
        if (lock["taskId"], lock["revision"], lock["candidateCommit"], lock["artifactSha256"]) != (
            task["taskId"], task["revision"], task["candidateCommit"], task["artifactSha256"]
        ):
            raise HQError("TASK LOCK POINTER STALE")
        qc = next((item for item in reviews if record_sha256(item) == task["qcReview"]), None)
        architecture = next((item for item in reviews if record_sha256(item) == task["architectureReview"]), None)
        if qc is None or architecture is None or lock["qcReportSha256"] != qc["reportSha256"] or lock["architectureReportSha256"] != architecture["reportSha256"]:
            raise HQError("LOCK EVIDENCE HASH BINDING FAIL")


def main() -> None:
    try:
        validate_repository()
        print("GITHUB SHARED HQ v0 VALIDATION PASS")
    except (HQError, OSError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
