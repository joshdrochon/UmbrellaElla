"""Ella as a procedural 3D sculpt in Blender (Cycles): every form is built here from code, nothing imported.

Run:  Blender -b --python Art/Source/Ella/ella3d.py -- <pose> <out.png> [seed] [samples]
pose: open | attack | shield | closed
World: X right (she faces +X), Z up, camera orthographic on -Y. Units are metres, Ella is about 1.6 tall.
Proportions are read off the Rehearsal Ella silhouettes and GDD SH1.0 ART-06 (no reference pixel is used).
"""
import math
import os
import random
import shutil
import sys

import bmesh
import bpy
from mathutils import Vector

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
POSE = ARGS[0] if ARGS else "open"
OUT = ARGS[1] if len(ARGS) > 1 else "/tmp/ella3d.png"
SEED = int(ARGS[2]) if len(ARGS) > 2 else 7
SAMPLES = int(ARGS[3]) if len(ARGS) > 3 else 96
RES = (int(ARGS[4]), int(ARGS[5])) if len(ARGS) > 5 else (600, 700)
RNG = random.Random(SEED)
YAX = Vector((0, 1, 0))


def V(x, z, y=0.0):
    return Vector((x, y, z))


def ang(deg):
    r = math.radians(deg)
    return Vector((math.cos(r), 0, math.sin(r)))


def perp(d):
    """In-plane left normal of an XZ direction."""
    return Vector((-d.z, 0, d.x))


ETCH = {"hi_pct": 84.0, "gamma": 0.68, "range": 0.68, "ink": 0.55}
for kv in os.environ.get("ELLA_ETCH", "").split(","):       # tuning override, e.g. ELLA_ETCH=gamma=0.9,range=0.55
    if "=" in kv:
        ETCH[kv.split("=")[0]] = float(kv.split("=")[1])


def etch(path):
    """Ink pass on the render, inside Blender (numpy): crush the values toward near-black ink, cut tone-following
    hatching (wider strokes where the form is darker, a cross-cut in the deepest shadow) and add paper grain.
    The emissive gold (spell, eye glints) is left clean: only the magic gives light (ART-06)."""
    import numpy as np
    img = bpy.data.images.load(path)
    w, h = img.size
    px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
    lin, al = px[..., :3], px[..., 3:]
    srgb_ = np.where(lin <= 0.0031308, lin * 12.92, 1.055 * np.power(np.clip(lin, 0, None), 1 / 2.4) - 0.055)
    lum = srgb_ @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    mx_, mn_ = srgb_.max(-1), srgb_.min(-1)
    gold = np.clip(((mx_ - mn_) - 0.10) / 0.08, 0, 1) * np.clip((lum - 0.60) / 0.1, 0, 1)
    rs = np.random.RandomState(SEED)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    wob = sum(a_ * np.sin(xx * fx + yy * fy + ph_) for a_, fx, fy, ph_ in
              [(rs.uniform(1.0, 2.2), rs.uniform(-0.05, 0.05), rs.uniform(-0.05, 0.05), rs.uniform(0, 6.28))
               for _ in range(6)])
    body = lum[(al[..., 0] > 0.9) & (gold < 0.5)]
    lo_, hi_ = np.percentile(body, 3), np.percentile(body, ETCH["hi_pct"])
    tone = np.clip((lum - lo_) / max(hi_ - lo_, 1e-3), 0, 1) ** ETCH["gamma"]   # 0 = deepest shadow, 1 = lit
    out_l = 0.03 + ETCH["range"] * tone                                         # ink range: near-black to worn bone

    def hatch(deg, period, lo, hi):
        r_ = math.radians(deg)
        ph_ = (xx * math.cos(r_) + yy * math.sin(r_) + wob) / period
        sn_ = 0.5 + 0.5 * np.sin(2 * math.pi * ph_)
        thr = lo + (hi - lo) * tone                                    # darker form: lower threshold, wider stroke
        return np.clip((sn_ - thr) / 0.18, 0, 1)

    ink = np.maximum(hatch(38, 4.6, 0.25, 1.3), hatch(-52, 5.2, 0.65, 2.6))
    grain = rs.normal(0, 1, (h, w)).astype(np.float32)
    grain = (grain + np.roll(grain, 1, 0) + np.roll(grain, 1, 1)) / 3
    out_l = out_l * (1 - ETCH["ink"] * ink) * (1 + 0.07 * grain)
    scale = (out_l / np.maximum(lum, 1e-3))[..., None]
    res = np.clip(srgb_ * scale, 0, 1)
    grey = out_l[..., None] * np.array([1.05, 1.0, 0.92], dtype=np.float32)   # warm ink grey
    res = np.clip(0.4 * res + 0.6 * grey, 0, 1)
    res = res * (1 - gold[..., None]) + srgb_ * gold[..., None]
    lin2 = np.where(res <= 0.04045, res / 12.92, np.power((res + 0.055) / 1.055, 2.4))
    img.pixels = np.concatenate([lin2, al], -1).ravel().tolist()
    img.save()



if os.environ.get("ELLA_ETCH_ONLY"):    # ink pass alone on a kept raw render: ELLA_RAW=<raw.png> ELLA_ETCH_ONLY=1
    shutil.copy(os.environ["ELLA_RAW"], OUT)
    etch(OUT)
    sys.exit(0)

# ------------------------------------------------------------------ scene
bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
COL = scn.collection


def new_obj(name, verts, faces, mat, smooth=True, subsurf=0, solidify=0.0, uvs=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.update()
    if uvs:                                   # u = round the form, v = along it: the engraving follows the form
        layer = me.uv_layers.new(name="UVMap")
        for lp in me.loops:
            layer.data[lp.index].uv = uvs[lp.vertex_index]
    ob = bpy.data.objects.new(name, me)
    COL.objects.link(ob)
    me.materials.append(mat)
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    if solidify:
        m = ob.modifiers.new("solid", "SOLIDIFY")
        m.thickness = solidify
        m.offset = 0
    if subsurf:
        m = ob.modifiers.new("sub", "SUBSURF")
        m.levels = m.render_levels = subsurf
    return ob


def loft(name, pts, radii, mat, segs=20, cap=True, subsurf=1, twist=0.0):
    """Tube along a polyline. radii: per point r or (r_inplane, r_depth). Frames stay in the XZ plane + Y."""
    verts, faces, uvs = [], [], []
    n = len(pts)
    run = 0.0
    for i, p in enumerate(pts):
        run += (p - pts[i - 1]).length if i else 0.0
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, n - 1)]
        t = (b - a)
        t = t.normalized() if t.length > 1e-9 else Vector((0, 0, 1))
        n1 = t.cross(YAX)
        n1 = n1.normalized() if n1.length > 1e-6 else Vector((1, 0, 0))
        n2 = n1.cross(t).normalized()
        r = radii[i]
        r1, r2 = (r, r) if isinstance(r, (int, float)) else r
        for s in range(segs):
            th = 2 * math.pi * s / segs + twist * i
            verts.append(p + n1 * (math.cos(th) * r1) + n2 * (math.sin(th) * r2))
            uvs.append((s / segs, run))
    for i in range(n - 1):
        for s in range(segs):
            a = i * segs + s
            b = i * segs + (s + 1) % segs
            faces.append((a, b, b + segs, a + segs))
    if cap:
        faces.append(tuple(range(segs - 1, -1, -1)))
        faces.append(tuple(range((n - 1) * segs, n * segs)))
    return new_obj(name, verts, faces, mat, subsurf=subsurf, uvs=uvs)


def smooth_path(pts, n=24):
    """Catmull-Rom resample of a control polyline."""
    out = []
    P = [pts[0]] + list(pts) + [pts[-1]]
    segs = len(pts) - 1
    for k in range(n + 1):
        u = k / n * segs
        i = min(int(u), segs - 1)
        t = u - i
        p0, p1, p2, p3 = P[i], P[i + 1], P[i + 2], P[i + 3]
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                          + (-p0 + 3 * p1 - 3 * p2 + p3) * t * t * t))
    return out


def lerp(a, b, t):
    if isinstance(a, tuple):
        return tuple(x + (y - x) * t for x, y in zip(a, b))
    return a + (b - a) * t


def prof(table, t):
    """Piecewise-linear profile lookup, table = [(t, v), ...]."""
    for (t0, v0), (t1, v1) in zip(table, table[1:]):
        if t <= t1:
            return lerp(v0, v1, (t - t0) / max(t1 - t0, 1e-9))
    return table[-1][1]


def sphere(name, c, r, mat, scale=(1, 1, 1), segs=20, rings=12):
    verts, faces, uvs = [], [], []
    for i in range(rings + 1):
        ph = math.pi * i / rings
        for s in range(segs):
            th = 2 * math.pi * s / segs
            uvs.append((s / segs, i / rings * r * 3))
            verts.append(Vector((c.x + r * scale[0] * math.sin(ph) * math.cos(th),
                                 c.y + r * scale[1] * math.sin(ph) * math.sin(th),
                                 c.z + r * scale[2] * math.cos(ph))))
    for i in range(rings):
        for s in range(segs):
            a = i * segs + s
            b = i * segs + (s + 1) % segs
            faces.append((a, b, b + segs, a + segs))
    return new_obj(name, verts, faces, mat, uvs=uvs)


# ------------------------------------------------------------------ materials
def srgb(c):
    def f(u):
        u /= 255.0
        return u / 12.92 if u <= 0.04045 else ((u + 0.055) / 1.055) ** 2.4
    return (f(c[0]), f(c[1]), f(c[2]), 1.0)


def material(name, base, hi, rough=0.6, metal=0.0, hatch=140.0, hatch_amt=0.5, bump=0.25, noise=26.0,
             hatch_dir=(0.3, 0.0, 1.0), ao=0.75, cross=40.0, cross_w=0.18):
    hatch = hatch / 5.0          # stroke count round the form
    hatch_amt = hatch_amt * 0.7
    """Sculpt-and-etch surface: two-tone base broken by noise, creases darkened (AO), fine engraved hatch as both
    colour and bump so it never reads as a flat fill."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    for n_ in list(N):
        N.remove(n_)
    out = N.new("ShaderNodeOutputMaterial")
    bsdf = N.new("ShaderNodeBsdfPrincipled")
    L.new(bsdf.outputs[0], out.inputs[0])
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    tc = N.new("ShaderNodeTexCoord")
    # blotchy tone
    nz = N.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = noise
    nz.inputs["Detail"].default_value = 6.0
    nz.inputs["Roughness"].default_value = 0.65
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    mix = N.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs["A"].default_value = srgb(base)
    mix.inputs["B"].default_value = srgb(hi)
    L.new(nz.outputs["Fac"], mix.inputs["Factor"])
    # engraving that follows the form: strokes run along the form (bands across u), a lighter cross-cut along v
    uv = N.new("ShaderNodeSeparateXYZ")
    L.new(tc.outputs["UV"], uv.inputs[0])
    lines = max(4, round(hatch))                       # strokes round the form; whole number so the seam closes
    jit = N.new("ShaderNodeMath")                      # wobble the strokes so they are hand-cut, not ruled
    jit.operation = "MULTIPLY_ADD"
    jit.inputs[1].default_value = 0.035
    L.new(nz.outputs["Fac"], jit.inputs[0])
    L.new(uv.outputs["X"], jit.inputs[2])
    su = N.new("ShaderNodeMath")
    su.operation = "MULTIPLY"
    su.inputs[1].default_value = 2 * math.pi * lines
    L.new(jit.outputs[0], su.inputs[0])
    w1 = N.new("ShaderNodeMath")
    w1.operation = "SINE"
    L.new(su.outputs[0], w1.inputs[0])
    sv = N.new("ShaderNodeMath")
    sv.operation = "MULTIPLY"
    sv.inputs[1].default_value = 2 * math.pi * cross
    L.new(uv.outputs["Y"], sv.inputs[0])
    w2 = N.new("ShaderNodeMath")
    w2.operation = "SINE"
    L.new(sv.outputs[0], w2.inputs[0])
    wr = N.new("ShaderNodeMath")                       # 0.75 * strokes + 0.25 * cross-cut, in -1..1
    wr.operation = "MULTIPLY_ADD"
    wr.inputs[1].default_value = cross_w
    L.new(w2.outputs[0], wr.inputs[0])
    L.new(w1.outputs[0], wr.inputs[2])
    hm = N.new("ShaderNodeMapRange")
    hm.clamp = False
    hm.inputs["From Min"].default_value = -1.0
    hm.inputs["From Max"].default_value = 1.0
    hm.inputs["To Min"].default_value = 1.0 - hatch_amt
    hm.inputs["To Max"].default_value = 1.0 + hatch_amt * 0.6
    L.new(wr.outputs[0], hm.inputs["Value"])
    # creases
    aon = N.new("ShaderNodeAmbientOcclusion")
    aon.inputs["Distance"].default_value = 0.12
    aon.samples = 8
    am = N.new("ShaderNodeMapRange")
    am.inputs["From Min"].default_value = 0.35
    am.inputs["From Max"].default_value = 1.0
    am.inputs["To Min"].default_value = 1.0 - ao
    am.inputs["To Max"].default_value = 1.0
    L.new(aon.outputs["AO"], am.inputs["Value"])
    k = N.new("ShaderNodeMath")
    k.operation = "MULTIPLY"
    L.new(hm.outputs[0], k.inputs[0])
    L.new(am.outputs[0], k.inputs[1])
    dark = N.new("ShaderNodeMix")
    dark.data_type = "RGBA"
    dark.blend_type = "MULTIPLY"
    dark.inputs["Factor"].default_value = 1.0
    L.new(mix.outputs["Result"], dark.inputs["A"])
    L.new(k.outputs[0], dark.inputs["B"])
    L.new(dark.outputs["Result"], bsdf.inputs["Base Color"])
    bp = N.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = min(1.0, bump * 1.2)
    bp.inputs["Distance"].default_value = 0.01
    hb = N.new("ShaderNodeMath")
    hb.operation = "ADD"
    L.new(wr.outputs[0], hb.inputs[0])
    L.new(nz.outputs["Fac"], hb.inputs[1])
    L.new(hb.outputs[0], bp.inputs["Height"])
    L.new(bp.outputs[0], bsdf.inputs["Normal"])
    return m


def emission(name, col, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n_ in list(nt.nodes):
        nt.nodes.remove(n_)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = srgb(col)
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs[0], out.inputs[0])
    return m


M_CLOTH = material("cloth", (56, 49, 43), (117, 103, 88), rough=0.95, hatch=500, hatch_amt=0.55, bump=0.5)
M_COAT = material("coat", (49, 42, 39), (106, 93, 80), rough=0.95, hatch=120, hatch_amt=0.5, bump=0.45,
                  hatch_dir=(1.0, 0.0, 0.3))
M_HAT = material("hat", (43, 38, 35), (97, 85, 74), rough=0.95, hatch=150, hatch_amt=0.5, bump=0.5)
M_HAIR = material("hair", (70, 56, 44), (150, 126, 98), rough=0.95, hatch=60, hatch_amt=0.25, bump=0.15, noise=6)
M_HAIR_D = material("hair_d", (40, 32, 26), (92, 76, 60), rough=0.95, hatch=60, hatch_amt=0.25, bump=0.15, noise=6)
M_SCARF = material("scarf", (120, 104, 84), (190, 172, 142), rough=0.95, hatch=200, hatch_amt=0.45, bump=0.4)
M_SKIN = material("skin", (150, 126, 104), (196, 172, 146), rough=0.95, hatch=60, hatch_amt=0.2, bump=0.1)
M_LEG = material("stocking", (51, 46, 42), (108, 95, 85), rough=0.95, hatch=100, hatch_amt=0.6, bump=0.4,
                 hatch_dir=(1.0, 0.0, 1.0))
M_BOOT = material("boot", (54, 46, 38), (119, 100, 80), rough=0.7, hatch=100, hatch_amt=0.3, bump=0.25)
M_METAL = material("metal", (58, 46, 34), (150, 122, 84), rough=0.55, metal=0.6, hatch=40, hatch_amt=0.25,
                   bump=0.2)
M_CANOPY = material("canopy", (49, 43, 41), (109, 98, 85), rough=0.95, hatch=1100, hatch_amt=0.6, bump=0.6,
                    hatch_dir=(1.0, 0.0, 1.0), cross=11.0, cross_w=0.7)
M_MASK = material("mask", (20, 18, 17), (40, 35, 32), rough=0.95, hatch=100, hatch_amt=0.5, bump=0.3)
M_GOLD = emission("gold", (233, 196, 106), 3.2)


# ------------------------------------------------------------------ poses
# Angles are absolute XZ directions in degrees (0 = +X / forward, 90 = up, -90 = down).
POSES = {
    "open": dict(
        pelvis=V(-0.06, 0.98), torso=78, head=82,
        legs=[(-104, -118, -30), (-82, -112, -22)],          # (thigh, shin, foot) far, near
        shaft_o=V(0.33, 1.30), shaft_d=92, shaft_len=1.24, apex_at=1.0, open=1.0,
        hands=[0.50, 0.62], elbow=[1, 1],
        wind=200, skirt_sweep=0.42, hat_tilt=8),
    "attack": dict(
        pelvis=V(-0.02, 0.92), torso=58, head=38,
        legs=[(-150, -168, -80), (-52, -128, -40)],
        shaft_o=V(-0.92, 1.06), shaft_d=0, shaft_len=1.92, apex_at=0.0, open=0.8,
        hands=[0.80, 1.22], elbow=[-1, -1],
        wind=170, skirt_sweep=0.5, hat_tilt=-14, spell=True),
    "shield": dict(
        pelvis=V(-0.10, 0.98), torso=80, head=74,
        legs=[(-98, -112, -28), (-70, -114, -24)],
        shaft_o=V(-0.62, 1.22), shaft_d=0, shaft_len=1.75, apex_at=1.0, open=1.0,
        hands=[0.70, 1.12], elbow=[-1, -1],
        wind=178, skirt_sweep=0.42, hat_tilt=6),
    "closed": dict(
        pelvis=V(-0.10, 1.02), torso=62, head=48,
        legs=[(-38, -112, -18), (-22, -106, -14)],
        shaft_o=V(0.26, 1.42), shaft_d=-96, shaft_len=1.38, apex_at=1.0, open=0.0,
        hands=[0.22, None], elbow=[-1, 1], hat_hand=True,
        wind=152, skirt_sweep=0.6, hat_tilt=-16, hair_len=1.25),
}
P = POSES[POSE]

TORSO_LEN, NECK = 0.46, 0.10
THIGH, SHIN = 0.40, 0.40
UPPER, FORE = 0.29, 0.27
pelvis = P["pelvis"]
td = ang(P["torso"])
chest = pelvis + td * TORSO_LEN
neck = chest + td * 0.04
hd = ang(P["head"])
head_c = neck + hd * (NECK + 0.06)
WIND = ang(P["wind"])


# ------------------------------------------------------------------ umbrella
def umbrella():
    o, d, ln = P["shaft_o"], ang(P["shaft_d"]), P["shaft_len"]
    end = o + d * ln
    # apex_at 1: canopy at the far end of the shaft; 0: at the origin end
    apex = end if P["apex_at"] > 0.5 else o
    u = d if P["apex_at"] > 0.5 else -d            # from handle toward apex
    tail = o if P["apex_at"] > 0.5 else end        # the free terminal end
    opn = P["open"]
    loft("shaft", [tail, apex + u * 0.02], [0.0115, 0.0115], M_METAL, segs=10, subsurf=0)
    # ferrules on the shaft
    for f in (0.12, 0.3):
        c = tail + u * (ln * f)
        loft("ferrule", [c - u * 0.012, c, c + u * 0.012], [0.014, 0.019, 0.014], M_METAL, segs=10)
    # crown finial: stacked beads and a spike
    fin = [(0.00, 0.020), (0.02, 0.030), (0.04, 0.016), (0.06, 0.026), (0.085, 0.012), (0.11, 0.018),
           (0.15, 0.006), (0.19, 0.001)]
    loft("finial", [apex + u * a for a, _ in fin], [r for _, r in fin], M_METAL, segs=12)
    for s_ in (-1, 1):   # small cross arms of the crown
        loft("finial_arm", [apex + u * 0.11, apex + u * 0.125 + perp(u) * 0.035 * s_], [0.007, 0.003], M_METAL,
             segs=8, subsurf=0)
    # terminal: narrow pierced diamond (clock-hand) at the free end
    t0 = tail - u * 0.03
    w_, l_ = 0.034, 0.15
    dm = [t0, t0 - u * l_ * 0.42 + perp(u) * w_, t0 - u * l_, t0 - u * l_ * 0.42 - perp(u) * w_, t0]
    loft("terminal", dm, [0.008] * 5, M_METAL, segs=8, cap=False, subsurf=0)
    loft("terminal_bar", [t0, t0 - u * l_ * 1.18], [0.006, 0.002], M_METAL, segs=8, subsurf=0)
    sphere("terminal_knob", tail - u * 0.015, 0.02, M_METAL)
    # canopy
    NG, SUB, RINGS = 10, 8, 14
    L = 0.80
    a_open = 1.12
    Rc = L / a_open
    e1, e2 = YAX, u.cross(YAX).normalized()
    beta = 0.17
    verts, faces, cuv = [], [], []
    rib_pts = [[] for _ in range(NG)]

    def rib_point(s, phi, sagf):
        al = a_open * s
        po_ax, po_r = Rc * (1 - math.cos(al)), Rc * math.sin(al)
        pc_ax, pc_r = L * s * math.cos(beta), L * s * math.sin(beta) + 0.012
        ax, r = lerp(pc_ax, po_ax, opn), lerp(pc_r, po_r, opn)
        r *= sagf
        return apex - u * ax + (e2 * math.cos(phi) + e1 * math.sin(phi)) * r

    cols = NG * SUB
    for j in range(RINGS + 1):
        for c in range(cols):
            g, f = divmod(c, SUB)
            fr = f / SUB
            bow = math.sin(math.pi * fr)
            s = j / RINGS
            s_edge = 1.0 - (0.085 * opn + 0.02) * bow          # scalloped hem
            sag = 1.0 - (0.07 * opn - 0.55 * (1 - opn)) * bow * s * s   # open: sags in; closed: folds bulge out
            phi = 2 * math.pi * (g + fr) / NG + 0.31
            p = rib_point(s * s_edge, phi, sag)
            verts.append(p)
            cuv.append((c / cols, s * L))
            if f == 0:
                rib_pts[g].append(rib_point(s, phi, 1.0) - u * 0.004)
    for j in range(RINGS):
        for c in range(cols):
            a = j * cols + c
            b = j * cols + (c + 1) % cols
            faces.append((a, b, b + cols, a + cols))
    new_obj("canopy", verts, faces, M_CANOPY, solidify=0.006, subsurf=1, uvs=cuv)
    for g in range(NG):
        loft("rib", rib_pts[g], [0.006] * len(rib_pts[g]), M_METAL, segs=6, subsurf=0)
        sphere("rib_tip", rib_pts[g][-1], 0.014, M_METAL, segs=10, rings=6)
        if opn > 0.4:   # stretcher from mid rib to the runner on the shaft
            runner = apex - u * (0.42 * (1.2 - 0.4 * opn))
            loft("stretcher", [rib_pts[g][RINGS // 2], runner], [0.004, 0.004], M_METAL, segs=6, subsurf=0)
    if opn > 0.4:
        runner = apex - u * (0.42 * (1.2 - 0.4 * opn))
        loft("runner", [runner - u * 0.02, runner + u * 0.02], [0.02, 0.02], M_METAL, segs=10)
    else:           # closed: a tie band round the folded canopy
        c = apex - u * (L * 0.82)
        loft("tie", [c - u * 0.025, c, c + u * 0.025], [(0.10, 0.10), (0.108, 0.108), (0.10, 0.10)], M_METAL,
             segs=16)
    return dict(o=o, d=d, tail=tail, apex=apex, u=u)


UMB = umbrella()


def shaft_at(dist):
    return P["shaft_o"] + ang(P["shaft_d"]) * dist


# ------------------------------------------------------------------ body
def torso():
    a = pelvis - td * 0.05
    ctrl = [a, pelvis + td * 0.10, pelvis + td * 0.22, pelvis + td * 0.34, chest, neck + td * 0.03]
    path = smooth_path(ctrl, 18)
    table = [(0.0, (0.105, 0.150)), (0.2, (0.100, 0.145)), (0.42, (0.078, 0.118)), (0.7, (0.100, 0.150)),
             (0.88, (0.092, 0.165)), (1.0, (0.045, 0.055))]
    radii = [prof(table, i / (len(path) - 1)) for i in range(len(path))]
    loft("torso", path, radii, M_COAT, segs=24)
    # belt
    w = pelvis + td * 0.19
    loft("belt", [w - td * 0.022, w, w + td * 0.022], [(0.086, 0.126), (0.090, 0.130), (0.086, 0.126)], M_METAL,
         segs=24)
    sphere("buckle", w + perp(td) * -0.088 + Vector((0, -0.03, 0)), 0.022, M_METAL, scale=(0.6, 1, 1))
    # coat front: placket and buttons toward the camera-front quarter
    fr = -perp(td)
    for k in range(4):
        c = pelvis + td * (0.25 + k * 0.055)
        rr = prof(table, (0.25 + k * 0.055 + 0.05) / (TORSO_LEN + 0.12))[0]
        sphere("button", c + fr * (rr * 0.82) + Vector((0, -0.075, 0)), 0.012, M_METAL, segs=10, rings=6)
    # collar ring
    loft("collar", [neck - td * 0.02, neck + td * 0.01, neck + td * 0.04],
         [(0.075, 0.10), (0.070, 0.092), (0.05, 0.062)], M_COAT, segs=20)
    # neck and head, face hidden under mask
    loft("neck", [neck, head_c - hd * 0.06], [0.04, 0.042], M_MASK, segs=14)
    sphere("head", head_c, 0.105, M_MASK, scale=(1.0, 0.95, 1.1))
    for ey in (-0.045, 0.02):      # eye glints: small, separate, the only light on the face
        sphere("glint", head_c + (-perp(hd)) * 0.092 + hd * 0.012 + Vector((0, ey - 0.03, 0)), 0.0085, M_GOLD,
               segs=8, rings=5)


def ik(a, c, l1, l2, bend):
    d = c - a
    dist = min(d.length, l1 + l2 - 1e-4)
    dn = d.normalized()
    x = (l1 * l1 - l2 * l2 + dist * dist) / (2 * dist)
    h = math.sqrt(max(l1 * l1 - x * x, 0.0))
    return a + dn * x + perp(dn) * h * bend


def sleeve(name, pts, y, r0, r1, mat):
    path = smooth_path([p + Vector((0, y, 0)) for p in pts], 20)
    n = len(path)
    radii = []
    for i in range(n):
        t = i / (n - 1)
        fold = 1 + 0.07 * math.sin(t * 34 + y * 40) * (0.4 + 0.6 * math.sin(math.pi * t))
        radii.append(lerp(r0, r1, t) * fold)
    return loft(name, path, radii, mat, segs=16)


def hand_on_shaft(c, y, d):
    """A fist round the shaft: back of the hand toward the camera and four finger rolls."""
    sphere("palm", c + Vector((0, y * 0.5, 0)), 0.036, M_SKIN, scale=(1.15, 1.0, 0.95))
    for k in range(4):
        cc = c + d * (-0.030 + k * 0.020)
        ring = []
        for s in range(9):
            th = math.pi * (0.15 + 1.2 * s / 8)
            ring.append(cc + perp(d) * (math.cos(th) * 0.024) + Vector((0, -math.sin(th) * 0.03 + y * 0.3, 0)))
        loft("finger", ring, [0.0095] * 9, M_SKIN, segs=8, subsurf=1)
    sphere("thumb", c + d * 0.012 + perp(d) * 0.026 + Vector((0, y * 0.5 - 0.02, 0)), 0.014, M_SKIN,
           scale=(1.6, 1, 0.9), segs=10, rings=6)


def arms():
    sh = chest - td * 0.03
    for i, (y, shade) in enumerate(((0.14, M_COAT), (-0.15, M_COAT))):     # far, near
        hd_ = P["hands"][i]
        if hd_ is None and P.get("hat_hand"):
            target = head_c + hd * 0.17 + perp(hd) * -0.10        # hand on the hat brim/crown
        else:
            target = shaft_at(hd_)
        s = sh + perp(td) * (0.02 if i == 0 else -0.02)
        el = ik(s, target, UPPER, FORE, P["elbow"][i])
        wr = el + (target - el) * 0.86
        sphere("shoulder", s + Vector((0, y, 0)), 0.066, M_COAT)
        sleeve("upper_arm", [s, lerp(s, el, 0.5), el], y, 0.060, 0.050, shade)
        sleeve("fore_arm", [el, lerp(el, wr, 0.5), wr], y * 0.9, 0.050, 0.040, shade)
        loft("cuff", [wr + Vector((0, y * 0.9, 0)) - (wr - el).normalized() * 0.03,
                      wr + Vector((0, y * 0.9, 0)) + (wr - el).normalized() * 0.012],
             [0.047, 0.050], M_COAT, segs=14)
        if hd_ is None:
            sphere("hat_hand", target + Vector((0, y * 0.6, 0)), 0.04, M_SKIN, scale=(1.3, 0.9, 0.7))
            for k in range(4):
                b = target + Vector((0, y * 0.6 - 0.03 + k * 0.02, 0))
                loft("hf", [b, b + ang(P["head"] + 100) * 0.05 + ang(P["head"]) * -0.01], [0.009, 0.007], M_SKIN,
                     segs=6)
        else:
            hand_on_shaft(target, y * 0.25 - 0.02, ang(P["shaft_d"]))


def boot(ankle, shin_d, foot_deg, y):
    fd = ang(foot_deg)
    up = -shin_d
    # boot shaft up the calf
    top = ankle + up * 0.17
    loft("boot_shaft", smooth_path([p + Vector((0, y, 0)) for p in (top, ankle + up * 0.08, ankle - up * 0.01)], 8),
         [0.060, 0.058, 0.054, 0.050, 0.048, 0.047, 0.048, 0.050, 0.052], M_BOOT, segs=16)
    loft("boot_cuff", [top + Vector((0, y, 0)) - up * 0.012, top + Vector((0, y, 0)) + up * 0.012],
         [0.064, 0.066], M_BOOT, segs=16)
    heel = ankle - up * 0.045 - fd * 0.035
    toe = heel + fd * 0.24
    fp = smooth_path([p + Vector((0, y, 0)) for p in (heel, lerp(heel, toe, 0.4) + perp(fd) * 0.012,
                                                      lerp(heel, toe, 0.8), toe)], 10)
    fr = [(0.046, 0.046), (0.052, 0.05), (0.054, 0.052), (0.052, 0.054), (0.048, 0.056), (0.044, 0.056),
          (0.040, 0.055), (0.038, 0.052), (0.036, 0.048), (0.030, 0.04), (0.012, 0.02)]
    loft("boot_foot", fp, fr, M_BOOT, segs=16)
    # sole and heel block
    sn = -perp(fd)
    sole = [heel + sn * 0.048 + Vector((0, y, 0)), toe + sn * 0.034 + Vector((0, y, 0))]
    loft("sole", sole, [(0.012, 0.05), (0.010, 0.04)], M_MASK, segs=10)
    hb = heel + sn * 0.058 + fd * 0.015 + Vector((0, y, 0))
    loft("heel", [hb - sn * 0.022, hb + sn * 0.022], [(0.034, 0.04), (0.030, 0.036)], M_MASK, segs=10)
    # laces up the front
    front = perp(shin_d) if perp(shin_d).dot(fd) > 0 else -perp(shin_d)
    for k in range(5):
        c = ankle + up * (0.015 + k * 0.032) + front * 0.05 + Vector((0, y, 0))
        loft("lace", [c + Vector((0, -0.03, 0)) + up * 0.008, c + front * 0.006, c + Vector((0, 0.03, 0)) - up * 0.008],
             [0.0045] * 3, M_SCARF, segs=6, subsurf=0)


def legs():
    for i, y in enumerate((0.075, -0.085)):
        th, sh_, ft = P["legs"][i]
        hip = pelvis + perp(td) * (0.01 if i else -0.01)
        knee = hip + ang(th) * THIGH
        ankle = knee + ang(sh_) * SHIN
        path = smooth_path([p + Vector((0, y, 0)) for p in (hip, lerp(hip, knee, 0.5), knee,
                                                            lerp(knee, ankle, 0.45), ankle)], 22)
        table = [(0.0, 0.088), (0.25, 0.082), (0.48, 0.060), (0.52, 0.062), (0.66, 0.062), (0.85, 0.044),
                 (1.0, 0.040)]
        loft("leg", path, [prof(table, k / 22) for k in range(23)], M_LEG, segs=16)
        boot(ankle, ang(sh_), ft, y)


def skirt():
    """Layered ragged tiers: pleated cones round the hips, hems cut like torn leaves, swept back by the wind."""
    down = -td
    side = perp(td)             # in-plane, toward her back when she faces +X
    back = side if side.dot(WIND) > 0 else -side
    sweep = P["skirt_sweep"]
    tiers = [(-0.20, 0.15, 0.20, 0.100), (-0.16, 0.23, 0.26, 0.105), (-0.12, 0.31, 0.31, 0.11),
             (-0.08, 0.38, 0.35, 0.115), (-0.05, 0.44, 0.38, 0.12)]
    # legs lifted forward push the front of the skirt: tilt the tiers a little toward the mean thigh
    thigh_mean = (ang(P["legs"][0][0]) + ang(P["legs"][1][0])).normalized()
    axis = (down * 0.7 + thigh_mean * 0.3).normalized()
    SEG, RINGS = 120, 12
    for ti, (start, length, flare, r_top) in enumerate(reversed(tiers)):
        rng = random.Random(SEED * 31 + ti)
        teeth = rng.randint(9, 12)
        tooth_amp = [rng.uniform(0.45, 1.0) for _ in range(teeth)]
        tooth_off = rng.uniform(0, 1)
        pleats = rng.randint(13, 17)
        ph = rng.uniform(0, 6.28)
        top = pelvis + td * (0.17 - 0.0) + axis * (start + 0.20)
        verts, faces, suv = [], [], []
        for j in range(RINGS + 1):
            t = j / RINGS
            for s in range(SEG):
                th = 2 * math.pi * s / SEG
                u_ = (s / SEG * teeth + tooth_off) % teeth
                k = int(u_)
                fr = u_ - k
                tri = 1 - abs(2 * fr - 1)                               # leaf point in the middle of a tooth
                notch = 0.5 * math.sin(fr * math.pi * 6) * 0.08          # small serration on each leaf
                hem = 1.0 - (0.5 * tooth_amp[k]) * (1 - tri) ** 1.2 + notch * tri
                ln = length * hem
                r = r_top + (flare - r_top) * (t ** 0.8)
                pleat = 1 + (0.05 + 0.13 * t) * math.sin(pleats * th + ph + 2.0 * t)
                r *= pleat
                c, sn = math.cos(th), math.sin(th)
                # the back of the skirt streams with the wind, the front is pressed to the thighs
                backness = max(0.0, c)
                wind_push = sweep * (t ** 1.6) * (0.55 + 0.75 * backness) * length
                flutter = 0.03 * t * math.sin(th * 5 + ph + ti)
                p = top + axis * (ln * t * (1 - 0.25 * sweep * backness)) + back * (c * r) \
                    + Vector((0, sn * r * 1.05, 0)) + WIND * wind_push + axis * flutter
                verts.append(p)
                suv.append((s / SEG, t * length))
        for j in range(RINGS):
            for s in range(SEG):
                a = j * SEG + s
                b = j * SEG + (s + 1) % SEG
                faces.append((a, b, b + SEG, a + SEG))
        new_obj(f"skirt{ti}", verts, faces, M_CLOTH if ti % 2 else M_COAT, solidify=0.008, subsurf=0, uvs=suv)


def hat():
    tilt = P["head"] + P["hat_tilt"]
    hu = ang(tilt)
    base = head_c + hd * 0.075
    # brim: wide, wavy, ragged, drooping
    SEG, RINGS = 72, 6
    rng = random.Random(SEED + 5)
    rag = [rng.uniform(0.9, 1.06) for _ in range(SEG)]
    verts, faces, buv = [], [], []
    hs = perp(hu)
    for j in range(RINGS + 1):
        t = j / RINGS
        for s in range(SEG):
            th = 2 * math.pi * s / SEG
            r = 0.10 + (0.25 - 0.10) * t
            if j == RINGS:
                r *= rag[s]
            wave = 0.035 * math.sin(3 * th + 0.7) * t * t + 0.018 * math.sin(7 * th) * t * t
            droop = -0.11 * t * t
            verts.append(base + hs * (math.cos(th) * r) + Vector((0, math.sin(th) * r, 0)) + hu * (wave + droop + 0.05 * (1 - t)))
            buv.append((s / SEG, r))
    for j in range(RINGS):
        for s in range(SEG):
            a = j * SEG + s
            b = j * SEG + (s + 1) % SEG
            faces.append((a, b, b + SEG, a + SEG))
    new_obj("brim", verts, faces, M_HAT, solidify=0.012, subsurf=1, uvs=buv)
    # cone: crumpled, bent backward into a curled tip
    n = 26
    pts, radii = [], []
    p = base + hu * 0.02
    d_deg = tilt
    for i in range(n):
        t = i / (n - 1)
        pts.append(p.copy())
        crumple = 1 + 0.045 * math.sin(t * 34) * (1 - t) + 0.025 * math.sin(t * 71)
        radii.append(max(0.004, (0.118 * (1 - t) ** 0.9 + 0.004) * crumple))
        bend = 3.0 + 26.0 * t ** 2.2            # bends more and more toward the tip: the curl
        d_deg += bend * (1 if WIND.x < 0 else -1) * 0.55
        p = p + ang(d_deg) * (0.44 / n) * (1.25 - 0.5 * t)
    loft("hat_cone", pts, radii, M_HAT, segs=18)
    loft("hat_band", [base + hu * 0.035, base + hu * 0.06, base + hu * 0.085], [0.127, 0.123, 0.115], M_SCARF, segs=20)
    sphere("hat_buckle", base + hu * 0.06 - hs * 0.11 + Vector((0, -0.05, 0)), 0.02, M_METAL, scale=(0.5, 1, 1.1))


HAIR_COL = bpy.data.collections.new("hair")     # strands: no ink outline (hundreds of curves)
COL.children.link(HAIR_COL)


def curve_strand(name, pts, radii, mat, bevel=0.012, res=3):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = bevel
    cu.bevel_resolution = res
    cu.use_fill_caps = True
    sp = cu.splines.new("NURBS")
    sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (p.x, p.y, p.z, 1)
        sp.points[i].radius = radii[i]
    sp.use_endpoint_u = True
    sp.order_u = 4
    ob = bpy.data.objects.new(name, cu)
    HAIR_COL.objects.link(ob)
    cu.materials.append(mat)
    return ob


def hair():
    """Long hair as clumps of fine strands (each clump follows one wavy guide), streaming with the wind."""
    rng = random.Random(SEED + 11)
    wperp = perp(WIND)
    length = P.get("hair_len", 1.0)
    for i in range(46):
        a = rng.uniform(-1.1, 1.1)
        yy = rng.uniform(-0.10, 0.10)
        root = head_c + WIND * (0.07 * math.cos(a)) + wperp * (0.085 * math.sin(a)) + Vector((0, yy, 0)) - hd * 0.02
        ln = rng.uniform(0.5, 0.95) * length
        amp = rng.uniform(0.03, 0.08)
        freq = rng.uniform(1.4, 2.4)
        phs = rng.uniform(0, 6.28)
        drift = rng.uniform(-0.30, 0.20)
        fall = rng.uniform(0.0, 0.16)
        for j in range(9):
            oy, oz = rng.uniform(-0.02, 0.02), rng.uniform(-0.022, 0.022)
            lj = ln * rng.uniform(0.8, 1.08)
            dph = rng.uniform(-0.35, 0.35)
            spread = rng.uniform(-0.05, 0.05)
            pts, radii = [], []
            n = 16
            for k in range(n):
                t = k / (n - 1)
                p = root + WIND * (lj * t) \
                    + wperp * (drift * lj * t * t + amp * math.sin(freq * 2 * math.pi * t + phs + dph * t) * t
                               + oz * (1 - 0.5 * t) + spread * t * t) \
                    + Vector((0, yy * 0.8 * t + oy + 0.03 * math.sin(phs + 5 * t), -fall * t * t))
                pts.append(p)
                radii.append(max(0.05, (1 - t) ** 0.6))
            curve_strand("hair", pts, radii, M_HAIR if (i + j) % 3 else M_HAIR_D, bevel=rng.uniform(0.0045, 0.0085),
                         res=2)
    sphere("hair_cap", head_c + WIND * 0.035 - hd * 0.005, 0.112, M_HAIR_D, scale=(1.0, 1.0, 1.05))


def ribbon(name, centre, width_fn, mat, y0=0.0, rag_seed=0):
    rng = random.Random(SEED + rag_seed)
    n = len(centre)
    W = 9
    verts, faces, ruv = [], [], []
    tear = [rng.uniform(0.0, 1.0) for _ in range(W)]
    for i, c in enumerate(centre):
        t = i / (n - 1)
        a = centre[max(i - 1, 0)]
        b = centre[min(i + 1, n - 1)]
        tn = (b - a).normalized()
        nrm = perp(tn)
        w = width_fn(t)
        for k in range(W):
            f = k / (W - 1) - 0.5
            twist = 0.9 * math.sin(t * 5.0 + rag_seed)
            ruv.append((k / (W - 1) * 0.25, t * 0.8))
            end_cut = (tn * (-0.10 * tear[k] * max(0, (t - 0.86)) / 0.14)) if t > 0.86 else Vector((0, 0, 0))
            verts.append(c + nrm * (f * w * math.cos(twist)) + Vector((0, y0 + f * w * math.sin(twist) + 0.02 * math.sin(t * 9 + k), 0)) + end_cut)
    for i in range(n - 1):
        for k in range(W - 1):
            a = i * W + k
            faces.append((a, a + 1, a + 1 + W, a + W))
    return new_obj(name, verts, faces, mat, solidify=0.007, subsurf=2, uvs=ruv)


def scarf():
    wperp = perp(WIND)
    # wrap round the neck
    loft("scarf_wrap", [neck - td * 0.025, neck + td * 0.02, neck + td * 0.065],
         [(0.085, 0.112), (0.094, 0.118), (0.078, 0.10)], M_SCARF, segs=22)
    loft("scarf_wrap2", [neck + td * 0.035 - perp(td) * 0.01, neck + td * 0.075, neck + td * 0.10],
         [(0.082, 0.10), (0.085, 0.104), (0.06, 0.078)], M_SCARF, segs=22)
    for j, (ln, amp, drift, y0, fq) in enumerate(((0.95, 0.075, -0.16, -0.10, 2.1), (0.72, 0.06, -0.34, 0.06, 2.6))):
        start = neck + WIND * 0.07 + td * 0.02
        pts = []
        n = 40
        for i in range(n):
            t = i / (n - 1)
            pts.append(start + WIND * (ln * t) + wperp * (drift * ln * t + amp * math.sin(fq * 2 * math.pi * t + j * 1.7) * (0.3 + t)))
        ribbon(f"scarf_tail{j}", pts, lambda t: 0.13 * (1 - 0.35 * t) * (0.55 + 0.45 * min(1, t * 5)), M_SCARF,
               y0=y0, rag_seed=3 + j)


def spell():
    """ATTACK only: separate gold magic leaving the forward terminal (ART-06: no wand, light only from magic)."""
    tip = UMB["tail"] - UMB["u"] * 0.24
    f = -UMB["u"]
    pts = [tip, tip + f * 0.05, tip + f * 0.12, tip + f * 0.22, tip + f * 0.30]
    loft("spell", pts, [(0.004, 0.004), (0.035, 0.03), (0.05, 0.04), (0.03, 0.025), (0.002, 0.002)], M_GOLD, segs=12)
    rng = random.Random(SEED + 3)
    for _ in range(7):
        c = tip + f * rng.uniform(-0.08, 0.34) + perp(f) * rng.uniform(-0.09, 0.09)
        sphere("spark", c, rng.uniform(0.006, 0.013), M_GOLD, segs=8, rings=5)


scarf_first = True
hair()
torso()
legs()
skirt()
arms()
scarf()
hat()
if P.get("spell"):
    spell()

# ------------------------------------------------------------------ light, camera, render
world = bpy.data.worlds.new("w")
scn.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.62, 0.52, 0.42, 1)
world.node_tree.nodes["Background"].inputs[1].default_value = 0.6


def sun(name, rot, energy, col, angle=0.25):
    li = bpy.data.lights.new(name, "SUN")
    li.energy = energy
    li.color = col
    li.angle = angle
    ob = bpy.data.objects.new(name, li)
    ob.rotation_euler = [math.radians(a) for a in rot]
    COL.objects.link(ob)


sun("key", (58, 0, 38), 5.5, (1.0, 0.93, 0.82))       # high, from the front-right of the camera
sun("rim", (115, 0, 200), 3.4, (1.0, 0.86, 0.68), 0.1)   # warm back rim
sun("fill", (80, 0, -70), 0.9, (0.85, 0.88, 1.0), 0.6)

# frame every mesh
mn = Vector((1e9, 1e9, 1e9))
mx = Vector((-1e9, -1e9, -1e9))
deps = bpy.context.evaluated_depsgraph_get()
for ob in scn.objects:
    if ob.type in ("MESH", "CURVE"):
        for c in ob.bound_box:
            w = ob.matrix_world @ Vector(c)
            mn = Vector((min(mn.x, w.x), min(mn.y, w.y), min(mn.z, w.z)))
            mx = Vector((max(mx.x, w.x), max(mx.y, w.y), max(mx.z, w.z)))
cam_d = bpy.data.cameras.new("cam")
cam_d.type = "ORTHO"
cx, cz = (mn.x + mx.x) / 2, (mn.z + mx.z) / 2
wv, hv = (mx.x - mn.x) * 1.10, (mx.z - mn.z) * 1.10
aspect = RES[0] / RES[1]
cam_d.ortho_scale = max(wv, hv * aspect) if aspect >= 1 else max(hv, wv / aspect)   # scale spans the longer side
cam = bpy.data.objects.new("cam", cam_d)
cam.location = (cx, -12, cz)
cam.rotation_euler = (math.radians(90), 0, 0)
COL.objects.link(cam)
scn.camera = cam

scn.render.engine = "CYCLES"
try:
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "METAL"
    prefs.get_devices()
    for d_ in prefs.devices:
        d_.use = True
    scn.cycles.device = "GPU"
except Exception as exc:                                    # CPU fallback
    print("ella3d: GPU not used:", exc)
scn.cycles.samples = SAMPLES
scn.cycles.use_denoising = True
scn.cycles.seed = SEED
scn.render.film_transparent = True
scn.render.resolution_x, scn.render.resolution_y = RES
scn.render.resolution_percentage = 100
scn.view_settings.view_transform = "Standard"
scn.view_settings.look = "None"
scn.render.image_settings.file_format = "PNG"
scn.render.image_settings.color_mode = "RGBA"
scn.render.filepath = OUT
scn.render.use_freestyle = True
scn.render.line_thickness = 1.25
vl = bpy.context.view_layer
vl.freestyle_settings.crease_angle = math.radians(120)
ls = vl.freestyle_settings.linesets.new("ink") if not vl.freestyle_settings.linesets else vl.freestyle_settings.linesets[0]
ls.select_silhouette = ls.select_border = ls.select_crease = True
ls.select_by_collection = True
ls.collection = HAIR_COL
ls.collection_negation = 'EXCLUSIVE'
if ls.linestyle is None:
    ls.linestyle = bpy.data.linestyles.new("ink")
ls.linestyle.color = (0.012, 0.010, 0.009)
ls.linestyle.thickness = 1.25
bpy.ops.render.render(write_still=True)


RAW = os.environ.get("ELLA_RAW")        # optional: keep the un-etched render here, to retune the ink pass alone
if RAW:
    shutil.copy(OUT, RAW)
etch(OUT)
