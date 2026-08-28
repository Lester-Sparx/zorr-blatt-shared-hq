from hashlib import sha256
from types import SimpleNamespace

from zb_reference_bridge.bridge import ReferenceBridge
from zb_reference_bridge.config import BridgeConfig
from zb_reference_bridge.github_cli import BridgeIssue
from zb_reference_bridge.journal import ReferenceJournal

PNG = b"\x89PNG\r\n\x1a\nabc"
TASK_BODY = """ZB_AGENT_TASK_V0
TASK_ID = ZB-REF-001
AGENT = SALVADOR
TASK_KIND = PRODUCTION_IMAGE_EDIT
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


def terminal_event():
    return "ZB_AGENT_EVENT_V0\nTASK_ID = ZB-REF-001\nAGENT = SALVADOR\nSTATE = FAILED\nBACKEND = COMFYUI_LOCAL\nEXECUTION_ID = NONE\nRESULT_SHA256 = NONE\nERROR_CODE = NONE"


class FakeGitHub:
    def __init__(self, comments=()):
        self.comments = list(comments)
        self.posted = []
    def list_task_issues(self):
        comments = tuple(SimpleNamespace(id=f"IC{i}", body=body) for i, body in enumerate(self.comments))
        return (BridgeIssue(92, "Task", TASK_BODY, comments),)
    def post_reference_event(self, issue_number, body):
        assert issue_number == 92
        self.posted.append(body)
        self.comments.append(body)


def config(tmp_path):
    return BridgeConfig(repository="r", drive_sync_root=tmp_path/"drive", drive_drop_folder_id="id", inbox_root=tmp_path/"inbox", runtime_root=tmp_path/"runtime", quarantine_root=tmp_path/"quarantine")


def make_bridge(tmp_path, comments=()):
    cfg = config(tmp_path); gh = FakeGitHub(comments)
    return cfg, gh, ReferenceBridge(cfg, gh, ReferenceJournal(cfg.runtime_root))


def put_source(cfg):
    folder = cfg.drive_sync_root / "DELIV-001"; folder.mkdir(parents=True)
    (folder / "source.png").write_bytes(PNG)


def test_no_delivery_event_is_skipped(tmp_path):
    cfg, gh, bridge = make_bridge(tmp_path)
    summary = bridge.run_once()
    assert summary.discovered == 1 and summary.skipped == 1 and not gh.posted


def test_valid_current_legal_task_publishes_then_posts_reference_ready_only(tmp_path):
    cfg, gh, bridge = make_bridge(tmp_path, (delivery_event(),)); put_source(cfg)
    summary = bridge.run_once()
    assert summary.accepted == 1
    assert (cfg.inbox_root / "ZB-REF-001" / "source.png").read_bytes() == PNG
    body = gh.posted[-1]
    assert body.startswith("ZB_REFERENCE_EVENT_V1")
    assert "STATE = REFERENCE_READY" in body
    assert "ZB_AGENT_EVENT_V0" not in body
    assert "ZB_AGENT_MESSAGE_V1" not in body


def test_terminal_salvador_task_stops_stale_delivery(tmp_path):
    cfg, gh, bridge = make_bridge(tmp_path, (delivery_event(), terminal_event())); put_source(cfg)
    summary = bridge.run_once()
    assert summary.rejected == 1
    assert "ERROR_CODE = REFERENCE_TASK_TERMINAL" in gh.posted[-1]
    assert not (cfg.inbox_root / "ZB-REF-001").exists()


def test_bridge_never_routes_logical_roles(tmp_path):
    cfg, gh, bridge = make_bridge(tmp_path, (delivery_event(),)); put_source(cfg); bridge.run_once()
    body = "\n".join(gh.posted)
    assert "FROM_ROLE" not in body and "TO_ROLE" not in body and "logicalRole" not in body
