from __future__ import annotations

from collections import defaultdict
from typing import Any


FACT_SCHEMA = "ZB_CONTEXT_FACT_V1"
CURRENT_STATE_SCHEMA = "ZB_CONTEXT_CURRENT_STATE_V1"
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
    candidates = [
        fact
        for fact in normalized
        if fact["class"] != "E0" and _scope_matches(fact, scope_tags)
    ]

    ids = [fact["fact_id"] for fact in normalized]
    if len(ids) != len(set(ids)):
        raise ContextDisciplineError("CONTEXT_FACT_ID_DUPLICATE")

    superseded_ids = {
        superseded_id
        for fact in candidates
        for superseded_id in fact["supersedes"]
    }
    current = [fact for fact in candidates if fact["fact_id"] not in superseded_ids]

    exclusive_by_key: dict[str, list[dict[str, Any]]] = defaultdict(list)
    nonexclusive: list[dict[str, Any]] = []
    for fact in current:
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
