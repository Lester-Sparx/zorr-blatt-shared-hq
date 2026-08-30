import { SceneSerializer } from '@babylonjs/core/Misc/sceneSerializer';
import type { Scene } from '@babylonjs/core/scene';

type JsonRecord = Record<string, unknown>;

const UNSTABLE_KEYS = new Set(['uniqueId']);

const isRecord = (value: unknown): value is JsonRecord =>
  Boolean(value) && typeof value === 'object' && !Array.isArray(value);

const normalizeGeometryIds = (value: JsonRecord): JsonRecord => {
  const replacements = new Map<string, string>();
  const meshes = Array.isArray(value.meshes) ? value.meshes : [];

  for (const meshValue of meshes) {
    if (!isRecord(meshValue)) {
      continue;
    }
    const name = meshValue.name;
    const geometryId = meshValue.geometryId;
    if (typeof name === 'string' && typeof geometryId === 'string') {
      replacements.set(geometryId, `geometry:${name}`);
    }
  }

  const replace = (current: unknown): unknown => {
    if (typeof current === 'string') {
      return replacements.get(current) ?? current;
    }
    if (Array.isArray(current)) {
      return current.map(replace);
    }
    if (!isRecord(current)) {
      return current;
    }
    return Object.fromEntries(
      Object.entries(current).map(([key, nested]) => [key, replace(nested)]),
    );
  };

  return replace(value) as JsonRecord;
};

const stableArrayKey = (value: unknown): string | null => {
  if (!isRecord(value)) {
    return null;
  }
  if (typeof value.name === 'string') {
    return `0:${value.name}`;
  }
  if (typeof value.id === 'string') {
    return `1:${value.id}`;
  }
  return null;
};

const canonicalize = (value: unknown): unknown => {
  if (typeof value === 'number') {
    if (!Number.isFinite(value)) {
      throw new Error('SCENE_EXPORT_NON_FINITE_NUMBER');
    }
    if (Object.is(value, -0)) {
      return 0;
    }
    return Number(value.toFixed(12));
  }

  if (Array.isArray(value)) {
    const normalized = value.map(canonicalize);
    const keys = normalized.map(stableArrayKey);
    if (keys.every((key): key is string => key !== null)) {
      return normalized
        .map((entry, index) => ({ entry, key: keys[index]! }))
        .sort((left, right) => left.key.localeCompare(right.key))
        .map(({ entry }) => entry);
    }
    return normalized;
  }

  if (!isRecord(value)) {
    return value;
  }

  const result: JsonRecord = {};
  for (const key of Object.keys(value).sort()) {
    if (UNSTABLE_KEYS.has(key) || value[key] === undefined) {
      continue;
    }
    result[key] = canonicalize(value[key]);
  }
  return result;
};

export function exportCanonicalBabylonScene(scene: Scene): string {
  const serialized = SceneSerializer.Serialize(scene) as JsonRecord;
  const normalized = normalizeGeometryIds(serialized);
  return `${JSON.stringify(canonicalize(normalized), null, 2)}\n`;
}
