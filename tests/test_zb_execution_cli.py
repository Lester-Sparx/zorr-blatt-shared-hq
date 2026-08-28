from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile
import unittest

from scripts.zb_execution_cli import run_duncan_qc, run_lester_execution, trusted_paths_from_env
from scripts.zb_execution_contract import parse_execution_request, parse_execution_result, render_execution_result
from scripts.zb_execution_worker import WorkerError, WorkerOutcome
from scripts.zb_execution_workspace import SubprocessCommand


DESIGN_HEAD = "89abcdef0123456789abcdef0123456789abcdef"


def git(*args: str, cwd: Path) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, check=True)
    return result.stdout.strip()


def init_repo(root: Path) -> str:
    git("init", cwd=root)
    git("config", "user.email", "zb-tests@example.invalid", cwd=root)
    git("config", "user.name", "ZB Tests", cwd=root)
    (root / "scripts").mkdir()
    (root / "scripts" / "fixture.py").write_text("VALUE = 1\n", encoding="utf-8")
    git("add", ".", cwd=root)
    git("commit", "-m", "base", cwd=root)
    return git("rev-parse", "HEAD", cwd=root)


def request_body(base_sha: str, *, role: str = "LESTER", profile: str = "LESTER_IMPLEMENT_R01", request_id: str = "req-lester-1", scope: str = "scripts/") -> str:
    fields = {
        "EXECUTION_REQUEST_ID": request_id,
        "MESSAGE_ID": "message-exec-001",
        "EVENT_ID": "event-exec-001",
        "CORRELATION_ID": "corr-exec-001",
        "CAUSATION_MESSAGE_ID": "cause-exec-001",
        "TASK_ID": "ZB_EXECUTION_PROOF_R01",
        "TASK_REVISION": "1",
        "LOGICAL_ROLE": role,
        "EXECUTION_PROFILE": profile,
        "EXECUTION_PROFILE_VERSION": "1",
        "BASE_SHA": base_sha,
        "AUTHORITY_REF": "issue:106:comment:5453724500",
        "DESIGN_HEAD": DESIGN_HEAD,
        "SOURCE_REFS": "issue:106;pr:122",
        "EVIDENCE_INPUT_REFS": "spec:120;plan:121",
        "ALLOWED_WRITE_SCOPE": scope,
        "TIMEOUT_SECONDS": "60",
        "NO_AUTO_MERGE": "TRUE",
        "PRODUCTION_ACTIVE": "NO",
    }
    return "ZB_EXECUTION_REQUEST_V1\n" + "\n".join(f"{k} = {v}" for k, v in fields.items()) + "\n"


class EditingWorker:
    def __init__(self, outcome: WorkerOutcome, *, edit: bool = False, raises: bool = False):
        self.outcome = outcome
        self.edit = edit
        self.raises = raises
        self.calls = 0

    def execute(self, request, *, worktree: Path, timeout_seconds: int):
        self.calls += 1
        if self.raises:
            raise WorkerError("worker did not start")
        if self.edit:
            (worktree / "scripts" / "fixture.py").write_text("VALUE = 2\n", encoding="utf-8")
        return self.outcome


class ExecutionCliTests(unittest.TestCase):
    def test_fake_worker_pass_produces_terminal_result_and_verified_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            base = init_repo(root)
            job_root = Path(tmp) / "job"
            worker = EditingWorker(WorkerOutcome(0, '{"type":"done"}\n', "", False), edit=True)
            result = run_lester_execution(
                request_body(base),
                repo_root=root,
                job_root=job_root,
                execution_id="github-actions:100:1:lester_execute",
                workflow_run_id="100",
                workflow_run_attempt=1,
                runner_provenance="github-actions:self-hosted:Windows:X64:zorr-blatt-exec-r01",
                worker=worker,
                command=SubprocessCommand(),
                verification_commands=(),
            )
            self.assertEqual(result.terminal_state, "PASS")
            self.assertEqual(result.process_exit_code, 0)
            self.assertEqual(result.changed_files, ("scripts/fixture.py",))
            self.assertEqual(result.start_head, base)
            self.assertEqual(result.end_head, base)
            self.assertEqual(parse_execution_result(render_execution_result(result)), result)
            self.assertTrue((job_root / "evidence" / "manifest.json").is_file())
            self.assertTrue((job_root / "evidence" / "result.txt").is_file())
            self.assertEqual(worker.calls, 1)

    def test_worker_nonzero_and_timeout_never_become_pass(self) -> None:
        cases = (
            (WorkerOutcome(7, "", "bad", False), "FAIL"),
            (WorkerOutcome(124, "", "timeout", True), "TIMEOUT"),
        )
        for outcome, expected in cases:
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / "repo"
                root.mkdir()
                base = init_repo(root)
                result = run_lester_execution(
                    request_body(base),
                    repo_root=root,
                    job_root=Path(tmp) / "job",
                    execution_id=f"github-actions:101:1:{expected.lower()}",
                    workflow_run_id="101",
                    workflow_run_attempt=1,
                    runner_provenance="github-actions:self-hosted:Windows:X64:zorr-blatt-exec-r01",
                    worker=EditingWorker(outcome),
                    command=SubprocessCommand(),
                    verification_commands=(),
                )
                self.assertEqual(result.terminal_state, expected)
                self.assertEqual(parse_execution_result(render_execution_result(result)), result)

    def test_worker_never_started_maps_to_execution_error_not_pass_or_running(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            base = init_repo(root)
            result = run_lester_execution(
                request_body(base),
                repo_root=root,
                job_root=Path(tmp) / "job",
                execution_id="github-actions:102:1:lester_execute",
                workflow_run_id="102",
                workflow_run_attempt=1,
                runner_provenance="github-actions:self-hosted:Windows:X64:zorr-blatt-exec-r01",
                worker=EditingWorker(WorkerOutcome(0, "", "", False), raises=True),
                command=SubprocessCommand(),
                verification_commands=(),
            )
            self.assertEqual(result.terminal_state, "EXECUTION_ERROR")
            self.assertNotEqual(result.terminal_state, "PASS")

    def test_duncan_recomputes_evidence_and_requires_distinct_execution_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            base = init_repo(root)
            job_root = Path(tmp) / "lester"
            lester = run_lester_execution(
                request_body(base),
                repo_root=root,
                job_root=job_root,
                execution_id="github-actions:200:1:lester_execute",
                workflow_run_id="200",
                workflow_run_attempt=1,
                runner_provenance="github-actions:self-hosted:Windows:X64:zorr-blatt-exec-r01",
                worker=EditingWorker(WorkerOutcome(0, "done", "", False), edit=True),
                command=SubprocessCommand(),
                verification_commands=(),
            )
            duncan_body = request_body(base, role="DUNCAN", profile="DUNCAN_QC_R01", request_id="req-duncan-1", scope="evidence/")
            qc = run_duncan_qc(
                duncan_body,
                candidate_evidence_dir=job_root / "evidence",
                execution_id="github-actions:200:1:duncan_qc",
                workflow_run_id="200",
                workflow_run_attempt=1,
                runner_provenance="github-actions:self-hosted:Windows:X64:zorr-blatt-exec-r01",
            )
            self.assertEqual(lester.terminal_state, "PASS")
            self.assertEqual(qc.terminal_state, "PASS")
            self.assertNotEqual(qc.execution_id, lester.execution_id)

            same_id = run_duncan_qc(
                duncan_body,
                candidate_evidence_dir=job_root / "evidence",
                execution_id=lester.execution_id,
                workflow_run_id="200",
                workflow_run_attempt=1,
                runner_provenance="github-actions:self-hosted:Windows:X64:zorr-blatt-exec-r01",
            )
            self.assertEqual(same_id.terminal_state, "BLOCKED")

    def test_duncan_fails_closed_on_manifest_tamper(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            base = init_repo(root)
            job_root = Path(tmp) / "lester"
            run_lester_execution(
                request_body(base),
                repo_root=root,
                job_root=job_root,
                execution_id="github-actions:201:1:lester_execute",
                workflow_run_id="201",
                workflow_run_attempt=1,
                runner_provenance="github-actions:self-hosted:Windows:X64:zorr-blatt-exec-r01",
                worker=EditingWorker(WorkerOutcome(0, "done", "", False), edit=True),
                command=SubprocessCommand(),
                verification_commands=(),
            )
            (job_root / "evidence" / "tests.txt").write_text("tampered\n", encoding="utf-8")
            qc = run_duncan_qc(
                request_body(base, role="DUNCAN", profile="DUNCAN_QC_R01", request_id="req-duncan-2", scope="evidence/"),
                candidate_evidence_dir=job_root / "evidence",
                execution_id="github-actions:201:1:duncan_qc",
                workflow_run_id="201",
                workflow_run_attempt=1,
                runner_provenance="github-actions:self-hosted:Windows:X64:zorr-blatt-exec-r01",
            )
            self.assertEqual(qc.terminal_state, "FAIL")

    def test_from_env_paths_cannot_escape_job_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            inside = root / "request.txt"
            inside.write_text("x", encoding="utf-8")
            resolved = trusted_paths_from_env({"ZB_EXECUTION_REQUEST_PATH": str(inside)}, workspace_root=root)
            self.assertEqual(resolved["ZB_EXECUTION_REQUEST_PATH"], inside)
            with self.assertRaisesRegex(ValueError, "FROM_ENV_PATH_ESCAPES_WORKSPACE"):
                trusted_paths_from_env({"ZB_EXECUTION_REQUEST_PATH": str(root.parent / "escape.txt")}, workspace_root=root)
            with self.assertRaisesRegex(ValueError, "FROM_ENV_UNKNOWN_KEY"):
                trusted_paths_from_env({"ZB_ARBITRARY_COMMAND": "whoami"}, workspace_root=root)


if __name__ == "__main__":
    unittest.main()
