#!/usr/bin/env python3
"""ZORR deterministic 2D face-motion engine R03.

Purpose
-------
Create temporally controlled local deformations from ONE immutable source raster.
The engine is intentionally not a generative renderer.

Core invariants
---------------
1. Every frame is sampled from frame 0, never from the previous output frame.
2. Pixels outside the explicit hard editable mask are copied byte-for-byte.
3. All region vector fields are composed before one remap, so region order cannot
   change the result.
4. Source size/hash, config hash, dependency versions and QC metrics are recorded.
5. CPU/OpenCL settings are pinned for reproducibility-oriented execution.

OSS runtime: Python + NumPy + OpenCV + PyYAML.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import cv2
import numpy as np
import yaml

ENGINE_VERSION = "2.1.0"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def smootherstep(t: float) -> float:
    t = float(np.clip(t, 0.0, 1.0))
    return t**3 * (t * (t * 6.0 - 15.0) + 10.0)


def smoothstep(t: float) -> float:
    t = float(np.clip(t, 0.0, 1.0))
    return t * t * (3.0 - 2.0 * t)


def easing(name: str, t: float) -> float:
    if name == "linear":
        return float(np.clip(t, 0.0, 1.0))
    if name == "smoothstep":
        return smoothstep(t)
    if name == "smootherstep":
        return smootherstep(t)
    raise ValueError(f"Unknown easing: {name}")


def _require(cond: bool, message: str) -> None:
    if not cond:
        raise ValueError(message)


def validate_config(cfg: Dict[str, Any]) -> None:
    _require(isinstance(cfg, dict), "Config must be a mapping")
    _require("source" in cfg and "animation" in cfg and "regions" in cfg, "Missing source/animation/regions")
    src = cfg["source"]
    anim = cfg["animation"]
    _require(isinstance(src.get("expected_size"), list) and len(src["expected_size"]) == 2, "source.expected_size must be [W,H]")
    w, h = [int(v) for v in src["expected_size"]]
    _require(w > 0 and h > 0, "Invalid expected size")
    t_values = anim.get("t_values")
    _require(isinstance(t_values, list) and len(t_values) >= 2, "animation.t_values needs >=2 values")
    t = [float(v) for v in t_values]
    _require(all(0.0 <= v <= 1.0 for v in t), "t_values must be within [0,1]")
    _require(all(b > a for a, b in zip(t, t[1:])), "t_values must be strictly increasing")
    _ = easing(str(anim.get("easing", "smootherstep")), 0.5)
    render = cfg.get("render", {})
    _require(str(render.get("interpolation", "cubic")) in {"nearest", "linear", "cubic"}, "render.interpolation must be nearest/linear/cubic")
    qc = cfg.get("qc", {})
    max_disp = float(qc.get("max_displacement_px", 24.0))
    _require(max_disp > 0.0, "qc.max_displacement_px must be > 0")
    _require(float(qc.get("min_line_energy_ratio_inside", 0.0)) >= 0.0, "qc.min_line_energy_ratio_inside must be >=0")
    min_j = float(qc.get("min_jacobian_det", 0.05))
    max_j = float(qc.get("max_jacobian_det", 4.0))
    _require(0.0 < min_j < max_j, "qc Jacobian bounds invalid")
    _require(float(qc.get("max_control_step_px", 1e9)) > 0.0, "qc.max_control_step_px must be >0")
    _require(float(qc.get("max_control_accel_px", 1e9)) > 0.0, "qc.max_control_accel_px must be >0")

    names = set()
    for ri, region in enumerate(cfg["regions"]):
        name = str(region.get("name", f"region_{ri}"))
        _require(name not in names, f"Duplicate region name: {name}")
        names.add(name)
        _require(region.get("blend_mode", "weighted_average") in {"weighted_average"}, "Unsupported blend_mode")
        _require(float(region.get("rbf_sigma_px", 0)) > 0, f"{name}: rbf_sigma_px must be >0")
        mask = region.get("mask", {})
        _require(mask.get("type") in {"ellipse", "polygon"}, f"{name}: unsupported mask type")
        _require(float(mask.get("feather_inward_px", 0.0)) >= 0, f"{name}: feather_inward_px must be >=0")
        controls = region.get("controls", [])
        locks = region.get("locks", [])
        _require(len(controls) + len(locks) >= 3, f"{name}: need at least 3 total control/lock points")
        for c in controls:
            _require(len(c.get("xy", [])) == 2 and len(c.get("delta_at_1", [])) == 2, f"{name}: invalid control")
            x, y = [float(v) for v in c["xy"]]
            dx, dy = [float(v) for v in c["delta_at_1"]]
            _require(0 <= x < w and 0 <= y < h, f"{name}: control out of bounds")
            _require(math.hypot(dx, dy) <= max_disp, f"{name}: control displacement exceeds max_displacement_px")
        for p in locks:
            _require(len(p) == 2, f"{name}: invalid lock")
            x, y = [float(v) for v in p]
            _require(0 <= x < w and 0 <= y < h, f"{name}: lock out of bounds")


def build_hard_and_alpha_masks(shape: Tuple[int, int], spec: Dict[str, Any]) -> Tuple[np.ndarray, np.ndarray]:
    """Return (hard editable mask bool, inward-feather alpha float32).

    Feathering is strictly INSIDE the hard editable envelope. This avoids the
    common bug where a Gaussian feather silently expands the editable region.
    """
    h, w = shape
    hard_u8 = np.zeros((h, w), np.uint8)
    kind = spec["type"]
    if kind == "ellipse":
        cx, cy = [int(round(v)) for v in spec["center"]]
        ax, ay = [int(round(v)) for v in spec["axes"]]
        _require(ax > 0 and ay > 0, "Ellipse axes must be >0")
        cv2.ellipse(hard_u8, (cx, cy), (ax, ay), float(spec.get("angle", 0.0)), 0, 360, 255, -1, lineType=cv2.LINE_8)
    elif kind == "polygon":
        pts = np.asarray(spec["points"], dtype=np.int32).reshape((-1, 1, 2))
        _require(len(pts) >= 3, "Polygon needs >=3 points")
        cv2.fillPoly(hard_u8, [pts], 255, lineType=cv2.LINE_8)
    else:
        raise ValueError(f"Unsupported mask type: {kind}")

    hard = hard_u8 > 0
    feather = float(spec.get("feather_inward_px", 0.0))
    if feather <= 0:
        return hard, hard.astype(np.float32)

    dist = cv2.distanceTransform(hard_u8, cv2.DIST_L2, 5).astype(np.float32)
    alpha = np.clip(dist / max(feather, 1e-6), 0.0, 1.0)
    alpha[~hard] = 0.0
    return hard, alpha


def solve_gaussian_rbf(control_xy: np.ndarray, inverse_displacement_xy: np.ndarray, sigma_px: float, regularization: float) -> Tuple[np.ndarray, np.ndarray]:
    c = control_xy.astype(np.float64)
    d = inverse_displacement_xy.astype(np.float64)
    diff = c[:, None, :] - c[None, :, :]
    r2 = np.sum(diff * diff, axis=2)
    K = np.exp(-r2 / (2.0 * sigma_px * sigma_px))
    K.flat[:: K.shape[0] + 1] += regularization
    return np.linalg.solve(K, d[:, 0]), np.linalg.solve(K, d[:, 1])


def bbox_from_hard_mask(hard: np.ndarray, pad: int) -> Tuple[int, int, int, int]:
    ys, xs = np.where(hard)
    if len(xs) == 0:
        return 0, 0, 0, 0
    h, w = hard.shape
    return max(0, int(xs.min()) - pad), max(0, int(ys.min()) - pad), min(w, int(xs.max()) + 1 + pad), min(h, int(ys.max()) + 1 + pad)


def evaluate_rbf_field(shape: Tuple[int, int], controls: np.ndarray, ax: np.ndarray, ay: np.ndarray, sigma_px: float, bbox: Tuple[int, int, int, int]) -> Tuple[np.ndarray, np.ndarray]:
    h, w = shape
    x0, y0, x1, y1 = bbox
    dx_full = np.zeros((h, w), np.float32)
    dy_full = np.zeros((h, w), np.float32)
    if x1 <= x0 or y1 <= y0:
        return dx_full, dy_full
    ys, xs = np.mgrid[y0:y1, x0:x1].astype(np.float64)
    dx = np.zeros_like(xs)
    dy = np.zeros_like(xs)
    denom = 2.0 * sigma_px * sigma_px
    for i, (cx, cy) in enumerate(controls):
        k = np.exp(-((xs - cx) ** 2 + (ys - cy) ** 2) / denom)
        dx += ax[i] * k
        dy += ay[i] * k
    dx_full[y0:y1, x0:x1] = dx.astype(np.float32)
    dy_full[y0:y1, x0:x1] = dy.astype(np.float32)
    return dx_full, dy_full


def region_inverse_field(shape: Tuple[int, int], region: Dict[str, Any], amount: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, Dict[str, Any]]:
    h, w = shape
    hard, alpha = build_hard_and_alpha_masks(shape, region["mask"])
    out_controls: List[List[float]] = []
    inv_delta: List[List[float]] = []
    controls_meta = []
    for ci, item in enumerate(region.get("controls", [])):
        x, y = [float(v) for v in item["xy"]]
        dx, dy = [float(v) * amount for v in item["delta_at_1"]]
        out_controls.append([x + dx, y + dy])
        inv_delta.append([-dx, -dy])
        controls_meta.append({"id": str(item.get("id", f"c{ci}")), "semantic": str(item.get("semantic", "unspecified")), "source_xy": [x, y], "forward_delta_px": [dx, dy]})
    for x, y in region.get("locks", []):
        out_controls.append([float(x), float(y)])
        inv_delta.append([0.0, 0.0])
    controls = np.asarray(out_controls, np.float64)
    inv_d = np.asarray(inv_delta, np.float64)
    sigma = float(region.get("rbf_sigma_px", 36.0))
    reg = float(region.get("regularization", 1e-6))
    ax, ay = solve_gaussian_rbf(controls, inv_d, sigma, reg)
    bbox = bbox_from_hard_mask(hard, int(max(8, sigma * 2.5)))
    dx, dy = evaluate_rbf_field((h, w), controls, ax, ay, sigma, bbox)
    dx[~hard] = 0.0
    dy[~hard] = 0.0
    meta = {"name": region["name"], "sigma_px": sigma, "bbox": list(bbox), "controls": controls_meta}
    return dx, dy, hard, alpha, meta


def compose_fields(shape: Tuple[int, int], regions: Iterable[Dict[str, Any]], amount: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, List[Dict[str, Any]]]:
    h, w = shape
    sum_dx = np.zeros((h, w), np.float64)
    sum_dy = np.zeros((h, w), np.float64)
    sum_w = np.zeros((h, w), np.float64)
    union_hard = np.zeros((h, w), bool)
    union_alpha = np.zeros((h, w), np.float32)
    meta: List[Dict[str, Any]] = []
    for region in regions:
        dx, dy, hard, alpha, rmeta = region_inverse_field(shape, region, amount)
        wgt = alpha.astype(np.float64)
        sum_dx += dx.astype(np.float64) * wgt
        sum_dy += dy.astype(np.float64) * wgt
        sum_w += wgt
        union_hard |= hard
        union_alpha = np.maximum(union_alpha, alpha)
        meta.append(rmeta)
    dx = np.zeros((h, w), np.float32)
    dy = np.zeros((h, w), np.float32)
    nz = sum_w > 1e-12
    dx[nz] = (sum_dx[nz] / sum_w[nz]).astype(np.float32)
    dy[nz] = (sum_dy[nz] / sum_w[nz]).astype(np.float32)
    dx[~union_hard] = 0.0
    dy[~union_hard] = 0.0
    return dx, dy, union_hard, union_alpha, meta


def render_from_source(source: np.ndarray, dx: np.ndarray, dy: np.ndarray, hard: np.ndarray, alpha: np.ndarray, interpolation: int) -> np.ndarray:
    h, w = source.shape[:2]
    gy, gx = np.mgrid[0:h, 0:w].astype(np.float32)
    warped = cv2.remap(source, gx + dx, gy + dy, interpolation=interpolation, borderMode=cv2.BORDER_REFLECT_101)
    a = alpha[..., None].astype(np.float32)
    out = np.rint(source.astype(np.float32) * (1.0 - a) + warped.astype(np.float32) * a).clip(0, 255).astype(np.uint8)
    out[~hard] = source[~hard]
    return out


def laplacian_energy(image: np.ndarray, mask: np.ndarray) -> float:
    if not np.any(mask):
        return 0.0
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    lap = cv2.Laplacian(gray, cv2.CV_32F, ksize=3)
    vals = lap[mask]
    return float(np.mean(vals * vals)) if vals.size else 0.0


def edge_density_ratio(source: np.ndarray, frame: np.ndarray, mask: np.ndarray) -> float:
    if not np.any(mask):
        return 1.0
    sg = cv2.cvtColor(source, cv2.COLOR_BGR2GRAY)
    fg = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    se = cv2.Canny(sg, 50, 150) > 0
    fe = cv2.Canny(fg, 50, 150) > 0
    s = int(np.count_nonzero(se & mask))
    f = int(np.count_nonzero(fe & mask))
    return float(f / s) if s else 1.0


def diff_metrics(source: np.ndarray, frame: np.ndarray, hard: np.ndarray, prev: np.ndarray | None = None) -> Dict[str, Any]:
    diff = cv2.absdiff(source, frame)
    diff_any = np.max(diff, axis=2)
    outside = ~hard
    inside = hard
    outside_changed = int(np.count_nonzero(diff_any[outside]))
    source_edge = laplacian_energy(source, inside)
    frame_edge = laplacian_energy(frame, inside)
    report: Dict[str, Any] = {
        "outside_changed_pixels": outside_changed,
        "outside_exact_identity_ratio": 1.0 if not np.any(outside) else 1.0 - outside_changed / int(np.count_nonzero(outside)),
        "inside_changed_pixels": int(np.count_nonzero(diff_any[inside])),
        "max_channel_delta_outside": int(diff[outside].max()) if np.any(outside) else 0,
        "max_channel_delta_inside": int(diff[inside].max()) if np.any(inside) else 0,
        "mean_abs_delta_inside": float(diff[inside].mean()) if np.any(inside) else 0.0,
        "line_energy_ratio_inside": frame_edge / source_edge if source_edge > 1e-12 else 1.0,
        "edge_density_ratio_inside": edge_density_ratio(source, frame, inside),
    }
    if prev is not None:
        pd = cv2.absdiff(prev, frame)
        pda = np.max(pd, axis=2)
        report["vs_previous"] = {"changed_pixels_inside": int(np.count_nonzero(pda[inside])), "mean_abs_delta_inside": float(pd[inside].mean()) if np.any(inside) else 0.0, "max_channel_delta_inside": int(pd[inside].max()) if np.any(inside) else 0}
    return report


def field_metrics(dx: np.ndarray, dy: np.ndarray, hard: np.ndarray) -> Dict[str, float]:
    vals = np.hypot(dx, dy)[hard]
    return {"max_inverse_displacement_px": float(vals.max()) if vals.size else 0.0, "mean_inverse_displacement_px": float(vals.mean()) if vals.size else 0.0, "p95_inverse_displacement_px": float(np.percentile(vals, 95)) if vals.size else 0.0}


def jacobian_metrics(dx: np.ndarray, dy: np.ndarray, hard: np.ndarray) -> Dict[str, float]:
    ddx_dy, ddx_dx = np.gradient(dx.astype(np.float64))
    ddy_dy, ddy_dx = np.gradient(dy.astype(np.float64))
    det = (1.0 + ddx_dx) * (1.0 + ddy_dy) - ddx_dy * ddy_dx
    interior = cv2.erode(hard.astype(np.uint8), np.ones((3, 3), np.uint8), iterations=1).astype(bool)
    vals = det[interior]
    if not vals.size:
        vals = det[hard]
    if not vals.size:
        return {"min_det": 1.0, "p01_det": 1.0, "median_det": 1.0, "p99_det": 1.0, "max_det": 1.0}
    return {"min_det": float(vals.min()), "p01_det": float(np.percentile(vals, 1)), "median_det": float(np.median(vals)), "p99_det": float(np.percentile(vals, 99)), "max_det": float(vals.max())}


def mask_overlap_report(shape: Tuple[int, int], regions: List[Dict[str, Any]]) -> Dict[str, Any]:
    masks = []
    for r in regions:
        hard, _ = build_hard_and_alpha_masks(shape, r["mask"])
        masks.append((r["name"], hard))
    pairs = []
    for i in range(len(masks)):
        for j in range(i + 1, len(masks)):
            ni, a = masks[i]
            nj, b = masks[j]
            inter = int(np.count_nonzero(a & b))
            if inter:
                union = int(np.count_nonzero(a | b))
                pairs.append({"a": ni, "b": nj, "intersection_px": inter, "iou": inter / max(1, union)})
    return {"pairs": pairs}


def trajectory_report(cfg: Dict[str, Any]) -> Dict[str, Any]:
    raw_t = np.asarray([float(v) for v in cfg["animation"]["t_values"]], np.float64)
    ename = str(cfg["animation"].get("easing", "smootherstep"))
    a = np.asarray([easing(ename, v) for v in raw_t], np.float64)
    controls = []
    for r in cfg["regions"]:
        for ci, c in enumerate(r.get("controls", [])):
            delta = np.asarray(c["delta_at_1"], np.float64)
            pos0 = np.asarray(c["xy"], np.float64)
            pos = pos0[None, :] + a[:, None] * delta[None, :]
            vel = np.diff(pos, axis=0)
            acc = np.diff(vel, axis=0)
            controls.append({"region": r["name"], "id": str(c.get("id", f"c{ci}")), "semantic": str(c.get("semantic", "unspecified")), "positions": pos.round(6).tolist(), "step_speed_px": np.linalg.norm(vel, axis=1).round(6).tolist(), "step_accel_px": np.linalg.norm(acc, axis=1).round(6).tolist()})
    return {"raw_t": raw_t.tolist(), "eased_t": a.tolist(), "controls": controls}


def trajectory_quality(traj: Dict[str, Any]) -> Dict[str, Any]:
    max_step = 0.0
    max_accel = 0.0
    worst_step = None
    worst_accel = None
    for c in traj["controls"]:
        speeds = [float(v) for v in c.get("step_speed_px", [])]
        accels = [float(v) for v in c.get("step_accel_px", [])]
        if speeds and max(speeds) > max_step:
            max_step = max(speeds)
            worst_step = {"region": c["region"], "id": c["id"]}
        if accels and max(accels) > max_accel:
            max_accel = max(accels)
            worst_accel = {"region": c["region"], "id": c["id"]}
    return {"max_control_step_px": max_step, "max_control_accel_px": max_accel, "worst_step_control": worst_step, "worst_accel_control": worst_accel}


def load_source_and_config(config_path: Path, source_override: Path | None) -> Tuple[Dict[str, Any], str, Path, np.ndarray, str]:
    text = config_path.read_text(encoding="utf-8")
    cfg = yaml.safe_load(text)
    validate_config(cfg)
    source_path = source_override or Path(cfg["source"]["path"])
    if not source_path.exists():
        raise FileNotFoundError(source_path)
    source = cv2.imread(str(source_path), cv2.IMREAD_COLOR)
    if source is None:
        raise RuntimeError(f"Cannot read source: {source_path}")
    h, w = source.shape[:2]
    if [w, h] != [int(v) for v in cfg["source"]["expected_size"]]:
        raise RuntimeError(f"Source size mismatch: got {[w,h]}, expected {cfg['source']['expected_size']}")
    source_sha = sha256_file(source_path)
    expected_sha = str(cfg["source"].get("sha256", "")).lower().strip()
    if expected_sha and source_sha.lower() != expected_sha:
        raise RuntimeError(f"Source SHA256 mismatch: {source_sha} != {expected_sha}")
    return cfg, text, source_path, source, source_sha


def runtime_metadata() -> Dict[str, Any]:
    return {"engine_version": ENGINE_VERSION, "python": platform.python_version(), "numpy": np.__version__, "opencv": cv2.__version__, "opencl_enabled": bool(cv2.ocl.useOpenCL()), "opencv_threads": int(cv2.getNumThreads())}


def run(config_path: Path, source_override: Path | None, out_dir: Path | None, validate_only: bool) -> Dict[str, Any]:
    cv2.ocl.setUseOpenCL(False)
    cv2.setNumThreads(1)
    cfg, cfg_text, source_path, source, source_sha = load_source_and_config(config_path, source_override)
    h, w = source.shape[:2]
    overlap = mask_overlap_report((h, w), cfg["regions"])
    traj = trajectory_report(cfg)
    traj_qc = trajectory_quality(traj)
    qc_cfg = cfg.get("qc", {})
    if traj_qc["max_control_step_px"] > float(qc_cfg.get("max_control_step_px", 1e9)) + 1e-9:
        raise RuntimeError(f"QC FAILED: control step {traj_qc['max_control_step_px']:.3f}px exceeds limit")
    if traj_qc["max_control_accel_px"] > float(qc_cfg.get("max_control_accel_px", 1e9)) + 1e-9:
        raise RuntimeError(f"QC FAILED: control acceleration {traj_qc['max_control_accel_px']:.3f}px exceeds limit")
    base = {"status": "VALID" if validate_only else "PASS", "runtime": runtime_metadata(), "source": {"path": str(source_path), "size": [w, h], "sha256": source_sha}, "config": {"path": str(config_path), "sha256": sha256_text(cfg_text)}, "mask_overlap": overlap, "trajectory": traj, "trajectory_qc": traj_qc}
    if validate_only:
        return base
    _require(out_dir is not None, "--out is required unless --validate-only")
    out_dir.mkdir(parents=True, exist_ok=True)
    t_values = [float(v) for v in cfg["animation"]["t_values"]]
    ease_name = str(cfg["animation"].get("easing", "smootherstep"))
    interpolation_name = str(cfg.get("render", {}).get("interpolation", "cubic"))
    interp = {"nearest": cv2.INTER_NEAREST, "linear": cv2.INTER_LINEAR, "cubic": cv2.INTER_CUBIC}[interpolation_name]
    max_allowed = float(qc_cfg.get("max_displacement_px", 24.0))
    min_edge_ratio = float(qc_cfg.get("min_line_energy_ratio_inside", 0.80))
    min_jac = float(qc_cfg.get("min_jacobian_det", 0.15))
    max_jac = float(qc_cfg.get("max_jacobian_det", 2.5))
    manifest = dict(base)
    manifest["frames"] = []
    prev = None
    for idx, raw_t in enumerate(t_values):
        amount = easing(ease_name, raw_t)
        dx, dy, hard, alpha, rmeta = compose_fields((h, w), cfg["regions"], amount)
        fm = field_metrics(dx, dy, hard)
        jm = jacobian_metrics(dx, dy, hard)
        if fm["max_inverse_displacement_px"] > max_allowed + 1e-6:
            raise RuntimeError(f"QC FAILED: field displacement {fm['max_inverse_displacement_px']:.3f}px > {max_allowed}px")
        if jm["min_det"] <= min_jac:
            raise RuntimeError(f"QC FAILED: Jacobian min {jm['min_det']:.4f} <= {min_jac}")
        if jm["max_det"] >= max_jac:
            raise RuntimeError(f"QC FAILED: Jacobian max {jm['max_det']:.4f} >= {max_jac}")
        frame = render_from_source(source, dx, dy, hard, alpha, interp)
        qc = diff_metrics(source, frame, hard, prev)
        if qc["outside_changed_pixels"] != 0:
            raise RuntimeError(f"QC FAILED: exterior changed at frame {idx}")
        if idx > 0 and qc["line_energy_ratio_inside"] < min_edge_ratio:
            raise RuntimeError(f"QC FAILED: line-energy ratio too low at frame {idx}: {qc['line_energy_ratio_inside']:.3f}")
        name = f"frame_{idx:03d}.png"
        cv2.imwrite(str(out_dir / name), frame)
        manifest["frames"].append({"frame": idx, "raw_t": raw_t, "eased_amount": amount, "file": name, "field": fm, "jacobian": jm, "qc": qc, "regions": rmeta})
        prev = frame
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, type=Path)
    ap.add_argument("--source", type=Path, default=None)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--validate-only", action="store_true")
    args = ap.parse_args()
    result = run(args.config, args.source, args.out, args.validate_only)
    print(json.dumps({"status": result["status"], "engine_version": result["runtime"]["engine_version"], "source_size": result["source"]["size"], "source_sha256": result["source"]["sha256"], "config_sha256": result["config"]["sha256"], "overlap_pairs": len(result["mask_overlap"]["pairs"]), "frames": len(result.get("frames", []))}, indent=2))


if __name__ == "__main__":
    main()
