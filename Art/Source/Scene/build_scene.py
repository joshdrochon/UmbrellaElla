"""Blender builder for the scene art: paper, skyline (and the menu/scene composites in later rounds).

  Blender -b --factory-startup -P Art/Source/Scene/build_scene.py -- --piece paper|skyline --out <png> [--seed N] [--blend <file>]

Ink-and-paper NPR to the art bible: sepia paper field (stained, fibrous, never flat), etched wind strokes, near-black
rock/gothic skyline. Orthographic camera, emission only (no lighting model), Standard view transform.
Palette values are the style.json entries (paper-light/mid/stain, etch-line, silhouette).
"""
import math
import os
import random
import sys

import bpy

PAPER_LIGHT, PAPER_MID, PAPER_STAIN = "#aa8f7f", "#93786b", "#7b6157"
ETCH, SILHOUETTE = "#c4a999", "#1d1713"
UNITS_PER_PX = 0.01


def hexrgb(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4) for x in c]
    return (*lin, 1.0)


def args():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    o = {"seed": 7, "samples": 24}
    i = 0
    while i < len(a):
        o[a[i].lstrip("-")] = a[i + 1]
        i += 2
    return o


def reset(w, h, transparent):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            sc.render.engine = eng
            break
        except TypeError:
            continue
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = transparent
    sc.view_settings.view_transform = "Standard"
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA" if transparent else "RGB"
    cam = bpy.data.cameras.new("cam")
    cam.type = "ORTHO"
    cam.ortho_scale = w * UNITS_PER_PX
    co = bpy.data.objects.new("cam", cam)
    bpy.context.collection.objects.link(co)
    co.location = (w * UNITS_PER_PX / 2, -10, h * UNITS_PER_PX / 2)
    co.rotation_euler = (math.pi / 2, 0, 0)
    sc.camera = co
    return sc


def emission_mat(name, build):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(em.outputs[0], out.inputs[0])
    col = build(nt)
    nt.links.new(col, em.inputs[0])
    return m


def tex(nt, kind, scale, seed, mapping=(1, 1, 1), **kw):
    c = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = mapping
    mp.inputs["Location"].default_value = (seed * 3.7, seed * 1.3, seed * 2.1)
    nt.links.new(c.outputs["Object"], mp.inputs[0])
    n = nt.nodes.new(kind)
    if "Scale" in n.inputs:
        n.inputs["Scale"].default_value = scale
    for k, v in kw.items():
        if k.capitalize() in n.inputs:
            n.inputs[k.capitalize()].default_value = v
        else:
            setattr(n, k, v)
    nt.links.new(mp.outputs[0], n.inputs["Vector"])
    return n


def math_node(nt, op, a, b=None, clamp=False):
    n = nt.nodes.new("ShaderNodeMath")
    n.operation = op
    n.use_clamp = clamp
    for i, v in enumerate((a, b)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            n.inputs[i].default_value = v
        else:
            nt.links.new(v, n.inputs[i])
    return n.outputs[0]


def ramp(nt, fac, stops):
    r = nt.nodes.new("ShaderNodeValToRGB")
    el = r.color_ramp.elements
    while len(el) > 1:
        el.remove(el[-1])
    for i, (pos, col) in enumerate(stops):
        e = el[0] if i == 0 else el.new(pos)
        e.position = pos
        e.color = col if len(col) == 4 else (*col, 1.0)
    nt.links.new(fac, r.inputs["Fac"])
    return r.outputs["Color"]


def paper_color(nt, seed):
    """Stained mottled sepia: low-frequency stains + mid blotches + stretched fibres + fine grain."""
    stain = tex(nt, "ShaderNodeTexNoise", 3.0, seed, noise_dimensions="3D", detail=8.0, roughness=0.62)
    blot = tex(nt, "ShaderNodeTexNoise", 14.0, seed + 1, noise_dimensions="3D", detail=6.0, roughness=0.7)
    fibre_h = tex(nt, "ShaderNodeTexNoise", 160.0, seed + 2, mapping=(1.0, 0.04, 1.0), noise_dimensions="3D",
                  detail=3.0, roughness=0.6)
    fibre_v = tex(nt, "ShaderNodeTexNoise", 160.0, seed + 3, mapping=(0.04, 1.0, 1.0), noise_dimensions="3D",
                  detail=3.0, roughness=0.6)
    grain = tex(nt, "ShaderNodeTexNoise", 900.0, seed + 4, noise_dimensions="3D", detail=1.0, roughness=0.9)
    mott = math_node(nt, "ADD", math_node(nt, "MULTIPLY", stain.outputs["Fac"], 0.62),
                     math_node(nt, "MULTIPLY", blot.outputs["Fac"], 0.38))
    base = ramp(nt, math_node(nt, "SUBTRACT", math_node(nt, "MULTIPLY", mott, 2.4), 0.55, clamp=True),
                [(0.0, hexrgb(PAPER_STAIN)), (0.5, hexrgb(PAPER_MID)), (1.0, hexrgb(PAPER_LIGHT))])
    fib = math_node(nt, "ADD", fibre_h.outputs["Fac"], fibre_v.outputs["Fac"])
    shade = math_node(nt, "ADD", math_node(nt, "MULTIPLY", math_node(nt, "SUBTRACT", fib, 1.0), 0.55),
                      math_node(nt, "MULTIPLY", math_node(nt, "SUBTRACT", grain.outputs["Fac"], 0.5), 0.55))
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.blend_type = "ADD"
    mix.inputs["Fac"].default_value = 1.0
    nt.links.new(base, mix.inputs[1])
    sh = nt.nodes.new("ShaderNodeCombineColor")
    for k in ("Red", "Green", "Blue"):
        nt.links.new(math_node(nt, "MULTIPLY", shade, 0.16), sh.inputs[k])
    nt.links.new(sh.outputs[0], mix.inputs[2])
    return mix.outputs[0]


def add_plane(w, h, mat, y=0.0):
    me = bpy.data.meshes.new("plane")
    me.from_pydata([(0, 0, 0), (w * UNITS_PER_PX, 0, 0), (w * UNITS_PER_PX, 0, h * UNITS_PER_PX), (0, 0, h * UNITS_PER_PX)],
                   [], [(0, 1, 2, 3)])
    ob = bpy.data.objects.new("plane", me)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(mat)
    ob.location.y = y
    return ob


def curve_strand(pts, width, mat, y):
    cu = bpy.data.curves.new("strand", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = width * UNITS_PER_PX / 2
    cu.bevel_resolution = 1
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for p, (x, z) in zip(sp.points, pts):
        p.co = (x * UNITS_PER_PX, 0, z * UNITS_PER_PX, 1)
    ob = bpy.data.objects.new("strand", cu)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(mat)
    ob.location.y = y
    return ob


def wind_bands(w, h, rnd, mat, seeds):
    """Etched wavy parallel strokes in bands (key art: top, bottom-left, bottom-right), periodic over w."""
    for (zc, amp, n, gap, phase) in seeds:
        k = rnd.choice((1, 2)) * 2 * math.pi / w
        for i in range(n):
            off = (i - n / 2) * gap
            pts = []
            for x in range(0, w + 1, 16):
                z = (zc + off + amp * math.sin(k * x + phase + i * 0.045) + amp * 0.45 * math.sin(2.7 * k * x + phase * 1.7)
                     + off * 0.25 * math.sin(k * 2 * x))
                pts.append((x, z))
            curve_strand(pts, rnd.choice((1.0, 1.2, 1.6)), mat, -1.0)


def sparkles(w, h, rnd, mat, n):
    for _ in range(n):
        x, z = rnd.uniform(40, w - 40), rnd.uniform(h * 0.12, h * 0.9)
        r = rnd.uniform(5, 13)
        curve_strand([(x + r * math.cos(a), z + r * math.sin(a)) for a in [i * 2 * math.pi / 24 for i in range(25)]], 1.1, mat, -1.0)
        curve_strand([(x + r * 0.45 * math.cos(a), z + r * 0.45 * math.sin(a)) for a in [i * 2 * math.pi / 16 for i in range(17)]], 0.8, mat, -1.0)


def build_paper(o, rnd):
    w, h = 3200, 1080
    sc = reset(w, h, False)
    seed = int(o["seed"])
    add_plane(w, h, emission_mat("paper", lambda nt: paper_color(nt, seed)), y=1.0)
    etch = emission_mat("etch", lambda nt: nt.nodes.new("ShaderNodeRGB") and _rgb(nt, ETCH))
    wind_bands(w, h, rnd, etch, [(h * 0.80, 34, 9, 7.5, 0.4), (h * 0.20, 40, 12, 8.5, 2.2)])
    sparkles(w, h, rnd, emission_mat("spark", lambda nt: _rgb(nt, "#e9dfd2")), 14)
    return sc, w, h


def _rgb(nt, hexc):
    n = nt.nodes.new("ShaderNodeRGB")
    n.outputs[0].default_value = hexrgb(hexc)
    return n.outputs[0]


def skyline_profile(w, rnd):
    """Jagged rock mesas with a few gothic spires; returns a polyline of (x, height px)."""
    pts, x = [], 0.0
    hgt = 95.0
    while x < w:
        step = rnd.uniform(40, 150)
        kind = rnd.random()
        if kind < 0.28:      # mesa: flat top, steep sides
            top = rnd.uniform(110, 230)
            pts += [(x, hgt), (x + 6, top - 18), (x + 14, top), (x + step * 0.8, top + rnd.uniform(-6, 6)), (x + step * 0.8 + 10, top - 30)]
            hgt = top - 40
        elif kind < 0.5:     # spire
            base = hgt
            sx = x + step * 0.4
            pts += [(x, base), (sx - 8, base + 6), (sx - 3, base + rnd.uniform(110, 210)), (sx + 3, base + 6), (x + step, base - 8)]
            hgt = base - 8
        elif kind < 0.7:     # broken ridge
            for j in range(4):
                pts.append((x + step * j / 4, hgt + rnd.uniform(-45, 55)))
            hgt = hgt + rnd.uniform(-20, 20)
        else:                # slope down to a gap
            pts += [(x, hgt), (x + step * 0.5, hgt - rnd.uniform(25, 60)), (x + step, rnd.uniform(70, 130))]
            hgt = rnd.uniform(70, 130)
        hgt = max(60.0, min(hgt, 240.0))
        x += step
    pts = [(min(max(px, 0), w), max(30.0, min(hh, 330.0))) for px, hh in pts]
    pts.sort(key=lambda p: p[0])
    return pts


def poly(pts, mat, y):
    me = bpy.data.meshes.new("poly")
    me.from_pydata([(x * UNITS_PER_PX, 0, z * UNITS_PER_PX) for x, z in pts], [], [list(range(len(pts)))])
    ob = bpy.data.objects.new("poly", me)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(mat)
    ob.location.y = y
    return ob


def pointed_arch(cx, z0, w, hh, n=10):
    """Pointed (gothic) arch outline, base centre cx, springing at z0, total height hh."""
    r = w
    pts = [(cx - w / 2, z0), (cx - w / 2, z0 + hh * 0.55)]
    for i in range(1, n):
        t = i / n
        pts.append((cx - w / 2 + w * t / 2 + 0 * t, z0 + hh * 0.55 + (hh * 0.45) * math.sin(t * math.pi / 2) ** 0.8))
    pts.append((cx, z0 + hh))
    for (x, z) in reversed(pts[2:-1]):
        pts.append((2 * cx - x, z))
    pts += [(cx + w / 2, z0 + hh * 0.55), (cx + w / 2, z0)]
    return pts


class Sky:
    def __init__(self, ink, glow, y):
        self.ink, self.glow, self.y = ink, glow, y

    def block(self, x, w, h, rnd, roof=None, y=0.0):
        """Building body + steep gable/hip roof, dormers, chimneys, lit pointed windows."""
        poly([(x, 0), (x, h), (x + w, h), (x + w, 0)], self.ink, self.y)
        rh = roof if roof is not None else w * rnd.uniform(0.5, 1.1)
        style = rnd.random()
        rustmat = getattr(self, "rust", None)
        rm = rustmat if (rustmat is not None and rnd.random() < 0.22) else self.ink
        if style < 0.55:
            poly([(x - w * 0.06, h - 2), (x + w / 2, h + rh), (x + w * 1.06, h - 2)], rm, self.y)
        else:
            poly([(x - w * 0.05, h - 2), (x + w * 0.2, h + rh * 0.7), (x + w * 0.8, h + rh * 0.7), (x + w * 1.05, h - 2)], rm, self.y)
        for k in range(rnd.randint(0, 3)):    # chimneys
            cx = x + w * rnd.uniform(0.1, 0.85)
            poly([(cx, h), (cx, h + rh * 0.8 + 10), (cx + 5, h + rh * 0.8 + 10), (cx + 5, h)], self.ink, self.y)
            poly([(cx - 1.5, h + rh * 0.8 + 10), (cx - 1.5, h + rh * 0.8 + 14), (cx + 6.5, h + rh * 0.8 + 14), (cx + 6.5, h + rh * 0.8 + 10)], self.ink, self.y)
        det = getattr(self, "detail", None)
        if det is not None:
            for t in range(1, 7):      # roof tile courses
                f = t / 7.0
                half = (w * 1.06 / 2) * (1 - f) if style < 0.55 else (w * 0.85 / 2)
                zz = h + rh * f * (1.0 if style < 0.55 else 0.7)
                if half > 2:
                    curve_strand([(x + w / 2 - half, zz), (x + w / 2 + half, zz)], 1.0, det, self.y - 0.2)
            for gx in range(1, int(w // 9)):   # eave brackets / wall courses
                curve_strand([(x + gx * 9, h - 6), (x + gx * 9, h - 1)], 0.6, det, self.y - 0.2)
            for row in range(1, int(h // 11)):  # stone courses
                curve_strand([(x + 1, row * 11.0), (x + w - 1, row * 11.0)], 0.8, det, self.y - 0.2)
        pwin = rnd.uniform(0.18, 0.7)                 # each house its own lit density
        wh = rnd.choice((14, 20, 20, 30))            # window height: squat, normal, tall lancet
        gap = wh + rnd.choice((6, 10, 16))
        nwin = max(1, int(w // rnd.choice((10, 13, 18))))
        for i in range(nwin):
            for row in range(max(1, int((h - 70) // gap))):
                if rnd.random() < pwin:
                    wx = x + (i + 0.5) * w / nwin
                    pw = min(10.0 if wh < 30 else 7.0, w / nwin * 0.62)
                    z0 = 76 + row * gap
                    if z0 + wh > h - 4:
                        continue
                    poly(pointed_arch(wx, z0, pw, wh), self.glow, self.y - 0.1)
                    if det is not None:     # muntins: dark bars across the lit window
                        curve_strand([(wx, z0), (wx, z0 + wh)], 0.9, self.ink, self.y - 0.3)
                        curve_strand([(wx - pw / 2, z0 + wh * 0.45), (wx + pw / 2, z0 + wh * 0.45)], 0.8, self.ink, self.y - 0.3)
        if style >= 0.8 and w > 34:      # side turret with its own pinnacle
            tx = x + (w - 9 if rnd.random() < 0.5 else 2)
            poly([(tx, h - 10), (tx, h + rh * 0.9), (tx + 7, h + rh * 0.9), (tx + 7, h - 10)], self.ink, self.y - 0.04)
            poly([(tx - 2, h + rh * 0.9 - 1), (tx + 3.5, h + rh * 0.9 + 26), (tx + 9, h + rh * 0.9 - 1)], self.ink, self.y - 0.04)
        if style < 0.55 and w > 30:     # dormer on the roof face
            dx = x + w * rnd.uniform(0.3, 0.7)
            dz = h + rh * 0.28
            poly([(dx - 7, dz), (dx - 7, dz + 11), (dx, dz + 22), (dx + 7, dz + 11), (dx + 7, dz)], self.ink, self.y - 0.05)
            poly(pointed_arch(dx, dz + 1, 6, 12), self.glow, self.y - 0.1)

    def spire(self, cx, base, w, hh, rnd, clock=False):
        poly([(cx - w / 2, 0), (cx - w / 2, base), (cx + w / 2, base), (cx + w / 2, 0)], self.ink, self.y)
        poly([(cx - w * 0.62, base - 2), (cx, base + hh), (cx + w * 0.62, base - 2)], self.ink, self.y)
        poly([(cx - 1.2, base + hh - 2), (cx - 1.2, base + hh + 18), (cx + 1.2, base + hh + 18), (cx + 1.2, base + hh - 2)], self.ink, self.y)
        poly([(cx - 5, base + hh + 11), (cx - 5, base + hh + 13), (cx + 5, base + hh + 13), (cx + 5, base + hh + 11)], self.ink, self.y)
        for side in (-1, 1):   # pinnacles
            px = cx + side * w * 0.72
            poly([(px - 4, base - 20), (px, base + hh * 0.35), (px + 4, base - 20)], self.ink, self.y)
        if clock:
            n = 24
            cz = base * 0.7
            poly([(cx + 15 * math.cos(2 * math.pi * i / n), cz + 15 * math.sin(2 * math.pi * i / n)) for i in range(n)], self.glow, self.y - 0.1)
            curve_strand([(cx, cz), (cx, cz + 11)], 1.3, self.ink, self.y - 0.3)
            curve_strand([(cx, cz), (cx + 8, cz - 3)], 1.3, self.ink, self.y - 0.3)
        else:
            poly(pointed_arch(cx, base * 0.45, w * 0.35, base * 0.45), self.glow, self.y - 0.1)

    def arcade(self, x, w, h, rnd):
        """Viaduct: a deck on pointed arches."""
        poly([(x, h), (x, h + 7), (x + w, h + 7), (x + w, h)], self.ink, self.y)
        n = max(2, int(w // 26))
        for i in range(n + 1):
            px = x + i * w / n
            poly([(px - 3, 0), (px - 3, h), (px + 3, h), (px + 3, 0)], self.ink, self.y)
        poly([(x, 0), (x, 20), (x + w, 20), (x + w, 0)], self.ink, self.y)
        for i in range(n):
            cxm = x + (i + 0.5) * w / n
            curve_strand([(cxm - w / n * 0.42 + w / n * 0.84 * t / 10.0, h - 4 - 9 * (1 - abs(t - 5) / 5.0) * -1 - 12 + 12 * 0) for t in range(11)], 3.0, self.ink, self.y - 0.1)


def gothic_layer(w, rnd, sk, hscale=1.0, dense=1.0):
    x = -20.0
    while x < w + 20:
        r = rnd.random()
        if r < 0.12:
            ww = rnd.uniform(26, 40)
            sk.spire(x + ww / 2, rnd.uniform(170, 240) * hscale, ww * 0.6, rnd.uniform(130, 230) * hscale, rnd, clock=rnd.random() < 0.4)
            x += ww
        elif r < 0.22:
            ww = rnd.uniform(70, 150)
            sk.arcade(x, ww, rnd.uniform(92, 120), rnd)
            x += ww - 4
        elif r < 0.3:   # dome / conservatory
            ww = rnd.uniform(50, 80)
            h0 = rnd.uniform(120, 150) * hscale
            poly([(x, 0), (x, h0), (x + ww, h0), (x + ww, 0)], sk.ink, sk.y)
            n = 16
            poly([(x + ww / 2 + ww / 2 * math.cos(math.pi * i / n), h0 + ww * 0.45 * math.sin(math.pi * i / n)) for i in range(n + 1)], sk.ink, sk.y)
            poly([(x + ww / 2 - 1, h0 + ww * 0.45), (x + ww / 2, h0 + ww * 0.45 + 20), (x + ww / 2 + 1, h0 + ww * 0.45)], sk.ink, sk.y)
            x += ww
        else:
            if rnd.random() < 0.22:      # wide manor: three gables of different height
                ww = rnd.uniform(110, 170)
                hh0 = rnd.uniform(120, 200) * hscale
                for k, (fx, fw, fh) in enumerate(((0.0, 0.36, 0.8), (0.3, 0.4, 1.0), (0.64, 0.36, 0.75))):
                    sk.block(x + ww * fx, ww * fw, hh0 * fh, rnd)
                x += ww * 0.95
            else:
                ww = rnd.uniform(34, 72)
                sk.block(x, ww, rnd.uniform(110, 235) * hscale, rnd)
                x += ww * rnd.uniform(0.7, 1.0)
    # central cathedral
    cx = w * 0.5
    sk.spire(cx, 290, 76, 300, rnd)
    for d in (-1, 1):
        sk.spire(cx + d * 76, 230, 36, 160, rnd)
        sk.block(cx + d * 140 - 30, 90, 190, rnd, roof=70)
        for k in range(3):    # flying buttress: arc from nave wall up to the central spire
            x0, x1 = cx + d * (40 + 22 * k), cx + d * 8
            curve_strand([(x0 + (x1 - x0) * t / 12.0, 150 + 70 * k + 55 * math.sin(math.pi * t / 24.0)) for t in range(13)], 4.0, sk.ink, sk.y - 0.2)


def ink_lines(sc, hexc, px):
    sc.render.use_freestyle = True
    sc.render.line_thickness_mode = "ABSOLUTE"
    sc.render.line_thickness = px
    vl = sc.view_layers[0]
    vl.use_freestyle = True
    fs = vl.freestyle_settings
    ls = fs.linesets[0] if len(fs.linesets) else fs.linesets.new("ink")
    ls.select_by_visibility = True
    ls.select_silhouette = ls.select_border = ls.select_crease = True
    if ls.linestyle is None:
        ls.linestyle = bpy.data.linestyles.new("ink")
    ls.linestyle.color = hexrgb(hexc)[:3]
    ls.linestyle.thickness = px


def build_skyline(o, rnd):
    w, h = 3200, 720
    sc = reset(w, h, True)
    seed = int(o["seed"])

    def ink_col(nt):
        g = tex(nt, "ShaderNodeTexNoise", 900.0, seed, noise_dimensions="3D", detail=3.0)
        v = tex(nt, "ShaderNodeTexNoise", 40.0, seed + 5, noise_dimensions="3D", detail=4.0)
        c = nt.nodes.new("ShaderNodeTexCoord")
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (1, 1, 1)
        nt.links.new(c.outputs["Object"], mp.inputs[0])
        br = nt.nodes.new("ShaderNodeTexBrick")
        br.inputs["Scale"].default_value = 85.0
        br.inputs["Mortar Size"].default_value = 0.05
        br.inputs["Brick Width"].default_value = 0.6
        br.inputs["Row Height"].default_value = 0.22
        br.inputs["Color1"].default_value = hexrgb("#2c221b")
        br.inputs["Color2"].default_value = hexrgb("#1f1813")
        br.inputs["Mortar"].default_value = hexrgb("#0b0807")
        nt.links.new(mp.outputs[0], br.inputs["Vector"])
        hs = nt.nodes.new("ShaderNodeMixRGB")
        hs.blend_type = "MULTIPLY"
        hs.inputs["Fac"].default_value = 1.0
        nt.links.new(br.outputs["Color"], hs.inputs[1])
        nt.links.new(ramp(nt, math_node(nt, "ADD", g.outputs["Fac"], v.outputs["Fac"]),
                          [(0.4, hexrgb("#9a8b80")), (1.4 / 2, hexrgb("#ffffff"))]), hs.inputs[2])
        return hs.outputs[0]

    def gold_col(nt):
        g = tex(nt, "ShaderNodeTexNoise", 400.0, seed + 6, noise_dimensions="3D", detail=2.0)
        return ramp(nt, g.outputs["Fac"], [(0.0, hexrgb("#c8a257")), (1.0, hexrgb("#e9c46a"))])
    ink = emission_mat("ink", ink_col)
    far = emission_mat("far", lambda nt: _rgb(nt, "#2b211b"))
    gold = emission_mat("gold", gold_col)
    detail = emission_mat("detail", lambda nt: _rgb(nt, "#70594a"))
    gothic_layer(w, random.Random(seed + 100), Sky(far, far, -0.5), hscale=0.8)
    near = Sky(ink, gold, -1.0)
    near.detail = detail
    near.rust = emission_mat("rust", lambda nt: _rgb(nt, "#8a331f"))
    gothic_layer(w, random.Random(seed), near)
    poly([(0, -4), (0, 86), (w, 86), (w, -4)], ink, -1.2)   # solid ground band
    rg = random.Random(seed + 7)
    zc = 0.0
    while zc < 84:      # irregular rubble courses: uneven height, jittered joints, a few arched openings
        ch = rg.uniform(11, 25)
        zc += ch
        curve_strand([(0, zc)] + [(xx, zc + rg.uniform(-1.6, 1.6)) for xx in range(60, w, 60)] + [(w, zc)], 0.9, detail, -1.4)
        xj = rg.uniform(0, 30)
        while xj < w:
            curve_strand([(xj, zc - ch), (xj + rg.uniform(-2, 2), zc)], 0.8, detail, -1.4)
            xj += rg.uniform(14, 62)
    for k in range(int(w // 260)):
        ax = rg.uniform(40, w - 40)
        curve_strand([(ax - 14 + 28 * t / 14.0, 30 + 26 * math.sin(math.pi * t / 14.0) ** 0.7) for t in range(15)], 1.4, detail, -1.45)
    ink_lines(sc, "#4a3a2f", 1.0)
    return sc, w, h


def _smooth_field(rng, h, w, cell, amp):
    """Low-frequency random field (bilinear up-sampled grid), values in [-amp, amp]."""
    import numpy as np
    gh, gw = h // cell + 3, w // cell + 3
    g = rng.uniform(-amp, amp, (gh, gw))
    ys, xs = np.arange(h) / cell, np.arange(w) / cell
    y0, x0 = ys.astype(int), xs.astype(int)
    fy, fx = (ys - y0)[:, None], (xs - x0)[None, :]
    a, b = g[y0][:, x0], g[y0][:, x0 + 1]
    c, d = g[y0 + 1][:, x0], g[y0 + 1][:, x0 + 1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def _blur(a, r):
    import numpy as np
    k = np.ones(2 * r + 1) / (2 * r + 1)
    for ax in (0, 1):
        a = np.apply_along_axis(lambda v: np.convolve(np.pad(v, r, mode="edge"), k, mode="valid"), ax, a)
    return a


def etch_post(path, seed, mode):
    """Hand-made finish on a render: edge jitter, ink bleed, paper grain, hatching, rim light, window glow."""
    import numpy as np
    img = bpy.data.images.load(path)
    w, h = img.size
    px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)[::-1].copy()   # top row first
    rng = np.random.default_rng(seed)
    # 1. hand jitter: displace sampling coords by two noise scales (wobbly, slightly torn edges)
    dx = _smooth_field(rng, h, w, 9, 1.0) + _smooth_field(rng, h, w, 3, 0.4)
    dy = _smooth_field(rng, h, w, 9, 1.0) + _smooth_field(rng, h, w, 3, 0.4)
    yy, xx = np.mgrid[0:h, 0:w]
    sy = np.clip((yy + dy).round().astype(int), 0, h - 1)
    sx = np.clip((xx + dx).round().astype(int), 0, w - 1)
    px = px[sy, sx]
    a = px[..., 3]
    rgb = px[..., :3]
    lum = rgb.mean(axis=2)
    gold = (a > 0.5) & (rgb[..., 0] > 0.45) & (rgb[..., 2] < 0.45) & (rgb[..., 1] > 0.6 * rgb[..., 0])
    ink = (a > 0.5) & ~gold
    rust = ink & (rgb[..., 0] > 1.5 * rgb[..., 1]) & (rgb[..., 0] > 1.9 * rgb[..., 2]) & (rgb[..., 0] > 0.14) & (rgb[..., 1] < 0.6 * rgb[..., 0])
    strand = np.clip((lum - 0.10) / 0.22, 0, 1) * ink   # lighter etched strands survive the ink pass
    # 2. ink bleed: ragged alpha edge from fine noise on a slightly blurred mask
    ragged = _blur(a, 1) + rng.normal(0, 0.09, a.shape)
    a = np.clip((ragged - 0.45) * 4.0, 0, 1) * (a > 0.02)
    # 3. ink variation + paper grain + fibres in the dark mass
    grain = rng.normal(0, 1, (h, w)).astype(np.float32)
    fib = _blur(rng.normal(0, 1, (h, w)), 1) * 0 + np.repeat(rng.normal(0, 1, (h, w // 12 + 1)), 12, axis=1)[:, :w]
    blot = _smooth_field(rng, h, w, 40, 1.0) + _smooth_field(rng, h, w, 11, 0.6)
    tone = 1.0 + (0.16 + 0.22 * (yy > h - 90)) * blot + 0.10 * grain + 0.05 * fib
    # 4. hatching: diagonal engraved lines, stronger toward the roofline (top of each mass)
    hatch = ((xx * 0.8 + yy * 1.0) % 4.0 < 1.1).astype(np.float32)
    cross = ((xx * -0.8 + yy * 1.0) % 7.0 < 0.9).astype(np.float32)
    inkc = np.array([0.045, 0.034, 0.027])
    base = inkc[None, None, :] * tone[..., None]
    lines = (0.55 * hatch + 0.35 * cross)[..., None] * np.array([0.10, 0.075, 0.058])[None, None, :]
    dark = base + lines * (0.6 + 0.4 * np.clip(blot + 0.5, 0, 1))[..., None]
    # 5. rim light: warm edge on inner top boundary of ink
    up = np.zeros_like(a)
    up[3:] = a[:-3]
    rim = np.clip(a - up, 0, 1) * (a > 0.5)
    rim = _blur(rim, 1) * 1.2
    dark = dark + rim[..., None] * np.array([0.30, 0.20, 0.13])[None, None, :]
    dark = dark * (1 - strand[..., None]) + rgb * strand[..., None] * 1.05
    rcol = np.array([0.30, 0.095, 0.060])[None, None, :] * (0.7 + 0.5 * np.clip(blot + 0.5, 0, 1))[..., None] + lines * 0.8
    dark = np.where(rust[..., None], rcol, dark)
    gb = np.clip((yy - (h - 86)) / 86.0, 0, 1)    # ground band: lighter umber toward the foot, depth from the mid-tone
    dark = dark + (gb * (blot * 0.5 + 0.5) * 0.035)[..., None] * np.array([1.0, 0.8, 0.65])[None, None, :]
    out = np.where(ink[..., None], dark, rgb)
    # 6. window glow: gold stays bright with grain; soft halo bleeds into the ink
    halo = _blur(gold.astype(np.float32), 4)
    out = out + (halo * (~gold) * (a > 0.5))[..., None] * np.array([0.22, 0.17, 0.07])[None, None, :]
    gcol = np.array([0.91, 0.77, 0.42])[None, None, :] * (0.90 + 0.10 * np.clip(grain * 0.5 + 0.5, 0, 1))[..., None]
    out = np.where(gold[..., None], gcol, out)
    res = np.concatenate([np.clip(out, 0, 1), a[..., None]], axis=2)[::-1]
    img.pixels = res.astype(np.float32).ravel().tolist()
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()


PIECES = {"paper": build_paper, "skyline": build_skyline}


def main():
    o = args()
    rnd = random.Random(int(o["seed"]))
    sc, w, h = PIECES[o["piece"]](o, rnd)
    sc.render.filepath = os.path.abspath(o["out"])
    try:
        sc.eevee.taa_render_samples = int(o["samples"])
    except AttributeError:
        pass
    bpy.ops.render.render(write_still=True)
    if o["piece"] == "skyline" and "raw" not in o:
        etch_post(sc.render.filepath, int(o["seed"]), o["piece"])
    if "blend" in o:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(o["blend"]), check_existing=False)
    print("SCENE_RENDER piece=%s size=%dx%d version=%s" % (o["piece"], w, h, bpy.app.version_string.split()[0]))


if __name__ == "__main__":
    main()
