from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

_TASK_ID_RE = re.compile(r"^[A-Z0-9_-]+$")
_SUPPORTED = {".png", ".jpg", ".jpeg", ".webp"}
_MAX_BYTES = 20 * 1024 * 1024


class PathBoundaryError(ValueError):
    pass


class ReferenceValidationError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class ReferenceImage:
    path: Path
    size: int


def _validate_task_id(task_id: str) -> None:
    if not isinstance(task_id, str) or not _TASK_ID_RE.fullmatch(task_id):
        raise PathBoundaryError("TASK_ID_PATH_INVALID")


def _magic_ok(path: Path, head: bytes) -> bool:
    ext = path.suffix.lower()
    if ext == ".png":
        return head.startswith(b"\x89PNG\r\n\x1a\n")
    if ext in {".jpg", ".jpeg"}:
        return head.startswith(b"\xff\xd8\xff")
    if ext == ".webp":
        return len(head) >= 12 and head[:4] == b"RIFF" and head[8:12] == b"WEBP"
    return False


def resolve_reference(inbox_root: Path, task_id: str) -> ReferenceImage | None:
    _validate_task_id(task_id)
    task_dir = Path(inbox_root) / task_id
    if not task_dir.exists():
        return None
    if not task_dir.is_dir():
        raise PathBoundaryError("TASK_DIRECTORY_INVALID")

    files = [p for p in task_dir.iterdir() if p.is_file()]
    supported = [p for p in files if p.suffix.lower() in _SUPPORTED]
    if not supported:
        if files:
            raise ReferenceValidationError("REFERENCE_EXTENSION_INVALID")
        return None
    if len(supported) != 1:
        raise ReferenceValidationError("REFERENCE_COUNT_INVALID")

    path = supported[0]
    size = path.stat().st_size
    if size == 0:
        raise ReferenceValidationError("REFERENCE_EMPTY")
    if size > _MAX_BYTES:
        raise ReferenceValidationError("REFERENCE_TOO_LARGE")
    with path.open("rb") as handle:
        head = handle.read(16)
    if not _magic_ok(path, head):
        raise ReferenceValidationError("REFERENCE_MAGIC_INVALID")
    return ReferenceImage(path=path, size=size)


def result_paths(result_root: Path, task_id: str) -> tuple[Path, Path]:
    _validate_task_id(task_id)
    task_dir = Path(result_root) / task_id
    return task_dir / "result.png", task_dir / "result.json"
