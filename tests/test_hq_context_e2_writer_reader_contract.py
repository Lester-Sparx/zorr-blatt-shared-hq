from __future__ import annotations

from types import SimpleNamespace
import unittest
from unittest.mock import patch

from scripts import hq_pre_action
from scripts import zb_communication_r02b as r02b


BUS_URL = "https://api.github.com/repos/Lester-Sparx/zorr-blatt-shared-hq/issues/111"
TRACKER_URL = "https://api.github.com/repos/Lester-Sparx/zorr-blatt-shared-hq/issues/106"


class WriterPort:
    def __init__(self) -> None:
        self.comments: list[dict[str, object]] = []

    def create_tracker_comment(self, body: str) -> int:
        comment_id = 9901
        self.comments.append(
            {
                "id": comment_id,
                "body": body,
                "issue_url": r02b.TRACKER_ISSUE_URL,
                "user": {"login": r02b.STATE_WRITER},
            }
        )
        return comment_id

    def read_comment(self, comment_id: int) -> dict[str, object]:
        for comment in self.comments:
            if comment["id"] == comment_id:
                return dict(comment)
        raise AssertionError(comment_id)


class ReaderApi:
    def __init__(self, terminal_comment: dict[str, object]) -> None:
        self.terminal_comment = dict(terminal_comment)
        self.terminal_comment.update(
            {
                "issue_url": TRACKER_URL,
                "created_at": "2026-09-01T06:30:00Z",
                "updated_at": "2026-09-01T06:30:00Z",
                "user": {"login": "github-actions[bot]"},
            }
        )

    def read_comment(self, comment_id: int) -> dict[str, object]:
        if comment_id == 8801:
            return {
                "id": 8801,
                "issue_url": BUS_URL,
                "created_at": "2026-09-01T06:29:00Z",
                "updated_at": "2026-09-01T06:29:00Z",
                "author_association": "OWNER",
                "user": {"login": "Lester-Sparx"},
                "body": "\n".join(
                    [
                        "ZB_AGENT_TASK_R03_V1",
                        "MESSAGE_ID = msg-contract-17",
                        "EVENT_ID = evt-contract-17",
                        "CORRELATION_ID = corr-contract-42",
                        f"TASK_ID = {r02b.R02B_TASK_ID}",
                        f"TASK_REVISION = {r02b.R02B_TASK_REVISION}",
                        f"BASE_SHA = {'a' * 40}",
                        "TASK_SPEC_COMMENT_ID = 7701",
                    ]
                ),
            }
        if comment_id == 9901:
            return dict(self.terminal_comment)
        raise AssertionError(comment_id)

    def list_tracker_comments(self) -> list[dict[str, object]]:
        return [
            {
                "id": 9001,
                "issue_url": TRACKER_URL,
                "created_at": "2026-09-01T06:29:30Z",
                "updated_at": "2026-09-01T06:29:30Z",
                "user": {"login": "github-actions[bot]"},
                "body": "\n".join(
                    [
                        "ZB_R03_DISPATCH_V1",
                        "ROOT_COMMENT_ID = 8801",
                        "MESSAGE_ID = msg-contract-17",
                        "CORRELATION_ID = corr-contract-42",
                        f"TASK_ID = {r02b.R02B_TASK_ID}",
                        f"TASK_REVISION = {r02b.R02B_TASK_REVISION}",
                        f"BASE_SHA = {'a' * 40}",
                    ]
                ),
            }
        ]


class WriterReaderContractTests(unittest.TestCase):
    @staticmethod
    def request() -> SimpleNamespace:
        return SimpleNamespace(
            message_id="msg-contract-17",
            correlation_id="corr-contract-42",
            task_id=r02b.R02B_TASK_ID,
            task_revision=r02b.R02B_TASK_REVISION,
            base_sha="a" * 40,
        )

    @staticmethod
    def lester() -> SimpleNamespace:
        return SimpleNamespace(execution_id="exec-lester-contract-9")

    @staticmethod
    def duncan() -> SimpleNamespace:
        return SimpleNamespace(execution_id="exec-duncan-contract-10")

    @staticmethod
    def context() -> dict[str, object]:
        return {
            "action": "CLAIM_PASS",
            "directlyAdvancesPhysicalResult": True,
            "activeAttempt": False,
            "exactOwnerInputProvided": False,
            "prerequisiteAlreadyProven": False,
            "provenProcessBlocker": False,
            "processMutationCountForBlocker": 0,
            "newPhysicalBlocker": False,
            "provenExternalBoundary": False,
            "freshVerificationEvidence": True,
            "explicitOwnerImageMutationCommand": False,
        }

    @staticmethod
    def packet(*, duncan_execution_id: str = "exec-duncan-contract-10") -> dict[str, object]:
        fact = {
            "schema": "ZB_CONTEXT_FACT_V1",
            "fact_id": "writer-reader-terminal-pass",
            "class": "E2",
            "key": "RESULT",
            "value": "PASS",
            "exclusive": True,
            "verified": True,
            "authority": "GITHUB",
            "created_at": "2026-09-01T06:30:00Z",
            "scope_tags": ["LESTER", "SECURITY_R02"],
            "source_refs": ["github:issue-comment:9901"],
            "supersedes": [],
        }
        return {
            "schema": "ZB_CONTEXT_PACKET_V1",
            "status": "PROVEN",
            "mandatory_anchors": [
                {"key": "CURRENT_TASK", "value": "#106"},
                {"key": "MESSAGE_ID", "value": "msg-contract-17"},
                {"key": "CORRELATION_ID", "value": "corr-contract-42"},
                {"key": "TASK_ID", "value": r02b.R02B_TASK_ID},
                {"key": "TASK_REVISION", "value": r02b.R02B_TASK_REVISION},
                {"key": "BASE_SHA", "value": "a" * 40},
                {"key": "LESTER_EXECUTION_ID", "value": "exec-lester-contract-9"},
                {"key": "DUNCAN_EXECUTION_ID", "value": duncan_execution_id},
                {"key": "AUTHORITY_REF", "value": "github:issue-comment:8801"},
            ],
            "current_state": hq_pre_action.project_current_state([fact]),
            "jit_facets": {},
            "missing_facets": [],
            "source_refs": ["github:issue:106", "github:issue-comment:8801"],
        }

    def writer_comment(self) -> dict[str, object]:
        port = WriterPort()
        with (
            patch.object(r02b, "_original_finalize_substantive_execution", return_value="OWNER_GATE_REQUIRED"),
            patch.object(r02b._core, "parse_execution_request", return_value=self.request()),
            patch.object(r02b._core, "parse_execution_result", side_effect=[self.lester(), self.duncan()]),
        ):
            result = r02b.finalize_substantive_execution("request", "lester", "duncan", port)
        self.assertEqual(result, "OWNER_GATE_REQUIRED")
        self.assertEqual(len(port.comments), 1)
        return port.comments[0]

    def evaluate(self, *, duncan_execution_id: str = "exec-duncan-contract-10") -> dict[str, object]:
        api = ReaderApi(self.writer_comment())
        return hq_pre_action.evaluate_pre_action_with_github_freshness(
            self.context(),
            context_packet=self.packet(duncan_execution_id=duncan_execution_id),
            github_api=api,
        )

    def test_actual_machine_writer_output_is_accepted_by_fresh_context_reader(self) -> None:
        result = self.evaluate()
        self.assertEqual(
            (result["decision"], result["reason"]),
            ("ALLOW", "PRE_ACTION_GATE_PASS"),
        )

    def test_actual_machine_writer_output_cannot_be_reused_for_changed_execution(self) -> None:
        result = self.evaluate(duncan_execution_id="exec-duncan-unseen-11")
        self.assertEqual(
            (result["decision"], result["reason"]),
            ("BLOCK", "DURABLE_CONTEXT_EVIDENCE_SUBJECT_MISMATCH"),
        )


if __name__ == "__main__":
    unittest.main()
