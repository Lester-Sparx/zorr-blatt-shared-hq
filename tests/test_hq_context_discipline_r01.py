from __future__ import annotations

import unittest


class ContextDisciplineR01Tests(unittest.TestCase):
    @staticmethod
    def _module():
        try:
            from scripts import hq_context_discipline
        except ImportError as exc:
            raise AssertionError(
                "scripts.hq_context_discipline must exist before Context Discipline R01 can pass"
            ) from exc
        return hq_context_discipline

    @staticmethod
    def fact(
        fact_id: str,
        fact_class: str,
        key: str,
        value: object,
        *,
        exclusive: bool,
        verified: bool,
        authority: str = "GITHUB",
        created_at: str = "2026-08-31T16:00:00Z",
        scope_tags: list[str] | None = None,
        source_refs: list[str] | None = None,
        supersedes: list[str] | None = None,
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
            "scope_tags": list(scope_tags or ["LESTER"]),
            "source_refs": list(source_refs or []),
            "supersedes": list(supersedes or []),
        }

    def test_e0_never_enters_current_projection(self) -> None:
        module = self._module()
        state = module.project_current_state([
            self.fact(
                "progress-1",
                "E0",
                "PROGRESS",
                "checking",
                exclusive=False,
                verified=False,
                authority="CHAT",
            )
        ])
        self.assertEqual(state["facts"], [])

    def test_new_head_explicitly_supersedes_old_head(self) -> None:
        module = self._module()
        facts = [
            self.fact("head-a", "E2", "ACTIVE_HEAD", "aaaa", exclusive=True, verified=True),
            self.fact(
                "head-b",
                "E2",
                "ACTIVE_HEAD",
                "bbbb",
                exclusive=True,
                verified=True,
                supersedes=["head-a"],
            ),
        ]
        state = module.project_current_state(facts)
        self.assertEqual(
            [(item["key"], item["value"]) for item in state["facts"]],
            [("ACTIVE_HEAD", "bbbb")],
        )

    def test_old_unsuperseded_owner_lock_survives(self) -> None:
        module = self._module()
        facts = [
            self.fact(
                "owner-lock-1",
                "E2",
                "OWNER_LOCK",
                "NO_OWNER_RELAY",
                exclusive=False,
                verified=True,
                authority="OWNER",
                created_at="2026-01-01T00:00:00Z",
                scope_tags=["ZORR"],
                source_refs=["github:owner-lock:1"],
            ),
            self.fact(
                "noise",
                "E0",
                "PROGRESS",
                "still checking",
                exclusive=False,
                verified=False,
                authority="CHAT",
            ),
        ]
        state = module.project_current_state(facts)
        self.assertTrue(any(item["fact_id"] == "owner-lock-1" for item in state["facts"]))

    def test_conflicting_unsuperseded_exclusive_values_fail_closed(self) -> None:
        module = self._module()
        facts = [
            self.fact("head-a", "E2", "ACTIVE_HEAD", "aaaa", exclusive=True, verified=True),
            self.fact("head-b", "E2", "ACTIVE_HEAD", "bbbb", exclusive=True, verified=True),
        ]
        with self.assertRaisesRegex(
            module.ContextDisciplineError,
            "DURABLE_CONTEXT_NOT_PROVEN:CONFLICT:ACTIVE_HEAD",
        ):
            module.project_current_state(facts)

    def test_scope_projection_excludes_unrelated_non_owner_facts(self) -> None:
        module = self._module()
        facts = [
            self.fact(
                "lynch-head",
                "E2",
                "ACTIVE_HEAD",
                "scene-head",
                exclusive=True,
                verified=True,
                scope_tags=["LYNCH", "SCENE"],
            ),
            self.fact(
                "sheriff-gap",
                "E2",
                "CURRENT_BLOCKER",
                "OCI_DIGEST",
                exclusive=True,
                verified=True,
                scope_tags=["LESTER", "SECURITY_R02"],
            ),
        ]
        state = module.project_current_state(facts, scope_tags={"LYNCH", "SCENE"})
        ids = [item["fact_id"] for item in state["facts"]]
        self.assertEqual(ids, ["lynch-head"])

    def test_invalid_fact_fails_closed(self) -> None:
        module = self._module()
        bad = self.fact("bad", "E2", "ACTIVE_HEAD", "x", exclusive=True, verified=True)
        del bad["source_refs"]
        with self.assertRaisesRegex(module.ContextDisciplineError, "CONTEXT_FACT_MISSING"):
            module.project_current_state([bad])

    def test_e2_requires_verified_evidence(self) -> None:
        module = self._module()
        unverified = self.fact(
            "fake-pass",
            "E2",
            "RESULT",
            "PASS",
            exclusive=True,
            verified=False,
            source_refs=["chat:self-report"],
        )
        with self.assertRaisesRegex(module.ContextDisciplineError, "CONTEXT_FACT_E2_REQUIRES_VERIFIED"):
            module.project_current_state([unverified])


if __name__ == "__main__":
    unittest.main()
