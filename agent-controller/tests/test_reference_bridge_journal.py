from datetime import datetime, timezone
import json
import os
import pytest

from zb_reference_bridge.journal import DeliveryReceipt, JournalConflict, ReferenceJournal


def receipt(delivery_id="DELIV-001", task_id="ZB-REF-001", sha="a"*64, state="ACCEPTED", error=None):
    return DeliveryReceipt(delivery_id, task_id, sha, state, 92, "2026-08-27T00:00:00Z", error)


def test_append_and_rebuild_indexes(tmp_path):
    j=ReferenceJournal(tmp_path); r=receipt(); j.append(r)
    assert j.lookup_delivery("DELIV-001")==r
    rebuilt=ReferenceJournal(tmp_path)
    assert rebuilt.lookup_delivery("DELIV-001")==r
    assert rebuilt.lookup_task("ZB-REF-001")==r


def test_receipt_write_is_atomic_replace(tmp_path, monkeypatch):
    seen=[]; real=os.replace
    def capture(src,dst): seen.append((src,dst)); return real(src,dst)
    monkeypatch.setattr("zb_reference_bridge.journal.os.replace", capture)
    ReferenceJournal(tmp_path).append(receipt())
    assert seen and seen[0][0].suffix==".tmp" and seen[0][1].suffix==".json"


def test_same_delivery_changed_hash_is_conflict(tmp_path):
    j=ReferenceJournal(tmp_path); j.append(receipt())
    with pytest.raises(JournalConflict) as exc: j.append(receipt(sha="b"*64))
    assert exc.value.code=="REFERENCE_DELIVERY_ID_CONFLICT"


def test_same_task_changed_hash_after_acceptance_is_conflict(tmp_path):
    j=ReferenceJournal(tmp_path); j.append(receipt())
    with pytest.raises(JournalConflict) as exc: j.append(receipt(delivery_id="DELIV-002",sha="b"*64))
    assert exc.value.code=="REFERENCE_TASK_CONFLICT"


def test_same_task_same_hash_new_delivery_is_idempotent_identity(tmp_path):
    j=ReferenceJournal(tmp_path); a=receipt(); b=receipt(delivery_id="DELIV-002"); j.append(a); j.append(b)
    assert j.lookup_delivery("DELIV-002")==b
    assert j.lookup_task("ZB-REF-001").source_sha256=="a"*64


def test_existing_identical_receipt_is_not_rewritten(tmp_path, monkeypatch):
    j=ReferenceJournal(tmp_path); r=receipt(); j.append(r)
    monkeypatch.setattr("zb_reference_bridge.journal.os.replace", lambda *a: (_ for _ in ()).throw(AssertionError("rewrite")))
    assert j.append(r)==r
