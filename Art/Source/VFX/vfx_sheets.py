"""Blender builder for the VFX sheets (art lane artfx). Blender only: every pixel is rendered by Blender.

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P Art/Source/VFX/vfx_sheets.py -- [--only NAME ...] [--cell 128]

Each sheet is one row of 8 square cells (the grid Source/UmbrellaElla/Public/Feedback/Vfx/VfxCatalog.h expects). A sheet is
a list of flat emissive layers per frame (core, shell, trail: pipeline/art/references.json vfx_spec), drawn with the GDD SH1.0
shot colours. Output: Art/Source/VFX/Raw/<Sheet>_PH.png (tracked placeholders until the art loop passes them) and one still
per sheet under Raw/Stills/ for the blind panel.
"""
import math
import os
import random
import sys

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "Raw")
FRAMES = 8

CORE, GOLD, AMBER, YSHADOW = "FFF5DC", "E9C46A", "F5AA28", "94611E"
YELLOW = "FFD84A"
RED, CORAL, RSHADOW = "FF3658", "FF7848", "8F173C"
INK, ASH, PALE = "171614", "8FA3B0", "C9CED2"


def lin(hexs):
    out = []
    for i in (0, 2, 4):
        c = int(hexs[i:i + 2], 16) / 255.0
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return out


# ---------- Blender plumbing ----------
def setup(cell):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            sc.render.engine = eng
            break
        except TypeError:
            continue
    sc.render.resolution_x = sc.render.resolution_y = cell
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.render.image_settings.color_depth = "8"
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    try:
        sc.eevee.taa_render_samples = 16
    except AttributeError:
        pass
    sc.render.filter_size = 1.2
    cam_data = bpy.data.cameras.new("Cam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = 2.0
    cam = bpy.data.objects.new("Cam", cam_data)
    cam.location = (0.0, 0.0, 10.0)
    sc.collection.objects.link(cam)
    sc.camera = cam
    world = bpy.data.worlds.new("W")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0, 0, 0, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.0
    sc.world = world
    return sc


def unit_mesh(shape, arg):
    if shape == "disc":
        vs = [(math.cos(a), math.sin(a), 0) for a in [2 * math.pi * i / 48 for i in range(48)]]
        return vs, [list(range(48))]
    if shape == "ring":
        n, inner = 64, arg
        vs = [(math.cos(2 * math.pi * i / n), math.sin(2 * math.pi * i / n), 0) for i in range(n)]
        vs += [(inner * x, inner * y, 0) for x, y, _ in vs[:n]]
        return vs, [[i, (i + 1) % n, n + (i + 1) % n, n + i] for i in range(n)]
    if shape == "star":
        n, inner = arg
        vs = [(0, 0, 0)]
        for i in range(2 * n):
            r = 1.0 if i % 2 == 0 else inner
            a = math.pi * i / n
            vs.append((r * math.cos(a), r * math.sin(a), 0))
        return vs, [[0, 1 + i, 1 + (i + 1) % (2 * n)] for i in range(2 * n)]
    if shape == "kite":  # pointed angular head, tip at +X
        back = arg if arg else 0.6
        return [(1, 0, 0), (0, 0.5, 0), (-back, 0, 0), (0, -0.5, 0)], [[0, 1, 2, 3]]
    if shape == "quad":
        return [(-1, -1, 0), (1, -1, 0), (1, 1, 0), (-1, 1, 0)], [[0, 1, 2, 3]]
    if shape == "taper":  # trail: wide at +X, a point at -X
        return [(1, 0.5, 0), (-1, 0, 0), (1, -0.5, 0)], [[0, 1, 2]]
    if shape == "arc":  # a slash: a thick arc from -arg to +arg radians, tapered ends
        n, half = 24, arg
        vs, fs = [], []
        for i in range(n + 1):
            u = i / n
            a = -half + 2 * half * u
            w = 0.16 * math.sin(math.pi * u) + 0.005
            vs.append(((1 + w) * math.cos(a), (1 + w) * math.sin(a), 0))
            vs.append(((1 - w) * math.cos(a), (1 - w) * math.sin(a), 0))
        for i in range(n):
            fs.append([2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1])
        return vs, fs
    raise ValueError(shape)


_mats = {}


def material(ramp, mode, hatch, hatch_scale, hatch_phase, cut=False, grain=True):
    """ramp: [(pos, hex, alpha)...]; mode: radial | x | y | flat."""
    key = (tuple(ramp), mode, round(hatch, 3), hatch_scale, round(hatch_phase, 3), cut, grain)
    if key in _mats:
        return _mats[key]
    m = bpy.data.materials.new("M")
    m.use_nodes = True
    try:
        m.surface_render_method = "BLENDED"
    except AttributeError:
        m.blend_method = "BLEND"
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    mix = nt.nodes.new("ShaderNodeMixShader")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    em = nt.nodes.new("ShaderNodeEmission")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.interpolation = "LINEAR"
    els = cr.color_ramp.elements
    while len(els) > 1:
        els.remove(els[-1])
    for i, (pos, hexs, alpha) in enumerate(ramp):
        e = els[0] if i == 0 else els.new(pos)
        e.position = pos
        e.color = (*lin(hexs), alpha)
    if mode == "radial":
        ln = nt.nodes.new("ShaderNodeVectorMath")
        ln.operation = "LENGTH"
        nt.links.new(tc.outputs["Object"], ln.inputs[0])
        nt.links.new(ln.outputs["Value"], cr.inputs["Fac"])
    elif mode in ("x", "y"):
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs["From Min"].default_value = -1.0
        mr.inputs["From Max"].default_value = 1.0
        nt.links.new(tc.outputs["Object"], sep.inputs[0])
        nt.links.new(sep.outputs["X" if mode == "x" else "Y"], mr.inputs["Value"])
        nt.links.new(mr.outputs["Result"], cr.inputs["Fac"])
    else:
        cr.inputs["Fac"].default_value = 0.0
    alpha_out = cr.outputs["Alpha"]
    color_out = cr.outputs["Color"]

    def ink_mix(fac_socket, amount):
        """Blend the colour toward ink where fac is set: etched lines and grain are ink, not holes."""
        nonlocal color_out
        amt = nt.nodes.new("ShaderNodeMath")
        amt.operation = "MULTIPLY"
        amt.inputs[1].default_value = amount
        nt.links.new(fac_socket, amt.inputs[0])
        mx = nt.nodes.new("ShaderNodeMix")
        mx.data_type = "RGBA"
        nt.links.new(amt.outputs[0], mx.inputs[0])
        nt.links.new(color_out, mx.inputs[6])
        mx.inputs[7].default_value = (*lin(INK), 1.0)
        color_out = mx.outputs[2]

    if hatch > 0.0:
        # Etched hatching: thin diagonal ink lines engraved into the shape (cut=True: cut out of a veil instead).
        wave = nt.nodes.new("ShaderNodeTexWave")
        wave.wave_type = "BANDS"
        wave.bands_direction = "DIAGONAL"
        wave.inputs["Scale"].default_value = hatch_scale
        wave.inputs["Distortion"].default_value = 1.5
        wave.inputs["Detail"].default_value = 1.0
        wave.inputs["Phase Offset"].default_value = hatch_phase
        nt.links.new(tc.outputs["Object"], wave.inputs["Vector"])
        gt = nt.nodes.new("ShaderNodeMath")
        gt.operation = "GREATER_THAN"
        gt.inputs[1].default_value = 0.72
        nt.links.new(wave.outputs["Fac"], gt.inputs[0])
        if cut:
            cutn = nt.nodes.new("ShaderNodeMath")
            cutn.operation = "MULTIPLY"
            cutn.inputs[1].default_value = hatch
            nt.links.new(gt.outputs[0], cutn.inputs[0])
            inv = nt.nodes.new("ShaderNodeMath")
            inv.operation = "SUBTRACT"
            inv.inputs[0].default_value = 1.0
            nt.links.new(cutn.outputs[0], inv.inputs[1])
            mul = nt.nodes.new("ShaderNodeMath")
            mul.operation = "MULTIPLY"
            nt.links.new(cr.outputs["Alpha"], mul.inputs[0])
            nt.links.new(inv.outputs[0], mul.inputs[1])
            alpha_out = mul.outputs[0]
        else:
            ink_mix(gt.outputs[0], min(1.0, hatch + 0.25))
    if grain:
        # Paper grain: fine ink speckle over every painted area.
        noise = nt.nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 55.0
        noise.inputs["Detail"].default_value = 3.0
        nt.links.new(tc.outputs["Object"], noise.inputs["Vector"])
        sp = nt.nodes.new("ShaderNodeMath")
        sp.operation = "GREATER_THAN"
        sp.inputs[1].default_value = 0.6
        nt.links.new(noise.outputs[0], sp.inputs[0])
        ink_mix(sp.outputs[0], 0.22)
    nt.links.new(color_out, em.inputs["Color"])
    nt.links.new(alpha_out, mix.inputs["Fac"])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    _mats[key] = m
    return m


def L(shape, x=0.0, y=0.0, sx=1.0, sy=None, rot=0.0, ramp=None, mode="flat", arg=None, hatch=0.0, hs=9.0, hp=0.0, a=1.0, ink=0.0, cut=False):
    """One layer. a scales every ramp alpha."""
    ramp = [(p, h, al * a) for p, h, al in (ramp or [(0.0, CORE, 1.0)])]
    return dict(shape=shape, x=x, y=y, sx=sx, sy=sx if sy is None else sy, rot=rot, ramp=ramp, mode=mode, arg=arg, hatch=hatch, hs=hs, hp=hp, ink=ink, cut=cut)


def render_frame(sc, layers, path):
    for ob in [o for o in sc.collection.objects if o.type == "MESH"]:
        me = ob.data
        bpy.data.objects.remove(ob, do_unlink=True)
        bpy.data.meshes.remove(me)
    drawn = []
    for ly in layers:
        if ly["ink"] > 0.0:
            # The ink line: the same shape, a little larger, in near-black behind it.
            top = max(al for _, _, al in ly["ramp"])
            drawn.append(dict(ly, sx=ly["sx"] + math.copysign(ly["ink"], ly["sx"]), sy=ly["sy"] + math.copysign(ly["ink"], ly["sy"]),
                              ramp=[(0.0, INK, top)], mode="flat", hatch=0.0, ink=0.0, cut=False))
        drawn.append(ly)
    for i, ly in enumerate(drawn):
        if min(abs(ly["sx"]), abs(ly["sy"])) < 1e-4 or max(al for _, _, al in ly["ramp"]) <= 0.003:
            continue
        vs, fs = unit_mesh(ly["shape"], ly["arg"])
        me = bpy.data.meshes.new("m")
        me.from_pydata(vs, [], fs)
        ob = bpy.data.objects.new("o", me)
        ob.location = (ly["x"], ly["y"], 0.01 * i)
        ob.scale = (ly["sx"], ly["sy"], 1.0)
        ob.rotation_euler = (0.0, 0.0, ly["rot"])
        soft = ly["mode"] != "flat" and min(al for _, _, al in ly["ramp"]) <= 0.003
        me.materials.append(material(ly["ramp"], ly["mode"], ly["hatch"], ly["hs"], ly["hp"], ly["cut"], not soft and not ly["cut"]))
        sc.collection.objects.link(ob)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


def read_png(path):
    img = bpy.data.images.load(path)
    w, h = img.size
    px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)[::-1]
    bpy.data.images.remove(img)
    return px


def write_png(px, path):
    h, w, _ = px.shape
    img = bpy.data.images.new("out", w, h, alpha=True)
    img.alpha_mode = "STRAIGHT"
    img.pixels = px[::-1].reshape(-1).tolist()
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)


# ---------- ramps ----------
def core_shell(core, shell, edge, a=1.0, soft=True):
    return [(0.0, core, a), (0.35, core, a), (0.6, shell, a), (0.92, edge, a * (0.85 if soft else 1.0)), (1.0, edge, 0.0 if soft else a)]


def glow(hexs, a):
    return [(0.0, hexs, a), (1.0, hexs, 0.0)]


def flat(hexs, a=1.0):
    return [(0.0, hexs, a)]


GOLD3 = (CORE, GOLD, AMBER)
RED3 = (CORE, CORAL, RED)
YEL3 = (CORE, YELLOW, AMBER)


def ease(t):
    return 1.0 - (1.0 - t) ** 2


def rnd(seed):
    return random.Random(seed)


def shards(n, t, seed, hexs, r0=0.2, r1=0.85, size=0.09, a=1.0, shape="kite"):
    r = rnd(seed)
    out = []
    for i in range(n):
        ang = 2 * math.pi * (i + r.uniform(-0.3, 0.3)) / n
        d = r0 + (r1 - r0) * ease(t) * r.uniform(0.7, 1.0)
        s = size * r.uniform(0.6, 1.2) * (1.0 - 0.6 * t)
        out.append(L(shape, d * math.cos(ang), d * math.sin(ang), s, s * 0.7, ang, flat(hexs, a * (1.0 - t ** 2))))
    return out


def squares(n, t, seed, hexs, x0, dx, spread, size, a=1.0):
    r = rnd(seed)
    out = []
    for i in range(n):
        x = x0 + dx * (t + i / n) * r.uniform(0.7, 1.1)
        y = r.uniform(-spread, spread)
        s = size * r.uniform(0.5, 1.0) * (1.0 - 0.5 * t)
        out.append(L("quad", x, y, s, s, 0.0, flat(hexs, a * max(0.0, 1.0 - t - 0.25 * i / n))))
    return out


# ---------- the sheets: name -> (loop, fn(i, t, ph) -> layers) ----------
def burst(c3, t, points=4, seed=1):
    core, shell, edge = c3
    return [
        L("ring", sx=0.3 + 0.55 * ease(t), arg=0.86, ramp=flat(edge, 0.9 * (1 - t)), ink=0.03),
        L("star", sx=0.4 + 0.5 * ease(t), arg=(points, 0.32), rot=0.5 * t, ramp=core_shell(core, shell, edge, 1 - t ** 2, soft=False), mode="radial", hatch=0.55, hs=14, ink=0.04),
        L("star", sx=(0.24 + 0.2 * ease(t)) * (1 - 0.5 * t), arg=(points, 0.4), rot=0.5 * t + math.pi / points, ramp=flat(core, 1 - t)),
    ]


def head(c3, ph, long=1.0, seed=3):
    core, shell, edge = c3
    pulse = 1.0 + 0.06 * math.sin(2 * math.pi * ph)
    ls = [L("taper", -0.42, 0, 0.42, 0.34, 0, [(0.0, edge, 0.0), (1.0, shell, 0.8)], mode="x", hatch=0.6, hs=16, hp=6 * ph)]
    r = rnd(seed)
    for k in range(4):
        u = (ph + k / 4.0) % 1.0
        ls.append(L("quad", -0.25 - 0.6 * u, r.uniform(-0.16, 0.16) * (1 + u), 0.05 * (1 - 0.6 * u), None, 0, flat(shell if k % 2 else edge, 0.95 * (1 - u))))
    ls += [
        L("kite", 0.28, 0, 0.6 * pulse * long, 0.52 * pulse, 0, core_shell(core, shell, edge, 1.0, soft=False), mode="radial", arg=0.75, hatch=0.5, hs=18, ink=0.05),
        L("kite", 0.34, 0, 0.36 * pulse * long, 0.26 * pulse, 0, flat(core), arg=0.6),
    ]
    return ls


def s_gold_release(i, t, ph):
    return burst(GOLD3, t, 4)


def s_gold_travel(i, t, ph):
    return head(GOLD3, ph)


def s_gold_impact(i, t, ph):
    return burst(GOLD3, t, 8) + shards(7, t, 11, AMBER) + [L("disc", sx=0.3 * (1 - t), ramp=flat(CORE, 1 - t))]


def s_gold_fade(i, t, ph):
    return [L("kite", 0.1 - 0.1 * t, 0, 0.45 * (1 - t), 0.36 * (1 - t), 0, core_shell(CORE, GOLD, AMBER, (1 - t) ** 2, soft=False), mode="radial", arg=0.75)] \
        + squares(7, t, 5, GOLD, 0.1, -0.7, 0.3, 0.07) + squares(4, t, 6, YSHADOW, 0.0, -0.5, 0.2, 0.05, 0.8)


def s_stream_start(i, t, ph):
    return [
        L("ring", -0.45, 0, 0.2 + 0.25 * ease(t), 0.45 + 0.3 * ease(t), arg=0.8, ramp=flat(AMBER, 1 - t)),
        L("kite", -0.3 + 0.5 * ease(t), 0, 0.3 + 0.6 * ease(t), 0.7, 0, core_shell(CORE, GOLD, AMBER, 1 - 0.7 * t, soft=False), mode="radial", arg=0.9, hatch=0.5, hs=16),
        L("kite", -0.3 + 0.55 * ease(t), 0, 0.2 + 0.4 * ease(t), 0.3, 0, flat(CORE, 1 - 0.5 * t), arg=0.9),
    ] + shards(5, t, 21, GOLD, 0.2, 0.7, 0.07)


def s_stream_sustain(i, t, ph):
    # The bright band is half the cell height: the quad is sized so that band is exactly the beam's hitbox.
    band = [(0.0, AMBER, 0.0), (0.12, AMBER, 0.95), (0.3, GOLD, 1.0), (0.42, CORE, 1.0), (0.58, CORE, 1.0), (0.7, GOLD, 1.0), (0.88, AMBER, 0.95), (1.0, AMBER, 0.0)]
    ls = [L("quad", 0, 0, 1.0, 0.5, 0, band, mode="y", hatch=0.35, hs=10, hp=2 * math.pi * ph)]
    for k in range(4):
        x = -1.0 + 2.0 * ((ph + k / 4.0) % 1.0)
        for x2 in (x, x - 2.0, x + 2.0):
            ls.append(L("kite", x2, 0.33 if k % 2 else -0.33, 0.12, 0.1, 0, flat(CORE, 0.9), arg=0.8))
    return ls


def s_twin_head(i, t, ph):
    rot = 2 * math.pi * ph / 5.0
    ls = []
    for k in range(3):
        u = (ph + k / 3.0) % 1.0
        ls.append(L("star", -0.3 - 0.5 * u, 0.12 * math.sin(6.28 * (u + k / 3)), 0.12 * (1 - 0.7 * u), arg=(4, 0.35), rot=rot, ramp=flat(GOLD if k else CORE, 0.9 * (1 - u))))
    ls += [
        L("star", 0.2, 0, 0.6, arg=(5, 0.42), rot=rot, ramp=core_shell(CORE, GOLD, YSHADOW, 1.0, soft=False), mode="radial", hatch=0.6, hs=16, ink=0.06),
        L("star", 0.2, 0, 0.3, arg=(5, 0.45), rot=rot, ramp=flat(CORE)),
    ]
    return ls


def s_needle_channel(i, t, ph):
    ls = []
    for k in range(2):
        u = (ph + k / 2.0) % 1.0
        ls.append(L("ring", sx=0.9 - 0.6 * u, arg=0.9, ramp=flat(GOLD if k else AMBER, 0.2 + 0.8 * u)))
    ls += [
        L("kite", 0.0, 0, 0.9, 0.06 + 0.03 * math.sin(6.28 * ph), 0, flat(GOLD, 0.95), arg=1.0),
        L("star", sx=0.2 + 0.05 * math.sin(6.28 * ph), arg=(4, 0.3), rot=0.785, ramp=flat(CORE)),
    ]
    return ls + [L("quad", 0.75 * math.cos(6.28 * (ph + k / 6)), 0.75 * math.sin(6.28 * (ph + k / 6)), 0.035, None, 0, flat(CORE, 0.9)) for k in range(6)]


def s_needle_sliver(i, t, ph):
    ls = [L("taper", -0.3, 0, 0.6, 0.1, 0, [(0.0, AMBER, 0.0), (1.0, GOLD, 0.9)], mode="x")]
    for k in range(3):
        u = (ph + k / 3.0) % 1.0
        ls.append(L("quad", -0.2 - 0.7 * u, 0.07 * (1 if k % 2 else -1), 0.03, None, 0, flat(GOLD, 0.9 * (1 - u))))
    return ls + [
        L("kite", 0.1, 0, 0.85, 0.2, 0, core_shell(CORE, GOLD, AMBER, 1.0, soft=False), mode="radial", arg=0.9, ink=0.035),
        L("kite", 0.2, 0, 0.7, 0.07, 0, flat(CORE), arg=0.9),
    ]


def s_needle_pierce(i, t, ph):
    return [
        L("ring", 0, 0, 0.12 + 0.2 * ease(t), 0.35 + 0.5 * ease(t), arg=0.82, ramp=flat(GOLD, 1 - t)),
        L("ring", 0.1, 0, 0.08 + 0.12 * ease(t), 0.2 + 0.35 * ease(t), arg=0.8, ramp=flat(CORE, 1 - t)),
        L("kite", 0.0, 0, 0.9, 0.05, 0, flat(CORE, 1 - t ** 2), arg=1.0),
    ] + shards(4, t, 31, AMBER, 0.1, 0.5, 0.05)


def s_blocked(i, t, ph):
    # Protected contact: cold and dull on purpose, so it never reads as damage.
    return [
        L("arc", -0.1 - 0.15 * ease(t), 0, 0.55 + 0.2 * ease(t), arg=1.0, rot=math.pi, ramp=flat(PALE, 1 - t)),
        L("arc", -0.05 - 0.1 * ease(t), 0, 0.35 + 0.15 * ease(t), arg=0.8, rot=math.pi, ramp=flat(ASH, 1 - t)),
    ] + squares(5, t, 41, PALE, -0.1, -0.7, 0.45, 0.06) + squares(3, t, 42, ASH, -0.1, -0.5, 0.3, 0.05)


def s_keeper_warning(i, t, ph):
    pulse = 0.5 + 0.5 * math.sin(2 * math.pi * ph)
    ls = [
        L("disc", sx=0.9, ramp=[(0.0, RED, 0.0), (0.6, RED, 0.08 + 0.1 * pulse), (1.0, RSHADOW, 0.3 + 0.2 * pulse)], mode="radial", hatch=0.6, hs=12, hp=6.28 * ph),
        L("ring", sx=0.9, arg=0.9, ramp=flat(RED, 1.0), ink=0.03),
        L("ring", sx=0.74 - 0.1 * pulse, arg=0.93, ramp=flat(CORAL, 0.5 + 0.5 * pulse)),
    ]
    for k in range(4):
        a = math.pi / 2 * k + math.pi / 4
        d = 0.62 - 0.14 * pulse
        ls.append(L("kite", d * math.cos(a), d * math.sin(a), 0.2, 0.16, a + math.pi, core_shell(CORE, CORAL, RED, 1.0, soft=False), mode="radial", arg=0.5, ink=0.03))
    return ls


def s_keeper_strike(i, t, ph):
    sweep = -1.0 + 2.0 * ease(t)
    ls = []
    for k, (c, w, a) in enumerate(((RSHADOW, 0.92, 0.7), (RED, 0.8, 1.0), (CORAL, 0.66, 1.0), (CORE, 0.56, 1.0))):
        ls.append(L("arc", -0.15, 0, w, arg=0.5 + 0.5 * ease(t), rot=sweep * 0.5 - 0.1 * k, ramp=flat(c, a * (1 - t ** 3)), hatch=0.4 if k < 2 else 0.0, hs=14))
    return ls + shards(6, t, 51, CORAL, 0.5, 0.9, 0.07)


def s_keeper_recovery(i, t, ph):
    r = rnd(61)
    ls = []
    for k in range(6):
        x, y = r.uniform(-0.5, 0.5), r.uniform(-0.4, 0.1) + 0.5 * t * r.uniform(0.5, 1.0)
        ls.append(L("disc", x, y, r.uniform(0.12, 0.26) * (1 + 0.5 * t), ramp=glow(ASH if k % 2 else PALE, 0.55 * (1 - t)), mode="radial"))
    return ls


def s_gust_puff(i, t, ph):
    ls = [L("arc", 0.0, 0, 0.3 + 0.5 * ease(t), arg=1.2, rot=math.pi, ramp=flat(ASH, 1 - t))]
    for k in range(5):
        y = -0.5 + 0.25 * k
        ls.append(L("taper", 0.1 - 0.5 * ease(t), y, 0.35, 0.05, math.pi, flat(PALE if k % 2 else ASH, 0.9 * (1 - t))))
    return ls


def s_gust(i, t, ph):
    ls = []
    r = rnd(71)
    for k in range(7):
        y = -0.78 + 0.26 * k
        off = r.uniform(0, 1)
        u = (ph + off) % 1.0
        x = 1.0 - 2.0 * u
        for x2 in (x, x + 2.0, x - 2.0):
            ls.append(L("taper", x2, y + 0.05 * math.sin(6.28 * (u + k)), 0.5, 0.045, math.pi, [(0.0, ASH, 0.0), (1.0, PALE if k % 2 else ASH, 0.85)], mode="x"))
    return ls


def s_clock_beat(i, t, ph):
    ls = []
    for k, delay in enumerate((0.0, 0.35)):
        u = max(0.0, min(1.0, (t - delay) / 0.65))
        if t >= delay:
            ls.append(L("ring", sx=0.25 + 0.65 * ease(u), arg=0.88, ramp=flat(RED if k == 0 else CORAL, 1 - u)))
    for k in range(12):
        a = 2 * math.pi * k / 12
        ls.append(L("kite", 0.8 * math.cos(a), 0.8 * math.sin(a), 0.1, 0.06, a + math.pi, flat(CORE if k % 3 == 0 else CORAL, 1 - t)))
    ls.append(L("disc", sx=0.2 * (1 - t), ramp=flat(CORE, 1 - t)))
    return ls


def s_clock_open(i, t, ph):
    gap = 0.5 * ease(t)
    return [
        L("disc", sx=0.8, ramp=[(0.0, CORE, 1.0), (0.4, YELLOW, 0.9), (1.0, AMBER, 0.0)], mode="radial", hatch=0.4, hs=14, a=ease(t) * (1 - t ** 4)),
        L("ring", sx=0.82, arg=0.92, ramp=flat(AMBER, 1 - t ** 4)),
        L("quad", -0.2 - gap, 0, 0.2, 0.7, 0, flat(INK, 0.9 * (1 - t))),
        L("quad", 0.2 + gap, 0, 0.2, 0.7, 0, flat(INK, 0.9 * (1 - t))),
    ] + [L("kite", 0.6 * math.cos(a), 0.6 * math.sin(a), 0.25 * ease(t), 0.05, a, flat(YELLOW, 1 - t)) for a in [math.pi / 4 * k for k in range(8)]]


def s_part_hit(i, t, ph):
    return burst(GOLD3, t, 6) + shards(5, t, 81, INK, 0.15, 0.7, 0.06) + shards(4, t, 82, CORE, 0.1, 0.8, 0.05)


def s_part_break(i, t, ph):
    return [
        L("disc", sx=0.9 * ease(t), ramp=glow(CORE, 0.8 * (1 - t)), mode="radial"),
        L("ring", sx=0.2 + 0.7 * ease(t), arg=0.9, ramp=flat(AMBER, 1 - t)),
    ] + shards(10, t, 91, INK, 0.1, 0.9, 0.13, shape="quad") + shards(8, t, 92, YSHADOW, 0.1, 0.8, 0.08) + shards(6, t, 93, CORE, 0.1, 0.85, 0.05)


def s_stun(i, t, ph):
    ls = [L("ring", 0, 0, 0.7, 0.28, arg=0.94, ramp=flat(YSHADOW, 0.7))]
    for k in range(3):
        a = 2 * math.pi * (ph + k / 3.0)
        front = math.sin(a) < 0
        ls.append(L("star", 0.7 * math.cos(a), 0.28 * math.sin(a), 0.2 if front else 0.14, arg=(4, 0.35), rot=a,
                    ramp=core_shell(CORE, YELLOW, AMBER, 1.0 if front else 0.7, soft=False), mode="radial", ink=0.03))
    return ls


def s_slow(i, t, ph):
    return [L("quad", ramp=flat(ASH, 0.16), hatch=0.5, hs=5, hp=2 * math.pi * ph, cut=True)]


def s_eye(i, t, ph):
    pulse = 0.5 + 0.5 * math.sin(2 * math.pi * ph)
    ls = [
        L("ring", sx=0.7 + 0.08 * pulse, arg=0.9, ramp=flat(YELLOW, 1.0), ink=0.03),
        L("disc", sx=0.14 + 0.03 * pulse, ramp=flat(CORE)),
    ]
    for k in range(4):
        a = math.pi / 2 * k
        d = 0.5 - 0.08 * pulse
        ls.append(L("kite", d * math.cos(a), d * math.sin(a), 0.2, 0.12, a + math.pi, flat(AMBER), arg=0.4))
    return ls


def s_blackout(i, t, ph):
    return [L("quad", ramp=flat(INK, 0.55)), L("quad", ramp=flat(INK, 0.25), hatch=1.0, hs=6, hp=2 * math.pi * ph, cut=True)]


def s_restoration(i, t, ph):
    return [
        L("quad", ramp=flat(CORE, 0.35 * (1 - t))),
        L("ring", sx=0.1 + 1.3 * ease(t), arg=0.9, ramp=flat(CORE, 0.9 * (1 - t))),
        L("ring", sx=0.05 + 1.0 * ease(t), arg=0.94, ramp=flat(GOLD, 0.8 * (1 - t))),
    ]


def s_departure(i, t, ph):
    r = rnd(101)
    ls = []
    for k in range(9):
        x = r.uniform(-0.8, 0.8)
        u = (ph + r.uniform(0, 1)) % 1.0
        ls.append(L("star", x, -0.8 + 1.6 * u, 0.1 * math.sin(math.pi * u) + 0.02, arg=(4, 0.3), rot=0.785,
                    ramp=flat(CORE if k % 2 else GOLD, math.sin(math.pi * u))))
    return ls


def s_light_shaft(i, t, ph):
    band = [(0.0, GOLD, 0.0), (0.3, GOLD, 0.35), (0.45, CORE, 0.85), (0.55, CORE, 0.85), (0.7, GOLD, 0.35), (1.0, GOLD, 0.0)]
    ls = [L("quad", ramp=band, mode="x")]
    r = rnd(111)
    for k in range(6):
        x = r.uniform(-0.3, 0.3)
        y = 1.0 - 2.0 * ((ph + r.uniform(0, 1)) % 1.0)
        for y2 in (y, y + 2.0, y - 2.0):
            ls.append(L("quad", x, y2, 0.05, 0.02, 0, flat(CORE, 0.9)))
    return ls


def s_umbra(i, t, ph):
    # Darkest right under the canopy (top of the cell), thinning toward the abyss; edges soften sideways.
    down = [(0.0, INK, 0.0), (0.75, INK, 0.5), (1.0, INK, 0.72)]
    side = [(0.0, INK, 0.0), (0.25, INK, 0.0), (0.5, INK, 0.25), (0.75, INK, 0.0), (1.0, INK, 0.0)]
    return [L("quad", ramp=down, mode="y", hatch=0.25, hs=7, hp=2 * math.pi * ph, cut=True), L("quad", sx=1.0, sy=1.0, ramp=side, mode="x")]


SHEETS = {
    "VFX_GoldRelease": (False, s_gold_release), "VFX_GoldTravel": (True, s_gold_travel), "VFX_GoldImpact": (False, s_gold_impact),
    "VFX_GoldFade": (False, s_gold_fade), "VFX_StreamStart": (False, s_stream_start), "VFX_StreamSustain": (True, s_stream_sustain),
    "VFX_TwinStarHead": (True, s_twin_head), "VFX_NeedleChannel": (True, s_needle_channel), "VFX_NeedleSliver": (True, s_needle_sliver),
    "VFX_NeedlePierce": (False, s_needle_pierce), "VFX_Blocked": (False, s_blocked), "VFX_KeeperWarning": (True, s_keeper_warning),
    "VFX_KeeperStrike": (False, s_keeper_strike), "VFX_KeeperRecovery": (False, s_keeper_recovery), "VFX_GustPuff": (False, s_gust_puff),
    "VFX_Gust": (True, s_gust), "VFX_ClockBeat": (False, s_clock_beat), "VFX_ClockOpen": (False, s_clock_open),
    "VFX_PartHit": (False, s_part_hit), "VFX_PartBreak": (False, s_part_break), "VFX_Stun": (True, s_stun), "VFX_Slow": (True, s_slow),
    "VFX_EyeExposed": (True, s_eye), "VFX_Blackout": (True, s_blackout), "VFX_Restoration": (False, s_restoration),
    "VFX_Departure": (True, s_departure), "VFX_LightShaft": (True, s_light_shaft), "VFX_Umbra": (True, s_umbra),
}
# Sheets that fill their cell on purpose (bands and veils): the cell border is not transparent.
FULL_FRAME = ("VFX_StreamSustain", "VFX_Slow", "VFX_Blackout", "VFX_Restoration", "VFX_LightShaft", "VFX_Umbra", "VFX_Gust")


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    only, cell = [], 128
    k = 0
    while k < len(argv):
        if argv[k] == "--only":
            k += 1
            while k < len(argv) and not argv[k].startswith("--"):
                only.append(argv[k])
                k += 1
        elif argv[k] == "--cell":
            cell = int(argv[k + 1])
            k += 2
        else:
            k += 1
    os.makedirs(os.path.join(OUT, "Stills"), exist_ok=True)
    tmp = os.path.join(bpy.app.tempdir, "vfx_frame.png")
    sc = setup(cell)
    for name, (loop, fn) in SHEETS.items():
        if only and name not in only:
            continue
        strip = np.zeros((cell, cell * FRAMES, 4), dtype=np.float32)
        for i in range(FRAMES):
            t = i / (FRAMES - 1.0)
            ph = i / float(FRAMES)
            render_frame(sc, fn(i, t, ph), tmp)
            px = read_png(tmp)
            if name not in FULL_FRAME:
                px[0, :, 3] = px[-1, :, 3] = 0.0
                px[:, 0, 3] = px[:, -1, 3] = 0.0
            strip[:, i * cell:(i + 1) * cell] = px
            if i == (2 if not loop else 0):
                write_png(px, os.path.join(OUT, "Stills", f"{name}_PH.png"))
        write_png(strip, os.path.join(OUT, f"{name}_PH.png"))
        print(f"VFX_SHEET {name} frames={FRAMES} cell={cell} loop={int(loop)}")


main()
