from __future__ import annotations

import json
import re

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
EVIDENCE_FIELDS = {
    "evidenceId",
    "agentId",
    "domain",
    "taskKind",
    "mode",
    "result",
    "verified",
    "sourceRef",
    "exactHead",
    "sequence",
}
_SHA40 = re.compile(r"[0-9a-f]{40}")


class LesterProgrammingSchoolError(RuntimeError):
    pass


def _canonical_record(record: dict[str, object]) -> str:
    return json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def _nonempty_string(record: dict[str, object], key: str, error: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value.strip():
        raise LesterProgrammingSchoolError(error)
    return value


def validate_evidence(records: list[dict[str, object]]) -> list[dict[str, object]]:
    if not isinstance(records, list):
        raise LesterProgrammingSchoolError("EVIDENCE_LIST_REQUIRED")

    validated: list[dict[str, object]] = []
    seen: dict[str, str] = {}
    for record in records:
        if not isinstance(record, dict):
            raise LesterProgrammingSchoolError("EVIDENCE_OBJECT_REQUIRED")
        if set(record) != EVIDENCE_FIELDS:
            raise LesterProgrammingSchoolError("EVIDENCE_FIELDS_INVALID")

        evidence_id = _nonempty_string(record, "evidenceId", "EVIDENCE_ID_INVALID")
        if record.get("agentId") != "LESTER":
            raise LesterProgrammingSchoolError("AGENT_ID_INVALID")

        domain = _nonempty_string(record, "domain", "DOMAIN_INVALID")
        if domain not in DOMAINS:
            raise LesterProgrammingSchoolError("DOMAIN_UNKNOWN")
        _nonempty_string(record, "taskKind", "TASK_KIND_INVALID")

        mode = record.get("mode")
        if mode not in MODES:
            raise LesterProgrammingSchoolError("MODE_INVALID")
        result = record.get("result")
        if result not in RESULTS:
            raise LesterProgrammingSchoolError("RESULT_INVALID")
        if type(record.get("verified")) is not bool:
            raise LesterProgrammingSchoolError("VERIFIED_INVALID")
        _nonempty_string(record, "sourceRef", "SOURCE_REF_INVALID")

        exact_head = record.get("exactHead")
        if not isinstance(exact_head, str):
            raise LesterProgrammingSchoolError("EXACT_HEAD_INVALID")
        if mode in {"EXECUTION", "TRANSFER"}:
            if _SHA40.fullmatch(exact_head) is None:
                raise LesterProgrammingSchoolError("EXACT_HEAD_INVALID")
        elif exact_head and _SHA40.fullmatch(exact_head) is None:
            raise LesterProgrammingSchoolError("EXACT_HEAD_INVALID")

        sequence = record.get("sequence")
        if type(sequence) is not int or sequence < 0:
            raise LesterProgrammingSchoolError("SEQUENCE_INVALID")

        canonical = _canonical_record(record)
        previous = seen.get(evidence_id)
        if previous is not None:
            if previous != canonical:
                raise LesterProgrammingSchoolError("EVIDENCE_ID_CONFLICT")
            continue
        seen[evidence_id] = canonical
        validated.append(record)

    return validated
