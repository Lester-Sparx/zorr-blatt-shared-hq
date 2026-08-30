# ZORR OPEN-SOURCE MARKETING MATHEMATICS STACK — R01

TRACKER = #222
BRANCH = research/zorr-studio-mathematics-r01
STATUS = OWNER-DIRECTED / RESEARCH / NOT CANON

## HARD LAW

For marketing, sales, growth, pricing, causal inference, forecasting, retention, experimentation and optimization:

```text
EXISTING ZORR CODE
-> STANDARD / NATIVE PLATFORM
-> MATURE OPEN-SOURCE IMPLEMENTATION
-> MINIMAL ZORR-SPECIFIC GLUE
```

Do not create a custom MMM engine, causal-inference framework, Bayesian sampler, optimization solver, survival-analysis engine, experimentation framework, or forecasting library when maintained OSS already supplies the required mathematics.

Every adopted OSS component must be checked for:

```text
repository
exact version/ref
license
maintenance state
API/tests
reproducibility
fit to ZORR use case
```

Open weights / available source != automatically acceptable license. Verify each project before production adoption.

## 1. MMM / media-response modeling

### Google Meridian

Use case:

```text
marketing mix modeling
incrementality-informed media measurement
adstock / saturation
ROI / response curves
budget optimization
reach-frequency analysis
```

Primary upstream:
https://github.com/google/meridian
https://developers.google.com/meridian

Fresh research evidence on 2026-08-30 indicates Meridian is an actively maintained open-source MMM framework. The repository identifies an Apache-2.0 license and current 2026 release line. Pin an exact release only at implementation time after fresh verification.

ZORR rule:

```text
DO NOT BUILD CUSTOM MMM CORE
USE MERIDIAN WHEN DATA / IDENTIFIABILITY REQUIREMENTS ARE SATISFIED
```

## 2. Causal effect / uplift / heterogeneous treatment effects

### Microsoft EconML

Use case:

```text
causal effect estimation
heterogeneous treatment effects
what-if response estimation
experimental / observational causal ML
```

Primary upstream:
https://www.microsoft.com/en-us/research/project/econml/
https://github.com/py-why/EconML

Microsoft Research describes EconML as open-source software for estimating individualized causal responses using machine-learning methods.

### Uber CausalML

Use case:

```text
uplift modeling
meta-learners
causal trees / forests
campaign targeting research
heterogeneous treatment effect estimation
```

Primary upstream:
https://github.com/uber/causalml

Fresh upstream documentation shows maintained Python installation paths and test suites. Pin a release/ref and verify license before production use.

Selection law:

```text
DO NOT USE BOTH BY DEFAULT
CHOOSE THE SMALLEST MATURE TOOL THAT MATCHES THE IDENTIFIED CAUSAL QUESTION
```

## 3. Bayesian modeling / uncertainty

### PyMC

Use case:

```text
Bayesian regression
hierarchical creative/channel models
posterior uncertainty
price elasticity models
retention / demand models
probabilistic forecasting
```

Primary upstream:
https://github.com/pymc-devs/pymc
https://www.pymc.io/

PyMC is a mature open-source probabilistic-programming package supporting MCMC and variational inference.

ZORR rule:

```text
DO NOT WRITE CUSTOM MCMC / VARIATIONAL INFERENCE ENGINES
```

## 4. Classical statistics / survival / censored data

### SciPy

Use case:

```text
statistical tests
distributions
optimization helpers
censored data
ECDF / survival functions
numerical methods
```

Primary upstream:
https://github.com/scipy/scipy
https://docs.scipy.org/

### statsmodels

Use case:

```text
regression
time series
GLM
statistical diagnostics
state-space models
```

Primary upstream:
https://github.com/statsmodels/statsmodels
https://www.statsmodels.org/

### lifelines

Candidate use case:

```text
Kaplan-Meier
Cox proportional hazards
customer / audience retention survival analysis
```

Primary upstream:
https://github.com/CamDavidsonPilon/lifelines
https://lifelines.readthedocs.io/

Before production adoption, fresh-verify version, license and maintenance state.

## 5. Optimization / allocation

### Google OR-Tools

Use case:

```text
budget constraints
assignment
integer / linear / constraint optimization
channel / territory / campaign allocation
resource allocation
```

Primary upstream:
https://github.com/google/or-tools
https://developers.google.com/optimization

ZORR rule:

```text
DO NOT BUILD A CUSTOM SOLVER
```

Use a mathematical optimizer only where the objective and constraints are explicitly defined and causal response estimates are sufficiently trustworthy.

## 6. Graph / network effects

### NetworkX

Use case:

```text
referral graphs
content/distribution networks
campaign dependency graphs
influence/reach topology research
```

Primary upstream:
https://github.com/networkx/networkx
https://networkx.org/

Do not infer causal influence from graph centrality alone.

## 7. General machine learning / calibration

### scikit-learn

Use case:

```text
calibration curves
Brier/log-loss diagnostics
classification / regression baselines
cross-validation
clustering only when decision-useful
preprocessing
```

Primary upstream:
https://github.com/scikit-learn/scikit-learn
https://scikit-learn.org/

ZORR rule:

```text
BASELINE FIRST
COMPLEX MODEL ONLY AFTER SIMPLE MODEL FAILS A MEASURED REQUIREMENT
```

## 8. Experiment-analysis principle

For randomized marketing tests, use mature scientific Python tooling rather than a custom ZORR statistics engine:

```text
NumPy
SciPy
statsmodels
PyMC when Bayesian inference is justified
```

Experiment design must still specify:

```text
unit of randomization
primary outcome
minimum effect of interest
power / uncertainty target
stopping rule
multiple-comparison handling where relevant
predeclared analysis
```

No library fixes a badly designed experiment.

## 9. Open-source decision matrix

Before adopting a component score/record at least:

```text
FUNCTIONAL FIT
LICENSE
ACTIVE MAINTENANCE
REPRODUCIBLE VERSION
TEST COVERAGE / VALIDATION EVIDENCE
DATA REQUIREMENTS
COMPUTE COST
INTEGRATION COST
LOCK-IN RISK
CUSTOM-GLUE SIZE
```

The decision must not be based on GitHub stars alone.

## 10. Prohibited custom infrastructure unless a proven gap exists

```text
CUSTOM MMM FRAMEWORK
CUSTOM ATTRIBUTION ENGINE
CUSTOM CAUSAL ML FRAMEWORK
CUSTOM BAYESIAN SAMPLER
CUSTOM SURVIVAL PACKAGE
CUSTOM OPTIMIZATION SOLVER
CUSTOM EXPERIMENT STATISTICS ENGINE
CUSTOM FORECASTING FRAMEWORK
CUSTOM MARKETING DATABASE
CUSTOM CRM
```

A thin adapter, schema mapper, reproducible notebook/script or deterministic QC wrapper is allowed only when it connects ZORR evidence to a proven upstream component.

## 11. Marketing research execution order

```text
QUESTION
-> SEARCH EXISTING ZORR EVIDENCE
-> SEARCH STANDARD / PRIMARY THEORY
-> SEARCH MATURE OSS
-> INSPECT SOURCE / API / TESTS / LICENSE
-> SELECT MINIMUM SUFFICIENT TOOL
-> PIN VERSION/REF
-> RUN BOUNDED EXPERIMENT
-> VERIFY ON CHANGED / UNSEEN CASE
-> RECORD EVIDENCE
```

`README READ != LEARNED CAPABILITY`.

Where practical, inspect upstream source modules and tests relevant to the exact method being adopted.

## 12. Current initial OSS map

```text
MMM / media response         -> Google Meridian
causal ML                    -> EconML OR CausalML
Bayesian models              -> PyMC
classical statistics         -> SciPy / statsmodels
survival / churn             -> SciPy / lifelines
optimization                 -> OR-Tools
graphs                       -> NetworkX
ML baselines / calibration   -> scikit-learn
```

This is a research map, not a mandate to install all components. `ONE QUESTION -> MINIMUM SUFFICIENT OSS`.

## 13. Next research actions

```text
1. inspect Meridian model/source/tests deeper
2. compare EconML vs CausalML by exact ZORR causal use cases
3. inspect PyMC hierarchical modeling patterns for creative/territory uncertainty
4. inspect OSS survival tooling for retention / repeat-purchase cohorts
5. define an OSS-first causal experiment template
6. define version/license provenance schema without creating a new database
7. validate all selected tools on small synthetic examples before touching real commercial decisions
```

No production marketing budget, price, channel decision or sales forecast is authorized by this document alone.
