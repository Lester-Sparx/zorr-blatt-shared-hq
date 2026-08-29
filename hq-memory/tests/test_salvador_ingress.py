from __future__ import annotations

from pathlib import Path
import json
import tempfile

import pytest

from zb_hq_memory import ArchiveIntegrityError, ArchiveStore, SearchIndex, build_salvador_context
from zb_hq_memory.salvador_ingress import GitHubShadowReader, ingest_salvador_events


TASK_BODY = """ZB_AGENT_TASK_V0
TASK_ID = ZB-SALVADOR-PROD-001
AGENT = SALVADOR
TASK_KIND = CANON_REFERENCE_EDIT
STATE = ASSIGNED
REFERENCE = LOCAL_INBOX

No redesign. Preserve the same subject, pose, composition, framing, silhouette, major costume forms, handheld prop, asymmetry, and shoulder/back attachment. Keep one character only. Apply the approved ZORR BLATT production drawing treatment.
"""

RUNNING_BODY = """ZB_AGENT_EVENT_V0
TASK_ID = ZB-SALVADOR-PROD-001
AGENT = SALVADOR
STATE = RUNNING
BACKEND = COMFYUI_LOCAL
EXECUTION_ID = 619cbaba-03f2-43e6-a1df-7c7291f557b4
RESULT_SHA256 = NONE
ERROR_CODE = NONE

SALVADOR_RUNNING"""

RESULT_READY_BODY = """ZB_AGENT_EVENT_V0
TASK_ID = ZB-SALVADOR-PROD-001
AGENT = SALVADOR
STATE = RESULT_READY
BACKEND = COMFYUI_LOCAL
EXECUTION_ID = 619cbaba-03f2-43e6-a1df-7c7291f557b4
RESULT_SHA256 = 69f20660a52750eeafbc97877f0c064d008e8e3fa1ed25dcd005924bed5ec6bf
ERROR_CODE = NONE

SALVADOR_RESULT_READY"""


def payload(*, actor: str = "Lester-Sparx", result_body: str = RESULT_READY_BODY) -> list[dict[str, object]]:
    return [
        {
            "number": 72,
            "title": "SALVADOR production task ZB-SALVADOR-PROD-001",
            "body": TASK_BODY,
            "comments": [
                {
                    "id": "IC_kwDOUDrwQc8AAAABQ-ntpg",
                    "body": RUNNING_BODY,
                    "createdAt": "2026-08-27T04:26:28Z",
                    "author": {"login": actor},
                },
                {
                    "id": "IC_kwDOUDrwQc8AAAABQ-okfQ",
                    "body": result_body,
                    "createdAt": "2026-08-27T04:28:40Z",
                    "author": {"login": actor},
                },
            ],
        }
    ]


class Runner:
    def __init__(self, value: list[dict[str, object]]):
        self.value = value
        self.calls: list[list[str]] = []

    def __call__(self, args: list[str], **kwargs: object):
        self.calls.append(args)
        return type("Result", (), {"returncode": 0, "stdout": json.dumps(self.value), "stderr": ""})()


def test_real_issue72_format_archives_runtime_evidence_without_qc_promotion() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        runner = Runner(payload())
        reader = GitHubShadowReader("Lester-Sparx/zorr-blatt-shared-hq", runner=runner)
        store = ArchiveStore(Path(tmp))

        summary = ingest_salvador_events(store, reader, expected_actor="Lester-Sparx")

        assert summary.issues_seen == 1
        assert summary.events_archived == 2
        records = store.iter_records()
        assert len(records) == 2
        assert {record.record_id for record in records} == {
            "salvador.github.comment.IC_kwDOUDrwQc8AAAABQ-ntpg",
            "salvador.github.comment.IC_kwDOUDrwQc8AAAABQ-okfQ",
        }
        assert any("STATE=RESULT_READY" in record.text for record in records)
        assert any("69f20660a52750eeafbc97877f0c064d008e8e3fa1ed25dcd005924bed5ec6bf" in record.text for record in records)

        # Runtime completion is evidence, not visual QC or competence promotion.
        assert build_salvador_context(store).skills == {}

        for record in records:
            assert record.source.source_location.startswith("raw:")
            digest = record.source.source_hash
            raw_path = store.raw_root / digest[:2] / f"{digest}.bin"
            assert raw_path.is_file()

        assert runner.calls[0][:3] == ["gh", "issue", "list"]
        assert "--json" in runner.calls[0]


def test_repeat_ingestion_is_idempotent() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        store = ArchiveStore(Path(tmp))
        reader = GitHubShadowReader("Lester-Sparx/zorr-blatt-shared-hq", runner=Runner(payload()))
        first = ingest_salvador_events(store, reader, expected_actor="Lester-Sparx")
        second = ingest_salvador_events(store, reader, expected_actor="Lester-Sparx")
        assert first.events_archived == 2
        assert second.events_archived == 2
        assert len(store.iter_records()) == 2


def test_same_github_comment_id_with_changed_body_fails_closed() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        store = ArchiveStore(Path(tmp))
        ingest_salvador_events(
            store,
            GitHubShadowReader("Lester-Sparx/zorr-blatt-shared-hq", runner=Runner(payload())),
            expected_actor="Lester-Sparx",
        )
        changed = RESULT_READY_BODY.replace("RESULT_READY", "FAILED", 1).replace("ERROR_CODE = NONE", "ERROR_CODE = MUTATED")
        with pytest.raises(ArchiveIntegrityError, match="RECORD_ID_COLLISION"):
            ingest_salvador_events(
                store,
                GitHubShadowReader(
                    "Lester-Sparx/zorr-blatt-shared-hq",
                    runner=Runner(payload(result_body=changed)),
                ),
                expected_actor="Lester-Sparx",
            )


def test_wrong_actor_and_unrelated_comments_do_not_enter_shadow_archive() -> None:
    mixed = payload(actor="Mallory")
    mixed[0]["comments"].append(
        {
            "id": "unrelated-1",
            "body": "SALVADOR_QC_PASS but not a controller runtime event",
            "createdAt": "2026-08-27T04:29:00Z",
            "author": {"login": "Lester-Sparx"},
        }
    )
    with tempfile.TemporaryDirectory() as tmp:
        store = ArchiveStore(Path(tmp))
        summary = ingest_salvador_events(
            store,
            GitHubShadowReader("Lester-Sparx/zorr-blatt-shared-hq", runner=Runner(mixed)),
            expected_actor="Lester-Sparx",
        )
        assert summary.events_archived == 0
        assert store.iter_records() == ()


def test_execution_failed_is_archived_as_runtime_evidence_not_visual_capability_fail() -> None:
    failed = RESULT_READY_BODY.replace("STATE = RESULT_READY", "STATE = FAILED").replace(
        "RESULT_SHA256 = 69f20660a52750eeafbc97877f0c064d008e8e3fa1ed25dcd005924bed5ec6bf",
        "RESULT_SHA256 = NONE",
    ).replace("ERROR_CODE = NONE", "ERROR_CODE = BACKEND_EXECUTION_FAILED")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        store = ArchiveStore(root / "archive")
        summary = ingest_salvador_events(
            store,
            GitHubShadowReader(
                "Lester-Sparx/zorr-blatt-shared-hq",
                runner=Runner(payload(result_body=failed)),
            ),
            expected_actor="Lester-Sparx",
        )
        assert summary.events_archived == 2
        assert build_salvador_context(store).skills == {}

        index = SearchIndex(root / "search.sqlite3")
        index.rebuild(store.iter_records())
        hits = index.search("BACKEND_EXECUTION_FAILED")
        assert hits
        assert hits[0].entity_id == "SALVADOR"
