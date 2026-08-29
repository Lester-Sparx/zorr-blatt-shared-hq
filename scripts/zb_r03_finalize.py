from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Protocol

from scripts import zb_communication_base as r01
from scripts.zb_r03_qc import expected_candidate_binding
from scripts.zb_r03_router import REPOSITORY, R03TaskPolicy, resolve_task


AUTH_COMMENT_ID = 5457544639
TRACKER_ISSUE_URL = r01.TRACKER_ISSUE_URL
CONSOLE_ISSUE_URL = r01.CONSOLE_ISSUE_URL
FINALIZE_MARKER = "ZB_R03_FINALIZE_V1"
OWNER_VIEW_MARKER = "ZB_OWNER_VIEW_R03_V1"
QC_MARKER = "ZB_R03_DUNCAN_QC_V1"
EXPECTED_AUTH_BODY = "\n".join(
    [
        "ZB106_R03_STANDING_OWNER_AUTH_V1",
        "",
        "OWNER_COMMAND = УТВЕРЖДАЮ R03 DESIGN B — GH-AW / САМ УТВЕРЖДАЙ ВСЕ",
        "SCOPE = R03 AUTOMATION TRACK ONLY",
        "AUTHORIZATION = CONTINUE WITHOUT REPEATED HUMAN CHECKPOINTS AFTER FRESH EVIDENCE",
        "ALLOWED = spec -> plan -> TDD -> review -> merge -> activation for R03 automation track",
        "REQUIRED_GUARDS = fresh exact-head readback; CI green; independent DUNCAN review; deny-by-default task authority; immutable evidence; no silent drift",
        "NOT_AUTHORIZED = canon mutation; OWNER LOCK mutation; merge PR #111; mutate issue #102; mutate PR #103; unrelated production changes",
        "MAIN_AT_AUTH = 1bb4ada5270b4d0fc48eba0fb152259d08b15085",
        "R03_DESIGN = thin ZB authority/QC layer + github/gh-aw",
        "UPSTREAM = github/gh-aw",
        "UPSTREAM_PIN_CANDIDATE = v0.86.2",
        "PRODUCTION_ACTIVE = NO",
    ]
)


class FinalizeError(ValueError):
    pass


@dataclass(frozen=True)
class FinalizeResult:
    merge_sha: str
    main_sha: str
    tracker_comment_id: int
    console_comment_id: int


class FinalizePort(Protocol):
    def read_authorization(self) -> dict[str, Any]: ...
    def read_pull(self, number: int) -> dict[str, Any]: ...
    def read_main_sha(self) -> str: ...
    def list_tracker_comments(self) -> list[dict[str, Any]]: ...
    def merge_pull(self, number: int, head_sha: str) -> dict[str, Any]: ...
    def create_tracker_comment(self, body: str) -> int: ...
    def create_console_comment(self, body: str) -> int: ...
    def read_comment(self, comment_id: int) -> dict[str, Any]: ...


class R03FinalizeGitHubApi:
    def __init__(self, token: str):
        self.api = r01.GitHubApi(token)

    def read_authorization(self) -> dict[str, Any]:
        return self.api.read_comment(AUTH_COMMENT_ID)

    def read_pull(self, number: int) -> dict[str, Any]:
        result = self.api._request_json(f"https://api.github.com/repos/{REPOSITORY}/pulls/{number}")
        if not isinstance(result, dict):
            raise FinalizeError("R03_CANDIDATE_PR_READ_INVALID")
        return result

    def read_main_sha(self) -> str:
        result = self.api._request_json(f"https://api.github.com/repos/{REPOSITORY}/git/ref/heads/main")
        value = ((result.get("object") or {}).get("sha")) if isinstance(result, dict) else None
        if not isinstance(value, str) or len(value) != 40:
            raise FinalizeError("R03_MAIN_READ_INVALID")
        return value

    def list_tracker_comments(self) -> list[dict[str, Any]]:
        return self.api.list_tracker_comments()

    def merge_pull(self, number: int, head_sha: str) -> dict[str, Any]:
        result = self.api._request_json(
            f"https://api.github.com/repos/{REPOSITORY}/pulls/{number}/merge",
            method="PUT",
            payload={"sha": head_sha, "merge_method": "merge"},
        )
        if not isinstance(result, dict):
            raise FinalizeError("R03_MERGE_RESPONSE_INVALID")
        return result

    def create_tracker_comment(self, body: str) -> int:
        return self.api.create_tracker_comment(body)

    def create_console_comment(self, body: str) -> int:
        return self.api.create_console_comment(body)

    def read_comment(self, comment_id: int) -> dict[str, Any]:
        return self.api.read_comment(comment_id)


def validate_standing_authorization(comment: Any) -> None:
    if not isinstance(comment, dict):
        raise FinalizeError("R03_STANDING_AUTH_INVALID")
    user = comment.get("user") or {}
    if (
        comment.get("id") != AUTH_COMMENT_ID
        or comment.get("issue_url") != TRACKER_ISSUE_URL
        or not isinstance(user, dict)
        or user.get("login") != "Lester-Sparx"
        or comment.get("author_association") != "OWNER"
        or comment.get("created_at") != comment.get("updated_at")
        or comment.get("body") != EXPECTED_AUTH_BODY
    ):
        raise FinalizeError("R03_STANDING_AUTH_INVALID")


def _parse_marker_fields(body: Any, marker: str) -> dict[str, str] | None:
    if not isinstance(body, str):
        return None
    lines = body.splitlines()
    if not lines or lines[0] != marker:
        return None
    fields: dict[str, str] = {}
    for line in lines[1:]:
        if not line or " = " not in line:
            continue
        name, value = line.split(" = ", 1)
        if not name or not value or name in fields:
            return None
        fields[name] = value
    return fields


def _expected_qc_fields(
    *,
    candidate_pr_number: int,
    candidate_head_sha: str,
    binding: dict[str, str],
) -> dict[str, str]:
    return {
        "MESSAGE_ID": binding["MESSAGE_ID"],
        "CORRELATION_ID": binding["CORRELATION_ID"],
        "TASK_ID": binding["TASK_ID"],
        "TASK_REVISION": binding["TASK_REVISION"],
        "BASE_SHA": binding["BASE_SHA"],
        "AUTHORITY_REF": binding["AUTHORITY_REF"],
        "CANDIDATE_PR": str(candidate_pr_number),
        "CANDIDATE_HEAD_SHA": candidate_head_sha,
        "STATE": "PASS",
        "RESULT_CODE": "QC_PASS",
        "PRODUCTION_ACTIVE": "NO",
    }


def _require_exact_duncan_pass(
    port: FinalizePort,
    *,
    candidate_pr_number: int,
    candidate_head_sha: str,
    binding: dict[str, str],
) -> None:
    expected = _expected_qc_fields(
        candidate_pr_number=candidate_pr_number,
        candidate_head_sha=candidate_head_sha,
        binding=binding,
    )
    matches: list[dict[str, Any]] = []
    for comment in port.list_tracker_comments():
        if not isinstance(comment, dict) or comment.get("issue_url") != TRACKER_ISSUE_URL:
            continue
        user = comment.get("user") or {}
        if not isinstance(user, dict) or user.get("login") != "github-actions[bot]":
            continue
        fields = _parse_marker_fields(comment.get("body"), QC_MARKER)
        if fields is None:
            continue
        if any(fields.get(name) != value for name, value in expected.items()):
            continue
        execution_id = fields.get("DUNCAN_EXECUTION_ID")
        if not execution_id or not execution_id.endswith(":duncan_qc"):
            continue
        matches.append(comment)
    if len(matches) != 1:
        raise FinalizeError("R03_DUNCAN_QC_RECORD_INVALID")


def _validate_candidate_for_merge(
    port: FinalizePort,
    *,
    candidate_pr_number: int,
    candidate_head_sha: str,
    binding: dict[str, str],
) -> None:
    if not isinstance(candidate_pr_number, int) or isinstance(candidate_pr_number, bool) or candidate_pr_number <= 0:
        raise FinalizeError("R03_CANDIDATE_PR_INVALID")
    pr = port.read_pull(candidate_pr_number)
    if not isinstance(pr, dict) or pr.get("number") != candidate_pr_number:
        raise FinalizeError("R03_CANDIDATE_PR_READ_INVALID")
    if pr.get("state") != "open" or pr.get("draft") is not True or pr.get("merged") is not False:
        raise FinalizeError("R03_CANDIDATE_STATE_INVALID")
    base = pr.get("base") or {}
    head = pr.get("head") or {}
    head_repo = head.get("repo") or {}
    if base.get("ref") != "main" or base.get("sha") != binding["BASE_SHA"]:
        raise FinalizeError("R03_CANDIDATE_BASE_MISMATCH")
    if head.get("sha") != candidate_head_sha:
        raise FinalizeError("R03_CANDIDATE_HEAD_MISMATCH")
    if head_repo.get("full_name") != REPOSITORY:
        raise FinalizeError("R03_CANDIDATE_REPOSITORY_MISMATCH")


def _write_and_verify(port: FinalizePort, body: str, *, console: bool = False) -> int:
    comment_id = port.create_console_comment(body) if console else port.create_tracker_comment(body)
    readback = port.read_comment(comment_id)
    expected_url = CONSOLE_ISSUE_URL if console else TRACKER_ISSUE_URL
    if (
        not isinstance(readback, dict)
        or readback.get("id") != comment_id
        or readback.get("body") != body
        or readback.get("issue_url") != expected_url
    ):
        raise FinalizeError("R03_FINALIZE_RECORD_READBACK_MISMATCH")
    return comment_id


def _render_finalize(
    *,
    binding: dict[str, str],
    candidate_pr_number: int,
    candidate_head_sha: str,
    merge_sha: str,
) -> str:
    return "\n".join(
        [
            FINALIZE_MARKER,
            f"MESSAGE_ID = {binding['MESSAGE_ID']}",
            f"CORRELATION_ID = {binding['CORRELATION_ID']}",
            f"TASK_ID = {binding['TASK_ID']}",
            f"TASK_REVISION = {binding['TASK_REVISION']}",
            f"BASE_SHA = {binding['BASE_SHA']}",
            f"AUTHORITY_REF = {binding['AUTHORITY_REF']}",
            f"CANDIDATE_PR = {candidate_pr_number}",
            f"CANDIDATE_HEAD_SHA = {candidate_head_sha}",
            f"MERGE_SHA = {merge_sha}",
            "STATE = PASS",
            "RESULT_CODE = AUTO_MERGED_AFTER_DUNCAN",
            "PRODUCTION_ACTIVE = NO",
        ]
    )


def _render_owner_view(
    *,
    binding: dict[str, str],
    candidate_pr_number: int,
    merge_sha: str,
) -> str:
    return "\n".join(
        [
            OWNER_VIEW_MARKER,
            f"MESSAGE_ID = {binding['MESSAGE_ID']}",
            f"TASK_ID = {binding['TASK_ID']}",
            f"CANDIDATE_PR = {candidate_pr_number}",
            f"MERGE_SHA = {merge_sha}",
            "LAST_STAGE = AUTO_MERGED_AFTER_DUNCAN",
            "PRODUCTION_ACTIVE = NO",
        ]
    )


def _render_blocked_finalize(
    *,
    binding: dict[str, str],
    candidate_pr_number: int | None,
    candidate_head_sha: str | None,
) -> str:
    candidate = str(candidate_pr_number) if candidate_pr_number is not None else "NONE"
    head = candidate_head_sha if candidate_head_sha else "NONE"
    return "\n".join(
        [
            FINALIZE_MARKER,
            f"MESSAGE_ID = {binding['MESSAGE_ID']}",
            f"CORRELATION_ID = {binding['CORRELATION_ID']}",
            f"TASK_ID = {binding['TASK_ID']}",
            f"TASK_REVISION = {binding['TASK_REVISION']}",
            f"BASE_SHA = {binding['BASE_SHA']}",
            f"AUTHORITY_REF = {binding['AUTHORITY_REF']}",
            f"CANDIDATE_PR = {candidate}",
            f"CANDIDATE_HEAD_SHA = {head}",
            "MERGE_SHA = NONE",
            "STATE = BLOCKED",
            "RESULT_CODE = UPSTREAM_NOT_PASS",
            "PRODUCTION_ACTIVE = NO",
        ]
    )


def _render_blocked_owner_view(
    *,
    binding: dict[str, str],
    candidate_pr_number: int | None,
) -> str:
    candidate = str(candidate_pr_number) if candidate_pr_number is not None else "NONE"
    return "\n".join(
        [
            OWNER_VIEW_MARKER,
            f"MESSAGE_ID = {binding['MESSAGE_ID']}",
            f"TASK_ID = {binding['TASK_ID']}",
            f"CANDIDATE_PR = {candidate}",
            "MERGE_SHA = NONE",
            "LAST_STAGE = UPSTREAM_NOT_PASS",
            "PRODUCTION_ACTIVE = NO",
        ]
    )


def finalize_candidate(
    port: FinalizePort,
    *,
    candidate_pr_number: int,
    candidate_head_sha: str,
    expected_binding: dict[str, str],
    policy: R03TaskPolicy,
    lester_result: str,
    duncan_result: str,
    qc_pass: bool,
) -> FinalizeResult:
    validate_standing_authorization(port.read_authorization())
    if lester_result != "success" or duncan_result != "success" or qc_pass is not True:
        raise FinalizeError("R03_UPSTREAM_RESULT_NOT_PASS")
    if policy.task_id != expected_binding.get("TASK_ID") or str(policy.revision) != expected_binding.get("TASK_REVISION"):
        raise FinalizeError("R03_POLICY_BINDING_MISMATCH")
    if policy.auto_merge_after_duncan is not True:
        raise FinalizeError("R03_AUTO_MERGE_NOT_AUTHORIZED")
    if port.read_main_sha() != expected_binding["BASE_SHA"]:
        raise FinalizeError("R03_MAIN_DRIFT")

    _validate_candidate_for_merge(
        port,
        candidate_pr_number=candidate_pr_number,
        candidate_head_sha=candidate_head_sha,
        binding=expected_binding,
    )
    _require_exact_duncan_pass(
        port,
        candidate_pr_number=candidate_pr_number,
        candidate_head_sha=candidate_head_sha,
        binding=expected_binding,
    )

    if port.read_main_sha() != expected_binding["BASE_SHA"]:
        raise FinalizeError("R03_MAIN_DRIFT")
    _validate_candidate_for_merge(
        port,
        candidate_pr_number=candidate_pr_number,
        candidate_head_sha=candidate_head_sha,
        binding=expected_binding,
    )

    merge = port.merge_pull(candidate_pr_number, candidate_head_sha)
    if not isinstance(merge, dict) or merge.get("merged") is not True:
        raise FinalizeError("R03_MERGE_FAILED")
    merge_sha = merge.get("sha")
    if not isinstance(merge_sha, str) or len(merge_sha) != 40:
        raise FinalizeError("R03_MERGE_RESPONSE_INVALID")

    merged_pr = port.read_pull(candidate_pr_number)
    main_sha = port.read_main_sha()
    if (
        not isinstance(merged_pr, dict)
        or merged_pr.get("state") != "closed"
        or merged_pr.get("merged") is not True
        or merged_pr.get("draft") is not False
        or merged_pr.get("merge_commit_sha") != merge_sha
        or main_sha != merge_sha
    ):
        raise FinalizeError("R03_MERGE_READBACK_MISMATCH")

    tracker_body = _render_finalize(
        binding=expected_binding,
        candidate_pr_number=candidate_pr_number,
        candidate_head_sha=candidate_head_sha,
        merge_sha=merge_sha,
    )
    console_body = _render_owner_view(
        binding=expected_binding,
        candidate_pr_number=candidate_pr_number,
        merge_sha=merge_sha,
    )
    tracker_id = _write_and_verify(port, tracker_body)
    console_id = _write_and_verify(port, console_body, console=True)
    return FinalizeResult(
        merge_sha=merge_sha,
        main_sha=main_sha,
        tracker_comment_id=tracker_id,
        console_comment_id=console_id,
    )


def finalize_execution(
    port: FinalizePort,
    *,
    candidate_pr_number: int | None,
    candidate_head_sha: str | None,
    expected_binding: dict[str, str],
    policy: R03TaskPolicy,
    lester_result: str,
    duncan_result: str,
    qc_pass: bool,
) -> FinalizeResult | None:
    validate_standing_authorization(port.read_authorization())
    if policy.task_id != expected_binding.get("TASK_ID") or str(policy.revision) != expected_binding.get("TASK_REVISION"):
        raise FinalizeError("R03_POLICY_BINDING_MISMATCH")

    upstream_pass = lester_result == "success" and duncan_result == "success" and qc_pass is True
    candidate_present = (
        isinstance(candidate_pr_number, int)
        and not isinstance(candidate_pr_number, bool)
        and candidate_pr_number > 0
        and isinstance(candidate_head_sha, str)
        and bool(candidate_head_sha)
    )
    if not upstream_pass or not candidate_present:
        tracker_body = _render_blocked_finalize(
            binding=expected_binding,
            candidate_pr_number=candidate_pr_number,
            candidate_head_sha=candidate_head_sha,
        )
        console_body = _render_blocked_owner_view(
            binding=expected_binding,
            candidate_pr_number=candidate_pr_number,
        )
        _write_and_verify(port, tracker_body)
        _write_and_verify(port, console_body, console=True)
        return None

    return finalize_candidate(
        port,
        candidate_pr_number=candidate_pr_number,
        candidate_head_sha=candidate_head_sha,
        expected_binding=expected_binding,
        policy=policy,
        lester_result=lester_result,
        duncan_result=duncan_result,
        qc_pass=qc_pass,
    )


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise FinalizeError(f"R03_MISSING_ENV:{name}")
    return value


def _optional_env(name: str) -> str | None:
    value = os.environ.get(name, "").strip()
    return value or None


def main() -> int:
    task_revision = int(_require_env("R03_TASK_REVISION"))
    binding = expected_candidate_binding(
        message_id=_require_env("R03_MESSAGE_ID"),
        correlation_id=_require_env("R03_CORRELATION_ID"),
        task_id=_require_env("R03_TASK_ID"),
        task_revision=task_revision,
        base_sha=_require_env("R03_BASE_SHA"),
        authority_ref=_require_env("R03_AUTHORITY_REF"),
    )
    policy = resolve_task(binding["TASK_ID"], task_revision)

    candidate_raw = _optional_env("R03_CANDIDATE_PR")
    candidate_pr_number = int(candidate_raw) if candidate_raw is not None else None
    candidate_head_sha = _optional_env("R03_CANDIDATE_HEAD")
    lester_result = _optional_env("R03_LESTER_RESULT") or "missing"
    duncan_result = _optional_env("R03_DUNCAN_RESULT") or "missing"
    qc_pass = (_optional_env("R03_QC_PASS") or "false").lower() == "true"

    result = finalize_execution(
        R03FinalizeGitHubApi(_require_env("GITHUB_TOKEN")),
        candidate_pr_number=candidate_pr_number,
        candidate_head_sha=candidate_head_sha,
        expected_binding=binding,
        policy=policy,
        lester_result=lester_result,
        duncan_result=duncan_result,
        qc_pass=qc_pass,
    )
    if result is None:
        print("R03_FINAL_STATE=BLOCKED")
        return 0
    print(f"R03_AUTO_MERGE_SHA={result.merge_sha}")
    print(f"R03_MAIN_SHA={result.main_sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
