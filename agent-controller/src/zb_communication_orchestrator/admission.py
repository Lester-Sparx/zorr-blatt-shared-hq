from __future__ import annotations
from dataclasses import dataclass
from .contracts import CommunicationProtocolError, TARGET_REPOSITORY, parse_message

class AdmissionError(RuntimeError):
    def __init__(self, code: str): self.code=code; super().__init__(code)

@dataclass(frozen=True)
class WebhookEnvelope:
    producer_event_id: str
    repository: str
    pr_number: int
    comment_id: int
    comment_body: str
    authenticated_actor: str
    event_type: str
    top_level: bool

def admit_event(envelope: WebhookEnvelope, canonical_pr: int):
    if envelope.repository != TARGET_REPOSITORY or envelope.pr_number != canonical_pr:
        raise AdmissionError("COMMUNICATION_PR_MISMATCH")
    if envelope.authenticated_actor != "Lester-Sparx":
        raise AdmissionError("TRANSPORT_ACTOR_REJECTED")
    if envelope.event_type != "issue_comment.created" or envelope.top_level is not True:
        raise AdmissionError("MESSAGE_PROTOCOL_INVALID")
    try:
        return parse_message(envelope.comment_body)
    except CommunicationProtocolError as exc:
        raise AdmissionError("MESSAGE_PROTOCOL_INVALID") from exc
