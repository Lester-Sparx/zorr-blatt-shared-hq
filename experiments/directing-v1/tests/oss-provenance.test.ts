import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
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
    expect(manifest.codeDependencies).toHaveLength(8);
    for (const dependency of manifest.codeDependencies) {
      expect(dependency.name.length).toBeGreaterThan(0);
      expect(dependency.version).toMatch(/^\d+\.\d+\.\d+$/);
      expect(allowedLicenses.has(dependency.license)).toBe(true);
    }
  });

  it('pins the only external mesh and uses no remote production surface', () => {
    const manifest = readManifest();
    expect(manifest.externalArtAssets).toEqual([expect.objectContaining({
      path: 'public/oxihuman-b0-body.glb',
      sourceCommit: '603b446854c3d5a9ca478214e7b85008d54786b9',
      license: 'Apache-2.0',
      sha256: '626be02ae16ddf2bfd8760633761489a3c24f5b35d1e5b3f4a0c9a602cbffaf0',
    })]);
    const glb = readFileSync(new URL('../public/oxihuman-b0-body.glb', import.meta.url));
    expect(createHash('sha256').update(glb).digest('hex')).toBe(
      '626be02ae16ddf2bfd8760633761489a3c24f5b35d1e5b3f4a0c9a602cbffaf0',
    );
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
