import pytest
from zb_communication_orchestrator.persistence import PersistError, RemoteComment, persist_and_verify
class GH:
    def __init__(self): self.writes=[]; self.comments={}; self.next=50
    def write_comment(self,pr,body): self.writes.append((pr,body)); self.next+=1; self.comments[self.next]=RemoteComment(self.next,'Lester-Sparx',body); return self.next
    def read_comment(self,cid): return self.comments[cid]
def test_write_id_fresh_read_match_is_verified():
    gh=GH(); r=persist_and_verify(gh,777,'BODY'); assert r.comment_id==51 and r.body=='BODY' and len(gh.writes)==1
def test_mismatch_actor_or_body_fails_closed():
    for mut in ('actor','body'):
        gh=GH(); cid=gh.write_comment(777,'BODY'); gh.writes.clear(); gh.comments[cid]=RemoteComment(cid,'FOREIGN' if mut=='actor' else 'Lester-Sparx','MUTATED' if mut=='body' else 'BODY')
        with pytest.raises(PersistError) as e: persist_and_verify(gh,777,'BODY',reconcile_comment_id=cid)
        assert e.value.code=='RECEIPT_READ_BACK_MISMATCH'; assert gh.writes==[]
def test_lost_ack_with_known_id_reconciles_without_second_write():
    gh=GH(); cid=gh.write_comment(777,'BODY'); gh.writes.clear(); r=persist_and_verify(gh,777,'BODY',reconcile_comment_id=cid); assert r.comment_id==cid and gh.writes==[]
def test_write_or_read_failure_has_stable_code():
    class W(GH):
        def write_comment(self,*a): raise RuntimeError('down')
    with pytest.raises(PersistError) as e: persist_and_verify(W(),777,'BODY')
    assert e.value.code=='RECEIPT_WRITE_FAILED'
    class R(GH):
        def read_comment(self,cid): raise KeyError(cid)
    with pytest.raises(PersistError) as e: persist_and_verify(R(),777,'BODY')
    assert e.value.code=='RECEIPT_READ_BACK_MISMATCH'
