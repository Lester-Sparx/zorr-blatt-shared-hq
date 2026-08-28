from types import SimpleNamespace

import pytest

import zb_communication_orchestrator.handler as handler
from zb_communication_orchestrator.admission import WebhookEnvelope
from zb_communication_orchestrator.handler import handle_webhook


def test_missing_id_message_resolves_by_message_id_when_event_body_is_normalized(monkeypatch):
    exact_body=(
        'ZB_AGENT_MESSAGE_V1\n'
        'MESSAGE_ID = msg-normalized-1\n'
        'EVENT_ID = evt-1\n'
        'CORRELATION_ID = corr-1\n'
        'CAUSATION_MESSAGE_ID = NONE\n'
        'TASK_ID = TASK_1\n'
        'FROM_ROLE = JINGO\n'
        'TO_ROLE = LESTER\n'
        'MESSAGE_KIND = ASSIGN\n'
        'TARGET_REPO = Lester-Sparx/zorr-blatt-shared-hq\n'
        'TARGET_ISSUE = 106\n'
        'TARGET_PR = 111\n'
        'BASE_SHA = 0000000000000000000000000000000000000000\n'
        'TARGET_HEAD_SHA = 1111111111111111111111111111111111111111\n'
        'TASK_REVISION = 1\n'
        'EVIDENCE_REF = NONE\n'
        'EVIDENCE_SHA256 = NONE\n'
        'EXPECTED_GATE = LESTER\n'
        'NO_AUTO_MERGE = TRUE'
    )
    normalized='ZB_AGENT_MESSAGE_V1 / MESSAGE_ID=msg-normalized-1 / EVENT_ID=evt-1'
    envelope=WebhookEnvelope('delivery-n1','Lester-Sparx/zorr-blatt-shared-hq',111,None,normalized,'Lester-Sparx','issue_comment.created',True)
    class GH:
        def __init__(self): self.fetch_calls=0; self.read_calls=[]
        def fetch_top_level_comments(self,pr):
            self.fetch_calls += 1
            return [SimpleNamespace(id=921,body=exact_body,actor='Lester-Sparx',top_level=True)]
        def read_comment(self,cid):
            self.read_calls.append(cid)
            return SimpleNamespace(id=cid,body=exact_body,actor='Lester-Sparx',top_level=True)
    seen={}
    monkeypatch.setattr(handler,'route_message',lambda resolved,*a,**k: seen.setdefault('envelope',resolved) or 'ROUTED')
    gh=GH()
    handle_webhook(envelope,gh,object(),SimpleNamespace(communication_pr=111))
    assert gh.fetch_calls == 1
    assert gh.read_calls == [921]
    assert seen['envelope'].comment_id == 921
    assert seen['envelope'].comment_body == exact_body


def test_missing_id_probe_resolves_by_probe_instance_when_event_body_is_normalized(monkeypatch):
    exact_body=(
        'ZB_WORK_COMMENT_EVENT_PROBE_V3\n'
        'PROBE_ONLY = TRUE\n'
        'AGENT_MESSAGE = NO\n'
        'PROBE_INSTANCE = UNIQUE_PROBE_921'
    )
    normalized='ZB_WORK_COMMENT_EVENT_PROBE_V3 / PROBE_ONLY=TRUE / AGENT_MESSAGE=NO / PROBE_INSTANCE=UNIQUE_PROBE_921'
    envelope=WebhookEnvelope('delivery-p1','Lester-Sparx/zorr-blatt-shared-hq',111,None,normalized,'Lester-Sparx','issue_comment.created',True)
    class GH:
        def __init__(self): self.fetch_calls=0; self.read_calls=[]
        def fetch_top_level_comments(self,pr):
            self.fetch_calls += 1
            return [SimpleNamespace(id=922,body=exact_body,actor='Lester-Sparx',top_level=True)]
        def read_comment(self,cid):
            self.read_calls.append(cid)
            return SimpleNamespace(id=cid,body=exact_body,actor='Lester-Sparx',top_level=True)
    seen={}
    monkeypatch.setattr(handler,'route_message',lambda resolved,*a,**k: seen.setdefault('envelope',resolved))
    gh=GH()
    handle_webhook(envelope,gh,object(),SimpleNamespace(communication_pr=111))
    assert gh.fetch_calls == 1
    assert gh.read_calls == [922]
    assert seen['envelope'].comment_id == 922
    assert seen['envelope'].comment_body == exact_body


def test_missing_id_key_lookup_fails_closed_on_duplicate_unique_key(monkeypatch):
    normalized='ZB_AGENT_MESSAGE_V1 / MESSAGE_ID=collision-key'
    envelope=WebhookEnvelope('delivery-c1','Lester-Sparx/zorr-blatt-shared-hq',111,None,normalized,'Lester-Sparx','issue_comment.created',True)
    rows=[
        SimpleNamespace(id=923,body='ZB_AGENT_MESSAGE_V1\nMESSAGE_ID = collision-key',actor='Lester-Sparx'),
        SimpleNamespace(id=924,body='ZB_AGENT_MESSAGE_V1\nMESSAGE_ID = collision-key',actor='Lester-Sparx'),
    ]
    class GH:
        def fetch_top_level_comments(self,pr): return rows
        def read_comment(self,cid): pytest.fail('ambiguous key must fail before exact read')
    monkeypatch.setattr(handler,'route_message',lambda *a,**k: pytest.fail('ambiguous key must not route'))
    with pytest.raises(Exception) as exc:
        handle_webhook(envelope,GH(),object(),SimpleNamespace(communication_pr=111))
    assert getattr(exc.value,'code',None) == 'SOURCE_COMMENT_RESOLUTION_FAILED'


def test_key_lookup_fresh_read_must_equal_candidate_not_normalized_event(monkeypatch):
    candidate='ZB_AGENT_MESSAGE_V1\nMESSAGE_ID = msg-readback-1'
    normalized='ZB_AGENT_MESSAGE_V1 / MESSAGE_ID=msg-readback-1'
    envelope=WebhookEnvelope('delivery-rb1','Lester-Sparx/zorr-blatt-shared-hq',111,None,normalized,'Lester-Sparx','issue_comment.created',True)
    class GH:
        def fetch_top_level_comments(self,pr):
            return [SimpleNamespace(id=925,body=candidate,actor='Lester-Sparx')]
        def read_comment(self,cid):
            return SimpleNamespace(id=cid,body=candidate+' mutated',actor='Lester-Sparx')
    monkeypatch.setattr(handler,'route_message',lambda *a,**k: pytest.fail('read-back mismatch must not route'))
    with pytest.raises(Exception) as exc:
        handle_webhook(envelope,GH(),object(),SimpleNamespace(communication_pr=111))
    assert getattr(exc.value,'code',None) == 'SOURCE_COMMENT_RESOLUTION_FAILED'


def test_bodyless_work_event_resolves_single_new_protocol_comment_after_epoch(monkeypatch):
    exact_body=(
        'ZB_WORK_COMMENT_EVENT_PROBE_V3\n'
        'PROBE_ONLY = TRUE\n'
        'AGENT_MESSAGE = NO\n'
        'PROBE_INSTANCE = BODYLESS_WORK_EVENT_01'
    )
    envelope=WebhookEnvelope(
        'delivery-bodyless-1',
        'Lester-Sparx/zorr-blatt-shared-hq',
        111,
        None,
        None,
        'Lester-Sparx',
        'issue_comment.created',
        True,
    )
    rows=[
        SimpleNamespace(id=100,body='ordinary prose',actor='Lester-Sparx',top_level=True),
        SimpleNamespace(id=200,body=exact_body,actor='Lester-Sparx',top_level=True),
    ]
    class GH:
        def __init__(self): self.fetch_calls=0; self.read_calls=[]
        def fetch_top_level_comments(self,pr):
            self.fetch_calls += 1
            return rows
        def read_comment(self,cid):
            self.read_calls.append(cid)
            return SimpleNamespace(id=cid,body=exact_body,actor='Lester-Sparx',top_level=True)
    seen={}
    monkeypatch.setattr(handler,'route_message',lambda resolved,*a,**k: seen.setdefault('envelope',resolved))
    gh=GH()
    handle_webhook(
        envelope,
        gh,
        object(),
        SimpleNamespace(communication_pr=111, ingress_epoch_comment_id=150),
    )
    assert gh.fetch_calls == 1
    assert gh.read_calls == [200]
    assert seen['envelope'].comment_id == 200
    assert seen['envelope'].comment_body == exact_body
