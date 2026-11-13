#!/usr/bin/env python3
"""artfx3: cut the effect itself out of the concept sheets for the 8 artfx3 vfx elements (originals never edited).
Reuses pipeline/art/proof/artfx2/make_crops.py (keyer, close, pieces) and adds keys: gold (yellow/amber shots, pale core),
arc (blue-white arcs). Writes pipeline/art/reference/crops/<element>/<name>.png and crops.json."""
import json, math, os, sys
sys.path.insert(0, "tools"); sys.path.insert(0, "pipeline/art/proof/artfx2")
from png import read_png, write_png
from art_judge import lab
import make_crops as M

D = M.D
S_Y = D + "20261110-0328_Ricky_1.png"   # yellow shots sheet
S_GEAR = D + "20261110-1047_Ricky_1.png"
S_CLK = D + "20261110-1220_Ricky_1.png"
SPEC = {
 "vfx-needle-sliver": [("travel", S_Y, (480, 465, 620, 500), "gold", "all"),
                       ("shot-diagram", S_Y, (1025, 190, 1420, 290), "gold", "largest")],
 "vfx-needle-channel": [("tell-ring", S_Y, (85, 465, 130, 510), "gold", "all"),
                        ("lit-flame", S_Y, (650, 825, 725, 860), "gold", "all")],
 "vfx-needle-pierce": [("release", S_Y, (245, 455, 390, 515), "gold", "all"),
                       ("fade", S_Y, (695, 470, 810, 495), "gold", "all")],
 "vfx-stream-start": [("release-burst", S_Y, (245, 455, 330, 515), "gold", "all"),
                      ("fall-flame", S_Y, (995, 825, 1070, 860), "gold", "all")],
 "vfx-stream-sustain": [("lit-flame", S_Y, (650, 825, 725, 860), "gold", "all"),
                        ("fall-flame", S_Y, (995, 825, 1070, 860), "gold", "all")],
 "vfx-part-hit": [("gear-swing", S_GEAR, (725, 340, 920, 430), "paper", "all"),
                ("gear-intact", S_GEAR, (225, 355, 320, 440), "paper", "all")],
 "vfx-part-break": [("rim-failure", S_GEAR, (1200, 345, 1340, 440), "paper", "all"),
                    ("wreckage", S_GEAR, (400, 780, 520, 858), "paper", "all")],
 "vfx-stun": [("arcs-clock", S_CLK, (780, 540, 1000, 720), "arc", "all"),
              ("arcs-shoulder", S_CLK, (170, 570, 350, 720), "arc", "all")],
}
_k = M.keyer
def keyer(key, rows, w, h):
    if key in ("gold", "arc"):
        m = [[False] * w for _ in range(h)]
        for y in range(h):
            for x in range(w):
                L, a, b = lab(rows[y][x]); c = math.hypot(a, b); hu = math.degrees(math.atan2(b, a)) % 360
                if key == "gold":
                    m[y][x] = (c >= 38 and 40 <= hu <= 110) or (L > 90 and c < 30)
                else:
                    m[y][x] = (c >= 18 and 200 <= hu <= 280 and L > 60) or (L > 94 and c < 12)
        return m
    return _k(key, rows, w, h)
M.keyer = keyer
M.SPEC = {k: v for k, v in SPEC.items() if not os.environ.get("ONLY") or k == os.environ["ONLY"]}
if __name__ == "__main__":
    M.main()
