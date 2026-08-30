# ZORR BLATT — PERSPECTIVE GEOMETRY MASTER R01

TRACKER = #222
BRANCH = `research/zorr-studio-mathematics-r01`
BASE_MAIN = `b18ca6b9cce2dce6fe304ca8ae36c05df4f4dcb1`
RESEARCH_PARENT_HEAD = `d051d3e48c1bab0dd5b40e1432653ffdd1505a20`
STATUS = RESEARCH / ADVANCED PERSPECTIVE MATHEMATICS
MAIN_MUTATION = NO
MERGE = NO
CANON_LOCK = NO
PRODUCTION_THRESHOLDS = QC_PENDING / NOT PROVEN

## 0. PURPOSE

This slice deepens the durable pixel/perspective handoff into a reusable mathematical perspective system for ZORR production.

The target is not “draw convergence lines by eye”. The target is:

`PIXEL -> PROJECTIVE GEOMETRY -> CAMERA -> WORLD -> DIFFERENTIAL SCALE -> OBJECT PLACEMENT -> OCCLUSION -> TEMPORAL CAMERA -> UNCERTAINTY -> STYLIZED RESIDUAL -> QC`

Perspective is treated as a measurable mapping, not a visual guess.

Operational law remains:

`DEFINE -> MEASURE -> CALCULATE -> APPLY -> VERIFY -> RECORD`

---

# 1. SOURCE / OSS GATE

Fresh upstream inspection for this slice selected OpenCV as the mature OSS geometry/calibration implementation to reuse rather than creating a ZORR RANSAC/PnP/calibration framework.

Upstream:

```text
repository = opencv/opencv
branch = 5.x
inspected ref = 390c4fdcb9fea6e58fb635bf88277f2a51e8d4b3
version header = 5.1.0-dev
license = Apache-2.0
```

Relevant inspected upstream paths:

```text
modules/geometry/doc/solvePnP.markdown
modules/geometry/src/solvepnp.cpp
modules/geometry/src/usac/
modules/geometry/test/test_solvepnp_ransac.cpp
doc/tutorials/calib3d/usac.markdown
modules/calib/src/calibration.cpp
modules/calib/src/multiview_calibration.cpp
modules/calib/test/test_cameracalibration.cpp
modules/calib/test/test_multiview_calib.cpp
```

OpenCV 5.x documentation describes PnP as minimizing 3D->2D reprojection error, includes P3P/AP3P/EPnP/IPPE/SQPnP, RANSAC PnP and LM/VVS refinement. The current USAC implementation provides robust homography/fundamental/essential/PnP estimation with multiple samplers, scores and local optimization methods. The current multiview calibration path performs per-camera intrinsics, pairwise registration, then global optimization.

ZORR rule:

```text
robust homography -> OpenCV USAC where suitable
PnP -> OpenCV solvePnP / solvePnPRansac / refinement
camera calibration -> OpenCV calib module
fisheye model -> OpenCV fisheye path
multi-camera calibration -> OpenCV multiview path where the data actually supports it
```

Custom ZORR code is limited to scene semantics, coordinate binding, measurements, tests and production-specific QC.

Important reproducibility note from upstream USAC documentation: parallel USAC execution is not generally deterministic. Deterministic QC must not silently assume that parallel robust estimation is byte-for-byte reproducible.

---

# 2. PROJECTIVE SPACE — DO NOT THROW AWAY POINTS AT INFINITY

Euclidean 2D coordinates `(x,y)` are embedded in projective space `P^2` as homogeneous points:

```text
p = [x, y, 1]^T
```

but a valid projective point may also have:

```text
p = [a, b, 0]^T
```

which is an ideal point / point at infinity.

This matters directly for perspective. A 3D direction parallel to the image plane has an ideal vanishing point. It is not a numerical failure and must not be “repaired” by inventing a finite coordinate.

Projective equality is up to nonzero scale:

```text
p ~ lambda p, lambda != 0
```

Point-line incidence:

```text
l^T p = 0
```

Line through two points:

```text
l = p1 x p2
```

Intersection of two lines:

```text
p = l1 x l2
```

The same cross-product algebra works for finite and ideal points.

### Session correction

The first synthetic proof attempt used a camera with zero yaw. One horizontal world direction therefore produced `w=0` and an infinite vanishing point. Treating this as a finite-point requirement caused that first gate to fail. The correct projective lesson is:

`INFINITE VANISHING POINT != INVALID PERSPECTIVE`

The corrected finite-yaw proof was then used for a convenient screen visualization, but the master model must retain homogeneous ideal points.

---

# 3. PINHOLE CAMERA AS A PROJECTIVE MAP

World point:

```text
X_w = [X,Y,Z,1]^T
```

Camera matrix:

```text
P = K [R | t]
```

Projection:

```text
p ~ P X_w
```

with intrinsics:

```text
K = [[fx, s,  cx],
     [0,  fy, cy],
     [0,  0,   1]]
```

where:

```text
fx, fy = focal lengths in pixel units
s      = skew
cx,cy  = principal point
```

Camera rigid transform is an element of `SE(3)`:

```text
T_cw = [[R,t],
        [0,1]]
```

and:

```text
X_c = R X_w + t
```

Production rule:

`WORLD SIZE -> CAMERA -> PIXEL SIZE`

never:

`DEPTH -> HAND-WRITTEN SCALE FACTOR`.

---

# 4. VANISHING GEOMETRY

For a 3D direction `d`:

```text
v_h ~ K R d
```

where `v_h` must remain homogeneous until it is known that `w != 0`.

For two parallel world line families with directions `d1,d2`, their vanishing points define the vanishing line of the plane they span:

```text
l_inf = v1 x v2
```

For a plane with normal `n_c` in camera coordinates, the same vanishing line is obtained by projective duality:

```text
l_inf ~ K^{-T} n_c
```

This gives an objective consistency test:

```text
normalize(v1 x v2) ~= normalize(K^{-T} n_c)
```

up to sign.

For a ground plane this line is the horizon of that plane.

---

# 5. ORTHOGONAL DIRECTIONS AND THE IMAGE OF THE ABSOLUTE CONIC

Define:

```text
omega = K^{-T} K^{-1}
```

For vanishing points `v_i, v_j` generated by orthogonal world directions:

```text
v_i^T omega v_j = 0
```

This is more general than the earlier special-case formula:

```text
(v1-c) dot (v2-c) + f^2 = 0
```

The special formula requires assumptions such as equal focal lengths, zero skew and known principal point.

The `omega` formulation allows multiple orthogonality constraints to estimate or verify intrinsic parameters. This is the correct route when ZORR has several architectural axis families rather than one assumed square-pixel camera.

Truth boundary:

- an orthogonality constraint is only valid if the corresponding world directions are actually known to be orthogonal;
- apparent right angles in a stylized drawing are not proof of real orthogonality;
- insufficient constraints leave intrinsics underdetermined.

---

# 6. PLANAR HOMOGRAPHY

For a plane with coordinates `(U,V)`, image mapping is:

```text
p ~ H [U,V,1]^T
```

A homography has 8 degrees of freedom up to scale.

For the world ground plane `Y=0`, parameterized by `(X,Z)`:

```text
H_ground->image = K [r_X r_Z t]
```

where `r_X` and `r_Z` are the relevant columns of `R`.

Inverse perspective mapping:

```text
[X,Z,1]^T ~ H^{-1} [x,y,1]^T
```

Critical limit:

`ONE HOMOGRAPHY == ONE PLANE`

A staircase, wall, floor, tilted roof and character body cannot all be made metrically correct by one floor homography. Use piecewise planes or a full 3D model.

---

# 7. DIFFERENTIAL PERSPECTIVE — THE PART MOST DRAWING SYSTEMS IGNORE

A homography is nonlinear after dehomogenization. For image->plane map:

```text
phi(x,y) = (U(x,y), V(x,y))
```

its local Jacobian is:

```text
J_phi = [[dU/dx, dU/dy],
         [dV/dx, dV/dy]]
```

Local physical area represented by image area is:

```text
dA_world = |det(J_phi)| dA_image
```

Directional scale for a unit image direction `q`:

```text
s(q) = ||J_phi q||
```

Singular value decomposition:

```text
J_phi = U Sigma V^T
Sigma = diag(sigma_1, sigma_2)
```

provides the two principal local stretch factors.

Perspective anisotropy:

```text
kappa = sigma_max / sigma_min
```

`kappa = 1` is locally isotropic; large `kappa` means a pixel displacement corresponds to very different world distances depending on direction.

This suggests a stronger ZORR map for every usable surface pixel:

```text
PERSPECTIVE_TENSOR(x,y) = J_phi(x,y)
```

rather than only a scalar “depth”.

Second-order change may be measured from the Hessian of `phi` or gradients of `log |det J|` when a shot has extreme perspective.

---

# 8. METRIC TENSOR VIEW

For world-plane->image map `psi(U,V)`, with Jacobian `J_psi`, define:

```text
G = J_psi^T J_psi
```

`G` is the local pullback metric induced by screen distance.

For a small world displacement `dX`:

```text
||dp||^2 ~= dX^T G dX
```

This turns “foreshortening” into an actual quadratic form.

Applications:

- how many pixels a 10 cm movement generates at a given floor position;
- which world direction is most compressed;
- how far two feet must be separated in world units to read as a chosen pixel separation;
- whether a motion will be subpixel and visually disappear;
- local sampling requirements for textures and linework.

---

# 9. ROBUST HOMOGRAPHY ESTIMATION

For noisy/outlier-contaminated correspondences, do not fit a homography from arbitrary four hand-picked points and call it truth.

Use robust estimation, then inspect residuals and degeneracy.

Current OSS path:

```text
cv::findHomography / cv2.findHomography
USAC / MAGSAC where appropriate
```

Relevant residual:

```text
r_i = ||p_i - dehomogenize(H P_i)||
```

For bi-directional checking, use symmetric transfer error.

Degenerate configurations include insufficiently independent point geometry, for example collinearity.

ZORR should record at least:

```text
correspondence_count
inlier_count
inlier_ratio
median_reprojection_error_px
high-quantile_error_px
spatial_coverage
condition/degeneracy evidence
```

No universal numerical threshold is locked yet.

---

# 10. PnP — FULL 3D OBJECT / CHARACTER / PROP POSE

When a model has 3D landmarks and corresponding image landmarks, solve:

```text
argmin_{R,t} sum_i rho(
    ||p_i - project(K,R,t,X_i)||^2
)
```

Use mature PnP implementations rather than a ZORR solver.

OpenCV paths verified in the inspected upstream include:

```text
solvePnP
solvePnPRansac
solvePnPGeneric
solvePnPRefineLM
solvePnPRefineVVS
```

The current docs describe planar/non-planar initialization, P3P/AP3P/EPnP/IPPE/SQPnP and nonlinear refinement.

For character staging this enables:

```text
3D landmark rig
-> image landmarks
-> camera/object pose estimate
-> reprojection residual map
```

It is especially useful when the feet, pelvis, shoulders and head have known model-space relationships.

---

# 11. SINGLE-VIEW METROLOGY

A single frame can recover more than a horizon when enough independent scene constraints exist.

Possible constraints:

```text
parallelism -> vanishing points
orthogonality -> IAC constraints
known plane -> homography
known length -> metric scale on that plane
known vertical direction -> vertical VP
known object height -> scene scale relation
```

Cross-ratio is projectively invariant. For four collinear homogeneous points:

```text
CR(A,B;C,D)
```

is preserved under projective transformation. This is useful for transferring ratios along receding lines without pretending screen intervals are uniform.

But absolute metric reconstruction from one view always depends on sufficient metric evidence. Missing reference length / camera height / calibration remains `NOT PROVEN`.

---

# 12. LENS DISTORTION MUST BE SEPARATE FROM PERSPECTIVE

Pinhole perspective and lens distortion are different transformations.

A common radial+tangential model uses normalized camera coordinates `(x,y)`, `r^2=x^2+y^2`:

```text
radial = 1 + k1 r^2 + k2 r^4 + k3 r^6

x_d = x*radial + 2 p1 x y + p2(r^2 + 2x^2)
y_d = y*radial + p1(r^2 + 2y^2) + 2 p2 x y
```

Do not absorb barrel/pincushion distortion into a false focal length or bent perspective grid.

For wide/fisheye cameras use the appropriate camera model. Current OpenCV upstream contains dedicated fisheye calibration/pose paths.

For anime, a deliberate curvilinear/fisheye composition is a style transformation and must be tagged as such rather than “corrected” into a pinhole image by default.

---

# 13. MULTI-VIEW GEOMETRY

For two views of the same 3D point:

```text
x2^T F x1 = 0
```

where `F` is the fundamental matrix.

With calibrated cameras:

```text
E = K2^T F K1
```

and ideally:

```text
E = [t]_x R
```

Triangulation reconstructs 3D points from intersecting camera rays, followed by cheirality checking (`depth > 0`).

For many views, bundle adjustment solves a joint optimization:

```text
min_{camera params, 3D points}
    sum_{i,j} rho(||p_ij - project(theta_i, X_j)||^2)
```

This is the correct higher-level route for a shot sequence / camera reconstruction problem; not repeated independent frame guesses.

OpenCV 5.x inspected multiview calibration uses a three-stage structure: independent intrinsics, pairwise camera registration, then global optimization.

---

# 14. CAMERA MOTION LIVES ON SE(3), NOT IN EULER-LERP SPACE

For animation camera pose:

```text
T(t) in SE(3)
```

Instantaneous camera motion is a twist:

```text
xi(t) in se(3)
```

Discrete update:

```text
T_{k+1} = exp( xi_hat * dt ) T_k
```

This avoids treating rigid camera rotation/translation as unrelated scalar channels.

For rotation-only interpolation, quaternions or `SO(3)` exponential/log maps are preferable to naive Euler-angle interpolation when continuity matters.

Perspective for animation therefore becomes:

```text
p(t) ~ K(t) [R(t)|t(t)] X(t)
```

and image velocity is:

```text
dp/dt = J_X dX/dt + J_camera dtheta/dt
```

This lets ZORR distinguish object motion from camera-induced optical flow.

---

# 15. ROLLING SHUTTER / TIME-VARYING PROJECTION

For a rolling-shutter sensor, different image rows may correspond to different exposure times:

```text
t_row = t0 + alpha * y
```

then:

```text
p ~ K [R(t_row)|t(t_row)] X
```

A single global homography/PnP pose may therefore be mathematically insufficient for fast motion.

This remains a production-camera model only and should be used only when source evidence indicates rolling-shutter behavior.

---

# 16. OCCLUSION IS DEPTH ORDER, NOT A 2D OVERLAP GUESS

Two projected shapes can overlap in screen space while being separated in depth.

For a ray:

```text
r(lambda) = C + lambda d
```

visibility is determined by the nearest valid surface intersection:

```text
lambda_visible = min positive lambda
```

For rasterized 3D production this is the z-buffer principle.

For 2D staging with reconstructed planes, each surface hit should retain depth so occlusion order can be verified numerically.

---

# 17. PLACEMENT AS SET GEOMETRY

Let usable floor region be `F` and a character footprint at orientation `theta` be `B_theta`.

The set of valid anchor positions is morphological erosion / Minkowski-set logic:

```text
VALID_theta = F erode B_theta
```

Equivalently, an anchor is valid if the translated footprint is a subset of free space:

```text
x is valid iff (x + B_theta) subset F
```

This is stronger than testing one foot pixel.

With projective reconstruction, perform the footprint test in world-plane coordinates, then project the accepted result to the image.

---

# 18. UNCERTAINTY MUST TRAVEL THROUGH THE PERSPECTIVE MAP

If measured parameters have covariance:

```text
Sigma_x
```

and output is:

```text
y = f(x)
```

first-order propagation is:

```text
Sigma_y ~= J_f Sigma_x J_f^T
```

Therefore a 1 px landmark uncertainty near the horizon can produce much larger world-position uncertainty than the same 1 px near the camera.

For camera estimation, uncertainty sources include:

```text
landmark localization
line fitting
principal point assumption
focal estimate
lens distortion
plane model
manual semantic mask
pose solve
```

A perspective result should therefore be represented as:

```text
estimate + assumptions + residuals + uncertainty
```

not a naked scalar.

---

# 19. CONDITIONING / DEGENERACY

A mathematically valid equation can still be numerically useless when the problem is ill-conditioned.

Track singular values of design/Jacobian matrices:

```text
sigma_1 >= ... >= sigma_n
```

Condition number:

```text
kappa(A) = sigma_max / sigma_min
```

Large `kappa` means small measurement changes may cause large parameter changes.

ZORR implication:

- nearly parallel evidence lines can make a vanishing point extremely unstable;
- tiny image coverage makes calibration fragile;
- correspondences concentrated in one small region give poor global homography evidence;
- planar PnP has ambiguity modes that differ from general 3D PnP.

Always measure geometry coverage and conditioning before trusting a low reprojection error.

---

# 20. CHARACTER FORESHORTENING AS A MEASURABLE RATIO

For a body segment with 3D endpoints `X1,X2`:

```text
L_world = ||X2-X1||
L_px = ||project(X2)-project(X1)||
```

Define projected compression:

```text
c = L_px / L_world
```

This is location/orientation dependent.

A limb aligned toward the camera may have much smaller `c` than a same-length limb across the image plane.

Do not “correct” this by restoring anatomical screen length; that destroys perspective unless the shot deliberately uses stylized deformation.

---

# 21. ZORR STYLIZED PERSPECTIVE — PHYSICAL CORE + CONTROLLED RESIDUAL

Anime does not require every pixel to obey a literal pinhole camera. But deviation should be explicit.

Define physical projection:

```text
p_phys = Pi(K,R,t,X)
```

Define stylized projection:

```text
p_style = p_phys + Delta_style(X, semantic, shot, t)
```

`Delta_style` is not an excuse for arbitrary drift. It is a controlled residual field.

Possible hard/soft constraints:

```text
foot/contact anchors remain on the support plane
key architectural lines preserve selected VP families
occlusion order remains valid unless intentionally surreal
character identity/silhouette may receive bounded local deformation
face/hands may use controlled readability correction
motion residual should be temporally smooth unless impact requires discontinuity
```

A research energy can be written:

```text
E =
  lambda_reproj * E_reproj
+ lambda_vanish * E_vanish
+ lambda_contact * E_contact
+ lambda_occlusion * E_occlusion
+ lambda_scale * E_scale
+ lambda_temporal * E_temporal
+ lambda_style * E_style
```

All `lambda_*` values remain `UNKNOWN / QC_PENDING` until learned from approved ZORR evidence. This is a framework for reasoning, not a locked style recipe.

This is the central ZORR perspective concept:

`PHYSICALLY COHERENT BASE + EXPLICIT ART-DIRECTION RESIDUAL`

rather than either rigid photorealism or uncontrolled eyeballing.

---

# 22. PERSPECTIVE ERROR BUDGET

A useful decomposition is:

```text
E_total =
  E_input
+ E_semantic
+ E_line
+ E_intrinsic
+ E_distortion
+ E_pose
+ E_plane
+ E_projection
+ E_style
+ E_temporal
```

These terms should not be collapsed prematurely into one universal quality score.

Examples:

```text
E_line       = vanishing-line / segment angular residual
E_projection = landmark reprojection residual in px
E_plane      = support-plane inconsistency in world units
E_contact    = foot/support distance
E_temporal   = change in residual field across frames
```

Hard failures such as body-floor penetration can remain explicit constraints rather than being averaged away by a weighted score.

---

# 23. PERSPECTIVE CONFIDENCE CLASSES — RESEARCH CONVENTION ONLY

For future discussion, a perspective result may be tagged by evidence class. This is a research convention, not canon:

```text
CALIBRATED_MULTI_VIEW
  intrinsics/extrinsics from measured calibration or sufficiently constrained multi-view evidence

CALIBRATED_SINGLE_VIEW
  single-view reconstruction with explicit independent metric/projective constraints

PROJECTIVE_SINGLE_VIEW
  vanishing geometry/homography recovered but absolute metric scale unresolved

ARTIST_DECLARED
  horizon/VP/camera parameters intentionally declared by production

UNPROVEN
  insufficient evidence; no numerical physical claim
```

Never upgrade a class by confidence rhetoric alone.

---

# 24. SYNTHETIC PROOF R01

A deterministic synthetic exercise was run in-session using NumPy plus OpenCV robust homography estimation.

Executable artifact SHA-256:

```text
0514de56fbf379a925950f6420a78aece106bd035991cb222fc813f3f485a03f
```

Synthetic camera:

```text
raster = 1920 x 1080
fx = fy = 900 px
camera center = (1.6, 2.2, -4.0)
target = (-0.8, 0.45, 7.0)
```

Measured finite-yaw vanishing points:

```text
VP_X = (5134.0323, 399.6091) px
VP_Z = (760.7785, 399.6091) px
horizon y = 399.6091 px
```

The same 1.8-world-unit vertical segment placed at increasing depth projected to:

```text
Z=1.5  -> 271.0052 px
Z=4.0  -> 193.7364 px
Z=7.5  -> 138.4706 px
Z=12.0 -> 101.3141 px
```

No manual scale multiplier was used.

Robust homography exercise:

```text
24 correspondences
4 deliberately injected gross outliers
OpenCV USAC_MAGSAC
20 / 24 inliers
all 4 injected outliers rejected
median recovered-model error to clean projection = 0.43557 px
```

Exact projective consistency checks:

```text
ground image->world->image round-trip max error = 3.0665e-14 world units
orthogonal-VP IAC residual = 8.8818e-16
horizon primal/dual residual = 0.0
```

PASS gates:

```text
all_injected_outliers_rejected = PASS
median_homography_error_lt_1px = PASS
roundtrip_lt_1e-9 = PASS
orthogonal_vp_residual_lt_1e-10 = PASS
horizon_duality_lt_1e-10 = PASS
equal_height_shrinks_with_depth = PASS
```

These thresholds are synthetic numerical self-test gates, not production ZORR style thresholds.

---

# 25. WHAT “PERSPECTIVE FROM DUNCAN” NOW MEANS

For a new ZORR scene, do not begin with a horizon sketch. Begin with the evidence graph:

```text
1. exact raster/hash
2. identify plane/3D evidence
3. detect or receive line/landmark correspondences
4. preserve homogeneous points, including ideal VPs
5. estimate vanishing geometry robustly
6. estimate/verify K only from sufficient constraints
7. model lens distortion separately
8. solve plane homography or full pose
9. map pixel <-> world
10. compute Jacobian/SVD/area/anisotropy fields
11. construct object footprint / 3D landmarks
12. project object from world geometry
13. verify contact/clearance/occlusion
14. propagate uncertainty
15. if art direction bends geometry, store Delta_style explicitly
16. for animation, carry camera/object state through time on SE(3)
17. record residuals, assumptions and unresolved scale
```

This is the new perspective discipline.

---

# 26. NEXT RESEARCH EDGES

Highest-value extensions after this slice:

1. **Ideal-point-safe vanishing estimator** — retain homogeneous VPs instead of forcing finite coordinates.
2. **Uncertainty map** — per-pixel covariance from line/VP/camera uncertainty.
3. **Multi-plane environment reconstruction** — floor + walls + stairs + roofs with plane adjacency constraints.
4. **Character support solver** — feet/footprint/world-height -> full projected character envelope.
5. **Perspective tensor QC** — local SVD / anisotropy / pixel-density maps.
6. **SE(3) camera trajectory** — temporal projection and continuity verification.
7. **Stylized residual learning** — measure where approved ZORR shots intentionally depart from the physical base.
8. **Changed/unseen transfer test** — apply the system to a different location instead of tuning to the original fortress frame.

---

# TERMINAL STATE

```text
PERSPECTIVE_GEOMETRY_MASTER_R01 = PASS
SYNTHETIC_PROJECTIVE_PROOF = PASS
OPEN_SOURCE_INSPECTION = PASS
OPEN_SOURCE_SELECTED = OpenCV
UPSTREAM_REF = 390c4fdcb9fea6e58fb635bf88277f2a51e8d4b3
UPSTREAM_VERSION = 5.1.0-dev
UPSTREAM_LICENSE = Apache-2.0
REAL_ZORR_CHANGED_SCENE_TRANSFER = NOT PROVEN
UNIVERSAL_STYLE_THRESHOLDS = NOT PROVEN
PHYSICAL_SCALE_WITHOUT_REFERENCE = NOT PROVEN
MAIN_MUTATION = NO
MERGE = NO
CANON_LOCK = NO
```
