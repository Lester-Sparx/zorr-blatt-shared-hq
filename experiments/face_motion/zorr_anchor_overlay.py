#!/usr/bin/env python3
"""Generate a pixel-coordinate overlay for manual anime control-anchor measurement."""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2


def parse_crop(text: str | None, w: int, h: int):
    if not text:
        return 0, 0, w, h
    vals = [int(v.strip()) for v in text.split(",")]
    if len(vals) != 4:
        raise ValueError("--crop must be x0,y0,x1,y1")
    x0, y0, x1, y1 = vals
    if not (0 <= x0 < x1 <= w and 0 <= y0 < y1 <= h):
        raise ValueError(f"crop outside image: {(x0, y0, x1, y1)} for {(w, h)}")
    return x0, y0, x1, y1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--crop", default=None, help="x0,y0,x1,y1 in source pixels")
    ap.add_argument("--step", type=int, default=10)
    ap.add_argument("--major", type=int, default=50)
    ap.add_argument("--scale", type=float, default=2.0)
    args = ap.parse_args()

    image = cv2.imread(str(args.source), cv2.IMREAD_COLOR)
    if image is None:
        raise RuntimeError(f"cannot read {args.source}")
    h, w = image.shape[:2]
    x0, y0, x1, y1 = parse_crop(args.crop, w, h)
    crop = image[y0:y1, x0:x1].copy()
    if args.scale <= 0:
        raise ValueError("--scale must be > 0")
    crop = cv2.resize(crop, None, fx=args.scale, fy=args.scale, interpolation=cv2.INTER_NEAREST)

    minor_x = (180, 180, 255)
    major_x = (0, 0, 255)
    minor_y = (255, 210, 170)
    major_y = (255, 110, 0)
    s = args.scale

    first_x = ((x0 + args.step - 1) // args.step) * args.step
    for x in range(first_x, x1, args.step):
        xx = int(round((x - x0) * s))
        is_major = x % args.major == 0
        cv2.line(crop, (xx, 0), (xx, crop.shape[0] - 1), major_x if is_major else minor_x, 1, cv2.LINE_AA)
        if is_major:
            cv2.putText(crop, str(x), (xx + 2, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.38, major_x, 1, cv2.LINE_AA)

    first_y = ((y0 + args.step - 1) // args.step) * args.step
    for y in range(first_y, y1, args.step):
        yy = int(round((y - y0) * s))
        is_major = y % args.major == 0
        cv2.line(crop, (0, yy), (crop.shape[1] - 1, yy), major_y if is_major else minor_y, 1, cv2.LINE_AA)
        if is_major:
            cv2.putText(crop, str(y), (2, yy - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.38, major_y, 1, cv2.LINE_AA)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(args.out), crop):
        raise RuntimeError(f"failed writing {args.out}")
    print(f"PASS {args.out} source={w}x{h} crop={(x0, y0, x1, y1)} scale={args.scale}")


if __name__ == "__main__":
    main()
