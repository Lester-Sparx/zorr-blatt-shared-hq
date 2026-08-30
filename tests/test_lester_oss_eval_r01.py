from __future__ import annotations

import json
from pathlib import Path
import unittest

from scripts.lester_oss_eval_r01 import INSPECT_REF, build_sheriff_result_event


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "training" / "LESTER_OSS_EVAL_R01.json"


class LesterOssEvalR01Tests(unittest.TestCase):
    def test_contract_pins_upstream_and_blocks_fake_proven(self) -> None:
        contract = json.loads(CONFIG.read_text(encoding="utf-8"))
        evaluator = contract["evaluator"]
        self.assertEqual(contract["schemaVersion"], "LESTER_OSS_EVAL_R01")
        self.assertEqual(evaluator["repository"], "UKGovernmentBEIS/inspect_ai")
        self.assertEqual(evaluator["ref"], "fbee5b35c656f1c7653af3adf682172033ee0590")
        self.assertEqual(evaluator["license"], "MIT")
        self.assertFalse(contract["historicalBackfill"])
        self.assertEqual(contract["singlePassState"], "PARTIAL_ONLY")
        self.assertTrue(contract["transferRequired"])
        self.assertFalse(contract["disciplineAffectsCompetence"])
        self.assertFalse(contract["customEvalFramework"])
        self.assertFalse(contract["customScoringEngine"])
        self.assertFalse(contract["customTrainingFramework"])
        self.assertEqual(
            contract["sheriffEventSchema"],
            "schemas/SHERIFF_AGENT_EVENT_V1.schema.json",
        )

    def test_upstream_correct_maps_to_existing_sheriff_result_without_proven(self) -> None:
        event = build_sheriff_result_event(
            candidate_head="a" * 40,
            run_id="12345",
            run_attempt="1",
            event_time="2026-08-30T09:30:00Z",
            inspect_log="logs/lester.eval",
            inspect_status="success",
            inspect_score="C",
        )
        self.assertEqual(INSPECT_REF, "fbee5b35c656f1c7653af3adf682172033ee0590")
        self.assertEqual(event["type"], "zb.agent.result")
        self.assertEqual(event["data"]["agentId"], "LESTER")
        self.assertEqual(event["data"]["status"], "PASS")
        self.assertTrue(event["data"]["verifiedPass"])
        self.assertEqual(event["data"]["skillStateAfter"], "PARTIAL_ONLY")
        self.assertTrue(event["data"]["transferRequired"])
        self.assertFalse(event["data"]["historicalBackfill"])
        self.assertNotIn("PROVEN", json.dumps(event, sort_keys=True))

    def test_non_correct_inspect_result_fails_closed(self) -> None:
        event = build_sheriff_result_event(
            candidate_head="b" * 40,
            run_id="12346",
            run_attempt="1",
            event_time="2026-08-30T09:31:00Z",
            inspect_log="logs/lester.eval",
            inspect_status="success",
            inspect_score="I",
        )
        self.assertEqual(event["data"]["status"], "FAIL")
        self.assertFalse(event["data"]["verifiedPass"])
        self.assertTrue(event["data"]["transferRequired"])


if __name__ == "__main__":
    unittest.main()
