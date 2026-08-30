# ZORR STUDIO MATHEMATICS — RESEARCH MAP R01

TRACKER = #222
STATUS = RESEARCH / NOT CANON

## Research thesis

Mathematics should be applied wherever it reduces one or more of:

```text
DRIFT
REWORK
UNCERTAINTY
QUEUEING
WASTED COMPUTE
UNPLANNED COST
SCHEDULE VARIANCE
FALSE PASS
FALSE FAIL
```

without destroying:

```text
DIRECTING JUDGEMENT
ACTING
STYLE CHOICE
HERO-SHAPE AUTHORSHIP
OWNER AUTHORITY
```

## 1. Production graph

Represent production as a directed graph:

```math
G=(V,E)
```

where nodes are tasks/assets and directed edges are dependencies.

For task `i` store at minimum:

```math
T_i=(d_i,r_i,p_i,c_i,q_i)
```

where:

- `d_i` = duration distribution;
- `r_i` = required resources;
- `p_i` = prerequisites;
- `c_i` = cost model;
- `q_i` = quality/evidence gate.

Research questions:

- Which nodes are on the critical path?
- Which asset change has the largest downstream impact radius?
- Where can a failed upstream gate invalidate expensive downstream work?
- Which dependency can be removed or simplified?

Change-impact candidate metric:

```math
Impact(v)=|Descendants(v)|
```

A richer expected repair-risk model:

```math
RiskChange(v)=P(failure|change_v) * ExpectedRepairCost(v) * Impact(v)
```

All probability/cost terms remain `UNKNOWN` until measured.

## 2. Flow / bottleneck mathematics

For stage `s`:

```math
lambda_s = arrival rate
mu_s     = completion/service rate
```

If sustained:

```math
lambda_s > mu_s
```

then backlog grows.

Track:

```text
WIP
THROUGHPUT
CYCLE_TIME
WAIT_TIME
REWORK_RATE
BLOCKED_TIME
```

Little-style relation can be used as an observed consistency check in a stable flow regime:

```math
WIP ~= Throughput * CycleTime
```

Do not treat this as exact for a transient creative pipeline without checking stationarity/definitions.

## 3. Rework mathematics

For a production stage:

```math
ReworkRate = ReopenedOrReturned / Completed
```

Expected time lost:

```math
E[T_rework] = sum_k P(E_k) * CostTime(E_k)
```

where `E_k` is an error class.

Research target:

> Find high-frequency/high-cost error classes whose prevention is cheaper than repeated repair.

## 4. Quality statistics

Binary PASS/FAIL is not sufficient for calibration.

Track confusion after downstream verification:

```text
TRUE_PASS
FALSE_PASS
TRUE_FAIL
FALSE_FAIL
```

Candidate metrics:

```math
FalsePassRate = FP/(TP+FP)
```

```math
FalseFailRate = FF/(TF+FF)
```

Expected decision loss:

```math
ExpectedLoss = C_FP * P(FP) + C_FF * P(FF)
```

Costs depend on asset class. A false pass on a recurring hero model may be much more expensive than a false fail on a disposable low-risk asset.

## 5. Threshold calibration

Do not pick QC thresholds by taste alone.

For metric `m`, collect approved and rejected distributions:

```math
p(m|PASS), p(m|FAIL)
```

Then choose candidate operating thresholds using measured tradeoffs rather than one universal number.

Research should report:

```text
sample size
asset class
distribution summary
measurement uncertainty
threshold candidate
false-pass implication
false-fail implication
confidence / limitations
```

## 6. Compute economics

Raw generation/render price is not the production cost metric.

Use:

```math
CostPerApproved = TotalComputeAndLaborCost / ApprovedOutputs
```

Useful secondary measures:

```math
ApprovalYield = ApprovedOutputs / Attempts
```

```math
ComputeEfficiency = ApprovedUsefulCompute / TotalCompute
```

For repeated stochastic generation, compare models/tools by cost per approved asset, not cost per attempt.

## 7. Shot budget optimization

Candidate value model:

```math
V_i = NarrativeImportance_i * VisualImpact_i * ReusePotential_i * FailureRisk_i
```

Candidate allocation problem:

```math
max sum_i V_i * x_i
```

subject to artist-hours, compute, deadline and quality constraints.

Weights and scales are `UNKNOWN`; the formula is a research scaffold, not canon.

## 8. Reliability mathematics

Pipeline quality also requires operational metrics:

```text
SUCCESS_RATE
RETRY_RATE
BROKEN_PUBLISH_RATE
CORRUPT_OUTPUT_RATE
MEAN_TIME_TO_RECOVER
DETERMINISTIC_RERENDER_RATE
```

Candidate reliability:

```math
R = SuccessfulValidRuns / AllDeclaredRuns
```

Do not set SLO numbers until enough telemetry exists.

## 9. Schedule uncertainty / Monte Carlo

A task duration should not always be modeled as a single point estimate.

For each task define an empirical or justified distribution:

```math
D_i ~ P_i(t)
```

For simulation run `k`:

```math
T_project^(k) = ScheduleSolve(D_1^(k),...,D_n^(k))
```

Report quantiles rather than false certainty:

```text
P50 completion
P80 completion
P95 completion
probability before target date
main schedule-risk drivers
```

## 10. Information value

A study/reference/test is valuable when it reduces uncertainty that matters to production.

Candidate model:

```math
InformationValue = InformationGain * ReusePotential / Cost
```

Questions:

- Does another reference reveal new geometry/topology/state?
- Does a test eliminate a dangerous hypothesis?
- Does an experiment reduce uncertainty at a bottleneck?
- Is the result reusable across many shots/assets?

## 11. Resource/task matching

For artist/tool `a` and task `t`, estimate from evidence:

```math
Utility(a,t) = ExpectedQuality(a,t) / ExpectedCost(a,t)
```

subject to schedule, learning, review and specialization constraints.

Do not reduce artists to a single score. Use task-specific evidence and preserve directing/creative authority.

## 12. Studio experiment design

Every proposed mathematical intervention should define:

```text
HYPOTHESIS
BASELINE
METRIC
UNIT
SAMPLE
INTERVENTION
EXPECTED EFFECT
FAILURE MODE
STOP RULE
FRESH VERIFICATION
```

Preferred progression:

```text
OBSERVE
-> BASELINE
-> ONE BOUNDED CHANGE
-> MEASURE
-> COMPARE
-> TRANSFER TO NEW CASE
-> KEEP / REJECT
```

## 13. Priority order

Initial practical priority:

```text
1. REWORK / ERROR COST
2. BOTTLENECK / QUEUE VISIBILITY
3. COST PER APPROVED OUTPUT
4. QUALITY THRESHOLD CALIBRATION
5. ASSET CHANGE IMPACT
6. SCHEDULE UNCERTAINTY
7. RESOURCE OPTIMIZATION
```

Reason: these areas can improve the studio without requiring a new production framework and can be measured from existing ZORR evidence incrementally.

## 14. Hard boundaries

Mathematics must not autonomously decide:

```text
acting
emotion
hero pose
dramatic camera intent
when style should deliberately break its normal rule
final hero FX shape
OWNER taste
canon authority
```

Mathematics may expose options, constraints, risks and measured consequences.

## 15. Next research slices

- collect current ZORR task/error/rework evidence from existing durable sources;
- define a minimal measurement schema without creating a second database;
- calculate baseline rework and throughput metrics where existing data supports them;
- identify the first studio bottleneck supported by evidence;
- test one mathematical intervention against the baseline;
- record outcome under tracker #222.
