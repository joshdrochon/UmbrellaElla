"""Keeper of Time owl, Blender builder (run by Blender, never python3):

  blender -b --factory-startup -P tools/build/assets/art_keeper_owl.py -- --job Art/Source/Keeper/Raw/Owl_Flap/Owl_Flap.job.json

GDD SH1.0 OWL-08 / ART-06: a crownless fabricated metal owl, left-facing side profile, rigid perforated vane wings on
articulated spars, two short mechanical legs, a chest clock (aged face, Roman markers, one hand) and three hanging
mechanisms, each on its own chain: front armillary sphere, middle ribbed cage, rear gear ring.

Registers the `keeper` builder in pipeline/art/blender/stand_ins.py's table and runs the shared sprite renderer
(camera, pivot, poses, .blend). The look is this file's: modelled sheet-metal plates (ridged, veined, riveted,
perforated) lit as worn metal in Cycles, Freestyle ink lines, then a paint pass that maps values onto the Keeper
palette (ink, soot, umber, bronze, taupe, paper), etches hatching into the shadows and adds paper tooth.
Built facing +X; the renderer mirrors it for faces=left.
"""
import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "pipeline", "art", "blender"))
import stand_ins as si  # noqa: E402

HALF = math.pi / 2
KEEPER_SCALE = 0.88          # whole figure, so the raised wing stays inside the frame
KEEPER_PALETTE = ("#0f0d0b", "#171614", "#292622", "#463C32", "#695640", "#918173", "#B0A294", "#cdbfa9")
KEEPER_STOPS = (0.0, 0.07, 0.2, 0.36, 0.52, 0.72, 0.9, 1.0)
KEEPER_LINE_PX = 1.25
KEEPER_HATCH_PX = 3.0         # engraving line pitch
KEEPER_ETCH = 0.7             # how much of the tone is carried by engraved lines
KEEPER_GAIN = 0.235           # render value scale of the tone shoulder (higher = darker)


def rad(deg):
    return math.radians(deg)


class KeeperKit:
    """Accumulates geometry into one mesh per (bone, material, shading) and hands the objects to the rig."""

    def __init__(self, rig, mats):
        self.rig, self.mats, self.bms = rig, mats, {}
        self.scale = Matrix.Scale(KEEPER_SCALE, 4)

    def bm(self, bone, mat, smooth=False, solid=0.0):
        key = (bone, mat, smooth, solid)
        if key not in self.bms:
            b = bmesh.new()
            b.loops.layers.uv.new("uv")
            self.bms[key] = b
        return self.bms[key]

    @staticmethod
    def place(x, z, y, a=0.0, tilt=0.0, pitch=0.0):
        """Local +X along picture-plane angle a (degrees), local Z across, local -Y toward the camera."""
        return (Matrix.Translation((x, y, z)) @ Matrix.Rotation(-rad(a), 4, "Y") @ Matrix.Rotation(tilt, 4, "X")
                @ Matrix.Rotation(-pitch, 4, "Z"))

    def blade(self, bone, mat, x, z, y, a, ln, wd, tilt=0.0, pitch=0.0, ridge=0.05, skew=0.0, tip=1.0, slots=0,
              thick=0.03, base=0.55):
        """One sheet-metal vane: pointed, ridged down the middle, optional perforation slots. UV: u along, v across."""
        b = self.bm(bone, mat, False, thick)
        uv = b.loops.layers.uv.active
        m = self.scale @ self.place(x, z, y, a, tilt, pitch)
        ts = (0.0, 0.05, 0.14, 0.4, 0.62, 0.78, 0.9, 1.0)       # straight-sided sheet, chisel point
        hw = (base, 0.9, 1.0, 1.0, 1.0, 0.94, 0.56 * tip + 0.3 * (1 - tip), 0.012)
        rows = []
        for t, h in zip(ts, hw):
            c = skew * wd * t * t
            h2 = h * wd / 2
            rows.append([(b.verts.new(m @ Vector((ln * t, 0.0, c - h2))), (t, 0.0)),
                         (b.verts.new(m @ Vector((ln * t, 0.0, c - h2 * 0.5))), (t, 0.25)),
                         (b.verts.new(m @ Vector((ln * t, -ridge * h, c))), (t, 0.5)),
                         (b.verts.new(m @ Vector((ln * t, 0.0, c + h2 * 0.5))), (t, 0.75)),
                         (b.verts.new(m @ Vector((ln * t, 0.0, c + h2))), (t, 1.0))])
        hole = set()
        if slots:   # perforations: skip the quads next to the ridge on alternate stations
            for k in range(slots):
                hole.add((2 + k, 1 if k % 2 else 2))
        for i in range(len(rows) - 1):
            for j in range(4):
                if (i, j) in hole:
                    continue
                q = (rows[i][j], rows[i + 1][j], rows[i + 1][j + 1], rows[i][j + 1])
                f = b.faces.new([v for v, _ in q])
                for lp, (_, u) in zip(f.loops, q):
                    lp[uv].uv = u
        return m

    def prim(self, bone, mat, kind, m, smooth=True, **kw):
        b = self.bm(bone, mat, smooth, 0.0)
        m = self.scale @ m
        if kind == "sphere":
            bmesh.ops.create_uvsphere(b, u_segments=kw.get("seg", 14), v_segments=kw.get("ring", 8), radius=1.0, matrix=m)
        elif kind == "cube":
            bmesh.ops.create_cube(b, size=1.0, matrix=m)
        elif kind == "cone":
            bmesh.ops.create_cone(b, cap_ends=True, segments=kw.get("seg", 20), radius1=kw.get("r1", 1.0),
                                  radius2=kw.get("r2", 1.0), depth=1.0, matrix=m)

    def sphere(self, bone, mat, x, z, y, r, sc=(1, 1, 1), a=0.0, seg=14):
        self.prim(bone, mat, "sphere", self.place(x, z, y, a) @ Matrix.Diagonal((r * sc[0], r * sc[1], r * sc[2], 1)),
                  seg=seg, ring=max(6, seg // 2))

    def box(self, bone, mat, x, z, y, a, sx, sy, sz, tilt=0.0):
        self.prim(bone, mat, "cube", self.place(x, z, y, a, tilt) @ Matrix.Diagonal((sx, sy, sz, 1)), smooth=False)

    def bar(self, bone, mat, p0, p1, y, wd, th=0.1):
        """A flat strut from p0 to p1 (picture-plane points)."""
        dx, dz = p1[0] - p0[0], p1[1] - p0[1]
        self.box(bone, mat, (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2, y, math.degrees(math.atan2(dz, dx)),
                 math.hypot(dx, dz), th, wd)

    def disc(self, bone, mat, x, z, y, r, depth=0.08, seg=28, r2=None):
        """A cylinder facing the camera (axis along Y)."""
        m = Matrix.Translation((x, y, z)) @ Matrix.Rotation(HALF, 4, "X") @ Matrix.Diagonal((1, 1, depth, 1))
        self.prim(bone, mat, "cone", m, smooth=False, seg=seg, r1=r, r2=r if r2 is None else r2)

    def ring(self, bone, mat, x, z, y, r, r_in, depth=0.08, seg=32):
        """An annulus facing the camera."""
        b = self.bm(bone, mat, False, 0.0)
        m = self.scale
        for k in range(seg):
            a0, a1 = 2 * math.pi * k / seg, 2 * math.pi * (k + 1) / seg
            for yy0, flip in ((y - depth / 2, False),):
                o0 = Vector((x + r * math.cos(a0), yy0, z + r * math.sin(a0)))
                o1 = Vector((x + r * math.cos(a1), yy0, z + r * math.sin(a1)))
                i0 = Vector((x + r_in * math.cos(a0), yy0, z + r_in * math.sin(a0)))
                i1 = Vector((x + r_in * math.cos(a1), yy0, z + r_in * math.sin(a1)))
                back = Vector((0, depth, 0))
                vs = [b.verts.new(m @ p) for p in (i0, o0, o1, i1, i0 + back, o0 + back, o1 + back, i1 + back)]
                b.faces.new((vs[0], vs[1], vs[2], vs[3]))          # front
                b.faces.new((vs[1], vs[5], vs[6], vs[2]))          # outer wall
                b.faces.new((vs[3], vs[7], vs[4], vs[0]))          # inner wall

    def gear(self, bone, mat, x, z, y, r, teeth, depth=0.1, tooth=0.14, r_in=None, phase=0.0):
        if r_in:
            self.ring(bone, mat, x, z, y, r, r_in, depth)
        else:
            self.disc(bone, mat, x, z, y, r, depth)
        for k in range(teeth):
            a = 360.0 * k / teeth + phase
            self.box(bone, mat, x + (r + tooth * 0.35) * math.cos(rad(a)), z + (r + tooth * 0.35) * math.sin(rad(a)), y, a,
                     tooth, depth, 2 * math.pi * r / teeth * 0.5)

    def tube(self, bone, mat, pts, radii, seg=8, flat=1.0, closed=False):
        """A round bar through 3D points (x, y, z); flat squashes it along Y."""
        b = self.bm(bone, mat, True, 0.0)
        n = len(pts)
        P = [Vector(p) for p in pts]
        rings = []
        for i in range(n):
            if closed:
                t = (P[(i + 1) % n] - P[i - 1]).normalized()
            else:
                t = (P[min(i + 1, n - 1)] - P[max(i - 1, 0)]).normalized()
            u = t.cross(Vector((0, 1, 0)))
            if u.length < 1e-4:
                u = t.cross(Vector((1, 0, 0)))
            u.normalize()
            v = t.cross(u).normalized()
            r = radii[i] if isinstance(radii, (list, tuple)) else radii
            ringv = []
            for k in range(seg):
                a = 2 * math.pi * k / seg
                off = u * math.cos(a) * r + v * math.sin(a) * r
                off.y *= flat
                ringv.append(b.verts.new(self.scale @ (P[i] + off)))
            rings.append(ringv)
        last = n if closed else n - 1
        for i in range(last):
            r0, r1 = rings[i], rings[(i + 1) % n]
            for k in range(seg):
                f = b.faces.new((r0[k], r0[(k + 1) % seg], r1[(k + 1) % seg], r1[k]))
                f.smooth = True
        if not closed:
            b.faces.new(rings[0][::-1])
            b.faces.new(rings[-1])

    def link(self, bone, mat, x, z, y, a, face_on, ln=0.2, wd=0.13, r=0.02):
        """One chain link: an oval seen face-on, or its edge."""
        pts = []
        ca, sa = math.cos(rad(a)), math.sin(rad(a))
        for k in range(12):
            t = 2 * math.pi * k / 12
            lx, lw = math.cos(t) * ln / 2, math.sin(t) * wd / 2
            if face_on:
                pts.append((x + lx * ca - lw * sa, y, z + lx * sa + lw * ca))
            else:
                pts.append((x + lx * ca, y + lw, z + lx * sa))
        self.tube(bone, mat, pts, r, seg=6, closed=True)

    def chain(self, bone, mat, p0, p1, y, sag=0.0, step=0.15):
        """Links along a sagging line from p0 to p1; returns the end point."""
        n = max(3, int(math.hypot(p1[0] - p0[0], p1[1] - p0[1]) * (1 + abs(sag)) / step))
        pts = []
        for k in range(n + 1):
            t = k / n
            pts.append((p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t - sag * 4 * t * (1 - t)))
        for k in range(n):
            (xa, za), (xb, zb) = pts[k], pts[k + 1]
            self.link(bone, mat, (xa + xb) / 2, (za + zb) / 2, y - 0.01 * (k % 2), math.degrees(math.atan2(zb - za, xb - xa)),
                      k % 2 == 0, ln=math.hypot(xb - xa, zb - za) * 1.45)
        return p1

    def rivet(self, bone, mat, x, z, y, r=0.04):
        self.sphere(bone, mat, x, z, y, r, sc=(1, 0.6, 1), seg=8)

    def finish(self):
        for (bone, mat, smooth, solid), b in self.bms.items():
            me = bpy.data.meshes.new(f"keeper_{bone}_{mat}")
            bmesh.ops.recalc_face_normals(b, faces=b.faces) if not solid else None
            b.to_mesh(me)
            b.free()
            ob = bpy.data.objects.new(me.name, me)
            bpy.context.scene.collection.objects.link(ob)
            me.materials.append(self.mats[mat])
            if smooth:
                for p in me.polygons:
                    p.use_smooth = True
            if solid:
                md = ob.modifiers.new("sheet", "SOLIDIFY")
                md.thickness, md.offset = solid * KEEPER_SCALE, -1.0
            self.rig.parts.append((ob, bone))


def keeper_wing(k, bone, y, sh, tone, dark, rnd, far=False, swing=0.0):
    """One rigid vane wing hung from an articulated arm: shoulder -> elbow -> wrist, primaries fanned from the wrist,
    secondaries along the forearm, two covert rows, riveted spars on top. y is the nearest layer; far wings step away."""
    d = 1.0 if far else -1.0          # depth direction of 'on top'
    sx, sz = sh
    cs, sn = math.cos(rad(swing)), math.sin(rad(swing))

    def turn(px, pz):
        return (sx + px * cs - pz * sn, sz + px * sn + pz * cs)
    el = turn(-1.15, 0.95)
    wr = turn(-2.35, 1.3)
    fe, sp, iron = tone
    # primaries: long broad perforated vanes from the wrist
    def seam_rivets(bx, bz, a, ln, yy, count):
        for q in range(count):
            u = 0.16 + 0.68 * q / max(1, count - 1)
            k.rivet(bone, iron, bx + ln * u * math.cos(rad(a)), bz + ln * u * math.sin(rad(a)), yy, 0.032)
    n = 7
    for i in range(n):
        t = i / (n - 1.0)
        a = 150 + 58 * t + rnd.uniform(-1.5, 1.5) + swing
        ln = 2.9 - 0.55 * t + rnd.uniform(-0.08, 0.08)
        bx, bz = wr[0] + 0.5 * t, wr[1] - 0.12 * t
        yy = y - d * (0.24 + 0.03 * i)
        k.blade(bone, fe if i % 2 else sp, bx, bz, yy, a, ln, 0.86, tilt=d * 0.28, ridge=0.08, skew=-0.3,
                slots=2 if i % 3 == 1 else 0, base=0.45)
        seam_rivets(bx, bz, a, ln, yy - d * 0.09, 4)
    # secondaries: along forearm then humerus, turning down toward the body
    n = 8
    for i in range(n):
        t = i / (n - 1.0)
        if t < 0.55:
            u = t / 0.55
            bx, bz = wr[0] + (el[0] - wr[0]) * u + 0.35, wr[1] + (el[1] - wr[1]) * u - 0.1
        else:
            u = (t - 0.55) / 0.45
            bx, bz = el[0] + (sx - el[0]) * u + 0.3, el[1] + (sz - el[1]) * u - 0.12
        a = 210 + 38 * t + rnd.uniform(-2, 2) + swing * (1 - 0.6 * t)
        ln = 2.55 - 0.95 * t + rnd.uniform(-0.1, 0.1)
        yy = y - d * (0.46 + 0.026 * i)
        k.blade(bone, fe if i % 2 else sp, bx, bz, yy, a, ln, 0.8, tilt=d * 0.26, ridge=0.07,
                skew=-0.24, slots=1 if i % 4 == 1 else 0, base=0.55)
        seam_rivets(bx, bz, a, ln, yy - d * 0.08, 3)
    # greater coverts: short broad plates over the vane roots
    n = 9
    for i in range(n):
        t = i / (n - 1.0)
        if t < 0.5:
            u = t / 0.5
            bx, bz = wr[0] + (el[0] - wr[0]) * u + 0.1, wr[1] + (el[1] - wr[1]) * u
        else:
            u = (t - 0.5) / 0.5
            bx, bz = el[0] + (sx - el[0]) * u + 0.1, el[1] + (sz - el[1]) * u
        a = 196 + 44 * t + rnd.uniform(-3, 3) + swing * (1 - 0.6 * t)
        ln = 1.4 - 0.3 * t + rnd.uniform(-0.06, 0.06)
        yy = y - d * (0.68 + 0.02 * i)
        k.blade(bone, sp if i % 2 else fe, bx, bz, yy, a, ln, 0.68, tilt=d * 0.24, ridge=0.07,
                skew=-0.2, base=0.7)
        seam_rivets(bx, bz, a, ln, yy - d * 0.08, 2)
    # lesser coverts: small plates along the arm
    n = 11
    for i in range(n):
        t = i / (n - 1.0)
        if t < 0.5:
            u = t / 0.5
            bx, bz = wr[0] + (el[0] - wr[0]) * u, wr[1] + (el[1] - wr[1]) * u + 0.05
        else:
            u = (t - 0.5) / 0.5
            bx, bz = el[0] + (sx - el[0]) * u, el[1] + (sz - el[1]) * u + 0.05
        a = 200 + 40 * t + rnd.uniform(-4, 4) + swing * (1 - 0.6 * t)
        k.blade(bone, fe if i % 2 else sp, bx, bz, y - d * (0.88 + 0.012 * i), a, 0.72, 0.46, tilt=d * 0.2, ridge=0.06,
                skew=-0.15, base=0.8)
    # the arm: two riveted spars, a brace, hinge discs with bolts
    ya = y - d * 1.06
    k.bar(bone, iron, (sx, sz), el, ya, 0.2, 0.1)
    k.bar(bone, iron, el, wr, ya, 0.17, 0.1)
    k.bar(bone, iron, (sx - 0.25, sz + 0.5), (el[0] - 0.55, el[1] + 0.3), ya + d * 0.03, 0.07, 0.06)   # brace
    for (px, pz), (qx, qz) in (((sx, sz), el), (el, wr)):
        for u in (0.25, 0.5, 0.75):
            k.rivet(bone, sp, px + (qx - px) * u, pz + (qz - pz) * u, ya - d * 0.06, 0.035)
    for (jx, jz), r in (((sx, sz), 0.3), (el, 0.24), (wr, 0.2)):
        k.disc(bone, sp, jx, jz, ya - d * 0.04, r, 0.1, seg=20)
        k.ring(bone, iron, jx, jz, ya - d * 0.1, r * 0.72, r * 0.5, 0.05, seg=20)
        k.sphere(bone, iron, jx, jz, ya - d * 0.12, r * 0.3, sc=(1, 0.6, 1), seg=10)
        for q in range(5):
            k.rivet(bone, iron, jx + r * 0.86 * math.cos(q * 1.257), jz + r * 0.86 * math.sin(q * 1.257), ya - d * 0.1, 0.022)


def keeper_roman(k, bone, mat, cx, cz, y, r, hour, size):
    """One Roman marker, top toward the rim. Built mirrored (the renderer flips the figure to face left)."""
    glyphs = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI", 7: "VII", 8: "VIII", 9: "IX", 10: "X", 11: "XI", 12: "XII"}[hour]
    ang = 90 + 30 * hour                      # mirrored dial: clockwise once flipped
    wds = {"I": 0.34, "V": 0.74, "X": 0.74}
    total = sum(wds[g] for g in glyphs) * size
    ux, uz = math.cos(rad(ang)), math.sin(rad(ang))          # up (outward)
    tx, tz = math.cos(rad(ang + 90)), math.sin(rad(ang + 90))   # along the marker (mirrored reading direction)
    pos = -total / 2
    st = size * 0.1
    for g in glyphs:
        w = wds[g] * size
        mx, mz = cx + ux * r + tx * (pos + w / 2), cz + uz * r + tz * (pos + w / 2)
        if g == "I":
            k.box(bone, mat, mx, mz, y, ang, size, 0.02, st)
        elif g == "V":
            for s in (-1, 1):
                k.box(bone, mat, mx + tx * s * w * 0.2, mz + tz * s * w * 0.2, y, ang + s * 17, size * 1.04, 0.02, st)
        else:
            for s in (-1, 1):
                k.box(bone, mat, mx, mz, y, ang + s * 30, size * 1.12, 0.02, st)
        pos += w


def build_keeper(m, rnd):
    r = si.Rig("Keeper")
    r.bone("body", (0, 0, -0.6), (0, 0, 0.8))
    r.bone("head", (0.95, 0, 0.9), (1.5, 0, 1.6), "body")
    r.bone("tail", (-1.5, 0, -0.1), (-3.0, 0, -0.7), "body")
    r.bone("wing_near", (-0.25, -0.5, 0.75), (-0.9, -0.5, 1.9), "body")
    r.bone("wing_far", (-0.1, 0.5, 0.85), (-0.7, 0.5, 2.0), "body")
    r.bone("mech", (0.6, -0.5, -0.9), (0.6, -0.5, -1.8), "body")
    k = KeeperKit(r, m)
    P, S, D, I, F = "k_plate", "k_spar", "k_dark", "k_iron", "k_face"

    # ---- far wing (behind everything), a touch higher so it shows over the near one
    keeper_wing(k, "wing_far", 1.6, (0.1, 1.0), ("k_far", "k_far2", I), "k_far2", rnd, far=True, swing=5.0)

    # ---- tail: plated fan
    for i in range(7):
        a = 186 + 9 * i + rnd.uniform(-1.5, 1.5)
        k.blade("tail", P if i % 2 else D, -1.25 - 0.05 * i, -0.2 - 0.08 * i, 0.35 - 0.02 * i, a, 2.7 - 0.12 * i, 0.66,
                tilt=-0.16, ridge=0.07, skew=-0.25, slots=1 if i % 3 == 1 else 0)
    # ---- far leg, then body core
    keeper_leg(k, (-0.5, -0.85), 0.45, P, S, I, D)
    k.sphere("body", D, -0.25, 0.0, 0.0, 1.0, sc=(1.75, 0.72, 1.08), a=12, seg=24)
    k.sphere("head", D, 0.9, 0.95, 0.0, 0.55, sc=(1.1, 0.9, 1.3), a=55, seg=16)      # neck
    # body plating: staggered scale rows over the barrel, front rows on top
    row = 0
    z = 0.95
    while z > -1.05:
        x = -1.85 + (0.16 if row % 2 else 0.0)
        col = 0
        while x < 1.5:
            e = ((x + 0.25) / 1.75) ** 2 + (z / 1.08) ** 2
            if e < 1.0:
                ys = -0.72 * math.sqrt(max(0.0, 1.0 - e)) - 0.05 - 0.02 * (x + 2.0)
                k.blade("body", (P, S, D)[(col + row) % 3], x + 0.2, z + 0.03 * math.sin(col), ys, 192 + 14 * (z < -0.3) + rnd.uniform(-5, 5),
                        0.56, 0.36, tilt=-0.12, pitch=0.08, ridge=0.05, base=0.85, thick=0.025)
            x += 0.33
            col += 1
        z -= 0.25
        row += 1
    # rump plates and a riveted belly keel
    for i in range(6):
        k.blade("body", P if i % 2 else S, -1.35 - 0.06 * i, 0.5 - 0.22 * i, -0.45, 186 + 6 * i, 1.1, 0.42, tilt=-0.1, ridge=0.05)
    k.tube("body", I, [(-1.6, -0.5, -0.75), (-0.8, -0.62, -1.02), (0.1, -0.66, -1.08), (0.9, -0.6, -0.92)], 0.07, seg=8)
    for i in range(9):
        t = i / 8.0
        k.rivet("body", S, -1.5 + 2.3 * t, -1.0 + 0.22 * (2 * t - 1) ** 2 - 0.02, -0.72, 0.035)
    for ex in (0.9, 0.0, -1.0):   # the three underside body eyes the chains hang from
        k.ring("body", I, ex, -1.16, -0.6, 0.11, 0.055, 0.05, seg=14)

    # ---- near leg
    keeper_leg(k, (0.2, -0.9), -0.62, P, S, I, D)

    # ---- hanging mechanisms, each on its own chain
    # front: armillary sphere (solid rim, intersecting hoops, central ball)
    ax, az = 1.1, -2.2
    k.chain("mech", I, (0.9, -1.1), (ax, az + 0.5), -1.0, sag=0.03)
    k.ring("mech", S, ax, az, -1.0, 0.42, 0.33, 0.1, seg=28)
    k.tube("mech", I, [(ax + 0.34 * math.cos(t), -1.0 + 0.34 * math.sin(t) * 0.9, az + 0.12 * math.sin(t))
                       for t in [2 * math.pi * q / 20 for q in range(20)]], 0.028, seg=6, closed=True)
    k.tube("mech", I, [(ax + 0.14 * math.sin(t), -1.0 + 0.3 * math.cos(t), az + 0.34 * math.sin(t))
                       for t in [2 * math.pi * q / 20 for q in range(20)]], 0.028, seg=6, closed=True)
    k.bar("mech", I, (ax - 0.4, az), (ax + 0.4, az), -0.98, 0.035, 0.04)
    k.sphere("mech", P, ax, az, -1.02, 0.15, seg=14)
    k.sphere("mech", I, ax, az + 0.46, -1.0, 0.06)
    k.tube("mech", S, [(ax, -1.0, az - 0.42), (ax, -1.0, az - 0.55), (ax, -1.0, az - 0.62)], [0.07, 0.05, 0.01], seg=8)
    # middle: ribbed cage cylinder, hanging lowest
    lx, lz = 3.15, -0.95
    k.chain("mech", I, (0.0, -1.25), (1.7, -1.3), -1.0, sag=0.16)
    k.chain("mech", I, (1.7, -1.3), (lx, lz + 0.92), -1.0, sag=-0.1)
    k.ring("mech", I, lx, lz + 0.8, -1.0, 0.1, 0.055, 0.04, seg=14)
    k.tube("mech", P, [(lx, -1.0, lz + 0.72), (lx, -1.0, lz + 0.62), (lx, -1.0, lz + 0.5), (lx, -1.0, lz + 0.42)],
           [0.06, 0.2, 0.4, 0.44], seg=14)                                                           # cap
    k.tube("mech", S, [(lx, -1.0, lz + 0.42), (lx, -1.0, lz + 0.36)], [0.46, 0.46], seg=14)
    k.tube("mech", I, [(lx, -0.8, lz + 0.36), (lx, -0.8, lz - 0.5)], [0.2, 0.2], seg=12)             # dark core
    for q in range(9):
        a = 2 * math.pi * q / 9 + 0.2
        k.tube("mech", S, [(lx + 0.4 * math.cos(a), -1.0 + 0.4 * math.sin(a), lz + 0.38),
                           (lx + 0.43 * math.cos(a), -1.0 + 0.43 * math.sin(a), lz - 0.05),
                           (lx + 0.4 * math.cos(a), -1.0 + 0.4 * math.sin(a), lz - 0.5)], 0.042, seg=6)
    for zz in (0.12, -0.2):
        k.tube("mech", P, [(lx + 0.44 * math.cos(t), -1.0 + 0.44 * math.sin(t), lz + zz)
                           for t in [2 * math.pi * q / 16 for q in range(16)]], 0.035, seg=6, closed=True)
    k.tube("mech", S, [(lx, -1.0, lz - 0.48), (lx, -1.0, lz - 0.56), (lx, -1.0, lz - 0.62), (lx, -1.0, lz - 0.74)],
           [0.46, 0.48, 0.3, 0.05], seg=14)                                                          # base + finial
    # rear: gear ring
    gx, gz = -1.2, -2.2
    k.chain("mech", I, (-1.0, -1.2), (gx, gz + 0.45), -1.0, sag=0.02)
    k.gear("mech", P, gx, gz, -1.0, 0.36, 10, 0.1, 0.15, r_in=0.2)
    k.ring("mech", I, gx, gz, -1.06, 0.2, 0.13, 0.05, seg=16)
    for q in range(4):
        k.bar("mech", S, (gx, gz), (gx + 0.22 * math.cos(q * HALF + 0.4), gz + 0.22 * math.sin(q * HALF + 0.4)), -1.0, 0.05, 0.05)
    k.sphere("mech", I, gx, gz, -1.04, 0.06)

    # ---- near wing
    keeper_wing(k, "wing_near", -0.75, (-0.25, 0.75), (P, S, I), D, rnd, swing=18.0)

    # ---- head: small, angular, crownless; swept-back plates, heavy brow, hooked beak, muted eye
    hx, hz = 1.42, 1.62
    k.sphere("head", D, hx, hz, 0.0, 0.7, sc=(1.0, 0.85, 0.98), seg=18)
    for row_i, rr in enumerate((0.66, 0.5, 0.36)):                 # plates sweeping back over the skull
        n = 10 - 2 * row_i
        for i in range(n):
            ph = 70 + 215 * i / (n - 1.0)
            px, pz = hx + rr * math.cos(rad(ph)) * 0.92 - 0.12, hz + rr * math.sin(rad(ph)) * 0.9
            k.blade("head", (P, S, P)[(i + row_i) % 3], px, pz, -0.5 - 0.06 * row_i - 0.004 * i, 140 + 0.42 * (ph - 70) + rnd.uniform(-4, 4),
                    0.5 - 0.04 * row_i, 0.32, tilt=-0.14, pitch=0.06, ridge=0.05, skew=-0.15, base=0.85, thick=0.025)
    for i in range(6):                                             # neck ruff down to the clock
        k.blade("head", S if i % 2 else P, hx - 0.62 + 0.2 * i, hz - 0.58 - 0.03 * i, -0.62, 232 + 9 * i, 0.66, 0.36, tilt=-0.14,
                ridge=0.05, skew=-0.15, base=0.8)
    ex, ez = hx + 0.26, hz + 0.02
    k.disc("head", P, ex, ez, -0.72, 0.4, 0.05, seg=10)                                # riveted face plate
    k.disc("head", I, ex, ez, -0.78, 0.27, 0.05, seg=24)                               # eye socket
    k.ring("head", S, ex, ez, -0.83, 0.25, 0.17, 0.04, seg=24)                         # rim
    k.sphere("head", F, ex, ez, -0.83, 0.165, sc=(1, 0.5, 1), seg=14)                  # muted glass eye, not lit
    k.sphere("head", I, ex + 0.02, ez - 0.01, -0.9, 0.09, sc=(1, 0.5, 1), seg=10)
    for q in range(8):
        k.rivet("head", I, ex + 0.33 * math.cos(q * 0.785 + 0.3), ez + 0.33 * math.sin(q * 0.785 + 0.3), -0.77, 0.022)
    k.blade("head", D, ex + 0.46, ez + 0.26, -0.92, 170, 0.95, 0.2, tilt=-0.3, ridge=0.07, skew=0.3, base=0.5)   # angular brow
    k.tube("head", S, [(hx + 0.5, -0.3, hz - 0.08), (hx + 0.66, -0.3, hz - 0.12), (hx + 0.76, -0.3, hz - 0.24),
                       (hx + 0.77, -0.3, hz - 0.4), (hx + 0.7, -0.3, hz - 0.52)], [0.17, 0.16, 0.12, 0.07, 0.008], seg=10, flat=0.7)
    k.tube("head", I, [(hx + 0.46, -0.25, hz - 0.26), (hx + 0.58, -0.25, hz - 0.33), (hx + 0.64, -0.25, hz - 0.42)],
           [0.09, 0.07, 0.01], seg=8, flat=0.7)
    k.sphere("head", I, hx + 0.6, hz - 0.1, -0.44, 0.025)                              # nostril

    # ---- chest clock: toothed back gear, riveted bezel, aged face, Roman markers, one long hand on one pivot
    cx, cz, cy = 0.78, 0.2, -1.4
    k.gear("body", I, cx - 0.12, cz - 0.1, cy + 0.14, 1.04, 22, 0.1, 0.16, phase=4)
    k.gear("body", S, cx - 0.75, cz - 0.7, cy + 0.2, 0.36, 10, 0.08, 0.13, r_in=0.16)
    k.disc("body", S, cx, cz, cy, 1.0, 0.16, seg=40)
    k.ring("body", P, cx, cz, cy - 0.1, 1.0, 0.86, 0.06, seg=40)
    k.ring("body", I, cx, cz, cy - 0.12, 0.86, 0.8, 0.05, seg=40)
    for q in range(16):
        a = 2 * math.pi * q / 16
        k.rivet("body", I, cx + 0.93 * math.cos(a), cz + 0.93 * math.sin(a), cy - 0.14, 0.03)
    k.disc("body", F, cx, cz, cy - 0.09, 0.8, 0.02, seg=40)
    k.ring("body", "k_facedark", cx, cz, cy - 0.105, 0.5, 0.485, 0.01, seg=40)
    k.ring("body", "k_facedark", cx, cz, cy - 0.105, 0.785, 0.76, 0.01, seg=40)
    for h in range(1, 13):
        keeper_roman(k, "body", "k_numeral", cx, cz, cy - 0.11, 0.62, h, 0.2)
    for q in range(60):
        if q % 5:
            a = rad(6 * q)
            k.box("body", "k_numeral", cx + 0.745 * math.cos(a), cz + 0.745 * math.sin(a), cy - 0.11, 6 * q, 0.03, 0.02, 0.012)
    ha = 62                                                         # the one hand
    k.blade("body", "k_numeral", cx - 0.14 * math.cos(rad(ha)), cz - 0.14 * math.sin(rad(ha)), cy - 0.14, ha, 0.82, 0.1,
            ridge=0.02, base=0.7, thick=0.01)
    k.disc("body", I, cx, cz, cy - 0.15, 0.07, 0.04, seg=14)
    k.sphere("body", S, cx, cz, cy - 0.18, 0.035)
    k.finish()
    return r.build(), {"mirror_bones": ()}


def keeper_leg(k, hip, y, P, S, I, D):
    """A short mechanical leg: plated thigh, hinge, banded shank, four hooked talons."""
    hx, hz = hip
    kn = (hx + 0.36, hz - 0.68)
    an = (hx + 0.04, hz - 1.36)
    for i in range(4):                                             # thigh plates
        k.blade("body", P if i % 2 else S, hx - 0.2 + 0.14 * i, hz + 0.28, y - 0.03 - 0.004 * i, 268 + 7 * i, 0.95, 0.36, tilt=-0.1,
                ridge=0.05, base=0.8)
    k.tube("body", S, [(hx + 0.05, y, hz), (kn[0], y, kn[1])], [0.2, 0.15], seg=10)
    k.tube("body", P, [(kn[0], y, kn[1]), (an[0], y, an[1])], [0.13, 0.11], seg=10)
    for u in (0.3, 0.55, 0.8):                                     # shank bands
        bx, bz = kn[0] + (an[0] - kn[0]) * u, kn[1] + (an[1] - kn[1]) * u
        k.tube("body", I, [(bx - 0.012, y, bz - 0.028), (bx + 0.012, y, bz + 0.028)], [0.15, 0.15], seg=10)
    k.tube("body", I, [(kn[0] - 0.2, y - 0.14, kn[1] - 0.15), (an[0] + 0.05, y - 0.14, an[1] + 0.3)], 0.03, seg=6)   # piston
    for (jx, jz), jr in ((kn, 0.19), (an, 0.15)):
        k.disc("body", S, jx, jz, y - 0.14, jr, 0.08, seg=18)
        k.ring("body", I, jx, jz, y - 0.19, jr * 0.7, jr * 0.45, 0.03, seg=18)
        k.sphere("body", I, jx, jz, y - 0.2, jr * 0.3, sc=(1, 0.6, 1), seg=8)
    for i, (da, ln) in enumerate(((-28, 0.74), (-60, 0.8), (-95, 0.7), (-158, 0.55))):   # talons: three forward, one back
        pts, rr = [], []
        for q in range(6):
            t = q / 5.0
            a = rad(da - 62 * t * t * (1 if da > -120 else -1))
            pts.append((an[0] + math.cos(rad(da)) * ln * t * 0.8 + math.cos(a) * ln * 0.2 * t,
                        y - 0.02 * i, an[1] - 0.05 + math.sin(rad(da)) * ln * t * 0.55 + math.sin(a) * ln * 0.45 * t - 0.25 * t * t))
            rr.append(0.095 * (1 - t) ** 0.7 + 0.006)
        k.tube("body", I if i % 2 else D, pts, rr, seg=8)
        k.sphere("body", S, pts[1][0], pts[1][2], y - 0.02 * i - 0.03, 0.06, seg=8)


# ---------- look: worn metal in Cycles ----------
def keeper_metal(name, base, vary=0.14, rough=0.5, veins=0.0, metallic=0.5):
    """Aged sheet metal: mottled value, fine scratches, optional barb veins from the UV (u along the vane, v across)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    N = nt.nodes.new
    L = nt.links.new
    out = N("ShaderNodeOutputMaterial")
    bsdf = N("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = rough
    geo = N("ShaderNodeNewGeometry")
    big = N("ShaderNodeTexNoise")
    big.inputs["Scale"].default_value = 2.2
    big.inputs["Detail"].default_value = 5.0
    fine = N("ShaderNodeTexNoise")
    fine.inputs["Scale"].default_value = 38.0
    fine.inputs["Detail"].default_value = 3.0
    scr_map = N("ShaderNodeMapping")
    scr_map.inputs["Scale"].default_value = (2.0, 2.0, 46.0)
    scr_map.inputs["Rotation"].default_value = (0.0, 0.5, 0.0)
    scr = N("ShaderNodeTexNoise")
    scr.inputs["Scale"].default_value = 9.0
    scr.inputs["Detail"].default_value = 2.0
    L(geo.outputs["Position"], big.inputs["Vector"])
    L(geo.outputs["Position"], fine.inputs["Vector"])
    L(geo.outputs["Position"], scr_map.inputs["Vector"])
    L(scr_map.outputs["Vector"], scr.inputs["Vector"])

    def math_node(op, a=None, b=None, c=None, clamp=False):
        n = N("ShaderNodeMath")
        n.operation, n.use_clamp = op, clamp
        for i, v in enumerate((a, b, c)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                L(v, n.inputs[i])
        return n.outputs[0]

    val = math_node("MULTIPLY_ADD", big.outputs["Fac"], vary * 2.0, 1.0 - vary)        # mottled plate value
    val = math_node("MULTIPLY", val, math_node("MULTIPLY_ADD", fine.outputs["Fac"], 0.3, 0.85))
    scratch = math_node("GREATER_THAN", scr.outputs["Fac"], 0.7)
    val = math_node("MULTIPLY", val, math_node("MULTIPLY_ADD", scratch, 0.22, 1.0))
    bump_h = math_node("MULTIPLY_ADD", fine.outputs["Fac"], 0.4, math_node("MULTIPLY", scratch, 0.3))
    if veins:
        uv = N("ShaderNodeUVMap")
        sep = N("ShaderNodeSeparateXYZ")
        L(uv.outputs["UV"], sep.inputs[0])
        vabs = math_node("ABSOLUTE", math_node("SUBTRACT", sep.outputs["Y"], 0.5))       # 0 on the ridge, 0.5 at the edge
        ph = math_node("ADD", math_node("MULTIPLY", sep.outputs["X"], veins), math_node("MULTIPLY", vabs, 9.0))
        barb = math_node("LESS_THAN", math_node("FRACT", ph), 0.14)
        barb = math_node("MULTIPLY", barb, math_node("GREATER_THAN", vabs, 0.04))
        ridge = math_node("LESS_THAN", vabs, 0.022)
        edge = math_node("GREATER_THAN", vabs, 0.455)
        root = math_node("SUBTRACT", 1.0, math_node("MULTIPLY", math_node("SUBTRACT", 1.0, sep.outputs["X"]), 0.45))   # darker at the root
        val = math_node("MULTIPLY", val, math_node("SUBTRACT", 1.0, math_node("MULTIPLY", barb, 0.3)))
        val = math_node("MULTIPLY", val, math_node("MULTIPLY_ADD", ridge, -0.5, 1.0))            # inked seam
        val = math_node("MULTIPLY", val, math_node("MULTIPLY_ADD", edge, 0.5, 1.0))               # worn bright edge
        val = math_node("MULTIPLY", val, math_node("MULTIPLY_ADD", sep.outputs["Y"], 0.45, 0.72))   # light falls across the plate
        hair = N("ShaderNodeTexNoise")                                                           # fine scratches along the plate
        hmap = N("ShaderNodeMapping")
        hmap.inputs["Scale"].default_value = (1.5, 60.0, 1.0)
        L(uv.outputs["UV"], hmap.inputs["Vector"])
        L(hmap.outputs["Vector"], hair.inputs["Vector"])
        hair.inputs["Scale"].default_value = 3.0
        val = math_node("MULTIPLY", val, math_node("MULTIPLY_ADD", math_node("GREATER_THAN", hair.outputs["Fac"], 0.62), -0.16, 1.0))
        val = math_node("MULTIPLY", val, root)
        bump_h = math_node("SUBTRACT", bump_h, math_node("MULTIPLY", barb, 0.8))
    col = N("ShaderNodeMixRGB")
    col.blend_type = "MULTIPLY"
    col.inputs["Fac"].default_value = 1.0
    col.inputs["Color1"].default_value = si.hex_rgb(base)
    comb = N("ShaderNodeCombineColor")
    for i in range(3):
        L(val, comb.inputs[i])
    L(comb.outputs[0], col.inputs["Color2"])
    L(col.outputs["Color"], bsdf.inputs["Base Color"])
    bev = N("ShaderNodeBevel")
    bev.samples = 4
    bev.inputs["Radius"].default_value = 0.018
    bump = N("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.2
    bump.inputs["Distance"].default_value = 0.02
    L(bump_h, bump.inputs["Height"])
    L(bev.outputs["Normal"], bump.inputs["Normal"])
    L(bump.outputs["Normal"], bsdf.inputs["Normal"])
    L(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return m


_keeper_base_materials = si.materials


def keeper_materials(colours, look):
    d = _keeper_base_materials(colours, look)
    d["k_plate"] = keeper_metal("k_plate", "#7d6b57", veins=7.0)
    d["k_spar"] = keeper_metal("k_spar", "#b9a78e", veins=7.0, rough=0.5)
    d["k_dark"] = keeper_metal("k_dark", "#57483b", veins=7.0, rough=0.6)
    d["k_far"] = keeper_metal("k_far", "#4c4035", veins=7.0, rough=0.7)
    d["k_far2"] = keeper_metal("k_far2", "#352c25", veins=7.0, rough=0.7)
    d["k_iron"] = keeper_metal("k_iron", "#332b25", rough=0.5, vary=0.2)
    d["k_face"] = keeper_metal("k_face", "#d8ccb6", rough=0.8, vary=0.14, metallic=0.0)
    d["k_facedark"] = keeper_metal("k_facedark", "#4a3d32", rough=0.8, vary=0.1, metallic=0.0)
    d["k_numeral"] = keeper_metal("k_numeral", "#1d1814", rough=0.7, vary=0.1, metallic=0.0)
    return d


def keeper_scene_look(scene, job):
    """Cycles, a key sun from the upper front, soft warm sky fill for the metal to reflect, thin ink lines."""
    scene.render.engine = "CYCLES"
    look = job["look"]
    scene.cycles.samples = int(look.get("cycles_samples", 128))
    scene.cycles.use_denoising = True
    scene.cycles.seed = int(look.get("seed", 11))
    scene.cycles.use_animated_seed = False
    try:
        scene.cycles.device = "CPU"
    except TypeError:
        pass
    for ob in list(scene.objects):
        if ob.type == "LIGHT":
            bpy.data.objects.remove(ob)
    sun = bpy.data.objects.new("key", bpy.data.lights.new("key", "SUN"))
    sun.data.energy = 5.5
    sun.data.angle = rad(6)
    sun.rotation_euler = (rad(42), rad(0), rad(-40))       # from the upper front-left of the final picture
    scene.collection.objects.link(sun)
    rim = bpy.data.objects.new("rim", bpy.data.lights.new("rim", "SUN"))
    rim.data.energy = 0.7
    rim.rotation_euler = (rad(110), rad(0), rad(150))
    scene.collection.objects.link(rim)
    w = scene.world or bpy.data.worlds.new("world")
    scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    grad = nt.nodes.new("ShaderNodeTexGradient")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Rotation"].default_value = (0.0, -HALF, 0.0)   # gradient along world Z: dark ground, light sky
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[0].color = 0.35, (0.03, 0.028, 0.025, 1)
    ramp.color_ramp.elements[1].position, ramp.color_ramp.elements[1].color = 0.75, (0.75, 0.72, 0.66, 1)
    nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], grad.inputs["Vector"])
    nt.links.new(grad.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 0.8
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    scene.render.film_transparent = True
    scene.render.filter_size = 1.1
    try:                                                    # the paint pass below owns the grain
        if hasattr(scene, "compositing_node_group"):
            scene.compositing_node_group = None
        else:
            scene.use_nodes = False
    except (AttributeError, TypeError):
        pass
    fs = scene.view_layers[0].freestyle_settings
    fs.crease_angle = rad(128)
    ls = fs.linesets[0]
    ls.select_silhouette = ls.select_border = ls.select_crease = True
    ls.linestyle.thickness = KEEPER_LINE_PX
    scene.render.line_thickness = KEEPER_LINE_PX


_keeper_base_setup = si.setup


def keeper_setup(job):
    scene, arm, extra, rep = _keeper_base_setup(job)
    if job.get("builder") == "keeper":
        keeper_scene_look(scene, job)
        rep["engine"] = "CYCLES"
    return scene, arm, extra, rep


si.materials = keeper_materials
si.setup = keeper_setup
si.BUILDERS["keeper"] = build_keeper


# ---------- paint pass ----------
def keeper_paint(path, seed=7):
    """On the rendered frame: map value onto the Keeper palette (ink .. paper), etch hatching into the shadows and
    half-tones, add paper tooth and a soft ink edge. Alpha untouched; the same seed for every frame (no boil)."""
    import numpy as np
    img = bpy.data.images.load(path)
    w, h = img.size
    px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
    rng = np.random.default_rng(seed)
    al = px[..., 3]
    rgb = px[..., :3]
    un = np.where(al[..., None] > 1e-4, rgb / np.maximum(al[..., None], 1e-4), 0.0)   # un-premultiply the edge pixels
    lum = np.clip(un @ np.array([0.3, 0.59, 0.11], dtype=np.float32), 0, 1)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)

    def noise(sc):
        g = rng.random((h // sc + 2, w // sc + 2)).astype(np.float32)
        gy, gx = np.arange(h, dtype=np.float32) / sc, np.arange(w, dtype=np.float32) / sc
        y0, x0 = gy.astype(int), gx.astype(int)
        fy, fx = (gy - y0)[:, None], (gx - x0)[None, :]
        top = g[y0][:, x0] * (1 - fx) + g[y0][:, x0 + 1] * fx
        bot = g[y0 + 1][:, x0] * (1 - fx) + g[y0 + 1][:, x0 + 1] * fx
        return top * (1 - fy) + bot * fy

    v = 1.0 - np.exp(-np.clip(lum - 0.004, 0, 4) / float(KEEPER_GAIN))   # shoulder: lit plates keep their tone
    # engraving: ink lines whose width follows the darkness (one family in the half-tones, a crossing one in shadow)
    wob = (noise(11) - 0.5) * 3.0
    dark = np.clip((0.74 - v) / 0.62, 0, 1)
    c1 = ((xx * 0.5 + yy * 0.866 + wob) % KEEPER_HATCH_PX) / KEEPER_HATCH_PX
    c2 = ((xx * 0.866 - yy * 0.5 - wob) % (KEEPER_HATCH_PX * 1.2)) / (KEEPER_HATCH_PX * 1.2)
    ink1 = np.clip((dark * 0.8 - c1) * KEEPER_HATCH_PX, 0, 1)            # soft 1 px edge, not a stair step
    ink2 = np.clip(((dark - 0.5) * 1.3 - c2) * KEEPER_HATCH_PX, 0, 1)
    ink = np.maximum(ink1, ink2)
    lifted = 0.3 + 0.7 * v                                               # the plate tone between the lines
    v = KEEPER_ETCH * (lifted * (1.0 - 0.62 * ink)) + (1.0 - KEEPER_ETCH) * v
    # paper tooth: fibres and specks in the ink, so no tone is a flat fill
    fibre = 0.5 * noise(2) + 0.5 * rng.random((h, w)).astype(np.float32)
    v = v * (0.9 + 0.2 * fibre)
    v = np.where(rng.random((h, w)) > 0.992, v * 1.25 + 0.05, v)         # worn specks
    v = np.clip(v, 0, 1)
    stops = np.array(KEEPER_STOPS, dtype=np.float32)
    cols = np.array([[int(c[i:i + 2], 16) / 255.0 for i in (1, 3, 5)] for c in KEEPER_PALETTE], dtype=np.float32)
    out = np.stack([np.interp(v, stops, cols[:, i]) for i in range(3)], axis=-1)   # a byte image's buffer is display-referred
    px[..., :3] = out * al[..., None]
    img.pixels[:] = px.ravel()
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)


if __name__ == "__main__":
    import json
    import shutil
    import tempfile
    import render_sprite
    _job = json.load(open(render_sprite.args(), encoding="utf-8"))
    _raw = os.path.join(tempfile.gettempdir(), "keeper_raw")       # unpainted renders, for --paint-only tuning
    os.makedirs(_raw, exist_ok=True)
    if "--paint-only" not in sys.argv:
        render_sprite.main()
        for _f in _job["frames"]:
            shutil.copyfile(_f, os.path.join(_raw, os.path.basename(_f)))
    for _f in _job["frames"]:
        if "--paint-only" in sys.argv:
            shutil.copyfile(os.path.join(_raw, os.path.basename(_f)), _f)
        keeper_paint(os.path.abspath(_f))
