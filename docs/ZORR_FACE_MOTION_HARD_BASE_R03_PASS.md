# ZORR FACE MOTION HARD BASE R03 — PASS

Status: **PASS** for the current scope: deterministic closed-mouth smile animation from one immutable source raster.

## Owner-contract correction

This hard base exists specifically to prevent the failure mode where each animation frame is independently regenerated. For sequential character animation, independent image regeneration is banned. Every frame must inherit the exact source raster and may only modify explicitly authorized local regions.

## Source contract

- Canvas: `1086 x 1448`
- Source SHA-256: `bd00c26373180a8678675dd9e7dc74a34c12899add8be246c82c6107b5f12d30`
- Output frames: 7
- Easing: `smootherstep`
- Render interpolation: `cubic`
- Runtime: NumPy + OpenCV + PyYAML

## Hard invariants

1. Every frame is sampled directly from frame 0.
2. No cumulative frame-to-frame warp.
3. All regional fields are composed before one `cv2.remap`.
4. Region composition is order-invariant.
5. Hard editable masks are explicit.
6. Feathering is inward-only and cannot expand the editable envelope.
7. Pixels outside the editable union mask are restored byte-for-byte from the source.
8. Source size and SHA-256 are checked before execution.
9. OpenCL is disabled and OpenCV threads are pinned to 1 for reproducibility-oriented CPU execution.
10. Deformation is rejected when displacement, trajectory, line-preservation, or Jacobian QC gates fail.

## Measured PASS evidence

- Unit tests: `10 / 10 PASS`
- Two independent CPU runs: all 7 output PNG SHA-256 hashes were identical.
- `outside_changed_pixels`: `0` on every frame.
- Minimum line-energy ratio inside editable regions: `0.8654299187`
- Edge-density ratio range: `0.9988568162 .. 1.0254358388`
- Jacobian determinant over sequence: `0.2195022289 .. 1.9655720559`
- Maximum inverse displacement: `14.7313423157 px`
- Maximum control-point frame step: `4.587255 px`
- Maximum control-point discrete acceleration: `2.196025 px`

## Current semantic regions

- mouth smile arc
- left cheek lift
- right cheek lift
- left lower-eyelid response
- right lower-eyelid response

The current target is a restrained adult closed-mouth smile/smirk, preserving the character's hard identity rather than turning the expression into a generic happy-face redraw.

## Production rule

```text
FRAME_N = FRAME_0 + MEASURED_LOCAL_DEFORMATION
```

Never:

```text
PROMPT -> NEW FRAME -> NEW FRAME -> NEW FRAME
```

for a continuous character animation shot.

## Files

- `experiments/face_motion/r03/zorr_face_motion_engine_r03.py`
- `experiments/face_motion/r03/smile_source_config_r03.yaml`
- `experiments/face_motion/r03/test_zorr_face_motion_engine_r03.py`

## Boundary

This PASS closes the **hard-base smile primitive**. It does not claim that arbitrary facial acting or full-body animation is solved. Future primitives must inherit these invariants and QC gates; they are not allowed to fall back to independent redraws.
