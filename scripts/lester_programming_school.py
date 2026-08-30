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
