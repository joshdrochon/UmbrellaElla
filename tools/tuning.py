#!/usr/bin/env python3
"""One definition of which tuning values are tunable and which are fixed (dry run B H3, H4). Stdlib only.

tools/bake_preset.py, tools/feel_check.py and tools/encounter_check.py all read this module, so the value the game
ships, the value the feel envelope checks and the value the encounter fairness sim checks follow the same rule.

  tunable  an approved_parameters key (docs/feature-manifest.json; GDD 1.3 printed section 5A ranges) with min, max
           and step: the value sits in min-max and on the step from the start ("use stated step")
  fixed    every other key. An approved_parameters key without a range (every GDD SH1.0 start: its section 9
           tables are blank, D-new-sh10-param-ranges; GDD 1.3 OWL-01.seed, OWL-01.initial_grace_s) must
           equal its start. A key with no approved entry (collider data such as OWL-01.collision_radius, the
           ENGINEERING_PROVISIONAL values) must equal the value already in the source (the bake never changes it;
           a change is a separate approved change, GDD 1.3 sections 7A, 7C)
  flags    an `<ID>.enabled` value is true only for an implementation_authorized APPROVED_P0/P1 (or CONFIRMED)
           record (dry run B C1)

SIM_KEYS maps each bake key to where the sims read it. Once pipeline/qa/baked.json exists, every SIM_KEYS value
in it must equal the sim's value (baked_vs_sim_problems): to ship a new number, change feel.json or encounter.json
in the same PR so the envelope and the fairness sim run on it.

Usage: python3 tools/tuning.py [--root PATH]   prints the baked-vs-sim result (exit 0 = equal or nothing baked)
"""
import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = "docs/feature-manifest.json"
FEEL = "pipeline/feel/feel.json"
ENCOUNTER = "pipeline/level/encounter.json"
STAMP = "pipeline/qa/baked.json"
AUTHORIZED = {"APPROVED_P0", "APPROVED_P1", "CONFIRMED"}
EPS = 1e-6
BASE_BOLT_FEATURE = "OWL-01"

# The GDD-coupled names, one model per GDD revision the manifest can be on (manifest gdd_revision). GDD 1.3 is a
# timer-driven arena with gravity and one owl bolt; GDD SH1.0 (Umbrella Ella: The Stolen Hour) is a four-state mover
# (rise / fall / free fall speeds, no gravity) and a state-driven three-phase Keeper fight whose numbers live in the
# encounter.json baseline preset (`numbers_from_gdd`: preset path -> manifest key). A frozen 1.3 manifest still
# checks against the 1.3 model, so the generic rules keep their tests.
MODELS = {
    "1.3": {
        # feel.json movement key -> bake key (GDD 1.3 section 5A)
        "feel_movement": {
            "move_speed": "CORE-01.move_speed", "move_accel": "CORE-01.move_accel",
            "open_steer_multiplier": "CORE-01.open_steer_multiplier",
            "gravity": "CORE-02.gravity", "max_fall_speed": "CORE-02.max_fall_speed",
            "ascent_speed": "UMB-01.ascent_speed", "ascent_accel": "UMB-01.ascent_accel",
        },
        "feel_forgiveness": {"iframes_s": "CORE-03.invulnerability_s"},   # GDD 1.3 section 6: 0.8 s
        "tell_key": "OWL-01.telegraph_delay",
        "timeline": True,            # encounter.json top-level patterns, phases and duration_sec are the shipped fight
        "sim_extra": ["OWL-01.projectile_speed", "OWL-01.cadence", "OWL-01.initial_grace_s", "OWL-01.seed",
                      "END-01.survival_s"],
        # feel_check: GDD 1.3 has one gravity rule and no fast fall, damage never reduces lift unless SURV-04 is on
        "gravity": True, "fast_fall_rejected": True, "lift_key": None, "lift_loss_feature": "SURV-04",
        "tell_event": "owl_tell_bolts", "gust_feature": "OWL-02", "bolt_prefix": "BOLT_",
    },
    "SH1.0": {
        "feel_movement": {
            "rise_speed": "MOVE-21.rise_speed", "fall_speed": "MOVE-21.fall_speed",
            "free_fall_speed": "MOVE-21.free_fall_speed", "horizontal_max_speed": "MOVE-21.horizontal_max_speed",
        },
        "feel_forgiveness": {"iframes_s": "SURV-05.post_hit_protection_s",
                             "hop_protection_s": "MOVE-21.hop_protection_s"},
        "tell_key": "OWL-21.cast_warning_s",   # the shortest physical warning; red volleys have no prefire (OWL-12)
        "timeline": False,           # the fight is the baseline preset; the top-level timeline is GDD 1.3 history
        "sim_extra": [],             # plus every key the baseline preset's numbers_from_gdd names
        # feel_check: four state speeds (no gravity), fast free fall is a P0 mode (MOVE-05), lift falls with active
        # health to SURV-05.min_lift, the wing gust (OWL-16) is P0, the shortest physical warning is the cast's 0.9 s
        "gravity": False, "fast_fall_rejected": False, "lift_key": "SURV-05.min_lift", "lift_loss_feature": None,
        "tell_event": "owl_tell_cast", "gust_feature": "OWL-16", "bolt_prefix": "RED_",
    },
}
LATEST = "SH1.0"


def model(manifest=None, root=None):
    """The GDD model of a manifest (or of docs/feature-manifest.json under root): MODELS[gdd_revision]."""
    if manifest is None:
        manifest = read_json(os.path.join(root or ROOT, MANIFEST)) or {}
    return MODELS.get((manifest or {}).get("gdd_revision"), MODELS[LATEST])


# The 1.3 names, kept for callers that pass a 1.3 manifest explicitly; new code calls model(manifest).
FEEL_MOVEMENT = MODELS["1.3"]["feel_movement"]
FEEL_FORGIVENESS = MODELS["1.3"]["feel_forgiveness"]
TELL_KEY = MODELS["1.3"]["tell_key"]
SIM_KEYS = sorted(set(FEEL_MOVEMENT.values()) | set(FEEL_FORGIVENESS.values()) | {TELL_KEY}
                  | set(MODELS["1.3"]["sim_extra"]))


def sim_keys(manifest=None, root=None, enc=None):
    """Every bake key a sim reads under the manifest's GDD model (SIM_KEYS for 1.3)."""
    m = model(manifest, root)
    keys = set(m["feel_movement"].values()) | set(m["feel_forgiveness"].values()) | set(m["sim_extra"])
    if m["timeline"]:
        keys.add(m["tell_key"])
    else:
        enc = read_json(os.path.join(root or ROOT, ENCOUNTER)) if enc is None else enc
        keys |= set(preset_numbers(enc))
    return sorted(keys)


def _path(obj, path):
    """Value at a dotted preset path; a list step selects the item whose id matches (targets.WINGS.hp)."""
    cur = obj
    for part in path.split("."):
        if isinstance(cur, list):
            cur = next((x for x in cur if isinstance(x, dict) and x.get("id") == part), None)
        elif isinstance(cur, dict):
            cur = cur.get(part)
        else:
            return None
    return cur


def preset_numbers(enc):
    """{manifest key: value} the encounter.json default preset copies from the GDD (its numbers_from_gdd)."""
    b = (enc or {}).get("encounter_presets") or {}
    p = (b.get("presets") or {}).get(b.get("default")) or {}
    out = {}
    for path, key in (p.get("numbers_from_gdd") or {}).items():
        v = _path(p, path)
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            out.setdefault(key, v)
    return out


def num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def read_json(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def approved(manifest):
    return ((manifest or {}).get("approved_parameters") or {}).get("values") or {}


def rule(manifest, key):
    """{'kind': 'tunable', start, min, max, step} | {'kind': 'fixed', 'start': <n or None>}."""
    rec = approved(manifest).get(key)
    if isinstance(rec, dict) and all(num(rec.get(k)) for k in ("start", "min", "max", "step")) and rec["step"] > 0:
        return {"kind": "tunable", "start": rec["start"], "min": rec["min"], "max": rec["max"], "step": rec["step"],
                "unit": rec.get("unit", "")}
    return {"kind": "fixed", "start": rec.get("start") if isinstance(rec, dict) and num(rec.get("start")) else None,
            "unit": (rec or {}).get("unit", "") if isinstance(rec, dict) else ""}


def on_step(v, start, step):
    k = (v - start) / step
    return abs(k - round(k)) * step <= EPS


DECISIONS = os.path.join(ROOT, "docs", "decisions.md")
VALUES_RE = re.compile(r"Values:\s*([^|;]+)")
VALUE_RE = re.compile(r"^\s*([A-Z]+-\d+\.[a-z0-9_.]+)\s*=\s*(-?\d+(?:\.\d+)?)\s*$")


_DECIDED_CACHE = None


def decided_values(text=None):
    """{key: value} from DECIDED rows of docs/decisions.md that carry a `Values: KEY=n, KEY=n` clause
    (D-new-move-speeds). Only these exact keys and values lift the GDD-range rule; every other key stays strict.
    Returns (values, problems): a clause entry that does not parse is a problem, never silently ignored."""
    global _DECIDED_CACHE
    if text is None:
        if _DECIDED_CACHE is None:
            try:
                with open(DECISIONS, encoding="utf-8") as fh:
                    _DECIDED_CACHE = decided_values(fh.read())
            except OSError:
                _DECIDED_CACHE = ({}, [])
        return _DECIDED_CACHE
    out, bad = {}, []
    for ln in text.splitlines():
        if not ln.startswith("| D-") or "Values:" not in ln:
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if not cells or not cells[-1].upper().startswith("DECIDED"):
            bad.append((cells[0] if cells else ln[:30], "has 'Values:' but is not DECIDED"))
            continue
        m = VALUES_RE.search(ln)
        for part in (m.group(1).split(",") if m else []):
            pm = VALUE_RE.match(part)
            if not pm:
                bad.append((cells[0], f"Values entry {part.strip()!r} is not KEY=number"))
                continue
            out[pm.group(1)] = float(pm.group(2))
    return out, bad

def value_problem(manifest, key, v, current=None):
    """Why v is not allowed for key, or None. current: the value already in the source, for a fixed key with no
    approved start (None = unknown, so only the approved rules apply)."""
    if not num(v):
        return f"{key}={v!r} is not a number"
    decided = decided_values()[0]
    if key in decided:
        # A DECIDED Values clause names this key: exactly that value is allowed, nothing else (D-new-move-speeds).
        return None if abs(v - decided[key]) <= EPS else f"{key}={v:g} differs from {decided[key]:g}, the DECIDED Values clause"
    r = rule(manifest, key)
    if r["kind"] == "tunable":
        # final-9 A M5: a `%` key is written in percent (100 = 100 %), never as a ratio (1.0); the code converts
        # at the point of use (pipeline/unreal/gameplay-code.md), so an 80 used as a gain is never shipped
        pct = (f"; a `%` key is written in percent ({r['start']:g} = {r['start']:g} %), not as a ratio "
               f"({r['start'] / 100:g}): convert with `* 0.01f` where it is used" if r["unit"] == "%" else "")
        if not r["min"] - EPS <= v <= r["max"] + EPS:
            return (f"{key}={v:g} is outside the approved range {r['min']:g}-{r['max']:g} {r['unit']} (GDD 1.3 section 5A)"
                    .replace("  ", " ") + pct)
        if not on_step(v, r["start"], r["step"]):
            return (f"{key}={v:g} is off the approved step {r['step']:g} from {r['start']:g} (GDD 1.3 section 5A: use "
                    f"stated step)" + pct)
        return None
    want = r["start"] if r["start"] is not None else current
    if want is not None and abs(v - want) > EPS:
        why = "the GDD 1.3 fixed value (no dev range)" if r["start"] is not None else \
              "the source value: a fixed key with no approved range is never changed by a bake (GDD 1.3 7A, 7C)"
        return f"{key}={v:g} differs from {want:g}, {why}"
    return None


def flag_problem(manifest, fid, on):
    """An unapproved feature ships off, whatever the manifest default says (dry run B C1)."""
    rec = next((f for f in (manifest or {}).get("features", []) if f.get("feature_id") == fid), None)
    if rec is None or on is not True:
        return None
    if rec.get("implementation_authorized") is True and rec.get("status") in AUTHORIZED:
        return None
    return (f"flag {fid}=on, but {fid} is {rec.get('status')} (implementation_authorized "
            f"{rec.get('implementation_authorized')}): an unapproved feature always ships off")


def base_bolt(enc):
    pats = (enc or {}).get("patterns") or {}
    ids = [pid for pid, p in pats.items() if isinstance(p, dict) and p.get("feature") == BASE_BOLT_FEATURE]
    return (ids[0], pats[ids[0]]) if len(ids) == 1 else (None, None)


def sim_values(root=ROOT, feel=None, enc=None, manifest=None):
    """{bake key: value the sims check} from feel.json and encounter.json (missing or ambiguous keys left out)."""
    feel = read_json(os.path.join(root, FEEL)) if feel is None else feel
    enc = read_json(os.path.join(root, ENCOUNTER)) if enc is None else enc
    m = model(manifest, root)
    out = {}
    mv = (feel or {}).get("movement") or {}
    for k, key in m["feel_movement"].items():
        if num(mv.get(k)):
            out[key] = mv[k]
    fg = (feel or {}).get("forgiveness") or {}
    for k, key in m["feel_forgiveness"].items():
        if num(fg.get(k)):
            out[key] = fg[k]
    if enc and not m["timeline"]:
        out.update(preset_numbers(enc))
    elif enc:
        if num(enc.get("duration_sec")):
            out["END-01.survival_s"] = enc["duration_sec"]
        if num(enc.get("seed")):
            out["OWL-01.seed"] = enc["seed"]
        pid, b = base_bolt(enc)
        if b:
            if num(b.get("telegraph_sec")):
                out[TELL_KEY] = b["telegraph_sec"]
            if num(b.get("speed")):
                out["OWL-01.projectile_speed"] = b["speed"]
            ats = sorted(e["at"] for ph in enc.get("phases") or [] for e in ph.get("schedule") or []
                         if isinstance(e, dict) and e.get("pattern") == pid and num(e.get("at")))
            if ats:
                out["OWL-01.initial_grace_s"] = ats[0]
            gaps = {round(y - x, 6) for x, y in zip(ats, ats[1:])}
            if len(gaps) == 1:
                out["OWL-01.cadence"] = gaps.pop()
    return out


def baked_values(root=ROOT):
    stamp = read_json(os.path.join(root, STAMP))
    return (stamp or {}).get("values") if isinstance(stamp, dict) else None


def baked_vs_sim_problems(root=ROOT, baked=None, feel=None, enc=None, manifest=None):
    """Once something is baked, each SIM_KEYS value the game ships equals the value the sims check (dry run B H4)."""
    baked = baked_values(root) if baked is None else baked
    if not baked:
        return []
    feel = read_json(os.path.join(root, FEEL)) if feel is None else feel
    enc = read_json(os.path.join(root, ENCOUNTER)) if enc is None else enc
    sim = sim_values(root, feel, enc, manifest)
    m = model(manifest, root)
    src = {k: feel for k in list(m["feel_movement"].values()) + list(m["feel_forgiveness"].values())}
    out = []
    for key in sim_keys(manifest, root, enc):
        if key not in baked or src.get(key, enc) is None:
            continue   # that data file is missing: feel_check / encounter_check already fail on it
        if key not in sim:
            out.append(f"{key}: baked {baked[key]}, but {FEEL} / {ENCOUNTER} give the sims no single value for it")
        elif not num(baked[key]) or abs(baked[key] - sim[key]) > EPS:
            out.append(f"{key}: baked {baked[key]}, but the sims check {sim[key]} ({FEEL} / {ENCOUNTER}); change the "
                       "data file in the same PR so the envelope and the fairness sim run on the shipped value")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=ROOT)
    a = ap.parse_args(argv)
    p = baked_vs_sim_problems(a.root)
    for x in p:
        print("FAIL: " + x)
    print(f"tuning: {'FAIL' if p else 'PASS'} {len(p)} problem(s)")
    return 1 if p else 0


if __name__ == "__main__":
    sys.exit(main())
