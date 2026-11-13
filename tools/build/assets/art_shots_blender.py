"""Blender-side builders for the shots art lane (owl-bolt, bolt-hit, wand-shot, wind-zone, wind-lines).

Run by tools/build/assets/art_shots.py, never by python3:
  blender -b --factory-startup -P tools/build/assets/art_shots_blender.py -- --job <job.json>
It registers its builders in pipeline/art/blender/stand_ins.py's BUILDERS (that file stays untouched, it is shared)
and then runs the shared renderer (render_sprite.py): same camera, ortho, transparent film, Freestyle ink, look.
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(HERE))), "pipeline", "art", "blender"))

import bpy  # noqa: E402
import stand_ins  # noqa: E402
from stand_ins import Rig, glow, hex_rgb  # noqa: E402

SHOT_EDGE_TOP = [(1.1, 0.04), (0.45, 0.32), (0.35, 0.12), (-0.3, 0.62), (-0.4, 0.14), (-1.2, 0.4), (-1.3, 0.06)]
SHOT_EDGE_BOT = [(1.15, -0.04), (0.55, -0.28), (0.4, -0.1), (-0.2, -0.54), (-0.3, -0.12), (-1.15, -0.36), (-1.25, -0.05)]


def alpha_glow(name, hexcol, alpha, strength=1.0):
    m = glow(name, hexcol, strength)
    nt = m.node_tree
    out = nt.nodes["Material Output"]
    emi = [n for n in nt.nodes if n.type == "EMISSION"][0]
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    mix.inputs["Fac"].default_value = alpha
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(emi.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    try:
        m.surface_render_method = "BLENDED"   # no dithered alpha: the spill is a soft even tint
    except (AttributeError, TypeError):
        pass
    return m


def graded(name, head_hex, tail_hex, x_tail=-2.6, x_head=1.4, grain=0.12, cut=0.38, snap=0.0, hatch=9.0):
    """An emission colour that shifts from head_hex at the head to tail_hex at the tail, with paper grain (painted, not
    a flat fill: the critic's 'flat fills, no paper texture' gap)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    emi = nt.nodes.new("ShaderNodeEmission")
    coord = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeMapRange")
    ramp.inputs["From Min"].default_value = x_tail
    ramp.inputs["From Max"].default_value = x_head
    mix = nt.nodes.new("ShaderNodeValToRGB")   # two palette colours in a hard step (no off-palette blends)
    mix.color_ramp.interpolation = "CONSTANT"
    mix.color_ramp.elements[0].position, mix.color_ramp.elements[0].color = 0.0, hex_rgb(tail_hex)
    mix.color_ramp.elements[1].position, mix.color_ramp.elements[1].color = cut, hex_rgb(head_hex)
    noise = nt.nodes.new("ShaderNodeTexWhiteNoise")   # per-pixel paper grain
    noise.noise_dimensions = "3D"
    gm = nt.nodes.new("ShaderNodeValToRGB")   # two grain levels only: tooth without leaving the palette's tolerance
    gm.color_ramp.interpolation = "CONSTANT"
    gm.color_ramp.elements[0].position, gm.color_ramp.elements[0].color = 0.0, (1, 1, 1, 1)
    g2 = 1.0 - grain
    gm.color_ramp.elements[1].position, gm.color_ramp.elements[1].color = 0.5, (g2, g2, g2, 1)
    mul = nt.nodes.new("ShaderNodeVectorMath")
    mul.operation = "MULTIPLY"
    mul2 = nt.nodes.new("ShaderNodeVectorMath")
    mul2.operation = "MULTIPLY"
    wave = nt.nodes.new("ShaderNodeTexWave")   # engraved hatch: thin diagonal lines, a darker shade of the same colour
    wave.wave_type = "BANDS"
    wave.bands_direction = "DIAGONAL"
    wave.inputs["Scale"].default_value = hatch
    wave.inputs["Distortion"].default_value = 1.2
    wave.inputs["Detail"].default_value = 0.0
    hr = nt.nodes.new("ShaderNodeValToRGB")
    hr.color_ramp.interpolation = "CONSTANT"
    hr.color_ramp.elements[0].position, hr.color_ramp.elements[0].color = 0.0, (1, 1, 1, 1)
    hr.color_ramp.elements[1].position, hr.color_ramp.elements[1].color = 0.9, (0.92, 0.92, 0.92, 1)
    mot = nt.nodes.new("ShaderNodeTexNoise")   # paper mottle: slow blotches, two levels
    mot.inputs["Scale"].default_value = 5.0
    mot.inputs["Detail"].default_value = 3.0
    mr = nt.nodes.new("ShaderNodeValToRGB")
    mr.color_ramp.interpolation = "CONSTANT"
    mr.color_ramp.elements[0].position, mr.color_ramp.elements[0].color = 0.0, (1, 1, 1, 1)
    mr.color_ramp.elements[1].position, mr.color_ramp.elements[1].color = 0.52, (0.95, 0.95, 0.95, 1)
    mul3 = nt.nodes.new("ShaderNodeVectorMath")
    mul3.operation = "MULTIPLY"
    L = nt.links.new
    L(coord.outputs["Object"], wave.inputs["Vector"])
    L(wave.outputs["Fac"], hr.inputs["Fac"])
    L(coord.outputs["Object"], mot.inputs["Vector"])
    L(mot.outputs["Fac"], mr.inputs["Fac"])
    L(hr.outputs[0], mul2.inputs[1])
    L(mr.outputs[0], mul3.inputs[1])
    L(coord.outputs["Object"], sep.inputs[0])
    if snap:   # one grain value per output pixel: the sub-pixel samples do not average it away
        sn = nt.nodes.new("ShaderNodeVectorMath")
        sn.operation = "SNAP"
        sn.inputs[1].default_value = (snap, snap, snap)
        L(coord.outputs["Object"], sn.inputs[0])
        L(sn.outputs[0], noise.inputs["Vector"])
    else:
        L(coord.outputs["Object"], noise.inputs["Vector"])
    L(sep.outputs["X"], ramp.inputs["Value"])
    L(ramp.outputs[0], mix.inputs[0])
    L(noise.outputs["Value"], gm.inputs[0])
    L(mix.outputs[0], mul3.inputs[0])
    L(mul3.outputs[0], mul2.inputs[0])
    L(mul2.outputs[0], mul.inputs[0])
    L(gm.outputs[0], mul.inputs[1])
    L(mul.outputs[0], emi.inputs["Color"])
    L(emi.outputs["Emission"], out.inputs["Surface"])
    return m


def glow_plane(r, bone, mat, size=(7.0, 3.6), centre=(-0.6, 0.45)):
    """A separate bounded light mask behind the shot: a soft radial falloff, never part of the body."""
    import bmesh
    me = bpy.data.meshes.new("glow")
    ob = bpy.data.objects.new("glow", me)
    bpy.context.scene.collection.objects.link(ob)
    bm = bmesh.new()
    w, h = size[0] / 2, size[1] / 2
    bm.faces.new([bm.verts.new((centre[0] + dx * w, 0.3, centre[1] * 0 + dz * h)) for dx, dz in
                  ((-1, -1), (1, -1), (1, 1), (-1, 1))])
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    r.parts.append((ob, bone))


def radial_glow(name, hexcol, alpha, rx, rz, cx):
    m = glow(name, hexcol)
    nt = m.node_tree
    out = nt.nodes["Material Output"]
    emi = [n for n in nt.nodes if n.type == "EMISSION"][0]
    coord = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nx = nt.nodes.new("ShaderNodeMath")
    nx.operation = "SUBTRACT"
    nx.inputs[1].default_value = cx
    ex = nt.nodes.new("ShaderNodeMath")
    ex.operation = "DIVIDE"
    ex.inputs[1].default_value = rx
    ez = nt.nodes.new("ShaderNodeMath")
    ez.operation = "DIVIDE"
    ez.inputs[1].default_value = rz
    comb = nt.nodes.new("ShaderNodeCombineXYZ")
    ln = nt.nodes.new("ShaderNodeVectorMath")
    ln.operation = "LENGTH"
    ramp = nt.nodes.new("ShaderNodeMapRange")
    ramp.inputs["From Min"].default_value = 0.0
    ramp.inputs["From Max"].default_value = 1.0
    ramp.inputs["To Min"].default_value = alpha
    ramp.inputs["To Max"].default_value = 0.0
    ramp.interpolation_type = "SMOOTHSTEP"
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    L = nt.links.new
    L(coord.outputs["Object"], sep.inputs[0])
    L(sep.outputs["X"], nx.inputs[0])
    L(nx.outputs[0], ex.inputs[0])
    L(sep.outputs["Z"], ez.inputs[0])
    L(ex.outputs[0], comb.inputs["X"])
    L(ez.outputs[0], comb.inputs["Y"])
    L(comb.outputs[0], ln.inputs[0])
    L(ln.outputs["Value"], ramp.inputs["Value"])
    L(ramp.outputs[0], mix.inputs[0])
    L(tr.outputs[0], mix.inputs[1])
    L(emi.outputs[0], mix.inputs[2])
    L(mix.outputs[0], out.inputs["Surface"])
    try:
        m.surface_render_method = "BLENDED"
    except (AttributeError, TypeError):
        pass
    return m


def inked():
    """The Freestyle collection: only objects linked here get an ink outline."""
    c = bpy.data.collections.get("inked")
    if c is None:
        c = bpy.data.collections.new("inked")
        bpy.context.scene.collection.children.link(c)
    return c


def poly_part(r, bone, mat, pts, y=0.0, thick=0.04, name="poly", ink=False):
    """A flat angular shape in the picture plane (x, z) at depth y (smaller y = nearer the camera)."""
    import bmesh
    me = bpy.data.meshes.new(name)
    ob = bpy.data.objects.new(name, me)
    (inked() if ink else bpy.context.scene.collection).objects.link(ob)
    bm = bmesh.new()
    f = bm.faces.new([bm.verts.new((x, y, z)) for x, z in pts])
    res = bmesh.ops.extrude_face_region(bm, geom=[f])
    bmesh.ops.translate(bm, vec=(0, thick, 0), verts=[e for e in res["geom"] if isinstance(e, bmesh.types.BMVert)])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    r.parts.append((ob, bone))
    return ob


def shot_outline(sx, sz, dx=0.0, head=1.5, tail=-2.2, grow=0.0):
    sx, sz, dx = sx * 0.82, sz * 1.4, dx * 0.82   # a stubbier build: the tuned aspect of the red-shot crops
    top = [(x * sx + dx, z * sz + grow) for x, z in SHOT_EDGE_TOP]
    bot = [(x * sx + dx, z * sz - grow) for x, z in SHOT_EDGE_BOT]
    return [(head * sx + dx + grow, 0.0)] + top + [(tail * sx + dx - grow, 0.0)] + list(reversed(bot))


def shot(m, rnd, shell, mid, body, core, spill, trail_a, trail_b):
    """bar-casters' shared projectile: bright core, shell, trail, light spill; one pointed angular geometry."""
    r = Rig("Shot")
    r.bone("body", (-0.5, 0, 0), (0.5, 0, 0))
    poly_part(r, "body", m["ink"], shot_outline(1.0, 1.0, 0.0, 1.5, -2.35, grow=0.04), y=0.04, thick=0.02, name="ink")
    poly_part(r, "body", m[shell], shot_outline(1.0, 1.0), y=0.0, name="shell")
    poly_part(r, "body", m["redshadow"], shot_outline(0.95, 0.3, -0.05), y=-0.03, name="shade")
    poly_part(r, "body", m[mid], shot_outline(0.86, 0.72, 0.1), y=-0.06, name="mid")
    poly_part(r, "body", m[body], shot_outline(0.7, 0.4, 0.25), y=-0.12, name="body")
    poly_part(r, "body", m[core], shot_outline(0.62, 0.17, 0.4), y=-0.18, name="core")
    streak = [(-1.2, 0.22), (-2.0, 0.15), (-2.7, 0.04), (-2.7, -0.04), (-2.0, -0.15), (-1.2, -0.22)]
    poly_part(r, "body", m["g_st_r" if shell == "g_shell" else "g_st_y"], streak, y=0.02, thick=0.02, name="streak")
    poly_part(r, "body", m["g_st_c" if shell == "g_shell" else "g_st_a"],
              [(x * 0.95, z * 0.45) for x, z in streak], y=-0.01, thick=0.02, name="streak_core")
    rr = random.Random(9)
    x = -2.2
    for i in range(6):   # broken-off shards thinning down the trail
        w, h = 0.2 - 0.02 * i, 0.075 - 0.007 * i
        z = rr.uniform(-0.3, 0.3)
        poly_part(r, "body", m[trail_a if i % 2 else trail_b],
                  [(x, z - h), (x - w, z - h), (x - w, z + h), (x, z + h)], y=-0.04, thick=0.02, name="shard%d" % i)
        x -= w + 0.03 + 0.02 * i
    return r.build(), {}


def build_shot_red(m, rnd):
    return shot(m, rnd, "g_shell", "g_mid", "g_core", "core", "spill_red", "red", "redshadow")


def build_shot_gold(m, rnd):
    return shot(m, rnd, "g_ys", "g_ym", "g_core", "core", "spill_gold", "yellow", "yshadow")


stand_ins.BUILDERS["shot_red"] = build_shot_red
stand_ins.BUILDERS["shot_gold"] = build_shot_gold

_materials = stand_ins.materials


def materials(colours, look):
    mats = _materials(colours, look)
    c = colours.get
    sn_ = float(look.get("snap", 0.0))
    mats["coral"] = glow("coral", c("coral", "#ff7848"))
    mats["yellow"] = glow("yellow", c("yellow", "#ffd84a"))
    mats["amber"] = glow("amber2", c("amber", "#f5aa28"))
    mats["yshadow"] = glow("yshadow", c("yellow shadow", "#94611e"))
    mats["g_shell"] = graded("g_shell", c("red", "#ff3658"), c("red shadow", "#8f173c"), snap=sn_)
    mats["g_mid"] = graded("g_mid", c("coral", "#ff7848"), c("red", "#ff3658"), snap=sn_)
    mats["g_core"] = graded("g_core", c("core", "#fff5dc"), c("coral", "#ff7848"), x_tail=-1.8, snap=sn_, grain=0.3)
    mats["g_ys"] = graded("g_ys", c("yellow", "#ffd84a"), c("yellow shadow", "#94611e"), snap=sn_)
    mats["g_ym"] = graded("g_ym", c("amber", "#f5aa28"), c("yellow", "#ffd84a"), snap=sn_)
    mats["g_st_r"] = graded("g_st_r", c("red", "#ff3658"), c("red", "#ff3658"), snap=sn_)
    mats["g_st_c"] = graded("g_st_c", c("coral", "#ff7848"), c("coral", "#ff7848"), snap=sn_)
    mats["g_st_y"] = graded("g_st_y", c("yellow", "#ffd84a"), c("yellow", "#ffd84a"), snap=sn_)
    mats["g_st_a"] = graded("g_st_a", c("amber", "#f5aa28"), c("amber", "#f5aa28"), snap=sn_)
    mats["spill_red"] = radial_glow("spill_red", c("red", "#ff3658"), 0.45, 2.6, 1.05, -0.5)
    mats["spill_gold"] = radial_glow("spill_gold", c("yellow", "#ffd84a"), 0.45, 2.6, 1.05, -0.5)
    return mats


stand_ins.materials = materials

_lines = stand_ins.lines


def lines(scene, ink_hex, px):
    rep = _lines(scene, ink_hex, px)
    if rep == "on" and "inked" in bpy.data.collections:
        ls = scene.view_layers[0].freestyle_settings.linesets[0]
        ls.select_by_collection = True
        ls.collection = bpy.data.collections["inked"]
    return rep


stand_ins.lines = lines

_setup = stand_ins.setup


def setup(job):
    out = _setup(job)
    # crisp edges: a wide reconstruction filter blends every colour edge into off-palette pixels at sprite size
    if not job["look"].get("freestyle", False):   # the outline is geometry (an ink slab behind each shape)
        out[0].render.use_freestyle = False
        out[0].view_layers[0].use_freestyle = False
    out[0].render.filter_size = float(job["look"].get("filter_px", 0.0))
    return out


stand_ins.setup = setup

if __name__ == "__main__":
    import render_sprite
    render_sprite.main()
