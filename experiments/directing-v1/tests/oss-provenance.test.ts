import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

type SceneManifest = {
  openSourceOnly: boolean;
  codeDependencies: Array<{
    name: string;
    version: string;
    license: string;
  }>;
  externalArtAssets: unknown[];
  materials: Array<{ id: string; source: string }>;
  textures: unknown[];
  hdris: unknown[];
  fonts: unknown[];
  audio: unknown[];
  remoteServices: unknown[];
};

const readText = (relativePath: string): string => readFileSync(
  new URL(relativePath, import.meta.url),
  'utf8',
);

const readManifest = (): SceneManifest => JSON.parse(
  readText('../public/cinematic-scene-r01.manifest.json'),
) as SceneManifest;

describe('cinematic scene OSS-only provenance', () => {
  it('allows only explicitly pinned open-source code dependencies', () => {
    const manifest = readManifest();
    const allowedLicenses = new Set(['Apache-2.0', 'MIT']);

    expect(manifest.openSourceOnly).toBe(true);
    expect(manifest.codeDependencies).toHaveLength(6);
    for (const dependency of manifest.codeDependencies) {
      expect(dependency.name.length).toBeGreaterThan(0);
      expect(dependency.version).toMatch(/^\d+\.\d+\.\d+$/);
      expect(allowedLicenses.has(dependency.license)).toBe(true);
    }
  });

  it('uses no external art, texture, HDRI, font, audio, or remote service', () => {
    const manifest = readManifest();
    expect(manifest.externalArtAssets).toEqual([]);
    expect(manifest.textures).toEqual([]);
    expect(manifest.hdris).toEqual([]);
    expect(manifest.fonts).toEqual([]);
    expect(manifest.audio).toEqual([]);
    expect(manifest.remoteServices).toEqual([]);
    expect(manifest.materials.length).toBeGreaterThan(0);
    expect(manifest.materials.every(
      ({ source }) => source === 'PROCEDURAL_CODE_AUTHORED',
    )).toBe(true);
  });

  it('contains no remote asset URL in the executable scene surface', () => {
    const executableInputs = [
      '../src/cinematicSet.ts',
      '../src/main.ts',
      '../public/cinematic-scene-r01.json',
      '../index.html',
    ].map(readText);

    for (const source of executableInputs) {
      expect(source).not.toMatch(/https?:\/\//i);
      expect(source).not.toMatch(/data:\s*application\//i);
    }
  });
});
