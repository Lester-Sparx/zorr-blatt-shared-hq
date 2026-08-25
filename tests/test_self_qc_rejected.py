import unittest

from _support import ROLES, registered_task, review_report
from hq_adapter import HQError, submit_review


class SelfQcTest(unittest.TestCase):
    def test_builder_cannot_qc_own_revision(self):
        _, task = registered_task()
        compromised = dict(ROLES, DUNCAN="lester")
        with self.assertRaisesRegex(HQError, "SELF REVIEW|ROLE"):
            submit_review(task, actor="lester", kind="QC", result="PASS", report=review_report("QC", "PASS"), roles=compromised)


if __name__ == "__main__": unittest.main()
