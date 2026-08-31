from __future__ import annotations
import numpy as np
from zb_local_controller.reference_analysis import AnalysisParams, extrema_anchors, proportions, silhouette_from_border


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
