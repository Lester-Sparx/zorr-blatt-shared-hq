# Reference Analysis R01 — execution evidence

Candidate branch: `zb/reference-analysis-base-r01`
Base: `b18ca6b9cce2dce6fe304ca8ae36c05df4f4dcb1`
Math contract SHA256: `a5926ba1f169d74a5562bd158ab6dc769090467aa7a1146541bd8a565bcac3c8`
OpenCV inspected upstream ref: `2ea6598f64f6f03d9d08db084a60585b0fc585f1`
Executed runtime: OpenCV Python `4.13.0`, NumPy `2.3.5`.

## Exact candidate bytes

- `reference_analysis.py` Git blob `88103f7fa4bbf4c641071ccf1247a49f8810e744`, SHA256 `f6b921eb9d4894df70c93e9d418a19b18a718862aa08a89dd9afcdcad0154045`
- `test_reference_analysis.py` Git blob `7a675fe29ba2f2094e32e599d4e26eabcdf6cd78`, SHA256 `a5db1ec9184b4b063a72a1e9c1bc74fa687f9665d3ca240236ca0d31fb531414`
- `pyproject.toml` Git blob `31bedc2431e89eb9953cf619dc83253ab069d1e1`, SHA256 `59ef59d306984ba585852a7e26e85940be0ffb894aa2749eef2db54157651b28`

Local isolated verification on those exact source/test bytes:
- `pytest`: **5 passed**.
- Tests cover source-derived Otsu silhouette evidence, visible-only extrema/proportion graph, deterministic NPZ bytes, and byte-identical full analysis output on repeated identical input.
- No render, generation, or image edit was executed.

## Determinism defect found and repaired

A fresh repeated real-reference run initially disproved full byte determinism: identical `1 Гаммот.png` input/parameters produced different NPZ hashes. Array-by-array isolation showed the only differing layer was `L2_gradient_strength`; `cv2.magnitude` differed by at most `0.00048828125` on `33420` pixels while `Gx` and `Gy` were identical.

Minimal repair:
- derivative authority remains native OpenCV `Scharr`;
- magnitude now evaluates the contract formula `G = sqrt(Gx^2 + Gy^2)` in float64 and stores float32;
- deterministic NPZ packaging uses sorted keys and fixed ZIP metadata;
- no custom edge detector/vectorizer/anatomy solver was introduced.

Fresh exact-candidate repeat after the repair:
- manifest SHA256 run A = `ca5c36f01d1dbff89cb4c7d2251c51cb8b958ae924e9628b2a26af615fbcdce2`
- manifest SHA256 run B = `ca5c36f01d1dbff89cb4c7d2251c51cb8b958ae924e9628b2a26af615fbcdce2`
- NPZ SHA256 run A = `4219e65bcf0db324c36d0be4d09395e7ccf693cbdfaa82ccbf682a28a3ceaa2d`
- NPZ SHA256 run B = `4219e65bcf0db324c36d0be4d09395e7ccf693cbdfaa82ccbf682a28a3ceaa2d`
- JSON byte comparison = identical.
- NPZ byte comparison = identical.

This proves repeated byte determinism for that exact input/parameter/runtime case; it does not prove cross-platform bit identity.

## Real-reference transfer runs

Controlled comparison parameters for all runs: `simplification epsilon = 1.5 px`, `tone sigma = 24 px`, `color clusters k = 6`. These are recorded experiment parameters, **not universal ZORR thresholds**.

### 1. `1 Гаммот.png`

- source SHA256 `d0ed48cc8ca1e7053e9272948431f667f644e0a64bd48c3ecd4e47196de64277`
- dimensions `1024x1536`
- bbox `(75,20,821,1498)` px
- external contour count `1`
- largest raw/simplified contour `8253 -> 459` points
- simplification error mean/rms/max `0.3909806 / 0.5132043 / 1.5920595` px
- structure NPZ SHA256 `4219e65bcf0db324c36d0be4d09395e7ccf693cbdfaa82ccbf682a28a3ceaa2d`
- manifest SHA256 `ca5c36f01d1dbff89cb4c7d2251c51cb8b958ae924e9628b2a26af615fbcdce2`

### 2. `f37607a7-fd21-4845-bd4e-62aaf72f76f1.png`

- source SHA256 `d8e226599ccf9cd1c672c09465d3ea19f928395ea397a6eff10c90083a4deafb`
- dimensions `1024x1536`
- bbox `(0,9,855,1527)` px; source evidence touches the left border and is preserved rather than repaired/invented
- external contour count `1`
- largest raw/simplified contour `9884 -> 520` points
- simplification error mean/rms/max `0.3817615 / 0.4933731 / 1.5165402` px
- structure NPZ SHA256 `fb46b9f25cf001336f4f3233a67834462f0681ef617f28dbd57cccbda10f7a33`
- manifest SHA256 `5f750aec194aa9a980e190d98e9e0b036963c505ab8d69d623c6ba0899267a8b`

### 3. `e28a871e-c77e-4f10-833d-d2ea85e20e61.png`

- source SHA256 `ad031c8ea5749b9c0ad5854c9b6d005210d4f03de75fce1de50872d4c0458edc`
- dimensions `1055x1491`
- bbox `(195,31,650,1446)` px
- external evidence components retained `315`; R01 does not silently delete small visible components
- largest raw/simplified contour `7899 -> 508` points
- simplification error mean/rms/max `0.3687546 / 0.4910386 / 1.4909986` px
- structure NPZ SHA256 `eba9e29576f645098326386ce60abd8806d89f6cf6884db8814c9fb27e2398ac`
- manifest SHA256 `fe3f090a54532182f3fe6ba786cbb034fbefe1b75d695758b4d99ec8b3dd03ec`

## Fail-closed layer state

All three exact-candidate runs report:

- `L0 PASS` — source RGB bytes decoded and retained as observed evidence.
- `L1 PASS` — luminance field emitted.
- `L2 PASS` — Scharr derivatives, magnitude and angle emitted.
- `L3 PARTIAL` — segmentation executed, but no independent ground-truth pixel mask exists.
- `L4 PARTIAL` — binary internal edge evidence only; semantic line class is not proven.
- `L5 PARTIAL` — Lab color masses only; no semantic object labels.
- `L6 PARTIAL` — visible silhouette extrema only; anatomy is not inferred.
- `L7 UNKNOWN` — occlusion ordering is not directly proven and is not guessed.
- `L8 PARTIAL` — visible-region texture-frequency summary only.
- `L9 PARTIAL` — 2D luminance-gradient evidence only; no imaginary 3D light reconstruction.
- `L10 PARTIAL` — `M_VISIBLE/M_UNKNOWN` emitted; `M_OCCLUDED` remains unknown.

Current terminal claim: `REFERENCE_STRUCTURE_STATE_EXECUTED / PARTIAL`.

Not claimed: full L0-L10 PASS, renderer readiness, semantic anatomy/occlusion PASS, production/canon/merge activation.

Renderer remains `NOT_STARTED`. Image generation = `NO`. Image editing = `NO`.

First remaining geometric blocker under the contract is `L3`: silhouette correctness is not independently verified against a ground-truth mask. The next repair/QC work must stay on L3 rather than jumping to style/render/generative assistance.
