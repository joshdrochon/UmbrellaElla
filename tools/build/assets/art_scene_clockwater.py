"""Build the clock, water and clock-water-wind backdrop layers from separately painted parts (GDD BG-03, BG-05, BG-06).
Blender python (numpy + bpy), no model calls.

  Blender -b --factory-startup --python tools/build/assets/art_scene_clockwater.py -- <layer> <out.png> <raw> [<raw> ...]
    clock <out> <dials.png> <hands.png>          two dial faces (front rim + face) and two separate hands
    water <out> <fall.png>                       one fall cut into spill source, falling middle, land pool, sea landing
    wind  <out> <ribbon.png> <dials.png> <hands.png> <fall.png>
                                                 wind entry/straight/bend/exit, one small clock and one thin fall
Every part is written next to <out> as <out stem>_<part>.png (keyed, graded, own file: BG-03 "its own output and
editability"); the layer is the parts placed on a 2400 x 1200 transparent canvas, content in the rows the camera sees
(5%..50% from the top). Hands are separate parts rotated onto the dial centre, so a ticking clock can turn them
without redrawing the face (BG-06). Water parts meet through feathered masks (BG-06 "blend contacts with masks").

Look (lead order Nov 13 18:28: "faint ash-blue clock rims and dial ghosts in the far dark, dim water/wind ribbons"):
graded by brightness only so the painted ash-blue / silver-grey hue stays (art_scene_world.grade_luma, on the
keyed pixels), then held faint with an alpha scale.
"""
import math
import os
import sys

import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import art_scene_world as world  # noqa: E402

W, H = 2400, 1200
# part look: (target mean luma, luma std, chroma kept, alpha scale, tint) ; tint = RGB ratio pulled in at TINT_MIX
ASH_BLUE = (0.86, 0.98, 1.16)     # BG-05 "ash-blue": the study's cool rim light, a step bluer than its grey void
SILVER = (0.95, 0.99, 1.06)       # BG-05 "silver-grey water"
LOOK = {
    "clock": (0.165, 0.040, 1.0, 0.60, ASH_BLUE),
    "hand": (0.250, 0.040, 1.0, 0.70, ASH_BLUE),
    "water": (0.215, 0.055, 1.0, 0.60, SILVER),
    "wind": (0.190, 0.035, 1.0, 0.24, ASH_BLUE),   # r1 at 0.42 alpha / full width read as a loud blue band in the route frame
    "wind-clock": (0.150, 0.035, 1.0, 0.40, ASH_BLUE),
    "wind-hand": (0.220, 0.035, 1.0, 0.50, ASH_BLUE),
    "wind-water": (0.200, 0.045, 1.0, 0.42, SILVER),
}
TINT_MIX = 0.8
FACE_GHOST = 0.35            # dial glass alpha relative to the rim: "dial ghosts", the rim carries the clock
RIM_SHARE = 0.84             # radius share where the front rim starts
WATER_FRAME = 0.05           # the fall draft came inside a cream frame: share cut off each side before keying
WATER_BANDS = (("source", 0.0, 0.19), ("middle", 0.19, 0.74), ("pool", 0.74, 0.86), ("sea", 0.86, 1.0))
WIND_BANDS = (("entry", 0.0, 0.14), ("straight", 0.14, 0.42), ("bend", 0.42, 0.72), ("exit", 0.72, 1.0))
FEATHER = 0.03               # share of the length over which neighbouring parts cross-fade
EDGE_FADE = 0.25             # water: the fall fades out over this share of its (cropped) width at each side
BOTTOM_FADE = 0.30           # water: the pool and sea landing fade out over this share of the height at the bottom
# (Nov 13 gate 3dfc4e2d: the side fade ran before the crop, so the cropped sea kept square sides and a cut bottom and
#  read as grey placeholder blocks in the route frame)
HAND_LONG, HAND_SHORT = 0.44, 0.30   # hand length as a share of the dial width (pivot to tip)
HAND_ANGLES = {"large": (-62.0, 128.0), "small": (35.0, -150.0)}   # long, short (degrees, clockwise from 12)


def load_td(path):
    """Top-down RGBA float array (Blender stores rows bottom-up)."""
    return world.load(path)[::-1].copy()


def save_td(px, path):
    out = bpy.data.images.new(os.path.basename(path), px.shape[1], px.shape[0], alpha=True)
    out.pixels.foreach_set(np.ascontiguousarray(np.clip(px[::-1], 0.0, 1.0)).ravel())
    out.filepath_raw = path
    out.file_format = "PNG"
    out.save()


def keyed(px):
    world.key(px)
    return px


def look(px, name):
    mean, std, chroma, alpha, tint = LOOK[name]
    mask = px[..., 3] >= world.SOLID_ALPHA
    if mask.any():
        rgb = px[..., :3]
        lum = rgb.mean(axis=2, keepdims=True)
        m, s = float(lum[mask].mean()), float(lum[mask].std()) + 1e-4
        new = np.clip((lum - m) / s * std + mean, 0.0, 1.0)
        graded = new + (rgb - lum) * chroma * (new / np.maximum(lum, 1e-3))
        rgb[...] = np.clip(graded * (1 - TINT_MIX) + new * np.array(tint, np.float32) * TINT_MIX, 0.0, 1.0)
    px[..., 3] *= alpha
    return px


def split(px, axis):
    """Two crops either side of the widest empty gap along axis (0 rows, 1 columns)."""
    filled = (px[..., 3] >= world.SOLID_ALPHA).any(axis=1 - axis)
    idx = np.nonzero(filled)[0]
    gaps = np.diff(idx)
    cut = idx[int(np.argmax(gaps))] + gaps.max() // 2
    a, b = (px[:cut], px[cut:]) if axis == 0 else (px[:, :cut], px[:, cut:])
    return world.crop(a.copy()), world.crop(b.copy())


def resize_td(px, w, h):
    return world.resize(px[::-1].copy(), max(1, w), max(1, h))[::-1].copy()


def over(dst, src, x, y):
    """Alpha-composite src onto dst with src's top-left at (x, y); clipped to dst."""
    h, w = src.shape[:2]
    x0, y0, x1, y1 = max(0, x), max(0, y), min(dst.shape[1], x + w), min(dst.shape[0], y + h)
    if x0 >= x1 or y0 >= y1:
        return dst
    s = src[y0 - y:y1 - y, x0 - x:x1 - x]
    d = dst[y0:y1, x0:x1]
    sa, da = s[..., 3:4], d[..., 3:4]
    oa = sa + da * (1 - sa)
    d[..., :3] = (s[..., :3] * sa + d[..., :3] * da * (1 - sa)) / np.maximum(oa, 1e-6)
    d[..., 3:4] = oa
    return dst


def fit(px, box):
    """Scale px to fit inside box (fractions x0, y0, x1, y1 of the canvas, y from the top); return (piece, x, y),
    centred across, sitting on the box bottom."""
    x0, y0, x1, y1 = box
    bw, bh = (x1 - x0) * W, (y1 - y0) * H
    s = min(bw / px.shape[1], bh / px.shape[0])
    piece = resize_td(px, int(px.shape[1] * s), int(px.shape[0] * s))
    return piece, int(x0 * W + (bw - piece.shape[1]) / 2), int(y1 * H - piece.shape[0])


def rotate_about(px, pivot, deg, size):
    """Rotate px (top-down) clockwise by deg about pivot (x, y in px) onto a size x size canvas whose centre is
    the pivot. Bilinear."""
    out_y, out_x = np.mgrid[0:size, 0:size].astype(np.float32)
    c = size / 2.0
    a = math.radians(deg)
    dx, dy = out_x - c, out_y - c
    sx = dx * math.cos(a) + dy * math.sin(a) + pivot[0]
    sy = -dx * math.sin(a) + dy * math.cos(a) + pivot[1]
    h, w = px.shape[:2]
    x0, y0 = np.floor(sx).astype(int), np.floor(sy).astype(int)
    fx, fy = (sx - x0)[..., None], (sy - y0)[..., None]
    pad = np.zeros((h + 2, w + 2, 4), dtype=np.float32)
    pad[1:-1, 1:-1] = px
    pad[1:-1, 1:-1, :3] *= px[..., 3:4]   # premultiply so transparent black does not darken edges
    def at(yy, xx):
        return pad[np.clip(yy + 1, 0, h + 1), np.clip(xx + 1, 0, w + 1)]
    v = (at(y0, x0) * (1 - fx) * (1 - fy) + at(y0, x0 + 1) * fx * (1 - fy)
         + at(y0 + 1, x0) * (1 - fx) * fy + at(y0 + 1, x0 + 1) * fx * fy)
    v[..., :3] /= np.maximum(v[..., 3:4], 1e-6)
    return v


def hand_on(dial, hand, length_share, deg):
    """Hand drawn pointing right with its pivot ring at the left end; turn it to deg (clockwise from 12) and pin
    the pivot on the dial centre (the dial is round above its drips: centre = (w/2, w/2))."""
    length = int(dial.shape[1] * length_share)
    s = length / max(1, hand.shape[1] - hand.shape[0] / 2.0)
    h = resize_td(hand, max(1, int(hand.shape[1] * s)), max(1, int(hand.shape[0] * s)))
    pivot = (h.shape[0] / 2.0, h.shape[0] / 2.0)
    size = 2 * (h.shape[1] + 2)
    turned = rotate_about(h, pivot, deg - 90.0, size)
    c = dial.shape[1] // 2
    return over(dial, turned, c - size // 2, c - size // 2)


def bands(px, spec, axis):
    """Cut px along axis into the named bands with feathered masks that sum to 1; returns {name: part}."""
    n = px.shape[axis]
    pos = (np.arange(n, dtype=np.float32) + 0.5) / n
    f = FEATHER
    parts = {}
    for name, a, b in spec:
        lo = np.ones(n, np.float32) if a <= 0 else np.clip((pos - (a - f / 2)) / f, 0, 1)
        hi = np.ones(n, np.float32) if b >= 1 else np.clip(((b + f / 2) - pos) / f, 0, 1)
        m = (lo * hi)[:, None] if axis == 0 else (lo * hi)[None, :]
        part = px.copy()
        part[..., 3] *= m
        parts[name] = part
    return parts


def recombine(parts):
    """Sum of the feathered parts (premultiplied), i.e. the masked blend of every contact."""
    first = next(iter(parts.values()))
    acc = np.zeros_like(first)
    for p in parts.values():
        acc[..., :3] += p[..., :3] * p[..., 3:4]
        acc[..., 3] += p[..., 3]
    acc[..., :3] /= np.maximum(acc[..., 3:4], 1e-6)
    acc[..., 3] = np.clip(acc[..., 3], 0, 1)
    return acc


def stem(out):
    return os.path.splitext(out)[0]


def ghost_face(dial):
    """Fade the dial glass inside the rim (round dial above its drips: centre (w/2, w/2), radius w/2)."""
    h, w = dial.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.hypot(xx - w / 2.0, yy - w / 2.0) / (w / 2.0)
    keep = FACE_GHOST + (1 - FACE_GHOST) * np.clip((r - RIM_SHARE) / 0.04, 0, 1)
    dial[..., 3] *= keep
    return dial


def clocks(dials_path, hands_path, out, name="clock", hand_name="hand"):
    big, small = split(keyed(load_td(dials_path)), axis=1)
    if big.shape[1] < small.shape[1]:
        big, small = small, big
    long_h, short_h = split(keyed(load_td(hands_path)), axis=0)
    if long_h.shape[1] < short_h.shape[1]:
        long_h, short_h = short_h, long_h
    parts = {"dial-large": big, "dial-small": small, "hand-long": long_h, "hand-short": short_h}
    for k, v in parts.items():
        look(v, hand_name if k.startswith("hand") else name)
        if k.startswith("dial"):
            ghost_face(v)
        save_td(v, "%s_%s.png" % (stem(out), k))
    made = {}
    for key, dial in (("large", big), ("small", small)):
        face = dial.copy()
        hand_on(face, short_h, HAND_SHORT, HAND_ANGLES[key][1])
        hand_on(face, long_h, HAND_LONG, HAND_ANGLES[key][0])
        made[key] = face
    return made


def edge_fade(h, w):
    """Top-down alpha factor: sides fade over EDGE_FADE of the width, the bottom over BOTTOM_FADE of the height."""
    x = (np.arange(w, dtype=np.float32) + 0.5) / w
    y = (np.arange(h, dtype=np.float32) + 0.5) / h
    side = np.clip(np.minimum(x, 1 - x) / EDGE_FADE, 0, 1)[None, :]
    bottom = np.clip((1 - y) / BOTTOM_FADE, 0, 1)[:, None]
    return side * bottom


def water_parts(fall_path, out, name="water"):
    px = load_td(fall_path)
    h, w = px.shape[:2]
    fy, fx = int(h * WATER_FRAME), int(w * WATER_FRAME)
    px = keyed(px[fy:h - fy, fx:w - fx].copy())
    px = world.crop(px)
    px[..., 3] *= edge_fade(px.shape[0], px.shape[1])
    look(px, name)
    parts = bands(px, WATER_BANDS, axis=0)
    for k, v in parts.items():
        save_td(v, "%s_%s.png" % (stem(out), k))
    return recombine(parts)


def layer_clock(out, dials, hands):
    made = clocks(dials, hands, out)
    canvas = np.zeros((H, W, 4), np.float32)
    for key, box in (("large", (0.05, 0.04, 0.24, 0.23)), ("small", (0.50, 0.05, 0.58, 0.15))):
        over(canvas, *fit(made[key], box))
    return canvas


def layer_water(out, fall):
    fall_px = water_parts(fall, out)
    canvas = np.zeros((H, W, 4), np.float32)
    for box in ((0.27, 0.13, 0.35, 0.50), (0.80, 0.24, 0.85, 0.50)):
        over(canvas, *fit(fall_px, box))
    return canvas


def layer_wind(out, ribbon, dials, hands, fall):
    px = world.crop(keyed(load_td(ribbon)))
    look(px, "wind")
    parts = bands(px, WIND_BANDS, axis=1)
    for k, v in parts.items():
        save_td(v, "%s_%s.png" % (stem(out), k))
    canvas = np.zeros((H, W, 4), np.float32)
    small = clocks(dials, hands, stem(out) + "-clock.png", name="wind-clock", hand_name="wind-hand")["small"]
    over(canvas, *fit(small, (0.84, 0.06, 0.90, 0.14)))
    over(canvas, *fit(water_parts(fall, stem(out) + "-water.png", name="wind-water"), (0.905, 0.20, 0.93, 0.44)))
    over(canvas, *fit(recombine(parts), (0.08, 0.29, 0.60, 0.36)))
    return canvas


def main():
    a = sys.argv[sys.argv.index("--") + 1:]
    layer, out, raws = a[0], a[1], a[2:]
    canvas = {"clock": layer_clock, "water": layer_water, "wind": layer_wind}[layer](out, *raws)
    save_td(canvas, out)
    print("art_scene_clockwater", layer, out, W, H, "transparent frac", round(float((canvas[..., 3] < 0.05).mean()), 3))


if __name__ == "__main__":
    main()
