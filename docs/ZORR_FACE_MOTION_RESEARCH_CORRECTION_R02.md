# ZORR FACE MOTION — ANALYSIS / RESEARCH / CORRECTION R02

## Failure being corrected
The invalid path was independent image regeneration per frame. That produces identity jitter and cannot satisfy pixel-locked animation QC. The valid base is one immutable source raster plus deterministic local deformation.

## Research findings used
- OpenCV `remap` is a generic inverse geometric mapping: output pixels sample source coordinates through explicit maps. This matches a deterministic raster-warp engine.
- OpenCV also exposes Thin Plate Spline shape transformation with a regularization parameter; TPS is a viable future alternative to the current Gaussian RBF field.
- scikit-image supports Piecewise Affine transforms based on control points / Delaunay triangulation, and also exposes ThinPlateSplineTransform. Piecewise affine is useful as a comparison backend when rigid local topology matters more than smooth organic deformation.
- MediaPipe Face Landmarker exposes 52 blendshape coefficients including left/right mouth smile and cheek squint. For stylized anime, automatic landmark detection is NOT treated as authoritative; the blendshape names are used only as a semantic control taxonomy unless validated against the asset.
- OpenToonz Plastic deforms a texture column through a triangular mesh and skeleton. This supports the wider production direction: local 2D deformation should be represented as explicit mesh/field data, not as independent redraws.

## R01 defects found in code review
1. Regions were applied sequentially inside a frame. Overlapping regions were therefore order-dependent and could resample already warped pixels.
2. Gaussian feathering could conceptually enlarge the editable influence envelope. Exact-pixel QC should be defined against a separate hard editable mask.
3. R01 recorded outside-pixel identity but did not measure line/texture degradation inside the deformation region.
4. Temporal control existed as easing, but no explicit control-point trajectory report was emitted.
5. Runtime reproducibility metadata was incomplete.

## R02 corrections
- SINGLE REMAP: compose all region vector fields first, then sample frame 0 exactly once.
- ORDER INVARIANCE: overlapping fields use weighted-average composition; region order cannot change output.
- HARD MASK + INWARD FEATHER: feather lives only inside the permitted editable envelope; exterior alpha is exactly 0.
- SOURCE LOCK: expected W/H + SHA256.
- CONFIG LOCK: SHA256 recorded.
- DISPLACEMENT GATE: fail if a control or composed field exceeds configured px limit.
- LINE-ENERGY QC: record Laplacian energy ratio inside the editable region to catch excessive interpolation softness.
- TEMPORAL REPORT: store control positions, per-step speed and acceleration for every semantic anchor.
- REPRODUCIBILITY: OpenCL disabled, OpenCV thread count pinned to 1, dependency versions recorded.
- VALIDATE-ONLY MODE: source/config/masks/trajectories can be audited without producing edited images.

## Semantic face-motion taxonomy
R02 uses semantic names compatible with a FACS/blendshape-like mental model: mouthSmileLeft/Right, cheekSquintLeft/Right, mouthUpperUpLeft/Right, etc. These are labels for control intent, not claims that the anime source was automatically solved by MediaPipe.

## Hard law
ANIMATION FRAME != NEW GENERATION.

For pixel-controlled ZORR facial animation:
SOURCE_0 -> CONTROL TRAJECTORY -> ONE COMPOSED FIELD -> ONE REMAP -> HARD PIXEL QC.

No iterative warp accumulation. No hidden redraw. No identity drift outside declared editable topology.

## Next backends to benchmark, not blindly adopt
A. Gaussian RBF (current R02): smooth organic deformation, small dependency surface.
B. Thin Plate Spline: global smooth interpolation with regularization.
C. Piecewise Affine / Delaunay: explicit triangular topology, sharper local control but possible triangle-boundary artifacts.
D. OpenToonz Plastic mesh export/adaptation: production-friendly rig representation for larger 2D body/cloth motion.

Benchmark criteria: exterior identity = 1.0, anchor residual, local line-energy preservation, temporal jerk, runtime, and visual fold/line artifacts.

## Synthetic backend benchmark (development evidence, not a production-quality claim)
Environment: OpenCV 4.13.0; scikit-image 0.26.0; 384x384 synthetic line-art target; identical hard exterior replacement. One measured run:

| Backend | Anchor residual | Field/build | Render | Line-energy ratio | Exterior changed |
|---|---:|---:|---:|---:|---:|
| Gaussian RBF R02 | mean 0.000072 px inverse residual | 40.289 ms | 12.451 ms | 0.442609 | 0 px |
| Thin Plate Spline (scikit-image) | mean 0.000066 px | 0.260 ms | 277.364 ms | 0.444308 | 0 px |
| Piecewise Affine (scikit-image) | 0.0 px | 12.010 ms | 47.109 ms | 0.603912 | 0 px |

Interpretation: on this synthetic test, Piecewise Affine preserved more high-frequency line energy and exactly hit control anchors, while RBF rendered fastest after its field was built. TPS was much slower to render in this environment. This is NOT enough to replace RBF globally: PWA can introduce triangle-boundary behavior on organic facial shapes, so it should be benchmarked on real art before promotion.

## Research references
- OpenCV geometric remap: https://docs.opencv.org/doc/doxygen/html/da/d54/group__imgproc__transform.html
- OpenCV ThinPlateSplineShapeTransformer: https://docs.opencv.org/doc/doxygen/html/dc/d18/classcv_1_1ThinPlateSplineShapeTransformer.html
- scikit-image PiecewiseAffineTransform / ThinPlateSplineTransform: https://scikit-image.org/docs/stable/api/skimage.transform.html
- MediaPipe Face Landmarker blendshape taxonomy: https://ai.google.dev/edge/api/mediapipe/python/mp/tasks/vision/drawing_styles/face_landmarker/Blendshapes
- OpenToonz Plastic mesh deformation: https://opentoonz.readthedocs.io/en/latest/create_animations_using_plastic_tool.html
