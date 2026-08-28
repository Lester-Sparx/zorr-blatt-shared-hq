from __future__ import annotations

import json
from pathlib import Path
import unittest

from scripts.zb_execution_contract import parse_execution_request
import scripts.zb_execution_profiles as execution_profiles
from scripts.zb_execution_profiles import (
    OPENCODE_VERSION,
    PROFILES,
    TASK_VERSION,
    ExecutionProfileError,
    resolve_profile,
    validate_task_inventory,
    validate_taskfile_text,
    validate_toolchain_versions,
)


ROOT = Path(__file__).resolve().parents[1]
BASE_SHA = "0123456789abcdef0123456789abcdef01234567"
DESIGN_HEAD = "89abcdef0123456789abcdef0123456789abcdef"


def request_body(**overrides: str) -> str:
    fields = {
        "EXECUTION_REQUEST_ID": "exec-request-002",
        "MESSAGE_ID": "message-002",
        "EVENT_ID": "event-002",
        "CORRELATION_ID": "corr-002",
        "CAUSATION_MESSAGE_ID": "cause-002",
        "TASK_ID": "ZB_EXECUTION_PROOF_R01",
        "TASK_REVISION": "1",
        "LOGICAL_ROLE": "LESTER",
        "EXECUTION_PROFILE": "LESTER_IMPLEMENT_R01",
        "EXECUTION_PROFILE_VERSION": "1",
        "BASE_SHA": BASE_SHA,
        "AUTHORITY_REF": "issue:106:comment:5453724500",
        "DESIGN_HEAD": DESIGN_HEAD,
        "SOURCE_REFS": "issue:106;pr:122",
        "EVIDENCE_INPUT_REFS": "spec:120;plan:121",
        "ALLOWED_WRITE_SCOPE": "scripts/;tests/",
        "TIMEOUT_SECONDS": "900",
        "NO_AUTO_MERGE": "TRUE",
        "PRODUCTION_ACTIVE": "NO",
    }
    fields.update(overrides)
    return "ZB_EXECUTION_REQUEST_V1\n" + "\n".join(f"{key} = {value}" for key, value in fields.items()) + "\n"


class ProfileRegistryTests(unittest.TestCase):
    def test_registry_contains_only_static_profiles_including_r02a(self) -> None:
        self.assertEqual(set(PROFILES), {"LESTER_IMPLEMENT_R01", "LESTER_IMPLEMENT_R02A", "DUNCAN_QC_R01"})
        self.assertEqual(PROFILES["LESTER_IMPLEMENT_R01"].task_name, "zb:exec:lester:implement-r01")
        self.assertEqual(PROFILES["LESTER_IMPLEMENT_R01"].worker_backend, "opencode")
        self.assertEqual(PROFILES["LESTER_IMPLEMENT_R01"].max_timeout_seconds, 1800)
        r02a = PROFILES["LESTER_IMPLEMENT_R02A"]
        self.assertEqual(r02a.logical_role, "LESTER")
        self.assertEqual(r02a.task_name, "zb:exec:lester:implement-r02a")
        self.assertEqual(r02a.worker_backend, "copilot-cli")
        self.assertEqual(r02a.max_timeout_seconds, 1800)
        self.assertEqual(PROFILES["DUNCAN_QC_R01"].task_name, "zb:exec:duncan:qc-r01")
        self.assertEqual(PROFILES["DUNCAN_QC_R01"].worker_backend, "deterministic-qc")
        self.assertEqual(PROFILES["DUNCAN_QC_R01"].max_timeout_seconds, 900)
        self.assertEqual(getattr(execution_profiles, "COPILOT_CLI_VERSION", None), "1.0.80")
        self.assertEqual(getattr(execution_profiles, "COPILOT_MODEL", None), "gpt-5.3-codex")

    def test_resolve_profile_accepts_exact_authorized_request(self) -> None:
        profile = resolve_profile(parse_execution_request(request_body()))
        self.assertEqual(profile.name, "LESTER_IMPLEMENT_R01")
        self.assertEqual(profile.logical_role, "LESTER")

    def test_resolve_profile_accepts_exact_r02a_request(self) -> None:
        profile = resolve_profile(parse_execution_request(request_body(EXECUTION_PROFILE="LESTER_IMPLEMENT_R02A")))
        self.assertEqual(profile.name, "LESTER_IMPLEMENT_R02A")
        self.assertEqual(profile.logical_role, "LESTER")
        self.assertEqual(profile.worker_backend, "copilot-cli")

    def test_unknown_profile_rejected(self) -> None:
        request = parse_execution_request(request_body(EXECUTION_PROFILE="UNKNOWN_R01"))
        with self.assertRaisesRegex(ExecutionProfileError, "EXECUTION_PROFILE_REJECTED"):
            resolve_profile(request)

    def test_role_mismatch_rejected(self) -> None:
        request = parse_execution_request(request_body(LOGICAL_ROLE="DUNCAN"))
        with self.assertRaisesRegex(ExecutionProfileError, "EXECUTION_ROLE_MISMATCH"):
            resolve_profile(request)

    def test_version_mismatch_rejected(self) -> None:
        request = parse_execution_request(request_body(EXECUTION_PROFILE_VERSION="2"))
        with self.assertRaisesRegex(ExecutionProfileError, "EXECUTION_PROFILE_VERSION_MISMATCH"):
            resolve_profile(request)

    def test_timeout_escalation_rejected_but_reduction_allowed(self) -> None:
        with self.assertRaisesRegex(ExecutionProfileError, "EXECUTION_TIMEOUT_ESCALATION"):
            resolve_profile(parse_execution_request(request_body(TIMEOUT_SECONDS="1801")))
        profile = resolve_profile(parse_execution_request(request_body(TIMEOUT_SECONDS="30")))
        self.assertEqual(profile.name, "LESTER_IMPLEMENT_R01")

    def test_write_scope_may_reduce_but_never_expand_profile(self) -> None:
        profile = resolve_profile(parse_execution_request(request_body(ALLOWED_WRITE_SCOPE="scripts/zb_execution_contract.py;tests/")))
        self.assertEqual(profile.name, "LESTER_IMPLEMENT_R01")
        with self.assertRaisesRegex(ExecutionProfileError, "EXECUTION_WRITE_SCOPE_ESCALATION"):
            resolve_profile(parse_execution_request(request_body(ALLOWED_WRITE_SCOPE="scripts/;secrets/")))
        with self.assertRaisesRegex(ExecutionProfileError, "EXECUTION_WRITE_SCOPE_ESCALATION"):
            resolve_profile(parse_execution_request(request_body(ALLOWED_WRITE_SCOPE="../")))


class TaskAuthorityTests(unittest.TestCase):
    def test_task_inventory_must_exactly_match_static_profile_tasks(self) -> None:
        task_json = json.dumps(
            {
                "tasks": [
                    {"name": "zb:exec:lester:implement-r01"},
                    {"name": "zb:exec:lester:implement-r02a"},
                    {"name": "zb:exec:duncan:qc-r01"},
                ]
            }
        )
        validate_task_inventory(task_json, PROFILES["LESTER_IMPLEMENT_R01"])
        validate_task_inventory(task_json, PROFILES["DUNCAN_QC_R01"])
        validate_task_inventory(task_json, PROFILES["LESTER_IMPLEMENT_R02A"])

    def test_task_inventory_rejects_missing_extra_or_dynamic_names(self) -> None:
        bad_inventories = (
            {"tasks": [{"name": "zb:exec:lester:implement-r01"}, {"name": "zb:exec:duncan:qc-r01"}]},
            {"tasks": [{"name": "zb:exec:lester:implement-r01"}, {"name": "zb:exec:lester:implement-r02a"}, {"name": "zb:exec:duncan:qc-r01"}, {"name": "extra"}]},
            {"tasks": [{"name": "zb:exec:lester:{{.CLI_ARGS}}"}, {"name": "zb:exec:lester:implement-r02a"}, {"name": "zb:exec:duncan:qc-r01"}]},
        )
        for inventory in bad_inventories:
            with self.subTest(inventory=inventory), self.assertRaises(ExecutionProfileError):
                validate_task_inventory(json.dumps(inventory), PROFILES["LESTER_IMPLEMENT_R01"])

    def test_taskfile_is_windows_safe_static_and_has_no_dynamic_surface(self) -> None:
        text = (ROOT / "Taskfile.yml").read_text(encoding="utf-8")
        validate_taskfile_text(text)
        self.assertIn("version: '3'", text)
        self.assertIn("zb:exec:lester:implement-r01", text)
        self.assertIn("zb:exec:lester:implement-r02a", text)
        self.assertIn("zb:exec:duncan:qc-r01", text)
        self.assertIn("python -m scripts.zb_execution_cli execute --from-env", text)
        self.assertIn("python -m scripts.zb_execution_cli qc --from-env", text)
        self.assertNotIn("python scripts/zb_execution_cli.py", text)
        self.assertNotIn("$ZB_", text)
        self.assertNotIn("CLI_ARGS", text)
        self.assertNotIn("includes:", text)

    def test_taskfile_validator_rejects_remote_include_cli_args_templates_and_shell_path_interpolation(self) -> None:
        bad = (
            "version: '3'\nincludes:\n  remote: https://example.invalid/tasks.yml\n",
            "version: '3'\ntasks:\n  x:\n    cmds:\n      - echo {{.CLI_ARGS}}\n",
            "version: '3'\ntasks:\n  '{{.TASK_NAME}}':\n    cmds:\n      - echo no\n",
            "version: '3'\ntasks:\n  x:\n    cmds:\n      - python x.py --request \"$ZB_EXECUTION_REQUEST_PATH\"\n",
        )
        for text in bad:
            with self.subTest(text=text), self.assertRaises(ExecutionProfileError):
                validate_taskfile_text(text)


class ToolchainPinTests(unittest.TestCase):
    def test_exact_versions_are_required(self) -> None:
        self.assertEqual(TASK_VERSION, "3.53.1")
        self.assertEqual(OPENCODE_VERSION, "1.18.25")
        self.assertEqual(getattr(execution_profiles, "COPILOT_CLI_VERSION", None), "1.0.80")
        self.assertEqual(getattr(execution_profiles, "COPILOT_MODEL", None), "gpt-5.3-codex")
        validate_toolchain_versions(task_version="3.53.1", opencode_version=None)
        validate_toolchain_versions(task_version="3.53.1", opencode_version="1.18.25")
        with self.assertRaisesRegex(ExecutionProfileError, "TASK_VERSION_MISMATCH"):
            validate_toolchain_versions(task_version="3.53.0", opencode_version=None)
        with self.assertRaisesRegex(ExecutionProfileError, "OPENCODE_VERSION_MISMATCH"):
            validate_toolchain_versions(task_version="3.53.1", opencode_version="1.18.24")

    def test_toolchain_manifest_contains_exact_approved_pins(self) -> None:
        manifest = json.loads((ROOT / "config/zb-execution/toolchain-r01.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["actions_runner"]["version"], "2.337.0")
        self.assertEqual(
            manifest["actions_runner"]["windows_x64_sha256"],
            "1150692afa94e71f872017e254ea55b6eece1eece3fe7e3a6d4c93d0a1b85cfc",
        )
        self.assertEqual(manifest["task"]["version"], "3.53.1")
        self.assertEqual(
            manifest["task"]["windows_amd64_sha256"],
            "27c0cd248c12cba03d8958d954a3df981c900be885ec9ce5f6a3cdc4e9a19316",
        )
        self.assertEqual(manifest["opencode"]["version"], "1.18.25")
        self.assertEqual(manifest["opencode"]["windows_x64_asset"], "opencode-windows-x64.zip")
        self.assertEqual(
            manifest["opencode"]["windows_x64_sha256"],
            "831e213e5f454d6e8b26f0fb24c7b3d42b40e47d73d154672a9192702eb08416",
        )
        self.assertEqual(manifest["actions"]["checkout_v4"], "11d5960a326750d5838078e36cf38b85af677262")
        self.assertEqual(manifest["actions"]["upload_artifact_v7"], "043fb46d1a93c77aae656e7c1c64a875d1fc6a0a")
        self.assertEqual(manifest["actions"]["download_artifact_v8"], "3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c")


if __name__ == "__main__":
    unittest.main()
