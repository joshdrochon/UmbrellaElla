"""Cut every artfx3 draft with the highest saturation cap whose art_check --effect colour rules pass.
  python3 pipeline/art/proof/artfx3/cut_all.py <draftN> <sheetN>   (e.g. draft1 sheet1)"""
import os, shutil, subprocess, sys
root = "pipeline/art/proof/artfx3"
draft, sheet = sys.argv[1], sys.argv[2]
blender = shutil.which("blender") or "/Applications/Blender.app/Contents/MacOS/Blender"
for p in ["NeedleChannel", "NeedleSliver", "NeedlePierce", "StreamStart", "StreamSustain", "PartHit", "PartBreak", "Stun"]:
    d = f"{root}/{p}"
    if not os.path.exists(f"{d}/{draft}.png"):
        continue
    for cap in [0.55, 0.50, 0.46, 0.42, 0.38, 0.35, 0.32, 0.30, 0.27]:
        subprocess.run([blender, "-b", "--factory-startup", "-P", f"{root}/cut_strip.py", "--", f"{d}/{draft}.png", f"{d}/{sheet}.png"],
                       env={**os.environ, "SATCAP": str(cap)}, capture_output=True)
        r = subprocess.run([sys.executable, "tools/art_check.py", "--effect", f"{d}/{sheet}.png"], capture_output=True, text=True)
        if r.returncode == 0:
            break
    print(p, "satcap", cap, "exit", r.returncode)
