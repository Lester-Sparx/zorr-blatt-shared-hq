# C1 — Cinematography Truth Probe

Status: **SPIKE / EXPERIMENT ONLY / NOT PRODUCTION**

ZB base: `9da550e842c7b2e22418b38d299e83b38e264122`

## Question

Can one immutable Action Truth support multiple intentional camera interpretations while keeping camera/operator/presentation layers strictly downstream and non-authoritative?

## Architecture contract under test

```text
ACTION TRUTH
→ SHOT INTENT
→ CAMERA TRUTH
→ OPERATOR PERFORMANCE
→ FRAME COMPOSITION
→ VIEW PRESENTATION
→ FRAME
```

Core laws:

```text
CAMERA DOES NOT FOLLOW ACTION. CAMERA INTERPRETS ACTION.
THE OPERATOR IS A PERFORMER.
CAMERA MOVEMENT MUST HAVE A REASON, A TARGET AND A SETTLE.
BIG HIT ≠ AUTOMATIC CAMERA SHAKE.
DIAGNOSTICS MUST NOT SILENTLY REWRITE AUTHORED SHOTS.
```

## Synthetic proof requirements

C1 passes only if all of these are machine-verified:

1. The canonical Action Truth bytes/hash are identical before and after all cinematography evaluation.
2. Two different shot intents derived from the same Action Truth produce different Camera Truth hashes.
3. Required moving-camera phases are ordered exactly:
   `HOLD → INITIATE → TRAVEL → REFRAME → SETTLE`.
4. A high-impact action does not produce shake unless shake is explicitly authored with a reason.
5. Attention can transfer between semantic anchors while the physical camera remains on HOLD.
6. Operator performance is a derived layer and does not rewrite canonical physical Camera Truth bytes/hash.
7. Diagnostics detect at least `CONTACT_OUTSIDE_FRAME` and `UNINTENTIONAL_AXIS_CROSS` on an intentionally bad authored-shot variant.
8. Diagnostics return findings only; the authored-shot bytes/hash are unchanged.
9. Repeated execution is deterministic.

## Authority boundary

```text
Action Truth = upstream derived action authority for C1 input
Shot Intent = authored cinematographic interpretation request
Camera Truth = canonical physical camera solution for a shot
Operator Performance = derived performance layer
Frame Composition / View Presentation = downstream derived representation
Diagnostics = read-only findings
```

C1 does **not** authorize:
- production camera runtime integration;
- Babylon camera implementation;
- Grani or reality-disagreement presentation;
- camera writes into Action Truth, Motion Truth, Body DNA, or Space Truth;
- automatic shake from impact magnitude;
- silent diagnostic shot rewriting;
- coordinate-system lock;
- `hq/state` or protected-state mutation;
- OWNER LOCK;
- G2;
- Voice-to-Shot.

Anything produced by this branch is throwaway proof infrastructure and must not be treated as production implementation.
