# ZORR BLATT — BABYLON CAMERA OPTIMIZATION ADVANCED R02A

TRACKER = #222
BRANCH = `research/zorr-studio-mathematics-r01`
STATUS = RESEARCH / ADVANCED OPTIMIZATION ADDENDUM
MAIN_MUTATION = NO
MERGE = NO
CANON_LOCK = NO
PRODUCTION_THRESHOLDS = UNKNOWN / QC_PENDING

This addendum deepens `BABYLON_CAMERA_PLACEMENT_MATHEMATICS_R02.md` beyond the basic inverse-projection formulation.

The research target is a mathematically diagnosable camera system that can distinguish:

```text
FEASIBLE
INFEASIBLE
UNDERDETERMINED
ILL-CONDITIONED
MULTI-MODAL
LOCALLY OPTIMAL
PARETO-NONDOMINATED
ROBUST UNDER UNCERTAINTY
FRAGILE UNDER UNCERTAINTY
```

instead of returning only “camera found / camera not found”.

---

# 1. CONSTRAINED OPTIMIZATION / KKT STRUCTURE

For camera variables `theta`:

```math
\min_\theta E(\theta)
```

subject to:

```math
g_j(\theta)\le0,
```

```math
h_k(\theta)=0.
```

Lagrangian:

```math
\mathcal L(\theta,\lambda,\mu)
=
E(\theta)
+
\sum_j\lambda_jg_j(\theta)
+
\sum_k\mu_kh_k(\theta).
```

First-order KKT conditions for a regular local optimum:

```math
\nabla_\theta\mathcal L=0,
```

```math
g_j(\theta)\le0,
```

```math
h_k(\theta)=0,
```

```math
\lambda_j\ge0,
```

```math
\lambda_jg_j(\theta)=0.
```

This gives a useful interpretation for camera staging: active constraint multipliers quantify which hard boundaries are currently controlling the shot.

A large active multiplier is a local “shadow price”: tightening that constraint further has high objective cost.

No universal magnitude threshold is claimed.

---

# 2. GAUSS-NEWTON / LEVENBERG-MARQUARDT STRUCTURE

If soft objective is residual vector:

```math
r(\theta)\in\mathbb R^m,
```

and:

```math
E(\theta)=\frac12r^TWr,
```

Jacobian:

```math
J=\partial r/\partial\theta.
```

Gauss-Newton local system:

```math
(J^TWJ)\delta
=
-J^TWr.
```

Levenberg-Marquardt / trust damping:

```math
(J^TWJ+\lambda D)\delta
=
-J^TWr.
```

This is natural for camera framing because many targets are screen-space residuals.

The normal matrix:

```math
\mathcal I=J^TWJ
```

also acts as a local information matrix for observability analysis.

---

# 3. ROBUST IRLS

For robust losses, use iterative reweighted least squares rather than pretending all points are Gaussian-perfect.

For residual scalar `e_i`, robust weight:

```math
w_i^{rob}=\psi(e_i)/e_i
```

where:

```math
\psi=\rho'.
```

Then solve weighted least squares with:

```math
W_{eff}=W_{measurement}W_{robust}.
```

This preserves a least-squares numerical structure while reducing the leverage of bad annotations.

---

# 4. NULL-SPACE SOLVE FOR PROTECTED LOCKS

Suppose high-priority protected screen constraints linearize to:

```math
J_p\delta\theta=0.
```

Let columns of `N` span:

```math
Null(J_p).
```

Then every first-order lock-preserving edit is:

```math
\delta\theta=Nz.
```

For secondary residual Jacobian `J_s` and residual `r_s`, solve reduced problem:

```math
\min_z\|J_sNz+r_s\|^2.
```

This is stronger than giving protected targets very large weights: it mathematically removes first-order directions that would break them.

Applications:

```text
preserve face center while changing architecture coverage
preserve foot contact while changing FOV
preserve two-character scale ratio while changing negative space
preserve horizon while orbiting camera
```

---

# 5. ACTIVE-SET INEQUALITY EDITING

For currently tight inequalities:

```math
g_a(\theta)=0,
```

allow only local edits satisfying:

```math
\nabla g_a^T\delta\theta\le0.
```

Examples:

```text
camera just touching clearance boundary
subject just touching safe-frame boundary
minimum face visibility currently active
minimum radius active
```

An interactive camera tool could project user intent onto the tangent cone of feasible directions.

This converts “camera snaps back because you broke a limit” into “camera slides along the mathematically valid boundary”.

---

# 6. SECOND-ORDER / REDUCED HESSIAN TEST

A first-order stationary camera can still be a saddle point.

Lagrangian Hessian:

```math
H_L=\nabla_{\theta\theta}^2\mathcal L.
```

For equality/active-constraint null-space basis `Z`, inspect reduced Hessian:

```math
H_R=Z^TH_LZ.
```

Positive definiteness on feasible tangent directions is second-order evidence of a strict local minimum.

For large camera systems, Gauss-Newton approximation may be sufficient, but the distinction should remain explicit.

---

# 7. SCHUR COMPLEMENT FOR CAMERA + ACTOR STAGING

If jointly optimizing camera variables `c` and actor floor coordinates `a`:

```math
\delta=[\delta c,\delta a]^T,
```

normal equations partition as:

```math
\begin{bmatrix}
H_{cc}&H_{ca}\\
H_{ac}&H_{aa}
\end{bmatrix}
\begin{bmatrix}
\delta c\\
\delta a
\end{bmatrix}
=
-\begin{bmatrix}
b_c\\b_a
\end{bmatrix}.
```

If actor block is invertible, eliminate actors:

```math
(H_{cc}-H_{ca}H_{aa}^{-1}H_{ac})\delta c
=
-(b_c-H_{ca}H_{aa}^{-1}b_a).
```

This is the same structural idea used in bundle adjustment: camera and scene variables can be solved efficiently without treating every variable identically.

Do not free scene variables that are supposed to be locked.

---

# 8. BILEVEL ART-DIRECTION FORMULATION

Final directing intent and mechanical camera solution are different levels.

Lower-level camera solve:

```math
\theta^*(\phi)
=
\arg\min_{\theta\in\mathcal M(\phi)}E(\theta;\phi),
```

where `phi` contains declared art-direction choices such as:

```text
shot class
which screen targets are protected
FOV preference
negative-space direction
allowed style residual family
```

Upper level selects art-direction configuration:

```math
\phi^*=\arg\min_\phi Q(\theta^*(\phi),\phi).
```

Mathematics solves the declared intent; it does not invent the dramatic intent.

---

# 9. MULTIOBJECTIVE / PARETO CAMERA FRONT

For objectives:

```math
F(\theta)=[f_1(\theta),...,f_k(\theta)],
```

camera `theta_a` dominates `theta_b` if:

```math
f_i(\theta_a)\le f_i(\theta_b)\ \forall i
```

and strict inequality holds for at least one objective.

Keep non-dominated candidate set for real conflicts such as:

```text
face size vs architecture visibility
negative space vs group separation
long lens compression vs camera clearance
short camera move vs better silhouette
```

This prevents one arbitrary scalarization from hiding meaningful directing options.

---

# 10. ROBUST CAMERA OPTIMIZATION UNDER UNCERTAINTY

Let uncertain inputs be:

```math
\xi\sim P(\xi)
```

including:

```text
landmark annotation error
actor pose variation
bounding uncertainty
floor-plane uncertainty
camera calibration uncertainty
```

Expected objective:

```math
\min_\theta\mathbb E_\xi[E(\theta,\xi)].
```

Worst-case robust alternative over uncertainty set `U`:

```math
\min_\theta\max_{\xi\in U}E(\theta,\xi).
```

Chance constraint:

```math
P(g(\theta,\xi)\le0)\ge1-\alpha.
```

`UNKNOWN`: acceptable alpha values are production risk choices, not universal constants.

---

# 11. ROBUST SAFE-FRAME CONSTRAINT

If a face-bound corner has uncertain screen position:

```math
p\sim(\mu_p,\Sigma_p),
```

a nominal safe-frame check on `mu_p` alone can be fragile.

A robust approximation can inflate projected bounds by uncertainty ellipses before testing frame margins.

This converts “passes at point estimate” into “passes under declared uncertainty”.

---

# 12. INFORMATION-OPTIMAL ANCHOR SELECTION

When reconstructing a camera from a reference, not all additional landmarks are equally useful.

Information matrix:

```math
\mathcal I=J^TWJ.
```

Possible experimental-design criteria:

D-optimal:

```math
\max \log\det\mathcal I
```

A-optimal:

```math
\min \operatorname{tr}(\mathcal I^{-1})
```

E-optimal:

```math
\max \lambda_{min}(\mathcal I).
```

Thus the system can answer:

> Which extra screen/world landmark would most improve camera identifiability?

This is more useful than requesting arbitrary extra points.

---

# 13. MINIMUM EXTRA CONSTRAINT TO REMOVE DEGENERACY

If SVD of `J` gives weak right-singular vector:

```math
v_{weak},
```

this vector describes the poorly observed camera parameter combination.

Candidate new measurement `m` has Jacobian row/block:

```math
j_m.
```

A useful new constraint has large projection onto the weak direction:

```math
|j_mv_{weak}|.
```

Therefore the solver can propose the next measurement based on observability, not guesswork.

---

# 14. CAMERA FEASIBLE ENVELOPE

Instead of one optimal point, compute or approximate feasible camera region:

```math
\mathcal F
=
\{\theta:\ g_j(\theta)\le0,\ h_k(\theta)=0,\ \|r_{critical}(\theta)\|\le\epsilon\}.
```

Questions enabled:

```text
How much can camera move while keeping face framing locked?
What alpha interval preserves weapon visibility?
What FOV/radius combinations keep both subjects inside frame?
Where does camera clearance destroy the requested composition?
```

Local approximation uses tangent/null spaces; larger regions require bounded sampling/continuation.

---

# 15. CONTINUATION / HOMOTOPY FOR HARD SHOTS

Difficult camera solves can be approached by gradually tightening the target.

Let:

```math
r(\theta,\tau)
```

interpolate from easy problem at `tau=0` to full problem at `tau=1`.

For example:

```text
start with no occlusion requirement
then increase visibility requirement
then tighten exact face target
then add negative-space objective
```

Track solution continuously instead of restarting from unrelated random states.

---

# 16. MINIMUM-RELAXATION INFEASIBILITY DIAGNOSIS

When hard constraints conflict, solve an auxiliary relaxation problem:

```math
\min_{\theta,s\ge0}\sum_j c_js_j
```

subject to:

```math
g_j(\theta)\le s_j.
```

The nonzero slack vector identifies which constraints require relaxation and by how much in their normalized units.

This is an “impossibility certificate with explanation”.

The solver must not automatically apply the relaxation; it only reports it.

---

# 17. CAMERA CONSTRAINT SHADOW PRICES

KKT multiplier `lambda_j` estimates local marginal cost of tightening active inequality `g_j`.

This can answer:

```text
Which constraint is making this shot expensive/impossible?
Is face margin or camera collision the stronger blocker?
How much composition error is caused by the fixed FOV bound?
```

Use these as diagnostic derivatives, not creative authority.

---

# 18. MULTI-RESOLUTION / MULTI-ASPECT ROBUSTNESS

A shot may be rendered at different pixel resolutions or cropped to different delivery windows.

Store targets in:

```text
primary pixels for exact current frame
normalized viewport coordinates for transfer
semantic protected regions
```

For delivery layouts `k=1,...,K`, robust camera objective:

```math
E_{multi}(\theta)=\sum_k\omega_kE_k(\theta).
```

Hard multi-format constraint:

```math
g_{k,j}(\theta)\le0\quad\forall k,j.
```

This supports one 3D composition that remains valid across required framing variants when physically possible.

---

# 19. SCREEN-AREA DIFFERENTIAL

For projected local surface map:

```math
p(u,v;\theta),
```

projected area density is:

```math
a_s=\left\|\frac{\partial p}{\partial u}\times\frac{\partial p}{\partial v}\right\|.
```

Camera derivative:

```math
\partial a_s/\partial\theta
```

measures how strongly camera edits change the screen dominance of a surface.

This generalizes projected bounding-box size to actual surface screen-area sensitivity.

---

# 20. SILHOUETTE DIFFERENTIAL / NONSMOOTH BOUNDARY

Visible silhouette depends on view direction and changes combinatorially when which triangles form the contour changes.

Therefore:

```text
exact silhouette metric = piecewise smooth / non-smooth at topology changes
```

Recommended architecture:

```text
smooth local projection metrics for optimization
exact rendered/projected silhouette verification after candidate
candidate refinement after contour event
```

Do not claim global differentiability.

---

# 21. HYBRID DISCRETE-CONTINUOUS CAMERA SOLVE

Some camera decisions are discrete:

```text
left side vs right side of subject
which corridor opening frames the character
which foreground object is used as occluder
which lens family / camera mode is allowed
```

For discrete configuration `d` and continuous parameters `theta`:

```math
\min_{d\in D}\ \min_{\theta\in\mathcal F_d}E_d(\theta).
```

Use a bounded set of meaningful discrete hypotheses, then continuous solve inside each.

Do not force a continuous optimizer to cross impossible occlusion topology boundaries blindly.

---

# 22. PROJECTIVE INVARIANTS FOR REFERENCE RECONSTRUCTION

Projective geometry preserves cross-ratio for collinear points.

For four collinear points `A,B,C,D`:

```math
(A,B;C,D)
```

is invariant under projective mapping.

This can be used as a consistency diagnostic for repeated architectural spacing in a perspective reference before committing to metric reconstruction.

Vanishing points/lines and cross-ratio are useful when absolute scale is unknown.

---

# 23. CAMERA PATH AS DIFFERENTIAL GEOMETRY

For camera center path:

```math
C(s),
```

parameterized by arc length `s`, tangent:

```math
T=C'(s).
```

Curvature:

```math
\kappa(s)=\|T'(s)\|.
```

In 3D, torsion describes twisting of the trajectory's osculating plane.

These quantities can distinguish:

```text
straight dolly
smooth arc
high-curvature whip
spatially twisting camera move
```

while screen-space targets remain separate constraints.

---

# 24. OPTIMAL CONTROL VIEW OF CAMERA MOTION

State:

```math
x(t)=[C(t),R(t),\dot C(t),...].
```

Control:

```math
u(t)=[a(t),\omega(t),\dot fov(t),...].
```

Dynamics:

```math
\dot x=f(x,u).
```

Cost:

```math
J=\int_0^T L(x,u,t)dt+\Phi(x(T)).
```

subject to screen-space path constraints.

This turns a cinematic camera move into a boundary-value / optimal-control problem.

For interactive or changing actor motion, receding-horizon/MPC reasoning is a possible research direction, not yet a production recommendation.

---

# 25. SCREEN-LOCKED MOVING CAMERA

Suppose world landmark moves `X(t)` and camera moves `theta(t)`.

Screen point:

```math
p(t)=\Pi(X(t),\theta(t)).
```

Differential:

```math
\dot p
=
J_X\dot X
+
J_\theta\dot\theta.
```

To keep it screen-locked:

```math
\dot p=0,
```

thus solve:

```math
J_\theta\dot\theta=-J_X\dot X.
```

If underdetermined, choose minimum-norm or null-space-optimized camera velocity.

This is direct mathematical stabilization of a moving face/hand/weapon in screen space.

---

# 26. MULTI-LANDMARK SCREEN STABILIZATION

For stacked landmarks:

```math
\dot p=J_XXdot+J_\theta\dot\theta.
```

Weighted least-squares camera velocity:

```math
\dot\theta^*
=
\arg\min_{\dot\theta}
\|J_\theta\dot\theta+J_X\dot X\|_W^2
+\lambda\|\dot\theta\|^2.
```

This gives the smoothest camera motion that best stabilizes multiple protected screen targets.

---

# 27. LENS-RATE CONSTRAINTS

If FOV changes over time:

```math
\theta_f(t)=fov(t).
```

Track:

```math
\dot\theta_f,
\quad
\ddot\theta_f.
```

A zoom can therefore be constrained not only by end FOV but by temporal rate/smoothness.

Intentional snap zoom is an explicitly authorized discontinuity.

---

# 28. HORIZON DYNAMICS

Ground-plane horizon line `l_h(t)` changes with camera orientation.

For a desired horizon trajectory:

```math
l_h(t)\approx l_h^*(t).
```

Use line-distance/orientation residuals per frame.

This allows:

```text
locked horizon
controlled horizon rise/fall
intentional roll event
metaphysical tilted space
```

while keeping the deviation mathematically explicit.

---

# 29. STYLE RESIDUAL AS A LOW-DIMENSIONAL MODEL

Do not let `Delta_style(u,v)` become an unconstrained arbitrary warp.

Prefer low-dimensional declared basis:

```math
\Delta_{style}(u,v)=\sum_{k=1}^m a_k\phi_k(u,v).
```

Examples of basis families:

```text
bounded screen translation
anisotropic scale around protected center
controlled perspective compression
bounded horizon/tilt adjustment
hero-subject local scale residual
```

Regularize coefficients:

```math
E_{style}=a^T\Lambda a.
```

This keeps intentional anime distortion auditable.

---

# 30. JOINT PHYSICAL + STYLE IDENTIFIABILITY

If both physical camera and style warp are too free, they can explain the same screen evidence.

This creates gauge ambiguity.

Therefore:

```text
solve physical camera first under physical constraints;
then unlock only declared style residual modes;
report physical and style components separately.
```

Otherwise the solver may replace a real camera mistake with a fake “style correction”.

---

# 31. ANCHOR INFORMATION GAIN

If current parameter covariance is:

```math
\Sigma_\theta,
```

and candidate measurement `m` yields posterior covariance `Sigma'_theta`, an information-gain proxy is:

```math
IG_m
=\frac12\log\frac{\det\Sigma_\theta}{\det\Sigma'_\theta}.
```

This can rank which reference measurement is worth annotating next.

---

# 32. CAMERA QC MUST REPORT RESIDUAL VECTOR, NOT ONLY RMS

RMS can hide one catastrophic landmark.

Always retain at least:

```text
per-target residual
RMS
median
maximum
hard-constraint violations
visibility shortfall
conditioning
```

A small RMS with one face/foot critical failure is not a valid camera result.

---

# 33. NEXT PROOF QUESTIONS

The future `BABYLON_CAMERA_SOLVER_PROOF_R03` should include additional advanced tests:

```text
KKT/active-set feasibility case
null-space protected-frame edit
rank-deficient camera problem and automatic diagnosis
information-optimal extra-anchor selection
uncertain landmark Monte Carlo
hybrid left/right camera hypothesis
screen-locked moving landmark case
physical+style residual separation
```

These are mathematical proof cases. Production usefulness remains `NOT PROVEN` until transferred to real ZORR Babylon staging evidence.
