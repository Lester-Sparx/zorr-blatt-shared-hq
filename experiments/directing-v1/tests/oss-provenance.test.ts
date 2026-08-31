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
  externalArtAssets: Array<{
    path: string;
    sourceCommit: string;
    license: string;
    sha256: string;
  }>;
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

  it('pins every R04 external asset and uses no remote production surface', () => {
    const manifest = readManifest();
    expect(manifest.externalArtAssets).toEqual([
      expect.objectContaining({
        path: 'public/assets/r04/quaternius-superhero-male.glb',
        sourceCommit: 'aa02a4e6d8337a0604d2da131bcbbeb1f01badf0',
        license: 'CC0',
        sha256: 'a466828c67a4acc9b2413212ce6d9cde235e3aed9b675680c14fd9673858f118',
      }),
      expect.objectContaining({
        path: 'public/assets/r04/quaternius-ual.glb',
        sourceCommit: 'aa02a4e6d8337a0604d2da131bcbbeb1f01badf0',
        license: 'CC0',
        sha256: '4c748767741a3e495d89667b9a218b690ba9810b9517a12e960780e3ca72c4e9',
      }),
      expect.objectContaining({
        path: 'public/assets/r04/sword.glb',
        sourceCommit: '71bbfbdfacd118196994b26da68eec1876d55c6b',
        license: 'CC0',
        sha256: '62add428c985df2ec32f7e516ab685a327cca886926446f798fe92d6ca180d3a',
      }),
    ]);

    for (const asset of manifest.externalArtAssets) {
      const glb = readFileSync(new URL(`../${asset.path}`, import.meta.url));
      expect(createHash('sha256').update(glb).digest('hex')).toBe(asset.sha256);
    }

    expect(manifest.textures).toEqual([]);
    expect(manifest.hdris).toEqual([]);
    expect(manifest.fonts).toEqual([]);
    expect(manifest.audio).toEqual([]);
    expect(manifest.remoteServices).toEqual([]);
    expect(manifest.materials.length).toBeGreaterThan(0);
    expect(manifest.materials.map(({ source }) => source)).toEqual([
      'EXISTING_BABYLON_STANDARD_MATERIAL',
      'PINNED_SOURCE_GLTF',
    ]);
  });

  it('contains no remote asset URL in the executable scene surface', () => {
    const executableInputs = [
      '../src/actionScene.ts',
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
