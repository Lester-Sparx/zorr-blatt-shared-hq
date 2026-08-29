import json
import unittest
from pathlib import Path

from _support import ROOT


POLICY = ROOT / "docs" / "SHERIFF_POLICY_V1.md"
SCHEMA = ROOT / "schemas" / "SHERIFF_VERDICT_V1.schema.json"
SCOREBOARD = ROOT / "hq" / "sheriff" / "SHERIFF_SCOREBOARD_V1.json"
AGENTS = ROOT / "AGENTS.md"


class SheriffPolicyV1Test(unittest.TestCase):
    def test_policy_defines_non_negotiable_discipline_rules(self):
        text = POLICY.read_text(encoding="utf-8")
        for marker in (
            "HONEST FAIL IS NOT A VIOLATION",
            "FALSE PASS",
            "REUSE-FIRST",
            "AUTHOR != QC != SHERIFF",
            "ERROR -> EVIDENCE -> ROOT CAUSE -> SHERIFF VERDICT -> REPAIR -> REGRESSION TEST -> LESSON",
        ):
            self.assertIn(marker, text)

    def test_verdict_schema_has_evidence_and_severity_contract(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        required = set(schema["required"])
        self.assertTrue({"verdictId", "agentId", "incidentClass", "evidence", "rootCause", "decision", "status"} <= required)
        self.assertEqual(
            schema["properties"]["incidentClass"]["enum"],
            ["I0_SELF_CAUGHT", "I1_CORRECTNESS", "I2_PROCESS", "I3_CRITICAL_INTEGRITY", "I4_SAFETY_SECURITY"],
        )
        self.assertGreaterEqual(schema["properties"]["evidence"]["minItems"], 1)

    def test_scoreboard_bootstraps_neutral_and_separates_skill_from_discipline(self):
        data = json.loads(SCOREBOARD.read_text(encoding="utf-8"))
        self.assertEqual(data["schemaVersion"], "SHERIFF_SCOREBOARD_V1")
        agents = data["agents"]
        ids = [entry["agentId"] for entry in agents]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue({"LESTER", "DUNCAN", "DJANGO", "JINGO", "SHERIFF"} <= set(ids))
        for entry in agents:
            self.assertEqual(entry["discipline"]["score"], 100)
            self.assertEqual(entry["discipline"]["incidentCount"], 0)
            self.assertEqual(entry["skill"]["system"], "glicko2")
            self.assertEqual(entry["skill"]["rating"], 1500)
            self.assertEqual(entry["skill"]["ratingDeviation"], 350)
            self.assertEqual(entry["skill"]["ratedMatches"], 0)

    def test_agent_restart_map_points_to_sheriff_policy(self):
        text = AGENTS.read_text(encoding="utf-8")
        self.assertIn("docs/SHERIFF_POLICY_V1.md", text)
        self.assertIn("SHERIFF_SCOREBOARD_V1.json", text)


if __name__ == "__main__":
    unittest.main()
