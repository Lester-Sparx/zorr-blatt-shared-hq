from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from scripts import hq_context_discipline as context
from scripts.hq_unified_archive import (
    derive_record,
    search_records,
    sync_sheriff_lessons,
    write_record,
)


class ContextDisciplineAcceptanceTests(unittest.TestCase):
    @staticmethod
    def fact(
        fact_id: str,
        fact_class: str,
        key: str,
        value: object,
        *,
        scope_tags: list[str],
        exclusive: bool = True,
        verified: bool = True,
        authority: str = "GITHUB",
        source_refs: list[str] | None = None,
        supersedes: list[str] | None = None,
        created_at: str = "2026-08-31T17:00:00Z",
    ) -> dict[str, object]:
        return {
            "schema": "ZB_CONTEXT_FACT_V1",
            "fact_id": fact_id,
            "class": fact_class,
            "key": key,
            "value": value,
            "exclusive": exclusive,
            "verified": verified,
            "authority": authority,
            "created_at": created_at,
            "scope_tags": scope_tags,
            "source_refs": list(source_refs or []),
            "supersedes": list(supersedes or []),
        }

    @staticmethod
    def archive_record(root: Path, *, number: int, title: str, body: str) -> str:
        event = {
            "action": "created",
            "repository": {"full_name": "Lester-Sparx/zorr-blatt-shared-hq"},
            "sender": {"login": "Lester-Sparx"},
            "issue": {
                "number": number,
                "title": title,
                "html_url": f"https://github.com/Lester-Sparx/zorr-blatt-shared-hq/issues/{number}",
            },
            "comment": {
                "body": body,
                "html_url": f"https://github.com/Lester-Sparx/zorr-blatt-shared-hq/issues/{number}#issuecomment-{number}",
            },
        }
        raw = (json.dumps(event, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
        digest = hashlib.sha256(raw).hexdigest()
        record = derive_record(
            raw,
            raw_sha256=digest,
            event_name="issue_comment",
            repository="Lester-Sparx/zorr-blatt-shared-hq",
            actor="Lester-Sparx",
        )
        write_record(record, root)
        return digest

    @staticmethod
    def state_value(state: dict[str, object], key: str) -> object | None:
        facts = state["facts"]
        values = [item["value"] for item in facts if item["key"] == key]
        if not values:
            return None
        if len(values) != 1:
            raise AssertionError(f"expected one {key}, got {values!r}")
        return values[0]

    @classmethod
    def decision_signature(cls, packet: dict[str, object]) -> dict[str, object]:
        anchors = {
            item["key"]: item["value"]
            for item in packet["mandatory_anchors"]
        }
        state = packet["current_state"]
        return {
            "role": cls.state_value(state, "ROLE"),
            "task": anchors.get("CURRENT_TASK"),
            "head": cls.state_value(state, "ACTIVE_HEAD"),
            "blocker": cls.state_value(state, "CURRENT_BLOCKER"),
            "next": cls.state_value(state, "NEXT_ACTION"),
            "owner_lock": cls.state_value(state, "OWNER_LOCK"),
        }

    @classmethod
    def long_history(cls) -> list[dict[str, object]]:
        history: list[dict[str, object]] = []
        for index in range(80):
            history.append(
                cls.fact(
                    f"progress-{index}",
                    "E0",
                    "PROGRESS",
                    "routine repeated status " + ("x" * 120),
                    scope_tags=["LESTER", "CONTEXT_R01"],
                    exclusive=False,
                    verified=False,
                    authority="CHAT",
                    source_refs=[],
                    created_at=f"2026-08-31T16:{index % 60:02d}:00Z",
                )
            )
        history.extend(
            [
                cls.fact(
                    "head-old",
                    "E2",
                    "ACTIVE_HEAD",
                    "old-head",
                    scope_tags=["LESTER", "CONTEXT_R01"],
                    source_refs=["github:commit:old-head"],
                    created_at="2026-08-31T15:00:00Z",
                ),
                cls.fact(
                    "head-new",
                    "E2",
                    "ACTIVE_HEAD",
                    "new-head",
                    scope_tags=["LESTER", "CONTEXT_R01"],
                    source_refs=["github:commit:new-head"],
                    supersedes=["head-old"],
                    created_at="2026-08-31T17:00:00Z",
                ),
                cls.fact(
                    "role",
                    "E2",
                    "ROLE",
                    "LESTER",
                    scope_tags=["LESTER", "CONTEXT_R01"],
                    source_refs=["github:issue:235"],
                ),
                cls.fact(
                    "blocker",
                    "E2",
                    "CURRENT_BLOCKER",
                    "ASSIGN_VS_EXECUTION",
                    scope_tags=["LESTER", "CONTEXT_R01"],
                    source_refs=["github:issue:235"],
                ),
                cls.fact(
                    "next",
                    "E2",
                    "NEXT_ACTION",
                    "REPRODUCE_NEGATIVE",
                    scope_tags=["LESTER", "CONTEXT_R01"],
                    source_refs=["github:issue:235"],
                ),
                cls.fact(
                    "owner-lock",
                    "E2",
                    "OWNER_LOCK",
                    "NO_OWNER_RELAY",
                    scope_tags=["ZORR"],
                    exclusive=False,
                    authority="OWNER",
                    source_refs=["github:owner:directive"],
                    created_at="2026-01-01T00:00:00Z",
                ),
                cls.fact(
                    "salvador-unrelated",
                    "E2",
                    "DRAWING_TASK",
                    "hands practice",
                    scope_tags=["SALVADOR", "DRAW"],
                    source_refs=["github:issue:214"],
                ),
            ]
        )
        return history

    def test_t1_long_chat_decision_parity(self) -> None:
        history = self.long_history()
        state = context.project_current_state(history, scope_tags={"LESTER", "CONTEXT_R01"})
        with tempfile.TemporaryDirectory() as tmp:
            packet = context.build_context_packet(
                Path(tmp),
                mandatory_anchors=[{"key": "CURRENT_TASK", "value": "#235"}],
                current_state=state,
                jit_queries=[],
            )
        self.assertEqual(packet["status"], "PROVEN")
        self.assertEqual(
            self.decision_signature(packet),
            {
                "role": "LESTER",
                "task": "#235",
                "head": "new-head",
                "blocker": "ASSIGN_VS_EXECUTION",
                "next": "REPRODUCE_NEGATIVE",
                "owner_lock": "NO_OWNER_RELAY",
            },
        )

    def test_t2_stale_supersession_rejected_even_if_superseder_is_out_of_scope(self) -> None:
        facts = [
            self.fact(
                "old",
                "E2",
                "ACTIVE_HEAD",
                "stale-head",
                scope_tags=["LYNCH", "SCENE"],
                source_refs=["github:commit:stale"],
            ),
            self.fact(
                "new",
                "E2",
                "ACTIVE_HEAD",
                "fresh-head",
                scope_tags=["LESTER", "SECURITY_R02"],
                source_refs=["github:commit:fresh"],
                supersedes=["old"],
            ),
        ]
        state = context.project_current_state(facts, scope_tags={"LYNCH", "SCENE"})
        self.assertIsNone(self.state_value(state, "ACTIVE_HEAD"))

    def test_t3_contradiction_fails_closed(self) -> None:
        facts = [
            self.fact("a", "E2", "ACTIVE_HEAD", "a", scope_tags=["LESTER"], source_refs=["github:a"]),
            self.fact("b", "E2", "ACTIVE_HEAD", "b", scope_tags=["LESTER"], source_refs=["github:b"]),
        ]
        with self.assertRaisesRegex(context.ContextDisciplineError, "DURABLE_CONTEXT_NOT_PROVEN:CONFLICT:ACTIVE_HEAD"):
            context.project_current_state(facts, scope_tags={"LESTER"})

    def test_t4_unrelated_history_excluded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.archive_record(root, number=801, title="LYNCH continuity", body="screen geography continuity beat map")
            self.archive_record(root, number=802, title="SHERIFF image", body="OCI digest pinning runtime container")
            state = context.project_current_state([
                self.fact("role", "E2", "ROLE", "LYNCH", scope_tags=["LYNCH"], source_refs=["github:scene"]),
            ])
            packet = context.build_context_packet(
                root,
                mandatory_anchors=[{"key": "CURRENT_TASK", "value": "scene-42"}],
                current_state=state,
                jit_queries=[{"facet": "DIRECTING", "query": "screen geography"}],
            )
        text = json.dumps(packet, ensure_ascii=False, sort_keys=True)
        self.assertIn("screen geography", text)
        self.assertNotIn("OCI digest", text)

    def test_t5_old_owner_lock_survives_compaction(self) -> None:
        state = context.project_current_state(self.long_history(), scope_tags={"LESTER", "CONTEXT_R01"})
        self.assertEqual(self.state_value(state, "OWNER_LOCK"), "NO_OWNER_RELAY")

    def test_t5b_e2_without_evidence_ref_is_rejected(self) -> None:
        unbound = self.fact(
            "unbound-pass",
            "E2",
            "RESULT",
            "PASS",
            scope_tags=["LESTER"],
            source_refs=[],
        )
        with self.assertRaisesRegex(context.ContextDisciplineError, "CONTEXT_FACT_E2_REQUIRES_EVIDENCE"):
            context.project_current_state([unbound])

    def test_t6_verified_lesson_transfers_but_open_lesson_does_not(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            archive = root / "archive"
            verdicts = repo / "hq/sheriff/verdicts"
            lessons = repo / "hq/sheriff/lessons"
            verdicts.mkdir(parents=True)
            lessons.mkdir(parents=True)
            lesson_ref = "hq/sheriff/lessons/CTX-001.md"
            (repo / lesson_ref).write_text(
                "Reject stale evidence substitution; bind current evidence provenance before PASS.\n",
                encoding="utf-8",
            )
            closed = {
                "schemaVersion": "SHERIFF_VERDICT_V1",
                "verdictId": "CTX-001",
                "agentId": "LESTER",
                "incidentClass": "I1_CORRECTNESS",
                "evidence": ["github:run:100"],
                "errorSignature": "STALE_EVIDENCE_SUBSTITUTION",
                "rootCause": "Current claim reused stale evidence.",
                "regressionTest": "tests/test_ctx.py::test_stale",
                "lessonRef": lesson_ref,
                "status": "CLOSED",
                "issuedAt": "2026-08-30T10:00:00Z",
            }
            open_verdict = {
                "schemaVersion": "SHERIFF_VERDICT_V1",
                "verdictId": "CTX-OPEN",
                "status": "OPEN",
            }
            (verdicts / "CTX-001.json").write_text(json.dumps(closed), encoding="utf-8")
            (verdicts / "CTX-OPEN.json").write_text(json.dumps(open_verdict), encoding="utf-8")
            sync = sync_sheriff_lessons(verdicts, repo, archive)
            self.assertEqual(sync["learned"], 1)
            self.assertEqual(sync["skipped_open"], 1)
            state = context.project_current_state([
                self.fact("head", "E2", "ACTIVE_HEAD", "changed-head", scope_tags=["LESTER"], source_refs=["github:commit:changed"]),
            ])
            packet = context.build_context_packet(
                archive,
                mandatory_anchors=[{"key": "CURRENT_TASK", "value": "changed-task-999"}],
                current_state=state,
                jit_queries=[],
                lesson_query="stale evidence substitution",
            )
        self.assertEqual(packet["learning"]["status"], "PROVEN")
        verdict_ids = [item["verdict_id"] for item in packet["learning"]["lessons"]]
        self.assertEqual(verdict_ids, ["CTX-001"])
        self.assertNotIn("CTX-OPEN", json.dumps(packet, sort_keys=True))

    def test_t7_disputed_evidence_expands_exact_record_jit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tail = "EXACT_TERMINAL_EVIDENCE=run:123456"
            body = "disputed terminal evidence " + ("x" * 1500) + tail
            digest = self.archive_record(root, number=901, title="terminal proof", body=body)
            self.archive_record(root, number=902, title="unrelated proof", body="unrelated drawing history")
            state = context.project_current_state([
                self.fact("result", "E2", "RESULT", "PASS", scope_tags=["LESTER"], source_refs=["sha256:" + digest]),
            ])
            packet = context.build_context_packet(
                root,
                mandatory_anchors=[{"key": "CURRENT_TASK", "value": "#901"}],
                current_state=state,
                jit_queries=[{"facet": "TERMINAL", "query": "disputed terminal evidence"}],
            )
            compact_text = json.dumps(packet, sort_keys=True)
            self.assertNotIn(tail, compact_text)
            expanded = search_records(root, "disputed terminal evidence", limit=1)
        self.assertEqual(len(expanded), 1)
        self.assertEqual(expanded[0]["raw_sha256"], digest)
        self.assertIn(tail, expanded[0]["body_text"])
        self.assertNotIn("unrelated drawing history", expanded[0]["body_text"])

    def test_t8_repeated_status_becomes_no_delta(self) -> None:
        state = context.project_current_state([
            self.fact("head", "E2", "ACTIVE_HEAD", "same-head", scope_tags=["LESTER"], source_refs=["github:head"]),
        ])
        for _ in range(3):
            delta = context.diff_current_state(state, state)
            rendered = context.render_owner_delta(delta, blocker="WAITING_FOR_CI", evidence=[], next_action=None)
            self.assertEqual(rendered, "NO DELTA. BLOCKER = WAITING_FOR_CI")
            self.assertNotIn("same-head", rendered)

    def test_t9_handoff_cold_start_recovers_next_action_without_transcript(self) -> None:
        state = context.project_current_state([
            self.fact("role", "E2", "ROLE", "LESTER", scope_tags=["LESTER"], source_refs=["github:issue:235"]),
            self.fact("base", "E2", "ACTIVE_BASE", "base-head", scope_tags=["LESTER"], source_refs=["github:base"]),
            self.fact("head", "E2", "ACTIVE_HEAD", "candidate-head", scope_tags=["LESTER"], source_refs=["github:candidate"]),
            self.fact("blocker", "E2", "CURRENT_BLOCKER", "ASSIGN_VS_EXECUTION", scope_tags=["LESTER"], source_refs=["github:issue:235"]),
            self.fact("next", "E2", "NEXT_ACTION", "REPRODUCE_NEGATIVE", scope_tags=["LESTER"], source_refs=["github:issue:235"]),
        ])
        handoff = context.build_handoff(
            role_or_engine="LESTER",
            current_goal="context reliability",
            task_or_correlation="#235",
            authoritative_main="main-head",
            current_state=state,
            open_gaps=["ASSIGN_VS_EXECUTION"],
            lesson_refs=[],
            next_action="REPRODUCE_NEGATIVE",
            source_refs=["github:issue:235", "github:candidate"],
        )
        validated = context.validate_handoff(handoff, fresh_authoritative_main="main-head")
        with tempfile.TemporaryDirectory() as tmp:
            packet = context.build_context_packet(
                Path(tmp),
                mandatory_anchors=[{"key": "CURRENT_TASK", "value": validated["task_or_correlation"]}],
                current_state=validated["verified_current_state"],
                jit_queries=[],
            )
        signature = self.decision_signature(packet)
        self.assertEqual(signature["role"], "LESTER")
        self.assertEqual(signature["head"], "candidate-head")
        self.assertEqual(signature["next"], "REPRODUCE_NEGATIVE")
        self.assertNotIn("transcript", json.dumps(handoff, sort_keys=True).lower())

    def test_t10_context_reduction_with_decision_parity(self) -> None:
        history = self.long_history()
        state = context.project_current_state(history, scope_tags={"LESTER", "CONTEXT_R01"})
        with tempfile.TemporaryDirectory() as tmp:
            packet = context.build_context_packet(
                Path(tmp),
                mandatory_anchors=[{"key": "CURRENT_TASK", "value": "#235"}],
                current_state=state,
                jit_queries=[],
            )
        naive_bytes = len(json.dumps(history, sort_keys=True, ensure_ascii=False).encode("utf-8"))
        compact_bytes = len(json.dumps(packet, sort_keys=True, ensure_ascii=False).encode("utf-8"))
        self.assertLess(compact_bytes, naive_bytes)
        self.assertEqual(
            self.decision_signature(packet),
            {
                "role": "LESTER",
                "task": "#235",
                "head": "new-head",
                "blocker": "ASSIGN_VS_EXECUTION",
                "next": "REPRODUCE_NEGATIVE",
                "owner_lock": "NO_OWNER_RELAY",
            },
        )


if __name__ == "__main__":
    unittest.main()
