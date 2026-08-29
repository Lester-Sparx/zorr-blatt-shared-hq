from __future__ import annotations

import unittest

from scripts.zb_r03_qc import (
    QcError,
    expected_candidate_binding,
    parse_candidate_binding,
    record_qc_pass,
    validate_candidate,
)
from scripts.zb_r03_router import resolve_task


BASE = "1" * 40
HEAD = "2" * 40


def candidate_body(**overrides: str) -> str:
    values = {
        "MESSAGE_ID": "msg-r03-001",
        "CORRELATION_ID": "corr-r03-001",
        "TASK_ID": "ZB_CODE_CHANGE_R03",
        "TASK_REVISION": "1",
        "BASE_SHA": BASE,
        "AUTHORITY_REF": "pr:111:comment:1234",
    }
    values.update(overrides)
    return "\n".join(
        [
            "ZB_R03_CANDIDATE_V1",
            *(f"{name} = {values[name]}" for name in values),
            "",
            "summary",
        ]
    )


def pull(*, body: str | None = None, head: str = HEAD, base: str = BASE, draft: bool = True, state: str = "open"):
    return {
        "number": 150,
        "state": state,
        "draft": draft,
        "merged": False,
        "body": candidate_body() if body is None else body,
        "base": {"ref": "main", "sha": base},
        "head": {"sha": head, "repo": {"full_name": "Lester-Sparx/zorr-blatt-shared-hq"}},
    }


FILES = [
    {"filename": "tests/test_example.py", "status": "modified", "changes": 2, "patch": "@@ -1 +1 @@\n-a\n+b"},
]


class FakePort:
    def __init__(self, pr=None, files=None, main_sha: str = BASE):
        self.pr = pull() if pr is None else pr
        self.files = FILES if files is None else files
        self.main_sha = main_sha
        self.writes: list[str] = []

    def read_pull(self, number: int):
        self.assert_number(number)
        return self.pr

    def list_pull_files(self, number: int):
        self.assert_number(number)
        return self.files

    def read_main_sha(self):
        return self.main_sha

    def create_tracker_comment(self, body: str):
        self.writes.append(body)
        return 999

    def read_comment(self, comment_id: int):
        if comment_id != 999:
            raise AssertionError("unexpected comment")
        return {
            "id": 999,
            "body": self.writes[-1],
            "issue_url": "https://api.github.com/repos/Lester-Sparx/zorr-blatt-shared-hq/issues/106",
            "user": {"login": "github-actions[bot]"},
        }

    @staticmethod
    def assert_number(number: int):
        if number != 150:
            raise AssertionError("unexpected PR")


class R03QcTests(unittest.TestCase):
    def binding(self):
        return expected_candidate_binding(
            message_id="msg-r03-001",
            correlation_id="corr-r03-001",
            task_id="ZB_CODE_CHANGE_R03",
            task_revision=1,
            base_sha=BASE,
            authority_ref="pr:111:comment:1234",
        )

    def test_candidate_binding_parser_is_exact_and_ordered(self):
        self.assertEqual(parse_candidate_binding(candidate_body()), self.binding())
        with self.assertRaisesRegex(QcError, "R03_CANDIDATE_BINDING_INVALID"):
            parse_candidate_binding(candidate_body().replace("MESSAGE_ID", "OTHER", 1))
        with self.assertRaisesRegex(QcError, "R03_CANDIDATE_BINDING_INVALID"):
            parse_candidate_binding(candidate_body().replace("MESSAGE_ID = msg-r03-001\nCORRELATION_ID", "CORRELATION_ID = corr-r03-001\nMESSAGE_ID"))

    def test_candidate_requires_open_draft_exact_base_same_repo_and_exact_binding(self):
        policy = resolve_task("ZB_CODE_CHANGE_R03", 1)
        self.assertEqual(validate_candidate(FakePort(), 150, self.binding(), policy), HEAD)
        bads = [
            FakePort(pr=pull(draft=False)),
            FakePort(pr=pull(state="closed")),
            FakePort(pr=pull(base="3" * 40)),
            FakePort(main_sha="4" * 40),
            FakePort(pr={**pull(), "base": {"ref": "dev", "sha": BASE}}),
            FakePort(pr={**pull(), "head": {"sha": HEAD, "repo": {"full_name": "other/repo"}}}),
            FakePort(pr=pull(body=candidate_body(MESSAGE_ID="wrong"))),
        ]
        for bad in bads:
            with self.subTest(pr=bad.pr):
                with self.assertRaises(QcError):
                    validate_candidate(bad, 150, self.binding(), policy)

    def test_changed_files_are_registry_bounded_and_binary_or_rename_escape_fails_closed(self):
        policy = resolve_task("ZB_CODE_CHANGE_R03", 1)
        bad_sets = [
            [{"filename": ".github/workflows/x.yml", "status": "modified", "changes": 1, "patch": "x"}],
            [{"filename": "tests/a.py", "previous_filename": ".github/workflows/x.yml", "status": "renamed", "changes": 1, "patch": "x"}],
            [{"filename": "tests/a.bin", "status": "modified", "changes": 1, "patch": None}],
            [{"filename": "../tests/a.py", "status": "modified", "changes": 1, "patch": "x"}],
        ]
        for files in bad_sets:
            with self.subTest(files=files):
                with self.assertRaises(QcError):
                    validate_candidate(FakePort(files=files), 150, self.binding(), policy)

    def test_changed_file_and_patch_limits_fail_closed(self):
        policy = resolve_task("ZB_CODE_CHANGE_R03", 1)
        too_many = [
            {"filename": f"tests/t{i}.py", "status": "modified", "changes": 1, "patch": "x"}
            for i in range(policy.max_changed_files + 1)
        ]
        with self.assertRaisesRegex(QcError, "R03_CANDIDATE_FILE_COUNT_EXCEEDED"):
            validate_candidate(FakePort(files=too_many), 150, self.binding(), policy)
        huge = [{"filename": "tests/a.py", "status": "modified", "changes": 1, "patch": "x" * (policy.max_patch_kb * 1024 + 1)}]
        with self.assertRaisesRegex(QcError, "R03_CANDIDATE_PATCH_EXCEEDED"):
            validate_candidate(FakePort(files=huge), 150, self.binding(), policy)

    def test_record_pass_revalidates_same_head_then_exact_write_readback(self):
        policy = resolve_task("ZB_CODE_CHANGE_R03", 1)
        port = FakePort()
        body = record_qc_pass(port, 150, HEAD, self.binding(), policy, execution_id="github-actions:1:duncan_qc")
        self.assertIn("ZB_R03_DUNCAN_QC_V1", body)
        self.assertIn(f"CANDIDATE_HEAD_SHA = {HEAD}", body)
        self.assertIn("STATE = PASS", body)
        self.assertIn("RESULT_CODE = QC_PASS", body)
        self.assertEqual(port.writes, [body])
        with self.assertRaisesRegex(QcError, "R03_CANDIDATE_HEAD_MOVED"):
            record_qc_pass(FakePort(pr=pull(head="3" * 40)), 150, HEAD, self.binding(), policy, execution_id="github-actions:1:duncan_qc")


if __name__ == "__main__":
    unittest.main()
