"""ZORR Perspective Master R01 — research-only mathematical kernel.

Minimal ZORR glue around NumPy/OpenCV. Robust homography/PnP estimation is
reused from OpenCV rather than reimplemented. No production thresholds or lore.
"""
from __future__ import annotations
import math
import json
import numpy as np
import cv2


def normalize(v):
    v = np.asarray(v, dtype=float)
    n = np.linalg.norm(v)
    if n <= 0:
        raise ValueError("zero vector")
    return v / n


def camera_matrix(fx, fy, cx, cy, skew=0.0):
    return np.array([[float(fx), float(skew), float(cx)],
                     [0.0, float(fy), float(cy)],
                     [0.0, 0.0, 1.0]], dtype=float)


def look_at_world_to_camera(camera_center, target, world_up=(0.0, 1.0, 0.0)):
    C = np.asarray(camera_center, float)
    T = np.asarray(target, float)
    forward = normalize(T - C)
    right = normalize(np.cross(forward, normalize(world_up)))
    up = normalize(np.cross(right, forward))
    R = np.vstack([right, -up, forward])
    t = -R @ C
    return R, t


def project_points(K, R, t, points_world):
    X = np.atleast_2d(np.asarray(points_world, float))
    Xc = (np.asarray(R, float) @ X.T + np.asarray(t, float)[:, None]).T
    q = (np.asarray(K, float) @ Xc.T).T
    return q[:, :2] / q[:, 2:3], Xc[:, 2]


def vanishing_point_h(K, R, direction_world):
    """Homogeneous VP. w=0 is a valid ideal point, not a failure."""
    return np.asarray(K, float) @ (np.asarray(R, float) @ normalize(direction_world))


def dehomogenize_point(p, eps=1e-12):
    p = np.asarray(p, float)
    if abs(p[-1]) <= eps:
        return None
    return p[:-1] / p[-1]


def line_through_hpoints(p1, p2):
    l = np.cross(np.asarray(p1, float), np.asarray(p2, float))
    n = math.hypot(l[0], l[1])
    if n <= 0:
        raise ValueError("degenerate line")
    return l / n


def plane_vanishing_line_from_normal(K, normal_camera):
    l = np.linalg.inv(np.asarray(K, float)).T @ np.asarray(normal_camera, float)
    n = math.hypot(l[0], l[1])
    if n <= 0:
        raise ValueError("degenerate vanishing line")
    return l / n


def ground_homography_xz(K, R, t):
    """World plane Y=0 parameterized by [X,Z,1]."""
    R = np.asarray(R, float)
    return np.asarray(K, float) @ np.column_stack([R[:, 0], R[:, 2], np.asarray(t, float)])


def homography_project(H, points_xy):
    pts = np.atleast_2d(np.asarray(points_xy, float))
    ph = np.column_stack([pts, np.ones(len(pts))])
    q = (np.asarray(H, float) @ ph.T).T
    return q[:, :2] / q[:, 2:3]


def homography_jacobian(H, x, y):
    H = np.asarray(H, float)
    a, b, c = H[0]
    d, e, f = H[1]
    g, h, i = H[2]
    den = g*x + h*y + i
    nu = a*x + b*y + c
    nv = d*x + e*y + f
    return np.array([
        [(a*den - g*nu)/(den*den), (b*den - h*nu)/(den*den)],
        [(d*den - g*nv)/(den*den), (e*den - h*nv)/(den*den)],
    ], dtype=float)


def perspective_area_scale(H_image_to_plane, x, y):
    return float(abs(np.linalg.det(homography_jacobian(H_image_to_plane, x, y))))


def iac(K):
    Ki = np.linalg.inv(np.asarray(K, float))
    return Ki.T @ Ki


def orthogonal_vp_residual(K, v1_h, v2_h):
    return float(np.asarray(v1_h, float) @ iac(K) @ np.asarray(v2_h, float))


def robust_homography(world_xy, image_uv, threshold_px=3.0):
    H, mask = cv2.findHomography(
        np.asarray(world_xy, np.float64),
        np.asarray(image_uv, np.float64),
        method=cv2.USAC_MAGSAC,
        ransacReprojThreshold=float(threshold_px),
        maxIters=10000,
        confidence=0.999,
    )
    if H is None or mask is None:
        raise RuntimeError("homography estimation failed")
    return H, mask.ravel().astype(bool)


def solve_pose_pnp(object_xyz, image_uv, K, dist=None):
    obj = np.asarray(object_xyz, np.float64)
    img = np.asarray(image_uv, np.float64)
    K = np.asarray(K, np.float64)
    dist = np.zeros((5, 1), np.float64) if dist is None else np.asarray(dist, np.float64)
    ok, rvec, tvec, inliers = cv2.solvePnPRansac(
        obj, img, K, dist,
        flags=cv2.SOLVEPNP_SQPNP,
        iterationsCount=1000,
        reprojectionError=3.0,
        confidence=0.999,
    )
    if not ok:
        raise RuntimeError("solvePnPRansac failed")
    return rvec, tvec, inliers


def project_vertical_segment(K, R, t, ground_xz, world_height):
    X, Z = map(float, ground_xz)
    pts = np.array([[X, 0.0, Z], [X, float(world_height), Z]], float)
    uv, depth = project_points(K, R, t, pts)
    if np.any(depth <= 0):
        raise ValueError("segment behind camera")
    return uv, float(np.linalg.norm(uv[1] - uv[0]))


def synthetic_proof():
    """Synthetic self-test only; PASS is not a production-style threshold."""
    cv2.setRNGSeed(222)
    rng = np.random.default_rng(222)
    W, H = 1920, 1080
    K = camera_matrix(900, 900, (W-1)/2, (H-1)/2)
    C = np.array([1.6, 2.2, -4.0])
    target = np.array([-0.8, 0.45, 7.0])
    R, t = look_at_world_to_camera(C, target)

    vx_h = vanishing_point_h(K, R, [1, 0, 0])
    vz_h = vanishing_point_h(K, R, [0, 0, 1])
    vx = dehomogenize_point(vx_h)
    vz = dehomogenize_point(vz_h)
    horizon = line_through_hpoints(vx_h, vz_h)

    n_cam = R @ np.array([0.0, 1.0, 0.0])
    horizon_dual = plane_vanishing_line_from_normal(K, n_cam)
    if np.dot(horizon, horizon_dual) < 0:
        horizon_dual *= -1

    H_g2i = ground_homography_xz(K, R, t)
    H_i2g = np.linalg.inv(H_g2i)
    ground = np.array([[x, z] for z in [2.,5.,9.,13.] for x in [-5.,-3.,-1.,1.,3.,5.]], np.float64)
    clean = homography_project(H_g2i, ground)
    noisy = clean + rng.normal(0, 0.8, clean.shape)
    outliers = np.array([2, 9, 17, 22])
    noisy[outliers] += rng.normal(0, 120, (4, 2))
    H_est, inliers = robust_homography(ground, noisy)
    recovered = homography_project(H_est, ground)
    errors = np.linalg.norm(recovered - clean, axis=1)

    roundtrip = []
    for X in np.linspace(-5, 5, 11):
        for Z in np.linspace(1, 14, 14):
            p = homography_project(H_g2i, [[X, Z]])[0]
            q = homography_project(H_i2g, [p])[0]
            roundtrip.append(np.linalg.norm(q - [X, Z]))

    depths = [1.5, 4.0, 7.5, 12.0]
    heights = [project_vertical_segment(K, R, t, [0, z], 1.8)[1] for z in depths]
    ortho = abs(orthogonal_vp_residual(K, vx_h, vz_h))
    horizon_residual = float(np.linalg.norm(horizon - horizon_dual))
    median_error = float(np.median(errors[inliers]))
    roundtrip_max = float(np.max(roundtrip))

    # Separate ideal-point proof: zero yaw makes the world-X VP ideal (w=0), which is valid in P^2.
    R0, t0 = look_at_world_to_camera([0.0, 2.2, -4.0], [0.0, 0.45, 7.0])
    ideal_vx_h = vanishing_point_h(K, R0, [1, 0, 0])
    ideal_point_gate = abs(float(ideal_vx_h[2])) < 1e-12

    gates = {
        "all_injected_outliers_rejected": bool(np.all(~inliers[outliers])),
        "median_homography_error_lt_1px": median_error < 1.0,
        "roundtrip_lt_1e-9": roundtrip_max < 1e-9,
        "orthogonal_vp_residual_lt_1e-10": ortho < 1e-10,
        "horizon_duality_lt_1e-10": horizon_residual < 1e-10,
        "equal_height_shrinks_with_depth": all(a > b for a, b in zip(heights[:-1], heights[1:])),
        "ideal_vanishing_point_supported": ideal_point_gate,
    }

    return {
        "result": "PASS" if all(gates.values()) else "FAIL",
        "vp_x": vx.tolist(),
        "vp_z": vz.tolist(),
        "horizon": horizon.tolist(),
        "homography_inliers": int(inliers.sum()),
        "homography_total": int(len(inliers)),
        "median_homography_error_px": median_error,
        "roundtrip_max": roundtrip_max,
        "orthogonal_vp_residual": ortho,
        "horizon_duality_residual": horizon_residual,
        "equal_1p8_unit_pixel_heights": dict(zip(map(str, depths), heights)),
        "ideal_vp_homogeneous": ideal_vx_h.tolist(),
        "pass_gates": gates,
    }


if __name__ == "__main__":
    result = synthetic_proof()
    print(json.dumps(result, indent=2))
    if result["result"] != "PASS":
        raise SystemExit(1)
