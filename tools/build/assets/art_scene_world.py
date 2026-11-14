"""Key and grade a painted world piece toward the Other Realm study (Blender python: numpy + bpy, no model calls).

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python tools/build/assets/art_scene_world.py -- \
      <in.png> <out.png> <preset> <W> <H> [x0 y0 x1 y1 [fit|fill|repeatN]]
  With a box (fractions of the canvas, y from the top), the keyed piece is scaled to fit inside the box (aspect kept,
  centred across, sitting on the box bottom) on a transparent W x H canvas: the backdrop panels are 4800 x 2400 world
  units centred on Z 0, so only rows 5%..50% from the top are ever in view (Z 0..1080); content goes there.

Presets (numbers measured on pipeline/art/reference/discord/20261111-0318_Ricky_other-realm.png, Nov 13, artscene):
  frame mean RGB (41, 39, 36), std (15, 11, 9); island lit parts mean (87, 66, 51).
  opaque  : grade the whole picture to the study's frame mean/std (start-end, base).
  near    : key off the green, grade the earth to near-island values, crop to the earth (world-solids).
  mid     : key, grade a step darker and flatter (bg-land, architecture).
  far     : key, grade dark and low contrast (skyline: distant islands).
  ghost   : key, grade to barely above the void (clock rims).
Keying: the green (or magenta) ground is sampled from the border (the model paints a muted green, not #00FF00), so alpha comes from
how much greener than red/blue a pixel is, relative to that sampled green. Straight alpha; green spill clamped.
"""
import sys

import bpy
import numpy as np

PRESETS = {
    # key, target mean (0-1), target std (0-1), alpha scale, crop to content
    "opaque": (False, (0.160, 0.151, 0.142), (0.060, 0.045, 0.035), 1.0, False),
    "near": (True, (0.250, 0.200, 0.160), (0.120, 0.090, 0.065), 1.0, True),
    "mid": (True, (0.205, 0.175, 0.148), (0.085, 0.065, 0.048), 1.0, False),
    "far": (True, (0.172, 0.158, 0.145), (0.040, 0.032, 0.028), 1.0, False),
    "ghost": (True, (0.200, 0.180, 0.158), (0.030, 0.026, 0.022), 0.75, False),
    # haze: an opaque painting of low ridges turned into a faint veil, fading out toward its top (the Base layer
    # sits in front of the skyline and land, so it must stay see-through)
    "haze": (False, (0.190, 0.180, 0.172), (0.050, 0.042, 0.038), 0.45, False),
}
HAZE_FADE = 0.55   # haze: share of the picture height (from the top) over which alpha ramps in
# (KEY_LO/HI were 0.25/0.70 until the refuge lantern's yellow glow over green keyed as an opaque grey halo, Nov 13)
KEY_LO = 0.12      # share of the ground's green excess below which a pixel is fully opaque
KEY_HI = 0.50      # share above which it is fully transparent
BORDER = 6         # px of border sampled for the ground colour
SOLID_ALPHA = 0.5  # alpha counted as content when cropping and grading
CROP_PAD = 2       # px kept around the content when cropping
TILE_FADE = 0.12   # repeatN: share of the piece width cross-faded so the copies join without a seam (BG-02)


def load(path):
    im = bpy.data.images.load(path)
    w, h = im.size
    px = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)
    return px


def key(px):
    rgb = px[..., :3]
    edge = np.concatenate([rgb[:BORDER].reshape(-1, 3), rgb[-BORDER:].reshape(-1, 3),
                           rgb[:, :BORDER].reshape(-1, 3), rgb[:, -BORDER:].reshape(-1, 3)])
    ground = np.median(edge, axis=0)
    if min(ground[0], ground[2]) > ground[1]:
        # magenta ground (Nov 13: on green the model grew grass on the islands' tops, which keyed out): excess is how
        # much both red and blue stand above green; warm earth (R > G > B) has none.
        ground_excess = max(1e-3, min(ground[0], ground[2]) - ground[1])
        excess = (np.minimum(rgb[..., 0], rgb[..., 2]) - rgb[..., 1]) / ground_excess
        alpha = np.clip(1.0 - (excess - KEY_LO) / (KEY_HI - KEY_LO), 0.0, 1.0)
        rgb[..., 2] = np.minimum(rgb[..., 2], rgb[..., 1])   # despill: pink fringe -> warm brown
    else:
        ground_excess = max(1e-3, ground[1] - max(ground[0], ground[2]))
        excess = (rgb[..., 1] - np.maximum(rgb[..., 0], rgb[..., 2])) / ground_excess
        alpha = np.clip(1.0 - (excess - KEY_LO) / (KEY_HI - KEY_LO), 0.0, 1.0)
        rgb[..., 1] = np.minimum(rgb[..., 1], np.maximum(rgb[..., 0], rgb[..., 2]))   # despill
    px[..., 3] = alpha
    return ground


def grade(px, mean, std):
    mask = px[..., 3] >= SOLID_ALPHA
    if not mask.any():
        return
    rgb = px[..., :3]
    m = rgb[mask].mean(axis=0)
    s = rgb[mask].std(axis=0) + 1e-4
    rgb[...] = np.clip((rgb - m) / s * np.array(std) + np.array(mean), 0.0, 1.0)


LUMA_PRESETS = {"opaque": (0.140, 0.065, 0.9), "near": (0.200, 0.110, 0.85)}   # target mean luma, luma std, chroma kept (study frame L 37/255; std raised so island bodies stay dark under lit rims)


def grade_luma(px, mean, std, chroma):
    """Match brightness only and keep the painting's own warm colour: the per-channel match flattened the amber rim
    light (r2 start-end, Nov 13)."""
    rgb = px[..., :3]
    lum = rgb.mean(axis=2, keepdims=True)
    m, s = float(lum.mean()), float(lum.std()) + 1e-4
    new = np.clip((lum - m) / s * std + mean, 0.0, 1.0)
    tint = (rgb - lum) * chroma
    rgb[...] = np.clip(new + tint * (new / np.maximum(lum, 1e-3)), 0.0, 1.0)


def crop(px):
    # Blender rows run bottom-up; crop is symmetric so the order does not matter here.
    ys, xs = np.nonzero(px[..., 3] >= SOLID_ALPHA)
    if len(ys) == 0:
        return px
    y0, y1 = max(0, ys.min() - CROP_PAD), min(px.shape[0], ys.max() + 1 + CROP_PAD)
    x0, x1 = max(0, xs.min() - CROP_PAD), min(px.shape[1], xs.max() + 1 + CROP_PAD)
    return px[y0:y1, x0:x1].copy()


def resize(px, w, h):
    im = bpy.data.images.new("r", px.shape[1], px.shape[0], alpha=True)
    im.pixels.foreach_set(np.ascontiguousarray(px).ravel())
    im.scale(w, h)
    return np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)


def tileable(px, fade):
    """Tileable copy, `fade` columns narrower: the first `fade` columns blend the source's last `fade` columns into
    its first ones (weights from art_scene_seam.crossfade_weights; art_scene_seam.make_tileable is the reference)."""
    w = px.shape[1]
    t = (np.arange(fade, dtype=np.float32) / max(1, fade - 1))[None, :, None]
    head = px[:, w - fade:] * (1.0 - t) + px[:, :fade] * t
    return np.concatenate([head, px[:, fade:w - fade]], axis=1)


def place(px, W, H, box, mode="fit"):
    """mode fit: keep aspect inside the box; fill: stretch to the box; repeatN: N copies side by side filling it."""
    x0, y0, x1, y1 = box
    bw, bh = (x1 - x0) * W, (y1 - y0) * H
    canvas = np.zeros((H, W, 4), dtype=np.float32)
    bottom = int(H - y1 * H)   # Blender rows run bottom-up
    if mode == "fit":
        s = min(bw / px.shape[1], bh / px.shape[0])
        w, h = max(1, int(px.shape[1] * s)), max(1, int(px.shape[0] * s))
        left = int(x0 * W + (bw - w) / 2)
        canvas[bottom:bottom + h, left:left + w] = resize(px, w, h)
        return canvas
    n = int(mode[len("repeat"):]) if mode.startswith("repeat") else 1
    w, h = int(bw / n), int(bh)
    if n > 1:
        # BG-02 tileability: cross-fade the ends so copy i's last column meets copy i+1's first as two neighbouring
        # source columns (checked by art_scene_seam.py on the output).
        fade = max(2, int(px.shape[1] * TILE_FADE))
        piece = resize(tileable(px, fade), w, h)
    else:
        piece = resize(px, w, h)
    for i in range(n):
        left = int(x0 * W) + i * w
        canvas[bottom:bottom + h, left:left + w] = piece
    return canvas


def main():
    a = sys.argv[sys.argv.index("--") + 1:]
    src, dst, preset, W, H = a[0], a[1], a[2], int(a[3]), int(a[4])
    do_key, mean, std, alpha_scale, do_crop = PRESETS[preset]
    px = load(src)
    if do_key:
        key(px)
    else:
        px[..., 3] = 1.0
    if preset == "haze":
        h = px.shape[0]
        top = 1.0 - np.arange(h, dtype=np.float32) / max(1, h - 1)   # 1 at the top row (Blender rows run bottom-up)
        px[..., 3] *= np.clip((1.0 - top) / HAZE_FADE, 0.0, 1.0)[:, None]
    if preset in LUMA_PRESETS:
        grade_luma(px, *LUMA_PRESETS[preset])
    else:
        grade(px, mean, std)
    px[..., 3] *= alpha_scale
    if do_crop or len(a) > 5:
        px = crop(px)
    if len(a) > 5:
        px = place(px, W, H, [float(v) for v in a[5:9]], a[9] if len(a) > 9 else "fit")
    h, w = px.shape[:2]
    out = bpy.data.images.new("o", w, h, alpha=True)
    out.pixels.foreach_set(np.ascontiguousarray(px).ravel())
    out.scale(W, H)
    out.filepath_raw = dst
    out.file_format = "PNG"
    out.save()
    print("art_scene_world", preset, dst, W, H, "transparent frac", round(float((px[..., 3] < 0.05).mean()), 3))


if __name__ == "__main__":
    main()
