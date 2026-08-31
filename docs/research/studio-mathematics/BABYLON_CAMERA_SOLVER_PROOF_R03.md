# ZORR BLATT — BABYLON CAMERA SOLVER PROOF R03

TRACKER = `#222`  
BRANCH = `research/zorr-studio-mathematics-r01`  
BASE_MAIN = `b18ca6b9cce2dce6fe304ca8ae36c05df4f4dcb1`  
RESEARCH_PARENT_HEAD = `701693c718599c64b62952e1bbd27c368d53bd8b`  
STATUS = `RESEARCH / PARTIAL PROOF / BABYLON NATIVE GATE OPEN`  
MAIN_MUTATION = `NO`  
MERGE = `NO`  
CANON_LOCK = `NO`  
PRODUCTION_THRESHOLDS = `UNKNOWN / QC_PENDING`

## Truth matrix

| Evidence state | Result |
|---|---|
| `FORMULA_PROOF` | `PASS` |
| `SYNTHETIC_RESULT` | `PASS` |
| `BABYLON_NATIVE_AGREEMENT` | `NOT_PROVEN` |
| `CHANGED_SCENE_TRANSFER` | `PASS` |
| `PRODUCTION_EFFECTIVENESS` | `NOT_PROVEN` |

Overall terminal state is therefore `NOT_PROVEN`. Synthetic convergence is not Babylon runtime verification.

## Fresh Babylon binding

```text
repository = BabylonJS/Babylon.js
release/tag = 9.23.0
annotated tag object = ed72f188d8824950092d5dbf76663a3e71b28c43
tag target commit = 38ed028f40722504a215002fbc2fa89a2c89cf5d
release date = 2026-08-27
license = Apache-2.0
```

Fresh-inspected exact-commit source paths include `camera.pure.ts`, `arcRotateCamera.pure.ts`, `math.vector.pure.ts`, `math.viewport.ts`, `ray.pure.ts`, `ray.ts`, `boundingInfo.ts`, and `framingBehavior.ts`.

Native facts used by this slice: projection handedness is selected from `scene.useRightHandedSystem`; `Vector3.Project/Unproject` use Babylon matrices/viewport; `ray.ts` registers `Scene.pickWithRay`; `BoundingInfo` supplies frustum tests; ArcRotate has native target-screen offset, limits, and collision handling; FramingBehavior remains the native framing primitive. No second scene graph, renderer, ray caster, PnP/RANSAC stack, or collision engine is introduced.

## Executable proof

Research code:

```text
code/zorr_babylon_camera_solver_proof_r03.py
code/zorr_babylon_native_probe_r03.mjs
```

Evidence:

```text
evidence/BABYLON_CAMERA_SOLVER_PROOF_R03_result.json
evidence/BABYLON_CAMERA_SOLVER_PROOF_R03_native_input.json
evidence/BABYLON_CAMERA_SOLVER_PROOF_R03_native_runtime_status.txt
```

General calibrated-camera recovery reuses mature OpenCV `solvePnP(SQPNP)` + `solvePnPRefineLM`. ArcRotate recovery uses bounded SciPy least-squares on normalized screen residuals. No custom PnP is created.

## Measured R03 cases

1. **Known general camera recovery** — PASS. Rotation geodesic error `0 rad`; camera-center error `1.7636828390897275e-14`; max reprojection error `6.12222357532858e-13 px`.
2. **ArcRotate recovery** — PASS. RMSE `2.4406841309732094e-12 px`; max `4.46718393149888e-12 px`.
3. **Projected-height exact solve** — PASS. True radius `9.4`; solved `9.400000000000007`; height residual `1.1368683772161603e-13 px`.
4. **Analytic vs finite-difference Jacobians** — PASS. Arc relative difference `9.251319018954073e-11`; projection relative difference `1.2605042207764782e-10`.
5. **Rank-deficient diagnosis** — PASS. One screen point gives `rank(J)=2` for four ArcRotate variables; state is explicitly underdetermined.
6. **Automatic extra anchor** — PASS. E-optimal candidate `7`, augmented `sigma_min=20.39320651344615`; separately, candidate `11` maximizes the selected weak-direction score (`1207.6633318951465`).
7. **Null-space safe edit** — PASS. Nullity `2`; protected drift `0.004738873542866336 px`; secondary horizontal motion `1.9905401879996134 px`.
8. **Active constraint** — PASS. A radius-decreasing violating local edit has linearized constraint change `+0.1`; tangent projection reduces it to `0.0`.
9. **Uncertainty Monte Carlo** — PASS for deterministic research execution. `80/80` solves, input `sigma=0.75 px`; median reprojection RMSE `0.9844224427767733 px`, p95 `1.2495554210537076 px`. Production threshold remains unknown.
10. **Babylon-native agreement** — NOT_PROVEN. Exact package runtime was unavailable in the sandbox; native harness syntax passes, but no fake runtime result is substituted.
11. **Occlusion** — analytic precheck PASS; exact Babylon `pickWithRay` remains NOT_PROVEN until native harness execution.
12. **Changed/unseen synthetic scene** — PASS without solver retuning. RMSE `1.1946137318279182e-13 px`; max `2.3437142008433856e-13 px`.
13. **Moving-target screen lock** — PASS. Finite-step screen shift falls from `0.07216801729263253 px` to `0.0000308884232403404 px` under differential compensation.
14. **Physical/style separation** — PASS. Declared style offset `[12,-5] px` is recovered by the low-dimensional style basis with zero remaining style residual and zero protected physical residual.

## Native verification contract

The companion Node harness delegates final authority to Babylon `NullEngine`, `Scene`, `ArcRotateCamera`, `getViewMatrix`, `getProjectionMatrix`, `getTransformationMatrix`, `viewport.toGlobal`, `Vector3.Project`, `Vector3.Unproject`, `Frustum.GetPlanes`, mesh frustum testing, and `Scene.pickWithRay`.

Native PASS is fail-closed and requires all of: exact engine version `9.23.0`, analytic/native reprojection agreement, ArcRotate camera-position agreement, unproject roundtrip, exact pick occlusion, and exact frustum inclusion.

Current sandbox evidence:

```text
@babylonjs/core@9.23.0 local dependency = NOT INSTALLED
npm registry attempt = FAIL / EAI_AGAIN
native harness node --check = PASS
BABYLON_NATIVE_AGREEMENT = NOT_PROVEN
```

## Truth boundary

Proven by this slice: formulas/Jacobians, general synthetic PnP, ArcRotate synthetic inverse solve, exact projected-height solve, observability diagnosis, information-based extra-anchor choice, null-space edit, active local constraint handling, uncertainty execution, moving-target differential lock, physical/style separation, and changed synthetic-scene transfer.

Not proven: Babylon 9.23.0 native agreement, exact Babylon occlusion, ZORR production-scene transfer, ZORR production effectiveness, and production weights/tolerances.

Next legal proof step:

```text
RUN EXACT BABYLON 9.23.0 NATIVE HARNESS
-> FEED RESULT TO PYTHON COMPARATOR
-> FRESH-READ CONSTITUTION + EXACT BRANCH HEAD
-> ONLY THEN CHANGE BABYLON_NATIVE_AGREEMENT STATUS
```

No relaxation, production promotion, main mutation, merge, or canon lock is authorized by R03.
