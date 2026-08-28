from hashlib import sha256
from pathlib import Path
import pytest

from zb_reference_bridge.config import BridgeConfig
from zb_reference_bridge.contracts import ReferenceDelivery
from zb_reference_bridge.local_delivery import ValidatedSource
from zb_reference_bridge.publisher import PublishError, publish_reference, quarantine_delivery

PNG=b"\x89PNG\r\n\x1a\nabc"

def cfg(tmp_path): return BridgeConfig(repository="r",drive_sync_root=tmp_path/"drive",drive_drop_folder_id="id",inbox_root=tmp_path/"inbox",runtime_root=tmp_path/"runtime",quarantine_root=tmp_path/"quarantine")
def delivery(sha=None,delivery_id="DELIV-001"): return ReferenceDelivery("ZB-REF-001",delivery_id,"folder","file","source.png",len(PNG),sha or sha256(PNG).hexdigest(),"image/png","OWNER_PROVIDED_REFERENCE","GOOGLE_DRIVE")
def source(tmp_path,data=PNG):
    p=tmp_path/"source.png"; p.write_bytes(data); return ValidatedSource(p,len(data),sha256(data).hexdigest(),".png","image/png")

def test_final_folder_absent_is_atomically_published(tmp_path):
    c=cfg(tmp_path); d=delivery(); r=publish_reference(c,d,source(tmp_path)); assert r.state=="PUBLISHED"; assert r.final_path==c.inbox_root/d.task_id/"source.png"; assert r.final_path.read_bytes()==PNG

def test_exact_existing_reference_is_already_present(tmp_path):
    c=cfg(tmp_path); d=delivery(); final=c.inbox_root/d.task_id; final.mkdir(parents=True); (final/"source.png").write_bytes(PNG); r=publish_reference(c,d,source(tmp_path)); assert r.state=="ALREADY_PRESENT"

def test_existing_conflicting_task_reference_is_never_overwritten(tmp_path):
    c=cfg(tmp_path); d=delivery(); final=c.inbox_root/d.task_id; final.mkdir(parents=True); p=final/"source.png"; p.write_bytes(b"different")
    with pytest.raises(PublishError) as exc: publish_reference(c,d,source(tmp_path))
    assert exc.value.code=="REFERENCE_DESTINATION_CONFLICT"; assert p.read_bytes()==b"different"

def test_unexpected_extra_final_file_is_conflict(tmp_path):
    c=cfg(tmp_path); d=delivery(); final=c.inbox_root/d.task_id; final.mkdir(parents=True); (final/"source.png").write_bytes(PNG); (final/"extra.txt").write_text("x")
    with pytest.raises(PublishError) as exc: publish_reference(c,d,source(tmp_path))
    assert exc.value.code=="REFERENCE_DESTINATION_CONFLICT"

def test_staged_rehash_mismatch_fails(tmp_path, monkeypatch):
    c=cfg(tmp_path); d=delivery(); s=source(tmp_path)
    def corrupt(src,dst): Path(dst).write_bytes(b"corrupt"); return str(dst)
    monkeypatch.setattr("zb_reference_bridge.publisher.shutil.copyfile",corrupt)
    with pytest.raises(PublishError) as exc: publish_reference(c,d,s)
    assert exc.value.code=="REFERENCE_STAGING_HASH_MISMATCH"; assert not (c.inbox_root/d.task_id).exists()

def test_quarantine_preserves_source_bytes(tmp_path):
    c=cfg(tmp_path); d=delivery(); s=source(tmp_path); q=quarantine_delivery(c,d,s.path,"REFERENCE_HASH_MISMATCH"); assert q.read_bytes()==PNG; assert d.delivery_id in str(q)
