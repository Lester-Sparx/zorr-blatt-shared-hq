# Reference Analysis R01 — execution evidence

Candidate branch: `zb/reference-analysis-base-r01`
Base: `b18ca6b9cce2dce6fe304ca8ae36c05df4f4dcb1`
Math contract SHA256: `a5926ba1f169d74a5562bd158ab6dc769090467aa7a1146541bd8a565bcac3c8`
OpenCV inspected upstream ref: `2ea6598f64f6f03d9d08db084a60585b0fc585f1`
Executed runtime: OpenCV Python `4.13.0`, NumPy `2.3.5`.

## Exact candidate bytes

- `reference_analysis.py` Git blob `1472fae4f9017bbf1f99b9cfcde7aeabd12d5b13`, SHA256 `1cb27de94f492522e60d5ae5cb4ae5cb37fcbf248d6bcd6551157e3d2d00422f`
- `test_reference_analysis.py` Git blob `3773e27380342a86adbfdbe9ddeac85efbb7523a`, SHA256 `360e93d36fdd69c4f84b92a0f9b64e5d6da7088403b469f4523555aa0a1f4331`
- `pyproject.toml` Git blob `31bedc2431e89eb9953cf619dc83253ab069d1e1`, SHA256 `59ef59d306984ba585852a7e26e85940be0ffb894aa2749eef2db54157651b28`

Local isolated verification on those exact source/test bytes:
- `pytest`: **5 passed**.
- Tests cover source-derived silhouette evidence, Otsu/Triangle consensus + disagreement, visible-only extrema/proportion graph, deterministic NPZ packaging, and byte-identical full analysis output on repeated identical input.
- No render, generation, or image edit was executed.

## Determinism defect found and repaired

A fresh repeated real-reference run initially disproved full byte determinism: identical `1 Гаммот.png` input/parameters produced different NPZ hashes. Array-by-array isolation showed the only differing layer was `L2_gradient_strength`; native `cv2.magnitude` differed by at most `0.00048828125` on `33420` pixels while `Gx` and `Gy` were identical.

Minimal repair:
- derivative authority remains native OpenCV `Scharr`;
- magnitude evaluates the contract formula `G = sqrt(Gx^2 + Gy^2)` in float64 and stores float32;
- deterministic NPZ packaging uses sorted keys and fixed ZIP metadata;
- no custom edge detector, contour tracer, vectorizer, pose model, anatomy solver, or renderer was introduced.

Fresh exact-candidate repeat after the repair and L3 uncertainty repair:
- manifest SHA256 run A = `c9f12470f4596e6e5e7180b6fc1c61d3fe018f4ddab9ef727d6357951373f0d7`
- manifest SHA256 run B = `c9f12470f4596e6e5e7180b6fc1c61d3fe018f4ddab9ef727d6357951373f0d7`
- NPZ SHA256 run A = `1ac23971b5e8c79adcc75667b6ba505f123065b610427c2f5a767818e7da1668`
- NPZ SHA256 run B = `1ac23971b5e8c79adcc75667b6ba505f123065b610427c2f5a767818e7da1668`
- JSON byte comparison = identical.
- NPZ byte comparison = identical.

This proves repeated byte determinism for that exact input/parameter/runtime case; it does **not** prove cross-platform bit identity.

## L3/L10 fail-closed repair

All three supplied character PNGs have alpha `255` at every pixel, so alpha contains no foreground/silhouette truth and is not used as geometry authority.

For the opaque near-white-background references, R01 now runs two native source-derived OpenCV threshold methods on the same measured Lab distance field:
- Otsu;
- Triangle.

The engine does **not** silently choose one method as truth:
- `M_VISIBLE` / L3 authoritative candidate = intersection of the two foreground masks;
- threshold disagreement (`XOR`) = L10 `UNKNOWN` and has no geometry authority;
- pixels classified background by both methods are stored as supported background evidence.

Observed method-disagreement fractions:
- `1 Гаммот.png`: `0.0239111582` (2.3911%)
- `f37607a7-fd21-4845-bd4e-62aaf72f76f1.png`: `0.0487333934` (4.8733%)
- `e28a871e-c77e-4f10-833d-d2ea85e20e61.png`: `0.0706405892` (7.0641%)

These are measurements, not PASS thresholds. L3 remains PARTIAL because no independent ground-truth mask exists.

## Real-reference transfer runs

Controlled comparison parameters for all runs: `simplification epsilon = 1.5 px`, `tone sigma = 24 px`, `color clusters k = 6`. These are recorded experiment parameters, **not universal ZORR thresholds**.

### 1. `1 Гаммот.png`

- source SHA256 `d0ed48cc8ca1e7053e9272948431f667f644e0a64bd48c3ecd4e47196de64277`
- dimensions `1024x1536`
- bbox `(75,20,821,1498)` px
- visible-consensus fraction `0.3619009654`
- uncertainty-disagreement fraction `0.0239111582`
- supported-background fraction `0.6141878764`
- external contour count `1`
- largest raw/simplified contour `8253 -> 459` points
- simplification error mean/rms/max `0.3909806 / 0.5132043 / 1.5920595` px
- structure NPZ SHA256 `1ac23971b5e8c79adcc75667b6ba505f123065b610427c2f5a767818e7da1668`
- manifest SHA256 `c9f12470f4596e6e5e7180b6fc1c61d3fe018f4ddab9ef727d6357951373f0d7`

### 2. `f37607a7-fd21-4845-bd4e-62aaf72f76f1.png`

- source SHA256 `d8e226599ccf9cd1c672c09465d3ea19f928395ea397a6eff10c90083a4deafb`
- dimensions `1024x1536`
- bbox `(0,9,855,1527)` px; source evidence touches the left border and is preserved rather than repaired/invented
- visible-consensus fraction `0.2848567963`
- uncertainty-disagreement fraction `0.0487333934`
- supported-background fraction `0.6664098104`
- external contour count `1`
- largest raw/simplified contour `9884 -> 520` points
- simplification error mean/rms/max `0.3817615 / 0.4933731 / 1.5165402` px
- structure NPZ SHA256 `7d8e734d2df9a0c3963bc270676a302aef5b40342920a0c258d1f6ebde23a373`
- manifest SHA256 `9d300ae6313dde788164ed5372f4d0a7c0c3b0f2bc53e846e7203287680b24b4`

### 3. `e28a871e-c77e-4f10-833d-d2ea85e20e61.png`

- source SHA256 `ad031c8ea5749b9c0ad5854c9b6d005210d4f03de75fce1de50872d4c0458edc`
- dimensions `1055x1491`
- bbox `(195,31,650,1446)` px
- visible-consensus fraction `0.2651282100`
- uncertainty-disagreement fraction `0.0706405892`
- supported-background fraction `0.6642312008`
- external evidence components retained `315`; R01 does not silently delete small visible components
- largest raw/simplified contour `7899 -> 508` points
- simplification error mean/rms/max `0.3687546 / 0.4910386 / 1.4909986` px
- structure NPZ SHA256 `01d638182e768bdc7d9825fbcfb33f93edd392d05419461224c244728914d331`
- manifest SHA256 `fb1008665d519be488035e5904c54dc0e2c9c15083b3156306e821216a3ad4c7`

## Fail-closed layer state

All three exact-candidate runs report:

- `L0 PASS` — source RGB bytes decoded and retained as observed evidence.
- `L1 PASS` — luminance field emitted.
- `L2 PASS` — Scharr derivatives, magnitude and angle emitted.
- `L3 PARTIAL` — two native source-derived segmenters provide a conservative visible consensus; no independent ground-truth mask exists.
- `L4 PARTIAL` — binary internal edge evidence only; semantic line class is not proven.
- `L5 PARTIAL` — Lab color masses only; no semantic object labels.
- `L6 PARTIAL` — visible silhouette extrema only; anatomy is not inferred.
- `L7 UNKNOWN` — occlusion ordering is not directly proven and is not guessed.
- `L8 PARTIAL` — visible-region texture-frequency summary only.
- `L9 PARTIAL` — 2D luminance-gradient evidence only; no imaginary 3D light reconstruction.
- `L10 PARTIAL` — threshold-disagreement `M_UNKNOWN` is emitted; `M_OCCLUDED` remains unknown.

Current terminal claim: `REFERENCE_STRUCTURE_STATE_EXECUTED / PARTIAL`.

Not claimed: full L0-L10 PASS, renderer readiness, semantic anatomy/occlusion PASS, production/canon/merge activation.

Renderer remains `NOT_STARTED`. Image generation = `NO`. Image editing = `NO`.

First remaining geometric blocker under the contract is still `L3`: no independent ground-truth silhouette/acceptance threshold exists for these references. More predicted segmenters would add opinions, not ground truth, so R01 does not stack models to manufacture a PASS.
