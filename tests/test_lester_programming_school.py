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


if __name__ == "__main__":
    unittest.main()
