#!/usr/bin/env python3
"""Point the 8 artfx3 vfx elements at their crop references (D-new-vfx-calibration). The old sheet refs move to `context`.
Adds one reference entry per crop (as artfx2 did). Re-runnable."""
import json, sys
P = "pipeline/art/references.json"
refs = json.load(open(P))
have = {x["id"] for x in refs["references"]}
WHAT = {
 "vfx-needle-sliver": "the Needle sliver in travel", "vfx-needle-channel": "the Needle channel (tell ring and lit shot)",
 "vfx-needle-pierce": "the Needle penetration (release burst and fading shot)", "vfx-stream-start": "the Streamed Blast startup (release burst and lit flame)",
 "vfx-stream-sustain": "the Streamed Blast sustain (lit flame)", "vfx-part-hit": "a Keeper part hit (gear swinging on its chain)",
 "vfx-part-break": "a Keeper part break (rim and spoke failure, wreckage)", "vfx-stun": "the Keeper stun (blue-white fault arcs)"}
for el, what in WHAT.items():
    d = json.load(open(f"pipeline/art/reference/crops/{el}/crops.json"))
    ids = []
    for c in d["crops"]:
        rid = "crop-" + el[4:] + "-" + c["file"][:-4]
        ids.append(rid)
        if rid not in have:
            refs["references"].append({"id": rid, "path": f"pipeline/art/reference/crops/{el}/{c['file']}", "kind": "image", "role": ["effects"],
              "what": f"Crop of the effect itself for {what}: box {c['box']} of {c['source'].split('/')[-1]}, key {c['key']} (crops.json beside it). Reference only; the whole sheet stays as context.",
              "cards": ["MVP 5"], "judge": True, "required": True,
              "origin": "crop of Ricky's #art-direction sheet (13 Nov, artfx3, D-new-vfx-calibration), keyed to an alpha mask; reference only"})
            have.add(rid)
    e = refs["elements"][el]
    if not all(i in e["refs"] for i in ids):
        old = [r for r in e["refs"] if not r.startswith("crop-")]
        e["refs"] = ids
        e["context"] = list(dict.fromkeys(old + ([ "d-yellow-shots"] if "needle" in el or "stream" in el else [])))
json.dump(refs, open(P, "w"), indent=1)
