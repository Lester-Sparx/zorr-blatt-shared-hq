from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from scripts.hq_unified_archive import build_learning_policy
except ModuleNotFoundError:
    from hq_unified_archive import build_learning_policy


SCHEMA = "ZB_PRE_ACTION_DECISION_V1"
CONTEXT_PACKET_SCHEMA = "ZB_CONTEXT_PACKET_V1"
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
    status = context_packet.get("status")
    if status not in {"PROVEN", "NOT_PROVEN"}:
        raise PreActionError("CONTEXT_PACKET_INVALID")
    missing_facets = context_packet.get("missing_facets", [])
    source_refs = context_packet.get("source_refs", [])
    if not isinstance(missing_facets, list) or not all(isinstance(item, str) and item for item in missing_facets):
        raise PreActionError("CONTEXT_PACKET_INVALID")
    if not isinstance(source_refs, list) or not all(isinstance(item, str) and item for item in source_refs):
        raise PreActionError("CONTEXT_PACKET_INVALID")
    if status == "PROVEN" and missing_facets:
        raise PreActionError("CONTEXT_PACKET_INVALID")


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
) -> dict[str, Any]:
    _validate_context(context)
    if context_packet is not None:
        _validate_context_packet(context_packet)
        if context_packet["status"] != "PROVEN":
            return _decision(
                context,
                "BLOCK",
                "DURABLE_CONTEXT_NOT_PROVEN",
                learning_policy,
                context_packet,
            )

    action = context["action"]

    if action == "IMAGE_MUTATION" and not context["explicitOwnerImageMutationCommand"]:
        return _decision(context, "BLOCK", "OWNER_IMAGE_MUTATION_COMMAND_REQUIRED", learning_policy, context_packet)

    if context["activeAttempt"] and action not in READ_ONLY_WHILE_ACTIVE:
        return _decision(context, "WAIT", "ACTIVE_ATTEMPT_OWNS_PATH", learning_policy, context_packet)

    if action == "SEARCH_ASSET" and context["exactOwnerInputProvided"]:
        return _decision(context, "BLOCK", "EXACT_OWNER_INPUT_SUPERSEDES_SEARCH", learning_policy, context_packet)

    if action == "VERIFY_PREREQUISITE" and context["prerequisiteAlreadyProven"]:
        return _decision(context, "BLOCK", "PREREQUISITE_ALREADY_PROVEN", learning_policy, context_packet)

    if action == "PROCESS_MUTATION" and not context["provenProcessBlocker"]:
        return _decision(
            context,
            "BLOCK",
            "PROCESS_MUTATION_REQUIRES_PROVEN_PROCESS_BLOCKER",
            learning_policy,
            context_packet,
        )

    if (
        action == "PROCESS_MUTATION"
        and context["processMutationCountForBlocker"] >= 1
        and not context["newPhysicalBlocker"]
    ):
        return _decision(
            context,
            "BLOCK",
            "REPEAT_PROCESS_MUTATION_REQUIRES_NEW_BLOCKER",
            learning_policy,
            context_packet,
        )

    if action == "REQUEST_OWNER_ACTION":
        if not context["provenExternalBoundary"]:
            return _decision(context, "BLOCK", "OWNER_IS_NOT_A_COURIER", learning_policy, context_packet)
        return _decision(context, "OWNER_REQUIRED", "PROVEN_EXTERNAL_BOUNDARY", learning_policy, context_packet)

    if action == "CLAIM_PASS" and not context["freshVerificationEvidence"]:
        return _decision(context, "BLOCK", "FRESH_VERIFICATION_REQUIRED", learning_policy, context_packet)

    if not context["directlyAdvancesPhysicalResult"] and action not in READ_ONLY_WHILE_ACTIVE:
        return _decision(context, "BLOCK", "NO_DIRECT_PRODUCT_PROGRESS", learning_policy, context_packet)

    return _decision(context, "ALLOW", "PRE_ACTION_GATE_PASS", learning_policy, context_packet)


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
    result = evaluate_pre_action(
        context,
        learning_policy=policy,
        context_packet=context_packet,
    )
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))
    return 0 if result["decision"] == "ALLOW" else 2


if __name__ == "__main__":
    raise SystemExit(main())
