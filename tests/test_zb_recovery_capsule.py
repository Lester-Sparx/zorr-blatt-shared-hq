from __future__ import annotations

import base64
import json
import unittest

from recovery.zb_recovery import RecoveryError, collect_recovery_state


class ZbRecoveryCapsuleTests(unittest.TestCase):
    @staticmethod
    def manifest() -> dict[str, object]:
        return {
            "schema": "ZB_RECOVERY_CAPSULE_V1",
            "repository": "Lester-Sparx/zorr-blatt-shared-hq",
            "expected_actor": "Lester-Sparx",
            "required_permissions": ["admin", "push", "pull"],
            "main_branch": "main",
            "archive_branch": "zb-archive-v1",
            "checkpoint_path": "checkpoints/ZB_CHECKPOINT_CURRENT.json",
            "communication_bus_pr": 111,
        }

    @staticmethod
    def endpoint_map(*, actor: str = "Lester-Sparx", admin: bool = True) -> dict[str, object]:
        repo = "repos/Lester-Sparx/zorr-blatt-shared-hq"
        checkpoint = {
            "schemaId": "ZB_CHECKPOINT_V1",
            "checkpointId": "2026-08-29-RC",
            "project": "ZORR BLATT",
        }
        return {
            "user": {"login": actor},
            repo: {
                "full_name": "Lester-Sparx/zorr-blatt-shared-hq",
                "permissions": {"admin": admin, "push": True, "pull": True},
            },
            f"{repo}/branches/main": {"name": "main", "commit": {"sha": "a" * 40}},
            f"{repo}/branches/zb-archive-v1": {
                "name": "zb-archive-v1",
                "commit": {"sha": "b" * 40},
            },
            f"{repo}/contents/checkpoints/ZB_CHECKPOINT_CURRENT.json?ref=main": {
                "sha": "c" * 40,
                "encoding": "base64",
                "content": base64.b64encode(json.dumps(checkpoint).encode("utf-8")).decode("ascii"),
            },
            f"{repo}/pulls/111": {
                "number": 111,
                "state": "open",
                "draft": True,
                "base": {"ref": "main", "sha": "a" * 40},
                "head": {"ref": "communication-bus", "sha": "d" * 40},
            },
            f"{repo}/issues/111/comments?per_page=100": [
                {
                    "id": 9001,
                    "body": "ZB_AGENT_MESSAGE_V1\nROLE = DUNCAN\nSTATE = PASS",
                    "created_at": "2026-08-29T08:00:00Z",
                    "user": {"login": "Lester-Sparx"},
                }
            ],
            f"{repo}/pulls?state=open&per_page=100": [
                {
                    "number": 171,
                    "state": "open",
                    "draft": True,
                    "updated_at": "2026-08-29T08:41:57Z",
                    "base": {"ref": "main", "sha": "a" * 40},
                    "head": {"ref": "duncan3/example", "sha": "e" * 40},
                    "title": "Example active candidate",
                }
            ],
        }

    @staticmethod
    def fake_gh(mapping: dict[str, object]):
        def get(endpoint: str) -> object:
            if endpoint not in mapping:
                raise AssertionError(f"unexpected endpoint: {endpoint}")
            return mapping[endpoint]

        return get

    def test_wrong_authenticated_actor_fails_closed(self) -> None:
        mapping = self.endpoint_map(actor="someone-else")
        with self.assertRaisesRegex(RecoveryError, "RECOVERY_ACTOR_MISMATCH"):
            collect_recovery_state(self.manifest(), self.fake_gh(mapping))

    def test_missing_required_repository_permission_fails_closed(self) -> None:
        mapping = self.endpoint_map(admin=False)
        with self.assertRaisesRegex(RecoveryError, "RECOVERY_PERMISSION_MISSING:admin"):
            collect_recovery_state(self.manifest(), self.fake_gh(mapping))

    def test_valid_remote_state_binds_exact_checkpoint_and_heads(self) -> None:
        mapping = self.endpoint_map()
        state = collect_recovery_state(self.manifest(), self.fake_gh(mapping))
        self.assertEqual(state["actor"], "Lester-Sparx")
        self.assertEqual(state["repository"], "Lester-Sparx/zorr-blatt-shared-hq")
        self.assertEqual(state["main_sha"], "a" * 40)
        self.assertEqual(state["archive_sha"], "b" * 40)
        self.assertEqual(state["checkpoint_blob_sha"], "c" * 40)
        self.assertEqual(state["checkpoint"]["checkpointId"], "2026-08-29-RC")
        self.assertEqual(state["bus"]["number"], 111)
        self.assertEqual(state["bus"]["head_sha"], "d" * 40)
        self.assertEqual(state["bus_comments"][0]["id"], 9001)
        self.assertEqual(state["open_prs"][0]["head_sha"], "e" * 40)


if __name__ == "__main__":
    unittest.main()
