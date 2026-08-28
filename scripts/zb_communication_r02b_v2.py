from __future__ import annotations

from typing import Any

from scripts import zb_communication_base as r01
from scripts import zb_communication_r02b as r02b

MARKER = "ZB_AGENT_MESSAGE_R02B_V2"


def admit_event(
    event: dict[str, Any],
    *,
    expected_base_sha: str,
    run_id: str,
    run_attempt: str,
    github_sha: str,
):
    body = ((event.get("comment") or {}).get("body"))
    if not isinstance(body, str) or not body.startswith(MARKER):
        raise r02b.ProtocolError("invalid marker")
    normalized = "ZB_AGENT_MESSAGE_R02B_V1" + body[len(MARKER):]
    event_copy = dict(event)
    comment = dict(event.get("comment") or {})
    comment["body"] = normalized
    event_copy["comment"] = comment
    return r02b.admit_event(
        event_copy,
        expected_base_sha=expected_base_sha,
        run_id=run_id,
        run_attempt=run_attempt,
        github_sha=github_sha,
    )


__all__ = ["MARKER", "admit_event"]
