from datetime import datetime, timezone
import hashlib
import json

from zb_local_controller.owner_output import find_latest_valid_output


PNG = b"\x89PNG\r\n\x1a\nfixture"


def write_result(root, task_id, created_at, *, image=PNG, **overrides):
    task = root / task_id
    task.mkdir(parents=True)
    (task / "result.png").write_bytes(image)
    metadata = {
        "taskId": task_id,
        "agent": "SALVADOR",
        "state": "RESULT_READY",
        "executionId": f"exec-{task_id}",
        "sha256": hashlib.sha256(image).hexdigest(),
        "createdAt": created_at,
    }
    metadata.update(overrides)
    (task / "result.json").write_text(json.dumps(metadata), encoding="utf-8")
    return task


def test_latest_valid_output_uses_created_at(tmp_path):
    write_result(tmp_path, "OLDER", "2026-08-27T01:00:00Z")
    newest = write_result(tmp_path, "NEWEST", "2026-08-27T02:00:00Z")

    output = find_latest_valid_output(tmp_path)

    assert output is not None
    assert output.task_id == "NEWEST"
    assert output.agent == "SALVADOR"
    assert output.created_at == datetime(2026, 8, 27, 2, tzinfo=timezone.utc)
    assert output.path == newest / "result.png"
    assert output.execution_id == "exec-NEWEST"


def test_hash_mismatch_is_ignored(tmp_path):
    write_result(tmp_path, "TASK", "2026-08-27T01:00:00Z", sha256="0" * 64)
    assert find_latest_valid_output(tmp_path) is None


def test_wrong_task_id_is_ignored(tmp_path):
    write_result(tmp_path, "TASK", "2026-08-27T01:00:00Z", taskId="OTHER")
    assert find_latest_valid_output(tmp_path) is None


def test_non_result_ready_is_ignored(tmp_path):
    write_result(tmp_path, "TASK", "2026-08-27T01:00:00Z", state="RUNNING")
    assert find_latest_valid_output(tmp_path) is None


def test_bad_png_signature_is_ignored(tmp_path):
    write_result(tmp_path, "TASK", "2026-08-27T01:00:00Z", image=b"not-png")
    assert find_latest_valid_output(tmp_path) is None


def test_invalid_newest_falls_back_to_older_valid(tmp_path):
    write_result(tmp_path, "OLDER", "2026-08-27T01:00:00Z")
    write_result(tmp_path, "BROKEN", "2026-08-27T02:00:00Z", sha256="bad")
    assert find_latest_valid_output(tmp_path).task_id == "OLDER"


def test_symlinked_task_directory_outside_root_is_ignored(tmp_path):
    outside = tmp_path.parent / "outside-result"
    outside.mkdir(exist_ok=True)
    write_result(outside, "TASK", "2026-08-27T01:00:00Z")
    (tmp_path / "LINK").symlink_to(outside / "TASK", target_is_directory=True)

    assert find_latest_valid_output(tmp_path) is None
