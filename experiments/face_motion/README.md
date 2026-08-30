# ZORR Pixel Face Motion Engine — Hard Base R01

Status: deterministic prototype, tested on the current front portrait.

## Why this exists

Per-frame image generation caused identity jitter: canvas size, crop, hair, scar, earrings, jacket geometry, face width and lighting drifted between frames. This engine replaces that workflow with deterministic local pixel deformation of one locked source raster.

## Hard invariants

1. One source raster is authoritative for the sequence.
2. Source width/height are checked before processing.
3. Optional SHA-256 pin prevents using the wrong source revision.
4. Only explicitly editable face masks may change.
5. Pixels outside those masks are restored byte-for-byte from the source.
6. Expression motion is defined as pixel displacement of control anchors.
7. Every frame is computed from the same source, never from the previous rendered frame. This prevents cumulative warp drift.
8. Frame timing is an explicit t schedule plus easing.
9. QC hard-fails if any pixel outside the editable masks changes.
10. No generative model is required for interpolation.

## OSS-first stack

- OpenCV 4.x: `cv.remap` for deterministic geometric remapping. OpenCV 4.5+ is Apache-2.0 licensed.
  - https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html
  - https://opencv.org/license/
- NumPy: RBF field construction and linear solve; modified BSD license.
  - https://numpy.org/about/
- PyYAML: readable anchor/mask/frame configuration.

The engine implements a small Gaussian radial-basis displacement solver locally instead of depending on a face-landmark ML model. For stylized anime faces, manual measured anchors remain authoritative. Automated landmark detection can be added later only as an optional proposal layer, never as the identity source of truth.

## Current smile proof

Source: 1086x1448 PNG, SHA-256 pinned in `smile_source_config_v2.yaml`.

Output: seven separate PNG frames including the untouched source frame.

Sequence:

`neutral -> micro transition -> quarter -> half -> three-quarter -> near target -> target closed smile`

The target is a controlled adult closed smile, not a new independently redrawn face.

Current deformation families:

- mouth arc / corner lift;
- small cheek lift;
- subtle lower-eyelid response;
- explicit local boundary locks.

QC result on the current proof: `outside_changed_pixels = 0` on all seven frames.

## Architecture

`SOURCE LOCK -> CONTROL ANCHORS -> EASING -> LOCAL INVERSE RBF FIELD -> cv.remap -> FEATHERED REGION COMPOSITE -> HARD OUTSIDE-MASK RESTORE -> PIXEL DIFF QC -> PNG`

Each frame is evaluated directly from frame 0. Do not chain `frame N -> frame N+1`.

## Next hardening steps

- add a small anchor-authoring helper for measured coordinates;
- add region-overlap QC and maximum-displacement limits;
- add mouth/eye motion presets as data, not code;
- add deterministic PNG metadata manifest and frame-to-frame motion report;
- extend the same engine to blink, eye shift, jaw clench, controlled rage microexpression and cloth micro-motion;
- keep image generation out of the interpolation loop.
