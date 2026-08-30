import { expect, test } from '@playwright/test';
import { mkdir, writeFile } from 'node:fs/promises';

type SceneSnapshot = {
  sceneId: string;
  timeSec: number;
  actors: Array<{
    id: string;
    position: { x: number; y: number; z: number };
    rotationYDeg: number;
  }>;
  activeCamera: {
    id: string;
    position: { x: number; y: number; z: number };
    target: { x: number; y: number; z: number };
    fovDeg: number;
  } | null;
  capture: {
    shotId: string;
    widthPx: number;
    heightPx: number;
    timeSec: number;
    output: string;
  };
};

type Bridge = {
  seek(timeSec: number): SceneSnapshot;
  snapshot(): SceneSnapshot;
  capture(): Promise<string>;
  exportScene(): string;
};

type CaptureProbe = {
  state: 'pending' | 'fulfilled' | 'rejected';
  dataUrl?: string;
  error?: string;
};

const decodePng = (dataUrl: string): Buffer => {
  const encoded = dataUrl.split(',', 2)[1];
  if (!encoded) {
    throw new Error('PNG_DATA_URL_MALFORMED');
  }
  return Buffer.from(encoded, 'base64');
};

const pngDimensions = (bytes: Buffer): { width: number; height: number } => {
  const signature = bytes.subarray(0, 8).toString('hex');
  if (signature !== '89504e470d0a1a0a') {
    throw new Error(`PNG_SIGNATURE_INVALID: ${signature}`);
  }
  return {
    width: bytes.readUInt32BE(16),
    height: bytes.readUInt32BE(20),
  };
};

test('cinematic scene exports deterministic PNG and Babylon scene', async ({
  page,
}) => {
  test.setTimeout(90_000);

  const seek = (timeSec: number): Promise<SceneSnapshot> => page.evaluate(
    (time) => {
      const bridge = (
        window as unknown as { __zbDirecting?: Bridge }
      ).__zbDirecting;
      if (!bridge) {
        throw new Error('DIRECTING_BRIDGE_NOT_READY');
      }
      return bridge.seek(time);
    },
    timeSec,
  );

  const snapshot = (): Promise<SceneSnapshot> => page.evaluate(() => {
    const bridge = (
      window as unknown as { __zbDirecting?: Bridge }
    ).__zbDirecting;
    if (!bridge) {
      throw new Error('DIRECTING_BRIDGE_NOT_READY');
    }
    return bridge.snapshot();
  });

  const exportScene = (): Promise<string> => page.evaluate(() => {
    const bridge = (
      window as unknown as { __zbDirecting?: Bridge }
    ).__zbDirecting;
    if (!bridge) {
      throw new Error('DIRECTING_BRIDGE_NOT_READY');
    }
    return bridge.exportScene();
  });

  const capture = async (): Promise<string> => {
    await page.evaluate(() => {
      const host = window as unknown as {
        __zbDirecting?: Bridge;
        __zbCaptureProbe?: CaptureProbe;
      };
      const bridge = host.__zbDirecting;
      if (!bridge) {
        throw new Error('DIRECTING_BRIDGE_NOT_READY');
      }

      const probe: CaptureProbe = { state: 'pending' };
      host.__zbCaptureProbe = probe;
      void bridge.capture().then(
        (dataUrl) => {
          probe.state = 'fulfilled';
          probe.dataUrl = dataUrl;
        },
        (error: unknown) => {
          probe.state = 'rejected';
          probe.error = error instanceof Error ? error.message : String(error);
        },
      );
    });

    await page.waitForFunction(() => {
      const probe = (
        window as unknown as { __zbCaptureProbe?: CaptureProbe }
      ).__zbCaptureProbe;
      return Boolean(probe && probe.state !== 'pending');
    }, undefined, { timeout: 60_000 });

    const probe = await page.evaluate(() => (
      window as unknown as { __zbCaptureProbe?: CaptureProbe }
    ).__zbCaptureProbe);
    if (!probe) {
      throw new Error('CAPTURE_PROBE_MISSING');
    }
    if (probe.state === 'rejected') {
      throw new Error(`CAPTURE_REJECTED: ${probe.error ?? 'unknown error'}`);
    }
    if (probe.state !== 'fulfilled' || typeof probe.dataUrl !== 'string') {
      throw new Error(`CAPTURE_PROBE_INVALID: ${JSON.stringify(probe)}`);
    }
    return probe.dataUrl;
  };

  const waitForScene = async (): Promise<void> => {
    await page.waitForFunction(() =>
      document.body.dataset.zbDirecting === 'ready'
      && document.body.dataset.zbSceneId === 'ZB-CINEMATIC-SCENE-R01',
    );
  };

  await page.goto('/');
  await waitForScene();

  const initial = await snapshot();
  expect(initial.sceneId).toBe('ZB-CINEMATIC-SCENE-R01');
  expect(initial.capture).toEqual({
    shotId: 'shot-scene-main',
    widthPx: 1280,
    heightPx: 720,
    timeSec: 2.25,
    output: 'zorr-cinematic-scene-r01.png',
  });
  expect(initial.activeCamera?.id).toBe('cam-scene-main');
  expect(initial.actors.map(({ id }) => id)).toEqual(['A', 'B']);

  const firstSnapshot = await seek(2.25);
  await seek(0.35);
  const secondSnapshot = await seek(2.25);
  expect(secondSnapshot).toEqual(firstSnapshot);

  const firstSceneText = await exportScene();
  const exported = JSON.parse(firstSceneText) as {
    metadata?: {
      zorrCinematicScene?: {
        sceneId?: string;
        authority?: string;
      };
      zorrOpenSourcePolicy?: {
        externalArtAssets?: unknown[];
        remoteInference?: boolean;
      };
    };
    cameras?: Array<{ name?: string }>;
    lights?: Array<{ name?: string }>;
    meshes?: Array<{ name?: string }>;
  };
  expect(exported.metadata?.zorrCinematicScene).toMatchObject({
    sceneId: 'ZB-CINEMATIC-SCENE-R01',
    authority: 'PROTOTYPE_NON_CANON',
  });
  expect(exported.metadata?.zorrOpenSourcePolicy).toEqual({
    externalArtAssets: [],
    geometry: 'PROCEDURAL_BABYLON_PRIMITIVES',
    materials: 'CODE_AUTHORED_STANDARD_MATERIALS',
    remoteInference: false,
  });
  expect(exported.cameras?.map(({ name }) => name)).toContain(
    'camera:cam-scene-main',
  );
  expect(exported.lights?.map(({ name }) => name)).toEqual(
    expect.arrayContaining([
      'set:light:key',
      'set:light:portal',
      'set:light:fill',
    ]),
  );
  expect(exported.meshes?.map(({ name }) => name)).toEqual(
    expect.arrayContaining([
      'set:portal:left',
      'set:portal:right',
      'set:portal:top',
      'actor:A:mesh:head',
      'actor:B:mesh:head',
    ]),
  );

  const firstPng = decodePng(await capture());
  expect(firstPng.byteLength).toBeGreaterThan(5_000);
  expect(pngDimensions(firstPng)).toEqual({ width: 1280, height: 720 });

  await page.reload();
  await waitForScene();

  const afterReload = await seek(2.25);
  expect(afterReload).toEqual(firstSnapshot);

  const secondSceneText = await exportScene();
  expect(secondSceneText).toBe(firstSceneText);

  const secondPng = decodePng(await capture());
  expect(secondPng.equals(firstPng)).toBe(true);

  const manifestText = await page.evaluate(async () => {
    const response = await fetch('/cinematic-scene-r01.manifest.json', {
      cache: 'no-store',
    });
    if (!response.ok) {
      throw new Error(`SCENE_MANIFEST_FETCH_FAILED: ${response.status}`);
    }
    return response.text();
  });
  const manifest = JSON.parse(manifestText) as {
    openSourceOnly?: boolean;
    externalArtAssets?: unknown[];
    remoteServices?: unknown[];
  };
  expect(manifest.openSourceOnly).toBe(true);
  expect(manifest.externalArtAssets).toEqual([]);
  expect(manifest.remoteServices).toEqual([]);

  await mkdir('artifacts', { recursive: true });
  await writeFile('artifacts/zorr-cinematic-scene-r01.png', secondPng);
  await writeFile(
    'artifacts/zorr-cinematic-scene-r01.babylon',
    secondSceneText,
    'utf8',
  );
  await writeFile(
    'artifacts/zorr-cinematic-scene-r01.manifest.json',
    manifestText,
    'utf8',
  );
});
