"""Blender builder for the gothic skyline layer (ART scene/skyline), 3200x720, transparent, tiles left to right.

  Blender -b --factory-startup -P Art/Source/Scene/build_skyline.py -- --out <png> [--seed N] [--keep <dir>]

How it works: the town is built as flat meshes in Blender, one mesh per ink class (wall, roof, glow, line, rust,
hole, pane), each shape a little nearer the camera than the one before (painter's order). Two emission-only EEVEE
renders per layer write the classes as colour channels; the finish pass (numpy inside Blender) turns the class
weights into ink on paper: warm near-black walls with canvas grain and stone courses, lighter tiled roofs, muted
amber windows with dark mullions, etched frames, eave shadows, window bounce light, rim light and a ragged ink
edge. A hazier far layer sits behind the near one. Units are pixels, origin bottom-left, z up.
"""
import math
import os
import random
import sys
import tempfile

import bpy
import numpy as np

W, H, G = 3200, 720, 80          # frame and ground-band top
U = 0.01                         # Blender units per pixel
CLASSES = ("wall", "roof", "glow", "line", "rust", "hole", "pane", "lwall", "rock", "etch", "facet")
PASSES = ({"roof": (1, 0, 0), "glow": (0, 1, 0), "line": (0, 0, 1)},
          {"rust": (1, 0, 0), "hole": (0, 1, 0), "pane": (0, 0, 1)},
          {"lwall": (1, 0, 0), "rock": (0, 1, 0), "etch": (0, 0, 1)},
          {"facet": (1, 0, 0)})


# ---------------------------------------------------------------- geometry kit
class Kit:
    def __init__(self, rnd, lit=0.3, sx=1.0, sz=1.0, dx=0.0, dz=0.0):
        self.rnd, self.lit, self.n, self.geo = rnd, lit, 0, {}
        self.sx, self.sz, self.dx, self.dz = sx, sz, dx, dz

    def _mesh(self, cls):
        self.n += 1
        return self.geo.setdefault(cls, ([], [])) + (-self.n * 2e-4,)

    def add(self, cls, pts):
        v, f, y = self._mesh(cls)
        i0 = len(v)
        v.extend(((x * self.sx + self.dx) * U, y, (z * self.sz + self.dz) * U) for x, z in pts)
        f.append(tuple(range(i0, i0 + len(pts))))

    def rect(self, cls, x0, z0, x1, z1):
        self.add(cls, [(x0, z0), (x0, z1), (x1, z1), (x1, z0)])

    def stroke(self, cls, pts, wd, jit=0.0):
        r = self.rnd
        if jit:
            pts = [(x + r.uniform(-jit, jit), z + r.uniform(-jit, jit)) for x, z in pts]
        v, f, y = self._mesh(cls)
        hw = wd / 2
        for (xa, za), (xb, zb) in zip(pts, pts[1:]):
            ddx, ddz = xb - xa, zb - za
            ln = math.hypot(ddx, ddz) or 1.0
            nx, nz, ex, ez = -ddz / ln * hw, ddx / ln * hw, ddx / ln * hw * 0.6, ddz / ln * hw * 0.6
            i0 = len(v)
            for (px, pz) in ((xa - ex + nx, za - ez + nz), (xb + ex + nx, zb + ez + nz),
                             (xb + ex - nx, zb + ez - nz), (xa - ex - nx, za - ez - nz)):
                v.append(((px * self.sx + self.dx) * U, y, (pz * self.sz + self.dz) * U))
            f.append((i0, i0 + 1, i0 + 2, i0 + 3))

    def disc(self, cls, cx, cz, r, n=28):
        self.add(cls, [(cx + r * math.cos(2 * math.pi * i / n), cz + r * math.sin(2 * math.pi * i / n)) for i in range(n)])

    def ring(self, cls, cx, cz, r, wd, n=28):
        self.stroke(cls, [(cx + r * math.cos(2 * math.pi * i / n), cz + r * math.sin(2 * math.pi * i / n))
                          for i in range(n + 1)], wd)


def arch_pts(cx, z0, w, h, n=7):
    """Pointed (two-centred) arch, convex."""
    zs = z0 + max(h - 0.95 * w, h * 0.35)
    rise = z0 + h - zs
    pts = [(cx - w / 2, z0), (cx - w / 2, zs)]
    for i in range(1, n):
        a = math.pi - (math.pi / 3) * i / n
        pts.append((cx + w / 2 + w * math.cos(a), zs + rise * math.sin(a) / 0.866))
    left = pts[1:]
    pts.append((cx, z0 + h))
    pts += [(2 * cx - x, z) for x, z in reversed(left)]
    pts.append((cx + w / 2, z0))
    return pts


def round_pts(cx, z0, w, h, n=12):
    zs = z0 + h - w / 2
    return ([(cx - w / 2, z0)] + [(cx - w / 2 * math.cos(math.pi * i / n), zs + w / 2 * math.sin(math.pi * i / n))
                                  for i in range(n + 1)] + [(cx + w / 2, z0)])


# ---------------------------------------------------------------- ornaments
def window(k, cx, z0, w, h, lit=None, rounded=False, frame=True):
    shape = round_pts if rounded else arch_pts
    lit = (k.rnd.random() < k.lit) if lit is None else lit
    if frame:
        k.add("line", shape(cx, z0 - 1.0, w + 3.0, h + 2.6))
    k.add("glow" if lit else "pane", shape(cx, z0, w, h))
    nb = 1 if w < 9 else (2 if w < 16 else 3)
    for i in range(1, nb + 1):
        x = cx - w / 2 + w * i / (nb + 1)
        top = z0 + h - (0.9 * w) * (abs(x - cx) / (w / 2)) ** 1.3 - 1.0
        k.stroke("wall", [(x, z0), (x, top)], 1.25)
    if h > 17:
        k.stroke("wall", [(cx - w / 2, z0 + h * 0.46), (cx + w / 2, z0 + h * 0.46)], 1.1)
    if w >= 13 and not rounded:      # tracery: foiled circle in the head, bars springing to it
        zc = z0 + h - 0.62 * w
        k.ring("wall", cx, zc, w * 0.17, 1.2, 12)
        k.stroke("wall", [(cx - w / 2, zc - w * 0.3), (cx, zc - w * 0.02), (cx + w / 2, zc - w * 0.3)], 1.0)
    k.stroke("line", [(cx - w / 2 - 2.6, z0 - 1.6), (cx + w / 2 + 2.6, z0 - 1.6)], 1.7)


def finial(k, cx, z, s=1.0, cross=True):
    k.stroke("wall", [(cx, z - 2), (cx, z + 15 * s)], 1.5)
    k.add("wall", [(cx - 2.6 * s, z + 5 * s), (cx, z + 9 * s), (cx + 2.6 * s, z + 5 * s), (cx, z + 2 * s)])
    if cross:
        k.stroke("wall", [(cx - 3.6 * s, z + 12 * s), (cx + 3.6 * s, z + 12 * s)], 1.3)


def chimney(k, cx, z0, ztop, w=7.0):
    r = k.rnd
    k.rect("wall", cx - w / 2, z0, cx + w / 2, ztop)
    k.stroke("line", [(cx + w / 2 - 1.2, z0 + 3), (cx + w / 2 - 1.2, ztop - 3)], 0.8)
    k.rect("wall", cx - w / 2 - 1.8, ztop - 2, cx + w / 2 + 1.8, ztop + 2.2)
    k.stroke("line", [(cx - w / 2 - 1.8, ztop + 2.4), (cx + w / 2 + 1.8, ztop + 2.4)], 0.8)
    for px in ((cx,) if w < 8 else (cx - w * 0.24, cx + w * 0.24)):
        ph = r.uniform(5, 9)
        k.rect("wall", px - 1.7, ztop + 2, px + 1.7, ztop + 2 + ph)
        k.rect("wall", px - 2.4, ztop + 1 + ph, px + 2.4, ztop + 2.6 + ph)


def cresting(k, x0, x1, z, hh=6.0):
    """Iron ridge cresting: a rail on little posts with knobs."""
    k.stroke("wall", [(x0, z + hh), (x1, z + hh)], 1.0)
    n = max(2, int((x1 - x0) // 5.5))
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        k.stroke("wall", [(x, z - 1), (x, z + hh + (2.6 if i % 2 == 0 else 0.8))], 0.9)


def balustrade(k, x0, x1, z, hh=8.0):
    k.stroke("wall", [(x0, z + hh), (x1, z + hh)], 1.6)
    k.stroke("line", [(x0, z + hh + 1.2), (x1, z + hh + 1.2)], 0.6)
    n = max(2, int((x1 - x0) // 4.6))
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        k.stroke("wall", [(x, z - 1), (x, z + hh)], 1.5 if i % 6 == 0 else 0.9)
        if i % 6 == 0:
            k.rect("wall", x - 1.8, z + hh, x + 1.8, z + hh + 3.4)


def dormer(k, cx, z, w=13.0, lit=None):
    hh = w * 0.95
    k.add("roof", [(cx - w / 2 - 3, z + hh - 1), (cx, z + hh + w * 0.78 + 3), (cx + w / 2 + 3, z + hh - 1)])
    k.rect("lwall", cx - w / 2, z, cx + w / 2, z + hh)
    k.add("lwall", [(cx - w / 2 - 0.8, z + hh - 0.5), (cx, z + hh + w * 0.72), (cx + w / 2 + 0.8, z + hh - 0.5)])
    k.stroke("line", [(cx - w / 2 - 2.6, z + hh - 0.5), (cx, z + hh + w * 0.76), (cx + w / 2 + 2.6, z + hh - 0.5)], 0.9)
    window(k, cx, z + 2.5, w * 0.5, hh * 0.92, lit)


def spire(k, cx, base, w, hh, lancet=True, crockets=True, facet=1):
    """Slender spire: flared foot, lighter facet on one side, crockets up both edges, lancet lights, finial."""
    k.rect("wall", cx - w / 2 - 2.5, base - 4, cx + w / 2 + 2.5, base + 1.5)
    k.stroke("line", [(cx - w / 2 - 2.5, base + 1.8), (cx + w / 2 + 2.5, base + 1.8)], 0.8)
    k.add("wall", [(cx - w / 2, base), (cx - w * 0.18, base + hh * 0.5), (cx, base + hh), (cx + w * 0.18, base + hh * 0.5),
                   (cx + w / 2, base)])
    if facet:
        k.add("roof", [(cx + facet * w * 0.07, base + 2), (cx + facet * w * 0.02, base + hh * 0.9),
                       (cx + facet * w * 0.15, base + hh * 0.5), (cx + facet * (w / 2 - 1.5), base + 2)])
    if crockets:
        n = max(3, int(hh // 13))
        for i in range(1, n):
            t = i / n
            for s in (-1, 1):
                half = (w / 2) * (1 - t) if t < 0.5 else (w * 0.18) * (1 - t) / 0.5
                if t < 0.5:
                    half = w / 2 + (w * 0.18 - w / 2) * (t / 0.5)
                ex, ez = cx + s * half, base + hh * t
                k.add("wall", [(ex - s * 0.5, ez - 2.0), (ex + s * 3.2, ez + 1.2), (ex - s * 0.5, ez + 2.6)])
    if lancet and w > 16:
        for s in ((-1, 1) if w > 30 else (0,)):
            lx = cx + s * w * 0.17
            lw, lh = max(3.0, w * 0.11), hh * 0.2
            k.add("line", arch_pts(lx, base + hh * 0.07 - 0.8, lw + 2.2, lh + 2.2))
            k.add("hole" if k.rnd.random() < 0.6 else "pane", arch_pts(lx, base + hh * 0.07, lw, lh))
    finial(k, cx, base + hh - 1, 1.0 + min(0.5, w / 80))


def pinnacle(k, cx, z0, w, hh):
    k.rect("wall", cx - w / 2, z0 - 30, cx + w / 2, z0)
    k.rect("wall", cx - w / 2 - 1.2, z0 - 2.5, cx + w / 2 + 1.2, z0)
    spire(k, cx, z0, w, hh, lancet=False, crockets=hh > 26, facet=0)


def clock(k, cx, cz, r):
    k.disc("line", cx, cz, r + 3.0)
    k.disc("wall", cx, cz, r + 1.4)
    k.disc("glow", cx, cz, r)
    k.ring("wall", cx, cz, r * 0.74, 0.9)
    for i in range(12):
        a = 2 * math.pi * i / 12
        k.stroke("wall", [(cx + r * 0.76 * math.cos(a), cz + r * 0.76 * math.sin(a)),
                          (cx + r * 0.97 * math.cos(a), cz + r * 0.97 * math.sin(a))], 1.5 if i % 3 == 0 else 0.9)
    ha, ma = k.rnd.uniform(0, 6.28), k.rnd.uniform(0, 6.28)
    k.stroke("wall", [(cx, cz), (cx + r * 0.45 * math.cos(ha), cz + r * 0.45 * math.sin(ha))], 1.9)
    k.stroke("wall", [(cx, cz), (cx + r * 0.68 * math.cos(ma), cz + r * 0.68 * math.sin(ma))], 1.3)
    k.disc("wall", cx, cz, 1.9, 10)


def rose(k, cx, cz, r):
    k.disc("line", cx, cz, r + 3.2)
    k.disc("wall", cx, cz, r + 1.5)
    k.disc("glow", cx, cz, r)
    k.ring("wall", cx, cz, r * 0.42, 1.3)
    k.disc("wall", cx, cz, r * 0.13, 10)
    for i in range(12):
        a = 2 * math.pi * i / 12
        k.stroke("wall", [(cx + r * 0.13 * math.cos(a), cz + r * 0.13 * math.sin(a)),
                          (cx + r * math.cos(a), cz + r * math.sin(a))], 1.15)
        b = a + math.pi / 12
        k.ring("wall", cx + r * 0.76 * math.cos(b), cz + r * 0.76 * math.sin(b), r * 0.14, 0.9, 10)


# ---------------------------------------------------------------- buildings
def win_rows(k, x0, x1, z0, z1, ww=None, course=True):
    """Storeys of framed windows on a wall face between x0..x1, from z0 up to z1."""
    r = k.rnd
    ww = ww or r.choice((10.0, 11.0, 13.0, 14.0))
    wh = ww * r.uniform(1.9, 2.5)
    storey = wh + r.uniform(13, 19)
    ncol = max(1, int((x1 - x0 - 4) // (ww + r.uniform(8, 13))))
    nrow = int((z1 - z0 - 5) // storey)
    for row in range(nrow):
        zz = z0 + 9 + row * storey
        skip = r.randrange(ncol) if (ncol > 2 and r.random() < 0.3) else -1
        for c in range(ncol):
            if c != skip:
                window(k, x0 + (c + 0.5) * (x1 - x0) / ncol, zz, ww, wh)
        if course and row < nrow - 1:
            k.stroke("line", [(x0 + 1, zz + storey - 6.5), (x1 - 1, zz + storey - 6.5)], 0.7)
    return nrow


def quoins(k, x0, x1, z0, z1):
    """Corner stones: short etched ticks up both edges of a face."""
    z, i = z0, 0
    while z < z1:
        ln = 5.0 if i % 2 else 2.8
        k.stroke("etch", [(x0 + 0.6, z), (x0 + 0.6 + ln, z)], 0.8)
        k.stroke("etch", [(x1 - 0.6 - ln, z), (x1 - 0.6, z)], 0.8)
        z, i = z + 5.5, i + 1


def gable_house(k, x, w, he, rh, side=0, sl=0.0):
    """Gable-front house; `side` (-1/+1) adds a wing running sideways under its own roof plane."""
    r = k.rnd
    if side:
        a0, a1 = (x + w - 2, x + w + sl) if side > 0 else (x - sl, x + 2)
        hw = he - r.uniform(0, 14)
        rw = rh * r.uniform(0.7, 0.92)
        k.rect("wall", a0, 0, a1, hw)
        if side > 0:
            roofp = [(x + w * 0.5, hw + rw), (a1 - rw * 0.35, hw + rw), (a1 + 4, hw - 1.5), (x + w * 0.5, hw - 1.5)]
        else:
            roofp = [(x + w * 0.5, hw + rw), (a0 + rw * 0.35, hw + rw), (a0 - 4, hw - 1.5), (x + w * 0.5, hw - 1.5)]
        k.add("roof", roofp)
        k.stroke("line", [(roofp[2][0], hw - 1.5), (x + w * 0.5, hw - 1.5)], 1.2)
        k.stroke("line", [roofp[0], roofp[1]], 0.9)
        if sl > 46 and r.random() < 0.7:
            cresting(k, min(roofp[0][0], roofp[1][0]) + 6, max(roofp[0][0], roofp[1][0]) - 4, hw + rw, 5.0)
        win_rows(k, a0 + 4, a1 - 4, G - 4, hw - 3)
        nd = int(sl // 30)
        for i in range(nd):
            if r.random() < 0.8:
                dormer(k, (a0 + (i + 0.5) * (a1 - a0) / nd) + side * 5, hw + 3, r.uniform(11, 14))
        cx = a1 - rw * 0.35 - r.uniform(4, 12) if side > 0 else a0 + rw * 0.35 + r.uniform(4, 12)
        chimney(k, cx, hw + rw * 0.5, hw + rw + r.uniform(14, 26), r.choice((6.5, 9.0)))
    k.add("roof", [(x - 6.5, he - 3), (x + w / 2, he + rh + 5.5), (x + w + 6.5, he - 3)])
    k.rect("lwall", x, 0, x + w, he + 1)
    k.add("lwall", [(x - 1.5, he - 0.5), (x + w / 2, he + rh), (x + w + 1.5, he - 0.5)])
    k.stroke("line", [(x - 5.5, he - 2.2), (x + w / 2, he + rh + 4.6), (x + w + 5.5, he - 2.2)], 0.9)
    quoins(k, x, x + w, G - 6, he - 3)
    k.stroke("line", [(x + 1, he - 1), (x + w - 1, he - 1)], 0.7)
    win_rows(k, x + 3, x + w - 3, G - 4, he - 3)
    if rh > 26:
        if r.random() < 0.5:
            window(k, x + w / 2, he + rh * 0.16, min(11.0, w * 0.2), rh * 0.36)
        else:
            cz, rr = he + rh * 0.34, min(6.5, rh * 0.14)
            k.disc("line", x + w / 2, cz, rr + 1.6, 14)
            k.disc("glow" if r.random() < k.lit else "pane", x + w / 2, cz, rr, 14)
            k.stroke("wall", [(x + w / 2 - rr, cz), (x + w / 2 + rr, cz)], 1.0)
            k.stroke("wall", [(x + w / 2, cz - rr), (x + w / 2, cz + rr)], 1.0)
    finial(k, x + w / 2, he + rh + 4, 0.8, cross=r.random() < 0.4)


def hip_house(k, x, w, he, rh, mansard=False):
    r = k.rnd
    k.rect("wall", x, 0, x + w, he + 1)
    inset = rh * (0.28 if mansard else 0.55)
    k.add("roof", [(x - 4.5, he - 1.5), (x + inset, he + rh), (x + w - inset, he + rh), (x + w + 4.5, he - 1.5)])
    k.stroke("line", [(x - 4.5, he - 1.2), (x + w + 4.5, he - 1.2)], 1.3)
    k.stroke("line", [(x + inset, he + rh), (x + w - inset, he + rh)], 0.9)
    if w - 2 * inset > 16:
        cresting(k, x + inset + 2, x + w - inset - 2, he + rh, 5.5)
    win_rows(k, x + 3, x + w - 3, G - 4, he - 3)
    quoins(k, x, x + w, G - 6, he - 3)
    nd = max(1, int(w // 34))
    for i in range(nd):
        if r.random() < 0.85:
            dormer(k, x + (i + 0.5) * w / nd, he + 2.5, r.uniform(11, 15))
    for s in (0, 1):
        if r.random() < 0.75:
            cx = x + inset + 5 if s == 0 else x + w - inset - 5
            chimney(k, cx, he + rh * 0.6, he + rh + r.uniform(13, 28), r.choice((6.5, 9.0)))


def tower_house(k, cx, w, he, rh):
    r = k.rnd
    k.rect("wall", cx - w / 2, 0, cx + w / 2, he)
    k.rect("wall", cx - w / 2 - 2.5, he - 5, cx + w / 2 + 2.5, he + 1)
    k.stroke("line", [(cx - w / 2 - 2.5, he + 1.2), (cx + w / 2 + 2.5, he + 1.2)], 0.9)
    k.add("rust" if r.random() < 0.3 else "roof", [(cx - w / 2 - 3.5, he + 1), (cx - w * 0.12, he + rh * 0.62), (cx, he + rh),
                                                  (cx + w * 0.12, he + rh * 0.62), (cx + w / 2 + 3.5, he + 1)])
    win_rows(k, cx - w / 2 + 2, cx + w / 2 - 2, G - 4, he - 8, ww=min(10.0, w * 0.34), course=True)
    finial(k, cx, he + rh - 1, 0.9)


def arcade(k, x0, x1, zdeck, span=44.0, rail=True):
    """Viaduct on round arches; the openings are cut out of the mass. Voussoir rings, spandrel roundels, lamps."""
    n = max(1, round((x1 - x0) / span))
    sw = (x1 - x0) / n
    k.rect("wall", x0, 0, x1, zdeck)
    for i in range(n):
        cx = x0 + (i + 0.5) * sw
        k.add("etch", round_pts(cx, -2, sw - 8.5, zdeck - 13, 14))
        k.add("wall", round_pts(cx, -2, sw - 11, zdeck - 14.5, 14))
        k.add("hole", round_pts(cx, -2, sw - 14, zdeck - 16, 14))
        k.stroke("etch", [(cx, zdeck - 16), (cx, zdeck - 5)], 1.8)                             # keystone
    for i in range(n + 1):
        px = x0 + i * sw
        k.rect("wall", px - 8.5, zdeck - sw * 0.5 - 13, px + 8.5, zdeck - sw * 0.5 - 9.5)   # impost blocks
        k.stroke("etch", [(px - 8.5, zdeck - sw * 0.5 - 9.2), (px + 8.5, zdeck - sw * 0.5 - 9.2)], 0.8)
        k.stroke("etch", [(px - 5, G - 4), (px - 5, zdeck - sw * 0.5 - 14)], 0.6)
        k.stroke("etch", [(px + 5, G - 4), (px + 5, zdeck - sw * 0.5 - 14)], 0.6)
        if 0 < i < n:
            k.disc("etch", px, zdeck - 9, 4.4, 12)                                           # spandrel roundel
            k.disc("pane", px, zdeck - 9, 3.0, 12)
    k.rect("wall", x0 - 2, zdeck - 1, x1 + 2, zdeck + 3.5)
    k.stroke("line", [(x0 - 2, zdeck + 3.6), (x1 + 2, zdeck + 3.6)], 0.9)
    k.stroke("etch", [(x0, zdeck - 3.5), (x1, zdeck - 3.5)], 0.7)
    if rail:
        balustrade(k, x0, x1, zdeck + 3.5)
    for i in range(n + 1):                                                                    # lamp standards
        px = x0 + i * sw
        k.stroke("wall", [(px, zdeck + 3), (px, zdeck + 25)], 1.5)
        k.stroke("wall", [(px - 3, zdeck + 25), (px + 3, zdeck + 25)], 1.2)
        k.disc("glow", px, zdeck + 28.4, 2.7, 10)
        k.add("wall", [(px - 3.4, zdeck + 31), (px, zdeck + 35.5), (px + 3.4, zdeck + 31)])


def clock_tower(k, cx, w, he):
    r = k.rnd
    for s in (-1, 1):                               # stepped corner buttresses
        k.rect("wall", cx + s * w / 2 - 4, 0, cx + s * w / 2 + 4, he * 0.62)
        k.add("wall", [(cx + s * w / 2 - 4, he * 0.62), (cx + s * (w / 2 - 2), he * 0.62 + 12), (cx + s * w / 2 + 4, he * 0.62)])
    k.rect("wall", cx - w / 2, 0, cx + w / 2, he)
    for f in (0.42, 0.66, 0.8):
        k.stroke("line", [(cx - w / 2 - 1, he * f), (cx + w / 2 + 1, he * f)], 1.0)
    window(k, cx, G + 26, w * 0.34, he * 0.42 - G - 36, lit=False)
    for s in (-1, 1):                               # belfry lights
        k.add("line", arch_pts(cx + s * w * 0.2, he * 0.45 - 1, w * 0.2 + 2.4, he * 0.19 + 2.4))
        k.add("hole" if s < 0 or r.random() < 0.5 else "pane", arch_pts(cx + s * w * 0.2, he * 0.45, w * 0.2, he * 0.19))
        for j in range(1, 5):
            zz = he * 0.45 + he * 0.15 * j / 5
            k.stroke("wall", [(cx + s * w * 0.2 - w * 0.1, zz), (cx + s * w * 0.2 + w * 0.1, zz)], 1.2)
    clock(k, cx, he * 0.89 - w * 0.2, w * 0.3)
    k.rect("wall", cx - w / 2 - 4, he - 4, cx + w / 2 + 4, he + 3)                 # corbelled cornice
    k.stroke("line", [(cx - w / 2 - 4, he + 3.2), (cx + w / 2 + 4, he + 3.2)], 1.0)
    for i in range(int(w // 5) + 2):
        k.rect("wall", cx - w / 2 - 3 + i * 5.2, he - 8, cx - w / 2 - 0.5 + i * 5.2, he - 4)
    for s in (-1, 1):
        pinnacle(k, cx + s * (w / 2 + 0.5), he + 3 + 16, 7.5, 38)
    rh = w * 2.1
    k.add("roof", [(cx - w / 2 - 1, he + 3), (cx - w * 0.2, he + 3 + rh * 0.55), (cx, he + 3 + rh), (cx + w * 0.2, he + 3 + rh * 0.55),
                   (cx + w / 2 + 1, he + 3)])
    k.add("wall", [(cx - w / 2 - 1, he + 3), (cx - w * 0.2, he + 3 + rh * 0.55), (cx, he + 3 + rh), (cx - w * 0.04, he + 3)])
    dormer(k, cx + w * 0.02, he + 5, w * 0.3, lit=False)
    finial(k, cx, he + 2 + rh, 1.5)


def domed_hall(k, cx, w, he):
    r = k.rnd
    k.rect("wall", cx - w / 2, 0, cx + w / 2, he)
    k.stroke("line", [(cx - w / 2 - 3, he), (cx + w / 2 + 3, he)], 1.4)
    win_rows(k, cx - w / 2 + 4, cx + w / 2 - 4, G - 4, he - 2, ww=12.0)
    balustrade(k, cx - w / 2 - 2, cx + w / 2 + 2, he + 0.5, 7)
    dr, dh = w * 0.31, w * 0.2                      # drum
    k.rect("wall", cx - dr, he, cx + dr, he + dh)
    for i in range(5):
        window(k, cx - dr + (i + 0.5) * 2 * dr / 5, he + 5, dr * 0.2, dh - 10, lit=(i in (1, 3)) or r.random() < 0.4, rounded=True)
    k.rect("wall", cx - dr - 3, he + dh - 1, cx + dr + 3, he + dh + 3.5)
    k.stroke("line", [(cx - dr - 3, he + dh + 3.6), (cx + dr + 3, he + dh + 3.6)], 1.0)
    zb, rr = he + dh + 3.5, dr + 1
    n = 22
    k.add("roof", [(cx - rr * math.cos(math.pi * i / n), zb + rr * 0.86 * math.sin(math.pi * i / n) ** 0.85) for i in range(n + 1)])
    for j in range(1, 8):                           # ribs
        t = -1 + 2 * j / 8
        k.stroke("wall" if j % 2 else "line", [(cx + rr * t * math.sin(math.pi * i / 2 / n) ** 0.9 * 1.0,
                                               zb + rr * 0.86 * math.cos(math.pi * i / 2 / n) ** 0.85) for i in range(n + 1)], 1.0)
    for f in (0.3, 0.58):
        hw = rr * math.cos(math.asin(min(1.0, f)))
        k.stroke("wall", [(cx - hw, zb + rr * 0.86 * f), (cx + hw, zb + rr * 0.86 * f)], 0.9)
    zl = zb + rr * 0.86 - 2                         # lantern
    k.rect("wall", cx - 6, zl, cx + 6, zl + 15)
    k.add("glow", round_pts(cx, zl + 3, 4.6, 10, 8))
    k.rect("wall", cx - 8, zl + 14, cx + 8, zl + 17)
    k.add("roof", [(cx - 7 * math.cos(math.pi * i / 10), zl + 17 + 8 * math.sin(math.pi * i / 10)) for i in range(11)])
    finial(k, cx, zl + 24, 1.2)


def conservatory(k, cx, w, he):
    """Glass house: a low wall and an iron-ribbed dome you can see through."""
    k.rect("wall", cx - w / 2, 0, cx + w / 2, he)
    for i in range(int(w // 11)):
        window(k, cx - w / 2 + (i + 0.5) * w / int(w // 11), G + 4, 6.0, he - G - 12, lit=False, rounded=True, frame=False)
    k.rect("wall", cx - w / 2 - 2, he - 1, cx + w / 2 + 2, he + 3)
    k.stroke("line", [(cx - w / 2 - 2, he + 3.2), (cx + w / 2 + 2, he + 3.2)], 0.9)
    rr, n = w / 2 - 2, 20
    k.add("pane", [(cx - rr * math.cos(math.pi * i / n), he + 3 + rr * 0.92 * math.sin(math.pi * i / n)) for i in range(n + 1)])
    for j in range(0, 11):
        t = -1 + 2 * j / 10
        k.stroke("wall", [(cx + rr * t * math.sin(math.pi * i / 2 / n), he + 3 + rr * 0.92 * math.cos(math.pi * i / 2 / n))
                          for i in range(n + 1)], 1.5 if j in (0, 5, 10) else 0.9)
    for f in (0.25, 0.5, 0.72, 0.9):
        hw = rr * math.cos(math.asin(f))
        k.stroke("wall", [(cx - hw, he + 3 + rr * 0.92 * f), (cx + hw, he + 3 + rr * 0.92 * f)], 1.0)
    k.rect("wall", cx - 4, he + 2 + rr * 0.92, cx + 4, he + 9 + rr * 0.92)
    finial(k, cx, he + 8 + rr * 0.92, 1.2)


def cathedral(k, cx):
    r = k.rnd
    nw, nh, gh = 176.0, 304.0, 116.0                # nave width, eave height, gable rise
    for s in (-1, 1):                               # flying buttresses, drawn first so the nave covers their heads
        for j, (reach, top) in enumerate(((178.0, 262.0), (236.0, 196.0))):
            px = cx + s * reach
            k.rect("wall", px - 6.5, 0, px + 6.5, top - 26)
            pinnacle(k, px, top + 4, 9.5, 44)
            x1, z1 = cx + s * (nw / 2 - 4), top + 78
            pts = [(px + (x1 - px) * t / 14.0, top - 34 + (z1 - top + 34) * math.sin(math.pi * t / 28.0) ** 1.0) for t in range(15)]
            k.stroke("wall", pts, 6.5)
            k.stroke("line", [(x, z + 3.4) for x, z in pts], 0.8)
            for t in range(2, 13, 2):               # openwork: little posts under a straight coping
                k.stroke("wall", [(pts[t][0], pts[t][1]), (pts[t][0], pts[t][1] + 9)], 1.2)
            k.stroke("wall", [(pts[1][0], pts[1][1] + 9), (pts[13][0], pts[13][1] + 9)], 1.3)
    for s in (-1, 1):                               # aisles with lean-to roofs
        ax0, ax1 = cx + s * nw / 2, cx + s * (nw / 2 + 62)
        k.rect("wall", min(ax0, ax1), 0, max(ax0, ax1), 200)
        k.add("roof", [(ax0, 244), (ax1 + s * 4, 198), (ax0, 198)])
        k.stroke("line", [(ax0, 198.5), (ax1 + s * 4, 198.5)], 1.1)
        for i in range(2):
            window(k, min(ax0, ax1) + 17 + i * 28, G + 40, 13.0, 62.0)
    for s in (-1, 1):                               # west towers
        tx, tw, th = cx + s * (nw / 2 - 6), 44.0, 356.0
        k.rect("wall", tx - tw / 2, 0, tx + tw / 2, th)
        for f in (0.5, 0.72, 0.985):
            k.stroke("line", [(tx - tw / 2 - 1.5, th * f), (tx + tw / 2 + 1.5, th * f)], 1.0)
        window(k, tx, th * 0.52 + 6, 9.0, 44.0, lit=False)
        k.add("line", arch_pts(tx, th * 0.74 - 1, 12.4, 62.4))
        k.add("hole", arch_pts(tx, th * 0.74, 10.0, 60.0))
        k.stroke("wall", [(tx, th * 0.74), (tx, th * 0.74 + 52)], 1.4)
        for j in range(1, 7):
            k.stroke("wall", [(tx - 5, th * 0.74 + 7.5 * j), (tx + 5, th * 0.74 + 7.5 * j)], 1.1)
        k.rect("wall", tx - tw / 2 - 3, th - 3, tx + tw / 2 + 3, th + 3)
        for q in (-1, 1):
            pinnacle(k, tx + q * (tw / 2 - 1), th + 3 + 14, 8.0, 40)
        spire(k, tx, th + 3, tw - 8, 150.0, facet=s)
    fz = nh + gh - 26                                # crossing fleche behind the gable
    k.rect("wall", cx - 21, nh, cx + 21, fz + 78)
    for q in (-1, 1):
        k.add("line", arch_pts(cx + q * 9.5, fz + 26 - 1, 10.4, 44.4))
        k.add("hole", arch_pts(cx + q * 9.5, fz + 26, 8.0, 42.0))
        pinnacle(k, cx + q * 21, fz + 78 + 12, 7.5, 36)
    k.rect("wall", cx - 24, fz + 76, cx + 24, fz + 81)
    k.stroke("line", [(cx - 24, fz + 81.2), (cx + 24, fz + 81.2)], 0.9)
    spire(k, cx, fz + 81, 38.0, 176.0, facet=1)
    k.add("roof", [(cx - nw / 2 - 5, nh - 3), (cx, nh + gh + 6), (cx + nw / 2 + 5, nh - 3)])   # nave gable
    k.rect("lwall", cx - nw / 2, 0, cx + nw / 2, nh + 1)
    k.add("lwall", [(cx - nw / 2 + 2, nh), (cx, nh + gh - 2), (cx + nw / 2 - 2, nh)])
    quoins(k, cx - nw / 2, cx + nw / 2, G, nh - 4)
    k.stroke("line", [(cx - nw / 2 - 4, nh - 2), (cx, nh + gh + 5), (cx + nw / 2 + 4, nh - 2)], 1.0)
    for i in range(1, 9):                            # crockets up the gable
        for s in (-1, 1):
            t = i / 9.0
            ex, ez = cx + s * (nw / 2 + 5) * (1 - t), nh - 3 + (gh + 9) * t
            k.add("wall", [(ex, ez - 2.5), (ex + s * 4.5, ez + 3.5), (ex - s * 1.5, ez + 3)])
    finial(k, cx, nh + gh + 4, 1.6)
    rose(k, cx, nh + 6, 31.0)
    k.stroke("line", [(cx - nw / 2 + 24, nh - 44), (cx + nw / 2 - 24, nh - 44)], 1.0)
    for dxw, ww, wh, lit in ((-50, 17.0, 104.0, True), (0, 21.0, 124.0, True), (50, 17.0, 104.0, True)):
        window(k, cx + dxw, G + 62, ww, wh, lit=lit)
    k.add("line", arch_pts(cx, 0, 36.0, G + 34.0))   # portal
    k.add("wall", arch_pts(cx, 0, 31.0, G + 30.0))
    k.add("rust", arch_pts(cx, 0, 22.0, G + 23.0))
    k.stroke("wall", [(cx, 0), (cx, G + 20)], 1.6)
    for s in (-1, 1):                               # niche lights in the gable
        window(k, cx + s * 44, nh + 4, 7.0, 22.0, lit=False)
    window(k, cx, nh + 60, 9.0, 26.0, lit=False)


# ---------------------------------------------------------------- town layout
def taper(x):
    """Height factor: the town sinks to the ground band toward both tile edges, so the tile wraps."""
    e = min(x, W - x)
    return max(0.0, min(1.0, (e - 70) / 420.0))


def house_row(k, x0, x1, lo, hi, front, blocked=(), low=(), gappy=0.0):
    """A row of houses. `blocked` spans stay empty (landmarks, viaduct openings), `low` spans keep to cottages."""
    r = k.rnd
    x, base_lit = x0, k.lit
    while x < x1:
        t = taper(x)
        if t <= 0.02:
            x += 30
            continue
        f = 0.35 if any(a <= x <= b for a, b in low) else 1.0
        he = G + (lo + (hi - lo) * r.random()) * (0.45 + 0.55 * t) * f
        kind = r.random()
        w = r.uniform(46, 66) if kind < 0.4 else (r.uniform(62, 118) if kind < 0.8 else r.uniform(22, 34))
        side = (r.choice((-1, 1, 1)) if r.random() < 0.75 else 0) if kind < 0.4 else 0
        sl = r.uniform(34, 78) if side else 0
        hit = [b for a, b in blocked if x - 8 < b and x + w + sl + 8 > a]
        if hit:
            x = max(hit) + 8
            continue
        k.lit = base_lit * r.choice((0.15, 0.15, 0.4, 1.0, 2.3))      # households, not confetti: some dark, some all lit
        if kind < 0.4:
            gable_house(k, x + (sl if side < 0 else 0), w, he, w * r.uniform(0.62, 0.92), side, sl)
        elif kind < 0.8:
            hip_house(k, x, w, he, r.uniform(30, 52) * (0.7 + 0.3 * f), mansard=r.random() < 0.3)
        elif kind < 0.92 or front:
            tower_house(k, x + w / 2, w, he + r.uniform(20, 60) * t * f, w * r.uniform(1.5, 2.3))
        else:
            k.rect("wall", x, 0, x + w, he + 30)
            window(k, x + w / 2, he - 8, 8.0, 24.0, lit=False)
            spire(k, x + w / 2, he + 30, w, r.uniform(90, 150) * (0.5 + 0.5 * t), facet=r.choice((-1, 1)))
        x += w + sl + r.uniform(-8, 8) + (r.uniform(18, 70) if r.random() < gappy else 0)
    k.lit = base_lit


def ground(k):
    """The town stands on the key art's black rock band: flat-topped buttes with steep, notched sides. Each butte
    has a lit facet on its left flank and a few cleft lines; the band has the same height at both tile edges."""
    r = k.rnd
    edge = G + 34.0
    prof, x, z = [(0.0, edge), (r.uniform(30, 60), edge + 2)], 60.0, edge
    buttes = []
    while x < W - 150:
        e = max(0.0, 1 - min(x, W - x) / 170.0)                        # the band lifts only at the tile edges
        top = G - 2 + 34 * e + r.uniform(3, 20) * (1 + 0.8 * e)        # butte top
        low = G - 9 + 30 * e + r.uniform(-4, 5)                        # gully between buttes
        wd = r.uniform(70, 210)
        gap = r.uniform(14, 46)
        x0 = x + gap
        prof += [(x + gap * 0.45, low), (x0 - r.uniform(2, 6), low + (top - low) * 0.35), (x0, top - r.uniform(2, 5))]
        n = r.randint(1, 3)                                             # notches along the flat top
        for i in range(1, n + 1):
            nx = x0 + wd * i / (n + 1) + r.uniform(-8, 8)
            prof += [(nx - 3, top + r.uniform(-1.5, 1.5)), (nx, top - r.uniform(3, 9)), (nx + r.uniform(3, 7), top + r.uniform(-2, 3))]
        x1 = x0 + wd
        prof += [(x1, top + r.uniform(-1, 3)), (x1 + r.uniform(-5, 3), top - (top - low) * 0.5)]
        buttes.append((x0, x1, top, low))
        x = x1
    prof += [(W - 60, edge + 2), (W, edge)]
    prof.sort(key=lambda q: q[0])
    for a, b in zip(prof, prof[1:]):
        k.add("rock", [(a[0], -4), a, b, (b[0], -4)])
    for x0, x1, top, low in buttes:
        fw = r.uniform(14, 34)                                          # lit left flank
        k.add("facet", [(x0 + 1.5, top - 5), (x0 + fw, top - 7), (x0 + fw * r.uniform(0.5, 0.9), low - r.uniform(14, 40)),
                        (x0 - 2, low - r.uniform(4, 16))])
        for _ in range(r.randint(1, 2)):                                # clefts running down from the rim
            cx = r.uniform(x0 + fw, x1 - 6)
            cz = top - r.uniform(3, 8)
            k.stroke("etch", [(cx, cz), (cx + r.uniform(-3, 3), cz - r.uniform(10, 22)), (cx + r.uniform(-6, 6), cz - r.uniform(24, 46))], 0.8)
        k.stroke("etch", [(x0 + fw + 3, top - 9), (x1 - 8, top - 9 + r.uniform(-2, 2))], 0.7, jit=0.6)   # ledge under the rim


VIADUCTS = ((742, 1018, 192, 46), (2190, 2452, 176, 44), (1340, 1430, 152, 45))
LANDMARKS = ((585, 695), (1090, 1210), (1640, 2120), (2560, 2740), (292, 342))


def near_town(k):
    for x0, x1, deck, span in VIADUCTS:             # viaducts first: their arches cut only what is behind them
        arcade(k, x0, x1, deck, span)
    spans = tuple((a + 4, b - 4) for a, b, _, _ in VIADUCTS)
    house_row(k, 150, W - 150, 84, 150, front=False, blocked=spans + LANDMARKS, gappy=0.1)      # back row
    conservatory(k, 1150, 104, G + 62)
    clock_tower(k, 640, 58, 330)
    cathedral(k, 1880)
    domed_hall(k, 2650, 160, 232)
    k.rect("wall", 300, 0, 334, 250)                        # parish spire, left
    window(k, 317, 196, 9.0, 30.0, lit=False)
    spire(k, 317, 250, 34, 150, facet=-1)
    house_row(k, 110, W - 110, 48, 108, front=True, low=((1690, 2070), (1100, 1200)) + tuple((a - 40, b) for a, b in spans), gappy=0.06)   # front row
    ground(k)


def far_town(k):
    r = k.rnd
    open_ = tuple(((a + 190 + 6) / 0.86, (b + 190 - 6) / 0.86) for a, b, _, _ in VIADUCTS)   # keep the arches open to the sky
    house_row(k, 150, W - 150, 50, 125, front=False, blocked=open_, gappy=0.25)
    for cx in (210, 520, 905, 1560, 2100, 2460, 2880, 3020):
        if any(a - 8 < cx < b + 8 for a, b in open_):
            continue
        t = taper(cx)
        w = r.uniform(26, 40)
        he = G + r.uniform(120, 200) * (0.4 + 0.6 * t)
        k.rect("wall", cx - w / 2, 0, cx + w / 2, he)
        window(k, cx, he - 40, 8.0, 26.0, lit=False)
        spire(k, cx, he, w, r.uniform(100, 170) * (0.4 + 0.6 * t), facet=r.choice((-1, 1)))
    k.rect("rock", 0, -4, W, G)


# ---------------------------------------------------------------- Blender render
def setup_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            sc.render.engine = eng
            break
        except TypeError:
            continue
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = W, H, 100
    sc.render.film_transparent = True
    sc.render.filter_size = 1.0
    sc.view_settings.view_transform = "Standard"
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    try:
        sc.eevee.taa_render_samples = 24
    except AttributeError:
        pass
    cam = bpy.data.cameras.new("cam")
    cam.type, cam.ortho_scale, cam.clip_start, cam.clip_end = "ORTHO", W * U, 0.1, 100.0
    co = bpy.data.objects.new("cam", cam)
    sc.collection.objects.link(co)
    co.location, co.rotation_euler = (W * U / 2, -30, H * U / 2), (math.pi / 2, 0, 0)
    sc.camera = co
    mats = {}
    for c in CLASSES:
        m = bpy.data.materials.new(c)
        m.use_nodes = True
        nt = m.node_tree
        nt.nodes.clear()
        out, em = nt.nodes.new("ShaderNodeOutputMaterial"), nt.nodes.new("ShaderNodeEmission")
        nt.links.new(em.outputs[0], out.inputs[0])
        mats[c] = (m, em)
    return sc, mats


def render_layer(sc, mats, kit, tmp, tag):
    obs = []
    for c, (v, f) in kit.geo.items():
        me = bpy.data.meshes.new(c)
        me.from_pydata(v, [], f)
        ob = bpy.data.objects.new(c, me)
        sc.collection.objects.link(ob)
        ob.data.materials.append(mats[c][0])
        obs.append(ob)
    out = []
    for i, chan in enumerate(PASSES):
        for c, (m, em) in mats.items():
            em.inputs[0].default_value = (*chan.get(c, (0, 0, 0)), 1.0)
        sc.render.filepath = os.path.join(tmp, "%s_%d.png" % (tag, i))
        bpy.ops.render.render(write_still=True)
        img = bpy.data.images.load(sc.render.filepath)
        a = np.empty(W * H * 4, dtype=np.float32)
        img.pixels.foreach_get(a)
        bpy.data.images.remove(img)
        out.append(a.reshape(H, W, 4)[::-1].copy())
    for ob in obs:
        me = ob.data
        bpy.data.objects.remove(ob)
        bpy.data.meshes.remove(me)
    return out


# ---------------------------------------------------------------- finish pass (ink on paper)
def box(a, r, axis=None):
    """Box blur by cumulative sums (edge padded); both axes when axis is None."""
    for ax in ((0, 1) if axis is None else (axis,)):
        pad = [(0, 0)] * a.ndim
        pad[ax] = (r + 1, r)
        c = np.cumsum(np.pad(a, pad, mode="edge"), axis=ax, dtype=np.float64)
        n = a.shape[ax]
        hi = np.take(c, np.arange(2 * r + 1, 2 * r + 1 + n), axis=ax)
        lo = np.take(c, np.arange(0, n), axis=ax)
        a = ((hi - lo) / (2 * r + 1)).astype(np.float32)
    return a


def field(rng, cell, amp):
    gh, gw = H // cell + 3, W // cell + 3
    g = rng.uniform(-amp, amp, (gh, gw)).astype(np.float32)
    ys, xs = np.arange(H) / cell, np.arange(W) / cell
    y0, x0 = ys.astype(int), xs.astype(int)
    fy, fx = (ys - y0)[:, None].astype(np.float32), (xs - x0)[None, :].astype(np.float32)
    fy, fx = fy * fy * (3 - 2 * fy), fx * fx * (3 - 2 * fx)
    return ((g[y0][:, x0] * (1 - fx) + g[y0][:, x0 + 1] * fx) * (1 - fy)
            + (g[y0 + 1][:, x0] * (1 - fx) + g[y0 + 1][:, x0 + 1] * fx) * fy)


def shift_down(a, n):
    out = np.empty_like(a)
    out[n:], out[:n] = a[:-n], a[:1]
    return out


def lin(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def col(*rgb):
    return np.array(rgb, dtype=np.float32)[None, None, :] / 255.0


def finish(p1, p2, p3, p4, seed, far=False):
    rng = np.random.default_rng(seed)
    # hand wobble: one displacement field for both passes
    dx, dy = field(rng, 13, 0.5) + field(rng, 4, 0.15), field(rng, 13, 0.5) + field(rng, 4, 0.15)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    sy = np.clip((yy + dy).round().astype(int), 0, H - 1)
    sx = np.clip((xx + dx).round().astype(int), 0, W - 1)
    p1, p2, p3, p4 = p1[sy, sx], p2[sy, sx], p3[sy, sx], p4[sy, sx]
    roof, glow, line = (lin(p1[..., i]) for i in range(3))
    rust, hole, pane = (lin(p2[..., i]) for i in range(3))
    a = p1[..., 3] * (1 - hole)
    zz = H - yy
    lwall, rock, etch = (lin(p3[..., i]) for i in range(3))
    wall = np.clip(1 - roof - glow - line - rust - pane - lwall - rock - etch - lin(p4[..., 0]), 0, 1)
    # paper and ink textures
    white = rng.normal(0, 1, (H, W)).astype(np.float32)
    weave = (box(rng.normal(0, 1, (H, W)).astype(np.float32), 2, 1) + box(rng.normal(0, 1, (H, W)).astype(np.float32), 2, 0)) * 1.6
    mott = field(rng, 70, 1.0) + field(rng, 19, 0.7) + field(rng, 6, 0.45)
    patch = np.clip(field(rng, 26, 1.0) + field(rng, 9, 0.6) + field(rng, 3, 0.5) - 0.05, 0, 1)        # where the etcher bothered to draw
    # walls: warm near-black, stone courses that fade in and out, darker under the eaves, warm near lit windows
    courses = ((zz % 9.0) < 1.0).astype(np.float32)
    joints = (((xx + 8.0 * (np.floor(zz / 9.0) % 2)) % 16.0) < 1.0).astype(np.float32) * ((zz % 9.0) > 1.0)
    stone = np.maximum(courses, joints * 0.8) * patch
    vhatch = (((xx * 1.0 + zz * 0.5) % 5.0) < 1.0).astype(np.float32) * np.clip(field(rng, 30, 1.0) - 0.25, 0, 1)
    eave = np.clip(box(shift_down(roof + line * 0.5, 6), 3) * 1.5, 0, 1)
    bounce = np.clip(box(glow, 12) * 3.2, 0, 1) * (1 - np.clip(rock + lin(p4[..., 0]), 0, 1))
    c_wall = col(25, 20, 17) * (1 + 0.08 * (zz / H))[..., None] + stone[..., None] * col(18, 15, 12) + vhatch[..., None] * col(17, 14, 11)
    c_wall = c_wall * (1 - 0.32 * eave)[..., None] + bounce[..., None] * col(40, 25, 12)
    c_lwall = (col(37, 31, 26) * (1 + 0.08 * (zz / H))[..., None] + stone[..., None] * col(24, 20, 17) + vhatch[..., None] * col(12, 10, 8))
    c_lwall = c_lwall * (1 - 0.4 * eave)[..., None] + bounce[..., None] * col(46, 29, 14)
    h1 = (((xx + zz * 0.6) % 4.0) < 1.0).astype(np.float32) * np.clip(field(rng, 40, 1.0) + field(rng, 11, 0.5) - 0.35, 0, 1)
    h2 = (((xx * 0.5 - zz) % 4.5) < 1.0).astype(np.float32) * np.clip(field(rng, 34, 1.0) + field(rng, 9, 0.5) - 0.45, 0, 1)
    c_rock = col(23, 18, 15) * (1 + 0.06 * mott)[..., None] + (h1 + h2)[..., None] * col(26, 21, 17)
    c_etch = col(78, 67, 57) * (0.75 + 0.4 * patch)[..., None]
    facet = lin(p4[..., 0])
    c_facet = col(27, 22, 18) + ((((xx * 0.7 + zz) % 3.6) < 1.0).astype(np.float32) * (0.6 + 0.5 * patch))[..., None] * col(40, 34, 28)
    # roofs: lighter umber, diamond slates, each slate lit along its upper edges
    p = 6.0
    wx, wz = xx + field(rng, 14, 2.2), zz + field(rng, 14, 2.2)      # slates laid by hand: the courses waver
    d1, d2 = (wx + wz) % p, (wx - wz) % p
    slate = np.maximum((d1 < 1.1), (d2 < 1.1)).astype(np.float32) * np.clip(0.55 + 0.5 * box(white, 1), 0, 1)
    lit_s = np.clip(1 - (d1 + d2) / (2 * p), 0, 1)
    c_roof = col(40, 33, 28) * (0.84 + 0.3 * lit_s)[..., None] + slate[..., None] * col(50, 43, 36) * (0.45 + 0.8 * patch)[..., None]
    c_rust = col(88, 41, 27) * (0.8 + 0.4 * lit_s)[..., None] + slate[..., None] * col(34, 14, 9)
    c_line = col(112, 96, 82) * (0.8 + 0.3 * patch)[..., None]
    c_pane = col(50, 44, 39) * (0.85 + 0.2 * (box(white, 1, 0)))[..., None]
    # windows: muted amber, brighter in the middle, streaked like old glass
    core = np.clip(box(glow, 3) * 1.25 - 0.1, 0, 1)
    streak = box(rng.normal(0, 1, (H, W)).astype(np.float32), 5, 0) * 2.6
    c_glow = (col(184, 124, 66) * (1 - core[..., None]) + col(238, 180, 104) * core[..., None]) * (1 + 0.09 * streak)[..., None]
    rgb = (wall[..., None] * c_wall + lwall[..., None] * c_lwall + rock[..., None] * c_rock + facet[..., None] * c_facet + etch[..., None] * c_etch + roof[..., None] * c_roof + rust[..., None] * c_rust + line[..., None] * c_line
           + pane[..., None] * c_pane + glow[..., None] * c_glow)
    halo = np.clip(box(glow, 4) * 1.6, 0, 1) * (1 - glow)
    rgb = rgb + halo[..., None] * col(58, 36, 14)
    rim = np.clip(a - shift_down(a, 2), 0, 1) * (a > 0.5)   # light catching the top edge of every mass
    rgb = rgb + (box(rim, 1) * (1 - glow))[..., None] * col(52, 44, 37)
    dark = (1 - glow)[..., None]
    tone = 1 + (0.11 * mott + 0.09 * weave + 0.08 * white)
    rgb = rgb * (1 + (tone - 1)[..., None] * (0.35 + 0.65 * dark))
    rgb = rgb + (((rng.random((H, W)) < 0.004) * rng.uniform(0.015, 0.045, (H, W))).astype(np.float32) * (1 - glow) * (1 - rock))[..., None] * col(255, 225, 190)
    if far:                                          # far layer: hazier, lower contrast
        rgb = rgb * 0.86 + col(98, 85, 73) * 0.14
    soft = np.stack([box(rgb[..., i], 1) for i in range(3)], axis=2)
    rgb = 0.9 * rgb + 0.1 * soft
    bite = np.clip(field(rng, 5, 1.0) + field(rng, 2, 0.8) - 0.9, 0, 1) * 0.5    # the ink edge breaks here and there
    rk = np.clip(box(rock, 3) * 1.4, 0, 1)                                       # rock is torn rougher than masonry
    tear = np.clip(field(rng, 7, 1.0) + field(rng, 3, 0.9) + field(rng, 2, 0.5) - 0.55, 0, 1) * 0.9
    rim_zone = np.clip((1 - box(a, 4)) * 2.5, 0, 1)                              # only the outline tears, not the mass
    ragged = a + rng.normal(0, 0.05, a.shape).astype(np.float32) * (1 + 2.5 * rk * rim_zone) - bite - tear * rk * rim_zone
    a = np.clip((ragged - 0.4) * 5.0, 0, 1) * (a > 0.03)
    skip = np.clip(field(rng, 4, 1.0) + field(rng, 2, 0.8) + 0.15 * white - 1.42, 0, 1) * 2.0   # dry-brush skips: paper shows through
    a = a * (1 - np.clip(skip, 0, 0.5) * (1 - glow) * (1 - 0.8 * rock))
    return np.clip(rgb, 0, 1), a


def over(top, ta, bot, ba):
    oa = ta + ba * (1 - ta)
    rgb = (top * ta[..., None] + bot * (ba * (1 - ta))[..., None]) / np.maximum(oa, 1e-6)[..., None]
    return rgb, oa


def save(path, rgb, a):
    img = bpy.data.images.new("out", W, H, alpha=True)
    img.alpha_mode = "STRAIGHT"
    img.pixels.foreach_set(np.concatenate([rgb, a[..., None]], axis=2)[::-1].astype(np.float32).ravel())
    img.filepath_raw, img.file_format = path, "PNG"
    img.save()


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    o = {"seed": "7"}
    o.update({argv[i].lstrip("-"): argv[i + 1] for i in range(0, len(argv) - 1, 2)})
    seed = int(o["seed"])
    tmp = o.get("keep") or tempfile.mkdtemp(prefix="skyline-")
    os.makedirs(tmp, exist_ok=True)
    sc, mats = setup_scene()
    far = Kit(random.Random(seed + 100), lit=0.12, sx=0.86, sz=0.9, dx=-190.0, dz=34.0)
    far_town(far)
    near = Kit(random.Random(seed), lit=0.46)
    near_town(near)
    fr, fa = finish(*render_layer(sc, mats, far, tmp, "far"), seed=seed + 1, far=True)
    nr, na = finish(*render_layer(sc, mats, near, tmp, "near"), seed=seed)
    rgb, a = over(nr, na, fr, fa)
    save(os.path.abspath(o["out"]), rgb, a)
    print("SKYLINE_RENDER size=%dx%d seed=%d shapes=%d version=%s" % (W, H, seed, near.n + far.n, bpy.app.version_string.split()[0]))


if __name__ == "__main__":
    main()
