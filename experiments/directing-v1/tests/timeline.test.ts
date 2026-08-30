import { NullEngine } from '@babylonjs/core/Engines/nullEngine';
import { describe, expect, it } from 'vitest';
import { compileDirectingScene } from '../src/compiler';
import { parseSceneDocument } from '../src/contract';
import { lerpAngleDeg } from '../src/interpolation';
import { evaluateAtTime } from '../src/timeline';

const makeDocument = () => parseSceneDocument({
  schemaVersion: 'babylon-directing-v1',
  sceneId: 'timeline-proof',
  stage: { width: 10, depth: 8, groundY: 0, unit: 'm' },
  actors: [{
    id: 'A',
    proxyType: 'humanoid-basic',
    heightM: 1.8,
    position: { x: 0, y: 0, z: 0 },
    rotationYDeg: 0,
    pose: {
      upperArmL: { x: 0, y: 0, z: 0 },
    },
    rootMotion: [
      {
        timeSec: 0,
        position: { x: 0, y: 0, z: 0 },
        rotationYDeg: 0,
      },
      {
        timeSec: 2,
        position: { x: 2, y: 0, z: 1 },
        rotationYDeg: 90,
      },
    ],
    jointMotion: [
      {
        timeSec: 0,
        joint: 'upperArmL',
        localRotationDeg: { x: 0, y: 0, z: 0 },
      },
      {
        timeSec: 2,
        joint: 'upperArmL',
        localRotationDeg: { x: 0, y: 0, z: -60 },
      },
    ],
  }],
  cameras: [
    {
      id: 'cam-a',
      position: { x: 0, y: 2, z: -8 },
      target: { x: 0, y: 1, z: 0 },
      fovDeg: 50,
      motion: [
        {
          timeSec: 0,
          position: { x: 0, y: 2, z: -8 },
          target: { x: 0, y: 1, z: 0 },
          fovDeg: 50,
        },
        {
          timeSec: 2,
          position: { x: 0, y: 2, z: -4 },
          target: { x: 1, y: 1, z: 0.5 },
          fovDeg: 40,
        },
      ],
    },
    {
      id: 'cam-b',
      position: { x: 5, y: 3, z: -5 },
      target: { x: 0, y: 1, z: 0 },
      fovDeg: 35,
    },
  ],
  shots: [
    {
      id: 'shot-a',
      cameraId: 'cam-a',
      startSec: 0,
      endSec: 1,
    },
    {
      id: 'shot-b',
      cameraId: 'cam-b',
      startSec: 1.01,
      endSec: 2,
    },
  ],
  capture: {
    shotId: 'shot-a',
    timeSec: 1,
    widthPx: 640,
    heightPx: 480,
    output: 'proof.png',
  },
});

describe('deterministic timeline', () => {
  it('uses shortest-path angle interpolation', () => {
    expect(lerpAngleDeg(170, -170, 0.5)).toBeCloseTo(180);
    expect(lerpAngleDeg(-170, 170, 0.5)).toBeCloseTo(-180);
  });

  it('is reset-then-evaluate and independent of seek order', () => {
    const engine = new NullEngine();
    try {
      const compiled = compileDirectingScene(engine, makeDocument());
      evaluateAtTime(compiled, 1.75);
      evaluateAtTime(compiled, 0.25);
      const selection = evaluateAtTime(compiled, 1);

      const actor = compiled.actors.get('A')!;
      expect(actor.root.position.x).toBeCloseTo(1);
      expect(actor.root.position.z).toBeCloseTo(0.5);
      expect(actor.root.rotation.y * 180 / Math.PI).toBeCloseTo(45);
      expect(actor.joints.get('upperArmL')!.rotation.z * 180 / Math.PI)
        .toBeCloseTo(-30);
      expect(selection).toEqual({
        activeCameraId: 'cam-a',
        activeShotId: 'shot-a',
      });
    } finally {
      engine.dispose();
    }
  });

  it('evaluates authored camera motion but selects cameras from explicit shots', () => {
    const engine = new NullEngine();
    try {
      const compiled = compileDirectingScene(engine, makeDocument());
      const selection = evaluateAtTime(compiled, 1.5);
      const movedCamera = compiled.cameras.get('cam-a')!;

      expect(movedCamera.position.z).toBeCloseTo(-5);
      expect(movedCamera.getTarget().x).toBeCloseTo(0.75);
      expect(movedCamera.fov * 180 / Math.PI).toBeCloseTo(42.5);
      expect(selection.activeShotId).toBe('shot-b');
      expect(selection.activeCameraId).toBe('cam-b');
      expect(compiled.scene.activeCamera?.name).toBe('camera:cam-b');
    } finally {
      engine.dispose();
    }
  });

  it('clamps authored channels outside their keyframe interval', () => {
    const engine = new NullEngine();
    try {
      const compiled = compileDirectingScene(engine, makeDocument());
      evaluateAtTime(compiled, 5);
      expect(compiled.actors.get('A')!.root.position.x).toBeCloseTo(2);
      expect(
        compiled.actors.get('A')!.joints.get('upperArmL')!.rotation.z
          * 180 / Math.PI,
      ).toBeCloseTo(-60);
      expect(compiled.cameras.get('cam-a')!.position.z).toBeCloseTo(-4);
    } finally {
      engine.dispose();
    }
  });

  it('falls back to the first declared camera outside every shot', () => {
    const engine = new NullEngine();
    try {
      const compiled = compileDirectingScene(engine, makeDocument());
      expect(evaluateAtTime(compiled, 1.005)).toEqual({
        activeCameraId: 'cam-a',
        activeShotId: null,
      });
    } finally {
      engine.dispose();
    }
  });

  it('rejects invalid evaluation times', () => {
    const engine = new NullEngine();
    try {
      const compiled = compileDirectingScene(engine, makeDocument());
      expect(() => evaluateAtTime(compiled, Number.NaN))
        .toThrow(/INVALID_EVALUATION_TIME/);
      expect(() => evaluateAtTime(compiled, -0.1))
        .toThrow(/INVALID_EVALUATION_TIME/);
    } finally {
      engine.dispose();
    }
  });
});
