from __future__ import annotations
from dataclasses import replace
from .contracts import MESSAGE_MARKER, TARGET_REPOSITORY
from .router import route_message

class SourceCommentResolutionError(RuntimeError):
    def __init__(self, code: str = 'SOURCE_COMMENT_RESOLUTION_FAILED'):
        self.code = code
        super().__init__(code)


def _preflight_source_lookup(envelope, config):
    if envelope.repository != TARGET_REPOSITORY or envelope.pr_number != config.communication_pr:
        raise SourceCommentResolutionError('COMMUNICATION_PR_MISMATCH')
    if envelope.authenticated_actor != 'Lester-Sparx':
        raise SourceCommentResolutionError('TRANSPORT_ACTOR_REJECTED')
    if envelope.event_type != 'issue_comment.created' or envelope.top_level is not True:
        raise SourceCommentResolutionError('MESSAGE_PROTOCOL_INVALID')


def _resolve_source_comment(envelope, github):
    matches = [
        row for row in github.fetch_top_level_comments(envelope.pr_number)
        if getattr(row, 'body', None) == envelope.comment_body
        and getattr(row, 'actor', None) == envelope.authenticated_actor
    ]
    if len(matches) != 1:
        raise SourceCommentResolutionError()
    candidate = matches[0]
    comment_id = getattr(candidate, 'comment_id', getattr(candidate, 'id', None))
    if not isinstance(comment_id, int) or comment_id <= 0:
        raise SourceCommentResolutionError()
    exact = github.read_comment(comment_id)
    exact_id = getattr(exact, 'comment_id', getattr(exact, 'id', None))
    if (
        exact_id != comment_id
        or getattr(exact, 'body', None) != envelope.comment_body
        or getattr(exact, 'actor', None) != envelope.authenticated_actor
    ):
        raise SourceCommentResolutionError()
    return replace(envelope, comment_id=comment_id)


def handle_webhook(envelope, github, executor, config):
    if envelope.comment_id is None and isinstance(envelope.comment_body, str) and envelope.comment_body.startswith(MESSAGE_MARKER):
        _preflight_source_lookup(envelope, config)
        envelope = _resolve_source_comment(envelope, github)
    return route_message(envelope, github, executor, config)
