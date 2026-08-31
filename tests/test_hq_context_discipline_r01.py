from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
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
        refs = source_refs
        if refs is None:
            refs = [f"github:fact:{fact_id}"] if fact_class == "E2" and verified else []
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
            "source_refs": list(refs),
            "supersedes": list(supersedes or []),
        }

    def state_with(self, key: str, value: object, *, fact_id: str = "state-1") -> dict[str, object]:
        module = self._module()
        return module.project_current_state([
            self.fact(fact_id, "E2", key, value, exclusive=True, verified=True)
        ])

    @staticmethod
    def _archive_record(root: Path, *, number: int, title: str, body: str) -> None:
        from scripts.hq_unified_archive import derive_record, write_record

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

    def test_jit_packet_excludes_unrelated_history(self) -> None:
        module = self._module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._archive_record(
                root,
                number=701,
                title="LYNCH directing lesson",
                body="LYNCH screen geography continuity requires a stable spatial map.",
            )
            self._archive_record(
                root,
                number=702,
                title="SHERIFF supply chain",
                body="SHERIFF OCI digest pinning protects mutable container tags.",
            )
            current = module.project_current_state([
                self.fact("role", "E2", "ROLE", "LYNCH", exclusive=True, verified=True, scope_tags=["LYNCH"]),
            ])
            packet = module.build_context_packet(
                root,
                mandatory_anchors=[{"key": "CURRENT_TASK", "value": "scene-17"}],
                current_state=current,
                jit_queries=[{"facet": "DIRECTING_LESSON", "query": "screen geography continuity"}],
            )
        text = json.dumps(packet, sort_keys=True, ensure_ascii=False)
        self.assertEqual(packet["status"], "PROVEN")
        self.assertIn("screen geography continuity", text)
        self.assertNotIn("OCI digest pinning", text)

    def test_missing_required_jit_facet_is_not_proven(self) -> None:
        module = self._module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            current = module.project_current_state([
                self.fact("role", "E2", "ROLE", "LYNCH", exclusive=True, verified=True, scope_tags=["LYNCH"]),
            ])
            packet = module.build_context_packet(
                root,
                mandatory_anchors=[{"key": "CURRENT_TASK", "value": "scene-17"}],
                current_state=current,
                jit_queries=[{"facet": "DIRECTING_LESSON", "query": "screen geography continuity"}],
            )
        self.assertEqual(packet["status"], "NOT_PROVEN")
        self.assertEqual(packet["missing_facets"], ["DIRECTING_LESSON"])

    def test_e3_is_pointer_only_in_context_packet(self) -> None:
        module = self._module()
        raw_secret = "RAW-WORKFLOW-LOG-BODY-THAT-MUST-NOT-BE-DUPLICATED"
        current = module.project_current_state([
            self.fact(
                "raw-1",
                "E3",
                "RAW_EVIDENCE",
                raw_secret,
                exclusive=False,
                verified=True,
                source_refs=["sha256:abc", "github:run:123"],
            )
        ])
        with tempfile.TemporaryDirectory() as tmp:
            packet = module.build_context_packet(
                Path(tmp),
                mandatory_anchors=[],
                current_state=current,
                jit_queries=[],
            )
        text = json.dumps(packet, sort_keys=True, ensure_ascii=False)
        self.assertNotIn(raw_secret, text)
        self.assertIn("sha256:abc", text)
        self.assertIn("github:run:123", text)

    def test_no_delta_does_not_repeat_settled_state(self) -> None:
        module = self._module()
        state = self.state_with("ACTIVE_HEAD", "bbbb")
        delta = module.diff_current_state(state, state)
        text = module.render_owner_delta(
            delta,
            blocker="WAITING_FOR_CI",
            evidence=[],
            next_action=None,
        )
        self.assertEqual(text, "NO DELTA. BLOCKER = WAITING_FOR_CI")
        self.assertNotIn("bbbb", text)

    def test_terminal_delta_keeps_exact_evidence(self) -> None:
        module = self._module()
        previous = self.state_with("RESULT", "RUNNING", fact_id="result-running")
        current = self.state_with("RESULT", "PASS", fact_id="result-pass")
        delta = module.diff_current_state(previous, current)
        text = module.render_owner_delta(
            delta,
            blocker=None,
            evidence=["run:33414957721", "head:556082d"],
            next_action="AUDIT_NEXT_GAP",
        )
        self.assertIn("DELTA:", text)
        self.assertIn("RESULT=PASS", text)
        self.assertIn("run:33414957721", text)
        self.assertIn("head:556082d", text)
        self.assertIn("NEXT: AUDIT_NEXT_GAP", text)


if __name__ == "__main__":
    unittest.main()
