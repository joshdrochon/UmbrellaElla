"""The UI ground: one painted, misty sepia frame every menu sits on, and the HUD clock face. Made procedurally with
numpy inside Blender's Python (D-new-art-blender: Blender only; no outside image is read).

  /Applications/Blender.app/Contents/MacOS/Blender -b --python Art/Source/UI/Ground/build_ground.py -- [--out DIR] [--only ground|clock]
  (Windows/Linux: the same with your Blender 5.2 binary.)
Writes Art/Source/UI/Ground/T_UI_Ground_PH.png (1920x1080) and T_UI_ClockFace_PH.png (512x512, transparent).
Layout follows the title-screen reference (references.json `title-screen`): a dark left third for the title lockup and
the menu, a clock arc top-left, floating islands and far ruins in mist on the right, a lit cottage and windmill on
the near island, ash-blue wind ribbons, gold embers. Fixed seed: the same bytes every run.
"""
import math
import os
import struct
import sys
import zlib

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "Font"))
import build_font  # noqa: E402  (numeral outlines for the clock faces)

W, H = 1920, 1080
SEED = 1112

INK = np.array([0.075, 0.062, 0.054])
ROCK = np.array([0.150, 0.118, 0.098])
ROCK_LIT = np.array([0.36, 0.29, 0.23])
HAZE = np.array([0.47, 0.43, 0.39])
HAZE_WARM = np.array([0.66, 0.53, 0.40])
GOLD = np.array([0.91, 0.66, 0.33])
GOLD_HOT = np.array([1.0, 0.86, 0.56])
ASH_BLUE = np.array([0.56, 0.63, 0.70])
CREAM = np.array([0.90, 0.85, 0.75])
RUST = np.array([0.66, 0.24, 0.13])


# ------------------------------------------------------------------ noise
class Noise:
    def __init__(self, seed):
        rng = np.random.default_rng(seed)
        self.table = rng.random((256, 256))

    def value(self, x, y):
        xi, yi = np.floor(x).astype(np.int64), np.floor(y).astype(np.int64)
        tx, ty = x - xi, y - yi
        tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
        a = self.table[yi & 255, xi & 255]
        b = self.table[yi & 255, (xi + 1) & 255]
        c = self.table[(yi + 1) & 255, xi & 255]
        d = self.table[(yi + 1) & 255, (xi + 1) & 255]
        return (a + (b - a) * tx) * (1 - ty) + (c + (d - c) * tx) * ty

    def fbm(self, x, y, octaves=5, gain=0.5, lac=2.03):
        out, amp, total = 0.0, 1.0, 0.0
        for i in range(octaves):
            out = out + amp * self.value(x + 17.3 * i, y + 9.1 * i)
            total += amp
            amp *= gain
            x, y = x * lac, y * lac
        return out / total


def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def mix(dst, colour, alpha):
    """dst (H,W,3) over-composited with colour at alpha (H,W) in place."""
    dst += (np.asarray(colour) - dst) * alpha[..., None]


# ------------------------------------------------------------------ shapes (anti-aliased coverage in a bounding box)
def convex(poly, shape):
    """Coverage of a convex polygon (any winding) on an (h, w) grid: (y0, x0, cover) for its bounding box."""
    h, w = shape
    p = np.asarray(poly, dtype=np.float64)
    x0, x1 = max(0, int(p[:, 0].min()) - 2), min(w, int(p[:, 0].max()) + 3)
    y0, y1 = max(0, int(p[:, 1].min()) - 2), min(h, int(p[:, 1].max()) + 3)
    if x1 <= x0 or y1 <= y0:
        return 0, 0, np.zeros((0, 0))
    yy, xx = np.mgrid[y0:y1, x0:x1] + 0.5
    area = 0.5 * np.sum(p[:, 0] * np.roll(p[:, 1], -1) - np.roll(p[:, 0], -1) * p[:, 1])
    sgn = 1.0 if area > 0 else -1.0
    d = np.full(xx.shape, -1e9)
    for (ax, ay), (bx, by) in zip(p, np.roll(p, -1, axis=0)):
        ex, ey = bx - ax, by - ay
        ln = math.hypot(ex, ey) or 1.0
        d = np.maximum(d, sgn * ((xx - ax) * ey - (yy - ay) * ex) / ln)
    return y0, x0, np.clip(0.5 - d, 0.0, 1.0)


SOLID = {"img": None, "mask": None}     # the main canvas and where it holds solid things (rock, buildings)


def mark_solid(img, y0, x0, cover):
    if img is SOLID["img"] and cover.size:
        m = SOLID["mask"][y0:y0 + cover.shape[0], x0:x0 + cover.shape[1]]
        np.maximum(m, cover, out=m)


def fill(img, poly, colour, alpha=1.0, mask=None):
    y0, x0, c = convex(poly, img.shape[:2])
    if c.size:
        mark_solid(img, y0, x0, c * alpha)
        mix(img[y0:y0 + c.shape[0], x0:x0 + c.shape[1]], colour, c * alpha)
        if mask is not None:
            m = mask[y0:y0 + c.shape[0], x0:x0 + c.shape[1]]
            np.maximum(m, c * alpha, out=m)


def line(img, a, b, width, colour, alpha=1.0, mask=None):
    (ax, ay), (bx, by) = a, b
    ex, ey = bx - ax, by - ay
    ln = math.hypot(ex, ey) or 1.0
    nx, ny = -ey / ln * width / 2, ex / ln * width / 2
    fill(img, [(ax + nx, ay + ny), (bx + nx, by + ny), (bx - nx, by - ny), (ax - nx, ay - ny)], colour, alpha, mask)


def disc(img, cx, cy, r, colour, alpha=1.0, soft=1.0):
    h, w = img.shape[:2]
    x0, x1 = max(0, int(cx - r - soft - 1)), min(w, int(cx + r + soft + 2))
    y0, y1 = max(0, int(cy - r - soft - 1)), min(h, int(cy + r + soft + 2))
    if x1 <= x0 or y1 <= y0:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1] + 0.5
    d = np.hypot(xx - cx, yy - cy)
    mix(img[y0:y1, x0:x1], colour, np.clip((r - d) / soft + 0.5, 0, 1) * alpha)


def glow(img, cx, cy, r, colour, strength):
    h, w = img.shape[:2]
    x0, x1 = max(0, int(cx - 3 * r)), min(w, int(cx + 3 * r))
    y0, y1 = max(0, int(cy - 3 * r)), min(h, int(cy + 3 * r))
    if x1 <= x0 or y1 <= y0:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1] + 0.5
    g = np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * r * r)) * strength
    img[y0:y1, x0:x1] += np.asarray(colour) * g[..., None]


def ring(img, cx, cy, r, width, colour, alpha, a0=0.0, a1=360.0, breaks=None):
    """An etched arc: a0..a1 in degrees clockwise from 12 o'clock; `breaks` (0..1 array by angle) wears it away."""
    h, w = img.shape[:2]
    x0, x1 = max(0, int(cx - r - width - 2)), min(w, int(cx + r + width + 3))
    y0, y1 = max(0, int(cy - r - width - 2)), min(h, int(cy + r + width + 3))
    if x1 <= x0 or y1 <= y0:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1] + 0.5
    d = np.abs(np.hypot(xx - cx, yy - cy) - r)
    ang = (np.degrees(np.arctan2(xx - cx, -(yy - cy))) + 360.0) % 360.0
    span = ((ang - a0) % 360.0) <= ((a1 - a0) % 360.0 if (a1 - a0) % 360.0 else 360.0)
    c = np.clip(width / 2 - d + 0.5, 0, 1) * span * alpha
    if breaks is not None:
        c = c * breaks(ang, np.hypot(xx - cx, yy - cy))
    mix(img[y0:y1, x0:x1], colour, c)


_GLYPHS = None


def numeral(img, text, cx, cy, size, rot_deg, colour, alpha):
    """Roman numeral in the game's own face, centred on (cx, cy), rotated to stand on the dial."""
    global _GLYPHS
    if _GLYPHS is None:
        src = build_font.glyphs()
        _GLYPHS = {ch: build_font.build_glyph(src[ch][0], [], nib_scale=0.8) for ch in "IVX"}
    k = size / build_font.CAP
    total = sum(_GLYPHS[ch][1] for ch in text) * k
    x = -total / 2
    cs, sn = math.cos(math.radians(rot_deg)), math.sin(math.radians(rot_deg))
    for ch in text:
        contours, adv = _GLYPHS[ch]
        for c in contours:
            pts = []
            for px, py in c:
                lx, ly = x + px * k, size / 2 - py * k
                pts.append((cx + lx * cs - ly * sn, cy + lx * sn + ly * cs))
            fill(img, pts, colour, alpha)
        x += adv * k


def clock_face(img, cx, cy, r, colour, alpha, nz, a0=0.0, a1=360.0, numerals=True, hands=None, worn=0.5):
    def breaks(ang, rad):
        n = nz.fbm(ang / 9.0 + cx * 0.01, rad / 40.0 + cy * 0.01, 3)
        return smooth(worn - 0.25, worn + 0.1, n + 0.25)
    w = max(1.2, r / 110.0)
    ring(img, cx, cy, r, w * 1.6, colour, alpha, a0, a1, breaks)
    ring(img, cx, cy, r * 0.955, w * 0.7, colour, alpha * 0.8, a0, a1, breaks)
    ring(img, cx, cy, r * 0.74, w * 0.7, colour, alpha * 0.7, a0, a1, breaks)
    names = ["XII", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI"]
    for i in range(60):
        deg = i * 6.0
        if ((deg - a0) % 360.0) > ((a1 - a0) % 360.0 if (a1 - a0) % 360.0 else 360.0):
            continue
        t = math.radians(deg)
        dx, dy = math.sin(t), -math.cos(t)
        inner = 0.90 if i % 5 == 0 else 0.925
        wear = float(breaks(np.array([deg]), np.array([r]))[0])
        line(img, (cx + dx * r * inner, cy + dy * r * inner), (cx + dx * r * 0.955, cy + dy * r * 0.955),
             w * (1.6 if i % 5 == 0 else 0.8), colour, alpha * (0.4 + 0.6 * wear))
        if numerals and i % 5 == 0:
            numeral(img, names[i // 5], cx + dx * r * 0.835, cy + dy * r * 0.835, r * 0.105, deg, colour, alpha * (0.45 + 0.55 * wear))
    for deg, length, width in hands or []:
        t = math.radians(deg)
        dx, dy = math.sin(t), -math.cos(t)
        nx, ny = -dy, dx
        tip = (cx + dx * r * length, cy + dy * r * length)
        mid = (cx + dx * r * length * 0.72, cy + dy * r * length * 0.72)
        fill(img, [(cx - dx * r * 0.08, cy - dy * r * 0.08), (mid[0] + nx * width * 1.6, mid[1] + ny * width * 1.6), tip,
                   (mid[0] - nx * width * 1.6, mid[1] - ny * width * 1.6)], colour, alpha)
        disc(img, cx, cy, width * 2.2, colour, alpha)


# ------------------------------------------------------------------ the scene
def ridge(img, nz, base_y, amp, scale, depth, seed, ruins=(), fade=210.0):
    """A far hill with ruin silhouettes; depth 0 (near, dark) .. 1 (far, lost in haze). The crest is soft, catches a
    warm rim of light, and the hill sinks back into the mist `fade` px below it, so layers read as depth, never as bands."""
    xs = np.arange(W) + 0.5
    top = base_y - amp * (nz.fbm(xs / scale + seed, np.full(W, seed * 1.7), 5) - 0.35) * 2.0
    yy, xx = np.mgrid[0:H, 0:W] + 0.5
    below = yy - top[None, :] + 5 * (nz.fbm(xx / 14.0 + seed, yy / 9.0, 3) - 0.5)
    cover = smooth(-3.0, 5.0, below)
    col = ROCK * (1 - depth) + HAZE * depth * 0.92
    tex = nz.fbm(xx / 38.0 + seed, yy / 16.0 + seed, 4)
    layer = np.empty((H, W, 3))
    layer[:] = col
    layer *= (0.80 + 0.42 * tex)[..., None] * (1.0 - 0.18 * smooth(0, fade, below))[..., None]
    rim = np.exp(-(below.clip(0) / 9.0)) * (below > -3) * smooth(0.3, 0.7, nz.fbm(xx / 60.0 + seed, np.full_like(xx, seed), 3))
    layer += (HAZE_WARM * 0.5)[None, None, :] * (rim * (0.25 + 0.5 * depth))[..., None]
    sil = np.zeros((H, W))
    for kind, x, s in ruins:
        y = float(top[int(np.clip(x, 0, W - 1))]) + 4
        build(layer, sil, kind, x, y, s, col * 0.86, depth)
    sink = 1.0 - smooth(fade * 0.25, fade, below + 60 * (nz.fbm(xx / 170.0 + seed, yy / 60.0, 3) - 0.5))
    side = smooth(0.14, 0.50, xx / W)
    a = np.maximum(cover * sink, sil) * side
    img += (layer - img) * a[..., None]
    return top


def arch_row(layer, sil, x, y, s, col, count, height):
    pw, gap = 9 * s, 30 * s
    for i in range(count + 1):
        px = x + i * (pw + gap)
        fill(layer, [(px, y), (px + pw, y), (px + pw, y - height), (px, y - height)], col, 1.0, sil)
    fill(layer, [(x - 2 * s, y - height), (x + count * (pw + gap) + pw + 2 * s, y - height),
                 (x + count * (pw + gap) + pw + 2 * s, y - height - 8 * s), (x - 2 * s, y - height - 8 * s)], col, 1.0, sil)
    for i in range(count):
        cx = x + i * (pw + gap) + pw + gap / 2
        for k in range(8):
            a0, a1 = math.pi * k / 8, math.pi * (k + 1) / 8
            r0, r1 = gap / 2, gap / 2 + 9 * s
            fill(layer, [(cx - r0 * math.cos(a0), y - height + 12 * s - r0 * math.sin(a0) * 0.9),
                         (cx - r1 * math.cos(a0), y - height + 12 * s - r1 * math.sin(a0) * 0.9),
                         (cx - r1 * math.cos(a1), y - height + 12 * s - r1 * math.sin(a1) * 0.9),
                         (cx - r0 * math.cos(a1), y - height + 12 * s - r0 * math.sin(a1) * 0.9)], col, 1.0, sil)


def build(layer, sil, kind, x, y, s, col, depth):
    if kind == "castle":
        for dx, wdt, hgt in ((-52, 20, 62), (-26, 16, 96), (-6, 24, 130), (22, 15, 84), (42, 22, 56)):
            fill(layer, [(x + dx * s, y), (x + (dx + wdt) * s, y), (x + (dx + wdt) * s, y - hgt * s), (x + dx * s, y - hgt * s)], col, 1.0, sil)
            fill(layer, [(x + (dx - 2) * s, y - hgt * s), (x + (dx + wdt + 2) * s, y - hgt * s),
                         (x + (dx + wdt / 2) * s, y - (hgt + wdt * 1.9) * s)], col, 1.0, sil)
        fill(layer, [(x - 70 * s, y), (x + 80 * s, y), (x + 80 * s, y - 30 * s), (x - 70 * s, y - 30 * s)], col, 1.0, sil)
        px, py = x + 6 * s, y - (130 + 24 * 1.9) * s
        line(layer, (px, py), (px, py - 26 * s), 1.6 * s, col, 1.0, sil)
        fill(layer, [(px, py - 26 * s), (px + 22 * s, py - 21 * s), (px, py - 15 * s)], RUST * (1 - 0.5 * depth) + HAZE * 0.5 * depth, 1.0, sil)
    elif kind == "arches":
        arch_row(layer, sil, x, y, s, col, 4, 44 * s)
    elif kind == "aqueduct":
        arch_row(layer, sil, x, y, s, col, 7, 58 * s)
    elif kind == "columns":
        for i, hgt in enumerate((70, 92, 92, 54)):
            px = x + i * 26 * s
            fill(layer, [(px, y), (px + 8 * s, y), (px + 8 * s, y - hgt * s), (px, y - hgt * s)], col, 1.0, sil)
        fill(layer, [(x + 22 * s, y - 92 * s), (x + 64 * s, y - 92 * s), (x + 64 * s, y - 102 * s), (x + 22 * s, y - 102 * s)], col, 1.0, sil)


def island(img, nz, cx, cy, width, depth_px, haze, seed, rng, gold=1.0):
    """A floating island: flat worn top, hanging rock teeth, strata and hatching, a gold rim; haze 0 near .. 1 far."""
    x0, x1 = int(max(0, cx - width / 2 - 4)), int(min(W, cx + width / 2 + 4))
    y0, y1 = int(max(0, cy - 30)), int(min(H, cy + depth_px + 30))
    if x1 <= x0 or y1 <= y0:
        return None
    xs = np.arange(x0, x1) + 0.5
    u = (xs - cx) / (width / 2)
    env = np.clip(1 - np.abs(u) ** 2.4, 0, 1)
    top = cy + 5 * (nz.fbm(xs / 46.0 + seed, np.full(xs.size, seed + 0.3), 3) - 0.5) * 2 - 6 * env
    teeth = np.zeros(xs.size)
    for _ in range(int(5 + width / 46)):
        tx = cx + rng.uniform(-0.82, 0.82) * width / 2
        tw = rng.uniform(0.05, 0.2) * width
        th = rng.uniform(0.35, 1.0)
        teeth = np.maximum(teeth, np.clip(1 - np.abs(xs - tx) / tw, 0, 1) ** 1.4 * th)
    rag = nz.fbm(xs / 9.0 + seed * 3, np.full(xs.size, seed), 4)
    under = top + depth_px * env ** 0.7 * (0.16 + 0.84 * teeth) * (0.74 + 0.5 * rag) + 3
    yy = (np.arange(y0, y1) + 0.5)[:, None]
    xg = np.broadcast_to(xs[None, :], (y1 - y0, xs.size))
    yg = np.broadcast_to(yy, xg.shape)
    cover = np.clip(yy - top[None, :] + 0.5, 0, 1) * np.clip(under[None, :] - yy + 0.5, 0, 1) * (env[None, :] > 0)
    t = np.clip((yy - top[None, :]) / np.maximum(under[None, :] - top[None, :], 1), 0, 1)
    strata = nz.fbm(xg / 7.0 + seed, yg / 70.0, 4)
    cracks = smooth(0.52, 0.6, nz.fbm(xg / 5.0 + 40 + seed, yg / 38.0, 3))
    hatch = 0.5 + 0.5 * np.sin((xg * 0.9 + yg * 0.55) * 1.35 + 6 * nz.fbm(xg / 60.0, yg / 60.0, 2))
    lit = smooth(0.0, 0.5, 1 - t) * (0.35 + 0.65 * strata)
    col = ROCK[None, None, :] * (0.55 + 0.9 * strata[..., None]) + (ROCK_LIT - ROCK)[None, None, :] * lit[..., None] * 0.9
    col = col * (1 - 0.42 * cracks[..., None])
    col = col + 0.035 * (smooth(0.75, 0.95, hatch) * (1 - t))[..., None]          # etched hatch on the lit rock
    col = col * (1 - 0.22 * smooth(0.8, 1.0, 1 - hatch) * t)[..., None]             # and in the shadow
    fade = np.clip(t ** 1.6 * 0.55 + haze * 0.85, 0, 0.93)
    col = col * (1 - fade[..., None]) + HAZE[None, None, :] * 0.62 * fade[..., None]
    region = img[y0:y1, x0:x1]
    region += (col - region) * cover[..., None]
    mark_solid(img, y0, x0, cover * (1 - haze))
    # worn grass line and the gold rim with drips
    rim = np.clip(1 - np.abs(yy - top[None, :] - 1.5) / 2.2, 0, 1) * (env[None, :] > 0.02)
    worn = smooth(0.38, 0.6, nz.fbm(xs / 13.0 + seed * 5, np.full(xs.size, 2.0), 3))[None, :]
    drip_len = 26 * smooth(0.62, 0.8, nz.fbm(xs / 4.0 + seed * 7, np.full(xs.size, 5.0), 2))[None, :] * gold
    drip = np.clip(1 - (yy - top[None, :]) / np.maximum(drip_len, 1e-3), 0, 1) * (yy > top[None, :]) * (drip_len > 2)
    g = np.clip(rim * worn + drip * 0.75, 0, 1) * cover.clip(0.25, 1) * (1 - haze * 0.75) * gold
    region += (GOLD[None, None, :] - region) * g[..., None]
    return top, xs


def cottage(img, x, y, s):
    wall, roof, beam = np.array([0.26, 0.20, 0.15]), np.array([0.105, 0.085, 0.075]), np.array([0.085, 0.07, 0.06])
    fill(img, [(x, y), (x + 150 * s, y), (x + 150 * s, y - 62 * s), (x, y - 62 * s)], wall)
    fill(img, [(x + 150 * s, y), (x + 232 * s, y), (x + 232 * s, y - 46 * s), (x + 150 * s, y - 46 * s)], wall * 0.86)
    for bx in (0, 36, 74, 112, 146, 190, 228):
        line(img, (x + bx * s, y), (x + bx * s, y - 62 * s if bx < 150 else y - 46 * s), 3.2 * s, beam)
    line(img, (x, y - 30 * s), (x + 150 * s, y - 30 * s), 3 * s, beam)
    for a, b in (((0, 0), (36, -30)), ((74, -30), (112, 0)), ((112, -62), (146, -30)), ((190, 0), (228, -46))):
        line(img, (x + a[0] * s, y + a[1] * s), (x + b[0] * s, y + b[1] * s), 2.4 * s, beam)
    fill(img, [(x - 14 * s, y - 58 * s), (x + 164 * s, y - 58 * s), (x + 118 * s, y - 132 * s), (x + 34 * s, y - 132 * s)], roof)
    fill(img, [(x + 142 * s, y - 44 * s), (x + 244 * s, y - 44 * s), (x + 214 * s, y - 92 * s), (x + 150 * s, y - 92 * s)], roof * 1.12)
    for k in range(9):       # shingle courses
        yy = y - (62 + k * 8) * s
        line(img, (x + (-10 + k * 5.6) * s, yy), (x + (160 - k * 5.4) * s, yy), 1.1 * s, roof * 1.9, 0.55)
    line(img, (x + 34 * s, y - 132 * s), (x + 118 * s, y - 132 * s), 3.4 * s, RUST * 0.8)
    line(img, (x + 150 * s, y - 92 * s), (x + 214 * s, y - 92 * s), 3.0 * s, RUST * 0.7)
    fill(img, [(x + 96 * s, y - 120 * s), (x + 112 * s, y - 120 * s), (x + 112 * s, y - 158 * s), (x + 96 * s, y - 158 * s)], roof * 1.2)
    fill(img, [(x + 58 * s, y - 126 * s), (x + 70 * s, y - 126 * s), (x + 70 * s, y - 150 * s), (x + 58 * s, y - 150 * s)], roof * 1.2)
    fill(img, [(x + 58 * s, y), (x + 82 * s, y), (x + 82 * s, y - 40 * s), (x + 58 * s, y - 40 * s)], beam * 1.3)
    for wx, wy, ww, wh in ((14, -52, 18, 16), (120, -24, 20, 18), (120, -54, 20, 16), (166, -34, 26, 22), (204, -34, 18, 20)):
        glow(img, x + (wx + ww / 2) * s, y + (wy + wh / 2) * s, 20 * s, GOLD, 0.26)
        fill(img, [(x + wx * s, y + wy * s), (x + (wx + ww) * s, y + wy * s), (x + (wx + ww) * s, y + (wy + wh) * s),
                   (x + wx * s, y + (wy + wh) * s)], GOLD_HOT)
        line(img, (x + (wx + ww / 2) * s, y + wy * s), (x + (wx + ww / 2) * s, y + (wy + wh) * s), 1.6 * s, beam)
        line(img, (x + wx * s, y + (wy + wh / 2) * s), (x + (wx + ww) * s, y + (wy + wh / 2) * s), 1.6 * s, beam)
    # lantern on a post
    line(img, (x - 34 * s, y), (x - 34 * s, y - 44 * s), 2.6 * s, beam)
    glow(img, x - 34 * s, y - 50 * s, 16 * s, GOLD, 0.5)
    disc(img, x - 34 * s, y - 50 * s, 4.5 * s, GOLD_HOT)


def windmill(img, x, y, s, turn=24.0):
    wood, dark, sail = np.array([0.20, 0.155, 0.12]), np.array([0.085, 0.07, 0.06]), np.array([0.62, 0.52, 0.42])
    fill(img, [(x - 30 * s, y), (x + 30 * s, y), (x + 17 * s, y - 128 * s), (x - 17 * s, y - 128 * s)], wood)
    for k in range(1, 7):
        yy = y - k * 18 * s
        half = (30 - 13 * k * 18 / 128) * s
        line(img, (x - half, yy), (x + half, yy), 1.4 * s, dark, 0.8)
    line(img, (x - 30 * s, y), (x + 17 * s, y - 128 * s), 1.6 * s, dark, 0.7)
    line(img, (x + 30 * s, y), (x - 17 * s, y - 128 * s), 1.6 * s, dark, 0.7)
    fill(img, [(x - 24 * s, y - 126 * s), (x + 24 * s, y - 126 * s), (x + 12 * s, y - 160 * s), (x - 12 * s, y - 160 * s)], dark * 1.5)
    hx, hy = x - 2 * s, y - 140 * s
    for i in range(4):
        a = math.radians(turn + 90 * i)
        dx, dy = math.cos(a), math.sin(a)
        nx, ny = -dy, dx
        line(img, (hx, hy), (hx + dx * 122 * s, hy + dy * 122 * s), 3.0 * s, dark)
        p0, p1 = 26 * s, 120 * s
        quad = [(hx + dx * p0 + nx * 3 * s, hy + dy * p0 + ny * 3 * s), (hx + dx * p1 + nx * 3 * s, hy + dy * p1 + ny * 3 * s),
                (hx + dx * p1 + nx * 34 * s, hy + dy * p1 + ny * 34 * s), (hx + dx * p0 + nx * 24 * s, hy + dy * p0 + ny * 24 * s)]
        fill(img, quad, sail, 0.86)
        for k in range(1, 6):
            q = p0 + (p1 - p0) * k / 6
            line(img, (hx + dx * q + nx * 3 * s, hy + dy * q + ny * 3 * s),
                 (hx + dx * q + nx * (24 + 10 * k / 6) * s, hy + dy * q + ny * (24 + 10 * k / 6) * s), 1.2 * s, dark, 0.8)
        line(img, quad[3], quad[2], 1.4 * s, dark, 0.9)
    disc(img, hx, hy, 5 * s, dark)
    line(img, (x, y - 160 * s), (x, y - 190 * s), 2.0 * s, dark)
    fill(img, [(x, y - 190 * s), (x + 26 * s, y - 184 * s), (x, y - 177 * s)], RUST)


def fence(img, x0, x1, top, xs, s, rng):
    col = np.array([0.10, 0.08, 0.068])
    prev = None
    x = x0
    while x < x1:
        y = float(np.interp(x, xs, top)) + 1
        hgt = rng.uniform(15, 21) * s
        line(img, (x, y), (x + rng.uniform(-1.5, 1.5), y - hgt), 2.2 * s, col)
        if prev:
            line(img, (prev[0], prev[1] - 13 * s), (x, y - 13 * s), 1.4 * s, col)
            line(img, (prev[0], prev[1] - 6 * s), (x, y - 6 * s), 1.4 * s, col)
        prev = (x, y)
        x += rng.uniform(17, 24) * s


def ribbons(img, nz, rng):
    yy, xx = np.mgrid[0:H, 0:W] + 0.5
    for i in range(4):
        base = (0.16 + 0.22 * i + rng.uniform(-0.05, 0.05)) * H
        slope = rng.uniform(-0.38, -0.12)
        ph = rng.uniform(0, 6.28, 3)
        centre = (base + slope * (xx - W * 0.55) + 70 * np.sin(xx / 310.0 + ph[0]) + 34 * np.sin(xx / 137.0 + ph[1])
                  + 120 * (nz.fbm(xx / 520.0 + i * 3.1, np.full_like(xx, i * 1.3), 2) - 0.5))
        thick = (16 + 34 * nz.fbm(xx / 260.0 + i * 9.0, np.full_like(xx, 1.0 + i), 2)) * rng.uniform(0.6, 1.25)
        v = (yy - centre) / thick
        strands = 0.5 + 0.5 * np.sin(v * rng.uniform(9, 15) + 3.0 * nz.fbm(xx / 150.0 + i, v * 0.8 + i, 2))
        body = np.exp(-(v * v) * 1.3) * (0.22 + 0.78 * strands ** 3)
        along = smooth(0.2, 0.55, nz.fbm(xx / 430.0 + i * 5.7, np.full_like(xx, 7.0), 2)) * smooth(0.0, 0.22, xx / W)
        img += (ASH_BLUE - img) * (body * along * rng.uniform(0.16, 0.30))[..., None]


def etch(img, nz, solid):
    """The engraver's pass: ink lines along the edges of solid things, cross-hatching that thickens in their shadows,
    and brush mottling everywhere, so no shape is left as a clean flat fill and the mist stays soft."""
    yy, xx = np.mgrid[0:H, 0:W] + 0.5
    lum = img @ np.array([0.3, 0.55, 0.15])
    gy, gx = np.gradient(lum)
    edge = np.hypot(gx, gy)
    near = np.clip(solid * 1.5, 0, 1)
    for _ in range(3):      # let the ink line sit just outside the shape too
        near = np.maximum(near, 0.25 * (np.roll(near, 1, 0) + np.roll(near, -1, 0) + np.roll(near, 1, 1) + np.roll(near, -1, 1)))
    wob = nz.fbm(xx / 5.0, yy / 5.0, 2)
    img = img * (1 - 0.66 * smooth(0.012, 0.07, edge * (0.6 + 0.8 * wob)) * (0.12 + 0.88 * near))[..., None]
    mott = nz.fbm(xx / 26.0 + 3, yy / 20.0 + 5, 4)
    img = img * (0.90 + 0.20 * mott)[..., None]
    warp = 7.0 * nz.fbm(xx / 90.0 + 11, yy / 90.0 + 4, 3)
    shade = 1 - smooth(0.04, 0.34, lum)
    h1 = smooth(0.55, 0.95, 0.5 + 0.5 * np.sin((xx + yy * 0.8) * 1.05 + warp))
    h2 = smooth(0.62, 0.95, 0.5 + 0.5 * np.sin((xx - yy * 0.9) * 1.0 - warp))
    gaps = smooth(0.3, 0.6, nz.fbm(xx / 14.0 + 21, yy / 14.0 + 8, 3))
    lit = smooth(0.06, 0.40, lum)
    on = 0.06 + 0.94 * np.clip(solid, 0, 1)
    img = img * (1 - 0.34 * h1 * gaps * (0.25 + 0.75 * shade) * lit * on)[..., None]
    img = img * (1 - 0.24 * h2 * gaps * smooth(0.45, 0.9, shade) * lit * on)[..., None]
    return img


def ground():
    nz = Noise(SEED)
    rng = np.random.default_rng(SEED)
    yy, xx = np.mgrid[0:H, 0:W] + 0.5
    u, v = xx / W, yy / H

    # sky: dark at the left and the corners, a warm lit haze upper right where the far clock hangs
    warp_x = xx + 160 * (nz.fbm(xx / 420.0, yy / 420.0, 3) - 0.5)
    warp_y = yy + 160 * (nz.fbm(xx / 420.0 + 31, yy / 420.0 + 7, 3) - 0.5)
    cloud = nz.fbm(warp_x / 330.0, warp_y / 190.0, 6)
    wisps = nz.fbm(warp_x / 120.0 + 50, warp_y / 46.0, 5)
    light = np.exp(-(((u - 0.80) / 0.36) ** 2 + ((v - 0.20) / 0.30) ** 2))
    side = smooth(0.16, 0.62, u)
    lum = 0.085 + side * (0.10 + 0.34 * smooth(0.30, 0.78, cloud)) + 0.30 * light * (0.45 + 0.55 * cloud)
    img = np.empty((H, W, 3))
    img[:] = HAZE
    img *= lum[..., None] / 0.44
    img += (HAZE_WARM - HAZE)[None, None, :] * (light * (0.4 + 0.6 * cloud) * 1.25)[..., None]
    SOLID["img"], SOLID["mask"] = img, np.zeros((H, W))

    # far ridges with ruins, each one nearer and darker; mist pools between them
    ridge(img, nz, H * 0.265, 46, 300, 0.80, 3.0, [("castle", W * 0.545, 0.62), ("arches", W * 0.585, 0.5), ("aqueduct", W * 0.895, 0.5)])
    # the far clock in the lit haze, half lost in cloud
    clock_face(img, W * 0.795, H * 0.20, 196, np.array([0.30, 0.235, 0.18]), 0.80, nz, 255, 105, True, [(214, 0.62, 5), (148, 0.42, 6)], 0.42)
    clock_face(img, W * 0.708, H * 0.19, 62, np.array([0.33, 0.26, 0.20]), 0.6, nz, 250, 110, False, None, 0.4)

    mist = smooth(0.42, 0.82, nz.fbm(warp_x / 300.0 + 9, warp_y / 90.0 + 3, 5))
    mix(img, HAZE * 0.86 + HAZE_WARM * 0.12, mist * 0.42 * side * smooth(0.15, 0.4, v))
    ridge(img, nz, H * 0.35, 60, 360, 0.60, 8.0, [("aqueduct", W * 0.63, 0.62), ("columns", W * 0.83, 0.5), ("arches", W * 0.92, 0.7)])
    mist = smooth(0.40, 0.80, nz.fbm(warp_x / 260.0 + 19, warp_y / 80.0 + 13, 5))
    mix(img, HAZE * 0.74, mist * 0.5 * side * smooth(0.25, 0.5, v))
    ridge(img, nz, H * 0.50, 84, 420, 0.42, 14.0, [("columns", W * 0.70, 0.9)])
    mist = smooth(0.36, 0.78, nz.fbm(warp_x / 300.0 + 29, warp_y / 100.0 + 23, 5))
    mix(img, HAZE * 0.66, mist * 0.62 * side * smooth(0.36, 0.62, v))
    mix(img, HAZE * 0.5, smooth(0.45, 0.8, wisps) * 0.28 * side)

    # floating islands, far to near
    island(img, nz, W * 0.985, H * 0.085, 330, 150, 0.55, 2.0, rng, 0.5)
    island(img, nz, W * 0.555, H * 0.83, 150, 120, 0.50, 4.0, rng, 0.6)
    top, xs = island(img, nz, W * 0.640, H * 0.295, 170, 150, 0.38, 6.0, rng, 0.9)
    fence(img, W * 0.625, W * 0.66, top, xs, 0.5, rng)
    top, xs = island(img, nz, W * 0.485, H * 0.425, 330, 250, 0.26, 8.0, rng)
    arch_row(img, np.zeros((H, W)), W * 0.482, float(np.interp(W * 0.5, xs, top)) + 3, 1.0, np.array([0.115, 0.095, 0.082]), 2, 78)
    island(img, nz, W * 0.445, H * 0.70, 230, 120, 0.34, 10.0, rng, 0.8)
    mist = smooth(0.42, 0.82, nz.fbm(warp_x / 240.0 + 41, warp_y / 70.0 + 37, 5))
    mix(img, HAZE * 0.56, mist * 0.36 * side * smooth(0.3, 0.7, v))

    # the near island with the bridge, the windmill and the lit cottage
    top, xs = island(img, nz, W * 0.655, H * 0.652, 300, 150, 0.12, 12.0, rng)
    arch_row(img, np.zeros((H, W)), W * 0.612, float(np.interp(W * 0.64, xs, top)) + 46, 1.15, np.array([0.16, 0.128, 0.105]), 2, 46)
    top, xs = island(img, nz, W * 0.845, H * 0.70, 760, 520, 0.02, 14.0, rng)
    gy = float(np.interp(W * 0.86, xs, top))
    fence(img, W * 0.69, W * 0.775, top, xs, 1.0, rng)
    windmill(img, W * 0.775, float(np.interp(W * 0.775, xs, top)) + 4, 1.0)
    cottage(img, W * 0.822, gy + 4, 1.0)
    fence(img, W * 0.80, W * 0.99, top + 46, xs, 1.0, rng)
    # chimney smoke
    sx, sy = W * 0.822 + 104, gy - 160
    smoke = np.exp(-(((xx - sx - 0.25 * (sy - yy) - 16 * np.sin((sy - yy) / 34.0)) / (7 + 0.16 * (sy - yy).clip(0))) ** 2)) \
        * smooth(0, 16, sy - yy) * (1 - smooth(70, 190, sy - yy)) * (0.4 + 0.6 * nz.fbm(xx / 20.0, yy / 20.0, 3))
    mix(img, HAZE * 1.25, smoke * 0.5)
    # flowers and grass flecks on the near island
    for _ in range(420):
        fx = rng.uniform(W * 0.66, W * 1.0)
        fy = float(np.interp(fx, xs, top)) + rng.uniform(2, 58) * rng.random()
        pick = rng.random()
        if pick < 0.12:      # poppies: the rust accent
            disc(img, fx, fy, rng.uniform(1.8, 3.2), RUST * rng.uniform(0.85, 1.25), 0.95)
        elif pick < 0.34:
            disc(img, fx, fy, rng.uniform(1.4, 2.8), CREAM * rng.uniform(0.7, 1.0), 0.9)
        else:
            line(img, (fx, fy), (fx + rng.uniform(-3, 3), fy - rng.uniform(4, 10)), 1.1, ROCK_LIT * rng.uniform(0.8, 1.5), 0.8)

    ribbons(img, nz, rng)

    # the left third goes dark for the lettering; the title clock arc sits behind the lockup
    dark = (1 - smooth(0.20, 0.52, u)) * 0.80
    img *= (1 - dark)[..., None]
    img += (INK * 1.05)[None, None, :] * (dark * (0.75 + 0.5 * cloud))[..., None]
    clock_face(img, W * 0.218, H * 0.332, 268, GOLD * 0.86, 0.88, nz, 318, 112, True, None, 0.34)

    # embers
    for _ in range(170):
        ex, ey = rng.uniform(0, W), rng.uniform(0, H)
        b = rng.uniform(0.25, 1.0) ** 2
        glow(img, ex, ey, rng.uniform(2.0, 4.5), GOLD, 0.16 * b)
        disc(img, ex, ey, rng.uniform(0.7, 1.5), GOLD_HOT, 0.85 * b)

    img = etch(np.clip(img, 0, 1), nz, SOLID["mask"])

    # paper: stains, fibres and grain over everything, then the painted vignette
    stain = nz.fbm(xx / 520.0 + 77, yy / 520.0 + 71, 4)
    img *= (0.86 + 0.28 * stain)[..., None]
    fibre = nz.fbm(xx / 2.2 + 13, yy / 44.0 + 3, 3) * 0.6 + nz.fbm(xx / 46.0, yy / 2.4 + 9, 3) * 0.4
    grain = rng.normal(0.0, 1.0, (H, W))
    tooth = nz.value(xx / 1.7 + 5, yy / 1.7 + 8)
    img *= (1.0 + 0.16 * (fibre - 0.5) + 0.10 * (tooth - 0.5))[..., None]
    img += (0.018 * grain)[..., None] * (0.5 + img)
    speck = rng.random((H, W))
    img *= (1 - 0.35 * (speck > 0.9985))[..., None]
    vig = 1 - 0.62 * smooth(0.52, 1.08, np.hypot((u - 0.5) * 1.06, (v - 0.5) * 1.18) * 1.6)
    img *= vig[..., None]
    return np.clip(img, 0, 1)


def clock_png():
    """The HUD clock face: an etched gold dial on a smoked glass disc, transparent outside."""
    n = 512
    nz = Noise(SEED + 5)
    rng = np.random.default_rng(SEED + 5)
    img = np.zeros((n, n, 3))
    yy, xx = np.mgrid[0:n, 0:n] + 0.5
    r = np.hypot(xx - n / 2, yy - n / 2)
    face = INK * 1.1 + (ROCK - INK) * nz.fbm(xx / 60.0, yy / 60.0, 4)[..., None] * 0.9
    img[:] = face
    img *= (1.0 - 0.45 * smooth(60, 250, r))[..., None]
    clock_face(img, n / 2, n / 2, 236, GOLD, 0.95, nz, 0, 360, False, None, 0.16)   # numerals stay live text in the HUD
    ring(img, n / 2, n / 2, 248, 5.0, GOLD * 0.62, 0.95)
    ring(img, n / 2, n / 2, 96, 1.4, GOLD * 0.7, 0.7)
    grain = rng.normal(0.0, 1.0, (n, n))
    img += (0.02 * grain)[..., None]
    alpha = np.clip(252.5 - r, 0, 1) * (0.80 + 0.2 * smooth(150, 250, r))
    return np.clip(img, 0, 1), alpha


def write_png(path, rgb, alpha=None):
    h, w = rgb.shape[:2]
    data = np.round(rgb * 255).astype(np.uint8)
    if alpha is not None:
        data = np.dstack([data, np.round(alpha * 255).astype(np.uint8)])
    raw = b"".join(b"\0" + data[y].tobytes() for y in range(h))

    def chunk(tag, body):
        return struct.pack(">I", len(body)) + tag + body + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF)
    with open(path, "wb") as fh:
        fh.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6 if alpha is not None else 2, 0, 0, 0))
                 + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def main(argv):
    out = HERE
    only = None
    if "--out" in argv:
        out = argv[argv.index("--out") + 1]
    if "--only" in argv:
        only = argv[argv.index("--only") + 1]
    os.makedirs(out, exist_ok=True)
    if only in (None, "ground"):
        write_png(os.path.join(out, "T_UI_Ground_PH.png"), ground())
        print("build_ground: wrote T_UI_Ground_PH.png")
    if only in (None, "clock"):
        rgb, a = clock_png()
        write_png(os.path.join(out, "T_UI_ClockFace_PH.png"), rgb, a)
        print("build_ground: wrote T_UI_ClockFace_PH.png")


if __name__ == "__main__":
    main(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
