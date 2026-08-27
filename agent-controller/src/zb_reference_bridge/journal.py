from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import re

_DELIVERY_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,128}$")


class JournalConflict(RuntimeError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class DeliveryReceipt:
    delivery_id: str
    task_id: str
    source_sha256: str
    state: str
    issue_number: int
    created_at_utc: str
    error_code: str | None = None
    delivery_metadata_sha256: str | None = None


def _require_safe_delivery_id(delivery_id: str) -> None:
    if not isinstance(delivery_id, str) or not _DELIVERY_ID_RE.fullmatch(delivery_id):
        raise JournalConflict("REFERENCE_DELIVERY_ID_CONFLICT")


def _fsync_directory(path: Path) -> None:
    try:
        directory_fd = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    except OSError:
        return
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)


class ReferenceJournal:
    def __init__(self, runtime_root: Path):
        self.runtime_root = Path(runtime_root)
        self.receipts_root = self.runtime_root / "receipts"
        self.consumed_comments_root = self.runtime_root / "consumed-comments"
        self._by_delivery: dict[str, DeliveryReceipt] = {}
        self._by_task: dict[str, DeliveryReceipt] = {}
        self._rebuild()

    def _rebuild(self) -> None:
        if not self.receipts_root.exists():
            return
        for path in sorted(self.receipts_root.glob("*.json")):
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                receipt = DeliveryReceipt(**raw)
                _require_safe_delivery_id(receipt.delivery_id)
            except Exception as exc:
                if isinstance(exc, JournalConflict):
                    raise
                raise JournalConflict("REFERENCE_DELIVERY_ID_CONFLICT") from exc
            existing = self._by_delivery.get(receipt.delivery_id)
            if existing is not None and existing != receipt:
                raise JournalConflict("REFERENCE_DELIVERY_ID_CONFLICT")
            task = self._by_task.get(receipt.task_id)
            if task is not None and task.state == "ACCEPTED" and receipt.state == "ACCEPTED" and task.source_sha256 != receipt.source_sha256:
                raise JournalConflict("REFERENCE_TASK_CONFLICT")
            self._by_delivery[receipt.delivery_id] = receipt
            if task is None or receipt.state == "ACCEPTED":
                self._by_task[receipt.task_id] = receipt

    def lookup_delivery(self, delivery_id: str) -> DeliveryReceipt | None:
        return self._by_delivery.get(delivery_id)

    def lookup_task(self, task_id: str) -> DeliveryReceipt | None:
        return self._by_task.get(task_id)

    def _comment_marker(self, comment_id: str) -> Path:
        if not isinstance(comment_id, str) or not comment_id:
            raise JournalConflict("REFERENCE_COMMENT_ID_INVALID")
        return self.consumed_comments_root / f"{sha256(comment_id.encode('utf-8')).hexdigest()}.json"

    def is_comment_consumed(self, comment_id: str) -> bool:
        marker = self._comment_marker(comment_id)
        if not marker.exists():
            return False
        try:
            raw = json.loads(marker.read_text(encoding="utf-8"))
        except Exception as exc:
            raise JournalConflict("REFERENCE_COMMENT_JOURNAL_INVALID") from exc
        if raw != {"comment_id": comment_id}:
            raise JournalConflict("REFERENCE_COMMENT_JOURNAL_INVALID")
        return True

    def mark_comment_consumed(self, comment_id: str) -> None:
        marker = self._comment_marker(comment_id)
        if self.is_comment_consumed(comment_id):
            return
        comments_root_existed = self.consumed_comments_root.exists()
        self.consumed_comments_root.mkdir(parents=True, exist_ok=True)
        if not comments_root_existed:
            _fsync_directory(self.runtime_root)
        tmp = marker.with_suffix(".tmp")
        try:
            with tmp.open("w", encoding="utf-8") as handle:
                handle.write(json.dumps({"comment_id": comment_id}, sort_keys=True) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp, marker)
            _fsync_directory(self.consumed_comments_root)
        finally:
            try:
                tmp.unlink(missing_ok=True)
            except OSError:
                pass

    def append(self, receipt: DeliveryReceipt) -> DeliveryReceipt:
        _require_safe_delivery_id(receipt.delivery_id)
        existing = self._by_delivery.get(receipt.delivery_id)
        if existing is not None:
            if existing == receipt:
                return existing
            raise JournalConflict("REFERENCE_DELIVERY_ID_CONFLICT")

        task = self._by_task.get(receipt.task_id)
        if task is not None and task.state == "ACCEPTED" and receipt.state == "ACCEPTED" and task.source_sha256 != receipt.source_sha256:
            raise JournalConflict("REFERENCE_TASK_CONFLICT")

        self.receipts_root.mkdir(parents=True, exist_ok=True)
        final = self.receipts_root / f"{receipt.delivery_id}.json"
        tmp = final.with_suffix(".tmp")
        try:
            tmp.write_text(json.dumps(asdict(receipt), indent=2, sort_keys=True) + "\n", encoding="utf-8")
            os.replace(tmp, final)
        finally:
            try:
                tmp.unlink(missing_ok=True)
            except OSError:
                pass
        self._by_delivery[receipt.delivery_id] = receipt
        if task is None or receipt.state == "ACCEPTED":
            self._by_task[receipt.task_id] = receipt
        return receipt
