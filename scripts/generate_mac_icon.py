#!/usr/bin/env python3
"""Generate a simple PNG iconset using only the Python standard library."""

from __future__ import annotations

import math
import struct
import sys
import zlib
from pathlib import Path


def clamp(value: float) -> int:
    return max(0, min(255, int(round(value))))


def blend(base: tuple[int, int, int, int], over: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    br, bg, bb, ba = [channel / 255 for channel in base]
    or_, og, ob, oa = [channel / 255 for channel in over]
    out_a = oa + ba * (1 - oa)
    if out_a == 0:
        return 0, 0, 0, 0
    out_r = (or_ * oa + br * ba * (1 - oa)) / out_a
    out_g = (og * oa + bg * ba * (1 - oa)) / out_a
    out_b = (ob * oa + bb * ba * (1 - oa)) / out_a
    return clamp(out_r * 255), clamp(out_g * 255), clamp(out_b * 255), clamp(out_a * 255)


def rounded_rect_mask(x: float, y: float, size: int, margin: float, radius: float) -> bool:
    left = margin
    right = size - margin
    bottom = margin
    top = size - margin
    if x < left or x > right or y < bottom or y > top:
        return False

    cx = left + radius if x < left + radius else right - radius if x > right - radius else x
    cy = bottom + radius if y < bottom + radius else top - radius if y > top - radius else y
    return (x - cx) ** 2 + (y - cy) ** 2 <= radius**2


def polygon_contains(point: tuple[float, float], polygon: list[tuple[float, float]]) -> bool:
    x, y = point
    inside = False
    previous_x, previous_y = polygon[-1]
    for current_x, current_y in polygon:
        intersects = (current_y > y) != (previous_y > y)
        if intersects:
            slope_x = (previous_x - current_x) * (y - current_y) / (previous_y - current_y) + current_x
            if x < slope_x:
                inside = not inside
        previous_x, previous_y = current_x, current_y
    return inside


def pixel(size: int, x: int, y: int) -> tuple[int, int, int, int]:
    nx = x / max(size - 1, 1)
    ny = y / max(size - 1, 1)
    margin = size * 0.04
    radius = size * 0.22

    if not rounded_rect_mask(x, y, size, margin, radius):
        return 0, 0, 0, 0

    top = (8, 24, 26)
    mid = (10, 68, 66)
    bottom = (140, 219, 128)
    mix = (nx * 0.45) + (1 - ny) * 0.55
    if mix < 0.58:
        local = mix / 0.58
        color = tuple(clamp(top[i] * (1 - local) + mid[i] * local) for i in range(3))
    else:
        local = (mix - 0.58) / 0.42
        color = tuple(clamp(mid[i] * (1 - local) + bottom[i] * local) for i in range(3))

    result = (*color, 255)

    cx = size * 0.5
    cy = size * 0.5
    distance = math.hypot(x - cx, y - cy)
    if size * 0.23 <= distance <= size * 0.33:
        result = blend(result, (186, 255, 199, 96))
    if distance < size * 0.21:
        result = blend(result, (4, 18, 21, 208))

    pick = [
        (size * 0.30, size * 0.30),
        (size * 0.68, size * 0.70),
        (size * 0.76, size * 0.62),
        (size * 0.38, size * 0.22),
    ]
    if polygon_contains((x, y), pick):
        result = blend(result, (255, 196, 89, 248))

    spark = [
        (size * 0.55, size * 0.28),
        (size * 0.62, size * 0.42),
        (size * 0.76, size * 0.48),
        (size * 0.62, size * 0.54),
        (size * 0.55, size * 0.68),
        (size * 0.48, size * 0.54),
        (size * 0.34, size * 0.48),
        (size * 0.48, size * 0.42),
    ]
    if polygon_contains((x, y), spark):
        result = blend(result, (194, 255, 189, 242))

    border = rounded_rect_mask(x, y, size, margin + size * 0.012, max(1, radius - size * 0.012))
    if not border:
        result = blend(result, (255, 255, 255, 48))

    return result


def write_png(path: Path, size: int) -> None:
    rows = []
    for y in range(size):
        row = bytearray([0])
        for x in range(size):
            row.extend(pixel(size, x, size - 1 - y))
        rows.append(bytes(row))

    raw = b"".join(rows)

    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 9))
    png += chunk(b"IEND", b"")
    path.write_bytes(png)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: generate_mac_icon.py ICONSET_DIR", file=sys.stderr)
        return 2

    iconset = Path(sys.argv[1])
    iconset.mkdir(parents=True, exist_ok=True)
    variants = {
        "icon_16x16.png": 16,
        "icon_16x16@2x.png": 32,
        "icon_32x32.png": 32,
        "icon_32x32@2x.png": 64,
        "icon_128x128.png": 128,
        "icon_128x128@2x.png": 256,
        "icon_256x256.png": 256,
        "icon_256x256@2x.png": 512,
        "icon_512x512.png": 512,
        "icon_512x512@2x.png": 1024,
    }
    for name, size in variants.items():
        write_png(iconset / name, size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
