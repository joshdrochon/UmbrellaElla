#!/usr/bin/env python3
"""Measure the Keeper box of a gameplay capture: no cream paper box, no lilac stand-in square (numbers only).

  python3 tools/build/assets/art_keeper_box_check.py <capture.png> [...]

The Keeper box is where AUmbrellaArena puts the Keeper at the play camera (KeeperAnchorX/ZFraction, 600 px of 1080):
x 0.594-0.906, y 0.122-0.678 of the frame (measured on pipeline/art/proof/screenfix/b2-ella-1280.png: cream box
760-1160 x 88-488 at 1280x720). Every pixel there is classed:
  lilac  = the stand-in colour (UmbrellaArtSlotConst::StandInKeeperColor, ~ (192,176,216) on screen): blue highest,
           green lowest, all channels > 140, blue - green > 25
  cream  = paper: all channels > 200, r >= g >= b, r - b < 45 (the clock's pale green face has g > r, so it is not cream)
PASS when lilac < 0.5 % and cream < 5 % of the box. Prints the shares and a 5x5 grid of sampled pixels.
Exit 1 on any FAIL.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from png import read_png  # noqa: E402  (tools/png.py)

KEEPER_BOX = (0.594, 0.122, 0.906, 0.678)
KEEPER_LILAC_MAX = 0.005
KEEPER_CREAM_MAX = 0.05


def keeper_is_lilac(r, g, b):
    return min(r, g, b) > 140 and b > r > g and b - g > 25


def keeper_is_cream(r, g, b):
    return min(r, g, b) > 200 and r >= g >= b and r - b < 45


def keeper_box_check(path):
    w, h, rows = read_png(path)
    x0, y0, x1, y1 = (int(KEEPER_BOX[0] * w), int(KEEPER_BOX[1] * h), int(KEEPER_BOX[2] * w), int(KEEPER_BOX[3] * h))
    total = lilac = cream = 0
    for y in range(y0, y1):
        row = rows[y]
        for x in range(x0, x1):
            r, g, b = row[x][:3]
            total += 1
            lilac += keeper_is_lilac(r, g, b)
            cream += keeper_is_cream(r, g, b)
    grid = [[tuple(rows[y0 + (y1 - y0 - 1) * j // 4][x0 + (x1 - x0 - 1) * i // 4][:3]) for i in range(5)] for j in range(5)]
    ok = lilac / total < KEEPER_LILAC_MAX and cream / total < KEEPER_CREAM_MAX
    print("keeper_box_check: %s %s %dx%d box=(%d,%d)-(%d,%d) lilac=%.4f cream=%.4f (max %.3f / %.3f)" % (
        "PASS" if ok else "FAIL", path, w, h, x0, y0, x1, y1, lilac / total, cream / total, KEEPER_LILAC_MAX, KEEPER_CREAM_MAX))
    for line in grid:
        print("  " + " ".join("(%3d,%3d,%3d)" % p for p in line))
    return ok


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    results = [keeper_box_check(p) for p in sys.argv[1:]]
    sys.exit(0 if all(results) else 1)
