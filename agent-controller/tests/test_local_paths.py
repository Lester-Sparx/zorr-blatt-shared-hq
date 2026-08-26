from pathlib import Path
import pytest
from zb_local_controller.local_paths import PathBoundaryError, ReferenceValidationError, resolve_reference, result_paths

PNG = b"\x89PNG\r\n\x1a\n" + b"x" * 32
JPG = b"\xff\xd8\xff" + b"x" * 32
WEBP = b"RIFF" + (40).to_bytes(4, "little") + b"WEBP" + b"x" * 32


def test_rejects_task_id_path_traversal(tmp_path: Path):
    with pytest.raises(PathBoundaryError):
        resolve_reference(tmp_path, "..\\outside")


def test_missing_reference_returns_none(tmp_path: Path):
    assert resolve_reference(tmp_path, "ZB-SALVADOR-X-001") is None


def test_exactly_one_png_is_accepted(tmp_path: Path):
    d = tmp_path / "ZB-SALVADOR-X-001"
    d.mkdir()
    (d / "ref.png").write_bytes(PNG)
    ref = resolve_reference(tmp_path, "ZB-SALVADOR-X-001")
    assert ref.path.name == "ref.png"
    assert ref.size == len(PNG)


def test_two_supported_images_rejected(tmp_path: Path):
    d = tmp_path / "ZB-SALVADOR-X-001"; d.mkdir()
    (d / "a.png").write_bytes(PNG); (d / "b.jpg").write_bytes(JPG)
    with pytest.raises(ReferenceValidationError) as exc:
        resolve_reference(tmp_path, "ZB-SALVADOR-X-001")
    assert exc.value.code == "REFERENCE_COUNT_INVALID"


def test_unsupported_extension_rejected(tmp_path: Path):
    d = tmp_path / "ZB-SALVADOR-X-001"; d.mkdir()
    (d / "ref.gif").write_bytes(b"GIF89a")
    with pytest.raises(ReferenceValidationError) as exc:
        resolve_reference(tmp_path, "ZB-SALVADOR-X-001")
    assert exc.value.code == "REFERENCE_EXTENSION_INVALID"


def test_zero_byte_rejected(tmp_path: Path):
    d = tmp_path / "ZB-SALVADOR-X-001"; d.mkdir()
    (d / "ref.png").write_bytes(b"")
    with pytest.raises(ReferenceValidationError) as exc:
        resolve_reference(tmp_path, "ZB-SALVADOR-X-001")
    assert exc.value.code == "REFERENCE_EMPTY"


def test_over_20_mib_rejected(tmp_path: Path):
    d = tmp_path / "ZB-SALVADOR-X-001"; d.mkdir()
    p = d / "ref.png"
    p.write_bytes(b"\x89PNG\r\n\x1a\n" + b"x" * (20 * 1024 * 1024 + 1))
    with pytest.raises(ReferenceValidationError) as exc:
        resolve_reference(tmp_path, "ZB-SALVADOR-X-001")
    assert exc.value.code == "REFERENCE_TOO_LARGE"


def test_magic_mismatch_rejected(tmp_path: Path):
    d = tmp_path / "ZB-SALVADOR-X-001"; d.mkdir()
    (d / "ref.png").write_bytes(b"not-png")
    with pytest.raises(ReferenceValidationError) as exc:
        resolve_reference(tmp_path, "ZB-SALVADOR-X-001")
    assert exc.value.code == "REFERENCE_MAGIC_INVALID"


def test_result_paths_stay_under_root(tmp_path: Path):
    png, meta = result_paths(tmp_path, "ZB-SALVADOR-X-001")
    assert png == tmp_path / "ZB-SALVADOR-X-001" / "result.png"
    assert meta.name == "result.json"
