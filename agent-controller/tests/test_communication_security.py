import inspect
import pytest
from zb_communication_orchestrator import admission, handler, router
from zb_communication_orchestrator.admission import AdmissionError, WebhookEnvelope, admit_event
from zb_communication_orchestrator.errors import REQUIRED_FAILURE_CODES

def test_all_required_failure_codes_exist():
    required={'TRANSPORT_ACTOR_REJECTED','COMMUNICATION_PR_MISMATCH','MESSAGE_PROTOCOL_INVALID','MESSAGE_ID_COLLISION','REPLAY_TERMINAL','CAUSATION_MISMATCH','ROLE_TRANSITION_ILLEGAL','TARGET_HEAD_STALE','BASE_CAS_MISMATCH','TASK_REVISION_MISMATCH','EVIDENCE_MISSING','EVIDENCE_MISMATCH','OWNER_GATE_REQUIRED','RECEIPT_WRITE_FAILED','RECEIPT_READ_BACK_MISMATCH','EXECUTION_START_FAILED','EXECUTION_TIMEOUT','RETRY_EXHAUSTED','DEAD_LETTERED','OWNER_VIEW_PERSISTENCE_FAILED'}
    assert required <= REQUIRED_FAILURE_CODES

def test_legacy_role_login_comment_never_becomes_live_handoff(message):
    body='builderGitHubLogin = Lester-Sparx\nreviewerGitHubLogin = Duncan-Sparx-ZB\nlogicalRole = DUNCAN'; env=WebhookEnvelope('pe','Lester-Sparx/zorr-blatt-shared-hq',777,10,body,'Lester-Sparx','issue_comment.created',True); assert admit_event(env,777) is None

@pytest.mark.parametrize('marker',['ZB_AGENT_EVENT_V0\nTASK_ID = ZB-SALVADOR-X-1','ZB_REFERENCE_EVENT_V1\nSTATE = REFERENCE_READY','ZB_REFERENCE_DELIVERY_V1\nTASK_ID = ZB-REF-1'])
def test_sibling_protocols_are_not_communication_messages(marker):
    env=WebhookEnvelope('pe','Lester-Sparx/zorr-blatt-shared-hq',777,10,marker,'Lester-Sparx','issue_comment.created',True); assert admit_event(env,777) is None

def test_foreign_authenticated_actor_cannot_be_overridden_by_body_claim(message):
    body=router.canonical_message_body(message); env=WebhookEnvelope('pe','Lester-Sparx/zorr-blatt-shared-hq',777,10,body,'Duncan-Sparx-ZB','issue_comment.created',True)
    with pytest.raises(AdmissionError) as e: admit_event(env,777)
    assert e.value.code=='TRANSPORT_ACTOR_REJECTED'

def test_orchestrator_source_has_no_forbidden_transport_or_authority_surfaces():
    source='\n'.join(inspect.getsource(module) for module in (admission,handler,router)).lower(); forbidden=('ghp_','github_pat_','subprocess','switch account','impersonat','merge_pull','auto_merge','owner_lock','production activation','while true','time.sleep','list_candidate_issues')
    for token in forbidden: assert token not in source
