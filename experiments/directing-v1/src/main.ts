import { Engine } from '@babylonjs/core/Engines/engine';
import { buildBladeDodgeAction } from './actionScene';
import { captureStill } from './capture';
import { buildCinematicSet } from './cinematicSet';
import { compileDirectingScene } from './compiler';
import { parseSceneDocument } from './contract';
import { exportCanonicalBabylonScene } from './sceneExport';
import { createEvaluatedSnapshot } from './snapshot';
import { evaluateAtTime } from './timeline';

declare global {
  interface Window {
    __zbDirecting?: {
      seek(timeSec: number): ReturnType<typeof createEvaluatedSnapshot>;
      snapshot(): ReturnType<typeof createEvaluatedSnapshot>;
      capture(): Promise<string>;
      exportScene(): string;
    };
  }
}

const bootstrap = async (): Promise<void> => {
  const canvas = document.querySelector<HTMLCanvasElement>('#renderCanvas');
  if (!canvas) {
    throw new Error('RENDER_CANVAS_NOT_FOUND');
  }

  const response = await fetch('/cinematic-scene-r01.json', {
    cache: 'no-store',
  });
  if (!response.ok) {
    throw new Error(`CINEMATIC_SCENE_FETCH_FAILED: ${response.status}`);
  }
  const sceneDocument = parseSceneDocument(await response.json());

  const engine = new Engine(canvas, true, {
    preserveDrawingBuffer: true,
    stencil: true,
  });
  const compiled = compileDirectingScene(engine, sceneDocument);
  buildCinematicSet(compiled.scene);
  for (const actor of compiled.actors.values()) {
    for (const mesh of actor.meshes) mesh.setEnabled(false);
  }
  await buildBladeDodgeAction(compiled.scene);

  let lastSeekSec = sceneDocument.capture.timeSec;
  evaluateAtTime(compiled, lastSeekSec);
  compiled.scene.render();

  window.__zbDirecting = {
    seek(timeSec) {
      lastSeekSec = timeSec;
      return createEvaluatedSnapshot(compiled, lastSeekSec);
    },
    snapshot() {
      return createEvaluatedSnapshot(compiled, lastSeekSec);
    },
    capture() {
      return captureStill(compiled, sceneDocument.capture);
    },
    exportScene() {
      evaluateAtTime(compiled, lastSeekSec);
      return exportCanonicalBabylonScene(compiled.scene);
    },
  };

  document.body.dataset.zbSceneId = sceneDocument.sceneId;
  document.body.dataset.zbDirecting = 'ready';
  engine.runRenderLoop(() => {
    compiled.scene.render();
  });
  window.addEventListener('resize', () => engine.resize());
};

void bootstrap().catch((error: unknown) => {
  const message = error instanceof Error ? error.message : String(error);
  document.body.dataset.zbDirecting = 'error';
  document.body.textContent = `BABYLON CINEMATIC SCENE BOOT FAILED: ${message}`;
  console.error(error);
});
