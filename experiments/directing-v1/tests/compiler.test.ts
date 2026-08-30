import { NullEngine } from '@babylonjs/core/Engines/nullEngine';
import { describe, expect, it } from 'vitest';
import { compileDirectingScene } from '../src/compiler';
import { JOINT_NAMES, parseSceneDocument } from '../src/contract';

const makeDocument = () => parseSceneDocument({
  schemaVersion: 'babylon-directing-v1',
  sceneId: 'compiler-proof',
  stage: { width: 10, depth: 8, groundY: 0, unit: 'm' },
  actors: [
    {
      id: 'A',
      proxyType: 'humanoid-basic',
      heightM: 1.8,
      position: { x: -1, y: 0, z: 0.2 },
      rotationYDeg: 30,
      pose: {
        upperArmL: { x: 0, y: 0, z: -25 },
        head: { x: 0, y: 8, z: 0 },
      },
    },
    {
      id: 'B',
      proxyType: 'humanoid-basic',
      heightM: 1.6,
      position: { x: 1.2, y: 0, z: 0.4 },
      rotationYDeg: -120,
      pose: {
        upperArmR: { x: 0, y: 0, z: 35 },
      },
    },
  ],
  cameras: [{
    id: 'cam',
    position: { x: 0, y: 2, z: -6 },
    target: { x: 0, y: 1, z: 0 },
    fovDeg: 40,
    nearClip: 0.1,
    farClip: 80,
  }],
  shots: [{
    id: 'shot',
    cameraId: 'cam',
    startSec: 0,
    endSec: 2,
  }],
  capture: {
    shotId: 'shot',
    timeSec: 1,
    widthPx: 640,
    heightPx: 480,
    output: 'proof.png',
  },
});

describe('compileDirectingScene', () => {
  it('compiles stable actor, camera, shot, and stage identifiers', () => {
    const engine = new NullEngine();
    try {
      const compiled = compileDirectingScene(engine, makeDocument());
      expect([...compiled.actors.keys()]).toEqual(['A', 'B']);
      expect([...compiled.cameras.keys()]).toEqual(['cam']);
      expect([...compiled.shots.keys()]).toEqual(['shot']);
      expect(compiled.scene.getMeshByName('stage:ground')).not.toBeNull();
      expect(compiled.scene.activeCamera?.name).toBe('camera:cam');
    } finally {
      engine.dispose();
    }
  });

  it('creates the exact approved named-joint hierarchy for each proxy', () => {
    const engine = new NullEngine();
    try {
      const compiled = compileDirectingScene(engine, makeDocument());
      for (const actor of compiled.actors.values()) {
        expect([...actor.joints.keys()]).toEqual([...JOINT_NAMES]);
        expect(actor.joints.get('upperArmL')?.parent?.name)
          .toBe(`actor:${actor.spec.id}:joint:shoulderL`);
        expect(actor.joints.get('forearmR')?.parent?.name)
          .toBe(`actor:${actor.spec.id}:joint:upperArmR`);
        expect(actor.joints.get('shinL')?.parent?.name)
          .toBe(`actor:${actor.spec.id}:joint:thighL`);
      }
    } finally {
      engine.dispose();
    }
  });

  it('applies exact source transforms, pose, scale, and camera optics', () => {
    const engine = new NullEngine();
    try {
      const compiled = compileDirectingScene(engine, makeDocument());
      const actorA = compiled.actors.get('A')!;
      const actorB = compiled.actors.get('B')!;
      const camera = compiled.cameras.get('cam')!;

      expect(actorA.root.position.x).toBeCloseTo(-1);
      expect(actorA.root.position.z).toBeCloseTo(0.2);
      expect(actorA.root.rotation.y * 180 / Math.PI).toBeCloseTo(30);
      expect(actorA.joints.get('upperArmL')!.rotation.z * 180 / Math.PI)
        .toBeCloseTo(-25);
      expect(actorA.root.scaling.x).toBeCloseTo(1);
      expect(actorB.root.scaling.x).toBeCloseTo(1.6 / 1.8);

      expect(camera.position.z).toBeCloseTo(-6);
      expect(camera.getTarget().y).toBeCloseTo(1);
      expect(camera.fov * 180 / Math.PI).toBeCloseTo(40);
      expect(camera.minZ).toBeCloseTo(0.1);
      expect(camera.maxZ).toBeCloseTo(80);
    } finally {
      engine.dispose();
    }
  });

  it('does not mutate parsed source data or create implicit animations', () => {
    const engine = new NullEngine();
    try {
      const document = makeDocument();
      const before = JSON.stringify(document);
      const compiled = compileDirectingScene(engine, document);
      expect(JSON.stringify(document)).toBe(before);
      expect(compiled.document).toBe(document);
      expect(compiled.scene.animationGroups).toHaveLength(0);
    } finally {
      engine.dispose();
    }
  });
});
