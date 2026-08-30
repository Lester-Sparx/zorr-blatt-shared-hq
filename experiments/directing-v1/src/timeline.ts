import { Vector3 } from '@babylonjs/core/Maths/math.vector';
import type {
  CameraKeyframe,
  EulerDeg,
  JointKeyframe,
  RootKeyframe,
  Vec3,
} from './contract';
import { JOINT_NAMES, type JointName } from './contract';
import {
  DEFAULT_FAR_CLIP,
  DEFAULT_NEAR_CLIP,
  type CompiledDirectingScene,
} from './compiler';
import { lerp, lerpAngleDeg, lerpVec3 } from './interpolation';

const DEG_TO_RAD = Math.PI / 180;

export type EvaluationSelection = {
  activeCameraId: string | null;
  activeShotId: string | null;
};

type Timed = { timeSec: number };

const toVector3 = ({ x, y, z }: Vec3): Vector3 => new Vector3(x, y, z);

const applyEulerDeg = (
  target: { rotation: Vector3 },
  value: EulerDeg,
): void => {
  target.rotation.copyFromFloats(
    value.x * DEG_TO_RAD,
    value.y * DEG_TO_RAD,
    value.z * DEG_TO_RAD,
  );
};

const bracket = <T extends Timed>(
  frames: readonly T[],
  timeSec: number,
): { left: T; right: T; t: number } => {
  const first = frames[0];
  const last = frames.at(-1);
  if (!first || !last) {
    throw new Error('EMPTY_TIMELINE_CHANNEL');
  }
  if (timeSec <= first.timeSec) {
    return { left: first, right: first, t: 0 };
  }
  if (timeSec >= last.timeSec) {
    return { left: last, right: last, t: 0 };
  }

  for (let index = 1; index < frames.length; index += 1) {
    const right = frames[index]!;
    if (timeSec <= right.timeSec) {
      const left = frames[index - 1]!;
      const duration = right.timeSec - left.timeSec;
      return {
        left,
        right,
        t: duration === 0 ? 0 : (timeSec - left.timeSec) / duration,
      };
    }
  }
  return { left: last, right: last, t: 0 };
};

const evaluateRoot = (
  frames: readonly RootKeyframe[],
  timeSec: number,
): Pick<RootKeyframe, 'position' | 'rotationYDeg'> => {
  const { left, right, t } = bracket(frames, timeSec);
  return {
    position: lerpVec3(left.position, right.position, t),
    rotationYDeg: lerpAngleDeg(left.rotationYDeg, right.rotationYDeg, t),
  };
};

const evaluateJoint = (
  frames: readonly JointKeyframe[],
  timeSec: number,
): EulerDeg => {
  const { left, right, t } = bracket(frames, timeSec);
  return {
    x: lerpAngleDeg(
      left.localRotationDeg.x,
      right.localRotationDeg.x,
      t,
    ),
    y: lerpAngleDeg(
      left.localRotationDeg.y,
      right.localRotationDeg.y,
      t,
    ),
    z: lerpAngleDeg(
      left.localRotationDeg.z,
      right.localRotationDeg.z,
      t,
    ),
  };
};

const evaluateCamera = (
  frames: readonly CameraKeyframe[],
  timeSec: number,
): Omit<CameraKeyframe, 'timeSec'> => {
  const { left, right, t } = bracket(frames, timeSec);
  return {
    position: lerpVec3(left.position, right.position, t),
    target: lerpVec3(left.target, right.target, t),
    fovDeg: lerp(left.fovDeg, right.fovDeg, t),
  };
};

const resetFromDocument = (compiled: CompiledDirectingScene): void => {
  for (const actorSpec of compiled.document.actors) {
    const actor = compiled.actors.get(actorSpec.id);
    if (!actor) {
      throw new Error(`COMPILED_ACTOR_NOT_FOUND: ${actorSpec.id}`);
    }
    actor.root.position.copyFrom(toVector3(actorSpec.position));
    actor.root.rotation.copyFromFloats(
      0,
      actorSpec.rotationYDeg * DEG_TO_RAD,
      0,
    );

    for (const jointName of JOINT_NAMES) {
      const joint = actor.joints.get(jointName);
      if (!joint) {
        throw new Error(
          `COMPILED_JOINT_NOT_FOUND: ${actorSpec.id}/${jointName}`,
        );
      }
      const pose = actorSpec.pose[jointName] ?? { x: 0, y: 0, z: 0 };
      applyEulerDeg(joint, pose);
    }
  }

  for (const cameraSpec of compiled.document.cameras) {
    const camera = compiled.cameras.get(cameraSpec.id);
    if (!camera) {
      throw new Error(`COMPILED_CAMERA_NOT_FOUND: ${cameraSpec.id}`);
    }
    camera.position.copyFrom(toVector3(cameraSpec.position));
    camera.setTarget(toVector3(cameraSpec.target));
    camera.getViewMatrix(true);
    camera.fov = cameraSpec.fovDeg * DEG_TO_RAD;
    camera.minZ = cameraSpec.nearClip ?? DEFAULT_NEAR_CLIP;
    camera.maxZ = cameraSpec.farClip ?? DEFAULT_FAR_CLIP;
  }
};

export function evaluateAtTime(
  compiled: CompiledDirectingScene,
  timeSec: number,
): EvaluationSelection {
  if (!Number.isFinite(timeSec) || timeSec < 0) {
    throw new Error(`INVALID_EVALUATION_TIME: ${timeSec}`);
  }

  resetFromDocument(compiled);

  for (const actorSpec of compiled.document.actors) {
    const actor = compiled.actors.get(actorSpec.id)!;
    if (actorSpec.rootMotion) {
      const root = evaluateRoot(actorSpec.rootMotion, timeSec);
      actor.root.position.copyFrom(toVector3(root.position));
      actor.root.rotation.y = root.rotationYDeg * DEG_TO_RAD;
    }

    if (actorSpec.jointMotion) {
      const channels = new Map<JointName, JointKeyframe[]>();
      for (const frame of actorSpec.jointMotion) {
        const channel = channels.get(frame.joint) ?? [];
        channel.push(frame);
        channels.set(frame.joint, channel);
      }
      for (const [jointName, frames] of channels) {
        const joint = actor.joints.get(jointName);
        if (!joint) {
          throw new Error(
            `COMPILED_JOINT_NOT_FOUND: ${actorSpec.id}/${jointName}`,
          );
        }
        applyEulerDeg(joint, evaluateJoint(frames, timeSec));
      }
    }
  }

  for (const cameraSpec of compiled.document.cameras) {
    if (!cameraSpec.motion) {
      continue;
    }
    const camera = compiled.cameras.get(cameraSpec.id)!;
    const evaluated = evaluateCamera(cameraSpec.motion, timeSec);
    camera.position.copyFrom(toVector3(evaluated.position));
    camera.setTarget(toVector3(evaluated.target));
    camera.getViewMatrix(true);
    camera.fov = evaluated.fovDeg * DEG_TO_RAD;
  }

  const activeShot = compiled.document.shots.find(
    (shot) => timeSec >= shot.startSec && timeSec <= shot.endSec,
  );
  const fallbackCameraId = compiled.document.cameras[0]?.id ?? null;
  const activeCameraId = activeShot?.cameraId ?? fallbackCameraId;
  const activeCamera = activeCameraId
    ? compiled.cameras.get(activeCameraId)
    : undefined;
  compiled.scene.activeCamera = activeCamera ?? null;

  return {
    activeCameraId,
    activeShotId: activeShot?.id ?? null,
  };
}
