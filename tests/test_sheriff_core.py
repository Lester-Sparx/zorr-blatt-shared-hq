import unittest

from _support import ROOT
from sheriff_core import (
    SheriffIntegrityError,
    apply_discipline,
    canonical_body_hash,
    classify_replay,
    discipline_status,
    remediation_path,
)


class SheriffCoreTest(unittest.TestCase):
    def test_canonical_body_hash_is_order_independent(self):
        left = {"id": "evt-1", "data": {"b": 2, "a": 1}}
        right = {"data": {"a": 1, "b": 2}, "id": "evt-1"}
        self.assertEqual(canonical_body_hash(left), canonical_body_hash(right))
        self.assertEqual(len(canonical_body_hash(left)), 64)

    def test_replay_is_idempotent_only_for_identical_body(self):
        digest = "a" * 64
        self.assertEqual(classify_replay(digest, digest), "IDEMPOTENT_REPLAY")
        with self.assertRaisesRegex(SheriffIntegrityError, "EVENT_ID_BODY_HASH_CONFLICT"):
            classify_replay(digest, "b" * 64)

    def test_discipline_is_bounded_and_status_is_deterministic(self):
        self.assertEqual(apply_discipline(100, -2), 98)
        self.assertEqual(apply_discipline(2, -50), 0)
        self.assertEqual(apply_discipline(99, 50), 100)
        self.assertEqual(discipline_status(100), "GREEN")
        self.assertEqual(discipline_status(89), "YELLOW")
        self.assertEqual(discipline_status(74), "ORANGE")
        self.assertEqual(discipline_status(49), "RED")

    def test_i0_self_caught_has_no_hold_path(self):
        self.assertEqual(remediation_path("I0_SELF_CAUGHT", 0), ())

    def test_first_correctness_incident_requires_learning_loop(self):
        path = remediation_path("I1_CORRECTNESS", 0)
        self.assertEqual(path, ("ROOT_CAUSE", "REGRESSION_TEST", "FRESH_VERIFICATION"))

    def test_repeat_incidents_escalate_required_controls(self):
        first_repeat = remediation_path("I1_CORRECTNESS", 1)
        self.assertIn("MANDATORY_PREFLIGHT", first_repeat)
        self.assertIn("INDEPENDENT_QC", first_repeat)
        repeated = remediation_path("I2_PROCESS", 2)
        self.assertIn("RESTRICT_SIMILAR_WORK", repeated)
        self.assertIn("INDEPENDENT_QC", repeated)

    def test_critical_incidents_require_hard_hold_and_independent_clearance(self):
        path = remediation_path("I3_CRITICAL_INTEGRITY", 0)
        for step in ("HARD_HOLD", "EVIDENCE_REVIEW", "REMEDIATION_PROOF", "INDEPENDENT_QC"):
            self.assertIn(step, path)
        safety_path = remediation_path("I4_SAFETY_SECURITY", 0)
        self.assertIn("OWNER_REINSTATEMENT", safety_path)

    def test_unknown_incident_class_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "UNKNOWN_INCIDENT_CLASS"):
            remediation_path("I9_UNKNOWN", 0)


if __name__ == "__main__":
    unittest.main()
