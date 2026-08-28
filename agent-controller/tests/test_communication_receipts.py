import pytest
from zb_communication_orchestrator.contracts import AgentReceipt, CommunicationProtocolError, canonical_receipt_body, parse_receipt

def receipt(**overrides):
    base=dict(message_id='msg-1',event_id='evt-1',correlation_id='corr-1',source_comment_id=101,receipt_id='rcpt-1',state='RECEIVED',transport_actor='Lester-Sparx',logical_role='LESTER',task_id='ZB-COMM-1',target_head_sha=None,execution_id=None,result_code=None,evidence_ref=None,evidence_sha256=None,attempt=1,read_back_required=True)
    base.update(overrides); return AgentReceipt(**base)

def test_receipt_roundtrip_has_no_self_attested_match():
    body=canonical_receipt_body(receipt())
    assert parse_receipt(body)==receipt()
    assert 'READ_BACK_REQUIRED = TRUE' in body
    assert 'READ_BACK = MATCH' not in body and 'READ_BACK_MATCH' not in body

def test_running_requires_execution_id():
    with pytest.raises(CommunicationProtocolError): canonical_receipt_body(receipt(state='RUNNING'))

def test_terminal_requires_result_code():
    for state in ('RESULT','BLOCKED','DEAD_LETTER'):
        with pytest.raises(CommunicationProtocolError): canonical_receipt_body(receipt(state=state))

def test_dead_letter_cannot_claim_pass():
    with pytest.raises(CommunicationProtocolError): canonical_receipt_body(receipt(state='DEAD_LETTER',result_code='PASS'))

def test_attempt_must_be_positive():
    with pytest.raises(CommunicationProtocolError): canonical_receipt_body(receipt(attempt=0))
