"""Blender stand-ins for the game's sprites: build, rig, shade (runs inside Blender; render_sprite.py imports it).

Every builder makes its parts in world units at rest, facing +X, with the rig's origin at the world origin (the
pixel the layout's pivot_px names), binds each part rigidly to one bone (vertex group + Armature modifier, parented
to the armature so a mirror flips it all) and returns the armature. Pose angles are degrees in the picture plane,
positive = counter-clockwise as the camera sees it (+Z toward -X).
Look (pipeline/art/blender/characters.json `look`): toon ramps in near-black palette shades with paper grain in the
material, emission-only accents (gold clock and star, amber eyes, rust-red bolt), Freestyle ink lines, one sun from
the front slightly above (art bible R11), transparent film, Standard view transform.
Add a character: write build_<name>(mats, rnd) here, add its recipe to characters.json. Revise the look for the art
loop here or in the recipe; never in the checks.
"""
import math
import random

import bpy  # noqa: F401  (Blender only)
from mathutils import Matrix, Quaternion, Vector

AXIS = Vector((0.0, -1.0, 0.0))   # the picture-plane normal toward the camera: positive angle = counter-clockwise


def hex_rgb(h):
    h = h.lstrip("#")
    srgb = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    # node colours are scene-linear; the Standard view transform turns them back into these sRGB values
    return tuple(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb) + (1.0,)


# ---------- materials ----------
def toon(name, shades, look):
    """Diffuse -> Shader to RGB -> constant ramp in the given shades, times paper grain, as emission."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    dif = nt.nodes.new("ShaderNodeBsdfDiffuse")
    s2r = nt.nodes.new("ShaderNodeShaderToRGB")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "CONSTANT"
    els = ramp.color_ramp.elements
    els[0].position, els[0].color = 0.0, hex_rgb(shades[0])
    els[1].position, els[1].color = 0.35, hex_rgb(shades[1])
    e = els.new(0.7)
    e.color = hex_rgb(shades[2])
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = float(look.get("grain_scale", 180.0))
    noise.inputs["Detail"].default_value = 6.0
    g = float(look.get("grain", 0.06))
    fac = nt.nodes.new("ShaderNodeMath")
    fac.operation = "MULTIPLY_ADD"   # noise * grain + (1 - grain): paper grain in the ink
    fac.inputs[1].default_value = g
    fac.inputs[2].default_value = 1.0 - g
    mul = nt.nodes.new("ShaderNodeVectorMath")
    mul.operation = "SCALE"
    emi = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(dif.outputs["BSDF"], s2r.inputs["Shader"])
    nt.links.new(s2r.outputs["Color"], ramp.inputs["Fac"])
    nt.links.new(noise.outputs["Fac"], fac.inputs[0])
    nt.links.new(ramp.outputs["Color"], mul.inputs[0])
    nt.links.new(fac.outputs[0], mul.inputs["Scale"])
    nt.links.new(mul.outputs[0], emi.inputs["Color"])
    nt.links.new(emi.outputs["Emission"], out.inputs["Surface"])
    return m


def glow(name, hexcol, strength=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    emi = nt.nodes.new("ShaderNodeEmission")
    emi.inputs["Color"].default_value = hex_rgb(hexcol)
    emi.inputs["Strength"].default_value = strength
    nt.links.new(emi.outputs["Emission"], out.inputs["Surface"])
    return m


def materials(colours, look):
    c = colours.get
    shades = [c(s, "#171614") for s in look.get("shades", ["ink", "silhouette", "owl-umber"])]
    return {
        "ink": toon("ink", shades, look),
        "feather": toon("feather", [c("silhouette"), c("owl-umber"), c("owl-feather")], look),
        "cloth": toon("cloth", [c("paper-stain"), c("paper-mid"), c("paper-light")], dict(look, grain=0.38)),
        "hair": toon("hair", [c("owl-umber"), c("paper-stain"), c("paper-mid")], dict(look, grain=0.38)),
        "stripe": toon("stripe", [c("ink"), c("ink"), c("silhouette")], look),
        "gold": glow("gold", c("gold", "#e9b04a")),
        "amber": glow("amber", c("amber-eye", "#c8862a")),
        "rust": glow("rust", c("rust-red", "#743422")),
        "red": glow("red", c("red", "#ff3658")),
        "redshadow": glow("redshadow", c("red shadow", "#8f173c")),
        "core": glow("core", c("core", "#fff5dc")),
        "spark": glow("spark", c("spark-white", "#fff3d6")),
    }


# ---------- parts and rig ----------
class Rig:
    def __init__(self, name):
        self.parts = []   # (object, bone)
        self.bones = {}   # name -> (head, tail, parent)
        self.name = name

    def bone(self, name, head, tail, parent=None):
        self.bones[name] = (Vector(head), Vector(tail), parent)

    def add(self, op, bone, mat, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), **kw):
        getattr(bpy.ops.mesh, op)(location=loc, rotation=rot, **kw)
        ob = bpy.context.active_object
        ob.scale = scale
        ob.data.materials.append(mat)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        self.parts.append((ob, bone))
        return ob

    def build(self):
        data = bpy.data.armatures.new(self.name + "_rig")
        arm = bpy.data.objects.new(self.name + "_rig", data)
        bpy.context.scene.collection.objects.link(arm)
        bpy.context.view_layer.objects.active = arm
        bpy.ops.object.mode_set(mode="EDIT")
        made = {}
        for name, (h, t, _) in self.bones.items():
            eb = data.edit_bones.new(name)
            eb.head, eb.tail = h, t
            made[name] = eb
        for name, (_, _, parent) in self.bones.items():
            if parent:
                made[name].parent = made[parent]
        bpy.ops.object.mode_set(mode="OBJECT")
        for ob, bone in self.parts:
            vg = ob.vertex_groups.new(name=bone)
            vg.add(list(range(len(ob.data.vertices))), 1.0, "REPLACE")
            mod = ob.modifiers.new("rig", "ARMATURE")
            mod.object = arm
            ob.parent = arm
            ob.matrix_parent_inverse = arm.matrix_world.inverted()
        return arm


def pose(arm, p, ppu, extra=None):
    """Apply one planned pose: bone angles, canopy (0 closed .. 1 open), lift (px), flash (wand star)."""
    for pb in arm.pose.bones:
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.scale = (1, 1, 1)
    for name, deg in (p.get("rot") or {}).items():
        pb = arm.pose.bones.get(name)
        if pb is None:
            continue
        sign = -1.0 if name in (extra or {}).get("mirror_bones", ()) else 1.0
        local = pb.bone.matrix_local.to_3x3().inverted() @ AXIS
        pb.rotation_quaternion = Quaternion(local, math.radians(deg * sign))
    cb = arm.pose.bones.get("canopy")
    if cb is not None and "canopy" in p:
        o = max(0.0, min(1.0, p["canopy"]))
        w = 0.22 + 0.78 * o
        cb.scale = (w, 1.55 - 0.55 * o, w)
    arm.location.z = float(p.get("lift", 0.0)) / ppu
    star = bpy.data.objects.get("wand_star")
    if star is not None:
        f = float(p.get("flash", 0.0))
        star.scale = (1 + 1.6 * f,) * 3
        node = star.data.materials[0].node_tree.nodes.get("Emission")
        if node:
            node.inputs["Strength"].default_value = 1.0 + 3.0 * f


# ---------- characters ----------
def _jag(ob, rnd, amt, below):
    """Ragged hem: push the lowest ring's vertices in and out (before transform_apply)."""
    for v in ob.data.vertices:
        if v.co.z < below:
            k = 1.0 + rnd.uniform(-amt, amt)
            v.co.x *= k
            v.co.y *= k
            v.co.z += rnd.uniform(-amt, amt) * 0.25


def build_ella(m, rnd):
    """Ella (GDD SH1.0 ART-06): bent pointed hat, long hair and torn scarf, layered ragged skirt, laced boots, a
    slender ribbed umbrella with a scalloped rim, crown finial and diamond terminal, one raised hand on the shaft."""
    r = Rig("Ella")
    r.bone("body", (0, 0, -0.2), (0, 0, 0.7))
    r.bone("skirt", (0, 0, 0.0), (0, 0, -0.9), "body")
    r.bone("umbrella_arm", (0.12, 0, 0.52), (0.14, 0, 0.97), "body")
    r.bone("canopy", (0.15, 0, 2.0), (0.15, 0, 1.55), "umbrella_arm")
    r.bone("wand_arm", (0.05, 0, 0.5), (0.05, 0, 0.1), "body")
    ink, stripe, gold, feather = m["hair"], m["stripe"], m["gold"], m["cloth"]
    pi = math.pi
    # ragged layered skirt: five stacked tiers, each wider and torn, over the legs
    for i in range(5):
        z = 0.02 - 0.19 * i
        rad = 0.30 + 0.085 * i
        t = r.add("primitive_cone_add", "skirt", feather if i % 2 else ink, loc=(-0.02 * i, 0, z - 0.2),
                  vertices=18, radius1=rad, radius2=0.17 + 0.02 * i, depth=0.4)
        _jag(t, rnd, 0.22, -0.15)
    for k in range(7):   # torn points that hang below the last tier
        x = -0.34 + 0.115 * k
        r.add("primitive_cone_add", "skirt", ink, loc=(x, rnd.uniform(-0.1, 0.1), -0.98 - rnd.uniform(0.0, 0.1)),
              rot=(pi, rnd.uniform(-0.25, 0.25), 0), vertices=3, radius1=0.07, radius2=0.0, depth=0.26)
    # legs and laced boots
    for x, dz, bend in ((-0.09, 0.0, 0.0), (0.05, 0.1, 0.9)):   # second knee bent: she is airborne, not standing
        r.add("primitive_cylinder_add", "body", feather, loc=(x, 0, -1.1 + dz), vertices=8, radius=0.05, depth=0.36)
        sx = -0.17 * math.sin(bend)
        r.add("primitive_cylinder_add", "body", ink, loc=(x + sx, 0, -1.3 + dz + 0.04 * bend), rot=(0, -bend * 0.5, 0),
              vertices=8, radius=0.062, depth=0.26)
        r.add("primitive_cube_add", "body", ink, loc=(x + sx * 1.6 + 0.07, 0, -1.42 + dz + 0.09 * bend),
              rot=(0, -bend * 0.5, 0), size=1, scale=(0.22, 0.09, 0.09))
        for q in range(3):
            r.add("primitive_torus_add", "body", gold, loc=(x + sx * 0.8, 0, -1.22 + dz - 0.06 * q),
                  major_radius=0.066, minor_radius=0.008, major_segments=10, minor_segments=4)
    # torso, belt, shoulder
    r.add("primitive_cylinder_add", "body", feather, loc=(0, 0, 0.32), vertices=14, radius=0.17, depth=0.62,
          scale=(1.0, 0.7, 1.0))
    r.add("primitive_cylinder_add", "body", gold, loc=(0, 0, 0.12), vertices=14, radius=0.178, depth=0.05,
          scale=(1.0, 0.72, 1.0))   # belt
    r.add("primitive_uv_sphere_add", "body", ink, loc=(0.1, 0, 0.58), segments=10, ring_count=6, radius=0.11)
    # head, mask, hair
    r.add("primitive_uv_sphere_add", "body", ink, loc=(0.02, 0, 0.84), segments=16, ring_count=10, radius=0.2)
    r.add("primitive_cylinder_add", "body", feather, loc=(0.08, -0.12, 0.8), rot=(pi / 2, 0, 0), vertices=10,
          radius=0.12, depth=0.1)   # cloth mask over the lower face
    r.add("primitive_uv_sphere_add", "body", m["amber"], loc=(0.16, -0.17, 0.89), segments=8, ring_count=6,
          radius=0.028)   # the eye glint the references show
    for k in range(7):   # long hair streaming back in the wind, in wavy cones
        y = rnd.uniform(-0.05, 0.05)
        ln = 0.7 + rnd.uniform(0.0, 0.4)
        r.add("primitive_cone_add", "body", feather if k % 2 else ink, loc=(-0.2 - 0.35 * ln, y, 0.7 - 0.07 * k),
              rot=(0, pi / 2 + 0.28 + 0.05 * k, 0), vertices=5, radius1=0.05, radius2=0.0, depth=ln)
    # torn scarf: a flat ribbon blown back, with ragged points
    for k in range(3):
        r.add("primitive_cube_add", "body", feather, loc=(-0.3 - 0.27 * k, 0.02, 0.58 - 0.07 * k),
              rot=(0, 0.3 + 0.12 * k, 0), size=1, scale=(0.34, 0.02, 0.15 - 0.03 * k))
        r.add("primitive_cone_add", "body", feather, loc=(-0.5 - 0.27 * k, 0.02, 0.52 - 0.1 * k),
              rot=(0, pi / 2 + 0.35, 0), vertices=3, radius1=0.07, radius2=0.0, depth=0.22)
    # hat: wide curved brim, then a pointed cone bent over in three sections
    r.add("primitive_cylinder_add", "body", ink, loc=(0.0, 0, 1.02), rot=(0, -0.14, 0), vertices=24, radius=0.46,
          depth=0.03, scale=(1.0, 0.55, 1.0))
    r.add("primitive_cone_add", "body", ink, loc=(-0.02, 0, 1.2), rot=(0, -0.1, 0), vertices=14, radius1=0.25,
          radius2=0.17, depth=0.3)
    r.add("primitive_cone_add", "body", feather, loc=(-0.1, 0, 1.45), rot=(0, -0.45, 0), vertices=14, radius1=0.17,
          radius2=0.1, depth=0.3)
    r.add("primitive_cone_add", "body", ink, loc=(-0.31, 0, 1.65), rot=(0, -0.95, 0), vertices=12, radius1=0.1,
          radius2=0.0, depth=0.42)
    r.add("primitive_torus_add", "body", gold, loc=(-0.02, 0, 1.08), major_radius=0.25, minor_radius=0.014,
          major_segments=16, minor_segments=4)   # hat band
    # umbrella: sleeve, raised hand, slender shaft, diamond terminal below the hand
    r.add("primitive_cylinder_add", "umbrella_arm", ink, loc=(0.13, 0, 0.74), vertices=8, radius=0.055, depth=0.5)
    r.add("primitive_uv_sphere_add", "umbrella_arm", feather, loc=(0.15, 0, 0.98), segments=8, ring_count=6,
          radius=0.06)   # hand
    r.add("primitive_cylinder_add", "umbrella_arm", gold, loc=(0.15, 0, 1.38), vertices=8, radius=0.02, depth=1.3)
    r.add("primitive_cone_add", "umbrella_arm", gold, loc=(0.15, 0, 0.62), rot=(pi, 0, 0), vertices=4,
          radius1=0.05, radius2=0.0, depth=0.16)   # diamond terminal: two cones
    r.add("primitive_cone_add", "umbrella_arm", gold, loc=(0.15, 0, 0.7), vertices=4, radius1=0.05, radius2=0.0,
          depth=0.12)
    # canopy: 16 ribbed gores alternating stripe/ink, scalloped rim, rib tips, crown finial
    can = r.add("primitive_cone_add", "canopy", ink, loc=(0.15, 0, 1.78), vertices=16, radius1=1.05, radius2=0.03,
                depth=0.46)
    can.data.materials.append(stripe)
    for v in can.data.vertices:
        if v.co.z < -0.2:   # scallop: every second rim vertex pulled up and in
            idx = v.index
            if idx % 2:
                v.co.z += 0.07
                v.co.x *= 0.93
                v.co.y *= 0.93
    for i, poly in enumerate(can.data.polygons):
        poly.material_index = i % 2
    rim = 16
    for k in range(rim):
        a = 2 * pi * k / rim
        dx, dy, dz = 1.05 * math.cos(a), 1.05 * math.sin(a), -0.46
        ln = math.sqrt(dx * dx + dy * dy + dz * dz)
        r.add("primitive_cylinder_add", "canopy", gold, loc=(0.15 + dx / 2, dy / 2, 2.0 + dz / 2 - 0.02),
              rot=(0, math.acos(dz / ln), math.atan2(dy, dx)), vertices=4, radius=0.012, depth=ln)
        r.add("primitive_cone_add", "canopy", gold, loc=(0.15 + 1.03 * math.cos(a), 1.03 * math.sin(a), 1.56),
              rot=(pi, 0, 0), vertices=3, radius1=0.04, radius2=0.0, depth=0.12)
    r.add("primitive_cone_add", "canopy", gold, loc=(0.15, 0, 2.06), vertices=4, radius1=0.045, radius2=0.0,
          depth=0.2)   # crown finial
    r.add("primitive_uv_sphere_add", "canopy", gold, loc=(0.15, 0, 2.0), segments=8, ring_count=6, radius=0.04)
    # the free arm: sleeve and hand, lifted behind the body
    r.add("primitive_cylinder_add", "wand_arm", ink, loc=(0.05, 0, 0.3), vertices=8, radius=0.05, depth=0.42)
    r.add("primitive_uv_sphere_add", "wand_arm", feather, loc=(0.05, 0, 0.08), segments=8, ring_count=6, radius=0.055)
    lean = 0.2   # airborne lean: the figure hangs diagonally from the raised umbrella, not upright
    rot = Matrix.Rotation(lean, 3, "Y")
    for name, (h, t, par) in list(r.bones.items()):
        r.bones[name] = (rot @ h, rot @ t, par)
    for ob, _ in r.parts:
        ob.data.transform(rot.to_4x4())
    return r.build(), {}


def build_owl(m, rnd):
    """Front view, wings spread in the picture plane. wing_far is the +X wing; wing_near (-X) is mirrored, so one
    positive angle lifts both wings."""
    r = Rig("Owl")
    r.bone("body", (0, 0, -1.6), (0, 0, 1.2))
    r.bone("head", (0, 0, 1.2), (0, 0, 2.6), "body")
    r.bone("tail", (0, 0, -1.6), (0, 0, -2.8), "body")
    r.bone("wing_far", (0.95, 0, 0.9), (3.6, 0, 1.4), "body")
    r.bone("wing_near", (-0.95, 0, 0.9), (-3.6, 0, 1.4), "body")
    ink, fea = m["ink"], m["feather"]
    r.add("primitive_uv_sphere_add", "body", fea, loc=(0, 0, -0.2), segments=20, ring_count=12, radius=1.0,
          scale=(1.35, 0.9, 1.8))
    for i in range(7):   # ruff of chest feathers, dark on dark
        a = -0.9 + i * 0.3
        r.add("primitive_cone_add", "body", ink, loc=(1.15 * math.sin(a), -0.55, -1.2 + 0.15 * abs(a)),
              rot=(0, a * 0.4, 0), vertices=3, radius1=0.16, radius2=0.0, depth=0.55, scale=(1, 0.3, 1))
    r.add("primitive_uv_sphere_add", "head", fea, loc=(0, 0, 1.95), segments=18, ring_count=10, radius=0.95,
          scale=(1.1, 0.9, 0.9))
    for s in (-1, 1):
        r.add("primitive_cone_add", "head", ink, loc=(0.62 * s, 0, 2.75), rot=(0, 0.35 * s, 0), vertices=4,
              radius1=0.2, radius2=0.0, depth=0.75)   # ear tufts
        r.add("primitive_uv_sphere_add", "head", ink, loc=(0.38 * s, -0.72, 2.05), segments=12, ring_count=8,
              radius=0.27, scale=(1, 0.4, 1))   # eye socket
        r.add("primitive_uv_sphere_add", "head", m["amber"], loc=(0.38 * s, -0.86, 2.05), segments=12,
              ring_count=8, radius=0.17, scale=(1, 0.4, 1))
    r.add("primitive_cone_add", "head", ink, loc=(0, -0.85, 1.72), rot=(math.pi, 0, 0), vertices=4, radius1=0.12,
          radius2=0.0, depth=0.35)   # beak
    # GDD SH1.0 OWL-08 / ART-06: the Keeper is crownless (the key art's gear crown and spires are gone)
    # chest clock: ink bezel, gold face, ink ticks and hands
    r.add("primitive_cylinder_add", "body", ink, loc=(0, -0.95, -0.05), rot=(math.pi / 2, 0, 0), vertices=24,
          radius=0.72, depth=0.08)
    r.add("primitive_cylinder_add", "body", m["gold"], loc=(0, -1.0, -0.05), rot=(math.pi / 2, 0, 0),
          vertices=24, radius=0.62, depth=0.06)
    for k in range(12):
        a = 2 * math.pi * k / 12
        r.add("primitive_cube_add", "body", ink, loc=(0.52 * math.cos(a), -1.04, -0.05 + 0.52 * math.sin(a)),
              rot=(0, -a, 0), size=1, scale=(0.12, 0.02, 0.03))
    r.add("primitive_cube_add", "body", ink, loc=(0.0, -1.06, 0.15), size=1, scale=(0.04, 0.02, 0.42))
    r.add("primitive_cube_add", "body", ink, loc=(0.14, -1.06, -0.05), rot=(0, 0.9, 0), size=1,
          scale=(0.03, 0.02, 0.32))
    for s, bone in ((1, "wing_far"), (-1, "wing_near")):   # ragged feather cards fanned from the shoulder
        for k in range(6):
            a = 0.55 - k * 0.24
            ln = 2.9 - k * 0.22 + rnd.uniform(-0.25, 0.25)
            cx = 0.95 + math.cos(a) * ln / 2
            cz = 0.9 + math.sin(a) * ln / 2
            r.add("primitive_cube_add", bone, fea if k % 2 else ink, loc=(cx * s, 0.1 + 0.02 * k, cz),
                  rot=(0, -a * s, 0), size=1, scale=(ln, 0.06, 0.3 - 0.02 * k))
            r.add("primitive_cone_add", bone, ink, loc=((0.95 + math.cos(a) * ln) * s, 0.1, 0.9 + math.sin(a) * ln),
                  rot=(0, (math.pi / 2 - a) * s, 0), vertices=3, radius1=0.15, radius2=0.0, depth=0.4)
    r.add("primitive_cone_add", "tail", ink, loc=(0, 0.1, -2.15), rot=(math.pi, 0, 0), vertices=5, radius1=0.6,
          radius2=0.1, depth=1.2, scale=(1, 0.3, 1))
    for s in (-1, 1):
        r.add("primitive_cone_add", "body", ink, loc=(0.45 * s, -0.3, -2.0), rot=(math.pi, 0, 0), vertices=4,
              radius1=0.12, radius2=0.0, depth=0.45)   # talons
    return r.build(), {"mirror_bones": ("wing_near",)}


def build_bolt(m, rnd):
    """Four-point cross bolt (vfx_spec: bright core, shell, trail). Built flying +X; the layout faces it left."""
    r = Rig("Bolt")
    r.bone("body", (-0.5, 0, 0), (0.5, 0, 0))
    for rot in (0.0, math.pi / 2):
        r.add("primitive_cone_add", "body", m["rust"], loc=(0, 0, 0), rot=(0, rot + math.pi / 2, 0), vertices=4,
              radius1=0.22, radius2=0.0, depth=1.5, scale=(1, 0.3, 1))
        r.add("primitive_cone_add", "body", m["rust"], loc=(0, 0, 0), rot=(0, rot - math.pi / 2, 0), vertices=4,
              radius1=0.22, radius2=0.0, depth=1.5, scale=(1, 0.3, 1))
    r.add("primitive_uv_sphere_add", "body", m["redshadow"], loc=(0, 0.05, 0), segments=12, ring_count=8,
          radius=0.36, scale=(1, 0.2, 1))   # shell
    r.add("primitive_uv_sphere_add", "body", m["core"], loc=(0, -0.1, 0), segments=12, ring_count=8, radius=0.14,
          scale=(1, 0.3, 1))   # core
    r.add("primitive_cone_add", "body", m["redshadow"], loc=(-1.25, 0.1, 0), rot=(0, -math.pi / 2, 0), vertices=6,
          radius1=0.14, radius2=0.0, depth=1.4, scale=(1, 0.3, 1))   # trail
    return r.build(), {}


def build_skyline(m, rnd):
    """The black jagged skyline: rock band, spires, roofs and a few gears, origin at the bottom-left corner."""
    r = Rig("Skyline")
    r.bone("body", (0, 0, 0), (0, 0, 1))
    ink = m["ink"]
    x = 0.0
    while x < 80.0:
        w = rnd.uniform(1.2, 3.5)
        h = rnd.uniform(1.5, 5.5)
        r.add("primitive_cube_add", "body", ink, loc=(x + w / 2, 0, h / 2), size=1, scale=(w, 1, h))
        kind = rnd.random()
        if kind < 0.35:
            sh = rnd.uniform(2.0, 7.0)
            r.add("primitive_cone_add", "body", ink, loc=(x + w / 2, 0, h + sh / 2), vertices=4, radius1=w * 0.35,
                  radius2=0.0, depth=sh)
        elif kind < 0.6:
            r.add("primitive_cone_add", "body", ink, loc=(x + w / 2, 0, h + 0.6), vertices=4, radius1=w * 0.72,
                  radius2=0.0, depth=1.2, rot=(0, 0, math.pi / 4), scale=(1, 0.3, 1))
        elif kind < 0.7:
            r.add("primitive_cylinder_add", "body", ink, loc=(x + w / 2, -0.6, h + 0.9), rot=(math.pi / 2, 0, 0),
                  vertices=12, radius=0.9, depth=0.2)
            for k in range(8):
                a = 2 * math.pi * k / 8
                r.add("primitive_cube_add", "body", ink, loc=(x + w / 2 + math.cos(a), -0.6, h + 0.9 + math.sin(a)),
                      size=1, scale=(0.3, 0.2, 0.3))
        x += w * rnd.uniform(0.7, 1.0)
    for k in range(40):   # jagged rock along the bottom
        r.add("primitive_cone_add", "body", ink, loc=(k * 2.0 + rnd.uniform(0, 1.5), -0.8, 0.6), vertices=3,
              radius1=rnd.uniform(0.8, 1.6), radius2=0.0, depth=rnd.uniform(1.0, 3.0), scale=(1, 0.3, 1))
    return r.build(), {}


BUILDERS = {"ella": build_ella, "owl": build_owl, "bolt": build_bolt, "skyline": build_skyline}


# ---------- scene ----------
def set_engine(scene):
    for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):   # 5.x id, then 4.2-4.5 [VERIFY on the installed version]
        try:
            scene.render.engine = eng
            return eng
        except TypeError:
            continue
    scene.render.engine = "CYCLES"
    return "CYCLES"


def camera(scene, job):
    w, h = job["frame_size"]
    ppu = job["px_per_unit"]
    scene.render.resolution_x, scene.render.resolution_y = w, h
    scene.render.resolution_percentage = 100
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    scene.collection.objects.link(cam)
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = max(w, h) / ppu
    px, py = job["pivot_px"]
    # the world origin (the rig's root) lands on pixel (px, py), y counted from the top
    cam.location = ((w / 2.0 - px) / ppu, -40.0, (py - h / 2.0) / ppu)
    cam.rotation_euler = (math.pi / 2, 0, 0)
    cam.data.clip_end = 200.0
    scene.camera = cam
    return cam


def light(scene, look):
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    sun.data.energy = 3.0
    ax, ay, az = (math.radians(v) for v in look.get("light_deg", [62, 0, 18]))
    sun.rotation_euler = (ax, ay, az)
    scene.collection.objects.link(sun)
    world = bpy.data.worlds.new("world")
    world.color = (0.0, 0.0, 0.0)
    scene.world = world


def lines(scene, ink_hex, px):
    """Freestyle ink lines. Returns 'on' or 'off' (a build without Freestyle)."""
    try:
        scene.render.use_freestyle = True
        scene.render.line_thickness_mode = "ABSOLUTE"
        scene.render.line_thickness = float(px)
        vl = scene.view_layers[0]
        vl.use_freestyle = True
        fs = vl.freestyle_settings
        ls = fs.linesets[0] if len(fs.linesets) else fs.linesets.new("ink")
        ls.select_by_visibility = True
        ls.select_silhouette = ls.select_border = ls.select_crease = True
        if ls.linestyle is None:   # an empty factory scene has a line set without a style
            ls.linestyle = bpy.data.linestyles.new("ink")
        ls.linestyle.color = hex_rgb(ink_hex)[:3]
        ls.linestyle.thickness = float(px)
        return "on"
    except (AttributeError, TypeError, RuntimeError):
        return "off"


def compositor_grain(scene, grain):
    """A paper-grain pass in the compositor where the installed version supports it [VERIFY: the compositor API
    changed in Blender 5 (node groups)]; the material grain is always there. Returns 'on' or 'off'."""
    try:
        if hasattr(scene, "compositing_node_group"):   # Blender 5.x
            tree = bpy.data.node_groups.new("paper_grain", "CompositorNodeTree")
            scene.compositing_node_group = tree
            tree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
            out = tree.nodes.new("NodeGroupOutput")
        else:   # 4.x
            scene.use_nodes = True
            tree = scene.node_tree
            tree.nodes.clear()
            out = tree.nodes.new("CompositorNodeComposite")
        rl = tree.nodes.new("CompositorNodeRLayers")
        noise = tree.nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 220.0
        mix = tree.nodes.new("ShaderNodeMath")
        mix.operation = "MULTIPLY_ADD"
        mix.inputs[1].default_value = grain
        mix.inputs[2].default_value = 1.0 - grain
        mul = tree.nodes.new("ShaderNodeVectorMath")
        mul.operation = "SCALE"
        alpha = tree.nodes.new("CompositorNodeSetAlpha")
        tree.links.new(noise.outputs["Fac"], mix.inputs[0])
        tree.links.new(rl.outputs["Image"], mul.inputs[0])
        tree.links.new(mix.outputs[0], mul.inputs["Scale"])
        tree.links.new(mul.outputs[0], alpha.inputs["Image"])
        tree.links.new(rl.outputs["Alpha"], alpha.inputs["Alpha"])
        tree.links.new(alpha.outputs["Image"], out.inputs[0])
        return "on"
    except (AttributeError, TypeError, RuntimeError, KeyError, IndexError):
        return "off"


def setup(job):
    """Empty scene with camera, light, look; returns (scene, armature, extra, report)."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    eng = set_engine(scene)
    scene.render.film_transparent = True
    scene.view_settings.view_transform = "Standard"
    try:
        scene.view_settings.look = "None"
    except TypeError:
        pass
    img = scene.render.image_settings
    img.file_format, img.color_mode, img.color_depth = "PNG", "RGBA", "8"
    look = job["look"]
    try:
        scene.eevee.taa_render_samples = int(look.get("samples", 16))
    except AttributeError:
        pass
    rnd = random.Random(int(look.get("seed", 11)))
    mats = materials(job["colours"], look)
    arm, extra = BUILDERS[job["builder"]](mats, rnd)
    if job.get("faces") == "left":
        arm.scale.x = -1.0
    camera(scene, job)
    light(scene, look)
    rep = {"engine": eng, "freestyle": lines(scene, job["colours"].get(look.get("ink", "ink"), "#171614"),
                                             look.get("line_px", 1.6)),
           "compositor": compositor_grain(scene, float(look.get("grain", 0.06)))}
    return scene, arm, extra, rep
