#!/usr/bin/env python3
"""Deterministic pixel-preserving local face motion engine for stylized 2D art.

Design goals:
- Keep source canvas/crop/identity pixel-identical outside explicitly editable masks.
- Drive expression with measured pixel displacements, not prompt-only regeneration.
- Use only OSS runtime dependencies: NumPy + OpenCV + PyYAML.
- Support repeatable frame schedules and QC manifests.

The warp uses Gaussian radial-basis interpolation of inverse displacement vectors.
Zero-displacement lock anchors pin region boundaries. Each region is composited with
its own feathered mask, so unrelated pixels remain exactly equal to the source.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import cv2
import numpy as np
import yaml


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def smoothstep(t: float) -> float:
    t = float(np.clip(t, 0.0, 1.0))
    return t * t * (3.0 - 2.0 * t)


def smootherstep(t: float) -> float:
    t = float(np.clip(t, 0.0, 1.0))
    return t**3 * (t * (t * 6.0 - 15.0) + 10.0)


def easing(name: str, t: float) -> float:
    if name == "linear":
        return float(np.clip(t, 0.0, 1.0))
    if name == "smoothstep":
        return smoothstep(t)
    if name == "smootherstep":
        return smootherstep(t)
    raise ValueError(f"Unknown easing: {name}")


def validate_config(cfg: Dict[str, Any], w: int, h: int) -> None:
    t_values = [float(v) for v in cfg["animation"]["t_values"]]
    if not t_values:
        raise ValueError("animation.t_values must not be empty")
    if any(t < 0.0 or t > 1.0 for t in t_values):
        raise ValueError("animation.t_values must stay in [0,1]")
    if any(b < a for a, b in zip(t_values, t_values[1:])):
        raise ValueError("animation.t_values must be nondecreasing")

    max_disp = float(cfg.get("limits", {}).get("max_control_displacement_px", 32.0))
    names = set()
    for region in cfg.get("regions", []):
        name = str(region.get("name", ""))
        if not name or name in names:
            raise ValueError(f"region names must be unique and nonempty: {name!r}")
        names.add(name)
        if not region.get("controls"):
            raise ValueError(f"region {name} has no controls")
        for item in region.get("controls", []):
            x, y = [float(v) for v in item["xy"]]
            dx, dy = [float(v) for v in item["delta_at_1"]]
            if not (0 <= x < w and 0 <= y < h):
                raise ValueError(f"control outside image in {name}: {(x, y)}")
            if float(np.hypot(dx, dy)) > max_disp:
                raise ValueError(
                    f"control displacement exceeds {max_disp}px in {name}: {(dx, dy)}"
                )
        for x, y in region.get("locks", []):
            if not (0 <= float(x) < w and 0 <= float(y) < h):
                raise ValueError(f"lock outside image in {name}: {(x, y)}")


def ellipse_mask(shape: Tuple[int, int], spec: Dict[str, Any]) -> np.ndarray:
    h, w = shape
    mask = np.zeros((h, w), np.uint8)
    cx, cy = [int(round(v)) for v in spec["center"]]
    ax, ay = [int(round(v)) for v in spec["axes"]]
    angle = float(spec.get("angle", 0.0))
    cv2.ellipse(mask, (cx, cy), (ax, ay), angle, 0, 360, 255, -1, lineType=cv2.LINE_AA)
    return mask


def polygon_mask(shape: Tuple[int, int], spec: Dict[str, Any]) -> np.ndarray:
    h, w = shape
    mask = np.zeros((h, w), np.uint8)
    pts = np.asarray(spec["points"], dtype=np.int32).reshape((-1, 1, 2))
    cv2.fillPoly(mask, [pts], 255, lineType=cv2.LINE_AA)
    return mask


def build_mask(shape: Tuple[int, int], spec: Dict[str, Any]) -> np.ndarray:
    kind = spec["type"]
    if kind == "ellipse":
        mask = ellipse_mask(shape, spec)
    elif kind == "polygon":
        mask = polygon_mask(shape, spec)
    else:
        raise ValueError(f"Unsupported mask type: {kind}")

    feather = float(spec.get("feather_px", 0.0))
    if feather > 0:
        sigma = max(0.1, feather / 2.5)
        mask_f = cv2.GaussianBlur(
            mask.astype(np.float32) / 255.0,
            (0, 0),
            sigmaX=sigma,
            sigmaY=sigma,
        )
    else:
        mask_f = mask.astype(np.float32) / 255.0
    return np.clip(mask_f, 0.0, 1.0)


def solve_gaussian_rbf(
    control_xy: np.ndarray,
    displacement_xy: np.ndarray,
    sigma_px: float,
    regularization: float = 1e-6,
) -> Tuple[np.ndarray, np.ndarray]:
    c = control_xy.astype(np.float64)
    d = displacement_xy.astype(np.float64)
    diff = c[:, None, :] - c[None, :, :]
    r2 = np.sum(diff * diff, axis=2)
    K = np.exp(-r2 / (2.0 * sigma_px * sigma_px))
    K.flat[:: K.shape[0] + 1] += regularization
    ax = np.linalg.solve(K, d[:, 0])
    ay = np.linalg.solve(K, d[:, 1])
    return ax, ay


def rbf_displacement_field(
    h: int,
    w: int,
    control_xy: np.ndarray,
    ax: np.ndarray,
    ay: np.ndarray,
    sigma_px: float,
    bbox: Tuple[int, int, int, int],
) -> Tuple[np.ndarray, np.ndarray]:
    x0, y0, x1, y1 = bbox
    x0 = max(0, int(np.floor(x0)))
    y0 = max(0, int(np.floor(y0)))
    x1 = min(w, int(np.ceil(x1)))
    y1 = min(h, int(np.ceil(y1)))

    dx_full = np.zeros((h, w), np.float32)
    dy_full = np.zeros((h, w), np.float32)
    if x1 <= x0 or y1 <= y0:
        return dx_full, dy_full

    ys, xs = np.mgrid[y0:y1, x0:x1].astype(np.float64)
    dx = np.zeros_like(xs, dtype=np.float64)
    dy = np.zeros_like(xs, dtype=np.float64)
    denom = 2.0 * sigma_px * sigma_px
    for i, (cx, cy) in enumerate(control_xy):
        r2 = (xs - cx) ** 2 + (ys - cy) ** 2
        k = np.exp(-r2 / denom)
        dx += ax[i] * k
        dy += ay[i] * k

    dx_full[y0:y1, x0:x1] = dx.astype(np.float32)
    dy_full[y0:y1, x0:x1] = dy.astype(np.float32)
    return dx_full, dy_full


def region_bbox(mask: np.ndarray, pad: int) -> Tuple[int, int, int, int]:
    ys, xs = np.where(mask > 1e-5)
    if len(xs) == 0:
        return (0, 0, 0, 0)
    return (
        int(xs.min()) - pad,
        int(ys.min()) - pad,
        int(xs.max()) + 1 + pad,
        int(ys.max()) + 1 + pad,
    )


def apply_region_warp(
    image: np.ndarray,
    region: Dict[str, Any],
    amount: float,
) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    h, w = image.shape[:2]
    mask = build_mask((h, w), region["mask"])

    controls: List[List[float]] = []
    inverse_d: List[List[float]] = []
    for item in region.get("controls", []):
        x, y = [float(v) for v in item["xy"]]
        dx, dy = [float(v) * amount for v in item["delta_at_1"]]
        controls.append([x + dx, y + dy])
        inverse_d.append([-dx, -dy])
    for x, y in region.get("locks", []):
        controls.append([float(x), float(y)])
        inverse_d.append([0.0, 0.0])

    c = np.asarray(controls, np.float64)
    inv_d = np.asarray(inverse_d, np.float64)
    sigma = float(region.get("rbf_sigma_px", 42.0))
    reg = float(region.get("regularization", 1e-6))
    ax, ay = solve_gaussian_rbf(c, inv_d, sigma, reg)

    pad = int(max(16, sigma * 2.5))
    bbox = region_bbox(mask, pad)
    dx, dy = rbf_displacement_field(h, w, c, ax, ay, sigma, bbox)

    grid_y, grid_x = np.mgrid[0:h, 0:w].astype(np.float32)
    warped = cv2.remap(
        image,
        grid_x + dx,
        grid_y + dy,
        interpolation=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REFLECT_101,
    )

    a = mask[..., None].astype(np.float32)
    blended = image.astype(np.float32) * (1.0 - a) + warped.astype(np.float32) * a
    out = np.rint(np.clip(blended, 0, 255)).astype(np.uint8)
    outside = mask <= 1e-5
    out[outside] = image[outside]

    meta = {
        "name": region.get("name", "region"),
        "amount": float(amount),
        "sigma_px": sigma,
        "bbox": [int(v) for v in bbox],
        "controls": [
            {
                "source_xy": item["xy"],
                "forward_delta_px": [float(v) * amount for v in item["delta_at_1"]],
            }
            for item in region.get("controls", [])
        ],
    }
    return out, mask, meta


def diff_metrics(source: np.ndarray, frame: np.ndarray, editable_mask: np.ndarray) -> Dict[str, Any]:
    diff = cv2.absdiff(source, frame)
    diff_any = np.max(diff, axis=2)
    outside = editable_mask <= 1e-5
    inside = editable_mask > 1e-5
    outside_changed = int(np.count_nonzero(diff_any[outside]))
    outside_total = int(np.count_nonzero(outside))
    inside_changed = int(np.count_nonzero(diff_any[inside]))
    inside_total = int(np.count_nonzero(inside))
    return {
        "outside_changed_pixels": outside_changed,
        "outside_total_pixels": outside_total,
        "outside_exact_identity_ratio": 1.0 - (outside_changed / max(1, outside_total)),
        "inside_changed_pixels": inside_changed,
        "inside_total_pixels": inside_total,
        "max_channel_delta_outside": int(diff[outside].max()) if outside_total else 0,
        "max_channel_delta_inside": int(diff[inside].max()) if inside_total else 0,
        "mean_abs_delta_inside": float(diff[inside].mean()) if inside_total else 0.0,
    }


def pair_metrics(previous: np.ndarray, current: np.ndarray, editable_mask: np.ndarray) -> Dict[str, Any]:
    diff = cv2.absdiff(previous, current)
    inside = editable_mask > 1e-5
    diff_any = np.max(diff, axis=2)
    total = int(np.count_nonzero(inside))
    return {
        "changed_pixels_inside": int(np.count_nonzero(diff_any[inside])),
        "mean_abs_delta_inside": float(diff[inside].mean()) if total else 0.0,
        "max_channel_delta_inside": int(diff[inside].max()) if total else 0,
    }


def run(config_path: Path, source_override: Path | None, out_dir: Path) -> None:
    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    source_path = source_override or Path(cfg["source"]["path"])
    if not source_path.exists():
        raise FileNotFoundError(source_path)

    img = cv2.imread(str(source_path), cv2.IMREAD_COLOR)
    if img is None:
        raise RuntimeError(f"Cannot read image: {source_path}")

    h, w = img.shape[:2]
    expected_wh = cfg["source"].get("expected_size")
    if expected_wh and [w, h] != list(expected_wh):
        raise RuntimeError(f"Source size mismatch: got {(w, h)}, expected {tuple(expected_wh)}")

    source_sha = sha256_file(source_path)
    expected_sha = cfg["source"].get("sha256")
    if expected_sha and source_sha.lower() != expected_sha.lower():
        raise RuntimeError(f"Source SHA256 mismatch: {source_sha} != {expected_sha}")

    validate_config(cfg, w, h)
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_t_values = [float(v) for v in cfg["animation"]["t_values"]]
    ease_name = str(cfg["animation"].get("easing", "smootherstep"))

    region_masks = [build_mask((h, w), r["mask"]) for r in cfg["regions"]]
    global_mask = np.maximum.reduce(region_masks) if region_masks else np.zeros((h, w), np.float32)
    if region_masks:
        coverage_sum = np.sum(
            np.stack([(m > 1e-5).astype(np.uint8) for m in region_masks]), axis=0
        )
    else:
        coverage_sum = np.zeros((h, w), np.uint8)
    overlap_pixels = int(np.count_nonzero(coverage_sum > 1))

    manifest: Dict[str, Any] = {
        "engine": "ZORR deterministic local RBF face warp",
        "config_version": cfg.get("version"),
        "source": {"path": str(source_path), "size": [w, h], "sha256": source_sha},
        "easing": ease_name,
        "editable_mask_pixels": int(np.count_nonzero(global_mask > 1e-5)),
        "region_overlap_pixels": overlap_pixels,
        "frames": [],
    }

    previous = img.copy()
    for idx, raw_t in enumerate(raw_t_values):
        amount = easing(ease_name, raw_t)
        frame = img.copy()
        region_meta = []
        if amount > 0:
            for region in cfg["regions"]:
                frame, _mask, meta = apply_region_warp(frame, region, amount)
                region_meta.append(meta)

        outside = global_mask <= 1e-5
        frame[outside] = img[outside]

        name = f"frame_{idx:03d}.png"
        cv2.imwrite(str(out_dir / name), frame)
        manifest["frames"].append(
            {
                "frame": idx,
                "raw_t": raw_t,
                "eased_amount": amount,
                "file": name,
                "qc": diff_metrics(img, frame, global_mask),
                "vs_previous": pair_metrics(previous, frame, global_mask),
                "regions": region_meta,
            }
        )
        previous = frame

    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    failed = [f for f in manifest["frames"] if f["qc"]["outside_changed_pixels"] != 0]
    if failed:
        raise RuntimeError(f"QC FAILED: outside-mask pixels changed in {len(failed)} frame(s)")

    print(
        json.dumps(
            {
                "status": "PASS",
                "frames": len(manifest["frames"]),
                "source_size": [w, h],
                "source_sha256": source_sha,
                "manifest": str(manifest_path),
                "output_dir": str(out_dir),
            },
            indent=2,
        )
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, type=Path)
    ap.add_argument("--source", type=Path, default=None)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    run(args.config, args.source, args.out)


if __name__ == "__main__":
    main()
