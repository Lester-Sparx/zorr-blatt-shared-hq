from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
from typing import Any


class EvidenceError(RuntimeError):
    pass


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _safe_changed_file(path: str) -> str:
    if not path or "\x00" in path or "\\" in path or path.startswith(("/", "~")):
        raise EvidenceError("INVALID_CHANGED_FILE")
    pure = PurePosixPath(path)
    if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
        raise EvidenceError("INVALID_CHANGED_FILE")
    return pure.as_posix()


def _write_bytes(path: Path, data: bytes) -> str:
    path.write_bytes(data)
    return _sha256_bytes(data)


def verify_artifact_metadata(
    metadata: dict[str, Any],
    *,
    expected_id: int,
    expected_digest: str,
    expected_run_id: int,
) -> None:
    if (
        not isinstance(expected_id, int)
        or isinstance(expected_id, bool)
        or expected_id <= 0
        or not isinstance(expected_run_id, int)
        or isinstance(expected_run_id, bool)
        or expected_run_id <= 0
    ):
        raise EvidenceError("ARTIFACT_BINDING_INVALID")
    if (
        not isinstance(expected_digest, str)
        or len(expected_digest) != 64
        or any(ch not in "0123456789abcdef" for ch in expected_digest)
    ):
        raise EvidenceError("ARTIFACT_DIGEST_INVALID")
    if not isinstance(metadata, dict):
        raise EvidenceError("ARTIFACT_METADATA_INVALID")
    workflow_run = metadata.get("workflow_run")
    if not isinstance(workflow_run, dict):
        raise EvidenceError("ARTIFACT_METADATA_INVALID")
    if metadata.get("id") != expected_id:
        raise EvidenceError("ARTIFACT_ID_MISMATCH")
    if metadata.get("expired") is not False:
        raise EvidenceError("ARTIFACT_EXPIRED_OR_UNKNOWN")
    if metadata.get("digest") != f"sha256:{expected_digest}":
        raise EvidenceError("ARTIFACT_DIGEST_MISMATCH")
    if workflow_run.get("id") != expected_run_id:
        raise EvidenceError("ARTIFACT_WORKFLOW_RUN_MISMATCH")


def build_evidence_bundle(
    *,
    request_body: str,
    result_body: str | None,
    patch_bytes: bytes,
    changed_files: tuple[str, ...],
    tests_text: str,
    worker_events: str,
    evidence_dir: Path,
) -> dict[str, str]:
    if not isinstance(request_body, str) or not isinstance(patch_bytes, bytes):
        raise EvidenceError("INVALID_EVIDENCE_INPUT")
    if result_body is not None and not isinstance(result_body, str):
        raise EvidenceError("INVALID_EVIDENCE_INPUT")
    evidence_dir = Path(evidence_dir)
    if evidence_dir.exists():
        if evidence_dir.is_symlink():
            raise EvidenceError("EVIDENCE_DIR_SYMLINK")
        shutil.rmtree(evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=False)

    normalized_files = tuple(sorted(_safe_changed_file(path) for path in changed_files))
    if len(normalized_files) != len(set(normalized_files)):
        raise EvidenceError("INVALID_CHANGED_FILE")

    contents: dict[str, bytes] = {
        "request.txt": request_body.encode("utf-8"),
        "patch.diff": patch_bytes,
        "changed-files.txt": ("\n".join(normalized_files) + ("\n" if normalized_files else "")).encode("utf-8"),
        "tests.txt": tests_text.encode("utf-8"),
        "worker-events.jsonl": worker_events.encode("utf-8"),
    }
    if result_body is not None:
        contents["result.txt"] = result_body.encode("utf-8")

    manifest = {name: _write_bytes(evidence_dir / name, contents[name]) for name in sorted(contents)}
    manifest_bytes = (json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    (evidence_dir / "manifest.json").write_bytes(manifest_bytes)
    return manifest


def verify_evidence_manifest(evidence_dir: Path) -> dict[str, str]:
    evidence_dir = Path(evidence_dir)
    manifest_path = evidence_dir / "manifest.json"
    if not evidence_dir.is_dir() or not manifest_path.is_file():
        raise EvidenceError("EVIDENCE_MANIFEST_MISSING")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvidenceError("EVIDENCE_MANIFEST_INVALID") from exc
    if not isinstance(manifest, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in manifest.items()):
        raise EvidenceError("EVIDENCE_MANIFEST_INVALID")

    expected_names = set(manifest) | {"manifest.json"}
    actual_names = {path.name for path in evidence_dir.iterdir() if path.is_file()}
    missing = expected_names - actual_names
    if missing:
        raise EvidenceError("EVIDENCE_FILE_MISSING")
    extra = actual_names - expected_names
    if extra:
        raise EvidenceError("EVIDENCE_EXTRA_FILE")

    for name, expected_digest in manifest.items():
        if len(expected_digest) != 64 or any(ch not in "0123456789abcdef" for ch in expected_digest):
            raise EvidenceError("EVIDENCE_MANIFEST_INVALID")
        path = evidence_dir / name
        actual = _sha256_bytes(path.read_bytes())
        if actual != expected_digest:
            raise EvidenceError("EVIDENCE_HASH_MISMATCH")
    return dict(sorted(manifest.items()))
