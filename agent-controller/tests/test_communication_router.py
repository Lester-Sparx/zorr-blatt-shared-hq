import hashlib, pytest
from dataclasses import replace
from datetime import datetime, timezone
from zb_communication_orchestrator.admission import WebhookEnvelope
from zb_communication_orchestrator.bindings import Evidence, PRMeta, TaskMeta
from zb_communication_orchestrator.execution import StartResult, TerminalResult
from zb_communication_orchestrator.persistence import RemoteComment
from zb_communication_orchestrator.router import OrchestratorConfig, RouterError, route_message
from zb_communication_orchestrator.contracts import canonical_message_body

class GH:
    def __init__(self,m): self.m=m; self.comments={}; self.writes=[]; self.next=100; self.fail_owner_view=False
    def write_comment(self,pr,body): self.next+=1; self.writes.append(body); self.comments[self.next]=RemoteComment(self.next,'Lester-Sparx',body); return self.next
    def read_comment(self,cid):
        c=self.comments[cid]
        if self.fail_owner_view and c.body.startswith('ZB_OWNER_VIEW_V0'): return RemoteComment(cid,c.actor,c.body+'\nMUTATED')
        return c
    def fetch_comments(self,pr): return []
    def read_protected_file(self,path): return '{"approvedTransportActors":["Lester-Sparx"],"logicalRoles":["OWNER","LESTER","DUNCAN","DJANGO","JINGO"]}','blob'
    def fetch_pr_meta(self,n): return PRMeta(n,self.m.target_head_sha)
    def fetch_protected_main_sha(self): return self.m.base_sha
    def fetch_task_meta(self,n): return TaskMeta(self.m.task_id,self.m.task_revision)
    def fetch_evidence(self,ref): return Evidence(b'evidence',self.m.target_head_sha)
class EX:
    def __init__(self,success=True): self.started=0; self.success=success
    def start(self,role,m): self.started+=1; return StartResult(True,'work-1','exec-ref','b'*64)
    def wait(self,eid,timeout): return TerminalResult(self.success,'PASS' if self.success else 'FAIL','result-ref','c'*64)
class FlakyStart(EX):
    def __init__(self,fail_count): super().__init__(True); self.fail_count=fail_count
    def start(self,role,m):
        self.started+=1
        if self.started<=self.fail_count:return StartResult(False,None,None,None)
        return StartResult(True,'work-retry','exec-ref','b'*64)
def setup(message):
    m=replace(message,evidence_sha256=hashlib.sha256(b'evidence').hexdigest()); gh=GH(m); ex=EX(); env=WebhookEnvelope('pe','Lester-Sparx/zorr-blatt-shared-hq',777,99,canonical_message_body(m),'Lester-Sparx','issue_comment.created',True); return m,gh,ex,env

def test_happy_path_orders_receipts_execution_owner_view_and_next(message):
    m,gh,ex,env=setup(message); r=route_message(env,gh,ex,OrchestratorConfig(777,False,30,lambda:datetime(2026,8,28,5,tzinfo=timezone.utc))); markers=[b.splitlines()[0] for b in gh.writes]; assert markers[:4]==['ZB_AGENT_RECEIPT_V1','ZB_AGENT_RECEIPT_V1','ZB_AGENT_RECEIPT_V1','ZB_OWNER_VIEW_V0']; assert markers[-1]=='ZB_AGENT_MESSAGE_V1'; assert ex.started==1; assert r.next_message_id is not None

def test_no_execution_if_received_readback_fails(message):
    m,gh,ex,env=setup(message); orig=gh.read_comment
    def bad(cid):
        c=orig(cid); return RemoteComment(cid,c.actor,c.body+'x') if c.body.startswith('ZB_AGENT_RECEIPT_V1') else c
    gh.read_comment=bad
    with pytest.raises(RouterError): route_message(env,gh,ex,OrchestratorConfig(777,False,30,lambda:datetime.now(timezone.utc)))
    assert ex.started==0

def test_owner_view_persistence_failure_blocks_forward(message):
    m,gh,ex,env=setup(message); gh.fail_owner_view=True
    with pytest.raises(RouterError) as e: route_message(env,gh,ex,OrchestratorConfig(777,False,30,lambda:datetime.now(timezone.utc)))
    assert e.value.code=='OWNER_VIEW_PERSISTENCE_FAILED'; assert [b.splitlines()[0] for b in gh.writes].count('ZB_AGENT_MESSAGE_V1')==0

def test_start_retry_running_dead_letter_and_timeout_are_truthful(message):
    m,gh,_,env=setup(message); ex=FlakyStart(2); r=route_message(env,gh,ex,OrchestratorConfig(777,False,30,lambda:datetime.now(timezone.utc),max_attempts=3)); running=[b for b in gh.writes if '\nSTATE = RUNNING\n' in b]; assert ex.started==3 and len(running)==1 and '\nATTEMPT = 3\n' in running[0] and r.result_code=='PASS'
    m,gh,_,env=setup(message); ex=FlakyStart(9); r=route_message(env,gh,ex,OrchestratorConfig(777,False,30,lambda:datetime.now(timezone.utc),max_attempts=2)); assert r.result_code=='RETRY_EXHAUSTED' and r.terminal_state_code=='DEAD_LETTERED' and any(b.startswith('ZB_OWNER_VIEW_V0') and 'RETRY_EXHAUSTED' in b for b in gh.writes)
    m,gh,ex,env=setup(message); ex.wait=lambda eid,timeout: TerminalResult(False,'EXECUTION_TIMEOUT','timeout-ref','d'*64,timed_out=True); r=route_message(env,gh,ex,OrchestratorConfig(777,False,30,lambda:datetime.now(timezone.utc))); assert r.result_code=='EXECUTION_TIMEOUT' and ex.started==1 and any(b.startswith('ZB_OWNER_VIEW_V0') and 'EXECUTION_TIMEOUT' in b for b in gh.writes)

def test_transient_write_retry_does_not_double_start_and_negative_verdict_not_upgraded(message):
    m,gh,ex,env=setup(message); original=gh.write_comment; calls={'n':0}
    def flaky(pr,body):
        calls['n']+=1
        if calls['n']==1: raise RuntimeError('transient before remote id')
        return original(pr,body)
    gh.write_comment=flaky; r=route_message(env,gh,ex,OrchestratorConfig(777,False,30,lambda:datetime.now(timezone.utc),max_attempts=3)); assert r.result_code=='PASS' and ex.started==1 and calls['n']>=2
    m,gh,ex,env=setup(message); waits={'n':0}
    def negative(eid,timeout): waits['n']+=1; return TerminalResult(False,'FAIL','negative-ref','e'*64)
    ex.wait=negative; r=route_message(env,gh,ex,OrchestratorConfig(777,False,30,lambda:datetime.now(timezone.utc),max_attempts=3)); assert r.result_code=='FAIL' and ex.started==1 and waits['n']==1 and r.next_message_id is None

def test_role_order_cannot_be_bypassed_by_unrelated_history_or_child(message):
    from zb_communication_orchestrator.ledger import VerifiedRecord
    m,gh,ex,env=setup(message); unrelated=replace(m,message_id='other-root',correlation_id='other-corr'); gh.fetch_comments=lambda pr:[VerifiedRecord(500,'Lester-Sparx',canonical_message_body(unrelated))]; forged=replace(m,from_role='JINGO',to_role='DJANGO',message_kind='ARCH_REVIEW',expected_gate='DJANGO_ARCH'); env=replace(env,comment_body=canonical_message_body(forged))
    with pytest.raises(RouterError) as e: route_message(env,gh,ex,OrchestratorConfig(777,True,30,lambda:datetime.now(timezone.utc)))
    assert e.value.code=='ROLE_TRANSITION_ILLEGAL' and ex.started==0
    m,gh,ex,env=setup(message); gh.fetch_comments=lambda pr:[VerifiedRecord(500,'Lester-Sparx',canonical_message_body(m))]; child=replace(m,message_id='msg-002',causation_message_id=m.message_id,from_role='LESTER',to_role='JINGO',message_kind='RETURN',expected_gate='JINGO_RETURN'); env=replace(env,comment_id=501,comment_body=canonical_message_body(child)); gh.m=child
    with pytest.raises(RouterError) as e: route_message(env,gh,ex,OrchestratorConfig(777,False,30,lambda:datetime.now(timezone.utc)))
    assert e.value.code=='ROLE_TRANSITION_ILLEGAL' and ex.started==0
