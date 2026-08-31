from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class ContextDisciplineCliTests(unittest.TestCase):
    @staticmethod
    def fact(
        fact_id: str,
        fact_class: str,
        key: str,
        value: object,
        *,
        source_refs: list[str],
        supersedes: list[str] | None = None,
        authority: str = "GITHUB",
        scope_tags: list[str] | None = None,
        exclusive: bool = True,
        verified: bool = True,
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
            "created_at": "2026-08-31T17:45:00Z",
            "scope_tags": list(scope_tags or ["LESTER", "CONTEXT_R01"]),
            "source_refs": source_refs,
            "supersedes": list(supersedes or []),
        }

    def test_benchmark_reports_measured_reduction_and_decision_parity(self) -> None:
        from scripts import hq_context_discipline as context

        history = []
        for index in range(40):
            history.append(
                self.fact(
                    f"noise-{index}",
                    "E0",
                    "PROGRESS",
                    "routine-no-delta-" + ("x" * 100),
                    source_refs=[],
                    exclusive=False,
                    verified=False,
                    authority="CHAT",
                )
            )
        history.extend(
            [
                self.fact("old", "E2", "ACTIVE_HEAD", "old-head", source_refs=["github:old"]),
                self.fact("new", "E2", "ACTIVE_HEAD", "new-head", source_refs=["github:new"], supersedes=["old"]),
                self.fact("role", "E2", "ROLE", "LESTER", source_refs=["github:issue:235"]),
                self.fact("blocker", "E2", "CURRENT_BLOCKER", "NONE", source_refs=["github:issue:235"]),
                self.fact("next", "E2", "NEXT_ACTION", "RUN_BENCHMARK", source_refs=["github:issue:235"]),
                self.fact(
                    "owner",
                    "E2",
                    "OWNER_LOCK",
                    "NO_OWNER_RELAY",
                    source_refs=["github:owner"],
                    authority="OWNER",
                    scope_tags=["ZORR"],
                    exclusive=False,
                ),
            ]
        )
        state = context.project_current_state(history, scope_tags={"LESTER", "CONTEXT_R01"})
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet = context.build_context_packet(
                root,
                mandatory_anchors=[{"key": "CURRENT_TASK", "value": "#235"}],
                current_state=state,
                jit_queries=[],
            )
            bundle_path = root / "benchmark.json"
            bundle_path.write_text(
                json.dumps(
                    {
                        "naive_history": history,
                        "scope_tags": ["LESTER", "CONTEXT_R01"],
                        "compact_packet": packet,
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    "scripts/hq_context_discipline_cli.py",
                    "benchmark",
                    "--input-path",
                    str(bundle_path),
                ],
                cwd=Path(__file__).resolve().parents[1],
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        report = json.loads(completed.stdout)
        self.assertEqual(report["schema"], "ZB_CONTEXT_BENCHMARK_V1")
        self.assertGreater(report["naive_context_bytes"], report["compact_context_bytes"])
        self.assertGreater(report["compression_ratio"], 1.0)
        self.assertTrue(report["decision_parity"])
        self.assertTrue(report["critical_fact_recall"])
        self.assertTrue(report["stale_fact_rejection"])

    def test_project_mode_emits_only_current_projection(self) -> None:
        history = [
            self.fact("old", "E2", "ACTIVE_HEAD", "old-head", source_refs=["github:old"]),
            self.fact("new", "E2", "ACTIVE_HEAD", "new-head", source_refs=["github:new"], supersedes=["old"]),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "facts.json"
            path.write_text(json.dumps(history), encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    "scripts/hq_context_discipline_cli.py",
                    "project",
                    "--input-path",
                    str(path),
                    "--scope-tag",
                    "LESTER",
                ],
                cwd=Path(__file__).resolve().parents[1],
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        text = json.dumps(payload, sort_keys=True)
        self.assertIn("new-head", text)
        self.assertNotIn("old-head", text)


if __name__ == "__main__":
    unittest.main()
