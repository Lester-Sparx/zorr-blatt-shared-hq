# BABYLON DIRECTING v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a small deterministic Babylon.js directing proof that loads structured scene data, creates two disposable humanoid proxies, evaluates explicit blocking/camera motion at exact timestamps, exposes inspectable state, and captures a real still frame for later SALVADOR reference handoff.

**Architecture:** Keep the subsystem isolated under `experiments/directing-v1/`. A strict TypeScript scene contract feeds a Babylon compiler. Timeline evaluation is recomputed from authored source data on every seek, so scrub order cannot change results. Browser rendering/capture is a thin adapter over the same compiler/evaluator tested headlessly with Babylon `NullEngine`.

**Tech Stack:** Babylon.js `@babylonjs/core@9.22.2`, TypeScript `7.0.2`, Vite `8.2.2`, Vitest `4.1.10`, Playwright `@playwright/test@1.62.1`, `@types/node@26.2.0`, Node.js `20.19+` or `22.12+`.

**Spec:** `docs/superpowers/specs/2026-08-27-babylon-directing-v1-design.md`

## Global Constraints

- Scope is proxy blocking + explicit camera + simple deterministic motion + deterministic frame capture only.
- Babylon consumes a structured scene document; it does not parse LYNCH prose in v1.
- No NLP, textures, production-body dependency, production rig dependency, audio/music, physics-driven combat, paid services, remote inference, SALVADOR auto-submit, or canon writeback.
- Proxy measurements are disposable directing parameters and never Character Truth.
- Camera does not auto-follow actors. Every camera transform is explicit.
- No automatic camera shake or hidden auto-framing.
- Child joints use local rotation only; joint translation is forbidden in v1.
- Capture output is reference evidence only and cannot alter SALVADOR's locked runtime profile.
- State determinism is the primary invariant; pixel-perfect GPU equality is not required.
- Implementation starts from the exact plan HEAD recorded in the future implementation-authorization issue, itself descended from approved spec head `8b60cd545b95981c9ef3ef5244100806fe2a334e`.
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
  .gitignore
  public/proof-scene.json
  src/contract.ts
  src/interpolation.ts
  src/proxy.ts
  src/compiler.ts
  src/timeline.ts
  src/snapshot.ts
  src/capture.ts
  src/main.ts
  tests/contract.test.ts
  tests/compiler.test.ts
  tests/timeline.test.ts
  tests/determinism.test.ts
  tests/capture.spec.ts
  artifacts/.gitkeep
  README.md
```

The subsystem is independent of `agent-controller/` and of the existing experimental Babylon body-compiler branch.

---

### Task 1: Isolated project + strict scene contract

**Files:**
- Create: `experiments/directing-v1/package.json`
- Create: `experiments/directing-v1/package-lock.json`
- Create: `experiments/directing-v1/tsconfig.json`
- Create: `experiments/directing-v1/vite.config.ts`
- Create: `experiments/directing-v1/src/contract.ts`
- Create: `experiments/directing-v1/tests/contract.test.ts`

**Interfaces:**
- Produces: `SceneDocument`, `ActorSpec`, `CameraSpec`, `ShotSpec`, `CaptureSpec`, `JointName`, `SceneContractError`, `parseSceneDocument(input: unknown): SceneDocument`.
- Consumes: no implementation code from later tasks.

- [ ] **Step 1: Create the pinned ESM manifest**

Create `package.json` exactly:

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
    "@types/node": "26.2.0",
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

Expected: Node satisfies Vite's supported floor (`20.19+` or `22.12+`) and `package-lock.json` is created.

- [ ] **Step 2: Create strict compiler/test configuration**

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
    "types": ["node", "vitest/globals"]
  },
  "include": ["src", "tests", "vite.config.ts", "playwright.config.ts"]
}
```

Create `vite.config.ts`:

```ts
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    environment: 'node',
    include: ['tests/**/*.test.ts'],
  },
});
```

- [ ] **Step 3: Write RED contract tests**

`tests/contract.test.ts` must contain these exact behaviors:

```ts
import { describe, expect, it } from 'vitest';
import { parseSceneDocument, SceneContractError } from '../src/contract';

const valid = {
  schemaVersion: 'babylon-directing-v1',
  sceneId: 'scene-001',
  stage: { width: 12, depth: 8, groundY: 0, unit: 'm' },
  actors: [{
    id: 'A', proxyType: 'humanoid-basic', heightM: 1.8,
    position: { x: -1.2, y: 0, z: 0 }, rotationYDeg: 25,
    pose: { head: { x: 0, y: 10, z: 0 } }
  }],
  cameras: [{
    id: 'cam-main', position: { x: 0, y: 2.1, z: -6.5 },
    target: { x: 0, y: 1, z: 0.2 }, fovDeg: 42
  }],
  shots: [{ id: 'shot-main', cameraId: 'cam-main', startSec: 0, endSec: 2 }],
  capture: { shotId: 'shot-main', timeSec: 1.5, widthPx: 768, heightPx: 512, output: 'proof-frame.png' }
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

```bash
npm test -- tests/contract.test.ts
```

Expected: FAIL because `src/contract.ts` does not exist.

- [ ] **Step 5: Implement the contract parser with explicit helper boundaries**

`src/contract.ts` defines the approved joint set and all contract types:

```ts
export const JOINT_NAMES = [
  'pelvis', 'spine', 'chest', 'neck', 'head',
  'shoulderL', 'shoulderR', 'upperArmL', 'upperArmR',
  'forearmL', 'forearmR', 'handL', 'handR',
  'thighL', 'thighR', 'shinL', 'shinR', 'footL', 'footR'
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

Implement parser helpers in this order so semantic validation is visible and testable:

```ts
const asObject = (value: unknown, path: string): Record<string, unknown> => {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new SceneContractError('INVALID_OBJECT', path, 'expected object');
  }
  return value as Record<string, unknown>;
};

const asFiniteNumber = (value: unknown, path: string): number => {
  if (typeof value !== 'number' || !Number.isFinite(value)) {
    throw new SceneContractError('INVALID_NUMBER', path, 'expected finite number');
  }
  return value;
};

const asVec3 = (value: unknown, path: string): Vec3 => {
  const object = asObject(value, path);
  return {
    x: asFiniteNumber(object.x, `${path}.x`),
    y: asFiniteNumber(object.y, `${path}.y`),
    z: asFiniteNumber(object.z, `${path}.z`),
  };
};
```

Add equivalent `asNonEmptyString`, `asPositiveNumber`, `asPositiveInteger`, and `assertUniqueIds` helpers. `parseSceneDocument` must parse into a new object and hard-fail on: unsupported schema, duplicate actor/camera/shot ids, empty ids, unsupported proxy type, non-finite or invalid positive values, malformed vectors, unknown joints, unknown shot camera, unresolved capture shot/camera, `endSec < startSec`, and keyframes that decrease in `timeSec`. No semantic value is silently corrected.

- [ ] **Step 6: Run GREEN and typecheck**

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

### Task 2: Disposable humanoid proxy + Babylon compiler

**Files:**
- Create: `experiments/directing-v1/src/proxy.ts`
- Create: `experiments/directing-v1/src/compiler.ts`
- Create: `experiments/directing-v1/tests/compiler.test.ts`

**Interfaces:**
- Consumes: `SceneDocument`, `ActorSpec`, `JointName`.
- Produces: `CompiledActor`, `CompiledDirectingScene`, `createHumanoidProxy(scene, actor)`, `compileDirectingScene(engine, document)`.

- [ ] **Step 1: Write RED compiler tests with `NullEngine`**

The tests must assert two stable actor ids, one camera id, presence of the named joint hierarchy, exact source root positions, initial pose rotation, camera FOV, and no mutation of the parsed document.

Core assertions:

```ts
const engine = new NullEngine();
const compiled = compileDirectingScene(engine, document);
expect([...compiled.actors.keys()]).toEqual(['A', 'B']);
expect([...compiled.cameras.keys()]).toEqual(['cam']);
expect(compiled.actors.get('A')?.joints.has('upperArmL')).toBe(true);
expect(compiled.scene.activeCamera?.name).toBe('camera:cam');
expect(compiled.actors.get('A')!.root.position.x).toBeCloseTo(-1);
```

- [ ] **Step 2: Run RED**

```bash
npm test -- tests/compiler.test.ts
```

Expected: FAIL because proxy/compiler modules do not exist.

- [ ] **Step 3: Implement `createHumanoidProxy`**

Use this fixed hierarchy:

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

Use only Babylon primitives (`CreateCapsule`, `CreateBox`, `CreateSphere`) as child meshes. Apply `heightM` as a single actor-scale factor. Initial pose rotations are local radians; no child-joint translation is authored from the contract.

- [ ] **Step 4: Implement `compileDirectingScene`**

Export:

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

Implementation order is fixed: create `Scene`; create ground with exact width/depth/groundY; create actors in document order; apply root position/Y rotation and static pose; create cameras in document order; set `fov`, `minZ`, `maxZ`, and explicit target; put shots in stable map; use first camera as deterministic initial `activeCamera`. Never mutate `document`.

- [ ] **Step 5: Run GREEN**

```bash
npm test -- tests/compiler.test.ts
npm run typecheck
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add experiments/directing-v1/src/proxy.ts experiments/directing-v1/src/compiler.ts experiments/directing-v1/tests/compiler.test.ts
git commit -m "feat: compile Babylon directing proxies and cameras"
```

---

### Task 3: Stateless deterministic timeline

**Files:**
- Create: `experiments/directing-v1/src/interpolation.ts`
- Create: `experiments/directing-v1/src/timeline.ts`
- Create: `experiments/directing-v1/tests/timeline.test.ts`

**Interfaces:**
- Consumes: compiled scene and authored keyframes.
- Produces: `lerpAngleDeg`, `evaluateAtTime(compiled, timeSec)`.

- [ ] **Step 1: Write RED timeline tests**

Required tests:

```ts
expect(lerpAngleDeg(170, -170, 0.5)).toBeCloseTo(180);
```

and a seek-order test that evaluates `1.75 -> 0.25 -> 1.0` then verifies a 0-to-2 second root motion resolves exactly to x=`1`, Y rotation=`45°`, and a 0-to-`-60°` upper-arm channel resolves to `-30°`.

- [ ] **Step 2: Run RED**

```bash
npm test -- tests/timeline.test.ts
```

Expected: FAIL because interpolation/timeline modules do not exist.

- [ ] **Step 3: Implement interpolation primitives exactly**

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

Keyframe bracketing rule: before first keyframe use first value; after last use last value; between keyframes use normalized local `t`.

- [ ] **Step 4: Implement `evaluateAtTime` as reset-then-evaluate**

Export:

```ts
export type EvaluationSelection = {
  activeCameraId: string | null;
  activeShotId: string | null;
};

export function evaluateAtTime(
  compiled: CompiledDirectingScene,
  timeSec: number,
): EvaluationSelection;
```

Every call resets actors/joints/cameras from the source document, then applies current-time root, joint, and camera channels. Use shortest-path angle interpolation per Euler axis. Active shot is the first source-order shot whose interval contains `timeSec`; its camera becomes active. If no shot contains the time, retain the first declared camera as explicit deterministic fallback. No previous seek state is read.

- [ ] **Step 5: Run GREEN and whole unit suite**

```bash
npm test -- tests/timeline.test.ts
npm test
npm run typecheck
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add experiments/directing-v1/src/interpolation.ts experiments/directing-v1/src/timeline.ts experiments/directing-v1/tests/timeline.test.ts
git commit -m "feat: add deterministic Babylon directing timeline"
```

---

### Task 4: Inspectable evaluated-state snapshot

**Files:**
- Create: `experiments/directing-v1/src/snapshot.ts`
- Create: `experiments/directing-v1/tests/determinism.test.ts`

**Interfaces:**
- Consumes: `evaluateAtTime` + compiled scene.
- Produces: `EvaluatedSnapshot`, `createEvaluatedSnapshot(compiled, timeSec)`.

- [ ] **Step 1: Write RED determinism regression**

Compile the same parsed scene twice in independent `NullEngine` instances, seek each to `1.25`, and assert:

```ts
expect(JSON.stringify(createEvaluatedSnapshot(a, 1.25)))
  .toBe(JSON.stringify(createEvaluatedSnapshot(b, 1.25)));
```

Also assert that arbitrary prior seeks do not change the `1.25` snapshot.

- [ ] **Step 2: Run RED**

```bash
npm test -- tests/determinism.test.ts
```

Expected: FAIL because snapshot module does not exist.

- [ ] **Step 3: Implement stable evidence serialization**

`EvaluatedSnapshot` contains scene/schema/time; actors in document order; every joint in `JOINT_NAMES` order; active camera id/position/target/FOV; active shot id; capture settings; Babylon version. Call `evaluateAtTime` before reading runtime state.

Use evidence-only rounding:

```ts
const roundEvidence = (value: number) => Number(value.toFixed(6));
```

Do not round Babylon runtime transforms themselves.

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
git commit -m "feat: expose Babylon directing state snapshots"
```

---

### Task 5: Checked-in proof scene + browser capture harness

**Files:**
- Create: `experiments/directing-v1/public/proof-scene.json`
- Create: `experiments/directing-v1/index.html`
- Create: `experiments/directing-v1/src/capture.ts`
- Create: `experiments/directing-v1/src/main.ts`
- Create: `experiments/directing-v1/artifacts/.gitkeep`

**Interfaces:**
- Consumes: parser/compiler/timeline/snapshot.
- Produces: `captureStill(compiled, capture): Promise<string>` and `window.__zbDirecting` proof bridge.

- [ ] **Step 1: Add exact proof scene fixture**

Create `public/proof-scene.json`:

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

- [ ] **Step 2: Implement exact capture-camera resolution**

`src/capture.ts`:

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
  let cameraId = capture.cameraId;

  if (capture.shotId) {
    const shot = compiled.shots.get(capture.shotId);
    if (!shot) throw new Error(`CAPTURE_SHOT_NOT_FOUND: ${capture.shotId}`);
    cameraId = shot.cameraId;
  }

  cameraId ??= selection.activeCameraId ?? undefined;
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

- [ ] **Step 3: Add minimal browser harness**

`index.html`:

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

`main.ts` creates Babylon `Engine`, fetches `/proof-scene.json`, parses and compiles it, seeks to the declared capture time, starts render loop, and exposes only:

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

Store `lastSeekSec` explicitly. `seek` updates it and returns the evaluated snapshot; `snapshot` evaluates the stored time; `capture` calls `captureStill` with document capture settings. No auto-directing behavior is allowed.

- [ ] **Step 4: Build**

```bash
npm run build
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add experiments/directing-v1/public experiments/directing-v1/index.html experiments/directing-v1/src/capture.ts experiments/directing-v1/src/main.ts experiments/directing-v1/artifacts/.gitkeep
git commit -m "feat: add Babylon directing proof scene and capture"
```

---

### Task 6: Real Chromium smoke + persisted PNG evidence

**Files:**
- Create: `experiments/directing-v1/playwright.config.ts`
- Create: `experiments/directing-v1/tests/capture.spec.ts`

**Interfaces:**
- Consumes: `window.__zbDirecting`.
- Produces: live browser smoke evidence and generated `artifacts/proof-frame.png`.

- [ ] **Step 1: Configure Playwright**

`playwright.config.ts`:

```ts
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  testMatch: '**/*.spec.ts',
  workers: 1,
  use: {
    baseURL: 'http://127.0.0.1:4173',
    viewport: { width: 1024, height: 768 }
  },
  webServer: {
    command: 'npm run build && npx vite preview --host 127.0.0.1 --port 4173',
    url: 'http://127.0.0.1:4173',
    reuseExistingServer: false
  }
});
```

- [ ] **Step 2: Write browser smoke**

`tests/capture.spec.ts`:

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

- [ ] **Step 3: Install browser and run smoke**

```bash
npx playwright install chromium
npm run test:browser
```

Expected after implementation is correct: `1 passed` and a non-empty `artifacts/proof-frame.png`.

If this step fails, stop completion claims and invoke systematic debugging. Any repair stays inside browser bootstrap/capture files or the exact upstream component proven faulty; no scope expansion.

- [ ] **Step 4: Prove repeatability with a fresh second run**

```bash
npm run test:browser
```

Expected: `1 passed` again. State snapshot equality is required; PNG byte equality is not required.

- [ ] **Step 5: Commit browser test**

```bash
git add experiments/directing-v1/playwright.config.ts experiments/directing-v1/tests/capture.spec.ts
git commit -m "test: prove Babylon directing browser capture"
```

Generated PNG is never committed.

---

### Task 7: Operator docs + final verification + Duncan handoff

**Files:**
- Create: `experiments/directing-v1/README.md`
- Create: `experiments/directing-v1/.gitignore`

**Interfaces:**
- Consumes: Tasks 1-6.
- Produces: repeatable owner/local instructions and an evidence-ready exact HEAD for independent QC.

- [ ] **Step 1: Write README with authority boundaries and commands**

README begins with:

```text
Purpose: disposable directing/staging proof only.
Not Character Truth.
Not final animation.
Not SALVADOR auto-submit.
```

Document exactly:

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

Document fixture `public/proof-scene.json`, generated evidence `artifacts/proof-frame.png`, and browser bridge methods `seek`, `snapshot`, `capture`.

- [ ] **Step 2: Ignore generated files**

`.gitignore`:

```gitignore
node_modules/
dist/
playwright-report/
test-results/
artifacts/*.png
```

Keep `artifacts/.gitkeep` tracked.

- [ ] **Step 3: Run clean verification**

On POSIX:

```bash
rm -rf node_modules dist playwright-report test-results
npm ci
npm test
npm run typecheck
npm run build
npx playwright install chromium
npm run test:browser
```

On owner Windows PowerShell, replace only the cleanup line with:

```powershell
Remove-Item node_modules,dist,playwright-report,test-results -Recurse -Force -ErrorAction SilentlyContinue
```

Expected: unit suite PASS; typecheck PASS; build PASS; browser smoke PASS; real PNG generated; no production/canon/SALVADOR mutation.

- [ ] **Step 4: Verify scope from the authorized base**

The implementation-authorization issue will state exact `PLAN_HEAD`. Use that SHA in these commands:

```bash
git status --short
git diff --stat PLAN_HEAD...HEAD
git diff --name-only PLAN_HEAD...HEAD
```

Before running them, replace the literal token `PLAN_HEAD` in the shell command with the exact SHA copied from the authorization issue. The resulting implementation diff must be only `experiments/directing-v1/**`.

- [ ] **Step 5: Commit docs and record exact evidence values**

```bash
git add experiments/directing-v1/README.md experiments/directing-v1/.gitignore
git commit -m "docs: document Babylon directing v1 proof"
git rev-parse HEAD
node --version
node -p "require('./node_modules/@babylonjs/core/package.json').version"
```

Compute PNG SHA256 using one platform-specific command:

```bash
sha256sum artifacts/proof-frame.png
```

or on Windows PowerShell:

```powershell
(Get-FileHash -Algorithm SHA256 artifacts\proof-frame.png).Hash.ToLower()
```

- [ ] **Step 6: Post the durable LESTER handoff to #69 using only real outputs**

The comment must contain these named fields populated from the authorization issue and Step 5 command outputs: `LESTER_BABYLON_DIRECTING_V1_IMPLEMENTATION_READY`, `SPEC_HEAD`, `PLAN_HEAD`, `EXACT_IMPLEMENTATION_HEAD`, `IMPLEMENTATION_BRANCH`, `NODE`, `BABYLON`, `VITEST`, `PLAYWRIGHT`, actual unit-test pass count, `TYPECHECK = PASS`, `BUILD = PASS`, `BROWSER_SMOKE = PASS`, `PROOF_SCENE = ZB-BABYLON-DIRECTING-PROOF-001`, `CAPTURE = artifacts/proof-frame.png`, actual `CAPTURE_SHA256`, `SCRUB_REPLAY_DETERMINISM = PASS`, `NLP = NOT ADDED`, `TEXTURES = NOT ADDED`, `PRODUCTION_BODY_DEPENDENCY = NOT ADDED`, `SALVADOR_AUTO_SUBMIT = NOT ADDED`, `CANON_WRITEBACK = NO`, `PRODUCTION_INTEGRATION = NO`, `MERGE = NO`, and `NEXT = DUNCAN independent QC exact implementation HEAD`.

Do not post the handoff until every value is known from real execution. Do not predeclare DUNCAN PASS.

---

## DUNCAN Independent QC Expectations

DUNCAN must independently verify the exact implementation HEAD and adversarially check:

1. malformed/unsupported scene data and bad references fail;
2. fixed timestamps produce the same evaluated state across fresh compilations;
3. arbitrary seek order does not alter target-time state;
4. actor ids, transforms, named joints, camera values, and shot selection are inspectable;
5. real Chromium execution creates a non-empty PNG at explicit capture time;
6. proxy data never writes to Character Truth or SALVADOR runtime;
7. NLP, textures, physics, body compiler dependency, audio/music, paid services, and hidden integration did not enter scope;
8. implementation diff is isolated to the authorized proof subsystem;
9. no merge or production integration occurred.

Verdict is `PASS` or `CHANGES_REQUIRED`. PASS authorizes only the next disposable/live directing review gate, not production integration.

---

## Plan Self-Review

- **Spec coverage: PASS.** Contract, proxy geometry, cameras, blocking motion, exact-time evaluation, snapshot inspectability, still capture, live browser smoke, SALVADOR/LYNCH boundaries, determinism, QC, and authority gates are mapped to explicit tasks.
- **Placeholder scan: PASS.** No TBD/TODO or fake evidence values are present. Future evidence is obtained by named commands before handoff. The literal shell token `PLAN_HEAD` has an explicit replacement instruction tied to the authorization issue.
- **Type consistency: PASS.** Contract -> compiler -> timeline -> snapshot/capture -> browser bridge -> Playwright is one direction with named interfaces.
- **Scope: PASS.** One isolated subsystem under `experiments/directing-v1/`; no production integration.
