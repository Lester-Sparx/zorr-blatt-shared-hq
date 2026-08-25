import unittest

from _support import ROLES, registered_task, review_report
from hq_adapter import HQError, create_owner_lock, submit_review


class OwnerLockTest(unittest.TestCase):
    def test_qc_pass_does_not_auto_lock_and_only_owner_can_lock(self):
        state, task = registered_task()
        task, qc = submit_review(task, actor="duncan", kind="QC", result="PASS", report=review_report("QC", "PASS"), roles=ROLES)
        self.assertEqual(task["status"], "QC_PASS")
        self.assertIsNone(task["lockRecord"])
        task, arch = submit_review(task, actor="django", kind="ARCHITECTURE", result="ACCEPTED", report=review_report("ARCHITECTURE", "ACCEPTED"), roles=ROLES)
        with self.assertRaisesRegex(HQError, "OWNER"):
            create_owner_lock(state, task, qc, arch, actor="duncan", timestamp="2026-08-25T00:00:00Z", roles=ROLES)
        locked, record = create_owner_lock(state, task, qc, arch, actor="owner", timestamp="2026-08-25T00:00:00Z", roles=ROLES)
        self.assertEqual(locked["status"], "LOCKED")
        self.assertEqual(record["artifactSha256"], task["artifactSha256"])


if __name__ == "__main__": unittest.main()
