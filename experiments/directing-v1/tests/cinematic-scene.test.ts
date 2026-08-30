import { NullEngine } from '@babylonjs/core/Engines/nullEngine';
import { describe, expect, it } from 'vitest';
import {
  buildCinematicSet,
  CINEMATIC_SET_LIGHT_NAMES,
  CINEMATIC_SET_MESH_NAMES,
} from '../src/cinematicSet';
import { compileDirectingScene } from '../src/compiler';
import { parseSceneDocument } from '../src/contract';
import { exportCanonicalBabylonScene } from '../src/sceneExport';

const makeDocument = () => parseSceneDocument({
  schemaVersion: 'babylon-directing-v1',
  sceneId: 'ZB-CINEMATIC-SCENE-R01',
  stage: { width: 20, depth: 14, groundY: 0, unit: 'm' },
  actors: [
    {
      id: 'A',
      proxyType: 'humanoid-basic',
      heightM: 1.82,
      position: { x: -1.25, y: 0, z: 0.65 },
      rotationYDeg: 28,
      pose: {
        head: { x: -4, y: 12, z: 0 },
        upperArmL: { x: 0, y: 0, z: -18 },
        forearmL: { x: 0, y: 0, z: -28 },
        upperArmR: { x: 0, y: 0, z: 12 },
      },
    },
    {
      id: 'B',
      proxyType: 'humanoid-basic',
      heightM: 1.68,
      position: { x: 1.45, y: 0, z: 2.35 },
      rotationYDeg: -138,
      pose: {
        head: { x: 0, y: -10, z: 0 },
        upperArmR: { x: 0, y: 0, z: 42 },
        forearmR: { x: 0, y: 0, z: 24 },
        upperArmL: { x: 0, y: 0, z: -8 },
      },
    },
  ],
  cameras: [{
    id: 'cam-scene-main',
    position: { x: 0.65, y: 2.15, z: -8.4 },
    target: { x: 0, y: 1.25, z: 1.75 },
    fovDeg: 47,
    nearClip: 0.05,
    farClip: 120,
  }],
  shots: [{
    id: 'shot-scene-main',
    cameraId: 'cam-scene-main',
    startSec: 0,
    endSec: 4,
    preferredCaptureSec: 2.25,
  }],
  capture: {
    shotId: 'shot-scene-main',
    timeSec: 2.25,
    widthPx: 1280,
    heightPx: 720,
    output: 'zorr-cinematic-scene-r01.png',
  },
});

const compileScene = () => {
  const engine = new NullEngine({
    renderWidth: 1280,
    renderHeight: 720,
    textureSize: 512,
    deterministicLockstep: true,
    lockstepMaxSteps: 4,
  });
  const compiled = compileDirectingScene(engine, makeDocument());
  const set = buildCinematicSet(compiled.scene);
  return { engine, compiled, set };
};

describe('Babylon blade-dodge scene R03', () => {
  it('builds the exact named set and light inventory', () => {
    const { engine, compiled, set } = compileScene();
    try {
      expect(set.meshes.map((mesh) => mesh.name)).toEqual([
        ...CINEMATIC_SET_MESH_NAMES,
      ]);
      expect(set.lights.map((light) => light.name)).toEqual([
        ...CINEMATIC_SET_LIGHT_NAMES,
      ]);
      for (const name of CINEMATIC_SET_MESH_NAMES) {
        expect(compiled.scene.getMeshByName(name)).not.toBeNull();
      }
      for (const name of CINEMATIC_SET_LIGHT_NAMES) {
        expect(compiled.scene.getLightByName(name)).not.toBeNull();
      }
      expect(compiled.scene.fogEnabled).toBe(true);
      expect(compiled.scene.metadata?.zorrCinematicScene?.authority)
        .toBe('PROTOTYPE_NON_CANON');
    } finally {
      engine.dispose();
    }
  });

  it('exports a deterministic, inspectable Babylon scene document', () => {
    const first = compileScene();
    const second = compileScene();
    try {
      const firstText = exportCanonicalBabylonScene(first.compiled.scene);
      const secondText = exportCanonicalBabylonScene(second.compiled.scene);
      expect(secondText).toBe(firstText);
      expect(firstText).not.toContain('uniqueId');

      const exported = JSON.parse(firstText) as {
        cameras?: Array<{ name?: string }>;
        lights?: Array<{ name?: string }>;
        meshes?: Array<{ name?: string }>;
        metadata?: {
          zorrCinematicScene?: {
            sceneId?: string;
            authority?: string;
          };
        };
      };
      expect(exported.metadata?.zorrCinematicScene).toEqual({
        sceneId: 'ZB-CINEMATIC-SCENE-R01',
        sceneVersion: 'R03',
        authority: 'PROTOTYPE_NON_CANON',
        designIntent: 'BLADE_DODGE_PRODUCTION_GREYBOX',
      });
      expect(exported.cameras?.map(({ name }) => name)).toContain(
        'camera:cam-scene-main',
      );
      expect(exported.lights?.map(({ name }) => name)).toEqual(
        expect.arrayContaining([...CINEMATIC_SET_LIGHT_NAMES]),
      );
      const meshNames = exported.meshes?.map(({ name }) => name) ?? [];
      expect(meshNames).toEqual(
        expect.arrayContaining([
          ...CINEMATIC_SET_MESH_NAMES,
          'actor:A:mesh:head',
          'actor:B:mesh:head',
        ]),
      );
    } finally {
      first.engine.dispose();
      second.engine.dispose();
    }
  });
});
