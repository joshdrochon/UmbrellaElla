#!/usr/bin/env python3
"""Flat filled boxes on a gameplay capture (visualqa item 5, lead order Nov 13 21:49). Stdlib only.

The Opus judge missed the Keeper's flat salmon warning band and the pale grey gust cube (C) on Josh's 1600x900 frames:
the gate's one keeper shot was taken between attacks, and a judge reads a small flat block as 'a cloud' or 'a card'.
This check needs no judgement: a box is a connected region of one flat colour that fills its bounding rectangle, has
hard edges against what is around it, and is big enough to see. Painted art (backdrops, islands, the Keeper, Ella) has
texture and soft or ragged edges; an untextured stand-in (a cube with a flat unlit tint) does not.

  flat_box.py IMAGE [IMAGE ...]   print one line per box; exit 1 when any image has one

Thresholds are shares of the frame so 1280x720 and 1600x900 captures read the same. Measured on the real captures in
tests/test_flat_box.py (pipeline/qa/visual/calibration/flatbox-*.png): the salmon band, the grey gust cube and a black
stand-in box are found; the Other Realm study, Josh's known-good frames and a Keeper frame between attacks give none.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import png  # noqa: E402  (tools/png.py)

# Analysis grid: every STEP-th pixel of a frame scaled to about 800 px wide.
GRID_W = 800
# A neighbour belongs to the region when every channel is within NEIGHBOUR_TOL of it and within SEED_TOL of the seed.
NEIGHBOUR_TOL = 3
SEED_TOL = 8
# Smallest box: MIN_AREA of the frame and MIN_SIDE of the frame height on each side (the 48x88 gust cube at 1280x720 is
# 0.46% of the frame; a 2 px light shaft or a thin HUD rule is not a box).
MIN_AREA = 0.0015
MIN_SIDE = 0.02
# A smaller box counts when it is crisp: its flat core alone fills SMALL_FILL of its rectangle and its edge contrast is at
# least SMALL_EDGE_CONTRAST (the 19x19 px lilac Keeper-head stand-in on fix-cast.png is 0.039% of a 1280x720 frame; its
# core fill is 1.0 and its edge against the red glow about 95). Smaller than SMALL_AREA is a spark or a HUD dot.
SMALL_AREA = 0.0003
SMALL_FILL = 0.95
SMALL_EDGE_CONTRAST = 36
# The region fills at least FILL of its bounding rectangle (a rectangle, not an organic shape). Cells of the rectangle
# reached from the flat core by smooth steps (each within NEIGHBOUR_TOL) count as the same box: lit shading on a flat
# stand-in (the red ring's glow over the grey wing box's lower-left on fix-cast.png left its flat core at 74%).
# The flat core itself must still fill CORE_FILL and be one flat tint (SHADE_EXACT of its cells the seed colour exactly:
# 0.48 on the grey wing box, at most 0.05 on dark painted sky, whose grain lets smooth steps wander), so a smooth
# gradient or a patch of sky is never a box.
FILL = 0.9
CORE_FILL = 0.5
SHADE_EXACT = 0.25
# A region on the frame edge is the backdrop or a letterbox only when it runs along most of that edge (EDGE_SPAN); the
# salmon warning band on shot-250.png touches the top edge but spans 52% of it. It must also be one flat tint
# (SHADE_EXACT) and touch one edge only: dark sky filling the top-right corner of a Director's Cut route shot
# (638x109, exact share low) is backdrop.
EDGE_SPAN = 0.8
# Hard edge: the mean channel difference between the region's border and a ring EDGE_RING grid cells outside it.
EDGE_CONTRAST = 18
EDGE_RING = 2
# A region of one exact colour (EXACT share of its cells equal to the seed) is never painted art (every painted surface
# and backdrop carries grain); it needs only EXACT_EDGE_CONTRAST (the pure-black box over Ella on the dark Keeper sky,
# vk_09: #000000 against about #0e0c0b, contrast 12; its exact share is 0.95 on the 800 px fixture, 1.0 at 1600).
EXACT = 0.9
EXACT_EDGE_CONTRAST = 8


def _grid(path):
    w, h, rows = png.read_png(path)
    step = max(1, w // GRID_W)
    gw, gh = w // step, h // step
    grid = [[rows[y * step][x * step][:3] for x in range(gw)] for y in range(gh)]
    return w, h, step, grid


def _close(a, b, tol):
    return abs(a[0] - b[0]) <= tol and abs(a[1] - b[1]) <= tol and abs(a[2] - b[2]) <= tol


def _edge_contrast(grid, x0, y0, x1, y1, seed):
    """Mean channel difference between the seed colour and the ring EDGE_RING cells outside the box (cells inside the
    frame only). A box drawn over the scene stands out from it all round; a flat patch of sky fades into more sky."""
    gh, gw = len(grid), len(grid[0])
    total, n = 0, 0
    for x in range(x0, x1 + 1):
        for y in (y0 - EDGE_RING, y1 + EDGE_RING):
            if 0 <= y < gh:
                c = grid[y][x]
                total += (abs(c[0] - seed[0]) + abs(c[1] - seed[1]) + abs(c[2] - seed[2])) / 3.0
                n += 1
    for y in range(y0, y1 + 1):
        for x in (x0 - EDGE_RING, x1 + EDGE_RING):
            if 0 <= x < gw:
                c = grid[y][x]
                total += (abs(c[0] - seed[0]) + abs(c[1] - seed[1]) + abs(c[2] - seed[2])) / 3.0
                n += 1
    return total / n if n else 0.0


def _shaded_fill(grid, cells, x0, y0, x1, y1):
    """Share of the rectangle covered by the flat core plus the cells reached from it by smooth steps (each within
    NEIGHBOUR_TOL of the cell it came from), staying inside the rectangle: a lit or shaded part of the same box."""
    inside = set(cells)
    stack = list(cells)
    while stack:
        x, y = stack.pop()
        c = grid[y][x]
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if x0 <= nx <= x1 and y0 <= ny <= y1 and (nx, ny) not in inside and _close(c, grid[ny][nx], NEIGHBOUR_TOL):
                inside.add((nx, ny))
                stack.append((nx, ny))
    return len(inside) / float((x1 - x0 + 1) * (y1 - y0 + 1))


def find_boxes(path):
    """Flat filled boxes in a capture: [{x, y, w, h, rgb, fill, edge}] in frame pixels, largest first."""
    w, h, step, grid = _grid(path)
    gh, gw = len(grid), len(grid[0])
    seen = bytearray(gw * gh)
    min_cells = MIN_AREA * gw * gh
    small_cells = SMALL_AREA * gw * gh
    min_side = MIN_SIDE * gh
    out = []
    # Seeds inside flat interiors first (a cell equal to its right and lower neighbours), so a box is grown from its own
    # colour before a near-black backdrop seed can take part of it (the black box in vk_09 was split that way).
    flat = [(sx, sy) for sy in range(gh - 1) for sx in range(gw - 1)
            if grid[sy][sx] == grid[sy][sx + 1] == grid[sy + 1][sx]]
    rest = [(sx, sy) for sy in range(gh) for sx in range(gw)]
    for sx, sy in flat + rest:
            if seen[sy * gw + sx]:
                continue
            seed = grid[sy][sx]
            stack = [(sx, sy)]
            seen[sy * gw + sx] = 1
            cells = []
            exact = 0
            x0 = x1 = sx
            y0 = y1 = sy
            while stack:
                x, y = stack.pop()
                cells.append((x, y))
                if x < x0:
                    x0 = x
                elif x > x1:
                    x1 = x
                if y < y0:
                    y0 = y
                elif y > y1:
                    y1 = y
                c = grid[y][x]
                exact += c == seed
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if 0 <= nx < gw and 0 <= ny < gh and not seen[ny * gw + nx]:
                        d = grid[ny][nx]
                        if _close(c, d, NEIGHBOUR_TOL) and _close(seed, d, SEED_TOL):
                            seen[ny * gw + nx] = 1
                            stack.append((nx, ny))
            count = len(cells)
            bw, bh = x1 - x0 + 1, y1 - y0 + 1
            if bw < min_side or bh < min_side or count < small_cells:
                continue
            core_fill = count / float(bw * bh)
            if core_fill < CORE_FILL:
                continue
            # Edge-touching regions: skip the ones that run along most of the edge they touch.
            touches = (y0 == 0) + (y1 == gh - 1) + (x0 == 0) + (x1 == gw - 1)
            if touches and (touches > 1 or exact < SHADE_EXACT * count or
                            ((y0 == 0 or y1 == gh - 1) and bw >= EDGE_SPAN * gw) or
                            ((x0 == 0 or x1 == gw - 1) and bh >= EDGE_SPAN * gh)):
                continue
            edge = _edge_contrast(grid, x0, y0, x1, y1, seed)
            if count < min_cells:
                if core_fill < SMALL_FILL or edge < SMALL_EDGE_CONTRAST:
                    continue
                fill = core_fill
            else:
                fill = core_fill
                if fill < FILL and exact >= SHADE_EXACT * count:
                    fill = _shaded_fill(grid, cells, x0, y0, x1, y1)
                if fill < FILL:
                    continue
                if edge < (EXACT_EDGE_CONTRAST if exact >= EXACT * count else EDGE_CONTRAST):
                    continue
            out.append({"x": x0 * step, "y": y0 * step, "w": bw * step, "h": bh * step, "rgb": "#%02x%02x%02x" % seed,
                        "fill": round(fill, 3), "edge": round(edge, 1)})
    out.sort(key=lambda b: -b["w"] * b["h"])
    return out


def describe(box):
    """One 'broken to a player' item for a box (defect kind 'box' in visual_qa.DEFECT_KINDS)."""
    return "flat filled box %dx%d px at (%d,%d) colour %s over the play space (untextured stand-in) [detector]" % (
        box["w"], box["h"], box["x"], box["y"], box["rgb"])


def same_box(a, b):
    """True when two boxes are the same stand-in seen in two captures: colour close, size within half. Place is not
    compared (a gust cube travels; the Keeper's band sits at Ella's altitude)."""
    ca = [int(a["rgb"][i:i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b["rgb"][i:i + 2], 16) for i in (1, 3, 5)]
    if max(abs(p - q) for p, q in zip(ca, cb)) > 40:
        return False
    ra, rb = a["w"] * a["h"], b["w"] * b["h"]
    return 0.5 <= ra / float(max(rb, 1)) <= 2.0


def main(argv):
    found = 0
    for path in argv:
        for box in find_boxes(path):
            found += 1
            print("FLAT_BOX %s %s" % (path, describe(box)))
    print("FLAT_BOX %s: %d box(es) in %d image(s)" % ("FAIL" if found else "PASS", found, len(argv)))
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
