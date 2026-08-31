"""ZORR Babylon Camera Solver Proof R03.

Research-only deterministic proof harness for tracker #222.
No production thresholds are introduced here.

The mathematical solver is independent from Babylon's runtime implementation, but
all terminal runtime claims are fail-closed: Babylon native agreement is only PASS
when the companion Node harness actually executes and its JSON result is supplied.
"""
from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import numpy as np
import cv2
from numpy.linalg import norm
from scipy.linalg import null_space
from scipy.optimize import least_squares, root_scalar

EPS = 1e-12


@dataclass(frozen=True)
class CameraSpec:
    width: int
    height: int
    target: np.ndarray


def normalize(v: np.ndarray) -> np.ndarray:
    v = np.asarray(v, dtype=float)
    n = norm(v)
    if n <= EPS:
        raise ValueError("zero vector")
    return v / n


def wrap_angle(x: float) -> float:
    return (x + math.pi) % (2.0 * math.pi) - math.pi


def arc_position(alpha: float, beta: float, radius: float, target: np.ndarray) -> np.ndarray:
    """Babylon ArcRotate default-Y-up camera-center formula."""
    sa, ca = math.sin(alpha), math.cos(alpha)
    sb, cb = math.sin(beta), math.cos(beta)
    q = radius * np.array([ca * sb, cb, sa * sb], dtype=float)
    return np.asarray(target, dtype=float) + q


def arc_position_jacobian(alpha: float, beta: float, rho: float) -> np.ndarray:
    """dC / d[alpha,beta,rho,Tx,Ty,Tz], with radius=exp(rho)."""
    r = math.exp(rho)
    sa, ca = math.sin(alpha), math.cos(alpha)
    sb, cb = math.sin(beta), math.cos(beta)
    d_alpha = r * np.array([-sa * sb, 0.0, ca * sb])
    d_beta = r * np.array([ca * cb, -sb, sa * cb])
    d_rho = r * np.array([ca * sb, cb, sa * sb])
    return np.column_stack([d_alpha, d_beta, d_rho, np.eye(3)])


def look_at_lh(camera_center: np.ndarray, target: np.ndarray, up=(0.0, 1.0, 0.0)) -> tuple[np.ndarray, np.ndarray]:
    """World->camera rotation for +Z-forward, +Y-up camera coordinates."""
    C = np.asarray(camera_center, dtype=float)
    T = np.asarray(target, dtype=float)
    fwd = normalize(T - C)
    right = normalize(np.cross(np.asarray(up, dtype=float), fwd))
    cam_up = normalize(np.cross(fwd, right))
    R = np.vstack([right, cam_up, fwd])
    t = -R @ C
    return R, t


def focal_from_vertical_fov(height_px: int, fov: float) -> float:
    return float(height_px) / (2.0 * math.tan(float(fov) / 2.0))


def project_camera_points(points_camera: np.ndarray, width: int, height: int, fov: float) -> np.ndarray:
    X = np.atleast_2d(np.asarray(points_camera, dtype=float))
    if np.any(X[:, 2] <= 0):
        raise ValueError("point behind camera")
    f = focal_from_vertical_fov(height, fov)
    cx = width / 2.0
    cy = height / 2.0
    u = cx + f * X[:, 0] / X[:, 2]
    v = cy - f * X[:, 1] / X[:, 2]
    return np.column_stack([u, v])


def project_world(points_world: np.ndarray, theta: np.ndarray, spec: CameraSpec) -> np.ndarray:
    alpha, beta, rho, fov = map(float, theta)
    r = math.exp(rho)
    C = arc_position(alpha, beta, r, spec.target)
    R, t = look_at_lh(C, spec.target)
    X = np.atleast_2d(np.asarray(points_world, dtype=float))
    Xc = (R @ X.T + t[:, None]).T
    return project_camera_points(Xc, spec.width, spec.height, fov)


def projection_jacobian_camera_point(Xc: np.ndarray, width: int, height: int, fov: float) -> np.ndarray:
    X, Y, Z = map(float, Xc)
    f = focal_from_vertical_fov(height, fov)
    return np.array(
        [
            [f / Z, 0.0, -f * X / (Z * Z)],
            [0.0, -f / Z, f * Y / (Z * Z)],
        ],
        dtype=float,
    )


def finite_difference_jacobian(fun: Callable[[np.ndarray], np.ndarray], x: np.ndarray, eps: float = 1e-6) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    y0 = np.asarray(fun(x), dtype=float).reshape(-1)
    J = np.zeros((y0.size, x.size), dtype=float)
    for j in range(x.size):
        h = eps * max(1.0, abs(x[j]))
        xp = x.copy(); xp[j] += h
        xm = x.copy(); xm[j] -= h
        yp = np.asarray(fun(xp), dtype=float).reshape(-1)
        ym = np.asarray(fun(xm), dtype=float).reshape(-1)
        J[:, j] = (yp - ym) / (2.0 * h)
    return J


def normalized_screen_residual(theta: np.ndarray, points_world: np.ndarray, targets_px: np.ndarray, spec: CameraSpec) -> np.ndarray:
    uv = project_world(points_world, theta, spec)
    d = uv - np.asarray(targets_px, dtype=float)
    d[:, 0] /= spec.width
    d[:, 1] /= spec.height
    return d.reshape(-1)


def recover_arc_camera(points_world: np.ndarray, targets_px: np.ndarray, spec: CameraSpec, seed: np.ndarray) -> dict[str, Any]:
    lower = np.array([-math.pi, 0.08, math.log(0.75), 0.25])
    upper = np.array([3.0 * math.pi, math.pi - 0.08, math.log(80.0), 1.55])
    sol = least_squares(
        normalized_screen_residual,
        np.asarray(seed, dtype=float),
        bounds=(lower, upper),
        args=(points_world, targets_px, spec),
        method="trf",
        x_scale="jac",
        ftol=1e-13,
        xtol=1e-13,
        gtol=1e-13,
        max_nfev=4000,
    )
    pred = project_world(points_world, sol.x, spec)
    err = norm(pred - targets_px, axis=1)
    return {
        "theta": sol.x,
        "success": bool(sol.success),
        "cost": float(sol.cost),
        "nfev": int(sol.nfev),
        "rmse_px": float(np.sqrt(np.mean(err**2))),
        "max_px": float(np.max(err)),
        "optimality": float(sol.optimality),
    }


def synthetic_scene_a() -> tuple[CameraSpec, np.ndarray, np.ndarray]:
    spec = CameraSpec(1920, 1080, np.array([0.35, 1.15, 5.4], dtype=float))
    theta = np.array([1.08, 1.19, math.log(8.6), 0.82], dtype=float)
    pts = np.array(
        [
            [-2.0, 0.0, 4.0], [-1.2, 1.7, 4.8], [0.1, 0.4, 5.0], [1.8, 0.0, 5.6],
            [-1.5, 2.7, 6.0], [0.8, 2.2, 6.5], [2.4, 1.0, 7.1], [-0.3, 3.1, 7.8],
            [1.1, 0.2, 8.5], [-2.2, 1.1, 8.9], [0.5, 1.6, 9.4], [2.0, 2.8, 10.0],
        ],
        dtype=float,
    )
    return spec, theta, pts


def synthetic_scene_b() -> tuple[CameraSpec, np.ndarray, np.ndarray]:
    spec = CameraSpec(1600, 900, np.array([-1.1, 0.8, 8.2], dtype=float))
    theta = np.array([2.18, 1.02, math.log(11.7), 0.69], dtype=float)
    pts = np.array(
        [
            [-4.0, 0.0, 6.0], [-2.7, 1.2, 7.1], [-1.0, 2.8, 7.8], [1.1, 0.0, 8.0],
            [2.2, 1.9, 9.2], [-3.1, 3.4, 9.8], [0.0, 1.0, 10.4], [3.3, 0.4, 11.2],
            [-1.8, 2.0, 12.0], [1.5, 3.2, 12.8], [2.8, 1.4, 13.6], [-0.4, 0.2, 14.1],
        ],
        dtype=float,
    )
    return spec, theta, pts



def case_known_general_camera_recovery_pnp() -> dict[str, Any]:
    """Recover a general calibrated pinhole camera using mature OpenCV PnP.

    This is intentionally not a custom ZORR PnP implementation. The synthetic
    convention here is OpenCV's calibrated pinhole convention and is kept
    separate from the Babylon ArcRotate proof below.
    """
    W, H = 1920, 1080
    f = 1180.0
    K = np.array([[f, 0.0, W / 2.0], [0.0, f, H / 2.0], [0.0, 0.0, 1.0]], dtype=np.float64)
    obj = np.array([
        [-1.4, -0.6, -0.2], [-0.7, 0.9, 0.5], [0.3, -0.8, 1.1],
        [1.2, 0.4, -0.4], [1.6, 1.1, 0.8], [-1.1, 1.4, 1.6],
        [0.6, 1.7, 2.0], [1.8, -0.5, 1.7], [-0.2, 0.2, 2.7],
        [-1.7, 0.5, 2.2], [0.9, -1.2, 2.4], [1.3, 1.5, 3.0],
    ], dtype=np.float64)
    rvec_true = np.array([[0.13], [-0.22], [0.07]], dtype=np.float64)
    tvec_true = np.array([[0.38], [-0.27], [7.4]], dtype=np.float64)
    img, _ = cv2.projectPoints(obj, rvec_true, tvec_true, K, None)
    img = img.reshape(-1, 2)

    ok, rvec, tvec = cv2.solvePnP(obj, img, K, None, flags=cv2.SOLVEPNP_SQPNP)
    if not ok:
        return {"solver": "OpenCV solvePnP SQPnP", "pass": False, "reason": "solvePnP returned false"}
    rvec, tvec = cv2.solvePnPRefineLM(obj, img, K, None, rvec, tvec)
    reproj, _ = cv2.projectPoints(obj, rvec, tvec, K, None)
    reproj = reproj.reshape(-1, 2)
    reproj_err = norm(reproj - img, axis=1)

    R_true, _ = cv2.Rodrigues(rvec_true)
    R_est, _ = cv2.Rodrigues(rvec)
    R_delta = R_est @ R_true.T
    angle = math.acos(float(np.clip((np.trace(R_delta) - 1.0) / 2.0, -1.0, 1.0)))
    C_true = (-R_true.T @ tvec_true).ravel()
    C_est = (-R_est.T @ tvec).ravel()
    center_error = float(norm(C_est - C_true))

    return {
        "solver": "OpenCV solvePnP(SQPNP) + solvePnPRefineLM",
        "custom_pnp": False,
        "rotation_geodesic_error_rad": float(angle),
        "camera_center_error_world": center_error,
        "reprojection_rmse_px": float(np.sqrt(np.mean(reproj_err**2))),
        "reprojection_max_px": float(np.max(reproj_err)),
        "pass": bool(angle < 1e-9 and center_error < 1e-9 and float(np.max(reproj_err)) < 1e-8),
    }

def case_arc_camera_recovery(spec: CameraSpec, theta_true: np.ndarray, pts: np.ndarray) -> dict[str, Any]:
    target = project_world(pts, theta_true, spec)
    seed = theta_true + np.array([0.22, -0.16, math.log(1.22), 0.11])
    rec = recover_arc_camera(pts, target, spec, seed)
    delta = rec["theta"] - theta_true
    delta[0] = wrap_angle(delta[0])
    return {
        "true_theta": theta_true.tolist(),
        "seed_theta": seed.tolist(),
        "recovered_theta": rec["theta"].tolist(),
        "parameter_error": delta.tolist(),
        "rmse_px": rec["rmse_px"],
        "max_px": rec["max_px"],
        "success": rec["success"],
        "pass": bool(rec["success"] and rec["rmse_px"] < 1e-5),
    }


def case_formula_jacobians() -> dict[str, Any]:
    alpha, beta, rho = 1.31, 0.94, math.log(7.3)
    target = np.array([0.4, -0.2, 5.0])
    x = np.r_[alpha, beta, rho, target]

    def f_arc(z: np.ndarray) -> np.ndarray:
        a, b, rr = z[:3]
        T = z[3:]
        return arc_position(a, b, math.exp(rr), T)

    J_a = arc_position_jacobian(alpha, beta, rho)
    J_fd = finite_difference_jacobian(f_arc, x, 1e-6)
    arc_abs = float(np.max(np.abs(J_a - J_fd)))
    arc_rel = float(norm(J_a - J_fd) / max(norm(J_fd), EPS))

    Xc = np.array([1.2, -0.7, 6.8])
    W, H, fov = 1920, 1080, 0.78
    Jp = projection_jacobian_camera_point(Xc, W, H, fov)
    Jp_fd = finite_difference_jacobian(lambda q: project_camera_points(q[None, :], W, H, fov)[0], Xc, 1e-6)
    proj_abs = float(np.max(np.abs(Jp - Jp_fd)))
    proj_rel = float(norm(Jp - Jp_fd) / max(norm(Jp_fd), EPS))

    return {
        "arc_position_max_abs": arc_abs,
        "arc_position_relative": arc_rel,
        "projection_max_abs": proj_abs,
        "projection_relative": proj_rel,
        "pass": bool(arc_rel < 1e-8 and proj_rel < 1e-8),
    }


def case_projected_height_exact_solve() -> dict[str, Any]:
    spec = CameraSpec(1920, 1080, np.array([0.0, 1.0, 6.0]))
    alpha, beta, fov = 1.37, 1.10, 0.76
    point_bottom = np.array([0.5, 0.0, 7.0])
    point_top = np.array([0.5, 2.15, 7.0])
    pts = np.vstack([point_bottom, point_top])
    true_radius = 9.4
    theta_true = np.array([alpha, beta, math.log(true_radius), fov])
    uv = project_world(pts, theta_true, spec)
    h_target = float(norm(uv[1] - uv[0]))

    def F(r: float) -> float:
        th = np.array([alpha, beta, math.log(r), fov])
        p = project_world(pts, th, spec)
        return float(norm(p[1] - p[0]) - h_target)

    grid = np.geomspace(2.0, 40.0, 120)
    vals = [F(float(r)) for r in grid]
    bracket = None
    for a, b, fa, fb in zip(grid[:-1], grid[1:], vals[:-1], vals[1:]):
        if fa == 0.0 or fa * fb <= 0.0:
            bracket = (float(a), float(b))
            break
    if bracket is None:
        return {"pass": False, "reason": "no root bracket"}
    sol = root_scalar(F, bracket=bracket, xtol=1e-12, rtol=1e-12, method="brentq")
    return {
        "target_height_px": h_target,
        "true_radius": true_radius,
        "solved_radius": float(sol.root),
        "radius_error": float(sol.root - true_radius),
        "height_residual_px": float(F(sol.root)),
        "pass": bool(sol.converged and abs(sol.root - true_radius) < 1e-8),
    }


def screen_jacobian_theta(point_world: np.ndarray, theta: np.ndarray, spec: CameraSpec) -> np.ndarray:
    return finite_difference_jacobian(lambda th: project_world(point_world[None, :], th, spec)[0], theta, 2e-6)


def case_rank_and_anchor_selection(spec: CameraSpec, theta: np.ndarray, pts: np.ndarray) -> dict[str, Any]:
    base = pts[2]
    J0 = screen_jacobian_theta(base, theta, spec)
    U, s, Vt = np.linalg.svd(J0, full_matrices=True)
    tol = max(J0.shape) * np.finfo(float).eps * s[0]
    rank = int(np.sum(s > tol))
    weak = Vt[-1]

    candidates = []
    for idx in [0, 1, 4, 6, 7, 10, 11]:
        Jm = screen_jacobian_theta(pts[idx], theta, spec)
        score_weak = float(norm(Jm @ weak))
        Jaug = np.vstack([J0, Jm])
        saug = np.linalg.svd(Jaug, compute_uv=False)
        min_sv = float(saug[-1])
        cond = float(saug[0] / max(saug[-1], EPS))
        candidates.append({"index": idx, "weak_score": score_weak, "min_singular": min_sv, "condition": cond})
    best_e = max(candidates, key=lambda x: x["min_singular"])
    best_weak = max(candidates, key=lambda x: x["weak_score"])
    return {
        "base_rank": rank,
        "parameter_dimension": int(theta.size),
        "base_singular_values": s.tolist(),
        "weak_direction": weak.tolist(),
        "candidate_scores": candidates,
        "e_optimal_selected_index": int(best_e["index"]),
        "e_optimal_selected_min_singular": best_e["min_singular"],
        "single_weak_direction_max_index": int(best_weak["index"]),
        "single_weak_direction_max_score": best_weak["weak_score"],
        "selection_rule": "E-optimal augmentation = maximize sigma_min(J_aug); weak-score is separately reported for |j_m v_weak| evidence",
        "pass": bool(rank < theta.size and best_e["min_singular"] > 1e-6 and best_weak["weak_score"] > 0.0),
    }


def case_nullspace_safe_edit(spec: CameraSpec, theta: np.ndarray, pts: np.ndarray) -> dict[str, Any]:
    p_protect = pts[2]
    p_secondary = pts[6]
    uv0 = project_world(np.vstack([p_protect, p_secondary]), theta, spec)
    Jp = screen_jacobian_theta(p_protect, theta, spec)
    N = null_space(Jp)
    Js = screen_jacobian_theta(p_secondary, theta, spec)[0:1, :]
    A = Js @ N
    desired_du = 2.0
    z = np.linalg.pinv(A) @ np.array([desired_du])
    delta = N @ z
    # Bound to a genuinely local edit if pseudoinverse produced a large parameter step.
    max_component = float(np.max(np.abs(delta)))
    if max_component > 0.025:
        delta *= 0.025 / max_component
    predicted_lock_motion = Jp @ delta
    predicted_secondary = float((Js @ delta)[0])
    uv1 = project_world(np.vstack([p_protect, p_secondary]), theta + delta, spec)
    actual_lock_drift = float(norm(uv1[0] - uv0[0]))
    actual_secondary_du = float(uv1[1, 0] - uv0[1, 0])
    return {
        "nullity": int(N.shape[1]),
        "delta_theta": delta.tolist(),
        "predicted_lock_motion_px": predicted_lock_motion.tolist(),
        "predicted_secondary_du_px": predicted_secondary,
        "actual_lock_drift_px": actual_lock_drift,
        "actual_secondary_du_px": actual_secondary_du,
        "pass": bool(N.shape[1] >= 1 and norm(predicted_lock_motion) < 1e-8 and abs(actual_secondary_du) > 0.2 and actual_lock_drift < 0.05),
    }


def case_active_constraint(theta: np.ndarray) -> dict[str, Any]:
    rho_min = float(theta[2])
    a = np.array([0.0, 0.0, -1.0, 0.0])  # g=rho_min-rho <= 0
    desired = np.array([0.012, -0.008, -0.10, 0.0])
    violation_direction = float(a @ desired)
    if violation_direction > 0:
        projected = desired - (violation_direction / float(a @ a)) * a
    else:
        projected = desired.copy()
    tangent_value = float(a @ projected)
    return {
        "constraint": "rho_min - rho <= 0",
        "desired_delta": desired.tolist(),
        "desired_linearized_g_change": violation_direction,
        "projected_delta": projected.tolist(),
        "projected_linearized_g_change": tangent_value,
        "pass": bool(violation_direction > 0 and tangent_value <= 1e-12 and projected[2] >= -1e-12),
    }


def case_uncertainty_monte_carlo(spec: CameraSpec, theta_true: np.ndarray, pts: np.ndarray, n: int = 80) -> dict[str, Any]:
    rng = np.random.default_rng(222_903)
    clean = project_world(pts, theta_true, spec)
    seed = theta_true + np.array([0.04, -0.035, 0.03, 0.025])
    params = []
    rmses = []
    failures = 0
    sigma_px = 0.75
    for _ in range(n):
        noisy = clean + rng.normal(0.0, sigma_px, clean.shape)
        rec = recover_arc_camera(pts, noisy, spec, seed)
        if not rec["success"]:
            failures += 1
            continue
        params.append(rec["theta"])
        rmses.append(rec["rmse_px"])
    P = np.asarray(params, dtype=float)
    if len(P) == 0:
        return {"pass": False, "reason": "all solves failed", "failures": failures}
    std = np.std(P, axis=0, ddof=1)
    err = P - theta_true
    err[:, 0] = np.vectorize(wrap_angle)(err[:, 0])
    rmse_param = np.sqrt(np.mean(err**2, axis=0))
    return {
        "trials": n,
        "successful": int(len(P)),
        "failures": failures,
        "input_pixel_sigma": sigma_px,
        "parameter_std": std.tolist(),
        "parameter_rmse": rmse_param.tolist(),
        "reprojection_rmse_px_median": float(np.median(rmses)),
        "reprojection_rmse_px_p95": float(np.quantile(rmses, 0.95)),
        "pass": bool(failures == 0 and np.all(np.isfinite(std))),
        "production_threshold": "UNKNOWN / QC_PENDING",
    }


def world_point_jacobian(point_world: np.ndarray, theta: np.ndarray, spec: CameraSpec) -> np.ndarray:
    return finite_difference_jacobian(lambda X: project_world(X[None, :], theta, spec)[0], point_world, 2e-6)


def case_moving_target_screen_lock(spec: CameraSpec, theta: np.ndarray, point: np.ndarray) -> dict[str, Any]:
    Xdot = np.array([0.55, 0.08, -0.12], dtype=float)
    Jt = screen_jacobian_theta(point, theta, spec)
    Jx = world_point_jacobian(point, theta, spec)
    rhs = -(Jx @ Xdot)
    lam = 1e-8
    theta_dot = np.linalg.solve(Jt.T @ Jt + lam * np.eye(theta.size), Jt.T @ rhs)
    static_vel = Jx @ Xdot
    compensated_vel = Jt @ theta_dot + static_vel
    dt = 1e-3
    p0 = project_world(point[None, :], theta, spec)[0]
    p_static = project_world((point + Xdot * dt)[None, :], theta, spec)[0]
    p_comp = project_world((point + Xdot * dt)[None, :], theta + theta_dot * dt, spec)[0]
    static_shift = float(norm(p_static - p0))
    comp_shift = float(norm(p_comp - p0))
    return {
        "world_velocity": Xdot.tolist(),
        "theta_dot": theta_dot.tolist(),
        "static_screen_velocity_px_s": static_vel.tolist(),
        "compensated_screen_velocity_px_s": compensated_vel.tolist(),
        "finite_dt_static_shift_px": static_shift,
        "finite_dt_compensated_shift_px": comp_shift,
        "pass": bool(norm(compensated_vel) < 1e-4 * max(norm(static_vel), EPS) and comp_shift < 0.02 * static_shift),
    }


def case_physical_style_separation(spec: CameraSpec, theta: np.ndarray, pts: np.ndarray) -> dict[str, Any]:
    physical = project_world(pts[:5], theta, spec)
    protected = physical.copy()
    style_target = physical.copy()
    style_target[0] += np.array([12.0, -5.0])
    # Low-dimensional style basis: only hero landmark gets declared x/y graphic offset.
    basis = np.zeros((physical.size, 2), dtype=float)
    basis[0, 0] = 1.0
    basis[1, 1] = 1.0
    residual = (style_target - physical).reshape(-1)
    coeff, *_ = np.linalg.lstsq(basis, residual, rcond=None)
    explained = basis @ coeff
    final_residual = residual - explained
    protected_residual = (protected[1:] - physical[1:]).reshape(-1)
    return {
        "style_coeff_px": coeff.tolist(),
        "declared_style_target_offset_px": [12.0, -5.0],
        "style_residual_after_basis_px_l2": float(norm(final_residual)),
        "physical_protected_residual_px_l2": float(norm(protected_residual)),
        "pass": bool(norm(final_residual) < 1e-10 and norm(protected_residual) < 1e-10),
    }


def ray_aabb_intersection(origin: np.ndarray, direction: np.ndarray, bmin: np.ndarray, bmax: np.ndarray) -> tuple[bool, float]:
    origin = np.asarray(origin, float)
    direction = np.asarray(direction, float)
    inv = np.where(np.abs(direction) > EPS, 1.0 / direction, np.inf)
    t1 = (bmin - origin) * inv
    t2 = (bmax - origin) * inv
    tmin = float(np.max(np.minimum(t1, t2)))
    tmax = float(np.min(np.maximum(t1, t2)))
    return bool(tmax >= max(0.0, tmin)), tmin


def case_occlusion_proxy(spec: CameraSpec, theta: np.ndarray, protected_point: np.ndarray) -> dict[str, Any]:
    alpha, beta, rho, _ = theta
    C = arc_position(alpha, beta, math.exp(rho), spec.target)
    to_p = protected_point - C
    dist = float(norm(to_p))
    d = to_p / dist
    center = C + 0.48 * to_p
    half = np.array([0.35, 0.55, 0.35])
    hit, t = ray_aabb_intersection(C, d, center - half, center + half)
    occluded = bool(hit and 0.0 <= t < dist)
    return {
        "smooth_proxy": "analytic ray-AABB only",
        "proxy_occluded": occluded,
        "proxy_hit_distance": float(t),
        "protected_distance": dist,
        "babylon_exact_required": True,
        "pass": bool(occluded),
        "terminal_exact_status": "NOT_PROVEN until Babylon pickWithRay harness runs",
    }


def native_payload(spec: CameraSpec, theta: np.ndarray, pts: np.ndarray, out_path: Path) -> None:
    alpha, beta, rho, fov = map(float, theta)
    radius = math.exp(rho)
    C = arc_position(alpha, beta, radius, spec.target)
    protected = np.asarray(pts, float)[2]
    occ_center = C + 0.48 * (protected - C)
    data = {
        "width": spec.width,
        "height": spec.height,
        "camera": {
            "alpha": alpha,
            "beta": beta,
            "radius": radius,
            "target": spec.target.tolist(),
            "fov": fov,
            "minZ": 0.1,
            "maxZ": 1000.0,
        },
        "points": np.asarray(pts, float).tolist(),
        "occlusion_case": {
            "box_center": occ_center.tolist(),
            "box_size": [0.7, 1.1, 0.7],
            "protected_point": protected.tolist(),
            "expected_occluded": True,
        },
        "frustum_case": {
            "box_center": protected.tolist(),
            "box_size": [0.35, 0.35, 0.35],
            "expected_in_frustum": True,
        },
    }
    out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def compare_native(native_json: Path | None, analytic_uv: np.ndarray, spec: CameraSpec, theta: np.ndarray) -> dict[str, Any]:
    if native_json is None or not native_json.exists():
        return {
            "status": "NOT_PROVEN",
            "reason": "Babylon 9.23.0 runtime result JSON was not supplied/executed in this environment",
        }
    data = json.loads(native_json.read_text(encoding="utf-8"))
    if not data.get("runtime_ok", False):
        return {"status": "FAIL", "native": data}
    native_uv = np.asarray(data["projected"], dtype=float)
    if native_uv.shape != analytic_uv.shape:
        return {"status": "FAIL", "reason": "shape mismatch", "native_shape": list(native_uv.shape), "analytic_shape": list(analytic_uv.shape)}
    e = norm(native_uv - analytic_uv, axis=1)
    alpha, beta, rho, _ = map(float, theta)
    expected_C = arc_position(alpha, beta, math.exp(rho), spec.target)
    native_C = np.asarray(data.get("camera", {}).get("native_global_position", [np.nan, np.nan, np.nan]), dtype=float)
    camera_position_delta = float(norm(native_C - expected_C))
    unproject_max = data.get("unproject_roundtrip_max")
    unproject_gate = unproject_max is not None and float(unproject_max) < 1e-8
    occ = data.get("occlusion") or {}
    occ_gate = bool(occ.get("requested") and occ.get("occluded_before_protected_point"))
    fr = data.get("frustum") or {}
    frustum_gate = bool(fr.get("requested") and fr.get("exact_babylon_in_frustum"))
    gates = {
        "reprojection_max_lt_1e-6_px": float(np.max(e)) < 1e-6,
        "arc_camera_position_lt_1e-9_world": camera_position_delta < 1e-9,
        "unproject_roundtrip_lt_1e-8_world": unproject_gate,
        "exact_pick_occlusion": occ_gate,
        "exact_frustum_inclusion": frustum_gate,
        "engine_version_is_9_23_0": data.get("engine_version") == "9.23.0",
    }
    return {
        "status": "PASS" if all(gates.values()) else "FAIL",
        "gates": gates,
        "max_reprojection_delta_px": float(np.max(e)),
        "rmse_reprojection_delta_px": float(np.sqrt(np.mean(e**2))),
        "arc_camera_position_delta_world": camera_position_delta,
        "unproject_roundtrip_max": unproject_max,
        "occlusion": occ,
        "frustum": fr,
        "engine_version": data.get("engine_version"),
    }


def build_report(native_result_path: Path | None = None) -> dict[str, Any]:
    spec_a, theta_a, pts_a = synthetic_scene_a()
    spec_b, theta_b, pts_b = synthetic_scene_b()

    formula = case_formula_jacobians()
    general_recovery = case_known_general_camera_recovery_pnp()
    recovery_a = case_arc_camera_recovery(spec_a, theta_a, pts_a)
    height = case_projected_height_exact_solve()
    rank_anchor = case_rank_and_anchor_selection(spec_a, theta_a, pts_a)
    null_edit = case_nullspace_safe_edit(spec_a, theta_a, pts_a)
    active = case_active_constraint(theta_a)
    uncertainty = case_uncertainty_monte_carlo(spec_a, theta_a, pts_a)
    recovery_b = case_arc_camera_recovery(spec_b, theta_b, pts_b)
    moving = case_moving_target_screen_lock(spec_a, theta_a, pts_a[2])
    style = case_physical_style_separation(spec_a, theta_a, pts_a)
    occ_proxy = case_occlusion_proxy(spec_a, theta_a, pts_a[2])

    analytic_uv = project_world(pts_a, theta_a, spec_a)
    native = compare_native(native_result_path, analytic_uv, spec_a, theta_a)

    synthetic_pass = all(
        x["pass"] for x in [general_recovery, recovery_a, height, rank_anchor, null_edit, active, uncertainty, moving, style, occ_proxy]
    )
    changed_pass = bool(recovery_b["pass"])

    # Production effectiveness is intentionally not inferable from synthetic math proofs.
    report = {
        "schema": "BABYLON_CAMERA_SOLVER_PROOF_R03",
        "source_binding": {
            "babylon_package": "9.23.0",
            "babylon_tag_commit": "38ed028f40722504a215002fbc2fa89a2c89cf5d",
            "license": "Apache-2.0",
        },
        "FORMULA_PROOF": {
            "status": "PASS" if formula["pass"] else "FAIL",
            "details": formula,
        },
        "SYNTHETIC_RESULT": {
            "status": "PASS" if synthetic_pass else "FAIL",
            "known_general_camera_recovery": general_recovery,
            "arc_rotate_recovery": recovery_a,
            "projected_height_exact_solve": height,
            "rank_deficiency_and_best_extra_anchor": rank_anchor,
            "null_space_safe_edit": null_edit,
            "active_constraint": active,
            "uncertainty_monte_carlo": uncertainty,
            "moving_target_screen_lock": moving,
            "physical_style_separation": style,
            "occlusion_proxy_precheck": occ_proxy,
        },
        "BABYLON_NATIVE_AGREEMENT": native,
        "CHANGED_SCENE_TRANSFER": {
            "status": "PASS" if changed_pass else "FAIL",
            "details": recovery_b,
        },
        "PRODUCTION_EFFECTIVENESS": {
            "status": "NOT_PROVEN",
            "reason": "No approved ZORR production scene/effectiveness dataset was measured by this synthetic proof.",
        },
        "PRODUCTION_THRESHOLDS": "UNKNOWN / QC_PENDING",
        "MAIN_MUTATION": "NO",
        "MERGE": "NO",
        "CANON_LOCK": "NO",
    }
    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--native-result", type=Path, default=None)
    ap.add_argument("--output", type=Path, default=Path("BABYLON_CAMERA_SOLVER_PROOF_R03_result.json"))
    ap.add_argument("--native-payload", type=Path, default=Path("BABYLON_CAMERA_SOLVER_PROOF_R03_native_input.json"))
    args = ap.parse_args()

    spec, theta, pts = synthetic_scene_a()
    native_payload(spec, theta, pts, args.native_payload)
    report = build_report(args.native_result)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    terminal_math_ok = report["FORMULA_PROOF"]["status"] == "PASS" and report["SYNTHETIC_RESULT"]["status"] == "PASS" and report["CHANGED_SCENE_TRANSFER"]["status"] == "PASS"
    return 0 if terminal_math_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
