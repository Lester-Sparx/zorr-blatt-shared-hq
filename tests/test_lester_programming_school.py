from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import unittest

from scripts import lester_programming_school as school


HEAD = "1" * 40
ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "LESTER_PROGRAMMING_EVIDENCE_V1.schema.json"


def evidence(
    evidence_id: str = "E1",
    *,
    domain: str = "python",
    task_kind: str = "unit_fix",
    mode: str = "EXECUTION",
    result: str = "PASS",
    verified: bool = True,
    source_ref: str = "github:pr:1#run:2",
    exact_head: str = HEAD,
    sequence: int = 1,
) -> dict[str, object]:
    return {
        "evidenceId": evidence_id,
        "agentId": "LESTER",
        "domain": domain,
        "taskKind": task_kind,
        "mode": mode,
        "result": result,
        "verified": verified,
        "sourceRef": source_ref,
        "exactHead": exact_head,
        "sequence": sequence,
    }


class LesterProgrammingSchoolModuleTests(unittest.TestCase):
    def test_module_exists(self) -> None:
        self.assertIsNotNone(importlib.util.find_spec("scripts.lester_programming_school"))

    def test_evidence_rules_live_in_draft_2020_12_json_schema(self) -> None:
        self.assertEqual(school.EVIDENCE_SCHEMA_PATH.resolve(), SCHEMA_PATH.resolve())
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(tuple(schema["properties"]["domain"]["enum"]), school.DOMAINS)
        self.assertFalse(schema["additionalProperties"])


class LesterProgrammingEvidenceTests(unittest.TestCase):
    def test_execution_requires_exact_head(self) -> None:
        record = evidence(exact_head="")
        with self.assertRaisesRegex(school.LesterProgrammingSchoolError, "EXACT_HEAD_INVALID"):
            school.validate_evidence([record])

    def test_unknown_domain_fails_closed(self) -> None:
        record = evidence(domain="invented_framework")
        with self.assertRaisesRegex(school.LesterProgrammingSchoolError, "DOMAIN_UNKNOWN"):
            school.validate_evidence([record])

    def test_duplicate_identical_evidence_is_idempotent(self) -> None:
        record = evidence()
        validated = school.validate_evidence([record, copy.deepcopy(record)])
        self.assertEqual(validated, [record])

    def test_duplicate_conflicting_evidence_fails_closed(self) -> None:
        first = evidence()
        second = evidence(result="FAIL")
        with self.assertRaisesRegex(school.LesterProgrammingSchoolError, "EVIDENCE_ID_CONFLICT"):
            school.validate_evidence([first, second])

    def test_study_may_omit_head_but_requires_durable_source(self) -> None:
        valid = evidence(mode="STUDY", exact_head="", source_ref="github:repo:upstream/ref:v1")
        self.assertEqual(school.validate_evidence([valid]), [valid])

        invalid = evidence(evidence_id="E2", mode="STUDY", exact_head="", source_ref="")
        with self.assertRaisesRegex(school.LesterProgrammingSchoolError, "SOURCE_REF_INVALID"):
            school.validate_evidence([invalid])


class LesterProgrammingProfileTests(unittest.TestCase):
    def test_empty_profile_is_neutral_untested(self) -> None:
        profile = school.build_profile([])
        self.assertEqual(profile["schemaVersion"], "LESTER_PROGRAMMING_PROFILE_V1")
        self.assertEqual(profile["agentId"], "LESTER")
        self.assertFalse(profile["historicalBackfill"])
        self.assertFalse(profile["disciplineAffectsCompetence"])
        self.assertTrue(all(item["state"] == "UNTESTED" for item in profile["domains"].values()))

    def test_study_and_unverified_pass_do_not_promote(self) -> None:
        study = evidence("S1", mode="STUDY", exact_head="", source_ref="github:repo:study", sequence=1)
        unverified = evidence("U1", verified=False, sequence=2)
        profile = school.build_profile([study, unverified])
        python = profile["domains"]["python"]
        self.assertEqual(python["state"], "UNTESTED")
        self.assertEqual(python["studyEvents"], 1)
        self.assertEqual(python["verifiedPasses"], 0)

    def test_verified_fail_without_pass_is_failed(self) -> None:
        profile = school.build_profile([evidence("F1", result="FAIL")])
        self.assertEqual(profile["domains"]["python"]["state"], "FAILED")

    def test_one_verified_execution_pass_is_partial(self) -> None:
        profile = school.build_profile([evidence("P1")])
        self.assertEqual(profile["domains"]["python"]["state"], "PARTIAL")

    def test_two_execution_passes_without_transfer_remain_partial(self) -> None:
        records = [
            evidence("P1", sequence=1),
            evidence("P2", exact_head="2" * 40, source_ref="github:pr:2#run:2", sequence=2),
        ]
        profile = school.build_profile(records)
        python = profile["domains"]["python"]
        self.assertEqual(python["verifiedPasses"], 2)
        self.assertEqual(python["verifiedTransferPasses"], 0)
        self.assertEqual(python["state"], "PARTIAL")

    def test_execution_plus_changed_unseen_transfer_can_be_proven(self) -> None:
        records = [
            evidence("P1", sequence=1),
            evidence(
                "T1",
                mode="TRANSFER",
                exact_head="3" * 40,
                source_ref="github:pr:3#run:4",
                task_kind="changed_unseen_fix",
                sequence=2,
            ),
        ]
        profile = school.build_profile(records)
        python = profile["domains"]["python"]
        self.assertEqual(python["verifiedPasses"], 2)
        self.assertEqual(python["verifiedTransferPasses"], 1)
        self.assertEqual(python["state"], "PROVEN")

    def test_task_kinds_are_derived_separately(self) -> None:
        records = [
            evidence("P1", task_kind="parser_fix", sequence=1),
            evidence(
                "T1",
                task_kind="parser_fix",
                mode="TRANSFER",
                exact_head="4" * 40,
                source_ref="github:pr:4#run:5",
                sequence=2,
            ),
            evidence("F1", task_kind="workflow_fix", result="FAIL", exact_head="5" * 40, sequence=3),
        ]
        profile = school.build_profile(records)
        kinds = profile["domains"]["python"]["taskKinds"]
        self.assertEqual(kinds["parser_fix"]["state"], "PROVEN")
        self.assertEqual(kinds["workflow_fix"]["state"], "FAILED")


if __name__ == "__main__":
    unittest.main()
