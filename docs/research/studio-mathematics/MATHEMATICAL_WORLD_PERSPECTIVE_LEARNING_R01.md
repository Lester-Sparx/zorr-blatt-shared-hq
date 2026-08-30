# ZORR BLATT — MATHEMATICAL WORLD / PIXEL / PERSPECTIVE LEARNING R01

TRACKER = #222
BRANCH = `research/zorr-studio-mathematics-r01`
BASE_MAIN = `b18ca6b9cce2dce6fe304ca8ae36c05df4f4dcb1`
RESEARCH_PARENT_HEAD = `8757420490afeb4530b1a44e4652bc4a82eecd40`
STATUS = RESEARCH / DURABLE LEARNING HANDOFF
MAIN_MUTATION = NO
MERGE = NO
CANON_LOCK = NO

## 0. PURPOSE

This document exists so later ZORR chats/agents can restore the mathematics learned in the 2026-08-30 pixel/perspective session without rebuilding it from chat memory.

It is **not canon authority**, **not a style lock**, and **not a production threshold specification**. It is a mathematical research handoff under tracker #222.

Required restore order remains:

`CURRENT MAIN -> ZORR_EXECUTION_CONSTITUTION.md -> AGENTS.md -> TRACKER #222 -> THIS HANDOFF`

The operational law is:

`DEFINE -> MEASURE -> CALCULATE -> APPLY -> VERIFY -> RECORD`

The central correction learned in this session is:

`VISUAL ESTIMATE != MEASUREMENT`

For quantitative image work, measurements must be reproducible in code where practical.

---

# 1. PIXEL SPACE IS THE PRIMARY MEASUREMENT SPACE

For a raster image:

```text
I(x,y) = [R,G,B,A]
x in [0, W-1]
y in [0, H-1]
origin = top-left
```

Always record exact raster size first:

```text
TOTAL_PIXELS = W * H
```

Normalized coordinates are derived only after pixel measurement:

```text
u = x / (W - 1)
v = y / (H - 1)
```

Do not replace measured pixels with vague language such as “roughly centered”, “a bit far”, or “large enough” when the decision is quantitative.

---

# 2. THREE DIFFERENT FORMS OF “EMPTY SPACE”

The session established that “empty pixels” must be split into distinct mathematical objects.

## 2.1 Geometric free space

A semantic/geometry mask:

```text
F_geo(x,y) in {0,1}
```

where `1` means the image position belongs to a surface usable for placement under the declared scene model.

For a floor example:

```text
F_geo = FLOOR_MASK AND NOT OCCLUDER_MASK
```

This requires semantic calibration. Edge detection alone does not prove floor/obstacle identity.

## 2.2 Visual empty / low-information space

A separate image-statistics quantity. One reproducible energy form is:

```text
E(x,y) = sqrt(
    G_norm(x,y)^2
  + S9_norm(x,y)^2
  + S31_norm(x,y)^2
  + Dedge_norm(x,y)^2
) / 2
```

where:

- `G` = luminance gradient magnitude;
- `S9`, `S31` = local luminance standard deviation at two scales;
- `Dedge` = local edge density.

A threshold may be selected from the frame by an objective method such as Otsu rather than invented by eye.

`VISUAL_EMPTY != GEOMETRIC_FREE`.

## 2.3 Perspective-correct physical free area

Image pixels do not represent equal physical areas on a receding plane.

For image-to-plane homography `H`:

```text
(U,V) = dehomogenize(H * [x,y,1]^T)
```

Local physical area represented by one image pixel is:

```text
dA_world = |det(J_H(x,y))| * dA_image
```

Therefore:

```text
A_free_world = sum over free pixels of |det(J_H(x,y))|
```

and not merely `count(free_pixels)`.

---

# 3. LOCATION CASE — PIXEL DECOMPOSITION R02

Exact source image SHA-256:

`313967e83237397b1035a3c254123d0c8570de1110585fc79e6df440cd9cb0ea`

Raster:

```text
W = 941 px
H = 1672 px
TOTAL = 1,573,352 px
W/H = 0.562799043
9:16 deviation = +0.053163%
```

A conservative floor/occluder model was built in code. The rear floor boundary was snapped to measured image-gradient evidence inside a bounded calibration corridor; foreground masonry was conservatively over-covered by explicit polygons; shadows remained floor rather than being treated as obstacles.

Measured under that exact R02 mask:

```text
GEOMETRIC_FREE = 1,081,593 px = 68.744502%
GEOMETRIC_BLOCKED = 491,759 px = 31.255498%
STRICT_5PX_FREE = 1,057,346 px = 67.203398%
VISUAL_EMPTY = 1,034,199 px = 65.732207%
QUIET_AND_GEOMETRIC_FREE = 782,998 px = 49.766232%
```

Maximum Euclidean clearance in image space:

```text
CENTER = (453, 854) px
RADIUS = 454 px
```

Largest axis-aligned rectangle fully inside the R02 free mask:

```text
x = [0, 811]
y = [438, 1407]
size = 812 x 970 px
area = 787,640 px
```

Rear boundary support check:

```text
median gradient on boundary /
median gradient at +/-4 px
= 3.866253x
```

## R02 truth boundary

`PASS` meant deterministic image-space mask construction and declared numerical gates passed for this exact raster and calibration.

It did **not** mean external semantic ground truth was available.

The foreground architecture mask contained conservative manually calibrated polygons. Any later session must retain that distinction.

The earlier chat-only estimate `69.434% free` was superseded by the code-derived R02 model and must not be reused as a measured result.

---

# 4. PERSPECTIVE CASE — PROJECTIVE GEOMETRY R03

The floor contains two strong line families. Long structural segments were detected and clustered by orientation, then deterministic vanishing-point fitting was applied.

Measured vanishing points:

```text
VP_A = (-527.255, 181.929) px
VP_B = (2331.979, -61.238) px
```

Evidence:

```text
family A: 36 / 38 inliers
median angular residual = 0.2556 deg

family B: 25 / 37 inliers
median angular residual = 0.4008 deg
```

Horizon:

```text
y(left)   = 137.088 px
y(center) = 97.116 px
y(right)  = 57.145 px
image horizon roll ~= -4.861 deg
```

## 4.1 Camera assumptions

The R03 calibration is conditional on:

```text
square pixels
zero skew
principal point = raster center
floor line families are orthogonal in the scene
pinhole camera
negligible lens distortion for this frame
```

Under these assumptions, with principal point `c` and orthogonal vanishing points `v1,v2`:

```text
(v1 - c) dot (v2 - c) + f^2 = 0
```

hence:

```text
f = sqrt( - (v1-c) dot (v2-c) )
```

Measured conditional camera model:

```text
f ~= 1127.291 px
HFOV ~= 45.309 deg
VFOV ~= 73.121 deg
camera depression relative to floor ~= 33.131 deg
```

Do not reinterpret these as externally calibrated real-camera truth. They are the internally consistent pinhole solution under the assumptions above.

---

# 5. IMAGE PIXEL -> FLOOR COORDINATE

With camera matrix `K`, normalized floor directions `d1,d2` and floor normal `n`, use:

```text
H_floor_to_image = K [d1 d2 n]
H_image_to_floor = inverse(H_floor_to_image)
```

For one image pixel:

```python
p = np.array([x, y, 1.0])
q = H_image_to_floor @ p
U, V = q[:2] / q[2]
```

The session used plane normalization `n dot X = 1`, so `(U,V)` are measured in **camera-height units**.

If real camera height is later established as `Hc`, then:

```text
U_real = U * Hc
V_real = V * Hc
A_real = A_normalized * Hc^2
```

No real meter scale may be claimed while `Hc` is unknown.

---

# 6. PERSPECTIVE SCALE IS NOT CONSTANT

At image center `x = 470 px`, the measured normalized floor area represented by one pixel changed strongly with depth:

```text
y=450  -> 4.402111e-05 Hc^2 / px
y=500  -> 2.959252e-05 Hc^2 / px
y=650  -> 1.145872e-05 Hc^2 / px
y=800  -> 5.579159e-06 Hc^2 / px
y=1000 -> 2.633128e-06 Hc^2 / px
y=1200 -> 1.445017e-06 Hc^2 / px
y=1400 -> 8.766183e-07 Hc^2 / px
y=1600 -> 5.712148e-07 Hc^2 / px
```

Thus a pixel near `y=450` represents about `77x` the floor area of a pixel near `y=1600` under the R03 model.

This is the key production rule:

`100 px FAR != 100 px NEAR`

For the full R02 geometric-free mask, Jacobian integration under R03 gave:

```text
A_free_normalized ~= 8.922710 Hc^2
```

Again, this is conditional on both the R02 mask and R03 camera model.

---

# 7. CHARACTER / OBJECT PLACEMENT MUST USE WORLD->CAMERA PROJECTION

For a floor contact position `P_f = (U_f,V_f)`:

```text
X_f = n + U_f d1 + V_f d2
```

If an object's physical height is represented as `q * Hc`, its top may be constructed along the floor normal and then projected:

```text
X_top = X_f - q n
p_floor ~ K X_f
p_top   ~ K X_top
```

The pixel height is derived from projection:

```text
h_px = ||p_top - p_floor||
```

Do not use a hand-written rule such as “farther = multiply scale by 0.7” when camera geometry is available.

For collision/placement, define a footprint/body geometry in floor/world space, project it, and test against obstacle/depth/clearance constraints.

---

# 8. CANON -> MATHEMATICAL CONSTRAINTS, NOT INVENTED PHYSICS

A user-supplied canon-interface artifact was inspected in this session:

```text
file family = ZORR_UNIVERSE_CANON_MASTER
version = R03
source SHA-256 = 3f2e514b2bf37e3a9596a591197c0d357a07393ef22407ef0925cbf9ddb90859
claims = 95
entities = 17
```

Its internal status counts were:

```text
LOCKED = 40
OBSERVED = 18
OPEN = 22
QUARANTINE = 14
SUPERSEDED = 1
```

This research document does not elevate that uploaded artifact into repository canon authority. Future chats must fresh-read the current authoritative canon source before applying canon-specific mathematics.

The transferable mathematical lesson is an epistemic state algebra:

```text
state(c) in {LOCKED, OBSERVED, OPEN, QUARANTINE, SUPERSEDED}
```

Use one-hot/categorical state, **not invented truth probabilities**.

Admissibility rule:

```text
LOCKED      -> objective constraint may enter world model
OBSERVED    -> story evidence/sample; do not promote automatically
OPEN        -> symbolic unknown; do not assign a value
QUARANTINE  -> retain historically; exclude from active world equations
SUPERSEDED  -> inactive
```

Core law:

`OPEN != INVENT`

---

# 9. FACETS / DEVELOPMENT MUST NOT BE COLLAPSED TO ONE POWER NUMBER

The inspected canon interface explicitly rejected a universal numeric Facet ladder/count/max.

Therefore the safe mathematical representation is a **family of state spaces**:

```text
for each developing element e:
    FacetState(e) in F_e
```

with no required identity:

```text
F_A != F_B    # allowed
```

Do not invent:

```text
POWER_LEVEL(character) = scalar
```

unless later explicit canon establishes such a quantity.

Possible future mathematics, once evidence exists:

- partial orders;
- graphs of transitions;
- manifolds/state spaces;
- multi-objective capability vectors;
- stochastic transition models.

None is canon merely because it is mathematically convenient.

---

# 10. UNKNOWN CHRONOLOGY / TRANSPORT STAY SYMBOLIC

When absolute chronology is unknown, use a partial order:

```text
E_i < E_j
```

only when evidence establishes precedence.

Do not invent calendar timestamps.

When transport physics is unknown, use a symbolic function:

```text
travel_time(P_i, P_j; theta_transport)
```

with:

```text
theta_transport = OPEN
```

Do not invent FTL velocity, metric, fuel law, or travel-time constants to make equations numerically complete.

---

# 11. PRODUCTION MATHEMATICS IS NOT LORE

The following are production models unless canon separately says otherwise:

## Camera / projection

```text
p ~ K [R|t] X
p ~ H P              # plane
```

## Motion

```text
q(t)
v(t) = dq/dt
a(t) = d2q/dt2
j(t) = d3q/dt3
```

## Constraints

```text
g(q,t) = 0
h(q,t) >= 0
```

## Cloth / deformation continuum form

```text
rho * d2x/dt2 = div(sigma) + f_external
```

## Rendering equation

```text
L_o = L_e + integral( f_r * L_i * cos(theta) d_omega )
```

These equations may improve animation/rendering/QC. They do not silently define ZORR cosmology.

---

# 12. COMPOSITION CAN BE MEASURED AS MULTIPLE MASS FIELDS

A separate anime-reference screenshot was measured in-session.

Source screenshot SHA-256:

`d3fe289a7fb247840e701fe59b1e870438190b53d7fc200646645d19863f1c60`

Screenshot raster:

```text
866 x 547 px
```

A nominal player viewport was measured as:

```text
x = 24..853
y = 44..481
830 x 438 = 363,540 px
```

However this viewport contains **player UI overlays** (dropdowns/arrows). Therefore its numerical outputs are useful as a measurement-method exercise but **must not be treated as a clean anime-frame style benchmark**.

Measured screenshot-viewport values included:

```text
luminance entropy = 7.1933 bits
information centroid normalized ~= (0.5565, 0.4849)
dark-mass centroid normalized ~= (0.4590, 0.5000)
information mass right/left ~= 1.4397
information mass bottom/top ~= 0.8350
```

Transferable lesson:

A composition need not satisfy `LEFT_MASS == RIGHT_MASS`.

Different visual fields can compensate:

```text
information_mass
ink/dark_mass
color_mass
face/saliency_mass
edge_density
negative_space
```

A more useful balance model is a multi-field moment system, for example:

```text
M_k = integral rho_k(x,y) * (r - r0) dA
```

for visual field `k`.

Dynamic equilibrium may exist even when individual fields are asymmetric.

But future style measurements require a clean source frame or an explicitly verified UI-exclusion mask.

---

# 13. CODE-FIRST PERSPECTIVE KERNEL

Minimal reusable equations:

```python
import numpy as np
import math


def focal_from_orthogonal_vps(v1, v2, principal_point):
    v1 = np.asarray(v1, float)
    v2 = np.asarray(v2, float)
    c = np.asarray(principal_point, float)
    s = -float((v1 - c) @ (v2 - c))
    if s <= 0:
        raise ValueError("No real focal solution under the stated assumptions")
    return math.sqrt(s)


def homography_project(H, x, y):
    q = np.asarray(H, float) @ np.array([x, y, 1.0])
    return q[:2] / q[2]


def homography_jacobian(H, x, y):
    H = np.asarray(H, float)
    a,b,c = H[0]
    d,e,f = H[1]
    g,h,i = H[2]

    den = g*x + h*y + i
    num_u = a*x + b*y + c
    num_v = d*x + e*y + f

    du_dx = (a*den - g*num_u) / den**2
    du_dy = (b*den - h*num_u) / den**2
    dv_dx = (d*den - g*num_v) / den**2
    dv_dy = (e*den - h*num_v) / den**2

    return np.array([
        [du_dx, du_dy],
        [dv_dx, dv_dy],
    ])


def area_scale(H_image_to_plane, x, y):
    J = homography_jacobian(H_image_to_plane, x, y)
    return abs(np.linalg.det(J))
```

These are generic projective-geometry helpers, not a new ZORR framework.

---

# 14. FUTURE CHAT BOOT RULES FROM THIS LEARNING

A future mathematics chat working on image/location/staging should follow this sequence:

1. **Record the exact input hash and raster dimensions.**
2. **Define coordinate origin, axes, units and mask semantics.**
3. **Separate geometric-free, visual-empty and perspective/world-space area.**
4. **Use code for quantitative values.**
5. **If perspective exists, detect/fit vanishing geometry or use known camera calibration.**
6. **State camera assumptions explicitly.**
7. **Use homography/Jacobian for planar physical scale.**
8. **Derive character/object pixel size from projection when possible.**
9. **Keep semantic masks tagged as manual / model-derived / externally verified.**
10. **Do not turn a deterministic self-check into external ground truth.**
11. **Do not convert OPEN canon into numerical constants.**
12. **Do not collapse multi-dimensional systems into one universal score without evidence.**
13. **Do not learn style metrics from screenshots contaminated by UI without an exclusion mask.**
14. **Record exact PASS scope and unresolved assumptions.**

---

# 15. PASS / NOT-PROVEN BOUNDARIES

## PASS — bounded learning slice

The following mathematical lessons are established for reuse:

- pixel-first measurement;
- deterministic raster accounting;
- explicit semantic-mask separation;
- distance-transform clearance;
- projective vanishing-point geometry;
- homography image<->plane mapping;
- Jacobian perspective-area correction;
- camera-scale normalization by unknown camera height;
- projection-derived object scale;
- categorical canon-state algebra;
- OPEN values remain symbolic;
- element-specific state spaces instead of an invented universal Facet scalar;
- multiple visual-mass fields for composition analysis;
- explicit contamination/assumption tracking.

## NOT PROVEN / must not be generalized

- R02 semantic free mask as external ground truth;
- R03 pinhole parameters as independently calibrated physical-camera truth;
- real metric floor dimensions without real camera height or another scale reference;
- universal ZORR style thresholds from one reference image;
- clean anime-frame composition statistics from the UI-contaminated screenshot;
- any new cosmological/transport/development mechanic not present in current canon authority;
- any production quality improvement until tested on changed/unseen ZORR work.

---

# 16. NEXT MATHEMATICAL RESEARCH EDGE

The next high-value continuation for this line is not another hand-picked scalar threshold. It is to generalize the proven geometry into reusable verification on changed/unseen ZORR scenes:

```text
INPUT FRAME
-> HASH / RASTER
-> SURFACE / OCCLUDER EVIDENCE
-> VANISHING GEOMETRY OR CALIBRATED CAMERA
-> IMAGE<->WORLD MAP
-> CLEARANCE / SCALE / OCCLUSION
-> OBJECT PLACEMENT
-> REPROJECT
-> NUMERICAL ERROR
-> RECORD
```

For animation, extend the same system through time:

```text
X(t) -> project(X(t)) -> clearance(t) -> occlusion(t) -> timing/trajectory error
```

For clothing and secondary motion, use measured kinematics/deformation rather than frame-by-frame unstructured guessing.

For composition/color/style, first create clean input/reference masks and then measure multiple fields rather than invent one “quality score”.

---

# TERMINAL STATE

```text
MATHEMATICAL_WORLD_PERSPECTIVE_LEARNING_R01 = PASS
DURABLE_HANDOFF = YES
MAIN_MUTATION = NO
MERGE = NO
CANON_LOCK = NO
EXTERNAL_SEMANTIC_GROUND_TRUTH = NOT PROVEN
PHYSICAL_METRIC_SCALE = NOT PROVEN
UNIVERSAL_STYLE_THRESHOLDS = NOT PROVEN
```
