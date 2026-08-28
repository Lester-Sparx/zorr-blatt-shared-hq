import hashlib, pytest
from dataclasses import replace
from zb_communication_orchestrator.bindings import BindingError, Evidence, PRMeta, TaskMeta, verify_bindings
class GH:
    def __init__(self,m,evidence): self.m=m; self.evidence=evidence
    def fetch_pr_meta(self,n): return PRMeta(n,self.m.target_head_sha)
    def fetch_protected_main_sha(self): return self.m.base_sha
    def fetch_task_meta(self,n): return TaskMeta(self.m.task_id,self.m.task_revision)
    def fetch_evidence(self,ref): return self.evidence
def base(message,evidence_bytes): return GH(message,Evidence(evidence_bytes,message.target_head_sha))
def test_exact_bindings_pass(message,evidence_bytes):
    m=replace(message,evidence_sha256=hashlib.sha256(evidence_bytes).hexdigest()); verify_bindings(m,base(m,evidence_bytes))
@pytest.mark.parametrize('kind,code',[('head','TARGET_HEAD_STALE'),('base','BASE_CAS_MISMATCH'),('rev','TASK_REVISION_MISMATCH'),('missing','EVIDENCE_MISSING'),('hash','EVIDENCE_MISMATCH'),('evhead','EVIDENCE_MISMATCH')])
def test_binding_failures_are_exact(message,evidence_bytes,kind,code):
    m=replace(message,evidence_sha256=hashlib.sha256(evidence_bytes).hexdigest()); gh=base(m,evidence_bytes)
    if kind=='head': gh.fetch_pr_meta=lambda n: PRMeta(n,'f'*40)
    elif kind=='base': gh.fetch_protected_main_sha=lambda:'f'*40
    elif kind=='rev': gh.fetch_task_meta=lambda n: TaskMeta(m.task_id,99)
    elif kind=='missing': gh.fetch_evidence=lambda ref:None
    elif kind=='hash': gh.evidence=Evidence(b'bad',m.target_head_sha)
    elif kind=='evhead': gh.evidence=Evidence(evidence_bytes,'f'*40)
    with pytest.raises(BindingError) as e: verify_bindings(m,gh)
    assert e.value.code==code
