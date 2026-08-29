# ZORR BLATT — HARD PROBLEM #001 / BASE POSE PRACTICE R01

STATUS = PRACTICE_READY
BASE_MAIN = d805242a8ba6e2b169c1216acd3df86b8f9ddd84
CUSTOM_CODE = 0

## Owner authority

Visual authority is the OWNER-locked clothed ZORR prototype recorded in issue #202:
SHA-256 `001167f34c0593246a60b96ea284d869965cea799b6aba6844c88f231f4075ce`.

## Global base-pose law

Every Tier-1 character starts from the same presentation state, not the same body:

- strict front;
- upright / at-attention;
- head and torso facing front;
- arms fully out of pockets and down alongside the body;
- hands fully visible and relaxed;
- balanced straight legs;
- no weapon / prop / FX;
- plain white background.

`COMMON BASE POSE != COMMON BODY`.

## Fresh ready-system verification

Existing `ZB_GEOMETRY_TRUTH_CORE_R02` was run unchanged.
Initial direct `pytest` invocation failed during collection because the package uses a standard `src/` layout and had not been installed/exposed on `sys.path`. No source defect was found and no code was changed. Correct reuse invocation `PYTHONPATH=src python -m pytest -q` produced `15 passed`; compileall also passed.

The package's existing mathematical contract remains the correct authority boundary:

`OBSERVATIONS -> FACTOR GRAPH -> MANIFOLD STATE -> WEIGHTED SOLVE -> NULLSPACE/OBSERVABILITY -> COVARIANCE -> TRUTH SERIALIZATION`.

Front-only hidden depth is not fabricated: unobservable Z coordinates remain `null` / `NOT_PROVEN`.

Existing r05 parametric driver and ARMS_DOWN proxy invariance were already freshly verified in issue #202: pose changes while topology, segment lengths, surface area/volume and rest-authority boundaries remain invariant within floating-point tolerance.

## Current ZORR truth boundary

LOCKED:
- OWNER visual identity/prototype;
- visible costume/hair/marking/silhouette evidence;
- global base presentation law;
- reuse of ready ARMS_DOWN semantic pose carrier.

NOT PROVEN:
- hidden body geometry under clothes;
- current character anatomical depth from this single front image;
- old r04 body candidate numbers as current OWNER canon.

Forbidden:
- importing old hypermuscular drift as current body authority;
- interpreting raw pixels as physical body coordinates;
- writing a replacement solver/rig/deformer when the ready ZORR geometry stack already provides the needed mechanics;
- any external aesthetic/style binding.

## First visual practice contract

The first visual candidate may change only the pose-dependent regions required to move both hands from pockets into the global arms-down base state. It must preserve identity, apparent build, facial geometry, hair mass, garment design, major garment silhouette, markings, colors and footwear. No weapon. White background.

Candidate is not canon until visual + structural QC passes.

## Learning loop

`PRACTICE -> ANALYSIS -> CORRECTION -> NEXT PRACTICE`.

Every failed candidate must be classified and recorded before the next candidate. Chat remains result-only; GitHub is durable evidence and learning memory.
