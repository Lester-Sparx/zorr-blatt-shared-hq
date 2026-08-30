# ZORR STUDIO MATHEMATICS — DEEPENING R02

TRACKER = #222
BRANCH = research/zorr-studio-mathematics-r01
STATUS = RESEARCH / NOT CANON
BASE_MAIN = b18ca6b9cce2dce6fe304ca8ae36c05df4f4dcb1
OWNER_DIRECTION = CONTINUOUS DEEP STUDY + DURABLE RECORD

## 0. Research thesis

The studio is not only a collection of artists and tools. It is a stochastic, constrained, partially observed production system.

Mathematics is useful when it reduces:

```text
DRIFT
REWORK
WAITING
QUEUE GROWTH
UNCERTAINTY
FALSE PASS
FALSE FAIL
WASTED COMPUTE
SCHEDULE VARIANCE
CHANGE BLAST RADIUS
```

without replacing:

```text
DIRECTING
ACTING
STYLE CHOICE
HERO-SHAPE AUTHORSHIP
OWNER AUTHORITY
```

Evidence labels used here:

- `STANDARD` — primary/official technical source or established mathematical result.
- `SOURCE-DERIVED` — follows from current ZORR durable law.
- `DERIVED` — direct mathematical derivation from declared assumptions.
- `PROJECT` — bounded ZORR research convention.
- `MEASURED` — reserved for future values measured on ZORR evidence.
- `UNKNOWN` — not yet supported; do not invent.

The operating loop remains:

```text
DEFINE -> MEASURE -> CALCULATE -> APPLY -> VERIFY -> RECORD
```

---

# 1. THE STUDIO AS A CLOSED-LOOP DYNAMIC SYSTEM

[PROJECT]

Represent the measurable studio state at time `t` as:

```math
S_t = [WIP_t, Backlog_t, Quality_t, Rework_t, Load_t, Compute_t, Risk_t]
```

Possible controllable interventions:

```math
U_t = [WIPLimit_t, Allocation_t, ReviewGate_t, Priority_t, ProcessSetting_t]
```

Disturbances that are not fully controlled:

```math
D_t = [Complexity_t, StoryChange_t, Failure_t, Absence_t, ToolVariance_t]
```

A general state model is:

```math
S_{t+1} = F(S_t, U_t, D_t) + epsilon_t
```

and observations are:

```math
Y_t = H(S_t) + eta_t
```

where `epsilon_t` is process variation and `eta_t` is measurement noise.

This is not a command to automate artistic judgement. It is a framework for separating:

```text
STATE
CONTROL
DISTURBANCE
MEASUREMENT ERROR
```

before blaming an artist or changing a pipeline.

## 1.1 Control-loop rule

The studio should not react to every one-frame or one-task fluctuation.

A robust intervention loop is:

```text
MEASURE
-> COMPARE TO BASELINE / SLO / CONTROL LIMIT
-> CLASSIFY COMMON VS SPECIAL CAUSE
-> INTERVENE ONLY WHEN EVIDENCE SUPPORTS IT
-> FRESH MEASURE
```

To prevent policy thrashing, use hysteresis when appropriate:

```math
enter intervention if Risk > T_high
exit intervention if Risk < T_low
```

with:

```math
T_low < T_high
```

Thresholds are `UNKNOWN` until measured.

---

# 2. FLOW MATHEMATICS — WIP, THROUGHPUT, CYCLE TIME

[STANDARD]

Little's Law relates average number in a stable system, average arrival/throughput rate, and average time in system:

```math
L = lambda W
```

ZORR interpretation:

```text
L       = average WIP
lambda  = average completed/arriving units per time
W       = average cycle/flow time
```

MIT materials emphasize the stability/steady-state condition. Therefore this must not be applied blindly to a rapidly changing production phase.

Source:
https://betterworld.mit.edu/littles-law/
https://ocw.mit.edu/courses/15-072j-queues-theory-and-applications-spring-2006/

## 2.1 Per-stage consistency check

For stage `s`:

```math
WIP_s \approx Throughput_s * CycleTime_s
```

Use the equality only after definitions and observation windows are consistent.

If observed values violate the relationship strongly, first investigate:

```text
mixed populations
inconsistent time windows
missing events
rework counted differently
unstable/transient queue
censored unfinished tasks
```

before interpreting the result as a production effect.

## 2.2 Flow efficiency

[PROJECT]

```math
FlowEfficiency = TouchTime / TotalCycleTime
```

where:

```text
TouchTime = time actually worked on the asset
TotalCycleTime = calendar time from admitted start to accepted completion
```

Low flow efficiency can identify a waiting/coordination problem even when individual artists are fast.

---

# 3. REWORK AMPLIFICATION

[DERIVED]

Suppose a stage has independent probability `r` that an output is returned for another visit to the same stage.

Expected number of visits is the geometric series:

```math
E[Visits] = 1 + r + r^2 + ... = 1/(1-r)
```

for:

```math
0 <= r < 1
```

Therefore effective load becomes:

```math
lambda_effective = lambda_external / (1-r)
```

Examples are intentionally not assigned project values. The main insight is nonlinear amplification: as rework probability grows, capacity is consumed faster than the raw reject count suggests.

## 3.1 Multi-stage rework as an absorbing Markov model

[DERIVED / RESEARCH]

For multiple transient production states with transition matrix `Q`, expected visit counts can be studied with the fundamental matrix:

```math
N = (I - Q)^(-1)
```

when the inverse exists and the process is absorbing.

This can expose loops such as:

```text
CLEANUP -> QC -> CLEANUP
COLOR -> COMPOSITE -> COLOR
LAYOUT -> KEY -> LAYOUT
```

Important distinction:

```text
PLANNED PRECEDENCE GRAPH = DAG
REWORK / STATE TRANSITION GRAPH = may contain cycles
```

Do not force rework loops into a DAG model.

---

# 4. PRODUCTION GRAPH / CRITICAL PATH / CHANGE IMPACT

[STANDARD / READY-MADE]

NetworkX provides maintained algorithms for DAGs including:

```text
is_directed_acyclic_graph
topological_sort
descendants
transitive_reduction
dag_longest_path
dag_longest_path_length
```

Source:
https://networkx.org/documentation/stable/reference/algorithms/dag.html

ZORR should use an existing graph library before implementing graph traversal/critical-path infrastructure from zero.

## 4.1 Change impact

[DERIVED]

For asset/task node `v`:

```math
ImpactRadius(v) = |Descendants(v)|
```

A weighted form:

```math
WeightedImpact(v) = sum_{u in Descendants(v)} RepairCost_u * P(Invalidated_u | Change_v)
```

All conditional probabilities and costs are `UNKNOWN` until measured.

## 4.2 Monte Carlo criticality index

[DERIVED]

When task durations are random, one deterministic critical path can be misleading.

Across `K` schedule simulations:

```math
CriticalityIndex_i = count(i on critical path) / K
```

This identifies tasks that are frequently schedule-critical rather than only critical under mean durations.

---

# 5. CONSTRAINED SCHEDULING — DO NOT BUILD A SECOND SCHEDULER

[STANDARD / READY-MADE]

Google OR-Tools CP-SAT is designed for constraint problems and provides scheduling examples, including job-shop scheduling with precedence and resource-exclusivity constraints.

Sources:
https://developers.google.com/optimization/cp
https://developers.google.com/optimization/scheduling/job_shop

ZORR research implication:

```text
EXISTING ZORR SCHEDULING SURFACE
-> if a mathematical solve is needed, use mature solver
-> add only bounded adapter/data mapping
```

not:

```text
build a new studio scheduler framework
```

## 5.1 Core model

For task `i`:

```math
start_i >= end_j
```

for each prerequisite `j -> i`.

For resource `r`, incompatible overlapping tasks are forbidden.

Candidate objectives can include:

```text
MINIMIZE MAKESPAN
MINIMIZE WEIGHTED LATENESS
MINIMIZE CONTEXT SWITCHES
MINIMIZE EXPENSIVE-IDLE TIME
```

but quality/canon/safety constraints remain hard constraints, not soft weights.

---

# 6. ARTIST / TOOL / TASK ASSIGNMENT

[STANDARD / READY-MADE]

Assignment is a standard optimization problem. OR-Tools supports assignment via MIP, CP-SAT, linear sum assignment and minimum-cost flow approaches.

Source:
https://developers.google.com/optimization/assignment

[PROJECT]

Define evidence-based cost matrix:

```math
C[a,t] = ExpectedTotalCost(artist_or_tool=a, task=t)
```

Possible components:

```text
expected labor time
expected review time
historical rework probability
specialization mismatch
continuity/context switching cost
compute cost
```

Do not collapse a person into one universal score.

The model must be task-specific and uncertainty-aware.

## 6.1 Lexicographic objective order

Recommended research order:

```text
1. HARD SAFETY / AUTHORITY / QC CONSTRAINTS
2. REQUIRED QUALITY FEASIBILITY
3. DEADLINE RISK
4. REWORK RISK
5. COST / COMPUTE
```

This is safer than one opaque scalar score where cheapness can mathematically compensate for unacceptable quality.

---

# 7. STATISTICAL PROCESS CONTROL — DETECT DRIFT BEFORE FAILURE

[STANDARD]

NIST describes process monitoring/control through SPC and control charts, including Shewhart, CUSUM, EWMA and multivariate charts.

Sources:
https://www.nist.gov/publications/nistsematech-engineering-statistics-handbook-chapter-6-process-or-product-monitoring
https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc31.htm
https://www.itl.nist.gov/div898/handbook/pmc/section1/pmc12.htm

Potential ZORR monitored series:

```text
FACE_LANDMARK_ERROR
SILHOUETTE_ERROR
LINE_WIDTH_DRIFT
PALETTE_DEVIATION
APPROVAL_YIELD
REWORK_RATE
RENDER_RETRY_RATE
CYCLE_TIME
QUEUE_AGE
```

## 7.1 Control limits are not specification limits

[STANDARD / IMPORTANT]

A control limit describes expected process behavior under an in-control baseline.

A specification/QC limit describes what the product is allowed to be.

Therefore:

```text
CONTROL LIMIT != ART/QUALITY ACCEPTANCE LIMIT
```

A process can be statistically stable but consistently bad; or unstable while still temporarily inside a quality limit.

## 7.2 Stability before capability claims

NIST states process stability in terms of constant distribution behavior over time, including mean/variance concepts, and treats stability as prerequisite to capability analysis.

Source:
https://www.itl.nist.gov/div898/handbook/ppc/section4/ppc45.htm

ZORR implication:

Do not estimate a permanent QC capability from a short transient period after a major workflow/model change.

---

# 8. DOE — TEST WHETHER AN INTERVENTION ACTUALLY CAUSED IMPROVEMENT

[STANDARD]

NIST defines Design of Experiments as a systematic approach to data collection intended to support defensible conclusions while minimizing experimental runs, time and cost.

Sources:
https://itl.nist.gov/div898/handbook/pmd/section3/pmd31.htm
https://www.itl.nist.gov/div898/handbook/pri/section3/pri3.htm

DOE can serve four ZORR purposes:

```text
COMPARE
SCREEN FACTORS
MODEL RESPONSE
OPTIMIZE
```

## 8.1 Compatible with ONE-CHANGE LAW

For a simple repair question:

```text
BASELINE
-> ONE BOUNDED CHANGE
-> MEASURE
-> NEW/CHANGED TRANSFER
```

remains preferred.

For a deliberate research experiment with multiple interacting factors, use factorial/fractional-factorial design instead of random one-at-a-time tuning.

Possible factors:

```text
resampler
cleanup strength
line simplification
shadow-level count
texture suppression
review stage
model/tool choice
```

Responses:

```text
quality metric
approval yield
artist correction time
cycle time
compute cost
```

## 8.2 Response surfaces

[STANDARD]

NIST response-surface methodology supports models including interaction and quadratic terms and is intended for finding improved/optimal process settings and robust regions.

Sources:
https://www.itl.nist.gov/div898/handbook/pri/section3/pri336.htm
https://www.itl.nist.gov/div898/handbook/pri/section5/pri53.htm

Generic quadratic model:

```math
y = beta_0 + sum_i beta_i x_i + sum_i beta_ii x_i^2 + sum_{i<j} beta_ij x_i x_j + epsilon
```

The fitted optimum is not production truth; confirmatory runs on changed/unseen material are required.

---

# 9. MEASUREMENT SYSTEM BEFORE PROCESS OPTIMIZATION

[STANDARD]

NIST separates measurement-process characterization, bias/accuracy, variability, gauge R&R, control and uncertainty.

Sources:
https://www.itl.nist.gov/div898/handbook/mpc/mpc_d.htm
https://www.nist.gov/itl/sed/topic-areas/measurement-uncertainty

ZORR implication:

Before claiming that a process improved by a small amount, verify that the measurement system can resolve that amount.

For a metric:

```math
Observed = TrueSignal + MeasurementError
```

Potential measurement error sources:

```text
segmentation error
registration error
landmark detector variance
human reviewer disagreement
color-management mismatch
resampling differences
mask leakage
rounding
```

## 9.1 Reviewer repeatability / reproducibility

[PROJECT]

For subjective-but-structured QC, study:

```text
same reviewer, same asset, repeated judgement -> repeatability
multiple reviewers, same asset -> reproducibility
```

Do not use artist identity as a quality proxy; measure the judgement system itself.

---

# 10. UNCERTAINTY PROPAGATION

[STANDARD]

NIST treats measurement outputs as functions of uncertain inputs and supports analytical/GUM-style and Monte Carlo propagation.

Sources:
https://www.nist.gov/itl/sed/topic-areas/measurement-uncertainty
https://uncertainty.nist.gov/

For:

```math
y = f(x_1,...,x_n)
```

first-order covariance propagation can be written:

```math
Var(y) \approx J Sigma J^T
```

where `J` is the Jacobian of `f` at the operating point and `Sigma` is input covariance.

For nonlinear or bounded systems, Monte Carlo propagation may be more appropriate.

## 10.1 Report values with uncertainty

Bad:

```text
face drift = 1.40 Cpx
```

when measurement noise is unknown.

Better structure:

```text
estimate
measurement method
repeatability
coverage/uncertainty interval
threshold distance
```

Exact project uncertainty conventions remain `UNKNOWN` pending experiments.

---

# 11. DECISION THEORY — QC AS EXPECTED LOSS, NOT ONLY A SCORE

[DERIVED]

Let latent truth be `GOOD` or `BAD` and action be `PASS` or `FAIL`.

Define:

```text
C_FP = cost of passing a bad asset
C_FF = cost of failing a good asset
```

Given evidence `x`:

```math
Risk(PASS|x) = C_FP * P(BAD|x)
```

```math
Risk(FAIL|x) = C_FF * P(GOOD|x)
```

Choose the lower expected-loss action, subject to hard critical-failure gates.

This formalizes why a hero character identity gate should have a different tolerance tradeoff than a disposable low-risk background detail.

Project costs and posterior probabilities are `UNKNOWN` until calibrated.

---

# 12. SLI / SLO / ERROR-BUDGET THINKING FOR STUDIO RELIABILITY

[STANDARD / TRANSFERRED PRINCIPLE]

Google SRE distinguishes:

```text
SLI = measured indicator
SLO = target/range for that indicator
error budget = allowed miss relative to SLO
```

and recommends selecting a small set of meaningful indicators, often using percentiles rather than averages for skewed long-tail behavior.

Sources:
https://sre.google/sre-book/service-level-objectives/
https://sre.google/workbook/error-budget-policy/
https://sre.google/workbook/monitoring/

Potential studio SLIs:

```text
VALID_EXPORT_YIELD
DETERMINISTIC_RERENDER_YIELD
ASSET_READBACK_SUCCESS
QUEUE_TO_FIRST_REVIEW_LATENCY
P95 CYCLE TIME
REWORK_RATE
QC FALSE-PASS RATE
ARCHIVE EVIDENCE READBACK SUCCESS
```

No studio SLO numbers are set in this research slice.

## 12.1 Do not optimize the average only

For cycle/review/render latency track at least:

```text
median
P80
P95
P99 when sample size supports it
```

A small tail of extremely delayed assets can dominate production pain while the mean looks acceptable.

---

# 13. TASK-DURATION DISTRIBUTIONS AND CENSORING

[STANDARD / READY-MADE]

Unfinished tasks are right-censored observations: their exact completion duration is unknown, but it is known to exceed the elapsed duration so far.

SciPy supports censored data and empirical survival functions.

Sources:
https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.CensoredData.html
https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.ecdf.html

ZORR implication:

Do not estimate cycle time by dropping all unfinished work; doing so can bias durations downward.

Define survival function:

```math
S(t) = P(T > t)
```

Useful questions:

```text
P(task still unfinished after 2 days)?
P(review still pending after 6 hours)?
How did the distribution change after intervention?
```

Specific time targets are `UNKNOWN` until measured.

---

# 14. MONTE CARLO SCHEDULE / COST RISK

[STANDARD / DERIVED APPLICATION]

NIST describes Monte Carlo as a method for propagating uncertainty by specifying input distributions and repeatedly sampling them.

Sources:
https://www.nist.gov/services-resources/software/monte-carlo-tool
https://www.nist.gov/publications/preface-uncertainty-evaluation-monte-carlo-method

For schedule simulation `k`:

```math
D_i^(k) ~ P_i(t)
```

then solve the precedence/resource schedule:

```math
T_project^(k) = ScheduleSolve(D_1^(k),...,D_n^(k))
```

Report:

```text
P50 completion
P80 completion
P95 completion
P(deadline met)
criticality index by task
main variance contributors
```

Do not invent triangular distributions merely because min/mode/max are convenient. Prefer empirical distributions when data exists; otherwise label the distribution assumption explicitly.

---

# 15. VALUE OF INFORMATION — WHICH RESEARCH SHOULD BE DONE NEXT?

[DERIVED]

Let `theta` represent an unknown production state and `a` a decision.

Current best expected loss:

```math
L_before = min_a E[L(a, theta)]
```

For a possible measurement/test result `Y`:

```math
L_after = E_Y[ min_a E[L(a, theta) | Y] ]
```

Expected value of information:

```math
EVI = L_before - L_after
```

Net research value:

```math
NetEVI = EVI - Cost(test)
```

ZORR uses:

```text
RUN THE TEST / BUILD THE REFERENCE
```

when expected decision improvement justifies its cost and it addresses a real production uncertainty.

This gives a deeper form to the existing DUNCAN information-gain law.

---

# 16. MULTI-OBJECTIVE OPTIMIZATION / PARETO FRONT

[DERIVED]

Studio decisions usually have multiple competing outputs:

```text
QUALITY
TIME
COST
COMPUTE
REWORK
RISK
```

Avoid prematurely forcing all objectives into one arbitrary scalar.

A candidate solution `A` Pareto-dominates `B` if it is no worse in every objective and strictly better in at least one.

Research should first expose the Pareto frontier, then let directing/OWNER policy choose tradeoffs.

Hard quality/authority constraints remain outside the tradeoff surface.

---

# 17. RISK-BASED QC SAMPLING WITHOUT BLIND SPOTS

[PROJECT]

Review attention is scarce. Candidate inspection allocation:

```math
ReviewPriority_i = Impact_i * FailureProbability_i * FailureCost_i
```

but risk-based inspection alone can miss unknown failure classes.

Therefore preserve two streams:

```text
TARGETED HIGH-RISK QC
+
SMALL UNBIASED AUDIT SAMPLE
```

The audit stream is used to estimate whether the risk model itself has blind spots.

Sampling rates remain `UNKNOWN`.

---

# 18. ANTI-GOODHART / ANTI-SINGLE-SCORE LAW

[PROJECT]

No single metric should become the studio's universal optimization target.

Examples of failure:

```text
maximize throughput -> hidden quality loss
minimize rework -> reviewers stop rejecting bad assets
maximize PASS rate -> thresholds become permissive
minimize cycle time -> difficult hero work is avoided
```

Therefore every optimization metric needs:

```text
PRIMARY OBJECTIVE
HARD GUARDRAILS
COUNTER-METRICS
AUDIT SAMPLE
```

This directly extends DUNCAN's rule that a critical failure overrides an aggregate score.

---

# 19. MINIMAL EXISTING-EVIDENCE TELEMETRY — NO SECOND DATABASE

[PROJECT]

Research should derive metrics from existing GitHub / workflow / archive evidence wherever possible.

Minimum event fields when already available or cheaply recordable:

```yaml
event_id:
timestamp:
source_ref:
asset_id:
task_id:
stage:
actor_or_tool:
input_ref:
output_ref:
state_from:
state_to:
started_at:
ended_at:
reviewed_at:
status:
error_class:
rework_of:
quality_metrics:
compute_usage:
evidence_ref:
```

Rules:

```text
NO SECOND DATABASE
NO FABRICATED BACKFILL
MISSING = UNKNOWN
RAW GITHUB / ARCHIVE EVIDENCE WINS
DERIVED METRICS MUST BE REBUILDABLE
```

---

# 20. FIRST DEEP STUDIO EXPERIMENTS

## EXP-A — Rework amplification baseline

Question:

```text
Which production stages generate the largest effective workload multiplier through returns/reopens?
```

Need:

```text
stage transitions
return/reopen events
accepted completions
elapsed times
```

Outputs:

```text
rework probability by stage
expected visits per accepted output
estimated time amplification
confidence / sample limits
```

## EXP-B — Tail latency baseline

Question:

```text
Which stage owns the P95/P99 waiting tail, not only the average delay?
```

Use censored treatment for unfinished work.

## EXP-C — QC calibration

Question:

```text
Which gates have false-pass or false-fail evidence downstream?
```

Outputs:

```text
confusion counts by asset class
expected-loss analysis
critical-failure overrides
```

## EXP-D — Process drift detection

Question:

```text
Can an EWMA/CUSUM/control-chart signal detect degradation earlier than terminal failures?
```

Do not deploy production alarms until retrospective validation proves useful sensitivity/specificity.

## EXP-E — Change blast radius

Question:

```text
Which source assets/policies invalidate the most expensive downstream work when changed?
```

Build from existing dependency evidence; do not create a new asset database.

---

# 21. RESEARCH PASS GATE FOR THIS R02

This document can reach `RESEARCH PASS` only if:

```text
[ ] core formulas dimensionally consistent
[ ] model assumptions stated
[ ] primary/official sources fresh-read where external claims matter
[ ] ready-made OSS identified before custom infrastructure
[ ] project thresholds not invented
[ ] DAG vs cyclic rework distinction explicit
[ ] measurement uncertainty separated from true process variation
[ ] no math rule overrides artistic/OWNER authority
[ ] no main/canon/production mutation
```

Production effectiveness remains `NOT PROVEN` until ZORR measurements/experiments validate transfer.

---

# 22. PRIMARY / OFFICIAL RESEARCH SOURCES — FRESH 2026-08-30

1. NIST/SEMATECH Engineering Statistics Handbook — Process Monitoring and Control
   https://www.nist.gov/publications/nistsematech-engineering-statistics-handbook-chapter-6-process-or-product-monitoring

2. NIST — Control Charts
   https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc31.htm

3. NIST — Process Control Techniques
   https://www.itl.nist.gov/div898/handbook/pmc/section1/pmc12.htm

4. NIST — Process Stability
   https://www.itl.nist.gov/div898/handbook/ppc/section4/ppc45.htm

5. NIST — Design of Experiments
   https://itl.nist.gov/div898/handbook/pmd/section3/pmd31.htm

6. NIST — Response Surface Designs
   https://www.itl.nist.gov/div898/handbook/pri/section3/pri336.htm

7. NIST — Process Optimization
   https://www.itl.nist.gov/div898/handbook/pri/section5/pri53.htm

8. NIST — Measurement Uncertainty
   https://www.nist.gov/itl/sed/topic-areas/measurement-uncertainty

9. NIST — Monte Carlo Tool
   https://www.nist.gov/services-resources/software/monte-carlo-tool

10. Google OR-Tools — Constraint Optimization / CP-SAT
    https://developers.google.com/optimization/cp

11. Google OR-Tools — Job Shop Scheduling
    https://developers.google.com/optimization/scheduling/job_shop

12. Google OR-Tools — Assignment
    https://developers.google.com/optimization/assignment

13. NetworkX — Directed Acyclic Graph Algorithms
    https://networkx.org/documentation/stable/reference/algorithms/dag.html

14. SciPy — CensoredData
    https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.CensoredData.html

15. SciPy — ECDF / survival function
    https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.ecdf.html

16. Google SRE — Service Level Objectives
    https://sre.google/sre-book/service-level-objectives/

17. Google SRE — Error Budget Policy
    https://sre.google/workbook/error-budget-policy/

18. Google SRE — Monitoring
    https://sre.google/workbook/monitoring/

19. MIT — Little's Law / queueing references
    https://betterworld.mit.edu/littles-law/
    https://ocw.mit.edu/courses/15-072j-queues-theory-and-applications-spring-2006/

---

# 23. NEXT RESEARCH EDGE

Next highest-value mathematical directions:

```text
1. measure ZORR rework transitions from durable evidence
2. measure cycle-time distributions including unfinished/censored work
3. derive initial dependency/change-impact graph from existing refs
4. define SPC baselines only after stable measurement windows exist
5. evaluate one bounded intervention with DOE discipline
6. quantify uncertainty of the QC measurements themselves
7. estimate value-of-information for the next reference/test before spending production effort
```

No numerical production threshold becomes canon from this document alone.
