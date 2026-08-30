"""Deterministic sandbox QC for the ZORR character drawing law.

This module is intentionally small glue around OpenCV primitives. It does not
render, train, or mutate production/canon state. R01 absolute thresholds are
derived from the OWNER-approved drawing anchor and durable law #199. R02
transfer thresholds are provisional consistency limits measured from the
current C00-B model-sheet front/3/4 study set; they are not canon locks. R03
head geometry thresholds measure mirrored yaw consistency only.
"""

from __future__ import annotations

from typing import Dict, Mapping, Sequence

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

TRANSFER_MIN_VIEWS = 3
TRANSFER_TONE_RANGE_MAX = 1.0
TRANSFER_EDGE_CV_MAX = 0.06
TRANSFER_INK_CV_MAX = 0.12
TRANSFER_LINE_CV_MAX = 0.06
TRANSFER_HIGH_FREQ_CV_MAX = 0.30

HEAD_GEOMETRY_CANVAS_SIZE = 512
HEAD_MIRROR_DICE_MIN = 0.96
HEAD_PAIR_ASPECT_DRIFT_MAX = 0.03


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


def _crop_to_mask(image_bgr: np.ndarray, mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    if image_bgr is None or image_bgr.ndim != 3 or image_bgr.shape[2] != 3:
        raise ValueError("expected non-empty BGR image with shape HxWx3")
    if mask is None or mask.ndim != 2:
        raise ValueError("expected non-empty 2D region mask")
    if mask.shape != image_bgr.shape[:2]:
        raise ValueError("region mask shape must match image height/width")

    region = mask.astype(bool)
    ys, xs = np.where(region)
    if ys.size == 0:
        raise ValueError("region mask is empty")

    y0 = int(ys.min())
    y1 = int(ys.max()) + 1
    x0 = int(xs.min())
    x1 = int(xs.max()) + 1
    return image_bgr[y0:y1, x0:x1], region[y0:y1, x0:x1].astype(np.uint8)


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


def _measure_normalized_region(crop: np.ndarray, mask: np.ndarray, target_width: int) -> Dict[str, float]:
    crop, mask = _normalize_head(crop, mask, target_width)
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


def _coefficient_of_variation(values: Sequence[float]) -> float:
    data = np.asarray(values, dtype=np.float64)
    if data.size == 0 or not np.all(np.isfinite(data)):
        raise ValueError("transfer metrics must be finite and non-empty")
    mean = float(np.mean(data))
    std = float(np.std(data))
    if abs(mean) <= 1e-12:
        return 0.0 if std <= 1e-12 else float("inf")
    return std / abs(mean)


def _normalize_binary_mask(mask: np.ndarray, canvas_size: int = HEAD_GEOMETRY_CANVAS_SIZE) -> np.ndarray:
    if mask is None or mask.ndim != 2:
        raise ValueError("head geometry mask must be a non-empty 2D array")
    region = mask.astype(bool)
    ys, xs = np.where(region)
    if ys.size == 0:
        raise ValueError("head geometry mask is empty")
    if canvas_size < 32:
        raise ValueError("head geometry canvas_size is too small")

    y0, y1 = int(ys.min()), int(ys.max()) + 1
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    crop = region[y0:y1, x0:x1].astype(np.uint8) * 255

    margin = max(4, canvas_size // 25)
    usable = canvas_size - 2 * margin
    scale = min(float(usable) / float(crop.shape[1]), float(usable) / float(crop.shape[0]))
    width = max(1, int(round(crop.shape[1] * scale)))
    height = max(1, int(round(crop.shape[0] * scale)))
    resized = cv2.resize(crop, (width, height), interpolation=cv2.INTER_NEAREST)

    canvas = np.zeros((canvas_size, canvas_size), dtype=np.uint8)
    x = (canvas_size - width) // 2
    y = (canvas_size - height) // 2
    canvas[y : y + height, x : x + width] = resized
    return canvas


def _binary_dice(mask_a: np.ndarray, mask_b: np.ndarray) -> float:
    a = mask_a.astype(bool)
    b = mask_b.astype(bool)
    denominator = int(a.sum()) + int(b.sum())
    if denominator == 0:
        raise ValueError("cannot compare two empty masks")
    return float(2.0 * np.logical_and(a, b).sum() / denominator)


def _mask_aspect_ratio(mask: np.ndarray) -> float:
    region = mask.astype(bool)
    ys, xs = np.where(region)
    if ys.size == 0:
        raise ValueError("head geometry mask is empty")
    width = float(xs.max() - xs.min() + 1)
    height = float(ys.max() - ys.min() + 1)
    return width / height


def _relative_pair_drift(value_a: float, value_b: float) -> float:
    mean = (abs(value_a) + abs(value_b)) / 2.0
    if mean <= 1e-12:
        return 0.0 if abs(value_a - value_b) <= 1e-12 else float("inf")
    return abs(value_a - value_b) / mean


def analyze_image_bgr(image_bgr: np.ndarray, target_width: int = TARGET_HEAD_WIDTH_PX) -> Dict[str, float]:
    """Measure the largest connected foreground component."""
    crop, component_mask = _largest_foreground_component(image_bgr)
    return _measure_normalized_region(crop, component_mask, target_width)


def analyze_region_bgr(
    image_bgr: np.ndarray,
    region_mask: np.ndarray,
    target_width: int = TARGET_HEAD_WIDTH_PX,
) -> Dict[str, float]:
    """Measure one explicit semantic region using the same deterministic metrics."""
    crop, mask = _crop_to_mask(image_bgr, region_mask)
    return _measure_normalized_region(crop, mask, target_width)


def analyze_head_geometry_masks(masks: Mapping[str, np.ndarray]) -> Dict[str, float]:
    """Measure mirrored yaw consistency from five caller-supplied silhouette masks."""
    required = (
        "profile_left",
        "threequarter_left",
        "front",
        "threequarter_right",
        "profile_right",
    )
    missing = [name for name in required if name not in masks]
    if missing:
        raise ValueError(f"missing head geometry masks: {', '.join(missing)}")

    normalized = {name: _normalize_binary_mask(masks[name]) for name in required}

    profile_dice = _binary_dice(normalized["profile_left"], cv2.flip(normalized["profile_right"], 1))
    threequarter_dice = _binary_dice(
        normalized["threequarter_left"], cv2.flip(normalized["threequarter_right"], 1)
    )
    front_dice = _binary_dice(normalized["front"], cv2.flip(normalized["front"], 1))

    profile_left_aspect = _mask_aspect_ratio(masks["profile_left"])
    profile_right_aspect = _mask_aspect_ratio(masks["profile_right"])
    threequarter_left_aspect = _mask_aspect_ratio(masks["threequarter_left"])
    threequarter_right_aspect = _mask_aspect_ratio(masks["threequarter_right"])

    return {
        "profile_mirror_dice": profile_dice,
        "threequarter_mirror_dice": threequarter_dice,
        "front_self_mirror_dice": front_dice,
        "profile_aspect_drift": _relative_pair_drift(profile_left_aspect, profile_right_aspect),
        "threequarter_aspect_drift": _relative_pair_drift(threequarter_left_aspect, threequarter_right_aspect),
    }


def evaluate_metrics(metrics: Mapping[str, float]) -> Dict[str, object]:
    """Apply the R01 absolute anchor envelope and return fail-closed reasons."""
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

    return {"verdict": "PASS" if not failures else "FAIL", "failures": failures}


def evaluate_transfer_consistency(samples: Sequence[Mapping[str, float]]) -> Dict[str, object]:
    """Check cross-view style stability without reusing the absolute R01 envelope."""
    if len(samples) < TRANSFER_MIN_VIEWS:
        raise ValueError("transfer consistency requires at least three views")

    metric_names = (
        "tone_bands",
        "strong_edge_density",
        "deep_ink_coverage",
        "line_hierarchy_ratio",
        "high_freq_laplacian_variance",
    )
    columns = {
        name: np.asarray([float(sample[name]) for sample in samples], dtype=np.float64)
        for name in metric_names
    }
    if any(not np.all(np.isfinite(values)) for values in columns.values()):
        raise ValueError("transfer metrics must be finite")

    tone_range = float(np.max(columns["tone_bands"]) - np.min(columns["tone_bands"]))
    edge_cv = _coefficient_of_variation(columns["strong_edge_density"])
    ink_cv = _coefficient_of_variation(columns["deep_ink_coverage"])
    line_cv = _coefficient_of_variation(columns["line_hierarchy_ratio"])
    high_freq_cv = _coefficient_of_variation(columns["high_freq_laplacian_variance"])

    failures = []
    if tone_range > TRANSFER_TONE_RANGE_MAX:
        failures.append("TRANSFER_TONE_DRIFT_FAIL")
    if edge_cv > TRANSFER_EDGE_CV_MAX:
        failures.append("TRANSFER_EDGE_DRIFT_FAIL")
    if ink_cv > TRANSFER_INK_CV_MAX:
        failures.append("TRANSFER_INK_DRIFT_FAIL")
    if line_cv > TRANSFER_LINE_CV_MAX:
        failures.append("TRANSFER_LINE_DRIFT_FAIL")
    if high_freq_cv > TRANSFER_HIGH_FREQ_CV_MAX:
        failures.append("TRANSFER_HIGH_FREQ_DRIFT_FAIL")

    return {
        "verdict": "PASS" if not failures else "FAIL",
        "failures": failures,
        "diagnostics": {
            "tone_range": tone_range,
            "edge_cv": edge_cv,
            "ink_cv": ink_cv,
            "line_cv": line_cv,
            "high_freq_cv": high_freq_cv,
        },
    }


def evaluate_head_geometry_consistency(metrics: Mapping[str, float]) -> Dict[str, object]:
    """Apply the provisional R03 mirrored-yaw geometry envelope."""
    failures = []
    profile_dice = float(metrics["profile_mirror_dice"])
    threequarter_dice = float(metrics["threequarter_mirror_dice"])
    front_dice = float(metrics["front_self_mirror_dice"])
    profile_aspect_drift = float(metrics["profile_aspect_drift"])
    threequarter_aspect_drift = float(metrics["threequarter_aspect_drift"])

    if profile_dice < HEAD_MIRROR_DICE_MIN:
        failures.append("HEAD_PROFILE_MIRROR_FAIL")
    if threequarter_dice < HEAD_MIRROR_DICE_MIN:
        failures.append("HEAD_THREEQUARTER_MIRROR_FAIL")
    if front_dice < HEAD_MIRROR_DICE_MIN:
        failures.append("HEAD_FRONT_SYMMETRY_FAIL")
    if profile_aspect_drift > HEAD_PAIR_ASPECT_DRIFT_MAX:
        failures.append("HEAD_PROFILE_ASPECT_DRIFT_FAIL")
    if threequarter_aspect_drift > HEAD_PAIR_ASPECT_DRIFT_MAX:
        failures.append("HEAD_THREEQUARTER_ASPECT_DRIFT_FAIL")

    return {"verdict": "PASS" if not failures else "FAIL", "failures": failures}
