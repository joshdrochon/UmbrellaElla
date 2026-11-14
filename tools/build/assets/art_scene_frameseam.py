#!/usr/bin/env python3
"""Straight-edge seam check for a captured game frame (dcseamless, Josh Nov 13: the DC route background must read as one
seamless painted world, no picture edges, panels or frame borders). Stdlib only.

  python3 tools/build/assets/art_scene_frameseam.py <frame.png> [...] [--ella-x X]   exit 0 PASS, 1 FAIL

A picture or panel edge is a straight line where the luminance jumps on MOST pixels along it; painted content does not.
Column score = median over rows of |L(x+1) - L(x)| (luma 0-255); row score = median over columns of |L(y+1) - L(y)|.
Excluded: Ella's rope (+-ROPE_PAD px around her drawn x, read from the capture's journey.log, else --ella-x, else the
centre), the HUD (top HUD_ROWS rows, left HUD_COLS columns) and the route floor bar band (FLOOR_BAND rows).
FAIL when any column or row scores SEAM_LIMIT or more.

Measured on the DC route sweep (45 shots at 1280x720, start to Keeper; dcseamless status), before the fix: start picture
right edge 5.0-7.2, end picture left edge 3.8-4.8, arena stand-in plane edges 3.0-5.1 (col) / 3.0 (row 53); every painted
frame without one of those edges scored at most 2.8 (straight island tops in the end picture: 2.2-2.9).
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))
import png  # noqa: E402  (tools/png.py, stdlib PNG reader)

SEAM_LIMIT = 3.0     # median jump (luma levels) along a whole line that a player sees as an edge; painted max was 2.9
ROPE_PAD = 18        # px each side of Ella's x (her umbrella rope is a straight vertical line)
HUD_ROWS = 40
HUD_COLS = 170
FLOOR_BAND = (620, 666)   # the route floor bar (a level piece, not the backdrop)


def luma_rows(path):
    w, h, rows = png.read_png(path)
    return w, h, [[0.2126 * p[0] + 0.7152 * p[1] + 0.0722 * p[2] for p in row] for row in rows]


def median(values):
    s = sorted(values)
    n = len(s)
    return 0.0 if n == 0 else (s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2]))


def ella_x_from_log(path):
    log = os.path.join(os.path.dirname(path), "journey.log")
    name = os.path.basename(path)
    try:
        with open(log, errors="replace") as fh:
            for line in fh:
                if name in line:
                    m = re.search(r"ella=drawn\((\d+),", line)
                    if m:
                        return int(m.group(1))
    except OSError:
        pass
    return None


def frame_scores(w, h, L, ella_x):
    """(column scores, row scores): median absolute luma step across each column / row boundary, exclusions zeroed."""
    lo, hi = FLOOR_BAND
    rows = [y for y in range(HUD_ROWS, h) if not lo <= y < hi]
    col = [0.0] * (w - 1)
    for x in range(w - 1):
        if 2 <= x and abs(x - ella_x) > ROPE_PAD:
            col[x] = median([abs(L[y][x + 1] - L[y][x]) for y in rows])
    cols = [x for x in range(HUD_COLS, w) if abs(x - ella_x) > ROPE_PAD]
    row = [0.0] * (h - 1)
    for y in range(HUD_ROWS, h - 1):
        if not lo <= y < hi:
            row[y] = median([abs(L[y + 1][x] - L[y][x]) for x in cols])
    return col, row


def check(path, ella_x=None):
    w, h, L = luma_rows(path)
    ex = ella_x if ella_x is not None else (ella_x_from_log(path) or w // 2)
    col, row = frame_scores(w, h, L, ex)
    cx = max(range(len(col)), key=col.__getitem__)
    ry = max(range(len(row)), key=row.__getitem__)
    return col[cx], cx, row[ry], ry


def main(argv):
    ella = None
    paths = []
    it = iter(argv)
    for a in it:
        if a == "--ella-x":
            ella = int(next(it))
        else:
            paths.append(a)
    if not paths:
        print(__doc__)
        return 2
    worst = 0.0
    for p in paths:
        c, cx, r, ry = check(p, ella)
        worst = max(worst, c, r)
        print("%s col_max=%.1f@x%d row_max=%.1f@y%d %s" % (os.path.basename(p), c, cx, r, ry,
                                                            "FAIL" if max(c, r) >= SEAM_LIMIT else "ok"))
    ok = worst < SEAM_LIMIT
    print("FRAMESEAM %s frames=%d worst=%.1f limit=%.1f" % ("PASS" if ok else "FAIL", len(paths), worst, SEAM_LIMIT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
