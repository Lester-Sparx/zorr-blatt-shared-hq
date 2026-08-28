import json
import tempfile
import unittest
from pathlib import Path

from _support import ROOT
from hq_adapter import HQError, authenticated_actor, require_role, role_registry


class IdentitySeparationTest(unittest.TestCase):
    def test_single_transport_registry_separates_transport_from_logical_roles(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "roles.yml"
            path.write_text(json.dumps({
                "approvedTransportActors": ["Lester-Sparx"],
                "logicalRoles": ["OWNER", "LESTER", "DUNCAN", "DJANGO", "JINGO"],
            }))
            registry = role_registry(path)
            require_role("Lester-Sparx", "DUNCAN", registry)
            require_role("Lester-Sparx", "DJANGO", registry)

    def test_unknown_transport_and_unknown_logical_role_are_rejected(self):
        registry = role_registry()
        with self.assertRaisesRegex(HQError, "APPROVED GITHUB TRANSPORT"):
            require_role("Duncan-Sparx-ZB", "DUNCAN", registry)
        with self.assertRaisesRegex(HQError, "LOGICAL ROLE"):
            require_role("Lester-Sparx", "INVENTED", registry)

    def test_caller_field_is_not_identity(self):
        with self.assertRaisesRegex(HQError, "GITHUB ACTIONS"):
            authenticated_actor({"GITHUB_ACTOR": "duncan", "GITHUB_EVENT_NAME": "pull_request"})
        self.assertEqual(authenticated_actor({
            "GITHUB_ACTIONS": "true", "GITHUB_ACTOR": "duncan", "GITHUB_EVENT_NAME": "pull_request"
        }), "duncan")


if __name__ == "__main__": unittest.main()
