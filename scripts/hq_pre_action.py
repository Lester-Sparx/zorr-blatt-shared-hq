from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from scripts.hq_unified_archive import build_learning_policy


SCHEMA = "ZB_PRE_ACTION_DECISION_V1"
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


def _decision(
    context: dict[str, Any],
    decision: str,
    reason: str,
    learning_policy: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "decision": decision,
        "reason": reason,
        "action": context["action"],
        "learning": _learning_view(learning_policy),
    }


def evaluate_pre_action(
    context: dict[str, Any],
    *,
    learning_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    _validate_context(context)
    action = context["action"]

    if action == "IMAGE_MUTATION" and not context["explicitOwnerImageMutationCommand"]:
        return _decision(context, "BLOCK", "OWNER_IMAGE_MUTATION_COMMAND_REQUIRED", learning_policy)

    if context["activeAttempt"] and action not in READ_ONLY_WHILE_ACTIVE:
        return _decision(context, "WAIT", "ACTIVE_ATTEMPT_OWNS_PATH", learning_policy)

    if action == "SEARCH_ASSET" and context["exactOwnerInputProvided"]:
        return _decision(context, "BLOCK", "EXACT_OWNER_INPUT_SUPERSEDES_SEARCH", learning_policy)

    if action == "VERIFY_PREREQUISITE" and context["prerequisiteAlreadyProven"]:
        return _decision(context, "BLOCK", "PREREQUISITE_ALREADY_PROVEN", learning_policy)

    if action == "PROCESS_MUTATION" and not context["provenProcessBlocker"]:
        return _decision(context, "BLOCK", "PROCESS_MUTATION_REQUIRES_PROVEN_PROCESS_BLOCKER", learning_policy)

    if (
        action == "PROCESS_MUTATION"
        and context["processMutationCountForBlocker"] >= 1
        and not context["newPhysicalBlocker"]
    ):
        return _decision(context, "BLOCK", "REPEAT_PROCESS_MUTATION_REQUIRES_NEW_BLOCKER", learning_policy)

    if action == "REQUEST_OWNER_ACTION":
        if not context["provenExternalBoundary"]:
            return _decision(context, "BLOCK", "OWNER_IS_NOT_A_COURIER", learning_policy)
        return _decision(context, "OWNER_REQUIRED", "PROVEN_EXTERNAL_BOUNDARY", learning_policy)

    if action == "CLAIM_PASS" and not context["freshVerificationEvidence"]:
        return _decision(context, "BLOCK", "FRESH_VERIFICATION_REQUIRED", learning_policy)

    if not context["directlyAdvancesPhysicalResult"] and action not in READ_ONLY_WHILE_ACTIVE:
        return _decision(context, "BLOCK", "NO_DIRECT_PRODUCT_PROGRESS", learning_policy)

    return _decision(context, "ALLOW", "PRE_ACTION_GATE_PASS", learning_policy)


def _load_context(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PreActionError("PRE_ACTION_CONTEXT_INVALID:UNREADABLE_JSON") from exc
    if not isinstance(payload, dict):
        raise PreActionError("PRE_ACTION_CONTEXT_INVALID:OBJECT_REQUIRED")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail-closed ZORR pre-action execution gate.")
    parser.add_argument("--context-path", required=True, type=Path)
    parser.add_argument("--archive-root", type=Path)
    parser.add_argument("--query")
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()

    if (args.archive_root is None) != (args.query is None):
        raise PreActionError("PRE_ACTION_LEARNING_ARGS_INCOMPLETE")
    if args.limit < 1:
        raise PreActionError("PRE_ACTION_CONTEXT_INVALID:LIMIT")

    context = _load_context(args.context_path)
    policy = None
    if args.archive_root is not None and args.query is not None:
        policy = build_learning_policy(args.archive_root, args.query, limit=args.limit)
    result = evaluate_pre_action(context, learning_policy=policy)
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))
    return 0 if result["decision"] == "ALLOW" else 2


if __name__ == "__main__":
    raise SystemExit(main())
