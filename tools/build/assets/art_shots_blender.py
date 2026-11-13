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

SHOT_EDGE_TOP = [(0.95, 0.10), (0.55, 0.40), (0.45, 0.19), (-0.05, 0.62), (-0.15, 0.29), (-0.75, 0.52),
                 (-0.85, 0.21), (-1.5, 0.38), (-1.6, 0.13), (-2.2, 0.19)]
SHOT_EDGE_BOT = [(1.0, -0.09), (0.62, -0.34), (0.5, -0.17), (0.0, -0.55), (-0.1, -0.26), (-0.7, -0.6),
                 (-0.8, -0.2), (-1.4, -0.34), (-1.5, -0.12), (-2.1, -0.2)]


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


def shot_outline(sx, sz, dx=0.0, head=1.45, tail=-2.9):
    sx, sz, dx = sx * 0.82, sz * 1.3, dx * 0.82   # a stubbier build: the tuned aspect of the red-shot crops
    top = [(x * sx + dx, z * sz) for x, z in SHOT_EDGE_TOP]
    bot = [(x * sx + dx, z * sz) for x, z in SHOT_EDGE_BOT]
    return [(head * sx + dx, 0.0)] + top + [(tail * sx + dx, 0.0)] + list(reversed(bot))


def shot(m, rnd, shell, mid, body, core, spill, trail_a, trail_b):
    """bar-casters' shared projectile: bright core, shell, trail, light spill; one pointed angular geometry."""
    r = Rig("Shot")
    r.bone("body", (-0.5, 0, 0), (0.5, 0, 0))
    poly_part(r, "body", m[spill], shot_outline(1.18, 1.9, -0.1), y=0.35, thick=0.01, name="spill")
    poly_part(r, "body", m[shell], shot_outline(1.0, 1.0), y=0.0, name="shell", ink=True)
    poly_part(r, "body", m["redshadow"], shot_outline(0.95, 0.3, -0.05), y=-0.03, name="shade")
    poly_part(r, "body", m[mid], shot_outline(0.86, 0.72, 0.1), y=-0.06, name="mid")
    poly_part(r, "body", m[body], shot_outline(0.7, 0.4, 0.25), y=-0.12, name="body")
    poly_part(r, "body", m[core], shot_outline(0.62, 0.17, 0.4), y=-0.18, name="core")
    rr = random.Random(9)
    x = -2.5
    for i in range(6):   # broken-off shards thinning down the trail
        w, h = 0.2 - 0.02 * i, 0.075 - 0.007 * i
        z = rr.uniform(-0.3, 0.3)
        poly_part(r, "body", m[trail_a if i % 2 else trail_b],
                  [(x, z - h), (x - w, z - h), (x - w, z + h), (x, z + h)], y=-0.04, thick=0.02, name="shard%d" % i)
        x -= w + 0.05 + 0.04 * i
    return r.build(), {}


def build_shot_red(m, rnd):
    return shot(m, rnd, "red", "coral", "core", "core", "spill_red", "red", "redshadow")


def build_shot_gold(m, rnd):
    return shot(m, rnd, "yshadow", "yellow", "amber", "core", "spill_gold", "yellow", "yshadow")


stand_ins.BUILDERS["shot_red"] = build_shot_red
stand_ins.BUILDERS["shot_gold"] = build_shot_gold

_materials = stand_ins.materials


def materials(colours, look):
    mats = _materials(colours, look)
    c = colours.get
    mats["coral"] = glow("coral", c("coral", "#ff7848"))
    mats["yellow"] = glow("yellow", c("yellow", "#ffd84a"))
    mats["amber"] = glow("amber2", c("amber", "#f5aa28"))
    mats["yshadow"] = glow("yshadow", c("yellow shadow", "#94611e"))
    mats["spill_red"] = alpha_glow("spill_red", c("red", "#ff3658"), 0.22)
    mats["spill_gold"] = alpha_glow("spill_gold", c("yellow", "#ffd84a"), 0.22)
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

if __name__ == "__main__":
    import render_sprite
    render_sprite.main()
