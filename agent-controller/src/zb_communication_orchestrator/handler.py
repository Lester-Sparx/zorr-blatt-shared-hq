from __future__ import annotations

from dataclasses import replace
import re

from .contracts import MESSAGE_MARKER, TARGET_REPOSITORY
from .router import route_message

PROBE_MARKER = "ZB_WORK_COMMENT_EVENT_PROBE_V3"
_SAFE_LOOKUP_KEY = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


class SourceCommentResolutionError(RuntimeError):
    def __init__(self, code: str = "SOURCE_COMMENT_RESOLUTION_FAILED"):
        self.code = code
        super().__init__(code)


def _preflight_source_lookup(envelope, config):
    if envelope.repository != TARGET_REPOSITORY or envelope.pr_number != config.communication_pr:
        raise SourceCommentResolutionError("COMMUNICATION_PR_MISMATCH")
    if envelope.authenticated_actor != "Lester-Sparx":
        raise SourceCommentResolutionError("TRANSPORT_ACTOR_REJECTED")
    if envelope.event_type != "issue_comment.created" or envelope.top_level is not True:
        raise SourceCommentResolutionError("MESSAGE_PROTOCOL_INVALID")


def _extract_unique_field(body: object, field: str) -> str | None:
    if not isinstance(body, str):
        return None
    matches = re.findall(rf"(?<![A-Za-z0-9_]){re.escape(field)}\s*=\s*([A-Za-z0-9._:-]{{1,128}})(?![A-Za-z0-9._:-])", body)
    if len(matches) != 1:
        return None
    value = matches[0]
    return value if _SAFE_LOOKUP_KEY.fullmatch(value) else None


def _source_lookup_identity(body: object) -> tuple[str, str, str] | None:
    if not isinstance(body, str):
        return None
    stripped = body.lstrip()
    if stripped.startswith(MESSAGE_MARKER):
        value = _extract_unique_field(body, "MESSAGE_ID")
        if value is None:
            raise SourceCommentResolutionError()
        return MESSAGE_MARKER, "MESSAGE_ID", value
    if stripped.startswith(PROBE_MARKER):
        value = _extract_unique_field(body, "PROBE_INSTANCE")
        if value is None:
            raise SourceCommentResolutionError()
        return PROBE_MARKER, "PROBE_INSTANCE", value
    return None


def _candidate_matches(row, actor: str, marker: str, field: str, value: str) -> bool:
    body = getattr(row, "body", None)
    if not isinstance(body, str) or getattr(row, "actor", None) != actor:
        return False
    lines = body.splitlines()
    if not lines or lines[0] != marker:
        return False
    return _extract_unique_field(body, field) == value


def _resolve_source_comment(envelope, github, identity):
    marker, field, value = identity
    matches = [
        row
        for row in github.fetch_top_level_comments(envelope.pr_number)
        if _candidate_matches(row, envelope.authenticated_actor, marker, field, value)
    ]
    if len(matches) != 1:
        raise SourceCommentResolutionError()

    candidate = matches[0]
    comment_id = getattr(candidate, "comment_id", getattr(candidate, "id", None))
    candidate_body = getattr(candidate, "body", None)
    if not isinstance(comment_id, int) or comment_id <= 0 or not isinstance(candidate_body, str):
        raise SourceCommentResolutionError()

    exact = github.read_comment(comment_id)
    exact_id = getattr(exact, "comment_id", getattr(exact, "id", None))
    exact_body = getattr(exact, "body", None)
    exact_top_level = getattr(exact, "top_level", True)
    if (
        exact_id != comment_id
        or getattr(exact, "actor", None) != envelope.authenticated_actor
        or exact_top_level is not True
        or exact_body != candidate_body
        or not _candidate_matches(exact, envelope.authenticated_actor, marker, field, value)
    ):
        raise SourceCommentResolutionError()

    # The webhook body may be normalized by Work. After exact-ID read-back,
    # route only the authoritative GitHub body so strict parsing/digests stay intact.
    return replace(envelope, comment_id=comment_id, comment_body=exact_body)


def handle_webhook(envelope, github, executor, config):
    if envelope.comment_id is None:
        identity = _source_lookup_identity(envelope.comment_body)
        if identity is not None:
            _preflight_source_lookup(envelope, config)
            envelope = _resolve_source_comment(envelope, github, identity)
    return route_message(envelope, github, executor, config)
