from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from zb_communication_base import (  # noqa: E402
    APPROVED_DESIGN_HEAD,
    GitHubApi,
    PersistenceError,
    ProtocolError,
    admit_event,
    parse_root_message,
    write_and_verify,
)


BASE_SHA = "a" * 40
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
        "issue": {
            "number": 111,
            "pull_request": {"url": "https://api.github.com/repos/Lester-Sparx/zorr-blatt-shared-hq/pulls/111"},
        },
        "comment": {
            "id": 9001,
            "body": body,
            "user": {"login": "Lester-Sparx"},
        },
    }


class RootParserAdmissionTest(unittest.TestCase):
    def test_valid_root_message_and_event_are_admitted(self):
        message = parse_root_message(VALID_BODY)
        self.assertEqual(message.message_id, "zb-native-r01-msg-001")
        self.assertEqual(message.task_id, "ZB_GITHUB_NATIVE_BASE_R01")
        self.assertEqual(message.task_revision, 1)
        self.assertEqual(message.design_head, APPROVED_DESIGN_HEAD)
        self.assertTrue(message.no_auto_merge)

        admitted_message, context = admit_event(
            valid_event(),
            expected_base_sha=BASE_SHA,
            run_id="12345",
            run_attempt="2",
            github_sha=BASE_SHA,
        )
        self.assertEqual(admitted_message, message)
        self.assertEqual(context.repository, "Lester-Sparx/zorr-blatt-shared-hq")
        self.assertEqual(context.issue_number, 111)
        self.assertEqual(context.comment_id, 9001)
        self.assertEqual(context.actor, "Lester-Sparx")
        self.assertEqual(context.run_id, "12345")
        self.assertEqual(context.run_attempt, "2")

    def test_duplicate_field_is_rejected(self):
        body = VALID_BODY + "MESSAGE_ID = duplicate\n"
        with self.assertRaisesRegex(ProtocolError, "duplicate"):
            parse_root_message(body)

    def test_unknown_field_is_rejected(self):
        body = VALID_BODY + "SURPRISE = nope\n"
        with self.assertRaisesRegex(ProtocolError, "unknown"):
            parse_root_message(body)

    def test_wrong_marker_is_rejected(self):
        body = VALID_BODY.replace("ZB_AGENT_MESSAGE_V1", "NOT_A_MESSAGE", 1)
        with self.assertRaisesRegex(ProtocolError, "marker"):
            parse_root_message(body)

    def test_wrong_task_revision_design_or_no_auto_merge_is_rejected(self):
        mutations = {
            "TASK_ID": "OTHER_TASK",
            "TASK_REVISION": "2",
            "DESIGN_HEAD": "b" * 40,
            "NO_AUTO_MERGE": "FALSE",
        }
        for field, value in mutations.items():
            with self.subTest(field=field):
                old_line = next(line for line in VALID_BODY.splitlines() if line.startswith(field + " = "))
                body = VALID_BODY.replace(old_line, f"{field} = {value}")
                with self.assertRaises(ProtocolError):
                    parse_root_message(body)

    def test_illegal_initial_role_transition_is_rejected(self):
        for field, value in (("FROM_ROLE", "LESTER"), ("TO_ROLE", "DUNCAN"), ("MESSAGE_KIND", "RETURN")):
            with self.subTest(field=field):
                old_line = next(line for line in VALID_BODY.splitlines() if line.startswith(field + " = "))
                body = VALID_BODY.replace(old_line, f"{field} = {value}")
                with self.assertRaises(ProtocolError):
                    parse_root_message(body)

    def test_stale_base_sha_is_rejected(self):
        with self.assertRaisesRegex(ProtocolError, "BASE_SHA"):
            admit_event(
                valid_event(),
                expected_base_sha="b" * 40,
                run_id="1",
                run_attempt="1",
                github_sha=BASE_SHA,
            )

    def test_foreign_actor_wrong_pr_non_pr_and_wrong_action_are_rejected(self):
        cases = []

        foreign = valid_event()
        foreign["comment"]["user"]["login"] = "Mallory"
        cases.append(foreign)

        wrong_pr = valid_event()
        wrong_pr["issue"]["number"] = 999
        cases.append(wrong_pr)

        not_pr = valid_event()
        not_pr["issue"].pop("pull_request")
        cases.append(not_pr)

        edited = valid_event()
        edited["action"] = "edited"
        cases.append(edited)

        wrong_repo = valid_event()
        wrong_repo["repository"]["full_name"] = "other/repo"
        cases.append(wrong_repo)

        for event in cases:
            with self.subTest(event=event):
                with self.assertRaises(ProtocolError):
                    admit_event(
                        copy.deepcopy(event),
                        expected_base_sha=BASE_SHA,
                        run_id="1",
                        run_attempt="1",
                        github_sha=BASE_SHA,
                    )


class FakePort:
    def __init__(self, readback: dict | None = None):
        self.created: list[str] = []
        self.readback = readback

    def create_tracker_comment(self, body: str) -> int:
        self.created.append(body)
        return 9001

    def read_comment(self, comment_id: int) -> dict:
        if self.readback is not None:
            return self.readback
        return {
            "id": comment_id,
            "body": self.created[-1],
            "issue_url": "https://api.github.com/repos/Lester-Sparx/zorr-blatt-shared-hq/issues/106",
        }

    def list_tracker_comments(self) -> list[dict]:
        return []


class PersistenceBoundaryTest(unittest.TestCase):
    def test_write_and_verify_returns_remote_id_after_exact_match(self):
        port = FakePort()
        self.assertEqual(write_and_verify(port, "BODY"), 9001)
        self.assertEqual(port.created, ["BODY"])

    def test_write_and_verify_rejects_id_body_or_container_mismatch(self):
        mismatches = [
            {"id": 9002, "body": "BODY", "issue_url": "https://api.github.com/repos/Lester-Sparx/zorr-blatt-shared-hq/issues/106"},
            {"id": 9001, "body": "OTHER", "issue_url": "https://api.github.com/repos/Lester-Sparx/zorr-blatt-shared-hq/issues/106"},
            {"id": 9001, "body": "BODY", "issue_url": "https://api.github.com/repos/Lester-Sparx/zorr-blatt-shared-hq/issues/999"},
        ]
        for readback in mismatches:
            with self.subTest(readback=readback):
                with self.assertRaises(PersistenceError):
                    write_and_verify(FakePort(readback), "BODY")

    def test_github_api_has_no_dangerous_mutation_surface(self):
        for method in (
            "merge_pull_request",
            "update_file",
            "update_issue",
            "update_pull_request",
            "dispatch_workflow",
            "write_contents",
        ):
            self.assertFalse(hasattr(GitHubApi, method), method)


if __name__ == "__main__":
    unittest.main()
