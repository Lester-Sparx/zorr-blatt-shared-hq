import inspect
from types import SimpleNamespace
import pytest

import zb_communication_orchestrator.handler as handler
from zb_communication_orchestrator.handler import handle_webhook
from zb_communication_orchestrator.admission import WebhookEnvelope


def test_handler_has_single_route_and_forbidden_surfaces_absent():
    src=inspect.getsource(handle_webhook).lower()
    for token in ('sleep(','subprocess','auto_merge','merge_pull','owner_lock','github polling','list_candidate'):
        assert token not in src


def test_self_generated_and_sibling_markers_are_ignored_without_execution():
    from dataclasses import replace
    from zb_communication_orchestrator.router import OrchestratorConfig
    class GH: pass
    class NeverExecute:
        def start(self,*args,**kwargs): raise AssertionError('self-generated/sibling events must never execute a logical role')
    base=WebhookEnvelope('pe','Lester-Sparx/zorr-blatt-shared-hq',777,1,'x','Lester-Sparx','issue_comment.created',True)
    for body in ('ZB_AGENT_RECEIPT_V1\nMESSAGE_ID = x','ZB_OWNER_VIEW_V0\nUPDATED_AT = 2026-08-28T00:00:00Z','ZB_AGENT_EVENT_V0\nTASK_ID = X','ZB_REFERENCE_EVENT_V1\nSTATE = REFERENCE_READY','ZB_REFERENCE_DELIVERY_V1\nTASK_ID = X','ordinary prose'):
        assert handle_webhook(replace(base,comment_body=body),GH(),NeverExecute(),OrchestratorConfig(777)) is None


def test_missing_comment_id_is_resolved_once_then_fresh_read_before_route(monkeypatch):
    body='ZB_AGENT_MESSAGE_V1\nMESSAGE_ID = unique-1'
    envelope=WebhookEnvelope('delivery-1','Lester-Sparx/zorr-blatt-shared-hq',111,None,body,'Lester-Sparx','issue_comment.created',True)
    class GH:
        def __init__(self): self.fetch_calls=0; self.read_calls=[]
        def fetch_top_level_comments(self,pr):
            self.fetch_calls+=1
            assert pr==111
            return [SimpleNamespace(id=901,body=body,actor='Lester-Sparx',top_level=True)]
        def read_comment(self,cid):
            self.read_calls.append(cid)
            return SimpleNamespace(id=cid,body=body,actor='Lester-Sparx',top_level=True)
    gh=GH(); seen={}
    def fake_route(resolved, github, executor, config):
        seen['envelope']=resolved
        return 'ROUTED'
    monkeypatch.setattr(handler,'route_message',fake_route)
    assert handle_webhook(envelope,gh,object(),SimpleNamespace(communication_pr=111))=='ROUTED'
    assert gh.fetch_calls==1
    assert gh.read_calls==[901]
    assert seen['envelope'].comment_id==901


def test_missing_comment_id_fails_closed_on_zero_or_multiple_exact_matches(monkeypatch):
    body='ZB_AGENT_MESSAGE_V1\nMESSAGE_ID = unique-2'
    envelope=WebhookEnvelope('delivery-2','Lester-Sparx/zorr-blatt-shared-hq',111,None,body,'Lester-Sparx','issue_comment.created',True)
    monkeypatch.setattr(handler,'route_message',lambda *a,**k: pytest.fail('route must not run'))
    class GH:
        def __init__(self,rows): self.rows=rows; self.fetch_calls=0; self.read_calls=[]
        def fetch_top_level_comments(self,pr): self.fetch_calls+=1; return self.rows
        def read_comment(self,cid): self.read_calls.append(cid); return None
    for rows in ([],[
        SimpleNamespace(id=1,body=body,actor='Lester-Sparx',top_level=True),
        SimpleNamespace(id=2,body=body,actor='Lester-Sparx',top_level=True),
    ]):
        gh=GH(rows)
        with pytest.raises(Exception) as exc:
            handle_webhook(envelope,gh,object(),SimpleNamespace(communication_pr=111))
        assert getattr(exc.value,'code',None)=='SOURCE_COMMENT_RESOLUTION_FAILED'
        assert gh.fetch_calls==1
        assert gh.read_calls==[]


def test_missing_comment_id_fails_closed_when_fresh_read_does_not_match(monkeypatch):
    body='ZB_AGENT_MESSAGE_V1\nMESSAGE_ID = unique-3'
    envelope=WebhookEnvelope('delivery-3','Lester-Sparx/zorr-blatt-shared-hq',111,None,body,'Lester-Sparx','issue_comment.created',True)
    monkeypatch.setattr(handler,'route_message',lambda *a,**k: pytest.fail('route must not run'))
    class GH:
        def fetch_top_level_comments(self,pr):
            return [SimpleNamespace(comment_id=903,body=body,actor='Lester-Sparx')]
        def read_comment(self,cid):
            return SimpleNamespace(comment_id=cid,body=body+' mutated',actor='Lester-Sparx')
    with pytest.raises(Exception) as exc:
        handle_webhook(envelope,GH(),object(),SimpleNamespace(communication_pr=111))
    assert getattr(exc.value,'code',None)=='SOURCE_COMMENT_RESOLUTION_FAILED'


def test_existing_comment_id_does_not_invoke_source_lookup(monkeypatch):
    body='ZB_AGENT_MESSAGE_V1\nMESSAGE_ID = already-bound'
    envelope=WebhookEnvelope('delivery-4','Lester-Sparx/zorr-blatt-shared-hq',111,904,body,'Lester-Sparx','issue_comment.created',True)
    class GH:
        def fetch_top_level_comments(self,pr): raise AssertionError('source lookup is only for missing IDs')
        def read_comment(self,cid): raise AssertionError('handler must not re-resolve already-bound IDs')
    seen={}
    monkeypatch.setattr(handler,'route_message',lambda resolved,*a,**k: seen.setdefault('id',resolved.comment_id) or 'ROUTED')
    handle_webhook(envelope,GH(),object(),SimpleNamespace(communication_pr=111))
    assert seen['id']==904


def test_missing_id_non_message_is_ignored_without_source_lookup(monkeypatch):
    envelope=WebhookEnvelope('delivery-5','Lester-Sparx/zorr-blatt-shared-hq',111,None,'ZB_AGENT_RECEIPT_V1\nMESSAGE_ID = x','Lester-Sparx','issue_comment.created',True)
    class GH:
        def fetch_top_level_comments(self,pr): raise AssertionError('non-message must not source-resolve')
    monkeypatch.setattr(handler,'route_message',lambda resolved,*a,**k: None)
    assert handle_webhook(envelope,GH(),object(),SimpleNamespace(communication_pr=111)) is None


@pytest.mark.parametrize('field,value,code',[
    ('repository','foreign/repo','COMMUNICATION_PR_MISMATCH'),
    ('pr_number',112,'COMMUNICATION_PR_MISMATCH'),
    ('authenticated_actor','Duncan-Sparx-ZB','TRANSPORT_ACTOR_REJECTED'),
    ('event_type','issue_comment.edited','MESSAGE_PROTOCOL_INVALID'),
    ('top_level',False,'MESSAGE_PROTOCOL_INVALID'),
])
def test_missing_id_message_scope_failure_happens_before_source_lookup(monkeypatch,field,value,code):
    from dataclasses import replace
    body='ZB_AGENT_MESSAGE_V1\nMESSAGE_ID = unique-scope'
    envelope=WebhookEnvelope('delivery-6','Lester-Sparx/zorr-blatt-shared-hq',111,None,body,'Lester-Sparx','issue_comment.created',True)
    envelope=replace(envelope,**{field:value})
    class GH:
        def __init__(self): self.fetch_calls=0
        def fetch_top_level_comments(self,pr): self.fetch_calls+=1; return []
    gh=GH()
    monkeypatch.setattr(handler,'route_message',lambda *a,**k: pytest.fail('invalid scope must not route'))
    with pytest.raises(Exception) as exc:
        handle_webhook(envelope,gh,object(),SimpleNamespace(communication_pr=111))
    assert getattr(exc.value,'code',None)==code
    assert gh.fetch_calls==0
