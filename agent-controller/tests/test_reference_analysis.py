from __future__ import annotations
import numpy as np
from pathlib import Path
from zb_local_controller.reference_analysis import AnalysisParams, extrema_anchors, proportions, save_npz_deterministic, silhouette_from_border


def test_params_validate() -> None:
    AnalysisParams(0.0, 1.0, 1).validate()


def test_otsu_silhouette_uses_source_border_evidence() -> None:
    rgb = np.full((16, 16, 3), 250, dtype=np.uint8)
    rgb[4:12, 5:11] = np.array([30, 40, 50], dtype=np.uint8)
    mask, _lab, info = silhouette_from_border(rgb)
    assert mask[8, 8] == 255 and mask[0, 0] == 0
    assert "Otsu" in info["method"]


def test_extrema_and_proportions_use_visible_mask_only() -> None:
    mask = np.zeros((10, 12), dtype=np.uint8); mask[2:9, 3:10] = 255
    anchors = extrema_anchors(mask)
    assert len(anchors) == 4 and all(a["provenance"] == "DERIVED" for a in anchors)
    graph = proportions(anchors, 7)
    assert graph["scale"]["value_px"] == 7 and len(graph["edges"]) == 6


def test_npz_bytes_are_deterministic(tmp_path: Path) -> None:
    arrays = {"b": np.arange(4, dtype=np.int16), "a": np.eye(2, dtype=np.float32)}
    p1, p2 = tmp_path / "one.npz", tmp_path / "two.npz"
    save_npz_deterministic(p1, arrays); save_npz_deterministic(p2, arrays)
    assert p1.read_bytes() == p2.read_bytes()


def test_full_analysis_bytes_are_deterministic(tmp_path: Path) -> None:
    import cv2
    from zb_local_controller.reference_analysis import analyze
    rgb = np.full((64, 64, 3), 250, dtype=np.uint8)
    rgb[12:52, 18:46] = np.array([20, 60, 120], dtype=np.uint8)
    source = tmp_path / "source.png"
    assert cv2.imwrite(str(source), cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
    params = AnalysisParams(1.0, 4.0, 2)
    j1, n1 = tmp_path / "one.json", tmp_path / "layers.npz"
    d2 = tmp_path / "repeat"; d2.mkdir()
    j2, n2 = d2 / "one.json", d2 / "layers.npz"
    analyze(source, j1, n1, params); analyze(source, j2, n2, params)
    assert n1.read_bytes() == n2.read_bytes()
    assert j1.read_bytes() == j2.read_bytes()
