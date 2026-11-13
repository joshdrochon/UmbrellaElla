#!/usr/bin/env python3
"""Render the shots art lane's pieces with Blender (owl-bolt, bolt-hit, wand-shot, wind-zone, wind-lines).

  python3 tools/build/assets/art_shots.py <piece> [--out-dir pipeline/art/proof/artshots/<piece>/Raw/Still]
Builds the render job from the shared planner (pipeline/art/blender/plan.py: colours, look, layout sheet), swaps in this
lane's builder (art_shots_blender.py) and runs Blender headless. Prints the frame path.
"""
import argparse
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "pipeline", "art", "blender"))
import plan  # noqa: E402

BLENDER = os.environ.get("BLENDER", "/Applications/Blender.app/Contents/MacOS/Blender")
# piece -> (recipe to borrow look/colours from, builder, asset, frame size, pivot, px per unit, faces)
PIECES = {
    "owl-bolt": ("bolt", "shot_red", "OwlBolt", (160, 80), (46, 40), 30.0, "left"),
    "bolt-hit": ("bolt", "burst_red", "BoltHit", (128, 128), (64, 64), 30.0, "right"),
    "wind-lines": ("bolt", "wind_lines", "WindLines", (408, 128), (204, 64), 40.0, "right"),
    "wind-zone": ("bolt", "wind_zone", "WindZone", (256, 448), (128, 224), 60.0, "right"),
    "wand-shot": ("bolt", "shot_gold", "WandShot", (128, 64), (99, 32), 24.0, "right"),
}


def make_job(piece, out_dir, seed=None, scale=1):
    base, builder, asset, size, pivot, ppu, faces = PIECES[piece]
    j = plan.job(base, "Still", out_dir, root=ROOT, seed=seed)
    j["look"]["line_px"] = 1.0 * scale
    j["look"]["samples"] = 1 if scale == 1 else 24
    j["look"]["filter_px"] = 0.0 if scale == 1 else 0.6
    j["look"]["snap"] = round(1.0 / (ppu * scale), 6)
    j.update(builder=builder, asset=asset, frame_size=[v * scale for v in size], pivot_px=[v * scale for v in pivot],
             px_per_unit=ppu * scale, faces=faces,
             character=piece, anim="Still", layout="recipe")
    j["frames"] = [f"{out_dir}/{asset}_Still_00.png"]
    j["blend"] = f"{out_dir}/{asset}_Still.blend"
    return j


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("piece", choices=sorted(PIECES))
    ap.add_argument("--out-dir")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--scale", type=int, default=1, help="render at N x the layout frame size")
    a = ap.parse_args(argv)
    out = (a.out_dir or f"pipeline/art/proof/artshots/{a.piece}/Raw/Still").rstrip("/")
    j = make_job(a.piece, out, a.seed, a.scale)
    os.makedirs(out, exist_ok=True)
    jp = f"{out}/{j['asset']}_Still.job.json"
    with open(jp, "w", encoding="utf-8") as fh:
        json.dump(j, fh, indent=1)
    script = os.path.join(ROOT, "tools", "build", "assets", "art_shots_blender.py")
    p = subprocess.run([BLENDER, "-b", "--factory-startup", "-P", script, "--", "--job", jp],
                       capture_output=True, text=True, cwd=ROOT)
    line = [x for x in p.stdout.splitlines() if x.startswith("BLENDER_RENDER")]
    if p.returncode or not line:
        print((p.stdout + p.stderr)[-1500:])
        return 1
    print(line[0])
    print(j["frames"][0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
