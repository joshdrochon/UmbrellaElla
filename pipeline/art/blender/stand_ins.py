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
from mathutils import Quaternion, Vector

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
def build_ella(m, rnd):
    r = Rig("Ella")
    r.bone("body", (0, 0, -0.2), (0, 0, 0.7))
    r.bone("skirt", (0, 0, 0.0), (0, 0, -0.9), "body")
    r.bone("umbrella_arm", (0.12, 0, 0.52), (0.14, 0, 0.97), "body")
    r.bone("canopy", (0.15, 0, 2.0), (0.15, 0, 1.55), "umbrella_arm")
    r.bone("wand_arm", (0.05, 0, 0.5), (0.05, 0, 0.1), "body")
    ink, stripe, gold = m["ink"], m["stripe"], m["gold"]
    r.add("primitive_cone_add", "skirt", ink, loc=(0, 0, -0.45), vertices=14, radius1=0.56, radius2=0.17, depth=1.0)
    for i, x in enumerate((-0.12, 0.13)):   # ragged hem
        r.add("primitive_cone_add", "skirt", ink, loc=(x * 3.4, 0, -0.98), rot=(0, 0.5 - i, 0), vertices=3,
              radius1=0.12, radius2=0.0, depth=0.3)
    for x in (-0.09, 0.1):
        r.add("primitive_cylinder_add", "body", ink, loc=(x, 0, -1.08), vertices=8, radius=0.045, depth=0.3)
        r.add("primitive_cube_add", "body", ink, loc=(x + 0.06, 0, -1.24), size=1, scale=(0.18, 0.08, 0.07))
    r.add("primitive_cylinder_add", "body", ink, loc=(0, 0, 0.32), vertices=12, radius=0.17, depth=0.58)
    r.add("primitive_uv_sphere_add", "body", ink, loc=(0.02, 0, 0.84), segments=16, ring_count=10, radius=0.23)
    r.add("primitive_uv_sphere_add", "body", ink, loc=(-0.14, 0, 0.74), segments=12, ring_count=8, radius=0.2,
          scale=(1.0, 0.8, 1.35))   # hair
    r.add("primitive_cylinder_add", "body", ink, loc=(0.0, 0, 1.0), rot=(0, -0.12, 0), vertices=20, radius=0.44,
          depth=0.035)   # hat brim
    r.add("primitive_cone_add", "body", ink, loc=(-0.08, 0, 1.3), rot=(0, -0.42, 0), vertices=12, radius1=0.24,
          radius2=0.0, depth=0.62)
    r.add("primitive_uv_sphere_add", "body", m["amber"], loc=(0.2, -0.2, 0.86), segments=8, ring_count=6,
          radius=0.03)   # the eye glint the references show
    # umbrella: arm, shaft, striped canopy (alternate faces), hook handle
    r.add("primitive_cylinder_add", "umbrella_arm", ink, loc=(0.13, 0, 0.74), vertices=8, radius=0.05, depth=0.46)
    r.add("primitive_cylinder_add", "umbrella_arm", ink, loc=(0.15, 0, 1.38), vertices=8, radius=0.022, depth=1.3)
    r.add("primitive_torus_add", "umbrella_arm", ink, loc=(0.22, 0, 0.74), rot=(math.pi / 2, 0, 0),
          major_radius=0.07, minor_radius=0.018, major_segments=12, minor_segments=6)
    can = r.add("primitive_cone_add", "canopy", ink, loc=(0.15, 0, 1.78), vertices=16, radius1=1.0, radius2=0.03,
                depth=0.44)
    can.data.materials.append(stripe)
    for i, poly in enumerate(can.data.polygons):
        poly.material_index = i % 2
    r.add("primitive_cone_add", "canopy", ink, loc=(0.15, 0, 2.07), vertices=6, radius1=0.03, radius2=0.0,
          depth=0.16)   # ferrule
    for k in range(8):   # rib tips under the rim, so the open canopy reads ragged in silhouette
        a = 2 * math.pi * k / 8
        r.add("primitive_cone_add", "canopy", ink, loc=(0.15 + 0.98 * math.cos(a), 0.98 * math.sin(a), 1.55),
              vertices=3, radius1=0.035, radius2=0.0, depth=0.12)
    # the free arm (GDD SH1.0 ART-06: no wand; spells leave the canopy, card 0.38 adds the second hand on the shaft)
    r.add("primitive_cylinder_add", "wand_arm", ink, loc=(0.05, 0, 0.3), vertices=8, radius=0.045, depth=0.42)
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
