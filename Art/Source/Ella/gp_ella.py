"""Ella as a Blender Grease Pencil 2D drawing (scripted strokes, painted gradients, paper grain, etched hatching).

Run:  Blender -b --python Art/Source/Ella/gp_ella.py -- <pose> <out.png> [seed]
pose: open | attack | shield | closed
Coordinates are authored in a 400x520 drawing space (x right, y down) read off the Rehearsal Ella silhouette
(proportions only; no reference pixel is copied, Official Rules 7(h)). Everything is drawn here with strokes.
"""
import math
import random
import sys

import bpy

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
POSE = ARGS[0] if ARGS else "open"
OUT = ARGS[1] if len(ARGS) > 1 else "/tmp/ella_gp.png"
SEED = int(ARGS[2]) if len(ARGS) > 2 else 7
RNG = random.Random(SEED)
W, H = 600, 700            # render size; drawing space is placed at 1:1 with a margin
OX, OY = 130, 60            # drawing-space offset inside the render
SCALE = 0.01               # blender units per drawing px


# ---------- palette: warm grey-brown ink on paper, tan accents (art bible: ink, bone, dusty gold)
def lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


INK = (22, 19, 18)
DEEP = (44, 38, 35)
MID = (88, 78, 68)
LIGHT = (140, 124, 104)
BONE = (196, 180, 152)
SKIN = (150, 128, 108)


def ramp(t, lo=DEEP, mid=MID, hi=LIGHT):
    t = max(0.0, min(1.0, t))
    return lerp(lo, mid, t * 2) if t < 0.5 else lerp(mid, hi, (t - 0.5) * 2)


# ---------- scene
bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
gp = bpy.data.grease_pencils.new("Ella")
layer = gp.layers.new("ink")
drawing = layer.frames.new(1).drawing
obj = bpy.data.objects.new("Ella", gp)
scn.collection.objects.link(obj)

STROKES = []
_MATS = {}
_TONES = []


def mat(color, kind):
    """One GP material per quantised tone and kind. Blender's background GP shader renders every stroke black on
    this machine, so the render converts the finished Grease Pencil object to mesh and re-materials it from _TONES."""
    key = (tuple(int(c) // 3 * 3 for c in color), kind)
    if key in _MATS:
        return _MATS[key]
    m = bpy.data.materials.new("gp")
    bpy.data.materials.create_gpencil_data(m)
    g = m.grease_pencil
    g.show_stroke = kind == "line"
    g.show_fill = kind == "fill"
    obj.data.materials.append(m)
    _TONES.append(key[0])
    _MATS[key] = len(obj.data.materials) - 1
    return _MATS[key]


def lin(color, a=1.0):
    return tuple((v / 255.0) ** 2.2 for v in color) + (a,)


def P(x, y):
    return ((x + OX) * SCALE, 0.0, -(y + OY) * SCALE)


LEAN = [0.0, (160.0, 140.0)]     # degrees (feet swing left), pivot at the grip


def lean_pt(q):
    a = math.radians(LEAN[0])
    if not a:
        return q
    px, py = LEAN[1]
    x, y = q[0] - px, q[1] - py
    return (px + x * math.cos(a) + y * math.sin(a), py - x * math.sin(a) + y * math.cos(a))


def add(points, radii, color, kind="line", cyclic=False, opacity=1.0):
    points = [lean_pt(q) for q in points]
    n = len(points)
    drawing.add_strokes([n])
    s = drawing.strokes[-1]
    s.material_index = mat(color, kind)
    s.cyclic = cyclic
    for i, (x, y) in enumerate(points):
        p = s.points[i]
        p.position = P(x, y)
        r = radii[i] if isinstance(radii, (list, tuple)) else radii
        p.radius = r * SCALE
        p.opacity = opacity
    r_list = [(radii[i] if isinstance(radii, (list, tuple)) else radii) for i in range(n)]
    STROKES.append((list(points), r_list, color, kind, cyclic, opacity))
    return s


# ---------- geometry helpers
def catmull(pts, per=6, closed=False):
    out = []
    n = len(pts)
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        p0 = pts[(i - 1) % n] if (closed or i > 0) else pts[0]
        p1 = pts[i]
        p2 = pts[(i + 1) % n]
        p3 = pts[(i + 2) % n] if (closed or i + 2 < n) else pts[-1]
        for k in range(per):
            t = k / per
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    if not closed:
        out.append(pts[-1])
    return out


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


def scan(poly, angle, spacing, jitter=0.0):
    """Hatch segments clipped to poly: list of ((x0,y0),(x1,y1)). angle in degrees."""
    x0, y0, x1, y1 = bbox(poly)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    R = math.hypot(x1 - x0, y1 - y0) / 2 + 2
    a = math.radians(angle)
    dx, dy = math.cos(a), math.sin(a)
    nx, ny = -dy, dx
    segs = []
    off = -R
    while off < R:
        o = off + RNG.uniform(-jitter, jitter)
        run = None
        t = -R
        while t <= R:
            x, y = cx + nx * o + dx * t, cy + ny * o + dy * t
            ins = inside(poly, x, y)
            if ins and run is None:
                run = t
            if (not ins or t + 1.5 > R) and run is not None:
                if t - run > 2.5:
                    segs.append(((cx + nx * o + dx * run, cy + ny * o + dy * run),
                                 (cx + nx * o + dx * t, cy + ny * o + dy * t)))
                run = None
            t += 1.5
        off += spacing
    return segs


def tapered(p, q, w, color, opacity=1.0, bow=0.0):
    """One etched/pressure stroke from p to q: swells in the middle, thin at the ends, slightly bowed."""
    n = 5
    pts, rs = [], []
    L = math.hypot(q[0] - p[0], q[1] - p[1]) or 1
    nx, ny = -(q[1] - p[1]) / L, (q[0] - p[0]) / L
    for i in range(n):
        t = i / (n - 1)
        b = math.sin(t * math.pi) * bow
        pts.append((p[0] + (q[0] - p[0]) * t + nx * b, p[1] + (q[1] - p[1]) * t + ny * b))
        rs.append(w * (0.25 + 0.75 * math.sin(t * math.pi) ** 0.6) * RNG.uniform(0.85, 1.15))
    add(pts, rs, color, "line", opacity=opacity)


# ---------- painters
def wash(poly, tone, light=(-1, -0.4), lo=DEEP, mid=MID, hi=LIGHT, bands=14):
    """Painted gradient: flat base fill, then broad overlapping translucent bands lighter toward the light side."""
    add(poly, 1.0, ramp(tone * 0.7, lo, mid, hi), "fill", cyclic=True)
    x0, y0, x1, y1 = bbox(poly)
    lx, ly = light
    ang = math.degrees(math.atan2(lx, -ly))   # bands run across the light direction
    for seg in scan(poly, ang + 90, max(2.2, (x1 - x0 + y1 - y0) / bands / 2), jitter=0.8):
        mx, my = (seg[0][0] + seg[1][0]) / 2, (seg[0][1] + seg[1][1]) / 2
        u = ((mx - x0) * -lx + (my - y0) * -ly) / (((x1 - x0) * abs(lx) + (y1 - y0) * abs(ly)) or 1)
        t = max(0.0, min(1.0, tone + (u - 0.5) * 0.9 + RNG.uniform(-0.05, 0.05)))
        tapered(seg[0], seg[1], 3.1, ramp(t, lo, mid, hi), opacity=0.55, bow=RNG.uniform(-0.8, 0.8))


def etch(poly, angle=62, spacing=3.4, color=INK, w=0.55, shade=None, opacity=0.8):
    """Etched hatching: fine pressure strokes. shade(x,y)->0..1 keeps a line (density follows form shadow)."""
    for a, b in scan(poly, angle, spacing, jitter=0.5):
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        if shade is not None and RNG.random() > shade(mx, my):
            continue
        # break long lines into dashes like an etching needle
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        k = max(1, int(L / 9))
        for i in range(k):
            t0, t1 = i / k + RNG.uniform(0, .08), (i + 1) / k - RNG.uniform(0, .08)
            p = (a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0)
            q = (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1)
            tapered(p, q, w, color, opacity=opacity, bow=RNG.uniform(-.6, .6))


def grain(poly, n, spread=22, base=None):
    """Paper grain: specks of tone, light and dark, scattered inside the shape."""
    x0, y0, x1, y1 = bbox(poly)
    placed = 0
    tries = 0
    while placed < n and tries < n * 6:
        tries += 1
        x, y = RNG.uniform(x0, x1), RNG.uniform(y0, y1)
        if not inside(poly, x, y):
            continue
        d = RNG.uniform(-spread, spread)
        c = tuple(max(0, min(255, v + d)) for v in (base or MID))
        r = RNG.uniform(0.4, 1.1)
        add([(x, y), (x + RNG.uniform(-1.4, 1.4), y + RNG.uniform(-1.4, 1.4))], [r, r * 0.7], c, "line",
            opacity=RNG.uniform(0.5, 0.95))
        placed += 1


def contour(poly, color=INK, w=1.7, closed=True, thick_side=(0.6, 0.8)):
    """Outline with pressure: thicker on the shadow side, thinner on the lit side, a little wobble."""
    pts = poly + [poly[0]] if closed else poly
    rs = []
    for i, p in enumerate(pts):
        j = (i + 1) % len(pts)
        dx, dy = pts[j][0] - p[0], pts[j][1] - p[1]
        L = math.hypot(dx, dy) or 1
        side = (-dy / L) * thick_side[0] + (dx / L) * thick_side[1]
        rs.append(max(0.45, w * (0.75 + 0.5 * side + RNG.uniform(-0.12, 0.12))))
    add(pts, rs, color, "line")


def shape(poly, tone, light=(-1, -0.4), hatch=62, cont=1.6, hatch_color=INK, lo=DEEP, mid=MID, hi=LIGHT,
          shade_dir=(1, 0.6), n_grain=0, hatch_w=0.55, spacing=3.4):
    wash(poly, tone, light, lo, mid, hi)
    x0, y0, x1, y1 = bbox(poly)
    sx, sy = shade_dir

    def shade(x, y):
        u = ((x - x0) * sx + (y - y0) * sy) / (((x1 - x0) * abs(sx) + (y1 - y0) * abs(sy)) or 1)
        return max(0.05, min(0.95, u * 0.95 + 0.1 - tone * 0.4))
    if hatch is not None:
        etch(poly, hatch, spacing, hatch_color, hatch_w, shade)
    if n_grain:
        grain(poly, n_grain, base=ramp(tone, lo, mid, hi))
    if cont:
        contour(poly, INK, cont)


def jag(a, b, n, amp, down=True):
    """Ragged edge from a to b: n teeth hanging down (cloth edge)."""
    pts = []
    for i in range(n + 1):
        t = i / n
        x = a[0] + (b[0] - a[0]) * t
        y = a[1] + (b[1] - a[1]) * t
        if i not in (0, n):
            y += amp * RNG.uniform(0.4, 1.0) * (1 if i % 2 else -0.35)
            x += RNG.uniform(-2, 2)
        pts.append((x, y))
    return pts


# ---------- the drawing
def umbrella(cx, cy, scale=1.0, tilt=0.0, open_=1.0, shaft_len=190):
    """Canopy centred on (cx, cy)=apex-ish; open_ 0..1 narrows it to a closed furl."""
    def T(x, y):
        x, y = (x - 155) * scale, (y - 30) * scale
        a = math.radians(tilt)
        return (cx + x * math.cos(a) - y * math.sin(a), cy + x * math.sin(a) + y * math.cos(a))
    half = 114 * open_
    n = 9
    tips = [(155 + half - i * (2 * half / n), 86) for i in range(n + 1)]
    dome = [(155 - half, 86), (155 - half * .74, 54), (155 - half * .4, 38), (155, 30), (155 + half * .4, 38),
            (155 + half * .74, 54), (155 + half, 86)]
    dome = catmull(dome, 6)
    edge = []
    for i in range(n):
        a, b = tips[i], tips[i + 1]
        for k in range(1, 7):
            t = k / 7
            edge.append((a[0] + (b[0] - a[0]) * t, 86 - 9 * math.sin(t * math.pi) * (open_ ** .5) + 4 * (1 - t) * 0))
        edge.append((b[0], 90 + RNG.uniform(0, 3)))
    poly = [T(*p) for p in dome + edge]
    under = [T(*p) for p in [(155 - half * .96, 84), (155, 58), (155 + half * .96, 84)] + edge[::-1]]
    # outer shell, then dark underside
    shape(poly, 0.42, light=(-1, -1), hatch=-28, cont=2.0, n_grain=260, spacing=3.0)
    shape(under, 0.1, light=(0, -1), hatch=18, cont=0, spacing=2.6, hatch_w=0.5)
    # ribs and rib highlights
    for i in range(n + 1):
        tip = T(*tips[i])
        apex = T(155, 30)
        mid = ((apex[0] * .5 + tip[0] * .5) + (tip[0] - apex[0]) * 0.02, apex[1] * .5 + tip[1] * .5 - 8 * scale)
        pts = catmull([apex, mid, tip], 8)
        add(pts, [0.9 * scale + 0.5 * (j / len(pts)) for j in range(len(pts))], INK, "line")
        add([(x - 1.2, y - 1.0) for x, y in pts], 0.5, LIGHT, "line", opacity=0.8)
    # ruffled seam under the rim
    contour([T(*p) for p in edge], INK, 1.8, closed=False)
    return T


def finial_and_shaft(T, shaft_to, tip_y=None):
    fx, fy = T(155, 30)
    top = (fx, fy - 24)
    shape([(fx - 3, fy), (fx + 3, fy), (fx + 2, fy - 12), (fx, fy - 22), (fx - 2, fy - 12)], 0.6, hatch=None, cont=1.1)
    shape([(fx, fy - 30), (fx + 5, fy - 20), (fx, fy - 12), (fx - 5, fy - 20)], 0.7, hatch=None, cont=1.1)
    return top


def shaft(p0, p1, w=3.2):
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy)
    nx, ny = -dy / L * w, dx / L * w
    poly = [(p0[0] + nx, p0[1] + ny), (p1[0] + nx, p1[1] + ny), (p1[0] - nx, p1[1] - ny), (p0[0] - nx, p0[1] - ny)]
    shape(poly, 0.45, light=(-1, 0), hatch=None, cont=1.2, lo=DEEP, mid=(110, 92, 70), hi=(170, 148, 108))
    add([(p0[0] - nx * .4, p0[1] - ny * .4), (p1[0] - nx * .4, p1[1] - ny * .4)], 0.5, (210, 190, 150), "line", opacity=.8)


def terminal(p, size=1.0):
    x, y = p
    shape([(x, y - 14 * size), (x + 7 * size, y), (x, y + 17 * size), (x - 7 * size, y)], 0.55, hatch=None, cont=1.3,
          lo=DEEP, mid=(120, 100, 72), hi=(190, 160, 110))


def hand(p, r=7):
    x, y = p
    poly = catmull([(x - r * .8, y - r), (x + r * .8, y - r * .9), (x + r, y + r * .5), (x, y + r * 1.1),
                    (x - r, y + r * .4)], 5, True)
    shape(poly, 0.55, hatch=None, cont=1.1, lo=(90, 74, 62), mid=SKIN, hi=(190, 164, 140))


def hat(c, tilt=-14, bend=1.0):
    cx, cy = c
    a = math.radians(tilt)

    def T(x, y):
        return (cx + x * math.cos(a) - y * math.sin(a), cy + x * math.sin(a) + y * math.cos(a))
    cone = catmull([T(-27, 0), T(-30, -16), T(-36, -30 * bend), T(-52, -44 * bend), T(-44, -52 * bend), T(-24, -38),
                    T(2, -34), T(22, -14), T(28, 0)], 5, True)
    brim = catmull([T(-44, 2), T(-20, -6), T(10, -6), T(42, -2), T(40, 6), T(8, 10), T(-24, 9), T(-44, 6)], 5, True)
    shape(cone, 0.18, light=(-1, -1), hatch=50, cont=1.7, n_grain=60, hi=(110, 96, 80), spacing=3.0)
    shape(brim, 0.22, light=(-1, -1), hatch=-20, cont=1.8, n_grain=40, hi=(120, 104, 86), spacing=3.0)
    band = [T(-27, -3), T(24, -3), T(24, -9), T(-28, -10)]
    shape(band, 0.55, hatch=None, cont=1.0, lo=DEEP, mid=(110, 92, 70), hi=(170, 148, 108))


def hair_and_scarf(root, spread=1.0):
    rx, ry = root
    # scarf ribbon: wide cloth streaming back and down, ragged torn end
    rib = [(rx + 6, ry + 8), (rx - 8, ry + 36), (rx - 30, ry + 70), (rx - 58, ry + 104), (rx - 76, ry + 136)]
    left = [(x - 9 + i * 1.2, y - 3) for i, (x, y) in enumerate(rib)]
    right = [(x + 10 - i * 1.8, y + 3) for i, (x, y) in enumerate(rib)]
    right[-1] = (rx - 70, ry + 148)
    poly = catmull(left, 5) + jag(right[-1], (rx - 82, ry + 134), 6, 7)[::-1] + catmull(right[::-1], 5)
    shape(poly, 0.55, light=(-1, 0), hatch=70, cont=1.2, lo=(120, 104, 82), mid=BONE, hi=(224, 208, 176),
          hatch_color=(60, 52, 44), n_grain=140, spacing=3.6, hatch_w=0.5)
    # long hair strands
    for i in range(34):
        t = i / 34
        sx, sy = rx + 4 + t * 16, ry - 6 + t * 24
        pts = [(sx, sy), (sx - 28 * spread - t * 8, sy + 24 + t * 22), (sx - 62 * spread - RNG.uniform(0, 18), sy + 66 + RNG.uniform(0, 26)),
               (sx - 96 * spread - RNG.uniform(0, 14), sy + 100 + RNG.uniform(0, 36))]
        pts = catmull(pts, 7)
        c = ramp(RNG.uniform(0.15, 0.75), (60, 50, 42), (110, 90, 70), (170, 148, 118))
        add(pts, [max(0.2, 1.4 * (1 - j / len(pts)) + .2) for j in range(len(pts))], c, "line", opacity=0.9)


def body(sx=0, lean=0):
    """Torso, belt, tiered ragged skirt, legs, boots. lean shifts lower body left (airborne)."""
    torso = catmull([(110, 205), (128, 198), (146, 204), (152, 232), (156, 262), (126, 270), (112, 246)], 5, True)
    shape(torso, 0.35, light=(-1, -.3), hatch=58, cont=1.6, n_grain=80, lo=(44, 38, 34), mid=(92, 80, 70), hi=(140, 122, 100),
          spacing=3.2)
    # three skirt tiers: flared, ragged, leaf-like layers (top narrow, hem wide with big irregular teeth)
    tiers = [((112, 258), (160, 258), 118, 168, 306, 20, 8), ((100, 286), (166, 286), 98, 178, 352, 26, 10),
             ((86, 322), (178, 322), 74, 188, 400, 34, 11)]
    for k, (a, b, hl, hr, yb, amp, n) in enumerate(tiers):
        bot = jag((hl - 8 + lean * k * 2, yb), (hr + 6, yb), n, amp)
        poly = [a, b] + bot[::-1]
        shape(poly, 0.34 + 0.07 * k, light=(-1, -.2), hatch=72, cont=1.8, n_grain=190, lo=(48, 41, 36), mid=(104, 92, 80),
              hi=(158, 140, 118), spacing=3.0)
        for f in range(7):
            x0 = a[0] + (b[0] - a[0]) * (f + 0.5) / 7
            xb = hl + (hr - hl) * (f + 0.5) / 7 + RNG.uniform(-6, 6)
            add(catmull([(x0, a[1] + 4), ((x0 + xb) / 2 + RNG.uniform(-4, 4), (a[1] + yb) / 2), (xb, yb - 4 - RNG.uniform(0, 14))], 6),
                0.8, INK, "line", opacity=.75)
    belt = [(110, 246), (156, 244), (157, 254), (111, 256)]
    shape(belt, 0.6, hatch=None, cont=1.1, lo=DEEP, mid=(120, 100, 76), hi=(184, 156, 112))


def legs():
    for (a, b, c) in (((108, 382), (98, 420), (92, 450)), ((136, 384), (132, 424), (126, 466))):
        pts = catmull([a, b, c], 8)
        poly = [(x - 8, y) for x, y in pts] + [(x + 8, y) for x, y in pts[::-1]]
        shape(poly, 0.12, hatch=80, cont=1.4, n_grain=40, lo=(28, 24, 22), mid=(56, 50, 46), hi=(94, 84, 74), spacing=3.0)
    for (x, y) in ((92, 446), (126, 462)):
        boot = catmull([(x - 10, y - 18), (x + 9, y - 18), (x + 11, y + 4), (x + 4, y + 10), (x - 18, y + 12), (x - 12, y + 2)], 5, True)
        shape(boot, 0.2, light=(-1, -1), hatch=40, cont=1.7, n_grain=40, hi=(120, 104, 86), spacing=2.8)
        for k in range(4):
            tapered((x - 8, y - 14 + k * 5), (x + 8, y - 12 + k * 5), 0.9, BONE, opacity=.8)


def arm(shoulder, wrist, w=11):
    dx, dy = wrist[0] - shoulder[0], wrist[1] - shoulder[1]
    L = math.hypot(dx, dy)
    nx, ny = -dy / L * w, dx / L * w
    poly = catmull([(shoulder[0] - nx, shoulder[1] - ny), ((shoulder[0] + wrist[0]) / 2 - nx * .8 - 4, (shoulder[1] + wrist[1]) / 2 - ny * .8),
                    (wrist[0] - nx * .5, wrist[1] - ny * .5), (wrist[0] + nx * .5, wrist[1] + ny * .5),
                    ((shoulder[0] + wrist[0]) / 2 + nx * .8 - 4, (shoulder[1] + wrist[1]) / 2 + ny * .8),
                    (shoulder[0] + nx, shoulder[1] + ny)], 5, True)
    shape(poly, 0.3, light=(-1, 0), hatch=75, cont=1.6, n_grain=50, lo=(34, 28, 26), mid=(72, 62, 54), hi=(116, 100, 84), spacing=3.0)


def draw_open():
    T = umbrella(160, 62, 1.0, tilt=0)
    shaft((160, 78), (166, 214), 3.0)
    terminal((166, 226), 1.0)
    finial_and_shaft(T, None)
    LEAN[0] = -9.0
    hair_and_scarf((112, 204))
    body(lean=1)
    legs()
    hat((112, 188), -14)
    LEAN[0] = -4.0
    arm((124, 214), (160, 146), 12)
    LEAN[0] = 0.0
    hand((161, 134))
    hand((163, 152), 6)


def draw_closed():
    hair_and_scarf((108, 202), 0.6)
    body(lean=0)
    legs()
    # closed umbrella held low like a cane
    shaft((166, 150), (176, 440), 4.0)
    umbrella(176, 176, 0.32, tilt=170, open_=0.18)
    arm((130, 212), (160, 300))
    hand((166, 304))
    hat((108, 192), -6)


def draw_attack():
    hair_and_scarf((108, 202))
    body(lean=2)
    legs()
    T = umbrella(244, 200, 0.7, tilt=-80)
    shaft((130, 234), (210, 206), 2.6)
    arm((130, 212), (190, 214))
    hand((196, 212))
    hat((108, 192))


def draw_shield():
    hair_and_scarf((108, 202), 0.8)
    body(lean=0)
    legs()
    T = umbrella(210, 250, 0.85, tilt=-100)
    shaft((150, 250), (230, 250), 3.0)
    arm((130, 214), (166, 246))
    hand((170, 248))
    hat((108, 192), -8)


{"open": draw_open, "closed": draw_closed, "attack": draw_attack, "shield": draw_shield}[POSE]()

# ---------- Blender's background GP shader renders every stroke black here, so the same stroke data (kept above as the
# editable Grease Pencil object) is also laid down as flat vertex-coloured ribbons and fills, drawn in order, and
# rendered by Workbench. Painter's order = stroke order.
import bmesh
from mathutils import Vector, geometry

obj.hide_render = True
me = bpy.data.meshes.new("EllaInk")
bm = bmesh.new()
col = bm.loops.layers.color.new("c")
for idx, (pts, rs, color, kind, cyc, op) in enumerate(STROKES):
    y = -idx * 4e-5
    c = tuple(v / 255.0 for v in color)
    c = (c[0], c[1], c[2], 1.0)
    if kind == "fill":
        poly = [Vector((P(*q)[0], y, P(*q)[2])) for q in pts]
        for tri in geometry.tessellate_polygon([poly]):
            vs = [bm.verts.new(poly[i]) for i in tri]
            try:
                f = bm.faces.new(vs)
            except ValueError:
                continue
            for lp in f.loops:
                lp[col] = c
        continue
    n = len(pts)
    left, right = [], []
    for i in range(n):
        a_ = pts[max(i - 1, 0)]
        b_ = pts[min(i + 1, n - 1)]
        dx, dy = b_[0] - a_[0], b_[1] - a_[1]
        L = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / L, dx / L
        r = rs[i] * (0.35 + 0.65 * op)
        left.append((pts[i][0] + nx * r, pts[i][1] + ny * r))
        right.append((pts[i][0] - nx * r, pts[i][1] - ny * r))
    for i in range(n - 1):
        q = [left[i], left[i + 1], right[i + 1], right[i]]
        vs = [bm.verts.new((P(*pt)[0], y, P(*pt)[2])) for pt in q]
        try:
            f = bm.faces.new(vs)
        except ValueError:
            continue
        for lp in f.loops:
            lp[col] = c
    # round dot at the start so very short specks still show
    r0 = rs[0]
    ring = [(pts[0][0] + r0 * math.cos(k * math.pi / 3), pts[0][1] + r0 * math.sin(k * math.pi / 3)) for k in range(6)]
    vs = [bm.verts.new((P(*pt)[0], y, P(*pt)[2])) for pt in ring]
    try:
        f = bm.faces.new(vs)
        for lp in f.loops:
            lp[col] = c
    except ValueError:
        pass
bm.to_mesh(me)
bm.free()
me.color_attributes.active_color = me.color_attributes["c"]
me.color_attributes.render_color_index = 0
mesh_obj = bpy.data.objects.new("EllaInkMesh", me)
scn.collection.objects.link(mesh_obj)
print("gp_ella: strokes", len(STROKES), "faces", len(me.polygons))
cam = bpy.data.cameras.new("cam")
cam.type = "ORTHO"
cam.ortho_scale = W * SCALE
co = bpy.data.objects.new("cam", cam)
scn.collection.objects.link(co)
co.location = (W * SCALE / 2, -10, -H * SCALE / 2)
co.rotation_euler = (math.radians(90), 0, 0)
scn.camera = co
scn.render.engine = "BLENDER_WORKBENCH"
scn.render.resolution_x, scn.render.resolution_y = W, H
scn.render.film_transparent = True
scn.render.image_settings.file_format = "PNG"
scn.render.image_settings.color_mode = "RGBA"
scn.display.shading.light = "FLAT"
scn.display.shading.color_type = "VERTEX"
scn.display.render_aa = "8"
scn.view_settings.view_transform = "Standard"
scn.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("gp_ella: wrote", OUT)
