#!/usr/bin/env python3
"""Umbrella Storybook: the game's display face, made procedurally (stdlib only, no outside font is read or copied).

Every glyph is a skeleton (lines and elliptical arcs) drawn with a slanted broad-nib pen: the sweep of the nib along
each skeleton segment is one convex contour, so thick and thin strokes come from the pen angle, as in hand lettering.
Wedge serifs and diamond dots are added as their own contours. Lowercase letters are small capitals (the title-screen
reference letters its menu in small caps). All contours wind the same way and overlap (non-zero fill).

  python3 Art/Source/UI/Font/build_font.py            write the TTF, the C++ byte array and the specimen PNG
  python3 Art/Source/UI/Font/build_font.py --check    exit 1 when a committed output differs from a fresh build
Outputs:
  Art/Source/UI/Font/UmbrellaStorybook.ttf                              the font file (source of the byte array)
  Source/UmbrellaElla/Private/UI/Style/UmbrellaStorybookFont.inl        the same bytes for the game (no loose file)
  Art/Source/UI/Font/UmbrellaStorybook_specimen.png (only with --specimen)   a preview sheet
"""
import math
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
TTF = os.path.join(HERE, "UmbrellaStorybook.ttf")
INL = os.path.join(ROOT, "Source", "UmbrellaElla", "Private", "UI", "Style", "UmbrellaStorybookFont.inl")
SPECIMEN = os.path.join(HERE, "UmbrellaStorybook_specimen.png")

UPM = 1000
CAP = 700               # capital height
ASCENT, DESCENT = 860, -240
PEN_ANGLE = math.radians(20.0)
NIB_W, NIB_T = 96.0, 20.0      # nib width and thickness for capitals
SMALL = 0.78            # small-capital scale
SMALL_NIB = 0.86        # small capitals keep most of the stroke weight
SIDE = 46               # side bearing
SPACE = 250
ARC_STEP = 11.0         # degrees per arc segment
INK_JITTER = 9.0        # font units: hand-inked edge roughness (title is about 60 px, so ~0.5 px); fixed hash, no random state


# ------------------------------------------------------------------ geometry
def arc(cx, cy, rx, ry, a0, a1):
    """Points on an ellipse from angle a0 to a1 (degrees, counter-clockwise positive)."""
    n = max(2, int(math.ceil(abs(a1 - a0) / ARC_STEP)))
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def hull(points):
    pts = sorted(set((round(x, 3), round(y, 3)) for x, y in points))
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def area(poly):
    return 0.5 * sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1]
                     for i in range(len(poly)))


def clockwise(poly):
    return poly if area(poly) < 0 else poly[::-1]


def nib(scale=1.0, width=None):
    w, t = (width or NIB_W) * scale, NIB_T * scale
    ux, uy = math.cos(PEN_ANGLE), math.sin(PEN_ANGLE)
    vx, vy = -uy, ux
    return [(sx * w / 2 * ux + sy * t / 2 * vx, sx * w / 2 * uy + sy * t / 2 * vy)
            for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]


def sweep(points, pen):
    """One convex contour per skeleton segment: the hull of the nib at both ends."""
    out = []
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        out.append(hull([(x0 + px, y0 + py) for px, py in pen] + [(x1 + px, y1 + py) for px, py in pen]))
    return out


def foot(x, y=0.0, left=62.0, right=62.0, half=44.0, up=True):
    """A wedge serif at a stem end: thin slab with a bracket on each side. up=False turns it for a stem top."""
    s = 1.0 if up else -1.0
    pts = [(x - half - left, y), (x + half + right, y), (x + half + right, y + s * 16), (x + half + 14, y + s * 30),
           (x + half, y + s * 74), (x - half, y + s * 74), (x - half - 14, y + s * 30), (x - half - left, y + s * 16)]
    return pts


def diamond(x, y, r=52.0):
    return [(x, y + r), (x + r * 0.92, y), (x, y - r), (x - r * 0.92, y)]


# ------------------------------------------------------------------ glyph skeletons (capital height 700)
T, B, M = 680.0, 20.0, 350.0     # top, bottom and middle centre lines
L = 80.0                         # the usual left stem


def stem(x, y0=B, y1=T):
    return [(x, y0), (x, y1)]


def glyphs():
    """name -> (strokes, extras). A stroke is a list of points; an extra is a ready polygon (serif, dot)."""
    g = {}

    def add(ch, strokes, extras=()):
        g[ch] = ([list(s) for s in strokes], [list(e) for e in extras])

    hs, fs = (lambda x, **k: foot(x, CAP, up=False, **k)), (lambda x, **k: foot(x, 0.0, **k))
    add("A", [[(300, 690), (40, B)], [(300, 690), (560, B)], [(128, 235), (478, 235)]],
        [foot(40, 0, half=18), foot(560, 0)])
    add("B", [stem(L), [(L, T), (285, T)] + arc(285, 528, 150, 152, 90, -90) + [(L, 376)],
              [(L, 376), (305, 376)] + arc(305, 198, 178, 178, 90, -90) + [(L, B)]],
        [hs(L, right=0), fs(L, right=0)])
    add("C", [arc(370, M, 320, 340, 48, 312)], [])
    add("D", [stem(L), [(L, T), (270, T)] + arc(270, M, 330, 330, 90, -90) + [(L, B)]], [hs(L, right=0), fs(L, right=0)])
    add("E", [stem(L), [(L, T), (440, T)], [(L, 362), (385, 362)], [(L, B), (460, B)]], [hs(L, right=0), fs(L, right=0)])
    add("F", [stem(L), [(L, T), (440, T)], [(L, 362), (385, 362)]], [hs(L, right=0), fs(L)])
    add("G", [arc(370, M, 320, 340, 48, 318), [(612, 300), (612, 64)], [(455, 300), (650, 300)]], [])
    add("H", [stem(L), stem(570), [(L, 356), (570, 356)]], [hs(L), fs(L), hs(570), fs(570)])
    add("I", [stem(L)], [hs(L), fs(L)])
    add("J", [[(250, T), (250, 170)] + arc(120, 170, 130, 160, 0, -140)], [hs(250)])
    add("K", [stem(L), [(L, 330), (490, 690)], [(190, 425), (530, B)]], [hs(L), fs(L), foot(530, 0)])
    add("L", [stem(L), [(L, B), (450, B)]], [hs(L), fs(L, right=0)])
    add("M", [[(76, B), (112, T)], [(112, T), (385, 70)], [(385, 70), (658, T)], [(658, T), (694, B)]],
        [foot(76, 0, half=22), foot(694, 0)])
    add("N", [stem(L), [(L, T), (570, B)], stem(570)], [fs(L, half=30), hs(570, half=30), foot(52, CAP, up=False, left=20, right=0, half=20)])
    add("O", [arc(365, M, 325, 345, 0, 360)], [])
    add("P", [stem(L), [(L, T), (285, T)] + arc(285, 505, 172, 175, 90, -90) + [(L, 330)]], [hs(L, right=0), fs(L)])
    add("Q", [arc(365, M, 325, 345, 0, 360), [(390, 130), (680, -130)]], [])
    add("R", [stem(L), [(L, T), (285, T)] + arc(285, 512, 168, 168, 90, -90) + [(L, 344)], [(262, 344), (545, B)]],
        [hs(L, right=0), fs(L), foot(545, 0, left=30)])
    add("S", [arc(285, 522, 200, 168, 28, 270)[:-1] + arc(285, 186, 215, 168, 90, -152)], [])
    add("T", [stem(300), [(30, T), (570, T)]], [fs(300)])
    add("U", [[(L, T), (L, 255)] + arc(315, 255, 235, 240, 180, 360) + [(550, T)]], [hs(L), hs(550, half=30)])
    add("V", [[(40, T), (300, B)], [(300, B), (560, T)]], [foot(40, CAP, up=False), foot(560, CAP, up=False, half=18)])
    add("W", [[(30, T), (225, B)], [(225, B), (420, T)], [(420, T), (615, B)], [(615, B), (810, T)]],
        [foot(30, CAP, up=False), foot(810, CAP, up=False, half=18)])
    add("X", [[(60, T), (545, B)], [(545, T), (60, B)]],
        [foot(60, CAP, up=False), foot(545, 0), foot(545, CAP, up=False, half=18), foot(60, 0, half=18)])
    add("Y", [[(40, T), (300, 335)], [(560, T), (300, 335)], [(300, 335), (300, B)]],
        [foot(40, CAP, up=False), foot(560, CAP, up=False, half=18), fs(300)])
    add("Z", [[(60, T), (545, T)], [(545, T), (60, B)], [(60, B), (560, B)]], [])

    add("0", [arc(270, M, 225, 345, 0, 360)], [])
    add("1", [stem(250), [(105, 555), (250, T)]], [fs(250)])
    add("2", [arc(265, 505, 195, 178, 165, -42) + [(60, B)], [(60, B), (490, B)]], [])
    add("3", [arc(245, 522, 185, 160, 150, -90)[:-1] + arc(245, 192, 205, 170, 90, -150)], [])
    add("4", [[(385, B), (385, T)], [(385, T), (50, 232)], [(50, 232), (530, 232)]], [fs(385)])
    add("5", [[(440, T), (135, T)], [(135, T), (112, 400)], arc(245, 222, 225, 202, 118, -150)], [])
    add("6", [arc(410, 250, 330, 440, 82, 180), arc(280, 222, 200, 204, 0, 360)], [])
    add("7", [[(50, T), (500, T)], [(500, T), (205, B)]], [])
    add("8", [arc(262, 528, 172, 158, 0, 360), arc(262, 190, 202, 176, 0, 360)], [])
    add("9", [arc(250, 478, 200, 204, 0, 360), arc(120, 450, 330, 440, -98, 0)], [])

    add(".", [], [diamond(60, 52)])
    add(",", [[(70, 30), (25, -120)]], [diamond(60, 52)])
    add(":", [], [diamond(60, 52), diamond(60, 400)])
    add(";", [[(70, 30), (25, -120)]], [diamond(60, 52), diamond(60, 400)])
    add("!", [[(60, T), (60, 230)]], [diamond(60, 52)])
    add("?", [arc(200, 520, 165, 165, 160, -70) + [(200, 230)]], [diamond(200, 52)])
    add("'", [[(40, 700), (30, 500)]], [])
    add('"', [[(40, 700), (30, 500)], [(190, 700), (180, 500)]], [])
    add("-", [[(30, 270), (300, 270)]], [])
    add("–", [[(20, 270), (480, 270)]], [])
    add("—", [[(20, 270), (780, 270)]], [])
    add("_", [[(0, -90), (500, -90)]], [])
    add("(", [arc(330, M, 250, 470, 122, 238)], [])
    add(")", [arc(-50, M, 250, 470, 58, -58)], [])
    add("[", [[(200, 760), (60, 760)], [(60, 760), (60, -100)], [(60, -100), (200, -100)]], [])
    add("]", [[(20, 760), (160, 760)], [(160, 760), (160, -100)], [(160, -100), (20, -100)]], [])
    add("/", [[(330, 760), (30, -100)]], [])
    add("%", [arc(140, 540, 110, 145, 0, 360), [(520, T), (120, B)], arc(500, 160, 110, 145, 0, 360)], [])
    add("+", [[(50, 330), (450, 330)], [(250, 130), (250, 530)]], [])
    add("=", [[(50, 420), (450, 420)], [(50, 230), (450, 230)]], [])
    add("*", [[(170, 700), (170, 440)], [(60, 630), (280, 510)], [(280, 630), (60, 510)]], [])
    add("&", [[(560, B), (190, 470)] + arc(280, 560, 118, 128, 200, -20) + [(110, 300)]
              + arc(270, 200, 195, 180, 150, 372) + [(560, 350)]], [])
    add("#", [[(190, T), (130, B)], [(410, T), (350, B)], [(40, 470), (520, 470)], [(20, 230), (500, 230)]], [])
    add("<", [[(430, 560), (60, 330)], [(60, 330), (430, 100)]], [])
    add(">", [[(60, 560), (430, 330)], [(430, 330), (60, 100)]], [])
    add("…", [], [diamond(60, 52), diamond(260, 52), diamond(460, 52)])
    add("•", [], [diamond(110, 350, 90)])
    return g


ALIASES = {"’": "'", "‘": "'", "“": '"', "”": '"', "`": "'"}


def _noise(a, b, k):
    """Deterministic value in [-1, 1] from integer inputs (no random state, so the build stays byte-identical)."""
    h = (a * 73856093 ^ b * 19349663 ^ k * 83492791) & 0xFFFFFFFF
    h = (h ^ (h >> 13)) * 1274126177 & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 32767.5 - 1.0


def rough(poly):
    """Hand-inked edge: long edges get a midpoint, every vertex a small fixed-hash nudge."""
    pts = []
    n = len(poly)
    for i, (x, y) in enumerate(poly):
        nx, ny = poly[(i + 1) % n]
        pts.append((x, y))
        if math.hypot(nx - x, ny - y) > 70:
            pts.append(((x + nx) / 2.0, (y + ny) / 2.0))
    out = []
    for x, y in pts:
        ix, iy = int(round(x)), int(round(y))
        out.append((x + INK_JITTER * _noise(ix, iy, 1), y + INK_JITTER * _noise(ix, iy, 2)))
    return out


def build_glyph(strokes, extras, scale=1.0, nib_scale=1.0):
    """Contours (clockwise integer polygons), shifted so the left edge sits at the side bearing; returns (contours, advance)."""
    pen = nib(nib_scale)
    polys = []
    for s in strokes:
        polys += sweep([(x * scale, y * scale) for x, y in s], pen)
    for e in extras:
        k = scale
        polys.append([(x * k, y * k) for x, y in e])
    polys = [clockwise(rough(p)) for p in polys if len(p) >= 3]
    xmin = min(x for p in polys for x, _ in p)
    xmax = max(x for p in polys for x, _ in p)
    side = SIDE * (scale if scale < 1.0 else 1.0)
    dx = side - xmin
    out = [[(int(round(x + dx)), int(round(y))) for x, y in p] for p in polys]
    return out, int(round(xmax - xmin + 2 * side))


def all_glyphs():
    """[(codepoints, contours, advance)], glyph 0 = .notdef, then space, then the rest in a fixed order."""
    src = glyphs()
    out = [([], [clockwise([(60, 0), (440, 0), (440, 700), (60, 700)]), clockwise([(110, 50), (110, 650), (390, 650), (390, 50)])[::-1]], 500),
           ([0x20, 0xA0], [], SPACE)]
    for ch in sorted(src):
        strokes, extras = src[ch]
        cps = [ord(ch)] + [ord(a) for a, b in sorted(ALIASES.items()) if b == ch]
        contours, adv = build_glyph(strokes, extras)
        out.append((cps, contours, adv))
        if "A" <= ch <= "Z":
            contours, adv = build_glyph(strokes, extras, SMALL, SMALL_NIB)
            out.append(([ord(ch.lower())], contours, adv))
    return out


# ------------------------------------------------------------------ TrueType writer
def _glyf(contours):
    if not contours:
        return b""
    pts = [p for c in contours for p in c]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    ends, n = [], 0
    for c in contours:
        n += len(c)
        ends.append(n - 1)
    data = struct.pack(">hhhhh", len(contours), min(xs), min(ys), max(xs), max(ys))
    data += b"".join(struct.pack(">H", e) for e in ends) + struct.pack(">H", 0)
    data += bytes([0x41] + [0x01] * (len(pts) - 1))      # on-curve; the first point also says "contours overlap"
    px = py = 0
    xb, yb = b"", b""
    for x, y in pts:
        xb += struct.pack(">h", x - px)
        yb += struct.pack(">h", y - py)
        px, py = x, y
    data += xb + yb
    return data + b"\0" * (-len(data) % 4)


def _cmap(mapping):
    cps = sorted(mapping)
    segs = []
    for cp in cps:
        if segs and cp == segs[-1][1] + 1 and mapping[cp] == mapping[segs[-1][1]] + 1:
            segs[-1][1] = cp
        else:
            segs.append([cp, cp])
    segs.append([0xFFFF, 0xFFFF])
    n = len(segs)
    ends = [s[1] for s in segs]
    starts = [s[0] for s in segs]
    deltas = [((mapping[s[0]] - s[0]) & 0xFFFF) if s[0] != 0xFFFF else 1 for s in segs]
    sr = 2 * (2 ** int(math.floor(math.log2(n))))
    sub = struct.pack(">HHHHHHH", 4, 16 + 8 * n, 0, n * 2, sr, int(math.log2(sr / 2)), 2 * n - sr)
    sub += b"".join(struct.pack(">H", e) for e in ends) + struct.pack(">H", 0)
    sub += b"".join(struct.pack(">H", s) for s in starts)
    sub += b"".join(struct.pack(">H", d) for d in deltas)
    sub += b"".join(struct.pack(">H", 0) for _ in segs)
    return struct.pack(">HH", 0, 1) + struct.pack(">HHI", 3, 1, 12) + sub


def _name():
    recs = {1: "Umbrella Storybook", 2: "Regular", 3: "Umbrella Storybook Regular 1.0", 4: "Umbrella Storybook",
            5: "Version 1.0", 6: "UmbrellaStorybook-Regular",
            0: "Made procedurally for Umbrella Ella The Stolen Hour (Art/Source/UI/Font/build_font.py)"}
    strings, table = b"", b""
    for nid in sorted(recs):
        s = recs[nid].encode("utf-16-be")
        table += struct.pack(">HHHHHH", 3, 1, 0x409, nid, len(s), len(strings))
        strings += s
    return struct.pack(">HHH", 0, len(recs), 6 + 12 * len(recs)) + table + strings


def _checksum(data):
    data += b"\0" * (-len(data) % 4)
    return sum(struct.unpack(">%dI" % (len(data) // 4), data)) & 0xFFFFFFFF


def build_ttf():
    gl = all_glyphs()
    glyf, loca, mapping = b"", [0], {}
    adv, lsb = [], []
    bounds = [1 << 15, 1 << 15, -(1 << 15), -(1 << 15)]
    max_pts = max_cont = 0
    for gid, (cps, contours, a) in enumerate(gl):
        glyf += _glyf(contours)
        loca.append(len(glyf))
        for cp in cps:
            mapping[cp] = gid
        pts = [p for c in contours for p in c]
        adv.append(a)
        lsb.append(min(p[0] for p in pts) if pts else 0)
        if pts:
            bounds = [min(bounds[0], min(p[0] for p in pts)), min(bounds[1], min(p[1] for p in pts)),
                      max(bounds[2], max(p[0] for p in pts)), max(bounds[3], max(p[1] for p in pts))]
        max_pts, max_cont = max(max_pts, len(pts)), max(max_cont, len(contours))
    n = len(gl)
    head = struct.pack(">IIIIHHqqhhhhHHhhh", 0x00010000, 0x00010000, 0, 0x5F0F3CF5, 0x000B, UPM, 3_800_000_000, 3_800_000_000,
                       bounds[0], bounds[1], bounds[2], bounds[3], 0, 8, 2, 1, 0)
    hhea = struct.pack(">IhhhHhhhhhhhhhhhH", 0x00010000, ASCENT, DESCENT, 0, max(adv), min(lsb), 0, bounds[2], 1, 0, 0,
                       0, 0, 0, 0, 0, n)
    maxp = struct.pack(">IHHHHHHHHHHHHHH", 0x00010000, n, max_pts, max_cont, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0)
    hmtx = b"".join(struct.pack(">Hh", a, l) for a, l in zip(adv, lsb))
    loca_b = b"".join(struct.pack(">I", o) for o in loca)
    os2 = struct.pack(">HhHHHhhhhhhhhhhh", 4, int(sum(adv) / n), 400, 5, 0, 650, 700, 0, 140, 650, 600, 0, 480, 50, 300, 0)
    os2 += bytes([2, 2, 5, 3, 0, 0, 0, 0, 0, 0])
    os2 += struct.pack(">IIII", 1, 0, 0, 0) + b"UMEL" + struct.pack(">HHH", 0x40, min(mapping), min(0xFFFF, max(mapping)))
    os2 += struct.pack(">hhhHH", ASCENT, DESCENT, 0, ASCENT, -DESCENT) + struct.pack(">II", 1, 0)
    os2 += struct.pack(">hhHHH", int(CAP * SMALL), CAP, 0, 0x20, 1)
    post = struct.pack(">IIhhIIIII", 0x00030000, 0, -100, 50, 0, 0, 0, 0, 0)
    tables = {b"OS/2": os2, b"cmap": _cmap(mapping), b"glyf": glyf, b"head": head, b"hhea": hhea, b"hmtx": hmtx,
              b"loca": loca_b, b"maxp": maxp, b"name": _name(), b"post": post}
    tags = sorted(tables)
    nt = len(tags)
    sr = 16 * (2 ** int(math.floor(math.log2(nt))))
    header = struct.pack(">IHHHH", 0x00010000, nt, sr, int(math.log2(sr / 16)), nt * 16 - sr)
    offset = 12 + 16 * nt
    directory, body = b"", b""
    for tag in tags:
        d = tables[tag]
        directory += tag + struct.pack(">III", _checksum(d), offset, len(d))
        pad = d + b"\0" * (-len(d) % 4)
        body += pad
        offset += len(pad)
    font = header + directory + body
    adj = (0xB1B0AFBA - _checksum(font)) & 0xFFFFFFFF
    at = 12 + 16 * tags.index(b"head")
    head_off = struct.unpack(">I", font[at + 8:at + 12])[0]
    return font[:head_off + 8] + struct.pack(">I", adj) + font[head_off + 12:]


def inl_text(data):
    lines = ["// Generated by Art/Source/UI/Font/build_font.py (Umbrella Storybook, made procedurally). Do not edit by hand:",
             "// change the script and run it again; `build_font.py --check` fails when this file is stale.",
             "#pragma once",
             f"static const int32 GUmbrellaStorybookFontSize = {len(data)};",
             "static const uint8 GUmbrellaStorybookFontData[] = {"]
    for i in range(0, len(data), 32):
        lines.append("\t" + ",".join(str(b) for b in data[i:i + 32]) + ",")
    lines.append("};")
    return "\n".join(lines) + "\n"


# ------------------------------------------------------------------ specimen (pure Python raster, for a look only)
def raster(polys, w, h, ss=3):
    """Non-zero fill coverage (0..1 rows) of polygons given in pixel space, y down."""
    W, H = w * ss, h * ss
    cover = [[0] * w for _ in range(h)]
    edges = []
    for p in polys:
        for (x0, y0), (x1, y1) in zip(p, p[1:] + p[:1]):
            if y0 != y1:
                edges.append((x0 * ss, y0 * ss, x1 * ss, y1 * ss))
    for sy in range(H):
        yc = sy + 0.5
        xs = []
        for x0, y0, x1, y1 in edges:
            if (y0 <= yc < y1) or (y1 <= yc < y0):
                xs.append((x0 + (yc - y0) * (x1 - x0) / (y1 - y0), 1 if y1 > y0 else -1))
        if not xs:
            continue
        xs.sort()
        wind, row = 0, cover[sy // ss]
        for (xa, d), (xb, _) in zip(xs, xs[1:]):
            wind += d
            if wind != 0:
                a, b = max(0, int(math.ceil(xa - 0.5))), min(W, int(math.ceil(xb - 0.5)))
                for sx in range(a, b):
                    row[sx // ss] += 1
    k = 1.0 / (ss * ss)
    return [[min(1.0, c * k) for c in r] for r in cover]


def specimen(path, lines=("Umbrella Ella", "The Stolen Hour", "Start Game  Director's Cut", "ABCDEFGHIJKLM", "NOPQRSTUVWXYZ",
                          "abcdefghijklm nopqrstuvwxyz", "0123456789 .,:;!?'\"-()/%+&*#")):
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    from png import write_png
    table = {}
    for cps, contours, adv in all_glyphs():
        for cp in cps:
            table[cp] = (contours, adv)
    size, pad, lead = 96, 30, 1.25
    k = size / UPM
    w, h = 1700, int(pad * 2 + len(lines) * size * lead)
    polys = []
    for i, line in enumerate(lines):
        x, base = pad, pad + (i * lead + 0.85) * size
        for ch in line:
            contours, adv = table.get(ord(ch), table[0x20])
            for c in contours:
                polys.append([(x + px * k, base - py * k) for px, py in c])
            x += adv * k
    cov = raster(polys, w, h)
    ink, paper = (0x1D, 0x17, 0x13), (0xE6, 0xD8, 0xC0)
    rows = [[tuple(int(paper[j] + (ink[j] - paper[j]) * c) for j in range(3)) + (255,) for c in r] for r in cov]
    write_png(path, w, h, rows)


def main(argv):
    data = build_ttf()
    text = inl_text(data)
    if "--check" in argv:
        bad = []
        if not os.path.exists(TTF) or open(TTF, "rb").read() != data:
            bad.append(os.path.relpath(TTF, ROOT))
        if not os.path.exists(INL) or open(INL, encoding="utf-8").read() != text:
            bad.append(os.path.relpath(INL, ROOT))
        for b in bad:
            print(f"build_font: {b} is stale; run Art/Source/UI/Font/build_font.py")
        print(f"build_font: {'FAIL' if bad else 'PASS'} bytes={len(data)}")
        return 1 if bad else 0
    with open(TTF, "wb") as fh:
        fh.write(data)
    os.makedirs(os.path.dirname(INL), exist_ok=True)
    with open(INL, "w", encoding="utf-8") as fh:
        fh.write(text)
    if "--specimen" in argv:
        specimen(SPECIMEN)
    print(f"build_font: wrote {len(data)} bytes, {len(all_glyphs())} glyphs")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
