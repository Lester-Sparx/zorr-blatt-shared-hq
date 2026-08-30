# ZORR BLATT — BABYLON CAMERA PLACEMENT MATHEMATICS R02

TRACKER = #222
BRANCH = `research/zorr-studio-mathematics-r01`
BASE_MAIN = `b18ca6b9cce2dce6fe304ca8ae36c05df4f4dcb1`
RESEARCH_PARENT_HEAD = `5abb95c8d0496de8114149aa1f9f581ec934bbef`
STATUS = RESEARCH / MATHEMATICAL CAMERA PLACEMENT SPEC
MAIN_MUTATION = NO
MERGE = NO
CANON_LOCK = NO
PRODUCTION_THRESHOLDS = QC_PENDING / NOT PROVEN

## 0. PURPOSE

This document develops a strictly mathematical system for camera placement in Babylon.js.

The target is not:

`move camera until the frame looks approximately right`.

The target is:

`ART INTENT -> SCREEN TARGETS + WORLD CONSTRAINTS -> INVERSE CAMERA SOLVE -> BABYLON CAMERA STATE -> NATIVE REPROJECTION -> NUMERICAL VERIFICATION`.

Babylon.js remains the engine of record for transforms, view/projection matrices, viewport projection, rays, picking, bounding volumes, frustum tests and camera execution. ZORR mathematics is a constraint/optimization layer above those primitives, not a second 3D engine.

The operational law is:

`DEFINE -> MEASURE -> CALCULATE -> APPLY -> VERIFY -> RECORD`.

Evidence labels used below:

- `STANDARD` = projective / numerical / optimization mathematics.
- `SOURCE-DERIVED` = verified against Babylon.js 9.23.0 source.
- `DERIVED` = mathematical consequence of stated equations.
- `PROJECT` = proposed bounded ZORR research convention.
- `UNKNOWN` = must be measured from approved ZORR evidence; never invent.

---

# 1. SOURCE / OSS BOUNDARY

## 1.1 Babylon version inspected

`SOURCE-DERIVED`

```text
BabylonJS/Babylon.js
release = 9.23.0
release target commit = 38ed028f40722504a215002fbc2fa89a2c89cf5d
```

Relevant inspected source paths:

```text
packages/dev/core/src/Cameras/camera.pure.ts
packages/dev/core/src/Cameras/arcRotateCamera.pure.ts
packages/dev/core/src/Maths/math.vector.pure.ts
packages/dev/core/src/Maths/math.viewport.ts
packages/dev/core/src/Culling/ray.pure.ts
packages/dev/core/src/Culling/boundingInfo.ts
```

Verified native capabilities used by this research:

- perspective and orthographic camera modes;
- FOV in radians;
- vertical-fixed and horizontal-fixed FOV modes;
- `setFocalLength()` conversion to FOV;
- `projectionPlaneTilt`;
- normalized camera viewport;
- `getViewMatrix()`, `getProjectionMatrix()`, `getTransformationMatrix()`;
- left/right handed projection selection from `scene.useRightHandedSystem`;
- `ArcRotateCamera(alpha,beta,radius,target)` and camera limits;
- `targetScreenOffset`;
- `Vector3.Project` / `Vector3.Unproject`;
- picking rays / `pickWithRay` / multi-pick;
- bounding box / bounding sphere / frustum tests;
- ArcRotate camera collision radius and collision checks.

## 1.2 Reuse law

Do not create a ZORR replacement for:

```text
Babylon scene graph
Babylon transform matrices
Babylon camera projection
Babylon ray casting
Babylon frustum tests
Babylon bounding volumes
Babylon camera interpolation/collision
```

Custom work is limited to:

```text
SCREEN-TARGET DEFINITIONS
CONSTRAINT DEFINITIONS
OBJECTIVE FUNCTIONS
ANALYTIC INITIALIZATION
SOLVER GLUE
UNCERTAINTY / OBSERVABILITY
ZORR-SPECIFIC QC
```

---

# 2. CAMERA PLACEMENT IS AN INVERSE PROBLEM

## 2.1 Forward problem

`STANDARD`

Given:

```math
X_w \in \mathbb{R}^3
```

and camera state:

```math
\theta_c = (K,R,C)
```

compute its screen projection:

```math
p = \Pi(X_w;\theta_c).
```

For a pinhole camera:

```math
\tilde p \sim K R (X_w-C).
```

After dehomogenization:

```math
p=(u,v).
```

## 2.2 Inverse problem

Camera placement reverses the question.

Given desired screen evidence:

```math
Y^* = \{p_i^*, h_j^*, A_k^*, l_m^*, \nu_n^*, ...\}
```

find camera parameters:

```math
\theta_c^* = \arg\min_{\theta_c\in\Omega} E(\theta_c)
```

subject to hard constraints:

```math
g_a(\theta_c) \le 0,
```

```math
h_b(\theta_c) = 0.
```

This is a constrained nonlinear inverse-projection problem.

---

# 3. COORDINATE SYSTEMS MUST BE EXPLICIT

## 3.1 World coordinates

`PROJECT`

A ZORR scene calculation must declare one world convention before any solve.

For example:

```text
X = right
Y = up
Z = forward
world units = declared scene units
```

Do not silently assume that a mathematical derivation and a Babylon scene use the same handedness.

## 3.2 Camera coordinates

For canonical derivations in this document:

```math
X_c = R(X_w-C)
```

with:

```text
camera x = screen-right
camera y = screen-up in the analytic derivation
camera z = forward
```

Babylon's actual matrix conventions / viewport y orientation remain authoritative at execution time. Every solved state must be verified through Babylon native projection.

## 3.3 Pixel coordinates

For a camera viewport of absolute pixel size:

```math
W_v \times H_v
```

use:

```text
u = horizontal pixel coordinate
v = vertical pixel coordinate
```

and normalized screen coordinates:

```math
s_x = \frac{u}{W_v},\qquad s_y = \frac{v}{H_v}.
```

Screen targets should normally be stored in both pixel and normalized form so they transfer across render resolutions without discarding the primary pixel measurement.

---

# 4. BABYLON CAMERA PARAMETERIZATION

## 4.1 General camera

`STANDARD / PROJECT`

A free camera optimization can use:

```math
\theta_{free} =
[C_x,C_y,C_z,\; \omega_x,\omega_y,\omega_z,\; \eta_f,\; \delta_x,\delta_y,\; \tau]^T
```

where:

- `C` = camera center in world coordinates;
- `omega` = local SO(3) rotation perturbation, not Euler angles as the optimization state;
- `eta_f` = logarithmic focal/FOV parameter;
- `delta_x,delta_y` = optional projection/screen offsets;
- `tau` = optional projection-plane tilt.

The exponential/log parameterization avoids singular Euler-angle behavior in local optimization.

## 4.2 ArcRotate camera

`SOURCE-DERIVED`

Babylon `ArcRotateCamera` exposes:

```math
\theta_{arc} = [\alpha,\beta,r,T_x,T_y,T_z,fov,o_x,o_y]^T
```

where:

- `alpha` = longitudinal orbit angle;
- `beta` = latitudinal orbit angle;
- `r` = radius to target;
- `T=(T_x,T_y,T_z)` = target;
- `o=(o_x,o_y)` = target screen offset.

For the default Y-up case Babylon computes the camera offset:

```math
q(\alpha,\beta,r)
=
r
\begin{bmatrix}
\cos\alpha\sin\beta\\
\cos\beta\\
\sin\alpha\sin\beta
\end{bmatrix}.
```

Thus:

```math
C=T+q.
```

For optimization, replace raw radius by:

```math
r=e^{\rho}
```

so positivity is automatic.

Babylon's native lower/upper limits on alpha, beta, radius and target-Y are hard feasible-set constraints when enabled.

---

# 5. INTRINSICS FROM BABYLON FOV

## 5.1 Vertical-fixed FOV

`SOURCE-DERIVED + DERIVED`

Babylon's default perspective FOV mode is vertical-fixed.

For vertical FOV:

```math
\theta_y=fov,
```

pixel focal length is:

```math
f_y=\frac{H_v}{2\tan(\theta_y/2)}.
```

Assuming square pixels:

```math
f_x=f_y.
```

The implied horizontal FOV is:

```math
\theta_x=2\arctan\left(\frac{W_v}{2f_x}\right).
```

## 5.2 Horizontal-fixed FOV

If Babylon is in horizontal-fixed mode:

```math
f_x=\frac{W_v}{2\tan(\theta_x/2)},
```

then:

```math
f_y=f_x,
```

and:

```math
\theta_y=2\arctan\left(\frac{H_v}{2f_y}\right).
```

## 5.3 Intrinsic matrix

Canonical pinhole intrinsics:

```math
K=
\begin{bmatrix}
f_x&s&c_x\\
0&f_y&c_y\\
0&0&1
\end{bmatrix}.
```

Do not assume the effective principal point is always the viewport center if the scene deliberately uses camera screen offsets, oblique/tilted projection or a non-full viewport.

---

# 6. FORWARD PIXEL PROJECTION

For camera-space point:

```math
X_c=(X,Y,Z)^T,\qquad Z>0,
```

the canonical pinhole equations are:

```math
u=f_x\frac{X}{Z}+c_x,
```

```math
v=f_y\frac{Y}{Z}+c_y.
```

The final Babylon verification must use the actual engine path:

```text
camera.getViewMatrix()
camera.getProjectionMatrix()
camera.getTransformationMatrix()
camera.viewport.toGlobal(...)
Vector3.Project(...)
```

because that path includes Babylon handedness, projection mode, FOV mode, viewport mapping and projection-plane details.

`SOLVER MODEL != FINAL AUTHORITY`.

`BABYLON NATIVE REPROJECTION = FINAL NUMERICAL CHECK`.

---

# 7. SCREEN TARGET ALGEBRA

A camera objective should be constructed from explicit screen targets instead of one vague “composition score”.

## 7.1 Point target

For landmark `i`:

```math
p_i^*=(u_i^*,v_i^*).
```

Residual:

```math
r_{point,i}=
\begin{bmatrix}
(u_i-u_i^*)/W_v\\
(v_i-v_i^*)/H_v
\end{bmatrix}.
```

Examples:

```text
eye center
face center
foot contact point
weapon tip
architecture landmark
vanishing-point marker
```

## 7.2 Bounding box center

If projected bounds are:

```math
B=[u_{min},v_{min},u_{max},v_{max}],
```

then:

```math
c_B=\left(\frac{u_{min}+u_{max}}2,\frac{v_{min}+v_{max}}2\right).
```

Target residual is normalized like a point residual.

## 7.3 Projected height

```math
h_{px}=v_{bottom}-v_{top}.
```

Use a multiplicative residual:

```math
r_h=\log\frac{h_{px}}{h_{px}^*}.
```

This treats “twice too large” and “half too large” symmetrically in log scale.

## 7.4 Projected width

```math
r_w=\log\frac{w_{px}}{w_{px}^*}.
```

## 7.5 Projected area

For visible or projected area:

```math
r_A=\log\frac{A_{px}}{A_{px}^*}.
```

## 7.6 Screen angle

For a desired screen direction angle `phi*`:

```math
r_\phi=\operatorname{wrap}(\phi-\phi^*)/\pi.
```

## 7.7 Horizon / line target

For desired normalized line:

```math
l^*=[a^*,b^*,c^*]^T,
```

and sampled projected horizon points `p_j`, use signed point-line distances normalized by image diagonal:

```math
r_{line,j}=\frac{a^*u_j+b^*v_j+c^*}{\sqrt{a^{*2}+b^{*2}}\sqrt{W_v^2+H_v^2}}.
```

## 7.8 Safe-frame / margin target

For a protected projected bound and required margin `m`:

```math
r_{left}=\max(0,m-u_{min})/W_v,
```

```math
r_{right}=\max(0,u_{max}-(W_v-m))/W_v,
```

with analogous top/bottom terms.

## 7.9 Relative scale between subjects

For subjects `i,j`:

```math
r_{ratio}=\log\frac{h_i/h_j}{\gamma^*}.
```

This is stronger than setting both sizes independently when only their visual hierarchy matters.

---

# 8. DO NOT MIX UNITS INSIDE ONE ERROR FUNCTION

Raw quantities may be in:

```text
pixels
radians
world units
percent visibility
log-scale
```

They must not be added directly.

Two lawful paths are:

## 8.1 Explicit normalization

```math
\bar r_i = r_i/s_i
```

where `s_i` is a declared physical or screen scale.

## 8.2 Covariance / Mahalanobis normalization

If measurement covariance is known:

```math
E_i=r_i^T\Sigma_i^{-1}r_i.
```

This is preferable when landmark uncertainty differs across measurements.

---

# 9. ROBUST LOSS

Pure squared loss makes one bad measurement dominate the solve.

Use a robust penalty when screen anchors may contain annotation/noise error.

Huber loss:

```math
\rho_\delta(e)=
\begin{cases}
\frac12e^2,& |e|\le\delta\\
\delta(|e|-\frac12\delta),& |e|>\delta.
\end{cases}
```

Then:

```math
E_{soft}(\theta)
=
\sum_i w_i\rho\left(r_i(\theta)^T\Sigma_i^{-1}r_i(\theta)\right).
```

`UNKNOWN`: ZORR weights and robust-loss breakpoints are not universal truths. They must be calibrated from approved scene evidence or kept as explicit research parameters.

---

# 10. HARD CONSTRAINTS VS SOFT OBJECTIVES

A major design rule:

`A HARD PRODUCTION REQUIREMENT MUST NOT BE REPRESENTED ONLY BY A SMALL WEIGHT`.

## 10.1 Hard constraints

Examples:

```text
camera outside forbidden geometry
near/far clipping safety
foot support
protected face visible
required object fully inside frame
minimum camera clearance
camera alpha/beta/radius limits
fixed actor/world anchors
```

Represent as:

```math
g_j(\theta)\le0
```

or:

```math
h_k(\theta)=0.
```

## 10.2 Soft objectives

Examples:

```text
desired thirds placement
preferred negative-space balance
preferred focal length
preferred camera distance
minimal deviation from previous shot
soft lead room
soft symmetry/asymmetry target
```

These belong in the weighted objective.

## 10.3 Lexicographic solving

Instead of collapsing everything into one arbitrary scalar, use priority levels:

```text
LEVEL 0 = feasibility / safety / support / clip / critical visibility
LEVEL 1 = mandatory screen framing
LEVEL 2 = composition and negative space
LEVEL 3 = minimal camera change / lens regularization
LEVEL 4 = optional style preference
```

Solve a lower level only inside the feasible or near-optimal set of higher levels.

This reduces Goodhart behavior from one giant score.

---

# 11. ANALYTIC INVERSE SOLUTIONS — USE THEM AS SEEDS

Optimization should not start blindly when geometry supplies a direct solution.

## 11.1 Pixel -> camera ray

For target pixel:

```math
\tilde p=[u,v,1]^T,
```

camera-space ray direction is:

```math
d_c \propto K^{-1}\tilde p.
```

Normalize:

```math
\hat d_c=d_c/\|d_c\|.
```

World ray:

```math
\hat d_w=R^T\hat d_c.
```

Ray equation:

```math
X(\lambda)=C+\lambda\hat d_w.
```

Babylon's `Vector3.Unproject` or native picking-ray creation should be used to bind this to engine conventions.

## 11.2 Ray -> support plane

For plane:

```math
n^TX+d=0,
```

intersection parameter:

```math
\lambda
=
-\frac{n^TC+d}{n^T\hat d_w}.
```

World point:

```math
X^*=C+\lambda\hat d_w.
```

If:

```math
|n^T\hat d_w|\approx0,
```

the inverse is ill-conditioned / tends to infinity.

Correct response:

`NOT PROVEN / ADD CONSTRAINT`, not a guessed depth.

## 11.3 Put a floor-supported object under a requested screen point

If an object's support anchor must appear at pixel `p*`:

```text
1. unproject p* to a ray;
2. intersect ray with the floor/support plane;
3. place the support anchor at the resulting world point;
4. project through Babylon and verify pixel residual.
```

This is an exact geometric seed when the support plane is known.

## 11.4 Projected height -> depth approximation

For fronto-parallel object of world height `H`:

```math
h_{px}\approx f_y\frac{H}{Z}.
```

Thus:

```math
Z_0\approx f_y\frac{H}{h_{px}^*}.
```

This is only an initialization.

For a tilted body / arbitrary camera, solve the exact scalar equation:

```math
F(z)=\|\Pi(X_{top}(z))-\Pi(X_{bottom}(z))\|-h_{px}^*=0.
```

Use bracketed root finding when monotonicity on the chosen interval is established.

## 11.5 World direction -> centered camera orientation

For fixed camera center `C` and desired centered target `X_t`:

```math
f_w=\frac{X_t-C}{\|X_t-C\|}.
```

Construct camera rotation from:

```text
forward = f_w
chosen up constraint
right = normalize(forward x up)
corrected up = right x forward
```

This still leaves the chosen roll/up convention as a real constraint, not an implicit assumption.

## 11.6 World direction -> off-center target pixel

Desired camera ray:

```math
\hat d_c^*
=
\operatorname{normalize}(K^{-1}[u^*,v^*,1]^T).
```

World direction:

```math
\hat d_w=
\operatorname{normalize}(X_t-C).
```

Solve rotation satisfying:

```math
R\hat d_w=\hat d_c^*.
```

This constrains two rotational degrees of freedom. Roll remains free until an up/horizon/vertical constraint fixes it.

## 11.7 Camera pose from 3D <-> 2D correspondences

When enough non-degenerate world anchors and screen anchors exist, use mature PnP rather than inventing a ZORR pose solver.

The existing perspective master selects OpenCV `solvePnP` / `solvePnPRansac` / refinement for this case.

After solving:

```text
OpenCV pose -> declared coordinate conversion -> Babylon camera state -> Babylon reprojection
```

The conversion is not accepted until native Babylon reprojection matches the source screen evidence.

## 11.8 Planar reference frame

If all trusted anchors lie on one plane, the correct first model is a homography:

```math
p\sim HP.
```

Do not pretend planar evidence uniquely determines the whole 3D camera/world without additional assumptions.

---

# 12. ANALYTIC JACOBIAN OF PERSPECTIVE

For:

```math
u=f_xX/Z+c_x,
```

```math
v=f_yY/Z+c_y,
```

the projection Jacobian wrt camera-space position is:

```math
J_\pi
=
\frac{\partial(u,v)}{\partial(X,Y,Z)}
=
\begin{bmatrix}
f_x/Z & 0 & -f_xX/Z^2\\
0 & f_y/Z & -f_yY/Z^2
\end{bmatrix}.
```

This matrix is fundamental for:

```text
camera optimization
uncertainty propagation
screen sensitivity
condition analysis
motion-to-pixel mapping
```

Near small `Z`, sensitivity grows rapidly. Near inverse-depth degeneracy, world-depth uncertainty can explode even when pixel residual is small.

---

# 13. POSE JACOBIAN ON SE(3)

For a local pose perturbation:

```math
\delta\xi=[\delta t,\delta\omega]^T\in\mathbb{R}^6,
```

under one declared left-perturbation convention:

```math
\delta X_c\approx\delta t-[X_c]_\times\delta\omega.
```

Therefore:

```math
J_{pose}
=
J_\pi
\begin{bmatrix}
I & -[X_c]_\times
\end{bmatrix}.
```

Sign/order depends on the exact perturbation convention. Implementation tests must verify the analytic Jacobian against finite differences before it is trusted.

---

# 14. FOV JACOBIAN

For vertical-fixed FOV:

```math
f_y(\theta)=\frac{H_v}{2\tan(\theta/2)}.
```

Derivative:

```math
\frac{df_y}{d\theta}
=
-\frac{H_v}{4\sin^2(\theta/2)}.
```

Then:

```math
\frac{\partial u}{\partial\theta}
=
\frac{X}{Z}\frac{df_x}{d\theta},
```

```math
\frac{\partial v}{\partial\theta}
=
\frac{Y}{Z}\frac{df_y}{d\theta}.
```

This shows mathematically why very narrow FOV states can become highly sensitive.

---

# 15. ARCRENDER CAMERA DERIVATIVES

From Babylon's exact default Y-up offset:

```math
C=T+r
\begin{bmatrix}
\cos\alpha\sin\beta\\
\cos\beta\\
\sin\alpha\sin\beta
\end{bmatrix},
```

we obtain:

```math
\frac{\partial C}{\partial\alpha}
=
r
\begin{bmatrix}
-\sin\alpha\sin\beta\\
0\\
\cos\alpha\sin\beta
\end{bmatrix},
```

```math
\frac{\partial C}{\partial\beta}
=
r
\begin{bmatrix}
\cos\alpha\cos\beta\\
-\sin\beta\\
\sin\alpha\cos\beta
\end{bmatrix},
```

```math
\frac{\partial C}{\partial r}
=
\begin{bmatrix}
\cos\alpha\sin\beta\\
\cos\beta\\
\sin\alpha\sin\beta
\end{bmatrix},
```

and:

```math
\frac{\partial C}{\partial T}=I.
```

These derivatives provide strong analytic seeds for camera sensitivity and local optimization.

For custom Babylon `upVector`, use the actual native view transform or insert the corresponding alignment rotation before applying this derivative model.

---

# 16. OBSERVABILITY — CAN THE REQUEST EVEN DETERMINE A CAMERA?

A solver must not confuse “optimizer returned a number” with “camera state is identifiable”.

## 16.1 Single point

One 2D point provides two scalar constraints.

A 6-DOF pose plus FOV has more unknowns than that.

Therefore:

`ONE SCREEN POINT != UNIQUE CAMERA`.

## 16.2 Planar evidence

Planar correspondences strongly constrain homography but not arbitrary 3D structure without further assumptions.

## 16.3 Focal length / distance coupling

For approximately fronto-parallel subjects:

```math
h_{px}\approx fH/Z.
```

Thus many `(f,Z)` pairs can produce similar framing.

Lens preference or another geometric constraint is required.

## 16.4 Missing roll evidence

A single target direction does not uniquely fix camera roll.

Need one of:

```text
world up
horizon target
vertical line family
explicit roll target
```

## 16.5 Jacobian rank

Let stacked residual Jacobian be:

```math
J=\frac{\partial r}{\partial\theta}.
```

Check:

```math
rank(J).
```

If the rank is below the number of locally free parameters, the state is locally underdetermined.

## 16.6 Conditioning

Use singular values:

```math
J=U\Sigma V^T.
```

Condition ratio:

```math
\kappa=\frac{\sigma_{max}}{\sigma_{min}}.
```

A very small minimum singular value means the solution is fragile along at least one parameter direction.

No universal ZORR cutoff is claimed here.

---

# 17. CAMERA FEASIBILITY CONSTRAINTS

## 17.1 Near/far clip

For protected point camera depth `z_i`:

```math
z_i > z_{near}+\delta_n,
```

```math
z_i < z_{far}-\delta_f.
```

Margins are project/QC parameters, not universal constants.

## 17.2 Frustum visibility

For objects required fully visible, use Babylon's own bounding/frustum mechanisms as final verification, e.g. full bounding volume in the active camera frustum when that geometric approximation is appropriate.

## 17.3 Camera collision / clearance

Camera center must remain outside forbidden geometry.

A generic signed-distance hard constraint is:

```math
\phi(C)\ge r_c,
```

where:

- `phi` = signed distance to obstacle surface;
- `r_c` = declared camera clearance.

Babylon ArcRotate also provides native collision checks and collision radius. Native collision outcome remains part of verification.

## 17.4 Subject support

For foot/support point `X_f` and support plane:

```math
n^TX_f+d=0.
```

Numerically:

```math
|n^TX_f+d|\le\epsilon_{support}.
```

The character footprint must also lie inside the valid support region.

---

# 18. OCCLUSION IS NON-SMOOTH — DO NOT FAKE A GRADIENT

For protected surface sample points `q_k`, define binary visibility:

```math
I_k=
\begin{cases}
1,&\text{first ray hit is the protected target}\\
0,&\text{otherwise}
\end{cases}.
```

Visibility fraction:

```math
\nu=\frac1N\sum_{k=1}^N I_k.
```

Required visibility:

```math
\nu\ge\nu_{min}.
```

Babylon native ray/picking APIs are suitable for the exact verification layer.

Because hard ray visibility changes discontinuously at silhouette boundaries, do not pretend this objective is globally differentiable.

Recommended solve pattern:

```text
1. optimize smooth projection/framing objectives;
2. use soft projected-overlap/depth proxies only if useful;
3. run exact Babylon ray visibility;
4. reject/refine candidates that violate protected visibility;
5. record exact visibility evidence.
```

---

# 19. OCCLUSION GRAPH

For camera `c`, create directed graph:

```math
G_{occ}^{(c)}=(V,E).
```

Edge:

```math
A\to B
```

means `A` occludes a measured part of `B` from the current camera.

Useful edge attributes:

```text
occluded pixel area
occluded percentage
protected-region overlap
nearest depth gap
screen bounding intersection
```

This turns “the sword blocks the face” into measurable scene evidence.

---

# 20. SCREEN OCCUPANCY AND NEGATIVE SPACE

Let:

```math
O(u,v)\in[0,1]
```

be screen occupancy / visual-mass field.

Let:

```math
N(u,v)\in[0,1]
```

be a protected negative-space field.

Overlap penalty:

```math
E_{neg}
=
\frac{1}{W_vH_v}
\sum_{u,v}N(u,v)O(u,v).
```

This allows a camera solve to preserve deliberate empty space rather than maximizing object fill.

For an importance field `I(u,v)`, information centroid is:

```math
c_I=
\frac{\sum_{u,v}I(u,v)[u,v]^T}{\sum_{u,v}I(u,v)}.
```

A target centroid can be a soft composition objective.

No universal “best centroid” is claimed.

---

# 21. LEAD ROOM / LOOK ROOM

Suppose a projected face/motion direction is unit vector:

```math
d_s\in\mathbb{R}^2.
```

Define a foreground screen point `p` and boundary distances in `+d_s` and `-d_s` directions:

```math
L_+=distance(p,frame,+d_s),
```

```math
L_-=distance(p,frame,-d_s).
```

A project-specific lead-room constraint can be:

```math
L_+ \ge \gamma L_-.
```

`UNKNOWN`: gamma is an art-direction parameter and must not be universalized without approved ZORR evidence.

---

# 22. MULTI-SUBJECT CAMERA SOLVE

For subjects `i=1,...,n`, solve a joint residual vector containing:

```text
screen centers
screen heights
relative scale ratios
minimum pair separation
protected visibility
depth order
negative-space fields
```

Depth-order hinge for “A must be in front of B”:

```math
r_{depth}
=
\max(0,z_A+m-z_B).
```

If actor positions are allowed to move on a floor plane, augment the unknown vector:

```math
\theta=
[\theta_{camera}, U_1,V_1, ..., U_n,V_n].
```

But only free actor variables explicitly authorized by the staging problem. Otherwise the solver may hide a bad camera by moving the whole scene.

---

# 23. PROJECTED-SIZE SOLVER

A high-value Babylon utility is:

`world object + desired screen height -> camera/world depth candidate`.

## 23.1 Exact definition

For top/bottom world anchors:

```math
h(\theta)=
\|\Pi(X_t;\theta)-\Pi(X_b;\theta)\|.
```

Target:

```math
h(\theta)=h^*.
```

## 23.2 One-dimensional ArcRotate radius solve

If target, alpha, beta and FOV are fixed and only radius is free:

```math
F(r)=h(r)-h^*=0.
```

Solve on Babylon's permitted radius interval:

```math
r\in[r_{min},r_{max}].
```

Use a bracketed method if a sign change / monotonic interval is verified.

## 23.3 Why this is strong

This produces exact scene framing such as:

```text
character = 620 px tall
face = 180 px tall
door = 410 px tall
weapon = 52% of frame width
```

while preserving the chosen camera angle and target.

---

# 24. CAMERA TARGET-OFFSET SOLVER

Babylon `ArcRotateCamera` exposes `targetScreenOffset` and applies it in the view matrix.

This creates a useful separation:

```text
orbit geometry = alpha/beta/radius/target
composition offset = targetScreenOffset
```

Research strategy:

```text
1. solve physical orbit geometry first;
2. use targetScreenOffset for bounded framing correction if desired;
3. keep the offset magnitude visible in the report;
4. do not use it to conceal wrong world placement or support.
```

A large offset is evidence that the physical camera/orbit may be poorly conditioned for the requested framing.

No universal maximum offset is claimed.

---

# 25. CAMERA LENS REGULARIZATION

A framing solver can often trade distance against FOV.

To prevent arbitrary extreme lenses, define a soft prior around a chosen reference FOV `theta_0`:

```math
r_{fov}
=
\log\frac{\tan(\theta/2)}{\tan(\theta_0/2)}.
```

This operates on perspective scale rather than raw degrees.

`theta_0` is a shot/art-direction input, not a universal ZORR law.

---

# 26. MINIMAL-CAMERA-MOTION REGULARIZER

If solving from previous accepted camera `T_0`:

```math
\Delta T=T_0^{-1}T.
```

Use Lie-log displacement:

```math
\xi=\log(\Delta T)\in\mathfrak{se}(3).
```

Regularizer:

```math
E_{move}=\xi^TW\xi.
```

This favors the smallest camera change that satisfies the new shot without forcing the camera to remain unchanged.

---

# 27. TEMPORAL CAMERA SOLVE

For camera sequence:

```math
T_0,T_1,...,T_N\in SE(3),
```

frame objectives become:

```math
E_{frame}=\sum_t E_{screen}(T_t).
```

Velocity regularizer:

```math
E_v=\sum_t\|\log(T_t^{-1}T_{t+1})\|^2.
```

Acceleration / jerk can be approximated in the Lie algebra or from sampled position/orientation trajectories.

For position:

```math
v_t\approx\frac{C_{t+1}-C_t}{\Delta t},
```

```math
a_t\approx\frac{C_{t+1}-2C_t+C_{t-1}}{\Delta t^2},
```

```math
j_t\approx\frac{a_{t+1}-a_t}{\Delta t}.
```

Candidate smoothness penalty:

```math
E_j=\sum_t\|j_t\|^2.
```

Intentional anime camera snaps are represented as explicit discontinuity/keyframe permissions, not solver accidents.

---

# 28. SCREEN-SPACE TEMPORAL STABILITY

World-smooth camera motion does not guarantee screen-smooth subject motion.

For protected landmark projection `p_t`:

```math
\dot p_t\approx\frac{p_{t+1}-p_t}{\Delta t}.
```

Track:

```text
screen velocity
screen acceleration
screen jerk
```

This enables a camera path that keeps a face visually stable even while both camera and actor move in world space.

---

# 29. UNCERTAINTY PROPAGATION

If a measured screen landmark has covariance:

```math
\Sigma_p,
```

and world/camera quantity is locally:

```math
y=f(p),
```

then:

```math
\Sigma_y\approx J\Sigma_pJ^T.
```

For fitted camera parameters with local weighted least squares:

```math
\Sigma_\theta
\approx
\sigma^2(J^TWJ)^{-1}
```

when local-model assumptions are justified.

Near a rank-deficient or badly conditioned solve, this covariance becomes large. That is useful evidence, not a reason to suppress the warning.

For strongly nonlinear cases, use bounded Monte Carlo propagation rather than falsely precise first-order intervals.

---

# 30. PERSPECTIVE TENSOR FOR CAMERA STAGING

For a ground/support-plane inverse map:

```math
(U,V)=H^{-1}(u,v),
```

local Jacobian:

```math
J_H(u,v)=
\frac{\partial(U,V)}{\partial(u,v)}.
```

SVD:

```math
J_H=U\Sigma V^T.
```

with:

```math
\Sigma=diag(\sigma_1,\sigma_2).
```

Local anisotropy:

```math
\kappa_p=\frac{\sigma_{max}}{\sigma_{min}}.
```

This tells the camera-placement system how strongly one pixel direction corresponds to a different world-space scale from another at the selected screen location.

Camera staging can use this to avoid regions where tiny pixel errors imply huge world-position uncertainty.

---

# 31. PHYSICAL BASE VS ANIME ART DIRECTION

Do not force every ZORR shot to remain photographically neutral.

Separate:

```math
p_{phys}=\Pi(X;\theta_{phys})
```

from an intentional style residual:

```math
p_{style}=p_{phys}+\Delta_{style}.
```

The report should store both:

```text
PHYSICAL REPROJECTION ERROR
STYLE RESIDUAL
```

A deliberate residual may be used for:

```text
hero scale exaggeration
controlled perspective compression
graphic horizon manipulation
screen-space target offset
selective composition distortion
```

but it must not silently hide:

```text
foot/support failure
wrong depth order
unintended face occlusion
broken character construction
camera inside geometry
unexplained temporal jump
```

---

# 32. FULL CAMERA OBJECTIVE

A generic research objective may be written:

```math
E(\theta)=
E_{anchor}
+E_{size}
+E_{ratio}
+E_{line}
+E_{negative}
+E_{composition}
+E_{continuity}
+E_{regularization},
```

subject to:

```math
\mathcal C_{support}(\theta)=true,
```

```math
\mathcal C_{clip}(\theta)=true,
```

```math
\mathcal C_{frustum}(\theta)=true,
```

```math
\mathcal C_{collision}(\theta)=true,
```

```math
\mathcal C_{visibility}(\theta)=true.
```

But the actual implementation should preserve residual vectors and priority classes; a single final scalar is only a solver device, not the semantic truth of the shot.

---

# 33. SOLVER PIPELINE

## Stage 0 — declare the problem

Record:

```text
render width/height
camera viewport
Babylon handedness
camera class
FOV mode
current camera state
fixed scene anchors
free variables
hard constraints
soft targets
uncertainties
```

## Stage 1 — analytic seed

Prefer:

```text
ray-plane intersection
current ArcRotate state
projected-size depth estimate
Babylon zoom/focus fit where sufficient
homography
PnP
vanishing geometry
```

before generic numerical search.

## Stage 2 — smooth local solve

Optimize differentiable residuals with an established nonlinear least-squares / trust-region / LM / L-BFGS implementation rather than inventing a solver.

## Stage 3 — enforce explicit parameter bounds

Examples:

```text
alpha interval
beta interval
radius interval
FOV interval
camera region
floor actor regions
```

## Stage 4 — exact non-smooth verification

Run native:

```text
ray/picking visibility
collision
bounding/frustum
clip tests
```

## Stage 5 — Babylon reprojection

For every protected anchor:

```text
project through actual Babylon matrices and viewport
compare to requested screen target
```

## Stage 6 — observability / uncertainty

Record:

```text
Jacobian rank
singular values / condition evidence
parameter uncertainty where justified
near-degenerate variables
```

## Stage 7 — report

Never return only “camera solved”.

Return the state plus evidence.

---

# 34. NON-CONVEXITY AND MULTI-START

Camera objectives are generally non-convex because of:

```text
occlusions
rotational periodicity
multiple possible sides of a subject
FOV/distance tradeoffs
scene obstacles
local composition minima
```

Use bounded multi-start when necessary:

```text
1. analytic seeds;
2. a small declared set of alternate seeds;
3. local optimization per seed;
4. discard hard-constraint failures;
5. compare surviving residual vectors/Pareto tradeoffs;
6. Babylon native verify;
7. retain top candidates for directing choice.
```

Do not use unbounded brute-force search.

---

# 35. PARETO CAMERA CHOICE

Some camera goals genuinely conflict.

Example:

```text
larger face
more architecture visible
less perspective distortion
more negative space
shorter camera move
```

A single arbitrary weighted sum may hide the tradeoff.

Maintain Pareto set:

```math
\mathcal P=\{\theta:\nexists\theta'\text{ that improves every declared objective}\}.
```

Then directing chooses among mathematically non-dominated candidates.

This is preferable to pretending mathematics can infer final dramatic intent.

---

# 36. DATA CONTRACT FOR A CAMERA TARGET

`PROJECT`

Each target should minimally contain:

```text
id
type
source world anchor / geometry
requested screen value
unit
viewport binding
hard_or_soft
priority class
uncertainty/covariance if known
weight only after normalization
provenance
```

Example conceptual structure:

```json
{
  "id": "hero_face_center",
  "type": "screen_point",
  "world_anchor": "CHAR_A.face_center",
  "target_px": [1180, 335],
  "hard_or_soft": "soft",
  "priority": 1,
  "sigma_px": [2.0, 2.0],
  "provenance": "approved_layout"
}
```

Values above are illustrative schema examples, not ZORR production thresholds.

---

# 37. CAMERA SOLVE REPORT

`PROJECT`

A result should contain:

```text
input scene/camera identifiers
input source hashes/versions where relevant
Babylon version/ref
handedness
viewport
camera class
camera state before
camera state after
free variables
hard constraints
soft targets
per-target residuals in px and normalized units
visibility measurements
frustum result
collision result
support result
Jacobian rank / singular-value evidence
uncertainty intervals where justified
Babylon-native reprojection residual
style residual if any
solver termination reason
NOT-PROVEN boundaries
```

---

# 38. PROPOSED CAMERA TARGET FAMILIES FOR ZORR

These are mathematical target families, not artistic laws.

## 38.1 Close-up

Candidate measurable quantities:

```text
face projected height
face center
left/right eye line screen angle
top/bottom margin
face visibility
negative space around gaze direction
```

## 38.2 Full body

```text
foot contact pixels
head pixel
body projected height
silhouette visibility
floor support
body-frame margins
```

## 38.3 Duel / two-subject shot

```text
both centers
relative scale ratio
depth ordering
minimum silhouette separation
look-room fields
weapon visibility
shared horizon / ground support
```

## 38.4 Hero architecture

```text
vertical-line target
horizon target
building screen area
foreground/background depth cues
protected negative space
camera clip/clearance
```

## 38.5 Moving chase shot

```text
time-varying subject screen position
subject screen velocity
camera velocity/acceleration/jerk
occlusion continuity
lead-room inequality
minimum collision clearance
```

---

# 39. BABYLON-SPECIFIC HIGH-VALUE REUSE

## 39.1 Native projection

Use Babylon `Vector3.Project` for final screen coordinates.

## 39.2 Native unprojection

Use Babylon `Vector3.Unproject` for screen-to-world ray construction when suitable.

## 39.3 Native view/projection

Use camera's actual:

```text
getViewMatrix()
getProjectionMatrix()
getTransformationMatrix()
```

for final truth.

## 39.4 Native viewport

Use camera viewport converted to absolute render dimensions.

## 39.5 Native rays

Use Babylon ray/picking system for exact line-of-sight checks.

## 39.6 Native bounds/frustum

Use bounding information and camera frustum where that approximation answers the requirement.

## 39.7 ArcRotate geometry

Exploit `alpha,beta,radius,target,targetScreenOffset` directly instead of mapping an unconstrained generic pose into ArcRotate after the fact when the production camera is actually ArcRotate.

---

# 40. CAMERA DESIGN AS A CONSTRAINT MANIFOLD

The feasible camera space is not all of `R^n`.

Define:

```math
\mathcal M_c
=
\{\theta\mid g_j(\theta)\le0,\ h_k(\theta)=0\}.
```

Screen objectives define level sets over that manifold.

Camera placement becomes:

```math
\theta^*
=
\arg\min_{\theta\in\mathcal M_c}E(\theta).
```

This view is useful because it distinguishes:

```text
IMPOSSIBLE SHOT
UNDERDETERMINED SHOT
MULTIPLE VALID SHOTS
NUMERICALLY FRAGILE SHOT
UNIQUE WELL-CONDITIONED SHOT
```

rather than reducing every failure to “optimizer did not converge”.

---

# 41. IMPOSSIBILITY CERTIFICATES

A mature camera solver should be able to return a mathematical blocker.

Examples:

```text
REQUIRED SUBJECT HEIGHT + FOV RANGE + CAMERA REGION = INFEASIBLE
FACE VISIBILITY + FIXED ACTOR POSITIONS + FIXED CAMERA SIDE = INFEASIBLE
CAMERA CLEARANCE + REQUIRED ANGLE = INFEASIBLE
PIXEL TARGET RAY PARALLEL TO SUPPORT PLANE = DEPTH NOT IDENTIFIABLE
JACOBIAN RANK DEFICIENT = CAMERA NOT UNIQUELY DETERMINED
```

This is more valuable than silently relaxing constraints.

---

# 42. SENSITIVITY MAP FOR DIRECTING

After a solution, compute how each camera parameter changes important screen targets:

```math
S_{ij}=\frac{\partial y_i}{\partial\theta_j}.
```

Interpretation:

```text
large |S_ij| = tiny camera change strongly changes target i
small |S_ij| = target i is insensitive to parameter j
```

This can tell a director/artist which control is safest to adjust without destroying locked framing.

Example:

```text
radius strongly changes body height
alpha strongly changes horizontal overlap
beta strongly changes horizon/foreshortening
FOV strongly changes perspective compression and projected size
screen offset changes framing without changing orbit geometry
```

These are qualitative examples; the actual derivatives come from the shot.

---

# 43. AUTOMATIC “SAFE ADJUSTMENT” DIRECTIONS

Let protected targets have Jacobian:

```math
J_p.
```

A small camera update `delta theta` that preserves them approximately satisfies:

```math
J_p\delta\theta\approx0.
```

The null space:

```math
\mathcal N(J_p)
```

contains local camera directions that minimally disturb protected locks.

This gives a powerful directing tool:

> move the camera only in directions that preserve the face framing and foot contact to first order.

A desired secondary adjustment gradient `g_s` can be projected into this null space:

```math
\delta\theta
=
P_{\mathcal N}(-g_s).
```

This is a high-value application of linear algebra to interactive camera editing.

---

# 44. ACTIVE-SET CAMERA EDITING

When some constraints become tight, define active set:

```math
\mathcal A=\{j:g_j(\theta)\approx0\}.
```

The allowed local edit direction must satisfy:

```math
\nabla g_j^T\delta\theta\le0,
\qquad j\in\mathcal A.
```

This supports camera gizmos that “slide along” a valid boundary instead of breaking floor, collision or framing locks.

---

# 45. REFERENCE-FRAME CAMERA RECONSTRUCTION -> BABYLON

For a 2D reference image:

```text
1. measure pixel landmarks;
2. detect/fit perspective geometry;
3. recover homography or camera pose where identifiable;
4. bind known world dimensions/planes;
5. solve scale if a real reference exists;
6. convert pose into Babylon handedness/camera parameterization;
7. create Babylon camera candidate;
8. reproject known landmarks with native Babylon matrices;
9. minimize residual;
10. preserve deliberate style residual separately.
```

This directly connects the existing ZORR pixel/perspective research to Babylon scene layout.

---

# 46. REQUIRED VALIDATION PROGRAM

The mathematical system is not production-proven until it survives changed scenes.

## Gate A — synthetic exact geometry

Known camera/world -> project targets -> recover camera -> compare ground truth.

Measure:

```text
position error
orientation error
FOV error
pixel reprojection RMS
pixel max error
```

## Gate B — Babylon-native agreement

For the same camera state:

```text
independent analytic projection
vs
Babylon Vector3.Project
```

must agree within justified numerical tolerance.

## Gate C — inverse ray agreement

Known pixel/support plane -> unproject/intersect -> reproject.

## Gate D — ArcRotate derivative finite-difference test

Compare analytic derivatives with finite differences.

## Gate E — changed scene

Use an unseen scene/layout, not the scene used to tune the solver.

## Gate F — non-smooth checks

Verify visibility/frustum/collision through Babylon native systems.

## Gate G — style residual

Confirm intentional art-direction residual is stored separately and does not alter hard physical/support constraints silently.

---

# 47. CURRENT STATUS / NON-CLAIMS

This document is a mathematical research specification.

It DOES establish:

```text
camera-placement variable definitions
screen-target residual families
hard/soft constraint separation
analytic inverse seeds
projection/pose/FOV/ArcRotate Jacobians
observability requirements
uncertainty model
occlusion/frustum/support verification model
Babylon native reuse boundary
solver/verification sequence
```

It does NOT yet prove:

```text
production effectiveness on a real ZORR Babylon scene
universal ZORR composition weights
universal screen tolerances
universal visibility thresholds
universal FOV preferences
changed-scene transfer
final Babylon runtime implementation
```

Those remain:

`NOT PROVEN / QC_PENDING`.

---

# 48. NEXT MATHEMATICAL SLICE

Highest-value next bounded experiment:

`BABYLON_CAMERA_SOLVER_PROOF_R03`

with one synthetic Babylon-compatible scene and one changed scene.

Required proof:

```text
1. construct known ArcRotate camera + world anchors;
2. project anchors to exact target pixels;
3. perturb camera;
4. recover alpha/beta/radius/target/FOV under declared bounds;
5. verify with Babylon-native projection;
6. run protected visibility/frustum checks;
7. compute Jacobian rank/conditioning;
8. report residuals instead of subjective PASS;
9. transfer to a second unseen arrangement.
```

Only after this should project-specific camera acceptance tolerances be calibrated.
