"""Paint the two wavy dripping clock-rim bands out of the start-end picture (Blender python: numpy + bpy, no model calls).

  Blender -b --factory-startup --python tools/build/assets/art_scene_unband.py -- <in.png> <out.png>

Why (Nov 13 gate 3dfc4e2d, keeper screen): the bg:start-end picture (bg-start-end/world_r2_post.png, 1920 x 1080, opaque)
carries two thick brown wavy bands with drips across its middle; in the keeper frame they read as "wind drawn as thick
brown dripping bands, not thin ash-blue ribbons". The wind ribbons themselves are flat-colour planes (not this art).
Fix: inside a mask over the bands (the windmill, barn and islands are kept), the picture is replaced by clean void:
per column, a straight blend between the void colour just above and just below the band zone, plus the grain of a
band-free void patch, plus a few dim amber flecks like the rest of the sky. The mask edge is feathered.
Boxes are in pixels of the 1920 x 1080 source, y from the top.
"""
import sys

import bpy
import numpy as np

BAND_TOP = 40                  # first row of the band zone; the mask ramps in from here (the crosshatched sky fades out)
BAND_FULL = 250                # row where the mask is full (the upper band's crest starts about row 255)
BAND_BOTTOM = 700              # last row of the band zone where nothing else is below (open void)
# (x0, x1, last band row) where land or buildings sit under the band zone: the zone stops above them
ZONE_FLOOR = ((0, 260, 655), (880, 1380, 652), (1380, 1800, 440), (1800, 1920, 515))
BOTTOM_REF_ROWS = 6            # rows sampled just under the zone, per column
BOTTOM_SMOOTH = 15             # columns averaged for that colour (odd)
# windmill (x0, x1, y0, y1): only its ink detail (picture minus its own blur) is kept over the clean void, so the band
# haze behind it goes but the strokes stay
LINE_ART = ((1232, 1380, 380, 680),)
# behind the barn the picture keeps a lighter glow (part of the band's haze) that the mask cannot reach without cutting
# the roof: that box is scaled toward the clean void's tone (barn included), feathered so no edge shows
GLOW_BOX = (1360, 1920, 425, 700)
GLOW_SAMPLES = ((1385, 1435, 450, 500), (1810, 1900, 455, 505))   # pure glow background inside the box
GLOW_TARGET = (300, 880, 705, 725)   # open void (x0, x1, y0, y1) whose tone the glow box is scaled to
GLOW_FEATHER = 45              # px
LINE_BLUR = 7                  # px box blur radius splitting ink detail from the smooth haze
REF_ROWS = 14                  # rows sampled above / below the zone for the void colour
SMOOTH = 61                    # columns averaged for the void colour (odd)
GRAIN_PATCH = (300, 880, 760, 1060)   # band-free void (x0, x1, y0, y1) whose fine grain is reused
GRAIN_BLUR = 9                 # px box blur splitting grain from tone
FEATHER = 12                   # px mask feather
FLECKS = 34                    # dim amber flecks added to the cleaned zone
FLECK_RGB = np.array([0.80, 0.52, 0.28], np.float32)   # sampled from the picture's own sky flecks
FLECK_ALPHA = (0.35, 0.8)
SEED = 7


def load_td(path):
    im = bpy.data.images.load(path)
    w, h = im.size
    return np.array(im.pixels[:], np.float32).reshape(h, w, 4)[::-1].copy()


def save_td(px, path):
    out = bpy.data.images.new("o", px.shape[1], px.shape[0], alpha=True)
    out.pixels.foreach_set(np.ascontiguousarray(np.clip(px[::-1], 0, 1)).ravel())
    out.filepath_raw = path
    out.file_format = "PNG"
    out.save()


def box_blur(a, r, axis):
    k = 2 * r + 1
    pad = [(0, 0)] * a.ndim
    pad[axis] = (r, r)
    c = np.cumsum(np.pad(a, pad, mode="edge"), axis=axis)
    c = np.concatenate([np.zeros_like(np.take(c, [0], axis=axis)), c], axis=axis)
    n = a.shape[axis]
    return (np.take(c, range(k, n + k), axis=axis) - np.take(c, range(0, n), axis=axis)) / k


def zone_bottom(w):
    floor = np.full(w, BAND_BOTTOM, np.int32)
    for x0, x1, y in ZONE_FLOOR:
        floor[x0:x1] = y
    return floor


def mask(h, w):
    ys = np.arange(h)[:, None]
    ramp = np.clip((ys - BAND_TOP) / float(BAND_FULL - BAND_TOP), 0, 1)
    m = (ramp * (ys <= zone_bottom(w)[None, :])).astype(np.float32)
    r = FEATHER // 2
    return np.clip(box_blur(box_blur(m, r, 0), r, 1), 0, 1)


def clean_void(px):
    h, w = px.shape[:2]
    rgb = px[..., :3]
    floor = zone_bottom(w)
    top = rgb[BAND_TOP - REF_ROWS:BAND_TOP].mean(0)
    # bottom colour per column from the picture just under the zone, so the cleaned zone meets it without a step
    # (Nov 13 gate a2bc7f3d: one global bottom colour left darker boxes above the islands and a step at row 700)
    bot = np.stack([np.median(rgb[f + 1:f + 1 + BOTTOM_REF_ROWS, x], axis=0) for x, f in enumerate(floor)])
    top, bot = box_blur(top, SMOOTH // 2, 0), box_blur(bot, BOTTOM_SMOOTH // 2, 0)
    ys = np.arange(h, dtype=np.float32)[:, None]
    t = np.clip((ys - BAND_TOP) / np.maximum(1, floor - BAND_TOP)[None, :], 0, 1)[..., None]
    tone = top[None] * (1 - t) + bot[None] * t
    x0, x1, y0, y1 = GRAIN_PATCH
    patch = rgb[y0:y1, x0:x1]
    grain = patch - box_blur(box_blur(patch, GRAIN_BLUR, 0), GRAIN_BLUR, 1)
    reps = (h // grain.shape[0] + 1, w // grain.shape[1] + 1, 1)
    tone = tone + np.tile(grain, reps)[:h, :w]
    rng = np.random.default_rng(SEED)
    yy, xx = np.mgrid[0:h, 0:w]
    for _ in range(FLECKS):
        cx = rng.uniform(0, w)
        cy = rng.uniform(BAND_TOP, BAND_BOTTOM)
        rad = rng.uniform(0.9, 1.8)
        a = rng.uniform(*FLECK_ALPHA)
        y_lo, y_hi, x_lo, x_hi = int(cy) - 4, int(cy) + 5, int(cx) - 4, int(cx) + 5
        y_lo, x_lo = max(0, y_lo), max(0, x_lo)
        d2 = (yy[y_lo:y_hi, x_lo:x_hi] - cy) ** 2 + (xx[y_lo:y_hi, x_lo:x_hi] - cx) ** 2
        g = (a * np.exp(-d2 / (2 * rad * rad)))[..., None]
        tone[y_lo:y_hi, x_lo:x_hi] = tone[y_lo:y_hi, x_lo:x_hi] * (1 - g) + FLECK_RGB * g
    return tone


def main():
    src, dst = sys.argv[sys.argv.index("--") + 1:][:2]
    px = load_td(src)
    m = mask(*px.shape[:2])[..., None]
    rgb = px[..., :3]
    x0, x1, y0, y1 = GLOW_BOX
    glow = np.concatenate([rgb[b:c, a:d].reshape(-1, 3) for a, d, b, c in GLOW_SAMPLES]).mean(0)
    target = rgb[GLOW_TARGET[2]:GLOW_TARGET[3], GLOW_TARGET[0]:GLOW_TARGET[1]].reshape(-1, 3).mean(0)
    gain = np.ones(px.shape[:2], np.float32)
    gain[y0:y1, x0:x1] = 0.0
    r = GLOW_FEATHER // 2
    weight = 1.0 - np.clip(box_blur(box_blur(gain, r, 0), r, 1), 0, 1)
    weight[y1 - GLOW_FEATHER:y1] *= np.linspace(1, 0, GLOW_FEATHER, dtype=np.float32)[:, None]
    weight[y1:] = 0
    factor = 1.0 + weight[..., None] * (target / np.maximum(glow, 1e-3) - 1.0)
    rgb = rgb * factor
    print("glow", glow.round(3), "target", target.round(3))
    px[..., :3] = rgb
    clean = clean_void(px)
    for x0, x1, y0, y1 in LINE_ART:
        part = rgb[y0:y1, x0:x1]
        detail = part - box_blur(box_blur(part, LINE_BLUR, 0), LINE_BLUR, 1)
        clean[y0:y1, x0:x1] += np.minimum(detail, 0) * 1.6 + np.maximum(detail, 0)
    px[..., :3] = rgb * (1 - m) + clean * m
    save_td(px, dst)
    print("art_scene_unband", dst, px.shape[1], px.shape[0], "masked frac", round(float((m > 0.5).mean()), 3))


if __name__ == "__main__":
    main()
