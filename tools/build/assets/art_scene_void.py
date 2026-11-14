"""Procedural pieces of the Other Realm void (numbers only, no model; Blender python: numpy + bpy).

  Blender -b --factory-startup --python tools/build/assets/art_scene_void.py -- <kind> <out.png> <W> <H> [seed] [under.png]
  under.png (flecks only): a same-size picture drawn under the flecks (the keyed clock rims: BG-05 puts the distant
  clocks behind the land, and bg:atmosphere is the one scene layer behind bg:land, so the rims ride on it).
  kind = sky   : the tiled Sky layer (T_Paper slot): a seamless warm charcoal void with faint fibre grain, no shapes
                 (it repeats every 600 world units, so anything distinct would show the repeat).
         flecks: the bg:atmosphere layer: about a hundred dim amber ember flecks plus a faint lighter haze band through
                 the middle of the view, transparent elsewhere; content only in rows 5%..50% (the part of a 4800 x 2400
                 panel the camera sees).
Colours measured on the study (pipeline/art/reference/discord/20261111-0318_Ricky_other-realm.png): void median
RGB about (37, 35, 32), flecks dim amber toward #E9C46A.
"""
import sys

import bpy
import numpy as np

VOID = np.array([0.135, 0.127, 0.118])      # study frame median, slightly under (layers add haze on top)
VOID_TOP = np.array([0.105, 0.098, 0.090])  # darker toward the top and bottom of the view
GRAIN = 0.012                               # fibre grain amplitude
FLECK = np.array([0.91, 0.77, 0.42])        # #E9C46A
FLECK_COUNT = 110
FLECK_RADIUS = (0.8, 2.6)                   # px at 2400 wide
FLECK_ALPHA = (0.25, 0.85)
HAZE = np.array([0.30, 0.28, 0.27])         # faint lighter haze band, a touch of ash blue
HAZE_ALPHA = 0.10
VIEW_TOP, VIEW_BOTTOM = 0.05, 0.50          # rows of a backdrop panel in view


def tile_noise(rng, w, h, scale):
    """Seamless value noise: random grid with wraparound, bilinear."""
    gw, gh = max(2, w // scale), max(2, h // scale)
    g = rng.random((gh, gw))
    ys, xs = np.linspace(0, gh, h, endpoint=False), np.linspace(0, gw, w, endpoint=False)
    y0, x0 = ys.astype(int), xs.astype(int)
    fy, fx = (ys - y0)[:, None], (xs - x0)[None, :]
    y1, x1 = (y0 + 1) % gh, (x0 + 1) % gw
    a = g[y0][:, x0] * (1 - fx) + g[y0][:, x1] * fx
    b = g[y1][:, x0] * (1 - fx) + g[y1][:, x1] * fx
    return a * (1 - fy) + b * fy


def sky(rng, w, h):
    n = 0.6 * tile_noise(rng, w, h, 64) + 0.4 * tile_noise(rng, w, h, 8) - 0.5
    px = np.ones((h, w, 4), dtype=np.float32)
    px[..., :3] = VOID + (n * 2 * GRAIN)[..., None]
    return px


def flecks(rng, w, h):
    px = np.zeros((h, w, 4), dtype=np.float32)
    rows = (1 - np.linspace(0, 1, h))[:, None]          # 0 at the bottom row, 1 at the top (Blender order)
    mid = (VIEW_TOP + VIEW_BOTTOM) / 2
    band = np.exp(-((1 - rows - mid) / 0.12) ** 2) * np.ones((1, w))
    band *= 0.7 + 0.3 * tile_noise(rng, w, h, 200)
    px[..., :3] = HAZE
    px[..., 3] = band * HAZE_ALPHA
    yy, xx = np.mgrid[0:h, 0:w]
    k = w / 2400.0
    for _ in range(FLECK_COUNT):
        cx = rng.uniform(0, w)
        cy = h - rng.uniform(VIEW_TOP, VIEW_BOTTOM) * h
        r = rng.uniform(*FLECK_RADIUS) * k
        a = rng.uniform(*FLECK_ALPHA)
        x0, x1 = int(max(0, cx - 4 * r)), int(min(w, cx + 4 * r + 1))
        y0, y1 = int(max(0, cy - 4 * r)), int(min(h, cy + 4 * r + 1))
        d2 = ((xx[y0:y1, x0:x1] - cx) ** 2 + (yy[y0:y1, x0:x1] - cy) ** 2) / (r * r)
        fa = a * np.exp(-d2)
        old = px[y0:y1, x0:x1, 3]
        new = fa + old * (1 - fa)
        px[y0:y1, x0:x1, :3] = (FLECK * fa[..., None] + px[y0:y1, x0:x1, :3] * (old * (1 - fa))[..., None]) / np.maximum(new, 1e-6)[..., None]
        px[y0:y1, x0:x1, 3] = new
    return px


def main():
    a = sys.argv[sys.argv.index("--") + 1:]
    kind, dst, w, h = a[0], a[1], int(a[2]), int(a[3])
    rng = np.random.default_rng(int(a[4]) if len(a) > 4 else 13)
    px = {"sky": sky, "flecks": flecks}[kind](rng, w, h)
    if kind == "flecks" and len(a) > 5:
        im = bpy.data.images.load(a[5])
        under = np.array(im.pixels[:], dtype=np.float32).reshape(im.size[1], im.size[0], 4)
        fa = px[..., 3:4]
        out_a = fa + under[..., 3:4] * (1 - fa)
        px[..., :3] = (px[..., :3] * fa + under[..., :3] * under[..., 3:4] * (1 - fa)) / np.maximum(out_a, 1e-6)
        px[..., 3:4] = out_a
    out = bpy.data.images.new("o", w, h, alpha=True)
    out.pixels.foreach_set(np.clip(px, 0, 1).ravel())
    out.filepath_raw = dst
    out.file_format = "PNG"
    out.save()
    print("art_scene_void", kind, dst, w, h)


main()
