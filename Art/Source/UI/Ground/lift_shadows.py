"""Lift the deepest shadows of a painted ground so the frame is not crushed (art_check dark_share <= 0.45).
Adds LIFT to each channel at black, tapering to 0 at KNEE (hue kept). Usage: lift_shadows.py in.png out.png [LIFT] [KNEE] [GRAIN]
Our post-processing step on a Gemini output; the threshold is not changed."""
import os, random, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "tools"))
from png import read_png, write_png

src, dst = sys.argv[1], sys.argv[2]
lift = float(sys.argv[3]) if len(sys.argv) > 3 else 10
knee = float(sys.argv[4]) if len(sys.argv) > 4 else 70
grain = float(sys.argv[5]) if len(sys.argv) > 5 else 0
rnd = random.Random(7)  # fixed seed: same bytes every run
w, h, rows = read_png(src)
lut = [min(255, round(v + lift * max(0.0, 1 - v / knee))) for v in range(256)]
def px(r, g, b):
    n = round(rnd.uniform(-grain, grain) * max(0.0, 1 - (r + g + b) / 3 / knee)) if grain else 0
    return (min(255, max(0, lut[r] + n)), min(255, max(0, lut[g] + n)), min(255, max(0, lut[b] + n)), 255)
out = [[px(r, g, b) for r, g, b, a in row] for row in rows]
write_png(dst, w, h, out)
