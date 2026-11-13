"""Keeper of Time owl, Blender builder (run by Blender, never python3):

  blender -b --factory-startup -P tools/build/assets/art_keeper_owl.py -- --job Art/Source/Keeper/Raw/Owl_Flap/Owl_Flap.job.json

GDD SH1.0 OWL-08 / ART-06: a crownless fabricated metal owl, left-facing side profile, rigid vane wings, two feet,
chest clock, three hanging mechanisms (lantern cage, ring gimbal, gear) on chains. Registers the `keeper` builder in
pipeline/art/blender/stand_ins.py's table and runs the shared sprite renderer, so the look (toon ramps, ink lines,
grain, light, camera) stays the team's. Built facing +X; the renderer mirrors for faces=left.
"""
import math
import os
import random
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "pipeline", "art", "blender"))
import stand_ins as si  # noqa: E402

S = math.pi / 2


def build_keeper(m, rnd):
    pal = si.hex_rgb
    plate = m["plate"]
    lite = m["lite"]
    ink, fea, gold, amber = m["ink"], m["feather"], m["gold"], m["amber"]
    r = si.Rig("Keeper")
    r.bone("body", (0, 0, -0.6), (0, 0, 0.8))
    r.bone("head", (1.7, 0, 0.5), (2.5, 0, 0.9), "body")
    r.bone("tail", (-1.7, 0, 0.0), (-3.2, 0, -0.5), "body")
    r.bone("wing_near", (-0.1, -0.35, 0.75), (0.5, -0.35, 1.9), "body")
    r.bone("wing_far", (-0.1, 0.35, 0.75), (0.5, 0.35, 1.9), "body")
    r.bone("mech", (1.0, -0.5, -0.8), (1.0, -0.5, -1.6), "body")

    add = r.add
    # body: tapered barrel, chest plates overlapping like scales
    add("primitive_uv_sphere_add", "body", plate, loc=(0, 0, 0), segments=24, ring_count=14, radius=1.0, scale=(2.1, 0.85, 1.0))
    add("primitive_uv_sphere_add", "body", ink, loc=(-0.3, 0.05, -0.35), segments=20, ring_count=10, radius=1.0, scale=(1.9, 0.8, 0.75))
    for row in range(3):
        for k in range(7):
            x = -1.0 + k * 0.42 + (0.21 if row % 2 else 0)
            z = -0.55 + row * 0.38
            if x > 1.45:
                continue
            add("primitive_cube_add", "body", lite if (k + row) % 2 else plate, loc=(x, -0.62 + 0.03 * row, z),
                rot=(0, 0.3, 0), size=1, scale=(0.5, 0.06, 0.34))
    # neck + head: angular, crownless, flat brow plate
    add("primitive_cylinder_add", "head", fea, loc=(1.55, 0, 0.45), rot=(0, 0.9, 0), vertices=12, radius=0.55, depth=0.9)
    add("primitive_uv_sphere_add", "head", lite, loc=(2.05, 0, 0.9), segments=20, ring_count=12, radius=0.86, scale=(1.05, 0.8, 0.9))
    add("primitive_cube_add", "head", ink, loc=(2.2, -0.2, 1.38), rot=(0, -0.15, 0), size=1, scale=(0.9, 0.5, 0.1))  # flat brow, no tufts
    for k in range(5):  # facial disc feather plates
        add("primitive_cube_add", "head", fea if k % 2 else plate, loc=(1.7 + k * 0.15, -0.55, 0.65 + 0.05 * k),
            rot=(0, 0.2 * k, 0), size=1, scale=(0.35, 0.05, 0.22))
    add("primitive_uv_sphere_add", "head", ink, loc=(2.3, -0.55, 1.0), segments=12, ring_count=8, radius=0.27, scale=(1, 0.4, 1))
    add("primitive_uv_sphere_add", "head", amber, loc=(2.32, -0.66, 1.0), segments=12, ring_count=8, radius=0.19, scale=(1, 0.35, 1))
    add("primitive_cone_add", "head", ink, loc=(2.92, -0.1, 0.7), rot=(0, S + 0.7, 0), vertices=5, radius1=0.2, radius2=0.0, depth=0.7)  # hooked beak
    add("primitive_cone_add", "head", ink, loc=(3.05, -0.1, 0.45), rot=(0, S + 1.7, 0), vertices=4, radius1=0.1, radius2=0.0, depth=0.3)
    # chest clock: gear-toothed bezel, gold face, ticks, hands
    cx, cy, cz = 1.0, -0.84, 0.0
    add("primitive_cylinder_add", "body", ink, loc=(cx, cy, cz), rot=(S, 0, 0), vertices=32, radius=0.98, depth=0.12)
    for k in range(18):
        a = 2 * math.pi * k / 18
        add("primitive_cube_add", "body", ink, loc=(cx + 1.03 * math.cos(a), cy, cz + 1.03 * math.sin(a)), rot=(0, -a, 0),
            size=1, scale=(0.14, 0.12, 0.12))
    add("primitive_cylinder_add", "body", plate, loc=(cx, cy - 0.05, cz), rot=(S, 0, 0), vertices=32, radius=0.84, depth=0.08)
    add("primitive_cylinder_add", "body", gold, loc=(cx, cy - 0.1, cz), rot=(S, 0, 0), vertices=32, radius=0.7, depth=0.06)
    for k in range(12):
        a = 2 * math.pi * k / 12
        add("primitive_cube_add", "body", ink, loc=(cx + 0.58 * math.cos(a), cy - 0.15, cz + 0.58 * math.sin(a)), rot=(0, -a, 0),
            size=1, scale=(0.14 if k % 3 == 0 else 0.08, 0.02, 0.04))
    add("primitive_cube_add", "body", ink, loc=(cx + 0.05, cy - 0.17, cz + 0.27), rot=(0, -0.2, 0), size=1, scale=(0.06, 0.02, 0.56))
    add("primitive_cube_add", "body", ink, loc=(cx + 0.2, cy - 0.17, cz - 0.05), rot=(0, 1.1, 0), size=1, scale=(0.05, 0.02, 0.4))
    add("primitive_uv_sphere_add", "body", ink, loc=(cx, cy - 0.18, cz), segments=10, ring_count=6, radius=0.07)
    # wings: rigid vane plates fanned from a jointed shoulder strut, near one in front and bigger
    for bone, y, sc, tone in (("wing_near", -0.4, 1.0, lite), ("wing_far", 0.45, 0.88, plate)):
        add("primitive_uv_sphere_add", bone, ink, loc=(-0.05, y, 0.8), segments=12, ring_count=8, radius=0.3)
        n = 11
        for k in range(n):
            a = math.radians(146 - k * 4.0)          # direction from +X: up-and-back, sweeping down
            ln = (4.9 - 0.16 * k) * sc + rnd.uniform(-0.1, 0.1)
            ox, oz = -0.05, 0.8
            cxw, czw = ox + math.cos(a) * ln / 2, oz + math.sin(a) * ln / 2
            yy = y + (-0.012 if bone == "wing_near" else 0.012) * k
            mat = tone if k % 2 else plate
            add("primitive_cube_add", bone, mat, loc=(cxw, yy, czw), rot=(0, -a, 0), size=1, scale=(ln, 0.05, 0.4))
            add("primitive_cone_add", bone, ink, loc=(ox + math.cos(a) * ln, yy, oz + math.sin(a) * ln),
                rot=(0, S - a, 0), vertices=3, radius1=0.2, radius2=0.0, depth=0.45, scale=(1, 0.3, 1))
            for t in (0.3, 0.6):   # rivets
                add("primitive_uv_sphere_add", bone, m["rust"], loc=(ox + math.cos(a) * ln * t, yy - 0.04, oz + math.sin(a) * ln * t),
                    segments=6, ring_count=4, radius=0.045)
        a0 = math.radians(146)   # jointed leading-edge strut
        add("primitive_cube_add", bone, ink, loc=(-0.05 + math.cos(a0) * 1.3 * sc, y - 0.05, 0.8 + math.sin(a0) * 1.3 * sc),
            rot=(0, -a0, 0), size=1, scale=(2.6 * sc, 0.1, 0.12))
    # tail: five hard plates
    for k in range(5):
        a = math.radians(188 + (k - 2) * 9)
        ln = 2.0 - 0.1 * abs(k - 2)
        add("primitive_cube_add", "tail", fea if k % 2 else plate, loc=(-1.7 + math.cos(a) * ln / 2, 0.03 * k, math.sin(a) * ln / 2 - 0.1),
            rot=(0, -a, 0), size=1, scale=(ln, 0.05, 0.36))
    # legs: two, hocked, three-toed
    for lx, ly in ((0.35, -0.38), (-0.35, 0.38)):
        add("primitive_cylinder_add", "body", plate, loc=(lx + 0.15, ly, -1.25), rot=(0, 0.35, 0), vertices=8, radius=0.16, depth=1.0)
        add("primitive_cylinder_add", "body", fea, loc=(lx - 0.15, ly, -2.05), rot=(0, -0.3, 0), vertices=8, radius=0.13, depth=0.95)
        add("primitive_uv_sphere_add", "body", ink, loc=(lx + 0.3, ly, -0.8), segments=10, ring_count=6, radius=0.22)
        add("primitive_uv_sphere_add", "body", ink, loc=(lx + 0.0, ly, -1.68), segments=10, ring_count=6, radius=0.17)
        for t in (-0.18, 0.0, 0.18):
            add("primitive_cone_add", "body", ink, loc=(lx - 0.45, ly + t * 0.4, -2.5), rot=(0, S + 0.15 + t, 0), vertices=4,
                radius1=0.09, radius2=0.0, depth=0.7)
        add("primitive_cone_add", "body", ink, loc=(lx + 0.18, ly, -2.5), rot=(0, -S + 0.15, 0), vertices=4, radius1=0.09, radius2=0.0, depth=0.5)
    # three hanging mechanisms on chains from the belly
    def chain(x0, z0, x1, z1, y):
        n = 7
        for k in range(n):
            t = (k + 0.5) / n
            add("primitive_torus_add", "mech", plate if k % 2 else ink, loc=(x0 + (x1 - x0) * t, y, z0 + (z1 - z0) * t),
                rot=(S if k % 2 else 0, 0, 0), major_radius=0.1, minor_radius=0.03, major_segments=10, minor_segments=5)
    chain(0.8, -0.85, 1.35, -1.9, -0.55)
    add("primitive_torus_add", "mech", plate, loc=(1.4, -0.55, -2.15), rot=(S, 0, 0), major_radius=0.28, minor_radius=0.06, major_segments=16, minor_segments=6)
    add("primitive_torus_add", "mech", ink, loc=(1.4, -0.55, -2.15), rot=(0, 0, 0), major_radius=0.28, minor_radius=0.05, major_segments=16, minor_segments=6)
    add("primitive_uv_sphere_add", "mech", ink, loc=(1.4, -0.55, -2.15), segments=10, ring_count=6, radius=0.14)
    chain(1.8, -0.5, 3.3, -1.5, -0.45)   # lantern cage
    add("primitive_cylinder_add", "mech", ink, loc=(3.4, -0.45, -2.1), vertices=6, radius=0.4, depth=0.9)
    add("primitive_cylinder_add", "mech", ink, loc=(3.4, -0.45, -1.6), vertices=6, radius=0.46, depth=0.1)
    add("primitive_cylinder_add", "mech", ink, loc=(3.4, -0.45, -2.6), vertices=6, radius=0.46, depth=0.1)
    add("primitive_uv_sphere_add", "mech", gold, loc=(3.4, -0.9, -2.1), segments=10, ring_count=6, radius=0.18)
    for k in range(6):
        a = 2 * math.pi * k / 6
        add("primitive_cube_add", "mech", ink, loc=(3.4 + 0.44 * math.cos(a), -0.45 + 0.44 * math.sin(a), -2.1), size=1, scale=(0.07, 0.07, 0.9))
    chain(-0.3, -0.85, -0.9, -1.9, -0.5)   # gear
    add("primitive_cylinder_add", "mech", plate, loc=(-0.95, -0.55, -2.25), rot=(S, 0, 0), vertices=20, radius=0.36, depth=0.1)
    for k in range(10):
        a = 2 * math.pi * k / 10
        add("primitive_cube_add", "mech", ink, loc=(-0.95 + 0.4 * math.cos(a), -0.58, -2.25 + 0.4 * math.sin(a)), rot=(0, -a, 0),
            size=1, scale=(0.14, 0.1, 0.12))
    add("primitive_uv_sphere_add", "mech", ink, loc=(-0.95, -0.62, -2.25), segments=8, ring_count=5, radius=0.1)
    return r.build(), {"mirror_bones": ()}


_orig = si.materials


def materials(colours, look):
    d = _orig(colours, look)
    c = colours.get
    d["plate"] = si.toon("plate", [c("owl-feather"), c("paper-stain", "#7b6157"), c("paper-mid", "#93786b")], look)
    d["feather"] = si.toon("feather", [c("owl-umber"), c("owl-feather"), c("paper-stain", "#7b6157")], look)
    d["lite"] = si.toon("lite", [c("paper-stain", "#7b6157"), c("paper-mid", "#93786b"), c("paper-light", "#aa8f7f")], look)
    d["rust"] = si.glow("rust", c("rust-red", "#743422"))
    return d


si.materials = materials
si.BUILDERS["keeper"] = build_keeper

if __name__ == "__main__":
    import render_sprite
    render_sprite.main()
