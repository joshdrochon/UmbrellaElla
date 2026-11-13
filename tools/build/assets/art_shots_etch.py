"""The shots art lane as engraved prints made in Blender (owl-bolt, wand-shot, bolt-hit).

Run (Blender only, never python3):
  Blender -b --factory-startup -P tools/build/assets/art_shots_etch.py -- <piece> <out.png> [seed] [--blend out.blend] [--mul 2]
piece: owl-bolt | wand-shot | bolt-hit

Technique (rounds 3 to 9 all lost on "flat vector fills, no etched line, no paper grain, no ink value structure"):
the piece is no longer a stack of flat polygons. It is built the way an engraver builds a plate:
  1. a continuous TONE field (0 = ink, 1 = pale core) from nested angular outlines, lit from above, fading to the tail;
  2. the tone is cut into the piece's palette ramp (ink, shadow, shell, hot, core) through a LINE SCREEN: between two
     neighbouring ramp colours the lighter one is laid as parallel engraved lines whose width follows the tone, the
     lines running along the swept blades (the bolt), the rays (the burst) or the star points (the pulse);
  3. paper tooth: grain in the threshold breaks every line the way laid paper breaks an ink line;
  4. a broken near-black ink contour on the shadow side, heavier where the form turns away from the light;
  5. the light is a tight stippled spill around the shot (alpha under 0.5: light, not body), never an airbrush halo.
Every opaque pixel is exactly one ramp colour (GDD SH1.0 hexes, pipeline/art/style.json accents), like a limited-palette
print, so nothing lands between two approved colours. The outlines are kept in the .blend as curve objects and the
print as a packed image on a plane. Nothing is traced from a reference; the drawing is generated here from numbers.
"""
import math
import sys

import bpy
import numpy as np

ARGV = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
BLEND = None
if "--blend" in ARGV:
    i = ARGV.index("--blend")
    BLEND = ARGV[i + 1]
    del ARGV[i:i + 2]
MUL = 1
if "--mul" in ARGV:
    i = ARGV.index("--mul")
    MUL = int(ARGV[i + 1])
    del ARGV[i:i + 2]
PIECE = ARGV[0] if ARGV else "owl-bolt"
OUT = ARGV[1] if len(ARGV) > 1 else "/tmp/shot_etch.png"
SEED = int(ARGV[2]) if len(ARGV) > 2 else 11
RNG = np.random.default_rng(SEED)

# frame size at 4x the layout cell (OwlBolt 160x80, WandShot 128x64, BoltHit 128x128)
SIZES = {"owl-bolt": (640, 320), "wand-shot": (512, 256), "bolt-hit": (512, 512)}
W, H = (v * MUL for v in SIZES[PIECE])   # --mul 2: an 8x master
SS = 3   # tone and coverage are computed at SS x and averaged down


def hx(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


RED = [("ink", "171614"), ("shadow", "8F173C"), ("shell", "FF3658"), ("hot", "FF7848"), ("core", "FFF5DC")]
GOLD = [("ink", "171614"), ("shadow", "94611E"), ("shell", "F5AA28"), ("hot", "FFD84A"), ("core", "FFF5DC")]
PULSE = [("ink", "171614"), ("shadow", "94611E"), ("shell", "F5AA28"), ("hot", "E9C46A"), ("core", "FFF5DC")]

OUTLINES = []   # (name, polygon) kept in the .blend as editable curves

YS, XS = np.mgrid[0:H * SS, 0:W * SS]
XS = (XS + 0.5) / SS
YS = (YS + 0.5) / SS
YF, XF = np.mgrid[0:H, 0:W]
XF = XF + 0.5
YF = YF + 0.5


# ---------------------------------------------------------------- raster helpers
def poly_mask(poly):
    """Even-odd fill of a polygon on the supersampled grid (bool)."""
    out = np.zeros(XS.shape, bool)
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    x0 = max(0, int(min(xs) * SS) - 1)
    x1 = min(W * SS, int(max(xs) * SS) + 2)
    y0 = max(0, int(min(ys) * SS) - 1)
    y1 = min(H * SS, int(max(ys) * SS) + 2)
    if x1 <= x0 or y1 <= y0:
        return out
    X = XS[y0:y1, x0:x1]
    Y = YS[y0:y1, x0:x1]
    m = np.zeros(X.shape, bool)
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if yi != yj:
            m ^= ((yi > Y) != (yj > Y)) & (X < (xj - xi) * (Y - yi) / (yj - yi) + xi)
        j = i
    out[y0:y1, x0:x1] = m
    return out


def box(a, r, axis):
    if r < 1:
        return a
    pad = [(0, 0), (0, 0)]
    pad[axis] = (r + 1, r)
    c = np.cumsum(np.pad(a, pad, mode="edge"), axis=axis)
    n = a.shape[axis]
    hi = np.take(c, np.arange(2 * r + 1, 2 * r + 1 + n), axis=axis)
    lo = np.take(c, np.arange(0, n), axis=axis)
    return (hi - lo) / (2 * r + 1)


def blur(a, sigma):
    """Gaussian-like blur: three box passes."""
    r = max(1, int(round(sigma * 0.95)))
    a = a.astype(float)
    for _ in range(3):
        a = box(box(a, r, 0), r, 1)
    return a


def down(a):
    return a.reshape(H, SS, W, SS).mean(axis=(1, 3))


def vnoise(cell, shape=None):
    """Smooth value noise in 0..1 with features about `cell` px."""
    h, w = shape or (H, W)
    gh, gw = int(h / cell) + 3, int(w / cell) + 3
    g = RNG.random((gh, gw))
    yy, xx = np.mgrid[0:h, 0:w]
    fy, fx = yy / cell, xx / cell
    iy, ix = fy.astype(int), fx.astype(int)
    ty, tx = fy - iy, fx - ix
    ty = ty * ty * (3 - 2 * ty)
    tx = tx * tx * (3 - 2 * tx)
    return (g[iy, ix] * (1 - ty) * (1 - tx) + g[iy + 1, ix] * ty * (1 - tx)
            + g[iy, ix + 1] * (1 - ty) * tx + g[iy + 1, ix + 1] * ty * tx)


def sstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def scaled(poly, cx, cy, sx, sy):
    return [(cx + (x - cx) * sx, cy + (y - cy) * sy) for x, y in poly]


def screen(phase, tone_shape, tooth, soft):
    """A hand-cut line screen as a threshold field: every line has its own weight, wanders a little and breaks."""
    phase = phase + (vnoise(11 * MUL, tone_shape) - 0.5) * 0.30
    line = np.floor(phase).astype(int)
    weight = (RNG.random(8192) - 0.5)[line % 8192]              # some lines cut deeper than others
    tri = np.abs(2 * (phase - np.floor(phase)) - 1)           # 0 on the line centre .. 1 between lines
    grain = RNG.random(tone_shape) - 0.5
    mott = vnoise(9 * MUL, tone_shape) - 0.5
    lift = vnoise(26 * MUL, tone_shape) - 0.5                  # where the burin lifts: the line thins or breaks
    return np.clip(0.5 + (tri - 0.5) * soft + weight * 0.26 + grain * tooth + mott * 0.18 + lift * 0.22, 0.02, 0.98)


def engrave(tone, phase, ramp, stops, tooth=0.3, soft=0.9, phase2=None):
    """Cut a tone field (final grid) into the ramp through a line screen. phase: screen phase in line periods;
    phase2: a second, crossing screen that only bites in the darkest step (cross-hatched ink in the deep shadow).
    Returns an index image into the ramp."""
    thr = screen(phase, tone.shape, tooth, soft)
    thr2 = screen(phase2, tone.shape, tooth, soft) if phase2 is not None else None
    idx = np.zeros(tone.shape, int)
    for k in range(len(stops) - 1):
        a, b = stops[k], stops[k + 1]
        f = (tone - a) / (b - a)
        up = (f > thr) & (tone >= a)
        if k == 0 and thr2 is not None:
            up &= f > thr2 * 0.62
        idx = np.where(up, k + 1, idx)
    return idx


def finish(tone_s, mask_s, phase, ramp, stops, light=(0.0, -1.0), halo_rgb=None, halo_r=7.0, halo_a=0.4,
           ink_w=2, tooth=0.3, soft=0.9, ink_skip=0.35, no_ink=None, phase2=None):
    """tone and mask on the supersampled grid -> RGBA print on the final grid."""
    tone = down(np.where(mask_s, tone_s, 0.0)) / np.maximum(down(mask_s.astype(float)), 1e-6)
    cov = down(mask_s.astype(float))
    body = cov >= 0.5
    idx = engrave(tone, phase, ramp, stops, tooth, soft, phase2)
    # broken ink contour on the side turned away from the light
    dy = 1 if light[1] < 0 else -1
    edge = np.zeros(body.shape, bool)
    for k in range(1, ink_w + 1):
        sh = np.roll(body, -k * dy, axis=0)
        edge |= body & ~sh
    brk = vnoise(14, body.shape)
    edge &= brk > ink_skip
    thin = body & ~np.roll(body, -dy, axis=0)                 # the 1 px line survives more of the breaks
    edge |= thin & (brk > ink_skip * 0.5)
    # a finer, more broken ink line round the rest of the silhouette (the lit side lifts off the paper)
    rim = np.zeros(body.shape, bool)
    for k in range(1, MUL + 1):
        for ax, sh in ((0, k * dy), (1, k), (1, -k)):
            rim |= body & ~np.roll(body, sh, axis=ax)
    edge |= rim & (vnoise(18 * MUL, body.shape) > 0.42)
    if no_ink is not None:
        edge &= down(no_ink.astype(float)) < 0.5
    idx = np.where(edge, 0, idx)
    cols = np.array([hx(c) for _, c in ramp], float)
    rgb = cols[idx]
    alpha = np.where(body, 1.0, 0.0)
    # anti-aliased silhouette: partly covered edge pixels carry the nearest body colour at low alpha
    if halo_rgb is not None:
        spill = blur(body.astype(float), halo_r)
        spill = np.clip(spill * 2.0, 0, 1) ** 1.6
        speck = RNG.random(body.shape)
        m2 = vnoise(6, body.shape)
        a = halo_a * spill * (0.55 + 0.9 * m2) * (speck > 0.3)
        a = np.clip(a, 0, 0.46)
        out_side = ~body
        rgb = np.where(out_side[..., None], np.array(halo_rgb, float)[None, None], rgb)
        alpha = np.where(out_side, a, alpha)
    return np.dstack([rgb / 255.0, alpha])


def save(rgba):
    img = bpy.data.images.new(PIECE + "_print", W, H, alpha=True)
    img.alpha_mode = "STRAIGHT"
    img.pixels = rgba[::-1].astype(np.float32).ravel()
    img.filepath_raw = OUT
    img.file_format = "PNG"
    img.save()
    return img


# ---------------------------------------------------------------- owl-bolt
def bolt_body(k, ox, Y):
    """Tone and mask of the bolt's body (no flecks): k = px per design unit, ox = x offset in px."""
    top = [(30, 0), (215, 64), (175, 33), (288, 66), (246, 32), (362, 52), (315, 24), (410, 12), (530, 1.6)]
    bot = [(530, 1.6), (418, 10), (392, 28), (362, 15), (338, 48), (298, 24), (275, 62), (236, 31), (198, 56),
           (165, 29)]
    notches = [(175, -33), (246, -32), (315, -24), (165, 29), (236, 31), (298, 24), (362, 15)]
    outline = [(ox + x * k, Y - d * k) for x, d in top] + [(ox + x * k, Y + d * k) for x, d in bot]
    OUTLINES.append(("silhouette", outline))
    n = 11
    tone = np.zeros(XS.shape)
    mask = poly_mask(outline)
    cx = ox + 235 * k
    for i in range(n):
        f = i / (n - 1)
        sx = 1 - 0.34 * f
        sy = 1 - 0.86 * f ** 0.8
        p = scaled(outline, cx, Y, sx, sy)
        p = [(x - 10 * k * f, y) for x, y in p]
        if i in (3, 6, 10):
            OUTLINES.append((f"layer{i}", p))
        tone = np.where(poly_mask(p), 0.20 + 0.80 * f ** 0.8, tone)
    tone = blur(tone, 1.2 * SS * k)
    # light from above: the upper faces lift, the under side drops; the tail cools toward its end
    up = sstep(-3 * k, 3 * k, Y - YS)
    lit = (up - 0.5) * 0.20
    core_w = sstep(0.75, 0.95, tone)
    tone = tone + lit * (1 - core_w)
    tone = tone * (1 - 0.55 * sstep(ox + 300 * k, ox + 510 * k, XS))
    # the crease behind each barb: a dark wedge from the notch toward the core
    for nx, nd in notches:
        ax, ay, bx, by = ox + nx * k, Y + nd * k, ox + (nx - 60) * k, Y + nd * 0.3 * k
        t = np.clip(((XS - ax) * (bx - ax) + (YS - ay) * (by - ay)) / ((bx - ax) ** 2 + (by - ay) ** 2), 0, 1)
        dist = np.hypot(XS - (ax + t * (bx - ax)), YS - (ay + t * (by - ay)))
        tone = tone - 0.24 * (1 - t) * np.exp(-(dist / (3.2 * k)) ** 2) * (1 - core_w)
    tone = np.where(mask, np.clip(tone, 0.06, 1.0), 0.0)
    return tone, mask


def bolt(ramp):
    """The GDD SH1.0 shared red projectile, pointing left: one clean head point, three swept barbs a side, nested
    layers from the magenta-red shadow edge in to the pale core, a narrow tail about one head long, square flecks."""
    Y = H / 2.0
    k = W / 640.0
    tone, mask = bolt_body(k, 0.0, Y)
    # square flecks on short dashed lines beside the tail (tidy, sparse)
    flecks = []
    no_ink = np.zeros(XS.shape, bool)
    for (fx, fy, s, t, rot) in ((452, -30, 6.5, 0.40, 0.2), (500, 24, 6.0, 0.28, -0.15), (528, -17, 4.8, 0.28, 0.1),
                                (470, 38, 4.8, 0.40, 0.3)):
        sq = [((fx + math.cos(rot + q * math.pi / 2 + math.pi / 4) * s) * k,
               Y + (fy + math.sin(rot + q * math.pi / 2 + math.pi / 4) * s) * k) for q in range(4)]
        flecks.append((sq, t))
        side = -1 if fy < 0 else 1
        for d in range(2):
            x0 = fx - 22 - d * 24
            y0 = fy - side * (2 + d * 2.5)
            dash = [(x0 * k, Y + (y0 - 0.9) * k), ((x0 + 14) * k, Y + (y0 + side * 1.2 - 0.9) * k),
                    ((x0 + 14) * k, Y + (y0 + side * 1.2 + 0.9) * k), (x0 * k, Y + (y0 + 0.9) * k)]
            flecks.append((dash, 0.30))
    for sq, t in flecks:
        m = poly_mask(sq)
        tone = np.where(m, t, tone)
        mask |= m
        no_ink |= m
        OUTLINES.append(("fleck", sq))
    stops = [0.0, 0.22, 0.47, 0.70, 0.93]
    period = 5.2 * k / (1.55 if MUL > 1 else 1.0)   # finer lines on the 8x master
    wav = (vnoise(40 * MUL) - 0.5) * 0.6
    phase = (0.30 * XF - 0.954 * np.abs(YF - Y)) / period + wav
    phase2 = (0.80 * XF + 0.60 * np.abs(YF - Y)) / (period * 0.9)
    return finish(tone, mask, phase, ramp, stops, halo_rgb=hx(ramp[2][1]), halo_r=6 * k, halo_a=0.42,
                  ink_w=max(1, int(round(2 * k))), no_ink=no_ink, phase2=phase2)


# ---------------------------------------------------------------- bolt-hit
def burst(ramp):
    """The red shot's impact, in the release-burst form (the GDD draws no impact; discord-crop-red-release): a compact
    crimson starburst of thin rays of uneven length around a pale core where the head struck, the rest of the shot
    still driving into it from behind, engraved along the rays and the blades."""
    k = W / 512.0
    cx, cy = 150 * k, H / 2.0
    rays = []
    nr = 16
    for i in range(nr):
        a = i * 2 * math.pi / nr + RNG.uniform(-0.07, 0.07)
        L = (RNG.uniform(118, 140) if i % 4 == 0 else RNG.uniform(86, 106) if i % 2 == 0 else RNG.uniform(60, 76))
        rays.append((a, L * k))

    def star(scale_l, inner, wid):
        out = []
        for i, (a, L) in enumerate(rays):
            a2 = (a + rays[(i + 1) % nr][0] + (2 * math.pi if i == nr - 1 else 0)) / 2
            tip = max(inner * 1.05, L * scale_l)
            out.append((cx + math.cos(a - wid) * inner, cy + math.sin(a - wid) * inner))
            out.append((cx + math.cos(a) * tip, cy + math.sin(a) * tip))
            out.append((cx + math.cos(a + wid) * inner, cy + math.sin(a + wid) * inner))
            out.append((cx + math.cos(a2) * inner * 0.86, cy + math.sin(a2) * inner * 0.86))
        return out
    hub = 40 * k
    # the shot behind the burst: the same body as owl-bolt, smaller, its head buried in the flash
    kb = 0.60 * k
    b_tone, b_mask = bolt_body(kb, cx - 55 * kb, cy)
    n = 10
    tone = np.zeros(XS.shape)
    outline = star(1.0, hub, 0.17)
    OUTLINES.append(("burst", outline))
    rr = np.hypot(XS - cx, YS - cy)
    s_mask = poly_mask(outline) | (rr < hub * 0.94)
    for i in range(n):
        f = i / (n - 1)
        p = star(1.0 - 0.70 * f, hub * (1 - 0.7 * f), 0.17 * (1 - 0.35 * f))
        m = poly_mask(p) | (rr < hub * 0.94 * (1 - 0.7 * f))
        if i in (4, 9):
            OUTLINES.append((f"burst_layer{i}", p))
        tone = np.where(m, 0.20 + 0.80 * f ** 0.85, tone)
    tone = blur(tone, 1.1 * SS * k)
    tone = tone + 0.30 * np.exp(-(rr / (14 * k)) ** 2)           # the flash at the centre
    tone = tone - 0.12 * sstep(-4 * k, 4 * k, YS - cy) * (rr > 20 * k)   # under side in shadow
    tone = np.where(s_mask, np.clip(tone, 0.06, 1.0), 0.0)
    tone = np.maximum(tone, b_tone)                              # burst and shot fuse where they overlap
    mask = s_mask | b_mask
    # flecks thrown outward
    no_ink = np.zeros(XS.shape, bool)
    for j, (a, r, sz) in enumerate(((2.2, 150, 6.5), (3.6, 135, 5.0), (4.4, 150, 6.0), (1.35, 142, 5.0),
                                    (5.1, 128, 4.5))):
        s = sz * k
        x, y = cx + math.cos(a) * r * k, cy + math.sin(a) * r * k
        sq = [(x + math.cos(a + q * math.pi / 2 + 0.5) * s, y + math.sin(a + q * math.pi / 2 + 0.5) * s)
              for q in range(4)]
        m = poly_mask(sq)
        tone = np.where(m, 0.28 if j % 2 else 0.40, tone)
        mask |= m
        no_ink |= m
        OUTLINES.append(("fleck", sq))
    stops = [0.0, 0.22, 0.47, 0.70, 0.93]
    ang = np.arctan2(YF - cy, XF - cx)
    rf = np.hypot(XF - cx, YF - cy)
    radial = ang / (2 * math.pi) * 56 + rf / (90 * k)
    swept = (0.30 * XF - 0.954 * np.abs(YF - cy)) / (5.2 * kb * (1.0 if MUL > 1 else 1.6))
    in_burst = down((s_mask & ~(b_mask & (rr > hub * 1.1))).astype(float)) > 0.5
    phase = np.where(in_burst, radial, swept) + (vnoise(40 * MUL) - 0.5) * 0.5
    return finish(tone, mask, phase, ramp, stops, halo_rgb=hx(ramp[2][1]), halo_r=11 * k, halo_a=0.44,
                  ink_w=max(1, int(round(1.5 * k))), no_ink=no_ink)


# ---------------------------------------------------------------- wand-shot
def pulse(ramp):
    """Ella's compact gold pulse (GDD SH1.0 COM-06 Small Blasts, Twin Stars heads), faces right: a four-point star
    head with short diagonal points, a pale core, a short tapered tail, a few tiny star sparks."""
    Y = H / 2.0
    k = W / 512.0
    hxc = 385 * k
    main = [(0.0, 112), (math.pi / 2, 74), (math.pi, 70), (3 * math.pi / 2, 74)]
    diag = [(math.pi / 4, 42), (3 * math.pi / 4, 36), (5 * math.pi / 4, 36), (7 * math.pi / 4, 42)]
    allr = sorted(main + diag)

    def star(cx, cy, rays, inner, s=1.0):
        out = []
        nn = len(rays)
        for i, (a, L) in enumerate(rays):
            out.append((cx + math.cos(a) * L * s, cy + math.sin(a) * L * s))
            a2 = (a + rays[(i + 1) % nn][0] + (2 * math.pi if i == nn - 1 else 0)) / 2
            out.append((cx + math.cos(a2) * inner * s, cy + math.sin(a2) * inner * s))
        return out

    def tail(s):
        x0, x1 = 200 * k, hxc
        pts_t, pts_b = [], []
        for j in range(25):
            u = j / 24
            x = x0 + (x1 - x0) * u
            hgt = 19 * k * u ** 1.5 * s + 0.6 * k
            pts_t.append((x, Y - hgt))
            pts_b.append((x, Y + hgt))
        return pts_t + pts_b[::-1]
    head = star(hxc, Y, [(a, L * k) for a, L in allr], 17 * k)
    OUTLINES.append(("head", head))
    OUTLINES.append(("tail", tail(1.0)))
    mask = poly_mask(head) | poly_mask(tail(1.0))
    tone = np.zeros(XS.shape)
    n = 10
    for i in range(n):
        f = i / (n - 1)
        s = 1 - 0.78 * f
        m = poly_mask(star(hxc, Y, [(a, L * k) for a, L in allr], 17 * k, s)) | poly_mask(tail(1 - 0.85 * f))
        tone = np.where(m, 0.22 + 0.78 * f ** 0.8, tone)
    tone = blur(tone, 1.1 * SS * k)
    rr = np.hypot(XS - hxc, YS - Y)
    tone = tone + 0.22 * np.exp(-(rr / (11 * k)) ** 2)
    tone = tone + (sstep(-3 * k, 3 * k, Y - YS) - 0.5) * 0.22 * (1 - sstep(0.8, 0.95, tone))
    tone = tone * (1 - 0.5 * sstep(330 * k, 200 * k, XS))
    no_ink = np.zeros(XS.shape, bool)
    tone = np.where(mask, np.clip(tone, 0.06, 1.0), 0.0)
    for (fx, fy, s) in ((168, -22, 7), (240, 36, 6), (296, -44, 5.5), (140, 14, 5)):
        sp = star(fx * k, Y + fy * k, [(q * math.pi / 2, s * k * (1.7 if q % 2 == 0 else 1.1)) for q in range(4)],
                  s * k * 0.3)
        m = poly_mask(sp)
        tone = np.where(m, 0.62, tone)
        mask |= m
        no_ink |= m
        OUTLINES.append(("spark", sp))
    stops = [0.0, 0.22, 0.47, 0.70, 0.93]
    ang = np.arctan2(YF - Y, XF - hxc)
    rf = np.hypot(XF - hxc, YF - Y)
    radial = ang / (2 * math.pi) * 56
    along = (YF - Y) / (4.6 * k / (1.5 if MUL > 1 else 1.0))
    w_tail = sstep(hxc - 30 * k, hxc - 70 * k, XF)
    phase = np.where(w_tail > 0.5, along, radial) + (vnoise(40 * MUL) - 0.5) * 0.5 + np.where(w_tail > 0.5, 0, rf / (80 * k))
    return finish(tone, mask, phase, ramp, stops, halo_rgb=hx(ramp[3][1]), halo_r=9 * k, halo_a=0.44,
                  ink_w=max(1, int(round(1.5 * k))), no_ink=no_ink)


if PIECE == "bolt-hit":
    RGBA = burst(RED)
elif PIECE == "wand-shot":
    RGBA = pulse(PULSE)
else:
    RGBA = bolt(RED)

bpy.ops.wm.read_factory_settings(use_empty=True)
IMG = save(RGBA)
if BLEND:
    scn = bpy.context.scene
    for name, poly in OUTLINES:
        cu = bpy.data.curves.new(PIECE + "_" + name, "CURVE")
        cu.dimensions = "2D"
        sp = cu.splines.new("POLY")
        sp.points.add(len(poly) - 1)
        for p, (x, y) in zip(sp.points, poly):
            p.co = (x * 0.01, -y * 0.01, 0.0, 1.0)
        sp.use_cyclic_u = True
        scn.collection.objects.link(bpy.data.objects.new(PIECE + "_" + name, cu))
    me = bpy.data.meshes.new(PIECE + "_plate")
    me.from_pydata([(0, -H * 0.01, 0), (W * 0.01, -H * 0.01, 0), (W * 0.01, 0, 0), (0, 0, 0)], [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new(name="uv")
    for li, c in zip(range(4), ((0, 0), (1, 0), (1, 1), (0, 1))):
        uv.data[li].uv = c
    mat = bpy.data.materials.new(PIECE + "_print")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    tx = nt.nodes.new("ShaderNodeTexImage")
    tx.image = IMG
    tx.interpolation = "Closest"
    nt.links.new(tx.outputs["Color"], em.inputs["Color"])
    nt.links.new(em.outputs[0], o.inputs["Surface"])
    me.materials.append(mat)
    scn.collection.objects.link(bpy.data.objects.new(PIECE + "_plate", me))
    IMG.pack()
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print(f"art_shots_etch: {PIECE} {W}x{H} opaque={int((RGBA[..., 3] >= 0.5).sum())} wrote {OUT}")
