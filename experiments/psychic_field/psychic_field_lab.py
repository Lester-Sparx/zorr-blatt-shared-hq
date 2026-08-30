#!/usr/bin/env python3
"""ZORR procedural PSYCHIC FIELD laboratory.

Production-only experiment. This script creates dependency-free PPM previews for
optical-field studies derived from the current ZORR visual-language research.
It does not define lore.

Design rule: a pattern is not decoration. The field must have a focus, a flow,
and a reason to interact with face/body/space.

Modes:
  checker_bulge  - checker grid displaced by a radial lens-like volume
  vortex         - spiral phase field for obsession / temporal pressure
  stripe_warp    - continuous stripes bent around a local attractor
  tunnel_checker - checker field pushed into a depth/tunnel illusion
  color_islands  - monochrome field interrupted by sparse color territories

Output is binary PPM (P6), readable by ImageMagick, ffmpeg, Krita, Blender,
OpenToonz and most image viewers.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple


TAU = 2.0 * math.pi


@dataclass(frozen=True)
class Params:
    width: int
    height: int
    scale: float
    strength: float
    focus_x: float
    focus_y: float
    phase: float
    color_accent: bool


def clamp01(v: float) -> float:
    return 0.0 if v < 0.0 else 1.0 if v > 1.0 else v


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    if edge0 == edge1:
        return 0.0
    t = clamp01((x - edge0) / (edge1 - edge0))
    return t * t * (3.0 - 2.0 * t)


def signed_checker(u: float, v: float, scale: float) -> float:
    a = math.floor(u * scale)
    b = math.floor(v * scale)
    return 1.0 if ((a + b) & 1) == 0 else -1.0


def to_rgb(gray: float, accent: float = 0.0) -> Tuple[int, int, int]:
    """Map scalar field to high-contrast fashion palette.

    `accent` is deliberately sparse. Black/white structure stays primary.
    """
    g = int(round(255.0 * clamp01(gray)))
    if accent <= 0.0:
        return g, g, g

    a = clamp01(accent)
    # Controlled acidic-magenta/cyan interpolation, used only as a small event.
    r = int(round((1.0 - a) * g + a * 245.0))
    gg = int(round((1.0 - a) * g + a * 70.0))
    b = int(round((1.0 - a) * g + a * 185.0))
    return r, gg, b


def normalize_pixel(x: int, y: int, p: Params) -> Tuple[float, float]:
    # Aspect-correct coordinates centered around the optical focus.
    aspect = p.width / p.height
    u = (x + 0.5) / p.width
    v = (y + 0.5) / p.height
    return (u - p.focus_x) * aspect, v - p.focus_y


def checker_bulge(x: int, y: int, p: Params) -> Tuple[float, float]:
    dx, dy = normalize_pixel(x, y, p)
    r = math.hypot(dx, dy)

    # Radial displacement. Strongest near the focus, decays smoothly outward.
    envelope = math.exp(-7.0 * r * r)
    k = 1.0 + p.strength * envelope
    wx = dx / k
    wy = dy / k

    # Return to 0..1-like field coordinates for checker sampling.
    u = wx + 0.5
    v = wy + 0.5
    c = signed_checker(u, v, p.scale)
    gray = 0.96 if c > 0 else 0.03

    # Thin local highlight makes volume readable without generic glow.
    rim = smoothstep(0.30, 0.26, abs(r - 0.28))
    gray = clamp01(gray + 0.12 * rim)
    return gray, 0.0


def vortex(x: int, y: int, p: Params) -> Tuple[float, float]:
    dx, dy = normalize_pixel(x, y, p)
    r = max(math.hypot(dx, dy), 1e-6)
    theta = math.atan2(dy, dx)

    # Spiral phase: angle and log radius are deliberately coupled.
    phase = p.scale * (theta / TAU + p.strength * math.log(r + 0.025)) + p.phase
    wave = math.sin(TAU * phase)
    gray = 0.97 if wave >= 0.0 else 0.02

    # Optional tiny accent island near the vortex core only.
    accent = 0.0
    if p.color_accent:
        accent = smoothstep(0.14, 0.02, r) * smoothstep(0.25, 0.75, 0.5 + 0.5 * wave)
    return gray, accent


def stripe_warp(x: int, y: int, p: Params) -> Tuple[float, float]:
    dx, dy = normalize_pixel(x, y, p)
    r2 = dx * dx + dy * dy

    # A local potential bends otherwise calm horizontal stripes.
    potential = p.strength * math.exp(-10.0 * r2) * dx
    phase = p.scale * (dy + potential) + p.phase
    wave = math.sin(TAU * phase)

    # Smooth stripe edges slightly to avoid aliasing while keeping hard graphics.
    edge = 0.12
    if wave > edge:
        gray = 0.98
    elif wave < -edge:
        gray = 0.02
    else:
        gray = 0.5 + 0.48 * wave / edge
    return gray, 0.0


def tunnel_checker(x: int, y: int, p: Params) -> Tuple[float, float]:
    dx, dy = normalize_pixel(x, y, p)
    r = max(math.hypot(dx, dy), 1e-5)
    theta = math.atan2(dy, dx)

    # Inverse radial coordinate creates depth compression toward the focus.
    depth = p.strength / (r + 0.08)
    angular = theta / TAU
    c = signed_checker(depth + p.phase, angular, p.scale)
    gray = 0.97 if c > 0 else 0.02

    # Darken the optical throat so the field has a hierarchy and focal endpoint.
    throat = smoothstep(0.16, 0.02, r)
    gray *= 1.0 - 0.7 * throat
    return gray, 0.0


def color_islands(x: int, y: int, p: Params) -> Tuple[float, float]:
    # Start from warped stripes, then add sparse circular accent territories.
    gray, _ = stripe_warp(x, y, p)
    u = (x + 0.5) / p.width
    v = (y + 0.5) / p.height

    # Deterministic islands: no random particle soup.
    islands = (
        (0.43, 0.46, 0.075),
        (0.58, 0.54, 0.052),
        (0.51, 0.38, 0.033),
    )
    accent = 0.0
    for cx, cy, radius in islands:
        d = math.hypot(u - cx, v - cy)
        accent = max(accent, smoothstep(radius, radius * 0.72, d))
    return gray, accent if p.color_accent else 0.0


MODES = {
    "checker_bulge": checker_bulge,
    "vortex": vortex,
    "stripe_warp": stripe_warp,
    "tunnel_checker": tunnel_checker,
    "color_islands": color_islands,
}


def render(mode: str, output: Path, p: Params) -> None:
    fn = MODES[mode]
    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open("wb") as f:
        f.write(f"P6\n{p.width} {p.height}\n255\n".encode("ascii"))
        for y in range(p.height):
            row = bytearray()
            for x in range(p.width):
                gray, accent = fn(x, y, p)
                row.extend(to_rgb(gray, accent))
            f.write(row)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=sorted(MODES), default="checker_bulge")
    parser.add_argument("--output", type=Path, default=Path("psychic_field.ppm"))
    parser.add_argument("--width", type=int, default=1080)
    parser.add_argument("--height", type=int, default=1920)
    parser.add_argument("--scale", type=float, default=18.0)
    parser.add_argument("--strength", type=float, default=1.35)
    parser.add_argument("--focus-x", type=float, default=0.5)
    parser.add_argument("--focus-y", type=float, default=0.43)
    parser.add_argument("--phase", type=float, default=0.0)
    parser.add_argument("--color-accent", action="store_true")
    return parser.parse_args()


def main() -> None:
    a = parse_args()
    if a.width <= 0 or a.height <= 0:
        raise SystemExit("width and height must be positive")
    if a.scale <= 0:
        raise SystemExit("scale must be positive")

    params = Params(
        width=a.width,
        height=a.height,
        scale=a.scale,
        strength=a.strength,
        focus_x=a.focus_x,
        focus_y=a.focus_y,
        phase=a.phase,
        color_accent=a.color_accent,
    )
    render(a.mode, a.output, params)
    print(f"wrote {a.output} ({a.width}x{a.height}) mode={a.mode}")


if __name__ == "__main__":
    main()
