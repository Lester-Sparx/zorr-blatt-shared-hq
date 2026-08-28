from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile
import unittest

from scripts.zb_execution_cli import run_duncan_qc, run_lester_execution
from scripts.zb_execution_worker import WorkerOutcome
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


def request_body(base_sha: str, *, role: str, profile: str, request_id: str, scope: str) -> str:
    fields = {
        "EXECUTION_REQUEST_ID": request_id,
        "MESSAGE_ID": "message-pipeline-001",
        "EVENT_ID": "event-pipeline-001",
        "CORRELATION_ID": "corr-pipeline-001",
        "CAUSATION_MESSAGE_ID": "cause-pipeline-001",
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


class CountingWorker:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, request, *, worktree: Path, timeout_seconds: int) -> WorkerOutcome:
        self.calls += 1
        (worktree / "scripts" / "fixture.py").write_text("VALUE = 2\n", encoding="utf-8")
        return WorkerOutcome(0, '{"type":"done"}\n', "", False)


class ExecutionPipelineTests(unittest.TestCase):
    def test_lester_then_duncan_pass_with_distinct_physical_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            base = init_repo(root)
            job_root = Path(tmp) / "lester"
            worker = CountingWorker()
            lester_request = request_body(base, role="LESTER", profile="LESTER_IMPLEMENT_R01", request_id="req-pipeline-lester", scope="scripts/")
            lester = run_lester_execution(
                lester_request,
                repo_root=root,
                job_root=job_root,
                execution_id="github-actions:300:1:lester_execute",
                workflow_run_id="300",
                workflow_run_attempt=1,
                runner_provenance="github-actions:self-hosted:Windows:X64:zorr-blatt-exec-r01",
                worker=worker,
                command=SubprocessCommand(),
                verification_commands=(),
            )
            duncan = run_duncan_qc(
                request_body(base, role="DUNCAN", profile="DUNCAN_QC_R01", request_id="req-pipeline-duncan", scope="evidence/"),
                candidate_evidence_dir=job_root / "evidence",
                execution_id="github-actions:300:1:duncan_qc",
                workflow_run_id="300",
                workflow_run_attempt=1,
                runner_provenance="github-actions:self-hosted:Windows:X64:zorr-blatt-exec-r01",
            )
            self.assertEqual(lester.terminal_state, "PASS")
            self.assertEqual(duncan.terminal_state, "PASS")
            self.assertNotEqual(lester.execution_id, duncan.execution_id)
            self.assertEqual(lester.start_head, base)
            self.assertEqual(lester.end_head, base)
            self.assertEqual(lester.changed_files, ("scripts/fixture.py",))
            self.assertEqual(worker.calls, 1)

    def test_replay_same_request_reuses_verified_terminal_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            base = init_repo(root)
            job_root = Path(tmp) / "lester"
            worker = CountingWorker()
            body = request_body(base, role="LESTER", profile="LESTER_IMPLEMENT_R01", request_id="req-pipeline-replay", scope="scripts/")
            first = run_lester_execution(
                body,
                repo_root=root,
                job_root=job_root,
                execution_id="github-actions:301:1:lester_execute",
                workflow_run_id="301",
                workflow_run_attempt=1,
                runner_provenance="github-actions:self-hosted:Windows:X64:zorr-blatt-exec-r01",
                worker=worker,
                command=SubprocessCommand(),
                verification_commands=(),
            )
            second = run_lester_execution(
                body,
                repo_root=root,
                job_root=job_root,
                execution_id="github-actions:301:1:lester_execute",
                workflow_run_id="301",
                workflow_run_attempt=1,
                runner_provenance="github-actions:self-hosted:Windows:X64:zorr-blatt-exec-r01",
                worker=worker,
                command=SubprocessCommand(),
                verification_commands=(),
            )
            self.assertEqual(first, second)
            self.assertEqual(worker.calls, 1)

    def test_duncan_fails_after_candidate_tamper(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            base = init_repo(root)
            job_root = Path(tmp) / "lester"
            run_lester_execution(
                request_body(base, role="LESTER", profile="LESTER_IMPLEMENT_R01", request_id="req-pipeline-tamper", scope="scripts/"),
                repo_root=root,
                job_root=job_root,
                execution_id="github-actions:302:1:lester_execute",
                workflow_run_id="302",
                workflow_run_attempt=1,
                runner_provenance="github-actions:self-hosted:Windows:X64:zorr-blatt-exec-r01",
                worker=CountingWorker(),
                command=SubprocessCommand(),
                verification_commands=(),
            )
            (job_root / "evidence" / "patch.diff").write_bytes(b"tampered")
            duncan = run_duncan_qc(
                request_body(base, role="DUNCAN", profile="DUNCAN_QC_R01", request_id="req-pipeline-tamper-qc", scope="evidence/"),
                candidate_evidence_dir=job_root / "evidence",
                execution_id="github-actions:302:1:duncan_qc",
                workflow_run_id="302",
                workflow_run_attempt=1,
                runner_provenance="github-actions:self-hosted:Windows:X64:zorr-blatt-exec-r01",
            )
            self.assertEqual(duncan.terminal_state, "FAIL")


if __name__ == "__main__":
    unittest.main()
