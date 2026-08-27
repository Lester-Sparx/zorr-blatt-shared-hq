from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import pytest

from zb_reference_bridge.bridge import ReferenceBridge
from zb_reference_bridge.config import BridgeConfig
from zb_reference_bridge.github_cli import BridgeGitHubError, BridgeIssue
from zb_reference_bridge.journal import ReferenceJournal

PNG = b"\x89PNG\r\n\x1a\nabc"

TASK_BODY = """ZB_AGENT_TASK_V0
TASK_ID = ZB-REF-001
AGENT = SALVADOR
TASK_KIND = CANON_REFERENCE_EDIT
STATE = ASSIGNED
REFERENCE = LOCAL_INBOX

Preserve the supplied reference.
"""


def delivery_event(task_id="ZB-REF-001", delivery_id="DELIV-001", digest=None, size=None):
    digest = digest or sha256(PNG).hexdigest()
    size = len(PNG) if size is None else size
    return "\n".join((
        "ZB_REFERENCE_DELIVERY_V1",
        f"TASK_ID = {task_id}",
        f"DELIVERY_ID = {delivery_id}",
        "DRIVE_FOLDER_ID = folder123",
        "DRIVE_FILE_ID = file123",
        "SOURCE_FILE_NAME = source.png",
        f"SIZE_BYTES = {size}",
        f"SOURCE_SHA256 = {digest}",
        "MIME_TYPE = image/png",
        "SOURCE_STATUS = OWNER_PROVIDED_REFERENCE",
        "TRANSPORT = GOOGLE_DRIVE",
    ))


def terminal_event(state="FAILED"):
    return "\n".join((
        "ZB_AGENT_EVENT_V0",
        "TASK_ID = ZB-REF-001",
        "AGENT = SALVADOR",
        f"STATE = {state}",
        "BACKEND = COMFYUI_LOCAL",
        "EXECUTION_ID = NONE",
        "RESULT_SHA256 = NONE",
        "ERROR_CODE = NONE",
    ))


class FakeGitHub:
    def __init__(self, comments=(), fail_posts=0):
        self.comments = list(comments)
        self.posted = []
        self.fail_posts = fail_posts

    def list_task_issues(self):
        return (BridgeIssue(92, "Task", TASK_BODY, tuple(self.comments)),)

    def post_reference_event(self, issue_number, body):
        assert issue_number == 92
        if self.fail_posts:
            self.fail_posts -= 1
            raise BridgeGitHubError("BRIDGE_GH_COMMENT_FAILED")
        self.posted.append(body)
        self.comments.append(body)


def config(tmp_path):
    return BridgeConfig(
        repository="Lester-Sparx/zorr-blatt-shared-hq",
        drive_sync_root=tmp_path / "drive",
        drive_drop_folder_id="root-id",
        inbox_root=tmp_path / "inbox",
        runtime_root=tmp_path / "runtime",
        quarantine_root=tmp_path / "quarantine",
    )


def put_source(cfg, delivery_id="DELIV-001", data=PNG):
    folder = cfg.drive_sync_root / delivery_id
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "source.png"
    path.write_bytes(data)
    return path


def make_bridge(tmp_path, comments=(), fail_posts=0):
    cfg = config(tmp_path)
    gh = FakeGitHub(comments, fail_posts)
    journal = ReferenceJournal(cfg.runtime_root)
    return cfg, gh, ReferenceBridge(cfg, gh, journal)


def test_no_delivery_event_is_skipped(tmp_path):
    cfg, gh, bridge = make_bridge(tmp_path)
    summary = bridge.run_once()
    assert summary.discovered == 1
    assert summary.skipped == 1
    assert not gh.posted


def test_delivery_without_synced_folder_waits_without_comment(tmp_path):
    cfg, gh, bridge = make_bridge(tmp_path, (delivery_event(),))
    summary = bridge.run_once()
    assert summary.waiting == 1
    assert not gh.posted
    assert not cfg.inbox_root.exists()


def test_terminal_task_delivery_is_rejected(tmp_path):
    cfg, gh, bridge = make_bridge(tmp_path, (delivery_event(), terminal_event()))
    summary = bridge.run_once()
    assert summary.rejected == 1
    assert "STATE = REFERENCE_FAILED" in gh.posted[-1]
    assert "ERROR_CODE = REFERENCE_TASK_TERMINAL" in gh.posted[-1]
    assert not (cfg.inbox_root / "ZB-REF-001").exists()


def test_event_task_id_mismatch_fails_closed(tmp_path):
    cfg, gh, bridge = make_bridge(tmp_path, (delivery_event(task_id="ZB-OTHER"),))
    summary = bridge.run_once()
    assert summary.rejected == 1
    assert "TASK_ID = ZB-REF-001" in gh.posted[-1]
    assert "ERROR_CODE = REFERENCE_TASK_ID_MISMATCH" in gh.posted[-1]
    assert not cfg.inbox_root.exists()


def test_valid_delivery_publishes_then_posts_reference_ready(tmp_path):
    cfg, gh, bridge = make_bridge(tmp_path, (delivery_event(),))
    put_source(cfg)
    summary = bridge.run_once()
    assert summary.accepted == 1
    final = cfg.inbox_root / "ZB-REF-001" / "source.png"
    assert final.is_file() and final.read_bytes() == PNG
    assert "STATE = REFERENCE_READY" in gh.posted[-1]
    receipt = ReferenceJournal(cfg.runtime_root).lookup_delivery("DELIV-001")
    assert receipt and receipt.state == "ACCEPTED"


def test_hard_validation_failure_quarantines_and_posts_failed(tmp_path):
    cfg, gh, bridge = make_bridge(tmp_path, (delivery_event(digest="0" * 64),))
    put_source(cfg)
    summary = bridge.run_once()
    assert summary.rejected == 1
    assert "ERROR_CODE = REFERENCE_HASH_MISMATCH" in gh.posted[-1]
    q = cfg.quarantine_root / "DELIV-001" / "source.png"
    assert q.read_bytes() == PNG
    assert not (cfg.inbox_root / "ZB-REF-001").exists()


def test_ready_post_failure_after_publish_retries_event_without_republish(tmp_path, monkeypatch):
    cfg, gh, bridge = make_bridge(tmp_path, (delivery_event(),), fail_posts=1)
    put_source(cfg)
    with pytest.raises(BridgeGitHubError):
        bridge.run_once()
    final = cfg.inbox_root / "ZB-REF-001" / "source.png"
    assert final.read_bytes() == PNG
    receipt = ReferenceJournal(cfg.runtime_root).lookup_delivery("DELIV-001")
    assert receipt and receipt.state == "ACCEPTED"

    def forbidden_publish(*args, **kwargs):
        raise AssertionError("must retry event only")
    monkeypatch.setattr("zb_reference_bridge.bridge.publish_reference", forbidden_publish)
    summary = bridge.run_once()
    assert summary.accepted == 0
    assert "STATE = REFERENCE_READY" in gh.posted[-1]


def test_exact_replay_with_ready_event_is_idempotent_skip(tmp_path):
    cfg, gh, bridge = make_bridge(tmp_path, (delivery_event(),))
    put_source(cfg)
    bridge.run_once()
    before = len(gh.posted)
    summary = bridge.run_once()
    assert summary.skipped >= 1
    assert len(gh.posted) == before


def test_conflicting_replay_same_delivery_id_is_failed_and_quarantined(tmp_path):
    cfg, gh, bridge = make_bridge(tmp_path, (delivery_event(),))
    put_source(cfg)
    bridge.run_once()
    different = b"\x89PNG\r\n\x1a\nDIFFERENT"
    (cfg.drive_sync_root / "DELIV-001" / "source.png").write_bytes(different)
    gh.comments = [delivery_event(digest=sha256(different).hexdigest(), size=len(different))]
    summary = bridge.run_once()
    assert summary.rejected == 1
    assert "ERROR_CODE = REFERENCE_DELIVERY_ID_CONFLICT" in gh.posted[-1]
    assert (cfg.quarantine_root / "DELIV-001" / "source.png").read_bytes() == different
    assert (cfg.inbox_root / "ZB-REF-001" / "source.png").read_bytes() == PNG


def test_conflicting_replay_same_delivery_id_changed_task_id_is_failed(tmp_path):
    cfg, gh, bridge = make_bridge(tmp_path, (delivery_event(),))
    put_source(cfg)
    bridge.run_once()
    gh.comments = [delivery_event(task_id="ZB-OTHER")]
    gh.posted.clear()
    summary = bridge.run_once()
    assert summary.rejected == 1
    assert "ERROR_CODE = REFERENCE_DELIVERY_ID_CONFLICT" in gh.posted[-1]
    assert (cfg.inbox_root / "ZB-REF-001" / "source.png").read_bytes() == PNG


@pytest.mark.parametrize("old,new", [
    ("DRIVE_FOLDER_ID = folder123", "DRIVE_FOLDER_ID = folder999"),
    ("DRIVE_FILE_ID = file123", "DRIVE_FILE_ID = file999"),
    ("SOURCE_FILE_NAME = source.png", "SOURCE_FILE_NAME = alternate.png"),
    (f"SIZE_BYTES = {len(PNG)}", f"SIZE_BYTES = {len(PNG)+1}"),
    ("MIME_TYPE = image/png", "MIME_TYPE = image/jpeg"),
])
def test_conflicting_replay_same_delivery_id_changed_file_metadata_is_failed(tmp_path, old, new):
    cfg, gh, bridge = make_bridge(tmp_path, (delivery_event(),))
    put_source(cfg)
    bridge.run_once()
    gh.comments = [delivery_event().replace(old, new)]
    gh.posted.clear()
    summary = bridge.run_once()
    assert summary.rejected == 1
    assert "ERROR_CODE = REFERENCE_DELIVERY_ID_CONFLICT" in gh.posted[-1]
    assert (cfg.inbox_root / "ZB-REF-001" / "source.png").read_bytes() == PNG


def test_unsafe_delivery_id_is_ignored_before_any_receipt_or_task_event(tmp_path):
    cfg, gh, bridge = make_bridge(tmp_path, (delivery_event(task_id="ZB-OTHER", delivery_id="../escape"),))
    summary = bridge.run_once()
    assert summary.skipped == 1
    assert not gh.posted
    assert not (cfg.runtime_root / "escape.json").exists()
    assert not (cfg.runtime_root / "receipts").exists()


class FakeClock:
    def __init__(self): self.value = 1000.0
    def __call__(self): return self.value
    def advance(self, seconds): self.value += seconds


def test_missing_drive_source_times_out_after_bounded_retry(tmp_path):
    from dataclasses import replace
    cfg, gh, _ = make_bridge(tmp_path, (delivery_event(),))
    cfg = replace(cfg, cloud_retry_timeout_seconds=5.0)
    clock = FakeClock()
    bridge = ReferenceBridge(cfg, gh, ReferenceJournal(cfg.runtime_root), clock=clock)
    first = bridge.run_once()
    assert first.waiting == 1 and first.rejected == 0
    clock.advance(5.1)
    second = bridge.run_once()
    assert second.rejected == 1
    assert "ERROR_CODE = REFERENCE_DRIVE_FOLDER_TIMEOUT" in gh.posted[-1]
    assert not (cfg.inbox_root / "ZB-REF-001").exists()
