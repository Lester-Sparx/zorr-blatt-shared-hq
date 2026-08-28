import unittest

from _support import ROLES, registered_task, review_report
from hq_adapter import HQError, submit_review


class SelfQcTest(unittest.TestCase):
    def test_same_transport_can_execute_qc_logical_role(self):
        _, task = registered_task()
        single_transport = {
            "approvedTransportActors": ["Lester-Sparx"],
            "logicalRoles": ["OWNER", "LESTER", "DUNCAN", "DJANGO", "JINGO"],
        }
        updated, review = submit_review(
            task, actor="Lester-Sparx", logical_role="DUNCAN", kind="QC", result="PASS",
            report=review_report("QC", "PASS"), roles=single_transport,
        )
        self.assertEqual(updated["status"], "QC_PASS")
        self.assertEqual(review["transportActor"], "Lester-Sparx")
        self.assertEqual(review["logicalRole"], "DUNCAN")

    def test_wrong_logical_role_cannot_execute_qc(self):
        _, task = registered_task()
        single_transport = {
            "approvedTransportActors": ["Lester-Sparx"],
            "logicalRoles": ["OWNER", "LESTER", "DUNCAN", "DJANGO", "JINGO"],
        }
        with self.assertRaisesRegex(HQError, "DUNCAN LOGICAL ROLE"):
            submit_review(
                task, actor="Lester-Sparx", logical_role="DJANGO", kind="QC", result="PASS",
                report=review_report("QC", "PASS"), roles=single_transport,
            )


if __name__ == "__main__": unittest.main()
