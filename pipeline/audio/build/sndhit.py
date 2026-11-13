#!/usr/bin/env python3
"""Lane sndhit (hit and trail sounds): this lane's recipes, run through the audio area's helpers unchanged.
  sndhit.py regen <Id> [--take N] [--fresh]   layered rebuild (the audio area's regen.py; key from the environment)
  sndhit.py critic <Id>                       new loop round + fresh blind critic (the audio area's critic.sh)
  sndhit.py generated <Id>                    provenance: one 'generated in jam' row per take, inserted in path order
  sndhit.py placeholder <Id> "<gap>"          provenance: the takes' rows read 'placeholder: audio critic fail (<gap>)'
  sndhit.py levels                            active RMS of every take of this lane against the hit family median
The helpers (regen.py, critic.sh, provenance.py, recipes.py) are the audio area's: used from this folder once
area/audio is merged, else from the sibling worktree ../audio. Nothing of theirs is copied here; this file only adds
RECIPES and points the helpers at this checkout. Loop card: SNDHIT (Saved/AudioLoop/SNDHIT)."""
import csv, os, subprocess, sys, types
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CARD = "SNDHIT"
IDS = ["EllaDown", "OutOfBounds", "SmallBlastImpact", "HitWing", "HitClock", "HitProtected", "WingsBreak",
       "MechanismBreak", "GlassCrack", "EyeHit", "WandBoltFade", "TwinStarsImpact", "NeedlePierce", "HitEnemy",
       "WardenDisable", "FloodDisable", "CourierDisable", "ShutterClose"]   # P0 first, then P1

DRY = ", dry, isolated, no other sounds"
HALL = {"rt60": 1.2, "wet_db": -8, "damp_hz": 3200, "predelay_ms": 18}       # hit, enemy: large stone hall
ROOM = {"rt60": 0.7, "wet_db": -11, "damp_hz": 4500, "predelay_ms": 10}      # clockwork: medium stone room
SMALL = {"rt60": 0.45, "wet_db": -10, "damp_hz": 7000, "predelay_ms": 8}     # wand: small hall


def thud(f0, drop, decay, gain_db, secs=0.6):
    """Synth low thud: a sine that falls from f0+drop to f0 in the first 30 ms, exponential decay, 2 ms rise."""
    return {"kind": "synth", "prompt": f"synthesised low thud: sine falling from {f0 + drop} to {f0} Hz, 2 ms rise, exponential decay",
            "secs": secs, "expr": f"(1-exp(-t*1500))*exp(-{decay}*t)*sin(2*PI*({f0}*t+{drop / 30.0:.4f}*(1-exp(-30*t))))",
            "gain_db": gain_db, "trim": secs}


def bell(freqs, partials, gain_db, secs=0.8, delay_ms=0, what="bell partial"):
    """Synth pitched partials: (ratio, level, decay) each; the take's fundamental comes from freqs."""
    expr = "+".join(f"{lv}*exp(-{dc}*t)*sin(2*PI*{ra}*{{f}}*t)" for ra, lv, dc in partials)
    spec = {"kind": "synth", "prompt": f"synthesised {what}: partials at " + ", ".join(f"{ra}x" for ra, _, _ in partials) + " with their own exponential decays",
            "secs": secs, "freqs": freqs, "expr": expr, "gain_db": gain_db, "trim": secs}
    if delay_ms:
        spec["delay_ms"] = delay_ms
    return spec


def falling(freqs, drop, gain_db, secs=1.5, delay_ms=0, what="falling tone"):
    """Synth harmonic tone whose pitch falls to 1/(1+drop) of the start over the sound: 3 harmonics, slow attack, decay."""
    ph = f"({{f}}*t-{{f}}*{drop/(1+drop):.4f}*t*t/(2*{secs}))"
    expr = f"(1-exp(-t*400))*exp(-{1.6/secs:.3f}*t)*(sin(2*PI*{ph})+0.4*sin(4*PI*{ph})+0.2*sin(6*PI*{ph}))"
    spec = {"kind": "synth", "prompt": f"synthesised {what}: three harmonics, pitch falling over {secs} s", "secs": secs,
            "freqs": freqs, "expr": expr, "gain_db": gain_db, "trim": secs}
    if delay_ms:
        spec["delay_ms"] = delay_ms
    return spec


def api(prompt, secs, filt, gain_db, trim=None, decay=None, delay_ms=0, start_db=-30, influence=None):
    spec = {"prompt": prompt + DRY, "secs": secs, "filter": filt, "gain_db": gain_db,
            "start_db": start_db, "trim": trim or secs}
    if decay is not None:
        spec["decay"] = decay
    if delay_ms:
        spec["delay_ms"] = delay_ms
    if influence is not None:
        spec["influence"] = influence
    return spec


CELESTA = [(1, 0.6, 9), (2, 0.25, 13), (3.01, 0.12, 18), (4.2, 0.05, 26)]     # the approved WandBolt bar partials
TINE = [(1, 0.6, 14), (2.76, 0.22, 22), (5.4, 0.08, 34)]                      # music-box tine (clamped bar modes)
BRASS = [(1, 0.5, 5), (2.41, 0.3, 7), (3.9, 0.2, 10), (5.3, 0.1, 14)]         # struck plate with a bell partial

RECIPES = {
 # ---- hit family (style: hit) ----
 "EllaDown": {
  "seconds": 2.6, "static_level": True, "lufs": -17, "fade_out": 0.9, "takes": 3, "reverb": dict(HALL, rt60=1.4, wet_db=-12, damp_hz=2400),
  "layers": {
   "crack": api("one sharp wooden crack, a thin wooden rib snapping", 1.0,
                "highpass=f=600,lowpass=f=6000", 0, trim=1.0, decay=12, start_db=-24),
   "ribs": api("umbrella collapsing: thin wooden ribs snapping and waxed canvas crumpling in one short crunch", 1.5,
               "highpass=f=350,lowpass=f=5000", 0, trim=1.2, decay=2, start_db=-24, delay_ms=15),
   "thud": thud(60, 50, 9, -16, secs=0.8),
   "ring": bell([660, 740, 587], [(1, 0.4, 14), (2.76, 0.25, 22), (5.4, 0.1, 34)], -14, secs=0.8, delay_ms=5, what="metal rib partial"),
   "drop": {"kind": "synth", "prompt": "synthesised sub drop: sine falling from 110 to 38 Hz over a second, slow decay", "secs": 2.2,
            "expr": "(1-exp(-t*40))*0.8*exp(-1.6*t)*sin(2*PI*(38*t+36*(1-exp(-2*t))))", "gain_db": -15, "delay_ms": 120, "trim": 1.6},
   "cloth": api("heavy cloth falling away and fluttering down into a deep shaft, soft, fading", 2.0,
                "highpass=f=250,lowpass=f=2200", -14, trim=2.0, decay=1.8, delay_ms=350),
   "swell": falling([247, 262, 233], 1.5, -17, secs=1.3, delay_ms=40, what="brass swell falling in pitch"),
   "chime": bell([392, 349, 440], [(1, 0.5, 4), (2.0, 0.2, 5), (3.0, 0.1, 7)], -14, secs=1.2, delay_ms=60, what="low clock-chime partial"),
  }},
 "OutOfBounds": {
  "seconds": 1.6, "static_level": True, "lufs": -19, "fade_out": 0.6, "takes": 3, "reverb": dict(HALL, rt60=1.6, wet_db=-12, damp_hz=2000),
  "layers": {
   "boom": thud(48, 70, 6, -19, secs=1.2),
   "brass": bell([196, 220, 175], [(1, 0.5, 6), (2.41, 0.3, 9), (3.9, 0.15, 14)], -11, secs=1.0, delay_ms=3, what="brass partial"),
   "stone": api("one heavy dull impact of a body of cloth and wood landing on a stone floor far below, deep and dark", 1.2,
                "highpass=f=70,lowpass=f=1400", 0, trim=1.2, decay=5, start_db=-24),
   "iron": api("one dull iron clank struck once, low pitched, short dead ring", 1.0,
               "highpass=f=350,lowpass=f=2600", -5, trim=0.8, decay=6, delay_ms=25),
   "fall": falling([440, 392, 466], 3.0, -19, secs=1.2, what="tone falling steeply in pitch"),
   "wind": {"kind": "synth", "prompt": "synthesised wind rush: low-passed noise fading out", "secs": 1.4,
            "expr": "random(0)*0.5*exp(-1.8*t)*(1-exp(-t*200))", "gain_db": -26, "trim": 1.4, "filter": "highpass=f=200,lowpass=f=1800"},
  }},
 "HitWing": {
  "seconds": 0.9, "static_level": True, "lufs": -16, "fade_out": 0.3, "takes": 3, "reverb": dict(HALL, rt60=1.0),
  "layers": {
   "slap": api("one hard leathery slap on thick stretched hide, a single sharp smack", 0.8,
               "highpass=f=250,lowpass=f=4500", 0, trim=0.4, decay=10, start_db=-24),
   "thud": thud(70, 60, 14, -10),
   "feathers": api("short burst of large feathers ruffling and scattering, soft rustle", 1.0,
                   "highpass=f=900,lowpass=f=5500", -10, trim=0.6, decay=5, delay_ms=30),
  }},
 "HitClock": {
  "seconds": 1.1, "static_level": True, "lufs": -16, "fade_out": 0.4, "takes": 3, "reverb": dict(HALL, rt60=1.1),
  "layers": {
   "clank": api("one bright brass clank struck once on a heavy clock face plate, pitched metallic ring", 1.0,
                "highpass=f=900,lowpass=f=6500", -6, trim=0.45, decay=12, start_db=-24),
   "bell": bell([830, 932, 784], BRASS, -3, secs=1.0, what="brass bell partial"),
   "thud": thud(85, 60, 16, -7),
  }},
 "HitProtected": {
  "seconds": 0.7, "static_level": True, "lufs": -19, "fade_out": 0.25, "takes": 3, "reverb": dict(HALL, rt60=0.8, wet_db=-10, damp_hz=2400),
  "layers": {
   "thud": thud(62, 70, 15, -7),
   "plate": api("one dull muted clank on a thick iron plate, damped, dead short ring, a blocked hit", 0.8,
                "highpass=f=250,lowpass=f=2400", -2, trim=0.45, decay=11, start_db=-24),
   "ring": bell([311, 277, 330], [(1, 0.5, 16), (2.41, 0.25, 24), (3.9, 0.1, 34)], -12, secs=0.5, what="damped iron plate ring"),
  }},
 "GlassCrack": {
  "seconds": 1.1, "static_level": True, "lufs": -16, "fade_out": 0.4, "takes": 3, "reverb": dict(HALL, rt60=1.0, damp_hz=4500),
  "layers": {
   "crack": api("one sharp crack of a thick glass pane splitting, then a short splintering crackle running across it", 1.0,
                "highpass=f=1200,lowpass=f=7500", -6, trim=0.35, decay=14, start_db=-24),
   "shards": bell([1760, 2093, 1568], [(1, 0.5, 7), (2.76, 0.3, 11), (5.4, 0.15, 17)], -9, secs=0.9, what="glass shard ring"),
   "thud": thud(75, 60, 13, -15),
   "frame": bell([523, 587, 494], [(1, 0.5, 9), (2.41, 0.25, 13), (3.9, 0.12, 18)], -13, secs=0.8, what="brass bezel ring"),
  }},
 "EyeHit": {
  "seconds": 1.0, "static_level": True, "lufs": -16, "fade_out": 0.35, "takes": 3, "reverb": dict(HALL, rt60=1.1),
  "layers": {
   "thud": thud(55, 80, 11, -13, secs=0.7),
   "lens": api("one heavy knock on a thick glass lens set in a brass housing, a dull clack with a short hollow ring", 1.0,
               "highpass=f=300,lowpass=f=4200", -1, trim=0.6, decay=8, start_db=-24),
   "ring": bell([622, 554, 698], [(1, 0.5, 6), (2.76, 0.2, 10), (5.4, 0.06, 16)], -11, secs=0.9, delay_ms=6, what="hollow lens ring"),
  }},
 # ---- clockwork family (style: clockwork) ----
 "WingsBreak": {
  "seconds": 1.6, "static_level": True, "lufs": -19, "fade_out": 0.5, "takes": 3, "reverb": ROOM,
  "layers": {
   "snap": api("a heavy clock spring snapping with a sharp metallic crack, then gear teeth skipping", 1.5,
               "highpass=f=400,lowpass=f=7000", 0, trim=0.5, decay=9, start_db=-24),
   "plates": api("large brass plates and rods collapsing in a short heavy clatter", 1.5,
                 "highpass=f=300,lowpass=f=5000", -12, trim=0.8, decay=5, delay_ms=90),
   "t2": bell([2100, 2500, 1900], [(1, 0.6, 70), (1.9, 0.3, 90)], -8, secs=0.3, delay_ms=260, what="escapement tick"),
   "t3": bell([2300, 2000, 2100], [(1, 0.6, 70), (1.9, 0.3, 90)], -9, secs=0.3, delay_ms=420, what="escapement tick"),
   "t4": bell([1800, 2200, 2000], [(1, 0.6, 70), (1.9, 0.3, 90)], -11, secs=0.3, delay_ms=640, what="escapement tick"),
   "lurch": falling([700, 620, 780], 1.2, -12, secs=0.5, delay_ms=150, what="spring lurch falling in pitch"),
   "thud": thud(80, 60, 12, -12),
   "ring": bell([1245, 1109, 1397], [(1, 0.5, 10), (2.76, 0.3, 16), (5.4, 0.12, 26)], -10, secs=0.9, delay_ms=4, what="resonant spring ring"),
   "tick": bell([2400, 2700, 2200], [(1, 0.6, 60), (1.9, 0.3, 80)], -9, secs=0.4, delay_ms=140, what="escapement tick"),
  }},
 "MechanismBreak": {
  "seconds": 1.1, "static_level": True, "lufs": -18.1, "fade_out": 0.35, "takes": 3, "reverb": dict(ROOM, rt60=0.45, wet_db=-14),
  "layers": {
   "chain": api("one iron chain link snapping with a sharp metallic ping", 0.8,
                "highpass=f=500,lowpass=f=4500", 0, trim=0.8, decay=8, start_db=-24),
   "lurch": api("a broken clock gear train lurching: a spring unwinding fast with ratchet clicks slowing down", 1.5,
                "highpass=f=350,lowpass=f=3500", -3, trim=1.0, decay=2, delay_ms=40),
   "fall": api("a heavy brass clock mechanism dropping onto stone and clanking apart", 1.5,
               "highpass=f=180,lowpass=f=3200", -4, trim=1.5, decay=2.5, delay_ms=220, start_db=-24),
   "thud": dict(thud(85, 60, 9, -11), delay_ms=220),
  }},
 "ShutterClose": {
  "seconds": 1.0, "static_level": True, "lufs": -19, "fade_out": 0.35, "takes": 3, "reverb": ROOM,
  "layers": {
   "slam": api("one heavy iron shutter slamming shut, a single hard metallic clack", 1.0,
               "highpass=f=350,lowpass=f=6000", 0, trim=0.6, decay=7, start_db=-24),
   "latch": api("one heavy clock escapement tick, a brass latch locking with a single exact click", 0.6,
                "highpass=f=900,lowpass=f=6500", -7, trim=0.25, decay=18, delay_ms=110),
   "thud": thud(90, 60, 16, -11),
  }},
 # ---- enemy family (style: enemy) ----
 "HitEnemy": {
  "seconds": 0.8, "static_level": True, "lufs": -17, "fade_out": 0.3, "takes": 3, "reverb": dict(HALL, rt60=0.9),
  "layers": {
   "clank": api("one iron gear clank, a pitched strike on a small iron plate", 0.8,
                "highpass=f=300,lowpass=f=3200", 0, trim=0.5, decay=8, start_db=-24),
   "spring": api("one short clock spring twang, a stiff steel spring released once", 0.8,
                 "highpass=f=400,lowpass=f=3000", -14, trim=0.5, decay=12, delay_ms=20),
   "thud": thud(95, 60, 16, -4),
   "strike": {"kind": "synth", "prompt": "synthesised metal strike: 8 ms broadband burst", "secs": 0.05,
              "expr": "random(0)*exp(-90*t)*(1-exp(-t*3000))", "gain_db": 4, "trim": 0.05},
   "p1": bell([880, 784, 932], [(1, 0.5, 9)], -8, secs=0.7, what="gear partial, slow decay"),
   "p2": bell([1318, 1175, 1397], [(1, 0.4, 30)], -9, secs=0.4, what="gear partial, fast decay"),
  }},
 "WardenDisable": {
  "seconds": 1.8, "static_level": True, "lufs": -17, "fade_out": 0.6, "takes": 3, "reverb": dict(HALL, rt60=1.3),
  "layers": {
   "clunk": api("one heavy iron clunk, a big gear locking up dead", 1.0,
                "highpass=f=150,lowpass=f=2600", 0, trim=0.7, decay=6, start_db=-24),
   "wind": api("a heavy clockwork machine winding down: a low spinning gear slowing to a stop and ticking out", 2.0,
               "highpass=f=200,lowpass=f=2800", -5, trim=1.6, decay=1.8, delay_ms=80),
   "thud": thud(58, 60, 9, -3, secs=0.8),
  }},
 "FloodDisable": {
  "seconds": 1.7, "static_level": True, "lufs": -17, "fade_out": 0.6, "takes": 3, "reverb": dict(HALL, rt60=1.3),
  "layers": {
   "buckle": api("tall wooden stilts with iron joints buckling: one wooden crack and a short clatter of poles falling", 1.5,
                 "highpass=f=200,lowpass=f=3200", 0, trim=1.3, decay=2.5, start_db=-24),
   "spring": api("a clock spring letting go with a low metallic twang", 1.0,
                 "highpass=f=250,lowpass=f=2600", -7, trim=0.7, decay=5, delay_ms=40),
   "thud": thud(66, 60, 10, -4, secs=0.8),
  }},
 "CourierDisable": {
  "seconds": 1.3, "static_level": True, "lufs": -17, "fade_out": 0.5, "takes": 3, "reverb": dict(HALL, rt60=1.0),
  "layers": {
   "ping": api("one small iron gear clank, a light pitched metal strike", 0.8,
               "highpass=f=450,lowpass=f=3400", 0, trim=0.4, decay=10, start_db=-24),
   "whirr": api("a small spinning gear whirring down quickly and ticking out, light clockwork", 1.5,
                "highpass=f=350,lowpass=f=3200", -5, trim=1.1, decay=2.5, delay_ms=50),
   "thud": thud(110, 60, 18, -6),
  }},
 # ---- wand family (style: wand): clean additive bars like the approved WandBolt, lower and with an impact tick ----
 "SmallBlastImpact": {
  "seconds": 0.6, "static_level": True, "lufs": -19, "fade_out": 0.25, "takes": 3, "reverb": SMALL,
  "layers": {
   "pluck": bell([1319, 1480, 1661], CELESTA, 0, secs=0.6, what="celesta pluck"),
   "octave": bell([2637, 2960, 3322], TINE, -4, secs=0.4, delay_ms=3, what="music-box tine an octave up"),
   "spark": {"kind": "synth", "prompt": "synthesised soft spark: 12 ms burst of high-passed noise", "secs": 0.12,
             "expr": "0.5*exp(-90*t)*(2*random(0)-1)", "filter": "highpass=f=3500,lowpass=f=9000", "gain_db": -14, "trim": 0.12},
   "glint": bell([3136, 3520, 3951], [(1, 0.5, 24), (2, 0.2, 32)], -17, secs=0.4, delay_ms=80, what="tiny chime ping"),
  }},
 "TwinStarsImpact": {
  "seconds": 0.7, "static_level": True, "lufs": -19, "fade_out": 0.3, "takes": 3, "reverb": SMALL,
  "layers": {
   "star1": bell([1568, 1760, 1397], CELESTA, 0, secs=0.6, what="celesta pluck"),
   "star2": bell([2349, 2637, 2093], CELESTA, -13, secs=0.6, delay_ms=45, what="second celesta pluck a fifth up"),
   "glint": bell([3951, 4435, 3520], [(1, 0.5, 22), (2, 0.2, 30)], -15, secs=0.4, delay_ms=130, what="tiny chime ping"),
  }},
 "NeedlePierce": {
  "seconds": 0.5, "static_level": True, "lufs": -19, "fade_out": 0.2, "takes": 3, "reverb": dict(SMALL, rt60=0.3, wet_db=-13),
  "layers": {
   "tine": bell([2794, 3136, 2489], [(1, 0.6, 20), (2.76, 0.25, 30), (5.4, 0.1, 44)], 0, secs=0.4, what="thin music-box tine"),
   "tick": {"kind": "synth", "prompt": "synthesised needle tick: 5 ms burst of high-passed noise", "secs": 0.06,
            "expr": "0.6*exp(-220*t)*(2*random(0)-1)", "filter": "highpass=f=4000,lowpass=f=10000", "gain_db": -12, "trim": 0.06},
   "through": bell([4186, 4699, 3729], [(1, 0.5, 30), (2, 0.15, 40)], -11, secs=0.3, delay_ms=45, what="second tine a fifth up, the far side"),
  }},
 "WandBoltFade": {
  "seconds": 0.8, "static_level": True, "lufs": -24, "fade_out": 0.35, "takes": 3, "reverb": dict(SMALL, rt60=0.6, wet_db=-7),
  "layers": {
   "p1": bell([3136, 3520, 2794], [(1, 0.5, 16), (2, 0.15, 24)], 0, secs=0.4, what="tiny chime ping"),
   "p2": bell([2637, 2960, 2349], [(1, 0.5, 16), (2, 0.15, 24)], -5, secs=0.4, delay_ms=90, what="tiny chime ping a third down"),
   "p3": bell([2093, 2349, 1865], [(1, 0.5, 14), (2, 0.15, 22)], -10, secs=0.4, delay_ms=190, what="tiny chime ping a fifth down"),
   "p4": bell([1568, 1760, 1397], [(1, 0.5, 12)], -16, secs=0.4, delay_ms=300, what="last faint chime ping an octave down"),
  }},
}


def helper_dir():
    for d in (HERE, ROOT.parent / "audio" / "pipeline" / "audio" / "build"):
        if (d / "regen.py").is_file():
            return d
    sys.exit("the audio area's helpers (regen.py) are neither in pipeline/audio/build nor in ../audio")


def run_helper(name, argv, main=True):
    """Run one of the audio area's scripts as if it lived in this checkout, with this lane's recipes added."""
    hd = helper_dir()
    ns = {}
    exec(compile((hd / "recipes.py").read_text(), str(hd / "recipes.py"), "exec"), ns)
    mod = types.ModuleType("recipes")
    mod.RECIPES = {**ns["RECIPES"], **RECIPES}
    sys.modules["recipes"] = mod
    sys.argv = [name, *argv]
    g = {"__file__": str(HERE / name), "__name__": "__main__" if main else "sndhit_helper"}
    exec(compile((hd / name).read_text(), str(hd / name), "exec"), g)
    return g


def prov_rows():
    with open(ROOT / "pipeline/art/provenance.csv", newline="", encoding="utf-8") as fh:
        return list(csv.reader(fh))


def prov_write(rows, sid, mine):
    """Replace this sound's rows by `mine`, each inserted before the first row with a greater path."""
    pre = f"Audio/Source/{sid}/"
    rows = [r for r in rows if not (r and r[0].startswith(pre))]
    for m in sorted(mine):
        at = next((i for i, r in enumerate(rows[1:], 1) if r and r[0].startswith("Audio/") and r[0] > m[0]), len(rows))
        rows.insert(at, m)
    with open(ROOT / "pipeline/art/provenance.csv", "w", newline="", encoding="utf-8") as fh:
        csv.writer(fh, lineterminator="\n").writerows(rows)


def provenance(sid, gap=None):
    """One row per take, same columns and wording as the audio area's provenance.py writes (that script now asks a
    newer audio_check for the verdict, which this branch does not have; the loop state is the record here)."""
    import datetime
    if sid not in RECIPES:
        sys.exit(f"{sid} is not a sndhit sound")
    rec = RECIPES[sid]
    prompt = "Layered mix (pipeline/audio/build/regen.py, ffmpeg): " + " + ".join(
        f"{n}: {l['prompt']}" for n, l in rec["layers"].items()) + ". Original sound for an etched gothic storybook game. No vocals with words."
    synth = all(l.get("kind") == "synth" for l in rec["layers"].values())
    tool, lic = (("ffmpeg", "LGPL-2.1-or-later (GPL build options); output belongs to the team") if synth else
                 ("ElevenLabs Sound Effects API", "ElevenLabs Terms: commercial use on a paid plan; free plan needs attribution [VERIFY]"))
    origin = (f"placeholder: audio critic fail ({gap.strip()})" if gap is not None else
              "synthesized in jam" if synth else "generated in jam")
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M+00:00")
    mine = [[f.relative_to(ROOT).as_posix(), "team (tools/assetgen.py)", origin, tool, "", prompt, "", "", now, lic,
             "none" if synth else "see pipeline/submission/credits.md"]
            for f in sorted((ROOT / "Audio/Source" / sid).glob("*.wav"))]
    prov_write(prov_rows(), sid, mine)
    print(f"provenance: {sid} {len(mine)} rows, origin '{origin[:70]}'")


def critic(sid):
    hd = helper_dir()
    text = (hd / "critic.sh").read_text()
    v2 = ROOT.parent / "audio" / "tools" / "audio_critic_prompt.md"
    here = ROOT / "tools" / "audio_critic_prompt.md"
    if "audio-critic/1`" in here.read_text() and v2.is_file() and "audio-critic/2" in v2.read_text():
        text = text.replace('"$ROOT/tools/audio_critic_prompt.md"', f'"{v2}"')   # the calibrated prompt, until main has it
    return subprocess.run(["bash", "-c", text, str(HERE / "critic.sh"), sid, CARD], cwd=ROOT).returncode


def short_takes(sid):
    import wave
    out = []
    for t in range(RECIPES[sid].get("takes", 3)):
        with wave.open(str(ROOT / "Audio/Source" / sid / f"SW_{sid}_{t:02d}.wav")) as w:
            if w.getnframes() / w.getframerate() < RECIPES[sid]["seconds"] - 0.02:
                out.append(t)
    return out


def levels():
    sys.path.insert(0, str(ROOT / "tools"))
    r = subprocess.run([sys.executable, "tools/audio_check.py", "--scan", "Audio/Source"], cwd=ROOT, capture_output=True, text=True)
    for ln in r.stdout.splitlines():
        if any(f"/{i}/" in ln for i in IDS) or "median" in ln:
            print(ln)


if __name__ == "__main__":
    cmd, rest = (sys.argv[1] if len(sys.argv) > 1 else ""), sys.argv[2:]
    if cmd == "regen":
        os.environ.setdefault("REGEN_DIR", "/tmp/gen-sndhit")
        run_helper("regen.py", rest)
        short = short_takes(rest[0])
        for _ in range(4):          # the convolution render now and then ends early: render that take again
            if not short:
                break
            run_helper("regen.py", [rest[0]] + [x for t in short for x in ("--take", str(t))])
            short = short_takes(rest[0])
        if short:
            sys.exit(f"{rest[0]}: takes {short} are shorter than the recipe")
    elif cmd == "critic":
        sys.exit(critic(rest[0]))
    elif cmd == "generated":
        provenance(rest[0])
    elif cmd == "placeholder":
        provenance(rest[0], rest[1])
    elif cmd == "levels":
        levels()
    else:
        sys.exit(__doc__)
