# GRANI — Presentation Truth Probe

Status: **SPIKE / EXPERIMENT ONLY / NOT PRODUCTION**

ZB base: `9da550e842c7b2e22418b38d299e83b38e264122`

## Question

Can downstream presentation intentionally alter the perceived frame while keeping canonical Body, Motion, Action, and Physical Camera truth byte-identical and fully recoverable?

## Architecture contract under test

```text
BODY TRUTH
→ MOTION TRUTH
→ ACTION TRUTH
→ PHYSICAL CAMERA / CAMERA TRUTH
→ VIEW PRESENTATION / GRANI
→ PERCEIVED FRAME
```

Core law:

```text
PHYSICAL CAMERA ≠ potentially PERCEIVED FRAME under presentation / Grani
```

Reality-disagreement effects belong downstream of canonical Camera Truth.

## Synthetic proof requirements

GRANI passes only if all are machine-verified:

1. Canonical Body Truth bytes/SHA are identical before and after presentation evaluation.
2. Canonical Motion Truth bytes/SHA are identical before and after presentation evaluation.
3. Canonical Action Truth bytes/SHA are identical before and after presentation evaluation.
4. Canonical Physical Camera bytes/SHA are identical before and after presentation evaluation.
5. Neutral and reality-disagreement presentation intents over the exact same canonical packet produce distinct perceived-frame hashes.
6. Presentation metadata explicitly marks disagreement as `DERIVED_PERCEIVED`, never `PHYSICAL_TRUTH`.
7. Disabling GRANI restores the canonical physical-camera view deterministically.
8. Presentation diagnostics/readout are read-only and cannot rewrite the presentation intent or canonical packet.
9. Repeated execution is deterministic.

## Authority boundary

```text
Body / Motion / Action Truth = upstream canonical input
Physical Camera / Camera Truth = canonical physical view state
View Presentation / Grani = downstream derived interpretation
Perceived Frame = derived presentation result
Diagnostics = read-only findings
```

GRANI does **not** authorize:
- production renderer/effects integration;
- Babylon presentation integration;
- presentation writeback into Camera/Action/Motion/Body Truth;
- coordinate-system lock;
- `hq/state` or protected-state mutation;
- OWNER LOCK;
- G2;
- Voice-to-Shot.

Anything produced by this branch is throwaway proof infrastructure and must not be treated as production implementation.
