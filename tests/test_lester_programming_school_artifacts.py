from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts import lester_programming_school as school


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "hq" / "training" / "LESTER_PROGRAMMING_DOMAIN_CATALOG_V1.json"
PROFILE_PATH = ROOT / "hq" / "training" / "LESTER_PROGRAMMING_PROFILE_V1.json"
DOC_PATH = ROOT / "docs" / "LESTER_PROGRAMMING_SCHOOL_R01.md"


class LesterProgrammingSchoolArtifactTests(unittest.TestCase):
    def test_catalog_is_exact_unique_curriculum_not_skill_claim(self) -> None:
        catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        self.assertEqual(catalog["schemaVersion"], "LESTER_PROGRAMMING_DOMAIN_CATALOG_V1")
        self.assertEqual(tuple(catalog["domains"]), school.DOMAINS)
        self.assertEqual(len(catalog["domains"]), len(set(catalog["domains"])), 16)
        self.assertFalse(catalog["claimsExistingCompetence"])

    def test_neutral_bootstrap_is_exact_rebuild_of_empty_evidence(self) -> None:
        persisted = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(persisted, school.build_profile([]))
        self.assertFalse(persisted["historicalBackfill"])
        self.assertFalse(persisted["disciplineAffectsCompetence"])
        self.assertTrue(all(bucket["state"] == "UNTESTED" for bucket in persisted["domains"].values()))
        self.assertTrue(all(not bucket["evidenceIds"] for bucket in persisted["domains"].values()))

    def test_operator_contract_records_learning_and_reuse_laws(self) -> None:
        text = DOC_PATH.read_text(encoding="utf-8")
        for required in (
            "REAL ZORR TASK -> EVIDENCE -> TEST/QC -> LESSON -> CHANGED/UNSEEN TRANSFER -> SKILL UPDATE",
            "READING != SKILL",
            "ONE PASS != PROVEN",
            "SHERIFF DISCIPLINE != PROGRAMMING COMPETENCE",
            "jsonschema==4.25.1",
        ):
            self.assertIn(required, text)


class LesterProgrammingSchoolCliTests(unittest.TestCase):
    def _run(self, payload: object) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temp_dir:
            evidence_path = Path(temp_dir) / "evidence.json"
            evidence_path.write_text(json.dumps(payload), encoding="utf-8")
            return subprocess.run(
                [sys.executable, "-m", "scripts.lester_programming_school", "--evidence", str(evidence_path)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

    def test_cli_emits_deterministic_profile_and_next_target(self) -> None:
        record = {
            "evidenceId": "CLI-P1",
            "agentId": "LESTER",
            "domain": "python",
            "taskKind": "unit_fix",
            "mode": "EXECUTION",
            "result": "PASS",
            "verified": True,
            "sourceRef": "github:pr:217#run:1",
            "exactHead": "1" * 40,
            "sequence": 1,
        }
        completed = self._run([record])
        self.assertEqual(completed.returncode, 0, completed.stderr)
        decoded = json.loads(completed.stdout)
        self.assertEqual(decoded["profile"]["domains"]["python"]["state"], "PARTIAL")
        self.assertEqual(decoded["nextTrainingTarget"]["state"], "UNTESTED")

    def test_cli_fails_closed_on_invalid_evidence(self) -> None:
        completed = self._run([{"evidenceId": "BROKEN"}])
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("EVIDENCE_SCHEMA_VALIDATION_FAILED", completed.stderr)


if __name__ == "__main__":
    unittest.main()
