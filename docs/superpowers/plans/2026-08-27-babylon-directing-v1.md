# BABYLON DIRECTING v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a small deterministic Babylon.js directing proof that loads structured scene data, creates two disposable humanoid proxies, evaluates explicit blocking/camera motion at exact timestamps, exposes inspectable state, and captures a reproducible still frame for later SALVADOR reference handoff.

**Architecture:** Keep the subsystem isolated under `experiments/directing-v1/`. A pure TypeScript scene contract/validator feeds a Babylon compiler. Time evaluation is explicit and stateless-from-source so scrubbing order cannot change results. Browser rendering/capture is a thin adapter over the same compiler/evaluator used by headless tests.

**Tech Stack:** Babylon.js `@babylonjs/core@9.22.2`, TypeScript `7.0.2`, Vite `8.2.2`, Vitest `4.1.10`, Playwright `@playwright/test@1.62.1`, Node.js `20.19+` or `22.12+`.

**Spec:** `docs/superpowers/specs/2026-08-27-babylon-directing-v1-design.md`

## Global Constraints

- Scope is proxy blocking + explicit camera + simple deterministic motion + deterministic frame capture only.
- Babylon must consume a structured scene document; it must not parse LYNCH prose in v1.
- No NLP, textures, production-body dependency, production rig dependency, audio/music, physics-driven combat, paid services, remote inference, SALVADOR auto-submit, or canon writeback.
- Proxy measurements are disposable directing parameters and never Character Truth.
- Camera does not auto-follow actors. Every camera transform is explicit.
- No automatic camera shake or hidden auto-framing.
- Joint child translation is forbidden in v1; child joints use local rotation only.
- Capture output is reference evidence only and does not alter SALVADOR's locked runtime profile.
- State determinism is the primary invariant; pixel-perfect GPU equality is not required.
- Implementation begins from exact approved spec head `8b60cd545b95981c9ef3ef5244100806fe2a334e` on a fresh implementation branch/worktree.
- No merge and no production integration are authorized by this plan.

---

## Planned File Structure

```text
experiments/directing-v1/
  package.json
  package-lock.json
  tsconfig.json
  vite.config.ts
  playwright.config.ts
  index.html
  public/
    proof-scene.json
  src/
    contract.ts          # versioned data types + parser/validation
    interpolation.ts     # deterministic scalar/vector/angle interpolation
    proxy.ts             # disposable humanoid proxy construction
    compiler.ts          # scene document -> Babylon runtime objects
    timeline.ts          # exact-time root/joint/camera evaluation
    snapshot.ts          # inspectable evaluated-state evidence
    capture.ts           # exact-time still capture adapter
    main.ts              # tiny browser proof harness
  tests/
    contract.test.ts
    compiler.test.ts
    timeline.test.ts
    determinism.test.ts
    capture.spec.ts
  artifacts/
    .gitkeep
  README.md
```

`experiments/directing-v1/` is intentionally independent of the existing experimental body-compiler branch and of `agent-controller/`.

---

### Task 1: Isolated project + scene contract validation

**Files:**
- Create: `experiments/directing-v1/package.json`
- Create: `experiments/directing-v1/package-lock.json`
- Create: `experiments/directing-v1/tsconfig.json`
- Create: `experiments/directing-v1/vite.config.ts`
- Create: `experiments/directing-v1/src/contract.ts`
- Create: `experiments/directing-v1/tests/contract.test.ts`

**Interfaces:**
- Produces: `SceneDocument`, `ActorSpec`, `CameraSpec`, `ShotSpec`, `CaptureSpec`, `JointName`, `SceneContractError`, `parseSceneDocument(input: unknown): SceneDocument`.
- Consumes: nothing from later tasks.

- [ ] **Step 1: Create the pinned project manifest**

Create `package.json` exactly with an ESM-only, no-framework proof:

```json
{
  "name": "zb-babylon-directing-v1",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite --host 127.0.0.1",
    "typecheck": "tsc --noEmit",
    "test": "vitest run",
    "test:watch": "vitest",
    "build": "npm run typecheck && vite build",
    "test:browser": "playwright test"
  },
  "dependencies": {
    "@babylonjs/core": "9.22.2"
  },
  "devDependencies": {
    "@playwright/test": "1.62.1",
    "typescript": "7.0.2",
    "vite": "8.2.2",
    "vitest": "4.1.10"
  }
}
```

Run:

```bash
cd experiments/directing-v1
node --version
npm install
```

Expected: Node satisfies `20.19+` or `22.12+`; `package-lock.json` is created with exact resolved versions.

- [ ] **Step 2: Add strict TypeScript/Vitest config**

Create `tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "useDefineForClassFields": true,
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "esModuleInterop": true,
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "types": ["vitest/globals"]
  },
  "include": ["src", "tests", "vite.config.ts", "playwright.config.ts"]
}
```

Create `vite.config.ts`:

```ts
import { defineConfig } from 'vite';

export default defineConfig({
  test: {
    environment: 'node',
    include: ['tests/**/*.test.ts'],
  },
});
```

- [ ] **Step 3: Write failing contract tests**

Create `tests/contract.test.ts` with at least these concrete cases:

```ts
import { describe, expect, it } from 'vitest';
import { parseSceneDocument, SceneContractError } from '../src/contract';

const valid = {
  schemaVersion: 'babylon-directing-v1',
  sceneId: 'scene-001',
  stage: { width: 12, depth: 8, groundY: 0, unit: 'm' },
  actors: [{
    id: 'A',
    proxyType: 'humanoid-basic',
    heightM: 1.8,
    position: { x: -1.2, y: 0, z: 0 },
    rotationYDeg: 25,
    pose: { head: { x: 0, y: 10, z: 0 } },
  }],
  cameras: [{
    id: 'cam-main',
    position: { x: 0, y: 2.1, z: -6.5 },
    target: { x: 0, y: 1, z: 0.2 },
    fovDeg: 42,
  }],
  shots: [{ id: 'shot-main', cameraId: 'cam-main', startSec: 0, endSec: 2 }],
  capture: { shotId: 'shot-main', timeSec: 1.5, widthPx: 768, heightPx: 512, output: 'proof-frame.png' },
};

describe('parseSceneDocument', () => {
  it('accepts the v1 contract', () => {
    expect(parseSceneDocument(valid).sceneId).toBe('scene-001');
  });

  it('rejects unsupported schema versions', () => {
    expect(() => parseSceneDocument({ ...valid, schemaVersion: 'v2' }))
      .toThrowError(SceneContractError);
  });

  it('rejects duplicate actor ids', () => {
    expect(() => parseSceneDocument({ ...valid, actors: [valid.actors[0], valid.actors[0]] }))
      .toThrow(/DUPLICATE_ACTOR_ID/);
  });

  it('rejects unknown joints', () => {
    const actor = { ...valid.actors[0], pose: { tail: { x: 0, y: 0, z: 0 } } };
    expect(() => parseSceneDocument({ ...valid, actors: [actor] }))
      .toThrow(/UNSUPPORTED_JOINT/);
  });

  it('rejects missing camera references', () => {
    const shots = [{ ...valid.shots[0], cameraId: 'missing' }];
    expect(() => parseSceneDocument({ ...valid, shots }))
      .toThrow(/UNKNOWN_CAMERA_REFERENCE/);
  });

  it('rejects non-finite numeric values', () => {
    const actor = { ...valid.actors[0], heightM: Number.NaN };
    expect(() => parseSceneDocument({ ...valid, actors: [actor] }))
      .toThrow(/INVALID_NUMBER/);
  });
});
```

- [ ] **Step 4: Run RED**

Run:

```bash
npm test -- tests/contract.test.ts
```

Expected: FAIL because `src/contract.ts` does not exist.

- [ ] **Step 5: Implement the strict contract**

Create `src/contract.ts` with these exported types and rules:

```ts
export const JOINT_NAMES = [
  'pelvis', 'spine', 'chest', 'neck', 'head',
  'shoulderL', 'shoulderR', 'upperArmL', 'upperArmR',
  'forearmL', 'forearmR', 'handL', 'handR',
  'thighL', 'thighR', 'shinL', 'shinR', 'footL', 'footR',
] as const;

export type JointName = typeof JOINT_NAMES[number];
export type Vec3 = { x: number; y: number; z: number };
export type EulerDeg = Vec3;
export type RootKeyframe = { timeSec: number; position: Vec3; rotationYDeg: number };
export type JointKeyframe = { timeSec: number; joint: JointName; localRotationDeg: EulerDeg };
export type CameraKeyframe = { timeSec: number; position: Vec3; target: Vec3; fovDeg: number };

export type ActorSpec = {
  id: string;
  proxyType: 'humanoid-basic';
  heightM: number;
  position: Vec3;
  rotationYDeg: number;
  pose: Partial<Record<JointName, EulerDeg>>;
  rootMotion?: RootKeyframe[];
  jointMotion?: JointKeyframe[];
  label?: string;
};

export type CameraSpec = {
  id: string;
  position: Vec3;
  target: Vec3;
  fovDeg: number;
  nearClip?: number;
  farClip?: number;
  motion?: CameraKeyframe[];
};

export type ShotSpec = {
  id: string;
  cameraId: string;
  startSec: number;
  endSec: number;
  label?: string;
  preferredCaptureSec?: number;
};

export type CaptureSpec = {
  shotId?: string;
  cameraId?: string;
  timeSec: number;
  widthPx: number;
  heightPx: number;
  output: string;
};

export type SceneDocument = {
  schemaVersion: 'babylon-directing-v1';
  sceneId: string;
  stage: { width: number; depth: number; groundY: number; unit: 'm' };
  actors: ActorSpec[];
  cameras: CameraSpec[];
  shots: ShotSpec[];
  capture: CaptureSpec;
};

export class SceneContractError extends Error {
  constructor(public readonly code: string, public readonly path: string, message: string) {
    super(`${code} at ${path}: ${message}`);
    this.name = 'SceneContractError';
  }
}
```

`parseSceneDocument(input)` must validate before returning a typed copy. Required hard failures: unsupported schema, duplicate actor/camera/shot ids, empty ids, unsupported proxy type, non-finite numbers, non-positive stage/height/FOV/capture dimensions, malformed vectors, unknown joints, camera references that do not exist, capture references that do not exist, negative shot duration, and keyframes whose `timeSec` values decrease within the same channel. It must not silently change semantic values.

- [ ] **Step 6: Run GREEN + typecheck**

```bash
npm test -- tests/contract.test.ts
npm run typecheck
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add experiments/directing-v1
git commit -m "feat: define Babylon directing v1 scene contract"
```

---

### Task 2: Disposable proxy + Babylon scene compiler

**Files:**
- Create: `experiments/directing-v1/src/proxy.ts`
- Create: `experiments/directing-v1/src/compiler.ts`
- Create: `experiments/directing-v1/tests/compiler.test.ts`

**Interfaces:**
- Consumes: `SceneDocument`, `ActorSpec`, `JointName` from `contract.ts`.
- Produces: `CompiledActor`, `CompiledDirectingScene`, `createHumanoidProxy(scene, actor)`, `compileDirectingScene(engine, document)`.

- [ ] **Step 1: Write failing compiler tests using Babylon NullEngine**

Create `tests/compiler.test.ts`:

```ts
import { NullEngine } from '@babylonjs/core/Engines/nullEngine';
import { describe, expect, it } from 'vitest';
import { compileDirectingScene } from '../src/compiler';
import { parseSceneDocument } from '../src/contract';

const document = parseSceneDocument({
  schemaVersion: 'babylon-directing-v1',
  sceneId: 'compiler-proof',
  stage: { width: 10, depth: 8, groundY: 0, unit: 'm' },
  actors: [
    { id: 'A', proxyType: 'humanoid-basic', heightM: 1.8, position: { x: -1, y: 0, z: 0 }, rotationYDeg: 20, pose: { upperArmL: { x: 0, y: 0, z: -30 } } },
    { id: 'B', proxyType: 'humanoid-basic', heightM: 1.65, position: { x: 1.2, y: 0, z: 0.3 }, rotationYDeg: -150, pose: { upperArmR: { x: 0, y: 0, z: 35 } } },
  ],
  cameras: [{ id: 'cam', position: { x: 0, y: 2, z: -6 }, target: { x: 0, y: 1, z: 0 }, fovDeg: 42 }],
  shots: [{ id: 'shot', cameraId: 'cam', startSec: 0, endSec: 2 }],
  capture: { shotId: 'shot', timeSec: 1, widthPx: 768, heightPx: 512, output: 'proof.png' },
});

describe('compileDirectingScene', () => {
  it('creates stable actor and camera maps', () => {
    const engine = new NullEngine();
    const compiled = compileDirectingScene(engine, document);
    expect([...compiled.actors.keys()]).toEqual(['A', 'B']);
    expect([...compiled.cameras.keys()]).toEqual(['cam']);
    expect(compiled.actors.get('A')?.joints.has('upperArmL')).toBe(true);
    expect(compiled.scene.activeCamera?.name).toBe('camera:cam');
    engine.dispose();
  });

  it('applies source root transforms without mutating the document', () => {
    const before = JSON.stringify(document);
    const engine = new NullEngine();
    const compiled = compileDirectingScene(engine, document);
    const a = compiled.actors.get('A')!;
    expect(a.root.position.x).toBeCloseTo(-1);
    expect(JSON.stringify(document)).toBe(before);
    engine.dispose();
  });
});
```

- [ ] **Step 2: Run RED**

```bash
npm test -- tests/compiler.test.ts
```

Expected: FAIL because compiler/proxy modules do not exist.

- [ ] **Step 3: Implement a minimal named-joint proxy**

`src/proxy.ts` must create one `TransformNode` root per actor and one `TransformNode` for every supported joint. Meshes are primitive children only; they must never become authority data.

Use a fixed normalized hierarchy, scaled by `heightM`:

```text
root
└─ pelvis
   ├─ spine -> chest -> neck -> head
   │  ├─ shoulderL -> upperArmL -> forearmL -> handL
   │  └─ shoulderR -> upperArmR -> forearmR -> handR
   ├─ thighL -> shinL -> footL
   └─ thighR -> shinR -> footR
```

Export:

```ts
export type CompiledActor = {
  spec: ActorSpec;
  root: TransformNode;
  joints: Map<JointName, TransformNode>;
};

export function createHumanoidProxy(scene: Scene, actor: ActorSpec): CompiledActor;
```

Use `MeshBuilder.CreateCapsule`, `CreateBox`, or `CreateSphere` only. Give left/right limbs different debug material values only if needed for readability; no textures.

Initial local pose rotations are applied as radians:

```ts
joint.rotation.set(
  Tools.ToRadians(pose.x),
  Tools.ToRadians(pose.y),
  Tools.ToRadians(pose.z),
);
```

- [ ] **Step 4: Implement compiler**

`src/compiler.ts` exports:

```ts
export type CompiledDirectingScene = {
  engine: AbstractEngine;
  scene: Scene;
  document: SceneDocument;
  actors: Map<string, CompiledActor>;
  cameras: Map<string, FreeCamera>;
  shots: Map<string, ShotSpec>;
};

export function compileDirectingScene(
  engine: AbstractEngine,
  document: SceneDocument,
): CompiledDirectingScene;
```

Compiler behavior:

1. create `Scene` and ground at `groundY` with exact stage width/depth;
2. create actors in source array order and put them in a `Map` by stable id;
3. set actor root position and Y rotation from source;
4. create `FreeCamera` for every camera, set `fov = Tools.ToRadians(fovDeg)`, `minZ = nearClip ?? 0.05`, `maxZ = farClip ?? 1000`, and `setTarget(target)`;
5. set the first declared camera as `scene.activeCamera` only as a deterministic default; capture/shot selection overrides it explicitly later;
6. keep the exact parsed document immutable by convention; no writeback.

- [ ] **Step 5: Run GREEN**

```bash
npm test -- tests/compiler.test.ts
npm run typecheck
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add experiments/directing-v1/src/proxy.ts experiments/directing-v1/src/compiler.ts experiments/directing-v1/tests/compiler.test.ts
git commit -m "feat: compile directing scene proxies and cameras"
```

---

### Task 3: Deterministic timeline evaluation

**Files:**
- Create: `experiments/directing-v1/src/interpolation.ts`
- Create: `experiments/directing-v1/src/timeline.ts`
- Create: `experiments/directing-v1/tests/timeline.test.ts`

**Interfaces:**
- Consumes: `CompiledDirectingScene` and source motion keyframes.
- Produces: `lerpAngleDeg`, `evaluateAtTime(compiled, timeSec)`, `resolveCameraForTime(compiled, timeSec, requestedShotId?)`.

- [ ] **Step 1: Write failing interpolation/timeline tests**

```ts
import { NullEngine } from '@babylonjs/core/Engines/nullEngine';
import { describe, expect, it } from 'vitest';
import { compileDirectingScene } from '../src/compiler';
import { parseSceneDocument } from '../src/contract';
import { evaluateAtTime } from '../src/timeline';
import { lerpAngleDeg } from '../src/interpolation';

it('takes the shortest angle path', () => {
  expect(lerpAngleDeg(170, -170, 0.5)).toBeCloseTo(180);
});

it('seeking is independent of previous seek order', () => {
  const engine = new NullEngine();
  const doc = parseSceneDocument({
    schemaVersion: 'babylon-directing-v1',
    sceneId: 'timeline',
    stage: { width: 8, depth: 8, groundY: 0, unit: 'm' },
    actors: [{
      id: 'A', proxyType: 'humanoid-basic', heightM: 1.8,
      position: { x: 0, y: 0, z: 0 }, rotationYDeg: 0, pose: {},
      rootMotion: [
        { timeSec: 0, position: { x: 0, y: 0, z: 0 }, rotationYDeg: 0 },
        { timeSec: 2, position: { x: 2, y: 0, z: 0 }, rotationYDeg: 90 }
      ],
      jointMotion: [
        { timeSec: 0, joint: 'upperArmL', localRotationDeg: { x: 0, y: 0, z: 0 } },
        { timeSec: 2, joint: 'upperArmL', localRotationDeg: { x: 0, y: 0, z: -60 } }
      ]
    }],
    cameras: [{ id: 'cam', position: { x: 0, y: 2, z: -6 }, target: { x: 0, y: 1, z: 0 }, fovDeg: 40 }],
    shots: [{ id: 'shot', cameraId: 'cam', startSec: 0, endSec: 2 }],
    capture: { shotId: 'shot', timeSec: 1, widthPx: 768, heightPx: 512, output: 'proof.png' }
  });
  const compiled = compileDirectingScene(engine, doc);
  evaluateAtTime(compiled, 1.75);
  evaluateAtTime(compiled, 0.25);
  evaluateAtTime(compiled, 1);
  const a = compiled.actors.get('A')!;
  expect(a.root.position.x).toBeCloseTo(1);
  expect(a.root.rotation.y).toBeCloseTo(Math.PI / 4);
  expect(a.joints.get('upperArmL')!.rotation.z).toBeCloseTo(-Math.PI / 6);
  engine.dispose();
});
```

- [ ] **Step 2: Run RED**

```bash
npm test -- tests/timeline.test.ts
```

Expected: FAIL because timeline/interpolation modules do not exist.

- [ ] **Step 3: Implement deterministic interpolation**

`src/interpolation.ts`:

```ts
import type { Vec3 } from './contract';

export const clamp01 = (value: number) => Math.max(0, Math.min(1, value));
export const lerp = (a: number, b: number, t: number) => a + (b - a) * clamp01(t);

export function lerpAngleDeg(a: number, b: number, t: number): number {
  const delta = ((b - a + 540) % 360) - 180;
  return a + delta * clamp01(t);
}

export function lerpVec3(a: Vec3, b: Vec3, t: number): Vec3 {
  return { x: lerp(a.x, b.x, t), y: lerp(a.y, b.y, t), z: lerp(a.z, b.z, t) };
}
```

Add a helper that finds the bracketing keyframes at a requested time. Before the first keyframe use the first value; after the last use the last value. No accumulated deltas.

- [ ] **Step 4: Implement exact-time evaluator**

`evaluateAtTime(compiled, timeSec)` must re-derive state from source every call:

1. reset each actor root to source initial position/facing and each joint to source initial pose;
2. apply root motion interpolation at `timeSec` if defined;
3. group joint motion by joint id, evaluate each channel independently, and apply local Euler rotations using shortest-path per axis;
4. reset each camera to source initial state, then apply camera motion interpolation if defined;
5. select active camera by shot interval using source shot order as deterministic precedence when intervals overlap;
6. return the active camera id and active shot id without storing timeline history.

Export:

```ts
export type EvaluationSelection = { activeCameraId: string | null; activeShotId: string | null };
export function evaluateAtTime(compiled: CompiledDirectingScene, timeSec: number): EvaluationSelection;
```

- [ ] **Step 5: Run GREEN**

```bash
npm test -- tests/timeline.test.ts
npm test
npm run typecheck
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add experiments/directing-v1/src/interpolation.ts experiments/directing-v1/src/timeline.ts experiments/directing-v1/tests/timeline.test.ts
git commit -m "feat: add deterministic directing timeline"
```

---

### Task 4: Inspectable snapshot + determinism regression

**Files:**
- Create: `experiments/directing-v1/src/snapshot.ts`
- Create: `experiments/directing-v1/tests/determinism.test.ts`

**Interfaces:**
- Consumes: evaluated `CompiledDirectingScene`.
- Produces: `EvaluatedSnapshot`, `createEvaluatedSnapshot(compiled, timeSec)`.

- [ ] **Step 1: Write failing snapshot determinism test**

The test must compile the same parsed fixture twice into two independent `NullEngine` instances, seek both to exactly `1.25`, serialize snapshots, and expect byte-for-byte equality after `JSON.stringify`.

```ts
const a = createEvaluatedSnapshot(compiledA, 1.25);
const b = createEvaluatedSnapshot(compiledB, 1.25);
expect(JSON.stringify(a)).toBe(JSON.stringify(b));
```

Also assert the snapshot contains actor ids, root transforms, every named joint rotation, active camera position/target/FOV, active shot, capture settings, schema version, scene id, and evaluated time.

- [ ] **Step 2: Run RED**

```bash
npm test -- tests/determinism.test.ts
```

Expected: FAIL because snapshot module does not exist.

- [ ] **Step 3: Implement snapshot serialization**

Export this stable shape:

```ts
export type EvaluatedSnapshot = {
  sceneId: string;
  schemaVersion: 'babylon-directing-v1';
  timeSec: number;
  actors: Array<{
    id: string;
    position: { x: number; y: number; z: number };
    rotationYDeg: number;
    joints: Array<{ joint: JointName; localRotationDeg: { x: number; y: number; z: number } }>;
  }>;
  activeCamera: null | {
    id: string;
    position: { x: number; y: number; z: number };
    target: { x: number; y: number; z: number };
    fovDeg: number;
  };
  activeShotId: string | null;
  capture: CaptureSpec;
  runtime: { babylonVersion: string };
};
```

Before reading transforms, call `evaluateAtTime(compiled, timeSec)`. Serialize actors in document order and joints in `JOINT_NAMES` order. Round only for evidence serialization with one explicit helper `roundEvidence(value) = Number(value.toFixed(6))`; do not round runtime transforms.

- [ ] **Step 4: Run GREEN**

```bash
npm test -- tests/determinism.test.ts
npm test
npm run typecheck
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add experiments/directing-v1/src/snapshot.ts experiments/directing-v1/tests/determinism.test.ts
git commit -m "feat: expose deterministic directing snapshots"
```

---

### Task 5: Proof fixture + browser harness + exact-time capture adapter

**Files:**
- Create: `experiments/directing-v1/public/proof-scene.json`
- Create: `experiments/directing-v1/index.html`
- Create: `experiments/directing-v1/src/capture.ts`
- Create: `experiments/directing-v1/src/main.ts`
- Create: `experiments/directing-v1/artifacts/.gitkeep`

**Interfaces:**
- Consumes: contract parser/compiler/timeline/snapshot.
- Produces: `captureStill(compiled, capture): Promise<string>` and browser test bridge `window.__zbDirecting`.

- [ ] **Step 1: Add the exact checked-in proof scene**

`public/proof-scene.json` must contain two actors and one authored movement:

```json
{
  "schemaVersion": "babylon-directing-v1",
  "sceneId": "ZB-BABYLON-DIRECTING-PROOF-001",
  "stage": { "width": 12, "depth": 8, "groundY": 0, "unit": "m" },
  "actors": [
    {
      "id": "A",
      "proxyType": "humanoid-basic",
      "heightM": 1.8,
      "position": { "x": -1.4, "y": 0, "z": 0 },
      "rotationYDeg": 25,
      "pose": {
        "head": { "x": 0, "y": 8, "z": 0 },
        "upperArmL": { "x": 0, "y": 0, "z": -22 },
        "forearmL": { "x": 0, "y": 0, "z": -18 }
      },
      "rootMotion": [
        { "timeSec": 0, "position": { "x": -1.4, "y": 0, "z": 0 }, "rotationYDeg": 25 },
        { "timeSec": 1.5, "position": { "x": -0.7, "y": 0, "z": 0.2 }, "rotationYDeg": 45 }
      ]
    },
    {
      "id": "B",
      "proxyType": "humanoid-basic",
      "heightM": 1.65,
      "position": { "x": 1.4, "y": 0, "z": 0.45 },
      "rotationYDeg": -145,
      "pose": {
        "head": { "x": 0, "y": -6, "z": 0 },
        "upperArmR": { "x": 0, "y": 0, "z": 34 },
        "forearmR": { "x": 0, "y": 0, "z": 20 }
      }
    }
  ],
  "cameras": [
    {
      "id": "cam-main",
      "position": { "x": 0, "y": 2.15, "z": -6.5 },
      "target": { "x": 0, "y": 1.0, "z": 0.2 },
      "fovDeg": 42,
      "nearClip": 0.05,
      "farClip": 100
    }
  ],
  "shots": [
    { "id": "shot-main", "cameraId": "cam-main", "startSec": 0, "endSec": 2, "preferredCaptureSec": 1.5 }
  ],
  "capture": {
    "shotId": "shot-main",
    "timeSec": 1.5,
    "widthPx": 768,
    "heightPx": 512,
    "output": "proof-frame.png"
  }
}
```

- [ ] **Step 2: Implement capture adapter**

Use Babylon's render-target screenshot API, not DOM screenshots:

```ts
import { CreateScreenshotUsingRenderTargetAsync } from '@babylonjs/core/Misc/screenshotTools';
import type { CaptureSpec } from './contract';
import type { CompiledDirectingScene } from './compiler';
import { evaluateAtTime } from './timeline';

export async function captureStill(
  compiled: CompiledDirectingScene,
  capture: CaptureSpec,
): Promise<string> {
  const selection = evaluateAtTime(compiled, capture.timeSec);
  const cameraId = capture.cameraId ?? selection.activeCameraId;
  if (!cameraId) throw new Error('CAPTURE_CAMERA_UNRESOLVED');
  const camera = compiled.cameras.get(cameraId);
  if (!camera) throw new Error(`CAPTURE_CAMERA_NOT_FOUND: ${cameraId}`);
  compiled.scene.activeCamera = camera;
  compiled.scene.render();
  return CreateScreenshotUsingRenderTargetAsync(
    compiled.engine,
    camera,
    { width: capture.widthPx, height: capture.heightPx },
    'image/png',
    1,
    false,
  );
}
```

If `capture.shotId` is present, resolve that shot's camera explicitly before falling back to active selection; do not silently choose another camera.

- [ ] **Step 3: Add minimal browser harness**

`index.html` contains only a full-window canvas and module script:

```html
<!doctype html>
<html>
<head><meta charset="UTF-8"><title>ZB Babylon Directing v1</title></head>
<body style="margin:0;overflow:hidden">
  <canvas id="renderCanvas" style="width:100vw;height:100vh;display:block"></canvas>
  <script type="module" src="/src/main.ts"></script>
</body>
</html>
```

`main.ts` must:

1. create Babylon `Engine` on `#renderCanvas`;
2. `fetch('/proof-scene.json')`;
3. parse with `parseSceneDocument`;
4. compile with `compileDirectingScene`;
5. evaluate at capture time;
6. start render loop without mutating authored state;
7. expose this narrow proof bridge:

```ts
declare global {
  interface Window {
    __zbDirecting: {
      seek(timeSec: number): ReturnType<typeof createEvaluatedSnapshot>;
      snapshot(): ReturnType<typeof createEvaluatedSnapshot>;
      capture(): Promise<string>;
    };
  }
}
```

`seek(timeSec)` calls `createEvaluatedSnapshot(compiled, timeSec)`. `snapshot()` reads the last explicitly sought time. `capture()` captures the document's exact `capture` settings.

- [ ] **Step 4: Verify local browser build before Playwright**

```bash
npm run build
```

Expected: PASS with no type errors.

- [ ] **Step 5: Commit**

```bash
git add experiments/directing-v1/public experiments/directing-v1/index.html experiments/directing-v1/src/capture.ts experiments/directing-v1/src/main.ts experiments/directing-v1/artifacts/.gitkeep
git commit -m "feat: add Babylon directing proof scene and capture"
```

---

### Task 6: Real browser smoke + reproducible frame evidence

**Files:**
- Create: `experiments/directing-v1/playwright.config.ts`
- Create: `experiments/directing-v1/tests/capture.spec.ts`

**Interfaces:**
- Consumes: browser bridge from Task 5.
- Produces: live Chromium smoke evidence and `artifacts/proof-frame.png` during test execution.

- [ ] **Step 1: Configure Playwright against local Vite**

Create `playwright.config.ts`:

```ts
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  testMatch: '**/*.spec.ts',
  workers: 1,
  use: {
    baseURL: 'http://127.0.0.1:4173',
    viewport: { width: 1024, height: 768 },
  },
  webServer: {
    command: 'npm run build && npx vite preview --host 127.0.0.1 --port 4173',
    url: 'http://127.0.0.1:4173',
    reuseExistingServer: false,
  },
});
```

- [ ] **Step 2: Write failing browser smoke**

Create `tests/capture.spec.ts`:

```ts
import { expect, test } from '@playwright/test';
import { mkdir, writeFile } from 'node:fs/promises';

const decodePng = (dataUrl: string) => Buffer.from(dataUrl.split(',', 2)[1]!, 'base64');

test('proof scene scrubs deterministically and captures a real PNG', async ({ page }) => {
  await page.goto('/');
  await page.waitForFunction(() => Boolean(window.__zbDirecting));

  const first = await page.evaluate(() => window.__zbDirecting.seek(1.5));
  await page.evaluate(() => window.__zbDirecting.seek(0.25));
  const second = await page.evaluate(() => window.__zbDirecting.seek(1.5));
  expect(second).toEqual(first);

  const dataUrl = await page.evaluate(() => window.__zbDirecting.capture());
  expect(dataUrl.startsWith('data:image/png;base64,')).toBe(true);

  const bytes = decodePng(dataUrl);
  expect(bytes.byteLength).toBeGreaterThan(1000);
  await mkdir('artifacts', { recursive: true });
  await writeFile('artifacts/proof-frame.png', bytes);
});
```

Add TypeScript global declaration in `main.ts` so Playwright compile sees `window.__zbDirecting`.

- [ ] **Step 3: Run RED if the browser dependency is not installed**

```bash
npx playwright install chromium
npm run test:browser
```

The first run may expose browser-only Babylon mistakes; treat each as a normal TDD failure. Do not weaken the assertions.

- [ ] **Step 4: Make the smallest browser fixes required**

Allowed fixes are limited to browser bootstrap, Babylon imports, render/capture timing, and explicit camera resolution. Do not add UI frameworks, automatic camera behavior, textures, physics, or integration code.

- [ ] **Step 5: Run GREEN twice from fresh server launches**

```bash
npm run test:browser
npm run test:browser
```

Expected both times:

```text
1 passed
```

`artifacts/proof-frame.png` exists and the 1.5-second snapshot is identical before/after an intervening seek.

- [ ] **Step 6: Commit**

```bash
git add experiments/directing-v1/playwright.config.ts experiments/directing-v1/tests/capture.spec.ts
git commit -m "test: prove Babylon directing browser capture"
```

Do not commit the generated `artifacts/proof-frame.png`; only `.gitkeep` is tracked.

---

### Task 7: Operator documentation + final implementation verification handoff

**Files:**
- Create: `experiments/directing-v1/README.md`
- Modify: `experiments/directing-v1/.gitignore` if generated artifacts need explicit ignore; otherwise create it.

**Interfaces:**
- Consumes: all Tasks 1-6.
- Produces: exact local run instructions and complete evidence package for DUNCAN.

- [ ] **Step 1: Add local README**

README must state exactly:

```text
Purpose: disposable directing/staging proof only.
Not Character Truth.
Not final animation.
Not SALVADOR auto-submit.
```

Document only these operator commands:

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

Document fixture path `public/proof-scene.json`, output evidence path `artifacts/proof-frame.png`, and browser proof bridge methods `seek`, `snapshot`, `capture`.

- [ ] **Step 2: Ignore generated evidence**

Create `.gitignore`:

```gitignore
node_modules/
dist/
playwright-report/
test-results/
artifacts/*.png
```

Keep `artifacts/.gitkeep` tracked.

- [ ] **Step 3: Run full verification from clean install**

```bash
rm -rf node_modules dist playwright-report test-results
npm ci
npm test
npm run typecheck
npm run build
npx playwright install chromium
npm run test:browser
```

On Windows PowerShell use equivalent `Remove-Item -Recurse -Force` commands rather than changing the verification content.

Expected:

- contract/compiler/timeline/determinism Vitest suite PASS;
- typecheck PASS;
- Vite build PASS;
- Chromium browser smoke PASS;
- real `artifacts/proof-frame.png` created;
- no SALVADOR task created;
- no production/canon mutation.

- [ ] **Step 4: Inspect scope before claiming completion**

```bash
git status --short
git diff --stat 8b60cd545b95981c9ef3ef5244100806fe2a334e...HEAD
git diff --name-only 8b60cd545b95981c9ef3ef5244100806fe2a334e...HEAD
```

Expected changed scope is only:

```text
experiments/directing-v1/**
```

plus this approved plan/spec history already present on the docs lineage. No `agent-controller/`, SALVADOR runtime, canon files, or unrelated architecture files may change.

- [ ] **Step 5: Commit docs**

```bash
git add experiments/directing-v1/README.md experiments/directing-v1/.gitignore
git commit -m "docs: document Babylon directing v1 proof"
```

- [ ] **Step 6: Post LESTER implementation handoff to #69**

The durable handoff must contain real values, not placeholders:

```text
LESTER_BABYLON_DIRECTING_V1_IMPLEMENTATION_READY
SPEC_HEAD = 8b60cd545b95981c9ef3ef5244100806fe2a334e
PLAN_HEAD = <exact plan commit>
EXACT_IMPLEMENTATION_HEAD = <exact implementation commit>
IMPLEMENTATION_BRANCH = <branch>
NODE = <version>
BABYLON = 9.22.2
VITEST = 4.1.10
PLAYWRIGHT = 1.62.1
UNIT_TESTS = <actual passed count / exit 0>
TYPECHECK = PASS
BUILD = PASS
BROWSER_SMOKE = PASS
PROOF_SCENE = ZB-BABYLON-DIRECTING-PROOF-001
CAPTURE = artifacts/proof-frame.png
CAPTURE_SHA256 = <actual sha256>
SCRUB_REPLAY_DETERMINISM = PASS
NLP = NOT ADDED
TEXTURES = NOT ADDED
PRODUCTION_BODY_DEPENDENCY = NOT ADDED
SALVADOR_AUTO_SUBMIT = NOT ADDED
CANON_WRITEBACK = NO
PRODUCTION_INTEGRATION = NO
MERGE = NO
NEXT = DUNCAN independent QC exact implementation HEAD
```

No DUNCAN PASS may be predeclared.

---

## DUNCAN QC Expectations After Implementation

DUNCAN should independently reconstruct/check exact implementation HEAD and verify at minimum:

1. scene validation rejects malformed/unsupported data and missing references;
2. same structured scene yields the same evaluated snapshots at fixed timestamps;
3. arbitrary seek order does not change the result at a target timestamp;
4. proxy actor ids, transforms, pose joints, and camera values are inspectable;
5. one real Chromium run creates a non-empty PNG at the explicit capture time;
6. the proof remains isolated from SALVADOR production runtime and Character Truth;
7. no NLP, textures, physics, body compiler dependency, audio/music, paid service, or hidden integration entered scope;
8. implementation changed only the planned proof subsystem;
9. no merge and no production integration occurred.

DUNCAN verdict is `PASS` or `CHANGES_REQUIRED`. A PASS only authorizes the next disposable/live directing review gate; it does not authorize production integration.

---

## Plan Self-Review

- Spec coverage: PASS — scene contract, proxies, cameras, simple motion, exact-time evaluation, inspectable snapshot, deterministic capture, browser smoke, SALVADOR/LYNCH boundaries, QC and authority gates are each mapped to tasks.
- Placeholder scan: PASS — implementation steps define concrete paths, signatures, commands, fixtures, assertions, and handoff fields. Angle-bracket fields appear only in the future handoff template and explicitly require real runtime substitution before posting.
- Type consistency: PASS — contract types feed compiler; compiler feeds timeline; timeline feeds snapshot/capture; browser bridge exposes snapshot/capture; Playwright consumes the bridge.
- Scope: PASS — one isolated subsystem under `experiments/directing-v1/`; no production integration.
