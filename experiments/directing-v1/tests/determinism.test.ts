import { NullEngine } from '@babylonjs/core/Engines/nullEngine';
import { describe, expect, it } from 'vitest';
import { compileDirectingScene } from '../src/compiler';
import { JOINT_NAMES, parseSceneDocument } from '../src/contract';
import { createEvaluatedSnapshot } from '../src/snapshot';
import { evaluateAtTime } from '../src/timeline';

const makeDocument = () => parseSceneDocument({
  schemaVersion: 'babylon-directing-v1',
  sceneId: 'determinism-proof',
  stage: { width: 12, depth: 8, groundY: 0, unit: 'm' },
  actors: [
    {
      id: 'A',
      proxyType: 'humanoid-basic',
      heightM: 1.8,
      position: { x: -1, y: 0, z: 0 },
      rotationYDeg: 10,
      pose: {
        head: { x: 0, y: 8, z: 0 },
      },
      rootMotion: [
        {
          timeSec: 0,
          position: { x: -1, y: 0, z: 0 },
          rotationYDeg: 10,
        },
        {
          timeSec: 2,
          position: { x: 1, y: 0, z: 0.5 },
          rotationYDeg: 70,
        },
      ],
    },
    {
      id: 'B',
      proxyType: 'humanoid-basic',
      heightM: 1.65,
      position: { x: 1.5, y: 0, z: 0.4 },
      rotationYDeg: -140,
      pose: {
        upperArmR: { x: 0, y: 0, z: 30 },
      },
    },
  ],
  cameras: [{
    id: 'cam',
    position: { x: 0, y: 2.2, z: -6.5 },
    target: { x: 0, y: 1, z: 0.2 },
    fovDeg: 42,
  }],
  shots: [{
    id: 'shot',
    cameraId: 'cam',
    startSec: 0,
    endSec: 2,
  }],
  capture: {
    shotId: 'shot',
    timeSec: 1.25,
    widthPx: 768,
    heightPx: 512,
    output: 'proof-frame.png',
  },
});

describe('evaluated-state snapshot determinism', () => {
  it('serializes identically across fresh independent compilations', () => {
    const engineA = new NullEngine();
    const engineB = new NullEngine();
    try {
      const a = compileDirectingScene(engineA, makeDocument());
      const b = compileDirectingScene(engineB, makeDocument());

      expect(JSON.stringify(createEvaluatedSnapshot(a, 1.25)))
        .toBe(JSON.stringify(createEvaluatedSnapshot(b, 1.25)));
    } finally {
      engineA.dispose();
      engineB.dispose();
    }
  });

  it('is unchanged by arbitrary prior seek history', () => {
    const engine = new NullEngine();
    try {
      const compiled = compileDirectingScene(engine, makeDocument());
      const expected = createEvaluatedSnapshot(compiled, 1.25);
      evaluateAtTime(compiled, 0.1);
      evaluateAtTime(compiled, 1.9);
      evaluateAtTime(compiled, 0.6);
      const replayed = createEvaluatedSnapshot(compiled, 1.25);
      expect(replayed).toEqual(expected);
    } finally {
      engine.dispose();
    }
  });

  it('uses stable document and approved joint ordering with inspectable values', () => {
    const engine = new NullEngine();
    try {
      const compiled = compileDirectingScene(engine, makeDocument());
      const snapshot = createEvaluatedSnapshot(compiled, 1.25);
      expect(snapshot.actors.map(({ id }) => id)).toEqual(['A', 'B']);
      expect(Object.keys(snapshot.actors[0]!.joints)).toEqual([...JOINT_NAMES]);
      expect(snapshot.actors[0]!.position).toEqual({
        x: 0.25,
        y: 0,
        z: 0.3125,
      });
      expect(snapshot.actors[0]!.rotationYDeg).toBe(47.5);
      expect(snapshot.activeCamera?.id).toBe('cam');
      expect(snapshot.activeCamera?.target).toEqual({ x: 0, y: 1, z: 0.2 });
      expect(snapshot.activeShotId).toBe('shot');
      expect(snapshot.capture.output).toBe('proof-frame.png');
      expect(snapshot.runtime.babylonVersion).toBe('9.22.2');
    } finally {
      engine.dispose();
    }
  });
});
