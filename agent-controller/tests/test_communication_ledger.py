import pytest
from dataclasses import replace
from zb_communication_orchestrator.contracts import AgentReceipt, canonical_message_body, canonical_receipt_body
from zb_communication_orchestrator.ledger import LedgerError, CorrelationLedger, VerifiedRecord
def rec(cid,body): return VerifiedRecord(cid,'Lester-Sparx',body)
def terminal_receipt(m): return AgentReceipt(m.message_id,m.event_id,m.correlation_id,101,'r1','RESULT','Lester-Sparx',m.to_role,m.task_id,m.target_head_sha,'exec-1','PASS',m.evidence_ref,m.evidence_sha256,1,True)
def test_duplicate_delivery_is_idempotent(message):
    l=CorrelationLedger.from_verified([rec(101,canonical_message_body(message))]); assert l.check(message).duplicate is True
def test_message_id_collision_blocks(message):
    l=CorrelationLedger.from_verified([rec(101,canonical_message_body(message))]); changed=replace(message,direction='different')
    with pytest.raises(LedgerError) as e:l.check(changed)
    assert e.value.code=='MESSAGE_ID_COLLISION'
def test_terminal_replay_blocks(message):
    l=CorrelationLedger.from_verified([rec(101,canonical_message_body(message)),rec(102,canonical_receipt_body(terminal_receipt(message)))])
    with pytest.raises(LedgerError) as e:l.check(message)
    assert e.value.code=='REPLAY_TERMINAL'
def test_causation_must_match_prior_message(message):
    l=CorrelationLedger.from_verified([rec(101,canonical_message_body(message))]); child=replace(message,message_id='msg-2',causation_message_id='wrong')
    with pytest.raises(LedgerError) as e:l.check(child)
    assert e.value.code=='CAUSATION_MISMATCH'
