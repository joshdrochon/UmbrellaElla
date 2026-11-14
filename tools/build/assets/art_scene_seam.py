#!/usr/bin/env python3
"""Seam check for a picture tiled side by side (GDD BG-02: qualify seams and tileability for each new asset). Stdlib only.

  python3 tools/build/assets/art_scene_seam.py <post.png> <x0> <x1> <N>
      <post.png> was made by art_scene_world.py with a box x0..x1 (fractions of the width) and mode repeatN.
      Measures every join between copies; exit 0 PASS, 1 FAIL.

A join is where copy i ends and copy i+1 starts. Its score compares the BAND columns on each side, row by row
(column_pair_score). PASS when every join scores no more than the picture's own 90th percentile of neighbouring band
pairs inside it (interior_limit): the join may be no rougher than the painting itself.

Measured before the fix (artscene, Nov 13): skyline r6 post joins 0.84 / 0.84 (interior p90 0.40), clock r3 post 0.71
(p90 0.42), skyline r4 post 0.92 (p90 0.53): each picture was cut by its canvas edge. art_scene_world.py repeatN now
cross-fades the ends (tileable()), which makes the join two neighbouring source columns.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))
import png  # noqa: E402  (tools/png.py, stdlib PNG reader)

INTERIOR_Q = 0.90   # a join may be no rougher than the picture's own 90th-percentile neighbouring bands
SEAM_FLOOR = 0.05   # a flat, noise-free picture has an interior p90 near 0; a 5% step over 2 x BAND px is not visible
INTERIOR_STEP = 37  # sample spacing in columns (prime, so it does not beat against a repeat)
CONTENT_ALPHA = 0.05
BAND = 8   # px each side of a join (the 2 px crop pad cannot hide a cut island)


def band_stats(row, x_from, x_to):
    """Max alpha and mean premultiplied RGB over columns [x_from, x_to) of one row."""
    px = row[max(0, x_from):x_to]
    if not px:
        return 0.0, (0.0, 0.0, 0.0)
    amax = max(p[3] for p in px)
    mean = tuple(sum(p[c] * p[3] for p in px) / len(px) for c in range(3))
    return amax, mean


def column_pair_score(rows, x_left, x_right, band=None):
    """Seam score between the band ending at column x_left and the band starting at x_right.

    Per row: |max alpha left - max alpha right| + mean |premultiplied colour left - right| over the two bands of
    BAND columns. A picture cut by the edge of its canvas leaves content on one side and an empty band on the
    other (score near 1 on every row it crosses); a painting that carries on across the join scores like any
    neighbouring pair of bands inside it. Mean over the rows where either band shows something."""
    band = BAND if band is None else band
    total, count = 0.0, 0
    for row in rows:
        al, cl = band_stats(row, x_left + 1 - band, x_left + 1)
        ar, cr = band_stats(row, x_right, x_right + band)
        if al < CONTENT_ALPHA and ar < CONTENT_ALPHA:
            continue
        total += abs(al - ar) + sum(abs(cl[c] - cr[c]) for c in range(3)) / 3.0
        count += 1
    return total / count if count else 0.0


def join_columns(width, x0, x1, n):
    """Columns (last of copy i, first of copy i+1) for each inner join, matching art_scene_world.place()."""
    w = int((x1 - x0) * width / n)
    left = int(x0 * width)
    return [(left + i * w - 1, left + i * w) for i in range(1, n)]


def crossfade_weights(fade):
    """Weight of the tile's original START at each of the first `fade` columns of the tileable piece (0 -> 1).

    The tileable piece is: columns [0, fade) = lerp(src[w - fade + j], src[j], t_j), then src[fade : w - fade].
    Its last column is src[w - fade - 1] and, when tiled, the next column is lerp at j = 0 = src[w - fade]: two
    neighbouring source columns, so the join is as smooth as the painting itself.
    """
    if fade <= 1:
        return [1.0] * max(fade, 0)
    return [j / (fade - 1) for j in range(fade)]


def make_tileable(row, fade):
    """Pure-python reference of the numpy cross-fade in art_scene_world.tileable() for one row of pixels."""
    w = len(row)
    out = []
    for j, t in enumerate(crossfade_weights(fade)):
        a, b = row[w - fade + j], row[j]
        out.append(tuple(a[c] * (1 - t) + b[c] * t for c in range(len(a))))
    return out + list(row[fade:w - fade])


def load_rows(path):
    _w, _h, rows = png.read_png(path)
    return [[tuple(c / 255.0 for c in px) for px in row] for row in rows]


def interior_limit(rows, step=INTERIOR_STEP, skip=()):
    """The picture's own INTERIOR_Q quantile of band-pair scores, sampled every `step` columns away from the joins."""
    width = len(rows[0])
    near = set()
    for xl, xr in skip:
        near.update(range(xl - 2 * BAND, xr + 2 * BAND))
    scores = sorted(column_pair_score(rows, x, x + 1) for x in range(BAND, width - BAND - 1, step) if x not in near)
    if not scores:
        return SEAM_FLOOR
    return max(SEAM_FLOOR, scores[int(INTERIOR_Q * (len(scores) - 1))])


def check(path, x0, x1, n):
    rows = load_rows(path)
    joins = join_columns(len(rows[0]), x0, x1, n)
    limit = interior_limit(rows, skip=joins)
    scores = [(xl, xr, column_pair_score(rows, xl, xr)) for xl, xr in joins]
    ok = all(s <= limit for _, _, s in scores)
    return ok, scores, limit


def main(argv):
    if len(argv) != 4:
        print(__doc__)
        return 2
    path, x0, x1, n = argv[0], float(argv[1]), float(argv[2]), int(argv[3])
    ok, scores, limit = check(path, x0, x1, n)
    for xl, xr, s in scores:
        print("seam join x=%d|%d score %.3f (limit %.3f = interior p%d, floor %.2f) %s"
              % (xl, xr, s, limit, int(INTERIOR_Q * 100), SEAM_FLOOR, "PASS" if s <= limit else "FAIL"))
    print("SEAM %s %s" % ("PASS" if ok else "FAIL", path))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
