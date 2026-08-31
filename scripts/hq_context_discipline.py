from __future__ import annotations

from collections import defaultdict
import json
from pathlib import Path
from typing import Any

try:
    from scripts.hq_unified_archive import build_learning_policy, build_restore_packet
except ModuleNotFoundError:
    from hq_unified_archive import build_learning_policy, build_restore_packet


FACT_SCHEMA = "ZB_CONTEXT_FACT_V1"
CURRENT_STATE_SCHEMA = "ZB_CONTEXT_CURRENT_STATE_V1"
PACKET_SCHEMA = "ZB_CONTEXT_PACKET_V1"
DELTA_SCHEMA = "ZB_CONTEXT_DELTA_V1"
HANDOFF_SCHEMA = "ZB_CONTEXT_HANDOFF_V1"
CLASSES = {"E0", "E1", "E2", "E3"}


class ContextDisciplineError(RuntimeError):
    pass


def normalize_fact(fact: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(fact, dict) or fact.get("schema") != FACT_SCHEMA:
        raise ContextDisciplineError("CONTEXT_FACT_INVALID")

    required = {
        "fact_id",
        "class",
        "key",
        "value",
        "exclusive",
        "verified",
        "authority",
        "created_at",
        "scope_tags",
        "source_refs",
        "supersedes",
    }
    missing = sorted(required - set(fact))
    if missing:
        raise ContextDisciplineError("CONTEXT_FACT_MISSING:" + ",".join(missing))

    if not isinstance(fact["fact_id"], str) or not fact["fact_id"]:
        raise ContextDisciplineError("CONTEXT_FACT_ID_INVALID")
    if fact["class"] not in CLASSES:
        raise ContextDisciplineError("CONTEXT_FACT_CLASS_INVALID")
    if not isinstance(fact["key"], str) or not fact["key"]:
        raise ContextDisciplineError("CONTEXT_FACT_KEY_INVALID")
    if type(fact["exclusive"]) is not bool or type(fact["verified"]) is not bool:
        raise ContextDisciplineError("CONTEXT_FACT_BOOLEAN_INVALID")
    if fact["class"] == "E2" and not fact["verified"]:
        raise ContextDisciplineError("CONTEXT_FACT_E2_REQUIRES_VERIFIED")
    if not isinstance(fact["authority"], str) or not fact["authority"]:
        raise ContextDisciplineError("CONTEXT_FACT_AUTHORITY_INVALID")
    if not isinstance(fact["created_at"], str):
        raise ContextDisciplineError("CONTEXT_FACT_CREATED_AT_INVALID")
    if not isinstance(fact["scope_tags"], list) or not all(
        isinstance(item, str) and item for item in fact["scope_tags"]
    ):
        raise ContextDisciplineError("CONTEXT_FACT_SCOPE_INVALID")
    if not isinstance(fact["source_refs"], list) or not all(
        isinstance(item, str) and item for item in fact["source_refs"]
    ):
        raise ContextDisciplineError("CONTEXT_FACT_SOURCE_INVALID")
    if fact["class"] == "E2" and not fact["source_refs"]:
        raise ContextDisciplineError("CONTEXT_FACT_E2_REQUIRES_EVIDENCE")
    if not isinstance(fact["supersedes"], list) or not all(
        isinstance(item, str) and item for item in fact["supersedes"]
    ):
        raise ContextDisciplineError("CONTEXT_FACT_SUPERSEDES_INVALID")

    return {
        "schema": FACT_SCHEMA,
        "fact_id": fact["fact_id"],
        "class": fact["class"],
        "key": fact["key"],
        "value": fact["value"],
        "exclusive": fact["exclusive"],
        "verified": fact["verified"],
        "authority": fact["authority"],
        "created_at": fact["created_at"],
        "scope_tags": list(fact["scope_tags"]),
        "source_refs": list(fact["source_refs"]),
        "supersedes": list(fact["supersedes"]),
    }


def _scope_matches(fact: dict[str, Any], scope_tags: set[str] | None) -> bool:
    if scope_tags is None:
        return True
    tags = set(fact["scope_tags"])
    if tags.intersection(scope_tags):
        return True
    if fact["authority"] == "OWNER" and tags.intersection({"ZORR", "GLOBAL"}):
        return True
    return False


def _project_fact(fact: dict[str, Any]) -> dict[str, Any]:
    projected = dict(fact)
    if projected["class"] == "E3":
        projected["value"] = None
        projected["raw_pointer_only"] = True
    return projected


def _validate_supersession_authority(facts: list[dict[str, Any]]) -> None:
    by_id = {fact["fact_id"]: fact for fact in facts}
    for superseder in facts:
        for target_id in superseder["supersedes"]:
            target = by_id.get(target_id)
            if target is None:
                continue
            if target["class"] == "E2" and superseder["class"] != "E2":
                raise ContextDisciplineError("CONTEXT_SUPERSESSION_AUTHORITY_INVALID")
            if target["authority"] == "OWNER" and superseder["authority"] != "OWNER":
                raise ContextDisciplineError("CONTEXT_SUPERSESSION_AUTHORITY_INVALID")


def project_current_state(
    facts: list[dict[str, Any]],
    *,
    scope_tags: set[str] | None = None,
) -> dict[str, Any]:
    if not isinstance(facts, list):
        raise ContextDisciplineError("CONTEXT_FACT_LIST_REQUIRED")
    if scope_tags is not None and (
        not isinstance(scope_tags, set)
        or not all(isinstance(item, str) and item for item in scope_tags)
    ):
        raise ContextDisciplineError("CONTEXT_SCOPE_TAGS_INVALID")

    normalized = [normalize_fact(fact) for fact in facts]
    ids = [fact["fact_id"] for fact in normalized]
    if len(ids) != len(set(ids)):
        raise ContextDisciplineError("CONTEXT_FACT_ID_DUPLICATE")

    live = [fact for fact in normalized if fact["class"] != "E0"]
    _validate_supersession_authority(live)
    superseded_ids = {
        superseded_id
        for fact in live
        for superseded_id in fact["supersedes"]
    }
    candidates = [
        fact
        for fact in live
        if fact["fact_id"] not in superseded_ids and _scope_matches(fact, scope_tags)
    ]

    exclusive_by_key: dict[str, list[dict[str, Any]]] = defaultdict(list)
    nonexclusive: list[dict[str, Any]] = []
    for fact in candidates:
        if fact["exclusive"]:
            exclusive_by_key[fact["key"]].append(fact)
        else:
            nonexclusive.append(fact)

    selected: list[dict[str, Any]] = list(nonexclusive)
    for key, group in exclusive_by_key.items():
        distinct_values = []
        for fact in group:
            if fact["value"] not in distinct_values:
                distinct_values.append(fact["value"])
        if len(distinct_values) > 1:
            raise ContextDisciplineError(f"DURABLE_CONTEXT_NOT_PROVEN:CONFLICT:{key}")
        winner = max(group, key=lambda item: (item["created_at"], item["fact_id"]))
        selected.append(winner)

    projected = [_project_fact(fact) for fact in selected]
    projected.sort(key=lambda item: (item["key"], item["created_at"], item["fact_id"]))
    return {
        "schema": CURRENT_STATE_SCHEMA,
        "facts": projected,
    }


def _validate_anchor(anchor: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(anchor, dict):
        raise ContextDisciplineError("CONTEXT_ANCHOR_INVALID")
    key = anchor.get("key")
    if not isinstance(key, str) or not key:
        raise ContextDisciplineError("CONTEXT_ANCHOR_KEY_INVALID")
    if "value" not in anchor:
        raise ContextDisciplineError("CONTEXT_ANCHOR_VALUE_MISSING")
    return dict(anchor)


def _validate_jit_query(query: dict[str, Any]) -> tuple[str, str]:
    if not isinstance(query, dict) or set(query) != {"facet", "query"}:
        raise ContextDisciplineError("CONTEXT_JIT_QUERY_INVALID")
    facet = query.get("facet")
    text = query.get("query")
    if not isinstance(facet, str) or not facet or not isinstance(text, str) or not text.strip():
        raise ContextDisciplineError("CONTEXT_JIT_QUERY_INVALID")
    return facet, text


def build_context_packet(
    archive_root: Path,
    *,
    mandatory_anchors: list[dict[str, Any]],
    current_state: dict[str, Any],
    jit_queries: list[dict[str, str]],
    lesson_query: str | None = None,
) -> dict[str, Any]:
    if not isinstance(current_state, dict) or current_state.get("schema") != CURRENT_STATE_SCHEMA:
        raise ContextDisciplineError("CONTEXT_CURRENT_STATE_INVALID")
    if not isinstance(current_state.get("facts"), list):
        raise ContextDisciplineError("CONTEXT_CURRENT_STATE_INVALID")
    if not isinstance(mandatory_anchors, list) or not isinstance(jit_queries, list):
        raise ContextDisciplineError("CONTEXT_PACKET_INPUT_INVALID")
    if lesson_query is not None and (not isinstance(lesson_query, str) or not lesson_query.strip()):
        raise ContextDisciplineError("CONTEXT_LESSON_QUERY_INVALID")

    anchors = [_validate_anchor(anchor) for anchor in mandatory_anchors]
    facet_results: dict[str, list[dict[str, Any]]] = {}
    missing_facets: list[str] = []
    seen_facets: set[str] = set()
    source_refs: set[str] = set()

    for raw_query in jit_queries:
        facet, query = _validate_jit_query(raw_query)
        if facet in seen_facets:
            raise ContextDisciplineError("CONTEXT_JIT_FACET_DUPLICATE:" + facet)
        seen_facets.add(facet)
        restored = build_restore_packet(Path(archive_root), query, limit=1)
        results = list(restored.get("results") or []) if isinstance(restored, dict) else []
        if not results:
            facet_results[facet] = []
            missing_facets.append(facet)
            continue
        compact_results: list[dict[str, Any]] = []
        for result in results:
            compact = {
                "raw_sha256": str(result.get("raw_sha256") or ""),
                "subject_kind": result.get("subject_kind"),
                "subject_number": result.get("subject_number"),
                "subject_title": str(result.get("subject_title") or ""),
                "body_excerpt": str(result.get("body_excerpt") or ""),
                "source_url": str(result.get("source_url") or ""),
                "created_at": str(result.get("created_at") or ""),
            }
            compact_results.append(compact)
            if compact["raw_sha256"]:
                source_refs.add("sha256:" + compact["raw_sha256"])
            if compact["source_url"]:
                source_refs.add(compact["source_url"])
        facet_results[facet] = compact_results

    for fact in current_state["facts"]:
        if not isinstance(fact, dict):
            raise ContextDisciplineError("CONTEXT_CURRENT_STATE_INVALID")
        for source_ref in fact.get("source_refs", []):
            if isinstance(source_ref, str) and source_ref:
                source_refs.add(source_ref)

    learning = None
    if lesson_query is not None:
        learning = build_learning_policy(Path(archive_root), lesson_query)
        if learning.get("status") == "PROVEN":
            for lesson in learning.get("lessons", []):
                if isinstance(lesson, dict):
                    for evidence_ref in lesson.get("evidence", []):
                        if isinstance(evidence_ref, str) and evidence_ref:
                            source_refs.add(evidence_ref)

    packet = {
        "schema": PACKET_SCHEMA,
        "status": "PROVEN" if not missing_facets else "NOT_PROVEN",
        "mandatory_anchors": anchors,
        "current_state": current_state,
        "jit_facets": {key: facet_results[key] for key in sorted(facet_results)},
        "missing_facets": sorted(missing_facets),
        "source_refs": sorted(source_refs),
    }
    if learning is not None:
        packet["learning"] = learning
    return packet


def _state_values(state: dict[str, Any]) -> dict[str, list[Any]]:
    if not isinstance(state, dict) or state.get("schema") != CURRENT_STATE_SCHEMA:
        raise ContextDisciplineError("CONTEXT_CURRENT_STATE_INVALID")
    facts = state.get("facts")
    if not isinstance(facts, list):
        raise ContextDisciplineError("CONTEXT_CURRENT_STATE_INVALID")
    values: dict[str, list[Any]] = defaultdict(list)
    for fact in facts:
        if not isinstance(fact, dict) or not isinstance(fact.get("key"), str):
            raise ContextDisciplineError("CONTEXT_CURRENT_STATE_INVALID")
        value = fact.get("value")
        if value not in values[fact["key"]]:
            values[fact["key"]].append(value)
    for key in values:
        values[key].sort(key=lambda value: json.dumps(value, sort_keys=True, ensure_ascii=False, default=str))
    return dict(values)


def diff_current_state(previous: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    before = _state_values(previous)
    after = _state_values(current)
    changed: list[dict[str, Any]] = []
    for key in sorted(set(before) | set(after)):
        old_values = before.get(key, [])
        new_values = after.get(key, [])
        if old_values == new_values:
            continue
        old_value: Any = old_values[0] if len(old_values) == 1 else old_values or None
        new_value: Any = new_values[0] if len(new_values) == 1 else new_values or None
        changed.append({"key": key, "old": old_value, "new": new_value})
    return {"schema": DELTA_SCHEMA, "changed": changed}


def _render_value(value: Any) -> str:
    if value is None:
        return "<CLEARED>"
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return str(value)


def render_owner_delta(
    delta: dict[str, Any],
    *,
    blocker: str | None,
    evidence: list[str],
    next_action: str | None,
) -> str:
    if not isinstance(delta, dict) or delta.get("schema") != DELTA_SCHEMA:
        raise ContextDisciplineError("CONTEXT_DELTA_INVALID")
    changed = delta.get("changed")
    if not isinstance(changed, list):
        raise ContextDisciplineError("CONTEXT_DELTA_INVALID")
    if blocker is not None and (not isinstance(blocker, str) or not blocker):
        raise ContextDisciplineError("CONTEXT_BLOCKER_INVALID")
    if not isinstance(evidence, list) or not all(isinstance(item, str) and item for item in evidence):
        raise ContextDisciplineError("CONTEXT_EVIDENCE_INVALID")
    if next_action is not None and (not isinstance(next_action, str) or not next_action):
        raise ContextDisciplineError("CONTEXT_NEXT_ACTION_INVALID")

    if not changed:
        return "NO DELTA." + (f" BLOCKER = {blocker}" if blocker else "")

    rendered_changes = []
    for item in changed:
        if not isinstance(item, dict) or not isinstance(item.get("key"), str) or "new" not in item:
            raise ContextDisciplineError("CONTEXT_DELTA_INVALID")
        rendered_changes.append(f"{item['key']}={_render_value(item['new'])}")
    lines = ["DELTA: " + "; ".join(rendered_changes)]
    if blocker:
        lines.append("BLOCKER: " + blocker)
    if evidence:
        lines.append("EVIDENCE: " + " | ".join(evidence))
    if next_action:
        lines.append("NEXT: " + next_action)
    return "\n".join(lines)


def _single_state_value(current_state: dict[str, Any], key: str) -> Any:
    values = _state_values(current_state).get(key, [])
    if len(values) > 1:
        raise ContextDisciplineError("HANDOFF_STATE_AMBIGUOUS:" + key)
    return values[0] if values else None


def _validate_string_list(value: Any, error: str, *, allow_empty: bool = True) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise ContextDisciplineError(error)
    if not allow_empty and not value:
        raise ContextDisciplineError(error)
    return list(value)


def build_handoff(
    *,
    role_or_engine: str,
    current_goal: str,
    task_or_correlation: str,
    authoritative_main: str,
    current_state: dict[str, Any],
    open_gaps: list[str],
    lesson_refs: list[str],
    next_action: str,
    source_refs: list[str],
) -> dict[str, Any]:
    for value, error in (
        (role_or_engine, "HANDOFF_ROLE_INVALID"),
        (current_goal, "HANDOFF_GOAL_INVALID"),
        (task_or_correlation, "HANDOFF_TASK_INVALID"),
        (authoritative_main, "HANDOFF_MAIN_INVALID"),
        (next_action, "HANDOFF_NEXT_ACTION_INVALID"),
    ):
        if not isinstance(value, str) or not value:
            raise ContextDisciplineError(error)
    if not isinstance(current_state, dict) or current_state.get("schema") != CURRENT_STATE_SCHEMA:
        raise ContextDisciplineError("HANDOFF_CURRENT_STATE_INVALID")

    gaps = _validate_string_list(open_gaps, "HANDOFF_OPEN_GAPS_INVALID")
    lessons = _validate_string_list(lesson_refs, "HANDOFF_LESSON_REFS_INVALID")
    sources = _validate_string_list(source_refs, "HANDOFF_SOURCE_REFS_REQUIRED", allow_empty=False)

    return {
        "schema": HANDOFF_SCHEMA,
        "authority": "DERIVED",
        "role_or_engine": role_or_engine,
        "current_goal": current_goal,
        "task_or_correlation": task_or_correlation,
        "authoritative_main": authoritative_main,
        "active_base": _single_state_value(current_state, "ACTIVE_BASE"),
        "active_head": _single_state_value(current_state, "ACTIVE_HEAD"),
        "verified_current_state": current_state,
        "current_blocker_or_none": _single_state_value(current_state, "CURRENT_BLOCKER"),
        "open_gaps": gaps,
        "relevant_verified_lesson_refs": lessons,
        "next_action": next_action,
        "source_refs": sources,
        "supersedes": [],
    }


def validate_handoff(
    handoff: dict[str, Any],
    *,
    fresh_authoritative_main: str,
) -> dict[str, Any]:
    if not isinstance(handoff, dict) or handoff.get("schema") != HANDOFF_SCHEMA:
        raise ContextDisciplineError("HANDOFF_INVALID")
    if handoff.get("authority") != "DERIVED":
        raise ContextDisciplineError("HANDOFF_AUTHORITY_INVALID")
    if not isinstance(fresh_authoritative_main, str) or not fresh_authoritative_main:
        raise ContextDisciplineError("HANDOFF_FRESH_MAIN_INVALID")
    if handoff.get("authoritative_main") != fresh_authoritative_main:
        raise ContextDisciplineError("HANDOFF_STALE")
    _validate_string_list(handoff.get("source_refs"), "HANDOFF_SOURCE_REFS_REQUIRED", allow_empty=False)
    state = handoff.get("verified_current_state")
    if not isinstance(state, dict) or state.get("schema") != CURRENT_STATE_SCHEMA:
        raise ContextDisciplineError("HANDOFF_CURRENT_STATE_INVALID")
    return dict(handoff)
