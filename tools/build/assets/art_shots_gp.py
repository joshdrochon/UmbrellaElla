"""The shots art lane as scripted Blender Grease Pencil drawings (owl-bolt, wand-shot, bolt-hit).

Run (Blender only, never python3):
  Blender -b --factory-startup -P tools/build/assets/art_shots_gp.py -- <piece> <out.png> [seed] [--blend out.blend]
piece: owl-bolt | wand-shot | bolt-hit

Technique (lead, Nov 12, after owl-bolt rounds 3-6 failed on "flat vector fills, no etched line or paper grain"): the
piece is drawn with pressure strokes the way an ink-and-wash illustrator would, not modelled as flat polygons:
  - a bounded glow under the shot (translucent, alpha kept under the art checks' 128 cut-off, so it is light, not body);
  - layered shell plates (shadow edge, crimson, coral) built as backward-swept spikes on one clean head point;
  - a painted pale core with a warm falloff toward the back;
  - etched interior line work: tapered pressure strokes along each spike and along the travel axis;
  - paper grain: specks of tone inside every plate, each within the palette tolerance of its plate colour;
  - a broken ink contour, heavier on the shadow side, and a short tapered geometric tail with clockwork flecks.
Every stroke goes into a Grease Pencil object (the editable drawing, saved in the .blend). Blender's background GP
shader renders every stroke black on this machine (checked Nov 12: material and vertex colours ignored), so the same
stroke data is laid down as vertex-coloured ribbons and fills and rendered with EEVEE in painter's order.
Colours are the GDD SH1.0 'Shared red projectile' / 'Shared yellow' hexes (pipeline/art/style.json accents).
Nothing is traced from a reference; the drawing is generated here from numbers.
"""
import math
import random
import sys

import bpy

ARGV = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
BLEND = None
if "--blend" in ARGV:
    i = ARGV.index("--blend")
    BLEND = ARGV[i + 1]
    del ARGV[i:i + 2]
PIECE = ARGV[0] if ARGV else "owl-bolt"
OUT = ARGV[1] if len(ARGV) > 1 else "/tmp/shot_gp.png"
SEED = int(ARGV[2]) if len(ARGV) > 2 else 11
RNG = random.Random(SEED)

# frame size at 4x the layout cell (OwlBolt 160x80, WandShot 128x64, BoltHit 128x128)
SIZES = {"owl-bolt": (640, 320), "wand-shot": (512, 256), "bolt-hit": (512, 512)}
W, H = SIZES[PIECE]
S = 0.01   # blender units per drawing px
S_PX = W / 640.0 if W >= H else W / 512.0   # drawing px per layout px x 4
WOBBLE = 0.9   # hand-drawn edge amplitude, px at 4x


def hx(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


RED = {"core": hx("FFF5DC"), "hot": hx("FF7848"), "shell": hx("FF3658"), "shadow": hx("8F173C"),
       "ink": hx("171614"), "glow": hx("FF3658")}
GOLD = {"core": hx("FFF5DC"), "hot": hx("FFD84A"), "shell": hx("F5AA28"), "shadow": hx("94611E"),
        "ink": hx("171614"), "glow": hx("FFD84A")}
PAL = GOLD if PIECE == "wand-shot" else RED


def shade(c, dl):
    """c shifted in lightness by dl (roughly L* units), hue kept: grain within the palette tolerance."""
    k = 1.0 + dl / 60.0
    return tuple(max(0, min(255, int(round(v * k)))) for v in c)


# ---------------------------------------------------------------- Grease Pencil drawing (the editable source)
bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
gp = bpy.data.grease_pencils.new(PIECE)
gp_layer = gp.layers.new("ink")
drawing = gp_layer.frames.new(1).drawing
gp_obj = bpy.data.objects.new(PIECE + "_GP", gp)
scn.collection.objects.link(gp_obj)
_MATS = {}
STROKES = []   # (points, radii, rgb, alphas, kind)


def lin(c):
    return tuple((v / 255.0) ** 2.2 for v in c)


def gp_mat(rgb, kind):
    key = (rgb, kind)
    if key not in _MATS:
        m = bpy.data.materials.new(f"{kind}_{'%02x%02x%02x' % rgb}")
        bpy.data.materials.create_gpencil_data(m)
        g = m.grease_pencil
        g.show_stroke = kind == "line"
        g.show_fill = kind == "fill"
        g.color = lin(rgb) + (1.0,)
        g.fill_color = lin(rgb) + (1.0,)
        gp.materials.append(m)
        _MATS[key] = len(gp.materials) - 1
    return _MATS[key]


def P(x, y):
    return (x * S, 0.0, -y * S)


def add(points, radii, rgb, alpha=1.0, kind="line"):
    if kind == "fill" and (alpha if not isinstance(alpha, (list, tuple)) else min(alpha)) >= 1.0 and WOBBLE:
        points = wobble(points, WOBBLE * S_PX)
    elif kind == "lens" and (alpha if not isinstance(alpha, (list, tuple)) else min(alpha)) >= 1.0 and WOBBLE:
        m_ = len(points) // 2
        points = [(x, y + RNG.uniform(-1, 1) * WOBBLE * S_PX * (0 if i in (0, m_ - 1, m_, len(points) - 1) else 1))
                  for i, (x, y) in enumerate(points)]
    n = len(points)
    if n < 2 and kind == "line":
        return
    radii = list(radii) if isinstance(radii, (list, tuple)) else [radii] * n
    alphas = list(alpha) if isinstance(alpha, (list, tuple)) else [alpha] * n
    drawing.add_strokes([n])
    s = drawing.strokes[-1]
    s.material_index = gp_mat(rgb, "fill" if kind == "lens" else kind)
    s.cyclic = kind in ("fill", "lens")
    for i, (x, y) in enumerate(points):
        p = s.points[i]
        p.position = P(x, y)
        p.radius = max(radii[i], 0.05) * S
        p.opacity = alphas[i]
    STROKES.append((list(points), radii, rgb, alphas, kind))


# ---------------------------------------------------------------- geometry
def lerp2(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def inside(poly, x, y):
    c = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-9) + xi:
            c = not c
        j = i
    return c


def bbox(poly):
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    return min(xs), min(ys), max(xs), max(ys)


def grow(poly, d):
    """Offset a polygon outward by about d px (vertex normals; fine for a glow)."""
    n = len(poly)
    cx = sum(p[0] for p in poly) / n
    cy = sum(p[1] for p in poly) / n
    out = []
    for i in range(n):
        a, b, c = poly[i - 1], poly[i], poly[(i + 1) % n]
        e1 = (b[0] - a[0], b[1] - a[1])
        e2 = (c[0] - b[0], c[1] - b[1])
        n1 = (e1[1], -e1[0])
        n2 = (e2[1], -e2[0])
        l1 = math.hypot(*n1) or 1
        l2 = math.hypot(*n2) or 1
        nx, ny = n1[0] / l1 + n2[0] / l2, n1[1] / l1 + n2[1] / l2
        ln = math.hypot(nx, ny) or 1
        nx, ny = nx / ln, ny / ln
        if (b[0] - cx) * nx + (b[1] - cy) * ny < 0:
            nx, ny = -nx, -ny
        out.append((b[0] + nx * d, b[1] + ny * d))
    return out


def tapered(p, q, w, rgb, alpha=1.0, bow=0.0, n=6, head=0.5):
    """A pressure stroke from p to q: thin at both ends, widest at `head` (0..1) along it, slightly bowed."""
    L = math.hypot(q[0] - p[0], q[1] - p[1]) or 1
    nx, ny = -(q[1] - p[1]) / L, (q[0] - p[0]) / L
    pts, rs, al = [], [], []
    for i in range(n):
        t = i / (n - 1)
        b = math.sin(t * math.pi) * bow
        pts.append((p[0] + (q[0] - p[0]) * t + nx * b, p[1] + (q[1] - p[1]) * t + ny * b))
        f = t / head if t < head else (1 - t) / (1 - head)
        rs.append(w * (0.15 + 0.85 * max(0.0, f) ** 0.7))
        al.append(alpha)
    add(pts, rs, rgb, al)


def grain(poly, n, rgb, spread=7.0, size=(0.7, 1.6), alpha=(0.75, 1.0)):
    """Paper grain: specks of the plate's own colour, lighter and darker within the palette tolerance."""
    x0, y0, x1, y1 = bbox(poly)
    placed = tries = 0
    while placed < n and tries < n * 8:
        tries += 1
        x, y = RNG.uniform(x0, x1), RNG.uniform(y0, y1)
        if not inside(poly, x, y):
            continue
        c = shade(rgb, RNG.choice((-1, 1)) * RNG.uniform(spread * 0.6, spread))
        r = RNG.uniform(*size)
        a = RNG.uniform(*alpha)
        ang = RNG.uniform(0, math.pi)
        d = RNG.uniform(0.6, 2.4)
        add([(x, y), (x + math.cos(ang) * d, y + math.sin(ang) * d)], [r, r * 0.6], c, a)
        placed += 1


def tooth(poly, n, rgb, alpha=(0.06, 0.3)):
    """Paper tooth in the light spill: translucent specks (alpha under 0.5), so the glow is mottled like light on
    laid paper, not an airbrush halo."""
    x0, y0, x1, y1 = bbox(poly)
    placed = tries = 0
    while placed < n and tries < n * 8:
        tries += 1
        x, y = RNG.uniform(x0, x1), RNG.uniform(y0, y1)
        if not inside(poly, x, y):
            continue
        r = RNG.uniform(0.6, 1.5)
        ang = RNG.uniform(0, math.pi)
        d = RNG.uniform(0.5, 2.2)
        add([(x, y), (x + math.cos(ang) * d, y + math.sin(ang) * d)], [r, r * 0.6], rgb, RNG.uniform(*alpha))
        placed += 1


def wobble(poly, amp, seg=7.0, closed=True):
    """A hand-drawn edge: long edges split into short runs, each point nudged sideways by up to amp px."""
    out = []
    n = len(poly)
    for i in range(n if closed else n - 1):
        a, b = poly[i], poly[(i + 1) % n]
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        k = max(1, int(L / seg))
        nx, ny = (-(b[1] - a[1]) / (L or 1), (b[0] - a[0]) / (L or 1))
        for j in range(k):
            t = j / k
            j_ = 0.0 if j == 0 else RNG.uniform(-amp, amp)
            out.append((a[0] + (b[0] - a[0]) * t + nx * j_, a[1] + (b[1] - a[1]) * t + ny * j_))
    if not closed:
        out.append(poly[-1])
    return out


def contour(poly, rgb, w, closed=True, light=(0.0, -1.0), skip=0.0, alpha=1.0):
    """Broken ink line with pressure: heavy on the shadow side (away from `light`), lifting off on the lit side."""
    pts = poly + [poly[0]] if closed else poly
    run, rs = [], []
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1
        nx, ny = dy / L, -dx / L   # outward for a clockwise (screen) polygon
        lit = nx * light[0] + ny * light[1]
        k = max(1, int(L / 6))
        for j in range(k):
            t = j / k
            p = lerp2(a, b, t)
            width = w * (0.55 - 0.45 * lit) * RNG.uniform(0.8, 1.15)
            if lit > 0.55 and RNG.random() < skip:
                if len(run) > 1:
                    add(run, rs, rgb, alpha)
                run, rs = [], []
                continue
            run.append(p)
            rs.append(max(0.25, width))
    if len(run) > 1:
        add(run, rs, rgb, alpha)


# ---------------------------------------------------------------- the shot (shared red / yellow geometry, OWL-14)
def blade(xf, side, L, e_tip, a0, b0, Y, back=0.62):
    """One swept-back spike: a long shallow leading edge from near the axis at xf out to the tip at xf+L, a short
    steep trailing edge back in. side -1 = top, +1 = bottom."""
    return [(xf, Y + side * a0), (xf + L, Y + side * e_tip), (xf + L * back, Y + side * b0)]


def lens(xs, env, Y, d=0.0, xa=None, xb=None):
    """A smooth closed outline around the shot: env(x)+d above and below; with d, rounded ends of radius d."""
    xa = xs[0] if xa is None else xa
    xb = xs[-1] if xb is None else xb
    if d:
        front = [xa - d * math.cos(k * math.pi / 16) for k in range(8, 0, -1)][::-1]
        back = [xb + d * math.sin(k * math.pi / 16) for k in range(1, 9)]
        xs = sorted(set(front + list(xs) + back))

    def hh(x):
        if x < xa:
            return d * math.sqrt(max(0.0, 1 - ((xa - x) / d) ** 2))
        if x > xb:
            return d * math.sqrt(max(0.0, 1 - ((x - xb) / d) ** 2))
        return env(x) + d
    top = [(x, Y - hh(x)) for x in xs]
    bot = [(x, Y + hh(x)) for x in reversed(xs)]
    return top + bot


def bolt():
    """The shot, pointing left (owl-bolt); wand-shot is the same drawing mirrored to face right.
    Construction (bar-casters 'Shared projectile'): one clean head point, a pale core triangle, layered shell blades
    swept back (shadow edge under crimson under coral), a narrow tail about one head long, sparse flecks."""
    Y = H / 2.0
    sc = W / 640.0
    tipx = 22 * sc
    head_end = 160 * sc
    body_end = 370 * sc
    tail_end = 490 * sc
    emax = 100 * sc

    def env(x):   # spike-tip envelope from the axis
        if x <= tipx:
            return 0.0
        if x <= head_end:
            return emax * 0.55 * (x - tipx) / (head_end - tipx)
        if x <= body_end:
            u = (x - head_end) / (body_end - head_end)
            return emax * (0.55 + 0.45 * math.sin(min(1.0, u * 1.7) * math.pi / 2)) * (1 - u) ** 1.1 + 12 * sc
        u = min(1.0, (x - body_end) / (tail_end - body_end))
        return 12 * sc * (1 - u) + 1.2 * sc

    def body(x):  # the solid body under the blades: the head wedge then a slim taper into the tail
        if x <= head_end:
            return emax * 0.5 * (x - tipx) / (head_end - tipx)
        u = min(1.0, (x - head_end) / (tail_end - head_end))
        return emax * 0.5 * (1 - u) ** 1.5 + 1.2 * sc

    xs = [tipx + (tail_end - tipx) * k / 80 for k in range(81)]

    def blades(seed, scale, shift, x_from, x_to, n, e_mul=1.0):
        rng = random.Random(seed)
        out = []
        for side in (-1, 1):
            for i in range(n):
                xf = x_from + (x_to - x_from) * (i + rng.uniform(0.0, 0.7)) / n + shift
                L = rng.uniform(85, 150) * sc * scale
                tip_x = xf + L
                e_tip = env(min(tip_x, body_end + 40 * sc)) * e_mul * rng.uniform(0.85, 1.12)
                a0 = body(xf) * 0.45
                b0 = body(xf + L * 0.62) * 0.5
                if e_tip <= b0 + 4 * sc:
                    continue
                out.append(blade(xf, side, L, e_tip, a0, b0, Y, back=rng.uniform(0.55, 0.7)))
        return out

    shadow_bl = blades(SEED * 13 + 1, 0.85, 8 * sc, 65 * sc, 300 * sc, 7, 1.0)
    shell_bl = blades(SEED * 13 + 2, 0.8, 0.0, 55 * sc, 290 * sc, 8, 0.86)
    hot_bl = blades(SEED * 13 + 3, 0.7, -6 * sc, 50 * sc, 230 * sc, 6, 0.55)
    body_poly = lens(xs, body, Y)

    # ---- 1. bounded glow (light spill): a smooth lens, alpha stays under 0.5, so it is light, not body
    gx_s = [tipx - 40 * sc + (tail_end + 80 * sc - tipx) * j / 120 for j in range(121)]
    raw = [max(env(x), body(x)) if tipx <= x <= tail_end else 0.0 for x in gx_s]
    win = 9
    smooth = [sum(raw[max(0, i - win):i + win + 1]) / len(raw[max(0, i - win):i + win + 1]) for i in range(len(raw))]

    def glow_env(x):
        i = min(len(gx_s) - 2, max(0, int((x - gx_s[0]) / (gx_s[1] - gx_s[0]))))
        t = (x - gx_s[i]) / (gx_s[1] - gx_s[0])
        return smooth[i] * (1 - t) + smooth[i + 1] * t
    for k in range(16):
        f = 0.85 + 0.015 * k
        add(lens(gx_s, lambda x, f=f, k=k: glow_env(x) * f + (1 + 0.75 * k) * sc * min(1.0, glow_env(x) / (8 * sc)),
                 Y), 1.0, PAL["glow"], 0.03, "lens")
    tooth(lens(gx_s, lambda x: glow_env(x) * 1.05 + 10 * sc * min(1.0, glow_env(x) / (8 * sc)), Y),
          int(5200 * sc * sc), PAL["glow"])
    for k in range(6):   # brief hot bloom at the head
        d = (2 + k * 4) * sc
        hp = lens([tipx + (head_end + 60 * sc - tipx) * j / 20 for j in range(21)],
                  lambda x: body(x) * 0.8, Y, d, tipx, head_end + 60 * sc)
        add(hp, 1.0, PAL["hot"], 0.03, "lens")

    # ---- 2. trail: thin dashed speed lines carrying tiny square flecks, a small clockwork arc
    for side, yo, x0, x1 in ((-1, 24, 330, 560), (1, 22, 345, 575), (-1, 8, 430, 585), (1, 40, 300, 450)):
        y_a = Y + side * yo * sc
        x = x0 * sc
        while x < x1 * sc:
            L = RNG.uniform(14, 34) * sc
            yy = y_a + side * (x - x0 * sc) * 0.06
            tapered((x, yy), (min(x + L, x1 * sc), yy + side * L * 0.06), 1.6 * sc, PAL["shell"], 0.95)
            x += L + RNG.uniform(7, 16) * sc
    for (fx, fy, s, c) in ((410, -31, 8, "shadow"), (480, -38, 6, "shell"), (460, 33, 7, "shadow"),
                           (545, 38, 5, "shell"), (575, -14, 5, "shadow")):
        x, y, s = fx * sc, Y + fy * sc, s * sc
        a = RNG.uniform(-0.25, 0.25)
        sq = [(x + math.cos(a + k * math.pi / 2 + math.pi / 4) * s * 0.7,
               y + math.sin(a + k * math.pi / 2 + math.pi / 4) * s * 0.7) for k in range(4)]
        add(sq, 1.0, PAL[c], 1.0, "fill")
    gx, gy, gr = 545 * sc, Y - 58 * sc, 13 * sc
    arc = [(gx + math.cos(a) * gr, gy + math.sin(a) * gr) for a in [math.pi + i * math.pi / 14 for i in range(15)]]
    add(arc, [2.4 * sc] * len(arc), PAL["shell"], 1.0)
    for i in range(1, 14, 3):
        a = math.pi + i * math.pi / 14
        add([(gx + math.cos(a) * gr, gy + math.sin(a) * gr),
             (gx + math.cos(a) * (gr + 6 * sc), gy + math.sin(a) * (gr + 6 * sc))], [2.6 * sc, 2.2 * sc],
            PAL["shell"], 1.0)

    # ---- 3. shell: shadow-edge blades, body, crimson blades, etched line work, coral blades
    for b in shadow_bl:
        add(b, 1.0, PAL["shadow"], 1.0, "fill")
    add(body_poly, 1.0, PAL["shadow"], 1.0, "lens")
    for b in shell_bl:
        add(b, 1.0, PAL["shell"], 1.0, "fill")
    add(lens(xs, lambda x: body(x) * 0.82, Y), 1.0, PAL["shell"], 1.0, "lens")
    shell_union = lens(xs, lambda x: max(env(x) * 0.8, body(x)), Y)
    grain(shell_union, int(2600 * sc * sc), PAL["shell"], spread=8)
    # etched: tapered strokes along each blade's leading edge (the engraver's line following the form)
    for b in shell_bl:
        (ax, ay), (tx, ty), (bx, by) = b
        for k in range(RNG.randint(2, 4)):
            f = RNG.uniform(0.15, 0.55)
            p0 = (ax + (bx - ax) * f, ay + (by - ay) * f)
            p1 = (tx + (bx - tx) * f * 0.5, ty + (by - ty) * f * 0.5)
            tapered(p0, p1, RNG.uniform(0.8, 1.4) * sc, PAL["shadow"], 1.0, bow=RNG.uniform(-1.5, 1.5) * sc,
                    head=0.7)
    for k in range(10):   # long speed lines converging on the head point
        off = RNG.uniform(-0.8, 0.8)
        x0 = RNG.uniform(140, 230) * sc
        x1 = RNG.uniform(320, 430) * sc
        tapered((x0, Y + off * body(x0) * 0.7), (x1, Y + off * body(x1) * 0.6 + RNG.uniform(-2, 2) * sc),
                RNG.uniform(0.7, 1.3) * sc, PAL["shadow"], 1.0, head=0.3)
    # engraved cross-contour hatching: dense on the lower (shadow) side, sparse on top, thinning toward the head
    x = 95 * sc
    while x < body_end - 10 * sc:
        k = (x - 95 * sc) / (body_end - 105 * sc)
        for side, dens in ((1, 0.9), (-1, 0.35)):
            if RNG.random() > dens * (0.4 + 0.6 * k):
                continue
            b0 = body(x)
            p0 = (x, Y + side * b0 * RNG.uniform(0.25, 0.4))
            p1 = (x + RNG.uniform(5, 9) * sc, Y + side * (b0 * RNG.uniform(0.8, 1.0)))
            tapered(p0, p1, RNG.uniform(0.55, 0.85) * sc, PAL["shadow"], 1.0, head=0.5, bow=0.6 * sc)
        x += RNG.uniform(4.0, 6.0) * sc
    for b in hot_bl:
        add(b, 1.0, PAL["hot"], 1.0, "fill")
    hot_union = lens([tipx + (320 * sc - tipx) * j / 40 for j in range(41)],
                     lambda x: body(x) * 0.62 * min(1.0, max(0.0, (320 * sc - x) / (100 * sc))) ** 0.8, Y)
    add(hot_union, 1.0, PAL["hot"], 1.0, "lens")
    grain(hot_union, int(900 * sc * sc), PAL["hot"], spread=7)
    for b in hot_bl:
        (ax, ay), (tx, ty), (bx, by) = b
        tapered(((ax + bx) / 2, (ay + by) / 2), (tx, ty), 1.0 * sc, PAL["shell"], 1.0, head=0.75)

    # ---- 4. pale core: one long clean triangle from the head point, warm falloff toward the back
    def core_env(x):
        if x <= 130 * sc:
            return 19 * sc * (x - tipx - 16 * sc) / (130 * sc - tipx - 16 * sc)
        u = min(1.0, (x - 130 * sc) / (290 * sc - 130 * sc))
        return 19 * sc * (1 - u) ** 1.3
    core = lens([tipx + 16 * sc + (290 * sc - tipx - 16 * sc) * j / 40 for j in range(41)],
                lambda x: max(0.0, core_env(x)), Y)
    add(core, 1.0, PAL["core"], 1.0, "lens")
    for k in range(30):
        x0 = RNG.uniform(150, 270) * sc
        yy = Y + RNG.uniform(-0.8, 0.8) * core_env(x0)
        tapered((x0, yy), (x0 + RNG.uniform(30, 70) * sc, Y + (yy - Y) * 0.3), RNG.uniform(1.0, 2.2) * sc,
                PAL["hot"], RNG.uniform(0.3, 0.55), head=0.3)
    grain(core, int(450 * sc * sc), PAL["core"], spread=8, alpha=(0.6, 0.9))
    tapered((tipx + 6 * sc, Y), (170 * sc, Y), 2.6 * sc, PAL["core"], 1.0, head=0.25)
    for d, a, c in ((10, 0.3, "hot"), (5, 0.45, "hot"), (2.4, 1.0, "core")):
        ring = [(body_end - 10 * sc + math.cos(t * math.pi / 6) * d * sc, Y + math.sin(t * math.pi / 6) * d * sc)
                for t in range(12)]
        add(ring, 1.0, PAL[c], a, "fill")

    # ---- 5. ink: a fine broken pressure line on the outer leading edge of the lower (shadow-side) blades only
    for b in shadow_bl:
        if b[1][1] > Y and RNG.random() < 0.7:
            (ax, ay), (tx, ty) = b[0], b[1]
            p0 = (ax + (tx - ax) * RNG.uniform(0.3, 0.5), ay + (ty - ay) * RNG.uniform(0.3, 0.5))
            tapered(p0, (tx, ty), 1.3 * sc, PAL["ink"], 1.0, head=0.8)
    tapered((tipx + 4 * sc, Y + 1 * sc), (head_end, Y + body(head_end) + 1 * sc), 1.6 * sc, PAL["shadow"], 1.0,
            head=0.7)
    return body_poly


def star(cx, cy, rays, inner):
    """A star outline: rays = [(angle, length)], inner = notch radius between rays."""
    out = []
    n = len(rays)
    for i, (a, L) in enumerate(rays):
        out.append((cx + math.cos(a) * L, cy + math.sin(a) * L))
        a2 = (a + rays[(i + 1) % n][0] + (2 * math.pi if i == n - 1 else 0)) / 2
        out.append((cx + math.cos(a2) * inner, cy + math.sin(a2) * inner))
    return out


def pulse():
    """wand-shot: Ella's compact gold pulse (GDD SH1.0 COM-06 Small Blasts VFX, Twin Stars VFX): a four-point star
    head with short secondary points, a pale core, a short finite tapered tail of slivers, faces right. Gold #E9C46A
    family, so it never reads as the Keeper's angular yellow shot (OWL-14 geometry)."""
    Y = H / 2.0
    sc = W / 512.0
    hx_, tail0 = 400 * sc, 150 * sc
    G = {"core": hx("FFF5DC"), "gold": hx("E9C46A"), "amber": hx("F5AA28"), "shadow": hx("94611E"),
         "ink": hx("171614"), "spark": hx("FFF3D6")}

    def tail_env(x):
        if x >= hx_:
            return 0.0
        u = (x - tail0) / (hx_ - tail0)
        return max(0.0, 15 * sc * u ** 1.4)
    xs = [tail0 + (hx_ + 10 * sc - tail0) * j / 60 for j in range(61)]

    # glow: soft gold lens around tail and head, and a round bloom on the head (alpha under 0.5)
    for k in range(14):
        f = 1.0 + 0.12 * k
        add(lens(xs, lambda x, f=f, k=k: tail_env(x) * f + (1 + 1.2 * k) * sc * min(1.0, tail_env(x) / (4 * sc)), Y),
            1.0, G["gold"], 0.026, "lens")
    for k in range(12):
        r = (14 + k * 5.5) * sc
        add([(hx_ + math.cos(t * math.pi / 16) * r * 1.15, Y + math.sin(t * math.pi / 16) * r) for t in range(32)],
            1.0, G["gold"], 0.03, "fill")
    # tail: overlapping tapered slivers (shadow under gold under core), short and finite
    tail = lens(xs, tail_env, Y)
    add(tail, 1.0, G["shadow"], 1.0, "lens")
    add(lens(xs, lambda x: tail_env(x) * 0.78, Y), 1.0, G["gold"], 1.0, "lens")
    grain(tail, int(500 * sc * sc), G["gold"], spread=8)
    for k in range(12):
        off = RNG.uniform(-0.7, 0.7)
        x0 = RNG.uniform(tail0 + 20 * sc, 300 * sc)
        x1 = hx_ - RNG.uniform(10, 40) * sc
        tapered((x0, Y + off * tail_env(x0)), (x1, Y + off * tail_env(x1) * 0.8), RNG.uniform(0.7, 1.3) * sc,
                G["shadow"] if k % 3 else G["amber"], 1.0, head=0.75)
    add(lens(xs, lambda x: tail_env(x) * 0.3 if x > 250 * sc else 0.0, Y), 1.0, G["core"], 1.0, "lens")
    # sparse sparks behind (tiny four-point stars), on thin broken trail lines
    for side, yo in ((-1, 26), (1, 22)):
        x = 170 * sc
        while x < 360 * sc:
            L = RNG.uniform(12, 26) * sc
            tapered((x, Y + side * yo * sc), (x + L, Y + side * (yo - 3) * sc), 1.2 * sc, G["gold"], 0.95)
            x += L + RNG.uniform(10, 20) * sc
    for (fx, fy, s) in ((120, -14, 7), (205, 30, 6), (280, -34, 5), (90, 8, 5)):
        add(star(fx * sc, Y + fy * sc, [(k * math.pi / 2, s * sc * (1.6 if k % 2 == 0 else 1.0)) for k in range(4)],
                 s * sc * 0.28), 1.0, G["gold"], 1.0, "fill")
    # the star head: shadow star, gold star, secondary diagonal points, pale core star, etched rays
    main = [(0.0, 96), (math.pi / 2, 52), (math.pi, 70), (3 * math.pi / 2, 52)]
    diag = [(math.pi / 4, 30), (3 * math.pi / 4, 26), (5 * math.pi / 4, 26), (7 * math.pi / 4, 30)]
    allr = sorted(main + diag)
    add(star(hx_, Y, [(a, (L + 6) * sc) for a, L in allr], 15 * sc), 1.0, G["shadow"], 1.0, "fill")
    add(star(hx_, Y, [(a, L * sc) for a, L in allr], 12 * sc), 1.0, G["gold"], 1.0, "fill")
    head_poly = star(hx_, Y, [(a, L * sc) for a, L in allr], 12 * sc)
    grain(head_poly, int(500 * sc * sc), G["gold"], spread=8)
    for a, L in allr:   # each point lit on its upper face, shadowed on the lower (an engraved bevel)
        tip = (hx_ + math.cos(a) * L * sc, Y + math.sin(a) * L * sc)
        for o, c in ((-0.16, G["amber"]), (0.12, G["shadow"])):
            base = (hx_ + math.cos(a + o * 3) * 9 * sc, Y + math.sin(a + o * 3) * 9 * sc)
            tapered(base, tip, (1.1 if c == G["shadow"] else 1.6) * sc * (L / 60), c, 1.0, head=0.3)
    add(star(hx_, Y, [(a, L * 0.55 * sc) for a, L in main], 6 * sc), 1.0, G["core"], 1.0, "fill")
    grain(star(hx_, Y, [(a, L * 0.55 * sc) for a, L in main], 6 * sc), int(150 * sc * sc), G["core"], spread=7,
          alpha=(0.6, 0.9))
    for d, a, c in ((7, 1.0, "spark"),):
        add([(hx_ + math.cos(t * math.pi / 8) * d * sc, Y + math.sin(t * math.pi / 8) * d * sc) for t in range(16)],
            1.0, G[c], a, "fill")
    # ink: fine broken line under the lower points and the tail's underside
    for a, L in allr:
        if math.sin(a) > 0.2:
            tip = (hx_ + math.cos(a) * (L + 6) * sc, Y + math.sin(a) * (L + 6) * sc)
            base = (hx_ + math.cos(a + 0.35) * 16 * sc, Y + math.sin(a + 0.35) * 16 * sc)
            tapered(base, tip, 1.2 * sc, G["ink"], 1.0, head=0.7)
    tapered((300 * sc, Y + tail_env(300 * sc) + 0.5 * sc), (hx_ - 30 * sc, Y + tail_env(hx_ - 30 * sc) + 0.5 * sc),
            1.0 * sc, G["ink"], 0.9, head=0.8)


def burst():
    """bolt-hit: the release burst form in the crimson family (the GDD draws no impact)."""
    cx, cy = W / 2.0, H / 2.0
    sc = W / 512.0
    n = 14
    rays = []
    for i in range(n):
        a = i * 2 * math.pi / n + RNG.uniform(-0.12, 0.12)
        L = (RNG.uniform(150, 210) if i % 2 == 0 else RNG.uniform(85, 125)) * sc
        rays.append((a, L))
    outer = []
    for a, L in rays:
        w = 0.17
        outer.append((cx + math.cos(a - w) * L * 0.32, cy + math.sin(a - w) * L * 0.32))
        outer.append((cx + math.cos(a) * L, cy + math.sin(a) * L))
        outer.append((cx + math.cos(a + w) * L * 0.32, cy + math.sin(a + w) * L * 0.32))
    for k, d in enumerate((40, 30, 22, 15, 9, 4)):
        add(grow(outer, d * sc), 1.0, PAL["glow"], 0.06, "fill")
    add(outer, 1.0, PAL["shadow"], 1.0, "fill")
    grain(outer, int(1400 * sc * sc), PAL["shadow"], spread=9)
    shell = [(cx + (x - cx) * 0.84, cy + (y - cy) * 0.84) for x, y in outer]
    add(shell, 1.0, PAL["shell"], 1.0, "fill")
    grain(shell, int(2200 * sc * sc), PAL["shell"], spread=8)
    for a, L in rays:
        for k in range(3):
            o = RNG.uniform(-0.09, 0.09)
            tapered((cx + math.cos(a + o) * L * 0.22, cy + math.sin(a + o) * L * 0.22),
                    (cx + math.cos(a + o * 0.3) * L * 0.8, cy + math.sin(a + o * 0.3) * L * 0.8),
                    RNG.uniform(0.9, 1.6) * sc, PAL["shadow"], 1.0, head=0.6)
    hot = [(cx + (x - cx) * 0.55, cy + (y - cy) * 0.55) for x, y in outer]
    add(hot, 1.0, PAL["hot"], 1.0, "fill")
    grain(hot, int(900 * sc * sc), PAL["hot"], spread=7)
    core = []
    for i, (a, L) in enumerate(rays):
        r = (60 if i % 2 == 0 else 34) * sc
        core.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
        core.append((cx + math.cos(a + math.pi / n) * 18 * sc, cy + math.sin(a + math.pi / n) * 18 * sc))
    add(core, 1.0, PAL["core"], 1.0, "fill")
    grain(core, int(400 * sc * sc), PAL["core"], spread=8, alpha=(0.6, 0.9))
    for a, L in rays:
        tapered((cx + math.cos(a) * 20 * sc, cy + math.sin(a) * 20 * sc),
                (cx + math.cos(a) * L * 0.5, cy + math.sin(a) * L * 0.5), 1.0 * sc, PAL["hot"], 0.5, head=0.3)
    contour(outer, PAL["ink"], 2.4 * sc, light=(-0.6, -0.8), skip=0.7)
    for i in range(10):
        a = RNG.uniform(0, 2 * math.pi)
        r = RNG.uniform(150, 220) * sc
        x, y, s = cx + math.cos(a) * r, cy + math.sin(a) * r, RNG.uniform(5, 9) * sc
        if not (12 < x < W - 12 and 12 < y < H - 12):
            continue
        sq = [(x + math.cos(a + k * math.pi / 2) * s * 0.7, y + math.sin(a + k * math.pi / 2) * s * 0.7)
              for k in range(4)]
        add(sq, 1.0, PAL["shadow" if i % 2 else "shell"], 1.0, "fill")
    return outer


if PIECE == "bolt-hit":
    burst()
elif PIECE == "wand-shot":
    pulse()
else:
    bolt()


# ---------------------------------------------------------------- palette discipline (after the render)
def palette_discipline(path):
    """Anti-aliasing mixes two neighbouring plate colours (crimson and shadow, shadow and ink) into saturated in-between
    tones the art bible does not allow (style.json: off_style, off_band). Like a limited-palette print, every opaque
    pixel that is such a tone is set to its nearest approved colour (the palette and the shot accents); everything
    else (the plate colours, their grain, the soft core falloff, the translucent glow) is left as rendered."""
    import json
    import os
    import numpy as np
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    with open(os.path.join(root, "pipeline", "art", "style.json"), encoding="utf-8") as fh:
        st = json.load(fh)

    def to_lab(rgb):   # rgb (..., 3) in 0..255, the same formula as tools/art_check.py
        c = rgb / 255.0
        c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
        x = (0.4124 * c[..., 0] + 0.3576 * c[..., 1] + 0.1805 * c[..., 2]) / 0.95047
        y = 0.2126 * c[..., 0] + 0.7152 * c[..., 1] + 0.0722 * c[..., 2]
        z = (0.0193 * c[..., 0] + 0.1192 * c[..., 1] + 0.9505 * c[..., 2]) / 1.08883

        def f(t):
            return np.where(t > 0.008856, np.cbrt(t), 7.787 * t + 16 / 116)
        fx, fy, fz = f(x), f(y), f(z)
        return np.stack([116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)], axis=-1)

    pal = np.array([hx(c["hex"]) for c in st["palette"]], dtype=float)
    roles = (st.get("accents") or {}).get("roles") or {}
    acc = [(np.array([hx(c["hex"]) for c in r["colours"]], dtype=float), r) for r in roles.values()]
    targets = np.concatenate([pal] + [a for a, _ in acc])
    img = bpy.data.images.load(path)
    w, h = img.size
    px = np.array(img.pixels[:], dtype=float).reshape(h, w, 4)
    rgb = np.clip(np.round(px[..., :3] * 255.0), 0, 255)
    lab = to_lab(rgb)
    pal_lab = to_lab(pal)
    d_pal = np.min(np.linalg.norm(lab[..., None, :] - pal_lab[None, None], axis=-1), axis=-1)
    chroma = np.hypot(lab[..., 1], lab[..., 2])
    hue = np.degrees(np.arctan2(lab[..., 2], lab[..., 1])) % 360
    is_acc = np.zeros((h, w), bool)
    for cols, r in acc:
        d = np.min(np.linalg.norm(lab[..., None, :] - to_lab(cols)[None, None], axis=-1), axis=-1)
        band = np.zeros((h, w), bool)
        for lo, hi in r["hue_bands_deg"]:
            band |= (hue >= lo) & (hue <= hi)
        is_acc |= (d <= r["delta_e_max"]) & band & (chroma >= r["chroma"][0]) & (chroma <= r["chroma"][1])
    mx, mn = rgb.max(-1), rgb.min(-1)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0)
    hg = st["hue_gate"]
    in_band = np.zeros((h, w), bool)
    for lo, hi in hg["allowed_hue_bands_deg"]:
        in_band |= (hue >= lo) & (hue <= hi)
    off_style = (sat >= st["off_style_saturation_min"]) & (lab[..., 0] > st["dark_l_max"])
    off_band = (chroma > hg["chroma_min"]) & ~in_band
    bad = (px[..., 3] >= 0.5) & (d_pal > st["delta_e_tolerance"]) & ~is_acc & (off_style | off_band)
    if bad.any():
        t_lab = to_lab(targets)
        near = np.argmin(np.linalg.norm(lab[bad][:, None, :] - t_lab[None], axis=-1), axis=-1)
        rgb[bad] = targets[near]
        px[..., :3] = rgb / 255.0
        img.pixels[:] = px.ravel().tolist()
        img.filepath_raw = path
        img.file_format = "PNG"
        img.save()
    return int(bad.sum())



# ---------------------------------------------------------------- render the stroke data (painter's order)
import bmesh  # noqa: E402
from mathutils import Vector, geometry  # noqa: E402

gp_obj.hide_render = True
me = bpy.data.meshes.new(PIECE + "_Ink")
bm = bmesh.new()
faces_col = []


def face(coords, cols):
    vs = [bm.verts.new(c) for c in coords]
    try:
        f = bm.faces.new(vs)
    except ValueError:
        return
    faces_col.append((f, cols))


for idx, (pts, rs, rgb, al, kind) in enumerate(STROKES):
    yv = -idx * 2e-5
    c = lin(rgb)
    if kind == "lens":   # x-monotone outline (top run, then bottom run reversed): triangulated as strips
        m_ = len(pts) // 2
        top_, bot_ = pts[:m_], list(reversed(pts[m_:]))
        for i in range(m_ - 1):
            q = [top_[i], top_[i + 1], bot_[i + 1], bot_[i]]
            face([(x * S, yv, -y * S) for x, y in q], [c + (al[0],)] * 4)
        continue
    if kind == "fill":
        poly = [Vector((x * S, yv, -y * S)) for x, y in pts]
        for tri in geometry.tessellate_polygon([poly]):
            face([poly[i] for i in tri], [c + (al[0],)] * 3)
        continue
    n = len(pts)
    left, right = [], []
    for i in range(n):
        a_ = pts[max(i - 1, 0)]
        b_ = pts[min(i + 1, n - 1)]
        dx, dy = b_[0] - a_[0], b_[1] - a_[1]
        L = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / L, dx / L
        left.append((pts[i][0] + nx * rs[i], pts[i][1] + ny * rs[i]))
        right.append((pts[i][0] - nx * rs[i], pts[i][1] - ny * rs[i]))
    for i in range(n - 1):
        q = [left[i], left[i + 1], right[i + 1], right[i]]
        face([(x * S, yv, -y * S) for x, y in q], [c + (al[i],), c + (al[i + 1],), c + (al[i + 1],), c + (al[i],)])
bm.to_mesh(me)
bm.free()
attr = me.color_attributes.new("c", "FLOAT_COLOR", "CORNER")
for poly, (f, cols) in zip(me.polygons, faces_col):
    for k, li in enumerate(poly.loop_indices):
        attr.data[li].color = cols[k]
mesh_obj = bpy.data.objects.new(PIECE + "_InkMesh", me)
scn.collection.objects.link(mesh_obj)

m = bpy.data.materials.new("ink")
m.use_nodes = True
nt = m.node_tree
nt.nodes.clear()
o = nt.nodes.new("ShaderNodeOutputMaterial")
at = nt.nodes.new("ShaderNodeVertexColor")
at.layer_name = "c"
em = nt.nodes.new("ShaderNodeEmission")
tr = nt.nodes.new("ShaderNodeBsdfTransparent")
mx = nt.nodes.new("ShaderNodeMixShader")
nt.links.new(at.outputs["Color"], em.inputs["Color"])
nt.links.new(at.outputs["Alpha"], mx.inputs["Fac"])
nt.links.new(tr.outputs[0], mx.inputs[1])
nt.links.new(em.outputs[0], mx.inputs[2])
nt.links.new(mx.outputs[0], o.inputs["Surface"])
for attr_name, val in (("surface_render_method", "BLENDED"), ("use_transparency_overlap", True),
                       ("use_backface_culling", False)):
    try:
        setattr(m, attr_name, val)
    except (AttributeError, TypeError):
        pass
me.materials.append(m)

cam = bpy.data.cameras.new("cam")
cam.type = "ORTHO"
cam.ortho_scale = max(W, H) * S
co = bpy.data.objects.new("cam", cam)
scn.collection.objects.link(co)
co.location = (W * S / 2, -10, -H * S / 2)
co.rotation_euler = (math.radians(90), 0, 0)
scn.camera = co
scn.render.engine = "BLENDER_EEVEE"
scn.eevee.taa_render_samples = 32
scn.render.filter_size = 0.7
scn.render.resolution_x, scn.render.resolution_y = W, H
scn.render.film_transparent = True
scn.render.image_settings.file_format = "PNG"
scn.render.image_settings.color_mode = "RGBA"
scn.view_settings.view_transform = "Standard"
scn.view_settings.look = "None"
scn.render.filepath = OUT
bpy.ops.render.render(write_still=True)
snapped = palette_discipline(OUT)
if BLEND:
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print(f"art_shots_gp: {PIECE} strokes={len(STROKES)} faces={len(me.polygons)} snapped={snapped} wrote {OUT}")
