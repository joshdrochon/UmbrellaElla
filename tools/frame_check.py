#!/usr/bin/env python3
"""tools/frame_check.py: a game capture must show something: fail a mostly-black or mostly-flat frame.

Why (screenfix): a real render of the Mill room came out black (lit cubes, no light) or one flat grey (a backdrop
covering the play layer; the camera centred on the wrong place). screen_check.py judges the art style; this one only
says "the frame has content".
  black  share of near-black pixels (all channels <= --black-level) at or above --black-max (default 0.50)
  flat   share of the single most common colour (channels quantised by --quant) at or above --flat-max (default 0.90)
Usage: python3 tools/frame_check.py <capture.png> [--black-max F] [--flat-max F]
Prints `frame_check: PASS|FAIL image=<p> black=<share> flat=<share> ...` and exits 0 (pass) or 1 (fail)."""
import argparse
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from png import read_png  # noqa: E402

BLACK_LEVEL = 12
BLACK_MAX = 0.50
FLAT_MAX = 0.90
QUANT = 8


def measure(path, black_level=BLACK_LEVEL, quant=QUANT):
    """Return (black share, top-colour share, top colour) of the whole frame."""
    w, h, rows = read_png(path)
    total = w * h
    black = 0
    counts = Counter()
    for row in rows:
        for p in row:
            if p[0] <= black_level and p[1] <= black_level and p[2] <= black_level:
                black += 1
            counts[(p[0] // quant, p[1] // quant, p[2] // quant)] += 1
    colour, n = counts.most_common(1)[0]
    return black / total, n / total, tuple(c * quant for c in colour)


def check(path, black_max=BLACK_MAX, flat_max=FLAT_MAX):
    black, flat, colour = measure(path)
    problems = []
    if black >= black_max:
        problems.append("mostly black: %.0f%% of the frame is near-black (lit placeholders with no light?)" % (black * 100))
    if flat >= flat_max:
        problems.append("mostly flat: %.0f%% of the frame is one colour %s (a backdrop covering the play layer?)" % (flat * 100, colour))
    return dict(pass_=not problems, black=black, flat=flat, colour=colour, problems=problems)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("image")
    ap.add_argument("--black-max", type=float, default=BLACK_MAX)
    ap.add_argument("--flat-max", type=float, default=FLAT_MAX)
    a = ap.parse_args(argv)
    res = check(a.image, a.black_max, a.flat_max)
    print("frame_check: %s image=%s black=%.3f flat=%.3f top_colour=%s" % ("PASS" if res["pass_"] else "FAIL", a.image, res["black"], res["flat"], res["colour"]))
    for p in res["problems"]:
        print("  - " + p)
    return 0 if res["pass_"] else 1


if __name__ == "__main__":
    sys.exit(main())
