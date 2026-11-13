"""Key the cream paper off the Keeper talon stand-in (Blender python: numpy + bpy; numbers only, no model).

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P tools/build/assets/art_keeper_talon_key.py -- \
      pipeline/art/proof/standins/keeper-talon/move_final2.png pipeline/art/proof/standins/keeper-talon/move_final2_keyed.png

The source is RGB: two iron talons inked on cream paper, so the slot drew a cream box over the whole Keeper.
Method: the paper is the light region reachable from the image border (a flood fill that stops at the ink outlines,
so pale claw highlights inside an outline stay). Thin paper fibres and small specks left in that region are closed
over; any opaque island smaller than the talons is dropped. Edges get a 1 px soft step. Writes straight-alpha RGBA.
"""
import sys

import bpy
import numpy as np

TALON_KEY_PAPER_LUMA = 0.56      # paper and its smudges are lighter than this; ink outlines are far darker
TALON_KEY_PAPER_WARMTH = 0.30    # paper red minus blue stays under this (the brass bands are warmer)
TALON_KEY_FIBRE_PX = 4           # close fibres/specks up to ~2x this wide that sit inside the paper
TALON_KEY_ISLAND_PX = 14         # an opaque island must survive this much erosion to count as talon


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
    im = bpy.data.images.load(src)
    w, h = im.size
    px = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)
    rgb = px[..., :3]
    luma = rgb @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    paperish = (luma > TALON_KEY_PAPER_LUMA) & ((rgb[..., 0] - rgb[..., 2]) < TALON_KEY_PAPER_WARMTH)
    border = np.zeros_like(paperish)
    border[0, :] = border[-1, :] = border[:, 0] = border[:, -1] = True
    paper = talon_reconstruct(border, paperish)
    # Fibres and specks sitting in the paper: close the paper over them (dilate then erode), then flood again from
    # the border so a closed gap inside a talon outline never opens.
    closed = talon_erode(talon_dilate(paper, TALON_KEY_FIBRE_PX), TALON_KEY_FIBRE_PX)
    paper = talon_reconstruct(border, closed | paper)
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
