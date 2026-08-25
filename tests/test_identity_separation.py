import json
import tempfile
import unittest
from pathlib import Path

from _support import ROOT
from hq_adapter import HQError, authenticated_actor, role_registry


class IdentitySeparationTest(unittest.TestCase):
    def test_duplicate_authenticated_identity_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "roles.yml"
            path.write_text(json.dumps({"OWNER": "same", "LESTER": "same", "DUNCAN": "d", "DJANGO": "j"}))
            with self.assertRaisesRegex(HQError, "CANNOT HOLD MULTIPLE"):
                role_registry(path)

    def test_caller_field_is_not_identity(self):
        with self.assertRaisesRegex(HQError, "GITHUB ACTIONS"):
            authenticated_actor({"GITHUB_ACTOR": "duncan", "GITHUB_EVENT_NAME": "pull_request"})
        self.assertEqual(authenticated_actor({
            "GITHUB_ACTIONS": "true", "GITHUB_ACTOR": "duncan", "GITHUB_EVENT_NAME": "pull_request"
        }), "duncan")


if __name__ == "__main__": unittest.main()
