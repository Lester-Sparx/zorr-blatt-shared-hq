from __future__ import annotations

import fnmatch
import os
import re
from typing import Any, Protocol

from scripts import zb_communication_base as r01
from scripts.zb_r03_router import REPOSITORY, R03TaskPolicy, resolve_task


CANDIDATE_MARKER = "ZB_R03_CANDIDATE_V1"
QC_MARKER = "ZB_R03_DUNCAN_QC_V1"
TRACKER_ISSUE_URL = r01.TRACKER_ISSUE_URL
_SHA40 = re.compile(r"^[0-9a-f]{40}$")
_BINDING_FIELDS = (
    "MESSAGE_ID",
    "CORRELATION_ID",
    "TASK_ID",
    "TASK_REVISION",
    "BASE_SHA",
    "AUTHORITY_REF",
)


class QcError(ValueError):
    pass


class QcPort(Protocol):
    def read_pull(self, number: int) -> dict[str, Any]: ...
    def list_pull_files(self, number: int) -> list[dict[str, Any]]: ...
    def read_main_sha(self) -> str: ...
    def create_tracker_comment(self, body: str) -> int: ...
    def read_comment(self, comment_id: int) -> dict[str, Any]: ...


class R03GitHubApi:
    def __init__(self, token: str):
        self.api = r01.GitHubApi(token)

    def read_pull(self, number: int) -> dict[str, Any]:
        if not isinstance(number, int) or isinstance(number, bool) or number <= 0:
            raise QcError("R03_CANDIDATE_PR_INVALID")
        result = self.api._request_json(f"https://api.github.com/repos/{REPOSITORY}/pulls/{number}")
        if not isinstance(result, dict):
            raise QcError("R03_CANDIDATE_PR_READ_INVALID")
        return result

    def list_pull_files(self, number: int) -> list[dict[str, Any]]:
        files: list[dict[str, Any]] = []
        for page in range(1, 21):
            result = self.api._request_json(
                f"https://api.github.com/repos/{REPOSITORY}/pulls/{number}/files?per_page=100&page={page}"
            )
            if not isinstance(result, list) or not all(isinstance(item, dict) for item in result):
                raise QcError("R03_CANDIDATE_FILES_READ_INVALID")
            files.extend(result)
            if len(result) < 100:
                return files
        raise QcError("R03_CANDIDATE_FILES_PAGINATION_EXCEEDED")

    def read_main_sha(self) -> str:
        result = self.api._request_json(f"https://api.github.com/repos/{REPOSITORY}/git/ref/heads/main")
        value = ((result.get("object") or {}).get("sha")) if isinstance(result, dict) else None
        if not isinstance(value, str) or not _SHA40.fullmatch(value):
            raise QcError("R03_MAIN_READ_INVALID")
        return value

    def create_tracker_comment(self, body: str) -> int:
        return self.api.create_tracker_comment(body)

    def read_comment(self, comment_id: int) -> dict[str, Any]:
        return self.api.read_comment(comment_id)


def expected_candidate_binding(
    *,
    message_id: str,
    correlation_id: str,
    task_id: str,
    task_revision: int,
    base_sha: str,
    authority_ref: str,
) -> dict[str, str]:
    if not isinstance(task_revision, int) or isinstance(task_revision, bool) or task_revision <= 0:
        raise QcError("R03_CANDIDATE_BINDING_INVALID")
    if not isinstance(base_sha, str) or not _SHA40.fullmatch(base_sha):
        raise QcError("R03_CANDIDATE_BINDING_INVALID")
    values = {
        "MESSAGE_ID": message_id,
        "CORRELATION_ID": correlation_id,
        "TASK_ID": task_id,
        "TASK_REVISION": str(task_revision),
        "BASE_SHA": base_sha,
        "AUTHORITY_REF": authority_ref,
    }
    if any(not isinstance(value, str) or not value for value in values.values()):
        raise QcError("R03_CANDIDATE_BINDING_INVALID")
    return values


def parse_candidate_binding(body: Any) -> dict[str, str]:
    if not isinstance(body, str):
        raise QcError("R03_CANDIDATE_BINDING_INVALID")
    lines = body.splitlines()
    if len(lines) < 7 or lines[0] != CANDIDATE_MARKER:
        raise QcError("R03_CANDIDATE_BINDING_INVALID")
    fields: dict[str, str] = {}
    for index, name in enumerate(_BINDING_FIELDS, start=1):
        line = lines[index]
        prefix = f"{name} = "
        if not line.startswith(prefix):
            raise QcError("R03_CANDIDATE_BINDING_INVALID")
        value = line[len(prefix) :]
        if not value or name in fields:
            raise QcError("R03_CANDIDATE_BINDING_INVALID")
        fields[name] = value
    if len(lines) > 7 and lines[7] != "":
        raise QcError("R03_CANDIDATE_BINDING_INVALID")
    try:
        revision = int(fields["TASK_REVISION"])
    except ValueError as exc:
        raise QcError("R03_CANDIDATE_BINDING_INVALID") from exc
    if revision <= 0 or str(revision) != fields["TASK_REVISION"] or not _SHA40.fullmatch(fields["BASE_SHA"]):
        raise QcError("R03_CANDIDATE_BINDING_INVALID")
    return fields


def _safe_repo_path(path: Any) -> bool:
    if not isinstance(path, str) or not path or path.startswith(("/", "~")) or "\\" in path or "\x00" in path:
        return False
    parts = path.split("/")
    return all(part not in ("", ".", "..") for part in parts)


def _allowed(path: str, policy: R03TaskPolicy) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in policy.allowed_files)


def _validate_files(files: Any, policy: R03TaskPolicy) -> None:
    if not isinstance(files, list) or not files or not all(isinstance(item, dict) for item in files):
        raise QcError("R03_CANDIDATE_FILES_INVALID")
    if len(files) > policy.max_changed_files:
        raise QcError("R03_CANDIDATE_FILE_COUNT_EXCEEDED")
    patch_bytes = 0
    for item in files:
        filename = item.get("filename")
        if not _safe_repo_path(filename) or not _allowed(filename, policy):
            raise QcError("R03_CANDIDATE_SCOPE_VIOLATION")
        if item.get("status") == "renamed":
            previous = item.get("previous_filename")
            if not _safe_repo_path(previous) or not _allowed(previous, policy):
                raise QcError("R03_CANDIDATE_SCOPE_VIOLATION")
        patch = item.get("patch")
        if not isinstance(patch, str):
            raise QcError("R03_CANDIDATE_PATCH_UNVERIFIABLE")
        patch_bytes += len(patch.encode("utf-8"))
        if patch_bytes > policy.max_patch_kb * 1024:
            raise QcError("R03_CANDIDATE_PATCH_EXCEEDED")


def validate_candidate(
    port: QcPort,
    candidate_pr_number: int,
    expected_binding: dict[str, str],
    policy: R03TaskPolicy,
) -> str:
    if not isinstance(candidate_pr_number, int) or isinstance(candidate_pr_number, bool) or candidate_pr_number <= 0:
        raise QcError("R03_CANDIDATE_PR_INVALID")
    pr = port.read_pull(candidate_pr_number)
    if not isinstance(pr, dict) or pr.get("number") != candidate_pr_number:
        raise QcError("R03_CANDIDATE_PR_READ_INVALID")
    if pr.get("state") != "open" or pr.get("draft") is not True or pr.get("merged") is not False:
        raise QcError("R03_CANDIDATE_STATE_INVALID")
    base = pr.get("base") or {}
    head = pr.get("head") or {}
    head_repo = head.get("repo") or {}
    expected_base = expected_binding.get("BASE_SHA")
    if base.get("ref") != "main" or base.get("sha") != expected_base:
        raise QcError("R03_CANDIDATE_BASE_MISMATCH")
    if port.read_main_sha() != expected_base:
        raise QcError("R03_MAIN_DRIFT")
    head_sha = head.get("sha")
    if not isinstance(head_sha, str) or not _SHA40.fullmatch(head_sha) or head_sha == expected_base:
        raise QcError("R03_CANDIDATE_HEAD_INVALID")
    if head_repo.get("full_name") != REPOSITORY:
        raise QcError("R03_CANDIDATE_REPOSITORY_MISMATCH")
    if parse_candidate_binding(pr.get("body")) != expected_binding:
        raise QcError("R03_CANDIDATE_BINDING_MISMATCH")
    _validate_files(port.list_pull_files(candidate_pr_number), policy)
    return head_sha


def _qc_record(
    *,
    candidate_pr_number: int,
    candidate_head_sha: str,
    binding: dict[str, str],
    execution_id: str,
) -> str:
    if not isinstance(execution_id, str) or not execution_id:
        raise QcError("R03_QC_EXECUTION_ID_INVALID")
    return "\n".join(
        [
            QC_MARKER,
            f"MESSAGE_ID = {binding['MESSAGE_ID']}",
            f"CORRELATION_ID = {binding['CORRELATION_ID']}",
            f"TASK_ID = {binding['TASK_ID']}",
            f"TASK_REVISION = {binding['TASK_REVISION']}",
            f"BASE_SHA = {binding['BASE_SHA']}",
            f"AUTHORITY_REF = {binding['AUTHORITY_REF']}",
            f"CANDIDATE_PR = {candidate_pr_number}",
            f"CANDIDATE_HEAD_SHA = {candidate_head_sha}",
            f"DUNCAN_EXECUTION_ID = {execution_id}",
            "STATE = PASS",
            "RESULT_CODE = QC_PASS",
            "PRODUCTION_ACTIVE = NO",
        ]
    )


def record_qc_pass(
    port: QcPort,
    candidate_pr_number: int,
    expected_head_sha: str,
    expected_binding: dict[str, str],
    policy: R03TaskPolicy,
    *,
    execution_id: str,
) -> str:
    actual_head = validate_candidate(port, candidate_pr_number, expected_binding, policy)
    if actual_head != expected_head_sha:
        raise QcError("R03_CANDIDATE_HEAD_MOVED")
    body = _qc_record(
        candidate_pr_number=candidate_pr_number,
        candidate_head_sha=actual_head,
        binding=expected_binding,
        execution_id=execution_id,
    )
    comment_id = port.create_tracker_comment(body)
    readback = port.read_comment(comment_id)
    if (
        not isinstance(readback, dict)
        or readback.get("id") != comment_id
        or readback.get("body") != body
        or readback.get("issue_url") != TRACKER_ISSUE_URL
    ):
        raise QcError("R03_QC_RECORD_READBACK_MISMATCH")
    return body


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise QcError(f"R03_MISSING_ENV:{name}")
    return value


def _binding_from_env() -> dict[str, str]:
    return expected_candidate_binding(
        message_id=_require_env("R03_MESSAGE_ID"),
        correlation_id=_require_env("R03_CORRELATION_ID"),
        task_id=_require_env("R03_TASK_ID"),
        task_revision=int(_require_env("R03_TASK_REVISION")),
        base_sha=_require_env("R03_BASE_SHA"),
        authority_ref=_require_env("R03_AUTHORITY_REF"),
    )


def _write_output(name: str, value: str) -> None:
    output_path = _require_env("GITHUB_OUTPUT")
    with open(output_path, "a", encoding="utf-8") as handle:
        handle.write(f"{name}={value}\n")


def main() -> int:
    phase = _require_env("R03_QC_PHASE")
    candidate_pr = int(_require_env("R03_CANDIDATE_PR"))
    binding = _binding_from_env()
    policy = resolve_task(binding["TASK_ID"], int(binding["TASK_REVISION"]))
    port = R03GitHubApi(_require_env("GITHUB_TOKEN"))
    if phase == "metadata":
        head = validate_candidate(port, candidate_pr, binding, policy)
        _write_output("candidate_head_sha", head)
        return 0
    if phase == "record":
        expected_head = _require_env("R03_EXPECTED_CANDIDATE_HEAD")
        execution_id = f"github-actions:{_require_env('GITHUB_RUN_ID')}:{_require_env('GITHUB_RUN_ATTEMPT')}:duncan_qc"
        record_qc_pass(port, candidate_pr, expected_head, binding, policy, execution_id=execution_id)
        _write_output("candidate_head_sha", expected_head)
        _write_output("qc_pass", "true")
        return 0
    raise QcError("R03_QC_PHASE_INVALID")


if __name__ == "__main__":
    raise SystemExit(main())
