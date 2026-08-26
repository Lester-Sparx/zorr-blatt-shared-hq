# M0 — Motion Truth / Action Truth Probe

Status: **SPIKE / EXPERIMENT ONLY / NOT PRODUCTION**

ZB base: `9da550e842c7b2e22418b38d299e83b38e264122`

## Question

Can ZB represent action as time-dependent mechanics rather than a pose snapshot, while keeping Motion DNA strictly separate from Body DNA?

## Architecture laws under test

```text
BODY TRUTH + SPACE TRUTH + MOTION TRUTH = ACTION TRUTH
POSE IS NOT MOTION.
MOTION IS THE TRANSFER OF MASS, SUPPORT AND MOMENTUM THROUGH TIME.
ACTION IS NOT AN ANIMATION CLIP.
MOTION DNA MUST NOT MUTATE BODY DNA.
```

Canonical action phases used by this probe:

```text
PREPARE → LOAD → LAUNCH → AIR_TRANSFER → CONTACT → RECOVERY
```

Landing mechanics are checked as an ordered mechanical response:

```text
FIRST_CONTACT
→ LOAD_ACCEPTANCE
→ COM_DECELERATION
→ JOINT_COMPRESSION
→ TORSO_RESPONSE
→ SECONDARY_CONTACT
→ FOOT_SETTLE
→ STABILIZATION
```

## Probe design

The runner uses a fully synthetic, anonymous actor. It contains no ZORR BLATT character measurements, rig, animation clip, production plate, camera data, or production motion data.

It proves four things:

1. A deterministic action trace has ordered phases, monotonic time, explicit COM state, support contacts, linear momentum, angular momentum, and landing response.
2. Two traces can have the **same pose snapshot at the same control time** yet different support/history/momentum; a pose-only hash must be identical while Motion Truth and Action Truth hashes must differ.
3. Body DNA is hashed before and after Motion DNA evaluation; the bytes/hashes must remain identical.
4. Action Truth is derived from Body Truth + Space Truth + Motion Truth. No animation clip, camera, renderer, or Babylon runtime is required to establish the mechanical truth contract.

## Acceptance

M0 may report `PROCEED` only when all checks pass:

- phase order is exact;
- time is strictly monotonic;
- every sample has finite COM position/velocity and explicit support state;
- momentum is derived from body mass + velocity, not copied from pose;
- landing sub-events are ordered and impact velocity is mechanically absorbed before stabilization;
- the pose counterexample has identical pose hashes but different Motion Truth hashes and different Action Truth hashes;
- Body DNA canonical bytes and SHA-256 are unchanged after all Motion DNA evaluation;
- report is deterministic across two executions in the same runner.

## Authority boundary

```text
BODY DNA = body authority
MOTION DNA = separate motion traits/input
MOTION TRUTH = derived time-dependent mechanics
ACTION TRUTH = derived body + space + motion contract
ANIMATION CLIP = one possible downstream realization only
```

M0 does **not** authorize:

- Motion DNA writing to Body DNA;
- a pose snapshot being treated as motion truth;
- animation clips becoming Action Truth authority;
- production animation/runtime integration;
- camera/cinematography implementation (C1 is separate);
- `hq/state`, task/review/lock/dashboard mutations;
- OWNER LOCK;
- G2;
- Voice-to-Shot.

Anything created by this branch is throwaway feasibility evidence unless a later, separately approved transition promotes a design.
