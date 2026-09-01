from __future__ import annotations

import re

try:
    from scripts import hq_pre_action_core as _core
except ModuleNotFoundError:  # direct script mode
    import hq_pre_action_core as _core


for _name in dir(_core):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_core, _name)


_original_evaluate_pre_action = _core.evaluate_pre_action
_original_evaluate_pre_action_with_github_freshness = _core.evaluate_pre_action_with_github_freshness
_ISSUE_COMMENT_REF = re.compile(r"^github:issue-comment:([1-9][0-9]*)$")
_TERMINAL_SUBJECT_KEYS = (
    "MESSAGE_ID",
    "CORRELATION_ID",
    "TASK_ID",
    "TASK_REVISION",
    "BASE_SHA",
    "LESTER_EXECUTION_ID",
    "DUNCAN_EXECUTION_ID",
)


def evaluate_pre_action(context, **kwargs):
    if context.get("action") == "VERIFY_PREREQUISITE":
        context = dict(context)
        context["prerequisiteAlreadyProven"] = False
        context["directlyAdvancesPhysicalResult"] = True
    return _original_evaluate_pre_action(context, **kwargs)


def _terminal_subject_matches(context_packet, github_api) -> bool:
    if not isinstance(context_packet, dict) or github_api is None:
        return False
    anchors = context_packet.get("mandatory_anchors")
    if not isinstance(anchors, list):
        return False
    anchor_values = {
        item.get("key"): item.get("value")
        for item in anchors
        if isinstance(item, dict) and isinstance(item.get("key"), str)
    }
    if any(key not in anchor_values for key in _TERMINAL_SUBJECT_KEYS):
        return False
    state = context_packet.get("current_state")
    facts = state.get("facts") if isinstance(state, dict) else None
    if not isinstance(facts, list):
        return False
    results = [fact for fact in facts if isinstance(fact, dict) and fact.get("key") == "RESULT" and fact.get("value") == "PASS"]
    if len(results) != 1:
        return False
    refs = results[0].get("source_refs")
    if not isinstance(refs, list):
        return False
    ids = []
    for ref in refs:
        if not isinstance(ref, str):
            continue
        match = _ISSUE_COMMENT_REF.fullmatch(ref)
        if match is not None:
            ids.append(int(match.group(1)))
    if len(ids) != 1:
        return False
    try:
        comment = github_api.read_comment(ids[0])
    except Exception:
        return False
    body = comment.get("body") if isinstance(comment, dict) else None
    if not isinstance(body, str):
        return False
    fields = {}
    for line in body.splitlines()[1:]:
        if " = " not in line:
            continue
        key, value = line.split(" = ", 1)
        if key in fields:
            return False
        fields[key] = value
    for key in _TERMINAL_SUBJECT_KEYS:
        expected = str(anchor_values[key])
        if fields.get(key) != expected:
            return False
    return True


def evaluate_pre_action_with_github_freshness(context, **kwargs):
    result = _original_evaluate_pre_action_with_github_freshness(context, **kwargs)
    if (
        context.get("action") == "CLAIM_PASS"
        and result.get("decision") == "ALLOW"
        and not _terminal_subject_matches(kwargs.get("context_packet"), kwargs.get("github_api"))
    ):
        return _core._decision(
            context,
            "BLOCK",
            "DURABLE_CONTEXT_EVIDENCE_SUBJECT_MISMATCH",
            kwargs.get("learning_policy"),
            kwargs.get("context_packet"),
        )
    return result


_core.evaluate_pre_action = evaluate_pre_action
_core.evaluate_pre_action_with_github_freshness = evaluate_pre_action_with_github_freshness


if __name__ == "__main__":
    raise SystemExit(_core.main())
