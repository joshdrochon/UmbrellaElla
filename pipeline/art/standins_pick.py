#!/usr/bin/env python3
"""Rank existing art candidates per piece across lane worktrees (read-only) for the stand-in import.
Rank: most pairs ours/same, art_ref_check pass, calibration passed/sessions, latest round."""
import glob, json, os, sys, hashlib
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
AREAS = os.path.dirname(ROOT)

def candidates():
    best = {}
    for f in glob.glob(os.path.join(AREAS, "*", "pipeline", "art", "critic", "*.json")):
        lane = f.split(os.sep)[-5]
        if lane == os.path.basename(ROOT):
            continue
        try:
            recs = json.load(open(f)).get("records", [])
        except Exception:
            continue
        for r in recs:
            p = os.path.join(AREAS, lane, r.get("file", ""))
            if not r.get("file") or not os.path.isfile(p) or not p.lower().endswith(".png") or "/reference/" in p:
                continue
            pairs = r.get("pairs") or {}
            good = sum(1 for v in pairs.values() if v in ("ours", "same"))
            cal = r.get("calibration") or {}
            key = (good, (r.get("results") or {}).get("art_ref_check") == "pass",
                   cal.get("passed", 0) / max(cal.get("sessions", 1), 1), r.get("at", ""))
            piece = r["piece"]
            if piece not in best or key > best[piece][0]:
                best[piece] = (key, lane, r, p)
    return best

if __name__ == "__main__":
    for piece, (key, lane, r, p) in sorted(candidates().items()):
        print(piece, lane, r["round"], r.get("pairs"), r["results"].get("art_ref_check"), os.path.relpath(p, AREAS))
