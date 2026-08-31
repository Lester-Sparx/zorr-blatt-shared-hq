# Reference Analysis R01 status

`REFERENCE_STRUCTURE_STATE_EXECUTED / PARTIAL`

What is physically proven on the exact candidate source bytes:
- deterministic OpenCV/NumPy structure-state path executes;
- **5 tests pass**;
- 3 existing character references complete without render/generation/edit;
- repeated identical `1 Гаммот.png` input + identical parameters produces byte-identical JSON and NPZ artifacts in the executed runtime;
- `L0/L1/L2 = PASS`;
- `L3/L4/L5/L6/L8/L9/L10 = PARTIAL` with exact reasons in the manifest/evidence;
- `L7 = UNKNOWN` rather than inferred.

A real determinism defect was found during review: native `cv2.magnitude` produced tiny repeat-run float drift in `L2_gradient_strength`. The repaired candidate keeps OpenCV `Scharr` derivatives and evaluates the contract formula `sqrt(Gx^2 + Gy^2)` deterministically as minimal math glue. Fresh repeated real-reference artifacts are byte-identical after that repair.

Not claimed:
- full L0-L10 PASS;
- renderer ready or started;
- semantic anatomy PASS;
- occlusion PASS;
- cross-platform bit identity;
- production/canon/merge activation.

First remaining geometric blocker: `L3` silhouette verification. Current segmentation is measured and recorded but lacks an independent ground-truth mask, so L3 remains PARTIAL.

Next legal work: improve/verify L3 only using existing/native/OSS evidence methods. Do not jump to renderer, style transfer, IP-Adapter, ControlNet, or diffusion while the silhouette authority gate remains PARTIAL.
