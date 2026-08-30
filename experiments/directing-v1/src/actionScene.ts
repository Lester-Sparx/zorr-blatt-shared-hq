import '@babylonjs/loaders/glTF';
import { Color3 } from '@babylonjs/core/Maths/math.color';
import { Quaternion, Vector3 } from '@babylonjs/core/Maths/math.vector';
import { StandardMaterial } from '@babylonjs/core/Materials/standardMaterial';
import { VertexBuffer } from '@babylonjs/core/Buffers/buffer';
import { CreateBox } from '@babylonjs/core/Meshes/Builders/boxBuilder';
import type { AbstractMesh } from '@babylonjs/core/Meshes/abstractMesh';
import type { Mesh } from '@babylonjs/core/Meshes/mesh';
import { SceneLoader } from '@babylonjs/core/Loading/sceneLoader';
import type { Scene } from '@babylonjs/core/scene';

export const ACTION_LOCK = {
  attackerPositionM: [-0.62, 0, 0.05] as const,
  attackerYawDeg: -8,
  attackerLeanM: 0.16,
  dodgerPositionM: [0.62, 0, -0.05] as const,
  dodgerYawDeg: 15,
  dodgerLeanM: 0.34,
  bladeLengthM: 1.08,
  measuredPrototypeClearanceM: 0.0970096418,
  cameraPositionM: [3.10, 1.55, 3.65] as const,
  cameraTargetM: [0.12, 1.02, -0.38] as const,
  cameraFovDeg: 39,
} as const;

const DEG = Math.PI / 180;

const whiteMaterial = (scene: Scene): StandardMaterial => {
  const material = new StandardMaterial('action:material:body-white', scene);
  material.diffuseColor = new Color3(0.72, 0.74, 0.78);
  material.specularColor = new Color3(0.12, 0.12, 0.12);
  return material;
};

const bladeMaterial = (scene: Scene): StandardMaterial => {
  const material = new StandardMaterial('action:material:blade', scene);
  material.diffuseColor = new Color3(0.58, 0.62, 0.68);
  material.emissiveColor = new Color3(0.035, 0.045, 0.06);
  material.specularColor = new Color3(0.9, 0.9, 0.9);
  return material;
};

const renderMeshes = (meshes: AbstractMesh[]): Mesh[] => meshes.filter(
  (mesh): mesh is Mesh => mesh.getTotalVertices() > 0 && 'makeGeometryUnique' in mesh,
);

const normalizeBody = (
  meshes: Mesh[],
  name: string,
  position: readonly [number, number, number],
  yawDeg: number,
  upperBodyOffsetM: number,
): void => {
  for (const [index, mesh] of meshes.entries()) {
    mesh.makeGeometryUnique();
    const positions = mesh.getVerticesData(VertexBuffer.PositionKind);
    if (positions) {
      let minY = Number.POSITIVE_INFINITY;
      let maxY = Number.NEGATIVE_INFINITY;
      for (let vertex = 1; vertex < positions.length; vertex += 3) {
        minY = Math.min(minY, positions[vertex] ?? minY);
        maxY = Math.max(maxY, positions[vertex] ?? maxY);
      }
      const spanY = maxY - minY;
      for (let vertex = 0; vertex < positions.length; vertex += 3) {
        const y = positions[vertex + 1] ?? minY;
        const normalized = spanY > 0 ? (y - minY) / spanY : 0;
        const t = Math.max(0, Math.min(1, (normalized - 0.42) / 0.48));
        const smooth = t * t * (3 - 2 * t);
        positions[vertex] = (positions[vertex] ?? 0) + upperBodyOffsetM * 10 * smooth;
      }
      mesh.updateVerticesData(VertexBuffer.PositionKind, positions, true, false);
      mesh.refreshBoundingInfo({ applySkeleton: false });
    }
    mesh.name = `action:actor:${name}:surface:${index}`;
    mesh.id = mesh.name;
    mesh.scaling.copyFromFloats(0.1, 0.1, 0.1);
    mesh.rotationQuaternion = null;
    mesh.rotation.y = yawDeg * DEG;
    mesh.position.copyFromFloats(...position);
    mesh.material = whiteMaterial(mesh.getScene());
    mesh.isPickable = false;
    mesh.metadata = {
      zorrActor: name,
      source: 'OXIHUMAN_B0_DERIVED_GLB',
      sourceSha256: '626be02ae16ddf2bfd8760633761489a3c24f5b35d1e5b3f4a0c9a602cbffaf0',
      upperBodyOffsetM,
    };
  }
};

const orientBetween = (mesh: Mesh, start: Vector3, end: Vector3): void => {
  const direction = end.subtract(start);
  mesh.position.copyFrom(start.add(end).scale(0.5));
  mesh.scaling.z = direction.length();
  mesh.rotationQuaternion = Quaternion.FromLookDirectionLH(
    direction.normalize(),
    Vector3.Up(),
  );
};

export type ActionScene = {
  attacker: Mesh[];
  dodger: Mesh[];
  blade: Mesh;
  grip: Mesh;
  crossguard: Mesh;
};

export async function buildBladeDodgeAction(scene: Scene): Promise<ActionScene> {
  const imported = await SceneLoader.ImportMeshAsync(
    '',
    '/',
    'oxihuman-b0-body.glb',
    scene,
  );
  const attacker = renderMeshes(imported.meshes);
  if (attacker.length === 0) {
    throw new Error('OXIHUMAN_BODY_HAS_NO_RENDER_MESH');
  }
  const dodger = attacker.map((mesh) => mesh.clone(`${mesh.name}:dodger`));

  normalizeBody(
    attacker,
    'attacker',
    ACTION_LOCK.attackerPositionM,
    ACTION_LOCK.attackerYawDeg,
    ACTION_LOCK.attackerLeanM,
  );
  normalizeBody(
    dodger,
    'dodger',
    ACTION_LOCK.dodgerPositionM,
    ACTION_LOCK.dodgerYawDeg,
    ACTION_LOCK.dodgerLeanM,
  );

  const bladeStart = new Vector3(-0.24, 1.28, -0.02);
  const bladeEnd = new Vector3(0.72, 1.54, -0.43);
  const blade = CreateBox(
    'action:blade',
    { width: 0.035, height: 0.012, depth: 1 },
    scene,
  );
  blade.material = bladeMaterial(scene);
  orientBetween(blade, bladeStart, bladeEnd);

  const gripStart = bladeStart.add(bladeStart.subtract(bladeEnd).normalize().scale(0.22));
  const grip = CreateBox(
    'action:blade:grip',
    { width: 0.045, height: 0.045, depth: 1 },
    scene,
  );
  grip.material = bladeMaterial(scene);
  orientBetween(grip, gripStart, bladeStart);

  const crossguard = CreateBox(
    'action:blade:crossguard',
    { width: 0.23, height: 0.025, depth: 0.035 },
    scene,
  );
  crossguard.position.copyFrom(bladeStart);
  crossguard.rotation.copyFrom(blade.rotation);
  crossguard.material = bladeMaterial(scene);

  scene.metadata = {
    ...scene.metadata,
    zorrActionScene: {
      action: 'BLADE_ATTACK_DODGE',
      coordinateSystem: 'BABYLON_Y_UP_METERS',
      locks: ACTION_LOCK,
      actorSurface: 'REAL_OXIHUMAN_DERIVED_3D_MESH',
      drawnImitation: false,
      clothResearchStatus: 'NOT_APPLIED_R03',
    },
  };

  return { attacker, dodger, blade, grip, crossguard };
}
