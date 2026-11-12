#!/usr/bin/env python3
"""Build the art-judge calibration set from the reference key art.

Writes known-bad variants next to the reference so both judges can be tested against
them. The LLM judge must reject all of them. The reference itself is the known-good G1.

  B1_colorful    hues rotated and saturation boosted ("colorful storybook" drift)
  B2_pixelated   downsampled 4x and upscaled with nearest-neighbour (pixel-art look)
  B4_grey_silh   near-black silhouettes lifted to mid grey
  B5_flat_white  paper texture replaced by flat near-white
  B6_gold_flood  top quarter of the frame painted accent gold (accents meant to be rare)
  B7_crushed     whole frame darkened to 25% (silhouettes lost in a black frame)

The numeric check must FAIL B1, B4, B5, B6 and B7 (B6 on accent_area, B7 on dark_share).

Usage: python3 tools/make_art_calibration.py pipeline/art/reference/target-keyart.png evals/art-judge/calibration
       python3 tools/make_art_calibration.py --swatch Art/Source/Swatch/Export/T_Swatch_Palette.png
  --swatch writes the palette-swatch sprite: one flat cell per style.json palette entry, in order,
  swatch.cols per row, swatch.cell_px square. art_check.py --swatch reads its in-engine capture.
"""
import json
import colorsys
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from png import read_png, write_png  # noqa: E402


def colorful(p):
    r, g, b, a = p
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    h = (h + 0.45) % 1.0
    s = min(1.0, s * 3 + 0.35) if v > 0.2 else s
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (int(r * 255), int(g * 255), int(b * 255), a)


def grey_silhouettes(p):
    r, g, b, a = p
    if max(r, g, b) < 60:
        return (115, 112, 110, a)
    return p


def flat_white(p):
    r, g, b, a = p
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    if v > 0.35 and s < 0.35:
        return (238, 236, 232, a)
    return p


GOLD = (0xE9, 0xB0, 0x4A)  # style.json "gold"; any accent color would do


def gold_flood(w, h, rows):
    out = [list(r) for r in rows]
    for y in range(h // 4):
        out[y] = [(GOLD[0], GOLD[1], GOLD[2], p[3]) for p in out[y]]
    return out


def crushed(p):
    r, g, b, a = p
    return (r // 4, g // 4, b // 4, a)


def pixelate(w, h, rows, f=4):
    out = []
    for y in range(h):
        sy = (y // f) * f
        out.append([rows[sy][(x // f) * f] for x in range(w)])
    return out


def swatch_rows(style):
    sw, pal = style["swatch"], style["palette"]
    cols, n = sw["cols"], sw["cell_px"]
    nrows = -(-len(pal) // cols)
    rgb = [tuple(int(c["hex"][i:i + 2], 16) for i in (1, 3, 5)) for c in pal]
    rows = []
    for y in range(nrows * n):
        row = []
        for x in range(cols * n):
            i = (y // n) * cols + x // n
            row.append(rgb[i] + (255,) if i < len(rgb) else (0, 0, 0, 0))
        rows.append(row)
    return rows


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) == 2 and argv[0] == "--swatch":
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(here, "pipeline", "art", "style.json"), encoding="utf-8") as f:
            rows = swatch_rows(json.load(f))
        write_png(argv[1], len(rows[0]), len(rows), rows)
        print(argv[1])
        return 0
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    src, out_dir = argv
    w, h, rows = read_png(src)
    os.makedirs(out_dir, exist_ok=True)
    variants = {
        "B1_colorful": [[colorful(p) for p in row] for row in rows],
        "B2_pixelated": pixelate(w, h, rows),
        "B4_grey_silh": [[grey_silhouettes(p) for p in row] for row in rows],
        "B5_flat_white": [[flat_white(p) for p in row] for row in rows],
        "B6_gold_flood": gold_flood(w, h, rows),
        "B7_crushed": [[crushed(p) for p in row] for row in rows],
    }
    for name, data in variants.items():
        path = os.path.join(out_dir, name + ".png")
        write_png(path, w, h, data)
        print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
