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

Two concrete defects/ambiguities were handled fail-closed:

1. Native `cv2.magnitude` produced tiny repeat-run float drift in `L2_gradient_strength`. OpenCV `Scharr` remains derivative authority; the contract formula `sqrt(Gx^2 + Gy^2)` is evaluated deterministically as minimal math glue. Fresh repeated real-reference artifacts are byte-identical after repair.

2. The source PNG alpha channels are fully opaque and therefore cannot prove silhouette. Otsu and Triangle source-derived masks disagree by 2.39%–7.06% across the three references. Their foreground intersection is retained as conservative visible evidence; their disagreement is emitted as `UNKNOWN`, not promoted to geometry.

Not claimed:
- full L0-L10 PASS;
- renderer ready or started;
- semantic anatomy PASS;
- occlusion PASS;
- cross-platform bit identity;
- production/canon/merge activation.

First remaining geometric blocker: `L3` has no independent ground-truth silhouette or owner-defined acceptance threshold. Adding more predicted segmentation models would not create ground truth, so R01 stops model-stacking here rather than manufacturing a PASS.

Renderer remains blocked. Image generation = `NO`. Image editing = `NO`.
