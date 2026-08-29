from __future__ import annotations

import unittest

from scripts import zb_r03_finalize as finalize
from scripts.zb_r03_finalize import FinalizeError, finalize_candidate, validate_standing_authorization
from scripts.zb_r03_qc import expected_candidate_binding
from scripts.zb_r03_router import resolve_task


BASE = "1bb4ada5270b4d0fc48eba0fb152259d08b15085"
HEAD = "2" * 40
MERGE = "3" * 40
AUTH_ID = 5457544639
TRACKER_URL = "https://api.github.com/repos/Lester-Sparx/zorr-blatt-shared-hq/issues/106"
CONSOLE_URL = "https://api.github.com/repos/Lester-Sparx/zorr-blatt-shared-hq/issues/39"

AUTH_BODY = "\n".join(
    [
        "ZB106_R03_STANDING_OWNER_AUTH_V1",
        "",
        "OWNER_COMMAND = УТВЕРЖДАЮ R03 DESIGN B — GH-AW / САМ УТВЕРЖДАЙ ВСЕ",
        "SCOPE = R03 AUTOMATION TRACK ONLY",
        "AUTHORIZATION = CONTINUE WITHOUT REPEATED HUMAN CHECKPOINTS AFTER FRESH EVIDENCE",
        "ALLOWED = spec -> plan -> TDD -> review -> merge -> activation for R03 automation track",
        "REQUIRED_GUARDS = fresh exact-head readback; CI green; independent DUNCAN review; deny-by-default task authority; immutable evidence; no silent drift",
        "NOT_AUTHORIZED = canon mutation; OWNER LOCK mutation; merge PR #111; mutate issue #102; mutate PR #103; unrelated production changes",
        f"MAIN_AT_AUTH = {BASE}",
        "R03_DESIGN = thin ZB authority/QC layer + github/gh-aw",
        "UPSTREAM = github/gh-aw",
        "UPSTREAM_PIN_CANDIDATE = v0.86.2",
        "PRODUCTION_ACTIVE = NO",
    ]
)


def binding():
    return expected_candidate_binding(
        message_id="msg-r03-001",
        correlation_id="corr-r03-001",
        task_id="ZB_CODE_CHANGE_R03",
        task_revision=1,
        base_sha=BASE,
        authority_ref="pr:111:comment:1234",
    )


def qc_body(head: str = HEAD) -> str:
    b = binding()
    return "\n".join(
        [
            "ZB_R03_DUNCAN_QC_V1",
            f"MESSAGE_ID = {b['MESSAGE_ID']}",
            f"CORRELATION_ID = {b['CORRELATION_ID']}",
            f"TASK_ID = {b['TASK_ID']}",
            f"TASK_REVISION = {b['TASK_REVISION']}",
            f"BASE_SHA = {b['BASE_SHA']}",
            f"AUTHORITY_REF = {b['AUTHORITY_REF']}",
            "CANDIDATE_PR = 150",
            f"CANDIDATE_HEAD_SHA = {head}",
            "DUNCAN_EXECUTION_ID = github-actions:1:1:duncan_qc",
            "STATE = PASS",
            "RESULT_CODE = QC_PASS",
            "PRODUCTION_ACTIVE = NO",
        ]
    )


def open_pull(head: str = HEAD):
    return {
        "number": 150,
        "state": "open",
        "draft": True,
        "merged": False,
        "merge_commit_sha": None,
        "base": {"ref": "main", "sha": BASE},
        "head": {"sha": head, "repo": {"full_name": "Lester-Sparx/zorr-blatt-shared-hq"}},
    }


class FakePort:
    def __init__(self, *, auth_body: str = AUTH_BODY, tracker=None, main_sha: str = BASE, candidate=None):
        self.auth_body = auth_body
        self.tracker = [qc_body()] if tracker is None else tracker
        self.main_sha = main_sha
        self.candidate = open_pull() if candidate is None else candidate
        self.merges: list[tuple[int, str]] = []
        self.tracker_writes: list[str] = []
        self.console_writes: list[str] = []
        self.comments: dict[int, tuple[str, str]] = {}
        self.next_id = 1000

    def read_authorization(self):
        return {
            "id": AUTH_ID,
            "body": self.auth_body,
            "issue_url": TRACKER_URL,
            "user": {"login": "Lester-Sparx"},
            "author_association": "OWNER",
            "created_at": "2026-08-28T20:41:32Z",
            "updated_at": "2026-08-28T20:41:32Z",
        }

    def read_pull(self, number: int):
        if number != 150:
            raise AssertionError("unexpected PR")
        return self.candidate

    def read_main_sha(self):
        return self.main_sha

    def list_tracker_comments(self):
        return [
            {"body": body, "issue_url": TRACKER_URL, "user": {"login": "github-actions[bot]"}}
            for body in self.tracker
        ]

    def merge_pull(self, number: int, head_sha: str):
        if number != 150:
            raise AssertionError("unexpected PR")
        self.merges.append((number, head_sha))
        self.candidate = {**self.candidate, "state": "closed", "merged": True, "draft": False, "merge_commit_sha": MERGE}
        self.main_sha = MERGE
        return {"merged": True, "sha": MERGE}

    def create_tracker_comment(self, body: str):
        self.tracker_writes.append(body)
        return self._store(body, TRACKER_URL)

    def create_console_comment(self, body: str):
        self.console_writes.append(body)
        return self._store(body, CONSOLE_URL)

    def _store(self, body: str, url: str):
        cid = self.next_id
        self.next_id += 1
        self.comments[cid] = (body, url)
        return cid

    def read_comment(self, comment_id: int):
        body, url = self.comments[comment_id]
        return {"id": comment_id, "body": body, "issue_url": url, "user": {"login": "github-actions[bot]"}}


class R03FinalizeTests(unittest.TestCase):
    def test_standing_authorization_is_exact_owner_tracker_and_immutable(self):
        validate_standing_authorization(FakePort().read_authorization())
        bads = [
            {**FakePort().read_authorization(), "id": 1},
            {**FakePort().read_authorization(), "body": AUTH_BODY.replace("SCOPE = R03 AUTOMATION TRACK ONLY", "SCOPE = ALL")},
            {**FakePort().read_authorization(), "user": {"login": "Other"}},
            {**FakePort().read_authorization(), "issue_url": CONSOLE_URL},
            {**FakePort().read_authorization(), "updated_at": "2026-08-29T00:00:00Z"},
        ]
        for bad in bads:
            with self.subTest(bad=bad):
                with self.assertRaises(FinalizeError):
                    validate_standing_authorization(bad)

    def test_upstream_failure_without_candidate_records_durable_blocked_state(self):
        fn = getattr(finalize, "finalize_execution", None)
        self.assertIsNotNone(fn, "R03_FINALIZE_EXECUTION_MISSING")
        port = FakePort()
        result = fn(
            port,
            candidate_pr_number=None,
            candidate_head_sha=None,
            expected_binding=binding(),
            policy=resolve_task("ZB_CODE_CHANGE_R03", 1),
            lester_result="failure",
            duncan_result="skipped",
            qc_pass=False,
        )
        self.assertIsNone(result)
        self.assertEqual(port.merges, [])
        self.assertIn("STATE = BLOCKED", port.tracker_writes[-1])
        self.assertIn("RESULT_CODE = UPSTREAM_NOT_PASS", port.tracker_writes[-1])
        self.assertIn("CANDIDATE_PR = NONE", port.tracker_writes[-1])
        self.assertIn("PRODUCTION_ACTIVE = NO", port.console_writes[-1])

    def test_success_requires_exact_duncan_record_and_exact_head_then_merges_once(self):
        port = FakePort()
        result = finalize_candidate(
            port,
            candidate_pr_number=150,
            candidate_head_sha=HEAD,
            expected_binding=binding(),
            policy=resolve_task("ZB_CODE_CHANGE_R03", 1),
            lester_result="success",
            duncan_result="success",
            qc_pass=True,
        )
        self.assertEqual(port.merges, [(150, HEAD)])
        self.assertEqual(result.merge_sha, MERGE)
        self.assertEqual(result.main_sha, MERGE)
        self.assertIn("ZB_R03_FINALIZE_V1", port.tracker_writes[-1])
        self.assertIn("RESULT_CODE = AUTO_MERGED_AFTER_DUNCAN", port.tracker_writes[-1])
        self.assertIn("ZB_OWNER_VIEW_R03_V1", port.console_writes[-1])
        self.assertIn("PRODUCTION_ACTIVE = NO", port.console_writes[-1])

    def test_no_merge_on_job_qc_authority_main_or_head_failure(self):
        cases = [
            dict(lester_result="failure"),
            dict(duncan_result="failure"),
            dict(qc_pass=False),
            dict(port=FakePort(tracker=[])),
            dict(port=FakePort(tracker=[qc_body(), qc_body()])),
            dict(port=FakePort(main_sha="4" * 40)),
            dict(port=FakePort(candidate=open_pull(head="5" * 40))),
            dict(port=FakePort(auth_body=AUTH_BODY.replace("AUTHORIZATION = CONTINUE", "AUTHORIZATION = STOP"))),
        ]
        for kwargs in cases:
            port = kwargs.pop("port", FakePort())
            params = dict(lester_result="success", duncan_result="success", qc_pass=True)
            params.update(kwargs)
            with self.subTest(params=params, port=port):
                with self.assertRaises(FinalizeError):
                    finalize_candidate(
                        port,
                        candidate_pr_number=150,
                        candidate_head_sha=HEAD,
                        expected_binding=binding(),
                        policy=resolve_task("ZB_CODE_CHANGE_R03", 1),
                        **params,
                    )
                self.assertEqual(port.merges, [])

    def test_merge_readback_must_prove_candidate_and_main_advanced_to_merge_sha(self):
        class BadPort(FakePort):
            def merge_pull(self, number: int, head_sha: str):
                self.merges.append((number, head_sha))
                return {"merged": True, "sha": MERGE}

        with self.assertRaisesRegex(FinalizeError, "R03_MERGE_READBACK_MISMATCH"):
            finalize_candidate(
                BadPort(),
                candidate_pr_number=150,
                candidate_head_sha=HEAD,
                expected_binding=binding(),
                policy=resolve_task("ZB_CODE_CHANGE_R03", 1),
                lester_result="success",
                duncan_result="success",
                qc_pass=True,
            )


if __name__ == "__main__":
    unittest.main()
