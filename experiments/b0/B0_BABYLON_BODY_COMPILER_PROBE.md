# B0 — Babylon Parametric Human / Body Compiler Probe

Status: **SPIKE / EXPERIMENT ONLY / NOT PRODUCTION**

ZB base: `9da550e842c7b2e22418b38d299e83b38e264122`

Pinned donor:
- repository: `cool-japan/oxihuman`
- commit: `603b446854c3d5a9ca478214e7b85008d54786b9`
- pack: `assets/packs/oxihuman-core-v1.ohpk`
- expected bytes: `2,093,260`
- expected SHA-256: `09c4bb1f849fe5d2bc21db6dd8a8bf7c753ee58db185bc46ab4c6b8e0dc0f6f7`

Pinned presentation runtime for this probe:
- `@babylonjs/core@9.22.2`
- `@babylonjs/loaders@9.22.2`
- `xhr2@0.2.1` for Node loader transport

## Question

Can a verified OxiHuman body be fitted from target measurements, compiled to a normal GLB through the donor's public/safety-gated export path, then loaded by Babylon.js headlessly without changing ZB authority semantics or silently changing the compiled geometry contract?

## Probe pipeline

```text
verified OHPK bytes
→ pinned OxiHuman fit_to_measurements(brief-172)
→ build_mesh_prepared()
→ OxiHuman bodysuit-gated GLB export
→ compiled GLB artifact
→ Babylon.js NullEngine + glTF loader
→ independent vertex/index/bounds inspection
→ contract result
```

The target is the already-used deterministic probe:

```json
{"height_cm":172.0,"chest_cm":96.0,"waist_cm":82.0,"hip_cm":98.0,"max_iterations":60}
```

## Acceptance

B0 may report `PROCEED` only if all of the following are true for the exact pinned inputs:

1. OxiHuman commit and OHPK size/SHA match the pins above.
2. Measurement fit executes and produces a real derived mesh.
3. The built mesh reports `has_suit = true` before human-facing GLB export.
4. GLB export succeeds through the normal OxiHuman exporter.
5. Babylon.js 9.22.2 loads the GLB under `NullEngine` with the glTF loader.
6. Babylon reports non-zero render meshes, vertices, and indices.
7. Babylon total vertex/index counts match the compiled Rust-side counts.
8. The three bounding-box spans match the Rust-side spans within tolerance after sorting axes. Axis sorting is intentional because the architecture keeps coordinate policy OPEN; B0 must not create a coordinate-system lock.
9. The fit residual report remains explicit and is not promoted to Character Truth.

## Authority boundary

```text
CHARACTER_DNA = anthropometric authority
CHARACTER-SPECIFIC REST_RIG = skeletal authority
OxiHuman fit params = derived donor state
OxiHuman mesh = derived candidate/compiled geometry
GLB = derived transport artifact
Babylon scene/mesh = presentation/runtime representation
```

B0 does **not** authorize:
- donor slider/fit values writing back to Character DNA;
- donor skeleton or skin weights becoming REST_RIG / production authority;
- coordinate-system lock;
- production runtime integration;
- `hq/state`, task/review/lock/dashboard mutations;
- OWNER LOCK;
- G2;
- Voice-to-Shot.

## Lifecycle

The B0 branch/PR exists only to execute and review this feasibility proof. It must not be interpreted as a production integration PR. A successful probe produces evidence and a recommendation, not runtime authority.
