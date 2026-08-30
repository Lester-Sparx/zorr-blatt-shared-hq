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
  constructor(
    public readonly code: string,
    public readonly path: string,
    message: string,
  ) {
    super(`${code} at ${path}: ${message}`);
    this.name = 'SceneContractError';
  }
}

const JOINT_SET = new Set<string>(JOINT_NAMES);

const fail = (code: string, path: string, message: string): never => {
  throw new SceneContractError(code, path, message);
};

const asObject = (value: unknown, path: string): Record<string, unknown> => {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    return fail('INVALID_OBJECT', path, 'expected object');
  }
  return value as Record<string, unknown>;
};

const asArray = (value: unknown, path: string): unknown[] => {
  if (!Array.isArray(value)) {
    return fail('INVALID_ARRAY', path, 'expected array');
  }
  return value;
};

const asNonEmptyString = (value: unknown, path: string): string => {
  if (typeof value !== 'string' || value.trim().length === 0) {
    return fail('INVALID_STRING', path, 'expected non-empty string');
  }
  return value;
};

const asFiniteNumber = (value: unknown, path: string): number => {
  if (typeof value !== 'number' || !Number.isFinite(value)) {
    return fail('INVALID_NUMBER', path, 'expected finite number');
  }
  return value;
};

const asNonNegativeNumber = (value: unknown, path: string): number => {
  const number = asFiniteNumber(value, path);
  if (number < 0) {
    return fail('INVALID_NON_NEGATIVE_NUMBER', path, 'expected number >= 0');
  }
  return number;
};

const asPositiveNumber = (value: unknown, path: string): number => {
  const number = asFiniteNumber(value, path);
  if (number <= 0) {
    return fail('INVALID_POSITIVE_NUMBER', path, 'expected number > 0');
  }
  return number;
};

const asPositiveInteger = (value: unknown, path: string): number => {
  const number = asPositiveNumber(value, path);
  if (!Number.isInteger(number)) {
    return fail('INVALID_POSITIVE_INTEGER', path, 'expected positive integer');
  }
  return number;
};

const asVec3 = (value: unknown, path: string): Vec3 => {
  const object = asObject(value, path);
  return {
    x: asFiniteNumber(object.x, `${path}.x`),
    y: asFiniteNumber(object.y, `${path}.y`),
    z: asFiniteNumber(object.z, `${path}.z`),
  };
};

const optionalString = (
  value: unknown,
  path: string,
): string | undefined => value === undefined ? undefined : asNonEmptyString(value, path);

const assertUniqueIds = (
  values: readonly { id: string }[],
  code: string,
  path: string,
): void => {
  const seen = new Set<string>();
  values.forEach((value, index) => {
    if (seen.has(value.id)) {
      fail(code, `${path}[${index}].id`, `duplicate id "${value.id}"`);
    }
    seen.add(value.id);
  });
};

const assertStrictlyIncreasing = (
  values: readonly { timeSec: number }[],
  path: string,
): void => {
  for (let index = 1; index < values.length; index += 1) {
    const previous = values[index - 1]!;
    const current = values[index]!;
    if (current.timeSec <= previous.timeSec) {
      fail(
        'NON_INCREASING_KEYFRAME_TIME',
        `${path}[${index}].timeSec`,
        `expected time greater than ${previous.timeSec}`,
      );
    }
  }
};

const parseJointName = (value: unknown, path: string): JointName => {
  const name = asNonEmptyString(value, path);
  if (!JOINT_SET.has(name)) {
    return fail('UNSUPPORTED_JOINT', path, `"${name}" is not supported`);
  }
  return name as JointName;
};

const parsePose = (
  value: unknown,
  path: string,
): Partial<Record<JointName, EulerDeg>> => {
  const object = asObject(value, path);
  const pose: Partial<Record<JointName, EulerDeg>> = {};
  for (const [jointValue, rotationValue] of Object.entries(object)) {
    const joint = parseJointName(jointValue, `${path}.${jointValue}`);
    pose[joint] = asVec3(rotationValue, `${path}.${jointValue}`);
  }
  return pose;
};

const parseRootMotion = (value: unknown, path: string): RootKeyframe[] => {
  const frames = asArray(value, path).map((frameValue, index) => {
    const framePath = `${path}[${index}]`;
    const frame = asObject(frameValue, framePath);
    return {
      timeSec: asNonNegativeNumber(frame.timeSec, `${framePath}.timeSec`),
      position: asVec3(frame.position, `${framePath}.position`),
      rotationYDeg: asFiniteNumber(frame.rotationYDeg, `${framePath}.rotationYDeg`),
    };
  });
  if (frames.length === 0) {
    fail('EMPTY_MOTION_CHANNEL', path, 'root motion must contain at least one keyframe');
  }
  assertStrictlyIncreasing(frames, path);
  return frames;
};

const parseJointMotion = (value: unknown, path: string): JointKeyframe[] => {
  const lastTimeByJoint = new Map<JointName, number>();
  const frames = asArray(value, path).map((frameValue, index) => {
    const framePath = `${path}[${index}]`;
    const frame = asObject(frameValue, framePath);
    const joint = parseJointName(frame.joint, `${framePath}.joint`);
    const timeSec = asNonNegativeNumber(frame.timeSec, `${framePath}.timeSec`);
    const previous = lastTimeByJoint.get(joint);
    if (previous !== undefined && timeSec <= previous) {
      fail(
        'NON_INCREASING_KEYFRAME_TIME',
        `${framePath}.timeSec`,
        `joint "${joint}" time must be greater than ${previous}`,
      );
    }
    lastTimeByJoint.set(joint, timeSec);
    return {
      timeSec,
      joint,
      localRotationDeg: asVec3(
        frame.localRotationDeg,
        `${framePath}.localRotationDeg`,
      ),
    };
  });
  if (frames.length === 0) {
    fail('EMPTY_MOTION_CHANNEL', path, 'joint motion must contain at least one keyframe');
  }
  return frames;
};

const parseCameraMotion = (value: unknown, path: string): CameraKeyframe[] => {
  const frames = asArray(value, path).map((frameValue, index) => {
    const framePath = `${path}[${index}]`;
    const frame = asObject(frameValue, framePath);
    const fovDeg = asPositiveNumber(frame.fovDeg, `${framePath}.fovDeg`);
    if (fovDeg >= 180) {
      fail('INVALID_FOV', `${framePath}.fovDeg`, 'expected FOV below 180 degrees');
    }
    return {
      timeSec: asNonNegativeNumber(frame.timeSec, `${framePath}.timeSec`),
      position: asVec3(frame.position, `${framePath}.position`),
      target: asVec3(frame.target, `${framePath}.target`),
      fovDeg,
    };
  });
  if (frames.length === 0) {
    fail('EMPTY_MOTION_CHANNEL', path, 'camera motion must contain at least one keyframe');
  }
  assertStrictlyIncreasing(frames, path);
  return frames;
};

const parseActor = (value: unknown, index: number): ActorSpec => {
  const path = `actors[${index}]`;
  const actor = asObject(value, path);
  const proxyType = asNonEmptyString(actor.proxyType, `${path}.proxyType`);
  if (proxyType !== 'humanoid-basic') {
    fail('UNSUPPORTED_PROXY_TYPE', `${path}.proxyType`, `"${proxyType}" is not supported`);
  }

  const rootMotion = actor.rootMotion === undefined
    ? undefined
    : parseRootMotion(actor.rootMotion, `${path}.rootMotion`);
  const jointMotion = actor.jointMotion === undefined
    ? undefined
    : parseJointMotion(actor.jointMotion, `${path}.jointMotion`);
  const label = optionalString(actor.label, `${path}.label`);

  return {
    id: asNonEmptyString(actor.id, `${path}.id`),
    proxyType: 'humanoid-basic',
    heightM: asPositiveNumber(actor.heightM, `${path}.heightM`),
    position: asVec3(actor.position, `${path}.position`),
    rotationYDeg: asFiniteNumber(actor.rotationYDeg, `${path}.rotationYDeg`),
    pose: parsePose(actor.pose, `${path}.pose`),
    ...(rootMotion ? { rootMotion } : {}),
    ...(jointMotion ? { jointMotion } : {}),
    ...(label ? { label } : {}),
  };
};

const parseCamera = (value: unknown, index: number): CameraSpec => {
  const path = `cameras[${index}]`;
  const camera = asObject(value, path);
  const fovDeg = asPositiveNumber(camera.fovDeg, `${path}.fovDeg`);
  if (fovDeg >= 180) {
    fail('INVALID_FOV', `${path}.fovDeg`, 'expected FOV below 180 degrees');
  }

  const nearClip = camera.nearClip === undefined
    ? undefined
    : asPositiveNumber(camera.nearClip, `${path}.nearClip`);
  const farClip = camera.farClip === undefined
    ? undefined
    : asPositiveNumber(camera.farClip, `${path}.farClip`);
  if (
    nearClip !== undefined
    && farClip !== undefined
    && farClip <= nearClip
  ) {
    fail(
      'INVALID_CLIP_RANGE',
      `${path}.farClip`,
      'far clip must be greater than near clip',
    );
  }
  const motion = camera.motion === undefined
    ? undefined
    : parseCameraMotion(camera.motion, `${path}.motion`);

  return {
    id: asNonEmptyString(camera.id, `${path}.id`),
    position: asVec3(camera.position, `${path}.position`),
    target: asVec3(camera.target, `${path}.target`),
    fovDeg,
    ...(nearClip !== undefined ? { nearClip } : {}),
    ...(farClip !== undefined ? { farClip } : {}),
    ...(motion ? { motion } : {}),
  };
};

const parseShot = (value: unknown, index: number): ShotSpec => {
  const path = `shots[${index}]`;
  const shot = asObject(value, path);
  const startSec = asNonNegativeNumber(shot.startSec, `${path}.startSec`);
  const endSec = asNonNegativeNumber(shot.endSec, `${path}.endSec`);
  if (endSec < startSec) {
    fail('NEGATIVE_SHOT_DURATION', `${path}.endSec`, 'end must be >= start');
  }
  const label = optionalString(shot.label, `${path}.label`);
  const preferredCaptureSec = shot.preferredCaptureSec === undefined
    ? undefined
    : asNonNegativeNumber(
      shot.preferredCaptureSec,
      `${path}.preferredCaptureSec`,
    );
  if (
    preferredCaptureSec !== undefined
    && (preferredCaptureSec < startSec || preferredCaptureSec > endSec)
  ) {
    fail(
      'PREFERRED_CAPTURE_OUTSIDE_SHOT',
      `${path}.preferredCaptureSec`,
      'preferred capture must fall inside shot interval',
    );
  }

  return {
    id: asNonEmptyString(shot.id, `${path}.id`),
    cameraId: asNonEmptyString(shot.cameraId, `${path}.cameraId`),
    startSec,
    endSec,
    ...(label ? { label } : {}),
    ...(preferredCaptureSec !== undefined ? { preferredCaptureSec } : {}),
  };
};

const parseCapture = (value: unknown): CaptureSpec => {
  const path = 'capture';
  const capture = asObject(value, path);
  const shotId = capture.shotId === undefined
    ? undefined
    : asNonEmptyString(capture.shotId, `${path}.shotId`);
  const cameraId = capture.cameraId === undefined
    ? undefined
    : asNonEmptyString(capture.cameraId, `${path}.cameraId`);
  if (!shotId && !cameraId) {
    fail(
      'CAPTURE_REFERENCE_REQUIRED',
      path,
      'capture must reference a shotId or cameraId',
    );
  }

  return {
    ...(shotId ? { shotId } : {}),
    ...(cameraId ? { cameraId } : {}),
    timeSec: asNonNegativeNumber(capture.timeSec, `${path}.timeSec`),
    widthPx: asPositiveInteger(capture.widthPx, `${path}.widthPx`),
    heightPx: asPositiveInteger(capture.heightPx, `${path}.heightPx`),
    output: asNonEmptyString(capture.output, `${path}.output`),
  };
};

export function parseSceneDocument(input: unknown): SceneDocument {
  const root = asObject(input, '$');
  if (root.schemaVersion !== 'babylon-directing-v1') {
    fail(
      'UNSUPPORTED_SCHEMA_VERSION',
      'schemaVersion',
      'expected "babylon-directing-v1"',
    );
  }

  const stageValue = asObject(root.stage, 'stage');
  if (stageValue.unit !== 'm') {
    fail('UNSUPPORTED_STAGE_UNIT', 'stage.unit', 'v1 requires meters ("m")');
  }

  const actors = asArray(root.actors, 'actors').map(parseActor);
  const cameras = asArray(root.cameras, 'cameras').map(parseCamera);
  const shots = asArray(root.shots, 'shots').map(parseShot);
  const capture = parseCapture(root.capture);

  assertUniqueIds(actors, 'DUPLICATE_ACTOR_ID', 'actors');
  assertUniqueIds(cameras, 'DUPLICATE_CAMERA_ID', 'cameras');
  assertUniqueIds(shots, 'DUPLICATE_SHOT_ID', 'shots');

  const cameraIds = new Set(cameras.map(({ id }) => id));
  const shotById = new Map(shots.map((shot) => [shot.id, shot] as const));

  shots.forEach((shot, index) => {
    if (!cameraIds.has(shot.cameraId)) {
      fail(
        'UNKNOWN_CAMERA_REFERENCE',
        `shots[${index}].cameraId`,
        `"${shot.cameraId}" does not exist`,
      );
    }
  });

  if (capture.cameraId && !cameraIds.has(capture.cameraId)) {
    fail(
      'UNKNOWN_CAPTURE_CAMERA',
      'capture.cameraId',
      `"${capture.cameraId}" does not exist`,
    );
  }

  if (capture.shotId) {
    const shot = shotById.get(capture.shotId) ?? fail(
      'UNKNOWN_CAPTURE_SHOT',
      'capture.shotId',
      `"${capture.shotId}" does not exist`,
    );
    if (capture.timeSec < shot.startSec || capture.timeSec > shot.endSec) {
      fail(
        'CAPTURE_TIME_OUTSIDE_SHOT',
        'capture.timeSec',
        `expected time inside [${shot.startSec}, ${shot.endSec}]`,
      );
    }
  }

  return {
    schemaVersion: 'babylon-directing-v1',
    sceneId: asNonEmptyString(root.sceneId, 'sceneId'),
    stage: {
      width: asPositiveNumber(stageValue.width, 'stage.width'),
      depth: asPositiveNumber(stageValue.depth, 'stage.depth'),
      groundY: asFiniteNumber(stageValue.groundY, 'stage.groundY'),
      unit: 'm',
    },
    actors,
    cameras,
    shots,
    capture,
  };
}
