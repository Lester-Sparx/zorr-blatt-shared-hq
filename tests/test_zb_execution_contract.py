from __future__ import annotations

import unittest

from scripts.zb_execution_contract import (
    ExecutionContractError,
    execution_replay_key,
    parse_execution_request,
    parse_execution_result,
    render_execution_request,
    render_execution_result,
)


BASE_SHA = "0123456789abcdef0123456789abcdef01234567"
DESIGN_HEAD = "89abcdef0123456789abcdef0123456789abcdef"


def valid_request(**overrides: str) -> str:
    fields = {
        "EXECUTION_REQUEST_ID": "exec-request-001",
        "MESSAGE_ID": "message-001",
        "EVENT_ID": "event-001",
        "CORRELATION_ID": "corr-001",
        "CAUSATION_MESSAGE_ID": "cause-001",
        "TASK_ID": "ZB_EXECUTION_PROOF_R01",
        "TASK_REVISION": "1",
        "LOGICAL_ROLE": "LESTER",
        "EXECUTION_PROFILE": "LESTER_IMPLEMENT_R01",
        "EXECUTION_PROFILE_VERSION": "1",
        "BASE_SHA": BASE_SHA,
        "AUTHORITY_REF": "issue:106:comment:5453724500",
        "DESIGN_HEAD": DESIGN_HEAD,
        "SOURCE_REFS": "issue:106;pr:121",
        "EVIDENCE_INPUT_REFS": "spec:120;plan:121",
        "ALLOWED_WRITE_SCOPE": "scripts/;tests/",
        "TIMEOUT_SECONDS": "900",
        "NO_AUTO_MERGE": "TRUE",
        "PRODUCTION_ACTIVE": "NO",
    }
    fields.update(overrides)
    return "ZB_EXECUTION_REQUEST_V1\n" + "\n".join(f"{key} = {value}" for key, value in fields.items()) + "\n"


def valid_result(**overrides: str) -> str:
    fields = {
        "EXECUTION_REQUEST_ID": "exec-request-001",
        "EXECUTION_ID": "github-actions:33180000000:1:lester_execute",
        "ATTEMPT": "1",
        "MESSAGE_ID": "message-001",
        "CORRELATION_ID": "corr-001",
        "TASK_ID": "ZB_EXECUTION_PROOF_R01",
        "TASK_REVISION": "1",
        "LOGICAL_ROLE": "LESTER",
        "EXECUTION_PROFILE": "LESTER_IMPLEMENT_R01",
        "EXECUTION_PROFILE_VERSION": "1",
        "BASE_SHA": BASE_SHA,
        "START_HEAD": BASE_SHA,
        "END_HEAD": BASE_SHA,
        "TERMINAL_STATE": "PASS",
        "RESULT_CODE": "OK",
        "PROCESS_EXIT_CODE": "0",
        "CHANGED_FILES": "scripts/example.py;tests/test_example.py",
        "TEST_EVIDENCE_REFS": "tests.txt",
        "ARTIFACT_EVIDENCE_REFS": "manifest.json;patch.diff",
        "WORKFLOW_RUN_ID": "33180000000",
        "WORKFLOW_RUN_ATTEMPT": "1",
        "RUNNER_PROVENANCE": "github-actions:self-hosted:Windows:X64:zorr-blatt-exec-r01",
        "STARTED_AT": "2026-08-28T14:30:00Z",
        "FINISHED_AT": "2026-08-28T14:31:00Z",
        "PRODUCTION_ACTIVE": "NO",
    }
    fields.update(overrides)
    return "ZB_EXECUTION_RESULT_V1\n" + "\n".join(f"{key} = {value}" for key, value in fields.items()) + "\n"


class ExecutionRequestContractTests(unittest.TestCase):
    def test_valid_request_round_trips_and_normalizes_lists(self) -> None:
        request = parse_execution_request(valid_request())
        self.assertEqual(request.execution_request_id, "exec-request-001")
        self.assertEqual(request.task_revision, 1)
        self.assertEqual(request.execution_profile_version, 1)
        self.assertEqual(request.timeout_seconds, 900)
        self.assertEqual(request.source_refs, ("issue:106", "pr:121"))
        self.assertEqual(request.evidence_input_refs, ("spec:120", "plan:121"))
        self.assertEqual(request.allowed_write_scope, ("scripts/", "tests/"))
        self.assertTrue(request.no_auto_merge)
        self.assertFalse(request.production_active)
        self.assertEqual(parse_execution_request(render_execution_request(request)), request)

    def test_replay_key_is_deterministic_and_binds_profile_base_and_revision(self) -> None:
        request = parse_execution_request(valid_request())
        self.assertEqual(
            execution_replay_key(request),
            f"{request.execution_request_id}:{request.execution_profile_version}:{request.base_sha}:{request.task_revision}",
        )

    def test_request_rejects_duplicate_field(self) -> None:
        body = valid_request() + "TASK_ID = DUPLICATE\n"
        with self.assertRaisesRegex(ExecutionContractError, "DUPLICATE_FIELD"):
            parse_execution_request(body)

    def test_request_rejects_missing_field(self) -> None:
        body = valid_request().replace("TIMEOUT_SECONDS = 900\n", "")
        with self.assertRaisesRegex(ExecutionContractError, "MISSING_FIELD"):
            parse_execution_request(body)

    def test_request_rejects_unknown_field(self) -> None:
        body = valid_request() + "SHELL = powershell -Command whoami\n"
        with self.assertRaisesRegex(ExecutionContractError, "UNKNOWN_FIELD"):
            parse_execution_request(body)

    def test_request_rejects_wrong_marker(self) -> None:
        with self.assertRaisesRegex(ExecutionContractError, "INVALID_MARKER"):
            parse_execution_request(valid_request().replace("ZB_EXECUTION_REQUEST_V1", "OTHER", 1))

    def test_request_rejects_malformed_identifier(self) -> None:
        with self.assertRaisesRegex(ExecutionContractError, "INVALID_IDENTIFIER"):
            parse_execution_request(valid_request(MESSAGE_ID="bad value with spaces"))

    def test_request_rejects_invalid_sha(self) -> None:
        with self.assertRaisesRegex(ExecutionContractError, "INVALID_SHA"):
            parse_execution_request(valid_request(BASE_SHA="deadbeef"))

    def test_request_rejects_nonpositive_revision_profile_version_and_timeout(self) -> None:
        for field in ("TASK_REVISION", "EXECUTION_PROFILE_VERSION", "TIMEOUT_SECONDS"):
            with self.subTest(field=field), self.assertRaisesRegex(ExecutionContractError, "INVALID_POSITIVE_INT"):
                parse_execution_request(valid_request(**{field: "0"}))
        with self.assertRaisesRegex(ExecutionContractError, "INVALID_POSITIVE_INT"):
            parse_execution_request(valid_request(TIMEOUT_SECONDS="abc"))

    def test_request_requires_exact_no_auto_merge_and_production_flags(self) -> None:
        with self.assertRaisesRegex(ExecutionContractError, "NO_AUTO_MERGE_REQUIRED"):
            parse_execution_request(valid_request(NO_AUTO_MERGE="FALSE"))
        with self.assertRaisesRegex(ExecutionContractError, "PRODUCTION_ACTIVE_FORBIDDEN"):
            parse_execution_request(valid_request(PRODUCTION_ACTIVE="YES"))

    def test_request_rejects_empty_list_member(self) -> None:
        with self.assertRaisesRegex(ExecutionContractError, "INVALID_LIST"):
            parse_execution_request(valid_request(ALLOWED_WRITE_SCOPE="scripts/;;tests/"))


class ExecutionResultContractTests(unittest.TestCase):
    def test_valid_result_round_trips_and_normalizes_fields(self) -> None:
        result = parse_execution_result(valid_result())
        self.assertEqual(result.attempt, 1)
        self.assertEqual(result.process_exit_code, 0)
        self.assertEqual(result.changed_files, ("scripts/example.py", "tests/test_example.py"))
        self.assertEqual(result.test_evidence_refs, ("tests.txt",))
        self.assertEqual(result.artifact_evidence_refs, ("manifest.json", "patch.diff"))
        self.assertFalse(result.production_active)
        self.assertEqual(parse_execution_result(render_execution_result(result)), result)

    def test_result_accepts_all_recognized_terminal_states(self) -> None:
        for state in ("PASS", "FAIL", "BLOCKED", "TIMEOUT", "EXECUTION_ERROR"):
            with self.subTest(state=state):
                self.assertEqual(parse_execution_result(valid_result(TERMINAL_STATE=state)).terminal_state, state)

    def test_result_rejects_illegal_terminal_state(self) -> None:
        with self.assertRaisesRegex(ExecutionContractError, "INVALID_TERMINAL_STATE"):
            parse_execution_result(valid_result(TERMINAL_STATE="RUNNING"))

    def test_result_rejects_duplicate_missing_and_unknown_fields(self) -> None:
        with self.assertRaisesRegex(ExecutionContractError, "DUPLICATE_FIELD"):
            parse_execution_result(valid_result() + "RESULT_CODE = AGAIN\n")
        with self.assertRaisesRegex(ExecutionContractError, "MISSING_FIELD"):
            parse_execution_result(valid_result().replace("RESULT_CODE = OK\n", ""))
        with self.assertRaisesRegex(ExecutionContractError, "UNKNOWN_FIELD"):
            parse_execution_result(valid_result() + "MERGED = YES\n")

    def test_result_rejects_invalid_sha(self) -> None:
        with self.assertRaisesRegex(ExecutionContractError, "INVALID_SHA"):
            parse_execution_result(valid_result(END_HEAD="not-a-sha"))

    def test_result_rejects_nonpositive_attempt_revision_profile_and_workflow_attempt(self) -> None:
        for field in ("ATTEMPT", "TASK_REVISION", "EXECUTION_PROFILE_VERSION", "WORKFLOW_RUN_ATTEMPT"):
            with self.subTest(field=field), self.assertRaisesRegex(ExecutionContractError, "INVALID_POSITIVE_INT"):
                parse_execution_result(valid_result(**{field: "0"}))

    def test_result_requires_numeric_process_exit_code(self) -> None:
        with self.assertRaisesRegex(ExecutionContractError, "INVALID_INT"):
            parse_execution_result(valid_result(PROCESS_EXIT_CODE="not-an-int"))
        self.assertEqual(parse_execution_result(valid_result(PROCESS_EXIT_CODE="-9")).process_exit_code, -9)

    def test_result_rejects_production_active(self) -> None:
        with self.assertRaisesRegex(ExecutionContractError, "PRODUCTION_ACTIVE_FORBIDDEN"):
            parse_execution_result(valid_result(PRODUCTION_ACTIVE="YES"))


if __name__ == "__main__":
    unittest.main()
