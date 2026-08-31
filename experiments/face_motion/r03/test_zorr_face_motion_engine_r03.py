#!/usr/bin/env python3
import importlib.util
import tempfile
from pathlib import Path

import cv2
import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("eng", HERE / "zorr_face_motion_engine_r03.py")
eng = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(eng)


def synthetic_source(w=160, h=120):
    im = np.full((h, w, 3), 245, np.uint8)
    cv2.rectangle(im, (30, 25), (130, 95), (230, 210, 180), -1)
    cv2.line(im, (55, 60), (105, 60), (15, 15, 15), 2)
    cv2.circle(im, (60, 45), 5, (10, 10, 10), -1)
    cv2.circle(im, (100, 45), 5, (10, 10, 10), -1)
    return im


def base_cfg():
    return {
        "source": {"expected_size": [160, 120]},
        "animation": {"t_values": [0, 0.25, 0.5, 0.75, 1.0], "easing": "smootherstep"},
        "render": {"interpolation": "cubic"},
        "qc": {"max_displacement_px": 12, "min_line_energy_ratio_inside": 0.2, "min_jacobian_det": 0.05, "max_jacobian_det": 4.0, "max_control_step_px": 4.0, "max_control_accel_px": 3.0},
        "regions": [
            {"name": "mouth", "blend_mode": "weighted_average", "rbf_sigma_px": 14, "regularization": 1e-6,
             "mask": {"type": "ellipse", "center": [80, 60], "axes": [35, 18], "feather_inward_px": 5},
             "controls": [{"id": "L", "xy": [55, 60], "delta_at_1": [-2, -8]}, {"id": "R", "xy": [105, 60], "delta_at_1": [2, -8]}, {"id": "C", "xy": [80, 60], "delta_at_1": [0, -1]}],
             "locks": [[45, 45], [80, 42], [115, 45], [45, 78], [80, 80], [115, 78]]},
            {"name": "cheek_overlap", "blend_mode": "weighted_average", "rbf_sigma_px": 12, "regularization": 1e-6,
             "mask": {"type": "ellipse", "center": [58, 57], "axes": [18, 16], "feather_inward_px": 4},
             "controls": [{"id": "A", "xy": [58, 57], "delta_at_1": [0, -4]}],
             "locks": [[42, 48], [72, 48], [42, 70], [72, 70]]},
        ],
    }


def test_inward_feather_never_expands_hard_mask():
    hard, alpha = eng.build_hard_and_alpha_masks((120, 160), base_cfg()["regions"][0]["mask"])
    assert np.all(alpha[~hard] == 0)
    assert np.any((alpha[hard] > 0) & (alpha[hard] < 1))


def test_region_order_invariant_composition():
    cfg = base_cfg()
    a = eng.compose_fields((120, 160), cfg["regions"], 0.7)
    b = eng.compose_fields((120, 160), list(reversed(cfg["regions"])), 0.7)
    for x, y in zip(a[:4], b[:4]):
        if x.dtype == bool:
            assert np.array_equal(x, y)
        else:
            assert np.allclose(x, y, atol=1e-6)


def test_exterior_pixels_are_byte_exact():
    src = synthetic_source()
    cfg = base_cfg()
    dx, dy, hard, alpha, _ = eng.compose_fields(src.shape[:2], cfg["regions"], 1.0)
    out = eng.render_from_source(src, dx, dy, hard, alpha, cv2.INTER_LINEAR)
    assert np.array_equal(out[~hard], src[~hard])
    assert np.count_nonzero(cv2.absdiff(out, src)[hard]) > 0


def test_zero_amount_is_exact_identity_everywhere():
    src = synthetic_source()
    cfg = base_cfg()
    dx, dy, hard, alpha, _ = eng.compose_fields(src.shape[:2], cfg["regions"], 0.0)
    out = eng.render_from_source(src, dx, dy, hard, alpha, cv2.INTER_LINEAR)
    assert np.array_equal(out, src)


def test_max_displacement_validation():
    cfg = base_cfg()
    cfg["regions"][0]["controls"][0]["delta_at_1"] = [0, -99]
    try:
        eng.validate_config(cfg)
    except ValueError as e:
        assert "exceeds max_displacement_px" in str(e)
    else:
        raise AssertionError("Expected validation failure")


def test_smile_corner_trajectory_is_monotone_up():
    cfg = base_cfg()
    tr = eng.trajectory_report(cfg)
    left = next(c for c in tr["controls"] if c["id"] == "L")
    ys = [p[1] for p in left["positions"]]
    assert all(b <= a for a, b in zip(ys, ys[1:]))


def test_validate_only_with_realistic_file_contract():
    src = synthetic_source()
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        p = td / "src.png"
        cv2.imwrite(str(p), src)
        cfg = base_cfg()
        cfg["source"]["path"] = str(p)
        cfg["source"]["sha256"] = eng.sha256_file(p)
        cpath = td / "cfg.yaml"
        cpath.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
        result = eng.run(cpath, None, None, validate_only=True)
        assert result["status"] == "VALID"
        assert result["source"]["size"] == [160, 120]


def test_jacobian_stays_positive_for_valid_warp():
    src = synthetic_source()
    cfg = base_cfg()
    dx, dy, hard, alpha, _ = eng.compose_fields(src.shape[:2], cfg["regions"], 1.0)
    jm = eng.jacobian_metrics(dx, dy, hard)
    assert jm["min_det"] > 0.0
    assert jm["max_det"] < 4.0


def test_trajectory_quality_is_bounded():
    cfg = base_cfg()
    tr = eng.trajectory_report(cfg)
    q = eng.trajectory_quality(tr)
    assert q["max_control_step_px"] <= cfg["qc"]["max_control_step_px"]
    assert q["max_control_accel_px"] <= cfg["qc"]["max_control_accel_px"]


def test_edge_density_metric_is_identity_at_zero():
    src = synthetic_source()
    mask = np.ones(src.shape[:2], bool)
    assert abs(eng.edge_density_ratio(src, src.copy(), mask) - 1.0) < 1e-12


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in tests:
        fn()
        print("PASS", fn.__name__)
    print(f"PASS all {len(tests)} tests")
