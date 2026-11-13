#!/usr/bin/env python3
"""Point the 10 artfx vfx elements at their crops (refs); the old whole-sheet refs move to context (look only)."""
import json
P = "pipeline/art/references.json"
d = json.load(open(P)); R = {r["id"]: r for r in d["references"]}
for el in [k for k in d["elements"] if k in "vfx-gold-fade vfx-gold-impact vfx-gust vfx-gust-puff vfx-light-shaft vfx-light-spill vfx-umbra vfx-blackout vfx-blocked vfx-slow".split()]:
    c = json.load(open(f"pipeline/art/reference/crops/{el}/crops.json"))
    ids = []
    for cr in c["crops"]:
        name = cr["file"][:-4]; rid = f"crop-{el[4:]}-{name}"; ids.append(rid)
        if rid in R: continue
        r = {"id": rid, "path": f"pipeline/art/reference/crops/{el}/{cr['file']}", "kind": "image", "role": ["effects"],
             "what": f"Crop of the effect itself for {el}: box {cr['box']} of {cr['source'].split('/')[-1]}, key {cr['key']} (crops.json beside it). Reference only; the whole sheet stays as context.",
             "cards": ["MVP 5", "artfx"], "judge": True, "required": True,
             "origin": "crop of a team concept sheet (13 Nov, artfx, D-new-vfx-calibration), keyed to an alpha mask; reference only"}
        d["references"].append(r); R[rid] = r
    e = d["elements"][el]
    old = [x for x in e["refs"] if not x.startswith("crop-")]
    e["context"] = list(dict.fromkeys(e.get("context", []) + old))
    e["refs"] = ids
json.dump(d, open(P, "w"), indent=1, ensure_ascii=False); open(P, "a").write("\n")
