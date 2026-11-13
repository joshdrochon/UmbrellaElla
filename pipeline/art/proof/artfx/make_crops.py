#!/usr/bin/env python3
"""Crops of the effect itself for the 10 artfx vfx elements (method of artfx2, D-new-vfx-calibration). Originals untouched.
Writes pipeline/art/reference/crops/<element>/<name>.png + crops.json. New keys on top of artfx2's: gale (blue-tinted
light wind on warm paper), all (whole box opaque: dark fog and veil studies). Stdlib only."""
import json, os, sys
sys.path.insert(0, "tools"); sys.path.insert(0, "pipeline/art/proof/artfx2")
import make_crops as M
from png import read_png, write_png
from art_judge import lab

OUT = M.OUT
S0348 = M.D + "20261110-0348_Ricky_1.png"
GOLD_A, GOLD_B, GLOW, FLOW = (1290, 225, 1420, 260), (1210, 280, 1315, 308), (380, 320, 600, 450), (1000, 140, 1672, 260)
FOG_LOW, FOG_ARCH = (150, 560, 760, 700), (100, 60, 620, 230)
SPEC = {
 "vfx-gold-impact": [("gold-shot-a", M.S_REALM, GOLD_A, "dark", "all"), ("gold-shot-b", M.S_REALM, GOLD_B, "dark", "all"),
                     ("umbrella-glow", M.S_REALM, GLOW, "dark", "all")],
 "vfx-gold-fade": [("gold-shot-a", M.S_REALM, GOLD_A, "dark", "all"), ("gold-shot-b", M.S_REALM, GOLD_B, "dark", "all")],
 "vfx-blocked": [("gold-shot-b", M.S_REALM, GOLD_B, "dark", "all"), ("umbrella-glow", M.S_REALM, GLOW, "dark", "all")],
 "vfx-light-spill": [("umbrella-glow", M.S_REALM, GLOW, "dark", "all"), ("gold-shot-a", M.S_REALM, GOLD_A, "dark", "all")],
 "vfx-gust": [("damaging-gust", S0348, (866, 490, 1145, 645), "gale", "all"), ("flow-ribbon", M.S_REALM, FLOW, "dark", "all")],
 "vfx-gust-puff": [("flap", S0348, (232, 500, 400, 650), "gale2", "all"), ("gust-front", S0348, (440, 500, 560, 650), "gale2", "all")],
 "vfx-slow": [("clock-face", M.S0800, (130, 165, 400, 430), "ellipse", "all"), ("reload-arc", M.S0800, (290, 450, 420, 600), "red", "all")],
 "vfx-light-shaft": [("umbrella-glow", M.S_REALM, GLOW, "dark", "all"), ("flow-ribbon", M.S_REALM, FLOW, "dark", "all")],
 "vfx-umbra": [("fog-low", M.S_REALM, FOG_LOW, "all", "all"), ("fog-arch", M.S_REALM, FOG_ARCH, "all", "all")],
 "vfx-blackout": [("fog-low", M.S_REALM, FOG_LOW, "all", "all"), ("fog-arch", M.S_REALM, FOG_ARCH, "all", "all")],
}
_k = M.keyer
def keyer(key, rows, w, h):
    if key == "all": return [[True] * w for _ in range(h)]
    if key == "gale":  # blue-tinted light (gale/edge #DCEAF0/#5A91B3) against warm paper
        return [[(lambda t: t[2] < -3 and t[0] > 45)(lab(rows[y][x])) for x in range(w)] for y in range(h)]
    if key == "gale2":  # looser: pale cool-grey sweeps with little blue
        return [[(lambda t: t[2] < 1 and t[0] > 50)(lab(rows[y][x])) for x in range(w)] for y in range(h)]
    return _k(key, rows, w, h)
M.keyer = keyer
_close = M.close
M.close = lambda m, w, h, r=2: m if all(all(r_) for r_ in m) else _close(m, w, h, r)
M.SPEC = {k: v for k, v in SPEC.items() if not os.path.exists(OUT + k + "/crops.json")}
if __name__ == "__main__": M.main()
