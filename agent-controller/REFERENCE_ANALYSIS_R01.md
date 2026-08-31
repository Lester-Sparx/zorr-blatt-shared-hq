# Reference Analysis R01

This is the deterministic pre-render slice for `ZORR_REFERENCE_TO_DRAWING_ENGINE_MATH.md`.

Boundary: analysis only. It does not render, generate, edit, or infer hidden anatomy.

Runtime path:

`reference pixels -> OpenCV evidence layers -> structure-state JSON + NPZ`

The CLI requires per-run values for contour simplification epsilon, tone low-frequency sigma, and color-cluster count. They are recorded parameters, not universal ZORR thresholds.

Current R01 deliberately leaves semantic anatomy anchors and occlusion ordering PARTIAL/UNKNOWN rather than guessing them.

Example invocation:

`zb-reference-analyze source.png --output-json state.json --output-npz layers.npz --simplification-epsilon-px 1.5 --tone-sigma-px 24 --color-clusters 6`

No output image is produced.
