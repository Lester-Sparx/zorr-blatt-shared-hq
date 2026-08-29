from __future__ import annotations

import base64
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

from recovery.zb_recovery import (
    RecoveryError,
    collect_recovery_state,
    render_recovery_state_json,
    render_resume_packet,
    run_gh_json,
    write_outputs,
)


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

    def valid_state(self) -> dict[str, object]:
        return collect_recovery_state(self.manifest(), self.fake_gh(self.endpoint_map()))

    def test_wrong_authenticated_actor_fails_closed(self) -> None:
        mapping = self.endpoint_map(actor="someone-else")
        with self.assertRaisesRegex(RecoveryError, "RECOVERY_ACTOR_MISMATCH"):
            collect_recovery_state(self.manifest(), self.fake_gh(mapping))

    def test_missing_required_repository_permission_fails_closed(self) -> None:
        mapping = self.endpoint_map(admin=False)
        with self.assertRaisesRegex(RecoveryError, "RECOVERY_PERMISSION_MISSING:admin"):
            collect_recovery_state(self.manifest(), self.fake_gh(mapping))

    def test_valid_remote_state_binds_exact_checkpoint_and_heads(self) -> None:
        state = self.valid_state()
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

    def test_resume_packet_is_exact_bound_and_orders_fresh_github_read(self) -> None:
        packet = render_resume_packet(self.manifest(), self.valid_state())
        for expected in (
            "GITHUB_ACTOR = Lester-Sparx",
            "REPOSITORY = Lester-Sparx/zorr-blatt-shared-hq",
            f"MAIN_SHA = {'a' * 40}",
            f"ARCHIVE_SHA = {'b' * 40}",
            "CHECKPOINT_ID = 2026-08-29-RC",
            f"CHECKPOINT_BLOB_SHA = {'c' * 40}",
            "COMMUNICATION_BUS_PR = 111",
            f"COMMUNICATION_BUS_HEAD = {'d' * 40}",
            "ACTIVE_PR_171_HEAD = " + "e" * 40,
            "NO CHAT IS PROJECT MEMORY. GITHUB DURABLE EVIDENCE IS PROJECT MEMORY.",
            "Fresh-read repository, main, zb-archive-v1, checkpoint, PR #111, and active PR heads before any mutation.",
            "This packet cannot grant privileges.",
        ):
            self.assertIn(expected, packet)

    def test_rendered_outputs_exclude_untrusted_secret_material(self) -> None:
        state = self.valid_state()
        state["untrusted_environment"] = {
            "GH_TOKEN": "ghp_TEST_SENTINEL",
            "GITHUB_APP_PRIVATE_KEY": "PRIVATE_KEY_SENTINEL",
        }
        json_text = render_recovery_state_json(state)
        packet = render_resume_packet(self.manifest(), state)
        for secret in ("ghp_TEST_SENTINEL", "PRIVATE_KEY_SENTINEL"):
            self.assertNotIn(secret, json_text)
            self.assertNotIn(secret, packet)
        self.assertNotIn("untrusted_environment", json_text)

    def test_write_outputs_creates_only_exact_atomic_artifacts(self) -> None:
        state = self.valid_state()
        state["untrusted_environment"] = {"GH_TOKEN": "ghp_TEST_SENTINEL"}
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / ".runtime"
            state_path, packet_path = write_outputs(self.manifest(), state, output_dir)
            self.assertEqual(state_path, output_dir / "RECOVERY_STATE.json")
            self.assertEqual(packet_path, output_dir / "RESUME_PACKET.md")
            self.assertEqual(
                sorted(path.name for path in output_dir.iterdir()),
                ["RECOVERY_STATE.json", "RESUME_PACKET.md"],
            )
            self.assertNotIn("ghp_TEST_SENTINEL", state_path.read_text(encoding="utf-8"))
            self.assertNotIn("ghp_TEST_SENTINEL", packet_path.read_text(encoding="utf-8"))
            self.assertFalse((output_dir / "RECOVERY_STATE.json.tmp").exists())
            self.assertFalse((output_dir / "RESUME_PACKET.md.tmp").exists())

    def test_gh_json_adapter_matches_existing_shell_false_pattern(self) -> None:
        calls: list[tuple[list[str], dict[str, object]]] = []

        def runner(args: list[str], **kwargs: object):
            calls.append((args, kwargs))
            return SimpleNamespace(returncode=0, stdout='{"login":"Lester-Sparx"}', stderr="")

        self.assertEqual(run_gh_json("user", runner=runner), {"login": "Lester-Sparx"})
        self.assertEqual(calls[0][0], ["gh", "api", "user"])
        self.assertIs(calls[0][1]["shell"], False)
        self.assertIs(calls[0][1]["capture_output"], True)
        self.assertIs(calls[0][1]["text"], True)

    def test_gh_json_adapter_fails_closed_on_invalid_json(self) -> None:
        def runner(args: list[str], **kwargs: object):
            return SimpleNamespace(returncode=0, stdout="not-json", stderr="")

        with self.assertRaisesRegex(RecoveryError, "RECOVERY_GH_OUTPUT_INVALID"):
            run_gh_json("user", runner=runner)

    def test_one_folder_entrypoint_taskfile_and_mcp_config_are_secret_free(self) -> None:
        start_cmd = Path("recovery/START_RECOVERY.cmd").read_text(encoding="utf-8")
        taskfile = Path("recovery/Taskfile.yml").read_text(encoding="utf-8")
        mcp = json.loads(Path("recovery/mcp.github.oauth.json").read_text(encoding="utf-8"))
        fallback = Path("recovery/GITHUB_APP_FALLBACK.env.example").read_text(encoding="utf-8")
        manifest = json.loads(Path("recovery/recovery_manifest.json").read_text(encoding="utf-8"))

        self.assertIn("task", start_cmd.lower())
        self.assertIn("recovery/Taskfile.yml", start_cmd.replace("\\", "/"))
        self.assertNotIn("ghp_", start_cmd.lower())
        self.assertNotIn("github_pat_", start_cmd.lower())

        for task in ("doctor:", "recover:", "mcp:"):
            self.assertIn(task, taskfile)
        self.assertIn("dir: '..'", taskfile)
        self.assertIn("deps: [doctor]", taskfile)
        self.assertIn("python -X utf8 -m recovery.zb_recovery", taskfile)
        self.assertIn("github-mcp-server stdio", taskfile)

        self.assertEqual(mcp["mcpServers"]["github"]["command"], "github-mcp-server")
        self.assertEqual(mcp["mcpServers"]["github"]["args"], ["stdio"])
        self.assertNotIn("env", mcp["mcpServers"]["github"])

        self.assertEqual(
            fallback.splitlines(),
            [
                "GITHUB_APP_ID=",
                "GITHUB_APP_INSTALLATION_ID=",
                "GITHUB_APP_PRIVATE_KEY_PATH=",
            ],
        )
        mcp_component = manifest["components"]["github_mcp_server"]
        self.assertEqual(mcp_component["version"], "1.0.5")
        self.assertEqual(
            mcp_component["windows_x86_64_sha256"],
            "92523838eaaac426aeb4ffc4540c5d3c49a6c1f627ff5f61ce585553240c2e09",
        )


if __name__ == "__main__":
    unittest.main()
