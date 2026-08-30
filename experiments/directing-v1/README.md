# ZB Babylon Directing v1

Purpose: disposable directing/staging proof only.  
Not Character Truth.  
Not final animation.  
Not SALVADOR auto-submit.

## What this proves

`BABYLON DIRECTING v1` turns one strict structured scene document into a
repeatable Babylon.js blocking scene:

```text
SCENE DOCUMENT
→ STRICT VALIDATION
→ DISPOSABLE HUMANOID PROXIES
→ EXPLICIT CAMERA / SHOT
→ STATELESS EXACT-TIME EVALUATION
→ INSPECTABLE SNAPSHOT
→ REAL PNG CAPTURE
```

The proof scene contains two stable proxy ids (`A`, `B`), different blocking
heights and poses, authored root motion, one explicit camera, one shot, and one
capture time. It deliberately does not depend on the production body compiler,
a production rig, NLP, physics, textures, paid services, remote inference,
ComfyUI, or the SALVADOR runtime.

## Coordinate and timing contract

- Babylon's default left-handed world is used.
- Unit is meters.
- `+Y` is up.
- Actor root positions are world-space.
- Child joints accept local Euler rotations in degrees only.
- Camera FOV is vertical degrees.
- Timeline time is seconds and must be finite and non-negative.
- Every seek resets runtime state from the parsed source document before
  evaluating keyframes. Prior seek order cannot affect a requested timestamp.
- Translation/FOV use linear interpolation.
- Rotation uses deterministic shortest-path degree interpolation per axis.
- Snapshot values are evidence-rounded to six decimals; runtime transforms are
  not rounded.

## Pinned open-source stack

- Babylon.js `@babylonjs/core@9.22.2`
- TypeScript `7.0.2`
- Vite `8.2.2`
- Vitest `4.1.10`
- Playwright `1.62.1`

## Reproducible npm install

The pinned Vitest dependency graph includes optional peers that trigger an
`npm@10.9.x` Arborist traversal defect on the verification runner. The checked-in
`.npmrc` sets only `legacy-peer-deps=true`; direct dependency versions remain
fully pinned and `npm ci` remains lockfile-driven.

## Commands

```bash
cd experiments/directing-v1
npm ci
npm test
npm run typecheck
npm run build
npx playwright install chromium
npm run test:browser
npm run dev
```

The browser smoke starts a built Vite preview, performs arbitrary seek/replay,
repeats the target-time state after a fresh page reload, captures a Babylon
render target, verifies the PNG signature and exact `768 × 512` dimensions,
and writes:

```text
artifacts/proof-frame.png
```

The generated PNG is evidence only and is intentionally ignored by Git.

## Scene contract

Checked-in fixture:

```text
public/proof-scene.json
```

The parser fails closed on unsupported schema/proxy/joint values, malformed or
non-finite numbers, duplicate ids, invalid references, invalid camera optics,
capture time outside its shot, and non-increasing keyframe times. It constructs
a fresh typed object and does not silently correct semantic data.

## Browser proof bridge

After successful boot the page exposes only:

```ts
window.__zbDirecting.seek(timeSec)
window.__zbDirecting.snapshot()
window.__zbDirecting.capture()
```

- `seek` returns the evaluated state at an explicit time.
- `snapshot` re-evaluates the last requested time.
- `capture` evaluates the checked-in capture time and returns a PNG data URL.

The bridge does not parse directing prose, submit work, mutate canon, write to
Character Truth, or change SALVADOR settings.

## Authority boundary

This subsystem produces a disposable visual reference and reproducibility
metadata. Its proxy dimensions, joint rotations, camera values, and PNG are not
character canon and do not authorize production integration. Implementation
verification is not independent DUNCAN QC and does not authorize merge.
