import unittest

from _support import base_state
from hq_adapter import HQError, assert_cas


class RevisionCasTest(unittest.TestCase):
    def test_stale_revision_and_commit_are_rejected(self):
        state, task = base_state()
        with self.assertRaisesRegex(HQError, "REVISION CAS"):
            assert_cas(state, task, 1, "0" * 40)
        with self.assertRaisesRegex(HQError, "MAIN COMMIT CAS"):
            assert_cas(state, task, 0, "a" * 40, current_main="b" * 40)


if __name__ == "__main__": unittest.main()
