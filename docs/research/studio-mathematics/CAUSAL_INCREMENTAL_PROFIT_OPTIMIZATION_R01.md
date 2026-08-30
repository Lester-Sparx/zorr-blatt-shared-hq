# ZORR CAUSAL INCREMENTAL PROFIT OPTIMIZATION — R01

TRACKER = #222
BRANCH = research/zorr-studio-mathematics-r01
STATUS = RESEARCH SLICE / FORMULA-QC PASS / COMMERCIAL EFFECTIVENESS NOT PROVEN
BASE_MAIN = b18ca6b9cce2dce6fe304ca8ae36c05df4f4dcb1
RESEARCH_BASE_HEAD = 73a5fab3f608484dd2ec01ed2b058910b8cf75a3
FRESH_SOURCE_REVIEW = 2026-08-30
MAIN_MUTATION = NO
CANON_LOCK = NO
MERGE = NO unless OWNER explicitly authorizes a merge gate

## 0. Research question

The next highest-value commercial mathematics problem is not generic attribution and not a new marketing dashboard.

It is:

> Which marketing spend is causally incremental, economically contribution-profitable, and sufficiently robust to uncertainty to justify changing the allocation?

This connects four previously separate ideas:

```text
INCREMENTALITY EXPERIMENTS
-> BAYESIAN MMM CALIBRATION
-> RESPONSE / mROI CURVES
-> CONTRIBUTION-PROFIT DECISION UNDER UNCERTAINTY
```

The core failure this slice is designed to prevent is:

```text
ATTRIBUTED REVENUE UP
while
TRUE INCREMENTAL CONTRIBUTION PROFIT <= 0
```

No production budget or price is authorized by this document.

Evidence labels:

- `STANDARD` — established mathematical/causal result or primary methodology.
- `SOURCE-DERIVED` — follows from current ZORR durable law.
- `DERIVED` — direct calculation from declared assumptions.
- `PROJECT` — bounded ZORR research convention.
- `MEASURED` — reserved for actual ZORR experimental/commercial evidence.
- `UNKNOWN` — unsupported; do not invent.

Operating loop remains:

```text
DEFINE -> MEASURE -> CALCULATE -> APPLY -> VERIFY -> RECORD
```

---

# 1. Why causal incremental profit outranks attributed ROAS

[STANDARD / SOURCE-DERIVED]

Let `x` be a marketing decision vector, for example channel spend by period or territory.

Observed outcome after exposure is not itself a causal effect.

Define the incremental outcome relative to a declared counterfactual or baseline `x_0`:

```math
Delta Y(x;x_0) = E[Y(x)-Y(x_0)]
```

For revenue outcome:

```math
Delta R(x;x_0) = E[R(x)-R(x_0)]
```

The economic objective is not gross incremental revenue alone. If `m` is the contribution-margin rate on incremental revenue after product/payment/fulfillment variable costs but before marketing spend, and `C_other(x)` contains other allocation-dependent variable costs:

```math
Pi(x) = m Delta R(x;x_0) - Spend(x) - C_other(x)
```

For a non-revenue KPI with validated incremental contribution value `v` per KPI unit:

```math
Pi(x) = v Delta KPI(x;x_0) - Spend(x) - C_other(x)
```

All ZORR values `m`, `v`, response parameters and channel effects are currently `UNKNOWN` unless measured.

The measurement order is therefore:

```text
CAUSAL EFFECT
-> MONETARY / CONTRIBUTION TRANSLATION
-> COST
-> UNCERTAINTY
-> DECISION
```

not:

```text
PLATFORM ATTRIBUTION
-> ROAS SORT
-> SPEND
```

---

# 2. Experiment-calibrated MMM as the measurement bridge

[STANDARD / READY-MADE]

Google Meridian is explicitly designed as a Bayesian causal MMM and supports incorporating prior information from incrementality experiments into ROI priors.

A compact Bayesian statement is:

```math
p(theta | D, E) proportional_to p(D | theta) p(theta | E)
```

where:

```text
D = observational MMM data
E = prior causal/experimental evidence
theta = media response parameters
```

The purpose is not to force the MMM to equal an experiment. The experiment-informed prior regularizes the model while the likelihood updates it.

Google's calibration paper reports that the ROI/ROAS reparameterization allows experiment information to be expressed directly as a prior and, in simulation, can reduce bias and posterior uncertainty in ROAS estimates.

Primary methodology:
- https://research.google/pubs/media-mix-model-calibration-with-bayesian-priors/
- https://developers.google.com/meridian/docs/causal-inference/rationale-for-causal-inference-and-bayesian-modeling

---

# 3. Match the experiment estimand before using it as a prior

[STANDARD / PROJECT GATE]

An experiment-derived prior is only meaningful when the experiment and MMM quantity refer to sufficiently compatible causal questions.

At minimum declare:

```text
CHANNEL / TREATMENT
POPULATION / GEO SET
TIME WINDOW
OUTCOME DEFINITION
SPEND DEFINITION
COUNTERFACTUAL
LAG / CARRYOVER INTERPRETATION
```

For a channel-level experiment with incremental revenue estimate `Delta R_exp` and spend corresponding to the tested treatment window `S_exp`, the research ROI estimand is:

```math
ROI_exp = Delta R_exp / S_exp
```

Do not calibrate a full-channel ROI prior from an experiment that only measured an incompatible subset without recording that mismatch.

Meridian provides `roi_calibration_period` and `rf_roi_calibration_period` to define a subset of media times to which an ROI prior applies. Current source defines the array shape as:

```text
(n_media_times, n_media_channels)
```

for media and the analogous RF shape for reach/frequency channels.

The source also defines the counterfactual semantics: media is historical except that the tested channel is zeroed during the calibration period; the denominator is spend during the calibration period subject to the documented modeling-window overlap.

Current implementation source:
- https://github.com/google/meridian/blob/05cbc3cb2f258666158b03cce959d90c5f22bcb5/meridian/model/spec.py

Current tests explicitly check valid and invalid calibration-period dimensions and reject `roi_calibration_period` unless the paid-media prior type is ROI:
- https://github.com/google/meridian/blob/05cbc3cb2f258666158b03cce959d90c5f22bcb5/meridian/model/spec_test.py

Important limitation:

```text
SAME CHANNEL NAME != SAME ESTIMAND
```

Calibration requires causal-definition alignment, not string matching.

---

# 4. Turning positive experiment evidence into a reusable ROI prior

[STANDARD / READY-MADE]

If an experiment supports a strictly positive ROI quantity and the modeling assumptions justify a lognormal prior, let the desired prior mean and standard deviation be:

```math
E[ROI] = r_bar > 0
```

```math
SD[ROI] = s >= 0
```

For `ROI ~ LogNormal(mu, sigma)` the exact moment conversion is:

```math
sigma^2 = ln(1 + s^2/r_bar^2)
```

```math
mu = ln(r_bar) - sigma^2/2
```

Do not implement this helper from zero. Meridian 1.8.0 currently exports:

```text
lognormal_dist_from_mean_std
lognormal_dist_from_range
```

and implements the same moment conversion in `meridian/model/prior_distribution.py`.

Exact source:
- https://github.com/google/meridian/blob/05cbc3cb2f258666158b03cce959d90c5f22bcb5/meridian/model/prior_distribution.py

The upstream test suite contains direct references to `lognormal_dist_from_mean_std`:
- https://github.com/google/meridian/blob/05cbc3cb2f258666158b03cce959d90c5f22bcb5/meridian/model/prior_distribution_test.py

## 4.1 Do not force negative/zero-capable evidence into a lognormal prior

[PROJECT / MATHEMATICAL SUPPORT LAW]

A lognormal distribution has positive support. If a credible experiment distribution materially supports zero or negative causal effect, coercing it into a positive-only prior destroys evidence.

Meridian's current model supports `media_effects_dist='normal'` or `'log_normal'` and documents that ROI support differs accordingly.

Therefore:

```text
EXPERIMENT SUPPORT
-> CHOOSE COMPATIBLE MODEL/PRIOR SUPPORT
```

not:

```text
MODEL DEFAULT
-> CLIP EXPERIMENT TO FIT
```

The exact prior family remains a modeling decision that must be justified from evidence.

---

# 5. Posterior health is required before optimization

[READY-MADE / STANDARD]

A posterior distribution is not automatically trustworthy because MCMC completed.

Meridian's current post-modeling guidance requires model-health assessment before using causal outputs and distinguishes causal modeling goals from pure prediction accuracy.

Relevant checks include:

```text
CONVERGENCE
GOODNESS OF FIT
PRIOR-POSTERIOR SHIFT
ROI CONSISTENCY
CONTROL / CONFOUNDER LOGIC
HOLDOUT PREDICTIVE CHECKS AS SUPPORTING EVIDENCE
```

Meridian explicitly notes that causal validity is difficult to assess directly without well-designed experiments and that prediction error should not be the primary target of MMM model selection.

Sources:
- https://developers.google.com/meridian/docs/post-modeling/model-fit
- https://developers.google.com/meridian/docs/post-modeling/health-checks

Research rule:

```text
MODEL HEALTH PASS != CAUSAL TRUTH PROVEN
```

Experiment evidence remains higher-value for direct causal validation.

---

# 6. Fixed-budget equivalence theorem

[DERIVED — HIGH VALUE]

This result determines when ZORR can reuse Meridian's existing outcome-maximizing optimizer directly instead of building a new profit optimizer.

Assume:

```text
A1. total marketing spend B is fixed;
A2. contribution-margin rate m is constant and positive for incremental revenue;
A3. no allocation-dependent variable cost remains outside m;
A4. feasible set X is the same for both objectives.
```

Then for any allocation `x in X` with:

```math
sum_c x_c = B
```

incremental contribution profit is:

```math
Pi(x) = m Delta R(x) - B
```

Because `m > 0` and `B` is constant:

```math
argmax_x Pi(x)
=
argmax_x [m Delta R(x)-B]
=
argmax_x Delta R(x)
```

Therefore:

```text
FIXED BUDGET + CONSTANT POSITIVE CONTRIBUTION RATE
=> MAX INCREMENTAL REVENUE ALLOCATION
   IS ALSO MAX INCREMENTAL CONTRIBUTION-PROFIT ALLOCATION
```

This is important OSS-first leverage: under these assumptions, Meridian's fixed-budget optimizer already solves the allocation ranking problem. ZORR does not need a second optimizer merely to rename the objective.

---

# 7. When the equivalence fails

[DERIVED / PROJECT]

The equivalence above fails if any important assumption fails.

## 7.1 Flexible total spend

When `B` changes:

```math
Pi(B) = m Delta R(B) - B
```

Maximizing `Delta R(B)` is no longer equivalent to maximizing profit because spend is no longer constant.

## 7.2 Different contribution rates

If product/territory/channel `c` maps incremental revenue to contribution at different rates `m_c`:

```math
Pi(x)=sum_c m_c Delta R_c(x_c)-sum_c x_c
```

then raw revenue response is insufficient.

## 7.3 Allocation-dependent non-media costs

Examples:

```text
platform/payment fees that change with mix
fulfillment cost differences
licensing royalty differences
localization/support cost
capacity overtime
refund/chargeback mix
```

must enter the contribution objective rather than being hidden.

## 7.4 Media unit cost or flighting changes with spend

Meridian 1.8.0's `BudgetOptimizer.optimize()` documents important scenario assumptions. Unless overridden with `new_data`, optimization uses historical flighting and historical cost per media unit, and holds them constant with respect to the overall channel budget.

Current source:
- https://github.com/google/meridian/blob/05cbc3cb2f258666158b03cce959d90c5f22bcb5/meridian/analysis/optimizer.py

If auction CPM/CPC, reach quality, territory mix or flighting changes materially as spend scales, a wide unconstrained budget recommendation is not justified by the historical response grid alone.

Use bounded scenarios and refreshed execution assumptions before trusting extrapolation.

---

# 8. Marginal contribution-profit condition

[DERIVED — HIGH VALUE]

Suppose incremental revenue response for channel `c` is differentiable:

```math
Delta R_c = R_c(x_c)
```

and contribution rate is constant `m > 0`.

Then:

```math
Pi_c(x_c)=mR_c(x_c)-x_c
```

The derivative is:

```math
dPi_c/dx_c = m dR_c/dx_c - 1
```

Define revenue marginal ROI:

```math
mROI_c = dR_c/dx_c
```

An unconstrained interior break-even optimum satisfies:

```math
m * mROI_c = 1
```

or:

```math
mROI_c = 1/m
```

This gives a direct translation from revenue mROI to contribution economics.

Examples of the law, not project values:

```text
if incremental outcome is already contribution margin:
  m = 1
  break-even marginal ROI = 1

if incremental outcome is gross revenue:
  the break-even mROI depends on the measured contribution-margin rate
```

ZORR must never use a generic `mROI = 1` break-even rule on gross revenue unless margin translation makes that correct.

For different channel contribution rates:

```math
dPi_c/dx_c = m_c mROI_c - 1
```

so allocation comparisons should use contribution-adjusted marginal return:

```math
CMROI_c = m_c * mROI_c
```

not raw mROI alone.

---

# 9. Fixed-budget marginal allocation condition

[DERIVED]

Under a fixed total budget:

```math
sum_c x_c=B
```

and differentiable concave channel responses, the Lagrangian is:

```math
L = m sum_c R_c(x_c) - sum_c x_c - lambda(sum_c x_c-B)
```

Since `sum_c x_c=B` is fixed, the `-sum_c x_c` term is constant. For active interior channels:

```math
m mROI_c = constant
```

With common `m`:

```math
mROI_1 = mROI_2 = ... = lambda_prime
```

This is the mathematical reason that budget should move toward channels with higher marginal rather than historical average ROI until constraints or diminishing returns equalize the relevant marginal values.

---

# 10. Posterior decision risk instead of point-estimate optimization

[STANDARD BAYESIAN DECISION THEORY / PROJECT]

For posterior draw `d`, define candidate-allocation profit:

```math
Pi^(d)(x) = m^(d) Delta R^(d)(x) - Spend(x) - C_other^(d)(x)
```

Do not discard the posterior distribution into one ROI point estimate before making a budget decision.

For each candidate allocation report at least:

```text
E[Pi(x)]
median Pi(x)
credible interval / quantiles
P(Pi(x) > 0)
P(Pi(x) > Pi(x_baseline))
downside quantile or expected shortfall when useful
```

A risk-constrained research objective can be written:

```math
maximize_x E[Pi(x)]
```

subject to:

```math
P(Pi(x) < Pi(x_baseline)) <= alpha
```

where:

```text
alpha = UNKNOWN / OWNER POLICY VALUE
```

No numeric risk tolerance is invented here.

## 10.1 Simplest-sufficient implementation rule

Do not build a new stochastic optimizer first.

Start with a small candidate set:

```text
HISTORICAL ALLOCATION
MERIDIAN FIXED-BUDGET OPTIMUM
BOUNDED CONSERVATIVE SHIFT
OPTIONAL FEW OWNER-RELEVANT SCENARIOS
```

Evaluate posterior contribution-profit risk across those candidates.

Only if real ZORR data proves that candidate evaluation is insufficient should a new optimization layer be considered, and then use mature SciPy / OR-Tools as appropriate rather than a custom solver.

---

# 11. mROI priors can regularize budget movement

[READY-MADE / CURRENT MERIDIAN]

Current Meridian guidance explicitly notes that mROI priors can be used to regularize budget optimization toward the historical allocation when there is a justified belief that historical budgets were already near optimal.

Source:
- https://developers.google.com/meridian/docs/advanced-modeling/how-to-choose-treatment-prior-types

This is not a default ZORR belief.

The lawful rule is:

```text
EVIDENCE THAT HISTORICAL MIX WAS NEAR OPTIMAL
-> MAY JUSTIFY mROI REGULARIZATION
```

not:

```text
HISTORICAL MIX EXISTS
-> ASSUME IT WAS OPTIMAL
```

---

# 12. Data sufficiency and confounding gate

[READY-MADE / STANDARD]

MMM should not be used merely because an optimizer API exists.

Current Meridian guidance recommends geo-level data when available and emphasizes sufficient data points relative to model parameters, confounder-aware controls and adequate history. It currently gives a rule-of-thumb minimum of about two years of weekly data for geo models and three years for national models, while also warning that actual sufficiency depends on data/model structure.

Source:
- https://developers.google.com/meridian/docs/pre-modeling/collect-data

This is an upstream modeling heuristic, not a ZORR threshold.

Current causal guidance also emphasizes that controls must address variables affecting both media execution and outcome; maximizing predictive fit is not a substitute for causal identification.

Source:
- https://developers.google.com/meridian/docs/post-modeling/model-fit
- https://developers.google.com/meridian/docs/causal-inference/rationale-for-causal-inference-and-bayesian-modeling

ZORR gate:

```text
INSUFFICIENT / NON-IDENTIFIABLE DATA
=> MMM DECISION = NOT PROVEN
```

Do not fill missing time history with fabricated backfill merely to satisfy a model.

---

# 13. OSS-first verification — exact component selected

[READY-MADE]

This slice needs one primary component, not the entire marketing OSS map.

## 13.1 Existing ZORR implementation search

Repository search found no existing production marketing/MMM/incrementality implementation to reuse.

Therefore the next preference is mature upstream OSS.

## 13.2 Selected component: Google Meridian

```text
REPOSITORY = google/meridian
EXACT INSPECTED REF = 05cbc3cb2f258666158b03cce959d90c5f22bcb5
DEFAULT BRANCH = main
PACKAGE VERSION AT REF = 1.8.0
LATEST RELEASE RECORDED IN CHANGELOG = 1.8.0 / 2026-08-14
INSPECTED MAIN COMMIT DATE = 2026-08-29
LICENSE = Apache-2.0
ARCHIVED = false
```

Current package metadata:
- https://github.com/google/meridian/blob/05cbc3cb2f258666158b03cce959d90c5f22bcb5/pyproject.toml

Current version:
- https://github.com/google/meridian/blob/05cbc3cb2f258666158b03cce959d90c5f22bcb5/meridian/version.py

License:
- https://github.com/google/meridian/blob/05cbc3cb2f258666158b03cce959d90c5f22bcb5/LICENSE

Changelog / maintenance evidence:
- https://github.com/google/meridian/blob/05cbc3cb2f258666158b03cce959d90c5f22bcb5/CHANGELOG.md

Relevant API / source inspected:

```text
ModelSpec.roi_calibration_period
ModelSpec.rf_roi_calibration_period
PriorDistribution
lognormal_dist_from_mean_std
BudgetOptimizer.optimize
OptimizationGrid.optimize
use_posterior=True path
```

Relevant tests inspected:

```text
meridian/model/spec_test.py
meridian/model/prior_distribution_test.py
meridian/analysis/optimizer_test.py
```

`optimizer_test.py` explicitly runs optimization scenarios from MCMC `InferenceData` and compares results with expected allocations/outcomes.

## 13.3 Why EconML / CausalML / PyMC / OR-Tools are not added here

[OSS-FIRST / SIMPLEST-SUFFICIENT]

For this exact slice:

```text
EXPERIMENT-INFORMED MMM + RESPONSE CURVES + FIXED-BUDGET ALLOCATION
```

Meridian already supplies the needed Bayesian MMM, ROI prior calibration and budget optimizer.

Adding EconML, CausalML, PyMC or OR-Tools now would increase dependencies without clearing a proven gap.

They remain valid candidates for later exact questions:

```text
heterogeneous uplift / treatment targeting -> EconML OR CausalML
custom Bayesian model outside Meridian's scope -> PyMC
integer / combinatorial budget constraints not handled by Meridian -> OR-Tools
```

but are intentionally NOT adopted in this slice.

---

# 14. Fresh mathematical verification

Performed before repository write.

## V01 — lognormal moment conversion

Input diagnostic values, not ZORR values:

```text
mean = 2.5
std = 0.6
```

Using:

```math
sigma^2 = ln(1+s^2/m^2)
mu = ln(m)-sigma^2/2
```

reconstructed distribution moments were:

```text
mean = 2.5
std = 0.6000000000000005
```

within floating-point error.

Result:

```text
V01 = PASS
```

## V02 — fixed-budget equivalence

For 100 synthetic candidate response values with:

```text
fixed B = 50
constant positive contribution rate m = 0.35
```

the ranking and argmax of:

```math
Delta R(x)
```

and:

```math
0.35 Delta R(x)-50
```

were identical.

Result:

```text
V02 = PASS
```

This is also guaranteed algebraically by positive affine transformation.

## V03 — flexible-budget non-equivalence counterexample

Take:

```math
R(B)=10 sqrt(B)
```

and:

```text
m = 0.5
```

Then:

```math
Pi(B)=5 sqrt(B)-B
```

and:

```math
dPi/dB = 2.5/sqrt(B)-1
```

so the interior profit optimum is:

```math
B^*=6.25
```

while gross incremental revenue continues increasing with `B`.

Result:

```text
V03 = PASS
```

This proves that a flexible-budget revenue maximum is not generally a profit maximum.

## V04 — marginal break-even identity

At the same diagnostic optimum:

```math
mROI(B)=dR/dB=5/sqrt(B)
```

At `B=6.25`:

```math
m * mROI = 0.5 * 2 = 1
```

which matches the derived condition.

Result:

```text
V04 = PASS
```

## V05 — upstream feature/source/test consistency

Fresh inspection confirmed:

```text
Meridian version = 1.8.0
Apache-2.0 license
active main through 2026-08-29
ROI calibration-period API exists
lognormal prior helpers exist
optimizer supports posterior-based optimization
source tests exist for calibration-period validation and optimization scenarios
```

Result:

```text
V05 = PASS
```

---

# 15. ZORR decision packet for future real data

[PROJECT SCHEMA]

Do not create a database for this. A bounded reproducible artifact/notebook/result is sufficient initially.

```yaml
commercial_decision_id:
product_surface:
outcome:
  type: revenue | contribution | KPI
  definition:
baseline_allocation:
candidate_allocations:
experiment_evidence:
  channel:
  estimand:
  geo_population:
  start_date:
  end_date:
  incremental_outcome_estimate:
  standard_error_or_interval:
  spend_definition:
mmm:
  component: google-meridian
  pinned_ref:
  version:
  data_window:
  controls:
  calibration_period:
  model_health:
economics:
  contribution_margin_rate:
  variable_cost_model:
posterior_decision:
  expected_incremental_profit:
  median_incremental_profit:
  interval:
  probability_beats_baseline:
  downside_metric:
assumptions:
  fixed_budget:
  constant_margin:
  fixed_flighting:
  fixed_cost_per_media_unit:
  other:
unknowns:
decision_status:
```

Missing economic or causal inputs remain `UNKNOWN`.

---

# 16. First lawful empirical gate for ZORR

The next real-data step is not to fit Meridian immediately.

First determine whether ZORR currently has enough durable commercial evidence to define:

```text
1. one exact product/revenue surface;
2. one outcome definition;
3. channel/time/geo spend history;
4. actual contribution-margin mapping;
5. control/confounder candidates;
6. any randomized or quasi-experimental incrementality evidence;
7. enough time/geo variation for an identifiable MMM.
```

If these are not available:

```text
MMM FIT = BLOCKED / NOT PROVEN
```

The mathematically correct next action is instrumentation or a bounded experiment, not simulated commercial certainty.

---

# 17. Slice result

```text
CAUSAL_INCREMENTAL_PROFIT_METHOD = PASS
MERIDIAN_OSS_FIT_FOR_THIS_SLICE = PASS
FORMULA_QC = PASS
SOURCE_QC = PASS
COMMERCIAL_EFFECTIVENESS_ON_ZORR = NOT PROVEN
ZORR_CAUSAL_COEFFICIENTS = UNKNOWN
ZORR_MARGIN_INPUTS = UNKNOWN until measured
ZORR_RISK_TOLERANCE = UNKNOWN
PRODUCTION_BUDGET_DECISION = NOT AUTHORIZED
CANON_LOCK = FALSE
MAIN_MUTATION = NO
MERGE = NO
```

Meaning of `PASS`:

The research method, formulas, OSS selection and inspected source boundaries passed this slice's declared checks.

It does **not** mean Meridian has been fit to ZORR data, that any channel is profitable, or that any commercial allocation has been validated.
