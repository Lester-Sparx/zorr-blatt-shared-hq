import copy
import unittest

from _support import base_state
from hq_adapter import HQError
from hq_validate import reject_production_values


class ScopeGuardTest(unittest.TestCase):
    def test_production_values_are_rejected_and_g2_is_blocked(self):
        state, _ = base_state()
        self.assertEqual(set(state["blockedGates"]), {"G2", "VOICE_TO_SHOT"})
        corrupt = copy.deepcopy(state)
        corrupt["lockedTiming"] = {"PARRY": 1}
        with self.assertRaisesRegex(HQError, "PRODUCTION VALUE FORBIDDEN"):
            reject_production_values(corrupt)


if __name__ == "__main__": unittest.main()
