# ZORR 9:16 PIXEL-CONTROL SIGMA EXECUTION CONTRACT R20

STATUS = SOURCE-EQUIVALENT SIGMA CONTRACT PASS / TARGET R17 RUNTIME FINGERPRINT NOT PROVEN  
DATE = 2026-08-31  
TARGET = exact 1080x1920 masked SDXL inpaint/outpaint hard base  
MODE = HARD OSS-FIRST / REPRODUCIBILITY / NO IMAGE GENERATION OR EDIT

## 1. One concrete open gap closed

R16 deliberately stopped at integer timestep semantics and recorded:

```text
SIGMA_VECTOR = NOT PROVEN
```

That left a reproducibility hole: two executions could report the same model, seed, requested/effective timesteps, precision and device while silently using a different Euler noise-level schedule because a sigma-affecting scheduler default/config changed.

R20 changes exactly one control boundary:

```text
SCHEDULER EXECUTION IDENTITY

R16:
exact requested/effective timestep indices
+ sigma vector NOT PROVEN

R20:
exact selected sigma construction semantics
+ explicit sigma-affecting defaults
+ exact current-host float32 sigma receipt
+ exact begin-index mapping into add_noise and scheduler.step
+ binary content fingerprints
```

No model, prompt, seed, strength, guidance, mask, canvas, seam, ControlNet, image bytes or source-truth rule is changed.

## 2. HARD OSS-FIRST inspection before glue

Pinned project Diffusers source is `c1bf18c92c6285334adcaac7e75ef8946a227f49`, version `0.41.0.dev0`, Apache-2.0. Fresh upstream `main` inspected on this run is `2e618cb6027037597cf80905fc3e356a71923087`.

Relevant blobs are byte-identical between the project pin and fresh main:

```text
StableDiffusionXLInpaintPipeline = 3f18cbe21d0fe12f89859d188dba2a487f3d87c5
EulerDiscreteScheduler           = eac6efe18aaf775b846e7536fd972686d3ec9683
Euler scheduler tests            = ee99465abfc39e7a7ce7a6734b22dbeb42df5efd
LICENSE                           = 038e32f6445e8f265bde482613cf0d2f43d86dbc
```

Pinned `EulerDiscreteScheduler` constructs the selected `scaled_linear` schedule as:

```text
betas = torch.linspace(sqrt(beta_start), sqrt(beta_end), N, float32) ** 2
alphas = 1 - betas
alphas_cumprod = cumprod(alphas)
training_sigma = sqrt((1 - alphas_cumprod) / alphas_cumprod)
```

For `interpolation_type = linear`, `set_timesteps()` evaluates inference sigmas with `np.interp()` at the requested timestep positions and appends the terminal sigma. The pinned constructor default is `final_sigmas_type = zero`, so the selected terminal sigma is exactly `0.0` float32.

The upstream Euler test suite also treats the sigma schedule as execution-significant: `full_loop_custom_sigmas()` captures `scheduler.sigmas`, reconstructs the scheduler from those sigmas, runs the loop, and checks the result against the ordinary schedule path.

## 3. Previously implicit sigma-affecting defaults are now explicit

The selected model scheduler config already pins:

```text
num_train_timesteps = 1000
beta_schedule       = scaled_linear
beta_start          = 0.00085
beta_end            = 0.012
timestep_spacing    = leading
steps_offset        = 1
interpolation_type  = linear
prediction_type     = epsilon
use_karras_sigmas   = false
```

R20 additionally binds pinned scheduler defaults that can change the selected sigma path or endpoint:

```text
trained_betas            = null
rescale_betas_zero_snr   = false
use_exponential_sigmas   = false
use_beta_sigmas          = false
final_sigmas_type        = zero
timestep_type            = discrete
```

This is an execution-identity rule, not a quality recommendation.

## 4. Strength 0.99 selects sigma index 1, not sigma index 0

R16 proved requested timesteps:

```text
[951, 901, 851, 801, 751, 701, 651, 601, 551, 501,
 451, 401, 351, 301, 251, 201, 151, 101, 51, 1]
```

and:

```text
strength = 0.99
init_timestep = 19
t_start = 1
scheduler.order = 1
begin_index = t_start * order = 1
```

The pinned SDXL inpaint pipeline calls `scheduler.set_begin_index(1)` before latent preparation. The pinned Euler `add_noise()` uses `sigmas[begin_index]` when `begin_index` is set and no denoising step has run. The first `scheduler.step()` initializes its step index from the same `begin_index`.

Therefore:

```text
full sigma index 0 -> timestep 951 -> skipped by strength=0.99 path
full sigma index 1 -> timestep 901 -> initial add_noise sigma
full sigma index 1 -> timestep 901 -> first scheduler.step sigma
...
full sigma index 19 -> timestep 1 -> last effective scheduler.step sigma
full sigma index 20 -> terminal successor sigma = 0.0
```

This closes a replay/reporting ambiguity left open by integer timestep logging alone.

## 5. Current-host deterministic sigma receipt

MEASURED environment:

```text
Python           = 3.13.5 CPython
OS               = Linux x86_64
Torch            = 2.10.0+cpu
Torch CUDA       = None
CUDA available   = false
NumPy            = 2.3.5
Diffusers import = absent
```

Diffusers is not imported or executed. R20 mirrors only the exact inspected scheduler scalar operations with the installed Torch/NumPy runtime.

The resulting full float32 vector contains 21 values: 20 scheduler values plus terminal zero:

```text
0  11.028335571289062
1   8.390686988830566
2   6.506400108337402
3   5.134433269500732
4   4.116698265075684
5   3.3477649688720703
6   2.756196975708008
7   2.2928547859191895
8   1.9234442710876465
9   1.6236929893493652
10  1.376179575920105
11  1.1682164669036865
12  0.9904093742370605
13  0.8356532454490662
14  0.6983985900878906
15  0.574050784111023
16  0.4583331346511841
17  0.3461872935295105
18  0.22814728319644928
19  0.04131447896361351
20  0.0
```

Decimal text is not the authoritative identity. R20 serializes contiguous little-endian IEEE-754 binary32 bytes and hashes them:

```text
FULL 21 SIGMAS SHA-256
= dd2b4c6776c6cad5ddb460a30f3906d4ccb3b1f694bf9e6e9e89a2dba07d578f

EFFECTIVE DENOISE SIGMAS [1:20], 19 values SHA-256
= e03af84d27673cb3cd8226551a084405224f01ead40a3ccc6c0189b993da24ec

SUCCESSOR SIGMAS [2:21], 19 values SHA-256
= 600d524c9374a76235a04b0665cfdf03752792232a57b4f2d402ceabf8a1a1e2
```

Exact binary32 checks:

```text
sigma[0] timestep 951 = 11.028335571289062 -> LE bytes 10 74 30 41
sigma[1] timestep 901 =  8.390686988830566 -> LE bytes 41 40 06 41
sigma[20] terminal     =  0.0               -> LE bytes 00 00 00 00
```

The first-run path starts from `sigma[1]`, not `sigma[0]`.

## 6. Target-runtime boundary remains fail-closed

The current host is CPU-only and does not satisfy R17. R20 does not promote the current float32 fingerprint into a claim about a physically executed `torch==2.10.0+cu126` host.

Required future target-host check:

```text
R17 exact host PASS
-> R18 exact 18-file snapshot PASS
-> R19 fp16/cuda precision gate PASS
-> recompute/capture scheduler sigma receipt on that exact environment
-> compare full/effective/successor binary32 fingerprints
-> only then call TARGET_R17_SIGMA_FINGERPRINT proven
```

If a target fingerprint differs, stop and inspect runtime dependency/numeric provenance. Do not hide the difference with a tolerance or silently change the baseline.

## 7. Fresh tests

```text
R20 deterministic suite = 13/13 PASS
R16 regression          = 10/10 PASS
COMPILEALL               = PASS
```

Coverage includes exact predecessor identities, pinned/fresh upstream source identities, fail-closed sigma-affecting defaults, beta drift rejection, exact float32 fingerprints, begin-index mapping, skipped timestep-951 sigma, shared initial-noise/first-step sigma, terminal zero transition, and preserved runtime/visual/ControlNet boundaries.

No image was generated or edited.

## 8. Model-license boundary fresh recheck

The already selected model remains:

```text
model        = diffusers/stable-diffusion-xl-1.0-inpainting-0.1
revision     = 212ee7d92278cfec477f0ccd1e369cd9d6e9c7e3
license tag  = openrail++
license name = CreativeML Open RAIL++-M License
```

The Hugging Face model page and immutable revision model card were fresh-rechecked during this run and still expose that metadata. R20 inherits the R12 provenance decision and makes no new legal interpretation. `FRAMEWORK LICENSE != MODEL-WEIGHT LICENSE` remains unchanged.

## 9. Truth boundary

SOURCE-DERIVED: exact Diffusers pinned/current refs and blobs; Apache-2.0 framework license; selected beta/sigma construction; terminal-zero default; pipeline begin-index behavior; Euler add_noise/step begin-index semantics; upstream custom-sigma test surface; current model-card license metadata.

MEASURED: current host Python/Torch/NumPy/CUDA state; exact 21-value source-equivalent float32 sigma vector on this host; exact binary fingerprints; R20 13/13 tests; R16 10/10 regression; compileall PASS.

DERIVED: effective begin index is 1; timestep-951 sigma is skipped; timestep-901 sigma is used by both initial add_noise and first Euler step; 19 effective denoising sigmas use 19 successor sigmas ending in terminal zero.

UNKNOWN / NOT PROVEN:

```text
TARGET_R17_SIGMA_FINGERPRINT      = NOT PROVEN
REAL_DIFFUSION_RUNTIME             = NOT PROVEN
RAW_REAL_BACKEND_LEAKAGE           = UNKNOWN
FREE_SEAM_BACKGROUND_CONTINUITY    = NOT MEASURED ON REAL BACKEND
MINIMUM_VRAM_BYTES                 = UNKNOWN
PRODUCTION_VISUAL_QUALITY          = NOT PROVEN
CONTROLNET_DEPTH_EDGE_NEED         = NOT PROVEN
```

## 10. Next hard edge

Do not change model, prompt, seed, strength, scheduler, seam parameters or add structural conditioning. The CPU host yielded a new reproducibility receipt rather than repeating the blocked CUDA/Hub path.

When a genuinely compatible host exists, continue:

```text
R17 host
-> R18 snapshot identity
-> R19 precision
-> R20 target sigma fingerprint
-> R08/R12 launch composition
-> explicit OWNER authorization
-> one raw masked R04 proposal
-> R05 raw KEEP leakage
-> R03 hard source recomposite
-> exact KEEP QC
-> R09/R11 real FREE seam/background measurement
```

Only a measured real-backend failure may justify ControlNet/depth/edge conditioning.
