import pytest
from zb_communication_orchestrator.admission import AdmissionError, WebhookEnvelope, admit_event

VALID='''ZB_AGENT_MESSAGE_V1
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
'''

def env(**kw):
    d=dict(producer_event_id='pe-1',repository='Lester-Sparx/zorr-blatt-shared-hq',pr_number=777,comment_id=123,comment_body=VALID,authenticated_actor='Lester-Sparx',event_type='issue_comment.created',top_level=True)
    d.update(kw); return WebhookEnvelope(**d)

def test_accepts_only_canonical_created_top_level_message():
    assert admit_event(env(),777).message_id=='msg-001'

@pytest.mark.parametrize('field,value,code',[
    ('authenticated_actor','Duncan-Sparx-ZB','TRANSPORT_ACTOR_REJECTED'),
    ('pr_number',778,'COMMUNICATION_PR_MISMATCH'),
    ('repository','other/repo','COMMUNICATION_PR_MISMATCH'),
    ('event_type','issue_comment.edited','MESSAGE_PROTOCOL_INVALID'),
    ('top_level',False,'MESSAGE_PROTOCOL_INVALID'),
])
def test_rejects_noncanonical_envelopes(field,value,code):
    with pytest.raises(AdmissionError) as e:
        admit_event(env(**{field:value}),777)
    assert e.value.code==code

def test_self_generated_sibling_and_prose_comments_are_ignored():
    for body in ('ZB_AGENT_RECEIPT_V1\nX = Y','ZB_OWNER_VIEW_V0\nX = Y','ZB_AGENT_EVENT_V0\nX = Y','ZB_REFERENCE_EVENT_V1\nX = Y','ZB_REFERENCE_DELIVERY_V1\nX = Y','hello'):
        assert admit_event(env(comment_body=body),777) is None

def test_malformed_message_marker_fails_closed():
    with pytest.raises(AdmissionError) as e:
        admit_event(env(comment_body='ZB_AGENT_MESSAGE_V1\nBROKEN = YES'),777)
    assert e.value.code=='MESSAGE_PROTOCOL_INVALID'
