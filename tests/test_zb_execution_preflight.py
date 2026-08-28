from __future__ import annotations

import json
from pathlib import Path
import unittest

from scripts.zb_execution_preflight import (
    PreflightError,
    run_activation_preflight,
    run_implementation_preflight,
    validate_effective_opencode_config,
)
from scripts.zb_execution_profiles import PROFILES


ROOT = Path(__file__).resolve().parents[1]
TASKS = json.dumps({"tasks": [{"name": "zb:exec:lester:implement-r01"}, {"name": "zb:exec:duncan:qc-r01"}]})
RUNNER_SHA256 = "1150692afa94e71f872017e254ea55b6eece1eece3fe7e3a6d4c93d0a1b85cfc"
TASK_SHA256 = "27c0cd248c12cba03d8958d954a3df981c900be885ec9ce5f6a3cdc4e9a19316"
OPENCODE_SHA256 = "831e213e5f454d6e8b26f0fb24c7b3d42b40e47d73d154672a9192702eb08416"


def policy() -> dict:
    return json.loads((ROOT / "config/zb-execution/opencode-r01.json").read_text(encoding="utf-8"))


def activation_kwargs() -> dict:
    return {
        "repository_private": True,
        "disposable_host": False,
        "runner_version": "2.337.0",
        "runner_sha256": RUNNER_SHA256,
        "task_version": "3.53.1",
        "task_sha256": TASK_SHA256,
        "opencode_version": "1.18.25",
        "opencode_sha256": OPENCODE_SHA256,
        "task_inventory_json": TASKS,
        "profile": PROFILES["LESTER_IMPLEMENT_R01"],
        "effective_config_json": json.dumps(policy()),
    }


class PreflightTests(unittest.TestCase):
    def test_implementation_preflight_accepts_static_inventory_and_exact_versions(self) -> None:
        run_implementation_preflight(
            profile=PROFILES["LESTER_IMPLEMENT_R01"],
            task_version="3.53.1",
            task_inventory_json=TASKS,
            opencode_version="1.18.25",
        )

    def test_implementation_preflight_rejects_wrong_task_or_opencode_version_and_inventory(self) -> None:
        with self.assertRaisesRegex(PreflightError, "TASK_VERSION_MISMATCH"):
            run_implementation_preflight(
                profile=PROFILES["LESTER_IMPLEMENT_R01"], task_version="3.53.0", task_inventory_json=TASKS, opencode_version="1.18.25"
            )
        with self.assertRaisesRegex(PreflightError, "OPENCODE_VERSION_MISMATCH"):
            run_implementation_preflight(
                profile=PROFILES["LESTER_IMPLEMENT_R01"], task_version="3.53.1", task_inventory_json=TASKS, opencode_version="1.18.24"
            )
        bad_inventory = json.dumps({"tasks": [{"name": "zb:exec:lester:implement-r01"}]})
        with self.assertRaisesRegex(PreflightError, "TASK_INVENTORY_MISMATCH"):
            run_implementation_preflight(
                profile=PROFILES["LESTER_IMPLEMENT_R01"], task_version="3.53.1", task_inventory_json=bad_inventory, opencode_version="1.18.25"
            )

    def test_public_repository_blocks_owner_pc_activation_before_runner_use(self) -> None:
        kwargs = activation_kwargs()
        kwargs["repository_private"] = False
        with self.assertRaisesRegex(PreflightError, "RUNNER_SECURITY_GATE_BLOCKED"):
            run_activation_preflight(**kwargs)

    def test_disposable_host_can_satisfy_public_repo_security_gate(self) -> None:
        kwargs = activation_kwargs()
        kwargs["repository_private"] = False
        kwargs["disposable_host"] = True
        run_activation_preflight(**kwargs)

    def test_activation_requires_exact_runner_task_and_opencode_provenance(self) -> None:
        for key, bad, code in (
            ("runner_version", "2.336.0", "RUNNER_VERSION_MISMATCH"),
            ("runner_sha256", "0" * 64, "RUNNER_PROVENANCE_MISMATCH"),
            ("task_version", "3.53.0", "TASK_VERSION_MISMATCH"),
            ("task_sha256", "0" * 64, "TASK_PROVENANCE_MISMATCH"),
            ("opencode_version", "1.18.24", "OPENCODE_VERSION_MISMATCH"),
            ("opencode_sha256", "0" * 64, "OPENCODE_PROVENANCE_MISMATCH"),
        ):
            with self.subTest(key=key):
                kwargs = activation_kwargs()
                kwargs[key] = bad
                with self.assertRaisesRegex(PreflightError, code):
                    run_activation_preflight(**kwargs)

    def test_effective_config_accepts_static_policy(self) -> None:
        validate_effective_opencode_config(json.dumps(policy()))

    def test_effective_config_rejects_mcp_plugin_agent_override_and_widened_permissions(self) -> None:
        mutations = []
        cfg = policy(); cfg["mcp"] = {"evil": {"command": ["cmd", "/c", "whoami"]}}; mutations.append((cfg, "UNAPPROVED_MCP"))
        cfg = policy(); cfg["plugin"] = ["evil-plugin"]; mutations.append((cfg, "UNAPPROVED_PLUGIN"))
        cfg = policy(); cfg["agent"] = {"build": {"permission": "allow"}}; mutations.append((cfg, "UNAPPROVED_AGENT_OVERRIDE"))
        cfg = policy(); cfg["permission"]["external_directory"] = "allow"; mutations.append((cfg, "EXTERNAL_DIRECTORY_WIDENED"))
        cfg = policy(); cfg["permission"]["bash"]["*"] = "allow"; mutations.append((cfg, "SHELL_PERMISSION_WIDENED"))
        cfg = policy(); cfg["permission"]["webfetch"] = "allow"; mutations.append((cfg, "NETWORK_PERMISSION_WIDENED"))
        cfg = policy(); cfg["permission"]["task"] = "allow"; mutations.append((cfg, "SUBAGENT_PERMISSION_WIDENED"))
        for cfg, code in mutations:
            with self.subTest(code=code), self.assertRaisesRegex(PreflightError, code):
                validate_effective_opencode_config(json.dumps(cfg))

    def test_activation_rejects_unverifiable_effective_config_and_task_inventory(self) -> None:
        kwargs = activation_kwargs()
        kwargs["effective_config_json"] = "not-json"
        with self.assertRaisesRegex(PreflightError, "EFFECTIVE_CONFIG_INVALID"):
            run_activation_preflight(**kwargs)

        kwargs = activation_kwargs()
        kwargs["task_inventory_json"] = json.dumps({"tasks": []})
        with self.assertRaisesRegex(PreflightError, "TASK_INVENTORY_MISMATCH"):
            run_activation_preflight(**kwargs)


if __name__ == "__main__":
    unittest.main()
