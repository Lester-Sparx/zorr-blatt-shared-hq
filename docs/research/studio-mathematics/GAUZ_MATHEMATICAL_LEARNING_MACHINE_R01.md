# ZORR BLATT — GAUZ MATHEMATICAL LEARNING MACHINE R01

TRACKER = #222
BRANCH = `research/zorr-studio-mathematics-r01`
STATUS = RESEARCH / META-LEARNING MATHEMATICS
MAIN_MUTATION = NO
MERGE = NO
CANON_LOCK = NO
PRODUCTION_EFFECTIVENESS = NOT PROVEN

Working research expansion of the OWNER-given name **GAUZ**:

`Generalized Adaptive Uncertainty-Zeroing`

This expansion is a research label, not a locked OWNER naming law.

## 0. TRUTH BOUNDARY

GAUZ is **not** a claim of omniscience, consciousness, autonomous self-modification of model weights, or literal mathematical omnipotence.

GAUZ is a bounded mathematical research architecture for making learning itself measurable and optimizable:

`UNKNOWN -> MEASURE UNCERTAINTY -> CHOOSE HIGHEST-VALUE EXPERIMENT -> OBSERVE -> UPDATE -> TEST TRANSFER -> CALIBRATE -> RECORD`.

The core question is:

> Given limited time, compute, references, tests and production opportunities, which next mathematical experiment should reduce the most important uncertainty or error per unit cost without violating protected constraints?

This is a direct continuation of the DUNCAN learning law in current `AGENTS.md`: `READING != LEARNING`, changed/unseen transfer matters, and verified experience must return to durable DUNCAN knowledge only after provenance and validation.

---

# 1. GAUZ STATE

Let the latent unknown research state be:

```math
\theta \in \mathbb R^d.
```

Examples of coordinates in `theta` may represent unknown quantities such as:

- camera calibration coefficients;
- style-response coefficients;
- QC false-pass rates;
- production cycle-time parameters;
- texture or color tolerances;
- motion-response parameters;
- uncertain skill/competence hypotheses;
- causal intervention effects.

GAUZ does not pretend `theta` is known. It maintains a belief state:

```math
b_t(\theta)=p(\theta\mid D_t),
```

where `D_t` is all admissible evidence at time `t`.

For a Gaussian local model:

```math
\theta\mid D_t \sim \mathcal N(\mu_t,\Sigma_t).
```

`mu_t` = current estimate.

`Sigma_t` = current uncertainty geometry.

The eigenvectors of `Sigma_t` identify uncertain directions; the largest eigenvalue identifies the current worst-observed local direction.

---

# 2. LEARNING ACTIONS ARE EXPERIMENTS

A candidate learning action `a` is not just “read another source”. It must define a measurable observation model:

```math
y = h_a(\theta)+\varepsilon.
```

For the linear-Gaussian proof slice:

```math
y=a^T\theta+\varepsilon,
```

```math
\varepsilon\sim\mathcal N(0,\sigma_a^2).
```

Each action also has metadata:

```text
cost(a)
risk(a)
ZORR_relevance(a)
transfer_potential(a)
source_authority(a)
redundancy(a | D_t)
```

No universal scalar weights are locked. Multi-objective/lexicographic selection is preferred until empirical tradeoff weights exist.

---

# 3. BAYESIAN UPDATE

For linear-Gaussian evidence with prior `(mu,Sigma)` and scalar observation `y`:

```math
K=\frac{\Sigma a}{\sigma^2+a^T\Sigma a},
```

```math
\mu' = \mu + K(y-a^T\mu),
```

```math
\Sigma'
=
\Sigma
-
\frac{\Sigma aa^T\Sigma}{\sigma^2+a^T\Sigma a}.
```

The covariance update does not depend on the realized value `y`; it describes the expected uncertainty reduction from taking that measurement.

---

# 4. EXPECTED INFORMATION GAIN

General Bayesian experimental design objective:

```math
IG(a\mid D_t)
=
\mathbb E_y\left[
D_{KL}
\left(
 p(\theta\mid D_t,a,y)
 \Vert
 p(\theta\mid D_t)
\right)
\right].
```

For the scalar linear-Gaussian case:

```math
\boxed{
IG(a\mid D_t)
=
\frac12
\log\left(
1+\frac{a^T\Sigma_t a}{\sigma_a^2}
\right)
}
```

This is the first GAUZ learning law:

> Prefer experiments that observe directions where uncertainty is large and measurement noise is low.

Redundant experiments naturally lose value as the posterior contracts in directions already measured.

---

# 5. VALUE OF LEARNING

Pure information gain is not enough for ZORR.

A research action can be mathematically informative but irrelevant to production.

Therefore maintain a vector objective:

```math
q(a)=
[
IG(a),
ExpectedTransfer(a),
ExpectedProductionValue(a),
-Cost(a),
-Risk(a),
-Redundancy(a)
].
```

Do not collapse this vector into one magic score until tradeoff coefficients are measured or explicitly authorized.

A bounded lexicographic policy can be:

```text
LEVEL 0: authority / safety / scope constraints
LEVEL 1: ZORR relevance
LEVEL 2: expected information gain / transfer
LEVEL 3: cost / compute / time
LEVEL 4: convenience
```

---

# 6. WEAK-DIRECTION TARGETING

Eigen-decompose posterior covariance:

```math
\Sigma=V\Lambda V^T.
```

Let:

```math
v_{weak}=\arg\max_v v^T\Sigma v,
```

with `||v||=1`.

A simple candidate experiment is valuable against the current weakest direction when:

```math
|a^T v_{weak}|
```

is large relative to its measurement noise and cost.

This is the same structural idea already used in camera observability research: do not collect more arbitrary evidence; collect evidence aligned with the unresolved singular/eigen direction.

---

# 7. INFORMATION MATRIX / OPTIMAL DESIGN

For local residual Jacobian `J` with weighting `W`:

```math
\mathcal I=J^TWJ.
```

Candidate research criteria:

```math
D\text{-optimal}:\quad \max\log\det\mathcal I,
```

```math
A\text{-optimal}:\quad \min\operatorname{tr}(\mathcal I^{-1}),
```

```math
E\text{-optimal}:\quad \max\lambda_{min}(\mathcal I).
```

Interpretation:

- D-optimal reduces total uncertainty-volume;
- A-optimal reduces average variance;
- E-optimal protects the worst-observed direction.

GAUZ should select the criterion according to the research failure mode, not by one universal rule.

---

# 8. LEARNING AS CONTROL

Let learning state be:

```math
x_t=(\mu_t,\Sigma_t,L_{holdout,t},C_{cal,t},G_t),
```

where:

- `L_holdout` = unseen/changed-case error;
- `C_cal` = confidence calibration state;
- `G_t` = durable knowledge/dependency graph.

Action:

```math
u_t = \text{next experiment / task / reference / test}.
```

State transition:

```math
x_{t+1}=F(x_t,u_t,y_t).
```

A candidate Lyapunov-like research potential is:

```math
V_t
=
\operatorname{tr}(W\Sigma_t)
+
\lambda_h L_{holdout,t}
+
\lambda_c L_{calibration,t}.
```

A learning step is useful only if it produces evidence that tends to reduce the protected research potential or exposes a previously hidden failure.

`READING WITH NO NEW EVIDENCE != PROGRESS`.

No universal lambdas are locked.

---

# 9. ANTI-GOODHART / HELD-OUT TRANSFER

If GAUZ optimizes only the training metric, it can learn to game that metric.

Therefore every serious learning slice should separate:

```text
TRAIN / DEVELOPMENT EVIDENCE
CHANGED / UNSEEN TRANSFER EVIDENCE
UNBIASED AUDIT EVIDENCE
```

Let training loss be `L_train` and unseen transfer loss be `L_test`.

A claimed skill improvement requires evidence that:

```math
\Delta L_{test}<0
```

or that a previously unknown failure boundary became correctly identified.

A lower training loss with worse unseen transfer is overfitting, not learning.

---

# 10. CALIBRATION

A mathematical machine must know how uncertain it is.

For probability forecast `p_i` and binary outcome `y_i`:

```math
Brier
=
\frac1N\sum_i(p_i-y_i)^2.
```

Calibration must be tracked separately from raw accuracy.

A system that is often right but confidently wrong on its failures is unsafe for autonomous research selection.

---

# 11. HYPOTHESIS COMPETITION

Maintain competing hypotheses instead of prematurely collapsing to one explanation.

For hypotheses `H_1,...,H_k`:

```math
p(H_j\mid D)
\propto
p(D\mid H_j)p(H_j).
```

Select future experiments that maximally separate predictions:

```math
a^*
=
\arg\max_a
\mathbb E[
H(H\mid D)-H(H\mid D,y_a)
].
```

This turns “what should I study next?” into an active discrimination problem.

---

# 12. CONCEPT DRIFT / NON-STATIONARY WORLD

Not all ZORR coefficients are stationary forever.

A bounded dynamic model:

```math
\theta_{t+1}=\theta_t+\nu_t,
```

```math
\nu_t\sim\mathcal N(0,Q).
```

`Q=0` means fixed truth in the local model.

`Q>0` permits measured drift.

Do not use forgetting blindly. Increase drift allowance only where data shows that the underlying process actually changes.

---

# 13. KNOWLEDGE GRAPH / CHANGE IMPACT

Let verified knowledge be graph:

```math
G=(V,E).
```

Nodes may represent:

```text
formula
measurement
assumption
source
code path
skill hypothesis
production rule candidate
QC result
```

Edges encode:

```text
depends_on
supports
contradicts
supersedes
validated_by
transfer_tested_by
```

If node `v` changes, the mathematical invalidation radius is a graph reachability problem over dependency edges.

This prevents a fresh contradiction from leaving stale downstream conclusions silently “valid”.

---

# 14. RESEARCH PORTFOLIO / BANDIT VIEW

For several research domains `k`, each has uncertain future value.

A bounded multi-armed-bandit interpretation can allocate study opportunities between:

```text
perspective
camera
color
texture
motion
Babylon scene math
QC statistics
production systems
marketing/sales math
other ZORR-relevant domains
```

Exploration is necessary where uncertainty is high.

Exploitation is necessary where a method already has high demonstrated ZORR value.

Do not optimize only for novelty and do not optimize only for familiar high-confidence domains.

---

# 15. SAFE LEARNING / IDENTITY AND AUTHORITY CONSTRAINTS

GAUZ learning is constrained.

Let protected constraints be:

```math
g_j(x)=0
```

or:

```math
g_j(x)\le0.
```

A local learning/edit direction `delta x` preserving equality invariants satisfies:

```math
J_g\,\delta x=0,
```

therefore:

```math
\delta x\in Null(J_g).
```

This is mathematically analogous to the safe-camera null-space developed in the Babylon camera research.

Research can expand knowledge, but may not silently rewrite:

```text
Constitution
authority boundaries
OWNER relationship
main/canon state
truth discipline
```

---

# 16. STOPPING / “ENOUGH EVIDENCE”

Do not study forever when a decision is already robust.

For decision `a*`, one stopping concept is expected value of sample information:

```math
EVSI
=
\mathbb E[
\max_a U(a\mid D,Y_{new})
]
-
\max_a U(a\mid D).
```

If additional information has lower expected value than its cost and cannot change a protected decision, further research may be wasteful.

Exact operational thresholds remain UNKNOWN until calibrated on real ZORR work.

---

# 17. SYNTHETIC PROOF R01

Executable file:

`docs/research/studio-mathematics/code/gauz_active_learning_proof_r01.py`

Synthetic construction:

```text
latent dimensions = 8
candidate experiments = 80
learning budget = 20 equal-cost experiments
noise variance = 0.04
prior covariance diagonal = [1,1,1,2,2,3,4,5]
40 candidates deliberately redundant around first 3 dimensions
40 candidates diverse across all 8 dimensions
random baseline trials = 1000
```

GAUZ selection rule:

```math
a_t^*
=
\arg\max_a
\frac12\log\left(1+\frac{a^T\Sigma_ta}{\sigma^2}\right).
```

Measured synthetic result:

```text
prior covariance trace = 19.000000
GAUZ active final trace = 0.133772444
random curriculum median final trace = 0.312206666
GAUZ trace reduction vs random median = 57.153%

GAUZ worst-direction variance = 0.022908250
random median worst-direction variance = 0.137697450
GAUZ worst-direction reduction vs random median = 83.363%

fraction of 1000 sampled random schedules worse on trace = 100.0%
fraction worse on worst-direction variance = 100.0%
```

All six declared synthetic proof gates passed:

```text
active posterior trace < random median
active worst-direction variance < random median
active beats all 1000 sampled random schedules on trace in this constructed pool
active beats all 1000 sampled random schedules on worst-direction variance in this constructed pool
posterior trace decreases monotonically
worst eigenvalue decreases monotonically
```

## Truth boundary of the proof

This proves only:

> In this exact synthetic linear-Gaussian candidate pool, selecting the next equal-cost experiment by expected information gain reduced posterior uncertainty more efficiently than the sampled random curricula.

It does **not** prove:

```text
general intelligence
literal self-improving model weights
universal superiority of one acquisition function
production effectiveness on ZORR
changed/unseen real-world transfer
```

---

# 18. GAUZ CORE LOOP

```text
1. DEFINE latent unknowns / decision boundary.
2. BUILD posterior uncertainty, not false certainty.
3. COMPUTE weak directions / degeneracies.
4. ENUMERATE admissible next experiments.
5. ESTIMATE information gain + ZORR relevance + cost/risk.
6. SELECT the best admissible experiment.
7. EXECUTE / MEASURE.
8. BAYES/STATISTICALLY UPDATE.
9. TEST changed/unseen transfer.
10. CHECK calibration and contradictions.
11. INVALIDATE dependent stale conclusions when needed.
12. RECORD provenance + exact evidence durably.
13. REPEAT only if expected additional information is worth its cost.
```

Compact equation:

```math
\boxed{
a_t^*
=
\arg\max_{a\in\mathcal A_{safe}}
\mathcal V
\left(
IG(a),
Transfer(a),
ProductionValue(a),
-Cost(a),
-Risk(a)
\right)
}
```

where `V` is multi-objective/lexicographic until real tradeoff weights are measured.

Then:

```math
b_{t+1}(\theta)
\propto
p(y_t\mid\theta,a_t^*)b_t(\theta).
```

---

# 19. NEXT RESEARCH EDGE — GAUZ R02

The next bounded proof should move beyond the linear-Gaussian toy case:

```text
1. nonlinear hypotheses;
2. heterogeneous experiment costs;
3. correlated/redundant evidence;
4. robust acquisition under model misspecification;
5. calibration loss;
6. explicit held-out transfer objective;
7. multi-domain research allocation;
8. knowledge-graph invalidation radius;
9. concept drift detection;
10. first use on a real ZORR mathematics uncertainty from tracker #222;
11. link to Night School tracker #206 without creating a second learning framework;
12. compare information-gain curriculum against naive recency/novelty/random curricula.
```

Terminal state for R01:

```text
GAUZ_FORMAL_RESEARCH_MODEL = RECORDED
SYNTHETIC_LINEAR_GAUSSIAN_ACTIVE_LEARNING_PROOF = PASS
REAL_ZORR_TRANSFER = NOT PROVEN
PRODUCTION_EFFECTIVENESS = NOT PROVEN
MODEL_SELF_MODIFICATION = NOT CLAIMED
MAIN_MUTATION = NO
MERGE = NO
CANON_LOCK = NO
```
