from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
WORKFLOW_PATH = ROOT / ".github/workflows/zb-communication-base.yml"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from zb_communication_base import (  # noqa: E402
    APPROVED_DESIGN_HEAD,
    EXPECTED_STAGES,
    GitHubApi,
    PersistenceError,
    ProtocolError,
    admit_event,
    main,
    parse_root_message,
    run_base,
    write_and_verify,
)

BASE_SHA = "a" * 40
TRACKER_URL = "https://api.github.com/repos/Lester-Sparx/zorr-blatt-shared-hq/issues/106"
BOT = "github-actions[bot]"
VALID_BODY = f"""ZB_AGENT_MESSAGE_V1
MESSAGE_ID = zb-native-r01-msg-001
EVENT_ID = zb-native-r01-evt-001
CORRELATION_ID = zb-native-r01
CAUSATION_MESSAGE_ID = NONE
TASK_ID = ZB_GITHUB_NATIVE_BASE_R01
FROM_ROLE = JINGO
TO_ROLE = LESTER
MESSAGE_KIND = ASSIGN
BASE_SHA = {BASE_SHA}
TASK_REVISION = 1
DESIGN_HEAD = 81c44232b72b4a98c8ad0ac2ea6a0a2876f988bc
NO_AUTO_MERGE = TRUE
"""


def valid_event(body: str = VALID_BODY) -> dict:
    return {
        "action": "created",
        "repository": {"full_name": "Lester-Sparx/zorr-blatt-shared-hq"},
        "issue": {"number": 111, "pull_request": {"url": "https://api.github.com/repos/Lester-Sparx/zorr-blatt-shared-hq/pulls/111"}},
        "comment": {"id": 9001, "body": body, "user": {"login": "Lester-Sparx"}},
    }


def admitted() -> tuple:
    return admit_event(valid_event(), expected_base_sha=BASE_SHA, run_id="12345", run_attempt="2", github_sha=BASE_SHA)


class RootParserAdmissionTest(unittest.TestCase):
    def test_valid_root_message_and_event_are_admitted(self):
        message = parse_root_message(VALID_BODY)
        self.assertEqual(message.message_id, "zb-native-r01-msg-001")
        self.assertEqual(message.task_id, "ZB_GITHUB_NATIVE_BASE_R01")
        self.assertEqual(message.task_revision, 1)
        self.assertEqual(message.design_head, APPROVED_DESIGN_HEAD)
        self.assertTrue(message.no_auto_merge)
        admitted_message, context = admitted()
        self.assertEqual(admitted_message, message)
        self.assertEqual((context.repository, context.issue_number, context.comment_id, context.actor), ("Lester-Sparx/zorr-blatt-shared-hq", 111, 9001, "Lester-Sparx"))
        self.assertEqual((context.run_id, context.run_attempt), ("12345", "2"))

    def test_duplicate_field_is_rejected(self):
        with self.assertRaisesRegex(ProtocolError, "duplicate"):
            parse_root_message(VALID_BODY + "MESSAGE_ID = duplicate\n")

    def test_unknown_field_is_rejected(self):
        with self.assertRaisesRegex(ProtocolError, "unknown"):
            parse_root_message(VALID_BODY + "SURPRISE = nope\n")

    def test_wrong_marker_is_rejected(self):
        with self.assertRaisesRegex(ProtocolError, "marker"):
            parse_root_message(VALID_BODY.replace("ZB_AGENT_MESSAGE_V1", "NOT_A_MESSAGE", 1))

    def test_wrong_task_revision_design_or_no_auto_merge_is_rejected(self):
        mutations = {"TASK_ID": "OTHER_TASK", "TASK_REVISION": "2", "DESIGN_HEAD": "b" * 40, "NO_AUTO_MERGE": "FALSE"}
        for field, value in mutations.items():
            with self.subTest(field=field):
                old = next(line for line in VALID_BODY.splitlines() if line.startswith(field + " = "))
                with self.assertRaises(ProtocolError):
                    parse_root_message(VALID_BODY.replace(old, f"{field} = {value}"))

    def test_illegal_initial_role_transition_is_rejected(self):
        for field, value in (("FROM_ROLE", "LESTER"), ("TO_ROLE", "DUNCAN"), ("MESSAGE_KIND", "RETURN")):
            with self.subTest(field=field):
                old = next(line for line in VALID_BODY.splitlines() if line.startswith(field + " = "))
                with self.assertRaises(ProtocolError):
                    parse_root_message(VALID_BODY.replace(old, f"{field} = {value}"))

    def test_stale_base_sha_is_rejected(self):
        with self.assertRaisesRegex(ProtocolError, "BASE_SHA"):
            admit_event(valid_event(), expected_base_sha="b" * 40, run_id="1", run_attempt="1", github_sha=BASE_SHA)

    def test_foreign_actor_wrong_pr_non_pr_wrong_action_and_repo_are_rejected(self):
        cases = []
        event = valid_event(); event["comment"]["user"]["login"] = "Mallory"; cases.append(event)
        event = valid_event(); event["issue"]["number"] = 999; cases.append(event)
        event = valid_event(); event["issue"].pop("pull_request"); cases.append(event)
        event = valid_event(); event["action"] = "edited"; cases.append(event)
        event = valid_event(); event["repository"]["full_name"] = "other/repo"; cases.append(event)
        for event in cases:
            with self.subTest(event=event), self.assertRaises(ProtocolError):
                admit_event(copy.deepcopy(event), expected_base_sha=BASE_SHA, run_id="1", run_attempt="1", github_sha=BASE_SHA)


class FakePort:
    def __init__(self, readback: dict | None = None):
        self.created: list[str] = []
        self.readback = readback

    def create_tracker_comment(self, body: str) -> int:
        self.created.append(body); return 9001

    def read_comment(self, comment_id: int) -> dict:
        return self.readback or {"id": comment_id, "body": self.created[-1], "issue_url": TRACKER_URL}

    def list_tracker_comments(self) -> list[dict]:
        return []


class PersistenceBoundaryTest(unittest.TestCase):
    def test_write_and_verify_returns_remote_id_after_exact_match(self):
        port = FakePort(); self.assertEqual(write_and_verify(port, "BODY"), 9001); self.assertEqual(port.created, ["BODY"])

    def test_write_and_verify_rejects_id_body_or_container_mismatch(self):
        mismatches = [
            {"id": 9002, "body": "BODY", "issue_url": TRACKER_URL},
            {"id": 9001, "body": "OTHER", "issue_url": TRACKER_URL},
            {"id": 9001, "body": "BODY", "issue_url": TRACKER_URL.replace("106", "999")},
        ]
        for readback in mismatches:
            with self.subTest(readback=readback), self.assertRaises(PersistenceError):
                write_and_verify(FakePort(readback), "BODY")

    def test_github_api_has_no_dangerous_mutation_surface(self):
        for method in ("merge_pull_request", "update_file", "update_issue", "update_pull_request", "dispatch_workflow", "write_contents"):
            self.assertFalse(hasattr(GitHubApi, method), method)


class RecordingPort:
    def __init__(self, existing: list[dict] | None = None):
        self.comments = list(existing or []); self.created: list[str] = []; self.next_id = 10000

    def create_tracker_comment(self, body: str) -> int:
        comment_id = self.next_id; self.next_id += 1
        self.comments.append({"id": comment_id, "body": body, "issue_url": TRACKER_URL, "user": {"login": BOT}})
        self.created.append(body)
        return comment_id

    def read_comment(self, comment_id: int) -> dict:
        for comment in self.comments:
            if comment.get("id") == comment_id:
                return dict(comment)
        raise AssertionError(f"missing comment {comment_id}")

    def list_tracker_comments(self) -> list[dict]:
        return [dict(comment) for comment in self.comments]


def receipt_record(message, context, *, state="RECEIVED", writer=BOT, issue_url=TRACKER_URL) -> dict:
    return {
        "id": 7001,
        "issue_url": issue_url,
        "user": {"login": writer},
        "body": "\n".join(["ZB_AGENT_RECEIPT_V1", f"MESSAGE_ID = {message.message_id}", f"SOURCE_COMMENT_ID = {context.comment_id}", f"STATE = {state}"]),
    }


class StateMachineTest(unittest.TestCase):
    def test_happy_path_writes_exact_order_provenance_and_stops_at_owner_gate(self):
        message, context = admitted(); port = RecordingPort()
        self.assertEqual(run_base(message, context, port), "OWNER_GATE_REQUIRED")
        self.assertEqual(len(port.created), 10)
        self.assertIn("STATE = RECEIVED", port.created[0])
        self.assertIn("STATE = RUNNING", port.created[1])
        self.assertIn("EXECUTION_ID = github-actions:12345:2", port.created[1])
        for body in port.created:
            self.assertIn("IMPLEMENTATION_PR = 118", body)
            self.assertIn(f"RUNNER_SHA = {BASE_SHA}", body)
            self.assertIn("PRODUCTION_ACTIVE = NO", body)
        results = port.created[2:9]
        self.assertEqual(len(results), len(EXPECTED_STAGES))
        for body, (from_role, to_role, kind) in zip(results, EXPECTED_STAGES):
            self.assertIn("STATE = RESULT", body); self.assertIn("RESULT_CODE = PASS", body)
            self.assertIn(f"LOGICAL_FROM_ROLE = {from_role}", body); self.assertIn(f"LOGICAL_TO_ROLE = {to_role}", body); self.assertIn(f"MESSAGE_KIND = {kind}", body)
        owner = port.created[-1]
        self.assertTrue(owner.startswith("ZB_OWNER_VIEW_V0\n")); self.assertIn("OWNER_GATE_REQUIRED = TRUE", owner); self.assertIn("OWNER_ACTION_REQUIRED = TRUE", owner)
        combined = "\n".join(port.created); self.assertNotIn("LOGICAL_TO_ROLE = OWNER", combined); self.assertNotIn("MESSAGE_KIND = OWNER", combined)

    def test_trusted_bot_replay_is_noop_without_duplicate_writes(self):
        message, context = admitted(); port = RecordingPort([receipt_record(message, context)])
        self.assertEqual(run_base(message, context, port), "NOOP_REPLAY"); self.assertEqual(port.created, [])

    def test_foreign_or_wrong_container_receipt_cannot_suppress_execution(self):
        message, context = admitted()
        forged = [receipt_record(message, context, writer="Mallory"), receipt_record(message, context, issue_url=TRACKER_URL.replace("106", "999"))]
        for record in forged:
            with self.subTest(record=record):
                port = RecordingPort([record])
                self.assertEqual(run_base(message, context, port), "OWNER_GATE_REQUIRED")
                self.assertEqual(len(port.created), 10)

    def test_malformed_tracker_record_does_not_grant_replay(self):
        message, context = admitted(); port = RecordingPort([receipt_record(message, context, state="BANANA")])
        self.assertEqual(run_base(message, context, port), "OWNER_GATE_REQUIRED"); self.assertEqual(len(port.created), 10)


class EntrypointWorkflowTest(unittest.TestCase):
    def _write_event(self, event: dict):
        temp = tempfile.TemporaryDirectory(); path = Path(temp.name) / "event.json"; path.write_text(json.dumps(event), encoding="utf-8"); return temp, str(path)

    def test_non_protocol_comment_is_ignored_without_github_port(self):
        temp, path = self._write_event(valid_event("ordinary prose")); self.addCleanup(temp.cleanup)
        def forbidden_factory(token: str): raise AssertionError("GitHub port must not be created for ordinary prose")
        env = {"GITHUB_EVENT_PATH": path, "GITHUB_REPOSITORY": "Lester-Sparx/zorr-blatt-shared-hq", "GITHUB_RUN_ID": "55", "GITHUB_RUN_ATTEMPT": "1", "GITHUB_SHA": BASE_SHA}
        self.assertEqual(main(environ=env, port_factory=forbidden_factory), 0)

    def test_valid_event_runs_base_through_injected_port(self):
        temp, path = self._write_event(valid_event()); self.addCleanup(temp.cleanup); port = RecordingPort(); seen = []
        def factory(token: str): seen.append(token); return port
        env = {"GITHUB_EVENT_PATH": path, "GITHUB_REPOSITORY": "Lester-Sparx/zorr-blatt-shared-hq", "GITHUB_RUN_ID": "12345", "GITHUB_RUN_ATTEMPT": "2", "GITHUB_SHA": BASE_SHA, "GITHUB_TOKEN": "test-token"}
        self.assertEqual(main(environ=env, port_factory=factory), 0); self.assertEqual(seen, ["test-token"]); self.assertEqual(len(port.created), 10); self.assertIn("OWNER_GATE_REQUIRED = TRUE", port.created[-1])

    def test_workflow_is_issue_comment_only_and_least_privilege(self):
        text = WORKFLOW_PATH.read_text(encoding="utf-8")
        for needle in ("issue_comment:", "types: [created]", "contents: read", "issues: write", "pull-requests: read", "GITHUB_TOKEN: ${{ github.token }}", "python3 scripts/zb_communication_base.py"):
            self.assertIn(needle, text)
        for needle in ("contents: write", "actions: write", "pull-requests: write", "workflow_dispatch", "schedule:", "secrets.", "PAT"):
            self.assertNotIn(needle, text)


if __name__ == "__main__":
    unittest.main()
