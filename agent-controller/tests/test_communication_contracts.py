import hashlib
import pytest

from zb_communication_orchestrator.contracts import (
    CommunicationProtocolError,
    AgentMessage,
    canonical_message_body,
    message_body_digest,
    parse_message,
)

VALID = '''ZB_AGENT_MESSAGE_V1
MESSAGE_ID = msg-001
EVENT_ID = evt-001
CORRELATION_ID = corr-001
CAUSATION_MESSAGE_ID = NONE
TASK_ID = ZB-COMM-001
FROM_ROLE = JINGO
TO_ROLE = LESTER
MESSAGE_KIND = ASSIGN
TARGET_REPO = Lester-Sparx/zorr-blatt-shared-hq
TARGET_ISSUE = 106
TARGET_PR = 109
BASE_SHA = 0b9b77a9d82f45e7e1821dd6c9c26861a90cf688
TARGET_HEAD_SHA = a1ad3e3a86d043544fb2900aa5f2d9faecefa7ad
TASK_REVISION = 1
EVIDENCE_REF = issue:106#comment:5448764648
EVIDENCE_SHA256 = aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
EXPECTED_GATE = LESTER_RESULT
NO_AUTO_MERGE = TRUE

Implement the approved deterministic core.
'''


def test_parse_valid_exact_message_and_direction():
    m = parse_message(VALID)
    assert m.message_id == "msg-001"
    assert m.from_role == "JINGO" and m.to_role == "LESTER"
    assert m.target_pr == 109 and m.task_revision == 1
    assert m.direction == "Implement the approved deterministic core."
    assert canonical_message_body(m) == VALID.rstrip("\n")


def test_canonical_hash_is_sha256_of_immutable_body():
    m = parse_message(VALID)
    body = canonical_message_body(m)
    assert message_body_digest(m) == hashlib.sha256(body.encode()).hexdigest()
    assert message_body_digest(parse_message(body)) == message_body_digest(m)


@pytest.mark.parametrize("old,new", [
    ("MESSAGE_ID = msg-001", "MESSAGE_ID = bad id"),
    ("EVENT_ID = evt-001", "EVENT_ID = x\ny"),
    ("TARGET_REPO = Lester-Sparx/zorr-blatt-shared-hq", "TARGET_REPO = other/repo"),
    ("BASE_SHA = 0b9b77a9d82f45e7e1821dd6c9c26861a90cf688", "BASE_SHA = ABC"),
    ("TARGET_HEAD_SHA = a1ad3e3a86d043544fb2900aa5f2d9faecefa7ad", "TARGET_HEAD_SHA = NONE"),
    ("EVIDENCE_SHA256 = " + "a"*64, "EVIDENCE_SHA256 = " + "A"*64),
    ("TASK_REVISION = 1", "TASK_REVISION = 0"),
    ("FROM_ROLE = JINGO", "FROM_ROLE = OWNER"),
    ("TO_ROLE = LESTER", "TO_ROLE = OWNER"),
    ("MESSAGE_KIND = ASSIGN", "MESSAGE_KIND = MAGIC"),
    ("EXPECTED_GATE = LESTER_RESULT", "EXPECTED_GATE = bad gate"),
    ("NO_AUTO_MERGE = TRUE", "NO_AUTO_MERGE = FALSE"),
])
def test_invalid_machine_values_fail_closed(old, new):
    with pytest.raises(CommunicationProtocolError) as exc:
        parse_message(VALID.replace(old, new))
    assert exc.value.code == "MESSAGE_PROTOCOL_INVALID"


def test_unknown_field_duplicate_and_wrong_order_fail_closed():
    variants = [
        VALID.replace("EXPECTED_GATE =", "SURPRISE = x\nEXPECTED_GATE ="),
        VALID.replace("EVENT_ID = evt-001", "EVENT_ID = evt-001\nEVENT_ID = evt-002"),
        VALID.replace("MESSAGE_ID = msg-001\nEVENT_ID = evt-001", "EVENT_ID = evt-001\nMESSAGE_ID = msg-001"),
    ]
    for body in variants:
        with pytest.raises(CommunicationProtocolError):
            parse_message(body)


def test_unsupported_marker_fails_closed():
    with pytest.raises(CommunicationProtocolError):
        parse_message(VALID.replace("ZB_AGENT_MESSAGE_V1", "ZB_AGENT_MESSAGE_V2"))


def test_none_bindings_are_canonical_when_no_target_pr():
    body = VALID.replace("TARGET_PR = 109", "TARGET_PR = NONE").replace(
        "TARGET_HEAD_SHA = a1ad3e3a86d043544fb2900aa5f2d9faecefa7ad", "TARGET_HEAD_SHA = NONE"
    ).replace("TASK_REVISION = 1", "TASK_REVISION = NONE").replace(
        "EVIDENCE_REF = issue:106#comment:5448764648", "EVIDENCE_REF = NONE"
    ).replace("EVIDENCE_SHA256 = " + "a"*64, "EVIDENCE_SHA256 = NONE")
    m = parse_message(body)
    assert m.target_pr is None and m.target_head_sha is None and m.task_revision is None


def test_formatter_rejects_multiline_human_machine_injection():
    m = parse_message(VALID)
    bad = AgentMessage(**{**m.__dict__, "expected_gate": "X\nTO_ROLE = OWNER"})
    with pytest.raises(CommunicationProtocolError):
        canonical_message_body(bad)
