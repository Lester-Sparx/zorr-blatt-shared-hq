import type { Light } from '@babylonjs/core/Lights/light';
import { PointLight } from '@babylonjs/core/Lights/pointLight';
import { SpotLight } from '@babylonjs/core/Lights/spotLight';
import { Color3, Color4 } from '@babylonjs/core/Maths/math.color';
import { Vector3 } from '@babylonjs/core/Maths/math.vector';
import { StandardMaterial } from '@babylonjs/core/Materials/standardMaterial';
import { CreateBox } from '@babylonjs/core/Meshes/Builders/boxBuilder';
import type { Mesh } from '@babylonjs/core/Meshes/mesh';
import { Scene } from '@babylonjs/core/scene';

export const CINEMATIC_SET_MESH_NAMES = [
  'set:platform',
  'set:threshold',
  'set:portal:left',
  'set:portal:right',
  'set:portal:top',
  'set:monolith:left',
  'set:monolith:right',
  'set:horizon-slab',
  'set:accent:portal-left',
  'set:accent:portal-right',
  'set:accent:floor-line',
] as const;

export const CINEMATIC_SET_LIGHT_NAMES = [
  'set:light:key',
  'set:light:portal',
  'set:light:fill',
] as const;

export type CinematicSet = {
  meshes: Mesh[];
  lights: Light[];
};

type MaterialSpec = {
  diffuse: Color3;
  emissive?: Color3;
  disableLighting?: boolean;
};

const createMaterial = (
  scene: Scene,
  name: string,
  spec: MaterialSpec,
): StandardMaterial => {
  const material = new StandardMaterial(name, scene);
  material.diffuseColor = spec.diffuse;
  material.emissiveColor = spec.emissive ?? Color3.Black();
  material.specularColor = Color3.Black();
  material.disableLighting = spec.disableLighting ?? false;
  return material;
};

const createSetBox = (
  scene: Scene,
  name: typeof CINEMATIC_SET_MESH_NAMES[number],
  dimensions: { width: number; height: number; depth: number },
  position: { x: number; y: number; z: number },
  material: StandardMaterial,
  rotationY = 0,
): Mesh => {
  const mesh = CreateBox(name, dimensions, scene);
  mesh.position.copyFromFloats(position.x, position.y, position.z);
  mesh.rotation.y = rotationY;
  mesh.material = material;
  mesh.isPickable = false;
  return mesh;
};

export function buildCinematicSet(scene: Scene): CinematicSet {
  scene.clearColor = new Color4(0.012, 0.014, 0.022, 1);
  scene.ambientColor = new Color3(0.02, 0.022, 0.034);
  scene.fogEnabled = true;
  scene.fogMode = Scene.FOGMODE_LINEAR;
  scene.fogStart = 7.5;
  scene.fogEnd = 25;
  scene.fogColor = new Color3(0.025, 0.028, 0.045);

  const originalStageLight = scene.getLightByName('stage:debug-light');
  if (originalStageLight) {
    originalStageLight.intensity = 0.22;
  }

  const graphite = createMaterial(scene, 'set:material:graphite', {
    diffuse: new Color3(0.055, 0.06, 0.078),
  });
  const thresholdMaterial = createMaterial(scene, 'set:material:threshold', {
    diffuse: new Color3(0.12, 0.115, 0.14),
  });
  const stone = createMaterial(scene, 'set:material:stone', {
    diffuse: new Color3(0.19, 0.2, 0.23),
  });
  const distantStone = createMaterial(scene, 'set:material:distant-stone', {
    diffuse: new Color3(0.075, 0.08, 0.11),
  });
  const magenta = createMaterial(scene, 'set:material:magenta-emissive', {
    diffuse: Color3.Black(),
    emissive: new Color3(0.72, 0.055, 0.42),
    disableLighting: true,
  });
  const cyan = createMaterial(scene, 'set:material:cyan-emissive', {
    diffuse: Color3.Black(),
    emissive: new Color3(0.02, 0.38, 0.52),
    disableLighting: true,
  });

  const meshes: Mesh[] = [
    createSetBox(
      scene,
      'set:platform',
      { width: 10.5, height: 0.18, depth: 7.2 },
      { x: 0, y: -0.09, z: 1.55 },
      graphite,
    ),
    createSetBox(
      scene,
      'set:threshold',
      { width: 4.7, height: 0.13, depth: 1.15 },
      { x: 0.35, y: 0.065, z: 2.75 },
      thresholdMaterial,
      -0.08,
    ),
    createSetBox(
      scene,
      'set:portal:left',
      { width: 0.5, height: 5.4, depth: 0.62 },
      { x: -2.85, y: 2.7, z: 5.45 },
      stone,
    ),
    createSetBox(
      scene,
      'set:portal:right',
      { width: 0.5, height: 5.4, depth: 0.62 },
      { x: 2.85, y: 2.7, z: 5.45 },
      stone,
    ),
    createSetBox(
      scene,
      'set:portal:top',
      { width: 6.2, height: 0.5, depth: 0.62 },
      { x: 0, y: 5.15, z: 5.45 },
      stone,
    ),
    createSetBox(
      scene,
      'set:monolith:left',
      { width: 1.25, height: 4.6, depth: 1.15 },
      { x: -4.75, y: 2.3, z: 3.6 },
      distantStone,
      0.14,
    ),
    createSetBox(
      scene,
      'set:monolith:right',
      { width: 1.0, height: 3.65, depth: 1.0 },
      { x: 4.55, y: 1.825, z: 4.3 },
      distantStone,
      -0.2,
    ),
    createSetBox(
      scene,
      'set:horizon-slab',
      { width: 18, height: 5.6, depth: 0.38 },
      { x: 0, y: 2.55, z: 10.2 },
      distantStone,
    ),
    createSetBox(
      scene,
      'set:accent:portal-left',
      { width: 0.065, height: 3.95, depth: 0.08 },
      { x: -2.56, y: 2.75, z: 5.1 },
      magenta,
    ),
    createSetBox(
      scene,
      'set:accent:portal-right',
      { width: 0.065, height: 3.95, depth: 0.08 },
      { x: 2.56, y: 2.75, z: 5.1 },
      magenta,
    ),
    createSetBox(
      scene,
      'set:accent:floor-line',
      { width: 0.045, height: 0.018, depth: 7.8 },
      { x: 0.18, y: 0.02, z: 1.55 },
      cyan,
      -0.055,
    ),
  ];

  const keyPosition = new Vector3(-4.8, 6.4, -3.8);
  const keyTarget = new Vector3(-0.3, 1.1, 1.3);
  const key = new SpotLight(
    'set:light:key',
    keyPosition,
    keyTarget.subtract(keyPosition).normalize(),
    0.95,
    2,
    scene,
  );
  key.diffuse = new Color3(1.0, 0.72, 0.48);
  key.specular = Color3.Black();
  key.intensity = 5.2;
  key.range = 18;

  const portal = new PointLight(
    'set:light:portal',
    new Vector3(0, 3.0, 5.15),
    scene,
  );
  portal.diffuse = new Color3(0.95, 0.08, 0.55);
  portal.specular = Color3.Black();
  portal.intensity = 4.6;
  portal.range = 10;

  const fill = new PointLight(
    'set:light:fill',
    new Vector3(4.2, 2.3, -1.6),
    scene,
  );
  fill.diffuse = new Color3(0.08, 0.52, 0.7);
  fill.specular = Color3.Black();
  fill.intensity = 1.7;
  fill.range = 11;

  scene.metadata = {
    ...scene.metadata,
    zorrCinematicScene: {
      sceneId: 'ZB-CINEMATIC-SCENE-R01',
      sceneVersion: 'R01',
      authority: 'PROTOTYPE_NON_CANON',
      designIntent: 'METAPHYSICAL_DRIFT_GATE',
    },
    zorrOpenSourcePolicy: {
      externalArtAssets: [],
      geometry: 'PROCEDURAL_BABYLON_PRIMITIVES',
      materials: 'CODE_AUTHORED_STANDARD_MATERIALS',
      remoteInference: false,
    },
  };

  return { meshes, lights: [key, portal, fill] };
}
