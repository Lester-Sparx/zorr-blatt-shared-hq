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

  const canvas = compiled.engine.getRenderingCanvas();
  if (!canvas) {
    throw new Error('CAPTURE_RENDERING_CANVAS_NOT_FOUND');
  }

  const originalWidth = canvas.width;
  const originalHeight = canvas.height;
  compiled.scene.activeCamera = camera;

  try {
    compiled.engine.setSize(capture.widthPx, capture.heightPx, true);
    camera.getProjectionMatrix(true);

    if (
      canvas.width !== capture.widthPx
      || canvas.height !== capture.heightPx
    ) {
      throw new Error(
        `CAPTURE_CANVAS_SIZE_MISMATCH: expected ${capture.widthPx}x${capture.heightPx}, got ${canvas.width}x${canvas.height}`,
      );
    }

    compiled.scene.render();
    const dataUrl = canvas.toDataURL('image/png');
    if (!dataUrl.startsWith('data:image/png;base64,')) {
      throw new Error('CAPTURE_DATA_URL_INVALID');
    }
    return dataUrl;
  } finally {
    compiled.engine.setSize(originalWidth, originalHeight, true);
    camera.getProjectionMatrix(true);
    compiled.scene.render();
  }
}
