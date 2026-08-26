# O0 — OxiHuman Donor Feasibility Proof

Status: **SPIKE / EXPERIMENT ONLY**  
ZB base: `149c07e3c531c637c5108c7d52d429232f861b49`  
Upstream: `cool-japan/oxihuman`  
Tag: `v0.2.1`  
Exact upstream commit: `603b446854c3d5a9ca478214e7b85008d54786b9`

This proof evaluates OxiHuman only as a narrow replaceable donor/backend candidate. It does not change protected HQ state, create OWNER LOCK, activate G2/Voice-to-Shot, or promote donor data to ZB authority.

## Verdict

**PROCEED TO AN ISOLATED EXECUTION PROOF, WITH BOUNDARIES.**

The pinned source contains the architecture pieces required for the proposed donor path:

```text
pinned body pack
+ morph targets
+ mesh re-measurement
+ measurement → fit → remeasure solver
+ WASM/browser bridge
+ provenance metadata
```

The source-level feasibility question is therefore answered positively. Production adoption is **not** approved by O0.

## 1. Exact upstream evidence

The workspace declares version `0.2.1` and `Apache-2.0` as the workspace code license.

The pinned core-pack provenance declares:

```text
path: assets/packs/oxihuman-core-v1.ohpk
format: OHPK v1
license: CC0-1.0
bytes: 2093260
base vertices: 21833
targets: 38
sha256: 09c4bb1f849fe5d2bc21db6dd8a8bf7c753ee58db185bc46ab4c6b8e0dc0f6f7
```

The pack provenance also lists measurement targets including bust, underbust, waist and hips, with individual source paths and hashes.

### Hash status

The SHA above is **pinned from upstream provenance**. In the current ChatGPT/GitHub connector environment the binary `.ohpk` bytes were not available in a form that allowed an independent local SHA-256 recomputation. Therefore O0 does **not** claim that the pack hash was independently byte-verified here.

`verify_pack.py` is included so that once the exact `.ohpk` bytes and provenance JSON are present in a local/CI workspace, the byte length and SHA can be independently checked before any donor execution.

## 2. Measurement → fit → remeasure exists in the pinned source

`crates/oxihuman-morph/src/calibration.rs` provides `BodyCalibrator`. It accepts tape measurements and measurement vertex sets, deforms the mesh with morph targets, computes measurements from the deformed vertices, and optimizes morph weights using Nelder–Mead. Its result contains morph parameters, per-measurement residuals, total RMS error, iteration count and convergence state.

This is compatible with the ZB rule:

```text
TARGET MEASUREMENTS
→ derived fit parameters
→ generated/deformed vertices
→ independent re-measurement
→ residual/error
```

It is not compatible with treating resulting morph weights as Character Truth, and O0 explicitly forbids that promotion.

## 3. Engine-level fit uses the morphed mesh as the forward model

`crates/oxihuman-wasm/src/engine_fit.rs` exposes an engine-level `fit_to_measurements` flow. The source describes and implements:

1. direct height solve against re-measured stature;
2. Nelder–Mead over weight / muscle / gender;
3. repeated construction and measurement of the current morphed mesh;
4. local refinement using named MakeHuman `measure/` girth targets;
5. final re-measurement;
6. JSON results containing requested target, measured value and delta.

Accepted input targets are any subset of:

```json
{
  "height_cm": 172.0,
  "chest_cm": 92.0,
  "waist_cm": 76.0,
  "hip_cm": 94.0
}
```

This is important for ZB because the objective is based on measurements of generated geometry rather than simply echoing requested dimensions.

## 4. WASM boundary exists

`crates/oxihuman-wasm/README.md` documents browser and Node `wasm-bindgen` builds and loading the core OHPK pack from bytes. It documents `OxiHumanEngine`, measurement snapshots and the measurement-fit surface.

Therefore a future adapter can remain narrow:

```text
ZB target measurements
→ replaceable OxiHuman execution adapter
→ donor fit parameters / mesh
→ ZB-owned re-measurement + residual QC
→ derived candidate body only
```

No OxiHuman parameter or skeleton crosses back into ZB authority.

## 5. Upstream tests provide relevant evidence, but were not executed here

The pinned repository includes `crates/oxihuman-wasm/tests/measurement_fit.rs`. Those tests are designed to cover pack-backed girth responses and measurement/fit round trips. The source explicitly guards tests when external assets are absent.

O0 inspected those tests but did **not** execute the upstream Rust suite in this environment. The test source is evidence of an existing upstream validation path, not evidence that this O0 run reproduced its results.

## 6. ZB authority boundary

The following remain hard requirements:

```text
CHARACTER_DNA = anthropometric authority
CHARACTER-SPECIFIC REST_RIG = skeletal authority
OxiHuman parameters = derived donor state
OxiHuman morph weights = derived donor state
OxiHuman generated mesh = derived candidate geometry
OxiHuman skeleton ≠ ZB skeletal authority
OxiHuman skin weights ≠ production ZB skinning authority
UNRESOLVED stays UNRESOLVED
```

Forbidden:

- donor slider → DNA writeback;
- donor skeleton → REST_RIG replacement;
- nearest-joint donor weights → production skinning by default;
- preview/fit values → canonical truth;
- coordinate-system lock inferred from donor conventions;
- importing the whole upstream repository into ZB as an unquestioned foundation.

## 7. O0 local verifier

Run the experiment utility against exact bytes:

```bash
python3 experiments/o0/verify_pack.py \
  --pack /path/to/oxihuman-core-v1.ohpk \
  --provenance /path/to/oxihuman-core-v1.provenance.json
```

The verifier fails closed on:

- pack filename mismatch;
- format other than `OHPK v1`;
- license other than `CC0-1.0`;
- byte-count mismatch;
- SHA-256 mismatch.

Synthetic verifier tests:

```bash
python3 experiments/o0/test_verify_pack.py
```

Local O0 TDD evidence before commit: expected RED because `verify_pack` did not yet exist, then GREEN with **6/6 tests passing**.

These synthetic tests validate the ZB verifier only. They are not presented as execution of OxiHuman itself.

## 8. What O0 proves / does not prove

### Proven at source-contract level

- exact upstream revision can be pinned;
- code and asset licensing are separable;
- pack provenance provides format, size, license, topology/target counts and SHA;
- morph-based fitting exists;
- actual deformed geometry is re-measured during fit;
- precise residuals are exposed;
- WASM/browser loading path exists;
- the donor can remain behind a replaceable adapter.

### Still unproven

- independent recomputation of the shipped OHPK SHA in this environment;
- successful execution of the pinned OHPK through the pinned Rust/WASM build in ZB CI;
- coverage of every ZB DNA dimension;
- fit quality for shoulder width, independent chest/pelvis depth, limb segment lengths, hand/foot lengths and REST_RIG surface alignment;
- production skinning quality;
- compatibility of donor topology with the future ZB Surface Contract without an adapter;
- performance budget under ZB runtime constraints.

## 9. Recommended next proof

Do **not** proceed directly to production body integration.

The next donor-specific experiment, if explicitly authorized, should execute the exact pinned OHPK and perform one deterministic round trip:

```text
known target measurements
→ OxiHuman fit
→ generated mesh
→ independent ZB-side re-measurement
→ residual report
```

Acceptance for that execution proof must be based on measured residuals and exact bytes, not donor slider values.

Separately, the architecture sequence may then advance toward B0 only after the donor/body boundary is considered sufficiently proven.

## 10. Scope statement

All O0 repository changes are confined to `experiments/o0/**`.

O0 changes no:

- `hq/state/**`;
- `hq/tasks/**`;
- `hq/reviews/**`;
- `hq/locks/**`;
- dashboard or transition evidence;
- ZB production data;
- runtime/body compiler implementation;
- G2;
- Voice-to-Shot;
- OWNER LOCK.
