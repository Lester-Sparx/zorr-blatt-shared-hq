import { describe, expect, it } from 'vitest';
import {
  parseSceneDocument,
  SceneContractError,
} from '../src/contract';

const makeValid = () => ({
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
  shots: [{
    id: 'shot-main',
    cameraId: 'cam-main',
    startSec: 0,
    endSec: 2,
  }],
  capture: {
    shotId: 'shot-main',
    timeSec: 1.5,
    widthPx: 768,
    heightPx: 512,
    output: 'proof-frame.png',
  },
});

describe('parseSceneDocument', () => {
  it('accepts the v1 contract and returns a fresh parsed object', () => {
    const input = makeValid();
    const parsed = parseSceneDocument(input);
    expect(parsed.sceneId).toBe('scene-001');
    expect(parsed).not.toBe(input);
    expect(parsed.actors[0]).not.toBe(input.actors[0]);
  });

  it('rejects unsupported schema versions', () => {
    expect(() => parseSceneDocument({
      ...makeValid(),
      schemaVersion: 'v2',
    })).toThrowError(SceneContractError);
  });

  it('rejects duplicate actor ids', () => {
    const valid = makeValid();
    expect(() => parseSceneDocument({
      ...valid,
      actors: [valid.actors[0]!, valid.actors[0]!],
    })).toThrow(/DUPLICATE_ACTOR_ID/);
  });

  it('rejects duplicate camera ids', () => {
    const valid = makeValid();
    expect(() => parseSceneDocument({
      ...valid,
      cameras: [valid.cameras[0]!, valid.cameras[0]!],
    })).toThrow(/DUPLICATE_CAMERA_ID/);
  });

  it('rejects duplicate shot ids', () => {
    const valid = makeValid();
    expect(() => parseSceneDocument({
      ...valid,
      shots: [valid.shots[0]!, valid.shots[0]!],
    })).toThrow(/DUPLICATE_SHOT_ID/);
  });

  it('rejects unknown joints', () => {
    const valid = makeValid();
    const actor = {
      ...valid.actors[0]!,
      pose: { tail: { x: 0, y: 0, z: 0 } },
    };
    expect(() => parseSceneDocument({
      ...valid,
      actors: [actor],
    })).toThrow(/UNSUPPORTED_JOINT/);
  });

  it('rejects missing shot camera references', () => {
    const valid = makeValid();
    const shots = [{
      ...valid.shots[0]!,
      cameraId: 'missing',
    }];
    expect(() => parseSceneDocument({
      ...valid,
      shots,
    })).toThrow(/UNKNOWN_CAMERA_REFERENCE/);
  });

  it('rejects non-finite numeric values', () => {
    const valid = makeValid();
    const actor = {
      ...valid.actors[0]!,
      heightM: Number.NaN,
    };
    expect(() => parseSceneDocument({
      ...valid,
      actors: [actor],
    })).toThrow(/INVALID_NUMBER/);
  });

  it('rejects unsupported proxy types', () => {
    const valid = makeValid();
    expect(() => parseSceneDocument({
      ...valid,
      actors: [{
        ...valid.actors[0]!,
        proxyType: 'production-body',
      }],
    })).toThrow(/UNSUPPORTED_PROXY_TYPE/);
  });

  it('requires a capture shot or camera reference', () => {
    const valid = makeValid();
    const capture = {
      timeSec: 1.5,
      widthPx: 768,
      heightPx: 512,
      output: 'proof.png',
    };
    expect(() => parseSceneDocument({
      ...valid,
      capture,
    })).toThrow(/CAPTURE_REFERENCE_REQUIRED/);
  });

  it('rejects an unknown capture shot', () => {
    const valid = makeValid();
    expect(() => parseSceneDocument({
      ...valid,
      capture: {
        ...valid.capture,
        shotId: 'missing',
      },
    })).toThrow(/UNKNOWN_CAPTURE_SHOT/);
  });

  it('rejects a capture time outside the referenced shot', () => {
    const valid = makeValid();
    expect(() => parseSceneDocument({
      ...valid,
      capture: {
        ...valid.capture,
        timeSec: 3,
      },
    })).toThrow(/CAPTURE_TIME_OUTSIDE_SHOT/);
  });

  it('rejects root keyframes that are not strictly increasing', () => {
    const valid = makeValid();
    expect(() => parseSceneDocument({
      ...valid,
      actors: [{
        ...valid.actors[0]!,
        rootMotion: [
          {
            timeSec: 1,
            position: { x: 0, y: 0, z: 0 },
            rotationYDeg: 0,
          },
          {
            timeSec: 0.5,
            position: { x: 1, y: 0, z: 0 },
            rotationYDeg: 20,
          },
        ],
      }],
    })).toThrow(/NON_INCREASING_KEYFRAME_TIME/);
  });

  it('validates joint keyframe ordering independently per joint', () => {
    const valid = makeValid();
    expect(() => parseSceneDocument({
      ...valid,
      actors: [{
        ...valid.actors[0]!,
        jointMotion: [
          {
            timeSec: 1,
            joint: 'head',
            localRotationDeg: { x: 0, y: 10, z: 0 },
          },
          {
            timeSec: 0,
            joint: 'upperArmL',
            localRotationDeg: { x: 0, y: 0, z: 0 },
          },
          {
            timeSec: 0.5,
            joint: 'head',
            localRotationDeg: { x: 0, y: 20, z: 0 },
          },
        ],
      }],
    })).toThrow(/NON_INCREASING_KEYFRAME_TIME/);
  });

  it('rejects invalid camera clip ranges', () => {
    const valid = makeValid();
    expect(() => parseSceneDocument({
      ...valid,
      cameras: [{
        ...valid.cameras[0]!,
        nearClip: 10,
        farClip: 1,
      }],
    })).toThrow(/INVALID_CLIP_RANGE/);
  });

  it('rejects FOV values outside the physical perspective range', () => {
    const valid = makeValid();
    expect(() => parseSceneDocument({
      ...valid,
      cameras: [{
        ...valid.cameras[0]!,
        fovDeg: 180,
      }],
    })).toThrow(/INVALID_FOV/);
  });
});
