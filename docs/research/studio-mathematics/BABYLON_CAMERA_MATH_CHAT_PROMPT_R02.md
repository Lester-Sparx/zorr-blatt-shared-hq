# PROMPT — ZORR / BABYLON STRICT CAMERA MATHEMATICS R02

Copy the block below into a fresh chat when you want that chat to continue this mathematical research line.

---

```text
ZORR MODE

ТЫ ЗАНИМАЕШЬСЯ ТОЛЬКО МАТЕМАТИКОЙ.

ТЕМА ЭТОГО ЧАТА:
СТРОГО МАТЕМАТИЧЕСКАЯ СИСТЕМА ПОСТАНОВКИ КАМЕРЫ И СЦЕНЫ В BABYLON.JS.

ЦЕЛЬ:
не “двигать камеру на глаз”, а превратить постановку камеры в обратную задачу проективной геометрии, constrained optimization, differential geometry, linear algebra, numerical methods, uncertainty и QC.

ВАЖНО:
- не лезь в production Babylon-сцену;
- не меняй main;
- не merge;
- не canon-lock;
- не создавай второй 3D engine / scene graph / ray caster / camera framework;
- Babylon должен оставаться исполнителем native transforms/view/projection/rays/bounds;
- наша область — МАТЕМАТИКА НАД BABYLON;
- CODE-FIRST для численных доказательств;
- никакого eyeballing для чисел;
- никакого fake PASS.

============================================================
0. ОБЯЗАТЕЛЬНО ВОССТАНОВИ DURABLE CONTEXT
============================================================

Сначала fresh-read:

1. current `main` HEAD;
2. `ZORR_EXECUTION_CONSTITUTION.md` с exact current main;
3. `AGENTS.md`;
4. issue #222 `DUNCAN PRIME — STUDIO MATHEMATICS / QUALITY RESEARCH` + latest comments;
5. exact current HEAD ветки `research/zorr-studio-mathematics-r01`;
6. `docs/research/studio-mathematics/README.md`;
7. `docs/research/studio-mathematics/MATHEMATICAL_WORLD_PERSPECTIVE_LEARNING_R01.md`;
8. `docs/research/studio-mathematics/PERSPECTIVE_GEOMETRY_MASTER_R01.md`;
9. `docs/research/studio-mathematics/code/zorr_perspective_master_r01.py`;
10. `docs/research/studio-mathematics/BABYLON_CAMERA_PLACEMENT_MATHEMATICS_R02.md`.

Не восстанавливай математику из chat memory, если GitHub содержит более свежую durable evidence.

============================================================
1. FRESH-STUDY BABYLON UPSTREAM
============================================================

Проверь текущий stable Babylon.js и exact upstream ref/version/license.

Изучи native implementation, а не только README/docs, минимум:

- Camera projection/view matrices;
- FOV modes;
- viewport;
- `Vector3.Project`;
- `Vector3.Unproject`;
- ArcRotateCamera alpha/beta/radius/target;
- targetScreenOffset;
- camera limits;
- camera collision support;
- Ray / pickWithRay / multiPick;
- BoundingInfo / frustum;
- существующий camera framing/zoom behavior;
- handedness rules.

Используй:
`EXISTING ZORR -> BABYLON NATIVE -> MATURE OSS -> MINIMAL GLUE`.

Не писать свой RANSAC/PnP/calibration solver, если OpenCV/Babylon уже решают exact subproblem.

============================================================
2. ОСНОВНАЯ МАТЕМАТИЧЕСКАЯ ПОСТАНОВКА
============================================================

Forward model:

    p = Pi(X; theta)

Camera inverse problem:

    theta* = argmin_{theta in Omega} E(theta)

subject to:

    g_j(theta) <= 0
    h_k(theta) = 0

Где `theta` — параметры камеры, `E` — нормализованные screen-space objectives, а `Omega` — допустимое пространство камеры.

Не смешивать raw pixels, radians, world units и percentages в одной сумме без normalization/covariance.

============================================================
3. ОБЯЗАТЕЛЬНЫЕ КООРДИНАТНЫЕ СИСТЕМЫ
============================================================

Явно объяви:

- Babylon world basis;
- handedness;
- camera basis;
- viewport basis;
- pixel origin;
- normalized screen coordinates;
- world units;
- frame/render resolution;
- active FOV mode.

Проверь преобразование через Babylon native matrices.

Математическая модель не считается доказанной, пока native Babylon reprojection не подтверждает ее.

============================================================
4. CAMERA PARAMETERIZATIONS
============================================================

Развивай минимум две модели.

A. General camera:

    theta_free = [C, omega, focal/FOV, projection offsets, tilt]

Rotation оптимизировать через SO(3)/quaternion/Lie algebra, не через наивные Euler increments.

B. ArcRotateCamera:

    theta_arc = [alpha, beta, log(radius), targetXYZ, FOV, targetScreenOffsetXY]

Для default Y-up Babylon используй exact upstream relation:

    C = T + r * [cos(alpha) sin(beta),
                 cos(beta),
                 sin(alpha) sin(beta)]^T

Выведи и проверь производные по alpha/beta/r/target.

============================================================
5. SCREEN TARGET LIBRARY
============================================================

Построй математическую библиотеку screen targets:

- world point -> target pixel;
- subject bounding center;
- subject screen height;
- subject screen width;
- projected area;
- safe-frame margins;
- horizon / line target;
- screen angle target;
- relative scale between characters;
- depth order;
- face/eye/hand/weapon protected regions;
- silhouette visibility;
- negative-space field;
- lead/look room;
- group centroid;
- screen information centroid;
- camera continuity across shots.

Для каждого target выведи residual в dimensionless form.

Примеры:

    r_point = [(u-u*)/W, (v-v*)/H]

    r_height = log(h/h*)

    r_area = log(A/A*)

    r_angle = wrap(phi-phi*)/pi

============================================================
6. ERROR FUNCTION — НЕ ОДИН “MAGIC SCORE”
============================================================

Разработай и сравни:

A. normalized weighted least squares;
B. Mahalanobis residuals;
C. Huber / robust losses;
D. lexicographic / hierarchical objectives;
E. Pareto camera candidates.

Ключевой закон:

HARD CONSTRAINT != SMALL WEIGHT.

Предпочтительная иерархия:

LEVEL 0:
- support
- collision/clearance
- clipping
- required visibility
- camera bounds

LEVEL 1:
- mandatory framing
- protected landmarks
- projected size

LEVEL 2:
- composition
- negative space
- relative scale

LEVEL 3:
- minimum camera change
- preferred FOV/lens

LEVEL 4:
- optional stylized perspective residual

Не назначать universal ZORR weights из головы.

============================================================
7. ВЫВЕСТИ ОБРАТНЫЕ РЕШЕНИЯ
============================================================

Обязательно развить аналитически:

1. pixel -> camera ray

       d_c ~ K^{-1} [u,v,1]^T

2. world ray

       d_w = R^T d_c

3. ray-plane intersection

       lambda = -(n^T C + d)/(n^T d_w)

4. screen point + support plane -> exact world support point;

5. desired projected height -> depth/radius;

       h_px ~= f H / Z

   как seed, затем exact nonlinear root solve;

6. target world direction -> centered camera orientation;

7. off-center target pixel -> rotation satisfying

       R d_world = normalize(K^{-1} p*)

8. 3D<->2D correspondences -> PnP/OpenCV -> Babylon conversion -> native reprojection;

9. planar scene -> homography;

10. known orthogonal line families -> vanishing geometry / focal constraints.

При вырожденной геометрии не угадывать глубину.

============================================================
8. JACOBIANS
============================================================

Выведи и проверь finite differences.

Perspective Jacobian:

    J_pi = [[fx/Z, 0, -fx X/Z^2],
            [0, fy/Z, -fy Y/Z^2]]

Pose Jacobian под явно объявленной SE(3) perturbation convention:

    J_pose = J_pi [I | -[Xc]_x]

или соответствующий знак при другой convention.

FOV derivative для vertical-fixed:

    fy(theta) = H / (2 tan(theta/2))

    dfy/dtheta = -H / (4 sin^2(theta/2))

ArcRotate derivatives вывести из exact Babylon formula.

Также построить sensitivity matrix:

    S_ij = partial y_i / partial theta_j

============================================================
9. OBSERVABILITY / IDENTIFIABILITY
============================================================

Перед solve проверять, может ли evidence вообще определить unknowns.

Используй:

    rank(J)

SVD:

    J = U Sigma V^T

condition evidence:

    kappa = sigma_max / sigma_min

Исследовать:

- one-point underdetermination;
- FOV-depth ambiguity;
- planar degeneracy;
- missing roll constraint;
- near-horizon depth instability;
- collinear/coplanar PnP pathologies;
- symmetric scene ambiguities.

Если camera state не идентифицируется:

    NOT PROVEN

и назови минимальный дополнительный anchor/constraint, который снимет degeneracy.

============================================================
10. OCCLUSION
============================================================

Не делать вид, что exact occlusion — гладкая функция.

Для protected samples q_k:

    visibility = (1/N) sum I_visible(q_k)

Exact verification делать Babylon native rays/picking.

Исследовать двухступенчатую схему:

- smooth overlap/depth surrogate во время solve;
- exact ray test после candidate;
- reject/refine if visibility constraint fails.

Построить occlusion graph:

    G_occ = (V,E)

с edge attributes:
- occluded px area;
- occluded percentage;
- depth gap;
- protected region overlap.

============================================================
11. FRUSTUM / CLIP / CAMERA CLEARANCE
============================================================

Использовать Babylon native BoundingInfo/frustum as final check.

Исследовать hard constraints:

    z_i > near + margin
    z_i < far - margin

    signedDistance(camera, obstacles) >= clearance

ArcRotate collision radius / checkCollisions использовать как native capability, не переписывать collision system.

============================================================
12. NEGATIVE SPACE / COMPOSITION FIELDS
============================================================

Пусть:

    O(u,v) = occupancy field
    N(u,v) = protected negative-space field

Тогда:

    E_neg = mean(N * O)

Изучить:

- visual mass centroid;
- information centroid;
- silhouette overlap;
- directional lead room;
- asymmetric balance;
- screen-space density fields.

Не превращать rule-of-thirds/golden-ratio в universal law.

============================================================
13. MULTI-SUBJECT SOLVE
============================================================

Для нескольких персонажей учитывать:

- centers;
- projected heights;
- relative scale ratios;
- depth order;
- minimum screen separation;
- face/weapon visibility;
- shared floor support;
- negative space.

Если разрешено двигать actors, joint variables:

    theta = [camera, actor_1_UV, ..., actor_n_UV]

НО не разрешай solver скрывать плохую camera, двигая fixed scene elements.

============================================================
14. TEMPORAL CAMERA MATHEMATICS
============================================================

Camera path:

    T(t) in SE(3)

Использовать Lie-log continuity:

    log(T_t^{-1} T_{t+1})

Исследовать:

- velocity;
- acceleration;
- jerk;
- screen-space face stability;
- actor+camera combined image motion;
- explicit intentional snap discontinuities.

Anime snap = declared discontinuity, не numeric bug.

============================================================
15. UNCERTAINTY
============================================================

Measurement covariance:

    Sigma_y ~= J Sigma_x J^T

Camera covariance local approximation:

    Sigma_theta ~= sigma^2 (J^T W J)^-1

при justified assumptions.

Для сильно nonlinear cases использовать bounded Monte Carlo.

Особо исследовать рост world-space uncertainty около horizon / weak depth geometry.

============================================================
16. SAFE ADJUSTMENT DIRECTIONS — РАЗВИТЬ ОСОБЕННО
============================================================

Если protected targets имеют Jacobian J_p, то локальные изменения камеры, почти не нарушающие locks:

    J_p delta_theta ~= 0

то есть:

    delta_theta in Null(J_p)

Разработай:

- null-space camera edits;
- active-set constraints;
- projection secondary gradient into safe null space;
- interactive camera adjustment preserving face/feet/framing locks.

Это потенциально один из самых сильных инструментов математики для Babylon staging.

============================================================
17. PHYSICAL BASE + ANIME STYLE RESIDUAL
============================================================

Разделяй:

    p_phys = Pi(X; theta)

    p_style = p_phys + Delta_style

Никогда не смешивай intentional distortion с accidental camera error.

Delta_style может отражать:
- hero scale exaggeration;
- perspective compression;
- graphic horizon shift;
- bounded targetScreenOffset;
- art-directed projection warp.

Но style residual не должен молча скрывать:
- broken support;
- wrong depth order;
- unintended occlusion;
- character construction drift;
- camera collision.

============================================================
18. SOLVER ARCHITECTURE
============================================================

Исследовательская схема:

STAGE 0 — validate units/viewport/handedness/FOV mode
STAGE 1 — analytic seed
STAGE 2 — smooth nonlinear solve
STAGE 3 — hard parameter bounds
STAGE 4 — native non-smooth Babylon checks
STAGE 5 — native Babylon reprojection
STAGE 6 — Jacobian rank/conditioning/uncertainty
STAGE 7 — report

При non-convexity:

- bounded multi-start;
- no unbounded brute force;
- preserve top Pareto candidates.

============================================================
19. REQUIRED OUTPUT DATA MODEL
============================================================

Разработай `CameraMathTarget`:

- id;
- target type;
- world anchor/geometry;
- desired screen value;
- units;
- viewport binding;
- hard/soft;
- priority;
- uncertainty/covariance;
- normalized weight;
- provenance.

Разработай `CameraSolveReport`:

- source hashes/version;
- Babylon version/ref;
- camera class;
- handedness;
- viewport;
- state before/after;
- residuals per target;
- hard constraint state;
- occlusion results;
- frustum results;
- support/collision results;
- rank/SVD/conditioning;
- uncertainty;
- Babylon native reprojection residual;
- style residual;
- solver termination reason;
- NOT-PROVEN boundaries.

============================================================
20. CODE-FIRST PROOF
============================================================

Следующий durable research slice должен быть:

    BABYLON_CAMERA_SOLVER_PROOF_R03

Сделай математический proof harness.

Минимум:

A. Synthetic known camera
- known Babylon-compatible camera state;
- known world anchors;
- exact projected target pixels;
- perturb camera;
- recover state.

B. Verify
- alpha/beta/radius/target/FOV errors;
- pixel RMS/max reprojection error;
- finite-difference vs analytic Jacobians;
- rank/conditioning;
- support/frustum/visibility.

C. Changed/unseen transfer
- second geometry arrangement not used to tune method.

D. Babylon agreement
- analytic projection vs native Babylon projection.

Не называй production PASS только потому, что synthetic optimization converged.

Различай:

    FORMULA PROOF
    SYNTHETIC PASS
    BABYLON-NATIVE AGREEMENT
    CHANGED-SCENE TRANSFER
    PRODUCTION EFFECTIVENESS

============================================================
21. DURABLE RECORD
============================================================

Если bounded research slice доказан:

- сохраняй docs/code только в `research/zorr-studio-mathematics-r01`;
- update `docs/research/studio-mathematics/README.md`, если меняется restore map;
- добавь issue #222 comment с exact branch HEAD, changed files, evidence и NOT-PROVEN boundaries;
- main mutation = NO;
- merge = NO;
- canon lock = NO.

Перед любым terminal PASS fresh-read Constitution снова.

============================================================
22. ЧТО Я ХОЧУ ОТ ТЕБЯ КАК ИССЛЕДОВАТЕЛЯ
============================================================

Не ограничивайся перечислением известных формул.

Развивай математику до практически полезной системы для постановки anime-сцен в Babylon:

- находи новые camera invariants;
- выводи закрытые решения, где возможно;
- находи degeneracies;
- строй Jacobians/Hessians/condition metrics;
- исследуй null-space camera editing;
- разрабатывай multi-subject constrained staging;
- связывай perspective tensor с camera sensitivity;
- связывай screen-space motion с SE(3) camera motion;
- исследуй оптимизацию по Pareto-front вместо magic score;
- отделяй mathematical physical base от controlled anime distortion;
- используй Babylon native code wherever it already solves the engine primitive;
- проверяй численно, а не словами.

Главный принцип:

    CAMERA IS NOT A GUESS.
    CAMERA IS A SOLUTION OF A CONSTRAINED PROJECTIVE PROBLEM.

Работай по закону:

    DEFINE -> MEASURE -> CALCULATE -> APPLY -> VERIFY -> RECORD

И веди исследование до честного bounded PASS или точного доказанного BLOCKER.
```

---

## Intended use

This prompt is a durable handoff for a fresh mathematics chat. It does not authorize production scene mutation, main mutation, merge or canon lock.
