#!/usr/bin/env python3
"""Ella as a small dark figure with a warm rim, the way she reads in Ricky's Other Realm study (bar-other-realm).

  python3 tools/build/assets/art_ella_silhouette.py <in.png> <out.png> --cols C --rows R [--cell-h 160]

Numbers only, no model: takes an in-jam Ella sheet (the stand-in grid the slot already draws), keeps its layout
(C x R cells, same cell aspect, same figure placement), and per cell
  1. thickens thin parts a little (umbrella shaft, scarf ends) so they survive the downscale,
  2. downsizes to about the size the game draws one cell (the slot imports with no mips, so a huge cell aliases),
  3. maps the figure's own light and dark into the study's dark warm range (body p10/p50/p95 below),
  4. adds a warm rim on the edges that face the light (up and to the left, the gold trail side), brightest on the
     umbrella canopy's top edge, and a faint all-round edge so the figure separates from a dark sky.
Transparent outside the figure: no paper, no frame, no border. Needs Pillow and numpy.

Colours are measured on the study (pipeline/art/reference/discord/20261111-0318_Ricky_other-realm.png, Ella's body,
head and canopy): darks (19,18,16), mids (44,36,31), lights (123,95,72), lit canopy edge (245,201,141).
Shots gold #E9C46A (art bible) is the rim's top colour.
"""
import argparse
import sys

import numpy as np
from PIL import Image, ImageFilter

STUDY_DARK = np.array([19.0, 18.0, 16.0])
STUDY_MID = np.array([44.0, 36.0, 31.0])
STUDY_LIGHT = np.array([123.0, 95.0, 72.0])
RIM_GOLD = np.array([233.0, 196.0, 106.0])      # #E9C46A
RIM_CANOPY = np.array([245.0, 201.0, 141.0])
EDGE_WARM = np.array([66.0, 52.0, 40.0])         # faint all-round edge
LIGHT_DIR = (-0.55, -0.83)                        # towards the light: left and up (x, y in image space)
RIM_STEPS = 2                                     # rim width in output pixels
RIM_STRENGTH = 0.75
EDGE_STRENGTH = 0.35
CANOPY_SHARE = 0.27                               # top share of the figure's height that is the umbrella canopy
THICKEN_SRC_PX = 5                                # max-filter size on the source alpha before the downscale
ALPHA_CUT = 0.04
CORE_PX = 7                                       # parts thinner than this (output px) get no rim
CANOPY_TOP_GAIN = 1.0
TONE_GAMMA = 1.4                                  # most of the figure sits in the darks, as in the study
LIGHT_CAP = 0.8                                   # the brightest body tone stops short of the study's lights; the rim carries the light
INTERIOR_BLUR = 0.8                               # px at output size: drops interior line noise, keeps the outline
KEY_FRINGE_SAT = 0.45                             # saturated yellow pixels in the source are key spill, painted dark


def shift(a, dx, dy):
    """a sampled at p + (dx, dy), zero outside (integer shift)."""
    out = np.zeros_like(a)
    h, w = a.shape
    xs0, xs1 = max(0, dx), min(w, w + dx)
    ys0, ys1 = max(0, dy), min(h, h + dy)
    out[max(0, -dy):max(0, -dy) + (ys1 - ys0), max(0, -dx):max(0, -dx) + (xs1 - xs0)] = a[ys0:ys1, xs0:xs1]
    return out


def tone(lum):
    """Map 0..1 source luminance to the study's dark warm ramp (piecewise linear dark -> mid -> light)."""
    lum = lum[..., None]
    low = STUDY_DARK + (STUDY_MID - STUDY_DARK) * np.clip(lum / 0.5, 0, 1)
    high = STUDY_MID + (STUDY_LIGHT - STUDY_MID) * np.clip((lum - 0.5) / 0.5, 0, 1)
    return np.where(lum < 0.5, low, high)


def cell(src, out_w, out_h):
    """One cell -> silhouette RGBA at out_w x out_h."""
    rgba = src.convert("RGBA")
    alpha = rgba.getchannel("A").filter(ImageFilter.MaxFilter(THICKEN_SRC_PX))
    # premultiplied downscale so the transparent pixels' colour never bleeds in
    arr = np.asarray(rgba).astype(np.float64) / 255.0
    rgb_src = arr[..., :3]
    mx, mn = rgb_src.max(-1), rgb_src.min(-1)
    sat = (mx - mn) / np.maximum(mx, 1e-3)
    fringe = (sat > KEY_FRINGE_SAT) & (rgb_src[..., 2] < rgb_src[..., 0] * 0.6)
    lum_raw = rgb_src @ np.array([0.299, 0.587, 0.114])
    lum_raw = np.where(fringe, 0.0, lum_raw)
    lum_src = lum_raw * arr[..., 3]
    lum_img = Image.fromarray(np.clip(lum_src * 255, 0, 255).astype(np.uint8)).resize((out_w, out_h), Image.LANCZOS)
    lum_img = lum_img.filter(ImageFilter.GaussianBlur(INTERIOR_BLUR))
    a0_img = rgba.getchannel("A").resize((out_w, out_h), Image.LANCZOS)
    a_img = alpha.resize((out_w, out_h), Image.LANCZOS)
    a0 = np.asarray(a0_img).astype(np.float64) / 255.0
    a = np.asarray(a_img).astype(np.float64) / 255.0
    lum = np.where(a0 > 1e-3, np.asarray(lum_img).astype(np.float64) / 255.0 / np.maximum(a0, 1e-3), 0.0)
    lum = np.clip(lum, 0, 1)
    # stretch the figure's own range so its darks and lights use the whole ramp
    inside = a0 > 0.5
    if inside.any():
        lo, hi = np.percentile(lum[inside], 5), np.percentile(lum[inside], 97)
        lum = np.clip((lum - lo) / max(hi - lo, 1e-3), 0, 1)
    rgb = tone(LIGHT_CAP * lum ** TONE_GAMMA)

    solid = (a > 0.5).astype(np.float64)
    rim = np.zeros_like(a)
    for k in range(1, RIM_STEPS + 1):
        dx, dy = int(round(LIGHT_DIR[0] * k)), int(round(LIGHT_DIR[1] * k))
        rim = np.maximum(rim, solid * (1.0 - shift(solid, dx, dy)) * (1.0 - 0.6 * (k - 1) / max(RIM_STEPS - 1, 1)))
    # thin streaming parts (hair, scarf ends) stay dark: the rim only sits on the body's core (a morphological
    # opening of CORE_PX drops everything thinner), grown back by RIM_STEPS so the core's own edge keeps its rim
    solid_img = Image.fromarray((solid * 255).astype(np.uint8))
    core = solid_img.filter(ImageFilter.MinFilter(CORE_PX)).filter(ImageFilter.MaxFilter(CORE_PX + 2 * RIM_STEPS))
    rim = rim * (np.asarray(core).astype(np.float64) / 255.0)
    edge = solid * (1.0 - np.minimum.reduce([shift(solid, 1, 0), shift(solid, -1, 0), shift(solid, 0, 1), shift(solid, 0, -1)]))

    ys = np.nonzero(solid.any(axis=1))[0]
    rim_col = np.broadcast_to(RIM_GOLD, rgb.shape).copy()
    if ys.size:
        top, bottom = ys.min(), ys.max()
        canopy_rows = np.arange(out_h) <= top + CANOPY_SHARE * (bottom - top)
        rim_col[canopy_rows] = RIM_CANOPY
        # the canopy is lit from straight above along its whole top edge, as in the study
        top_edge = solid * (1.0 - shift(solid, 0, -1)) * canopy_rows[:, None]
        rim = np.maximum(rim, top_edge * CANOPY_TOP_GAIN)
    rgb = rgb * (1 - EDGE_STRENGTH * edge[..., None]) + EDGE_WARM * EDGE_STRENGTH * edge[..., None]
    rgb = rgb * (1 - RIM_STRENGTH * rim[..., None]) + rim_col * RIM_STRENGTH * rim[..., None]

    a = np.where(a < ALPHA_CUT, 0.0, a)
    out = np.dstack([np.clip(rgb, 0, 255), a * 255.0]).astype(np.uint8)
    out[a == 0] = 0
    return Image.fromarray(out, "RGBA")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--cols", type=int, required=True)
    ap.add_argument("--rows", type=int, required=True)
    ap.add_argument("--cell-h", type=int, default=160, help="output cell height in px (about the drawn size)")
    args = ap.parse_args(argv)
    src = Image.open(args.src)
    cw, ch = src.width // args.cols, src.height // args.rows
    out_h = args.cell_h
    out_w = max(1, int(round(out_h * cw / ch)))
    sheet = Image.new("RGBA", (out_w * args.cols, out_h * args.rows), (0, 0, 0, 0))
    for r in range(args.rows):
        for c in range(args.cols):
            box = (c * cw, r * ch, (c + 1) * cw, (r + 1) * ch)
            sheet.paste(cell(src.crop(box), out_w, out_h), (c * out_w, r * out_h))
    sheet.save(args.out)
    print("silhouette: %s %dx%d cells %dx%d (src cell %dx%d, aspect %.4f -> %.4f)"
          % (args.out, sheet.width, sheet.height, out_w, out_h, cw, ch, cw / ch, out_w / out_h))
    return 0


if __name__ == "__main__":
    sys.exit(main())
