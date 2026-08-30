import { Engine } from '@babylonjs/core/Engines/engine';
import type { EulerDeg, JointName, Vec3 } from './contract';
import { JOINT_NAMES } from './contract';
import type { CompiledDirectingScene } from './compiler';
import { evaluateAtTime } from './timeline';

const RAD_TO_DEG = 180 / Math.PI;
const roundEvidence = (value: number): number =>
  Number(value.toFixed(6));

const evidenceVec3 = (value: {
  x: number;
  y: number;
  z: number;
}): Vec3 => ({
  x: roundEvidence(value.x),
  y: roundEvidence(value.y),
  z: roundEvidence(value.z),
});

const evidenceEulerDeg = (value: {
  x: number;
  y: number;
  z: number;
}): EulerDeg => ({
  x: roundEvidence(value.x * RAD_TO_DEG),
  y: roundEvidence(value.y * RAD_TO_DEG),
  z: roundEvidence(value.z * RAD_TO_DEG),
});

export type EvaluatedActorSnapshot = {
  id: string;
  position: Vec3;
  rotationYDeg: number;
  joints: Record<JointName, EulerDeg>;
};

export type EvaluatedCameraSnapshot = {
  id: string;
  position: Vec3;
  target: Vec3;
  fovDeg: number;
  nearClip: number;
  farClip: number;
};

export type EvaluatedSnapshot = {
  sceneId: string;
  schemaVersion: 'babylon-directing-v1';
  timeSec: number;
  actors: EvaluatedActorSnapshot[];
  activeCamera: EvaluatedCameraSnapshot | null;
  activeShotId: string | null;
  capture: {
    shotId?: string;
    cameraId?: string;
    timeSec: number;
    widthPx: number;
    heightPx: number;
    output: string;
  };
  runtime: {
    babylonVersion: string;
  };
};

export function createEvaluatedSnapshot(
  compiled: CompiledDirectingScene,
  timeSec: number,
): EvaluatedSnapshot {
  const selection = evaluateAtTime(compiled, timeSec);

  const actors = compiled.document.actors.map((actorSpec) => {
    const actor = compiled.actors.get(actorSpec.id);
    if (!actor) {
      throw new Error(`COMPILED_ACTOR_NOT_FOUND: ${actorSpec.id}`);
    }

    const joints = Object.fromEntries(
      JOINT_NAMES.map((jointName) => {
        const joint = actor.joints.get(jointName);
        if (!joint) {
          throw new Error(
            `COMPILED_JOINT_NOT_FOUND: ${actorSpec.id}/${jointName}`,
          );
        }
        return [jointName, evidenceEulerDeg(joint.rotation)];
      }),
    ) as Record<JointName, EulerDeg>;

    return {
      id: actorSpec.id,
      position: evidenceVec3(actor.root.position),
      rotationYDeg: roundEvidence(actor.root.rotation.y * RAD_TO_DEG),
      joints,
    };
  });

  const activeCamera = selection.activeCameraId
    ? compiled.cameras.get(selection.activeCameraId)
    : undefined;

  return {
    sceneId: compiled.document.sceneId,
    schemaVersion: compiled.document.schemaVersion,
    timeSec: roundEvidence(timeSec),
    actors,
    activeCamera: activeCamera
      ? {
        id: selection.activeCameraId!,
        position: evidenceVec3(activeCamera.position),
        target: evidenceVec3(activeCamera.getTarget()),
        fovDeg: roundEvidence(activeCamera.fov * RAD_TO_DEG),
        nearClip: roundEvidence(activeCamera.minZ),
        farClip: roundEvidence(activeCamera.maxZ),
      }
      : null,
    activeShotId: selection.activeShotId,
    capture: {
      ...(compiled.document.capture.shotId
        ? { shotId: compiled.document.capture.shotId }
        : {}),
      ...(compiled.document.capture.cameraId
        ? { cameraId: compiled.document.capture.cameraId }
        : {}),
      timeSec: compiled.document.capture.timeSec,
      widthPx: compiled.document.capture.widthPx,
      heightPx: compiled.document.capture.heightPx,
      output: compiled.document.capture.output,
    },
    runtime: {
      babylonVersion: Engine.Version,
    },
  };
}
