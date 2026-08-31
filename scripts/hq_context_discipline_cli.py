from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from scripts import hq_context_discipline as context
except ModuleNotFoundError:
    import hq_context_discipline as context


BENCHMARK_SCHEMA = "ZB_CONTEXT_BENCHMARK_V1"
CRITICAL_KEYS = {
    "ROLE",
    "ACTIVE_BASE",
    "ACTIVE_HEAD",
    "CURRENT_BLOCKER",
    "NEXT_ACTION",
    "OWNER_LOCK",
    "RESULT",
}


class ContextDisciplineCliError(RuntimeError):
    pass


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContextDisciplineCliError("CONTEXT_CLI_INPUT_INVALID") from exc


def _json_bytes(value: Any) -> int:
    return len(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


def _fact_signature(state: dict[str, Any], *, critical_only: bool = False) -> list[tuple[str, str]]:
    facts = state.get("facts") if isinstance(state, dict) else None
    if not isinstance(facts, list):
        raise ContextDisciplineCliError("CONTEXT_CLI_STATE_INVALID")
    signature: list[tuple[str, str]] = []
    for fact in facts:
        if not isinstance(fact, dict) or not isinstance(fact.get("key"), str):
            raise ContextDisciplineCliError("CONTEXT_CLI_STATE_INVALID")
        key = fact["key"]
        if critical_only and key not in CRITICAL_KEYS:
            continue
        signature.append(
            (
                key,
                json.dumps(fact.get("value"), sort_keys=True, ensure_ascii=False, default=str),
            )
        )
    return sorted(signature)


def _benchmark(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ContextDisciplineCliError("CONTEXT_BENCHMARK_INPUT_INVALID")
    history = payload.get("naive_history")
    scope_tags = payload.get("scope_tags")
    packet = payload.get("compact_packet")
    if not isinstance(history, list) or not isinstance(scope_tags, list) or not isinstance(packet, dict):
        raise ContextDisciplineCliError("CONTEXT_BENCHMARK_INPUT_INVALID")
    if not all(isinstance(tag, str) and tag for tag in scope_tags):
        raise ContextDisciplineCliError("CONTEXT_BENCHMARK_INPUT_INVALID")
    compact_state = packet.get("current_state")
    if not isinstance(compact_state, dict):
        raise ContextDisciplineCliError("CONTEXT_BENCHMARK_INPUT_INVALID")

    projected = context.project_current_state(history, scope_tags=set(scope_tags))
    naive_bytes = _json_bytes(history)
    compact_bytes = _json_bytes(packet)
    decision_parity = _fact_signature(projected) == _fact_signature(compact_state)
    critical_fact_recall = _fact_signature(projected, critical_only=True) == _fact_signature(
        compact_state,
        critical_only=True,
    )

    superseded_ids = {
        target
        for fact in history
        if isinstance(fact, dict)
        for target in (fact.get("supersedes") or [])
        if isinstance(target, str) and target
    }
    compact_ids = {
        fact.get("fact_id")
        for fact in compact_state.get("facts", [])
        if isinstance(fact, dict) and isinstance(fact.get("fact_id"), str)
    }
    stale_fact_rejection = not bool(superseded_ids.intersection(compact_ids))

    return {
        "schema": BENCHMARK_SCHEMA,
        "naive_context_bytes": naive_bytes,
        "compact_context_bytes": compact_bytes,
        "compression_ratio": (naive_bytes / compact_bytes) if compact_bytes else 0.0,
        "decision_parity": decision_parity,
        "critical_fact_recall": critical_fact_recall,
        "stale_fact_rejection": stale_fact_rejection,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="ZORR Context Discipline utility CLI.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    project_parser = subparsers.add_parser("project")
    project_parser.add_argument("--input-path", required=True, type=Path)
    project_parser.add_argument("--scope-tag", action="append", default=[])

    benchmark_parser = subparsers.add_parser("benchmark")
    benchmark_parser.add_argument("--input-path", required=True, type=Path)

    args = parser.parse_args()
    payload = _load_json(args.input_path)

    if args.command == "project":
        if not isinstance(payload, list):
            raise ContextDisciplineCliError("CONTEXT_PROJECT_INPUT_INVALID")
        scope = set(args.scope_tag) if args.scope_tag else None
        result = context.project_current_state(payload, scope_tags=scope)
    else:
        result = _benchmark(payload)

    print(json.dumps(result, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
