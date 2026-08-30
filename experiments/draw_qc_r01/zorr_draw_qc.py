"""Deterministic sandbox QC for the ZORR character drawing law.

This module is intentionally small glue around OpenCV primitives. It does not
render, train, or mutate production/canon state. Thresholds are sandbox R01
values derived from the OWNER-approved drawing anchor and durable law #199.
"""

from __future__ import annotations

from typing import Dict, Mapping

import cv2
import numpy as np


TARGET_HEAD_WIDTH_PX = 397
FOREGROUND_GRAY_MAX = 244
INK_GRAY_MAX = 29
STRONG_EDGE_SOBEL_MIN = 50.0
KMEANS_MAX_CLUSTERS = 8
KMEANS_OCCUPANCY_MIN = 0.02
KMEANS_SEED = 1337

TONE_BANDS_MIN = 4
TONE_BANDS_MAX = 6
STRONG_EDGE_DENSITY_MIN = 0.08
STRONG_EDGE_DENSITY_MAX = 0.14
DEEP_INK_COVERAGE_MAX = 0.05
LINE_HIERARCHY_RATIO_MIN = 4.0
HIGH_FREQ_LAPLACIAN_VARIANCE_MAX = 800.0


def _largest_foreground_component(image_bgr: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    if image_bgr is None or image_bgr.ndim != 3 or image_bgr.shape[2] != 3:
        raise ValueError("expected non-empty BGR image with shape HxWx3")

    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    binary = (gray <= FOREGROUND_GRAY_MAX).astype(np.uint8)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
    if count <= 1:
        raise ValueError("no foreground component found")

    component_index = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    x = int(stats[component_index, cv2.CC_STAT_LEFT])
    y = int(stats[component_index, cv2.CC_STAT_TOP])
    w = int(stats[component_index, cv2.CC_STAT_WIDTH])
    h = int(stats[component_index, cv2.CC_STAT_HEIGHT])
    if w <= 0 or h <= 0:
        raise ValueError("invalid foreground component bounds")

    crop = image_bgr[y : y + h, x : x + w]
    mask = (labels[y : y + h, x : x + w] == component_index).astype(np.uint8)
    return crop, mask


def _normalize_head(crop: np.ndarray, mask: np.ndarray, target_width: int) -> tuple[np.ndarray, np.ndarray]:
    if target_width <= 0:
        raise ValueError("target_width must be positive")
    source_width = crop.shape[1]
    scale = float(target_width) / float(source_width)
    target_height = max(1, int(round(crop.shape[0] * scale)))
    interpolation = cv2.INTER_AREA if scale <= 1.0 else cv2.INTER_LINEAR
    resized = cv2.resize(crop, (target_width, target_height), interpolation=interpolation)
    resized_mask = cv2.resize(mask, (target_width, target_height), interpolation=cv2.INTER_NEAREST).astype(bool)
    if not np.any(resized_mask):
        raise ValueError("foreground mask became empty after normalization")
    return resized, resized_mask


def _tone_band_count(image_bgr: np.ndarray, mask: np.ndarray) -> int:
    lab = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2LAB)
    samples = lab[mask].reshape(-1, 3)
    if samples.size == 0:
        raise ValueError("cannot quantize empty foreground")

    unique_count = int(np.unique(samples, axis=0).shape[0])
    k = min(KMEANS_MAX_CLUSTERS, unique_count, int(samples.shape[0]))
    if k <= 0:
        raise ValueError("cannot quantize empty foreground")

    data = samples.astype(np.float32)
    cv2.setRNGSeed(KMEANS_SEED)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 50, 0.2)
    _, labels, _ = cv2.kmeans(data, k, None, criteria, 1, cv2.KMEANS_PP_CENTERS)
    counts = np.bincount(labels.reshape(-1), minlength=k).astype(np.float64)
    occupancy = counts / counts.sum()
    return int(np.count_nonzero(occupancy >= KMEANS_OCCUPANCY_MIN))


def analyze_image_bgr(image_bgr: np.ndarray, target_width: int = TARGET_HEAD_WIDTH_PX) -> Dict[str, float]:
    """Measure one front-head candidate using deterministic OpenCV operations."""

    crop, component_mask = _largest_foreground_component(image_bgr)
    crop, mask = _normalize_head(crop, component_mask, target_width)
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)

    gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    magnitude = cv2.magnitude(gx, gy)
    strong_edge_density = float(np.mean(magnitude[mask] > STRONG_EDGE_SOBEL_MIN))

    deep_ink_coverage = float(np.mean(gray[mask] <= INK_GRAY_MAX))
    ink = ((gray <= INK_GRAY_MAX) & mask).astype(np.uint8)
    ink_distance = cv2.distanceTransform(ink, cv2.DIST_L2, 5)
    ink_values = ink_distance[ink.astype(bool)]
    if ink_values.size:
        median_radius = float(np.median(ink_values))
        p95_radius = float(np.percentile(ink_values, 95))
        line_hierarchy_ratio = p95_radius / max(median_radius, 1e-6)
    else:
        line_hierarchy_ratio = 0.0

    laplacian = cv2.Laplacian(gray, cv2.CV_64F, ksize=1)
    high_freq_laplacian_variance = float(np.var(laplacian[mask]))

    return {
        "tone_bands": float(_tone_band_count(crop, mask)),
        "strong_edge_density": strong_edge_density,
        "deep_ink_coverage": deep_ink_coverage,
        "line_hierarchy_ratio": float(line_hierarchy_ratio),
        "high_freq_laplacian_variance": high_freq_laplacian_variance,
    }


def evaluate_metrics(metrics: Mapping[str, float]) -> Dict[str, object]:
    """Apply the R01 measurable envelope and return fail-closed reasons."""

    failures = []
    tone_bands = float(metrics["tone_bands"])
    edge_density = float(metrics["strong_edge_density"])
    deep_ink = float(metrics["deep_ink_coverage"])
    line_ratio = float(metrics["line_hierarchy_ratio"])
    high_freq = float(metrics["high_freq_laplacian_variance"])

    if not TONE_BANDS_MIN <= tone_bands <= TONE_BANDS_MAX:
        failures.append("STYLE_TONE_COUNT_FAIL")
    if not STRONG_EDGE_DENSITY_MIN <= edge_density <= STRONG_EDGE_DENSITY_MAX:
        failures.append("STYLE_EDGE_DENSITY_FAIL")
    if not deep_ink < DEEP_INK_COVERAGE_MAX:
        failures.append("STYLE_DEEP_INK_FAIL")
    if not line_ratio >= LINE_HIERARCHY_RATIO_MIN:
        failures.append("STYLE_LINE_HIERARCHY_FAIL")
    if not high_freq <= HIGH_FREQ_LAPLACIAN_VARIANCE_MAX:
        failures.append("STYLE_TOO_NOISY")

    return {
        "verdict": "PASS" if not failures else "FAIL",
        "failures": failures,
    }
