from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import os
from pathlib import Path
import re
import shutil
from uuid import uuid4

from .config import BridgeConfig
from .contracts import ReferenceDelivery
from .local_delivery import ValidatedSource

_TASK_ID_RE = re.compile(r"^[A-Z0-9_-]+$")


class PublishError(RuntimeError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class PublishResult:
    state: str
    final_path: Path


def _expected_final(config: BridgeConfig, delivery: ReferenceDelivery, source: ValidatedSource) -> tuple[Path, Path]:
    if not _TASK_ID_RE.fullmatch(delivery.task_id):
        raise PublishError("REFERENCE_DESTINATION_CONFLICT")
    final_dir = Path(config.inbox_root) / delivery.task_id
    return final_dir, final_dir / f"source{source.extension}"


def _existing_result(final_dir: Path, final_file: Path, expected_sha: str) -> PublishResult:
    if not final_dir.is_dir():
        raise PublishError("REFERENCE_DESTINATION_CONFLICT")
    try:
        entries = list(final_dir.iterdir())
    except OSError as exc:
        raise PublishError("REFERENCE_DESTINATION_CONFLICT") from exc
    if len(entries) != 1 or entries[0] != final_file or not final_file.is_file() or final_file.is_symlink():
        raise PublishError("REFERENCE_DESTINATION_CONFLICT")
    try:
        digest = sha256(final_file.read_bytes()).hexdigest()
    except OSError as exc:
        raise PublishError("REFERENCE_DESTINATION_CONFLICT") from exc
    if digest != expected_sha:
        raise PublishError("REFERENCE_DESTINATION_CONFLICT")
    return PublishResult("ALREADY_PRESENT", final_file)


def publish_reference(config: BridgeConfig, delivery: ReferenceDelivery, source: ValidatedSource) -> PublishResult:
    final_dir, final_file = _expected_final(config, delivery, source)
    if final_dir.exists():
        return _existing_result(final_dir, final_file, source.sha256)

    staging_root = Path(config.runtime_root) / "staging"
    staging_dir = staging_root / f"{delivery.delivery_id}-{uuid4().hex}"
    staged = staging_dir / f"source{source.extension}"
    try:
        staging_dir.mkdir(parents=True, exist_ok=False)
        shutil.copyfile(source.path, staged)
        try:
            staged_sha = sha256(staged.read_bytes()).hexdigest()
        except OSError as exc:
            raise PublishError("REFERENCE_PUBLISH_FAILED") from exc
        if staged_sha != source.sha256:
            raise PublishError("REFERENCE_STAGING_HASH_MISMATCH")
        Path(config.inbox_root).mkdir(parents=True, exist_ok=True)
        if final_dir.exists():
            return _existing_result(final_dir, final_file, source.sha256)
        try:
            os.replace(staging_dir, final_dir)
        except OSError as exc:
            if final_dir.exists():
                return _existing_result(final_dir, final_file, source.sha256)
            raise PublishError("REFERENCE_PUBLISH_FAILED") from exc
        return PublishResult("PUBLISHED", final_file)
    finally:
        if staging_dir.exists():
            shutil.rmtree(staging_dir, ignore_errors=True)


def quarantine_delivery(config: BridgeConfig, delivery: ReferenceDelivery, source_path: Path, error_code: str) -> Path:
    root = Path(config.quarantine_root) / delivery.delivery_id
    root.mkdir(parents=True, exist_ok=True)
    source_path = Path(source_path)
    suffix = source_path.suffix.lower() or ".bin"
    final = root / f"source{suffix}"
    tmp = root / f".source-{uuid4().hex}.tmp"
    try:
        shutil.copyfile(source_path, tmp)
        os.replace(tmp, final)
    except OSError as exc:
        raise PublishError("REFERENCE_PUBLISH_FAILED") from exc
    finally:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
    return final
