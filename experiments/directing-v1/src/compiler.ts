import type { AbstractEngine } from '@babylonjs/core/Engines/abstractEngine';
import { FreeCamera } from '@babylonjs/core/Cameras/freeCamera';
import { HemisphericLight } from '@babylonjs/core/Lights/hemisphericLight';
import { Color3, Color4 } from '@babylonjs/core/Maths/math.color';
import { Vector3 } from '@babylonjs/core/Maths/math.vector';
import { StandardMaterial } from '@babylonjs/core/Materials/standardMaterial';
import { CreateGround } from '@babylonjs/core/Meshes/Builders/groundBuilder';
import { Scene } from '@babylonjs/core/scene';
import type { SceneDocument, ShotSpec, Vec3 } from './contract';
import { createHumanoidProxy, type CompiledActor } from './proxy';

const DEG_TO_RAD = Math.PI / 180;
export const DEFAULT_NEAR_CLIP = 0.05;
export const DEFAULT_FAR_CLIP = 100;

export type CompiledDirectingScene = {
  engine: AbstractEngine;
  scene: Scene;
  document: SceneDocument;
  actors: Map<string, CompiledActor>;
  cameras: Map<string, FreeCamera>;
  shots: Map<string, ShotSpec>;
};

const toVector3 = ({ x, y, z }: Vec3): Vector3 => new Vector3(x, y, z);

export function compileDirectingScene(
  engine: AbstractEngine,
  document: SceneDocument,
): CompiledDirectingScene {
  const scene = new Scene(engine);
  scene.clearColor = new Color4(0.035, 0.04, 0.055, 1);

  const ground = CreateGround(
    'stage:ground',
    { width: document.stage.width, height: document.stage.depth, subdivisions: 1 },
    scene,
  );
  ground.position.y = document.stage.groundY;
  ground.isPickable = false;

  const groundMaterial = new StandardMaterial('stage:debug-material', scene);
  groundMaterial.diffuseColor = new Color3(0.16, 0.17, 0.2);
  groundMaterial.specularColor = Color3.Black();
  ground.material = groundMaterial;

  const light = new HemisphericLight(
    'stage:debug-light',
    new Vector3(0.1, 1, -0.2),
    scene,
  );
  light.intensity = 0.95;
  light.groundColor = new Color3(0.16, 0.18, 0.22);

  const actors = new Map<string, CompiledActor>();
  for (const actor of document.actors) {
    actors.set(actor.id, createHumanoidProxy(scene, actor));
  }

  const cameras = new Map<string, FreeCamera>();
  for (const cameraSpec of document.cameras) {
    const camera = new FreeCamera(
      `camera:${cameraSpec.id}`,
      toVector3(cameraSpec.position),
      scene,
    );
    camera.setTarget(toVector3(cameraSpec.target));
    camera.fov = cameraSpec.fovDeg * DEG_TO_RAD;
    camera.minZ = cameraSpec.nearClip ?? DEFAULT_NEAR_CLIP;
    camera.maxZ = cameraSpec.farClip ?? DEFAULT_FAR_CLIP;
    cameras.set(cameraSpec.id, camera);
  }

  const firstCamera = cameras.values().next().value as FreeCamera | undefined;
  scene.activeCamera = firstCamera ?? null;

  const shots = new Map<string, ShotSpec>();
  for (const shot of document.shots) {
    shots.set(shot.id, shot);
  }

  scene.metadata = {
    zorrDirecting: {
      sceneId: document.sceneId,
      schemaVersion: document.schemaVersion,
      unit: document.stage.unit,
      authority: 'DISPOSABLE_DIRECTING_REFERENCE_ONLY',
      defaults: {
        nearClip: DEFAULT_NEAR_CLIP,
        farClip: DEFAULT_FAR_CLIP,
      },
    },
  };

  return {
    engine,
    scene,
    document,
    actors,
    cameras,
    shots,
  };
}
