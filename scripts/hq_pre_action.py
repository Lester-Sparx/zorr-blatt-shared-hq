from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
from typing import Any

try:
    from scripts.hq_context_discipline import ContextDisciplineError, project_current_state
    from scripts.hq_unified_archive import build_learning_policy
    from scripts.zb_communication_base import API_ROOT, REPOSITORY, TRANSPORT_ACTOR, GitHubApi, PersistenceError
except ModuleNotFoundError:
    from hq_context_discipline import ContextDisciplineError, project_current_state
    from hq_unified_archive import build_learning_policy
    from zb_communication_base import API_ROOT, REPOSITORY, TRANSPORT_ACTOR, GitHubApi, PersistenceError


SCHEMA = "ZB_PRE_ACTION_DECISION_V1"
CONTEXT_PACKET_SCHEMA = "ZB_CONTEXT_PACKET_V1"
CONTEXT_STATE_SCHEMA = "ZB_CONTEXT_CURRENT_STATE_V1"
ACTIONS = {
    "EXECUTE_PRODUCT_STEP",
    "READ_ACTIVE_RESULT",
    "READ_REQUIRED_EVIDENCE",
    "SEARCH_ASSET",
    "VERIFY_PREREQUISITE",
    "PROCESS_MUTATION",
    "REQUEST_OWNER_ACTION",
    "CLAIM_PASS",
    "IMAGE_MUTATION",
}
BOOL_FIELDS = (
    "directlyAdvancesPhysicalResult",
    "activeAttempt",
    "exactOwnerInputProvided",
    "prerequisiteAlreadyProven",
    "provenProcessBlocker",
    "newPhysicalBlocker",
    "provenExternalBoundary",
    "freshVerificationEvidence",
    "explicitOwnerImageMutationCommand",
)
REQUIRED_FIELDS = ("action", *BOOL_FIELDS, "processMutationCountForBlocker")
READ_ONLY_WHILE_ACTIVE = {"READ_ACTIVE_RESULT", "READ_REQUIRED_EVIDENCE"}
_GITHUB_PR_SOURCE = re.compile(r"^github:pr:([1-9][0-9]*)$")
_GITHUB_ISSUE_COMMENT_SOURCE = re.compile(r"^github:issue-comment:([1-9][0-9]*)$")
_TASK_ISSUE = re.compile(r"^#([1-9][0-9]*)$")
_SHA40 = re.compile(r"^[0-9a-f]{40}$")
_TRUSTED_DURABLE_AUTHORITIES = {"GITHUB", "OWNER", "SHERIFF"}
_NEW_BLOCKER_IDENTITY_KEYS = {
    "NEW_PHYSICAL_BLOCKER",
    "ERROR_SIGNATURE",
    "PROCESS_MUTATION_ERROR_SIGNATURE",
}
_PERMISSION_E2_KEYS = _NEW_BLOCKER_IDENTITY_KEYS | {"RESULT"}
_E2_EVIDENCE_MARKER = "ZB_CONTEXT_E2_EVIDENCE_V1"


class PreActionError(RuntimeError):
    pass


def _validate_context(context: dict[str, Any]) -> None:
    if not isinstance(context, dict):
        raise PreActionError("PRE_ACTION_CONTEXT_INVALID:OBJECT_REQUIRED")
    missing = [key for key in REQUIRED_FIELDS if key not in context]
    if missing:
        raise PreActionError("PRE_ACTION_CONTEXT_MISSING:" + ",".join(missing))
    if set(context) - set(REQUIRED_FIELDS):
        unknown = sorted(set(context) - set(REQUIRED_FIELDS))
        raise PreActionError("PRE_ACTION_CONTEXT_INVALID:UNKNOWN_FIELDS:" + ",".join(unknown))
    action = context["action"]
    if not isinstance(action, str) or action not in ACTIONS:
        raise PreActionError("PRE_ACTION_CONTEXT_INVALID:ACTION")
    for key in BOOL_FIELDS:
        if type(context[key]) is not bool:
            raise PreActionError(f"PRE_ACTION_CONTEXT_INVALID:{key}")
    count = context["processMutationCountForBlocker"]
    if type(count) is not int or count < 0:
        raise PreActionError("PRE_ACTION_CONTEXT_INVALID:processMutationCountForBlocker")


def _learning_view(learning_policy: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(learning_policy, dict) or learning_policy.get("status") != "PROVEN":
        return {
            "status": "NOT_PROVEN",
            "lesson_count": 0,
            "verdict_ids": [],
            "policy_prefix": "",
        }
    lessons = learning_policy.get("lessons")
    if not isinstance(lessons, list):
        lessons = []
    verdict_ids = sorted(
        str(item.get("verdict_id"))
        for item in lessons
        if isinstance(item, dict) and isinstance(item.get("verdict_id"), str) and item.get("verdict_id")
    )
    return {
        "status": "PROVEN",
        "lesson_count": int(learning_policy.get("lesson_count") or len(verdict_ids)),
        "verdict_ids": verdict_ids,
        "policy_prefix": str(learning_policy.get("policy_prefix") or ""),
    }


def _validate_context_packet(context_packet: dict[str, Any]) -> None:
    if not isinstance(context_packet, dict) or context_packet.get("schema") != CONTEXT_PACKET_SCHEMA:
        raise PreActionError("CONTEXT_PACKET_INVALID")
    required = {
        "status",
        "mandatory_anchors",
        "current_state",
        "jit_facets",
        "missing_facets",
        "source_refs",
    }
    if not required.issubset(context_packet):
        raise PreActionError("CONTEXT_PACKET_INVALID")
    status = context_packet.get("status")
    if status not in {"PROVEN", "NOT_PROVEN"}:
        raise PreActionError("CONTEXT_PACKET_INVALID")
    anchors = context_packet.get("mandatory_anchors")
    if not isinstance(anchors, list):
        raise PreActionError("CONTEXT_PACKET_INVALID")
    for anchor in anchors:
        if (
            not isinstance(anchor, dict)
            or not isinstance(anchor.get("key"), str)
            or not anchor.get("key")
            or "value" not in anchor
        ):
            raise PreActionError("CONTEXT_PACKET_INVALID")
    current_state = context_packet.get("current_state")
    if (
        not isinstance(current_state, dict)
        or current_state.get("schema") != CONTEXT_STATE_SCHEMA
        or not isinstance(current_state.get("facts"), list)
    ):
        raise PreActionError("CONTEXT_PACKET_INVALID")
    try:
        reprojection = project_current_state(current_state["facts"])
    except ContextDisciplineError as exc:
        raise PreActionError("DURABLE_CONTEXT_NOT_PROVEN") from exc
    if reprojection != current_state:
        raise PreActionError("CONTEXT_PACKET_INVALID")
    jit_facets = context_packet.get("jit_facets")
    if not isinstance(jit_facets, dict):
        raise PreActionError("CONTEXT_PACKET_INVALID")
    if not all(isinstance(key, str) and key and isinstance(value, list) for key, value in jit_facets.items()):
        raise PreActionError("CONTEXT_PACKET_INVALID")
    missing_facets = context_packet.get("missing_facets")
    source_refs = context_packet.get("source_refs")
    if not isinstance(missing_facets, list) or not all(isinstance(item, str) and item for item in missing_facets):
        raise PreActionError("CONTEXT_PACKET_INVALID")
    if not isinstance(source_refs, list) or not all(isinstance(item, str) and item for item in source_refs):
        raise PreActionError("CONTEXT_PACKET_INVALID")
    if status == "PROVEN" and (missing_facets or not source_refs):
        raise PreActionError("CONTEXT_PACKET_INVALID")


def _packet_facts(context_packet: dict[str, Any]) -> list[dict[str, Any]]:
    current_state = context_packet.get("current_state")
    facts = current_state.get("facts", []) if isinstance(current_state, dict) else []
    return [fact for fact in facts if isinstance(fact, dict)]


def _packet_current_task_issue(context_packet: dict[str, Any]) -> int | None:
    anchors = context_packet.get("mandatory_anchors")
    if not isinstance(anchors, list):
        return None
    values = [
        anchor.get("value")
        for anchor in anchors
        if isinstance(anchor, dict) and anchor.get("key") == "CURRENT_TASK"
    ]
    if len(values) != 1 or not isinstance(values[0], str):
        return None
    match = _TASK_ISSUE.fullmatch(values[0])
    return int(match.group(1)) if match is not None else None


def _packet_active_head_fact(context_packet: dict[str, Any]) -> dict[str, Any] | None:
    heads = [fact for fact in _packet_facts(context_packet) if fact.get("key") == "ACTIVE_HEAD"]
    if len(heads) != 1:
        return None
    return heads[0]


def _packet_active_head(context_packet: dict[str, Any]) -> str | None:
    fact = _packet_active_head_fact(context_packet)
    if fact is None:
        return None
    value = fact.get("value")
    if not isinstance(value, str) or not value:
        return None
    return value


def _packet_active_head_pr(context_packet: dict[str, Any]) -> int | None:
    fact = _packet_active_head_fact(context_packet)
    if fact is None:
        return None
    refs = fact.get("source_refs")
    if not isinstance(refs, list):
        return None
    matches: list[int] = []
    for ref in refs:
        if not isinstance(ref, str):
            continue
        match = _GITHUB_PR_SOURCE.fullmatch(ref)
        if match is not None:
            matches.append(int(match.group(1)))
    if len(matches) != 1:
        return None
    return matches[0]


def _packet_process_mutation_count(context_packet: dict[str, Any]) -> int | None:
    counts = [fact for fact in _packet_facts(context_packet) if fact.get("key") == "PROCESS_MUTATION_COUNT"]
    if len(counts) != 1:
        return None
    fact = counts[0]
    value = fact.get("value")
    refs = fact.get("source_refs")
    if (
        fact.get("class") != "E2"
        or fact.get("verified") is not True
        or type(value) is not int
        or value < 0
        or not isinstance(refs, list)
        or not refs
        or not all(isinstance(item, str) and item for item in refs)
    ):
        return None
    return value


def _packet_verified_fact(context_packet: dict[str, Any], key: str) -> dict[str, Any] | None:
    matches = [fact for fact in _packet_facts(context_packet) if fact.get("key") == key]
    if len(matches) != 1:
        return None
    fact = matches[0]
    refs = fact.get("source_refs")
    if (
        fact.get("class") != "E2"
        or fact.get("verified") is not True
        or fact.get("authority") not in _TRUSTED_DURABLE_AUTHORITIES
        or not isinstance(refs, list)
        or not refs
        or not all(isinstance(item, str) and item for item in refs)
    ):
        return None
    return fact


def _packet_has_verified_true_fact(context_packet: dict[str, Any], key: str) -> bool:
    fact = _packet_verified_fact(context_packet, key)
    return fact is not None and fact.get("value") is True


def _packet_verified_string_fact(context_packet: dict[str, Any], key: str) -> str | None:
    fact = _packet_verified_fact(context_packet, key)
    if fact is None:
        return None
    value = fact.get("value")
    if not isinstance(value, str) or not value.strip():
        return None
    return value


def _canonical_evidence_value(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _fact_issue_comment_id(fact: dict[str, Any]) -> int | None:
    refs = fact.get("source_refs")
    if not isinstance(refs, list):
        return None
    matches: list[int] = []
    for ref in refs:
        if not isinstance(ref, str):
            continue
        match = _GITHUB_ISSUE_COMMENT_SOURCE.fullmatch(ref)
        if match is not None:
            matches.append(int(match.group(1)))
    if len(matches) != 1:
        return None
    return matches[0]


def _comment_proves_fact(
    comment: dict[str, Any],
    fact: dict[str, Any],
    *,
    expected_issue: int,
) -> bool:
    issue_url = comment.get("issue_url")
    user = comment.get("user")
    expected_issue_url = f"{API_ROOT}/repos/{REPOSITORY}/issues/{expected_issue}"
    if issue_url != expected_issue_url:
        return False
    if not isinstance(user, dict) or user.get("login") != TRANSPORT_ACTOR:
        return False
    body = comment.get("body")
    if not isinstance(body, str):
        return False
    lines = body.splitlines()
    if not lines or lines[0].strip() != _E2_EVIDENCE_MARKER:
        return False
    fields: dict[str, str] = {}
    for line in lines[1:]:
        if " = " not in line:
            continue
        key, value = line.split(" = ", 1)
        if key in fields:
            return False
        fields[key] = value
    return (
        fields.get("KEY") == fact.get("key")
        and fields.get("VALUE_JSON") == _canonical_evidence_value(fact.get("value"))
        and fields.get("AUTHORITY") == fact.get("authority")
    )


def _verify_new_blocker_identity_evidence(
    context_packet: dict[str, Any],
    github_api: GitHubApi | None,
) -> frozenset[str]:
    present = {
        str(fact.get("key")): fact
        for fact in _packet_facts(context_packet)
        if fact.get("key") in _PERMISSION_E2_KEYS
    }
    if not present or github_api is None:
        return frozenset()
    expected_issue = _packet_current_task_issue(context_packet)
    if expected_issue is None:
        return frozenset()
    proven: set[str] = set()
    for key, fact in present.items():
        if _packet_verified_fact(context_packet, key) is None:
            continue
        comment_id = _fact_issue_comment_id(fact)
        if comment_id is None:
            continue
        try:
            comment = github_api.read_comment(comment_id)
        except PersistenceError:
            continue
        if _comment_proves_fact(comment, fact, expected_issue=expected_issue):
            proven.add(key)
    return frozenset(proven)


def _read_current_pr_head(github_api: GitHubApi, pr_number: int) -> str:
    try:
        payload = github_api._request_json(f"{API_ROOT}/repos/{REPOSITORY}/pulls/{pr_number}")
    except PersistenceError:
        raise
    except Exception as exc:
        raise PersistenceError("GitHub PR freshness read failed") from exc
    if not isinstance(payload, dict):
        raise PersistenceError("GitHub PR freshness read returned non-object")
    head = payload.get("head")
    sha = head.get("sha") if isinstance(head, dict) else None
    if not isinstance(sha, str) or _SHA40.fullmatch(sha) is None:
        raise PersistenceError("GitHub PR freshness read returned invalid head SHA")
    return sha


def _packet_has_verified_terminal_pass(context_packet: dict[str, Any]) -> bool:
    results = [fact for fact in _packet_facts(context_packet) if fact.get("key") == "RESULT"]
    if len(results) != 1:
        return False
    result = results[0]
    refs = result.get("source_refs")
    return (
        result.get("class") == "E2"
        and result.get("verified") is True
        and result.get("value") == "PASS"
        and isinstance(refs, list)
        and bool(refs)
        and all(isinstance(item, str) and item for item in refs)
    )


def _context_view(context_packet: dict[str, Any] | None) -> dict[str, Any] | None:
    if context_packet is None:
        return None
    return {
        "status": str(context_packet["status"]),
        "missing_facets": list(context_packet.get("missing_facets", [])),
        "source_refs": list(context_packet.get("source_refs", [])),
    }


def _decision(
    context: dict[str, Any],
    decision: str,
    reason: str,
    learning_policy: dict[str, Any] | None,
    context_packet: dict[str, Any] | None = None,
) -> dict[str, Any]:
    result = {
        "schema": SCHEMA,
        "decision": decision,
        "reason": reason,
        "action": context["action"],
        "learning": _learning_view(learning_policy),
    }
    context_view = _context_view(context_packet)
    if context_view is not None:
        result["context"] = context_view
    return result


def evaluate_pre_action(
    context: dict[str, Any],
    *,
    learning_policy: dict[str, Any] | None = None,
    context_packet: dict[str, Any] | None = None,
    fresh_active_head: str | None = None,
    _externally_proven_e2_keys: frozenset[str] = frozenset(),
) -> dict[str, Any]:
    _validate_context(context)
    action = context["action"]
    effective_process_mutation_count = context["processMutationCountForBlocker"]
    durable_new_physical_blocker = False
    current_error_signature: str | None = None
    process_mutation_error_signature: str | None = None
    if fresh_active_head is not None and (not isinstance(fresh_active_head, str) or not fresh_active_head):
        raise PreActionError("FRESH_ACTIVE_HEAD_INVALID")
    if context_packet is None and action not in READ_ONLY_WHILE_ACTIVE:
        return _decision(context, "BLOCK", "DURABLE_CONTEXT_NOT_PROVEN", learning_policy, None)
    if context_packet is not None:
        _validate_context_packet(context_packet)
        if context_packet["status"] != "PROVEN":
            return _decision(context, "BLOCK", "DURABLE_CONTEXT_NOT_PROVEN", learning_policy, context_packet)
        facts = _packet_facts(context_packet)
        process_mutation_count_facts = [fact for fact in facts if fact.get("key") == "PROCESS_MUTATION_COUNT"]
        durable_process_mutation_count = _packet_process_mutation_count(context_packet)
        if process_mutation_count_facts and durable_process_mutation_count is None:
            return _decision(context, "BLOCK", "DURABLE_CONTEXT_NOT_PROVEN", learning_policy, context_packet)
        if durable_process_mutation_count is not None:
            effective_process_mutation_count = max(effective_process_mutation_count, durable_process_mutation_count)
        durable_new_physical_blocker = _packet_has_verified_true_fact(context_packet, "NEW_PHYSICAL_BLOCKER")
        current_error_signature = _packet_verified_string_fact(context_packet, "ERROR_SIGNATURE")
        process_mutation_error_signature = _packet_verified_string_fact(context_packet, "PROCESS_MUTATION_ERROR_SIGNATURE")
        if (
            action not in READ_ONLY_WHILE_ACTIVE
            and effective_process_mutation_count >= 1
            and context["newPhysicalBlocker"]
            and durable_new_physical_blocker
        ):
            present_identity_keys = {
                str(fact.get("key"))
                for fact in facts
                if fact.get("key") in _NEW_BLOCKER_IDENTITY_KEYS
            }
            if not present_identity_keys.issubset(_externally_proven_e2_keys):
                return _decision(
                    context,
                    "BLOCK",
                    "DURABLE_CONTEXT_EVIDENCE_SOURCE_NOT_PROVEN",
                    learning_policy,
                    context_packet,
                )
        if action == "CLAIM_PASS" and _packet_has_verified_terminal_pass(context_packet) and "RESULT" not in _externally_proven_e2_keys:
            return _decision(
                context,
                "BLOCK",
                "DURABLE_CONTEXT_EVIDENCE_SOURCE_NOT_PROVEN",
                learning_policy,
                context_packet,
            )
        packet_active_head = _packet_active_head(context_packet)
        if action not in READ_ONLY_WHILE_ACTIVE and packet_active_head is not None and fresh_active_head is None:
            return _decision(context, "BLOCK", "DURABLE_CONTEXT_NOT_PROVEN", learning_policy, context_packet)
        if fresh_active_head is not None:
            if packet_active_head is None:
                return _decision(context, "BLOCK", "DURABLE_CONTEXT_NOT_PROVEN", learning_policy, context_packet)
            if packet_active_head != fresh_active_head:
                return _decision(context, "BLOCK", "DURABLE_CONTEXT_STALE", learning_policy, context_packet)

    if action == "IMAGE_MUTATION":
        if not context["explicitOwnerImageMutationCommand"]:
            return _decision(context, "BLOCK", "OWNER_IMAGE_MUTATION_COMMAND_REQUIRED", learning_policy, context_packet)
        return _decision(context, "BLOCK", "DURABLE_OWNER_COMMAND_NOT_PROVEN", learning_policy, context_packet)
    if context["activeAttempt"] and action not in READ_ONLY_WHILE_ACTIVE:
        return _decision(context, "WAIT", "ACTIVE_ATTEMPT_OWNS_PATH", learning_policy, context_packet)
    if action == "SEARCH_ASSET" and context["exactOwnerInputProvided"]:
        return _decision(context, "BLOCK", "EXACT_OWNER_INPUT_SUPERSEDES_SEARCH", learning_policy, context_packet)
    if action == "VERIFY_PREREQUISITE" and context["prerequisiteAlreadyProven"]:
        return _decision(context, "BLOCK", "PREREQUISITE_ALREADY_PROVEN", learning_policy, context_packet)
    if action == "PROCESS_MUTATION" and not context["provenProcessBlocker"]:
        return _decision(context, "BLOCK", "PROCESS_MUTATION_REQUIRES_PROVEN_PROCESS_BLOCKER", learning_policy, context_packet)
    if action not in READ_ONLY_WHILE_ACTIVE and effective_process_mutation_count >= 1 and context["newPhysicalBlocker"]:
        if not durable_new_physical_blocker:
            return _decision(context, "BLOCK", "DURABLE_NEW_BLOCKER_NOT_PROVEN", learning_policy, context_packet)
        if current_error_signature is None or process_mutation_error_signature is None:
            return _decision(context, "BLOCK", "DURABLE_NEW_BLOCKER_SIGNATURE_NOT_PROVEN", learning_policy, context_packet)
        if current_error_signature == process_mutation_error_signature:
            return _decision(context, "BLOCK", "DURABLE_NEW_BLOCKER_NOT_DISTINCT", learning_policy, context_packet)
    if action not in READ_ONLY_WHILE_ACTIVE and effective_process_mutation_count >= 1 and not context["newPhysicalBlocker"]:
        return _decision(context, "BLOCK", "REPEAT_PROCESS_MUTATION_REQUIRES_NEW_BLOCKER", learning_policy, context_packet)
    if action == "REQUEST_OWNER_ACTION":
        if not context["provenExternalBoundary"]:
            return _decision(context, "BLOCK", "OWNER_IS_NOT_A_COURIER", learning_policy, context_packet)
        return _decision(context, "OWNER_REQUIRED", "PROVEN_EXTERNAL_BOUNDARY", learning_policy, context_packet)
    if action == "CLAIM_PASS" and not context["freshVerificationEvidence"]:
        return _decision(context, "BLOCK", "FRESH_VERIFICATION_REQUIRED", learning_policy, context_packet)
    if action == "CLAIM_PASS" and context_packet is not None and not _packet_has_verified_terminal_pass(context_packet):
        return _decision(context, "BLOCK", "DURABLE_TERMINAL_EVIDENCE_NOT_PROVEN", learning_policy, context_packet)
    if not context["directlyAdvancesPhysicalResult"] and action not in READ_ONLY_WHILE_ACTIVE:
        return _decision(context, "BLOCK", "NO_DIRECT_PRODUCT_PROGRESS", learning_policy, context_packet)
    return _decision(context, "ALLOW", "PRE_ACTION_GATE_PASS", learning_policy, context_packet)


def evaluate_pre_action_with_github_freshness(
    context: dict[str, Any],
    *,
    learning_policy: dict[str, Any] | None = None,
    context_packet: dict[str, Any] | None = None,
    github_api: GitHubApi | None = None,
) -> dict[str, Any]:
    _validate_context(context)
    action = context["action"]
    if context_packet is None or action in READ_ONLY_WHILE_ACTIVE:
        return evaluate_pre_action(context, learning_policy=learning_policy, context_packet=context_packet)
    _validate_context_packet(context_packet)
    if context_packet["status"] != "PROVEN":
        return evaluate_pre_action(context, learning_policy=learning_policy, context_packet=context_packet)
    externally_proven_e2_keys = _verify_new_blocker_identity_evidence(context_packet, github_api)
    facts = _packet_facts(context_packet)
    present_identity_keys = {
        str(fact.get("key"))
        for fact in facts
        if fact.get("key") in _NEW_BLOCKER_IDENTITY_KEYS
    }
    if context["newPhysicalBlocker"] and present_identity_keys and not present_identity_keys.issubset(externally_proven_e2_keys):
        return _decision(
            context,
            "BLOCK",
            "DURABLE_CONTEXT_EVIDENCE_SOURCE_NOT_PROVEN",
            learning_policy,
            context_packet,
        )
    if action == "CLAIM_PASS" and _packet_has_verified_terminal_pass(context_packet) and "RESULT" not in externally_proven_e2_keys:
        return _decision(
            context,
            "BLOCK",
            "DURABLE_CONTEXT_EVIDENCE_SOURCE_NOT_PROVEN",
            learning_policy,
            context_packet,
        )
    packet_active_head = _packet_active_head(context_packet)
    if packet_active_head is None:
        return evaluate_pre_action(
            context,
            learning_policy=learning_policy,
            context_packet=context_packet,
            _externally_proven_e2_keys=externally_proven_e2_keys,
        )
    pr_number = _packet_active_head_pr(context_packet)
    if pr_number is None or github_api is None:
        return _decision(context, "BLOCK", "DURABLE_CONTEXT_FRESHNESS_SOURCE_NOT_PROVEN", learning_policy, context_packet)
    try:
        fresh_active_head = _read_current_pr_head(github_api, pr_number)
    except PersistenceError:
        return _decision(context, "BLOCK", "DURABLE_CONTEXT_FRESHNESS_SOURCE_NOT_PROVEN", learning_policy, context_packet)
    return evaluate_pre_action(
        context,
        learning_policy=learning_policy,
        context_packet=context_packet,
        fresh_active_head=fresh_active_head,
        _externally_proven_e2_keys=externally_proven_e2_keys,
    )


def _load_json_object(path: Path, error: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PreActionError(error) from exc
    if not isinstance(payload, dict):
        raise PreActionError(error)
    return payload


def _load_context(path: Path) -> dict[str, Any]:
    return _load_json_object(path, "PRE_ACTION_CONTEXT_INVALID:UNREADABLE_JSON")


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail-closed ZORR pre-action execution gate.")
    parser.add_argument("--context-path", required=True, type=Path)
    parser.add_argument("--context-packet-path", type=Path)
    parser.add_argument("--fresh-active-head")
    parser.add_argument("--archive-root", type=Path)
    parser.add_argument("--query")
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()
    if (args.archive_root is None) != (args.query is None):
        raise PreActionError("PRE_ACTION_LEARNING_ARGS_INCOMPLETE")
    if args.limit < 1:
        raise PreActionError("PRE_ACTION_CONTEXT_INVALID:LIMIT")
    context = _load_context(args.context_path)
    context_packet = None
    if args.context_packet_path is not None:
        context_packet = _load_json_object(args.context_packet_path, "CONTEXT_PACKET_INVALID")
    policy = None
    if args.archive_root is not None and args.query is not None:
        policy = build_learning_policy(args.archive_root, args.query, limit=args.limit)
    github_api = None
    github_token = os.environ.get("GITHUB_TOKEN")
    if github_token:
        try:
            github_api = GitHubApi(github_token)
        except PersistenceError:
            github_api = None
    result = evaluate_pre_action_with_github_freshness(
        context,
        learning_policy=policy,
        context_packet=context_packet,
        github_api=github_api,
    )
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))
    return 0 if result["decision"] == "ALLOW" else 2


if __name__ == "__main__":
    raise SystemExit(main())