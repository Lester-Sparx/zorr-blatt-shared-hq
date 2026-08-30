import { expect, test } from '@playwright/test';
import { mkdir, writeFile } from 'node:fs/promises';

type Bridge = {
  seek(timeSec: number): unknown;
  snapshot(): unknown;
  capture(): Promise<string>;
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

test('proof scene scrubs deterministically and captures a real PNG', async ({
  page,
}) => {
  test.setTimeout(60_000);

  const seek = (timeSec: number): Promise<unknown> => page.evaluate(
    (time) => {
      const value = (
        window as unknown as { __zbDirecting?: Bridge }
      ).__zbDirecting;
      if (!value) {
        throw new Error('DIRECTING_BRIDGE_NOT_READY');
      }
      return value.seek(time);
    },
    timeSec,
  );

  const capture = async (): Promise<string> => {
    await page.evaluate(() => {
      const host = window as unknown as {
        __zbDirecting?: Bridge;
        __zbCaptureProbe?: CaptureProbe;
      };
      const value = host.__zbDirecting;
      if (!value) {
        throw new Error('DIRECTING_BRIDGE_NOT_READY');
      }

      const probe: CaptureProbe = { state: 'pending' };
      host.__zbCaptureProbe = probe;
      void value.capture().then(
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
    }, undefined, { timeout: 45_000 });

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

  await page.goto('/');
  await page.waitForFunction(() =>
    document.body.dataset.zbDirecting === 'ready',
  );

  const first = await seek(1.5);
  await seek(0.25);
  const second = await seek(1.5);
  expect(second).toEqual(first);

  const dataUrl = await capture();
  expect(dataUrl.startsWith('data:image/png;base64,')).toBe(true);

  const bytes = decodePng(dataUrl);
  expect(bytes.byteLength).toBeGreaterThan(1000);
  expect(pngDimensions(bytes)).toEqual({ width: 768, height: 512 });

  await mkdir('artifacts', { recursive: true });
  await writeFile('artifacts/proof-frame.png', bytes);

  await page.reload();
  await page.waitForFunction(() =>
    document.body.dataset.zbDirecting === 'ready',
  );
  const afterFreshReload = await seek(1.5);
  expect(afterFreshReload).toEqual(first);
});
