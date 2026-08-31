from __future__ import annotations

import argparse, hashlib, json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np

CONTRACT_SHA256 = "a5926ba1f169d74a5562bd158ab6dc769090467aa7a1146541bd8a565bcac3c8"
OPENCV_REF = "2ea6598f64f6f03d9d08db084a60585b0fc585f1"


@dataclass(frozen=True)
class AnalysisParams:
    simplification_epsilon_px: float
    tone_sigma_px: float
    color_clusters: int

    def validate(self) -> None:
        if self.simplification_epsilon_px < 0 or self.tone_sigma_px <= 0 or self.color_clusters < 1:
            raise ValueError("invalid analysis parameters")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def to_rgb(image: np.ndarray) -> tuple[np.ndarray, np.ndarray | None]:
    if image.ndim == 2:
        return cv2.cvtColor(image, cv2.COLOR_GRAY2RGB), None
    if image.shape[2] == 4:
        return cv2.cvtColor(image[:, :, :3], cv2.COLOR_BGR2RGB), image[:, :, 3].copy()
    if image.shape[2] == 3:
        return cv2.cvtColor(image, cv2.COLOR_BGR2RGB), None
    raise ValueError(f"unsupported image shape {image.shape}")


def perimeter(a: np.ndarray) -> np.ndarray:
    return np.concatenate((a[0], a[-1], a[1:-1, 0], a[1:-1, -1]), axis=0)


def silhouette_from_border(rgb: np.ndarray) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
    border = perimeter(lab)
    bg = np.median(border, axis=0)
    dist = np.linalg.norm(lab - bg[None, None, :], axis=2).astype(np.float32)
    lo, hi = float(dist.min()), float(dist.max())
    if hi <= lo:
        raise ValueError("no measurable border/foreground separation")
    scaled = np.clip((dist - lo) * 255.0 / (hi - lo), 0, 255).astype(np.uint8)
    threshold_u8, mask = cv2.threshold(scaled, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    info = {
        "method": "OpenCV Lab border median distance + Otsu",
        "background_lab_median": [float(x) for x in bg],
        "background_lab_std": [float(x) for x in border.std(axis=0)],
        "otsu_threshold_u8": float(threshold_u8),
        "otsu_threshold_lab_encoded_distance": lo + float(threshold_u8) * (hi - lo) / 255.0,
        "foreground_fraction": float(np.count_nonzero(mask) / mask.size),
        "provenance": "DERIVED",
    }
    return mask, lab, info


def extrema_anchors(mask: np.ndarray) -> list[dict[str, Any]]:
    ys, xs = np.nonzero(mask)
    if not xs.size:
        return []
    h, w = mask.shape
    idxs = {"left": np.argmin(xs), "right": np.argmax(xs), "top": np.argmin(ys), "bottom": np.argmax(ys)}
    return [{
        "name": f"silhouette_{name}", "x_px": int(xs[i]), "y_px": int(ys[i]),
        "x_norm": float(xs[i] / w), "y_norm": float(ys[i] / h),
        "provenance": "DERIVED", "authority": "visible_silhouette_only",
    } for name, i in idxs.items()]


def proportions(anchors: list[dict[str, Any]], width_px: int) -> dict[str, Any]:
    edges = []
    for i, a in enumerate(anchors):
        for b in anchors[i + 1:]:
            d = float(np.hypot(a["x_px"] - b["x_px"], a["y_px"] - b["y_px"]))
            edges.append({"a": a["name"], "b": b["name"], "distance_px": d,
                          "ratio_to_visible_bbox_width": d / width_px, "provenance": "DERIVED"})
    return {"scale": {"name": "visible_bbox_width", "value_px": width_px, "provenance": "DERIVED"},
            "edges": edges, "provenance": "DERIVED"}


def color_masses(lab: np.ndarray, mask: np.ndarray, k: int) -> tuple[np.ndarray, list[dict[str, Any]]]:
    fg = mask.astype(bool)
    samples = lab[fg].reshape(-1, 3).astype(np.float32)
    if len(samples) < k:
        raise ValueError("color cluster count exceeds visible pixel count")
    cv2.setRNGSeed(0)
    criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_MAX_ITER, 30, 0.25)
    compactness, labels, centers = cv2.kmeans(samples, k, None, criteria, 3, cv2.KMEANS_PP_CENTERS)
    label_map = np.full(mask.shape, -1, dtype=np.int16)
    label_map[fg] = labels.ravel().astype(np.int16)
    regions = []
    for i in range(k):
        s = samples[labels.ravel() == i]
        regions.append({"cluster_id": i, "area_px": int(len(s)), "mean_lab": [float(x) for x in s.mean(0)],
                        "variance_lab": [float(x) for x in s.var(0)], "center_lab": [float(x) for x in centers[i]],
                        "semantic_authority": "NONE_color_mass_only", "provenance": "DERIVED"})
    regions.sort(key=lambda x: x["area_px"], reverse=True)
    return label_map, regions + [{"kmeans_compactness": float(compactness), "provenance": "DERIVED"}]


def contour_error(raw: np.ndarray, simple: np.ndarray) -> dict[str, Any]:
    if len(simple) < 3:
        return {"mean_px": None, "rms_px": None, "max_px": None}
    d = np.array([abs(cv2.pointPolygonTest(simple, tuple(map(float, p)), True)) for p in raw[:, 0]], dtype=float)
    return {"mean_px": float(d.mean()), "rms_px": float(np.sqrt(np.mean(d * d))), "max_px": float(d.max())}


def analyze(source: Path, out_json: Path, out_npz: Path, p: AnalysisParams) -> dict[str, Any]:
    p.validate()
    image = cv2.imread(str(source), cv2.IMREAD_UNCHANGED)
    if image is None:
        raise ValueError(f"OpenCV cannot decode {source}")
    rgb, alpha = to_rgb(image)
    h, w = rgb.shape[:2]
    lum = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32)
    gx, gy = cv2.Scharr(lum, cv2.CV_32F, 1, 0), cv2.Scharr(lum, cv2.CV_32F, 0, 1)
    mag, angle = cv2.magnitude(gx, gy), cv2.phase(gx, gy, angleInDegrees=False)
    mask, lab, silhouette_info = silhouette_from_border(rgb)
    fg = mask.astype(bool)
    if not fg.any():
        raise ValueError("empty visible silhouette")

    ys, xs = np.nonzero(fg)
    bbox = {"x_px": int(xs.min()), "y_px": int(ys.min()), "width_px": int(xs.max()-xs.min()+1),
            "height_px": int(ys.max()-ys.min()+1), "provenance": "DERIVED"}
    anchors = extrema_anchors(mask)

    arrays: dict[str, np.ndarray] = {
        "L0_source_rgb": rgb, "L1_luminance": lum, "L2_gradient_x": gx, "L2_gradient_y": gy,
        "L2_gradient_strength": mag, "L2_gradient_angle_rad": angle, "L3_visible_silhouette_mask": mask,
        "L10_uncertainty_subject_geometry_mask": (~fg).astype(np.uint8) * 255,
    }
    if alpha is not None:
        arrays["source_alpha"] = alpha

    contour_records = []
    contours, _ = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    for i, raw in enumerate(sorted(contours, key=cv2.contourArea, reverse=True)):
        simple = cv2.approxPolyDP(raw, p.simplification_epsilon_px, True)
        rk, sk = f"contour_{i:04d}_raw_xy", f"contour_{i:04d}_simplified_xy"
        arrays[rk], arrays[sk] = raw[:, 0].astype(np.int32), simple[:, 0].astype(np.int32)
        contour_records.append({"raw_contour": {"npz_key": rk, "point_count": len(raw), "provenance": "DERIVED"},
                                "simplified_contour": {"npz_key": sk, "point_count": len(simple), "provenance": "DERIVED"},
                                "simplification_epsilon_px": p.simplification_epsilon_px,
                                "pixel_error_to_raw": contour_error(raw, simple), "provenance": "DERIVED"})

    grad_u8 = cv2.normalize(mag, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    grad_otsu, internal = cv2.threshold(grad_u8, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    internal[~fg] = 0
    arrays["L4_internal_edge_map"] = internal
    color_map, regions = color_masses(lab, mask, p.color_clusters)
    arrays["L5_color_cluster_map"] = color_map
    low = cv2.GaussianBlur(lum, (0, 0), p.tone_sigma_px)
    local = lum - low
    arrays["tone_low_frequency"], arrays["local_tone"] = low, local

    valid_x, valid_y = fg[:, :-1] & fg[:, 1:], fg[:-1] & fg[1:]
    dx, dy = np.abs(lum[:, 1:] - lum[:, :-1]), np.abs(lum[1:] - lum[:-1])
    texture = {"Tx": float(dx[valid_x].mean()) if valid_x.any() else None,
               "Ty": float(dy[valid_y].mean()) if valid_y.any() else None, "provenance": "DERIVED"}
    lighting = {"mean_gradient_x": float(gx[fg].mean()), "mean_gradient_y": float(gy[fg].mean()),
                "mean_gradient_strength": float(mag[fg].mean()), "provenance": "DERIVED",
                "note": "2D evidence only; no reconstructed 3D light"}
    tone = {"mean": float(lum[fg].mean()), "std": float(lum[fg].std()),
            "quantiles_05_25_50_75_95": [float(x) for x in np.quantile(lum[fg], [.05,.25,.5,.75,.95])],
            "local_tone_std": float(local[fg].std()), "sigma_px": p.tone_sigma_px, "provenance": "DERIVED"}

    out_npz.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out_npz, **arrays)
    npz_hash = sha256(out_npz)
    na = "NOT_APPLICABLE_NO_DRAWING_CANDIDATE"
    manifest = {
        "contract": {"sha256": CONTRACT_SHA256, "status": "ENGINE_SPEC_NO_RENDER"},
        "source": {"name": source.name, "sha256": sha256(source), "width_px": w, "height_px": h, "provenance": "OBSERVED"},
        "runtime": {"opencv_python_version": cv2.__version__, "opencv_inspected_ref": OPENCV_REF,
                    "numpy_version": np.__version__, "custom_cv_algorithm": "NO", "image_generation": "NO", "image_editing": "NO"},
        "parameters": {"simplification_epsilon_px": p.simplification_epsilon_px, "tone_sigma_px": p.tone_sigma_px,
                       "color_clusters": p.color_clusters, "internal_edge_otsu_threshold_u8": float(grad_otsu)},
        "visible_bbox_px": bbox, "visible_silhouette": {"npz_key": "L3_visible_silhouette_mask", **silhouette_info},
        "contours": contour_records, "anchors": anchors, "proportion_graph": proportions(anchors, bbox["width_px"]),
        "occlusion_graph": {"relations": [], "provenance": "UNKNOWN", "reason": "not directly proven; not inferred"},
        "color_regions": regions, "tone_field_summary": tone, "texture_summary": texture, "lighting_evidence_summary": lighting,
        "uncertainty_mask": {"npz_key": "L10_uncertainty_subject_geometry_mask", "scope": "subject_geometry_authority",
                             "provenance": "DERIVED", "rule": "outside visible silhouette has no subject geometry authority"},
        "layers": {"L0":"PASS","L1":"PASS","L2":"PASS","L3":"PASS","L4":"PARTIAL","L5":"PARTIAL",
                   "L6":"PARTIAL","L7":"UNKNOWN","L8":"PARTIAL","L9":"PARTIAL","L10":"PASS"},
        "qc_vector": {k: na for k in ["E_silhouette_px","E_anchor_px","E_proportion","E_occlusion","E_tone","E_color","E_texture","E_line_topology"]},
        "artifacts": {"layers_npz": {"name": out_npz.name, "sha256": npz_hash}},
        "terminal": {"structure_state":"CREATED","renderer":"NOT_STARTED","unknown_promoted_to_geometry":False,
                     "image_generation":"NO","image_editing":"NO"},
    }
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="ZORR reference -> structure state; analysis only")
    ap.add_argument("source", type=Path); ap.add_argument("--output-json", type=Path, required=True); ap.add_argument("--output-npz", type=Path, required=True)
    ap.add_argument("--simplification-epsilon-px", type=float, required=True); ap.add_argument("--tone-sigma-px", type=float, required=True); ap.add_argument("--color-clusters", type=int, required=True)
    a = ap.parse_args(argv)
    m = analyze(a.source, a.output_json, a.output_npz, AnalysisParams(a.simplification_epsilon_px, a.tone_sigma_px, a.color_clusters))
    print(json.dumps({"status":m["terminal"]["structure_state"],"source_sha256":m["source"]["sha256"],"layers_npz_sha256":m["artifacts"]["layers_npz"]["sha256"],"renderer":m["terminal"]["renderer"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
