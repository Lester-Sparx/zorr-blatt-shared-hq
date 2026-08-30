# ZORR CLOTH + ANIME MOTION MATHEMATICS R01

TRACKER = #222
BRANCH = research/zorr-studio-mathematics-r01
STATUS = RESEARCH SLICE / FORMULA-QC PASS / PRODUCTION THRESHOLDS QC_PENDING
BASE_MAIN = b18ca6b9cce2dce6fe304ca8ae36c05df4f4dcb1
FRESH_SOURCE_REVIEW = 2026-08-30
MAIN_MUTATION = NO
CANON_LOCK = NO
MERGE = NO unless OWNER explicitly authorizes a merge gate

## 0. Research purpose

This slice studies the mathematics of:

```text
BODY MOTION
CLOTHING / FABRIC
HAIR
STRAPS / CHAINS / JEWELRY / LOOSE ACCESSORIES
PROPS / WEAPONS
CONTACTS
IMPACTS
SMEARS
CAMERA-RELATIVE MOTION
SECONDARY MOTION
FX MOTION
ANIME TIMING / SPACING / HOLDS
```

The goal is not to force anime into physically realistic motion.

The goal is to establish a measurable baseline so ZORR can tell the difference between:

```text
INTENTIONAL STYLIZATION
vs
ACCIDENTAL DRIFT / JITTER / SLIDING / PENETRATION / BAD TIMING
```

Core law:

```text
PHYSICAL / GEOMETRIC BASELINE
-> EXPLICIT STYLE TRANSFORM
-> FRAME-ROLE-AWARE QC
```

Physics is a reference and control surface. Directing remains artistic authority.

Evidence labels:

- `STANDARD` — established mathematical/physical formulation or primary publication.
- `SOURCE-DERIVED` — follows from durable ZORR law.
- `DERIVED` — direct derivation from declared assumptions.
- `PROJECT` — bounded ZORR research convention.
- `MEASURED` — reserved for reproducible measurements from approved ZORR assets.
- `UNKNOWN` — do not invent.

---

# 1. ONE MOTION LANGUAGE FOR ALL MOVING THINGS

[DERIVED / PROJECT]

A tracked point, joint, cloth vertex, prop marker, camera marker or FX centroid is a trajectory:

```math
x(t) \in R^2 \;\text{or}\; R^3
```

with:

```math
v(t)=dx/dt
```

```math
a(t)=d^2x/dt^2
```

```math
j(t)=d^3x/dt^3
```

where `j` is jerk.

For sampled animation with frame interval:

```math
Delta t = 1/fps
```

central finite differences are:

```math
v_n \approx (x_{n+1}-x_{n-1})/(2 Delta t)
```

```math
a_n \approx (x_{n+1}-2x_n+x_{n-1})/Delta t^2
```

and jerk can be obtained by differencing acceleration or by a higher-order stencil when justified.

For ZORR, store both:

```text
WORLD-SPACE MOTION
SCREEN-SPACE MOTION IN Cpx
```

because a physically stationary object can move on screen due to camera motion.

---

# 2. MOTION DECOMPOSITION

[PROJECT]

A visible point should be treated as the composition of multiple causes rather than one unexplained screen trajectory:

```math
x_screen(t)
=
Pi(
Camera(t),
Root(t),
Skeleton(q(t)),
Deformation(t),
Secondary(t)
)
```

Practical causal decomposition:

```text
ROOT / BODY TRANSLATION
+ ARTICULATED SKELETON
+ SOFT DEFORMATION
+ CLOTH / HAIR / ACCESSORY SECONDARY MOTION
+ PROP MOTION
+ CAMERA MOTION
+ FX MOTION
```

This prevents false QC. Example: do not classify camera pan as character jitter.

---

# 3. TIMING, EXPOSURE AND SPACING

[STANDARD TOOL BEHAVIOR / PROJECT]

Animation frame rate does not imply one unique drawing every frame.

OpenToonz Xsheet/Timeline explicitly controls exposure and provides Step 2, Step 3 and Step 4 operations that repeat drawings. Krita's animation timeline likewise separates frame slots, keyframes and holds.

Therefore define an exposure map:

```math
D(n) = drawing\_id\; displayed\; at\; output\; frame\; n
```

A hold is:

```math
D(n)=D(n+1)=...=D(n+h)
```

The geometric spacing of a tracked feature is:

```math
d_n = ||x_{n+1}-x_n||
```

and cumulative path length is:

```math
s_k = \sum_{n=0}^{k-1} d_n
```

A motion can therefore be characterized by:

```text
DRAWING EXPOSURE PATTERN
SPACING SEQUENCE
PATH GEOMETRY
FRAME ROLE
```

not by FPS alone.

No QC rule may demand smooth interpolation through a deliberate hold, snap or impact.

Sources:
- https://opentoonz.readthedocs.io/en/latest/working_in_xsheet.html
- https://docs.krita.org/en/reference_manual/dockers/animation_timeline.html
- https://docs.krita.org/en/reference_manual/dockers/animation_curves.html

---

# 4. NEUTRAL SMOOTH-MOTION BASELINE — NOT AN ANIME LAW

[STANDARD MATH / PROJECT USE]

For normalized phase:

```math
u=(t-t_0)/(t_1-t_0), \quad 0\le u\le1
```

a useful minimum-jerk position law with zero velocity and acceleration at both ends is:

```math
s(u)=10u^3-15u^4+6u^5
```

Fresh symbolic check:

```text
s(0)=0
s(1)=1
s'(0)=s'(1)=0
s''(0)=s''(1)=0
```

Use this only as a neutral comparison curve. Anime timing may intentionally use asymmetric ease, sudden spacing, holds, overshoot or discontinuities.

Krita's Animation Curves supports constant, linear and Bezier interpolation; this is useful as an existing timing/control surface rather than a reason to auto-tween every drawing.

---

# 5. TRAJECTORY ARCS AND CURVATURE

[STANDARD MATH]

For a 2D path `(x(t),y(t))` the curvature is:

```math
kappa(t)=
|x'(t)y''(t)-y'(t)x''(t)|
/
(x'(t)^2+y'(t)^2)^{3/2}
```

For a circle of radius `R`:

```math
kappa=1/R
```

which was numerically fresh-checked in this slice.

Useful measurements:

```text
arc length
peak curvature
curvature sign changes
endpoint tangent
path overshoot
path self-intersection
```

For hands, heads, weapons, hair tips and garment hems this exposes accidental wobble while still allowing deliberately straight or snapped anime motion.

---

# 6. RIGID / ARTICULATED BODY MOTION

[STANDARD MATH]

Forward kinematics for a joint chain:

```math
T_i = T_parent(i) T_local(q_i)
```

and a homogeneous point is:

```math
p_world = T_i p_local
```

Inverse kinematics can be written as constrained optimization:

```math
q^* = argmin_q ||f(q)-p_target||^2 + R(q)
```

subject to joint limits and contact constraints.

For rigid orientation `R_n in SO(3)`, angular motion should be computed from relative rotation, not by naively subtracting Euler angles. A useful local approximation is:

```math
omega_n \approx Log(R_n^T R_{n+1})/Delta t
```

where `Log` maps the relative rotation to its axis-angle / Lie-algebra vector.

This avoids false jumps at Euler wrap boundaries.

---

# 7. CENTER OF MASS, SUPPORT AND CONTACT

[STANDARD MATH / PROJECT QC]

For point masses:

```math
r_COM = (\sum_i m_i r_i)/(\sum_i m_i)
```

In grounded actions, support geometry and center-of-mass projection provide a physical baseline for balance. Anime may intentionally exaggerate beyond static balance; that should be tagged as authored action rather than silently treated as ordinary standing.

For a foot contact interval `C`:

```math
E_slide = \sum_{n in C} ||p_foot(n+1)-p_foot(n)||
```

Report in:

```text
Cpx
Cpx / character-height
world units if available
```

No universal ZORR threshold is assigned yet.

---

# 8. IMPACT, MOMENTUM AND RECOIL

[STANDARD MATH / PROJECT STYLE USE]

Linear momentum:

```math
p=mv
```

Impulse:

```math
J=\int F(t)dt = Delta p
```

For fixed mass:

```math
Delta v = J/m
```

A useful secondary-motion / recoil baseline is the damped oscillator:

```math
m x_ddot + c x_dot + kx = F(t)
```

with natural angular frequency:

```math
omega_n=sqrt(k/m)
```

and damping ratio:

```math
zeta=c/(2sqrt(km))
```

Anime impact analysis should measure separately:

```text
PRE-IMPACT VELOCITY
IMPACT FRAME ROLE
IMPULSE-LIKE SPACING JUMP
POST-IMPACT HOLD
OVERSHOOT
REBOUND
DECAY
```

A deliberate impact-frame discontinuity is not automatically motion error.

---

# 9. SECONDARY MOTION AS A DRIVEN DYNAMIC SYSTEM

[DERIVED / PROJECT]

Hair, cloth tails, straps and jewelry are driven by anchor motion.

A coarse angular model can be written:

```math
theta_ddot
+ 2 zeta omega_0 theta_dot
+ omega_0^2 sin(theta)
= u(t)
```

where `u(t)` represents forcing caused by anchor acceleration, wind, collision or authored action.

Core visual consequences:

```text
DRIVER MOVES
-> SECONDARY ELEMENT LAGS
-> ENERGY PROPAGATES
-> OVERSHOOT
-> DAMPED RECOVERY
```

This causal ordering is more useful to animation QC than simply comparing silhouettes frame-to-frame.

---

# 10. MEASURING PHASE LAG

[STANDARD SIGNAL MATH / PROJECT]

After removing irrelevant offsets/trends, lag between a driver signal `x(t)` and secondary response `y(t)` can be estimated using cross-correlation:

```math
R_xy(tau)=\sum_t x(t)y(t+tau)
```

```math
tau^*=argmax_tau R_xy(tau)
```

Possible signals:

```text
root angular velocity -> coat-tail angle
head rotation -> hair-tip displacement
hand acceleration -> sleeve-lag displacement
body stop -> jacket-hem overshoot
```

Store lag in both frames and milliseconds.

A secondary element leading its driver may be valid only when another cause exists, such as wind, anticipation, contact or explicit stylization.

---

# 11. CLOTH STATE — TRIANGULAR SURFACE MODEL

[STANDARD]

Baraff and Witkin model cloth as a triangular mesh. Let vertex `i` have:

```math
x_i(t) \in R^3
```

and a fixed rest/material coordinate:

```math
(u_i,v_i)
```

A general cloth equation is:

```math
M x_ddot = -nabla E(x) + F_ext(x,x_dot)
```

where internal energy `E` and external forces include effects such as gravity, air drag, damping and contact/constraint forces.

Baraff/Witkin distinguish internal contributions associated with stretch, shear and bending and emphasize that cloth strongly resists stretch while permitting much more bending/shear. They also note that clothing requires higher spatial resolution than simple hanging sheets because wrinkles and folds must be represented.

Primary source:
- David Baraff, Andrew Witkin, Large Steps in Cloth Simulation, SIGGRAPH 1998: https://www.cs.cmu.edu/~baraff/papers/sig98.pdf

---

# 12. MASS FROM REST MATERIAL AREA

[STANDARD]

For a rest triangle with areal density `rho_A` and rest/material area `A_0`:

```math
m_triangle = rho_A A_0
```

A simple lumped-mass allocation assigns:

```math
m_i += m_triangle/3
```

to each triangle vertex.

This matches the mass construction described by Baraff/Witkin for their triangular cloth discretization.

---

# 13. CLOTH DEFORMATION GRADIENT AND DIRECTIONAL STRETCH

[STANDARD CONTINUUM MATH / DERIVED APPLICATION]

For one triangle, define rest-material edge matrix:

```math
D_m =
[
 u_1-u_0   u_2-u_0
 v_1-v_0   v_2-v_0
]
```

and deformed edge matrix:

```math
D_s = [x_1-x_0, x_2-x_0]
```

with shape `3x2`.

Then:

```math
F = D_s D_m^{-1}
```

maps rest tangent directions into the deformed surface.

For a unit material direction `a` in the rest 2D coordinates:

```math
lambda(a)=||Fa||
```

and engineering strain proxy:

```math
epsilon(a)=lambda(a)-1
```

A more complete strain tensor is the Green strain:

```math
E_G = 1/2 (F^T F - I)
```

This is the mathematical foundation for distinguishing warp/weft/bias deformation instead of treating every garment as isotropic rubber.

---

# 14. CLOTH ANISOTROPY: WARP / WEFT / BIAS

[STANDARD MATERIAL CONCEPT / PROJECT APPLICATION]

Woven clothing can respond differently along material directions.

Represent local rest directions:

```text
a_warp
a_weft
a_bias
```

and measure:

```math
lambda_warp = ||F a_warp||
```

```math
lambda_weft = ||F a_weft||
```

```math
lambda_bias = ||F a_bias||
```

Do not assume:

```math
k_warp = k_weft = k_bias
```

unless the material model is intentionally isotropic.

This distinction is directly relevant to costume identity: denim, leather-like cloth, knit, silk-like fabric and stiff uniform cloth should not all share one anonymous deformation response.

The exact ZORR material constants remain `UNKNOWN` until solver parameterization and approved visual anchors are selected.

---

# 15. STRETCH, SHEAR AND BENDING ENERGY PROXIES

[DERIVED / MODEL-SPECIFIC]

For a simple edge stretch proxy:

```math
epsilon_e=(l-l_0)/l_0
```

and:

```math
E_stretch = 1/2 k_s(l-l_0)^2
```

For two neighboring triangles with dihedral angle `theta` and rest angle `theta_0`, a simple bending proxy is:

```math
E_bend = 1/2 k_b(theta-theta_0)^2
```

These equations are intentionally labeled proxies. A production shell model may include area/edge weighting and a more precise constitutive law.

Do not confuse a useful QC observable with a complete physical cloth law.

---

# 16. FOLD MATHEMATICS

[DERIVED / PROJECT]

For each internal garment edge:

```math
Delta theta_e = theta_e-theta_{0,e}
```

Candidate fold descriptors:

```text
|Delta theta| distribution
signed bend distribution
fold-edge length per garment area
connected fold ridge count
fold wavelength in Cpx
fold orientation distribution
principal-curvature distribution
```

At the final drawing level, fold information must be interpreted in screen space.

A fold wavelength:

```math
lambda_fold,Cpx
```

that is meaningful at 4K may collapse into aliasing/noise at 1080p. Therefore:

```text
WORK-RES FOLD PASS != DELIVERY-RES FOLD PASS
```

Fresh QC is required after deterministic downsampling.

---

# 17. POSITION BASED DYNAMICS — READY-MADE FOUNDATION

[STANDARD / OSS-FIRST]

PBD operates by iteratively projecting positional constraints rather than accumulating ordinary force updates first.

For constraint `C_j(x)=0`, the PBD paper notation summarized by XPBD gives:

```math
s_j = -C_j(x_i) / (nabla C_j M^{-1} nabla C_j^T)
```

and a mass-weighted correction:

```math
Delta x = k_j s_j M^{-1} nabla C_j^T
```

where `k_j` is the traditional PBD constraint stiffness factor.

The important limitation: effective stiffness depends on time step and number of solver projections/iterations.

Primary background:
- XPBD paper, Section 3: https://mmacklin.com/xpbd.pdf

---

# 18. XPBD — COMPLIANCE AS THE BETTER MATERIAL CONTROL SURFACE

[STANDARD]

XPBD introduces compliance `alpha`, the inverse of stiffness in the paper's formulation, and scales it by time step:

```math
alpha_tilde = alpha / Delta t^2
```

For one constraint `j`, the core Gauss-Seidel multiplier update is:

```math
Delta lambda_j =
(-C_j(x_i) - alpha_tilde_j lambda_j^i)
/
(nabla C_j M^{-1} nabla C_j^T + alpha_tilde_j)
```

then:

```math
Delta x = M^{-1} nabla C_j^T Delta lambda_j
```

Fresh limiting check:

```text
alpha_tilde -> 0
```

reduces the multiplier update to the infinitely stiff PBD/Newton projection scale.

XPBD's primary production advantage is that material stiffness is not entangled in the same way with time step and iteration count, making reusable garment parameters more meaningful.

Primary source:
- Macklin, Mueller, Chentanez, XPBD: Position-Based Simulation of Compliant Constrained Dynamics, 2016: https://mmacklin.com/xpbd.pdf

Author publication page:
- https://blog.mmacklin.com/publications/

---

# 19. XPBD DIMENSION CHECK

[DERIVED CHECK]

For a distance constraint:

```text
C : length
M^-1 : 1 / mass
nabla C : dimensionless
alpha : compliance ~ length / force
alpha_tilde = alpha / time^2 ~ 1 / mass
```

Therefore the denominator of the XPBD update has units `1/mass`, `Delta lambda` has units `mass*length`, and:

```math
M^{-1} nabla C^T Delta lambda
```

has units of length as required for a position correction.

This protects against a common implementation error: using unscaled compliance across different time steps.

---

# 20. CURRENT BLENDER AS IMPLEMENTATION EVIDENCE

[READY-MADE / CURRENT TOOL]

Blender 5.3's standard Cloth settings expose separate physical controls for:

```text
vertex mass
air viscosity
tension stiffness
compression stiffness
shear stiffness
bending stiffness
and damping for the same deformation families
```

Its cloth introduction describes virtual tension, compression, shear and angular-bending springs.

Blender's newer Geometry Nodes Cloth Dynamics uses the XPBD Solver node and provides structural constraints plus gravity, damping and collision. This feature is currently documented as experimental and currently lacks some functionality such as self-collision, so it is research/reference material rather than an automatic production mandate.

Sources:
- https://docs.blender.org/manual/en/5.3/physics/cloth/introduction.html
- https://docs.blender.org/manual/en/5.3/physics/cloth/settings/physical_properties.html
- https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/simulation/cloth_dynamics.html
- https://docs.blender.org/manual/en/5.3/modeling/geometry_nodes/simulation/xpbd_solver.html

---

# 21. OSS-FIRST CLOTH / CONSTRAINT CODE STUDY

[READY-MADE]

Do not write a ZORR cloth solver from zero while mature reusable code exists.

Primary open-code research candidate:

```text
InteractiveComputerGraphics/PositionBasedDynamics
License: MIT
```

The library documents PBD/XPBD constraints including distance, isometric bending, volume, strain/FEM-related constraints, contact/collision systems and rods, and exposes Python bindings.

Its source directly defines the classic distance constraint:

```math
C(p_0,p_1)=||p_0-p_1||-l_0=0
```

Sources:
- https://github.com/InteractiveComputerGraphics/PositionBasedDynamics
- https://github.com/InteractiveComputerGraphics/PositionBasedDynamics/blob/master/LICENSE
- https://github.com/InteractiveComputerGraphics/PositionBasedDynamics/blob/master/PositionBasedDynamics/PositionBasedDynamics.h

Before any production adoption, pin an exact commit/tag and verify dependency licenses. Research reading of `master` is not a production pin.

---

# 22. COLLISION AND SELF-COLLISION

[STANDARD / PROJECT QC]

Cloth-body and cloth-prop contact is part of motion identity.

Baraff/Witkin describe cloth/solid contact constraints and cloth self-collision checks involving face-vertex and edge-edge relationships.

For a signed-distance collision proxy `phi(x)` and allowed clearance radius/thickness `r`, a simple penetration measure is:

```math
d_pen(x)=max(0, r-phi(x))
```

Candidate QC:

```text
maximum penetration
penetration area
penetration duration
contact count
self-intersection count
collision-pop displacement
```

At high velocity, discrete frame-only collision checks can miss tunneling. Continuous collision detection or sufficiently conservative substeps are needed when physical simulation is relied upon.

Blender's current cloth documentation also exposes object collision and self-collision mechanisms in its standard cloth system.

---

# 23. FRICTION

[STANDARD PHYSICS / PROJECT]

A Coulomb-style contact baseline separates static and dynamic behavior.

Static tangential force obeys a bound of the form:

```math
||F_t|| <= mu_s F_n
```

and dynamic friction opposes tangential relative motion.

In clothing this affects:

```text
cloth sliding over torso
sleeve sliding over arm
coat over trousers
belt / strap movement
cloth-ground contact
```

Actual coefficients are solver/material dependent and remain `UNKNOWN` until selected and calibrated.

---

# 24. AIR / WIND FORCING

[STANDARD PHYSICS / DERIVED PROXY]

Two useful drag baselines are:

linear drag:

```math
F_drag=-c_d v_rel
```

quadratic drag:

```math
F_drag=-1/2 rho C_D A |v_rel| v_rel
```

For fabric, projected area and surface normal matter; the scalar point formula is only a diagnostic/proxy, not a complete cloth aerodynamic model.

Define:

```math
v_rel = v_cloth - v_air(x,t)
```

This makes wind an explicit causal field instead of arbitrary per-frame waving.

---

# 25. GARMENT ATTACHMENTS / PINS

[STANDARD CONSTRAINT IDEA / PROJECT]

Collars, waistbands, cuffs, seams, belt loops and tied accessories can be represented as constraints to animated anchors.

Hard attachment:

```math
C(x,t)=x-a(t)=0
```

Compliant attachment:

```text
same relation with non-zero compliance / soft pinning
```

Attachment QC should distinguish:

```text
DESIGN-INTENDED SLIDING
SOFT DEFORMATION
ACCIDENTAL DETACHMENT
```

Blender's current Cloth Dynamics node supports pin-group weights, including soft pinning.

---

# 26. CLOTH MOTION HIERARCHY

[PROJECT]

Animate / validate garment motion from large cause to small detail:

```text
BODY / ROOT MOTION
-> GARMENT ANCHORS
-> LARGE CLOTH MASSES
-> FOLD WAVES
-> MICROFOLDS / LINE DETAIL
```

Microfold animation cannot rescue a wrong coat mass or wrong hem trajectory.

This mirrors the wider ZORR rule that authored structure has priority over random micro-detail.

---

# 27. CLOTH MATERIAL VECTOR

[PROJECT SCHEMA]

A reusable garment state can be represented as:

```math
M_cloth = [
areal_density,
warp_response,
weft_response,
shear_response,
bend_response,
damping_stretch,
damping_shear,
damping_bend,
contact_friction,
air_drag,
thickness,
pin_compliance
]
```

Important:

```text
SCHEMA != VALUES
```

Actual parameter values are `UNKNOWN` until a chosen solver's units/semantics and approved ZORR visual anchors are measured.

Do not fabricate leather/silk/denim constants and call them canon.

---

# 28. PHYSICAL BASELINE -> ANIME STYLE TRANSFORM

[PROJECT]

Let a physical/reference trajectory be:

```math
x_phys(t)
```

and the authored anime trajectory be:

```math
x_anim(n)=T_style(x_phys, n; theta_style)
```

The style transform may contain explicit components:

```text
TIME WARP
AMPLITUDE EXAGGERATION
PHASE OFFSET
HOLD / EXPOSURE QUANTIZATION
SELECTIVE DAMPING
SILHOUETTE PRESERVATION
FOLD SIMPLIFICATION
SMEAR REPLACEMENT
IMPACT DISCONTINUITY
```

This is the central research model:

```text
ANIME != FAILED PHYSICS
ANIME = AUTHORED TRANSFORMATION OF MOTION CAUSALITY
```

The transformation should preserve readable cause/effect unless the direction intentionally chooses otherwise.

---

# 29. TIME WARP

[STANDARD MATH / PROJECT]

A path can keep its spatial geometry while changing timing:

```math
x_anim(t)=x_ref(tau(t))
```

For ordinary forward time:

```math
d tau / dt >= 0
```

unless reversal is intentional.

Time warp lets ZORR separate:

```text
PATH ERROR
from
TIMING ERROR
```

This is useful for anticipation, acceleration into impact, hit-stop, recovery and slow reveal.

---

# 30. FRAME ROLE TAXONOMY — REQUIRED BEFORE MOTION QC

[PROJECT]

A frame should declare its intended role when relevant:

```text
KEY
BREAKDOWN
INBETWEEN
HOLD
SMEAR
MULTIPLE-IMAGE FRAME
IMPACT
ANTICIPATION
RECOVERY
FX-DOMINANT
```

The same metric cannot be judged identically across all roles.

Examples:

```text
SMEAR: silhouette/anatomy may intentionally violate neutral model
HOLD: zero spacing is intentional
IMPACT: temporal discontinuity may be intentional
INBETWEEN: continuity/arc behavior may be more constrained
KEY: identity/readability usually dominates
```

Role-aware QC prevents mathematically "correcting" anime language out of the animation.

---

# 31. SMEAR MATHEMATICS

[PROJECT / DERIVED]

A smear is authored geometry, not generic motion blur.

Given screen velocity direction:

```math
v_hat = v_screen / ||v_screen||
```

candidate smear measurements include:

```text
principal elongation axis
angle between elongation and v_hat
smear length in Cpx
silhouette area ratio
endpoint coverage
topology tags for intentional multiples
```

A physical motion-blur comparison length can be approximated by:

```math
L_blur \approx ||v_screen|| t_exposure
```

but `L_smear` is not required to equal `L_blur`.

The physical formula is only a reference scale.

---

# 32. SQUASH / STRETCH AS DEFORMATION MATH

[PROJECT / STANDARD LINEAR ALGEBRA]

For a local 2D deformation gradient/Jacobian `J`, singular values:

```math
sigma_1, sigma_2
```

measure principal stretch.

Area scale is:

```math
A_scale = |det J| = sigma_1 sigma_2
```

A stylized smear may deliberately have:

```text
large sigma_1
small sigma_2
```

while approximately preserving area, or may intentionally violate area conservation.

The correct QC question is not "did shape deform?" but:

```text
WAS THE DEFORMATION ROLE-INTENDED AND READABLE?
```

---

# 33. CAMERA-RELATIVE MOTION

[SOURCE-DERIVED / STANDARD PROJECTIVE GEOMETRY]

For world point `P`:

```math
p_tilde = K [R|t] P
```

followed by perspective divide.

Screen velocity contains object and camera components. Therefore jitter analysis should estimate or remove expected camera-induced motion before accusing the animated subject.

Store:

```text
Cpx/frame
Cpx/second
normalized by subject height
world velocity where available
```

---

# 34. TEMPORAL FREQUENCY ANALYSIS

[STANDARD SIGNAL MATH / PROJECT]

For a sampled secondary-motion signal `y[n]`, FFT/PSD can estimate:

```text
dominant oscillation frequency
energy bands
unexpected high-frequency jitter
damping / decay behavior
periodicity
```

At output frame rate `f_s` the temporal Nyquist frequency is:

```math
f_N=f_s/2
```

but held drawings create piecewise-constant signals and deliberate discontinuities, so spectral metrics must be interpreted with frame roles and exposure patterns.

Never use a high-frequency metric as a generic command to smooth all anime motion.

---

# 35. MOTION + CLOTH DELIVERY-SCALE QC

[PROJECT]

Motion must be re-evaluated at delivery raster.

Possible failures after 4K -> 1080p include:

```text
thin fold-line disappearance
rapid edge flicker
moiré from textile/fold detail
false temporal texture
small accessory jitter amplified by resampling
smear edge ringing
contact-gap appearance/disappearance
```

Therefore:

```text
WORK-RES MOTION PASS != DELIVERY-RES MOTION PASS
```

This connects cloth/motion math to the existing Cpx texture/sampling research.

---

# 36. MOTION QC PACKET

[PROJECT SCHEMA]

```yaml
shot_id:
fps:
delivery_raster:
character_height_Cpx:
frame_roles:
  - frame:
    role:
camera:
  model:
  transform_source:
tracked_motion:
  points:
  spacing_Cpx:
  velocity_Cpx_per_frame:
  acceleration_Cpx_per_frame2:
  jerk_proxy:
  path_length_Cpx:
  curvature:
contacts:
  intervals:
  foot_slide_Cpx:
  penetration:
secondary_motion:
  driver_signal:
  response_signal:
  lag_frames:
  lag_ms:
  overshoot:
  decay:
cloth:
  garment_id:
  rest_shape_ref:
  anchor_points:
  topology_ok:
  strain_quantiles:
  bend_angle_quantiles:
  fold_density:
  fold_wavelength_Cpx:
  collision_events:
  penetration:
solver_reference:
  backend:
  exact_version_or_commit:
  parameters:
  deterministic_seed_if_any:
delivery_qc:
  aliasing:
  fold_line_loss:
  temporal_flicker:
  contact_readability:
critical_failures:
warnings:
decision:
```

Missing parameters remain `UNKNOWN`; fields are not a command to fabricate values.

---

# 37. CRITICAL FAILURES

[PROJECT]

A weighted average must not hide critical motion defects.

Candidate critical classes:

```text
UNINTENDED BODY/CLOTH PENETRATION
GARMENT ATTACHMENT DETACHMENT
UNINTENDED COSTUME TOPOLOGY CHANGE
FOOT/CONTACT SLIDING THAT BREAKS THE SHOT
UNEXPLAINED TEMPORAL JITTER
MOTION CAUSALITY BREAK WITHOUT INTENT TAG
DELIVERY-RES ALIASING THAT CHANGES READABILITY
SMEAR / IMPACT MISCLASSIFIED AS MODEL FAILURE OR VICE VERSA
```

Research gate:

```text
PASS iff
CriticalFailures = 0
AND MotionIntent = PASS
AND Identity/CostumeTopology = PASS
AND Contact = PASS
AND DeliveryScale = PASS
```

Actual numeric thresholds remain `QC_PENDING` until measured on approved ZORR motion anchors.

---

# 38. OSS-FIRST IMPLEMENTATION MAP

[READY-MADE]

Use existing tools before custom simulation infrastructure.

```text
CLOTH / HAIR PHYSICS REFERENCE
  Blender standard Cloth
  Blender Geometry Nodes XPBD Cloth/Hair (experimental; verify feature limits)

PBD / XPBD CODE STUDY
  InteractiveComputerGraphics/PositionBasedDynamics (MIT)

2D TIMING / EXPOSURE
  OpenToonz Xsheet/Timeline
  Krita Animation Timeline / Animation Curves

MEASUREMENT / QC
  NumPy
  SciPy
  OpenCV
  scikit-image where applicable
```

ZORR should build thin measurement/adaptation layers, not a second general cloth engine or animation editor.

---

# 39. EMPIRICAL ZORR RESEARCH PROGRAM

[PROJECT]

The next meaningful research step is not to invent material presets.

For approved ZORR cuts:

```text
1. classify motion/frame roles;
2. track body root, major joints and contact points;
3. track garment anchors, hems, sleeve points, hair/accessory tips;
4. measure spacing, velocity, acceleration, jerk and path curvature;
5. measure driver -> secondary lag and overshoot;
6. extract garment silhouette/fold descriptors;
7. measure contact and penetration events;
8. compare hand-authored motion to neutral physical/reference baselines;
9. identify which physical behaviors artists consistently exaggerate, simplify, delay or suppress;
10. build ZORR style transforms by garment class + action class;
11. repeat at delivery resolution;
12. only then propose numeric QC ranges.
```

Priority experiments:

```text
A. RUN -> HARD STOP -> COAT HEM FOLLOW-THROUGH
B. 180 DEG BODY TURN -> JACKET / HAIR PHASE LAG
C. PUNCH -> SLEEVE + LOOSE STRAP IMPULSE RESPONSE
D. JUMP / LAND -> CLOTH COMPRESSION + REBOUND
E. WIND SHOT -> CAPE / SKIRT / HAIR CAUSAL RESPONSE
F. WALK / RUN -> FOOT CONTACT + CLOTH PERIODICITY
G. IMPACT SMEAR -> ROLE-AWARE GEOMETRIC DEFORMATION
```

---

# 40. FRESH RESEARCH VERIFICATION

Performed for this slice before repository write:

```text
PASS: minimum-jerk endpoint position/velocity/acceleration identities
PASS: central finite-difference sanity check on polynomial motion
PASS: curvature formula checked against circle curvature 1/R
PASS: XPBD alpha_tilde -> 0 limit reproduces rigid PBD projection scale
PASS: XPBD position-correction dimensional consistency
PASS: primary Baraff/Witkin cloth model and collision claims fresh-read
PASS: XPBD equations (16-18) fresh-read from author-hosted paper
PASS: current Blender 5.3 cloth parameters fresh-read
PASS: current Blender XPBD cloth/hair documentation fresh-read with experimental limitations retained
PASS: PositionBasedDynamics OSS capabilities and MIT license fresh-read
PASS: OpenToonz/Krita timing/hold/exposure behavior fresh-read
```

Not passed / intentionally unresolved:

```text
ZORR garment material constants = UNKNOWN
ZORR cloth stiffness/compliance presets = UNKNOWN
ZORR acceptable foot-slide threshold = UNKNOWN
ZORR acceptable penetration threshold = UNKNOWN
ZORR secondary-motion lag ranges = UNKNOWN
ZORR fold-density ranges = UNKNOWN
ZORR per-action timing distributions = UNKNOWN
```

These cannot become canon until measured from approved ZORR evidence.

---

# 41. SOURCE SET

Primary papers / author sources:

- David Baraff, Andrew Witkin, *Large Steps in Cloth Simulation*, SIGGRAPH 1998: https://www.cs.cmu.edu/~baraff/papers/sig98.pdf
- Miles Macklin, Matthias Mueller, Nuttapong Chentanez, *XPBD: Position-Based Simulation of Compliant Constrained Dynamics*, MIG 2016: https://mmacklin.com/xpbd.pdf
- XPBD author publication page: https://blog.mmacklin.com/publications/

Current implementation/documentation evidence:

- Blender 5.3 Cloth Introduction: https://docs.blender.org/manual/en/5.3/physics/cloth/introduction.html
- Blender 5.3 Cloth Physical Properties: https://docs.blender.org/manual/en/5.3/physics/cloth/settings/physical_properties.html
- Blender Cloth Dynamics / XPBD: https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/simulation/cloth_dynamics.html
- Blender XPBD Solver: https://docs.blender.org/manual/en/5.3/modeling/geometry_nodes/simulation/xpbd_solver.html
- Blender 5.3 Hair Dynamics: https://docs.blender.org/manual/en/5.3/modeling/geometry_nodes/simulation/hair_dynamics.html
- PositionBasedDynamics repository: https://github.com/InteractiveComputerGraphics/PositionBasedDynamics
- PositionBasedDynamics license: https://github.com/InteractiveComputerGraphics/PositionBasedDynamics/blob/master/LICENSE
- PositionBasedDynamics constraint API/source: https://github.com/InteractiveComputerGraphics/PositionBasedDynamics/blob/master/PositionBasedDynamics/PositionBasedDynamics.h
- OpenToonz Xsheet/Timeline: https://opentoonz.readthedocs.io/en/latest/working_in_xsheet.html
- Krita Animation Timeline: https://docs.krita.org/en/reference_manual/dockers/animation_timeline.html
- Krita Animation Curves: https://docs.krita.org/en/reference_manual/dockers/animation_curves.html

---

# 42. SLICE RESULT

```text
CLOTH_MATH_RESEARCH_R01 = PASS
ANIME_MOTION_MATH_RESEARCH_R01 = PASS
FORMULA_QC = PASS
OSS_FIRST_REVIEW = PASS
PRODUCTION_THRESHOLDS = QC_PENDING
CANON_LOCK = FALSE
MAIN_MUTATION = NO
MERGE = NO
```

Meaning of PASS here:

The mathematical research artifact passed its declared formula/source checks. It does not assert that any unmeasured ZORR material parameter, motion threshold or costume behavior has been approved for production.
