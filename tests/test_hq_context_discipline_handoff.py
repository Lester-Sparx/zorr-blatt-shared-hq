from __future__ import annotations

import unittest

from scripts import hq_context_discipline as context


class ContextDisciplineHandoffTests(unittest.TestCase):
    @staticmethod
    def fact(fact_id: str, key: str, value: object) -> dict[str, object]:
        return {
            "schema": "ZB_CONTEXT_FACT_V1",
            "fact_id": fact_id,
            "class": "E2",
            "key": key,
            "value": value,
            "exclusive": True,
            "verified": True,
            "authority": "GITHUB",
            "created_at": "2026-08-31T17:00:00Z",
            "scope_tags": ["LESTER", "CONTEXT_R01"],
            "source_refs": [f"github:fact:{fact_id}"],
            "supersedes": [],
        }

    def current_state(self) -> dict[str, object]:
        return context.project_current_state([
            self.fact("base", "ACTIVE_BASE", "28bca057"),
            self.fact("head", "ACTIVE_HEAD", "candidate-head"),
            self.fact("blocker", "CURRENT_BLOCKER", "ASSIGN_VS_EXECUTION"),
        ])

    def test_handoff_contains_minimum_resume_state_and_is_derived(self) -> None:
        handoff = context.build_handoff(
            role_or_engine="LESTER",
            current_goal="harden chat reasoning",
            task_or_correlation="#235",
            authoritative_main="b18ca6b",
            current_state=self.current_state(),
            open_gaps=["STALE_TERMINAL_EVIDENCE"],
            lesson_refs=["verdict:SV1-LOOP-001"],
            next_action="REPRODUCE_NEXT_NEGATIVE",
            source_refs=["github:issue:235", "github:pr:241"],
        )
        self.assertEqual(handoff["schema"], "ZB_CONTEXT_HANDOFF_V1")
        self.assertEqual(handoff["authority"], "DERIVED")
        self.assertEqual(handoff["active_base"], "28bca057")
        self.assertEqual(handoff["active_head"], "candidate-head")
        self.assertEqual(handoff["current_blocker_or_none"], "ASSIGN_VS_EXECUTION")
        self.assertEqual(handoff["next_action"], "REPRODUCE_NEXT_NEGATIVE")
        self.assertEqual(handoff["source_refs"], ["github:issue:235", "github:pr:241"])

    def test_handoff_cannot_override_fresher_authoritative_main(self) -> None:
        handoff = context.build_handoff(
            role_or_engine="LESTER",
            current_goal="harden chat reasoning",
            task_or_correlation="#235",
            authoritative_main="old-main",
            current_state=self.current_state(),
            open_gaps=[],
            lesson_refs=[],
            next_action="READ_FRESH_MAIN",
            source_refs=["github:issue:235"],
        )
        with self.assertRaisesRegex(context.ContextDisciplineError, "HANDOFF_STALE"):
            context.validate_handoff(handoff, fresh_authoritative_main="new-main")

    def test_handoff_requires_source_evidence(self) -> None:
        with self.assertRaisesRegex(context.ContextDisciplineError, "HANDOFF_SOURCE_REFS_REQUIRED"):
            context.build_handoff(
                role_or_engine="LESTER",
                current_goal="harden chat reasoning",
                task_or_correlation="#235",
                authoritative_main="b18ca6b",
                current_state=self.current_state(),
                open_gaps=[],
                lesson_refs=[],
                next_action="READ_FRESH_MAIN",
                source_refs=[],
            )


if __name__ == "__main__":
    unittest.main()
