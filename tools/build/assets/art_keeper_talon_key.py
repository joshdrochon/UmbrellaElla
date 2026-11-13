"""Key the cream paper off a Keeper stand-in drawn on paper (Blender python: numpy + bpy; numbers only, no model).

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P tools/build/assets/art_keeper_talon_key.py -- \
      <in.png> <out.png> [--line-px N] [--holes]
  Used for keeper-talon, keeper-wing and keeper-mech-front (pipeline/art/proof/standins/<piece>/move_final2.png ->
  move_final2_keyed.png; mech-front with --line-px 3 --holes for its drawn frame line and chain-enclosed pockets).

Those sources are RGB: ink on cream paper, so each slot drew a paper box over the whole Keeper.
Method: a dark surround touching the border (a photographed sheet edge) is background; the paper is the light region
reachable from the border or that surround (a flood fill that stops at the ink outlines, so pale highlights inside an
outline stay). --line-px N also lets the flood cross ink lines up to 2N px wide drawn on the paper itself (a frame). Thin paper fibres and small specks left in that region are closed
over; any opaque island smaller than the talons is dropped. Edges get a 1 px soft step. Writes straight-alpha RGBA.
"""
import sys

import bpy
import numpy as np

TALON_KEY_PAPER_LUMA = 0.56      # paper and its smudges are lighter than this; ink outlines are far darker
TALON_KEY_PAPER_WARMTH = 0.30    # paper red minus blue stays under this (the brass bands are warmer)
TALON_KEY_FIBRE_PX = 4           # close fibres/specks up to ~2x this wide that sit inside the paper
TALON_KEY_ISLAND_PX = 14         # an opaque island must survive this much erosion to count as talon
TALON_KEY_SURROUND_LUMA = 0.30   # a sheet's dark surround is darker than this
TALON_KEY_SURROUND_REACH_PX = 6  # paper starts within this many px of the surround (the sheet's torn edge)
TALON_KEY_HOLE_COLOUR = 0.07     # --holes: an enclosed pixel this close (RGB distance) to the median paper is paper
TALON_KEY_HOLE_CORE_PX = 8       # --holes: an enclosed paper pocket must survive this much erosion (not a highlight)


def talon_shift(m, dy, dx):
    out = np.zeros_like(m)
    h, w = m.shape
    out[max(dy, 0):h + min(dy, 0), max(dx, 0):w + min(dx, 0)] = m[max(-dy, 0):h + min(-dy, 0), max(-dx, 0):w + min(-dx, 0)]
    return out


def talon_dilate(m, r):
    for _ in range(r):
        m = m | talon_shift(m, 1, 0) | talon_shift(m, -1, 0) | talon_shift(m, 0, 1) | talon_shift(m, 0, -1)
    return m


def talon_erode(m, r):
    return ~talon_dilate(~m, r)


def talon_reconstruct(seed, within):
    """Geodesic flood: grow seed inside `within` until it stops."""
    cur = seed & within
    while True:
        for _ in range(16):
            cur = talon_dilate(cur, 1) & within
        nxt = talon_dilate(cur, 1) & within
        if np.array_equal(nxt, cur):
            return cur
        cur = nxt


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    src, dst = args[0], args[1]
    line_px = int(args[args.index("--line-px") + 1]) if "--line-px" in args else 0
    im = bpy.data.images.load(src)
    w, h = im.size
    px = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)
    rgb = px[..., :3]
    luma = rgb @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    paperish = (luma > TALON_KEY_PAPER_LUMA) & ((rgb[..., 0] - rgb[..., 2]) < TALON_KEY_PAPER_WARMTH)
    border = np.zeros_like(paperish)
    border[0, :] = border[-1, :] = border[:, 0] = border[:, -1] = True
    surround = talon_reconstruct(border, luma < TALON_KEY_SURROUND_LUMA)
    # A surround only counts when it is a frame around the sheet, not a figure touching the edge: keep it if it is thin.
    if surround.mean() > 0.25:
        surround[:] = False
    border = border | talon_dilate(surround, TALON_KEY_SURROUND_REACH_PX)
    if line_px:
        paperish = paperish | talon_erode(talon_dilate(paperish, line_px), line_px)
    paper = talon_reconstruct(border, paperish) | surround
    # Fibres and specks sitting in the paper: close the paper over them (dilate then erode), then flood again from
    # the border so a closed gap inside a talon outline never opens.
    closed = talon_erode(talon_dilate(paper, TALON_KEY_FIBRE_PX), TALON_KEY_FIBRE_PX)
    paper = talon_reconstruct(border, closed | paper) | surround
    if "--holes" in args:
        # Paper pockets enclosed by ink (inside a chain loop): paper-coloured, and wide enough not to be a highlight.
        median = np.median(rgb[paper & ~surround], axis=0)
        near = (np.linalg.norm(rgb - median, axis=-1) < TALON_KEY_HOLE_COLOUR) & ~paper
        pockets = talon_reconstruct(talon_erode(near, TALON_KEY_HOLE_CORE_PX), near)
        pockets = talon_erode(talon_dilate(pockets, TALON_KEY_FIBRE_PX), TALON_KEY_FIBRE_PX) & ~(luma < TALON_KEY_PAPER_LUMA) | pockets
        paper = paper | pockets
    solid = ~paper
    # Drop opaque islands smaller than the talons (dark paper specks): keep only what grows back from a deep core.
    solid = talon_reconstruct(talon_erode(solid, TALON_KEY_ISLAND_PX), solid)
    alpha = solid.astype(np.float32)
    soft = (alpha + np.roll(alpha, 1, 0) + np.roll(alpha, -1, 0) + np.roll(alpha, 1, 1) + np.roll(alpha, -1, 1)) / 5.0
    alpha = np.where(solid, np.maximum(soft, 0.6), soft * 0.5)
    alpha[0, :] = alpha[-1, :] = alpha[:, 0] = alpha[:, -1] = 0.0
    px[..., 3] = alpha
    out = bpy.data.images.new("talon_keyed", w, h, alpha=True)
    out.pixels.foreach_set(px.ravel())
    out.filepath_raw = dst
    out.file_format = "PNG"
    out.save()
    # Blender pixel rows run bottom-up; corners are corners either way.
    corners = [float(alpha[y, x]) for y, x in ((0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1))]
    print("TALON_KEY %s %dx%d opaque=%.3f transparent=%.3f corners=%s" % (
        dst, w, h, float((alpha > 0.5).mean()), float((alpha < 0.05).mean()), corners))


main()
