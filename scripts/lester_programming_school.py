from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

SKILL_STATES = ("UNTESTED", "FAILED", "PARTIAL", "PROVEN")
MODES = {"STUDY", "EXECUTION", "TRANSFER"}
RESULTS = {"PASS", "FAIL"}
DOMAINS = (
    "python",
    "typescript_javascript",
    "git_github",
    "testing_tdd",
    "debugging_root_cause",
    "software_architecture",
    "oss_reuse",
    "ci_cd_automation",
    "security_supply_chain",
    "data_storage_search",
    "graphics_realtime",
    "computer_vision",
    "ai_agent_integration",
    "performance_reliability",
    "windows_linux_runtime",
    "math_scientific_computing",
)
EVIDENCE_SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas" / "LESTER_PROGRAMMING_EVIDENCE_V1.schema.json"


class LesterProgrammingSchoolError(RuntimeError):
    pass


_VALIDATOR: Draft202012Validator | None = None


def _validator() -> Draft202012Validator:
    global _VALIDATOR
    if _VALIDATOR is None:
        try:
            schema = json.loads(EVIDENCE_SCHEMA_PATH.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise LesterProgrammingSchoolError("EVIDENCE_SCHEMA_UNREADABLE") from exc
        try:
            Draft202012Validator.check_schema(schema)
        except Exception as exc:
            raise LesterProgrammingSchoolError("EVIDENCE_SCHEMA_INVALID") from exc
        _VALIDATOR = Draft202012Validator(schema, format_checker=FormatChecker())
    return _VALIDATOR


def _canonical_record(record: dict[str, object]) -> str:
    return json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def _schema_error_code(error: object) -> str:
    path = list(getattr(error, "absolute_path", []))
    if "exactHead" in path:
        return "EXACT_HEAD_INVALID"
    if "domain" in path:
        return "DOMAIN_UNKNOWN"
    if "sourceRef" in path:
        return "SOURCE_REF_INVALID"
    if "mode" in path:
        return "MODE_INVALID"
    if "result" in path:
        return "RESULT_INVALID"
    if "sequence" in path:
        return "SEQUENCE_INVALID"
    if "verified" in path:
        return "VERIFIED_INVALID"
    if "agentId" in path:
        return "AGENT_ID_INVALID"
    if "evidenceId" in path:
        return "EVIDENCE_ID_INVALID"
    if "taskKind" in path:
        return "TASK_KIND_INVALID"
    return "EVIDENCE_SCHEMA_VALIDATION_FAILED"


def validate_evidence(records: list[dict[str, object]]) -> list[dict[str, object]]:
    if not isinstance(records, list):
        raise LesterProgrammingSchoolError("EVIDENCE_LIST_REQUIRED")

    validator = _validator()
    validated: list[dict[str, object]] = []
    seen: dict[str, str] = {}
    for record in records:
        if not isinstance(record, dict):
            raise LesterProgrammingSchoolError("EVIDENCE_OBJECT_REQUIRED")

        errors = sorted(validator.iter_errors(record), key=lambda item: list(item.absolute_path))
        if errors:
            first = errors[0]
            code = _schema_error_code(first)
            location = ".".join(str(part) for part in first.absolute_path) or "$"
            raise LesterProgrammingSchoolError(f"{code}:{location}:{first.message}")

        evidence_id = str(record["evidenceId"])
        canonical = _canonical_record(record)
        previous = seen.get(evidence_id)
        if previous is not None:
            if previous != canonical:
                raise LesterProgrammingSchoolError("EVIDENCE_ID_CONFLICT")
            continue
        seen[evidence_id] = canonical
        validated.append(record)

    return validated


def _empty_bucket(*, with_task_kinds: bool) -> dict[str, object]:
    bucket: dict[str, object] = {
        "state": "UNTESTED",
        "studyEvents": 0,
        "verifiedPasses": 0,
        "verifiedFailures": 0,
        "verifiedTransferPasses": 0,
        "evidenceIds": [],
        "sourceRefs": [],
        "lastSequence": None,
    }
    if with_task_kinds:
        bucket["taskKinds"] = {}
    return bucket


def _derive_state(bucket: dict[str, object]) -> str:
    passes = int(bucket["verifiedPasses"])
    failures = int(bucket["verifiedFailures"])
    transfers = int(bucket["verifiedTransferPasses"])
    if passes == 0 and failures == 0:
        return "UNTESTED"
    if passes == 0:
        return "FAILED"
    if passes >= 2 and transfers >= 1:
        return "PROVEN"
    return "PARTIAL"


def _apply_record(bucket: dict[str, object], record: dict[str, object]) -> None:
    evidence_ids = bucket["evidenceIds"]
    source_refs = bucket["sourceRefs"]
    assert isinstance(evidence_ids, list)
    assert isinstance(source_refs, list)
    evidence_ids.append(str(record["evidenceId"]))
    source_ref = str(record["sourceRef"])
    if source_ref not in source_refs:
        source_refs.append(source_ref)
    bucket["lastSequence"] = int(record["sequence"])

    mode = str(record["mode"])
    if mode == "STUDY":
        bucket["studyEvents"] = int(bucket["studyEvents"]) + 1
        bucket["state"] = _derive_state(bucket)
        return
    if record["verified"] is not True:
        bucket["state"] = _derive_state(bucket)
        return

    if record["result"] == "PASS":
        bucket["verifiedPasses"] = int(bucket["verifiedPasses"]) + 1
        if mode == "TRANSFER":
            bucket["verifiedTransferPasses"] = int(bucket["verifiedTransferPasses"]) + 1
    else:
        bucket["verifiedFailures"] = int(bucket["verifiedFailures"]) + 1
    bucket["state"] = _derive_state(bucket)


def build_profile(records: list[dict[str, object]]) -> dict[str, object]:
    validated = validate_evidence(records)
    ordered = sorted(validated, key=lambda item: (int(item["sequence"]), str(item["evidenceId"])))
    domains: dict[str, dict[str, object]] = {
        domain: _empty_bucket(with_task_kinds=True) for domain in DOMAINS
    }

    for record in ordered:
        domain_bucket = domains[str(record["domain"])]
        _apply_record(domain_bucket, record)
        task_kinds = domain_bucket["taskKinds"]
        assert isinstance(task_kinds, dict)
        task_kind = str(record["taskKind"])
        task_bucket = task_kinds.setdefault(task_kind, _empty_bucket(with_task_kinds=False))
        assert isinstance(task_bucket, dict)
        _apply_record(task_bucket, record)

    return {
        "schemaVersion": "LESTER_PROGRAMMING_PROFILE_V1",
        "agentId": "LESTER",
        "historicalBackfill": False,
        "disciplineSource": "hq/sheriff/SHERIFF_SCOREBOARD_V1.json",
        "disciplineAffectsCompetence": False,
        "domains": domains,
    }


def choose_next_training_target(
    profile: dict[str, object],
    preferred_domains: list[str] | None = None,
) -> dict[str, str]:
    if not isinstance(profile, dict) or profile.get("schemaVersion") != "LESTER_PROGRAMMING_PROFILE_V1":
        raise LesterProgrammingSchoolError("PROFILE_INVALID")
    domains = profile.get("domains")
    if not isinstance(domains, dict) or set(domains) != set(DOMAINS):
        raise LesterProgrammingSchoolError("PROFILE_DOMAINS_INVALID")

    order = list(DOMAINS)
    if preferred_domains is not None:
        if not isinstance(preferred_domains, list) or len(set(preferred_domains)) != len(preferred_domains):
            raise LesterProgrammingSchoolError("PREFERRED_DOMAINS_INVALID")
        if any(domain not in DOMAINS for domain in preferred_domains):
            raise LesterProgrammingSchoolError("PREFERRED_DOMAIN_UNKNOWN")
        order = preferred_domains + [domain for domain in DOMAINS if domain not in preferred_domains]

    state_priority = {"FAILED": 0, "UNTESTED": 1, "PARTIAL": 2, "PROVEN": 3}
    ranked: list[tuple[int, int, int, str, dict[str, object]]] = []
    for index, domain in enumerate(order):
        bucket = domains[domain]
        if not isinstance(bucket, dict):
            raise LesterProgrammingSchoolError("PROFILE_BUCKET_INVALID")
        state = bucket.get("state")
        if state not in state_priority:
            raise LesterProgrammingSchoolError("PROFILE_STATE_INVALID")
        passes = bucket.get("verifiedPasses")
        failures = bucket.get("verifiedFailures")
        if type(passes) is not int or type(failures) is not int or passes < 0 or failures < 0:
            raise LesterProgrammingSchoolError("PROFILE_ATTEMPTS_INVALID")
        ranked.append((state_priority[str(state)], passes + failures, index, domain, bucket))

    _, _, _, domain, bucket = min(ranked)
    state = str(bucket["state"])
    if state == "FAILED":
        recommended_mode = "EXECUTION"
        reason = "REMEDIATE_VERIFIED_FAILURE"
    elif state == "UNTESTED":
        recommended_mode = "EXECUTION"
        reason = "ESTABLISH_VERIFIED_BASELINE"
    elif state == "PARTIAL":
        recommended_mode = "TRANSFER"
        reason = "REQUIRE_CHANGED_UNSEEN_TRANSFER"
    else:
        recommended_mode = "TRANSFER"
        reason = "MAINTAIN_PROVEN_SKILL_WITH_TRANSFER"
    return {
        "domain": domain,
        "state": state,
        "recommendedMode": recommended_mode,
        "reason": reason,
    }
