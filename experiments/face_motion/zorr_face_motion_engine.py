#!/usr/bin/env python3
"""Deterministic pixel-preserving local face motion for stylized 2D art.

OSS runtime: NumPy + OpenCV + PyYAML.

Hard invariant: pixels outside explicitly editable masks are copied byte-for-byte
from the source raster. Every frame is computed from frame 0, never from the
previous rendered frame, so interpolation cannot accumulate identity drift.
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


def build_mask(shape: Tuple[int, int], spec: Dict[str, Any]) -> np.ndarray:
    h, w = shape
    raw = np.zeros((h, w), np.uint8)
    kind = spec["type"]
    if kind == "ellipse":
        cx, cy = [int(round(v)) for v in spec["center"]]
        ax, ay = [int(round(v)) for v in spec["axes"]]
        cv2.ellipse(
            raw,
            (cx, cy),
            (ax, ay),
            float(spec.get("angle", 0.0)),
            0,
            360,
            255,
            -1,
            lineType=cv2.LINE_AA,
        )
    elif kind == "polygon":
        pts = np.asarray(spec["points"], dtype=np.int32).reshape((-1, 1, 2))
        cv2.fillPoly(raw, [pts], 255, lineType=cv2.LINE_AA)
    else:
        raise ValueError(f"Unsupported mask type: {kind}")

    feather = float(spec.get("feather_px", 0.0))
    if feather <= 0:
        return raw.astype(np.float32) / 255.0
    sigma = max(0.1, feather / 2.5)
    mask = cv2.GaussianBlur(raw.astype(np.float32) / 255.0, (0, 0), sigmaX=sigma, sigmaY=sigma)
    return np.clip(mask, 0.0, 1.0)


def solve_gaussian_rbf(
    control_xy: np.ndarray,
    inverse_displacement_xy: np.ndarray,
    sigma_px: float,
    regularization: float,
) -> Tuple[np.ndarray, np.ndarray]:
    c = control_xy.astype(np.float64)
    d = inverse_displacement_xy.astype(np.float64)
    diff = c[:, None, :] - c[None, :, :]
    r2 = np.sum(diff * diff, axis=2)
    K = np.exp(-r2 / (2.0 * sigma_px * sigma_px))
    K.flat[:: K.shape[0] + 1] += regularization
    return np.linalg.solve(K, d[:, 0]), np.linalg.solve(K, d[:, 1])


def region_bbox(mask: np.ndarray, pad: int) -> Tuple[int, int, int, int]:
    ys, xs = np.where(mask > 1e-5)
    if len(xs) == 0:
        return 0, 0, 0, 0
    return (
        int(xs.min()) - pad,
        int(ys.min()) - pad,
        int(xs.max()) + 1 + pad,
        int(ys.max()) + 1 + pad,
    )


def evaluate_rbf_field(
    h: int,
    w: int,
    control_xy: np.ndarray,
    ax: np.ndarray,
    ay: np.ndarray,
    sigma_px: float,
    bbox: Tuple[int, int, int, int],
) -> Tuple[np.ndarray, np.ndarray]:
    x0, y0, x1, y1 = bbox
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(w, x1), min(h, y1)

    dx_full = np.zeros((h, w), np.float32)
    dy_full = np.zeros((h, w), np.float32)
    if x1 <= x0 or y1 <= y0:
        return dx_full, dy_full

    ys, xs = np.mgrid[y0:y1, x0:x1].astype(np.float64)
    dx = np.zeros_like(xs)
    dy = np.zeros_like(xs)
    denom = 2.0 * sigma_px * sigma_px
    for i, (cx, cy) in enumerate(control_xy):
        k = np.exp(-((xs - cx) ** 2 + (ys - cy) ** 2) / denom)
        dx += ax[i] * k
        dy += ay[i] * k

    dx_full[y0:y1, x0:x1] = dx.astype(np.float32)
    dy_full[y0:y1, x0:x1] = dy.astype(np.float32)
    return dx_full, dy_full


def apply_region_warp(
    image: np.ndarray,
    region: Dict[str, Any],
    amount: float,
) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    h, w = image.shape[:2]
    mask = build_mask((h, w), region["mask"])

    output_controls: List[List[float]] = []
    inverse_delta: List[List[float]] = []

    for item in region.get("controls", []):
        x, y = [float(v) for v in item["xy"]]
        dx, dy = [float(v) * amount for v in item["delta_at_1"]]
        # remap uses output -> source coordinates. A forward landmark move
        # (dx,dy) therefore becomes inverse displacement (-dx,-dy) at x+dx,y+dy.
        output_controls.append([x + dx, y + dy])
        inverse_delta.append([-dx, -dy])

    for x, y in region.get("locks", []):
        output_controls.append([float(x), float(y)])
        inverse_delta.append([0.0, 0.0])

    controls = np.asarray(output_controls, np.float64)
    inv_d = np.asarray(inverse_delta, np.float64)
    sigma = float(region.get("rbf_sigma_px", 42.0))
    reg = float(region.get("regularization", 1e-6))
    ax, ay = solve_gaussian_rbf(controls, inv_d, sigma, reg)

    pad = int(max(16, sigma * 2.5))
    bbox = region_bbox(mask, pad)
    dx, dy = evaluate_rbf_field(h, w, controls, ax, ay, sigma, bbox)

    grid_y, grid_x = np.mgrid[0:h, 0:w].astype(np.float32)
    warped = cv2.remap(
        image,
        grid_x + dx,
        grid_y + dy,
        interpolation=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REFLECT_101,
    )

    alpha = mask[..., None]
    blended = image.astype(np.float32) * (1.0 - alpha) + warped.astype(np.float32) * alpha
    out = np.rint(np.clip(blended, 0, 255)).astype(np.uint8)

    # Hard local identity invariant.
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
    inside_total = int(np.count_nonzero(inside))
    return {
        "outside_changed_pixels": outside_changed,
        "outside_total_pixels": outside_total,
        "outside_exact_identity_ratio": 1.0 - outside_changed / max(1, outside_total),
        "inside_changed_pixels": int(np.count_nonzero(diff_any[inside])),
        "inside_total_pixels": inside_total,
        "max_channel_delta_outside": int(diff[outside].max()) if outside_total else 0,
        "max_channel_delta_inside": int(diff[inside].max()) if inside_total else 0,
        "mean_abs_delta_inside": float(diff[inside].mean()) if inside_total else 0.0,
    }


def run(config_path: Path, source_override: Path | None, out_dir: Path) -> None:
    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    source_path = source_override or Path(cfg["source"]["path"])
    if not source_path.exists():
        raise FileNotFoundError(source_path)

    source = cv2.imread(str(source_path), cv2.IMREAD_COLOR)
    if source is None:
        raise RuntimeError(f"Cannot read source: {source_path}")
    h, w = source.shape[:2]

    expected_size = cfg["source"].get("expected_size")
    if expected_size and [w, h] != list(expected_size):
        raise RuntimeError(f"Source size mismatch: got {(w, h)}, expected {tuple(expected_size)}")

    source_sha = sha256_file(source_path)
    expected_sha = cfg["source"].get("sha256")
    if expected_sha and source_sha.lower() != expected_sha.lower():
        raise RuntimeError(f"Source SHA256 mismatch: {source_sha} != {expected_sha}")

    out_dir.mkdir(parents=True, exist_ok=True)
    raw_t_values = [float(v) for v in cfg["animation"]["t_values"]]
    ease_name = str(cfg["animation"].get("easing", "smootherstep"))

    manifest: Dict[str, Any] = {
        "engine": "ZORR deterministic local RBF face warp",
        "source": {"path": str(source_path), "size": [w, h], "sha256": source_sha},
        "easing": ease_name,
        "frames": [],
    }

    for idx, raw_t in enumerate(raw_t_values):
        amount = easing(ease_name, raw_t)
        frame = source.copy()
        union_mask = np.zeros((h, w), np.float32)
        region_meta = []

        if amount > 0:
            for region in cfg["regions"]:
                frame, mask, meta = apply_region_warp(frame, region, amount)
                union_mask = np.maximum(union_mask, mask)
                region_meta.append(meta)

        # Reassert identity lock after composing all regions.
        outside = union_mask <= 1e-5
        frame[outside] = source[outside]

        name = f"frame_{idx:03d}.png"
        cv2.imwrite(str(out_dir / name), frame)
        manifest["frames"].append(
            {
                "frame": idx,
                "raw_t": raw_t,
                "eased_amount": amount,
                "file": name,
                "qc": diff_metrics(source, frame, union_mask),
                "regions": region_meta,
            }
        )

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
