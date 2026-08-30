import { CreateScreenshotUsingRenderTargetAsync } from '@babylonjs/core/Misc/screenshotTools';
import type { CaptureSpec } from './contract';
import type { CompiledDirectingScene } from './compiler';
import { evaluateAtTime } from './timeline';

export async function captureStill(
  compiled: CompiledDirectingScene,
  capture: CaptureSpec,
): Promise<string> {
  const selection = evaluateAtTime(compiled, capture.timeSec);
  let cameraId = capture.cameraId;

  if (capture.shotId) {
    const shot = compiled.shots.get(capture.shotId);
    if (!shot) {
      throw new Error(`CAPTURE_SHOT_NOT_FOUND: ${capture.shotId}`);
    }
    cameraId = shot.cameraId;
  }

  cameraId ??= selection.activeCameraId ?? undefined;
  if (!cameraId) {
    throw new Error('CAPTURE_CAMERA_UNRESOLVED');
  }

  const camera = compiled.cameras.get(cameraId);
  if (!camera) {
    throw new Error(`CAPTURE_CAMERA_NOT_FOUND: ${cameraId}`);
  }

  compiled.scene.activeCamera = camera;
  compiled.scene.render();

  return CreateScreenshotUsingRenderTargetAsync(
    compiled.engine,
    camera,
    { width: capture.widthPx, height: capture.heightPx },
    'image/png',
    1,
    false,
  );
}
