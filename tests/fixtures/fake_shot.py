#!/usr/bin/env python3
"""Fake smoke screenshot for the stand-in games in tests (the real one is the card 0.6 hook's -SmokeShot= capture).
Usage: fake_shot.py OUT W H [--no-lock] [--flat-teal] [--keyart]
Draws an on-style frame (mottled paper, jagged rock band, round owl, gold and rust dots, colours from style.json) at
1/8 scale. The gameplay view is the largest 16:9 box in WxH with black bars around it; --no-lock stretches the scene
over the whole window (no 16:9 lock); --flat-teal adds the flat solid teal wind box (broken on purpose); --keyart
draws the key art itself as the scene (a build that looks like the target), at 1/4 scale."""
import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from png import write_png  # noqa: E402


def rgb(h):
    return tuple(int(h.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


def scene(w, h, teal=False):
    pal = {c["name"]: rgb(c["hex"]) for c in json.load(open(os.path.join(ROOT, "pipeline", "art", "style.json")))["palette"]}
    rnd = random.Random(1)
    rows = [[pal["paper-light"] if rnd.random() < 0.3 else pal["paper-mid"] for _ in range(w)] for _ in range(h)]
    for x in range(w):   # jagged rock silhouette
        top = int(h * (0.8 + 0.06 * math.sin(x / 3.0)))
        for y in range(top, h):
            rows[y][x] = pal["silhouette"]
    cx, cy, r = int(w * 0.75), int(h * 0.35), max(3, h // 5)
    for y in range(h):
        for x in range(w):
            if (x - cx) ** 2 + (y - cy) ** 2 < r * r:
                rows[y][x] = pal["owl-umber"]
    for x in range(w // 8, w // 2, 6):
        rows[h // 2][x] = pal["gold"]
    for x in (w // 3, w // 3 + 9):
        rows[h // 3][x] = pal["rust-red"]
    if teal:
        for y in range(h // 5, h // 5 + h // 2):
            for x in range(w // 3, w // 3 + w // 6):
                rows[y][x] = (42, 157, 143, 255)
    return rows


def keyart(w, h):
    """The key art scaled to w x h, cached in the temp folder (the stand-in game takes one shot per smoke)."""
    import tempfile
    from png import read_png
    cache = os.path.join(tempfile.gettempdir(), f"fake_shot_keyart_{w}x{h}.png")
    if os.path.isfile(cache):
        return read_png(cache)[2]
    kw, kh, rows = read_png(os.path.join(ROOT, "pipeline", "art", "reference", "target-keyart.png"))
    out = [[rows[y * kh // h][x * kw // w] for x in range(w)] for y in range(h)]
    write_png(cache + ".tmp", w, h, out)
    os.replace(cache + ".tmp", cache)
    return out


def main(argv):
    scale = 4 if "--keyart" in argv else 8
    out, w, h = argv[0], max(16, int(argv[1]) // scale), max(9, int(argv[2]) // scale)
    make = keyart if "--keyart" in argv else (lambda a, b: scene(a, b, "--flat-teal" in argv))
    if "--no-lock" in argv:
        rows = make(w, h)
    else:
        vw, vh = (round(h * 16 / 9), h) if w * 9 > h * 16 else (w, round(w * 9 / 16))
        inner = make(vw, vh)
        x0, y0 = (w - vw) // 2, (h - vh) // 2
        black = (0, 0, 0, 255)
        rows = [[black] * w for _ in range(h)]
        for y in range(vh):
            rows[y0 + y][x0:x0 + vw] = inner[y]
    write_png(out, w, len(rows), rows)


if __name__ == "__main__":
    main(sys.argv[1:])
