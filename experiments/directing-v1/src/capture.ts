import { CreateScreenshotUsingRenderTarget } from '@babylonjs/core/Misc/screenshotTools';
import type { CaptureSpec } from './contract';
import type { CompiledDirectingScene } from './compiler';
import { evaluateAtTime } from './timeline';

const SCREENSHOT_TIMEOUT_MS = 30_000;

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

  return await new Promise<string>((resolve, reject) => {
    let settled = false;
    const succeed = (data: string): void => {
      if (!settled) {
        settled = true;
        resolve(data);
      }
    };
    const fail = (error: unknown): void => {
      if (!settled) {
        settled = true;
        reject(error);
      }
    };

    try {
      CreateScreenshotUsingRenderTarget(
        compiled.engine,
        camera,
        { width: capture.widthPx, height: capture.heightPx },
        succeed,
        'image/png',
        1,
        false,
        undefined,
        false,
        false,
        true,
        undefined,
        undefined,
        undefined,
        SCREENSHOT_TIMEOUT_MS,
        () => fail(new Error(
          `CAPTURE_TIMEOUT: screenshot was not ready after ${SCREENSHOT_TIMEOUT_MS}ms`,
        )),
      );
    } catch (error) {
      fail(error);
    }
  });
}
