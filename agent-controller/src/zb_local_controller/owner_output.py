from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


@dataclass(frozen=True)
class OutputView:
    task_id: str
    agent: str
    state: str
    created_at: datetime
    sha256: str
    path: Path
    execution_id: str | None


def _created_at(value: object) -> datetime:
    if not isinstance(value, str) or not value:
        raise ValueError("CREATED_AT_INVALID")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("CREATED_AT_INVALID")
    return parsed.astimezone(timezone.utc)


def _read_candidate(task_dir: Path) -> OutputView:
    image_path = task_dir / "result.png"
    metadata_path = task_dir / "result.json"
    if image_path.is_symlink() or metadata_path.is_symlink():
        raise ValueError("RESULT_LINK_INVALID")
    content = image_path.read_bytes()
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if not isinstance(metadata, dict):
        raise ValueError("METADATA_INVALID")
    if not content.startswith(PNG_SIGNATURE):
        raise ValueError("PNG_INVALID")
    task_id = task_dir.name
    if metadata.get("taskId") != task_id or metadata.get("state") != "RESULT_READY":
        raise ValueError("METADATA_INVALID")
    digest = hashlib.sha256(content).hexdigest()
    if metadata.get("sha256") != digest:
        raise ValueError("HASH_MISMATCH")
    agent = metadata.get("agent")
    if not isinstance(agent, str) or not agent:
        raise ValueError("AGENT_INVALID")
    execution_id = metadata.get("executionId")
    if execution_id is not None and (not isinstance(execution_id, str) or not execution_id):
        raise ValueError("EXECUTION_ID_INVALID")
    return OutputView(
        task_id=task_id,
        agent=agent,
        state="RESULT_READY",
        created_at=_created_at(metadata.get("createdAt")),
        sha256=digest,
        path=image_path,
        execution_id=execution_id,
    )


def find_latest_valid_output(result_root: Path) -> OutputView | None:
    root = Path(result_root)
    try:
        candidates = tuple(root.iterdir())
    except OSError:
        return None
    valid: list[OutputView] = []
    for task_dir in candidates:
        if task_dir.is_symlink() or not task_dir.is_dir():
            continue
        try:
            valid.append(_read_candidate(task_dir))
        except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError):
            continue
    return max(valid, key=lambda item: item.created_at, default=None)


def open_output(path: Path) -> None:
    candidate = Path(path)
    if not candidate.is_file():
        raise RuntimeError("OUTPUT_PATH_INVALID")
    if os.name != "nt" or not hasattr(os, "startfile"):
        raise RuntimeError("OUTPUT_OPEN_UNSUPPORTED")
    os.startfile(str(candidate))
