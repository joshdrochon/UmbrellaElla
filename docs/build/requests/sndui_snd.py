#!/usr/bin/env python3
"""sndui driver: runs the audio lane's helpers (pipeline/audio/build) with recipes read from Audio/Source/<Id>/recipe.json.
  snd.py gen <Id> [regen args]   layered build (regen.py), then level-match to the ui family RMS target and re-mix
  snd.py prov <Id>               provenance rows (provenance.py generated), moved to sorted place among Audio/Source rows
Run from the repo root."""
import csv, json, os, runpy, subprocess, sys, types
from pathlib import Path
ROOT = Path.cwd(); B = ROOT / "pipeline/audio/build"
TARGET_RMS, TOL = -22.6, 0.6

def recipes():
    sys.path.insert(0, str(B))
    import recipes as R
    for f in sorted((ROOT / "Audio/Source").glob("*/recipe.json")):
        R.RECIPES[f.parent.name] = json.loads(f.read_text())
    return R

def regen(sid, extra):
    sys.argv = ["regen.py", sid, *extra]
    try: runpy.run_path(str(B / "regen.py"), run_name="regen_run")
    except SystemExit as e:
        if e.code: raise

def rms(sid):
    sys.path.insert(0, str(ROOT / "tools"))
    import audio_check as ac
    rules = ac.load_rules(); wr = rules["wav"]
    info, ch = ac.read_wav(str(ROOT / f"Audio/Source/{sid}/SW_{sid}_00.wav"))
    return ac.measure(ch, info["rate"], wr["gate_dbfs"], wr["tail_ms"])

cmd, sid = sys.argv[1], sys.argv[2]
R = recipes()
if cmd == "gen":
    regen(sid, sys.argv[3:])
    f = ROOT / f"Audio/Source/{sid}/recipe.json"
    for _ in range(4):
        m = rms(sid); d = TARGET_RMS - m["rms_db"]
        if abs(d) <= TOL: break
        rec = json.loads(f.read_text()); rec["post_gain_db"] = round(rec.get("post_gain_db", 0) + d, 1)
        f.write_text(json.dumps(rec, indent=1) + "\n"); R.RECIPES[sid] = rec
        regen(sid, [a for a in sys.argv[3:] if a != "--fresh"])
    m = rms(sid); print(f"{sid}: rms {m['rms_db']:.1f} peak {m['peak_dbfs']:.1f} lead {m['lead_ms']:.1f}ms tail {m['tail_dbfs']:.1f}")
    print(subprocess.run(["python3", "tools/audio_style_check.py", "measure", f"Audio/Source/{sid}/SW_{sid}_00.wav"], capture_output=True, text=True).stdout.strip())
    print(subprocess.run(["python3", "tools/audio_style_check.py", "check", "Audio/Source", "--ids", sid], capture_output=True, text=True).stdout.strip())
elif cmd == "prov":
    sys.path.insert(0, str(B))
    import provenance as P
    rows = P.generated(P.dedupe(P.load()), sid)
    mine = [r for r in rows if r and r[0].startswith(f"Audio/Source/{sid}/")]
    rest = [r for r in rows if r not in mine]
    idx = [i for i, r in enumerate(rest) if r and r[0].startswith("Audio/Source/")]
    at = next((i for i in idx if rest[i][0] > mine[0][0]), idx[-1] + 1)
    P.save(rest[:at] + mine + rest[at:])
    print("provenance rows:", len(mine), "at line", at + 1)
