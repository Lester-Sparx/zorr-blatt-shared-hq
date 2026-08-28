from __future__ import annotations

from pathlib import Path


TARGET = Path("tests/fixtures/zb-execution-proof/result.txt")
EXPECTED = "ZB_R02A_PROOF_TARGET_V1\nSTATE = AFTER\n"


def verify_proof_target(root: Path | str = Path.cwd()) -> Path:
    root_path = Path(root).resolve()
    candidate = root_path / TARGET
    if candidate.is_symlink():
        raise RuntimeError("PROOF_TARGET_NOT_AFTER")
    target = candidate.resolve()
    if target != root_path and root_path not in target.parents:
        raise RuntimeError("PROOF_TARGET_NOT_AFTER")
    if not target.is_file():
        raise RuntimeError("PROOF_TARGET_NOT_AFTER")
    try:
        content = target.read_text(encoding="utf-8")
    except OSError as exc:
        raise RuntimeError("PROOF_TARGET_NOT_AFTER") from exc
    if content != EXPECTED:
        raise RuntimeError("PROOF_TARGET_NOT_AFTER")
    return target


def main() -> int:
    target = verify_proof_target(Path.cwd())
    print(f"PROOF_VERIFY = PASS | {target.relative_to(Path.cwd().resolve()).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
