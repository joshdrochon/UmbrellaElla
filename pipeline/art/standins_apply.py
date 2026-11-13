#!/usr/bin/env python3
"""Import the best existing candidate of a piece into its drawn slots as a _PH stand-in (not a pass).
  python3 pipeline/art/standins_apply.py <piece> [--src <png relative to ../>] [--lane L] [--note TEXT]
Copies to Art/Source/StandIns/<piece>/, imports via import_art_candidate.py into every drawn slot of the piece,
records pipeline/art/standins.json and a provenance row. Never writes a pass record."""
import argparse, csv, hashlib, json, os, shutil, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
AREAS = os.path.dirname(ROOT)
sys.path.insert(0, HERE)
import standins_pick

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("piece"); ap.add_argument("--src"); ap.add_argument("--lane"); ap.add_argument("--note", default="")
    ap.add_argument("--only", help="comma list of visual ids (default: all drawn slots of the piece)")
    a = ap.parse_args()
    rows = list(csv.DictReader(open(os.path.join(ROOT, "docs/build/art-inventory.csv"), encoding="utf-8")))
    vis = [r["visual"] for r in rows if r["piece"] == a.piece and r["slot"] and r["drawn_by"] not in ("", "-")]
    if a.only: vis = [v for v in vis if v in a.only.split(",")]
    if not vis: sys.exit("no drawn slot for piece " + a.piece)
    info = {"pairs": None, "round": None, "art_ref_check": None, "calibration": None}
    if a.src:
        src = os.path.join(AREAS, a.src) if not os.path.isabs(a.src) else a.src; lane = a.lane or a.src.split("/")[0]
    else:
        c = standins_pick.candidates().get(a.piece)
        if not c: sys.exit("no candidate for " + a.piece)
        _, lane, r, src = c
        info = {"pairs": r.get("pairs"), "round": r.get("round"), "art_ref_check": r["results"].get("art_ref_check"), "calibration": r.get("calibration")}
    dst_dir = os.path.join(ROOT, "Art/Source/StandIns", a.piece); os.makedirs(dst_dir, exist_ok=True)
    dst = os.path.join(dst_dir, os.path.basename(src))
    if os.path.abspath(src) != dst: shutil.copy(src, dst)
    sha = hashlib.sha256(open(dst, "rb").read()).hexdigest()
    rel = os.path.relpath(dst, ROOT)
    for v in vis:
        rc = subprocess.call([sys.executable, os.path.join(ROOT, "tools/build/assets/import_art_candidate.py"), dst, v], cwd=ROOT)
        if rc: print("IMPORT FAILED", v, rc); 
    jp = os.path.join(HERE, "standins.json")
    d = json.load(open(jp)) if os.path.exists(jp) else {"_about": "Stand-ins: best existing candidate per drawn slot, imported as _PH. Not a pass.", "slots": {}}
    for v in vis:
        d["slots"][v] = {"piece": a.piece, "source": os.path.relpath(src, AREAS) if src.startswith(AREAS) else src, "lane": lane,
                         "copy": rel, "sha256": sha, "round": info["round"], "panel_pairs": info["pairs"],
                         "art_ref_check": info["art_ref_check"], "calibration": info["calibration"],
                         "status": "best-so-far (not passed)", "note": a.note}
    json.dump(d, open(jp, "w"), indent=1, sort_keys=True); open(jp, "a").write("\n")
    pp = os.path.join(HERE, "provenance.csv")
    with open(pp, "a", newline="", encoding="utf-8") as fh:
        csv.writer(fh).writerow([rel, "team (candidate from lane %s)" % lane, "stand-in, not passed: copy of %s" % os.path.relpath(src, AREAS) if src.startswith(AREAS) else "stand-in, not passed: " + a.note,
                                 "see source candidate row", "", "", "", "", "2026-11-13", "same as the source candidate (team-made in jam)", "none"])
    print("OK", a.piece, vis)
main()
