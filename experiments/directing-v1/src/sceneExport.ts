import { SceneSerializer } from '@babylonjs/core/Misc/sceneSerializer';
import type { Scene } from '@babylonjs/core/scene';

type JsonRecord = Record<string, unknown>;

const isRecord = (value: unknown): value is JsonRecord =>
  Boolean(value) && typeof value === 'object' && !Array.isArray(value);

const stableObjectId = (value: JsonRecord): string | null => {
  if (typeof value.id === 'string') {
    return value.id;
  }
  if (typeof value.name === 'string') {
    return value.name;
  }
  return null;
};

const collectStableUniqueIds = (
  value: unknown,
  stableIds: Map<number, string>,
): void => {
  if (Array.isArray(value)) {
    for (const nested of value) {
      collectStableUniqueIds(nested, stableIds);
    }
    return;
  }
  if (!isRecord(value)) {
    return;
  }

  const uniqueId = value.uniqueId;
  const stableId = stableObjectId(value);
  if (typeof uniqueId === 'number' && stableId !== null) {
    const previous = stableIds.get(uniqueId);
    if (previous !== undefined && previous !== stableId) {
      throw new Error(
        `SCENE_EXPORT_UNIQUE_ID_COLLISION: ${uniqueId} ${previous} ${stableId}`,
      );
    }
    stableIds.set(uniqueId, stableId);
  }

  for (const nested of Object.values(value)) {
    collectStableUniqueIds(nested, stableIds);
  }
};

const geometryReplacements = (value: JsonRecord): Map<string, string> => {
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

  return replacements;
};

const isUnstableIdentityKey = (key: string): boolean =>
  key === 'uniqueId' || key.endsWith('UniqueId');

const normalizeIdentifiers = (
  value: unknown,
  stableIds: ReadonlyMap<number, string>,
  geometryIds: ReadonlyMap<string, string>,
  parentKey?: string,
): unknown => {
  if (typeof value === 'number' && parentKey === 'parentId') {
    const stableParentId = stableIds.get(value);
    if (stableParentId === undefined) {
      throw new Error(`SCENE_EXPORT_PARENT_ID_UNRESOLVED: ${value}`);
    }
    return stableParentId;
  }

  if (typeof value === 'string') {
    return geometryIds.get(value) ?? value;
  }

  if (Array.isArray(value)) {
    return value.map((nested) => normalizeIdentifiers(
      nested,
      stableIds,
      geometryIds,
    ));
  }

  if (!isRecord(value)) {
    return value;
  }

  const result: JsonRecord = {};
  for (const [key, nested] of Object.entries(value)) {
    if (isUnstableIdentityKey(key) || nested === undefined) {
      continue;
    }
    result[key] = normalizeIdentifiers(
      nested,
      stableIds,
      geometryIds,
      key,
    );
  }
  return result;
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
    if (value[key] === undefined) {
      continue;
    }
    result[key] = canonicalize(value[key]);
  }
  return result;
};

export function exportCanonicalBabylonScene(scene: Scene): string {
  const serialized = SceneSerializer.Serialize(scene) as JsonRecord;
  const stableIds = new Map<number, string>();
  collectStableUniqueIds(serialized, stableIds);
  const normalized = normalizeIdentifiers(
    serialized,
    stableIds,
    geometryReplacements(serialized),
  );
  return `${JSON.stringify(canonicalize(normalized), null, 2)}\n`;
}
