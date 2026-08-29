from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path

from pydantic import ValidationError

from .models import DurableRecord, parse_record


class ArchiveIntegrityError(RuntimeError):
    pass


@dataclass(frozen=True)
class RawObject:
    sha256: str
    path: Path
    size: int


class ArchiveStore:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.raw_root = self.root / "raw" / "sha256"
        self.records_root = self.root / "records"
        self.raw_root.mkdir(parents=True, exist_ok=True)
        self.records_root.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _write_once(path: Path, data: bytes, *, collision_code: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        except FileExistsError:
            try:
                existing = path.read_bytes()
            except OSError as exc:
                raise ArchiveIntegrityError(collision_code) from exc
            if existing != data:
                raise ArchiveIntegrityError(collision_code)
            return

        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
        except Exception:
            try:
                path.unlink(missing_ok=True)
            finally:
                raise

    @staticmethod
    def _canonical_record(record: DurableRecord) -> bytes:
        payload = record.model_dump(mode="json", exclude_none=True)
        return json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")

    def ingest_raw(self, data: bytes) -> RawObject:
        if not isinstance(data, bytes):
            raise TypeError("RAW_BYTES_REQUIRED")
        digest = hashlib.sha256(data).hexdigest()
        path = self.raw_root / digest[:2] / f"{digest}.bin"
        self._write_once(path, data, collision_code="RAW_HASH_MISMATCH")
        try:
            persisted = path.read_bytes()
        except OSError as exc:
            raise ArchiveIntegrityError("RAW_READBACK_FAILED") from exc
        if hashlib.sha256(persisted).hexdigest() != digest:
            raise ArchiveIntegrityError("RAW_HASH_MISMATCH")
        return RawObject(sha256=digest, path=path, size=len(data))

    def _verify_record_source(self, record: DurableRecord) -> None:
        location = record.source.source_location
        if not location.startswith("raw:"):
            return

        location_hash = location.removeprefix("raw:")
        expected_hash = record.source.source_hash
        if location_hash != expected_hash:
            raise ArchiveIntegrityError("SOURCE_RAW_BINDING_MISMATCH")

        raw_path = self.raw_root / expected_hash[:2] / f"{expected_hash}.bin"
        if not raw_path.is_file():
            raise ArchiveIntegrityError("SOURCE_RAW_MISSING")
        try:
            raw_bytes = raw_path.read_bytes()
        except OSError as exc:
            raise ArchiveIntegrityError("SOURCE_RAW_READ_FAILED") from exc
        if hashlib.sha256(raw_bytes).hexdigest() != expected_hash:
            raise ArchiveIntegrityError("SOURCE_RAW_HASH_MISMATCH")

    def append_record(self, record: DurableRecord) -> Path:
        self._verify_record_source(record)
        canonical = self._canonical_record(record)
        target = self.records_root / record.record_type.lower() / f"{record.record_id}.json"

        matches = sorted(self.records_root.glob(f"*/{record.record_id}.json"))
        if matches:
            if len(matches) != 1 or matches[0] != target:
                raise ArchiveIntegrityError("RECORD_ID_COLLISION")
            try:
                existing = matches[0].read_bytes()
            except OSError as exc:
                raise ArchiveIntegrityError("RECORD_READBACK_FAILED") from exc
            if existing != canonical:
                raise ArchiveIntegrityError("RECORD_ID_COLLISION")
            return target

        self._write_once(target, canonical, collision_code="RECORD_ID_COLLISION")
        try:
            persisted = target.read_bytes()
        except OSError as exc:
            raise ArchiveIntegrityError("RECORD_READBACK_FAILED") from exc
        if persisted != canonical:
            raise ArchiveIntegrityError("RECORD_READBACK_MISMATCH")
        return target

    @staticmethod
    def _load_record(path: Path) -> DurableRecord:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            record = parse_record(payload)
        except (OSError, UnicodeError, json.JSONDecodeError, ValidationError, TypeError, ValueError) as exc:
            raise ArchiveIntegrityError("RECORD_INVALID") from exc
        if path.stem != record.record_id or path.parent.name != record.record_type.lower():
            raise ArchiveIntegrityError("RECORD_PATH_MISMATCH")
        return record

    def iter_records(self) -> tuple[DurableRecord, ...]:
        records: list[DurableRecord] = []
        for path in sorted(self.records_root.glob("*/*.json")):
            record = self._load_record(path)
            self._verify_record_source(record)
            records.append(record)
        ids = [record.record_id for record in records]
        if len(ids) != len(set(ids)):
            raise ArchiveIntegrityError("RECORD_ID_COLLISION")
        return tuple(records)

    def get_record(self, record_id: str) -> DurableRecord:
        matches = sorted(self.records_root.glob(f"*/{record_id}.json"))
        if not matches:
            raise ArchiveIntegrityError("RECORD_NOT_FOUND")
        if len(matches) != 1:
            raise ArchiveIntegrityError("RECORD_ID_COLLISION")
        record = self._load_record(matches[0])
        self._verify_record_source(record)
        return record
