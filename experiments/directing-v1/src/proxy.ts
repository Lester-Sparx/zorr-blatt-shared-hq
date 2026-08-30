import { Color3 } from '@babylonjs/core/Maths/math.color';
import { Vector3 } from '@babylonjs/core/Maths/math.vector';
import { StandardMaterial } from '@babylonjs/core/Materials/standardMaterial';
import { CreateBox } from '@babylonjs/core/Meshes/Builders/boxBuilder';
import { CreateCapsule } from '@babylonjs/core/Meshes/Builders/capsuleBuilder';
import { CreateSphere } from '@babylonjs/core/Meshes/Builders/sphereBuilder';
import type { Mesh } from '@babylonjs/core/Meshes/mesh';
import { TransformNode } from '@babylonjs/core/Meshes/transformNode';
import type { Scene } from '@babylonjs/core/scene';
import {
  JOINT_NAMES,
  type ActorSpec,
  type EulerDeg,
  type JointName,
  type Vec3,
} from './contract';

const REFERENCE_HEIGHT_M = 1.8;
const DEG_TO_RAD = Math.PI / 180;

export type CompiledActor = {
  spec: ActorSpec;
  root: TransformNode;
  joints: Map<JointName, TransformNode>;
  meshes: Mesh[];
};

const toVector3 = ({ x, y, z }: Vec3): Vector3 => new Vector3(x, y, z);

const applyEulerDeg = (node: TransformNode, value: EulerDeg): void => {
  node.rotation.copyFromFloats(
    value.x * DEG_TO_RAD,
    value.y * DEG_TO_RAD,
    value.z * DEG_TO_RAD,
  );
};

const debugColorForId = (id: string): Color3 => {
  let hash = 2166136261;
  for (const character of id) {
    hash ^= character.charCodeAt(0);
    hash = Math.imul(hash, 16777619);
  }
  const red = 0.38 + ((hash >>> 0) & 0x3f) / 512;
  const green = 0.42 + ((hash >>> 8) & 0x3f) / 512;
  const blue = 0.48 + ((hash >>> 16) & 0x3f) / 512;
  return new Color3(red, green, blue);
};

const createDebugMaterial = (
  scene: Scene,
  actorId: string,
): StandardMaterial => {
  const material = new StandardMaterial(`actor:${actorId}:debug-material`, scene);
  const color = debugColorForId(actorId);
  material.diffuseColor = color;
  material.emissiveColor = color.scale(0.08);
  material.specularColor = Color3.Black();
  return material;
};

const addJoint = (
  scene: Scene,
  actorId: string,
  joints: Map<JointName, TransformNode>,
  name: JointName,
  parent: TransformNode,
  position: Vec3,
): TransformNode => {
  const joint = new TransformNode(`actor:${actorId}:joint:${name}`, scene);
  joint.parent = parent;
  joint.position.copyFrom(toVector3(position));
  joints.set(name, joint);
  return joint;
};

const attachMesh = (
  mesh: Mesh,
  parent: TransformNode,
  material: StandardMaterial,
  meshes: Mesh[],
  position: Vec3 = { x: 0, y: 0, z: 0 },
  rotation: Vec3 = { x: 0, y: 0, z: 0 },
): void => {
  mesh.parent = parent;
  mesh.position.copyFrom(toVector3(position));
  mesh.rotation.copyFrom(toVector3(rotation));
  mesh.material = material;
  mesh.isPickable = false;
  meshes.push(mesh);
};

export function createHumanoidProxy(
  scene: Scene,
  actor: ActorSpec,
): CompiledActor {
  const root = new TransformNode(`actor:${actor.id}:root`, scene);
  root.position.copyFrom(toVector3(actor.position));
  root.rotation.y = actor.rotationYDeg * DEG_TO_RAD;
  const scale = actor.heightM / REFERENCE_HEIGHT_M;
  root.scaling.copyFromFloats(scale, scale, scale);

  const joints = new Map<JointName, TransformNode>();
  const pelvis = addJoint(
    scene,
    actor.id,
    joints,
    'pelvis',
    root,
    { x: 0, y: 0.94, z: 0 },
  );
  const spine = addJoint(
    scene,
    actor.id,
    joints,
    'spine',
    pelvis,
    { x: 0, y: 0.12, z: 0 },
  );
  const chest = addJoint(
    scene,
    actor.id,
    joints,
    'chest',
    spine,
    { x: 0, y: 0.18, z: 0 },
  );
  const neck = addJoint(
    scene,
    actor.id,
    joints,
    'neck',
    chest,
    { x: 0, y: 0.22, z: 0 },
  );
  const head = addJoint(
    scene,
    actor.id,
    joints,
    'head',
    neck,
    { x: 0, y: 0.12, z: 0 },
  );

  const shoulderL = addJoint(
    scene,
    actor.id,
    joints,
    'shoulderL',
    chest,
    { x: -0.23, y: 0.1, z: 0 },
  );
  const shoulderR = addJoint(
    scene,
    actor.id,
    joints,
    'shoulderR',
    chest,
    { x: 0.23, y: 0.1, z: 0 },
  );
  const upperArmL = addJoint(
    scene,
    actor.id,
    joints,
    'upperArmL',
    shoulderL,
    { x: 0, y: 0, z: 0 },
  );
  const upperArmR = addJoint(
    scene,
    actor.id,
    joints,
    'upperArmR',
    shoulderR,
    { x: 0, y: 0, z: 0 },
  );
  const forearmL = addJoint(
    scene,
    actor.id,
    joints,
    'forearmL',
    upperArmL,
    { x: -0.28, y: 0, z: 0 },
  );
  const forearmR = addJoint(
    scene,
    actor.id,
    joints,
    'forearmR',
    upperArmR,
    { x: 0.28, y: 0, z: 0 },
  );
  const handL = addJoint(
    scene,
    actor.id,
    joints,
    'handL',
    forearmL,
    { x: -0.25, y: 0, z: 0 },
  );
  const handR = addJoint(
    scene,
    actor.id,
    joints,
    'handR',
    forearmR,
    { x: 0.25, y: 0, z: 0 },
  );

  const thighL = addJoint(
    scene,
    actor.id,
    joints,
    'thighL',
    pelvis,
    { x: -0.11, y: -0.1, z: 0 },
  );
  const thighR = addJoint(
    scene,
    actor.id,
    joints,
    'thighR',
    pelvis,
    { x: 0.11, y: -0.1, z: 0 },
  );
  const shinL = addJoint(
    scene,
    actor.id,
    joints,
    'shinL',
    thighL,
    { x: 0, y: -0.43, z: 0 },
  );
  const shinR = addJoint(
    scene,
    actor.id,
    joints,
    'shinR',
    thighR,
    { x: 0, y: -0.43, z: 0 },
  );
  const footL = addJoint(
    scene,
    actor.id,
    joints,
    'footL',
    shinL,
    { x: 0, y: -0.41, z: 0 },
  );
  const footR = addJoint(
    scene,
    actor.id,
    joints,
    'footR',
    shinR,
    { x: 0, y: -0.41, z: 0 },
  );

  if (joints.size !== JOINT_NAMES.length) {
    throw new Error(
      `PROXY_JOINT_COUNT_MISMATCH: expected ${JOINT_NAMES.length}, got ${joints.size}`,
    );
  }

  const material = createDebugMaterial(scene, actor.id);
  const meshes: Mesh[] = [];

  attachMesh(
    CreateBox(
      `actor:${actor.id}:mesh:pelvis`,
      { width: 0.3, height: 0.2, depth: 0.22 },
      scene,
    ),
    pelvis,
    material,
    meshes,
    { x: 0, y: -0.02, z: 0 },
  );
  attachMesh(
    CreateBox(
      `actor:${actor.id}:mesh:torso`,
      { width: 0.44, height: 0.38, depth: 0.24 },
      scene,
    ),
    chest,
    material,
    meshes,
    { x: 0, y: -0.09, z: 0 },
  );
  attachMesh(
    CreateCapsule(
      `actor:${actor.id}:mesh:neck`,
      { height: 0.15, radius: 0.055, tessellation: 8, subdivisions: 1 },
      scene,
    ),
    neck,
    material,
    meshes,
    { x: 0, y: 0.02, z: 0 },
  );
  attachMesh(
    CreateSphere(
      `actor:${actor.id}:mesh:head`,
      { diameter: 0.25, segments: 12 },
      scene,
    ),
    head,
    material,
    meshes,
    { x: 0, y: 0.09, z: 0 },
  );

  const upperArmLength = 0.28;
  const forearmLength = 0.25;
  const armRadius = 0.045;
  for (const side of [-1, 1] as const) {
    const suffix = side < 0 ? 'L' : 'R';
    const upperArm = side < 0 ? upperArmL : upperArmR;
    const forearm = side < 0 ? forearmL : forearmR;
    const hand = side < 0 ? handL : handR;

    attachMesh(
      CreateCapsule(
        `actor:${actor.id}:mesh:upperArm${suffix}`,
        {
          height: upperArmLength,
          radius: armRadius,
          tessellation: 8,
          subdivisions: 1,
        },
        scene,
      ),
      upperArm,
      material,
      meshes,
      { x: side * upperArmLength * 0.5, y: 0, z: 0 },
      { x: 0, y: 0, z: side * Math.PI * 0.5 },
    );
    attachMesh(
      CreateCapsule(
        `actor:${actor.id}:mesh:forearm${suffix}`,
        {
          height: forearmLength,
          radius: armRadius * 0.9,
          tessellation: 8,
          subdivisions: 1,
        },
        scene,
      ),
      forearm,
      material,
      meshes,
      { x: side * forearmLength * 0.5, y: 0, z: 0 },
      { x: 0, y: 0, z: side * Math.PI * 0.5 },
    );
    attachMesh(
      CreateBox(
        `actor:${actor.id}:mesh:hand${suffix}`,
        { width: 0.12, height: 0.08, depth: 0.1 },
        scene,
      ),
      hand,
      material,
      meshes,
      { x: side * 0.06, y: 0, z: 0 },
    );
  }

  const thighLength = 0.43;
  const shinLength = 0.41;
  const legRadius = 0.06;
  for (const side of [-1, 1] as const) {
    const suffix = side < 0 ? 'L' : 'R';
    const thigh = side < 0 ? thighL : thighR;
    const shin = side < 0 ? shinL : shinR;
    const foot = side < 0 ? footL : footR;

    attachMesh(
      CreateCapsule(
        `actor:${actor.id}:mesh:thigh${suffix}`,
        {
          height: thighLength,
          radius: legRadius,
          tessellation: 8,
          subdivisions: 1,
        },
        scene,
      ),
      thigh,
      material,
      meshes,
      { x: 0, y: -thighLength * 0.5, z: 0 },
    );
    attachMesh(
      CreateCapsule(
        `actor:${actor.id}:mesh:shin${suffix}`,
        {
          height: shinLength,
          radius: legRadius * 0.85,
          tessellation: 8,
          subdivisions: 1,
        },
        scene,
      ),
      shin,
      material,
      meshes,
      { x: 0, y: -shinLength * 0.5, z: 0 },
    );
    attachMesh(
      CreateBox(
        `actor:${actor.id}:mesh:foot${suffix}`,
        { width: 0.13, height: 0.09, depth: 0.26 },
        scene,
      ),
      foot,
      material,
      meshes,
      { x: 0, y: -0.045, z: 0.07 },
    );
  }

  for (const jointName of JOINT_NAMES) {
    const joint = joints.get(jointName);
    if (!joint) {
      throw new Error(`PROXY_JOINT_MISSING: ${jointName}`);
    }
    const pose = actor.pose[jointName];
    if (pose) {
      applyEulerDeg(joint, pose);
    }
  }

  return { spec: actor, root, joints, meshes };
}
