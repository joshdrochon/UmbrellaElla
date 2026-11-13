#!/usr/bin/env python3
"""Calibrate only the 8 artfx2 vfx elements (the full art_judge calibrate also walks the scene refs: ~10 min).
Same function, same margin; --write stores score_min/detail_min/calibration for these elements only."""
import copy, json, sys
sys.path.insert(0, "tools")
import art_judge as J
MINE = ["vfx-keeper-recovery", "vfx-keeper-strike", "vfx-keeper-warning", "vfx-clock-beat", "vfx-clock-open",
        "vfx-eye-exposed", "vfx-departure", "vfx-restoration"]
P = "pipeline/art/references.json"
refs = json.load(open(P))
sub = copy.deepcopy(refs)
sub["elements"] = {k: v for k, v in refs["elements"].items() if k in MINE}
sub["scene"]["refs"] = []
cal = J.calibrate(sub, [J.ROOT])
cal.pop("scene", None)
for k, c in cal.items():
    print(k, c["basis"], c["score_min"], c["detail_min"], c["loo"])
if "--write" in sys.argv:
    tmp = copy.deepcopy(refs)
    J.write_calibration(P, {k: v for k, v in cal.items()})
