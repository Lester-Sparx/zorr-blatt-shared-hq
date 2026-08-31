import '@babylonjs/loaders/glTF';
import type { AnimationGroup } from '@babylonjs/core/Animations/animationGroup';
import { Color3, Color4 } from '@babylonjs/core/Maths/math.color';
import { StandardMaterial } from '@babylonjs/core/Materials/standardMaterial';
import type { AbstractMesh } from '@babylonjs/core/Meshes/abstractMesh';
import { Mesh } from '@babylonjs/core/Meshes/mesh';
import { TransformNode } from '@babylonjs/core/Meshes/transformNode';
import { SceneLoader } from '@babylonjs/core/Loading/sceneLoader';
import type { Scene } from '@babylonjs/core/scene';
import type { Skeleton } from '@babylonjs/core/Bones/skeleton';

export const ACTION_LOCK = {
  attackerPositionM: [-0.50, 0.00951, 0.05] as const,
  attackerYawDeg: 65,
  dodgerPositionM: [0.50, 0.00951, -0.05] as const,
  dodgerYawDeg: -90,
  bladeLengthM: 1.08,
  bladeScale: 0.34076,
  attackClip: 'Sword_Attack',
  attackPoseFraction: 0.45,
  dodgeClip: 'Roll',
  dodgePoseFraction: 0.55,
  measuredPrototypeClearanceM: 0.0970096418,
  cameraPositionM: [3.10, 1.55, 3.65] as const,
  cameraTargetM: [0.12, 1.02, -0.38] as const,
  cameraFovDeg: 39,
} as const;

const DEG = Math.PI / 180;
const ASSET_ROOT = '/assets/r04/';

const renderMeshes = (meshes: AbstractMesh[]): Mesh[] => meshes.filter(
  (mesh): mesh is Mesh => mesh instanceof Mesh && mesh.getTotalVertices() > 0,
);

const requireSkeleton = (skeletons: Skeleton[], actor: string): Skeleton => {
  const skeleton = skeletons[0];
  if (!skeleton) throw new Error(`R04_${actor.toUpperCase()}_SKELETON_MISSING`);
  return skeleton;
};

const poseGroup = (
  source: AnimationGroup,
  name: string,
  skeleton: Skeleton,
  fraction: number,
): AnimationGroup => {
  const targets = new Map(
    skeleton.bones.map((bone) => [bone.name, bone.getTransformNode() ?? bone]),
  );
  const group = source.clone(name, (oldTarget: { name?: string }) => {
    const target = oldTarget.name ? targets.get(oldTarget.name) : undefined;
    if (!target) throw new Error(`R04_ANIMATION_TARGET_MISSING:${oldTarget.name ?? 'unnamed'}`);
    return target;
  });
  group.start(false, 1, group.from, group.to);
  group.pause();
  group.goToFrame(group.from + (group.to - group.from) * fraction);
  return group;
};

const setupActor = (
  scene: Scene,
  meshes: AbstractMesh[],
  skeleton: Skeleton,
  actor: 'attacker' | 'dodger',
  position: readonly [number, number, number],
  yawDeg: number,
): Mesh[] => {
  const importedRoot = meshes[0];
  if (!importedRoot) throw new Error(`R04_${actor.toUpperCase()}_ROOT_MISSING`);

  const actorRoot = new TransformNode(`action:actor:${actor}:root`, scene);
  actorRoot.position.copyFromFloats(...position);
  actorRoot.rotation.y = yawDeg * DEG;
  importedRoot.parent = actorRoot;

  const surfaces = renderMeshes(meshes);
  if (surfaces.length === 0) throw new Error(`R04_${actor.toUpperCase()}_SURFACE_MISSING`);
  for (const [index, mesh] of surfaces.entries()) {
    mesh.name = `action:actor:${actor}:surface:${index}`;
    mesh.id = mesh.name;
    mesh.isPickable = false;
    mesh.metadata = {
      zorrActor: actor,
      source: 'QUATERNIUS_UBC_CC0',
      sourceSha256: 'a466828c67a4acc9b2413212ce6d9cde235e3aed9b675680c14fd9673858f118',
      skeleton: skeleton.name,
    };
  }
  return surfaces;
};

export type ActionScene = {
  attacker: Mesh[];
  dodger: Mesh[];
  blade: Mesh[];
  attackAnimation: AnimationGroup;
  dodgeAnimation: AnimationGroup;
};

export async function buildBladeDodgeAction(scene: Scene): Promise<ActionScene> {
  scene.clearColor = new Color4(0.965, 0.965, 0.965, 1);
  scene.ambientColor = new Color3(0.48, 0.48, 0.48);
  scene.fogEnabled = false;

  for (const mesh of scene.meshes) {
    if (mesh.name.startsWith('set:') && mesh.name !== 'set:platform') mesh.setEnabled(false);
  }
  scene.getMeshByName('stage:ground')?.setEnabled(false);
  const stageDebugLight = scene.getLightByName('stage:debug-light');
  if (stageDebugLight) stageDebugLight.setEnabled(false);

  const platform = scene.getMeshByName('set:platform');
  if (platform) {
    platform.scaling.y = 0.01;
    platform.position.y = -0.0009;
    const floor = new StandardMaterial('action:material:white-floor', scene);
    floor.diffuseColor = new Color3(0.96, 0.96, 0.96);
    floor.emissiveColor = new Color3(0.96, 0.96, 0.96);
    floor.specularColor = Color3.Black();
    floor.disableLighting = true;
    platform.material = floor;
  }
  for (const lightName of ['set:light:key', 'set:light:portal', 'set:light:fill']) {
    const light = scene.getLightByName(lightName);
    if (light) {
      light.diffuse = Color3.White();
      light.specular = Color3.Black();
    }
  }

  const attackerImport = await SceneLoader.ImportMeshAsync('', ASSET_ROOT, 'quaternius-superhero-male.glb', scene);
  const attackerSkeleton = requireSkeleton(attackerImport.skeletons, 'attacker');
  const attacker = setupActor(scene, attackerImport.meshes, attackerSkeleton, 'attacker', ACTION_LOCK.attackerPositionM, ACTION_LOCK.attackerYawDeg);

  const dodgerImport = await SceneLoader.ImportMeshAsync('', ASSET_ROOT, 'quaternius-superhero-male.glb', scene);
  const dodgerSkeleton = requireSkeleton(dodgerImport.skeletons, 'dodger');
  const dodger = setupActor(scene, dodgerImport.meshes, dodgerSkeleton, 'dodger', ACTION_LOCK.dodgerPositionM, ACTION_LOCK.dodgerYawDeg);

  const motionImport = await SceneLoader.ImportMeshAsync('', ASSET_ROOT, 'quaternius-ual.glb', scene);
  for (const mesh of motionImport.meshes) mesh.setEnabled(false);
  const attackSource = motionImport.animationGroups.find((group) => group.name === ACTION_LOCK.attackClip);
  const dodgeSource = motionImport.animationGroups.find((group) => group.name === ACTION_LOCK.dodgeClip);
  if (!attackSource) throw new Error(`R04_MOTION_MISSING:${ACTION_LOCK.attackClip}`);
  if (!dodgeSource) throw new Error(`R04_MOTION_MISSING:${ACTION_LOCK.dodgeClip}`);

  const attackAnimation = poseGroup(attackSource, 'action:animation:attacker:sword-attack', attackerSkeleton, ACTION_LOCK.attackPoseFraction);
  const dodgeAnimation = poseGroup(dodgeSource, 'action:animation:dodger:roll', dodgerSkeleton, ACTION_LOCK.dodgePoseFraction);

  const swordImport = await SceneLoader.ImportMeshAsync('', ASSET_ROOT, 'sword.glb', scene);
  const swordRoot = swordImport.meshes[0];
  const hand = attackerSkeleton.bones.find((bone) => bone.name === 'hand_r')?.getTransformNode();
  if (!swordRoot) throw new Error('R04_SWORD_ROOT_MISSING');
  if (!hand) throw new Error('R04_HAND_R_NODE_MISSING');

  const socket = new TransformNode('action:blade:socket', scene);
  socket.parent = hand;
  socket.position.copyFromFloats(0, 0, 0);
  socket.rotation.x = -Math.PI / 2;
  socket.scaling.copyFromFloats(ACTION_LOCK.bladeScale, ACTION_LOCK.bladeScale, ACTION_LOCK.bladeScale);
  swordRoot.parent = socket;

  const blade = renderMeshes(swordImport.meshes);
  for (const mesh of blade) {
    if (mesh.material) mesh.material.alpha = 1;
    mesh.name = 'action:blade';
    mesh.id = mesh.name;
    mesh.isPickable = false;
    mesh.metadata = {
      source: 'QUATERNIUS_ANIMATED_KNIGHT_PACK_CC0',
      sourceSha256: '62add428c985df2ec32f7e516ab685a327cca886926446f798fe92d6ca180d3a',
      attachedTo: 'hand_r',
    };
  }

  scene.metadata = {
    ...scene.metadata,
    zorrActionScene: {
      action: 'BLADE_ATTACK_DODGE',
      revision: 'R04',
      coordinateSystem: 'BABYLON_Y_UP_METERS',
      locks: ACTION_LOCK,
      actorSurface: 'QUATERNIUS_UBC_CC0_SKINNED_GLB',
      animationLibrary: 'QUATERNIUS_UAL_CC0',
      weapon: 'QUATERNIUS_ANIMATED_KNIGHT_SWORD_CC0',
      weaponAttachment: 'hand_r',
      drawnImitation: false,
      vertexWarp: false,
    },
    zorrOpenSourcePolicy: {
      externalArtAssets: [
        'QUATERNIUS_UBC_CC0',
        'QUATERNIUS_UAL_CC0',
        'QUATERNIUS_ANIMATED_KNIGHT_SWORD_CC0',
      ],
      geometry: 'PINNED_SKINNED_GLTF_PLUS_EXISTING_BABYLON_SET',
      materials: 'SOURCE_GLTF_PLUS_WHITE_STAGE_STANDARD_MATERIAL',
      remoteInference: false,
    },
  };

  return { attacker, dodger, blade, attackAnimation, dodgeAnimation };
}
