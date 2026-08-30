import type { Vec3 } from './contract';

export const clamp01 = (value: number): number =>
  Math.max(0, Math.min(1, value));

export const lerp = (a: number, b: number, t: number): number =>
  a + (b - a) * clamp01(t);

export function lerpAngleDeg(a: number, b: number, t: number): number {
  const delta = ((b - a + 540) % 360) - 180;
  return a + delta * clamp01(t);
}

export function lerpVec3(a: Vec3, b: Vec3, t: number): Vec3 {
  return {
    x: lerp(a.x, b.x, t),
    y: lerp(a.y, b.y, t),
    z: lerp(a.z, b.z, t),
  };
}
