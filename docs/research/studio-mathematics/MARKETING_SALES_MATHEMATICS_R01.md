# ZORR MARKETING / SALES MATHEMATICS — R01

TRACKER = #222
BRANCH = research/zorr-studio-mathematics-r01
STATUS = OWNER-DIRECTED / RESEARCH / NOT CANON
BASE_MAIN = b18ca6b9cce2dce6fe304ca8ae36c05df4f4dcb1

## 0. Prime commercial question

ZORR mathematics must answer not only:

> How do we make the product better?

but also:

> How do we convert product quality into measurable demand, purchase, licensing, margin, retention, and reinvestment?

The commercial chain is modeled as:

```text
PRODUCT QUALITY
-> ATTENTION
-> INTEREST
-> INTENT
-> CONVERSION
-> REVENUE
-> CONTRIBUTION MARGIN
-> RETENTION / REPEAT PURCHASE
-> REINVESTMENT
```

No link may be assumed. Each link must be measured or remain `UNKNOWN`.

## 1. Commercial objective

A useful top-level objective is expected incremental contribution profit:

```math
ExpectedIncrementalProfit = IncrementalRevenue - VariableCost - IncrementalMarketingCost
```

For decision vector `x` over channels, creatives, territories, offers, release windows, and prices:

```math
x^* = argmax_x E[IncrementalContributionProfit(x)]
```

subject to:

```text
BRAND / OWNER CONSTRAINTS
PRODUCT QUALITY GATES
BUDGET
CAPACITY
LEGAL / PLATFORM CONSTRAINTS
RISK LIMITS
```

Revenue alone is not sufficient because high revenue can coexist with negative contribution margin.

## 2. Demand model

Let demand be:

```math
Q = f(P, A, C, D, R, W, S, X) + epsilon
```

where:

- `P` = price;
- `A` = advertising/media exposure;
- `C` = creative strength;
- `D` = distribution/accessibility;
- `R` = reputation/social proof;
- `W` = release timing/window;
- `S` = segment/territory state;
- `X` = external conditions.

All coefficients are `UNKNOWN` until estimated from experiments or observational models.

## 3. Price elasticity

Own-price elasticity:

```math
E_p = (dQ/dP) * (P/Q)
```

Interpretation:

```text
|E_p| > 1 -> elastic demand
|E_p| < 1 -> relatively inelastic demand
```

This is descriptive, not a command to raise or lower prices blindly.

Cross-price elasticity for product `i` relative to alternative `j`:

```math
E_ij = (dQ_i/dP_j) * (P_j/Q_i)
```

Useful for bundles, editions, merchandise tiers, licensing packages, and substitute/complement analysis.

## 4. Unit economics

For acquired customer/fan `u`:

```math
Contribution_u = Revenue_u - VariableCost_u - AcquisitionCost_u - ServiceCost_u
```

Aggregate acquisition cost:

```math
CAC = AcquisitionSpend / IncrementalNewCustomers
```

Do not use total attributed customers in the denominator when incrementality is unknown.

A simplified expected lifetime contribution:

```math
LTV = sum_{t=0}^{T} E[Margin_t * Survival_t] / (1+r)^t
```

where `r` is a discount rate if long horizons justify discounting.

A useful constraint is not merely `LTV > CAC`, but:

```math
P(LTV - CAC > 0) sufficiently high
```

with uncertainty explicitly reported.

## 5. Funnel mathematics

For funnel stages:

```text
IMPRESSION
VIEW
ENGAGED VIEW
VISIT
WISHLIST / FOLLOW / LEAD
PURCHASE
REPEAT / UPSELL / LICENSE
```

conditional conversion:

```math
CR_{i->j} = N_j / N_i
```

End-to-end conversion:

```math
CR_{0->k} = product_i CR_{i->i+1}
```

This makes bottlenecks visible. A weak purchase rate can originate upstream in audience mismatch rather than checkout design.

## 6. Incrementality before attribution

Observed conversions after exposure do not prove causal effect.

Define incremental lift:

```math
Lift = E[Y | treatment] - E[Y | counterfactual no-treatment]
```

Incremental ROAS:

```math
iROAS = IncrementalRevenue / IncrementalAdSpend
```

Preferred evidence order:

```text
RANDOMIZED HOLDOUT / GEO EXPERIMENT
-> STRONG QUASI-EXPERIMENT
-> CALIBRATED MMM
-> PLATFORM ATTRIBUTION AS DIAGNOSTIC
```

Attribution is useful operationally but must not be confused with causality.

## 7. Marketing Mix Modeling (MMM)

[READY-MADE / PRIMARY]

Google Meridian is an open-source MMM framework designed for causal marketing measurement and budget optimization. Its model supports media transformations such as adstock and saturation and can use prior information and experiments for calibration.

Primary source:
https://developers.google.com/meridian

A generic channel response model:

```math
Sales_t = Base_t + sum_c beta_c * Saturation(Adstock(Spend_{c,t})) + Controls_t + epsilon_t
```

### 7.1 Adstock

Carryover can be represented recursively:

```math
A_t = X_t + alpha A_{t-1}
```

for a simple geometric case, with `0 <= alpha < 1`.

Exact Meridian implementations/parameterizations should follow its documented model rather than this simplified research equation.

### 7.2 Saturation

Marketing response usually has diminishing returns. A generic Hill-type curve:

```math
Response(x) = x^s / (x^s + k^s)
```

where `k` controls half-saturation and `s` shape.

Parameters remain `UNKNOWN` until fitted.

## 8. Budget allocation by marginal return

For channel response `R_c(x_c)`, allocate spend where marginal contribution is highest:

```math
MR_c = dR_c/dx_c
```

At an interior optimum under one budget constraint and comparable monetary output:

```math
MR_1 = MR_2 = ... = lambda
```

subject to minimum/maximum channel constraints and uncertainty.

The practical question is:

> Where does the next dollar/hryvnia/euro of spend create the highest expected incremental contribution profit?

not:

> Which channel had the highest historical ROAS?

## 9. Creative mathematics

A creative is not just a channel asset. It is an experimental treatment.

Represent creative `c` with feature vector:

```math
z_c = [hook, character, color, motion, typography, duration, CTA, music, framing, promise, proof]
```

Response:

```math
Y_c = f(z_c, audience, placement, frequency, time) + epsilon
```

Do not infer causal contribution of a feature from one winning creative. Use repeated tests, factorial designs where practical, or hierarchical models across creatives.

## 10. Bayesian creative testing / bandits

For repeated creative/channel selection, estimate uncertain conversion or profit distributions rather than only point estimates.

A simple Bernoulli conversion model can use:

```math
p_c ~ Beta(alpha_c, beta_c)
```

After observations:

```math
alpha_c' = alpha_c + successes
beta_c'  = beta_c  + failures
```

Thompson sampling can balance exploration and exploitation by sampling from posteriors.

However, bandits are not a substitute for clean causal experiments when treatment effects or long-term brand effects matter.

## 11. Audience segmentation

Do not optimize only for demographic labels.

Potential measurable state:

```text
ACQUISITION SOURCE
CONTENT RESPONSE
PRICE RESPONSE
RETENTION
PURCHASE TYPE
REGION
LANGUAGE
PLATFORM
ENGAGEMENT DEPTH
```

For segment `s`:

```math
Value_s = E[IncrementalMargin_s] - ExpectedServiceAndAcquisitionCost_s
```

Segmentation must remain useful for decisions, not become arbitrary clustering.

## 12. Retention and survival

For recurring engagement/customer relationship:

```math
S(t) = P(T > t)
```

where `T` can represent time until churn/inactivity.

Hazard:

```math
h(t) = f(t)/S(t)
```

Use cohorts because aggregate retention can hide acquisition-mix changes.

## 13. Cohort value

For acquisition cohort `k`:

```math
LTV_k(t) = cumulative contribution margin generated by cohort k up to age t
```

Compare cohorts at equal age, not calendar totals.

This separates product/marketing improvement from mere growth in acquisition volume.

## 14. Virality / referral loop

A simplified referral reproduction number:

```math
K = invitations_per_user * invite_conversion_probability
```

For broader organic spread, replace invitations with measurable exposure-generation events.

`K > 1` does not guarantee sustainable growth because retention, saturation, network overlap, platform limits, and finite market size matter.

## 15. Market size as a distribution, not one number

Instead of one unsupported TAM number, model scenarios:

```math
RevenuePotential = ReachableAudience * PurchaseProbability * ARPPU
```

with distributions over each uncertain input.

Monte Carlo output should report:

```text
P10
P50
P90
probability of break-even
main uncertainty drivers
```

## 16. Break-even marketing spend

If incremental gross contribution per converted customer is `M` and incremental conversion probability per acquired lead is `p`, expected contribution per lead is:

```math
E[ContributionPerLead] = p * M
```

Maximum economically rational cost per lead before other risk adjustments:

```math
CPL_break_even = p * M
```

Analogous calculation applies to impressions/clicks when downstream probabilities are modeled.

## 17. Release-window optimization

For release time `t`:

```math
ExpectedValue(t) = Demand(t) * Margin(t) - CompetitionCost(t) - DelayCost(t)
```

Potential factors:

```text
seasonality
competitive releases
platform events
production readiness
marketing lead time
territory calendars
fan anticipation decay/growth
```

Do not choose a launch date solely from generic industry seasonality; calibrate to ZORR evidence.

## 18. Marketing-production coupling

Marketing should affect production decisions only through measured expected value, not trend chasing.

For production feature `f`:

```math
CommercialVOI(f) = ExpectedIncrementalCommercialValue(f) - IncrementalProductionCost(f)
```

Examples:

```text
trailer hero shot
key visual variant
character reveal
localized poster
merchandise-ready design element
short-form cutdown
```

Hard artistic/canon constraints remain non-tradable.

## 19. Portfolio mathematics

If ZORR develops multiple products/IP surfaces:

```math
PortfolioReturn = sum_i w_i R_i
```

and risk depends on covariance:

```math
Var(R_p) = w^T Sigma w
```

This is useful for allocating marketing/production capital among releases whose outcomes are correlated.

Do not diversify merely for mathematical appearance; only real products/opportunities enter the model.

## 20. Brand effect vs direct-response effect

Separate short-horizon measurable conversion from long-horizon brand state.

A research state-space representation:

```math
Brand_{t+1} = rho Brand_t + gamma Media_t + delta ProductExperience_t + noise
```

```math
Sales_t = f(Brand_t, Price_t, Distribution_t, Media_t, Season_t) + epsilon_t
```

This prevents forcing every campaign to pay back within an arbitrarily short attribution window.

## 21. Frequency / fatigue

Response may depend on repeated exposure count `n`:

```math
P(conversion | n)
```

Marginal gain:

```math
Delta_n = P(conversion|n+1) - P(conversion|n)
```

When marginal gain becomes small or negative, further frequency may waste spend or create fatigue.

Thresholds must be measured by platform/audience/creative.

## 22. Localization economics

For territory/language `g`:

```math
LocalizationValue_g = ExpectedIncrementalMargin_g - LocalizationCost_g - IncrementalSupportCost_g
```

Use uncertainty intervals and option value when a localization creates future reuse across episodes/products.

## 23. Merchandise / licensing mathematics

For SKU/license opportunity `i`:

```math
ExpectedProfit_i = P(success_i) * Upside_i - DevelopmentCost_i - InventoryRisk_i - OpportunityCost_i
```

Inventory products require explicit overage/underage cost modeling.

For digital/licensing products with low marginal inventory cost, capacity and cannibalization become more relevant than stock risk.

## 24. Experiment design for selling

Every commercial intervention should declare:

```text
HYPOTHESIS
PRIMARY METRIC
GUARDRAIL METRICS
UNIT OF RANDOMIZATION
TARGET POPULATION
TREATMENT
CONTROL
POWER / MINIMUM EFFECT OF INTEREST
STOP RULE
ANALYSIS PLAN
```

Do not stop tests merely when a favorable p-value appears.

## 25. Sequential learning

Commercial learning loop:

```text
QUESTION
-> BASELINE
-> TEST
-> CAUSAL ESTIMATE
-> UNCERTAINTY
-> DECISION
-> NEW SEGMENT / NEW TIME / NEW CREATIVE TRANSFER
-> DURABLE RECORD
```

One campaign success does not prove a universal rule.

## 26. Sales probability / pipeline

For B2B licensing/sponsorship/distribution opportunities, use stage-conditional probability rather than subjective single percentage.

If pipeline stages are `S_0...S_n`:

```math
P(close) = product_i P(S_{i+1} | S_i)
```

Expected opportunity value:

```math
EV = P(close) * ContributionIfWon - ExpectedPursuitCost
```

Calibration must compare predicted probabilities against actual outcomes.

## 27. Calibration of commercial forecasts

For predictions `p_i`, group comparable predictions and compare predicted probability with observed frequency.

A forecast system claiming 70% should succeed about 70% over a sufficiently large comparable set.

Track:

```text
Brier score
calibration curve
log loss when appropriate
segment-wise calibration
```

No forecast confidence is trustworthy without calibration evidence.

## 28. Anti-Goodhart commercial law

Never optimize a proxy without guardrails.

Examples:

```text
CTR up, purchase quality down
views up, retention down
ROAS up, incrementality zero
conversion up, refunds/churn up
CAC down, low-value segment mix up
```

For every primary commercial metric keep:

```text
PRIMARY OBJECTIVE
CAUSAL CHECK
MARGIN CHECK
RETENTION CHECK
BRAND/QUALITY GUARDRAIL
```

## 29. Commercial north-star research vector

Do not collapse this prematurely to one KPI. Track a vector:

```math
M = [
IncrementalDemand,
IncrementalRevenue,
ContributionMargin,
CAC,
LTV,
Retention,
Conversion,
OrganicLift,
BrandLift,
ForecastCalibration,
Risk
]
```

Optimization should expose Pareto tradeoffs before OWNER/directing chooses policy.

## 30. ZORR commercial master equation

A useful conceptual chain is:

```math
CommercialValue = ProductValue * Discoverability * Persuasion * Accessibility * Retention
```

This multiplicative form is a research heuristic, not a measured law. Its purpose is to expose a critical fact: if one essential factor is near zero, excellence elsewhere may not produce sales.

A more operational model is:

```math
ExpectedStudioValue = ExpectedIncrementalContributionProfit + StrategicOptionValue - RiskCost
```

subject to artistic, canon, legal, production, and OWNER constraints.

## 31. Mandatory research program

Marketing/sales mathematics is now a first-class research foundation beside image quality and production mathematics.

Priority research slices:

```text
1. DEFINE ZORR PRODUCT / REVENUE SURFACES
2. DEFINE FUNNEL EVENT TAXONOMY USING EXISTING SYSTEMS
3. MEASURE BASELINE CONVERSION / RETENTION / MARGIN WHEN DATA EXISTS
4. IDENTIFY WHICH SALES CLAIMS ARE ATTRIBUTION VS CAUSAL
5. BUILD EXPERIMENT DISCIPLINE FOR CREATIVE / OFFER / CHANNEL TESTS
6. USE MMM ONLY WHEN DATA VOLUME / TIME SERIES SUPPORTS IT
7. MODEL PRICE / OFFER ELASTICITY
8. ESTIMATE COST PER INCREMENTAL APPROVED CUSTOMER, NOT COST PER CLICK
9. CONNECT MARKETING LEARNING BACK TO PRODUCTION WITHOUT TREND-CHASING
10. OPTIMIZE REINVESTMENT INTO THE HIGHEST-MARGINAL-VALUE PRODUCTION AND DISTRIBUTION WORK
```

## 32. Primary / official sources checked

- Google Meridian — open-source Marketing Mix Modeling and budget optimization framework:
  https://developers.google.com/meridian

- Google Meridian documentation — model, media response and optimization surfaces are to be preferred over custom MMM infrastructure when applicable.

Existing ZORR laws still apply:

```text
EXISTING ZORR CODE -> NATIVE/STANDARD PLATFORM -> MATURE OSS/UPSTREAM -> MINIMAL ZORR GLUE
```

No custom marketing platform, attribution engine, MMM framework, CRM, or data warehouse is authorized by this research document.

## 33. Boundary

This document establishes marketing/sales mathematics as a mandatory research foundation. It does not set:

```text
prices
marketing budgets
channel allocations
CAC targets
LTV targets
ROI targets
launch dates
territory priorities
sales forecasts
```

Those remain `UNKNOWN` until measured from actual ZORR commercial data and authorized by OWNER.
