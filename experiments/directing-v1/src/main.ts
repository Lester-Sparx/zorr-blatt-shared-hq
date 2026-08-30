import { Engine } from '@babylonjs/core/Engines/engine';
import { captureStill } from './capture';
import { compileDirectingScene } from './compiler';
import { parseSceneDocument } from './contract';
import { createEvaluatedSnapshot } from './snapshot';
import { evaluateAtTime } from './timeline';

declare global {
  interface Window {
    __zbDirecting?: {
      seek(timeSec: number): ReturnType<typeof createEvaluatedSnapshot>;
      snapshot(): ReturnType<typeof createEvaluatedSnapshot>;
      capture(): Promise<string>;
    };
  }
}

const bootstrap = async (): Promise<void> => {
  const canvas = document.querySelector<HTMLCanvasElement>('#renderCanvas');
  if (!canvas) {
    throw new Error('RENDER_CANVAS_NOT_FOUND');
  }

  const response = await fetch('/proof-scene.json', { cache: 'no-store' });
  if (!response.ok) {
    throw new Error(`PROOF_SCENE_FETCH_FAILED: ${response.status}`);
  }
  const sceneDocument = parseSceneDocument(await response.json());

  const engine = new Engine(canvas, true, {
    preserveDrawingBuffer: true,
    stencil: true,
  });
  const compiled = compileDirectingScene(engine, sceneDocument);

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
  };

  document.body.dataset.zbDirecting = 'ready';
  engine.runRenderLoop(() => {
    compiled.scene.render();
  });
  window.addEventListener('resize', () => engine.resize());
};

void bootstrap().catch((error: unknown) => {
  const message = error instanceof Error ? error.message : String(error);
  document.body.dataset.zbDirecting = 'error';
  document.body.textContent = `BABYLON DIRECTING BOOT FAILED: ${message}`;
  console.error(error);
});
