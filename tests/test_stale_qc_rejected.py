import unittest

from _support import ROLES, registered_task, review_report
from hq_adapter import HQError, create_owner_lock, submit_review


class StaleQcTest(unittest.TestCase):
    def test_old_qc_cannot_lock_new_revision(self):
        state, task = registered_task()
        task, qc = submit_review(task, actor="duncan", kind="QC", result="PASS", report=review_report("QC", "PASS"), roles=ROLES)
        task, arch = submit_review(task, actor="django", kind="ARCHITECTURE", result="ACCEPTED", report=review_report("ARCHITECTURE", "ACCEPTED"), roles=ROLES)
        task["revision"] = 2
        with self.assertRaisesRegex(HQError, "STALE OR FOREIGN"):
            create_owner_lock(state, task, qc, arch, actor="owner", timestamp="2026-08-25T00:00:00Z", roles=ROLES)


if __name__ == "__main__": unittest.main()
