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
_AUTHORITY_SUBJECT_KEYS = (
    "MESSAGE_ID",
    "CORRELATION_ID",
    "TASK_ID",
    "TASK_REVISION",
    "BASE_SHA",
)
_AUTHORITY_REF_KEY = "AUTHORITY_REF"
_AUTHORITY_MARKER = "ZB_AGENT_TASK_R03_V1"
_AUTHORITY_ISSUE_URL = "https://api.github.com/repos/Lester-Sparx/zorr-blatt-shared-hq/issues/111"
_AUTHORITY_ACTOR = "Lester-Sparx"


def evaluate_pre_action(context, **kwargs):
    if context.get("action") == "VERIFY_PREREQUISITE":
        context = dict(context)
        context["prerequisiteAlreadyProven"] = False
        context["directlyAdvancesPhysicalResult"] = True
    return _original_evaluate_pre_action(context, **kwargs)


def _anchor_values(context_packet):
    if not isinstance(context_packet, dict):
        return None
    anchors = context_packet.get("mandatory_anchors")
    if not isinstance(anchors, list):
        return None
    values = {}
    for item in anchors:
        if not isinstance(item, dict) or not isinstance(item.get("key"), str):
            continue
        key = item["key"]
        if key in values:
            return None
        values[key] = item.get("value")
    return values


def _parse_comment_fields(body):
    if not isinstance(body, str):
        return None
    lines = body.splitlines()
    if not lines:
        return None
    fields = {}
    for line in lines[1:]:
        if " = " not in line:
            continue
        key, value = line.split(" = ", 1)
        if key in fields:
            return None
        fields[key] = value
    return lines[0].strip(), fields


def _terminal_authority_status(context_packet, github_api):
    anchor_values = _anchor_values(context_packet)
    if anchor_values is None or github_api is None:
        return "DURABLE_CONTEXT_AUTHORITY_SUBJECT_NOT_PROVEN"
    if any(key not in anchor_values for key in _AUTHORITY_SUBJECT_KEYS):
        return "DURABLE_CONTEXT_AUTHORITY_SUBJECT_NOT_PROVEN"
    authority_ref = anchor_values.get(_AUTHORITY_REF_KEY)
    if not isinstance(authority_ref, str):
        return "DURABLE_CONTEXT_AUTHORITY_SUBJECT_NOT_PROVEN"
    match = _ISSUE_COMMENT_REF.fullmatch(authority_ref)
    if match is None:
        return "DURABLE_CONTEXT_AUTHORITY_SUBJECT_NOT_PROVEN"
    try:
        comment = github_api.read_comment(int(match.group(1)))
    except Exception:
        return "DURABLE_CONTEXT_AUTHORITY_SUBJECT_NOT_PROVEN"
    if not isinstance(comment, dict):
        return "DURABLE_CONTEXT_AUTHORITY_SUBJECT_NOT_PROVEN"
    user = comment.get("user")
    if (
        comment.get("issue_url") != _AUTHORITY_ISSUE_URL
        or not isinstance(user, dict)
        or user.get("login") != _AUTHORITY_ACTOR
        or comment.get("author_association") != "OWNER"
        or not comment.get("created_at")
        or comment.get("created_at") != comment.get("updated_at")
    ):
        return "DURABLE_CONTEXT_AUTHORITY_SUBJECT_NOT_PROVEN"
    parsed = _parse_comment_fields(comment.get("body"))
    if parsed is None:
        return "DURABLE_CONTEXT_AUTHORITY_SUBJECT_NOT_PROVEN"
    marker, fields = parsed
    if marker != _AUTHORITY_MARKER:
        return "DURABLE_CONTEXT_AUTHORITY_SUBJECT_NOT_PROVEN"
    for key in _AUTHORITY_SUBJECT_KEYS:
        if fields.get(key) != str(anchor_values[key]):
            return "DURABLE_CONTEXT_AUTHORITY_SUBJECT_MISMATCH"
    return None


def _terminal_subject_matches(context_packet, github_api) -> bool:
    anchor_values = _anchor_values(context_packet)
    if anchor_values is None or github_api is None:
        return False
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
    parsed = _parse_comment_fields(body)
    if parsed is None:
        return False
    _, fields = parsed
    for key in _TERMINAL_SUBJECT_KEYS:
        expected = str(anchor_values[key])
        if fields.get(key) != expected:
            return False
    return True


def evaluate_pre_action_with_github_freshness(context, **kwargs):
    result = _original_evaluate_pre_action_with_github_freshness(context, **kwargs)
    if context.get("action") == "CLAIM_PASS" and result.get("decision") == "ALLOW":
        authority_reason = _terminal_authority_status(kwargs.get("context_packet"), kwargs.get("github_api"))
        if authority_reason is not None:
            return _core._decision(
                context,
                "BLOCK",
                authority_reason,
                kwargs.get("learning_policy"),
                kwargs.get("context_packet"),
            )
        if not _terminal_subject_matches(kwargs.get("context_packet"), kwargs.get("github_api")):
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
