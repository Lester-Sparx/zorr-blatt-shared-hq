from __future__ import annotations

import hashlib

from scripts import zb_communication_r02b as r02b
from scripts.zb_communication_base import DispatchDecision, GitHubPort, RootMessage


def prepare_r02b_dispatch_once(
    message: RootMessage,
    event: dict,
    port: GitHubPort,
) -> DispatchDecision:
    """Record a new request once; never unlock execution for a replay.

    The exact request body is the durable in-progress/terminal identity. A replay
    of the same source comment therefore remains blocked even when the workflow
    run itself is retried.
    """
    request_body = r02b._request_body(message, event)
    request_sha256 = hashlib.sha256(request_body.encode("utf-8")).hexdigest()
    for comment in port.list_tracker_comments():
        if r02b._trusted_tracker_comment(comment) and comment.get("body") == request_body:
            return DispatchDecision("REQUEST_REPLAY_BLOCKED", None, request_sha256)

    decision = r02b.prepare_substantive_dispatch(message, event, port)
    return DispatchDecision("REQUEST_NEW", decision.request_body, decision.request_sha256)
